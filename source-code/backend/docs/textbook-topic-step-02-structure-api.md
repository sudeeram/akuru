# Textbook topics Step 2: structure API

Step 2 separates a logical textbook structure from uploaded files. An Admin first creates an iGCSE textbook edition, chooses whether its groups are displayed as **Units** or **Modules**, and then creates ordered groups and topics.

All routes under `/api/v1/admin/textbooks` require an authenticated Admin. Mutations also require the session CSRF token. Responses expose random `book_`, `group_`, and `topic_` public references; database UUIDs stay internal.

## Rules

- A textbook belongs to one active course and subject. Its groups and topics inherit that scope and cannot be moved across books or subjects.
- Textbook title and edition, group codes and positions, and topic codes and positions are unique in their documented scope.
- Reordering requires every active public reference exactly once. The service moves rows through a temporary sequence range to preserve database uniqueness during swaps.
- Publishing requires explicit identity and structure confirmation, at least one group, and at least one topic in every group.
- Each publication stores an immutable JSON snapshot in `textbook_structure_versions`. Later edits return the live structure to draft and the next publication creates another version.
- Unreferenced groups and topics may be removed because immutable published snapshots retain their history. Topics referenced by documents, coverage, question mappings, retrieval, mastery, recommendations, study plans, or assessment snapshots are protected.
- Every create, edit, reorder, publish, remove, and archive operation writes an audit event.

Alembic revision `d42e6f7b8c53` adds the immutable structure-version table. Production remains on its prior schema until the release step in the roadmap.
