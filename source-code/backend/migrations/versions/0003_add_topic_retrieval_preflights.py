"""add persisted topic retrieval preflights

Revision ID: 0003_retrieval_preflight
Revises: 0002_visual_reference
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_retrieval_preflight"
down_revision = "0002_visual_reference"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("topic_retrieval_preflights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("content_version_id", sa.Uuid(), nullable=False),
        sa.Column("queries", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["textbook_topics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["content_version_id"], ["textbook_topic_content_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("public_ref"),
    )
    op.create_index("ix_topic_retrieval_preflights_topic_id", "topic_retrieval_preflights", ["topic_id"])
    op.create_index("ix_topic_retrieval_preflights_content_version_id", "topic_retrieval_preflights", ["content_version_id"])
    op.create_index("ix_topic_retrieval_preflights_passed", "topic_retrieval_preflights", ["passed"])
    op.create_index("ix_topic_retrieval_preflights_created_at", "topic_retrieval_preflights", ["created_at"])


def downgrade() -> None:
    op.drop_table("topic_retrieval_preflights")
