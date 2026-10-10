# Marathon state (72 h) — rewritten every cycle

- Brief: `pictures/PROMPT-MARATHON-3-DAYS.md` · session `83576a42` (https://claude.ai/code/session_012zYrS6wZ3aYt9ga9JeqR2d)
- **Start: 2026-10-09 16:44 (local)** · end ≈ 2026-10-12 16:44
- Current cycle: **12** (11:2x: CI green eb7d0abd; completeness critic c12 running; e7w opus round 6, e7y P-056 in review, e7q P-052 haiku)
- Previous: cycle 10 (09:3x: 082a34fb Vercel Ready; 3 worktrees busy: e7q opus, e7w opus, e7y haiku P-049)
- main = `e7b7aeaa` (… b2ee1e39 CI hotfix → eb7d0abd P-049 → e7b7aeaa P-056)
- Last status message to owner: 2026-10-10 11:2x (18 h status) · CI green on eb7d0abd · next: 24 h visual report due 16:44

## Health (cycle 0)
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
| W4 fixes A (capabilities) | e7w | haiku failed 2nd review (otro resolver 4 false positives of 9, placement in front of structures, volume budget only on one path) → ESCALATED sonnet xhigh; sonnet DONE 78bdb5e7 (0/6 old false positives; lote-02 identical; goldens 0 diffs; 10 M cm³ budget → arch 500×320 thickness 120→105 cm) | 3rd review FIX (blocker: ajustar_tamanos densidad bypasses volume budget → 22.9 M cm³/18 s; lentejuelas/tapete false positives; duplicate otro dropped; guided column range widened = pricing surface) → ESCALATED opus xhigh; opus DONE 99837810 (13 M budget on every ajustar path, guided range kept, lote-02 byte-identical) → 4th review FIX (A1: budget metric changes after comoOrganico → converted arch + cambiar_pieza 160 = 22.9 M) → opus 628a1e9b (one body metric, 8 M cm³, length cap 2000 cm; arch 500×320 cap 133 cm; lote-02 identical) → 5th review FIX (A1: cambiar_pieza alto/ancho on non-trazo organic checks an estimate → 14.6 M) → opus fixing |
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
| P-052 colour resolver limits | e7q fix/resolutor-limites | implementer (haiku) | 38bdf09f (b,c,d; a deferred → P-057) → review running |

## Next items (queue)
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
FLUX 1.28/3 (Kontext exp complete incl. silver check) · Gemini 0.00/2 · Anthropic 0.00/8 · total 1.28/13

## Metrics
- Scenario pass rate (c4, after review fixes): seed1 98.5 % of 2,000 (0 rejected; 2,612 pieces without a band); open: flowers on solo_grandes dip 3 cm under floor (whitelisted), aro lujoso/medio under band, thin columns 20/m.
- W4 BASELINE (all 30 photos, main fb956d8c, Haiku CLI medium, 2 turns, US$0, 552 calls): mean proporciones 0.446, colores 0.366, IoU 0.525 (old all-balloons metric); failures: capacidad_faltante 29/30, compilacion 7. Next pass after fixes A+B merge (compare same metric).
