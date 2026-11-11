"""No paid calls: safe partial release, curriculum freshness and truthful progress."""
import copy, uuid
import pytest
from sqlalchemy import select, func, event
from app.models import (DocumentBlock, OfficialPaperReviewQuestion, OfficialPaperReviewWorkspace,
    TextbookTopic, TextbookTopicContentVersion, RetrievalChunk, TutorPaperRelease, OfficialQuestionAnalysis, User)
from app.config import get_settings
from app.ai.fake import FakeAIProvider
from app.services import accuracy_jobs, paper_workflow, tutor_past_papers, paper_curriculum
from test_auth_integration import auth_client  # noqa
from test_accuracy_reassessment_jobs import setup
from test_official_paper_review_workspace import _source


def prepared(auth_client, sibling=False):
    c,h,db,root,q,req,out,storage=setup(auth_client)
    row=db.scalar(select(OfficialPaperReviewQuestion));w=db.get(OfficialPaperReviewWorkspace,row.workspace_id)
    data=copy.deepcopy(row.review_data)
    for part in data['parts']:
        for role in ('paper','scheme'):
            block=db.scalar(select(DocumentBlock).where(DocumentBlock.document_version_id==getattr(w,role+'_version_id')))
            part[role+'Sources'][0]['blockId']=str(block.id)
    if sibling:
        second=copy.deepcopy(data['parts'][0]);second.update(label='b',prompt='State a property of the sample.',status='unreviewed')
        data['parts'].append(second);data['marks']+=second['marks']
        low=copy.deepcopy(out['parts'][0]);low.update(label='b',percent=70);out['parts'].append(low)
    row.review_data=data;w.expected_question_count=1
    topic=db.scalar(select(TextbookTopic).where(TextbookTopic.public_ref==data['parts'][0]['topicRefs'][0]))
    actor=db.scalar(select(User).where(User.username==auth_client[1]))
    source=_source(db,actor,uuid.uuid4().hex,'textbook');source[0].review_state='published'
    pub=TextbookTopicContentVersion(topic_id=topic.id,version_number=1,published_by=actor.id,
        source_manifest=[dict(documentVersionId=str(source[1].id),role='primary')],extraction_manifest={})
    db.add(pub);db.flush()
    chunk=RetrievalChunk(document_id=source[0].id,document_version_id=source[1].id,
        topic_id=topic.id,topic_content_version_id=pub.id,group_id=topic.group_id,
        course_id='igcse',subject_id='chemistry',source_type='textbook_section',source_item_id=source[3].id,
        source_ordinal=0,content='Chromatography separates soluble dyes; one spot indicates one substance.',
        page_number=1,bounding_box={},content_hash='a'*64,embedding_model='fixture',embedding=[0.0]*256)
    db.add(chunk);db.commit()
    for p in out['parts']:
        p.update(selfContained=True,curriculum=dict(coverage='supported',percent=96,
            reason='Published evidence explains chromatography and separated dyes.',chunkIds=[str(chunk.id)]))
    q=c.get(root).json()['questions'][0]
    req.update(workflowPolicy='final-source-accuracy-v2',expectedRevision=q['revision'],expectedContentHash=q['analysisContentHash'],expectedAnalysisVersion=q['analysisVersion'])
    return c,h,db,root,q,req,out,storage,chunk,pub


def run(c,h,db,root,req,out,storage):
    r=c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]});assert r.status_code==202,r.text
    accuracy_jobs.process_next(db,get_settings(),storage,generator=FakeAIProvider(out).generate)
    job=c.get(root+'/accuracy-jobs').json()[0];assert job['status']=='completed',job
    return job


@pytest.mark.integration
def test_partial_release_retry_withdrawal_and_progress(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client,True)
    job=run(c,h,db,root,req,out,storage)
    assert job['result']['tutorReleases'][0]['enabled'],job
    assert not job['result']['tutorReleases'][1]['enabled']
    releases=c.get(root+'/chat-releases').json();assert len(releases)==1 and releases[0]['current']
    assert c.get(root).json()['questions'][0]['status']=='unreviewed'
    assert c.post(root+'/auto-tutor-release',json={}).status_code==403
    assert c.post(root+'/auto-tutor-release',headers=h,json={}).status_code==200
    assert db.scalar(select(func.count()).select_from(TutorPaperRelease))==1
    row=db.scalar(select(OfficialPaperReviewQuestion));paper_id=uuid.UUID(root.split('/')[-1])
    workflow=paper_workflow.summaries(db,[paper_id])['documents'][0]['scopes'][0]
    assert workflow['steps'][3]['state']=='attention' and workflow['steps'][3]['completed']==1
    assert workflow['steps'][3]['total']==2
    assert c.post(root+'/questions/1/chat-release',headers=h,json=dict(partLabel='a',revision=row.revision,confirmSelfContained=True,enabled=False)).status_code==200
    c.post(root+'/auto-tutor-release',headers=h,json={})
    assert not c.get(root+'/chat-releases').json()[0]['current']


@pytest.mark.integration
@pytest.mark.parametrize('mode',['threshold','uncertain','conflict','dependent','unseen'])
def test_confidence_and_mapping_safety_gates(auth_client,mode):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    p=out['parts'][0]
    if mode=='threshold':p['percent']=75
    if mode=='uncertain':p['curriculum']['percent']=80
    if mode=='conflict':p['curriculum'].update(coverage='partial_or_uncertain',chunkIds=[])
    if mode=='dependent':p['selfContained']=False
    if mode=='unseen':p['curriculum']['chunkIds']=[str(uuid.uuid4())]
    c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]})
    accuracy_jobs.process_next(db,get_settings(),storage,generator=FakeAIProvider(out).generate)
    if mode=='unseen':assert c.get(root+'/accuracy-jobs').json()[0]['errorCode']=='curriculum_unseen_evidence'
    else:assert c.get(root+'/accuracy-jobs').json()[0]['status']=='completed'
    assert db.scalar(select(func.count()).select_from(TutorPaperRelease))==0
    assert c.get(root).json()['questions'][0]['data']['parts'][0]['topicRefs']==q['data']['parts'][0]['topicRefs']


@pytest.mark.integration
def test_publication_change_and_companion_scoped_checks(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    run(c,h,db,root,req,out,storage)
    paper_id=uuid.UUID(root.split('/')[-1]);w=db.scalar(select(OfficialPaperReviewWorkspace))
    endpoint='/api/v1/admin/official-paper-reviews/workflow';ids=[paper_id,w.scheme_document_id,w.report_document_id]
    r=c.get(endpoint,params=[('documentId',str(i))for i in ids]);assert r.status_code==200,r.text
    by_id={d['documentId']:d for d in r.json()['documents']}
    assert all(s['state']=='complete'for s in by_id[str(paper_id)]['scopes'][0]['steps']),by_id
    assert by_id[str(w.report_document_id)]['scopes'][0]['steps'][2]['label']=='Guidance checked'
    assert by_id[str(w.scheme_document_id)]['scopes'][0]['steps'][2]['state']=='complete'
    pub.status='superseded';db.commit()
    assert not c.get(root+'/chat-releases').json()[0]['current']
    wf=c.get(endpoint,params={'documentId':str(paper_id)}).json()['documents'][0]['scopes'][0]
    assert wf['steps'][2]['state']!='complete' and wf['steps'][3]['completed']==0
    c.post('/api/v1/auth/logout',headers=h)
    assert c.get(endpoint,params={'documentId':str(paper_id)}).status_code==401


@pytest.mark.integration
def test_cross_subject_candidates_excluded(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    row=db.scalar(select(OfficialPaperReviewQuestion));w=db.get(OfficialPaperReviewWorkspace,row.workspace_id)
    assert paper_curriculum.candidates(db,w,row)[0]['chunkId']==str(chunk.id)
    chunk.subject_id='biology';db.commit()
    assert paper_curriculum.candidates(db,w,row)==[]


@pytest.mark.integration
def test_release_failure_preserves_paid_assessment(auth_client,monkeypatch):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    def fail(*args,**kwargs):raise RuntimeError('simulated release failure')
    monkeypatch.setattr(tutor_past_papers,'auto_release',fail)
    job=run(c,h,db,root,req,out,storage)
    assert job['result']['tutorReleases'][0]['code']=='release_retry_required'
    assert db.scalar(select(func.count()).select_from(OfficialQuestionAnalysis))==1


@pytest.mark.integration
def test_aggregation_query_count_is_bounded(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    w=db.scalar(select(OfficialPaperReviewWorkspace));queries=[]
    def count(*args):queries.append(1)
    event.listen(db.get_bind(),'before_cursor_execute',count)
    try:paper_workflow.summaries(db,[w.paper_document_id,w.scheme_document_id,w.report_document_id])
    finally:event.remove(db.get_bind(),'before_cursor_execute',count)
    assert len(queries)<=13,len(queries)


@pytest.mark.integration
def test_admin_context_matches_worker_and_rejects_public_access(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    r=c.get(root+'/questions/1/accuracy-context');assert r.status_code==200,r.text
    context=r.json();assert context['revision']==q['revision']
    assert context['curriculumSources'][0]['chunkId']==str(chunk.id)
    assert context['pages'] and 'untrusted' in context['instructions']
    c.post('/api/v1/auth/logout',headers=h)
    assert c.get(root+'/questions/1/accuracy-context').status_code==401


@pytest.mark.integration
def test_publication_change_during_paid_call_rejects_entire_result(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]})
    def changed(request):
        result=FakeAIProvider(out).generate(request)
        pub.status='superseded';db.commit()
        return result
    accuracy_jobs.process_next(db,get_settings(),storage,generator=changed)
    assert c.get(root+'/accuracy-jobs').json()[0]['errorCode']=='curriculum_publication_changed'
    assert db.scalar(select(func.count()).select_from(OfficialQuestionAnalysis))==0


@pytest.mark.integration
def test_undecided_mapping_is_filled_only_with_exact_high_confidence_evidence(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    row=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(row.review_data)
    data['parts'][0].update(coverage='unreviewed',topicRefs=[],coverageReason='',textbookEvidence=[])
    row.review_data=data;db.commit()
    q=c.get(root).json()['questions'][0]
    req.update(expectedRevision=q['revision'],expectedContentHash=q['analysisContentHash'])
    run(c,h,db,root,req,out,storage)
    saved=c.get(root).json()['questions'][0]
    assert saved['data']['parts'][0]['coverage']=='supported'
    assert saved['data']['parts'][0]['topicRefs']==[db.get(TextbookTopic,pub.topic_id).public_ref]
    assert saved['accuracyAnalysis']['isCurrent']


@pytest.mark.integration
def test_no_images_and_incomplete_inventory_never_claim_full_release(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    row=db.scalar(select(OfficialPaperReviewQuestion));w=db.get(OfficialPaperReviewWorkspace,row.workspace_id)
    data=copy.deepcopy(row.review_data);data['visualAssetIds']=[];data['sharedStem']='Consider the sample.'
    for p in data['parts']:p.update(visualAssetIds=[],prompt='Describe the separation.')
    row.review_data=data;db.commit()
    result=paper_workflow.summaries(db,[w.paper_document_id])['documents'][0]['scopes'][0]
    assert result['steps'][1]['state']=='complete'
    w.expected_question_count=2;db.commit()
    result=paper_workflow.summaries(db,[w.paper_document_id])['documents'][0]['scopes'][0]
    assert all(step['state']!='complete'for step in result['steps'])


@pytest.mark.integration
def test_verified_no_comment_and_shared_report_have_independent_paper_scopes(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    for estimate in [out['question'],*out['parts']]:
        next(v for v in estimate['sourceChecks']if v['role']=='report')['status']='no_comment'
    run(c,h,db,root,req,out,storage)
    w=db.scalar(select(OfficialPaperReviewWorkspace));actor=db.scalar(select(User).where(User.username==auth_client[1]))
    other=_source(db,actor,uuid.uuid4().hex,'past_paper')
    db.add(OfficialPaperReviewWorkspace(paper_document_id=other[0].id,paper_version_id=other[1].id,
        report_document_id=w.report_document_id,report_version_id=w.report_version_id,
        created_by=actor.id,expected_question_count=1));db.commit()
    scopes=paper_workflow.summaries(db,[w.report_document_id])['documents'][0]['scopes']
    assert len(scopes)==2
    assert {s['steps'][2]['state']for s in scopes}=={'complete','attention'}


@pytest.mark.integration
def test_ai_disagreement_with_manual_outside_coverage_is_saved_as_conflict(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    row=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(row.review_data)
    data['parts'][0].update(coverage='outside_current_coverage',topicRefs=[],textbookEvidence=[],coverageReason='')
    row.review_data=data;db.commit()
    q=c.get(root).json()['questions'][0];req.update(expectedContentHash=q['analysisContentHash'])
    run(c,h,db,root,req,out,storage)
    saved=c.get(root).json()['questions'][0]
    assert saved['data']['parts'][0]['coverage']=='outside_current_coverage'
    assert saved['accuracyAnalysis']['parts'][0]['curriculum']['conflict']
    assert not c.get(root+'/chat-releases').json()


@pytest.mark.integration
def test_explicit_manual_low_confidence_adjudication_releases_without_extra_click(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    out['parts'][0]['percent']=70
    run(c,h,db,root,req,out,storage)
    assert c.get(root+'/chat-releases').json()==[]
    current=c.get(root).json()['questions'][0]
    data=current['data'];data['parts'][0]['status']='approved'
    response=c.post(root+'/questions',headers=h,json=dict(number='1',expectedRevision=current['revision'],status='unreviewed',data=data))
    assert response.status_code==200,response.text
    releases=c.get(root+'/chat-releases').json()
    assert len(releases)==1 and releases[0]['current']
    # A newer, still-low assessment is not silently adjudicated by the earlier decision.
    current=c.get(root).json()['questions'][0]
    req.update(requestId=str(uuid.uuid4()),expectedRevision=current['revision'],expectedContentHash=current['analysisContentHash'],expectedAnalysisVersion=current['analysisVersion'])
    run(c,h,db,root,req,out,storage)
    assert not c.get(root+'/chat-releases').json()[0]['current']


@pytest.mark.integration
def test_companion_initial_states_and_upload_association_progress_independently(auth_client):
    from test_official_paper_review_workspace import _setup
    c,h,db,paper,scheme,report,topic=_setup(auth_client)
    scheme[0].source_document_id=None;scheme[1].status='uploaded';db.commit()
    def states():return [s['state']for s in paper_workflow.summaries(db,[scheme[0].id])['documents'][0]['scopes'][0]['steps']]
    assert states()==['not_started','not_started','not_started']
    scheme[1].status='processing';db.commit()
    assert states()==['processing','not_started','not_started']
    scheme[1].status='completed';scheme[0].source_document_id=paper[0].id;db.commit()
    assert states()==['complete','complete','not_started']
    scheme[0].component='2C';db.commit()
    assert states()==['complete','attention','not_started']


@pytest.mark.integration
def test_legacy_assessment_request_never_silently_enables_automatic_release(auth_client):
    c,h,db,root,q,req,out,storage,chunk,pub=prepared(auth_client)
    req.pop('workflowPolicy')
    run(c,h,db,root,req,out,storage)
    assert db.scalar(select(func.count()).select_from(TutorPaperRelease))==0
    assert c.get(root).json()['questions'][0]['accuracyAnalysis']['isCurrent']
