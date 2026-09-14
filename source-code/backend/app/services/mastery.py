import math
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.errors import DomainError
from app.models import (Assessment, AssessmentInteraction, AssessmentQuestion, AssessmentResult,
    StudentProfile, TextbookUnit, UnitMastery, UnitMasteryDimension, UnitMasteryEvent)
from app.schemas.mastery import MasteryDimensionResponse, MasteryEventResponse, MasteryResponse, UnitMasteryResponse
from app.security import Principal

DIMENSIONS = ("knowledge", "application", "method", "accuracy", "reasoning", "communication", "retention")
MODE_WEIGHT = {"practice": 0.7, "mock": 1.15, "official_paper": 1.25}
DIFFICULTY_WEIGHT = {"foundation": 0.85, "standard": 1.0, "mixed": 1.0, "stretch": 1.15}
def _now(): return datetime.now(timezone.utc)

def evidence_factors(marks, difficulty, mode, hints, retries, age_days, confidence):
    return {"marks": math.sqrt(marks), "difficulty": DIFFICULTY_WEIGHT.get(difficulty, 1),
        "mode": MODE_WEIGHT.get(mode, 1), "hints": 1 / (1 + 0.2 * hints),
        "retries": 1 / (1 + 0.15 * retries), "recency": 0.35 + 0.65 * (0.5 ** (age_days / 90)),
        "assessmentConfidence": 0.75 + 0.25 * confidence}

def authorize(db, principal, student_id):
    profile = db.get(StudentProfile, student_id)
    if not profile: raise DomainError("student_not_found", "Student not found.", 404)
    if principal.user.role == "student" and principal.user.id != student_id:
        raise DomainError("student_access_denied", "Students may only view their own mastery.", 403)
    if principal.user.role == "parent" and profile.parent_id != principal.user.id:
        raise DomainError("student_access_denied", "This student is not linked to your parent account.", 403)

def _dimension(question, decision):
    source = next((point for point in question.rubric.get("markingPoints", [])
        if isinstance(point, dict) and str(point.get("code")) == decision.get("pointId")), {})
    if source.get("kind") in {"method", "accuracy", "communication"}: return source["kind"]
    value = f"{decision.get('criterion', '')} {decision.get('rationale', '')}".lower()
    if any(word in value for word in ("apply", "scenario", "substitut", "experiment", "variable")): return "application"
    if any(word in value for word in ("reason", "explain", "because", "conclusion", "evaluate")): return "reasoning"
    return "knowledge"

def _unit_weights(question):
    raw = question.unit_weights or {}
    if raw and sum(int(value) for value in raw.values()) == 100:
        return {uuid.UUID(key): int(value) / 100 for key, value in raw.items()}
    ids = [uuid.UUID(value) for value in question.unit_ids]
    return {unit_id: 1 / len(ids) for unit_id in ids} if ids else {}

def _evidence(db, student_id):
    rows = db.execute(select(AssessmentResult, AssessmentQuestion, Assessment).join(
        AssessmentQuestion, AssessmentQuestion.id == AssessmentResult.question_id).join(
        Assessment, Assessment.id == AssessmentResult.assessment_id).where(
        Assessment.student_id == student_id, AssessmentResult.status == "published").order_by(
        AssessmentResult.created_at.desc(), AssessmentResult.version_number.desc())).all()
    latest, chosen = set(), []
    for result, question, assessment in rows:
        if question.id in latest: continue
        latest.add(question.id); chosen.append((result, question, assessment))
    chosen.sort(key=lambda row: row[0].created_at)
    attempts, evidence = defaultdict(int), []
    for result, question, assessment in chosen:
        retry = attempts[question.source_question_version_id]; attempts[question.source_question_version_id] += 1
        hints = db.query(AssessmentInteraction).filter_by(assessment_id=assessment.id, question_id=question.id, kind="hint").count()
        age_days = max(0, (_now() - result.created_at).total_seconds() / 86400)
        factors = evidence_factors(question.marks, question.difficulty, assessment.mode, hints, retry, age_days, result.confidence)
        base, ratio = math.prod(factors.values()), result.awarded_marks / result.max_marks
        for unit_id, unit_weight in _unit_weights(question).items():
            dimensions = defaultdict(list); dimensions["knowledge"].append((ratio, base * unit_weight))
            for decision in result.marking_decisions:
                dimensions[_dimension(question, decision)].append((decision["marksAwarded"] / decision["maxMarks"], base * unit_weight))
            evidence.append({"result": result, "question": question, "assessment": assessment, "unitId": unit_id,
                "unitWeight": unit_weight, "weight": base * unit_weight, "ratio": ratio,
                "dimensions": dimensions, "factors": factors, "retry": retry, "hints": hints})
    return evidence

def _weighted(values):
    total = sum(weight for _, weight in values)
    return (sum(value * weight for value, weight in values) / total, total) if total else (0, 0)

def calculate(rows, now=None):
    now = now or _now()
    score, total_weight = _weighted([(row["ratio"] * 10, row["weight"]) for row in rows])
    modes = {row["assessment"].mode for row in rows}; difficulties = {row["question"].difficulty for row in rows}
    variety = len(modes) + len(difficulties); dates = [row["result"].created_at for row in rows]
    recent_days = max(0, (now - max(dates)).total_seconds() / 86400)
    span_days = (max(dates) - min(dates)).total_seconds() / 86400 if len(dates) > 1 else 0
    if len(rows) >= 8 and variety >= 3 and span_days >= 14 and recent_days <= 45 and total_weight >= 8: confidence = "high"
    elif len(rows) >= 3 and variety >= 2 and recent_days <= 90 and total_weight >= 2.5: confidence = "medium"
    else: confidence = "low"
    ordered = sorted(rows, key=lambda row: row["result"].created_at); recent, older = ordered[-3:], ordered[:-3]
    recent_score = _weighted([(row["ratio"] * 10, row["weight"]) for row in recent])[0]
    older_score = _weighted([(row["ratio"] * 10, row["weight"]) for row in older])[0] if older else recent_score
    dimension_values = defaultdict(list)
    for index, row in enumerate(ordered):
        for dimension, values in row["dimensions"].items(): dimension_values[dimension].extend(values)
        if any((row["result"].created_at - previous["result"].created_at).days >= 7 for previous in ordered[:index]):
            dimension_values["retention"].append((row["ratio"], row["weight"]))
    dimensions = {name: _weighted([(value * 10, weight) for value, weight in dimension_values[name]]) for name in DIMENSIONS}
    return {"score": min(10, max(0, score)), "weight": total_weight, "confidence": confidence,
        "provisional": confidence == "low", "count": len(rows), "variety": variety,
        "trend": max(-10, min(10, recent_score - older_score)), "last": max(dates), "dimensions": dimensions}

def record_result(db, result):
    if result.status != "published": return
    question = db.get(AssessmentQuestion, result.question_id); assessment = db.get(Assessment, result.assessment_id)
    all_evidence = _evidence(db, assessment.student_id)
    for unit_id in _unit_weights(question):
        if db.scalar(select(UnitMasteryEvent).where(UnitMasteryEvent.unit_id == unit_id, UnitMasteryEvent.trigger_result_id == result.id)): continue
        rows = [row for row in all_evidence if row["unitId"] == unit_id]; calculated = calculate(rows)
        mastery = db.scalar(select(UnitMastery).where(UnitMastery.student_id == assessment.student_id, UnitMastery.unit_id == unit_id).with_for_update())
        previous_score, previous_confidence = (float(mastery.score), mastery.confidence) if mastery else (None, None)
        if not mastery:
            mastery = UnitMastery(student_id=assessment.student_id, unit_id=unit_id, subject_id=assessment.subject_id)
            db.add(mastery)
        else:
            mastery.version_number += 1; db.execute(delete(UnitMasteryDimension).where(UnitMasteryDimension.mastery_id == mastery.id))
        mastery.score=calculated["score"]; mastery.display_score=round(calculated["score"], 1)
        mastery.confidence=calculated["confidence"]; mastery.provisional=calculated["provisional"]
        mastery.evidence_count=calculated["count"]; mastery.evidence_weight=calculated["weight"]
        mastery.variety_count=calculated["variety"]; mastery.trend=calculated["trend"]; mastery.last_evidence_at=calculated["last"]
        db.flush()
        for name, (dimension_score, weight) in calculated["dimensions"].items():
            db.add(UnitMasteryDimension(mastery_id=mastery.id, dimension=name, score=dimension_score, evidence_weight=weight))
        trigger = next(row for row in rows if row["result"].id == result.id)
        explanation = (f"{assessment.mode.replace('_', ' ')} result; {result.awarded_marks}/{result.max_marks} marks; "
            f"unit weight {round(trigger['unitWeight'] * 100)}%; {trigger['hints']} hints; retry {trigger['retry'] + 1}.")
        db.add(UnitMasteryEvent(mastery_id=mastery.id, student_id=assessment.student_id, unit_id=unit_id,
            trigger_result_id=result.id, previous_score=previous_score, new_score=calculated["score"],
            previous_confidence=previous_confidence, new_confidence=calculated["confidence"],
            contribution={"explanation": explanation, "factors": trigger["factors"], "unitWeight": trigger["unitWeight"],
                "contributingResultIds": [str(row["result"].id) for row in rows]}))
    db.commit()

def list_mastery(db, principal, student_id, subject_id=None):
    authorize(db, principal, student_id)
    query = select(UnitMastery, TextbookUnit).join(TextbookUnit, TextbookUnit.id == UnitMastery.unit_id).where(UnitMastery.student_id == student_id)
    if subject_id: query = query.where(UnitMastery.subject_id == subject_id)
    units = []
    for mastery, unit in db.execute(query.order_by(UnitMastery.subject_id, TextbookUnit.sequence)).all():
        dimensions = db.scalars(select(UnitMasteryDimension).where(UnitMasteryDimension.mastery_id == mastery.id)).all()
        events = db.scalars(select(UnitMasteryEvent).where(UnitMasteryEvent.mastery_id == mastery.id).order_by(UnitMasteryEvent.created_at.desc()).limit(10)).all()
        units.append(UnitMasteryResponse(unitId=unit.id, unitCode=unit.unit_code, unitTitle=unit.title, subjectId=mastery.subject_id,
            score=float(mastery.display_score), preciseScore=float(mastery.score), confidence=mastery.confidence,
            provisional=mastery.provisional, evidenceCount=mastery.evidence_count, evidenceWeight=float(mastery.evidence_weight),
            varietyCount=mastery.variety_count, trend=float(mastery.trend), lastEvidenceAt=mastery.last_evidence_at,
            dimensions=[MasteryDimensionResponse(dimension=row.dimension, score=float(row.score), evidenceWeight=float(row.evidence_weight)) for row in dimensions],
            recentEvents=[MasteryEventResponse(id=row.id, previousScore=float(row.previous_score) if row.previous_score is not None else None,
                newScore=float(row.new_score), previousConfidence=row.previous_confidence, newConfidence=row.new_confidence,
                explanation=row.contribution.get("explanation", "Mastery recalculated from assessed evidence."), createdAt=row.created_at) for row in events]))
    return MasteryResponse(studentId=student_id, units=units)
