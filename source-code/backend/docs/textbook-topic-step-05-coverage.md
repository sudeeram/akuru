# Step 5 — Incremental, versioned topic coverage

Curriculum coverage now assigns each published textbook topic to the Grade and Term where it is first introduced. Only topics with a published content version from the active published iGCSE textbook edition are selectable. The database uniqueness rule keeps one introduction period per topic and plan version.

`POST /api/v1/admin/curriculum-plans/{subject}/draft` creates the next draft. It copies the current published plan and records its lineage, so an Admin can add topics taught this term without rebuilding earlier coverage. Saving calculates additions, removals and moves. Publishing a draft with a removal or move requires `confirmPublishedChanges`; additions do not require destructive-change confirmation. Every action is audited and prior plan versions remain immutable and superseded rather than overwritten.

Student eligibility is the union of topic introductions across the student's recorded progression through the current Grade and Term. Missing reached periods fail closed with topic-level coverage diagnostics. Assessment snapshots store the exact plan and covered topic IDs; publishing later coverage cannot change a started assessment. Until Step 6 supplies confirmed topic mappings, the question-pool diagnostic reports a topic-level shortage instead of falling back to unrelated unit mappings.

Migration `g75b9c1e6f86` makes the legacy textbook-content reference optional for new topic plans and adds `based_on_plan_id` for draft lineage. Legacy unit plans remain readable during the staged Steps 6–7 migration.
