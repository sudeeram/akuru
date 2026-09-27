from __future__ import annotations

import re


SUBSCRIPT_PATTERN = re.compile(r"(?<=[A-Za-z\)])\d+")
UNIT_POWER_PATTERN = re.compile(r"(?i)\b(?:cm|mm|dm|m|km)([23])\b")
AMBIGUOUS_CHARGE_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9()]*\d[+-](?=\W|$)")


def proposal(text: str) -> dict | None:
    """Create review-only notation suggestions without changing OCR text."""
    if not text:
        return None
    marks: list[dict] = []
    for match in SUBSCRIPT_PATTERN.finditer(text):
        marks.append({"type": "subscript", "start": match.start(), "end": match.end(),
                      "method": "scientific_context", "confidence": 0.72})
    for match in UNIT_POWER_PATTERN.finditer(text):
        start, end = match.span(1)
        marks = [mark for mark in marks if not (mark["start"] < end and mark["end"] > start)]
        marks.append({"type": "superscript", "start": start, "end": end,
                      "method": "unit_power", "confidence": 0.9})
    ambiguous = [match.group(0) for match in AMBIGUOUS_CHARGE_PATTERN.finditer(text)]
    if not marks and not ambiguous:
        return None
    return {"version": 1, "marks": marks, "ambiguousTokens": ambiguous,
            "requiresAdminReview": True}
