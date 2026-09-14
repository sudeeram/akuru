import pytest

from app.services.subject_marking import analyze, policy, symbolic_equivalent


def test_maths_symbolic_equivalence_and_method_signals_remain_advisory():
    assert symbolic_equivalent("2*(x+1)", "2*x+2") is True
    assert symbolic_equivalent("2*x+3", "2*x+2") is False
    result = analyze("maths", "Calculate x and give cm", "x = 2 + 3\n= 6 cm", {
        "markingPoints": [{"code": "M1", "text": "M1 substitutes into x=2+3"},
                          {"code": "A1", "text": "A1 x=5"}], "alternatives": ["x=5"]})
    assert result["awardedMarks"] is None
    assert result["signals"]["showsFormula"] is True
    assert result["signals"]["showsSubstitution"] is True
    assert any(item["equivalent"] is False for item in result["signals"]["symbolicEquivalence"])


@pytest.mark.parametrize("subject,expected_engine,expected_dimension,answer", [
    ("biology", "science", "variables", "The independent variable changes, therefore repeat and average the measurements."),
    ("chemistry", "science", "calculation", "Measure the mass because the result supports the conclusion."),
    ("physics", "science", "causal_reasoning", "Use V = 2 * 3 because voltage causes the current to rise."),
    ("human-biology", "science", "conclusion", "The data supports the conclusion because the rate increased."),
    ("ict", "ict", "trade_offs", "This helps the business because it is faster; however, it costs more."),
    ("english", "english", "organisation", 'The quotation “light” is evidence.\n\nHowever, the second paragraph develops it.'),
    ("french", "french", "grammar", "Je suis allé à Paris et je vais étudier demain."),
])
def test_reviewed_subject_examples_expose_required_engine_dimensions(subject, expected_engine, expected_dimension, answer):
    rubric = {"markingPoints": [{"text": "Task purpose evidence organisation structure language vocabulary grammar communication comprehension detail accuracy tense message meaning"}]}
    result = analyze(subject, "Approved question", answer, rubric)
    assert policy(subject).name == expected_engine
    assert expected_dimension in result["dimensions"]
    assert result["engine"] == expected_engine and result["version"] == "1.0.0"
    if expected_engine == "science": assert "terminologyMatches" in result["signals"]
    if expected_engine == "ict": assert "vocabularyMatches" in result["signals"]
    if expected_engine == "english": assert {"taskTermMatches", "evidenceMarkers", "paragraphs", "languageVariety"} <= result["signals"].keys()
    if expected_engine == "french": assert {"comprehensionTermMatches", "vocabularyVariety", "verbIndicators", "communicationEvidence"} <= result["signals"].keys()


def test_english_and_french_require_complete_approved_rubric_dimensions():
    incomplete = {"markingPoints": [{"text": "Uses suitable vocabulary"}]}
    assert not all(analyze("english", "Write", "An answer", incomplete)["rubricCoverage"].values())
    assert not all(analyze("french", "Écrivez", "Je suis ici", incomplete)["rubricCoverage"].values())
