# AKURU source code

This repository separates `frontend/` and `backend/`. The working React portal and temporary Node mock API are in `frontend/`. The initial real FastAPI/PostgreSQL service is in `backend/` and will replace mock endpoints incrementally.

## Architecture references

- [Overall architecture](docs/architecture.md): roles, family ownership, iGCSE catalog, textbook-first ingestion, unit mappings and term-mock eligibility.
- [Frontend architecture](frontend/docs/architecture.md): screens, mock API, local storage, migration and API boundary.
- [Backend architecture](backend/docs/architecture.md): planned FastAPI modules, PostgreSQL constraints, document pipeline and immutable assessments.
- [User guides](../user-docs/README.txt): Admin, Parent and Student instructions.

## Run locally

From `source-code`:

```sh
npm run dev       # http://127.0.0.1:5180
npm run build
npm start         # compiled preview: http://127.0.0.1:5181
```

Use one mode at a time. Stop with Ctrl+C. The launcher selects an already installed Node >=22.13; it does not install software. Frontend dependencies were moved intact and no additional packages are required for this revision. `PORTAL_PORT` changes the built preview port. `PORTAL_DATA_DIR` selects a separate local data directory for isolated testing.

After completing the one-time Python setup in [backend/README.md](backend/README.md), `npm test` runs both frontend and backend tests. Use `npm run backend:dev` to start FastAPI locally on port 8000.

## Local accounts and setup

The existing demo login buttons remain. Admin login is `admin` / `admin123`; parent is `parent` / `parent123`; child demos are `alex` / `alex123`, `jamie` / `jamie123`, `sam` / `sam123`. These publicly documented accounts are local-only. Admin-created account passwords are stored as salted scrypt hashes in server-side local data and are not added to the demo buttons.

Admin must create each parent before creating linked children, then assign iGCSE, Grade 10 or Grade 11, one or more completed/current Grade + Term combinations, and selected subjects. Phase 1 subjects are English, Maths, ICT, Biology, Chemistry, Physics, French and Human Biology.

Admin uploads and approves textbooks, registers their units, sets term coverage, uploads same-subject past papers and related marking schemes/reports, manually enters and maps every question, then approves the complete paper. A student's mock includes a question only if every mapped unit is covered in the union of that student's saved Grade + Term progression. A Grade 10 Term2 student therefore receives eligible Grade 10 Term1 and Term2 questions. No coverage or no approved questions produces an empty state, never a full-syllabus fallback.

Parents now view courses/resources and review/assign work for their own children. They no longer manage accounts, enrolments or learning-document uploads. Students can still attach their own answer working; that does not create a learning document.

## Data migration

The existing private data directory moved to `frontend/.local-data/`. On first revised-server startup, the v2 migration saves a `state-before-v2-*.json` backup and retains prior work. Existing students require Admin confirmation of grade, term and subjects. Old demo questions are historical until properly re-entered/mapped. Old resource files remain available to Admin but need re-import with curriculum metadata. Old active exams are archived with saved answers.

Do not run an old server against the previous paths after moving the project. Restart using the new launcher when ready. Back up the complete private data directory while the server is stopped. It is excluded from Git.

## Verification

```sh
npm test
npm run typecheck
npm run lint
npm run build
```

The current integration tests use isolated temporary storage and validate authorization, family isolation, Phase 1 enrolments, document ordering, subject/unit integrity, publication gates, term filtering, private files and exam submission/timing. Historical verification notes under `docs/verification.md` describe the earlier demo, not current role permissions.

## Implementation limits

The FastAPI/PostgreSQL foundation is now present, while feature APIs, automatic PDF extraction, equation/diagram ingestion, AI tutoring/assessment, generated media and production authentication are not yet connected. The manual question editor establishes the curriculum constraints without pretending to extract PDF contents. The mock stores data in JSON and supports one process; it is not ready for public hosting.
