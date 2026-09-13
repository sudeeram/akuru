# Curriculum plans and cumulative coverage

Step 7 stores curriculum coverage as immutable published versions. An Admin starts from the currently published iGCSE textbook for a subject, assigns each approved unit to the Grade and Term where it is first taught, saves a draft, and explicitly publishes it. Publishing a replacement supersedes the previous plan; published rows are never edited in place.

The authenticated Admin endpoints are:

- `GET /api/v1/admin/curriculum-plans/{subject_id}` returns the current draft or publication plus the approved units. Before the first save it returns `not_started` with six empty periods.
- `POST /api/v1/admin/curriculum-plans/{subject_id}` saves a new draft or replaces the current draft's assignments.
- `POST /api/v1/admin/curriculum-plans/{subject_id}/publish` publishes the draft after subject and textbook confirmation.
- `GET /api/v1/admin/students/{student_id}/coverage?subjectId=...` diagnoses cumulative coverage.
- `GET /api/v1/admin/students/{student_id}/question-pool?subjectId=...&questionCount=...&marks=...` reports eligible capacity and exact shortages.

The service accepts only units from the currently published textbook for the same course and subject. A unit is assigned once, to its introduction period. Student coverage is the union of assignments for the student's saved progression entries through the current entry. Thus Grade 10 Term2 includes the configured Grade 10 Term1 and Term2 units. Every reached progression period must have coverage; otherwise assessment creation fails closed.

`assessment_curriculum_snapshots` freezes the published plan, current Grade and Term, progression entries, and covered unit IDs under an idempotent assessment reference. A later plan publication changes new assessments only. Question-pool diagnostics require every mapping of a published question to fall inside the frozen eligible unit set and never broaden coverage to satisfy requested counts or marks.
