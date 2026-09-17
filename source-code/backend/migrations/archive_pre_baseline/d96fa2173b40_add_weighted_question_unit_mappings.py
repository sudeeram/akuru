"""add weighted question unit mappings

Revision ID: d96fa2173b40
Revises: c95f72db031e
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d96fa2173b40"
down_revision: Union[str, None] = "c95f72db031e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("official_material_versions", sa.Column("textbook_content_version_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(None, "official_material_versions", "textbook_content_versions", ["textbook_content_version_id"], ["id"], ondelete="RESTRICT")
    op.execute("""
        UPDATE official_material_versions material
        SET textbook_content_version_id = (
            SELECT content.id FROM textbook_content_versions content
            WHERE content.course_id = material.course_id
              AND content.subject_id = material.subject_id
              AND content.status = 'published'
            ORDER BY content.version_number DESC LIMIT 1
        )
        WHERE material.kind = 'past_paper' AND material.textbook_content_version_id IS NULL
    """)
    op.execute("""
        UPDATE official_material_versions material
        SET textbook_content_version_id = paper.textbook_content_version_id
        FROM official_material_versions paper
        WHERE material.source_paper_version_id = paper.id
          AND material.textbook_content_version_id IS NULL
    """)
    op.add_column("official_question_versions", sa.Column("mapping_status", sa.String(20), server_default="pending", nullable=False))
    op.create_check_constraint("ck_official_question_mapping_status", "official_question_versions", "mapping_status IN ('pending','draft','confirmed')")
    op.create_table(
        "official_question_unit_mappings",
        sa.Column("question_version_id", sa.Uuid(), nullable=False), sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False), sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("suggestion_method", sa.String(40), nullable=True), sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), server_default="", nullable=False), sa.Column("confirmed_by", sa.Uuid(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("weight BETWEEN 1 AND 100", name="ck_official_question_unit_weight"),
        sa.CheckConstraint("status IN ('draft','confirmed')", name="ck_official_question_unit_status"),
        sa.CheckConstraint("confidence IS NULL OR confidence BETWEEN 0 AND 1", name="ck_official_question_unit_confidence"),
        sa.ForeignKeyConstraint(["question_version_id"], ["official_question_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["textbook_units.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("question_version_id", "unit_id"),
    )


def downgrade() -> None:
    op.drop_table("official_question_unit_mappings")
    op.drop_constraint("ck_official_question_mapping_status", "official_question_versions", type_="check")
    op.drop_column("official_question_versions", "mapping_status")
    op.drop_constraint(None, "official_material_versions", type_="foreignkey")
    op.drop_column("official_material_versions", "textbook_content_version_id")
