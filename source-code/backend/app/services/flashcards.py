import re
import random
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (
    AuditEvent, Document, DocumentAsset, DocumentBlock, DocumentPage, FlashcardDeck, FlashcardLearningState,
    FlashcardReport, FlashcardReview, FlashcardSession, FlashcardVersion, RetrievalChunk, TextbookGroup,
    TextbookTopic, TextbookTopicContentSource, TextbookTopicContentVersion, TextbookTopicVisualAsset,
    TopicRetrievalPreflight,
)
from app.schemas.flashcards import (FlashcardCardResponse, FlashcardDeckResponse, FlashcardDiscardResponse,
    FlashcardMasteryCategory, FlashcardMasteryResponse, FlashcardMasterySession, FlashcardSessionResponse,
    FlashcardReportResponse, FlashcardStudyOption, FlashcardStudyOptionsResponse)
from app.security import Principal
from app.services.curriculum_plans import student_coverage
from app.storage.base import ObjectStorage, StoredObject


PROMPT_VERSION = "grounded-flashcards-v1"
MASTERY_VERSION = "akuru-flashcard-mastery-v1"
SELECTION_VERSION = "akuru-flashcard-selection-v2"
RATING_VALUES = {"difficult": 0.0, "good": 0.65, "easy": 1.0}
RECENCY_WEIGHTS = (1.0, 0.75, 0.5, 0.25, 0.125)


def _mastery_from_ratings(ratings: list[str]) -> tuple[float, str, int, int]:
    """Return score, status, Easy streak and evaluated rating count.

    Ratings are chronological and must come only from completed sessions. Again
    adds no numeric value, resets the streak and forces Needs Review.
    """
    if not ratings:
        return 0.0, "to_evaluate", 0, 0
    streak = 0
    for rating in reversed(ratings):
        if rating != "easy":
            break
        streak += 1
    meaningful = [RATING_VALUES[rating] for rating in ratings if rating in RATING_VALUES]
    recent = list(reversed(meaningful[-len(RECENCY_WEIGHTS):]))
    weights = RECENCY_WEIGHTS[:len(recent)]
    score = round(sum(value * weight for value, weight in zip(recent, weights)) / sum(weights), 5) if recent else 0.0
    if ratings[-1] == "again":
        status = "needs_review"
    elif streak >= 3:
        status = "mastered"
    elif score >= 0.55:
        status = "good"
    else:
        status = "needs_review"
    return score, status, streak, len(ratings)


def _latest_cards(db: Session, deck_id) -> list[FlashcardVersion]:
    rows = db.scalars(select(FlashcardVersion).where(
        FlashcardVersion.deck_id == deck_id).order_by(
        FlashcardVersion.ordinal, FlashcardVersion.version_number.desc())).all()
    latest = {}
    for row in rows:
        latest.setdefault(row.ordinal, row)
    return list(latest.values())


_PAGE_BOUNDARY = re.compile(
    r"\b(?:start|end)\s+of\s+(?:printed\s+)?page\s+[a-z0-9._-]+\b\s*[:;,.\-–—]*",
    re.IGNORECASE,
)
_FIGURE_REFERENCE = re.compile(r"\bfig(?:ure)?\s*(\d+(?:\.\d+)*)\b", re.IGNORECASE)


def _clean_passage(value: str) -> str:
    """Remove extraction navigation markers that are not textbook content."""
    return " ".join(_PAGE_BOUNDARY.sub(" ", value).split())


def _readable_paragraphs(value: str) -> list[str]:
    cleaned = _PAGE_BOUNDARY.sub(" ", value).strip()
    explicit = [" ".join(part.split()) for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
    if len(explicit) > 1:
        return explicit
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if any(re.match(r"^(?:[-•]|\d+[.)])\s+", line) for line in lines):
        return lines
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(cleaned.split()))
    return [" ".join(sentences[index:index + 3]) for index in range(0, len(sentences), 3) if sentences[index:index + 3]]


def _approved_visual(db: Session, card: FlashcardVersion, chunk: RetrievalChunk,
                     page: DocumentPage | None) -> TextbookTopicVisualAsset | None:
    if card.visual_asset_id:
        visual = db.get(TextbookTopicVisualAsset, card.visual_asset_id)
        return visual if visual and visual.status == "approved" else None
    figure = _FIGURE_REFERENCE.search(chunk.content)
    if not figure:
        return None
    content_sources = select(TextbookTopicContentSource.document_version_id).where(
        TextbookTopicContentSource.content_version_id == chunk.topic_content_version_id,
        TextbookTopicContentSource.role == "primary",
    )
    candidates = db.scalars(select(TextbookTopicVisualAsset).where(
        TextbookTopicVisualAsset.topic_id == chunk.topic_id,
        TextbookTopicVisualAsset.status == "approved",
        TextbookTopicVisualAsset.document_version_id.in_(content_sources),
    ).order_by(TextbookTopicVisualAsset.reviewed_at.desc())).all()
    label = figure.group(1)
    matching = [row for row in candidates if re.search(
        rf"\bfig(?:ure)?\s*{re.escape(label)}\b", row.caption, re.IGNORECASE)]
    if page:
        same_page = [row for row in matching if (block := db.get(DocumentBlock, row.block_id))
                     and block.page_id == page.id]
        if same_page:
            return same_page[0]
    return matching[0] if len(matching) == 1 else None


def _visual_reference_page(db: Session, chunk: RetrievalChunk,
                           printed_page: str | None) -> DocumentPage | None:
    if not printed_page:
        return None
    versions = select(TextbookTopicContentSource.document_version_id).where(
        TextbookTopicContentSource.content_version_id == chunk.topic_content_version_id,
        TextbookTopicContentSource.role == "visual_reference",
    )
    return db.scalar(select(DocumentPage).where(
        DocumentPage.document_version_id.in_(versions),
        DocumentPage.printed_page_label == printed_page,
    ).order_by(DocumentPage.page_number))


def _source(db: Session, chunk: RetrievalChunk, card: FlashcardVersion | None = None,
            session_ref: str | None = None, position: int | None = None) -> dict:
    document = db.get(Document, chunk.document_id)
    block = db.get(DocumentBlock, chunk.source_item_id)
    page = db.get(DocumentPage, block.page_id) if block else None
    printed_page = page.printed_page_label if page else None
    result = {
        "chunkRef": str(chunk.id), "documentTitle": document.title if document else "Textbook",
        "page": chunk.page_number, "printedPage": printed_page,
        "passage": _clean_passage(chunk.content), "paragraphs": _readable_paragraphs(chunk.content),
    }
    if card and session_ref:
        visual = _approved_visual(db, card, chunk, page)
        if visual:
            result["visual"] = {"caption": visual.caption,
                "altText": visual.alt_text or card.card_metadata.get("visualAltText", ""),
                "contentUrl": f"/api/v1/flashcards/student/sessions/{session_ref}/visuals/{visual.public_ref}"}
        textbook_page = _visual_reference_page(db, chunk, printed_page)
        if textbook_page:
            result["textbookPageUrl"] = (
                f"/api/v1/flashcards/student/sessions/{session_ref}/textbook-pages/{textbook_page.id}")
    return result


def _card_out(db: Session, card: FlashcardVersion, *, reveal=False, session_ref=None,
              selected_rating: str | None = None, attempted: bool = False,
              position: int | None = None):
    chunk = db.get(RetrievalChunk, card.source_chunk_id)
    snapshot = dict(card.source_snapshot or {})
    if chunk and session_ref:
        snapshot.update(_source(db, chunk, card, session_ref, position))
    elif "passage" in snapshot:
        snapshot["passage"] = _clean_passage(snapshot["passage"])
    snapshot.pop("sourceUrl", None)
    return FlashcardCardResponse(cardRef=card.public_ref, ordinal=card.ordinal,
        version=card.version_number, front=card.front, back=card.back if reveal else None,
        explanation=(card.card_metadata or {}).get("explanation") if reveal else None,
        status=card.status, warnings=card.validation_warnings or [], source=snapshot,
        conceptKey=card.concept_key, category=card.category, variationType=card.variation_type,
        difficulty=card.difficulty, selectedRating=selected_rating, attempted=attempted)


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
        cards=[_card_out(db, row, reveal=reveal) for row in cards]
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
        cards.extend(card for card in _latest_cards(db, deck.id)
                     if card.status == "approved" and card.availability == "active")
    return cards


def _state_map(db: Session, student_id, cards: list[FlashcardVersion]):
    ids = [card.id for card in cards]
    return {row.card_version_id: row for row in db.scalars(select(FlashcardLearningState).where(
        FlashcardLearningState.student_id == student_id, FlashcardLearningState.card_version_id.in_(ids))).all()} if ids else {}


def study_options(db: Session, principal: Principal, deck_ref: str):
    decks = _eligible_deck_models(db, principal)
    deck = next((row for row in decks if row.public_ref == deck_ref), None)
    if not deck:
        raise DomainError("flashcard_deck_not_available", "This deck is not available in your current learning coverage.", 403)
    cards = _cards_for_decks(db, [deck])
    states = _state_map(db, principal.user.id, cards)
    counts = Counter((states[card.id].mastery_status if card.id in states else "to_evaluate") for card in cards)
    difficult_available = sum(
        state.mastery_status == "needs_review" if (state := states.get(card.id))
        else card.difficulty == "difficult" for card in cards
    )
    options = [
        FlashcardStudyOption(mode="review", title="Review Flashcards",
            description="Choose Easy, Difficult or Mixed cards, then study 20 or 30.",
            availableCount=len(cards), sessionSize=min(20, len(cards)), enabled=bool(cards),
            supportedCounts=[count for count in (20, 30) if len(cards) >= count] or ([len(cards)] if cards else []),
            difficulties=["easy", "difficult", "mixed"]),
        FlashcardStudyOption(mode="difficult", title="Difficult Flashcards",
            description="Focus on cards needing review and unattempted Difficult cards.",
            availableCount=difficult_available, sessionSize=min(20, difficult_available),
            enabled=difficult_available > 0,
            supportedCounts=[count for count in (20, 30) if difficult_available >= count] or
                ([difficult_available] if difficult_available else []), difficulties=[]),
    ]
    return FlashcardStudyOptionsResponse(deckRef=deck_ref, options=options,
        summary={"to_evaluate": counts["to_evaluate"], "needs_review": counts["needs_review"],
                 "good": counts["good"], "mastered": counts["mastered"]})


def _recent_card_ids(db: Session, student_id, deck_id) -> set[uuid.UUID]:
    sessions = db.scalars(select(FlashcardSession).where(
        FlashcardSession.student_id == student_id, FlashcardSession.deck_id == deck_id,
        FlashcardSession.status == "completed").order_by(
        FlashcardSession.completed_at.desc()).limit(3)).all()
    return {uuid.UUID(value) for session in sessions for value in session.selected_card_version_ids}


def _select_cards(db: Session, principal: Principal, deck: FlashcardDeck, mode: str,
                  difficulty: str | None, requested_count: int):
    cards = _cards_for_decks(db, [deck])
    states = _state_map(db, principal.user.id, cards)
    recent = _recent_card_ids(db, principal.user.id, deck.id)
    candidates = []
    for card in cards:
        state = states.get(card.id)
        status = state.mastery_status if state else "to_evaluate"
        if mode == "review":
            if difficulty in ("easy", "difficult") and card.difficulty != difficulty:
                continue
        elif not (status == "needs_review" or (status == "to_evaluate" and card.difficulty == "difficult")):
            continue
        reason = status
        priority = {"needs_review": 0, "to_evaluate": 1, "good": 2, "mastered": 3}[status]
        if card.id in recent and status != "needs_review":
            priority += 3
            reason += "_recent"
        candidates.append([priority, random.SystemRandom().random(), card, reason])
    random.SystemRandom().shuffle(candidates)
    candidates.sort(key=lambda row: (row[0], row[1]))
    by_category = defaultdict(list)
    for row in candidates:
        by_category[row[2].category].append(row)
    selected = []
    category_names = list(by_category)
    random.SystemRandom().shuffle(category_names)
    concept_counts = Counter()
    while category_names and len(selected) < requested_count:
        remaining = []
        for category in category_names:
            if by_category[category] and len(selected) < requested_count:
                # Prefer a concept not yet represented in this set. Priority and
                # randomized tie-breaking remain authoritative within that choice.
                rows = by_category[category]
                best_index = min(range(len(rows)), key=lambda index: (
                    concept_counts[rows[index][2].concept_key], rows[index][0], rows[index][1]
                ))
                chosen = rows.pop(best_index)
                selected.append(chosen)
                concept_counts[chosen[2].concept_key] += 1
            if by_category[category]:
                remaining.append(category)
        category_names = remaining
    return [(row[2], row[3]) for row in selected]


def _owned_session(db: Session, principal: Principal, session_ref: str, *, lock=False):
    statement = select(FlashcardSession).where(
        FlashcardSession.public_ref == session_ref,
        FlashcardSession.student_id == principal.user.id)
    if lock:
        statement = statement.with_for_update()
    row = db.scalar(statement)
    if not row:
        raise DomainError("flashcard_session_not_found", "Flashcard session not found.", 404)
    return row


def _session_card(db: Session, session: FlashcardSession, position: int) -> FlashcardVersion:
    ids = [str(value) for value in session.selected_card_version_ids]
    if position < 1 or position > len(ids):
        raise DomainError("flashcard_position_invalid", "That flashcard position is unavailable.", 404)
    card = db.get(FlashcardVersion, uuid.UUID(ids[position - 1]))
    if not card:
        raise DomainError("flashcard_not_found", "The flashcard is unavailable.", 404)
    return card

def _report_out(db: Session, report: FlashcardReport) -> FlashcardReportResponse:
    card = db.get(FlashcardVersion, report.card_version_id)
    return FlashcardReportResponse(reportRef=report.public_ref, cardRef=card.public_ref,
        question=card.front, reason=report.reason, status=report.status,
        availability=card.availability, createdAt=report.created_at.isoformat(),
        adminNote=report.admin_note)

def report_card(db: Session, principal: Principal, session_ref: str, reason: str):
    session = _owned_session(db, principal, session_ref, lock=True)
    reviews = _reviews(db, session); position = _first_unattempted(session, reviews)
    card = _session_card(db, session, position)
    existing = db.scalar(select(FlashcardReport).where(
        FlashcardReport.student_id == principal.user.id,
        FlashcardReport.card_version_id == card.id))
    if existing:
        return _report_out(db, existing)
    report = FlashcardReport(card_version_id=card.id, student_id=principal.user.id, reason=reason)
    card.availability = "reported"
    # Remove the card from every incomplete snapshot so it cannot reappear.
    for active in db.scalars(select(FlashcardSession).where(FlashcardSession.status == "active")).all():
        ids = [str(value) for value in active.selected_card_version_ids]
        if str(card.id) not in ids: continue
        index = ids.index(str(card.id)); ids.pop(index)
        reasons = list(active.selection_reasons or [])
        if index < len(reasons): reasons.pop(index)
        revealed = [value for value in (active.revealed_card_version_ids or []) if str(value) != str(card.id)]
        db.query(FlashcardReview).filter(FlashcardReview.session_id == active.id,
            FlashcardReview.card_version_id == card.id).delete()
        active.selected_card_version_ids = ids; active.selection_reasons = reasons
        active.revealed_card_version_ids = revealed; active.target_count = len(ids)
        active.current_ordinal = max(1, min(active.current_ordinal, len(ids))) if ids else 1
        if not ids: active.status = "discarded"
    db.add(report); db.add(AuditEvent(actor_id=principal.user.id, action="flashcard.reported",
        target_type="flashcard", target_id=card.public_ref, event_data={"reason": reason}))
    db.commit(); db.refresh(report)
    return _report_out(db, report)

def admin_reports(db: Session):
    return [_report_out(db, row) for row in db.scalars(select(FlashcardReport).order_by(
        FlashcardReport.created_at.desc())).all()]

def decide_report(db: Session, principal: Principal, report_ref: str, decision: str, note: str):
    report = db.scalar(select(FlashcardReport).where(FlashcardReport.public_ref == report_ref).with_for_update())
    if not report: raise DomainError("flashcard_report_not_found", "Flashcard report not found.", 404)
    card = db.get(FlashcardVersion, report.card_version_id)
    report.status = "excluded" if decision == "exclude" else "restored"
    card.availability = "excluded" if decision == "exclude" else "active"
    report.reviewed_by = principal.user.id; report.reviewed_at = datetime.now(timezone.utc); report.admin_note = note or None
    db.add(AuditEvent(actor_id=principal.user.id, action=f"flashcard.report_{report.status}",
        target_type="flashcard_report", target_id=report.public_ref, event_data={"cardRef": card.public_ref, "note": note}))
    db.commit(); db.refresh(report)
    return _report_out(db, report)


def _reviews(db: Session, session: FlashcardSession) -> list[FlashcardReview]:
    rows = db.scalars(select(FlashcardReview).where(
        FlashcardReview.session_id == session.id).order_by(FlashcardReview.created_at)).all()
    positions = {str(value): index + 1 for index, value in enumerate(session.selected_card_version_ids)}
    return sorted(rows, key=lambda row: positions.get(str(row.card_version_id), 10**9))


def _first_unattempted(session: FlashcardSession, reviews: list[FlashcardReview]) -> int:
    return min(len(session.selected_card_version_ids), len(reviews) + 1)


def _allowed_position(session: FlashcardSession, reviews: list[FlashcardReview], position: int | None) -> int:
    total = len(session.selected_card_version_ids)
    frontier = total if session.status == "completed" else _first_unattempted(session, reviews)
    viewed = position or frontier
    if viewed < 1 or viewed > total or (session.status == "active" and viewed > frontier):
        raise DomainError("flashcard_position_locked", "Complete the current flashcard before opening a later card.", 409)
    return viewed


def _stored_asset(storage: ObjectStorage, asset: DocumentAsset, missing_code: str) -> StoredObject:
    try:
        return storage.get(asset.object_key, asset.mime_type)
    except FileNotFoundError as error:
        raise DomainError(missing_code, "The approved textbook image is unavailable.", 404) from error


def open_visual(db: Session, principal: Principal, storage: ObjectStorage,
                session_ref: str, visual_ref: str) -> StoredObject:
    session = _owned_session(db, principal, session_ref)
    visual = None
    revealed = set(session.revealed_card_version_ids or [])
    for raw_id in session.selected_card_version_ids:
        if str(raw_id) not in revealed:
            continue
        card = db.get(FlashcardVersion, uuid.UUID(str(raw_id)))
        chunk = db.get(RetrievalChunk, card.source_chunk_id) if card else None
        block = db.get(DocumentBlock, chunk.source_item_id) if chunk else None
        page = db.get(DocumentPage, block.page_id) if block else None
        candidate = _approved_visual(db, card, chunk, page) if card and chunk else None
        if candidate and candidate.public_ref == visual_ref:
            visual = candidate; break
    if not visual:
        raise DomainError("flashcard_visual_not_found", "The approved flashcard visual was not found.", 404)
    asset = db.get(DocumentAsset, visual.document_asset_id)
    if not asset:
        raise DomainError("flashcard_visual_not_found", "The approved flashcard visual was not found.", 404)
    return _stored_asset(storage, asset, "flashcard_visual_missing")


def open_textbook_page(db: Session, principal: Principal, storage: ObjectStorage,
                       session_ref: str, page_id: uuid.UUID) -> StoredObject:
    session = _owned_session(db, principal, session_ref)
    expected = None
    revealed = set(session.revealed_card_version_ids or [])
    for raw_id in session.selected_card_version_ids:
        if str(raw_id) not in revealed:
            continue
        card = db.get(FlashcardVersion, uuid.UUID(str(raw_id)))
        chunk = db.get(RetrievalChunk, card.source_chunk_id) if card else None
        block = db.get(DocumentBlock, chunk.source_item_id) if chunk else None
        source_page = db.get(DocumentPage, block.page_id) if block else None
        candidate = _visual_reference_page(
            db, chunk, source_page.printed_page_label if source_page else None) if chunk else None
        if candidate and candidate.id == page_id:
            expected = candidate; break
    if not expected:
        raise DomainError("flashcard_textbook_page_not_found", "The matching textbook page was not found.", 404)
    asset = db.get(DocumentAsset, expected.original_render_asset_id or expected.render_asset_id)
    if not asset:
        raise DomainError("flashcard_textbook_page_not_found", "The matching textbook page was not found.", 404)
    return _stored_asset(storage, asset, "flashcard_textbook_page_missing")


def _session_out(db: Session, session: FlashcardSession, *, position: int | None = None,
                 message="Ready to study."):
    deck = db.get(FlashcardDeck, session.deck_id)
    reviews = _reviews(db, session)
    viewed = _allowed_position(session, reviews, position)
    ids = [str(value) for value in session.selected_card_version_ids]
    card = _session_card(db, session, viewed) if ids else None
    review_by_card = {str(row.card_version_id): row for row in reviews}
    selected_review = review_by_card.get(ids[viewed - 1]) if ids else None
    attempted = selected_review is not None
    revealed = attempted or ids[viewed - 1] in (session.revealed_card_version_ids or [])
    frontier = len(ids) if session.status == "completed" else _first_unattempted(session, reviews)
    return FlashcardSessionResponse(sessionRef=session.public_ref,
        deck=_deck_out(db, deck, include_cards=False, student_id=session.student_id), status=session.status,
        currentOrdinal=frontier, reviewedCount=len(reviews), totalCards=len(ids),
        currentCard=_card_out(db, card, reveal=revealed, session_ref=session.public_ref,
            selected_rating=selected_review.rating if selected_review else None,
            attempted=attempted, position=viewed) if card else None,
        answerRevealed=revealed, masteryVersion=session.mastery_version,
        selectionVersion=session.selection_version, message=message, mode=session.mode,
        difficulty=session.difficulty_filter, selectionReasons=session.selection_reasons,
        viewedOrdinal=viewed, firstUnattemptedOrdinal=frontier,
        canGoPrevious=viewed > 1, canGoNext=viewed < frontier,
        hasUncommittedResults=session.status == "active" and bool(reviews))


def start_session(db: Session, principal: Principal, deck_ref: str, request_key: str,
                  mode: str = "review", difficulty: str | None = None, requested_count: int = 20):
    existing = db.scalar(select(FlashcardSession).where(FlashcardSession.request_key == request_key))
    if existing:
        if existing.student_id != principal.user.id:
            raise DomainError("request_key_conflict", "Request key is already in use.", 409)
        return _session_out(db, existing)
    allowed = {row.deckRef for row in student_decks(db, principal)}
    if deck_ref not in allowed:
        raise DomainError("flashcard_deck_not_available", "This deck is not available in your current learning coverage.", 403)
    deck = db.scalar(select(FlashcardDeck).where(FlashcardDeck.public_ref == deck_ref))
    active = db.scalar(select(FlashcardSession).where(
        FlashcardSession.student_id == principal.user.id,
        FlashcardSession.deck_id == deck.id, FlashcardSession.status == "active"))
    if active:
        return _session_out(db, active, message="Your incomplete session is ready to continue.")
    selected = _select_cards(db, principal, deck, mode, difficulty, requested_count)
    if not selected:
        raise DomainError("flashcard_mode_empty", "No cards are currently available for this selection.", 409)
    session = FlashcardSession(student_id=principal.user.id, deck_id=deck.id, current_ordinal=1,
        mastery_version=MASTERY_VERSION, selection_version=SELECTION_VERSION,
        request_key=request_key, mode=mode, difficulty_filter=difficulty,
        target_count=len(selected), selected_card_version_ids=[str(card.id) for card, _ in selected],
        selection_reasons=[reason for _, reason in selected], revealed_card_version_ids=[])
    db.add(session); db.commit(); db.refresh(session)
    message = (f"Started with {len(selected)} available cards." if len(selected) < requested_count
               else "Your flashcard session is ready.")
    return _session_out(db, session, message=message)


def get_session(db: Session, principal: Principal, session_ref: str, position: int | None = None):
    return _session_out(db, _owned_session(db, principal, session_ref), position=position)


def reveal(db: Session, principal: Principal, session_ref: str):
    session = _owned_session(db, principal, session_ref, lock=True)
    if session.status != "active":
        raise DomainError("flashcard_session_complete", "This session is already complete.", 409)
    reviews = _reviews(db, session)
    frontier = _first_unattempted(session, reviews)
    card = _session_card(db, session, frontier)
    revealed = list(session.revealed_card_version_ids or [])
    if str(card.id) not in revealed:
        revealed.append(str(card.id)); session.revealed_card_version_ids = revealed
        db.commit(); db.refresh(session)
    return _session_out(db, session, position=frontier, message="Approved answer shown.")


def _apply_mastery(db: Session, session: FlashcardSession, reviews: list[FlashcardReview], now: datetime) -> None:
    for review in reviews:
        history = list(db.scalars(select(FlashcardReview.rating).join(
            FlashcardSession, FlashcardReview.session_id == FlashcardSession.id).where(
            FlashcardSession.student_id == session.student_id,
            FlashcardReview.card_version_id == review.card_version_id,
            FlashcardReview.committed_at.is_not(None)).order_by(FlashcardReview.committed_at)).all())
        score, status, streak, evaluated = _mastery_from_ratings(history + [review.rating])
        state = db.scalar(select(FlashcardLearningState).where(
            FlashcardLearningState.student_id == session.student_id,
            FlashcardLearningState.card_version_id == review.card_version_id).with_for_update())
        card = db.get(FlashcardVersion, review.card_version_id)
        if not state:
            state = FlashcardLearningState(student_id=session.student_id,
                card_version_id=review.card_version_id, concept_key=card.concept_key)
            db.add(state)
        state.mastery_score = score; state.mastery_status = status
        state.consecutive_easy = streak; state.evaluated_count = evaluated
        state.mastery_version = MASTERY_VERSION; state.last_rating = review.rating
        state.last_reviewed_at = now; review.committed_at = now


def rate(db: Session, principal: Principal, session_ref: str, rating: str, request_key: str):
    session = _owned_session(db, principal, session_ref, lock=True)
    existing = db.scalar(select(FlashcardReview).where(FlashcardReview.request_key == request_key))
    if existing:
        if existing.session_id != session.id:
            raise DomainError("request_key_conflict", "Request key is already in use.", 409)
        return _session_out(db, session, message="That rating was already saved.")
    if session.status != "active":
        raise DomainError("flashcard_session_complete", "This session is already complete.", 409)
    reviews = _reviews(db, session)
    frontier = _first_unattempted(session, reviews)
    card = _session_card(db, session, frontier)
    if str(card.id) not in (session.revealed_card_version_ids or []):
        raise DomainError("flashcard_answer_required", "Show the approved answer before rating this card.", 409)
    review = FlashcardReview(session_id=session.id, card_version_id=card.id,
                             rating=rating, request_key=request_key)
    db.add(review); db.flush(); reviews.append(review)
    now = datetime.now(timezone.utc)
    if len(reviews) == len(session.selected_card_version_ids):
        _apply_mastery(db, session, reviews, now)
        session.status = "completed"; session.completed_at = now
        session.current_ordinal = len(reviews)
        message = "You completed this flashcard session. Your mastery has been updated."
        viewed = len(reviews)
    else:
        session.current_ordinal = len(reviews) + 1
        message = "Rating saved. Here is the next card."
        viewed = session.current_ordinal
    db.commit(); db.refresh(session)
    return _session_out(db, session, position=viewed, message=message)


def discard(db: Session, principal: Principal, session_ref: str) -> FlashcardDiscardResponse:
    session = _owned_session(db, principal, session_ref, lock=True)
    if session.status != "active":
        raise DomainError("flashcard_session_not_active", "Only an incomplete session can be discarded.", 409)
    review_count = len(_reviews(db, session))
    deck = db.get(FlashcardDeck, session.deck_id)
    db.add(AuditEvent(actor_id=principal.user.id, action="flashcard_session.discarded",
        target_type="flashcard_session", target_id=session.public_ref,
        event_data={"deckRef": deck.public_ref if deck else None,
                    "provisionalRatingsDiscarded": review_count}))
    db.delete(session); db.commit()
    return FlashcardDiscardResponse(sessionRef=session_ref, status="discarded",
                                    message="The incomplete attempt and its provisional results were discarded.")


def mastery_summary(db: Session, principal: Principal, deck_ref: str) -> FlashcardMasteryResponse:
    eligible = {deck.public_ref: deck for deck in _eligible_deck_models(db, principal)}
    deck = eligible.get(deck_ref)
    if not deck:
        raise DomainError("flashcard_deck_not_available", "This deck is not available in your current learning coverage.", 403)
    cards = _cards_for_decks(db, [deck]); states = _state_map(db, principal.user.id, cards)
    totals = Counter(); by_category = defaultdict(Counter)
    scores = []; latest = None
    for card in cards:
        state = states.get(card.id); status = state.mastery_status if state else "to_evaluate"
        totals[status] += 1; by_category[card.category][status] += 1
        if state:
            scores.append(state.mastery_score)
            if state.last_reviewed_at and (latest is None or state.last_reviewed_at > latest): latest = state.last_reviewed_at
    categories = []
    for category in sorted(by_category):
        values = by_category[category]; total = sum(values.values()); evaluated = total - values["to_evaluate"]
        category_states = [states.get(card.id) for card in cards if card.category == category and states.get(card.id)]
        categories.append(FlashcardMasteryCategory(category=category, total=total,
            toEvaluate=values["to_evaluate"], needsReview=values["needs_review"],
            good=values["good"], mastered=values["mastered"],
            coveragePercent=round(100 * evaluated / total, 1) if total else 0,
            masteryPercent=round(100 * sum(state.mastery_score for state in category_states) / evaluated, 1) if evaluated else 0))
    evaluated = len(cards) - totals["to_evaluate"]
    completed = db.scalar(select(func.count()).select_from(FlashcardSession).where(
        FlashcardSession.student_id == principal.user.id, FlashcardSession.deck_id == deck.id,
        FlashcardSession.status == "completed")) or 0
    recent_rows = db.scalars(select(FlashcardSession).where(
        FlashcardSession.student_id == principal.user.id, FlashcardSession.deck_id == deck.id,
        FlashcardSession.status == "completed").order_by(
        FlashcardSession.completed_at.desc()).limit(5)).all()
    recent = [FlashcardMasterySession(sessionRef=row.public_ref, mode=row.mode,
        difficulty=row.difficulty_filter, cardCount=row.target_count,
        completedAt=row.completed_at.isoformat()) for row in recent_rows if row.completed_at]
    recommendation = "difficult" if totals["needs_review"] else "review"
    return FlashcardMasteryResponse(deckRef=deck_ref, totalCards=len(cards),
        toEvaluate=totals["to_evaluate"], needsReview=totals["needs_review"],
        good=totals["good"], mastered=totals["mastered"],
        coveragePercent=round(100 * evaluated / len(cards), 1) if cards else 0,
        masteryPercent=round(100 * sum(scores) / evaluated, 1) if evaluated else 0,
        categories=categories, completedSessions=completed, recentSessions=recent,
        recommendedMode=recommendation,
        recommendedDifficulty=None if recommendation == "difficult" else (
            "difficult" if totals["to_evaluate"] and any(
                card.difficulty == "difficult" and card.id not in states for card in cards) else "mixed"),
        recommendedCount=30 if len(cards) >= 30 and evaluated >= 20 else 20,
        masteryVersion=MASTERY_VERSION, recalculatedAt=latest.isoformat() if latest else None)


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
