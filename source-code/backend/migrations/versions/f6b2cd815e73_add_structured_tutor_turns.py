"""add structured tutor turn provenance

Revision ID: f6b2cd815e73
Revises: e5a1bc704d62
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6b2cd815e73"
down_revision: Union[str, None] = "e5a1bc704d62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("tutor_turns", sa.Column("response_data", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("tutor_turns", sa.Column("operation_id", sa.Uuid(), nullable=True))
    op.add_column("tutor_turns", sa.Column("provider", sa.String(40), nullable=True))
    op.add_column("tutor_turns", sa.Column("model", sa.String(120), nullable=True))
    op.add_column("tutor_turns", sa.Column("prompt_name", sa.String(80), nullable=True))
    op.add_column("tutor_turns", sa.Column("prompt_version", sa.String(40), nullable=True))
    op.create_index("ix_tutor_turns_operation_id", "tutor_turns", ["operation_id"])


def downgrade():
    op.drop_index("ix_tutor_turns_operation_id", table_name="tutor_turns")
    for column in ("prompt_version", "prompt_name", "model", "provider", "operation_id", "response_data"):
        op.drop_column("tutor_turns", column)
