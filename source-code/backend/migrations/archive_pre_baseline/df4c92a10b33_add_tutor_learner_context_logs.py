"""add tutor learner context logs

Revision ID: df4c92a10b33
Revises: c14d7a2f9e01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "df4c92a10b33"
down_revision: Union[str, None] = "c14d7a2f9e01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "tutor_learner_context_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_ref", sa.String(48), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("active_unit_id", sa.Uuid(), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("context_version", sa.String(64), nullable=False),
        sa.Column("evidence_references", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("context_snapshot", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["tutor_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["active_unit_id"], ["textbook_units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "request_key", name="uq_tutor_context_request"),
    )
    op.create_index("ix_tutor_learner_context_logs_public_ref", "tutor_learner_context_logs", ["public_ref"], unique=True)
    op.create_index("ix_tutor_learner_context_logs_session_id", "tutor_learner_context_logs", ["session_id"])
    op.create_index("ix_tutor_learner_context_logs_student_id", "tutor_learner_context_logs", ["student_id"])
    op.create_index("ix_tutor_learner_context_logs_subject_id", "tutor_learner_context_logs", ["subject_id"])
    op.create_index("ix_tutor_learner_context_logs_context_version", "tutor_learner_context_logs", ["context_version"])


def downgrade():
    op.drop_table("tutor_learner_context_logs")
