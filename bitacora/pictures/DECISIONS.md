# pictures — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — Sempertex ideas are built lazily
- **Date:** 2026-10-08 · **Status:** Accepted
- **Context:** importing the Library evaluated and built all 393 ideas: 18.6 s of pure JS; /3d froze ~20 s in production.
- **Decision:** every idea computes its content on first access (memoized getter); `BIBLIOTECA_FABRICA` never touches `contenido`; Library index runs in a Web Worker; `test-carga-3d` fails over 500 ms.
- **Alternatives:** precompute a static JSON index at build time — deferred, still an option for the Library counts.
- **Consequences:** + /3d loads in ~2 s / − heavy ideas (e.g. #471, ~6 s) show "Armando…" when opened.
- **Source:** [day log](2026-10/W2/2026-10-08.md) · commit ef70eb7e

## D-002 — Viewer draws by batches and only on change
- **Date:** 2026-10-08 · **Status:** Accepted
- **Context:** every edit rebuilt all meshes (one LatheGeometry + material per balloon) and it rendered 60 fps idle.
- **Decision:** instanced batches per (geometry, material), per-node fingerprints for incremental rebuild, render on demand, shadow map only on scene change; lower detail in editor, high quality kept for capture.
- **Consequences:** + 536→36 draw calls, select ~800→60–90 ms / − clear balloons look more opaque in the editor.
- **Source:** commit 7b168359

## D-003 — Keep FLUX.2 /edit for the 3D photo; closed inventory in the prompt
- **Date:** 2026-10-08 · **Status:** Accepted
- **Context:** FLUX invented pieces (extra tree, tables, second pumpkin). Experiment (US$0.52 of 0.60 cap) compared FLUX.2 edit vs FLUX.1 i2i 0.35/0.55 vs ControlNet canny+depth.
- **Decision:** keep FLUX.2 with "Igual al visor" room, closed per-piece inventory and organic silhouettes; FLUX.1 variants stay only in `scripts/exp/render-fiel.ts`.
- **Alternatives:** FLUX.1 i2i / ControlNet — faithful (IoU 0.91–0.97) but do not look like photos.
- **Consequences:** + no invented objects / − colors drift (ΔE ~23); next: photoreal 3D or post color correction.
- **Source:** commits 84d04b70, 761bc2dc · `pictures-workspace/render-fiel/`

## D-004 — Editor redesign: rail + panels, full viewer, right inspector, solo editor
- **Date:** 2026-10-08 · **Status:** Accepted
- **Context:** owner found the editor's UX poor: 9 mixed tabs, endless left column, no selection inspector.
- **Decision:** approved mockups https://claude.ai/artifact/2JLXNGsiCaEukgh5KV3Scq; the 9 generator tabs become the solo editor of each type.
- **Consequences:** + one mental model (scene editor) / − large refactor of `Taller3D.tsx` and panels.
- **Source:** [day log](2026-10/W2/2026-10-08.md)

## D-005 — Idea digitization loop paused for performance/UX work
- **Date:** 2026-10-08 · **Status:** Accepted
- **Context:** owner: «pausemos el resto, centrémonos en rendimiento».
- **Decision:** stop the 10-minute loop after lot 26; state documented in repo `SEGUIMIENTO.md` (pause section).
- **Source:** [day log](2026-10/W2/2026-10-08.md)

## D-006 — FLUX color text uses official balloon hex and neutral light
- **Date:** 2026-10-08 · **Status:** Accepted
- **Context:** FLUX.2 warmed/darkened the whole photo and turned «Fashion Azul Caribe» (named "turquoise") green.
- **Decision:** every color goes with its `hexGlobo` («light aqua blue (#4BBBCF)»), room tones with hex and without "warm", plus color-fidelity and neutral white-balance sentences; MAX_DESCRIPCION 1400 → 1800.
- **Alternatives:** post-correct colors per piece — kept as next step if residual drift matters.
- **Consequences:** + mean per-piece ΔE ~25 → ~15 (experiment US$0.096) / − longer prompt (~2.6k chars).
- **Source:** commit c25490f1 · `scripts/exp/render-color.ts`

## D-007 · Parametric organic pieces keep their generator · 2026-10-08
Context: the owner finds structures rigid; photo garlands need any silhouette and must stay editable.
Decision: `organico` pieces may carry `generador` (today `trazo`); editors and the AI change the generator and
re-derive `opciones` (`piezaDeGenerador`). Recolor writes both. Organic-column question round answered with the
recommended defaults (three types: classic / irregular / freeform; to be built in REQ-001 step 2).
Alternatives: new piece type (touches every switch) · keep raw tramos (not editable). Source: REQ-001.

## D-008 · Photo → scene through a structured reading · 2026-10-08
Context: the owner wants the AI to recreate a Pinterest photo autonomously.
Decision: the model only READS the photo into `LecturaFoto` (catalog pieces in image coordinates, silhouettes with
thickness, decorator colour names + finish, sizes, foliage, backdrops, scale reference); `compilarLectura` builds the
scene deterministically (testable). The 13 owner photos are read by hand with the same format as the benchmark.
Alternatives: free-form tool calling from the image (untestable, drifts) · generating images (forbidden for Gemini).

## D-009 · Scene agent: stay on Gemini Flash, invest in tools and rules · 2026-10-08
Context: the AI changed whole pieces when asked for "the link-o-loons of Ramas" or "the colours of one size".
Decision: keep Flash; give it sight inside pieces (parts contract, `ver_pieza`, `buscar_en_escena`), a trade glossary,
selector-based precise edits verified by rebuild, layout/group tools, selection context, ask-when-ambiguous and an
evaluation bank. Every piece must be made of identifiable balloon types/products by parts. Source: owner, REQ-003.

## D-010 · Library RAG architecture · 2026-10-08
Decision: Neon Postgres + pgvector; embeddings for everything (text fichas + item photos + standard 3D renders);
Python does batch work (embeddings, analysis, rerank), Next does the online hybrid query (FTS + trigram + vectors, RRF,
hard filters) with in-memory fallback; code stays source of truth for factory items; owner items move to the DB;
taxonomy of ~60 celebrations + ~50 themes first. Alternatives: query through Python (extra hop to a hand-deployed VPS);
DB as editable source (later, with an admin). Source: owner, REQ-002.

## D-011 · Library classification by Claude subagents, not paid API calls · 2026-10-08
Context: REQ-002 step 1 planned a Gemini pass (cap US$1.00) to tag every item with celebrations and themes.
Decision: rules first (free), then Claude Sonnet 5.5 subagents at medium effort read batches of fichas and assign
celebraciones/temáticas with confidence and reason; output stored as versioned JSON; rule/model disagreements listed
for owner review. No paid Gemini calls for classification. Embeddings themselves still need the embedding API
(paid, capped, after REQ-004's spend ledger). Source: owner.

## D-012 · Photo → scene: measure with detection, never settle for the tools · 2026-10-08
Context: Gemini's eyeballed reading of a photo gets scale, balloon sizes, thickness and zones wrong (83 sparse balloons).
Decision: Gemini reads WHAT and WHERE (pieces, axis); a second Gemini pass detects every balloon (tiled box_2d + colour)
and backdrops; deterministic code measures scale, tier formats (by ratio, anchored on mediums), per-segment thickness/mix,
colours per tier/zone and anchors giants. Claude renders a reference first; missing engine capabilities are built, not
worked around. A colour is never changed to keep a format (drop the format instead). Source: owner.

## D-013 · Antagonistic review gates and the orphan-property rule · 2026-10-08
Decision: every branch and plan passes hostile senior reviewers (architecture, correctness, orphan properties, separation,
performance) before merge; every contract field must have a declared consumer (typed ledger test) or an explicit
"ignored" reason. Source: owner ("agentes antagónicos por donde haya", "propiedades que se pierden").

## D-014 · REQ-007 plan v1 rejected · 2026-10-08
Context: 3 antagonistic architects: customer already has the designer engine (Python ports, golden vectors, the SVG the
customer approves); Escena-as-API freezes the workshop; separation cosmetic; shadow in request path unsafe (9.3 s for
1 483 balloons). Decision: PLAN v2 (ADR on canonical engine first, real product separation, contracts in
contracts/domain/v1, offline shadow, versioned approvals). Owner decisions D1–D5 pending.

## D-015 · Automatic photo refinement stays OFF until owner-labelled calibration · 2026-10-08
Context: calibration over 4 owner photos × 28 known perturbations: capture/embedding noise is 0, but image-embedding
cosine does not separate small changes (moving 50 cm improved similarity in 2/4 photos). Decision: MARGEN_MEJORA 0.02,
RONDAS_AUTOMATICAS = 0; enable only after ~30 owner-labelled A/B rounds give a threshold that rejects bad rounds.

## D-016 · Merge order of the four review branches · 2026-10-08
e4m (refine) → e4q (materials, based on e4m) → e4p (furniture) → e4n (photo fidelity, last). Hand-resolve: `ambiente` in
e4m's `esquema-escena.ts`; per-viewer scenery caches in escena-globos.ts (no module-level env/material maps).

## D-017 · Viewer resources are per viewer, never module-level · 2026-10-09
Context: three branches independently re-introduced module-level caches holding GPU resources (env map, scenery
materials/geometries); a second viewer (capture, library thumbnail) disposing them turned metals/foil black.
Decision: every cache holding a GPU resource lives inside the viewer (`crearEscena` closure / per-viewer factories such
as `escenografia-visor.ts`) and is released in `destruir`; enforced by test-foil-visor (no module-level env) and
test-escenografia-visor (two viewers share nothing).

## D-018 · Bundled script font for text signs: Great Vibes (SIL OFL 1.1) · 2026-10-09
Context: system cursive fonts don't join letters and change text size per OS → non-deterministic captures.
Decision: bundle Great Vibes (woff2, OFL.txt included), loaded before rasterising; no silent fallback. Reversible:
another OFL script (Sacramento, Alex Brush) can be added per sign later if the owner prefers.

## D-019 · REQ-007 owner rulings: the 3D engine becomes canonical; two products, one engine · 2026-10-09
Context: REQ-007 PLAN v2 asked D1–D5. Owner (2026-10-09): "el motor 3D es el que va a [reemplazar] el Python, [que] no
nos sirve para nada… la pregunta es A y B"; "el chat normal todavía usa el motor viejo… lo 2D es básicamente el 3D del
plan modificado ligeramente; el 3D y el chat normal van a ser productos diferentes"; "el chat… es otro producto, va a
utilizar el motor, pero no se lo va a mostrar al usuario… podrá modificar cositas puntuales, pero no el nivel de
control del motor pro".
Decision: D1 = target (a) — globos3d is the canonical geometry/quantity engine — reached through (b): the customer chat
keeps its current (Python/designer) engine until each structure type passes parity with golden vectors, then switches
to globos3d. The customer "2D" view is the plan's 3D render lightly modified (not a separate drawing). Two products:
Taller 3D pro (full engine control) and the customer chat (engine hidden, a short list of point edits). D2–D5 still
use the PLAN recommendations unless the owner says otherwise; D4 (the exact edit list) still needs the owner.

## D-020 · REQ-007 D4: what the customer can edit · 2026-10-09
Context: D4 asked which edits the customer chat exposes. Owner: the customer asks the AI for changes and "más o menos
lo haga"; can change colours (colour references and colour proportions) and size proportions; cannot drag things,
create pieces or any fine control that depends on the browser 3D environment ("lo bonito del otro motor"). Later the
customer-side AI will be limited so it doesn't do "pro" things ("tiempo al tiempo").
Decision: customer edits = (1) natural-language requests to the AI, (2) colour references, (3) colour proportions,
(4) size proportions. No direct manipulation (drag/move/create/select-in-viewer) in the customer product. A future
capability limit for the customer AI is a separate, later item (not now).

## D-021 · Taller AI UX: direction B (side assistant with per-turn change cards) · 2026-10-09
Context: AI-UX audit of the Taller (10 ranked problems) and two directions (artifact Nuv9GST6YR9HmGgAMoDdMr). Owner:
"Me gusta la B".
Decision: build B — AI tab in the right panel ("Pieza | ✦ IA"), each turn a card (what it did, scene diff before→after
with 3D highlight on hover, steps, "Deshacer turno" reverting only AI-touched pieces, "Ver antes"), question cards,
scope chips (piece / several / whole scene), FLUX render card with time and cost, half-height sheet on phones,
conversation saved with the scene. Common base first: pure scene diff by piece id, per-turn undo as one named step in
the global history, abort for every request, streamed steps (NDJSON) if cheap. The "✦ Pedir a la IA" chip from A is
not in scope unless the owner asks.

## D-022 · AI feedback (REQ-010): full form everywhere, non-blocking, Neon + dedicated file storage · 2026-10-09
Context: owner wants every AI action rated (1–10, multiple-choice reasons, comment on gaps/improvements) with the full
render state (images, current and previous states) to find the AI's gaps.
Decision (owner answers): full form in the Taller AND the customer chat; always visible and non-blocking on each AI
turn, opening the "why" panel automatically on undo/correction; data + scenes in Neon, before/after images in a
DEDICATED Garage S3 for demo-decoracion on advin-vps (the existing Garage serves Maros Construction and must not be
mixed); admin panel + automatic periodic gap analysis.
