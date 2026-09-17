"""add versioned curriculum plans

Revision ID: a72d4f318c60
Revises: f91c8e30b2a7
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a72d4f318c60"
down_revision: Union[str, None] = "f91c8e30b2a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "curriculum_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("textbook_content_version_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("published_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("version_number > 0", name="ck_curriculum_plan_version"),
        sa.CheckConstraint("status IN ('draft','published','superseded')", name="ck_curriculum_plan_status"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["textbook_content_version_id"], ["textbook_content_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "subject_id", "version_number", name="uq_curriculum_plan_version"),
    )
    op.create_index(op.f("ix_curriculum_plans_subject_id"), "curriculum_plans", ["subject_id"])
    op.create_table(
        "curriculum_plan_units",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("term", sa.Integer(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("grade IN (10, 11)", name="ck_curriculum_plan_unit_grade"),
        sa.CheckConstraint("term IN (1, 2, 3)", name="ck_curriculum_plan_unit_term"),
        sa.ForeignKeyConstraint(["plan_id"], ["curriculum_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["textbook_units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("plan_id", "grade", "term", "unit_id"),
    )
    op.create_table(
        "assessment_curriculum_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_ref", sa.String(120), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("term", sa.Integer(), nullable=False),
        sa.Column("covered_unit_ids", sa.JSON(), nullable=False),
        sa.Column("progression_periods", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("grade IN (10, 11)", name="ck_assessment_snapshot_grade"),
        sa.CheckConstraint("term IN (1, 2, 3)", name="ck_assessment_snapshot_term"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["plan_id"], ["curriculum_plans.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_ref"),
    )
    op.create_index(op.f("ix_assessment_curriculum_snapshots_student_id"), "assessment_curriculum_snapshots", ["student_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_assessment_curriculum_snapshots_student_id"), table_name="assessment_curriculum_snapshots")
    op.drop_table("assessment_curriculum_snapshots")
    op.drop_table("curriculum_plan_units")
    op.drop_index(op.f("ix_curriculum_plans_subject_id"), table_name="curriculum_plans")
    op.drop_table("curriculum_plans")
