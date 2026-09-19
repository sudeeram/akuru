from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.database import Base
from app import models  # noqa: F401


def _constraint_names(table_name: str, kind: type) -> set[str]:
    return {
        constraint.name for constraint in Base.metadata.tables[table_name].constraints
        if isinstance(constraint, kind) and constraint.name
    }


def test_textbook_group_topic_hierarchy_is_registered() -> None:
    expected = {
        "textbooks", "textbook_groups", "textbook_topics", "textbook_topic_documents",
        "curriculum_plan_topics", "official_question_topic_mappings", "topic_mastery",
        "topic_mastery_dimensions", "topic_mastery_events",
        "textbook_topic_content_versions", "textbook_topic_content_sources",
    }
    assert expected <= set(Base.metadata.tables)
    assert "ck_textbook_group_label" in _constraint_names("textbooks", CheckConstraint)
    assert "uq_textbook_topic_code" in _constraint_names("textbook_topics", UniqueConstraint)
    assert "uq_curriculum_plan_topic_introduction" in _constraint_names("curriculum_plan_topics", UniqueConstraint)


def test_topic_provenance_reaches_downstream_learning_tables() -> None:
    expected_columns = {
        "retrieval_chunks": {"group_id", "topic_id", "topic_content_version_id"},
        "assessment_curriculum_snapshots": {"covered_topic_ids"},
        "weakness_diagnoses": {"topic_id"},
        "improvement_recommendations": {"topic_id"},
        "study_plan_items": {"topic_id"},
    }
    for table_name, names in expected_columns.items():
        assert names <= {column.name for column in Base.metadata.tables[table_name].columns}


def test_identity_and_operational_tables_remain_present() -> None:
    preserved = {
        "users", "auth_sessions", "student_profiles", "student_progressions", "student_subjects",
        "ai_provider_accounts", "student_ai_quotas", "audit_events",
    }
    assert preserved <= set(Base.metadata.tables)


def test_topic_sources_support_non_retrievable_visual_references() -> None:
    constraints = [
        constraint for constraint in Base.metadata.tables["textbook_topic_documents"].constraints
        if isinstance(constraint, CheckConstraint) and constraint.name == "ck_topic_document_role"
    ]
    assert len(constraints) == 1
    assert "visual_reference" in str(constraints[0].sqltext)


def test_topic_identity_is_stable_and_scoped_to_its_textbook_subject() -> None:
    topic = Base.metadata.tables["textbook_topics"]
    assert topic.c.public_ref.unique
    assert "fk_textbook_topic_group_scope" in _constraint_names("textbook_topics", ForeignKeyConstraint)
    assert "fk_textbook_topic_book_scope" in _constraint_names("textbook_topics", ForeignKeyConstraint)
