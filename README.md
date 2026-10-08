# metodologia

Mi forma de trabajar con IA, empaquetada como skill para **Claude Code** y **Codex**:

- **Requerimientos por rondas** → spec → plan → **una sola aprobación** → ejecutor autónomo (`/loop` en Claude,
  `/goal` en Codex) en una ventana aparte.
- **Estándares de ingeniería** (responsabilidad única, features, Atomic Design, alerta de 500 líneas, tests
  pragmáticos, stacks por defecto) y **5 subagentes** (explorer, researcher, implementer, reviewer, runner).
- **Bitácora** por proyecto (`bitacora/`): logs por día y sesión, DECISIONS, PENDING, SUMMARY, ARCHITECTURE,
  TOOLS; sincronizada entre computadoras.
- **Panel web local**: proyectos, documentos, rondas como formulario, aprobación del plan, revisión y fusión, y el
  **grafo de trazabilidad**.

```
metodologia/
  skill/      la skill (SKILL.md, references/, templates/, scripts/, agents/, assets/)
  bitacora/   la documentación de todos los proyectos
  evals/      casos de prueba de la skill
  install.py  configura una computadora
```

---

## Instalar en una computadora nueva

### Requisitos

| | Para qué | ¿Obligatorio? |
|---|---|---|
| **Git** | clonar y sincronizar | sí |
| **Python 3.12+** | los scripts de la skill (solo librería estándar) | sí |
| **Sesión de GitHub** con la cuenta `dav033` (`gh auth login` o el login de Git) | el repo es privado | sí |
| **Claude Code** y/o **Codex** | los agentes | al menos uno |
| **winget** (viene con Windows 11) | instalar gitleaks (escaneo de secretos) | opcional |
| **npm** | instalar CodeGraph (grafo de código para el explorer) | opcional |

### Pasos

```
git clone https://github.com/dav033/metodologia ~/metodologia
python ~/metodologia/install.py
```

Después, **en Codex**, aprueba los hooks una vez: abre `codex` y escribe `/hooks`.
Si tenías sesiones de Claude Code o Codex abiertas, reinícialas.

Eso es todo. `install.py` se puede correr las veces que quieras: lo que ya está bien lo deja igual.

---

## Qué hace `install.py`

| Paso | Qué hace |
|---|---|
| **1. Accesos directos** | Crea `~/.claude/skills/metodologia` y `~/.agents/skills/metodologia` → `skill/` (Claude y Codex encuentran la skill) y `~/bitacora` → `bitacora/`. Si alguna ruta ya existe como **carpeta real**, se detiene sin tocar nada y avisa. |
| **2. Hooks** | Agrega a `~/.claude/settings.json` y `~/.codex/hooks.json` los hooks de inicio, cierre (recordatorio de documentar), fin de sesión y aviso de archivos de más de 500 líneas, con las rutas de esa máquina. Conserva tus otros hooks y ajustes. |
| **3. Siempre activa** | Agrega a `~/.claude/CLAUDE.md` el import de `SKILL.md` y a `~/.codex/AGENTS.md` la indicación de usar la skill. No duplica si ya están. |
| **4. Subagentes** | Instala los 5 roles en `~/.claude/agents/` y `~/.codex/agents/` desde `skill/agents/`. |
| **5. Workspaces** | Busca en esa computadora dónde están clonados los repos de cada proyecto (por su URL de GitHub) e informa cuáles faltan. No clona nada todavía. |
| **6. Secretos** | Instala gitleaks si falta (winget) y pone un hook de pre-commit con gitleaks en cada repo de los workspaces (no toca repos que ya tienen su propio hook). |
| **7. CodeGraph** *(opcional)* | Si hay npm, instala CodeGraph globalmente. Registrarlo como MCP es manual: ver `skill/references/codegraph.md`. |

**No hace:** borrar nada, tocar el código de tus proyectos (el hook de pre-commit vive en `.git`, no se versiona),
hacer push, ni aprobar los hooks de Codex por ti.

---

## Uso diario

| Quiero… | Cómo |
|---|---|
| Planificar (sala de planificación / HQ) | Abre `claude` o `codex` en `~/bitacora` |
| Trabajar en un proyecto | Abre la sesión donde siempre (tu carpeta personal, el workspace o el repo): la sesión detecta el proyecto sola |
| Ver el panel | "abre el panel" · `python ~/.claude/skills/metodologia/scripts/bitacora.py web` |
| Ver el grafo | "muéstrame el grafo" · `bitacora.py --project <p> graph` |
| Saber en qué estamos | "¿en qué estamos?" |
| Registrar un proyecto de varios repos | `bitacora.py --project <p> workspace add <rol> <ruta>` |
| Clonar en esta máquina los repos que falten | `bitacora.py --project <p> workspace clone` |
| Revisar la trazabilidad | `bitacora.py --project <p> trace` |
| Correr las evaluaciones de la skill | `python ~/metodologia/evals/run.py` (≈ USD 1.5, tope configurable) |

La bitácora se sincroniza sola: baja lo último al iniciar cada sesión y sube cada cambio en segundo plano.
Los cambios a la skill misma son commits normales en este repo.

---

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| La sesión no muestra el bloque `[bitácora]` al iniciar | Corre `python ~/metodologia/install.py` de nuevo y reinicia la sesión |
| En Codex no corren los hooks | `/hooks` dentro de Codex y apruébalos (también tras actualizar la skill) |
| Aviso "bitácora sync failed" | Sin internet o conflicto: no se pierde nada local; se reintenta en la próxima sesión. Si persiste: `git -C ~/metodologia status` |
| Aviso de **posible secreto** en la bitácora | Reemplaza el valor por una referencia (ruta de la llave, nombre de variable, alias SSH) y corre `bitacora.py commit "fix: remove secret"` |
| Un commit de tus repos bloqueado por gitleaks | Quita el secreto del código; si es falso positivo, agrégalo a `.gitleaksignore` |
| El panel no abre | `bitacora.py web` lo levanta (puerto 8765); se reinicia solo si su código cambió |
