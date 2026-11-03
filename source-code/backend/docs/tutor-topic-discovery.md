# Topic discovery in Tutor chat

Students can ask location questions such as “I have learnt about viruses. Which topic does this belong to?” from any active topic session. The existing authenticated agent-turn endpoint handles these requests before ordinary topic-scoped teaching or past-paper practice.

## Behaviour

The deterministic lookup searches only the current subject's topics returned by the student's session options: published cumulative curriculum coverage intersected with explicit pilot grants when configured. The active session is revalidated, and every candidate is checked with the existing Tutor source-access gate, including pilot content-version checks and formal-assessment restrictions. Published book/topic checks and the active published content version are required. Only active textbook chunks from published, nonremoved documents and reviewed blocks are considered.

Concept matching normalises existing retrieval terms and a small set of aliases (including viruses/viral → virus). All substantive query concepts must occur in a factual block. Exercise questions, answer spaces and image-only blocks are excluded as evidence. Occurrence and heading matches rank up to five topics; ranking is a text-match heuristic, not an accuracy probability or proof of syllabus importance. No model invocation, embedding call or AI quota reservation is needed.

The response adds an optional `topicMatches` list containing stable public references, textbook/group/topic labels, content version, a page reference and a short matching excerpt. Ordinary citations stay empty: discovery does not mint cross-topic source URLs or relax the active-topic citation/asset API. The exchange is retained in the normal session transcript, with deterministic provenance. Existing request-key replay and safety-event detection are retained.

The chat displays matches and an **Open this topic** action. Only that action invokes the existing authenticated topic-switch API; it rechecks eligibility. The current topic is determined from current session state, so a retained discovery response cannot enable a redundant switch. Changing topics preserves the transcript and clears old practice/paper state through the existing session transition logic.

A missing match means insufficient evidence in the student's accessible published topics, not absence from the complete syllabus. Ambiguous concepts can yield several related matches. This intentionally does not use general model knowledge to invent curriculum mappings. More aliases can be added with regression cases as needed.

## Validation

The prepared 22-topic Biology corpus ranks Topic 2, **The Variety of Living Organisms**, first for the requested virus query. Its strongest block is on printed page 30. Related mentions occur in topics 21, 22, 5, 19 and 15. The UI caps the result set at five.

Backend regression tests cover intent recognition, factual versus exercise evidence, aliases, unrelated queries, missing published content, subject isolation, candidate access denial, active-session access failure, excerpt positioning and routing before paid teaching. Frontend rendering tests cover escaped excerpts, page labels, disabled current-topic/busy actions and empty results. No database migration or new environment setting is required.
