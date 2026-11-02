"""Explicit reviewed-subpart practice releases; reuse assessment attempts."""
from alembic import op
import sqlalchemy as sa

revision = '0018_tutor_past_paper_chat'
down_revision = '0017_official_question_analyses'
branch_labels = depends_on = None


def upgrade():
    op.create_table('tutor_paper_chat_requests',
        sa.Column('session_id', sa.Uuid(), sa.ForeignKey('tutor_sessions.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('request_key', sa.String(100), primary_key=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table('tutor_paper_releases',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('question_id', sa.Uuid(), sa.ForeignKey('official_paper_review_questions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('part_label', sa.String(40), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('fingerprint', sa.String(64), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('released_by', sa.Uuid(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('question_id', 'part_label', 'fingerprint', name='uq_tutor_paper_release_source'))
    op.add_column('assessment_questions', sa.Column('tutor_paper_release_id', sa.Uuid(), sa.ForeignKey('tutor_paper_releases.id', ondelete='RESTRICT'), nullable=True))
    op.alter_column('assessment_questions', 'source_question_version_id', nullable=True)
    op.create_check_constraint('ck_assessment_question_source', 'assessment_questions', '(source_question_version_id IS NOT NULL) <> (tutor_paper_release_id IS NOT NULL)')


def downgrade():
    # Never discard attempts using the new source type during rollback.
    connection = op.get_bind()
    if connection.execute(sa.text('SELECT count(*) FROM assessment_questions WHERE tutor_paper_release_id IS NOT NULL')).scalar():
        raise RuntimeError('Retain the compatible schema: tutor past-paper attempts exist.')
    op.drop_constraint('ck_assessment_question_source', 'assessment_questions')
    op.alter_column('assessment_questions', 'source_question_version_id', nullable=False)
    op.drop_column('assessment_questions', 'tutor_paper_release_id')
    op.drop_table('tutor_paper_releases')
    op.drop_table('tutor_paper_chat_requests')
