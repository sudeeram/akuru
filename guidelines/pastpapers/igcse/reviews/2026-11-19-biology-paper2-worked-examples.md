# Biology Paper 2 — final drawing examples and Tutor release

Started: 2026-11-19  
Completed: 2026-11-19  
Scope: the three remaining drawing-answer gaps in the supplied Biology 2B/2BR batch.

## Production outcome

All **22 papers, 141 questions and 692 subparts** now have complete four-step workflow state and **692 current Tutor-practice releases**. The three additions complete the previously recorded 689 releases. No formal-exam publication, paid model calls, source-PDF replacements, Student-record changes or Chemistry changes were made.

| Paper / Admin review | Completed example | Current releases |
| --- | --- | ---: |
| [January 2023 2B Q3(b)(ii)](https://akuru.magicalinternational.com/admin/exam-documents/review/e4643895-278b-4018-b8fa-e837dcc3cd0f?record=%223%22&section=b%28ii%29) | Codominant roan cross, gametes, Punnett square and separate male probability | 31/31 |
| [January 2021 2BR Q2(b)(ii)](https://akuru.magicalinternational.com/admin/exam-documents/review/cef70f70-b102-4c5a-a8ba-295621719315?record=%222%22&section=b%28ii%29) | Labelled bubble potometer; water uptake distinguished from direct transpiration | 35/35 |
| [November 2020 2B Q2(a)(ii)](https://akuru.magicalinternational.com/admin/exam-documents/review/a2620c45-0a45-4b16-a03f-e19301f79abb?record=%222%22&section=a%28ii%29) | Qualitative time-to-clot curve, minimum at the question's 37°C optimum | 30/30 |

Each example retains a permanent **AI-generated worked answer — not an official Pearson answer** label, accessible explanation and limitations. Example confidence is 90%, explicitly an uncalibrated estimate. Following original-source and rendered-image comparison, the three affected source findings were updated from 65% to 85%; this is source interpretation confidence, not a claim of exact drawing-marking reliability. Existing extraction history remains intact.

## Method and safeguards

- Added strictly typed, bounded science templates and trusted PNG rendering; arbitrary coordinates, executable code, external media and fabricated measured data remain unsupported. The source JSON storage requires no migration.
- Visually compared the original question and scheme pages, then inspected local and production previews.
- Used authenticated, CSRF-protected Admin import, separate scientific approval/attachment, prepared correction, final source-analysis, source-issue-resolution, guarded AI-approval and per-subpart Tutor-release APIs. No direct database updates or model-generation jobs.
- Review notes explicitly identify the delegated Codex review. No owner/human scientific sign-off is claimed. The existing Admin approval lifecycle and normal release gates were used without bypasses.
- Restricted the bubble diagram to P1–P5, leaving the alternative mass-potometer criteria and four-mark maximum unchanged. Original marks, alternatives, source links, curriculum bindings, question images and answer grids were preserved.
- Verified unchanged sibling parts/questions and preservation of every previously current release in the three papers. All papers retain their 70-mark allocation. The batch workflow API confirms all four stages complete for all 22 papers, with formal-exam publication false.
- Existing Admin UI preview was checked in the browser: approved example, attached image, AI label and confidence/limitations are visible. This was not a paid Student chat/marking evaluation.

## Code and verification

Runtime release: `3842bd64da742e79536e8137eb3b458838c0496c`, pushed to `codex/biology-tutor-rollout` and deployed after an encrypted database/document backup.

- Worked-answer/schema/render/lifecycle suite: **31 passed**.
- Science diagrams, whole-question Tutor release and paper-workflow suite: **46 passed** (overlapping suites; counts are not additive).
- Frontend typecheck and generated API contract freshness passed.
- Production build, schema-drift check, service health, HTTPS/security headers, route/fallback and binding acceptance passed. No migration was needed.
- Authenticated per-paper readbacks and final 22-paper workflow acceptance passed; three scoped additions, 692/692 current Tutor releases, zero paid calls.

Deployment evidence: `/data/akuru/release-evidence/deployed-3842bd64da742e79536e8137eb3b458838c0496c-20261119T171521Z.txt`.

Private source pages, diagrams, request/response receipts and machine-readable acceptance are retained under ignored `tmp/biology-worked-examples/`; licensed source PDFs and extracted full text are not committed.

The separate planned hardening of empty source-issue IDs remains outside this delivery, as do Paper 1 review batches and formal-exam publication.
