# REQ-014 verification (2026-10-14, HEAD d14d429b, read-only audits)

Totals over 59 tasks: DONE 9 · PARTIAL 31 · MISSING 8 · N/A 11. Existence is not acceptance: PARTIAL = implemented under other names/paths but the task's named test or artifact is absent. T50 (P-017) is covered in practice by `test-foil-visor.ts` (6/6, wired as globos3d:test-foil-visor); the named `test-foil-script-dorado.ts` does not exist. Repo `demo-decoracion` and branches feat/req-014-* do not exist here; commit d2590cd4 absent (T1).

## T1-T20
# REQ-014 — auditoría de tareas T1–T20 (solo lectura)

Repo: /home/david/dev/pictures · HEAD d14d429b (feat/req-015-judge-fix) · Plan: /home/david/bitacora/pictures/requirements/REQ-014-72h-marathon-autonomous-product-developm/PLAN.md

Contexto: no existe la rama `feat/req-014-…` ni `feat/guiada-motor-ediciones`, `feat/escenarios-matriz`, `feat/bb-rapidos`, `feat/ia-local-claude` (ni local ni remota). El commit `d2590cd4` no existe en este repo. El trabajo de Fase 5 está en `d05a52b8` (ancestro de HEAD).

| Task | Verdict | Evidence | What's missing |
|---|---|---|---|
| T1 REQ-007 Phase 5 merge | PARTIAL | `git merge-base --is-ancestor d2590cd4 HEAD` falla (hash inexistente). Fase 5 presente en HEAD vía `d05a52b8` (ancestro). `scripts/test/_explora-ediciones.ts` no existe en ningún commit. `scripts/test/test-motor-guiada.ts` rc=0 («ok») | Verify literal no cumple (ancestría); no hay merge de la rama de origen |
| T2 pure edit ops | DONE | `scripts/test/test-motor-guiada-ediciones.ts` ejecutado: 23/23 pass, rc=0 | — |
| T3 mapping table | DONE | `src/lib/globos3d/motor/edicion-desde-pedido.ts:29` («No pude: …»); `scripts/test/test-motor-guiada-ediciones-mapeo.ts` ejecutado: 8/8 pass | — |
| T4 POST /editar | DONE | `src/app/api/guiada/motor/editar/route.ts:39` (`export const POST`); `scripts/test/test-motor-guiada-editar-ruta.ts` ejecutado: 15/15 pass; `d05a52b8` | Gate «solo con GUIADA_MOTOR=3d» no verificado por separado |
| T5 client design + contrato | PARTIAL | `src/lib/guiada-motor/editar-contrato.ts:14,21,29` (RUTA_EDITAR_MOTOR, CuerpoEditarMotor, CODIGOS_FALLO_EDITAR) | No existe `/home/david/bitacora/pictures/requirements/REQ-007-*/FASE5-INTEGRACION.md` (carpeta: PLAN-v3, DOSSIER-SWITCH, PARIDAD-*, PRECIO-UNICO…); falta `scripts/test/test-motor-guiada-ediciones-contrato.ts` |
| T6 guardia prerender | DONE | `scripts/test/test-guardia-prerender.ts` ejecutado: rc=0 (24 violaciones en fixture; 297 componentes cliente y 38 de servidor sin hallazgos); commits `53502782`, `082a34fb` | — |
| T7 customer UI wiring | PARTIAL | Componentes: `src/components/guiado/ajuste/usarAjustePlanGuiado.ts`, `src/components/guiado/ajuste/edicion-chat-guiada.ts` (el plan dice edicion-chat-3d, no existe), `src/components/guiado/ModificarPieza.tsx`, `src/components/guiado/TarjetaPlan.tsx` | `scripts/test/test-ui-plan-motor3d.ts` solo tiene casos «Deshacer» (REQ-016, líneas ~95–112); sin casos de tamano_pieza/tamano_globos, proporcion_color ni edición por /motor/editar |
| T8 PM review decorator | N/A | Tarea de proceso (PM). `research/pm/BACKLOG.md` no contiene «REQ-014 T8» | Ejecutar la revisión (no es verificable por código) |
| T9 regression sweep | DONE | Ejecutados, todos rc=0: test-guardia-proveedores-ia («PASS»), test-proxy-matcher («OK»), test-motor-guiada-golden (46 casos), test-motor3d-svg, test-esquema-gemini (6 ok) | Justificación de diffs de golden no revisada |
| T10 feedback UI | PARTIAL | Fixes: `51129697` (nota guardada al recargar, sin ráfaga), `90e8f369`. `test-feedback-ia-ui.ts` 31/31 OK (montar no envía nada, líneas ~403–408); `test-feedback-ia-componentes.ts` 25/25 OK | No encontré aserción de «nota de 1–10 guardada visible tras recargar»; no hay evidencia de assertions failing-first |
| T11 columna_asimetrica densidad | PARTIAL | `53502782` (columna densa por defecto); `src/lib/globos3d/motor/constructores-organicos.ts:74`; `src/lib/globos3d/motor/espec-a-escena.ts:43`; `scripts/test/test-columna-asimetrica-densa.ts` OK (23,3 globos/m, banda 20–26) | Falta `scripts/test/test-columna-asimetrica-densidad.ts` (nombre del verify); regeneración de fixtures con motivo no evidenciada |
| T12 library data 29–31 | MISSING | `src/lib/biblioteca-sempertex/planes-ideas.json`: `deco-real-31-arco-futbol-balones-gigantes` sigue con estructura `semiarco`; 29 y 30 siguen con `columna`. Script `scripts/biblioteca/precomputar-planes-ideas.ts` existe. Sin commit que toque las ideas 29–31 | `scripts/test/test-planes-ideas-29-31.ts` no existe; corrección de datos no evidenciada |
| T13 generador de escenarios | PARTIAL | `scripts/escenarios/generador.ts` (124 líneas; `escenarioDe` :109, semilla vía `./azar.ts`); `15c74eb7` | Falta `scripts/test/test-escenarios-generador.ts`. Rango de colores en código `COLORES_MIN=1`, `COLORES_MAX=6` (:20–21) vs. 1–8 pedido en el plan. No existe rama `feat/escenarios-matriz` |
| T14 Ship #1 | N/A | Depende de push autorizado por el dueño y de la rama `feat/req-014-…` (inexistente) | — |
| T15 invariantes | PARTIAL | `scripts/escenarios/invariantes.ts` (151 líneas): `INVARIANTES` :13 (no_lanza, banda_conteo, sin_solapes, dentro_sala, determinismo, tiempo, avisos_honestos); `evaluar` :140 | Falta `scripts/test/test-escenarios-invariantes.ts` (fixtures malas) |
| T16 proveedor Claude local | PARTIAL | `src/lib/ia/nucleo/registro.ts:23,59,95` (claude solo si `claudeLocalPermitido`); `src/lib/ia/claude/config.ts:19` (MODELO por defecto claude-haiku-5-5), `:43` (IA_LOCAL_ESFUERZO); commits `8c397842`, `a8247ecc`; `scripts/test/test-proveedor-claude-local.ts` existe | ADR `research/w5-anthropic/ADR-proveedor-claude.md` no existe (solo NOTES.md); falta `scripts/test/test-proveedor-local.ts` (el existente tiene otro nombre); rechazo en prod/Vercel no verificado |
| T17 ADR repositorios REQ-013 | PARTIAL | `requirements/REQ-013-catalogue-repositories/SPEC.md` y `PLAN.md` existen; SPEC cubre repositorio, sempertex, mobiliario, escenografia, manifest, acierto@5; PLAN tiene 29 líneas «verify:» | Ni SPEC ni PLAN contienen «033» (exigido por el verify). Conflicto de numeración: `scripts/migrations/033_proveedor_anthropic.sql` ya ocupa el 033 |
| T18 PM review customer | N/A | Tarea de proceso (PM). Sin «REQ-014 T18» en `research/pm/BACKLOG.md` | Ejecutar la revisión |
| T19 runner de escenarios | PARTIAL | `scripts/escenarios/correr.ts` (126 líneas) | Falta `scripts/test/test-escenarios-humo.ts` |
| T20 adaptador de herramientas | DONE | `scripts/test/test-herramientas-anthropic.ts` ejecutado: 8 pruebas ok, rc=0; `src/lib/ia/claude/herramientas.ts`; commits `8c397842`, `a8247ecc` | Aserciones concretas (nombres vs DECLARACIONES_ESCENA) no leídas línea a línea |

Totales: DONE 6 (T2, T3, T4, T6, T9, T20) · PARTIAL 10 (T1, T5, T7, T10, T11, T13, T15, T16, T17, T19) · MISSING 1 (T12) · N/A 3 (T8, T14, T18).

## T21-T40
# REQ-014 — auditoría de T21…T40 (solo lectura)

Repo auditado: /home/david/dev/pictures, HEAD d14d429b (feat/req-015-judge-fix). El PLAN usa `repo: demo-decoracion` (worktree Windows `C:/Users/davidt/...`), que no existe en esta máquina (`~/dev/pictures-wt/t7` ausente); las rutas del PLAN se comparan con las de este checkout.

| Task | Verdict | Evidence | What's missing |
|---|---|---|---|
| T21 Claude ChatPort | PARTIAL | src/lib/ia/claude/chat.ts, cuerpo.ts, sse.ts, precios.ts (haiku-5-5), config.ts:43 (IA_LOCAL_ESFUERZO); envoltorios src/lib/registro/envoltorios-anthropic.ts; commits 8c397842, a8247ecc; guardia test-guardia-proveedores-ia.ts:69 (anthropic-chatport, detector de create/stream) | scripts/test/test-chat-claude.ts no existe (verify falla en su primer comando) |
| T22 Scenario sweep #1 | MISSING | scripts/escenarios/correr.ts (--n 2000 por defecto, commit 15c74eb7) | research/escenarios/PASS-RATE.md y FALLOS-*.md no existen; no hay fila «REQ-014 T22»; no hay tareas nuevas de origin T22 en PLAN |
| T23 Repositorio abstraction | PARTIAL | src/lib/catalogo/repositorio.ts, src/lib/catalogo/repositorios/{sempertex,mobiliario,escenografia}/manifiesto.ts + lock.json, src/lib/catalogo/ids.ts; commit 6a760e21 | src/lib/repositorios/ no existe (ruta distinta); scripts/test/test-repositorios-registro.ts no existe (hay test-catalogo-repositorios.ts, no nombrado) |
| T24 Migración 033 repositorio | MISSING | scripts/migrations/034_catalogo_repositorios.sql:21 (ADD COLUMN IF NOT EXISTS repositorio DEFAULT 'sempertex', commit d4b4020d, «migración 034 aplicada»); 033 ya es scripts/migrations/033_proveedor_anthropic.sql | El número 033 está tomado; el cambio ya se aplicó como 034 (contra lo que pide «NOT applied»). scripts/test/test-migracion-033.ts no existe |
| T25 BalloonBuilder inflado | PARTIAL | «segundos de bomba»: src/lib/globos3d/bomba-segundos.ts, src/components/tres-d/SeccionBomba.tsx, scripts/test/test-bomba-segundos.ts (commits e7109cc8, 21ba148c) | src/lib/globos3d/inflado.ts no existe; no tabla «inflar a N cm» por capa; scripts/test/test-inflado-capas.ts no existe |
| T26 Completeness critic | N/A | Tarea de proceso (crítica y tareas nuevas en PLAN) | research/pm/BACKLOG.md no contiene heading «REQ-014 T26» (grep sin resultados) |
| T27 Cotas de medidas | PARTIAL | src/components/tres-d/EtiquetasMedidas.tsx, src/lib/globos3d/medidas-caja.ts (medidasDePieza, textoMetros), scripts/test/test-medidas-caja.ts (commit e7109cc8, PRO-13) | scripts/test/test-cotas-medidas.ts no existe; toggle de overlay no verificado |
| T28 Helio y cinta en BOM | PARTIAL | src/components/tres-d/SeccionHelio.tsx, HojaArmadoHelio.tsx, ListaCompra.tsx; scripts/test/test-helio-cinta.ts, test-helio-cobertura.ts (commits e7109cc8, df620c43) | motor/bom.ts no existe; scripts/test/test-bom-helio-cinta.ts no existe; ft³/litros por tamaño no verificados |
| T29 Receta por idea | PARTIAL | src/components/tres-d/TarjetaReceta.tsx, SelectorPerfilTamano.tsx, PanelOrganico.test.ts (commit c69e307b, «receta por idea») | scripts/test/test-receta-ideas.ts no existe; «toda idea tiene receta y su total = plan» no verificado; chips de ocasión/técnica no verificados |
| T30 Property tests armarEscena | MISSING | scripts/test/test-propiedades-motor.ts (semillas, motor 3D de la vista guiada, commit d9a9a6b5) no referencia armarEscena (grep) | scripts/test/test-propiedades-armar-escena.ts no existe; sin 300 casos sobre armarEscena |
| T31 Ship #2 | N/A | Acción de push (autorizada por la política de deploy del SPEC) | Rama feat/req-014-72h-marathon-autonomous-product-developm no existe local ni remota (git branch -a); el verify no puede pasar aquí |
| T32 PM review (decorator) | N/A | Tarea de proceso | research/pm/BACKLOG.md sin heading «REQ-014 T32» |
| T33 Agente de escena en Claude | PARTIAL | src/app/api/escena-ia/route.ts:3,112-117 (usa destinoGenerativo; Claude solo en local, sin resolverProveedor); src/lib/globos3d/modelo-escena/sesion-claude.ts (guardia anthropic-escena-ia) | scripts/test/test-agente-escena-claude.ts no existe; «resolver» tal como pide el PLAN no se usa (se documenta como decisión distinta) |
| T34 Lectura de foto en Claude | PARTIAL | src/lib/globos3d/leer-foto-ia.ts:185 (destinoGenerativo), src/lib/ia/claude/como-gemini.ts; scripts/test/test-lectura-foto.ts existe | scripts/test/test-lectura-foto-claude.ts no existe; bloques de imagen JPEG del normalizar-foto y fixture no verificados |
| T35 Inventario de fotos | PARTIAL | scripts/entrenamiento/arnes.ts:118 (lista images (25)…(54).jpg desde --fotos, por defecto C:/Users/davidt/Downloads/iaiaaaaa); scripts/entrenamiento/lib-fotos.ts; /home/david/bitacora/pictures/research/entrenamiento/LEADERBOARD.md existe | scripts/entrenamiento/inventario.ts no existe; ids estables y hashes no encontrados; scripts/test/test-entrenamiento-inventario.ts no existe |
| T36 Harness core correr-foto | PARTIAL | scripts/entrenamiento/arnes.ts (modo --seco simulado, --tope-usd, --max-llamadas, commit fb956d8c); scripts/exp/lib-proporciones.ts y lib-zonas.ts existen | scripts/entrenamiento/correr-foto.ts no existe; scripts/test/test-entrenamiento-harness.ts no existe; «nunca edita escena a mano» no verificado |
| T37 Property tests armarDesdeEspec | PARTIAL | scripts/test/test-motor-guiada-ediciones.ts (asserts «No pude: …», lineas 41, 71, 105) | Sin tests generados ni de edición inversa = identidad (grep: sin «inversa/identidad»); scripts/test/test-propiedades-espec-ediciones.ts no existe |
| T38 Propiedades de herramientas | PARTIAL | scripts/test/test-propiedades-herramientas.ts (311 líneas); verify ejecutado: exit 0 (semilla 20261009, 40 casos, 1720 llamadas válidas); esquema contra DECLARACIONES_ESCENA | El criterio «argumentos desconocidos reportados por argumentos-desconocidos» no aparece en el test (0 aciertos); la implementación sí existe en src/lib/globos3d/herramientas-escena.ts |
| T39 Corpus de frases del dueño | DONE | scripts/test/test-frases-dueno.ts (84 líneas, commit 0849a074, corpus de 107 frases); verify ejecutado: exit 0, «118 frases en 21.1 s · 0 fallan · 1 fallas esperadas» | Ninguno detectado frente al acceptance (≥ 12 frases, llamadas simuladas, escena asertada) |
| T40 PM review (customer) | N/A | Tarea de proceso | research/pm/BACKLOG.md sin heading «REQ-014 T40» |

Notas: el PLAN aún tiene T21…T40 sin marcar (`- [ ]`). Ninguna línea de crecimiento con `origin: T22|T26|T32|T40` existe en el PLAN (grep `origin: T` solo devuelve las descripciones de las tareas PM/crítica/sweep ya listadas).

## T41-T59
# REQ-014 · auditoría T41–T59 (read-only, HEAD d14d429b, branch feat/req-015-judge-fix)

Nota: el repo `demo-decoracion` del plan (worktree marathon) no existe en esta máquina; el repo auditado es `/home/david/dev/pictures`. No hay branch `feat/req-014-*` local ni remoto. Los tests nombrados `scripts/test/test-*.ts` de las tareas no existen salvo donde se indica.

| Task | Verdict | Evidence | What's missing |
|---|---|---|---|
| T41 | PARTIAL | Loaders REQ-013 ya existentes: `src/lib/catalogo/repositorios/{sempertex,mobiliario,escenografia}/cargador.ts`, `fondos.ts` (commit 6a760e21) | `scripts/test/test-repositorios-datos.ts` no existe; no commit de la migración de datos de REQ-014 identificado; verify no ejecutado |
| T42 | PARTIAL | `src/lib/globos3d/perfiles-tamano.ts`, `src/lib/globos3d/perfiles-tamano.test.ts` (18 tests), `src/components/tres-d/SelectorPerfilTamano.tsx`, `usePerfilesTamano.ts` (commit c69e307b) | `scripts/test/test-perfiles-tamano.ts` no existe; verify no ejecutado; «guardar propio» (localStorage) no verificado |
| T43 | PARTIAL | `src/lib/globos3d/ambiente-visor.ts` (+ `.test.ts`), `src/components/tres-d/SelectorAmbienteVisor.tsx` con `LENTES_VISOR`, `NOMBRES_LUZ_VISOR` (commit c69e307b) | `scripts/test/test-presets-luz-lente.ts` no existe; verify no ejecutado; consumo por ambiente-sala no confirmado |
| T44 | MISSING | `research/kontext-color/` (en bitácora) solo contiene capturas y descripciones de idea 07/10; sin `EXPERIMENTO-*.md`; `src/lib/generacion/solicitud-kontext-contrato.ts` sin tratamiento de cromo/plata/lila | `scripts/test/test-prompt-kontext-colores.ts`, experimento pagado, hex/finish en el prompt, hoja de resultados |
| T45 | PARTIAL | `scripts/test/test-foto-cumple.ts:429-` (caso 10: rótulo acrílico y neón no se vuelven foil); commits 49e66620, 45d9eded | Aserción explícita de la cortina «plata» no confirmada; lote-02 gate no verificado; verify no ejecutado (tiempo/red) |
| T46 | PARTIAL | `scripts/entrenamiento/lib-leaderboard.ts`, `scripts/test/test-entrenamiento-leaderboard.ts`, `scripts/entrenamiento/lib-fallos.ts` | `scripts/test/test-entrenamiento-clasificar.ts` no existe; clasificación de 5 categorías y triptico no confirmados |
| T47 | PARTIAL | `scripts/test/test-motor-guiada-integracion.ts` (relacionado); `scripts/lib/casos-motor-guiada.ts` | `scripts/test/test-motor-guiada-integracion-ideas.ts` no existe; 28 ideas + re-precio no confirmados |
| T48 | N/A | Proceso (critic). Sin salida: `research/pm/BACKLOG.md` sin encabezado «REQ-014 T48»; PLAN sin líneas `origin: T48` | — (no ejecutada aún) |
| T49 | MISSING | `scripts/motor/reporte-paridad.ts` no existe (hay `scripts/motor/paridad-ideas.ts`). Solo `REQ-007-*/PARIDAD-2026-10-09{,b}.md/.csv` (previos) | Reporte nuevo con delta vs 2026-10-09. El verify (glob ≥2) pasa solo por los archivos previos: no es evidencia |
| T50 | MISSING | Sin `scripts/test/test-foil-script-dorado.ts`; no se encontró corrección de material de foil script | Fix del material y aserción de color/metalness |
| T51 | DONE | `scripts/test/test-figuras3d.ts`; commit 8679fbfb (figure test fixes, P-006). Verify ejecutado: exit 0, «OK test-figuras3d» | — |
| T52 | DONE | `scripts/test/test-python-adapter.ts:710` (sin LoRA, lista vacía); `.github/workflows/checks.yml` deterministic-tests con `if: ${{ !cancelled() }}` por paso y comentario de reporte de todas las suites. Verify ejecutado: exit 0 | CI del job no ejecutado en remoto (no verificable localmente) |
| T53 | MISSING | Sin `scripts/test/test-componer-letrero.ts`; sin módulo de composición de letrero en `src/`/`scripts/` | Todo (composición, flag, fixtures) |
| T54 | PARTIAL | `src/lib/globos3d/salon-armar.ts` (mesas `medidasDeMesa`, `sillas` como parámetro); `scripts/test/test-salon-evento.ts` existe | `scripts/test/test-salon-mesas-parametricas.ts` no existe; sustitución de `opciones.sillas` por sets paramétricos no confirmada |
| T55 | N/A | Ship #3 (proceso, push autorizado). Branch `feat/req-014-*` ausente local y en remotos; depende de T31–T54 | — |
| T56 | N/A | PM review (proceso). Sin `REQ-014 T56` en BACKLOG; sin líneas `origin: T56` | — |
| T57 | PARTIAL | `research/entrenamiento/LEADERBOARD.md` tiene 30 filas `images (N)`, pero fechadas 2026-10-11, coste 0.0000 | Primera pasada real de 5 fotos con tope US$1.50 y registro de gasto no evidenciados; verify pasaría con filas previas. Requiere API key (no ejecutado) |
| T58 | PARTIAL | `REQ-007-*/DOSSIER-SWITCH.md` (143 líneas): contiene counts, D-026, desktop, phone, failure modes, rollback | Drill de rollback no hecho (el dossier lo marca bloqueado: rollback graceful no construido, §4); sin referencias a capturas en artifacts/ |
| T59 | N/A | PM review (proceso). Sin `REQ-014 T59` en BACKLOG; sin líneas `origin: T59` | — |

SUMMARY (conteo): DONE 2 (T51, T52) · PARTIAL 9 (T41, T42, T43, T45, T46, T47, T54, T57, T58) · MISSING 4 (T44, T49, T50, T53) · N/A 4 (T48, T55, T56, T59). Total 19.
Verify ejecutados (cheap): test-figuras3d OK (exit 0); test-python-adapter OK (exit 0). No ejecutados: los demás (lentos, con red o API de pago).
UNVERIFIED: commit de T52 no identificado; T50 y T54 pueden tener cambios no detectados por búsqueda de palabras clave.

## Verify commands executed 2026-10-14 (HEAD d14d429b; env without API keys/DB; 240 s cap)

PASS 16: T2,T3,T4,T6,T7,T9,T10,T20,T38,T39,T45,T49,T51,T52,T57,T58 · SKIP 4 (git/remote: T1,T14,T31,T55) · FAIL 39: 29 because the named test file does not exist in scripts/test (T5 T11 T12 T13 T15 T16 T19 T21 T23 T24 T25 T27 T28 T29 T30 T33 T34 T35 T36 T37 T41 T42 T43 T44 T46 T47 T50 T53 T54), 2 doc checks (T17, T22) and 8 template placeholders without a real command (T8 T18 T26 T32 T40 T48 T56 T59). New passes vs the audit: T7, T10, T45 (real tests, 16/25/37 cases); T49, T57, T58 pass only on older files (PARIDAD/LEADERBOARD/DOSSIER dated before this marathon): not evidence.

T1|SKIP|git/remote check (needs absent branch/commit or network)
T2|PASS|ℹ duration_ms 1023.90484
T3|PASS|ℹ duration_ms 727.345742
T4|PASS|ℹ duration_ms 733.11628
T5|FAIL|Node.js v24.21.0
T6|PASS|test-guardia-prerender: ok (guardia parcial; fixture: 24 violaciones, 6 por un salto; hook sin directiva marcado; Taller3D previo marcado; 297 compone
T7|PASS|test-ui-plan-motor3d: ok (16 pruebas, 39 sobres)
T8|FAIL|
T9|PASS|test-esquema-gemini: 6 pruebas ok
T10|PASS|25 pruebas OK
T11|FAIL|Node.js v24.21.0
T12|FAIL|Node.js v24.21.0
T13|FAIL|Node.js v24.21.0
T14|SKIP|git/remote check (needs absent branch/commit or network)
T15|FAIL|Node.js v24.21.0
T16|FAIL|Node.js v24.21.0
T17|FAIL|
T18|FAIL|
T19|FAIL|Node.js v24.21.0
T20|PASS|test-herramientas-anthropic: 8 pruebas ok
T21|FAIL|Node.js v24.21.0
T22|FAIL|FileNotFoundError: [Errno 2] No such file or directory: '/home/david/bitacora/pictures/research/escenarios/PASS-RATE.md'
T23|FAIL|Node.js v24.21.0
T24|FAIL|Node.js v24.21.0
T25|FAIL|Node.js v24.21.0
T26|FAIL|
T27|FAIL|Node.js v24.21.0
T28|FAIL|Node.js v24.21.0
T29|FAIL|Node.js v24.21.0
T30|FAIL|Node.js v24.21.0
T31|SKIP|git/remote check (needs absent branch/commit or network)
T32|FAIL|
T33|FAIL|Node.js v24.21.0
T34|FAIL|Node.js v24.21.0
T35|FAIL|Node.js v24.21.0
T36|FAIL|Node.js v24.21.0
T37|FAIL|Node.js v24.21.0
T38|PASS|test-propiedades-herramientas (semilla 20261009, 40 casos): 45 herramientas (2 exentas con motivo); 924 llamadas que aplicaron un resultado consistent
T39|PASS|test-frases-dueno: 118 frases en 21.5 s · 0 fallan · 1 fallas esperadas
T40|FAIL|
T41|FAIL|Node.js v24.21.0
T42|FAIL|Node.js v24.21.0
T43|FAIL|Node.js v24.21.0
T44|FAIL|Node.js v24.21.0
T45|PASS|test-foto-cumple: 37 pruebas ok, 0 con fallas
T46|FAIL|Node.js v24.21.0
T47|FAIL|Node.js v24.21.0
T48|FAIL|
T49|PASS|
T50|FAIL|Node.js v24.21.0
T51|PASS|OK test-figuras3d: Celebra ed. 27 en sus 25 sitios de la foto
T52|PASS|Python adapter: OK
T53|FAIL|Node.js v24.21.0
T54|FAIL|Node.js v24.21.0
T55|SKIP|git/remote check (needs absent branch/commit or network)
T56|FAIL|
T57|PASS|
T58|PASS|
T59|FAIL|