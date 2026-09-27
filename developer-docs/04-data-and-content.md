# Data and content lifecycle

## PostgreSQL and migrations

SQLAlchemy models in `backend/app/models.py` define the runtime relational model. Alembic migrations under `backend/migrations/versions` define how an existing environment reaches it. The current production path begins at the consolidated `0001_initial_akuru_schema` baseline and advances only through reviewed forward migrations.

Never delete or recreate a populated database for a routine feature. Prefer additive migrations, prove them on disposable databases, run `alembic check`, take encrypted production backups, and apply them through the release script.

UUID primary keys are internal. Stable `public_ref` values identify many textbook, Tutor and content resources in APIs and user-visible links.

## Core relationships

```mermaid
erDiagram
    USER ||--o| STUDENT_PROFILE : has
    USER ||--o{ AUTH_SESSION : owns
    USER ||--o{ STUDENT_PROGRESSION : progresses
    TEXTBOOK ||--o{ TEXTBOOK_GROUP : contains
    TEXTBOOK_GROUP ||--o{ TEXTBOOK_TOPIC : contains
    TEXTBOOK_TOPIC ||--o{ TEXTBOOK_TOPIC_DOCUMENT : attaches
    DOCUMENT ||--o{ DOCUMENT_VERSION : versions
    DOCUMENT_VERSION ||--o{ DOCUMENT_PAGE : renders
    DOCUMENT_PAGE ||--o{ DOCUMENT_BLOCK : extracts
    TEXTBOOK_TOPIC ||--o{ TEXTBOOK_TOPIC_CONTENT_VERSION : publishes
    TEXTBOOK_TOPIC_CONTENT_VERSION ||--o{ RETRIEVAL_CHUNK : indexes
    TEXTBOOK_TOPIC ||--o{ FLASHCARD_DECK : grounds
```

The actual model contains additional assessment, mastery, Tutor, audit, quota and evaluation tables. Read the model and latest migrations before changing a relationship.

## Textbook hierarchy

The current hierarchy is:

```text
Textbook -> Unit or Module group -> Topic -> attached document versions
```

A topic may publish independently. Adding later topics does not change the stable identity of an existing published topic. Course and subject are inherited and validated; a Chemistry source cannot be attached to a Mathematics topic.

Attached sources have roles:

- `primary`: canonical text used for readiness, publication and retrieval;
- `supporting`: explicitly included distinct supporting text;
- `reference`: explicitly included reference text;
- `visual_reference`: provenance and selectable visual assets; its OCR text is excluded from ordinary retrieval.

Exactly selected and approved visual assets enter a published topic version with document/version/checksum/page/bounding-box provenance and accessible text. A selected but unapproved visual blocks publication.

Each Topic attachment has one explicit role: `primary`, `supporting`, `reference`
or `visual_reference`. The first three require complete extraction review and
can contribute text. A visual reference contributes page provenance and approved
assets only; every page needs a confirmed printed-page label, while its OCR
blocks are excluded from readiness and retrieval. Role changes recalculate the
draft attachment without mutating a published manifest.

Scientific inline review is extraction-block metadata containing a versioned,
restricted mark document, normalized search alias and renderer version. Original
OCR text and geometry remain available for audit. The API validates mark types
and ranges and rejects arbitrary HTML. Existing JSON metadata stores the feature,
so there is no migration.

Paragraph reconstruction also uses existing page and block metadata. New
extractions preserve raw line text, OCR paragraph/line identities, geometry,
layout column, confidence and versioned boundary decisions. Reconstructed block
text is the editable draft; raw evidence remains available through comparison.
Final-document confirmation is stored in `Document.source_metadata` with the
exact content hash and is repeated in `DocumentEvent`. Any saved content change
changes the computed hash and therefore invalidates the confirmation. Published
content versions remain immutable and cannot be reprocessed.

## Document lifecycle

1. Admin uploads a supported private file.
2. AKURU validates signature, size, subject prerequisites and malware policy.
3. The original receives a checksum and immutable version record.
4. Redis carries the job ID to the worker.
5. The worker preflights, renders pages, extracts native text/OCR, reading order, equations, tables and visual assets.
6. Low-confidence or structurally important pages/blocks remain review tasks.
7. Admin corrections update review evidence; completion synchronizes document, version and active topic attachment readiness.
8. A separate explicit operation publishes immutable topic content.

Storage bytes are private. Database rows provide authorization, ownership and evidence. Local storage defaults outside the checkout at `/data/akuru/documents`; OCI storage is optional.

## Retrieval and citations

Only reviewed, published, authorized topic content produces active retrieval chunks. pgvector stores 256-dimensional embeddings. Queries are filtered by Student access, course, subject and eligible topics before relevance ranking. Exact source metadata is retained so Tutor and learning features can cite the approved document and page.

Duplicate source text must not create repeated active evidence. Visual-reference OCR is deliberately excluded while approved visuals retain their own provenance.

## Curriculum and assessment snapshots

Coverage is versioned by course, subject, grade and term. Student eligibility is cumulative across recorded progression periods. Mock-paper selection requires every topic mapped to a question to be covered.

Starting an assessment freezes question versions, coverage, rubric, ordering, sources and deadlines. Later curriculum or question changes affect new sessions only. Assessment result revisions retain prior versions and reviewer provenance.

## Publication rule

Publication is a domain transition, not a boolean edited by the client. Services verify review completion, source availability, exact versions, subject ownership, evidence, duplicate protection and any applicable evaluation gate inside the publication transaction.
