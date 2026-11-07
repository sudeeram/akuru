# Tutor text personalisation: instructions, response rules and evaluation

Status: In progress.
Created: 7 November 2026.
Started: 7 November 2026.
Completed: Not completed.

## Objective

Make the saved tutor properties visibly and consistently influence both Subject
chat and Topic chat, without changing factual accuracy, source honesty, access,
assessment restrictions or student performance records. Separate properties that
can be checked mechanically from subjective style preferences that require
behavioural evaluation. Do not promise perfect enforcement of tone.

## Current implementation and scope

The text agent sends tone, friendliness, enthusiasm, speed, communication
character, explanation depth and teaching style in `tutorProfile`, but has no
explicit property-to-behaviour policy. Voice already has explicit tone,
friendliness and enthusiasm instructions and a speed mapping. Preserve voice
behaviour while improving text tutoring.

Existing stored values are:

| Property | Values | Text-chat treatment |
| --- | --- | --- |
| Tone | calm, encouraging, direct, playful | Explicit wording and presentation guidance |
| Friendliness | low, medium, high | Degree of warmth and conversational framing |
| Enthusiasm | low, medium, high | Energy, emphasis and restrained expressive punctuation |
| Explanation depth | concise, standard, detailed | Relative detail, examples and response structure |
| Teaching style | guided, socratic, example_led, exam_focused | Method of teaching, subordinate to the requested activity |
| Communication character | childlike, balanced, authoritative | Age-appropriate presentation; clearer display labels |
| Speed | low, medium, high | Voice only; no artificial delay or text-generation-speed claim |
| Voice / presentation / avatar | Existing curated choices | Do not infer knowledge, personality or teaching quality from gender or appearance |

## Step 0 - Define and document the behaviour policy

- [x] Inspect the current text, supplementary-teaching, past-paper, guided-practice
  and voice paths; record which replies call a model and which are deterministic.
- [x] Create one versioned backend policy mapping each allowlisted property/value
  to bounded instructions. Avoid concatenating arbitrary profile names or other
  student-entered text into trusted instructions.
- [x] Define calm as measured and reassuring; encouraging as specific constructive
  support; direct as answer-first with little framing; playful as occasional
  relevant analogies without baby talk or distracting jokes.
- [x] Define low friendliness as polite and professional, medium as approachable,
  and high as warmer and supportive. No setting permits hostility, shame,
  manipulative attachment, excessive praise or claims of human relationships.
- [x] Define enthusiasm levels without suggesting greater scientific confidence.
  Default to no emojis; agree and document any tightly limited exception for
  playful/high-enthusiasm responses. Never alter formulas or scientific notation.
- [x] Define depth as content budgets and structure preferences, not arbitrary
  answer truncation. Necessary safety statements, source references, equations,
  accessibility text and essential reasoning take precedence over brevity.
- [x] Define teaching styles using existing values: guided = staged steps;
  socratic = a focused reasoning question; example_led = relevant illustrative
  examples; exam_focused = command words and available approved marking evidence.
  A style cannot authorise marks, invent examiner requirements or reveal a
  restricted answer.

## Step 1 - Define conflict and precedence rules

- [x] Document and implement this ordering: safety/access/source/assessment rules;
  the student's explicit permitted request and selected activity; teaching style
  and explanation depth; tone, friendliness and enthusiasm.
- [x] Preserve the student's requested question count and task where supported;
  use the profile's normal question limit only as a default. Do not let Socratic
  style obstruct a clear permitted request for an explanation.
- [x] Keep factual meaning and available citation references invariant across
  personalities. Style must not turn uncertainty into certainty.
- [x] Define how the selected Teaching approach temporarily overrides the saved
  teaching style without editing the profile.
- [x] Clarify overlapping properties: playful tone controls wording; playful
  communication character controls presentation. Do not multiply their effects.

## Step 2 - Integrate with text generation and provenance

- [x] Build a shared trusted instruction compiler from validated stored values;
  use conservative documented defaults for legacy/missing fields.
- [x] Apply it to textbook-supported and supplementary teaching in both session
  scopes. Retain conversation-context resolution and ambiguity handling.
- [x] Inventory past-paper chat and guided-practice replies. Apply style only to
  eligible generated explanations. Preserve official question wording, exact
  marking guidance, deterministic tool messages and safety notices.
- [x] Remove speed from text-personality instructions; preserve it in saved
  profiles and voice controls. Do not implement artificial typing delays.
- [x] Continue using the profile version attached to the session. Tutor switches
  should apply the selected version while retaining the conversation. Document
  when an edited profile takes effect; do not silently change historical turns.
- [x] Version changed prompts and the personalisation policy. Record the policy
  version and relevant profile-version identity in invocation/turn provenance
  without copying secrets or unnecessary personal data into logs.
- [x] Preserve account routing, request idempotency, quota accounting, source
  authorisation and student/family isolation.

## Step 3 - Add proportionate response validation

- [x] Define configurable default budgets for explanation sections, paragraph
  sizes, follow-up questions and optional expressive punctuation. Use separate
  rules for task types rather than one universal character limit.
- [x] Check measurable constraints after existing output-schema and source checks.
  Report subjective tone matching as an evaluation result, not a hard guarantee.
- [x] Keep citations, uncertainty labels, scientific notation and official
  evidence intact. Never silently clip an explanation or rewrite a marking scheme
  to meet a style target.
- [x] Decide which violations are safe to normalise, which are logged as style
  deviations, and which make a response unusable. Minor personality deviations
  should not prevent an otherwise correct educational answer from being shown.
- [x] Do not introduce automatic paid retries for style alone. If a bounded repair
  call is later justified, explicitly account for cost, quotas, retry limits,
  duplicate requests and provider failure before enabling it.
- [x] Ensure invalid model output cannot bypass existing source or safety checks
  through a formatting fallback.

## Step 4 - Clarify the profile UI without breaking saved profiles

- [x] Display communication-character options as **Playful**, **Balanced** and
  **Structured** instead of Childlike/Childish and Authoritative. Keep the existing
  stored enum values initially; map labels consistently rather than migrating
  retained profile versions unnecessarily.
- [x] Explain the distinction between Tone: Playful and Communication character:
  Playful with short descriptions or consider a clearer label during design review.
- [x] Describe explanation-depth and teaching-style choices with realistic examples.
- [x] Label Speed as **Voice speed** and explain that it does not control text-chat
  response speed. Retain existing voice choices and accessibility.
- [x] Add a small static preview illustrating contrasting profiles. Clearly label
  it as illustrative; changing a selector must not trigger a paid AI request.
- [x] Keep selection controls keyboard-accessible and usable on mobile. Update
  Student and Parent profile displays consistently.

## Step 5 - Test behaviour, privacy and cost

- [x] Unit-test every property mapping, legacy fallback, instruction-injection
  boundary and precedence rule, including conflicting settings.
- [x] Integration-test both session scopes, tutor switching, follow-up pronouns,
  supplementary labels, citation integrity and retained profile-version identity.
- [x] Test direct/concise versus encouraging/detailed and low versus high
  friendliness using the same source-supported question. Scientific content and
  access rules must stay consistent while presentation differs.
- [x] Test all four teaching styles and explicit Teaching approach overrides.
- [x] Test a long calculation, requested multi-question revision, a source gap,
  ambiguity and a safety refusal so brevity or personality cannot degrade them.
- [x] Verify deterministic paper wording and approved marking points remain
  unchanged, with assessment assistance still blocked during formal attempts.
- [x] Test property changes cannot access another student's context or affect
  mastery, assessment outcomes, study plans or quota ownership.
- [x] Run routine checks with deterministic providers and zero paid calls. Prepare
  a small representative live evaluation for subjective tone/style; obtain an
  explicit evaluation budget before spending and distinguish its results from
  deterministic structural checks.
- [x] Record prompt/input size and any repair overhead against the baseline;
  avoid sending redundant property descriptions or excessive instructions.
- [x] Run frontend tests, typecheck, lint, build, backend regressions and generated
  API-contract checks if schemas change.

## Step 6 - Document and release

- [x] Update backend policy documentation and Student/Parent instructions with
  examples, precedence, text-versus-voice differences and honest limitations.
- [x] Confirm whether schema changes are actually needed. A backend policy and
  display-label update should not require a migration; add one only if the final
  implementation introduces persisted fields.
- [x] Prepare tested release evidence and review affected pilot prompt pins and
  general-release gates. Preserve student audience, content grants, model, expiry
  and all security controls when updating compatible pins.
- [ ] Commit and deploy only when implementation is separately authorised. Use
  the standard backup, migration-if-needed and acceptance procedure.
- [ ] Verify contrasting tutor profiles in a normal signed-in Student session on
  production, in Subject and Topic chat; retain factual/citation checks alongside
  the style review.
- [x] Provide rollback instructions that retain profile versions and transcripts;
  never disable safety/access gates to recover an older prompt.

## Completion criteria

- Every supported text property has explicit, versioned behaviour instructions.
- Measurable rules are checked with sensible task-specific exceptions; subjective
  properties have evaluation evidence and no claim of perfect enforcement.
- Students can recognise meaningful differences between contrasting profiles.
- Textbook evidence, scientific meaning, privacy and assessment rules are unchanged.
- Speed is clearly a voice property, saved profiles remain compatible, and routine
  settings changes make no paid AI calls.

## Implementation starting points

- `source-code/backend/app/services/tutor_agent.py`
- `source-code/backend/app/ai/prompts.py`
- `source-code/backend/app/services/tutor_profiles.py`
- `source-code/backend/app/services/tutor_past_papers.py`
- `source-code/backend/app/services/tutor_realtime.py`
- `source-code/frontend/features/tutor-profiles.tsx`
- `source-code/frontend/features/tutor-sessions.tsx`
- `source-code/backend/docs/tutor-subject-chat-and-context.md`

## Implementation evidence — 7 November 2026

- Policy and release evidence: `source-code/backend/docs/tutor-text-personalisation-and-chat.md` and `source-code/backend/evaluations/tutor/chatbot-personalisation-20261107.json`.
- 406 backend tests passed (1 skipped), 120 frontend tests passed; typecheck, lint and production build passed. API contracts regenerated. No schema migration required.
- The authorised live Evaluation sample used the existing cumulative US$0.75 ledger. Results are qualitative, not measured general accuracy. Visual mismatches found during evaluation were corrected and regression tested.
- Depth/paragraph targets are soft instruction preferences and versioned module defaults, not hard truncation or new environment settings. Official paper wording and deterministic safety/help replies remain unchanged.
- Production deployment and normal Student acceptance are pending; retain this plan in ongoing until those checks finish.
