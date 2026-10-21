from types import SimpleNamespace
import pytest
from app.errors import DomainError
from app.schemas.assessments import MarkingDecision
from app.schemas.official_paper_reviews import ReviewQuestionData
from app.services.marking_rules import score, validate_rules, compile_review
from app.services.assessment_marking import _official_points


def points():
    return [{"pointId": f"M{i}", "criterion": text, "maxMarks": 1, "acceptedAnswers": aliases}
            for i, (text, aliases) in enumerate([
                ("Bubbles", ["bubbles", "fizzing", "effervescence"]),
                ("Moves", ["moves"]), ("Floats", ["floats"]),
                ("Gets smaller", ["gets smaller", "disappears", "dissolves"])], 1)]


def decisions(awarded=(), evidence="moves on the surface"):
    return [MarkingDecision(pointId=p['pointId'], criterion=p['criterion'], maxMarks=1,
        awarded=p['pointId'] in awarded, marksAwarded=int(p['pointId'] in awarded),
        studentEvidence=evidence, rationale="Evidence checked", confidence=.95) for p in points()]


RULES = {"version": 1, "groups": [], "combinedResponses": [{"phrase": "moves on the surface", "pointIds": ["M2", "M3"]}]}


def test_any_two_cap_and_synonym_deduplication():
    total, rows, audit = score(decisions(['M1','M2','M3','M4']), points(), 2, RULES)
    assert total == sum(r.marksAwarded for r in rows) == 2
    assert len(audit['matchedPointIds']) == 4
    assert list(audit['pointOutcomes'].values()).count('matched_capped') == 2
    _, _, optional = score(decisions(['M1','M2']), points(), 2, RULES)
    assert optional['pointOutcomes']['M3'] == 'not_required'
    assert score(decisions(), points(), 2, RULES, 'fizzing; bubbles')[0] == 1


def test_exact_combined_response_and_negation_are_not_substring_matches():
    assert score(decisions(), points(), 2, RULES, 'moves on the surface')[0] == 2
    assert score(decisions(), points(), 2, RULES, 'does not move on the surface')[0] == 0
    assert score(decisions(), points(), 2, RULES, 'moves on the surface but sinks')[0] == 0
    assert score(decisions(), points(), 2, RULES, '')[0] == 0
    assert score(decisions(), points(), 2, RULES, 'does not float; floats')[0] == 0


@pytest.mark.parametrize('matched,expected', [([],0),(['M1'],1),(['M2','M3'],2),(['M1','M2','M3','M4'],2)])
def test_selected_point_combinations(matched,expected):
    assert score(decisions(matched), points(), 2, RULES)[0] == expected


def test_rejects_fabricated_evidence_duplicate_decisions_and_mutated_criteria():
    with pytest.raises(DomainError,match='supporting phrase'):
        score(decisions(['M1'], 'invented'),points(),2,RULES,'student text')
    rows=decisions();rows[1]=rows[0]
    with pytest.raises(DomainError,match='exactly once'):score(rows,points(),2,RULES)
    rows=decisions();rows[0].criterion='different'
    with pytest.raises(DomainError,match='changed'):score(rows,points(),2,RULES)


def test_group_caps_required_points_dependencies_and_invalid_graphs():
    p=points()
    rule={'groups':[{'id':'first','pointIds':['M1','M2'],'maxMarks':1},{'id':'second','pointIds':['M3','M4'],'maxMarks':1}]}
    assert score(decisions(['M1','M2','M3','M4']),p,3,rule)[0] == 2
    mandatory={'groups':[{'id':'all','pointIds':['M1','M2','M3','M4'],'maxMarks':3,'requiredForFullCredit':['M4']}]}
    assert score(decisions(['M1','M2','M3']),p,3,mandatory)[0] == 2
    p[1]['dependsOn']='M1'
    assert score(decisions(['M2']),p,4,{})[0] == 0
    p[1]['followThrough']=True
    assert score(decisions(['M2']),p,4,{})[0] == 1
    p[0]['dependsOn']='M2'
    with pytest.raises(DomainError,match='cycles'):validate_rules(p,2,{})
    with pytest.raises(DomainError,match='nested or disjoint'):
        validate_rules(points(),2,{'groups':[{'id':'x','pointIds':['M1','M2'],'maxMarks':1},{'id':'y','pointIds':['M2','M3'],'maxMarks':1}]})
    with pytest.raises(DomainError,match='existing points'):
        validate_rules(points(),2,{'combinedResponses':[{'phrase':'match','pointIds':['M1','bogus']}]})


def test_compilation_preserves_per_part_maxima_and_namespaces_private_rules():
    part={'label':'a','marks':2,'markingPoints':[{'code':p['pointId'],'text':p['criterion'],'acceptedAnswers':p['acceptedAnswers']} for p in points()], 'scoringRules':RULES}
    data=ReviewQuestionData.model_validate({'marks':3,'parts':[part,{'label':'b','marks':1,'markingPoints':[{'code':'M1','text':'Different answer'}]}]})
    compiled,rules=compile_review(data)
    assert rules['groups'][0]['maxMarks']==2
    assert rules['combinedResponses'][0]['pointIds']==['a.M2','a.M3']
    assert compiled[-1]['code']=='b.M1'
    frozen=_official_points(SimpleNamespace(marks=3,rubric={'markingPoints':compiled,'scoringRules':rules}))
    assert len(frozen)==5
    with pytest.raises(DomainError,match='exceed'):
        _official_points(SimpleNamespace(marks=3,rubric={'markingPoints':compiled}))


def test_required_points_keep_credit_when_group_is_full():
    rules={'groups':[{'id':'all','pointIds':['M1','M2','M3','M4'],'maxMarks':3,'requiredForFullCredit':['M4']}]}
    total,rows,_=score(decisions(['M1','M2','M3','M4']), points(),3,rules)
    assert total == 3
    assert next(r for r in rows if r.pointId=='M4').awarded
