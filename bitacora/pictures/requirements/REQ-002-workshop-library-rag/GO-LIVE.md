# REQ-002 — Go-live runbook (needs owner notice before step 1)

Everything is on main with `TALLER_RAG_ENABLED` OFF. Steps, in order, from the working repo with `.env.local`:

1. **Migrations on Neon** (additive): `npm run rag:migrate:check`, then `npm run rag:migrate -- --allow-remote`
   (applies 028_taller_biblioteca + 029_ai_call_log_embedding_imagen). Rollback: drop the 4 `taller_*` tables;
   029 only widens a CHECK.
2. **Fresh fichas** (16 ideas changed occasions): `npx tsx scripts/taller/extraer-biblioteca.ts`.
3. **Vectors** for changed fichas only (cache by hash): from `services/ai-api`,
   `python -m app.taller.embeber_biblioteca --fichas ../../data/taller/fichas.jsonl --manifest-renders ../../data/taller/renders/manifest.json --ejecutar --tope-usd 0.05`.
4. **Index**: `npx tsx --conditions=react-server scripts/taller/indexar-biblioteca.ts --comparar` (dry), then
   `--aplicar`; upsert vectors from `data/taller/embeddings` (reader `src/lib/taller/vectores-cache.ts`).
   **4b. Vectors to the DB** (added 2026-10-09 — no script did this before): `npx tsx --conditions=react-server
   scripts/taller/subir-vectores.ts --comparar`, then `--aplicar` (batches of 200; skips text vectors whose ficha
   changed; the text hash is sha256("RETRIEVAL_DOCUMENT|ficha"), same as the Python batch).
   Status 2026-10-09: steps 1–4 done on Neon (3217 items, 12567 part lines); 4b running (6447 vectors).
   `taller_taxonomia` stays empty: the search reads the taxonomy from code (no writer exists) — orphan table, P-030.
5. **Smoke on Neon**: run `scripts/taller/evaluar-rag-local.ts`-style queries against the real pool (latency,
   same top-5 as PGlite for 5 queries); check that format/part ids in `taller_items` match the glossary.
6. **Flag**: set `TALLER_RAG_ENABLED=true` in Vercel (preview first), redeploy, test Library search, «Buscar por
   foto», and the scene AI `buscar_en_biblioteca`.
7. Vercel builds `@sempertex/agente-core` (`vercel-build`); locally run
   `npm run build --workspace=@sempertex/agente-core` after pulling.
