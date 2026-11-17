import json
import uuid

import pytest
from sqlalchemy import select

from app.config import get_settings
from app.models import EvidenceLinkJob, OfficialPaperReviewQuestion
from app.ai.base import AIResult, AIUsage
from app.services import paper_scoring_validation
from test_auth_integration import auth_client  # noqa
from test_paper_workflow import prepared, run


@pytest.mark.integration
@pytest.mark.parametrize('match', [True, False])
def test_synthetic_scoring_job_checks_marks_and_records_readiness(auth_client, match):
    c,h,db,root,q,req,out,storage,_,_=prepared(auth_client)
    run(c,h,db,root,req,out,storage)
    row = db.scalar(select(OfficialPaperReviewQuestion))
    from copy import deepcopy
    data = deepcopy(row.review_data)
    data['parts'][0].update(assessmentReadiness='manual_only', assessmentReadinessReason='Awaiting scoring validation.')
    row.review_data = data
    db.commit()
    q = c.get(root).json()['questions'][0]
    part = q['data']['parts'][0]
    codes = [p['code'] for p in part['markingPoints']]
    assert part['marks'] == len(codes) == 2
    jid = str(uuid.uuid4())
    body = dict(requestId=jid, partLabel=part['label'], expectedRevision=q['revision'], confirmReviewed=True,
                samples=[dict(answer='A credited synthetic example.', expectedPoints=codes),
                         dict(answer='A partial synthetic example.', expectedPoints=codes[:1]),
                         dict(answer='An incorrect synthetic example.', expectedPoints=[])])
    url = root+'/questions/1/validate-scoring'
    assert c.post(url,json=body).status_code == 403
    assert c.post(url,headers=h,json=body).status_code == 202
    calls=[]

    def generate(_db,_settings,request):
        assert "criterion and maxMarks EXACTLY" in request.instructions
        assert "without added quotation marks" in request.instructions
        task=json.loads(request.task)
        calls.append(task)
        awarded_codes = (codes if match and task['studentAnswer'].startswith('A credited') else
                         codes[:1] if task['studentAnswer'].startswith('A partial') else [])
        points=[dict(pointId=p['pointId'],criterion=p['criterion'],maxMarks=p['maxMarks'],
                     awarded=p['pointId'] in awarded_codes,marksAwarded=int(p['pointId'] in awarded_codes),studentEvidence=task['studentAnswer'],
                     rationale='Fixture outcome',confidence=0.99) for p in task['officialMarkingPoints']]
        output=(dict(decisions=points,overallConfidence=.99) if request.output_type.__name__=='AssessmentPassOne'
                else dict(decisions=points,confidence=.99,improvedAnswer='Fixture',teachingExplanation='Fixture'))
        return AIResult(request.output_type.model_validate(output),'fixture','fixture',None,AIUsage(),0,1)

    paper_scoring_validation.process_next(db,get_settings(),generator=generate)
    assert len(calls)==6
    job=c.get(root+'/scoring-validation/'+jid).json()
    assert job['status']=='completed',job
    assert job['result']['passed']==match
    saved=c.get(root).json()['questions'][0]
    assert saved['analysisVersion']==q['analysisVersion'] and saved['accuracyAnalysis']['isCurrent']
    if match:
        assert saved['data']['parts'][0]['assessmentReadinessReason'].startswith(paper_scoring_validation.PASS_PREFIX)
        saved['data']['parts'][0]['markingPoints'][0]['acceptedAnswers']=['A changed synonym']
        edited=c.post(root+'/questions',headers=h,json=dict(number='1',expectedRevision=saved['revision'],
                      status=saved['status'],data=saved['data']))
        assert edited.status_code==200,edited.text
        assert edited.json()['questions'][0]['data']['parts'][0]['assessmentReadiness']=='unreviewed'
    else:
        assert saved['data']==q['data']
    assert db.get(EvidenceLinkJob,uuid.UUID(jid)).request_data['payload']=={}
    assert c.post(url,headers=h,json=body).json()['id']==jid
