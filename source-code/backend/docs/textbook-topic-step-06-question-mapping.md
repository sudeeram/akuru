# Step 6 — Past-paper topic mapping

Published past-paper questions can now be mapped to the smallest reviewed textbook topics. New papers record the active logical textbook edition. Mapping candidates are restricted to topics whose structure and content are both published in that exact iGCSE course, subject and edition.

The Admin endpoints are:

- `GET /api/v1/questions/papers/{paperId}/topic-mappings`
- `POST /api/v1/questions/{questionId}/topic-mapping/suggest`
- `POST /api/v1/questions/{questionId}/topic-mapping`
- `POST /api/v1/questions/{questionId}/topic-mapping/publish`

A mapping may include topics from several Unit or Module groups within the same subject. Weights total 100 percent, each topic occurs once, and at least one topic is mandatory. Confirmed mappings are immutable on that question version. Corrections require a corrected question version, preserving assessment history and audit evidence.

Candidate responses are grouped by the textbook's Unit or Module structure. Question responses include prompt, shared stem, source page evidence, mapping confidence and rationale, mandatory status, and aggregate weights by parent group. Paper responses report confirmed questions against the complete question inventory.

Student question eligibility uses topic mappings whenever the published curriculum plan uses topics. Every mandatory confirmed topic must be in cumulative student coverage. Similarity, optional topics and pool shortages never broaden the syllabus. Diagnostics name missing required topics. Legacy unit mappings remain temporarily available for old data until Step 7 completes the downstream migration.
