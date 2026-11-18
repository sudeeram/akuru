# Prepared past-paper review workflow

AKURU's model-free review API imports source analysis prepared by a developer, including Codex-assisted work. It does not call an inference API itself. See [the backend contract and CLI guide](../source-code/backend/docs/developer-review-apis.md) for routes, scope bindings, transactions, history and security boundaries, and [the Admin guide](../user-docs/PREPARED-PAST-PAPER-REVIEW.md) for the UI.

Prepared packages and receipts are persisted in indexed audit records. Each question change set is atomic; a batch is a sequence of individually committed question transactions. Resume does not refresh stale hashes or repeat successful changes. The existing source analyses remain immutable and record new comparisons separately from unchanged findings carried forward with their ancestry.

Per-part freshness separates real shared dependencies from aggregate question revisions. Newly created Tutor release fingerprints use those scoped bindings. Older release fingerprints remain conservative until explicitly renewed through the guarded release API. The same publication, same-subject curriculum, exact-evidence, source-issue, scoring and withdrawal checks continue to apply.

A source-confidence estimate above 75% is not a scoring certificate. The deployed deterministic engine must replay its actual test cases before a new deterministic rubric can be certified. Unsupported semantic explanations remain manual-only even when their source content is AI approved. Complete-exam publication remains separate from Tutor practice.

No new database migration is required: existing UUID primary keys and audit/analysis storage provide durable records. The backend guide records the implementation boundaries and the completed roadmap records production acceptance; neither a CLI receipt nor a green source label should be mistaken for proof of a complete formal exam release.
