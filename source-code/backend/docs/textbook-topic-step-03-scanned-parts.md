# Textbook topics Step 3: scanned textbook parts

Step 3 attaches each uploaded PDF or image to a previously selected logical textbook topic. The uploaded file remains a versioned private `Document`, while `textbook_topic_documents` records its textbook, topic, role, order, printed-page range and review state.

## Upload and isolation

- Only an authenticated Admin with a CSRF token can upload or review textbook parts.
- The single-file route accepts PDF, PNG and JPEG bytes for one public textbook and topic reference. The batch route accepts up to 20 encoded items and a bounded aggregate size.
- The backend derives course, subject, edition, publisher and group from the selected textbook and topic. Clients cannot use upload metadata to cross subjects or textbooks.
- Roles are `primary`, `supporting` or `reference`. Multiple files and roles may be attached to one topic.
- Every request has a topic-scoped idempotency key. Retrying the same request returns the original document and job, while a duplicate checksum under another request is rejected.
- Originals and derived assets use the configured private object-storage backend. With local storage they remain under `AKURU_STORAGE_LOCAL_ROOT`, outside the release checkout.
- Filename suggestions are deterministic and advisory. Admin must select or confirm the destination topic.

## Extraction and review

The existing isolated worker performs native extraction and falls back to Tesseract OCR for image-only pages. It stores:

- the original rendered page and a separate normalized review image;
- physical PDF page number and editable printed-page label;
- OCR languages, extraction method, confidence, reading order and bounding boxes;
- contrast, resolution, orientation, rotation and deskew diagnostics;
- retained diagram, image, table and equation crops.

Equations, chemical notation, subscripts, superscripts, reaction arrows, tables, diagrams, low-confidence OCR and language fallback are marked for Admin review. Admin correction endpoints update block type, text, LaTeX, reading order and printed-page labels and write document audit events. Topic links move to `needs_review` after extraction and `failed` after a processing failure. Step 4 will add independent topic-content publication and approved retrieval chunks; no Step 3 extraction is published automatically.

Deterministic extraction always remains available. Any future multimodal provider enhancement must remain optional, provider-configured and subject to the same Admin review before publication.
