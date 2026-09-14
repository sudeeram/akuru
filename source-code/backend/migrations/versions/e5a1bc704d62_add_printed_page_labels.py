"""add printed page labels

Revision ID: e5a1bc704d62
Revises: df4c92a10b33
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5a1bc704d62"
down_revision: Union[str, None] = "df4c92a10b33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("document_pages", sa.Column("printed_page_label", sa.String(40), nullable=True))


def downgrade():
    op.drop_column("document_pages", "printed_page_label")
