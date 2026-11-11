# June 2025 Biology exact-evidence acceptance

Started and completed: 2026-11-11. Application release: `d85795457fc7c08e345a6621af9c73072615be4b` (includes `4f37c4f` feature and `95ca90a` bounded-output/identity follow-up). Scope: source associations, fresh source-fidelity assessments and guarded AI review; no Student release or automatic-scoring enablement.

## Production results

| Paper | Questions | Subparts with exact paper and scheme evidence | Region associations | AI-approved questions | AI-approved subparts |
| --- | ---: | ---: | ---: | ---: | ---: |
| June 2025 2BR | 6 | 31/31 | 118 | 0 | 30 |
| June 2025 1BR | 10 | 49/49 | 191 | 0 | 48 |
| June 2025 1B | 10 | 46/46 | 146 | 3 | 43 |
| June 2025 2B | 6 | 30/30 | 99 | 0 | 29 |
| Total | 32 | 156/156 | 554 | 3 | 150 |

Region associations include shared evidence repeated under the actual affected part labels; identical underlying version/role/bounds/text blocks are reused. Every parent question also has exact paper evidence. Existing source PDFs, questions, marks, marking points, curriculum decisions, report associations, manual-only scoring and release restrictions were preserved. All 32 final accuracy assessments are current. The 2BR Q1(c)(ii) curriculum uncertainty remains unchanged.

Six subparts deliberately remain unreviewed by the AI-approval policy:

- 2BR Q6(b)(iii): 70%, publisher rubric/mark-allocation inconsistency.
- 1BR Q6(a)(i): 87%, answer-visual approval/proposals remain unresolved.
- 1B Q4(b)(ii): 65%, question/scheme mark-allocation conflict.
- 1B Q5(b)(i): 88%, answer-visual approval/proposals remain unresolved.
- 1B Q6(b)(i): 88%, answer-visual approval/proposals remain unresolved.
- 2B Q6(b)(i): 70%, publisher rubric/mark-allocation inconsistency.

Most parent questions still have proposed/unassigned question visuals. These independent gates were not bypassed. Only 1B Q8–10 reached question-level AI approval. No human approval was created and no paper was published to students.

## Source comparison and provenance

The pilot started with 2BR and proceeded to 1BR, 1B and 2B after validating the pilot. Compared original question/scheme source-region renders and native text, including shared passages, MC options, full marking/guidance columns, labelled diagrams, data tables and continuations. Corrected an omitted pollination passage, invented shared-stem part labels, incomplete MC options/graphs/guidance and pharmaceutical-passage bounds. Omitted generic answer instructions and blank plotting grids as exact native text. Original extraction remains intact; separate visual approval remains required.

Layout proposals used the Evaluation project's actual returned `gpt-6.1-sol` model and recorded response IDs. Reasoning effort was provider default, not an explicitly requested Light setting. Final region checking/correction and fresh assessments used Codex-assisted review, attributed as operator-confirmed GPT-6.1 Sol / Light. 2B Q4–6 coordinates were prepared with Codex assistance without further paid API calls. Previously compared report sources and associations were checked as unchanged; no new handwriting transcription is claimed.

Material associations invalidated earlier accuracy. Fresh source comparison appended new assessments without raising the pre-existing source-fidelity estimates or removing conflicts. These percentages are estimated fidelity judgements, not independently calibrated accuracy rates. Earlier analysis history and provenance remain available.

A first 2B Q1 response exceeded the 4000-token output allowance and failed without applying partial output. A new explicit bounded run succeeded; the unknown-cost failure retained its full budget reservation. Purpose-specific production evidence output now defaults to 8000 tokens without changing tutor limits. The private ledger contains 30 dispatched calls (29 completed); conservative cumulative charged bound **US$1.822089**, below the approved US$2 ceiling. Completed-response rate-based estimate **US$1.1807199** excludes the unknown failed request and is not an invoice. A further request was blocked before dispatch; no further paid calls were made.

## Acceptance evidence

- 57 focused backend tests passed, including role isolation, CSRF, stale snapshots, exact-label identity, ambiguous repeated wording, cross-source blocks, missing/blank regions, source checksums, idempotent operations, human-approval protection, rejection history, jobs, accuracy and approval/review regressions.
- 122 frontend tests, typecheck, lint, OpenAPI/contract checks and production build passed during implementation. Four additional backend regression cases were added after deployment; they change tests only.
- Production migration `0021_exact_evidence_jobs` applied; Alembic drift check passed. Normal encrypted-backup deployment completed; API, worker and web health checks passed over verified HTTPS.
- Authenticated read-back verified all final links and current assessments, unchanged protected question data, source identities and release readiness. Each paper's protected preview returned PNG; unauthenticated proposal/job/preview reads returned 401. Local non-Admin regression checks returned 403.
- Normal Admin browser acceptance confirmed the accuracy panel, linked counts, separate AI status, expandable original scheme excerpt and private image preview in a narrow mobile viewport. Private screenshot: `tmp/exact-evidence-pilot/admin-source-preview.png`.
- Private source snapshots, checksums, proposal/apply receipts, fresh analyses, acceptance JSON, screenshots and cost ledger remain in ignored `tmp/exact-evidence-pilot/`; source PDFs and credentials are excluded from Git.
- Deployment evidence: `/data/akuru/release-evidence/deployed-d85795457fc7c08e345a6621af9c73072615be4b-20261111T094745Z.txt`.

The production build still reports 30 pre-existing npm dependency advisories (1 low, 13 moderate, 12 high, 4 critical), tracked by the separate dependency-security work. This feature did not update dependencies. They remain an operational follow-up, not a claim of a vulnerability-free release.

## Subsequent batches

The collection remains 16 of 44 papers source-compared, with 28 preliminary native-extraction papers still requiring full source comparison. This release does not bulk-approve those papers. Use explicit session batches, establish source/version eligibility and actual model/effort first, then verify region proposals and append fresh confidence only after source comparison. Do not copy these four papers' scores or historical model identity to a later batch.
