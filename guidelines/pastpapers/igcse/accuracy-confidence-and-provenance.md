# Accuracy confidence and extraction provenance

Standard: `akuru-igcse-pastpapers` 1.4.0

Last updated: 2026-11-11

Record question-paper, marking-scheme and examiner-report interpretation independently. Retain the raw native/OCR extraction method separately from AI interpretation. For AI work, record the actual returned model identifier, friendly name when known, provider, response ID when available, time, guideline version and prompt version. Distinguish provider-confirmed identity from operator-supplied identity. Unknown historical model IDs MUST remain unknown; a later model assessment must not be described as the original extraction.

### Model and reasoning-effort recording — 2026-11-11 clarification

Before starting an AI-assisted batch, establish the model used for each source role and any subpart-specific override. For API work, use the actual response model/response ID. For Codex work where runtime identity is unavailable, obtain the operator's model selection and record it as `operator_recorded`, never `provider_response`. An operator-supplied display label is not a verified API model identifier. Do not silently reuse the model from a previous batch.

Also record the selected reasoning effort using the operator/provider's exact label. The current production provenance contract has no separate reasoning-effort field; record it explicitly in provenance `notes` (for example, `Reasoning effort: Light`). Do not put reasoning effort into `modelName` or infer it from answer quality. A future structured field must remain backward compatible with these records.

When the operator later confirms historical identity, append a provenance-corrected analysis with the same confidence, source checks and content hash. Record the confirmation date and distinguish it from the original processing time. Retain prior analysis history, and verify question content, approval states and release gates remain unchanged. Do not relabel native PDF/OCR-only records as AI-assisted just to fill the Model column.

For each question and subpart, a source comparison SHOULD produce an accuracy-confidence estimate, inspected source pages, specific reasons and unresolved concerns. Compare wording/part boundaries, marks/options, notation, diagrams/labels/axes, rubric alternatives/dependencies/caps and report association. OCR confidence alone cannot establish semantic correctness. Do not claim a percentage is a measured accuracy rate without independent calibration. Do not turn an Admin approval into a 100% score.

Use the weakest subpart to constrain the question estimate. Missing report material and a report with no comment are different outcomes; retain that distinction. A source that has not been checked must say so. Existing approval, manual-marking readiness, release status and frozen attempts are independent of confidence metadata.

Each reassessment creates another dated record bound to exact source versions and reviewed content. Preserve earlier records and mark them outdated when material content changes. A new model may identify proposed corrections; confidence/provenance recording MUST NOT silently apply those corrections to reviewed content. Admin content-review and release gates remain required.

## Reusable reassessment procedure

Follow [source comparison and confidence reassessment](source-comparison-and-confidence-reassessment.md) when improving an existing paper. Compare the actual sources and saved crops, correct defects through revision-protected APIs, and only then assess the saved version. A higher score must reflect the comparison performed, not a raised cap or copied scores. Record unverified handwriting and source conflicts explicitly; report question and subpart threshold counts separately.

## Exact-source linking follow-up

A model's region-match percentage is distinct from a question's overall accuracy confidence. Verify the original crop and native text, actual nested part label, MC options, shared passage/table/diagram context, all rubric columns and continuation guidance. Repeat a shared region under real affected part labels; do not invent `shared stem` subparts. Keep blank plotting grids in the visual workflow rather than manufacturing exact native text. Do not link general answer instructions as question wording.

Link question-paper evidence at both the subpart and parent-question levels. Deduplicate identical version/role/bounds/text regions while retaining all affected part associations. A material source-link change requires a fresh source comparison and appended accuracy record, never an old score rebound to a new hash. Retain unresolved publisher conflicts, curriculum uncertainty, manual-scoring and visual-release requirements. Record the model actually returned by API generation, and explicitly distinguish operator-confirmed Codex review identity/effort. Truncated model output fails without applying a partial result or silently retrying a paid request.
