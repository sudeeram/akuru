# Deterministic scoring and readiness

Implementation started 2026-11-18. See the ongoing deterministic-scoring TODO for rollout status; this document does not imply the production pilot is complete.

## Contract

Version 1/2 marking rules retain their existing serialization when `deterministic` is absent. Version 3 adds declarative `deterministic-v1` recognition before the existing server allocator. It never contacts an AI provider, reserves model quota or performs a paid fallback. Authentication, ownership, formal-assessment restrictions, source access, curriculum and release checks remain in effect.

Extraction confidence, content approval, scoring readiness and Tutor release are independent. A high confidence percentage is not a scoring certificate. Historical automatic/model-validated rubrics remain identifiable as legacy; they are not silently recertified.

## Supported capability matrix

| Recognition | Input | Allocation | Boundary |
| --- | --- | --- | --- |
| Numeric | Decimal/scientific final, optional approved unit | Independent criteria, existing groups, highest weighted band | Exact decimal/rational reference; explicitly authorised precision, rounding/truncation or power-of-ten alternatives only |
| Arithmetic method | Structured final plus bounded arithmetic expressions | Explicit criterion, alternative band | Only source-reviewed multiply/divide operations and operands; no free prose reasoning |
| Fixed choice/name | Entire reviewed alias or recognised source distractor | Independent point/group | Unknown synonym, negation or conflicting choice refers for review |
| Labelled answers | Exact keyed fields | Independent labelled points/caps | Correct names in wrong fields do not earn credit |
| Member set | Reviewed atomic member aliases | Source-defined all-required set | Known extra members can score zero; unknown grammar refers |
| Open explanation, drawing, handwriting | Unsupported | Manual/semantic route | Never substitute keyword occurrence for understanding |

Version-2 allocator restrictions still apply to combinations/dependencies with weighted bands. Mixed-engine **papers** can contain separate deterministic and semantic assessment items. A single compiled main-question item mixing those engines is explicitly rejected pending safe item splitting; deterministic certificates must never be silently discarded. Arbitrary tolerances/ranges, unit conversion and general symbolic algebra are not supported by this initial engine.

## Actual validation and persistence

Admin-only CSRF-protected POST `admin/official-paper-reviews/{paper}/questions/{number}/validate-deterministic` accepts bounded synthetic answer fixtures, expected scores/credited IDs, an engine hash, optimistic revision and confirmation of source review. It accepts no client marking decision or pass flag. The deployed engine executes every answer and the allocator computes actual credit. A pass requires all fixtures, coverage of all criteria, full/partial/zero outcomes as applicable, a holdout and an abstention case. The operator must additionally review source-specific allowance/mutation coverage; the coverage flag is not proof of exhaustive natural-language correctness.

The indexed existing `AuditEvent` table provides durable append-only runs, actor, timestamps, cases, hashes, source notes and provenance; no migration is required. The run UUID becomes the readiness certificate. A current certificate binds relevant shared context, part prompt, points, rules, source references, source blocks/assets and source document versions. Editing those rules invalidates readiness. Engine source hashes pin recognition, allocation, schema, validation and the marking adapter; upgrade requires replay. History returns the newest 100 runs, preserving older database audit records.

Certificate IDs are excluded from source-content hashes: adding a receipt does not itself change extracted content. Frozen assessments retain rules and certificate references, with proof verification at marking time. Pending/unrecognised answers have no released score and must not update mastery. Actual recognised zero is different from unscored review.

## Student interface

Only field names and whether arithmetic working is supported are sent before answer reveal. Private aliases and rubric values are not exposed by the answer-format contract. Practice, chat practice and assessment forms offer final/labelled fields. Unknown grammar is saved as pending review, with no paid fallback. Deterministic provenance is explicitly distinguished from model confidence; the legacy result-storage confidence column is not an accuracy estimate.

## Developer CLI

Use `source-code/backend/.venv/bin/python source-code/scripts/deterministic-scoring.py --help` from the repository root. Credentials live in an ignored file containing `AKURU_ADMIN_USERNAME` and `AKURU_ADMIN_PASSWORD`; never pass passwords on the command line.

Common arguments: `--credentials tmp/akuru-admin.env --paper <paper UUID> --number <question> --part <label> --output <private JSON path>`. Commands:

1. `fetch`: retrieve current question, capability hash and source context.
2. `preview --package <reviewed package>`: reject stale content/revision and show bounded change summary.
3. `apply --package ...`: apply only named-part rules/optional points; retain manual readiness pending replay. Save the receipt.
4. `record-assessment --package ... --receipt <apply receipt>`: submit explicitly reviewed source-comparison findings using existing versioned analysis API; no inferred confidence is manufactured.
5. `validate --package ... --receipt ...`: replay server engine; reuse only an identical current passing fixture receipt. Failed runs exit nonzero.
6. `history`: inspect current/historical validation evidence.
7. `release --enable-tutor`: explicit guarded release for the named eligible part. This never publishes a formal exam.
8. `inventory`: list per-part status/engine/readiness.

Prepared packages include schema, paper/question/part identity, expected revision/content hash, complete rules, optional source-faithful points, synthetic cases, source notes and provenance. Private source packages/receipts are mode 0600. Review every new source version before updating preconditions. Do not blindly rewrite stale hashes to force an overwrite.

A failed scoring run never enables readiness. Existing explicit withdrawals require a separate deliberate release. Whole-question source assessments/releases currently retain legacy question-wide freshness checks; restore unchanged eligible sibling releases explicitly after an intentional source reassessment. Do not claim sibling release preservation is fully solved by part-scoped scoring certificates alone.
