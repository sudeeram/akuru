# Backend API

## Student published textbook access

The Student Topic response also enumerates labelled Visual Reference pages from
the published source manifest. A role-checked page-image endpoint serves the
original render only when the enrolled Student can read that published Topic
and the referenced document version remains reviewed. Existing publications
without page lists in their manifest resolve pages from the exact published
document version; no draft Visual Reference is exposed.
The thumbnail endpoint applies the same authorization and published-source
checks as the full page endpoint, then downsizes the page image in memory.
Student page and thumbnail responses use private, no-store cache headers.

`GET /api/v1/student/textbooks` lists books with a published structure and at
least one published Topic content version in the Student's enrolled subjects.
`GET /api/v1/student/textbooks/{bookRef}/topics/{topicRef}` returns reviewed
passages from the active Topic content version, published page metadata and
approved visual references. Page-image and visual endpoints recheck the same
Student role, subject enrolment, published structure and Topic content on every
request. They return private no-store image responses. Page images use a Topic
page ordinal, so two PDF parts can each have a physical page 1 without
ambiguity. Draft structure edits are excluded by reading the latest published
structure snapshot. Grade/Term limits continue to govern assessed practice,
not textbook reading. No new database tables are required for this reader.

## Textbook source moves

`POST /api/v1/admin/textbooks/{textbookRef}/topics/{topicRef}/sources/{documentId}/move` moves an unreferenced source within the same textbook. It requires Admin authentication and CSRF protection, validates the destination through the textbook scope, rejects duplicates, and blocks sources used by published content, retrieval chunks, or reviewed visual assets. A successful move updates source metadata and writes a `textbook_topic_document.moved` audit event. No database migration is required for this UI release.

## Application composition

`app/main.py` creates FastAPI, installs error handlers and security middleware, includes the v1 router, and exposes `/health` plus authenticated `/ready`. API documentation is available only in development.

`app/api/v1/router.py` assembles domain routers under `/api/v1`. Each domain generally follows this direction:

```text
route -> Pydantic schema -> service -> repository/model/storage/provider
```

Routes translate HTTP concerns. Services own business rules and transactions. Repositories hold reusable persistence queries. Adapters isolate AI, queue and object-storage implementations.

## HTTP layer

Files under `app/api/v1` should:

- declare explicit request and response models;
- apply the narrowest authentication/role dependency;
- require CSRF on mutations;
- pass the authenticated `Principal` into services;
- use public references in user-facing routes where available; and
- avoid embedding business decisions in route functions.

The common middleware applies host and origin validation, per-path body limits, rate limiting and security headers. Ordinary JSON bodies are limited to 1 MB; document and assessment-working endpoints use configured limits.

## Schemas and errors

Pydantic models under `app/schemas` are the public contract. Response models must omit password hashes, session digests, storage keys, provider credentials and internal implementation data. Validation constraints should be expressed in schemas when they are local to one payload; cross-record constraints belong in services.

Domain failures use stable error codes and user-safe messages from `app/errors.py`. Use an appropriate status:

- `400/422` for invalid input;
- `401` for no valid session;
- `403` for insufficient role or ownership;
- `404` when an authorized caller cannot access the requested resource;
- `409` for lifecycle, prerequisite or concurrency conflicts; and
- `413` for configured upload limits.

## Service layer

Services under `app/services` own workflows such as account creation, document processing, textbook publication, retrieval, assessments, mastery, flashcards and tutoring. A service should:

1. load authoritative records;
2. verify ownership, role, subject, course and lifecycle;
3. lock rows or use immutable versions where races matter;
4. make all related database changes in one transaction;
5. store audit/provenance evidence; and
6. return a response-safe result.

Do not rely on a frontend filter or an earlier request for current authorization. Recheck access when files, citations, results and generated media are delivered.

## External adapters

- `app/ai`: provider interface, fake provider, OpenAI provider, prompts and account routing.
- `app/storage`: private local filesystem and OCI Object Storage adapters.
- `app/queue`: Redis queue abstraction.
- `app/workers/document_worker.py`: consumes durable job IDs and advances extraction stages.
- `app/malware.py`: configured fail-closed scanner boundary.

Dependencies are selected through factories so tests can use deterministic substitutes.

## Background work

Document uploads synchronously validate authorization, metadata and file limits, store the original privately, create database records and enqueue a job. The worker renders and extracts content, writing progress and evidence to PostgreSQL. It must be safe to retry: stage/version keys and stored status prevent duplicate authoritative publication.

PostgreSQL is authoritative for job state. Redis loss must not turn queued work into published content. Admin operational screens expose failed jobs and retry paths.

## Adding an endpoint

Add or update the schema, service, route and tests. Include the router if it is a new domain. Regenerate the contract, update the matching `frontend/api/<domain>` operation and type files, and build the corresponding role UI. Run the full verification gate before committing.
