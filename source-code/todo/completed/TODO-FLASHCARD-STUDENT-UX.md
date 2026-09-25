# Flashcard mastery and Student experience

**Status:** Completed on 25 September 2026.

This is the single delivery plan for the next Flashcard release. It combines mastery ranking, varied card selection, completed-set scoring, constrained navigation, clearer answers, readable textbook evidence, protected source caching and the existing visual improvements. It supersedes the current Student-facing Quick Review, Normal Review, Full Topic Practice, Difficult Cards, Due Today and Unit Mixed Practice modes.

The existing generated Chemistry flashcard release and all Student sessions, provisional responses, reviews, learning states and other assignments or performance records that depend on that release may be removed through the reviewed reset in Step 0. The cards will be recreated with intrinsic difficulty included in the curated artifact from the start. Textbook content, reviewed retrieval chunks, source mappings, approved visuals, users, enrolments and unrelated learning records are outside this reset.

Each Unit or Topic may have a different total number of cards and category distribution according to its learning content, concepts, calculations, diagrams and common misconceptions. AKURU validates coverage and quality for that specific release rather than enforcing the former States of Matter totals.

No OpenAI request is required while a Student studies or when AKURU calculates mastery. Backend authorization and family separation remain authoritative.

## Agreed product rules

- [x] Expose only **Review Flashcards** and **Difficult Flashcards** as new-session choices.
- [x] In **Review Flashcards**, ask for Easy, Difficult or Mixed intrinsic difficulty and then 20 or 30 cards.
- [x] In **Difficult Flashcards**, select cards in Needs Review plus unattempted cards with reviewed intrinsic difficulty Difficult; then ask for 20 or 30 cards.
- [x] Remove **Due Today** completely from the Student experience and new selection logic.
- [x] Remove Quick Review, Normal Review, Full Topic Practice and Unit Mixed Practice from the Student experience, new-session API and active Flashcard schema after the reviewed reset.
- [x] Record mastery only after every card in the selected set has been attempted and the set completes successfully.
- [x] Keep provisional ratings in an incomplete set separate from permanent learning and mastery records.
- [x] Make ratings immutable after the Student submits them.
- [x] Permit backward navigation only through attempted cards and never beyond the first unattempted card.
- [x] After the new system launches, discarding an incomplete set removes only that set's provisional results and never deletes earlier completed learning history.
- [x] Treat every mastery and performance result as Student-owned. Intrinsic difficulty belongs to a card version; mastery belongs uniquely to one Student and that immutable card version.
- [x] Apply the same Student-ownership rule to all future performance measurements, caches, summaries, exports and recommendations across AKURU.

## Step 0 — Inventory and reset the existing Flashcard domain safely

- [x] Document the current deterministic selection, immediate rating update, spaced-review fields, session lifecycle and Student routes before changing them.
- [x] Inventory every foreign key and application dependency on Flashcard decks, card versions, sessions, responses, reviews, learning states, assignments, caches and audit references.
- [x] Prove that the deletion scope contains only the replaceable Flashcard release and its dependent Student records; explicitly exclude textbook sources, retrieval chunks, visuals, accounts, enrolments and unrelated performance evidence.
- [x] Create a dry-run reset command that reports row counts by table and refuses unknown dependencies or an unexpected deck scope.
- [x] Require an encrypted database backup and reviewed dry-run evidence before executing the reset locally or in production.
- [x] Delete dependants in a transaction-safe order, retain a non-sensitive deletion audit event and verify every Flashcard-domain count is zero afterward.
- [x] Remove obsolete scheduler columns and compatibility code where the clean reset makes them unnecessary, while keeping migration downgrade and database restore instructions.
- [x] Recreate the States of Matter release later through the reviewed import workflow with intrinsic difficulty present from the first card version.

**Acceptance:** the precise reset is dry-run verified, backed up, auditable and removes only replaceable Flashcard content and dependent Student records before the new schema is populated.

## Step 1 — Define versioned difficulty and mastery rules

- [x] Add reviewed intrinsic card difficulty values `easy` and `difficult`; keep this independent from a Student's mastery status.
- [x] Define Student-specific mastery statuses `to_evaluate`, `needs_review`, `good` and `mastered`.
- [x] Version the calculation as `akuru-flashcard-mastery-v1` and the selector as `akuru-flashcard-selection-v2`.
- [x] Use completed-set ratings only, with numeric mastery values Difficult `0`, Good `0.65` and Easy `1.0`.
- [x] Exclude Again from the numeric average, but make it reset the consecutive-Easy streak and place or keep the card in Needs Review.
- [x] Require three consecutive Easy ratings in three separately completed sessions to reach Mastered.
- [x] Use a documented recency-weighted score for downgrade and recovery decisions so a later Difficult rating moves Mastered to Good or Needs Review according to recent evidence.
- [x] Define deterministic thresholds for Good and Needs Review, minimum evidence, rounding and tie handling.
- [x] Keep coverage separate from mastery: coverage is the proportion attempted in completed sets; mastery is performance over evaluated cards.
- [x] Require every mastery lookup and mutation to be keyed by authenticated Student plus immutable card version; never expose or update a global card mastery value.

**Acceptance:** identical rating histories always produce the same status, score and Easy streak, including the three-Easy promotion and later-failure downgrade examples.

## Step 2 — Extend the reviewed card and mastery schema

- [x] Add intrinsic difficulty to each immutable Flashcard card version and to the curated release artifact schema.
- [x] Validate that every newly imported card has an allowed reviewed difficulty.
- [x] Require intrinsic difficulty during recreation of every card and include it in editorial review instead of inferring it permanently from category alone.
- [x] Add per-Student, per-card mastery score, status, consecutive-Easy count, evaluated-at timestamp and mastery algorithm version.
- [x] Add provisional session-response storage with one immutable submitted rating per selected card.
- [x] Add completed-set summary data sufficient to reproduce category and deck statistics without exposing database UUIDs.
- [x] Enforce one mastery state per `(student_id, card_version_id)`, plus rating enums, valid transitions and Student ownership at the database and service layers.
- [x] Include Student identity boundaries in mastery caches, query keys, jobs and aggregates, and clear them on logout or identity change.

**Acceptance:** the clean schema prevents duplicate responses, supports reproducible mastery calculations and makes cross-Student state reuse structurally impossible.

## Step 3 — Replace study modes with the two agreed workflows

- [x] Replace the Student mode contract with `review` and `difficult` for new sessions.
- [x] For Review Flashcards, validate difficulty `easy`, `difficult` or `mixed` and requested count 20 or 30.
- [x] For Difficult Flashcards, include every Needs Review card regardless of intrinsic difficulty plus To Evaluate cards whose intrinsic difficulty is Difficult.
- [x] Clearly offer the actual smaller count or a return to selection when fewer than 20 or 30 eligible cards exist; never silently pad with unrelated cards.
- [x] Remove Due Today from options, summaries, query keys, routes, API schemas, selection rules, tests and documentation.
- [x] Remove legacy mode handling after the clean reset and reject retired values in every new-session boundary.

**Acceptance:** Students see two understandable workflows, and no new session can be created using a retired mode.

## Step 4 — Build balanced, varied session selection

- [x] Replace deterministic ordinal selection with controlled random sampling performed once when a session starts.
- [x] Save the immutable selected card-version references and their order so refresh, resume and routed navigation never reshuffle the set.
- [x] Prioritize Needs Review, To Evaluate, Good and then a limited number of Mastered cards within the chosen workflow.
- [x] Reduce the priority of cards used in the Student's recent completed sets unless they need review.
- [x] Balance concepts and avoid excessive variations of one concept in a set.
- [x] Balance the content categories actually present in the selected Unit or Topic in proportion to eligible inventory while respecting the requested intrinsic difficulty; do not require a fixed category count or ratio.
- [x] Store selection reasons and the selector version for support and evaluation.
- [x] Ensure separate Students have independent histories and randomized sessions.

**Acceptance:** repeated new sessions normally differ when inventory permits, yet each saved session is stable across refresh, resume and browser navigation.

## Step 5 — Make ratings provisional and complete sets atomically

- [x] Show Again, Difficult, Good and Easy with equal neutral styling; remove the current primary/default appearance from Good.
- [x] Require an explicit rating after the approved answer is revealed; selecting it immediately advances to the next unattempted card.
- [x] Store the rating provisionally and lock it against later editing.
- [x] Count Again as an attempted card for set completion without adding a numeric mastery value.
- [x] Do not update mastery, streaks, permanent reviews, deck statistics or legacy schedules while the set remains incomplete.
- [x] On the final rating, complete the session and apply every permanent review and mastery change in one database transaction.
- [x] Make finalization idempotent so retries cannot count a session twice.
- [x] Leave the whole set incomplete if finalization fails and apply no partial mastery changes.

**Acceptance:** abandoned sets change no permanent ranking, while a completed set updates every included card exactly once.

## Step 6 — Constrain card navigation and protect incomplete work

- [x] Add Previous and Next controls with accessible names, keyboard operation and visible focus.
- [x] Allow Previous only to attempted cards and present their question, approved answer, chosen rating and optional learning aids read-only.
- [x] Prevent rating changes when reviewing a previous card.
- [x] Prevent Next from moving past the first unattempted card and reject URL manipulation that requests a future card.
- [x] Keep the routed card position synchronized so permitted refresh and browser back/forward restore the same view.
- [x] Protect top navigation, deck changes, subject changes, sign-out and other internal exits from an incomplete set with a confirmation dialog.
- [x] Use clear actions **Continue studying** and **Exit and discard attempt**, explaining that only the current incomplete attempt will be discarded.
- [x] On confirmed exit, delete or invalidate only the active session's provisional results and clear its protected source cache.
- [x] Use the browser's standard leave-page warning for closing, reloading or navigating outside AKURU when unsaved provisional work exists.

**Acceptance:** a Student can inspect completed cards but cannot skip ahead or revise ratings, and accidental navigation cannot silently lose an incomplete attempt.

## Step 7 — Separate approved answers, explanations and evidence

- [x] After **Show approved answer**, initially render only a clearly labelled Approved answer section.
- [x] Add a separate **Show explanation** / **Hide explanation** toggle and keep the explanation collapsed initially on every card.
- [x] Give Approved answer and Explanation distinct, consistent visual treatment and semantic headings.
- [x] Preserve formulas, lists, paragraphs and accessible reading order in both sections.
- [x] Hide the explanation control cleanly when no separate explanation exists.
- [x] Keep exact textbook evidence as a third independent expandable section.

**Acceptance:** the expected answer, supporting explanation and textbook evidence are visually and semantically distinct on desktop, tablet and mobile.

## Step 8 — Improve exact textbook evidence presentation

- [x] Make **Open exact textbook source** a true expand/collapse control with an accurate label and `aria-expanded` state.
- [x] Allow the source to close without leaving or resetting the card.
- [x] Show the document name on its own line and `Page Number X` on the following line without the word `printed`.
- [x] Render page ranges consistently as `Page Numbers X–Y` without exposing internal page identifiers.
- [x] Restore each attempted card's source-panel state while navigating within the active set.
- [x] Keep the visual-reference page link separate from the reviewed primary-text passage.

**Acceptance:** Students can scan, open and close a source while seeing the familiar textbook page reference in the agreed format.

## Step 9 — Cache protected textbook pages for the active set

- [x] Audit text-source, visual and protected textbook-page requests to identify repeated downloads.
- [x] Cache authorized source data in memory by authenticated Student, source version and page or visual reference for the active session only.
- [x] Reuse an already fetched page or approved visual when another card cites it and deduplicate simultaneous requests.
- [x] Clear the cache when the set completes or is discarded, on logout, forced expiry or identity change.
- [x] Do not persist protected textbook pages in browser storage or allow cross-user cache reuse.
- [x] Respect source versions and authorization so replaced or withdrawn material cannot be served from stale cache.

**Acceptance:** reopening the same source within a set makes no duplicate download, while every identity and lifecycle boundary removes protected cached data.

## Step 10 — Repair loading visuals and constrain learning media

- [x] Reproduce missing AKURU BOT loaders on route transitions, nested routes and Flashcard data loads.
- [x] Verify every asset filename and letter case, then use stable root-relative URLs that work in development and the production build.
- [x] Keep five loader variants stable within each loading event and provide accessible text plus a lightweight failure fallback.
- [x] Prevent loaders from causing layout shifts or hiding loading and error announcements.
- [x] Add one shared responsive container for approved figures, diagrams and photographs.
- [x] Preserve intrinsic aspect ratio, use `object-fit: contain`, prevent unnecessary upscaling and constrain width and viewport-relative height.
- [x] Retain captions and provide an intentional accessible enlargement action where closer inspection helps.
- [x] Test Figure 1.13 plus portrait, landscape, narrow, tall and low-resolution assets without figure-specific CSS.

**Acceptance:** loaders are reliable and every learning image remains legible, proportionate and free from accidental cropping or excessive enlargement.

## Step 11 — Reconstruct readable textbook paragraphs

- [x] Locate whether awkward line breaks originate in reviewed blocks, retrieval serialization or frontend rendering.
- [x] Preserve intentional paragraph, heading, list, formula, caption and table boundaries.
- [x] Join OCR line wraps inside the same paragraph with deterministic rules while preserving punctuation and meaningful whitespace.
- [x] Never join across headings, columns, captions, bullet points, formulas, tables or separate source blocks.
- [x] Render semantic paragraphs with comfortable line length and spacing.
- [x] Prefer presentation-only normalization; make any stored-content migration explicit, reviewed and reversible.
- [x] Add regression examples for hyphenated endings, chemical notation, numbered lists, captions and two-column material.

**Acceptance:** evidence reads as coherent textbook prose without changing scientific meaning or merging unrelated content.

## Step 12 — Build mastery summaries and recommendations

- [x] Add authorized APIs for deck mastery, category breakdown, status counts, recent completed sets and a recommended next session.
- [x] Show Mastered, Good, Needs Review and To Evaluate counts and percentages for the whole deck.
- [x] Show coverage separately from mastery so unattempted cards do not misleadingly count as failures.
- [x] Show performance for every category present in the selected deck using totals calculated dynamically from that released deck.
- [x] Show the current algorithm version and last recalculation time in support data, without cluttering the Student view.
- [x] Recommend Difficult Flashcards when Needs Review evidence warrants it; otherwise suggest a suitable Review Flashcards combination.
- [x] Use public references and enforce Student ownership on every summary and session endpoint.

**Acceptance:** the Student can understand deck coverage, strengths, weak areas and the next useful action without exposing another learner's data.

## Step 13 — Recreate and validate the first reviewed release

- [x] Generate a new reviewed States of Matter artifact from the approved source material using a content-appropriate card count and category distribution.
- [x] Assign `easy` or `difficult` intrinsic difficulty to every card during creation and include it in reviewer-visible validation.
- [x] Validate concept coverage, variation quality, category balance, source grounding, visual references and intrinsic difficulty before import.
- [x] Import the new immutable release only after the new schema, APIs and Student interface pass on a disposable database.
- [x] Verify every card starts as To Evaluate independently for every Student and that no Student has inherited another Student's state.
- [x] Record release checksums, counts by dynamically present category and difficulty, reviewer evidence and rollback instructions.

**Acceptance:** the recreated release is reviewed and grounded, intrinsic difficulty exists from its first version, and each Student begins with an independent To Evaluate state.

## Step 14 — Test, document and release

- [x] Test all mastery transitions, including three completed Easy sessions, subsequent Difficult downgrade, Again handling and recovery.
- [x] Test incomplete, discarded, resumed, failed-finalization and idempotently retried sessions.
- [x] Test Easy, Difficult and Mixed selection, 20/30 limits, insufficient inventory, category balance, recent-card avoidance and saved-order stability.
- [x] Test that every retired mode and Due Today is absent from the new UI and rejected at every new-session boundary.
- [x] Test permitted backward navigation, immutable ratings, future-card rejection and exit confirmation paths.
- [x] Test answer/explanation separation, source toggling, page labels, paragraph normalization, loaders and responsive media.
- [x] Test protected-source request deduplication and cache clearing on completion, discard, logout, expiry and identity change.
- [x] Test mastery statistics against completed-session histories and prove that two Students can hold different mastery, streak and status values for the same card version.
- [x] Add a mandatory reusable performance-isolation test pattern for future Student measurement domains.
- [x] Run frontend tests, backend tests, generated API contract checks, migration checks, type checking, linting and the production build.
- [x] Update Student, parent/support and developer documentation, including the exact mastery rules and the meaning of each status.
- [x] Verify locally with separate Student accounts, require passing CI, back up and run the reviewed production reset, deploy with rollback evidence, import the recreated release and complete production smoke checks.

**Acceptance:** automated and production evidence proves the combined mastery and experience release, each Student's performance is isolated, protected textbook data stays intact and rollback is ready.

## Completion evidence

- Git commit: `d2eae517f0318d98880ac43fe37111b6ad75741b`.
- GitHub Actions run `36131063601`: backend, frontend and deployment-playbook jobs passed.
- Local migration downgrade/upgrade and Alembic drift checks passed.
- Local verification: 49 frontend tests, 126 backend tests, type checking, lint and production build passed.
- Encrypted production backup manifest: `/data/akuru/backups/akuru-20260925T114709Z.manifest`.
- Production reset removed 1 deck, 100 card versions, 7 sessions, 29 reviews and 25 prior learning-state rows; all five Flashcard tables verified empty before migration.
- Production deployment evidence: `/data/akuru/release-evidence/deployed-d2eae517f0318d98880ac43fe37111b6ad75741b-20260925T114854Z.txt`.
- Released artifact checksum: `833e4e75fc749d23fb807d85ac762f38d4f295598fa4dab6421161eaf8142bcf`; 100 cards, 49 Easy, 51 Difficult, zero validation errors.
- Production acceptance passed HTTPS, security headers, routed entry points, fallback boundaries, service health, timers and loopback binding.
- Self-cleaning Student smoke test for `roshinika` proved eligible access, Review/Difficult modes, 20-card selection, reveal, provisional rating isolation, future-card rejection and discard cleanup with zero inherited mastery.
