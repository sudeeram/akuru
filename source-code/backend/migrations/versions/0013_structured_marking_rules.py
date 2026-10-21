"""Preserve private grouped marking rules in versioned official rubrics."""
from alembic import op
import sqlalchemy as sa

revision = "0013_structured_marking_rules"
down_revision = "0012_student_community"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("mark_scheme_entry_versions", sa.Column("scoring_rules", sa.JSON(), nullable=True))

def downgrade():
    op.drop_column("mark_scheme_entry_versions", "scoring_rules")
