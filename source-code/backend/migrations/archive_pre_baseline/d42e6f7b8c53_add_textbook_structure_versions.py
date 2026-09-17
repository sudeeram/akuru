"""add immutable textbook structure versions

Revision ID: d42e6f7b8c53
Revises: c31d9e5a7b42
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d42e6f7b8c53"
down_revision: Union[str, None] = "c31d9e5a7b42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "textbook_structure_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("textbook_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("published_by", sa.Uuid(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("version_number > 0", name="ck_textbook_structure_version"),
        sa.ForeignKeyConstraint(["textbook_id"], ["textbooks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("textbook_id", "version_number", name="uq_textbook_structure_version"),
    )
    op.create_index("ix_textbook_structure_versions_textbook_id", "textbook_structure_versions", ["textbook_id"])


def downgrade():
    op.drop_index("ix_textbook_structure_versions_textbook_id", table_name="textbook_structure_versions")
    op.drop_table("textbook_structure_versions")
