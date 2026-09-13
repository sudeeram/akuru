import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer,
    JSON, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column

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


class TextbookUnit(TimestampMixin, Base):
    __tablename__ = "textbook_units"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    textbook_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    unit_code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(240))
    sequence: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint("textbook_id", "unit_code", name="uq_textbook_unit_code"),
        UniqueConstraint("id", "course_id", "subject_id", name="uq_unit_scope"),
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
