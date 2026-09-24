from app.main import app
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from app.services.flashcards import (INTERVALS, PROMPT_VERSION, SCHEDULER_VERSION, SELECTION_VERSION,
    _clean_passage, _question, _schedule, _selection_reason)
from app.schemas.flashcard_artifacts import FlashcardReleaseArtifact
from app.services.flashcard_artifacts import _quality_errors, canonical_checksum


def test_grounded_draft_recognizes_definition_and_flags_generic_wording():
    front, back, warnings = _question("Diffusion is the random movement of particles.", "States of Matter")
    assert front == "What is Diffusion?"
    assert back == "Diffusion is the random movement of particles."
    assert warnings == []
    generic_front, _, generic_warnings = _question(
        "Particles move more quickly when their temperature rises.", "States of Matter"
    )
    assert generic_front.startswith("Explain this key idea from States of Matter")
    assert generic_warnings


def test_scheduler_is_deterministic_and_versioned():
    assert INTERVALS == {"again": 0, "difficult": 1, "good": 3, "easy": 7}
    assert SCHEDULER_VERSION == "akuru-spaced-review-v1"
    assert SELECTION_VERSION == "akuru-adaptive-selection-v1"
    assert PROMPT_VERSION == "grounded-flashcards-v1"


def test_openapi_exposes_role_scoped_flashcard_workflow():
    paths = set(app.openapi()["paths"])
    assert "/api/v1/flashcards/admin/decks/generate" not in paths
    assert "/api/v1/flashcards/admin/decks/{deck_ref}/withdraw" in paths
    assert "/api/v1/flashcards/student/decks" in paths
    assert "/api/v1/flashcards/student/decks/{deck_ref}/study-options" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/reveal" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/rate" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/visuals/{visual_ref}" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/textbook-pages/{page_id}" in paths


def test_student_source_excerpt_removes_extraction_page_boundaries():
    assert _clean_passage("Start of page 4: Particles are close together. End of page 5") == \
        "Particles are close together."
    assert _clean_passage("A real textbook sentence remains unchanged.") == \
        "A real textbook sentence remains unchanged."


def test_curated_artifact_checksum_and_quality_rules_are_deterministic():
    base = {
        "schemaVersion": "akuru.flashcards.v1", "releaseId": "release-example", "courseId": "igcse",
        "subjectId": "chemistry", "textbookRef": "book_example", "groupRef": "group_example",
        "createdAt": "2026-09-24T00:00:00Z", "editor": "AKURU reviewer",
        "sourceContentChecksums": {"topicver_example": "a" * 64},
        "decks": [{"key": "deck-example", "title": "Example cards", "topicRef": "topic_example",
            "contentVersionRef": "topicver_example", "requiredConceptKeys": ["particles", "states"], "cards": [
                {"key": "card-one", "conceptKey": "particles", "category": "essential_knowledge",
                 "variationType": "recall", "question": "What is diffusion?", "answer": "Diffusion is the spreading of particles.",
                 "sourceChunkRefs": ["00000000-0000-0000-0000-000000000001"], "reviewer": "Reviewer"},
                {"key": "card-two", "conceptKey": "particles", "category": "explanation_comparison",
                 "variationType": "explanation", "question": "Why do gases diffuse?", "answer": "Their particles move randomly.",
                 "sourceChunkRefs": ["00000000-0000-0000-0000-000000000001"], "reviewer": "Reviewer"},
                {"key": "card-three", "conceptKey": "states", "category": "application_misconception",
                 "variationType": "application", "question": "Why can a liquid flow?", "answer": "Its particles can move around one another.",
                 "sourceChunkRefs": ["00000000-0000-0000-0000-000000000001"], "reviewer": "Reviewer"}
            ]}]
    }
    artifact = FlashcardReleaseArtifact.model_validate(base)
    assert canonical_checksum(artifact) == canonical_checksum(artifact)
    assert _quality_errors(artifact) == []
    base["decks"][0]["cards"][0]["question"] = "Explain diffusion using particle movement."
    assert _quality_errors(FlashcardReleaseArtifact.model_validate(base)) == []
    base["decks"][0]["cards"][0]["question"] = "Figure 1.2"
    assert _quality_errors(FlashcardReleaseArtifact.model_validate(base))


def test_selection_priority_and_scheduler_are_deterministic():
    now = datetime(2026, 9, 24, tzinfo=timezone.utc)
    unseen_rank, unseen_reason = _selection_reason(None, False, now)
    assert (unseen_rank, unseen_reason) == (3, "unseen")
    overdue = SimpleNamespace(due_at=now - timedelta(days=1), last_rating="good", repetitions=4)
    assert _selection_reason(overdue, False, now) == (0, "overdue")
    state = SimpleNamespace(repetitions=0, lapses=0, interval_days=0, ease_factor=2.5,
        last_rating=None, due_at=now, last_reviewed_at=None)
    assert _schedule(state, "again", now) == now + timedelta(minutes=10)
    assert state.lapses == 1 and state.interval_days == 0
    due = _schedule(state, "good", now)
    assert due == now + timedelta(days=1)
    assert state.repetitions == 1 and state.last_rating == "good"
