"""add tutor evaluation and staged release gates

Revision ID: b72fa92d4e11
Revises: e4c21b793f60
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b72fa92d4e11"
down_revision: Union[str, None] = "e4c21b793f60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_constraint("uq_evaluation_corpus_subject_version", "evaluation_corpora", type_="unique")
    op.add_column("evaluation_corpora", sa.Column("workflow", sa.String(32), server_default="assessment", nullable=False))
    op.create_index("ix_evaluation_corpora_workflow", "evaluation_corpora", ["workflow"])
    op.create_check_constraint("ck_evaluation_corpus_workflow", "evaluation_corpora", "workflow IN ('assessment','tutor')")
    op.create_unique_constraint("uq_evaluation_corpus_subject_workflow_version", "evaluation_corpora", ["subject_id", "workflow", "version_number"])

    for name, default in (("workflow", "assessment"), ("modality", "assessment"), ("environment", "ci")):
        op.add_column("evaluation_runs", sa.Column(name, sa.String(32 if name == "workflow" else 16), server_default=default, nullable=False))
        op.create_index(f"ix_evaluation_runs_{name}", "evaluation_runs", [name])
    op.create_check_constraint("ck_evaluation_run_workflow", "evaluation_runs", "workflow IN ('assessment','tutor')")
    op.create_check_constraint("ck_evaluation_run_modality", "evaluation_runs", "modality IN ('assessment','text','voice','tools')")
    op.create_check_constraint("ck_evaluation_run_environment", "evaluation_runs", "environment IN ('ci','staging')")

    op.drop_constraint("ck_evaluation_release_workflow", "evaluation_releases", type_="check")
    op.add_column("evaluation_releases", sa.Column("audience", sa.String(20), server_default="students", nullable=False))
    op.create_check_constraint("ck_evaluation_release_workflow", "evaluation_releases", "workflow IN ('assessment_feedback','content_publication','tutor_text','tutor_voice','tutor_tools','tutor_learner_context','tutor_next_unit','tutor_sources','tutor_practice','tutor_visuals')")
    op.create_check_constraint("ck_evaluation_release_audience", "evaluation_releases", "audience IN ('admin_testing','parent_pilot','students')")


def downgrade():
    op.drop_constraint("ck_evaluation_release_audience", "evaluation_releases", type_="check")
    op.drop_constraint("ck_evaluation_release_workflow", "evaluation_releases", type_="check")
    op.drop_column("evaluation_releases", "audience")
    op.create_check_constraint("ck_evaluation_release_workflow", "evaluation_releases", "workflow IN ('assessment_feedback','content_publication')")
    for constraint in ("ck_evaluation_run_environment", "ck_evaluation_run_modality", "ck_evaluation_run_workflow"):
        op.drop_constraint(constraint, "evaluation_runs", type_="check")
    for name in ("environment", "modality", "workflow"):
        op.drop_index(f"ix_evaluation_runs_{name}", table_name="evaluation_runs")
        op.drop_column("evaluation_runs", name)
    op.drop_constraint("uq_evaluation_corpus_subject_workflow_version", "evaluation_corpora", type_="unique")
    op.drop_constraint("ck_evaluation_corpus_workflow", "evaluation_corpora", type_="check")
    op.drop_index("ix_evaluation_corpora_workflow", table_name="evaluation_corpora")
    op.drop_column("evaluation_corpora", "workflow")
    op.create_unique_constraint("uq_evaluation_corpus_subject_version", "evaluation_corpora", ["subject_id", "version_number"])
