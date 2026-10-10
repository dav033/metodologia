---
req: REQ-013
status: planned
created: 2026-10-09
---
# Plan — REQ-013 Catalogue repositories

## Approach
Repositories are introduced as **views over the existing modules** (Phase 1, pure refactor, byte-identity proven by
snapshots), then the RAG gets a **logical partition** (`taller_items.repositorio`, migration 034, an always-on hard
filter whose default `sempertex` returns exactly today's rows), then new content, visibility, UI, pricing and
third-party packs land one per phase, each behind its own flag (default off = today). Ids are never rewritten: the
qualified id `<repo>:<localId>` is a handle over frozen local ids (SPEC §5). Alternatives and their rejection: SPEC §3.

Base: `origin/main` = `b4433bc9` (`C:/Users/davidt/Downloads/e6f`). One implementer per phase, one worktree per phase
(`git worktree add ../e8<x> -b feat/catalogo-<fase> origin/main`), rebased on main before review.

## Global constraints (every task)
- TypeScript without `any`; files ≤ 500 lines — `biblioteca.ts` (1 075), `herramientas-escena.ts` (1 294) and
  `Biblioteca.tsx` (829) must not grow: new code goes into new files.
- R8 layering: `src/lib/catalogo/{ids,tipos}.ts` are leaves; nothing under `src/lib/globos3d/**` imports
  `src/lib/catalogo/registro.ts` or `src/lib/catalogo/repositorios/**`.
- D-001 lazy: no entry content is built at import; `test-carga-3d` < 500 ms.
- Flags default off; with every flag off each phase is behaviour-identical (golden + byte-identity snapshots).
- Migrations: only 034, additive/idempotent, dry-run → owner notice → `npx tsx --env-file=<demo-decoracion>/.env.local
  scripts/migrate.ts --allow-remote`, logged. Apply on Neon **before** the code that reads the column reaches main.
- Paid runs: only Phase 3 embeddings, cap US$0.05 declared and logged (Gemini cap US$2/day).
- No `next build`, never restart :3010/:8000, never flip `GUIADA_MOTOR`, no customer-visible pricing change.
- Tests one suite at a time: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/<f>.ts`
  (UI tests without `--conditions`). Do not run `test-inyeccion-prompt`.
- RAG eval needs the git-ignored artefacts: copy `C:/Users/davidt/Downloads/e4r/data/taller/` into the worktree's
  `data/taller/` (never regenerate vectors to get them).
- Every phase ends with the antagonist review (architecture + orphan properties, D-013) and the reviewer pair
  (spec / standards) before merge.

Verify commands run from the worktree root of `demo-decoracion`.

---

## Phase 1 — Repository model as views (pure refactor) · size M (~1 day) · no flag
Goal: the three founding repositories exist as typed, manifest-described, lazily-loaded views; every catalogue entry
has exactly one repository; ids parse in both forms; **nothing observable changes**.

- [ ] T1 — Baselines on b4433bc9 *before any code change*: record the scene golden (already
  `scripts/test/dorado/armado-escena.json`), write the catalogue golden `scripts/test/dorado/catalogo-fondos.json`
  (sha of the built elements of each of the 51 `FONDOS_CATALOGO` entries with defaults + `mesa_param`/`sillas_param`
  presets) and the identity snapshot `scripts/test/dorado/identidad-catalogo.json` (sha256 of `DECLARACIONES_ESCENA`
  JSON, of `esquemaLecturaParaGemini()`, of the `prompt-lectura-foto` fondos text and of the `FONDOS_CATALOGO` id order)
  · files: `scripts/test/test-catalogo-dorado.ts`, `scripts/test/test-catalogo-identidad.ts` · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-dorado.ts` · covers: AC-1, AC-4
- [ ] T2 — Leaf modules: `src/lib/catalogo/ids.ts` (grammar, founding ids, slug regex, `parsearId`,
  `calificar` for founding prefixes) and `src/lib/catalogo/tipos.ts` (SPEC §4.1 types), no imports from `globos3d`
  · after: T1 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-ids.ts` · covers: §5.1
- [ ] T3 — Kind schemas `src/lib/catalogo/esquemas.ts` (zod per `clase`, manifest schema) and the explicit assignment
  table `src/lib/catalogo/asignacion-fondos.ts` (51 ids + 2 generators → `mobiliario` | `escenografia`)
  · after: T2 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-repositorios.ts` · covers: AC-5
- [ ] T4 — Repositories as views: `src/lib/catalogo/repositorios/{sempertex,mobiliario,escenografia}/{manifiesto.ts,cargador.ts}`
  (sempertex: library items + derived via `indexarEscena`, formats, colour table, shop props, guided plans/details/
  decorations, module types; mobiliario/escenografia: filters over `FONDOS_CATALOGO` in its order + generators);
  `src/lib/catalogo/registro.ts` (lazy `perezoso` getters, local-id index, `resolverEntrada`, `repositorioDeItem`,
  `repositorioDePieza`); lock file `src/lib/catalogo/repositorios.lock.json` + `huellaRepositorio`
  · after: T3 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-repositorios.ts` · covers: AC-5, AC-6, AC-12
- [ ] T5 — `entradaDeCatalogo` / `muebleDe` accept the qualified form through `ids.ts` (additive; short ids
  unchanged) · files: `src/lib/globos3d/fondos-escenografia.ts`, `mobiliario-catalogo.ts` · after: T2 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-fondos-escenografia.ts`
- [ ] T6 — Boundary tests: extend `scripts/test/test-motor-guiada-fronteras.ts` (closure must not contain
  `catalogo/registro.ts` or `catalogo/repositorios/**`) and add `scripts/test/test-estudio-fronteras.ts` (same for
  `src/app/3d/modulos/page.tsx`); add a `test-carga-3d` case: importing `@/lib/catalogo/registro` builds no entry
  · after: T4 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-motor-guiada-fronteras.ts` · covers: AC-3, AC-9
- [ ] T7 — Stored-data corpus: `scripts/test/fixtures/escenas-guardadas/` (golden scenes, the `referencias-dueno`
  readings compiled, a saved-owner-items sample, 3 scene JSON from Taller `ai_feedback` rows — staff scenes, no customer data) loads, builds
  and resolves every `mueble.id` in both forms · after: T4 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-compatibilidad.ts` · covers: AC-6

**Gate (all green, 0 diffs):** `npx tsc --noEmit`; `test-armado-escena-dorado`; `test-catalogo-dorado`;
`test-catalogo-identidad`; `test-catalogo-repositorios`; `test-catalogo-ids`; `test-catalogo-compatibilidad`;
`test-carga-3d`; `test-esquema-gemini`; `test-biblioteca`; `test-fondos-escenografia`; `test-mobiliario`;
`test-mobiliario-libre`; `test-motor-guiada-fronteras`; `test-estudio-fronteras`; `test-motor3d-frontera`.
**Rollback:** revert the merge (only new files + two additive lookups).

---

## Phase 2 — RAG partition: migration 034 + indexer + always-on filter · size M (~1 day) · after Phase 1
Goal: every `taller_items` row has a repository; every read query filters by the visible repositories (default
`sempertex` = all current rows, so results are identical); the indexer can never deactivate another repository.
Flag: `CATALOGO_REPOS_RAG` (default `sempertex`).

- [ ] T8 — `scripts/migrations/034_catalogo_repositorios.sql` exactly as SPEC §6.2 (header comment with rollback);
  `scripts/taller/evaluar-rag-local.ts` applies 034 after 028 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-migracion-034.ts` (PGlite: apply twice, every row `sempertex`, CHECK rejects `otro`, rollback statement works) · covers: AC-7
- [ ] T9 — Minimal visibility: `src/lib/catalogo/visibilidad.ts` with `reposVisibles(superficie)` = env
  `CATALOGO_REPOS_<SUPERFICIE>` → manifest default (runtime rows come in Phase 4) · after: T8 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-visibilidad.ts`
- [ ] T10 — Indexer: `RegistroParaIndice.repositorio` (absent in an old JSONL → `sempertex`), `RegistroTaller.repositorio`
  from `repositorioDeItem` (not hashed), `COLUMNAS_ITEM` + `repositorio`, upsert `WHERE … OR repositorio IS DISTINCT
  FROM EXCLUDED.repositorio …`, `construirConsultaHashes(repo)` / `construirDesactivarAusentes(ids, repo)` scoped;
  `scripts/taller/indexar-biblioteca.ts --repositorio=<id>` (default `sempertex`; any other needs
  `--permitir-otros-repos`) · files: `src/lib/taller/indice.ts`, `fichas.ts`, `fichas-tipos.ts` · after: T8 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-taller-indice.ts`
- [ ] T11 — Search: `FiltrosTaller.repositorios?`; `condicionesDuras` always adds `t.repositorio = ANY($visibles ∩
  pedidos)` (empty intersection → no rows, never "all"); `buscarEnTaller` passes `reposVisibles("rag")`; the in-memory
  fallback applies the same rule; `/api/taller/buscar` accepts `filtros.repositorios` (strict schema extended) and
  returns `repositorio` per result (additive); `buscar-foto.ts` goes through the same path. A test asserts that every
  SQL text built against `taller_items` contains the repository condition · files: `src/lib/taller/buscar-sql.ts`,
  `buscar.ts`, `src/app/api/taller/buscar/route.ts` · after: T9, T10 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-taller-buscar.ts` · covers: AC-8 (filter part)
- [ ] T12 — Eval on PGlite with 034 using the copied `data/taller/` artefacts: dev / holdout / photo acierto@5 and
  MRR ≥ the b4433bc9 baseline (`eval-2026-10-09.json`); write `data/taller/eval-<date>-req013-f2.json`
  · after: T11 · verify: `npx tsx --conditions=react-server scripts/taller/evaluar-rag-local.ts --pglite=C:/Users/davidt/Downloads/pglite-req013` · covers: AC-2
- [ ] T13 — Deploy runbook (in the phase PR description and the day log): dry-run 034 on Neon → owner notice →
  apply → `npx tsx --conditions=react-server scripts/taller/indexar-biblioteca.ts --comparar` shows no change caused
  by `repositorio` (content changes that predate REQ-013 are listed and handled as a normal re-index) → merge → Neon
  smoke (5 queries, same top-5 as before; latency within 10 %) · after: T12 · level: architecture

**Gate:** Phase 1 gate + `test-taller-indice`, `test-taller-buscar`, `test-migracion-034`, `test-catalogo-visibilidad`,
`test-escena-ia-biblioteca-rag`, `test-rag-db-reintento`, eval ≥ baseline. **Order is the gate:** 034 on Neon before
merge (otherwise `42703` → silent memory fallback). **Rollback:** revert code; then (optionally)
`ALTER TABLE taller_items DROP COLUMN IF EXISTS repositorio`.

---

## Phase 3 — Index `mobiliario` and `escenografia` (invisible by default) · size M (~1 day) · after Phase 2 is live on Neon
Goal: furniture and scenery become searchable rows of their own repositories; with default flags no surface sees
them. Flag: `CATALOGO_REPOS_RAG` (add `mobiliario,escenografia` to see them).

- [ ] T14 — Fichas for founding non-library entries: `src/lib/catalogo/fichas-fondos.ts` (Spanish 80–250 words: name,
  description, colours-in-order (`descripcionConColores`), measures and limits, seats (`asientosDeEntrada`), table/
  chair types for generators, synonyms from `fondos-sinonimos.ts`, provenance/licence); `tipo` = the `clase`
  (`mueble`, `mueble-fijo`, `generador`, `fondo`, `decorado`); `ResultadoTaller.tipo` widened accordingly
  · after: Phase 2 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-fichas-fondos.ts`
- [ ] T15 — Extractor per repository: `scripts/taller/extraer-biblioteca.ts --repositorio=<id>` writes
  `data/catalogos/<id>/fichas.jsonl` (sempertex keeps `data/taller/fichas.jsonl`); `.gitignore` covers
  `data/catalogos/*/` · after: T14 · verify: `npx tsx scripts/taller/extraer-biblioteca.ts --repositorio=mobiliario --sin-escribir`
- [ ] T16 — Paid: text embeddings for the 53 new fichas through the Python batch (`--fichas
  ../../data/catalogos/<id>/fichas.jsonl --ejecutar --tope-usd 0.05`), spend logged; index with `--repositorio=<id>
  --permitir-otros-repos` (PGlite first, Neon with notice) · after: T15 · level: architecture
- [ ] T17 — Memory fallback for the two repositories: keyword search over entry name/description/synonyms
  (tiny lists, same response shape) · files: `src/lib/catalogo/buscar-memoria-fondos.ts` · after: T14 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-taller-buscar.ts`
- [ ] T18 — Gold set `scripts/test/fixtures/oro-busqueda-catalogo.json` (≥ 15 owner-style queries: «sillas tiffany
  doradas», «mesa imperial para 10», «panel redondo con aro dorado», «base para el pastel», «cortina de flecos»…);
  HNSW starvation check: a `mobiliario`-only vector query returns ≥ min(k, 28) candidates; if not, add `SET LOCAL
  hnsw.ef_search` (or `hnsw.iterative_scan` if Neon's pgvector ≥ 0.8) inside the search transaction · after: T16 · verify: `npx tsx --conditions=react-server scripts/taller/evaluar-rag-local.ts --pglite=C:/Users/davidt/Downloads/pglite-req013 --oro=catalogo` (new `--oro` option) · covers: AC-8

**Gate:** with default flags the T12 eval is unchanged (new rows exist but are invisible); with all three repositories
visible: catalogue gold acierto@5 ≥ 90 % and Sempertex dev acierto@5 ≥ 95 % (reported, informs whether `rag` may
ever include them by default); AC-8 starvation test; Phase 2 gate. **Rollback:** `UPDATE taller_items SET activo =
FALSE WHERE repositorio <> 'sempertex'` (or keep — invisible by default).

---

## Phase 4 — Visibility per surface + AI catalogue filter · size M (~1 day) · after Phase 2 (∥ Phase 3)
Goal: one server-side resolver decides what each surface sees; the scene AI can filter by repository; customer
surfaces are provably Sempertex-only. Flags: `CATALOGO_REPOS_*`, `CATALOGO_FILTRO_IA`,
`CATALOGO_PERMITIR_SIN_PRECIO_CLIENTE`.

- [ ] T19 — Extract the 30 s runtime-settings reader from `src/lib/guiada-motor/bandera.ts` into
  `src/lib/ajustes/ajustes-runtime.ts` (pure refactor, same precedence for `guiada_motor`) · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-guiada-motor-bandera.ts`
- [ ] T20 — `visibilidad.ts`: runtime rows `catalogo_repos_<superficie>` → env → manifest; `catalogoPara(superficie)`;
  the `sin-precio` rule for `guiada`/`estudio`; boolean flags added to the `FeatureFlag` union (default off)
  · after: T19 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-visibilidad.ts` · covers: AC-9
- [ ] T21 — Scene AI: `repositorio` **string** parameter on `buscar_en_biblioteca` (declared only with
  `CATALOGO_FILTRO_IA`; description lists the visible ids; validated by `parsearRepositorio`), placed in
  `herramientas-escena-biblioteca-filtros.ts`; `insertar_de_biblioteca` accepts both id forms; `agregar_mobiliario`
  enum and the table tools derived from `reposVisibles("ia_taller")` (same order; absent when hidden); the photo
  reading list filtered by `reposVisibles("foto")` (order kept). The default visibility keeps today's module-level
  constants (byte-identical); declarations/schemas are rebuilt per request only when visibility differs (memoised by
  the visible set) · files: new `src/lib/catalogo/herramientas-ia.ts`,
  minimal edits in `herramientas-escena-mobiliario.ts`, `herramientas-escena-mesas.ts`, `lectura-foto.ts`,
  `prompt-lectura-foto.ts` · after: T20 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-esquema-gemini.ts` · covers: AC-4
- [ ] T22 — Customer-scope proofs: property test over the guided goldens (no piece whose `mueble.id` resolves outside
  `sempertex`); `test-catalogo-identidad` with flags off still byte-identical; owner-phrases subset with a mocked model
  («busca sillas tiffany» with filter `mobiliario` returns only furniture; «arco orgánico dorado» with `sempertex`)
  · after: T21 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-superficies.ts` · covers: AC-9

**Gate:** Phase 1 gate + `test-esquema-gemini` (flags off identical; on ≤ +1 024 B, 0 new enum values),
`test-escena-ia-biblioteca-rag`, `test-mobiliario-libre-ia`, `test-mobiliario-honestidad-integrado`,
`test-agente-escena`, `test-guiada-motor-bandera`, `test-motor-guiada*`, `test-modulos-*`, `test-catalogo-superficies`.
**Rollback:** flags off (runtime row delete) → identical; code revert if needed.

---

## Phase 5 — Taller «Añadir» by repository · size M (~1 day) · after Phase 4
Goal: the pro user browses Sempertex / Mobiliario / Escenografía (and Terceros later) separately. Flag:
`CATALOGO_UI_REPOSITORIOS` (served by the API, not `NEXT_PUBLIC_*`).

- [ ] T23 — `GET /api/catalogo/repositorios` (auth like `/api/taller/buscar`; manifests + `reposVisibles("taller")` +
  `ui` flag) · files: `src/app/api/catalogo/repositorios/route.ts` · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-api.ts`
- [ ] T24 — `PanelAnadir.tsx`: repository switcher (new `SelectorRepositorio.tsx`); Sempertex = today's tabs;
  Mobiliario = `FondosYMuebles` groups asiento + mesa + «Mesa con sillas a medida»; Escenografía = groups fondo +
  decorado; `FondosYMuebles` gets a `repositorio` prop; library grid filtered by repository through a new hook (no
  growth of `Biblioteca.tsx`); item detail shows provenance/licence; counts per repository · after: T23 · verify: `npx tsx scripts/test/test-anadir-repositorios.tsx` · covers: AC-11
- [ ] T25 — Shopping list: today's «Escenografía» lines split into «Mobiliario» / «Escenografía» sections (flag on);
  identical with flag off · after: T24 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-biblioteca.ts`
- [ ] T26 — Browser pass on :3010 (no restart; Playwright or Chrome MCP): flag off = today's panel; flag on = three
  repositories, add one item from each, undo works, mobile sheet works · after: T25

**Gate:** Phase 1 gate + `test-anadir-repositorios`, `test-mobiliario-libre-ui`, `test-carga-3d`, prerender safety
(no `Date.now()/Math.random()/new Date()` in render bodies or `useState` initialisers), product judge ≥ 8.
**Rollback:** flag off.

---

## Phase 6 — Price source per repository · size S–M (~0.5–1 day) · after Phase 1 (∥ Phases 2–5)
Goal: a quote is composed per repository; Sempertex unchanged; furniture can be priced from a rental list; nothing is
ever shown as 0. Flag: `CATALOGO_PRECIO_ALQUILER`.

- [ ] T27 — Port `src/lib/catalogo/precio.ts` (SPEC §8); `sempertex` adapter wrapping `bomDeEscena` →
  `planearCompra` → `cotizarBom` (no logic copied); `escenografia` and default `mobiliario` = `sin-precio`; shop props
  stay link-only · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-motor-guiada-precio.ts` · covers: AC-10
- [ ] T28 — Rental list: zod schema + loader for `data/catalogos/mobiliario/precios-alquiler-<vigencia>.json`
  (`idLocal` or generator type → price per unit/event, currency, validity); missing id → `sin-cobertura`; test fixture
  only under `scripts/test/fixtures/` (no real prices without the owner) · after: T27 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-precio-repositorios.ts`
- [ ] T29 — Taller (pro) list shows mobiliario prices when the flag is on and a list exists; the guided quote is not
  touched (it only sees `sempertex`) · after: T28 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-precio-repositorios.ts`

**Gate:** golden priced fixtures (`generar-golden-precio` outputs: counts + variant ids) unchanged,
`test-motor-guiada-precio`, `test-precio-chat-guiado`, `test-precio-repositorios`, Phase 1 gate. **Rollback:** flag off.

---

## Phase 7 — Qualified ids at boundaries + third-party packs · size M (~1 day) · after Phases 4–5
Goal: boundaries speak qualified ids; a `terceros/<slug>` pack can be dropped in as data with a mandatory licence.
Flags: `CATALOGO_IDS_CALIFICADOS`, `CATALOGO_TERCEROS`.

- [ ] T30 — Emit `idCalificado` (additive field; `id` stays local) in `/api/taller/buscar` results, AI tool results,
  feedback records and «Añadir» keys; every reader uses `parsearId` · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-catalogo-compatibilidad.ts` · covers: AC-6
- [ ] T31 — Terceros loader: `data/catalogos/terceros/<slug>/{manifiesto.json, entradas.jsonl}` validated with zod
  (licence mandatory, slug regex, local ids unique and not colliding with founding ids, `base` must resolve to a
  founding `mobiliario`/`escenografia` entry); insertion expands a `mueble-ref` into `mueble.id = <base>` +
  `mueble.ref = <qualified>` (`MuebleDePiezaSchema` gains `ref`, ≤ 60) with consumers: price, list name, detail;
  CLI `scripts/catalogo/validar-terceros.ts` · after: T30 · verify: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/test-terceros.ts` · covers: AC-13
- [ ] T32 — Sample pack fixture `scripts/test/fixtures/terceros-ejemplo/` (2 chairs, 1 backdrop) shown in «Añadir» only
  with `CATALOGO_TERCEROS`; not indexed in the RAG unless `CATALOGO_REPOS_RAG` lists it · after: T31 · verify: `npx tsx scripts/test/test-anadir-repositorios.tsx`

**Gate:** Phase 1 gate + `test-terceros`, `test-catalogo-compatibilidad`, `test-esquema-gemini`, eval unchanged with
default flags. **Rollback:** flags off.

---

## Dependencies & order
Phase 1 → Phase 2 (→ Neon 034 before merge) → Phase 3. Phase 4 after Phase 2 (∥ Phase 3). Phase 5 after Phase 4.
Phase 6 after Phase 1 (∥ 2–5). Phase 7 after Phases 4–5. Rebase each worktree on main before review; the exhaustive
assignment test will flag furniture added meanwhile by other branches (REQ-008/012 follow-ups, W2/W3).

## Verification (end to end)
1. With every flag off on main: `test-armado-escena-dorado`, `test-catalogo-dorado`, `test-catalogo-identidad`,
   `test-esquema-gemini` byte-identical; eval ≥ baseline on PGlite and Neon; guided and studio closures clean.
2. Flip on a preview (runtime rows, no deploy): `catalogo_repos_rag = sempertex,mobiliario,escenografia`,
   `CATALOGO_UI_REPOSITORIOS`, `CATALOGO_FILTRO_IA` → «Añadir» shows three repositories: Sempertex with today's four tabs, Mobiliario with 28 entries
   (26 + the 2 generators), Escenografía with 25; the scene AI answers «busca sillas tiffany» from
   `mobiliario` only; the guided chat and `/3d/modulos` are unchanged.
3. Delete the runtime rows → everything back to today within 30 s.

## Rulings
<!-- Judgment calls made during execution without asking:
- T<n>: <what I decided> — <why> — cost if wrong: <low/med/high> -->

## Progress log
<!-- One line per meaningful step, so work survives a context reset. -->

## Phase 3 run-book (verified 2026-10-10; NOT applied — apply only when every production reader runs ≥ d4b4020d, incl. the VPS)
Once per repo (`mobiliario`, `escenografia`), from `demo-decoracion`:
1. `npx tsx scripts/taller/extraer-biblioteca.ts --repositorio=<id>`
2. `cd services/ai-api && python -m app.taller.embeber_biblioteca --fichas ../../data/catalogos/<id>/fichas.jsonl --salida ../../data/catalogos/<id>/embeddings --modalidades texto --ejecutar --tope-usd 0.05` (GEMINI_API_KEY in the shell; ≈US$0.002 total)
3. `NODE_OPTIONS=--use-system-ca npx tsx --env-file=.env.local --conditions=react-server scripts/taller/indexar-biblioteca.ts --repositorio=<id> --permitir-otros-repos --confirmo-filtro-en-produccion --aplicar`
4. `NODE_OPTIONS=--use-system-ca npx tsx --env-file=.env.local --conditions=react-server scripts/taller/subir-vectores.ts --repositorio=<id> --aplicar`
Rollback: `UPDATE taller_items SET activo = FALSE WHERE repositorio <> 'sempertex';`. `evaluar-rag-local --oro=catalogo` sends 20 paid Gemini queries on first run (≈US$0.00004). Visibility (`CATALOGO_REPOS_RAG`) stays off until catalogue acierto@5 ≥ 90 % hybrid and the scene AI can insert catalogue ids (Phase 4).

### Applied 2026-10-10
Run-book Phase 3 applied to Neon production (owner approval D-037; VPS e7b7aeaa, Vercel main; run from `demo-decoracion` @ e7b7aeaa). `CATALOGO_REPOS_RAG` untouched (visibility off).
- **Extract:** `mobiliario` 28 fichas (mueble 25, generador 2, mueble-fijo 1); `escenografia` 25 fichas (decorado 17, fondo 8). 0 outside 80-250 words.
- **Embeddings (paid, Python batch, text only, `gemini-embedding-2` @768):** mobiliario 28 vectors ~US$0.0010, escenografia 25 vectors ~US$0.0008 (cap US$0.05 each, never close). Plus eval: 20 catalogue query embeddings ~US$0.00004. Total paid ~US$0.0018.
- **Dry runs (ensayo + `--comparar`, read-only on Neon):** mobiliario new 28 / changed 0 / reactivated 0 / unchanged 0 / absent-from-file (would deactivate) 0; escenografia new 25 / 0 / 0 / 0 / 0. No sempertex rows involved, no deletions. `subir-vectores` compare: 28 and 25 to upload.
- **Applied rows:** `taller_items` mobiliario 28 (all active), escenografia 25 (all active). **Vectors uploaded:** 28 + 25 = 53 text embeddings (`taller_items_embeddings`).
- **Sempertex untouched:** before/after snapshot via read-only SQL: 3217 rows (3217 active), md5 over `id||hash||activo` identical (`ad448920...`), 6447 sempertex embeddings before and after. (`indexar-biblioteca.ts --comparar` for sempertex could not run: no `data/taller/fichas.jsonl` in the main checkout, so the SQL fingerprint was used instead.)
- **Eval `evaluar-rag-local.ts --oro=catalogo` (local PGlite with all three repos visible, same fichas and vectors as Neon):** catalogue gold (20 queries) **acierto@5 hybrid 95.0%** (lexical 80.0%; recall@5 64.4%, MRR 0.812, nDCG@10 0.769), Gate >= 90% met. Sempertex dev (40 queries) acierto@5 hybrid 100.0% (lexical 97.5%), Gate >= 95% met. Worst catalogue queries: Q63 panel redondo con aro dorado, Q67 letrero de neon, Q76 carrito de dulces, Q71 arco metalico, Q72 pared de lentejuelas doradas.
- **Warnings / notes:** (1) the Python module needed the repo's `services/ai-api/.venv` (system Python lacks `httpx`); key loaded by a scratch wrapper, never printed. (2) pg `sslmode` deprecation warning (harmless). (3) The eval used PGlite from a scratch dir (`pglite-req013` no longer existed) and untracked copies of the sempertex data (`data/taller/{fichas.jsonl,embeddings,eval-vectores-consulta.json}` from worktree e7o) placed in the gitignored `demo-decoracion/data/taller/`. (4) The eval is local, not against Neon; Neon retrieval behaviour (HNSW starvation check, AC-8) is not exercised by it. No rollback used. Nothing committed.
