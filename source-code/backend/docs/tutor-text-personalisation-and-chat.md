# Tutor text personalisation and chat behaviour

Implemented: 7 November 2026. No database migration. Prompt pins: baseline 1.2.0; supplementary 2.2.0.

## Request flow

Ownership, source access and formal-assessment exclusions run before help or teaching. Existing request replay runs before paid work. Clear capability/topic-list requests use authoritative eligibility data and deterministic transcript exchanges, without a provider call. Mixed factual/help questions stay on the evidence-backed path. Existing topic discovery and past-paper commands retain their specialised dispatch, approved wording and reveal rules.

Ordinary requests use `tutor_intent.py` (teaching-intent-v1) to choose the activity, including recent activity for continuations. Clients send `auto`; legacy supported modes remain accepted, but French conversation outside French is rejected. Natural French-conversation requests in other subjects receive a free boundary message. Routing does not start formal assessments or award marks.

`tutor_chat_capabilities.py` supplies the protected session `/tools` endpoint and help replies. It checks current subject/topic releases, pilot restrictions, question eligibility, voice source/model release and remaining voice allowance. No automatic-marking capability is promised. The Subject chat topic focus appears only within usable practice/voice tools; Topic chat retains Move topic.

## Personalisation and precedence

`tutor_personality.py` compiles allowlisted stored values into trusted instructions. Session profile versions are retained; switching tutors changes the selected snapshot without changing historical turns. Arbitrary tutor names, avatar, presentation and voice speed are not promoted into text instructions.

Priority: safety/access/evidence/assessment rules, explicit permitted student request and activity, profile style/depth, then tone/friendliness/enthusiasm. Calm, encouraging, direct and playful wording remain age-appropriate and scientifically honest. Friendliness never permits shaming, manipulative attachment or human-relationship claims. No emojis are requested. Display labels Playful/Balanced/Structured preserve existing stored enums.

Concise/standard/detailed default word budgets are 120/250/500, doubled for revision, questions and calculations/comparisons. Explicit detail requests may expand the target. Question counts override the default one-check-question preference. These are module-level policy defaults, not deployment tuning knobs. Style deviations (word count, question count, expressive punctuation, emoji) are logged; answers are never clipped and style alone never triggers paid repair. No hard paragraph-size restriction is imposed on scientific reasoning. Subjective tone is evaluated separately, not claimed as mechanically enforced.

Generated textbook and supplementary explanations receive the policy. Deterministic help, official paper wording, approved marking points, assessment-service feedback and safety notices are preserved. Voice retains its existing separate instruction and speed mapping.

Turn and invocation provenance contain routing policy/reason, personalisation policy version and profile-version identity. Existing account routing, quotas, request claims and family isolation remain in force. Source chunks are not duplicated into usage metadata.

## Approved visual selection

`tutor_chat_visuals.py` selects existing stored assets only. Candidates must belong to authorised published topic content, match the publication manifest checksum/version/caption/alt text, retain live Admin approval and pass the visual tool release gate. Page renders, prose screenshots and decorative/text-only assets are excluded. Labelled scientific figures and useful tables remain eligible. Previously generated explanatory media requires independent human review, publication and an authorised source citation; chat never generates or renders a new image.

Concept matching prioritises newly named concepts over old context, supports follow-up anchors and avoids generic word collisions. Numbered figures ambiguous across topics ask for clarification. Up to two useful figures are selected, with repeat suppression unless explicitly requested. Opening a protected asset rechecks access and approval; withdrawal revokes saved URLs. Captions, accessible labels and source provenance accompany assets. Missing figures are an honest unavailable result, not a page-image fallback.

The output validator rejects model-authored Markdown images, image HTML/data, SVG/Mermaid/ASCII substitutes. The client accepts visual URLs only from the session's protected approved-visual/media routes and renders normal text safely. Ordinary formulas and scientific notation remain valid.

## Validation and operations

Routine regression uses deterministic providers and disposable database schemas. Live Chemistry/Biology cases use a separate Evaluation key with the cumulative US$0.75 ledger; no image pixels are sent to the model. Live results are semantic observations, not measured general accuracy. Broad-word visual mismatches found in live and production Student checks were corrected with concept filtering, structural ranking, plural plant-label exclusions and nucleus-specific matches. The production check covers cross-topic distractors beyond the single-topic evaluation package. The default personality compiler adds 1,435 UTF-8 bytes (192 words) to the prior instructions; there are no paid style-repair calls.

Use the standard reviewed-release script (backup, contract/build checks, migration verification and service health). Advance compatible pilot prompt/evidence pins with `deploy/ubuntu/update-tutor-chat-release.py`; preserve student audience, topic/content grants, model, expiry and security gates. See committed evaluation evidence for counts. Existing general-release evaluation records require explicit re-evaluation for the new prompt versions.

Rollback the code to the previous reviewed release and restore its protected environment backup together; keep profile versions, transcripts and database data. Never disable release/access gates to accommodate an older prompt. No new schema means there is no downgrade migration for this change.

## Overview-help follow-up — 7 November 2026

Teaching-intent policy `teaching-intent-v1.1` recognises bounded overview paraphrases such as “Can you tell me what can you teach me on this subject?”, “What can I learn in Biology?” and polite tell-me wrappers. Named factual requests (“teach me about viruses”) and mixed factual/help requests remain on grounded teaching paths. Capability reply version 1.1.0 lists accessible published topics grouped under their saved textbook Unit/Module headings in Subject chat; explicit overview requests also work in Topic chat with the scope limitation explained. This is an authoritative catalogue response, with no model call, no inferred mastery and no new schema.
