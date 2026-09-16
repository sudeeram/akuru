# Textbook topics Step 4: independent publication

Textbook structure publication and topic-content publication are separate operations. A structure may list all topics while only reviewed topics become available as learning evidence.

## Readiness

Every Admin textbook response includes topic diagnostics: content state, current published version, source counts, processing/review/failure counts, unresolved pages and blocks, average extraction confidence, and explicit readiness checks.

A topic can be published only when:

- it has at least one primary textbook part;
- every attached source has finished processing;
- every flagged page and block has been resolved by an Admin;
- no attached source has failed; and
- reviewed blocks contain publishable text or formulae.

The publication request requires explicit confirmation of the topic, source versions and extraction review.

## Immutable versions and retrieval

`textbook_topic_content_versions` stores an immutable source and extraction manifest. `textbook_topic_content_sources` binds the exact document versions, roles and extractor versions used. Publication creates topic-scoped retrieval chunks only from reviewed blocks and records exact page, bounding-box and retained asset provenance.

Publishing corrected content creates a new version. The previous content version and its retrieval chunks become `superseded`; historical rows and manifests remain intact. Only chunks connected to the current published topic-content version are active, preventing unreviewed or superseded extraction from entering new retrieval or mapping workflows.

The readiness comparison fingerprints the current source set, extraction version and reviewed block content against the published manifest. An unchanged topic cannot create a redundant version; a new upload or reviewed correction must exist first.

Migration `f64a8b0d5e75` adds the topic-content version tables and topic-version provenance on retrieval chunks. Topic chunks deliberately have no legacy unit identifier; Step 7 will authorize and retrieve them through topic coverage.
