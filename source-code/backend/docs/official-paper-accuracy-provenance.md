# Question accuracy confidence and extraction provenance

`official_question_analyses` stores append-only metadata alongside `official_paper_review_questions`. Migration `0017_official_question_analyses` is additive. Recording an analysis preserves question wording, source evidence, human decisions, reviewer/time, approved assets, published versions and student attempts. A current accuracy record can separately trigger the audited AI approval policy, changing AI statuses and the question revision without rewriting the assessed content.

## Scope and history

Each record has an analysis version, stage (`extraction` or `accuracy`), assessed question revision, content hash, actor/time, method version, source manifest, question estimate and estimates for every current subpart. Each estimate contains separate question-paper, marking-scheme and examiner-report checks, inspected PDF pages, reasons, and source confidence where actually checked. `no_comment` is an assessed report outcome; `not_available` is reserved for a missing source. `not_checked` makes the limitation explicit and caps the overall estimate at 70%.

The server keeps the question percentage no higher than its weakest subpart. Percentages are subjective estimates, not calibrated error rates. Current accuracy above 75% can trigger the separately audited [AI approval policy](question-ai-approval.md), subject to the existing content-review requirements. Manual-marking readiness and explicit release remain separate.

The content hash binds reviewed wording, marks, rubric rules, report advice, question/model-answer visuals, source evidence and exact source versions/hashes. It also hashes linked block content and asset hashes/metadata. Approval and curriculum/readiness status changes alone do not invalidate an assessment. Material changes mark old assessments as earlier content; the UI excludes those scores from current-confidence sorting and retains their history.

## Source/model provenance

Each source role has its own interpretation method, provider, exact model ID and friendly name when known, response ID, processing time, guideline ID/version, prompt version and notes. The source manifest separately captures native/OCR page extraction methods. A deterministic PDF extractor must never be described as ChatGPT extraction.

`modelIdentitySource` distinguishes a provider response from an operator record or missing identity. A provider-confirmed record needs both model and response IDs. Importers should use the actual returned model ID rather than just a configurable alias. If Codex does not expose a verifiable exact model ID, leave it null and describe the assistance in `method`/`notes`. Do not invent a historical identity or label a later source comparison as the original extraction.

New draft-bank imports create an extraction history record in the import transaction. They accept optional `provenance` at the request level or as a list in `draftBank.provenance`; omitted roles remain explicitly unknown. The deterministic confidence algorithm retains its own method version. Older questions remain without original extraction provenance until reliable evidence exists. A later accuracy assessment does not backdate that provenance.

Question-level `provenance` in the draft bank overrides matching batch roles; subpart-level `provenance` overrides matching question roles. Accuracy submissions similarly support per-subpart overrides. This preserves mixed-model runs without falsely assigning one model to every part. The UI resolves those overrides for the selected part and includes them in its model search.

## API and operations

- `GET /api/v1/admin/official-paper-reviews/{paperId}` includes the latest accuracy/extraction analyses and the content hash/analysis version needed for a write.
- `GET .../questions/{number}/analyses` lists the immutable history, newest first.
- `POST .../questions/{number}/analyses` records a prepared source comparison. The request must match the question revision, content hash and analysis version and assess every current subpart. Source pages are validated against the workspace's bound document versions.

These endpoints require an Admin session; mutations also require CSRF protection and write an audit event. History has no update/delete route. Metadata is not exposed through Student exam payloads.

Use `source-code/scripts/record-official-question-analyses.py` with a prepared private JSON payload, an ignored credential file and the exact pre-assessment review baseline. The script defaults to dry-run, validates all questions against the baseline before writing, and can save private before/after evidence. Use `--execute` only after source comparison. It verifies that content and human decisions remain unchanged, allowing only the confidence policy’s AI-status transitions and associated revision increment.

The Admin-only `/admin/exam-documents/review/$paperId/accuracy` route shows every question and subpart in a separate table with confidence, per-source checks, dates, review statuses and model information. The compact review navigation no longer contains confidence figures. The page supports lowest-confidence ordering, question/subpart filters, detailed provenance/history and links back to the exact question/subpart and its source pages using the validated `record`/`section` search keys. Presentation helpers suppress stale scores; AI approval is assigned only by the server policy. No automatic re-extraction or content replacement is triggered when a new model appears. A later model can append a fresh comparison; corrections must use the existing Admin content-review workflow.
