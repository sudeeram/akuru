# Prepared screenshot textbook packages

Implemented locally: 2026-11-01. No migrations; uses existing document, extraction, source, visual and publication tables. Guideline: `guidelines/textbooks/igcse/README.md` at project root.

## Boundary

This is an operator-assisted import, not a new vision-model integration or an OCR replacement. A trusted operator prepares content from screenshots; an Admin validates/imports a ZIP as a **separate supporting draft**. It never changes the primary role, approves figures, publishes a topic or regenerates flashcards automatically. Published topic versions remain the student-facing source until the normal publication workflow explicitly replaces them.

## Portable format and tooling

Run from `source-code/backend` with the existing virtual environment:

```sh
.venv/bin/python scripts/package_prepared_textbook.py /absolute/path/to/prepared-folder /absolute/path/to/new-candidate.zip
```

The source folder needs `topic-package.json` in the pilot format. The tool copies only referenced PNG pages/crops, rewrites paths inside the ZIP and records the original manifest SHA256. Source references may resolve within the parent topic folder only. Output files are never overwritten. Keep licensed files and resulting archives in the ignored textbook directory.

Accepted ZIP: `topic-package.json` plus exactly referenced source PNGs and original-pixel crops. Limits: 50 MB compressed, 100 MB expanded, 2 MB manifest, 100 pages/20 million pixels per page and 60 million source pixels in total, 300 figures, 2,000 teaching blocks. No absolute/traversal paths, duplicate members, symlinks, encrypted files, HTML or scripts. Checks include hashes, image dimensions, crop bounds/pixel equality, IDs, source pages, table shape and exercise/figure/issue references. Printed labels in this v1 contract are unique positive numeric labels; roman/range labels require a future contract extension. Sources are never extracted to arbitrary filesystem paths or executed. The configured malware scanner is honoured on import.

## API and review

All routes are under `/api/v1/admin/textbooks/{book}/topics/{topic}/prepared-packages`:

- `POST /preview`: octet-stream ZIP; validates scope and returns inventory/decisions without writes.
- `POST /import`: octet-stream ZIP; validates again, stores private original and derived assets, creates a pending document/version/job and supporting source. Same exact archive in the same topic returns its existing import; cross-topic/removed duplicate conflicts. Topic row lock serialises sequence assignment. Storage writes are cleaned up if persistence fails.
- `GET /{document_uuid}/review`: exceptions, whole-document content hash, existing decisions and editable document URL.
- `POST /{document_uuid}/review`: explicit whole-document confirmation, current content hash and a non-empty resolution per exception. Stale content conflicts. Resolution notes are appended to affected teaching blocks, originals remain in metadata, page/block review is recorded as an audited batch and the existing final-document confirmation is used. Published documents are immutable.

All endpoints require Admin authentication; every POST also requires session CSRF protection. Binary request limits are integrated with the existing bounded-body middleware. Archive titles/course/subject must match destination scope. Codes and edition remain operator-checked metadata; original title/edition pages are not invented when missing.

Teaching kinds such as lists/procedures/safety notes map to paragraph blocks with explicit rendered items and original typed metadata retained. Tables get readable cell text plus structured original rows; exercises retain nested groups/context as source metadata with wording rendered in the question block. Figure references appear explicitly in teaching text so existing flashcard visual matching works. Crops are selected (not approved) with caption/alt-text candidates. No synthetic OCR accuracy is claimed: confidence is zero with `confidenceNotMeasured`, until audited review becomes the quality signal.

Existing block/page editors remain available. Whole-package approval is a deliberate alternative to saving every unmodified prepared block; it is not automatic. Publication additionally requires the prepared review and current final-document hash, so individually saving blocks cannot bypass the whole-package gate. Visual approval, primary selection, visual-reference page mapping, topic publication and retrieval preflight are still separate.

## Validation and limits

`tests/test_prepared_textbooks.py` tests archive rejection, authentication/CSRF, scope, duplicate import, draft isolation, whole-review/stale hash, selected/approved visual separation, publication, printed-page evidence and flashcard figure resolution. The private Topic 1 scenario runs when its ignored archive exists; CI uses the synthetic fixture. Integration tests use the existing transaction/rollback fixture, not production.

Local embedding preflight verifies authorised version-bound evidence, not educational correctness. No paid model request or production data changes are needed. Live tutor-answer quality, official specification alignment, owner review time and Topic 2 generalisation require separate evaluation. Existing flashcard cards are not regenerated by this importer.

### Local verification on 2026-11-01

Backend suite: 263 passed, 1 skipped. Frontend suite: 108 passed. Typecheck, lint, build and contract checks passed. Six local-embedding relevance probes plus flashcard matching/printed-page visual-reference checks passed on the private pilot in a rolled-back transaction. The browser acceptance test bundles the isolated component and mocks all APIs; it requires the existing Playwright module (`PLAYWRIGHT_MODULE` may point to it) and Chrome, and installs nothing. Run it with a supported Node release from the project root:

```sh
node source-code/frontend/tests/prepared-textbook-import-browser.mjs
```

The ordinary project Node scripts enforce the patched runtime policy. A compatible bundled Node 24.22.1 was used for this task; no local Node installation was changed.

## Optional live teaching evaluation

`python scripts/evaluate_prepared_tutor.py --help` documents the opt-in runner. Supply the private portable package, accepted-decision JSON, predeclared case JSON, ignored evaluation credential file, private output directory and persistent budget ledger. Without `--live`, the entire Tutor/import/publication pipeline uses a fake response and costs nothing. `--live --budget-usd 2` permits bounded generation only after the owner has authorised it. The runner rejects budgets above US$2, remote database hosts, a teacher model other than `gpt-6.1-sol`, reused backend/OpenClaw keys and overwriting prior result folders.

The process substitutes only Evaluation credentials, local embeddings and synthetic test accounts. It uses a unique schema translation map on localhost and drops that schema/storage afterwards. Whole-document/visual approvals in that disposable fixture do not constitute approval of the real document. The budget transport serialises access with a ledger lock, reserves conservative input/output bounds before dispatch, disables retries and preserves reservations on unknown usage. Keep the same ledger across live retests; do not delete it to reset spending. API-reported usage produces an estimate at recorded dated rates, not an authoritative invoice.

The November 1 pilot and improvements are recorded in `guidelines/textbooks/igcse/reviews/2026-11-01-chemistry-topic1-teaching-evaluation.md`. Actual licensed prompts, responses and readable report stay inside the ignored Topic 1 material folder. Current Tutor prompts are version 1.0.2; production release gates must be evaluated for that version before enabling it. The evidence-ranking score is not an extraction-accuracy or answer-confidence percentage.
