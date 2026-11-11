# Exact question and marking-scheme evidence

The Admin review and accuracy pages provide two separate actions: free deterministic block matching and queued model-assisted original-source region selection. Both create private proposals, not question approvals. A question is the unit of work; large papers can be processed incrementally. The worker uses the existing AI account router and records the actual returned model and response ID. Model sources are treated as untrusted data.

`EvidenceLinkJob` is an additive durable table, serviced by the existing document worker. It stores the initiating Admin, revision/content-hash snapshot, processing state, safe error code and result reference. An explicit whole-paper batch queues distinct questions durably; separate new jobs are blocked while that paper already has pending work. Interrupted jobs fail after 15 minutes and are never automatically retried or charged again. The Admin may explicitly start another job. Requests are capped at 12 original source pages, also subject to the configured provider's page/input/output limits. Model analysis never holds a question lock during the paid call; the snapshot is revalidated afterwards.

Proposals and apply/reject decisions use append-only audit events. New original-PDF regions create derived `subpart` blocks with their actual source text, bounds, source checksum and provenance. Original extraction remains intact. Existing blocks are reused; source role, page, version and fingerprint are checked. Blank native regions fail closed rather than accepting invented transcription; scanned-only material requires reviewed OCR first. Alternative/continuation regions can all be linked to one subpart.

## Authenticated Admin APIs

Under `/api/v1/admin/official-paper-reviews/{paperId}`:

- `GET /evidence-links`: recent saved proposals and their decisions.
- `POST /evidence-links`: bounded one-question text matching, or import explicit source-region/block selections with manual or model provenance.
- `GET /evidence-links/{runId}/{proposalId}/preview`: private original-source crop.
- `POST /evidence-links/{runId}/review`: apply or reject selected proposals; optimistic revision/hash and source-review confirmation are required for manual application. Automatic application accepts only unique exact reviewed text matches, never model confidence alone.
- `GET /evidence-link-jobs`, `POST /evidence-link-jobs`: durable one-question AI job status/creation.
- `POST /evidence-link-job-batch`: atomically validate and queue an explicit whole-paper snapshot; duplicate requests return the existing job receipts.

All reads require Admin authentication. Mutations additionally require CSRF. Request IDs are idempotency keys; changed payloads cannot reuse an ID. Applying an already-applied selection returns its receipt without duplicating blocks or links. Apply all desired regions for a question together; later changes require a fresh proposal snapshot. Rejected proposals are retained. The existing source-evidence controls can unlink an erroneous association; replacement is audited by a new proposal and review, never by deleting history.

Changes to exact evidence invalidate prior accuracy hashes and revoke AI approval. A new source comparison must be recorded through the existing analysis API; there is no copy-forward or rebind shortcut. Human-approved questions/subparts require reopening before evidence edits. Curriculum decisions, rubric/scoring rules, published versions, Student attempts and release gates are not changed. Confidence strictly above 75% still requires all existing content/visual requirements; scoring and Student release remain separate.

The UI retains the current question/subpart on refresh after applying, provides original-region previews, explicit confirmation and toast feedback, and shows ambiguous/missing matches as review work. Text matching and model matching confidence are distinct from overall source accuracy. Analysis errors use safe, part-specific messages rather than raw exception tuples.

Tests: `tests/test_exact_evidence_links.py`, plus existing source-review, analysis-history and AI-approval suites. Live evaluation uses the separately authorised Evaluation project and a private cumulative spend ledger; no keys or source files belong in Git.

Evidence jobs have a dedicated bounded output allowance: `AKURU_EVIDENCE_AI_MAX_OUTPUT_TOKENS` defaults to 8000 (range 1000–16000). Multi-part questions can exceed the general provider's 4000-token allowance. This setting only affects evidence jobs; it does not change tutor or assessment output limits. A truncated/invalid response fails without applying links or automatically retrying.
