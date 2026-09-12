import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AuthSession, User

password_hasher = PasswordHash.recommended()
SESSION_COOKIE = "akuru_session"
CSRF_COOKIE = "akuru_csrf"
DUMMY_PASSWORD_HASH = password_hasher.hash("AKURU timing equalization value")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_secret() -> str:
    return secrets.token_urlsafe(48)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return password_hasher.verify(password, stored_hash)
    except Exception:
        return False


@dataclass(frozen=True)
class Principal:
    user: User
    session: AuthSession


def get_principal(
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Principal:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in.")
    if not session_token:
        raise unauthorized
    row = db.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(AuthSession.token_hash == digest(session_token))
    ).one_or_none()
    if row is None:
        raise unauthorized
    auth_session, user = row
    if auth_session.revoked_at is not None or auth_session.expires_at <= utcnow() or not user.is_active:
        raise unauthorized
    return Principal(user=user, session=auth_session)


def require_csrf(
    principal: Annotated[Principal, Depends(get_principal)],
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Principal:
    if not csrf_token or not hmac.compare_digest(digest(csrf_token), principal.session.csrf_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token.")
    return principal


def require_roles(*roles: str):
    def check(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
        if principal.user.must_change_password:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Change the temporary password before continuing.")
        if principal.user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission.")
        return principal
    return check


def require_csrf_roles(*roles: str):
    def check(principal: Annotated[Principal, Depends(require_csrf)]) -> Principal:
        if principal.user.must_change_password:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Change the temporary password before continuing.")
        if principal.user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission.")
        return principal
    return check


def session_expiry() -> datetime:
    return utcnow() + timedelta(hours=get_settings().session_hours)


def request_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
