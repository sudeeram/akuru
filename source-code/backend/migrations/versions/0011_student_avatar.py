"""Persist optional versioned Student avatar selections.

Revision ID: 0011_student_avatar
Revises: 0010_visual_placements
"""
from alembic import op
import sqlalchemy as sa

revision = '0011_student_avatar'
down_revision = '0010_visual_placements'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('student_profiles', sa.Column('avatar_config', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('student_profiles', 'avatar_config')
