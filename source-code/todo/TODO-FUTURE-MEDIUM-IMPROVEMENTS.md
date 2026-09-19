# Medium priority — Low-cost learning and document-review improvements

**Status: Future work — not started. Begin after the high-priority Student pilot is stable.**

This plan contains features that can be implemented independently of advanced OCR, voice and OpenClaw. It prioritizes deterministic processing and economical text interactions with limited additional model usage.

## Delivery sequence

1. Preserve and review Chemistry notation.
2. Link diagrams and tables to captions for better source understanding.
3. Build structured short revision-question activities.
4. Connect deterministic study-plan recommendations.
5. Complete shared Student accessibility, API-contract and error-state behaviour.

## Future Step 1 — Link images and diagrams with their captions

### Extraction pipeline

- [ ] Preserve candidate captions as independent text blocks; do not merge caption text into image pixels or discard either source.
- [ ] Detect likely captions using page geometry, reading order, distance from the visual, caption prefixes such as `Figure`, `Fig.`, `Diagram`, `Table` and subject-appropriate variants, and matching figure numbers.
- [ ] Associate each candidate caption with exactly one image, diagram, graph or table when the evidence is strong.
- [ ] Record the relationship explicitly in persisted extraction data, including visual block, caption block, relationship confidence, detection method and source bounding boxes.
- [ ] Leave ambiguous, missing and one-caption-to-multiple-visual cases unlinked and require Admin review rather than guessing.
- [ ] Preserve relationships when an Admin changes block order, block type, caption text or diagram crop.
- [ ] Carry approved image-caption relationships into retrieval chunks, exact citations, tutor visuals and accessible descriptions without duplicating caption text.

### Admin review experience

- [ ] Display a linked visual and caption together while retaining separate editable blocks.
- [ ] Clearly label the relationship, for example `Caption for Figure 1.2`.
- [ ] Let an Admin link, unlink or reassign a caption to a visual on the same source page.
- [ ] Show confidence and the original page position so the reviewer can verify the proposed link.
- [ ] Prevent a visual or caption from being marked fully reviewed while a required relationship remains ambiguous.
- [ ] Make the combined review usable by keyboard and screen reader, including meaningful image alternative text and relationship announcements.

### Verification and completion criteria

- [ ] Add representative native-text and scanned-PDF fixtures containing captions above and below visuals, multiple figures on one page, tables, multi-column layouts and captions continuing across lines.
- [ ] Measure caption detection and visual-link precision/recall separately; false links must fail closed into review.
- [ ] Test Admin linking, unlinking, reassignment, audit history, publication readiness, retrieval and citation rendering.
- [ ] Confirm existing reviewed documents remain valid or receive an explicit, auditable migration/re-review state.

**Done when:** AKURU can propose and persist evidence-based visual-caption relationships during extraction, an Admin can correct them safely on the review page, and only reviewed relationships are used by learning, retrieval and accessibility features.


## Future Step 2 — Preserve and review superscript and subscript notation

### Extraction pipeline

- [ ] Preserve native PDF character spans and their baseline, font size and vertical position so existing superscript and subscript formatting is retained.
- [ ] Detect probable superscript and subscript tokens in OCR using word/character bounding boxes, neighbouring baselines, relative character height and scientific context.
- [ ] Support common school-level forms such as `cm³`, `m²`, `10⁻³`, `H₂O`, `CO₂`, `H₂SO₄`, `Ca²⁺` and `SO₄²⁻`.
- [ ] Store a structured, lossless representation that separates display text from semantics, while retaining original extracted text, source coordinates and confidence.
- [ ] Generate LaTeX or MathML for equation/formula blocks where appropriate without replacing the human-readable reviewed text.
- [ ] Treat ambiguous charges, indices, powers and OCR-flattened forms such as `SO42-` as review-required; never infer a chemically different expression silently.
- [ ] Keep plain-text search aliases such as `H2O` where useful, while displaying and citing the reviewed scientific notation.

### Admin review experience

- [ ] Add keyboard-accessible **Subscript** and **Superscript** controls to the extracted-block editor.
- [ ] Allow formatting of a selected character range without requiring the reviewer to find and paste Unicode characters.
- [ ] Provide a clear preview using accessible HTML/MathML while preserving an editable source representation.
- [ ] Offer common scientific symbols and charge notation where this reduces manual entry, but require explicit Admin acceptance.
- [ ] Show the original page crop beside the edited notation and highlight low-confidence or automatically inferred characters.
- [ ] Validate malformed or ambiguous structured notation and retain the block in review until corrected.
- [ ] Ensure copying, searching, screen-reader output and downstream AI context retain the intended scientific meaning.

### Verification and completion criteria

- [ ] Add native-text and scanned fixtures covering powers, units, chemical formulae, ionic charges, isotopes, nested subscript/superscript and multi-character notation.
- [ ] Measure character accuracy and semantic-notation accuracy separately from ordinary OCR similarity.
- [ ] Test formatting controls with mouse, keyboard and screen reader, including selection, undo, save and reload.
- [ ] Test persistence, audit events, retrieval, citations, tutor output, assessment content and publication gates.
- [ ] Confirm unsafe or uncertain automatic corrections remain visibly review-required.

**Done when:** Native and OCR extraction preserve or safely propose scientific baseline notation, Admins can correct it without specialist input syntax, and reviewed superscripts/subscripts retain their meaning through retrieval, display, citation and assessment workflows.


## Medium-priority learning extensions

### Short revision questions — frontend and backend readiness

- [ ] Define a structured revision activity separate from free-form Tutor chat, with activity, question, response, result and completion records.
- [ ] Support a bounded set of question forms such as recall, short answer and multiple choice without silently converting them into formal examination results.
- [ ] Generate or select questions only from the student's eligible covered topics and approved published evidence.
- [ ] Route straightforward generation and feedback through `tutor_economy`, while routing complex calculations, misconceptions and failed validation through `tutor_standard`.
- [ ] Preserve the question, expected answer or marking criteria, exact source evidence, prompt/model version and routing decision in an immutable activity snapshot.
- [ ] Add Student APIs to start/resume an activity, fetch one question at a time, save/submit an answer, request permitted help and complete the activity idempotently.
- [ ] Build an accessible Student workflow with topic and length selection, `Question n of total`, answer controls, feedback, source links, next-question navigation and completion summary.
- [ ] Make clear whether feedback is a recall check, Tutor guidance or authoritative assessment; reuse the assessment service whenever marks or marking points are awarded.
- [ ] Record completion and weak-topic evidence for recommendations without allowing unverified AI observations to alter mastery automatically.
- [ ] Add retry and spaced-review recommendations using deterministic scheduling rather than model-generated dates.
- [ ] Retain conversational `questions` and `revision` Tutor modes, while directing students to the structured activity when they request a scored or multi-question revision session.
- [ ] Add backend generation, selection, evidence, authorization, idempotency, quota and escalation tests plus frontend contract, accessibility and browser-flow tests.

### Study planner and recommendation readiness

- [ ] Keep mastery calculation, next-topic priority and study-plan scheduling deterministic; use the model only for bounded, grounded wording or explanations.
- [ ] Add an explicit `study_plan` model policy and define which outputs may use the economy model and which evidence failures require escalation.
- [ ] Preserve topic, grade, cumulative term coverage, due dates, mastery evidence and recommendation factors in the response shown to the Student and Parent.
- [ ] Ensure Tutor-proposed signals remain non-authoritative and cannot automatically alter the study plan.
- [ ] Add Student and Parent states for available plan, insufficient evidence, exhausted quota, provider unavailable and recommendation awaiting review.
- [ ] Test that model-policy changes cannot reorder deterministic priorities, cross subjects, expose another child or include uncovered topics.

### Shared frontend behaviour and API contracts

- [ ] Display consistent loading, retry, quota-exhausted, provider-unavailable, evidence-insufficient and review-pending states across all Student AI activities.
- [ ] Preserve typed generated frontend API contracts for policy-backed responses and fail CI when backend schemas change without regeneration.
- [ ] Ensure Enter-key behaviour, focus restoration, screen-reader announcements and keyboard navigation work for Tutor chat, flashcards, revision questions and Guided Practice.
- [ ] Prevent duplicate actions during loading and use idempotency keys for every state-changing Student request.
- [ ] Keep provider names, credential aliases, internal confidence and raw routing reasons out of ordinary Student and Parent views.
- [ ] Provide Admin-visible diagnostic references that identify a logical operation without exposing prompts, source text outside authorization or credentials.
- [ ] Add navigation and dashboard entry points only after the corresponding feature passes its release gate; do not show non-functional controls to students.
- [ ] Run responsive browser tests for tablet and desktop layouts used by children, including long Chemistry notation, diagrams, citations and error messages.

## Medium-priority completion gate

- [ ] Caption and notation improvements preserve reviewed evidence without forcing unrelated OCR redevelopment.
- [ ] Students can complete structured short revision sessions using eligible published topics.
- [ ] Study-plan ordering remains deterministic and cannot be changed by unverified Tutor observations.
- [ ] The new workflows use economical model policies where evaluation permits and can ship without low-priority work.
- [ ] Responsive, keyboard and screen-reader checks pass across the Student learning workflows.

**Done when:** AKURU adds low-cost revision and study-plan experiences plus focused review improvements without depending on advanced OCR, realtime voice or OpenClaw.
