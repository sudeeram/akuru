# Tutor Step 10 — Realtime voice and French tutoring

AKURU establishes browser audio with OpenAI Realtime over WebRTC. The authenticated Student asks FastAPI for a short-lived client secret for an owned, active Tutor session. FastAPI checks the voice feature flag, formal-assessment guard, session ownership and per-child voice allowance before selecting the first healthy configured OpenAI account. The permanent dotenv credential remains on the backend; only the expiring client secret enters browser memory.

The connection configuration contains the active unit, server-built learner context, recent saved transcript, bounded tutor persona, approved provider voice and speech speed. A failed connection is settled, its account is excluded, and the next credential request uses the next healthy account. Tutor and unit switches close active connection ledgers; the browser reconnects with freshly built instructions and retained transcript context.

## Data and accounting

`tutor_realtime_connections` records the AKURU session, immutable Tutor profile version, selected provider account, provider session identifier, model, voice, language mode, status and reserved/billed seconds. It never stores the ephemeral secret or audio bytes.

One connection reserves at most `AKURU_TUTOR_REALTIME_CONNECTION_SECONDS` or the child's remaining seconds, whichever is smaller. A connected session is billed from server timestamps and unused reserved seconds are returned once on end, failure, cancellation, Tutor switch, unit switch or Tutor-session end. Append-only `student_ai_usage` entries make retry settlement idempotent.

Completed input and output captions are posted back through authenticated, CSRF-protected endpoints. They become ordinary `TutorTurn` rows with `modality=voice`; Student safety detection runs on input captions. Replayed caption event keys cannot create duplicate transcript turns. Raw microphone and response audio pass between the browser and provider and are not recorded by AKURU.

## French voice

The French subject exposes conversation, vocabulary and pronunciation modes. The backend rejects those modes for other subjects. French instructions favour age-appropriate spoken French with brief English clarification when needed. Pronunciation feedback uses short repeatable phrases and does not claim biometric or accent scoring.

## Operational controls

Voice remains off until `AKURU_TUTOR_VOICE_ENABLED=true`. The browser provides Start, Pause/Resume, Mute, Interrupt, Repeat, Slower, text fallback and End controls with live captions. The application and Nginx policies permit same-origin microphone use and connections only to the AKURU origin and `https://api.openai.com`.

The implementation follows the official OpenAI Realtime client-secret and WebRTC call APIs. Re-check the current official API documentation and provider data controls before each production release.
