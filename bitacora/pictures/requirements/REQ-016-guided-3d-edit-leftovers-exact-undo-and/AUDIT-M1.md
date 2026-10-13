# Auditoría independiente — Hito M1 (REQ-016)

- **Fecha:** 2026-10-13 15:42
- **Auditor:** Gemini 3.8 Flash low (Antigravity)
- **Rama auditada:** `feat/req-016-guided-3d-edit-leftovers-exact-undo-and` en worktree `t12`
- **Commits auditados:**
  - `58f10c04` feat(guiada): «Deshacer» el último ajuste de un plan 3D restaura el plan de antes (espec, firma y precio), sin ajuste inverso (P-042)
  - `fe3e9bcb` test(guiada): la prueba de «Deshacer» reproduce también el color que no vuelve por su nombre (P-042)
- **Base:** `1f304b4e` (feat/req-015-judge-fix)

---

## 1. Veredicto

**PASS** (Aprobado sin cambios adicionales requeridos en el árbol).

El hito M1 (Tarea T1) cumple cabalmente con la especificación (US-1, R1, P-042), restaura fielmente el plan previo exacto en memoria byte a byte con su firma, cotización y hash, resuelve la deriva por ajuste inverso y la mutación de paletas/códigos por retorno nominal, preserva los estados y acciones posteriores del usuario (uso, compra abierta), limpia adecuadamente imágenes desactualizadas en IndexedDB y rechaza honestamente cuando el token está vencido o no hay plan previo disponible.

---

## 2. Hallazgos corregidos (Findings fixed)

En las sesiones previas del constructor (Opus/Sonnet) y revisiones antagonistas se identificaron y solventaron directamente en el commit:
1. **Borrado de imagen desactualizada en navegador (`borrarImagenNavegador`):** Al deshacer, se purga de IndexedDB la imagen del plan deshecho para evitar que una recarga muestre la imagen del ajuste revertido.
2. **Reproducción de fusión de color por nombre:** Se reforzó el caso de prueba en `fe3e9bcb` para que el test reproduzca fielmente la fusión de códigos de color (`040+970` a `040`) demostrando que el deshacer restaura byte a byte los códigos exactos originales.
3. **Rechazo por expiración del token (`APROBACION_VENCIDA`):** Detección defensiva de token vencido o con margen menor a 5 minutos, informando al cliente con claridad en lugar de dejar un plan inoperante.

---

## 3. Hallazgos diferidos (Findings deferred)

Todos los hallazgos secundarios identificados han sido debidamente catalogados en `PENDING.md` y no bloquean M1:
1. **P-078 (Urgencia med, Complejidad S):** Ajuste de historial de chat tras deshacer (el mensaje de confirmación previo permanece en el chat) y sincronización de registro para evitar entradas fantasma en cierres desincronizados.
2. **P-079 (Urgencia med, Complejidad S):** Limpieza de imagen en IndexedDB al realizar un ajuste normal sucesivo (hoy `borrarImagenNavegador` se invoca en deshacer, pero un ajuste directo nuevo que recarga la página puede leer la imagen previa si no se re-generó).
3. **P-080 (Urgencia low, Complejidad M):** Extensión de funcionalidad «Deshacer» para planes generados por el motor de Python e intención por chat («deshaz eso»).

---

## 4. Pruebas y verificaciones ejecutadas (What was run)

Todas las verificaciones se ejecutaron en el entorno local contra el worktree `t12`:

1. **Prueba de verificación del hito:**
   ```bash
   npx tsx --conditions=react-server scripts/test/test-deshacer-ajuste-3d.ts
   ```
   **Resultado:** 8 tests pasan (0 fallos, 303 ms). Verifica:
   - Deriva de redimensionamiento (3.00x2.40 -> 2.97x2.38 en inverso vs idéntico en deshacer).
   - Retorno y fusión de color nominal (040+970 -> 040 vs idéntico en deshacer).
   - Cadena múltiple de hasta 4 ajustes con desapilado LIFO.
   - Rechazo honesto por token vencido.
   - Rechazo honesto si el plan cambió por fuera.
   - Preservación de selecciones del cliente (uso y compra).

2. **Prueba de UI de Motor 3D:**
   ```bash
   npx tsx scripts/test/test-ui-plan-motor3d.ts
   ```
   **Resultado:** 16 tests pasan (incluyendo caso explícito de renderizado de botón «Deshacer» en `TarjetaPlan`).

3. **Suites completas de regresión:**
   ```bash
   npm run motor3d:test
   ```
   **Resultado:** 27 tests pasan (0 fallos).
   ```bash
   npm run guiada:test
   ```
   **Resultado:** 14 suites / scripts pasan (0 fallos).

4. **Calidad de código y linters:**
   - `npx eslint` sobre todos los archivos creados y modificados en M1: **0 errores**.
   - `npx tsc --noEmit`: sin errores en el código de M1 (único error preexistente en `src/app/layout.tsx` por tipado `LayoutProps` de Next.js independiente del cambio).
   - Git status limpio en rama `feat/req-016-guided-3d-edit-leftovers-exact-undo-and`.

5. **Documentación y bitácora:**
   - Registrada decisión **D-045** en `DECISIONS.md`.
   - `SPEC.md` y `PLAN.md` reflejan adecuadamente el avance de M1/T1.
