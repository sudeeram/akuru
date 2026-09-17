"""add textbook unit chapter

Revision ID: f91c8e30b2a7
Revises: e8b01a76d9c4
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f91c8e30b2a7"
down_revision: Union[str, None] = "e8b01a76d9c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "textbook_unit_versions",
        sa.Column("chapter", sa.String(length=240), server_default="", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("textbook_unit_versions", "chapter")
