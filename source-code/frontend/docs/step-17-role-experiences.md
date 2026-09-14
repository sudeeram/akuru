# Step 17 — Role-specific experiences

## Student

My progress displays marks, marking-point evidence, strengths, mistakes, the improved answer and explanation. Each unit includes dimension scores, confidence and trend, observed mistakes and approved recommendations. Scores are evidence-based indicators, not predicted qualification grades. The history disclosure intentionally shows the latest ten changes per unit; dates and individual scores remain visible.

## Parent

Assessment reviews contains a separate summary for every linked child and a student filter. Open an answer to inspect typed or uploaded working and the official marking decisions. Change point-level marks, evidence, explanations, improved answer and mistake lists; enter a reason and publish. The previous result is retained. A stale result must be refreshed before it can be reviewed. Recommendation approval is a separate queue. The backend enforces family scope even if a caller changes an identifier.

## Admin

Assessment audit lists result versions, provider/model, confidence, prompt and engine versions, source manifests and deterministic checks. Open a result to inspect submitted working and publish a human review, or reassess the entire submitted assessment. Reassessment uses OpenAI and creates new versions. Failed requests retain their idempotency key for retry within the mounted view. Reopen or refresh the audit after an uncertain request before starting a different operation.

## Accessibility and failure handling

`ResultReview` is shared by Parent and Admin. Fields are labelled, errors appear beside the form, and retrying an unchanged form uses the same request key. Audit loading is distinct from empty results, with an explicit retry action.

`LearningImage` uses the shared accessible dialog for enlarged uploaded diagrams, Escape dismissal and focus containment. It shows the question context as a caption and alternative text; this is contextual identification, not an invented visual transcription. The original asset can also be opened at its native size. Image failures have a retry control. The built-in SVG diagrams use the same dialog and provide text descriptions.

`Equation` renders common textbook notation using native MathML: fractions, square roots, powers, subscripts, text and common symbols. Unsupported notation is preserved visibly as source with an explanation; it is never silently discarded. This is a deliberately bounded renderer, not a full LaTeX engine. Original equation source remains available below the rendering.

## Local verification

Run `npm run verify` from `source-code` for contracts, backend integration tests, frontend checks and production build. Run `node frontend/tests/step17-browser.mjs` with a local frontend on port 5180 and an existing Playwright installation. Set `PLAYWRIGHT_MODULE` to its module path if it is not installed in this project; `AKURU_URL` overrides the frontend URL. The browser test uses isolated API fixtures and never writes real accounts or calls OpenAI. It checks Student feedback, Parent review failure/retry, Admin audit retry, MathML and diagram keyboard dismissal.
