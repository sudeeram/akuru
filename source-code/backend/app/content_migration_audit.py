"""Read-only audit for the empty-content textbook/topic schema migration."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database import SessionLocal


CONTENT_TABLES: dict[str, tuple[str, ...]] = {
    "documents": (
        "documents", "document_versions", "document_assets", "document_pages", "document_blocks",
        "document_events", "document_jobs", "document_stage_runs", "educational_media",
    ),
    "textbooks_and_retrieval": (
        "textbooks", "textbook_groups", "textbook_topics", "textbook_topic_documents",
        "textbook_topic_content_versions", "textbook_topic_content_sources",
        "textbook_structure_versions", "retrieval_chunks",
    ),
    "curriculum": (
        "curriculum_plans", "curriculum_plan_topics", "assessment_blueprints",
    ),
    "official_materials_and_mappings": (
        "official_material_versions", "official_question_versions", "mark_scheme_entry_versions",
        "examiner_comment_versions", "official_question_topic_mappings",
    ),
    "assessments": (
        "assessments", "assessment_questions", "assessment_answers", "assessment_interactions",
        "assessment_results", "assessment_working_files", "assessment_curriculum_snapshots",
    ),
    "mastery_and_planning": (
        "topic_mastery", "topic_mastery_dimensions", "topic_mastery_events", "weakness_diagnoses",
        "improvement_recommendations", "study_plans", "study_plan_items",
    ),
    "tutor_learning_records": (
        "tutor_sessions", "tutor_turns", "tutor_turn_sources", "tutor_session_profile_events",
        "tutor_session_topic_events", "tutor_learner_context_logs",
        "tutor_practices", "tutor_signals",
        "tutor_session_summaries", "tutor_safety_events", "tutor_realtime_connections",
    ),
    "evaluation_content": ("evaluation_corpora", "evaluation_runs", "evaluation_releases"),
}

# Tables used by the pre-baseline schema. Production is audited before that
# schema is removed, so the reset gate must understand both layouts.
LEGACY_CONTENT_TABLES: dict[str, tuple[str, ...]] = {
    "legacy_textbooks_and_retrieval": (
        "textbook_units", "unit_chapters", "textbook_unit_documents",
        "question_unit_mappings",
    ),
    "legacy_curriculum": ("curriculum_plan_units",),
    "legacy_mastery": ("unit_mastery", "unit_mastery_dimensions", "unit_mastery_events"),
    "legacy_tutor_learning": ("tutor_session_unit_events",),
}


def content_counts(db: Session) -> dict[str, dict[str, int]]:
    """Count migration-sensitive records without modifying the database."""
    present = set(inspect(db.get_bind()).get_table_names(schema="public"))
    result: dict[str, dict[str, int]] = {}
    for category, table_names in {**CONTENT_TABLES, **LEGACY_CONTENT_TABLES}.items():
        category_counts: dict[str, int] = {}
        for table_name in table_names:
            if table_name not in present:
                continue
            # Names come only from the fixed allowlists above, never user input.
            category_counts[table_name] = int(db.scalar(text(f'SELECT count(*) FROM "{table_name}"')) or 0)
        result[category] = category_counts
    return result


def total_records(counts: Mapping[str, Mapping[str, int]]) -> int:
    return sum(count for tables in counts.values() for count in tables.values())


def report(counts: Mapping[str, Mapping[str, int]]) -> dict:
    total = total_records(counts)
    return {
        "status": "empty" if total == 0 else "content_present",
        "safeForCleanTextbookTopicMigration": total == 0,
        "safeForBaselineReset": total == 0,
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
    parser.add_argument(
        "--require-baseline-reset-eligible", action="store_true",
        help="Exit with status 2 unless all known current and legacy educational-content tables are empty.",
    )
    args = parser.parse_args()
    with SessionLocal() as db:
        result = report(content_counts(db))
    print(json.dumps(result, indent=2, sort_keys=True))
    if (args.require_empty or args.require_baseline_reset_eligible) and not result["safeForBaselineReset"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
