"""add versioned topic coverage draft lineage

Revision ID: g75b9c1e6f86
Revises: f64a8b0d5e75
"""
from alembic import op
import sqlalchemy as sa

revision = "g75b9c1e6f86"
down_revision = "f64a8b0d5e75"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("curriculum_plans", "textbook_content_version_id", existing_type=sa.Uuid(), nullable=True)
    op.add_column("curriculum_plans", sa.Column("based_on_plan_id", sa.Uuid(), nullable=True))
    op.create_index("ix_curriculum_plans_based_on_plan_id", "curriculum_plans", ["based_on_plan_id"])
    op.create_foreign_key("fk_curriculum_plan_base", "curriculum_plans", "curriculum_plans",
                          ["based_on_plan_id"], ["id"], ondelete="RESTRICT")


def downgrade():
    op.drop_constraint("fk_curriculum_plan_base", "curriculum_plans", type_="foreignkey")
    op.drop_index("ix_curriculum_plans_based_on_plan_id", table_name="curriculum_plans")
    op.drop_column("curriculum_plans", "based_on_plan_id")
    op.alter_column("curriculum_plans", "textbook_content_version_id", existing_type=sa.Uuid(), nullable=False)
