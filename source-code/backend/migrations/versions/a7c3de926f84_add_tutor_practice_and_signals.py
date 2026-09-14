"""add tutor practice and bounded signals

Revision ID: a7c3de926f84
Revises: f6b2cd815e73
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a7c3de926f84"
down_revision: Union[str, None] = "f6b2cd815e73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_table("tutor_practices",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", sa.String(32), sa.ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("unit_id", sa.Uuid(), sa.ForeignKey("textbook_units.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), sa.ForeignKey("assessments.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("assessment_questions.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)), sa.CheckConstraint("status IN ('active','submitted')", name="ck_tutor_practice_status"),
        sa.UniqueConstraint("session_id", "request_key", name="uq_tutor_practice_request"))
    op.create_index("ix_tutor_practices_public_ref", "tutor_practices", ["public_ref"], unique=True)
    for column in ("session_id", "student_id", "subject_id", "unit_id", "status"):
        op.create_index(f"ix_tutor_practices_{column}", "tutor_practices", [column])
    op.create_index("uq_active_tutor_practice_session", "tutor_practices", ["session_id"], unique=True, postgresql_where=sa.text("status = 'active'"))
    op.create_table("tutor_signals",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_id", sa.Uuid(), sa.ForeignKey("tutor_turns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_id", sa.Uuid(), sa.ForeignKey("textbook_units.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category", sa.String(32), nullable=False), sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), server_default="[]", nullable=False), sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("prompt_name", sa.String(80), nullable=False), sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False), sa.Column("model", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("category IN ('engagement','confidence','misconception','practice_need')", name="ck_tutor_signal_category"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_tutor_signal_confidence"))
    op.create_index("ix_tutor_signals_public_ref", "tutor_signals", ["public_ref"], unique=True)
    for column in ("student_id", "session_id", "turn_id", "unit_id", "created_at"):
        op.create_index(f"ix_tutor_signals_{column}", "tutor_signals", [column])

def downgrade():
    op.drop_table("tutor_signals")
    op.drop_table("tutor_practices")
