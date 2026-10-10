# Completeness critic — cycle 4 (session 83576a42)

Sources: brief §4–§10, STATE.md (cycle 4), day log 83576a42, PENDING.md, pm/BACKLOG.md. Read-only.
"Not evidenced" = no record in those files, not proof the work is absent.

## Gaps, ranked by owner value

1. **Product judge ≥ 8 almost never run (§5, §10).** One judge recorded (pump section 6/10, "fixed", not re-scored). No judge on: W3 quick wins e7109cc8, P-040 21ba148c, Kontext 9f8687a7, REQ-008 salon, REQ-011 studio, REQ-012 sets, rating UI 1f77b6ca, birthday fixes edaa49e5. Next: judge the 6 visible ones with screenshots (sonnet xhigh); re-score pump. M.
2. **Customer edit honesty untested (CUS-04, D-023).** Owner has caught 4+ false confirmations. Next: 10 forced-failure cases, one per customer edit tool, each must yield "No pude:". S.
3. **6-hourly status overdue.** STATE last status 16:44; first due ~22:44. Next: send ≤12 lines now, update STATE. S.
4. **W3: no tracker for the 19 ideas; about 9 not started.** Shipped or in batch 2: pump seconds, dimension labels, helium (not judged), profiles, light/lens presets, recipe cards. Not started: build sheet (idea 3, PRO-01 M), 3-tier quote + margin (5, PRO-05 M), colour pins (13, PRO-12 M), exports PNG 3000/SVG/GLB (14/18, PRO-06 M), mosaic (16, L), patterns (L), organic extras (M), vinyl sticker (M). Click-to-paint (14) and ΔE labels unverified. Next: 19-row status table (S); start PRO-01 build sheet (M).
5. **W2 visual regression absent.** No ~60-scene gallery, baselines or image judge. Next: pick 60 of the 405 dorado scenes, capture offline, commit baselines (M).
6. **W2 scenario matrix not merged.** Schema cap 6 colours rejects 673 seed-1 specs; brief asks 1–8. banda_conteo fails (aro_circular 87 %, pared_densa 92 %). Pass rate recorded only at c0. Next: finish fix ae4bd443; decide cap 8 or document; add per-cycle metric row (S–M).
7. **W4 harness not started.** No scripts/entrenamiento/, no LEADERBOARD.md. Next: skeleton + dry run over 30 photos with no paid calls (M). Keep Claude references r02–r05 (hand-read in 46a78670) out of the leaderboard as truth; brief says no hand modelling.
8. **W5 not runnable.** ANTHROPIC_API_KEY missing (owner Q3 unanswered). Vision, guided chat and interpreter port and IA_LOCAL_ESFUERZO not confirmed. Next: coverage check vs brief W5 (S); re-ask Q3 in the batch (S).
9. **W1 open bullets.** Birthday curtain (reads silver) and banner (reads neon) still wrong (M). Sign composite (M). Salon tables still catalogue, not parametric (M). Ideas 29/30/31 held: needs Python reachable from VPS (S–M). Audit of unmerged e3*/e4* branches not recorded (S). P-017 gold script black, P-006, P-011, P-036 (three failing tests): S each. Splits of VistaGuiada 2146 and herramientas-escena 1245 (M, when touched).
10. **Testing doctrine (§7).** CI deterministic-tests stops at test-python-adapter, so later suites never run (P-029). No Playwright e2e per release. Property test e7l not reviewed; P-042 shows undo is not round-trip identity. Next: runner full baseline of §7 suites (S); e2e smoke (M); pin P-042 as failing property (S).
11. **W7 switch dossier lacks evidence.** Missing judge screenshots, live Python check, rollback drill; price 0.70x unexplained to owner. Next: produce the three (M). No switch.
12. **W6 phases 3–7 open.** Taller Añadir by repository, AI filter, studio/guided Sempertex-only not started. Next: finish Phase 3, then scope Phase 4 (M–L).
13. **PM rotation (§6.7).** Only cycle-0 deltas exist. Next: ask both PMs for cycles 1–4 (S each). Correct CUS-08: voice is live in prod (dca3aebd), PM read a stale checkout.
14. **Standing housekeeping, none recorded since cycle 0.** RAM cleanup every 30 min (§9); worktree pruning e3–e6 (§9); SUMMARY rewrite + commit per cycle (§6.6); confirm dynamic /loop is live (old cron deleted in the pause). S each.
15. **Spend not reconciled.** STATE FLUX 1.28/3 and Gemini 0.00 not tied to the ledger (`npm run registros`). Next: reconcile (S).
16. **CUS gaps.** CUS-02 card/quote count test, CUS-03 aviso for unrepresentable structures, CUS-13 quote fields and response window, CUS-14 spares. S–M each.

## Contradictions with the brief

- D-028 and W3 quick wins reached prod before judge ≥ 8 (judge 6/10). Contradicts §10 order. Either stop, or record an owner ruling amending §10.
- REQ-013 Phase 3 implementer on opus. §5 allows opus only for architecture; index work is sonnet.
- Owner Q6 (CI deploy) was asked, not defaulted. §11 says take the reversible default: deploy.yml to workflow_dispatch.
- Fleet size: STATE lists 6+ agents with 2.3 GB free; §13 says max 2 implementers. Check before launching more.
- Pushes 21ba148c and 9f8687a7 show "verified" but no antagonist pass (§5 mandatory). Verify or review.
- PENDING P-034 says "owner to pick" for BalloonBuilder ideas; brief says build all 19.

## Hygiene

- Shipped but still open in PENDING: P-010, P-015, P-018, P-021, P-031. P-035 is struck but still in Open.
- Add PENDING rows for W2 visual, W3 build sheet and quote, W4 harness, W5 key, W6 phases.
