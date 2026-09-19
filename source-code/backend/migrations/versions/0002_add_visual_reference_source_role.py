"""add visual reference topic-source role

Revision ID: 0002_visual_reference
Revises: 0001_initial_akuru_schema
"""

from alembic import op


revision = "0002_visual_reference"
down_revision = "0001_initial_akuru_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_topic_document_role", "textbook_topic_documents", type_="check")
    op.create_check_constraint(
        "ck_topic_document_role", "textbook_topic_documents",
        "role IN ('primary','supporting','reference','visual_reference')",
    )
    op.drop_constraint("ck_topic_content_source_role", "textbook_topic_content_sources", type_="check")
    op.create_check_constraint(
        "ck_topic_content_source_role", "textbook_topic_content_sources",
        "role IN ('primary','supporting','reference','visual_reference')",
    )


def downgrade() -> None:
    op.execute("UPDATE textbook_topic_documents SET role = 'reference' WHERE role = 'visual_reference'")
    op.execute("UPDATE textbook_topic_content_sources SET role = 'reference' WHERE role = 'visual_reference'")
    op.drop_constraint("ck_topic_content_source_role", "textbook_topic_content_sources", type_="check")
    op.create_check_constraint(
        "ck_topic_content_source_role", "textbook_topic_content_sources",
        "role IN ('primary','supporting','reference')",
    )
    op.drop_constraint("ck_topic_document_role", "textbook_topic_documents", type_="check")
    op.create_check_constraint(
        "ck_topic_document_role", "textbook_topic_documents",
        "role IN ('primary','supporting','reference')",
    )
