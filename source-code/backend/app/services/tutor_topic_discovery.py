"""Deterministic concept location, restricted to eligible published tutor topics.

Discovery does not broaden ordinary source retrieval or authorise cross-topic assets.
"""
import re
import uuid

from types import SimpleNamespace

from sqlalchemy import select

from app.errors import DomainError
from app.models import Document, DocumentBlock, DocumentPage, RetrievalChunk, TextbookTopic
from app.schemas.tutor_agent import TutorAgentTurnResponse, TutorTopicMatch
from app.services import tutor_sessions, tutor_sources
from app.services.assessment_access import TutorCapability, require_tutor_access
from app.repositories import tutor_agent as repository


_LOCATION = re.compile(
    r'\b(?:which|what)\s+(?:(?:textbook|biology|chemistry|school)\s+)?(?:topic|topics|unit|units|chapter|chapters)\b'
    r'|\bwhere\s+(?:can\s+i\s+(?:find|learn|study)|(?:is|are|do|does|would|should).{0,60}(?:cover|taught|belong|learn|find|fit))'
    r'|\b(?:find|locate|identify)\b.{0,60}\b(?:topic|topics|chapter|chapters)\b', re.I)
_NOISE = set('learnt learned learning covered cover covers taught belong belongs fit fits locate find identify could would studied study read chapter chapters topics units books book biology chemistry physics english french science syllabus curriculum tell think remember recently already today yesterday'.split())


def concept_terms(message):
    aliases = {'viruses': 'virus', 'viral': 'virus', 'bacteria': 'bacterium', 'bacterial': 'bacterium'}
    return {aliases.get(term, term) for term in tutor_sources._terms(message)} - _NOISE


def requested(message):
    return bool(_LOCATION.search(message))


def rank_records(query, records):
    """Require substantive lexical evidence; never guess a topic from model knowledge."""
    wanted = concept_terms(query)
    if not wanted:
        return []
    matches = []
    for chunk, block, page in records:
        if block.block_kind in {'question', 'subpart', 'answer_space', 'image', 'diagram'}:
            continue
        text = re.split(r'\bCHAPTER QUESTIONS\b', chunk.content, flags=re.I)[0]
        terms = concept_terms(text)
        if not wanted <= terms:
            continue
        occurrences = [concept_terms(word) for word in text.split()]
        score = sum(min(sum(term in tokens for tokens in occurrences), 5) for term in wanted)
        score += 3 if wanted <= concept_terms(text.split('\n')[0]) else 0
        matches.append((score, chunk, page))
    return sorted(matches, key=lambda item: (-item[0], item[1].page_number, item[1].source_ordinal))


def evidence_excerpt(text, query):
    # Centre long passages on the actual match, rather than an unrelated page introduction.
    wanted = concept_terms(query)
    offset = next((match.start() for match in re.finditer(r'[^\W_]+', text)
                   if concept_terms(match.group()) & wanted), 0)
    start = max(0, offset - 100)
    return ('…' if start else '') + text[start:start + 600] + ('…' if start + 600 < len(text) else '')


def handle(db, settings, principal, session, payload):
    if not requested(payload.message):
        return None
    # Validate the active session/coverage as well as each potential destination.
    tutor_sources._session(db, settings, principal, session.public_ref)
    choices = tutor_sessions.options(db, principal.user.id, settings)
    subject = next((s for s in choices.subjects if s.id == session.subject_id), None)
    matches = []
    for item in subject.topics if subject else []:
        topic = db.scalar(select(TextbookTopic).where(TextbookTopic.public_ref == item.topicRef,
            TextbookTopic.subject_id == session.subject_id, TextbookTopic.status == 'published'))
        if not topic:
            continue
        try:
            require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                session.subject_id, 'tutor_sources', topic_id=topic.id)
        except DomainError as error:
            if error.status_code not in {403, 409}:
                raise
            continue
        # Reuse book/publication checks without changing the actual session topic.
        _, version, book = tutor_sources._active_chunks(db, SimpleNamespace(active_topic_id=topic.id))
        if not version or not book:
            continue
        records = db.execute(select(RetrievalChunk, DocumentBlock, DocumentPage).join(
            DocumentBlock, DocumentBlock.id == RetrievalChunk.source_item_id).join(
            Document, Document.id == RetrievalChunk.document_id).join(DocumentPage,
                (DocumentPage.document_version_id == RetrievalChunk.document_version_id) &
                (DocumentPage.page_number == RetrievalChunk.page_number)).where(
            RetrievalChunk.topic_id == topic.id, RetrievalChunk.topic_content_version_id == version.id,
            RetrievalChunk.status == 'active', RetrievalChunk.source_type == 'textbook_section',
            DocumentBlock.needs_review.is_(False), Document.review_state == 'published',
            Document.removed_at.is_(None))).all()
        ranked = rank_records(payload.message, records)
        if not ranked:
            continue
        score, chunk, page = ranked[0]
        label = page.printed_page_label or page.page_metadata.get('printedPageLabel')
        matches.append((score, TutorTopicMatch(topicRef=topic.public_ref, topicCode=topic.code,
            topicTitle=topic.title, groupCode=item.groupCode, groupTitle=item.groupTitle,
            textbookTitle=book.title, contentVersion=version.version_number,
            pageReference=f'Page {label}' if label else f'PDF page {page.page_number}',
            excerpt=evidence_excerpt(chunk.content, payload.message), active=topic.id == session.active_topic_id)))
    matches.sort(key=lambda item: (-item[0], item[1].topicCode, item[1].topicRef))
    selected = [item for _, item in matches[:5]]
    content = ('I found the following published topics in your subject. The strongest text match is listed first; other matches may be related applications.\n\n' +
        '\n\n'.join(f'{m.groupCode} · {m.groupTitle} → {m.topicCode} · {m.topicTitle}\n{m.textbookTitle} · {m.pageReference}' for m in selected)
        if selected else 'I could not locate that concept in your accessible, published topics. Please name the concept more precisely. This does not mean it is absent from the whole syllabus.')
    operation_id = uuid.uuid4()
    stored = TutorAgentTurnResponse(operationRef=f'tutor_operation_{operation_id.hex}', turnRef='pending',
        content=content, teachingMode=payload.teachingMode, topicMatches=selected,
        provider='akuru', model='topic-discovery-v1', promptName='topic-discovery', promptVersion='1.0.0',
        retrievalProvenance={'strategy': 'authorized_published_topic_lookup',
            'topicRefs': [m.topicRef for m in selected]}).model_dump(mode='json')
    turn = repository.save_exchange(db, session, payload.message.strip(), payload.requestKey, stored,
        [], operation_id, 'akuru', 'topic-discovery-v1', 'topic-discovery', '1.0.0')
    return TutorAgentTurnResponse.model_validate({**stored, 'turnRef': turn.public_ref})
