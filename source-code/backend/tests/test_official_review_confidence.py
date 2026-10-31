"""Import confidence is bounded triage evidence, never an approval shortcut."""
from app.services.official_review_confidence import estimate, VERSION


def test_import_confidence_prioritises_missing_text_and_low_quality_pages():
    good = estimate('Explain how the substance changes state.', [.98, .96], 'M1: correct explanation')
    low = estimate('Explain how the substance changes state.', [.55, .96], 'M1: correct explanation')
    missing = estimate('', [.98], 'M1: correct explanation')
    assert good['methodVersion'] == VERSION
    assert good['percent'] <= 70
    assert missing['percent'] < low['percent'] < good['percent']
    assert any('missing' in reason.lower() for reason in missing['reasons'])


def test_import_confidence_flags_page_furniture_and_answer_lines():
    clean = estimate('Choose the correct measurement from the graph.', [.99], 'A1')
    furniture = estimate('Choose the correct measurement. DO NOT WRITE IN THIS AREA', [.99], 'A1')
    dotted = estimate('Choose the correct measurement ............', [.99], 'A1')
    assert furniture['percent'] < clean['percent']
    assert dotted['percent'] < clean['percent']
