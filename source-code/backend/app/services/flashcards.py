import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (
    Document, DocumentBlock, DocumentPage, FlashcardDeck, FlashcardReview, FlashcardSession,
    FlashcardVersion, RetrievalChunk, TextbookGroup, TextbookTopic, TextbookTopicContentVersion,
    TopicRetrievalPreflight,
)
from app.schemas.flashcards import FlashcardCardResponse, FlashcardDeckResponse, FlashcardSessionResponse
from app.security import Principal
from app.services.curriculum_plans import student_coverage


PROMPT_VERSION = "grounded-flashcards-v1"
SCHEDULER_VERSION = "akuru-spaced-review-v1"
INTERVALS = {"again": 0, "difficult": 1, "good": 3, "easy": 7}


def _latest_cards(db: Session, deck_id) -> list[FlashcardVersion]:
    rows = db.scalars(select(FlashcardVersion).where(
        FlashcardVersion.deck_id == deck_id).order_by(
        FlashcardVersion.ordinal, FlashcardVersion.version_number.desc())).all()
    latest = {}
    for row in rows:
        latest.setdefault(row.ordinal, row)
    return list(latest.values())


def _source(db: Session, chunk: RetrievalChunk, student_id=None) -> dict:
    document = db.get(Document, chunk.document_id)
    block = db.get(DocumentBlock, chunk.source_item_id)
    page = db.get(DocumentPage, block.page_id) if block else None
    return {
        "chunkRef": str(chunk.id), "documentTitle": document.title if document else "Textbook",
        "page": chunk.page_number, "printedPage": page.printed_page_label if page else None,
        "passage": chunk.content,
        "sourceUrl": (f"/api/v1/retrieval/evidence/{chunk.id}?studentId={student_id}"
                      if student_id else None),
    }


def _card_out(db: Session, card: FlashcardVersion, *, reveal=False, student_id=None):
    chunk = db.get(RetrievalChunk, card.source_chunk_id)
    snapshot = dict(card.source_snapshot or {})
    if chunk and student_id:
        snapshot.update(_source(db, chunk, student_id))
    return FlashcardCardResponse(cardRef=card.public_ref, ordinal=card.ordinal,
        version=card.version_number, front=card.front, back=card.back if reveal else None,
        status=card.status, warnings=card.validation_warnings or [], source=snapshot)


def _deck_out(db: Session, deck: FlashcardDeck, *, include_cards=True, reveal=True,
              student_id=None) -> FlashcardDeckResponse:
    topic = db.get(TextbookTopic, deck.topic_id); group = db.get(TextbookGroup, topic.group_id)
    version = db.get(TextbookTopicContentVersion, deck.content_version_id)
    cards = _latest_cards(db, deck.id)
    counts = {key: sum(row.status == key for row in cards)
              for key in ("approved", "review_required", "rejected")}
    return FlashcardDeckResponse(deckRef=deck.public_ref, topicRef=topic.public_ref,
        topicCode=topic.code, topicTitle=topic.title, groupCode=group.code, groupTitle=group.title,
        subjectId=topic.subject_id, title=deck.title, status=deck.status,
        contentVersion=version.version_number, cardCount=len(cards),
        approvedCount=counts["approved"], reviewRequiredCount=counts["review_required"],
        rejectedCount=counts["rejected"],
        cards=[_card_out(db, row, reveal=reveal, student_id=student_id) for row in cards]
              if include_cards else [],
        releasedAt=deck.released_at.isoformat() if deck.released_at else None)


def _question(content: str, topic_title: str) -> tuple[str, str, list[str]]:
    clean = " ".join(content.split())
    sentence = re.split(r"(?<=[.!?])\s+", clean)[0][:1200]
    match = re.match(r"^(.{2,90}?)\s+(?:is|are|means|refers to)\s+(.+)$", sentence, re.I)
    if match:
        return f"What is {match.group(1).strip(' :;,')}?", sentence, []
    match = re.match(r"^(.{2,90}?):\s+(.+)$", sentence)
    if match:
        return f"What should you know about {match.group(1).strip()}?", sentence, []
    return f"Explain this key idea from {topic_title}: {sentence[:100].rstrip('.,;:')}…", sentence, ["Review the automatically drafted question wording."]


def generate(db: Session, principal: Principal, topic_ref: str, card_limit: int, request_key: str):
    existing = db.scalar(select(FlashcardDeck).where(FlashcardDeck.generation_key == request_key))
    if existing:
        return _deck_out(db, existing)
    topic = db.scalar(select(TextbookTopic).where(TextbookTopic.public_ref == topic_ref))
    if not topic or topic.status != "published":
        raise DomainError("published_topic_required", "Publish the textbook topic before creating flashcards.", 409)
    version = db.scalar(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == topic.id,
        TextbookTopicContentVersion.status == "published").order_by(
        TextbookTopicContentVersion.version_number.desc()))
    if not version:
        raise DomainError("published_topic_content_required", "Publish reviewed topic content before creating flashcards.", 409)
    preflight = db.scalar(select(TopicRetrievalPreflight).where(
        TopicRetrievalPreflight.topic_id == topic.id,
        TopicRetrievalPreflight.content_version_id == version.id,
        TopicRetrievalPreflight.passed.is_(True)).order_by(TopicRetrievalPreflight.created_at.desc()))
    if not preflight:
        raise DomainError("retrieval_preflight_required", "Run and pass the topic retrieval preflight before creating flashcards.", 409)
    chunks = db.scalars(select(RetrievalChunk).where(
        RetrievalChunk.topic_id == topic.id,
        RetrievalChunk.topic_content_version_id == version.id,
        RetrievalChunk.source_type == "textbook_section", RetrievalChunk.status == "active"
    ).order_by(RetrievalChunk.page_number, RetrievalChunk.source_ordinal).limit(card_limit * 3)).all()
    unique = []
    seen = set()
    for chunk in chunks:
        normalized = " ".join(chunk.content.lower().split())
        if len(normalized) >= 24 and normalized not in seen:
            seen.add(normalized); unique.append(chunk)
        if len(unique) >= card_limit: break
    if len(unique) < 3:
        raise DomainError("insufficient_flashcard_evidence", "At least three distinct reviewed textbook passages are required.", 409)
    deck = FlashcardDeck(topic_id=topic.id, content_version_id=version.id,
        title=f"{topic.title} flashcards", status="review", card_limit=card_limit,
        generation_key=request_key, created_by=principal.user.id,
        generation_metadata={"generator": "deterministic_grounded_draft", "promptVersion": PROMPT_VERSION,
                             "preflightRef": preflight.public_ref, "sourceCount": len(unique)})
    db.add(deck); db.flush()
    fronts = set()
    for ordinal, chunk in enumerate(unique, 1):
        front, back, warnings = _question(chunk.content, topic.title)
        normalized_front = front.casefold()
        if normalized_front in fronts: warnings.append("This question is similar to another card.")
        fronts.add(normalized_front)
        db.add(FlashcardVersion(deck_id=deck.id, ordinal=ordinal, version_number=1,
            front=front, back=back, source_chunk_id=chunk.id, source_snapshot=_source(db, chunk),
            status="review_required", validation_warnings=warnings, provider="akuru",
            model="grounded-draft-v1", prompt_version=PROMPT_VERSION, created_by=principal.user.id))
    db.commit(); db.refresh(deck)
    return _deck_out(db, deck)


def admin_list(db: Session):
    return [_deck_out(db, row, include_cards=False) for row in db.scalars(
        select(FlashcardDeck).order_by(FlashcardDeck.created_at.desc())).all()]


def admin_get(db: Session, deck_ref: str):
    deck = db.scalar(select(FlashcardDeck).where(FlashcardDeck.public_ref == deck_ref))
    if not deck: raise DomainError("flashcard_deck_not_found", "Flashcard deck not found.", 404)
    return _deck_out(db, deck)


def review_card(db: Session, principal: Principal, deck_ref: str, card_ref: str,
                front: str, back: str, decision: str):
    deck = db.scalar(select(FlashcardDeck).where(FlashcardDeck.public_ref == deck_ref))
    current = db.scalar(select(FlashcardVersion).where(
        FlashcardVersion.public_ref == card_ref, FlashcardVersion.deck_id == (deck.id if deck else None)))
    if not deck or not current: raise DomainError("flashcard_not_found", "Flashcard not found.", 404)
    latest = next((row for row in _latest_cards(db, deck.id) if row.ordinal == current.ordinal), None)
    if not latest or latest.id != current.id:
        raise DomainError("stale_flashcard_version", "This card was already changed. Reload the deck.", 409)
    if deck.status in ("released", "superseded"):
        raise DomainError("released_deck_immutable", "Released flashcards cannot be edited. Create a new deck.", 409)
    current.status = "superseded"
    warnings = []
    if len(front) > 240: warnings.append("Consider shortening the question for easier reading.")
    replacement = FlashcardVersion(deck_id=deck.id, ordinal=current.ordinal,
        version_number=current.version_number + 1, front=front, back=back,
        source_chunk_id=current.source_chunk_id, source_snapshot=current.source_snapshot,
        status=decision, validation_warnings=warnings, provider=current.provider, model=current.model,
        prompt_version=current.prompt_version, created_by=principal.user.id)
    db.add(replacement); db.commit(); db.refresh(replacement)
    return _deck_out(db, deck)


def release(db: Session, principal: Principal, deck_ref: str):
    deck = db.scalar(select(FlashcardDeck).where(FlashcardDeck.public_ref == deck_ref))
    if not deck: raise DomainError("flashcard_deck_not_found", "Flashcard deck not found.", 404)
    if deck.status == "released": return _deck_out(db, deck)
    cards = _latest_cards(db, deck.id)
    if len(cards) < 3 or any(card.status != "approved" for card in cards):
        raise DomainError("flashcard_review_incomplete", "Approve every card before releasing this deck.", 409)
    valid_chunks = set(db.scalars(select(RetrievalChunk.id).where(
        RetrievalChunk.topic_content_version_id == deck.content_version_id,
        RetrievalChunk.status == "active")).all())
    if any(card.source_chunk_id not in valid_chunks for card in cards):
        raise DomainError("flashcard_source_changed", "A source is no longer part of the published topic version. Generate a new deck.", 409)
    preflight = db.scalar(select(TopicRetrievalPreflight).where(
        TopicRetrievalPreflight.topic_id == deck.topic_id,
        TopicRetrievalPreflight.content_version_id == deck.content_version_id,
    ).order_by(TopicRetrievalPreflight.created_at.desc()))
    if not preflight or not preflight.passed:
        raise DomainError("retrieval_preflight_required", "The current topic version needs a passing retrieval preflight.", 409)
    now = datetime.now(timezone.utc)
    for prior in db.scalars(select(FlashcardDeck).where(
        FlashcardDeck.topic_id == deck.topic_id, FlashcardDeck.status == "released",
        FlashcardDeck.id != deck.id)).all():
        prior.status = "superseded"; prior.superseded_at = now
    deck.status = "released"; deck.released_by = principal.user.id; deck.released_at = now
    db.commit(); db.refresh(deck)
    return _deck_out(db, deck)


def student_decks(db: Session, principal: Principal):
    coverage_by_subject = {}
    rows = []
    for deck in db.scalars(select(FlashcardDeck).where(
        FlashcardDeck.status == "released").order_by(FlashcardDeck.released_at.desc())).all():
        topic = db.get(TextbookTopic, deck.topic_id)
        if topic.subject_id not in coverage_by_subject:
            coverage = student_coverage(db, principal.user.id, topic.subject_id)
            coverage_by_subject[topic.subject_id] = ({row.topicRef for row in coverage.coveredTopics}
                if coverage.status == "ready" else set())
        if topic.public_ref in coverage_by_subject[topic.subject_id]:
            rows.append(_deck_out(db, deck, include_cards=False, student_id=principal.user.id))
    return rows


def _owned_session(db: Session, principal: Principal, session_ref: str):
    row = db.scalar(select(FlashcardSession).where(
        FlashcardSession.public_ref == session_ref, FlashcardSession.student_id == principal.user.id))
    if not row: raise DomainError("flashcard_session_not_found", "Flashcard session not found.", 404)
    return row


def _session_out(db: Session, session: FlashcardSession, reveal=False, message="Ready to study."):
    deck = db.get(FlashcardDeck, session.deck_id); cards = [c for c in _latest_cards(db, deck.id) if c.status == "approved"]
    reviews = db.scalars(select(FlashcardReview).where(FlashcardReview.session_id == session.id)).all()
    current = next((c for c in cards if c.ordinal == session.current_ordinal), None) if session.status == "active" else None
    return FlashcardSessionResponse(sessionRef=session.public_ref,
        deck=_deck_out(db, deck, include_cards=False, student_id=session.student_id), status=session.status,
        currentOrdinal=session.current_ordinal, reviewedCount=len(reviews), totalCards=len(cards),
        currentCard=_card_out(db, current, reveal=reveal, student_id=session.student_id) if current else None,
        answerRevealed=reveal, schedulerVersion=session.scheduler_version, message=message)


def start_session(db: Session, principal: Principal, deck_ref: str, request_key: str):
    existing = db.scalar(select(FlashcardSession).where(FlashcardSession.request_key == request_key))
    if existing:
        if existing.student_id != principal.user.id: raise DomainError("request_key_conflict", "Request key is already in use.", 409)
        return _session_out(db, existing)
    allowed = {row.deckRef for row in student_decks(db, principal)}
    if deck_ref not in allowed: raise DomainError("flashcard_deck_not_available", "This deck is not available in your current learning coverage.", 403)
    deck = db.scalar(select(FlashcardDeck).where(FlashcardDeck.public_ref == deck_ref))
    active = db.scalar(select(FlashcardSession).where(FlashcardSession.student_id == principal.user.id,
        FlashcardSession.deck_id == deck.id, FlashcardSession.status == "active"))
    if active: return _session_out(db, active, message="Your earlier session is ready to continue.")
    first = min(row.ordinal for row in _latest_cards(db, deck.id) if row.status == "approved")
    session = FlashcardSession(student_id=principal.user.id, deck_id=deck.id, current_ordinal=first,
        scheduler_version=SCHEDULER_VERSION, request_key=request_key)
    db.add(session); db.commit(); db.refresh(session)
    return _session_out(db, session)


def get_session(db: Session, principal: Principal, session_ref: str, reveal=False):
    return _session_out(db, _owned_session(db, principal, session_ref), reveal=reveal)


def rate(db: Session, principal: Principal, session_ref: str, rating: str, request_key: str):
    session = _owned_session(db, principal, session_ref)
    existing = db.scalar(select(FlashcardReview).where(FlashcardReview.request_key == request_key))
    if existing:
        if existing.session_id != session.id:
            raise DomainError("request_key_conflict", "Request key is already in use.", 409)
        return _session_out(db, session, message="That rating was already saved.")
    if session.status != "active": raise DomainError("flashcard_session_complete", "This session is already complete.", 409)
    deck = db.get(FlashcardDeck, session.deck_id); cards = [c for c in _latest_cards(db, deck.id) if c.status == "approved"]
    current = next((c for c in cards if c.ordinal == session.current_ordinal), None)
    if not current: raise DomainError("flashcard_not_found", "The current flashcard is unavailable.", 409)
    interval = INTERVALS[rating]
    db.add(FlashcardReview(session_id=session.id, card_version_id=current.id, rating=rating,
        interval_days=interval, due_at=datetime.now(timezone.utc) + timedelta(days=interval), request_key=request_key))
    following = next((c for c in cards if c.ordinal > current.ordinal), None)
    if following: session.current_ordinal = following.ordinal; message = "Rating saved. Here is the next card."
    else:
        session.status = "completed"; session.completed_at = datetime.now(timezone.utc)
        message = "You completed this flashcard session. Well done."
    db.commit(); return _session_out(db, session, message=message)
