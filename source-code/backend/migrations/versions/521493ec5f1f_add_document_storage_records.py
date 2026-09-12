"""add document storage records

Revision ID: 521493ec5f1f
Revises: 1077b2ef7586
Create Date: 2026-09-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "521493ec5f1f"
down_revision: Union[str, None] = "1077b2ef7586"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("edition", sa.String(length=80), nullable=True))
    op.add_column("documents", sa.Column("publication_year", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("exam_session", sa.String(length=80), nullable=True))
    op.add_column("documents", sa.Column("component", sa.String(length=80), nullable=True))
    op.add_column("documents", sa.Column("variant", sa.String(length=80), nullable=True))
    op.add_column("documents", sa.Column("source_metadata", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("documents", sa.Column("size_bytes", sa.Integer(), server_default="0", nullable=False))
    op.add_column("documents", sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint("ck_documents_size_bytes", "documents", "size_bytes >= 0")
    op.create_check_constraint(
        "ck_documents_publication_year",
        "documents",
        "publication_year IS NULL OR publication_year BETWEEN 1900 AND 2100",
    )

    op.create_table(
        "document_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), server_default="uploaded", nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version_number > 0", name="ck_document_versions_number"),
        sa.CheckConstraint("size_bytes > 0", name="ck_document_versions_size"),
        sa.CheckConstraint("status IN ('uploaded','failed','removed')", name="ck_document_versions_status"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_number", name="uq_document_version_number"),
        sa.UniqueConstraint("object_key"),
        sa.UniqueConstraint("sha256"),
    )
    op.create_index(op.f("ix_document_versions_document_id"), "document_versions", ["document_id"])

    op.execute(sa.text("""
        INSERT INTO document_versions
            (id, document_id, version_number, original_filename, object_key, mime_type,
             sha256, size_bytes, status, uploaded_by, created_at)
        SELECT gen_random_uuid(), id, 1, original_filename, object_key, mime_type,
               sha256, GREATEST(size_bytes, 1), 'uploaded', uploaded_by, created_at
        FROM documents
    """))

    op.create_table(
        "document_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("asset_kind", sa.String(length=40), nullable=False),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.Column("asset_metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("size_bytes > 0", name="ck_document_assets_size"),
        sa.CheckConstraint("page_number IS NULL OR page_number > 0", name="ck_document_assets_page"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index(op.f("ix_document_assets_document_version_id"), "document_assets", ["document_version_id"])

    op.create_table(
        "document_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("event_data", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_events_actor_id"), "document_events", ["actor_id"])
    op.create_index(op.f("ix_document_events_created_at"), "document_events", ["created_at"])
    op.create_index(op.f("ix_document_events_document_id"), "document_events", ["document_id"])
    op.create_index(op.f("ix_document_events_document_version_id"), "document_events", ["document_version_id"])
    op.create_index(op.f("ix_document_events_event_type"), "document_events", ["event_type"])


def downgrade() -> None:
    op.drop_index(op.f("ix_document_events_event_type"), table_name="document_events")
    op.drop_index(op.f("ix_document_events_document_version_id"), table_name="document_events")
    op.drop_index(op.f("ix_document_events_document_id"), table_name="document_events")
    op.drop_index(op.f("ix_document_events_created_at"), table_name="document_events")
    op.drop_index(op.f("ix_document_events_actor_id"), table_name="document_events")
    op.drop_table("document_events")
    op.drop_index(op.f("ix_document_assets_document_version_id"), table_name="document_assets")
    op.drop_table("document_assets")
    op.drop_index(op.f("ix_document_versions_document_id"), table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_constraint("ck_documents_publication_year", "documents", type_="check")
    op.drop_constraint("ck_documents_size_bytes", "documents", type_="check")
    op.drop_column("documents", "removed_at")
    op.drop_column("documents", "size_bytes")
    op.drop_column("documents", "source_metadata")
    op.drop_column("documents", "variant")
    op.drop_column("documents", "component")
    op.drop_column("documents", "exam_session")
    op.drop_column("documents", "publication_year")
    op.drop_column("documents", "edition")
