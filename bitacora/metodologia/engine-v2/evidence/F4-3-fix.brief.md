# Task F4-3-fix — published subplan facts must track accepted work, not survive a redo

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding). Your worktree is `ev2/F4-3` at `c129d7179`
(worker commit `7c1289f66` + lead flow-bus commit). Commit on top; do not rewrite history.
Authority: `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/ENGINE-F4.md`, `SCHEMA-1.3.0.md`,
`/home/david/dev/.engine-v2-wt/F4-3.brief.md`. Own: `skill/scripts/bt_scheduler_core/` (code, README, tests),
`skill/scripts/bt_scheduler_adapter.py`, `skill/scripts/tests/test_scheduler_subplan_adapter.py`, `skill/references/modules.md`.

## Independent review findings to fix (lead rulings in brackets)
1. [medium, spec] A rework of an accepted member task leaves the subplan's published-version fact in place, so
   `subplan_status` stays `published` and the composition gate opens on redone, unpublished work
   (`subplans.py:158`, `gate_ready/gate_waiting` 172-181). Repro: T1–T3 accepted, `record_subplan_version("SP-1", 1, …)`,
   then `core.rework(("T1",), "op", "redo")`, redo T1–T3 → gate task T4 becomes active with no new publication.
   [Ruling: bind each version fact to the accepted identity of its subplan's work — at least the accepted attempt of
   the subplan audit task (and, if cheap, a digest of the accepted attempts of all member tasks). A fact whose bound
   identity no longer matches the current accepted state is stale: `subplan_status` must not report `published`,
   gates wait, attention shows why. Keep the stale fact in history/audit; the next publication is version N+1.]
2. [gap, spec] A gate task already READY (or reserved but not dispatched) when its facts become stale (revision or
   rework) must not start: re-check `gate_waiting` at promotion and at the reservation/dispatch boundary
   (`scheduler.py` ~387, `promote_ready`). Return it to pending with the attention reason.
3. [low, standards] A plan revision that keeps a subplan's work untouched (rebase conserving T1–T3) currently makes
   its fact stale and refuses re-recording the same version. [Ruling: allow an idempotent re-bind of the SAME version,
   commit and manifest to the new plan revision when the bound accepted identity (finding 1) is unchanged; any
   other change still requires N+1.] Document the rule in README and modules.md.
4. [gap] Publishing a subplan version requires the subplan's audit task to be accepted in the current state;
   otherwise `NOT_ALLOWED`.
5. [cosmetic] Re-recording a candidate composition with a different manifest returns a misleading "terminal" message:
   give it a precise message (candidates under the same id stay immutable; a new candidate needs a new id), no
   semantics change.

## Constraints
State schema: extend schema 4 compatibly (facts written by `7c1289f66` load; missing identity = stale for gate
purposes, never published). Legacy 1.2 plans byte-identical behaviour and fingerprints. Keep modules < 500 lines.

## Tests (write failing first)
The exact repro of finding 1; READY-gate-then-stale for both revision and rework; idempotent re-bind after an
unaffected rebase and refusal after an affected one; publication before audit acceptance refused; old schema-4 facts
load. Then module suite, `tests/test_flow*.py`, adapter test, and the full root suite per RULES.md.
