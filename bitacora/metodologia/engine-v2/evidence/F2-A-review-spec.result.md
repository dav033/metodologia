AXIS: spec  
VERDICT: CHANGES_NEEDED

FINDINGS:

- `F2A-1` — severity: low; classification: defect; `skill/references/subagents.md:19`. **Disparador:** alguien consulta la tabla para descubrir las skills disponibles. **Esperado:** que el inventario refleje las skills cableadas en los prompts. **Observado:** la fila de Researcher dice “None currently listed”, aunque `skill/agents/researcher.md:16-17` activa dos skills privadas. La instrucción posterior de consultar el prompt del rol evita que se desactiven, pero deja el inventario incorrecto. **Remedio acotado:** listar `external-research-memory` y `source-freshness-verification`.

CHECKED:

- Diff de `a02434ced7efdba0086616a6aac49f310a3353b7` contra su padre; checkout sin cambios.
- Requisitos F2-A del contrato, PROMPT puntos 5 y 7, maestro §§14.6.5, 19 y 20.7; política vigente en `bt_review_policy.py`.
- Prompts y skills de Antagonist, Runner y Explorer; el comando de consulta de Explorer coincide con el parser disponible y su contrato.
- `git diff --check`: sin errores. No ejecuté pruebas ni validé la instalación de los prompts.

Gaps de cobertura: la instalación efectiva y el comportamiento runtime de los roles no forman parte de esta inspección de solo lectura.