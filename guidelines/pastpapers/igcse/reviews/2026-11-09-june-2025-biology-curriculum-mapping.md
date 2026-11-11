# June 2025 Biology curriculum mapping

Started: 2026-11-08. Completed: 2026-11-09.

## Scope and method

Added AI-assisted curriculum decisions to the existing production June 2025 Biology standard **1B/2B** and regional **1BR/2BR** review workspaces. Compared each subpart's wording and marking requirements with all 22 current published Biology topic evidence sets. This is curriculum mapping, not a new extraction, source-confidence reassessment, human content approval or Student release.

The semantic decisions were prepared with Codex assistance in this conversation, without paid model API calls. An exact conversation model identifier is not asserted. Existing extraction/source-comparison provenance remains unchanged. These mappings are not new accuracy percentages.

Confirmed links use published, same-subject topic public references. Reasons distinguish the knowledge assessed from the question's novel application or supplied numerical data. Cross-topic prerequisites are linked where needed; shared passage keywords alone do not establish coverage. Optional marking alternatives are not automatically imposed as prerequisites for every valid answer.

No reconstructed textbook-PDF page numbers or unverified printed-page labels were added. Existing textbook-page evidence was preserved. Published evidence snapshots, explicit per-subpart decisions, before/after records, optimistic-revision receipts and verification results are retained under ignored `tmp/biology-june2025-curriculum/`; they are not committed textbook/source material or credentials.

## Production results

| Paper | Questions | Subparts | Supported | Partial or uncertain |
|---|---:|---:|---:|---:|
| 1B | 10 | 46 | 46 | 0 |
| 2B | 6 | 30 | 30 | 0 |
| 1BR | 10 | 49 | 49 | 0 |
| 2BR | 6 | 31 | 30 | 1 |
| **Total** | **32** | **156** | **155** | **1** |

Examples of subpart-specific decisions:

- 1B Q1: cell structures/respiration map to Topic 1, Euglena classification to Topic 2, and the movement explanation combines the relevant concepts.
- 1B Q4: phloem transport maps to Topic 11; pest-control questions map to Topic 15. Phloem feeding's effect on growth also requires Topic 1's respiration/protein-synthesis context.
- 2B Q1: homeostasis maps to Topic 8, reproductive hormones to Topic 9, antibiotic resistance to Topic 19, and the nitrate-removal application to Topics 14/15. The river passage is not mapped wholesale to circulation because of its metaphorical title.
- 2B Q5(c): transpiration and plant chemical coordination map to Topics 11/12. Preserve the question's ABA wording without teaching that abscisic acid is an auxin.
- 2BR Q5: the cloning procedure/data map to Topic 20, while the weakened-immune-system explanation maps to Topic 5.

**Uncertain:** 2BR Q1(c)(ii), sweet fruit and animal-mediated seed dispersal. Topic 13 is related, but the published content does not explicitly establish dispersal through fruit consumption and egestion. Saved as `partial_or_uncertain`, with no confirmed topic references and a specific reason. A related chapter title alone is insufficient evidence for confirmed support. Supplementary evidence or Admin adjudication is still needed.

## Approval and release boundaries

Reran the existing server AI-approval policy for all four papers. **No questions or subparts became AI-approved.** All 156 parts currently have page-level question/scheme sources but lack the exact paper and marking-scheme block references required for content approval. Some questions also retain proposed/unassigned visual candidates. Curriculum mapping does not resolve these independent gates.

Next work is exact question/scheme block association, visual acceptance and adjudication of previously recorded source conflicts. The uncertain seed-dispersal mapping also remains open. Do not approve proposed crops, alter confidence or claim Student readiness merely to obtain a higher approval count.

All 156 parts remain manual-only for scoring. Whole-paper readiness, assessment release and automatic-assessment readiness remain false for all four papers. Source-conflict warnings from the earlier standard/regional audits are preserved.

## Verification

- Authenticated, CSRF-protected Admin APIs only; no direct database updates.
- Verified all 12 production source checksums, all 32 optimistic question revisions and unchanged evidence for all 22 published topics before mutation.
- Read back every saved question. Only coverage status, confirmed topic references and coverage reasons changed; wording, marks, marking points, scheme/report associations, crops, scoring rules and original extraction-confidence metadata are unchanged.
- All 32 accuracy assessments remain current. Their IDs, versions, values, provenance and content hashes are unchanged: coverage-only fields are excluded from the source-comparison hash. No duplicate reassessment was created.
- Five protected workspaces (Chemistry 1C and January 2023 Biology standard/regional papers) remain unchanged.
- **41 existing local review/AI-approval/analysis/confidence tests passed**, with dependency deprecation warnings. The initial sandboxed run could not access local PostgreSQL; the rerun with local database access passed.
- No application deployment, migration, service restart or paid AI call was required. Unrelated local application changes were not deployed.

## Review links

- [June 2025 1B](https://akuru.magicalinternational.com/admin/exam-documents/review/8efd7e44-17f6-496f-9974-eb68e45a54ca)
- [June 2025 2B](https://akuru.magicalinternational.com/admin/exam-documents/review/8f5efb85-51ba-4f09-8003-ec3569f8f13d)
- [June 2025 1BR](https://akuru.magicalinternational.com/admin/exam-documents/review/99a01ebb-1f5f-4213-97f3-9e4d6773ac17)
- [June 2025 2BR](https://akuru.magicalinternational.com/admin/exam-documents/review/eea024fe-978f-4392-b330-c0011201cf63)

These are follow-up mappings for four already source-compared papers. They do not increase the collection's source-comparison count: **16 of 44** source-compared, **28 remaining**.
