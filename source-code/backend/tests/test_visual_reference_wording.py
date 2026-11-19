"""Precision instructions must not invent a missing question visual."""
from types import SimpleNamespace
import pytest
from app.services.official_paper_reviews import visual_requirement_issues


@pytest.mark.parametrize('precision', ['two significant figures', '3 SIGNIFICANT FIGURES', 'two decimal figures'])
def test_numeric_precision_does_not_require_diagram(precision):
    data = {'parts': [{'label': 'b(i)', 'prompt': f'Calculate the mean from the table. Give your answer to {precision}.', 'visualAssetIds': ['results']}]}
    assets = {'results': SimpleNamespace(asset_metadata={'kind': 'table', 'reviewCrop': True})}
    assert visual_requirement_issues(data, assets) == []


def test_precision_does_not_hide_a_real_figure_reference():
    data = {'parts': [{'label': 'a', 'prompt': 'Use Figure 2 to calculate the rate to two significant figures.'}]}
    assert visual_requirement_issues(data, {}) == ['Part a: attach a reviewed diagram referenced by the question.']


def test_precision_does_not_hide_a_missing_results_table():
    data = {'parts': [{'label': 'a', 'prompt': 'Use the table. Give the mean to two significant figures.'}]}
    assert visual_requirement_issues(data, {}) == ['Part a: attach a reviewed table referenced by the question.']


@pytest.mark.parametrize('instruction', ['Include a genetic diagram in your answer.', 'Draw a labelled diagram of the apparatus the student could use.', 'Draw a fully labeled genetic diagram.'])
def test_student_requested_answer_diagram_is_not_a_supplied_question_visual(instruction):
    data = {'parts': [{'label': 'b(ii)', 'prompt': instruction, 'visualAssetIds': []}]}
    assert visual_requirement_issues(data, {}) == []


def test_student_drawing_instruction_does_not_hide_a_supplied_diagram_reference():
    data = {'parts': [{'label': 'a', 'prompt': 'Use the diagram of the parents. Include a genetic diagram in your answer.'}]}
    assert visual_requirement_issues(data, {}) == ['Part a: attach a reviewed diagram referenced by the question.']


def test_drawing_instruction_referencing_diagram_shown_above_still_requires_it():
    data = {'parts': [{'label': 'a', 'prompt': 'Draw a diagram shown above with the missing labels.'}]}
    assert visual_requirement_issues(data, {}) == ['Part a: attach a reviewed diagram referenced by the question.']


