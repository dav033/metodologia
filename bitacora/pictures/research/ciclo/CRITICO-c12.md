# Completeness critic - cycle 12 (session 83576a42, T+18.5 h, main eb7d0abd)
Sources: brief, STATE c12, CRITICO-c4, PENDING, pm/BACKLOG (c0, c8), DOSSIER-SWITCH, TRACKER, LEADERBOARD, day log, `git log origin/main`
(29 commits since start), `git ls-tree` of main. Read-only. "Not found" = absent from those files or from main.

## 1. Headline
Throughput is high (CI green, rollback and honesty hardened) but it went to hardening, not to proving or shipping owner-visible value.
Three brief deliverables have no evidence: (a) W4 improvement after fixes, (b) the REQ-007 switch dossier, (c) product-judge scores.
W3 pro features and W2 visual/e2e barely moved. 53.5 h remain.

## 2. Workstreams vs brief
- W1: Phase 5, P-033/037, Kontext, resolver, CI done. Untouched: sign composite, salon tables parametric, birthday curtain/banner,
  P-017, P-027, P-006, P-011, ideas 29/30/31 (held), file splits (VistaGuiada grew 2146 to about 2230).
- W2: matrix, property tests, owner-phrase corpus shipped. Missing: ~60-scene visual gallery/baselines/image judge, Playwright e2e per
  release (no *.spec.ts on main), P-042 undo not identity, P-048 (18 % of pieces skip geometry checks), P-051 (4 structures build 0 balloons).
- W3: 6 of 19 done (4, 9, 11, 12, pump, dims) plus helium. Build sheet (3) shipped FLAG OFF and never seen. Not started: 3-tier quote and
  margin (5, 6), colour pins (7), palette dE (2), PNG 3000/GLB (14), live paint counter (10), patterns/organic extras (19), mosaic (8),
  vinyl, backdrops (15). PRO-04 quote-from-scene absent.
- W4: harness and 30-photo baseline (0.446 / 0.366 / IoU 0.525) exist; fix B shipped, fix A at review round 6. NO re-run. No viewer
  captures (leaderboard says "pendiente"), so no triptychs and no judge agent photo-vs-capture (both in the brief). 29/30 fail as
  "capacidad_faltante": too coarse to steer fixes.
- W5: provider and CLI transport done, US$0. Key never given; usage-limit exposure of the subscription CLI is undocumented.
- W6: Phases 1-3 shipped; 4-7 (UI by repository, AI filter, customer scope) not started; Phase 3 Neon apply blocked by D-034.
- W7: Phase 5, integration tests, P-045, P-049 shipped; dossier evidence missing (section 5).

## 3. c4 items still undone
- #1 product judge: 3 of about 12 visible features scored (recipe card 8, light/lens 8, pump 8). Unjudged: guided 3D plan card, "Ver como
  quedaria", customer edits, kill-switch banner, honesty wording, helio/dimension labels, build sheet, salon/grouped rows, colour resolver,
  Kontext resume, rating UI. Contradicts brief 10 and D-028/D-030.
- #5 W2 visual regression and #10 e2e per release: absent. #13 PM rotation: only c0 and c8 exist (brief: every cycle).
- #14 housekeeping: 98 registered worktrees (about 60 e3*/e4*/e5*), merged ones never pruned, 34 local unmerged branches with no recorded
  audit. PENDING still lists shipped P-010/015/018/021/026/031 as open and ends with duplicated boilerplate. #15 spend not reconciled.
- Closed since c4: CUS-04 (21 cases), W3 tracker, W4 harness, W5, CI green, matrix merged, CUS-02 test.

## 4. Where agent time goes
- Hostile rounds: build sheet 4, W4 capabilities 5 done plus a 6th running (about 4.5 h on one branch), P-049 3, resolver 4, harness 4,
  scale 3, CLI 3, P-045 several. About 8 of 11 M-size tasks escalated: haiku fails twice, then sonnet, then opus.
- W4 findings drifted from correctness (rounds 2-3: false positives, budget bypass) to perf bounds and pre-existing main behaviour
  (round 5: 14.6 M cm3 via `cambiar_pieza`; P-054 shows main has the same). Round 6 is diminishing returns.
- Build sheet and P-049 used 7 rounds on flag-off or flag-gated code with zero owner-visible effect yet.
- Verdict: reviews found real blockers (dead dialog, budget bypass), keep them, but there is no stop-rule and no "better than main" test.

## 5. REQ-007 switch dossier: missing evidence (and it is stale)
DOSSIER-SWITCH section 4 still says P-045 is "in review, not on main"; it shipped (7aafc12c, eb7d0abd). Regenerate. Missing:
1. judge screenshots desktop + phone >= 8; 2. live Python price check per idea (read-only VPS call; dossier wants owner confirm);
3. rollback drill on the deployed app with timing (flag and kill switch, steps 2 and 4; low risk, setting the kill while motor is python
changes nothing for customers); 4. cause of the 1.18x price effect; 5. visual review of sencilla/media/lujosa; 6. undo semantics (P-042);
7. the 8 ideas outside +-15 % and the arch-inflation default (D-032 Q1) stated to the owner; 8. 18-structure coverage test with customer
aviso (CUS-03), since P-051 says 4 of 18 fall back to Python; 9. an explicit owner accept line for the 0.70 price ratio.

## 6. Ranked recommendations for the next 6 h (11:30 to 17:30)
1. Time-box W4 capabilities and re-run the 30 photos. Value: high. Effort: S decision + about 80 min wall (baseline took 75 min, US$0).
   Why: the W4 loop has no after-number. Ship the branch if it is strictly better than main and the open finding is a perf bound already
   on main; log under P-054 and add route `maxDuration`. B changed IoU to visible balloons, so re-score stored baseline captures with the
   new metric or report both, else the delta is not comparable.
2. Product-judge sweep with screenshots (desktop + phone), one sonnet-xhigh judge; local flag-on for build sheet and guided 3D, prod for
   the rest. Value: high. Effort: M (about 1.5 h). Why: closes c4 #1, feeds dossier item 1, supplies the 24 h visual report due 16:44.
   Under 8 becomes a fix item; if the build sheet scores >= 8, enable `taller_hoja_armado` for staff (reversible, D-030).
3. Finish the switch dossier (section 5, items 1-9) and rewrite its stale section 4. Value: critical (owner's top ask). Effort: M.
   Run the rollback drill and a read-only Python check from the VPS (no deploy, consistent with D-034).
4. Start the W3 money flow: PRO-04 quote from scene, then PRO-05 tiers, surcharges and margin. Value: high for the decorator. Effort:
   M each, start on sonnet (reuse `lib/cotizacion/borrador-profesional.ts`). Why: ideas 5-6 are the most valuable untouched items;
   18 h passed with none started. Pair with an S batch: dE labels, live paint counter, PNG 3000 px.
5. Adopt a review stop-rule and a model rule, recorded as a D-number. Value: medium (saves hours every cycle). Effort: S. Max 3 hostile
   rounds; round 4+ fixes only correctness, pricing, security or data loss; perf and pre-existing findings go to PENDING. Start M-size
   or engine/AI tasks directly on sonnet xhigh; keep haiku for S tasks, tests and docs.
6. W2 minimum viable visual + e2e. Value: medium. Effort: M. 20-scene gallery with committed baselines (not 60), one Playwright smoke each
   for `/3d` and `/asistente` (load, build, zero console errors). Why: engine edits continue and nothing catches a visual regression.
7. Make W4 diagnostic. Value: medium. Effort: M. Split "capacidad_faltante" into the named missing capability, add headless viewer capture
   and before/after triptychs for the 5 lowest photos (54, 44, 53, 52, 35 by proporciones). Needs one dev server.
8. Hygiene batch (haiku). Effort: S. Prune merged worktrees (98 to under 30), audit the 34 unmerged branches, clean PENDING, reconcile spend
   against the ledger, run both PMs for cycles 9-12 (focus P-051, P-053, dossier), extract `useCorte3d` (P-056 A5) as a real VistaGuiada split.
9. Small-bug batch (haiku, one worktree). Effort: S. P-017 gold script black, P-027 burgundy 915 (record accept or "aprox."), P-006, P-011,
   CUS-14 spares test.
10. Defer: W6 phases 4-7, W3 mosaic/vinyl/patterns, P-052 (a)-(d), REQ-004. Invisible or low value this weekend; revisit after 1-4 land.

## 7. Cadence and risks
- 24 h visual report due 16:44 and next 6 h status about 17:20: build both from items 1-2 so they carry evidence.
- RAM (about 2.3 GB free) is the limit: serialise the W4 re-run (CLI + :3010) and the judge (browser); no third launch.
- Restart :3010 on post-merge origin/main before the re-run (D-033 permits), or the comparison is invalid.
- Owner proposals (not blocking): enable `taller_hoja_armado` for staff once judged; accept the 0.70 price ratio only after the live check.
