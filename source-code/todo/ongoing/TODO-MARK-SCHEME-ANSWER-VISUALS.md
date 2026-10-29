# Approved mark-scheme answer visuals and drawn-response assessment

Created: 2026-10-29
Started: 2026-10-29
Status: core implementation deployed and production verified on 2026-10-29. Extended visual regression fixtures and expert-reviewed scientific evaluation remain open; automatic drawing marking remains disabled.

## Objective and scope

Capture diagram answers from marking schemes as reviewed, private model-answer visuals, then show them to Students when answers may be revealed. Use June 2025 Edexcel Chemistry 4CH1/1C Q5(c)(ii) as the first acceptance case, while supporting other drawing, graph and scientific-diagram questions without question-specific code.

Deliver model-answer capture and display first (Steps 0–5). Student drawing submission and automatic visual assessment are a separately gated second phase (Steps 6–7). Displaying an approved answer must not imply that AKURU can automatically assess a drawing reliably.

Extend the existing [official-paper review workspace](../ongoing/TODO-OFFICIAL-PAPER-REVIEW-WORKSPACE.md) and [past-paper analysis plan](../planned/TODO-IGCSE-PASTPAPER-ANALYSIS.md). Reuse their source provenance, revisions, approvals, assessment snapshots and release controls.

## Verified starting point

Read-only inspection on 2026-10-28 confirmed Q5(c)(ii) has two textual marking points and links to marking-scheme PDF page 8, but no dedicated approved model-answer images. The scheme requires fully displayed butane and methylpropane, one mark each, with all bonds shown. Its original drawings are intact. The page also contains neighbouring answers, so showing the complete scheme page is unsuitable as a targeted model answer.

The current question-visual attachment mechanism must not be reused to expose answers: question visuals are available while answering. Q5(c)(ii)'s automatic-assessment readiness was unreviewed at inspection; re-read production before any later update.

## Step 0 — Define contracts and source fixtures

- [x] Inspect current rubric, visual-asset, review, assessment and Student answer-display contracts; document what can be reused and what requires an additive migration.
- [x] Record source version/hash, exact subpart and marking-point identities for Q5(c)(ii); keep licensed PDFs and extracted images outside Git.
- [x] Define distinct roles for question illustrations, approved scheme answers and examiner-report candidate examples. Incorrect candidate examples must never become trusted model answers.
- [x] Define reveal rules for guided practice and formal assessments, using server-side submission/result-release policies rather than frontend visibility alone.

## Step 1 — Store private, versioned answer visuals

- [x] Add explicit rubric/subpart answer-visual associations, supporting multiple images and optional links to individual marking points.
- [x] Store source document/version, PDF page, normalized crop bounds, asset identity/hash, caption, accessible description, display order, review state and reviewer/audit details.
- [x] Require a matching paper/subject and scheme source; reject cross-paper assets, invalid crops and stale revisions.
- [x] Preserve published rubric/attempt snapshots when a crop or description is replaced. New edits require review and release through existing version controls.
- [x] Keep answer assets and their URLs out of question-taking payloads. Enforce authorization on image/content endpoints, including guessed asset IDs and cached responses.

## Step 2 — Propose and review answer diagrams

- [x] Detect or propose relevant diagram regions within the correct scheme row/subpart; allow manual creation when extraction is uncertain.
- [x] Include meaningful bonds, atom labels, axes, legends and external annotations; exclude neighbouring answers and unrelated row text.
- [x] Add Admin preview, crop adjustment, subpart/marking-point association, caption/alt-text editing, approve, reject and replace actions.
- [x] Show proposed versus approved states and missing visual-answer warnings clearly. Permit incomplete draft saves without marking the answer ready.
- [x] Provide idempotent authenticated API operations with expected-revision conflict handling and audit records; preserve unrelated reviewed content on re-analysis.
- [x] For Q5(c)(ii), prepare separate approved crops for butane and methylpropane, associated with their corresponding one-mark points. Record the shared requirement to show every bond.

## Step 3 — Integrate answer readiness and publication

- [x] Represent when a model answer requires a visual; block release of an incomplete visual model answer with actionable messages.
- [x] Keep content/model-answer approval separate from automatic-scoring readiness. Support reviewed model answers with manual-only assessment where appropriate.
- [x] Freeze approved answer assets and their source versions into released rubrics/assessment snapshots; prevent a later replacement from silently changing an existing attempt's answer.
- [x] Preserve ordinary text-only answers and existing question visuals without requiring retrospective visual approval on every question.

## Step 4 — Display approved model answers to Students

- [x] Integrate approved answer visuals into existing practice feedback and released formal-assessment results, alongside marking points and explanation.
- [x] Use responsive bounded image sizing, accessible descriptions and zoom/fullscreen where useful; preserve scientific detail on mobile.
- [x] Display only the relevant answer crops, with useful source attribution, rather than exposing an unrestricted marking-scheme page or raw JSON link.
- [x] Explain Q5(c)(ii)'s two distinct structures, all-bonds requirement and why rotating the same molecule does not count as another isomer.
- [x] Apply reveal permissions to image retrieval, downloads and client caches; clear user-specific caches on logout/account changes and prevent pre-release fetching.

## Step 5 — Test and release model-answer visuals

- [ ] Add synthetic fixtures for multiple diagrams, adjacent scheme rows, clipped labels, replacement versions and rejected proposals.
- [x] Test Admin APIs, draft saves, approvals, concurrent edits, provenance, published snapshots and text-only backwards compatibility.
- [x] Test Student/family isolation and attempts to fetch answer assets before submission or formal result release, including direct URLs.
- [ ] Verify the complete Admin-to-Student flow on desktop/mobile with keyboard and screen-reader-accessible controls.
- [x] Update `guidelines/pastpapers/igcse`, developer docs and Admin/Student instructions: diagram answers need dedicated reviewed model-answer assets; source links alone are insufficient.
- [x] Run relevant backend/frontend checks, prepare migration/rollback instructions if needed, and deploy only when implementation/release is authorized.
- [x] Re-read production Q5(c)(ii), apply only the reviewed answer-visual changes through authenticated APIs, and verify authorized display plus pre-release denial. Do not approve unrelated questions or enable automatic marking as a side effect.

## Step 6 — Add drawn-answer submission (separate phase)

- [x] Audit existing submission capabilities before deciding whether to extend photo upload, add an accessible drawing canvas, or both.
- [x] Bind drawing/photo submissions to the authenticated Student, attempt and exact subpart; enforce exam timing, final submission and immutable submitted versions.
- [x] Validate file content/type/size, safe rendering and ownership; provide preview, replacement before submission and accessible alternatives.
- [x] Retain the original submitted image for review; do not reduce a diagram to OCR text as the only assessment evidence.
- [x] Provide an explicit pending/manual-review result when automatic visual marking is unavailable; do not turn unsupported submissions into zero scores or negative mastery evidence.

## Step 7 — Evaluate diagram-aware marking before enabling it

- [x] Use the approved rubric and model-answer visuals with the Student image to produce structured marking-point evidence, uncertainties and proposed credit.
- [x] For molecular diagrams, check connectivity, atom labels, required bonds and distinct isomers; accept valid rotations/orientations. Do not use pixel similarity as correctness.
- [x] Enforce marks and existing structured scoring rules deterministically after model evidence matching; Q5(c)(ii) can never exceed two marks.
- [ ] Build expert-reviewed test cases for both correct isomers, rotated duplicates, condensed formulas, missing C–H bonds, incorrect valency, ambiguous handwriting and poor image quality.
- [x] Define measurable acceptance thresholds and manual-review triggers before testing; record model/prompt/rubric versions and evaluate regressions before enabling each supported diagram type.
- [x] Keep automatic marking disabled for unsupported types or failed evaluation gates; release behind controlled configuration with monitoring and rollback.

## Completion criteria

Phase 1 is complete when Admin can approve exact scheme-answer crops, Students can see them only when permitted, and Q5(c)(ii) displays both correct structures with its marking requirements. Phase 2 is complete only when drawn submissions and evaluated scoring/manual-review paths work end to end. Keep this plan open or explicitly split/defer Phase 2 rather than marking unbuilt assessment work complete.


## Implementation evidence — 2026-10-29

- Additive migrations 0014/0015; no data reset. Dedicated scheme crops, per-subpart review manifests, frozen rubric answers, private post-submission image routes, drawing uploads and human review are implemented.
- Local automated checks: 215 backend tests passed, one skipped; 100 frontend tests passed; typecheck, lint and build passed. New integration test uploads/replaces a per-part drawing, submits, reveals the answer, queues manual review, and denies sibling access.
- Desktop/mobile Student browser checks verify the model-answer image and enlargement/keyboard dismissal. Production Admin verification passed after the saved-scheme preview correction; see release evidence below.
- Original scheme fixture SHA-256: `a3e855a616c73d1d3921ab8a7778853451edea2de4add40bdbb27f18efae2c98`, PDF page 8. Visually verified normalized crops: butane `(0.23, 0.661, 0.40, 0.742)`; methylpropane `(0.23, 0.749, 0.40, 0.852)`. Licensed source/images remain outside Git.
- Source block regions can initialize the crop editor; unknown layouts still require Admin crop selection. No inference is silently approved.
- Automatic diagram scoring is deliberately not enabled. Optional image-based proposals use original Student images plus approved scheme visuals, validated points and deterministic caps, and always require human approval. The expert-reviewed image corpus/live-model scientific evaluation remains outstanding in `backend/evaluations/drawings/README.md`; mocked and software tests do not complete that gate.

## Production verification — 2026-10-29

- Implementation `ee86ae9`, preview correction `0615e53`; both pushed and deployed. Production migrations are at `0015_drawing_submissions` with no schema drift.
- Release evidence: `/data/akuru/release-evidence/deployed-0615e53af9fae2ef8136d26e12aa005965b35975-20261029T144834Z.txt`. HTTPS, route fallback, headers, services, timers and loopback-binding acceptance checks passed.
- Authenticated API update attached both reviewed scheme crops to Q5(c)(ii), linked to M1/M2. Q5 revision advanced from 7 to 8; unrelated subparts were preserved. Question content remains `needs_correction`, c(ii) remains `unreviewed`, and drawing assessment is `manual_only`. This did not publish or approve the paper.
- Production crop pixels match the inspected source crops. Live authenticated Admin browser checks loaded both images at desktop/mobile sizes without JavaScript errors. The new assessment answer-image endpoint returns 401 without authentication. Local integration tests cover owner/submission/sibling restrictions; no artificial Student attempts were created in production.
- Local browser regression also verifies that previews and the crop editor use the saved workspace scheme rather than the unsaved companion selector. Student desktop/mobile answer enlargement and keyboard dismissal passed. Comprehensive screen-reader/manual end-to-end acceptance and the extended synthetic edge-case matrix remain open above.
- Temporary local test server was stopped. Unrelated local navigation/style edits were excluded from the release.
- Existing dependency audit follow-up: production `npm audit --omit=dev` reported 20 findings (1 critical, 10 high, 8 moderate, 1 low), including transitive `proxy-addr` GHSA-jqcg-44mw-7w3h. Dependencies were unchanged by this feature. Investigate runtime reachability and compatible updates separately; release health checks do not constitute a clean dependency-security audit.
