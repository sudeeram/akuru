import pytest
from pydantic import ValidationError

from app.schemas.documents import ScientificTextContent
from app.services.scientific_text import proposal


def test_scientific_notation_proposals_are_review_only_and_conservative():
    water = proposal("Water is H2O and occupies 5 cm3.")
    assert water and water["requiresAdminReview"] is True
    assert any(mark["type"] == "subscript" for mark in water["marks"])
    assert any(mark["type"] == "superscript" for mark in water["marks"])
    ambiguous = proposal("The ion may be written SO42- by OCR.")
    assert ambiguous and "SO42-" in ambiguous["ambiguousTokens"]


def test_scientific_content_rejects_out_of_range_marks():
    valid = ScientificTextContent(text="H₂O", plainText="H2O",
        marks=[{"type": "subscript", "start": 1, "end": 2}])
    assert valid.version == 1
    with pytest.raises(ValidationError):
        ScientificTextContent(text="H2O", plainText="H2O",
            marks=[{"type": "subscript", "start": 1, "end": 8}])
