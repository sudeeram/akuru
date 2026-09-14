# Tutor Step 3 — Grounded learner context

The learner-context service gives future tutor turns a read-only, reproducible view of demonstrated learning. It is available through `POST /api/v1/tutoring/sessions/{sessionRef}/learner-context` and requires an authenticated Student, CSRF token, enabled text-tutor capability, an active practice session, and a unique request key.

## Authorization and scope

The session establishes the Student and subject. The service recalculates cumulative Grade and Term coverage on every request and excludes units outside that coverage. Session ownership returns a not-found response for siblings and other families. The existing formal-assessment guard prevents context access during mock or official-paper attempts.

Only published assessment results count as evidence. A mastery event is accepted only when its published result belongs to a question mapped to the same unit. Weakness records must also link to published results. Study-plan items must belong to the current active plan and an approved recommendation. A database score without qualifying events cannot create a strength, weakness, or trend claim.

## Context contents

Each eligible unit includes:

- validated mastery score, confidence, dimensions and trend;
- recent assessed attempts and concise missing-marking-point rationales;
- mistake taxonomy grouped by explicit topic, with seven-day, thirty-day and lifetime counts;
- approved current study-plan activities;
- structured statements with signal, cautiousness and the exact evidence references supporting them.

Classification is deterministic. Scores of at least 7/10 are strong and scores of at most 4/10 are weak when evidence is not provisional and has adequate quantity and variety. Trends at or above `0.35` are improving and at or below `-0.35` are declining. Missing, provisional, low-confidence, low-variety, or single-event mastery produces cautious low-confidence or insufficient-evidence language.

## Provider boundary and audit

`providerContext` contains a one-way pseudonymous learner reference, subject, active unit code, evidence-backed statements, recurring counts and approved activities. It excludes username, display name, parent details, account identifiers and answer text.

Every operation is stored in `tutor_learner_context_logs` with its public operation reference, algorithm-derived context version, session scope, evidence references and immutable JSON snapshot. Retrying the same request key returns that exact snapshot. The context version is a SHA-256 digest over the algorithm version, scope and sorted evidence references, making a tutor statement reproducible from authorized records.
