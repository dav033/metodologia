# Marathon state (72 h) — rewritten every cycle

- Brief: `pictures/PROMPT-MARATHON-3-DAYS.md` · session `83576a42` (https://claude.ai/code/session_012zYrS6wZ3aYt9ga9JeqR2d)
- **Start: 2026-10-09 16:44 (local)** · end ≈ 2026-10-12 16:44
- Current cycle: **5**
- main = `a7014966` (… c69e307b W3 batch 2 → a7014966 W7 integration test)
- Last status message to owner: 2026-10-09 22:30 (6 h status)

## Health (cycle 0)
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
| REQ-013 Phase 3 index mobiliario/escenografía (hidden) | e7o feat/repositorios-fase3 | implementer (opus xhigh) a2903e43 | running (dry-run only; lead applies, ≤US$0.05) |
| W3 batch 2 | main c69e307b | PUSHED; judge on prod: recipe card 8/10 (clear matrix, measures 306×503×140 cm; chip «Armazón recto» on an arch scene is odd), light/lens selector 8/10 (UV look not checked) | — |
| P-040 pump rows per size | main 21ba148c | PUSHED | — |
| W2 property tests + owner phrases + colour-resolver fix | e7l @6c643ea6 | fixes done; found resolver idempotence bug (fixed) + P-047 name→code mismatches | re-review running |
| W7 switch dossier | main a7014966 + DOSSIER-SWITCH.md | — | P-045 graceful rollback: e7p feat/guiada-rollback-ordenado, implementer (opus xhigh) running |
| W5 local Claude provider | main 8c397842 | PUSHED (verified 17 suites + unit + contracts) | needs ANTHROPIC_API_KEY + migration 033 before first local run |
| W2 scenario matrix | e7a ship/escenarios @15c74eb7 (squash) | SHIP-ready | runner verifying → push |
| W6 REQ-013 ADR | — | opus xhigh | DONE: SPEC+PLAN 7 phases (requirements/REQ-013-catalogue-repositories); risk = migration 033 before Phase 2 code; eval data copy from e4r/data/taller |
| W5 Anthropic research | — | researcher (haiku) | DONE: claude-haiku-5-5 exists (effort param, $0.10/$0.50 MTok); notes research/w5-anthropic/NOTES.md |
| PM pro / PM customer | — | general-purpose (haiku) | DONE: research/pm/BACKLOG.md PRO-01..14, CUS-01..14 (customer read stale checkout; flagged) |
| W3 quick wins (PRO-02/03/13) | main | judge re-score after P-040: Bomba collapsed «Bomba · 2 min 46,1 s» 8/10; minor: «Por pieza» lists 14 «Ojo con venas N · 1 globo» rows (group identical decorations) | — |
| CI green + manual VPS deploy (D-031) | e7h | review FIX FIRST: no workspace build in CI, 4 stale plan:test suites, LINT RED on main from c69e307b (set-state-in-effect in useAmbienteVisor/usePerfilesTamano) → haiku a61d5a41 | fixing |
| W1 library ideas 29/30/31 | e7f fix/biblioteca-feedback @998a7b18 | HELD: customer-visible (stale stored Python counts → mismatch warnings); needs Python re-resolve | — |
| Feedback rating reload/burst | main 51129697 | PUSHED (verified) | product judge on prod (customer chats) |

## Next items (queue)
0. Critic c4 (research/ciclo/CRITICO-c4.md): judge shipped features with screenshots; CUS-04 forced-failure honesty tests; W3 19-idea tracker + build sheet; W2 visual regression; W4 harness dry-run skeleton. Also: REQ-013 Phase 3 (opus), P-041 salon capacity wording, P-037 guard server components, W4 harness skeleton (needs key to run), completeness critic at cycle 4.
1. Baseline test run (runner) — failing tests list.
2. W2 scenario matrix generator (`scripts/escenarios/`) — offline, free.
3. W1 quick fixes: columna_asimetrica density, P-033 prerender guard, feedback rating reload.
4. W3 quick wins batch (pump seconds, dimension labels, helium line, recipe cards).
5. W5 provider implementation (opus xhigh — provider abstraction) when an implementer slot frees; key needed to run it.

## Owner questions (batched, asked 2026-10-09 16:5x)
(1) R-12 inflation classic arches · (3) ANTHROPIC_API_KEY + Haiku id · (4) BalloonBuilder customer vs pro ·
(5) REQ-004 accounts. (6) asked ~20:05: making CI green turns on automatic VPS deploys (incl. Python ai-api) on every push to main — ok, or make deploy manual (workflow_dispatch) first? (2) fixed: no switch, bring dossier. Deploy to main authorized.

## Decisions taken alone (D-027+)
- D-031 VPS deploy manual (workflow_dispatch) before CI goes green (Q6 reversible default)
- D-030 product judge for staff Taller features on the production deploy
- D-029 REQ-013 class-prefixed local ids for Sempertex kinds without catalogue id
- D-028 flag-gated, customer-invisible work ships after antagonist SHIP + verified merge; the product judge (screenshots) runs on it in the W7 switch dossier
- Migration numbers: 033 = W5 proveedor anthropic, 034 = REQ-013 repositorio (lead ruling)
- D-027 helium litres = sphere volume of inflated diameter (PRO-02 '97 L' was wrong)

## Escalations
- 19:0x Kontext colour exp: haiku failed twice (script bug, timeout) → sonnet xhigh.
- 18:2x W3 quick wins: haiku failed hostile review twice → sonnet xhigh (rule §5).
- none yet (16:50: first wave was launched without explicit model, stopped after ~3 min and relaunched per the model rule)

## Spend (24 h window from start) vs caps
FLUX 1.28/3 (Kontext exp complete incl. silver check) · Gemini 0.00/2 · Anthropic 0.00/8 · total 1.28/13

## Metrics
- Scenario pass rate (c4, after review fixes): seed1 98.5 % of 2,000 (0 rejected; 2,612 pieces without a band); open: flowers on solo_grandes dip 3 cm under floor (whitelisted), aro lujoso/medio under band, thin columns 20/m.
- W4 leaderboard: n/a
