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

## D-023 · 2026-10-09 · The AI must never claim an action that failed
After the owner incident (4 false confirmations), the server enforces disclosure: the scene check describes furniture from the catalogue (never the model-chosen name) and any failed step in a turn is appended as "No pude: …" if the answer omits it. Voice dictation goes on directly in production (VOZ_ENABLED=true): owner asked for it everywhere, route needs login, cost 0.

## D-024 · Guided chat moves to the 3D engine now (supersedes D-019's parity gate) · 2026-10-09
Context: owner asked whether the guided chat uses the new engine (it does not: Python plan + pricing). Owner: «hagamos
la migración ahora, reemplacemos la decisión».
Decision: the guided customer chat switches to globos3d now, without waiting for per-structure shadow parity (D-019 (b)
gate removed). Kept from D-019/D-020: two products (engine hidden in the customer chat), customer 2D = the plan's 3D
render lightly modified, customer edits = AI requests + colour refs/proportions + size proportions, no drag/create.
Safety instead of the gate: one runtime flag (`GUIADA_MOTOR=3d|python`) for instant rollback, a one-off parity report
per structure type (information, not a gate), golden fixtures for the BOM. Pricing keeps the existing price service
(Python prices a given material list) in this step; moving pricing off Python is a later item. Classic chat follows
after the guided chat is stable.

## D-025 · Taller "Foto realista · Igual al visor" uses FLUX.1 Kontext max · 2026-10-09
Context: owner said the render was "supremamente mal" (FLUX.2 /edit dropped tables, moved the camera). Two paid rounds (US$0.597) on a 12×9 m wedding test: FLUX.1 img2img kept the layout but stayed a CG render; FLUX.2 /edit was photoreal but re-framed and changed counts; Kontext max was the only one both photoreal and faithful (camera, 6 tables × 4 chairs, centrepieces, frame, sign).
Decision: "Igual al visor" = Kontext max with a layout-to-photo instruction and the full-room capture from the current view; other "Lugar" options keep FLUX.2 /edit. Cost US$0.08 per photo (cap 30/h). Kontext is a FLUX base model (no LoRA), consistent with the fal-only/FLUX-base rule.

## D-026 · Quotes use the Sempertex standard presentations (closes P-035) · 2026-10-09
Context: the 3D engine had to choose which bags (presentaciones) to buy; the stored library plans had an allowlist of mostly 50-packs. Owner: «no entiendo lo de las bolsas, usa el estándar Sempertex».
Decision: quote with the presentations Sempertex sells for each balloon (PAQ X 12 / X 50 / etc. as published in the store catalogue), choosing the combination the Python resolver chooses (cheapest combination that covers the need, one 8 % reserve for the whole plan covered first by leftovers) = `POLITICA_PAQUETES = "python"`, already the default. No per-idea allowlist restriction; no "cheapest regardless" variant in production.

## D-027 · Helium litres = sphere volume of the inflated diameter (marathon, taken alone) · 2026-10-09
Context: PM backlog PRO-02 asked for "10 balloons of 30 cm with 7 % loss → 97 L"; that figure came from a 6-balloon BalloonBuilder example, not from 10 × 30 cm. Sphere maths gives 151.3 L.
Decision: helium per balloon = 4/3·π·(infladoCm/2)³ of each balloon as drawn (same size the pump list uses), × (1 + 7 % loss); tank = one nominal constant, labelled as an estimate in the UI and in the copied text. Reversible; owner can supply real supplier figures.

## D-028 · Product judge for flag-gated work runs at the switch dossier (marathon, taken alone) · 2026-10-09
Context: the marathon's definition of done asks for a product judge ≥ 8 with screenshots; customer edits on the 3D engine (REQ-007 Phase 5) are invisible to customers (GUIADA_MOTOR=python, Neon ajustes_runtime empty, no env var) and screenshots need a dev server on a low-RAM PC.
Decision: flag-gated, customer-invisible work ships after the antagonist says SHIP and the merged tree is verified; the product judge scores it (with screenshots, desktop + phone) as part of the W7 switch dossier, before any switch. Visible features keep the judge before merge.

## D-029 · REQ-013: class-prefixed local ids for Sempertex entries that had no catalogue id (marathon, taken alone) · 2026-10-09
Context: REQ-013 Phase 1 review (A7): SPEC R1 says the local id is today's id, but some Sempertex kinds never had a catalogue id — an idea plan and its guided decoration share the same `deco-…` key, and bare codes like `570` (colour) or `R-12` (format) carry no repository claim, so the local-id index could not be injective.
Decision: those entries get `<clase>:<código>` local ids (`formato:R-12`, `color:570`, `producto-tienda:<handle>`, `plan-idea:<deco-id>`, `decoracion-guiada:<deco-id>`, `modulo:<tipo>`), claimed by the Sempertex manifest. R1 still holds: these were never stored ids, so nothing stored is rewritten. Stored `mueble.id` is always the short form; qualified ids are normalised where scenes are written, and a qualified id whose repository does not match is rejected.

## D-030 · Product judge for staff-visible Taller features runs on the production deploy (marathon, taken alone) · 2026-10-09
Context: the definition of done asks for a product judge ≥ 8 with screenshots before merge, but a local dev server for screenshots competes for RAM on this 15.7 GB PC (and needs a turbopack.root hack per worktree).
Decision: Taller (staff/pro) features ship after hostile review SHIP + verified merge; the product judge scores them on the production deploy (desktop + phone screenshots via the browser) within the same cycle; a score < 8 opens a fix item immediately, and a broken experience is reverted. Customer-visible chat changes still get the judge before merge, or ship behind a flag.

## D-031 · VPS deploy becomes manual (workflow_dispatch) before CI goes green (marathon, taken alone) · 2026-10-09
Context: `deploy.yml` deploys main to the VPS (incl. the Python ai-api that prices customer quotes) on every green "Quality checks" run. CI has been red for a long time, so every automatic deploy is "skipped"; the CI-green branch would silently turn automatic VPS deploys on. Owner question (6) went unanswered; the brief says take the reversible default.
Decision: switch the deploy trigger to `workflow_dispatch` (manual, input `ref`, default main) in the same branch that makes CI green. This keeps today's behaviour (no automatic VPS deploys; the owner deploys by hand at milestones) and is reversible by restoring the `workflow_run` trigger.

## D-032 · Owner away all weekend: open questions take the recommended reversible defaults (marathon) · 2026-10-10
Context: owner, 2026-10-10 00:40: «Tienes completo control, yo me encuentro afuera de ese computador todo el fin de semana». Open questions (1) R-12 inflation in classic arches, (4) BalloonBuilder customer vs pro, (5) REQ-004 accounts; (3) API key: owner has none → Claude Code CLI transport for the local AI (W5b).
Decision: (1) keep the engine's official 5 quartets/m (no change; customers are on Python anyway); (4) every BalloonBuilder feature built this weekend is pro-only (Taller); customer-facing ones (palette→stock, tier quote) only behind a flag, default off; (5) keep the shared password; no accounts this weekend. Hard rules of the brief still apply (never kill :3010/:8000, no GUIADA_MOTOR switch, spend caps). All reversible; to be confirmed on Monday.

## D-033 · Owner allows touching the local dev servers this weekend · 2026-10-10
Owner: «Si puedes tocar los servidores de desarrollo». This lifts, for the weekend, the brief's rule «never restart/kill :3010 or :8000»: the lead may restart the owner's Next dev server on :3010 (e.g. after merges, to switch the local AI provider) and start/stop a local Python ai-api on :8000 (needed to re-resolve stored plans, P-039). Still never: Claude, Chrome, system processes; no `next build`.

## D-034 · No VPS deploy during the weekend, even with CI green (marathon, taken alone) · 2026-10-10
Context: main 77b4af27 is the first fully green CI run; D-031 makes the VPS deploy a manual `workflow_dispatch` gated on green CI. The VPS also serves the Python ai-api that prices customer quotes (Vercel calls it), and main carries Python changes never deployed there (R-36 served as R-24 b7f5cfe2, organic column silhouette a09b638b, guide tones bccc07f0, ruff format) plus the REQ-013 repository filter the Neon indexing (Phase 3 apply) depends on.
Decision: do not dispatch the VPS deploy while the owner is away; Vercel (customer UI + Taller) keeps auto-deploying main as before. On Monday the owner gets a deploy note (what changes in quotes) and decides; after that the REQ-013 Phase 3 Neon apply can run. Reversible: one `workflow_dispatch`.

## D-035 · Persisted guided-plan fields: the reader ships one deploy before the writer (marathon, taken alone) · 2026-10-10
Context: P-049 (eb7d0abd) stores an optional `propuesta` on 3D plan widgets. The saved-session schemas (`EstadoGuardadoSchema`, plan widget) are `.strict()`, so a build that predates a field discards the whole saved conversation when it meets the field. Today only admin-cookie tabs hold 3D plans, so reverting P-049 is safe now; once `guiada_motor` is `3d` for customers it would wipe their open conversations.
Decision: any new persisted field on a customer widget/session is added as `.optional().catch(undefined)` and first shipped as reader-only (schema accepts it, nobody writes it); the writer ships in a later deploy. Before flipping GUIADA_MOTOR to 3d for everyone, check that the deployed build and the previous one both accept `propuesta`. Reversible: process rule only.

## D-036 · Review stop-rule and model start for M tasks (marathon, taken alone) · 2026-10-10
Context: critic c12 — W4 capabilities spent ~4.5 h over 6 hostile rounds; rounds 5–6 found bounds main already has; build sheet and P-049 took 7 rounds on flag-gated code; ~8 of 11 M tasks escalated from haiku.
Decision: at most 3 hostile rounds per branch; from round 4 only correctness, pricing, security or data-loss findings block, the rest go to PENDING. M-size tasks start on sonnet xhigh (S stays haiku). W4 capabilities ships after the current opus round if it is strictly better than main (lote-02 not worse, budget holes closed), then the 30-photo re-run reports old and new IoU. Reversible: process rule.

## D-037 · Owner: not real production — VPS deploy approved, go hard (owner) · 2026-10-10
Context: owner, 11:4x: «La app no está en producción real así que dale duro» · «Aprobado» (VPS deploy, answering the D-034 question).
Decision: D-034 is lifted. Dispatch the VPS deploy on the first green main, then the REQ-013 Phase 3 Neon apply (dry run first), the live Python checks (P-039 ideas 29–31, dossier price check). Customer-visibility caution is lowered; hard rules (secrets, spend caps, FLUX base only, no Gemini images) stay.

## D-038 · One quote everywhere — pick the best model (owner) · 2026-10-10
Context: the guided 3D engine quotes ≈0.70× Python for the same idea; the dossier also notes an unexplained ×1.18 effect. Owner: «La cotización tiene que ser la misma en todos lados escoge la mejor».
Decision: a single pricing source of truth for classic, guided-python and guided-3D (same plan → same price, to the cent). An opus analysis compares both models against the Sempertex price list and real build counts, picks the more correct one, and every surface calls it; a cross-surface parity test pins it.

## D-039 · Beta: production is the same for everyone, everything on everywhere (owner) · 2026-10-10
Context: owner, 12:3x: «producción debe ser exactamente lo que debería ver todo el mundo incluido yo, el sistema está en beta y debe ser el mismo para todos los ámbitos así que enciende todo en todos lados».
Decision: no admin-only or flag-off features in production. Done 12:32: Neon `ajustes_runtime` rows `taller_hoja_armado = activo` and `guiada_motor = 3d` (GUIADA_MOTOR for all customers; supersedes the brief's "never flip to 3d" rule and D-028's flag-gating). Next: inventory every remaining off-by-default flag/env/role gate (Next + Python), turn on each, and keep the site-wide login (it guards paid FLUX/Gemini calls; not a feature gate). New features ship on by default from now on. The emergency kill `guiada_motor_corte` stays available, inactive. Prices: the 3D engine quotes ≈0.70× Python until D-038 (single quote) ships — accepted by the owner's ruling.
Applied 13:5x after the gate inventory (workflow wf_2c1a2e9f-d6d, 58 candidates; research/ciclo/INVENTARIO-GATES-2026-10-10.json): Vercel `MODULOS_ESCRITURA=abierta` (anyone logged in can generate/discard module renders; FLUX ≈US$0.08 each, 30/h per instance cap) and `NEXT_PUBLIC_SOLO_GUIADA` removed (classic view, catalogue, Happie, stats, admin pages and the view switch come back; both effective on the next production build); code change removing the solo-guiada mode in feat/sin-solo-guiada (guided keeps the Sempertex library gallery; login lands on /asistente). Not opened on purpose: the AI-feedback admin panel (ADMIN_PASSWORD) — it would let every customer read and export other customers' orders, comments and photos (third-party data, not a feature gate). CATALOGO_REPOS_RAG waits for REQ-013 Phase 4 (in progress), then goes on.

D-040 · 2026-10-13 · Bitácora temporarily lives inside the private metodologia monorepo (symlinked from ~/bitacora) so it syncs across machines; revisit a dedicated private repo.

D-041 · 2026-10-13 · Development of pictures is done entirely from this laptop from now on (owner); the Windows marathon clone is no longer an executor. Its unpushed work (judge-fix e7x) must be re-done or recovered.

D-042 · 2026-10-13 · Delegation picks the best model per situation regardless of the hosting session's provider; audits go to a different provider than the builder (owner). Router fixed in bt_agents.py.
