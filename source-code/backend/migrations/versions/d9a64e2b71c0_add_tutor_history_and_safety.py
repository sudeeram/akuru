"""add tutor summaries safety events and transcript purge state

Revision ID: d9a64e2b71c0
Revises: c8f4186d35b2
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d9a64e2b71c0"
down_revision: Union[str, None] = "c8f4186d35b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("tutor_turns", sa.Column("purged_at", sa.DateTime(timezone=True)))
    op.create_table("tutor_session_summaries",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", sa.String(32), sa.ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("units_covered", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("activities", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("strengths", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("difficulties", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("next_steps", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("usage_data", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_tutor_session_summaries_public_ref", "tutor_session_summaries", ["public_ref"], unique=True)
    op.create_index("ix_tutor_session_summaries_student_id", "tutor_session_summaries", ["student_id"])
    op.create_index("ix_tutor_session_summaries_subject_id", "tutor_session_summaries", ["subject_id"])
    op.create_table("tutor_safety_events",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_turn_id", sa.Uuid(), sa.ForeignKey("tutor_turns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(32), nullable=False), sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("notification_status", sa.String(20), server_default="notified", nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True)),
        sa.Column("review_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("review_note", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("severity IN ('low','medium','high','critical')", name="ck_tutor_safety_severity"),
        sa.CheckConstraint("notification_status IN ('pending','notified')", name="ck_tutor_safety_notification"),
        sa.CheckConstraint("review_status IN ('pending','reviewed','resolved')", name="ck_tutor_safety_review"),
        sa.UniqueConstraint("source_turn_id", "category", name="uq_tutor_safety_turn_category"))
    for column in ("public_ref", "student_id", "parent_id", "session_id"):
        op.create_index(f"ix_tutor_safety_events_{column}", "tutor_safety_events", [column], unique=column == "public_ref")


def downgrade():
    op.drop_table("tutor_safety_events")
    op.drop_table("tutor_session_summaries")
    op.drop_column("tutor_turns", "purged_at")
