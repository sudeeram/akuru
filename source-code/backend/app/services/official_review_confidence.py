"""Conservative import-time triage estimates, not calibrated correctness probabilities."""
import re

VERSION = "paper-extraction-triage-v1"
BOILERPLATE = re.compile(r"DO NOT WRITE IN THIS AREA|\bP\d{7,}[A-Z]?\b", re.I)
ANSWER_LINES = re.compile(r"\.{8,}")


def estimate(text: str, page_confidences: list[float], scheme_text: str = "", *, report_confidences: list[float] | None = None) -> dict:
    reasons = ["Page-level sources still need exact question and marking-point review."]
    if page_confidences:
        weakest = min(page_confidences)
        score = min(70, round(35 + 35 * weakest))
        if weakest < .85:
            reasons.append("At least one paper or scheme page has low extraction confidence.")
    else:
        score = 15
        reasons.append("Source-page extraction confidence is unavailable.")
    if not scheme_text.strip():
        score = min(score, 45)
        reasons.append("The marking-scheme text has not been extracted for this question.")
    if not text.strip():
        score = min(score, 15)
        reasons.append("Question wording is missing from the draft extraction.")
    elif len(text.strip()) < 15:
        score = min(score, 35)
        reasons.append("Question wording is unusually short; check for lost text or a shared stem.")
    if BOILERPLATE.search(text):
        score = min(score, 40)
        reasons.append("Printed page furniture appears in the extracted wording.")
    if ANSWER_LINES.search(text):
        score = min(score, 55)
        reasons.append("Answer-space dots may have been assigned to the wrong subpart.")
    if report_confidences:
        report_low = min(report_confidences)
        if report_low < .85:
            score = min(score, round(35 + 35 * report_low))
            reasons.append("A candidate examiner-report page has low extraction confidence.")
        reasons.append("Examiner-report page association is only a candidate until reviewed.")
    return {"percent": max(0, min(100, score)), "methodVersion": VERSION, "reasons": reasons}
