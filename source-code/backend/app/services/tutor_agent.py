import json
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.base import AIProviderError, AIRequest, AIResult
from app.ai.prompts import get_tutor_prompt
from app.ai.router import AIAccountRouter
from app.config import Settings
from app.errors import DomainError
from app.models import AIInvocation, EducationalMedia, RetrievalChunk, TextbookUnit, TutorProfileVersion
from app.repositories import tutor_agent as repository
from app.schemas.tutor_agent import (
    TutorAgentTurnRequest, TutorAgentTurnResponse, TutorProviderOutput, TutorToolResult, TutorVisual,
)
from app.schemas.tutor_sources import TutorCitation
from app.security import Principal
from app.services import tutor_context, tutor_recommendations, tutor_sessions, tutor_sources
from app.services.assessment_access import TutorCapability, require_tutor_access


Generator = Callable[[AIRequest, uuid.UUID], AIResult]


def _invoke(db: Session, settings: Settings, principal: Principal, request: AIRequest,
            operation_id: uuid.UUID, generator: Generator | None) -> AIResult:
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
        invocation.status = "failed"; invocation.error_code = error.code
        invocation.latency_ms = round((time.monotonic() - started) * 1000)
        invocation.completed_at = datetime.now(timezone.utc); db.commit()
        raise DomainError(error.code, str(error), 503) from error
    invocation.status = "completed"; invocation.provider = result.provider; invocation.model = result.model
    invocation.response_id = result.response_id; invocation.latency_ms = result.latency_ms
    invocation.input_tokens = result.usage.input_tokens; invocation.output_tokens = result.usage.output_tokens
    invocation.total_tokens = result.usage.total_tokens; invocation.attempt_count = result.attempt_count
    invocation.completed_at = datetime.now(timezone.utc); db.commit()
    return result


def _media(db: Session, session) -> list[TutorVisual]:
    rows = db.scalars(select(EducationalMedia).where(
        EducationalMedia.status == "published", EducationalMedia.subject_id == session.subject_id,
        EducationalMedia.unit_id == session.active_unit_id,
    ).order_by(EducationalMedia.created_at.desc()).limit(3)).all()
    return [TutorVisual(title=row.title, altText=row.alt_text,
        contentUrl=f"/api/v1/tutoring/sessions/{session.public_ref}/media/{row.id}",
        sourceRefs=[str(item.get("chunkId")) for item in row.source_manifest if item.get("chunkId")]) for row in rows]


def _tools(db: Session, settings: Settings, principal: Principal, session, payload: TutorAgentTurnRequest,
           operation_id: uuid.UUID):
    from app.services import tutor_practice

    context = tutor_context.build_and_log(db, settings, principal, session.public_ref,
        f"agent-context-{operation_id.hex}")
    source_result = tutor_sources.search(db, settings, principal, session.public_ref,
        payload.message, None, 5)
    active = next(item for item in context.units if item.active)
    evidence_refs = [ref for statement in active.statements for ref in statement.evidenceRefs]
    practice = tutor_practice.current(db, settings, principal, session.public_ref)
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
        TutorToolResult(name="guided_practice", status="ready" if practice else ("ready" if payload.teachingMode in {"guided_practice", "socratic_practice", "questions"} else "unavailable"),
            summary=("Authoritative submitted assessment feedback is available." if practice and practice.feedbackVisible
                     else "An eligible practice question is active." if practice
                     else "Eligible practice can be started; marking remains with the assessment service." if payload.teachingMode in {"guided_practice", "socratic_practice", "questions"}
                     else "Guided practice was not requested."), evidenceRefs=practice_refs),
    ]
    if "what" in payload.message.lower() and ("next" in payload.message.lower() or "improve" in payload.message.lower()):
        recommendation = tutor_recommendations.recommend(db, settings, principal, session.public_ref,
            session.subject_id, f"agent-next-{operation_id.hex}")
        results.append(TutorToolResult(name="next_unit", status="ready" if recommendation.status == "ready" else "evidence_insufficient",
            summary=recommendation.message, evidenceRefs=[recommendation.contextOperationRef] if recommendation.contextOperationRef else []))
    else:
        recommendation = None
        results.append(TutorToolResult(name="next_unit", status="unavailable", summary="A next-unit recommendation was not requested."))
    visuals = _media(db, session)
    results.append(TutorToolResult(name="deterministic_media", status="ready" if visuals else "evidence_insufficient",
        summary=f"{len(visuals)} approved active-unit visual(s) available."))
    return context, source_result.citations, recommendation, results, visuals, practice


def _response(turn, stored: dict) -> TutorAgentTurnResponse:
    return TutorAgentTurnResponse.model_validate({**stored, "turnRef": turn.public_ref})


def complete_turn(db: Session, settings: Settings, principal: Principal, session_ref: str,
                  payload: TutorAgentTurnRequest, generator: Generator | None = None) -> TutorAgentTurnResponse:
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref, lock=True)
    tutor_sessions._require_active(session)
    existing = repository.replay(db, session.id, payload.requestKey)
    if existing:
        return _response(existing, existing.response_data)
    unit = db.get(TextbookUnit, session.active_unit_id)
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
        return _response(turn, stored)
    history = [{"role": row.role, "content": row.content[:1200]} for row in repository.recent(db, session.id)]
    prompt = get_tutor_prompt(payload.teachingMode)
    task_data = {
        "scope": {"course": "iGCSE", "subject": session.subject_id,
                  "activeUnit": {"code": unit.unit_code, "title": unit.title}},
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
                  "unit": unit.unit_code, "mode": payload.teachingMode})
    result = _invoke(db, settings, principal, request, operation_id, generator)
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
    repository.append_signals(db, session, turn, output.proposedSignals,
        result.provider, result.model, prompt.name, prompt.version)
    return _response(turn, stored)


def open_media(db: Session, settings: Settings, principal: Principal, storage, session_ref: str, media_id: uuid.UUID):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref)
    tutor_sessions._require_active(session)
    row = db.get(EducationalMedia, media_id)
    if not row or row.status != "published" or row.subject_id != session.subject_id or row.unit_id != session.active_unit_id:
        raise DomainError("tutor_media_not_found", "Tutor visual not found.", 404)
    return storage.get(row.object_key, row.content_type)
