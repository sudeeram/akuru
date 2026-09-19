# Future AKURU roadmap — priority index

**Status: Future work — prioritized for staged delivery.**

The original combined document-review and AI backlog has been divided so AKURU can deliver useful Student learning features before larger extraction, voice and messaging projects.

## Priority order

1. [High priority — Chemistry Topic 1 readiness, text tutoring and flashcards](TODO-FUTURE-HIGH-LEARNING.md)
   - Make the reviewed Chemistry v2.1 source usable and canonical.
   - Complete grounded text tutoring, Guided Practice, misconception support and flashcards.
   - Add the minimum model routing, quota, Admin and evaluation controls needed for release.

2. [Medium priority — Low-cost learning and document-review improvements](TODO-FUTURE-MEDIUM-IMPROVEMENTS.md)
   - Add caption relationships and scientific notation review.
   - Build structured short revision questions and deterministic study-plan extensions.
   - Complete shared accessibility and API-contract behaviour.

3. [Low priority — Advanced extraction, assessment routing and voice delegation](TODO-FUTURE-LOW-ADVANCED-AI.md)
   - Complete and evaluate layout-aware OCR, photographed-page processing, tables and equations.
   - Extend model policies into document interpretation and assessment marking.
   - Add bounded realtime voice delegation.

4. [Lowest priority — OpenClaw Telegram Quick Mock](TODO-FUTURE-LOWEST-OPENCLAW.md)
   - Add isolated Telegram identities and temporary OpenClaw-generated and marked mocks.
   - Keep Quick Mock state outside AKURU PostgreSQL and independent of permanent mastery.

## Scheduling rules

- Complete high-priority launch prerequisites before starting medium feature delivery.
- Medium work must remain independently deployable without low or lowest-priority services.
- Low-priority work must not change or delay the released text Tutor and flashcard paths.
- Lowest-priority OpenClaw work starts only after production model routing, privacy controls and operational monitoring are stable.
- A lower-priority item may move earlier only when it becomes a documented blocker for a higher-priority acceptance criterion.
- All checkboxes remain unchecked until implementation, verification and the relevant release gate are complete.
