# Tutor Step 9 — Parent history and Admin safety controls

The horizontal portal navigation now includes **Tutor history** for Parents and **Tutor history & safety** for Admins.

Parents see completed-session learning summaries, allowed aggregate usage and safety notifications for linked children. The interface intentionally does not request or display raw Tutor transcripts, internal identifiers, source messages, model details or provider credentials.

Admins can supply a mandatory support reason to open a full transcript, resolve a safety event, preview an age-based transcript cleanup and confirm the purge. The API enforces the role and records the sensitive action; disabled controls in the interface provide an additional usability guard. A purge replaces transcript content with a clear redaction marker while summaries remain available.
