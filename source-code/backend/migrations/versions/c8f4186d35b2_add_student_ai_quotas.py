"""add per-child AI quotas and usage ledger

Revision ID: c8f4186d35b2
Revises: a7c3de926f84
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c8f4186d35b2"
down_revision: Union[str, None] = "a7c3de926f84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table("student_ai_quotas",
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("public_ref", sa.String(56), nullable=False, unique=True),
        sa.Column("period_days", sa.Integer(), server_default="30", nullable=False),
        sa.Column("period_anchor", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("request_allowance", sa.Integer(), server_default="100", nullable=False),
        sa.Column("text_token_allowance", sa.Integer(), server_default="200000", nullable=False),
        sa.Column("voice_seconds_allowance", sa.Integer(), server_default="3600", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("updated_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("period_days BETWEEN 1 AND 366", name="ck_student_ai_quota_period_days"),
        sa.CheckConstraint("request_allowance >= 0", name="ck_student_ai_quota_requests"),
        sa.CheckConstraint("text_token_allowance >= 0", name="ck_student_ai_quota_text_tokens"),
        sa.CheckConstraint("voice_seconds_allowance >= 0", name="ck_student_ai_quota_voice_seconds"))
    op.create_table("student_ai_usage",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation_id", sa.String(100), nullable=False),
        sa.Column("dimension", sa.String(24), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(300)), sa.Column("event_data", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("dimension IN ('request','text_token','voice_second')", name="ck_student_ai_usage_dimension"),
        sa.CheckConstraint("event_type IN ('reserve','settle','release','adjustment')", name="ck_student_ai_usage_event_type"),
        sa.UniqueConstraint("student_id", "operation_id", "dimension", "event_type", name="uq_student_ai_usage_operation_event"))
    for column in ("student_id", "operation_id", "dimension", "event_type", "created_at"):
        op.create_index(f"ix_student_ai_usage_{column}", "student_ai_usage", [column])
    op.execute("""INSERT INTO student_ai_quotas
        (student_id, public_ref, period_days, request_allowance, text_token_allowance, voice_seconds_allowance, is_enabled)
        SELECT student_id, 'quota_' || replace(gen_random_uuid()::text, '-', ''), 30, 100, 200000, 3600, true
        FROM student_profiles""")


def downgrade():
    op.drop_table("student_ai_usage")
    op.drop_table("student_ai_quotas")
