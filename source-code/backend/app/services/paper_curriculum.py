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
from app.models import Document, OfficialQuestionAnalysis, RetrievalChunk, Textbook, TextbookTopic, TextbookTopicContentVersion

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
    def terms(text):
        return set(re.findall(r'[a-z]{3,}', text.lower()))

    parts = question.review_data.get('parts', [])
    queries = {p['label']: terms(' '.join(
        [p.get('prompt', ''), *(m['text'] for m in p.get('markingPoints', []))]))
        for p in parts}
    chunk_terms = {c.id: terms(c.content) for c in chunks}

    def ranked(words, pool):
        return sorted(pool, key=lambda c: (-len(words & chunk_terms[c.id]), str(c.id)))

    counts, seen, result = {}, set(), []

    def add(chunk):
        topic, version = versions[chunk.topic_content_version_id]
        if chunk.id in seen or counts.get(topic.public_ref, 0) >= 3 or len(result) >= 40:
            return
        seen.add(chunk.id)
        counts[topic.public_ref] = counts.get(topic.public_ref, 0) + 1
        result.append(dict(chunkId=str(chunk.id), topicRef=topic.public_ref, title=topic.title,
            publicationId=str(version.id), publicationVersion=version.version_number,
            documentVersionId=str(chunk.document_version_id), page=chunk.page_number,
            contentHash=chunk.content_hash, text=chunk.content[:2200]))

    # A newer incomplete comparison must not crowd out still-current accepted
    # evidence. Reuse it as input only; the model must verify it again.
    by_id = {str(c.id): c for c in chunks}
    retained = {}
    history = db.scalars(select(OfficialQuestionAnalysis).where(
        OfficialQuestionAnalysis.question_id == question.id,
        OfficialQuestionAnalysis.stage == 'accuracy'
    ).order_by(OfficialQuestionAnalysis.version_number.desc()).limit(20)).all()
    for part in parts:
        for assessment in history:
            prior = next((p for p in assessment.analysis_data['parts']
                          if p['label'] == part['label']), None)
            check = (prior or {}).get('curriculum')
            if check and check.get('accepted') and current(db, part, check):
                retained[part['label']] = [by_id[e['chunkId']] for e in check['evidence']
                                          if e['chunkId'] in by_id]
                break

    # Give each mapped subpart a turn before broad subject retrieval.
    pools = {}
    for part in parts:
        label = part['label']
        refs = set(part.get('topicRefs', []))
        pools[label] = retained.get(label, []) + ranked(queries[label], [
            c for c in chunks if versions[c.topic_content_version_id][0].public_ref in refs
            and queries[label] & chunk_terms[c.id]])
    for _ in range(3):
        for pool in pools.values():
            while pool:
                count = len(result)
                add(pool.pop(0))
                if len(result) > count:
                    break

    words = terms(question.review_data.get('sharedStem', '')) | set().union(*queries.values())
    for chunk in ranked(words, chunks):
        add(chunk)
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
