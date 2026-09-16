from unittest.mock import MagicMock

from app.content_migration_audit import CONTENT_TABLES, content_counts, report, total_records


def test_content_audit_covers_every_expected_category_and_is_read_only() -> None:
    db = MagicMock()
    db.scalar.return_value = 0

    counts = content_counts(db)

    assert set(counts) == set(CONTENT_TABLES)
    assert all(value == 0 for tables in counts.values() for value in tables.values())
    assert db.scalar.call_count == sum(len(tables) for tables in CONTENT_TABLES.values())
    assert report(counts)["safeForCleanTextbookTopicMigration"] is True


def test_content_audit_fails_closed_when_one_record_exists() -> None:
    counts = {category: {table: 0 for table in tables} for category, tables in CONTENT_TABLES.items()}
    counts["documents"]["documents"] = 1

    result = report(counts)

    assert total_records(counts) == 1
    assert result["status"] == "content_present"
    assert result["safeForCleanTextbookTopicMigration"] is False
