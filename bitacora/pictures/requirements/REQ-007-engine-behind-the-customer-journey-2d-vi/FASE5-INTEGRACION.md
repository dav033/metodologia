# REQ-007 Phase 5 — client integration review (FASE5-INTEGRACION)

Reviewed against `PLAN-v3.md` §Phase 5 at repo commit `6e1388af` (branch `feat/req-015-judge-fix`, repo `demo-decoracion`).
Scope: client wiring only. Everything below is stated as it exists in code today; anything not present is listed under
"Not built / follow-ups". Pinned by `scripts/test/test-motor-guiada-ediciones-contrato.ts` (10 tests, no network, no DB).

## 1. Module boundaries

| Layer | Module | Responsibility |
|---|---|---|
| Contract (shared, no `server-only`) | `src/lib/guiada-motor/editar-contrato.ts` | `RUTA_EDITAR_MOTOR`, `CuerpoEditarMotor`, `EdicionDelCliente` (`ops` / `pedido` / `cambio`), `CODIGOS_FALLO_EDITAR`, `FalloEditarMotorSchema`, `TurnoEdicionSchema`, `RespuestaEditarMotorSchema`. Imports motor types only as `import type`. |
| Route (server) | `src/app/api/guiada/motor/editar/route.ts` -> `src/lib/guiada-motor/editar-motor.ts` (`atenderEditarMotor`) | session, same-origin, body validation, plan token/hash/signed-spec check, flag/cut-off, per-browser edit cap, apply edits, re-arm via piece cache, price via Python `lista-materiales`, new signed plan, audit row. |
| Server mapping | `src/lib/globos3d/motor/{ediciones-espec,edicion-desde-pedido,ediciones-color,ediciones-pieza,plan-actual-espec}.ts` | pure ops on the spec; chat `PedidoEdicionPlan` and panel `CambioPanelV1` -> `EdicionEspecV1`; `planActualDesdeEspec` (exact projection of the spec for the chat model). |
| Browser transport | `src/components/guiado/edicion-motor3d.ts` | `crearDependenciasEdicion3d` (POST, deadline `PLAZO_EDICION_MS`, response validated with the contract schemas), `FalloMotor3dApagado`, `avisosDelCambio`. No React, no motor code. |
| Panel adapter | `src/components/guiado/ajuste/ejecutar-ajuste-3d.ts` | `aCambioPanel` (exhaustive `switch` over `CambioPlan`), `ejecutarCambio3d`; sends the Sempertex code of the colour row being replaced when the signed spec allows it. |
| Chat adapter | `src/components/guiado/ajuste/edicion-chat-3d.ts` | `ejecutarEdicionChat3d`: forwards the already-understood `PedidoEdicionPlan` with the chat `turnoId`; builds the colour-diff confirmation from the new plan. Plugged into `edicion-chat-guiada.ts` (`dependencias.motor3d`). |
| Panel state | `src/components/guiado/ajuste/usarAjustePlanGuiado.ts` | `hacerCambioDelPanel` picks 3D (`motor3d` dependency present) or the unchanged Python path; `useAjustePlanGuiado` runs one change at a time. |
| Publication | `src/components/guiado/ajuste/publicar-ajuste-plan.ts` | `usePublicarAjustePlan`: replaces the plan widget only if the base hash is still current; image/undo side effects run after React commits. |
| Undo | `src/components/guiado/deshacer-ajuste.ts` | pure stack of previous signed widgets (max 4, in memory only, 3D plans only); undo restores the earlier plan without calling the server and rejects an expired approval token. |
| Plan for the chat model | `src/components/guiado/plan-actual.ts` | `planActualDelPlan`: uses the exact `planActual` carried by a 3D plan, falls back to the lossy `planActualDesdePlan` for Python plans and for 3D plans saved before Phase 5. |
| View | `src/components/guiado/VistaGuiada.tsx` (2 355 lines) | wires all of the above (`crearDependenciasEdicion3d` at ~l.1026, `deshacerUltimoAjuste` ~l.978). |

Layering holds: the browser bundle reaches the motor only through types (asserted by the contract test); the route owns every
state change; the client never edits the plan or the spec.

## 2. Data flow (one edit)

1. Customer asks in the chat or moves a control in "Ajustar mi plan". The 3D path is taken only when the visible plan widget has `motor === "3d"`.
2. Browser: `POST /api/guiada/motor/editar` with exactly `{ plan, turnoId?, edicion }`. `plan` is the current signed plan (token, hash, signed spec); `edicion` is one of `{tipo:"ops"}`, `{tipo:"pedido"}`, `{tipo:"cambio"}`. `turnoId` is the chat message id (chat edits) and is omitted for panel edits, in which case the server generates one.
3. Server: verify -> map to spec ops -> apply -> re-arm changed pieces -> price -> new plan with new `plan_hash` and new approval token bound to the same browser -> response.
4. Response (`RespuestaEditarMotorSchema`, strict): `plan`, `cotizacion`, `descripcion` ("Ultimo ajuste: ..."), `confirmacion`, `avisos`, `noAplicadas`, `tocadas`, `turno`.
5. Client publishes only if the base hash is still the visible one; otherwise the chat says the plan changed meanwhile. A stack entry for undo is recorded.
6. Failure: a `codigo` from `CODIGOS_FALLO_EDITAR` plus a customer sentence ("No pude: ..."). 409/422/429 sentences are shown; 400/401/500 use a generic fallback; a `fallback.razon` (cut-off, expired approval) becomes `FalloMotor3dApagado`. The plan stays as it was.
7. A bad or old signed plan makes the server answer with the recalculation message; the Python flag alone never blocks editing a 3D plan already open (P-045).

## 3. Turn data for feedback: `{turnoId, espec antes/despues, capturas}`

Exists:
- `turno = { turnoId, antes: { especHash, espec }, despues: { especHash, espec } }` is returned by every successful edit (`TurnoEdicionSchema`). `especHash` equals the plan hash of the plan before/after.
- Chat edits: `VistaGuiada` stores `edicion3d: { turnoId, antes, despues }` on the message (`estado-guardado.ts` schema); `escenasDelTurnoGuiado` in `CalificacionGuiada.tsx` hands `{antes:{espec}, despues:{espec}}` to the rating controller as the turn's scenes, so the rating row carries both specs. `turnoId` is the chat message id, i.e. the one used by the rating.
- Panel edits: the turn is returned and its `turno_id` and both spec hashes are logged via `registrarAjuste` (`extra` in `hacerCambioDelPanel`). It is NOT stored on the message and has no rating.
- Server audit row (`PLAN_3D_EDITADO` / `PLAN_3D_EDICION_RECHAZADA`) carries `turno_id` when it is a UUID, base and new hash, touched pieces.

Not built:
- `capturas`: the feedback controller supports an optional `capturas()` upload (`/api/feedback-ia/capturas`), but `CalificacionGuiada` does not pass it, so guided 3D turns upload no screenshots today.
- Ratings for panel edits (no `edicion3d` on those messages).
- The `PRODUCTOS_FEEDBACK=["taller","cliente"]` contract is unchanged; this phase adds no new product value.

## 4. Python path untouched

- `/api/plan-editar`, `ejecutar-ajuste.ts` (Python), `edicion-chat-guiada.ts` Python branch and the classic chat are unmodified in behaviour: `hacerCambioDelPanel` and `edicion-chat-guiada.ts` take the 3D branch only when a `motor3d` dependency exists, and `VistaGuiada` supplies it only for `motor === "3d"` plans.
- The contract module has no import of Python adapters (asserted by the test). The route calls Python only for pricing (`lista-materiales`), as the plan, armada and image routes already do.
- 3D plans never call Taller tools or the Python catalogue search; colours resolve through the Sempertex crosswalk, and a colour that cannot be resolved is a "No pude" (the plan's stated risk).
- Rollback stays "flip the flag": 3D plans already open keep editing on the 3D routes.

## 5. Review vs PLAN-v3 §Phase 5

| PLAN-v3 item | State |
|---|---|
| `ediciones-espec.ts`, `edicion-desde-pedido.ts`, `POST /api/guiada/motor/editar`, `planActualDesdeEspec` | Exist and are used. |
| `edicion-chat-guiada.ts` / `usarAjustePlanGuiado.ts` inject 3D dependencies instead of `/api/plan-editar` | Done (`motor3d` dependency, `edicion-chat-3d.ts`, `ejecutar-ajuste-3d.ts`). |
| `AjustarPlan` size control -> `tamano_pieza`/`tamano_globos`, colour slider -> `proporcion_color` | Server ops exist (`tamano_pieza`, `tamano_globos`, `proporcion_color`). Panel `CambioPlan` types forwarded today: `protagonismo`, `cantidad`, `tamano`, `tamano-globos`, `tamano-todo`, `medidas`, `agregar/quitar/reemplazar-color`, `quitar-pieza`. UI re-wiring of the size and colour controls is task T7 and is not claimed here. |
| Forward-compatible turn data | Spec before/after + `turnoId`: yes for chat. Captures: no (section 3). |
| `asistente-guiado/route.ts` l.236 aviso engine-neutral | Not re-verified in this review. |
| Tests | `test-motor-guiada-ediciones.ts`, `-ediciones-mapeo.ts`, `-editar-ruta.ts`, `test-deshacer-ajuste-3d.ts`, plus the new `test-motor-guiada-ediciones-contrato.ts` (client <-> route contract). |

## 6. Follow-ups

1. T7: customer UI wiring per this document (size control -> `tamano_pieza`/`tamano_globos`, colour slider -> `proporcion_color`) with cases in `test-ui-plan-motor3d.ts`.
2. Store the panel turn (`edicion3d`) on the message if panel edits should be ratable; decide with the feedback owner.
3. Provide `capturas` for guided 3D turns once a stable scene capture exists in the guided view.
4. `VistaGuiada.tsx` is 2 355 lines (over the 500-line alert); any further wiring should extract by responsibility first (T7 already says so).
5. `usarAjustePlanGuiado.ts` reads `espec` through a cast (`base as PlanGuiado & { espec?: unknown }`, same pattern as `motor3d/firma-plan.ts`): the signed spec is an untyped extra on `PlanGuiado`. A typed accessor would remove the casts.
6. Undo stack is per view session (lost on reload by design, D-035); documented in `deshacer-ajuste.ts`.
