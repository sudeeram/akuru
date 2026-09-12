from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AuthSession, LoginThrottle, User
from app.security import (
    CSRF_COOKIE, DUMMY_PASSWORD_HASH, SESSION_COOKIE, Principal, digest, get_principal, new_secret, request_ip,
    require_csrf, session_expiry, utcnow, verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
settings = get_settings()


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    id: str
    username: str
    name: str
    role: Literal["admin", "parent", "student"]
    mustChangePassword: bool


class LoginResponse(BaseModel):
    user: UserResponse
    csrfToken: str


def public_user(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id), username=user.username, name=user.display_name,
        role=user.role, mustChangePassword=user.must_change_password,
    )


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(min_length=1, max_length=200)
    newPassword: str = Field(min_length=12, max_length=200)

    @model_validator(mode="after")
    def passwords_must_differ(self):
        if self.currentPassword == self.newPassword:
            raise ValueError("The new password must be different.")
        return self


def throttle_key(request: Request, username: str) -> str:
    return digest(f"{request_ip(request)}\0{username}")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Annotated[Session, Depends(get_db)]) -> LoginResponse:
    now = utcnow()
    key = throttle_key(request, payload.username)
    # Serialize attempts for this client/username pair so concurrent requests
    # cannot race past the failure counter.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})
    throttle = db.get(LoginThrottle, key)
    if throttle and throttle.locked_until and throttle.locked_until > now:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Try again later.", headers={"Retry-After": str(settings.login_lock_minutes * 60)})
    if throttle and now - throttle.window_started_at >= timedelta(minutes=settings.login_window_minutes):
        throttle.failure_count = 0
        throttle.window_started_at = now
        throttle.locked_until = None

    user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    password_valid = verify_password(payload.password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    valid = bool(user and user.is_active and password_valid)
    if not valid:
        if throttle is None:
            throttle = LoginThrottle(key_hash=key, failure_count=0, window_started_at=now)
            db.add(throttle)
        throttle.failure_count += 1
        if throttle.failure_count >= settings.login_attempt_limit:
            throttle.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The username or password is incorrect.")

    if throttle:
        db.delete(throttle)
    db.execute(delete(AuthSession).where((AuthSession.user_id == user.id) & (AuthSession.expires_at <= now)))
    token, csrf = new_secret(), new_secret()
    db.add(AuthSession(
        user_id=user.id,
        token_hash=digest(token),
        csrf_hash=digest(csrf),
        expires_at=session_expiry(),
        client_ip_hash=digest(request_ip(request)),
        user_agent=request.headers.get("user-agent", "")[:300],
    ))
    db.commit()
    response.set_cookie(
        SESSION_COOKIE, token, max_age=settings.session_hours * 3600,
        httponly=True, secure=settings.cookie_secure, samesite="strict", path="/",
    )
    response.set_cookie(
        CSRF_COOKIE, csrf, max_age=settings.session_hours * 3600,
        httponly=False, secure=settings.cookie_secure, samesite="strict", path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return LoginResponse(user=public_user(user), csrfToken=csrf)


@router.get("/me", response_model=UserResponse)
def me(principal: Annotated[Principal, Depends(get_principal)]) -> UserResponse:
    return public_user(principal.user)


@router.post("/logout", status_code=204)
def logout(response: Response, db: Annotated[Session, Depends(get_db)], principal: Annotated[Principal, Depends(require_csrf)]) -> None:
    principal.session.revoked_at = utcnow()
    db.commit()
    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=settings.cookie_secure, samesite="strict", path="/")
    response.delete_cookie(CSRF_COOKIE, httponly=False, secure=settings.cookie_secure, samesite="strict", path="/")


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[Principal, Depends(require_csrf)],
) -> None:
    if not verify_password(payload.currentPassword, principal.user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The current password is incorrect.")
    from app.security import hash_password

    principal.user.password_hash = hash_password(payload.newPassword)
    principal.user.must_change_password = False
    db.execute(
        delete(AuthSession).where(
            (AuthSession.user_id == principal.user.id)
            & (AuthSession.id != principal.session.id)
        )
    )
    db.commit()
