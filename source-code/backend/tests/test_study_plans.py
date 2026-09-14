from datetime import datetime, timezone
from types import SimpleNamespace
from app.services.study_plans import _balanced, _fingerprint

def row(identifier, subject, score, trend=0, confidence="medium", occurrence=1):
    recommendation=SimpleNamespace(id=identifier,subject_id=subject,created_at=datetime.now(timezone.utc),review_status="approved")
    diagnosis=SimpleNamespace(occurrence_number=occurrence)
    mastery=SimpleNamespace(score=score,trend=trend,confidence=confidence,version_number=1)
    return recommendation,diagnosis,mastery

def test_balancing_rotates_subjects_while_preserving_priority():
    rows=[row("m1","maths",3),row("m2","maths",4),row("s1","biology",5),row("s2","biology",6)]
    selected=_balanced(rows,{"biology"},4)
    assert [item[0].subject_id for item in selected] == ["maths","biology","maths","biology"]
    assert selected[0][0].id == "m1" and selected[1][0].id == "s1"

def test_fingerprint_changes_only_with_planning_evidence():
    rows=[row("m1","maths",3)]
    assert _fingerprint(rows) == _fingerprint(rows)
    rows[0][2].version_number=2
    assert _fingerprint(rows) != _fingerprint([row("m1","maths",3)])
