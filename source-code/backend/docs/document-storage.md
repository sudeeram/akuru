# Private document storage

AKURU stores document metadata and provenance in PostgreSQL and original bytes in private object storage. Browser clients can access those bytes only through an authenticated, authorized FastAPI endpoint; object keys are never public URLs.

## Local development

The default `.env.example` selects `AKURU_STORAGE_BACKEND=local` and writes beneath `backend/.local-data/documents`. The path is ignored by Git. Server-generated object keys and path-confinement checks prevent filenames from escaping this root.

Admin upload accepts raw PDF, PNG or JPEG bytes at `POST /api/v1/documents`. Metadata is supplied as query fields and the original filename in `X-Filename`. FastAPI verifies authentication, CSRF, size, extension, declared content type and binary signature before storage. SHA-256 uniqueness rejects identical uploads.

Useful endpoints:

- `GET /api/v1/documents` lists active documents for Admin.
- `GET /api/v1/documents/{id}` returns status and provenance for Admin.
- `GET /api/v1/documents/{id}/content` streams the private original to Admin.
- `POST /api/v1/documents/{id}/retry` records a retry for a failed version.
- `DELETE /api/v1/documents/{id}` soft-removes it and records the event while retaining original evidence.

## OCI production adapter

Set `AKURU_STORAGE_BACKEND=oci`, the namespace and private bucket variables. The adapter uses the OCI SDK's default configuration chain. Install its separately declared production dependency with:

```bash
python -m pip install -r requirements-oci.txt
```

On an OCI compute instance, use an instance principal and a narrowly scoped dynamic-group policy for the designated private bucket. Bucket objects must remain private. OCI Vault and deployment wiring are finalized in the production-security roadmap step.

## Database records

- `documents` holds logical classification, course, subject and source metadata.
- `document_versions` holds immutable original filename, storage key, checksum, size and uploader.
- `document_assets` is reserved for derived page, diagram, equation and image assets with source coordinates.
- `document_events` is the append-only upload, retry, removal and later processing history.

Removal is deliberately soft at this stage so an accidental Admin action does not destroy source evidence. A future retention workflow can purge database and object records after an explicit retention decision.
