import re
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.errors import DomainError
from app.models import (AuditEvent, Document, OfficialMaterialVersion, OfficialQuestionTopicMapping,
    OfficialQuestionVersion, Textbook, TextbookGroup, TextbookTopic, TextbookTopicContentVersion)
from app.schemas.question_mappings import (SaveTopicMappingsRequest, TopicGroupOption, TopicMapping,
    TopicMappingSuggestionResponse, TopicOption, TopicPaperMappingResponse, TopicQuestionMappingResponse)
from app.security import Principal

TOKEN_RE = re.compile(r"[a-z][a-z0-9-]{2,}", re.I)
STOP = {"the", "and", "for", "with", "from", "that", "this", "describe", "explain", "state", "give", "calculate"}

def _paper(db: Session, paper_id: uuid.UUID):
    material = db.scalar(select(OfficialMaterialVersion).where(OfficialMaterialVersion.document_id == paper_id,
        OfficialMaterialVersion.kind == "past_paper", OfficialMaterialVersion.status == "published").order_by(OfficialMaterialVersion.version_number.desc()))
    if not material: raise DomainError("published_paper_required", "Publish the reviewed past paper first.", 409)
    book = db.get(Textbook, material.textbook_id) if material.textbook_id else db.scalar(select(Textbook).where(
        Textbook.course_id == material.course_id, Textbook.subject_id == material.subject_id,
        Textbook.status == "published").order_by(Textbook.published_at.desc()))
    if not book: raise DomainError("topic_textbook_required", "Link the paper to the active published subject textbook edition.", 409)
    if book.course_id != material.course_id or book.subject_id != material.subject_id or book.status != "published":
        raise DomainError("paper_textbook_scope_mismatch", "The paper and textbook must have the same course and subject.", 409)
    return material, db.get(Document, paper_id), book

def _question(db, question_id):
    question = db.get(OfficialQuestionVersion, question_id)
    if not question: raise DomainError("question_not_found", "Published question not found.", 404)
    material = db.get(OfficialMaterialVersion, question.material_version_id)
    if not material or material.kind != "past_paper" or material.status != "published":
        raise DomainError("published_question_required", "Only a published past-paper question can be mapped.", 409)
    _, _, book = _paper(db, material.document_id)
    return question, material, book

def _inventory(db, book):
    content = select(TextbookTopicContentVersion.topic_id).where(TextbookTopicContentVersion.status == "published")
    groups = db.scalars(select(TextbookGroup).where(TextbookGroup.textbook_id == book.id, TextbookGroup.status == "published").order_by(TextbookGroup.sequence)).all()
    topics = db.scalars(select(TextbookTopic).where(TextbookTopic.textbook_id == book.id,
        TextbookTopic.status == "published", TextbookTopic.id.in_(content)).order_by(TextbookTopic.sequence)).all()
    return groups, topics

def _rows(db, question_id):
    return db.scalars(select(OfficialQuestionTopicMapping).where(
        OfficialQuestionTopicMapping.question_version_id == question_id).order_by(OfficialQuestionTopicMapping.weight.desc())).all()

def _topic_option(topic, group):
    return TopicOption(topicRef=topic.public_ref, code=topic.code, title=topic.title,
        groupRef=group.public_ref, groupCode=group.code, groupTitle=group.title)

def _question_response(db, question, topics, groups):
    by_id, by_group = {t.id:t for t in topics}, {g.id:g for g in groups}; mappings=[]; aggregate=defaultdict(int)
    for row in _rows(db, question.id):
        topic = by_id.get(row.topic_id)
        if not topic: continue
        mappings.append(TopicMapping(topicRef=topic.public_ref, weight=row.weight, required=row.required,
            rationale=row.rationale, confidence=row.confidence, method=row.suggestion_method))
        aggregate[by_group[topic.group_id].code] += row.weight
    return TopicQuestionMappingResponse(questionId=str(question.id), number=question.question_number,
        prompt=question.prompt, sharedStem=question.shared_stem, marks=question.marks, status=question.mapping_status,
        sourceLocations=question.source_locations, mappings=mappings, groupWeights=dict(aggregate))

def paper_mappings(db: Session, paper_id: uuid.UUID):
    material, paper, book = _paper(db, paper_id); groups, topics = _inventory(db, book); by_group={g.id:g for g in groups}
    questions = db.scalars(select(OfficialQuestionVersion).where(OfficialQuestionVersion.material_version_id == material.id).order_by(OfficialQuestionVersion.question_number)).all()
    return TopicPaperMappingResponse(paperId=str(paper.id), paperTitle=paper.title, subjectId=material.subject_id,
        textbookTitle=book.title, textbookEdition=book.edition, groupLabel=book.group_label,
        groups=[TopicGroupOption(groupRef=g.public_ref, code=g.code, title=g.title,
            topics=[_topic_option(t,g) for t in topics if t.group_id == g.id]) for g in groups],
        questions=[_question_response(db,q,topics,groups) for q in questions],
        confirmedQuestionCount=sum(q.mapping_status == "confirmed" for q in questions), totalQuestionCount=len(questions))

def _tokens(value): return Counter(x.lower() for x in TOKEN_RE.findall(value) if x.lower() not in STOP)

def suggest(db: Session, question_id: uuid.UUID):
    question, _, book = _question(db, question_id); groups, topics = _inventory(db, book)
    if not topics: raise DomainError("published_topics_required", "Publish reviewed topics before mapping questions.", 409)
    question_tokens=_tokens(f"{question.shared_stem} {question.prompt}"); scored=[]
    for topic in topics:
        score=sum(min(n, _tokens(f"{topic.code} {topic.title} {topic.description} {topic.syllabus_ref}")[token]) for token,n in question_tokens.items())
        if score: scored.append((topic,score))
    if not scored: scored=[(topics[0],1)]
    selected=sorted(scored,key=lambda x:(-x[1],x[0].sequence))[:4]; total=sum(x[1] for x in selected)
    weights=[round(score*100/total) for _,score in selected]; weights[0]+=100-sum(weights)
    return TopicMappingSuggestionResponse(questionId=str(question.id), method="metadata", suggestions=[
        TopicMapping(topicRef=t.public_ref, weight=w, required=True, confidence=min(.95,.45+s/10),
                     rationale=f"Question evidence overlaps {t.code} · {t.title}.", method="metadata")
        for (t,s),w in zip(selected,weights)])

def save(db: Session, principal: Principal, question_id: uuid.UUID, payload: SaveTopicMappingsRequest):
    question, material, book = _question(db, question_id)
    if question.mapping_status == "confirmed": raise DomainError("mapping_already_confirmed", "Confirmed mappings are immutable; create a corrected question version.", 409)
    groups, topics = _inventory(db, book); allowed={t.public_ref:t for t in topics}
    if any(row.topicRef not in allowed for row in payload.mappings):
        raise DomainError("foreign_topic_mapping", "Every topic must be published in this paper's approved subject and textbook edition.", 422)
    db.execute(delete(OfficialQuestionTopicMapping).where(OfficialQuestionTopicMapping.question_version_id == question.id))
    for row in payload.mappings:
        db.add(OfficialQuestionTopicMapping(question_version_id=question.id, topic_id=allowed[row.topicRef].id,
            weight=row.weight, required=row.required, status="draft", suggestion_method=row.method,
            confidence=row.confidence, rationale=row.rationale))
    question.mapping_status="draft"
    db.add(AuditEvent(actor_id=principal.user.id, action="question_topic_mapping.saved",
        target_type="official_question_version", target_id=str(question.id),
        event_data={"topicRefs":[r.topicRef for r in payload.mappings],"requiredTopicCount":sum(r.required for r in payload.mappings)}))
    db.commit(); return _question_response(db,question,topics,groups)

def publish(db: Session, principal: Principal, question_id: uuid.UUID):
    question, material, book = _question(db, question_id)
    if question.mapping_status != "draft": raise DomainError("mapping_draft_required", "Save a topic mapping draft before confirmation.", 409)
    groups, topics = _inventory(db, book); allowed={t.id for t in topics}; rows=_rows(db,question.id)
    if not rows or sum(r.weight for r in rows)!=100 or not any(r.required for r in rows):
        raise DomainError("invalid_mapping_weights", "Confirmed mappings need 100% total weight and at least one required topic.", 409)
    if any(r.topic_id not in allowed for r in rows): raise DomainError("foreign_topic_mapping", "A topic is no longer published in the approved textbook.", 409)
    now=datetime.now(timezone.utc)
    for row in rows: row.status="confirmed"; row.confirmed_by=principal.user.id; row.confirmed_at=now
    question.mapping_status="confirmed"
    db.add(AuditEvent(actor_id=principal.user.id, action="question_topic_mapping.confirmed",
        target_type="official_question_version", target_id=str(question.id),
        event_data={"topics":[{"topicRef":next(t.public_ref for t in topics if t.id==r.topic_id),"weight":r.weight,"required":r.required} for r in rows]}))
    db.commit(); return _question_response(db,question,topics,groups)
