# Solver 20261101-214559-5b5d — pictures REQ-021 r39

## Trigger
Two reconcile resolution requests, SP-5×SP-3 (D-297): `Taller3D.tsx` (b22fcece…) and `SelectorAmbienteVisor.tsx` (c579d638…). No task or decision behind them.

## Origin
Genuine text conflicts, no system defect:
- SP-5 (ours) wraps the viewer in `TextosProductoProvider` + `IdiomaTallerEdicion` (bilingual UI) and translates the `aria-label` via `textoTallerEdicion`.
- SP-3 (theirs) changes the root container class to `fixed inset-x-0 bottom-0 top-[var(--barra-cuenta-alto,0px)]` and moves the light/lens selector into a flex column in `sobreVisor` (drops its absolute positioning).
The changes are orthogonal; neither excludes the other.

## Fix (resolutions written, nothing committed, no ref moved)
- `b22fcece….resolved`: ours' two provider wrapper lines + theirs' root `<div>` class. Closing tags for both providers already exist in the merged tail (lines 1037-1038); no conflict markers left.
- `c579d638….resolved`: ours' translated `aria-label` + theirs' className without `absolute left-1/2 top-16 -translate-x-1/2` (the selector is now laid out by its parent column at Taller3D.tsx:791).

## Rule / decision
None needed: no engine defect; the reconcile loop opened the requests correctly.

## Not done
Did not run the merged tree's typecheck (the engine's next reconcile pass combines files and moves the lines, or opens the next round in the inbox).
