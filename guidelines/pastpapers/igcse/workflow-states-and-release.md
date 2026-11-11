# Workflow states, final assessment and Tutor release

Standard: `akuru-igcse-pastpapers` 1.5.0

Last updated: 2026-11-12

Status: implemented in production release `314d3e4`. Individual papers still require their recorded source/image/curriculum/scoring gates; deployment does not mark a paper complete. See the implementation plan and acceptance evidence for pilot results and remaining per-paper content work. This document does not itself authorise model spending or production data changes.

Implementation plan: [past-paper workflow and automatic Tutor release](../../../source-code/todo/completed/TODO-PAST-PAPER-WORKFLOW-AND-AUTO-TUTOR-RELEASE.md).

## Past-paper milestones

1. **Extracted:** available source content and exact associations are captured and expected question/subpart inventories reconcile. Processing completion alone does not establish accuracy.
2. **Images reviewed:** Admin has resolved required question/answer crops, labels and associations, including applicable scheme/report images. No relevant images means complete with an explicit Not applicable reason.
3. **Assessed:** final saved wording, marking points/rules, exact source evidence, reviewed visuals and curriculum mappings have current assessments. AI approves eligible items strictly above 75%; items at or below 75% and explicit blockers require manual resolution. A completed model call alone does not complete this milestone.
4. **Tutor practice released:** eligible approved, self-contained items are automatically released under the server policy. None released is grey; partial release or blockers is amber; all required items currently released is green. Retain required/released/excluded counts and reasons; never hide missing inventory or silently reduce the denominator to obtain green. Complete-exam publication remains separate.

High confidence is an estimated judgement, not calibrated correctness or permission to bypass gates. Exact evidence, image approval, supported curriculum and supported scoring requirements must pass independently. Curriculum matching uses authorised published topics of the same subject/course/specification, exact textbook evidence and publication versions; its confidence is separate from extraction accuracy. Preserve uncertain and outside-current-coverage outcomes rather than force a match.

Admin image review is required; duplicate manual approval of every high-confidence wording/marking item is not. AI approvals must record policy/model provenance, assessment version, content/source fingerprints and reasons. Preserve human decisions, explicit withdrawals and frozen attempts. Partial release must include all required shared context without leaking sibling answers; do not simply bypass parent-question guards.

## Companion-source milestones and transitions

Show three independent labels, not one replacing the previous label. Initially each is **grey — Not started** if no corresponding work has occurred. Existing documents derive states from recorded work; do not reset them.

| Milestone | Marking scheme | Examiner report |
| --- | --- | --- |
| 1 · Extracted | Complete extraction captures available pages, marking points and relevant diagrams. | Complete extraction captures available pages, commentary and examples. |
| 2 · Linked to paper | Verified association to the correct session, subject and paper code. | Verified association to the correct session and applicable paper or papers. |
| 3 · Evidence checked / Guidance checked | Final reassessment verifies exact evidence against extracted answers, marking rules and allocations for the applicable scope. | Final reassessment verifies commentary associations and interpretation for the applicable scope. |

Use grey for not started, blue for active work, amber for partial/uncertain/blocked and green for complete. Include text, scoped counts, details and action links; failures remain explicit. Associations can exist before extraction completes. Upload starts extraction blue; successful complete extraction makes label 1 green; matching the source makes label 2 green; final checks make label 3 green only when the applicable scope is complete.

Extraction complete is not accuracy approval. Derive milestones from source checks and question associations; do not require duplicate manual document approval. A report covering several papers needs per-paper summaries, not a document-wide green based on one question. Distinguish missing reports, unchecked available material and verified no-applicable-comment outcomes. An optional absent report is not equivalent to missing essential scheme evidence. The scheme remains authoritative for scoring; report examples/advice cannot silently override it.

## Invalidation and verification

Material changes to wording, rubric, source versions/links, visual crop bytes/labels/associations or curriculum evidence must invalidate affected checks. Recompute affected milestones; retain previous assessments/history rather than rebind old scores to changed content. New textbook publications require checking referenced mapping versions, not silently changing stable printed-page evidence. Unrelated changes must not invalidate the whole collection unnecessarily.

Reassess the latest saved revision after manual image review, then run guarded approval and release only in an explicitly authorised workflow. Assessment-only/provenance-only actions must not incidentally approve or release content. Audit automatic transitions and use idempotent, revision-protected writes. Student access still requires enrolment, cumulative topic coverage and authorised reveal rules. Formal assessments must not expose private answers or examiner examples.

Verify initial and independent milestone transitions, partial/stale states, source conflicts, exactly 75% versus above 75%, image and scoring blockers, multiple-paper reports, no applicable commentary, exclusions, concurrent edits, withdrawals and Student access. Record executed checks rather than claiming planned automation ran.
