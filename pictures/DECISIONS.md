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
