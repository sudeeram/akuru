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

Flashcards are delivered as curated, checksum-bound release artifacts prepared outside the production request path. A deterministic validator confirms hierarchy ownership, published content versions, exact evidence, wording, duplicates and scientific notation before a transactional, idempotent import. The Admin interface inspects or withdraws releases but does not generate or edit cards.

Student flashcard citations return presentation metadata instead of linking to the retrieval JSON endpoint. Approved primary-source figures are resolved by an explicit artifact reference or an unambiguous reviewed caption match. Printed textbook pages are resolved separately by printed-page label from a published `visual_reference` source and served only through the owning Student session. This preserves source separation and prevents one child from requesting another child's learning assets.

Document review stores a normalized `reviewedCaption` on the visual block when a Figure caption is adjacent to, or embedded near the beginning of, another extracted block. This avoids rewriting or discarding a larger paragraph that may also contain examinable text. Visual-asset selection uses the reviewed caption in preference to raw OCR text.

Student sessions use immutable card snapshots and deterministic Quick, Normal, Full topic, Difficult, Due today and Unit mixed modes. Per-child scheduling state changes future selection without calling an AI model or changing authoritative mastery. Citations link every factual answer back to approved topic evidence.

## Evaluation gates

An Admin-approved subject/workflow corpus defines expected behavior. Candidate model and prompt versions produce recorded runs and metrics. Automatic behavior activates only for a passing release that exactly matches runtime model and prompt versions. Missing, stale or failing evidence restores review-required behavior.

## Structured marking rules

`app/schemas/marking_rules.py` defines the private version-1 rule contract; `app/services/marking_rules.py` validates references/dependencies and allocates credit after model point matching. Review parts retain `assessmentReadiness` independently from content status. The workspace response exposes `automaticAssessmentReady` and detailed `assessmentBlockers`; draft preparation and official scheme publication enforce readiness separately.

The compiler namespaces point codes per subpart and creates a group for every paper-specified subpart maximum. Additional groups, required full-credit points, accepted equivalents and combined responses survive preparation in the versioned `mark_scheme_entry_versions.scoring_rules` JSON column (migration `0013_structured_marking_rules`). They are copied into frozen assessment rubrics, so changing a later draft cannot change an existing attempt.

For structured rubrics, both AI passes must identify every point, preserve criteria, and provide exact evidence for awarded matches. Standalone approved phrases may produce deterministic matches; longer semantic variants remain model evidence decisions. The server caps credit and records raw decisions, matched/credited point IDs and per-point outcomes. `matched_capped` and `not_required` outcomes do not create negative mastery/weakness evidence. Human result review uses the same allocator. Student views distinguish unused alternatives from mistakes; the existing formal-assessment visibility gate keeps private rubric rules out of active student payloads.

The v1 contract supports unit-credit points and nested/disjoint groups. More complex conditional rejection rules or alternate allocation paths must be marked manual-only, not approximated by additive points. Local synthetic tests do not establish live-model quality; existing confidence, reconciliation and release gates continue to apply.

Rollout: back up the database, apply the additive migration, deploy backend/frontend together, then configure and confirm scoring rules through the Admin review UI. Legacy workspace content approvals remain, but default to unchecked automatic readiness. Published legacy additive rubrics still use the legacy scorer; previously invalid overcomplete legacy rubrics remain blocked. Configure Q2(a)'s accepted equivalents and combined response before removing its historical limitation note. No production content is changed by this migration.

Dependencies that interact with selective/capped groups are explicitly rejected in rule v1, rather than risk under-allocation. Dependencies within ordinary additive subparts remain supported. Keep unsupported combinations manual-only. Exact phrase matching is disabled for an answer containing negation markers, leaving that answer to semantic evidence matching and existing review gates.

### Official-paper textbook page evidence

`ReviewPart.textbookEvidence` stores topic reference, document-version UUID, PDF page position and the reviewed printed-page label in the existing review JSON. No relational migration is required. The Admin-only topic-evidence endpoint exposes eligible visual pages from the current published topic manifest. Saves validate topic/subject ownership, historical visual-source publication membership and page labels. Existing references survive label edits as historical provenance; the UI flags references absent from current options for revalidation. Question-save audit events retain previous and new page-reference lists. Primary-text repagination does not rewrite these references.

Coverage reasons remain explanatory prose. Existing pilot reasons are not silently rewritten: the review UI offers removal of legacy parenthesized textbook-page references, preserving the conceptual explanation. Admins select verified visual pages separately.


## AI-generated worked graph answers

The implementation uses a versioned `GeneratedWorkedAnswer` draft and durable worker polling, the existing OpenAI account router, strict declarative graph schemas and trusted PyMuPDF plotting. Admin review and a separate attach operation feed immutable, explicitly generated private assets into the existing `AnswerVisual` release/snapshot pipeline. Source hashes invalidate current drafts without rewriting historical attempt answers.

Practice reveals record `worked_answer` interactions and exclude those questions from independent mastery evidence. Formal assessment assistance is rejected; rubric/image release follows the existing submission gate. Generation is disabled by default and requires configured account aliases. See [the backend architecture and operation guide](../source-code/backend/docs/ai-generated-worked-answers.md) and [the 1C source audit](../source-code/backend/docs/ai-generated-worked-answers-1c-audit.md).
