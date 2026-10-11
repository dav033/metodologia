# Completeness critic - cycle 24 (session 83576a42, T+32 h, main 59a06582, ~40 h left; marathon ends 2026-10-12 16:44)
Sources: brief, STATE c24, CRITICO-c4/c12, PENDING, DECISIONS D-027..D-039, pm/BACKLOG (c0,c8,c20), TRACKER, LEADERBOARD, DOSSIER-SWITCH, JUEZ, day logs 10-10/10-11,
`git log/ls-tree/show origin/main` (49 commits since start), package.json, checks.yml, deploy.yml. Read-only; nothing paid or run. "Not found" = absent from those.

## Headline
24 cycles bought breadth; what is missing is the safety net around a production that D-039 made "everything on for everyone". (1) Nobody reads prod signals each cycle
and nobody will after 16:44 Sunday. (2) The real gate lives in the lead's session, not in CI (the 405-scene golden is not in CI). (3) The customer money path is live with
no judge score >= 8 and no prod chat probe. (4) Every spend cap is per warm serverless instance. Items 1-5 are mostly S and protect everything else.

## Top 8 (ranked by value x confidence / effort)
1. Prod pulse + handoff canary - value H - size S (script) + M (cron)
   Evidence: one system check in 24 cycles (c18, found catalogue empty on Vercel, /3d crash, plan_audit_log empty 20 h); no recorded read of ai_feedback, `registros --nivel error`
   or Vercel logs since (grep STATE, logs, BACKLOG); the owner found the quince failure himself (10-10 21:52). Pieces exist: `registros`, `analizar-feedback-ia.ts`, `stack-check.ts`, `e2e:humo`.
   Accept: `npm run prod:pulso` (read-only, last 6 h) prints error lines by event for Vercel/VPS/Python, ai_call_log by proveedor/flujo/resultado with sum(coste_estimado), ai_feedback
   ratings <= 4 with comments, plan_audit_log rows vs plans, `GET /api/guiada/motor` source, free `/api/plan-idea` price of 5 fixed ideas vs a fixture; exit 1 past thresholds; lead runs it
   first in every cycle (STATE line); a 30-min GitHub Actions cron with the free probes only is live before the marathon ends so Monday does not start blind.
2. Make the lead's gate the CI - value H - size S (wire) + M (script)
   Evidence: brief 7 "keep green": test-armado-escena-dorado, test-honestidad-escena, test-agente-escena, test-herramientas-escena, test-foto-a-escena, test-lectura-foto are named in no
   package.json script or workflow on main; ~265 of 499 scripts/test/*.ts are in no npm script. Pushed red twice (888637d0 -> b2ee1e39, e4216c98 -> 95a8ad57); 59a06582 was caught only by the local chain.
   Accept: committed `npm run gate` (PowerShell-safe: git rev-parse SHA, py -3.13, tsc verif config incl scripts/**/*.tsx, eslint changed, kontext:test, dorado, honestidad, globos3d, catalogo,
   motor3d, contracts, e2e:humo when :3010 is up; stops at first red) + the six suites and an "unwired test" check in checks.yml; mutation check: change one golden node -> CI red.
3. Customer money path: judge >= 8 + prod probe - value H - size M
   Evidence: /asistente judged 5/10 (JUEZ 10-10, Python down, plan card never seen) and never re-scored though it runs the 3D engine + D-038 prices for all; prod smoke = 13 PASS / 0 / 2 SKIP, chat skipped
   (README: chat only runs local-Claude or --con-chat); P-066 prod run open; P-042 undo not identity; NC-2 (7-year-old unicorn -> baby-shower garlands) open; test-frases-dueno has 8 phrases.
   Accept: sonnet-xhigh judge on prod, desktop + phone: idea -> 3D plan card -> price -> chat edit -> undo -> "Ver como quedaria" -> rating, each >= 8 or a fix item; one `e2e:humo --con-chat`
   (cap US$0.05, logged) asserting card price == Taller "Precio en la tienda" for 3 ideas; P-042 fixed (restore stored spec); corpus grown to >= 40 phrases mined from prod conversations.
4. Durable spend guard - value H - size M
   Evidence: tope-fotos-hora.ts and tope-imagenes-navegador.ts count in globalThis ("por instancia"); with MODULOS_ESCRITURA=abierta any password holder can run FLUX renders (~US$0.08) and
   discard cached ones (modulos-render/route.ts:135, same gate); NP-3 not built; /api/guiada/motor/imagen not in the durable audit (P-062); STATE spend (~US$1.39) excludes visitor spend.
   Accept: Neon-backed hourly + daily counters (global and per browser, additive migration) on render-3d-imagen, modulos-render, guiada/motor/imagen, escena-desde-foto; 429 "No pude: limite..." with wait
   time; test with two simulated instances; every FLUX call in ai_call_log; discard only by the session that created the render.
5. Rollback drill + persisted-state compat test - value H - size S
   Evidence: DOSSIER 4 "Drill status: not done" (and its text still says P-045 is in review); NC-4 not started; D-035 pre-flip check never recorded; guiada_motor=3d for all since 10-10 12:32;
   `propuesta` (eb7d0abd) sits in a `.strict()` saved-state schema, so a code revert wipes open customer chats.
   Accept: timed prod drill at low traffic: kill on -> `GET /api/guiada/motor` = {python, corte} on 3 fetches <= 35 s, open chat shows "Recalcular mi plan" and keeps data, kill off restores; timings
   in DOSSIER (section 4 rewritten); `test-estado-guardado-compat`: previous-release saved-state fixtures parse with the new schema and every new field is `.optional().catch`.
6. W4 transfer + pass 3 + triptychs - value M-H - size M
   Evidence: LEADERBOARD scores are Haiku/CLI, production reads photos with Gemini Flash; last pass b3f66d39 predates figures 0e47760f, P-054, the quince fix; "Captura del visor: pendiente en todas las
   filas"; no triptychs, no photo-vs-capture judge (brief W4); 24/30 still capacidad_faltante.
   Accept: pass 3 on current main (Haiku, US$0, same metrics, deltas per photo); 8-photo Gemini pass (cap US$0.60 of the US$2) with delta vs Haiku; >= 5 triptychs in research/entrenamiento/triptychs/.
7. Held and dead work - value M - size M
   Evidence: P-039 ideas 29/30/31 held as "customer-visible" but D-037/D-039 removed that reason; PENDING lists shipped P-010/015/018/021/031 as open and ends with 6 duplicated boilerplate lines; 47 local
   branches not ancestors of origin/main + 99 worktrees (c12 said 98) with no audit recorded; non-squashed leftovers: datos/recolector-estructuras 15, exp/kontext-color 13, split-vercel-frontend 5, fase-c 4.
   Accept: research/ciclo/RAMAS.md (branch -> shipped-as sha by tree diff / keep / close + note; `git cherry` is wrong after squashes); merged worktrees pruned to < 30; 29/30/31 regenerated through the
   local Python (arrancar-ai-api.py) with goldens changed only for those three; PENDING cleaned.
8. W3 money flow, then W2 visual baseline - value H (pro) - size M each
   Evidence: no 3-tier / surcharge / margin code in src (grep recargo|margen|niveles); TRACKER 5 of 19 done (3,4,9,11,12) and stale since 10-10 00:04; #5/#6 untouched 32 h after c12 flagged them; zero
   baseline images on main (git ls-tree: no png/webp outside public/design; only evaluacion/linea-base, old colour work).
   Accept: Taller "Cotizar": scene BOM -> 3 tiers + surcharges (rush/outdoor/peak, delivery/setup/teardown) + margin view on the D-038 pricer (parity test, on by default per D-039); then 20 committed scene
   baselines (Playwright capture, tolerance, judge on diffs) as c12 #6 scoped it.

## Still open from c4 / c12
- c4 #1 / c12 #2 product judge: build sheet 8, Taller cards 8, recipe/light 8; never scored: 3D plan card, "Ver como quedaria", customer edits, kill banner, honesty wording, rating UI, NP-1, curated pricing.
- c4 #5 / c12 #6 visual regression: none. e2e per release exists (bbb3fe4d, local only, not CI, chat skipped on prod). Matrix metric row not updated since c4 (CI floor 0.97 only).
- c4 #4 W3: 13 of 19 tracker rows open (2 dE, 5/6 tiers+margin, 7 pins, 8 mosaic, 10 live counter, 13-19); PRO-06 PNG/GLB part (no GLTFExporter in src).
- c4 #9 / c12 #9 W1: no commit since start on sign composite, parametric salon tables, P-017 cursive gold black, P-027, P-011, P-006, birthday curtain/banner (subjects searched).
- c12 #3 / W7 dossier: stale, drill and judge screenshots missing (item 5); CUS-07 sencilla/media/lujosa never viewed; CUS-05, CUS-10, CUS-13 not started.
- c12 #8 / c4 #14-15 hygiene: branch + worktree audit, PENDING cleanup, spend reconciliation against ai_call_log all undone; PM rotation c0/c8/c20 only (brief: every cycle; c24 due).
- Giant files grew: VistaGuiada 2146 -> 2187, herramientas-escena 1245 -> 1297, TarjetaPlanDecoracion 1591; W6 phases 6-7 (price source per repository, qualified ids) not started.
- Closed since c12 (credit): W4 pass 2 + diagnostics, D-036 stop-rule, e2e humo, CUS-03/04/14, NC-3/NC-5, CI green, CLI transport, owner-phrases corpus (8), P-049/P-045.

## Risks in production now (everything on for everyone, D-037/38/39)
- Spend: caps are per instance (item 4); MODULOS_ESCRITURA open; shared site password. Check: `ai_call_log` last 24 h `SELECT proveedor, flujo, resultado, count(*), sum(coste_estimado) ... GROUP BY 1,2,3`
  and the fal.ai usage page (the lead's US$1.39 is not visitor spend).
- Deploy skew: Vercel builds on push to main before CI; the VPS follows 10-25 min later (59a06582: ~16 min). A commit touching both sides (pricing, plan contract) gives open Python plans PROPUESTA_DESACTUALIZADA or
  mixed prices. Rule: anything touching services/ai-api or plan-contrato goes ship-branch -> CI -> VPS -> ff main (as D-038 did). Check each ship: VPS `DEPLOY_OK sha=` equals the Vercel Ready sha.
- Python single point: NC-1 (plan creation fails with "No pude terminar este plan" when :8000/VPS is down) open; no uptime monitor beyond deploy.yml's one-shot curl. Check `registros --origen python-vps --nivel error --desde 6h`.
- Rollback: kill switch untimed; code revert of any commit adding persisted customer fields wipes open chats (D-035). Roll back with the flag, never with git.
- Audit gaps: FLUX guided image not durable-audited (P-062); plan route has no per-browser quota for audit rows; catalogue snapshot prices age until `npm run catalogo:snapshot` (D-038 quotes use them): add an age check.
- Signal pollution: STATE says local .env.local points at prod Neon, so e2e, W4 runs and the drill write into prod tables; filter or move local to a Neon branch before trusting rating/audit counts.
- Feedback: nobody has read ai_feedback since launch. Check `SELECT calificacion, count(*) FROM ai_feedback WHERE creado_en > now() - interval '24 hours' GROUP BY 1` and the <= 4 rows with comments
  (`analizar-feedback-ia.ts`); the admin panel stays closed (third-party data), read via Neon only.
- Unwatched window: the loop ends 16:44 Sunday, owner is back Monday; schedule the canary (item 1) and leave a Spanish handoff with the kill-switch SQL.
- Photo quality: Taller photo reading is the owner's tested weak spot (quince: gold 59% vs ~35%, thin garland, one panel; P-067 in flight); production runs Gemini while W4 measures Haiku (item 6).

## Process gaps the lead keeps re-learning (STATE NOTE lines) -> automate
- Full SHA / `git rev-parse` (hand-typed SHA cancelled), deploy.yml headSha != deployed ref, checks.yml name, tsc verif config with .tsx, py -3.13 vs CI 3.11, kontext:test before ship, e2e:humo before/after,
  PowerShell-only junctions, `git add pictures/` scope, "stop on ANY red": fold into `npm run gate` + a `ship.ps1` (gate -> push branch -> CI wait -> deploy.yml with rev-parsed SHA -> ff main -> smoke -> STATE line).
- Add `scripts/test` wiring lint (test file in no script/workflow fails CI) and a pre-flip checklist file for any new persisted field (D-035) so decisions stop living only in STATE.
