# Solver 20261101-174711-3b88 — pictures REQ-021 r39

**Trigger:** `resolution` SP-12×SP-10 (D-297 reconcile): `src/app/api/asistente-guiado/route.ts` needed a recorded
resolution; no task or decision behind it.

**Origin:** a real overlapping edit, not an engine defect. Both subplans replaced the same final line
`mandar("fin", {... result: datos })` in `turnoGuiado`:
- ours (SP-12): `ProtectorStreamRecomendaciones.finalizar(...)` wraps the result, may replace the reply, strips `decoraciones` while recommendations run.
- theirs (SP-10): `construirContenidoVisible` re-sanitizes the reply and translates the decorations for English.
It was the only hunk in the file; all imports from both sides (`getRagPool`, `construirContenidoVisible`, `DecoracionSempertexSchema`, `ProtectorStreamRecomendaciones`, ...) were already merged.

**Fix (resolution):** wrote `.../resolutions/397579b9ac08eda823b51203c92f4397.resolved` = the diff3 merge with the hunk replaced by
SP-10's content-visible block first (mutates `reply`, `datos.decoraciones`), then SP-12's finalization block
(`finalizar(datos,...)`, `resultadoFinal`, `mandar("fin", { reply: respuestaFinal.reply ?? reply, ... })`).
Order matters: the translated decorations feed the protector, and its recommendation reply still wins in recommendation turns
(where decorations are dropped from the result anyway). `reply` is already `let`; `contexto`, `idioma`, `recomendacionesListas` are in scope.
Checked: no conflict markers left; TypeScript transpile reports 0 syntax diagnostics. No ref moved, nothing committed to the project.

**Rule / system change:** none. The two edits are semantically composable but touch the same statement, which no textual
merge rule can settle safely.

**Decision:** none open (reconcile request only). The engine's next pass combines the line.

**Could not do:** typecheck the merged file against the full merged tree (not materialized for me); the engine's next pass / the
subplan checks will do it. If it opens a next round, it arrives in the inbox.
