# Textbook Topic Step 1 — schema foundation

Status: implemented locally in Alembic revision `c31d9e5a7b42`.

## Authoritative hierarchy

The new content hierarchy is:

```text
textbooks
└── textbook_groups
    └── textbook_topics
        └── textbook_topic_documents
```

`textbooks.group_label` is constrained to `unit` or `module`. Backend rules always use the same `textbook_groups` table; the label controls presentation only. Topic codes are unique across a textbook, group sequence is unique inside a textbook, and topic sequence is unique inside a group.

`textbook_topics` repeats textbook, course and subject scope so composite foreign keys can prove that a topic's group and logical textbook agree. Its composite scope key supports later same-subject relationships without relying on client input or an AI classification.

An uploaded document remains an immutable `document_version`. `textbook_topic_documents` connects that version to a topic with its role, order, printed-page range and review state. It supports several primary, supporting or reference parts per topic without creating several logical textbooks.

## Topic-level learning structures

- `curriculum_plan_topics` records the one Grade + Term introduction period for each topic within a curriculum-plan version.
- `official_question_topic_mappings` stores weighted, required topic mappings for an official question version.
- `retrieval_chunks.group_id` and `retrieval_chunks.topic_id` preserve topic provenance alongside the current compatibility unit reference.
- `assessment_curriculum_snapshots.covered_topic_ids` freezes topic eligibility for an assessment.
- `topic_mastery`, `topic_mastery_dimensions` and `topic_mastery_events` own topic evidence and scores.
- Weakness, recommendation and study-plan rows have transitional `topic_id` references ready for their service migrations.
- Curriculum plans and official material versions have a transitional logical `textbook_id` reference.

## Clean migration guard

The migration calls `_require_empty_content()` before changing the schema. It checks all document, textbook, curriculum, official-material, question-mapping, assessment, mastery, planning, Tutor-learning and evaluation-content tables and raises before DDL when any row exists.

Identity, authentication, family/enrolment, course/subject catalogue, provider configuration, quota, audit and operational records are not migration-sensitive and remain unchanged.

The local and production audits both proved the educational-content scope empty. The production migration is intentionally deferred to the production rollout step so the deployed application and database change together.

## Staged compatibility boundary

The existing unit tables and columns remain temporarily because the currently deployed APIs still use them. They are deprecated compatibility scaffolding and must receive no new production content. Steps 2–7 move structure, upload, coverage, mapping, retrieval, mastery, Tutor and study-planning services to topics. A later reviewed migration can then remove the unused unit-only structures without transforming records.

This staged boundary keeps all existing authentication and portal checks passing while preventing an incomplete mixture of old services and the new schema from being deployed as a content-ready release.
