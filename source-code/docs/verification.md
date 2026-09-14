# Local verification — 12 September 2026

## Step 0 foundation baseline

- Frontend contract tests: 6 passed.
- Backend unit and PostgreSQL integration tests: 14 passed with 2 upstream deprecation warnings.
- Alembic migration and schema-drift check: passed at revision `521493ec5f1f`; no new upgrade operations detected.
- Frontend TypeScript check, Oxlint and production build: passed.
- PostgreSQL backup/restore drill: passed. The restored copy contained the expected Alembic revision and 15 public tables, then the isolated drill database was removed.
- GitHub Actions now repeats frontend checks and backend checks against an isolated PostgreSQL service on every push and pull request.

## Step 1 backend-boundary verification

- Existing authentication, CSRF, first-login password changes, Admin account management, family isolation and cumulative progression requests pass through the new versioned routers.
- HTTP routers contain transport concerns, services contain validation and transactions, and repositories contain SQLAlchemy access.
- Admin role gates and student submission ownership live in the central permission module.
- Validation, domain, permission and unexpected processing failures use the documented structured error envelope.
- `npm run contract:check` confirms that the committed OpenAPI document and TypeScript contract match FastAPI.

## Step 2 private-document verification

- Local object storage round-trips exact bytes and rejects keys that escape its configured private root.
- The dependency-free OCI adapter contract is tested with an injected OCI-compatible client; the separately declared OCI SDK is needed only when deploying that adapter.
- PostgreSQL contains logical document, immutable version, derived asset and append-only event tables at Alembic revision `521493ec5f1f`.
- Admin upload validates PDF/image extension, media type, binary signature and size, records SHA-256 provenance, and rejects exact duplicates with a specific error.
- Past-paper ingestion fails closed until a same-course, same-subject textbook exists. Marking schemes and examiner reports require a related same-scope paper.
- Original downloads are byte-for-byte identical, use private no-store responses and reject Parent access. Retry and soft-removal actions create document events.
- A post-migration backup restored successfully at revision `521493ec5f1f` with 18 public tables; the isolated restore database was removed.

## Step 3 asynchronous-processing verification

- A real local Redis instance passed an isolated job-ID enqueue/dequeue round trip; the temporary test list was removed afterwards.
- Upload integration verifies prompt queued responses, structured job status, failed-only retry, progress, useful error fields and Admin authorization.
- Worker integration verifies PostgreSQL claiming, isolated preflight, page counting, transition to `needs_review`, and reuse of a completed stage without increasing the attempt count.
- Queue unit tests cover unavailable/invalid messages, unknown PDF page counts and configured page-limit rejection.
- `npm run verify` passed: 7 frontend tests, 19 backend tests, generated-contract check, TypeScript, Oxlint and the production frontend build. The backend suite retains 2 upstream Starlette/httpx deprecation warnings.
- Alembic is at revision `73eec4d0d322`; the schema-drift check found no pending model changes.
- A post-migration backup restored successfully at revision `73eec4d0d322` with 20 public tables; the isolated restore database was removed.

## Step 4 deterministic-extraction verification

- Generated fixtures cover Maths equations, Biology text and raster diagrams, ICT, English, French, standalone images, scanned PDF OCR and vector-only diagrams without including copyrighted Pearson material.
- PyMuPDF renders each page and stores native text coordinates; Tesseract OCR is exercised locally for scan/image paths with English and French language data. Missing requested language data still produces an explicit review flag.
- Equation candidates retain deterministic LaTeX and source crops. Embedded image bytes, rendered diagram crops, vector drawing crops and full page renders remain in private storage.
- PostgreSQL enforces same-document-version relationships between pages, blocks and their source/render assets. Worker integration verifies persistence and idempotent reuse.
- Authenticated API integration verifies Admin extraction metadata and private page-image retrieval, plus Parent denial.
- `npm run verify` passed: 8 frontend tests, 29 backend tests, generated-contract check, TypeScript, Oxlint and the production frontend build. Reported warnings come from upstream PyMuPDF SWIG and Starlette/httpx compatibility layers.
- Alembic is at revision `37308ed3ea42`; the schema-drift check found no pending model changes.
- A post-migration backup restored successfully at revision `37308ed3ea42` with 22 public tables; the isolated restore database was removed.

Run the local quality gate from `source-code/` with `npm run verify`. Run `npm run database:restore-drill` separately when validating backup recoverability.

## Step 19 evaluation-gate verification

- Synthetic tests cover all twelve evaluation metrics, complete-category corpus approval, Admin-only mutations, same-subject release binding, and rejection of a passing run from another subject.
- Assessment integration verifies that automatic publication requires the exact evaluated model and prompt version. Missing, failed, stale or low-confidence releases fail closed to `needs_review`.
- `npm run verify` passed with 22 frontend tests and 73 backend tests, plus generated-contract checking, type checking, linting and a production build. Alembic reported no model/schema drift at revision `e19a72c34b91`.
- Synthetic fixtures validate the gate mechanics only. Production educational quality requires Admin-approved, licensed corpora for all eight Phase 1 subjects before automatic releases are activated.

## Automated checks

- `npm test`: 13 integration tests passed against the actual local API handler with isolated temporary storage. Covers authentication, student isolation, independent grades/enrolments, answer-key withholding, marking/review permissions, review audit history, file access and approval, assignments, private drafts, study plans, exam restrictions/deadlines/idempotent submission, request methods, origin/host checks and logout.
- `npm run typecheck`: passed.
- `npm run lint`: passed.
- `npm run build`: passed with the installed Node 23.11.1 runtime.
- Dependency installation audit: zero reported vulnerabilities after compatible package updates.

## Browser checks

Verified the development portal and then the compiled portal at `http://127.0.0.1:5181/` using the in-app browser.

- Student and parent sign-in/sign-out.
- Alex: Maths hint and correct answer returned 2/2; Science lesson and particle animation worked; a written answer and private draft were saved; written work entered review.
- Parent: reviewed Alex's Science response with marks and feedback; changed Jamie to Year 6 and Mathematics to iLower Secondary while keeping other subject enrolments independent; uploaded a synthetic PNG and saved manual review notes; assigned a fractions task to Jamie.
- Jamie: displayed the changed grade/course settings and no Alex attempts in personal progress.
- Sam on the compiled build: started a 15-minute Maths mock, saved answers, navigated all three diagram questions and submitted with a final unsaved answer. All three answers appeared in personal progress, totalling 5/5.
- Sam: generated four subject revision suggestions from personal history.
- Mobile viewport 390 × 844: dashboard visually inspected, page width matched viewport (no horizontal overflow), sidebar opened and closed when selecting a destination. Viewport override reset afterwards.
- Desktop dashboard visually inspected at 1440 × 1000.
- Read-only WebMCP progress summary worked for the signed-in student and rejected another student's ID.

The preview retains synthetic QA records for inspection. No real textbooks or exam papers were supplied. The uploaded PNG remains pending, not approved as teaching material.

## Limits of these checks

API integration tests invoke the request handler directly; browser checks exercise actual HTTP in the running app. Step 18 tests verify deterministic SVG/plot generation, private media storage and authorization, simulated image-provider output, review publication and provenance. They do not make paid external AI calls. Browser print/PDF output, real scanned-paper extraction, production databases, internet deployment and a full cross-browser/accessibility audit have not been verified. The README describes the remaining deployment work.
# Historical verification

The checks below describe the earlier four-subject demo before the Admin/iGCSE revision. Current role and curriculum requirements are in [architecture.md](architecture.md); current integration tests are in `../frontend/tests/api.test.mjs`.
