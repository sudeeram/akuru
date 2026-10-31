# Accuracy confidence and extraction provenance

Standard: `akuru-igcse-pastpapers` 1.3.0

Last updated: 2026-11-01

Record question-paper, marking-scheme and examiner-report interpretation independently. Retain the raw native/OCR extraction method separately from AI interpretation. For AI work, record the actual returned model identifier, friendly name when known, provider, response ID when available, time, guideline version and prompt version. Distinguish provider-confirmed identity from operator-supplied identity. Unknown historical model IDs MUST remain unknown; a later model assessment must not be described as the original extraction.

For each question and subpart, a source comparison SHOULD produce an accuracy-confidence estimate, inspected source pages, specific reasons and unresolved concerns. Compare wording/part boundaries, marks/options, notation, diagrams/labels/axes, rubric alternatives/dependencies/caps and report association. OCR confidence alone cannot establish semantic correctness. Do not claim a percentage is a measured accuracy rate without independent calibration. Do not turn an Admin approval into a 100% score.

Use the weakest subpart to constrain the question estimate. Missing report material and a report with no comment are different outcomes; retain that distinction. A source that has not been checked must say so. Existing approval, manual-marking readiness, release status and frozen attempts are independent of confidence metadata.

Each reassessment creates another dated record bound to exact source versions and reviewed content. Preserve earlier records and mark them outdated when material content changes. A new model may identify proposed corrections; confidence/provenance recording MUST NOT silently apply those corrections to reviewed content. Admin content-review and release gates remain required.
