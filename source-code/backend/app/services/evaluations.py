import hashlib
import json
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import AuditEvent, EvaluationCorpus, EvaluationRelease, EvaluationRun, Subject, TutorAvatar, TutorVoicePreset
from app.schemas.evaluations import CorpusCreate, EvaluationRunCreate, ReleaseUpdate
from app.security import Principal


PHASE1_SUBJECTS = ("english", "maths", "ict", "biology", "chemistry", "physics", "french", "human-biology")
THRESHOLDS = {
    "inventory_recall": .98, "ocr_similarity": .97, "equation_preservation": 1.0,
    "diagram_preservation": 1.0, "mapping_precision": .95, "cross_subject_rejection": 1.0,
    "mark_exactness": .90, "method_mark_exactness": .95, "small_error_recall": .90,
    "improved_answer_quality": .95, "grounding": 1.0, "repeatability": .95,
}
TUTOR_CATEGORIES = {
    "tutor_factual", "tutor_mathematical", "tutor_grounding", "tutor_personalisation",
    "tutor_recommendation", "tutor_persona", "tutor_security", "tutor_handover",
    "tutor_voice", "tutor_preset_safety", "tutor_operations",
}
TUTOR_THRESHOLDS = {
    "tutor_factual_accuracy": .95, "tutor_mathematical_accuracy": 1.0,
    "tutor_source_grounding": 1.0, "tutor_personalisation_accuracy": 1.0,
    "tutor_recommendation_accuracy": 1.0, "tutor_persona_suitability": 1.0,
    "tutor_security_isolation": 1.0, "tutor_handover_accuracy": 1.0,
    "tutor_voice_quality": .95, "tutor_preset_safety": 1.0,
    "tutor_operational_readiness": 1.0,
}
TUTOR_METRICS = {
    "tutor_factual": "tutor_factual_accuracy",
    "tutor_mathematical": "tutor_mathematical_accuracy",
    "tutor_grounding": "tutor_source_grounding",
    "tutor_personalisation": "tutor_personalisation_accuracy",
    "tutor_recommendation": "tutor_recommendation_accuracy",
    "tutor_persona": "tutor_persona_suitability",
    "tutor_security": "tutor_security_isolation",
    "tutor_handover": "tutor_handover_accuracy",
    "tutor_voice": "tutor_voice_quality",
    "tutor_preset_safety": "tutor_preset_safety",
    "tutor_operations": "tutor_operational_readiness",
}
TUTOR_RELEASE_MODALITY = {
    "tutor_text": "text", "tutor_voice": "voice", "tutor_tools": "tools",
    "tutor_learner_context": "tools", "tutor_next_unit": "tools", "tutor_sources": "tools",
    "tutor_practice": "tools", "tutor_visuals": "tools",
}
TUTOR_PERSONA_COMBINATION_COUNT = 3 * 4 * 3 * 3 * 3 * 3 * 3 * 4


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _ratio(found, expected) -> float:
    expected_set, found_set = set(map(str, expected or [])), set(map(str, found or []))
    return 1.0 if not expected_set else len(expected_set & found_set) / len(expected_set)


def _score(category: str, expected: dict, output: dict) -> dict[str, float]:
    if category in TUTOR_CATEGORIES:
        return {TUTOR_METRICS[category]: _ratio(output.get("passedChecks"), expected.get("requiredChecks"))}
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
    return {"id": row.id, "subjectId": row.subject_id, "workflow": row.workflow,
            "versionNumber": row.version_number, "name": row.name,
            "cases": row.cases, "status": row.status, "contentHash": row.content_hash,
            "createdAt": row.created_at, "approvedAt": row.approved_at}


def run_response(row):
    return {"id": row.id, "corpusId": row.corpus_id, "subjectId": row.subject_id, "candidateModel": row.candidate_model,
            "workflow": row.workflow, "modality": row.modality, "environment": row.environment,
            "promptVersion": row.prompt_version, "metrics": row.metrics, "thresholds": row.thresholds,
            "passed": row.passed, "failureReasons": row.failure_reasons, "createdAt": row.created_at}


def release_response(row):
    return {"subjectId": row.subject_id, "workflow": row.workflow, "mode": row.mode, "runId": row.run_id,
            "confidenceThreshold": row.confidence_threshold, "audience": row.audience,
            "activatedAt": row.activated_at}


def dashboard(db: Session):
    corpora = db.scalars(select(EvaluationCorpus).order_by(EvaluationCorpus.subject_id, EvaluationCorpus.version_number.desc())).all()
    runs = db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(100)).all()
    releases = db.scalars(select(EvaluationRelease).order_by(EvaluationRelease.subject_id, EvaluationRelease.workflow)).all()
    return {"corpora": [corpus_response(row) for row in corpora], "runs": [run_response(row) for row in runs],
            "releases": [release_response(row) for row in releases],
            "missingApprovedSubjects": [s for s in PHASE1_SUBJECTS if not any(r.subject_id == s and r.workflow == "assessment" and r.status == "approved" for r in corpora)],
            "missingApprovedTutorSubjects": [s for s in PHASE1_SUBJECTS if not any(r.subject_id == s and r.workflow == "tutor" and r.status == "approved" for r in corpora)]}


def create_corpus(db: Session, principal: Principal, payload: CorpusCreate):
    if payload.subjectId not in PHASE1_SUBJECTS or not db.get(Subject, payload.subjectId):
        raise DomainError("evaluation_subject_invalid", "Select a Phase 1 iGCSE subject.", 422)
    version = (db.scalar(select(func.max(EvaluationCorpus.version_number)).where(
        EvaluationCorpus.subject_id == payload.subjectId, EvaluationCorpus.workflow == payload.workflow)) or 0) + 1
    cases = [case.model_dump() for case in payload.cases]
    row = EvaluationCorpus(subject_id=payload.subjectId, workflow=payload.workflow,
                           version_number=version, name=payload.name, cases=cases,
                           content_hash=_hash(cases), created_by=principal.user.id)
    db.add(row); db.flush()
    db.add(AuditEvent(actor_id=principal.user.id, action="evaluation.corpus_created", target_type="evaluation_corpus", target_id=str(row.id), event_data={"subjectId": row.subject_id, "version": version, "caseCount": len(cases)}))
    db.commit(); db.refresh(row); return corpus_response(row)


def review_corpus(db: Session, principal: Principal, corpus_id: uuid.UUID, decision: str):
    row = db.get(EvaluationCorpus, corpus_id)
    if not row: raise DomainError("evaluation_corpus_not_found", "Evaluation corpus was not found.", 404)
    if decision == "approved":
        categories = {case["category"] for case in row.cases}
        required = TUTOR_CATEGORIES if row.workflow == "tutor" else {"inventory", "ocr", "equation", "diagram", "mapping", "marking", "feedback", "repeatability"}
        if categories != required:
            raise DomainError("evaluation_corpus_incomplete", "Approved corpora must include every required evaluation category.", 409)
        if row.workflow == "tutor":
            mastery = {case.get("input", {}).get("masteryLevel") for case in row.cases}
            if not {"low", "medium", "high"}.issubset(mastery):
                raise DomainError("tutor_evaluation_mastery_incomplete", "Tutor corpora must cover low, medium and high mastery levels.", 409)
            persona = next(case for case in row.cases if case["category"] == "tutor_persona")
            persona_expected = persona.get("expected", {})
            if (not persona_expected.get("personaMatrixComplete") or
                    persona_expected.get("personaCombinationCount") != TUTOR_PERSONA_COMBINATION_COUNT):
                raise DomainError("tutor_evaluation_persona_incomplete", "Tutor corpora must review the complete supported persona matrix.", 409)
            preset = next(case for case in row.cases if case["category"] == "tutor_preset_safety")
            expected = preset.get("expected", {})
            avatars = set(db.scalars(select(TutorAvatar.code).where(TutorAvatar.is_enabled.is_(True))).all())
            voices = set(db.scalars(select(TutorVoicePreset.code).where(TutorVoicePreset.is_enabled.is_(True))).all())
            if set(expected.get("reviewedAvatarCodes", [])) != avatars or set(expected.get("reviewedVoiceCodes", [])) != voices:
                raise DomainError("tutor_evaluation_presets_incomplete", "Every enabled avatar and voice preset must be included in the child-safety review.", 409)
        for prior in db.scalars(select(EvaluationCorpus).where(EvaluationCorpus.subject_id == row.subject_id, EvaluationCorpus.status == "approved", EvaluationCorpus.id != row.id)):
            if prior.workflow == row.workflow: prior.status = "retired"
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
    if corpus.workflow == "assessment" and payload.modality != "assessment":
        raise DomainError("evaluation_modality_invalid", "Assessment corpora require assessment modality.", 422)
    if corpus.workflow == "tutor" and payload.modality == "assessment":
        raise DomainError("evaluation_modality_invalid", "Tutor corpora require text, voice or tools modality.", 422)
    values: dict[str, list[float]] = {}
    for case in corpus.cases:
        for metric, value in _score(case["category"], case["expected"], observed[case["caseId"]]).items(): values.setdefault(metric, []).append(value)
    metrics = {key: round(sum(scores) / len(scores), 6) for key, scores in values.items()}
    thresholds = TUTOR_THRESHOLDS if corpus.workflow == "tutor" else THRESHOLDS
    missing = sorted(set(thresholds) - set(metrics))
    failures = [f"{key} {metrics[key]:.3f} is below {threshold:.3f}" for key, threshold in thresholds.items() if key in metrics and metrics[key] < threshold]
    failures += [f"Missing metric: {key}" for key in missing]
    row = EvaluationRun(corpus_id=corpus.id, subject_id=corpus.subject_id, workflow=corpus.workflow,
        modality=payload.modality, environment=payload.environment, candidate_model=payload.candidateModel,
        prompt_version=payload.promptVersion, observations_hash=_hash([item.model_dump() for item in payload.observations]),
        metrics=metrics, thresholds=thresholds, passed=not failures, failure_reasons=failures, created_by=principal.user.id)
    db.add(row); db.flush()
    db.add(AuditEvent(actor_id=principal.user.id, action="evaluation.run_completed", target_type="evaluation_run", target_id=str(row.id), event_data={"subjectId": row.subject_id, "workflow": row.workflow, "modality": row.modality, "environment": row.environment, "passed": row.passed, "model": row.candidate_model, "promptVersion": row.prompt_version}))
    db.commit(); db.refresh(row); return run_response(row)


def set_release(db: Session, principal: Principal, payload: ReleaseUpdate):
    run_row = db.get(EvaluationRun, payload.runId) if payload.runId else None
    if payload.mode == "automatic" and (not run_row or not run_row.passed or run_row.subject_id != payload.subjectId):
        raise DomainError("evaluation_release_blocked", "Automatic workflow requires a passing run for the same subject.", 409)
    if payload.workflow in TUTOR_RELEASE_MODALITY and payload.mode == "automatic":
        required_modality = TUTOR_RELEASE_MODALITY[payload.workflow]
        if run_row.workflow != "tutor" or run_row.modality != required_modality:
            raise DomainError("tutor_release_modality_mismatch", f"This feature requires a passing {required_modality} tutor run.", 409)
        if payload.audience == "students" and run_row.environment != "staging":
            raise DomainError("tutor_release_staging_required", "Student release requires a passing production-like staging run.", 409)
        existing = db.scalar(select(EvaluationRelease).where(
            EvaluationRelease.subject_id == payload.subjectId, EvaluationRelease.workflow == payload.workflow))
        stages = {"admin_testing": 0, "parent_pilot": 1, "students": 2}
        if (not existing and payload.audience != "admin_testing") or (existing and stages[payload.audience] > stages[existing.audience] + 1):
            raise DomainError("tutor_release_stage_invalid", "Release must progress through Admin testing, parent pilot and students.", 409)
    row = db.scalar(select(EvaluationRelease).where(EvaluationRelease.subject_id == payload.subjectId, EvaluationRelease.workflow == payload.workflow))
    if not row:
        row = EvaluationRelease(subject_id=payload.subjectId, workflow=payload.workflow, activated_by=principal.user.id)
        db.add(row)
    row.mode, row.run_id, row.confidence_threshold, row.audience = payload.mode, payload.runId, payload.confidenceThreshold, payload.audience
    row.activated_by, row.activated_at = principal.user.id, datetime.now(timezone.utc)
    db.add(AuditEvent(actor_id=principal.user.id, action="evaluation.release_updated", target_type="evaluation_release", target_id=f"{payload.subjectId}:{payload.workflow}", event_data={"mode": payload.mode, "audience": payload.audience, "runId": str(payload.runId) if payload.runId else None}))
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


def tutor_feature_allowed(db: Session, subject_id: str, workflow: str,
                          model: str | None = None, prompt_version: str | None = None) -> tuple[bool, str]:
    release = db.scalar(select(EvaluationRelease).where(
        EvaluationRelease.subject_id == subject_id, EvaluationRelease.workflow == workflow))
    if not release or release.mode != "automatic" or release.audience != "students" or not release.run_id:
        return False, f"{workflow} is not released to students. Use its kill switch or complete the staged release gates."
    run_row = db.get(EvaluationRun, release.run_id)
    if not run_row or not run_row.passed or run_row.workflow != "tutor" or run_row.environment != "staging":
        return False, "The tutor release no longer has a passing staging evaluation."
    if model and run_row.candidate_model != model:
        return False, "The active Tutor model differs from the passing staging release."
    if prompt_version and run_row.prompt_version != prompt_version:
        return False, "The active Tutor prompt differs from the passing staging release."
    corpus = db.get(EvaluationCorpus, run_row.corpus_id)
    if not corpus or corpus.status != "approved":
        return False, "The Tutor evaluation corpus is no longer approved."
    return True, ""
