# Database baseline Step 1: topic-only runtime schema

Step 1 removed the compatibility layer that kept AKURU's original unit-only data model active beside the newer textbook hierarchy.

## Final domain model

The authoritative curriculum path is:

```text
Textbook → TextbookGroup → TextbookTopic → published topic content
```

`TextbookGroup` intentionally retains the display label **Unit** or **Module** because Edexcel books use both terms. These labels describe sections of a book. They do not refer to the removed `textbook_units` table or create a second mapping model.

Topic references now control curriculum coverage, official-question mapping, retrieval and citations, assessment snapshots, mastery, study plans, Tutor sessions, Tutor practice, Tutor recommendations, transcript summaries, realtime context, and educational media.

## Removed compatibility schema

The SQLAlchemy metadata no longer defines:

- `textbook_units`, `textbook_content_versions`, or `textbook_unit_versions`
- `curriculum_plan_units` or `term_coverage`
- `official_question_unit_mappings`
- legacy `questions` and `question_units`
- `unit_mastery`, `unit_mastery_dimensions`, or `unit_mastery_events`
- `tutor_session_unit_events`

Compatibility columns and JSON fields such as `unit_id`, `unitIds`, `covered_unit_ids`, and `unit_evidence` were removed from current models and API contracts.

## Removed runtime paths

The old textbook-review workflow and its document routes were removed. Admins use the textbook structure workflow to create Unit or Module groups, define topics, attach scanned parts to a topic, review extraction quality, and publish each topic.

Tutor session start, switching, practice, sources, learner context, recommendations, history, realtime, and signals use topic references exclusively. The routes are `switch-topic` and `next-topic`.

Topic mastery is persisted. Unit or Module summaries are calculated from topic mastery and are not stored independently.

## Verification

`tests/test_topic_only_schema.py` fails if deprecated tables return to SQLAlchemy metadata, if runtime Python contains a deprecated compatibility token, or if OpenAPI exposes removed routes or fields.

The frontend OpenAPI contract is regenerated from this topic-only API. Frontend tests assert the topic-based workflows and types.

The existing local database still reflects the pre-squash migration chain. It is deliberately unchanged during this step. Database-backed integration tests that query renamed columns require the clean baseline created in Step 2 and exercised on a disposable database in Step 3.
