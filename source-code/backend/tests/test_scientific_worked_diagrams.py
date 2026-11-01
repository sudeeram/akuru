"""Source-bound qualitative models share the ordinary private approval lifecycle."""
import copy
import pytest
import pymupdf
from pydantic import ValidationError
from app.schemas.scientific_diagrams import DiagramSolution, DiagramInput, Ion
from app.schemas.worked_answers import ImportWorkedAnswerDraft
from app.services.worked_answers.graphs import render,validate_source
from app.models import GeneratedWorkedAnswer
from test_auth_integration import auth_client  # noqa
from test_official_paper_review_workspace import _setup,_question

FACTS=[{'kind':'volume_time','xLabel':'Time','yLabel':'Volume'},
       {'kind':'exothermic_profile','reactants':'Mg + 2HCl','products':'MgCl₂ + H₂'},
       {'kind':'ionic_pair','ions':[{'symbol':'Mg','atomicNumber':12,'charge':2},{'symbol':'O','atomicNumber':8,'charge':-2}]}]

def payload(facts):
    graph={'schemaVersion':'science-diagram-v1','facts':facts,'partLabels':['a'],
           'verificationNote':'Verified all scientific facts against the exact original question and scheme.'}
    solution={'schemaVersion':'science-diagram-v1','title':'Synthetic science model','facts':facts,
              'steps':[{'partLabel':'a','explanation':'Illustrative model matching the exact reviewed scientific marking criteria.'}],
              'limitations':'Qualitative, not measured geometry; independent scientific approval is required.',
              'confidencePercent':95,'confidenceBasis':'Checked the source facts; an independent scientific review is still required.'}
    return {'expectedQuestionRevision':1,'graph':graph,'solution':solution,'generationNote':'Codex-prepared candidate from verified sources, requiring Admin approval.'}

@pytest.mark.parametrize('facts',FACTS)
def test_typed_models_preserve_facts_and_render_inert_png(facts):
    parsed=ImportWorkedAnswerDraft.model_validate(payload(facts))
    validate_source(parsed.solution,parsed.graph.model_dump())
    raw=render(parsed.solution,0);pix=pymupdf.Pixmap(raw)
    assert (pix.width,pix.height)==(1200,960)
    changed=copy.deepcopy(parsed.graph.model_dump());changed['partLabels']=['b']
    with pytest.raises(ValueError,match='subparts'):validate_source(parsed.solution,changed)
    changed=copy.deepcopy(parsed.graph.model_dump());changed['facts']['kind']='invalid'
    with pytest.raises(ValueError,match='scientific facts'):validate_source(parsed.solution,changed)

def test_ion_shells_and_invalid_or_executable_inputs():
    assert Ion(symbol='Mg',atomicNumber=12,charge=2).shells()==[2,8]
    assert Ion(symbol='O',atomicNumber=8,charge=-2).shells()==[2,8]
    for value in [dict(symbol='O',atomicNumber=12,charge=2),dict(symbol='Mg',atomicNumber=12,charge=0)]:
        with pytest.raises(ValidationError):Ion(**value)
    bad=payload(FACTS[0]);bad['solution']['script']='alert(1)'
    with pytest.raises(ValidationError):ImportWorkedAnswerDraft.model_validate(bad)
    bad=payload(FACTS[0]);bad['solution']['steps']*=2
    with pytest.raises(ValidationError):ImportWorkedAnswerDraft.model_validate(bad)

@pytest.mark.integration
@pytest.mark.parametrize('facts',FACTS)
def test_science_draft_preview_approval_and_private_attachment(auth_client,facts):
    client,headers,db,paper,scheme,report,topic=_setup(auth_client)
    GeneratedWorkedAnswer.__table__.create(db.connection(),checkfirst=True)
    root=f'/api/v1/admin/official-paper-reviews/{paper[0].id}'
    assert client.post(root+'/start',headers=headers,json={'schemeDocumentId':str(scheme[0].id)}).status_code==200
    question=_question(paper,scheme,topic);question['status']='needs_correction'
    assert client.post(root+'/questions',headers=headers,json=question).status_code==200
    endpoint=root+'/questions/1/worked-answers'
    body=payload(facts)
    assert client.post(endpoint+'/import-draft',json=body).status_code==403
    created=client.post(endpoint+'/import-draft',headers=headers,json=body)
    assert created.status_code==201,created.text
    row=created.json();assert row['status']=='awaiting_review' and row['assets']==[]
    assert client.post(endpoint+'/import-draft',headers=headers,json=body).json()['id']==row['id']
    before=client.get(root).json()['questions'][0]
    assert before['data']['parts'][0].get('answerVisuals',[])==[]
    assert client.get(endpoint+f"/{row['id']}/steps/0/image").content.startswith(b'\x89PNG')
    approval=client.post(endpoint+f"/{row['id']}/review",headers=headers,json={'expectedRevision':row['revision'],'action':'approve'})
    assert approval.status_code==200,approval.text
    saved=client.get(root).json()['questions'][0];visual=saved['data']['parts'][0]['answerVisuals'][0]
    assert visual['origin']=='ai_generated' and visual['workedAnswerId']==row['id']
    assert visual['status']=='approved' and visual['dataText']
    assert saved['status']==before['status']

@pytest.mark.parametrize('facts,point',[(FACTS[0],(350,318)),(FACTS[1],(400,376))])
def test_curves_do_not_close_into_spurious_answer_lines(facts,point):
    # Closing a Bézier path draws a scientifically incorrect diagonal chord.
    solution=ImportWorkedAnswerDraft.model_validate(payload(facts)).solution
    pix=pymupdf.Pixmap(render(solution,0))
    assert all(c>240 for c in pix.pixel(round(point[0]*1.5),round(point[1]*1.5)))

@pytest.mark.integration
def test_two_models_on_one_question_keep_both_subpart_answers(auth_client):
    client,headers,db,paper,scheme,report,topic=_setup(auth_client)
    GeneratedWorkedAnswer.__table__.create(db.connection(),checkfirst=True)
    root=f'/api/v1/admin/official-paper-reviews/{paper[0].id}'
    client.post(root+'/start',headers=headers,json={'schemeDocumentId':str(scheme[0].id)})
    question=_question(paper,scheme,topic);question['status']='needs_correction'
    second=copy.deepcopy(question['data']['parts'][0]);second['label']='b'
    question['data']['parts'].append(second);question['data']['marks']=4
    assert client.post(root+'/questions',headers=headers,json=question).status_code==200
    endpoint=root+'/questions/1/worked-answers';drafts=[]
    for label,facts in zip(('a','b'),FACTS[:2]):
        body=payload(facts);body['graph']['partLabels']=[label];body['solution']['steps'][0]['partLabel']=label
        created=client.post(endpoint+'/import-draft',headers=headers,json=body)
        assert created.status_code==201,created.text
        drafts.append(created.json())
    for row in drafts:
        approval=client.post(endpoint+f"/{row['id']}/review",headers=headers,json={'expectedRevision':row['revision'],'action':'approve'})
        assert approval.status_code==200,approval.text
    saved=client.get(root).json()['questions'][0]
    assert [p['answerVisuals'][0]['workedAnswerId'] for p in saved['data']['parts']]==[r['id'] for r in drafts]
    assert all(r['status']=='approved' for r in client.get(endpoint).json())
