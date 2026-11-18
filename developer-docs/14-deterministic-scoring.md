# Deterministic assessment execution

See [the implementation contract, capability matrix and CLI runbook](../source-code/backend/docs/deterministic-scoring-and-readiness.md) and [delivery status](../source-code/todo/ongoing/TODO-DETERMINISTIC-SCORING-AND-READINESS.md).

The pipeline has three distinct proofs: allocation tests; actual answer recognition followed by allocation; and optional paid model-behaviour validation. Only actual server-executed recognition establishes a deterministic readiness certificate.

`schemas/deterministic_scoring.py` defines bounded declarative rules. `services/deterministic_scoring.py` parses supported answers using decimal/rational arithmetic and a tiny arithmetic AST. It returns matches to the existing `marking_rules` allocator or abstains. `deterministic_validation.py` executes synthetic cases and persists immutable audit receipts. No package contains executable Python and no provider receives an unrecognised answer automatically.

`assessment_marking.py` dispatches before model routing/quota reservation and verifies frozen certificates. The response contract exposes only supported field names before answer reveal. A referred response has no released numerical score and does not update mastery. Student identity/family authorization comes from the existing assessment services, never from authoring packages.

Rules and runtime receipts are source-bound and engine-hashed; adding a receipt does not change source extraction content. Existing audit infrastructure avoids a schema migration. Production readiness requires production API replay; local fixture passes are preparation evidence only.
