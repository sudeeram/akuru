import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (AuditEvent, Document, DocumentBlock, DocumentPage, FlashcardDeck,
    FlashcardVersion, RetrievalChunk, Textbook, TextbookGroup, TextbookTopic,
    TextbookTopicContentVersion, TextbookTopicVisualAsset, User)
from app.schemas.flashcard_artifacts import FlashcardReleaseArtifact


def canonical_checksum(artifact: FlashcardReleaseArtifact) -> str:
    payload = artifact.model_dump(mode="json", exclude={"artifactChecksum"})
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_artifact(path: str | Path) -> FlashcardReleaseArtifact:
    return FlashcardReleaseArtifact.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _quality_errors(artifact: FlashcardReleaseArtifact) -> list[str]:
    errors: list[str] = []
    all_cards = [card for deck in artifact.decks for card in deck.cards]
    for card in all_cards:
        question, answer = _normalized(card.question), _normalized(card.answer)
        if re.search(r"\b(page number|learning objectives?|figure \d+(?:\.\d+)?)\b", question):
            errors.append(f"{card.key}: question resembles a page label, objective or isolated caption")
        if question.rstrip(" ?") == answer.rstrip(" .") or (len(question) > 24 and question in answer):
            errors.append(f"{card.key}: answer merely repeats the question")
        if re.search(r"\b(?:hci|nh4ci)\b", card.question + " " + card.answer, re.I):
            errors.append(f"{card.key}: suspicious Chemistry OCR substitution (use HCl, not HCI)")
        command = re.match(r"^(calculate|compare|correct|define|describe|determine|explain|give|identify|name|plot|put|state|use|write)\b", card.question.strip(), re.I)
        if "?" not in card.question and not command:
            errors.append(f"{card.key}: question is incomplete or lacks a question mark")
        if card.category == "calculation_interpretation_diagram" and card.variationType not in {"calculation", "interpretation", "diagram"}:
            errors.append(f"{card.key}: category and variation type disagree")
    for index, left in enumerate(all_cards):
        left_q = _normalized(left.question)
        for right in all_cards[index + 1:]:
            ratio = SequenceMatcher(None, left_q, _normalized(right.question)).ratio()
            if ratio >= .90:
                errors.append(f"{left.key}/{right.key}: near-duplicate questions ({ratio:.0%})")
    return errors


def validate_artifact(db: Session, artifact: FlashcardReleaseArtifact) -> dict:
    errors = _quality_errors(artifact)
    checksum = canonical_checksum(artifact)
    if artifact.artifactChecksum and artifact.artifactChecksum != checksum:
        errors.append("artifactChecksum does not match the canonical artifact content")
    book = db.scalar(select(Textbook).where(Textbook.public_ref == artifact.textbookRef))
    group = db.scalar(select(TextbookGroup).where(TextbookGroup.public_ref == artifact.groupRef))
    if not book or book.course_id != artifact.courseId or book.subject_id != artifact.subjectId:
        errors.append("textbook does not belong to the declared course and subject")
    if not group or not book or group.textbook_id != book.id:
        errors.append("unit/module does not belong to the declared textbook")
    distribution = Counter()
    variations = Counter()
    difficulties = Counter()
    concepts = Counter()
    resolved: dict[str, dict] = {}
    for deck in artifact.decks:
        actual_concepts = {card.conceptKey for card in deck.cards}
        missing_concepts = set(deck.requiredConceptKeys) - actual_concepts
        if missing_concepts:
            errors.append(f"{deck.key}: required concepts without cards: {', '.join(sorted(missing_concepts))}")
        topic = db.scalar(select(TextbookTopic).where(TextbookTopic.public_ref == deck.topicRef))
        version = db.scalar(select(TextbookTopicContentVersion).where(TextbookTopicContentVersion.public_ref == deck.contentVersionRef))
        if not topic or topic.status != "published" or not group or topic.group_id != group.id:
            errors.append(f"{deck.key}: topic is not a published child of the declared unit/module")
            continue
        if not version or version.topic_id != topic.id or version.status != "published":
            errors.append(f"{deck.key}: content version is not the active published topic evidence")
            continue
        expected_checksum = artifact.sourceContentChecksums.get(deck.contentVersionRef)
        actual_checksum = hashlib.sha256(json.dumps({"sources": version.source_manifest, "extraction": version.extraction_manifest}, sort_keys=True, default=str).encode()).hexdigest()
        if expected_checksum != actual_checksum:
            errors.append(f"{deck.key}: source content checksum is missing or stale")
        resolved[deck.key] = {"topic": topic, "version": version, "cards": []}
        for card in deck.cards:
            chunks = db.scalars(select(RetrievalChunk).where(RetrievalChunk.id.in_(card.sourceChunkRefs))).all()
            if len(chunks) != len(set(card.sourceChunkRefs)):
                errors.append(f"{card.key}: one or more source chunks do not exist")
                continue
            if any(chunk.status != "active" or chunk.source_type != "textbook_section" or chunk.topic_id != topic.id or chunk.topic_content_version_id != version.id or chunk.subject_id != artifact.subjectId for chunk in chunks):
                errors.append(f"{card.key}: source evidence is outside the active published topic version")
                continue
            visual = None
            if card.visualAssetRef:
                visual = db.scalar(select(TextbookTopicVisualAsset).where(TextbookTopicVisualAsset.public_ref == card.visualAssetRef))
                if not visual or visual.topic_id != topic.id or visual.status != "approved":
                    errors.append(f"{card.key}: visual asset is not approved for this topic")
            resolved[deck.key]["cards"].append((card, chunks, visual))
            distribution[card.category] += 1
            variations[card.variationType] += 1
            difficulties[card.difficulty] += 1
            concepts[card.conceptKey] += 1
    return {"valid": not errors, "checksum": checksum, "errors": sorted(set(errors)),
        "cardCount": sum(len(deck.cards) for deck in artifact.decks), "deckCount": len(artifact.decks),
        "categoryDistribution": dict(sorted(distribution.items())), "conceptCount": len(concepts),
        "variationDistribution": dict(sorted(variations.items())),
        "difficultyDistribution": dict(sorted(difficulties.items())), "duplicateCount": 0,
        "resolved": resolved}


def import_artifact(db: Session, artifact: FlashcardReleaseArtifact, admin: User, *, release: bool, dry_run: bool) -> dict:
    report = validate_artifact(db, artifact)
    if not report["valid"]:
        raise DomainError("flashcard_artifact_invalid", "The curated flashcard artifact failed validation.", 422, report["errors"])
    existing = db.scalars(select(FlashcardDeck).where(FlashcardDeck.generation_metadata["releaseId"].as_string() == artifact.releaseId)).all()
    if existing:
        prior = {row.generation_metadata.get("artifactChecksum") for row in existing}
        if prior != {report["checksum"]}:
            raise DomainError("flashcard_release_id_conflict", "This release ID already belongs to different content.", 409)
        return {**{k: v for k, v in report.items() if k != "resolved"}, "status": "already_imported", "deckRefs": [row.public_ref for row in existing]}
    if dry_run:
        return {**{k: v for k, v in report.items() if k != "resolved"}, "status": "dry_run", "deckRefs": []}
    deck_refs = []
    git_revision = os.environ.get("AKURU_RELEASE_SHA", "")
    if not git_revision:
        try: git_revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, timeout=3).strip()
        except Exception: git_revision = "unknown"
    try:
        for deck_input in artifact.decks:
            item = report["resolved"][deck_input.key]
            topic, version = item["topic"], item["version"]
            generation_key = "curated:" + hashlib.sha256(f"{artifact.releaseId}:{deck_input.key}".encode()).hexdigest()[:72]
            deck = FlashcardDeck(topic_id=topic.id, content_version_id=version.id, title=deck_input.title,
                status="released" if release else "review", card_limit=len(deck_input.cards), generation_key=generation_key,
                generation_metadata={"releaseId": artifact.releaseId, "deckKey": deck_input.key,
                    "artifactChecksum": report["checksum"], "schemaVersion": artifact.schemaVersion,
                    "editor": artifact.editor, "generator": artifact.generator,
                    "generatorVersion": artifact.generatorVersion, "categoryDistribution": report["categoryDistribution"],
                    "validation": "passed", "gitRevision": git_revision,
                    "validationSummary": {"conceptCount": report["conceptCount"],
                        "duplicateCount": report["duplicateCount"], "variationDistribution": report["variationDistribution"],
                        "difficultyDistribution": report["difficultyDistribution"], "sourceVersion": deck_input.contentVersionRef}},
                created_by=admin.id,
                released_by=admin.id if release else None)
            if release:
                from datetime import datetime, timezone
                deck.released_at = datetime.now(timezone.utc)
                for prior in db.scalars(select(FlashcardDeck).where(FlashcardDeck.topic_id == topic.id, FlashcardDeck.status == "released").with_for_update()).all():
                    prior.status = "superseded"; prior.superseded_at = deck.released_at
            db.add(deck); db.flush(); deck_refs.append(deck.public_ref)
            for ordinal, (card, chunks, visual) in enumerate(item["cards"], 1):
                primary = chunks[0]
                document = db.get(Document, primary.document_id)
                block = db.get(DocumentBlock, primary.source_item_id)
                page = db.get(DocumentPage, block.page_id) if block else None
                snapshot = {"chunkRef": str(primary.id), "documentTitle": document.title if document else "Published textbook",
                    "page": primary.page_number, "printedPage": page.printed_page_label if page else None, "passage": primary.content,
                    "supportingChunkRefs": [str(chunk.id) for chunk in chunks[1:]]}
                version_row = FlashcardVersion(deck_id=deck.id, ordinal=ordinal, version_number=1,
                    front=card.question, back=card.answer, source_chunk_id=primary.id, source_snapshot=snapshot,
                    status="approved", validation_warnings=[], provider="curated", model=artifact.generator,
                    prompt_version=artifact.generatorVersion, external_key=card.key, concept_key=card.conceptKey,
                    category=card.category, variation_type=card.variationType, difficulty=card.difficulty,
                    card_metadata={"reviewer": card.reviewer, "reviewedAt": artifact.createdAt,
                        "reviewNote": card.reviewNote,
                        "explanation": card.explanation,
                        "allSourceChunkRefs": card.sourceChunkRefs, "visualAltText": card.visualAltText},
                    visual_asset_id=visual.id if visual else None, created_by=admin.id)
                db.add(version_row); db.flush()
        db.add(AuditEvent(actor_id=admin.id, action="flashcard_release.imported", target_type="flashcard_release",
            target_id=artifact.releaseId, event_data={"artifactChecksum": report["checksum"], "deckRefs": deck_refs,
                "cardCount": report["cardCount"], "released": release, "gitRevision": git_revision,
                "sourceContentVersions": list(artifact.sourceContentChecksums)}))
        db.commit()
    except Exception:
        db.rollback(); raise
    return {**{k: v for k, v in report.items() if k != "resolved"}, "status": "released" if release else "imported", "deckRefs": deck_refs}
