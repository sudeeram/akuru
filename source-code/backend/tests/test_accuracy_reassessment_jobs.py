"""No paid calls: final snapshots, image gates and conservative source review."""
import copy, uuid, hashlib
from datetime import datetime,timezone,timedelta
import pymupdf,pytest
from sqlalchemy import select,func
from app.models import DocumentAsset,DocumentVersion,OfficialPaperReviewWorkspace,OfficialPaperReviewQuestion,OfficialQuestionAnalysis,EvidenceLinkJob,User
from app.ai.fake import FakeAIProvider
from app.config import get_settings
from app.services.accuracy_jobs import process_next
from test_auth_integration import auth_client
from test_exact_evidence_links import setup as source_setup


def setup(auth_client):
 c,h,db,root,q,a,storage=source_setup(auth_client)
 workspace=db.scalar(select(OfficialPaperReviewWorkspace))
 v=db.get(DocumentVersion,workspace.report_version_id);pdf=pymupdf.open();p=pdf.new_page();p.insert_text((30,60),'Examiner report: Question 1 chromatogram.');blob=pdf.tobytes();storage.put(v.object_key,blob,'application/pdf');v.sha256=hashlib.sha256(blob).hexdigest();db.commit()
 for asset in db.scalars(select(DocumentAsset).where(DocumentAsset.document_version_id.in_([workspace.paper_version_id,workspace.scheme_version_id]))):
  image=pdf[0].get_pixmap().tobytes('png');storage.put(asset.object_key,image,'image/png');asset.sha256=hashlib.sha256(image).hexdigest();asset.mime_type='image/png'
 row=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(row.review_data)
 for part in data['parts']:part['reportSources']=[dict(page=1,blockId=None,assetId=None)]
 row.review_data=data;db.commit()
 q=c.get(root).json()['questions'][0]
 req=dict(requestId=str(uuid.uuid4()),number=q['number'],expectedRevision=q['revision'],expectedContentHash=q['analysisContentHash'],expectedAnalysisVersion=q['analysisVersion'])
 output=dict(question=a['question'],parts=[dict(**p,dimensions=dict(wording=95,markingPoints=95,visuals=95),manualReviewReasons=[])for p in a['parts']])
 return c,h,db,root,q,req,output,storage

@pytest.mark.integration
def test_final_accuracy_job_records_current_assessment_without_rewriting_content(auth_client):
 c,h,db,root,q,req,out,storage=setup(auth_client)
 before=copy.deepcopy(q['data']);r=c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]});assert r.status_code==202,r.text
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]}).json()==r.json()
 assert c.get(root+'/evidence-link-jobs').json()==[]
 fake=FakeAIProvider(out);process_next(db,get_settings(),storage,generator=fake.generate)
 jobs=c.get(root+'/accuracy-jobs').json();assert jobs[0]['status']=='completed',jobs
 after=c.get(root).json()['questions'][0];assert after['accuracyAnalysis']['isCurrent']
 assert after['accuracyAnalysis']['provenance'][0]['modelId']=='fake-structured-v1'
 for p in after['data']['parts']:p['status']=next(v['status']for v in before['parts']if v['label']==p['label'])
 assert after['data']==before
 assert not c.get(root).json()['assessmentReleaseReady']
 assert len(fake.requests[0].pages)>=4 and 'untrusted' in fake.requests[0].instructions
 assert 'Wording confidence' in after['accuracyAnalysis']['parts'][0]['reasons'][0]

@pytest.mark.integration
def test_queue_is_atomic_and_respects_visual_and_analysis_snapshots(auth_client):
 c,h,db,root,q,req,out,storage=setup(auth_client)
 stale={**req,'expectedAnalysisVersion':100}
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[stale]}).status_code==409
 row=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(row.review_data);data['candidateVisualAssetIds']=[str(uuid.uuid4())];row.review_data=data;db.commit()
 q=c.get(root).json()['questions'][0];req.update(expectedContentHash=q['analysisContentHash'])
 ready=c.get(root+'/accuracy-readiness').json()['questions'][0];assert ready['visualBlockers']and not ready['canReassess']
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]}).status_code==409
 assert db.scalar(select(func.count()).select_from(EvidenceLinkJob))==0

@pytest.mark.integration
@pytest.mark.parametrize('mode',['stale','unseen_page','missing_part','manual_flag'])
def test_invalid_or_stale_generation_never_saves_high_confidence(auth_client,mode):
 c,h,db,root,q,req,out,storage=setup(auth_client)
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]}).status_code==202
 fake=FakeAIProvider(out)
 if mode=='stale':
  row=db.scalar(select(OfficialPaperReviewQuestion));row.revision+=1;db.commit()
 if mode=='unseen_page':out['parts'][0]['sourceChecks'][0]['pages']=[99]
 if mode=='missing_part':out['parts'][0]['label']='invented'
 if mode=='manual_flag':out['parts'][0]['manualReviewReasons']=['Contradictory source marking instructions.']
 process_next(db,get_settings(),storage,generator=fake.generate)
 job=c.get(root+'/accuracy-jobs').json()[0]
 if mode=='manual_flag':
  assert job['status']=='completed';after=c.get(root).json()['questions'][0];assert after['accuracyAnalysis']['question']['percent']<=70 and after['status']!='ai_approved'
 else:
  assert job['status']=='failed'and db.scalar(select(func.count()).select_from(OfficialQuestionAnalysis))==0
 if mode=='stale':assert not fake.requests

@pytest.mark.integration
def test_reassessment_permissions_and_interrupted_jobs(auth_client):
 c,h,db,root,q,req,out,storage=setup(auth_client)
 assert c.post(root+'/accuracy-jobs',json={'questions':[req]}).status_code==403
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]}).status_code==202
 job=db.scalar(select(EvidenceLinkJob));job.status='processing';job.started_at=datetime.now(timezone.utc)-timedelta(minutes=16);db.commit()
 fake=FakeAIProvider(out);process_next(db,get_settings(),storage,generator=fake.generate);db.refresh(job)
 assert job.status=='failed'and job.error_code=='accuracy_job_interrupted'and not fake.requests
 user=db.get(User,job.created_by);user.role='parent';db.commit()
 assert c.get(root+'/accuracy-jobs').status_code==403
 assert c.get(root+'/accuracy-readiness').status_code==403
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]}).status_code==403
 assert c.post('/api/v1/auth/logout',headers=h).status_code==204
 assert c.get(root+'/accuracy-jobs').status_code==401
 assert c.get(root+'/accuracy-readiness').status_code==401

@pytest.mark.integration
def test_checked_source_conflict_is_not_silently_overruled(auth_client):
 c,h,db,root,q,req,out,storage=setup(auth_client)
 from app.schemas.paper_analysis import RecordQuestionAnalysis
 from app.services import official_question_analyses as analyses
 from types import SimpleNamespace
 estimate=copy.deepcopy(out['question']);estimate['percent']=70;estimate['sourceChecks'][1]['percent']=70;estimate['reasons']=['Publisher scheme contradicts question marks.']
 payload=RecordQuestionAnalysis(expectedQuestionRevision=q['revision'],expectedAnalysisVersion=q['analysisVersion'],expectedContentHash=q['analysisContentHash'],stage='accuracy',methodVersion='source-conflict-test',provenance=[dict(role=r,method='manual')for r in ['paper','scheme','report']],question=estimate,parts=[dict(label=p['label'],**copy.deepcopy(estimate))for p in q['data']['parts']])
 actor=db.scalar(select(User).where(User.username==auth_client[1]));analyses.record(db,SimpleNamespace(user=actor),uuid.UUID(root.split('/')[-1]),q['number'],payload)
 q=c.get(root).json()['questions'][0];req.update(expectedAnalysisVersion=q['analysisVersion'])
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]}).status_code==202
 process_next(db,get_settings(),storage,generator=FakeAIProvider(out).generate)
 after=c.get(root).json()['questions'][0];assert after['accuracyAnalysis']['question']['percent']==70
 assert 'Earlier checked source concern' in after['accuracyAnalysis']['parts'][0]['reasons'][-1]

@pytest.mark.integration
def test_content_change_during_generation_invalidates_result_and_workers_are_isolated(auth_client):
 c,h,db,root,q,req,out,storage=setup(auth_client)
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]}).status_code==202
 from app.services.evidence_link_jobs import process_next as evidence_worker
 assert evidence_worker(db,get_settings(),storage,generator=FakeAIProvider({}).generate) is None
 def changed(request):
  result=FakeAIProvider(out).generate(request)
  row=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(row.review_data);data['visualAltText']='Changed while model was processing';row.review_data=data;db.commit()
  return result
 process_next(db,get_settings(),storage,generator=changed)
 assert c.get(root+'/accuracy-jobs').json()[0]['errorCode']=='evidence_conflict'
 assert db.scalar(select(func.count()).select_from(OfficialQuestionAnalysis))==0

@pytest.mark.integration
def test_human_content_approval_and_image_decisions_are_preserved(auth_client):
 c,h,db,root,q,req,out,storage=setup(auth_client)
 row=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(row.review_data);data['parts'][0]['status']='approved';row.review_data=data;row.status='approved';db.commit()
 q=c.get(root).json()['questions'][0];req.update(expectedContentHash=q['analysisContentHash'])
 assert c.post(root+'/accuracy-jobs',headers=h,json={'questions':[req]}).status_code==202
 out['parts'][0]['manualReviewReasons']=['Source rubric needs adjudication.']
 process_next(db,get_settings(),storage,generator=FakeAIProvider(out).generate)
 after=c.get(root).json()['questions'][0]
 assert after['status']=='approved'and after['data']==data
 assert c.get(root+'/accuracy-readiness').json()['questions'][0]['manualContentParts']==[]
