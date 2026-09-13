# AKURU implementation roadmap

This is the ordered delivery backlog for the document-ingestion, OpenAI tutoring, assessment, unit-mastery and study-planning capabilities agreed for AKURU. Complete the steps in order unless an item explicitly says it can run in parallel.

The authoritative rules remain in [docs/architecture.md](docs/architecture.md). Check a box only after the step's acceptance criteria and tests pass.

Status: `[ ]` not started, `[~]` in progress, `[x]` complete, `[!]` blocked with the reason recorded beside it.

## Step 0 — Protect the current foundation

**Goal:** Preserve authentication, family isolation, iGCSE catalog and cumulative progression behavior.

- [x] Record a baseline run of frontend, backend and PostgreSQL integration tests.
- [x] Add CI for frontend tests, type checking, linting and production build.
- [x] Add backend CI with isolated PostgreSQL and Alembic migrations.
- [x] Document environment variables without committing secrets.
- [x] Document and test database backup and restore.

**Done when:** A clean checkout can run all documented checks; existing role, family-scope and Grade + Term progression tests pass.

## Step 1 — Establish backend module boundaries

**Goal:** Separate the new domains before the initial portal module grows further.

- [x] Add versioned routers and schemas for documents, curriculum, questions, assessments, tutoring and mastery.
- [x] Add service and repository boundaries for database access.
- [x] Centralize Admin-only content and student-owned submission permissions.
- [x] Maintain a typed frontend contract from FastAPI OpenAPI.
- [x] Standardize validation, permission and processing error responses.

**Done when:** HTTP concerns live in routers, rules live in services, and every endpoint derives role and scope from the authenticated principal.

## Step 2 — Add private object storage and document records

**Goal:** Preserve original documents and derived assets with complete provenance.

- [x] Build a storage interface with local-filesystem and OCI Object Storage implementations.
- [x] Add `documents`, `document_versions`, `document_assets` and `document_events` tables.
- [x] Store type, course, subject, edition, year, session, component, variant and source metadata.
- [x] Calculate SHA-256 checksums and detect duplicates.
- [x] Validate file signature, content type, extension and size.
- [x] Add Admin-only upload, status, retry and removal APIs.
- [x] Serve private files only through authorized endpoints.

**Done when:** Only Admin can upload learning documents; original bytes are recoverable unchanged; invalid and duplicate files produce specific errors.

## Step 3 — Add asynchronous processing

**Goal:** Keep large PDF and image work outside ordinary FastAPI requests.

- [x] Add a Redis-backed queue and document worker.
- [x] Track queued, processing, needs-review, failed and completed states.
- [x] Make every processing stage idempotent and safely retryable.
- [x] Record progress, timestamps, extraction version and useful failures.
- [x] Add job-status APIs and frontend progress reporting.
- [x] Enforce time, memory and page-count limits.

**Done when:** Upload returns promptly, worker restarts do not duplicate data, and Admin can inspect and retry a failed stage.

## Step 4 — Build deterministic PDF and image extraction

**Goal:** Preserve text, equations, diagrams and source locations before using AI.

- [x] Render every PDF page at review resolution.
- [x] Extract native PDF text and coordinates where available.
- [x] Run OCR on scans and image-only regions.
- [x] Detect headings, paragraphs, tables, questions, subparts and answer spaces.
- [x] Extract embedded images plus diagram and page crops.
- [x] Recognize equations; store LaTeX and the original crop.
- [x] Store page, bounding box, method and confidence for every block.
- [x] Add Maths, Science, ICT, English and French fixtures.

**Done when:** Every block traces to its source, diagram-only questions are retained, and low-confidence OCR/equations are flagged for review.

## Step 5 — Add the OpenAI provider layer

**Goal:** Use the OpenAI Platform for structured multimodal understanding without making it authoritative for permissions or curriculum rules.

- [x] Define an `AIProvider` interface and OpenAI Responses API implementation.
- [x] Keep API keys in backend secrets and OCI Vault in production.
- [x] Version prompts separately for textbook extraction, paper extraction, mapping, assessment and tutoring.
- [x] Require Structured Outputs/JSON schemas and validate every result.
- [x] Send only pages and context required for the operation.
- [x] Record provider, model, prompt version, purpose, latency, usage and response ID.
- [x] Add timeouts, bounded retries, concurrency and cost limits.
- [x] Treat uploaded content as untrusted reference data, never as system instructions.
- [x] Add a fake provider so tests never require paid API calls.

**Architecture decision:** The AKURU runtime uses the OpenAI Responses API. Codex supports development, review, migrations, testing and deployment; it is not the student-facing tutor. PostgreSQL and AKURU services remain authoritative.

**Done when:** No provider secret reaches the frontend or logs, malformed AI output fails safely, and tests run without external calls.

## Step 5A — Add ordered OpenAI account routing

**Goal:** Let Admin configure an ordered pool of backend-only OpenAI credentials and continue work when a preferred account is temporarily unavailable or has exhausted prepaid credit.

- [x] Store account name, credential alias, unique priority (0–100), model, enabled state and health in PostgreSQL without storing keys.
- [x] Resolve credential aliases from `AKURU_OPENAI_ACCOUNT_KEYS` in the backend dotenv file.
- [x] Build authenticated Admin list, create and update APIs without returning secrets or internal IDs.
- [x] Add an Admin portal screen for priority, model, enabled state and sanitized health information.
- [x] Route each complete AI operation through enabled accounts in ascending priority order.
- [x] Retry only a failed complete operation; never combine partial results from two accounts.
- [x] Fail over after exhausted credit or bounded transient failures and preserve one logical operation ID.
- [x] Disable invalid credentials and use cooldowns for temporary failures.
- [x] Require the same requested model and prompt/schema/context across attempts.
- [x] Record every provider attempt and selected account without secrets or source content.
- [x] Add deterministic tests for ordering, failover, uniqueness, authorization and secret isolation.

**Architecture decision:** Account configuration is database-managed, while keys remain in dotenv. The database stores a credential alias that resolves against a JSON map such as `AKURU_OPENAI_ACCOUNT_KEYS='{"HOME":"sk-..."}'`. Account switching occurs between complete Responses API calls and may add latency or lose project-specific prompt caching, but it must not change curriculum inputs or accepted output schemas.

**Done when:** Admin can safely manage unique priorities, the router selects the first healthy configured account, failover produces one validated result, and no credential appears in an API response, database row or log.

## Step 6 — Extract and approve textbooks

**Goal:** Turn each textbook into the reviewed unit vocabulary for its subject.

- [x] Propose chapters, units, sections, definitions, concepts, equations, examples and diagrams.
- [x] Add immutable textbook and unit versions.
- [x] Build side-by-side Admin review of source page and extraction.
- [x] Let Admin correct hierarchy, page ranges, text and equations.
- [x] Require course, subject and edition confirmation.
- [x] Add publication and superseding workflows with audit history.
- [x] Block downstream paper ingestion until units are approved.

**Done when:** Every unit belongs to one approved textbook version and unreviewed content cannot enter coverage, retrieval or assessment.

## Step 7 — Implement curriculum plans and cumulative coverage

**Goal:** Define exactly which approved units each Grade + Term covers.

- [x] Add versioned curriculum-plan and term-coverage tables.
- [x] Build Admin coverage editing and publication APIs.
- [x] Union coverage across the student's ordered progression entries.
- [x] Snapshot the curriculum-plan version at assessment start.
- [x] Add missing-coverage and question-pool shortage diagnostics.

**Done when:** Grade 10 Term 2 includes configured Terms 1 and 2; missing coverage fails closed; existing assessments keep their original snapshot.

## Step 8 — Extract papers, marking schemes and examiner reports

**Goal:** Build complete, linked official assessment material.

- [x] Require an approved same-subject textbook before accepting a paper.
- [x] Extract questions, subparts, stems, marks, equations, tables and diagrams.
- [x] Reconcile the complete question inventory against the source paper.
- [x] Link marking-scheme entries to question/subpart and source location.
- [x] Extract alternatives, method marks, accuracy marks and required points.
- [x] Link examiner comments, common mistakes and advice.
- [x] Store immutable question and rubric versions.
- [x] Build Admin correction, completeness sign-off and publication screens.

**Done when:** No question publishes without prompt, marks, assets and provenance; shared stems remain attached; incomplete papers cannot publish.

## Step 9 — Map questions to textbook units

**Goal:** Make every assessed question traceable to one or more curriculum units.

- [ ] Add weighted question-to-unit mappings.
- [ ] Suggest mappings with metadata-filtered retrieval and OpenAI.
- [ ] Restrict suggestions to the selected same-course, same-subject textbook.
- [ ] Require Admin confirmation.
- [ ] Reject empty, cross-subject, cross-course and foreign-edition mappings transactionally.
- [ ] Require multi-unit weights to total 100%.

**Done when:** Similarity never overrides relational validation, and a multi-unit question is eligible only when every required unit is covered.

## Step 10 — Build approved retrieval and RAG

**Goal:** Provide precise source context without leaking unrelated or unapproved material.

- [ ] Enable `pgvector` and versioned embeddings.
- [ ] Chunk approved textbook sections, marking points and examiner guidance with provenance.
- [ ] Filter by course, subject, textbook, unit, publication and student eligibility before vector ranking.
- [ ] Return evidence with document, page and bounding box.
- [ ] Re-index only affected content after approved corrections.
- [ ] Add retrieval-quality tests for every subject.

**Done when:** Retrieval excludes foreign-family, foreign-subject, pending and superseded content, and every result opens at its authorized source location.

## Step 11 — Deliver practice, official papers and mocks

**Goal:** Give each student only eligible, immutable assessment material.

- [ ] Implement the deterministic all-units eligibility service.
- [ ] Add blueprints for marks, time, skills and difficulty.
- [ ] Support individual practice, uploaded official papers and term mocks.
- [ ] Freeze question versions, assets, rubric, coverage and deadline at start.
- [ ] Add autosave, idempotent submission and deadline enforcement.
- [ ] Hide hints, answers and feedback during active exam mode.
- [ ] Report shortages instead of broadening the syllabus.

**Done when:** Students cannot choose arbitrary questions, post-exam feedback stays hidden until submission/expiry, and later edits cannot change an active assessment.

## Step 12 — Build the AKURU assessment service

**Goal:** Mark answers from official evidence and show exactly how to improve.

- [ ] Define a versioned schema for marks, marking-point decisions, strengths, small mistakes, conceptual mistakes, improved answer, teaching explanation, unit evidence, recommendations and confidence.
- [ ] Retrieve the exact question, rubric, marking scheme, examiner advice and mapped textbook context.
- [ ] Compare meaning and method rather than wording alone.
- [ ] Produce both an exam-ready answer and a teaching explanation.
- [ ] Scale responses to the command word and available marks.
- [ ] Cite student evidence for every awarded or missed point.
- [ ] Prevent awarded marks exceeding the maximum.
- [ ] Route uncertain or subjective results to review.
- [ ] Preserve model, prompt, sources and rubric version for every assessment.

**Done when:** Every mark is traceable to rubric and student evidence, feedback is specific, official points are never invented, and reassessment creates history.

## Step 13 — Add subject-specific marking

**Goal:** Combine AI judgement with checks suited to each subject.

- [ ] Maths: symbolic equivalence, method, formula, substitution, units and rounding.
- [ ] Science: terminology, causal reasoning, experiments, variables, calculations and conclusions.
- [ ] ICT: vocabulary, scenario application, trade-offs and extended reasoning.
- [ ] English: approved task, evidence, organisation and language rubrics.
- [ ] French: approved comprehension, vocabulary, grammar and communication rubrics.
- [ ] Handwritten answers: OCR confidence plus original-image review.

**Done when:** Maths can award method marks despite a wrong final answer, deterministic and AI results remain separate, and every enabled engine has reviewed examples.

## Step 14 — Calculate unit mastery and confidence

**Goal:** Produce a meaningful, explainable unit score such as 7/10.

- [ ] Add `unit_mastery`, `unit_mastery_dimensions` and append-only `unit_mastery_events`.
- [ ] Track relevant knowledge, application, method, accuracy, reasoning, communication and retention dimensions.
- [ ] Weight evidence by marks, unit mapping, difficulty, assessment mode, hints, retries and recency.
- [ ] Give timed mocks and official exam-mode papers more weight than hinted practice.
- [ ] Calculate a 0–10 display score with higher internal precision.
- [ ] Calculate low, medium or high confidence from quantity, variety and recency.
- [ ] Mark scores provisional when evidence is insufficient.
- [ ] Store every previous score, new score and contributing event.
- [ ] Calculate recent trend without discarding older evidence.

**Done when:** One easy question cannot create a high-confidence ranking, multi-unit results update by approved weights, and every change can be explained.

## Step 15 — Diagnose weaknesses and recommend improvement

**Goal:** Turn missed marking points into specific next actions.

- [ ] Create a subject-aware mistake taxonomy.
- [ ] Tag issues such as formula selection, units, terminology, graph interpretation and command-word response.
- [ ] Detect recurring mistakes without mixing siblings.
- [ ] Generate recommendations from diagnosed weakness and approved textbook material.
- [ ] Link each recommendation to its unit, source and activity.
- [ ] Recommend review, targeted practice, spaced retry and short unit checks.
- [ ] Provide Parent/Admin review for sensitive or low-confidence recommendations.

**Done when:** Recommendations state the observed weakness and evidence, and every suggested question passes student eligibility.

## Step 16 — Connect mastery to the study planner

**Goal:** Create an adaptive, reviewable plan for each student.

- [ ] Prioritize weak, declining and low-confidence units within covered scope.
- [ ] Balance enrolled subjects and upcoming assessments.
- [ ] Give each plan item a duration, reason, source and success condition.
- [ ] Schedule spaced retries after feedback.
- [ ] Keep completed plan history and regenerate only from new evidence or request.
- [ ] Keep every child's plans and Parent reviews separate.

**Done when:** Plans contain only assigned subjects and covered units, and every activity explains why it was selected.

## Step 17 — Build role-specific experiences

**Goal:** Make assessment and mastery understandable to Students, Parents and Admins.

- [ ] Student answer review with marks, evidence, improvements, model answer and explanation.
- [ ] Student unit dashboard with score, confidence, trend, dimensions, mistakes and next steps.
- [ ] Parent child-by-child summaries, longer-term trends and review tasks.
- [ ] Admin extraction review with original page beside extracted content.
- [ ] Admin assessment audit with sources, versions, confidence and reassessment controls.
- [ ] Accessible equations, diagram zoom, keyboard navigation and descriptions.
- [ ] Clear loading, failure, retry and insufficient-evidence states.

**Done when:** Students understand the result and next action, Parent scope remains isolated, and Admin can correct all AI-derived content.

## Step 18 — Add diagrams and optional media

**Goal:** Improve explanations visually without weakening accuracy.

- [ ] Generate controlled SVG for circuits, forces and geometry where practical.
- [ ] Use plotting code for graphs and numerical visuals.
- [ ] Add an OpenAI image provider for conceptual illustrations.
- [ ] Store prompts, source links, model versions and assets privately.
- [ ] Require review before publishing generated educational images.
- [ ] Later: approved explanation → storyboard → narration → video → review → publication.

**Done when:** Exam-critical visuals are deterministic or reviewed, generated media never replaces official source evidence, and video remains optional.

## Step 19 — Add evaluation and release gates

**Goal:** Prove quality before enabling automatic publication or marking.

- [ ] Create an Admin-approved evaluation corpus for every Phase 1 subject.
- [ ] Measure question inventory recall, OCR, equation and diagram preservation.
- [ ] Measure mapping precision and cross-subject rejection.
- [ ] Compare marks and method marks with reviewed expected results.
- [ ] Test small-error detection, improved answers and grounding.
- [ ] Test repeatability across model and prompt versions.
- [ ] Set confidence thresholds for automatic feedback versus review.
- [ ] Run regressions before model or prompt changes.

**Done when:** Each enabled subject meets documented thresholds and failed evaluation blocks its automatic workflow.

## Step 20 — Production security, privacy and operations

**Goal:** Operate safely for children and family data on OCI.

- [ ] Put FastAPI and workers behind HTTPS and a hardened reverse proxy.
- [ ] Put OpenAI, database and storage credentials in OCI Vault.
- [ ] Add rate limits, quotas, AI budgets and per-family usage controls.
- [ ] Minimize student data sent to providers and use pseudonymous identifiers where appropriate.
- [ ] Define retention and deletion for answers, working and generated content.
- [ ] Add encrypted backups and restoration drills.
- [ ] Add audit review, job monitoring, alerts and cost monitoring.
- [ ] Review provider data controls before public deployment.
- [ ] Test broken object authorization, prompt injection, malicious files and answer-key leakage.

**Done when:** Secrets are absent from repositories, images, browser bundles and logs; every private endpoint has authorization tests; backup and incident procedures are verified.

## Deferred beyond Phase 1

- [ ] iPrimary curriculum and grade model.
- [ ] iLower Secondary curriculum and grade model.
- [ ] Multiple guardians per student.
- [ ] School-specific curriculum plans.
- [ ] Fully automatic handwritten essay marking without review.
- [ ] Student-facing generated video lessons.
- [ ] Qualification-grade prediction.

## Definition of done for every step

- Code and migrations are committed.
- Relevant authorization and domain tests pass against PostgreSQL.
- Frontend type checking, linting, tests and build pass when affected.
- Documentation and environment examples are updated.
- No secret, answer key or private student data appears in logs or fixtures.
- AI-derived records include source provenance, version, confidence and review status.
- The step's acceptance criteria have been demonstrated.
