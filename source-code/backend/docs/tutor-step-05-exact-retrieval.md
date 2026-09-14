# Tutor Step 5 — Exact textbook retrieval and citation

Tutor retrieval is available only to an authenticated Student in an active practice tutor session with the tools capability enabled. `POST /api/v1/tutoring/sessions/{sessionRef}/sources/search` accepts a query, optional textbook edition and result limit.

Before pgvector ranking, the service resolves current cumulative curriculum coverage and filters candidates by iGCSE course, enrolled session subject, active eligible unit, published textbook content version, completed source document version, published nonremoved document and approved extraction block. An edition request must match that exact published content version. This ordering prevents semantic similarity from broadening authorization or crossing units and editions.

An `exact` result includes an opaque citation reference, displayed textbook title and edition, immutable document version, block kind, passage, bounding box, confidence and opaque asset reference. `pdfPageIndex` is zero-based for viewers and `pdfPageNumber` is one-based. `printedPageLabel` is extracted from PDF page-label metadata and remains separate, so printed page 101 may correctly resolve to PDF page 2. `pageReference` displays both values when they differ.

`GET .../sources/{citationRef}` revalidates the active session, current unit and exact published versions. `GET .../context` returns neighboring approved chunks from only the same content version and unit. `GET .../asset` serves the extraction crop when present or its page render, with the existing local/OCI object-storage abstraction and `private, no-store` response headers. Opaque references do not authorize access by themselves.

If an edition is unavailable or no result reaches `AKURU_TUTOR_RETRIEVAL_MIN_SCORE`, search returns `evidence_insufficient` with no citations. Tutor prompts must treat that status as a prohibition on mentioning a textbook page, edition or quotation. Step 6 will consume this contract when generating Tutor replies.

Migration `e5a1bc704d62` adds `document_pages.printed_page_label`. Existing rows remain nullable and can be populated by reprocessing their source PDF.
