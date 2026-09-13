from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import AIProviderAccount, AuditEvent
from app.schemas.ai_accounts import AIAccountResponse, AIAccountWriteRequest
from app.security import Principal


def _response(account: AIProviderAccount, settings: Settings) -> AIAccountResponse:
    iso = lambda value: value.isoformat() if value else None
    return AIAccountResponse(
        name=account.display_name, credentialAlias=account.credential_alias,
        priority=account.priority, model=account.model, enabled=account.enabled,
        credentialConfigured=settings.openai_account_key(account.credential_alias) is not None,
        healthStatus=account.health_status, cooldownUntil=iso(account.cooldown_until),
        lastErrorCode=account.last_error_code, lastSuccessAt=iso(account.last_success_at),
        lastFailureAt=iso(account.last_failure_at),
    )


def list_accounts(db: Session, settings: Settings) -> list[AIAccountResponse]:
    rows = db.scalars(select(AIProviderAccount).order_by(AIProviderAccount.priority)).all()
    return [_response(row, settings) for row in rows]


def save_account(
    db: Session, principal: Principal, settings: Settings, payload: AIAccountWriteRequest,
    existing_alias: str | None = None,
) -> AIAccountResponse:
    account = None
    if existing_alias:
        account = db.scalar(select(AIProviderAccount).where(
            AIProviderAccount.credential_alias == existing_alias.upper()
        ))
        if not account:
            raise DomainError("ai_account_not_found", "OpenAI account configuration not found.", 404)
    if account is None:
        account = AIProviderAccount()
        db.add(account)
        action = "ai_account.created"
    else:
        action = "ai_account.updated"
    account.display_name = payload.name
    account.credential_alias = payload.credentialAlias
    account.priority = payload.priority
    account.model = payload.model
    account.enabled = payload.enabled
    account.health_status = "unknown"
    account.cooldown_until = None
    account.last_error_code = None
    db.add(AuditEvent(
        actor_id=principal.user.id, action=action, target_type="ai_provider_account",
        target_id=payload.credentialAlias,
        event_data={"priority": payload.priority, "model": payload.model, "enabled": payload.enabled},
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(
            "ai_account_conflict", "Account name, credential alias, and priority must each be unique.", 409
        ) from exc
    db.refresh(account)
    return _response(account, settings)
