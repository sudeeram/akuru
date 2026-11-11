"""Bounded published-textbook evidence for final exam-content comparisons.

The model selects supplied chunk IDs, never arbitrary topic/page references. Saved
manual mapping decisions remain authoritative; disagreements become blockers.
"""
import hashlib
import json
import re
import uuid
from sqlalchemy import select
from app.errors import DomainError
from app.models import Document, RetrievalChunk, Textbook, TextbookTopic, TextbookTopicContentVersion

POLICY = 'paper-curriculum-v1'
AUTO_MAPPING_THRESHOLD = 90


def candidates(db, workspace, question):
    paper = db.get(Document, workspace.paper_document_id)
    topics = db.execute(select(TextbookTopic, TextbookTopicContentVersion).join(
        Textbook, Textbook.id == TextbookTopic.textbook_id).join(
        TextbookTopicContentVersion, TextbookTopicContentVersion.topic_id == TextbookTopic.id).where(
        TextbookTopic.course_id == paper.course_id, TextbookTopic.subject_id == paper.subject_id,
        Textbook.status == 'published', TextbookTopic.status == 'published',
        TextbookTopicContentVersion.status == 'published')).all()
    versions = {v.id: (t, v) for t, v in topics}
    if not versions:
        return []
    chunks = db.scalars(select(RetrievalChunk).join(Document, Document.id == RetrievalChunk.document_id).where(
        RetrievalChunk.topic_content_version_id.in_(versions), RetrievalChunk.status == 'active',
        RetrievalChunk.source_type == 'textbook_section', RetrievalChunk.course_id == paper.course_id,
        RetrievalChunk.subject_id == paper.subject_id, Document.removed_at.is_(None),
        Document.review_state == 'published').order_by(RetrievalChunk.id)).all()
    words = set(re.findall(r'[a-z]{3,}', json.dumps(question.review_data).lower()))
    def score(chunk):
        return len(words & set(re.findall(r'[a-z]{3,}', chunk.content.lower())))
    # Up to 3 relevant passages per topic; bounded globally. Include all published
    # topic identities in the task separately so no match is never a false absence.
    ranked = sorted(chunks, key=lambda c: (-score(c), str(c.id)))
    counts = {}; result = []
    for chunk in ranked:
        topic, version = versions[chunk.topic_content_version_id]
        if counts.get(topic.public_ref, 0) >= 3:
            continue
        counts[topic.public_ref] = counts.get(topic.public_ref, 0) + 1
        result.append(dict(chunkId=str(chunk.id), topicRef=topic.public_ref, title=topic.title,
            publicationId=str(version.id), publicationVersion=version.version_number,
            documentVersionId=str(chunk.document_version_id), page=chunk.page_number,
            contentHash=chunk.content_hash, text=chunk.content[:2200]))
        if len(result) >= 40:
            break
    return result


def mapping_hash(part):
    return hashlib.sha256(json.dumps({k: part.get(k) for k in (
        'coverage', 'topicRefs', 'textbookEvidence', 'coverageReason')}, sort_keys=True).encode()).hexdigest()


def current(db, part, check):
    if not check or check.get('mappingHash') != mapping_hash(part):
        return False
    for source in check.get('evidence', []):
        chunk = db.get(RetrievalChunk, uuid.UUID(source['chunkId']))
        version = db.get(TextbookTopicContentVersion, uuid.UUID(source['publicationId']))
        topic = db.get(TextbookTopic, version.topic_id) if version else None
        book = db.get(Textbook, topic.textbook_id) if topic else None
        document = db.get(Document, chunk.document_id) if chunk else None
        if (not chunk or chunk.status != 'active' or chunk.content_hash != source['contentHash']
                or str(chunk.document_version_id) != source['documentVersionId'] or chunk.page_number != source['page']
                or not version or version.status != 'published' or chunk.topic_content_version_id != version.id
                or not topic or topic.status != 'published' or topic.public_ref != source['topicRef']
                or chunk.topic_id != topic.id or (check.get('accepted') and topic.public_ref not in part.get('topicRefs', []))
                or not book or book.status != 'published'
                or not document or document.removed_at or document.review_state != 'published'):
            return False
    return True


def resolve(db, output, supplied, question):
    """Validate citations and return metadata; apply only previously undecided mappings."""
    by_id = {c['chunkId']: c for c in supplied}
    data = json.loads(json.dumps(question.review_data)); checks = {}
    for assessed in output.parts:
        proposal = assessed.curriculum
        part = next(p for p in data['parts'] if p['label'] == assessed.label)
        if proposal is None:
            continue
        if any(cid not in by_id for cid in proposal.chunkIds):
            raise DomainError('curriculum_unseen_evidence', 'The model cited an unprovided textbook passage.', 409)
        evidence = [by_id[cid] for cid in dict.fromkeys(proposal.chunkIds)]
        refs = sorted({v['topicRef'] for v in evidence})
        if proposal.coverage == 'supported' and not evidence:
            raise DomainError('curriculum_evidence_required', 'Supported curriculum needs exact published passages.', 409)
        confirmed = proposal.coverage == 'supported' and proposal.percent >= AUTO_MAPPING_THRESHOLD
        conflict = part['coverage'] != 'unreviewed' and (
            part['coverage'] != proposal.coverage or (proposal.coverage == 'supported' and set(part['topicRefs']) != set(refs)))
        # No model may replace a manually decided mapping, including outside coverage.
        if part['coverage'] == 'unreviewed' and confirmed:
            part.update(coverage='supported', topicRefs=refs, coverageReason=proposal.reason)
        check = proposal.model_dump(exclude={'chunkIds'})
        check.update(policy=POLICY, evidence=[{k: v for k, v in e.items() if k != 'text'} for e in evidence],
            accepted=confirmed and not conflict, conflict=conflict, mappingHash=mapping_hash(part))
        checks[assessed.label] = check
    return data, checks
