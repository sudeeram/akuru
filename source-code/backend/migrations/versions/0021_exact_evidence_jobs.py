"""Bounded, durable exact-evidence model jobs; no source/content backfill."""
from alembic import op
import sqlalchemy as sa
revision='0021_exact_evidence_jobs'
down_revision='0020_question_ai_approval'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('evidence_link_jobs',
        sa.Column('id',sa.Uuid(),primary_key=True),
        sa.Column('paper_id',sa.Uuid(),sa.ForeignKey('documents.id',ondelete='CASCADE'),nullable=False),
        sa.Column('created_by',sa.Uuid(),sa.ForeignKey('users.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('status',sa.String(20),nullable=False),
        sa.Column('request_data',sa.JSON(),nullable=False),
        sa.Column('result_data',sa.JSON(),nullable=False),
        sa.Column('error_code',sa.String(80)),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column('started_at',sa.DateTime(timezone=True)),
        sa.Column('completed_at',sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('queued','processing','completed','failed')",name='ck_evidence_job_status'))
    op.create_index('ix_evidence_link_jobs_paper_id','evidence_link_jobs',['paper_id'])
    op.create_index('ix_evidence_link_jobs_status','evidence_link_jobs',['status'])

def downgrade():
    op.drop_table('evidence_link_jobs')
