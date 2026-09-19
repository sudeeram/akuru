# Chemistry source configuration and reviewed visuals

The Admin textbook Topic workflow supports a safe production configuration without direct database changes.

For a Topic with a clean v2.1 PDF and an original scan, the Admin can apply the recommended roles. AKURU requires exactly one filename identifiable as the clean v2.1 source, assigns it as canonical primary text, and assigns the remaining scan as a visual reference. The operation is explicit, confirmed in the frontend, audited, and does not publish content.

The Topic review checklist reports unresolved pages and blocks, formula/equation blocks, tables, image/diagram blocks, and visual selections awaiting approval. Extraction completion remains separate from Topic publication.

Visual-reference OCR text never enters normal retrieval. The Admin may open the visual asset manager and select extracted diagrams, images, or tables. Approval requires a useful accessible text alternative. Approved selections store:

- Topic, document and document-version ownership;
- source block and document asset;
- kind, exact page, printed page and bounding box;
- caption and accessible text;
- asset checksum;
- selecting and reviewing actors and timestamps.

Pending selected assets block Topic publication. Rejected and unselected assets do not enter a Topic version. Approved assets are frozen into the next immutable Topic content version's source and extraction manifests. Text retrieval chunks continue to come only from reviewed primary, supporting, and reference text.

The authenticated Admin endpoints live below:

`/api/v1/admin/textbooks/{textbookRef}/topics/{topicRef}`

- `GET /review-checklist`
- `POST /sources/apply-recommended-roles`
- `GET /sources/{documentId}/visual-assets`
- `PATCH /sources/{documentId}/visual-assets/{assetRef}`

