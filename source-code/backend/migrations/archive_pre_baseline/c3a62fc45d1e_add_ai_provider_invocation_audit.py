"""add ai provider invocation audit

Revision ID: c3a62fc45d1e
Revises: 37308ed3ea42
Create Date: 2026-09-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a62fc45d1e"
down_revision: Union[str, None] = "37308ed3ea42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_invocations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("document_version_id", sa.Uuid(), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("prompt_name", sa.String(length=80), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("schema_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("response_id", sa.String(length=120), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("request_metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("attempt_count >= 0", name="ck_ai_invocations_attempt_count"),
        sa.CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="ck_ai_invocations_input_tokens"),
        sa.CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_ai_invocations_latency"),
        sa.CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="ck_ai_invocations_output_tokens"),
        sa.CheckConstraint(
            "purpose IN ('textbook_extraction','paper_extraction','unit_mapping','assessment','tutoring')",
            name="ck_ai_invocations_purpose",
        ),
        sa.CheckConstraint("status IN ('processing','completed','failed')", name="ck_ai_invocations_status"),
        sa.CheckConstraint("total_tokens IS NULL OR total_tokens >= 0", name="ck_ai_invocations_total_tokens"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_invocations_actor_id"), "ai_invocations", ["actor_id"])
    op.create_index(op.f("ix_ai_invocations_created_at"), "ai_invocations", ["created_at"])
    op.create_index(op.f("ix_ai_invocations_document_version_id"), "ai_invocations", ["document_version_id"])
    op.create_index(op.f("ix_ai_invocations_purpose"), "ai_invocations", ["purpose"])
    op.create_index(op.f("ix_ai_invocations_response_id"), "ai_invocations", ["response_id"])
    op.create_index(op.f("ix_ai_invocations_status"), "ai_invocations", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_invocations_status"), table_name="ai_invocations")
    op.drop_index(op.f("ix_ai_invocations_response_id"), table_name="ai_invocations")
    op.drop_index(op.f("ix_ai_invocations_purpose"), table_name="ai_invocations")
    op.drop_index(op.f("ix_ai_invocations_document_version_id"), table_name="ai_invocations")
    op.drop_index(op.f("ix_ai_invocations_created_at"), table_name="ai_invocations")
    op.drop_index(op.f("ix_ai_invocations_actor_id"), table_name="ai_invocations")
    op.drop_table("ai_invocations")
