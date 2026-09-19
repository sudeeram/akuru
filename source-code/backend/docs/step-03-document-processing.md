# Asynchronous document processing

AKURU stores each upload and its initial job in PostgreSQL before publishing the job ID to Redis. The HTTP request therefore returns promptly without making Redis the source of truth. If Redis is temporarily unavailable, the stored job remains queued and worker startup recovery republishes it.

## Local operation

Start PostgreSQL and Redis, apply migrations, and run the API and worker in separate terminals from `source-code`:

```bash
npm run backend:migrate
npm run backend:dev
```

```bash
npm run backend:worker
```

The worker uses `AKURU_REDIS_URL` and `AKURU_DOCUMENT_QUEUE_NAME`. Original files remain in the configured private storage backend. Do not run the worker with a different database or storage configuration from the API.

## State and recovery

An upload creates a `queued` document version and job. The worker claims it as `processing`, records its attempt and heartbeat, then moves it to `needs_review` after preflight. Later extraction and Admin review stages can move content to `completed`. A controlled failure records `failed`, a stable error code and a display-safe explanation. Admin can retry only failed jobs.

Redis contains disposable job identifiers. PostgreSQL contains authoritative status, progress, timestamps, attempt count, processing limits, extraction version, result and failure details. At startup, the worker republishes queued jobs and resets stale processing jobs to queued. Duplicate Redis deliveries are harmless because a worker only claims a queued row.

Each stage run is unique by document version, stage and extraction version. A completed run is reused when its input checksum still matches. Changing extraction logic requires a new `AKURU_EXTRACTION_VERSION`; it does not overwrite the provenance of an earlier result.

## Processing limits

Preflight executes in a spawned child process rather than the FastAPI or long-running worker process. It enforces `AKURU_DOCUMENT_JOB_TIMEOUT_SECONDS` and `AKURU_DOCUMENT_MAX_PAGES`. On Linux, including the OCI Ubuntu deployment target, it also applies `AKURU_DOCUMENT_JOB_MEMORY_MB` as an address-space limit. The reviewed default is 1536 MiB because OCR of image-only textbook PDFs needs substantially more working memory than native-text PDFs. macOS local development retains process and timeout isolation but does not apply the Linux resource limit. Retrying a failed job refreshes all three ceilings from the current configuration so an operator correction takes effect without re-uploading the source document.

The `deterministic-v1` stage validates the stored bytes, renders source pages, extracts native text and coordinates, invokes OCR for sparse/scanned pages, and records diagram/equation crops behind the same queue and idempotency contract. Scanned pages render at 240 DPI, receive deterministic contrast normalization, and use automatic page segmentation. OCR lines are assigned to left, right, spanning or single-column regions and persisted in layout-aware reading order. This supports textbook columns while retaining every original and normalized page for Admin comparison.

## Admin API

- `POST /api/v1/documents` returns both the document record and queued job.
- `GET /api/v1/documents/{document_id}/jobs/latest` returns current progress.
- `GET /api/v1/documents/{document_id}/jobs/{job_id}` returns a specific job.
- `POST /api/v1/documents/{document_id}/retry` requeues a failed job.

All routes require an authenticated Admin session. The Admin document library polls while a job is queued or processing and displays progress and useful failure text without exposing internal exceptions.

### Repairing historical review-state mismatches

Run the repair in report-only mode first:

```bash
cd backend
PYTHONPATH=. .venv/bin/python -m app.reconcile_document_reviews
```

The JSON report contains every proposed document-version and Library-state change. After reviewing it, apply the same calculation with an existing Admin username so completion events remain attributable:

```bash
PYTHONPATH=. .venv/bin/python -m app.reconcile_document_reviews --apply --actor-username ADMIN_USERNAME
```

The command never publishes topic content. It only reconciles extraction-review states from persisted pages and blocks.
