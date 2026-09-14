# Textbook extraction and publication

Step 6 turns a deterministically extracted textbook into an Admin-reviewed, immutable unit vocabulary. AI and extraction output remain proposals; only a published content version is authoritative.

## Workflow

1. Admin uploads a textbook with course, subject and edition. Edition is mandatory.
2. The document worker renders pages and retains text, equations, diagrams, coordinates and confidence.
3. **Propose units** creates a draft from the extracted headings and page evidence. It includes chapter, unit, sections, definitions, concepts, equations, examples, diagrams and page ranges. This conservative proposal works without a paid provider; structured OpenAI enrichment can use the same draft schema when enabled.
4. Admin compares the editable draft with the source page images, corrects every field and saves it.
5. Publication requires explicit course, subject and edition confirmations and at least one valid unit.
6. Publication freezes the content version and creates its authoritative `textbook_units`. Later edits create a new draft version. Publishing that version supersedes the old publication without modifying its rows.

Only Admin endpoints may read or mutate the review. Every save and publication adds a document event with actor, source document version, content version and unit count.

## Tables

- `textbook_content_versions` identifies the immutable reviewed edition and its lifecycle: `draft`, `published`, or `superseded`.
- `textbook_unit_versions` retains the complete reviewed hierarchy and evidence fields for that content version.
- `textbook_units` is the stable published vocabulary consumed by curriculum coverage and question mapping. Each row points back to its content version.

Past-paper ingestion queries for a published same-course, same-subject textbook content version. An uploaded or draft textbook does not satisfy this prerequisite.

## Endpoints

- `GET /api/v1/documents/{document_id}/textbook-review`
- `POST /api/v1/documents/{document_id}/textbook-review/propose`
- `POST /api/v1/documents/{document_id}/textbook-review`
- `POST /api/v1/documents/{document_id}/textbook-review/publish`

All endpoints require an authenticated Admin. Mutations also require the session CSRF token.
