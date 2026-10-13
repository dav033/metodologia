---
id: REQ-014
status: stopped 2026-10-11 06:14 at cycle 26 (planned end 2026-10-12 16:44); not resumed
created: 2026-10-09
track: deep
---
# REQ-014 — 72h marathon — autonomous product development

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

> Source of truth: `C:/Users/davidt/bitacora/pictures/PROMPT-MARATHON-3-DAYS.md` (the owner's 72-hour brief).
> **Every session must read PROMPT-MARATHON-3-DAYS.md §2, §5 (models & escalation), §7 before working.**
> This REQ turns the brief into one requirement that the marathon supervisor (`bitacora.py run`) executes task by
> task. Where this file and the brief disagree, the brief wins.

## Problem & goal
demo-decoracion (Sempertex balloon decoration: Taller 3D pro tool at `/3d` + guided customer chat at `/asistente`)
has a long tail of known bugs, an engine that is only proven on curated scenes, an unfinished customer-edit phase of
the guided migration (REQ-007 Phase 5 WIP on `d2590cd4`), a competitor (BalloonBuilder) with 19 ranked features worth
adopting, 30 reference photos nobody may model by hand, no local-only AI provider, and one flat catalogue that mixes
Sempertex balloons with furniture and scenery. The owner is away for ~72 h and wants an autonomous, self-sustaining
development loop that fixes, hardens, extends and ships — with hostile review and product-manager agents feeding it.

**Success looks like:**
- Every W1 item from the brief closed with a test that fails without the fix; REQ-007 Phase 5 verified and shipped
  behind `GUIADA_MOTOR` (default `python`).
- A scenario matrix running ≥ 2 000 offline scenarios per sweep with a pass rate tracked per cycle in
  `research/escenarios/PASS-RATE.md`, every failure turned into a fix + regression test.
- BalloonBuilder quick wins shipped; the W4 harness producing a per-photo leaderboard with local Haiku; the Claude
  provider refusing every production/Vercel context by code; a `Repositorio` abstraction with data migrated without
  behaviour change; a switch dossier for the owner (no switch).
- The plan keeps growing from evidence (PM reviews, completeness critics, scenario sweeps) for the full 72 h; main
  stays green and Vercel Ready after every ship.

## Users / actors / stakeholders
- Owner (Sempertex product lead) — away; answers §11 questions in a batch; final say on switch and pricing.
- Decorators (pro users of the Taller 3D) — persona of the decorator-PM.
- End customers (guided chat `/asistente`) — persona of the customer-PM.
- Marathon supervisor + headless task sessions (Haiku → Sonnet → Opus escalation), antagonist/product/visual judges.

## Scope (in)

### US-1 (P1, Must) — W1: fix everything known broken
As the owner, I want every known defect closed with proof so that the product is trustworthy before it grows.
**Acceptance:**
- Given REQ-007 Phase 5 WIP `d2590cd4`, when it is merged onto the marathon branch, then
  `test-motor-guiada-ediciones`, `-ediciones-mapeo`, `-editar-ruta`, `test-ui-plan-motor3d` and the guard suites pass
  and the client integration follows a written design (`REQ-007/FASE5-INTEGRACION.md`).
- Given any item listed in brief §4 W1 (Kontext colour fidelity, sign fidelity, birthday photo→3D, sparse
  `columna_asimetrica`, salon tables as parametric sets, ideas 29/30/31, feedback UI reload/burst, P-033, P-029,
  P-030, P-017, P-027, P-006, P-011, giant files), when it is fixed, then a test that fails without the fix exists.
- Given any client component, when it renders or initialises state, then a static guard rejects
  `Date.now()/Math.random()/new Date()` there (P-033).

### US-2 (P1, Must) — W2: the engine works in "infinite" scenarios
As a decorator, I want the engine to build anything I ask without throwing, overlapping or miscounting.
**Acceptance:**
- Given a seed, when the scenario generator runs, then it produces the same specs (deterministic) covering structure
  type × size × density × colours (1–8, all finishes) × occasion × room size × furniture × lighting.
- Given a generated scenario, when it is built, then: no throw, counts within the per-structure bands of
  `PARIDAD-2026-10-09.md`, no intersecting boxes, inside the room, deterministic, under the time budget, honest notes
  for anything approximated.
- Given a sweep, when it finishes, then the pass rate is appended to `research/escenarios/PASS-RATE.md` and each
  failure class becomes a fix task with a regression test from the failing seed.
- Property tests exist for `armarEscena`, `armarDesdeEspec`, AI tool argument schemas and edit round-trips; an owner
  phrases corpus runs through the tools with a mocked model; `test-armado-escena-dorado` stays at 0 diffs or each diff
  is explained node by node.

### US-3 (P2, Should) — W3: everything worth copying from BalloonBuilder
As a decorator, I want pump/inflation data, dimensions, helium & ribbon, recipe cards, size profiles, light presets,
build sheets, palette→stock matching, tiered quotes and the rest of the 19 ranked ideas
(`research/balloonbuilder/notas.md` §"Top ideas") in our own UX.
**Acceptance:** quick wins first; each feature has a spec entry, tests, antagonist pass, product judge ≥ 8 and ships;
no text copied verbatim.

### US-4 (P2, Should) — W4: autonomous renders training set
As the owner, I want the app's own AI to model the 30 photos in `C:/Users/davidt/Downloads/iaiaaaaa` (never by hand)
and improve its tools from the failures.
**Acceptance:** a harness in `scripts/entrenamiento/` drives photo → `modelar_desde_foto` → refine turns → capture →
metrics (+ judge); failures are classified (reading, measuring, compiling, missing capability, viewer); a leaderboard
per photo lives in `research/entrenamiento/LEADERBOARD.md` with before/after triptychs; local only, Haiku, spend
capped per pass and logged.

### US-5 (P1, Must) — W5: local-only AI provider = Claude Haiku
As the owner, I want local development to use Claude Haiku (medium effort) while production stays on Gemini Flash.
**Acceptance:**
- The Claude provider resolves only when `!process.env.VERCEL && process.env.NODE_ENV !== "production"` **and**
  `IA_PROVEEDOR=claude`; any production/Vercel context refuses it (tested).
- Gemini declarations → Anthropic tool format adapter with tests (same names/args; zod is the source of truth);
  vision via image blocks; same audit wrappers, cost telemetry and guard inventory as Gemini.
- Model id = newest Haiku available to the key (research: `claude-haiku-5-5`, `research/w5-anthropic/NOTES.md`);
  `IA_LOCAL_ESFUERZO=low|medium|high`, default medium.

### US-6 (P2, Should) — W6: catalogue repositories
As the owner, I want Sempertex balloons separated from furniture, scenery and future packs.
**Acceptance:** an ADR/REQ (`REQ-013-catalogue-repositories`, started by the live-loop session 83576a42) defines `Repositorio`
(id, versioned manifest, item schema per kind, provenance/license, namespaced ids, own loader, RAG partition via an
additive `repositorio` column on `taller_items`, own pricing source, per-repository flags); existing data migrates
without behaviour change (golden tests + RAG `acierto@5` must not drop); Taller «Añadir» browses by repository, AI
tools filter by it, studio and guided chat see only `sempertex` unless a flag says otherwise.

### US-7 (P1, Must) — W7: finish the guided migration safely
As the owner, I want a switch dossier, not a switch.
**Acceptance:** Phase 5 shipped behind the flag → integration tests over the 28 ideas + proposals → refreshed parity
report → `REQ-007/DOSSIER-SWITCH.md` (counts, prices under D-026, desktop/phone screenshots, failure modes, rollback
drill evidence). `GUIADA_MOTOR` stays `python` for customers.

### US-8 (P1, Must) — organic, self-sustaining development
As the owner, I want the work to keep finding and planning its own next steps for 72 h.
**Acceptance:** PM reviews (decorator / customer, alternating), completeness critics and scenario sweeps append new,
well-formed, evidence-backed task lines to PLAN.md and deltas to `research/pm/BACKLOG.md`; ship tasks merge groups to
production per the deploy policy and confirm Vercel Ready.

## Out of scope
- Flipping `GUIADA_MOTOR` to `3d` for customers; changing customer-visible pricing policy (owner, §11).
- REQ-004 real user accounts (owner question (5)); REQ-006 venue photo → 3D.
- Hand-modelling any W4 photo; LoRA; Gemini generating images; any image generator other than fal.ai FLUX base models.
- Local `next build`; touching processes on :3010/:8000, Claude, Chrome or system processes.
- Paid evals/tests in verify gates (`test-inyeccion-prompt` never runs in sweeps).

## Requirements
- R1. When a task changes behaviour, the session shall add or extend a test that fails without the change.
- R2. When the scenario runner completes a sweep, the system shall record the pass rate and every failing seed.
- R3. If the Claude provider is requested in a production or Vercel context, then the resolver shall refuse it and
  fall back to Gemini.
- R4. While `GUIADA_MOTOR` resolves to `python`, the guided chat shall behave byte-identically to main.
- R5. When a customer edit is unsupported, the system shall answer «No pude: …» and leave the plan unchanged (D-023).
- R6. When data moves into repositories, `test-armado-escena-dorado`, the mobiliario suites and RAG `acierto@5` shall
  not regress.
- R7. When a PM review, completeness critic or sweep task finishes, PLAN.md shall have gained ≥ 3 new task lines
  tagged with its id (`origin: T<n>`) and `research/pm/BACKLOG.md` (or the sweep report) shall cite that id.
- R8. When a ship task runs, the feature branch shall be contained in `origin/main` (or `origin/maraton-preview` if
  the deploy policy forbids production) and the Vercel deploy shall be Ready.
- R9. If a paid run would exceed its §8 cap, then the session shall stop the run, log the spend and continue with
  free work.

## Edge cases & errors
- A task blocked at the top tier stalls the ship task that depends on it → the next growth task appends a new ship
  task whose `after:` excludes the blocked one.
- `ANTHROPIC_API_KEY` missing → W5 code still lands with mocked transports; paid W4 passes `task fail --blocked`.
- The verify `cwd` is the registered `demo-decoracion` path: it must be the marathon worktree (see Pre-launch).
- A Vercel deploy in Error after a ship → the ship task reads `vercel inspect --logs` and hotfixes before `task done`.

## Constraints

### Hard rules (verbatim from the brief §2)
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

### Spend caps (verbatim from the brief §8)
FLUX (fal.ai) US$3 · Gemini US$2 · Anthropic Haiku (local W4/W5) US$8 · total US$13/day. Stop and report if a cap is
reached; continue with free work.

### Owner answers (verbatim from the brief §11)
### Owner answers (filled in by the owner before launch — treat a filled line as final; empty = ask once, batched)
- (1) R-12 inflation in classic arches: 
- (2) GUIADA_MOTOR switch: no switch during these 72 h — bring the dossier (fixed).
- (3) `ANTHROPIC_API_KEY` in `demo-decoracion/.env.local`: 
- (4) BalloonBuilder features customer vs pro: 
- (5) REQ-004 real accounts: 
- Deploy policy: §6 step 5 (fast-forward to `main` = production deploy) is **authorized** unless this line says
  otherwise: 

### Deploy policy (as applied by this plan)
The deploy-policy line above is empty, so §6 step 5 is **authorized**: ship tasks fast-forward the marathon branch
to `main` (production deploy) and confirm Vercel Ready. If the owner fills that line with a restriction before launch,
ship tasks push `HEAD:maraton-preview` instead (their verify accepts either). Ship tasks are the **only** tasks allowed
to push; this is the owner-authorized exception to the session rule "never push". Every other task never pushes.

### Models & escalation
Brief §5: tasks start on Haiku (default effort); failed twice / same error / stuck → Sonnet `xhigh`; still failing or
hard architecture → Opus `xhigh`. Tasks marked `level: architecture` (W5 provider abstraction, W6 repository ADR +
abstraction, REQ-007 Phase 5 integration design) start on Opus. Judges run on Sonnet `xhigh` (Opus for architecture
reviews). Record every escalation in the day log.

### Testing (brief §7)
Run suites one at a time; `npx tsx --conditions=react-server scripts/test/<f>.ts` (UI/React tests without
`--conditions`); never `next build`; never `test-inyeccion-prompt`; known pre-existing failures: test-python-adapter
LoRA assert, test-ayudas-guiada, test-color-foto-etiquetas-mandan, test-ui-cotizacion-guiada. Verify commands run
under Windows `cmd.exe` (supervisor `shell=True`), from the registered repo path.

### Pre-launch checklist (HQ / owner, before `launch --mode marathon`)
1. The registered path of role `demo-decoracion` (`C:/Users/davidt/Downloads/pictures-workspace/demo-decoracion`) is
   on `fix/color-organico-conteo`, 166 commits behind `origin/main`, and is probably the checkout behind :3010. Create a
   dedicated worktree from `origin/main` on branch `feat/req-014-72h-marathon-autonomous-product-developm` with a
   `node_modules` junction, and point the role at it (`bitacora.py --project pictures workspace add demo-decoracion
   <path>`), so sessions and verify commands never switch the owner's checkout.
2. Stop the live `/loop` session 83576a42 (or let it finish its in-flight items and record them in STATE.md) so
   the loop and the supervisor never work the same items.
3. Fill the empty §11 owner answers (they are copied above; a filled line is final).
4. Put `ANTHROPIC_API_KEY` in `.env.local` of that worktree if W4/W5 paid runs should happen.

## Priorities & phases
Order of the plan (interleaved): W1 (REQ-007 Phase 5 first) → W2 → W5 → W6 → W3 quick wins → W4 harness → W7
dossier, with a PM review every ~8 tasks, a completeness critic every ~16 and a ship task after each group. MVP of
the first 24 h = Phase 5 shipped behind the flag, prerender guard, scenario matrix with a first pass rate, local
provider resolver + adapter, REQ-013 repository ADR finished with a PLAN, four BalloonBuilder quick wins.

## Timeline & dependencies
72 h from launch. Depends on: origin/main `b4433bc9`, WIP `d2590cd4`, W5 research `research/w5-anthropic/NOTES.md`,
BalloonBuilder notes `research/balloonbuilder/notas.md`, parity bands `REQ-007/PARIDAD-2026-10-09.md`, PM backlog
`research/pm/BACKLOG.md`.

## Assumptions
- The empty deploy-policy line means production deploys are authorized (the brief says "authorized unless this line
  says otherwise").
- The W6 ADR is `REQ-013-catalogue-repositories` (created by the live-loop session 83576a42 at 16:58, as the brief
  says); this marathon REQ was renumbered to REQ-014 to avoid the clash.
- The live `/loop` session 83576a42 (research/ciclo/STATE.md) already has work in flight on branches
  `feat/guiada-motor-ediciones` (e6g), `feat/escenarios-matriz` (e7a), `feat/bb-rapidos` (e7b), `feat/ia-local-claude`
  (e7c). A task whose work exists on one of those branches merges it and finishes/verifies it instead of redoing it.
  The loop and this supervisor must not both run (see pre-launch checklist).
- Offline tests do not need `NODE_OPTIONS=--use-system-ca`; it is kept only where the suite header asks for it.
- `fast-check` is not a dependency: property tests use a small seeded generator (`scripts/escenarios/`).

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered (brief §4–§6) |
| Edge cases | Covered |
| Acceptance criteria | Covered |
| Constraints | Covered (verbatim §2, §8, §11) |
| Priorities & phases | Covered |
| Timeline | Covered |

## Clarifications
### Round 0 — 2026-10-09
- Source: the owner's brief PROMPT-MARATHON-3-DAYS.md (written by session 46a78670 at the owner's request). Open owner
  questions stay in its §11 and are batched by the marathon, never blocking.
