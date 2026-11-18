import copy
from types import SimpleNamespace
import uuid
import pytest
from app.errors import DomainError
from app.schemas.marking_rules import MarkingRules
from app.services import deterministic_scoring as e
from app.services.deterministic_validation import Package,replay
from app.schemas.official_paper_reviews import ReviewQuestionData

POINTS=[dict(pointId='FULL',criterion='Correct final to two significant figures',maxMarks=1),dict(pointId='PARTIAL',criterion='Official partial-credit values',maxMarks=1)]
RULES=dict(version=3,scoreBands=[dict(id='rate',bands=[dict(pointId='FULL',marks=2),dict(pointId='PARTIAL',marks=1)])],deterministic=dict(engine='deterministic-v1',matchers=[
 dict(pointId='FULL',kind='numeric',values=[dict(value='0.057',significantFigures=2)],units=['g/h','grams per hour']),
 dict(pointId='PARTIAL',kind='numeric',values=[dict(value='11/192',roundedFrom=True,minimumSignificantFigures=3),dict(value='0.06'),dict(value='0.1')],units=['g/h','grams per hour'])]))

@pytest.mark.parametrize('text,marks',[
 ('0.057',2),('5.7e-2',2),('5.7 × 10⁻²',2),('0.057 grams per hour',2),
 ('0.0573',1),('0.05729',1),('0.0572916666667',1),('0.06',1),('0.1',1),('0.572',0),('2.75',0),('-0.057',0),
 ('{"final":"0.057","working":["(207.25-204.50)/48"]}',2)])
def test_actual_answer_to_score(text,marks):
 total,ds,audit=e.recognize(text,POINTS,2,RULES)
 assert total==sum(d.marksAwarded for d in ds)==marks
 assert audit['noModelCalls']

@pytest.mark.parametrize('text',['0.0570','0.057 or 0.06','I think 0.057','0.057 kg/h','NaN','1e999','__import__("os")','{"final":"0.057","working":["__import__(\"os\")"]}',''])
def test_ambiguous_or_unsupported_grammar_abstains(text):
 with pytest.raises(DomainError)as exc:e.recognize(text,POINTS,2,RULES)
 assert exc.value.code=='deterministic_requires_review'

def test_labelled_identification_is_not_unordered_keyword_matching():
 ps=[dict(pointId='W',criterion='W lens',maxMarks=1),dict(pointId='X',criterion='X cornea',maxMarks=1)]
 rules=dict(version=3,deterministic=dict(matchers=[dict(pointId='W',kind='choice',answerKey='W',accepted=['lens'],rejected=['cornea']),dict(pointId='X',kind='choice',answerKey='X',accepted=['cornea'],rejected=['lens'])]))
 assert e.recognize('{"W":"lens","X":"cornea"}',ps,2,rules)[0]==2
 assert e.recognize('{"W":"cornea","X":"lens"}',ps,2,rules)[0]==0
 with pytest.raises(DomainError):e.recognize('lens cornea',ps,2,rules)
 with pytest.raises(DomainError):e.recognize('{"W":"not lens","X":"cornea"}',ps,2,rules)

def test_source_authorised_working_stage_not_keyword_credit():
 rules=copy.deepcopy(RULES);rules['deterministic']['matchers'][1]['methods']=[dict(operator='divide',right='3374',leftValues=['225','317'])]
 assert e.recognize('{"final":"6.67","working":["225/3374*100"]}',POINTS,2,rules)[0]==1
 with pytest.raises(DomainError):e.recognize('{"final":"6.67","working":["225/3375*100"]}',POINTS,2,rules)
 with pytest.raises(DomainError):e.expression('2**1000000000')
 with pytest.raises(DomainError):e.expression('1/0')

def test_version_and_matcher_completeness_and_legacy_dump():
 old={'version':1,'groups':[],'combinedResponses':[]}
 assert MarkingRules.model_validate(old).model_dump()==old
 bad=copy.deepcopy(RULES);bad['deterministic']['matchers'].pop()
 with pytest.raises(DomainError):e.validate(POINTS,2,bad)

def test_server_replay_uses_answers_not_supplied_model_matches():
 data=ReviewQuestionData.model_validate(dict(marks=2,parts=[dict(label='b',marks=2,prompt='Rate?',markingPoints=[dict(code=p['pointId'],text=p['criterion'])for p in POINTS],scoringRules=RULES)]))
 payload=Package(requestId=uuid.uuid4(),partLabel='b',expectedRevision=1,expectedEngineHash=e.engine_hash(),confirmSourceReviewed=True,sourceNotes='Original scheme has been inspected.',cases=[
 dict(answer='0.057',expectedMarks=2,expectedPoints=['FULL']),dict(answer='0.06',expectedMarks=1,expectedPoints=['PARTIAL']),dict(answer='0.572',expectedMarks=0),dict(answer='5.7e-2',expectedMarks=2,expectedPoints=['FULL'],holdout=True),dict(answer='unclear',requiresReview=True)])
 assert replay(data,data.parts[0],payload)['passed']
 payload.cases[0].expectedMarks=1
 assert not replay(data,data.parts[0],payload)['passed']


def test_required_member_set_and_extra_member_zero():
 ps=[dict(pointId='P1',criterion='C H O, no extra elements',maxMarks=1)]
 rules=dict(version=3,deterministic=dict(matchers=[dict(pointId='P1',kind='set',requiredMembers=[['carbon','C'],['hydrogen','H'],['oxygen','O']],extraMembers=['nitrogen','N'])]))
 for s in ['carbon, hydrogen and oxygen','O C H','C,H,O']:
  assert e.recognize(s,ps,1,rules)[0]==1
 assert e.recognize('C H O N',ps,1,rules)[0]==0
 assert e.recognize('carbon hydrogen',ps,1,rules)[0]==0
 with pytest.raises(DomainError):e.recognize('not carbon hydrogen oxygen',ps,1,rules)


def test_duplicate_fields_and_extreme_precision_refer_instead_of_false_zero():
 for s in ['{"final":"0.057","final":"0.572"}','0.057291666666666666666666666']:
  with pytest.raises(DomainError):e.recognize(s,POINTS,2,RULES)


def test_explicit_source_range_is_inclusive_and_not_an_inferred_tolerance():
 ps=[dict(pointId='R',criterion='Reviewed permitted interval',maxMarks=1)]
 rules=dict(version=3,deterministic=dict(matchers=[dict(pointId='R',kind='numeric',values=[dict(minimumValue='1/2',maximumValue='0.75')],units=['g'])]))
 for answer,score in [('0.5',1),('0.75 g',1),('6e-1',1),('0.499999',0),('0.750001',0),('-0.6',0)]:
  assert e.recognize(answer,ps,1,rules)[0]==score
 with pytest.raises(DomainError):e.recognize('0.6 kg',ps,1,rules)
 bad=copy.deepcopy(rules);bad['deterministic']['matchers'][0]['values'][0]['minimumValue']='2'
 with pytest.raises(DomainError):e.validate(ps,1,bad)
 with pytest.raises(ValueError):MarkingRules.model_validate(dict(version=3,deterministic=dict(matchers=[dict(pointId='R',kind='numeric',values=[dict(value='0.6',minimumValue='0.5',maximumValue='0.75')])])))
 # New optional bounds do not change serialization/fingerprints of earlier rules.
 value=MarkingRules.model_validate(RULES).model_dump()['deterministic']['matchers'][0]['values'][0]
 assert 'minimumValue'not in value and 'maximumValue'not in value
