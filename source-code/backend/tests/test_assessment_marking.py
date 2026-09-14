import pytest

from app.errors import DomainError
from app.schemas.assessments import MarkingDecision
from app.services.assessment_marking import _validate
from app.services.subject_marking import analyze


def decision(**changes):
    value = {"pointId": "M1", "criterion": "States the required method", "awarded": True,
             "marksAwarded": 1, "maxMarks": 1, "studentEvidence": "I used the method",
             "rationale": "The method is present.", "confidence": 0.9}
    value.update(changes)
    return MarkingDecision.model_validate(value)


def test_marking_requires_exact_official_points_and_caps_question_total():
    points = [{"pointId": "M1", "criterion": "States the required method", "maxMarks": 1}]
    assert _validate([decision()], points, 1) == 1
    with pytest.raises(DomainError, match="every approved marking point"):
        _validate([], points, 1)
    with pytest.raises(DomainError, match="question maximum"):
        _validate([decision()], points, 0)


def test_marking_rejects_changed_official_criterion():
    points = [{"pointId": "M1", "criterion": "States the required method", "maxMarks": 1}]
    with pytest.raises(DomainError, match="changed an approved marking point"):
        _validate([decision(criterion="A point invented by the model")], points, 1)


def test_maths_method_mark_survives_wrong_final_answer_without_deterministic_marking():
    points = [{"pointId": "M1", "criterion": "Correct substitution", "maxMarks": 1},
              {"pointId": "A1", "criterion": "Correct final answer", "maxMarks": 1}]
    checks = analyze("maths", "Calculate x", "x = 2 + 3\n= 6", {
        "markingPoints": [{"text": "Correct substitution"}, {"text": "x=5"}], "alternatives": ["x=5"]})
    decisions = [decision(pointId="M1", criterion="Correct substitution"),
                 decision(pointId="A1", criterion="Correct final answer", awarded=False,
                          marksAwarded=0, studentEvidence="The student wrote 6", rationale="The official answer is 5")]
    assert checks["awardedMarks"] is None
    assert any(item["equivalent"] is False for item in checks["signals"]["symbolicEquivalence"])
    assert _validate(decisions, points, 2) == 1
