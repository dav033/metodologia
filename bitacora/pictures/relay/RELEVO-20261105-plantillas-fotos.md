Continúa el trabajo de plantillas de cumpleaños desde fotos en Pictures. Responde en español.

Repo: `~/dev/pictures-wt/pilot`, rama `integ/req-021-pilot`, igual a `main` en `dd42c5c52`. Producción: https://demo-decoracion.vercel.app (Vercel despliega al hacer push a `main`).
Lee primero: `~/bitacora/pictures/2026-11/W2/2026-11-05.md` (últimas secciones), `~/bitacora/pictures/PENDING.md` (P-237 a P-242) y D-098 en `~/bitacora/pictures/DECISIONS.md`.

Estado:
- 13 plantillas en producción, subcategoría «Fotos de referencia»: 6 infantiles (`Downloads/1`) y 7 de adulto (`Downloads/2`). Todas con `recipe.estructuras`, seleccionables en el chat. Ids de las de adulto en `~/dev/pictures-infra/plantillas/fotos-cumple/ids-plantillas.json`.
- La meta de 80/100 NO se alcanzó. Última nota de 2 jueces: infantiles 58 a 72,5 (Sonnet); adulto 57,7 a 71 (Terra, no comparable). Lo más bajo: materiales y luz (39-41 %) y sala (52-54 %). Más ajustes a recetas ya no parecen dar el salto.
- Etiquetado del pool hecho: 268 ítems con confianza baja esperan revisión humana (P-239).

Trabajo en curso al escribir esto:
- Experimento de render fotográfico con Blender Cycles en CPU, sin tocar recetas ni producción. Delegación D-20261105-083904-ae6e (Terra medium, codex-2), worktree ~/dev/pictures-wt/cf3-cycles, rama cf3/cycles, encargo y salida en /home/david/.local/tmp/claude-1000/-home-david-dev-pictures-wt-pilot/6f27eab5-f22b-40d9-ab6c-863c6a8188ec/scratchpad/cf/cycles/ (BRIEF.md, lado-arcoiris-osito.png, lado-arco-negro.png).
- Primero: `python ~/.claude/skills/metodologia/scripts/bitacora.py --project pictures delegate status D-20261105-083904-ae6e`. Si sigue corriendo, espérala; no la relances. Mira tú las imágenes: `verified` solo dice que los archivos existen.
- Si se ve claramente más fotográfico: pásalo por 2 jueces con RUBRICA.md sobre las mismas 2 plantillas (antes 72,5 y 70). Si sube a 80, propón a David usar esas imágenes como miniatura e imagen guardada del chat; el Taller en vivo seguiría con su render, y hay que decírselo. Ocurre fuera del navegador, así que no sirve para colores cambiados en vivo. Si no sube, díselo con las notas y deja la decisión en él.

Pendiente de David:
1. Decidir si invierte en un render más fotográfico o acepta las plantillas (P-237, P-242). Si acepta, cierra el objetivo con `/goal clear`.
2. Confirmar las categorías que eligió el agente: niña, niño y hombre.
3. Dar acceso con `davidt@sempertex.com` para comprobar las plantillas en producción con sesión (P-240).

Reglas que aplican:
- Subagentes: Codex `gpt-6.1-terra` medium repartido entre `codex-1`, `codex-2`, `codex-luis`, y Sonnet solo en `claude-personal`, con `bitacora.py --project pictures delegate start`. Terra para pronto: dale listas exactas y mira el resultado.
- No correr pruebas ni antes de publicar, salvo que David lo pida; comprobar en la app. `tsc` sí, y que un fallo detenga el push.
- D-098: ninguna plantilla base se da por terminada sin estructuras comprobadas en `/asistente`.
- Una sola sesión escribe en producción: comprueba otras sesiones vivas con ListAgents antes de publicar o guardar, y si hay alguna, acuérdalo con ella.
- La base local y la de producción son la misma: guardar una plantilla la publica. Actualiza plantillas con `publicar.cjs <slug> <ronda>`, que conserva el id; requiere `:3010` encendido.
- `:3010` lo sostiene una tarea de otra sesión y puede caer. Para levantarlo: desde `pilot`, carga `/home/david/dev/pictures/.env.local` y `~/.config/metodologia/{pictures-db,pictures-local-ai,pictures-almacen}.env`, exporta `DATABASE_URL` y `CATALOG_DATABASE_URL` con `PICTURES_DB_APP_URL`, `RAG_PYTHON_QUERY_EMBEDDINGS_ENABLED=false`, `AUTH_LOCAL_SIN_RESTRICCIONES=1`, quita `DB_GATEWAY_URL` y `DB_GATEWAY_KEY`, y corre `node scripts/next-with-system-ca.cjs dev --port 3010 --hostname 127.0.0.1`.

Herramientas, recetas y jueces: `/home/david/.local/tmp/claude-1000/-home-david-dev-pictures-wt-pilot/6f27eab5-f22b-40d9-ab6c-863c6a8188ec/scratchpad/cf/` (`rerender2.sh`, `camaras2.json`, `revisar_globos.ts`, `RUBRICA.md`, `juicios/`, `estructuras-*.json`); las recetas están en `~/dev/pictures-infra/plantillas/fotos-cumple/`. Es una carpeta temporal: copia lo que necesites conservar.

Marcha atrás: `demo-decoracion-c3r9hkgh9` para el código anterior al último cambio; backups en el VPS `/root/backups/pictures/pictures-before-estructuras-fotos-20261105T131620Z.dump`. No guardes secretos en ningún archivo.
