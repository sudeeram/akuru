from datetime import timedelta

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import DomainError
from app.models import AuthSession, LoginThrottle, User
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.security import (
    DUMMY_PASSWORD_HASH, Principal, digest, hash_password, new_secret, request_ip,
    session_expiry, utcnow, verify_password,
)


settings = get_settings()


def public_user(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id), username=user.username, name=user.display_name,
        role=user.role, mustChangePassword=user.must_change_password,
    )


def login(db: Session, payload: LoginRequest, request: Request) -> tuple[LoginResponse, str, str]:
    now = utcnow()
    key = digest(f"{request_ip(request)}\0{payload.username}")
    repository = UserRepository(db)
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})
    throttle = repository.throttle(key)
    if throttle and throttle.locked_until and throttle.locked_until > now:
        raise DomainError(
            "rate_limited", "Too many attempts. Try again later.", 429,
            [{"retryAfterSeconds": settings.login_lock_minutes * 60}],
        )
    if throttle and now - throttle.window_started_at >= timedelta(minutes=settings.login_window_minutes):
        throttle.failure_count = 0
        throttle.window_started_at = now
        throttle.locked_until = None

    user = repository.by_username(payload.username)
    password_valid = verify_password(payload.password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if not (user and user.is_active and password_valid):
        if throttle is None:
            throttle = LoginThrottle(key_hash=key, failure_count=0, window_started_at=now)
            db.add(throttle)
        throttle.failure_count += 1
        if throttle.failure_count >= settings.login_attempt_limit:
            throttle.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
        db.commit()
        raise DomainError("invalid_credentials", "The username or password is incorrect.", 401)

    if throttle:
        db.delete(throttle)
    repository.expired_sessions(user.id, now)
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
    return LoginResponse(user=public_user(user), csrfToken=csrf), token, csrf


def change_password(db: Session, principal: Principal, new_password: str) -> None:
    if not principal.user.must_change_password:
        raise DomainError("password_already_changed", "The temporary password has already been replaced.", 409)
    if verify_password(new_password, principal.user.password_hash):
        raise DomainError(
            "password_reused", "The new password cannot be same as the existing password.", 400
        )
    principal.user.password_hash = hash_password(new_password)
    principal.user.must_change_password = False
    UserRepository(db).revoke_other_sessions(principal.user.id, principal.session.id)
    db.commit()


def logout(db: Session, principal: Principal) -> None:
    principal.session.revoked_at = utcnow()
    db.commit()
