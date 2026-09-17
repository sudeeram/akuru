"""add reviewed textbook versions

Revision ID: e8b01a76d9c4
Revises: d47e9b2a61f0
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e8b01a76d9c4"
down_revision: Union[str, None] = "d47e9b2a61f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "textbook_content_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("source_document_version_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("edition", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("published_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("version_number > 0", name="ck_textbook_content_version_number"),
        sa.CheckConstraint("status IN ('draft','published','superseded')", name="ck_textbook_content_version_status"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_document_version_id"], ["document_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_number", name="uq_textbook_content_version"),
    )
    op.create_index(op.f("ix_textbook_content_versions_document_id"), "textbook_content_versions", ["document_id"])
    op.create_table(
        "textbook_unit_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content_version_id", sa.Uuid(), nullable=False),
        sa.Column("unit_code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("start_page", sa.Integer(), nullable=False),
        sa.Column("end_page", sa.Integer(), nullable=False),
        sa.Column("sections", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("definitions", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("concepts", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("equations", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("examples", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("diagrams", sa.JSON(), server_default="[]", nullable=False),
        sa.CheckConstraint("sequence > 0", name="ck_textbook_unit_version_sequence"),
        sa.CheckConstraint("start_page > 0 AND end_page >= start_page", name="ck_textbook_unit_version_pages"),
        sa.ForeignKeyConstraint(["content_version_id"], ["textbook_content_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_version_id", "unit_code", name="uq_textbook_unit_version_code"),
    )
    op.create_index(op.f("ix_textbook_unit_versions_content_version_id"), "textbook_unit_versions", ["content_version_id"])
    op.add_column("textbook_units", sa.Column("content_version_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(None, "textbook_units", "textbook_content_versions", ["content_version_id"], ["id"], ondelete="RESTRICT")
    op.create_index(op.f("ix_textbook_units_content_version_id"), "textbook_units", ["content_version_id"])
    op.drop_constraint("uq_textbook_unit_code", "textbook_units", type_="unique")
    op.create_unique_constraint("uq_textbook_unit_code", "textbook_units", ["textbook_id", "content_version_id", "unit_code"])


def downgrade() -> None:
    op.drop_constraint("uq_textbook_unit_code", "textbook_units", type_="unique")
    op.create_unique_constraint("uq_textbook_unit_code", "textbook_units", ["textbook_id", "unit_code"])
    op.drop_index(op.f("ix_textbook_units_content_version_id"), table_name="textbook_units")
    op.drop_constraint(None, "textbook_units", type_="foreignkey")
    op.drop_column("textbook_units", "content_version_id")
    op.drop_index(op.f("ix_textbook_unit_versions_content_version_id"), table_name="textbook_unit_versions")
    op.drop_table("textbook_unit_versions")
    op.drop_index(op.f("ix_textbook_content_versions_document_id"), table_name="textbook_content_versions")
    op.drop_table("textbook_content_versions")
