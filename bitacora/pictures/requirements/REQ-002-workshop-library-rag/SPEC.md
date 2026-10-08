# REQ-002 — RAG for the 3D workshop library (decorations, structures, templates)

Status: DRAFT — round 1 answered 2026-10-08 (see Answers). No code yet.

## Why
The owner: "we need to put this in a database; let's design a RAG only for decorations, structures and templates".
Today the Library (`biblioteca.ts`, ~1,000+ items: Sempertex ideas, organic bases, owner references, predefined
decorations, utilería, presets, and pieces derived from every scene) lives in code and memory; search is keyword +
stems (`buscarEnBiblioteca`, worker filters); the owner's own items live only in localStorage. The scene AI and the
photo→scene flow need to FIND the right template by meaning, parts and products ("a freeform column with grapes
like the graduation one", "garland with monstera leaves in emerald and blush").

## Existing infra to reuse (explorer report, 2026-10-08)
- Neon Postgres + pgvector (768-d) already used by the product RAG (`src/lib/rag/**`, migrations 001/007/009/012).
- Embeddings: gemini-embedding (768) through the Python service (`RAG_PYTHON_QUERY_EMBEDDINGS_ENABLED`).
- Retrieval pattern: Spanish FTS + trigram + vector fused with RRF, hard filters, optional Python rerank.
- Audit/telemetry: `decidir`, `registrarGemini`; feature flags in env.

## Proposal
**Source of truth**: code stays the source for factory items; the DB is the searchable index (+ the owner's own
items, which move from localStorage to the DB).

**Tables** (new migration):
- `taller_items`: id, tipo (escena/conjunto/estructura/decoracion/utileria), nombre, descripcion, ocasiones[],
  fuente (tipo, titulo, url, foto), tipos_pieza[], formatos[], colores[] (codes), partes[], productos[], medidas
  (alto/ancho cm), globos (count), ficha (generated Spanish text), contenido JSONB, hash, propietario (null = factory),
  timestamps.
- `taller_items_partes`: item_id, parte, formato, color, cantidad (from `inventarioDe`) — structured filters
  ("has LOL-660", "R-24 in 940").
- `taller_items_embeddings`: item_id, modelo, vector(768), texto.

**Ingest** (`scripts/taller/indexar-biblioteca.ts`): build every item (incl. derived pieces), compute facets from the
parts contract (`partes-globos.ts`), write the *ficha* (what it is, silhouette, parts → formats/colours/counts,
products, occasions, measures, source), upsert by content hash, embed only changed items. Cost: ~1,500 fichas ×
~300 tokens of embeddings ≈ cents; declared cap per run.

**Retrieval** (`src/lib/taller/buscar.ts`, route `/api/taller/buscar`): hybrid FTS + trigram + vector with RRF and
hard filters (tipo, ocasión, formatos, colores, partes, medidas, fuente, propietario); glossary-normalised queries
(`glosario-taller.ts`). Flag `TALLER_RAG_ENABLED`; if off or DB down, fall back to today's in-memory search.

**Consumers**: (1) the scene AI's `buscar_en_biblioteca` / `insertar_de_biblioteca`; (2) photo→scene: after the reading,
retrieve the closest templates from its facets + summary and start from them; (3) the Library panel's search;
(4) the owner's saved items (multi-device).

**Phase 2 (optional)**: image embeddings of the item photos and renders, to match an uploaded photo directly.

## Open questions (round 1)
1. Move the owner's saved items (and later saved scenes) from the browser to the DB? (rec: items now, scenes later)
2. Reuse gemini-embedding 768 via the Python service, like the product RAG? (rec: yes)
3. Image embeddings for photo→template matching now or phase 2? (rec: phase 2)
4. Retrieval in Next (Vercel → Neon) like the product RAG, or in Python? (rec: Next)
5. Code as source of truth for factory items, DB as index (rec), or DB as the editable source with an admin?

## Constraints
No customer data in the repo; paid runs declare a cap; the VPS is deployed by hand and only with notice; no restart of
:3010/:8000.

## Answers (round 1, 2026-10-08)
1. Owner's saved items move to the DB now (scenes later). 2. Embeddings explained; reuse gemini-embedding 768 (pending
his OK after the explanation). 3. Image search: YES (include image embeddings of item photos/renders; after text).
4. Owner asked whether Python is more optimal. Answer given: split by job — Python = ingest/fichas review, embeddings
(text and image), analysis and rerank (batch, data ecosystem); Next = the online query (one SQL to Neon, no hop to the
hand-deployed VPS, falls back to in-memory). The scene building stays in TS (the 3D engine), so the extractor that
produces items/facets runs in TS and hands JSONL to Python. 5. Code = source for factory items; DB = index + owner's items.
