"""Explicit subject/topic chat scope; preserve every existing topic session."""
from alembic import op
import sqlalchemy as sa

revision = '0019_tutor_chat_scope'
down_revision = '0018_tutor_past_paper_chat'
branch_labels = depends_on = None


def upgrade():
    op.add_column('tutor_sessions', sa.Column('chat_scope', sa.String(16), nullable=False, server_default='topic'))
    op.create_check_constraint('ck_tutor_session_chat_scope', 'tutor_sessions', "chat_scope IN ('topic','subject')")


def downgrade():
    if op.get_bind().execute(sa.text("SELECT count(*) FROM tutor_sessions WHERE chat_scope = 'subject'")).scalar():
        raise RuntimeError('Subject conversations exist; retain their scope with the compatible schema.')
    op.drop_constraint('ck_tutor_session_chat_scope', 'tutor_sessions')
    op.drop_column('tutor_sessions', 'chat_scope')
