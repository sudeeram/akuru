"""add tutor sessions and transcripts

Revision ID: c14d7a2f9e01
Revises: a31c0f4e8b72
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c14d7a2f9e01"
down_revision: Union[str, None] = "a31c0f4e8b72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table("tutor_sessions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("public_ref", sa.String(48), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False), sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("active_unit_id", sa.Uuid(), nullable=False), sa.Column("current_profile_version_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(16), server_default="practice", nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("start_request_key", sa.String(100), nullable=False), sa.Column("end_request_key", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("mode = 'practice'", name="ck_tutor_session_mode"),
        sa.CheckConstraint("status IN ('active','ended')", name="ck_tutor_session_status"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["active_unit_id"], ["textbook_units.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["current_profile_version_id"], ["tutor_profile_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "start_request_key", name="uq_tutor_session_start_request"))
    op.create_index("ix_tutor_sessions_public_ref", "tutor_sessions", ["public_ref"], unique=True)
    op.create_index("ix_tutor_sessions_student_id", "tutor_sessions", ["student_id"])
    op.create_index("ix_tutor_sessions_subject_id", "tutor_sessions", ["subject_id"])
    op.create_index("ix_tutor_sessions_status", "tutor_sessions", ["status"])
    op.create_index("uq_active_tutor_session_per_student", "tutor_sessions", ["student_id"], unique=True, postgresql_where=sa.text("status = 'active'"))

    op.create_table("tutor_turns",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("public_ref", sa.String(48), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False), sa.Column("profile_version_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False), sa.Column("role", sa.String(16), nullable=False),
        sa.Column("modality", sa.String(12), server_default="text", nullable=False), sa.Column("content", sa.Text(), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("sequence > 0", name="ck_tutor_turn_sequence"),
        sa.CheckConstraint("role IN ('student','assistant')", name="ck_tutor_turn_role"),
        sa.CheckConstraint("modality IN ('text','voice')", name="ck_tutor_turn_modality"),
        sa.ForeignKeyConstraint(["session_id"], ["tutor_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_version_id"], ["tutor_profile_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence", name="uq_tutor_turn_sequence"),
        sa.UniqueConstraint("session_id", "request_key", name="uq_tutor_turn_request"))
    op.create_index("ix_tutor_turns_public_ref", "tutor_turns", ["public_ref"], unique=True)
    op.create_index("ix_tutor_turns_session_id", "tutor_turns", ["session_id"])

    op.create_table("tutor_turn_sources",
        sa.Column("turn_id", sa.Uuid(), nullable=False), sa.Column("retrieval_chunk_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.CheckConstraint("ordinal >= 0", name="ck_tutor_turn_source_ordinal"),
        sa.ForeignKeyConstraint(["turn_id"], ["tutor_turns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["retrieval_chunk_id"], ["retrieval_chunks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("turn_id", "retrieval_chunk_id"))

    op.create_table("tutor_session_profile_events",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("from_profile_version_id", sa.Uuid(), nullable=False), sa.Column("to_profile_version_id", sa.Uuid(), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False), sa.Column("handover_summary", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["tutor_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_profile_version_id"], ["tutor_profile_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_profile_version_id"], ["tutor_profile_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("session_id", "request_key", name="uq_tutor_profile_switch_request"))
    op.create_index("ix_tutor_session_profile_events_session_id", "tutor_session_profile_events", ["session_id"])

    op.create_table("tutor_session_unit_events",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("from_unit_id", sa.Uuid(), nullable=False), sa.Column("to_unit_id", sa.Uuid(), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["tutor_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_unit_id"], ["textbook_units.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_unit_id"], ["textbook_units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("session_id", "request_key", name="uq_tutor_unit_switch_request"))
    op.create_index("ix_tutor_session_unit_events_session_id", "tutor_session_unit_events", ["session_id"])


def downgrade():
    op.drop_table("tutor_session_unit_events")
    op.drop_table("tutor_session_profile_events")
    op.drop_table("tutor_turn_sources")
    op.drop_table("tutor_turns")
    op.drop_table("tutor_sessions")
