# pictures — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex balloon-decoration demo (`demo-decoracion`: Next 16 on Vercel + Python ai-api on a VPS). Two products on one
engine: the **Taller 3D** (`/3d`, pro tool with a scene AI agent) and the **guided customer chat** (`/asistente`,
quotes priced by Python; the 3D engine sits behind `GUIADA_MOTOR=python`).

## Current state (last deployment record: `65edd83b`, 2026-10-11 06:14; local work: 2026-10-15)
- REQ-015 local branch `feat/req-015-judge-fix` at `26db7b8b`, 24 commits ahead of tracked origin/main; T12 cap and audit #3 corrections are committed locally. Current uncommitted work makes the colour regression reproducible without the ignored Shopify snapshot and includes it in guiada:test. No push/deploy in this session. Previous REQ-015 independent reviews approve; prior full gate passed (P-076 closed).
- **One quote everywhere (D-038) live:** same plan = same price on every surface; per-balloon spares with a cost cap;
  Python = engine (42-BOM shared fixture in CI). Every guided idea (engine and curated) is priced by the single pricer;
  prod e2e «paridad de precio» checks assistant = Taller on every release.
- **Beta, everything on for everyone (D-039):** guided chat runs the 3D engine for all customers, Taller build sheet on,
  solo-guiada mode removed, catalogue repositories on; VPS deploys follow every green main (D-037). Only the AI-feedback
  admin panel stays closed (third-party data).
- **Owner photo case (quinceañera backdrop) fixed (59a06582 + 9f86d67b):** the backdrop is the subject (no guest table),
  scale and floor come from the installation, the garland spans the real balloons with the photo's colour shares, a
  second glitter wall, plum chrome → Reflex. Left in P-068 (doors, pink roses, low camera).
- **Spend caps are global (392fff68):** paid-call hourly caps count in Neon `topes_gasto` (migration 035), not per Vercel instance.
- **Happia Integrations API client live (2026-10-15, 2e43a113):** HappiaClient reads the new `{status,data,pagination}` contract (prod recommender had been 502 since 2026-10-12); services reader and session-guarded check route `/api/happie/prueba-api`; outside-consumer guide `docs/happie-external-integration.md`. Open: P-094 (UI routes recomendar/recomendar-pasos still fail the strict happie.v1 schema).
- **Ship gate:** `npm run gate` locally + `escena:test` (405-scene golden, honesty, photo suites) in CI; free prod pulse `npm run prod:pulso`; rollback drill on prod 2026-10-11 all PASS (research/ciclo/SIMULACRO-ROLLBACK-2026-10-11.md).
- **72 h marathon STOPPED** at cycle 26 (2026-10-11 06:14; planned end 2026-10-12 16:44). Its state is in `research/ciclo/STATE.md`.
  From 2026-10-13 development runs entirely from this laptop (owner decision, D-041); origin/main is still `65edd83b` and the
  judge-fix task (card/quote count parity, honest edit banner, card price) never reached origin.
- **Local AI = Claude Haiku via Claude Code CLI** (no API key; `.env.local` IA_PROVEEDOR=claude, IA_CLAUDE_TRANSPORTE=cli,
  IA_LOCAL_ESFUERZO=medium); production stays on Gemini.
- **Shipped this marathon:** D-038 single quote; REQ-007 Phase 5 (customer 3D edits) + P-045 graceful rollback; REQ-013
  catalogue repositories Phases 1–5; Taller build sheet (complete: helium, positions, foil lines) + helium/pump/measures,
  recipe cards, size profiles, light/lens; Kontext resume + metallic tint; AI rating (one POST per turn); honesty tests
  (CUS-03/CUS-04); scenario matrix + property tests; colour resolver rewrite + limits; prerender guard; W4 training
  harness, scale policy, figures capability, diagnostics; scene-AI time bounds (P-054); kill switch on armada/imagen;
  production fixes (catalogue on Vercel, /3d id guard, guided-3D plan audit); e2e smoke per release.
- **W4 training** (30 owner photos, Haiku CLI, US$0): pass 1 → pass 2: proporciones 0.447 → 0.482, colores 0.365 →
  0.385, IoU 0.524 → 0.559.

## REQ-015 judge-fix (2026-10-13)
- Branch `feat/req-015-judge-fix` (24 commits, local, not pushed): count/price parity, chips by rules (D-043), cost cap (D-044), honest colour-swap, rating row. Gate GATE OK, tsc 0, lint 0 errors. Owner decides push/PR. Report: requirements/REQ-015-*/REPORT.md.

## Active focus
- REQ-017 implementation and verification completed on 2026-10-16 in isolated worktree `req-017-v2`. The curated event map, server schema enforcement/audit and exact-ID selectable menu are implemented; explicit customer requests and existing-plan edits retain precedence, and the saved widget schema is unchanged. `guiada:test`, tool property tests (45 tools, 1,720 invalid calls rejected), `npx tsc --noEmit`, lint (0 errors, 50 existing warnings), workspace builds and the Webpack app build pass; both independent review axes approve. The default Turbopack build rejects the external `node_modules` symlink before compilation; `npm run build -- --webpack` compiled and generated 83/83 pages, leaving 27 untracked standalone trace files under `pictures/node_modules` that are excluded from source changes and preserved. SPEC remains in progress and round-01 open because the Opus defaults are revisable assumptions, not five item-by-item product approvals (D-052). PLAN is done. No integration, commit, push or deployment occurred; P-101 tracks owner review. The older `req-017` worktree is untouched.
- REQ-014 branch `feat/req-014-motor-bandas`: PR #11 merged into `main` as `f8227ca5`. The PR merged 38 branch commits and 268 changed paths, including P-091 (`4916115f`), P-092 (`125548cf`), P-099/P-100 (`5c7649fb`) and earlier work already on this branch. P-092 retains centimetre-measured aro maxima with a strict 5% cap, `sin_banda` below 1 m and measured provenance distinct from PARIDAD. P-099 preserves the semiarco contour; D-050 bounds the empirical fill cap at 1.04, with versioned BOM, price and scene goldens. Seed 2 n=4000 yields 3,999/4,000, with only baseline E-03532 (guirnalda lujosa); no failure was allowlisted. The P-087 commit `a14a70fa` was already in the branch; its two later local modifications remain unstaged and uncommitted. Post-merge Quality workflow `38816458147` passed and Vercel reports deployment completed; no manual VPS deployment was started.
- REQ-016 (Guided 3D edit leftovers: exact undo and colour resolver) **DONE**: Verified and closed in local worktree `t12` on branch `feat/req-016-guided-3d-edit-leftovers-exact-undo-and` (commits 58f10c04..fb872bce). Exact in-memory undo (D-045, P-042), signed last colour order with suppressed redundant asking (D-046, P-058 A1-A4, D-047), reader-before-writer rollout compatibility (D-035) and untouched-piece replay protection (D-048, P-082). Gate 10/10 green (`GATE OK`), tsc clean (0 errors), lint 0 errors. REPORT.md written; PLAN.md status: done.
- REQ-015 implementation and verification complete locally, ready for owner review/commit/publication: chosen-idea chips by rules, shared price, honest color counts, durable quote cap. Restored ambiguous/composite idea prices show “Precio al elegir”; no session contract change. REPORT.md contains evidence; visual rating UI 9/9, contract 27/27, final types/build pass.
- 2026-10-14 follow-up: deterministic colour coverage passes in guiada:test (15 scripts); final lint 0 errors/49 warnings, workspace builds and app types pass. Application build/full gate not rerun for this test-only change.

## Top pending (see PENDING.md)
- P-075 still has real-Python UI and quote-cap follow-ups; see PENDING.md for the full queue. Two local follow-up modifications for P-087 remain outside the merged PR.

## Recent decisions (see DECISIONS.md)
- D-027 helium sphere volume · D-028/D-030 product judge timing · D-029 class-prefixed ids · D-031 manual VPS deploy ·
  D-032 owner-away defaults · D-033 dev servers allowed · D-034 no VPS deploy this weekend · D-035 reader-first persisted fields · D-036 review stop-rule · D-037 VPS approved · D-038 one quote · D-039 everything on · D-049/D-050 semiarco fill calibration with an empirical price-bounded cap.

_Last updated: 2026-10-16_
