"""initial akuru schema

Revision ID: 0001_initial_akuru_schema
Revises:
Create Date: 2026-09-17 13:00:37.968907
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


revision: str = '0001_initial_akuru_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector is part of the AKURU schema and is safe to create repeatedly.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('ai_provider_accounts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('display_name', sa.String(length=120), nullable=False),
    sa.Column('credential_alias', sa.String(length=40), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('model', sa.String(length=120), nullable=False),
    sa.Column('enabled', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('health_status', sa.String(length=24), server_default='unknown', nullable=False),
    sa.Column('cooldown_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_error_code', sa.String(length=80), nullable=True),
    sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("health_status IN ('unknown','available','cooldown','credit_exhausted','invalid_credential')", name='ck_ai_provider_accounts_health'),
    sa.CheckConstraint('priority BETWEEN 0 AND 100', name='ck_ai_provider_accounts_priority'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('credential_alias'),
    sa.UniqueConstraint('display_name'),
    sa.UniqueConstraint('priority')
    )
    op.create_table('courses',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('phase1_active', sa.Boolean(), server_default='false', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('login_throttles',
    sa.Column('key_hash', sa.String(length=64), nullable=False),
    sa.Column('failure_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('window_started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('failure_count >= 0', name='ck_login_failure_count'),
    sa.PrimaryKeyConstraint('key_hash')
    )
    op.create_table('subjects',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('tutor_avatars',
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('display_name', sa.String(length=80), nullable=False),
    sa.Column('description', sa.String(length=240), nullable=False),
    sa.Column('image_path', sa.String(length=240), nullable=False),
    sa.Column('presentation', sa.String(length=16), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("presentation IN ('masculine','feminine','neutral')", name='ck_tutor_avatar_presentation'),
    sa.CheckConstraint('sort_order BETWEEN 0 AND 1000', name='ck_tutor_avatar_sort_order'),
    sa.PrimaryKeyConstraint('code')
    )
    op.create_table('tutor_voice_presets',
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('display_name', sa.String(length=80), nullable=False),
    sa.Column('description', sa.String(length=240), nullable=False),
    sa.Column('provider_voice_ref', sa.String(length=80), nullable=True),
    sa.Column('presentation', sa.String(length=16), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("presentation IN ('masculine','feminine','neutral')", name='ck_tutor_voice_presentation'),
    sa.CheckConstraint('sort_order BETWEEN 0 AND 1000', name='ck_tutor_voice_sort_order'),
    sa.PrimaryKeyConstraint('code')
    )
    op.create_table('users',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('display_name', sa.String(length=160), nullable=False),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('must_change_password', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("role IN ('admin','parent','student')", name='ck_users_role'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('ai_provider_attempts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('operation_id', sa.Uuid(), nullable=False),
    sa.Column('account_id', sa.Uuid(), nullable=False),
    sa.Column('attempt_number', sa.Integer(), nullable=False),
    sa.Column('purpose', sa.String(length=40), nullable=False),
    sa.Column('model', sa.String(length=120), nullable=False),
    sa.Column('prompt_version', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('response_id', sa.String(length=120), nullable=True),
    sa.Column('error_code', sa.String(length=80), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('processing','completed','failed')", name='ck_ai_provider_attempts_status'),
    sa.CheckConstraint('attempt_number > 0', name='ck_ai_provider_attempts_number'),
    sa.ForeignKeyConstraint(['account_id'], ['ai_provider_accounts.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('operation_id', 'attempt_number', name='uq_ai_provider_attempt_operation_number')
    )
    op.create_index(op.f('ix_ai_provider_attempts_account_id'), 'ai_provider_attempts', ['account_id'], unique=False)
    op.create_index(op.f('ix_ai_provider_attempts_operation_id'), 'ai_provider_attempts', ['operation_id'], unique=False)
    op.create_table('assessment_blueprints',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('grade', sa.Integer(), nullable=False),
    sa.Column('term', sa.Integer(), nullable=False),
    sa.Column('mode', sa.String(length=24), nullable=False),
    sa.Column('target_marks', sa.Integer(), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('question_count', sa.Integer(), nullable=False),
    sa.Column('skills', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('difficulty_profile', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('status', sa.String(length=16), server_default='draft', nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("mode IN ('practice','official_paper','mock')", name='ck_assessment_blueprint_mode'),
    sa.CheckConstraint("status IN ('draft','published','retired')", name='ck_assessment_blueprint_status'),
    sa.CheckConstraint('grade IN (10, 11) AND term IN (1, 2, 3)', name='ck_assessment_blueprint_period'),
    sa.CheckConstraint('target_marks > 0 AND duration_minutes > 0 AND question_count > 0', name='ck_assessment_blueprint_values'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessment_blueprints_course_id'), 'assessment_blueprints', ['course_id'], unique=False)
    op.create_index(op.f('ix_assessment_blueprints_status'), 'assessment_blueprints', ['status'], unique=False)
    op.create_index(op.f('ix_assessment_blueprints_subject_id'), 'assessment_blueprints', ['subject_id'], unique=False)
    op.create_table('audit_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('target_type', sa.String(length=40), nullable=False),
    sa.Column('target_id', sa.String(length=80), nullable=False),
    sa.Column('event_data', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_action'), 'audit_events', ['action'], unique=False)
    op.create_index(op.f('ix_audit_events_actor_id'), 'audit_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_events_created_at'), 'audit_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_events_target_id'), 'audit_events', ['target_id'], unique=False)
    op.create_table('auth_sessions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('csrf_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('client_ip_hash', sa.String(length=64), nullable=False),
    sa.Column('user_agent', sa.String(length=300), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_auth_sessions_expires_at'), 'auth_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_auth_sessions_user_id'), 'auth_sessions', ['user_id'], unique=False)
    op.create_table('documents',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=24), nullable=False),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('title', sa.String(length=240), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('object_key', sa.String(length=500), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('review_state', sa.String(length=16), server_default='pending', nullable=False),
    sa.Column('uploaded_by', sa.Uuid(), nullable=False),
    sa.Column('source_document_id', sa.Uuid(), nullable=True),
    sa.Column('edition', sa.String(length=80), nullable=True),
    sa.Column('publication_year', sa.Integer(), nullable=True),
    sa.Column('exam_session', sa.String(length=80), nullable=True),
    sa.Column('component', sa.String(length=80), nullable=True),
    sa.Column('variant', sa.String(length=80), nullable=True),
    sa.Column('source_metadata', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('size_bytes', sa.Integer(), server_default='0', nullable=False),
    sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('upload_request_key', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('textbook','reference','past_paper','mark_scheme','examiner_report')", name='ck_documents_kind'),
    sa.CheckConstraint("review_state IN ('pending','reviewed','published','rejected')", name='ck_documents_review_state'),
    sa.CheckConstraint('publication_year IS NULL OR publication_year BETWEEN 1900 AND 2100', name='ck_documents_publication_year'),
    sa.CheckConstraint('size_bytes >= 0', name='ck_documents_size_bytes'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_document_id'], ['documents.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('object_key'),
    sa.UniqueConstraint('sha256'),
    sa.UniqueConstraint('upload_request_key')
    )
    op.create_index(op.f('ix_documents_subject_id'), 'documents', ['subject_id'], unique=False)
    op.create_table('evaluation_corpora',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('workflow', sa.String(length=32), server_default='assessment', nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=180), nullable=False),
    sa.Column('cases', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('approved_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('draft','approved','retired')", name='ck_evaluation_corpus_status'),
    sa.CheckConstraint("workflow IN ('assessment','tutor')", name='ck_evaluation_corpus_workflow'),
    sa.CheckConstraint('version_number > 0', name='ck_evaluation_corpus_version'),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('subject_id', 'workflow', 'version_number', name='uq_evaluation_corpus_subject_workflow_version')
    )
    op.create_index(op.f('ix_evaluation_corpora_status'), 'evaluation_corpora', ['status'], unique=False)
    op.create_index(op.f('ix_evaluation_corpora_subject_id'), 'evaluation_corpora', ['subject_id'], unique=False)
    op.create_index(op.f('ix_evaluation_corpora_workflow'), 'evaluation_corpora', ['workflow'], unique=False)
    op.create_table('student_profiles',
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('parent_id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('student_id')
    )
    op.create_index(op.f('ix_student_profiles_parent_id'), 'student_profiles', ['parent_id'], unique=False)
    op.create_table('textbooks',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('title', sa.String(length=240), nullable=False),
    sa.Column('edition', sa.String(length=80), nullable=False),
    sa.Column('publisher', sa.String(length=160), server_default='', nullable=False),
    sa.Column('group_label', sa.String(length=12), nullable=False),
    sa.Column('status', sa.String(length=16), server_default='draft', nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('published_by', sa.Uuid(), nullable=True),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("group_label IN ('unit','module')", name='ck_textbook_group_label'),
    sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_textbook_status'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['published_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('course_id', 'subject_id', 'title', 'edition', name='uq_textbook_edition'),
    sa.UniqueConstraint('id', 'course_id', 'subject_id', name='uq_textbook_scope'),
    sa.UniqueConstraint('public_ref')
    )
    op.create_index(op.f('ix_textbooks_course_id'), 'textbooks', ['course_id'], unique=False)
    op.create_index(op.f('ix_textbooks_status'), 'textbooks', ['status'], unique=False)
    op.create_index(op.f('ix_textbooks_subject_id'), 'textbooks', ['subject_id'], unique=False)
    op.create_table('curriculum_plans',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('textbook_id', sa.Uuid(), nullable=False),
    sa.Column('based_on_plan_id', sa.Uuid(), nullable=True),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('published_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('draft','published','superseded')", name='ck_curriculum_plan_status'),
    sa.CheckConstraint('version_number > 0', name='ck_curriculum_plan_version'),
    sa.ForeignKeyConstraint(['based_on_plan_id'], ['curriculum_plans.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['published_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['textbook_id'], ['textbooks.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('course_id', 'subject_id', 'version_number', name='uq_curriculum_plan_version')
    )
    op.create_index(op.f('ix_curriculum_plans_based_on_plan_id'), 'curriculum_plans', ['based_on_plan_id'], unique=False)
    op.create_index(op.f('ix_curriculum_plans_subject_id'), 'curriculum_plans', ['subject_id'], unique=False)
    op.create_index(op.f('ix_curriculum_plans_textbook_id'), 'curriculum_plans', ['textbook_id'], unique=False)
    op.create_table('document_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('object_key', sa.String(length=500), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=24), server_default='uploaded', nullable=False),
    sa.Column('uploaded_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('uploaded','queued','processing','needs_review','failed','completed','removed')", name='ck_document_versions_status'),
    sa.CheckConstraint('size_bytes > 0', name='ck_document_versions_size'),
    sa.CheckConstraint('version_number > 0', name='ck_document_versions_number'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_id', 'version_number', name='uq_document_version_number'),
    sa.UniqueConstraint('object_key'),
    sa.UniqueConstraint('sha256')
    )
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)
    op.create_table('evaluation_runs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('corpus_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('workflow', sa.String(length=32), server_default='assessment', nullable=False),
    sa.Column('modality', sa.String(length=16), server_default='assessment', nullable=False),
    sa.Column('environment', sa.String(length=16), server_default='ci', nullable=False),
    sa.Column('candidate_model', sa.String(length=120), nullable=False),
    sa.Column('prompt_version', sa.String(length=80), nullable=False),
    sa.Column('observations_hash', sa.String(length=64), nullable=False),
    sa.Column('metrics', sa.JSON(), nullable=False),
    sa.Column('thresholds', sa.JSON(), nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('failure_reasons', sa.JSON(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("environment IN ('ci','staging')", name='ck_evaluation_run_environment'),
    sa.CheckConstraint("modality IN ('assessment','text','voice','tools')", name='ck_evaluation_run_modality'),
    sa.CheckConstraint("workflow IN ('assessment','tutor')", name='ck_evaluation_run_workflow'),
    sa.ForeignKeyConstraint(['corpus_id'], ['evaluation_corpora.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_runs_corpus_id'), 'evaluation_runs', ['corpus_id'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_created_at'), 'evaluation_runs', ['created_at'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_environment'), 'evaluation_runs', ['environment'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_modality'), 'evaluation_runs', ['modality'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_passed'), 'evaluation_runs', ['passed'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_subject_id'), 'evaluation_runs', ['subject_id'], unique=False)
    op.create_index(op.f('ix_evaluation_runs_workflow'), 'evaluation_runs', ['workflow'], unique=False)
    op.create_table('family_usage_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('family_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=True),
    sa.Column('kind', sa.String(length=24), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('operation_id', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('ai_request','ai_token')", name='ck_family_usage_kind'),
    sa.CheckConstraint('quantity >= 0', name='ck_family_usage_quantity'),
    sa.ForeignKeyConstraint(['family_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('family_id', 'kind', 'operation_id', name='uq_family_usage_operation')
    )
    op.create_index(op.f('ix_family_usage_events_created_at'), 'family_usage_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_usage_events_family_id'), 'family_usage_events', ['family_id'], unique=False)
    op.create_index(op.f('ix_family_usage_events_kind'), 'family_usage_events', ['kind'], unique=False)
    op.create_index(op.f('ix_family_usage_events_operation_id'), 'family_usage_events', ['operation_id'], unique=False)
    op.create_index(op.f('ix_family_usage_events_student_id'), 'family_usage_events', ['student_id'], unique=False)
    op.create_table('student_ai_quotas',
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('period_days', sa.Integer(), server_default='30', nullable=False),
    sa.Column('period_anchor', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('request_allowance', sa.Integer(), server_default='100', nullable=False),
    sa.Column('text_token_allowance', sa.Integer(), server_default='200000', nullable=False),
    sa.Column('voice_seconds_allowance', sa.Integer(), server_default='3600', nullable=False),
    sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('period_days BETWEEN 1 AND 366', name='ck_student_ai_quota_period_days'),
    sa.CheckConstraint('request_allowance >= 0', name='ck_student_ai_quota_requests'),
    sa.CheckConstraint('text_token_allowance >= 0', name='ck_student_ai_quota_text_tokens'),
    sa.CheckConstraint('voice_seconds_allowance >= 0', name='ck_student_ai_quota_voice_seconds'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('student_id'),
    sa.UniqueConstraint('public_ref')
    )
    op.create_table('student_ai_usage',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('operation_id', sa.String(length=100), nullable=False),
    sa.Column('dimension', sa.String(length=24), nullable=False),
    sa.Column('event_type', sa.String(length=20), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('reason', sa.String(length=300), nullable=True),
    sa.Column('event_data', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("dimension IN ('request','text_token','voice_second')", name='ck_student_ai_usage_dimension'),
    sa.CheckConstraint("event_type IN ('reserve','settle','release','adjustment')", name='ck_student_ai_usage_event_type'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'operation_id', 'dimension', 'event_type', name='uq_student_ai_usage_operation_event')
    )
    op.create_index(op.f('ix_student_ai_usage_created_at'), 'student_ai_usage', ['created_at'], unique=False)
    op.create_index(op.f('ix_student_ai_usage_dimension'), 'student_ai_usage', ['dimension'], unique=False)
    op.create_index(op.f('ix_student_ai_usage_event_type'), 'student_ai_usage', ['event_type'], unique=False)
    op.create_index(op.f('ix_student_ai_usage_operation_id'), 'student_ai_usage', ['operation_id'], unique=False)
    op.create_index(op.f('ix_student_ai_usage_student_id'), 'student_ai_usage', ['student_id'], unique=False)
    op.create_table('student_progressions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('grade', sa.Integer(), nullable=False),
    sa.Column('term', sa.Integer(), nullable=False),
    sa.Column('is_current', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('grade IN (10, 11)', name='ck_progression_grade'),
    sa.CheckConstraint('term IN (1, 2, 3)', name='ck_progression_term'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'course_id', 'grade', 'term', name='uq_student_progression_period')
    )
    op.create_index(op.f('ix_student_progressions_student_id'), 'student_progressions', ['student_id'], unique=False)
    op.create_index('uq_current_progression_per_student', 'student_progressions', ['student_id'], unique=True, postgresql_where=sa.text('is_current'))
    op.create_table('student_subjects',
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('student_id', 'subject_id')
    )
    op.create_table('study_plans',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('evidence_fingerprint', sa.String(length=64), nullable=False),
    sa.Column('generation_reason', sa.String(length=20), nullable=False),
    sa.Column('requested_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("generation_reason IN ('evidence','request')", name='ck_study_plan_reason'),
    sa.CheckConstraint("status IN ('active','superseded')", name='ck_study_plan_status'),
    sa.CheckConstraint('version_number > 0', name='ck_study_plan_version'),
    sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'version_number', name='uq_study_plan_student_version')
    )
    op.create_index(op.f('ix_study_plans_status'), 'study_plans', ['status'], unique=False)
    op.create_index(op.f('ix_study_plans_student_id'), 'study_plans', ['student_id'], unique=False)
    op.create_index('uq_study_plan_active_student', 'study_plans', ['student_id'], unique=True, postgresql_where=sa.text("status = 'active'"))
    op.create_table('textbook_groups',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('textbook_id', sa.Uuid(), nullable=False),
    sa.Column('code', sa.String(length=80), nullable=False),
    sa.Column('title', sa.String(length=240), nullable=False),
    sa.Column('summary', sa.Text(), server_default='', nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), server_default='draft', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_textbook_group_status'),
    sa.CheckConstraint('sequence > 0', name='ck_textbook_group_sequence'),
    sa.ForeignKeyConstraint(['textbook_id'], ['textbooks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id', 'textbook_id', name='uq_textbook_group_scope'),
    sa.UniqueConstraint('public_ref'),
    sa.UniqueConstraint('textbook_id', 'code', name='uq_textbook_group_code'),
    sa.UniqueConstraint('textbook_id', 'sequence', name='uq_textbook_group_sequence')
    )
    op.create_index(op.f('ix_textbook_groups_textbook_id'), 'textbook_groups', ['textbook_id'], unique=False)
    op.create_table('textbook_structure_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('textbook_id', sa.Uuid(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('snapshot', sa.JSON(), nullable=False),
    sa.Column('published_by', sa.Uuid(), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('version_number > 0', name='ck_textbook_structure_version'),
    sa.ForeignKeyConstraint(['published_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['textbook_id'], ['textbooks.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('textbook_id', 'version_number', name='uq_textbook_structure_version')
    )
    op.create_index(op.f('ix_textbook_structure_versions_textbook_id'), 'textbook_structure_versions', ['textbook_id'], unique=False)
    op.create_table('tutor_profiles',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=48), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('current_version_number', sa.Integer(), server_default='1', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('current_version_number > 0', name='ck_tutor_profile_current_version'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tutor_profiles_public_ref'), 'tutor_profiles', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_profiles_student_id'), 'tutor_profiles', ['student_id'], unique=False)
    op.create_table('ai_invocations',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=True),
    sa.Column('document_version_id', sa.Uuid(), nullable=True),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('model', sa.String(length=120), nullable=False),
    sa.Column('purpose', sa.String(length=40), nullable=False),
    sa.Column('prompt_name', sa.String(length=80), nullable=False),
    sa.Column('prompt_version', sa.String(length=40), nullable=False),
    sa.Column('schema_name', sa.String(length=120), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('response_id', sa.String(length=120), nullable=True),
    sa.Column('latency_ms', sa.Integer(), nullable=True),
    sa.Column('input_tokens', sa.Integer(), nullable=True),
    sa.Column('output_tokens', sa.Integer(), nullable=True),
    sa.Column('total_tokens', sa.Integer(), nullable=True),
    sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('request_metadata', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('error_code', sa.String(length=80), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("purpose IN ('textbook_extraction','paper_extraction','unit_mapping','assessment','tutoring')", name='ck_ai_invocations_purpose'),
    sa.CheckConstraint("status IN ('processing','completed','failed')", name='ck_ai_invocations_status'),
    sa.CheckConstraint('attempt_count >= 0', name='ck_ai_invocations_attempt_count'),
    sa.CheckConstraint('input_tokens IS NULL OR input_tokens >= 0', name='ck_ai_invocations_input_tokens'),
    sa.CheckConstraint('latency_ms IS NULL OR latency_ms >= 0', name='ck_ai_invocations_latency'),
    sa.CheckConstraint('output_tokens IS NULL OR output_tokens >= 0', name='ck_ai_invocations_output_tokens'),
    sa.CheckConstraint('total_tokens IS NULL OR total_tokens >= 0', name='ck_ai_invocations_total_tokens'),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_invocations_actor_id'), 'ai_invocations', ['actor_id'], unique=False)
    op.create_index(op.f('ix_ai_invocations_created_at'), 'ai_invocations', ['created_at'], unique=False)
    op.create_index(op.f('ix_ai_invocations_document_version_id'), 'ai_invocations', ['document_version_id'], unique=False)
    op.create_index(op.f('ix_ai_invocations_purpose'), 'ai_invocations', ['purpose'], unique=False)
    op.create_index(op.f('ix_ai_invocations_response_id'), 'ai_invocations', ['response_id'], unique=False)
    op.create_index(op.f('ix_ai_invocations_status'), 'ai_invocations', ['status'], unique=False)
    op.create_table('assessment_curriculum_snapshots',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('assessment_ref', sa.String(length=120), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('plan_id', sa.Uuid(), nullable=False),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('grade', sa.Integer(), nullable=False),
    sa.Column('term', sa.Integer(), nullable=False),
    sa.Column('covered_topic_ids', sa.JSON(), nullable=False),
    sa.Column('progression_periods', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('grade IN (10, 11)', name='ck_assessment_snapshot_grade'),
    sa.CheckConstraint('term IN (1, 2, 3)', name='ck_assessment_snapshot_term'),
    sa.ForeignKeyConstraint(['plan_id'], ['curriculum_plans.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assessment_ref')
    )
    op.create_index(op.f('ix_assessment_curriculum_snapshots_student_id'), 'assessment_curriculum_snapshots', ['student_id'], unique=False)
    op.create_table('document_assets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('asset_kind', sa.String(length=40), nullable=False),
    sa.Column('object_key', sa.String(length=500), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=True),
    sa.Column('bounding_box', sa.JSON(), nullable=True),
    sa.Column('asset_metadata', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('page_number IS NULL OR page_number > 0', name='ck_document_assets_page'),
    sa.CheckConstraint('size_bytes > 0', name='ck_document_assets_size'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id', 'document_version_id', name='uq_document_asset_version'),
    sa.UniqueConstraint('object_key')
    )
    op.create_index(op.f('ix_document_assets_document_version_id'), 'document_assets', ['document_version_id'], unique=False)
    op.create_table('document_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=True),
    sa.Column('actor_id', sa.Uuid(), nullable=False),
    sa.Column('event_type', sa.String(length=40), nullable=False),
    sa.Column('event_data', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_events_actor_id'), 'document_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_document_events_created_at'), 'document_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_document_events_document_id'), 'document_events', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_events_document_version_id'), 'document_events', ['document_version_id'], unique=False)
    op.create_index(op.f('ix_document_events_event_type'), 'document_events', ['event_type'], unique=False)
    op.create_table('document_jobs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('stage', sa.String(length=40), server_default='preflight', nullable=False),
    sa.Column('status', sa.String(length=24), server_default='queued', nullable=False),
    sa.Column('progress', sa.Integer(), server_default='0', nullable=False),
    sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('extraction_version', sa.String(length=80), nullable=False),
    sa.Column('error_code', sa.String(length=80), nullable=True),
    sa.Column('error_message', sa.String(length=500), nullable=True),
    sa.Column('result_data', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('max_seconds', sa.Integer(), nullable=False),
    sa.Column('max_memory_mb', sa.Integer(), nullable=False),
    sa.Column('max_pages', sa.Integer(), nullable=False),
    sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('queued','processing','needs_review','failed','completed')", name='ck_document_jobs_status'),
    sa.CheckConstraint('attempt_count >= 0', name='ck_document_jobs_attempt_count'),
    sa.CheckConstraint('max_memory_mb > 0', name='ck_document_jobs_max_memory'),
    sa.CheckConstraint('max_pages > 0', name='ck_document_jobs_max_pages'),
    sa.CheckConstraint('max_seconds > 0', name='ck_document_jobs_max_seconds'),
    sa.CheckConstraint('progress BETWEEN 0 AND 100', name='ck_document_jobs_progress'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_version_id', 'stage', 'extraction_version', name='uq_document_job_stage_version')
    )
    op.create_index(op.f('ix_document_jobs_document_id'), 'document_jobs', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_jobs_document_version_id'), 'document_jobs', ['document_version_id'], unique=False)
    op.create_index(op.f('ix_document_jobs_status'), 'document_jobs', ['status'], unique=False)
    op.create_table('document_stage_runs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('stage', sa.String(length=40), nullable=False),
    sa.Column('extraction_version', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('input_checksum', sa.String(length=64), nullable=False),
    sa.Column('output_data', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('processing','failed','completed')", name='ck_document_stage_runs_status'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_version_id', 'stage', 'extraction_version', name='uq_document_stage_run_version')
    )
    op.create_index(op.f('ix_document_stage_runs_document_version_id'), 'document_stage_runs', ['document_version_id'], unique=False)
    op.create_table('evaluation_releases',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('workflow', sa.String(length=32), nullable=False),
    sa.Column('mode', sa.String(length=20), server_default='review_required', nullable=False),
    sa.Column('run_id', sa.Uuid(), nullable=True),
    sa.Column('confidence_threshold', sa.Float(), server_default='0.85', nullable=False),
    sa.Column('audience', sa.String(length=20), server_default='students', nullable=False),
    sa.Column('activated_by', sa.Uuid(), nullable=False),
    sa.Column('activated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("audience IN ('admin_testing','parent_pilot','students')", name='ck_evaluation_release_audience'),
    sa.CheckConstraint("mode IN ('review_required','automatic')", name='ck_evaluation_release_mode'),
    sa.CheckConstraint("workflow IN ('assessment_feedback','content_publication','tutor_text','tutor_voice','tutor_tools','tutor_learner_context','tutor_next_unit','tutor_sources','tutor_practice','tutor_visuals')", name='ck_evaluation_release_workflow'),
    sa.CheckConstraint('confidence_threshold BETWEEN 0 AND 1', name='ck_evaluation_release_confidence'),
    sa.ForeignKeyConstraint(['activated_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['run_id'], ['evaluation_runs.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('subject_id', 'workflow', name='uq_evaluation_release_subject_workflow')
    )
    op.create_index(op.f('ix_evaluation_releases_subject_id'), 'evaluation_releases', ['subject_id'], unique=False)
    op.create_table('official_material_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('source_document_version_id', sa.Uuid(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=24), nullable=False),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('source_paper_id', sa.Uuid(), nullable=True),
    sa.Column('source_paper_version_id', sa.Uuid(), nullable=True),
    sa.Column('textbook_id', sa.Uuid(), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('inventory_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('completeness_confirmed', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('published_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("kind IN ('past_paper','mark_scheme','examiner_report')", name='ck_official_material_kind'),
    sa.CheckConstraint("status IN ('draft','published','superseded')", name='ck_official_material_status'),
    sa.CheckConstraint('version_number > 0 AND inventory_count >= 0', name='ck_official_material_counts'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['published_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_document_version_id'], ['document_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_paper_id'], ['documents.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_paper_version_id'], ['official_material_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['textbook_id'], ['textbooks.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_id', 'version_number', name='uq_official_material_version')
    )
    op.create_index(op.f('ix_official_material_versions_document_id'), 'official_material_versions', ['document_id'], unique=False)
    op.create_index(op.f('ix_official_material_versions_textbook_id'), 'official_material_versions', ['textbook_id'], unique=False)
    op.create_table('textbook_topics',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('textbook_id', sa.Uuid(), nullable=False),
    sa.Column('group_id', sa.Uuid(), nullable=False),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('code', sa.String(length=80), nullable=False),
    sa.Column('title', sa.String(length=240), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('syllabus_ref', sa.String(length=120), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('status', sa.String(length=16), server_default='draft', nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('draft','published','archived')", name='ck_textbook_topic_status'),
    sa.CheckConstraint('sequence > 0', name='ck_textbook_topic_sequence'),
    sa.ForeignKeyConstraint(['group_id', 'textbook_id'], ['textbook_groups.id', 'textbook_groups.textbook_id'], name='fk_textbook_topic_group_scope', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['textbook_id', 'course_id', 'subject_id'], ['textbooks.id', 'textbooks.course_id', 'textbooks.subject_id'], name='fk_textbook_topic_book_scope', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('group_id', 'sequence', name='uq_textbook_topic_sequence'),
    sa.UniqueConstraint('id', 'course_id', 'subject_id', name='uq_textbook_topic_scope'),
    sa.UniqueConstraint('public_ref'),
    sa.UniqueConstraint('textbook_id', 'code', name='uq_textbook_topic_code')
    )
    op.create_index(op.f('ix_textbook_topics_course_id'), 'textbook_topics', ['course_id'], unique=False)
    op.create_index(op.f('ix_textbook_topics_group_id'), 'textbook_topics', ['group_id'], unique=False)
    op.create_index(op.f('ix_textbook_topics_status'), 'textbook_topics', ['status'], unique=False)
    op.create_index(op.f('ix_textbook_topics_subject_id'), 'textbook_topics', ['subject_id'], unique=False)
    op.create_index(op.f('ix_textbook_topics_textbook_id'), 'textbook_topics', ['textbook_id'], unique=False)
    op.create_table('tutor_profile_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('profile_id', sa.Uuid(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('presentation', sa.String(length=16), nullable=False),
    sa.Column('avatar_code', sa.String(length=40), nullable=False),
    sa.Column('voice_code', sa.String(length=40), nullable=False),
    sa.Column('tone', sa.String(length=16), nullable=False),
    sa.Column('friendliness', sa.String(length=8), nullable=False),
    sa.Column('enthusiasm', sa.String(length=8), nullable=False),
    sa.Column('speed', sa.String(length=8), nullable=False),
    sa.Column('communication_character', sa.String(length=16), nullable=False),
    sa.Column('explanation_depth', sa.String(length=16), nullable=False),
    sa.Column('teaching_style', sa.String(length=20), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("communication_character IN ('childlike','balanced','authoritative')", name='ck_tutor_profile_character'),
    sa.CheckConstraint("enthusiasm IN ('low','medium','high')", name='ck_tutor_profile_enthusiasm'),
    sa.CheckConstraint("explanation_depth IN ('concise','standard','detailed')", name='ck_tutor_profile_depth'),
    sa.CheckConstraint("friendliness IN ('low','medium','high')", name='ck_tutor_profile_friendliness'),
    sa.CheckConstraint("presentation IN ('masculine','feminine','neutral')", name='ck_tutor_profile_presentation'),
    sa.CheckConstraint("speed IN ('low','medium','high')", name='ck_tutor_profile_speed'),
    sa.CheckConstraint("teaching_style IN ('guided','socratic','example_led','exam_focused')", name='ck_tutor_profile_teaching_style'),
    sa.CheckConstraint("tone IN ('calm','encouraging','direct','playful')", name='ck_tutor_profile_tone'),
    sa.CheckConstraint('version_number > 0', name='ck_tutor_profile_version_number'),
    sa.ForeignKeyConstraint(['avatar_code'], ['tutor_avatars.code'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['profile_id'], ['tutor_profiles.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['voice_code'], ['tutor_voice_presets.code'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('profile_id', 'version_number', name='uq_tutor_profile_version')
    )
    op.create_index(op.f('ix_tutor_profile_versions_profile_id'), 'tutor_profile_versions', ['profile_id'], unique=False)
    op.create_table('assessments',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('mode', sa.String(length=24), nullable=False),
    sa.Column('status', sa.String(length=16), server_default='active', nullable=False),
    sa.Column('blueprint_id', sa.Uuid(), nullable=True),
    sa.Column('official_paper_version_id', sa.Uuid(), nullable=True),
    sa.Column('curriculum_snapshot_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('target_marks', sa.Integer(), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('skills', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('difficulty_profile', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('submission_key', sa.String(length=100), nullable=True),
    sa.CheckConstraint("mode IN ('practice','official_paper','mock')", name='ck_assessment_mode'),
    sa.CheckConstraint("status IN ('active','submitted','expired')", name='ck_assessment_status'),
    sa.CheckConstraint('target_marks > 0 AND duration_minutes > 0', name='ck_assessment_values'),
    sa.ForeignKeyConstraint(['blueprint_id'], ['assessment_blueprints.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['curriculum_snapshot_id'], ['assessment_curriculum_snapshots.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['official_paper_version_id'], ['official_material_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'submission_key', name='uq_assessment_submission_key')
    )
    op.create_index(op.f('ix_assessments_ends_at'), 'assessments', ['ends_at'], unique=False)
    op.create_index(op.f('ix_assessments_status'), 'assessments', ['status'], unique=False)
    op.create_index(op.f('ix_assessments_student_id'), 'assessments', ['student_id'], unique=False)
    op.create_index(op.f('ix_assessments_subject_id'), 'assessments', ['subject_id'], unique=False)
    op.create_index('uq_active_assessment_per_student', 'assessments', ['student_id'], unique=True, postgresql_where=sa.text("status = 'active'"))
    op.create_table('curriculum_plan_topics',
    sa.Column('plan_id', sa.Uuid(), nullable=False),
    sa.Column('grade', sa.Integer(), nullable=False),
    sa.Column('term', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('grade IN (10, 11)', name='ck_curriculum_plan_topic_grade'),
    sa.CheckConstraint('term IN (1, 2, 3)', name='ck_curriculum_plan_topic_term'),
    sa.ForeignKeyConstraint(['plan_id'], ['curriculum_plans.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('plan_id', 'grade', 'term', 'topic_id'),
    sa.UniqueConstraint('plan_id', 'topic_id', name='uq_curriculum_plan_topic_introduction')
    )
    op.create_table('document_pages',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=False),
    sa.Column('printed_page_label', sa.String(length=40), nullable=True),
    sa.Column('width_points', sa.Float(), nullable=False),
    sa.Column('height_points', sa.Float(), nullable=False),
    sa.Column('render_asset_id', sa.Uuid(), nullable=False),
    sa.Column('original_render_asset_id', sa.Uuid(), nullable=True),
    sa.Column('native_text', sa.Text(), server_default='', nullable=False),
    sa.Column('extraction_method', sa.String(length=24), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('needs_review', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('page_metadata', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('confidence BETWEEN 0 AND 1', name='ck_document_pages_confidence'),
    sa.CheckConstraint('page_number > 0', name='ck_document_pages_number'),
    sa.CheckConstraint('width_points > 0 AND height_points > 0', name='ck_document_pages_dimensions'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['original_render_asset_id', 'document_version_id'], ['document_assets.id', 'document_assets.document_version_id'], name='fk_document_page_original_asset_version', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['render_asset_id', 'document_version_id'], ['document_assets.id', 'document_assets.document_version_id'], name='fk_document_page_render_asset_version', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_version_id', 'page_number', name='uq_document_page_number'),
    sa.UniqueConstraint('id', 'document_version_id', name='uq_document_page_version'),
    sa.UniqueConstraint('original_render_asset_id'),
    sa.UniqueConstraint('render_asset_id')
    )
    op.create_index(op.f('ix_document_pages_document_version_id'), 'document_pages', ['document_version_id'], unique=False)
    op.create_table('examiner_comment_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('material_version_id', sa.Uuid(), nullable=False),
    sa.Column('question_number', sa.String(length=40), nullable=False),
    sa.Column('common_mistakes', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('advice', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('source_locations', sa.JSON(), server_default='[]', nullable=False),
    sa.ForeignKeyConstraint(['material_version_id'], ['official_material_versions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('material_version_id', 'question_number', name='uq_examiner_comment_number')
    )
    op.create_index(op.f('ix_examiner_comment_versions_material_version_id'), 'examiner_comment_versions', ['material_version_id'], unique=False)
    op.create_table('mark_scheme_entry_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('material_version_id', sa.Uuid(), nullable=False),
    sa.Column('question_number', sa.String(length=40), nullable=False),
    sa.Column('max_marks', sa.Integer(), nullable=False),
    sa.Column('marking_points', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('alternatives', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('source_locations', sa.JSON(), server_default='[]', nullable=False),
    sa.CheckConstraint('max_marks > 0', name='ck_mark_scheme_entry_marks'),
    sa.ForeignKeyConstraint(['material_version_id'], ['official_material_versions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('material_version_id', 'question_number', name='uq_mark_scheme_entry_number')
    )
    op.create_index(op.f('ix_mark_scheme_entry_versions_material_version_id'), 'mark_scheme_entry_versions', ['material_version_id'], unique=False)
    op.create_table('official_question_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('material_version_id', sa.Uuid(), nullable=False),
    sa.Column('question_number', sa.String(length=40), nullable=False),
    sa.Column('parent_number', sa.String(length=40), nullable=True),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('shared_stem', sa.Text(), server_default='', nullable=False),
    sa.Column('marks', sa.Integer(), nullable=False),
    sa.Column('equations', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('asset_ids', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('source_locations', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('mapping_status', sa.String(length=20), server_default='pending', nullable=False),
    sa.CheckConstraint("mapping_status IN ('pending','draft','confirmed')", name='ck_official_question_mapping_status'),
    sa.CheckConstraint('marks > 0', name='ck_official_question_marks'),
    sa.ForeignKeyConstraint(['material_version_id'], ['official_material_versions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('material_version_id', 'question_number', name='uq_official_question_number')
    )
    op.create_index(op.f('ix_official_question_versions_material_version_id'), 'official_question_versions', ['material_version_id'], unique=False)
    op.create_table('textbook_topic_content_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), server_default='published', nullable=False),
    sa.Column('source_manifest', sa.JSON(), nullable=False),
    sa.Column('extraction_manifest', sa.JSON(), nullable=False),
    sa.Column('published_by', sa.Uuid(), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('published','superseded')", name='ck_topic_content_version_status'),
    sa.CheckConstraint('version_number > 0', name='ck_topic_content_version_number'),
    sa.ForeignKeyConstraint(['published_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_ref'),
    sa.UniqueConstraint('topic_id', 'version_number', name='uq_topic_content_version')
    )
    op.create_index(op.f('ix_textbook_topic_content_versions_status'), 'textbook_topic_content_versions', ['status'], unique=False)
    op.create_index(op.f('ix_textbook_topic_content_versions_topic_id'), 'textbook_topic_content_versions', ['topic_id'], unique=False)
    op.create_table('textbook_topic_documents',
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('role', sa.String(length=24), server_default='primary', nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('printed_start_page', sa.String(length=24), nullable=True),
    sa.Column('printed_end_page', sa.String(length=24), nullable=True),
    sa.Column('review_status', sa.String(length=20), server_default='pending', nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("review_status IN ('pending','processing','needs_review','ready','published','failed','superseded')", name='ck_topic_document_review_status'),
    sa.CheckConstraint("role IN ('primary','supporting','reference')", name='ck_topic_document_role'),
    sa.CheckConstraint('sequence > 0', name='ck_topic_document_sequence'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('topic_id', 'document_version_id'),
    sa.UniqueConstraint('topic_id', 'sequence', name='uq_topic_document_sequence')
    )
    op.create_index(op.f('ix_textbook_topic_documents_document_id'), 'textbook_topic_documents', ['document_id'], unique=False)
    op.create_index(op.f('ix_textbook_topic_documents_review_status'), 'textbook_topic_documents', ['review_status'], unique=False)
    op.create_table('topic_mastery',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('score', sa.Numeric(precision=8, scale=5), nullable=False),
    sa.Column('display_score', sa.Numeric(precision=3, scale=1), nullable=False),
    sa.Column('confidence', sa.String(length=12), nullable=False),
    sa.Column('provisional', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('evidence_count', sa.Integer(), nullable=False),
    sa.Column('evidence_weight', sa.Numeric(precision=10, scale=5), nullable=False),
    sa.Column('variety_count', sa.Integer(), nullable=False),
    sa.Column('trend', sa.Numeric(precision=8, scale=5), server_default='0', nullable=False),
    sa.Column('last_evidence_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('version_number', sa.Integer(), server_default='1', nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("confidence IN ('low','medium','high')", name='ck_topic_mastery_confidence'),
    sa.CheckConstraint('evidence_count >= 0 AND evidence_weight >= 0 AND variety_count >= 0 AND version_number > 0', name='ck_topic_mastery_counts'),
    sa.CheckConstraint('score BETWEEN 0 AND 10 AND display_score BETWEEN 0 AND 10', name='ck_topic_mastery_score'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'topic_id', name='uq_topic_mastery_student_topic')
    )
    op.create_index(op.f('ix_topic_mastery_student_id'), 'topic_mastery', ['student_id'], unique=False)
    op.create_index(op.f('ix_topic_mastery_subject_id'), 'topic_mastery', ['subject_id'], unique=False)
    op.create_index(op.f('ix_topic_mastery_topic_id'), 'topic_mastery', ['topic_id'], unique=False)
    op.create_table('tutor_sessions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=48), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('active_topic_id', sa.Uuid(), nullable=False),
    sa.Column('current_profile_version_id', sa.Uuid(), nullable=False),
    sa.Column('mode', sa.String(length=16), server_default='practice', nullable=False),
    sa.Column('status', sa.String(length=16), server_default='active', nullable=False),
    sa.Column('start_request_key', sa.String(length=100), nullable=False),
    sa.Column('end_request_key', sa.String(length=100), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("mode = 'practice'", name='ck_tutor_session_mode'),
    sa.CheckConstraint("status IN ('active','ended')", name='ck_tutor_session_status'),
    sa.ForeignKeyConstraint(['active_topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['current_profile_version_id'], ['tutor_profile_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'start_request_key', name='uq_tutor_session_start_request')
    )
    op.create_index(op.f('ix_tutor_sessions_active_topic_id'), 'tutor_sessions', ['active_topic_id'], unique=False)
    op.create_index(op.f('ix_tutor_sessions_public_ref'), 'tutor_sessions', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_sessions_status'), 'tutor_sessions', ['status'], unique=False)
    op.create_index(op.f('ix_tutor_sessions_student_id'), 'tutor_sessions', ['student_id'], unique=False)
    op.create_index(op.f('ix_tutor_sessions_subject_id'), 'tutor_sessions', ['subject_id'], unique=False)
    op.create_index('uq_active_tutor_session_per_student', 'tutor_sessions', ['student_id'], unique=True, postgresql_where=sa.text("status = 'active'"))
    op.create_table('assessment_questions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('source_question_version_id', sa.Uuid(), nullable=False),
    sa.Column('source_document_version_id', sa.Uuid(), nullable=False),
    sa.Column('question_number', sa.String(length=40), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('shared_stem', sa.Text(), server_default='', nullable=False),
    sa.Column('marks', sa.Integer(), nullable=False),
    sa.Column('equations', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('asset_ids', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('source_locations', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('rubric', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('topic_ids', sa.JSON(), nullable=False),
    sa.Column('topic_weights', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('skills', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('difficulty', sa.String(length=24), server_default='mixed', nullable=False),
    sa.CheckConstraint('sequence > 0 AND marks > 0', name='ck_assessment_question_values'),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_document_version_id'], ['document_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_question_version_id'], ['official_question_versions.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assessment_id', 'sequence', name='uq_assessment_question_sequence'),
    sa.UniqueConstraint('assessment_id', 'source_question_version_id', name='uq_assessment_question_source')
    )
    op.create_index(op.f('ix_assessment_questions_assessment_id'), 'assessment_questions', ['assessment_id'], unique=False)
    op.create_table('document_blocks',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('page_id', sa.Uuid(), nullable=False),
    sa.Column('sequence_number', sa.Integer(), nullable=False),
    sa.Column('block_kind', sa.String(length=32), nullable=False),
    sa.Column('text', sa.Text(), server_default='', nullable=False),
    sa.Column('latex', sa.Text(), nullable=True),
    sa.Column('bounding_box', sa.JSON(), nullable=False),
    sa.Column('extraction_method', sa.String(length=24), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('needs_review', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('source_asset_id', sa.Uuid(), nullable=True),
    sa.Column('block_metadata', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("block_kind IN ('heading','paragraph','table','question','subpart','answer_space','equation','image','diagram')", name='ck_document_blocks_kind'),
    sa.CheckConstraint('confidence BETWEEN 0 AND 1', name='ck_document_blocks_confidence'),
    sa.CheckConstraint('sequence_number > 0', name='ck_document_blocks_sequence'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['page_id', 'document_version_id'], ['document_pages.id', 'document_pages.document_version_id'], name='fk_document_block_page_version', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_asset_id', 'document_version_id'], ['document_assets.id', 'document_assets.document_version_id'], name='fk_document_block_source_asset_version', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('page_id', 'sequence_number', name='uq_document_block_sequence')
    )
    op.create_index(op.f('ix_document_blocks_block_kind'), 'document_blocks', ['block_kind'], unique=False)
    op.create_index(op.f('ix_document_blocks_document_version_id'), 'document_blocks', ['document_version_id'], unique=False)
    op.create_index(op.f('ix_document_blocks_page_id'), 'document_blocks', ['page_id'], unique=False)
    op.create_table('official_question_topic_mappings',
    sa.Column('question_version_id', sa.Uuid(), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.Column('required', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('suggestion_method', sa.String(length=40), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('rationale', sa.Text(), server_default='', nullable=False),
    sa.Column('confirmed_by', sa.Uuid(), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('draft','confirmed')", name='ck_official_question_topic_status'),
    sa.CheckConstraint('confidence IS NULL OR confidence BETWEEN 0 AND 1', name='ck_official_question_topic_confidence'),
    sa.CheckConstraint('weight BETWEEN 1 AND 100', name='ck_official_question_topic_weight'),
    sa.ForeignKeyConstraint(['confirmed_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['question_version_id'], ['official_question_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('question_version_id', 'topic_id')
    )
    op.create_table('retrieval_chunks',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('official_material_version_id', sa.Uuid(), nullable=True),
    sa.Column('group_id', sa.Uuid(), nullable=True),
    sa.Column('topic_id', sa.Uuid(), nullable=True),
    sa.Column('topic_content_version_id', sa.Uuid(), nullable=True),
    sa.Column('course_id', sa.String(length=32), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('source_type', sa.String(length=32), nullable=False),
    sa.Column('source_item_id', sa.Uuid(), nullable=False),
    sa.Column('source_ordinal', sa.Integer(), server_default='0', nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=False),
    sa.Column('bounding_box', sa.JSON(), nullable=False),
    sa.Column('source_asset_id', sa.Uuid(), nullable=True),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('embedding_model', sa.String(length=120), nullable=False),
    sa.Column('embedding_version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=256), nullable=False),
    sa.Column('status', sa.String(length=16), server_default='active', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("source_type IN ('textbook_section','marking_point','examiner_guidance')", name='ck_retrieval_chunk_source_type'),
    sa.CheckConstraint("status IN ('active','superseded')", name='ck_retrieval_chunk_status'),
    sa.CheckConstraint('page_number > 0 AND embedding_version > 0', name='ck_retrieval_chunk_values'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['group_id'], ['textbook_groups.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['official_material_version_id'], ['official_material_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_asset_id'], ['document_assets.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_content_version_id'], ['textbook_topic_content_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_type', 'source_item_id', 'source_ordinal', 'embedding_version', name='uq_retrieval_chunk_source_version')
    )
    op.create_index(op.f('ix_retrieval_chunks_course_id'), 'retrieval_chunks', ['course_id'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_document_id'), 'retrieval_chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_document_version_id'), 'retrieval_chunks', ['document_version_id'], unique=False)
    op.create_index('ix_retrieval_chunks_embedding_hnsw', 'retrieval_chunks', ['embedding'], unique=False, postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_index(op.f('ix_retrieval_chunks_group_id'), 'retrieval_chunks', ['group_id'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_official_material_version_id'), 'retrieval_chunks', ['official_material_version_id'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_source_item_id'), 'retrieval_chunks', ['source_item_id'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_source_type'), 'retrieval_chunks', ['source_type'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_status'), 'retrieval_chunks', ['status'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_subject_id'), 'retrieval_chunks', ['subject_id'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_topic_content_version_id'), 'retrieval_chunks', ['topic_content_version_id'], unique=False)
    op.create_index(op.f('ix_retrieval_chunks_topic_id'), 'retrieval_chunks', ['topic_id'], unique=False)
    op.create_table('textbook_topic_content_sources',
    sa.Column('content_version_id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('role', sa.String(length=24), nullable=False),
    sa.Column('extraction_version', sa.String(length=80), nullable=False),
    sa.CheckConstraint("role IN ('primary','supporting','reference')", name='ck_topic_content_source_role'),
    sa.ForeignKeyConstraint(['content_version_id'], ['textbook_topic_content_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('content_version_id', 'document_version_id')
    )
    op.create_table('topic_mastery_dimensions',
    sa.Column('mastery_id', sa.Uuid(), nullable=False),
    sa.Column('dimension', sa.String(length=24), nullable=False),
    sa.Column('score', sa.Numeric(precision=8, scale=5), nullable=False),
    sa.Column('evidence_weight', sa.Numeric(precision=10, scale=5), nullable=False),
    sa.CheckConstraint("dimension IN ('knowledge','application','method','accuracy','reasoning','communication','retention')", name='ck_topic_mastery_dimension_name'),
    sa.CheckConstraint('score BETWEEN 0 AND 10 AND evidence_weight >= 0', name='ck_topic_mastery_dimension_values'),
    sa.ForeignKeyConstraint(['mastery_id'], ['topic_mastery.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('mastery_id', 'dimension')
    )
    op.create_table('tutor_learner_context_logs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=48), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('active_topic_id', sa.Uuid(), nullable=False),
    sa.Column('request_key', sa.String(length=100), nullable=False),
    sa.Column('context_version', sa.String(length=64), nullable=False),
    sa.Column('evidence_references', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('context_snapshot', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['active_topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id', 'request_key', name='uq_tutor_context_request')
    )
    op.create_index(op.f('ix_tutor_learner_context_logs_active_topic_id'), 'tutor_learner_context_logs', ['active_topic_id'], unique=False)
    op.create_index(op.f('ix_tutor_learner_context_logs_context_version'), 'tutor_learner_context_logs', ['context_version'], unique=False)
    op.create_index(op.f('ix_tutor_learner_context_logs_public_ref'), 'tutor_learner_context_logs', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_learner_context_logs_session_id'), 'tutor_learner_context_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_tutor_learner_context_logs_student_id'), 'tutor_learner_context_logs', ['student_id'], unique=False)
    op.create_index(op.f('ix_tutor_learner_context_logs_subject_id'), 'tutor_learner_context_logs', ['subject_id'], unique=False)
    op.create_table('tutor_realtime_connections',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('profile_version_id', sa.Uuid(), nullable=False),
    sa.Column('account_id', sa.Uuid(), nullable=False),
    sa.Column('operation_id', sa.String(length=100), nullable=False),
    sa.Column('provider_session_id', sa.String(length=120), nullable=True),
    sa.Column('model', sa.String(length=120), nullable=False),
    sa.Column('voice', sa.String(length=40), nullable=False),
    sa.Column('language_mode', sa.String(length=32), nullable=False),
    sa.Column('reserved_seconds', sa.Integer(), nullable=False),
    sa.Column('billed_seconds', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='connecting', nullable=False),
    sa.Column('failure_code', sa.String(length=80), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('connected_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("language_mode IN ('auto','french_conversation','french_vocabulary','french_pronunciation')", name='ck_tutor_realtime_language_mode'),
    sa.CheckConstraint("status IN ('connecting','connected','ended','failed','cancelled')", name='ck_tutor_realtime_status'),
    sa.CheckConstraint('billed_seconds IS NULL OR billed_seconds >= 0', name='ck_tutor_realtime_billed_seconds'),
    sa.CheckConstraint('reserved_seconds > 0', name='ck_tutor_realtime_reserved_seconds'),
    sa.ForeignKeyConstraint(['account_id'], ['ai_provider_accounts.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['profile_version_id'], ['tutor_profile_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('operation_id')
    )
    op.create_index(op.f('ix_tutor_realtime_connections_account_id'), 'tutor_realtime_connections', ['account_id'], unique=False)
    op.create_index(op.f('ix_tutor_realtime_connections_provider_session_id'), 'tutor_realtime_connections', ['provider_session_id'], unique=False)
    op.create_index(op.f('ix_tutor_realtime_connections_public_ref'), 'tutor_realtime_connections', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_realtime_connections_session_id'), 'tutor_realtime_connections', ['session_id'], unique=False)
    op.create_index(op.f('ix_tutor_realtime_connections_student_id'), 'tutor_realtime_connections', ['student_id'], unique=False)
    op.create_table('tutor_session_profile_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('from_profile_version_id', sa.Uuid(), nullable=False),
    sa.Column('to_profile_version_id', sa.Uuid(), nullable=False),
    sa.Column('request_key', sa.String(length=100), nullable=False),
    sa.Column('handover_summary', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['from_profile_version_id'], ['tutor_profile_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['to_profile_version_id'], ['tutor_profile_versions.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id', 'request_key', name='uq_tutor_profile_switch_request')
    )
    op.create_index(op.f('ix_tutor_session_profile_events_session_id'), 'tutor_session_profile_events', ['session_id'], unique=False)
    op.create_table('tutor_session_summaries',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('topics_covered', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('activities', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('strengths', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('difficulties', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('next_steps', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('usage_data', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_tutor_session_summaries_public_ref'), 'tutor_session_summaries', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_session_summaries_student_id'), 'tutor_session_summaries', ['student_id'], unique=False)
    op.create_index(op.f('ix_tutor_session_summaries_subject_id'), 'tutor_session_summaries', ['subject_id'], unique=False)
    op.create_table('tutor_session_topic_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('from_topic_id', sa.Uuid(), nullable=False),
    sa.Column('to_topic_id', sa.Uuid(), nullable=False),
    sa.Column('request_key', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['from_topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['to_topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id', 'request_key', name='uq_tutor_topic_switch_request')
    )
    op.create_index(op.f('ix_tutor_session_topic_events_session_id'), 'tutor_session_topic_events', ['session_id'], unique=False)
    op.create_table('tutor_turns',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=48), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('profile_version_id', sa.Uuid(), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.Column('modality', sa.String(length=12), server_default='text', nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('response_data', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('operation_id', sa.Uuid(), nullable=True),
    sa.Column('provider', sa.String(length=40), nullable=True),
    sa.Column('model', sa.String(length=120), nullable=True),
    sa.Column('prompt_name', sa.String(length=80), nullable=True),
    sa.Column('prompt_version', sa.String(length=40), nullable=True),
    sa.Column('request_key', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('purged_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("modality IN ('text','voice')", name='ck_tutor_turn_modality'),
    sa.CheckConstraint("role IN ('student','assistant')", name='ck_tutor_turn_role'),
    sa.CheckConstraint('sequence > 0', name='ck_tutor_turn_sequence'),
    sa.ForeignKeyConstraint(['profile_version_id'], ['tutor_profile_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id', 'request_key', name='uq_tutor_turn_request'),
    sa.UniqueConstraint('session_id', 'sequence', name='uq_tutor_turn_sequence')
    )
    op.create_index(op.f('ix_tutor_turns_operation_id'), 'tutor_turns', ['operation_id'], unique=False)
    op.create_index(op.f('ix_tutor_turns_public_ref'), 'tutor_turns', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_turns_session_id'), 'tutor_turns', ['session_id'], unique=False)
    op.create_table('assessment_answers',
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('question_id', sa.Uuid(), nullable=False),
    sa.Column('answer_text', sa.Text(), server_default='', nullable=False),
    sa.Column('file_id', sa.String(length=120), nullable=True),
    sa.Column('save_revision', sa.Integer(), server_default='1', nullable=False),
    sa.Column('idempotency_key', sa.String(length=100), nullable=False),
    sa.Column('saved_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('save_revision > 0', name='ck_assessment_answer_revision'),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['assessment_questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('assessment_id', 'question_id'),
    sa.UniqueConstraint('assessment_id', 'idempotency_key', name='uq_assessment_answer_idempotency')
    )
    op.create_table('assessment_interactions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('question_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=24), nullable=False),
    sa.Column('request_key', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('hint')", name='ck_assessment_interaction_kind'),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['assessment_questions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assessment_id', 'question_id', 'request_key', name='uq_assessment_interaction_request')
    )
    op.create_index(op.f('ix_assessment_interactions_assessment_id'), 'assessment_interactions', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_assessment_interactions_question_id'), 'assessment_interactions', ['question_id'], unique=False)
    op.create_index(op.f('ix_assessment_interactions_student_id'), 'assessment_interactions', ['student_id'], unique=False)
    op.create_table('assessment_results',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('question_id', sa.Uuid(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('schema_version', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('answer_revision', sa.Integer(), nullable=False),
    sa.Column('input_hash', sa.String(length=64), nullable=False),
    sa.Column('request_key', sa.String(length=100), nullable=False),
    sa.Column('awarded_marks', sa.Integer(), nullable=False),
    sa.Column('max_marks', sa.Integer(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('marking_decisions', sa.JSON(), nullable=False),
    sa.Column('strengths', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('small_mistakes', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('conceptual_mistakes', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('improved_answer', sa.Text(), nullable=False),
    sa.Column('teaching_explanation', sa.Text(), nullable=False),
    sa.Column('topic_evidence', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('recommendations', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('review_reasons', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('model', sa.String(length=120), nullable=False),
    sa.Column('prompt_name', sa.String(length=80), nullable=False),
    sa.Column('prompt_version', sa.String(length=40), nullable=False),
    sa.Column('rubric_snapshot', sa.JSON(), nullable=False),
    sa.Column('source_manifest', sa.JSON(), nullable=False),
    sa.Column('pass_one_output', sa.JSON(), nullable=False),
    sa.Column('pass_two_output', sa.JSON(), nullable=False),
    sa.Column('subject_engine', sa.String(length=80), nullable=False),
    sa.Column('subject_engine_version', sa.String(length=40), nullable=False),
    sa.Column('deterministic_checks', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('published','needs_review')", name='ck_assessment_result_status'),
    sa.CheckConstraint('awarded_marks BETWEEN 0 AND max_marks AND max_marks > 0', name='ck_assessment_result_marks'),
    sa.CheckConstraint('confidence BETWEEN 0 AND 1', name='ck_assessment_result_confidence'),
    sa.CheckConstraint('version_number > 0 AND answer_revision >= 0', name='ck_assessment_result_versions'),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['assessment_questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assessment_id', 'question_id', 'request_key', name='uq_assessment_result_request'),
    sa.UniqueConstraint('question_id', 'version_number', name='uq_assessment_result_question_version')
    )
    op.create_index(op.f('ix_assessment_results_assessment_id'), 'assessment_results', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_assessment_results_input_hash'), 'assessment_results', ['input_hash'], unique=False)
    op.create_index(op.f('ix_assessment_results_question_id'), 'assessment_results', ['question_id'], unique=False)
    op.create_index(op.f('ix_assessment_results_status'), 'assessment_results', ['status'], unique=False)
    op.create_table('assessment_working_files',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('question_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=80), nullable=False),
    sa.Column('byte_size', sa.Integer(), nullable=False),
    sa.Column('checksum', sa.String(length=64), nullable=False),
    sa.Column('object_key', sa.String(length=500), nullable=False),
    sa.Column('ocr_text', sa.Text(), server_default='', nullable=False),
    sa.Column('ocr_confidence', sa.Float(), server_default='0', nullable=False),
    sa.Column('ocr_metadata', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('byte_size > 0', name='ck_assessment_working_file_size'),
    sa.CheckConstraint('ocr_confidence BETWEEN 0 AND 1', name='ck_assessment_working_ocr_confidence'),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['assessment_questions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('object_key')
    )
    op.create_index(op.f('ix_assessment_working_files_assessment_id'), 'assessment_working_files', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_assessment_working_files_question_id'), 'assessment_working_files', ['question_id'], unique=False)
    op.create_index(op.f('ix_assessment_working_files_student_id'), 'assessment_working_files', ['student_id'], unique=False)
    op.create_table('educational_media',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('source_chunk_id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=28), nullable=False),
    sa.Column('title', sa.String(length=180), nullable=False),
    sa.Column('alt_text', sa.String(length=1000), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('prompt_version', sa.String(length=40), nullable=False),
    sa.Column('parameters', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('source_manifest', sa.JSON(), nullable=False),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('model', sa.String(length=120), nullable=False),
    sa.Column('response_id', sa.String(length=180), nullable=True),
    sa.Column('object_key', sa.String(length=500), nullable=False),
    sa.Column('content_type', sa.String(length=80), nullable=False),
    sa.Column('checksum', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('reviewed_by', sa.Uuid(), nullable=True),
    sa.Column('review_notes', sa.Text(), server_default='', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("kind IN ('circuit_svg','forces_svg','geometry_svg','plot_svg','conceptual_image')", name='ck_educational_media_kind'),
    sa.CheckConstraint("status IN ('pending_review','published','rejected')", name='ck_educational_media_status'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_chunk_id'], ['retrieval_chunks.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('object_key')
    )
    op.create_index(op.f('ix_educational_media_created_at'), 'educational_media', ['created_at'], unique=False)
    op.create_index(op.f('ix_educational_media_created_by'), 'educational_media', ['created_by'], unique=False)
    op.create_index(op.f('ix_educational_media_kind'), 'educational_media', ['kind'], unique=False)
    op.create_index(op.f('ix_educational_media_source_chunk_id'), 'educational_media', ['source_chunk_id'], unique=False)
    op.create_index(op.f('ix_educational_media_status'), 'educational_media', ['status'], unique=False)
    op.create_index(op.f('ix_educational_media_subject_id'), 'educational_media', ['subject_id'], unique=False)
    op.create_index(op.f('ix_educational_media_topic_id'), 'educational_media', ['topic_id'], unique=False)
    op.create_table('tutor_practices',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('question_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.String(length=16), server_default='active', nullable=False),
    sa.Column('request_key', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('active','submitted')", name='ck_tutor_practice_status'),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['question_id'], ['assessment_questions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assessment_id'),
    sa.UniqueConstraint('question_id'),
    sa.UniqueConstraint('session_id', 'request_key', name='uq_tutor_practice_request')
    )
    op.create_index(op.f('ix_tutor_practices_public_ref'), 'tutor_practices', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_practices_session_id'), 'tutor_practices', ['session_id'], unique=False)
    op.create_index(op.f('ix_tutor_practices_status'), 'tutor_practices', ['status'], unique=False)
    op.create_index(op.f('ix_tutor_practices_student_id'), 'tutor_practices', ['student_id'], unique=False)
    op.create_index(op.f('ix_tutor_practices_subject_id'), 'tutor_practices', ['subject_id'], unique=False)
    op.create_index(op.f('ix_tutor_practices_topic_id'), 'tutor_practices', ['topic_id'], unique=False)
    op.create_index('uq_active_tutor_practice_session', 'tutor_practices', ['session_id'], unique=True, postgresql_where=sa.text("status = 'active'"))
    op.create_table('tutor_safety_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('parent_id', sa.Uuid(), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('source_turn_id', sa.Uuid(), nullable=False),
    sa.Column('category', sa.String(length=32), nullable=False),
    sa.Column('severity', sa.String(length=16), nullable=False),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('notification_status', sa.String(length=20), server_default='notified', nullable=False),
    sa.Column('notified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_status', sa.String(length=20), server_default='pending', nullable=False),
    sa.Column('reviewed_by', sa.Uuid(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("notification_status IN ('pending','notified')", name='ck_tutor_safety_notification'),
    sa.CheckConstraint("review_status IN ('pending','reviewed','resolved')", name='ck_tutor_safety_review'),
    sa.CheckConstraint("severity IN ('low','medium','high','critical')", name='ck_tutor_safety_severity'),
    sa.ForeignKeyConstraint(['parent_id'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_turn_id'], ['tutor_turns.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_turn_id', 'category', name='uq_tutor_safety_turn_category')
    )
    op.create_index(op.f('ix_tutor_safety_events_parent_id'), 'tutor_safety_events', ['parent_id'], unique=False)
    op.create_index(op.f('ix_tutor_safety_events_public_ref'), 'tutor_safety_events', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_safety_events_session_id'), 'tutor_safety_events', ['session_id'], unique=False)
    op.create_index(op.f('ix_tutor_safety_events_student_id'), 'tutor_safety_events', ['student_id'], unique=False)
    op.create_table('tutor_signals',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_ref', sa.String(length=56), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('turn_id', sa.Uuid(), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('category', sa.String(length=32), nullable=False),
    sa.Column('observation', sa.Text(), nullable=False),
    sa.Column('evidence_references', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('prompt_name', sa.String(length=80), nullable=False),
    sa.Column('prompt_version', sa.String(length=40), nullable=False),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('model', sa.String(length=120), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("category IN ('engagement','confidence','misconception','practice_need')", name='ck_tutor_signal_category'),
    sa.CheckConstraint('confidence BETWEEN 0 AND 1', name='ck_tutor_signal_confidence'),
    sa.ForeignKeyConstraint(['session_id'], ['tutor_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['turn_id'], ['tutor_turns.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tutor_signals_created_at'), 'tutor_signals', ['created_at'], unique=False)
    op.create_index(op.f('ix_tutor_signals_public_ref'), 'tutor_signals', ['public_ref'], unique=True)
    op.create_index(op.f('ix_tutor_signals_session_id'), 'tutor_signals', ['session_id'], unique=False)
    op.create_index(op.f('ix_tutor_signals_student_id'), 'tutor_signals', ['student_id'], unique=False)
    op.create_index(op.f('ix_tutor_signals_topic_id'), 'tutor_signals', ['topic_id'], unique=False)
    op.create_index(op.f('ix_tutor_signals_turn_id'), 'tutor_signals', ['turn_id'], unique=False)
    op.create_table('tutor_turn_sources',
    sa.Column('turn_id', sa.Uuid(), nullable=False),
    sa.Column('retrieval_chunk_id', sa.Uuid(), nullable=False),
    sa.Column('ordinal', sa.Integer(), nullable=False),
    sa.CheckConstraint('ordinal >= 0', name='ck_tutor_turn_source_ordinal'),
    sa.ForeignKeyConstraint(['retrieval_chunk_id'], ['retrieval_chunks.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['turn_id'], ['tutor_turns.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('turn_id', 'retrieval_chunk_id')
    )
    op.create_table('topic_mastery_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('mastery_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('trigger_result_id', sa.Uuid(), nullable=False),
    sa.Column('previous_score', sa.Numeric(precision=8, scale=5), nullable=True),
    sa.Column('new_score', sa.Numeric(precision=8, scale=5), nullable=False),
    sa.Column('previous_confidence', sa.String(length=12), nullable=True),
    sa.Column('new_confidence', sa.String(length=12), nullable=False),
    sa.Column('contribution', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('new_score BETWEEN 0 AND 10', name='ck_topic_mastery_event_new'),
    sa.CheckConstraint('previous_score IS NULL OR previous_score BETWEEN 0 AND 10', name='ck_topic_mastery_event_previous'),
    sa.ForeignKeyConstraint(['mastery_id'], ['topic_mastery.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['trigger_result_id'], ['assessment_results.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('topic_id', 'trigger_result_id', name='uq_topic_mastery_event_trigger')
    )
    op.create_index(op.f('ix_topic_mastery_events_created_at'), 'topic_mastery_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_topic_mastery_events_mastery_id'), 'topic_mastery_events', ['mastery_id'], unique=False)
    op.create_index(op.f('ix_topic_mastery_events_student_id'), 'topic_mastery_events', ['student_id'], unique=False)
    op.create_index(op.f('ix_topic_mastery_events_topic_id'), 'topic_mastery_events', ['topic_id'], unique=False)
    op.create_index(op.f('ix_topic_mastery_events_trigger_result_id'), 'topic_mastery_events', ['trigger_result_id'], unique=False)
    op.create_table('weakness_diagnoses',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('result_id', sa.Uuid(), nullable=False),
    sa.Column('question_id', sa.Uuid(), nullable=False),
    sa.Column('category', sa.String(length=40), nullable=False),
    sa.Column('dimension', sa.String(length=24), nullable=False),
    sa.Column('severity', sa.String(length=12), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('evidence', sa.JSON(), nullable=False),
    sa.Column('occurrence_number', sa.Integer(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("severity IN ('minor','moderate','major')", name='ck_weakness_diagnosis_severity'),
    sa.CheckConstraint('confidence BETWEEN 0 AND 1 AND occurrence_number > 0', name='ck_weakness_diagnosis_values'),
    sa.ForeignKeyConstraint(['question_id'], ['assessment_questions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['result_id'], ['assessment_results.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('result_id', 'topic_id', 'category', name='uq_weakness_diagnosis_result_topic_category')
    )
    op.create_index(op.f('ix_weakness_diagnoses_category'), 'weakness_diagnoses', ['category'], unique=False)
    op.create_index(op.f('ix_weakness_diagnoses_created_at'), 'weakness_diagnoses', ['created_at'], unique=False)
    op.create_index(op.f('ix_weakness_diagnoses_result_id'), 'weakness_diagnoses', ['result_id'], unique=False)
    op.create_index(op.f('ix_weakness_diagnoses_student_id'), 'weakness_diagnoses', ['student_id'], unique=False)
    op.create_index(op.f('ix_weakness_diagnoses_subject_id'), 'weakness_diagnoses', ['subject_id'], unique=False)
    op.create_index(op.f('ix_weakness_diagnoses_topic_id'), 'weakness_diagnoses', ['topic_id'], unique=False)
    op.create_table('improvement_recommendations',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('diagnosis_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('source_chunk_id', sa.Uuid(), nullable=False),
    sa.Column('activity_question_version_id', sa.Uuid(), nullable=True),
    sa.Column('activity_type', sa.String(length=24), nullable=False),
    sa.Column('title', sa.String(length=180), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('action', sa.Text(), nullable=False),
    sa.Column('success_condition', sa.Text(), nullable=False),
    sa.Column('review_status', sa.String(length=20), nullable=False),
    sa.Column('review_reason', sa.Text(), server_default='', nullable=False),
    sa.Column('reviewed_by', sa.Uuid(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("activity_type IN ('review','targeted_practice','spaced_retry','unit_check')", name='ck_improvement_recommendation_activity'),
    sa.CheckConstraint("review_status IN ('approved','pending_review','rejected')", name='ck_improvement_recommendation_review'),
    sa.ForeignKeyConstraint(['activity_question_version_id'], ['official_question_versions.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['diagnosis_id'], ['weakness_diagnoses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_chunk_id'], ['retrieval_chunks.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('diagnosis_id', 'activity_type', name='uq_improvement_recommendation_activity')
    )
    op.create_index(op.f('ix_improvement_recommendations_created_at'), 'improvement_recommendations', ['created_at'], unique=False)
    op.create_index(op.f('ix_improvement_recommendations_diagnosis_id'), 'improvement_recommendations', ['diagnosis_id'], unique=False)
    op.create_index(op.f('ix_improvement_recommendations_review_status'), 'improvement_recommendations', ['review_status'], unique=False)
    op.create_index(op.f('ix_improvement_recommendations_student_id'), 'improvement_recommendations', ['student_id'], unique=False)
    op.create_index(op.f('ix_improvement_recommendations_subject_id'), 'improvement_recommendations', ['subject_id'], unique=False)
    op.create_index(op.f('ix_improvement_recommendations_topic_id'), 'improvement_recommendations', ['topic_id'], unique=False)
    op.create_table('study_plan_items',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('plan_id', sa.Uuid(), nullable=False),
    sa.Column('student_id', sa.Uuid(), nullable=False),
    sa.Column('recommendation_id', sa.Uuid(), nullable=False),
    sa.Column('subject_id', sa.String(length=32), nullable=False),
    sa.Column('topic_id', sa.Uuid(), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('activity_type', sa.String(length=24), nullable=False),
    sa.Column('title', sa.String(length=180), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('source_chunk_id', sa.Uuid(), nullable=False),
    sa.Column('success_condition', sa.Text(), nullable=False),
    sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('planned','completed')", name='ck_study_plan_item_status'),
    sa.CheckConstraint('sequence > 0 AND duration_minutes BETWEEN 5 AND 120', name='ck_study_plan_item_values'),
    sa.ForeignKeyConstraint(['plan_id'], ['study_plans.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['recommendation_id'], ['improvement_recommendations.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_chunk_id'], ['retrieval_chunks.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['topic_id'], ['textbook_topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('plan_id', 'recommendation_id', name='uq_study_plan_item_recommendation'),
    sa.UniqueConstraint('plan_id', 'sequence', name='uq_study_plan_item_sequence')
    )
    op.create_index(op.f('ix_study_plan_items_plan_id'), 'study_plan_items', ['plan_id'], unique=False)
    op.create_index(op.f('ix_study_plan_items_status'), 'study_plan_items', ['status'], unique=False)
    op.create_index(op.f('ix_study_plan_items_student_id'), 'study_plan_items', ['student_id'], unique=False)
    op.create_index(op.f('ix_study_plan_items_subject_id'), 'study_plan_items', ['subject_id'], unique=False)
    op.create_index(op.f('ix_study_plan_items_topic_id'), 'study_plan_items', ['topic_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    raise RuntimeError(
        "The AKURU initial baseline cannot be downgraded because that would destroy "
        "all application data. Restore a reviewed backup instead."
    )
