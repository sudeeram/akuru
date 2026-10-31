"""Append-only accuracy assessments and source/model provenance."""
from alembic import op
import sqlalchemy as sa

revision = "0017_official_question_analyses"
down_revision = "0016_generated_worked_answers"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("official_question_analyses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("official_paper_review_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(16), nullable=False),
        sa.Column("question_revision", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("source_manifest", sa.JSON(), nullable=False),
        sa.Column("analysis_data", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("question_id", "version_number", name="uq_official_question_analysis_version"),
        sa.CheckConstraint("version_number > 0 AND question_revision > 0", name="ck_official_question_analysis_version"),
        sa.CheckConstraint("stage IN ('extraction','accuracy')", name="ck_official_question_analysis_stage"))
    op.create_index("ix_official_question_analyses_question_id", "official_question_analyses", ["question_id"])


def downgrade():
    op.drop_table("official_question_analyses")
