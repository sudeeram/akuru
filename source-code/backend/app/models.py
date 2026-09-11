import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer,
    String, Text, UniqueConstraint, func, text,
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
    __table_args__ = (
        CheckConstraint("kind IN ('textbook','reference','past_paper','mark_scheme','examiner_report')", name="ck_documents_kind"),
        CheckConstraint("review_state IN ('pending','reviewed','published','rejected')", name="ck_documents_review_state"),
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
