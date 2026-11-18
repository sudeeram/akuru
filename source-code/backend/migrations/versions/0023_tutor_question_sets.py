"""Private resumable topic practice sets; preserve existing assessment history."""
from alembic import op
import sqlalchemy as sa
revision = '0023_tutor_question_sets'
down_revision = '0022_accuracy_reassessment'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('tutor_question_sets',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('public_ref', sa.String(56), nullable=False, unique=True),
        sa.Column('session_id', sa.Uuid(), sa.ForeignKey('tutor_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Uuid(), sa.ForeignKey('student_profiles.student_id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_key', sa.String(100), nullable=False),
        sa.Column('status', sa.String(16), nullable=False, server_default='active'),
        sa.Column('source_kind', sa.String(16), nullable=False),
        sa.Column('requested_count', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('topic_refs', sa.JSON(), nullable=False),
        sa.Column('items', sa.JSON(), nullable=False),
        sa.Column('provenance', sa.JSON(), nullable=False),
        sa.Column('processing_key', sa.String(100)),
        sa.Column('processing_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('session_id', 'request_key', name='uq_tutor_question_set_request'),
        sa.CheckConstraint("status IN ('active','completed','abandoned')", name='ck_tutor_question_set_status'),
        sa.CheckConstraint("source_kind IN ('official','generated')", name='ck_tutor_question_set_kind'),
        sa.CheckConstraint('requested_count BETWEEN 1 AND 20', name='ck_tutor_question_set_count'))
    for col in ('public_ref','session_id','student_id'):
        op.create_index('ix_tutor_question_sets_'+col, 'tutor_question_sets', [col])
    op.create_index('uq_active_tutor_question_set', 'tutor_question_sets', ['session_id'], unique=True, postgresql_where=sa.text("status = 'active'"))


def downgrade():
    op.drop_table('tutor_question_sets')
