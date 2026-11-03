"""Synthetic/public native-layout fixtures; no licensed source PDFs in CI."""
from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
import sys,json
from types import SimpleNamespace as Row

import pymupdf
import pytest
from app.services.assessments import official_paper_duration

scripts=Path(__file__).resolve().parents[2]/'scripts'
spec=spec_from_file_location('pearson_intake',scripts/'pearson_intake.py');intake=module_from_spec(spec);spec.loader.exec_module(intake)
spec=spec_from_file_location('pearson_import',scripts/'import-pearson-intake.py');importer=module_from_spec(spec);spec.loader.exec_module(importer)


def line(text,x=60,y=100,page=2):return dict(text=text,x=x,y=y,page=page,box=[x,y,x+100,y+10])


def test_mark_allocation_does_not_terminate_mc_options_and_dots_do_not_create_parts():
    records=[line('(a) Which group?',y=100),line('(1)',x=490,y=115),
        line('A bacteria',x=130,y=140),line('B viruses',x=130,y=160),
        line('(b) Explain.',y=200),line('(2)',x=490,y=220)]
    stem,parts,issues=intake.split_parts(records)
    assert [p['label'] for p in parts]==['a','b']
    assert [p['marks'] for p in parts]==[1,2]
    assert 'B viruses' in parts[0]['extractionCandidate']
    assert not issues


def test_nested_context_is_kept_for_each_child_and_cross_page_minor_continues():
    records=[line('Shared stem'),line('(a) Use this table.',y=120),line('(i) Name one.',y=140),
        line('(1)',x=490,y=150),line('(ii) Explain why.',y=60,page=3),line('(2)',x=490,y=80,page=3)]
    stem,parts,issues=intake.split_parts(records)
    assert stem=='Shared stem'
    assert [p['label'] for p in parts]==['a(i)','a(ii)']
    assert all('Use this table.' in p['extractionCandidate'] for p in parts)
    assert parts[1]['sourcePages']==[3]


def test_page_furniture_and_dotted_answer_slots_are_excluded_but_units_remain():
    pdf=pymupdf.open();page=pdf.new_page()
    for point,text in [((60,100),'(a) Calculate 5 cm3.'),((490,120),'(2)'),((60,160),'1 ...................'),((60,790),'P123456A0128'),((10,200),'DO NOT WRITE IN THIS AREA')]:page.insert_text(point,text)
    records=intake.line_records(pdf)
    assert [r['text'] for r in records]==['(a) Calculate 5 cm3.','(2)']
    assert intake.clean_text(records)=='(a) Calculate 5 cm3.'


def pdf_file(path,cover):
    path.parent.mkdir(parents=True,exist_ok=True);pdf=pymupdf.open();p=pdf.new_page();p.insert_text((60,80),cover);pdf.save(path);pdf.close()


def test_catalogue_verifies_paperbr_from_content_and_quarantines_wrong_report(tmp_path):
    for kind,prefix,internal in [('Question-paper','Questionpaper','2BR'),('Mark-Scheme','Markscheme','2BR'),('Examiner-report','Examinerreport','2B')]:
        pdf_file(tmp_path/kind/f'{prefix}-PaperBR-January2020.pdf',f'Biology 4BI1 Paper {internal}')
    rows=intake.catalogue(tmp_path)
    assert all(r['component']=='2BR' for r in rows)
    assert 'internal_component_conflict_or_unreadable' in next(r for r in rows if r['kind']=='examinerReport')['issues']
    assert not any('internal_component_conflict_or_unreadable' in r['issues'] for r in rows if r['kind']!='examinerReport')
    assert next(r for r in rows if r['kind']=='markScheme')['path'].startswith('Mark-Scheme')


def test_catalogue_keeps_provisional_as_distinct_source(tmp_path):
    pdf_file(tmp_path/'Markscheme-Paper1B-June2021.pdf','Mark Scheme Results 4BI1 Paper 1B')
    pdf_file(tmp_path/'ProvisionalMarkscheme-Paper1B-June2021.pdf','Mark Scheme Provisional 4BI1 Paper 1B')
    rows=intake.catalogue(tmp_path)
    assert len(rows)==2 and sum(r['provisional'] for r in rows)==1
    assert len({r['sha256'] for r in rows})==2


@pytest.mark.parametrize('component,minutes',[('1B',120),('1BR',120),('2B',75),('2BR',75),('1C',120),('2CR',75)])
def test_biology_and_chemistry_official_timers(component,minutes):
    assert official_paper_duration(Row(component=component,source_metadata={}),1)==minutes


def test_unreviewed_scheme_transcription_cannot_enable_automatic_marking():
    q=dict(subparts=[dict(label='a',sourcePages=[2],schemePages=[4],schemeExtractionCandidate='Any two of four points')],source={'reportHeadingCandidatePdfPages':[5]},issues=[])
    live=dict(data=dict(parts=[dict(label='a',prompt='Explain the result.')]))
    pages={kind:[dict(pageNumber=n,renderAssetId='asset')] for kind,n in [('question',2),('markScheme',4),('examinerReport',5)]}
    data=importer.enrich_question(q,live,pages)
    part=data['parts'][0]
    assert part['assessmentReadiness']=='manual_only'
    assert part['examinerAdvice']==''
    assert 'Any two of four' in part['assessmentReadinessReason']
    assert part['schemeSources']==[dict(page=4,assetId='asset')]


def test_invalid_source_hash_blocks_before_authentication(tmp_path):
    out=tmp_path/'.akuru-intake';out.mkdir();(tmp_path/'x.pdf').write_bytes(b'wrong')
    bank=dict(status='local_draft_unreleased',studentAccess=False,papers=[dict(paperKey='test',files={'question':'x.pdf'},sourceSha256={'question':'0'*64})])
    (out/'4-test.json').write_text(json.dumps(bank))
    with pytest.raises(ValueError,match='hash'):importer.planned_banks(tmp_path)


def test_proposed_points_never_accept_mc_distractor_explanations():
    points=intake.proposed_points('C (protoctists)\nA is not the answer as bacteria lack nuclei\nB is not the answer')
    assert len(points)==1 and points[0]['text']=='C (protoctists)'
    assert points[0]['kind']=='other'


def test_bullet_transcription_preserves_alternatives_without_inventing_rules():
    points=intake.proposed_points('An explanation that makes reference to two points:\n• respiration / releases energy (1)\n• movement / swimming (1)')
    assert len(points)==2
    assert '/ releases energy' in points[0]['text']
    assert all('dependsOn'not in p for p in points)


def test_topic_hints_require_multiple_discriminative_source_terms():
    corpus=[dict(topicRef='cells',code='1',title='Cells',chunks=[{'text':'mitochondria respiration nucleus chromosomes organelles'}]),
        dict(topicRef='environment',code='2',title='Environment',chunks=[{'text':'pollution nitrates eutrophication oxygen algae'}])]
    assert importer.suggest_topics('The diagram shows results',corpus)==[]
    hints=importer.suggest_topics('Explain mitochondria respiration nucleus chromosomes',corpus)
    assert len(hints)==1 and hints[0][0]['topicRef']=='cells'


def test_candidate_description_uses_source_labels_without_claiming_approval():
    from app.services.paper_visual_layout import candidate_alt_text
    pdf=pymupdf.open();page=pdf.new_page();page.insert_text((80,100),'Volume of air in lungs')
    text=candidate_alt_text(page,'diagram',pymupdf.Rect(60,60,300,140),2)
    assert 'Volume of air in lungs' in text
    assert 'Check the full source page' in text
    assert 'PDF page 2' in text


def test_drawing_response_detection_does_not_confuse_drawing_a_conclusion():
    assert importer.drawing_required('Draw a labelled diagram of the cell.')
    assert importer.drawing_required('Plot the results on the grid.')
    assert not importer.drawing_required('Draw a conclusion from these results.')


def test_readback_reconciliation_ignores_only_server_added_source_links():
    expected={'prompt':'Question','parts':[{'prompt':'Explain','schemeSources':[{'page':4,'assetId':None}]}]}
    actual={'prompt':'Question','parts':[{'prompt':'Explain','schemeSources':[{'page':4,'blockId':'server-link'}]}]}
    assert importer.same_content(actual,expected)
    actual['parts'][0]['prompt']='Admin correction'
    assert not importer.same_content(actual,expected)
    actual['parts'][0]['prompt']='Explain'
    actual['parts'][0]['schemeSources'][0]['page']=5
    assert not importer.same_content(actual,expected)


def test_complete_build_handles_repeated_continuation_question_number(tmp_path):
    folder=tmp_path/'Question-paper';folder.mkdir()
    doc=pymupdf.open();p=doc.new_page();p.insert_text((60,80),'Biology 4BI1 Paper 1B')
    p=doc.new_page();p.insert_text((43,90),'1 Read this shared passage.')
    p=doc.new_page();p.insert_text((43,90),'1 (a) Explain the source evidence.');p.insert_text((490,120),'(110)');p.insert_text((300,300),'(Total for Question 1 = 110 marks)')
    doc.save(folder/'Questionpaper-Paper1B-June2025.pdf');doc.close()
    pdf_file(tmp_path/'Mark-scheme/Markscheme-Paper1B-June2025.pdf','Biology 4BI1 Paper 1B')
    bank=intake.build_bank(tmp_path,intake.catalogue(tmp_path))
    assert bank['papers'][0]['totalMarks']==110
    question=bank['questions'][0]
    assert question['sharedStemExtractionCandidate']=='Read this shared passage.'
    assert question['subparts'][0]['label']=='a'
    assert question['subparts'][0]['marks']==110
    assert '1 (a)'not in question['subparts'][0]['extractionCandidate']


def test_inconsistent_subpart_totals_block_intake():
    bank=dict(status='local_draft_unreleased',studentAccess=False,papers=[dict(paperKey='p',questionCount=1,totalMarks=2)],questions=[dict(paperKey='p',number='1',marks=2,subparts=[dict(label='a',marks=1)])])
    with pytest.raises(ValueError,match='subpart inventory'):intake.validate_bank(bank)
