import copy
import pytest
from sqlalchemy import select
from app.models import OfficialPaperReviewQuestion
from app.services import accuracy_jobs, paper_source_issues
from test_auth_integration import auth_client  # noqa
from test_paper_workflow import prepared, run


@pytest.mark.integration
def test_low_report_fidelity_does_not_cap_extraction_or_release_correct_rubric(auth_client):
    c,h,db,root,q,req,out,storage,_,_=prepared(auth_client)
    for scope in [out['question'],*out['parts']]:
        report=next(s for s in scope['sourceChecks'] if s['role']=='report')
        report['percent']=65
    out['parts'][0]['issues']=[dict(kind='report_guidance',role='report',pages=[1],
        description='Generic examiner guidance does not match this source.')]
    job=run(c,h,db,root,req,out,storage)
    after=c.get(root).json()['questions'][0]
    assert after['accuracyAnalysis']['parts'][0]['percent']==95
    assert after['accuracyAnalysis']['parts'][0]['confidencePolicy']=='extraction-v1'
    assert job['result']['tutorReleases'][0]['enabled']
    from app.models import TutorPaperRelease
    release=db.scalar(select(TutorPaperRelease))
    assert release.snapshot['part']['examinerAdvice']==''


@pytest.mark.integration
def test_discrepancy_requires_audited_resolution_not_a_lower_score(auth_client):
    c,h,db,root,q,req,out,storage,_,_=prepared(auth_client)
    out['parts'][0]['issues']=[dict(kind='source_discrepancy',role='report',pages=[1],
        description='Report example reverses ovule and seed; official scheme is correct.')]
    job=run(c,h,db,root,req,out,storage)
    assert not job['result']['tutorReleases'][0]['enabled']
    after=c.get(root).json()['questions'][0]
    assert after['accuracyAnalysis']['parts'][0]['percent']==95
    assert after['data']['parts'][0]['status']=='ai_approved'
    issues=c.get(root+'/questions/1/source-issues').json()
    issue=issues['issues'][0]
    payload=dict(analysisId=issues['analysisId'],partLabel=issue['partLabel'],issueId=issue['id'],
        note='Use the authoritative scheme; retain the report typo as a documented publisher error.')
    assert c.post(root+'/questions/1/source-issues/resolve',json=payload).status_code==403
    assert c.post(root+'/questions/1/source-issues/resolve',headers=h,json=payload).status_code==200
    assert c.get(root+'/questions/1/source-issues').json()['issues'][0]['resolved']
    c.post(root+'/auto-tutor-release',headers=h,json={})
    assert c.get(root+'/chat-releases').json()[0]['current']
    # The same issue cannot vanish on a later model output; preserve its history.
    out['parts'][0]['issues']=[]
    fresh=c.get(root).json()['questions'][0]
    req.update(requestId=__import__('uuid').uuid4().hex, expectedRevision=fresh['revision'],
        expectedContentHash=fresh['analysisContentHash'],expectedAnalysisVersion=fresh['analysisVersion'])
    run(c,h,db,root,req,out,storage)
    assert c.get(root+'/questions/1/source-issues').json()['issues'][0]['resolved']
    # Material edits invalidate the earlier source-bound decision.
    row=db.scalar(select(OfficialPaperReviewQuestion)); data=copy.deepcopy(row.review_data)
    data['parts'][0]['prompt']+=' Revised wording.';row.review_data=data;row.revision+=1;db.commit()
    assert c.get(root+'/questions/1/source-issues').json()['analysisId'] is None
    assert not c.get(root+'/chat-releases').json()[0]['current']
