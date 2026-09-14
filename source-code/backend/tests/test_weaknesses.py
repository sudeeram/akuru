from app.services.weaknesses import classify

def test_subject_taxonomy_covers_key_edexcel_mistakes():
    assert classify("maths", "Selected the wrong formula") == ("formula_selection", "method")
    assert classify("physics", "The answer omitted the unit") == ("units", "accuracy")
    assert classify("biology", "Misread the graph") == ("graph_interpretation", "application")
    assert classify("ict", "Terminology is imprecise") == ("terminology", "knowledge")
    assert classify("english", "Did not respond to explain") == ("command_word_response", "reasoning")

def test_mark_scheme_kind_is_used_when_text_has_no_taxonomy_keyword():
    assert classify("maths", "The intermediate step is absent", "method") == ("method", "method")
