from enum import StrEnum


class DocumentType(StrEnum):
    TEXTBOOK = "textbook"
    REFERENCE = "reference"
    PAST_PAPER = "past_paper"
    MARK_SCHEME = "mark_scheme"
    EXAMINER_REPORT = "examiner_report"
