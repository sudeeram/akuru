"""Regression checks for official-paper timing and the local intake catalogue."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pymupdf
import pytest

from app.errors import DomainError
from app.services.assessments import official_paper_duration
from app.services.documents import _validate_relationships
from app.schemas.documents import DocumentType

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'catalog-pearson-chemistry.py'
spec = spec_from_file_location('catalog_pearson_chemistry', SCRIPT)
catalogue = module_from_spec(spec)
spec.loader.exec_module(catalogue)
PILOT_SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'pilot-pearson-chemistry.py'
pilot_spec = spec_from_file_location('pilot_pearson_chemistry', PILOT_SCRIPT)
pilot = module_from_spec(pilot_spec)
pilot_spec.loader.exec_module(pilot)
DRAFT_SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'build-pearson-chemistry-draft-bank.py'
draft_spec = spec_from_file_location('build_pearson_chemistry_draft_bank', DRAFT_SCRIPT)
draft_bank = module_from_spec(draft_spec)
draft_spec.loader.exec_module(draft_bank)


@pytest.mark.parametrize(('component', 'minutes'), [('1C', 120), ('1CR', 120), ('2C', 75), ('2CR', 75)])
def test_official_chemistry_paper_uses_component_duration(component, minutes):
    document = SimpleNamespace(component=component, source_metadata={})
    assert official_paper_duration(document, 1) == minutes
    assert official_paper_duration(document, 110) == minutes


def test_official_duration_requires_reviewed_metadata_and_allows_explicit_duration():
    with pytest.raises(DomainError, match='component or duration'):
        official_paper_duration(SimpleNamespace(component=None, source_metadata={}), 110)
    assert official_paper_duration(SimpleNamespace(component=None, source_metadata={'durationMinutes': 90}), 110) == 90


def pdf_bytes(component):
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((70, 70), f'Chemistry 4CH1/{component}', fontsize=14)
    content = document.tobytes()
    document.close()
    return content


def test_catalogue_links_available_companions_without_requiring_examiner_report(tmp_path):
    session = tmp_path / 'International GCSE-Chemistry (2017) (Current)-June 2021.pastpapers'
    for directory, stem in [('Question-paper', 'Questionpaper'), ('Mark-scheme', 'Markscheme')]:
        folder = session / directory
        folder.mkdir(parents=True)
        (folder / f'{stem}-Paper1C-June2021.pdf').write_bytes(pdf_bytes('1C'))
    rows, by_paper = catalogue.make_catalogue(tmp_path)
    assert len(rows) == 2
    key = '4CH1-2017-2021-JUNE-1C'
    assert by_paper[key] == {'past_paper', 'mark_scheme'}
    assert next(row for row in rows if row['kind'] == 'mark_scheme')['source_paper_key'] == key
    assert all(row['internal_code_check'] == 'matched' for row in rows)


def test_january_2020_ambiguous_filename_is_resolved_to_paper_2cr(tmp_path):
    path = tmp_path / 'International GCSE-Chemistry (2017) (Current)-January 2020.pastpapers' / 'Question-paper' / 'Questionpaper-PaperCR-January2020.pdf'
    assert catalogue.identity(path)[3] == '2CR'
    with pytest.raises(ValueError, match='Ambiguous component'):
        catalogue.identity(Path(str(path).replace('January 2020', 'June 2022').replace('January2020', 'June2022')))


def test_companion_identity_must_match_its_exact_paper():
    paper_id = __import__('uuid').uuid4()
    paper = SimpleNamespace(course_id='igcse', subject_id='chemistry',
                            exam_session='June 2025', component='1CR',
                            variant='regional', publication_year=2025)
    repository = SimpleNamespace(course_and_subject_exist=lambda *_: True,
                                 source_paper=lambda value: paper if value == paper_id else None)
    _validate_relationships(repository, DocumentType.MARK_SCHEME, 'igcse', 'chemistry',
                            paper_id, 'June 2025', '1CR', 'regional', 2025)
    with pytest.raises(DomainError, match='component'):
        _validate_relationships(repository, DocumentType.MARK_SCHEME, 'igcse', 'chemistry',
                                paper_id, 'June 2025', '1C', 'regional', 2025)


def test_pilot_rejects_a_scheme_with_different_question_marks(tmp_path):
    def write_pdf(path, lines):
        path.parent.mkdir(parents=True, exist_ok=True)
        document = pymupdf.open()
        page = document.new_page()
        for index, line in enumerate(lines):
            page.insert_text((60, 80 + 24 * index), line)
        document.save(path)
        document.close()

    base = tmp_path
    write_pdf(base / 'Question-paper/Questionpaper-Paper1C-June2025.pdf',
              ['Total for Question 1 = 8 marks', 'TOTAL FOR PAPER = 8'])
    write_pdf(base / 'Mark-scheme/Markscheme-Paper1C-June2025.pdf', ['Total 7'])
    write_pdf(base / 'Examiner-report/Examinerreport-Paper1C-June2025.pdf', ['Paper 1C'])
    with pytest.raises(ValueError, match='disagree'):
        pilot.inspect_set(base, '1C')


def test_pilot_retains_all_subpart_marks_and_exact_source_pages(tmp_path):
    def write_pdf(path, pages):
        path.parent.mkdir(parents=True, exist_ok=True)
        document = pymupdf.open()
        for lines in pages:
            page = document.new_page()
            for index, line in enumerate(lines):
                page.insert_text((60, 80 + 24 * index), line)
        document.save(path)
        document.close()

    write_pdf(tmp_path / 'Question-paper/Questionpaper-Paper1C-June2025.pdf',
              [['Cover'], ['Periodic table'],
               ['1 Question about atoms', '(a) First part', '(3)', '(b) Second part', '(5)',
                '(Total for Question 1 = 8 marks)', 'TOTAL FOR PAPER = 8']])
    write_pdf(tmp_path / 'Mark-scheme/Markscheme-Paper1C-June2025.pdf',
              [['Cover'], ['Guidance'], ['Overview'], ['Question 1', 'Marking points', 'Total 8']])
    write_pdf(tmp_path / 'Examiner-report/Examinerreport-Paper1C-June2025.pdf',
              [['Question 1(a)', 'Examiner comments']])
    result = pilot.inspect_set(tmp_path, '1C')
    assert result['questionCount'] == 1 and result['totalMarks'] == 8
    assert result['questions'][0]['subpartMarkAllocations'] == [3, 5]
    assert result['reviewDrafts'][0]['questionPdfPages'] == [3]
    assert result['reviewDrafts'][0]['schemePdfPages'] == [4]
    assert result['reviewDrafts'][0]['reportCandidatePdfPages'] == [1]
    assert set(result['sourceSha256']) == {'question', 'markScheme', 'examinerReport'}
    assert all(len(digest) == 64 for digest in result['sourceSha256'].values())


def test_pilot_keeps_every_page_of_a_continued_scheme(tmp_path):
    def write_pdf(path, pages):
        path.parent.mkdir(parents=True, exist_ok=True)
        document = pymupdf.open()
        for lines in pages:
            page = document.new_page()
            for index, line in enumerate(lines):
                page.insert_text((60, 80 + 24 * index), line)
        document.save(path)
        document.close()

    write_pdf(tmp_path / 'Question-paper/Questionpaper-Paper1C-June2025.pdf',
              [['Cover'], ['Periodic table'],
               ['1 Question about atoms', '(a) First part', '(3)', '(b) Second part', '(5)',
                '(Total for Question 1 = 8 marks)', 'TOTAL FOR PAPER = 8']])
    write_pdf(tmp_path / 'Mark-scheme/Markscheme-Paper1C-June2025.pdf',
              [['Cover'], ['Guidance'], ['Overview'], ['Question number', '1 (a)', 'First marking point'],
               ['(b) Continued marking points', 'Total 8']])
    write_pdf(tmp_path / 'Examiner-report/Examinerreport-Paper1C-June2025.pdf',
              [['Question 1 examiner comments']])
    result = pilot.inspect_set(tmp_path, '1C')
    assert result['reviewDrafts'][0]['schemePdfPages'] == [4, 5]


def test_pilot_rejects_a_companion_with_an_internal_regional_mismatch(tmp_path):
    path = tmp_path / 'scheme.pdf'
    document = pymupdf.open()
    document.new_page().insert_text((60, 80), 'Chemistry 4CH1/1CR Mark Scheme')
    document.save(path)
    document.close()
    with pytest.raises(ValueError, match='disagrees'):
        pilot.check_component(path, '1C')


def test_pilot_defaults_to_standard_papers_only(tmp_path, monkeypatch):
    import json
    import sys

    inspected = []

    def fake_inspect(_root, component):
        inspected.append(component)
        return {'component': component, 'questionCount': 1, 'totalMarks': 1}

    monkeypatch.setattr(pilot, 'inspect_set', fake_inspect)
    monkeypatch.setattr(sys, 'argv', ['pilot-pearson-chemistry.py', str(tmp_path)])
    pilot.main()
    manifest = json.loads((tmp_path / 'june-2025-pilot-manifest.json').read_text())
    assert inspected == ['1C', '2C']
    assert manifest['pilotComponents'] == ['1C', '2C']
    assert manifest['releaseStatus'] == 'preflight_only'


def test_examiner_report_candidates_exclude_incidental_introduction_mentions():
    pages = [
        'Introduction\nQuestion 1 was an easy starter.\nQuestion 2 was harder.',
        'Question 1(b)(i)\nCandidates often missed this point.',
        'Question 2(a)\nRelevant commentary.',
    ]
    assert pilot.report_heading_pages(pages, 1) == [2]
    assert pilot.report_heading_pages(pages, 2) == [3]


def test_draft_subparts_keep_nested_labels_and_fail_on_missing_marks():
    raw = ('6 (a) First question\n(2)\n'
           '(b) (i) Second question\n(1)\n'
           '(ii) Third question\n(3)')
    stem, parts = draft_bank.separate_subparts(raw, [2, 1, 3])
    assert stem == ''
    assert [(part['label'], part['marks']) for part in parts] == [
        ('a', 2), ('b(i)', 1), ('b(ii)', 3)]
    with pytest.raises(ValueError, match='disagree'):
        draft_bank.separate_subparts(raw, [2, 1, 2])
