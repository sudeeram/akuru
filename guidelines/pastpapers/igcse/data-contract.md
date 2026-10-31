# Logical intake data contract

Standard: `akuru-igcse-pastpapers` 1.2.0

Last updated: 2026-10-31

Status: proposed logical requirements, not an executable JSON Schema or current API payload.

| Entity | Required information |
| --- | --- |
| Intake batch | Stable ID, guideline/profile versions, import-format and extractor versions, processing time, validation result and optional AI provenance |
| Source | Exact paper identity, role, file hash, uploaded document/version reference and availability |
| Source location | Source/version reference, 1-based PDF page, optional printed label, block/asset reference and bounding box with declared coordinate system |
| Question | Stable paper-scoped key, number, total marks, shared stem, ordered parts, shared visuals, source locations and review state |
| Part | Stable parent-scoped key, label, parent reference, order, wording, inherited context, marks, response type, answer layout, choices, visuals and sources |
| Choice | Stable part-scoped key, source label, order and wording; correctness stays in the private rubric |
| Visual proposal | Role (question illustration, private scheme answer, or report example), exact source/version/page, crop bounds with declared coordinates, content hash, scoped subparts/marking points, accessible description, review state and completeness issues |
| Rubric | Points and source labels, semantic kind, alternatives, capped groups, dependencies, scoring instructions, correct choices, maximum and exact sources |
| Report item | Commentary/example/transcription type, question/part scope, original image where applicable, transcript uncertainty, linked comments, explicit marks and sources |
| Validation issue | Stable code, severity, affected entity/region, human-readable reason, suggested correction, resolution and reviewer |
| Review decision | Actor, timestamp, revision, decision, evidence reviewed and change history |

Keep IDs stable through retries and re-analysis. Never use a display label alone as a globally unique key. Preserve source hashes and expected review revisions to detect stale writes. Draft source locations may lack exact blocks, but approval must resolve the evidence required by the applicable release gate.

A future executable schema must validate these requirements and map them into AKURU's supported contracts. Unsupported fields must not be silently dropped. Store richer extraction proposals separately if the current review model cannot represent them, and flag the limitation. Source approval, question approval and Student publication are separate states.

Private rubric/report data must not be exposed through student question payloads during formal assessments. Existing enrolment, topic coverage and per-student access checks remain mandatory.

The visual proposal is a logical extraction record, not permission to submit additional fields to existing APIs. Preserve any unsupported axis/table-completeness metadata in the batch validation report rather than silently dropping it or claiming that AKURU stores it as structured data. Private answer visuals and report examples must remain distinguishable from question illustrations throughout extraction, review and release.
