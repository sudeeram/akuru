# High priority — Chemistry Topic 1 readiness, text tutoring and flashcards

**Status: In progress. Core flashcard persistence, review/release APIs, Student sessions and accessible interfaces are implemented locally.**

This is the first delivery plan. Its immediate objective is to let Students use the reviewed `Edexcel-iGCSE-Chemistry-Unit-1-Topic-1-States-of-Matter-v2.1.pdf` content through grounded text tutoring and accessible flashcards. Work in this file takes precedence over the medium, low and lowest-priority future plans.

## Delivery sequence

1. Make the reviewed v2.1 document and topic status consistent everywhere.
2. Establish one canonical primary text source and prevent the original scan from duplicating retrieval evidence.
3. Prove the published Chemistry Topic 1 retrieval and citation path.
4. Separate model policy from provider-account priority for Student text learning.
5. Complete and verify grounded text tutoring, Guided Practice and misconception support.
6. Build, evaluate and release flashcards.
7. Enable the Student navigation only after the feature release gates pass.

## Chemistry Topic 1 launch prerequisites

Local implementation support completed on 19 September 2026 (not deployed):

- [x] One authoritative extraction-review completion transition now synchronizes the document version, Library review state and every active topic attachment.
- [x] The Admin topic source manager supports `primary`, `supporting`, `reference` and `visual_reference` roles with clear retrieval effects.
- [x] Visual-reference OCR is excluded from readiness, quality gating, publication manifests and normal retrieval indexing.
- [x] Existing published source manifests remain immutable when an Admin changes the role used by the next topic publication.
- [x] The migration, authenticated Admin APIs, frontend controls, API contract and regression checks are ready for a later reviewed deployment.

The production-specific checks below remain open until this code is deployed and an Admin applies it to the two Chemistry files. No production record was changed by this implementation.

- [ ] Confirm v2.1 has no unresolved required page or block reviews.
- [ ] Confirm the document version, library review state and active topic-document link agree.
- [ ] Designate v2.1 as the canonical primary text for Topic 1 — States of Matter.
- [ ] Keep the original scan as a visual reference and exclude its duplicate OCR text from normal retrieval.
- [ ] Publish a reviewed Topic 1 content version with exact document/page provenance.
- [ ] Run retrieval checks for representative States of Matter questions before enabling Student use.
- [ ] Confirm Student enrolment and term coverage make Topic 1 eligible for the intended pilot account.
- [ ] Keep the release limited to Admin testing until citation, Tutor and flashcard evaluations pass.

## Admin launch workflow — first usable Chemistry flashcard and Tutor release

The first Student release must work from one independently published topic. AKURU must not require every topic in Unit 1, every Chemistry unit or the complete textbook to be published before Students can use Topic 1 — States of Matter. A Unit-level deck may contain only currently eligible published topics, but the Student interface must label that partial coverage accurately.

### Admin Step 1 — Confirm the textbook hierarchy

- [ ] Confirm the Edexcel iGCSE Chemistry textbook, Unit 1 group and Topic 1 — States of Matter records exist and have stable public references and subject ownership. *(The authenticated hierarchy and ownership validation are implemented; this remains an environment-specific launch check. The local database currently has no Chemistry hierarchy.)*
- [ ] Verify Unit 1 is represented as a textbook group and States of Matter as a child topic rather than attaching the PDF directly to an unrelated unit or subject. *(The enforced parent-child model is implemented; verify the production records after deployment.)*
- [x] Permit the remaining Unit 1 topics and later units to be created and published incrementally without changing the released Topic 1 identity.
- [x] Show the Admin the number of total, reviewed, published and Student-eligible topics within Unit 1.

### Admin Step 2 — Select the canonical Topic 1 source

- [x] Provide the source-manager controls required to set `Edexcel-iGCSE-Chemistry-Unit-1-Topic-1-States-of-Matter-v2.1.pdf` as the canonical `primary` text source.
- [ ] Change the original scan to `visual_reference`, preserve its provenance and exclude its duplicate OCR text from ordinary retrieval.
- [x] Preview exactly which document versions, text blocks and optional visual assets will enter the next published Topic 1 version.
- [x] Block publication when two materially duplicate sources are still selected as canonical primary text.

### Admin Step 3 — Complete extraction review

- [ ] Show one authoritative Topic 1 review checklist covering remaining pages, remaining blocks, reading order, Chemistry notation, required tables and selected visual assets.
- [x] Mark v2.1 reviewed only when no required page or block remains unresolved and synchronize that state across Library, document version and topic attachment.
- [x] Provide an actionable reason and direct review-page links for every item still blocking publication.
- [x] Keep completion of extraction review separate from the explicit publication action.

### Admin Step 4 — Publish Topic 1 independently

- [x] Let the Admin publish the reviewed States of Matter topic without publishing all of Unit 1 or any other Chemistry unit.
- [x] Create an immutable published content version containing the reviewed primary text, selected reviewed assets, exact document/page provenance and retrieval manifest.
- [x] Exclude unpublished sibling topics from Student retrieval, Tutor context and flashcard generation.
- [x] Display `1 published topic` or equivalent partial-coverage wording for Unit 1 instead of implying that the entire unit is available.

### Admin Step 5 — Add grade and term coverage

- [x] Let the Admin add the published States of Matter topic to an effective iGCSE Chemistry Grade 10 or Grade 11 term-coverage version.
- [x] Preserve cumulative progression so a topic covered in Term 1 remains eligible in Terms 2 and 3 for the same grade, subject and course.
- [x] Prevent draft, future, withdrawn or unpublished coverage from granting Student access.
- [x] Show which published topics in Unit 1 are covered for each grade/term combination before activation.

### Admin Step 6 — Verify Student enrolment and eligibility

- [x] Provide an Admin readiness view confirming the pilot Student is active, enrolled in iGCSE, assigned Chemistry and associated with an eligible grade/term progression record.
- [x] Calculate Student access from account, course, subject, progression, coverage and publication state; do not require a separate manual deck assignment for every child.
- [x] Explain the exact missing prerequisite when a Student is ineligible, without exposing internal UUIDs.
- [ ] Test Laura/Enya-style separation so an eligible child cannot read another child's flashcard history, Tutor transcript or source authorization.

### Admin Step 7 — Verify retrieval and citations

- [x] Add an Admin preflight that runs representative States of Matter retrieval checks before Tutor or flashcard release.
- [x] Include checks for the three states of matter, particle arrangement, melting, diffusion and sublimation where the reviewed source supports them.
- [x] Require each accepted result to resolve to the canonical v2.1 document version, correct topic, exact page reference and authorized passage.
- [x] Fail the preflight for duplicate scan/v2.1 evidence, cross-subject results, unpublished passages, missing page provenance or insufficient evidence.
- [x] Save the preflight configuration and result as release evidence without treating generated answers as source truth.

### Admin Step 8 — Generate the Topic 1 flashcard deck

- [x] Add an Admin action to generate a deck for one selected published topic.
- [ ] Optionally add a Unit 1 generation action that includes only eligible published topics.
- [ ] Show the generation scope before confirmation, including course, subject, unit, included topics, source version and proposed card limit.
- [x] Persist the generated deck and immutable card versions with front, back, source evidence, page citation, model/prompt version and generation status.
- [x] Prevent generation from unpublished, superseded, rejected or visual-reference OCR text.
- [x] Make generation idempotent by request key. Material duplicate warnings remain part of the wider quality pass.

### Admin Step 9 — Review and release the deck

- [x] Provide an Admin deck-review queue with card front/back, source passage, page reference, topic and validation warnings; generation provenance is persisted for audit.
- [x] Let the Admin edit, approve or reject individual cards by creating immutable versions without silently changing an already released card version. Individual regeneration remains pending.
- [ ] Require clear wording, factual correctness, appropriate iGCSE level, correct formula/notation, non-duplication and direct approved evidence before approval.
- [x] Prevent release while any included card lacks approved evidence or remains review-required.
- [x] Release an immutable deck version through a separate explicit action and retain prior released versions for historical Student-session integrity.

### Admin Step 10 — Enable and verify the Student experience

- [ ] Enable the flashcard and text-Tutor release gates first for Admin testing, then the selected Student pilot, with an immediate rollback switch.
- [ ] Show a descriptive Student message when the required AI provider is unavailable.
- [x] Add Student navigation to flashcards; deck visibility remains closed until Admin release and cumulative curriculum eligibility pass.
- [ ] Show Unit 1 with the exact number of published eligible topics and never display an unavailable sibling topic as usable content.
- [x] Let the Student select States of Matter, start or resume a flashcard session, reveal answers, rate recall, open exact sources and complete the session using keyboard and screen reader.
- [x] Let the Student start a grounded text Tutor session for the same eligible topic, ask questions and receive exact reviewed citations.
- [ ] Run a production-like acceptance journey as the pilot Student and verify that an ineligible Student cannot see or call the same deck and Tutor context.
- [ ] Record the release decision, evaluation evidence, active deck/content versions and rollback procedure for the first Student launch.

### End-to-end Admin readiness summary

- [x] Add one Admin summary showing `Textbook structure`, `Source selected`, `Extraction reviewed`, `Topic published`, `Coverage active`, `Student eligible`, `Retrieval passed`, `Deck generated`, `Deck released` and `Student access enabled`.
- [x] Make every failed item link to the exact Admin screen and record that must be corrected.
- [x] Do not show the overall state as ready until all ten steps pass for at least one pilot Student.
- [x] Document the repeatable process for adding the next Chemistry topic without requiring changes to already published Topic 1.

## Future Step 3 — Synchronize completed review status across the library and topics

### Problem recorded

The Admin can clear the final review-required page or block and make the attached textbook part `ready`, while **Review documents** still displays the document version as `needs_review`. The topic link and library card currently derive their status from different persisted fields, so they can disagree after the final review save.

### Backend state transition

- [x] Define one authoritative review-completion rule: at least one extracted page exists and no page or block remains `needs_review`.
- [x] After every page or block review save, calculate completion once and synchronize the document version, document review state and every active topic-document link in the same database transaction.
- [x] Move a fully reviewed document version from `needs_review` to `completed` and its document review state from `pending` to `reviewed`, unless a stronger terminal state such as `published`, `rejected`, `removed`, `failed` or `superseded` applies.
- [x] Move an active topic-document link to `ready` only when the same authoritative rule passes.
- [x] Preserve publishing as a separate explicit Admin action; completing extraction review must never publish content automatically.
- [x] Handle documents that are not attached to a textbook topic so their library status still becomes accurate.
- [x] Keep the transition idempotent and write an audit event when the overall review first becomes complete.
- [x] Provide a reviewed repair/backfill operation for existing records whose topic link is `ready` while the document or version still says `pending` or `needs_review`.

### Admin experience

- [x] Make **Review documents** use the synchronized overall review status and show `Reviewed` or `Completed` after the final required item is saved.
- [x] Refresh the library record immediately after a review save so the Admin does not need to reload the page manually.
- [x] Keep `Ready for topic publication` distinct from `Published` in labels and accessible status text.
- [x] Show a clear remaining-page and remaining-block count whenever the document genuinely still needs review.

### Verification and completion criteria

- [x] Add a regression test in which the last outstanding block is reviewed and all document, version, library and topic-link responses become consistent.
- [ ] Test the last outstanding page-only review, documents without topic links and documents attached to a topic.
- [ ] Test that failed, removed, rejected, superseded and published states are not incorrectly downgraded or overwritten.
- [ ] Test immediate frontend refresh and ensure a completed document disappears from the `needs_review` list without a full browser reload.
- [ ] Run the repair operation against a disposable copy of production data and report every proposed change before applying it in production.

**Done when:** Saving the final required review produces one consistent, auditable completed state everywhere, the library no longer shows a reviewed document as `needs_review`, and no review action publishes content automatically.


## Future Step 4 — Manage primary, supporting and visual-reference sources

### Problem recorded

The original scanned Chemistry PDF and its clean v2.1 text PDF are both attached to the same topic as `primary`. This makes AKURU evaluate both as publishable text sources, permits duplicate retrieval content and makes unresolved OCR reviews in the scan block publication even when the canonical v2.1 text has been fully reviewed.

The intended configuration for this case is:

- v2.1 text PDF: canonical `primary` source for reviewed text, citations and retrieval;
- original scanned PDF: `visual_reference` source retained for provenance, comparison and selected reviewed diagrams, with its OCR text excluded from ordinary retrieval.

### Domain model and source lifecycle

- [x] Define clear semantics for `primary`, `supporting`, `reference` and `visual_reference` topic attachments, including which content each role may contribute.
- [x] Require at least one reviewed primary source before topic-content publication.
- [x] Prevent two sources containing materially duplicate canonical text from silently operating as equal primary sources.
- [x] Allow an Admin to change an unpublished attachment's role without re-uploading the document.
- [x] Allow an Admin to detach a source from a topic without deleting the underlying document, extraction evidence or audit history.
- [x] Protect sources already used by a published content version: later role changes or detachment must create a new draft version while existing citations remain bound to their published source manifest.
- [x] Retain checksums, source versions, extraction versions, role history and actor/time audit evidence for every change.
- [x] Define deterministic ordering when a topic legitimately has multiple non-duplicate primary or supporting parts.

### Role-specific review and publication gates

- [x] Require all primary text sources included in the next content version to complete extraction review and pass the document-quality gate.
- [ ] Include supporting text in publication only when explicitly selected and fully reviewed.
- [x] Do not make unresolved OCR text from a visual-reference source block publication when none of that text or its assets is selected for the content version.
- [ ] Require every diagram, image, table or page crop selected from a visual reference to be reviewed before it can be published or shown to students.
- [x] Show exactly which sources and assets will enter the next topic-content version before the Admin confirms publication.
- [x] Fail closed when a selected source or visual becomes unavailable, changes version or loses its reviewed state.

### Retrieval, citations and duplicate protection

- [x] Index reviewed primary text by default and exclude visual-reference OCR text from ordinary retrieval.
- [ ] Permit approved visual assets from a visual reference to retain exact document, version, page and bounding-box citations without indexing unrelated OCR text.
- [x] Detect likely duplicate passages across attached documents and warn the Admin before publication.
- [x] Prevent duplicate chunks from inflating relevance scores or causing AKURU to present repeated evidence.
- [ ] Preserve source-role and source-version information in retrieval chunks, Tutor citations and assessment evidence.
- [x] Keep historical published chunks immutable when later source roles change.

### Admin experience

- [x] Add a topic source manager showing filename, version, role, review status, inclusion in the next publication and existing published-version usage.
- [x] Let an Admin change roles using clear choices and explanations of retrieval and publication effects.
- [x] Provide **Detach from topic** separately from **Remove document**, with an impact preview and confirmation.
- [ ] Allow selection and review of individual visual assets from a visual-reference document.
- [x] Display duplicate-content warnings and identify the proposed canonical source.
- [x] Distinguish `Ready primary text`, `Visual reference`, `Excluded from retrieval`, `Blocking publication` and `Used by published version` with accessible text rather than colour alone.

### Current Chemistry transition

- [ ] After this feature is implemented and verified, prepare a dry-run migration for Topic 1 — States of Matter.
- [ ] Keep `Edexcel-iGCSE-Chemistry-Unit-1-Topic-1-States-of-Matter-v2.1.pdf` as the canonical primary source.
- [ ] Change `Edexcel-iGCSE-Chemistry-Unit-1-Topic-1-States-of-Matter.pdf` from primary to visual reference without deleting it.
- [ ] Exclude the original scan's duplicate OCR text from the next retrieval index.
- [ ] Retain the scan for provenance and later selection of reviewed diagrams.
- [ ] Re-run topic readiness, quality and retrieval-duplication reports before publishing.
- [ ] Present the proposed production changes for review before applying them.

### Verification and completion criteria

- [ ] Test role changes, detachment, reattachment, ordering and audit history before initial publication.
- [ ] Test that an unselected visual reference with unresolved OCR does not block reviewed primary text, while an unreviewed selected visual does block publication.
- [ ] Test duplicate detection and verify that duplicate sources cannot create repeated active retrieval chunks.
- [ ] Test published-version immutability, new-draft creation and exact historical citations after role changes.
- [ ] Test authorization, CSRF protection, family/student isolation and concurrent Admin updates.
- [ ] Test the source manager with keyboard and screen reader and provide understandable impact messages.

**Done when:** An Admin can designate one canonical reviewed text source, retain scans as non-duplicating visual references, detach sources without deleting evidence, preview exactly what will be published, and produce retrieval and citations without duplicated textbook content.


## Future Step 6 — Add feature-specific model routing and quality escalation

### Separate provider accounts from model policy

- [ ] Remove the assumption that the first provider account's model determines the required model for every request.
- [ ] Keep provider-account priority responsible for selecting the credential and account used to execute a request.
- [ ] Introduce a versioned model-policy configuration responsible for selecting the primary model, optional escalation model, reasoning effort, output limit and enabled state for each supported feature.
- [ ] Allow one provider credential to execute multiple models without duplicating the credential or weakening the existing unique account-priority rules.
- [ ] Define how an account declares or discovers model availability and fail closed when no healthy account can execute the selected model.
- [ ] Preserve the existing account cooldown, invalid-credential, exhausted-credit and retry behaviour underneath model selection.
- [ ] Add a reviewed migration from the existing account-bound model configuration without exposing or rewriting credentials.

### Initial feature policies

- [ ] Define the first controlled policy keys for `tutor_economy`, `tutor_standard` and `flashcards`; extend the same framework to assessment, study-plan, document and voice policies only in their assigned lower-priority plans.
- [ ] Route flashcards, factual recall and routine guided practice to the economy Tutor policy by default.
- [ ] Route detailed explanations, misconception correction, repeated incorrect answers, complex equations, multi-step calculations and evidence-sensitive teaching directly to the standard Tutor policy.
- [ ] Preserve the current independently gated assessment-marking behaviour; do not make assessment-policy redevelopment a prerequisite for the text Tutor and flashcard pilot.
- [ ] Keep document extraction and interpretation outside the high-priority Student policy so later OCR experiments cannot silently alter Tutor behaviour.
- [ ] Define explicit defaults and a safe disabled state for every policy so a missing configuration never results in an arbitrary model choice.

### End-to-end feature readiness inventory

- [ ] Produce one reviewed matrix for every AI-backed feature showing its user role, frontend entry point, backend API, domain service, prompt, output schema, primary policy, escalation policy, release gate, audit evidence and automated tests.
- [ ] Classify every feature as `ready`, `partially_ready`, `backend_only`, `frontend_only` or `not_started`; do not treat a prompt definition or API contract alone as a usable feature.
- [ ] Cover at least flashcards, short revision questions, guided practice, Socratic practice, detailed explanations, misconception correction, repeated-error help, difficult calculations, assessment marking, study-plan wording, document classification, document interpretation and realtime voice delegation.
- [ ] Record the existing Guided Practice workflow as implemented but requiring model-policy integration and regression verification.
- [ ] Record short revision questions as partially ready because conversational `questions` and `revision` Tutor modes exist without a structured activity lifecycle.
- [x] Record flashcards as implemented for persistence, deterministic scheduling, authenticated APIs, Admin review/release and the accessible Student experience; policy routing and controlled pilot gates remain pending.
- [ ] Remove or update stale Student-interface text that says the Tutor backend is a future feature, and link legacy Practice surfaces to the active Tutor Room where appropriate.
- [ ] Keep policy activation disabled for any feature whose required frontend, backend, evidence or release-gate row is incomplete.

### Student flashcards — frontend and backend readiness

- [x] Define persisted flashcard decks, immutable card versions, reviewed source references, card fronts/backs, eligible topic scope, generation provenance and lifecycle states.
- [x] Generate cards only from published, authorized textbook-topic content and preserve exact passage/page citations for every factual answer.
- [ ] Add deterministic duplicate, empty-answer, excessive-length, unsupported-formula and insufficient-evidence checks before cards can become available.
- [ ] Route routine card drafting through `tutor_economy`; escalate only cards that fail approved grounding, notation or complexity checks.
- [x] Require explicit Admin review and release for generated decks. The additional controlled pilot evaluation gate remains pending.
- [x] Add authenticated Student APIs to list eligible decks, start/resume a review, reveal an answer, rate recall and complete a session.
- [x] Add idempotent persistence for each response using controlled ratings `again`, `difficult`, `good` and `easy`.
- [x] Implement a deterministic spaced-repetition scheduler; keep scheduling outside the language model and version the scheduling rules.
- [x] Build an accessible Student flashcard experience with topic/deck selection, card count, reveal control, keyboard operation, progress, completion summary and exact-source access.
- [x] Show an understandable empty state when no reviewed cards or published topic sources are available.
- [ ] Add Parent progress summaries and Admin deck-quality/status views without exposing another family's activity.
- [x] Ensure flashcard ratings do not directly change authoritative mastery unless a separately reviewed evidence-weighting rule explicitly permits it.
- [x] Add backend scheduling and API-contract tests plus frontend accessibility and feature-contract tests.
- [ ] Add full database-backed domain, authorization, idempotency, grounding, cross-child isolation, keyboard and browser-flow tests.
- [ ] Add model-routing and escalation tests when those capabilities are implemented.

### Guided and Socratic practice — completion and routing review

- [ ] Preserve the existing Tutor Room workflow for starting one eligible topic question, viewing assets, obtaining hints, saving an answer, submitting it and displaying authoritative assessment feedback.
- [ ] Preserve the separate Student Practice workflow and define when navigation should open Tutor Guided Practice versus standalone assessment practice.
- [ ] Attach an explicit model-policy key to Tutor guidance, hint explanation and submitted-answer feedback without changing the immutable assessment question snapshot.
- [ ] Use the economy policy for routine hints and step-by-step prompts; route repeated misunderstanding, complex calculations and evidence-sensitive explanations to the standard policy.
- [ ] Ensure AI-generated guidance never awards marks; keep marking decisions and improved answers within the authorized assessment-marking workflow.
- [ ] Prevent hints, Tutor voice and answer-revealing tools during mocks and official-paper attempts.
- [ ] Retain an active question and its saved answer when switching tutors, and continue blocking topic changes until required submission rules are satisfied.
- [ ] Show the final model/policy outcome only when useful to Admin audit; do not expose internal confidence, account identity or escalation mechanics to the child.
- [ ] Regression-test published coverage eligibility, question-topic mapping, diagrams, progressive hints, answer persistence, assessment feedback, Tutor switching and release gates.

### Detailed teaching, misconceptions and difficult calculations

- [ ] Give each Tutor teaching mode a typed task category and explicit policy instead of routing every request under undifferentiated `tutoring` behaviour.
- [ ] Route detailed explanations, low-mastery teaching, repeated-error help, misconception correction and multi-step calculations directly to `tutor_standard` when deterministic evidence already establishes complexity.
- [ ] Preserve approved textbook citations and learner-context evidence for every claim about the student's strengths, weaknesses or repeated mistakes.
- [ ] Add subject-aware deterministic validators for supported numerical answers, units, chemical formulae and equation formatting before accepting economy-model output.
- [ ] Provide accessible visual and text alternatives when an explanation uses diagrams, equations or textbook imagery.
- [ ] Make insufficient evidence visible as an actionable Student message rather than producing an unsupported answer or unnecessary model escalation.
- [ ] Add evaluation cases covering Chemistry notation, unit conversion, multi-step working, common misconceptions, conflicting evidence and repeated student errors.

### Deterministic request classification

- [ ] Add a typed routing hint or policy key to `AIRequest`; do not infer routing from free-form prompt text inside the account router.
- [ ] Build a deterministic Tutor complexity classifier using information AKURU already owns, including teaching mode, requested activity, student mastery, recent repeated errors, misconception history, calculation depth, required citations and evidence sufficiency.
- [ ] Record the classifier version, inputs, resulting policy and human-readable routing reasons for each invocation.
- [ ] Route clearly complex or high-consequence requests directly to Terra instead of paying for a Luna attempt first.
- [ ] Keep the classifier bounded and testable; do not make a separate AI request merely to choose the model in the initial release.
- [ ] Ensure the classifier cannot use another child's history or material outside the student's authorized course, subject and topic scope.

### Luna-to-Terra quality escalation

- [ ] Extend the applicable structured provider output with internal confidence, escalation-needed and controlled escalation-reason fields that are not presented as established facts to the student.
- [ ] Validate required citations, source grounding, structured-output completeness, calculation checks and safety/evidence gates before releasing an economy-model answer.
- [ ] Escalate when required evidence is missing, the answer cannot be validated, a repeated misconception remains unresolved, a calculation fails checking, the student challenges a material conclusion, or an approved controlled reason applies.
- [ ] Send Terra the original authorized context, the Luna draft and the validation reason without expanding the student's data scope.
- [ ] Show only the final accepted answer to the student and preserve both attempts for authorized audit and evaluation.
- [ ] Prevent escalation loops and limit each logical request to the configured bounded attempt path.
- [ ] Distinguish quality escalation from account failover: model escalation changes capability, while account failover retries the same required model on another healthy credential.

### Admin configuration and reporting

- [ ] Add authenticated Admin APIs and an accessible Admin interface for viewing and editing feature policies.
- [ ] Offer a controlled, server-validated model list rather than accepting arbitrary model names without validation.
- [ ] Let an Admin configure the primary model, optional escalation model, reasoning effort, maximum output tokens, escalation state and policy status.
- [ ] Version policy changes, require a reason, write audit events and support rollback to a previously reviewed version.
- [ ] Keep credential aliases and priorities in the provider-account interface; clearly explain the difference between account failover and model routing.
- [ ] Report requests, input/output tokens, estimated cost, latency, failure rate and quality-escalation rate by feature, policy, model and account as authorization permits.
- [ ] Show why a request escalated and link the two provider attempts under one logical operation without exposing prompts, credentials or another student's data.

### Usage and cost accounting

- [ ] Record selected policy, classifier version, routing reason, requested model, actual model, reasoning effort, escalation parent/child relationship and final disposition for every invocation.
- [ ] Count both Luna and Terra usage when escalation occurs using provider-reported usage where available.
- [ ] Ensure account retry attempts, quality escalations and client retries cannot double-count provider usage.
- [ ] Add configurable price metadata or a versioned cost catalogue for reporting estimates; do not hard-code current public prices into historical usage records.
- [ ] Store the pricing version and calculated estimate so later price changes do not rewrite historical reports.
- [ ] Alert Admins when escalation frequency or cost exceeds configured operational thresholds.

### Evaluation and controlled release gates

- [ ] Build representative high-priority evaluation sets for Chemistry explanations, factual recall, flashcards, Guided Practice, misconception correction, repeated errors, calculations, citations and insufficient-evidence cases.
- [ ] Compare Luna-only, Terra-only and Luna-with-escalation behaviour for correctness, citation accuracy, mark-scheme alignment, successful-task cost, latency and student-appropriate language.
- [ ] Define release thresholds before enabling automatic routing, including high recall for answers that genuinely require escalation and an acceptable false-escalation rate for routine work.
- [ ] Start in shadow mode: calculate and record the proposed policy while retaining the currently approved model response.
- [ ] Review shadow results, then enable the feature for controlled students or subjects with a one-switch rollback to the previous fixed-model behaviour.
- [ ] Include provider unavailability, exhausted accounts, malformed structured output, timeouts and concurrent-request tests.
- [ ] Run authorization, audit, privacy, prompt-injection, source-grounding and cross-family isolation tests for both the initial and escalated attempts.
- [ ] Re-evaluate high-priority policies when model versions, provider prices, Tutor/flashcard prompts or published Chemistry evidence changes.

**Done when:** AKURU independently selects reviewed text-Tutor and flashcard policies, routes routine learning work economically, sends complex learning work directly to the stronger model, escalates only validated exceptional cases, preserves account failover beneath model routing, records every provider attempt, and passes documented quality, cost, privacy and rollback gates. Each enabled high-priority feature must also have a complete accessible frontend, authenticated backend workflow, authoritative evidence boundary, release gate and automated end-to-end verification.

## High-priority completion gate

- [ ] The ten-step Admin readiness summary passes for the Chemistry States of Matter pilot without requiring publication of the remaining Unit 1 topics or textbook units.
- [ ] A Student can open Chemistry Topic 1 and receive a grounded text explanation with exact reviewed citations.
- [ ] The Tutor can ask questions, run Guided Practice and explain misconceptions without using uncovered or cross-subject material.
- [ ] A Student can complete an accessible flashcard review session and resume it safely.
- [ ] Parent/Admin visibility, privacy, authorization, accessibility and release tests pass.
- [ ] No medium, low or lowest-priority feature is required for the Student pilot to operate.

**Done when:** Students can safely learn the published States of Matter topic through grounded text tutoring and flashcards, with one canonical source, exact citations, isolated child data, controlled provider behaviour and reviewed release evidence.
