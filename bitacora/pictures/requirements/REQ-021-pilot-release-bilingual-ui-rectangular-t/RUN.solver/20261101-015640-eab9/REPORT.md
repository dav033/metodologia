# Solver report 20261101-015640-eab9 — pictures REQ-021 r35

## Trigger
`pictures:REQ-021:r35:T3.15:blocked:9ada...`: T3.15 (SP-3 audit) blocked, F1 high open after 4 remediation rounds.
Inbox: decision `T94:d1@k1` (CG-4 gate task, «integration conflict keeps coming back») and ~45 `resolution` triggers for T94.

## Origin 1 — T3.15 audited a gutted tree (D-288)
- a201 ran in a half-built worktree (1933 of 8564 files). Its snapshot descends from the SP-3 line tip, so
  `GitLineIntegrator._merge` fast-forwarded the **SP-3 subplan line** onto it; a301..a601 did the same.
- D-283/D-286/D-287 only guarded where a snapshot is *continued from*, and D-287 compared with the line tip — which was
  itself gutted — so the guard never fired (a501, a601 continued from f3f5297/fca8ff8). Audit said «source absent» (F1).
- Fix: `integrate` refuses a snapshot with under half of the subplan line's files (run line when none); `sync` reports it.
  Test `test_a_gutted_snapshot_is_never_integrated_into_a_line` (red before). Merge 266388e19, D-288.
- Data repair: `refs/bt/subplan/pictures/REQ-021/r35/pictures/SP-3` fca8ff81 -> 860f035e (8564 files, update-ref with
  old-value guard). `bt-durable retry-task T3.15 --by solver` started a701 from 860f035e.
- 291 resolution requests whose `theirs` was the gutted 3485dbb3 (delete/modify artefacts of composing the shell) were
  moved to `.state/durable/composition/resolutions/superseded-gutted-3485dbb3/` (moved, not deleted).

## Origin 2 — gate task T94 refused for conflicts its own base had left out (D-289)
- `_caught_up` leaves out of a gate task's base every downstream subplan line that conflicts; `integrate` then merged the
  snapshot into the same lines and refused for the same conflict («line of SP-5»). A gate has no own line (`own=""`), so
  every retry met it (decision T94:d1) and each attempt wrote ~15 new resolution requests (snapshots differ per attempt).
- Fix: for `home` = gate, a conflicting subplan line is left out and reported (`left`); refused only when no subplan line
  takes it. Test `test_a_gate_task_leaves_out_the_lines_its_base_left_out` (red before). Merge 96b787087, D-289.
- Decision answered: `T94:d1@k1` -> `reverify` (checks had passed; only integration failed).

## Not done / notes
- The remaining open resolution requests (T94 attempts a1/a2, older runs) were not resolved by hand: they are per-attempt
  artefacts; D-289 removes the need.
- Proposal: engine restart still SIGKILLs running git children; `.verification-snapshot/` tracked in pictures origin/main.
