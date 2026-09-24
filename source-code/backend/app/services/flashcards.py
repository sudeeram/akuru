import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (
    AuditEvent, Document, DocumentBlock, DocumentPage, FlashcardDeck, FlashcardLearningState,
    FlashcardReview, FlashcardSession, FlashcardVersion, RetrievalChunk, TextbookGroup,
    TextbookTopic, TextbookTopicContentVersion, TopicRetrievalPreflight, WeaknessDiagnosis,
)
from app.schemas.flashcards import (FlashcardCardResponse, FlashcardDeckResponse, FlashcardSessionResponse,
    FlashcardStudyOption, FlashcardStudyOptionsResponse)
from app.security import Principal
from app.services.curriculum_plans import student_coverage


PROMPT_VERSION = "grounded-flashcards-v1"
SCHEDULER_VERSION = "akuru-spaced-review-v1"
INTERVALS = {"again": 0, "difficult": 1, "good": 3, "easy": 7}
SELECTION_VERSION = "akuru-adaptive-selection-v1"


def _selection_reason(state, weak_topic: bool, now: datetime) -> tuple[int, str]:
    if state and state.due_at <= now: return 0, "overdue"
    if state and state.last_rating in ("again", "difficult"): return 1, "difficult"
    if weak_topic: return 2, "weak_topic"
    if not state: return 3, "unseen"
    if state.repetitions < 2: return 4, "learning"
    return 5, "mastered_variation"


def _schedule(state, rating: str, now: datetime) -> datetime:
    if rating == "again":
        state.repetitions = 0; state.lapses += 1; state.interval_days = 0
        due = now + timedelta(minutes=10)
    elif rating == "difficult":
        state.repetitions += 1; state.ease_factor = max(1.3, state.ease_factor - .15)
        state.interval_days = max(1, round(max(1, state.interval_days) * 1.2)); due = now + timedelta(days=state.interval_days)
    elif rating == "good":
        state.repetitions += 1
        state.interval_days = 1 if state.repetitions == 1 else (3 if state.repetitions == 2 else max(4, round(state.interval_days * state.ease_factor)))
        due = now + timedelta(days=state.interval_days)
    else:
        state.repetitions += 1; state.ease_factor = min(3.0, state.ease_factor + .15)
        state.interval_days = 4 if state.repetitions == 1 else max(7, round(max(1, state.interval_days) * state.ease_factor))
        due = now + timedelta(days=state.interval_days)
    state.last_rating, state.due_at, state.last_reviewed_at = rating, due, now
    return due


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
        status=card.status, warnings=card.validation_warnings or [], source=snapshot,
        conceptKey=card.concept_key, category=card.category, variationType=card.variation_type,
        difficulty=card.difficulty)


def _deck_out(db: Session, deck: FlashcardDeck, *, include_cards=True, reveal=True,
              student_id=None) -> FlashcardDeckResponse:
    topic = db.get(TextbookTopic, deck.topic_id); group = db.get(TextbookGroup, topic.group_id)
    version = db.get(TextbookTopicContentVersion, deck.content_version_id)
    cards = _latest_cards(db, deck.id)
    counts = {key: sum(row.status == key for row in cards)
              for key in ("approved", "review_required", "rejected")}
    validation_summary = dict(deck.generation_metadata.get("validationSummary", {}))
    active_sources = set(db.scalars(select(RetrievalChunk.id).where(
        RetrievalChunk.topic_content_version_id == deck.content_version_id,
        RetrievalChunk.status == "active")).all())
    validation_summary["sourceHealth"] = ("current" if version.status == "published" and
        all(card.source_chunk_id in active_sources for card in cards) else "stale")
    return FlashcardDeckResponse(deckRef=deck.public_ref, topicRef=topic.public_ref,
        topicCode=topic.code, topicTitle=topic.title, groupCode=group.code, groupTitle=group.title,
        subjectId=topic.subject_id, title=deck.title, status=deck.status,
        contentVersion=version.version_number, cardCount=len(cards),
        approvedCount=counts["approved"], reviewRequiredCount=counts["review_required"],
        rejectedCount=counts["rejected"],
        cards=[_card_out(db, row, reveal=reveal, student_id=student_id) for row in cards]
              if include_cards else [],
        releasedAt=deck.released_at.isoformat() if deck.released_at else None,
        releaseId=deck.generation_metadata.get("releaseId"),
        artifactChecksum=deck.generation_metadata.get("artifactChecksum"),
        validationStatus=deck.generation_metadata.get("validation"),
        categoryDistribution=deck.generation_metadata.get("categoryDistribution", {}),
        validationSummary=validation_summary)


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
            model="grounded-draft-v1", prompt_version=PROMPT_VERSION,
            external_key=f"legacy-{ordinal}", concept_key=f"legacy-{ordinal}", created_by=principal.user.id))
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
        prompt_version=current.prompt_version, external_key=current.external_key,
        concept_key=current.concept_key, category=current.category, variation_type=current.variation_type,
        difficulty=current.difficulty, card_metadata=current.card_metadata,
        visual_asset_id=current.visual_asset_id, created_by=principal.user.id)
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
        version = db.get(TextbookTopicContentVersion, deck.content_version_id)
        if not topic or topic.status != "published" or not version or version.status != "published":
            continue
        if topic.subject_id not in coverage_by_subject:
            coverage = student_coverage(db, principal.user.id, topic.subject_id)
            coverage_by_subject[topic.subject_id] = ({row.topicRef for row in coverage.coveredTopics}
                if coverage.status == "ready" else set())
        if topic.public_ref in coverage_by_subject[topic.subject_id]:
            rows.append(_deck_out(db, deck, include_cards=False, student_id=principal.user.id))
    return rows


def _eligible_deck_models(db: Session, principal: Principal) -> list[FlashcardDeck]:
    refs = {row.deckRef for row in student_decks(db, principal)}
    return db.scalars(select(FlashcardDeck).where(FlashcardDeck.public_ref.in_(refs))).all() if refs else []


def _cards_for_decks(db: Session, decks: list[FlashcardDeck]) -> list[FlashcardVersion]:
    cards = []
    for deck in decks:
        cards.extend(card for card in _latest_cards(db, deck.id) if card.status == "approved")
    return cards


def _state_map(db: Session, student_id, cards: list[FlashcardVersion]):
    ids = [card.id for card in cards]
    return {row.card_version_id: row for row in db.scalars(select(FlashcardLearningState).where(
        FlashcardLearningState.student_id == student_id, FlashcardLearningState.card_version_id.in_(ids))).all()} if ids else {}


def _weak_topic_ids(db: Session, student_id):
    return set(db.scalars(select(WeaknessDiagnosis.topic_id).where(
        WeaknessDiagnosis.student_id == student_id, WeaknessDiagnosis.severity.in_(("moderate", "major")))).all())


def study_options(db: Session, principal: Principal, deck_ref: str):
    decks = _eligible_deck_models(db, principal)
    deck = next((row for row in decks if row.public_ref == deck_ref), None)
    if not deck:
        raise DomainError("flashcard_deck_not_available", "This deck is not available in your current learning coverage.", 403)
    topic = db.get(TextbookTopic, deck.topic_id)
    group_decks = [row for row in decks if db.get(TextbookTopic, row.topic_id).group_id == topic.group_id]
    cards, unit_cards = _cards_for_decks(db, [deck]), _cards_for_decks(db, group_decks)
    states = _state_map(db, principal.user.id, unit_cards)
    now = datetime.now(timezone.utc)
    difficult = [c for c in cards if (states.get(c.id) and states[c.id].last_rating in ("again", "difficult"))]
    due = [c for c in cards if states.get(c.id) and states[c.id].due_at <= now]
    specs = [
        ("quick", "Quick review", "A focused 10-card review.", len(cards), min(10, len(cards))),
        ("normal", "Normal review", "A balanced 20-card review.", len(cards), min(20, len(cards))),
        ("full_topic", "Full topic practice", "Review every card in this topic.", len(cards), len(cards)),
        ("difficult", "Difficult cards", "Revisit cards rated Again or Difficult.", len(difficult), len(difficult)),
        ("due_today", "Due today", "Review cards due from your learning schedule.", len(due), len(due)),
        ("unit_mixed", "Unit mixed practice", "Mix eligible cards across published topics in this unit.", len(unit_cards), min(20, len(unit_cards))),
    ]
    unseen = sum(card.id not in states for card in cards)
    learning = sum(bool(states.get(card.id) and states[card.id].repetitions < 2) for card in cards)
    return FlashcardStudyOptionsResponse(deckRef=deck_ref, options=[FlashcardStudyOption(
        mode=mode, title=title, description=description, availableCount=count,
        sessionSize=size, enabled=count > 0) for mode, title, description, count, size in specs],
        summary={"due": len(due), "difficult": len(difficult), "new": unseen, "learning": learning})


def _select_cards(db: Session, principal: Principal, deck: FlashcardDeck, mode: str):
    eligible = _eligible_deck_models(db, principal)
    topic = db.get(TextbookTopic, deck.topic_id)
    decks = ([row for row in eligible if db.get(TextbookTopic, row.topic_id).group_id == topic.group_id]
             if mode == "unit_mixed" else [deck])
    cards = _cards_for_decks(db, decks)
    states = _state_map(db, principal.user.id, cards)
    weak_topics = _weak_topic_ids(db, principal.user.id)
    now = datetime.now(timezone.utc)
    ranked = []
    for card in cards:
        state = states.get(card.id)
        card_deck = db.get(FlashcardDeck, card.deck_id)
        rank, reason = _selection_reason(state, card_deck.topic_id in weak_topics, now)
        if mode == "difficult" and reason not in ("overdue", "difficult"): continue
        if mode == "due_today" and not (state and state.due_at <= now): continue
        ranked.append((rank, state.due_at if state else now, card.concept_key, card.ordinal, card, reason))
    ranked.sort(key=lambda row: (row[0], row[1], row[2], row[3]))
    limit = {"quick": 10, "normal": 20, "unit_mixed": 20}.get(mode, len(ranked))
    selected, deferred, previous, per_concept = [], [], None, {}
    for row in ranked:
        if row[2] == previous or (mode in ("quick", "normal", "unit_mixed") and per_concept.get(row[2], 0) >= 2):
            deferred.append(row); continue
        selected.append(row); previous = row[2]
        per_concept[row[2]] = per_concept.get(row[2], 0) + 1
        if len(selected) >= limit: break
    if len(selected) < limit:
        selected.extend(deferred[:limit - len(selected)])
    return [(row[4], row[5]) for row in selected]


def _owned_session(db: Session, principal: Principal, session_ref: str):
    row = db.scalar(select(FlashcardSession).where(
        FlashcardSession.public_ref == session_ref, FlashcardSession.student_id == principal.user.id))
    if not row: raise DomainError("flashcard_session_not_found", "Flashcard session not found.", 404)
    return row


def _session_out(db: Session, session: FlashcardSession, reveal=False, message="Ready to study."):
    deck = db.get(FlashcardDeck, session.deck_id)
    reviews = db.scalars(select(FlashcardReview).where(FlashcardReview.session_id == session.id)).all()
    ids = [str(value) for value in session.selected_card_version_ids]
    current = None
    if session.status == "active" and session.current_ordinal <= len(ids):
        current = db.get(FlashcardVersion, uuid.UUID(ids[session.current_ordinal - 1]))
    return FlashcardSessionResponse(sessionRef=session.public_ref,
        deck=_deck_out(db, deck, include_cards=False, student_id=session.student_id), status=session.status,
        currentOrdinal=session.current_ordinal, reviewedCount=len(reviews), totalCards=len(ids),
        currentCard=_card_out(db, current, reveal=reveal, student_id=session.student_id) if current else None,
        answerRevealed=reveal, schedulerVersion=session.scheduler_version, message=message,
        mode=session.mode, selectionReasons=session.selection_reasons)


def start_session(db: Session, principal: Principal, deck_ref: str, request_key: str, mode: str = "normal"):
    existing = db.scalar(select(FlashcardSession).where(FlashcardSession.request_key == request_key))
    if existing:
        if existing.student_id != principal.user.id: raise DomainError("request_key_conflict", "Request key is already in use.", 409)
        return _session_out(db, existing)
    allowed = {row.deckRef for row in student_decks(db, principal)}
    if deck_ref not in allowed: raise DomainError("flashcard_deck_not_available", "This deck is not available in your current learning coverage.", 403)
    deck = db.scalar(select(FlashcardDeck).where(FlashcardDeck.public_ref == deck_ref))
    active = db.scalar(select(FlashcardSession).where(FlashcardSession.student_id == principal.user.id,
        FlashcardSession.deck_id == deck.id, FlashcardSession.mode == mode, FlashcardSession.status == "active"))
    if active: return _session_out(db, active, message="Your earlier session is ready to continue.")
    selected = _select_cards(db, principal, deck, mode)
    if not selected:
        raise DomainError("flashcard_mode_empty", "No cards are currently available for this study mode.", 409)
    session = FlashcardSession(student_id=principal.user.id, deck_id=deck.id, current_ordinal=1,
        scheduler_version=SCHEDULER_VERSION, request_key=request_key, mode=mode,
        target_count=len(selected), selected_card_version_ids=[str(card.id) for card, _ in selected],
        selection_reasons=[reason for _, reason in selected])
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
    ids = [str(value) for value in session.selected_card_version_ids]
    current = db.get(FlashcardVersion, uuid.UUID(ids[session.current_ordinal - 1])) if session.current_ordinal <= len(ids) else None
    if not current: raise DomainError("flashcard_not_found", "The current flashcard is unavailable.", 409)
    now = datetime.now(timezone.utc)
    state = db.scalar(select(FlashcardLearningState).where(
        FlashcardLearningState.student_id == principal.user.id,
        FlashcardLearningState.card_version_id == current.id).with_for_update())
    if not state:
        state = FlashcardLearningState(student_id=principal.user.id, card_version_id=current.id,
            concept_key=current.concept_key, due_at=now)
        db.add(state); db.flush()
    due = _schedule(state, rating, now)
    interval = state.interval_days
    db.add(FlashcardReview(session_id=session.id, card_version_id=current.id, rating=rating,
        interval_days=interval, due_at=due, request_key=request_key))
    if session.current_ordinal < len(ids): session.current_ordinal += 1; message = "Rating saved. Here is the next card."
    else:
        session.status = "completed"; session.completed_at = now
        message = "You completed this flashcard session. Well done."
    db.commit(); return _session_out(db, session, message=message)


def withdraw(db: Session, principal: Principal, deck_ref: str, reason: str):
    deck = db.scalar(select(FlashcardDeck).where(FlashcardDeck.public_ref == deck_ref))
    if not deck:
        raise DomainError("flashcard_deck_not_found", "Flashcard deck not found.", 404)
    if deck.status != "released":
        raise DomainError("flashcard_deck_not_released", "Only a released deck can be withdrawn.", 409)
    deck.status = "superseded"; deck.superseded_at = datetime.now(timezone.utc)
    previous = db.scalar(select(FlashcardDeck).where(FlashcardDeck.topic_id == deck.topic_id,
        FlashcardDeck.status == "superseded", FlashcardDeck.id != deck.id,
        FlashcardDeck.generation_metadata["validation"].as_string() == "passed").order_by(
        FlashcardDeck.released_at.desc()).with_for_update())
    restored_ref = None
    if previous:
        version = db.get(TextbookTopicContentVersion, previous.content_version_id)
        if version and version.status == "published":
            previous.status = "released"; previous.superseded_at = None
            restored_ref = previous.public_ref
    db.add(AuditEvent(actor_id=principal.user.id, action="flashcard_release.withdrawn",
        target_type="flashcard_deck", target_id=deck.public_ref,
        event_data={"reason": reason, "restoredDeckRef": restored_ref}))
    db.commit(); db.refresh(deck)
    return _deck_out(db, deck)
