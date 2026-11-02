# Improve Tutor retrieval and add related curriculum explanations

Created: 2026-11-01
Started: 2026-11-02
Completed: 2026-11-02
Status: completed — existing single-Student production pilot verified.
Priority: high — improve the current single-student teaching pilot.

## Objective

Students should receive useful explanations of closely related curriculum concepts even when the current textbook search returns insufficient evidence. “What is evaporation?” must not be refused merely because retrieval fails. First distinguish a retrieval failure from genuinely missing textbook content; do not assume this concept is absent from Topic 1.

Support three explicit outcomes: textbook-grounded teaching with real citations; clearly labelled **Additional explanation** based on model knowledge within the approved learning scope; and clarification or a helpful boundary for unrelated, unsafe or uncertain requests. Additional explanation is not independently verified textbook or Pearson evidence. Use the existing OpenAI provider/account router, without automatic web browsing or an additional AI service.

## Step 0 — Reproduce the gap and define the teaching boundary

- [x] Reproduce short definitions and follow-ups against the currently published Topic 1 version, including evaporation, boiling point, melting point and their differences.
- [x] Inspect the actual published passages and retrieval scores; record whether each failure is missing content, wording mismatch, chunking, or a ranking threshold issue.
- [x] Define allowed prerequisite/related-concept teaching for the selected subject, course and grade. Current topic remains the anchor; related explanations do not grant access to unpublished documents, other subjects or uncovered assessments.
- [x] Define ambiguous and outside-scope behaviour: clarify or briefly redirect, rather than silently teaching an unrestricted topic. Do not claim exact Pearson syllabus alignment without authorized specification evidence.
- [x] Record baseline cases and expected outcomes before changing prompts or retrieval. Preserve existing pilot restrictions and release evidence.

## Step 1 — Improve short-question and follow-up retrieval

- [x] Normalize short definition questions and scientific notation, and add bounded, curated concept aliases/related search terms where useful (for example evaporation, liquid surface and escaping particles). Avoid broad keyword expansion that returns unrelated passages.
- [x] Handle a single meaningful concept term without requiring two overlapping keywords; use an exact/curated concept match and scoped relevance checks rather than lowering the global threshold indiscriminately.
- [x] Use a bounded amount of the same student's current-session conversation to resolve follow-ups and pronouns. An explicit new question must override stale context.
- [x] Deduplicate results and retain published-version, source-role, topic, review and private-asset authorization constraints. Exercise prompts alone remain insufficient factual evidence.
- [x] Bound search attempts and context size. Prefer deterministic query expansion first; avoid a paid model call solely to rewrite every query.

## Step 2 — Implement explicit supplementary teaching

- [x] Replace the blanket missing-citation refusal in the text Tutor with a controlled decision: grounded, supplementary, mixed, clarification needed, or outside scope.
- [x] Extend the structured output contract to identify the answer basis and distinguish supported claims from supplementary explanation. A mixed answer must not imply that its textbook citation supports every additional claim.
- [x] Allow scientifically established, grade-appropriate definitions, explanations and clearly identified illustrative examples for related concepts. Label model-created examples as examples, not textbook exercises or official exam questions.
- [x] Never invent pages, figures, quotations, specification references, marking points or examiner advice. Exact textbook/official-exam claims still require the corresponding authorized evidence.
- [x] Keep retrieved material and student messages as untrusted data. Preserve privacy isolation, verified learner-history rules and the existing safety controls; no invented mastery or past mistakes.
- [x] Use uncertainty and clarification appropriately; do not present a model's self-reported confidence as measured scientific accuracy. Document handling of textbook contradictions without silently modifying published sources.
- [x] Keep this path in text teaching. Do not relax marking, mock/official-paper generation, assessment feedback, formal-assessment assistance restrictions, or automatic mastery/study-plan updates.
- [x] Continue using account routing, model pinning, token accounting, quotas, request idempotency and audited invocation records. Supplementary text must not bypass any pilot or release gate.

## Step 3 — Complete the Student experience and retained records

- [x] Render a clear **Additional explanation** label and concise explanation that this material extends beyond the retrieved textbook evidence. Distinguish textbook-supported and supplementary sections in mixed replies.
- [x] Show citations only for actual authorized evidence. Offer available textbook sources without fabricated page links, unrelated diagrams or a misleading empty textbook-evidence panel.
- [x] Replace generic “ask Admin to review extraction” messages with an accurate, useful explanation of missing evidence, ambiguity or scope limits. Do not suggest an extraction fault unless established.
- [x] Preserve answer-basis labels and provenance when reopening transcripts and in relevant Parent/Admin support views. Old transcripts without the new fields must remain readable and must not be relabelled as verified.
- [x] Keep automatic scrolling to new answers and mobile/readability/accessibility behaviour working for grounded, supplementary and mixed responses.

## Step 4 — Provenance, contracts and persistence

- [x] Record retrieval outcome, query strategy, answer basis, model, prompt version, available/used citation references and active topic content version, without storing credentials or logging private prompts unnecessarily.
- [x] Review existing JSON turn/invocation records before proposing schema changes. Prefer additive structured metadata when sufficient; add a reviewed migration only if a new persistent column/index is actually needed.
- [x] Update backend schemas, generated OpenAPI/TypeScript contracts and frontend domain types together. Support existing saved replies with optional/defaulted fields.
- [x] Bump the Tutor prompt version and update the relevant evaluation/pilot evidence. Do not silently change the pinned production prompt or fabricate a passing general-release evaluation.

## Step 5 — Test and evaluate the teaching quality

- [x] Add deterministic retrieval regressions for single-term questions, aliases, follow-ups, explicit topic changes, off-topic keyword collisions, exercise-only evidence and publication/source authorization.
- [x] Test grounded, supplementary, mixed, uncertain and outside-scope outputs, including rejected invented citation IDs and unsupported claims of official examiner guidance.
- [x] Test Student/Parent/Admin ownership, cross-student isolation, pilot audience/topic/model/content-version/expiry restrictions, CSRF and formal-assessment blocking. Verify assessment workflows retain their existing stricter rules.
- [x] Test transcript compatibility, labels, actual citation links, new-answer scrolling and mobile layout in the browser. The missing-evidence path must not strand the Student on an error page.
- [x] Run a small predeclared live evaluation: evaporation; evaporation versus boiling; factors affecting evaporation; heating versus a change of state; a related prerequisite; a mixed-evidence explanation; an ambiguous term; an unrelated advanced topic; and prompt injection/personal-history requests.
- [x] Use a separately agreed spend ceiling and the Evaluation key for development evaluation, preserving its existing cumulative budget ledger. Do not assume a fresh US$2 allowance or charge AKURU-backend for development evaluations without authorization.
- [x] Review scientific correctness, scope, appropriate labels, source honesty and token cost. Do not equate model confidence or one successful answer with measured accuracy.
- [x] Run the relevant frontend/backend regressions, typecheck, lint, contract checks and production build.

## Step 6 — Controlled release and operator documentation

- [x] Document the new answer types, their limitations, operator controls and the reason teaching differs from assessment evidence requirements.
- [x] Prepare a rollback/kill switch that can disable supplementary teaching without removing textbook-grounded tutoring. Keep the initial deployment limited to the authorized pilot audience and subject/topic scope.
- [x] Obtain deployment authorization, commit/push the reviewed changes, take the normal production backup, deploy and update the applicable pilot/release configuration and evidence.
- [x] Verify the Student flow on production: a useful evaporation answer, a related follow-up, honest labels/citations, safe scope boundaries and recorded usage. Use normal authorized sign-in; do not synthesize additional Student credentials.
- [x] Confirm health/security checks, retain acceptance evidence and mark this plan complete only after the full permitted release scope is verified. Record remaining limitations explicitly.

## Acceptance criteria

- A short question about evaporation produces an appropriate explanation instead of a generic retrieval refusal.
- Textbook support is used when available; supplementary material is visibly distinguished and cannot masquerade as official evidence.
- The Tutor can explain related concepts without granting new content access or expanding the pilot audience.
- Uncertain, unrelated or unsafe requests receive an appropriate boundary; the absence of a citation is not itself treated as proof that a concept cannot be taught.
- Existing account isolation, assessment restrictions, source authorization, costs/quotas, provenance and release controls remain effective.

## Implementation references

- `source-code/backend/app/services/tutor_sources.py` — query handling, published-source search and citations.
- `source-code/backend/app/services/tutor_agent.py` — evidence gate, structured teaching and turn persistence.
- `source-code/backend/app/ai/prompts.py` and `app/schemas/tutor_agent.py` — prompt and answer contract.
- `source-code/backend/app/services/assessment_access.py` — formal-assessment, release and pilot restrictions.
- `source-code/frontend/features/tutor-sessions.tsx` — Student conversation, evidence and automatic scrolling.
- `source-code/backend/docs/tutor-controlled-text-pilot.md` and `source-code/todo/ongoing/TODO-SCREENSHOT-TEXTBOOK-PACKAGES.md` — current pilot controls and evidence.

## Verification record — 2026-11-02

Production baseline: 54 active Topic 1 version-2 chunks; evaporation is explained on PDF page 6. The short query failed the former two-term lexical requirement. The published source was not replaced.

Local results: 308 backend tests passed, one existing skip; 116 frontend tests passed; typecheck/lint/build and generated contracts checked. The zero-cost nine-case pipeline run and the separately authorized live Evaluation run passed. Six paid calls estimated US$0.057192 with US$0.081501 conservatively charged against the new US$0.75 phase ledger; the original cumulative ledger remains unchanged. The evaluated fixture is the prepared screenshot candidate, and normal production v2.2 acceptance subsequently passed. Desktop/mobile synthetic UI checks confirmed readable labels, folded references and automatic scrolling.

Evaluation evidence: `source-code/backend/evaluations/tutor/supplementary-teaching-20261102.json`. No migration. Supplementary aliases are initially validated for Chemistry States of Matter; this is not unrestricted all-subject supplementary release.

Production release `fe526cf8f272fb3bc2815182ecf3141af8bd1499` deployed via the encrypted-backup playbook on 2026-11-02. The existing roshinika-only Topic 1 pilot now permits supplementary prompt 2.0.0, with the original subject/topic/content/model/expiry unchanged. Original grounded prompt 1.0.2 remains the rollback. Evaluation SHA256: `3785c9a21792634724af0d8e0b597e0cd549689022cbedaa6ef9c6e417675801`. Activation evidence: `/data/akuru/release-evidence/tutor-supplementary-20261102T070907Z-activation.json`. HTTPS/header/authentication/route/service/timer/loopback acceptance passed; read-only gates allow roshinika and deny laura. Existing npm dependency advisories remain tracked in `todo/planned/TODO-NPM-DEPENDENCY-SECURITY.md`; no dependency upgrades were made.

Read-only published-source comparison with local embeddings: evaporation query 0→9 ranked matches; boiling point 6→11; melting point 6→7; evaporation-versus-boiling 5→14. These are ranking counts, not accuracy percentages; the ordinary source limit still bounds the passages supplied. The current production v2.2 sources remain unchanged.

The user signed in normally as roshinika. Production checks passed: evaporation answered from published evidence; source image opened printed page 5/PDF page 6; wet-clothes and pronoun-follow-up replies separated textbook support from additional explanation; an advanced-topic request was redirected without a provider call; answer labels survived reload. Three production AKURU-backend calls recorded 13,447 total tokens (5,494 + 3,926 + 4,027), separately from the Evaluation budget. No assessment marks or mastery were awarded. Acceptance evidence: `/data/akuru/release-evidence/tutor-supplementary-20261102-acceptance.json`. Screenshot: ignored local `tmp/tutor-supplementary-production.png`.
