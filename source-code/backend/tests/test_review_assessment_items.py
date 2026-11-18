import copy,uuid
from types import SimpleNamespace
import pytest
from sqlalchemy import select
from app.models import OfficialPaperReviewQuestion,OfficialQuestionVersion,MarkSchemeEntryVersion
from app.schemas.official_paper_reviews import ReviewQuestionData
from app.services import marking_rules,review_assessment_items,deterministic_validation
from test_auth_integration import auth_client
from test_deterministic_validation import configured

@pytest.mark.integration
def test_mixed_drafts_preserve_parent_inventory_and_frozen_certificate(auth_client,monkeypatch):
 c,h,db,root,q,proof=configured(auth_client)
 result=c.post(root+'/questions/1/validate-deterministic',headers=h,json=proof);assert result.status_code==200,result.text
 q=c.get(root).json()['questions'][0]
 row=db.scalar(select(OfficialPaperReviewQuestion));data=copy.deepcopy(row.review_data)
 b=copy.deepcopy(data['parts'][0]);b.update(label='b',prompt='Explain the sample property.',scoringRules={'version':1,'groups':[],'combinedResponses':[]},status='approved',assessmentReadiness='automatic')
 data['parts'].append(b);data['marks']+=b['marks'];row.review_data=data;db.commit()
 current=c.get(root).json()['questions'][0];old=q['accuracyAnalysis'];findings=copy.deepcopy(old['parts']);other=copy.deepcopy(findings[0]);other['label']='b';findings.append(other)
 r=c.post(root+'/questions/1/analyses',headers=h,json=dict(expectedQuestionRevision=current['revision'],expectedContentHash=current['analysisContentHash'],expectedAnalysisVersion=current['analysisVersion'],stage='accuracy',methodVersion=old['methodVersion'],provenance=old['provenance'],question=old['question'],parts=findings));assert r.status_code==201,r.text
 def forbidden(*a,**kw):pytest.fail('Draft projection must not invoke a provider')
 monkeypatch.setattr('app.ai.router.AIAccountRouter.generate',forbidden)
 state=c.get(root).json();assert state['automaticAssessmentReady'],state['assessmentBlockers']
 response=c.post(root+'/prepare-official-drafts',headers=h);assert response.status_code==200,response.text
 assert not response.json()['published']
 questions=db.scalars(select(OfficialQuestionVersion)).all()
 assert [(q.question_number,q.parent_number,q.marks)for q in sorted(questions,key=lambda q:q.question_number)]==[('1(a)','1',b['marks']),('1(b)','1',b['marks'])]
 entries={e.question_number:e for e in db.scalars(select(MarkSchemeEntryVersion))}
 deterministic=entries['1(a)'];semantic=entries['1(b)']
 assert deterministic.scoring_rules['deterministic']['parts'][0]['scoringRules']['deterministic']['certificateId']==proof['requestId']
 assert not semantic.scoring_rules.get('deterministic')
 item=next(q for q in questions if q.question_number=='1(a)')
 assert deterministic_validation.require_frozen_certificate(db,SimpleNamespace(shared_stem=item.shared_stem,prompt=item.prompt,marks=item.marks,rubric={'scoringRules':deterministic.scoring_rules,'markingPoints':deterministic.marking_points}))
 assert c.get(root).json()['expectedQuestionCount']==1  # Source question count unchanged.

 # Publish using the same source-to-draft reconciliation used in production.
 workspace=c.get(root).json()
 confirm=dict(confirmCourse=True,confirmSubject=True,confirmComplete=True,confirmSourcePaper=True)
 for key in ['paperDocumentId','schemeDocumentId']:
  published=c.post('/api/v1/documents/'+workspace[key]+'/official-review/publish',headers=h,json=confirm)
  assert published.status_code==200,published.text
 # Reports may still refer to the original parent; exact child advice wins.
 from app.models import DocumentBlock,OfficialPaperReviewWorkspace,OfficialMaterialVersion
 w=db.scalar(select(OfficialPaperReviewWorkspace))
 block=db.scalar(select(DocumentBlock).where(DocumentBlock.document_version_id==w.report_version_id))
 report=dict(expectedItemCount=2,completenessConfirmed=True,examinerComments=[dict(questionNumber=number,advice=[advice],sourceLocations=[dict(page=1,blockId=str(block.id))])for number,advice in [('1','Parent report advice'),('1(a)','Specific part advice')]])
 saved=c.post('/api/v1/documents/'+workspace['reportDocumentId']+'/official-review',headers=h,json=report);assert saved.status_code==200,saved.text
 published=c.post('/api/v1/documents/'+workspace['reportDocumentId']+'/official-review/publish',headers=h,json=confirm);assert published.status_code==200,published.text
 from app.services.assessments import _rubric
 paper_version=db.scalar(select(OfficialMaterialVersion).where(OfficialMaterialVersion.document_id==uuid.UUID(workspace['paperDocumentId']),OfficialMaterialVersion.status=='published'))
 assert _rubric(db,paper_version.id,'1(a)')['examinerAdvice']==['Specific part advice']
 assert _rubric(db,paper_version.id,'1(b)')['examinerAdvice']==['Parent report advice']
