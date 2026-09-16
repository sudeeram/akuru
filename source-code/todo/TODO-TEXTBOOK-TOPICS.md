# AKURU textbook groups, topics and incremental coverage roadmap

This roadmap updates AKURU for textbooks that contain **Units** or **Modules**, each containing ordered **Topics**. A topic may be supplied as one or more scanned PDFs. Topic coverage is added to a Grade + Term as teaching progresses and is cumulative for students.

The production system has no uploaded educational content yet. The initial administrator and operational data must remain intact, but no legacy textbook, curriculum, question, assessment or mastery content needs conversion. Complete the steps in order unless a step explicitly permits parallel work.

Status: `[ ]` not started, `[~]` in progress, `[x]` complete, `[!]` blocked with the reason recorded beside it.

## Textbook hierarchy and fixed rules

AKURU uses this canonical hierarchy:

```text
Course
└── Subject
    └── Textbook edition
        └── Section group (displayed as Unit or Module)
            └── Topic
                └── One or more uploaded textbook parts
```

- `section_group` is the internal concept; each textbook selects the visible label `unit` or `module`.
- `topic` is the smallest curriculum, question-mapping, retrieval, mastery and study-planning level.
- Unit or Module mastery is an explainable aggregation of its topic mastery.
- Uploaded files are textbook parts; uploading one topic PDF must not create a separate logical textbook.
- Only published topics and reviewed source content may enter coverage, retrieval, mock papers or Tutor context.
- A question may require multiple topics, but every topic must belong to the question's subject.
- A topic is introduced in one Grade + Term per curriculum-plan version; student eligibility is cumulative across reached progression periods.
- Existing assessment sessions retain immutable topic-coverage snapshots when coverage later changes.

## Step 0 — Record the new architecture and protect production

**Goal:** Make the hierarchy authoritative and confirm that the empty-content migration path is safe.

### Backend and data

- [x] Update the overall and backend architecture documents with Textbook → Section Group → Topic → Textbook Part.
- [x] Record `unit` and `module` as presentation labels over the same backend entity.
- [x] Document topic-level authorization, publication, retrieval, mapping, mastery and snapshot rules.
- [x] Add a read-only pre-migration audit that counts documents, textbook content, curriculum plans, official materials, mappings, assessments, mastery and Tutor sessions.
- [x] Require all educational-content counts to be zero before using the clean restructuring path.
- [x] Back up the production PostgreSQL database and `/data/akuru/documents` before schema deployment.

### Frontend and product

- [x] Update the frontend architecture with Admin structure editing, topic uploads, extraction review and incremental coverage.
- [x] Define consistent labels and empty states for Textbook, Unit/Module, Topic and Textbook Part.
- [x] Confirm that internal UUIDs remain hidden from users.

**Completed:** The overall, backend and frontend architecture documents now make the topic hierarchy authoritative and preserve Unit/Module as a display choice. `app.content_migration_audit` counts every migration-sensitive content table, emits a structured report and fails closed with `--require-empty`. Its tests cover complete category traversal and non-empty rejection. The production audit on 16 September 2026 reported `safeForCleanTextbookTopicMigration: true` with `totalRecords: 0`; users, authentication, family/enrolment, catalogue, provider, quota and audit/operations records are deliberately preserved.

**Rollback evidence:** A root-owned mode-`0700` rollback directory was created at `/data/akuru/backups/pre-topic-step0-20260916T134856Z`. Its PostgreSQL custom dump, document archive and checksum manifest are mode `0600`; `pg_restore --list` and `tar -tzf` validated both archives. The server still needs the separately planned off-server `age` recipient before automated encrypted backups can be enabled.

**Validation:** `npm run verify` passes with the generated API contract, 33 frontend tests, 101 backend tests, TypeScript, lint and the production frontend build. The two new audit tests verify complete table-category traversal and fail-closed detection when one content record exists.

**Done when:** Architecture and terminology are agreed, the production audit proves no educational content needs migration, and rollback inputs exist.

## Step 1 — Replace the unit-only schema with the topic hierarchy

**Goal:** Establish the correct normalized model before content is uploaded.

### Backend and database

- [x] Add or reshape a logical `textbooks` entity with course, subject, title, edition, publisher, `group_label`, status and audit fields.
- [x] Add ordered `textbook_groups` with textbook, code, title, sequence and summary.
- [x] Add ordered `textbook_topics` with group, code, title, sequence, optional syllabus reference, description and publication state.
- [x] Add `textbook_topic_documents` linking topics to document versions with role, order, printed-page metadata and review state.
- [x] Add group and topic provenance to approved retrieval chunks.
- [x] Introduce topic-level curriculum-plan rows, question mappings, mastery, mastery events, weaknesses, recommendations and study-plan references.
- [x] Add topic identifiers to immutable assessment curriculum snapshots.
- [x] Retain user, family, authentication, provider, quota, audit and operational tables unchanged.
- [x] Use an Alembic migration that fails closed if educational-content tables are unexpectedly non-empty.
- [x] Add uniqueness, ordering, same-textbook and same-subject constraints at database level where possible.
- [x] Update SQLAlchemy models and migration-drift checks.

**Completed:** Alembic revision `c31d9e5a7b42` adds the normalized textbook hierarchy, topic document associations, topic curriculum introductions, official-question topic mappings, retrieval and assessment-snapshot provenance, topic mastery tables and downstream topic references. Composite constraints bind topics to the same textbook, course, subject and group. The previous unit structures remain deprecated compatibility scaffolding until Steps 2–7 move the existing services; production has no educational content that can enter them.

**Migration safety:** The local audit initially found one empty legacy study-plan shell for local test user `laura`. Its complete row was preserved at `/tmp/akuru-local-orphan-study-plan-b28230a8.json` with mode `0600`, then the item-free shell was removed. The repeated local audit reported zero content records. The migration applied locally and `alembic check` reports no drift at the single head `c31d9e5a7b42`. Production remains at the prior schema until the planned production rollout step.

**Validation:** `npm run verify` passes with 33 frontend and 105 backend tests, API contract verification, TypeScript, lint and the production frontend build. New tests cover hierarchy registration, downstream topic provenance, preserved identity/operations tables and fail-closed migration refusal.

**Done when:** A clean database can represent both Unit-based and Module-based books without duplicating backend logic, and Alembic reaches one head with no drift.

## Step 2 — Build textbook structure APIs and domain rules

**Goal:** Let Admin create and maintain the logical structure independently from uploaded PDFs.

### Backend

- [x] Add Admin-only create, read, update, publish and archive operations for textbooks.
- [x] Add ordered group and topic management with safe reordering.
- [x] Validate `group_label` as `unit` or `module`.
- [x] Require unique group codes and topic codes within a textbook.
- [x] Prevent cross-course, cross-subject and cross-textbook relationships.
- [x] Version published structure changes and retain audit history.
- [x] Prevent removal of a published topic referenced by coverage, mappings or immutable assessments.
- [x] Expose public references rather than database UUIDs in user-facing contracts.
- [x] Regenerate and verify the typed OpenAPI frontend contract.

### Frontend

- [x] Add an Admin textbook catalogue with subject, edition, structure label, status and topic readiness.
- [x] Add a structure editor for groups and topics with explicit save and publish actions.
- [x] Display Unit or Module according to the textbook configuration.
- [x] Provide validation messages for duplicate codes, invalid order and protected published content.

**Completed:** Admin-only APIs and the Admin portal now manage logical textbook editions, ordered Unit/Module groups and ordered topics independently of PDF uploads. Publishing creates immutable structure snapshots, later edits create a new draft, referenced topics are protected, all changes are audited, and user-facing contracts contain public references rather than UUIDs.

**Validation:** Alembic reaches the single head `d42e6f7b8c53` with no drift. Integration coverage exercises authentication, duplicate editions, ordered groups and topics, confirmation, safe swapping, immutable publication versions and audit records. The generated OpenAPI contract, frontend contract tests, TypeScript, lint and production build are verified by `npm run verify`.

**Done when:** Admin can publish an empty Chemistry structure containing Units 1–4 and Topics 1–29 before uploading any topic PDF.

## Step 3 — Attach scanned textbook parts to topics

**Goal:** Process image-only topic PDFs without treating every file as an independent textbook.

### Backend and worker

- [x] Extend document upload metadata with logical textbook, group, topic and document role.
- [x] Support one or many primary or supporting documents per topic.
- [x] Add single-file and batch-upload APIs with idempotency and duplicate detection.
- [x] Keep originals and all derived assets in private storage outside the release directory.
- [x] Reuse page rendering and OCR for PDFs with no native text.
- [x] Add orientation detection, rotation correction, deskew and image-quality diagnostics where deterministic tooling permits.
- [x] Preserve original page images alongside normalized review images.
- [x] Store OCR language, confidence, bounding boxes, reading order and extraction method per block.
- [x] Flag chemical formulae, equations, subscripts, superscripts, reaction arrows, tables and diagrams for review.
- [x] Preserve separate physical PDF page indexes and editable printed-page labels.
- [x] Associate approved chunks and assets with the exact textbook, group, topic, document version and page.
- [x] Keep optional multimodal OpenAI enhancement behind provider configuration and human review; deterministic extraction remains available when AI is disabled.

### Frontend

- [x] Add upload from within a selected topic so scope is unambiguous.
- [x] Add batch upload with filename-based topic suggestions that Admin must confirm.
- [x] Show job progress, retry controls and specific extraction failures.
- [x] Build side-by-side original page, normalized page and extracted-block review.
- [x] Allow correction of text, formulae, block type, reading order and printed page label.
- [x] Show diagram, image, table and equation crops.
- [x] Prevent topic publication while required pages or low-confidence blocks remain unresolved.

**Completed:** Topic-scoped single and batch upload APIs derive scope from the logical textbook, enforce roles, idempotency, duplicate detection and private storage, then connect the existing isolated OCR worker to the topic document. Original and normalized pages, detailed OCR provenance, quality diagnostics and review flags are preserved. The Admin portal uploads within a topic and supports complete extraction correction. Topic content has no automatic publication path; Step 4 will permit publication only after review readiness passes.

**Validation:** Migration `e53f7a9c4d64` adds upload idempotency and original-page provenance. Integration tests cover topic attachment, repeat requests, processing-state propagation, dual page assets, diagnostics, block correction and printed labels; extraction tests cover scanned OCR, page labels and visual assets.

**Done when:** An image-only Chemistry topic PDF produces reviewable pages, text and visual assets, and published content is traceable to the original scan.

## Step 4 — Publish textbook topics independently

**Goal:** Allow useful reviewed content to become available without waiting for an entire book.

### Backend

- [x] Separate textbook-structure publication from topic-content publication.
- [x] Require at least one reviewed primary source before publishing a topic's content.
- [x] Record the exact source document versions and extraction version in each published topic version.
- [x] Supersede corrected topic content without changing historical citations or assessment snapshots.
- [x] Block unreviewed and superseded topic content from retrieval and new mappings.
- [x] Add extraction-quality and publication-readiness diagnostics per topic and textbook.

### Frontend

- [x] Show topic states: no document, processing, needs review, ready, published, failed and superseded.
- [x] Add an Admin readiness checklist and explicit publication confirmation.
- [x] Add textbook-level progress such as published topics out of total topics without implying unreviewed content is usable.

**Completed:** Topic-content publication is independent from textbook structure. Readiness requires reviewed source evidence, each publication records immutable document and extractor versions, reviewed blocks become topic-versioned retrieval chunks, and corrected publications supersede prior content and chunks without deleting history. The Admin catalogue shows state, confidence, checks, version and textbook publication progress.

**Validation:** Migration `f64a8b0d5e75` reaches one Alembic head without drift. Integration coverage verifies readiness transitions, explicit publication, exact source manifests, active topic chunks, corrected version supersession and batch uploads that return the topic to a draft-processing state while its prior published version remains preserved.

**Done when:** Topics 1 and 2 can be published and used while Topics 3–29 remain absent or under review.

## Step 5 — Build incremental, versioned topic coverage

**Goal:** Let Admin add topics to a Grade + Term as they are taught.

### Backend

- [x] Replace unit-level plan membership with topic-level introduction periods.
- [x] Permit coverage to reference only published topics from the active textbook edition and selected subject.
- [x] Add “create next draft from published plan” so Admin does not rebuild coverage on every update.
- [x] Allow newly completed topics to be appended to the current term.
- [x] Keep one introduction period per topic within a plan version.
- [x] Calculate cumulative eligibility across all reached student Grade + Term progression entries.
- [x] Warn and require explicit confirmation before removing or moving previously published coverage.
- [x] Preserve old plan versions and immutable assessment snapshots.
- [x] Return missing-coverage and insufficient-question-pool diagnostics at topic level.

### Frontend

- [x] Replace the unit coverage editor with a grouped Unit/Module → Topic checklist.
- [x] Display published coverage separately from unsaved additions and removals.
- [x] Add “Add topics covered now” workflow for the current term.
- [x] Show cumulative preview for each Grade + Term.
- [x] Show impact warnings before publishing removals or period moves.
- [x] Display plan version and audit information without internal identifiers.

**Completed:** Coverage uses published topics from the active logical textbook. A new draft clones the current publication, reports additions, removals and moves, and requires explicit impact confirmation for destructive changes. Cumulative eligibility follows saved student progression and assessment snapshots retain their original topic set.

**Validation:** Migration `g75b9c1e6f86` records plan lineage. Integration coverage verifies cloned drafts, current-term additions, cumulative Grade 10 Term 1–2 eligibility, superseded plan history and immutable assessment topic snapshots.

**Done when:** Adding Chemistry Topic 5 to Grade 10 Term 2 makes Topics 1–5 available to an eligible student while an already-started assessment retains its original snapshot.

## Step 6 — Move past-paper question mapping to topics

**Goal:** Match questions to the smallest covered concepts while preserving strict subject boundaries.

### Backend

- [x] Replace or extend unit mappings with weighted topic mappings.
- [x] Restrict candidates to published topics in the paper's approved subject and textbook edition.
- [x] Permit one question to require multiple topics, including topics in different groups of the same subject.
- [x] Require all mandatory mapped topics to be covered before a question enters a student's pool.
- [x] Aggregate topic mappings to their parent group for reporting.
- [x] Update mapping suggestions, review, confirmation, audit and completeness checks.
- [x] Return topic-level reasons when the mock-paper pool is short.

### Frontend

- [x] Show mapping candidates grouped by Unit or Module.
- [x] Let Admin select multiple topics and assign weights or required status.
- [x] Display extracted question evidence beside topic mappings.
- [x] Show same-subject validation and clear eligibility diagnostics.

**Completed:** Past-paper questions use weighted, reviewed topic mappings constrained to the active published same-subject textbook. Multiple required topics may span groups, group totals are reported, question evidence remains visible, and confirmed mappings are audited and immutable. Student selection requires every mandatory topic and shortage diagnostics name missing topics.

**Validation:** Integration coverage maps one Chemistry question to Topics 4 and 7 in different groups, rejects a Biology topic, verifies weights and group aggregation, and confirms both mandatory mappings. Assessment and pool selection use the topic set whenever topic coverage is active.

**Done when:** A question requiring Topics 4 and 7 is eligible only after both are covered and can never map to a topic in another subject.

## Step 7 — Update retrieval, citations and learning services

**Goal:** Make every learning capability topic-aware without losing group summaries.

### Backend

- [x] Filter textbook retrieval by published edition, group, topic and student coverage before vector ranking.
- [x] Include topic, group label/title, source document, PDF page, printed page and bounding box in citations.
- [x] Update assessment context selection to use mapped topics.
- [x] Calculate topic mastery and evidence confidence from published assessment results.
- [x] Calculate Unit or Module mastery as an explainable aggregation of topic mastery.
- [x] Move weaknesses, recommendations and study-plan items to topic scope.
- [x] Update deterministic next-topic recommendations while retaining group context.
- [x] Update Tutor sessions and tools to use an active topic and permit only covered-topic switching.
- [x] Preserve formal-assessment restrictions, family isolation, per-child quotas and transcript rules.
- [x] Return evidence-insufficient results instead of crossing topics or inventing citations.

### Frontend

- [x] Update student progress to show Unit/Module summaries expandable into topics.
- [x] Update study plans and recommendations to name the topic and its parent group.
- [x] Update Tutor selection, context, switching and citations to topic level.
- [x] Update Parent summaries to show group-level progress and actionable topic weaknesses.
- [x] Update Admin evaluation screens with topic isolation and citation-quality results.

**Done when:** AKURU can say “Topic 14 in Unit 2 needs work” with assessment evidence and open the exact reviewed textbook page supporting its explanation.

## Step 8 — Complete role-specific usability and accessibility

**Goal:** Make the richer hierarchy understandable on desktop, tablet and mobile.

- [x] Use the configured Unit or Module label consistently across all roles.
- [x] Add search and filtering by subject, textbook, group, topic, status and term.
- [x] Add accessible tree/list navigation that does not rely on drag-and-drop.
- [x] Provide keyboard controls, focus states, screen-reader labels and non-colour status indicators.
- [x] Preserve horizontal top navigation and AKURU BOT loading transitions.
- [x] Avoid exposing UUIDs, provider secrets, storage paths or raw internal confidence objects.
- [x] Add destructive-action confirmation only for meaningful published-content changes.

**Done when:** Admin can complete structure, upload, review and coverage tasks with a keyboard, and parents and students can understand topic progress on a tablet.

## Step 9 — Add evaluation and release gates

**Goal:** Prove scanned extraction and topic isolation are good enough before production content is trusted.

### Automated validation

- [ ] Add database constraint and migration tests for both label types and all scope boundaries.
- [ ] Add backend authorization, family-isolation, idempotency and immutable-snapshot tests.
- [ ] Add scanned English, French, Science, ICT and Maths fixtures with equations, diagrams and tables.
- [ ] Add frontend contract tests for every Admin and role-specific workflow.
- [ ] Add cumulative-coverage tests across Grade 10 and Grade 11 terms.
- [ ] Add multi-topic eligibility, cross-subject rejection and pool-shortage tests.
- [ ] Add topic mastery aggregation and Tutor citation-isolation tests.
- [ ] Run contract generation/check, backend tests, frontend tests, typecheck, lint, build, Alembic upgrade/check and security checks.

### Content-quality evaluation

- [ ] Define thresholds for page coverage, OCR confidence, formula review, diagram retention, printed-page accuracy and topic retrieval precision.
- [ ] Produce an Admin quality report per topic PDF.
- [ ] Block publication when mandatory checks fail; allow audited Admin resolution of review flags.
- [ ] Pilot with Chemistry Topics 1 and 2 before processing the remaining collection.

**Done when:** The complete quality gate passes and pilot content retrieves only the correct reviewed topic with exact citations.

## Step 10 — Deploy safely to production

**Goal:** Introduce the new empty-content schema without affecting authentication or operations.

- [ ] Commit and push a reviewed release revision.
- [ ] Confirm the production educational-content audit is still empty immediately before migration.
- [ ] Take encrypted database and document-storage backups and record the restoration procedure.
- [ ] Deploy the exact release revision and locked dependencies.
- [ ] Apply the Alembic migration and verify one migration head with no drift.
- [ ] Restart API, worker and frontend services and verify health, logs and loopback bindings.
- [ ] Verify the production Admin account, role authorization and HTTPS security headers.
- [ ] Create the Chemistry book, select Unit terminology, and define Units 1–4 and Topics 1–29.
- [ ] Upload and review only the pilot topics first.
- [ ] Test structure publication, OCR review, topic publication, incremental coverage, retrieval and question eligibility end to end.
- [ ] Record release evidence and rollback decision points before expanding to other subjects.

**Done when:** The production Admin can manage the new hierarchy and pilot scanned topics safely, while existing accounts, security controls and operations remain healthy.
