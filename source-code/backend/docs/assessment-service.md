# AKURU assessment service

Step 12 assesses a submitted practice question, mock paper or official past paper against the immutable question and rubric captured when the assessment began.

## Flow

1. The student saves answers and submits the assessment.
2. The frontend calls `POST /api/v1/assessments/{assessmentId}/evaluate` with an idempotency key.
3. The backend builds an evidence bundle from the frozen question, marking points, accepted alternatives, examiner advice and approved same-subject textbook chunks for the mapped units.
4. The first AI pass decides each official marking point and cites the student's evidence.
5. The second AI pass reconciles those decisions and produces an exam-ready answer, teaching explanation, strengths, mistakes, unit evidence and recommendations.
6. Backend validation rejects missing, changed or duplicated marking points and prevents the total from exceeding the frozen question maximum.
7. Results below `AKURU_ASSESSMENT_CONFIDENCE_THRESHOLD`, subjective English results below 0.90, and answers with attached working are marked `needs_review`. Their provisional score is not included in the student progress totals.

## Traceability and history

`assessment_results` stores the schema version, answer revision, awarded marks, every point decision and student citation, both structured AI passes, provider and model, full prompt snapshot, frozen rubric, and exact source manifest. Reusing an idempotency key returns the same result. A new key performs a reassessment and appends a version without changing earlier results.

Source documents remain private. The response contains feedback but does not expose the internal source manifest or model audit fields. All assessment routes require a student session, CSRF protection for writes, and ownership checks.

## Local configuration

Configure the backend-only OpenAI accounts as documented in [ai-provider.md](ai-provider.md). The Admin portal controls their unique priorities. Set the publication threshold and evidence limit in `.env`:

```dotenv
AKURU_ASSESSMENT_CONFIDENCE_THRESHOLD=0.75
AKURU_ASSESSMENT_CONTEXT_CHUNKS=12
```

The current call is synchronous. A later scale-out step can place evaluation on the existing Redis worker queue without changing the result schema or API response.
