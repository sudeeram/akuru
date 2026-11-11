# Final-content accuracy reassessment

The final accuracy workflow is distinct from exact-source linking. `accuracy_jobs.py` uses the existing durable `EvidenceLinkJob` store with `job_kind=accuracy` (migration 0022). Source-link workers/listings explicitly filter `job_kind=evidence`; the document worker services both types. Existing rows default to evidence. Batch queue creation validates all snapshots and image gates before any writes, serializes against pending paper work and uses request IDs for duplicate-free receipt recovery.

Admin APIs under `/api/v1/admin/official-paper-reviews/{paperId}`:

- `GET /accuracy-readiness`: per-question image blockers, stale-assessment status, current content at 75% or lower and eligibility.
- `GET /accuracy-jobs`: private recent durable job history.
- `POST /accuracy-jobs`: explicit question snapshot batch. Each item supplies requestId, number, expectedRevision, expectedContentHash and expectedAnalysisVersion. Mutations require CSRF; all endpoints require Admin.

The worker checks active Admin permissions, snapshots, original PDF checksums, selected crop bytes and review state. It supplies original paper, scheme and report pages plus reviewed crops to the existing account router, treating all source/content/old notes as untrusted data. Report pages can include the earlier source comparison's verified scope when no per-part report link exists. A report not checked cannot receive a checked score. No source text or image is generated or overwritten.

Model output must assess every actual part once, use only supplied original pages, provide independent wording/marking/visual confidence, reasons and paper/scheme/report checks. Current percentages are constrained by dimensions, weakest source/part and explicit manual-review flags. Earlier checked source findings at or below 75% remain capped for Admin adjudication; the model cannot silently settle a publisher contradiction. These are estimated fidelity judgements, not calibrated correctness probabilities. Human decisions are not overwritten.

One question is the reassessment unit, preserving shared context and avoiding reruns of unaffected current questions. The request is limited to 24 original pages/selected crops and the configured input/image limits; evidence-specific output cap defaults to 8000 tokens. Excess/invalid/missing input fails closed. Source/model failures do not retry automatically. Processing jobs interrupted for 15 minutes fail without dispatching again. A deliberate new job is required for a retry; inspect history first.

No long transaction/question lock spans the paid call. Revision/hash and analysis-history checks run again before saving. Fresh analysis, normal guarded AI status changes and completed job receipt commit atomically. No Student-release switches, frozen attempts, marking rules, curriculum mappings, human image approvals or source associations are changed. Asset edits invalidate the hash as before.

Frontend `AccuracyReassessment` is available in the accuracy overview and selected-question review, with unsaved-edit protection, explicit paid-call confirmation, resumable progress and distinct image/content queues. A completed final assessment uses the existing strict >75% approval policy, still subject to all evidence/visual/coverage gates; scoring readiness and Student release remain separate.

Tests: `test_accuracy_reassessment_jobs.py`, plus exact evidence, analysis history, official review and auto-approval regressions. Implementation tests use synthetic original PDFs/crops and `FakeAIProvider`; they make no paid model calls.
