"""Admin-only official-paper review workspaces

Revision ID: 0009_paper_review
Revises: 0008_password_lifecycle
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_paper_review"
down_revision = "0008_password_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("official_paper_review_workspaces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("paper_document_id", sa.Uuid(), sa.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("paper_version_id", sa.Uuid(), sa.ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scheme_document_id", sa.Uuid(), sa.ForeignKey("documents.id", ondelete="RESTRICT")),
        sa.Column("scheme_version_id", sa.Uuid(), sa.ForeignKey("document_versions.id", ondelete="RESTRICT")),
        sa.Column("report_document_id", sa.Uuid(), sa.ForeignKey("documents.id", ondelete="RESTRICT")),
        sa.Column("report_version_id", sa.Uuid(), sa.ForeignKey("document_versions.id", ondelete="RESTRICT")),
        sa.Column("expected_question_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("expected_question_count >= 0", name="ck_official_review_expected_count"))
    op.create_table("official_paper_review_questions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("official_paper_review_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.String(40), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(24), nullable=False, server_default="unreviewed"),
        sa.Column("review_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("revision > 0", name="ck_official_review_question_revision"),
        sa.CheckConstraint("status IN ('unreviewed','needs_correction','ready_for_approval','approved','excluded')", name="ck_official_review_question_status"),
        sa.UniqueConstraint("workspace_id", "number", name="uq_official_review_question_number"))
    op.create_index("ix_official_paper_review_questions_workspace_id", "official_paper_review_questions", ["workspace_id"])


def downgrade():
    op.drop_table("official_paper_review_questions")
    op.drop_table("official_paper_review_workspaces")
