# Official paper, marking-scheme and examiner-report review

Step 8 turns deterministic document extraction into immutable, reviewed official assessment material. The workflow is Admin-only and uses the existing private document and asset endpoints.

For a past paper, the proposal groups each detected question or subpart with following text, equations, tables and diagram assets until the next question. It preserves shared introductory text, marks, parent/subpart identifiers and every page/block/bounding-box source location. For a marking scheme, it records question/subpart, maximum marks, typed marking points (`method`, `accuracy`, `independent`, `communication` or `other`), accepted alternatives and sources. Examiner-report records retain question links, common mistakes, advice and sources.

The endpoints are:

- `POST /api/v1/documents/{id}/official-review/propose`
- `GET /api/v1/documents/{id}/official-review`
- `POST /api/v1/documents/{id}/official-review`
- `POST /api/v1/documents/{id}/official-review/publish`

Admin reviews the rendered source beside the editable proposal, reconciles the expected inventory count, and attests that the entire document was checked. Saving rejects duplicate numbers, count mismatches, content for the wrong document kind, foreign block locations and foreign assets. Publication rejects empty or unattested inventories.

A marking scheme or examiner report must reference its same-course, same-subject source paper. The paper must already be published and every linked number must exist in that published version. Marking schemes must cover the complete paper inventory and their maximum marks must match. Publication freezes the exact source-paper version, so later paper corrections do not silently change historical links. Corrections create a new material version and supersede the earlier publication.

Step 9 will add reviewed unit mappings to these published question versions. Until that mapping is approved, Step 8 publications do not enter student candidate pools.
