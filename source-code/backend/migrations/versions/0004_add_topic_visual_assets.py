"""add reviewed topic visual assets

Revision ID: 0004_topic_visual_assets
Revises: 63f925e43652
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_topic_visual_assets"
down_revision: Union[str, None] = "63f925e43652"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("textbook_topic_visual_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_ref", sa.String(length=56), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("document_asset_id", sa.Uuid(), nullable=False),
        sa.Column("block_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="selected", nullable=False),
        sa.Column("caption", sa.Text(), server_default="", nullable=False),
        sa.Column("alt_text", sa.Text(), server_default="", nullable=False),
        sa.Column("selected_by", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("selected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('selected','approved','rejected')", name="ck_topic_visual_asset_status"),
        sa.ForeignKeyConstraint(["block_id"], ["document_blocks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_asset_id"], ["document_assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["selected_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["topic_id"], ["textbook_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("public_ref"),
        sa.UniqueConstraint("topic_id", "document_asset_id", name="uq_topic_visual_asset"))
    op.create_index(op.f("ix_textbook_topic_visual_assets_topic_id"), "textbook_topic_visual_assets", ["topic_id"])
    op.create_index(op.f("ix_textbook_topic_visual_assets_document_version_id"), "textbook_topic_visual_assets", ["document_version_id"])
    op.create_index(op.f("ix_textbook_topic_visual_assets_document_asset_id"), "textbook_topic_visual_assets", ["document_asset_id"])
    op.create_index(op.f("ix_textbook_topic_visual_assets_status"), "textbook_topic_visual_assets", ["status"])

def downgrade() -> None:
    op.drop_table("textbook_topic_visual_assets")
