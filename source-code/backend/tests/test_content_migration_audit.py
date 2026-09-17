from unittest.mock import MagicMock, patch

from app.content_migration_audit import CONTENT_TABLES, LEGACY_CONTENT_TABLES, content_counts, report, total_records


TOPIC_CONTENT_TABLES = {
    "textbooks",
    "textbook_groups",
    "textbook_topics",
    "textbook_topic_documents",
    "textbook_structure_versions",
    "textbook_topic_content_versions",
    "textbook_topic_content_sources",
    "curriculum_plan_topics",
    "official_question_topic_mappings",
    "topic_mastery",
    "topic_mastery_dimensions",
    "topic_mastery_events",
    "tutor_session_topic_events",
}


def test_content_audit_covers_every_expected_category_and_is_read_only() -> None:
    db = MagicMock()
    db.get_bind.return_value = MagicMock()
    db.scalar.return_value = 0

    all_tables = {table for tables in {**CONTENT_TABLES, **LEGACY_CONTENT_TABLES}.values() for table in tables}
    with patch("app.content_migration_audit.inspect") as inspect_mock:
        inspect_mock.return_value.get_table_names.return_value = sorted(all_tables)
        counts = content_counts(db)

    assert set(counts) == set(CONTENT_TABLES) | set(LEGACY_CONTENT_TABLES)
    assert all(value == 0 for tables in counts.values() for value in tables.values())
    assert db.scalar.call_count == sum(len(tables) for tables in {**CONTENT_TABLES, **LEGACY_CONTENT_TABLES}.values())
    assert report(counts)["safeForCleanTextbookTopicMigration"] is True
    assert report(counts)["safeForBaselineReset"] is True


def test_content_audit_fails_closed_when_one_record_exists() -> None:
    counts = {category: {table: 0 for table in tables} for category, tables in {**CONTENT_TABLES, **LEGACY_CONTENT_TABLES}.items()}
    counts["documents"]["documents"] = 1

    result = report(counts)

    assert total_records(counts) == 1
    assert result["status"] == "content_present"
    assert result["safeForCleanTextbookTopicMigration"] is False
    assert result["safeForBaselineReset"] is False


def test_content_audit_includes_every_topic_hierarchy_content_table() -> None:
    audited_tables = {table for tables in CONTENT_TABLES.values() for table in tables}

    assert TOPIC_CONTENT_TABLES <= audited_tables
