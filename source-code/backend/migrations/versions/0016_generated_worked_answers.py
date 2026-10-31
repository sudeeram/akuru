"""Private, versioned generated worked-answer drafts and job state."""
from alembic import op
import sqlalchemy as sa
revision = "0016_generated_worked_answers"
down_revision = "0015_drawing_submissions"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_assessment_interaction_kind", "assessment_interactions", type_="check")
    op.create_check_constraint("ck_assessment_interaction_kind", "assessment_interactions", "kind IN ('hint','worked_answer')")
    op.create_table("generated_worked_answers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("official_paper_review_questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("source_manifest", sa.JSON(), nullable=False),
        sa.Column("graph_input", sa.JSON(), nullable=False),
        sa.Column("solution", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("provenance", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("assets", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(24), nullable=False, server_default="queued"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_code", sa.String(100)),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('queued','processing','awaiting_review','approved','rejected','stale','failed','superseded')", name="ck_worked_answer_status"),
        sa.CheckConstraint("revision > 0", name="ck_worked_answer_revision"))
    op.create_index("ix_generated_worked_answers_question_id", "generated_worked_answers", ["question_id"])


def downgrade():
    # Preserve assistance evidence when reverting to the older interaction schema.
    op.execute("UPDATE assessment_interactions SET kind='hint' WHERE kind='worked_answer'")
    op.drop_constraint("ck_assessment_interaction_kind", "assessment_interactions", type_="check")
    op.create_check_constraint("ck_assessment_interaction_kind", "assessment_interactions", "kind IN ('hint')")
    op.drop_table("generated_worked_answers")
