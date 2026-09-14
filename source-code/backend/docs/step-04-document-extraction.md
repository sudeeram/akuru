# Deterministic document extraction

AKURU's `deterministic-v1` worker stage preserves the source representation before any AI interpretation. PyMuPDF opens PDFs and supported images, renders every page as PNG at the configured review DPI, and extracts native PDF text with point-based bounding boxes. Sparse and image-only pages are sent to Tesseract OCR. English is used for most subjects; French requests French plus English when both language packs are installed and records a review-visible fallback when they are not.

## Stored provenance

`document_pages` stores the source page number, physical PDF dimensions, rendered-page asset, extraction method, confidence and review flag. `document_blocks` stores ordered headings, paragraphs, tables, questions, subparts, answer spaces, equations and diagrams. Every block records its page, bounding box and coordinate space, extraction method, confidence and review flag.

Derived bytes remain in private object storage and their metadata stays in `document_assets`:

- `page_render` is the complete page image used for Admin comparison and later visual models.
- `embedded_image` preserves the embedded image bytes, while `diagram_crop` preserves the region as it appeared on the rendered page; the matching `diagram` block prevents image-only questions from disappearing.
- `equation_crop` preserves the exact source pixels beside a deterministic LaTeX candidate.

Native PDF coordinates use `pdf_points`. OCR coordinates use normalized values between 0 and 1, allowing the browser to overlay blocks at any display size. Asset downloads use authenticated Admin endpoints and private, no-store responses.

## Detection and review policy

Layout recognition in this stage is deliberately deterministic. Font size and casing suggest headings; anchored numbering suggests questions and subparts; dotted/underscored lines suggest answer spaces; PyMuPDF supplies table regions; and mathematical symbols suggest equation candidates. These labels are proposals for Admin review. Equation candidates and diagram regions are always flagged because heuristic classification and symbol-to-LaTeX conversion are not sufficient for publication.

OCR word confidence is aggregated per line. Lines below 85% confidence, pages without blocks, unavailable requested language data, equations and diagrams require review. The pipeline never invents omitted text or silently discards a diagram-only page.

## API

- `GET /api/v1/documents/{document_id}/extraction` returns ordered pages and blocks.
- `GET /api/v1/documents/{document_id}/assets/{asset_id}/content` returns an authorized rendered page or crop.

The Admin document review screen loads this data after processing reaches `needs_review`, displays the rendered source page, and identifies blocks requiring attention.

## Limits

Deterministic LaTeX conversion handles common text-layer symbols and preserves the crop for correction. Complex two-dimensional notation, handwriting, charts without embedded image regions, merged table cells and unusual layouts require later reviewed extraction improvements and may use the Step 5 AI provider only as a proposal source. Publication continues to require Admin approval.
