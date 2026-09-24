# Curated flashcard library

AKURU serves curated flashcard releases built from published textbook-topic content. Production does not generate cards on demand, and Student study makes no language-model calls.

## Release artifact

The versioned `akuru.flashcards.v1` JSON artifact declares the textbook, unit/module, topics, published content versions and reviewed cards. Each card has a stable key, concept key, category, variation type, difficulty, approved question and answer, one or more exact retrieval-chunk references, and optional approved visual provenance.

Run the operator command from `backend`:

```bash
.venv/bin/python -m app.flashcard_release validate /secure/path/release.json
.venv/bin/python -m app.flashcard_release import /secure/path/release.json --admin-username ADMIN --dry-run --release
.venv/bin/python -m app.flashcard_release import /secure/path/release.json --admin-username ADMIN --release
```

Validation checks the artifact checksum, subject and hierarchy ownership, published content-version checksum, active source evidence, approved visuals, required fields, duplicate wording, sentence quality and suspicious Chemistry OCR notation. Import is idempotent by release ID and checksum and writes the entire release transactionally. Release artifacts derived from copyrighted textbook material stay outside Git.

## Student selection and scheduling

Only released decks within the Student's cumulative Grade and Term coverage are visible. The modes are Quick review (10), Normal review (20), Full topic practice, Difficult cards, Due today and Unit mixed practice (20).

Selection is deterministic and child-scoped. It prioritizes overdue cards, prior Again/Difficult ratings, recorded weak topics, unseen cards, learning cards and finally mastered variations. A session snapshots its immutable card-version IDs and selection reasons. Closely related concept variations are separated where possible.

Ratings update a per-child card state with a versioned deterministic schedule. `Again` is due after ten minutes; later intervals depend on repetitions, rating and bounded ease factor. Ratings never update authoritative academic mastery.

## Admin and API boundaries

The Admin screen is read-only for content and shows release provenance, distribution and source evidence. Admins may withdraw a released deck with an audited reason. The browser generation, arbitrary card editing and manual release endpoints have been removed.

Authenticated endpoints are under `/api/v1/flashcards`:

- Admin: list/get decks and withdraw a released deck.
- Student: list eligible decks, inspect study options, start/resume a mode, reveal an answer and record a rating.

Every revealed answer links back to the exact authorized textbook passage.
