"""add tutor realtime connection accounting

Revision ID: e4c21b793f60
Revises: d9a64e2b71c0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e4c21b793f60"
down_revision: Union[str, None] = "d9a64e2b71c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "tutor_realtime_connections",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_version_id", sa.Uuid(), sa.ForeignKey("tutor_profile_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("ai_provider_accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("operation_id", sa.String(100), nullable=False, unique=True),
        sa.Column("provider_session_id", sa.String(120)),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("voice", sa.String(40), nullable=False),
        sa.Column("language_mode", sa.String(32), nullable=False),
        sa.Column("reserved_seconds", sa.Integer(), nullable=False),
        sa.Column("billed_seconds", sa.Integer()),
        sa.Column("status", sa.String(20), server_default="connecting", nullable=False),
        sa.Column("failure_code", sa.String(80)),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("reserved_seconds > 0", name="ck_tutor_realtime_reserved_seconds"),
        sa.CheckConstraint("billed_seconds IS NULL OR billed_seconds >= 0", name="ck_tutor_realtime_billed_seconds"),
        sa.CheckConstraint("status IN ('connecting','connected','ended','failed','cancelled')", name="ck_tutor_realtime_status"),
        sa.CheckConstraint("language_mode IN ('auto','french_conversation','french_vocabulary','french_pronunciation')", name="ck_tutor_realtime_language_mode"),
    )
    for column in ("public_ref", "session_id", "student_id", "account_id", "provider_session_id"):
        op.create_index(f"ix_tutor_realtime_connections_{column}", "tutor_realtime_connections", [column], unique=column == "public_ref")


def downgrade():
    op.drop_table("tutor_realtime_connections")
