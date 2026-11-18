# Prepared past-paper review APIs

Implementation started: 18 November 2026. Scope: authenticated, model-free review authoring. This workflow does not call a provider, reserve model quota, generate answers or queue an inference job. Imported confidence is an attributed source comparison, not server-generated evidence of accuracy.

## Workflow

1. Export `GET /api/v1/admin/official-paper-reviews/{paper}/review-package`. Use `number`, `offset` and `limit` (maximum 20 questions). Private original-document links, source versions, question revision, analysis version, scope hashes and source issues accompany the question data.
2. Inspect the original sources. Prepare a `StageReview` JSON using the exported revision/content/analysis hashes, explicit per-part corrections and attributed `sourceFinding` records. Never replace an expected hash merely to force an old correction through.
3. POST `/{paper}/change-sets`. This creates an immutable prepared audit record; it does not change the live question. An identical request ID/payload returns the existing record. A reused ID with a different payload conflicts.
4. GET `/{paper}/change-sets/{id}/preview`. Inspect before/after content, selected parts, unchanged siblings, source versions and any visual operations. Previewing visual metadata runs inside a rolled-back savepoint. Preview hashes also bind current topic publications and mappings, so a publication change requires another preview. A wording/shared-stem correction rebuilds the aggregate prompt; absent shared context must be explicitly confirmed rather than silently discarded.
5. POST `/{paper}/change-sets/{id}/apply` with a new request ID and the exact preview hash. Correction, attributed analysis, issue decisions and optional approval/release share a database transaction. Failures roll back the entire item. The receipt distinguishes newly compared findings from findings carried forward with their original analysis ID.
6. Inspect `/{paper}/readiness`. Source confidence, content approval, curriculum and executable scoring are separate gates. Open explanations stay manual unless their supported scoring implementation is independently validated. Confidence strictly above 75% is necessary but not sufficient for AI approval.

All routes require an authenticated Admin. Mutations require the existing CSRF header and same-origin checks. Credentials, source exports and prepared packages belong in ignored private files, never Git. No SQL access or privileged universal token is required.

## Scopes and preservation

A stable part reference is derived from the stored question ID and part label. Renaming a label is deliberately unsupported here: it is a new identity needing review, never a transfer of another part's approval. Scope hashes bind the actual part, shared context, relevant source blocks/assets and source versions. Aggregate question extraction text is not a hidden dependency of otherwise unchanged subparts.

Unchanged source findings can be carried forward only when their dependency bindings match. Legacy analyses without part bindings can be bootstrapped only while their original whole-question snapshot is current. Unknown historical scope remains stale. Shared-context/visual changes require findings for every affected part. Human-approved content requires explicit scoped reopening; human-approved siblings remain intact.

Scoring certificate IDs cannot be supplied or replaced by a correction package. Existing certificates are checked against the revised rubric/dependencies and cleared when incompatible. Tutor releases created under fingerprint version 2 use part dependencies rather than the aggregate question revision. Legacy fingerprints retain their conservative historical behaviour. Explicitly withdrawn releases are not automatically resurrected.

## Source decisions and assets

`issueDecisions` retain the original issue and typed disposition. An extraction omission requires both a relevant content correction and a new source finding. A note alone is insufficient in this workflow. Unchanged part decisions carry their original ancestry; whole-question decisions are conservatively reconsidered after corrections. Excluding report guidance keeps that guidance unavailable to students even after carry-forward. The marking scheme governs report conflicts, while internal contradictions in the scheme require explicit adjudication.

Existing exact-evidence proposal APIs now accept report sources. The `materialize` decision creates private source-bound exact blocks and returns `materializedRef` without changing question content, revision or approvals. Those references can be attached in a prepared correction. Repeating materialisation returns the existing references. Rejecting/applying legacy proposals remains available separately.

Existing reviewed crop assets can be approved/rejected with `visualDecisions`; no new files are written during the atomic correction. Asset ownership, source role/version, SHA and crop identity are checked. New crop files must first be prepared through the existing bounded crop API; this API cannot accept arbitrary filesystem paths or URLs. Curriculum corrections use the existing published same-subject topic/evidence validation.

## Routes and durable execution

In addition to export, readiness and change-set stage/get/preview/apply:

- `POST /{paper}/questions/{number}/auto-approval`: scoped policy evaluation, optionally dry-run, with idempotent receipts.
- `POST /{paper}/release-validation`: diagnostics for Tutor practice, official drafts or formal exams. This never publishes an exam. Formal validation invokes the same official-material publication checks with publication disabled inside a rolled-back savepoint. It checks the current drafts, source identity and inventory without publishing them. Actual publication still uses the separate explicit workflow.
- `POST /{paper}/review-batches`, `GET /{paper}/review-batches/{id}`, `POST /{paper}/review-batches/{id}/resume`: maximum 50 distinct prepared items, each with its own exact preview hash and transaction. Earlier successful items remain committed if a later item conflicts. Resume skips current completed receipts, reports stale ones and never fabricates new findings.
- `GET /{paper}/review-history?offset=0&limit=50`: bounded audit history, including batch attempts and approval operations.

Prepared records, batches and receipts use existing indexed `AuditEvent` rows; analyses remain immutable `OfficialQuestionAnalysis` rows. No schema migration or database reset is required. Request UUIDs use the existing primary-key uniqueness constraint; paper/actor/payload checks prevent cross-operation reuse. Temporary local files are not the sole state.

## CLI and Admin UI

`source-code/scripts/developer-review.py --help` lists export, readiness, stage, preview, apply, batch/resume, source-context, evidence operations and release-validation commands. Run with the backend virtualenv Python. Supply `--credentials tmp/akuru-admin.env`, `--paper UUID`, and an ignored `--output` path. Writes additionally require explicit `--input`; operation commands require `--operation UUID`. JSON output files are mode 0600. The CLI uses the same authenticated HTTPS APIs as the UI and logs out after use.

The question review page includes **Prepared developer review** tools. It disables applying external packages while the page has unsaved edits, shows the source-bound diff and requires explicit confirmation before applying. Saving refreshes the review while preserving the selected question/subpart. Accuracy views show per-part freshness and carried-forward origin.

## Acceptance evidence

See [Biology production acceptance](developer-review-biology-acceptance.md) for the three source corrections, all 31 part states, preserved certificates and remaining independent release blockers. The implementation roadmap tracks final deployment acceptance. Route availability and source approval do not imply a whole exam is published.
