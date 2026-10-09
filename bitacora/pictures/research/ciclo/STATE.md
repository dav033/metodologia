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

## In flight
| Item | Worktree / branch | Agent | Status |
|---|---|---|---|
| W1 REQ-007 Phase 5 (finish from d2590cd4) | e6g feat/guiada-motor-ediciones | implementer | launched c0 |
| W5 Anthropic provider research | — | researcher | launched c0 |
| W6 REQ-013 repositories ADR | — | Plan | launched c0 |
| PM backlog (pro + customer) | — | general-purpose ×2 | launched c0 |
| W2 scenario matrix | e7a feat/escenarios-matriz | implementer | launched c0 |

## Next items (queue)
1. Baseline test run (runner) — failing tests list.
2. W2 scenario matrix generator (`scripts/escenarios/`) — offline, free.
3. W1 quick fixes: columna_asimetrica density, P-033 prerender guard, feedback rating reload.
4. W3 quick wins batch (pump seconds, dimension labels, helium line, recipe cards).
5. W5 provider implementation once research lands (key needed to run it).

## Owner questions (batched, asked 2026-10-09 16:5x)
(1) R-12 inflation classic arches · (3) ANTHROPIC_API_KEY + Haiku id · (4) BalloonBuilder customer vs pro ·
(5) REQ-004 accounts. (2) fixed: no switch, bring dossier. Deploy to main authorized.

## Decisions taken alone (D-027+)
- none yet

## Spend (24 h window from start) vs caps
FLUX 0.00/3 · Gemini 0.00/2 · Anthropic 0.00/8 · total 0.00/13

## Metrics
- Scenario pass rate: n/a (generator not built)
- W4 leaderboard: n/a
