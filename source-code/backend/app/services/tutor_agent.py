import hashlib
import json
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.ai.base import AIProviderError, AIRequest, AIResult
from app.ai.prompts import get_tutor_prompt
from app.ai.router import AIAccountRouter
from app.config import Settings
from app.errors import DomainError
from app.models import AIInvocation, EducationalMedia, RetrievalChunk, TextbookGroup, TextbookTopic, TextbookUnit, TutorProfileVersion, TutorTurn
from app.repositories import tutor_agent as repository
from app.schemas.tutor_agent import (
    TutorAgentTurnRequest, TutorAgentTurnResponse, TutorProviderOutput, TutorToolResult, TutorVisual,
)
from app.schemas.tutor_sources import TutorCitation
from app.security import Principal
from app.services import tutor_context, tutor_history, tutor_quotas, tutor_recommendations, tutor_sessions, tutor_sources
from app.services.assessment_access import TutorCapability, require_tutor_access


Generator = Callable[[AIRequest, uuid.UUID], AIResult]


def _invoke(db: Session, settings: Settings, principal: Principal, request: AIRequest,
            operation_id: uuid.UUID, generator: Generator | None) -> AIResult:
    quota_operation = f"tutor_operation_{operation_id.hex}"
    estimated_tokens = min(settings.ai_max_input_characters + settings.ai_max_output_tokens,
                           max(500, len(request.instructions) + len(request.task) + settings.ai_max_output_tokens))
    tutor_quotas.reserve_text(db, principal.user.id, quota_operation, estimated_tokens)
    invocation = AIInvocation(actor_id=principal.user.id, provider="account-router", model="ordered-account",
        purpose="tutoring", prompt_name=request.prompt_name, prompt_version=request.prompt_version,
        schema_name=request.output_type.__name__, status="processing",
        request_metadata={"operationRef": f"tutor_operation_{operation_id.hex}", "sessionRef": request.metadata["session_ref"]})
    db.add(invocation); db.flush()
    started = time.monotonic()
    try:
        result = generator(request, operation_id) if generator else AIAccountRouter(db, settings).generate(
            request, operation_id=operation_id)
    except AIProviderError as error:
        tutor_quotas.release_text(db, principal.user.id, quota_operation, estimated_tokens, error.code)
        invocation.status = "failed"; invocation.error_code = error.code
        invocation.latency_ms = round((time.monotonic() - started) * 1000)
        invocation.completed_at = datetime.now(timezone.utc); db.commit()
        raise DomainError(error.code, str(error), 503) from error
    except Exception:
        tutor_quotas.release_text(db, principal.user.id, quota_operation, estimated_tokens, "unexpected_provider_error")
        invocation.status = "failed"; invocation.error_code = "unexpected_provider_error"
        invocation.latency_ms = round((time.monotonic() - started) * 1000)
        invocation.completed_at = datetime.now(timezone.utc); db.commit()
        raise
    invocation.status = "completed"; invocation.provider = result.provider; invocation.model = result.model
    invocation.response_id = result.response_id; invocation.latency_ms = result.latency_ms
    invocation.input_tokens = result.usage.input_tokens; invocation.output_tokens = result.usage.output_tokens
    invocation.total_tokens = result.usage.total_tokens; invocation.attempt_count = result.attempt_count
    actual_tokens = result.usage.total_tokens if result.usage.total_tokens is not None else estimated_tokens
    tutor_quotas.settle_text(db, principal.user.id, quota_operation, estimated_tokens, actual_tokens)
    invocation.completed_at = datetime.now(timezone.utc); db.commit()
    return result


VISUAL_TERMS = {
    "diagram", "draw", "figure", "graph", "plot", "chart", "image", "picture", "visual",
    "equation", "formula", "geometry", "triangle", "angle", "circuit", "force", "vector",
}


def _visual_requested(message: str) -> bool:
    words = {word.strip(".,?!:;()[]{}\"").lower() for word in message.split()}
    return bool(words & VISUAL_TERMS)


def _media(db: Session, settings: Settings, principal: Principal, session,
           citations: list[TutorCitation], requested: bool) -> list[TutorVisual]:
    if not requested:
        return []
    visuals = [TutorVisual(
        title=f"Official source · {citation.textbookTitle}, {citation.pageReference}",
        altText=citation.passage,
        visualType="official_source", kind=citation.contentKind,
        contentUrl=citation.assetUrl, readableFallback=citation.passage,
        equation=citation.passage if citation.contentKind == "equation" else None,
        sourceLabel=f"{citation.textbookTitle} · {citation.pageReference}",
        provenance={"origin": "official_textbook", "citationRef": citation.citationRef,
                    "assetRef": citation.assetRef, "documentVersion": citation.documentVersion,
                    "reviewState": "published"}, sourceRefs=[citation.citationRef],
    ) for citation in citations if citation.contentKind in {"image", "diagram", "equation"}]
    rows = db.scalars(select(EducationalMedia).where(
        EducationalMedia.status == "published", EducationalMedia.subject_id == session.subject_id,
        EducationalMedia.unit_id == session.active_unit_id,
        or_(EducationalMedia.provider == "akuru", EducationalMedia.reviewed_at.is_not(None)),
    ).order_by(EducationalMedia.created_at.desc()).limit(3)).all()
    for row in rows:
        citation_ref = f"citation_{row.source_chunk_id.hex}"
        try:
            source = tutor_sources.get_citation(db, settings, principal, session.public_ref, citation_ref)
        except DomainError:
            continue
        visuals.append(TutorVisual(title=row.title, altText=row.alt_text,
            visualType="explanatory", kind=row.kind,
            contentUrl=f"/api/v1/tutoring/sessions/{session.public_ref}/media/{row.id}",
            readableFallback=row.alt_text, sourceLabel=f"Based on {source.textbookTitle} · {source.pageReference}",
            provenance={"origin": "deterministic" if row.provider == "akuru" else "reviewed_generation",
                        "mediaId": str(row.id),
                        "promptDigest": hashlib.sha256(row.prompt.encode()).hexdigest(),
                        "promptVersion": row.prompt_version, "parameters": row.parameters,
                        "generator": row.provider, "model": row.model, "responseId": row.response_id,
                        "reviewState": row.status,
                        "reviewedAt": row.reviewed_at.isoformat() if row.reviewed_at else None,
                        "checksum": row.checksum}, sourceRefs=[source.citationRef]))
    return visuals[:4]


def _tools(db: Session, settings: Settings, principal: Principal, session, payload: TutorAgentTurnRequest,
           operation_id: uuid.UUID):
    from app.services import tutor_practice

    context = tutor_context.build_and_log(db, settings, principal, session.public_ref,
        f"agent-context-{operation_id.hex}")
    source_result = tutor_sources.search(db, settings, principal, session.public_ref,
        payload.message, None, 5)
    active = next(item for item in (context.topics if session.active_topic_id else context.units) if item.active)
    evidence_refs = [ref for statement in active.statements for ref in statement.evidenceRefs]
    try:
        practice = tutor_practice.current(db, settings, principal, session.public_ref)
        practice_allowed = True
    except DomainError as error:
        if error.code != "tutor_release_blocked": raise
        practice, practice_allowed = None, False
    practice_refs = ([f"assessment_result:{practice.question.result.id}"]
                     if practice and practice.question.result else [])
    results = [
        TutorToolResult(name="learner_context", status="ready", summary="Verified learner context loaded.", evidenceRefs=evidence_refs),
        TutorToolResult(name="mastery_summary", status="ready" if active.masteryScore is not None else "evidence_insufficient",
            summary=f"Verified mastery is {active.masteryScore:.1f}/10." if active.masteryScore is not None else "No verified mastery score is available.", evidenceRefs=evidence_refs),
        TutorToolResult(name="study_plan_context", status="ready" if active.studyPlan else "evidence_insufficient",
            summary=f"{len(active.studyPlan)} approved active-unit study-plan item(s).",
            evidenceRefs=[item.evidenceRef for item in active.studyPlan]),
        TutorToolResult(name="approved_source_search", status="ready" if source_result.status == "exact" else "evidence_insufficient",
            summary=source_result.message, evidenceRefs=[item.citationRef for item in source_result.citations]),
        TutorToolResult(name="authorized_source_opening", status="ready" if source_result.citations else "evidence_insufficient",
            summary="Private source links were authorized for this session." if source_result.citations else "No source was authorized.",
            evidenceRefs=[item.citationRef for item in source_result.citations]),
        TutorToolResult(name="guided_practice", status="ready" if practice else ("ready" if practice_allowed and payload.teachingMode in {"guided_practice", "socratic_practice", "questions"} else "unavailable"),
            summary=("Authoritative submitted assessment feedback is available." if practice and practice.feedbackVisible
                     else "An eligible practice question is active." if practice
                     else "Eligible practice can be started; marking remains with the assessment service." if practice_allowed and payload.teachingMode in {"guided_practice", "socratic_practice", "questions"}
                     else "Guided practice is not released for this subject." if not practice_allowed
                     else "Guided practice was not requested."), evidenceRefs=practice_refs),
    ]
    if "what" in payload.message.lower() and ("next" in payload.message.lower() or "improve" in payload.message.lower()):
        try:
            recommendation = tutor_recommendations.recommend(db, settings, principal, session.public_ref,
                session.subject_id, f"agent-next-{operation_id.hex}")
            results.append(TutorToolResult(name="next_unit", status="ready" if recommendation.status == "ready" else "evidence_insufficient",
                summary=recommendation.message, evidenceRefs=[recommendation.contextOperationRef] if recommendation.contextOperationRef else []))
        except DomainError as error:
            if error.code != "tutor_release_blocked": raise
            recommendation = None
            results.append(TutorToolResult(name="next_unit", status="unavailable",
                summary="The next-unit tool is not released for this subject."))
    else:
        recommendation = None
        results.append(TutorToolResult(name="next_unit", status="unavailable", summary="A next-unit recommendation was not requested."))
    visual_allowed = True
    if settings.tutor_release_gates_required:
        from app.services.evaluations import tutor_feature_allowed
        visual_allowed, _ = tutor_feature_allowed(db, session.subject_id, "tutor_visuals")
    visuals = _media(db, settings, principal, session, source_result.citations,
                     visual_allowed and _visual_requested(payload.message))
    results.append(TutorToolResult(name="deterministic_media", status="ready" if visuals else "evidence_insufficient",
        summary=(f"{len(visuals)} authorized active-unit visual aid(s) available. Official source visuals and "
                 "explanatory media remain separately labelled." if visuals else
                 "No visual was requested or no authorized active-unit visual is available."),
        evidenceRefs=[ref for visual in visuals for ref in visual.sourceRefs]))
    return context, source_result.citations, recommendation, results, visuals, practice


def _response(turn, stored: dict) -> TutorAgentTurnResponse:
    return TutorAgentTurnResponse.model_validate({**stored, "turnRef": turn.public_ref})


def _record_safety(db: Session, session, assistant_turn) -> None:
    student_turn = db.scalar(select(TutorTurn).where(
        TutorTurn.session_id == session.id, TutorTurn.operation_id == assistant_turn.operation_id,
        TutorTurn.role == "student"))
    if student_turn:
        tutor_history.detect_safety(db, session, student_turn); db.commit()


def complete_turn(db: Session, settings: Settings, principal: Principal, session_ref: str,
                  payload: TutorAgentTurnRequest, generator: Generator | None = None) -> TutorAgentTurnResponse:
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref, lock=True)
    tutor_sessions._require_active(session)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT,
                         session.subject_id, "tutor_text")
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_tools")
    existing = repository.replay(db, session.id, payload.requestKey)
    if existing:
        return _response(existing, existing.response_data)
    unit = db.get(TextbookUnit, session.active_unit_id) if session.active_unit_id else None
    topic = db.get(TextbookTopic, session.active_topic_id) if session.active_topic_id else None
    group = db.get(TextbookGroup, topic.group_id) if topic else None
    profile = db.get(TutorProfileVersion, session.current_profile_version_id)
    operation_id = uuid.uuid4()
    context, citations, recommendation, tool_results, visuals, practice = _tools(
        db, settings, principal, session, payload, operation_id)
    if not citations and not (recommendation and recommendation.status == "ready") and payload.teachingMode != "exam_technique":
        stored = TutorAgentTurnResponse(operationRef=f"tutor_operation_{operation_id.hex}", turnRef="pending",
            content="I could not find enough approved evidence in this unit to explain that reliably. Try rephrasing the question or ask your administrator to review the textbook extraction.",
            teachingMode=payload.teachingMode, citations=[],
            followUpChoices=["Can you help me rephrase my question?"], toolResults=tool_results,
            visuals=visuals, proposedSignals=[], provider="akuru", model="evidence-gate-v1",
            promptName="tutor-evidence-gate", promptVersion="1.0.0").model_dump(mode="json")
        turn = repository.save_exchange(db, session, payload.message.strip(), payload.requestKey, stored,
            [], operation_id, "akuru", "evidence-gate-v1", "tutor-evidence-gate", "1.0.0")
        _record_safety(db, session, turn)
        return _response(turn, stored)
    history = [{"role": row.role, "content": row.content[:1200]} for row in repository.recent(db, session.id)]
    prompt = get_tutor_prompt(payload.teachingMode)
    task_data = {
        "scope": {"course": "iGCSE", "subject": session.subject_id,
                  **({"activeUnit": {"code": unit.unit_code, "title": unit.title}} if unit else {}),
                  **({"activeTopic": {"code": topic.code, "title": topic.title,
                      "groupCode": group.code, "groupTitle": group.title}} if topic else {})},
        "tutorProfile": {"name": profile.name, "tone": profile.tone, "friendliness": profile.friendliness,
                         "enthusiasm": profile.enthusiasm, "speed": profile.speed,
                         "communicationCharacter": profile.communication_character,
                         "explanationDepth": profile.explanation_depth, "teachingStyle": profile.teaching_style},
        "learnerContext": context.providerContext.model_dump(mode="json"),
        "approvedCitations": [item.model_dump(mode="json") for item in citations],
        "nextUnitRecommendation": recommendation.model_dump(mode="json") if recommendation else None,
        "guidedPractice": practice.model_dump(mode="json") if practice else None,
        "toolResults": [item.model_dump(mode="json") for item in tool_results],
        "recentTranscript": history,
        "currentTurnEvidenceRef": "turn:current",
        "learnerMessage": payload.message,
    }
    request = AIRequest(purpose="tutoring", prompt_name=prompt.name, prompt_version=prompt.version,
        instructions=prompt.instructions, task=json.dumps(task_data, ensure_ascii=False),
        output_type=TutorProviderOutput,
        metadata={"session_ref": session.public_ref, "subject": session.subject_id,
                  "unit": unit.unit_code if unit else None, "topic": topic.code if topic else None,
                  "mode": payload.teachingMode})
    result = _invoke(db, settings, principal, request, operation_id, generator)
    if settings.tutor_release_gates_required:
        from app.services.evaluations import tutor_feature_allowed
        allowed, reason = tutor_feature_allowed(db, session.subject_id, "tutor_text",
                                                result.model, prompt.version)
        if not allowed:
            raise DomainError("tutor_release_blocked", reason, 403)
    output = TutorProviderOutput.model_validate(result.output)
    allowed = {item.citationRef: item for item in citations}
    if any(ref not in allowed for ref in output.citationRefs):
        raise DomainError("tutor_output_invalid", "The Tutor returned an unauthorized or invented citation.", 502)
    validated_citations: list[TutorCitation] = [tutor_sources.get_citation(
        db, settings, principal, session_ref, ref) for ref in output.citationRefs]
    known_evidence = ({item.ref for item in context.evidence} | set(allowed) | {"turn:current"} |
                      {ref for item in tool_results for ref in item.evidenceRefs})
    if any(ref not in known_evidence for signal in output.proposedSignals for ref in signal.evidenceRefs):
        raise DomainError("tutor_output_invalid", "The Tutor returned an unsupported learner signal.", 502)
    stored = TutorAgentTurnResponse(operationRef=f"tutor_operation_{operation_id.hex}", turnRef="pending",
        content=output.content, teachingMode=payload.teachingMode, citations=validated_citations,
        followUpChoices=output.followUpChoices, toolResults=tool_results, visuals=visuals,
        proposedSignals=output.proposedSignals, provider=result.provider, model=result.model,
        promptName=prompt.name, promptVersion=prompt.version).model_dump(mode="json")
    source_ids = [uuid.UUID(hex=ref.removeprefix("citation_")) for ref in output.citationRefs]
    turn = repository.save_exchange(db, session, payload.message.strip(), payload.requestKey, stored,
        source_ids, operation_id, result.provider, result.model, prompt.name, prompt.version)
    _record_safety(db, session, turn)
    repository.append_signals(db, session, turn, output.proposedSignals,
        result.provider, result.model, prompt.name, prompt.version)
    return _response(turn, stored)


def open_media(db: Session, settings: Settings, principal: Principal, storage, session_ref: str, media_id: uuid.UUID):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref)
    tutor_sessions._require_active(session)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_visuals")
    row = db.get(EducationalMedia, media_id)
    if not row or row.status != "published" or row.subject_id != session.subject_id or row.unit_id != session.active_unit_id:
        raise DomainError("tutor_media_not_found", "Tutor visual not found.", 404)
    return storage.get(row.object_key, row.content_type)
