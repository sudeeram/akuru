# Curated flashcard library and adaptive Student review

**Status: Planned**

This roadmap replaces Admin-triggered flashcard generation with a curated, source-grounded release process. Flashcards are prepared after textbook topics are reviewed and published, validated outside the Student request path, imported into AKURU as a versioned release artifact, and then served using deterministic study and scheduling rules.

The number of cards is chosen from the learning points in each textbook unit. Chemistry Unit 1 may contain approximately 100 cards, but completeness and quality take precedence over reaching a fixed number.

## Product decisions

- Remove **Generate grounded draft** and its card-limit control from the Admin interface.
- Do not call OpenAI when a Student opens, reveals, rates or resumes flashcards.
- Do not generate cards on demand in production.
- Prepare cards from published textbook evidence using a developer-operated workflow and import them through a validated application command or protected release operation. Never insert them directly with ad-hoc SQL.
- Keep exact topic, content-version, document, printed-page and source-passage provenance for every card.
- Keep released decks immutable. Corrections produce a new deck release while prior Student history remains readable.
- Allow the Admin to view deck readiness, provenance, validation results, release state and rollback controls. Card generation is not an Admin task.
- Select the final card count from a concept-coverage report. Avoid filler cards created only to reach 100.

## Quality distribution

Each unit release must report how its cards are distributed across:

1. **Essential knowledge** — terminology, definitions, facts, processes and required notation.
2. **Explanation and comparison** — particle explanations, cause and effect, similarities, differences and linked ideas.
3. **Application and misconception** — unfamiliar situations, common errors, prediction and correction of faulty reasoning.
4. **Calculation, interpretation and diagram** — quantitative work, tables, graphs, experimental observations and reviewed visual assets where the source supports them.

Question variations must test a distinct cognitive action. A definition, explanation, application and misconception check may share one concept; superficial rewordings of the same recall question do not count as useful variation.

## Low-token operating model

- Build the concept inventory deterministically from published topic headings, reviewed learning objectives and approved source passages.
- Draft cards in one bounded batch per topic. Human-authored cards are valid; an OpenAI batch may assist drafting only when requested.
- If OpenAI is used, send only the minimum reviewed passages required for the current concept and request structured JSON in a single call or small bounded batches.
- Cache the draft against the topic content-version checksum, prompt version and model. Do not regenerate unchanged concepts.
- Run formatting, duplication, grounding, notation and coverage checks locally without OpenAI.
- Use human review for final factual and pedagogical approval.
- Import the approved artifact once. Student study, selection and scheduling remain deterministic and consume no model tokens.
- Reuse an approved card library until its source content changes or a reviewed correction is required.

## Step 0 — Freeze the current pilot deck and record the replacement

- [x] Keep the existing 30-card production deck unreleased.
- [x] Export its deck reference, topic reference, content version and status as migration evidence.
- [x] Retain it as a non-released historical pilot after the curated deck is imported; it remains unavailable to Students.
- [x] Record that this roadmap supersedes **Admin Step 8 — Generate the Topic 1 flashcard deck** in `TODO-FUTURE-HIGH-LEARNING.md`.

**Done when:** the weak pilot cannot become Student-visible accidentally and its disposition is auditable.

## Step 1 — Remove generation from the Admin product

- [x] Remove the **Create a draft deck**, topic selector, maximum-card input and **Generate grounded draft** action from the Admin Flashcard page.
- [x] Retain a read-only deck catalogue showing subject, unit, topic coverage, content version, card count, validation result, release state and release date.
- [x] Replace generation guidance with a short message that reviewed flashcard releases are prepared from published textbook content.
- [x] Retire the browser-facing Admin generation API after the curated import path is operational.
- [x] Keep authorization and audit protection around all remaining Admin deck operations.
- [x] Update Admin documentation, API contracts and frontend tests.

**Done when:** no Admin control or public application workflow can generate arbitrary flashcards.

## Step 2 — Define the curated flashcard artifact

- [x] Define a versioned JSON schema for a unit or topic flashcard release.
- [x] Include release ID, course, subject, textbook, unit, included topic references, topic content versions, generator/editor provenance, schema version and creation timestamp.
- [x] Give every card a stable external key, concept key, category, difficulty, variation type, question, approved answer and display order.
- [x] Bind every factual card to one or more active retrieval chunk references and their immutable content-version references.
- [x] Support an optional approved visual-asset reference and accessible description for diagram cards.
- [x] Store a checksum for the complete artifact and checksums for the source content versions.
- [x] Exclude copyrighted source passages from Git-tracked artifacts unless repository policy explicitly permits them; resolve authoritative passages by source reference during validation/import.
- [x] Provide an example artifact containing a small, synthetic set of cards.

**Done when:** a release is portable, reviewable, reproducible and cannot silently point at changed textbook evidence.

## Step 3 — Build deterministic quality validation

- [x] Reject missing questions, answers, concepts, categories, citations or topic ownership.
- [x] Reject source references outside the declared subject, textbook, unit, topic or published content version.
- [x] Reject superseded, unpublished, visual-reference-only or unauthorized OCR evidence.
- [x] Detect exact and near-duplicate questions and answers within a concept, topic and unit.
- [x] Detect answers that merely repeat the question, incomplete sentence fragments, page labels, headings, learning objectives and isolated figure captions.
- [x] Enforce readable question and answer length limits while allowing justified worked explanations.
- [x] Validate required structured categories and suspicious Chemistry OCR substitutions such as `HCI` for `HCl`; formulae, units and state notation remain part of human release review.
- [x] Require diagram cards to reference an approved visual asset and supply meaningful alternative text.
- [x] Produce category, concept, topic, difficulty and variation coverage reports.
- [x] Fail the release when a required concept has no suitable card or when added variations are only superficial rewordings.

**Done when:** one local command produces a clear pass/fail report without using OpenAI.

## Step 4 — Prepare the Chemistry Unit 1 concept inventory

- [x] List every examinable learning point from each independently published Unit 1 topic.
- [x] Map each learning point to exact reviewed textbook evidence and printed pages.
- [x] Mark whether the concept needs essential knowledge, explanation/comparison, application/misconception, calculation/interpretation or diagram coverage.
- [x] Assign an initial number of useful variations based on importance and likely misconceptions.
- [x] Produce a proposed card count from the inventory rather than forcing exactly 100.
- [x] Allow Topic 1 — States of Matter to be released independently while later Unit 1 topics remain unavailable.
- [x] Recalculate the Unit 1 total as later topics are published without changing stable Topic 1 card identities.

The first inventory contains 72 reviewed cards for the only currently published Unit 1 topic: 20 essential knowledge, 22 explanation/comparison, 18 application/misconception and 12 calculation/interpretation cards. Later topic releases extend the unit total using stable topic and card keys.

**Done when:** every proposed card has a reason to exist and the report explains whether approximately 100 cards adequately cover the published unit.

## Step 5 — Author and approve the curated cards

- [x] Draft concise iGCSE-level questions and approved answers for the concept inventory.
- [x] Use purposeful variations: recall, explanation, comparison, application, misconception, calculation, interpretation or diagram.
- [x] Keep each card focused on one assessable learning action unless a linked multi-step calculation requires more.
- [x] Verify every answer against its cited passage and any applicable Edexcel terminology.
- [x] Review formulae, units and scientific notation manually; this release does not contain diagram cards because no approved visual was required.
- [x] Record reviewer identity, review time, review decision and notes in the release evidence.
- [x] Run the deterministic validator and resolve every blocking issue before import.
- [x] Sample the final distribution to ensure easy recall cards do not crowd out explanation and application.

**Done when:** the artifact passes automated checks and a human reviewer signs off its factual accuracy, age suitability and coverage.

## Step 6 — Import and release safely

- [x] Build an idempotent backend import command or protected operator endpoint using the artifact release ID and checksum.
- [x] Support `validate` and `dry-run` modes that make no database changes.
- [x] Resolve every source reference against the target environment before writing cards.
- [x] Create the deck and immutable card versions in one transaction; roll back the complete import on any failure.
- [x] Record import actor, Git revision, artifact checksum, source content versions and validation report in the audit log.
- [x] Refuse an altered artifact that reuses an existing release ID.
- [x] Allow a new release to supersede an earlier released deck without deleting historical sessions or ratings.
- [x] Provide an explicit rollback that removes Student visibility from the new release and restores the previous valid release where appropriate.
- [x] Keep production credentials and textbook-derived release artifacts outside Git and transfer them through the established secure deployment process.

**Done when:** the same reviewed artifact can be proven locally, imported once in production and rolled back without direct database editing.

## Step 7 — Add Student study-mode selection

- [x] Add **Quick review** with 10 selected cards.
- [x] Add **Normal review** with 20 selected cards.
- [x] Add **Full topic practice** containing all eligible cards for one topic.
- [x] Add **Difficult cards** using the Student's prior `Again` and `Difficult` ratings.
- [x] Add **Due today** using persisted review due dates.
- [x] Add **Unit mixed practice** across eligible published topics within the selected unit.
- [x] Show the exact mode, available-card count and estimated session size before starting.
- [x] Provide clear empty states when no difficult, due or eligible cards exist.
- [x] Preserve keyboard, screen-reader, answer-reveal and exact-source behaviour.

**Done when:** a Student can intentionally choose a short review, a complete topic or a mixed unit session without being forced through the entire library.

## Step 8 — Build deterministic adaptive card selection

- [x] Snapshot selected card-version IDs when a session starts so an in-progress session remains stable.
- [x] Select cards in this order: overdue; previously rated `Again` or `Difficult`; concepts associated with the Student's recorded weak areas; unseen cards; limited alternate variations of mastered concepts.
- [x] Define deterministic tie-breakers and a versioned selection-policy name.
- [x] Cap cards from one concept so a short session remains varied.
- [x] Avoid showing two close variations of the same concept consecutively unless the mode explicitly targets that concept.
- [x] Use only cards from released decks, published content versions and the Student's cumulative Grade/Term coverage.
- [x] Keep selection family- and child-scoped; one child's ratings must never affect another child.
- [x] Store the selection reason for each session card for later explanation and evaluation.

**Done when:** identical Student state and policy version produce an explainable, repeatable selection with no OpenAI call.

## Step 9 — Complete spaced repetition and progress

- [x] Replace the current fixed interval recording with a reviewed, versioned deterministic scheduling rule.
- [x] Update per-child, per-card review state after `Again`, `Difficult`, `Good` or `Easy`.
- [x] Use due dates during **Due today**, Quick and Normal selection.
- [x] Preserve history when a materially identical card with the same stable key enters a later release; changed cards begin new learning state.
- [x] Show due, new, learning and difficult counts without presenting recall ratings as formal academic marks.
- [x] Let a Student stop a session and resume the same snapshotted cards safely.
- [x] Ensure repeated requests cannot duplicate ratings or advance a session twice.

**Done when:** ratings change future deterministic selection and a completed session no longer merely restarts every card from the beginning.

## Step 10 — Improve Admin visibility without restoring generation

- [x] Show imported release validation, category distribution, topic coverage, concept coverage, duplicate count and source-version health.
- [x] Show whether a release is awaiting release, released or superseded, plus its separate validation result; withdrawal uses the audited superseded state.
- [x] Let the Admin withdraw or roll back a release with an audited reason.
- [x] Do not provide question-generation, prompt, model or arbitrary bulk-edit controls in the Admin UI.
- [x] Retain exact source inspection for support and audit purposes.

**Done when:** the Admin can understand and control availability without becoming responsible for generating the library.

## Step 11 — Test and release incrementally

- [ ] Test artifact schema, checksum, dry run, idempotency, invalid evidence, cross-subject evidence, stale content versions and transactional rollback.
- [ ] Test duplicate detection, formula validation, variation limits and category coverage.
- [ ] Test all six Student modes with zero, few and many eligible cards.
- [ ] Test overdue, difficult, weak, unseen and alternate-variation selection order.
- [ ] Test session resume, concurrent ratings, superseded cards and prior history.
- [ ] Test Student isolation, cumulative Grade/Term eligibility and unavailable sibling topics.
- [ ] Test keyboard operation, screen-reader announcements, small screens and 100-card library performance.
- [ ] Import first into a disposable/local database and preserve the validation report.
- [ ] Release Topic 1 to a selected pilot Student before expanding to all published Unit 1 topics.
- [ ] Record production acceptance evidence and the rollback procedure.

**Done when:** the curated library passes quality, authorization, accessibility, scheduling and production acceptance gates.

## Suggested implementation order

1. Steps 0–3: remove Admin generation and establish the safe artifact/validator boundary.
2. Steps 4–5: prepare and approve the States of Matter library with a justified card count.
3. Step 6: import the curated Topic 1 release safely.
4. Steps 7–9: add Student modes, adaptive selection and functioning spaced repetition.
5. Steps 10–11: finish operational visibility, verification and controlled release.

The first usable release may use the existing sequential Student interface immediately after Step 6. Steps 7–9 improve how a larger library is selected and revisited without requiring the approved cards to be regenerated.

## Completion gate

- [ ] No Admin-facing flashcard generation remains.
- [ ] The reviewed card count is justified by published Unit 1 concept coverage.
- [ ] Every card has approved evidence and a meaningful category and variation type.
- [ ] Import is validated, idempotent, audited and reversible.
- [ ] Routine Student flashcard use consumes no OpenAI tokens.
- [ ] Students can use all six study modes with deterministic child-scoped selection.
- [ ] Ratings affect future reviews through a tested versioned scheduling policy.
- [ ] The production pilot passes authorization, source-grounding, quality, accessibility and rollback checks.

**Done when:** AKURU provides a high-quality, maintainable Unit 1 flashcard library whose size follows syllabus coverage, whose questions remain tied to reviewed textbook evidence, and whose daily Student experience is adaptive without recurring AI cost.
