"""add educational media

Revision ID: c72d8e4f19a1
Revises: d661c1b505e4
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str='c72d8e4f19a1'
down_revision: Union[str,None]='d661c1b505e4'
branch_labels: Union[str,Sequence[str],None]=None
depends_on: Union[str,Sequence[str],None]=None

def upgrade():
    op.create_table('educational_media',
        sa.Column('id',sa.Uuid(),nullable=False),sa.Column('subject_id',sa.String(32),nullable=False),
        sa.Column('unit_id',sa.Uuid(),nullable=False),sa.Column('source_chunk_id',sa.Uuid(),nullable=False),
        sa.Column('kind',sa.String(28),nullable=False),sa.Column('title',sa.String(180),nullable=False),
        sa.Column('alt_text',sa.String(1000),nullable=False),sa.Column('prompt',sa.Text(),nullable=False),
        sa.Column('prompt_version',sa.String(40),nullable=False),sa.Column('parameters',sa.JSON(),server_default='{}',nullable=False),
        sa.Column('source_manifest',sa.JSON(),nullable=False),sa.Column('provider',sa.String(40),nullable=False),
        sa.Column('model',sa.String(120),nullable=False),sa.Column('response_id',sa.String(180),nullable=True),
        sa.Column('object_key',sa.String(500),nullable=False),sa.Column('content_type',sa.String(80),nullable=False),
        sa.Column('checksum',sa.String(64),nullable=False),sa.Column('status',sa.String(20),nullable=False),
        sa.Column('created_by',sa.Uuid(),nullable=False),sa.Column('reviewed_by',sa.Uuid(),nullable=True),
        sa.Column('review_notes',sa.Text(),server_default='',nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False),
        sa.Column('reviewed_at',sa.DateTime(timezone=True),nullable=True),
        sa.CheckConstraint("kind IN ('circuit_svg','forces_svg','geometry_svg','plot_svg','conceptual_image')",name='ck_educational_media_kind'),
        sa.CheckConstraint("status IN ('pending_review','published','rejected')",name='ck_educational_media_status'),
        sa.ForeignKeyConstraint(['subject_id'],['subjects.id'],ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['unit_id'],['textbook_units.id'],ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['source_chunk_id'],['retrieval_chunks.id'],ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'],['users.id'],ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reviewed_by'],['users.id'],ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),sa.UniqueConstraint('object_key'))
    for column in ('subject_id','unit_id','source_chunk_id','kind','status','created_by','created_at'):
        op.create_index(f'ix_educational_media_{column}','educational_media',[column])

def downgrade():
    op.drop_table('educational_media')
