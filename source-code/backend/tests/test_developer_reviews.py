"""Actual authenticated staged corrections; inference is forbidden."""
import copy,uuid
import pytest
from sqlalchemy import select
from app.models import AuditEvent
from test_auth_integration import auth_client  # noqa
from test_deterministic_validation import configured


def forbid_inference_and_jobs(monkeypatch):
 def forbidden(*args,**kwargs):pytest.fail('Prepared review must not route inference, reserve model quota or create AI jobs')
 for path in ['app.ai.router.AIAccountRouter.generate','app.services.accuracy_jobs.create_batch','app.services.evidence_link_jobs.create','app.services.tutor_quotas.reserve_text','app.services.tutor_quotas.reserve_voice']:
  monkeypatch.setattr(path,forbidden)


def package(auth_client,monkeypatch):
 c,h,db,root,q,_=configured(auth_client)
 forbid_inference_and_jobs(monkeypatch)
 exported=c.get(root+'/review-package').json();part=q['data']['parts'][0];label=part['label']
 finding=copy.deepcopy(next(p for p in q['accuracyAnalysis']['parts']if p['label']==label))
 body=dict(requestId=str(uuid.uuid4()),number=q['number'],expectedRevision=q['revision'],expectedContentHash=q['analysisContentHash'],expectedAnalysisVersion=q['analysisVersion'],
  reason='Exact synthetic source compared with corrected wording.',provenance=q['accuracyAnalysis']['provenance'],
  corrections=[dict(partLabel=label,expectedScopeHash=exported['questions'][0]['scopes'][label],fields=dict(examinerAdvice='Reviewed source commentary: revised fixture.'),sourceFinding=finding)])
 return c,h,db,root,q,body

@pytest.mark.integration
def test_stage_preview_apply_receipt_and_rollback(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 def forbidden(*a,**k):pytest.fail('Developer correction must not invoke a model')
 monkeypatch.setattr('app.ai.router.AIAccountRouter.generate',forbidden)
 assert c.post(root+'/change-sets',json=body).status_code==403
 r=c.post(root+'/change-sets',headers=h,json=body);assert r.status_code==201,r.text
 key=r.json()['id'];assert c.get(root).json()['questions'][0]['revision']==q['revision']
 assert c.post(root+'/change-sets',headers=h,json=body).json()['id']==key
 preview=c.get(root+f'/change-sets/{key}/preview');assert preview.status_code==200,preview.text
 assert preview.json()['noInference']and not preview.json()['formalPublication']
 request=dict(requestId=str(uuid.uuid4()),expectedPreviewHash='f'*64)
 assert c.post(root+f'/change-sets/{key}/apply',headers=h,json=request).status_code==409
 assert c.get(root).json()['questions'][0]['revision']==q['revision']
 request['expectedPreviewHash']=preview.json()['previewHash']
 result=c.post(root+f'/change-sets/{key}/apply',headers=h,json=request);assert result.status_code==200,result.text
 assert result.json()['modelInvocations']==0
 assert c.post(root+f'/change-sets/{key}/apply',headers=h,json=request).json()['analysisId']==result.json()['analysisId']
 current=c.get(root).json()['questions'][0]
 assert current['accuracyAnalysis']['isCurrent']
 assert current['data']['parts'][0]['examinerAdvice']=='Reviewed source commentary: revised fixture.'
 assert c.get(root+'/review-history').status_code==200
 readiness=c.get(root+'/readiness');assert readiness.status_code==200,readiness.text
 assert readiness.json()['parts'][0]['sourceAccuracy']['current']

@pytest.mark.integration
def test_unknown_status_fields_and_stale_edits_are_rejected(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 body['corrections'][0]['fields']['status']='ai_approved'
 assert c.post(root+'/change-sets',headers=h,json=body).status_code==422
 del body['corrections'][0]['fields']['status']
 body['expectedRevision']+=1
 assert c.post(root+'/change-sets',headers=h,json=body).status_code==409

@pytest.mark.integration
def test_release_validation_is_not_publication_and_batch_is_resumable(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 r=c.post(root+'/change-sets',headers=h,json=body);assert r.status_code==201,r.text
 key=r.json()['id'];preview=c.get(root+f'/change-sets/{key}/preview').json()
 batch=dict(requestId=str(uuid.uuid4()),items=[key],previewHashes={key:preview['previewHash']})
 r=c.post(root+'/review-batches',headers=h,json=batch);assert r.status_code==201,r.text
 assert r.json()['completed']==1
 again=c.post(root+f"/review-batches/{batch['requestId']}/resume",headers=h,json=batch)
 assert again.status_code==200 and again.json()['completed']==1
 check=c.post(root+'/release-validation',headers=h,json=dict(target='formal_exam'))
 assert check.status_code==200 and not check.json()['published']

@pytest.mark.integration
def test_issue_failure_rolls_back_the_whole_correction(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 body['issueDecisions']=[dict(issueId='a'*64,partLabel=body['corrections'][0]['partLabel'],disposition='corrected_and_rechecked',note='Unknown issue must roll back content and analysis.')]
 r=c.post(root+'/change-sets',headers=h,json=body);assert r.status_code==201,r.text
 key=r.json()['id'];preview=c.get(root+f'/change-sets/{key}/preview').json()
 r=c.post(root+f'/change-sets/{key}/apply',headers=h,json=dict(requestId=str(uuid.uuid4()),expectedPreviewHash=preview['previewHash']))
 assert r.status_code==409
 current=c.get(root).json()['questions'][0]
 assert current['revision']==q['revision']and current['analysisVersion']==q['analysisVersion']and current['data']==q['data']

@pytest.mark.integration
def test_unchanged_sibling_finding_and_approval_are_carried_forward(auth_client,monkeypatch):
 from app.models import OfficialPaperReviewQuestion
 from app.services import review_scopes
 from app.schemas.paper_analysis import RecordQuestionAnalysis
 from app.services import official_question_analyses
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 data=copy.deepcopy(q['data']);second=copy.deepcopy(data['parts'][0]);second['label']='b';second['status']='unreviewed';data['parts'].append(second);data['marks']*=2
 r=c.post(root+'/questions',headers=h,json=dict(number=q['number'],expectedRevision=q['revision'],status='unreviewed',data=data));assert r.status_code==200,r.text
 q=c.get(root).json()['questions'][0]
 prior=copy.deepcopy(q['accuracyAnalysis']);parts=prior['parts'];other=copy.deepcopy(parts[0]);other['label']='b';parts.append(other)
 recorded=c.post(root+'/questions/1/analyses',headers=h,json=dict(expectedQuestionRevision=q['revision'],expectedAnalysisVersion=q['analysisVersion'],expectedContentHash=q['analysisContentHash'],stage='accuracy',methodVersion=prior['methodVersion'],provenance=prior['provenance'],question=prior['question'],parts=parts));assert recorded.status_code==201,recorded.text
 q=c.get(root).json()['questions'][0];before=copy.deepcopy(q['data']['parts'][1]);exports=c.get(root+'/review-package').json()['questions'][0]
 body.update(requestId=str(uuid.uuid4()),expectedRevision=q['revision'],expectedAnalysisVersion=q['analysisVersion'],expectedContentHash=q['analysisContentHash'])
 body['corrections'][0]['expectedScopeHash']=exports['scopes'][body['corrections'][0]['partLabel']]
 original_scheme=next(p for p in q['accuracyAnalysis']['provenance']if p['role']=='scheme')
 body['provenance']=[dict(role='scheme',method='codex_assisted',modelId='new-correction-model',notes='Synthetic new model attribution.')if p['role']=='scheme'else p for p in body['provenance']]
 key=c.post(root+'/change-sets',headers=h,json=body).json()['id'];preview=c.get(root+f'/change-sets/{key}/preview').json()
 result=c.post(root+f'/change-sets/{key}/apply',headers=h,json=dict(requestId=str(uuid.uuid4()),expectedPreviewHash=preview['previewHash']));assert result.status_code==200,result.text
 current=c.get(root).json()['questions'][0]
 assert current['data']['parts'][1]==before
 assert current['accuracyAnalysis']['reviewOrigins']['b']['kind']=='carried_forward'
 sibling=next(p for p in current['accuracyAnalysis']['parts']if p['label']=='b')
 assert next(p for p in sibling['provenance']if p['role']=='scheme')['modelId']==original_scheme['modelId']
 # A later actual edit to a only invalidates a; b retains its bound AI approval.
 row=db.scalar(select(OfficialPaperReviewQuestion));edited=copy.deepcopy(row.review_data);edited['parts'][0]['prompt']+=' Changed source.';row.review_data=edited;db.commit()
 shown=c.get(root).json()['questions'][0]
 assert shown['data']['parts'][0]['status']=='unreviewed'
 assert shown['data']['parts'][1]['status']=='ai_approved'
 assert shown['accuracyAnalysis']['partCurrent']=={'a':False,'b':True}

@pytest.mark.integration
def test_all_developer_routes_require_authentication_and_write_csrf(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 key=str(uuid.uuid4())
 reads=['/readiness','/review-package','/review-history',f'/change-sets/{key}',f'/change-sets/{key}/preview',f'/review-batches/{key}']
 writes=['/change-sets',f'/change-sets/{key}/apply','/questions/1/auto-approval','/release-validation','/review-batches',f'/review-batches/{key}/resume']
 for path in writes:assert c.post(root+path,json={}).status_code==403,path
 assert c.post('/api/v1/auth/logout',headers=h).status_code==204
 for path in reads:assert c.get(root+path).status_code==401,path
 for path in writes:assert c.post(root+path,json={}).status_code==401,path

@pytest.mark.integration
def test_shared_context_requires_finding_for_every_affected_sibling(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 # A changed human-approved scope needs an explicit reopen, never a status patch.
 from app.models import OfficialPaperReviewQuestion
 row=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(row.review_data);data['parts'][0]['status']='approved';row.review_data=data;db.commit()
 body['sharedFields']={'sharedStem':'Revised shared scientific context.'}
 response=c.post(root+'/change-sets',headers=h,json=body)
 assert response.status_code==409 and response.json()['error']['code']=='review_reopen_required'

@pytest.mark.integration
def test_scoped_approval_retry_returns_durable_receipt(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 payload=dict(requestId=str(uuid.uuid4()),expectedRevision=q['revision'],partLabels=[q['data']['parts'][0]['label']])
 endpoint=root+'/questions/'+q['number']+'/auto-approval'
 result=c.post(endpoint,headers=h,json=payload);assert result.status_code==200,result.text
 assert c.post(endpoint,headers=h,json=payload).json()==result.json()


def test_excluded_report_guidance_stays_excluded():
 from types import SimpleNamespace
 from app.services.paper_source_issues import report_usable
 question_id=uuid.uuid4();issue='a'*64
 analysis=SimpleNamespace(question_id=question_id,content_hash='b'*64,analysis_data={'question':{'confidencePolicy':'extraction-v1'},'parts':[{'label':'a','sourceChecks':[{'role':'report','status':'checked','percent':99}]}]})
 event=SimpleNamespace(target_id=str(question_id),event_data={'issueId':issue,'partLabel':'a','contentHash':'b'*64,'disposition':'report_guidance_excluded'})
 assert not report_usable(analysis,'a',[event])

@pytest.mark.integration
def test_malformed_typed_content_is_a_safe_validation_error(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 body['corrections'][0]['fields']={'marks':'not a number'}
 result=c.post(root+'/change-sets',headers=h,json=body)
 assert result.status_code==422 and result.json()['error']['code']=='review_content_invalid'
 assert c.get(root).json()['questions'][0]['data']==q['data']

@pytest.mark.integration
@pytest.mark.parametrize('role',['parent','student'])
def test_non_admin_denied_every_developer_route(auth_client,role,monkeypatch):
 from app.models import User
 from app.security import hash_password
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 user=User(username='review-'+uuid.uuid4().hex,display_name='Review role fixture',role=role,password_hash=hash_password('role fixture password'),must_change_password=False)
 db.add(user);db.commit()
 assert c.post('/api/v1/auth/logout',headers=h).status_code==204
 assert c.post('/api/v1/auth/login',json={'username':user.username,'password':'role fixture password'}).status_code==200
 key=str(uuid.uuid4())
 for path in ['/readiness','/review-package','/review-history',f'/change-sets/{key}',f'/change-sets/{key}/preview',f'/review-batches/{key}']:
  assert c.get(root+path).status_code==403,path
 for path in ['/change-sets',f'/change-sets/{key}/apply','/questions/1/auto-approval','/release-validation','/review-batches',f'/review-batches/{key}/resume']:
  assert c.post(root+path,headers=h,json={}).status_code==403,path

@pytest.mark.integration
def test_batch_partial_commit_and_resume_does_not_refresh_conflicting_hashes(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 ids=[];hashes={}
 for advice in ['First prepared comparison.','Conflicting prepared comparison.']:
  item=copy.deepcopy(body);item['requestId']=str(uuid.uuid4());item['corrections'][0]['fields']['examinerAdvice']=advice
  result=c.post(root+'/change-sets',headers=h,json=item);assert result.status_code==201,result.text
  key=result.json()['id'];ids.append(key);hashes[key]=c.get(root+f'/change-sets/{key}/preview').json()['previewHash']
 payload=dict(requestId=str(uuid.uuid4()),items=ids,previewHashes=hashes,stopOnConflict=False)
 result=c.post(root+'/review-batches',headers=h,json=payload);assert result.status_code==201,result.text
 assert result.json()['completed']==1 and result.json()['total']==2
 assert result.json()['attempt'][1]['state']=='blocked'
 revision=c.get(root).json()['questions'][0]['revision']
 retried=c.post(root+f"/review-batches/{payload['requestId']}/resume",headers=h,json=payload)
 assert retried.status_code==200 and retried.json()['completed']==1
 assert c.get(root).json()['questions'][0]['revision']==revision

@pytest.mark.integration
def test_wrong_paper_and_invented_visual_fail_closed(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 result=c.post(root+'/change-sets',headers=h,json=body);assert result.status_code==201,result.text
 key=result.json()['id']
 wrong='/api/v1/admin/official-paper-reviews/'+str(uuid.uuid4())
 assert c.get(wrong+f'/change-sets/{key}').status_code==404
 body['requestId']=str(uuid.uuid4())
 body['visualDecisions']=[dict(assetId=str(uuid.uuid4()),expectedSha256='a'*64,sourceRole='scheme',partLabel=body['corrections'][0]['partLabel'],decision='approve',caption='Fixture',altText='An invented asset must not be approved.')]
 assert c.post(root+'/change-sets',headers=h,json=body).status_code==409
 assert c.get(root).json()['questions'][0]['data']==q['data']

@pytest.mark.integration
def test_publication_change_invalidates_an_already_reviewed_preview(auth_client,monkeypatch):
 from app.models import TextbookTopicContentVersion
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 staged=c.post(root+'/change-sets',headers=h,json=body);assert staged.status_code==201,staged.text
 key=staged.json()['id'];preview=c.get(root+f'/change-sets/{key}/preview').json()
 publication=db.scalar(select(TextbookTopicContentVersion));assert publication is not None
 publication.status='superseded';db.commit()
 response=c.post(root+f'/change-sets/{key}/apply',headers=h,json={'requestId':str(uuid.uuid4()),'expectedPreviewHash':preview['previewHash']})
 assert response.status_code==409,response.text
 assert c.get(root).json()['questions'][0]['revision']==q['revision']

@pytest.mark.integration
def test_visual_preview_rolls_back_tentative_asset_metadata(auth_client,monkeypatch):
 from app.models import DocumentAsset,OfficialPaperReviewWorkspace
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 w=db.scalar(select(OfficialPaperReviewWorkspace))
 asset=db.scalar(select(DocumentAsset).where(DocumentAsset.document_version_id==w.paper_version_id))
 assert asset is not None
 original=copy.deepcopy(asset.asset_metadata);asset.asset_metadata={**original,'reviewCrop':True,'reviewApproved':False};db.commit()
 q=c.get(root).json()['questions'][0];scopes=c.get(root+'/review-package').json()['questions'][0]['scopes']
 body.update(expectedRevision=q['revision'],expectedContentHash=q['analysisContentHash'],expectedAnalysisVersion=q['analysisVersion'])
 body['corrections'][0]['expectedScopeHash']=scopes[body['corrections'][0]['partLabel']]
 body['visualDecisions']=[dict(assetId=str(asset.id),expectedSha256=asset.sha256,sourceRole='paper',partLabel=body['corrections'][0]['partLabel'],decision='approve',caption='Reviewed fixture visual',altText='Reviewed fixture visual including its original scientific labels.')]
 staged=c.post(root+'/change-sets',headers=h,json=body);assert staged.status_code==201,staged.text
 result=c.get(root+f"/change-sets/{staged.json()['id']}/preview");assert result.status_code==200,result.text
 db.refresh(asset)
 assert asset.asset_metadata=={**original,'reviewCrop':True,'reviewApproved':False}
 assert c.get(root).json()['questions'][0]['revision']==q['revision']

@pytest.mark.integration
def test_wording_correction_keeps_aggregate_prompt_consistent(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 body['sharedFields']={'sharedStem':q['data']['sharedStem']}
 body['corrections'][0]['fields']={'prompt':'Explain the corrected fixture concept.'}
 staged=c.post(root+'/change-sets',headers=h,json=body);assert staged.status_code==201,staged.text
 key=staged.json()['id'];preview=c.get(root+f'/change-sets/{key}/preview').json()
 assert 'Explain the corrected fixture concept.'in preview['assembledPrompt']['after']
 response=c.post(root+f'/change-sets/{key}/apply',headers=h,json={'requestId':str(uuid.uuid4()),'expectedPreviewHash':preview['previewHash']})
 assert response.status_code==200,response.text
 assert 'Explain the corrected fixture concept.'in c.get(root).json()['questions'][0]['data']['prompt']

@pytest.mark.integration
def test_incompatible_finding_policy_is_a_safe_atomic_error(auth_client,monkeypatch):
 c,h,db,root,q,body=package(auth_client,monkeypatch)
 body['corrections'][0]['sourceFinding']['confidencePolicy']='legacy'if q['accuracyAnalysis']['question']['confidencePolicy']=='extraction-v1'else'extraction-v1'
 staged=c.post(root+'/change-sets',headers=h,json=body);assert staged.status_code==201,staged.text
 key=staged.json()['id'];preview=c.get(root+f'/change-sets/{key}/preview').json()
 result=c.post(root+f'/change-sets/{key}/apply',headers=h,json={'requestId':str(uuid.uuid4()),'expectedPreviewHash':preview['previewHash']})
 assert result.status_code==422 and result.json()['error']['code']=='review_analysis_invalid'
 assert c.get(root).json()['questions'][0]['revision']==q['revision']
