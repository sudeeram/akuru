"""add OpenAI account routing

Revision ID: d47e9b2a61f0
Revises: c3a62fc45d1e
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d47e9b2a61f0"
down_revision: Union[str, None] = "c3a62fc45d1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_provider_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("credential_alias", sa.String(length=40), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("health_status", sa.String(length=24), server_default="unknown", nullable=False),
        sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=80), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("priority BETWEEN 0 AND 100", name="ck_ai_provider_accounts_priority"),
        sa.CheckConstraint(
            "health_status IN ('unknown','available','cooldown','credit_exhausted','invalid_credential')",
            name="ck_ai_provider_accounts_health",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("credential_alias"),
        sa.UniqueConstraint("display_name"),
        sa.UniqueConstraint("priority"),
    )
    op.create_table(
        "ai_provider_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("response_id", sa.String(length=120), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("attempt_number > 0", name="ck_ai_provider_attempts_number"),
        sa.CheckConstraint("status IN ('processing','completed','failed')", name="ck_ai_provider_attempts_status"),
        sa.ForeignKeyConstraint(["account_id"], ["ai_provider_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("operation_id", "attempt_number", name="uq_ai_provider_attempt_operation_number"),
    )
    op.create_index(op.f("ix_ai_provider_attempts_account_id"), "ai_provider_attempts", ["account_id"])
    op.create_index(op.f("ix_ai_provider_attempts_operation_id"), "ai_provider_attempts", ["operation_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_provider_attempts_operation_id"), table_name="ai_provider_attempts")
    op.drop_index(op.f("ix_ai_provider_attempts_account_id"), table_name="ai_provider_attempts")
    op.drop_table("ai_provider_attempts")
    op.drop_table("ai_provider_accounts")
