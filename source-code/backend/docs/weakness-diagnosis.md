# Weakness diagnosis and recommendations

Step 15 converts missed published marking evidence into specific, source-grounded next actions. Diagnosis runs only after an assessment result is published. Results awaiting human review do not alter diagnoses or recommendations.

## Subject-aware diagnosis

AKURU classifies small mistakes, conceptual mistakes and missed marking points with a subject-specific taxonomy. Categories cover formula selection, units, calculations, graph interpretation, terminology, experimental variables, causal reasoning, scenario application, trade-offs, evidence selection, organisation, vocabulary, grammar, communication and command-word response. The original evidence strings, result, frozen question, unit, severity, assessment confidence and occurrence number are retained.

Recurrence is counted by student, unit and category. A sibling's work is never included in that count.

## Recommendation controls

Recommendations are created only when an active retrieval chunk exists for an approved textbook in the same subject and unit. Each recommendation links the diagnosis, covered unit, source document and page, and one of four activities: review, targeted practice, spaced retry or short unit check.

Question activities are chosen from published iGCSE past-paper questions with confirmed mappings. Every mapped unit for the selected question must be within the student's cumulative published coverage. This uses server-side eligibility; a client cannot supply or broaden the question pool.

Recommendations based on assessment confidence below 0.85, provisional mastery, or subjective English/French communication evidence start as `pending_review`. A linked parent or an administrator can approve or reject them. Students receive approved recommendations only. Parents can see only their linked children's recommendations; administrators can query the review queue across students.

The authenticated endpoints are:

- `GET /api/v1/recommendations`, optionally filtered by `studentId`;
- `POST /api/v1/recommendations/{id}/review` for Parent/Admin decisions; and
- the portal state, which includes role-filtered recommendations for each visible student.
