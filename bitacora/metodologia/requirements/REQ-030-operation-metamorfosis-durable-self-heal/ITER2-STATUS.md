# REQ-030 iteration 2 — status at interruption (2026-10-28, usage limit)

- REQ-021 durable run PAUSED (`bt-durable pause`, request fff43cd3…). T2.6:k1 and T3.2:k1 wait on owner decisions d1
  (runtime defect). Do not answer them until the WIP below is finished and deployed.
- Live bug found and fixed on main (366cbf372): the engine (a systemd service) passed its own INVOCATION_ID and
  BT_DURABLE_DATABASE_URL to agent units → a1 attempts of T2.6/T3.2 orphaned (LAUNCH_CONFLICT). Evidence:
  evidence/iter2/orphan-units-20261028.txt. Engine NOT restarted yet with the fix.
- T3.2 already has a valid owner receipt (RUN.attestations/T3.2, bound to att-0059): with item 3 it reconciles to PASS
  (answer d1 `reverify` after deploy).
- WIP branch `req030-iter2-wip` (2ed7493ac), not merged:
  - item 2: `adapters/briefs.py` (legacy `owner_notes`/`contract_notes`, history across runtimes), continuation note;
    legacy wiring fix (design contract notes were dropped by `executor.briefs.notes = ...`). Parity test NOT written.
  - item 3: M6Verifier `attestations_for` + `on_verdict` (RUN.notes), classifier MANUAL_EVIDENCE_REQUIRED, owner
    `reverify` loop (patch bt-task-owner-reverify), reconcile asks owner first (patch bt-task-reconcile-asks-owner),
    `bt-durable attest`. E2E NOT written.
  - item 1: control/subplans.py, subplan lines refs/bt/subplan/..., adapters/composition.py (bt_composition),
    bt.run behind patch bt-run-subplans. test_durable_subplans: 3 pure tests pass; e2e fails — first sync runs before
    the run line's `-base` pin exists (LINE_BASE_UNKNOWN). Fix: create the run line + pin in `sync` when missing.
    REQ-021 needs `refs/bt/line/pictures/REQ-021/r15/pictures-base` = fa101a47 pinned before deploy.
- Subagents launched in worktrees for items 5 (M2 router), 6 (panel/projection), 7 (Pydantic plan contracts),
  8 (shell file guard): their branches must be reviewed and merged.
- Pending: items 4, 9, 10; full regression; deploy (backup + smoke); resume REQ-021; REPORT.md.
