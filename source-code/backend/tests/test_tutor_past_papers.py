import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select, func

from app.config import Settings, get_settings
from app.database import get_db
from app.main import app
from app.errors import DomainError
from app.models import (Assessment, AssessmentAnswer, AssessmentInteraction, AssessmentResult,
    CurriculumPlan, CurriculumPlanTopic, OfficialPaperReviewQuestion, StudentProfile,
    StudentProgression, StudentSubject, TextbookTopicContentVersion, TutorPaperRelease, User)
from app.services import tutor_past_papers as service
from test_auth_integration import auth_client  # noqa: F401
from test_official_paper_review_workspace import _setup, _question


@pytest.mark.parametrize('text,active,expected', [
    ('Can you ask me a question from igcse chemistry paper?', False, 'select'),
    ('Discuss 1C question 3(a)', False, 'select'),
    ('Show approved answer', True, 'reveal'), ('Give me a hint', True, 'hint'),
    ('Next question', False, 'select'), ('My answer: Pencil is insoluble.', True, 'answer'),
    ('What is evaporation?', False, None), ('Can you explain this?', True, 'help'),
    ('Create a mock exam', False, 'mock'), ('Stop past-paper practice', True, 'stop'),
])
def test_intent_routes_before_textbook_retrieval(text, active, expected):
    assert service.intent(text, active) == expected


def _ready(auth_client, monkeypatch):
    client, headers, db, paper, scheme, report, topic = _setup(auth_client)
    root = f'/api/v1/admin/official-paper-reviews/{paper[0].id}'
    assert client.post(root + '/start', headers=headers, json={'schemeDocumentId': str(scheme[0].id), 'expectedQuestionCount': 1}).status_code == 200
    saved = client.post(root + '/questions', headers=headers, json=_question(paper, scheme, topic))
    assert saved.status_code == 200, saved.text
    admin = db.get(User, paper[0].uploaded_by)
    token = uuid.uuid4().hex
    parent = User(username='parent-'+token, display_name='Test Parent', role='parent', password_hash=admin.password_hash, must_change_password=False)
    child = User(username='student-'+token, display_name='Practice Student', role='student', password_hash=admin.password_hash, must_change_password=False)
    db.add_all([parent,child]); db.flush()
    db.add(StudentProfile(student_id=child.id,parent_id=parent.id));db.flush()
    db.add_all([StudentSubject(student_id=child.id,subject_id='chemistry'), StudentProgression(student_id=child.id,course_id='igcse',grade=10,term=1,is_current=True)])
    db.add(TextbookTopicContentVersion(topic_id=topic.id, version_number=1, status='published', source_manifest=[],extraction_manifest={},published_by=admin.id))
    version = (db.scalar(select(func.max(CurriculumPlan.version_number)).where(CurriculumPlan.subject_id=='chemistry')) or 0)+1
    for old in db.scalars(select(CurriculumPlan).where(CurriculumPlan.subject_id=='chemistry',CurriculumPlan.status=='published')).all():old.status='superseded'
    plan = CurriculumPlan(course_id='igcse',subject_id='chemistry',textbook_id=topic.textbook_id, version_number=version,status='published',created_by=admin.id,published_by=admin.id)
    db.add(plan);db.flush();db.add(CurriculumPlanTopic(plan_id=plan.id,topic_id=topic.id,grade=10,term=1)); db.commit()
    settings=Settings(database_password='test',_env_file=None,tutor_text_enabled=True,tutor_tools_enabled=True,
        tutor_release_gates_required=False,tutor_past_paper_chat_enabled=True,tutor_past_paper_chat_student_ids=[child.id])
    app.dependency_overrides[get_settings]=lambda:settings
    monkeypatch.setattr('app.config.get_settings',lambda:settings)
    return client,headers,db,root,child,topic,paper,scheme,settings


def _login_student(client, child, topic):
    login=client.post('/api/v1/auth/login',json={'username':child.username,'password':'correct horse battery staple'})
    assert login.status_code==200,login.text
    headers={'X-CSRF-Token':login.json()['csrfToken']}
    profile=client.post('/api/v1/tutoring/profiles',headers=headers,json={
        'name':'Test Tutor','presentation':'neutral','avatarCode':'akuru-spark','voiceCode':'bright-companion',
        'tone':'encouraging','friendliness':'high','enthusiasm':'medium','speed':'medium',
        'communicationCharacter':'balanced','explanationDepth':'standard','teachingStyle':'guided'})
    assert profile.status_code==201,profile.text
    session=client.post('/api/v1/tutoring/sessions',headers=headers,json={'subjectId':'chemistry',
        'topicRef':topic.public_ref,'profileRef':profile.json()['profileRef'],'requestKey':uuid.uuid4().hex})
    assert session.status_code==201,session.text
    return headers,session.json()['sessionRef']


@pytest.mark.integration
def test_release_permissions_validation_and_source_staleness(auth_client,monkeypatch):
    client,headers,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
    path=root+'/questions/1/chat-release'
    payload={'partLabel':'a','revision':1,'confirmSelfContained':True}
    assert client.post(path,json=payload).status_code==403
    assert client.post(path,headers=headers,json={**payload,'revision':9}).status_code==409
    assert client.post(path,headers=headers,json={**payload,'confirmSelfContained':False}).status_code==409
    released=client.post(path,headers=headers,json=payload)
    assert released.status_code==200,released.text
    assert client.post(path,headers=headers,json=payload).json()==released.json()
    assert len(service.eligible(db,child.id,'chemistry'))==1
    assert client.get(root+'/chat-releases').json()[0]['current'] is True
    q=db.scalar(select(OfficialPaperReviewQuestion).where(OfficialPaperReviewQuestion.number=='1',OfficialPaperReviewQuestion.workspace_id.is_not(None)))
    q.revision+=1; db.commit()
    assert service.eligible(db,child.id,'chemistry')==[]
    assert client.get(root+'/chat-releases').json()[0]['current'] is False


@pytest.mark.integration
def test_chat_select_hint_reveal_next_and_private_sources_without_model_calls(auth_client,monkeypatch):
    client,headers,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
    assert client.post(root+'/questions/1/chat-release',headers=headers,json={'partLabel':'a','revision':1,'confirmSelfContained':True}).status_code==200
    sh,ref=_login_student(client,child,topic)
    path=f'/api/v1/tutoring/sessions/{ref}/agent-turns'
    def send(message,key=None):
        r=client.post(path,headers=sh,json={'message':message,'requestKey':key or uuid.uuid4().hex})
        assert r.status_code==200,r.text
        return r.json()
    monkeypatch.setattr('app.services.tutor_agent._invoke',lambda *a,**kw:pytest.fail('Selection/hints/reveal must not invoke a model'))
    key=uuid.uuid4().hex
    answer=send('Can you ask me a question from igcse chemistry paper?',key)
    assert answer['model']=='approved-exam-tools-v1'
    assert 'could not find enough' not in answer['content']
    state=answer['pastPaper'];aid=state['practice']['assessmentId'];qid=state['practice']['question']['id']
    assert state['practice']['question']['rubric'] is None
    assert state['markingGuidance']==[]
    assert [s['label'] for s in state['sources']]==['Paper · Page 1']
    assert send('Can you ask me a question from igcse chemistry paper?',key)['turnRef']==answer['turnRef']
    assert db.scalar(select(func.count()).select_from(Assessment).where(Assessment.student_id==child.id))==1
    assert send('Next question')['pastPaper'] is None
    assert send('Give me a hint')['pastPaper']['markingGuidance']==[]
    scheme_url=f'/api/v1/tutoring/sessions/{ref}/past-paper/assets/{scheme[4].id}'
    assert client.get(scheme_url).status_code==404
    mismatch=send('Show approved answer for question 1(b)')
    assert mismatch['pastPaper'] is None and 'different question or subpart' in mismatch['content']
    assert db.scalar(select(func.count()).select_from(AssessmentInteraction).where(AssessmentInteraction.assessment_id==uuid.UUID(aid),AssessmentInteraction.kind=='worked_answer'))==0
    revealed=send('Show approved answer')['pastPaper']
    assert revealed['state']=='revealed' and len(revealed['markingGuidance'])==2
    assert [s['label'] for s in revealed['sources']]==['Paper · Page 1']
    assert client.get(scheme_url).status_code==404  # no adjacent unreleased answers after reveal
    assert db.scalar(select(func.count()).select_from(AssessmentAnswer).where(AssessmentAnswer.assessment_id==uuid.UUID(aid)))==0
    assert db.scalar(select(func.count()).select_from(AssessmentResult).where(AssessmentResult.assessment_id==uuid.UUID(aid)))==0
    assert db.scalar(select(AssessmentInteraction).where(AssessmentInteraction.assessment_id==uuid.UUID(aid),AssessmentInteraction.kind=='worked_answer'))
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/past-paper').json()['answerRevealed'] is True
    assert send('Next question')['pastPaper']['state']=='awaiting_answer'
    assert send('Create a mock exam')['pastPaper'] is None
    assert 'not available' in send('Create a mock exam')['content']
    # Account gating applies to direct assessment endpoints too.
    settings.tutor_past_paper_chat_student_ids=[]
    assert client.get(f'/api/v1/assessments/{aid}/assets/{paper[5].id}').status_code==403
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/past-paper').status_code==403


@pytest.mark.integration
def test_saved_answer_respects_marking_gate_and_formal_assessment_block(auth_client,monkeypatch):
    client,headers,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
    assert client.post(root+'/questions/1/chat-release',headers=headers,json={'partLabel':'a','revision':1,'confirmSelfContained':True}).status_code==200
    sh,ref=_login_student(client,child,topic)
    path=f'/api/v1/tutoring/sessions/{ref}/agent-turns'
    def send(text,key=None):
        return client.post(path,headers=sh,json={'message':text,'requestKey':key or uuid.uuid4().hex})
    first=send('Ask me a question from an igcse chemistry paper').json()['pastPaper']
    aid=uuid.UUID(first['practice']['assessmentId'])
    monkeypatch.setattr('app.services.tutor_agent._invoke',lambda *a,**kw:pytest.fail('An unreleased marking model must not be called'))
    monkeypatch.setattr('app.services.evaluations.automatic_feedback_allowed',lambda *a,**kw:(False,'Missing evaluation'))
    submitted_key=uuid.uuid4().hex
    saved=send('My answer: One spot means one dye.',submitted_key)
    assert saved.status_code==200,saved.text
    assert 'answer is saved' in saved.json()['content']
    assert saved.json()['pastPaper']['state']=='answered'
    assert send('My answer: One spot means one dye.',submitted_key).json()['turnRef']==saved.json()['turnRef']
    assert db.scalar(select(func.count()).select_from(AssessmentAnswer).where(AssessmentAnswer.assessment_id==aid))==1
    assert db.scalar(select(func.count()).select_from(AssessmentResult).where(AssessmentResult.assessment_id==aid))==0
    assert 'No score' in saved.json()['content']
    assert send('Show approved answer').json()['pastPaper']['markingGuidance']
    following=send('Next question').json()['pastPaper']
    assessment=db.get(Assessment,uuid.UUID(following['practice']['assessmentId']))
    assessment.mode='mock';db.commit()
    assert send('Show approved answer').status_code==403
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/past-paper').status_code==403
    assert client.get(f'/api/v1/assessments/{assessment.id}/assets/{paper[5].id}').status_code==403


@pytest.mark.integration
def test_coverage_revocation_and_wrong_student_cannot_open_sources(auth_client,monkeypatch):
    client,headers,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
    assert client.post(root+'/questions/1/chat-release',headers=headers,json={'partLabel':'a','revision':1,'confirmSelfContained':True}).status_code==200
    sh,ref=_login_student(client,child,topic)
    path=f'/api/v1/tutoring/sessions/{ref}/agent-turns'
    request={'message':'Discuss 1C question 1(a)','requestKey':uuid.uuid4().hex}
    selected=client.post(path,headers=sh,json=request)
    assert selected.status_code==200,selected.text
    assert selected.json()['pastPaper']['questionLabel']=='1(a)'
    assert client.post(path,json={**request,'requestKey':uuid.uuid4().hex}).status_code==403
    for text in ['Discuss 2C question 1(a)','Discuss 1C question 1(a) in 2020','Ask me a physics paper question']:
        result=client.post(path,headers=sh,json={'message':text,'requestKey':uuid.uuid4().hex})
        assert result.status_code==200,result.text
        assert result.json()['pastPaper'] is None
    db.query(CurriculumPlanTopic).filter_by(topic_id=topic.id).delete();db.commit()
    with pytest.raises(DomainError) as blocked:
        service.eligible(db,child.id,'chemistry')
    assert blocked.value.code == 'assessment_coverage_not_ready'
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/past-paper').status_code==409
    # A genuine separate login cannot use the first Student's session reference.
    parent=db.get(User,db.get(StudentProfile,child.id).parent_id)
    assert client.post('/api/v1/auth/login',json={'username':parent.username,'password':'correct horse battery staple'}).status_code==200
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/past-paper').status_code==403


@pytest.mark.integration
def test_sibling_student_cannot_read_another_students_practice(auth_client,monkeypatch):
    client,headers,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
    assert client.post(root+'/questions/1/chat-release',headers=headers,json={'partLabel':'a','revision':1,'confirmSelfContained':True}).status_code==200
    sh,ref=_login_student(client,child,topic)
    first=client.post(f'/api/v1/tutoring/sessions/{ref}/agent-turns',headers=sh,json={'message':'Ask me a chemistry paper question','requestKey':uuid.uuid4().hex}).json()['pastPaper']
    sibling=User(username='sibling-'+uuid.uuid4().hex,display_name='Sibling',role='student',password_hash=child.password_hash,must_change_password=False)
    db.add(sibling);db.flush();db.add(StudentProfile(student_id=sibling.id,parent_id=db.get(StudentProfile,child.id).parent_id));db.commit()
    settings.tutor_past_paper_chat_student_ids.append(sibling.id)
    assert client.post('/api/v1/auth/login',json={'username':sibling.username,'password':'correct horse battery staple'}).status_code==200
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/past-paper').status_code==404
    assert client.get(f'/api/v1/assessments/{first["practice"]["assessmentId"]}/assets/{paper[5].id}').status_code==404


@pytest.mark.integration
def test_released_marking_reuses_two_pass_router_quotas_and_preserves_unaided_attempt(auth_client,monkeypatch):
    from app.ai.base import AIResult, AIUsage
    from app.models import AIInvocation, StudentAIUsage
    client,headers,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
    assert client.post(root+'/questions/1/chat-release',headers=headers,json={'partLabel':'a','revision':1,'confirmSelfContained':True}).status_code==200
    sh,ref=_login_student(client,child,topic)
    path=f'/api/v1/tutoring/sessions/{ref}/agent-turns'
    def send(text,key=None):
        response=client.post(path,headers=sh,json={'message':text,'requestKey':key or uuid.uuid4().hex})
        assert response.status_code==200,response.text
        return response.json()
    selected=send('Ask me a chemistry paper question')['pastPaper']
    observed=[]
    monkeypatch.setattr('app.services.evaluations.automatic_feedback_allowed',lambda *a,**kw:(True,''))
    def generate(router,request,**kwargs):
        import json
        data=json.loads(request.task);observed.append((request.purpose,request.prompt_name,request.metadata))
        decisions=[dict(pointId=p['pointId'],criterion=p['criterion'],maxMarks=p['maxMarks'],awarded=True,marksAwarded=p['maxMarks'],studentEvidence='One spot; separated dyes.',rationale='The student explicitly matches the criterion.',confidence=.99) for p in data['officialMarkingPoints']]
        if request.output_type.__name__=='AssessmentPassOne':output=request.output_type(decisions=decisions,overallConfidence=.99)
        else:output=request.output_type(decisions=decisions,confidence=.99,improvedAnswer='One spot; separated dyes.',teachingExplanation='Your response identifies the spots and dyes.')
        return AIResult(output=output,provider='fake',model='fake-assessment',response_id='test-only',usage=AIUsage(input_tokens=50,output_tokens=20,total_tokens=70),latency_ms=1,attempt_count=1)
    monkeypatch.setattr('app.ai.router.AIAccountRouter.generate',generate)
    reply=send('My answer: One spot; separated dyes.')
    assert len(observed)==2
    assert all(purpose=='assessment' and metadata['session_ref']==ref for purpose,_,metadata in observed)
    assert reply['pastPaper']['practice']['question']['result']['awardedMarks']==2
    assert db.scalar(select(func.count()).select_from(AIInvocation).where(AIInvocation.actor_id==child.id,AIInvocation.purpose=='assessment'))==2
    assert db.scalar(select(func.count()).select_from(StudentAIUsage).where(StudentAIUsage.student_id==child.id,StudentAIUsage.dimension=='request',StudentAIUsage.event_type=='reserve'))==2
    feedback=send('Show approved answer')['pastPaper']
    assert feedback['answerRevealed'] is False
    assert db.scalar(select(func.count()).select_from(AssessmentInteraction).where(AssessmentInteraction.assessment_id==uuid.UUID(selected['practice']['assessmentId']),AssessmentInteraction.kind=='worked_answer'))==0


@pytest.mark.parametrize('text,number,part',[
    ('Discuss 1C question 3(a)','3','a'),('Show answer for Q3c(ii)','3','c(ii)'),
    ('Question 3 in June 2025','3',None),('Question 3 part b','3','b'),('What about part c?',None,'c'),
])
def test_exact_question_identity_does_not_confuse_words_with_labels(text,number,part):
    found=service.identity(text)
    assert found['number']==number and found['part']==part


@pytest.mark.parametrize('component', ['1B', '2BR', '1C', '2CR'])
def test_past_paper_identity_preserves_biology_and_chemistry_components(component):
    identity = service.identity(f'June 2025 {component} question 2(b)')
    assert identity == dict(component=component, year=2025, session='june', number='2', part='b')


@pytest.mark.integration
@pytest.mark.parametrize('change', ['publication', 'visual'])
def test_manual_release_also_invalidates_on_textbook_or_visual_changes(auth_client, monkeypatch, change):
    from app.models import Textbook, DocumentAsset
    import copy
    client,headers,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
    result=client.post(root+'/questions/1/chat-release',headers=headers,json=dict(partLabel='a',revision=1,confirmSelfContained=True))
    assert result.status_code==200,result.text
    if change=='publication':
        book=db.get(Textbook,topic.textbook_id);book.status='archived'
    else:
        q=db.scalar(select(OfficialPaperReviewQuestion))
        asset=db.get(DocumentAsset,uuid.UUID(q.review_data['visualAssetIds'][0]))
        metadata=copy.deepcopy(asset.asset_metadata);metadata['altText']='Materially changed reviewed label.';asset.asset_metadata=metadata
    db.commit()
    assert client.get(root+'/chat-releases').json()[0]['current'] is False
    assert service.eligible(db,child.id,'chemistry')==[]
