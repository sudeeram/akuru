from app.main import app
import pytest
from pydantic import ValidationError

from app.services.flashcards import (MASTERY_VERSION, PROMPT_VERSION, SELECTION_VERSION,
    _clean_passage, _mastery_from_ratings, _question, _readable_paragraphs)
from app.schemas.flashcard_artifacts import FlashcardReleaseArtifact
from app.schemas.flashcards import FlashcardSessionStartRequest
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


def test_mastery_is_deterministic_and_versioned():
    assert MASTERY_VERSION == "akuru-flashcard-mastery-v1"
    assert SELECTION_VERSION == "akuru-flashcard-selection-v2"
    assert PROMPT_VERSION == "grounded-flashcards-v1"


def test_openapi_exposes_role_scoped_flashcard_workflow():
    paths = set(app.openapi()["paths"])
    assert "/api/v1/flashcards/admin/decks/generate" not in paths
    assert "/api/v1/flashcards/admin/decks/{deck_ref}/withdraw" in paths
    assert "/api/v1/flashcards/student/decks" in paths
    assert "/api/v1/flashcards/student/decks/{deck_ref}/study-options" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/reveal" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/rate" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/discard" in paths
    assert "/api/v1/flashcards/student/decks/{deck_ref}/mastery" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/visuals/{visual_ref}" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/textbook-pages/{page_id}" in paths


def test_student_source_excerpt_removes_extraction_page_boundaries():
    assert _clean_passage("Start of page 4: Particles are close together. End of page 5") == \
        "Particles are close together."
    assert _clean_passage("A real textbook sentence remains unchanged.") == \
        "A real textbook sentence remains unchanged."
    assert _readable_paragraphs("First sentence. Second sentence. Third sentence. Fourth sentence.") == [
        "First sentence. Second sentence. Third sentence.", "Fourth sentence."
    ]
    assert _readable_paragraphs("1. Heat the solid\n2. Record the temperature") == [
        "1. Heat the solid", "2. Record the temperature"
    ]


def test_new_session_contract_rejects_retired_modes_and_invalid_combinations():
    assert FlashcardSessionStartRequest(
        requestKey="request-123", mode="review", difficulty="mixed", requestedCount=20
    ).difficulty == "mixed"
    assert FlashcardSessionStartRequest(
        requestKey="request-456", mode="difficult", requestedCount=30
    ).difficulty is None
    for retired in ("quick", "normal", "full_topic", "due_today", "unit_mixed"):
        with pytest.raises(ValidationError):
            FlashcardSessionStartRequest(
                requestKey="request-old", mode=retired, difficulty="mixed", requestedCount=20
            )
    with pytest.raises(ValidationError):
        FlashcardSessionStartRequest(requestKey="request-no-difficulty", mode="review", requestedCount=20)
    with pytest.raises(ValidationError):
        FlashcardSessionStartRequest(
            requestKey="request-difficult-filter", mode="difficult", difficulty="easy", requestedCount=20
        )
    with pytest.raises(ValidationError):
        FlashcardSessionStartRequest(
            requestKey="request-wrong-count", mode="review", difficulty="mixed", requestedCount=10
        )


def test_curated_artifact_checksum_and_quality_rules_are_deterministic():
    base = {
        "schemaVersion": "akuru.flashcards.v1", "releaseId": "release-example", "courseId": "igcse",
        "subjectId": "chemistry", "textbookRef": "book_example", "groupRef": "group_example",
        "createdAt": "2026-09-24T00:00:00Z", "editor": "AKURU reviewer",
        "sourceContentChecksums": {"topicver_example": "a" * 64},
        "decks": [{"key": "deck-example", "title": "Example cards", "topicRef": "topic_example",
            "contentVersionRef": "topicver_example", "requiredConceptKeys": ["particles", "states"], "cards": [
                {"key": "card-one", "conceptKey": "particles", "category": "essential_knowledge",
                 "variationType": "recall", "difficulty": "easy", "question": "What is diffusion?", "answer": "Diffusion is the spreading of particles.",
                 "sourceChunkRefs": ["00000000-0000-0000-0000-000000000001"], "reviewer": "Reviewer"},
                {"key": "card-two", "conceptKey": "particles", "category": "explanation_comparison",
                 "variationType": "explanation", "difficulty": "difficult", "question": "Why do gases diffuse?", "answer": "Their particles move randomly.",
                 "sourceChunkRefs": ["00000000-0000-0000-0000-000000000001"], "reviewer": "Reviewer"},
                {"key": "card-three", "conceptKey": "states", "category": "application_misconception",
                 "variationType": "application", "difficulty": "difficult", "question": "Why can a liquid flow?", "answer": "Its particles can move around one another.",
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


def test_completed_rating_history_drives_mastery_deterministically():
    assert _mastery_from_ratings([]) == (0.0, "to_evaluate", 0, 0)
    assert _mastery_from_ratings(["easy", "easy", "easy"])[1:3] == ("mastered", 3)
    score, status, streak, count = _mastery_from_ratings(["easy", "easy", "easy", "difficult"])
    assert status == "good" and streak == 0 and count == 4 and 0.55 <= score < 0.8
    score, status, streak, count = _mastery_from_ratings(["easy", "again"])
    assert status == "needs_review" and streak == 0 and count == 2 and score == 1.0
    recovered = _mastery_from_ratings(["easy", "again", "good", "easy", "easy", "easy"])
    assert recovered[1:3] == ("mastered", 3)


def test_mastery_storage_is_structurally_student_specific():
    from app.models import FlashcardLearningState, FlashcardReview

    learning_uniques = {tuple(constraint.columns.keys())
                        for constraint in FlashcardLearningState.__table__.constraints
                        if constraint.__class__.__name__ == "UniqueConstraint"}
    review_uniques = {tuple(constraint.columns.keys())
                      for constraint in FlashcardReview.__table__.constraints
                      if constraint.__class__.__name__ == "UniqueConstraint"}
    assert ("student_id", "card_version_id") in learning_uniques
    assert ("session_id", "card_version_id") in review_uniques
