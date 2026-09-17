from pathlib import Path

from app.models import Base


MIGRATIONS = Path(__file__).parents[1] / "migrations"
BASELINE = MIGRATIONS / "versions" / "0001_initial_akuru_schema.py"


def test_only_one_active_baseline_revision_exists():
    revisions = sorted((MIGRATIONS / "versions").glob("*.py"))
    assert revisions == [BASELINE]
    text = BASELINE.read_text()
    assert "revision: str = '0001_initial_akuru_schema'" in text
    assert "down_revision: Union[str, None] = None" in text


def test_baseline_matches_topic_only_metadata_inventory():
    text = BASELINE.read_text()
    assert text.count("op.create_table(") == len(Base.metadata.tables) == 72
    assert 'CREATE EXTENSION IF NOT EXISTS vector' in text
    assert "pgvector.sqlalchemy" in text
    assert "group_label IN ('unit','module')" in text
    for table_name in Base.metadata.tables:
        assert f"op.create_table('{table_name}'" in text


def test_baseline_has_no_destructive_downgrade_or_deprecated_tables():
    text = BASELINE.read_text()
    downgrade = text[text.index("def downgrade() -> None:"):]
    assert "RuntimeError" in downgrade
    assert "op.drop_table" not in downgrade
    for table_name in (
        "textbook_units", "textbook_content_versions", "textbook_unit_versions",
        "curriculum_plan_units", "official_question_unit_mappings", "term_coverage",
        "questions", "question_units", "unit_mastery", "unit_mastery_dimensions",
        "unit_mastery_events", "tutor_session_unit_events",
    ):
        assert f"op.create_table('{table_name}'" not in text
