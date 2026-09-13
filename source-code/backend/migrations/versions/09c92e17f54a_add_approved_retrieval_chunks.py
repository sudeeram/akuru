"""add approved retrieval chunks

Revision ID: 09c92e17f54a
Revises: d96fa2173b40
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR

revision: str = "09c92e17f54a"
down_revision: Union[str, None] = "d96fa2173b40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "retrieval_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("textbook_content_version_id", sa.Uuid(), nullable=True),
        sa.Column("official_material_version_id", sa.Uuid(), nullable=True),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_item_id", sa.Uuid(), nullable=False),
        sa.Column("source_ordinal", sa.Integer(), server_default="0", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("bounding_box", sa.JSON(), nullable=False),
        sa.Column("source_asset_id", sa.Uuid(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding_model", sa.String(120), nullable=False),
        sa.Column("embedding_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("embedding", VECTOR(dim=256), nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("source_type IN ('textbook_section','marking_point','examiner_guidance')", name="ck_retrieval_chunk_source_type"),
        sa.CheckConstraint("status IN ('active','superseded')", name="ck_retrieval_chunk_status"),
        sa.CheckConstraint("page_number > 0 AND embedding_version > 0", name="ck_retrieval_chunk_values"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["official_material_version_id"], ["official_material_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_asset_id"], ["document_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["textbook_content_version_id"], ["textbook_content_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["textbook_units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_type", "source_item_id", "source_ordinal", "embedding_version", name="uq_retrieval_chunk_source_version"),
    )
    for column in ("document_id", "document_version_id", "textbook_content_version_id", "official_material_version_id", "unit_id", "course_id", "subject_id", "source_type", "source_item_id", "status"):
        op.create_index(f"ix_retrieval_chunks_{column}", "retrieval_chunks", [column])
    op.execute("CREATE INDEX ix_retrieval_chunks_embedding_hnsw ON retrieval_chunks USING hnsw (embedding vector_cosine_ops)")

def downgrade() -> None:
    op.drop_table("retrieval_chunks")
