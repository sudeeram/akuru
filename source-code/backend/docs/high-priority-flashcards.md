# Curated Flashcard library and Student mastery

AKURU serves reviewed Flashcard releases built from published textbook-topic content. Production does not generate cards on demand, and studying a released deck makes no language-model request.

## Release artifact

The versioned `akuru.flashcards.v1` JSON artifact declares the textbook, unit or module, topics, published content versions and reviewed cards. Every immutable card version has a stable key, concept key, category, variation type, reviewed intrinsic difficulty (`easy` or `difficult`), approved answer, optional explanation, exact retrieval-chunk references and optional approved visual provenance. Card totals and category ratios depend on the topic; AKURU does not enforce the historical 100-card Chemistry distribution.

Run the operator commands from `backend`:

```bash
.venv/bin/python -m app.flashcard_release validate /secure/path/release.json
.venv/bin/python -m app.flashcard_release import /secure/path/release.json --admin-username ADMIN --dry-run --release
.venv/bin/python -m app.flashcard_release import /secure/path/release.json --admin-username ADMIN --release
```

Validation checks the artifact checksum, hierarchy ownership, content-version checksum, source evidence, approved visuals, duplicate wording, sentence quality and suspicious Chemistry OCR notation. Import is transactional and idempotent by release ID and checksum. Release artifacts derived from copyrighted textbook material stay outside Git.

## Student workflows and selection

Only released decks within the Student's cumulative Grade and Term coverage are visible. New sessions support:

- **Review Flashcards:** Easy, Difficult or Mixed intrinsic difficulty; 20 or 30 requested cards.
- **Difficult Flashcards:** cards in the Student's Needs Review state plus unattempted cards with intrinsic difficulty Difficult; 20 or 30 requested cards.

When fewer cards qualify, AKURU clearly uses the smaller available set. Selection is randomized once, stored with the session, balanced across available categories and biased toward Needs Review, To Evaluate, Good and then Mastered. Recently completed cards have lower priority unless they need review. Refresh and permitted navigation preserve the selected card versions and order.

## Student-owned mastery

Mastery is unique to `(student_id, card_version_id)`. This isolation rule applies to every present and future Student performance measurement in AKURU. Another Student's attempt can never alter or populate this state.

`akuru-flashcard-mastery-v1` uses completed sessions only. Difficult contributes `0`, Good `0.65`, and Easy `1.0` to a recency-weighted score. Again is attempted but excluded from the numeric average; it resets the Easy streak and places the card in Needs Review. Three consecutive Easy ratings in three separately completed sessions promote a card to Mastered. A later Difficult rating resets the streak and can downgrade it according to recent evidence. Scores of at least `0.55` are Good unless the three-Easy Mastered rule applies; lower scores are Needs Review. Cards without completed evidence are To Evaluate.

Ratings remain provisional while a set is active. A rating is immutable once submitted. Completing the last card commits all reviews, learning states and the session in one transaction. Discarding an incomplete session deletes its provisional ratings and leaves all previously completed learning unchanged.

The Student dashboard reports To Evaluate, Needs Review, Good and Mastered counts, coverage, mastery, category results, completed sessions and a recommended next mode. Coverage measures cards evaluated in completed sets. Mastery averages evaluated cards only.

## Navigation, answers and sources

Students can revisit attempted cards read-only, but cannot skip beyond the first unattempted card or change a rating. Internal exits and sign-out show an explicit discard choice; browser reload and external navigation use the browser leave warning.

The approved answer appears first. An optional explanation has a separate toggle. Exact textbook evidence has its own remembered expand/collapse state, readable paragraphs, the document name, and `Page Number X` or `Page Numbers X–Y`. Approved visuals use a responsive container. Protected visuals and textbook pages are fetched once into an in-memory cache scoped to the active Student session. They are revoked on completion, discard, identity change or component teardown and are never written to browser storage. Server responses use `private, no-store`.

## Reset before this schema

The migration to the mastery experience requires the Flashcard tables to be empty. The reviewed command is dry-run by default:

```bash
.venv/bin/python -m app.flashcard_reset
.venv/bin/python -m app.flashcard_reset --apply --admin-username ADMIN --confirm 'RESET AKURU FLASHCARDS'
```

Take and verify an encrypted database backup first. The command refuses unknown external dependencies, deletes only Flashcard decks, versions, sessions, reviews and learning states in a transaction, records a non-sensitive audit event, and preserves textbooks, extraction, retrieval, visuals, accounts, enrolments and all unrelated learning domains.

## API boundaries

Admins can list, inspect and withdraw releases. Students can list eligible decks, inspect options and personal mastery, start or resume a session, reveal, rate, navigate to an allowed position, discard an incomplete session, and fetch authorized protected sources. Every Student endpoint resolves ownership from the authenticated session; database UUIDs are not used as public learner identifiers.
