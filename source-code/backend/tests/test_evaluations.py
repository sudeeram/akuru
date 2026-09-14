from app.services.evaluations import THRESHOLDS, _score


def test_evaluation_metrics_cover_step_19_quality_dimensions():
    assert _score("inventory", {"questionIds": ["Q1", "Q2"]}, {"questionIds": ["Q1"]}) == {"inventory_recall": .5}
    assert _score("equation", {"equation": "x²"}, {"equation": "x²"})["equation_preservation"] == 1
    assert _score("diagram", {"preserved": True}, {"preserved": False})["diagram_preservation"] == 0
    mapping = _score("mapping", {"unitIds": ["u1"], "crossSubjectRejected": True}, {"unitIds": ["u1", "u2"], "crossSubjectRejected": True})
    assert mapping == {"mapping_precision": .5, "cross_subject_rejection": 1}
    marking = _score("marking", {"marks": 2, "methodPoints": ["M1"]}, {"marks": 1, "methodPoints": ["M1"]})
    assert marking == {"mark_exactness": 0, "method_mark_exactness": 1}
    feedback = _score("feedback", {"smallErrors": ["unit"], "sourceIds": ["s1"], "improvedAnswerRequired": True}, {"smallErrors": ["unit"], "sourceIds": ["s1"], "improvedAnswer": "Improved"})
    assert feedback == {"small_error_recall": 1, "improved_answer_quality": 1, "grounding": 1}
    assert set(THRESHOLDS) == {"inventory_recall", "ocr_similarity", "equation_preservation", "diagram_preservation", "mapping_precision", "cross_subject_rejection", "mark_exactness", "method_mark_exactness", "small_error_recall", "improved_answer_quality", "grounding", "repeatability"}
