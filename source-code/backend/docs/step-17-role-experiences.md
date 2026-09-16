# Step 17 — Role-specific experiences

**Status: Implemented; final verification recorded in `source-code/todo/TODO.md`.**

Step 17 presents the evidence created by Steps 12–16 in a form each role can act on.

## Student

Answer reviews show marks, result confidence and version, strengths, small and conceptual mistakes, the evidence used for every marking point, an improved exam-ready answer, and a teaching explanation. Unit cards show the 0–10 mastery score, confidence, recent trend, dimension scores, score history, observed mistake patterns, and approved next activities. Provisional and empty states say when more assessed evidence is required.

## Parent

The portal loads assessments, mastery, recommendations, and plans only for children linked to the authenticated parent. The review page groups summaries by child, shows longer-term unit events, and provides approval or rejection tasks for recommendations that require adult review.

## Admin

Document extraction review uses a side-by-side original-page and extracted-content layout. The Assessment audit route lists every versioned result with its student, marks, confidence, provider/model, prompt and subject-engine versions, deterministic checks, marking evidence, review reasons, and frozen source manifest. Reassessment creates a new immutable result version through the normal two-pass assessment service; it does not overwrite the earlier audit record.

## API and accessibility

- `GET /api/v1/assessments/admin/audit` is Admin-only.
- `POST /api/v1/assessments/admin/{assessment_id}/reassess` is Admin-only and CSRF protected.
- Parent assessment data is selected using linked student IDs on the server.
- Equations have readable labels, diagrams have descriptions and an enlarged view, interactive controls are keyboard-operable, and failures provide retry actions where remote loading occurs.


## Human review and transaction guarantees

`POST /api/v1/assessments/results/{result_id}/review` accepts Parent/Admin reviews with CSRF protection. Parent ownership is checked against the assessment student's current linked parent. Point IDs, criteria and maxima must match the frozen official rubric. An unchanged retry returns the original published review; a new request against an older result receives 409. Reviews create a new immutable result and AuditEvent with reviewer and reason. Original model confidence remains unchanged. Superseded recommendations are rejected and new diagnosis is based on the reviewed mistakes and marking decisions.

Assessment evaluation and human review lock the assessment row to serialize writes. Provider health and usage commits use a separate session so they cannot release this lock. Results, mastery and diagnosis are committed together, including results that still need review. No schema migration or additional package installation is required.

Admin working downloads use the same private content endpoint as linked Parents/Students. The audit includes typed answers and working links. Historical unit events remain stored; the role screens explicitly label their latest-ten-event view.
