import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.ai.base import AIProviderError
from app.ai.image_provider import ImageResult, OpenAIImageProvider
from app.config import Settings
from app.models import AIProviderAccount, AIProviderAttempt

class ImageAccountRouter:
    def __init__(self, db: Session, settings: Settings, provider_builder=None):
        self.db, self.settings = db, settings
        self.provider_builder = provider_builder or (lambda key: OpenAIImageProvider(key, settings.openai_image_model,
            settings.openai_image_size, settings.ai_timeout_seconds))

    def generate(self, prompt: str, operation_id: uuid.UUID) -> ImageResult:
        now = datetime.now(timezone.utc)
        accounts = self.db.scalars(select(AIProviderAccount).where(AIProviderAccount.enabled.is_(True),
            AIProviderAccount.health_status != "credit_exhausted", or_(AIProviderAccount.cooldown_until.is_(None),
            AIProviderAccount.cooldown_until <= now)).order_by(AIProviderAccount.priority)).all()
        configured = [(account, key) for account in accounts if (key := self.settings.openai_account_key(account.credential_alias))]
        if not configured: raise AIProviderError("no_ai_account", "No enabled OpenAI account has a configured credential.")
        last = None
        for number, (account, key) in enumerate(configured, 1):
            attempt = AIProviderAttempt(operation_id=operation_id, account_id=account.id, attempt_number=number,
                purpose="illustration", model=self.settings.openai_image_model, prompt_version="illustration-v1", status="processing")
            self.db.add(attempt); self.db.flush()
            try: result = self.provider_builder(key).generate(prompt)
            except AIProviderError as exc:
                last=exc; attempt.status="failed"; attempt.error_code=exc.code; attempt.completed_at=datetime.now(timezone.utc)
                account.last_error_code=exc.code; account.last_failure_at=attempt.completed_at
                if exc.disable_account: account.enabled=False; account.health_status="invalid_credential"
                elif exc.code == "credit_balance_exhausted": account.health_status="credit_exhausted"
                elif exc.cooldown_seconds: account.health_status="cooldown"; account.cooldown_until=attempt.completed_at+timedelta(seconds=exc.cooldown_seconds)
                self.db.commit()
                if not exc.failover_allowed: raise
                continue
            attempt.status="completed"; attempt.response_id=result.response_id; attempt.completed_at=datetime.now(timezone.utc)
            account.health_status="available"; account.last_success_at=attempt.completed_at; account.last_error_code=None; account.cooldown_until=None
            self.db.commit(); return result
        raise AIProviderError("all_ai_accounts_unavailable", "All configured OpenAI accounts are unavailable.") from last
