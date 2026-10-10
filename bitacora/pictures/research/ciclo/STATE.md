# Marathon state (72 h) — rewritten every cycle

- Brief: `pictures/PROMPT-MARATHON-3-DAYS.md` · session `83576a42` (https://claude.ai/code/session_012zYrS6wZ3aYt9ga9JeqR2d)
- **Start: 2026-10-09 16:44 (local)** · end ≈ 2026-10-12 16:44
- Current cycle: **3**
- main = `d4b4020d` (… 9f8687a7 Kontext → d4b4020d REQ-013 phase 2 RAG partition)
- Last status message to owner: 2026-10-09 16:44 (start)

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
| REQ-013 Phase 2 RAG partition | main d4b4020d | PUSHED (migrations 033+034 on Neon) | Phase 3 next (index mobiliario/escenografía, ~US$0.05 embeddings) |
| W3 batch 2: recipe cards, size profiles, light/lens presets | e7k @cf8c5ed7 | review FIX FIRST (neutral light overrides warm rooms, FLUX capture picks up UV/lens, recipe measures ignore tubes, chip mismatch + 78 KB import) → haiku a6dd27f4 | fixing |
| P-040 pump rows per size | e7m ship/bomba (squash) | SHIP | verifying → push |
| W2 property tests + owner-phrases corpus | e7l @59e0594f | built (tests only; 0 violations; 8/8 phrases) | queued for antagonist |
| W7 switch dossier prep (integration test 28 ideas, parity refresh, DOSSIER-SWITCH.md) | e7n feat/dossier-guiada | implementer (haiku) a0ad4967 | running |
| W5 local Claude provider | main 8c397842 | PUSHED (verified 17 suites + unit + contracts) | needs ANTHROPIC_API_KEY + migration 033 before first local run |
| W2 scenario matrix | e7a | review FIX FIRST (VERSION_MOTOR 1.2.3, flaky time, silent rejections, weak bands) → haiku ae4bd443 | fixing |
| W6 REQ-013 ADR | — | opus xhigh | DONE: SPEC+PLAN 7 phases (requirements/REQ-013-catalogue-repositories); risk = migration 033 before Phase 2 code; eval data copy from e4r/data/taller |
| W5 Anthropic research | — | researcher (haiku) | DONE: claude-haiku-5-5 exists (effort param, $0.10/$0.50 MTok); notes research/w5-anthropic/NOTES.md |
| PM pro / PM customer | — | general-purpose (haiku) | DONE: research/pm/BACKLOG.md PRO-01..14, CUS-01..14 (customer read stale checkout; flagged) |
| W3 quick wins (PRO-02/03/13) | main e7109cc8 | product judge on prod: Bomba 6/10 (too many per-cm rows) → P-040 fix next; helium not judged (no helium scene in that template) | fix queued |
| CI green (P-036 + P-029) | e7h fix/ci-verde-2 (9 commits) | built (haiku); python-quality unverified (no venv) | HELD: green CI on main auto-deploys the VPS (deploy.yml workflow_run) — today every deploy is 'skipped' because CI is red → owner question (6) |
| W1 library ideas 29/30/31 | e7f fix/biblioteca-feedback @998a7b18 | HELD: customer-visible (stale stored Python counts → mismatch warnings); needs Python re-resolve | — |
| Feedback rating reload/burst | main 51129697 | PUSHED (verified) | product judge on prod (customer chats) |

## Next items (queue)
1. Baseline test run (runner) — failing tests list.
2. W2 scenario matrix generator (`scripts/escenarios/`) — offline, free.
3. W1 quick fixes: columna_asimetrica density, P-033 prerender guard, feedback rating reload.
4. W3 quick wins batch (pump seconds, dimension labels, helium line, recipe cards).
5. W5 provider implementation (opus xhigh — provider abstraction) when an implementer slot frees; key needed to run it.

## Owner questions (batched, asked 2026-10-09 16:5x)
(1) R-12 inflation classic arches · (3) ANTHROPIC_API_KEY + Haiku id · (4) BalloonBuilder customer vs pro ·
(5) REQ-004 accounts. (6) asked ~20:05: making CI green turns on automatic VPS deploys (incl. Python ai-api) on every push to main — ok, or make deploy manual (workflow_dispatch) first? (2) fixed: no switch, bring dossier. Deploy to main authorized.

## Decisions taken alone (D-027+)
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
- Scenario pass rate (c0): seed1 99.1 % (1315/1327 valid; 673 rejected = 7–8 colours > schema cap 6), seed2 98.8 %; only banda_conteo fails (aro_circular 87 %, pared_densa 92 %). Remaining: aro calibration, band vs tube cross-section, classic columns over band, short garlands, lighting/furniture not varied.
- W4 leaderboard: n/a
