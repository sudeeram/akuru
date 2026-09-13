"""add immutable assessments

Revision ID: 6b51f918c2e0
Revises: 09c92e17f54a
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "6b51f918c2e0"
down_revision: Union[str, None] = "09c92e17f54a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("assessment_blueprints",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("name", sa.String(160), nullable=False),
        sa.Column("course_id", sa.String(32), nullable=False), sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False), sa.Column("term", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(24), nullable=False), sa.Column("target_marks", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False), sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("skills", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("difficulty_profile", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(16), server_default="draft", nullable=False), sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("grade IN (10, 11) AND term IN (1, 2, 3)", name="ck_assessment_blueprint_period"),
        sa.CheckConstraint("mode IN ('practice','official_paper','mock')", name="ck_assessment_blueprint_mode"),
        sa.CheckConstraint("target_marks > 0 AND duration_minutes > 0 AND question_count > 0", name="ck_assessment_blueprint_values"),
        sa.CheckConstraint("status IN ('draft','published','retired')", name="ck_assessment_blueprint_status"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_assessment_blueprints_course_id", "assessment_blueprints", ["course_id"])
    op.create_index("ix_assessment_blueprints_subject_id", "assessment_blueprints", ["subject_id"])
    op.create_index("ix_assessment_blueprints_status", "assessment_blueprints", ["status"])
    op.create_table("assessments",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False), sa.Column("mode", sa.String(24), nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("blueprint_id", sa.Uuid(), nullable=True), sa.Column("official_paper_version_id", sa.Uuid(), nullable=True),
        sa.Column("curriculum_snapshot_id", sa.Uuid(), nullable=False), sa.Column("title", sa.String(200), nullable=False),
        sa.Column("target_marks", sa.Integer(), nullable=False), sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("skills", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("difficulty_profile", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False), sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_key", sa.String(100), nullable=True),
        sa.CheckConstraint("mode IN ('practice','official_paper','mock')", name="ck_assessment_mode"),
        sa.CheckConstraint("status IN ('active','submitted','expired')", name="ck_assessment_status"),
        sa.CheckConstraint("target_marks > 0 AND duration_minutes > 0", name="ck_assessment_values"),
        sa.ForeignKeyConstraint(["blueprint_id"], ["assessment_blueprints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["curriculum_snapshot_id"], ["assessment_curriculum_snapshots.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["official_paper_version_id"], ["official_material_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "submission_key", name="uq_assessment_submission_key"))
    for col in ("student_id", "subject_id", "status", "ends_at"): op.create_index(f"ix_assessments_{col}", "assessments", [col])
    op.create_table("assessment_questions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False), sa.Column("source_question_version_id", sa.Uuid(), nullable=False),
        sa.Column("source_document_version_id", sa.Uuid(), nullable=False), sa.Column("question_number", sa.String(40), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False), sa.Column("shared_stem", sa.Text(), server_default="", nullable=False),
        sa.Column("marks", sa.Integer(), nullable=False), sa.Column("equations", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("asset_ids", sa.JSON(), server_default="[]", nullable=False), sa.Column("source_locations", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("rubric", sa.JSON(), server_default="{}", nullable=False), sa.Column("unit_ids", sa.JSON(), nullable=False),
        sa.Column("skills", sa.JSON(), server_default="[]", nullable=False), sa.Column("difficulty", sa.String(24), server_default="mixed", nullable=False),
        sa.CheckConstraint("sequence > 0 AND marks > 0", name="ck_assessment_question_values"),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_version_id"], ["document_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_question_version_id"], ["official_question_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("assessment_id", "sequence", name="uq_assessment_question_sequence"),
        sa.UniqueConstraint("assessment_id", "source_question_version_id", name="uq_assessment_question_source"))
    op.create_index("ix_assessment_questions_assessment_id", "assessment_questions", ["assessment_id"])
    op.create_table("assessment_answers",
        sa.Column("assessment_id", sa.Uuid(), nullable=False), sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("answer_text", sa.Text(), server_default="", nullable=False), sa.Column("file_id", sa.String(120), nullable=True),
        sa.Column("save_revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("save_revision > 0", name="ck_assessment_answer_revision"),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["assessment_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("assessment_id", "question_id"),
        sa.UniqueConstraint("assessment_id", "idempotency_key", name="uq_assessment_answer_idempotency"))

def downgrade() -> None:
    op.drop_table("assessment_answers"); op.drop_table("assessment_questions"); op.drop_table("assessments"); op.drop_table("assessment_blueprints")
