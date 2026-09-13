# Approved retrieval and RAG

AKURU indexes only published, reviewed learning content. `retrieval_chunks` stores immutable embedding versions for textbook blocks, marking points, and examiner guidance. Each chunk retains its document version, unit, page, bounding box, and optional source asset.

An admin reindexes one changed document with `POST /api/v1/retrieval/admin/reindex`. Existing active chunks for that document become superseded; unrelated documents remain untouched. This keeps corrections auditable and limits reprocessing.

Students and parents search with `POST /api/v1/retrieval/search`. The backend derives the student's cumulative units from the published curriculum plan and checks the student-subject assignment before similarity ranking. It filters active chunks by iGCSE course, requested subject, eligible unit, and published source. Parents may search only for linked children. A student may search only for their own account.

Every result includes an authenticated `sourceUrl`. `GET /api/v1/retrieval/evidence/{chunkId}?studentId=...` repeats the authorization and publication checks, then returns the cited page and bounding box. It never grants access to the full admin-only source file.

Development defaults to deterministic local embeddings. Production semantic retrieval should use:

```dotenv
AKURU_EMBEDDING_PROVIDER=openai
AKURU_EMBEDDING_MODEL=text-embedding-3-small
AKURU_EMBEDDING_DIMENSIONS=256
```

The PostgreSQL server must have pgvector installed before migrations run. For the local EDB PostgreSQL 18 installation on macOS:

```bash
git clone --branch v0.8.6 --depth 1 https://github.com/pgvector/pgvector.git /tmp/akuru-pgvector
cd /tmp/akuru-pgvector
make PG_CONFIG=/Library/PostgreSQL/18/bin/pg_config
sudo env PG_CONFIG=/Library/PostgreSQL/18/bin/pg_config make install
```

The Alembic migration enables the `vector` extension and creates a cosine HNSW index.
