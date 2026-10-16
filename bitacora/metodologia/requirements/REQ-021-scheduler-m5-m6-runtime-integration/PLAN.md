---
req: REQ-021
status: approved
created: 2026-10-15
---
# Plan — Scheduler M5/M6 runtime integration

## Approach

Reuse the isolated M6 package after revalidating it, then integrate it selectively into the current M1/M3/M5 tree.
The composition remains caller-controlled: `quality_store_path` opts in to M6 and the existing `VerificationPort`
remains usable otherwise. A deterministic local E2E proves the real M5/M6 chain without provider spend.

## Global constraints

- Keep M1 authoritative; do not change M1 state, contract signatures, or verdict semantics.
- Preserve the source M6 worktree and all concurrent dirty M2/M4/M5 files.
- Do not import M1/M3 implementation packages outside their established adapters.
- M6 checks run only in its required bubblewrap sandbox; no insecure fallback.
- No global activation, install, real-provider call, production state change, push, merge, or commit.
- M5 T19 stays subject to its approved fresh quota preflight; no provider starts unless the threshold passes.

## Tasks

- [x] T01 — Audit the isolated M6 source, current contracts, repository import boundaries, and shared worktree state · verify: source M6 package 66/66, real-M3 E2E 1/1, M1 boundary 6/6 · covers: R1, R2, R8
- [x] T02 — Copy only M6 source/package/tests into the current checkout; adapt the M1/M3 adapter to established public adapter imports · files: `skill/scripts/bt_scheduler_quality/**`, `bt_scheduler_quality_adapter.py` · verify: M6 package 66/66, real-M3 E2E 1/1, M1 boundary 6/6 · covers: R1, R2, R8
- [x] T03 — Add explicit M6 composition and ordered lifecycle cleanup in the existing executor wiring · files: `bt_scheduler_executor_wiring.py`, `bt_scheduler_executor_adapter.py` · verify: composition guards and shutdown-order tests · covers: R3–R6, AC01–AC03, AC06
- [x] T04 — Add real Planner/M1/M2/M3/M5/M6 E2E for rejection, recovery, snapshot continuation, and later acceptance · files: `skill/scripts/tests/test_scheduler_m1_m6_e2e.py` · verify: 4 tests passed, including the full end-to-end chain · covers: R7, AC04–AC05
- [x] T05 — Reconcile module boundaries, wheel metadata, installed-package checks, and scoped lint · files: `skill/references/modules.md`, `pyproject.toml`, `tests/migration/test_package_install.py`, `skill/scripts/tests/test_scheduler_integration.py` · verify: pending final integrated run · covers: R8, AC01–AC03, AC06, AC08
- [ ] T06 — Refresh the T19 quota preflight and run the bounded experiment only if two distinct fresh routes meet the approved <=50% use gate · verify: opt-in preflight and T19 receipt · covers: R9, AC07
- [ ] T07 — Run the relevant integrated suites, audit the exact diff, update REQ-019/REQ-021 reports and project memory · verify: recorded test outputs and final acceptance matrix · covers: AC01–AC08

## Verification

Prove both modes: default/custom `VerificationPort` injection remains unchanged, while explicit M6 wiring processes the
approved M1 order against M3's preserved attempt snapshot, produces a content-addressed evidence manifest, and sends
the correlated verdict through M1. The end-to-end rejection must enter M1 recovery and a later independent M6 PASS must
be the only event completing the task. Check that M1/M3 source state, plans, handoffs, and concurrent work remain
unchanged. Separately report the T19 live gate and every test not executed.

## Rulings

- The owner's direct full-chain request approves this integration plan.
- M6 is opt-in through a caller-supplied private store path; M6 `NEEDS_REVIEW` remains in M1 `VERIFYING` until an
  explicit operator resolution.
- Reuse the M6 behavior and tests from its isolated worktree, but do not copy its REQ-020/D-042 files because those
  identifiers are already used by current M2 quota work. Record this integration as REQ-021/D-043.
- No M1/M3 contract change is required; M6 reaches their public types through the current adapter boundary.

## Progress log

- 2026-10-15 — Audited M6 at isolated base `8749e44`; current source tests passed (66 package, 1 real-M3 E2E, 6 M1
  boundary). Found no central runtime wiring, a stale base relative to current M4/M5, and direct M1/M3 imports in the
  M6 adapter that must be reconciled with the current module boundary before integration.
- 2026-10-15 — Integrated opt-in M6 composition and ordered shutdown. The local Planner/M1/M2/M3/M4/M5/M6 E2E passed:
  M6 FAIL left the first M1 attempt rejected, M5 recommended retry, M2 emitted a distinct decision, M3 resumed the
  captured snapshot in a new worktree, and M6 PASS completed the second attempt. M4 stream events and source checkout
  preservation were asserted. Boundary, wheel, and remaining lint/diff closeout checks are tracked in T05/T07.
