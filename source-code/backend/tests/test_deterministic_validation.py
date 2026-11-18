import copy,uuid
import pytest
from sqlalchemy import select
from app.models import OfficialPaperReviewQuestion,AuditEvent
from app.services import deterministic_validation as v
from test_auth_integration import auth_client  # noqa
from test_paper_workflow import prepared,run


def configured(auth_client):
 c,h,db,root,q,req,out,storage,_,_=prepared(auth_client)
 data=copy.deepcopy(q['data']);p=data['parts'][0];codes=[p['code']for p in p['markingPoints']]
 p.update(assessmentReadiness='manual_only',assessmentReadinessReason='Awaiting deterministic replay.',scoringRules=dict(version=3,deterministic=dict(matchers=[
  dict(pointId=codes[0],kind='choice',accepted=['AB','A'],rejected=['C','B']),
  dict(pointId=codes[1],kind='choice',accepted=['AB','B'],rejected=['C','A'])])))
 assert c.post(root+'/questions',headers=h,json=dict(number='1',expectedRevision=q['revision'],status=q['status'],data=data)).status_code==200
 q=c.get(root).json()['questions'][0]
 req.update(expectedRevision=q['revision'],expectedContentHash=q['analysisContentHash'],expectedAnalysisVersion=q['analysisVersion'])
 run(c,h,db,root,req,out,storage);q=c.get(root).json()['questions'][0]
 caps=c.get(root+'/deterministic-capabilities').json()
 package=dict(requestId=str(uuid.uuid4()),partLabel=p['label'],expectedRevision=q['revision'],expectedEngineHash=caps['engineHash'],confirmSourceReviewed=True,sourceNotes='Original paper and exact scheme checked independently.',cases=[
  dict(answer='AB',expectedMarks=2,expectedPoints=codes),dict(answer='A',expectedMarks=1,expectedPoints=codes[:1]),
  dict(answer='B',expectedMarks=1,expectedPoints=codes[1:],holdout=True),dict(answer='C',expectedMarks=0),dict(answer='unclear',requiresReview=True)])
 return c,h,db,root,q,package

@pytest.mark.integration
def test_authenticated_replay_certificate_and_no_readiness_bypass(auth_client):
 c,h,db,root,q,pkg=configured(auth_client)
 data=copy.deepcopy(q['data']);data['parts'][0]['assessmentReadiness']='automatic'
 refused=c.post(root+'/questions',headers=h,json=dict(number='1',expectedRevision=q['revision'],status=q['status'],data=data))
 assert refused.status_code==409,refused.text
 endpoint=root+'/questions/1/validate-deterministic'
 assert c.post(endpoint,json=pkg).status_code==403
 r=c.post(endpoint,headers=h,json=pkg);assert r.status_code==200,r.text
 assert r.json()['passed']and r.json()['noModelCalls']
 saved=c.get(root).json()['questions'][0];part=saved['data']['parts'][0]
 assert part['assessmentReadiness']=='automatic'
 assert part['scoringRules']['deterministic']['certificateId']==pkg['requestId']
 assert saved['accuracyAnalysis']['isCurrent']
 assert c.post(endpoint,headers=h,json=pkg).json()['id']==pkg['requestId']
 hist=c.get(root+'/questions/1/deterministic-validations').json()
 assert len(hist)==1 and hist[0]['current']
 # A materially changed matcher invalidates only its readiness and receipt.
 changed=copy.deepcopy(saved['data']);changed['parts'][0]['scoringRules']['deterministic']['matchers'][0]['accepted']=['different']
 edited=c.post(root+'/questions',headers=h,json=dict(number='1',expectedRevision=saved['revision'],status=saved['status'],data=changed))
 assert edited.status_code==200,edited.text
 assert edited.json()['questions'][0]['data']['parts'][0]['assessmentReadiness']=='unreviewed'
 assert not c.get(root+'/questions/1/deterministic-validations').json()[0]['current']
 assert db.get(AuditEvent,uuid.UUID(pkg['requestId'])).event_data['passed']

@pytest.mark.integration
def test_failed_stale_and_engine_mismatch_never_enable_readiness(auth_client):
 c,h,db,root,q,pkg=configured(auth_client);endpoint=root+'/questions/1/validate-deterministic'
 pkg['expectedEngineHash']='f'*64
 assert c.post(endpoint,headers=h,json=pkg).status_code==409
 pkg['expectedEngineHash']=v.engine.engine_hash();pkg['expectedRevision']+=1
 assert c.post(endpoint,headers=h,json=pkg).status_code==409
 pkg['expectedRevision']-=1;pkg['cases'][0]['expectedMarks']=0
 r=c.post(endpoint,headers=h,json=pkg);assert r.status_code==200,r.text
 assert not r.json()['passed']
 assert c.get(root).json()['questions'][0]['data']['parts'][0]['assessmentReadiness']=='manual_only'

@pytest.mark.integration
def test_real_student_submission_has_no_provider_or_quota_calls(auth_client,monkeypatch):
 from test_tutor_past_papers import _ready,_login_student
 from app.services import assessment_marking
 from app.models import AssessmentResult,Assessment,User
 from sqlalchemy import func
 c,h,db,root,child,topic,paper,scheme,settings=_ready(auth_client,monkeypatch)
 q=c.get(root).json()['questions'][0];data=copy.deepcopy(q['data']);p=data['parts'][0];codes=[p['code']for p in p['markingPoints']]
 p.update(assessmentReadiness='manual_only',assessmentReadinessReason='Pending actual recognition validation.',scoringRules=dict(version=3,deterministic=dict(matchers=[dict(pointId=code,kind='choice',accepted=['AB',label],rejected=['C',other])for code,label,other in [(codes[0],'A','B'),(codes[1],'B','A')]])))
 response=c.post(root+'/questions',headers=h,json=dict(number='1',expectedRevision=q['revision'],status=q['status'],data=data));assert response.status_code==200,response.text
 q=c.get(root).json()['questions'][0]
 checks=[dict(role=role,status='checked'if role!='report'else'not_available',percent=99 if role!='report'else None,pages=[1]if role!='report'else[],reasons=['Source fixture inspected.'])for role in ['paper','scheme','report']]
 estimate=dict(confidencePolicy='extraction-v1',percent=98,reasons=['Reviewed fixture sources.'],sourceChecks=checks)
 r=c.post(root+'/questions/1/analyses',headers=h,json=dict(expectedQuestionRevision=q['revision'],expectedAnalysisVersion=q['analysisVersion'],expectedContentHash=q['analysisContentHash'],stage='accuracy',methodVersion='final-source-accuracy-v3',provenance=[dict(role=r,method='manual')for r in ['paper','scheme','report']],question=estimate,parts=[dict(**estimate,label=p['label'],selfContained=True)]));assert r.status_code==201,r.text
 q=c.get(root).json()['questions'][0]
 package=dict(requestId=str(uuid.uuid4()),partLabel=p['label'],expectedRevision=q['revision'],expectedEngineHash=v.engine.engine_hash(),confirmSourceReviewed=True,sourceNotes='Independent exact fixture-source comparison completed.',cases=[dict(answer='AB',expectedMarks=2,expectedPoints=codes),dict(answer='A',expectedMarks=1,expectedPoints=codes[:1]),dict(answer='B',expectedMarks=1,expectedPoints=codes[1:],holdout=True),dict(answer='C',expectedMarks=0),dict(answer='unclear',requiresReview=True)])
 r=c.post(root+'/questions/1/validate-deterministic',headers=h,json=package);assert r.status_code==200 and r.json()['passed'],r.text
 q=c.get(root).json()['questions'][0]
 r=c.post(root+'/questions/1/chat-release',headers=h,json=dict(partLabel=p['label'],revision=q['revision'],confirmSelfContained=True,enabled=True));assert r.status_code==200,r.text
 sh,ref=_login_student(c,child,topic)
 def forbidden(*a,**kw):pytest.fail('Deterministic Student marking cannot invoke/reserve a model')
 monkeypatch.setattr('app.services.tutor_agent._invoke',forbidden)
 monkeypatch.setattr('app.services.assessment_marking._generate',forbidden)
 monkeypatch.setattr('app.services.usage_limits.reserve_assessment',forbidden)
 monkeypatch.setattr('app.services.evaluations.automatic_feedback_allowed',forbidden)
 endpoint=f'/api/v1/tutoring/sessions/{ref}/agent-turns'
 r=c.post(endpoint,headers=sh,json=dict(message='Ask me a question from an igcse chemistry paper',requestKey=uuid.uuid4().hex));assert r.status_code==200,r.text
 assert r.json()['pastPaper']['practice']['question']['rubric'] is None
 assert r.json()['pastPaper']['practice']['question']['answerFormat']['fields']==['']
 r=c.post(endpoint,headers=sh,json=dict(message='My answer: AB',requestKey=uuid.uuid4().hex));assert r.status_code==200,r.text
 result=r.json()['pastPaper']['practice']['question']['result'];assert result['status']=='published'and result['awardedMarks']==2
 saved=db.scalar(select(AssessmentResult).join(Assessment).where(Assessment.student_id==child.id))
 assert saved.provider=='deterministic'and saved.subject_engine=='deterministic-v1'
 r=c.post(endpoint,headers=sh,json=dict(message='Next question',requestKey=uuid.uuid4().hex));assert r.status_code==200,r.text
 r=c.post(endpoint,headers=sh,json=dict(message='My answer: unclear',requestKey=uuid.uuid4().hex));assert r.status_code==200,r.text
 pending=r.json()['pastPaper']['practice']['question']['result'];assert pending['status']=='needs_review'and pending['markingDecisions']==[]
 assert 'no score' in r.json()['content'].lower()

@pytest.mark.integration
def test_full_question_compilation_preserves_proofs_and_rejects_forgery(auth_client):
 from types import SimpleNamespace
 from app.schemas.official_paper_reviews import ReviewQuestionData
 from app.services import marking_rules,assessment_marking
 c,h,db,root,q,pkg=configured(auth_client)
 r=c.post(root+'/questions/1/validate-deterministic',headers=h,json=pkg);assert r.status_code==200 and r.json()['passed'],r.text
 q=c.get(root).json()['questions'][0];data=ReviewQuestionData.model_validate(q['data'])
 points,rules=marking_rules.compile_review(data)
 frozen=SimpleNamespace(marks=data.marks,shared_stem=data.sharedStem,prompt=data.prompt,rubric=dict(markingPoints=points,scoringRules=rules))
 assert v.require_frozen_certificate(db,frozen)
 label=data.parts[0].label
 import json
 assert v.engine.recognize(json.dumps({label:'AB'}),assessment_marking._official_points(frozen),frozen.marks,rules)[0]==2
 rules['deterministic']['parts'][0]['prompt']='Forged context'
 with pytest.raises(Exception,match='certificate|context|rules'):v.require_frozen_certificate(db,frozen)
