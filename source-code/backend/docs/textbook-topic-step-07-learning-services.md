# Step 7 — Topic-aware learning services

Published topics are the learning boundary for topic-structured textbooks. Retrieval first limits chunks to the student's cumulative covered-topic set, the published textbook edition, the published topic, its current published topic-content version and a reviewed document. Vector ranking happens only after those constraints are applied.

Assessment questions now retain `topic_ids` and `topic_weights` alongside the legacy unit fields. Published results create topic mastery evidence. Group (Unit or Module) progress is calculated as an explainable, evidence-weighted aggregation of the child topics; it is a summary and never adds evidence across topics.

Weaknesses, recommendations and study-plan items may use `topic_id`. Their approved source chunk must belong to that exact topic. Where no reviewed topic evidence exists, services return an evidence-insufficient outcome rather than using material from another topic.

Tutor sessions can retain either legacy unit context or new active-topic context during the migration. New topic sessions allow only switches to topics covered by the student's cumulative plan. Tutor source search, citations, learner context, practice selection, recommendations, quotas, transcript retention and formal-assessment restrictions remain subject- and student-scoped.

The migration `h86c0d2f7a97_add_topic_learning_context.py` adds the topic assessment fields and the nullable transition links required for topic-owned learning records. Apply it with `npm run backend:migrate` from `source-code`.
