"""Private answer assets must never behave like question illustrations."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
import pymupdf
import pytest
from app.main import app
from app.storage.factory import get_storage
from app.errors import DomainError
from app.schemas.answer_visuals import AnswerVisual
from app.services.answer_visuals import validate_visuals, download
from app.models import DocumentAsset
from test_auth_integration import auth_client  # noqa: F401
from test_official_paper_review_workspace import _setup, _question

@pytest.mark.integration
def test_scheme_crops_are_private_reviewed_and_replay_safe(auth_client):
    client, headers, session, paper, scheme, report, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    assert client.post(root+'/start', headers=headers, json={'schemeDocumentId':str(scheme[0].id)}).status_code == 200
    storage = app.dependency_overrides[get_storage]()
    with pymupdf.open() as pdf:
        page=pdf.new_page(width=100,height=100)
        page.draw_line((20,30),(60,30))
        storage.put(scheme[1].object_key, pdf.tobytes(), 'application/pdf')
    body=dict(source='scheme',page=1,kind='diagram',x0=.1,y0=.1,x1=.7,y1=.6,altText='Displayed molecule with all bonds.')
    response=client.post(root+'/visual-crops',headers=headers,json=body)
    assert response.status_code == 200,response.text
    asset_id=response.json()['assetId']
    assert client.post(root+'/visual-crops',headers=headers,json=body).json()['assetId']==asset_id
    asset=session.get(DocumentAsset,uuid.UUID(asset_id))
    assert asset.document_version_id==scheme[1].id and asset.asset_metadata['answerVisual']
    question=_question(paper,scheme,topic)
    part=question['data']['parts'][0]
    part.update(responseType='drawing',answerVisualRequired=True,assessmentReadiness='manual_only',assessmentReadinessReason='Inspect the original diagram.',answerVisuals=[dict(assetId=asset_id,partLabel='a',pointCodes=['M1'],caption='Model answer',altText=body['altText'],status='proposed')])
    blocked=client.post(root+'/questions',headers=headers,json=question)
    assert blocked.status_code==409,blocked.text
    part['answerVisuals'][0]['status']='approved'
    saved=client.post(root+'/questions',headers=headers,json=question)
    assert saved.status_code==200,saved.text
    assert saved.json()['questions'][0]['data']['parts'][0]['answerVisuals'][0]['assetId']==asset_id
    question['expectedRevision']=1
    question['status']='needs_correction'
    question['data']['visualAssetIds']=[asset_id]
    assert client.post(root+'/questions',headers=headers,json=question).status_code==422
    visual=AnswerVisual.model_validate(part['answerVisuals'][0])
    with pytest.raises(DomainError): validate_visuals(session,paper[1].id,[visual],{'M1'},'a')
    with pytest.raises(DomainError): validate_visuals(session,scheme[1].id,[visual],{'M2'},'a')
    with pytest.raises(DomainError): validate_visuals(session,scheme[1].id,[visual],{'M1'},'b')

def test_answer_download_requires_submitted_owned_attempt_and_frozen_asset(monkeypatch):
    from app.services import assessments
    aid,qid,vid=uuid.uuid4(),uuid.uuid4(),uuid.uuid4()
    assessment=SimpleNamespace(id=aid,status='active',submitted_at=None)
    question=SimpleNamespace(assessment_id=aid,rubric={'answerVisuals':[{'assetId':str(vid),'status':'approved'}]})
    asset=SimpleNamespace(asset_metadata={'answerVisual':True},object_key='private.png',mime_type='image/png')
    db=SimpleNamespace(get=lambda cls,key: asset if cls is DocumentAsset else question)
    storage=SimpleNamespace(get=lambda *args: b'private-image')
    monkeypatch.setattr(assessments,'_owned',lambda *args: assessment)
    with pytest.raises(DomainError): download(db,storage,None,aid,qid,vid)
    assessment.status='expired'
    with pytest.raises(DomainError): download(db,storage,None,aid,qid,vid)
    assessment.submitted_at=datetime.now(timezone.utc)
    assert download(db,storage,None,aid,qid,vid)==b'private-image'
    with pytest.raises(DomainError): download(db,storage,None,aid,qid,uuid.uuid4())
    question.assessment_id=uuid.uuid4()
    with pytest.raises(DomainError): download(db,storage,None,aid,qid,vid)
    def forbidden(*args): raise DomainError('assessment_not_found','Not owned.',404)
    monkeypatch.setattr(assessments,'_owned',forbidden)
    with pytest.raises(DomainError): download(db,storage,None,aid,qid,vid)


def test_manual_result_has_valid_pending_contract_and_no_student_score():
    from app.services.answer_visuals import queue_manual_result
    from app.services.assessment_marking import result_response
    from app.schemas.assessments import AssessmentResultResponse
    rows=[]
    db=SimpleNamespace(scalar=lambda query:0,add=rows.append)
    assessment=SimpleNamespace(id=uuid.uuid4())
    question=SimpleNamespace(id=uuid.uuid4(),marks=2,rubric={'drawingParts':['c(ii)']})
    answer=SimpleNamespace(save_revision=1,drawing_files={'c(ii)':str(uuid.uuid4())})
    points=[dict(pointId='M1',criterion='All bonds',maxMarks=1),dict(pointId='M2',criterion='Distinct isomer',maxMarks=1)]
    row=queue_manual_result(db,assessment,question,answer,points,'request-123')
    row.id=uuid.uuid4();row.created_at=datetime.now(timezone.utc)
    for field in ('strengths','small_mistakes','conceptual_mistakes','topic_evidence','recommendations'): setattr(row,field,[])
    payload=AssessmentResultResponse.model_validate(result_response(row))
    assert payload.status=='needs_review' and payload.markingDecisions==[]
    assert 'No score' in payload.teachingExplanation
    assert len(rows)==1 and row.deterministic_checks['scorePending']


def test_visual_proposal_supplies_original_and_answer_images_without_ocr_substitution():
    from app.services.drawing_assessment import propose
    from app.ai.base import AIResult, AIUsage
    calls=[]
    aid=uuid.uuid4()
    asset=SimpleNamespace(asset_metadata={'answerVisual':True},object_key='model',mime_type='image/png')
    db=SimpleNamespace(get=lambda *args:asset)
    storage=SimpleNamespace(get=lambda key,mime:SimpleNamespace(content=key.encode(),content_type=mime))
    q=SimpleNamespace(id=uuid.uuid4(),prompt='Draw two isomers.',rubric={'answerVisuals':[dict(assetId=str(aid),status='approved',partLabel='c(ii)',pointCodes=['M1'],altText='All bonds shown')]})
    work=SimpleNamespace(question_id=q.id,student_id=uuid.uuid4(),object_key='original',content_type='image/png',ocr_metadata={'partLabel':'c(ii)'})
    def generate(db,settings,request): calls.append(request);return 'proposal'
    assert propose(db,storage,None,q,None,work,[],generate)=='proposal'
    assert len(calls[0].pages)==2
    assert 'STUDENT RESPONSE' in calls[0].pages[0].text
    assert 'MODEL ANSWER ONLY' in calls[0].pages[1].text
    assert 'never compare pixels' in calls[0].instructions

@pytest.mark.integration
def test_student_drawing_roundtrip_and_result_release(auth_client, monkeypatch):
    from datetime import timedelta
    from io import BytesIO
    from PIL import Image
    from sqlalchemy import select, func
    from app.models import (User, StudentProfile, CurriculumPlan, AssessmentCurriculumSnapshot,
        OfficialMaterialVersion, OfficialQuestionVersion, Assessment, AssessmentQuestion, AssessmentAnswer)
    from app.security import hash_password
    from app.services import assessment_working
    client, headers, session, paper, scheme, report, topic = _setup(auth_client)
    admin_id=paper[0].uploaded_by
    token=uuid.uuid4().hex
    parent=User(username='parent-'+token,display_name='Parent',role='parent',password_hash=hash_password('test drawing password'),must_change_password=False)
    student=User(username='student-'+token,display_name='Learner',role='student',password_hash=hash_password('test drawing password'),must_change_password=False)
    sibling=User(username='sibling-'+token,display_name='Sibling',role='student',password_hash=hash_password('test drawing password'),must_change_password=False)
    session.add_all([parent,student,sibling]);session.flush()
    session.add_all([StudentProfile(student_id=u.id,parent_id=parent.id) for u in (student,sibling)]);session.flush()
    plan=CurriculumPlan(course_id='igcse',subject_id='chemistry',textbook_id=topic.textbook_id,version_number=(session.scalar(select(func.max(CurriculumPlan.version_number)).where(CurriculumPlan.subject_id=='chemistry')) or 0)+1,created_by=admin_id)
    session.add(plan);session.flush()
    snap=AssessmentCurriculumSnapshot(assessment_ref=token,student_id=student.id,plan_id=plan.id,course_id='igcse',subject_id='chemistry',grade=10,term=1,covered_topic_ids=[],progression_periods=[])
    material=OfficialMaterialVersion(document_id=paper[0].id,source_document_version_id=paper[1].id,version_number=1,kind='past_paper',course_id='igcse',subject_id='chemistry',created_by=admin_id)
    session.add_all([snap,material]);session.flush()
    source=OfficialQuestionVersion(material_version_id=material.id,question_number='5',prompt='Draw isomers',marks=2)
    session.add(source);session.flush()
    assessment=Assessment(student_id=student.id,subject_id='chemistry',mode='practice',curriculum_snapshot_id=snap.id,title='Draw',target_marks=2,duration_minutes=30,ends_at=datetime.now(timezone.utc)+timedelta(minutes=30))
    session.add(assessment);session.flush()
    asset=scheme[5];asset.asset_metadata={**asset.asset_metadata,'answerVisual':True}
    visual=dict(assetId=str(asset.id),partLabel='c(ii)',pointCodes=['M1'],caption='Model',altText='Complete displayed molecule.',status='approved')
    question=AssessmentQuestion(assessment_id=assessment.id,sequence=1,source_question_version_id=source.id,source_document_version_id=paper[1].id,question_number='5',prompt='Draw isomers',marks=2,topic_ids=[],rubric={'drawingParts':['c(ii)'],'answerVisuals':[visual],'markingPoints':[{'code':'M1','text':'Butane'},{'code':'M2','text':'Methylpropane'}]})
    session.add(question);session.commit()
    storage=app.dependency_overrides[get_storage]()
    image=BytesIO();Image.new('RGB',(60,60),'white').save(image,format='PNG');png=image.getvalue()
    storage.put(asset.object_key,png,'image/png')
    monkeypatch.setattr(assessment_working,'extract_document',lambda *args:{'pages':[],'pageCount':1})
    login=client.post('/api/v1/auth/login',json={'username':student.username,'password':'test drawing password'}).json()
    h={'X-CSRF-Token':login['csrfToken'],'Content-Type':'image/png','X-Filename':'drawing.png'}
    root=f'/api/v1/assessments/{assessment.id}'
    image_url=f'{root}/questions/{question.id}/answer-visuals/{asset.id}'
    assert client.get(image_url).status_code==404
    assert client.get(f'/api/v1/documents/{scheme[0].id}/assets/{asset.id}/content').status_code==403
    upload_url=f'{root}/questions/{question.id}/drawings/c(ii)'
    uploaded=client.post(upload_url,content=png,headers=h)
    assert uploaded.status_code==201,uploaded.text
    first=uploaded.json()['id']
    second=client.post(upload_url,content=png,headers=h).json()['id']
    answer=session.get(AssessmentAnswer,(assessment.id,question.id));session.refresh(answer)
    assert answer.drawing_files=={'c(ii)':second} and second!=first
    assert client.get(root+'/working/'+second).status_code==200
    assert client.post(root+'/submit',headers={'X-CSRF-Token':h['X-CSRF-Token']},json={'idempotencyKey':'submit-drawing-123'}).status_code==200
    assert client.post(upload_url,content=png,headers=h).status_code==409
    assert client.get(image_url).status_code==200
    assessed=client.post(root+'/evaluate',headers={'X-CSRF-Token':h['X-CSRF-Token']},json={'idempotencyKey':'evaluate-drawing-123'})
    assert assessed.status_code==200,assessed.text
    result=assessed.json()['questions'][0]['result']
    assert result['status']=='needs_review' and result['markingDecisions']==[]
    assert assessed.json()['questions'][0]['rubric']['answerVisuals']==[visual]
    client.post('/api/v1/auth/login',json={'username':sibling.username,'password':'test drawing password'})
    assert client.get(image_url).status_code==404
    assert client.get(root+'/working/'+second).status_code==404
