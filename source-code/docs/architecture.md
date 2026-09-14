# AKURU overall architecture

Status: authoritative Phase 1 domain specification, with the frontend connected to a FastAPI/PostgreSQL identity, account and enrolment foundation. This document supersedes the earlier parent-managed, mixed-qualification demo design. Implementation details belong in [frontend architecture](../frontend/docs/architecture.md) and [backend architecture](../backend/docs/architecture.md).

## Repository boundaries

One repository contains two application folders. No additional repository is required.

```text
source-code/
  docs/architecture.md           Shared domain rules and system boundaries
  frontend/                     React/TypeScript application
    app/                        Portal shell and role navigation
    features/                   Admin, Parent and Student screens
    lib/api.ts                  Frontend API boundary
    tests/                      Frontend boundary tests
    docs/architecture.md        Frontend implementation and API contract
  backend/
    docs/architecture.md        FastAPI design and implementation requirements
    README.md                   Backend setup, authentication and deployment notes
  scripts/run-web.mjs           Existing local frontend launcher
```

The browser uses same-origin `/api/v1/*` routes. Vite proxies that prefix to FastAPI during development; the production reverse proxy owns the same route. The frontend must never hold provider API keys or implement authoritative permissions.

## System layout

```mermaid
flowchart TD
    A[Admin portal] --> F[Frontend API client]
    P[Parent portal] --> F
    S[Student portal] --> F
    F --> API[FastAPI: identity, permissions and domain services]
    API --> DB[(PostgreSQL + pgvector)]
    API --> OBJ[Private object storage]
    API --> JOB[Document and media job queue]
    JOB --> OCR[PDF pages, OCR, equations and diagrams]
    OCR --> REVIEW[Admin review and unit mapping]
    REVIEW --> DB
    API --> ELIG[Deterministic curriculum eligibility]
    ELIG --> TUTOR[Tutor, assessment and study planning]
```

FastAPI authentication, account administration, document processing, approved retrieval, deterministic eligibility, immutable assessment delivery, AI assessment and explainable unit mastery are implemented. Weakness diagnosis and adaptive study planning continue in later roadmap steps.

## Roles and family ownership

| Action | Admin | Parent | Student |
| --- | --- | --- | --- |
| Create parent accounts | Yes | No | No |
| Create child accounts and link to a parent | Yes | No | No |
| Assign course, grade, term and subjects | Yes | No | No |
| Upload and approve learning documents | Yes | No | No |
| Define textbook units and term coverage | Yes | No | No |
| Map and approve paper questions | Yes | No | No |
| View student records | All, audited in production | Own children only | Own records only |
| Review answers and create practice assignments | Administrative access as required in production | Own children only | No |
| Submit practice/exams | No | No | Own account only |
| Upload answer working | No learning-work impersonation | No | Own submission attachments only |

A parent has zero or more children. Each child belongs to exactly one parent account in Phase 1. Multi-guardian access is a future explicit schema change, not implied by the Parent role. An Admin must create the parent first. Parent role alone does not grant access to every family.

Admin-created usernames must be unique. Password hashes belong to server storage. A child's client-supplied `studentId` or `parentId` never grants ownership. Every read, mutation, attachment retrieval, review and report checks the authenticated actor. If an Admin changes a child's parent, access follows the current parent relationship; historical actor/audit information remains. Family/enrolment changes are blocked during an active mock in the local implementation.

## Course and enrolment catalog

There are exactly three course identifiers: `iPrimary`, `iLower Secondary`, `iGCSE`. Only `iGCSE` is active in Phase 1. Other course names remain in the catalog for future implementation; Phase 1 enrolment and ingestion reject them rather than silently converting them.

iGCSE supports exactly:

- Grades: `Grade 10`, `Grade 11`.
- Terms within each grade: `Term1`, `Term2`, `Term3`.
- Subjects: English, Maths, ICT, Biology, Chemistry, Physics, French, Human Biology.

Biology, Chemistry, Physics and Human Biology are separate subjects. There is no combined `Science` subject in this Phase 1 catalog. Example references to a science paper mean a paper within its specific science subject; they never authorize cross-subject unit relationships.

A student has one active course, one current grade, one current term and one or more enrolled subjects. The student also has an ordered progression list of Grade + Term combinations already reached. For example, Grade 10 Term2 stores both Grade 10 Term1 and Grade 10 Term2. The phase-one course applies to every selected subject. The old feature allowing arbitrary qualifications per subject is superseded. Keep syllabus/specification and textbook edition identities in the production curriculum model so two specifications or editions are not accidentally mixed.

PostgreSQL stores the current enrolment and progression history. Each practice session, official paper and mock now captures the accumulated scope in an immutable assessment snapshot. Advancement is an Admin action; no automatic promotion is assumed.

## Textbooks, units and coverage

A textbook belongs to one course and one subject, with an edition/version identity in the production schema. A unit belongs to exactly one textbook. Its subject and course are inherited from that textbook. Unit codes are unique within a textbook, not globally.

Admin assigns every approved unit to the Grade + Term where it is first taught inside a versioned curriculum plan. A draft may be edited; publication makes the version immutable and supersedes the prior publication for that subject. Phase 1 uses the current published iGCSE plan shared by enrolled students. A future school-specific plan can add explicit student plan assignment without changing historical assessment snapshots.

Coverage is defined per Grade + Term, and student eligibility is cumulative across the student's saved progression list. For example, Grade 10 Term2 includes the union of Grade 10 Term1 and Grade 10 Term2 coverage. Grade 11 includes Grade 10 only when those Grade 10 periods exist in that student's progression. Every reached period requires an explicit assignment and missing coverage fails closed. An empty union means no eligible questions. There is no fallback to the entire syllabus.

Each past paper must associate with one approved textbook that provides its mapping vocabulary. Each question may map to multiple units within that textbook. Future versions may support curated equivalences across editions, but must never equate units solely by number or title.

## Document ingestion and publishing

Supported learning document types are `Textbook`, `Past paper`, `Marking scheme`, `Examiner report`, `Reference material`. Only Admin can upload them. Student answer attachments are a separate permission and do not become learning documents.

Required workflow:

1. Admin selects iGCSE and the subject, uploads the textbook and verifies its identity/edition.
2. Admin reviews the textbook and records its units. With OCR later, extracted unit proposals remain untrusted until reviewed.
3. Admin assigns the units covered in each grade and term.
4. Only after an approved same-subject textbook with registered units exists may Admin upload a past paper. Upload validates this server-side.
5. Admin uploads the matching marking scheme and examiner report linked to that past paper in the same subject/course. In production also validate session, year, paper/component, variant and specification.
6. Every question or independently usable subpart is entered/extracted with question number, marks, prompt, equations, diagrams and source page references. A subpart requiring a common stem or shared diagram must retain that dependency.
7. Every question is linked to one or more units of the selected textbook, all in the same course and subject. An empty, missing, foreign-subject or foreign-textbook mapping is invalid.
8. Admin checks the question, mapping, worked explanation and marking points. Pending questions cannot be used for study or mocks.
9. Admin confirms that the entire paper has been captured and reviewed before approving the paper. Until extraction is implemented, the manual workflow requires a completeness attestation plus at least one reviewed question; it cannot independently count questions in a PDF. The extraction pipeline must reconcile the source question inventory and subparts before publication.

Paper questions are tagged by unit, not by an artificial term assigned to the original full-syllabus paper. Marking schemes and examiner reports stay linked to their source paper and, where possible, to individual questions/subparts. A source paper may cover the whole syllabus; a student's generated term mock must still pass the covered-unit filter.

Question edits invalidate paper sign-off. Holding a textbook or paper for review removes its questions from new candidate pools. Historical attempts remain readable. Production uses immutable document/question versions and explicit publication transitions; never rewrite an exam that a student has already started or submitted.

## Mandatory term-mock selection rule

For student `s`, subject `x`, and question `q`, let `C` be the union of covered-unit sets for every saved Grade + Term progression combination for the student's current course and subject, and `U(q)` the question's required unit set.

```text
eligible(s, q) =
  active valid enrolment
  AND q.subject is enrolled by s
  AND q.course = s.course
  AND approved textbook, paper and question
  AND U(q) is non-empty
  AND every linked unit belongs to q's textbook/course/subject
  AND U(q) is a subset of C
```

Example: covered units are `{1, 2}`. A question mapped to `{1}` or `{1, 2}` is eligible. A question mapped to `{2, 3}` is excluded because Unit 3 is not covered. Overlap alone is insufficient.

Server computes the candidate pool. Clients cannot choose arbitrary question IDs or broaden scope. The local implementation applies the same rule to practice, lessons, hints, assignments and study suggestions, as well as mocks, to keep the term experience consistent. It returns an explicit no-eligible-questions response when coverage or mappings are incomplete. It never invents source questions or silently includes untaught units.

Production assembles papers from this eligible pool using requested marks, duration, topic balance and difficulty. Those optimizations must not relax eligibility. If the pool is insufficient, return a shortage report and ask Admin to prepare more content. AI-generated variants must inherit validated source-unit constraints, be checked and reviewed under a separately defined publication policy before being presented as assessed content.

At exam start, persist an immutable snapshot of student enrolment, coverage version, question versions/order, required units, marks, source references and deadline. Later coverage changes affect new exams only. Hints and explanations are unavailable during an active mock. Server enforces timing, answer ownership and idempotent submission.

Full past papers, marking schemes and examiner reports remain Admin-only in the current portal; exposing full-syllabus files could bypass term filtering or reveal answers. Parents and students can read approved enrolled-subject textbooks/reference materials and eligible question content. Approved textbooks may contain units outside the current term; term filtering applies to assessed question selection. The production tutor should restrict retrieved passages to the active question/lesson's units where appropriate.

## Data model and referential rules

| Entity | Required relationships |
| --- | --- |
| User | Unique username, role, password hash/identity provider, account status |
| StudentProfile | Student user, exactly one Parent user |
| EnrolmentPeriod | Student, academic year, course, grade, term, selected subject enrolments |
| CurriculumPlanVersion | Course/specification, effective academic period, publication status |
| DocumentVersion | Kind, course, subject, edition/source metadata, private object key, review state |
| TextbookUnit | Textbook version, same course/subject, unique unit code within book |
| TermCoverage | Plan version, course, subject, grade, term, one-to-many selected unit rows |
| Paper | Past-paper document version, selected textbook version, exam session/component |
| QuestionVersion | Paper, question/subpart number, marks, prompt/assets/stem dependencies, status |
| QuestionUnit | Many-to-many question-to-unit mapping; same textbook/course/subject |
| SourceAnnotation | Question, marking-scheme/report document, page/bounding box, marking point |
| MockExam / ExamItem | Student and immutable enrolment/coverage/question snapshot |
| Attempt / Review | Student, question version, submitted work, marks, feedback, audit history |
| Assignment / StudyPlan | Student; all suggested questions pass current eligibility |

PostgreSQL foreign keys, unique/check constraints and transactional domain validation jointly enforce these rules. Subject isolation is not entrusted to an LLM, dropdown, similarity search or filename. Retrieval uses metadata filters before vector ranking; same-subject checks occur again before returning content.

## Current implementation and future work

Implemented with FastAPI/PostgreSQL: three roles, Argon2 authentication, forced first-login password replacement, Admin account creation, audit events, parent-child isolation, active iGCSE catalog, progression and subject enrolments, and role-scoped portal state. The frontend screens for later workflows remain while their APIs are implemented.

Implemented foundations now include private document ingestion, reviewed versioned textbook and official-material extraction, same-subject weighted unit mappings, approved retrieval, immutable assessment delivery, two-pass source-grounded AI assessment, subject-specific marking policies, private OCR-assisted handwritten working, explainable per-student unit mastery, and reviewed source-linked weakness recommendations. Still planned: full account lifecycle, adaptive study planning, generated media and deployment to OCI.

Legacy mock records are not imported automatically. Any future import must preserve provenance and require Admin confirmation rather than inventing grade, term, subject, or unit mappings.

## Acceptance criteria for future generated code

- Parent A cannot read, review, assign to or fetch private working from Parent B's children.
- Parent/Student cannot create accounts, change enrolments, approve documents, define coverage or map questions through direct API requests.
- Phase 1 rejects other courses, unsupported grades/terms and combined Science enrolments.
- Paper upload fails without the correct approved textbook and registered units.
- A Mathematics paper cannot map to a Chemistry unit or an unrelated Mathematics textbook edition.
- Unmapped/pending questions and incomplete/unapproved papers never enter candidate pools.
- A question spanning covered and uncovered units is excluded.
- Grade and term matching is exact and absence of coverage fails closed.
- Existing exams retain their frozen content/scope when curriculum versions change.
- Invalid mutations are atomic; upload and publication failures cannot leave eligible partial records.
- Math equations, diagrams and source references survive ingestion with reviewable provenance.
- No API exposes passwords, hashes, session tokens or answer keys in ordinary student state.
