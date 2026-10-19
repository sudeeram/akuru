# AKURU delivery plans

This directory separates active delivery work, future plans and finished implementation records.

## Ongoing

- [Student Community: course discovery and following](ongoing/TODO-STUDENT-COMMUNITY.md) — implementation and local acceptance in progress; commit and production deployment authorized.

- [Route-wide frontend refresh](ongoing/TODO-ROUTE-FRONTEND-REFRESH.md) — implement the full frontend route audit locally.

- [UI features and portal presentation refresh](ongoing/TODO-UI-FEATURES-REFRESH.md) — frontend-only PreSkool-inspired previews, Academy learning patterns and ShadcnStore navigation; implemented; responsive visual acceptance pending. No backend or API contract changes.

These roadmaps already contain completed work and still have outstanding actions. Finish or explicitly close them before starting another planned roadmap.

- [Core assessment and learning roadmap](ongoing/TODO.md)
- [Tutor Agent roadmap](ongoing/TODO-TUTOR.md)
- [Textbook groups, topics and incremental coverage](ongoing/TODO-TEXTBOOK-TOPICS.md)
- [Database baseline reset and migration squash](ongoing/TODO-DATABASE-BASELINE.md)
- [High: Chemistry Topic 1, text tutoring and flashcards](ongoing/TODO-FUTURE-HIGH-LEARNING.md)
- [Pearson Chemistry past-paper intake pilot](ongoing/TODO-PEARSON-CHEMISTRY-PAST-PAPERS.md)
- [Admin official-paper review workspace](ongoing/TODO-OFFICIAL-PAPER-REVIEW-WORKSPACE.md)

## Planned


- [Original Student avatar builder](planned/TODO-STUDENT-AVATAR-BUILDER.md) — original AKURU character customisation, profile integration and validated persistence; Style A vector editor and validated saving implemented locally; Student/Parent signed-in acceptance and deployment remain pending.

- [Admin official-paper review workspace](planned/TODO-OFFICIAL-PAPER-REVIEW-WORKSPACE.md) — side-by-side question, scheme, examiner and textbook review with per-part decisions and separate release gates.
- [Future Parent-assisted and self-service account recovery](planned/TODO-FUTURE-ACCOUNT-RECOVERY.md) — Parent requests, verified recovery contacts and expiring one-time email tokens after the Admin-managed lifecycle is complete.
- [Future TanStack capabilities](planned/TODO-TANSTACK-FUTURE.md) — optional suite features to assess when their product use cases are built.
- [Future roadmap priority index](planned/TODO-FUTURE-DOCUMENT-REVIEW.md)
  - [Medium: low-cost learning and document-review improvements](planned/TODO-FUTURE-MEDIUM-IMPROVEMENTS.md)
  - [Low: advanced extraction, assessment routing and voice](planned/TODO-FUTURE-LOW-ADVANCED-AI.md)
  - [Lowest: OpenClaw Telegram Quick Mock — ordered action plans](../../openclaw/todo/README.md)

## OpenClaw

The [top-level OpenClaw folder](../../openclaw/README.md) holds its own build artifacts and [delivery plans](../../openclaw/todo/README.md). The earlier [combined OpenClaw proposal](planned/TODO-FUTURE-LOWEST-OPENCLAW.md) remains a requirements reference; its per-child quota extensions are separate work.

## Completed

- [Admin, Student and Parent profiles](completed/TODO-ACCOUNT-PROFILES.md) — implemented locally; no backend changes or deployment.

- [Textbook paragraph reconstruction, newline normalization and final-document review](completed/TODO-TEXTBOOK-PARAGRAPH-RECONSTRUCTION.md) — deterministic reconstruction, Admin correction and final reviewed-document confirmation delivered.

- [Visual Reference and scientific-text review](completed/TODO-VISUAL-REFERENCE-REVIEW.md) — explicit source roles, role-aware readiness, printed-page provenance and restricted scientific notation review.

- [Textbook administration and Exam Documents experience](completed/TODO-TEXTBOOK-ADMIN-EXPERIENCE.md) — routed textbook list, create, manage and review workspaces with separated Exam Documents and protected source moves.
- [Account password lifecycle and login visibility](completed/TODO-ACCOUNT-PASSWORD-LIFECYCLE.md) — Admin resets, forced replacement, authenticated changes, session revocation, last-login visibility and audit controls.
- [Flashcard mastery and Student experience](completed/TODO-FLASHCARD-STUDENT-UX.md) — Student-owned mastery, randomized completed-set study and protected evidence experience.
- [TanStack Router and Query foundation](completed/TODO-TANSTACK-FOUNDATION.md)
- [Curated flashcard library and adaptive Student review](completed/TODO-FLASHCARD-LIBRARY.md)
- [Manual `api.ts` refactor](completed/TODO-MANUAL-API-TS.md)

Status markers used by the roadmaps:

- `[ ]` not started
- `[~]` in progress
- `[x]` complete
- `[!]` blocked, with the reason recorded beside the item

A roadmap starts in `planned`, moves to `ongoing` when implementation begins, and moves to `completed` only after its acceptance criteria pass and every intended action is closed. Complete or explicitly close ongoing work before starting another planned roadmap. Completed plans remain as implementation history.

The authoritative product, security and data rules remain in the architecture documents under [`../docs`](../docs), [`../backend/docs`](../backend/docs) and [`../frontend/docs`](../frontend/docs).
