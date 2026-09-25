"""flashcard reporting and global availability

Revision ID: 0007_flashcard_reporting
Revises: 0006_flashcard_mastery
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_flashcard_reporting"
down_revision = "0006_flashcard_mastery"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("flashcard_versions", sa.Column("availability", sa.String(16), nullable=False, server_default="active"))
    op.create_index("ix_flashcard_versions_availability", "flashcard_versions", ["availability"])
    op.create_check_constraint("ck_flashcard_availability", "flashcard_versions", "availability IN ('active','reported','excluded')")
    op.create_table("flashcard_reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("public_ref", sa.String(56), nullable=False, unique=True),
        sa.Column("card_version_id", sa.Uuid(), sa.ForeignKey("flashcard_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("admin_note", sa.Text()), sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('open','excluded','restored')", name="ck_flashcard_report_status"),
        sa.UniqueConstraint("student_id", "card_version_id", name="uq_flashcard_report_student_card"))
    op.create_index("ix_flashcard_reports_card_version_id", "flashcard_reports", ["card_version_id"])
    op.create_index("ix_flashcard_reports_student_id", "flashcard_reports", ["student_id"])
    op.create_index("ix_flashcard_reports_status", "flashcard_reports", ["status"])
    op.create_index("ix_flashcard_reports_created_at", "flashcard_reports", ["created_at"])

def downgrade():
    op.drop_table("flashcard_reports")
    op.drop_constraint("ck_flashcard_availability", "flashcard_versions", type_="check")
    op.drop_index("ix_flashcard_versions_availability", table_name="flashcard_versions")
    op.drop_column("flashcard_versions", "availability")
