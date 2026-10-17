# metodologia

Mi forma de trabajar con IA, empaquetada como skill para **Claude Code** y **Codex**, con Planner disponible también
en **Antigravity**:

- **Requerimientos por rondas** → spec → plan → **una sola aprobación** → ejecutor autónomo (`/loop` en Claude,
  `/goal` en Codex) en una ventana aparte.
- **Flujo automático**: el agente dimensiona el requerimiento, lo planifica en hitos y `handoff` lo lanza en
  segundo plano (aprobándolo solo si no hay motivos de riesgo): **una sesión limpia por hito**, cada hito cerrado por
  una **auditoría independiente** de otro agente.
- **Varios agentes y suscripciones**: Claude (Haiku, Sonnet, Opus 5.5) y Codex (GPT-6 Luna, GPT-6.1 Sol) en una sola
  escalera de capacidad; el enrutador elige cuenta, modelo y esfuerzo por tipo de trabajo, cuotas y resultados
  medidos, y cualquier agente puede delegar en cualquier otro. Detalle: `skill/references/agents.md`.
- **Telemetría y aprendizaje**: cada intento queda medido por agente, modelo y esfuerzo; lo aprendido sobre el
  proyecto y tus preferencias se guarda con evidencia y se inyecta en las sesiones siguientes.
- **Estándares de ingeniería** (responsabilidad única, features, Atomic Design, alerta de 500 líneas, tests
  pragmáticos, stacks por defecto) y **7 agentes**: Planner más explorer, researcher, implementer, reviewer, runner y
  antagonist. Planner está disponible en Claude Code, Codex y Antigravity; los perfiles configurados de Claude y Codex
  reciben su propia instalación.
- **Calidad de interfaces y revisiones con evidencia**: dirección visual explícita, contenido real y cobertura
  de interacción; revisión del impacto en consumidores y simplificaciones concretas. Adaptaciones selectivas de
  Antislop y Thermos, integradas en el flujo existente, sin dependencias ni nuevas puertas de aprobación.
  Detalle: `skill/references/interface-quality.md` y `skill/references/subagents.md`.
- **Uso real por suscripción, sin agentes**: `bitacora.py usage poll` consulta ventanas de 5 horas y semana;
  `usage show` muestra muestras y errores. En Linux, `usage install-timer` activa la consulta horaria con systemd
  de usuario. El router favorece cuentas con más margen, conserva las restricciones del proyecto y usa datos
  locales al decidir. Credenciales caducadas o datos antiguos nunca se presentan como uso cero.
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

Compatible con Windows, Linux y macOS (Python 3.12+). En Linux, el lanzador busca
kitty, GNOME Terminal, Konsole, xterm o x-terminal-emulator. En macOS usa Terminal
mediante `osascript`; el sistema puede pedir permiso para automatizar Terminal.
Sin terminal gráfica se puede ejecutar el supervisor directamente con `bitacora.py run`.

La reanudación después de iniciar sesión utiliza systemd de usuario en Linux
(sin sudo), XDG Autostart si no hay systemd, LaunchAgents en macOS y Startup en Windows.
Los compositores que no procesen XDG Autostart necesitan un gestor de sesión compatible
o ejecutar `run --resume` manualmente. `--no-autostart` desactiva el registro.
Las notificaciones usan notify-send en Linux, osascript en macOS y WinRT en Windows.
No hay cambios de configuración ni servicios hasta ejecutar el instalador o iniciar un maratón.

| | Para qué | ¿Obligatorio? |
|---|---|---|
| **Git** | clonar y sincronizar | sí |
| **Python 3.12+** | los scripts de la skill (solo librería estándar) | sí |
| **Sesión de GitHub** con la cuenta `dav033` (`gh auth login` o el login de Git) | el repo es privado | sí |
| **Claude Code** y/o **Codex** | los agentes | al menos uno |
| **winget** (viene con Windows 11) | instalar gitleaks (escaneo de secretos) | opcional |
| **npm** | instalar CodeGraph (grafo de código para el explorer) | opcional |
| **RTK** | comprimir salida de comandos para la skill madre | opcional; `python install.py --rtk-only` en Linux x86_64 |

Para gitleaks: `brew install gitleaks` en macOS; el gestor de paquetes de la
distribución en Linux (`pacman -S gitleaks` en Arch, requiere permisos de administrador).
El instalador sólo intenta instalarlo automáticamente en Windows. Si está instalado
pero no puede completar el escaneo, el commit queda bloqueado; si no está instalado,
se conserva el comportamiento anterior de escaneo opcional.

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
| Correr un plan aprobado por días (maratón: una sesión limpia por tarea, Haiku 5.5 + ultracode) | Aprobar con **Modo: Maratón** en el panel · `bitacora.py --project <p> launch REQ-001 --mode marathon` · reanudar tras reiniciar: `bitacora.py --project <p> run REQ-001 --resume` |
| Lanzar un plan sin más conversación (valida, aprueba si es seguro, corre por hitos con el mejor agente) | `bitacora.py --project <p> handoff REQ-001` (`--dry-run` para ver la decisión) |
| Ver agentes, cuentas y cuotas · qué ruta se usaría | `bitacora.py agents` · `bitacora.py --project <p> agents route --kind audit` |
| Delegar una tarea a otro agente o suscripción | `bitacora.py --project <p> delegate start "<tarea>" --kind test --verify "<cmd>"` |
| Comparar agentes, modelos y esfuerzo con datos | Panel → **Métricas de agentes** · `bitacora.py metrics --by kind,agent,model,effort` · `bitacora.py metrics --advice` |
| Ver o confirmar lo aprendido | `bitacora.py --project <p> learn list` · `learn confirm L-003` · `learn reject L-003` |
| Dar a un agente todo el contexto en una pantalla | `bitacora.py --project <p> context` |
| Ajustes de la máquina (aprobación automática, auditorías, pool de cuentas) | `bitacora.py config get` · `config set audit.mode off` |
| Pausar, reanudar o detener un maratón | Pestaña **Maratón** del requerimiento · `bitacora.py --project <p> run-control REQ-001 pause\|resume\|stop` |
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

## RTK dentro de la skill madre

Caveman y Grill Me aportan instrucciones adaptadas dentro de `metodologia`; no se instalan como otras skills.
RTK es el ejecutable opcional para reducir la salida de comandos, con instalación y pautas propias de este repo:

```bash
python install.py --rtk-only
```

Instala RTK **0.51.0** en `~/.local/bin/rtk`, con SHA-256 fijados para el archivo y el binario, sin sudo,
hooks ni cambios de configuración. Esta versión del instalador soporta Linux x86_64; otras plataformas
necesitan un paquete oficial. Conserva cualquier binario distinto que ya exista y avisa del conflicto.
La ruta debe estar en PATH (`fish_add_path ~/.local/bin` en fish, si hace falta).
Para incluir RTK al configurar deliberadamente todo el marco: `python install.py --with-rtk`.

La medición local con tres repeticiones por comando observó un 27,5 % menos tokens de salida para `git status`,
64,7 % para `git log -n 20`, 0,4 % para un diff pequeño y 96,4–99,8 % para pytest verboso.
Con pytest ya silencioso (`-q`), la reducción fue 33,8 %. Se conservaron códigos y los tres diagnósticos.
Recuperar la salida completa de un fallo elevó el total 1,8 % frente a pytest nativo. Son tokens de **salida de
comandos**, contados con `o200k_base`; no son ahorro total de sesión ni de facturación. RTK añadió 3–7 ms a las
consultas Git de esta muestra; mide también el tiempo si importa.

Benchmark reproducible, sin modelos de pago ni ejecutar suites de tus proyectos:

```bash
uv run --no-project --with pytest --with tiktoken python evals/benchmark_rtk.py --output /tmp/metodologia-rtk-bench-1
```

Guarda los resultados y la salida original, compara Git en este repo y ejecuta un fixture aislado de pytest.
Valida el SHA-256 del binario RTK v0.51.0, el código de recuperación, los diagnósticos recuperados y que pytest
no vuelva a ejecutarse. Usa un directorio nuevo y vacío por corrida; rechaza sobrescribir evidencia.
La skill elige filtros explícitos y recupera evidencia existente; la instalación no activa interceptación automática.

## Comprobaciones de portabilidad

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v
```

Las pruebas aíslan los archivos y sustituyen los agentes por stubs; no consumen modelos.
La matriz de CI incluye Linux y macOS. Las pruebas de macOS comprueban comandos y plist;
la automatización gráfica y los permisos de Terminal necesitan una prueba manual en Mac.
El instalador y el flujo de sincronización mantienen sus políticas de commits/push
automáticos: revisarlas antes de activar la skill si tus reglas locales los prohíben.

Referencias: [LaunchAgents de Apple](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html),
[formato de entradas XDG](https://specifications.freedesktop.org/desktop-entry/latest-single/).
