import json
from types import SimpleNamespace

import pytest

from app.ai.base import SourcePage
from app.errors import DomainError
from app.services.accuracy_jobs import budgeted_request, build_request


def test_budget_counts_serialized_text_and_preserves_required_sources():
    row = SimpleNamespace(number='2', review_data={'parts': [{'prompt': 'Name parts W, X and Y.'}]})
    prior = SimpleNamespace(analysis_data={'parts': [{'percent': 65}]})
    pages = [SourcePage(page_number=6, text='Original question and marking scheme')]
    allowed = {'paper': [6], 'scheme': [6], 'report': []}
    fits = {'chunkId': 'relevant', 'text': 'lens, cornea and retina'}
    huge = {'chunkId': 'too-long', 'text': 'é' * 300}
    baseline = build_request(row, prior, pages, allowed, [fits])
    limit = len(baseline.task) + len(pages[0].text)

    result, supplied = budgeted_request(row, prior, pages, allowed, [huge, fits], limit)

    assert result.pages == tuple(pages)
    assert supplied == [fits]
    assert json.loads(result.task) == json.loads(baseline.task)

    minimum = build_request(row, prior, pages, allowed, [])
    with pytest.raises(DomainError) as error:
        budgeted_request(row, prior, pages, allowed, [fits], len(minimum.task) + len(pages[0].text) - 1)
    assert error.value.code == 'accuracy_required_input_limit'
