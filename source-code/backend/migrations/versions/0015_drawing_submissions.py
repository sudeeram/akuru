"""Freeze a private uploaded drawing for each subpart of an answer."""
from alembic import op
import sqlalchemy as sa
revision="0015_drawing_submissions"
down_revision="0014_answer_visuals"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("assessment_answers",sa.Column("drawing_files",sa.JSON(),nullable=False,server_default="{}"))

def downgrade():
    op.drop_column("assessment_answers","drawing_files")
