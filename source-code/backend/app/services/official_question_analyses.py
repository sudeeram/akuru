"""Versioned source comparisons with separately audited confidence approval."""
import hashlib
import json
import uuid
from sqlalchemy import select, func
from pydantic import ValidationError
from app.errors import DomainError
from app.models import (
    AuditEvent, DocumentAsset, DocumentBlock, DocumentPage, DocumentVersion,
    OfficialPaperReviewQuestion, OfficialQuestionAnalysis,
)
from app.schemas.paper_analysis import AnalysisProvenance, QuestionAnalysisResponse, RecordQuestionAnalysis

ROLES = ("paper", "scheme", "report")


def source_manifest(db, workspace):
    result = []
    for role in ROLES:
        version_id = getattr(workspace, role + "_version_id")
        version = db.get(DocumentVersion, version_id) if version_id else None
        methods = sorted(set(db.scalars(select(DocumentPage.extraction_method).where(
            DocumentPage.document_version_id == version_id)))) if version else []
        result.append({"role": role, "documentVersionId": str(version.id) if version else None,
            "sha256": version.sha256 if version else None,
            "filename": version.original_filename if version else None,
            "version": version.version_number if version else None,
            "pageExtractionMethods": methods})
    return result


def content_hash(db, question, manifest, *, block_rows=None, asset_rows=None):
    data = json.loads(json.dumps(question.review_data))
    data.pop("extractionConfidence", None)
    for part in data.get("parts", []):
        for field in ("status", "coverage", "topicRefs", "textbookEvidence", "coverageReason",
                      "assessmentReadiness", "assessmentReadinessReason", "extractionConfidence"):
            part.pop(field, None)
    block_ids, asset_ids = set(), set()
    for scope in [data, *data.get("parts", [])]:
        asset_ids.update(scope.get("visualAssetIds", []))
        asset_ids.update(scope.get("candidateVisualAssetIds", []))
        asset_ids.update(visual["assetId"] for visual in scope.get("answerVisuals", []))
        for field in ("paperSources", "schemeSources", "reportSources"):
            for source in scope.get(field, []):
                if source.get("blockId"): block_ids.add(source["blockId"])
                if source.get("assetId"): asset_ids.add(source["assetId"])
    blocks = [{"id": str(block.id), "text": block.text, "latex": block.latex,
               "kind": block.block_kind, "bounds": block.bounding_box}
              for block in (block_rows if block_rows is not None else db.scalars(select(DocumentBlock).where(DocumentBlock.id.in_(
                  [uuid.UUID(value) for value in block_ids])).order_by(DocumentBlock.id))) if str(block.id) in block_ids] if block_ids else []
    assets = [{"id": str(asset.id), "sha256": asset.sha256, "bounds": asset.bounding_box,
               "metadata": asset.asset_metadata}
              for asset in (asset_rows if asset_rows is not None else db.scalars(select(DocumentAsset).where(DocumentAsset.id.in_(
                  [uuid.UUID(value) for value in asset_ids])).order_by(DocumentAsset.id))) if str(asset.id) in asset_ids] if asset_ids else []
    return hashlib.sha256(json.dumps({"question": data, "sources": manifest,
        "blocks": blocks, "assets": assets}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def response(row, digest):
    return QuestionAnalysisResponse(id=str(row.id), version=row.version_number, stage=row.stage,
        questionRevision=row.question_revision, contentHash=row.content_hash,
        sourceManifest=row.source_manifest, createdAt=row.created_at, isCurrent=row.content_hash == digest,
        **row.analysis_data)


def summaries(db, workspace, questions):
    if not questions: return {}
    manifest = source_manifest(db, workspace)
    history = db.scalars(select(OfficialQuestionAnalysis).where(
        OfficialQuestionAnalysis.question_id.in_([q.id for q in questions])).order_by(
        OfficialQuestionAnalysis.version_number.desc())).all()
    by_question = {}
    for row in history:
        by_question.setdefault(row.question_id, []).append(row)
    result = {}
    for question in questions:
        digest = content_hash(db, question, manifest)
        rows = by_question.get(question.id, [])
        accuracy = next((row for row in rows if row.stage == "accuracy"), None)
        extraction = next((row for row in rows if row.stage == "extraction"), None)
        result[question.id] = dict(analysisContentHash=digest, analysisVersion=rows[0].version_number if rows else 0,
            accuracyAnalysis=response(accuracy, digest) if accuracy else None,
            extractionAnalysis=response(extraction, digest) if extraction else None)
    return result


def _context(db, paper_id, number, *, lock=False):
    from .official_paper_reviews import _workspace, _validate_bound_versions
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    query = select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == workspace.id, OfficialPaperReviewQuestion.number == number)
    question = db.scalar(query.with_for_update() if lock else query)
    if not question: raise DomainError("question_not_found", "Question review not found.", 404)
    return workspace, question


def history(db, paper_id, number):
    workspace, question = _context(db, paper_id, number)
    digest = content_hash(db, question, source_manifest(db, workspace))
    return [response(row, digest) for row in db.scalars(select(OfficialQuestionAnalysis).where(
        OfficialQuestionAnalysis.question_id == question.id).order_by(OfficialQuestionAnalysis.version_number.desc()))]


def record(db, principal, paper_id, number, payload: RecordQuestionAnalysis, *, commit=True):
    workspace, question = _context(db, paper_id, number, lock=True)
    manifest = source_manifest(db, workspace)
    digest = content_hash(db, question, manifest)
    latest = db.scalar(select(func.max(OfficialQuestionAnalysis.version_number)).where(
        OfficialQuestionAnalysis.question_id == question.id)) or 0
    if (question.revision != payload.expectedQuestionRevision or digest != payload.expectedContentHash
            or latest != payload.expectedAnalysisVersion):
        raise DomainError("analysis_conflict", "The question, sources or analysis changed. Reload before recording an assessment.", 409)
    if {part.label for part in payload.parts} != {part["label"] for part in question.review_data.get("parts", [])}:
        raise DomainError("analysis_parts_mismatch", "Assess every current subpart exactly once.", 422)
    available = {source["role"]: source["documentVersionId"] for source in manifest}
    pages = {role: set(db.scalars(select(DocumentPage.page_number).where(
        DocumentPage.document_version_id == uuid.UUID(version_id)))) if version_id else set()
        for role, version_id in available.items()}
    for scope in [payload.question, *payload.parts]:
        for check in scope.sourceChecks:
            if (available[check.role] is None) != (check.status == "not_available"):
                raise DomainError("analysis_source_mismatch", "Record unavailable status only for an absent source.", 422)
            if not set(check.pages) <= pages[check.role]:
                raise DomainError("analysis_page_mismatch", "An inspected page does not belong to the bound source version.", 422)
    from .paper_curriculum import current as current_curriculum
    for assessed in payload.parts:
        if assessed.curriculum is not None:
            saved = next(p for p in question.review_data['parts'] if p['label'] == assessed.label)
            if not current_curriculum(db, saved, assessed.curriculum.model_dump(mode='json')):
                raise DomainError('curriculum_publication_changed', 'Curriculum evidence or mapping changed before recording the assessment.', 409)
    result = payload.model_dump(mode="json", exclude={"expectedQuestionRevision", "expectedAnalysisVersion", "expectedContentHash", "stage"})
    result["question"]["percent"] = min(payload.question.percent, *(part.percent for part in payload.parts))
    row = OfficialQuestionAnalysis(question_id=question.id, version_number=latest + 1, stage=payload.stage,
        question_revision=question.revision, content_hash=digest, source_manifest=manifest,
        analysis_data=result, created_by=principal.user.id)
    db.add(row)
    db.flush()
    db.add(AuditEvent(actor_id=principal.user.id, action="official_review.analysis_recorded",
        target_type="official_question_analysis", target_id=str(row.id),
        event_data={"questionId": str(question.id), "paperId": str(paper_id), "number": number,
                    "questionRevision": question.revision, "analysisVersion": row.version_number,
                    "stage": row.stage, "contentHash": digest}))
    if row.stage == "accuracy":
        from .question_auto_approval import apply
        apply(db, principal, workspace, question)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return response(row, digest)


def record_import(db, principal, workspace, question, supplied_provenance, question_provenance=None, part_provenance=None):
    """Keep native/OCR source methods distinct from optional AI interpretation."""
    manifest = source_manifest(db, workspace)
    by_role = {item.role: item for item in supplied_provenance}
    def overrides(values):
        if not isinstance(values, list) or len(values) > 3:
            raise DomainError("invalid_analysis_provenance", "Use at most three source-specific provenance records.", 422)
        try:
            parsed = [AnalysisProvenance.model_validate(value) for value in values]
        except ValidationError as exc:
            raise DomainError("invalid_analysis_provenance", "Check the source role, method and model provenance fields.", 422) from exc
        if len({value.role for value in parsed}) != len(parsed):
            raise DomainError("invalid_analysis_provenance", "Source provenance roles must be unique.", 422)
        return parsed
    by_role.update({item.role: item for item in overrides(question_provenance or [])})
    provenance = []
    for source in manifest:
        role = source["role"]
        provenance.append(by_role[role].model_dump(mode="json") if role in by_role else {
            "role": role, "method": "unknown", "provider": None, "modelId": None, "modelName": None,
            "responseId": None, "guidelineId": None, "guidelineVersion": None, "promptVersion": None,
            "processedAt": None, "notes": "Original interpretation/model identity was not supplied by the importer."})
    def scope(item):
        estimate = item.get("extractionConfidence") or {"percent": 0, "reasons": ["Import has no confidence estimate."]}
        return {"percent": estimate["percent"], "reasons": estimate["reasons"], "sourceChecks": [
            {"role": source["role"], "status": "not_checked" if source["documentVersionId"] else "not_available",
             "percent": None, "pages": [], "reasons": ["Import triage does not establish semantic accuracy or exact source association."]}
            for source in manifest]}
    data = {"methodVersion": "paper-extraction-triage-v1", "provenance": provenance,
            "question": scope(question.review_data), "parts": [dict(label=part["label"], **scope(part),
                provenance=[value.model_dump(mode="json") for value in overrides((part_provenance or {}).get(part["label"], []))])
                for part in question.review_data.get("parts", [])]}
    row = OfficialQuestionAnalysis(question_id=question.id, version_number=1, stage="extraction",
        question_revision=question.revision, content_hash=content_hash(db, question, manifest),
        source_manifest=manifest, analysis_data=data, created_by=principal.user.id)
    db.add(row)
