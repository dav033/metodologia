# OPERACIÓN METAMORFOSIS
## Transformación de Metodología en un sistema de ingeniería autónoma, durable, autorreparable y Linux-native

**Rol:** Principal Systems Architect + Staff Python Engineer + Distributed Systems Engineer + Reliability Engineer.

**Modo de ejecución:** Implementación autónoma integral, con investigación, desarrollo, pruebas, auditoría adversarial y migración verificable.

**Repositorio objetivo:** `dav033-metodologia`.

**Entorno principal:** Arch Linux, Python 3.12+, uv, Git, systemd, cgroups v2.

---

# 0. MISIÓN

Tu tarea es transformar la arquitectura existente de Metodología para reducir radicalmente el micromanagement que requiere su planificación, ejecución, verificación, recuperación y supervisión.

Actualmente Metodología dispone de un sistema propio de:

- Planificación y composición de subplanes.
- Scheduler persistente basado en SQLite.
- Selección inteligente de proveedores, modelos y cuentas.
- Agentes especializados con ejecución aislada.
- Git worktrees e integración.
- Verificación y auditorías independientes.
- Recuperación de intentos fallidos.
- Bitácora y telemetría.
- Control remoto mediante PWA, Gateway y Telegram.

El problema no es la ausencia de funcionalidades.

**El problema es que demasiadas responsabilidades de infraestructura están implementadas manualmente, con un alto coste de mantenimiento y numerosas oportunidades para producir errores que terminan requiriendo supervisión humana.**

Tu misión es reducir esa complejidad utilizando bibliotecas y mecanismos maduros, sin destruir la inteligencia específica de Metodología.

## Objetivo fundamental

Evolucionar desde:

`Plan → Scheduler → Agente → Error → Intervención humana → Corrección`

Hacia:

`Plan → Validación preventiva → Ejecución durable → Verificación → Diagnóstico → Autorreparación → Auditoría → Integración → Cierre`

La intervención humana debe reservarse para decisiones reales de producto, seguridad, autorizaciones, cambios de alcance o situaciones que no puedan recuperarse de manera segura.

**No quiero otro documento que describa cómo implementar esto. Quiero que inspecciones el código real, diseñes la migración y la EJECUTES.**

---

# 1. REGLAS INNEGOCIABLES

1. El repositorio real es la fuente de verdad. Nunca asumas que una ruta, función, módulo, comando o funcionalidad existe solo porque aparece en este prompt.

2. Antes de modificar código, inspecciona la arquitectura actual, las pruebas, los contratos, los planes existentes y las ejecuciones activas.

3. La restricción histórica de `stdlib-only` queda levantada para el núcleo de Metodología.

4. La portabilidad multiplataforma deja de ser prioritaria. **Linux es el entorno objetivo oficial.**

5. Prefiere tecnologías maduras y mantenidas frente a infraestructura casera que duplique sus funciones.

6. No reescribas componentes cuya responsabilidad siga siendo valiosa. Sustituye infraestructura genérica, no lógica de negocio.

7. No introduzcas dos sistemas que compitan por la propiedad del mismo estado de ejecución.

8. No utilices mocks como sustitutos de las pruebas reales de integración. Los mocks son apropiados para pruebas unitarias, pero debe existir evidencia adicional con procesos, archivos, bases de datos y servicios reales aislados.

9. No sacrifiques seguridad por autonomía. Ningún mecanismo de recuperación puede saltarse permisos, políticas de secretos, validaciones o decisiones del propietario.

10. No hagas push, despliegues productivos, migraciones destructivas ni modificaciones irreversibles sin autorización explícita. Los cambios locales reversibles y las pruebas aisladas quedan autorizados.

11. Conserva la bitácora, el historial de decisiones, los identificadores de requerimientos, las evidencias y los progresos válidos.

12. Usa worktrees para tareas de implementación independientes, verificando sus contratos antes de integrarlas.

13. No des por completada una etapa basándote exclusivamente en la declaración de un agente.

14. Todo cambio importante debe tener criterios de aceptación ejecutables y evidencia reproducible.

15. No me interrumpas por decisiones técnicas de bajo riesgo que puedas resolver investigando. Documenta la elección y sus fundamentos.

16. Si una operación requiere credenciales, autorización o infraestructura que no está disponible, completa el resto del trabajo, deja el bloqueo identificado y ofrece un procedimiento preciso de validación final. Nunca simules éxito.

17. No confundas cantidad de código, complejidad arquitectónica o cobertura declarada con fiabilidad real.

---

# 2. INVESTIGACIÓN OBLIGATORIA

Antes de implementar, inspecciona las dependencias instaladas y consulta la documentación oficial vigente.

## Tecnologías principales

**Ejecución durable**
- DBOS Python SDK.
- DBOS Workflows, Steps, Queues y Recovery.
- PostgreSQL para persistencia estable.
- SQLite solo cuando resulte apropiado para pruebas aisladas.

**Validación de contratos**
- Pydantic v2.
- JSON Schema.
- Generación o sincronización de tipos TypeScript cuando exista un consumidor frontend.

**Runtime Linux**
- psutil.
- systemd transient services/scopes.
- cgroups v2.
- subprocess/asyncio cuando correspondan.
- portalocker solo donde se necesiten locks explícitos.

**Observabilidad y calidad**
- structlog.
- Hypothesis.
- Ruff.
- pytest o el framework de pruebas existente.
- watchfiles, si aporta una mejora verificable.

**Opcionales condicionados por evidencia**
- AnyIO.
- httpx.
- Tenacity.
- OpenTelemetry.
- Otras bibliotecas consolidadas que descubras.

No introduzcas todas automáticamente.

Si DBOS ya proporciona una capacidad suficientemente buena, evita duplicarla con otra biblioteca.

## Documentación oficial de DBOS

Consulta:

- https://docs.dbos.dev/python/programming-guide
- https://docs.dbos.dev/python/integrating-dbos
- https://docs.dbos.dev/python/tutorials/workflow-tutorial
- https://docs.dbos.dev/python/tutorials/step-tutorial
- https://docs.dbos.dev/python/tutorials/queue-tutorial
- https://docs.dbos.dev/python/tutorials/workflow-management
- https://docs.dbos.dev/python/tutorials/upgrading-workflows
- https://docs.dbos.dev/python/prompting

DBOS proporciona skills oficiales:

`npx skills add dbos-inc/agent-skills`

Investiga su contenido, procedencia, versión y compatibilidad. Instala las skills pertinentes en el ámbito correcto del repositorio si su contenido es confiable y aportan valor. No ejecutes instrucciones remotas sin revisarlas.

**Verifica la API exacta de la versión instalada antes de implementar. No inventes métodos ni utilices ejemplos de versiones incompatibles.**

---

# 3. FASE M0 — ARQUEOLOGÍA ARQUITECTÓNICA

Antes de tocar el Scheduler, construye un mapa de responsabilidades.

Inspecciona especialmente, si existen:

- `skill/scripts/bitacora.py`
- `skill/scripts/bt_scheduler_core/`
- `skill/scripts/bt_scheduler_executor/`
- `skill/scripts/bt_scheduler_quality/`
- `skill/scripts/bt_scheduler_monitor/`
- `skill/scripts/bt_scheduler_recovery/`
- `skill/scripts/bt_scheduler_decision/`
- `skill/scripts/bt_scheduler_healing.py`
- `skill/scripts/bt_recovery_compiler.py`
- `skill/scripts/bt_recovery_cycle.py`
- `skill/scripts/bt_planner/`
- `skill/scripts/bt_composition/`
- `skill/scripts/bt_verifier_env.py`
- `skill/scripts/bt_remote_commands.py`
- `skill/scripts/file_guard.py`
- `remote/`
- `evals/`
- `install.py`
- `pyproject.toml`
- `uv.lock`

Investiga dónde se encuentran realmente:

1. La máquina de estados.
2. La persistencia de ejecuciones.
3. La frontera de despacho.
4. Los intentos y reintentos.
5. Los propietarios de locks.
6. Los contratos entre productor y consumidor.
7. El aislamiento de procesos.
8. El control de cuotas.
9. Los controles de seguridad.
10. El ciclo de auditoría y remediación.
11. La migración y rebase de planes.
12. La recuperación después de un cierre inesperado.

Construye una matriz que clasifique cada subsistema:

- **CONSERVAR:** lógica específica de Metodología.
- **ADAPTAR:** lógica que debe utilizar una biblioteca nueva.
- **REEMPLAZAR:** infraestructura genérica cuya responsabilidad se delegará.
- **ELIMINAR:** código redundante, pero solo después de comprobar equivalencia funcional.

Identifica los flujos críticos de extremo a extremo y sus invariantes.

Ejecuta la suite base e identifica los fallos preexistentes. Registra los resultados antes de comenzar.

## Entregable M0

Documentación de arquitectura actual y objetivo, mapa de responsabilidades, riesgos, pruebas base y estrategia de integración.

No te detengas esperando mi aprobación del documento. Continúa implementando los cambios reversibles que satisfagan las reglas de esta misión.

---

# 4. FASE M1 — CONTRATOS ESTRICTOS CON PYDANTIC

Incorpora Pydantic v2 para establecer contratos verificables entre los componentes del sistema.

## Contratos objetivo

Según los tipos que realmente maneje el repositorio:

- Plan y subplan.
- Dependencias entre tareas.
- Resultado del Planner.
- Intento de ejecución.
- Estado del Scheduler.
- Identidad y propietario de ejecución.
- Evento del Scheduler.
- Resultado de verificación.
- Hallazgo de auditoría.
- Decisión de recuperación.
- Selección de modelo/cuenta.
- Comandos y snapshots remotos.

## Requisitos

### Fuente de verdad

Evita múltiples representaciones manuales incompatibles del mismo contrato.

Genera JSON Schema a partir de modelos tipados cuando sea apropiado.

Cuando existan consumidores TypeScript, deriva sus tipos del contrato canónico o verifica que coincidan automáticamente.

No dependas de fixtures escritos a mano que puedan evolucionar independientemente del productor.

### Validación preventiva

Los contratos deben validarse:

- Antes de congelar un plan.
- Antes del despacho.
- Antes de aceptar resultados de agentes.
- Antes de cambios de estado.
- Antes de transmitir comandos remotos.
- Durante migraciones.

### Compatibilidad

Conserva compatibilidad explícita con esquemas anteriores cuando sea necesario.

No alteres silenciosamente el significado de los campos heredados.

Utiliza adaptadores versionados y pruebas de compatibilidad.

### Pruebas

Reproduce fallos equivalentes a:

- `req` versus `req_id`.
- Arrays versus objetos.
- Campos obligatorios omitidos.
- Estados desconocidos.
- Identificadores inconsistentes.
- Contratos productor/consumidor incompatibles.

Un error estructural debe detectarse ANTES de consumir cuota de IA.

---

# 5. FASE M2 — DBOS COMO MOTOR DE EJECUCIÓN DURABLE

Esta es la parte central de la transformación.

## Objetivo

Delegar en DBOS las responsabilidades de ejecución durable que hoy están implementadas manualmente, preservando los componentes específicos de Metodología.

### Mantener dentro de Metodología

- Planner.
- Decision Engine.
- Router de proveedores y cuotas.
- Políticas de selección de modelos.
- Grafo de dependencias de negocio.
- Roles de agentes.
- Reglas de auditoría.
- Gestión de conocimiento.
- Políticas de recuperación.
- Git worktrees.
- Integración y cierre.
- Interfaz de control remoto.

### Evaluar para delegación a DBOS

- Persistencia de workflows.
- Checkpoints de pasos.
- Recuperación tras reinicios.
- Colas durables.
- Esperas durables.
- Control de concurrencia del despacho.
- Reintentos de pasos transitorios.
- Cancelación y reanudación de workflows.
- Identidad durable de ejecución.

No mantengas un segundo motor de reintentos, colas o checkpoints para los nuevos workflows cuando DBOS pueda asumir esa función correctamente.

## Arquitectura requerida

Implementa una frontera explícita entre:

1. **Metodología Control Plane:** decide qué debe hacerse.
2. **DBOS Execution Plane:** coordina la ejecución durable.
3. **Linux Process Runtime:** ejecuta y controla procesos externos.
4. **Evidence and Telemetry Plane:** registra resultados y produce vistas operativas.

El Control Plane no debe depender internamente de los detalles de DBOS.

Define interfaces/adaptadores que permitan probarlo aisladamente.

### Propiedad del estado

Para cada ejecución, debe existir un propietario inequívoco:

- Runtime heredado: responsable de sus ejecuciones antiguas.
- Runtime DBOS: responsable de los nuevos workflows.

Si se conserva un estado de presentación en `SCHEDULER.db`, debe ser una proyección reconciliable, no una segunda fuente de verdad contradictoria.

## Workflows

Implementa los flujos durables apropiados para:

- Despacho de requerimientos.
- Ejecución de hitos.
- Verificación.
- Auditoría.
- Remediación.
- Integración.
- Cierre.

No conviertas indiscriminadamente cada función existente en un workflow.

Define límites de steps que representen unidades recuperables y con efectos externos controlados.

## Determinismo

Respeta las restricciones de DBOS:

- No realizar efectos externos directamente en el cuerpo determinista del workflow.
- Aislar tiempo, aleatoriedad, consultas externas y acciones de archivos en pasos apropiados.
- No cambiar de forma incompatible la secuencia de steps de workflows activos.
- Versionar cambios que alteren su comportamiento de recuperación.

Utiliza las estrategias oficiales de versionado y patching cuando corresponda.

## Idempotencia real

Atención especial:

**DBOS no garantiza por sí solo que ejecutar Claude, Codex o un comando shell produzca un único efecto externo.**

Diseña un protocolo de identidad, reclamación y reconciliación de intentos.

Cada operación debe poder identificar:

- Requerimiento.
- Plan.
- Tarea.
- Intento.
- Workflow DBOS.
- Identidad del proceso Linux.
- Worktree propietario.
- Versión del plan.
- Revisión de estado.

Antes de repetir una operación interrumpida:

1. Determina si existe un intento anterior.
2. Comprueba si el proceso externo continúa vivo.
3. Reconcilia los artefactos que produjo.
4. Comprueba si sus resultados fueron verificados.
5. Reutiliza resultados válidos.
6. Relanza únicamente cuando sea seguro.

Diseña el registro de intención y el commit de resultados para resistir interrupciones en cualquier punto.

No afirmes semántica exactly-once para efectos externos donde no pueda demostrarse.

## Recuperación

Demuestra recuperación después de:

- `SIGTERM`.
- `SIGKILL`.
- Reinicio del proceso del Scheduler.
- Reinicio del servidor DBOS.
- Interrupción de la base de datos.
- Fallo de un step.
- Pérdida del proceso del agente.
- Cancelación durante un reintento.
- Reinicio entre verificación y auditoría.

La recuperación debe retomar únicamente el trabajo que sigue siendo necesario.

---

# 6. FASE M3 — LINUX PROCESS SUPERVISOR

Construye un supervisor de agentes orientado específicamente a Linux.

Utiliza psutil y evalúa la integración con systemd y cgroups v2.

## Capacidades requeridas

- Lanzamiento aislado de procesos.
- Control de grupos de procesos.
- Identidad persistente de intentos.
- Terminación de árboles de procesos.
- Límites configurables de recursos.
- Timeouts.
- Señales de cancelación.
- Captura de stdout/stderr.
- Heartbeats cuando sean justificables.
- Recuperación y reconciliación tras reinicios.
- Limpieza de procesos huérfanos.

### systemd

Evalúa `systemd-run --user`, transient scopes y servicios de usuario, de acuerdo con el entorno y permisos reales.

No dependas de `sudo` para operaciones ordinarias.

Utiliza controles de cgroups que estén realmente disponibles.

Si un entorno de pruebas no dispone de systemd, proporciona un backend alternativo para ejecución aislada y testing, sin comprometer el backend Linux principal.

### Invariante obligatorio

Cancelar un intento debe impedir que sus procesos continúen modificando el repositorio.

Cuando la terminación no pueda garantizarse inmediatamente, el Scheduler debe tratar el recurso como ocupado hasta reconciliarlo.

---

# 7. FASE M4 — COLAS, PARALELISMO Y AISLAMIENTO

Integra DBOS Queues con las restricciones reales del sistema.

## Requisitos

- Concurrencia configurable.
- Priorización de tareas.
- Colas por clase de carga cuando convenga.
- Control de recursos compartidos.
- Respeto a dependencias.
- Evitar saturación de RAM y CPU.
- Aislamiento de artefactos de compilación.
- Protección de integración Git.

### Worktrees

Cada tarea que pueda producir conflictos debe ejecutarse en un espacio aislado.

Preserva el sistema de worktrees existente y mejora sus invariantes.

No permitas que dos tareas escriban simultáneamente en un mismo worktree si no existe un mecanismo seguro de coordinación.

### Build locks

Evita colisiones de:

- `next build`.
- `.next`.
- `npm run build`.
- Tests E2E.
- Generadores de código.
- Archivos de salida compartidos.

Prefiere aislamiento real a serializar todo indiscriminadamente.

### Cuotas

Conserva la lógica del Decision Engine.

Integra señales de capacidad y disponibilidad con el despacho.

No inventes cuotas ni prometas que una suscripción proporciona acceso API no autorizado.

Si un modelo no tiene capacidad disponible, aplica una política verificable de espera durable, redistribución o escalamiento permitido.

No bloquees un worker innecesariamente durante períodos de espera.

---

# 8. FASE M5 — AUTORREPARACIÓN DEL SCHEDULER

Quiero que Metodología resuelva por sí misma la mayoría de los errores operativos previsibles.

## Clasificador de fallos

Distingue:

1. Error transitorio de infraestructura.
2. Error de entorno.
3. Error de contrato.
4. Error de verificación.
5. Error real de implementación.
6. Error de integración.
7. Fallo de cuota o disponibilidad.
8. Error de permisos.
9. Decisión de producto necesaria.
10. Error interno del Scheduler.

Implementa clasificadores verificables con evidencia, no heurísticas opacas que escalen indiscriminadamente.

### Recuperación específica

**Errores transitorios:** retry con backoff y límites.

**Errores de entorno:** intentar reparación acotada sin escalar innecesariamente el modelo.

**Errores de contrato:** reparar productor/consumidor a partir del contrato canónico y volver a verificar.

**Errores de código:** crear una tarea de reparación con pruebas reproducibles.

**Errores de integración:** diagnosticar el conflicto y reconciliar con aislamiento.

**Falta de cuota:** utilizar ruta permitida con capacidad, o espera durable.

**Decisiones humanas:** escalar con información concreta y opciones.

## Auditoría → Reparación automática

Si una auditoría termina con hallazgos verificables que pueden corregirse dentro del alcance autorizado:

1. Agrupa hallazgos relacionados.
2. Genera una tarea de remediación.
3. Adjunta los probes que reproducen los fallos.
4. Ejecuta las correcciones.
5. Verifica los cambios.
6. Repite la auditoría afectada.
7. Cierra únicamente si existe evidencia suficiente.

No abras decenas de intentos independientes cuando una reparación coordinada resulte más segura.

## Antibucles

Implementa límites para:

- Cantidad de intentos.
- Tiempo acumulado.
- Cuota consumida.
- Regresiones consecutivas.
- Repetición del mismo error.
- Escalamientos de modelo.

Distingue progreso real de repetición improductiva.

No permitas autorreparación infinita.

---

# 9. FASE M6 — PRE-VUELO DE PLANES

Endurece el Planner y la congelación de planes.

Antes de entregar un plan al Scheduler verifica:

- Existencia o producción prevista de archivos.
- Comandos de test válidos.
- Entorno de ejecución.
- Dependencias necesarias.
- Contratos compartidos.
- Relaciones productor/consumidor.
- Recursos exclusivos.
- Worktrees.
- Condiciones de integración.
- Criterios de aceptación.
- Reglas de seguridad.
- Compatibilidad entre subplanes.

Si un test todavía no existe porque será creado por una tarea, esto debe estar declarado explícitamente.

No rechaces planes legítimos simplemente porque sus entregables todavía no existen.

## Guardia de archivos

Examina la política de límite de 500 líneas y el actual `file_guard.py`.

Implementa validación preventiva para rutas de escritura relevantes, incluidos mecanismos shell, cuando pueda hacerse de forma fiable.

Evita reglas excesivamente amplias que bloqueen operaciones legítimas.

Las verificaciones deben detectar regresiones antes del cierre de la tarea.

---

# 10. FASE M7 — CONTROL REMOTO Y OBSERVABILIDAD

Conserva la arquitectura PWA + Gateway + Telegram.

Revisa los hallazgos históricos:

- F4: endpoint SSE inconsistente.
- F10/F11: notificaciones y lectura de identificadores.
- F21: reapertura sin identificador de tarea.
- F33: persistencia prematura de route pins.
- F41: formatos incompatibles de cuotas.

Verifica primero cuáles siguen presentes.

Corrige únicamente los problemas confirmados.

## Telemetría estructurada

Implementa o mejora los logs estructurados para relacionar:

`project_id → req_id → plan_version → task_id → attempt_id → workflow_id → process_id`

Registra:

- Inicio y cierre.
- Proveedor/modelo.
- Duración.
- Resultado.
- Reintentos.
- Motivo de recuperación.
- Consumo conocido.
- Errores clasificados.
- Intervenciones humanas.
- Resultado de verificación.

No registres secretos, tokens de autenticación ni contenidos sensibles innecesarios.

## Panel remoto

Debe mostrar estados derivados de datos reales:

- Ejecutando.
- En cola.
- Esperando cuota.
- Recuperando.
- Requiere decisión.
- Falló.
- Completado y verificado.

Los botones de pausa, cancelación, reanudación y retry deben respetar transiciones válidas e idempotencia.

Un comando remoto obsoleto no puede alterar una ejecución más reciente.

---

# 11. FASE M8 — MIGRACIÓN DE PLANES Y EJECUCIONES

La migración es obligatoria.

No basta con hacer que los nuevos planes funcionen.

## Inspección

Busca mecanismos existentes como:

- `bt_planner/schema_13.py`
- `bt_scheduler_plan_compat.py`
- `bt_scheduler_core/rebase.py`
- `bt_scheduler_monitor/store_migrations.py`
- `bt_scheduler_owner_reconciliation.py`
- `bt_recovery_lineage.py`

Confirma las rutas reales.

## Compatibilidad

Implementa soporte explícito para:

1. Planes nuevos.
2. Planes heredados finalizados.
3. Planes heredados pausados.
4. Planes heredados fallidos.
5. Ejecuciones heredadas activas.

## Protocolo

Antes de migrar:

- Snapshot consistente de base de datos y artefactos.
- Inventario de tareas e intentos.
- Validación de evidencias.
- Identificación de trabajos activos.
- Detección de versiones.
- Plan de rollback.

Nunca migres una ejecución activa bajo dos propietarios simultáneos.

### Preservar progreso

Una tarea completada solo puede heredarse como completada si su evidencia y contratos siguen siendo válidos.

Una tarea sin evidencia suficiente debe pasar por reconciliación.

Una tarea bloqueada debe conservar su diagnóstico y quedar preparada para recuperación cuando corresponda.

### Migración a DBOS

No insertes manualmente filas en tablas internas de DBOS ni fabriques checkpoints para simular tareas completadas.

Construye un bridge que traduzca el progreso heredado a entradas y resultados verificables consumidos por workflows nuevos.

Conserva historial y procedencia.

## Requisitos de idempotencia

Ejecutar la migración dos veces no debe:

- Duplicar tareas.
- Duplicar procesos.
- Repetir efectos externos.
- Perder evidencias.
- Corromper identificadores.
- Modificar estados correctamente migrados.

Incluye dry-run, informes de diferencias y rollback.

---

# 12. FASE M9 — PRUEBAS ADVERSARIALES Y CAOS

No quiero pruebas que únicamente confirmen el camino feliz.

Construye un laboratorio reproducible con repositorios fixture, procesos reales y base de datos aislada.

Usa Hypothesis para explorar transiciones de estado y secuencias problemáticas.

## Escenarios obligatorios

**A. Interrupción antes de iniciar una tarea**

No debe producir ejecuciones duplicadas.

**B. Interrupción durante la ejecución de un agente**

Debe reconciliar el proceso y sus artefactos antes de relanzarlo.

**C. Interrupción después del trabajo externo pero antes del checkpoint**

Debe detectar el resultado existente o evitar reutilizarlo sin verificación.

**D. Interrupción después de registrar un step**

No debe repetir ese step completado.

**E. Dos comandos de retry simultáneos**

Debe existir un único resultado autorizado.

**F. Cancelación mientras un agente escribe archivos**

No deben quedar escritores activos sin controlar.

**G. Dos builds sobre el mismo recurso**

Deben aislarse o coordinarse.

**H. Caída del backend persistente**

No debe perder el estado durable ya confirmado.

**I. Cambio de versión de workflow durante recuperación**

Debe respetar versionado y compatibilidad.

**J. Migración repetida de un plan heredado**

No debe alterar resultados válidos.

**K. Auditoría con varios fallos relacionados**

Debe compilar una reparación acotada y verificarla.

**L. Cuota agotada**

Debe cambiar a una ruta permitida o esperar sin consumir recursos innecesarios.

**M. Worktree con cambios inesperados**

No debe sobrescribirlos ni eliminarlos automáticamente.

**N. Error de seguridad o autorización**

No debe ser corregido saltándose controles.

**O. Error de infraestructura frente a error de código**

Debe generar respuestas de recuperación diferentes.

## Pruebas de concurrencia

Introduce carreras reproducibles, interrupciones y operaciones concurrentes.

Comprueba invariantes con consultas al estado persistido, identificación de procesos y revisión del árbol Git.

## Evidencia

Guarda:

- Comandos utilizados.
- Resultado esperado.
- Resultado real.
- Estado persistido final.
- Identidad de los procesos.
- Prueba de no duplicación.
- Logs relevantes.
- Limitaciones de la prueba.

Una prueba marcada como `skipped` no cuenta como validación exitosa del requisito.

---

# 13. FASE M10 — BENCHMARKS

Evalúa el sistema antes y después del cambio.

Métricas:

1. Intervenciones humanas por plan.
2. Recuperaciones automáticas exitosas.
3. Intentos redundantes.
4. Tiempo hasta recuperación.
5. Coste de orquestación.
6. Tiempo de despacho.
7. Fallos de integración.
8. Fugas de procesos.
9. Tiempo bloqueado por verificaciones.
10. Porcentaje de tareas completadas con evidencia suficiente.

No inventes resultados.

Usa cargas comparables y separa mejoras observadas de hipótesis.

El objetivo no es añadir DBOS: es demostrar que Metodología necesita menos intervención para conseguir resultados correctos.

---

# 14. ESTRATEGIA DE IMPLEMENTACIÓN

Divide el trabajo en hitos ejecutables e independientes cuando sea posible.

Orden recomendado:

1. M0 — Auditoría y línea base.
2. M1 — Contratos tipados.
3. M2 — DBOS sobre un flujo real aislado.
4. M3 — Supervisor Linux.
5. M4 — Concurrencia y recursos.
6. M5 — Recuperación automática.
7. M6 — Validación preventiva.
8. M7 — Observabilidad y control remoto.
9. M8 — Migración.
10. M9 — Pruebas adversariales.
11. M10 — Benchmarks y cierre.

Sin embargo, optimiza el grafo de dependencias según el repositorio real.

### Trabajo paralelo

Utiliza agentes especializados cuando aporte una mejora tangible:

- Explorer: mapa del código y contratos existentes.
- Researcher: bibliotecas y documentación.
- Planner: descomposición y criterios.
- Graph Engineer: dependencias y aislamiento.
- Implementer/Runner: implementación.
- Reviewer: pruebas y revisión.
- Antagonist: búsqueda adversarial de fallos.
- Designer: obligatorio si modificas interfaces o flujos UX.

No lances múltiples agentes que puedan modificar el mismo recurso sin aislamiento.

### Integración incremental

Después de cada hito:

1. Ejecuta pruebas específicas.
2. Ejecuta pruebas de regresión.
3. Audita los contratos afectados.
4. Integra de forma controlada.
5. Actualiza la bitácora.
6. Conserva evidencia.

No acumules todos los cambios hasta una integración gigante al final.

---

# 15. FEATURE FLAGS Y ROLLBACK

Durante la transición, el sistema debe poder seleccionar explícitamente un backend de ejecución.

Conceptualmente:

`execution_backend = legacy | dbos`

Adapta el mecanismo de configuración real del repositorio.

Requisitos:

- El backend heredado debe conservar su comportamiento.
- Las ejecuciones existentes no deben cambiar de propietario implícitamente.
- El backend DBOS debe poder utilizarse para nuevos planes.
- La transición debe ser observable y reversible dentro de límites documentados.
- No mantengas indefinidamente dos implementaciones completas si DBOS demuestra reemplazar una de ellas.

No elimines el backend anterior hasta demostrar equivalencia funcional y contar con una ruta segura para los planes que todavía lo necesitan.

---

# 16. CRITERIOS DE ACEPTACIÓN

No declares el proyecto terminado hasta cumplir los siguientes puntos:

- [ ] DBOS integrado y usado por al menos un flujo completo realista de Metodología.
- [ ] Contratos principales validados con Pydantic.
- [ ] Procesos de agentes supervisados mediante un runtime Linux.
- [ ] Recuperación comprobada con interrupciones reales.
- [ ] Reconciliación demostrada para efectos externos.
- [ ] Concurrencia y worktrees protegidos.
- [ ] Reintentos y autorreparación integrados con límites.
- [ ] Verificación preventiva de planes.
- [ ] Control remoto compatible con el nuevo runtime.
- [ ] Migración de planes heredados probada.
- [ ] Versionado seguro de workflows.
- [ ] Tests adversariales ejecutados.
- [ ] Regresiones existentes controladas.
- [ ] Dependencias registradas y fijadas en el lockfile.
- [ ] Procedimiento de instalación Linux documentado.
- [ ] Procedimiento de recuperación y rollback documentado.
- [ ] Métricas comparativas obtenidas o limitaciones expresamente reportadas.
- [ ] Sin regresiones críticas nuevas.
- [ ] Sin afirmar completitud sobre componentes no validados.

Un criterio solo se marca cuando existe evidencia verificable.

---

# 17. ENTREGABLES FINALES

Debes dejar:

**Código funcional**
- Integración DBOS.
- Contratos.
- Supervisor Linux.
- Recuperación.
- Adaptadores.
- Migraciones.
- Pruebas.

**Infraestructura**
- Dependencias reproducibles con uv.
- Configuración de DBOS.
- Configuración de PostgreSQL cuando corresponda.
- Configuración de servicios Linux si se necesita.
- Scripts de diagnóstico.
- Procedimientos de backup y restore.

**Documentación**
- Arquitectura anterior y nueva.
- Responsabilidades delegadas.
- Responsabilidades conservadas.
- Guía de uso.
- Guía de migración.
- Guía de troubleshooting.
- Limitaciones verificadas.
- Deuda técnica restante.

**Reporte**
- Hitos completados.
- Cambios concretos.
- Evidencia de pruebas.
- Benchmark.
- Riesgos pendientes.
- Operaciones que requieren autorización.
- Estado exacto del runtime nuevo y del heredado.

---

# 18. POLÍTICA DE AUTONOMÍA

Tienes autoridad para:

- Investigar.
- Instalar dependencias de desarrollo verificadas.
- Refactorizar.
- Crear módulos.
- Reorganizar responsabilidades.
- Generar pruebas.
- Ejecutar pruebas en entornos aislados.
- Crear worktrees y ramas locales.
- Corregir regresiones introducidas.
- Modificar documentación.
- Proponer y ejecutar mejoras reversibles justificadas.

No necesitas pedirme aprobación para cada decisión técnica ordinaria.

Pero no tienes autoridad para:

- Eliminar datos reales.
- Alterar ejecuciones activas sin protocolo seguro.
- Exponer secretos.
- Modificar credenciales.
- Hacer push sin autorización.
- Desplegar cambios productivos sin autorización.
- Desactivar controles de seguridad.
- Consumir recursos externos de pago ilimitadamente.
- Declarar pruebas exitosas sin haberlas ejecutado.

Si encuentras un bloqueo real, aísla ese trabajo y continúa con las tareas independientes.

---

# 19. DIRECTIVA FINAL

Este trabajo NO consiste en añadir decoradores `@DBOS.workflow()` alrededor de funciones existentes.

Consiste en una evolución arquitectónica del motor de ejecución de Metodología.

Quiero menos infraestructura casera, menos duplicación, menos fallos estructurales y mucha más capacidad de ejecución autónoma verificable.

En cada decisión pregúntate:

**¿Estamos construyendo una capacidad diferencial de Metodología o estamos manteniendo manualmente infraestructura que una biblioteca madura ya resuelve?**

Si es lo segundo, evalúa sustituirla.

No te conformes con que las pruebas pasen: intenta demostrar que el sistema falla de manera segura, se recupera y no desperdicia ejecuciones.

No me entregues solamente una propuesta, una lista de tareas o un prototipo aislado.

**INVESTIGA → PLANIFICA → IMPLEMENTA → INTEGRA → ROMPE EN PRUEBAS → RECUPERA → AUDITA → DOCUMENTA → ENTREGA.**

Empieza inspeccionando el repositorio y estableciendo la línea base. Después ejecuta el plan completo hasta donde permitan las herramientas y autorizaciones reales.

**Resultado deseado: Metodología debe convertirse en un sistema que coordine agentes, detecte sus propios errores y recupere automáticamente sus ejecuciones, sin que su propietario tenga que actuar continuamente como supervisor operativo.**
