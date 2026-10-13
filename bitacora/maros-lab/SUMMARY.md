# maros-lab — Summary

> Isolated frontend laboratory: `/home/david/dev/maros-lab/maros-next`, no remote and no env files. Never start a server, API, worker or migration, and never call the real API. The real Maros project has separate memory at `/home/david/bitacora/maros`; its production status and backlog are not this lab's status.

## Purpose
Prove the automatic milestone workflow against a real-codebase invoice-list feature: several URL-driven filters plus shared-element motion in the same view.
This scope comes from the owner's 2026-10-12 request; no new business interview took place.

## Current state
REQ-001 tasks T1–T7, independent M1/M2/M3 audits and FINAL/session 12 closing work are complete on `feat/req-001-invoice-list-filters-and-shared-element` at `d9b92ff`. Baseline: `3ea1a97`; full diff: 23 files. Plan is done; spec remains in-progress for owner review/merge.
Fresh whole-branch spec and standards reviews approve; antagonist approves the final correction commit. P-009/P-011 are closed: unique checkbox instances and recovered shared-title projection have real-Motion regressions.
Exact final Verification passes 15 feature files / 125 tests, typecheck and global lint (0 errors, 164 preexisting warnings, none in invoice-scans); diff and trace checks pass. Evidence: `artifacts/REQ-001-final-session12-postfix-verification.log`; final REPORT: `requirements/REQ-001-invoice-list-filters-and-shared-element/REPORT.md`.
Nothing has been merged, pushed, deployed or published.

## Active focus
- Owner review of REQ-001's REPORT and local feature branch; no further implementation is scheduled.
- Keep R5 visual verification explicit: real Motion presence is tested, but jsdom cannot certify pixel movement. P-005 remains an owner review before merge; the lab forbids starting the server.
- Preserve the original snapshot's unrelated work; no backend or API contract change belongs to this requirement.

## Top pending (see PENDING.md)
- P-005: desktop/mobile visual motion pass, title/detail return and reduced-motion preference.
- P-012: check rapid typing with delayed Next URL propagation in that browser pass.
- P-006/P-013/P-014: owner decisions on chip-removal focus, amount input and mobile panel compactness.
- P-007/P-008/P-003: unmeasured prefetch behavior, filter propagation after creation and multi-field search semantics.
- P-002: 11 unrelated baseline whole-suite failures; outside the approved final Verification.

## Recent decisions (see DECISIONS.md)
- D-001: issue date first, otherwise local creation day.
- D-002: replace browser query state, preserving unrelated keys/hash.
- D-003: measurable Popover options/shared chips and normal-flow exits.
- D-004: validated query state follows fixed detail/list destinations.
- D-005: nested shared titles do not hold row/card exits open.

## Known limitations
- Build and full-project tests are outside the plan's allowed final checks. Earlier independent audits reproduced the same 11 baseline failures; this closing session does not claim the whole project is green.
- Existing CounterpartySelect React warnings (43 in this run) and global lint warnings remain.
- Trace lint is clean for all R1–R7/T1–T7 and the project; P-010's metadata issue is closed without a SPEC parser change.
- Workflow is unavailable in this harness; native reviewer/runner agents completed closure. No started agent or job remains running.

_Last updated: 2026-10-13_
