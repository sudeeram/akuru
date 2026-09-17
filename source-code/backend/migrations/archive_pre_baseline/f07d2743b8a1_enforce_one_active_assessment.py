"""enforce one active assessment

Revision ID: f07d2743b8a1
Revises: 6b51f918c2e0
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f07d2743b8a1"
down_revision: Union[str, None] = "6b51f918c2e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_index("uq_active_assessment_per_student", "assessments", ["student_id"], unique=True,
        postgresql_where=sa.text("status = 'active'"))

def downgrade() -> None:
    op.drop_index("uq_active_assessment_per_student", table_name="assessments")
