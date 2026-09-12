from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.accounts import AccountResponse, CreateAccountRequest, UpdateStudentRequest
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
