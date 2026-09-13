# Immutable practice, official papers and term mocks

Step 11 introduces one assessment lifecycle for individual practice, complete uploaded Edexcel papers and generated term mocks.

Before vector ranking or random choice, the eligibility service derives cumulative covered units from the student's published curriculum plan. A question is eligible only when every confirmed unit mapping belongs to that set. Official papers are offered only when every question is eligible. Mock blueprints require an exact question count and mark total; AKURU reports a shortage instead of adding material from later terms.

Admins publish mock blueprints with a subject, Grade and Term, mark total, duration, skills and difficulty profile. Students can only start a blueprint matching their current Grade and Term. The server chooses questions deterministically, so clients cannot submit question IDs.

Starting an assessment creates immutable question snapshots containing the source document version, prompt, equations, assets, locations, confirmed units and the available marking-scheme and examiner-report rubric. It also freezes curriculum coverage, timing and blueprint settings. Later source edits cannot affect the active assessment.

During an active assessment, API responses omit rubrics, answers and examiner feedback. They become visible only after submission or expiry. Answer saves require an idempotency key and stop at the frozen deadline. Submission also requires an idempotency key; retrying the same request returns the same assessment. A submission after the deadline preserves answers saved in time and records the assessment as expired.

Primary endpoints:

- `POST /api/v1/assessments/admin/blueprints`
- `GET /api/v1/assessments/blueprints`
- `POST /api/v1/assessments/start`
- `POST /api/v1/assessments/{id}/answers`
- `POST /api/v1/assessments/{id}/submit`
- `GET /api/v1/assessments`
