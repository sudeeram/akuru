import re
import uuid
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import AIRequest
from app.ai.base import AIProviderError
from app.ai.prompts import get_prompt
from app.ai.router import AIAccountRouter
from app.config import Settings
from app.errors import DomainError
from app.models import (
    AIProviderAccount, AuditEvent, Document, OfficialMaterialVersion,
    OfficialQuestionUnitMapping, OfficialQuestionVersion, TextbookContentVersion,
    TextbookUnit, TextbookUnitVersion,
)
from app.schemas.question_mappings import (
    AIUnitSuggestionOutput, MappingSuggestionResponse, PaperMappingResponse,
    QuestionMappingResponse, SaveUnitMappingsRequest, UnitMapping, UnitOption,
)
from app.security import Principal


TOKEN_RE = re.compile(r"[a-z][a-z0-9-]{2,}", re.I)
STOP = {"the", "and", "for", "with", "from", "that", "this", "describe", "explain", "state", "give", "calculate"}


def _paper(db: Session, paper_id: uuid.UUID):
    material = db.scalar(select(OfficialMaterialVersion).where(
        OfficialMaterialVersion.document_id == paper_id,
        OfficialMaterialVersion.kind == "past_paper",
        OfficialMaterialVersion.status == "published",
    ).order_by(OfficialMaterialVersion.version_number.desc()))
    if not material or not material.textbook_content_version_id:
        raise DomainError("published_paper_required", "Publish the reviewed paper with its approved textbook first.", 409)
    document = db.get(Document, paper_id)
    textbook_version = db.get(TextbookContentVersion, material.textbook_content_version_id)
    textbook = db.get(Document, textbook_version.document_id)
    return material, document, textbook_version, textbook


def _units(db: Session, material: OfficialMaterialVersion):
    return db.scalars(select(TextbookUnit).where(
        TextbookUnit.content_version_id == material.textbook_content_version_id,
        TextbookUnit.course_id == material.course_id,
        TextbookUnit.subject_id == material.subject_id,
    ).order_by(TextbookUnit.sequence)).all()


def _question(db: Session, question_id: uuid.UUID):
    question = db.get(OfficialQuestionVersion, question_id)
    if not question:
        raise DomainError("question_not_found", "Published question not found.", 404)
    material = db.get(OfficialMaterialVersion, question.material_version_id)
    if not material or material.status != "published" or material.kind != "past_paper":
        raise DomainError("published_question_required", "Only a published paper question can be mapped.", 409)
    return question, material


def _mapping_rows(db: Session, question_id: uuid.UUID):
    return db.scalars(select(OfficialQuestionUnitMapping).where(
        OfficialQuestionUnitMapping.question_version_id == question_id
    ).order_by(OfficialQuestionUnitMapping.weight.desc())).all()


def paper_mappings(db: Session, paper_id: uuid.UUID) -> PaperMappingResponse:
    material, paper, textbook_version, textbook = _paper(db, paper_id)
    units = _units(db, material)
    questions = db.scalars(select(OfficialQuestionVersion).where(
        OfficialQuestionVersion.material_version_id == material.id
    ).order_by(OfficialQuestionVersion.question_number)).all()
    return PaperMappingResponse(
        paperId=str(paper.id), paperTitle=paper.title, subjectId=material.subject_id,
        textbookTitle=textbook.title, textbookEdition=textbook_version.edition,
        units=[UnitOption(id=str(unit.id), code=unit.unit_code, title=unit.title) for unit in units],
        questions=[QuestionMappingResponse(
            questionId=str(question.id), number=question.question_number, prompt=question.prompt,
            marks=question.marks, status=question.mapping_status,
            mappings=[UnitMapping(unitId=row.unit_id, weight=row.weight, rationale=row.rationale, confidence=row.confidence, method=row.suggestion_method) for row in _mapping_rows(db, question.id)],
        ) for question in questions],
    )


def _unit_text(db: Session, unit: TextbookUnit) -> str:
    version = db.scalar(select(TextbookUnitVersion).where(
        TextbookUnitVersion.content_version_id == unit.content_version_id,
        TextbookUnitVersion.unit_code == unit.unit_code,
    ))
    if not version:
        return f"{unit.unit_code} {unit.title}"
    return " ".join([unit.unit_code, unit.title, version.summary, *version.sections, *version.concepts, *version.definitions])


def _tokens(value: str):
    return Counter(token.lower() for token in TOKEN_RE.findall(value) if token.lower() not in STOP)


def _metadata_suggestions(db: Session, question: OfficialQuestionVersion, units: list[TextbookUnit]):
    question_tokens = _tokens(f"{question.shared_stem} {question.prompt}")
    scored = []
    for unit in units:
        unit_tokens = _tokens(_unit_text(db, unit))
        score = sum(min(count, unit_tokens[token]) for token, count in question_tokens.items())
        if score:
            scored.append((unit, score))
    if not scored:
        scored = [(units[0], 1)] if units else []
    scored.sort(key=lambda row: (-row[1], row[0].sequence))
    selected = scored[:3]
    total = sum(score for _, score in selected)
    weights = [round(score * 100 / total) for _, score in selected]
    if weights:
        weights[0] += 100 - sum(weights)
    return [UnitMapping(unitId=unit.id, weight=weight, confidence=min(0.95, 0.45 + score / 10), rationale=f"Metadata overlap with {unit.unit_code} · {unit.title}.", method="metadata") for (unit, score), weight in zip(selected, weights)]


def suggest(db: Session, settings: Settings, question_id: uuid.UUID) -> MappingSuggestionResponse:
    question, material = _question(db, question_id)
    units = _units(db, material)
    if not units:
        raise DomainError("approved_units_required", "The paper's approved textbook has no available units.", 409)
    metadata = _metadata_suggestions(db, question, units)
    configured = db.scalars(select(AIProviderAccount).where(AIProviderAccount.enabled.is_(True)).order_by(AIProviderAccount.priority)).all()
    if not any(settings.openai_account_key(row.credential_alias) for row in configured):
        return MappingSuggestionResponse(questionId=str(question.id), method="metadata", suggestions=metadata)
    prompt = get_prompt("unit_mapping")
    task = "Question:\n" + question.prompt + "\n\nAllowed approved units:\n" + "\n".join(f"{unit.unit_code}: {_unit_text(db, unit)}" for unit in units)
    try:
        result = AIAccountRouter(db, settings).generate(AIRequest(
            purpose=prompt.purpose, prompt_name=prompt.name, prompt_version=prompt.version,
            instructions=prompt.instructions, task=task, output_type=AIUnitSuggestionOutput,
            metadata={"question_version_id": str(question.id), "subject_id": material.subject_id},
        ))
    except AIProviderError:
        return MappingSuggestionResponse(questionId=str(question.id), method="metadata", suggestions=metadata)
    by_code = {unit.unit_code.lower(): unit for unit in units}
    suggestions = []
    for row in result.output.mappings:
        unit = by_code.get(row.unitCode.lower())
        if not unit:
            raise DomainError("invalid_ai_unit_mapping", "AI suggested a unit outside the approved textbook.", 422)
        suggestions.append(UnitMapping(unitId=unit.id, weight=row.weight, confidence=row.confidence, rationale=row.rationale, method="openai"))
    if len({row.unitId for row in suggestions}) != len(suggestions):
        raise DomainError("invalid_ai_unit_mapping", "AI suggested a duplicate unit.", 422)
    return MappingSuggestionResponse(questionId=str(question.id), method="openai", suggestions=suggestions)


def save(db: Session, principal: Principal, question_id: uuid.UUID, payload: SaveUnitMappingsRequest):
    question, material = _question(db, question_id)
    if question.mapping_status == "confirmed":
        raise DomainError("mapping_already_confirmed", "Confirmed mappings are immutable; create a corrected question version.", 409)
    allowed = {unit.id for unit in _units(db, material)}
    if any(row.unitId not in allowed for row in payload.mappings):
        raise DomainError("foreign_unit_mapping", "Every mapped unit must belong to this paper's approved course, subject and textbook edition.", 422)
    db.execute(delete(OfficialQuestionUnitMapping).where(OfficialQuestionUnitMapping.question_version_id == question.id))
    for row in payload.mappings:
        db.add(OfficialQuestionUnitMapping(question_version_id=question.id, unit_id=row.unitId, weight=row.weight, status="draft", suggestion_method=row.method, confidence=row.confidence, rationale=row.rationale))
    question.mapping_status = "draft"
    db.add(AuditEvent(actor_id=principal.user.id, action="question_mapping.saved", target_type="official_question_version", target_id=str(question.id), event_data={"unitCount": len(payload.mappings)}))
    db.commit()
    return next(row for row in paper_mappings(db, material.document_id).questions if row.questionId == str(question.id))


def publish(db: Session, principal: Principal, question_id: uuid.UUID):
    question, material = _question(db, question_id)
    if question.mapping_status != "draft":
        raise DomainError("mapping_draft_required", "Save a mapping draft before confirmation.", 409)
    rows = _mapping_rows(db, question.id)
    if not rows or sum(row.weight for row in rows) != 100:
        raise DomainError("invalid_mapping_weights", "Confirmed mappings require at least one unit and exactly 100% total weight.", 409)
    allowed = {unit.id for unit in _units(db, material)}
    if any(row.unit_id not in allowed for row in rows):
        raise DomainError("foreign_unit_mapping", "A mapping no longer belongs to this paper's approved textbook.", 409)
    now = datetime.now(timezone.utc)
    for row in rows:
        row.status = "confirmed"; row.confirmed_by = principal.user.id; row.confirmed_at = now
    question.mapping_status = "confirmed"
    db.add(AuditEvent(actor_id=principal.user.id, action="question_mapping.confirmed", target_type="official_question_version", target_id=str(question.id), event_data={"weights": {str(row.unit_id): row.weight for row in rows}}))
    db.commit()
    return next(row for row in paper_mappings(db, material.document_id).questions if row.questionId == str(question.id))
