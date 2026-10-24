Aye

**AXIS:** spec — `origin/main...6c936b4e653c587ced26b2646bbeeda320bcbd63` (incluye `d2a1d3fd7` y las reparaciones F4-1b).

**VERDICT:** CHANGES_NEEDED

**FINDINGS**

1. **F4-1-F1 · high · defect** — `skill/scripts/bt_composition/engine.py:26-28,181-182,200-201,225`  
   **Criterio:** ENGINE-F4 §6: los veredictos deben vincularse al `composition_id`, `manifest_sha256` y árbol candidato. Abrir el workspace recalcula el hash al cambiar el estado; publicar vuelve a recalcularlo al guardar veredictos. Además, `publish()` solo recibe estados como `"PASS"` y no comprueba identidad del candidato, hash ni árbol de la evidencia. Así, un PASS obsoleto o de otro candidato puede publicarlo, y el hash cambia durante el ciclo. **Remedio:** mantener un hash estable para la identidad inmutable del candidato y exigir que cada veredicto lo identifique y vincule al commit/árbol evaluado. `semantic_fingerprint`: `composition-verdict-unbound-to-stable-candidate-manifest`.

2. **F4-1-F2 · medium · defect** — `skill/scripts/bt_composition/engine.py:245-247`  
   **Criterio:** ENGINE-F4 §1, equivalencia de evidencia por rutas relevantes, contratos y entorno. Dos `EvidenceKey` con `paths=()` y digest, contratos y entorno iguales se consideran reutilizables; `propagate()` puede entonces omitir reverificación aunque no haya rutas cuya equivalencia se haya probado. El adaptador rechaza rutas vacías al calcular el digest, pero la API pública del módulo no exige que la clave las contenga. **Remedio:** rechazar claves con rutas vacías antes de afirmar equivalencia. `semantic_fingerprint`: `evidence-reuse-with-empty-relevant-path-set`.

3. **F4-1-F3 · medium · defect** — `skill/scripts/bt_composition/engine.py:113-125`  
   **Criterio:** ENGINE-F4 §1, base de construcción `current` o una base de ejecución indicada. Con una composición actual publicada, pasar `run_base` no cambia la base elegida: `current_commit` prevalece siempre. La llamada construye desde un commit distinto al solicitado. **Remedio:** honrar `run_base` cuando se proporciona y definir/verificar explícitamente cómo se publica esa composición respecto de `current`. `semantic_fingerprint`: `explicit-run-base-overridden-by-current`.

**CHECKED:** refs inmutables y CAS con OID completos; transacción atómica de publicación; ruta C1 → S1@v2 → C2 y preservación de C1 ante fallo; reconciliación tras fallos de escritura; nuevos números tras rechazo; rechazo de versiones hacia atrás; acumulación de rutas de conflicto; digest de rutas y comparación de claves; propagación selectiva en las ramas inspeccionadas. El orden puede pasarse mediante `member_order`; sin él, se usa el orden de inserción del mapping, así que la garantía de orden del plan depende del llamador. Revisé los consumidores del módulo: el adaptador y las pruebas de integración; el cableado M1/M3 del runtime queda fuera de este subplan y está en cola aparte. `git diff --check` pasó; no ejecuté pruebas. No encontré otros desvíos demostrados dentro del eje spec.