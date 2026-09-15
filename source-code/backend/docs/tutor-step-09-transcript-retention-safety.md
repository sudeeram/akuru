# Tutor Step 9 — Transcript retention, summaries and safety

AKURU retains text and voice tutor turns without automatic expiry. The stored turn records preserve the tutor profile version, modality, model provenance and request key. An Admin purge redacts the turn content and structured response while retaining the row, timestamps, usage aggregates, session summary, safety record and audit trail.

## Visibility policy

- A Student sees the complete transcript only for their own Tutor sessions through the existing student session endpoints.
- A linked Parent sees structured summaries, aggregate session usage and redacted safety notifications for their children. Parents cannot retrieve full transcripts.
- An Admin sees summaries and safety events across the installation. Full transcript access requires a written support reason and creates `tutor_transcript.support_accessed` in the audit log.

Ending a session creates one idempotent summary containing the units covered, activities, verified tutor-signal strengths and difficulties, suggested next steps, session AI request/token totals and voice-turn count. Usage is joined to the session's persisted tutor turns so concurrent activity cannot be attributed to the wrong session.

## Safety events

Student turns pass through deterministic safety phrase detection after persistence. A unique `(source_turn_id, category)` constraint makes replayed requests notification-idempotent. The linked Parent receives the category, severity and action, but the notification omits the child's message. Review status and an Admin's reason are recorded separately; every review creates an audit event.

This detector is an initial safety control, not a clinical assessment or emergency service. Production incident procedures must route critical alerts to the configured operator and guardian notification channel when those delivery integrations are introduced.

## Retention and deletion

`GET /api/v1/tutoring/admin/transcripts/purge-preview` is read-only. `POST /api/v1/tutoring/admin/transcripts/purge` requires Admin authentication, CSRF protection, a reason, and the exact `PURGE TRANSCRIPTS` confirmation. It redacts only unpurged turns strictly older than the selected cutoff.

The privacy command `python -m app.retention --student-id UUID --apply` also redacts every unpurged Tutor turn belonging to that child, regardless of age. It preserves summary and safety metadata needed for learning history and safeguarding provenance. Database backups contain Tutor transcripts and must therefore remain encrypted. After deletion, content can remain in recovery media only until the configured encrypted-backup retention window expires.

Tests cover linked-family visibility, unrelated-family denial, parent denial of raw transcripts, event idempotency, Admin support and review auditing, strict purge boundaries, invalid confirmation, and preservation of summaries and audit records.
