"""Source-derived Q3(b) bands: model evidence matching is separated from allocation."""
from types import SimpleNamespace
import pytest
from app.errors import DomainError
from app.schemas.marking_rules import MarkingRules
from app.schemas.assessments import MarkingDecision
from app.schemas.official_paper_reviews import ReviewQuestionData
from app.services.marking_rules import score, validate_rules, compile_review, expected_marks
from app.services.assessment_marking import _official_points, mark_text_answer
from app.ai.base import AIResult, AIUsage
from app.config import Settings
from app.services.subject_marking import policy
import json

RULES = {'version': 2, 'scoreBands': [{'id': 'rate', 'bands': [
    {'pointId': 'FULL', 'marks': 2}, {'pointId': 'PARTIAL', 'marks': 1}]}]}
RAW = [{'code': 'FULL', 'text': 'Correct rate to two significant figures: 0.057 g per hour, including 5.7 × 10⁻².'},
       {'code': 'PARTIAL', 'text': 'Scheme-approved one-mark result: 0.0573, 0.05729…, 0.06 or 0.1. Do not credit 0.572.'}]

def question():
    return SimpleNamespace(rubric={'markingPoints': RAW, 'scoringRules': RULES}, marks=2,
        prompt='Calculate the rate of mass loss to two significant figures.', question_number='3(b)',
        shared_stem='207.25 g to 204.50 g in 48 hours.', equations=[])

def rows(matched, answer):
    return [MarkingDecision(pointId=p['pointId'], criterion=p['criterion'], maxMarks=1,
        awarded=p['pointId'] in matched, marksAwarded=int(p['pointId'] in matched),
        studentEvidence=answer, rationale='Fixture evidence match', confidence=.99)
        for p in _official_points(question())]

@pytest.mark.parametrize('answer,matched,expected', [
    ('0.057 g per hour', ['FULL'], 2), ('5.7 × 10⁻² g per hour', ['FULL'], 2),
    ('0.0573', ['PARTIAL'], 1), ('0.05729', ['PARTIAL'], 1),
    ('0.06', ['PARTIAL'], 1), ('0.1', ['PARTIAL'], 1), ('0.572', [], 0),
    ('2.75', [], 0), ('0.05729, rounded to 0.057', ['FULL', 'PARTIAL'], 2)])
def test_q3b_allocation(answer, matched, expected):
    total, decisions, audit = score(rows(matched,answer),_official_points(question()),2,RULES,answer)
    assert total == sum(d.marksAwarded for d in decisions) == expected
    assert len([d for d in decisions if d.awarded]) <= 1
    assert audit['engine'] == 'structured-marking-v2'
    for d in decisions:
        MarkingDecision.model_validate(d.model_dump())


def test_untrusted_model_cannot_assign_band_marks_or_invent_evidence():
    bad=rows(['FULL'],'0.057');bad[0].marksAwarded=2
    with pytest.raises(DomainError,match='inconsistent'):
        score(bad,_official_points(question()),2,RULES,'0.057')
    with pytest.raises(DomainError,match='supporting phrase'):
        score(rows(['FULL'],'invented'),_official_points(question()),2,RULES,'0.572')
    with pytest.raises(DomainError,match='supporting phrase'):
        score(rows(['FULL'],' '),_official_points(question()),2,RULES,'0.572')
    p=_official_points(question());p[0]['acceptedAnswers']=['0.057']
    assert score(rows([], '0.057 but this is wrong'),p,2,RULES,'0.057 but this is wrong')[0] == 0


@pytest.mark.parametrize('mutation', [
    {'version':1},
    {'scoreBands':[{'id':'x','bands':[{'pointId':'UNKNOWN','marks':2},{'pointId':'PARTIAL','marks':1}]}]},
    {'scoreBands':[{'id':'x','bands':[{'pointId':'FULL','marks':3},{'pointId':'PARTIAL','marks':1}]}]},
    {'scoreBands':[{'id':'x','bands':[{'pointId':'FULL','marks':2},{'pointId':'FULL','marks':1}]}]},
    {'groups':[{'id':'cut','pointIds':['FULL'],'maxMarks':1}]},
    {'groups':[{'id':'cut','pointIds':['FULL','PARTIAL'],'maxMarks':1}]},
    {'combinedResponses':[{'phrase':'answer','pointIds':['FULL','PARTIAL']}]},
])
def test_invalid_bands_fail_closed(mutation):
    with pytest.raises(DomainError):validate_rules(_official_points(question()),2,RULES|mutation)


def test_expected_scores_and_legacy_hashes():
    assert expected_marks(['FULL'],RULES)==2
    assert expected_marks(['PARTIAL'],RULES)==1
    assert expected_marks([],RULES)==0
    with pytest.raises(DomainError):expected_marks(['FULL','PARTIAL'],RULES)
    old={'version':1,'groups':[],'combinedResponses':[]}
    assert MarkingRules.model_validate(old).model_dump()==old
    assert MarkingRules.model_validate(old).model_dump(mode='json')==old


def test_full_paper_compilation_preserves_weighted_subpart_scores():
    data=ReviewQuestionData.model_validate({'marks':3,'parts':[
        {'label':'b','marks':2,'markingPoints':RAW,'scoringRules':RULES},
        {'label':'c','marks':1,'markingPoints':[{'code':'P1','text':'Control temperature.'}]}]})
    compiled,rules=compile_review(data)
    assert rules['scoreBands'][0]['bands'][0]=={'pointId':'b.FULL','marks':2}
    ps=_official_points(SimpleNamespace(marks=3,rubric={'markingPoints':compiled,'scoringRules':rules}))
    ds=[MarkingDecision(pointId=p['pointId'],criterion=p['criterion'],maxMarks=1,awarded=True,
        marksAwarded=1,studentEvidence='answer',rationale='Fixture',confidence=.99)for p in ps]
    total,out,audit=score(ds,ps,3,rules,'answer')
    assert total==3 and audit['creditedPointIds']==['b.FULL','c.P1']
    assert sum(d.marksAwarded for d in out)==3


def test_two_pass_marking_returns_server_allocated_band_score():
    q=question();calls=[]
    def generate(_db,_settings,req):
        task=json.loads(req.task);calls.append(task)
        assert 'never assign the band score yourself' in req.instructions
        ds=[r.model_dump() for r in rows(['FULL'],task['studentAnswer'])]
        output=({'decisions':ds,'overallConfidence':.99} if req.output_type.__name__=='AssessmentPassOne'
            else {'decisions':ds,'confidence':.99,'improvedAnswer':'0.057 g per hour','teachingExplanation':'Divide mass lost by elapsed time.'})
        return AIResult(req.output_type.model_validate(output),'fixture','fixture',None,AIUsage(),0,1)
    deterministic={}
    result=mark_text_answer(None,Settings(),q,SimpleNamespace(answer_text='0.057',file_id=None),
        _official_points(q),[],policy('biology'),deterministic,None,'0.057',{},generate)
    assert len(calls)==2 and result[2]==2
    assert deterministic['rubricScoring']['creditedPointIds']==['FULL']
