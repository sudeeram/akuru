# OpenClaw Telegram Quick Mock delivery plans

**Planned:** 2026-10-03
**Status:** Docker and the isolated OpenClaw Gateway installed on 2026-10-03. AKURU integration, Telegram and Student release have not started.

These are the action plans for the optional Telegram Quick Mock. The earlier [combined proposal](../../source-code/todo/planned/TODO-FUTURE-LOWEST-OPENCLAW.md) remains a requirements reference; track implementation in the files below. Per-child quota extensions in that file are separate work. Move each plan from `planned/` to `ongoing/` when started and then to `completed/` when verified; update links in this index when moving it.

Complete the plans in this order:

1. [Docker host preparation](ongoing/01-DOCKER-HOST-PREPARATION.md)
2. [OpenClaw installation and hardening](completed/02-OPENCLAW-INSTALLATION.md)
3. [AKURU integration APIs and Telegram identity](planned/03-AKURU-INTEGRATION-APIS.md)
4. [AKURU plugin and Telegram Quick Mock](planned/04-PLUGIN-AND-TELEGRAM-QUICK-MOCK.md)
5. [Evaluation, pilot and release](planned/05-EVALUATION-AND-RELEASE.md)

The first two plans installed an isolated Gateway **without** a Telegram channel, AKURU plugin, Student data or AKURU credential. This permits an early infrastructure and security check. Do not connect a Telegram bot or give OpenClaw AKURU credentials until plan 3's API and isolation tests pass. Before any channel is enabled, pair a dedicated operator device and rerun the deep security audit to clear or explicitly accept its limited-read warning. All production changes require a reviewed release and rollback path. Nothing in these plans authorizes access to AKURU's PostgreSQL credentials, document filesystem, or existing web/Tutor secrets.

## Fixed product boundary

- AKURU owns identity, enrolment, cumulative coverage and approved educational evidence.
- OpenClaw owns only temporary question, answer, timer and marking state for Telegram Quick Mock.
- Quick Mock does not update AKURU assessments, mastery, study plans or Parent review data.
- Each API request resolves the Student from trusted Telegram runtime identity and checks authorization again. A model-supplied name or Student ID is never trusted.
- The production VM is Ubuntu 24 LTS on ARM64 with 11 GiB RAM and AKURU Node v22.23.2. Docker Engine and Compose are installed; OpenClaw's pinned container supplies its own runtime. Keep the AKURU Node installation unchanged.

## Decisions to record before the pilot

- Exact pinned OpenClaw release/image digest and official ARM64 image availability.
- Telegram bot ownership and secure token handoff.
- OpenClaw OpenAI credential and model/cost policy, separate from AKURU's provider accounts unless explicitly approved.
- Temporary mock and transcript retention periods, plus deletion and backup exclusions.
- Initial Student and Chemistry scope for the controlled pilot.
