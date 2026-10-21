# Question-paper analysis

Standard: `akuru-igcse-pastpapers` 1.1.0  
Last updated: 2026-10-21

## Identity and evidence

MUST identify awarding body, qualification, subject, specification, year/session, component and regional variant. Preserve the original PDF and hash. Keep PDF page index, printed page label and bounding boxes distinct. Source locations must resolve to the actual uploaded document version; never fabricate IDs.

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

Represent numbered answer slots, written responses, formula inputs, graph drawing and table completion explicitly. Do not require every question to have a visual. No scientific diagrams are required for 1C Q2; its option boxes are controls.

## Review output

Produce an unapproved proposal with marks, source locations, content roles, uncertain regions and issues. Reconcile subpart totals and the complete paper inventory. Preserve all Admin edits on re-analysis; produce a proposed diff for changed content.
