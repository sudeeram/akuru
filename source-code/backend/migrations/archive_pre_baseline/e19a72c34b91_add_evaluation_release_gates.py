"""add evaluation corpora, runs and release gates

Revision ID: e19a72c34b91
Revises: c72d8e4f19a1
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e19a72c34b91"
down_revision: Union[str, None] = "c72d8e4f19a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_table("evaluation_corpora",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False), sa.Column("name", sa.String(180), nullable=False),
        sa.Column("cases", sa.JSON(), nullable=False), sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False), sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("version_number > 0", name="ck_evaluation_corpus_version"),
        sa.CheckConstraint("status IN ('draft','approved','retired')", name="ck_evaluation_corpus_status"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("subject_id", "version_number", name="uq_evaluation_corpus_subject_version"))
    op.create_index("ix_evaluation_corpora_subject_id", "evaluation_corpora", ["subject_id"])
    op.create_index("ix_evaluation_corpora_status", "evaluation_corpora", ["status"])
    op.create_table("evaluation_runs",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("corpus_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False), sa.Column("candidate_model", sa.String(120), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False), sa.Column("observations_hash", sa.String(64), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False), sa.Column("thresholds", sa.JSON(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False), sa.Column("failure_reasons", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["corpus_id"], ["evaluation_corpora.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"))
    for column in ("corpus_id", "subject_id", "passed", "created_at"):
        op.create_index(f"ix_evaluation_runs_{column}", "evaluation_runs", [column])
    op.create_table("evaluation_releases",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("workflow", sa.String(32), nullable=False), sa.Column("mode", sa.String(20), server_default="review_required", nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True), sa.Column("confidence_threshold", sa.Float(), server_default="0.85", nullable=False),
        sa.Column("activated_by", sa.Uuid(), nullable=False), sa.Column("activated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("workflow IN ('assessment_feedback','content_publication')", name="ck_evaluation_release_workflow"),
        sa.CheckConstraint("mode IN ('review_required','automatic')", name="ck_evaluation_release_mode"),
        sa.CheckConstraint("confidence_threshold BETWEEN 0 AND 1", name="ck_evaluation_release_confidence"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["run_id"], ["evaluation_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["activated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("subject_id", "workflow", name="uq_evaluation_release_subject_workflow"))
    op.create_index("ix_evaluation_releases_subject_id", "evaluation_releases", ["subject_id"])

def downgrade():
    op.drop_table("evaluation_releases")
    op.drop_table("evaluation_runs")
    op.drop_table("evaluation_corpora")
