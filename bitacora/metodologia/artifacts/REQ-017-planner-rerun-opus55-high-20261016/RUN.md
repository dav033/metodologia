# Planner skill smoke run — REQ-017

- Model: Claude Opus 5.5 (`claude-opus-5-5`), effort `high`.
- Runner: Claude Code CLI 2.1.301; exit code 0; elapsed time approximately 7 minutes.
- Profile: metodologia `planner`; read-only permission mode and tools `Read`, `Grep`, `Glob`.
- Invocation: `claude -p --agent planner --model claude-opus-5-5 --effort high --permission-mode plan --tools Read Grep Glob --no-session-persistence` (wrapped in a 1,800-second timeout; prompt/result streams were captured outside the repository).
- Scope: temporary planning rerun only. Parent SPEC, PLAN, round, product source, and approval state were not changed.
- Planner's own `bt_planner check`: not run; the model had no Bash or write tools.
- Post-run command: `PYTHONPATH=skill/scripts python3 -m bt_planner check /home/david/dev/metodologia/bitacora/metodologia/artifacts/REQ-017-planner-rerun-opus55-high-20261016 --repo pictures=/home/david/dev/pictures` → exit 0, `OK: PLAN.json is publishable`.
- Check warning: `T2.1` and `T3.1` share `event-structure-policy` without an `after` edge; the scheduler must serialize that shared-resource pair. The model output is preserved unchanged.
- `bt_planner report`: 7 tasks, 4 milestones, 400 estimated minutes, 295-minute critical path, widest level 2; no missing command verification, low-confidence tasks, unordered conflicts, or unconsumed results.
- `PLAN.mmd` was checked against task IDs and dependency edges by inspection; it was not parsed or rendered.

Aye. Este fue el borrador nuevo de REQ-017. La corrida de Opus usó solo herramientas de lectura; no cambió la SPEC, la ronda, el plan anterior ni el checkout de `pictures`. Después, el chequeo externo confirmó que el contrato es publicable con una advertencia de recurso compartido. El propietario aprobó este artefacto para un experimento aislado M1/M2 y se congeló como revisión 1; eso no autoriza implementación por M3.

## Lo que encontré en el código

Revisé `AGENTS.md`/`CLAUDE.md`, la SPEC, `round-01.json`, el `PLAN.md` anterior, el contrato y el esquema del planificador, y el código relacionado.

**Hechos comprobados en el código:**
- **Eventos:** `eventoDeTexto`, `eventoDeMensajes` y `EVENTOS_CONOCIDOS` viven en `ideas-guiadas.ts`. Ese archivo importa `biblioteca.ts`, que carga `decoraciones.json` y código de entorno. Por eso el navegador no puede importarlo tal cual; hay que extraer el normalizador y el analizador de eventos a módulos sin dependencias.
- **Lista sin 3D:** ya existe un dueño único, `ESTRUCTURAS_SIN_VISTA_3D` en `src/lib/guiada-motor/sin-vista-3d.ts` (figura, centro_mesa, pared_organica, pared_no_densa). El plan anterior la repetía a mano.
- **Recorrido del servidor:** `route.ts` hace `alcanceDelTurno` → `esquemaHerramientaPropuesta` → `proponer_composicion` → `propuestaConLoPedido` → `normalizarPropuestaComposicion`, y audita con `decidir(...)`. `eventoTurno` usa `briefVigente().evento` sin normalizarlo.
- **Menú de piezas:** `PIEZAS_INDIVIDUALES` en `PreguntaPropuesta.tsx` es fijo. Su botón «Arco orgánico» envía **`arco`** a propósito, y una prueba exige que ningún botón dé `arco_asimetrico`. El nombre oficial de `arco_asimetrico` también es «Arco orgánico». La tabla de Opus ponía `arco_asimetrico` primero en cinco actividades, así que una tarjeta con su nombre oficial volvería a meter el defecto ya corregido.
- **Widgets guardados:** `WidgetGuiadoSchema` es `.strict()`. Un campo nuevo en el widget rompería las sesiones guardadas si se vuelve a una versión anterior. Esto confirma la corrección que ya se hizo en el plan anterior.
- **Comandos de prueba del plan anterior:**
  - `guiada:test` no incluye las pruebas nuevas que ese plan prometía cubrir con él.
  - `test-propiedades-herramientas` no toca `proponer_composicion`.
- **Iconos:** `IconoEstructura` cubre los 18 IDs, así que las tarjetas no necesitan iconos nuevos.
- **SPEC:** su cabecera dice `status: in-progress`, pero D-051 y el checkpoint la devolvieron a borrador y aclaración. No la toqué.

**Sin comprobar:** el dato de «31 ideas cubren 10 de 18 estructuras» viene de la delegación anterior. Tampoco sé si las pruebas actuales pasan.

---



[PLAN.md, PLAN.json y PLAN.mmd se guardan como archivos adyacentes.]


---

## Revisión adversaria

Es una revisión del propio planificador, no una auditoría independiente.

**Posibles errores del contrato** (sin comprobar, porque `bt_planner check` no se ejecutó):
- **Anclas de la SPEC:** no sé cómo convierte el validador los encabezados en anclas. Usé solo `#requirements`, `#constraints` y `#assumptions`.
- **Varios recursos en una línea:** `resources: a, b` asume que se separan por comas igual que `files:`.
- **`created_by` propio:** T1.2, T2.1 y T3.1 marcan como `created_by` su propia prueba. El README no aclara si se permite.
- **Precedentes:** `precedent:D-039`, `REQ-017/T1.1` y `REQ-017/T3.1` dependen de que el adaptador encuentre esos IDs.
- **Archivos:** cada evidencia `file:` apunta a un archivo que abrí o encontré con búsqueda. Los archivos nuevos no se citan como evidencia.

**Omisiones de alcance:**
- **«La que tú quieras»** (pieza individual sin estructura elegida): hoy el modelo elige cualquier estructura. La SPEC no lo cubre y el plan anterior no lo mencionaba. Queda como supuesto A7.
- **Auditoría:** R6 pide registrar solo los ajustes. Yo propongo una decisión por cada turno en que la política está activa, que incluye los ajustes. Se puede recortar.
- **Informe de cobertura de la biblioteca:** lo quité, porque la SPEC lo deja como información y no como entrega.

**Riesgos técnicos:**
- **Choque de nombres con «Arco orgánico»** (ver hallazgos), resuelto provisionalmente con el supuesto A6.
- **Precedencia en `route.ts`:** la política debe ir antes de `propuestaConLoPedido` y no aplicarse si hay plan vigente.
- **Medidas:** al reemplazar una pieza hay que descartar sus `medidas`.
- **Evento sin normalizar:** `brief.evento` puede llegar como texto libre del modelo. Hay que normalizarlo con la misma función en el cliente y en el servidor para que coincidan.
- **`aro_circular`:** solo su forma parcial no tiene 3D.
- **Sin prueba manual:** recorrer la interfaz exige llamadas al modelo, que son de pago.

**Supuestos de producto:** q1–q5 de la ronda 01 siguen sin respuesta. Además hay tres nuevos:
- **A6:** `arco_asimetrico` se cambia por `arco` en la tabla.
- **A7:** «La que tú quieras» mantiene el comportamiento actual.
- **A8:** se pueden recomendar `bouquet`, `arco_no_denso` y `columna_no_densa`, aunque su 3D es solo aproximado.

## Diferencias con el plan anterior
1. Reutiliza `ESTRUCTURAS_SIN_VISTA_3D` en vez de copiar la lista sin 3D.
2. Detecta el choque de «Arco orgánico» y cambia la tabla bajo el supuesto A6.
3. Fija el orden en el servidor: primero la política del evento, después `propuestaConLoPedido`. Protege las piezas que nombró el cliente y descarta las medidas de la pieza reemplazada.
4. Una sola función, `eventoCanonicoDelTurno`, resuelve la actividad en el cliente y en el servidor.
5. Cambia comandos de verificación que no comprobaban nada:
   - `test-propiedades-herramientas` no toca la propuesta.
   - `guiada:test` no ejecutaba las pruebas nuevas; ahora T4.1 las registra en ese script.
6. Las pruebas se escriben dentro de cada tarea y se añade el hito M4 de integración.
7. El módulo pasa a `src/lib/ia/guiado/`, para que `lib/plan` no dependa de `ia`.
8. Quita todo el estado de aprobación y el historial contradictorio, y añade `PLAN.json` 1.1.0 (revisión 1).

## Pendiente del propietario
- q1–q5 de la ronda 01 y los nuevos A6, A7 y A8.
- Si la auditoría debe registrar cada turno con la política activa o solo los ajustes.
- La cabecera de la SPEC (`status: in-progress`) contradice D-051. Es para que la revises; no la cambié.

El plan quedó aprobado y congelado tras el chequeo externo. Para ejecutarlo en M1 debe consumirse este artefacto aprobado; la advertencia T2.1/T3.1 requiere serialización de `event-structure-policy`.
