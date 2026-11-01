# Solver 20261101-004604-27e4 — pictures REQ-021 r35

## Trigger
`pictures:REQ-021:r35:ended:eaad731aa25e9029`: run ended blocked, gate CG-4 rejected `git_text_conflict`; T3.15 blocked.

## Origin
CG-4 composes SP-1, SP-2 and SP-14. SP-2 and SP-14 both edit `src/components/cuentas/MenuCuenta.tsx`; the composer
recorded a resolution request (`composition/resolutions/2a49ab6d27d4b6eddfe3fead986233c9.{json,diff3}`, base a48ce92,
ours 4377350 = SP-2, theirs bd6d7cc = SP-14) at r32 (2026-10-31 21:45) and nobody wrote `.resolved`, so r32 and r35 were
both rejected on the same three blobs.

## Fix
SP-14's only change is a `/planes` link using `copy.plans`; SP-2's version (4377350) already contains that link and
`plans` in its texts file. The union is therefore SP-2's file: wrote it byte-exact to `2a49...resolved`.
Then `bt-durable retry-task pictures REQ-021 T94 --by solver`: CG-4 recomposed as C2 with no conflicts (telemetry
`gate_recompose`, `gate_composed` state candidate), run reopened as `bt:pictures:REQ-021:r35@2`, status running, T94 running.

## Not done / open
- No metodologia code changed, nothing integrated, no D-NNN. Gap: a resolution request that is unresolved for hours
  (r32 -> r35) is only noticed by the solver after the run ends; the `resolution_after_seconds` trigger did not fire in time.
- T3.15 is still `blocked`: its round-2 audit was rejected with "changed 6632 file(s) it did not declare:
  .verification-snapshot/scripts/test/..." (telemetry `audit_blocked`, 2026-11-01 00:43). I could not find where
  `.verification-snapshot/` is created (not in metodologia/skill nor in the pictures repo scripts) before the engine
  told me the triggers were resolved. Next solver/trigger should start there (bt_audit_gate.stray_changes counts it).
- Other stale MenuCuenta requests (9089, 9c0b, a3ff, a9cb) are for older blobs; left alone.
