# Low priority — Advanced extraction, assessment routing and voice delegation

**Status: Future work — not started. Begin after high and medium priorities meet their release gates.**

This plan contains larger or more operationally expensive work. It improves difficult scans and structured content, extends model routing into assessment/document workflows, and connects realtime voice to the reviewed text Tutor policies.

## Delivery sequence

1. Evaluate and complete the local layout-aware OCR prototype.
2. Add photographed-page preparation and multi-region OCR.
3. Add structured tables, equations and advanced diagram handling.
4. Extend model policies to document classification and difficult interpretation.
5. Evaluate assessment-marking policies independently.
6. Add bounded realtime voice delegation after text tutoring is stable.

## Future Step 5 — Complete and evaluate layout-aware OCR

**Current state:** A local, uncommitted prototype exists. It has not been merged, deployed or used to reprocess production documents. The prototype is evidence for this future step, not a completed implementation.

### Local prototype already available for review

- [ ] Raise scanned-page rendering from 180 DPI to 240 DPI so Tesseract receives clearer character shapes.
- [ ] Apply deterministic automatic contrast normalization to every rendered scan while retaining the original page image.
- [ ] Change Tesseract from page segmentation mode 6 to automatic page segmentation mode 3.
- [ ] Detect a basic two-column layout from OCR bounding boxes and read the left column before the right column.
- [ ] Preserve spanning headings and record `single`, `left`, `right` or `spanning` column metadata with deterministic reading order.
- [ ] Preserve Tesseract block, paragraph and line identifiers for later reconstruction and diagnosis.
- [ ] Narrow the scientific-notation detector so ordinary words such as `acid`, `alkali`, `mole` and `ion` do not create false review flags by themselves.
- [ ] Retain the local unit test for two-column reading order and review the prototype against the complete extraction test suite.

These items remain unchecked until the prototype is reviewed, committed, evaluated against representative documents and released through the normal production gates.

### Image preparation still required

- [ ] Detect and correct page orientation rather than recording a fixed zero-degree result.
- [ ] Deskew slightly rotated scans and record the measured and applied angle.
- [ ] Detect page boundaries and correct perspective or camera keystone distortion for photographed pages.
- [ ] Reduce shadows, paper texture, uneven illumination and reverse-side bleed-through without erasing faint characters or diagram lines.
- [ ] Compare grayscale, adaptive-threshold, sharpened and colour-preserving variants per region instead of applying one treatment to every page.
- [ ] Detect blur and insufficient resolution early and give the Admin an actionable capture-quality warning.
- [ ] Keep every original, normalized and selected OCR input as private review evidence with processing-version metadata.

### Layout and multi-pass OCR still required

- [ ] Replace the fixed two-column thresholds with region detection that supports one column, two columns, mixed-width regions, side notes and content spanning columns.
- [ ] Segment headings, paragraphs, lists, captions, tables, equations and visuals before OCR when confidence supports the classification.
- [ ] Run OCR per detected text region so diagrams and neighbouring columns do not contaminate text recognition.
- [ ] Evaluate a bounded set of Tesseract page-segmentation modes for uncertain regions and select a result using confidence, reading-order and text-quality evidence.
- [ ] Preserve alternate OCR candidates for Admin comparison when no result is clearly superior; do not silently combine conflicting text.
- [ ] Reconstruct paragraphs from lines without joining unrelated columns or splitting scientific expressions incorrectly.
- [ ] Connect caption candidates and scientific baseline notation to Future Steps 1 and 2 rather than implementing incompatible representations.

### Tables, diagrams and equations still required

- [ ] Detect table boundaries, rows, columns, merged cells and header cells separately from ordinary OCR lines.
- [ ] Store a structured table representation plus an accessible text form and the original table crop.
- [ ] Let the Admin correct table cells and structure instead of manually drawing a replacement table outside AKURU.
- [ ] Separate equation regions from surrounding explanatory paragraphs and retain original crops when notation recognition is uncertain.
- [ ] Avoid overlapping duplicate blocks such as a table crop, flattened table text and one large equation block containing the same table and following paragraphs.
- [ ] Preserve diagrams as visual assets and use the explicit caption relationships planned in Future Step 1.

### Controlled comparison and release gates

- [ ] Build a permitted reference corpus from representative AKURU inputs, including clean native PDFs, image-only scans, original HEIF photographs, two-column textbook pages, tables, diagrams, equations and scientific notation.
- [ ] Include the manually corrected v2.1 document as a reference transcription while recording that diagrams and tables were manually reconstructed.
- [ ] Compare the current production extractor, the local prototype and future candidates using ordered text coverage, precision, sequence similarity, reading-order accuracy, table structure, caption links, notation accuracy and review workload.
- [ ] Report results by page and content type; an improved average must not hide regressions in tables, equations or diagrams.
- [ ] Record runtime, peak memory and storage cost so the selected pipeline remains safe on the OCI worker.
- [ ] Version every extraction change and require explicit Admin-controlled reprocessing; never overwrite reviewed production extraction silently.
- [ ] Promote the implementation only after backend tests, document-quality evaluation, migration/reprocessing review and production rollback checks pass.

**Done when:** AKURU consistently converts representative scans and photographs into correctly ordered, structured and traceable content with materially less manual correction, while preserving original evidence and routing uncertain layout, tables, diagrams, equations and notation to focused Admin review.


## Low-priority model-routing extensions

### Assessment marking and feedback readiness

- [ ] Map assessment marking, marking-point decisions, improved answers and teaching feedback to independently configurable policies rather than inheriting the Tutor policy.
- [ ] Preserve the existing two-stage marking/feedback separation where configured and record the model policy used for each stage.
- [ ] Never use an economy policy for an assessment type until its subject-specific marking evaluation passes the existing automatic-release threshold.
- [ ] Keep formal assessment feedback hidden until submission and until the configured automatic or human-review release gate permits publication.
- [ ] Show descriptive Student, Parent and Admin errors when the required model or account is unavailable; never fall back to an unapproved model silently.
- [ ] Confirm frontend results distinguish awarded marks, small mistakes, conceptual mistakes, improved answers, pending review and unavailable feedback.
- [ ] Regression-test mark totals, M/A/B/C marking-point handling, evidence citations, handwritten-work attachments, review queues, release gates and model escalation.

### Document classification and interpretation readiness

- [ ] Split document work into explicit policy-backed operations such as preflight classification, structure proposal, OCR interpretation, table/equation interpretation, topic mapping and quality review.
- [ ] Keep deterministic extraction and confidence calculations available when AI is disabled or unavailable; do not make document upload dependent on an optional model.
- [ ] Route ordinary classification through the economical reviewed policy and difficult page interpretation through the stronger reviewed policy.
- [ ] Never let model escalation bypass Admin review for uncertain OCR, captions, tables, equations, superscript/subscript or image relationships.
- [ ] Display the actual processing stage, selected extraction version, review requirement and safe failure reason in the Admin document UI.
- [ ] Provide retry/reprocess controls that create versioned results and never overwrite reviewed or published evidence silently.
- [ ] Test native PDFs, image-only scans, photographs, multi-column pages, diagrams, tables, equations, duplicate primary sources and malicious document text under both primary and escalated policies.

### Realtime voice delegation readiness

- [ ] Keep the realtime audio model and voice quota independently configurable from text model policies.
- [ ] Define bounded server-side delegation from a voice session to `tutor_economy` or `tutor_standard` using the same authorized learner context and published sources as text tutoring.
- [ ] Prevent the realtime client from selecting arbitrary backend models, accounts, tools, subjects or student records.
- [ ] Include delegated text-model usage in the correct child's quota and link it to the voice session without double-counting voice duration.
- [ ] Preserve captions and parent-visible summaries under the existing transcript and retention rules while continuing not to store microphone audio.
- [ ] Keep voice and delegated Tutor help disabled throughout mocks and official assessments.
- [ ] Test interruption, reconnect, delegation timeout, quota exhaustion, account failover, model escalation and French voice tutoring.

## Low-priority completion gate

- [ ] Advanced extraction materially reduces review effort without regressing tables, equations, diagrams or reading order.
- [ ] Assessment policies meet subject-specific automatic-release thresholds before marks are released.
- [ ] Voice delegation uses the same authorized context as text tutoring and remains disabled during formal assessments.
- [ ] These services can be disabled independently without affecting high-priority text tutoring and flashcards.

**Done when:** Advanced OCR, document interpretation, assessment policy routing and realtime voice pass their own quality, cost, privacy and rollback gates without destabilizing the core Student learning experience.
