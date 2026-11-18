import copy
import json
import uuid
import pytest
from sqlalchemy import select
from app.ai.base import AIResult, AIUsage
from app.errors import DomainError
from app.models import OfficialPaperReviewQuestion, TutorQuestionSet, TutorPaperRelease
from app.services import tutor_question_sets as sets
from test_auth_integration import auth_client  # noqa: F401
from test_tutor_past_papers import _ready, _login_student


@pytest.mark.parametrize('message,kind,count',[
    ('Give me 5 questions from Coordination','official',5),
    ('Can you generate new questions from Topic 6?','generated',1),
    ('Generate three difficult questions from Topic 6','generated',3),
    ('Give me 20 past-paper questions from Topic 1','official',20)])
def test_count_intent(message,kind,count):
    assert sets.request_spec(message)['kind']==kind
    assert sets.request_spec(message)['count']==count


def test_limits_and_teaching():
    with pytest.raises(DomainError):sets.request_spec('Give me 100 questions from Topic 1')
    assert sets.request_spec('What is a cell?') is None
    assert sets.request_spec('Can you ask me a question from igcse chemistry paper?') is None


def begin(auth_client,monkeypatch,manual=False):
    client,headers,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
    if manual:
        q=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(q.review_data)
        data['parts'][0]['assessmentReadiness']='manual_only';data['parts'][0]['assessmentReadinessReason']='Semantic answer.'
        q.review_data=data;db.commit()
    r=client.post(root+'/questions/1/chat-release',headers=headers,json={'partLabel':'a','revision':1,'confirmSelfContained':True})
    assert r.status_code==200,r.text
    sh,ref=_login_student(client,child,topic)
    def send(message,key=None):
        r=client.post(f'/api/v1/tutoring/sessions/{ref}/agent-turns',headers=sh,json={'message':message,'requestKey':key or uuid.uuid4().hex})
        assert r.status_code==200,r.text
        return r.json()
    return client,db,child,topic,ref,send


def feedback(request):
    data=json.loads(request.task);answer=data['studentAnswer']
    value=request.output_type(matches=[{'pointId':p['code'],'matched':True,'evidence':answer,'reason':'Meaning matches.'} for p in data['question']['markingPoints']],
        correctPoints=['Identifies the observation.'],mistakes=[],omissions=[],improvedAnswer='One spot indicates a pure substance; multiple spots indicate a mixture.',
        explanation='Link each observation to a conclusion.',uncertainty='Indicative interpretation.')
    return AIResult(value,'fixture','fixture-formative',None,AIUsage(10,20,30),1,1)


@pytest.mark.integration
def test_manual_feedback_resume_replay_and_completion(auth_client,monkeypatch):
    client,db,child,topic,ref,send=begin(auth_client,monkeypatch,True)
    calls=[]
    def invoke(db,settings,principal,request,op,generator):calls.append(request.prompt_name);return feedback(request)
    monkeypatch.setattr('app.services.tutor_agent._invoke',invoke)
    key=uuid.uuid4().hex;message='Give me 5 questions from '+topic.title
    state=send(message,key)['practiceSet']
    assert state['availableCount']==1 and state['requestedCount']==5
    assert 'markingGuidance' not in state['question']
    assert send(message,key)['practiceSet']==state and not calls
    assert send('Next question')['practiceSet']['position']==1
    response=send('My answer: One spot; separated dyes.')['practiceSet']
    assert response['feedback']['score']==2 and response['feedback']['indicative']
    assert len(calls)==1
    resumed=client.get(f'/api/v1/tutoring/sessions/{ref}/question-set').json()
    assert resumed['answer']=='One spot; separated dyes.'
    assert resumed['feedback']['score']==2 and resumed['itemStatus']=='feedback'
    assert resumed['completedCount']==1
    assert send('Next question')['practiceSet']['status']=='completed'


@pytest.mark.integration
def test_retry_hint_reveal_withdrawal(auth_client,monkeypatch):
    client,db,child,topic,ref,send=begin(auth_client,monkeypatch)
    message='Give me 1 question from '+topic.title
    send(message)
    def failed(*args):raise DomainError('provider_timeout','Feedback unavailable.',503)
    monkeypatch.setattr('app.services.tutor_agent._invoke',failed)
    response=send('My answer: One spot.')['practiceSet']
    assert response['answer']=='One spot.' and response['feedback'] is None
    monkeypatch.setattr('app.services.tutor_agent._invoke',lambda db,settings,principal,request,op,generator:feedback(request))
    assert send('Retry feedback')['practiceSet']['feedback']['score']==2
    send('Next question');send(message)
    hint=send('Give me a hint')['practiceSet']
    assert hint['assisted'] and hint['itemStatus']=='awaiting_answer' and 'markingGuidance' not in hint['question']
    assert send('My answer: One spot.')['practiceSet']['summary']['maximumMarks']==0
    send('Next question');send(message)
    assert send('Show the answer for question 9(b)')['practiceSet']['itemStatus']=='awaiting_answer'
    revealed=send('Please show me the answer')['practiceSet'];assert revealed['itemStatus']=='revealed'
    assert send('My answer: copied')['practiceSet']['feedback'] is None
    send('Next question');send(message)
    release=db.scalar(select(TutorPaperRelease));release.enabled=False;db.commit()
    assert send('Show answer')['practiceSet'] is None
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/question-set').status_code==409
    send('Stop practice')
    assert db.scalar(select(TutorQuestionSet).where(TutorQuestionSet.status=='active')) is None


@pytest.mark.integration
def test_generated_frozen_checked_private(auth_client,monkeypatch):
    client,db,child,topic,ref,send=begin(auth_client,monkeypatch)
    monkeypatch.setattr(sets,'_generation_context',lambda db,topics:([{'content':'Particles move randomly.'}],[]))
    calls=[]
    def invoke(db,settings,principal,request,op,generator):
        calls.append(request.prompt_name)
        if request.prompt_name=='formative-question-generation':
            value=request.output_type(prompt='Explain why gas particles spread throughout a container.',marks=1,
                markingPoints=[{'code':'G1','text':'Particles move randomly.'}],suggestedAnswer='Gas particles move randomly in all directions.',
                topicRefs=[topic.public_ref],difficulty='medium',requiresVisual=False)
        elif request.prompt_name=='formative-question-check':
            value=request.output_type(scientificallyCorrect=True,solvableFromQuestion=True,rubricConsistent=True,topicGrounded=True,originalWording=True,reason='Supported.')
        else:return feedback(request)
        return AIResult(value,'fixture','fixture-generation',None,AIUsage(10,20,30),1,1)
    # Exercise real invocation/quota commits between generation, validation
    # and saving the frozen item, while substituting only the external provider.
    monkeypatch.setattr('app.ai.router.AIAccountRouter.generate',
        lambda router,request,**kwargs:invoke(None,None,None,request,None,None))
    state=send('Generate 2 new questions from '+topic.title)['practiceSet']
    assert state['sourceKind']=='generated' and state['availableCount']==2
    assert 'suggestedAnswer' not in state['question']
    assert state['processing'] is False
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/question-set').json()['question']==state['question']
    assert len(calls)==2
    assert send('My answer: Particles move randomly.')['practiceSet']['feedback']['score']==1
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/question-set').json()['feedback']['score']==1
    assert db.scalar(select(TutorQuestionSet)).items[0]['provenance']['model']=='fixture-generation'
    assert len(db.scalars(select(OfficialPaperReviewQuestion)).all())==1
    assert client.get('/api/v1/tutoring/sessions/tutor_session_missing/question-set').status_code==404


@pytest.mark.integration
def test_question_set_owner_assets_and_formal_assessment_protection(auth_client,monkeypatch):
    from app.models import Assessment, User, StudentProfile
    from datetime import datetime,timedelta,timezone
    client,db,child,topic,ref,send=begin(auth_client,monkeypatch)
    selected=send('Give me 1 question from '+topic.title)['practiceSet']
    asset=selected['question']['assets'][0]['url']
    # The fixture crop has metadata but no physical image; missing files fail safely.
    assert client.get(asset).status_code==404
    from app.services.curriculum_plans import snapshot
    coverage=snapshot(db,'formal-test-'+uuid.uuid4().hex,child.id,'chemistry')
    active=Assessment(curriculum_snapshot_id=coverage.id,student_id=child.id,subject_id='chemistry',mode='mock',status='active',title='Formal test',
        target_marks=2,duration_minutes=10,started_at=datetime.now(timezone.utc),ends_at=datetime.now(timezone.utc)+timedelta(minutes=10))
    db.add(active);db.commit()
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/question-set').status_code==403
    assert client.get(asset).status_code==403
    active.status='expired';db.commit()
    sibling=User(username='sibling-'+uuid.uuid4().hex,display_name='Sibling',role='student',password_hash=child.password_hash,must_change_password=False)
    db.add(sibling);db.flush();db.add(StudentProfile(student_id=sibling.id,parent_id=db.get(StudentProfile,child.id).parent_id));db.commit()
    assert client.post('/api/v1/auth/login',json={'username':sibling.username,'password':'correct horse battery staple'}).status_code==200
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/question-set').status_code==404
    assert client.get(asset).status_code==404
    client.cookies.clear()
    assert client.get(f'/api/v1/tutoring/sessions/{ref}/question-set').status_code==401
    assert client.get(asset).status_code==401


@pytest.mark.integration
def test_generation_failed_check_never_serves_unchecked_question(auth_client,monkeypatch):
    client,db,child,topic,ref,send=begin(auth_client,monkeypatch)
    monkeypatch.setattr(sets,'_generation_context',lambda db,topics:([{'content':'Particles move randomly.'}],[]))
    def invoke(db,settings,principal,request,op,generator):
        if request.prompt_name=='formative-question-generation':
            value=request.output_type(prompt='Explain the motion of particles in a gas.',marks=1,
                markingPoints=[{'code':'G1','text':'Random motion.'}],suggestedAnswer='Gas particles move randomly.',
                topicRefs=[topic.public_ref],difficulty='medium',requiresVisual=False)
        else:value=request.output_type(scientificallyCorrect=False,solvableFromQuestion=True,rubricConsistent=True,topicGrounded=True,originalWording=True,reason='Not grounded enough.')
        return AIResult(value,'fixture','fixture-generation',None,AIUsage(1,1,2),1,1)
    monkeypatch.setattr('app.services.tutor_agent._invoke',invoke)
    value=send('Generate 2 new questions from '+topic.title)
    assert value['practiceSet']['question'] is None
    assert 'Retry generation' in value['followUpChoices']
    assert db.scalar(select(TutorQuestionSet)).items==[{},{}]
