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
 assert c.get(root+'/deterministic-capabilities').status_code==403
 assert c.post(root+'/questions/1/validate-deterministic',headers=sh,json=package).status_code==403
 assert r.json()['pastPaper']['practice']['question']['rubric'] is None
 assert r.json()['pastPaper']['practice']['question']['answerFormat']['fields']==['']
 r=c.post(endpoint,headers=sh,json=dict(message='My answer: AB',requestKey=uuid.uuid4().hex));assert r.status_code==200,r.text
 result=r.json()['pastPaper']['practice']['question']['result'];assert result['status']=='published'and result['awardedMarks']==2
 saved=db.scalar(select(AssessmentResult).join(Assessment).where(Assessment.student_id==child.id))
 assert saved.provider=='deterministic'and saved.subject_engine=='deterministic-v1'
 # Exercise the same certified rule through a separate formal assessment item.
 from app.models import AssessmentQuestion,AssessmentAnswer,OfficialMaterialVersion,OfficialQuestionVersion
 from app.schemas.official_paper_reviews import ReviewQuestionData
 from app.services import marking_rules
 from datetime import datetime,timezone
 original=db.get(Assessment,saved.assessment_id)
 formal=Assessment(student_id=child.id,subject_id=original.subject_id,mode='official_paper',status='submitted',
  curriculum_snapshot_id=original.curriculum_snapshot_id,title='Synthetic formal scoring test',target_marks=2,duration_minutes=10,
  ends_at=datetime.now(timezone.utc),submitted_at=datetime.now(timezone.utc))
 db.add(formal);db.flush()
 data=ReviewQuestionData.model_validate(q['data']);compiled,compiled_rules=marking_rules.compile_review(data)
 original_question=db.get(AssessmentQuestion,saved.question_id)
 material=OfficialMaterialVersion(document_id=paper[0].id,source_document_version_id=paper[1].id,version_number=1,
  kind='past_paper',course_id=paper[0].course_id,subject_id=paper[0].subject_id,created_by=paper[0].uploaded_by)
 db.add(material);db.flush()
 source_question=OfficialQuestionVersion(material_version_id=material.id,question_number='1',prompt=data.prompt,shared_stem=data.sharedStem,marks=2)
 db.add(source_question);db.flush()
 formal_question=AssessmentQuestion(assessment_id=formal.id,sequence=1,source_question_version_id=source_question.id,source_document_version_id=original_question.source_document_version_id,
  question_number='1',prompt=data.prompt,shared_stem=data.sharedStem,marks=2,equations=[],asset_ids=[],topic_ids=original_question.topic_ids,
  source_locations=original_question.source_locations,rubric=dict(markingPoints=compiled,scoringRules=compiled_rules))
 db.add(formal_question);db.flush()
 import json
 db.add(AssessmentAnswer(assessment_id=formal.id,question_id=formal_question.id,idempotency_key='synthetic-formal-answer',answer_text=json.dumps({p['label']:'AB'})))
 db.flush()
 assessment_marking.evaluate(db,settings,formal,'formal-deterministic-test')
 formal_result=db.scalar(select(AssessmentResult).where(AssessmentResult.assessment_id==formal.id))
 assert formal_result.provider=='deterministic' and formal_result.awarded_marks==2 and formal_result.status=='published'

 # Mixed-engine paper: only the semantic item reaches the supplied fixture model
 # and reserves two passes. The certified item is marked locally again.
 legacy=[point.model_dump(mode='json') for point in data.parts[0].markingPoints]
 semantic_source=OfficialQuestionVersion(material_version_id=material.id,question_number='2',prompt='Semantic fixture',shared_stem='',marks=2)
 db.add(semantic_source);db.flush()
 semantic=AssessmentQuestion(assessment_id=formal.id,sequence=2,source_question_version_id=semantic_source.id,
  source_document_version_id=original_question.source_document_version_id,question_number='2',prompt='Semantic fixture',
  shared_stem='',marks=2,equations=[],asset_ids=[],topic_ids=original_question.topic_ids,source_locations=original_question.source_locations,
  rubric=dict(markingPoints=legacy,scoringRules=dict(version=1,groups=[],combinedResponses=[])))
 db.add(semantic);db.flush();formal.target_marks=4
 db.add(AssessmentAnswer(assessment_id=formal.id,question_id=semantic.id,idempotency_key='mixed-semantic-fixture',answer_text='AB'));db.flush()
 reserved=[];model_calls=[];gates=[]
 monkeypatch.setattr('app.services.usage_limits.reserve_assessment',lambda db,settings,assessment,key,count:reserved.append(count))
 monkeypatch.setattr('app.services.evaluations.automatic_feedback_allowed',lambda *a,**k:(gates.append(True)or True,''))
 from app.ai.base import AIResult,AIUsage
 def fixture_model(db,settings,request):
  model_calls.append(request.prompt_name)
  decisions=[dict(pointId=p['code'],criterion=p['text'],maxMarks=1,awarded=True,marksAwarded=1,studentEvidence='AB',rationale='Synthetic dispatcher fixture.',confidence=1)for p in legacy]
  if request.output_type.__name__=='AssessmentPassOne':output=request.output_type(decisions=decisions,overallConfidence=1)
  else:output=request.output_type(decisions=decisions,confidence=1,improvedAnswer='Fixture',teachingExplanation='Fixture')
  return AIResult(output,'fixture','fixture-model',None,AIUsage(0,0,0),0,1)
 assessment_marking.evaluate(db,settings,formal,'mixed-engine-fixture',generator=fixture_model)
 assert reserved==[2] and len(model_calls)==2 and len(gates)==1


 r=c.post(endpoint,headers=sh,json=dict(message='Next question',requestKey=uuid.uuid4().hex));assert r.status_code==200,r.text
 r=c.post(endpoint,headers=sh,json=dict(message='My answer: unclear',requestKey=uuid.uuid4().hex));assert r.status_code==200,r.text
 pending=r.json()['pastPaper']['practice']['question']['result'];assert pending['status']=='needs_review'and pending['markingDecisions']==[] and pending['awardedMarks'] is None
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

@pytest.mark.integration
def test_engine_build_upgrade_requires_fresh_server_replay(auth_client,monkeypatch):
 c,h,db,root,q,pkg=configured(auth_client)
 endpoint=root+'/questions/1/validate-deterministic'
 first=c.post(endpoint,headers=h,json=pkg)
 assert first.status_code==200 and first.json()['passed']
 monkeypatch.setattr(v.engine,'engine_hash',lambda:'a'*64)
 assert c.get(root+'/questions/1/deterministic-validations').json()[0]['current']is False
 current=c.get(root).json()['questions'][0]
 pkg.update(requestId=str(uuid.uuid4()),expectedRevision=current['revision'],expectedEngineHash='a'*64)
 second=c.post(endpoint,headers=h,json=pkg)
 assert second.status_code==200 and second.json()['passed'],second.text
 history=c.get(root+'/questions/1/deterministic-validations').json()
 assert len(history)==2 and sum(row['current']for row in history)==1
 assert c.get(root).json()['questions'][0]['accuracyAnalysis']['isCurrent']
