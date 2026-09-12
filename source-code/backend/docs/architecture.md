# AKURU FastAPI backend architecture

Status: initial implementation. This folder now contains the FastAPI application, SQLAlchemy domain tables, Alembic migration configuration, and local tests. The [overall architecture](../../docs/architecture.md) defines mandatory domain constraints and takes precedence over implementation choices here.

## Intended modules

```text
backend/
  app/
    main.py                       FastAPI application and middleware
    api/                          Versioned routers and request/response schemas
    identity/                     Accounts, password hashing, sessions and roles
    families/                     Parent-child ownership and enrolment periods
    curriculum/                   Courses, subjects, units, term coverage and eligibility
    documents/                    Upload authorization, versions, provenance and review
    questions/                    Question/subpart versions and unit mapping
    assessments/                  Paper assembly, exam snapshots, answers and reviews
    tutoring/                     Restricted retrieval and tutor/planner orchestration
    storage/                      PostgreSQL repositories and private object storage
    workers/                      OCR, extraction, embeddings and media jobs
  migrations/                     Versioned database migrations
  tests/                          Unit, API, database and end-to-end contract tests
  docs/architecture.md
```

These module paths are planned, not generated placeholders. Start with identity, family ownership and curriculum eligibility before adding AI calls.

## Infrastructure

FastAPI serves JSON endpoints; PostgreSQL stores authoritative relational state. pgvector indexes approved text/semantic representations alongside metadata. Private object storage holds original PDFs, page images, diagram crops, audio/video and answer attachments. A background job system processes long extraction/indexing tasks; Redis can supply the queue/session infrastructure if selected during implementation.

For OCI or home deployment, use an HTTPS reverse proxy, private database/object access, explicit secret configuration and backups. Providers and secrets remain backend-only. Hosting manifests, dependency versions and external provider choices are future implementation decisions, not requirements silently installed on the user's computer.

## Identity and permissions

Create Admin through an explicit bootstrap procedure outside ordinary account creation. Admin creates Parent and Student accounts. Each Student has exactly one Parent in Phase 1. Persist only strong salted password hashes or external identity IDs. Add first-login password change, reset/disable flows, session revocation and rate limits before public use.

The initial implementation uses Argon2 password hashes and random opaque sessions. Only token digests are persisted. HttpOnly, Secure-in-production, SameSite=Strict cookies carry session tokens; a separate same-site token plus request header protects mutations from CSRF. Login failure counters are persisted and updated under a PostgreSQL advisory transaction lock. `/health` is the sole constant public liveness route; login is necessarily public, and functional APIs resolve an active user from a non-expired, non-revoked session.

Centralize permission checks by action and resource. Parent queries must join authorized child IDs; do not fetch global student data and filter it only in the UI. Student writes derive their student ID from the session. Admin operations require the Admin role and record actor, target, timestamp and before/after audit context without credentials. Fetching files must apply the same ownership/document policy as fetching records.

## Relational constraints

- Course enum/catalog contains only iPrimary, iLower Secondary and iGCSE, with a Phase 1 activation gate permitting iGCSE only.
- Progression records capture every Grade 10/11 and Term 1/2/3 period reached by a student. One record is current. Adding a period must validate chronological continuity. Eligible coverage is the union of all recorded periods up to the current period, so Grade 10 Term 2 includes Grade 10 Terms 1 and 2. Historical periods remain immutable after use by assessments.
- Subject IDs are the eight explicit iGCSE subjects. Combined Science is not accepted.
- Student-to-parent foreign key must reference a Parent role; enforce role-sensitive links transactionally or using appropriate constrained identity tables.
- Document version includes course, subject, kind, object key, source metadata, checksum and review/publication state.
- Textbook unit belongs to a specific textbook version. Unique (textbook_version_id, unit_code).
- Past paper selects a same-course, same-subject approved textbook with units. Mark schemes and reports reference a same-course/subject/source-session paper.
- Question references its paper version and contains versioned text, marks, equations, assets, shared stems, subparts and marking annotations.
- QuestionUnit uses unique (question_version_id, unit_id). At least one valid unit is required at publication. Use composite foreign keys carrying subject/course/textbook identity where practical, plus transactional validation, to prohibit foreign-subject or foreign-edition mappings.
- Coverage rows are unique for a curriculum plan version, subject, grade, term and unit. A unit must be from an approved allowed textbook in that same subject/course.
- Exam items reference immutable question versions and store presentation/marking snapshots. Attempts and reviews keep student and exam/question provenance.

Plain foreign keys do not enforce multi-row requirements such as “at least one mapped unit” or “all questions approved.” Validate these inside a transaction when publishing and when generating exams; use database constraints/triggers where useful. Lock or use optimistic versions to prevent publication races.

## Document pipeline

1. Authorize Admin, validate catalog and prerequisite textbook before accepting a learning upload.
2. Store original bytes privately, calculate checksum, validate file format and size, create pending version and ingestion job.
3. Render PDF pages. Extract text, layout, equations and diagrams while retaining page numbers and bounding boxes. Keep original page crops as evidence when OCR is uncertain.
4. For textbooks, identify units/sections and propose a hierarchy. Admin confirms it before use as the unit vocabulary.
5. For past papers, detect question numbers, subparts, shared stems, mark totals and assets. Reconcile the question inventory against the complete source paper; never silently omit diagram-only questions.
6. Link marking schemes and examiner reports to the correct paper, question/subpart and page evidence. Missing mappings remain explicit review tasks.
7. Suggest question-to-unit mappings only within the selected same-subject textbook. LLM/vector suggestions are proposals; Admin approves final links.
8. Publish immutable reviewed versions atomically. Only approved published content can be indexed for student retrieval and considered for mocks.

Reference material supplements context and cannot replace a required textbook/unit mapping. The question bank contains full-syllabus source questions; term scope comes from coverage, not from tagging an entire past paper as a term paper.

## Deterministic eligibility service

One service owns candidate selection for mocks, practice, parent assignments, tutor retrieval and revision suggestions. Inputs are authenticated student, enrolled subject and current enrolment/plan version; clients do not supply trusted coverage or arbitrary accepted question IDs.

Equivalent query logic:

```sql
-- Schematic: schema names will be fixed when implementing migrations.
SELECT q.id
FROM published_question q
WHERE q.course_id = :student_course
  AND q.subject_id = :enrolled_subject
  AND q.paper_and_textbook_approved
  AND EXISTS (SELECT 1 FROM question_unit qu WHERE qu.question_id = q.id)
  AND NOT EXISTS (
    SELECT 1 FROM question_unit qu
    WHERE qu.question_id = q.id
      AND NOT EXISTS (
        SELECT 1 FROM term_coverage tc
        WHERE tc.unit_id = qu.unit_id
          AND tc.plan_version_id = :plan_version
          AND tc.subject_id = q.subject_id
          AND EXISTS (
            SELECT 1 FROM student_progression sp
            WHERE sp.student_id = :student_id
              AND sp.course_id = tc.course_id
              AND sp.grade = tc.grade
              AND sp.term = tc.term
          )
      )
  );
```

The NOT EXISTS condition ensures every mapped unit is covered. An any-match/overlap query is incorrect. Cumulative coverage comes only from the student's validated progression records. Missing coverage or insufficient eligible questions returns an actionable 409/domain error and never broadens the syllabus.

Document retrieval and vector ranking must use the same course/subject/unit filters. Full paper and solution files are Admin-only by default. Expose student-safe question crops and appropriate post-submission explanation excerpts instead of leaking an entire marking scheme.

## Mock assembly and assessment

Within the eligible pool, apply a paper blueprint for marks, time, skills and difficulty. Preserve mandatory stems/assets and dependencies when selecting subparts. For a multi-unit question, require all units even if only one unit has high semantic similarity.

Start an exam in a transaction: freeze enrolled grade/term, curriculum plan and coverage version, ordered question versions, source provenance, marking rubric, allowed aids and deadline. Curriculum changes affect new exams, not the existing snapshot. Use idempotency keys for creation/submission and validate answer ownership and deadline server-side.

Numeric validation should distinguish final-answer checks from method marking. Handwriting/OCR and rubric-based AI assessment remain provisional when uncertain. Parent review stays scoped to their own children, retains revisions and explains score changes. Scores on practice attempts are not predicted qualification grades.

Study plans aggregate each student's assessed history and covered units. Do not mix siblings' reviews or infer mastery from another child's data. AI tutor and media services can explain material only after eligibility/source authorization; they cannot change enrolments, publish documents or expand coverage.

## API and migration strategy

Use typed FastAPI request models, explicit response models and generated OpenAPI types. The frontend API wrapper is the integration seam, using the same-origin `/api/v1` prefix in development and production.

Before migration, freeze and back up local JSON and file bytes, map legacy identity/curriculum data explicitly, import with stable provenance and compare per-family counts. Preserve original backups. Unmapped legacy Science questions cannot be automatically assigned to Biology, Chemistry or Physics without review. Do not silently assign existing children to Grade 10/11 based on old school-year labels.

## Required verification

Use real PostgreSQL integration tests for transactions and constraints, plus HTTP tests for authentication and ownership. Cover all overall-architecture acceptance criteria, including foreign-family private file access; inactive courses; cross-subject and cross-textbook mappings; unmapped/partially reviewed questions; all-units filtering; empty pools; frozen exam versions; publication races; retry/idempotency; and complete preservation of equation/diagram source evidence.

The frontend's local tests are behavioral examples, not proof of production database or infrastructure correctness. Add a small reviewed corpus per subject and evaluate extraction/mapping/marking accuracy before allowing automatic publication or assessment.
