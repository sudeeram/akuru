# Chemistry Topic 1 — screenshot preparation pilot

Prepared: 2026-11-01. Guideline: `akuru-igcse-textbook-screenshots` v1.0.0.

## Scope and decision

Local, operator-assisted preparation of 12 screenshot pages (printed pages 2–13), compared with the owner's manually prepared v2.2 primary PDF. No AKURU API calls, production writes, automatic publication or application-code changes were made.

Proceed with screenshot-based AI preparation for subsequent topics. The owner should not need to hand-typeset a replacement primary PDF just to supply teaching context. Keep the original pages for visual reference and focused review. This is evidence for the preparation approach, not approval to replace existing published content or bypass review gates.

## Outputs and provenance

Private source and derivatives remain under the Git-ignored `textbooks/igcse/chemistry/Unit1-Topic1/ai-prepared-v1/` directory:

- `review.html`: assembled reading/review document, source-page links and original figure crops.
- `topic-package.json` / `topic-content.md`: structured draft and readable representation.
- `review-issues.md`: four explicit exception decisions.
- `validation.json`, `render-validation.json`: executed checks.
- `benchmark-report.md`, `benchmark-results.json`: separate comparison.
- `source-first-freeze.json`: SHA256 of candidate before comparison.

The package builder reads screenshots, not v2.2. Previous discussion had already inspected v2.2, so the trial was not formally blinded. Method: Codex visual-assisted preparation with local deterministic rendering and checks; exact model ID unavailable and not invented. No API usage/cost claim is made. Source hashes, crop bounds, printed-page references and the guideline version are recorded in the private package.

Frozen package SHA256: `b35b0f23cc69de8ad5afcd9a4a726060a443503bc2c9c66c2639142ef105f15d`.

## Results

| Measure | Result |
|---|---|
| Source pages | 12 |
| Explicit learning objectives | 7, with Chemistry-only scope distinguished |
| Teaching blocks | 57; reconstructed reading text, not verbatim transcription |
| Source figures | 19 crops, visually checked; external labels retained |
| Structured tables | 4 |
| Exercises | 6 root questions; 25 leaf parts |
| Structure/reference/numerical validation | 37 passed checks |
| Targeted vocabulary/value presence | Candidate 28/28; v2.2 native text 28/28 |
| Desktop/mobile HTML | 1280px and 390px; all 19 images loaded, no document horizontal overflow or script errors |
| Focused exceptions | 4; unresolved draft decisions |

Presence checks do not establish comprehension or global extraction accuracy. No WER/CER, official difficulty calibration, production retrieval, student outcomes, timed human effort or cost saving was measured. Manual visual comparison covered the source pages/figure crops and the v2.2 rendered contact sheets, with a full-size notation spot-check. It was not an independent character-by-character gold transcription audit.

## Findings carried into the guideline

- Preserve original printed-page identity despite a reflowed primary PDF having different PDF page numbers.
- Keep diagram labels, axes, legends, captions and accessible descriptions with the correct visual, including labels outside the apparent drawing.
- Represent tables as cells with units and explicit missing values, not flattened prose.
- Preserve nested exercise context and do not infer official marks, answers or difficulty from an unexplained badge.
- Validate chemistry letter case, subscripts, units and arithmetic against source pixels; native PDF text can also contain `I`/`l` ambiguity.
- Separate literal source claims from proposed scientific clarification. Four exceptions concern solute/solvent wording, kinetic-energy context, saturation/excess-solid context and a long particle-mass literal.
- Current OCR can be damaged by TSV quote parsing, a subsequent coordinate re-sort and sidebar classification. Diagnostic experiments are not deployed fixes.

## Remaining adoption work

1. Review the four exceptions and sample the assembled content against source pages; obtain Admin approval.
2. Implement a supported, audited draft-package import/review path if adopting this format. The package is not an existing AKURU endpoint payload.
3. Fix the observed OCR defects with targeted regression fixtures, without adding licensed source pages to Git.
4. Test real published-topic retrieval, citations, approved visuals and answer grounding before release. Use specification and past-paper evidence for exam demand and marking; textbook task estimates cannot replace them.
5. Repeat on a second topic without a manually prepared primary PDF to evaluate generalisation and record actual human review effort.

No release/import gates are marked complete by this pilot. The structured content and derivatives are intentionally excluded from Git; only this sanitised methodology and results are tracked.

## Follow-on local implementation — 2026-11-01

After the frozen pilot, a separate authenticated Admin ZIP import/review workflow was implemented and tested locally. See the backend package guide and ongoing `TODO-SCREENSHOT-TEXTBOOK-PACKAGES.md`. The original pilot results above remain unchanged; a rollback-only integration test now additionally covers versioned publication, figure matching and separate visual-reference printed-page mapping. No production import occurred and the four real review decisions remain awaiting Admin approval.
