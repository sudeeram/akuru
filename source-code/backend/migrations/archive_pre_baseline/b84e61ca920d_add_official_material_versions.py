"""add official material versions

Revision ID: b84e61ca920d
Revises: a72d4f318c60
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b84e61ca920d"
down_revision: Union[str, None] = "a72d4f318c60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "official_material_versions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("source_document_version_id", sa.Uuid(), nullable=False), sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False), sa.Column("course_id", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False), sa.Column("source_paper_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("inventory_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completeness_confirmed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False), sa.Column("published_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True), sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("kind IN ('past_paper','mark_scheme','examiner_report')", name="ck_official_material_kind"),
        sa.CheckConstraint("status IN ('draft','published','superseded')", name="ck_official_material_status"),
        sa.CheckConstraint("version_number > 0 AND inventory_count >= 0", name="ck_official_material_counts"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_version_id"], ["document_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_paper_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("document_id", "version_number", name="uq_official_material_version"),
    )
    op.create_index(op.f("ix_official_material_versions_document_id"), "official_material_versions", ["document_id"])
    op.create_table(
        "official_question_versions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("material_version_id", sa.Uuid(), nullable=False),
        sa.Column("question_number", sa.String(40), nullable=False), sa.Column("parent_number", sa.String(40), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False), sa.Column("shared_stem", sa.Text(), server_default="", nullable=False),
        sa.Column("marks", sa.Integer(), nullable=False), sa.Column("equations", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("asset_ids", sa.JSON(), server_default="[]", nullable=False), sa.Column("source_locations", sa.JSON(), server_default="[]", nullable=False),
        sa.CheckConstraint("marks > 0", name="ck_official_question_marks"),
        sa.ForeignKeyConstraint(["material_version_id"], ["official_material_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("material_version_id", "question_number", name="uq_official_question_number"),
    )
    op.create_index(op.f("ix_official_question_versions_material_version_id"), "official_question_versions", ["material_version_id"])
    op.create_table(
        "mark_scheme_entry_versions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("material_version_id", sa.Uuid(), nullable=False),
        sa.Column("question_number", sa.String(40), nullable=False), sa.Column("max_marks", sa.Integer(), nullable=False),
        sa.Column("marking_points", sa.JSON(), server_default="[]", nullable=False), sa.Column("alternatives", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("source_locations", sa.JSON(), server_default="[]", nullable=False),
        sa.CheckConstraint("max_marks > 0", name="ck_mark_scheme_entry_marks"),
        sa.ForeignKeyConstraint(["material_version_id"], ["official_material_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("material_version_id", "question_number", name="uq_mark_scheme_entry_number"),
    )
    op.create_index(op.f("ix_mark_scheme_entry_versions_material_version_id"), "mark_scheme_entry_versions", ["material_version_id"])
    op.create_table(
        "examiner_comment_versions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("material_version_id", sa.Uuid(), nullable=False),
        sa.Column("question_number", sa.String(40), nullable=False),
        sa.Column("common_mistakes", sa.JSON(), server_default="[]", nullable=False), sa.Column("advice", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("source_locations", sa.JSON(), server_default="[]", nullable=False),
        sa.ForeignKeyConstraint(["material_version_id"], ["official_material_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("material_version_id", "question_number", name="uq_examiner_comment_number"),
    )
    op.create_index(op.f("ix_examiner_comment_versions_material_version_id"), "examiner_comment_versions", ["material_version_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_examiner_comment_versions_material_version_id"), table_name="examiner_comment_versions")
    op.drop_table("examiner_comment_versions")
    op.drop_index(op.f("ix_mark_scheme_entry_versions_material_version_id"), table_name="mark_scheme_entry_versions")
    op.drop_table("mark_scheme_entry_versions")
    op.drop_index(op.f("ix_official_question_versions_material_version_id"), table_name="official_question_versions")
    op.drop_table("official_question_versions")
    op.drop_index(op.f("ix_official_material_versions_document_id"), table_name="official_material_versions")
    op.drop_table("official_material_versions")
