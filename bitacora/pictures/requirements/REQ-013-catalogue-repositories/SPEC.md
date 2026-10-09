---
id: REQ-013
status: ready
created: 2026-10-09
track: standard
---
# REQ-013 — Catalogue repositories (ADR)

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

Owner (2026-10-09, marathon brief W6): «tenemos el repositorio de globos y decoraciones Sempertex pero queremos
separarlo del repositorio de por ejemplo mobiliario y nuevas cosas que queremos hacer en el futuro».

Grounded in `origin/main` = `b4433bc9` (worktree `C:/Users/davidt/Downloads/e6f`). All paths below are relative to
`demo-decoracion/`.

---

## 1. Context

### 1.1 What exists today (one undivided catalogue)

| Source | Where | Size (b4433bc9) | Ids today | Priced? |
|---|---|---|---|---|
| Factory library (`BIBLIOTECA_FABRICA`) | `src/lib/globos3d/biblioteca.ts:1000-1068` | 557 items: `idea:` 423 · `decoracion:` 63 · `base-organica:` 20 · `utileria:` 17 · `celebra:` 13 · `referencia:` 13 · `escena:` 8 | prefixed (`idea:<slug>`…) | latex balloons only (crosswalk); shop products (utilería, impresos, metalizados) are links without price |
| Derived library items | `indexarEscena` (`biblioteca.ts:718`) | ~2.6 k (3 217 rows in Neon incl. factory) | `<sceneId>~<nodeId>` | same |
| Sempertex ideas (lazy, D-001) | `src/lib/globos3d/ideas-sempertex/` (lots 01–30, `fuentes.ts`, `tipos.ts`) + `ideas-figuras.ts`, `ideas-formas.ts`, `ideas-impresos.ts` | 423 | `idea:<slug>` | balloons |
| Guided-chat library | `src/lib/biblioteca-sempertex/`: `planes-ideas.json` (v1, 28 plans, reader `lib/plan/planes-ideas-guardados.ts`), `detalles-ideas.json` (31, reader `detalle-idea.ts`), `decoraciones.json` (46: 31 real, 15 example; reader `biblioteca.ts`), `proveedores.json` (13 example suppliers) | — | idea keys | balloons (Python / engine BOM) |
| Balloon formats & colours | `FORMATOS_GLOBO` (14, `src/lib/globos3d/formatos.ts:31`), colour table `contracts/domain/v1/sempertex/tabla-color.json` (90 codes, `sempertex-color.v1`, loaded as `TABLA_SEMPERTEX` in `src/lib/plan/referencia-sempertex.ts:60`), `colores-formato.ts` | — | `R-12`, `LOL-660`, codes `570`… | defines the crosswalk key `formatoId\|codigo` |
| Shop props (utilería) | `CATALOGO_UTILERIA` (`utileria-catalogo.ts:39`, 620 shop entries, no price field) | 620 | shop url | link only |
| Fixed backdrops (`FONDOS_BASE`) | `src/lib/globos3d/fondos-escenografia.ts:93-104` | 9 | bare snake_case (`panel_redondo`) | no ("escenografía: no cotiza") |
| Parametric furniture + standing décor (`CATALOGO_MOBILIARIO`) | `src/lib/globos3d/mobiliario-catalogo.ts:338` (+ `mobiliario-*.ts` builders) | 42 (asiento 9 · mesa 16 · decorado 17) | bare snake_case (`silla_tiffany`, `pastel`) | no |
| Parametric table/chair sets (REQ-012) | `mobiliario-conjunto*.ts`, `mobiliario-mesas-param.ts`, `mobiliario-sillas-param.ts` | 2 generators | `mesa_param`, `sillas_param` (labels in `pieza.mueble.id`) | no |
| One registry for both | `FONDOS_CATALOGO = [...FONDOS_BASE, ...CATALOGO_MOBILIARIO]` (`fondos-escenografia.ts:106`) | 51 | — | — |

Consumers of the undivided registry:
- Taller «Añadir» = `PanelAnadir.tsx` with 4 tabs (Estructuras, Decoraciones, Utilería, Ideas; `:22-29`, content
  `:132-179`); `FONDOS_CATALOGO` appears only in the Utilería tab through `FondosYMuebles.tsx` (groups fondo, asiento,
  mesa, decorado; «Mesa con sillas a medida» button). The library grid («De la biblioteca», `Biblioteca.tsx`) runs in
  the Web Worker `biblioteca.worker.ts` → `biblioteca-motor.ts` → `globos3d/biblioteca.ts`.
- Photo reading: `lectura-foto.ts:153` puts every `FONDOS_CATALOGO` id in a `z.enum`; `prompt-lectura-foto.ts:77`
  lists them all, in order, in the Gemini prompt; the reading schema has its own 22 528 B cap.
- Scene AI (`herramientas-escena.ts`): `buscar_en_biblioteca` (`:286`; texto, tipo, ocasion, colores, tipo_pieza,
  limite + `CAMPOS_FILTROS_BIBLIOTECA`: celebracion, tematica, formato, parte, alto/ancho, fuente),
  `insertar_de_biblioteca` (`:319`, takes an item `id`), `agregar_del_catalogo`, `usar_preset`;
  `agregar_mobiliario` (`herramientas-escena-mobiliario.ts:311`, `id: z.enum(<all 51 FONDOS ids>)`),
  `agregar_mesas` / `cambiar_sillas` / `cambiar_mesas` (`herramientas-escena-mesas.ts`), salon and centrepiece tools.
- `detectar-globos-ia.ts`, `escenografia-ingles.ts` / `mobiliario-ingles.ts` (FLUX names), `fondos-sinonimos.ts`.
- The **engine itself**: `escena.ts` → `mobiliario-pieza.ts` → `fondos-escenografia.ts` / `mobiliario-catalogo.ts`
  (an `escenografia` piece is built by looking up its `mueble.id`). Hence the guided motor and the module studio
  reach `FONDOS_CATALOGO` *transitively* even though their own code never lists furniture.

RAG (REQ-002, D-010): migration `028_taller_biblioteca.sql` → `taller_items` (PK `id`, `propietario`, `activo`,
`hash`), `taller_items_partes`, `taller_items_embeddings` (partial HNSW per modality), orphan `taller_taxonomia`
(P-030). Extractor `scripts/taller/extraer-biblioteca.ts` → `data/taller/fichas.jsonl` (git-ignored); vectors in
`data/taller/embeddings/` (cache keyed by id + `hash_entrada`); indexer `scripts/taller/indexar-biblioteca.ts`
(upsert by hash, deactivates absent factory ids); search `src/lib/taller/buscar.ts` + pure SQL builder
`buscar-sql.ts` (`filtrados AS MATERIALIZED` CTE + FTS / trigram / vector branches + RRF), route
`/api/taller/buscar` (strict zod body), in-memory fallback. Only library items are indexed: furniture and backdrops
are **not** in the RAG today. Eval: gold set `scripts/test/fixtures/oro-busqueda-taller.json` (40 queries + 13
photos; holdout `oro-busqueda-taller-holdout.json`, 15), metrics in `src/lib/taller/evaluar.ts`, runners
`scripts/taller/evaluar-busqueda.ts` (memory vs Neon) and `evaluar-rag-local.ts --pglite=<dir>` (applies only 028
today). acierto@5 97.5 % (RAG) vs 87.5 % (memory); last artefacts in `C:/Users/davidt/Downloads/e4r/data/taller/`
(`fichas.jsonl`, `embeddings/`, `eval-2026-10-09.json`) — `data/taller/` is git-ignored and absent from e6f. Gold ids
are local ids (`referencia:graduacion-columnas-uvas~columna-organica`).

Pricing (REQ-007 Phase 2, D-024, D-026) is **latex-balloon only**: `motor/bom.ts` `bomDeEscena` sums
`{formatoId, codigo, cantidad}`; `motor/crosswalk-variantes.ts` maps `claveCruce = "formatoId|codigo"` →
`{productId, variantes[{variantId, unidadesPaq, precio}]}` (snapshot `motor/datos/crosswalk-vigente.json`: 653 pairs,
39 `sinCobertura`; generator `scripts/motor/generar-crosswalk.ts`; live `crosswalk-consulta.ts`, 10 min TTL);
`plan-de-compra.ts` `planearCompra(…, "python")` picks packages; `cotizar-bom.ts` `cotizarBom` sends variant ids to
the Python `lista-materiales` price service. The motor has no utilería/escenografía/mobiliario kind; `productos-tienda.ts`
(216 balloon products) is a URL/verification list, not a price source. In the Taller shopping list (`productosDe`,
`biblioteca.ts:596`) furniture and backdrops come out as unpriced `LineaEscenografia` lines and shop props as links.

Persistence: scenes live in localStorage (`taller3d:escena:v1`, `VERSION_GUARDADO = 2`, loaded by `leerGuardada`,
`src/components/tres-d/guardado-escena.ts:28`), owner items in `taller3d:biblioteca-propia:v1` (`validarItem`),
conversations in `taller3d:conversacion:v1`; scene JSON reaches Neon only inside `ai_feedback` rows. Nodes carry no
library-origin field; the only catalogue reference inside a scene is `pieza.mueble.id` (free string; an unknown id
renders a placeholder, `mobiliario-pieza.ts:109`). Server-side validation: `EscenaSchema` → `MuebleDePiezaSchema`.

Flags: `featureEnabled(name)` (`src/lib/ia/nucleo/feature-flags.ts:68`, reads `process.env` per call); runtime rows in
`ajustes_runtime` (032) are read only by `src/lib/guiada-motor/bandera.ts` (`crearLectorBandera`, TTL 30 s).

### 1.2 Problems

1. **No boundary.** Sempertex brand content (ideas, Celebra, shop props, formats/colours) and in-house parametric
   furniture/backdrops share registries, id spaces and code paths; adding a furniture rental list or a third-party
   pack has no home, no provenance and no licence record.
2. **One registry, two natures.** `FONDOS_CATALOGO` mixes rentable furniture (tables, chairs, lounges) with scenery
   (panels, curtains, pedestals, cakes). They will be priced, sourced and shown differently.
3. **No pricing source per origin.** Sempertex prices come from the shop crosswalk; furniture would come from a rental
   list (does not exist yet); scenery has no price. Today the distinction is implicit (`tipo === "escenografia"`).
4. **No scope per surface.** The customer surfaces (guided chat, module studio) must only see Sempertex; today this
   holds only because their code happens not to import furniture (no guard, no flag).
5. **RAG cannot partition.** A future furniture index would be mixed into library searches with no hard filter.

### 1.3 Forces / constraints

- Zero behaviour change while migrating: `test-armado-escena-dorado` 0 diffs, RAG eval acierto@5 must not drop.
- D-001: importing the library must stay lazy (`test-carga-3d` < 500 ms). D-010: code is the source of truth for
  factory items; the DB is an index. D-013: no orphan properties. D-017: no module-level GPU caches (unaffected).
- `test-esquema-gemini`: scene-tool declarations ≤ 122 880 B (comment: ~112 KB today), ≤ 170 enum values in total
  (162 today → **8 left**), ≤ 46 tools (42 today), photo-reading schema ≤ 22 528 B. `MuebleDePiezaSchema.id` ≤ 60.
- The guided motor import closure is policed by `scripts/test/test-motor-guiada-fronteras.ts` (only `motor/v1` from
  outside; `globos3d/biblioteca.ts` and `ideas-sempertex/` forbidden) and `test-motor3d-frontera.ts` (browser side).
- Hard rules (brief §2): migrations additive/idempotent, next free number 033, dry-run then `--allow-remote`;
  risky things behind a flag default off; never flip `GUIADA_MOTOR`; no customer-visible pricing change without the
  owner; TypeScript without `any`; files ≤ 500 lines (`biblioteca.ts` is already 1 075 — do not grow it).
- Stored data that must keep loading: localStorage scenes and owner items, scene JSON inside `ai_feedback`, hand-read
  photo readings (`referencias-dueno.ts` uses fondo ids), salon zones (`salon-evento.ts:208` `mueble: "silla_tiffany"`),
  eval gold sets, `src/lib/taller/datos/clasificacion-biblioteca.json` and render manifests (keyed by item id), the
  vector cache (keyed by id + `hash_entrada`).

---

## 2. Decision

Introduce **catalogue repositories** as a first-class, code-defined boundary in a new feature module
`src/lib/catalogo/`. A repository is *a source of catalogue entries with one owner, one licence regime, one price
source and one visibility policy*. The geometry engine (`globos3d`: piece model, `armarPieza`, scenery primitives,
furniture builders) stays shared and repository-agnostic; repositories own **entries** (data, defaults,
descriptions, provenance, price source), not geometry.

Founding repositories:

| id | Contains | Price source | Default visibility |
|---|---|---|---|
| `sempertex` | the whole factory library (ideas, Celebra, predefined decorations, utilería, organic bases, owner references, preset scenes) and their derived items; balloon formats & colour table; shop props; guided-chat library (`planes-ideas.json`, `detalles-ideas.json`, `decoraciones.json`); module types | `crosswalk-tienda` (existing crosswalk + Python price service for latex; shop props/impresos/metalizados stay link-only) | every surface |
| `mobiliario` | `FONDOS_CATALOGO` entries with `grupo` `asiento` or `mesa` (26, incl. `mesa_mantel` and the 3 fixed table+chairs presets and `sala_lounge`) + generators `mesa_param`, `sillas_param` | `sin-precio` now; `lista-alquiler` when a rental list exists (flag) | Taller, scene AI, photo reading |
| `escenografia` | `FONDOS_CATALOGO` entries with `grupo` `fondo`/none or `decorado` (25: panels, media luna, chiara arches, sequins, rug/tapete, curtains incl. `cortina_flecos`, sign, pedestals, `base_hexagonal`, `columna_griega`, steps, metal hoops/arches, frames, screen, neon, acrylic name, pampas vase, floor lamp, `base_pastel`, `pastel`) | `sin-precio` | Taller, scene AI, photo reading |
| `terceros/<slug>` (future) | data-only packs (JSON), referencing existing engine families | declared in its manifest (mandatory) | none until enabled |

Key rulings (each one argued in §3):

- **R1 Ids.** A **qualified id** `<repo>:<localId>` is the canonical public handle; the **local id is today's id,
  frozen** (`sempertex:idea:<slug>`, `mobiliario:silla_tiffany`, `escenografia:panel_redondo`,
  `sempertex:escena:x~n3`). Un-namespaced ids stay valid forever and resolve through the registry (§5). No stored
  id, DB key, hash or file is rewritten.
- **R2 Repository assignment** is a pure, exhaustive function of the entry's source (library → `sempertex`;
  `FONDOS_CATALOGO` by `grupo`; generators → `mobiliario`). Derived items inherit their parent scene's repository.
  Owner-saved items get the repository of their content (any balloon piece → `sempertex`; furniture/scenery only →
  the repository of their `mueble.id`). An unassigned entry fails CI.
- **R3 Views first, moves later.** Phase 1 builds repositories as *views* over the existing modules, preserving
  every existing order (the photo prompt and `z.enum` order are behaviour). Physical relocation of source files is
  out of scope (Proposal P-1).
- **R4 RAG partition = column + hard filter**, not separate tables: `taller_items.repositorio` (migration 033),
  `repositorio = ANY(visible)` in `condicionesDuras`, same in the in-memory fallback.
- **R5 Price source is a port per repository**; a quote groups lines by repository and never shows a `sin-precio`
  line as 0.
- **R6 Visibility is a matrix repository × surface**, resolved server-side (runtime row → env → manifest default);
  customer surfaces (`guiada`, `estudio`) cannot see a `sin-precio` repository unless explicitly permitted.
- **R7 Generated data per repository** under `data/catalogos/<repo>/`; `sempertex` keeps `data/taller/` (declared in
  its manifest) so nothing is re-embedded.
- **R8 Layering.** `src/lib/catalogo/{ids,tipos}.ts` are leaf modules (no imports from `globos3d`); the
  repositories, registry and visibility modules import `globos3d`, **never the reverse**. The engine may import only
  the leaf modules (to accept qualified ids). This keeps the registry — and through it `globos3d/biblioteca.ts` —
  out of the guided-motor and studio closures (`test-motor-guiada-fronteras`).

---

## 3. Options considered

### 3.1 Partitioning model
| Option | Verdict |
|---|---|
| A. Status quo + more tags (`fuente`, `grupo` filters) | Rejected: no owner/licence/price boundary, no place for third-party packs, customer scope still accidental. |
| B. One table per repository (`sempertex_items`, `mobiliario_items`…) | Rejected: duplicates the hybrid SQL and RRF across tables, one migration per new pack, cross-repo search needs UNION. |
| C. Postgres `PARTITION BY LIST (repositorio)` | Rejected now: needs a table rebuild (not additive), PK/FK churn for 3 k rows that do not need it. Kept as escape hatch. |
| D. Separate Neon schema/database per repository | Rejected: the pool of 20 is shared with the product RAG; ops cost with no benefit at this size. |
| **E. Logical partition: `repositorio` column + index + hard filter, repositories as code modules** | **Chosen.** Additive, one SQL, per-repo filter in one place, trivially reversible. |

### 3.2 Id scheme
| Option | Verdict |
|---|---|
| i. Rewrite every id to the qualified form (DB, files, scenes) | Rejected: PK rewrite is not additive; `huellaDe` hashes the id (`fichas.ts:46`) so all 3 217 rows would "change"; embeddings are keyed by item id (re-upload or paid re-embed); every stored scene, reading, gold set and classification file would need a migration — all for no user value. |
| ii. Composite key `(repositorio, id_local)` | Rejected: changing the PK is not additive; same consumer churn. |
| **iii. Qualified handle over frozen local ids** | **Chosen.** Zero rewrite; collision-free by construction for the founding repos (library ids are prefixed, furniture ids are unique in one map today) and enforced for future packs (§5.3). |

### 3.3 Where repository code lives
| Option | Verdict |
|---|---|
| Move ideas lots, furniture builders and data files into per-repo folders now | Rejected for this REQ: ~10 k lines of engine-coupled code; breaks every import and the D-001 lazy pattern; high merge cost against parallel branches. |
| **Views + adapters in `src/lib/catalogo/`, relocation later per file** | **Chosen** (R3). |

### 3.4 Visibility control
| Option | Verdict |
|---|---|
| Only env flags | Rejected alone: needs a redeploy to react. |
| **`ajustes_runtime` (032) row → env var → manifest default** | **Chosen**: same pattern as `guiada_motor` (D-024), instant rollback. |

---

## 4. Schema

### 4.1 Types (`src/lib/catalogo/tipos.ts`)

```ts
export type IdRepositorioFundador = "sempertex" | "mobiliario" | "escenografia";
export type IdRepositorio = IdRepositorioFundador | `terceros/${string}`;     // slug: ^[a-z0-9][a-z0-9-]{1,23}$
export type Superficie = "taller" | "ia_taller" | "foto" | "rag" | "estudio" | "guiada";

export type Licencia = {
  regimen: "propia" | "marca-socio" | "referencia" | "cc-by" | "cc0" | "comercial";
  titular: string;                 // "Sempertex", "Equipo demo-decoracion", supplier name
  url?: string;
  atribucion?: string;             // text to show when the entry is rendered/exported
  restricciones: string[];         // e.g. "imágenes solo por url pública, nunca copiadas al repo"
};

export type FuentePrecioDeclarada =
  | { tipo: "crosswalk-tienda" }                                   // sempertex
  | { tipo: "lista-alquiler"; archivo: string; moneda: "COP" | "USD"; vigencia: string }
  | { tipo: "sin-precio"; motivo: string };

export type ManifiestoRepositorio = {
  esquema: 1;                      // manifest schema version
  id: IdRepositorio;
  version: string;                 // semver of the CONTENT; bumped when the content hash changes (lock test)
  nombre: string;                  // UI label: "Sempertex", "Mobiliario", "Escenografía"
  descripcion: string;
  clases: readonly ClaseEntrada[]; // kinds it may hold (§4.2)
  licencia: Licencia;              // default for its entries; an entry may override (provenance)
  precio: FuentePrecioDeclarada;
  visiblePorDefecto: readonly Superficie[];
  depende: readonly IdRepositorio[];      // sempertex scenes place escenografia/mobiliario pieces
  idsLocales: { prefijos: readonly string[] } | { exactos: "del-cargador" };  // ownership claims for resolution
  datos: string;                   // generated-data folder: "data/taller" (sempertex, legacy) | "data/catalogos/<id>"
};

export type Procedencia = {
  fuente: "idea-sempertex" | "celebra" | "tienda-sempertex" | "referencia-web" | "referencia-dueno" | "propio" | "terceros";
  titulo: string; url?: string; fotoUrl?: string;
  licencia?: Licencia;             // only when it differs from the manifest's
};

export type EntradaCatalogo<C extends ClaseEntrada = ClaseEntrada> = {
  id: string;                      // qualified: `${repositorio}:${idLocal}`
  idLocal: string;                 // frozen legacy id
  repositorio: IdRepositorio;
  clase: C;
  nombre: string;
  descripcion: string;
  procedencia: Procedencia;
  dato: DatoDeClase[C];            // kind payload, built lazily (getter, D-001)
};
```

`Repositorio` (the loader contract, `src/lib/catalogo/repositorio.ts`):

```ts
export type Repositorio = {
  manifiesto: ManifiestoRepositorio;
  /** Lazy: no entry content is built at import (D-001). Order = today's order (R3). */
  entradas(): readonly EntradaCatalogo[];
  porIdLocal(idLocal: string): EntradaCatalogo | undefined;
  /** Searchable records for the RAG (fichas); `sempertex` delegates to `fichaDeItem`. */
  registrosParaIndice(opciones: OpcionesFicha): Iterable<RegistroTaller>;
  precio: FuentePrecio;            // runtime port (§8)
};
```

The registry (`src/lib/catalogo/registro.ts`) holds the three founding repositories as lazy getters
(`perezoso`), plus `terceros/*` loaded from `data/catalogos/terceros/<slug>/` only when `CATALOGO_TERCEROS` is on.
Importing `src/lib/catalogo` must not import `ideas-sempertex/*` or build any entry (`test-carga-3d`).

### 4.2 Item schema per kind (`ClaseEntrada`, zod-validated, discriminated on `clase`)

| Repository | `clase` | `dato` | Source adapter |
|---|---|---|---|
| sempertex | `item-biblioteca` | `ItemBiblioteca` (`tipo` escena/conjunto/estructura/decoracion/utileria — unchanged) | `BIBLIOTECA_FABRICA`, `indexarEscena` |
| sempertex | `formato` | `FORMATOS_GLOBO` record | `formatos.ts` |
| sempertex | `color` | `ReferenciaSchema` record (`codigo`, `familia`, `hexGlobo`, `formatos[]`) | `contracts/domain/v1/sempertex/tabla-color.json` via `referencia-sempertex.ts` |
| sempertex | `producto-tienda` | `CATALOGO_UTILERIA` entry (shop url, temática; no price) | `utileria-catalogo.ts` |
| sempertex | `plan-idea` | the `planes-ideas.json` record (+ `detalles-ideas.json` detail) | `biblioteca-sempertex/`, `plan/planes-ideas-guardados.ts` |
| sempertex | `decoracion-guiada` | `DecoracionSempertexSchema` record (`decoraciones.json`) | `biblioteca-sempertex/biblioteca.ts` |
| sempertex | `modulo` | `{ tipo: TipoModulo, simetrias }` | `modulos.ts` (studio, REQ-011) |
| mobiliario | `mueble` | `MuebleCatalogo` (grupo `asiento`/`mesa`) | `CATALOGO_MOBILIARIO` |
| mobiliario | `mueble-fijo` | `FondoFijo` (`mesa_mantel`) | `FONDOS_BASE` |
| mobiliario | `generador` | `{ id: "mesa_param" \| "sillas_param", tipos: TIPOS_MESA \| TIPOS_SILLA, limites }` | `mobiliario-conjunto-tipos.ts` |
| escenografia | `fondo` | `FondoFijo` | `FONDOS_BASE` |
| escenografia | `decorado` | `MuebleCatalogo` (grupo `decorado`) | `CATALOGO_MOBILIARIO` |
| terceros/* | `mueble-ref` / `fondo-ref` | `{ base: <qualified id of a mobiliario/escenografia entry>, medidas, colores, precio?, fotoUrl? }` — data only, never code | `data/catalogos/terceros/<slug>/entradas.jsonl` |

Every kind has a zod schema in `src/lib/catalogo/esquemas.ts`; the founding adapters are checked against them in a
test (not at runtime, to keep imports cheap); `terceros` entries are validated at load and rejected with a reason.

### 4.3 Manifests (`src/lib/catalogo/repositorios/<id>/manifiesto.ts`)

- `sempertex`: licence `marca-socio`, titular Sempertex, restrictions "photos only by public https url, never copied
  into the repo; shop links point to sempertex shop". Item-level provenance keeps today's `FuenteItem.tipo`
  (`referencia-web` and `referencia-dueno` items carry licence `referencia`: geometry re-created, image not stored).
  `idsLocales.prefijos = ["idea:", "celebra:", "decoracion:", "utileria:", "base-organica:", "referencia:", "escena:"]`;
  `datos: "data/taller"`; `depende: ["escenografia", "mobiliario"]` (owner-reference scenes compiled by
  `compilar-lectura.ts` place catalogue backdrops/furniture; inline scenery inside idea lots — 108 pieces without
  `mueble` — belongs to the idea itself).
- `mobiliario` / `escenografia`: licence `propia` (in-house parametric models; `rotulo_acrilico`/`neon_cursiva` render
  with the bundled Great Vibes font, OFL 1.1 — D-018 — recorded as attribution). `idsLocales.exactos = "del-cargador"`.
- Lock file `src/lib/catalogo/repositorios.lock.json`: `{ id, version, huella }` per repository, where `huella` =
  sha256 of the ordered `(idLocal, claveContenido-or-entry-JSON)` list. `test-catalogo-repositorios` fails when the
  hash changes and the version does not (forces a deliberate version bump + changelog line in the manifest).

---

## 5. Id scheme

### 5.1 Grammar
```
IdCalificado := IdRepositorio ":" IdLocal
IdRepositorio := "sempertex" | "mobiliario" | "escenografia" | "terceros/" slug
IdLocal      := today's id, unchanged (may contain ":" and "~": "idea:arco-x", "escena:boda~n3")
```
Parsing (`src/lib/catalogo/ids.ts`): split at the first `:`; if the head is a registered repository id the rest is
the local id; otherwise the whole string is a local id (legacy/short form) and is resolved by the registry's
**local-id index** (`Map<idLocal, IdRepositorio>` built lazily from prefixes + exact ids). No founding local id
starts with `sempertex:`, `mobiliario:`, `escenografia:` or `terceros/` (verified on b4433bc9; asserted by test).

API:
```ts
parsearId(s): { repositorio: IdRepositorio; idLocal: string; forma: "calificada" | "corta" } | { error: "desconocido" | "ambiguo" }
calificar(idLocal): string             // throws on unknown in tests, returns undefined at runtime
resolverEntrada(s): EntradaCatalogo | undefined   // accepts both forms
```
Derived ids resolve through their prefix (`escena:x~n3` → `escena:` → sempertex). Owner items (`propio`) are not
claimed by any prefix: they resolve to `sempertex` for visibility unless their content says otherwise (R2).

### 5.2 Where each form is used
- **Short (local) form stays the storage form** for every founding entry: `pieza.mueble.id`, `LecturaFoto` fondo
  ids, salon zones (`mueble: "silla_tiffany"`), `taller_items.id`, fichas, vector cache, gold sets, classification
  JSON, render manifests, localStorage. The piece type already scopes these ids.
- **Qualified form** is emitted (behind `CATALOGO_IDS_CALIFICADOS`) at catalogue boundaries: `/api/taller/buscar`
  results (`id` stays local; new field `idCalificado`), AI tool results (`buscar_en_biblioteca`, catalogue listings),
  «Añadir» keys, telemetry/feedback records. Every reader accepts both forms.
- **`terceros/*` entries are always referenced qualified**, including inside pieces
  (`mueble.id = "terceros/acme:silla-x"`, ≤ 60 chars: slug ≤ 24, local ≤ 34).

### 5.3 Collision rules
1. The local-id index must be injective: a test builds it over all repositories and fails on any duplicate or on a
   local id claimed by two prefixes.
2. A `terceros` pack's local ids may not collide with any founding local id (validated at load; the pack is refused
   with the list of conflicts). Because terceros are always used qualified, they never enter the short-form index.

---

## 6. Migration of existing data (zero behaviour change)

### 6.1 Code data (Phase 1 — views, no moves)
| Today | → Repository | How |
|---|---|---|
| `BIBLIOTECA_FABRICA` (557) + derived | `sempertex` / `item-biblioteca` | adapter over the same array, same order, same lazy getters |
| `formatos.ts`, colour table | `sempertex` / `formato`, `color` | adapter |
| `CATALOGO_UTILERIA` (620) | `sempertex` / `producto-tienda` | adapter |
| `planes-ideas.json`, `detalles-ideas.json`, `decoraciones.json` | `sempertex` / `plan-idea`, `decoracion-guiada` | adapter for the registry; the guided chat keeps its current direct imports (it is Sempertex-only by construction) |
| `modulos.ts` | `sempertex` / `modulo` | adapter (studio) |
| `FONDOS_CATALOGO` grupo `asiento`/`mesa` (26) + `mesa_param`/`sillas_param` | `mobiliario` | filter view; explicit table `ASIGNACION_FONDOS` (id → repo) checked exhaustively |
| `FONDOS_CATALOGO` grupo none/`decorado` (25) | `escenografia` | same |

`FONDOS_CATALOGO` keeps its exact order and stays the source for `lectura-foto.ts`/`prompt-lectura-foto.ts` in
Phase 1 (their output must be byte-identical: snapshot hash test). `entradaDeCatalogo(id)` additionally accepts the
qualified form (additive). Nothing else changes.

### 6.2 Database (Phase 2 — migration `033_catalogo_repositorios.sql`)
```sql
-- REQ-013: partición lógica de la biblioteca por repositorio de catálogo. Aditiva e idempotente.
-- Todas las filas existentes vienen de la biblioteca de fábrica o de dueños → 'sempertex' (regla R2).
-- rollback: (después de revertir el código que filtra) ALTER TABLE taller_items DROP COLUMN IF EXISTS repositorio;
ALTER TABLE taller_items ADD COLUMN IF NOT EXISTS repositorio TEXT NOT NULL DEFAULT 'sempertex';
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'taller_items_repositorio_check') THEN
    ALTER TABLE taller_items ADD CONSTRAINT taller_items_repositorio_check
      CHECK (repositorio ~ '^(sempertex|mobiliario|escenografia|terceros/[a-z0-9][a-z0-9-]{1,23})$');
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS ix_taller_items_repositorio ON taller_items (repositorio, activo, tipo);
```
`ADD COLUMN … DEFAULT <constant>` is metadata-only (no rewrite) on PG ≥ 11. No PK, hash, embedding or id changes.

Indexer: `RegistroParaIndice.repositorio` (from the registry), `COLUMNAS_ITEM` gains `repositorio`, the upsert's
`WHERE` becomes `hash IS DISTINCT FROM … OR repositorio IS DISTINCT FROM EXCLUDED.repositorio OR NOT activo`,
`construirConsultaHashes` and `construirDesactivarAusentes` are scoped per repository (`WHERE propietario IS NULL
AND repositorio = $1`), so indexing `mobiliario` never deactivates `sempertex` rows. `repositorio` is **not** part of
`huellaDe` (no re-embedding).

### 6.3 Generated data
`sempertex` keeps `data/taller/{fichas.jsonl, embeddings/, renders/}`. New repositories write
`data/catalogos/<id>/{fichas.jsonl, embeddings/}` (git-ignored like today). The Python batch
(`services/ai-api/app/taller/embeber_biblioteca.py`) takes the folder as an argument already (`--fichas`); no
Python change beyond documentation.

### 6.4 New content (Phase 3)
Fichas for the 28 `mobiliario` + 25 `escenografia` entries (Spanish text from name, description, colours-de,
measures, seats, synonyms in `fondos-sinonimos.ts`), embedded once (~53 × 300 tokens; cap US$0.05, logged) and
indexed with their repository. They stay invisible while the `rag` visibility is `sempertex` only.

---

## 7. Feature flags

Resolved server-side by `src/lib/catalogo/visibilidad.ts` → `reposVisibles(superficie)`: `ajustes_runtime` row
`catalogo_repos_<superficie>` → env `CATALOGO_REPOS_<SUPERFICIE>` (comma list) → manifest `visiblePorDefecto`.
Unknown ids are ignored and logged. The 30 s runtime reader is extracted from `guiada-motor/bandera.ts`
(`crearLectorBandera`/`leerAjusteNeon`) into a shared `src/lib/ajustes/ajustes-runtime.ts` (pure refactor; the guided
flag keeps its precedence, `test-guiada-motor-bandera` gate). Boolean flags join the `FeatureFlag` union in
`feature-flags.ts` (default off). The Taller is a client page, so it reads its visibility and the repository
manifests from `GET /api/catalogo/repositorios` (`{ repositorios: [{ id, nombre, version, licencia, precio, visible }],
ui: boolean }`), never from `NEXT_PUBLIC_*` (switchable without a rebuild).

| Flag / setting | Default (= today) | Effect |
|---|---|---|
| `CATALOGO_REPOS_TALLER` | sempertex,mobiliario,escenografia | what «Añadir» / Library list |
| `CATALOGO_REPOS_IA_TALLER` | sempertex,mobiliario,escenografia | which repos the scene AI tools may read; a hidden repo's tools are not declared |
| `CATALOGO_REPOS_FOTO` | sempertex,mobiliario,escenografia | photo reading vocabulary |
| `CATALOGO_REPOS_RAG` | sempertex | hard filter of every RAG query (route, tools, photo search) |
| `CATALOGO_REPOS_ESTUDIO` | sempertex | `/3d/modulos` |
| `CATALOGO_REPOS_GUIADA` | sempertex | guided customer chat (any catalogue access) |
| `CATALOGO_UI_REPOSITORIOS` | off | «Añadir» grouped by repository (tabs) |
| `CATALOGO_FILTRO_IA` | off | `repositorio` parameter in AI catalogue tools |
| `CATALOGO_IDS_CALIFICADOS` | off | emit qualified ids at boundaries (§5.2) |
| `CATALOGO_PRECIO_ALQUILER` | off | `mobiliario` priced from its rental list |
| `CATALOGO_TERCEROS` | off | load `terceros/*` packs |

Safety rule: `reposVisibles("guiada" | "estudio")` drops any repository whose price source is `sin-precio` unless
`CATALOGO_PERMITIR_SIN_PRECIO_CLIENTE=true` (owner decision; a customer never sees an unpriceable item).

---

## 8. Pricing per repository

Port (`src/lib/catalogo/precio.ts`):
```ts
export type LineaACotizar = { repositorio: IdRepositorio; idLocal: string; cantidad: number; detalle: unknown };
export type LineaCotizada = LineaACotizar & ({ estado: "con-precio"; precio: Dinero; fuente: string } | { estado: "sin-precio"; motivo: string } | { estado: "sin-cobertura"; motivo: string });
export type FuentePrecio = { cotizar(lineas: readonly LineaACotizar[]): Promise<LineaCotizada[]> };
```
- `sempertex` → adapter over the existing path (`bomDeEscena` → `planearCompra` with `crosswalk-variantes` →
  `cotizarBom` → Python `lista-materiales`, D-026 presentations), byte-identical results. Pairs in `sinCobertura`
  map to `sin-cobertura`. Shop props, impresos and metalizados stay link-only lines (`sin-precio`, with url) exactly as
  today — pricing them is a separate owner decision.
- `escenografia` → `sin-precio` ("escenografía del montaje: no se vende").
- `mobiliario` → `sin-precio` until a rental list exists; with `CATALOGO_PRECIO_ALQUILER` → `lista-alquiler` reading
  `data/catalogos/mobiliario/precios-alquiler-<vigencia>.json` (`{ idLocal | generator type → precio por unidad/día }`),
  never inventing a price for an id not in the list (`sin-cobertura`).
- The Taller shopping list (`productosDe`) splits today's `escenografia` lines by repository (behind
  `CATALOGO_UI_REPOSITORIOS`); the guided quote is unchanged (it only sees `sempertex`).
- No customer-visible pricing change ships without the owner (brief §2).

---

## 9. Surfaces

- **Taller «Añadir»** (flag `CATALOGO_UI_REPOSITORIOS`, `PanelAnadir.tsx`): a repository switcher above the tabs.
  *Sempertex* = today's Estructuras · Decoraciones · Utilería de fiesta (`UtileriaFiesta`) · Ideas, with the library
  grid; *Mobiliario* = `FondosYMuebles` groups asiento + mesa + «Mesa con sillas a medida»; *Escenografía* =
  `FondosYMuebles` groups fondo + decorado; *Terceros* when enabled. Search scoped to the selected repository or
  "Todos"; counts per repository; provenance/licence line in the item detail. `FondosYMuebles` gains a `repositorio`
  prop (filter by the registry assignment, order unchanged). Off = today's 4 tabs, byte-identical render.
- **Scene AI** (flag `CATALOGO_FILTRO_IA`): `buscar_en_biblioteca` gets an optional `repositorio` parameter declared
  as a **string** whose description lists the visible ids (validated server-side by `parsearRepositorio`), not an
  enum: the enum budget has 8 values left (`test-esquema-gemini`). `insertar_de_biblioteca` accepts both id forms.
  `agregar_mobiliario`'s `z.enum` is built from `reposVisibles("ia_taller")` (same order; unchanged with defaults);
  hiding both furniture repositories removes `agregar_mobiliario` and the table tools from the declaration.
  Budget: ≤ 1 024 B and 0 enum values added; total ≤ 122 880 B; with flags off the declarations are byte-identical.
- **Photo reading**: unchanged vocabulary by default; `reposVisibles("foto")` filters the `FONDOS_CATALOGO` list
  only when a repository is hidden (order preserved; reading schema ≤ 22 528 B).
- **Studio `/3d/modulos` and guided chat** read only `sempertex`. Their own code never lists furniture today; the
  engine reaches `FONDOS_CATALOGO` transitively (to *build* a stored `mueble.id`), which is acceptable. Enforcement:
  (a) static — extend `test-motor-guiada-fronteras` and add a studio twin: the closures of `motor/v1`,
  `src/app/api/asistente-guiado`, `src/app/api/guiada/**`, `src/lib/guiada-motor/**`, `src/lib/ia/guiado/**`,
  `src/components/guiado/**`, `src/app/3d/modulos/**`, `src/lib/modulos-estudio/**` must not contain
  `src/lib/catalogo/registro.ts` or `src/lib/catalogo/repositorios/**` (R8), and their *direct* imports must not include
  `mobiliario-catalogo.ts`/`fondos-escenografia.ts`; (b) output — a property test over the guided goldens asserts
  that no produced scene contains a piece whose `mueble.id` resolves outside the surface's visible repositories
  (inline scenery without `mueble`, e.g. the 108 bottles/weights/props drawn inside Sempertex idea lots, is part of
  the Sempertex entry and allowed); (c) runtime — any future catalogue listing from these surfaces goes through
  `catalogoPara("guiada" | "estudio")`.

---

## 10. Consequences

\+ One place answers "where does this come from, who owns it, may we show it, how is it priced".
\+ Furniture can get a rental price list and its own RAG rows without touching Sempertex data or the customer chat.
\+ Third-party packs become data drops with a mandatory licence instead of code changes.
\+ Customer scope becomes a guarded invariant instead of an accident.
− Two id forms coexist forever (short for storage, qualified at boundaries); readers must use `parsearId`.
− `FONDOS_CATALOGO` order is now a contract (prompt/enum byte identity) until those consumers read per repository.
− One more hard filter in every RAG query; small repositories may starve the HNSW vector branch (§12, R-2).
− Library code stays physically inside `globos3d` for now (R3); the separation is logical until P-1.

---

## 11. Acceptance criteria

- **AC-1** `test-armado-escena-dorado` (405 scenes, 6 586 nodes, fixture `scripts/test/dorado/armado-escena.json`)
  reports 0 diffs after every phase, and a new catalogue golden (every `FONDOS_CATALOGO` entry built with its
  defaults + the two generators with their presets) reports 0 diffs — the scene golden does not cover catalogue-only
  furniture.
- **AC-2** RAG eval acierto@5 ≥ the baseline measured at the start of Phase 2 (97.5 % on b4433bc9) and MRR does not
  drop by more than 0.01, with default flags, on PGlite and on Neon.
- **AC-3** `test-carga-3d` stays < 500 ms; importing `src/lib/catalogo` builds no entry.
- **AC-4** `test-esquema-gemini` green: declarations ≤ 122 880 B, enum values ≤ 170, tools ≤ 46, reading schema
  ≤ 22 528 B; REQ-013 adds ≤ 1 024 B and 0 enum values; with flags off the declarations and the photo prompt are
  byte-identical to b4433bc9 (sha256 snapshot).
- **AC-5** Every `BIBLIOTECA_FABRICA` item, every derived item and every `FONDOS_CATALOGO` entry belongs to exactly one
  repository (exhaustive test); expected counts: escenografia 25, mobiliario 26 + 2 generators, sempertex 557 factory.
- **AC-6** For 100 % of entries `resolverEntrada(idLocal) === resolverEntrada(idCalificado)`; the local-id index is
  injective; a corpus of stored scenes (golden fixture, `referencias-dueno` readings, saved owner items sample, scene
  JSON from AI feedback rows) loads and builds with 0 diffs.
- **AC-7** Migration 033 runs twice without error or change; dry-run clean; every existing row has `repositorio =
  'sempertex'`; rollback statement documented and tested on PGlite.
- **AC-8** With `CATALOGO_REPOS_RAG=sempertex,mobiliario`, a filtered query returns only that repository's rows and
  the vector branch returns ≥ min(k, rows) candidates for a 28-row repository.
- **AC-9** Default flags: the guided and studio closures contain neither the registry nor any repository module, and
  their direct imports include no furniture catalogue (§9); guided goldens produce no piece with a non-Sempertex
  `mueble.id`;
  `reposVisibles("guiada")` = `["sempertex"]`; a `sin-precio` repository cannot be made visible to `guiada`/`estudio`
  without the explicit permit.
- **AC-10** Sempertex priced golden fixtures (`test-motor-guiada-precio`, `generar-golden-precio`) unchanged; with
  `CATALOGO_PRECIO_ALQUILER` on, mobiliario lines are priced from the list or `sin-cobertura`, never 0.
- **AC-11** «Añadir» with the UI flag shows Sempertex / Mobiliario / Escenografía with the AC-5 counts and finds an
  item by name inside each; flag off = today's panel.
- **AC-12** The lock test fails when a repository's content hash changes without a version bump.
- **AC-13** A `terceros` pack without licence, with a colliding local id, or referencing an unknown base is refused
  with a reason; a valid pack appears only with `CATALOGO_TERCEROS` on.

---

## 12. Risks

| # | Risk | Mitigation |
|---|---|---|
| R-1 | **Ordering/leak at the RAG boundary**: if non-Sempertex rows are indexed before every reader filters by `repositorio`, furniture leaks into library search, the scene AI and the photo search; if the filtering code ships before 033 is on Neon, queries fail (`42703`) and silently fall back to memory. | Phase 2 order: apply 033 on Neon (dry-run, notice) → merge code with the always-on filter (default `sempertex`, results identical) → only then Phase 3 indexes new rows. A test asserts every SQL builder that reads `taller_items` includes the filter; the indexer refuses to write a non-sempertex row unless the deployed version supports it (`--permitir-otros-repos`). |
| R-2 | HNSW post-filter starvation for small repositories (28 rows among 9 k vectors). | AC-8 test; if starved, `SET LOCAL hnsw.ef_search` / `hnsw.iterative_scan` (check Neon's pgvector version) or a partial HNSW per repository (additive migration). |
| R-3 | Hidden behaviour change through order: `FONDOS_CATALOGO` order feeds the Gemini photo prompt and `z.enum`. | Byte-identity snapshot of the prompt text and of the tool declarations in Phase 1. |
| R-4 | Lazy-import regression (D-001) from a registry that touches heavy modules. | Registry entries are `perezoso` getters; `test-carga-3d` gate on every phase. |
| R-5 | Id ambiguity with future packs. | Qualified-only for `terceros`, injectivity test, load-time refusal. |
| R-6 | Orphan property (D-013): `repositorio` stored but not consumed, or manifest fields (`licencia`, `depende`) with no reader. | Consumer ledger: `repositorio` → search filter + UI; `licencia` → item detail + export; `depende` → validation that a scene's pieces belong to declared repositories; `version` → lock test + search response metadata. |
| R-7 | Parallel branches touching `biblioteca.ts`, `FONDOS_CATALOGO`, furniture tools (REQ-008/012 follow-ups, W2/W3). | Phase 1 adds files and touches existing ones minimally; rebase per phase; exhaustive assignment test catches new entries. |
| R-8 | Eval drift from new rows (Phase 3) if a surface sees them by mistake. | `rag` default `sempertex`; eval run with default flags is a gate of Phases 2–3. |
| R-9 | Gemini enum budget (8 values left) or tool count (4 left) exhausted by a naive `repositorio` enum or per-repo tools. | String parameter + server validation; no new tools; per-visibility pruning only removes declarations. |
| R-10 | The eval cannot run in a fresh worktree (`data/taller/` is git-ignored) and someone regenerates vectors (paid) to get it. | Copy `C:/Users/davidt/Downloads/e4r/data/taller/` (fichas, embeddings cache, eval-2026-10-09) into the worktree; regeneration of fichas is free, vectors come from the cache. |

---

## 13. Out of scope / Proposals
- P-1 Physical relocation of source modules into `src/lib/catalogo/repositorios/<id>/` (file by file, with re-export
  shims).
- P-2 Splitting owner Pinterest references and web organic bases into a `referencias` repository (licence
  `referencia`) — today they stay in `sempertex` with item-level provenance.
- P-3 A real rental price list for furniture (owner/supplier data needed).
- P-4 Moving owner-saved items from localStorage to `taller_items` (REQ-002 Q1, still pending).
- P-5 Dropping the orphan `taller_taxonomia` table (P-030).
- P-6 Invert the engine → furniture dependency (`escena.ts` → `mobiliario-pieza.ts` → `FONDOS_CATALOGO`): the engine
  resolves `mueble.id` through an injected port fed by the registry, so customer closures stop carrying furniture
  data at all.
- `proveedores.json` / `ciudades.ts` (supplier directory, example data) are not catalogue entries: out of scope.

## 14. Open owner questions (non-blocking; defaults taken, flag-gated)
1. Customer surfaces stay Sempertex-only — default yes (brief W6).
2. Cakes and pedestals are scenery (`escenografia`), tables/chairs/lounges are furniture (`mobiliario`) — default as
   the brief says.
3. Rental prices: currency and unit (per event / per day) — default COP per event, only when a list is provided.
