# Question-paper analysis

Standard: `akuru-igcse-pastpapers` 1.2.0

Last updated: 2026-10-31

## Identity and evidence

MUST identify awarding body, qualification, subject, specification, year/session, component and regional variant. Preserve the original PDF and hash. Keep PDF page index, printed page label and bounding boxes distinct. Source locations must resolve to the actual uploaded document version; never fabricate IDs.

## Extraction mode and uncertainty

Classify each page or region as native text, scanned image or mixed content. Retain usable native text and vector geometry; use OCR/vision for image-only regions without duplicating content already extracted from the same page. Resolve reading order from layout before paragraph reconstruction. Preserve headings, instructions, lists, equations and table cells while joining typographic line wraps.

Record extraction confidence separately from completeness. Native text can still have broken glyphs, missing symbols or a wrong reading order; high OCR confidence cannot establish a complete graph or correct subpart association. Compare uncertain science notation and every essential visual with the original rendered page. Keep unreadable spans unresolved rather than inventing replacements.

## Boundaries and reading order

- Use question labels, indentation, coordinates and continuation context to identify question and subpart boundaries. A mark allocation is metadata, never an end-of-part delimiter.
- Preserve nested labels such as `c(i)` and `c(ii)`. Attach their common context to parent `c`, not only to the first child.
- Carry a question across pages until the next valid boundary or question total. Do not drop content following the final mark allocation.
- Detect columns and reading order before combining lines. Distinguish labels from formula notation, list numbering, option letters and prose.
- Keep text preceding the first subpart as a shared stem. Render inherited context once, in the correct order, when presenting a child part.
- Flag uncertain boundaries rather than shifting text into the next part by default.

## Content roles

Store question wording, answer spaces, choices, tables and diagrams separately. Dotted writing lines and numbered response slots belong to response layout, not prompt text. Preserve meaningful completion blanks inside equations, tables and sentences. A leading dotted-line block is a review warning; it is not an absolute reason to delete punctuation.

For multiple-choice parts, retain every option label, wording and order; detect the complete option set from the source rather than assuming four options for every paper. Preserve instructions about how many choices to select. Checkboxes become response controls, not standalone diagram assets. Keep the correct option in the private rubric only.

Normalise typographic line wraps without changing meaning. Preserve charges, subscripts, superscripts, units, inequalities, minus signs and numerical precision. Do not silently repair an uncertain chemical formula.

## Visuals and response areas

Associate each diagram/table with all and only the parts requiring it. Shared visuals are explicitly scoped. Crops must include necessary labels, legends, axes, units and scales; avoid both clipped labels and unrelated content. Provide a draft accessible description that describes supplied information without solving the question. Preserve tables as structured data where reliable and retain their source image.

Treat text labels positioned outside a diagram’s drawn border as part of the diagram when they identify its lines, arrows, components or data. Expand the crop to include those labels, even when PDF extraction stores them as separate text blocks. Verify the crop against the full source page; do not treat diagram labels as standalone captions or omit them after OCR. Preserve the original geometry and aspect ratio. For measurement questions, retain access to the original-scale PDF; a resized screen crop is not a calibrated ruler.

Represent numbered answer slots, written responses, formula inputs, graph drawing and table completion explicitly. Do not require every question to have a visual. No scientific diagrams are required for 1C Q2; its option boxes are controls.

### Graph completeness and crop verification

For every graph, inspect the original full page and check both axis titles, units (including ° and superscript powers), numbered scales, tick marks, grid extents, origin, any axis breaks/logarithmic scales, legends, plotted symbols/lines and explanatory annotations **where supplied by the source**. Treat nearby text identifying an axis as part of the visual even when extracted as a separate block. A vector cluster or image bounding box is only a candidate, not the final crop. Use layout/context to expand it; fixed padding alone cannot establish completeness.

Retain a small clear margin around all required content and inspect the final rendered crop at readable resolution. Do not stretch, redraw, truncate scale ends or add missing labels/points that the Student is meant to provide. A blank plotting grid must remain blank; scheme solutions belong to private model-answer assets. Record any verified omission against the exact question/subpart and source page before approval.

For June 2025 1C Q7, retain the complete source graph: Y-axis **Temperature in °C**, numbered 20.0, 25.0 and 30.0; X-axis **Volume of sulfuric acid in cm³**, numbered 0.0 through 40.0 in steps of 10.0; all intermediate grid lines and the separate results table. These values describe this source, not a fixed template for other graphs.

### Tables and visual lifecycle

Preserve column/row headings, units, merged headers, blank response cells, numerical precision and row-to-column relationships. Reconcile extracted cells against the source image; do not flatten a table into a sequence that loses which value belongs to which heading. Keep the source image even when structured data is reliable. A partial table must be visibly flagged.

Replacing a clipped crop must update every affected question/subpart association while preserving unaffected visuals, wording, markings and review decisions. Retain old assets for frozen published/attempt snapshots. Re-read the saved associations and inspect the actual downloaded replacement image; a successful API response alone is insufficient. Remove only the specific warning resolved by the verified replacement, retaining any unrelated blockers. Proposed visual selection and question/subpart approval remain separate decisions.

## Review output

Produce an unapproved proposal with marks, source locations, content roles, uncertain regions and issues. Reconcile subpart totals and the complete paper inventory. Preserve all Admin edits on re-analysis; produce a proposed diff for changed content.

## Stable curriculum coverage and textbook page evidence

Map each subpart to stable topic references. Explain the curriculum relationship without embedding PDF page positions in the coverage reason. Store page evidence separately as topic reference, Visual reference document-version ID, PDF page position and reviewed printed-page label. Use only verified pages from a published visual source in the same subject. Primary-text repagination does not change this evidence. Retain historical source references and flag them for revalidation when no longer available in the current publication. Missing page evidence may be saved in a draft; never invent a page match.

## Named structure captions: June 2025 1C Q8 regression

Include the printed names beneath separate structures (for example, diamond and graphite), even when the PDF stores them as independent text blocks outside the vector drawing bounds. Keep each caption with its own structure and applicable subpart. Compare against the complete source page; do not infer a name from the structure or borrow a neighbouring caption. The `visual-layout-v2` native-text proposal heuristic expands nearby compact labels conservatively, but does not approve candidates, handle every scanned/rotated layout, or rewrite existing reviewed crops. Existing incomplete crops need an explicit reviewed replacement.
