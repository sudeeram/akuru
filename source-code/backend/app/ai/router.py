import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.ai.base import AIProvider, AIProviderError, AIRequest, AIResult
from app.ai.provider import OpenAIProvider
from app.config import Settings
from app.models import AIProviderAccount, AIProviderAttempt


ProviderBuilder = Callable[[AIProviderAccount, str], AIProvider]


class AIAccountRouter:
    def __init__(
        self, db: Session, settings: Settings,
        provider_builder: ProviderBuilder | None = None,
    ):
        self.db = db
        self.settings = settings
        self.provider_builder = provider_builder or self._build_openai

    def generate(self, request: AIRequest, *, operation_id: uuid.UUID | None = None) -> AIResult:
        operation_id = operation_id or uuid.uuid4()
        now = datetime.now(timezone.utc)
        accounts = self.db.scalars(
            select(AIProviderAccount).where(
                AIProviderAccount.enabled.is_(True),
                AIProviderAccount.health_status != "credit_exhausted",
                or_(AIProviderAccount.cooldown_until.is_(None), AIProviderAccount.cooldown_until <= now),
            ).order_by(AIProviderAccount.priority)
        ).all()
        configured = [
            (account, key) for account in accounts
            if (key := self.settings.openai_account_key(account.credential_alias))
        ]
        if not configured:
            raise AIProviderError("no_ai_account", "No enabled OpenAI account has a configured credential.")

        required_model = configured[0][0].model
        eligible = [(account, key) for account, key in configured if account.model == required_model]
        last_error: AIProviderError | None = None
        for number, (account, key) in enumerate(eligible, start=1):
            attempt = AIProviderAttempt(
                operation_id=operation_id, account_id=account.id, attempt_number=number,
                purpose=request.purpose, model=required_model,
                prompt_version=request.prompt_version, status="processing",
            )
            self.db.add(attempt)
            self.db.flush()
            try:
                result = self.provider_builder(account, key).generate(request)
            except AIProviderError as exc:
                last_error = exc
                completed = datetime.now(timezone.utc)
                attempt.status = "failed"
                attempt.error_code = exc.code
                attempt.completed_at = completed
                account.last_error_code = exc.code
                account.last_failure_at = completed
                if exc.disable_account:
                    account.enabled = False
                    account.health_status = "invalid_credential"
                elif exc.code == "credit_balance_exhausted":
                    account.health_status = "credit_exhausted"
                elif exc.cooldown_seconds:
                    account.health_status = "cooldown"
                    account.cooldown_until = completed + timedelta(seconds=exc.cooldown_seconds)
                self.db.commit()
                if not exc.failover_allowed:
                    raise
                continue
            completed = datetime.now(timezone.utc)
            attempt.status = "completed"
            attempt.response_id = result.response_id
            attempt.completed_at = completed
            account.health_status = "available"
            account.cooldown_until = None
            account.last_error_code = None
            account.last_success_at = completed
            self.db.commit()
            return result
        if last_error:
            raise AIProviderError(
                "all_ai_accounts_unavailable", "All configured OpenAI accounts are unavailable."
            ) from last_error
        raise AIProviderError(
            "no_compatible_ai_account", "No backup OpenAI account supports the required model."
        )

    def _build_openai(self, account: AIProviderAccount, api_key: str) -> AIProvider:
        return OpenAIProvider(
            api_key=api_key, model=account.model, timeout_seconds=self.settings.ai_timeout_seconds,
            max_retries=self.settings.ai_max_retries,
            max_concurrency=self.settings.ai_max_concurrency,
            max_pages=self.settings.ai_max_pages_per_request,
            max_input_characters=self.settings.ai_max_input_characters,
            max_image_bytes=self.settings.ai_max_image_bytes,
            max_output_tokens=self.settings.ai_max_output_tokens,
        )
