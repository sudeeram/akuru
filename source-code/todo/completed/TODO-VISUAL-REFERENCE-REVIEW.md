# Visual Reference upload and role-aware review

## Objective

Make the Topic source role an explicit upload decision and give Visual Reference
documents a review workflow that matches how AKURU uses them. OCR text from a
Visual Reference must remain excluded from retrieval, tutoring, flashcards and
assessment generation. Its unresolved OCR text must not block Topic publication.
Printed-page provenance and every visual selected for Student use must remain
accurate, accessible, audited and publication-gated.

At the same time, give Primary, Supporting and Reference text sources a bounded
scientific-text editor that preserves and corrects superscript, subscript and
common school-level scientific notation. This is one coordinated delivery plan:
the source role decides whether the Admin receives the simplified visual workflow
or the complete scientific-text review workflow.

This roadmap applies to Topic document sources with these roles:

- **Primary text** — canonical reviewed text used to build retrieval content.
- **Supporting text** — additional reviewed learning text retained in the Topic
  publication manifest.
- **Reference text** — reviewed supplementary text retained in the Topic source
  set.
- **Visual reference** — original page images and approved visuals; OCR text is
  excluded from retrieval.

Changing a role affects only the next Topic publication. Existing published
versions, citations, Student evidence and audit history remain immutable.

## Step 0 — Record role-specific rules and current-data compatibility

- [x] Add the source-role and review matrix to the overall, frontend and backend
  architecture documentation.
- [x] Inventory every readiness, quality, review, publication, retrieval and
  visual-selection check that currently reads document or extraction status.
- [x] Confirm that existing `TextbookTopicDocument.role` records remain valid and
  require no destructive data conversion.
- [x] Decide whether role-specific review evidence can use existing page metadata
  and audit events or requires one reviewed migration with explicit fields.
- [x] Define how existing Visual Reference documents receive their initial
  printed-page review state without marking OCR blocks as reviewed.

**Acceptance:** one documented matrix defines the requirements for all four roles
and existing published Topic versions remain unchanged.

## Step 1 — Require the source role before Topic upload

- [x] Add a required, accessible **Source role** control to every Topic upload
  panel before the file picker.
- [x] Provide concise descriptions of retrieval inclusion and review effort for
  each role.
- [x] Remove the frontend's silent `primary` default; require a deliberate Admin
  selection for each upload operation.
- [x] Apply the selected role to all files in a multi-file upload and show it in
  the destination summary, progress state and completion state.
- [x] Preserve backend role validation, Topic ownership, subject boundaries,
  filename-conflict confirmation, idempotency and upload-size limits.
- [x] Keep the role editable after upload with an explicit impact confirmation.

**Acceptance:** an Admin cannot upload a Topic source without seeing and choosing
how AKURU will use and review it.

## Step 2 — Separate Visual Reference evidence from OCR review state

- [x] Introduce an explicit role-aware review calculation instead of treating
  `DocumentPage.needs_review` as the readiness result for every source role.
- [x] Track an audited printed-page-label review independently from unresolved OCR
  blocks.
- [x] Define **Fully reviewed** to require a non-empty, confirmed Printed page
  label as well as completion of every review requirement applicable to that
  source role; an empty label must display **Partially reviewed** or **Needs page
  label** instead.
- [x] Derive a Visual Reference state such as **Not reviewed**, **Partially
  reviewed**, **Ready for visuals** or **Ready** without rewriting OCR evidence.
- [x] Preserve the original extraction, confidence, blocks, assets and processing
  events for provenance and possible future reclassification.
- [x] Recalculate readiness immediately when a source changes between a text role
  and Visual Reference.
- [x] Ensure changing Visual Reference to a text role correctly introduces the
  full page, block, formula, table and extraction review requirements.

**Acceptance:** unresolved OCR text in a Visual Reference is visible as extraction
evidence but is not misrepresented as required review work.

## Step 3 — Build the simplified Visual Reference review page

- [x] Display a prominent **Visual reference — OCR excluded from retrieval** badge
  and explanatory text.
- [x] Show each source page with PDF page number, page preview and editable
  **Printed page label**.
- [x] Collapse pages initially and provide progress totals plus direct links to
  pages whose printed label remains unconfirmed.
- [x] Show **Fully reviewed** only after the Printed page label is saved and every
  other role-specific requirement for that page is complete; update the badge and
  progress totals immediately when the label is added, changed or cleared.
- [x] Hide text-block correction, reading-order, formula and OCR-confidence tasks
  from the required Visual Reference workflow.
- [x] Retain an optional read-only extraction view for diagnosis without making it
  a publication requirement.
- [x] Present detected diagrams, images and tables with crop preview, caption,
  accessible alternative text and selection status.
- [x] Allow irrelevant visuals to remain unselected without creating review work.
- [x] Require every selected visual to have a correct crop, reviewed caption,
  accessible alternative text and Admin approval.
- [x] Keep private document and asset access, keyboard operation, responsive
  layout, status text and colour-independent cues.

**Acceptance:** an Admin can finish a Visual Reference without opening or saving
irrelevant OCR blocks.

## Step 4 — Preserve scientific notation during extraction

- [x] Preserve native PDF character spans with baseline, font size, vertical
  position, source coordinates and confidence so existing superscript and
  subscript formatting is retained.
- [x] Detect probable superscript and subscript tokens in scanned OCR using
  character geometry, neighbouring baselines, relative height and bounded
  scientific context.
- [x] Support common forms including `cm³`, `m²`, `10⁻³`, `H₂O`, `CO₂`,
  `H₂SO₄`, `Ca²⁺`, `SO₄²⁻`, isotopes and reaction arrows.
- [x] Treat ambiguous flattened forms such as `SO42-`, charges, coefficients,
  years and page numbers as review-required instead of silently changing their
  scientific meaning.
- [x] Persist the original extraction, structured reviewed content, display text,
  plain search alias, source geometry and confidence without losing evidence.
- [x] Generate bounded LaTeX or MathML for equation/formula blocks where useful
  without replacing the reviewed human-readable text.
- [x] Generate normalized search and AI-context aliases such as `H2O` for `H₂O`
  and `cm3` for `cm³`, so formatted notation remains discoverable.
- [x] Keep these notation rules out of the required Visual Reference OCR workflow;
  apply them when its role later changes to a text role.

**Acceptance:** native notation is preserved, OCR only proposes defensible
formatting, and ambiguous scientific meaning fails closed into Admin review.

## Step 5 — Build a safe scientific-text review editor

- [x] Replace the plain extracted-text control for text-role blocks with a
  restricted scientific editor rather than an unrestricted HTML WYSIWYG editor.
- [x] Support only approved inline marks and symbols: subscript, superscript,
  bold, italic, Greek characters, degree, plus/minus, reaction arrows and other
  explicitly reviewed school-level symbols.
- [x] Allow an Admin to select `2` in `H2O` and apply **Subscript**, or select `3`
  in `cm3` and apply **Superscript**, without pasting special Unicode characters.
- [x] Provide keyboard-accessible Subscript, Superscript, Clear formatting, Undo
  and Redo controls, including documented shortcuts that do not conflict with
  browser or screen-reader commands.
- [x] Provide an accessible Student-display preview beside the original page crop
  and visibly highlight low-confidence or automatically proposed notation.
- [x] Keep the current LaTeX field and rendered equation preview for complex
  equations; define predictable conversion between inline notation and formula
  blocks without lossy round trips.
- [x] Use one reusable scientific editor for paragraphs, headings, table cells,
  figure captions and answers where those content types support inline notation.
- [x] Sanitize and validate the structured document on both frontend and backend;
  reject arbitrary HTML, scripts, event handlers, unsafe links and unsupported
  marks.
- [x] Validate malformed, overlapping or semantically ambiguous marks and keep the
  block review-required until corrected.
- [x] Make selection, formatting, preview, copying, saving and reloading work with
  mouse, keyboard, touch and screen readers.

**Acceptance:** Admins can correct `H₂O`, `SO₄²⁻`, `cm³` and related notation
visually and safely without writing markup or specialist input syntax.

## Step 6 — Define canonical storage and downstream rendering

- [x] Choose and document a versioned restricted rich-text schema, for example a
  paragraph with text runs carrying `subscript` or `superscript` marks.
- [x] Store structured reviewed content alongside the original OCR text and
  existing block evidence; do not store arbitrary editor-generated HTML as the
  source of truth.
- [x] Produce safe React/HTML and accessible MathML for display, normalized plain
  text for search and embeddings, and LaTeX only where mathematically appropriate.
- [x] Ensure copy/paste provides useful scientific Unicode and a normalized plain
  fallback.
- [x] Include structured scientific content in reviewed-content hashes, immutable
  Topic manifests and audit events so formatting-only corrections create
  traceable new evidence.
- [x] Update retrieval chunks, exact citations, Tutor context, flashcards,
  assessments, exports and source previews to retain the reviewed meaning.
- [x] Version the renderer and normalizer so future changes cannot silently alter
  already published content.
- [x] Define a safe compatibility path for existing plain-text and LaTeX blocks;
  do not require destructive conversion of published records.

**Acceptance:** one reviewed edit produces consistent display, search, AI context,
citation and publication evidence without unsafe HTML or semantic loss.

## Step 7 — Make readiness and publication gates role-aware

- [x] Keep full extraction and quality gates for Primary, Supporting and Reference
  text sources.
- [x] Exclude Visual Reference pages and blocks from OCR confidence, formula,
  reading-order, retrieval-precision and unresolved-block blockers.
- [x] Require processing success and confirmed printed-page labels for the Visual
  Reference pages used by AKURU.
- [x] Apply the non-empty Printed page label rule consistently to page status,
  document progress, Topic readiness, quality reports and publication checks so
  the frontend cannot claim completion that the backend would reject.
- [x] Require every selected visual to be approved with caption, alternative text,
  page provenance and a valid crop.
- [x] Decide and document whether all Visual Reference pages require confirmed
  printed labels or only pages retained in the published visual manifest; default
  to all pages for reliable textbook navigation.
- [x] Prevent an approved visual with a missing printed-page label from entering a
  new Topic publication.
- [x] Keep unselected visuals outside the manifest and outside readiness counts.
- [x] Preserve immutable published source manifests, checksums and citations when
  source roles or reviews later change.

**Acceptance:** irrelevant Visual Reference OCR can never block publication, while
missing page provenance or incomplete selected visuals always block it.

## Step 8 — Improve Admin status and quality reports

- [x] Show role-specific review status in View Textbooks, Review Textbooks and the
  Topic source manager.
- [x] For a Visual Reference, report page-label totals, selected visuals, approved
  visuals and remaining required work.
- [x] Replace misleading OCR failure text with **OCR text excluded from retrieval**.
- [x] Separate text-source quality results from Visual Reference readiness in the
  Topic PDF quality report.
- [x] Link every blocking result to the exact page or visual that needs attention.
- [x] Refresh Topic readiness and quality immediately after page-label, visual or
  role changes.

**Acceptance:** the Admin can understand and resolve every blocker without being
directed to irrelevant OCR corrections.

## Step 9 — Audit, authorization and regression protection

- [x] Record role selection, role changes, printed-label confirmation, visual
  selection, visual approval and publication in the audit log without storing
  secret or unnecessary Student data.
- [x] Keep all upload, review, role-change and publication operations Admin-only
  with CSRF and authenticated API protection.
- [x] Test that Parent and Student accounts cannot read private source files or use
  Admin review endpoints.
- [x] Test that Visual Reference OCR blocks never enter retrieval chunks, Tutor
  citations, flashcard evidence or assessment generation.
- [x] Test that changing to a text role restores all full-review blockers.
- [x] Test missing and duplicate printed labels, multi-page labels, selected and
  unselected visuals, incorrect crops, role changes and immutable prior versions.
- [x] Add a regression test proving a page with completed block review but an empty
  Printed page label is not **Fully reviewed**, and becomes fully reviewed only
  after a valid label is saved.
- [x] Test existing Visual Reference records through any migration or derived-state
  transition.
- [x] Add native-text and scanned fixtures for powers, units, chemical formulae,
  ionic charges, isotopes, nested notation, multi-character notation, ambiguous
  flattened OCR and scientific content inside tables and captions.
- [x] Measure ordinary character accuracy separately from semantic-notation
  accuracy and confirm uncertain automatic corrections remain review-required.
- [x] Test editor selection, formatting, shortcuts, undo/redo, sanitization,
  malformed data, save/reload, copy/paste and accessible announcements.
- [x] Test structured notation through retrieval, citations, Tutor answers,
  flashcards, assessment content, immutable manifests and audit history.
- [x] Update Admin and developer documentation.
- [x] Run API contract checks, frontend/backend tests, type checking, linting,
  production build and migration drift checks.
- [x] Deploy the exact reviewed commit and run production acceptance without
  changing currently published Chemistry learning content.

**Done when:** source role is an explicit upload decision, Visual References have
a short and accurate review process, text roles provide safe visual correction of
scientific notation, and reviewed meaning remains grounded, searchable,
accessible, traceable and publication-safe throughout AKURU.


## Completion evidence

Completed on 2026-09-27. The source role is required at upload, Visual Reference readiness uses printed-page and approved-visual evidence without OCR blockers, text roles use validated structured scientific content, and publication hashes include reviewed notation. `npm run verify` passed 54 frontend and 130 backend tests plus contract, type, lint and production-build checks. `alembic check` reported no schema drift.
