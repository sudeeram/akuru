"""add topic learning context

Revision ID: h86c0d2f7a97
Revises: g75b9c1e6f86
"""
from alembic import op
import sqlalchemy as sa

revision = "h86c0d2f7a97"
down_revision = "g75b9c1e6f86"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assessment_questions", sa.Column("topic_ids", sa.JSON(), server_default="[]", nullable=False))
    op.add_column("assessment_questions", sa.Column("topic_weights", sa.JSON(), server_default="{}", nullable=False))
    op.alter_column("weakness_diagnoses", "unit_id", existing_type=sa.Uuid(), nullable=True)
    op.alter_column("improvement_recommendations", "unit_id", existing_type=sa.Uuid(), nullable=True)
    op.alter_column("study_plan_items", "unit_id", existing_type=sa.Uuid(), nullable=True)
    op.create_unique_constraint("uq_weakness_diagnosis_result_topic_category", "weakness_diagnoses",
                                ["result_id", "topic_id", "category"])
    op.alter_column("tutor_sessions", "active_unit_id", existing_type=sa.Uuid(), nullable=True)
    op.add_column("tutor_sessions", sa.Column("active_topic_id", sa.Uuid(), nullable=True))
    op.create_index("ix_tutor_sessions_active_topic_id", "tutor_sessions", ["active_topic_id"])
    op.create_foreign_key("fk_tutor_sessions_active_topic", "tutor_sessions", "textbook_topics",
                          ["active_topic_id"], ["id"], ondelete="RESTRICT")
    op.create_table("tutor_session_topic_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_topic_id", sa.Uuid(), sa.ForeignKey("textbook_topics.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("to_topic_id", sa.Uuid(), sa.ForeignKey("textbook_topics.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("session_id", "request_key", name="uq_tutor_topic_switch_request"))
    op.create_index("ix_tutor_session_topic_events_session_id", "tutor_session_topic_events", ["session_id"])
    op.alter_column("tutor_learner_context_logs", "active_unit_id", existing_type=sa.Uuid(), nullable=True)
    op.add_column("tutor_learner_context_logs", sa.Column("active_topic_id", sa.Uuid(), nullable=True))
    op.create_index("ix_tutor_learner_context_logs_active_topic_id", "tutor_learner_context_logs", ["active_topic_id"])
    op.create_foreign_key("fk_tutor_context_active_topic", "tutor_learner_context_logs", "textbook_topics",
                          ["active_topic_id"], ["id"], ondelete="RESTRICT")
    for table in ("tutor_practices", "tutor_signals"):
        op.alter_column(table, "unit_id", existing_type=sa.Uuid(), nullable=True)
        op.add_column(table, sa.Column("topic_id", sa.Uuid(), nullable=True))
        op.create_index(f"ix_{table}_topic_id", table, ["topic_id"])
        op.create_foreign_key(f"fk_{table}_topic", table, "textbook_topics", ["topic_id"], ["id"], ondelete="RESTRICT")


def downgrade():
    for table in ("tutor_signals", "tutor_practices"):
        op.drop_constraint(f"fk_{table}_topic", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_topic_id", table_name=table)
        op.drop_column(table, "topic_id")
        op.alter_column(table, "unit_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_constraint("fk_tutor_context_active_topic", "tutor_learner_context_logs", type_="foreignkey")
    op.drop_index("ix_tutor_learner_context_logs_active_topic_id", table_name="tutor_learner_context_logs")
    op.drop_column("tutor_learner_context_logs", "active_topic_id")
    op.alter_column("tutor_learner_context_logs", "active_unit_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_table("tutor_session_topic_events")
    op.drop_constraint("fk_tutor_sessions_active_topic", "tutor_sessions", type_="foreignkey")
    op.drop_index("ix_tutor_sessions_active_topic_id", table_name="tutor_sessions")
    op.drop_column("tutor_sessions", "active_topic_id")
    op.alter_column("tutor_sessions", "active_unit_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_constraint("uq_weakness_diagnosis_result_topic_category", "weakness_diagnoses", type_="unique")
    op.alter_column("study_plan_items", "unit_id", existing_type=sa.Uuid(), nullable=False)
    op.alter_column("improvement_recommendations", "unit_id", existing_type=sa.Uuid(), nullable=False)
    op.alter_column("weakness_diagnoses", "unit_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_column("assessment_questions", "topic_weights")
    op.drop_column("assessment_questions", "topic_ids")
