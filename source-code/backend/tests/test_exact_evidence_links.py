"""Versioned source links preserve history and fail closed on ambiguity."""
import copy,uuid,hashlib
import pymupdf,pytest
from sqlalchemy import select,func
from app.main import app
from app.models import DocumentBlock,OfficialPaperReviewQuestion,EvidenceLinkJob,OfficialPaperReviewWorkspace,DocumentVersion
from app.storage import get_storage
from app.ai.fake import FakeAIProvider
from app.config import get_settings
from app.services.evidence_link_jobs import process_next
from test_auth_integration import auth_client
from test_official_question_analyses import setup_analysis

def setup(auth_client):
 c,h,db,root,q,a=setup_analysis(auth_client)
 row=db.scalar(select(OfficialPaperReviewQuestion));row.status='unreviewed';data=copy.deepcopy(row.review_data)
 for p in data['parts']:
  p['status']='unreviewed'
  for role in ['paper','scheme']:p[role+'Sources']=[{**s,'blockId':None}for s in p[role+'Sources']]
 row.review_data=data;db.commit();q=c.get(root).json()['questions'][0]
 storage=app.dependency_overrides[get_storage]();workspace=db.scalar(select(OfficialPaperReviewWorkspace))
 for vid in [workspace.paper_version_id,workspace.scheme_version_id]:
  v=db.get(DocumentVersion,vid);pdf=pymupdf.open();pg=pdf.new_page(width=100,height=100);pg.insert_text((5,30),'Question 1 a Chromatogram',fontsize=5);pg.insert_text((5,45),'Explain spots and solvent',fontsize=5);content=pdf.tobytes();storage.put(v.object_key,content,'application/pdf');v.sha256=hashlib.sha256(content).hexdigest()
 db.commit();q=c.get(root).json()['questions'][0]
 return c,h,db,root,q,a,storage

def proposal(q,**kw):return dict(requestId=str(uuid.uuid4()),number=q['number'],expectedRevision=q['revision'],expectedContentHash=q['analysisContentHash'],**kw)
def imported(q):return proposal(q,selections=[dict(part='a',role=r,page=1,bounds=dict(x0=0,y0=.15,x1=1,y1=.55),reason='Compared exact source label and complete answer region.',confidence=93,sourceVerified=True)for r in ['paper','scheme']],provenance=[dict(role=r,method='codex_assisted',modelId='test-model',notes='Synthetic comparison.')for r in ['paper','scheme']])
def decision(q,run,**kw):return dict(proposalIds=[p['id']for p in run['proposals']],expectedRevision=q['revision'],expectedContentHash=q['analysisContentHash'],decision='apply',confirmSourceReview=True,**kw)

@pytest.mark.integration
def test_region_apply_retry_and_stale_accuracy(auth_client):
 c,h,db,root,q,a,storage=setup(auth_client);a.update(expectedQuestionRevision=q['revision'],expectedContentHash=q['analysisContentHash'])
 assert c.post(root+'/questions/1/analyses',headers=h,json=a).status_code==201
 q=c.get(root).json()['questions'][0];body=imported(q);r=c.post(root+'/evidence-links',headers=h,json=body);assert r.status_code==200,r.text
 run=r.json();assert c.post(root+'/evidence-links',headers=h,json=body).json()==run
 assert c.get(root+f'/evidence-links/{run["id"]}/{run["proposals"][0]["id"]}/preview').status_code==200
 endpoint=root+'/evidence-links/'+run['id']+'/review';r=c.post(endpoint,headers=h,json=decision(q,run));assert r.status_code==200,r.text
 new=r.json()['review']['questions'][0];assert not new['accuracyAnalysis']['isCurrent'];assert new['data']['parts'][0]['topicRefs']==q['data']['parts'][0]['topicRefs']
 assert len([s for s in new['data']['parts'][0]['paperSources']if s['blockId']])==1
 count=db.scalar(select(func.count()).select_from(DocumentBlock));assert c.post(endpoint,headers=h,json=decision(q,run)).json()['alreadyApplied'];assert db.scalar(select(func.count()).select_from(DocumentBlock))==count
 assert not r.json()['review']['assessmentReleaseReady']
 assert db.scalar(select(DocumentBlock).where(DocumentBlock.block_kind=='question')).text=='Question 1'

@pytest.mark.integration
@pytest.mark.parametrize('change',['wrong_block','wrong_page','unknown_part','bad_bounds','missing_model','unknown_field'])
def test_invalid_selection_before_writes(auth_client,change):
 c,h,db,root,q,*_=setup(auth_client);p=imported(q)
 if change=='wrong_block':p['selections'][0].pop('bounds');p['selections'][0]['blockId']=str(uuid.uuid4())
 if change=='wrong_page':p['selections'][0]['page']=99
 if change=='unknown_part':p['selections'][0]['part']='z'
 if change=='bad_bounds':p['selections'][0]['bounds']['x1']=0
 if change=='missing_model':p['provenance'][0].pop('modelId')
 if change=='unknown_field':p['selections'][0]['text']='invented answer'
 before=db.scalar(select(func.count()).select_from(DocumentBlock));r=c.post(root+'/evidence-links',headers=h,json=p);assert r.status_code==422,r.text;assert db.scalar(select(func.count()).select_from(DocumentBlock))==before

@pytest.mark.integration
def test_stale_approval_ambiguity_and_csrf(auth_client):
 c,h,db,root,q,*_=setup(auth_client)
 assert c.post(root+'/evidence-links',json=proposal(q)).status_code==403
 run=c.post(root+'/evidence-links',headers=h,json=imported(q)).json();endpoint=root+'/evidence-links/'+run['id']+'/review'
 assert c.post(endpoint,headers=h,json=decision(q,run,autoOnly=True)).status_code==409
 row=db.scalar(select(OfficialPaperReviewQuestion));row.status='approved';db.commit();assert c.post(endpoint,headers=h,json=decision(q,run)).status_code==409
 row.status='unreviewed';row.revision+=1;db.commit();assert c.post(endpoint,headers=h,json=decision(q,run)).status_code==409
 assert c.post('/api/v1/auth/logout',headers=h).status_code==204
 for path in ['/evidence-links','/evidence-link-jobs']:
  assert c.get(root+path).status_code==401
  assert c.post(root+path,json=proposal(q)).status_code==401

@pytest.mark.integration
def test_job_proposals_only_actual_model(auth_client):
 c,h,db,root,q,a,storage=setup(auth_client);body=proposal(q);r=c.post(root+'/evidence-link-jobs',headers=h,json=body);assert r.status_code==202,r.text
 assert c.post(root+'/evidence-link-jobs',headers=h,json=body).json()['id']==r.json()['id']
 fake=FakeAIProvider(dict(selections=imported(q)['selections']));process_next(db,get_settings(),storage,generator=fake.generate)
 job=db.scalar(select(EvidenceLinkJob));assert job.status=='completed',job.error_code
 run=c.get(root+'/evidence-links').json()[0];assert run['provenance'][0]['modelId']=='fake-structured-v1' and run['provenance'][0]['modelIdentitySource']=='provider_response'
 assert c.get(root).json()['questions'][0]==q
 assert fake.requests[0].pages and 'untrusted' in fake.requests[0].instructions

@pytest.mark.integration
def test_job_wrong_page_fails_closed(auth_client):
 c,h,db,root,q,a,storage=setup(auth_client);assert c.post(root+'/evidence-link-jobs',headers=h,json=proposal(q)).status_code==202
 selections=imported(q)['selections'];selections[0]['page']=999
 process_next(db,get_settings(),storage,generator=FakeAIProvider(dict(selections=selections)).generate)
 job=db.scalar(select(EvidenceLinkJob));assert job.status=='failed' and job.error_code=='invalid_ai_evidence';assert c.get(root+'/evidence-links').json()==[]

@pytest.mark.integration
def test_durable_batch_atomic_snapshots_and_idempotence(auth_client):
 c,h,db,root,q,a,storage=setup(auth_client)
 row=db.scalar(select(OfficialPaperReviewQuestion));second=OfficialPaperReviewQuestion(workspace_id=row.workspace_id,number='2',revision=1,status='unreviewed',review_data=copy.deepcopy(row.review_data));db.add(second);db.commit()
 questions=c.get(root).json()['questions'];bodies=[proposal(x)for x in questions]
 broken=copy.deepcopy(bodies);broken[1]['expectedRevision']+=1
 assert c.post(root+'/evidence-link-job-batch',headers=h,json={'questions':broken}).status_code==409
 assert db.scalar(select(func.count()).select_from(EvidenceLinkJob))==0
 r=c.post(root+'/evidence-link-job-batch',headers=h,json={'questions':bodies});assert r.status_code==202,r.text
 assert len(r.json())==2
 again=c.post(root+'/evidence-link-job-batch',headers=h,json={'questions':bodies});assert again.status_code==202
 assert [v['id']for v in again.json()]==[v['id']for v in r.json()]
 assert db.scalar(select(func.count()).select_from(EvidenceLinkJob))==2

@pytest.mark.integration
def test_parent_cannot_read_or_mutate_exact_evidence(auth_client):
 from app.models import User
 c,h,db,root,q,a,storage=setup(auth_client)
 user=db.scalar(select(User).where(User.username==auth_client[1]));user.role='parent';db.commit()
 for path in ['/evidence-links','/evidence-link-jobs']:
  assert c.get(root+path).status_code==403
  assert c.post(root+path,headers=h,json=proposal(q)).status_code==403
 assert c.post(root+'/evidence-link-job-batch',headers=h,json={'questions':[proposal(q)]}).status_code==403
