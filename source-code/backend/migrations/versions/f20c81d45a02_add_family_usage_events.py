"""add family usage events

Revision ID: f20c81d45a02
Revises: e19a72c34b91
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f20c81d45a02"
down_revision: Union[str, None] = "e19a72c34b91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_table("family_usage_events",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=True), sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("operation_id", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("kind IN ('ai_request','ai_token')", name="ck_family_usage_kind"),
        sa.CheckConstraint("quantity >= 0", name="ck_family_usage_quantity"),
        sa.ForeignKeyConstraint(["family_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "kind", "operation_id", name="uq_family_usage_operation"))
    for column in ("family_id", "student_id", "kind", "operation_id", "created_at"):
        op.create_index(f"ix_family_usage_events_{column}", "family_usage_events", [column])

def downgrade():
    op.drop_table("family_usage_events")
