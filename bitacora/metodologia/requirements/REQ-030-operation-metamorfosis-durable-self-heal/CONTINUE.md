# Goal: terminar REQ-030 (Operación Metamorfosis) — lo pendiente tras la primera iteración

Eres el ingeniero principal de Metodología (repo `~/dev/metodologia`, rama `main`). Trabaja de forma autónoma hasta
cumplir todos los criterios de aceptación de abajo. No uses el Scheduler heredado, `handoff`, `launch` ni el flujo de
planificación de la metodología para construir esto: trabaja directo en esta sesión, con subagentes en worktrees
aislados si hay trabajo paralelo, y usa solo la bitácora para dejar rastro. Conversación en español; código, commits
y bitácora en inglés.

## Lee primero (en este orden)
1. `~/bitacora/metodologia/requirements/REQ-030-operation-metamorfosis-durable-self-heal/REQUEST.raw.md` — el
   requerimiento original completo (es la especificación; sus reglas innegociables siguen vigentes).
2. `.../REQ-030-*/REPORT.md` y `.../M0-ARCHAEOLOGY.md` — qué se hizo, evidencia, estado vivo, deuda.
3. `skill/scripts/bt_durable/README.md` — arquitectura (control / execution / adapters), instalación, migración,
   regla de `DBOS.patch` (nunca justo antes de `recv`/`sleep`/`get_result`/`set_event`), limitaciones.
4. Skill `dbos-python` en `.claude/skills/dbos-python/` (DBOS fijado a 3.3.0: `enable_patching=True` explícito).

## Estado vivo al empezar (verifícalo, no lo asumas)
- `bt-durable.service` (systemd de usuario) corre el engine sobre PostgreSQL `metodologia-dbos-pg`
  (127.0.0.1:5435; URL solo en `~/.config/bitacora/durable.env`, 0600). Rutas: `bitacora.py config get execution.routes`.
- pictures REQ-021 ya es del runtime durable (`RUN.owner.json` backend `dbos`, workflow `bt:pictures:REQ-021:r15`):
  28 tareas heredadas e integradas en `refs/bt/line/pictures/REQ-021/r15/pictures`; T2.6/T3.2/T3.11 reconciliando
  desde sus snapshots heredados; 14 por ejecutar. El runtime heredado de ese run está en hold y sus servicios
  `metodologia-run-pictures-REQ-021` / `metodologia-monitor-pictures-REQ-021` deshabilitados.
- Estado: `uv run bt-durable status pictures REQ-021`; telemetría: `~/bitacora/.state/durable/telemetry.jsonl`;
  métricas: `uv run python -m bt_durable.bench durable <telemetry> [<launches>]`.

## Primer paso obligatorio
Mientras los puntos 1–3 no estén terminados y desplegados, REQ-021 no debe lanzar agentes nuevos:
`uv run bt-durable pause pictures REQ-021` (las verificaciones en curso pueden terminar). Reanuda con `resume`
cuando 1–3 cumplan sus criterios y el engine esté reiniciado con el código nuevo (respetando la regla de patch para
workflows ya en curso: si cambias la secuencia de pasos de `bt.run`/`bt.task`/`bt.agent`, va detrás de
`DBOS.patch`, con una prueba al estilo de `tests/test_durable_versioning.py`).

## Pendiente, por prioridad (con criterios de aceptación ejecutables)

1. **Subplanes y composition gates (plan schema 1.3.0) en el runtime durable.** Hoy se ignoran: REQ-021 tiene 4
   subplanes (SP-1, SP-2, SP-3, SP-14) y todo integra en una sola línea. Reutiliza la lógica que ya existe
   (`bt_scheduler_core/subplans.py`, `bt_composition/`, `bt_scheduler_owner_composition.py`, líneas por subplan
   `refs/m3/line/<run>/<role>/<SP>`), sin reescribirla, a través de las puertas de adaptador (`bt_durable/legacy.py`).
   *Acepta cuando*: un e2e con un plan de 2 subplanes y un gate demuestra líneas por subplan, que una tarea tras el
   gate no arranca antes de que el gate pase, y que la migración de REQ-021 conserva la línea de cada subplan.
2. **Contexto del brief igual al heredado.** El adaptador `bt_durable/adapters/m3.py` usa el brief básico. Lleva al
   prompt lo mismo que `bt_scheduler_executor_wiring.wire` (`_with_owner_notes`: `RUN.notes/<task>.md`, historial,
   análisis; notas de diseño y aprobaciones `bt_design_approval`; `contract_notes`). *Acepta cuando*: una prueba
   compara, para la misma tarea de un plan fixture, el prompt que generan ambos runtimes y no falta ninguna sección;
   y el prompt de un intento real de REQ-021 contiene la nota de `RUN.notes/T2.6.md`.
3. **Checks manuales y atestaciones.** Conecta `attestations` del M6 (`bt_attestation`, coordinador/manual reviewer)
   en `M6Verifier`, igual que el owner heredado. *Acepta cuando*: un check `manual` con recibo válido pasa sin
   intervención y uno sin recibo produce una decisión con su request id (no un bloqueo opaco).
4. **Auditoría de hito → remediación coordinada** dentro de los workflows (`bt_audit_gate`, `bt_remediation`,
   límites `max_reworks`/rounds), agrupando hallazgos en una reparación con probes. *Acepta cuando*: el escenario K
   del requerimiento (auditoría con varios fallos relacionados) pasa en el laboratorio e2e.
5. **Router con el motor de decisión M2** (`bt_scheduler_decision`, ranking/batch, cuentas) en lugar de la lista
   fija, manteniendo `LiveQuota` como señal. *Acepta cuando*: una prueba con dos cuentas, una sin cuota, enruta a la
   otra sin gastar intento, y la decisión queda en telemetría.
6. **Panel remoto y web con runs durables.** Una proyección reconciliable (no una segunda fuente de verdad) desde
   los eventos `summary`/`state`/`decision` de DBOS hacia lo que leen `bt_remote_snapshot` y el dashboard; los
   comandos remotos (pause/resume/retry/answer) llegan como mensajes durables con request id. *Acepta cuando*:
   `test_remote_contracts` valida el snapshot con un run durable y un comando obsoleto se rechaza.
7. **Contratos de plan/subplan en Pydantic** como fuente canónica (manteniendo los validadores del planner como
   adaptador versionado mientras haga falta), con JSON Schema generado. *Acepta cuando*: los planes congelados
   reales de `~/bitacora/*/requirements/*/plan-revisions/` validan igual con ambos, y un test reproduce
   `req`/`req_id`, array/objeto y estado desconocido rechazados antes de gastar cuota.
8. **Guardia de archivos** para escrituras por shell donde sea fiable (hoy `file_guard.py` solo ve Edit/Write).
9. **Retirar infraestructura duplicada del runtime heredado** solo con equivalencia demostrada: proponer en
   `DECISIONS.md` qué se elimina (watchdog, hold files, outboxes, healing/ready-monitor) y qué se queda para runs
   que siguen en legacy; no borrar nada sin esa prueba.
10. **Benchmark comparable**: correr el mismo plan fixture (con fallos inyectados equivalentes) en ambos runtimes y
    reportar intervenciones, intentos redundantes, tiempo de recuperación y tokens; separar observación de hipótesis.

## Reglas que siguen vigentes
- El repo real es la fuente de verdad; verifica APIs instaladas antes de usarlas.
- Hooks, CLI de bitácora y runtime heredado corren con `/usr/bin/python3` (stdlib): `test_stdlib_boundary` debe
  seguir verde; solo `bt_contracts`, `bt_supervisor`, `bt_durable` usan dependencias (uv).
- Fronteras: solo `bt_scheduler_adapter` entra a `bt_scheduler_core`; solo `bt_scheduler_executor_adapter` al
  ejecutor; solo `bt_plan_adapter` al planner (tests `test_scheduler_integration`, `test_scheduler_executor_integration`,
  `test_plan_boundary`; este último tiene 5 infractores previos que no deben crecer).
- Pruebas reales (procesos, git, sandbox M6, DBOS) además de unitarias; un `skipped` no cuenta. Laboratorio:
  `tests/durable_support.py` (usa `BT_LAB_DIR` en el scratchpad, nunca barras sobre `/tmp`).
- Regresión completa antes de integrar: suite legacy con `python3`, suites nuevas con `.venv/bin/python`; solo
  pueden fallar los 5 archivos que ya fallaban en la línea base (ver `REQ-030-*/evidence/baseline-results.txt`).
- Producción: autorizado (D-078 y aprobación del 2026-10-28) a hacer push, deploy (advin, Vercel) y reiniciar
  servicios, siempre con paso de seguridad previo (backup / release anterior anotada) y smoke después. No borrar
  datos del usuario. No afirmar exactly-once.
- Cada hito: commit propio, pruebas específicas + regresión, entrada en
  `~/bitacora/metodologia/2026-10/W5/<día>.md` (o el día que toque) y actualización de `REQ-030-*/REPORT.md`.

## Hecho cuando
Los 10 puntos cumplen sus criterios (o el que no pueda cumplirse queda bloqueado con su motivo y el procedimiento
exacto para cerrarlo), REQ-021 corre en el runtime durable con subplanes, notas, atestaciones y auditorías, el panel
lo muestra, y `REPORT.md` refleja el estado exacto de ambos runtimes con evidencia reproducible.
