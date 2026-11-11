"""Distinguish durable source-link proposals from final accuracy reassessment."""
from alembic import op
import sqlalchemy as sa
revision='0022_accuracy_reassessment'
down_revision='0021_exact_evidence_jobs'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('evidence_link_jobs',sa.Column('job_kind',sa.String(20),server_default='evidence',nullable=False))
    op.create_index('ix_evidence_link_jobs_job_kind','evidence_link_jobs',['job_kind'])

def downgrade():
    op.drop_index('ix_evidence_link_jobs_job_kind',table_name='evidence_link_jobs')
    op.drop_column('evidence_link_jobs','job_kind')
