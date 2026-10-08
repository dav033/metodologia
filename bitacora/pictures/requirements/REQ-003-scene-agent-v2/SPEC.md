# REQ-003 — Scene agent v2 (sees inside pieces, targets by format/size/part, many more tools)

Status: IN PROGRESS (owner, 2026-10-08: "send agents aggressively"; stay on Gemini Flash; semantic + programmatic +
rules + many tools).

## Owner rules
- Every decoration and structure is made of balloon types (formats) or store products, identifiable by parts. Always.
- The AI must change exactly what is named: "the link-o-loons of the decoration Ramas", "the colours of the R-24s",
  never the whole piece.

## Root causes found
The AI could not see inside pieces (`ver_escena` = one line per piece), had no selector below the piece level, and
no trade glossary. "More R-24" only had `tamanos` (allowed list) → no change (log 3d-20261008-140634).

## Design (contract in main `bfe3447f`)
- `parte` on every built balloon/tube; `partes-globos.ts`: SelectorGlobos {formatos (exact/family), partes (prefix),
  colores}, `inventarioDe`, `contar`.
- Agents (worktrees): A1 decorations labelled + audit (e3a) · A2 structures labelled + products + audit of the whole
  Library (e3c) · A3 glossary `glosario-taller.ts`, `ver_pieza`, `buscar_en_escena`, prompt vocabulary (e3d) · A4
  `editar_globos` precise edit engine with rebuild verification (e3e) · A5 selection context, `preguntar_usuario`,
  verify loop, layout/group tools, evaluation bank from the owner's logs + paid eval script with cap (e3f).
- Already merged: `ajustar_tamanos` (`98046b48`).

## Acceptance
- 100 % of balloons in the whole Library have valid format, colour made in that format, and a part label.
- Offline bank: every owner request is satisfiable by tools; paid eval (cap US$0.50) scores the model.
- "Cambia los link-o-loon de Ramas a verde" changes only those; "los R-24 a azul reflex" only the R-24.
