# Subject chat and conversational context

Implemented 7 November 2026. This is an additive release: migration
`0019_tutor_chat_scope` defaults every existing session to `topic`.

## Session scope and source authorization

Students choose Topic chat or Subject chat before starting a session. Scope is
persisted and cannot be changed through the topic-switch endpoint. Subject chat
requires an enrolled subject with released, published, cumulatively covered
topics. It does not grant access to the whole syllabus or bypass pilot scopes.

The existing non-null `active_topic_id` is retained as an explicit practice/voice
focus. In Subject chat it is not a retrieval restriction. Source searches use
exact authorized topic/content-version pairs; citations derive their textbook,
group and topic identity from the chunk, never from the practice focus. Opening
citations/assets and nearby context repeats authorization, including coverage,
publication and pilot gates. Topic chat keeps single-topic retrieval.

Past-paper releases, automatic-marking readiness, formal-assessment exclusions,
quotas and family isolation remain unchanged. Educational media and voice stay
focused on the chosen practice topic. Cross-topic proposed tutor signals are not
stored against that focus, preventing misleading topic attribution. Session
summaries include cited topics and a Subject/Topic chat activity label.

## Follow-up resolution

`services/tutor_conversation.py` assembles only this session's recent turns. Both
student and assistant messages contribute to retrieval context; no paid routing
call is introduced. Model history is capped at 4,800 characters, with 1,200 per
turn. Retrieval uses at most four recent turns plus a bounded named-question
anchor. Original student messages are preserved without rewriting the transcript.
Explicit named requests override old retrieval context. A refusal, clarification
or uncertain reply prevents resolution back through that boundary. An explicit
Topic-chat topic switch resets model/retrieval context, while tutor-profile
switches preserve it. Subject-chat practice-focus changes do not reset scope.

The model is instructed to resolve pronouns from context, clarify genuinely
ambiguous references and never treat earlier generated text as published source
evidence. Bounded context is not permanent or unlimited conversation memory.

Prompt versions: textbook-only `1.1.0`; supplementary `2.1.0`. Production pilot
pins and evidence digests must be updated together with the compatible release;
do not disable release gates. Model identity, topic/content scope, expiry and
student audience must remain unchanged.

## Acceptance

Run `tests/test_tutor_subject_chat.py` and the Tutor, access, auth and assessment
regressions. They cover session defaults, durable scope, context bounds,
assistant-introduced antecedents, explicit new questions, source cross-topic
retrieval and immediate coverage revocation. No live model calls are made by
these tests. Check the frontend scope radio controls, history labels, reload,
login isolation and separate practice/voice focus.

In a released Student account, end an existing conversation before creating a
Subject chat. Ask a Biology question, follow with "Why does it happen?", then
ask an explicit question from another covered topic. Verify each cited topic and
source. Also repeat a focused Topic chat. These live checks assess model behaviour
in addition to deterministic routing and authorization tests.
