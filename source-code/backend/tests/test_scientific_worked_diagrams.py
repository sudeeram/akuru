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
       {'kind':'roan_cross','parents':'roan_x_roan','target':'male_roan'},
       {'kind':'bubble_potometer','measurement':'water_uptake_proxy'},
       {'kind':'clotting_temperature','optimumC':37,'minimumC':30,'maximumC':42,'quantity':'time_to_clot'},
       {'kind':'ionic_pair','ions':[{'symbol':'Mg','atomicNumber':12,'charge':2},{'symbol':'O','atomicNumber':8,'charge':-2}]}]

FACTS.append({'kind':'ptc_cross','parents':'Tt_x_Tt','target':'male_taster'})

FACTS.extend([
    {'kind':'monohybrid_cross','dominantAllele':'B','recessiveAllele':'b','parents':['Bb','Bb'],'dominantPhenotype':'black','recessivePhenotype':'brown','target':'phenotype_ratio'},
    {'kind':'paired_line_graph','xAxis':{'label':'Time / days','minimum':0,'maximum':120,'tick':20},'yAxis':{'label':'Mean leaf area / cm²','minimum':0,'maximum':8000,'tick':1000},'labelA':'Room A','labelB':'Room B','points':[{'x':20,'yA':6,'yB':10},{'x':40,'yA':50,'yB':800}]},
    {'kind':'starch_leaf_halves','left':'outside_jar_starch_present','right':'inside_co2_absorbing_jar_starch_absent'},
    {'kind':'pyramid_of_numbers','levels':[{'label':'Oak trees','count':4},{'label':'Mice','count':20},{'label':'Foxes','count':2}]},
])

def test_number_pyramid_preserves_scale_trophic_order_and_equal_bar_heights():
    from app.services.worked_answers.biology_diagrams import render as render_biology,describe
    facts=ImportWorkedAnswerDraft.model_validate(payload(FACTS[-1])).solution.facts
    class Page:
        def __init__(self):self.bars=[]
        def draw_rect(self,rect,**kwargs):self.bars.append(rect)
    page=Page();labels=[]
    render_biology(page,facts,lambda rect,text,*args:labels.append(text),lambda *args:None,lambda *args:None)
    bars=page.bars
    assert len(bars)==3
    widths=[b[2]-b[0]for b in bars]
    assert widths[1]/widths[0]==5 and widths[0]/widths[2]==2
    assert len({b[3]-b[1]for b in bars})==1
    assert bars[0][3]>bars[1][3]>bars[2][3]
    assert len({(b[0]+b[2])/2 for b in bars})==1
    assert ['Oak trees: 4','Mice: 20','Foxes: 2']==[t for t in labels if ':'in t]
    assert 'bottom to top: Oak trees: 4; Mice: 20; Foxes: 2' in describe(facts)

@pytest.mark.parametrize('levels',[
    [{'label':'Trees','count':0},{'label':'Mice','count':20}],
    [{'label':'Trees','count':1.5},{'label':'Mice','count':20}],
    [{'label':'Trees','count':True},{'label':'Mice','count':20}],
    [{'label':'Trees','count':4},{'label':' trees ','count':20}],
    [{'label':' ','count':4},{'label':'Mice','count':20}],
    [{'label':'Trees','count':1},{'label':'Mice','count':1000}],
])
def test_number_pyramid_rejects_invalid_or_unreadable_source_counts(levels):
    with pytest.raises(ValidationError):
        ImportWorkedAnswerDraft.model_validate(payload({'kind':'pyramid_of_numbers','levels':levels}))

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


def test_biology_templates_reject_invented_measurements_and_unsupported_crosses():
    for facts,field,value in [(FACTS[2],'parents','red_x_white'),
                              (FACTS[3],'measurement','direct_transpiration'),
                              (FACTS[4],'optimumC',35),
                              (FACTS[4],'clottingSeconds',[10,20])]:
        body=payload(copy.deepcopy(facts));body['graph']['facts'][field]=value
        with pytest.raises(ValidationError):ImportWorkedAnswerDraft.model_validate(body)


def test_biology_accessible_descriptions_preserve_scientific_limits():
    from app.services.worked_answers.scientific_diagrams import describe_facts
    descriptions=[describe_facts(ImportWorkedAnswerDraft.model_validate(payload(f)).solution.facts) for f in FACTS[2:5]]
    assert '1/4 = 25%' in descriptions[0] and 'independent' in descriptions[0]
    assert 'proxy' in descriptions[1] and 'not a direct' in descriptions[1]
    assert 'minimum at 37' in descriptions[2] and 'No numerical clotting' in descriptions[2]


def test_ptc_cross_keeps_dominant_inheritance_distinct_from_roan():
    from app.services.worked_answers.scientific_diagrams import describe_facts
    body=payload(FACTS[6]);solution=ImportWorkedAnswerDraft.model_validate(body).solution
    description=describe_facts(solution.facts)
    assert '3/8 = 37.5%' in description and 'TT, Tt, Tt, tt' in description
    assert 'roan' not in description
    body['graph']['facts']['parents']='tt_x_Tt'
    with pytest.raises(ValidationError):ImportWorkedAnswerDraft.model_validate(body)


def test_monohybrid_outcomes_are_derived_and_cannot_override_probability():
    from fractions import Fraction
    from app.schemas.biology_worked_diagrams import MonohybridFacts
    f=MonohybridFacts(**(FACTS[7]|{'target':'male_dominant'}))
    assert f.outcomes()==['BB','Bb','Bb','bb'] and f.probability()==Fraction(3,8)
    f=MonohybridFacts(**(FACTS[7]|{'parents':['Bb','bb'],'target':'recessive'}))
    assert f.probability()==Fraction(1,2)
    for mutation in [{'parents':['Bb','CC']},{'recessiveAllele':'c'},{'probability':1}]:
        with pytest.raises(ValidationError):MonohybridFacts(**(FACTS[7]|mutation))


def test_paired_graph_rejects_unverified_geometry_and_source_data_changes():
    for mutate in ['outside','duplicate','labels']:
        body=payload(copy.deepcopy(FACTS[8]));f=body['graph']['facts']
        if mutate=='outside':f['points'][0]['yA']=9000
        if mutate=='duplicate':f['points'][1]['x']=20
        if mutate=='labels':f['labelB']=f['labelA']
        with pytest.raises(ValidationError):ImportWorkedAnswerDraft.model_validate(body)
    parsed=ImportWorkedAnswerDraft.model_validate(payload(FACTS[8]));source=parsed.graph.model_dump();source['facts']['points'][0]['yA']=7
    with pytest.raises(ValueError,match='scientific facts'):validate_source(parsed.solution,source)


def test_starch_regions_are_not_reversed_silently():
    body=payload(FACTS[9]);body['graph']['facts']=dict(body['graph']['facts'],left='starch_absent')
    with pytest.raises(ValidationError):ImportWorkedAnswerDraft.model_validate(body)
