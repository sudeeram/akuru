# Reproducible Biology official-paper draft intake

Started: 2026-11-04. This pipeline creates **unpublished Admin review drafts**, not approved papers or automatically markable Student material.

## Local build

Use the existing backend environment; no new system packages or paid AI calls are required:

```sh
source-code/backend/.venv/bin/python source-code/scripts/build-pearson-intake.py pastpapers/igcse/biology
source-code/backend/.venv/bin/python source-code/scripts/import-pearson-intake.py pastpapers/igcse/biology
```

The second command is a hash-validated dry run. `--paper-key 4BI1-2017-2025-JUNE-1B` (repeatable) selects a batch. All licensed data, full source transcriptions, manifests, visual evidence and receipts stay under the ignored source root's `.akuru-intake` directory. The separately downloaded specification is excluded from exam-component parsing and handled as a versioned reference document.

## Authenticated draft upload

Store `AKURU_ADMIN_USERNAME` and `AKURU_ADMIN_PASSWORD` in an ignored file with mode 0600. Do not put credentials in CLI arguments, Git or reports.

```sh
source-code/backend/.venv/bin/python source-code/scripts/import-pearson-intake.py pastpapers/igcse/biology \
  --paper-key 4BI1-2017-2025-JUNE-1B \
  --origin https://akuru.magicalinternational.com \
  --credentials tmp/akuru-admin.env --suggest-topics --execute
```

Uploads, exact companion associations, processing jobs, workspace creation, proposal seeding, draft enrichment, visual generation and extraction-analysis records all use the normal authenticated Admin API with CSRF. No database write bypass is used. Source checksums and version IDs are checkpointed in a private receipt. Existing checksum matches must also match subject, kind, component, year and source paper; another review workspace is never silently adopted.

The importer waits for processing, preserves source identity conflicts, excludes provisional schemes from active pairing and permits absent reports. It never marks source blocks reviewed, approves a question/crop, publishes a document or releases a Student assessment. The initially disputed January 2020 report is now paired through a reviewed, three-hash identity exception: all six question contexts match 2BR despite the 2B cover misprint. Final June 2021 schemes are used without fabricated reports.

A saved question's revision is checkpointed. Pending writes are journalled before sending; an interrupted response is reconciled by read-back rather than blindly repeating a write. Automatic evidence-block enrichment is allowed in that comparison, while substantive draft changes and unexpected revisions stop the importer. Visual candidate generation's own revision changes are also reconciled. `--refresh-generated` may refresh only importer-owned, still-unreviewed revisions; it is not an override for Admin edits. If an interrupted first seed cannot be reconciled against its journal and source-bound bank, stop for explicit recovery.

## Chemistry lessons carried forward

- Split subparts at source labels/layout boundaries, not mark lines. Preserve options after the allocation and parent context across pages; distinguish repeated continuation question numbers from new questions.
- Exclude page furniture and standalone answer dots, but retain embedded cloze blanks and intentional source grids/tables. Infer a whole-question mark allocation only from its explicit source total.
- Keep exact question/scheme/report versions separate; never substitute another variant. Preserve original page coordinates and source renders.
- Separate scheme answer cells from guidance using table geometry. Proposed source bullets and MC correct-option text are private, editable proposals. Distractor explanations are not accepted answers. Dependencies, caps, exclusions and combined-response semantics are not inferred into executable rules: automatic readiness stays off.
- Keep report headings/source pages as leads. Handwritten candidates and their errors require source comparison; they are not automatically converted to examiner advice or trusted answers.
- Generate focused question visual candidates with existing label-expansion heuristics. Source-only label descriptions are prefilled and remain unapproved. Admin must check complete external labels, graph axes/units/scales, crop completeness and correct shared/subpart scope.
- Drawing/plotting tasks are proposed as drawing responses and remain manual-only. Scheme answer visuals and any optional AI worked solutions have separate private review gates.
- Topic hints require multiple discriminative terms in published same-subject textbook evidence. They are shown in coverage reasons; confirmed topic links remain empty until Admin review. No mutable reflow page numbers are invented.
- Append current **extraction triage** provenance after enrichment/crop changes. Keep semantic source checks `not_checked` and absent reports `not_available`; percentages are capped at 70 and are not measured semantic accuracy. Old analysis records remain retained. No AI model is claimed when native parsing was used.

## Admin handoff

Go to `/admin/exam-documents`, select Biology, and open **Review questions**. Each receipt also records the direct `/admin/exam-documents/review/{paper-id}` link. Review wording, shared context, part marks, exact scheme proposals/guidance, report examples, visual crops, topic coverage and assessment readiness. The dedicated accuracy view shows triage/provenance; a separate source comparison is still needed for a semantic accuracy estimate.

Content approval, scoring readiness, complete-original-paper publication, coverage-filtered mock eligibility and individual Tutor-chat releases are separate gates. The initial bulk pipeline intentionally does not complete those human acceptance decisions. Never present an unapproved draft as a completed original paper.

## Validation and limitations

Synthetic tests cover B/BR timing, native layout/MC boundaries, nested context, page furniture, source aliases/conflicts, provisional schemes, source-hash guards, source-only descriptions, source point transcriptions, conservative topic hints and drawing detection. Existing Chemistry tests remain in the full backend suite.

Native layout heuristics do not prove all semantic relationships. Broad report heading ranges, missing/merged scheme rows, photographs, source typos, conditional scoring and difficult table continuation require Admin review. Record issues at their source locations. A low-confidence draft is useful review input, not a release failure that can be solved by increasing its percentage.

Related: [intake assessment](biology-pastpaper-intake-assessment.md), [delivery plan](../todo/ongoing/TODO-PEARSON-BIOLOGY-PAST-PAPERS.md), [shared conformance backlog](../todo/planned/TODO-IGCSE-PASTPAPER-ANALYSIS.md).


## Bulk intake refinement (2026-11-04)

Native extractor `pearson-native-layout-v1.1` also normalises the older private-font bullet glyph and handles correct MC answers without parentheses. The rebuilt corpus has 4,726 source point proposals. This improves transcription coverage, not semantic approval.

`reviewProposalVersion: 1` is an additive, private seeding format. It accepts only bounded marking-point proposals, response type, coverage reason and scoring-review notes; the server binds all paper/scheme/report page assets to the workspace's exact versions. Status remains unreviewed, confirmed topic links stay empty, and readiness is forced to manual-only. Invalid versions and attempts to import approval/automatic-readiness fields are rejected. The client validates the returned fields and source pages before checkpointing a fully populated seed. This avoids downloading every extraction page and resaving every question individually for new workspaces. Legacy banks retain their existing behaviour and the client can fall back to ordinary per-question enrichment.

Read-only requests retry bounded transient failures. Mutations are not blindly retried. A local exclusive lock prevents simultaneous imports using the same source root, and checkpoints always have mode 0600. Neither retry handling nor bulk seeding changes publication gates.

Identity exceptions are registered in `scripts/pearson-identity-overrides.json` and apply only to the exact question/scheme/report triplet. The January 2020 review also supplies page associations for the final discussion without a conventional question heading. The original cover is never edited. See [the source comparison](../../guidelines/pastpapers/igcse/reviews/2026-11-04-biology-january-2020-2br-report-identity.md).
