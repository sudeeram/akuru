"""add independently published topic content versions

Revision ID: f64a8b0d5e75
Revises: e53f7a9c4d64
"""
from alembic import op
import sqlalchemy as sa

revision = "f64a8b0d5e75"
down_revision = "e53f7a9c4d64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("textbook_topic_content_versions",
        sa.Column("id", sa.UUID(), nullable=False), sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("topic_id", sa.UUID(), nullable=False), sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), server_default="published", nullable=False),
        sa.Column("source_manifest", sa.JSON(), nullable=False), sa.Column("extraction_manifest", sa.JSON(), nullable=False),
        sa.Column("published_by", sa.UUID(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("version_number > 0", name="ck_topic_content_version_number"),
        sa.CheckConstraint("status IN ('published','superseded')", name="ck_topic_content_version_status"),
        sa.ForeignKeyConstraint(["topic_id"], ["textbook_topics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("public_ref"),
        sa.UniqueConstraint("topic_id", "version_number", name="uq_topic_content_version"))
    op.create_index("ix_textbook_topic_content_versions_topic_id", "textbook_topic_content_versions", ["topic_id"])
    op.create_index("ix_textbook_topic_content_versions_status", "textbook_topic_content_versions", ["status"])
    op.create_table("textbook_topic_content_sources",
        sa.Column("content_version_id", sa.UUID(), nullable=False),
        sa.Column("document_version_id", sa.UUID(), nullable=False), sa.Column("role", sa.String(24), nullable=False),
        sa.Column("extraction_version", sa.String(80), nullable=False),
        sa.CheckConstraint("role IN ('primary','supporting','reference')", name="ck_topic_content_source_role"),
        sa.ForeignKeyConstraint(["content_version_id"], ["textbook_topic_content_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("content_version_id", "document_version_id"))
    op.add_column("retrieval_chunks", sa.Column("topic_content_version_id", sa.UUID(), nullable=True))
    op.create_index("ix_retrieval_chunks_topic_content_version_id", "retrieval_chunks", ["topic_content_version_id"])
    op.create_foreign_key("fk_retrieval_chunk_topic_content_version", "retrieval_chunks", "textbook_topic_content_versions",
                          ["topic_content_version_id"], ["id"], ondelete="CASCADE")
    op.alter_column("retrieval_chunks", "unit_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("retrieval_chunks", "unit_id", existing_type=sa.UUID(), nullable=False)
    op.drop_constraint("fk_retrieval_chunk_topic_content_version", "retrieval_chunks", type_="foreignkey")
    op.drop_index("ix_retrieval_chunks_topic_content_version_id", table_name="retrieval_chunks")
    op.drop_column("retrieval_chunks", "topic_content_version_id")
    op.drop_table("textbook_topic_content_sources")
    op.drop_index("ix_textbook_topic_content_versions_status", table_name="textbook_topic_content_versions")
    op.drop_index("ix_textbook_topic_content_versions_topic_id", table_name="textbook_topic_content_versions")
    op.drop_table("textbook_topic_content_versions")
