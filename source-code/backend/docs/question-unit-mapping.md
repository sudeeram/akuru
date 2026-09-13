# Reviewed question-to-unit mapping

Step 9 maps each immutable, published paper question to one or more units in the exact approved textbook content version frozen onto that paper. Mappings are weighted so later mastery calculations can apportion evidence across units.

The Admin endpoints are:

- `GET /api/v1/questions/papers/{paper_id}/unit-mappings` returns the published questions and only the allowed same-course, same-subject, same-edition units.
- `POST /api/v1/questions/{question_id}/unit-mapping/suggest` returns advisory metadata/OpenAI suggestions.
- `POST /api/v1/questions/{question_id}/unit-mapping` saves an Admin-reviewed draft.
- `POST /api/v1/questions/{question_id}/unit-mapping/publish` confirms the mapping permanently.

Metadata suggestions compare the question and shared stem with approved unit titles, summaries, sections, concepts and definitions. If an enabled OpenAI account has a configured credential alias, the same operation sends only the question and this filtered unit list through the Step 5A account router using the versioned `unit-mapping` prompt and a strict structured-output schema. Returned unit codes are checked again against the relational allow-list. Provider failure falls back to the deterministic metadata proposal; neither path writes an authoritative mapping.

Admin selects every required unit and assigns integer percentages totaling exactly 100. Saving is transactional and rejects empty mappings, duplicates, invalid totals, pending/superseded questions, and units from another course, subject, textbook or edition. Confirmation repeats those checks, records the Admin and timestamp, and makes the rows immutable. Correcting a confirmed mapping requires a corrected question/material version so historical assessments remain reproducible.

The eligibility diagnostic now reads published official question versions with confirmed mappings. A multi-unit question is eligible only if every mapped unit is inside the student's cumulative published coverage. Similarity and AI output never override these relational rules.
