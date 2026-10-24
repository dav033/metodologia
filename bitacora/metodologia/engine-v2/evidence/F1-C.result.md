Aye. **STATUS: DONE**

**SUMMARY:** Actualicé el prompt del Planner y cuatro skills para planificar con schema 1.3.0, el gate activo de Designer, auditorías tempranas y composición entre subplanes. Conservé la ruta legacy y documenté el rechazo `PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE` sin proponer workarounds. El commit es `99c52be8`; el worktree quedó limpio.

**CHANGES:**

- [planner.md](/home/david/dev/.engine-v2-wt/F1-C/skill/agents/planner.md): etapa obligatoria de subplanes, reglas de Designer, auditoría/rework y verificación externa.
- [functional-subplan-decomposition/SKILL.md](/home/david/dev/.engine-v2-wt/F1-C/skill/agents/planner/skills/functional-subplan-decomposition/SKILL.md): contrato 1.3.0, códigos de validación y correcciones.
- [wbs-dag-decomposition/SKILL.md](/home/david/dev/.engine-v2-wt/F1-C/skill/agents/planner/skills/wbs-dag-decomposition/SKILL.md), [adversarial-plan-review/SKILL.md](/home/david/dev/.engine-v2-wt/F1-C/skill/agents/planner/skills/adversarial-plan-review/SKILL.md) y [plan-mermaid-view/SKILL.md](/home/david/dev/.engine-v2-wt/F1-C/skill/agents/planner/skills/plan-mermaid-view/SKILL.md): DAG interno, revisión adversarial y vista opcional de subplanes.

**VERIFICATION:**

- Prueba enfocada, `python -m unittest tests.test_planner_runtime tests.test_planner_profile` → **21 tests, 2 fallos**. Los fallos esperan el texto “schema 1.2.0” y exactamente cuatro skills; ambas expectativas quedaron obsoletas por este cambio.
- Suite completa, `python -m unittest discover -s tests` → **2.404 tests, 17 fallos, 6 omitidos** (896,5 s). Quince fallos corresponden a las categorías baseline de RULES.md; los otros dos son las mismas expectativas obsoletas del perfil Planner.
- Validación de frontmatter de las cinco skills y `git diff --check` → **correctos**.

**COMMITS:** `99c52be8 Update planner prompts for schema 1.3 subplans`

**PROVENANCE:** No se incorporó contenido nuevo de fuentes externas.

**CONCERNS:** Las dos aserciones de `test_planner_profile` requieren actualización fuera del alcance de archivos asignado. No se proporcionó una ruta `-o` para un archivo de resultado; entrego el informe aquí.