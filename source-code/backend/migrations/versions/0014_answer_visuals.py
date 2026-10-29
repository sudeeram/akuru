"""Private approved answer visuals on immutable rubric versions."""
from alembic import op
import sqlalchemy as sa
revision = "0014_answer_visuals"
down_revision = "0013_structured_marking_rules"
branch_labels = None
depends_on = None

def upgrade():
    for name in ("answer_visuals", "drawing_parts"):
        op.add_column("mark_scheme_entry_versions", sa.Column(name, sa.JSON(), nullable=False, server_default="[]"))

def downgrade():
    for name in ("drawing_parts", "answer_visuals"):
        op.drop_column("mark_scheme_entry_versions", name)
