from app.main import app
from app.services.flashcards import INTERVALS, PROMPT_VERSION, SCHEDULER_VERSION, _question


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
    assert PROMPT_VERSION == "grounded-flashcards-v1"


def test_openapi_exposes_role_scoped_flashcard_workflow():
    paths = set(app.openapi()["paths"])
    assert "/api/v1/flashcards/admin/decks/generate" in paths
    assert "/api/v1/flashcards/admin/decks/{deck_ref}/release" in paths
    assert "/api/v1/flashcards/student/decks" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/reveal" in paths
    assert "/api/v1/flashcards/student/sessions/{session_ref}/rate" in paths
