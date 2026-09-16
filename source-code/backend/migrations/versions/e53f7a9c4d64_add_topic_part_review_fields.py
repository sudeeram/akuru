"""add topic part upload idempotency and original page assets

Revision ID: e53f7a9c4d64
Revises: d42e6f7b8c53
"""
from alembic import op
import sqlalchemy as sa

revision = "e53f7a9c4d64"
down_revision = "d42e6f7b8c53"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("upload_request_key", sa.String(100), nullable=True))
    op.create_unique_constraint("uq_documents_upload_request_key", "documents", ["upload_request_key"])
    op.add_column("document_pages", sa.Column("original_render_asset_id", sa.UUID(), nullable=True))
    op.create_unique_constraint("uq_document_pages_original_render", "document_pages", ["original_render_asset_id"])
    op.create_foreign_key(
        "fk_document_page_original_asset_version", "document_pages", "document_assets",
        ["original_render_asset_id", "document_version_id"], ["id", "document_version_id"], ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_document_page_original_asset_version", "document_pages", type_="foreignkey")
    op.drop_constraint("uq_document_pages_original_render", "document_pages", type_="unique")
    op.drop_column("document_pages", "original_render_asset_id")
    op.drop_constraint("uq_documents_upload_request_key", "documents", type_="unique")
    op.drop_column("documents", "upload_request_key")
