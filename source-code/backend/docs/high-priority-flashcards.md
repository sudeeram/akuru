# High-priority flashcard workflow

AKURU creates flashcard drafts from one published textbook topic content version. Generation requires a passing retrieval preflight and uses only active `textbook_section` retrieval chunks from that exact version. Every card stores an immutable front/back version, exact source chunk, page-aware evidence snapshot and generation metadata.

The first generator is deterministic and source grounded. It recognizes definition-like passages and flags generic wording for Admin review. This keeps the initial Chemistry pilot usable without allowing generated wording to become source truth. Feature-specific OpenAI model routing, escalation and child quota charging remain separate high-priority tasks.

Admins use `/#flashcards` to generate a draft, edit each card and approve or reject it. Every edit creates a new card version. A deck can be released only when it has at least three cards, every current card version is approved, all evidence still belongs to the pinned topic content version, and the latest retrieval preflight passes. Releasing a new deck supersedes the earlier released deck without deleting historical data.

Student APIs only return released decks whose topics are included in that Student's cumulative published Grade and Term coverage. Sessions are owned by one Student, resume while active, hide answers until reveal, and persist one idempotent rating per card. The versioned deterministic schedule is:

| Rating | Next interval |
| --- | --- |
| Again | same day |
| Difficult | 1 day |
| Good | 3 days |
| Easy | 7 days |

Flashcard ratings do not change authoritative mastery. Each revealed answer includes the exact authorized textbook passage and source link.

The authenticated endpoints are under `/api/v1/flashcards`:

- Admin: list/get decks, generate, version and review a card, release a deck.
- Student: list eligible decks, start or resume a session, reveal the answer, and rate recall.

