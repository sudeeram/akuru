from pathlib import Path

from app.main import app
from app.models import Base


DEPRECATED_TABLES = {
    "textbook_units",
    "textbook_content_versions",
    "textbook_unit_versions",
    "curriculum_plan_units",
    "official_question_unit_mappings",
    "term_coverage",
    "questions",
    "question_units",
    "unit_mastery",
    "unit_mastery_dimensions",
    "unit_mastery_events",
    "tutor_session_unit_events",
}

DEPRECATED_RUNTIME_TOKENS = {
    "TextbookUnit",
    "TextbookContentVersion",
    "TextbookUnitVersion",
    "CurriculumPlanUnit",
    "OfficialQuestionUnitMapping",
    "TermCoverage",
    "QuestionUnit",
    "UnitMastery",
    "TutorSessionUnitEvent",
    "active_unit_id",
    "covered_unit_ids",
    "unit_evidence",
    "unit_id",
    "unitIds",
    "switch-unit",
    "next-unit",
    "textbook-review",
}


def test_sqlalchemy_metadata_has_no_deprecated_unit_only_tables():
    assert DEPRECATED_TABLES.isdisjoint(Base.metadata.tables)


def test_runtime_python_has_no_deprecated_compatibility_tokens():
    app_root = Path(__file__).parents[1] / "app"
    offenders: dict[str, list[str]] = {}
    for path in app_root.rglob("*.py"):
        text = path.read_text()
        matches = sorted(token for token in DEPRECATED_RUNTIME_TOKENS if token in text)
        if matches:
            offenders[str(path.relative_to(app_root))] = matches
    assert offenders == {}


def test_openapi_exposes_topic_only_routes_and_contracts():
    schema = app.openapi()
    paths = set(schema["paths"])
    assert not any(fragment in path for path in paths for fragment in (
        "switch-unit", "next-unit", "textbook-review", "unit-mapping",
    ))
    assert "/api/v1/tutoring/sessions/{session_ref}/switch-topic" in paths
    assert "/api/v1/tutoring/sessions/{session_ref}/next-topic" in paths
    serialized = str(schema)
    assert "UnitMasteryResponse" not in serialized
    assert "unitIds" not in serialized
