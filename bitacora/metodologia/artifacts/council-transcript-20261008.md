# Council transcript — skill metodologia (2026-10-08)

# Council question

**¿Está bien diseñada la skill "metodologia"? ¿Qué le sobra, qué le falta, qué riesgos tiene y qué harías distinto?**

## Who uses it
A solo developer (works at Sempertex + personal projects), Windows 11, several computers, works mostly from the home
folder across many projects. Uses Claude Code (Opus) and Codex. Explicit preferences: maximum agent autonomy
("no quiero limitaciones", "no preguntar cada 5 minutos"), questions only up front, ONE approval gate (the plan),
everything documented, hates giant files, Spanish conversation, code in the repo's language.

## What was built (in one long session, ~1 day) — repo C:\Users\davidt\metodologia (private GitHub monorepo)
- **Always-on skill** (`skill/SKILL.md` ~110 lines, injected every session via CLAUDE.md @import; Codex via hook) +
  references loaded on demand (~1,050 lines total: requirements, execution, engineering + 4 stack guides,
  documentation, tools, subagents, codegraph).
- **Requirements flow**: explore first, prioritized rounds (≤5 questions, recommended answer each), coverage
  checklist, SPEC (EARS, user stories), PLAN, single human gate (plan approval), then autonomous execution.
- **HQ planning room** (~/bitacora): plan there, then `launch` opens a NEW Windows Terminal window with
  `claude --dangerously-skip-permissions` + `/loop` (or `codex --yolo` + `/goal`) and a HANDOFF.md.
- **Bitácora** per project (markdown): day logs per session, week/month rollups, DECISIONS (ADR-lite), PENDING,
  SUMMARY, ARCHITECTURE, TOOLS (servers/hosting access, no secrets), INDEX; local git + auto push/pull to GitHub.
- **Hooks**: SessionStart (context injection, pull), Stop (blocks stopping until the bitácora is updated if files
  changed), SessionEnd (cleanup + commit), PostToolUse (500-line file alert).
- **Local web UI** (Python stdlib server on 127.0.0.1, token-protected forms): dashboard, documents, question
  rounds as forms, plan approval button that launches the executor, Review tab (REPORT.md, per-repo diff,
  one-click merge of all repos), interactive trace graph (Cytoscape).
- **Trace graph** derived from IDs (REQ/US/R/T/D/P + commits citing them), lint for drift, context bundles.
- **Workspaces**: a project = several repos with roles, portable across machines (git remote + hint path).
- **5 subagent roles** (explorer/researcher/implementer/reviewer/runner) installed for Claude + Codex.
- **gitleaks** secret scanning (bitácora commits + pre-commit in project repos); optional CodeGraph MCP.
- **Evals**: 10 real `claude -p` cases in throwaway repos, 10/10 passing (~USD 1.5/run).
- Size: 20 Python scripts (~2,800 lines), web assets, templates; `install.py` sets up any machine.

## Evidence so far
- Already used live by the user's other sessions without supervision: 5 projects in the bitácora (one created
  REQ-004 with 13 requirements not yet covered by tasks — the graph flagged it).
- NEVER tested end to end: HQ → web rounds → approve button → executor window with /loop → REPORT → merge.
  Unverified: /loop as initial prompt, launching Windows Terminal from the background server, Codex /goal.
- Bugs found during the build: several self-inflicted breakages of the live hooks (escaping errors), hooks failing
  under PowerShell for ~20 min, a test commit accidentally made in a real repo (reverted, never pushed),
  console windows flashing. All fixed.

## Deliberate decisions
- No guard hook against destructive commands (user rejected limits); executor runs with permissions bypassed;
  safety = prose rules ("stop and ask for push/deploy/destroying data/credentials") + secret scanning.
- One private monorepo with skill + all project docs (incl. employer projects) on the personal GitHub account.
- Replaced the user's previous tool "hefesto" entirely.
- Documented for later: executor status/notifications/resume, concurrent edits to central files, pruning.

## What's at stake
This is meant to be the user's daily way of working for every project (personal and employer), with agents
running autonomously with full permissions on his machine and servers. A bad design costs time every day, can
lose work or leak data, and an over-engineered one may simply stop being used.

Files you may skim if useful (keep it brief): C:\Users\davidt\metodologia\README.md,
C:\Users\davidt\metodologia\skill\SKILL.md, C:\Users\davidt\metodologia\skill\references\execution.md

---

# Advisor responses (anonymized order; mapping in the reviews section)

**Response A:**
Lo que importa es si esto funciona el lunes a las 9. Hoy no se sabe. La pieza central (HQ → rondas web → botón aprobar → ventana ejecutora con /loop → REPORT → merge) nunca se ha ejecutado completa. Hay 20 scripts, una UI web, un grafo Cytoscape y evals, y el camino principal está sin probar. Eso no es una metodología, es un prototipo con buena documentación.
Qué haría, en orden: 1) Mañana, sin tocar código, un requerimiento real y pequeño de un proyecto personal (no de Sempertex) completo por el flujo HQ; anotar cada falla e intervención: ese es el backlog real. 2) Comprobar que `launch` abre Windows Terminal desde el servidor en segundo plano y que `/loop` arranca como prompt inicial; plan B: el botón copia el comando al portapapeles (10 líneas). 3) Congelar funcionalidades dos semanas. 4) Punto de recuperación barato: que `launch` cree rama + stash/tag antes de empezar — un botón de deshacer, media hora. 5) Sacar los proyectos de Sempertex del GitHub personal hoy (git filter-repo o repo aparte). 6) Stop hook con salida de emergencia (variable de entorno).
Sobra para el día a día: rondas como formularios (el chat ya funciona), merge de todos los repos con un clic (peligroso y sin probar), resumen mensual. Veredicto: el diseño sirve, pero está sin probar.

**Response B:**
El fallo de fondo: toda la seguridad depende de que el modelo obedezca un texto, y eso nunca se ha probado. El ejecutor corre con permisos desactivados en un /loop largo, con TOOLS.md que tiene alias SSH a servidores reales; la única barrera es la lista "stop and ask" en prosa, lo primero que se diluye cuando el contexto se compacta. Los 10 evals cubren el camino feliz; ninguno comprueba que el agente se detiene antes de `git push --force`, `rm` fuera del repo o un `ssh` a producción. La sesión de construcción, supervisada, ya rompió hooks y commiteó en un repo real.
Riesgo laboral: documentos de Sempertex (arquitectura, decisiones, servidores) en un repo de la cuenta personal con push automático; gitleaks detecta secretos, no información confidencial.
Se dio por terminado lo que nunca se ejecutó, y ya sustituyó a hefesto sin vuelta atrás. ~2.800 líneas hechas en un día: ¿quién lo mantiene? Fallos previsibles: conflictos de auto push/pull entre máquinas y ejecutores; el Stop hook puede forzar logs de relleno o quemar tokens en loops desatendidos; REQ con 13 requisitos sin tareas detectado pero nadie actúa.
Haría: un hook mínimo que bloquee solo lo catastrófico (force-push, borrados fuera del repo, deploy a prod) — un cinturón, no un límite; evals adversariales de stop-and-ask; sacar lo del empleador del GitHub personal; congelar features hasta que el flujo completo funcione 5 veces seguidas.

**Response C:**
Lo valioso no es la skill: es el corpus. REQ, decisiones, tareas y commits enlazados por IDs en todos tus proyectos son un registro de cómo decides, hoy usado solo para detectar drift. 1) Usar DECISIONS pasadas para las respuestas recomendadas de las rondas ("en el proyecto X elegiste Postgres por…"): la entrevista se acorta con cada proyecto. 2) Las rondas-formulario como portal de requerimientos para Sempertex: que conteste quien pide (negocio, operaciones); REPORT y grafo como evidencia auditable; resúmenes semanales como informe de estado al jefe; podría volverse el estándar de desarrollo con IA de la empresa. 3) Una flota: varios REQ en paralelo, cada uno en su worktree, con la UI como torre de control. Extra: cada sesión real que termine mal se convierte automáticamente en caso de eval.
Distinto: no sumar infraestructura hasta probar el flujo completo; el lint de trazabilidad debería ser un control (CI / Stop hook), no solo una vista — es lo mejor del sistema.

**Response D:**
Desde fuera alarma: 1) Documentos de proyectos de Sempertex en tu GitHub personal, contado como decisión técnica; parece un incumplimiento de las normas de la empresa, más con TOOLS.md describiendo servidores. 2) La protección contra desastres es un texto "para y pregunta" mientras el agente corre con un flag que dice *dangerously* sobre una máquina con acceso a servidores; con supervisión ya rompiste hooks e hiciste un commit de prueba en un repo real. 3) Todo construido en un día y nunca probado de principio a fin; que los evals pasen 10/10 me hace sospechar que son demasiado fáciles. 4) Jerga incomprensible (HQ, bitácora, REQ/US/R/T/D/P, EARS, HANDOFF, launch): no sé cómo es un martes normal; dentro de tres meses tampoco lo sabrás tú, y un sistema que exige recordar tanto se abandona. 5) Sustituiste hefesto sin plan B. 6) El Stop hook parece una fábrica de bucles o de entradas de relleno.
Haría: sacar los proyectos de la empresa del repo personal hoy; recorrer una vez el flujo completo con un proyecto de juguete; escribir un párrafo de "un día normal" sin siglas; congelar funcionalidades hasta que eso funcione.

**Response E:**
La pregunta de fondo: ¿qué problema resuelve y cuál es lo mínimo que lo resuelve? El usuario quiere tres cosas: no perder contexto entre sesiones y máquinas; que el agente entienda qué construir antes de construirlo; que lo construya solo sin interrumpirlo. Lo construido es un producto de gestión de proyectos completo, hecho en un día, sin probar el ciclo: la fábrica antes de la primera pieza.
Supuesto falso 1: "no quiero limitaciones" ≠ "sin barreras". Odia las interrupciones, no los límites: un hook que bloquea en silencio `rm -rf`, `push --force` o deploy a prod nunca pregunta. Supuesto 2: documentar más ≠ más contexto: el agente necesita SUMMARY, PENDING y DECISIONS; rollups y logs diarios se escriben y nadie los lee, y el Stop hook cobra ese costo cada sesión. Supuesto 3: el gate humano va en el plan — el riesgo real está en el resultado; el merge con un clic sobre todos los repos es la puerta crítica. 4) Documentos del empleador en el GitHub personal: decisión de cumplimiento que nadie tomó.
Haría: una sola métrica (tiempo de la intención a un cambio verificado y mergeado); probar el ciclo completo tres veces con requerimientos reales; recortar lo que no mueva esa métrica (grafo, rollups, formularios web); agregar el hook silencioso contra comandos destructivos.

---

# Peer reviews

Mapping: **A = Executor · B = Contrarian · C = Expansionist · D = Outsider · E = First Principles**

## Review 1
Strongest: **B** — root cause (prose-only safety, diluted by compaction; evals only happy path; no adversarial evals); proportional remedies. Biggest blind spot: **C** — more scope on an untested flow; ignores employer-docs risk and would expose more. All missed: bus factor / tested restore across machines; context & token cost never measured (always-on SKILL.md, Stop hook, unattended /loop); platform dependency (/loop, /goal, hooks may change); no success/abandon criterion; personal data & credentials in the bitácora.

## Review 2 (read E→A)
Strongest: **B** (A close second). Blind spot: **C** (more on an untested flow; corporate exposure). All missed: usage data to know if it's really used; single points of failure and no continuity plan if Claude Code/Codex change; no spend/iteration cap for unattended /loop; executor crash/out-of-context recovery deferred; SSH keys on disk reachable by an unlimited agent (no isolation / least privilege); "move the employer docs out" — but to where (company remote?), nobody says to ask Sempertex.

## Review 3 (lens: respects user's autonomy preference?)
Strongest: **A** — only one that adds no barriers or questions: test the real flow once, undo button (branch/tag in launch), emergency exit for the Stop hook — recovery, not blocking; Sempertex split actionable today. B and E more complete on risk but clash with autonomy. Blind spot: **C** (and D ignores the autonomy preference). All missed: kill switch / rollback for a runaway /loop (cost or token cap); a "silent" blocking hook is still a de-facto interruption — the autonomy-respecting alternative is reversible snapshots/backups, least-privilege credentials and staging servers; measurable success/abandon criteria with a review date; risk policy per environment (personal vs Sempertex) instead of global rules; hooks break live — need hook tests before activation and a safe deploy mode.

## Review 4 (lens: cheap & actionable this week)
Strongest: **A** — ordered, cheap steps (real small requirement end to end; verify launch & /loop with a 10-line clipboard plan B; recovery point; Stop-hook escape). Blind spot: **C** (more infra on an unexecuted flow; treats a risk as an asset — though "lint as a control" is useful). All missed: recurring cost (always-on context, Stop hook, unattended loop tokens) and no spend/iteration cap; no stuck/rollback criterion for the loop; no exit plan (hefesto replaced without fallback); no dated keep/trim/abandon decision; no quality criterion for evals (no concrete adversarial case).

## Review 5 (lens: long-term sustainability)
Strongest: **E** — starts from the real problem (3 needs), separates "no interruptions" from "no barriers", notes rollups/daily logs are written but not read while the Stop hook charges every session; one metric and concrete cuts. D second (abandonment via jargon, "a normal Tuesday"). Blind spot: **C** (adds more; ignores abandonment and context cost; amplifies compliance risk). A ignores security and context cost. All missed: per-session context budget / on-demand loading; degraded mode if the web server / Python / hook fails (documented kill switch); a maintenance owner for Claude Code/Codex changes; a one-week "minimal mode" trial (SUMMARY/PENDING/DECISIONS only) before deciding what to keep; concurrent multi-machine writes to central files.

## Tally
Strongest: B ×2, A ×2, E ×1. Biggest blind spot: C ×5 (unanimous).

---

# Chairman synthesis

See council-report-20261008.html (full verdict reproduced there).
