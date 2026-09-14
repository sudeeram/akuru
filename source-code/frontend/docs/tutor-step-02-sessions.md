# Tutor Step 2 — Student tutor room

Students open **Tutor room** from the horizontal navigation. Before a session begins, the page offers only their active tutor profiles and units returned as eligible by the backend.

During practice, the room shows the selected AKURU BOT, subject, active unit and retained transcript. The Student can change tutor or move to another covered unit without ending the session. Messages submit on the form and are stored against the tutor-profile version that received them. Errors from coverage, formal-assessment locks, feature flags and authorization checks are displayed in the room.

The browser generates a fresh idempotency key for each start, message, switch and end action. Server responses replace local session state, keeping the backend authoritative. The UI never records or uploads raw audio. Voice capture and model-generated tutor replies are later roadmap steps.
