from collections import defaultdict
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.mastery import calculate, evidence_factors


def evidence(when, ratio, mode="practice", difficulty="foundation", weight=1):
    return {"ratio": ratio, "weight": weight, "result": SimpleNamespace(created_at=when),
        "assessment": SimpleNamespace(mode=mode), "question": SimpleNamespace(difficulty=difficulty),
        "dimensions": defaultdict(list, {"knowledge": [(ratio, weight)]})}


def test_one_easy_question_is_low_confidence_and_provisional():
    now = datetime.now(timezone.utc)
    result = calculate([evidence(now, 1)], now)
    assert result["score"] == 10
    assert result["confidence"] == "low" and result["provisional"] is True


def test_quantity_variety_and_recency_raise_confidence_without_changing_precision():
    now = datetime.now(timezone.utc)
    rows = [evidence(now - timedelta(days=21 - index * 3), 0.73333,
        "official_paper" if index % 2 else "mock", "stretch" if index % 3 else "standard", 1.5)
        for index in range(8)]
    result = calculate(rows, now)
    assert result["confidence"] == "high" and result["provisional"] is False
    assert 7.3332 < result["score"] < 7.3334


def test_recent_trend_keeps_older_evidence_in_overall_score():
    now = datetime.now(timezone.utc)
    rows = [evidence(now - timedelta(days=20), 0.3), evidence(now - timedelta(days=15), 0.4),
        evidence(now - timedelta(days=3), 0.7), evidence(now - timedelta(days=2), 0.8),
        evidence(now - timedelta(days=1), 0.9)]
    result = calculate(rows, now)
    assert result["trend"] > 0
    assert 6 < result["score"] < 9


def test_timed_papers_outweigh_hinted_retried_practice():
    official = evidence_factors(4, "standard", "official_paper", 0, 0, 0, 0.9)
    practice = evidence_factors(4, "standard", "practice", 2, 2, 0, 0.9)
    product = lambda values: __import__("math").prod(values.values())
    assert product(official) > product(practice) * 2
