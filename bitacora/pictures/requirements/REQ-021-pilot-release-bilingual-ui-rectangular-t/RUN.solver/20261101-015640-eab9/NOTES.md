# Solver notes 20261101-015640-eab9
- Trigger 1 T3.15 blocked (audit F1 high): audits a601 etc. audited a gutted tree (1933/8564 files). Origin found: the
  r35 SP-3 subplan line ref (refs/bt/subplan/pictures/REQ-021/r35/pictures/SP-3 in /home/david/dev/pictures-wt/asesor)
  advanced to the gutted snapshots 3485dbb3..fca8ff81 (a201..a601); last good tip 860f035e (8564 files).
  D-287 compares to the line tip, which is itself gutted -> guard inert.
- Worktree: ~/.local/share/bitacora-solver/pictures/20261101-015640-eab9/wt (branch solver/20261101-015640-eab9)
- Queued in inbox: T94:d1@k1 decision; 2 resolution triggers (EditorConjuntoMesa.tsx, ListaEscenografia.tsx) for T94.
- TODO: find how integrate() moved the line to a gutted snapshot; guard it; repair SP-3 ref; retry-task T3.15; then T94.
- DONE: D-288 integrated (main 266388e19). SP-3 r35 line restored to 860f035e (was fca8ff81). retry-task T3.15 sent 
  (request 670e07bc...). Archived 291 stale resolution requests (theirs=3485dbb3, the gutted snapshot) into
  composition/resolutions/superseded-gutted-3485dbb3/ (moved, not deleted).
- T94 decision d1@k1: INTEGRATION_CONFLICT "(line of SP-5)": gate task T94 base leaves conflicting lines out
  (_caught_up) but integrate() rejects the same conflict (own="" for gates) -> every retry meets it. Plan: D-289, leave
  out conflicting non-required lines for gate tasks in integrate(); need >=1 line taking it.
- Remaining stale-ish requests: MenuCuenta 01:40 (T94 a1 vs run line), 22:48 textos-acceso (old).
