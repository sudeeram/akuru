# Tutor Step 12 — Evaluation and controlled release gates

AKURU extends the reviewed Step 19 evaluation framework with `tutor` corpora. Every enabled iGCSE subject requires an independently versioned and Admin-approved corpus. Approval requires all Tutor quality categories, low/medium/high mastery examples, an explicit review of all 11,664 supported persona combinations, and exact lists of every enabled avatar and voice preset.

## Required evidence

Tutor cases cover factual and mathematical accuracy; exact edition/page grounding and invented-reference rejection; evidence-backed personalisation, recurring-error counts and confidence language; deterministic next-unit recommendations; every supported persona combination; prompt injection, cross-subject access, sibling isolation, unsupported units and formal-assessment blocking; tutor switching and handover; French voice, captions, interruption, latency, reconnect and quotas; preset child safety; and security, privacy, accessibility, cost, retention and rollback.

Observed checks are hashed and scored against fixed thresholds. Runs identify their model, prompt version, modality (`text`, `voice`, or `tools`) and environment (`ci` or `staging`). A missing metric fails the run.

## Release order and rollback

Separate audited gates exist for text, voice, the tool bundle, learner context, next-unit recommendations, sources, guided practice and visuals. A gate can only use a passing run for the same subject and modality. It progresses through `admin_testing`, `parent_pilot`, then `students`; skipping a stage is rejected. Student release additionally requires a passing staging run. Setting a gate to `review_required` is its immediate database kill switch. Environment switches remain the outer text, voice and tools kill switches.

Production requires `AKURU_TUTOR_RELEASE_GATES_REQUIRED=true`. With that setting, runtime authorization checks the applicable database gate and fails closed if the release, run or approved corpus is missing or retired. Run this after staging migrations and evaluation approval:

```bash
cd /opt/akuru/current/source-code/backend
.venv/bin/python -m app.tutor_release_check
```

The command exits non-zero until every Tutor feature is released for every enabled Phase 1 subject. Keep its output with the deployment record. CI exercises schema, scoring, security/isolation, accessibility, quota, retention, staged progression and rollback behavior without requiring production releases.
