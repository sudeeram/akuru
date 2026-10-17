# June 2025 Chemistry standard-paper local draft bank

Scope: Pearson 4CH1 June 2025 `1C` and `2C` only. This is a **local review package**, not an AKURU import, publication or Student release. `1CR` and `2CR` remain outside the pilot.

## Reproduce locally

From the project root, using the backend virtual environment:

```sh
source-code/backend/.venv/bin/python source-code/scripts/pilot-pearson-chemistry.py 'pastpapers/igcse/chemistry/International GCSE-Chemistry (2017) (Current)-June 2025.pastpapers'
source-code/backend/.venv/bin/python source-code/scripts/build-pearson-chemistry-draft-bank.py 'pastpapers/igcse/chemistry/International GCSE-Chemistry (2017) (Current)-June 2025.pastpapers'
```

The builder verifies each of the six source PDF hashes against the pilot manifest and writes `.pilot-review/june-2025-standard-draft-bank.json` plus 35 rendered question-page and 20 marking-scheme-page PNGs under the ignored June 2025 source folder. Rerunning replaces the rendered images, so they correspond to the verified PDF bytes. The source folder and generated review package are ignored by Git; only the scripts and review documentation belong in the repository.

## Private production textbook comparison

Run `bash source-code/scripts/stage-pearson-chemistry-pilot.sh --dry-run '<absolute June 2025 source folder>'` first, then use `--execute` to stage the validated, unreleased 1C/2C draft bank on the production host. This is a one-time, non-overwriting operation. It places the JSON and rendered review images in `/data/akuru/pilots/pearson-chemistry-june-2025-standard` with access restricted to the `akuru` service account. It does not copy the Pearson source PDFs, modify the deployed code, create document/question rows, or expose the material through student APIs.

The staging command then runs `analyze-staged-pearson-chemistry.py` against **published** iGCSE Chemistry topics and active textbook retrieval chunks, using a read-only database transaction. The private `analysis-report.json` contains lexical evidence suggestions by subpart and textbook page. A suggestion is neither a verified syllabus mapping nor an approved question; every part remains `human_review_required` and question coverage remains `unverified`. Questions outside the two currently published topics may still receive incidental word-overlap candidates. Admin review of question wording, marking scheme, examiner guidance, topic mapping, and source pages is required before any official-material import or student use.

The first production comparison on 17 October 2026 analyzed 16 questions and 87 subparts against 2 published Chemistry topics and 94 active textbook chunks. It created zero mappings. A local copy of the resulting report is saved in the Git-ignored `.pilot-review/production-textbook-analysis.json` folder for review.

## What the package contains

- Exact paper key, component, standard variant, source PDF filenames and SHA-256 hashes for both papers.
- 16 top-level draft questions, 10 from `1C` and 6 from `2C`, totalling 180 marks.
- 87 labelled subpart candidates with reconciled marks. A label or mark mismatch causes the builder to stop.
- Full rendered source and marking-scheme pages for every question, preserving diagrams, tables, formulas, answer choices, graph axes, accepted alternatives and marking dependencies for review. These are local review assets, not approved UI assets or figure crops.
- Raw question and exact-scheme extraction, complete question/scheme PDF page ranges, and examiner-report heading candidate pages.

Every question has `studentPrompt: null`, empty approved `markingPoints`, `alternatives`, `approvedComments` and `topicMappings`, and `reviewStatus: not_approved_for_import_or_students`. The overall package has `studentAccess: false`. A candidate subpart's extracted text may include answer lines or PDF boilerplate. The scheme extraction may lose table layout, drawn chemical structures and dependencies. The heading pages are leads for reviewing examiner comments, not approved evidence.

## Before any AKURU import

1. Review each rendered question and write an accurate Student prompt, shared stem and subpart text. Associate the necessary figures, tables and diagrams with their questions.
2. Review every scheme entry against all its PDF pages. Encode exact marking points, alternatives, dependencies, calculation follow-through, accepted notation and maximum marks. Do not infer a rubric from numerical totals alone.
3. Link examiner comments to their actual question or subpart, excluding introductions and unrelated example pages.
4. Map each complete question to all required **published Chemistry topics**. A multi-topic question is ineligible if any required topic is uncovered for the Student.
5. Import into an isolated local AKURU environment through the reviewed document workflow, validate exact paper/scheme/report identity, and only then consider publication and local Student tests. The local database had no textbook, topic or document records at the time of this pilot, so this environment gate is still open.

The page-by-page visual findings are in `docs/pearson-chemistry-june-2025-question-review.md`. The package can be regenerated without putting licensed source PDFs or rendered pages into Git.
