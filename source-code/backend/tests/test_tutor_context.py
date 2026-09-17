import uuid

from app.services.tutor_context import CONTEXT_ALGORITHM, _reference


def test_context_algorithm_is_topic_only():
    assert CONTEXT_ALGORITHM == "learner-context-v2-topics"


def test_evidence_references_are_stable_and_versioned():
    row_id = uuid.UUID("00000000-0000-0000-0000-000000000123")
    assert _reference("topic_mastery", row_id) == f"topic_mastery:{row_id}"
    assert _reference("assessment", row_id, 3) == f"assessment:{row_id}:v3"
