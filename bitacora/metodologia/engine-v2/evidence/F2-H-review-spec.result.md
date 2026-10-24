## AXIS

spec

## VERDICT

CHANGES_NEEDED — no encontré incumplimientos demostrables en el diff, pero no pude validar el brief requerido: `F2-H.brief.md` no aparece en las ubicaciones disponibles. Según el criterio de revisión, esa brecha impide aprobar.

## FINDINGS

Ninguno demostrado.

## CHECKED

- Comparé `05d02454` con su padre `6a28476fe`; revisé además los cambios pertinentes de `949823755` y `6a28476fe`.
- Revisé los ocho prompts fuente, selección de modelo de Designer, carga condicional de skills, resolución de recursos para los tres proveedores y protección de archivos generados y escritos a mano.
- Las pruebas estáticas comprueban las rutas en los prompts fuente (`body`), además de las generadas; el inventario inyectado no puede ocultar referencias faltantes. Las 9 pruebas de `test_agent_skills_static` pasaron.
- La prueba de paridad normaliza la raíz de recursos en todos los archivos generados. No observé evidencia de que esta normalización oculte una deriva actual ajena a esa ruta.
- `git diff --check` pasó. No ejecuté la suite de migración ni instalé roles en perfiles reales; la instalación real queda fuera del alcance indicado.
- **Brecha:** no encontré `F2-H.brief.md`; por eso no pude contrastar criterios que dependan exclusivamente de ese documento.