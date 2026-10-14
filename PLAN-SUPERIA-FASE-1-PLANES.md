---
id: PLAN-PLANNER-001
title: "Evolución del Planificador — clasificación y contrato estructurado"
status: phase-1-closed
created: 2026-10-14
closed: 2026-10-14
track: architecture
scope: planner-only
schema_version: "1.0.0"
---

# Plan — Evolución del Planificador de la metodología

> **Propósito:** ampliar el Planificador existente para entregar planes **clasificados, verificables y consumibles por un Scheduler determinista**, sin convertir al Planificador en un supervisor de agentes.
>
> **Decisión arquitectónica acordada:** el Planificador inspecciona el proyecto, genera el plan, lo valida, lo entrega y **termina**. No permanece activo durante la ejecución. El Scheduler y sus módulos son otro sistema.
>
> **Estado:** Fase 1 **cerrada el 2026-10-14** (REQ-009 contrato, REQ-010 módulo aislado, REQ-012 cierre). La sección §16 resume qué se implementó y con qué evidencia; el resto del documento conserva el diseño original.

## 1. Contexto y punto de partida

La metodología actual ya maneja requisitos mediante `SPEC.md`, `PLAN.md` y, cuando aplica, `HANDOFF.md`. También utiliza hitos, tareas identificadas, dependencias (`after`), verificaciones por tarea, revisiones independientes y registros de ejecución como `RUN.json`.

En los ejemplos existentes:

- **REQ-013** define fases, tamaños/estimaciones por fase, dependencias y posibilidades de trabajo paralelo.
- **REQ-014** documenta un supervisor (`bitacora.py run`) y reglas de escalamiento entre modelos.
- **REQ-015** ofrece tareas con dependencias, comandos de verificación y registro de avances.
- **REQ-016** contiene `PLAN.md`, `HANDOFF.md`, auditorías y `RUN.json`; este último contempla atributos como `complexity` y `risk`, que aparecen sin clasificación en el ejemplo examinado.

**Problema a resolver:** la intención del plan es comprensible para una persona o un agente, pero su metadata operativa no es uniforme ni suficientemente explícita para que otro programa elija modelos, evalúe paralelismo y administre tareas sin reinterpretar Markdown libre.

## 2. Objetivo

Que **cada tarea ejecutable** del plan posea una descripción precisa y una clasificación consistente que el Scheduler pueda utilizar como entrada, junto con un **`PLAN.json` versionado y validado**.

El Planificador seguirá entregando documentación humana (`SPEC.md` y `PLAN.md`) y, cuando la metodología lo requiera, `HANDOFF.md`. Su salida adicional será una representación estructurada del **plan de trabajo**, separada del **estado de ejecución**.

### Resultado esperado

Un requisito aprobado debe poder pasar por este flujo:

```text
Objetivo del usuario
       │
       ▼
Planificador (ejecución temporal)
  ├─ inspecciona proyecto y restricciones
  ├─ produce/actualiza SPEC.md
  ├─ diseña hitos, tareas y dependencias
  ├─ clasifica cada tarea
  ├─ define verificaciones y aceptación
  ├─ emite PLAN.md + PLAN.json (+ HANDOFF.md)
  └─ valida consistencia y finaliza
       │
       ▼
Scheduler (fuera del alcance de este plan)
  └─ consume PLAN.json y gestiona RUN.json
```

## 3. Alcance

### Incluido

1. Estandarizar las **cinco dimensiones obligatorias** de clasificación de tarea.
2. Añadir una **estimación de duración** expresada numéricamente, con nivel de confianza.
3. Hacer explícitos **dependencias, superficies afectadas y recursos potencialmente compartidos**.
4. Definir `PLAN.json` como contrato estructurado entre Planificador y Scheduler.
5. Añadir validación automática de esquema y consistencia del grafo de tareas (DAG).
6. Mantener la compatibilidad con el formato humano y los procesos de la metodología.
7. Documentar cómo interpretar estimaciones inciertas, tareas de alcance excesivo y condiciones sin verificación automatizable.
8. Probar la generación del contrato con planes reales representativos (sin modificar trabajos aprobados).

### Excluido / no objetivos

- No implementar ni rediseñar el Scheduler, Monitor, Recovery Manager o los ejecutores.
- No elegir Claude, Codex, Gemini, Haiku, Sonnet, Opus ni cuentas particulares por tarea.
- No determinar la concurrencia definitiva ni lanzar agentes.
- No mantener vivo al Planificador para supervisar ejecuciones.
- No sobrescribir `RUN.json` ni decidir estados de ejecución (`running`, `done`, `failed`, etc.).
- No hacer cambios de código, despliegues, migraciones ni llamadas pagadas durante la **planificación**, salvo que una política explícita los autorice y sean estrictamente necesarios para investigación; este plan no presupone esa autorización.
- No agregar un microservicio, una base de datos ni infraestructura nueva solamente por esta mejora.

## 4. Taxonomía obligatoria por tarea

Las dimensiones son **independientes**: una tarea grande no necesariamente es difícil; una tarea sencilla no necesariamente es segura; una tarea difícil puede ser paralelizable si no comparte dependencias.

### 4.1 Complejidad cognitiva (`complexity`)

| Valor | Definición operativa | Señales típicas |
|---|---|---|
| `low` | Solución conocida y localizada; poca incertidumbre | Ajuste evidente, patrón ya existente, prueba directa |
| `medium` | Requiere investigar y tomar algunas decisiones técnicas | Varios archivos, integración estándar, comportamiento parcialmente conocido |
| `high` | Razonamiento profundo, interacción entre componentes o incertidumbre relevante | Contratos cruzados, refactor delicado, múltiples escenarios |
| `extreme` | Incertidumbre excepcional o decisiones arquitectónicas de gran alcance | Invariantes difíciles, rediseño transversal, compatibilidad compleja |

La **complejidad** estima el razonamiento requerido, no el tiempo, la cantidad de archivos ni la calidad del modelo que debe ejecutarla.

### 4.2 Alcance (`scope`)

| Valor | Significado |
|---|---|
| `isolated_fix` | Corrige un defecto acotado |
| `small_change` | Modificación pequeña con efecto local |
| `large_change` | Modificación extensa o transversal a varios componentes |
| `full_feature` | Funcionalidad completa con comportamiento verificable de extremo a extremo |
| `full_system` | Conjunto o subsistema integral; **debe descomponerse**, salvo excepción explícita y justificada |

**Nota:** esto reemplaza la denominación informal de «duración» usada inicialmente en la conversación: estos valores describen **alcance**, mientras la duración se estima por separado.

### 4.3 Duración (`estimated_minutes`)

- Número entero positivo, estimado para **una ejecución razonable de la tarea**, incluidos cambios y verificación local prevista.
- Es una **estimación, no un límite de tiempo ni una orden de cancelación**.
- Debe registrarse con la confianza de la estimación (véase §4.6).
- Si no hay base para cuantificarla, el Planificador debe justificar la incertidumbre y pedir completar la planificación o descomponer la tarea. No inventar precisión.
- Las estimaciones deberán calibrarse después usando resultados históricos del Scheduler; **esa calibración no forma parte de este alcance**.

### 4.4 Riesgo (`risk`)

| Valor | Definición |
|---|---|
| `low` | Error de efecto local, reversible y detectable con pruebas simples |
| `medium` | Posible regresión funcional, contrato compartido o impacto moderado |
| `high` | Seguridad, datos, permisos, compatibilidad, producción, pagos o cambios difíciles de revertir |

El riesgo describe **el impacto potencial del error**, no la dificultad. Un fix de dos líneas sobre autorización puede ser `low` en complejidad y `high` en riesgo.

### 4.5 Acoplamiento (`coupling`)

| Valor | Definición |
|---|---|
| `low` | Independiente de otras tareas y con superficie de cambio poco compartida |
| `medium` | Usa contratos o recursos compartidos que requieren coordinación |
| `high` | Tiene interacciones estrechas, alto potencial de conflicto o restricciones cruzadas |

`coupling` es una **señal de planificación**, no una autorización automática de concurrencia. El Scheduler comprobará dependencias, worktrees, contratos y recursos antes de paralelizar.

### 4.6 Confianza de la estimación (`confidence`)

| Valor | Uso |
|---|---|
| `high` | Se investigó el código y existen precedentes o evidencia directa |
| `medium` | Hay evidencia parcial; algunas hipótesis siguen abiertas |
| `low` | La estimación es preliminar o depende de incógnitas relevantes |

**Campo complementario obligatorio:** `estimate_rationale`, explicación corta de los factores que sustentan la clasificación y duración; evita etiquetas arbitrarias.

## 5. Datos de planificación por tarea

Cada tarea ejecutable debe contener como mínimo:

| Campo | Tipo | Requisito |
|---|---|---|
| `id` | string | Identificador único y estable dentro del requisito |
| `milestone_id` | string | Hito al que pertenece |
| `title` | string | Nombre conciso |
| `objective` | string | Resultado concreto a conseguir |
| `after` | string[] | IDs de tareas prerrequisito; `[]` si no hay |
| `acceptance_criteria` | string[] | Condiciones observables de éxito |
| `verification` | object[] | Comandos de pruebas o verificaciones manuales explícitas |
| `complexity` | enum | `low / medium / high / extreme` |
| `scope` | enum | Cinco valores de §4.2 |
| `estimated_minutes` | integer | Estimación positiva |
| `risk` | enum | `low / medium / high` |
| `coupling` | enum | `low / medium / high` |
| `confidence` | enum | `low / medium / high` |
| `estimate_rationale` | string | Justificación breve |
| `repository` | string | Repositorio o rol de repositorio objetivo |
| `expected_paths` | string[] | Archivos o patrones previstos; **orientativos**, no lista obligatoria cerrada |
| `shared_resources` | string[] | Contratos, BD, puertos, servicios o recursos que puedan producir conflictos |

Otros campos pueden incorporarse bajo control de versión (p. ej. decisiones abiertas, contratos de entrada/salida, referencias a pruebas existentes). **No se admiten valores por defecto silenciosos** para clasificaciones obligatorias: la ausencia es un error de validación.

### 5.1 Ejemplo del objeto final (`PLAN.json`)

> Ejemplo ilustrativo; es el contrato de salida **propuesto**, no el formato que ya genere actualmente `bitacora.py`.

```json
{
  "schema_version": "1.0.0",
  "plan_id": "REQ-EXAMPLE",
  "revision": 1,
  "spec_ref": "SPEC.md",
  "milestones": [
    {
      "id": "M1",
      "title": "Autenticación base",
      "acceptance_criteria": [
        "La API cumple el contrato aprobado"
      ]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "milestone_id": "M1",
      "title": "Corregir validación de sesión",
      "objective": "Rechazar sesiones expiradas sin alterar sesiones válidas",
      "repository": "backend",
      "after": [],
      "complexity": "low",
      "scope": "isolated_fix",
      "estimated_minutes": 25,
      "risk": "high",
      "coupling": "medium",
      "confidence": "medium",
      "estimate_rationale": "Cambio localizado, pero sensible por afectar autenticación",
      "expected_paths": ["src/auth/**", "tests/auth/**"],
      "shared_resources": ["auth-session-contract"],
      "acceptance_criteria": [
        "Las sesiones expiradas son rechazadas",
        "Las sesiones vigentes continúan funcionando"
      ],
      "verification": [
        {
          "type": "command",
          "value": "pytest tests/auth -q",
          "purpose": "Probar rechazo y aceptación de sesiones"
        }
      ]
    }
  ]
}
```

**Regla:** no inventar rutas, comandos, repositorios ni nombres de test. La generación del plan debe basarse en la inspección real. Si una verificación aún no existe, el plan debe incluir la tarea de crearla o marcar explícitamente una comprobación manual con el resultado esperado.

## 6. Separación de plan y ejecución

| Archivo | Propiedad |
|---|---|
| `SPEC.md` | Qué se requiere, limitaciones y criterios generales |
| `PLAN.md` | Explicación humana de enfoque, hitos, tareas, decisiones y validación |
| `PLAN.json` | **Contrato estructurado del plan**, único artefacto operativo que publica el Planificador para el Scheduler |
| `HANDOFF.md` | Instrucciones para que una sesión ejecutora nueva reciba el contexto necesario |
| `RUN.json` | **Estado de ejecución**: intentos, sesiones, agentes, resultados, costes, heartbeat, errores, evidencias |

Reglas de consistencia:

1. Al **aprobarse**, un `PLAN.json` se congela para esa revisión. Cambiar el alcance implica crear **nueva revisión** o una enmienda versionada, no editar silenciosamente un plan en marcha.
2. `RUN.json` referencia `plan_id` y `revision`; no copia la planificación como segunda fuente de verdad.
3. El Planificador no escribe estados de ejecución ni registra sesiones ficticias.
4. Los `checkboxes` y el progreso narrativo de `PLAN.md` son presentación/bitácora, nunca autoridad operativa cuando existe `RUN.json`.
5. Una migración desde planes históricos debe conservar la evidencia real y distinguir **«clasificación no disponible»** de **«estimación realizada»**. No imputar valores retrospectivos sin marcarlos como inferidos.

## 7. Proceso del Planificador

### Paso 1 — Recibir objetivo y restricciones

Identificar el requisito, su definición de terminado, proyecto, repositorios, restricciones operativas, autorizaciones y decisiones del usuario. Reutilizar la metodología de entrevistas/clarificaciones cuando falte información verdaderamente bloqueante.

### Paso 2 — Inspeccionar el proyecto

Leer estructura, convenciones, archivos relevantes, pruebas y restricciones. Registrar hipótesis y evidencia. No asumir que rutas, dependencias o pruebas existen solo por aparecer en otro plan histórico.

### Paso 3 — Elaborar o actualizar `SPEC.md`

Preservar objetivos, historias de usuario, limitaciones, criterios de aceptación, alcance y decisiones ya aprobadas.

### Paso 4 — Diseñar hitos y DAG de tareas

Descomponer en entregables verificables. Registrar dependencias **reales** (`after`), evitando ordenamientos artificiales. Detectar tareas que deban esperar contratos compartidos.

### Paso 5 — Clasificar cada tarea

Evaluar **independientemente** complejidad, alcance, duración, riesgo, acoplamiento y confianza. Escribir justificación; para `scope=full_system`, descomponer antes de emitir una tarea ejecutable, salvo excepción documentada.

### Paso 6 — Documentar validación prevista

Para cada tarea: condiciones observables, comandos viables o prueba manual explícita, y rutas/contratos previstos. Los tests que aún no existan deben quedar como trabajo planificado, no como evidencia de éxito.

### Paso 7 — Generar archivos

Emitir `PLAN.md` legible y `PLAN.json` conforme al esquema. Mantener `HANDOFF.md` si el flujo existente lo requiere. El Markdown debe tener referencias coherentes a IDs de hitos y tareas del JSON.

### Paso 8 — Validación determinista (sin otro LLM obligatorio)

Ejecutar validación JSON Schema (o equivalente tipado), integridad de referencias, ausencia de ciclos y presencia de campos de aceptación. Devolver errores accionables y corregir el plan; no publicar uno inválido.

### Paso 9 — Aprobación y cierre

Aplicar el proceso de aprobación ya establecido en la metodología; publicar la revisión aprobada y finalizar la sesión de planificación. El Scheduler consume la revisión aprobada posteriormente.

## 8. Hitos y tareas de implementación

### M1 — Diagnóstico y diseño de contrato

- [x] **T1.** Localizar en el código actual dónde se producen `SPEC.md`, `PLAN.md`, `HANDOFF.md` y dónde `bitacora.py` extrae tareas/dependencias. Documentar el flujo real sin suposiciones. **Verificar:** mapa de productores/consumidores y un ejemplo real completo.
- [x] **T2.** Definir JSON Schema `1.0.0` o su equivalente tipado para planes, hitos y tareas, incluidas enumeraciones y validaciones. **Después de:** T1. **Verificar:** esquema publicado y casos válidos/inválidos.
- [x] **T3.** Documentar rúbrica de clasificación con ejemplos límite (fix sensible, refactor grande mecánico, cambio de contrato, sistema completo). **Después de:** T1. **Verificar:** ejemplos clasificados con justificación y coherencia interna.

### M2 — Salida estructurada y sincronización

- [x] **T4.** Incorporar la generación de `PLAN.json` al flujo existente del Planificador, sin sustituir los Markdown. **Después de:** T2, T3. **Verificar:** un requisito de prueba genera JSON parseable y campos completos.
- [x] **T5.** Introducir verificación de consistencia `PLAN.md` ↔ `PLAN.json` por IDs, hitos y dependencias (sin interpretar libremente toda la prosa). **Después de:** T4. **Verificar:** inconsistencias deliberadas producen fallos claros.
- [x] **T6.** Asegurar revisiones inmutables de planes aprobados y referencia desde la ejecución, sin alterar `RUN.json` existente en marcha. **Después de:** T4. **Verificar:** cambios al plan generan revisión nueva o error; historial preservado.

### M3 — Validación y retrocompatibilidad

- [x] **T7.** Implementar validador: duplicados, referencias inexistentes, ciclos de dependencias, hitos huérfanos, omisión de metadata y criterios vacíos. **Después de:** T2, T4. **Verificar:** pruebas negativas automatizadas.
- [x] **T8.** Probar el contrato con planes históricos representativos: `REQ-013`, `REQ-015` y `REQ-016`, **sin reescribir sus estados reales**. **Después de:** T5, T7. **Verificar:** informe de compatibilidad y valores que requieren enriquecimiento explícito.
- [x] **T9.** Probar el ciclo completo: objetivo ficticio → SPEC/PLAN/JSON → validación → aprobación → cierre del Planificador; sin lanzar ejecutores. **Después de:** T6, T8. **Verificar:** salida reproducible e integridad comprobada.

### M4 — Documentación y adopción

- [x] **T10.** Documentar el nuevo contrato, rúbrica y proceso de revisión en la metodología, conservando convenciones actuales y rutas reales descubiertas en M1. **Después de:** T9. **Verificar:** otra sesión nueva puede interpretar el plan sin contexto conversacional previo.
- [x] **T11.** Preparar compatibilidad para que el futuro Scheduler consuma `PLAN.json`, con ejemplo de entrada y errores esperables; **no implementar su motor en este requisito**. **Después de:** T9. **Verificar:** prueba de lectura/parseo sin invocar agentes.

**Dependencias de fases:** M1 → M2 → M3 → M4; dentro de cada fase rigen los `after` descritos. La paralelización es asunto del Scheduler, no una orden de este plan.

## 9. Criterios de aceptación (obligatorios)

### AC-01 — Preservación de la metodología

**Dado** un requisito existente, **cuando** se planifica con la mejora, **entonces** continúan generándose `SPEC.md`, `PLAN.md` y los handoffs que ya correspondan, sin perder requisitos, restricciones ni pruebas previamente especificadas.

### AC-02 — Contrato estructurado

**Dado** un plan listo para aprobación, **cuando** se genera la salida, **entonces** existe `PLAN.json`, parsea correctamente y supera el esquema versionado.

### AC-03 — Clasificación completa

**Dada** cada tarea ejecutable, **cuando** se valida el plan, **entonces** tiene `complexity`, `scope`, `estimated_minutes`, `risk`, `coupling`, `confidence` y `estimate_rationale` válidos, sin `null` ni defaults silenciosos.

### AC-04 — Taxonomías independientes

**Dada** una tarea simple que afecta seguridad, **cuando** se clasifica, **entonces** puede resultar `complexity=low` y `risk=high`; el validador no obliga a igualar ambas dimensiones.

### AC-05 — Dependencias verificadas

**Dado** un plan con dependencias, **cuando** se valida, **entonces** todos los IDs referenciados existen y el grafo no contiene ciclos; las dependencias inválidas bloquean la publicación.

### AC-06 — Superficies compartidas expresas

**Dadas** tareas sobre contratos o recursos compartidos, **cuando** se publican, **entonces** su `shared_resources` describe los puntos relevantes conocidos; la información no se presenta como garantía de paralelismo seguro.

### AC-07 — Verificación comprobable

**Dada** una tarea, **cuando** se emite, **entonces** posee criterios de aceptación observables y verificaciones previstas con comandos existentes o comprobaciones manuales explícitas; no se atribuyen éxitos no ejecutados.

### AC-08 — Tareas demasiado grandes

**Dada** una tarea `full_system`, **cuando** el Planificador intenta entregarla como unidad ejecutable, **entonces** la descompone o registra una excepción explícita revisable; nunca la trata automáticamente como un fix sencillo.

### AC-09 — Estimaciones honestas

**Dada** una estimación incierta, **cuando** se registra, **entonces** conserva `confidence=low` y una justificación; si falta información para un número defendible, el plan no se publica como si hubiera certeza.

### AC-10 — Inmutabilidad y revisiones

**Dado** un plan aprobado, **cuando** se necesita modificar su contenido, **entonces** se crea una nueva revisión o una enmienda rastreable; la revisión utilizada por una ejecución previa permanece recuperable.

### AC-11 — Aislamiento del estado de ejecución

**Dado** `RUN.json` con sesiones reales, **cuando** el Planificador produce o revisa el plan, **entonces** no lo reescribe, no resetea intentos ni cambia estados operativos.

### AC-12 — Fin de sesión del Planificador

**Dado** el plan aprobado y validado, **cuando** termina su generación, **entonces** el Planificador finaliza sin quedar como coordinador activo; el plan puede leerse en una sesión posterior sin depender de su contexto original.

### AC-13 — Compatibilidad retrospectiva

**Dados** `REQ-013`, `REQ-015` y `REQ-016`, **cuando** se evalúa compatibilidad, **entonces** se conserva su información y se identifican explícitamente clasificaciones faltantes; no se sustituyen valores ausentes por datos ficticios.

### AC-14 — Pruebas negativas

**Dado** un plan con campos ausentes, tipos inválidos, IDs duplicados, referencias rotas o ciclos, **cuando** se invoca el validador, **entonces** falla con diagnóstico que indique la tarea/campo causante y no publica un contrato aprobado.

### AC-15 — Sin selección de modelos

**Dada** una tarea clasificada como compleja, **cuando** se genera el plan, **entonces** no se asigna una cuenta, un modelo concreto ni un número de trabajadores. Es información destinada al Scheduler y su modelo de decisión.

## 10. Estrategia de verificación

La implementación debe añadir pruebas automatizadas equivalentes a las siguientes; los nombres y comandos definitivos dependen del repositorio real encontrado en M1:

| Prueba | Qué valida |
|---|---|
| Esquema / enums | Tipos, valores permitidos, obligatorios, versiones |
| Integridad DAG | Duplicados, ciclos, referencias inexistentes, orden lógico |
| Rúbrica | Casos contrastantes de complejidad, alcance, riesgo y acoplamiento |
| Consistencia documental | Hitos/tareas/IDs sincronizados entre `PLAN.md` y `PLAN.json` |
| Congelación | Un plan aprobado no cambia silenciosamente |
| Retrocompatibilidad | Los planes históricos son leídos sin corromper el estado |
| Ciclo de vida | Planificador termina al publicar; no lanza agentes |
| Prueba negativa | Rechazo claro de entradas incompletas o inválidas |

**Criterio de entrega:** todas las pruebas nuevas pasan; se ejecutan además los gates existentes aplicables de la metodología; se reportan fallos preexistentes separadamente, sin llamarlos aprobados.

## 11. Restricciones y decisiones de seguridad

- Respetar las restricciones del proyecto y de la metodología (permisos, secretos, branches, revisiones, gates y límites de coste).
- No ejecutar migraciones, despliegues, publicaciones, envíos externos ni comandos destructivos como efecto secundario de generar el plan.
- No inventar permisos por omisión. Autorización no declarada no equivale a autorización.
- No corregir planes históricos alterando `RUN.json` ni el estado real de un requisito ya ejecutado.
- Preferir cambios incrementales y retrocompatibles. Si un consumidor antiguo solo entiende `PLAN.md`, mantenerlo funcional durante la transición.
- Mantener el JSON determinista cuando sea posible (orden estable de claves y tareas, IDs estables, formato canonizado); registrar revisión y procedencia para auditoría.

## 12. Riesgos de la implementación y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Clasificaciones subjetivas o inconsistentes | Rúbrica, justificación y pruebas de casos límite |
| `PLAN.md` y `PLAN.json` divergen | Generación desde representación común y validador de consistencia |
| Estimaciones artificialmente precisas | Confianza y rationale; calibración histórica futura |
| Planes antiguos se rompen | Compatibilidad explícita; migración opt-in, no reescritura masiva |
| Confundir acoplamiento bajo con paralelismo seguro | Anotar recursos compartidos; concurrencia sigue bajo Scheduler |
| Agregar demasiadas responsabilidades al Planificador | Rechazar selección de agente, ejecución, monitorización y recovery en este módulo |
| Alteración accidental de trabajos ya aprobados | Versionado por revisión y separación rigurosa de `RUN.json` |

## 13. Entregables

1. Contrato versionado `PLAN.json` y su validador.
2. Rúbrica de las cinco dimensiones y la confianza de estimación.
3. Generación del JSON desde el Planificador actual, manteniendo `SPEC.md`, `PLAN.md` y handoffs aplicables.
4. Pruebas automáticas de esquema, integridad y compatibilidad.
5. Ejemplos reales/fixtures y reporte de migración de planes existentes.
6. Documentación de interfaz para el Scheduler, sin implementarlo en esta fase.
7. Informe final con cambios, evidencias, decisiones tomadas y pendientes.

## 14. Definición de terminado (DoD)

- [x] Todas las tareas T1–T11 cerradas con evidencia.
- [x] AC-01 a AC-15 verificados y trazables a pruebas o inspecciones documentadas.
- [x] `PLAN.json` generado y validado para un caso nuevo completo.
- [x] `SPEC.md` / `PLAN.md` / `HANDOFF.md` preservados según las reglas existentes.
- [x] Compatibilidad con REQ-013, REQ-015 y REQ-016 evaluada sin alterar sus ejecuciones.
- [x] Ningún estado operativo de `RUN.json` sobrescrito por el Planificador.
- [x] Documentación y gates aplicables actualizados; fallos restantes reportados honestamente.
- [x] Planificador finaliza tras producir el artefacto aprobado.

## 15. Decisiones abiertas que conviene resolver durante M1

Estas cuestiones **no impiden redactar el plan**, pero deben resolverse contra el código real antes de implementar:

1. Ubicación exacta del nuevo esquema y si el modelo de tipos actual usa Python, TypeScript o ambos.
2. Forma de derivar `PLAN.md` y `PLAN.json` de una misma representación para evitar divergencias.
3. Mecánica exacta de aprobación/versionado con el supervisor existente.
4. Compatibilidad de lectura de planes previos sin `PLAN.json`.
5. Manejo de tareas con estimación de duración todavía indeterminable: bloquear aprobación, insertar tarea de investigación o permitir excepción formal.

---

**Principio rector:** el Planificador **describe y clasifica el trabajo**. No decide quién lo ejecutará, no lo supervisa y no intenta recuperarlo. Produce un contrato autocontenido, verificable y versionado; después desaparece.

## 16. Cierre de la Fase 1 (2026-10-14)

**Resultado.** El Planificador produce `PLAN.json` 1.1.0 validado, sincronizado con `PLAN.md`, congelado en la
aprobación y verificado por una única compuerta en todas las rutas de lanzamiento. Módulo: `skill/scripts/bt_planner/`
(README = contrato); metodología: `skill/references/plan-contract.md`; decisiones D-019, D-020, D-021.

| Tareas | Evidencia |
|---|---|
| T1–T3 (mapa, esquema, rúbrica) | REQ-009 `artifacts/plan-contract-map.md`; `bt_planner/data/plan.schema.json`; rúbrica con casos límite en el README del módulo |
| T4–T6 (JSON, sincronía, revisiones) | `sync.py`, `revisions.py`; REQ-012 amplía la sincronía a títulos, repos, verificaciones e ids duplicados y congela en la aprobación |
| T7–T9 (validador, históricos, ciclo completo) | `contract.py` + `evidence.py` + `quality.py`; compat de REQ-013/015/016 de solo lectura; 6 pruebas reales de planificación (`REQ-012/planning-trials/`) |
| T10–T11 (documentación, interfaz para el Scheduler) | README del módulo, `plan-contract.md`, `plan.example.json` 1.1.0; el lector del núcleo del Scheduler carga la revisión congelada (solo lectura) |

**Criterios AC-01…AC-15:** trazados a pruebas en `REQ-012/AC-TRACE.md`.

**Cambios del cierre respecto al diseño original**
1. Esquema 1.1.0: `classification_evidence` obligatorio (justificación + referencias tipificadas por dimensión); 1.0.0
   sigue cargándose (REQ-009/010 congelados) pero las revisiones nuevas deben usar 1.1.0.
2. La sincronía MD↔JSON compara también títulos, `repo`, `verify` y `risk` legado y rechaza ids/encabezados duplicados.
3. La aprobación congela exactamente los bytes aprobados; un lanzamiento nunca congela: edición no aprobada = `PLAN_DRIFT`,
   plan nunca congelado = `PLAN_NOT_FROZEN` (solo `--force` explícito del dueño, registrado `launch-forced`).
4. Tareas sin orden entre sí que comparten ruta o recurso no pueden declarar `coupling: low`.

**Limitaciones demostradas (no resueltas, registradas como pendientes)**
- La evidencia se verifica por estructura y existencia (ficheros, specs, tareas, requisitos, decisiones, commits y
  ejecutables citados), no por verdad semántica: ningún validador determinista puede confirmar que una justificación
  fluida sea cierta (P-023). Los criterios AC-03/AC-07/AC-09 piden justificación con evidencia verificable, no oráculo de verdad.
- Las estimaciones no están calibradas con tiempos reales: eso pertenece al Scheduler (P-020).
