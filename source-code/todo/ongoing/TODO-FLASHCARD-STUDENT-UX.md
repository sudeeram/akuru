# Flashcard mastery and Student experience

**Status:** Planned.

This is the single delivery plan for the next Flashcard release. It combines mastery ranking, varied card selection, completed-set scoring, constrained navigation, clearer answers, readable textbook evidence, protected source caching and the existing visual improvements. It supersedes the current Student-facing Quick Review, Normal Review, Full Topic Practice, Difficult Cards, Due Today and Unit Mixed Practice modes.

The existing generated Chemistry flashcard release and all Student sessions, provisional responses, reviews, learning states and other assignments or performance records that depend on that release may be removed through the reviewed reset in Step 0. The cards will be recreated with intrinsic difficulty included in the curated artifact from the start. Textbook content, reviewed retrieval chunks, source mappings, approved visuals, users, enrolments and unrelated learning records are outside this reset.

Each Unit or Topic may have a different total number of cards and category distribution according to its learning content, concepts, calculations, diagrams and common misconceptions. AKURU validates coverage and quality for that specific release rather than enforcing the former States of Matter totals.

No OpenAI request is required while a Student studies or when AKURU calculates mastery. Backend authorization and family separation remain authoritative.

## Agreed product rules

- [ ] Expose only **Review Flashcards** and **Difficult Flashcards** as new-session choices.
- [ ] In **Review Flashcards**, ask for Easy, Difficult or Mixed intrinsic difficulty and then 20 or 30 cards.
- [ ] In **Difficult Flashcards**, select cards in Needs Review plus unattempted cards with reviewed intrinsic difficulty Difficult; then ask for 20 or 30 cards.
- [ ] Remove **Due Today** completely from the Student experience and new selection logic.
- [ ] Remove Quick Review, Normal Review, Full Topic Practice and Unit Mixed Practice from the Student experience, new-session API and active Flashcard schema after the reviewed reset.
- [ ] Record mastery only after every card in the selected set has been attempted and the set completes successfully.
- [ ] Keep provisional ratings in an incomplete set separate from permanent learning and mastery records.
- [ ] Make ratings immutable after the Student submits them.
- [ ] Permit backward navigation only through attempted cards and never beyond the first unattempted card.
- [ ] After the new system launches, discarding an incomplete set removes only that set's provisional results and never deletes earlier completed learning history.
- [ ] Treat every mastery and performance result as Student-owned. Intrinsic difficulty belongs to a card version; mastery belongs uniquely to one Student and that immutable card version.
- [ ] Apply the same Student-ownership rule to all future performance measurements, caches, summaries, exports and recommendations across AKURU.

## Step 0 — Inventory and reset the existing Flashcard domain safely

- [ ] Document the current deterministic selection, immediate rating update, spaced-review fields, session lifecycle and Student routes before changing them.
- [ ] Inventory every foreign key and application dependency on Flashcard decks, card versions, sessions, responses, reviews, learning states, assignments, caches and audit references.
- [ ] Prove that the deletion scope contains only the replaceable Flashcard release and its dependent Student records; explicitly exclude textbook sources, retrieval chunks, visuals, accounts, enrolments and unrelated performance evidence.
- [ ] Create a dry-run reset command that reports row counts by table and refuses unknown dependencies or an unexpected deck scope.
- [ ] Require an encrypted database backup and reviewed dry-run evidence before executing the reset locally or in production.
- [ ] Delete dependants in a transaction-safe order, retain a non-sensitive deletion audit event and verify every Flashcard-domain count is zero afterward.
- [ ] Remove obsolete scheduler columns and compatibility code where the clean reset makes them unnecessary, while keeping migration downgrade and database restore instructions.
- [ ] Recreate the States of Matter release later through the reviewed import workflow with intrinsic difficulty present from the first card version.

**Acceptance:** the precise reset is dry-run verified, backed up, auditable and removes only replaceable Flashcard content and dependent Student records before the new schema is populated.

## Step 1 — Define versioned difficulty and mastery rules

- [ ] Add reviewed intrinsic card difficulty values `easy` and `difficult`; keep this independent from a Student's mastery status.
- [ ] Define Student-specific mastery statuses `to_evaluate`, `needs_review`, `good` and `mastered`.
- [ ] Version the calculation as `akuru-flashcard-mastery-v1` and the selector as `akuru-flashcard-selection-v2`.
- [ ] Use completed-set ratings only, with numeric mastery values Difficult `0`, Good `0.65` and Easy `1.0`.
- [ ] Exclude Again from the numeric average, but make it reset the consecutive-Easy streak and place or keep the card in Needs Review.
- [ ] Require three consecutive Easy ratings in three separately completed sessions to reach Mastered.
- [ ] Use a documented recency-weighted score for downgrade and recovery decisions so a later Difficult rating moves Mastered to Good or Needs Review according to recent evidence.
- [ ] Define deterministic thresholds for Good and Needs Review, minimum evidence, rounding and tie handling.
- [ ] Keep coverage separate from mastery: coverage is the proportion attempted in completed sets; mastery is performance over evaluated cards.
- [ ] Require every mastery lookup and mutation to be keyed by authenticated Student plus immutable card version; never expose or update a global card mastery value.

**Acceptance:** identical rating histories always produce the same status, score and Easy streak, including the three-Easy promotion and later-failure downgrade examples.

## Step 2 — Extend the reviewed card and mastery schema

- [ ] Add intrinsic difficulty to each immutable Flashcard card version and to the curated release artifact schema.
- [ ] Validate that every newly imported card has an allowed reviewed difficulty.
- [ ] Require intrinsic difficulty during recreation of every card and include it in editorial review instead of inferring it permanently from category alone.
- [ ] Add per-Student, per-card mastery score, status, consecutive-Easy count, evaluated-at timestamp and mastery algorithm version.
- [ ] Add provisional session-response storage with one immutable submitted rating per selected card.
- [ ] Add completed-set summary data sufficient to reproduce category and deck statistics without exposing database UUIDs.
- [ ] Enforce one mastery state per `(student_id, card_version_id)`, plus rating enums, valid transitions and Student ownership at the database and service layers.
- [ ] Include Student identity boundaries in mastery caches, query keys, jobs and aggregates, and clear them on logout or identity change.

**Acceptance:** the clean schema prevents duplicate responses, supports reproducible mastery calculations and makes cross-Student state reuse structurally impossible.

## Step 3 — Replace study modes with the two agreed workflows

- [ ] Replace the Student mode contract with `review` and `difficult` for new sessions.
- [ ] For Review Flashcards, validate difficulty `easy`, `difficult` or `mixed` and requested count 20 or 30.
- [ ] For Difficult Flashcards, include every Needs Review card regardless of intrinsic difficulty plus To Evaluate cards whose intrinsic difficulty is Difficult.
- [ ] Clearly offer the actual smaller count or a return to selection when fewer than 20 or 30 eligible cards exist; never silently pad with unrelated cards.
- [ ] Remove Due Today from options, summaries, query keys, routes, API schemas, selection rules, tests and documentation.
- [ ] Remove legacy mode handling after the clean reset and reject retired values in every new-session boundary.

**Acceptance:** Students see two understandable workflows, and no new session can be created using a retired mode.

## Step 4 — Build balanced, varied session selection

- [ ] Replace deterministic ordinal selection with controlled random sampling performed once when a session starts.
- [ ] Save the immutable selected card-version references and their order so refresh, resume and routed navigation never reshuffle the set.
- [ ] Prioritize Needs Review, To Evaluate, Good and then a limited number of Mastered cards within the chosen workflow.
- [ ] Reduce the priority of cards used in the Student's recent completed sets unless they need review.
- [ ] Balance concepts and avoid excessive variations of one concept in a set.
- [ ] Balance the content categories actually present in the selected Unit or Topic in proportion to eligible inventory while respecting the requested intrinsic difficulty; do not require a fixed category count or ratio.
- [ ] Store selection reasons and the selector version for support and evaluation.
- [ ] Ensure separate Students have independent histories and randomized sessions.

**Acceptance:** repeated new sessions normally differ when inventory permits, yet each saved session is stable across refresh, resume and browser navigation.

## Step 5 — Make ratings provisional and complete sets atomically

- [ ] Show Again, Difficult, Good and Easy with equal neutral styling; remove the current primary/default appearance from Good.
- [ ] Require an explicit rating after the approved answer is revealed; selecting it immediately advances to the next unattempted card.
- [ ] Store the rating provisionally and lock it against later editing.
- [ ] Count Again as an attempted card for set completion without adding a numeric mastery value.
- [ ] Do not update mastery, streaks, permanent reviews, deck statistics or legacy schedules while the set remains incomplete.
- [ ] On the final rating, complete the session and apply every permanent review and mastery change in one database transaction.
- [ ] Make finalization idempotent so retries cannot count a session twice.
- [ ] Leave the whole set incomplete if finalization fails and apply no partial mastery changes.

**Acceptance:** abandoned sets change no permanent ranking, while a completed set updates every included card exactly once.

## Step 6 — Constrain card navigation and protect incomplete work

- [ ] Add Previous and Next controls with accessible names, keyboard operation and visible focus.
- [ ] Allow Previous only to attempted cards and present their question, approved answer, chosen rating and optional learning aids read-only.
- [ ] Prevent rating changes when reviewing a previous card.
- [ ] Prevent Next from moving past the first unattempted card and reject URL manipulation that requests a future card.
- [ ] Keep the routed card position synchronized so permitted refresh and browser back/forward restore the same view.
- [ ] Protect top navigation, deck changes, subject changes, sign-out and other internal exits from an incomplete set with a confirmation dialog.
- [ ] Use clear actions **Continue studying** and **Exit and discard attempt**, explaining that only the current incomplete attempt will be discarded.
- [ ] On confirmed exit, delete or invalidate only the active session's provisional results and clear its protected source cache.
- [ ] Use the browser's standard leave-page warning for closing, reloading or navigating outside AKURU when unsaved provisional work exists.

**Acceptance:** a Student can inspect completed cards but cannot skip ahead or revise ratings, and accidental navigation cannot silently lose an incomplete attempt.

## Step 7 — Separate approved answers, explanations and evidence

- [ ] After **Show approved answer**, initially render only a clearly labelled Approved answer section.
- [ ] Add a separate **Show explanation** / **Hide explanation** toggle and keep the explanation collapsed initially on every card.
- [ ] Give Approved answer and Explanation distinct, consistent visual treatment and semantic headings.
- [ ] Preserve formulas, lists, paragraphs and accessible reading order in both sections.
- [ ] Hide the explanation control cleanly when no separate explanation exists.
- [ ] Keep exact textbook evidence as a third independent expandable section.

**Acceptance:** the expected answer, supporting explanation and textbook evidence are visually and semantically distinct on desktop, tablet and mobile.

## Step 8 — Improve exact textbook evidence presentation

- [ ] Make **Open exact textbook source** a true expand/collapse control with an accurate label and `aria-expanded` state.
- [ ] Allow the source to close without leaving or resetting the card.
- [ ] Show the document name on its own line and `Page Number X` on the following line without the word `printed`.
- [ ] Render page ranges consistently as `Page Numbers X–Y` without exposing internal page identifiers.
- [ ] Restore each attempted card's source-panel state while navigating within the active set.
- [ ] Keep the visual-reference page link separate from the reviewed primary-text passage.

**Acceptance:** Students can scan, open and close a source while seeing the familiar textbook page reference in the agreed format.

## Step 9 — Cache protected textbook pages for the active set

- [ ] Audit text-source, visual and protected textbook-page requests to identify repeated downloads.
- [ ] Cache authorized source data in memory by authenticated Student, source version and page or visual reference for the active session only.
- [ ] Reuse an already fetched page or approved visual when another card cites it and deduplicate simultaneous requests.
- [ ] Clear the cache when the set completes or is discarded, on logout, forced expiry or identity change.
- [ ] Do not persist protected textbook pages in browser storage or allow cross-user cache reuse.
- [ ] Respect source versions and authorization so replaced or withdrawn material cannot be served from stale cache.

**Acceptance:** reopening the same source within a set makes no duplicate download, while every identity and lifecycle boundary removes protected cached data.

## Step 10 — Repair loading visuals and constrain learning media

- [ ] Reproduce missing AKURU BOT loaders on route transitions, nested routes and Flashcard data loads.
- [ ] Verify every asset filename and letter case, then use stable root-relative URLs that work in development and the production build.
- [ ] Keep five loader variants stable within each loading event and provide accessible text plus a lightweight failure fallback.
- [ ] Prevent loaders from causing layout shifts or hiding loading and error announcements.
- [ ] Add one shared responsive container for approved figures, diagrams and photographs.
- [ ] Preserve intrinsic aspect ratio, use `object-fit: contain`, prevent unnecessary upscaling and constrain width and viewport-relative height.
- [ ] Retain captions and provide an intentional accessible enlargement action where closer inspection helps.
- [ ] Test Figure 1.13 plus portrait, landscape, narrow, tall and low-resolution assets without figure-specific CSS.

**Acceptance:** loaders are reliable and every learning image remains legible, proportionate and free from accidental cropping or excessive enlargement.

## Step 11 — Reconstruct readable textbook paragraphs

- [ ] Locate whether awkward line breaks originate in reviewed blocks, retrieval serialization or frontend rendering.
- [ ] Preserve intentional paragraph, heading, list, formula, caption and table boundaries.
- [ ] Join OCR line wraps inside the same paragraph with deterministic rules while preserving punctuation and meaningful whitespace.
- [ ] Never join across headings, columns, captions, bullet points, formulas, tables or separate source blocks.
- [ ] Render semantic paragraphs with comfortable line length and spacing.
- [ ] Prefer presentation-only normalization; make any stored-content migration explicit, reviewed and reversible.
- [ ] Add regression examples for hyphenated endings, chemical notation, numbered lists, captions and two-column material.

**Acceptance:** evidence reads as coherent textbook prose without changing scientific meaning or merging unrelated content.

## Step 12 — Build mastery summaries and recommendations

- [ ] Add authorized APIs for deck mastery, category breakdown, status counts, recent completed sets and a recommended next session.
- [ ] Show Mastered, Good, Needs Review and To Evaluate counts and percentages for the whole deck.
- [ ] Show coverage separately from mastery so unattempted cards do not misleadingly count as failures.
- [ ] Show performance for every category present in the selected deck using totals calculated dynamically from that released deck.
- [ ] Show the current algorithm version and last recalculation time in support data, without cluttering the Student view.
- [ ] Recommend Difficult Flashcards when Needs Review evidence warrants it; otherwise suggest a suitable Review Flashcards combination.
- [ ] Use public references and enforce Student ownership on every summary and session endpoint.

**Acceptance:** the Student can understand deck coverage, strengths, weak areas and the next useful action without exposing another learner's data.

## Step 13 — Recreate and validate the first reviewed release

- [ ] Generate a new reviewed States of Matter artifact from the approved source material using a content-appropriate card count and category distribution.
- [ ] Assign `easy` or `difficult` intrinsic difficulty to every card during creation and include it in reviewer-visible validation.
- [ ] Validate concept coverage, variation quality, category balance, source grounding, visual references and intrinsic difficulty before import.
- [ ] Import the new immutable release only after the new schema, APIs and Student interface pass on a disposable database.
- [ ] Verify every card starts as To Evaluate independently for every Student and that no Student has inherited another Student's state.
- [ ] Record release checksums, counts by dynamically present category and difficulty, reviewer evidence and rollback instructions.

**Acceptance:** the recreated release is reviewed and grounded, intrinsic difficulty exists from its first version, and each Student begins with an independent To Evaluate state.

## Step 14 — Test, document and release

- [ ] Test all mastery transitions, including three completed Easy sessions, subsequent Difficult downgrade, Again handling and recovery.
- [ ] Test incomplete, discarded, resumed, failed-finalization and idempotently retried sessions.
- [ ] Test Easy, Difficult and Mixed selection, 20/30 limits, insufficient inventory, category balance, recent-card avoidance and saved-order stability.
- [ ] Test that every retired mode and Due Today is absent from the new UI and rejected at every new-session boundary.
- [ ] Test permitted backward navigation, immutable ratings, future-card rejection and exit confirmation paths.
- [ ] Test answer/explanation separation, source toggling, page labels, paragraph normalization, loaders and responsive media.
- [ ] Test protected-source request deduplication and cache clearing on completion, discard, logout, expiry and identity change.
- [ ] Test mastery statistics against completed-session histories and prove that two Students can hold different mastery, streak and status values for the same card version.
- [ ] Add a mandatory reusable performance-isolation test pattern for future Student measurement domains.
- [ ] Run frontend tests, backend tests, generated API contract checks, migration checks, type checking, linting and the production build.
- [ ] Update Student, parent/support and developer documentation, including the exact mastery rules and the meaning of each status.
- [ ] Verify locally with separate Student accounts, require passing CI, back up and run the reviewed production reset, deploy with rollback evidence, import the recreated release and complete production smoke checks.

**Acceptance:** automated and production evidence proves the combined mastery and experience release, each Student's performance is isolated, protected textbook data stays intact and rollback is ready.
