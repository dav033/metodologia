AXIS: standards

VERDICT: APPROVED

FINDINGS: Ninguno. No encontré violaciones demostrables de corrección o seguridad introducidas o agravadas por `05d02454` frente a su padre.

CHECKED:

- `05d02454` y su delta; árbol de trabajo limpio al inspeccionarlo.
- Generación y resolución de recursos para Claude, Codex y Antigravity en [install_agents.py](/home/david/dev/.engine-v2-wt/F2-H/skill/scripts/install_agents.py:99): el root absoluto sale de `resource_root().resolve()`; Codex respeta las preferencias de modelo existentes y usa `codex_model` cuando no hay una opción nativa ([líneas 108–126](/home/david/dev/.engine-v2-wt/F2-H/skill/scripts/install_agents.py:108)).
- Copia de skills privadas, protección del enlace de Planner y manejo de conflictos/`--force` en [install_agents.py](/home/david/dev/.engine-v2-wt/F2-H/skill/scripts/install_agents.py:195). Los tests inspeccionados cubren archivos escritos en directorios temporales.
- Comportamiento por defecto de Antigravity: Planner en la instalación general; un rol seleccionado, como Designer, se instala con `--agent` ([líneas 244–280](/home/david/dev/.engine-v2-wt/F2-H/skill/scripts/install_agents.py:244)).
- Normalización de rutas en la prueba de paridad: convierte los roots temporales/de recursos conocidos para comparar legacy y wheel; la prueba también verifica el root generado antes de normalizar ([test_entrypoint_parity.py](/home/david/dev/.engine-v2-wt/F2-H/tests/migration/test_entrypoint_parity.py:51)).
- Contratos solicitados: CONTRACT §3 y PROMPT F2 puntos 8–10; contexto de rutas/procedencia en `949823755` y `6a28476fe`.

Brecha: inspeccioné las pruebas, pero no las ejecuté.