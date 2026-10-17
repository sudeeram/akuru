"""Preserve reviewed subpart visual placements in published and frozen questions.

Revision ID: 0010_visual_placements
Revises: 0009_paper_review
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_visual_placements"
down_revision = "0009_paper_review"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("official_question_versions", sa.Column("visual_placements", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("assessment_questions", sa.Column("visual_placements", sa.JSON(), nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("assessment_questions", "visual_placements")
    op.drop_column("official_question_versions", "visual_placements")
