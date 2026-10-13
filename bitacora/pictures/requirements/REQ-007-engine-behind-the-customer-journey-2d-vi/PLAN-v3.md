---
id: REQ-007
status: draft v3. Written after mapping the code (repo at 7245991f, the same as main dca3aebd for the guided flow) under D-024.
  Next step: owner answers Q1–Q6, then Phase 0.
supersedes: PLAN.md v2 phases 4 (shadow gate) and 7 (row-by-row switch)
---
# REQ-007 — Plan v3: the guided chat moves to globos3d now (D-019, D-020, D-024)

## 0. Decisions this plan follows
- D-024: the guided chat moves to globos3d now. There is no per-structure parity gate. Safety comes from three things:
  the runtime flag `GUIADA_MOTOR=3d|python` (default `python` until the owner has tested), a one-off parity report that
  is information only, and golden BOM fixtures.
- D-019: two products. The engine stays hidden in the customer chat. The customer "2D" is the plan's 3D render, lightly
  modified.
- D-020: the customer can make AI requests and change colour references, colour proportions and size proportions. No
  drag, move, create or select in the viewer.
- D-024: pricing stays on the existing Python price service, which prices a given material list. Moving pricing off
  Python and migrating the classic chat are later items.

## 1. Current state: the guided flow end to end (file:line)

### 1.1 Conversation (`/api/asistente-guiado`)
- `src/app/api/asistente-guiado/route.ts` is a streamed Omoikane turn (`ejecutarConversacionStream`, l.534) with
  these tools:
  - brief, catalogue search, `proponer_composicion` (l.44, l.287–307)
  - options, steps, providers, `costear_decoracion` (l.348–376)
  - plan actions (l.53)
  - plan edit tools from `edicion-plan-chat.ts:110` (`HERRAMIENTAS_EDICION`: cambiar/agregar/quitar color,
    mas_o_menos_color, quitar_pieza, cambiar_tamano, agregar_pieza, colores_pieza, flores, editar_pieza)
- The route never builds a plan. It returns `datos.propuesta`, `datos.edicionPlan` or `datos.ideaElegida` in the SSE
  `fin` event (l.607), and the view builds the plan. The edit tool tells the model "Python vuelve a contar los globos"
  (l.236).
- `planActual` arrives as `PlanActualGuiadoSchema` (`src/lib/ia/contracts/asistente-guiado-v1.ts:51`). This is a
  lossy projection built by `planActualDesdePlan` (`src/lib/ia/guiado/instruccion-plan.ts:518`).

### 1.2 Decoration catalogue ("solo categorías reales")
- `bibliotecaVisible()` (`src/lib/biblioteca-sempertex/biblioteca.ts:333`) drops `origen:"ejemplo"`. That leaves 31 of
  46 entries in `decoraciones.json`, all `deco-real-*`.
- Where each decoration's plan comes from: a **stored plan**, `src/lib/biblioteca-sempertex/planes-ideas.json`. It is
  precomputed offline by `scripts/biblioteca/precomputar-planes-ideas.ts` from `data/biblioteca-real/analisis/*.plan.json`
  (schema `plan-de-idea.ts:23`). It is not a designer or armado route.
  - 28 of the 31 have a stored plan. Figures 21, 23 and 26 have none.
  - "Crear mi plan con esta idea" and "Agregar a mi plan" call `/api/plan-idea` → `planDesdeIdea`
    (`src/lib/plan/plan-desde-idea.ts:56`). That re-resolves the stored plan with Python `/plan/resolve`
    (`resolverPlan`, l.82) and signs it (`crearTokenPlan`, l.96).
- Structures in the stored plans:

  | Official id / type / size mix | Pieces |
  |---|---|
  | arco/clasica | 3 |
  | semiarco/organica_fina | 9 |
  | semiarco_asimetrico | 1 |
  | columna/clasica (3 with `armado_columna`) | 4 |
  | columna/organica_fina | 1 |
  | columna_asimetrica | 3 |
  | guirnalda/organica_fina | 7 |
  | guirnalda/clasica | 2 |
  | bouquet | 3 |
  | centro_mesa | 1 |
  | aro_circular (one `forma:parcial`, one `forma:organico` + `flores`) | 2 |

- Existing data mismatches:
  - 29 (Link-O-Loon arch + bouquet) is stored as two classic columns of 30 balloons.
  - 30 (column + figure) is stored as the column only.
  - 31 (arco_asimetrico) is stored as semiarco_asimetrico.
- The carousel `costear_decoracion` prices the decoration's **curated** `materiales` list directly (route l.364–365),
  not its plan.

### 1.3 Plan creation (three origins, all through Python)
1. **Proposal**: `aceptarPropuesta` (`VistaGuiada.tsx:1024`) → `ejecutarPlan` (l.808) → `pedirPlanChat` (l.2085) →
   **`/api/chat`**. That is the classic agent: RAG product choice, `confirmar_plan_decoracion`, Python resolve. It
   retries up to 2× (cases with 16 calls / ~65 s are on record, l.819).
2. **Catalogue idea**: `pedirPlanDeIdea` (`plan-exacto-idea.ts:34`, `VistaGuiada.tsx:1333`, l.1361) → `/api/plan-idea`.
3. **Photo**: `/api/references/analyze` (l.2106) → blueprint → `aceptarPlanFoto` (l.1071) → `/api/chat` with the
   photo.

Result: `PlanGuiadoSchema = BasePlanSchema` (`src/lib/plan/edicion-esquemas.ts:37`), i.e. `PlanDecoracion` plus
`plan_hash`, `approval_token`, `estructuras[].lineas` and `compras`. The view places it with `colocarPlan` (l.885).

### 1.4 Quantities, pricing, drawing, image, edits
- **Quantities**: Python `plan.py`. A piece with an `armado_*` is counted by its armado engine
  (`armado_arco.py`, `armado_*_organica.py`). Otherwise the formula applies (densidad × medidas, aro = π × d).
  `MERMA = 0.08` (`services/ai-api/app/merma.py`). `ARMADO_ARCO_COLUMNA_V1` is off (`feature-flags.ts`), so most guided
  plans are counted by formula.
- **Pricing of a given list**: yes. `llamarPythonListaMateriales` (`src/lib/ia/nucleo/python-adapter.ts:4092`) →
  `/internal/v1/plan/lista-materiales` → `cotizar_lista_materiales` (`plan.py:6887`). For each `(variant_id, cantidad)`
  it does closed packages, price and IVA, with **no merma**. It reads the published snapshot (`catalog.py:471`) and
  returns `material_no_disponible` (422) if any variant is missing. Contracts: `ListaMaterialesRequestSchema` and
  `ResultadoSchema` (`asistente-guiado-v1.ts:101–112`).
- **Plan "gráfica" (2D)**: `GraficaMotorGuiada.tsx:48` decides via `motorDePieza` (`motor-pieza.ts:85`):
  - an armado piece, or its recipe (`armado_*: null`), goes to `/api/plan-armado-{arco,arco-organico,columna,
    columna-organica,guirnalda-organica}` (`RUTA_MOTOR`, l.30). These are Python previews with SVG. They are capped at
    4 in flight per instance (`plan-armado-arco-organico/route.ts:55`).
  - pared, aro, techo and centro_mesa go to `/api/plan-dibujo-estructura` (`dibujo-estructura.ts:45`). This drawing is
    schematic and does not count.
  - bouquet and figura show an icon.
  - **Known defect**: the recipe drawing does not match what is counted (the formula), so "what is drawn ≠ what is
    charged".
- **FLUX image**: `verComoQuedaria` (`VistaGuiada.tsx:1166`) → `pedirImagenConRecuperacion`
  (`src/lib/generacion/pedir-imagen.ts`) → `/api/generate`, which runs:
  - Python re-resolve (`generate/route.ts:639`)
  - the Python disc "scene guide" `llamarPythonPlanGuiaEscena` (l.1099–1131)
  - FLUX `/edit`
  The image is stored **only** in IndexedDB (`imagenes-navegador.ts:7–9`, key = plan message id, 20 max).
- **Customer edits** (all Python, `/api/plan-editar`, modes at `route.ts:49–122`):
  - modes: `aplicar` with 14 `EdicionPlan` ops (`edicion-esquemas.ts:280`), `quitar_pieza`, `agregar_color`,
    `reemplazar_color`, `agregar_pieza`, `editar_pieza`, `buscar`, `colores`, `recomendadas`
  - the "Ajustar mi plan" panel produces `CambioPlan` (`ajuste-plan-guiado.ts:868`): protagonismo, cantidad, tamano,
    medidas, quitar/agregar/reemplazar color, tamano-todo, quitar-pieza
  - chat edits go through `ejecutarEdicionChat` (`edicion-chat-guiada.ts`, wired at `VistaGuiada.tsx:964–976`)
  - "Modificar esta pieza" (`ModificarPieza.tsx`) exposes the armado designer knobs. That is "pro" control and is out
    under D-020.

### 1.5 Client state
- `sessionStorage["demo_guiado_v2"]` = `{mensajes(last N), brief, seleccionadaId, uso}` (`VistaGuiada.tsx:137, 372,
  1997`). The plan, cotización, widget flags and `plan_hash`/`approval_token` live inside `mensajes[].widgets`.
- Business-price drafts are stored as `cotizacion-profesional:plan-<hash>`, `cotizacion-granel:plan-<hash>` and
  `…:guiado-<idea>` (`empezar-de-nuevo.ts:9–14`).
- IndexedDB `demo-decoracion-guiada/imagenes` (key = plan message id).
- "Approvals by hash" (`demo_generaciones_v1`, `src/lib/estado/persistencia-generacion.ts`) is **classic only**
  (`src/app/page.tsx`). The guided chat does not use it.

### 1.6 Shared with the classic chat
`/api/chat`, `/api/plan-editar`, `/api/plan-armado-*`, `/api/plan-dibujo-estructura`, `/api/generate` (same body via
`cuerpoGeneracion`), `src/lib/plan/*`, `VistaMotor`, and the Python resolver and engines. v3 adds new routes and
**changes none of these** for the classic chat.

## 2. The 3D engine side (what is reused)
- **Model**:
  - `Pieza` is a union of 17 kinds (`src/lib/globos3d/piezas.ts:37–110`); `armarPieza` is at l.153.
  - `Escena`/`NodoEscena` are at `escena.ts:96–98`.
  - `armarEscena` (l.432) is deterministic and seeded, with an optional per-piece cache (l.343–351).
- **BOM**: `EscenaArmada.materiales = MaterialDecoracion[] {formatoId, codigo, cantidad}` (`figuras.ts:108`), summed per
  node (`escena.ts:433–443`). The Taller shows it in `ListaCompra.tsx`. Products map to the shop by name and URL only
  (`productos-tienda.ts:34`). **There is no `variant_id` anywhere in globos3d.**
- **Server-side**: works. globos3d is pure TS; the only DOM file is `foto-cliente.ts`. `/api/escena-ia` already runs
  it on the server. Measured on this checkout (tsx, cold):

  | Piece | Balloons | Time |
  |---|---|---|
  | semiarco orgánico 1.5 × 2 m | 96 | 389 ms |
  | columna orgánica 1.8 m | 59 | 173 ms |
  | guirnalda orgánica 2.4 m | 94 | 139 ms |

  The aro failed: "verde salvia" is not resolvable by the Taller colour resolver.
- **Builders that guided pieces can use**:
  - `crearEstructura` (`herramientas-escena-estructuras.ts:430`): columna/guirnalda/semiarco/aro/marco orgánico with
    ranges at l.45–58, plus forma, letras, metalizado, mural, techo, árbol
  - classic `columna`/`arco` (quartets, `PatronTrenza` with 5 patterns / ≤4 colours, `trenza.ts:14`)
  - `arco_organico` (`formas-escena.ts:16`, has `densidad`), `guirnalda` (classic), `pared_malla`
  - decoration `flor` (balloon flower), `racimo` (`racimos-globos.ts`), `ramo_helio` (`halloween.ts:128`)
  - `techo` red with `anchoCm`/`fondoCm`
- **Plan → Escena converter: none exists.** `compilar-lectura.ts` converts photo readings, not plans. The Taller
  library (`biblioteca.ts`, `ideas-sempertex/*`) holds sempertex.com blog ideas, not the guided `deco-real-*` catalogue.
  `planActualDesdePlan` is a lossy plan → chat projection, not a scene.
- **Rendering**: `crearEscena` (`components/tres-d/escena-globos.ts:577`) needs three.js and WebGL.
  - It has `capturar()` (JPEG 1536 for FLUX) and `renderEstandar(vista, lado)`.
  - Drawing helper: `mostrarArmada` (`armada-visor.ts`).
  - Headless capture with viewer reuse: `CapturaRender.tsx`, where `RENDERS_POR_VISOR=40` recycles the viewer.
  - three.js itself is ~720 KB minified (core + module); the viewer is already lazy-loaded everywhere
    (`import("./escena-globos")`).
- **FLUX from the Taller**: `/api/render-3d-imagen` sends the capture as the `/edit` base. The prompt comes from
  `promptRender3d`/`promptRender3dFiel` (`render-ia.ts`) with an inventory built from `escenaEnIngles`/
  `descripcionRender3d`. Hourly cap: `TOPE_FOTOS_POR_HORA`.

## 3. Target architecture (v3)
- **`EspecClienteV1`** is the customer's source of truth: small, versioned and registered in `contracts/domain/v1`.
  - Proposals, ideas and edits all produce or modify a spec.
  - The engine turns spec → `Escena` → BOM.
  - Price = BOM + merma → variant crosswalk → `llamarPythonListaMateriales`.
  - An adapter outputs a `PlanGuiado`-compatible envelope, so the existing card, steps, buy and business-price
    components keep working.
- **The engine stays on the server** (`import "server-only"` in the facade). The client receives a **compact armada**
  (balloon positions, ~16 B each; a plan of ≤1 500 balloons is ≤30 KB) and only loads the lazy viewer chunk.
  - This keeps the engine hidden (D-019) and the client bundle small.
  - There is no client/server engine-version skew, because the client never re-arms.
- **Routing**: `GUIADA_MOTOR` decides the engine **when a plan is created**. Every plan widget stores
  `motor: "3d" | "python"`.
  - Existing plans keep their engine for edits and images, so a flag flip only affects new plans.
  - A 3D plan whose spec contains an unrepresentable piece falls back to python for that plan. The reason is logged
    with `decidir("regla:motor_guiada", …)`.
- **Tokens**: `crearTokenPlan` gets `backend: "globos3d"` (`aprobacion.ts:10`). `/api/generate` and `/api/plan-editar`
  reject `globos3d` tokens, and the new routes reject `python` tokens. Each plan has one quantity owner.

### 3.1 Contract types (sketch)
```ts
// src/lib/globos3d/motor/espec-cliente-v1.ts   (zod, exported to contracts/domain/v1/espec-cliente.schema.json)
type EspecClienteV1 = {
  version: "espec-cliente.v1";
  origen: { tipo: "propuesta" | "idea" | "idea_sumada" | "edicion"; ideaIds?: string[] };
  piezas: PiezaEspec[];                         // 1..8 (MAX_PIEZAS_PLAN)
};
type PiezaEspec = {
  id: string;                                   // EST_01_ARCO… stable across edits
  oficial: EstructuraOficialId;                 // the 18 of estructuras-oficiales.ts:51
  nombre: string;
  lugar: "centro" | "izquierda" | "derecha" | "fondo" | "techo" | "mesa";
  medidas: { anchoM?: number; altoM?: number; largoM?: number; grosorM?: number };
  colores: Array<{ codigo: string /* Sempertex "570" */; nombre: string /* customer word */; peso: number }>; // 1..6, Σpeso=1
  tamanos: "clasica" | "organica_fina" | "organica_gruesa" | "solo_grandes";   // = MEZCLAS (size proportion)
  densidad?: "sencilla" | "media" | "lujosa";
  forma?: string;                               // formas-pieza ids (aro "parcial", "organico"…)
  flores?: { cantidad: number; petalos: number; codigo: string; centro?: string } | null;
  /** Escape hatch for unrepresentable pieces: counted from the catalogue, not drawn. */
  declarada?: { materiales: Array<{ formatoId: string; codigo: string; cantidad: number }>; motivo: string };
};
// src/lib/globos3d/motor/v1.ts  (server-only facade; the ONLY entry the guided product may import)
type ResultadoMotorV1 = {
  motor: { id: "globos3d"; version: string };   // VERSION_MOTOR, bumped on any BOM-changing engine change
  especHash: string;                            // sha256(jsonEstable(espec) + version)
  armada: ArmadaCompactaV1;                     // positions/radii/hex per balloon, tubes, flowers, per-piece boxes
  bom: { porPieza: Record<string, BomLinea[]>; total: BomLinea[] };  // BomLinea = { formatoId, codigo, cantidad }
  avisos: string[];                             // customer words ("Las flores no se dibujan…")
  noRepresentable: Array<{ piezaId: string; motivo: string }>;
};
declare function armarDesdeEspec(espec: EspecClienteV1): ResultadoMotorV1;
// pricing: CotizacionPlanGuiado-compatible (asistente-guiado-v1.ts:140), mermaPorcentaje = 8, lines with varianteId
// edits (Phase 5):
type EdicionEspecV1 =
  | { op: "reemplazar_color"; de: string; a: string; piezas?: string[] }
  | { op: "agregar_color"; color: string; piezas?: string[] }
  | { op: "quitar_color"; color: string; piezas?: string[] }
  | { op: "proporcion_color"; pieza: string; pesos: number[] } | { op: "mas_menos_color"; color: string; direccion: 1 | -1; piezas?: string[] }
  | { op: "tamano_pieza"; pieza: string; medidas?: PiezaEspec["medidas"]; direccion?: 1 | -1 }
  | { op: "tamano_globos"; pieza?: string; direccion: 1 | -1 }               // moves along MEZCLAS
  | { op: "quitar_pieza"; pieza: string }                                    // Q4
  | { op: "agregar_pieza"; oficial: EstructuraOficialId } | { op: "flores"; pieza: string; flores: PiezaEspec["flores"] }; // Q4
// flag
type MotorGuiada = "3d" | "python";
declare function leerMotorGuiada(req: Request): Promise<{ motor: MotorGuiada; fuente: "cookie" | "ajuste" | "env" | "defecto" }>;
```

### 3.2 Orphan-property ledger (kept from v2, smaller)
`motor/consumo.ts`: `CONSUMO satisfies Record<RutaHoja<EspecClienteV1>, "escena" | "bom" | "flux" | "ui" | {ignorado: string}>`.
A new spec field fails compilation until someone declares where it goes. The conversions plan → spec and
propuesta → spec carry their own ledgers of `PlanDecoracion`/`PropuestaComposicion` fields that are deliberately
ignored, each with a reason:
- `armado_*.v1` designer knobs (cima, curva, ondulación, salientes, racimo)
- `variant_overrides`
- `restricciones.tamanos`
- `referencia_element_id`

## 4. Phases (each one can ship on its own behind `GUIADA_MOTOR`, default `python`)
Sizes: S ≤ 2 dev-days, M 3–5, L 6–10.

### Phase 0 — Runtime flag, routing skeleton, client upcast (S, ~1.5 d)
- **Create**:
  - `src/lib/guiada-motor/bandera.ts` (`leerMotorGuiada`). Order: admin-only cookie `guiada_motor=3d` (owner testing in
    production, same pattern as `ia_proveedor` at route l.201) → Neon `ajustes_runtime` row (30 s TTL) → env
    `GUIADA_MOTOR` → `python`.
  - `scripts/migrations/032_ajustes_runtime.sql`. **Use 032**: 030 is taken by e4z and 031 by e5m.
  - `GET /api/guiada/motor` (no-store).
- **Change**:
  - `VistaGuiada.tsx`: add `WidgetPlan.motor`, upcast missing = `python` in `leerSesion` (l.1997).
  - Move the branching into a new hook `src/components/guiado/usarMotorGuiada.ts`. VistaGuiada is already 2 146 lines,
    so it should not grow.
- **Tests**: flag precedence and TTL; cookie ignored without admin; old `demo_guiado_v2` payload fixtures upcast.
- **Risk**: the page is prerendered (cacheComponents), so the flag must not be read in `app/asistente/page.tsx`. The
  GET route handles that.

### Phase 1 — Facade `armarDesdeEspec` + spec builders + golden fixtures (L, 6–8 d)
- **Create** (`src/lib/globos3d/motor/`):
  - `v1.ts`, `espec-cliente-v1.ts`, `espec-a-escena.ts` (private; table below)
  - `layout.ts`: places pieces by `lugar` inside `SALA_INICIAL`; widths from medidas
  - `colores-espec.ts`:
    - customer words and `COLORES_PROPUESTA_V2` + tonos → Sempertex `codigo`, via a reviewed table
    - plan materials `(product title, color, acabado)` → codigo via `referenciaDelTitulo`/`referenciaDelCatalogo`
  - `espec-desde-propuesta.ts` (propuesta + brief.medida → spec; no model, no RAG)
  - `espec-desde-plan.ts` (stored idea `PlanDecoracion` → spec; participacion → peso, mezcla → tamanos, flores, forma)
  - `representable.ts`, `consumo.ts`, `armada-compacta.ts`
- **Change**: `scripts/ops/export-domain-contract-schemas.ts` registers `espec-cliente.v1` and `resultado-motor.v1`
  (guarded by `contracts:check`).
- **Builder map**:

  | Official id | Engine builder |
  |---|---|
  | arco | `arco` quartets; pattern from colours (1 → un_color, 2 → dos_colores, 3–4 → espiral) |
  | arco_asimetrico | new small builder: two `formaSemiarco` tramos, heavier side (S) |
  | arco_no_denso | `arco_organico` with `densidad` < 1 (approximation) |
  | semiarco / semiarco_asimetrico | `semiarco_organico` (mirror by `lugar`) |
  | columna | `columna` quartets + `remate` from `armado_columna` |
  | columna_asimetrica | `columna_organica` with inclinación |
  | columna_no_densa | `columna_organica` with lower density (approximation) |
  | pared_densa | `pared_malla` |
  | pared_no_densa / pared_organica | gap (see §5) |
  | guirnalda (organica_*) | `guirnalda_organica` |
  | guirnalda (clasica) | `guirnalda` |
  | aro_circular (organico) | `aro_organico` |
  | techo_globos | `techo` red (ancho × fondo) |
  | racimo_pared | decoration `racimo` on the wall |
  | bouquet | `ramo_helio` (partial) |
  | centro_mesa | gap until e4v |
  | figura | `declarada` |

  Balloon flowers → decoration `flor` nodes hung on the piece's anchors (`colocacion` ancla).
- **Tests**:
  - golden BOM fixtures `contracts/domain/v1/golden/motor-guiada/idea-<id>.json` for the 28 stored ideas, plus one
    default spec per official structure: counts per (formatoId, codigo), total, box ± 5 cm
  - determinism (same spec twice gives a byte-identical BOM)
  - colour coverage (every `COLORES_PROPUESTA_V2` word and every colour in `planes-ideas.json` resolves; includes
    "verde salvia")
  - perf: p95 ≤ 1.5 s per plan of ≤ 8 pieces / ≤ 1 500 balloons, with a hard cap on balloons per piece
  - an import-boundary check: the guided code imports only `motor/v1.ts`, and `motor/*` never imports `biblioteca.ts`
    or `ideas-sempertex/*` (huge, lazy)
- **Risks**:
  - Counts differ from Python, especially organic pieces that lean on R-5. This is expected under D-024; the report
    (Phase 6) quantifies it.
  - Seeded output changes whenever the engine changes. Bump `VERSION_MOTOR` and re-baseline the goldens in the same
    PR.

### Phase 2 — BOM from the engine, priced by the existing price service (M, 4–5 d)
- **Create**:
  - `motor/crosswalk-variantes.ts`: `(formatoId, codigo)` → `{product_id, variant_id}`. Built from
    `catalog_variants`/`catalog_products` (forma, diam_pulg, title → codigo through `TABLA_SEMPERTEX`). Generated per
    snapshot by `scripts/motor/generar-crosswalk.ts` into `data/motor/crosswalk-<snapshot>.json`, with a live-query
    fallback through `getRagPool`.
  - Explicit `sin_cobertura` when a colour is not sold in that size (see `NO_ESTAN_EN_LA_TIENDA`).
  - `motor/cotizar-bom.ts`: apply `MERMA` (0.08; a single constant exported with the domain contract and asserted equal
    to `merma.py`), `ceil`, then `llamarPythonListaMateriales`, then the `CotizacionPlanGuiado` shape.
  - `motor/plan-guiado-desde-motor.ts`: the adapter. It builds a `PlanGuiado`-valid envelope: a `PlanDecoracion`
    projection, `estructuras[].lineas` per piece and variant, `compras`, `plan_hash = especHash`, and an approval token
    with `backend:"globos3d"`. It also attaches `motor` and `espec`.
  - Route `POST /api/guiada/motor/plan` (`{desde:"propuesta", propuesta, brief} | {desde:"idea", idea_id, base?}`).
- **Change**:
  - `aprobacion.ts`: add `"globos3d"` to `BackendPlan`.
  - `generate/route.ts` and `plan-editar/route.ts`: reject globos3d tokens.
  - `usarMotorGuiada.ts`: `aceptarPropuesta`, `crearPlanDeIdea` and `agregarIdeaAlPlan` branch on motor.
  - `asistente-guiado/route.ts`: `costear_decoracion` prices the idea's engine BOM when it has a spec (Q3). The
    curated list stays for the 3 figures.
- **Tests**:
  - crosswalk coverage (every pair in the goldens resolves or is declared)
  - pricing with an adapter double
  - envelope parses with `PlanGuiadoSchema` and `CotizacionPlanGuiadoSchema`
  - `TablaGlobosPieza`, `ComprarMateriales` (`plan-compra.ts`) and `CotizacionPersonalGuiada` render from the
    envelope (existing tsx tests extended)
  - golden **priced** fixtures store counts and variant ids only; prices are not snapshot-stable
- **Risks**:
  - A missing variant makes the whole quote fail (`material_no_disponible` is all or nothing in `plan.py:6896`).
    Pre-filter with the crosswalk; on failure, fall back to the python plan for that request.
  - Carousel cards show Python counts and curated lists (`detalles-ideas.json`) while the plan shows engine counts
    (Q2). Precompute the engine BOM for the 28 ideas and show it when motor=3d.

### Phase 3 — Customer view: read-only 3D render, "lightly modified" (M, 4–5 d)
- **Create** (`src/components/guiado/motor3d/`):
  - `VistaPlan3D.tsx` (lazy)
  - `visor-compartido.ts`: **one** off-screen viewer per page that renders stills (`renderEstandar`, ~768 px) for every
    card. Recycled like `CapturaRender` and disposed per D-017 (no module-level GPU caches).
  - `HojaOrbita.tsx`: tap → one live orbit sheet, a single live WebGL context, `webglcontextlost` handled
  - `desde-armada-compacta.ts`: compact armada → `EscenaArmada` subset → `mostrarArmada`
- **"Lightly modified"** means:
  - fixed `frente`/`tres-cuartos` camera and `salaNeutra`
  - no grid or helpers
  - legend chips from the BOM
  - no selection, drag or inspector
- **Fallback** for no WebGL or low memory: server SVG projection, `motor/vista2d-svg.ts` (pure TS, depth-sorted shaded
  discs).
- **Change**:
  - `TarjetaPlan.tsx` (l.243, l.331): motor=3d shows the scene still instead of `GraficaMotorGuiada`, plus per-piece
    crops by piece box.
  - Hide `ModificarPieza` (l.265) for 3D plans (D-020).
- **Tests**:
  - SVG projection is structural (circle count per colour = BOM)
  - the component renders the no-WebGL path
  - bundle budget: `/asistente` first-load JS unchanged; three.js only in the lazy chunk (build check script)
  - manual check on a mid-range Android device and on iOS Safari
- **Risks**:
  - Mobile WebGL context limits and memory. One viewer plus stills handles this.
  - About 200 KB gzip downloaded on first plan. It is lazy, but it counts on 4G.

### Phase 4 — FLUX guide from the same geometry (M, ~3 d)
- **Create**: `POST /api/guiada/motor/imagen` with `{espec, token, captura?, ambiente}` and the `x-solicitud-imagen`
  header.
  - The server re-arms the **signed** spec and builds the inventory from it (`escenaEnIngles` +
    `descripcionRender3d`). It never trusts client text.
  - Prompt: `promptRender3dFiel`/`promptRender3d`, **consumed, not edited**.
  - `generarConSempertexFlux` `/edit`, with the capture as base.
  - Recovery reuses `src/lib/generacion/imagen-recuperable.ts`.
  - Cost telemetry `superficie:"guiada-3d"` and the hourly cap.
- **Base image**: the client capture comes from the shared viewer (`capturar()`, what the customer sees). The fallback
  is the SVG projection rasterised with sharp (the `rasterizar-guia.ts` pattern).
- **Change**: `pedirImagenConRecuperacion` takes a route parameter; `verComoQuedaria` branches. IndexedDB stays the
  same.
- **Tests**: the prompt never contains client text; schema checks; recovery doubles; a token mismatch gets 4xx.
- **Risk**: e5r changes `render-ia.ts`. Consume its exports after it merges. If a guided-specific variant is needed,
  put it in a new `render-ia-guiada.ts`; do not edit `render-ia.ts`.

### Phase 5 — Customer edits as limited AI tools (M–L, 5–6 d)
- **Create**:
  - `motor/ediciones-espec.ts`: pure ops (§3.1) with ranges from `RANGOS_ESTRUCTURA` and honest avisos
  - `motor/edicion-desde-pedido.ts`: maps the existing chat `PedidoEdicionPlan` and panel `CambioPlan` to
    `EdicionEspecV1`; anything unsupported returns a "No pude: …" result (D-023)
  - `POST /api/guiada/motor/editar` (`{espec, token, edicion}` → re-arm only the changed pieces via the cache → price →
    new envelope)
  - `planActualDesdeEspec` (exact, so the lossy `planActualDesdePlan` is no longer used for 3D plans)
- **Change**:
  - `edicion-chat-guiada.ts` / `usarAjustePlanGuiado.ts`: inject 3D dependencies in place of `/api/plan-editar`.
  - `asistente-guiado/route.ts`: the l.236 aviso becomes engine-neutral; no Taller tools are ever exposed.
  - `AjustarPlan`: the size control maps to `tamano_pieza`/`tamano_globos`, the colour slider to `proporcion_color`.
- **Forward-compatible with e4z**: each AI turn exposes `{turnoId, espec antes/después, capturas}`, matching
  `PRODUCTOS_FEEDBACK=["taller","cliente"]`.
- **Tests**:
  - each op as a unit
  - a mapping-table test over all 10 `HERRAMIENTAS_EDICION`
  - a "no drag/create" guarantee: no op adds geometry outside the official list
  - failure disclosure
- **Risk**: some chat edits today rely on Python catalogue search (`buscar` with the approval token). For 3D, colours
  resolve to Sempertex codes through the crosswalk instead.

### Phase 6 — One-off parity report, information only (S, ~2 d)
- `scripts/motor/reporte-paridad.ts` runs:
  - the 28 stored ideas
  - for each of the 18 official structures, the default plus 2 sizes
  - optionally, a sample of logged guided plans
- It compares Python resolve against the engine on: total balloons Δ%, colour-set equality, size mix, price Δ, box
  dimensions and unrepresentable flags.
- Output: `REQ-007/PARIDAD-<fecha>.md` + CSV in the bitácora. No gate.

### Phase 7 — Switch (S, 1 d + 1 week watch)
- Order: the owner tests with the cookie, then the `ajustes_runtime` value is set to `3d`.
- Runbook signals:
  - fallback-to-python rate per reason
  - `armar` p95
  - pricing 422s
  - image failures and cost per plan
  - customer edits rejected
- Rollback = flip the value (≤30 s). 3D plans already in sessions keep working on 3D routes, which stay deployed.
- The Python guided paths stay for the classic chat and for fallback. Deleting them is a later item.

**Total: ~27–33 dev-days.** Phases 0–2 are the minimum switchable unit, with the 3D still and edits following.

## 5. What the engine cannot represent today (base 7245991f)

| Structure | What is missing | Catalogue items affected |
|---|---|---|
| figura | No generic figure. Only specific digitised ones exist (mono, flor_tubito, Halloween set). | 21, 23, 26; figure part of 30. `declarada` (curated list, photo, no geometry), or hand-built escena per idea (S each). |
| centro_mesa | No builder in base. e4v adds `centros-mesa(-diseno).ts`. | 03 |
| bouquet | `ramo_helio` exists, but there is no `armado-bouquet.v1` mapping and no organic base or weight variants. | 03, 16 (×2) |
| aro_circular `forma:"parcial"` | No partial/diagonal ring and no visible metal hoop. The full organic ring is fine. | 27 (28 needs balloon-flower mapping, which is feasible) |
| arco_no_denso / columna_no_densa / pared_no_densa | No airy ("sencilla") classic-quartet builder. Organic approximation only. | — |
| pared_organica | No parametric organic wall. `trazo_organico` silhouette needs a builder. | — |
| arco_asimetrico | No "carga" (heavier side) parameter. New 2-tramo builder needed (S). | 31's idea |
| Classic arch/column patterns | Plan patterns `anillos, bloques, degradado, aleatorio, flor, damero, zonas` and >4 colours: `PatronTrenza` has 5 patterns and ≤4 colours. | 02 (6 materials), partial |
| Photo-inspired plans | Blueprint, scene props, element boxes: not in spec v1. Python fallback per plan. Later: lectura → `compilar-lectura` → spec, after fixing the v2 garland-colour bug. | — |
| Plan-only fields | `armado_*` designer knobs, `variant_overrides`, `restricciones.tamanos`, `referencia_element_id`. Ignored, with ledger reasons. | — |
| Data issues (not engine) | Stored plans of 29 (LOL arch → 2 columns), 30 (figure dropped), 31 (asym arch → semiarco). | 29, 30, 31 |

Representable with Phase 1 builders: 01, 04–15, 17–20, 22, 24, 25, 31, the column part of 30, and 02 with an
approximate pattern. That is 23–24 of the 28 stored ideas.

## 6. Owner questions (batched; recommendation first)
1. **Merma** on engine counts: apply 8 % before package rounding, like Python. Rec: yes.
2. **Idea cards** show engine counts when motor=3d, and "cantidades exactas" copy changes to "cantidades del motor".
   Rec: yes.
3. **Carousel "¿cuánto cuesta?"** prices the engine BOM, with the curated list only for figures. Rec: yes.
4. **Edit list**: keep remove piece, add an official piece or catalogue idea, and balloon flowers; keep left/right side
   only; drop rename/move. Rec: yes (these are plan composition, not viewer manipulation).
5. **Photo plans**: Python fallback per plan until a later phase. Rec: yes.
6. **Proposal plans** no longer pass through the model/RAG product choice; colour words map to a reviewed
   Sempertex-code table. Rec: yes. It removes the 2–16 model calls per plan.

## 7. Parallel branches (real conflicts only)
- **feat/mobiliario-libre (e5f)**: no conflict. v3 has no furniture and edits no file it touches.
- **feat/salon-evento (e4v)**: no textual conflict. It is a **dependency** for `centro_mesa` (`centros-mesa-diseno.ts`).
  Its `escenas-presets.ts`/`escena.ts` edits may move the goldens if Phase 1 imports presets; re-baseline after merge.
- **fix/honestidad-render (e5r)**: edits `render-ia.ts` (mobiliario prompt rules) and `escena.ts`. Phase 4 consumes
  `promptRender3d*` and `descripcionRender3d`. Land e5r first, or rebase Phase 4 on it. Do not edit `render-ia.ts` in
  v3.
- **feat/estudio-modulos (e5m)**: changes `armada-visor.ts` (`mostrarArmada` gains an optional 4th arg, compatible),
  `camara-estandar.ts` (constants moved, API compatible), `render-3d-imagen/route.ts`, `imagen-liviana.ts`,
  `tope-fotos-hora.ts` and migration 031.
  - Phase 3/4 reuse those viewer helpers read-only and add new files.
  - **Migration number: use 032.**
  - The `modulos.ts` pareja fix is geometry only and changes no BOM counts (guided specs use no `modulo` pieces), so
    there is no golden conflict.
- **feat/feedback-ia (e4z)**: no conflict now. It does not touch `VistaGuiada.tsx` yet. Migration 030 is taken.
  Phase 5 emits turn data compatible with its contract. When its customer rating UI lands, whoever merges second
  rebases `VistaGuiada.tsx`.
- **`src/components/guiado/Compositor.tsx`** is touched by all branches through main's voice change. v3 does not edit
  it.

## 8. Review gates
- CI: `contracts:check` (spec/result schemas), ledger compile, goldens, colour/crosswalk coverage, import boundary,
  perf bench, `/asistente` bundle budget.
- Human: the owner tests with the cookie before Phase 7; antagonistic review on Phase 2 (pricing/tokens) and Phase 5
  (customer edits).

## 9. Rulings taken 2026-10-09 (owner asked for autonomy; recommendations adopted, owner may override)
Q1 merma 8 % before package rounding — yes. Q2 idea cards show engine counts ("cantidades del motor") — yes. Q3 carousel
prices the engine BOM, curated list only for figures — yes. Q4 keep remove piece / add official piece or idea / balloon
flowers / left-right side; drop rename/move — yes. Q5 photo plans fall back to Python per plan — yes. Q6 proposal plans
skip the model/RAG product choice, colour words → reviewed Sempertex-code table — yes.
Execution: Phase 0 and Phase 1 start now in parallel worktrees (e6a feat/guiada-motor-bandera, e6b
feat/guiada-motor-fachada); Phase 2 crosswalk next.
