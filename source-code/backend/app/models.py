import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, ForeignKeyConstraint, Index, Integer,
    JSON, Numeric, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import VECTOR

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PARENT = "parent"
    STUDENT = "student"


class DocumentKind(str, enum.Enum):
    TEXTBOOK = "textbook"
    REFERENCE = "reference"
    PAST_PAPER = "past_paper"
    MARK_SCHEME = "mark_scheme"
    EXAMINER_REPORT = "examiner_report"


class ReviewState(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    REJECTED = "rejected"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    display_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(16))
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    __table_args__ = (CheckConstraint("role IN ('admin','parent','student')", name="ck_users_role"),)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    client_ip_hash: Mapped[str] = mapped_column(String(64))
    user_agent: Mapped[str] = mapped_column(String(300), default="")


class LoginThrottle(Base):
    __tablename__ = "login_throttles"
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint("failure_count >= 0", name="ck_login_failure_count"),)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str] = mapped_column(String(80), index=True)
    event_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    parent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    phase1_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class StudentProgression(TimestampMixin, Base):
    __tablename__ = "student_progressions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    grade: Mapped[int] = mapped_column(Integer)
    term: Mapped[int] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    __table_args__ = (
        CheckConstraint("grade IN (10, 11)", name="ck_progression_grade"),
        CheckConstraint("term IN (1, 2, 3)", name="ck_progression_term"),
        UniqueConstraint("student_id", "course_id", "grade", "term", name="uq_student_progression_period"),
        Index("uq_current_progression_per_student", "student_id", unique=True, postgresql_where=text("is_current")),
    )


class StudentSubject(TimestampMixin, Base):
    __tablename__ = "student_subjects"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), primary_key=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), primary_key=True)


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(24))
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    original_filename: Mapped[str] = mapped_column(String(255))
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    review_state: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending")
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="RESTRICT"))
    edition: Mapped[str | None] = mapped_column(String(80))
    publication_year: Mapped[int | None] = mapped_column(Integer)
    exam_session: Mapped[str | None] = mapped_column(String(80))
    component: Mapped[str | None] = mapped_column(String(80))
    variant: Mapped[str | None] = mapped_column(String(80))
    source_metadata: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("kind IN ('textbook','reference','past_paper','mark_scheme','examiner_report')", name="ck_documents_kind"),
        CheckConstraint("review_state IN ('pending','reviewed','published','rejected')", name="ck_documents_review_state"),
        CheckConstraint("size_bytes >= 0", name="ck_documents_size_bytes"),
        CheckConstraint(
            "publication_year IS NULL OR publication_year BETWEEN 1900 AND 2100",
            name="ck_documents_publication_year",
        ),
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    original_filename: Mapped[str] = mapped_column(String(255))
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="uploaded", server_default="uploaded")
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("version_number > 0", name="ck_document_versions_number"),
        CheckConstraint("size_bytes > 0", name="ck_document_versions_size"),
        CheckConstraint(
            "status IN ('uploaded','queued','processing','needs_review','failed','completed','removed')",
            name="ck_document_versions_status",
        ),
        UniqueConstraint("document_id", "version_number", name="uq_document_version_number"),
    )


class DocumentAsset(Base):
    __tablename__ = "document_assets"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    asset_kind: Mapped[str] = mapped_column(String(40))
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer)
    bounding_box: Mapped[dict | None] = mapped_column(JSON)
    asset_metadata: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_document_assets_size"),
        CheckConstraint("page_number IS NULL OR page_number > 0", name="ck_document_assets_page"),
        UniqueConstraint("id", "document_version_id", name="uq_document_asset_version"),
    )


class DocumentPage(Base):
    __tablename__ = "document_pages"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    page_number: Mapped[int] = mapped_column(Integer)
    width_points: Mapped[float] = mapped_column()
    height_points: Mapped[float] = mapped_column()
    render_asset_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    native_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    extraction_method: Mapped[str] = mapped_column(String(24))
    confidence: Mapped[float] = mapped_column()
    needs_review: Mapped[bool] = mapped_column(default=False, server_default="false")
    page_metadata: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("page_number > 0", name="ck_document_pages_number"),
        CheckConstraint("width_points > 0 AND height_points > 0", name="ck_document_pages_dimensions"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_document_pages_confidence"),
        ForeignKeyConstraint(
            ["render_asset_id", "document_version_id"],
            ["document_assets.id", "document_assets.document_version_id"],
            ondelete="RESTRICT",
            name="fk_document_page_render_asset_version",
        ),
        UniqueConstraint("id", "document_version_id", name="uq_document_page_version"),
        UniqueConstraint("document_version_id", "page_number", name="uq_document_page_number"),
    )


class DocumentBlock(Base):
    __tablename__ = "document_blocks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    page_id: Mapped[uuid.UUID] = mapped_column(index=True)
    sequence_number: Mapped[int] = mapped_column(Integer)
    block_kind: Mapped[str] = mapped_column(String(32), index=True)
    text: Mapped[str] = mapped_column(Text, default="", server_default="")
    latex: Mapped[str | None] = mapped_column(Text)
    bounding_box: Mapped[dict] = mapped_column(JSON)
    extraction_method: Mapped[str] = mapped_column(String(24))
    confidence: Mapped[float] = mapped_column()
    needs_review: Mapped[bool] = mapped_column(default=False, server_default="false")
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column()
    block_metadata: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("sequence_number > 0", name="ck_document_blocks_sequence"),
        CheckConstraint(
            "block_kind IN ('heading','paragraph','table','question','subpart','answer_space','equation','image','diagram')",
            name="ck_document_blocks_kind",
        ),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_document_blocks_confidence"),
        ForeignKeyConstraint(
            ["page_id", "document_version_id"],
            ["document_pages.id", "document_pages.document_version_id"],
            ondelete="CASCADE",
            name="fk_document_block_page_version",
        ),
        ForeignKeyConstraint(
            ["source_asset_id", "document_version_id"],
            ["document_assets.id", "document_assets.document_version_id"],
            ondelete="RESTRICT",
            name="fk_document_block_source_asset_version",
        ),
        UniqueConstraint("page_id", "sequence_number", name="uq_document_block_sequence"),
    )


class DocumentEvent(Base):
    __tablename__ = "document_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    event_data: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class DocumentJob(Base):
    __tablename__ = "document_jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(String(40), default="preflight", server_default="preflight")
    status: Mapped[str] = mapped_column(String(24), default="queued", server_default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    extraction_version: Mapped[str] = mapped_column(String(80))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(String(500))
    result_data: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    max_seconds: Mapped[int] = mapped_column(Integer)
    max_memory_mb: Mapped[int] = mapped_column(Integer)
    max_pages: Mapped[int] = mapped_column(Integer)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','processing','needs_review','failed','completed')",
            name="ck_document_jobs_status",
        ),
        CheckConstraint("progress BETWEEN 0 AND 100", name="ck_document_jobs_progress"),
        CheckConstraint("attempt_count >= 0", name="ck_document_jobs_attempt_count"),
        CheckConstraint("max_seconds > 0", name="ck_document_jobs_max_seconds"),
        CheckConstraint("max_memory_mb > 0", name="ck_document_jobs_max_memory"),
        CheckConstraint("max_pages > 0", name="ck_document_jobs_max_pages"),
        UniqueConstraint(
            "document_version_id", "stage", "extraction_version",
            name="uq_document_job_stage_version",
        ),
    )


class DocumentStageRun(Base):
    __tablename__ = "document_stage_runs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(String(40))
    extraction_version: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(24))
    input_checksum: Mapped[str] = mapped_column(String(64))
    output_data: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("status IN ('processing','failed','completed')", name="ck_document_stage_runs_status"),
        UniqueConstraint(
            "document_version_id", "stage", "extraction_version",
            name="uq_document_stage_run_version",
        ),
    )


class AIInvocation(Base):
    __tablename__ = "ai_invocations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_versions.id", ondelete="SET NULL"), index=True
    )
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    purpose: Mapped[str] = mapped_column(String(40), index=True)
    prompt_name: Mapped[str] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(40))
    schema_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(24), index=True)
    response_id: Mapped[str | None] = mapped_column(String(120), index=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    request_metadata: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    error_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('textbook_extraction','paper_extraction','unit_mapping','assessment','tutoring')",
            name="ck_ai_invocations_purpose",
        ),
        CheckConstraint("status IN ('processing','completed','failed')", name="ck_ai_invocations_status"),
        CheckConstraint("attempt_count >= 0", name="ck_ai_invocations_attempt_count"),
        CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_ai_invocations_latency"),
        CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="ck_ai_invocations_input_tokens"),
        CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="ck_ai_invocations_output_tokens"),
        CheckConstraint("total_tokens IS NULL OR total_tokens >= 0", name="ck_ai_invocations_total_tokens"),
    )


class AIProviderAccount(TimestampMixin, Base):
    __tablename__ = "ai_provider_accounts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(120), unique=True)
    credential_alias: Mapped[str] = mapped_column(String(40), unique=True)
    priority: Mapped[int] = mapped_column(Integer, unique=True)
    model: Mapped[str] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    health_status: Mapped[str] = mapped_column(String(24), default="unknown", server_default="unknown")
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(80))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("priority BETWEEN 0 AND 100", name="ck_ai_provider_accounts_priority"),
        CheckConstraint(
            "health_status IN ('unknown','available','cooldown','credit_exhausted','invalid_credential')",
            name="ck_ai_provider_accounts_health",
        ),
    )


class AIProviderAttempt(Base):
    __tablename__ = "ai_provider_attempts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    operation_id: Mapped[uuid.UUID] = mapped_column(index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_provider_accounts.id", ondelete="RESTRICT"), index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(24))
    response_id: Mapped[str | None] = mapped_column(String(120))
    error_code: Mapped[str | None] = mapped_column(String(80))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("attempt_number > 0", name="ck_ai_provider_attempts_number"),
        CheckConstraint("status IN ('processing','completed','failed')", name="ck_ai_provider_attempts_status"),
        UniqueConstraint("operation_id", "attempt_number", name="uq_ai_provider_attempt_operation_number"),
    )


class TextbookContentVersion(Base):
    __tablename__ = "textbook_content_versions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    source_document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id", ondelete="RESTRICT"))
    version_number: Mapped[int] = mapped_column(Integer)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    edition: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    published_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("version_number > 0", name="ck_textbook_content_version_number"),
        CheckConstraint("status IN ('draft','published','superseded')", name="ck_textbook_content_version_status"),
        UniqueConstraint("document_id", "version_number", name="uq_textbook_content_version"),
    )


class TextbookUnitVersion(Base):
    __tablename__ = "textbook_unit_versions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    content_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_content_versions.id", ondelete="CASCADE"), index=True)
    unit_code: Mapped[str] = mapped_column(String(80))
    chapter: Mapped[str] = mapped_column(String(240), default="", server_default="")
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str] = mapped_column(Text, default="", server_default="")
    sequence: Mapped[int] = mapped_column(Integer)
    start_page: Mapped[int] = mapped_column(Integer)
    end_page: Mapped[int] = mapped_column(Integer)
    sections: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    definitions: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    concepts: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    equations: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    examples: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    diagrams: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    __table_args__ = (
        CheckConstraint("sequence > 0", name="ck_textbook_unit_version_sequence"),
        CheckConstraint("start_page > 0 AND end_page >= start_page", name="ck_textbook_unit_version_pages"),
        UniqueConstraint("content_version_id", "unit_code", name="uq_textbook_unit_version_code"),
    )


class TextbookUnit(TimestampMixin, Base):
    __tablename__ = "textbook_units"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    textbook_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    unit_code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(240))
    sequence: Mapped[int] = mapped_column(Integer)
    content_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("textbook_content_versions.id", ondelete="RESTRICT"), index=True
    )
    __table_args__ = (
        UniqueConstraint("textbook_id", "content_version_id", "unit_code", name="uq_textbook_unit_code"),
        UniqueConstraint("id", "course_id", "subject_id", name="uq_unit_scope"),
    )


class CurriculumPlan(Base):
    __tablename__ = "curriculum_plans"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    textbook_content_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_content_versions.id", ondelete="RESTRICT"))
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    published_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("version_number > 0", name="ck_curriculum_plan_version"),
        CheckConstraint("status IN ('draft','published','superseded')", name="ck_curriculum_plan_status"),
        UniqueConstraint("course_id", "subject_id", "version_number", name="uq_curriculum_plan_version"),
    )


class CurriculumPlanUnit(Base):
    __tablename__ = "curriculum_plan_units"
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_plans.id", ondelete="CASCADE"), primary_key=True)
    grade: Mapped[int] = mapped_column(Integer, primary_key=True)
    term: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="RESTRICT"), primary_key=True)
    __table_args__ = (
        CheckConstraint("grade IN (10, 11)", name="ck_curriculum_plan_unit_grade"),
        CheckConstraint("term IN (1, 2, 3)", name="ck_curriculum_plan_unit_term"),
    )


class AssessmentCurriculumSnapshot(Base):
    __tablename__ = "assessment_curriculum_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assessment_ref: Mapped[str] = mapped_column(String(120), unique=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="RESTRICT"), index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_plans.id", ondelete="RESTRICT"))
    course_id: Mapped[str] = mapped_column(String(32))
    subject_id: Mapped[str] = mapped_column(String(32))
    grade: Mapped[int] = mapped_column(Integer)
    term: Mapped[int] = mapped_column(Integer)
    covered_unit_ids: Mapped[list] = mapped_column(JSON)
    progression_periods: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("grade IN (10, 11)", name="ck_assessment_snapshot_grade"),
        CheckConstraint("term IN (1, 2, 3)", name="ck_assessment_snapshot_term"),
    )


class OfficialMaterialVersion(Base):
    __tablename__ = "official_material_versions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    source_document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id", ondelete="RESTRICT"))
    version_number: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(24))
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    source_paper_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="RESTRICT"))
    source_paper_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("official_material_versions.id", ondelete="RESTRICT"))
    textbook_content_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("textbook_content_versions.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    inventory_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    completeness_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    published_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("kind IN ('past_paper','mark_scheme','examiner_report')", name="ck_official_material_kind"),
        CheckConstraint("status IN ('draft','published','superseded')", name="ck_official_material_status"),
        CheckConstraint("version_number > 0 AND inventory_count >= 0", name="ck_official_material_counts"),
        UniqueConstraint("document_id", "version_number", name="uq_official_material_version"),
    )


class OfficialQuestionVersion(Base):
    __tablename__ = "official_question_versions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    material_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("official_material_versions.id", ondelete="CASCADE"), index=True)
    question_number: Mapped[str] = mapped_column(String(40))
    parent_number: Mapped[str | None] = mapped_column(String(40))
    prompt: Mapped[str] = mapped_column(Text)
    shared_stem: Mapped[str] = mapped_column(Text, default="", server_default="")
    marks: Mapped[int] = mapped_column(Integer)
    equations: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    asset_ids: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    source_locations: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    mapping_status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    __table_args__ = (
        CheckConstraint("marks > 0", name="ck_official_question_marks"),
        CheckConstraint("mapping_status IN ('pending','draft','confirmed')", name="ck_official_question_mapping_status"),
        UniqueConstraint("material_version_id", "question_number", name="uq_official_question_number"),
    )


class OfficialQuestionUnitMapping(Base):
    __tablename__ = "official_question_unit_mappings"
    question_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("official_question_versions.id", ondelete="CASCADE"), primary_key=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="RESTRICT"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    suggestion_method: Mapped[str | None] = mapped_column(String(40))
    confidence: Mapped[float | None] = mapped_column()
    rationale: Mapped[str] = mapped_column(Text, default="", server_default="")
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("weight BETWEEN 1 AND 100", name="ck_official_question_unit_weight"),
        CheckConstraint("status IN ('draft','confirmed')", name="ck_official_question_unit_status"),
        CheckConstraint("confidence IS NULL OR confidence BETWEEN 0 AND 1", name="ck_official_question_unit_confidence"),
    )


class MarkSchemeEntryVersion(Base):
    __tablename__ = "mark_scheme_entry_versions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    material_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("official_material_versions.id", ondelete="CASCADE"), index=True)
    question_number: Mapped[str] = mapped_column(String(40))
    max_marks: Mapped[int] = mapped_column(Integer)
    marking_points: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    alternatives: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    source_locations: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    __table_args__ = (
        CheckConstraint("max_marks > 0", name="ck_mark_scheme_entry_marks"),
        UniqueConstraint("material_version_id", "question_number", name="uq_mark_scheme_entry_number"),
    )


class ExaminerCommentVersion(Base):
    __tablename__ = "examiner_comment_versions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    material_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("official_material_versions.id", ondelete="CASCADE"), index=True)
    question_number: Mapped[str] = mapped_column(String(40))
    common_mistakes: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    advice: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    source_locations: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    __table_args__ = (UniqueConstraint("material_version_id", "question_number", name="uq_examiner_comment_number"),)


class RetrievalChunk(Base):
    __tablename__ = "retrieval_chunks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    textbook_content_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("textbook_content_versions.id", ondelete="CASCADE"), index=True)
    official_material_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("official_material_versions.id", ondelete="CASCADE"), index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True)
    source_item_id: Mapped[uuid.UUID] = mapped_column(index=True)
    source_ordinal: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    content: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int] = mapped_column(Integer)
    bounding_box: Mapped[dict] = mapped_column(JSON)
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("document_assets.id", ondelete="SET NULL"))
    content_hash: Mapped[str] = mapped_column(String(64))
    embedding_model: Mapped[str] = mapped_column(String(120))
    embedding_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    embedding: Mapped[list] = mapped_column(VECTOR(256))
    status: Mapped[str] = mapped_column(String(16), default="active", server_default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("source_type IN ('textbook_section','marking_point','examiner_guidance')", name="ck_retrieval_chunk_source_type"),
        CheckConstraint("status IN ('active','superseded')", name="ck_retrieval_chunk_status"),
        CheckConstraint("page_number > 0 AND embedding_version > 0", name="ck_retrieval_chunk_values"),
        UniqueConstraint("source_type", "source_item_id", "source_ordinal", "embedding_version", name="uq_retrieval_chunk_source_version"),
        Index("ix_retrieval_chunks_embedding_hnsw", "embedding", postgresql_using="hnsw",
              postgresql_ops={"embedding": "vector_cosine_ops"}),
    )


class TermCoverage(TimestampMixin, Base):
    __tablename__ = "term_coverage"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    grade: Mapped[int] = mapped_column(Integer)
    term: Mapped[int] = mapped_column(Integer)
    unit_id: Mapped[uuid.UUID] = mapped_column()
    __table_args__ = (
        CheckConstraint("grade IN (10, 11)", name="ck_coverage_grade"),
        CheckConstraint("term IN (1, 2, 3)", name="ck_coverage_term"),
        UniqueConstraint("course_id", "subject_id", "grade", "term", "unit_id", name="uq_term_coverage"),
        ForeignKeyConstraint(
            ["unit_id", "course_id", "subject_id"],
            ["textbook_units.id", "textbook_units.course_id", "textbook_units.subject_id"],
            ondelete="CASCADE",
            name="fk_coverage_unit_scope",
        ),
    )


class Question(TimestampMixin, Base):
    __tablename__ = "questions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    question_number: Mapped[str] = mapped_column(String(40))
    prompt: Mapped[str] = mapped_column(Text)
    marks: Mapped[int] = mapped_column(Integer)
    review_state: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending")
    __table_args__ = (
        CheckConstraint("marks > 0", name="ck_questions_marks"),
        CheckConstraint("review_state IN ('pending','reviewed','published','rejected')", name="ck_questions_review_state"),
        UniqueConstraint("paper_id", "question_number", name="uq_paper_question_number"),
        UniqueConstraint("id", "course_id", "subject_id", name="uq_question_scope"),
    )


class QuestionUnit(Base):
    __tablename__ = "question_units"
    question_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    course_id: Mapped[str] = mapped_column(String(32))
    subject_id: Mapped[str] = mapped_column(String(32))
    __table_args__ = (
        ForeignKeyConstraint(
            ["question_id", "course_id", "subject_id"],
            ["questions.id", "questions.course_id", "questions.subject_id"],
            ondelete="CASCADE",
            name="fk_question_unit_question_scope",
        ),
        ForeignKeyConstraint(
            ["unit_id", "course_id", "subject_id"],
            ["textbook_units.id", "textbook_units.course_id", "textbook_units.subject_id"],
            ondelete="CASCADE",
            name="fk_question_unit_unit_scope",
        ),
    )


class AssessmentBlueprint(TimestampMixin, Base):
    __tablename__ = "assessment_blueprints"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    grade: Mapped[int] = mapped_column(Integer)
    term: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(24))
    target_marks: Mapped[int] = mapped_column(Integer)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    question_count: Mapped[int] = mapped_column(Integer)
    skills: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    difficulty_profile: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    status: Mapped[str] = mapped_column(String(16), default="draft", server_default="draft", index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("grade IN (10, 11) AND term IN (1, 2, 3)", name="ck_assessment_blueprint_period"),
        CheckConstraint("mode IN ('practice','official_paper','mock')", name="ck_assessment_blueprint_mode"),
        CheckConstraint("target_marks > 0 AND duration_minutes > 0 AND question_count > 0", name="ck_assessment_blueprint_values"),
        CheckConstraint("status IN ('draft','published','retired')", name="ck_assessment_blueprint_status"),
    )


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="RESTRICT"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    mode: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(16), default="active", server_default="active", index=True)
    blueprint_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assessment_blueprints.id", ondelete="RESTRICT"))
    official_paper_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("official_material_versions.id", ondelete="RESTRICT"))
    curriculum_snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_curriculum_snapshots.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(200))
    target_marks: Mapped[int] = mapped_column(Integer)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    skills: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    difficulty_profile: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submission_key: Mapped[str | None] = mapped_column(String(100))
    __table_args__ = (
        CheckConstraint("mode IN ('practice','official_paper','mock')", name="ck_assessment_mode"),
        CheckConstraint("status IN ('active','submitted','expired')", name="ck_assessment_status"),
        CheckConstraint("target_marks > 0 AND duration_minutes > 0", name="ck_assessment_values"),
        UniqueConstraint("student_id", "submission_key", name="uq_assessment_submission_key"),
        Index("uq_active_assessment_per_student", "student_id", unique=True,
              postgresql_where=text("status = 'active'")),
    )


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    source_question_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("official_question_versions.id", ondelete="RESTRICT"))
    source_document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id", ondelete="RESTRICT"))
    question_number: Mapped[str] = mapped_column(String(40))
    prompt: Mapped[str] = mapped_column(Text)
    shared_stem: Mapped[str] = mapped_column(Text, default="", server_default="")
    marks: Mapped[int] = mapped_column(Integer)
    equations: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    asset_ids: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    source_locations: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    rubric: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    unit_ids: Mapped[list] = mapped_column(JSON)
    unit_weights: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    skills: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    difficulty: Mapped[str] = mapped_column(String(24), default="mixed", server_default="mixed")
    __table_args__ = (
        CheckConstraint("sequence > 0 AND marks > 0", name="ck_assessment_question_values"),
        UniqueConstraint("assessment_id", "sequence", name="uq_assessment_question_sequence"),
        UniqueConstraint("assessment_id", "source_question_version_id", name="uq_assessment_question_source"),
    )


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_questions.id", ondelete="CASCADE"), primary_key=True)
    answer_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    file_id: Mapped[str | None] = mapped_column(String(120))
    save_revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    idempotency_key: Mapped[str] = mapped_column(String(100))
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("save_revision > 0", name="ck_assessment_answer_revision"),
        UniqueConstraint("assessment_id", "idempotency_key", name="uq_assessment_answer_idempotency"),
    )


class AssessmentWorkingFile(Base):
    __tablename__ = "assessment_working_files"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_questions.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="RESTRICT"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(80))
    byte_size: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    ocr_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    ocr_metadata: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("byte_size > 0", name="ck_assessment_working_file_size"),
        CheckConstraint("ocr_confidence BETWEEN 0 AND 1", name="ck_assessment_working_ocr_confidence"),
    )


class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_questions.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(24), index=True)
    answer_revision: Mapped[int] = mapped_column(Integer)
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    request_key: Mapped[str] = mapped_column(String(100))
    awarded_marks: Mapped[int] = mapped_column(Integer)
    max_marks: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float)
    marking_decisions: Mapped[list] = mapped_column(JSON)
    strengths: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    small_mistakes: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    conceptual_mistakes: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    improved_answer: Mapped[str] = mapped_column(Text)
    teaching_explanation: Mapped[str] = mapped_column(Text)
    unit_evidence: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    recommendations: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    review_reasons: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    prompt_name: Mapped[str] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(40))
    rubric_snapshot: Mapped[dict] = mapped_column(JSON)
    source_manifest: Mapped[list] = mapped_column(JSON)
    pass_one_output: Mapped[dict] = mapped_column(JSON)
    pass_two_output: Mapped[dict] = mapped_column(JSON)
    subject_engine: Mapped[str] = mapped_column(String(80))
    subject_engine_version: Mapped[str] = mapped_column(String(40))
    deterministic_checks: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("version_number > 0 AND answer_revision >= 0", name="ck_assessment_result_versions"),
        CheckConstraint("status IN ('published','needs_review')", name="ck_assessment_result_status"),
        CheckConstraint("awarded_marks BETWEEN 0 AND max_marks AND max_marks > 0", name="ck_assessment_result_marks"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_assessment_result_confidence"),
        UniqueConstraint("question_id", "version_number", name="uq_assessment_result_question_version"),
        UniqueConstraint("assessment_id", "question_id", "request_key", name="uq_assessment_result_request"),
    )


class AssessmentInteraction(Base):
    __tablename__ = "assessment_interactions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_questions.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(24))
    request_key: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("kind IN ('hint')", name="ck_assessment_interaction_kind"),
        UniqueConstraint("assessment_id", "question_id", "request_key", name="uq_assessment_interaction_request"),
    )


class UnitMastery(Base):
    __tablename__ = "unit_mastery"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="RESTRICT"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    score: Mapped[float] = mapped_column(Numeric(8, 5))
    display_score: Mapped[float] = mapped_column(Numeric(3, 1))
    confidence: Mapped[str] = mapped_column(String(12))
    provisional: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    evidence_count: Mapped[int] = mapped_column(Integer)
    evidence_weight: Mapped[float] = mapped_column(Numeric(10, 5))
    variety_count: Mapped[int] = mapped_column(Integer)
    trend: Mapped[float] = mapped_column(Numeric(8, 5), default=0, server_default="0")
    last_evidence_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version_number: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 10 AND display_score BETWEEN 0 AND 10", name="ck_unit_mastery_score"),
        CheckConstraint("confidence IN ('low','medium','high')", name="ck_unit_mastery_confidence"),
        CheckConstraint("evidence_count >= 0 AND evidence_weight >= 0 AND variety_count >= 0 AND version_number > 0", name="ck_unit_mastery_counts"),
        UniqueConstraint("student_id", "unit_id", name="uq_unit_mastery_student_unit"),
    )


class UnitMasteryDimension(Base):
    __tablename__ = "unit_mastery_dimensions"
    mastery_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("unit_mastery.id", ondelete="CASCADE"), primary_key=True)
    dimension: Mapped[str] = mapped_column(String(24), primary_key=True)
    score: Mapped[float] = mapped_column(Numeric(8, 5))
    evidence_weight: Mapped[float] = mapped_column(Numeric(10, 5))
    __table_args__ = (
        CheckConstraint("dimension IN ('knowledge','application','method','accuracy','reasoning','communication','retention')", name="ck_unit_mastery_dimension_name"),
        CheckConstraint("score BETWEEN 0 AND 10 AND evidence_weight >= 0", name="ck_unit_mastery_dimension_values"),
    )


class UnitMasteryEvent(Base):
    __tablename__ = "unit_mastery_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    mastery_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("unit_mastery.id", ondelete="RESTRICT"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="RESTRICT"), index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="RESTRICT"), index=True)
    trigger_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_results.id", ondelete="RESTRICT"), index=True)
    previous_score: Mapped[float | None] = mapped_column(Numeric(8, 5))
    new_score: Mapped[float] = mapped_column(Numeric(8, 5))
    previous_confidence: Mapped[str | None] = mapped_column(String(12))
    new_confidence: Mapped[str] = mapped_column(String(12))
    contribution: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    __table_args__ = (
        CheckConstraint("previous_score IS NULL OR previous_score BETWEEN 0 AND 10", name="ck_unit_mastery_event_previous"),
        CheckConstraint("new_score BETWEEN 0 AND 10", name="ck_unit_mastery_event_new"),
        UniqueConstraint("unit_id", "trigger_result_id", name="uq_unit_mastery_event_trigger"),
    )


class WeaknessDiagnosis(Base):
    __tablename__ = "weakness_diagnoses"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="RESTRICT"), index=True)
    result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_results.id", ondelete="RESTRICT"), index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_questions.id", ondelete="RESTRICT"))
    category: Mapped[str] = mapped_column(String(40), index=True)
    dimension: Mapped[str] = mapped_column(String(24))
    severity: Mapped[str] = mapped_column(String(12))
    description: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON)
    occurrence_number: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    __table_args__ = (
        CheckConstraint("severity IN ('minor','moderate','major')", name="ck_weakness_diagnosis_severity"),
        CheckConstraint("confidence BETWEEN 0 AND 1 AND occurrence_number > 0", name="ck_weakness_diagnosis_values"),
        UniqueConstraint("result_id", "unit_id", "category", name="uq_weakness_diagnosis_result_unit_category"),
    )


class ImprovementRecommendation(Base):
    __tablename__ = "improvement_recommendations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    diagnosis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("weakness_diagnoses.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="RESTRICT"), index=True)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("retrieval_chunks.id", ondelete="RESTRICT"))
    activity_question_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("official_question_versions.id", ondelete="RESTRICT"))
    activity_type: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(180))
    reason: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    success_condition: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(20), index=True)
    review_reason: Mapped[str] = mapped_column(Text, default="", server_default="")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    __table_args__ = (
        CheckConstraint("activity_type IN ('review','targeted_practice','spaced_retry','unit_check')", name="ck_improvement_recommendation_activity"),
        CheckConstraint("review_status IN ('approved','pending_review','rejected')", name="ck_improvement_recommendation_review"),
        UniqueConstraint("diagnosis_id", "activity_type", name="uq_improvement_recommendation_activity"),
    )


class StudyPlan(Base):
    __tablename__ = "study_plans"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), index=True)
    evidence_fingerprint: Mapped[str] = mapped_column(String(64))
    generation_reason: Mapped[str] = mapped_column(String(20))
    requested_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("version_number > 0", name="ck_study_plan_version"),
        CheckConstraint("status IN ('active','superseded')", name="ck_study_plan_status"),
        CheckConstraint("generation_reason IN ('evidence','request')", name="ck_study_plan_reason"),
        UniqueConstraint("student_id", "version_number", name="uq_study_plan_student_version"),
        Index("uq_study_plan_active_student", "student_id", unique=True, postgresql_where=text("status = 'active'")),
    )


class StudyPlanItem(Base):
    __tablename__ = "study_plan_items"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_plans.id", ondelete="RESTRICT"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), index=True)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("improvement_recommendations.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="RESTRICT"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(180))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("retrieval_chunks.id", ondelete="RESTRICT"))
    success_condition: Mapped[str] = mapped_column(Text)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("sequence > 0 AND duration_minutes BETWEEN 5 AND 120", name="ck_study_plan_item_values"),
        CheckConstraint("status IN ('planned','completed')", name="ck_study_plan_item_status"),
        UniqueConstraint("plan_id", "sequence", name="uq_study_plan_item_sequence"),
        UniqueConstraint("plan_id", "recommendation_id", name="uq_study_plan_item_recommendation"),
    )


class EducationalMedia(Base):
    __tablename__ = "educational_media"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("textbook_units.id", ondelete="RESTRICT"), index=True)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("retrieval_chunks.id", ondelete="RESTRICT"), index=True)
    kind: Mapped[str] = mapped_column(String(28), index=True)
    title: Mapped[str] = mapped_column(String(180))
    alt_text: Mapped[str] = mapped_column(String(1000))
    prompt: Mapped[str] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(String(40))
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    source_manifest: Mapped[list] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    response_id: Mapped[str | None] = mapped_column(String(180))
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    content_type: Mapped[str] = mapped_column(String(80))
    checksum: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    review_notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("kind IN ('circuit_svg','forces_svg','geometry_svg','plot_svg','conceptual_image')", name="ck_educational_media_kind"),
        CheckConstraint("status IN ('pending_review','published','rejected')", name="ck_educational_media_status"),
    )


class EvaluationCorpus(Base):
    __tablename__ = "evaluation_corpora"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(180))
    cases: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft", index=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("version_number > 0", name="ck_evaluation_corpus_version"),
        CheckConstraint("status IN ('draft','approved','retired')", name="ck_evaluation_corpus_status"),
        UniqueConstraint("subject_id", "version_number", name="uq_evaluation_corpus_subject_version"),
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    corpus_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_corpora.id", ondelete="RESTRICT"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    candidate_model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(80))
    observations_hash: Mapped[str] = mapped_column(String(64))
    metrics: Mapped[dict] = mapped_column(JSON)
    thresholds: Mapped[dict] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean, index=True)
    failure_reasons: Mapped[list] = mapped_column(JSON)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class EvaluationRelease(Base):
    __tablename__ = "evaluation_releases"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    workflow: Mapped[str] = mapped_column(String(32))
    mode: Mapped[str] = mapped_column(String(20), default="review_required", server_default="review_required")
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="RESTRICT"))
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.85, server_default="0.85")
    activated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("workflow IN ('assessment_feedback','content_publication')", name="ck_evaluation_release_workflow"),
        CheckConstraint("mode IN ('review_required','automatic')", name="ck_evaluation_release_mode"),
        CheckConstraint("confidence_threshold BETWEEN 0 AND 1", name="ck_evaluation_release_confidence"),
        UniqueConstraint("subject_id", "workflow", name="uq_evaluation_release_subject_workflow"),
    )


class FamilyUsageEvent(Base):
    __tablename__ = "family_usage_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("student_profiles.student_id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    operation_id: Mapped[str] = mapped_column(String(80), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    __table_args__ = (
        CheckConstraint("kind IN ('ai_request','ai_token')", name="ck_family_usage_kind"),
        CheckConstraint("quantity >= 0", name="ck_family_usage_quantity"),
        UniqueConstraint("family_id", "kind", "operation_id", name="uq_family_usage_operation"),
    )
