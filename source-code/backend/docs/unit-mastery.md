# Unit mastery and confidence

Step 14 turns published assessment results into a separate mastery record for each student and textbook unit. Students can read their own records. A parent can read only records belonging to a linked child. Administrators do not use the student mastery endpoint.

## Score calculation

Each published result contributes its awarded-mark ratio on a 0–10 scale. The contribution is weighted by:

- the square root of available marks, so larger questions matter more without overwhelming all smaller evidence;
- the approved percentage for each mapped unit;
- question difficulty;
- assessment mode, with official papers and timed mocks weighted above practice;
- recorded hint use and retries;
- assessment confidence; and
- recency, with older evidence gradually reduced to a floor instead of discarded.

Only the latest published assessment result for an immutable assessment question is used in the current score. Reassessment therefore replaces that question's current evidence while preserving every historical mastery event. The internal score uses five decimal places and the portal displays one decimal place out of ten.

## Dimensions and confidence

AKURU records knowledge, application, method, accuracy, reasoning, communication and retention. Marking-point kinds populate method, accuracy and communication directly. Criterion and rationale terms identify application and reasoning; the result mark ratio supplies general knowledge evidence. Retention begins when later evidence follows earlier evidence in the unit by at least seven days.

Confidence describes the evidence behind a score rather than the score itself. It uses evidence count, assessment-mode and difficulty variety, elapsed coverage, total evidence weight and recency. Low-confidence scores are marked `provisional`. One easy question therefore may show a high score but cannot claim high confidence.

## History and API

`unit_mastery` stores the current snapshot, `unit_mastery_dimensions` stores its seven dimension snapshots, and `unit_mastery_events` stores the previous score, new score, confidence change and factors for every contributing published result. Event rows are append-only in the service and retain the result reference used to create them.

The authenticated endpoint is `GET /api/v1/mastery/students/{student_id}` with optional `subjectId`. Portal bootstrap responses also include the authorized student's mastery summaries. Practice hints are recorded through `POST /api/v1/assessments/{assessment_id}/questions/{question_id}/hint`; mock and official-paper modes reject hints.
