# Tutor Step 2 — Sessions, transcripts and switching

Tutor sessions are authenticated, Student-owned practice records. A session starts only when the Student is enrolled in the selected subject, the curriculum plan is ready, and the selected unit is in the Student's cumulative Grade and Term coverage. Step 0 feature flags and the formal-assessment lock are checked on every mutation.

## Data model

- `tutor_sessions` retains the subject, active unit, selected immutable profile version and lifecycle. A partial unique index permits one active session per Student.
- `tutor_turns` stores ordered text or voice transcripts and the exact tutor-profile version active for the turn. It has no raw-audio column.
- `tutor_turn_sources` retains authorized retrieval-chunk links for future grounded replies.
- `tutor_session_profile_events` records each profile change, both immutable versions and a compact server-created handover summary.
- `tutor_session_unit_events` records explicit moves between eligible units in the same subject.

Internal UUIDs remain database keys. API clients use opaque `sessionRef`, `turnRef` and existing `profileRef` values.

## API lifecycle

`GET /api/v1/tutoring/session-options` returns the Student's active profiles and eligible covered units. `POST /sessions` starts a practice session. Turns, tutor switches, unit switches and ending use nested POST routes with CSRF protection. `GET /sessions` and `GET /sessions/{sessionRef}` return only the authenticated Student's records.

Every create or switch request carries a client-generated `requestKey`. Database uniqueness constraints make retries return the prior result. Session rows are locked during ordered turn and switch mutations, so competing operations cannot silently overwrite context.

The handover summary contains the subject, active unit, current practice state and short excerpts from the most recent six retained turns. It is generated on the backend and cannot be supplied by the browser. Step 6 will use this retained state when it adds model-generated teaching replies.
