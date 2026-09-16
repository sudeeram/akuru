"""Read-only audit for the empty-content textbook/topic schema migration."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models  # noqa: F401 - registers every mapped table
from app.database import Base, SessionLocal


CONTENT_TABLES: dict[str, tuple[str, ...]] = {
    "documents": (
        "documents", "document_versions", "document_assets", "document_pages", "document_blocks",
        "document_events", "document_jobs", "document_stage_runs", "educational_media",
    ),
    "textbooks_and_retrieval": (
        "textbook_content_versions", "textbook_unit_versions", "textbook_units", "retrieval_chunks",
    ),
    "curriculum": (
        "curriculum_plans", "curriculum_plan_units", "term_coverage", "assessment_blueprints",
    ),
    "official_materials_and_mappings": (
        "official_material_versions", "official_question_versions", "mark_scheme_entry_versions",
        "examiner_comment_versions", "official_question_unit_mappings", "questions", "question_units",
    ),
    "assessments": (
        "assessments", "assessment_questions", "assessment_answers", "assessment_interactions",
        "assessment_results", "assessment_working_files", "assessment_curriculum_snapshots",
    ),
    "mastery_and_planning": (
        "unit_mastery", "unit_mastery_dimensions", "unit_mastery_events", "weakness_diagnoses",
        "improvement_recommendations", "study_plans", "study_plan_items",
    ),
    "tutor_learning_records": (
        "tutor_sessions", "tutor_turns", "tutor_turn_sources", "tutor_session_profile_events",
        "tutor_session_unit_events", "tutor_learner_context_logs", "tutor_practices", "tutor_signals",
        "tutor_session_summaries", "tutor_safety_events", "tutor_realtime_connections",
    ),
    "evaluation_content": ("evaluation_corpora", "evaluation_runs", "evaluation_releases"),
}


def content_counts(db: Session) -> dict[str, dict[str, int]]:
    """Count migration-sensitive records without modifying the database."""
    result: dict[str, dict[str, int]] = {}
    for category, table_names in CONTENT_TABLES.items():
        category_counts: dict[str, int] = {}
        for table_name in table_names:
            table = Base.metadata.tables[table_name]
            category_counts[table_name] = int(db.scalar(select(func.count()).select_from(table)) or 0)
        result[category] = category_counts
    return result


def total_records(counts: Mapping[str, Mapping[str, int]]) -> int:
    return sum(count for tables in counts.values() for count in tables.values())


def report(counts: Mapping[str, Mapping[str, int]]) -> dict:
    total = total_records(counts)
    return {
        "status": "empty" if total == 0 else "content_present",
        "safeForCleanTextbookTopicMigration": total == 0,
        "totalRecords": total,
        "categories": counts,
        "preservedTables": [
            "users and authentication", "family and enrolment", "course and subject catalogue",
            "AI provider configuration and quotas", "audit events and operations",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count content that must be empty before the clean textbook/topic schema migration."
    )
    parser.add_argument(
        "--require-empty", action="store_true",
        help="Exit with status 2 when any migration-sensitive content record exists.",
    )
    args = parser.parse_args()
    with SessionLocal() as db:
        result = report(content_counts(db))
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.require_empty and not result["safeForCleanTextbookTopicMigration"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
