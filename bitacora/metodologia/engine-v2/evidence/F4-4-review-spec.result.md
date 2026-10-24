AXIS: spec

VERDICT: APPROVED

FINDINGS: Ninguna desviación contractual introducida en `3544d295` frente a `9186e9ba`. El cambio añade `design → designer` y acepta `review_axis: visual → reviewer`, manteniendo `kind: audit`; preserva los mapeos y las opciones de modelos existentes. El catálogo nuevo usa Claude Opus/high y Codex GPT-6.1 Sol/high. La selección continúa pasando por las rutas existentes de candidatos, cuotas y elegibilidad. `review_axis` no se incorpora a `TaskFacts`; según el ruling del brief, el rol basta si M2 no tiene un espacio natural para esa metadata. M1 aporta `subplan_id`/`review_axis` y M3 deriva el eje visual en el brief: son tareas con interfaces fijadas, no omisiones de este diff.

CHECKED:

- Diff, estado del worktree y consumidores: revisados; `git diff --check` pasó.
- `python -m unittest discover -s tests -p 'test_role_policy.py'`: 9 tests, OK.
- `python -m unittest discover -s tests -p 'test_plan_contract_compat.py'`: 10 tests, OK; incluye comparación de ruta legacy.
- `python -m unittest discover -s tests -p 'test_scheduler_decision_sources.py'`: 17 tests; 1 fallo en `test_m1_reserves_the_m2_recommendation_through_its_assignment_contract`, por `PLAN_CHECKS_UNMAPPED` al congelar el fixture. La falla corresponde a la validación de criterios/verificaciones de ese fixture; no encontré relación con los hunks de F4-4.
- No ejecuté la suite completa.

Cobertura pendiente fuera de este cambio: la producción de metadata por M1 y la construcción del brief visual por M3, ambas asignadas a sus tareas respectivas.