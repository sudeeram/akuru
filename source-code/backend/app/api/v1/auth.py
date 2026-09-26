from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, NormalPasswordChangeRequest, UserResponse
from app.security import CSRF_COOKIE, SESSION_COOKIE, Principal, get_principal, require_csrf
from app.services import authentication


router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()

def _set_auth_cookies(response: Response, token: str, csrf: str) -> None:
    response.set_cookie(SESSION_COOKIE, token, max_age=settings.session_hours * 3600,
        httponly=True, secure=settings.cookie_secure, samesite="strict", path="/")
    response.set_cookie(CSRF_COOKIE, csrf, max_age=settings.session_hours * 3600,
        httponly=False, secure=settings.cookie_secure, samesite="strict", path="/")
    response.headers["Cache-Control"] = "no-store"


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    result, token, csrf = authentication.login(db, payload, request)
    _set_auth_cookies(response, token, csrf)
    return result


@router.get("/me", response_model=UserResponse)
def me(principal: Annotated[Principal, Depends(get_principal)]) -> UserResponse:
    return authentication.public_user(principal.user)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[Principal, Depends(require_csrf)],
) -> None:
    authentication.logout(db, principal)
    response.delete_cookie(
        SESSION_COOKIE, httponly=True, secure=settings.cookie_secure, samesite="strict", path="/"
    )
    response.delete_cookie(
        CSRF_COOKIE, httponly=False, secure=settings.cookie_secure, samesite="strict", path="/"
    )


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[Principal, Depends(require_csrf)],
) -> None:
    token, csrf = authentication.change_password(db, principal, payload.newPassword, request)
    _set_auth_cookies(response, token, csrf)


@router.post("/change-known-password", status_code=204)
def change_known_password(payload: NormalPasswordChangeRequest, request: Request, response: Response,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[Principal, Depends(require_csrf)]) -> None:
    token, csrf = authentication.change_known_password(
        db, principal, payload.currentPassword, payload.newPassword, request)
    _set_auth_cookies(response, token, csrf)
