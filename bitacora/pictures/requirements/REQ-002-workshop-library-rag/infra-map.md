# REQ-002 — Existing RAG infrastructure (explorer, 2026-10-08)

- **Pool**: `src/lib/rag/db.ts` (DATABASE_URL, max 20, 5 s timeout), read retry `db-reintento.ts`; `RagUnavailableError`
  only when every branch fails.
- **Hybrid search**: `src/lib/rag/retrieval/search.ts` (weights FTS 0.55 / trigram 0.3 / vector 0.15),
  `retrieval/rrf.ts` (k = 60, auditable). Spanish FTS with unaccent (migration 002), pg_trgm GIN (009), pgvector
  768 exact search (no HNSW yet — products are few; the library will need HNSW).
- **Embeddings**: `src/lib/rag/embeddings.ts` — model **gemini-embedding-2, 768 dims**, RETRIEVAL_DOCUMENT /
  RETRIEVAL_QUERY; query embeddings optionally via Python `POST /internal/v1/embed`
  (`RAG_PYTHON_QUERY_EMBEDDINGS_ENABLED`, default off); documents via Gemini API at ingest; every call logged with
  `registrarGemini`; idempotency key `embedding:<corr>:<sha256(text)>`; failure → lexical-only.
- **Rerank**: Python `POST /internal/v1/rerank` (cross-encoder, ~80 MB, single worker), flag `RAG_RERANK_ENABLED` off.
- **Flags**: RAG_ENABLED, RAG_USE_VECTOR, RAG_USE_FULLTEXT, RAG_USE_TRIGRAM, RAG_RERANK_ENABLED,
  RAG_PYTHON_QUERY_EMBEDDINGS_ENABLED (`src/lib/ia/nucleo/feature-flags.ts`).
- **Migrations**: `scripts/migrations/001…026` (Postgres, idempotent DDL, applied by npm scripts or manual SQL);
  023 = embedding provenance (dims, task type, unused `catalog_embedding_job_lock`); 012 = scene catalog extension
  (additive, little retrieval code). `services/ai-api/migrations/001` = Python operational schema.
- **No image-embedding infrastructure.**

## Implications for the library tables
- New migration `027_taller_items.sql` in `scripts/migrations/` following the catalog conventions; HNSW index on
  the vector columns from day one; reuse `getRagPool`, `rrf.ts` and `embeddings.ts` (document/query task types).
- Keep retrieval in Next (one SQL, fallback to in-memory search); Python only for batch embeddings and rerank.
- Pool of 20 shared with the product RAG: keep the library query to one round-trip.
