# Complete past-paper review through authenticated developer APIs

Created: 2026-11-18
Started: 2026-11-18
Status: ongoing — implementation authorised by the user.
Priority: high
First acceptance scope: Biology June 2025 2BR, paper `eea024fe-978f-4392-b330-c0011201cf63`. Do not change Chemistry or another paper during this pilot.

## Objective and meaning of “without paid model calls”

Complete source inspection, targeted corrections, exact evidence links, curriculum mapping, visual review, source reassessment, discrepancy decisions, eligible AI approval, deterministic scoring validation and guarded Tutor release through normal authenticated APIs and a reusable CLI. The Admin should not have to repeat unchanged browser reviews or manually restore unrelated approvals after each correction.

Source interpretation is prepared here by the developer/Codex workflow using original authorised source material. AKURU imports that attributed review and executes deterministic checks and existing approval policies. A new endpoint does **not** independently understand biology, inspect handwriting or establish semantic correctness without an appropriate reviewer/recognizer. This workflow avoids paid **AKURU inference API** calls; it does not promise free Codex/subscription usage or universally automatic marking of unrestricted student prose.

Do not build a “force approve”, “set confidence above 75%” or “all scoring rules checked” bypass. Confidence is an attributed estimate of source fidelity, not a scoring certificate or measured accuracy. Unsupported semantic scoring can remain manual-only while source content becomes AI approved. Never label developer-provided findings as an AKURU provider response.

## Evaluation performed

The catalogue below was checked against local route handlers, schemas and service call paths on 2026-11-18, including:

- `backend/app/api/v1/official_paper_reviews.py` and `documents.py`.
- `services/official_paper_reviews.py`, `official_question_analyses.py`, `question_auto_approval.py`.
- `services/paper_source_issues.py`, `evidence_links.py`, `evidence_link_jobs.py`, `accuracy_jobs.py`.
- `services/paper_curriculum.py`, `paper_workflow.py`, `tutor_past_papers.py`.
- `services/deterministic_validation.py`, `paper_scoring_validation.py`, and the developer scoring CLI.

This is a code-based capability evaluation, not a new production security audit or a new assessment of the original PDFs. Production findings for Q1/Q4/Q5 below come from the immediately preceding authenticated inspection in this chat and must be fetched again before any future write.

### Confirmed gaps

1. Full-question saves replace a large document of review data. Reopening a human-approved question can demote approved sibling parts. There is no general staged, scoped correction transaction with a reviewable diff and impact report.
2. Analysis input currently requires every subpart even for a one-part correction. Source accuracy hashes include the whole question. Unchanged findings have to be copied forward by scripts rather than explicitly carried forward with their own validity proof.
3. Source-issue decisions are bound to the whole-question content hash. A sibling change can make an unchanged adjudication appear unresolved. `resolve` currently records a note; it does not itself demonstrate that an extraction omission was corrected.
4. Tutor release fingerprints include question revision/full data and the full-question evidence hash. Eligibility also filters release revision against the current question revision. Scoping only a scoring certificate does not solve sibling release freshness.
5. Confidence approval is server-owned, but its explicit endpoint is paper-wide. Some save/analysis services also invoke approval internally. A correction package needs a predictable scoped result without evaluating unrelated questions or hiding side effects.
6. Existing services commit independently. Calling several APIs sequentially can leave corrected wording saved but analysis stale, an issue unresolved, or a release not restored. Reusable staging/resume support is needed beyond private scripts.
7. Exact-link proposal selections support only `paper` and `scheme`; report links can be saved through the question payload but lack the same structured proposal/review contract. AI-assisted imported link proposals also require a known model ID, whereas analysis provenance permits explicitly unrecorded identity.
8. Crop creation/review and association are possible, but a generic existing-candidate visual decision API is missing. `create_review_crop` creates an already-reviewed crop; it must not be confused with automatic approval of every generated candidate.
9. Published curriculum evidence can be read and mappings saved, but no general typed prepared-mapping validation/apply operation gives a scoped preview, conflict report and publication binding independent of paid reassessment jobs.
10. Workflow, accuracy readiness, release readiness, issues and scoring certificates have separate reads. They do not yet provide one structured, per-part explanation of all gates and exactly which operation resolves each blocker.
11. `accuracy-context` builds rich source pages, including image data. A lightweight, version-bound review-package manifest with authorised asset links would make developer inspection more manageable.
12. Existing no-model routes are not assembled into an enforced no-inference workflow. Authenticated access alone does not guarantee that a queued operation will avoid a provider call.

## Existing endpoints to reuse

All paths in the next tables are relative to `/api/v1/admin/official-paper-reviews`, unless another base is written explicitly. Existing paths are implemented; proposed paths later are design candidates, not available APIs.

| ID | Existing method/path | Capability and cost boundary | Action |
| --- | --- | --- | --- |
| E01 | `GET /{paper_id}` | Current question data, revisions, analyses and paper blockers; no inference | Retain; expose stable part references and link to unified readiness |
| E02 | `GET /{paper_id}/questions/{number}/accuracy-context` | Original page context and curriculum candidates; reading does not invoke a model | Retain; reuse its source preparation in lightweight package export |
| E03 | `GET /{paper_id}/questions/{number}/analyses` | Immutable analysis history/currentness; no inference | Extend with per-part freshness and carry-forward origin |
| E04 | `POST /{paper_id}/questions/{number}/analyses` | Imports supplied, attributed source findings; no inference. Currently requires all parts and can evaluate confidence approval | Extend with scoped import, explicit approval intent, immutable carried-forward findings and transaction support |
| E05 | `POST /{paper_id}/questions` | Saves wording, points, alternatives, report guidance, evidence, mappings and scoring rules; no inference | Keep backwards compatibility; route new scoped corrections through the shared change-set service |
| E06 | `GET /{paper_id}/questions/{number}/source-issues` | Current issue listing and resolution notes | Add issue lifecycle/history, dependency bindings and typed actions |
| E07 | `POST /{paper_id}/questions/{number}/source-issues/resolve` | Audited source decision; no inference; currently whole-question-hash bound | Extend; a note alone must not certify a corrected extraction |
| E08 | `GET /{paper_id}/evidence-links` | Evidence proposal history | Retain; add role/scope filters and pagination |
| E09 | `POST /{paper_id}/evidence-links` | Imports supplied selections or makes deterministic lexical proposals; this synchronous service does not call an inference provider | Extend report role, provenance and unlink/replace operations; lexical suggestions are not semantic source verification |
| E10 | `POST /{paper_id}/evidence-links/{run_id}/review` | Applies/rejects reviewed links | Retain and support atomic change-set application without an internal commit |
| E11 | `GET /{paper_id}/evidence-links/{run_id}/{proposal_id}/preview` | Private original-source crop | Retain; authorise every read against the bound source/version |
| E12 | `GET /{paper_id}/topics` | Published same-subject topics | Retain |
| E13 | `GET /{paper_id}/topics/{topic_ref}/evidence` | Published textbook evidence | Retain; use stable topic/publication/chunk references, with visual-reference printed pages for display where available |
| E14 | `GET/POST /{paper_id}/visual-crops` | Lists reviewed crops/creates an explicitly reviewed crop | Extend review intent and bindings; use staged visual decisions for existing candidates |
| E15 | `POST /{paper_id}/visual-candidates/generate` | Existing source-layout candidate generation, separate from paid illustrative generation | Reuse only after inspecting its complete call graph; no implicit approval or image-model generation |
| E16 | `GET /{paper_id}/deterministic-capabilities` | Deployed bounded scoring engine and fingerprint | Retain |
| E17 | `POST /{paper_id}/questions/{number}/validate-deterministic` | Deployed engine executes actual answer fixtures; derives scoring readiness without model calls | Retain authoritative proof; integrate guarded replay and idempotency, never accept client pass flags |
| E18 | `GET /{paper_id}/questions/{number}/deterministic-validations` | Actual case results and current/historical certificates | Retain; paginate history/case details as volumes grow |
| E19 | `POST /{paper_id}/auto-approval` | Applies confidence/content policy without inference, currently paper-wide | Retain legacy operation; new workflow uses scoped policy evaluation |
| E20 | `GET /{paper_id}/chat-release-readiness` and `GET /{paper_id}/chat-releases` | Tutor release diagnostics/history; no inference | Retain and expose part-scoped validity/withdrawal reasons |
| E21 | `POST /{paper_id}/questions/{number}/chat-release` | Explicit guarded Tutor release/withdrawal | Retain; add idempotency, scope fingerprints and clear restoration provenance |
| E22 | `POST /{paper_id}/auto-tutor-release` | Retries guarded releases subject to configuration, without inference | Extend optional question/part selection and dry-run; respect explicit withdrawals |
| E23 | `GET /workflow?documentId=...` | Read-only workflow labels for papers and companions | Retain; derive from shared readiness service rather than duplicate gate logic |
| E24 | `POST /{paper_id}/prepare-official-drafts` | Prepares complete-paper drafts after existing gates | Retain; separate from Tutor release and formal publication |
| E25 | `POST /{paper_id}/questions/{number}/worked-answers/import-draft` | Imports an externally prepared attributed worked answer, without generation | Reuse when actually needed; retain independent review, provenance and approval |
| E26 | `/api/v1/documents/{document_id}/content`, `/extraction`, `/assets/{asset_id}/content` (`GET`) | Original documents, extracted blocks and stored asset bytes | Reuse; no duplicate public source-download endpoint |
| E27 | `/api/v1/documents/{document_id}/official-review` (`GET/POST`), `/official-review/publish` (`POST`) | Official companion/paper material review and explicit publication | Retain; do not manufacture “AI approved” companion-document labels from question confidence |

Existing start/seed/upload/retry, worked-answer review/attach and account APIs remain in place. They are not all new endpoint requirements for correcting Q1(e), Q4(b)(iv) and Q5(d).

### Existing routes excluded from the no-inference workflow

- `POST /{paper_id}/accuracy-jobs`: queues a worker that calls `AIAccountRouter.generate` in its normal production path.
- `POST /{paper_id}/evidence-link-jobs` and `/evidence-link-job-batch`: model-assisted worker paths.
- `POST /{paper_id}/questions/{number}/validate-scoring`: existing semantic scoring regression, normally using model marking passes.
- `POST /{paper_id}/questions/{number}/worked-answers`: model generation, distinct from `import-draft`.
- Assessment evaluate/reassess endpoints are **not universally model-free**: cost depends on frozen question engines. Never invoke them implicitly to repair source approval.

Do not redirect to any of these on a missing finding, unsupported answer or failed deterministic check. Optional paid workflows remain separate and require explicit authorisation outside this plan's no-inference operations.

## Proposed new endpoint catalogue

Implement shared domain services first; the route count is not a requirement to duplicate existing logic. The following twelve routes form a proposed coherent API. Consolidate overlapping reads with query parameters if design review shows an existing response can provide the same contract.

| ID | Proposed method/path | Purpose | Priority |
| --- | --- | --- | --- |
| N01 | `GET /{paper_id}/readiness` | One per-question/per-part gate report: source freshness, confidence, exact evidence, visuals, curriculum, content approval, source decisions, scoring engine/certificate, Tutor eligibility and formal-paper readiness | Essential |
| N02 | `GET /{paper_id}/review-package` | Paginated source-bound export; filter question numbers/part references. Include version/hash manifests, reviewed data, original page/block/asset references, analyses, issue decisions, publication bindings and current releases; image bytes excluded by default | Essential |
| N03 | `POST /{paper_id}/change-sets` | Stage typed, attributed corrections for one question and selected parts; accepts prepared source findings, evidence/mapping changes and issue decisions without applying them | Essential |
| N04 | `GET /{paper_id}/change-sets/{change_set_id}` | Retrieve immutable prepared revision, state, base/target hashes, provenance and operation linkage | Essential |
| N05 | `GET /{paper_id}/change-sets/{change_set_id}/preview` | Deterministic validation and human-readable diff; show every affected scope, carried-forward review, invalidated proof, required re-review and intended release change | Essential |
| N06 | `POST /{paper_id}/change-sets/{change_set_id}/apply` | Apply the exact reviewed preview transactionally to the question/parts. Return source-analysis, issue, approval and release outcomes separately; no provider calls | Essential |
| N07 | `POST /{paper_id}/review-batches` | Start a bounded list of already-staged change sets, each with expected hashes and explicit action intent. Use a separate no-inference job kind, never an accuracy/model job | Important for repeatability |
| N08 | `GET /{paper_id}/review-batches/{batch_id}` | Durable per-item progress, receipts, current/stale state, failures, remaining blockers and actual no-inference execution evidence | Important for repeatability |
| N09 | `POST /{paper_id}/review-batches/{batch_id}/resume` | Resume incomplete work only; verify revisions/hashes, skip current completed receipts, do not replay successful mutations or rebase over another Admin's edits | Important for repeatability |
| N10 | `POST /{paper_id}/questions/{number}/auto-approval` | Server evaluates policy for the named question/selected parts, including aggregate question status; no client-assigned `ai_approved` field. Supports dry-run and optimistic concurrency | Essential |
| N11 | `POST /{paper_id}/release-validation` | Non-mutating validation with an explicit target: `tutor_practice`, `official_drafts` or `formal_exam`. Returns typed blockers and an expiring hash-bound readiness receipt; passing validation itself publishes nothing | Essential |
| N12 | `GET /{paper_id}/review-history` | Paginated, role-restricted combined history of corrections, source findings, carried-forward evidence, discrepancy decisions, proofs, approval and release changes | Important for audit/recovery |

N01/N02/N10/N11 should be small interfaces over shared policy services. N03–N06 provide the principal safe write path. N07–N09 supply durable orchestration, not a second interpretation engine. N12 may aggregate existing immutable audit/analysis records rather than introduce a duplicate audit ledger.

### Typed operations inside a change set — not twelve more standalone APIs

- `correct_part_content`: wording, shared context where explicitly targeted, marking points, accepted alternatives, report guidance and supported scoring-rule definitions.
- `change_evidence_links`: add/unlink/replace exact paper/scheme/report evidence while validating document ownership and source versions.
- `record_visual_decision`: keep/re-crop/replace/reject candidate, caption/accessible description, shared-versus-part association and question-versus-answer visual distinction. An approval action requires explicit visual-review provenance; never silently tick images because text was reviewed.
- `record_curriculum_mapping`: same-subject topic/publication/chunk/printed-page references with a validation/conflict result and review basis.
- `record_source_assessment`: newly compared findings for changed scopes and explicit carry-forward references for unchanged scopes.
- `resolve_source_issue`: typed decision tied to exact issue/source versions and, for a corrected extraction, the correction and reinspection receipt.
- `evaluate_content_approval`: server policy only, with selected scope.
- `replay_deterministic_scoring`: reuse E17; actual server execution required if scoring meaning/engine changed.
- `request_tutor_release`: explicit selected scope and existing release policy. Default is validation only; formal publication is never implicit.

Use dedicated typed request schemas and allowlisted fields, not arbitrary JSON paths, SQL, Python, shell commands or executable package code. There is no Student-performance mutation operation in this source-review API.

## Step 0 — Freeze scope and prove current blockers

- [ ] Fetch fresh Q1–Q6, bound original source versions, current analyses, issue history, scoring certificates, curriculum evidence and Tutor releases through existing authenticated reads.
- [ ] Record the initial Q1(e), Q4(b)(iv) and Q5(d) blockers and their source pages; do not treat an old snapshot as a write target.
- [ ] Preserve human approvals and known discrepancy decisions, including the standing marking-scheme-over-report decision. An internal marking-scheme contradiction still requires an explicit adjudication.
- [ ] Record that AI content approval, automatic scoring readiness, Tutor release and complete-exam publication are separate outcomes. Define “no repeated review” as carrying forward unchanged, correctly bound evidence, not skipping review of actual changes.
- [ ] Confirm exact new/extended route shapes against generated OpenAPI before implementation. Check callers so legacy Admin UI and scripts remain compatible.

## Step 1 — Define part-scoped dependencies and review validity

- [ ] Give each subpart a stable reference distinct from its display label; retain question number/labels and backward-compatible lookup. A rename must not transfer a review to different content.
- [ ] Define separate fingerprints for source wording/marking content, shared context, visuals, rubric/answer format, curriculum publication/mapping, issue decisions and release policy.
- [ ] Distinguish genuinely shared source blocks from the parent question's aggregate union of child links. Likewise, an assembled parent prompt containing all subparts must not make every sibling depend on all other subpart wording.
- [ ] Store new part bindings on analysis/decision/release records. Backfill historical bindings only when the saved source snapshot proves them; unknown historical scope remains stale and must not be invented.
- [ ] A sibling-only correction preserves unchanged part findings, human/AI decisions, valid scoring certificates and eligible releases. A shared stem/table/diagram, relevant source version or genuinely shared scoring dependency invalidates all affected dependants.
- [ ] A metadata-only note does not invalidate scientific content; a curriculum-publication change invalidates affected mapping/release gates even if wording is unchanged. A real rubric edit invalidates affected scoring proof.
- [ ] Fix all freshness consumers together: analysis responses, `current_accuracy`/approval policy, source-issue resolution, `release_fingerprint`, release eligibility revision filters, workflow labels and frontend cache keys. Do not merely change the hash helper while leaving contradictory checks elsewhere.
- [ ] Derive whole-question confidence/status from constituent valid findings and explicit shared findings. An unchanged part must say “carried forward from analysis X”, not pretend it was freshly re-read.

## Step 2 — Build unified diagnostics and review-package export (N01/N02)

- [ ] Return stable blocker codes, question/part, gate, evidence references, next action, whether it needs source interpretation, and whether the proposed action uses a model. Distinguish blocking errors, warnings and informational findings.
- [ ] Keep `contentApproval`, `sourceAccuracy`, `reportGuidance`, `curriculum`, `scoringReadiness`, `tutorRelease` and `formalRelease` separate. A manual-only scoring limitation does not automatically prevent valid source-content AI approval.
- [ ] Surface missing report/no applicable commentary truthfully. Report fidelity is separate from the extraction confidence used by current policy; unreliable commentary can be excluded with an audited decision.
- [ ] Export original stored PDFs/page images/blocks through existing authenticated source URLs, with document/version/page/bounds/hash identity. Do not embed every image in routine summary responses or create public source URLs.
- [ ] Bound page/part/asset counts, paginate, preserve source permissions, and detect changed versions. No arbitrary URL retrieval or filesystem paths from client payloads.

## Step 3 — Build scoped correction staging and preview (N03–N05; E05 extension)

- [ ] Define package version, paper identity, expected question/part revisions, base source/rubric hashes, guideline version, provenance and explicit operations.
- [ ] Stage corrections without changing live content. Preview reports before/after data, affected gates, preserved siblings, issue actions, source-assessment requirements, proof invalidation and release consequences.
- [ ] Allow an approved part to be amended through an explicit scoped reopen action. Preserve its previous approved version/history and untouched sibling approvals. Never silently keep approval on materially changed wording.
- [ ] Hash and bind the preview; any changed payload, source, publication or conflicting Admin edit requires a fresh preview. No server-side “refresh expected hashes and overwrite” shortcut.
- [ ] Do not let packages directly set `ai_approved`, assert a scoring certificate, overwrite import-time confidence or silently re-enable a withdrawn release.

## Step 4 — Extend evidence, visual and curriculum operations (E09/E10/E12–E15)

- [ ] Extend exact-link imports to examiner reports with correct `checked`, `no_comment`, `not_available` and page-only versus exact-block semantics. Do not require an invented report block when no applicable report comment exists.
- [ ] Accept honest Codex-assisted provenance when the actual model identity is unknown: explicit `not_recorded` with an explanation. Record a reliable model/reasoning setting when available; never fabricate an API response ID, token usage or human reviewer identity.
- [ ] Validate source ownership, role, document version, page and block/region. Expose linked/unlinked state and idempotent add/remove/replace results. Linking a source is not extracting its marking points.
- [ ] Support explicit existing-candidate visual review without unnecessary re-cropping. Preserve labels, axes, units and captions; validate shared/subpart association and answer-visual ownership. Retain existing manual visual approvals when the visual and its dependencies are unchanged.
- [ ] Validate supplied curriculum mappings against current published same-subject topic/content/chunk records; flag conflicts rather than overwriting an Admin's different choice. Use visual-reference printed page labels for familiar book references when available, while retaining publication/hash bindings internally.
- [ ] Do not infer that a generic numerical calculation automatically establishes complete curriculum support or that printed-page labels alone verify an entire concept.

## Step 5 — Import targeted source findings and resolve issues safely (E03/E04/E06/E07)

- [ ] Import newly reviewed source findings for changed parts only; assemble the current question analysis using valid carried-forward siblings and immutable ancestry.
- [ ] Store method/execution origin, known/unknown model identity, guideline/version, inspected original source references, source-specific confidence/reasons and actual processing time. Keep initial extraction provenance separate from later review provenance.
- [ ] Bind findings to the exact previewed final content and source versions. A source confidence estimate cannot be raised automatically just because a correction was submitted or tests passed.
- [ ] Represent issue dispositions such as `corrected_and_rechecked`, `scheme_precedence`, `report_guidance_excluded`, `publisher_ambiguity_adjudicated`, or `still_unresolved`. Preserve the original issue and decision history.
- [ ] Carry forward a resolution only when that specific issue and all relevant scope dependencies remain unchanged. A changed issue description, scheme row or interpretation requires a new decision. Sibling changes alone must not invalidate it.
- [ ] For extraction defects, require a linked correction and attributed source recheck. For report/scheme conflicts, record the exact controlling instruction; prefer the marking scheme under the user's standing rule without treating internal scheme contradictions as resolved.

## Step 6 — Apply changes atomically and evaluate scoped approval (N06/N10)

- [ ] Refactor participating services to support caller-owned transactions (`commit=False` or a clear unit of work). Reuse existing policy logic; do not copy approval rules into the orchestration layer.
- [ ] For one question change set, atomically persist the scoped correction, analysis/carry-forward bindings, issue decisions and requested content-approval evaluation, or roll back the database changes together.
- [ ] Stage filesystem/object-store crops before commit and clean up failed staging; use transactional outbox/finalisation where needed. Database rollback alone does not undo external files.
- [ ] Return independent outcomes: content saved, source assessment current, issues resolved, part/whole-question approval, scoring readiness and Tutor-release result. A manual-scoring blocker must not be reported as a failed save of valid content.
- [ ] Use idempotency keys plus request hashes, optimistic version/hash checks and appropriate locks. Same request/same payload returns its receipt; same key/different payload or changed sources returns a conflict.
- [ ] Scoped AI approval requires current attributed confidence **strictly above 75%**, complete required evidence, reviewed applicable visuals, valid content and no unresolved extraction defect. Preserve human-approved decisions. Apply current source-discrepancy/release rules separately rather than silently changing policy.
- [ ] Recompute the whole-question label when every required subpart passes. Never mark a whole question AI approved merely because one subpart passed, or downgrade valid sibling approvals because a different part was edited.

## Step 7 — Integrate deterministic proofs and guarded release (E16–E22; N11)

- [ ] Preserve existing server-replayed certificates when their actual rubric, answer grammar, sources/shared dependencies and engine remain compatible. Re-run actual answer recognition/allocation only when affected.
- [ ] Reuse E17 for supported engines with positive/partial/zero, near-miss, ambiguous and holdout cases. No imported local pass/expected marking decision can replace deployed server execution.
- [ ] Unsupported open explanations/drawings remain explicitly manual/semantic; no paid fallback and no “manual attestation” that masquerades as a deterministic certificate.
- [ ] Validate Tutor practice, official drafts and formal publication separately. Content AI approval is not evidence of unrestricted automatic scoring capability or complete-paper release readiness.
- [ ] Restore only explicitly intended previously enabled releases whose scoped gates still pass. Preserve explicit withdrawals; do not re-enable them because an old snapshot once showed them live.
- [ ] Keep whole-exam publication a separate explicit action using existing material review/publication APIs. Return companion marking-scheme/examiner-report status from real source review/association state, not a duplicated four-step approval label.

## Step 8 — Durable no-inference batches, audit and CLI (N07–N09/N12)

- [ ] Add bounded per-question transactions with durable item receipts. Batch responses must state partial completion accurately; never imply a paper-wide atomic commit when earlier questions already committed.
- [ ] Support dry-run, selected question/part, stop-on-conflict, continue-independent-items and resume. Do not retry semantic interpretation, fabricate missing findings, duplicate passes or overwrite concurrent edits.
- [ ] Include before/after scoped hashes, actor, delegated execution origin, timestamps, guideline/provenance, imported versus carried-forward findings, issue/proof/approval/release references and remaining blockers in audit receipts.
- [ ] Prohibit provider routing, model quota reservation, AI generation and model-job creation by construction in this workflow. A `noPaidCalls=true` label alone is insufficient. Record model invocation count/token use as actual execution telemetry, not client assertions.
- [ ] Extend the existing CLI with export, stage, preview, apply, status/history, scoped approval, source-decision, prepared-mapping, validation and resume operations. No routine direct production SQL or server-private service imports are needed for review authoring.
- [ ] Keep credentials in ignored files or authorised sessions, never in command arguments/logs/packages/Git. Keep licensed source exports and private review packages outside Git; commit only safe schemas, tooling, guidelines and sanitised evidence.
- [ ] Choose durable tables/constraints for change sets, operation items and dependency bindings after reviewing existing audit/analysis/job models. Add forward migrations if needed; do not reset databases or store the sole operation state in temporary files.

## Step 9 — Security, frontend parity and regression gates

- [ ] All new reads are Admin-only; writes require the existing authenticated Admin session and CSRF protection. Do not create an unauthenticated Codex endpoint or a universal long-lived bypass token. Future service credentials would need separate scoped design.
- [ ] Check paper/course/subject/source ownership and bound versions on every request. Enforce private asset access, limits, pagination, rate control, state transitions and safe error messages; do not expose credentials, Student transcripts or filesystem details.
- [ ] Frontend uses the shared readiness service, displays per-part freshness and blockers, preserves selected question/subpart and invalidates affected queries after API-driven work. Show carried-forward versus newly reviewed provenance and useful toasts.
- [ ] Test unauthenticated/Student/Parent denial, CSRF, cross-paper references, wrong source roles, invented page/block IDs, foreign-subject mappings and withdrawn publications.
- [ ] Test sibling-only preservation, shared-context invalidation, source-version change, explicit withdrawal, engine upgrade, failed actual scoring replay and human-approved content amendments.
- [ ] Test correction-plus-assessment rollback, staged asset cleanup, duplicate requests, crashes/resume, conflicting Admin edits, changed previews and honest partial batch outcomes.
- [ ] Use fail-on-call provider/router/quota/job stubs for every new workflow, including failure/retry paths. Tests must fail if a paid path is called; imported provenance is not a real model invocation.
- [ ] Verify unsupported semantic marking stays manual while corrected source content can become AI approved. Confidence estimates must remain source-justified; do not hard-code a passing percentage to turn a label green.
- [ ] Run meaningful backend/frontend tests, generated contract checks, typecheck, lint, build and disposable-database migration checks. Update API/architecture/CLI/user instructions and source-extraction guidelines.

## Step 10 — Biology-only acceptance and controlled deployment

- [ ] Locally prove correction packages for Q1(e), Q4(b)(iv) and Q5(d) using their exact original scheme rows and permitted alternatives. Preserve original documents and all earlier analyses.
- [ ] Q1(e): restore equivalent-answer and scented-petal allowances and preserve the source's distinction between adaptation naming and explanation. Recheck against the original before supplying a new confidence estimate.
- [ ] Q4(b)(iv): include permitted converse comparisons for ungrazed B and variation between quadrats, with official caps intact.
- [ ] Q5(d): include permitted converse controls and the distinction between birth mass/puberty mass; preserve the scheme's rejection of an unqualified higher-mass assertion.
- [ ] Preview the exact affected parts and preserved siblings; apply the corrections, scoped findings, extraction-issue resolutions and eligible AI approval through the new API workflow. No repeated browser review of unchanged items.
- [ ] Confirm whether Q1/Q4/Q5 now meet whole-question AI approval. Report each remaining gate explicitly; do not promise a confidence result before inspecting the final content.
- [ ] Review any remaining report-guidance/source-discrepancy decisions separately. Q6(b)(iii)'s internal scheme contradiction and Q4(b)(ii)'s unsupported scoring pathways do not disappear because source content is AI approved.
- [ ] Verify the existing ten deterministic certificates/135 cases and fourteen previously live Tutor subparts are preserved where unaffected; replay only genuinely changed proofs. Keep Student performance records out of source-review migrations/tests.
- [ ] Deploy only the reviewed, tested release when implementation is requested and authorised; perform backups, forward migrations, health/security and authenticated acceptance checks. No deployment is part of writing this plan.
- [ ] Publish a sanitised before/after report with approval, source freshness, issue, scoring and release status for all 31 subparts. Chemistry and other papers remain unchanged.
- [ ] Mark this roadmap complete only when the generic workflow and Biology acceptance are proved; record start/completion dates and move it to `todo/completed`. A later other-paper rollout requires its own authorised scope.

## Minimum path versus complete delivery

For the three immediate corrections, the minimum development is N01/N02 plus staged/scoped changes and preview/apply (N03–N06), targeted analysis/issue extensions, scoped approval (N10), and safe dependency preservation. Existing deterministic validation and Tutor release APIs should be reused.

For repeatable future intake, add durable batches/resume/history and unified release validation (N07–N09/N11/N12). Evidence/report, visual and curriculum extensions complete the authoring workflow without unnecessary standalone endpoints for every field.

The current APIs can already perform much of the immediate work sequentially. New development is primarily to make the process scoped, auditable, atomic where promised, resumable and free from repeated review of unchanged content—not to obtain authentication that was previously missing.

## Related plans and documentation

- [Existing deterministic scoring and readiness roadmap](../ongoing/TODO-DETERMINISTIC-SCORING-AND-READINESS.md) — reuse certificates, CLI and execution; implement shared dependency-freshness work once.
- [Biology rollout evidence and per-part limitations](../../backend/docs/deterministic-scoring-pilot.md).
- [Deterministic scoring contracts and commands](../../backend/docs/deterministic-scoring-and-readiness.md).
- [Past-paper workflow and automatic Tutor release](../completed/TODO-PAST-PAPER-WORKFLOW-AND-AUTO-TUTOR-RELEASE.md) — reuse the existing four-stage release policy.
- [Past-paper extraction standards](../../../guidelines/pastpapers/igcse/README.md).

## Implementation checkpoint — 2026-11-18

The twelve model-free routes, scoped analysis/decision/release bindings, prepared review UI and CLI are implemented locally. Exact evidence can be materialised without changing a live review. Per-question apply uses a savepoint plus one transaction; batches persist independent receipts and resume without inference. Existing audit/analysis tables are reused, so no migration/reset is necessary.

Validation so far: 609 backend tests passed, 1 skipped; 123 frontend tests passed; typecheck, lint, generated contract and production build passed. Additional malformed-content validation was added after the full backend run and requires its targeted check. Production deployment and Biology correction acceptance are still pending. Checkboxes remain open until acceptance is recorded rather than declaring the plan complete prematurely.

Implementation documentation: [API and CLI guide](../../backend/docs/developer-review-apis.md), [developer overview](../../../developer-docs/15-prepared-past-paper-reviews.md), [Admin instructions](../../../user-docs/PREPARED-PAST-PAPER-REVIEW.md).
