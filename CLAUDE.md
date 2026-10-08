# HQ — sala de planificación

Esta carpeta es el HQ de la skill `metodologia`. Aquí se planifica; no se programa.

1. Elige o crea el proyecto (`bitacora.py bind <session_id> <proyecto>`; el session_id viene en el contexto de inicio).
2. Levanta requerimientos por rondas (references/requirements.md), leyendo el código del repo del proyecto (`<proyecto>/project.json`).
3. Escribe SPEC y PLAN; muestra el plan y espera la aprobación del usuario.
4. Aprobado → `PLAN.md status: approved` y `bitacora.py --project <proyecto> launch REQ-NNN` (añade `--agent codex` si lo pide; `--repo <ruta>` la primera vez o si es proyecto nuevo). Eso abre una sesión ejecutora aparte, con permisos completos, en loop.
5. Registra el lanzamiento en el log del día y queda disponible para el siguiente requerimiento.

No edites los repositorios de los proyectos desde aquí.
