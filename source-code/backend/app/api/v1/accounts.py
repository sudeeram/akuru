from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.accounts import (AccountResponse, AccountSecurityEventResponse,
    AdminPasswordResetRequest, AdminPasswordResetResponse, CreateAccountRequest,
    UpdateStudentRequest)
from app.schemas.portal import PortalStateResponse, StudentResponse, UiFeaturesResponse
from app.security import Principal, get_principal
from app.services import accounts, portal


router = APIRouter(tags=["accounts"])


@router.get("/admin/ui-features", response_model=UiFeaturesResponse)
def ui_features_access(
    principal: Annotated[Principal, Depends(require_roles("admin"))],
) -> UiFeaturesResponse:
    return {"allowed": True, "user": {"name": principal.user.display_name, "role": principal.user.role}}


@router.post("/admin/accounts", status_code=status.HTTP_201_CREATED, response_model=AccountResponse)
def create_account(
    payload: CreateAccountRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> AccountResponse:
    return accounts.create_account(db, principal, payload)


@router.post("/admin/accounts/{account_ref}/reset-password", response_model=AdminPasswordResetResponse)
def reset_account_password(account_ref: str, payload: AdminPasswordResetRequest, response: Response,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)]) -> AdminPasswordResetResponse:
    result = accounts.reset_password(db, principal, account_ref, payload.requestKey)
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/admin/accounts/security-events", response_model=list[AccountSecurityEventResponse])
def account_security_events(
    principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    return accounts.security_events(db)


@router.post("/admin/students", response_model=StudentResponse)
def update_student(
    payload: UpdateStudentRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> StudentResponse:
    return StudentResponse.model_validate(accounts.update_student(db, principal, payload))


@router.get("/state", response_model=PortalStateResponse)
def state(
    principal: Annotated[Principal, Depends(get_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> PortalStateResponse:
    return PortalStateResponse.model_validate(portal.get_portal_state(db, principal))
