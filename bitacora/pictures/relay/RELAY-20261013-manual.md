# Relevo manual · 2026-10-13 ~16:40 (claude-work al 91 %, renueva 19:30)

Continúa el trabajo de la sesión HQ `7bbc8e55` (proyecto `pictures`). Habla con David en español, empieza cada mensaje con `Aye`. Sigue la skill `metodologia`. Lee primero `~/bitacora/pictures/2026-10/W3/2026-10-13.md` (sección `7bbc8e55`), SUMMARY.md y PENDING.md.

## 1. REQ-016 (maratón en curso, el supervisor puede haber muerto)
- `~/bitacora/pictures/requirements/REQ-016-*/` (SPEC, PLAN, RUN.json). Rama de trabajo: worktree `~/dev/pictures-wt/t12`, rama `feat/req-016-guided-3d-edit-leftovers-exact-undo-and`, sin push.
- Estado: T1 hecha (commits 58f10c04 y fe3e9bcb, auditoría M1 PASS). T2 (resolutor de color, guardar el último pedido) estaba en la sesión 8 tras escalar: exige token de aprobación v3 con despliegue en dos etapas (lector antes que escritor). T3 y la auditoría M2 pendientes.
- El supervisor (`bitacora.py --project pictures run REQ-016 --resume`) colgaba de la sesión anterior: comprueba el latido en RUN.json; si está viejo, reábrelo dentro de tmux (`tmux new-session -d -s pictures-REQ-016-marathon ...`) y vigílalo con `bitacora.py --project pictures watch REQ-016` en segundo plano hasta `terminal: true`.
- Reglas: no push, merge, deploy ni llamadas de pago. Cuentas: `pictures` es proyecto de trabajo (claude-work válida). Un cambio manual de RUN.json ya se hizo una vez (verify de T1 y `repo: t12`); no repetir salvo necesidad y anotarlo.

## 2. Skill metodologia (repo `~/dev/metodologia`, SIN commit, ~47 archivos modificados, incluidos cambios previos de David: no tocar ni revertir lo ajeno)
Hecho y verificado (suite de la skill: 526 pruebas, solo 3 fallos previos ajenos: test_platform kitty, test_audit_routing, test_subscription_usage):
- `globalusage` (skill/scripts/globalusage.py, enlace en ~/.local/bin): lectura en vivo, caché 60 s, resalta la sesión actual, usa la última medición guardada si falla.
- Métricas de calidad por defectos (`bt_quality.py`, `task done --findings/--severity`, `defects-YYYY-MM.jsonl`), revisadas por un revisor independiente y corregidas.
- Relevo por cuota para sesiones interactivas (`bt_relay*.py`, references/relay.md): hooks YA instalados en ~/.claude y ~/.claude-work, kitty.conf con control remoto (reiniciar kitty), `relay.enabled=true`, umbral 92 %. Dos rondas de revisión de seguridad aplicadas (80 pruebas del relevo OK).
En curso cuando se escribió esto: un subagente implementador añadía el lanzador padre `relay_run.py` (relevo totalmente automático, también por SSH, sin teclear en paneles; el cliente solo se cierra si su proceso padre es el lanzador). David lo autorizó explícitamente. Mira `git status` en skill/ para ver qué quedó (relay_run.py, cambios en bt_profiles/bt_relay_launch/bt_relay_client, `relay wrap-status`, tests). Si quedó a medias, termínalo según esa descripción; si está completo, haz una revisión independiente de seguridad (reviewer) antes de darlo por bueno. No instales wrappers: regenerarlos con `--apply` es paso de David.

## 3. Pendiente de David / propuestas
- Commit de los cambios de la skill y de la rama t12: decide David.
- Prueba real del relevo en una sesión nueva de kitty.
- Opcional: `usage --force`. P-077 (calibrar tope costeo_idea_hora) sin tocar.
- Los permisos del clasificador bloquean autoediciones (hooks, config relay.*, mensajes a subagentes que crean agentes): usa `!` para que lo ejecute David o pídele una regla de permiso.

## 4. Primer paso sugerido
`python ~/dev/metodologia/skill/scripts/bitacora.py --project pictures watch REQ-016` y `globalusage` para ver cuota; reporta a David en ≤6 líneas.
