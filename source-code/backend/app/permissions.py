import uuid
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status

from app.security import Principal, get_principal, require_csrf


def require_roles(*roles: str) -> Callable[..., Principal]:
    def check(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
        return _check_role(principal, roles)

    return check


def require_csrf_roles(*roles: str) -> Callable[..., Principal]:
    def check(principal: Annotated[Principal, Depends(require_csrf)]) -> Principal:
        return _check_role(principal, roles)

    return check


def _check_role(principal: Principal, roles: tuple[str, ...]) -> Principal:
    if principal.user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Change the temporary password before continuing.",
        )
    if principal.user.role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission.")
    return principal


def require_student_submission_owner(principal: Principal, student_id: uuid.UUID) -> None:
    """Prevent a client from creating or changing another student's submission."""
    if principal.user.role != "student" or principal.user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students may submit work only for their own account.",
        )
