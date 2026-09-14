# Tutor Step 6 — Structured text Tutor Agent

`POST /api/v1/tutoring/sessions/{sessionRef}/agent-turns` completes one text exchange in an active practice session. The request contains only the learner message, one of seven versioned teaching modes, and an idempotency key. Identity, course, subject, active unit, tutor-profile version and authorization always come from the authenticated server session.

## Server-controlled tools

The orchestrator assembles a bounded package from learner context, mastery summary, approved study-plan context, exact textbook search and source opening, deterministic next-unit advice when requested, guided-practice availability, and approved deterministic media. Each result has `ready`, `evidence_insufficient` or `unavailable` status. The provider receives results but cannot choose a student, broaden the curriculum, open a storage key, change a unit, mark an answer, alter mastery or update a study plan. Step 7 will connect creation and submission of eligible practice through the assessment service.

Seven prompts are independently named and versioned: explanation, questions, guided practice, Socratic practice, revision, exam technique and French conversation. Their shared security boundary treats learner messages, transcript text, document passages and tool results as untrusted JSON data. It permits only supplied citation references and prohibits invented pages, editions, quotations, scores and mistake counts.

The required provider schema contains response content, citation references, up to four follow-up choices and non-authoritative signal proposals. Server tool results and approved visuals are added authoritatively. Every returned citation is reopened through the Step 5 authorization service, and each signal evidence reference must exist in the Step 3 context or Step 5 citation set. Invalid structured output, invented citations and unsupported signals fail before turns are saved.

Complete provider calls use `AIAccountRouter` with one operation UUID across ordered account attempts. `ai_invocations` records usage, latency, response ID, provider, model and prompt. The assistant turn stores that provenance and the structured response snapshot; `tutor_turn_sources` stores validated retrieval relationships. Repeating a request key replays the stored response without another provider call. When subject evidence is absent, the deterministic evidence gate stores a cautious response and never asks the provider to invent an explanation.

Approved visuals use `GET /api/v1/tutoring/sessions/{sessionRef}/media/{mediaId}`. The private endpoint repeats session, subject, active-unit and publication checks and sends `private, no-store`.
