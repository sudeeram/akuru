"""Admin generation stays private, versioned, explicitly reviewed and source-bound."""
import uuid
from types import SimpleNamespace
import pytest
from sqlalchemy import select
from app.config import get_settings
from app.main import app
from app.models import GeneratedWorkedAnswer, OfficialPaperReviewQuestion, DocumentAsset
from app.services.worked_answers.generation import process_next
from app.services.answer_visuals import validate_visuals
from app.schemas.answer_visuals import AnswerVisual
from app.schemas.worked_answers import GraphSolution
from app.errors import DomainError
from app.ai.base import AIResult, AIUsage
from test_auth_integration import auth_client  # noqa
from test_official_paper_review_workspace import _setup, _question
from test_worked_answer_graphs import fixture


@pytest.mark.integration
def test_generated_answer_lifecycle(auth_client):
    client,headers,db,paper,scheme,report,topic=_setup(auth_client)
    # DDL lives inside this fixture's outer rollback, not the local application schema.
    GeneratedWorkedAnswer.__table__.create(db.connection(),checkfirst=True)
    root=f'/api/v1/admin/official-paper-reviews/{paper[0].id}'
    assert client.post(root+'/start',headers=headers,json={'schemeDocumentId':str(scheme[0].id)}).status_code==200
    q=_question(paper,scheme,topic);q['status']='needs_correction'
    original=q['data']['parts'][0]
    q['data']['parts']=[]
    for label in ['c(i)','c(ii)','c(iii)']:
        p=dict(original);p['label']=label;q['data']['parts'].append(p)
    assert client.post(root+'/questions',headers=headers,json=q).status_code==200
    path=root+'/questions/1/worked-answers'
    from app.models import AIProviderAccount
    from pydantic import SecretStr
    priorities=set(db.scalars(select(AIProviderAccount.priority)))
    db.add(AIProviderAccount(display_name='Worked test '+uuid.uuid4().hex,credential_alias='WORKED_TEST',
        model='test-model',priority=next(i for i in range(101) if i not in priorities)))
    db.commit()
    settings=get_settings().model_copy(update={'worked_answers_enabled':True,'openai_account_keys':{'WORKED_TEST':SecretStr('fake-credential')}})
    app.dependency_overrides[get_settings]=lambda:settings
    sol=GraphSolution.model_validate(fixture())
    graph={k:sol.model_dump()[k] for k in ('xAxis','yAxis','points')}
    graph.update(partLabels=['c(i)','c(ii)','c(iii)'],verificationNote='Verified against the exact synthetic data source.')
    body={'expectedQuestionRevision':1,'graph':graph}
    assert client.post(path,json=body).status_code==403
    response=client.post(path,headers=headers,json=body)
    assert response.status_code==202,response.text
    row=response.json();assert row['status']=='queued'
    assert client.post(path,headers=headers,json=body).status_code==409
    result=AIResult(sol,'fake','test-model',None,AIUsage(30,40,70),1,1)
    assert process_next(db,settings,lambda request:result)
    row=client.get(path).json()[0];assert row['status']=='awaiting_review'
    assert 'test-model'==row['provenance']['model']
    base=path+'/'+row['id']
    preview=client.get(base+'/steps/0/image');assert preview.status_code==200 and preview.content.startswith(b'\x89PNG')
    assert 'no-store' in preview.headers['cache-control']
    attach={'expectedQuestionRevision':1}
    assert client.post(base+'/attach',headers=headers,json=attach).status_code==409
    review={'expectedRevision':row['revision'],'action':'approve','reviewNote':'Checked the data, anomaly and fitted lines against the source.'}
    approved=client.post(base+'/review',headers=headers,json=review);assert approved.status_code==200,approved.text
    assert client.post(base+'/review',headers=headers,json=review).status_code==409
    attached=client.post(base+'/attach',headers=headers,json=attach);assert attached.status_code==200,attached.text
    saved=client.get(root).json()['questions'][0]
    assert saved['status']=='needs_correction' and saved['revision']==2
    visuals=saved['data']['parts'][0]['answerVisuals']
    assert visuals[0]['origin']=='ai_generated'
    visual=AnswerVisual.model_validate(visuals[0]);validate_visuals(db,scheme[1].id,[visual])
    asset=db.get(DocumentAsset,visual.assetId)
    assert asset.asset_metadata['generatedAnswer'] and 'reviewCrop' not in asset.asset_metadata
    # Same source/data reuses approved generation; no provider call or cost.
    body['expectedQuestionRevision']=2
    assert client.post(path,headers=headers,json=body).json()['id']==row['id']
    with pytest.raises(DomainError): validate_visuals(db,scheme[1].id,[visual],question_number='different-question')
    modified=sol.model_dump();modified['steps'][0]['explanation']='A scientifically reviewed correction to the first explanation.'
    edit_payload={'expectedRevision':approved.json()['revision'],'action':'edit','solution':modified,'reviewNote':'Correct the explanation and re-check the scientific meaning.'}
    bad=sol.model_dump();bad['points'][0]['y']=22
    assert client.post(base+'/review',headers=headers,json={**edit_payload,'solution':bad}).status_code==422
    edited=client.post(base+'/review',headers=headers,json=edit_payload)
    assert edited.status_code==200 and edited.json()['status']=='awaiting_review'
    with pytest.raises(DomainError):validate_visuals(db,scheme[1].id,[visual])
    reapproved=client.post(base+'/review',headers=headers,json={**review,'expectedRevision':edited.json()['revision']})
    assert reapproved.status_code==200
    with pytest.raises(DomainError):validate_visuals(db,scheme[1].id,[visual])  # old image must not inherit a changed solution's approval
    assert client.post(base+'/attach',headers=headers,json={'expectedQuestionRevision':2}).status_code==200
    question=db.scalar(select(OfficialPaperReviewQuestion).where(OfficialPaperReviewQuestion.id==uuid.UUID(row['questionId'])))
    question.review_data={**question.review_data,'sharedStem':'A materially changed question source'};db.commit()
    assert client.get(path).json()[0]['status']=='stale'
    with pytest.raises(DomainError):validate_visuals(db,scheme[1].id,[visual])
    assert client.post(base+'/attach',headers=headers,json={'expectedQuestionRevision':3}).status_code==409
    body['expectedQuestionRevision']=3
    queued=client.post(path,headers=headers,json=body);assert queued.status_code==202
    def fail(request):
        from app.ai.base import AIProviderError
        raise AIProviderError('provider_unavailable','Private provider diagnostic must not become content.')
    process_next(db,settings,fail)
    failed=next(item for item in client.get(path).json() if item['id']==queued.json()['id'])
    assert failed['status']=='failed' and failed['errorCode']=='provider_unavailable' and failed['solution']=={}


@pytest.mark.integration
def test_practice_reveal_is_private_and_formal_assessments_fail_closed(auth_client):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import text, func
    from app.models import (User, StudentProfile, CurriculumPlan, AssessmentCurriculumSnapshot,
        OfficialMaterialVersion, OfficialQuestionVersion, Assessment, AssessmentQuestion, AssessmentInteraction)
    from app.security import hash_password
    from app.storage.factory import get_storage
    client,headers,db,paper,scheme,report,topic=_setup(auth_client)
    db.execute(text("ALTER TABLE assessment_interactions DROP CONSTRAINT ck_assessment_interaction_kind"))
    db.execute(text("ALTER TABLE assessment_interactions ADD CONSTRAINT ck_assessment_interaction_kind CHECK (kind IN ('hint','worked_answer'))"))
    token=uuid.uuid4().hex;password='worked answer test password'
    parent=User(username='worked-parent-'+token,display_name='Parent',role='parent',password_hash=hash_password(password),must_change_password=False)
    children=[User(username=f'worked-{i}-{token}',display_name='Learner',role='student',password_hash=hash_password(password),must_change_password=False) for i in range(2)]
    db.add_all([parent,*children]);db.flush()
    db.add_all([StudentProfile(student_id=c.id,parent_id=parent.id) for c in children]);db.flush()
    plan=CurriculumPlan(course_id='igcse',subject_id='chemistry',textbook_id=topic.textbook_id,
        version_number=(db.scalar(select(func.max(CurriculumPlan.version_number)).where(CurriculumPlan.subject_id=='chemistry')) or 0)+1,created_by=paper[0].uploaded_by)
    db.add(plan);db.flush()
    snap=AssessmentCurriculumSnapshot(assessment_ref=token,student_id=children[0].id,plan_id=plan.id,course_id='igcse',subject_id='chemistry',grade=10,term=1,covered_topic_ids=[],progression_periods=[])
    material=OfficialMaterialVersion(document_id=paper[0].id,source_document_version_id=paper[1].id,version_number=1,kind='past_paper',course_id='igcse',subject_id='chemistry',created_by=paper[0].uploaded_by)
    db.add_all([snap,material]);db.flush()
    source=OfficialQuestionVersion(material_version_id=material.id,question_number='7',prompt='Plot the points',marks=1)
    db.add(source);db.flush()
    assessment=Assessment(student_id=children[0].id,subject_id='chemistry',mode='practice',curriculum_snapshot_id=snap.id,title='Graph',target_marks=1,duration_minutes=30,ends_at=datetime.now(timezone.utc)+timedelta(minutes=30))
    db.add(assessment);db.flush()
    asset=scheme[5];asset.asset_metadata={**asset.asset_metadata,'answerVisual':True,'generatedAnswer':True}
    visual=dict(assetId=str(asset.id),partLabel='c(i)',pointCodes=['M1'],caption='Graph',altText='The verified data plotted on axes.',status='approved',origin='ai_generated')
    question=AssessmentQuestion(assessment_id=assessment.id,sequence=1,source_question_version_id=source.id,source_document_version_id=paper[1].id,question_number='7',prompt='Plot the points',marks=1,topic_ids=[],rubric={'answerVisuals':[visual]})
    db.add(question);db.commit()
    app.dependency_overrides[get_storage]().put(asset.object_key,b'private generated png','image/png')
    root=f'/api/v1/assessments/{assessment.id}';reveal=f'{root}/questions/{question.id}/worked-answer'
    image=f'{root}/questions/{question.id}/answer-visuals/{asset.id}'
    login=client.post('/api/v1/auth/login',json={'username':children[0].username,'password':password}).json()
    h={'X-CSRF-Token':login['csrfToken']}
    assert client.get(image).status_code==404
    before=client.get('/api/v1/assessments').json()['assessments'][0]['questions'][0]
    assert before['rubric'] is None and before['generatedWorkedAnswerAvailable'] is True
    assert client.post(reveal).status_code==403
    for mode in ['mock','official_paper']:
        assessment.mode=mode;db.commit()
        assert client.post(reveal,headers=h).status_code==403
        assert client.get(image).status_code==404
    assessment.mode='practice';db.commit()
    shown=client.post(reveal,headers=h)
    assert shown.status_code==200 and shown.json()['assisted'] is True
    assert shown.json()['visuals'][0]['origin']=='ai_generated'
    assert client.get(image).content==b'private generated png'
    assert client.post(reveal,headers=h).status_code==200
    assert db.scalar(select(func.count()).select_from(AssessmentInteraction).where(AssessmentInteraction.assessment_id==assessment.id,AssessmentInteraction.kind=='worked_answer'))==1
    # A previous practice reveal cannot bypass a formal assessment gate.
    assessment.mode='mock';db.commit()
    assert client.get(image).status_code==404
    assessment.status='expired';db.commit()
    assert client.get(image).status_code==404
    assessment.submitted_at=datetime.now(timezone.utc);db.commit()
    assert client.get(image).status_code==200
    for user in [children[1],parent]:
        client.post('/api/v1/auth/login',json={'username':user.username,'password':password})
        assert client.get(image).status_code in (403,404)
        assert client.get(f'/api/v1/admin/official-paper-reviews/{paper[0].id}/questions/7/worked-answers').status_code==403
