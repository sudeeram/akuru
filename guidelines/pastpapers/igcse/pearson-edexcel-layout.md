# Pearson Edexcel layout profile

Profile ID: `pearson-edexcel-igcse`  
Profile version: `1.0.0`  
Last updated: 2026-10-21

Initially verified against June 2025 International GCSE Chemistry 1C pages used in the reference examples. Detect the profile from document identity and actual page geometry; do not assume that every Pearson paper or year has the same layout.

## Question-paper page regions

Use the enclosing question-content border where reliably detectable. Detect repeated side warnings, footer codes, barcodes, registration marks, page numbers and turn-over notices. Exclude them from question wording while preserving them in the original source.

Use coordinates rather than PDF text-stream order: barcode text may appear before question text in extraction. Do not delete every extracted token after a barcode. Do not blindly apply a fixed rectangle to covers, inserts, landscape pages or unusual diagrams. If border detection is uncertain, use repeated-margin evidence and flag the region for review. Preserve meaningful footnotes and instructions inside the content region.

## Content recognition

- Marks in parentheses may appear before answer lines or A–D options. They do not terminate a part.
- Numbered response lines are not new subparts.
- Nested roman-numeral labels inherit the lettered parent context.
- Preserve option letters, wording and selection instructions even when boxes are vector graphics.
- Continue parts across pages. Question totals are useful reconciliation evidence, not prompt wording.
- Check figure captions, axes and labels outside detected vector clusters before proposing a crop.

## Scheme and report profiles

The question-paper border rules must not be applied to scheme tables or report pages. Scheme extraction follows cells and continued rows; report extraction follows headings, commentary panels and candidate-image groups. Handle PDF pages with both native text and embedded scanned images as mixed-content pages.

## Exceptions

Record profile/version, detected region, confidence and any override. Preserve the source for Admin comparison. Add a regression example before broadening a rule to a new layout or year.
