# Step 19 — Evaluation and release gates

AKURU keeps evaluation evidence in three immutable/auditable layers: an Admin-reviewed corpus, a candidate run, and an active subject/workflow release. A corpus is versioned per Phase 1 subject and cannot be approved unless it contains inventory, OCR, equation, diagram, mapping, marking, feedback and repeatability cases. Approving a new version retires the prior approved corpus.

Each run names the exact model and prompt version and records a SHA-256 hash of its observations. The evaluator measures question recall, OCR similarity, exact equation and diagram preservation, unit-mapping precision, cross-subject rejection, exact total and method marks, small-error recall, improved-answer presence, source grounding and repeatability. Run metrics, thresholds, failures, actor and time remain in PostgreSQL.

## Thresholds

| Metric | Minimum |
| --- | ---: |
| Question inventory recall | 98% |
| OCR similarity | 97% |
| Equation preservation | 100% |
| Diagram preservation | 100% |
| Mapping precision | 95% |
| Cross-subject rejection | 100% |
| Exact awarded marks | 90% |
| Method-mark agreement | 95% |
| Small-error recall | 90% |
| Improved-answer presence | 95% |
| Source grounding | 100% |
| Repeatability | 95% |

These conservative defaults protect exam-critical material. Change them only through a reviewed migration and an updated rationale; they are deliberately server-owned rather than supplied by the browser.

## Enforcement

An Admin can activate `assessment_feedback` automatic mode only with a passing run for the same subject. Runtime publication additionally requires the response confidence to meet the release threshold and the actual model and prompt version to exactly match the passing run. Missing, failed, stale or mismatched releases add a review reason and store the assessment result as `needs_review`; the feedback remains available for Parent/Admin review. Generated conceptual media and official learning material retain their existing explicit Admin publication gates.

The Admin **Evaluation gates** screen creates and approves corpora, submits observations, displays every metric/failure, reports Phase 1 subjects missing an approved corpus, and activates passing releases. API endpoints are under `/api/v1/evaluations/admin` and require an authenticated Admin; mutations also require CSRF protection. Audit events cover corpus creation/approval, completed runs and release changes.

Before changing a production model or prompt, execute the candidate over the approved corpus for every enabled subject and submit the observations as a new run. Activate only passing subject releases. Because runtime checks the model and prompt identity, changing either without a matching passing release automatically restores review-required behavior.

No real Edexcel answer is fabricated by the repository. Parents/Admins must build the corpus from licensed material and independently reviewed expected results. Tests use synthetic cases to verify calculation, authorization and fail-closed release behavior; they do not establish educational accuracy for production.
