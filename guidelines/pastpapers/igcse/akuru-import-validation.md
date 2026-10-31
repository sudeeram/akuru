# Import, review and release validation

Standard: `akuru-igcse-pastpapers` 1.2.0

Last updated: 2026-10-31

Status: required checks; see the implementation plan for enforcement progress.

## Gate A: accept a draft batch

Reject invalid format, wrong source identity/hash, cross-paper references, inaccessible source versions, duplicate stable identifiers, malformed locations and unauthorised writes. Require an explicit unapproved state and record guideline/profile versions. Use authenticated Admin APIs when supported; never treat a guideline as permission to bypass validation with direct database edits.

Allow incomplete but structurally valid proposals to enter the review workspace with visible issues. Missing optional report material is not a draft-import blocker. Retries must be idempotent and must not overwrite reviewed content.

## Gate B: approve a question

| Check | Required handling |
| --- | --- |
| Labels, order, nested context or continuation uncertain | Block approval until resolved |
| Part marks and question total disagree | Block approval |
| Multiple-choice options incomplete, duplicated or misplaced | Block approval |
| Wording starts with answer-line debris or contains page furniture | Flag exact region; resolve before approval |
| Scheme linked but marking rules absent/incomplete | Block assessment approval |
| Rubric maximum exceeds allowed marks or required rule is unsupported | Block automatic-assessment release |
| Referenced scientific visual absent, clipped or unapproved | Block approval until reviewed/replaced or absence justified |
| Graph loses source-provided axis titles, units, ticks, grid extents or essential external labels | Reject that crop as complete; compare with full source page and widen/replace it |
| Table headings/units/cells are missing or misaligned | Preserve the source image and resolve the specific cell/heading issue before approval |
| Model-answer diagram missing or attached as a question illustration | Require the dedicated private answer visual and correct marking-point/subpart association |
| High extraction confidence but unresolved layout/symbol uncertainty | Retain a visible issue; confidence cannot override completeness checks |
| Handwriting/report association uncertain | Keep affected report item unapproved; do not make unsupported report content mandatory for question approval |
| Report missing or no comment found for a part | Record availability; do not fabricate a comment |
| Source version changed or concurrent review edited | Reject stale write and require reconciliation |

Warnings must identify the part and source region, not only display “review required”. Draft saves remain available even when approval is blocked. Approval must record an explicit reviewer decision. Linking existing exact evidence should not demand duplicate manual work, but ambiguous links must not be guessed.

## Gate C: Student release

Retain AKURU's separate paper/scheme completeness, publication, cumulative topic coverage and per-student access gates. A reviewed question does not automatically publish a paper or enter mocks. Never expose private marking rules or examiner examples through question payloads during a formal assessment.

## Re-analysis and reporting

Produce a validation report with source inventory, guideline version, counts of passed/warning/blocking checks, exact issues and any missing companions. Keep original extraction and reviewed versions. Show proposed differences before replacing Admin-reviewed content; preserve previous attempts and citations. A content-version change requires the appropriate review/release process.

Claim conformance only for checks actually executed. A successful upload, evidence link or 100% processing indicator is not proof of accurate interpretation.

## Required batch evidence

Complete [the extraction checklist](extraction-checklist.md) with each check recorded as passed, failed, not run or not applicable (with a reason). Include source/page/part references, missing companions, crop completeness, mark reconciliation, unresolved issues and proposed differences from existing reviewed content. Record supported scoring limits separately from content/visual approval. Screenshots or downloaded crops used for verification remain private where licensed content is involved.

For a correction through AKURU APIs, use authentication/CSRF and the latest expected revision, read the saved question back and compare only the intended changes. Do not approve a question/subpart, overwrite concurrent Admin edits or publish a paper as an incidental consequence of fixing a crop. Retain previous asset references in existing frozen snapshots.
