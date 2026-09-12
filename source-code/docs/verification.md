# Local verification — 12 September 2026

## Step 0 foundation baseline

- Frontend contract tests: 6 passed.
- Backend unit and PostgreSQL integration tests: 9 passed with 2 upstream deprecation warnings.
- Alembic migration and schema-drift check: passed at revision `1077b2ef7586`; no new upgrade operations detected.
- Frontend TypeScript check, Oxlint and production build: passed.
- PostgreSQL backup/restore drill: passed. The restored copy contained the expected Alembic revision and 15 public tables, then the isolated drill database was removed.
- GitHub Actions now repeats frontend checks and backend checks against an isolated PostgreSQL service on every push and pull request.

Run the local quality gate from `source-code/` with `npm run verify`. Run `npm run database:restore-drill` separately when validating backup recoverability.

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

API integration tests invoke the request handler directly; browser checks exercise actual HTTP in the running app. Browser print/PDF output, real scanned-paper extraction, external AI services, generated media, production databases, internet deployment and a full cross-browser/accessibility audit have not been verified. The README describes the demo content and remaining backend integrations.
# Historical verification

The checks below describe the earlier four-subject demo before the Admin/iGCSE revision. Current role and curriculum requirements are in [architecture.md](architecture.md); current integration tests are in `../frontend/tests/api.test.mjs`.
