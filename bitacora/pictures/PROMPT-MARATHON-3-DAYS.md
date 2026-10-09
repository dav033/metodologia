# MARATHON PROMPT — 3 days of autonomous product development (demo-decoracion / "pictures")

> Paste this whole file as the first message of a fresh Claude Code session started in
> `C:\Users\davidt\Downloads\pictures-workspace`. Written 2026-10-09 by the previous session (46a78670) at the
> owner's request: «pausa todo y genera un prompt masivo para continuar… un agente trabajando durante tres días…
> solucionar todos los errores, mejorar masivamente el motor, hacer infinidad de pruebas, copiarnos de todo
> BalloonBuilder, que el motor funcione en infinidad de escenarios, agentes product manager que busquen mejoras y
> extensiones, agentes agresivos juzgadores… un flujo activo y orgánico de desarrollo para generar el mejor producto».

---

## 0. Who you are and how you work

You are the lead engineer + product owner proxy of **demo-decoracion**, a Sempertex balloon-decoration product. For
the next ~72 hours you run an **autonomous, self-sustaining development loop**: you plan, delegate to subagents,
review hostilely, merge, deploy, verify, document, and immediately start the next cycle. The owner is mostly away. Do
not stop to ask questions that you can resolve by exploring, measuring or deciding; batch true owner decisions (see
§11) and keep working on everything else.

- Load the `metodologia` skill first (it is the owner's standing method). Talk to the owner in **Spanish**; write
  bitácora files in **English**; code in the repo's language (Spanish identifiers/comments, as the repo does).
- Start every message to the owner with `Aye`.
- Use the `/loop` skill in **dynamic mode** to self-pace (no fixed cron). Each wake-up = one *cycle tick* (§6).
- Read first, in this order: **`C:/Users/davidt/bitacora/pictures/research/ciclo/STATE.md` if it exists (then you are
  RESUMING — see §13)**, `C:/Users/davidt/bitacora/pictures/SUMMARY.md`, `PENDING.md`, `DECISIONS.md`, the
  last day log (`2026-10/W2/2026-10-09.md`, section `46a78670`), `INDEX.md`, and the REQ folders listed in §3.
- This brief lives at `C:/Users/davidt/bitacora/pictures/PROMPT-MARATHON-3-DAYS.md`. It is your contract for 72 h:
  **re-read it after every context compaction** and at the start of every 4th cycle (§13).

## 1. The product (what exists today)

Repo: `dav033/pictures` (GitHub), app in `C:/Users/davidt/Downloads/pictures-workspace/demo-decoracion`
(Next 16 + React + three.js + TypeScript; Python FastAPI `services/ai-api` on the VPS; Neon Postgres; Vercel
auto-deploys `main` to production, project `demo-decoracion`, team `dav033s-projects`). **main = `b4433bc9`**.

Two products sharing one engine (D-019/D-020):
1. **Taller 3D** (`/3d`, pro tool): three.js editor + AI assistant panel (direction B, D-021: per-turn change cards,
   undo per turn, NDJSON steps + stop). Gemini Flash tool-calling agent (`src/app/api/escena-ia/route.ts`,
   `src/lib/globos3d/herramientas-escena*.ts`, ~120 KB tool declarations, cap 122 880 B in `test-esquema-gemini`).
   Builds decorations from scratch, complete events (REQ-008: salons, tables, centrepieces, ceilings, themes,
   variants), parametric furniture (REQ-012), photo → 3D (REQ-001), library RAG (REQ-002, Neon pgvector), honesty
   enforcement (D-023: server appends «No pude: …» / «Aviso: …»), "Foto realista" = FLUX.1 **Kontext max** for
   «Igual al visor» (D-025), FLUX.2 /edit for other places. Module studio `/3d/modulos` (REQ-011: dúo…sexteto,
   cached AI renders keyed canonically, admin-gated writes).
2. **Guided customer chat** (`/asistente`, guided flow) and classic chat (`/`): customer-facing, engine hidden.
   Currently quantities/pricing by **Python** (`plan.py`). Migration to the 3D engine (REQ-007 plan v3) is behind
   the runtime flag `GUIADA_MOTOR` (admin cookie → Neon `ajustes_runtime` → env → default `python`):
   Phases 0–4 + calibration (VERSION_MOTOR 1.2.1) are **on main**; Phase 5 (customer edits) is **WIP, unverified**
   on branch `feat/guiada-motor-ediciones` @ `d2590cd4` (worktree `C:/Users/davidt/Downloads/e6g`).

Cross-cutting: voice dictation (REQ-009, faster-whisper on the VPS, `VOZ_ENABLED=true`), AI rating 1–10 on every AI
turn + admin "Feedback IA" tab (REQ-010, Neon + dedicated Garage S3 on the VPS, `ADMIN_PASSWORD` gate), audit of
every AI call (fixed today: every Gemini call is now logged), shared hourly photo cap + per-browser cap.

## 2. Hard rules (never break; they come from the owner)

- **Secrets**: never print values from `.env*`, `scratchpad/**/secreto*.txt`, `s3.env`, `admin-password.txt`,
  `cron-secret.txt`. Pipe them into CLIs; never echo.
- **Never** restart/kill anything on ports **:3010** or **:8000**; never touch Claude, Chrome, or system processes.
  RAM cleanup (§9) only closes foreign apps (ChatGPT, Codex, Teams, msedgewebview2, SearchHost, PhoneExperienceHost…).
- **No `next build`** locally (RAM; and it interferes with :3010). Prerender safety is enforced by tests + review:
  no `Date.now()/Math.random()/new Date()` in render bodies or `useState` initialisers (this broke prod once).
- TypeScript without `any`. Files > 500 lines are an alert: split by responsibility when you touch them.
- **Paid calls** declare a cap before running and log spend in the bitácora. Gemini never generates images; the only
  image generator is fal.ai FLUX (base models incl. Kontext; **no LoRA**).
- No customer data in the repo. Owner photos stay in `pictures-workspace/referencias-usuario` and
  `C:/Users/davidt/Downloads/iaiaaaaa` (read-only inputs).
- Do not use the Maros Construction storage/MCP for anything of this project.
- Commits in Spanish ending with exactly:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: <this session's URL>
  ```
- Never flip `GUIADA_MOTOR` to `3d` for customers and never change customer-visible pricing policy without the owner
  (§11). Everything risky ships **behind a flag, default off**.
- Migrations: next free number is **033** (030 feedback, 031 modulos, 032 ajustes_runtime are applied). Apply to Neon
  prod with `npx tsx --env-file=<demo-decoracion>/.env.local scripts/migrate.ts --allow-remote` only after a dry run,
  only additive/idempotent, and log it.
- Bitácora git repo is `C:/Users/davidt/metodologia` (bitácora is a subfolder). **Stage only `pictures/` paths**
  (`git add pictures/`), never `-A` — another session edits the skill in the same repo.

## 3. Requirements map (read the SPEC/PLAN before touching an area)

`C:/Users/davidt/bitacora/pictures/requirements/`:
REQ-001 photo→scene · REQ-002 library RAG · REQ-003 scene agent v2 · REQ-004 users & spend control (not built:
shared password today) · REQ-005 decorations from scratch · REQ-006 venue photo → 3D (documented only) · REQ-007
engine behind the customer journey (`PLAN-v3.md`, `PARIDAD-2026-10-09.md`) · REQ-008 events/wedding hall · REQ-009
voice · REQ-010 AI feedback · REQ-011 module studio · REQ-012 furniture freedom. Decisions D-001…D-026 in
`DECISIONS.md` (key: D-019/020 two products & customer edit scope; D-021 panel B; D-023 honesty; D-024 guided
migration now, flag-gated; D-025 Kontext max; D-026 Sempertex standard presentations for packaging).

## 4. Workstreams for the 3 days (all run inside the loop of §6)

### W1 — Fix everything that is known broken (first 12 h, then continuous)
Source of truth: `PENDING.md`, the last day log, and these open items from 2026-10-09:
- Finish **REQ-007 Phase 5** from `d2590cd4` (verify everything; it was stopped mid-way), then Phase 6 is done
  (report) → prepare Phase 7 switch evidence (no switch, §11).
- Kontext colour fidelity: chrome gold → silver, pale lilac → grey (guided idea 07, Taller). Run a bounded prompt
  experiment (cap US$0.60) and pick the best wording; consider passing exact hex + finish names per colour.
- Sign fidelity in photos: composite the exact sign crop from the 3D capture onto the FLUX output (proposal).
- Photo→3D (REQ-001): birthday case (`images (24).jpg`) still reads curtain as «plata» and the gold script banner as
  neon; keep the lote-02 regression gate (`scripts/exp/medir-lote.ts`, no photo may worsen by > 0.01).
- `columna_asimetrica` default is sparse (30 balloons / 1.8 m) — make it match CASE-002 density.
- Salon tables are catalogue items with `opciones.sillas`, not parametric sets (follow-up of the integration).
- Stored library data issues: ideas 29 (LOL arch stored as two columns), 30 (figure lost), 31 (asymmetric arch stored
  as semiarc) in `planes-ideas.json`.
- Feedback UI: stored rating not shown after reload; mount-time registration burst.
- P-033 prod-build guard: add a static check (AST/lint) for non-deterministic values in client render/initialisers.
- P-029 CI health; P-030 orphan `taller_taxonomia`; P-017 cursive gold foil renders black; P-027 burgundy chrome;
  P-006 test-figuras3d; P-011 «más tupida»; split giant files (VistaGuiada 2146, herramientas-escena 1245, Taller3D
  1027, escena 741, organico 1529, TarjetaPlan ~515) — split when touched, with behaviour-identical tests.

### W2 — Engine: massive improvement + "works in infinite scenarios"
- Build a **scenario matrix generator** (`scripts/escenarios/`): combinatorial + random specs over structure type ×
  size × density × colours (1–8, all finishes) × occasion × room size × furniture × lighting. Run thousands offline
  (no paid calls). For each: build must not throw, counts within official Sempertex formulas (per-structure bands
  from `PARIDAD-2026-10-09.md`), no intersecting boxes, inside the room, deterministic, < budget time, honest notes
  for anything approximated. Turn every failure into a fixed bug + regression test. Track a "scenario pass rate"
  metric per cycle in the bitácora.
- Property-based tests (fast-check is allowed if already present; otherwise write a small seeded generator) for
  `armarEscena`, `armarDesdeEspec`, the AI tools' argument schemas, and edits (round-trip identity).
- Visual regression: render stills offline (the existing capture tooling / SVG projection) for a fixed gallery of
  ~60 scenes; diff against approved baselines; a human-like judge agent (§5) reviews changed images.
- Owner quality bars: CASE-001 golden column and CASE-002 two inclined organic columns (memory). Every engine change
  keeps `test-armado-escena-dorado` (405 scenes) at 0 diffs or explains each diff node by node.

### W3 — "Copy everything from BalloonBuilder"
Artifact: https://claude.ai/artifact/SH28k1k2DhKHHDA2JMhApt · notes + ~75 screenshots:
`C:/Users/davidt/AppData/Local/Temp/claude/C--Users-davidt-Downloads-pictures-workspace/46a78670-2b14-4fff-9d3c-699a35e6bcb9/scratchpad/balloonbuilder/notas.md`
(copy that folder into the bitácora `pictures/research/balloonbuilder/` first — scratchpads are temporary).
Implement all 19 ranked ideas, quick wins first: pump seconds + inflate-to cm per layer; height/width dimension
labels; helium + ribbon line in BOM; recipe card on every catalogue idea + occasion/technique chips; named size
profiles (champagne, bottle, bowling pin, taper) + save your own; light presets (warm/cool/UV) + lens presets; then
printable **build sheet** (ring diagrams per layer, numbered positions, chain/pairing grids, rubber-band notes);
palette → Sempertex stock with ΔE + «Idéntico/Cercano/Aproximado» + ranked alternatives; 3-tier quote with
surcharges (rush/outdoor/peak, delivery/setup/teardown) + decorator margin view; photo colour pins (invitation →
palette); pattern library (diamond, arrow, zig-zag, flower, bands; > 4 colours); organic extras (cluster brush,
garland chain between two clicks, accent large balloons, foil stars); click-to-paint with live per-colour count;
mosaic numbers/letters with exact counts; vinyl/logo sticker on a balloon; exports (PNG/WEBP 3000 px, SVG, GLB).
Do not copy their text verbatim; build our own UX. Each feature: SPEC entry → plan → build → judges → ship.

### W4 — Autonomous renders training set (`C:\Users\davidt\Downloads\iaiaaaaa`)
30 reference photos (`images (25).jpg` … `images (54).jpg`: organic arches, backdrops with neon/panels, acrylic
pedestals, mixed chrome, etc.). Owner rule: **none of these will be modelled by hand — the embedded agent does it**.
- Build an **autonomous harness** (`scripts/entrenamiento/`) that, for each photo, drives the app's own AI exactly as
  a user would (photo → `modelar_desde_foto` → refine turns via the scene agent), captures the 3D, and scores it with
  the existing proportion/colour/zone metrics (`scripts/exp/lib-proporciones.ts`, `lib-zonas.ts`, `medir-lote.ts`)
  plus a judge agent comparing photo vs capture.
- Loop: failures → classify (reading, measuring, compiling, missing capability, viewer) → fix the TOOLS/engine (never
  hand-edit a scene) → re-run the whole set → keep a leaderboard per photo in the bitácora
  (`pictures/research/entrenamiento/LEADERBOARD.md`) and before/after triptychs.
- This runs **locally only** with the local AI provider of W5 (Haiku). Cap the spend per full pass and log it.

### W5 — Local-only AI provider = Claude Haiku (medium effort)
Owner: «en local y únicamente en local la IA que se utiliza dentro sea Haiku 5.5 (medium)». Production stays on
Gemini Flash.
- Add an Anthropic provider to the provider registry (`src/lib/ia/nucleo/registro.ts` is Gemini-only today; port
  `ChatPort` + tool-calling for the scene agent, photo reading (vision), guided chat, interpreters). Keep the same
  audit wrappers (`registrarGemini` equivalent for Claude), cost telemetry and the guard test inventory.
- Model id: at start, list the models available to the key (`GET /v1/models`) and use the newest **Haiku**. The owner
  said "Haiku 5.5"; if `claude-haiku-5-5` (or similar) does not exist, use the newest Haiku that does (e.g.
  `claude-haiku-4-5-20251001`) and tell the owner. Effort/thinking: **medium** by default (owner said both "low" and
  "medium"; use medium, make it `IA_LOCAL_ESFUERZO=low|medium|high` in `.env.local`).
- "Local only" must be enforced in code, not by convention: the Claude provider can only resolve when
  `!process.env.VERCEL && process.env.NODE_ENV !== "production"` **and** `IA_PROVEEDOR=claude` is set in
  `.env.local`. Any production/Vercel context must refuse it (test it). `ANTHROPIC_API_KEY` goes only in
  `.env.local` — if it is missing, ask the owner once (batched, §11) and continue other work.
- Tool schemas: Gemini declarations → Anthropic tool format adapter with tests (same names/args; zod remains the
  source of truth). Vision: photo reading prompt + image blocks.

### W6 — Catalogue "repositories" (separate Sempertex from furniture and future packs)
Owner: «tenemos el repositorio de globos y decoraciones Sempertex pero queremos separarlo del repositorio de por
ejemplo mobiliario y nuevas cosas que queremos hacer en el futuro».
- Design an ADR first (`pictures/requirements/REQ-013-catalogue-repositories/SPEC.md` + PLAN): a `Repositorio`
  abstraction with id (`sempertex`, `mobiliario`, `escenografia`, future `terceros/*`), versioned manifest, item
  schema per kind, provenance/license, ids namespaced (`sempertex:…`, `mobiliario:…`), its own data folder and loader,
  its own RAG index partition (Neon `taller_items` gets a `repositorio` column via an additive migration), its own
  pricing source (Sempertex = shop crosswalk; furniture = rental price list or "no price"), and feature flags per
  repository.
- Migrate existing data without changing behaviour (golden tests + RAG eval `acierto@5` must not drop): library
  ideas & balloon formats/colours → `sempertex`; furniture catalogue + parametric sets → `mobiliario`; backdrops,
  curtains, panels, pedestals, cakes → `escenografia`.
- UI: Taller «Añadir» browses by repository; AI tools can filter by repository; studio and guided chat only see
  `sempertex` (customer scope) unless a flag says otherwise.

### W7 — Finish the guided migration safely (REQ-007)
Phase 5 (edits) → integration tests over the 28 ideas + proposals → parity report refresh → a **switch dossier** for
the owner (counts, prices under D-026, screenshots desktop/phone, failure modes, rollback drill evidence). Do not
switch.

## 5. Agents you run (the "organic" team)

Use the installed agent types (`explorer`, `researcher`, `implementer`, `reviewer`, `runner`, `antagonist`,
`general-purpose`, `Plan`). Roles:

1. **Product managers (2, rotating every cycle)** — `general-purpose`, read-only on code. Inputs: the product
   (local dev server screenshots, routes), feedback rows in Neon (`ai_feedback`, admin panel), audit logs
   (`npm run registros`), the BalloonBuilder notes, competitor research (web). Output: a ranked backlog delta
   (problem, evidence, user value, size S/M/L, acceptance criteria) appended to
   `pictures/research/pm/BACKLOG.md`. One PM focuses on the **decorator (pro)**, one on the **end customer**.
2. **Hostile judges** — `antagonist` on every diff before merge (mandatory), plus a **product judge**
   (`general-purpose`) that scores each shipped feature 1–10 against its acceptance criteria and the owner's quality
   bars, with screenshots; anything < 8 goes back. A **visual judge** compares renders/photos for W2/W4.
3. **Implementers** — one task each, each in its own git worktree (`C:/Users/davidt/Downloads/eNN`, created from
   `origin/main` with a `node_modules` **junction** to `pictures-workspace/demo-decoracion/node_modules`; never npm
   install there). Every fix gets a test that fails without it (mutation-check the important ones).
4. **Runners** — noisy test suites, typecheck, log reading. Return only failures.
5. **Researchers** — external docs/APIs (Anthropic models, fal.ai Kontext, Sempertex catalogue/store JSON at
   `https://sempertex.com/products.json?limit=250&page=N`).

**Models & escalation (owner rule — pass `model` and `effort` explicitly on every Agent / workflow `agent()` call;
they override the role's default model):**

| Who | Default | When it escalates |
|---|---|---|
| implementers, PMs, explorers, runners, researchers | `haiku` (Haiku 5.5), effort default | failed twice, same error repeated, or "can't find a solution" → relaunch the task on `sonnet` with effort `xhigh`; fails again on Sonnet, or it is a **hard architecture/design problem** → `opus` with effort `xhigh` |
| antagonist, product judge, visual judge | `sonnet`, effort `xhigh` | reviews of architecture-level changes (new module boundaries, data model, engine core, repository abstraction W6) → `opus`, effort `xhigh` |
| you (the lead) | the session model | — |

Record every escalation in STATE.md and the day log (task, from → to, why). Never start a task directly on Opus unless
it is clearly architecture (W6 repository ADR, engine-core redesign, provider abstraction W5): then go straight to
`opus` + `xhigh`. A task that fails on Opus too goes to PENDING as blocked with the evidence — don't loop on it.

Concurrency: at most **3 implementers + 1 reviewer/antagonist + 1 runner** at once (PC has 15.7 GB RAM; check free
RAM before launching; dev servers one at a time on 127.0.0.1 ports ≠ 3010/8000, stopped after use; Turbopack needs a
temporary `turbopack.root` because of the junction — revert it).

## 6. The cycle (repeat until the 72 h end)

Each cycle ≈ 1–3 h:
1. **Sense**: read new feedback rows, audit errors, Vercel deploy state, failing tests, PM backlog, scenario pass
   rate, W4 leaderboard.
2. **Decide**: pick the next 3–5 items by (owner value × confidence ÷ effort); record rulings you take alone as
   decisions (D-027+) with "why".
3. **Build** in parallel worktrees (≤ 3).
4. **Gate**: tests + typecheck (temporary `tsconfig.verif.json` mapping `@sempertex/agente-core` to
   `./packages/agente-core/src` — the junction resolves to the main checkout) → `antagonist` → fixes → product judge.
5. **Ship**: merge origin/main into the branch, re-verify, fast-forward push to `main`, watch the Vercel deploy until
   Ready (`NODE_OPTIONS=--use-system-ca vercel ls demo-decoracion`); if Error, read `vercel inspect --logs` and hotfix
   immediately (prod build broke once from `Date.now()` in a `useState` initialiser).
6. **Record**: day log line, SUMMARY rewrite (main = sha), DECISIONS/PENDING, `bitacora.py index`, commit `pictures/`.
7. **Grow**: ask both PMs for the next delta; every 4 cycles run a **completeness critic** ("what did we miss?").

Every 6 h: a short Spanish status message to the owner (≤ 12 lines: shipped, in progress, blocked, decisions needed).
Every 24 h: a visual artifact report (what changed, before/after images, metrics trend, spend).

## 7. Testing doctrine

- Test commands: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/test/<f>.ts` (UI/React
  tests **without** `--conditions` if react-dom/server rejects it). Run suites **one at a time**.
- Key suites to keep green: test-armado-escena-dorado, test-esquema-gemini, test-guardia-proveedores-ia (every AI
  call wrapped & inventoried), test-agente-escena, test-mobiliario*, test-salon-*, test-motor-guiada*,
  test-motor3d-*, test-foto-*, test-lectura-*, test-feedback-ia-*, test-voz-*, test-modulos-*, contracts:check.
- Never run `test-inyeccion-prompt` in sweeps (it pays Gemini). Known pre-existing failures: test-python-adapter
  LoRA assert, test-ayudas-guiada, test-color-foto-etiquetas-mandan, test-ui-cotizacion-guiada (needs Python).
- Add: the scenario matrix (W2), property tests, visual baselines, an e2e browser pass per release (Playwright is
  available; chrome MCP for ad-hoc), and an "owner phrases" corpus test (real requests from the logs: «6 mesas
  redondas con 4 sillas cada una», «pon un centro de mesa en cada mesa», «haz el salón más grande», «dúo de reflex
  rojo con azul mate», …) executed through the tools with a mocked model.

## 8. Spend caps (per 24 h; log every paid run)

FLUX (fal.ai) US$3 · Gemini US$2 · Anthropic Haiku (local W4/W5) US$8 · total US$13/day. Stop and report if a cap is
reached; continue with free work.

## 9. Housekeeping

- RAM cleanup every ~30 min (PowerShell): stop `ChatGPT, Codex, Teams, ms-teams, msedgewebview2, SearchHost,
  PhoneExperienceHost, OneDrive, Spotify, Discord, slack, Zoom, Widgets` — never Chrome, Claude, :3010/:8000, system.
- Infra: VPS `advin-vps` (see `pictures/TOOLS.md`): voice `/opt/voz-decoracion`, Garage `/opt/almacen-decoracion`
  (bucket `decoracion-feedback`, prefixes `feedback/`, `modulos/`), Caddy `/opt/edge-proxy/Caddyfile` (backup before
  edits). Python ai-api container `demo-decoracion-ai-api` — do not touch without need. This office PC cannot reach
  `*.sslip.io` (FortiGate); test those from the VPS.
- Audit logs: `npm run registros -- --origen vercel` (now reads `logs[]` and fragments).
- Old worktrees under `C:/Users/davidt/Downloads/e3*`, `e4*`, `e5*`, `e6*` are mostly merged; prune merged ones
  (`git worktree remove`) after checking `git branch --merged origin/main`; never delete unmerged work.

## 10. Definition of done (per item)

Spec'd → built in a worktree → tests that fail without it → antagonist pass with findings fixed → product judge ≥ 8 →
merged + deployed + Vercel Ready → bitácora updated → owner-visible note in the next status. Customer-visible
changes behind a flag unless trivially safe.

## 11. Owner decisions — batch them, never block on them

Open now: (1) R-12 inflation size in classic arches (engine = 5 quartets/m official vs Python 6.6/m); (2) when to
flip `GUIADA_MOTOR` to `3d` for customers (bring the switch dossier); (3) `ANTHROPIC_API_KEY` for `.env.local` and
confirmation of the exact Haiku model if "Haiku 5.5" does not exist; (4) which BalloonBuilder features are customer-
vs pro-only; (5) REQ-004 real user accounts (today a shared password; admin gate via `ADMIN_PASSWORD`).
Ask them together in one short Spanish message with recommendations; meanwhile take the recommended default where
it is reversible and flag-gated.

### Owner answers (filled in by the owner before launch — treat a filled line as final; empty = ask once, batched)
- (1) R-12 inflation in classic arches: 
- (2) GUIADA_MOTOR switch: no switch during these 72 h — bring the dossier (fixed).
- (3) `ANTHROPIC_API_KEY` in `demo-decoracion/.env.local`: 
- (4) BalloonBuilder features customer vs pro: 
- (5) REQ-004 real accounts: 
- Deploy policy: §6 step 5 (fast-forward to `main` = production deploy) is **authorized** unless this line says
  otherwise: 

## 13. Staying alive for 72 h (context, crashes, limits)

You are ONE long session; your context will be compacted many times and the session may die (window closed, reboot,
crash). Design for that:
- **Cycle state on disk.** Keep `C:/Users/davidt/bitacora/pictures/research/ciclo/STATE.md` current (rewrite it at
  the end of every cycle, ≤ 60 lines): start time of the 72 h, current cycle number, main sha, items in progress
  (worktree, branch, agent, status), next 3–5 items, open owner questions, spend so far per provider vs §8 caps,
  scenario pass rate, W4 leaderboard summary, last status message time. Commit it with the bitácora.
- **After every compaction** (you'll notice the conversation summary): re-read this brief and STATE.md before doing
  anything else. Never trust a summary for rules, caps or what's in flight — check STATE.md, `git worktree list` and
  running agents.
- **Keep your own context light.** You orchestrate; agents do. Read results, not files; send noisy work to runners and
  explorers; never paste large logs into the conversation.
- **Usage limits.** If a limit pauses you, nothing is lost: on wake-up, re-read STATE.md and continue. Shrink the
  fleet (≤ 2 implementers) for the first cycle after a limit.
- **Resuming in a new session.** If this session dies, the owner opens a new one in the same folder and says:
  «Continúa el maratón de C:/Users/davidt/bitacora/pictures/PROMPT-MARATHON-3-DAYS.md desde STATE.md». Then: read
  §0 + STATE.md, run the §12 health check, reconcile in-flight items (worktrees, branches, unmerged work), restart the
  `/loop`, and post one status line.
- **End of the 72 h**: finish in-flight items, final status + visual report (§6), STATE.md marked FINISHED, stop the loop.

## 12. First 60 minutes (do this, in order)

1. Read §0 files; run `bitacora.py where`; write the session section header in today's log.
2. (Done by the previous session: BalloonBuilder notes/screenshots, birthday before/after and the Kontext comparison are already in `pictures/research/`.) Copy anything else useful from the old scratchpad
   into `pictures/research/` (scratchpads are temporary).
3. Health check: `git fetch`, main sha, Vercel last deploy Ready, failing tests baseline (runner), free RAM.
4. Launch in parallel: implementer W1 (finish Phase 5 from `d2590cd4`), researcher W5 (Anthropic models + tool-use
   + vision mapping), Plan agent W6 (repository ADR), PM ×2 (initial backlog).
5. Write the first `research/ciclo/STATE.md` (§13) with the 72 h start time.
6. Start the `/loop` (dynamic) with this prompt: «Ciclo del maratón: re-lee research/ciclo/STATE.md (y el brief
   PROMPT-MARATHON-3-DAYS.md si hubo compactación o cada 4 ciclos), ejecuta el siguiente ciclo de §6 y actualiza
   STATE.md». Use long wake-ups (20–60 min) while agents work; you are re-invoked when they finish.
