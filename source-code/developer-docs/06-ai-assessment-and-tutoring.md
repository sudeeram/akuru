# AI, assessment and tutoring

## Provider architecture

`backend/app/ai` defines the provider interface and structured result types. Implementations include a deterministic fake provider for tests and the OpenAI provider for configured environments. Factories select the implementation; domain services should not instantiate vendor clients directly.

The account router separates a credential alias and priority from the secret stored in the backend environment. Lower numeric priority is tried first. Bounded retries happen within an account; configured provider limit errors can move one complete request to the next eligible account. The same prompt, schema and authorized context are used after failover.

## Prompt and response rules

Prompts are named and versioned. Persist the prompt name/version, provider/model, source references and usage with AI-backed decisions. Treat a behavior-changing prompt edit like a code change: create a new version and rerun the applicable evaluation corpus.

Use structured responses and validate:

- expected identifiers and exact rubric points;
- allowed enum values and bounded numeric fields;
- cited sources and Student evidence;
- mark totals and confidence thresholds; and
- absence of sources the authenticated learner cannot access.

## Assessment pipeline

An assessment is created from immutable eligible question versions. On submission, deterministic subject signals and the frozen rubric accompany the Student answer. The marking workflow uses structured passes to decide official marking points and then produce an exam-ready answer plus teaching feedback. Server code remains responsible for totals and publication state.

Low-confidence, subjective, handwriting-dependent or release-gate failures produce `needs_review`. Admin/Parent review creates another immutable result version rather than changing history. Mastery and progress consume published reviewed results only.

## Retrieval grounding

Retrieval starts from published topic content and applies authorization and curriculum filters before ranking. Tutor explanations, flashcards, media and recommendations must cite exact approved evidence. If the score or evidence is insufficient, the service returns an evidence-insufficient outcome rather than inventing a page reference.

## Tutor architecture

Tutor services are split by responsibility:

- profiles and curated child-safe avatars/voices;
- sessions, transcript turns and Tutor switching;
- learner context from mastery, weaknesses and recent mistakes;
- deterministic next-topic recommendations;
- exact textbook sources and citations;
- structured Tutor replies and bounded tool results;
- guided practice and evidence-backed observations;
- per-child allowances, history, parent summaries and safety events;
- realtime voice credentials/captions; and
- official-source and explanatory learning visuals.

Text, voice and tool capability flags default off. Production also requires staged database release gates. Voice is available only in practice contexts and is blocked during formal assessment.

Tutor observations do not automatically rewrite mastery or study plans. They are bounded signals with evidence and explicit downstream review rules.

## Flashcards

Flashcard generation uses only published, Student-eligible topic content. Admin reviews individual cards and releases an immutable deck version. Student sessions use released versions so later edits do not rewrite learning history. Citations link every factual answer back to approved topic evidence.

## Evaluation gates

An Admin-approved subject/workflow corpus defines expected behavior. Candidate model and prompt versions produce recorded runs and metrics. Automatic behavior activates only for a passing release that exactly matches runtime model and prompt versions. Missing, stale or failing evidence restores review-required behavior.
