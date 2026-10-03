# 04 — AKURU plugin and Telegram Quick Mock

**Status:** Planned
**Depends on:** Restricted AKURU APIs (plan 03) and a hardened, initially unconnected OpenClaw Gateway (plan 02).

## Plugin and channel

- [ ] Build a versioned AKURU Quick Mock plugin with strict schemas for profile, enrolment, covered topics, mock options, generation context and marking context.
- [ ] Pass sender identity from Telegram/OpenClaw runtime to AKURU outside model-controlled parameters; no `studentId`, `familyId` or arbitrary sender ID in model-callable tools.
- [ ] Give the plugin only its restricted AKURU integration credential. Require idempotency keys for Telegram callbacks and tool calls.
- [ ] Configure a dedicated Telegram bot for private DMs only. Start with long polling, which needs no new public ingress; disable group/forum Quick Mock use.
- [ ] Implement `/link`, `/unlink`, `/mock`, `/status`, `/question`, `/next`, `/previous`, `/flag`, `/submit`, `/result` and `/delete_mock` where deterministic commands improve reliability.

## Temporary mock lifecycle

- [ ] Confirm requested subject, course and scope against the linked Student's eligible AKURU topics before generating.
- [ ] Generate a strict paper schema from authorized evidence; validate marks, topics, source references, duplicate questions, marking criteria and answer leakage before the mock starts.
- [ ] Present one question at a time with marks, equations/diagrams and accessible text alternatives; save each answer before acknowledgment.
- [ ] Support navigation, flags, timer, reconnect/resume and explicit final submission. Disallow hints, answer reveal and marking criteria during an active mock.
- [ ] Mark submitted answers with authorized evidence; validate per-point scores and quoted Student evidence, bound retries/escalations, and show mistakes and improved answers only after submission.
- [ ] Store paper, answers and results only in isolated OpenClaw/plugin state outside AKURU PostgreSQL and checkout. Define expiry, deletion, transcript policy and backup exclusions.
- [ ] Clearly label this as temporary practice that does not update AKURU mastery, study plans or tracked assessments.

## Verification

- [ ] Test two simultaneous Students, sender spoofing, duplicate Telegram updates, restart/resume and deletion without state crossover.
- [ ] Test equations, diagrams, long answers, prompt injection and insufficient evidence; fail closed rather than inventing questions or marking criteria.
- [ ] Record provider usage and enforce per-Student temporary mock limits without copying answers into AKURU logs.

**Done when:** One linked Student can request, take, submit and review an authorized temporary mock through Telegram, while another Student cannot access any part of that state.
