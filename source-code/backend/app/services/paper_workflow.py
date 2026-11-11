"""Bounded batched source summaries. Never mutate approvals or charge a model."""
import uuid
from collections import defaultdict
from sqlalchemy import select, or_
from app.models import AuditEvent, Document, DocumentVersion, DocumentPage, DocumentBlock, DocumentAsset, OfficialPaperReviewWorkspace, OfficialPaperReviewQuestion, OfficialQuestionAnalysis, EvidenceLinkJob, TutorPaperRelease, RetrievalChunk, TextbookTopicContentVersion, TextbookTopic, Textbook
from .official_question_analyses import content_hash
from .paper_curriculum import mapping_hash
from .tutor_past_papers import release_fingerprint
from .official_paper_reviews import visual_requirement_issues

def step(number, label, done, total, href, *, active=False, valid=True, attempted=False, checked=None, detail=None):
    state = 'complete' if total > 0 and done == total and valid else 'processing' if active else 'attention' if done or not valid or attempted else 'not_started'
    return dict(number=number, label=label, state=state, completed=done, checked=checked, total=total, href=href, detail=detail or f'{done}/{total} complete')

def summaries(db, document_ids):
    selected = set(document_ids)
    workspaces = db.scalars(select(OfficialPaperReviewWorkspace).where(or_(OfficialPaperReviewWorkspace.paper_document_id.in_(selected), OfficialPaperReviewWorkspace.scheme_document_id.in_(selected), OfficialPaperReviewWorkspace.report_document_id.in_(selected)))).all()
    all_ids = selected | {i for w in workspaces for i in (w.paper_document_id, w.scheme_document_id, w.report_document_id) if i}
    docs = {d.id: d for d in db.scalars(select(Document).where(or_(Document.id.in_(all_ids), Document.id.in_(select(Document.source_document_id).where(Document.id.in_(selected)).correlate(None))), Document.removed_at.is_(None)))}
    all_ids.update(docs)
    versions = {v.id: v for v in db.scalars(select(DocumentVersion).where(DocumentVersion.document_id.in_(all_ids)).order_by(DocumentVersion.version_number))}
    latest = {v.document_id: v for v in versions.values()}
    pages = defaultdict(list)
    for p in db.scalars(select(DocumentPage).where(DocumentPage.document_version_id.in_(versions))):
        pages[p.document_version_id].append(p)
    questions = db.scalars(select(OfficialPaperReviewQuestion).where(OfficialPaperReviewQuestion.workspace_id.in_([w.id for w in workspaces]))).all()
    by_workspace = defaultdict(list)
    for q in questions:
        by_workspace[q.workspace_id].append(q)
    analyses = {}
    for a in db.scalars(select(OfficialQuestionAnalysis).where(OfficialQuestionAnalysis.question_id.in_([q.id for q in questions]), OfficialQuestionAnalysis.stage == 'accuracy').order_by(OfficialQuestionAnalysis.version_number.desc())):
        analyses.setdefault(a.question_id, a)
    manual_checks = list(db.scalars(select(AuditEvent).where(AuditEvent.action == 'official_review.part_manually_approved', AuditEvent.target_id.in_([str(q.id) for q in questions]))))
    active = {j.paper_id for j in db.scalars(select(EvidenceLinkJob).where(EvidenceLinkJob.paper_id.in_(all_ids), EvidenceLinkJob.status.in_(['queued', 'processing'])))}
    releases = defaultdict(list)
    for r in db.scalars(select(TutorPaperRelease).where(TutorPaperRelease.question_id.in_([q.id for q in questions]))):
        releases[r.question_id].append(r)
    block_ids = set()
    asset_ids = set()
    chunk_ids = set()
    for q in questions:
        for scope in [q.review_data, *q.review_data['parts']]:
            asset_ids.update(scope.get('visualAssetIds', []))
            asset_ids.update(scope.get('candidateVisualAssetIds', []))
            asset_ids.update((v['assetId'] for v in scope.get('answerVisuals', [])))
            for role in ('paper', 'scheme', 'report'):
                for source in scope.get(role + 'Sources', []):
                    if source.get('blockId'):
                        block_ids.add(source['blockId'])
                    if source.get('assetId'):
                        asset_ids.add(source['assetId'])
        a = analyses.get(q.id)
        if a:
            for p in a.analysis_data['parts']:
                chunk_ids.update((e['chunkId'] for e in (p.get('curriculum') or {}).get('evidence', [])))
    blocks = list(db.scalars(select(DocumentBlock).where(DocumentBlock.id.in_([uuid.UUID(v) for v in block_ids])).order_by(DocumentBlock.id)))
    assets = list(db.scalars(select(DocumentAsset).where(DocumentAsset.id.in_([uuid.UUID(v) for v in asset_ids])).order_by(DocumentAsset.id)))
    asset_map = {str(a.id): a for a in assets}
    chunks = {str(c.id): c for c in db.scalars(select(RetrievalChunk).join(Document, Document.id == RetrievalChunk.document_id).where(RetrievalChunk.id.in_([uuid.UUID(v) for v in chunk_ids]), Document.review_state == 'published', Document.removed_at.is_(None)))}
    pub_rows = db.execute(select(TextbookTopicContentVersion, TextbookTopic, Textbook).join(TextbookTopic, TextbookTopic.id == TextbookTopicContentVersion.topic_id).join(Textbook, Textbook.id == TextbookTopic.textbook_id).where(or_(TextbookTopicContentVersion.id.in_([c.topic_content_version_id for c in chunks.values()]), TextbookTopic.public_ref.in_([ref for q in questions for p in q.review_data['parts'] for ref in p.get('topicRefs',[])])))).all()
    pubs = {str(v.id): (v, t, b) for v, t, b in pub_rows}
    published = defaultdict(list)
    for version, topic, book in pub_rows:
        if all(item.status == 'published' for item in (version,topic,book)):
            published[topic.public_ref].append((version,topic))

    def curriculum_current(part, check):
        if not check or not check.get('accepted') or check.get('mappingHash') != mapping_hash(part):
            return False
        evidence = check.get('evidence', [])
        if not evidence:
            return False
        for e in evidence:
            c = chunks.get(e['chunkId'])
            pub = pubs.get(e['publicationId'])
            if not c or not pub or c.status != 'active' or (c.content_hash != e['contentHash']) or (str(c.document_version_id) != e['documentVersionId']) or (c.page_number != e['page']) or (pub[1].public_ref != e['topicRef']) or (c.topic_id != pub[1].id) or any((x.status != 'published' for x in pub)):
                return False
        return True
    result = defaultdict(list)

    def extracted(doc_id, version_id, href):
        v = versions.get(version_id)
        count = len(pages.get(version_id, []))
        complete = bool(v and v.status in {'needs_review', 'completed'} and count)
        return step(1, 'Extracted', int(complete), 1, href, active=bool(v and v.status in {'queued', 'processing'}), valid=bool(v and v.status != 'failed'), detail=f'{count} extracted pages; extraction completion is not accuracy approval.' if count else 'No complete extraction recorded.')
    for w in workspaces:
        paper = docs.get(w.paper_document_id)
        if not paper:
            continue
        qs = by_workspace[w.id]
        href = f'/admin/exam-documents/review/{paper.id}'
        accuracy = href + '/accuracy'
        manifest = []
        for role in ('paper', 'scheme', 'report'):
            vid = getattr(w, role + '_version_id')
            v = versions.get(vid)
            manifest.append(dict(role=role, documentVersionId=str(v.id) if v else None, sha256=v.sha256 if v else None, filename=v.original_filename if v else None, version=v.version_number if v else None, pageExtractionMethods=sorted({p.extraction_method for p in pages.get(vid, [])})))
        bound = all((not getattr(w, r + '_version_id') or (getattr(w, r + '_document_id') in docs and latest[getattr(w, r + '_document_id')].id == getattr(w, r + '_version_id')) for r in ('paper', 'scheme', 'report')))
        image_done = assessed_done = released = excluded = total = compared = 0
        image_attempted = False
        checked = {'scheme': 0, 'report': 0}
        check_total = 0
        for q in qs:
            data = q.review_data
            a = analyses.get(q.id)
            evidence_hash = content_hash(db, q, manifest, block_rows=blocks, asset_rows=assets)
            current = bool(bound and a and a.content_hash == evidence_hash)
            scores = {p['label']: p for p in a.analysis_data['parts']} if current else {}
            ids = set(data.get('visualAssetIds', [])) | {v for p in data['parts'] for v in p.get('visualAssetIds', [])}
            images_ok = not data.get('candidateVisualAssetIds') and all((v in asset_map and asset_map[v].asset_metadata.get('reviewApproved') and (data.get('visualAltText', '').strip() or asset_map[v].asset_metadata.get('altText', '').strip()) for v in ids)) and (not any((v['status'] == 'proposed' for p in data['parts'] for v in p.get('answerVisuals', []))))
            approved_answers = [v for p in data['parts'] for v in p.get('answerVisuals', []) if v['status'] == 'approved']
            images_ok = images_ok and all((v['assetId'] in asset_map and asset_map[v['assetId']].document_version_id == w.scheme_version_id for v in approved_answers))
            images_ok = images_ok and (not visual_requirement_issues(data, asset_map))
            image_attempted = image_attempted or any((asset_map[v].asset_metadata.get('reviewApproved') for v in ids if v in asset_map)) or bool(approved_answers)
            image_done += int(images_ok)
            for part in data['parts']:
                total += 1
                check_total += 1
                compared += int(bool(current and a.analysis_data.get('methodVersion') == 'final-source-accuracy-v2'))
                excluded += int(q.status == 'excluded' or part['status'] == 'excluded')
                score = scores.get(part['label'])
                mapping_ok = curriculum_current(part, score.get('curriculum')) if score else False
                approved = part['status'] in {'approved', 'ai_approved'}
                if score and score['percent'] <= 75:
                    approved = part['status'] == 'approved' and any((e.target_id == str(q.id) and e.event_data.get('part') == part['label'] and (e.event_data.get('analysisId') == str(a.id)) and (e.event_data.get('contentHash') == a.content_hash) for e in manual_checks))
                marking_ready = part.get('assessmentReadiness') == 'automatic' or (part.get('assessmentReadiness') == 'manual_only' and part.get('responseType') == 'drawing')
                assessed_done += int(bool(current and mapping_ok and approved and images_ok and marking_ready))
                for role in ('scheme', 'report'):
                    source = next((s for s in (score or {}).get('sourceChecks', []) if s['role'] == role), None)
                    checked[role] += int(bool(source and source['status'] in {'checked', 'no_comment'} and (source.get('percent', 0) > 75 or (approved and part['status'] == 'approved'))))
                rows = releases[q.id]
                publication_refs = sorted(set(part.get('topicRefs',[])))
                publications = [dict(topicRef=ref,publicationId=str(published[ref][0][0].id)) for ref in publication_refs if len(published[ref])==1 and published[ref][0][1].course_id==paper.course_id and published[ref][0][1].subject_id==paper.subject_id]
                publication_bound = bool(publications and len(publications)==len(publication_refs))
                released += int(bool(bound and publication_bound and images_ok and approved and (part['coverage'] == 'supported') and (q.status not in {'excluded', 'needs_correction'}) and any((r.enabled and r.part_label == part['label'] and (r.fingerprint == release_fingerprint(q, w, publications, evidence_hash)) and (r.snapshot.get('releasePolicy') != 'auto-tutor-release-v1' or mapping_ok) for r in rows))))
        inventory = bool(w.expected_question_count and len(qs) == w.expected_question_count and all(q.review_data['parts'] and all(p.get('prompt','').strip() and p.get('marks',0)>0 and p.get('markingPoints') and p.get('paperSources') and p.get('schemeSources') for p in q.review_data['parts']) for q in qs))
        steps = [step(1, 'Extracted', len(qs), w.expected_question_count, href, active=bool(versions.get(w.paper_version_id) and versions[w.paper_version_id].status in {'queued', 'processing'}), valid=inventory and bound, detail=f'{len(qs)}/{w.expected_question_count} expected questions; {total} subparts. Inventory must reconcile.'), step(2, 'Images reviewed', image_done, len(qs), href, valid=inventory and bound, attempted=image_attempted, detail=f'{image_done}/{len(qs)} questions; no relevant images counts as not applicable.'), step(3, 'Assessed', assessed_done, total, accuracy, checked=compared, active=paper.id in active, valid=inventory and bound, attempted=any((q.id in analyses for q in qs)), detail=f'{compared}/{total} current final comparisons; {assessed_done}/{total} subparts complete; current curriculum, content and image checks required.'), step(4, 'Tutor practice released', released, total, href, valid=inventory and bound, detail=f'{released}/{total} released; {excluded} excluded (retained in required total). Formal-exam publication is separate.')]
        result[paper.id].append(dict(paperId=str(paper.id), paperTitle=paper.title, steps=steps, excluded=excluded, formalExamPublished=paper.review_state == 'published'))
        for role in ('scheme', 'report'):
            did = getattr(w, role + '_document_id')
            vid = getattr(w, role + '_version_id')
            if not did or did not in selected:
                continue
            checklabel = 'Evidence checked' if role == 'scheme' else 'Guidance checked'
            role_bound = bool(did in docs and latest[did].id == vid and (paper.id in latest) and (latest[paper.id].id == w.paper_version_id))
            result[did].append(dict(paperId=str(paper.id), paperTitle=paper.title, steps=[extracted(did, vid, href), step(2, 'Linked to paper', int(role_bound), 1, href, valid=role_bound, detail='Source identity/version bound to ' + paper.title), step(3, checklabel, checked[role], check_total, accuracy, active=paper.id in active, valid=inventory and bound, attempted=any((q.id in analyses for q in qs)))], excluded=excluded))
    for did in selected:
        doc = docs.get(did)
        if not doc or doc.kind not in {'past_paper', 'mark_scheme', 'examiner_report'}:
            continue
        if not result[did]:
            href = '/admin/exam-documents'
            v = latest.get(did)
            parent = docs.get(doc.source_document_id)
            if parent and parent.kind != 'past_paper':
                parent = None
            identity = bool(parent and doc.publication_year and doc.exam_session and doc.component and all(
                getattr(doc, field) == getattr(parent, field) for field in
                ('course_id', 'subject_id', 'publication_year', 'exam_session', 'component', 'variant')))
            if parent:
                href = f'/admin/exam-documents/review/{parent.id}'
            orphan_steps = [
                step(1, 'Extracted', 0, 1, href, active=bool(v and v.status in {'queued','processing'}), valid=False,
                     detail='Start a question review workspace and reconcile the expected inventory.'),
                step(2, 'Images reviewed', 0, 1, href), step(3, 'Assessed', 0, 1, href),
                step(4, 'Tutor practice released', 0, 1, href)
            ] if doc.kind == 'past_paper' else [
                extracted(did, v.id if v else None, href),
                step(2, 'Linked to paper', int(identity), 1, href, valid=not parent or identity,
                     detail='Matching paper association recorded at upload; exact evidence is not checked yet.' if identity else 'Associate the correct source paper and verify its session/component identity.'),
                step(3, 'Guidance checked' if doc.kind == 'examiner_report' else 'Evidence checked', 0, 1, href)
            ]
            result[did].append(dict(paperId=str(parent.id) if parent else None,
                paperTitle=parent.title if parent else 'Not linked to a review workspace', steps=orphan_steps))

    return dict(policy='past-paper-workflow-v1', documents=[dict(documentId=str(did), scopes=scopes) for did, scopes in result.items() if did in selected])
