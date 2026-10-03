# 05 — Evaluate and release the Telegram pilot

**Status:** Planned
**Depends on:** Plans 01–04 and a reviewed Chemistry source scope.

## Quality, privacy and cost gates

- [ ] Build a small reviewed Chemistry evaluation set for syllabus relevance, scope/coverage, source grounding, difficulty, mark balance, duplicate content and answer leakage.
- [ ] Compare OpenClaw marking against human/mark-scheme decisions for exact marks, partial credit, scientific notation, diagrams and improved answers.
- [ ] Define acceptance thresholds before release; withhold scores that fail structural/evidence checks.
- [ ] Test provider outages, exhausted credit, malformed output, AKURU timeout, Telegram retry, server restart and temporary-state expiry.
- [ ] Test Laura/Enya separation across APIs, sessions, plugin state, media, logs, retries, deletion and model context.
- [ ] Inspect retained transcripts, temporary state, logs and backups against the approved privacy/retention policy.
- [ ] Confirm provider usage/cost limits and Admin operational totals without retaining mock contents in AKURU.

## Controlled production release

- [ ] Review the installed image digest, security audit, firewall exposure, credential scopes, API contracts and rollback instructions.
- [ ] Pilot one linked Student and one Chemistry scope. Verify AKURU web, backend and existing learning features remain healthy.
- [ ] Test a denied/unlinked Telegram sender and an ineligible Student as well as the authorized pilot Student.
- [ ] Expand to the second Student only after the first pilot's isolation and educational-quality evidence passes.
- [ ] Provide a one-switch disable path for the bot/plugin plus credential revocation that leaves AKURU web running.
- [ ] Update Student, Parent, Admin, developer and Ubuntu operations guides with linking, temporary-result limits, expiry, cost and support steps.
- [ ] Record the release decision, test evidence, pinned version, active configuration and rollback rehearsal.

**Done when:** The two-Student pilot passes authorization, learning quality, marking, cost, privacy and operational checks; disabling OpenClaw leaves AKURU unaffected.
