# OpenClaw Telegram Quick Mock delivery plans

**Planned:** 2026-10-03
**Status:** Not started. No OpenClaw or container runtime has been installed on the AKURU production server.

These are the action plans for the optional Telegram Quick Mock. The earlier [combined proposal](../../source-code/todo/planned/TODO-FUTURE-LOWEST-OPENCLAW.md) remains a requirements reference; track implementation in the files below. Per-child quota extensions in that file are separate work. Move each plan from `planned/` to `ongoing/` when started and then to `completed/` when verified; update links in this index when moving it.

Complete the plans in this order:

1. [Docker host preparation](ongoing/01-DOCKER-HOST-PREPARATION.md)
2. [OpenClaw installation and hardening](planned/02-OPENCLAW-INSTALLATION.md)
3. [AKURU integration APIs and Telegram identity](planned/03-AKURU-INTEGRATION-APIS.md)
4. [AKURU plugin and Telegram Quick Mock](planned/04-PLUGIN-AND-TELEGRAM-QUICK-MOCK.md)
5. [Evaluation, pilot and release](planned/05-EVALUATION-AND-RELEASE.md)

The first two plans install an isolated Gateway **without** a Telegram channel, AKURU plugin, Student data or AKURU credential. This permits an early infrastructure and security check. Do not connect a Telegram bot or give OpenClaw AKURU credentials until plan 3's API and isolation tests pass. All production changes require a reviewed release and rollback path. Nothing in these plans authorizes access to AKURU's PostgreSQL credentials, document filesystem, or existing web/Tutor secrets.

## Fixed product boundary

- AKURU owns identity, enrolment, cumulative coverage and approved educational evidence.
- OpenClaw owns only temporary question, answer, timer and marking state for Telegram Quick Mock.
- Quick Mock does not update AKURU assessments, mastery, study plans or Parent review data.
- Each API request resolves the Student from trusted Telegram runtime identity and checks authorization again. A model-supplied name or Student ID is never trusted.
- The current production VM is Ubuntu 24 LTS on ARM64 with 11 GiB RAM, Node v22.23.2, and no Docker installation as of this planning review. Keep the AKURU Node installation unchanged; OpenClaw's container supplies its own supported runtime.

## Decisions to record before the pilot

- Exact pinned OpenClaw release/image digest and official ARM64 image availability.
- Telegram bot ownership and secure token handoff.
- OpenClaw OpenAI credential and model/cost policy, separate from AKURU's provider accounts unless explicitly approved.
- Temporary mock and transcript retention periods, plus deletion and backup exclusions.
- Initial Student and Chemistry scope for the controlled pilot.
