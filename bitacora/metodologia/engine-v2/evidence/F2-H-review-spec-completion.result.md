AXIS: spec

VERDICT: APPROVED

FINDINGS: Ninguno demostrado.

CHECKED:
- Leí completo `/home/david/dev/.engine-v2-wt/F2-H.brief.md`. Queda resuelta la brecha del informe anterior: contrasté sus criterios con el diff `6a28476fe..05d02454ab8c988d324668e07ce29631d9cd4a5d`, el contrato F2 y §§20.3–20.7 del documento maestro.
- Verifiqué que el instalador resuelve recursos Claude/Codex desde la raíz instalada, copia las skills de Antigravity para el rol seleccionado, conserva Planner como default de Antigravity, admite `designer` en la ejecución general Claude/Codex y con `--agent designer`, y protege archivos manuales salvo `--force`.
- Revisé los prompts de los ocho roles y las pruebas estáticas: las skills privadas tienen rutas y condiciones de carga; también se comprueban frontmatter, rutas, exclusiones del Implementer, protocolo del Runner y formas obvias de secretos.
- `python -m unittest discover -s skill/scripts/tests -p 'test_agent_skills_static.py'` → pasó, 9 pruebas. `python -m unittest discover -s tests/migration -p 'test_entrypoint_parity.py'` → pasó, 12 pruebas. `python skill/scripts/install_agents.py --help` → código 0; documenta los ocho roles y las opciones. `git diff --check 6a28476fe 05d02454` → código 0.
- `test_role_routing.py` no pudo importarse en las invocaciones enfocadas por falta de `bt_agents` en `sys.path`; no lo considero prueba de un defecto en el diff. No repetí la suite completa: el resultado ya registrado es 2.423 pruebas, con los 15 fallos baseline conocidos.
- Brechas restantes: no verifiqué instalaciones en perfiles reales; el brief reserva esa instalación para el trabajo posterior autorizado del lead.