# June 2025 Chemistry 1C accuracy assessment

Prepared: 2026-11-01

Completed and verified on production: 2026-11-01. Application release: `e4c264f`; migration: `0017_official_question_analyses`.

Scope: the current approved production 1C review, all 10 questions and 49 subparts. This assessment adds metadata only. It proposes no automatic edits, approval resets, marking-readiness changes or publication changes.

The original PDFs were downloaded through authenticated Admin APIs and matched against the local originals by SHA-256:

| Source | SHA-256 |
| --- | --- |
| Question paper | `d860cbae11a72b38853a3a5f3176845ee117a0b5a6a01b4bb766f7bb88bfb06f` |
| Marking scheme | `a3e855a616c73d1d3921ab8a7778853451edea2de4add40bdbb27f18efae2c98` |
| Examiner report | `c74f15906d09c17b8fe4cbe88083f1f0f157d91b40542c721b55dbcd0ed1cf31` |

Question pages, all relevant scheme rows and the complete native report commentary were compared with the saved wording, marks, rubric points/rules and report advice. All 17 distinct attached question/model-answer visuals were fetched and visually compared, alongside original source pages. Selected report example pages were visually inspected for continuation, printed commentary and handwriting context. This is not a claim to have produced complete literal transcripts of every handwritten candidate example.

Method: `source-comparison-v1`; prompt: `1c-source-comparison-v1`; guidelines: `akuru-igcse-pastpapers` 1.3.0. Assistance: Codex conversation. The exact current model ID is not exposed in this conversation and is recorded as **not recorded**. The model used for the original extraction is also unknown; the new assessment must not be represented as historical extraction provenance.

## Estimates

| Question | Accuracy confidence | Lowest-confidence part |
| --- | --- | --- |
| 1 | 80% | c |
| 2 | 92% | a |
| 3 | 92% | a |
| 4 | 78% | b(ii) |
| 5 | 82% | d |
| 6 | 82% | e(i) |
| 7 | 82% | b |
| 8 | 85% | a |
| 9 | 84% | b |
| 10 | 88% | b(i) |

These are subjective confidence estimates to prioritise source comparison, not measured accuracy rates. Question values follow their weakest subpart and source component. Manual-marking requirements alone do not reduce confidence in faithfully captured source material.

## Reasons to prioritise a further check

- Q1: answer leaders and table headings remain in neighbouring wording. The accepted element-symbol alternative is not explicit in the reviewed rubric fields.
- Q4(b)(ii): the main calculation is correct, but a specific partial-credit route and significant-figure allowance are not fully represented.
- Q5(d), Q6(e)(i) and Q8: positive scientific points are present; some conditional, alternative or ignored-response instructions remain less precise in the reviewed fields than in the original scheme. The linked original remains available.
- Q7(b): the reviewed advice focuses on insulation. The report also discusses a valid measuring-apparatus improvement that is missing from that summary.
- Several calculation/equation parts have the main answer correct while leaving an explicit accepted alternative or full-credit-without-working instruction only in the original source.

Per-subpart source pages, percentages and detailed reasons are retained in the private API analysis records. Licensed source PDFs, screenshots and the full prepared payload remain outside Git.

Deployment and metadata import must verify every saved question's content, revision, approval, reviewer and review timestamp against the pre-assessment baseline. The generic authenticated recording script performs those checks before and after the batch.

## Completion evidence

All 10 assessments were recorded through the authenticated, CSRF-protected Admin API. The before/after comparison confirmed that all 10 question approvals and all 49 subpart approvals remained in place and that reviewed content, revisions and reviewer metadata were identical. Repeating the dry-run recognised and skipped all 10 identical current assessments.

Verification passed: 237 backend tests (one unrelated skip), 106 frontend tests, TypeScript, targeted lint, generated-contract checks, schema consistency and production HTTPS/operations acceptance. Read-only production browser checks confirmed low-confidence sorting, Q4(b)(ii) selection, source/model provenance, immutable history access, model filtering, desktop/mobile rendering and no unsaved question changes. Private payloads, downloaded sources, screenshots and before/after evidence remain under ignored `tmp/` paths.
