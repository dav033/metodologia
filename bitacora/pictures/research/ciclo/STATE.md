# Marathon state (72 h) — rewritten every cycle

- Brief: `pictures/PROMPT-MARATHON-3-DAYS.md` · session `83576a42` (https://claude.ai/code/session_012zYrS6wZ3aYt9ga9JeqR2d)
- **Start: 2026-10-09 16:44 (local)** · end ≈ 2026-10-12 16:44
- Current cycle: **20** (17:5x: brief re-read due (every 4 cycles) — hard rules unchanged except owner D-037/D-039; PM delta c20 running; VPS 0e47760f)
- Prev: cycle 19 (17:10: 6 h status sent; figures verifying; D-038 capped rule; P-054 round 2; Phase 5)
- Prev: cycle 18 (16:0x: Phase 4 on; Phase 5 launched; RAM 1.4 GB → one launch only)
- Prev: cycle 17 (14:5x: main b5f32b06 no solo-guiada; VPS chain pending; RAM 4.5 GB)
- Prev: cycle 16 (14:1x: brief §7 re-read — still missing: e2e browser pass per release, visual baselines, owner-phrases corpus; VPS follows d9a9a6b5 when CI green)
- Prev: cycle 15 (13:4x: D-039 flags on; inventory workflow wf_2c1a2e9f-d6d running; D-038 opus ad858971; P-052 round 2; Phase 4 at T20; W4 diagnostics)
- Prev: cycle 14 (13:1x: D-038 opus at 3 commits incl. parity test; P-052 review round 2; Phase 4 launched)
- Prev: cycle 13 (12:4x: VPS e7b7aeaa; main b3f66d39; agents: D-038 opus e7y, P-052 sonnet e7q, W4 re-run e7w; RAM 2.0 GB → Phase 4 held)
- Previous: cycle 10 (09:3x: 082a34fb Vercel Ready; 3 worktrees busy: e7q opus, e7w opus, e7y haiku P-049)
- main = `0e47760f` (… bbb3fe4d e2e smoke → 8955d367 REQ-013 Phase 4 → 0e47760f W4 figures) · VPS = 0e47760f (rule: VPS follows every green main); CATALOGO_FILTRO_IA live since the 0e47760f Vercel build
- Last status message to owner: 2026-10-10 17:10 (24 h status) · next ≈23:10

## Health (cycle 0)
- NOTE: system check 17:3x (workflow wf_a968de44-14c): all layers amber, nothing down; prod smoke 11 PASS / 1 FAIL (catalogue) / 2 SKIP; stopped idle :3020 dev server (e4r, 37 h) per D-033 → RAM 2.7 GB; :3010 → 0e47760f. Old claude.exe sessions left alone.
- NOTE: before/after each release run `npm run e2e:humo -- --env-file <demo-decoracion>/.env.local` (local :3010 on the shipped sha).
- NOTE: ship verification MUST include `npm run kontext:test` (provider guard is strict on new /api routes) — 888637d0 shipped an unclassified route; hotfixed b2ee1e39 within 10 min.
- NOTE: create worktree junctions ONLY with the PowerShell tool (bash quoting created a stray `Downloads$2` junction twice; removed safely).
- RAM: 15.7 GB, ~2.3 GB free after cleanup (commit 24.6/32.7 GB) → max 2 implementers at once until RAM improves.
- Ports in use: 3010 (owner dev, untouchable), 3020 (unknown dev server, left alone).
- `ANTHROPIC_API_KEY` absent in `.env.local` (IA_PROVEEDOR=gemini) → owner question (3).

## In flight (relaunched 16:50 with explicit models per brief §5 model rule)
| Item | Worktree / branch | Agent (model) | Status |
|---|---|---|---|
| W1 REQ-007 Phase 5 | main d05a52b8 | PUSHED (verified: tsc, 11 suites, contracts) | watch Vercel; product judge at switch dossier (D-028) |
| W1 P-033 prerender guard + dense asym column | main 53502782 | PUSHED | — |
| REQ-013 Phase 1 | main 6a760e21 | PUSHED (verified tsc, catalogo:test, 16 suites, contracts) | Phase 2 next (migration 034 must be applied before its code) |
| Kontext P-038 + per-metal wording | main 9f8687a7 | PUSHED (verified; test-espera-imagen is a UI test, passes without --conditions) | — |
| REQ-013 Phase 2 RAG partition | main d4b4020d | PUSHED | — |
| REQ-013 Phase 3 | main 318c5aaa | PUSHED (fichas + exact branch; Neon NOT applied — VPS must run ≥ d4b4020d first) | Phase 4 later |
| W3 batch 2 | main c69e307b | PUSHED; judge on prod: recipe card 8/10 (clear matrix, measures 306×503×140 cm; chip «Armazón recto» on an arch scene is odd), light/lens selector 8/10 (UV look not checked) | — |
| P-040 pump rows per size | main 21ba148c | PUSHED | — |
| W2 property tests + colour resolver (P-047) | main 0c7cc72e | PUSHED | P-052 follow-ups |
| W7 switch dossier + P-045 graceful rollback | main 7aafc12c | PUSHED (verified 25 suites, eslint 0) | dossier still missing: judge screenshots, live Python check, rollback drill |
| W3 build sheet (PRO-01) | e7q | haiku failed 2nd review (one page per piece → 118 pages; tilted columns broken rings) → ESCALATED sonnet xhigh; sonnet DONE 9a51054a (pages p90 32→6, max 119→13; all 1511 pages fit Letter/A4 measured in Chrome) | 3rd review FIX (blocker: Radix dialog inert inside native showModal → Imprimir dead; helio/estampado merged; handedness mirrored for sobre/ancla; no flag) → ESCALATED opus xhigh; opus DONE 3b7964d9 (DialogoCompra + esbuild/Playwright smoke; flag taller_hoja_armado default off; 1604 pages, all fit Letter/A4 with Geist) → 4th review FIX small (A1 focus not returned to opener; A2 estampado hash over-splits 8 scenes; env doc; log prefix; test deps) → opus 85e47f62; lead-reviewed; PUSHED main 888637d0 (verified tsc, eslint, globos3d, catalogo, contracts, dorado, fronteras) | product judge needs flag on (local) |
| CUS-04 honesty | main eb17544e | PUSHED | — |
| W4 training harness | main | baseline pass over 30 photos done | re-run after fixes A+B |
| W5b Claude Code CLI transport | main a8247ecc | PUSHED; LOCAL :3010 now runs origin/main (detached) with IA_PROVEEDOR=claude, IA_CLAUDE_TRANSPORTE=cli, IA_LOCAL_ESFUERZO=medium — /api/ia/salud: predeterminado claude (haiku, medium), factorPlazo 4 | .env.local backup in %TEMP%/env.local.bak-* |
| Small-fix bundle | main 55475888 | PUSHED | — |
| W4 fixes A (capabilities) | e7w | haiku failed 2nd review (otro resolver 4 false positives of 9, placement in front of structures, volume budget only on one path) → ESCALATED sonnet xhigh; sonnet DONE 78bdb5e7 (0/6 old false positives; lote-02 identical; goldens 0 diffs; 10 M cm³ budget → arch 500×320 thickness 120→105 cm) | 3rd review FIX (blocker: ajustar_tamanos densidad bypasses volume budget → 22.9 M cm³/18 s; lentejuelas/tapete false positives; duplicate otro dropped; guided column range widened = pricing surface) → ESCALATED opus xhigh; opus DONE 99837810 (13 M budget on every ajustar path, guided range kept, lote-02 byte-identical) → 4th review FIX (A1: budget metric changes after comoOrganico → converted arch + cambiar_pieza 160 = 22.9 M) → opus 628a1e9b (one body metric, 8 M cm³, length cap 2000 cm; arch 500×320 cap 133 cm; lote-02 identical) → 5th review FIX (A1 stretch estimate) → opus fa0af65c → PUSHED main b3f66d39 (verified 18 suites incl. kontext/motor3d/dorado/lectura-foto) | 30-photo re-run running |
| W4 fixes B (scale policy, visible metric, convergence) | main ad6a3710 | PUSHED 07:0x (verified tsc, 11 suites, boundary, eslint changed files) | re-run 30 photos after A |
| W5 local Claude provider | main 8c397842 | PUSHED (verified 17 suites + unit + contracts) | needs ANTHROPIC_API_KEY + migration 033 before first local run |
| W2 scenario matrix | main 15c74eb7 | PUSHED (verified) | P-048 follow-ups |
| W6 REQ-013 ADR | — | opus xhigh | DONE: SPEC+PLAN 7 phases (requirements/REQ-013-catalogue-repositories); risk = migration 033 before Phase 2 code; eval data copy from e4r/data/taller |
| W5 Anthropic research | — | researcher (haiku) | DONE: claude-haiku-5-5 exists (effort param, $0.10/$0.50 MTok); notes research/w5-anthropic/NOTES.md |
| PM pro / PM customer | — | general-purpose (haiku) | DONE: research/pm/BACKLOG.md PRO-01..14, CUS-01..14 (customer read stale checkout; flagged) |
| W3 quick wins (PRO-02/03/13) | main | judge re-score after P-040: Bomba collapsed «Bomba · 2 min 46,1 s» 8/10; minor: «Por pieza» lists 14 «Ojo con venas N · 1 globo» rows (group identical decorations) | — |
| CI | main 77b4af27 | FIRST FULLY GREEN Quality checks run (all 4 jobs) | VPS deploy now possible manually (D-031 gate); VPS still runs pre-d4b4020d code |
| W1 library ideas 29/30/31 | e7f fix/biblioteca-feedback @998a7b18 | HELD: customer-visible (stale stored Python counts → mismatch warnings); needs Python re-resolve | — |
| Feedback rating reload/burst | main 51129697 | PUSHED (verified) | product judge on prod (customer chats) |

| P-050 ajustar_tamanos formats | main 390ac0a2 | PUSHED (antagonist SHIP; premise not reproduced, only error message) | e7y free |

| P-037 prerender guard on server components | main 082a34fb | PUSHED (test-only; lead-reviewed diff; 28 server files clean) | e7y free |

| P-049 kill switch on imagen/armada routes + proactive notice | e7y fix/corte-rutas | implementer (haiku) | aa3c4534; review FIX (banner not marked → double notice; «Recalcular» via chat text depends on the model; copy; untested prod guard) → haiku eabef2ba; 2nd review FIX (Ver cómo quedaría dead after notice; propuesta on every plan breaks rollback under .strict()) → ESCALATED sonnet xhigh; sonnet d42676bf → 3rd review SHIP → PUSHED main eb7d0abd (verified incl. kontext:test); follow-ups P-056; D-035 |

| P-055 test-cuerpo-generacion red on main | main 2a3105c6 | PUSHED (stale regex → behavioural, in kontext:test) | e7q free |

| P-056 P-049 follow-ups (title, motor3d:test in CI, body drain, useCorte3d) | e7y fix/corte-seguimiento | implementer (haiku) | PUSHED main e7b7aeaa (review SHIP; minors → P-057) |
| P-052 colour resolver limits | e7q fix/resolutor-limites | implementer (haiku) | 38bdf09f → review FIX (b regressed: exact card name «Rosa» no longer wins; needless ask on rosa→blanco; property tests blind) → sonnet ff5b5024 (exact name wins; anti-alternation only step 2 on edited specs; generator/oracle cover 011/009, sensitivity proven) → review 2 SHIP → PUSHED main d9a9a6b5 (leftovers P-058) | e7q free |

| D-038 single quote everywhere (analysis + one pricer + parity test) | e7y feat/cotizacion-unica | implementer (opus xhigh) | DONE 71b67d4b (8 commits; 3D model kept, Python buys same packs+reserve; card quotes the plan the customer gets; Taller «Precio en la tienda»; 19-BOM shared fixture in CI; ×1.18 = size mix 1.07 × fragmentation 1.07) → opus review FIX (A1 reserve search can price +18.5 % above loose pack; A2 reserve not per colour/size; A4 card fallback on transient errors; A6 Taller all-or-nothing) → opus 40ec1d4c (per-balloon reserve ceil(n×0.08) in one search; TS=Python on 40 BOMs; prices rise: vector 24 140k→220k, idea 13 +34 %) → round 2 CONCERNS/SHIP (TS=Python 3,000 BOMs, 0 diffs) → opus 9550e897 (capped spare rule; idea 13 133,205→115,501; vector 24 220k→110k; wording «repuestos de cada globo»; 256-line chunks) → FINAL review round 3; ship plan: push ship branch to origin (not main) → CI green → deploy.yml VPS from that SHA → fast-forward main (Vercel); deploy order: Vercel then VPS at low traffic (open Python plans → PROPUESTA_DESACTUALIZADA) |
| VPS deploy (D-037) | — | lead | DONE 11:56 run 38069265687 DEPLOY_OK e7b7aeaa (first attempt failed: checkout needs the full SHA) |
| REQ-013 Phase 3 Neon apply | main checkout | general-purpose (sonnet) | DONE 12:1x: mobiliario 28 + escenografia 25 rows/vectors on Neon; sempertex untouched (3217 rows, md5 identical); acierto@5 catalogue 95 % hybrid, sempertex 100 %; US$0.0018 Gemini; CATALOGO_REPOS_RAG still off (Phase 4) |

| Product judge (screenshots) | :3010 | general-purpose (sonnet) | DONE research/juez/JUEZ-2026-10-10.md: build sheet 8/10, Taller cards 8/10, /asistente 5/10 blocked (local :8000 was down → restarted 12:05 via scratchpad/arrancar-ai-api.py); re-judge /asistente |

| Owner question «qué mejoras veo en producción» | — | workflow wf_35ff8442-93b (4 map + 4 verify + synth) | running |

| REQ-013 Phase 4 (T19–T22, flags off = byte-identical) | e7x feat/catalogo-fase4 | implementer (sonnet xhigh) | DONE 89e66b14 (T19–T22; defaults byte-identical; +306 B with CATALOGO_FILTRO_IA) → review SHIP (fix before flip: A1 settings read without deadline on critical path, A2 garbage row drops Sempertex, A3 prompt hint, A4 error text, A7 tests in CI) → PUSHED main 8955d367; ON 15:50: Neon row catalogo_repos_rag=sempertex,mobiliario,escenografia + Vercel CATALOGO_FILTRO_IA=true (next build) — was: row catalogo_repos_rag=sempertex,mobiliario,escenografia + env CATALOGO_FILTRO_IA=true (D-039) |

| W4 diagnostics (deterministic detection cache, specific failure classes, ver_escena claim) | e7w feat/entrenamiento-diagnostico | implementer (sonnet xhigh) | DONE ca1a2f24 (cache key = photo hash + detector config; capacidad_faltante → figura 18, mueble/fondo 14, pared 7, arco 2, tamaño 3; ver_escena = model tries native tool under CLI) → PUSHED main b1fdf465 | e7w free |

| P-054 scene AI time bounds (cheap searches, balloon-weighted budget, maxDuration + deadline) | e7q fix/escena-ia-tiempo | implementer (sonnet xhigh) | DONE 22a39c8e (arch «más R-24» 40.6→10.4 s; R-5 column 59 s→instant reject; balloon-count budget 430; maxDuration 75 + deadline; marco 500×320@100 in a 320 cm room now errors instead of refit) → review FIX (3 existing tests broken; «más R-5» regression on tronco; 430 cap on intermediate pieces forces R-24 into thin bodies; 19.8 s semiarco; marco regression acceptable with cheap fix) → sonnet fixing (round 2) |

| D-039 remove solo-guiada mode | e7z feat/sin-solo-guiada | implementer (sonnet xhigh) | PUSHED main b5f32b06 (this build also picks up MODULOS_ESCRITURA=abierta and the removed NEXT_PUBLIC_SOLO_GUIADA) | e7z free |

| W4 figures capability (falta_figura 18 photos) | e7w feat/w4-figuras | implementer (sonnet xhigh) | DONE c1bcafef (reader→pumpkins/rizos/balloon flowers/filled numbers; agregar_pieza forma+texto; offline falta_figura 18→14; 2 internal antagonist rounds) → PUSHED main 0e47760f | e7w free |

| E2E smoke per release (npm run e2e:humo) | main bbb3fe4d | PUSHED; run vs :3010 @b5f32b06: 14/14 PASS in 83 s, 0 paid calls — run it on every release | e7z free |

| REQ-013 Phase 5 (Taller «Añadir» by repository; catalogo_ui_repositorios row, ON by default per D-039) | e7x feat/catalogo-fase5 | implementer (sonnet xhigh) | launched 16:0x |

| System check fixes: prod /catalogo empty on Vercel (SQLite in /tmp), /3d crash clasificacionDe(undefined id), guided-3D plans not audited server-side (plan_audit_log empty since 10-09 11:15Z), pg SSL log noise | e7z fix/catalogo-vercel | implementer (sonnet xhigh) | launched 17:4x |

| NP-1 complete build sheet (helium in hoja, printed positions, foil/forma lines, organic «cómo armar», copy polish) | e7w feat/hoja-completa | implementer (sonnet xhigh) | launched 18:0x |

## Next items (queue)
- PM delta c20 (research/pm/BACKLOG.md): top 8 = NC-3 audit (in flight), NP-1 build sheet (in flight), NP-6 prod price parity check after D-038, NC-4 rollback drill (careful: local .env.local points at prod Neon — drill flips prod), NP-4 copy polish, CUS-03+CUS-14 tests, NC-5 one rating POST per turn, NC-1 plan creation survives Python down.
- W4 next by evidence: figures (falta_figura 18 photos, 12 dominant) and furniture/backdrops (14 photos, 10 dominant); cache the photo reader too; intercept native tool_use in the CLI transport.
- Brief §7 gaps left: 20-scene visual baseline, owner-phrases corpus test with mocked model.
- 24 h visual report PUBLISHED 15:50 (artifact v2 https://claude.ai/artifact/TD2Co1cSeN6i4GExCjvJhU). Next 6 h status due ≈17:15; 48 h report ≈16:44 Sunday.
- Critic c12 (research/ciclo/CRITICO-c12.md) top: (1) time-box W4, ship if strictly better, re-run 30 photos (report both IoU metrics; restart :3010 on origin/main first); (2) screenshot judge sweep → feeds 24 h visual report 16:44; (3) switch dossier incl. rollback drill; (4) W3 money flow PRO-04/05. D-036 stop-rule.
- Owner report artifact: https://claude.ai/artifact/TD2Co1cSeN6i4GExCjvJhU (update at 24 h).
- Small-fix bundle (haiku, one worktree) when a slot frees: P-041 salon capacity wording, P-043 ideas 30/31 duplicated price (check), P-046 group identical decorations «× N», «Armazón recto» chip on arch scenes, CUS-02 card=quote test, CUS-03 18-structure test (PM delta c8).
- DONE 03:37: main checkout (clean, branch fix/color-organico-conteo, 0 ahead / 179 behind origin/main) → `git checkout main && git merge --ff-only origin/main`, `npm run build --workspaces --if-present`, set .env.local IA_PROVEEDOR=claude + IA_CLAUDE_TRANSPORTE=cli + IA_LOCAL_ESFUERZO=medium, restart :3010 (`node --use-system-ca node_modules/next/dist/bin/next dev -p 3010`, parent pid 12980) — D-033.
0. Critic c4 (research/ciclo/CRITICO-c4.md): judge shipped features with screenshots; CUS-04 forced-failure honesty tests; W3 19-idea tracker + build sheet; W2 visual regression; W4 harness dry-run skeleton. Also: REQ-013 Phase 3 (opus), P-041 salon capacity wording, P-037 guard server components, W4 harness skeleton (needs key to run), completeness critic at cycle 4.
1. Baseline test run (runner) — failing tests list.
2. W2 scenario matrix generator (`scripts/escenarios/`) — offline, free.
3. W1 quick fixes: columna_asimetrica density, P-033 prerender guard, feedback rating reload.
4. W3 quick wins batch (pump seconds, dimension labels, helium line, recipe cards).
5. W5 provider implementation (opus xhigh — provider abstraction) when an implementer slot frees; key needed to run it.

## Owner questions (batched, asked 2026-10-09 16:5x)
(1) R-12 inflation classic arches · (3) ANTHROPIC_API_KEY — owner 00:3x: no key; asked for a Claude Code CLI patch (W5b) · (4) BalloonBuilder customer vs pro ·
(5) REQ-004 accounts. (6) asked ~20:05: making CI green turns on automatic VPS deploys (incl. Python ai-api) on every push to main — ok, or make deploy manual (workflow_dispatch) first? (2) fixed: no switch, bring dossier. Deploy to main authorized.

## Decisions taken alone (D-027+)
- D-039 (owner) beta: everything on for everyone — Neon rows taller_hoja_armado=activo, guiada_motor=3d set 12:32
- D-038 (owner) one quote everywhere, pick the best model
- D-037 (owner) not real production: VPS deploy approved, go hard (lifts D-034)
- D-036 review stop-rule; M tasks start on sonnet
- D-035 reader-first persisted fields
- D-034 no VPS deploy this weekend (Python quote changes pending owner); REQ-013 P3 Neon apply waits for it
- D-033 (owner) dev servers :3010/:8000 may be restarted this weekend
- D-032 owner away all weekend (full control): Q1 keep 5 quartets/m, Q4 BB features pro-only (customer ones flag-off), Q5 shared password; Q3 → CLI transport
- D-031 VPS deploy manual (workflow_dispatch) before CI goes green (Q6 reversible default)
- D-030 product judge for staff Taller features on the production deploy
- D-029 REQ-013 class-prefixed local ids for Sempertex kinds without catalogue id
- D-028 flag-gated, customer-invisible work ships after antagonist SHIP + verified merge; the product judge (screenshots) runs on it in the W7 switch dossier
- Migration numbers: 033 = W5 proveedor anthropic, 034 = REQ-013 repositorio (lead ruling)
- D-027 helium litres = sphere volume of inflated diameter (PRO-02 '97 L' was wrong)

## Escalations
- 10:0x P-049: haiku failed review twice → sonnet xhigh.
- 08:4x W4 capabilities: sonnet failed 3rd review (budget bypass) → opus xhigh.
- 08:3x build sheet: sonnet failed 3rd review (dead dialog blocker) → opus xhigh.
- 06:5x W4 capabilities: haiku failed review twice → sonnet xhigh.
- 06:xx build sheet: haiku failed review twice → sonnet xhigh.
- 03:1x colour resolver: sonnet failed review → opus xhigh.
- 03:xx W4 harness: haiku failed hostile review twice → sonnet xhigh.
- 23:3x property tests/colour resolver: haiku failed hostile review twice → sonnet xhigh.
- 19:0x Kontext colour exp: haiku failed twice (script bug, timeout) → sonnet xhigh.
- 18:2x W3 quick wins: haiku failed hostile review twice → sonnet xhigh (rule §5).
- none yet (16:50: first wave was launched without explicit model, stopped after ~3 min and relaunched per the model rule)

## Spend (24 h window from start) vs caps
FLUX 1.28/3 (Kontext exp complete incl. silver check) · Gemini 0.002/2 · Anthropic 0.00/8 · total 1.28/13 (+US$0.002 Gemini)

## Metrics
- Scenario pass rate (c4, after review fixes): seed1 98.5 % of 2,000 (0 rejected; 2,612 pieces without a band); open: flowers on solo_grandes dip 3 cm under floor (whitelisted), aro lujoso/medio under band, thin columns 20/m.
- W4 PASS 2 (b3f66d39, same settings): proporciones 0.482, colores 0.385, IoU all 0.559 / visible 0.541; noise caveat: detection cache never hit, reader/assistant resampled.
- W4 BASELINE (all 30 photos, main fb956d8c, Haiku CLI medium, 2 turns, US$0, 552 calls): mean proporciones 0.446, colores 0.366, IoU 0.525 (old all-balloons metric); failures: capacidad_faltante 29/30, compilacion 7. Next pass after fixes A+B merge (compare same metric).
