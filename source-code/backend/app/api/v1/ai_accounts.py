from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.ai_accounts import AIAccountResponse, AIAccountWriteRequest
from app.security import Principal
from app.services import ai_accounts


router = APIRouter(prefix="/admin/ai-accounts", tags=["ai accounts"])


@router.get("", response_model=list[AIAccountResponse])
def list_provider_accounts(
    _principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
) -> list[AIAccountResponse]:
    return ai_accounts.list_accounts(db, settings)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AIAccountResponse)
def create_provider_account(
    payload: AIAccountWriteRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
) -> AIAccountResponse:
    return ai_accounts.save_account(db, principal, settings, payload)


@router.post("/{credential_alias}", response_model=AIAccountResponse)
def update_provider_account(
    credential_alias: str, payload: AIAccountWriteRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
) -> AIAccountResponse:
    return ai_accounts.save_account(db, principal, settings, payload, credential_alias)
