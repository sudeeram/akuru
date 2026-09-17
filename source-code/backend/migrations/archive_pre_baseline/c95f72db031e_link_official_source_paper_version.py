"""link official source paper version

Revision ID: c95f72db031e
Revises: b84e61ca920d
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c95f72db031e"
down_revision: Union[str, None] = "b84e61ca920d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("official_material_versions", sa.Column("source_paper_version_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_official_material_source_paper_version", "official_material_versions", "official_material_versions", ["source_paper_version_id"], ["id"], ondelete="RESTRICT")


def downgrade() -> None:
    op.drop_constraint("fk_official_material_source_paper_version", "official_material_versions", type_="foreignkey")
    op.drop_column("official_material_versions", "source_paper_version_id")
