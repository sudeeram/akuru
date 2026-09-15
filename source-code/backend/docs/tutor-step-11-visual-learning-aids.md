# Tutor Step 11 — Visual learning aids

Tutor visuals are a bounded, read-only tool. The service offers them only when the learner explicitly asks for a diagram, image, graph, plot, equation, circuit, force or related visual. It returns at most four assets for the active covered unit.

## Evidence boundary

`official_source` visuals come from the current exact textbook search. They retain the citation, asset, document-version and publication provenance and use the existing session-scoped source endpoint. Source blocks must belong to the active subject and unit, be from a published textbook version, and have passed extraction review.

`explanatory` visuals come from `educational_media`. Deterministic SVGs are accepted only from the validated AKURU generator. Generated conceptual illustrations must be published and have a recorded review time. Their source chunk is re-authorized against the session's current published textbook edition. The response carries its citation, prompt digest and version, parameters, generator, model, provider response ID, review state and asset checksum. The full grounded prompt remains protected in the database and Admin API. These visuals are labelled as supporting explanations and cannot replace official evidence.

The Tutor Agent cannot request arbitrary generation or provide an asset URL. It receives the server-selected visual list after authorization. Formal assessments do not use the Tutor Agent, so tutor media cannot be introduced into an assessment question or marking decision.

## Access and accessibility

Tutor media content is served only to the student who owns the active session. The endpoint repeats subject, active-unit, publication and tutor-capability checks and returns private no-store and restrictive content headers. Every visual has required alt text and a readable text fallback. Equation blocks also provide a source-string fallback for the MathML renderer.

Tests cover visual-intent gating, official citation linkage and provenance, active-session source access, active-unit media authorization, review gates, SVG validation and escaping.
