"""add textbook group and topic hierarchy

Revision ID: c31d9e5a7b42
Revises: b72fa92d4e11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c31d9e5a7b42"
down_revision: Union[str, None] = "b72fa92d4e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONTENT_TABLES = (
    "documents", "document_versions", "document_assets", "document_pages", "document_blocks",
    "document_events", "document_jobs", "document_stage_runs", "educational_media",
    "textbook_content_versions", "textbook_unit_versions", "textbook_units", "retrieval_chunks",
    "curriculum_plans", "curriculum_plan_units", "term_coverage", "assessment_blueprints",
    "official_material_versions", "official_question_versions", "mark_scheme_entry_versions",
    "examiner_comment_versions", "official_question_unit_mappings", "questions", "question_units",
    "assessments", "assessment_questions", "assessment_answers", "assessment_interactions",
    "assessment_results", "assessment_working_files", "assessment_curriculum_snapshots",
    "unit_mastery", "unit_mastery_dimensions", "unit_mastery_events", "weakness_diagnoses",
    "improvement_recommendations", "study_plans", "study_plan_items", "tutor_sessions", "tutor_turns",
    "tutor_turn_sources", "tutor_session_profile_events", "tutor_session_unit_events",
    "tutor_learner_context_logs", "tutor_practices", "tutor_signals", "tutor_session_summaries",
    "tutor_safety_events", "tutor_realtime_connections", "evaluation_corpora", "evaluation_runs",
    "evaluation_releases",
)


def _require_empty_content() -> None:
    connection = op.get_bind()
    populated = [
        table for table in CONTENT_TABLES
        if connection.execute(sa.text(f'SELECT EXISTS (SELECT 1 FROM "{table}" LIMIT 1)')).scalar()
    ]
    if populated:
        raise RuntimeError(
            "The clean textbook-topic migration requires empty educational-content tables; found data in: "
            + ", ".join(populated)
        )


def upgrade():
    _require_empty_content()

    op.create_table(
        "textbooks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("course_id", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("edition", sa.String(80), nullable=False),
        sa.Column("publisher", sa.String(160), server_default="", nullable=False),
        sa.Column("group_label", sa.String(12), nullable=False),
        sa.Column("status", sa.String(16), server_default="draft", nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("published_by", sa.Uuid(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("group_label IN ('unit','module')", name="ck_textbook_group_label"),
        sa.CheckConstraint("status IN ('draft','published','archived')", name="ck_textbook_status"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_ref"),
        sa.UniqueConstraint("course_id", "subject_id", "title", "edition", name="uq_textbook_edition"),
        sa.UniqueConstraint("id", "course_id", "subject_id", name="uq_textbook_scope"),
    )
    for column in ("course_id", "subject_id", "status"):
        op.create_index(f"ix_textbooks_{column}", "textbooks", [column])

    op.create_table(
        "textbook_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("textbook_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("sequence > 0", name="ck_textbook_group_sequence"),
        sa.CheckConstraint("status IN ('draft','published','archived')", name="ck_textbook_group_status"),
        sa.ForeignKeyConstraint(["textbook_id"], ["textbooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_ref"),
        sa.UniqueConstraint("textbook_id", "code", name="uq_textbook_group_code"),
        sa.UniqueConstraint("textbook_id", "sequence", name="uq_textbook_group_sequence"),
        sa.UniqueConstraint("id", "textbook_id", name="uq_textbook_group_scope"),
    )
    op.create_index("ix_textbook_groups_textbook_id", "textbook_groups", ["textbook_id"])

    op.create_table(
        "textbook_topics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_ref", sa.String(56), nullable=False),
        sa.Column("textbook_id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("syllabus_ref", sa.String(120), server_default="", nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(16), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("sequence > 0", name="ck_textbook_topic_sequence"),
        sa.CheckConstraint("status IN ('draft','published','archived')", name="ck_textbook_topic_status"),
        sa.ForeignKeyConstraint(["group_id", "textbook_id"], ["textbook_groups.id", "textbook_groups.textbook_id"],
                                ondelete="CASCADE", name="fk_textbook_topic_group_scope"),
        sa.ForeignKeyConstraint(["textbook_id", "course_id", "subject_id"],
                                ["textbooks.id", "textbooks.course_id", "textbooks.subject_id"],
                                ondelete="CASCADE", name="fk_textbook_topic_book_scope"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_ref"),
        sa.UniqueConstraint("textbook_id", "code", name="uq_textbook_topic_code"),
        sa.UniqueConstraint("group_id", "sequence", name="uq_textbook_topic_sequence"),
        sa.UniqueConstraint("id", "course_id", "subject_id", name="uq_textbook_topic_scope"),
    )
    for column in ("textbook_id", "group_id", "course_id", "subject_id", "status"):
        op.create_index(f"ix_textbook_topics_{column}", "textbook_topics", [column])

    op.create_table(
        "textbook_topic_documents",
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(24), server_default="primary", nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("printed_start_page", sa.String(24), nullable=True),
        sa.Column("printed_end_page", sa.String(24), nullable=True),
        sa.Column("review_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('primary','supporting','reference')", name="ck_topic_document_role"),
        sa.CheckConstraint("sequence > 0", name="ck_topic_document_sequence"),
        sa.CheckConstraint("review_status IN ('pending','processing','needs_review','ready','published','failed','superseded')",
                           name="ck_topic_document_review_status"),
        sa.ForeignKeyConstraint(["topic_id"], ["textbook_topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("topic_id", "document_version_id"),
        sa.UniqueConstraint("topic_id", "sequence", name="uq_topic_document_sequence"),
    )
    op.create_index("ix_textbook_topic_documents_document_id", "textbook_topic_documents", ["document_id"])
    op.create_index("ix_textbook_topic_documents_review_status", "textbook_topic_documents", ["review_status"])

    op.create_table(
        "curriculum_plan_topics",
        sa.Column("plan_id", sa.Uuid(), nullable=False), sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("term", sa.Integer(), nullable=False), sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("grade IN (10, 11)", name="ck_curriculum_plan_topic_grade"),
        sa.CheckConstraint("term IN (1, 2, 3)", name="ck_curriculum_plan_topic_term"),
        sa.ForeignKeyConstraint(["plan_id"], ["curriculum_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["textbook_topics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("plan_id", "grade", "term", "topic_id"),
        sa.UniqueConstraint("plan_id", "topic_id", name="uq_curriculum_plan_topic_introduction"),
    )

    op.create_table(
        "official_question_topic_mappings",
        sa.Column("question_version_id", sa.Uuid(), nullable=False), sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False), sa.Column("required", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("suggestion_method", sa.String(40), nullable=True), sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), server_default="", nullable=False), sa.Column("confirmed_by", sa.Uuid(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("weight BETWEEN 1 AND 100", name="ck_official_question_topic_weight"),
        sa.CheckConstraint("status IN ('draft','confirmed')", name="ck_official_question_topic_status"),
        sa.CheckConstraint("confidence IS NULL OR confidence BETWEEN 0 AND 1", name="ck_official_question_topic_confidence"),
        sa.ForeignKeyConstraint(["question_version_id"], ["official_question_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["textbook_topics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("question_version_id", "topic_id"),
    )

    op.create_table(
        "topic_mastery",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False), sa.Column("subject_id", sa.String(32), nullable=False),
        sa.Column("score", sa.Numeric(8, 5), nullable=False), sa.Column("display_score", sa.Numeric(3, 1), nullable=False),
        sa.Column("confidence", sa.String(12), nullable=False), sa.Column("provisional", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False), sa.Column("evidence_weight", sa.Numeric(10, 5), nullable=False),
        sa.Column("variety_count", sa.Integer(), nullable=False), sa.Column("trend", sa.Numeric(8, 5), server_default="0", nullable=False),
        sa.Column("last_evidence_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("score BETWEEN 0 AND 10 AND display_score BETWEEN 0 AND 10", name="ck_topic_mastery_score"),
        sa.CheckConstraint("confidence IN ('low','medium','high')", name="ck_topic_mastery_confidence"),
        sa.CheckConstraint("evidence_count >= 0 AND evidence_weight >= 0 AND variety_count >= 0 AND version_number > 0",
                           name="ck_topic_mastery_counts"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["textbook_topics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("student_id", "topic_id", name="uq_topic_mastery_student_topic"),
    )
    for column in ("student_id", "topic_id", "subject_id"):
        op.create_index(f"ix_topic_mastery_{column}", "topic_mastery", [column])

    op.create_table(
        "topic_mastery_dimensions",
        sa.Column("mastery_id", sa.Uuid(), nullable=False), sa.Column("dimension", sa.String(24), nullable=False),
        sa.Column("score", sa.Numeric(8, 5), nullable=False), sa.Column("evidence_weight", sa.Numeric(10, 5), nullable=False),
        sa.CheckConstraint("dimension IN ('knowledge','application','method','accuracy','reasoning','communication','retention')",
                           name="ck_topic_mastery_dimension_name"),
        sa.CheckConstraint("score BETWEEN 0 AND 10 AND evidence_weight >= 0", name="ck_topic_mastery_dimension_values"),
        sa.ForeignKeyConstraint(["mastery_id"], ["topic_mastery.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("mastery_id", "dimension"),
    )

    op.create_table(
        "topic_mastery_events",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("mastery_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False), sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("trigger_result_id", sa.Uuid(), nullable=False), sa.Column("previous_score", sa.Numeric(8, 5), nullable=True),
        sa.Column("new_score", sa.Numeric(8, 5), nullable=False), sa.Column("previous_confidence", sa.String(12), nullable=True),
        sa.Column("new_confidence", sa.String(12), nullable=False), sa.Column("contribution", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("previous_score IS NULL OR previous_score BETWEEN 0 AND 10", name="ck_topic_mastery_event_previous"),
        sa.CheckConstraint("new_score BETWEEN 0 AND 10", name="ck_topic_mastery_event_new"),
        sa.ForeignKeyConstraint(["mastery_id"], ["topic_mastery.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["topic_id"], ["textbook_topics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["trigger_result_id"], ["assessment_results.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("topic_id", "trigger_result_id", name="uq_topic_mastery_event_trigger"),
    )
    for column in ("mastery_id", "student_id", "topic_id", "trigger_result_id", "created_at"):
        op.create_index(f"ix_topic_mastery_events_{column}", "topic_mastery_events", [column])

    op.add_column("curriculum_plans", sa.Column("textbook_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_curriculum_plans_textbook", "curriculum_plans", "textbooks", ["textbook_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_curriculum_plans_textbook_id", "curriculum_plans", ["textbook_id"])
    op.add_column("official_material_versions", sa.Column("textbook_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_official_material_versions_textbook", "official_material_versions", "textbooks", ["textbook_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_official_material_versions_textbook_id", "official_material_versions", ["textbook_id"])
    op.add_column("assessment_curriculum_snapshots", sa.Column("covered_topic_ids", sa.JSON(), server_default="[]", nullable=False))
    for name, target in (("group_id", "textbook_groups"), ("topic_id", "textbook_topics")):
        op.add_column("retrieval_chunks", sa.Column(name, sa.Uuid(), nullable=True))
        op.create_foreign_key(f"fk_retrieval_chunks_{name}", "retrieval_chunks", target, [name], ["id"], ondelete="CASCADE")
        op.create_index(f"ix_retrieval_chunks_{name}", "retrieval_chunks", [name])
    for table in ("weakness_diagnoses", "improvement_recommendations", "study_plan_items"):
        op.add_column(table, sa.Column("topic_id", sa.Uuid(), nullable=True))
        op.create_foreign_key(f"fk_{table}_topic", table, "textbook_topics", ["topic_id"], ["id"], ondelete="RESTRICT")
        op.create_index(f"ix_{table}_topic_id", table, ["topic_id"])


def downgrade():
    for table in ("study_plan_items", "improvement_recommendations", "weakness_diagnoses"):
        op.drop_index(f"ix_{table}_topic_id", table_name=table)
        op.drop_constraint(f"fk_{table}_topic", table, type_="foreignkey")
        op.drop_column(table, "topic_id")
    for name in ("topic_id", "group_id"):
        op.drop_index(f"ix_retrieval_chunks_{name}", table_name="retrieval_chunks")
        op.drop_constraint(f"fk_retrieval_chunks_{name}", "retrieval_chunks", type_="foreignkey")
        op.drop_column("retrieval_chunks", name)
    op.drop_column("assessment_curriculum_snapshots", "covered_topic_ids")
    op.drop_index("ix_official_material_versions_textbook_id", table_name="official_material_versions")
    op.drop_constraint("fk_official_material_versions_textbook", "official_material_versions", type_="foreignkey")
    op.drop_column("official_material_versions", "textbook_id")
    op.drop_index("ix_curriculum_plans_textbook_id", table_name="curriculum_plans")
    op.drop_constraint("fk_curriculum_plans_textbook", "curriculum_plans", type_="foreignkey")
    op.drop_column("curriculum_plans", "textbook_id")
    for table in (
        "topic_mastery_events", "topic_mastery_dimensions", "topic_mastery",
        "official_question_topic_mappings", "curriculum_plan_topics", "textbook_topic_documents",
        "textbook_topics", "textbook_groups", "textbooks",
    ):
        op.drop_table(table)
