---
status: draft
---
# maros-lab — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- REQ-001 M1 completed locally: guarded matchMedia test setup, pure scan filters and pure URL query state; all three tasks have separate reviewed commits.
- REQ-001 M2/T4 implemented and committed locally; both invoice sections use accessible URL-driven filters.
- REQ-001 M2 complete locally on 2026-10-13, ready for independent milestone audit; final feature suite passes 100 tests.
- REQ-001 M3 complete locally in `55ffc40` / `b16a07f`: responsive list/shared filter motion and tested filtered detail returns. Final 115 feature tests, typecheck and global lint pass; independent audit follows.
- REQ-001 M2/M3 audits and FINAL/session 12 complete: whole-branch spec/standards and final antagonist approve; `d9b92ff` corrects checkbox associations and revived titles. Final 125 feature tests, typecheck, global lint and trace pass. REPORT ready for owner review; no merge/push/deploy.

## Done
- REQ-001 T1 `ccd2376`: invoice page tests pass (21).
- REQ-001 T2 `073c7d5`: AND-combined pure filters; domain suite passed (10 tests) and antagonist re-review approved.
- REQ-001 T3 `f3fcd8e`: pure filter query parse/serialize; domain suite passed (14 tests), typecheck passed, and antagonist re-review approved.
- REQ-001 T4 `7222eb6`: filter bar/page wiring; 65 feature tests, typecheck and feature ESLint pass; spec and antagonist reviews approve.
- REQ-001 T5 `5b73e77`: page criterion/combination/accessibility tests and URL restoration; 100 feature tests, typecheck and feature ESLint pass. Antagonist re-review approves asymmetric section/empty-state coverage and explicit creation-day TZ.
- REQ-001 T6 `55ffc40`: both responsive surfaces keep exits visible in flow; shared chips/options remount on projection-identity changes. Exact 106-test suite/typecheck/feature ESLint and both re-reviews pass.
- REQ-001 T7 `b16a07f`: initial/dynamic reduced-motion and stable responsive title contracts; nine-control detail round trips, validated fixed destinations and direct/error/delete returns. Exact 115-test suite/typecheck/global lint and both reviews pass; 164 unchanged global lint warnings remain.
- M3 audit `64cfd28` resolves stuck exiting records; M2 audit `c1a524d` names active filters and tests draft resets. P-004 audit closed; P-010 metadata trace issue closed without changing the approved requirements.
- FINAL `d9b92ff`: P-009/P-011 closed with real-Motion regressions. Exact final Verification passes 15 files / 125 tests, typecheck and lint (164 existing warnings, 0 errors); trace lint clean. Full evidence and final report are in the REQ-001 folder/artifacts.

## Decisions
- D-001: date filtering uses issue date, otherwise local creation day when absent.
- D-002: replace the current browser query for local filter edits, preserving unrelated parameters/hash.
- D-003: existing Popover supplies measurable reversible option/chip surfaces; sync exits avoid overflow clipping.
- D-004: validated query state follows fixed detail/list hrefs, including explicit/error/delete returns.

## Not done / dropped
- Build/full-project tests/live browser checks were not run because lab verification is restricted to the approved plan; P-002's 11 unrelated baseline failures remain. P-005 visual motion confirmation and the design/performance/typing proposals remain open. Plan is done, spec awaits owner review/merge; no publication.

## Carried over to next week
- P-005 browser review and the PENDING.md design/performance proposals; owner merge decision.
