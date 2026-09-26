"""password lifecycle and login visibility

Revision ID: 0008_password_lifecycle
Revises: 0007_flashcard_reporting
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_password_lifecycle"
down_revision = "0007_flashcard_reporting"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("public_ref", sa.String(56), nullable=True))
    op.execute("UPDATE users SET public_ref = 'account_' || replace(id::text, '-', '')")
    op.alter_column("users", "public_ref", nullable=False)
    op.create_unique_constraint("uq_users_public_ref", "users", ["public_ref"])
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True)))
    op.create_index("ix_users_last_login_at", "users", ["last_login_at"])
    op.create_table("password_reset_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_key", sa.String(100), nullable=False, unique=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sessions_revoked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_password_reset_receipts_actor_id", "password_reset_receipts", ["actor_id"])
    op.create_index("ix_password_reset_receipts_target_user_id", "password_reset_receipts", ["target_user_id"])
    op.create_index("ix_password_reset_receipts_created_at", "password_reset_receipts", ["created_at"])

def downgrade():
    op.drop_table("password_reset_receipts")
    op.drop_index("ix_users_last_login_at", table_name="users")
    op.drop_column("users", "last_login_at")
    op.drop_constraint("uq_users_public_ref", "users", type_="unique")
    op.drop_column("users", "public_ref")
