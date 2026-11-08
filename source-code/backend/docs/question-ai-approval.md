# Confidence-based question approval

Implemented: 8 November 2026.

A current **accuracy** analysis with confidence **strictly above 75%** can assign
`ai_approved` to a question or subpart. Exactly 75% does not qualify. Initial
extraction confidence is insufficient. Overall question confidence is bounded by
the weakest subpart; every subpart must qualify or already have human approval.

The server runs this policy after an accuracy analysis is recorded and after a
question review is saved. To evaluate existing analyses, Admin opens the paper's
**Accuracy confidence** page and selects **Apply AI approval above 75%**. The
result lists each question's status and outstanding requirements. This action
uses existing analyses and makes no model calls.

The existing evidence, wording, mark totals, marking points, coverage decision
and visual-review requirements still apply. For example, an unmapped part with
unreviewed coverage cannot become AI approved solely because its wording has a
high confidence estimate. Outside-current-coverage remains an allowed decision;
it does not grant student curriculum access.

Human `approved`, `excluded` and `needs_correction` question decisions are
preserved. Human subpart decisions are preserved. The status cannot be selected
manually or forged through a review save. Admin can reopen an AI-approved item,
mark it as needing correction, or explicitly complete human approval.

Changing content or bound evidence makes the analysis stale. Stale AI approvals
are immediately excluded from readiness/release checks and presented as
unreviewed; the next policy evaluation persists that withdrawal. A newer accuracy
analysis at 75% or below also withdraws the corresponding AI approval. Human
approvals retain their existing lifecycle.

AI approval is content approval, **not automatic publication**. Explicit release,
coverage, drawing/manual-marking and automatic-assessment gates continue to apply.
AI-approved content can pass the same subsequent publication checks as human-
approved content when its analysis and review requirements remain valid.

## API and audit

`POST /api/v1/admin/official-paper-reviews/{paper_id}/auto-approval` requires an
Admin session and CSRF token. It locks question records, evaluates the latest
bound analyses and returns per-question results. GET requests never persist
approval changes. Question revisions advance when decisions change, protecting
existing editors and invalidating old tutor-release fingerprints.

Audit event `official_review.ai_approval_evaluated` records policy
`accuracy-auto-approval-v1`, exclusive threshold 75, analysis ID, content hash,
previous/new status, subpart decisions and blockers. The actor is the Admin who
triggered processing; `reviewedBy`/`reviewedAt` remain the last human review edit,
not a claim of human approval. Existing analysis history retains model provenance.

Migration `0020_question_ai_approval` extends the database status constraint.
Downgrading demotes AI approvals to unreviewed instead of inventing human approval.
Confidence remains an estimate, not a calibrated guarantee of correctness.
