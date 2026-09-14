import hashlib
import json
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import AuditEvent, EvaluationCorpus, EvaluationRelease, EvaluationRun, Subject
from app.schemas.evaluations import CorpusCreate, EvaluationRunCreate, ReleaseUpdate
from app.security import Principal


PHASE1_SUBJECTS = ("english", "maths", "ict", "biology", "chemistry", "physics", "french", "human-biology")
THRESHOLDS = {
    "inventory_recall": .98, "ocr_similarity": .97, "equation_preservation": 1.0,
    "diagram_preservation": 1.0, "mapping_precision": .95, "cross_subject_rejection": 1.0,
    "mark_exactness": .90, "method_mark_exactness": .95, "small_error_recall": .90,
    "improved_answer_quality": .95, "grounding": 1.0, "repeatability": .95,
}


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _ratio(found, expected) -> float:
    expected_set, found_set = set(map(str, expected or [])), set(map(str, found or []))
    return 1.0 if not expected_set else len(expected_set & found_set) / len(expected_set)


def _score(category: str, expected: dict, output: dict) -> dict[str, float]:
    if category == "inventory": return {"inventory_recall": _ratio(output.get("questionIds"), expected.get("questionIds"))}
    if category == "ocr": return {"ocr_similarity": SequenceMatcher(None, str(expected.get("text", "")).strip(), str(output.get("text", "")).strip()).ratio()}
    if category == "equation": return {"equation_preservation": float(output.get("equation") == expected.get("equation"))}
    if category == "diagram": return {"diagram_preservation": float(bool(output.get("preserved")) == bool(expected.get("preserved", True)))}
    if category == "mapping":
        predicted, wanted = output.get("unitIds", []), expected.get("unitIds", [])
        precision = 1.0 if not predicted and not wanted else (len(set(predicted) & set(wanted)) / len(set(predicted)) if predicted else 0.0)
        return {"mapping_precision": precision, "cross_subject_rejection": float(bool(output.get("crossSubjectRejected")) == bool(expected.get("crossSubjectRejected", True)))}
    if category == "marking":
        return {"mark_exactness": float(output.get("marks") == expected.get("marks")), "method_mark_exactness": _ratio(output.get("methodPoints"), expected.get("methodPoints"))}
    if category == "feedback":
        improved = str(output.get("improvedAnswer", "")).strip()
        return {"small_error_recall": _ratio(output.get("smallErrors"), expected.get("smallErrors")),
                "improved_answer_quality": float(bool(improved) == bool(expected.get("improvedAnswerRequired", True))),
                "grounding": _ratio(output.get("sourceIds"), expected.get("sourceIds"))}
    if category == "repeatability": return {"repeatability": _ratio(output.get("stableDecisions"), expected.get("stableDecisions"))}
    return {}


def corpus_response(row):
    return {"id": row.id, "subjectId": row.subject_id, "versionNumber": row.version_number, "name": row.name,
            "cases": row.cases, "status": row.status, "contentHash": row.content_hash,
            "createdAt": row.created_at, "approvedAt": row.approved_at}


def run_response(row):
    return {"id": row.id, "corpusId": row.corpus_id, "subjectId": row.subject_id, "candidateModel": row.candidate_model,
            "promptVersion": row.prompt_version, "metrics": row.metrics, "thresholds": row.thresholds,
            "passed": row.passed, "failureReasons": row.failure_reasons, "createdAt": row.created_at}


def release_response(row):
    return {"subjectId": row.subject_id, "workflow": row.workflow, "mode": row.mode, "runId": row.run_id,
            "confidenceThreshold": row.confidence_threshold, "activatedAt": row.activated_at}


def dashboard(db: Session):
    corpora = db.scalars(select(EvaluationCorpus).order_by(EvaluationCorpus.subject_id, EvaluationCorpus.version_number.desc())).all()
    runs = db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(100)).all()
    releases = db.scalars(select(EvaluationRelease).order_by(EvaluationRelease.subject_id, EvaluationRelease.workflow)).all()
    approved = {row.subject_id for row in corpora if row.status == "approved"}
    return {"corpora": [corpus_response(row) for row in corpora], "runs": [run_response(row) for row in runs],
            "releases": [release_response(row) for row in releases], "missingApprovedSubjects": [s for s in PHASE1_SUBJECTS if s not in approved]}


def create_corpus(db: Session, principal: Principal, payload: CorpusCreate):
    if payload.subjectId not in PHASE1_SUBJECTS or not db.get(Subject, payload.subjectId):
        raise DomainError("evaluation_subject_invalid", "Select a Phase 1 iGCSE subject.", 422)
    version = (db.scalar(select(func.max(EvaluationCorpus.version_number)).where(EvaluationCorpus.subject_id == payload.subjectId)) or 0) + 1
    cases = [case.model_dump() for case in payload.cases]
    row = EvaluationCorpus(subject_id=payload.subjectId, version_number=version, name=payload.name, cases=cases,
                           content_hash=_hash(cases), created_by=principal.user.id)
    db.add(row); db.flush()
    db.add(AuditEvent(actor_id=principal.user.id, action="evaluation.corpus_created", target_type="evaluation_corpus", target_id=str(row.id), event_data={"subjectId": row.subject_id, "version": version, "caseCount": len(cases)}))
    db.commit(); db.refresh(row); return corpus_response(row)


def review_corpus(db: Session, principal: Principal, corpus_id: uuid.UUID, decision: str):
    row = db.get(EvaluationCorpus, corpus_id)
    if not row: raise DomainError("evaluation_corpus_not_found", "Evaluation corpus was not found.", 404)
    if decision == "approved":
        categories = {case["category"] for case in row.cases}
        required = {"inventory", "ocr", "equation", "diagram", "mapping", "marking", "feedback", "repeatability"}
        if categories != required:
            raise DomainError("evaluation_corpus_incomplete", "Approved corpora must include every required evaluation category.", 409)
        for prior in db.scalars(select(EvaluationCorpus).where(EvaluationCorpus.subject_id == row.subject_id, EvaluationCorpus.status == "approved", EvaluationCorpus.id != row.id)):
            prior.status = "retired"
        row.approved_by, row.approved_at = principal.user.id, datetime.now(timezone.utc)
    row.status = decision
    db.add(AuditEvent(actor_id=principal.user.id, action=f"evaluation.corpus_{decision}", target_type="evaluation_corpus", target_id=str(row.id), event_data={"subjectId": row.subject_id}))
    db.commit(); db.refresh(row); return corpus_response(row)


def run(db: Session, principal: Principal, payload: EvaluationRunCreate):
    corpus = db.get(EvaluationCorpus, payload.corpusId)
    if not corpus or corpus.status != "approved": raise DomainError("evaluation_corpus_not_approved", "Only an approved corpus can be evaluated.", 409)
    observed = {item.caseId: item.output for item in payload.observations}
    if len(observed) != len(payload.observations) or set(observed) != {case["caseId"] for case in corpus.cases}:
        raise DomainError("evaluation_observations_incomplete", "Provide exactly one observation for every corpus case.", 422)
    values: dict[str, list[float]] = {}
    for case in corpus.cases:
        for metric, value in _score(case["category"], case["expected"], observed[case["caseId"]]).items(): values.setdefault(metric, []).append(value)
    metrics = {key: round(sum(scores) / len(scores), 6) for key, scores in values.items()}
    missing = sorted(set(THRESHOLDS) - set(metrics))
    failures = [f"{key} {metrics[key]:.3f} is below {threshold:.3f}" for key, threshold in THRESHOLDS.items() if key in metrics and metrics[key] < threshold]
    failures += [f"Missing metric: {key}" for key in missing]
    row = EvaluationRun(corpus_id=corpus.id, subject_id=corpus.subject_id, candidate_model=payload.candidateModel,
        prompt_version=payload.promptVersion, observations_hash=_hash([item.model_dump() for item in payload.observations]),
        metrics=metrics, thresholds=THRESHOLDS, passed=not failures, failure_reasons=failures, created_by=principal.user.id)
    db.add(row); db.flush()
    db.add(AuditEvent(actor_id=principal.user.id, action="evaluation.run_completed", target_type="evaluation_run", target_id=str(row.id), event_data={"subjectId": row.subject_id, "passed": row.passed, "model": row.candidate_model, "promptVersion": row.prompt_version}))
    db.commit(); db.refresh(row); return run_response(row)


def set_release(db: Session, principal: Principal, payload: ReleaseUpdate):
    run_row = db.get(EvaluationRun, payload.runId) if payload.runId else None
    if payload.mode == "automatic" and (not run_row or not run_row.passed or run_row.subject_id != payload.subjectId):
        raise DomainError("evaluation_release_blocked", "Automatic workflow requires a passing run for the same subject.", 409)
    row = db.scalar(select(EvaluationRelease).where(EvaluationRelease.subject_id == payload.subjectId, EvaluationRelease.workflow == payload.workflow))
    if not row:
        row = EvaluationRelease(subject_id=payload.subjectId, workflow=payload.workflow, activated_by=principal.user.id)
        db.add(row)
    row.mode, row.run_id, row.confidence_threshold = payload.mode, payload.runId, payload.confidenceThreshold
    row.activated_by, row.activated_at = principal.user.id, datetime.now(timezone.utc)
    db.add(AuditEvent(actor_id=principal.user.id, action="evaluation.release_updated", target_type="evaluation_release", target_id=f"{payload.subjectId}:{payload.workflow}", event_data={"mode": payload.mode, "runId": str(payload.runId) if payload.runId else None}))
    db.commit(); db.refresh(row); return release_response(row)


def automatic_feedback_allowed(db: Session, subject_id: str, confidence: float, model: str, prompt_version: str) -> tuple[bool, str]:
    release = db.scalar(select(EvaluationRelease).where(EvaluationRelease.subject_id == subject_id, EvaluationRelease.workflow == "assessment_feedback"))
    if not release or release.mode != "automatic" or not release.run_id:
        return False, "Automatic feedback is disabled until an evaluation release passes Admin review."
    run_row = db.get(EvaluationRun, release.run_id)
    if not run_row or not run_row.passed:
        return False, "The active evaluation release no longer has a passing regression run."
    corpus = db.get(EvaluationCorpus, run_row.corpus_id)
    if not corpus or corpus.status != "approved":
        return False, "The release corpus has been retired; run the candidate against the current approved corpus."
    if run_row.candidate_model != model or run_row.prompt_version != prompt_version:
        return False, "The active model or prompt version differs from the passing evaluation release."
    if confidence < release.confidence_threshold:
        return False, f"Confidence {confidence:.2f} is below the evaluated automatic-feedback threshold {release.confidence_threshold:.2f}."
    return True, ""
