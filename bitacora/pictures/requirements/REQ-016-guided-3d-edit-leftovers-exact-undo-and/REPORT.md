# Informe de Cierre — REQ-016 (Guided 3D edit leftovers: exact undo and colour resolver)

- **Requerimiento:** REQ-016 (P-042, P-058, P-082)
- **Fecha:** 2026-10-13
- **Rama:** `feat/req-016-guided-3d-edit-leftovers-exact-undo-and` en worktree `t12`
- **Base:** `1f304b4e` (`feat/req-015-judge-fix`)
- **Head commit:** `fb872bce` (`fix(motor3d): retain untouched colour resolutions on replay`)
- **Estado:** Completado (Done) / Verificado

---

## 1. Built (Construido)

Se implementaron y corrigieron todos los objetivos de REQ-016 organizados en dos hitos principales y seis commits en la rama local:

### Hito M1 — Deshacer Exacto (Exact Undo — P-042, R1, US-1)
- **Restauración fiel en memoria (`D-045`):** Se introdujo el mecanismo de «Deshacer» en la tarjeta del plan 3D guiado (`src/components/guiado/TarjetaPlan.tsx`, `VistaGuiada.tsx`, `deshacer-ajuste.ts`, `usarDeshacerAjuste.ts`). En lugar de calcular y aplicar un ajuste inverso (que provocaba deriva dimensional de hasta 7.2% y mutación/fusión de códigos de color por retorno nominal, ej. `040+970` a `040`), la UI mantiene una pila LIFO en memoria con el widget anterior completo: especificación firmada, hash, token y cotización.
- **Acciones y estado del cliente preservados:** Al deshacer se conserva el estado posterior del cliente (uso de la idea, compra abierta) mientras se purga honestamente la imagen obsoleta del plan revertido de IndexedDB (`imagenes-navegador.ts`) y se rechaza limpiamente si el token ha vencido (`APROBACION_VENCIDA`) o si el plan cambió externamente.
- **Commits M1:**
  - `58f10c04`: feat(guiada): «Deshacer» el último ajuste de un plan 3D restaura el plan de antes (espec, firma y precio), sin ajuste inverso (P-042).
  - `fe3e9bcb`: test(guiada): la prueba de «Deshacer» reproduce también el color que no vuelve por su nombre (P-042).

### Hito M2 — Resolutor de Color (Colour Resolver — P-058, R2–R4, US-2)
- **A1 / R2 — Almacenamiento de última orden de color y supresión de aclaraciones innecesarias (`D-046`):**
  - Se almacena el contexto de la última sustitución exitosa de color en el contexto firmado del plan (`src/lib/plan/orden-color.ts`, `src/lib/globos3d/motor/orden-color.ts`).
  - Cuando una orden de paleta se repite o su destino ya está seleccionado en la pieza tras un ajuste previo, se evita una pregunta redundante de aclaración.
  - Las aclaraciones potenciales («puede ser») se contabilizan correctamente en el balance de `no_aplicadas` y en la auditoría durable.
- **A2 / R3 — Preservación de `origen`:**
  - `sumarIdeaAEspec` en `src/lib/globos3d/motor/espec-desde-idea.ts` mantiene intacto el campo `origen` de las piezas agregadas, evitando que se pierda la protección anti-alternancia.
- **A3 / R4 — «Rosa → rosado» sin aclaración innecesaria (`D-047`):**
  - Se añadió la guarda para evitar preguntas de aclaración cuando el reemplazo solicitado coincide exactamente con el color que la pieza ya tiene (`!entran.includes(codigo)` con protección para destino único `Set(entran).size === 1` en `color-en-pieza.ts`).
- **A4 — Declaración de `origen.tipo` en consumo:**
  - `consumo.ts` declara adecuadamente `origen.tipo: "resolutor"` en lugar del valor no conforme `'ui'`, permitiendo que el motor diferencie el origen de edición de manera fiel.
- **Compatibilidad reader-before-writer (`D-035` / `D-046`) y resolución de piezas no tocadas (`P-082` / `D-048`):**
  - Emisión de token v3 condicionada por bandera `PLAN_COLOR_ORDER_V3=true` (desactivada por defecto). Los lectores aceptan v1, v2 y v3.
  - Los planes legados v1/v2 permanecen como v2 con historial desconocido hasta que una edición explícita de color establezca contexto conocido.
  - Implementación de `colour-order.v2` con instantáneas `resolucionesSinCambio` (`fb872bce`): previene que al repetir una orden idéntica sobre la misma selección se reinterpreten y muten piezas no tocadas originalmente (resolviendo `P-082`).
- **Commits M2:**
  - `84fa287a`: feat(globos3d): almacenar última orden de color en payload v3 y evitar aclaración si destino ya está seleccionado (P-058 A1, D-046)
  - `c6dd13d4`: fix(motor3d): conservar origen al sumar una idea; «rosa → rosado» sin aclaración si ya está puesto; origen.tipo como resolutor (REQ-016 T3, P-058 A2-A4, D-047)
  - `df0be2a0`: fix(motor3d): preserve token rollout and colour order boundaries
  - `fb872bce`: fix(motor3d): retain untouched colour resolutions on replay

---

## 2. Verification evidence (Evidencia de Verificación)

Todas las verificaciones se ejecutaron en el entorno local sobre la rama `feat/req-016-guided-3d-edit-leftovers-exact-undo-and` en `t12`:

| Verificación | Comando ejecutado | Resultado |
|---|---|---|
| **Compuerta completa (Full Gate)** | `npm run gate` | **GATE OK** (10/10 suites completas pasaron en ~559 s). Suites: `contracts:check`, `kontext:test`, `catalogo:test`, `globos3d:test`, `motor3d:test`, `escena:test`, `guiada:test`, `topes:test`, `test-cotizacion-unica`, `test-guardia-prerender`. |
| **Verificación M1 (Deshacer 3D)** | `npx tsx --conditions=react-server scripts/test/test-deshacer-ajuste-3d.ts` | **8/8 tests pass** (0 fallos, 304 ms). Identidad byte a byte sin deriva dimensional; reversión exacta de códigos de color fusionados (`040+970` a `040`); rechazo honesto por token vencido. |
| **UI de Plan Motor 3D** | `npx tsx scripts/test/test-ui-plan-motor3d.ts` | **16/16 tests pass**. Renderizado e interacción del botón «Deshacer» en `TarjetaPlan`. |
| **Verificación M2 (Confirmación Color)** | `npx tsx --conditions=react-server scripts/test/test-confirmacion-color-motor3d.ts` | **OK**. Supresión de aclaración si el destino ya está seleccionado tras ajuste. |
| **Suite principal última orden** | `npx tsx --conditions=react-server scripts/test/test-ultima-orden-color-motor3d.ts` | **20/20 tests pass**. Cobertura de A1, A2, A3, A4, orígenes y contexto de orden de color. |
| **Regresión Replay / P-082** | `npx tsx --conditions=react-server scripts/test/test-ultima-orden-color-replay-selection.ts` | **9/9 tests pass**. Preservación de resoluciones sin cambio en repetición de selección idéntica; compatibilidad con lector v1 y escritor v3. |
| **Verificación de Tipos (TypeScript)** | `npx tsc --noEmit` | **Clean (Exit code 0)**. 0 errores en todo el proyecto. |
| **Linter (ESLint)** | `npm run lint` | **Exit code 0**. 0 errores (50 advertencias preexistentes en scripts/componentes no modificados). |
| **Pruebas de Propiedades de Color** | Invocación generador (semilla 20261009, 40 casos) | **Exit code 0**. 306 aplicados, 3 ausentes, 15 preguntas, 15 opciones, 15 replays, 15 sin editar verificados con historial retornado. |

---

## 3. Rulings (Decisiones y Reglas)

- **D-045 (Deshacer guiado en memoria):** La acción «Deshacer» restaura el widget previo guardado en memoria (especificación firmada, hash, token, cotización) en lugar de invocar un ajuste inverso o crear un nuevo endpoint en el servidor. Preserva la firma original y previene divergencia de precios o deriva geométrica.
- **D-046 (Última orden de color en contexto firmado v3):** Se almacena la última orden exitosa de color en el contexto de aprobación firmado del plan. Para cumplir con la política reader-before-writer (D-035), el escritor v3 permanece condicionado a `PLAN_COLOR_ORDER_V3=true` (desactivado por defecto). Los lectores soportan v1, v2 y v3. Los planes v1/v2 mantienen historial desconocido sin forzar aclaraciones erróneas.
- **D-047 (Preservación de origen y destino único en guard):** `sumarIdeaAEspec` preserva `origen`. `consumo.ts` declara `origen.tipo: "resolutor"`. `color-en-pieza.ts` exige destino de código único (`Set(entran).size === 1`) para evitar suprimir preguntas cuando una orden multicolor afecte piezas existentes.
- **D-048 (Instantáneas de resolución sin cambio v2):** Se extiende el contrato v3 con la versión interna `colour-order.v2` que almacena `resolucionesSinCambio`. Esto garantiza que piezas seleccionadas originalmente que no requirieron cambio mantengan su resolución intacta en reejecuciones idénticas sin alterar la prioridad de tarjeta exacta.

---

## 4. Needs your eyes (Requiere tu atención)

1. **Activación de `PLAN_COLOR_ORDER_V3`:**
   - La funcionalidad de emisión de tokens v3 con historial persistido de órdenes de color está protegida por la bandera de entorno `PLAN_COLOR_ORDER_V3` (por defecto `false` en `.env.example`).
   - Requiere que primero se despliegue a producción la versión que lee tokens v3 (`colour-order.v1` y `colour-order.v2`) antes de habilitar la emisión de v3 para evitar que clientes con versiones viejas o sesiones concurrentes reciban tokens no interpretables.
2. **Revisión del Pull Request / Merge:**
   - La rama `feat/req-016-guided-3d-edit-leftovers-exact-undo-and` en `t12` contiene 6 commits listos para revisión y merge a la rama integradora / `main`.

---

## 5. Proposals (Propuestas para el futuro)

1. **P-078 / P-080 — Deshacer ampliado:**
   - Sincronizar el historial de chat al deshacer (anotar visualmente que el último ajuste fue deshecho para evitar confusión en el diálogo).
   - Extender el mecanismo de deshacer por instantánea a planes guiados generados por el motor de Python y reconocer la intención de deshacer desde el chat de texto («deshaz eso»).
2. **P-084 — Refactorización de suite de pruebas:**
   - Separar `test-ultima-orden-color-motor3d.ts` (542 líneas) dividiendo las pruebas puras de lógica de dominio de las pruebas de ciclo de vida de rutas firmadas.

---

## 6. Pending (Pendientes y Defectos Relacionados)

Los siguientes ítems permanecen documentados en `PENDING.md` como no bloqueantes para REQ-016:
- **P-083 (med, M):** Fallo en compilación completa local de Next.js (`npm run build`) en worktree por symlink externo de Turbopack e importación cliente de `node:crypto` a través de `ReferenceAnalysisController`. (No atribuible a REQ-016).
- **P-081 (low, S):** Seguimientos menores de T3: revisar si `soloEseColor` requiere evaluación per-pieza en vez de agregada; documentar `idea_sumada` como legado en `ORIGENES_ESPEC`.
- **P-079 (med, S):** Purgado de imágenes en IndexedDB en ajustes sucesivos directos (actualmente cubierto en Deshacer).
- **P-084 (low, S):** División de responsabilidades en `test-ultima-orden-color-motor3d.ts`.

---

## 7. Walkthrough (Recorrido de la Solución)

1. **Flujo de Deshacer en el Asistente Guiado:**
   - El usuario solicita un ajuste (ej. «hazlo más alto» o «cámbialo a dorado»).
   - La tarjeta del plan 3D renderiza el nuevo plan y muestra el botón «Deshacer» junto a «Último ajuste».
   - Si el usuario pulsa «Deshacer», el cliente toma la instantánea previa de memoria (`espec`, firma, hash y cotización intactos) y restablece el estado sin recalcular ni contactar al servidor.
   - La imagen 3D deshecha se elimina de IndexedDB para que no reaparezca tras refrescar.
2. **Flujo de Resolución de Color:**
   - El usuario pide «cambia a azul». El motor resuelve y almacena la orden en el contexto de edición.
   - Si el usuario vuelve a pedir «azul» o un ajuste posterior sobre la misma selección, el resolutor detecta que el destino ya fue procesado y no formula preguntas redundantes.
   - Si una orden idéntica afecta a múltiples piezas donde una cambió y otra se mantuvo sin cambios por prioridad de tarjeta (`P-082`), la instantánea `colour-order.v2` recuerda la resolución neutra y protege ambas piezas contra mutaciones inesperadas.
