# Marathon state (72 h) — rewritten every cycle

- Brief: `pictures/PROMPT-MARATHON-3-DAYS.md` · session `83576a42` (https://claude.ai/code/session_012zYrS6wZ3aYt9ga9JeqR2d)
- **Start: 2026-10-09 16:44 (local)** · end ≈ 2026-10-12 16:44
- Current cycle: **0 (bootstrap)**
- main = `b4433bc9` · Vercel prod Ready
- Last status message to owner: 2026-10-09 16:44 (start)

## Health (cycle 0)
- RAM: 15.7 GB, ~2.3 GB free after cleanup (commit 24.6/32.7 GB) → max 2 implementers at once until RAM improves.
- Ports in use: 3010 (owner dev, untouchable), 3020 (unknown dev server, left alone).
- `ANTHROPIC_API_KEY` absent in `.env.local` (IA_PROVEEDOR=gemini) → owner question (3).

## In flight (relaunched 16:50 with explicit models per brief §5 model rule)
| Item | Worktree / branch | Agent (model) | Status |
|---|---|---|---|
| W1 REQ-007 Phase 5 | e6g feat/guiada-motor-ediciones @903916f4 | built (haiku); antagonist (sonnet xhigh) a1075ed3 | in review |
| W5 local Claude provider | e7c feat/ia-local-claude | implementer (opus xhigh, architecture) a3def6b1 | running |
| W2 scenario matrix | e7a feat/escenarios-matriz | implementer (haiku) ae4bd443 | running |
| W6 REQ-013 ADR | — | general-purpose (opus xhigh) a9b97ee7 | running |
| W5 Anthropic research | — | researcher (haiku) | DONE: claude-haiku-5-5 exists (effort param, $0.10/$0.50 MTok); notes research/w5-anthropic/NOTES.md |
| PM pro / PM customer | — | general-purpose (haiku) | DONE: research/pm/BACKLOG.md PRO-01..14, CUS-01..14 (customer read stale checkout; flagged) |
| W3 quick wins (PRO-02 helium/ribbon, PRO-03 pump s, dims) | e7b feat/bb-rapidos | implementer (haiku) a96635ab | running |

## Next items (queue)
1. Baseline test run (runner) — failing tests list.
2. W2 scenario matrix generator (`scripts/escenarios/`) — offline, free.
3. W1 quick fixes: columna_asimetrica density, P-033 prerender guard, feedback rating reload.
4. W3 quick wins batch (pump seconds, dimension labels, helium line, recipe cards).
5. W5 provider implementation (opus xhigh — provider abstraction) when an implementer slot frees; key needed to run it.

## Owner questions (batched, asked 2026-10-09 16:5x)
(1) R-12 inflation classic arches · (3) ANTHROPIC_API_KEY + Haiku id · (4) BalloonBuilder customer vs pro ·
(5) REQ-004 accounts. (2) fixed: no switch, bring dossier. Deploy to main authorized.

## Decisions taken alone (D-027+)
- none yet

## Escalations
- none yet (16:50: first wave was launched without explicit model, stopped after ~3 min and relaunched per the model rule)

## Spend (24 h window from start) vs caps
FLUX 0.00/3 · Gemini 0.00/2 · Anthropic 0.00/8 · total 0.00/13

## Metrics
- Scenario pass rate: n/a (generator not built)
- W4 leaderboard: n/a
