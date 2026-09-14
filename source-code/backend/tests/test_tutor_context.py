from types import SimpleNamespace
import uuid
from datetime import datetime, timedelta, timezone

from app.services.tutor_context import _signal_statements


def test_strong_unit_one_algebra_claim_requires_assessed_evidence():
    unit = SimpleNamespace(unit_code="Unit 1", title="Algebra")
    mastery = SimpleNamespace(display_score=8.0, confidence="high", provisional=False, variety_count=2, trend=0.1)
    events = [SimpleNamespace(id=uuid.uuid4()), SimpleNamespace(id=uuid.uuid4())]
    signals, statements = _signal_statements(unit, mastery, events)
    assert signals == ["strong"]
    assert statements[0].text == "Your assessed work shows strong skills in Unit 1 – Algebra."
    assert len(statements[0].evidenceRefs) == 2
    assert statements[0].cautious is False


def test_unassessed_mastery_value_never_becomes_a_claim():
    unit = SimpleNamespace(unit_code="Unit 2", title="Equations")
    mastery = SimpleNamespace(display_score=10.0, confidence="high", provisional=False, variety_count=9, trend=1.0)
    signals, statements = _signal_statements(unit, mastery, [])
    assert signals == ["insufficient_evidence"]
    assert statements[0].evidenceRefs == []
    assert statements[0].cautious is True


def test_old_mastery_evidence_uses_cautious_language():
    unit = SimpleNamespace(unit_code="Unit 3", title="Graphs")
    mastery = SimpleNamespace(display_score=8.0, confidence="high", provisional=False, variety_count=3,
                              trend=.5, last_evidence_at=datetime.now(timezone.utc) - timedelta(days=120))
    events = [SimpleNamespace(id=uuid.uuid4()), SimpleNamespace(id=uuid.uuid4())]
    signals, statements = _signal_statements(unit, mastery, events)
    assert signals == ["low_confidence"]
    assert "old or limited" in statements[0].text
    assert statements[0].cautious is True
