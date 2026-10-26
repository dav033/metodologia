---
req: REQ-021
status: draft
created: 2026-10-26
---
# Plan — Lanzamiento del piloto: cuentas y planes de acceso, trabajo guardado, gasto de IA, funciones esenciales del Taller, inglés, módulos y chat

Esquema (planificación colaborativa, fase Esqueleto). Solo hitos y subplanes; las tareas se definen subplan por subplan
con el propietario.

## Enfoque
Base de código: origin/main `a9f3d6e5` de `dav033/pictures` (Next 16 en Vercel, ai-api en Python en el VPS, Neon Postgres con
`scripts/migrations/NNN_*.sql` aplicados mediante `npm run rag:migrate`). El trabajo parte de origin/main en nuevos worktrees;
no se usa `~/dev/pictures`.

**Orden inverso desde el piloto (2026-11-16).** Las cuentas van primero porque los proyectos y las decoraciones guardados, el gasto
por usuario, los planes de acceso y el idioma por cuenta requieren una sesión iniciada. Los elementos del Taller que no requieren
cuentas (mesas rectangulares, Backing, exportación a Blender y módulos editables) se ejecutan en paralelo desde el primer día. El idioma
parte de su propia base en paralelo y es lo primero que se recorta.

| Hito | Fecha objetivo | ¿No se recorta? | Fecha límite de recorte (propietario, ronda 4) |
|---|---|---|---|
| M1 — Cuentas, planes de acceso y funciones esenciales del Taller | 2026-11-01 | sí | — |
| M2 — Trabajo guardado, gasto por usuario y herramientas del chat | 2026-11-07 | sí | — |
| M3 — Inglés / español | 2026-11-09 | no (primer recorte) | 2026-11-09: solo se publica SP-8 (Taller 3D y navegación) |
| M4 — Módulos editables y chat → 3D | 2026-11-12 | no (segundo y tercer recorte) | 2026-11-11: se recortan los módulos; 2026-11-12: se recortan las funciones del chat más allá de la división y la confiabilidad |
| M5 — Lanzamiento del piloto | 2026-11-16 | sí | — |

**Dependencias.** SP-1 (cuentas) → SP-2, SP-4, SP-5, SP-6, SP-7, SP-8. SP-4 (identidad del proyecto) → SP-6 y SP-12.
SP-6 (etiquetado del gasto) → SP-7. SP-8 (mecanismo de idioma) → SP-9, SP-10. SP-7 (herramientas del chat, explorador de decoraciones) →
SP-10, SP-12. SP-3 y SP-11 no dependen de nada. SP-13 integra todos los subplanes publicados.

**Viabilidad, en términos claros.** Tamaño aproximado: unas 70 tareas para toda la SPEC y unas 45 para la parte que no se recorta (SP-1 a SP-7 y
SP-13). El tiempo de los agentes no es el límite; sí lo son las esperas: los reintentos, los límites de uso y las pruebas del propietario por subplan (menos de 24 h,
D-131). Solo es viable si el planificador ejecuta dos o más subplanes a la vez y los reintentos son pocos. Si M1 se retrasa más allá del
2026-11-03, se aplican las fechas de recorte acordadas; el trabajo que no se recorta nunca se sacrifica por el idioma, los módulos o el chat→3D.

**Seguridad.** SP-1 (identidad, sesiones, permisos, aplicación en el servidor, indicador local y primer administrador) es su
propio subplan y tiene su propia auditoría; SP-4 verifica que un usuario solo pueda acceder a sus propios proyectos.

Fuera de este plan: espacio 3D, exportación a Illustrator/vectorial y límites de gasto de IA (D-072).

### M1 — Cuentas, planes de acceso y elementos esenciales del Taller
Las personas reales inician sesión con su propia cuenta de invitación y cada una accede exactamente a lo que permite su rol o plan de acceso; la APP_PASSWORD compartida ya no permite abrir la aplicación; las tablas, Backing y el archivo de Blender funcionan en el Taller.

- **SP-1 — Cuentas, sesiones y permisos del lado del servidor**: Las cuentas invitadas con contraseñas con hash y sesiones del servidor revocables reemplazan la APP_PASSWORD compartida; cada página y API del piloto comprueba en el servidor el permiso que necesita; los roles y los tres planes de acceso son conjuntos de permisos; la marca local sin restricciones no se puede activar en producción; el primer administrador se crea mediante un comando de una sola ejecución. Cubre R1, R2, R3, R16.

<!-- SP-1 tasks -->

  Tareas de SP-1 (borrador para confirmación del propietario). Decisiones del propietario, rondas 5–6: los planes de acceso son roles (Usuario · Plan 1, Usuario · Plan 2, Usuario · Plan 3, Empleado interno, Administrador; un rol por cuenta); permisos según las aclaraciones de SPEC de la ronda 6; sesión de 30 días; contraseña de al menos 8 caracteres; 5 intentos fallidos por correo electrónico en 15 min la bloquean durante 15 min; enlace de invitación de 7 días y enlace de restablecimiento de 24 h, ambos copiados por el administrador (sin servicio de correo electrónico); `AUTH_LOCAL_SIN_RESTRICCIONES=1` solo con `next dev` en loopback; el propietario crea personalmente el primer administrador de producción mediante un comando de una sola ejecución.
  Decisiones del planificador (revisables durante la confirmación): los cinco roles del sistema son fijos en el código y de solo lectura en el piloto (los roles personalizados sí se pueden editar), para que ningún administrador pueda impedir el acceso a todos y los planes siempre coincidan con R16; las rutas que no están en el mapa son solo para administradores; las páginas se protegen en `src/proxy.ts` (no existen acciones del servidor) y los controladores de API también llaman al guardián por su cuenta; SP-1 no tiene pantallas nuevas: el inicio de sesión, la activación y las pantallas de administración corresponden a SP-2, así que SP-1 se prueba con el modo local en el navegador y `npm run cuentas:probar-acceso` en la terminal. Hasta que se integre SP-2, la página /login actual no permite iniciar sesión; nada llega a `main` antes de que se aprueben todos los subplanes de M1.
  Contratos generados: permission-map@1 (T1.2: catálogo de `src/lib/cuentas/permisos.ts` y roles del sistema, `src/lib/cuentas/mapa-rutas.ts`), account-service@1 (T1.3: `src/lib/cuentas/servicio.ts`), session-guard@1 (T1.4: `obtenerSesion(request)`, `exigirPermiso(request, permiso)` en `src/lib/cuentas/guardia.ts`). Consumidores: SP-2, SP-4, SP-5, SP-6, SP-7, SP-8. DAG: T1.1 → T1.2 → T1.3 → T1.4 → {T1.5, T1.6} → T1.7 → T1.8.
  Base de datos de pruebas: cada prueba de base de datos lee `PICTURES_REQ021_DATABASE_URL` (o, solo en CI, `DATABASE_URL` con `APP_ENV=test`) mediante `scripts/test/lib/base-prueba.ts`, que crea un esquema temporal (`search_path` = ese esquema, public) para que las ejecuciones nunca vean las filas de las demás. La evidencia de auditoría se guarda en `.evidence/REQ-021/` porque el motor necesita el registro en el repositorio.

- [ ] T1.1 — Esquema de cuentas: migración 037 y helper para esquema de pruebas aislado · repo: pictures · verificar: `npm run cuentas:test-esquema -- --test-name-pattern=migracion` · archivos: scripts/migrations/037_cuentas.sql, scripts/test/lib/base-prueba.ts, scripts/test/test-cuentas-esquema.ts · recursos: scripts de package.json · cubre: R1, R2, R3 · tipo: implementar · subplan: SP-1 · ui: no

  Clasificación: complejidad media; alcance small_change; riesgo alto; acoplamiento medio; confianza alta; estimación: 60 minutos.
  Tablas (solo aditivas, `IF NOT EXISTS`, comentario de reversión como en 036): `roles` (id, `clave` única para los cinco roles del sistema `usuario_plan_1`, `usuario_plan_2`, `usuario_plan_3`, `empleado_interno`, `administrador`, nombre, campo booleano `sistema`); `rol_permisos` (rol_id, permiso; solo para roles personalizados, los permisos de roles del sistema están en el código); `cuentas` (id, correo con un índice único en `lower(correo)`, nombre, empresa nullable, rol_id, estado `invitada|activa|desactivada`, hash_contrasena nullable, invitada_en, activada_en, ultimo_acceso_en, aviso_datos_version, aviso_datos_aceptado_en, idioma nullable `es|en`, es_local boolean, creada_por nullable); `sesiones` (id, cuenta_id ON DELETE CASCADE, hash_token char(64) unique, creada_en, expira_en, revocada_en); `enlaces_cuenta` (id, cuenta_id ON DELETE CASCADE, tipo `invitacion|restablecer`, hash_token unique, expira_en, usado_en, creado_por); `intentos_ingreso` (correo normalizado, en, exitoso) con índice en (correo, en).
  Los únicos datos personales que se conservan son los que enumera la ronda 5 q6. `base-prueba.ts` exporta `crearBasePrueba()` → `{ url, pool, cerrar() }`: se niega a continuar a menos que la URL provenga de `PICTURES_REQ021_DATABASE_URL` o de `DATABASE_URL` con `APP_ENV=test`; crea el esquema `prueba_<random>`, aplica todas las migraciones de `scripts/migrations/` con la lógica del ejecutor, devuelve una URL cuyas opciones establecen `search_path=<schema>,public` y elimina el esquema en `cerrar()`.
  Script de npm agregado: `cuentas:test-esquema` = `tsx --test scripts/test/test-cuentas-esquema.ts`.

  - Aceptación / integración: La migración 037 se aplica sin error a un esquema aislado vacío y luego a otro que ya contiene las migraciones; crea las tablas de cuentas, roles, sesiones, enlaces e intentos de inicio de sesión, y carga exactamente los cinco roles del sistema. Comprobación: `npm run cuentas:test-esquema -- --test-name-pattern=migracion`
  - Aceptación / funcional: La base de datos rechaza una segunda cuenta cuyo correo electrónico solo difiere en mayúsculas y minúsculas, y elimina las sesiones y los enlaces de una cuenta cuando esta se elimina. Comprobación: `npm run cuentas:test-esquema -- --test-name-pattern=restricciones`
  - Aceptación / funcional: Cada ejecución de prueba funciona en su propio esquema temporal de la base de datos de pruebas de REQ-021, lo elimina al finalizar y se niega a ejecutarse contra cualquier base de datos que no sea PICTURES_REQ021_DATABASE_URL o una base de datos de CI marcada como APP_ENV=test. Comprobación: `npm run cuentas:test-esquema -- --test-name-pattern=aislamiento`

- [ ] T1.2 — Catálogo de permisos, los cinco roles del sistema y el mapa de permisos de rutas · repositorio: pictures · después de: T1.1 · verificar: `npm run cuentas:test-permisos -- --test-name-pattern=cobertura` · archivos: src/lib/cuentas/permisos.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-mapa-rutas.ts · recursos: scripts de package.json, contract:permission-map · cubre: R2, R3, R16 · tipo: implementación · subplan: SP-1 · ui: no

  Clasificación: complejidad media; alcance small_change; riesgo alto; acoplamiento alto; confianza media; estimación: 90 minutos.
  Permisos (claves estables, etiquetas ES/EN para SP-2): `chat.usar`, `contador.usar`, `catalogo.ver`, `costos.usar`, `decoraciones.explorar`, `taller.usar`, `proyectos.ver_todos`, `gasto.ver`, `internas.usar`, `cuentas.administrar`, `roles.administrar`, `textos.corregir`. Roles del sistema: Plan 1 = chat, contador, catálogo; Plan 2 = Plan 1 + costos, decoraciones; Plan 3 = Plan 2 + taller; Empleado interno = Plan 3 + proyectos.ver_todos, gasto.ver, internas.usar; Administrador = todo.
  Entradas del mapa: `{ patron, acceso }`, donde `acceso` = `{ permiso }`, `'sesion'` (cualquier cuenta con sesión iniciada: página de inicio, cerrar sesión), `'publica'` (inicio de sesión, activación, `/cotizacion-compartida/*` y sus API públicas) o `'auth-propia'` (excepciones actuales del proxy: asesor, recomendación/webhook de Happie, webhook de Shopify, cron de feedback, transcripción de voz). Clasificación: /asistente, chat y API del motor guiado → chat.usar; /catalogo y API de lectura de catálogo/productos → catalogo.ver; cotizacion-profesional → costos.usar; API de lectura de decoraciones → decoraciones.explorar; /3d, IA de escenas, plan-armado-*, plan-patron, plan-dibujo-estructura, plan-idea, plan-editar, taller/*, modulos-*, renderizado y generación de imágenes, escena-desde-foto, hoja-armado → taller.usar; /admin, /api/admin/*, API de escritura de productos y decoraciones, /estadisticas, laboratorios, prueba de Happie, proveedor de IA, administración de feedback, IA interna → internas.usar. El contador de globos no tiene una ruta propia hasta SP-7. Una ruta cuya herramienta no esté clara se asigna a internas.usar y se incluye en el informe de la tarea.
  `resolverAcceso(path)` devuelve la única entrada coincidente o `null` (= solo Administrador, permiso `cuentas.administrar`). El script npm `cuentas:test-permisos` = `tsx --test scripts/test/test-mapa-rutas.ts`.

  - Aceptación / estática: Cada page.tsx y route.ts dentro de src/app coincide exactamente con una entrada del mapa de permisos de rutas, y la prueba falla indicando cualquier archivo que no coincida con ninguna o coincida con varias. Verificación: `npm run cuentas:test-permisos -- --test-name-pattern=cobertura`
  - Aceptación / funcional: Los cinco roles del sistema tienen exactamente los permisos de la tabla del propietario: Plan 1: chat, contador de globos y catálogo; Plan 2 añade costos y el explorador de decoraciones; Plan 3 añade Taller 3D; Empleado interno añade los proyectos de todos, el gasto de IA y las herramientas internas; Administrador añade usuarios, roles y correcciones de textos. Verificación: `npm run cuentas:test-permisos -- --test-name-pattern=roles-sistema`
  - Aceptación / funcional: Una ruta que no figure en el mapa solo es accesible con el permiso de administración de usuarios, y las excepciones públicas y de autenticación propia del comparador actual del proxy siguen siendo públicas o de autenticación propia. Verificación: `npm run cuentas:test-permisos -- --test-name-pattern=excepciones`

- [ ] T1.3 — Servicio de cuentas: invitaciones, activación, inicio de sesión con bloqueo, enlaces de restablecimiento, roles y comandos de ejecución única · repositorio: pictures · después de: T1.2 · verificar: `npm run cuentas:test-servicio -- --test-name-pattern=invitacion` · archivos: src/lib/seguridad/scrypt.ts, src/lib/asesor/auth.ts, src/lib/cuentas/servicio.ts, src/lib/cuentas/enlaces.ts, src/lib/cuentas/limite-intentos.ts, scripts/cuentas/primer-admin.ts, scripts/cuentas/sembrar-prueba.ts, scripts/test/test-cuentas-servicio.ts · recursos: scripts de package.json, contract:account-service, contract:permission-map · cubre: R1, R3, R16 · tipo: implementación · subplan: SP-1 · ui: no

  Clasificación: complejidad alta; alcance large_change; riesgo alto; acoplamiento alto; confianza media; estimación: 150 minutos.
  Traslada sin cambios el hash/verificación scrypt de `src/lib/asesor/auth.ts` a `src/lib/seguridad/scrypt.ts`; el inicio de sesión del asesor lo importa y conserva su comportamiento.
  API del servicio (`src/lib/cuentas/servicio.ts`, solo servidor): `invitar({correo, nombre, empresa?, rolId}, porCuentaId)` → enlace; `activar(token, {contrasena, versionAviso})`; `ingresar(correo, contrasena, ip)` → cuenta o el error genérico `CREDENCIALES_INVALIDAS`; `crearEnlaceRestablecer(cuentaId, porCuentaId)`; `restablecer(token, contrasena)`; `cambiarRol`, `desactivar`, `reactivar`, `eliminar`; `crearRol({nombre, permisos})`, `editarRol`, `eliminarRol`. Tokens: 32 bytes aleatorios en base64url, solo se almacena SHA-256; invitación: 7 días, restablecimiento: 24 h, uso único con bloqueo de fila. Contraseñas: mínimo 8 caracteres, máximo 200, scrypt. Bloqueo: 5 intentos fallidos para un correo normalizado en 15 min → se rechaza ese correo durante 15 min (se comprueba antes de verificar la contraseña; mismo error genérico). El último Administrador activo no puede desactivarse, eliminarse ni cambiarse a otro rol. Al eliminar una cuenta se borran su fila, sesiones, enlaces e intentos de inicio de sesión; los subplanes posteriores decidirán qué ocurre con sus proyectos.
  `npm run cuentas:primer-admin -- --correo <email>` (el propietario lo ejecuta durante la publicación contra la base de datos de `DATABASE_URL`): se niega a hacer cambios si ya existe un Administrador activo; de lo contrario, crea la cuenta invitada de Administrador e imprime el enlace de activación una sola vez en la terminal, nunca en un archivo de registro. `npm run cuentas:sembrar-prueba`: se niega a ejecutarse salvo que el destino sea `PICTURES_REQ021_DATABASE_URL`; crea `plan1@prueba.local`, `plan2@prueba.local`, `plan3@prueba.local`, `empleado@prueba.local` y `admin@prueba.local`, activas, con una contraseña ingresada sin mostrarla. El script npm `cuentas:test-servicio` = `tsx --conditions=react-server --test scripts/test/test-cuentas-servicio.ts`.

  - Aceptación / funcional: La invitación de un administrador crea una cuenta invitada con un enlace de uso único válido durante siete días; al activarla, se establece una contraseña de al menos ocho caracteres y se registra la versión y la fecha del aviso de datos; se rechaza un segundo uso del mismo enlace. Verificación: `npm run cuentas:test-servicio -- --test-name-pattern=invitacion`
  - Aceptación / funcional: Iniciar sesión con el correo y la contraseña correctos de una cuenta activa crea una sesión; una contraseña incorrecta, un correo desconocido y una cuenta desactivada reciben el mismo rechazo genérico. Verificación: `npm run cuentas:test-servicio -- --test-name-pattern=ingreso`
  - Aceptación / funcional: Tras cinco inicios de sesión fallidos para un correo en quince minutos, se rechaza ese correo durante quince minutos incluso con la contraseña correcta, y los demás correos no se ven afectados. Verificación: `npm run cuentas:test-servicio -- --test-name-pattern=bloqueo`
  - Aceptación / funcional: El enlace de restablecimiento generado por un administrador es de uso único, vence después de 24 horas, establece una contraseña nueva y revoca todas las sesiones abiertas de esa cuenta. Verificación: `npm run cuentas:test-servicio -- --test-name-pattern=restablecer`
  - Aceptación / funcional: Se rechaza desactivar, eliminar o cambiar el rol del último Administrador activo; al eliminar una cuenta, se borran sus filas de datos personales. Verificación: `npm run cuentas:test-servicio -- --test-name-pattern=ultimo-admin`
  - Aceptación / funcional: Un administrador crea un rol usando solo permisos del catálogo; los cinco roles del sistema no se pueden editar ni eliminar; no se puede eliminar un rol que siga asignado a cuentas. Verificación: `npm run cuentas:test-servicio -- --test-name-pattern=roles`
  - Aceptación / integración: npm run cuentas:primer-admin crea un Administrador invitado para el correo indicado e imprime su enlace de activación una sola vez, y se niega a hacer cambios si ya existe un Administrador activo. Verificación: `npm run cuentas:test-servicio -- --test-name-pattern=primer-admin`
  - Aceptación / funcional: npm run cuentas:sembrar-prueba crea una cuenta activa por cada rol del sistema con una contraseña leída en la terminal sin mostrarla, y se niega a ejecutarse cuando la base de datos de destino no es la base de datos de prueba de REQ-021. Verificación: `npm run cuentas:test-servicio -- --test-name-pattern=sembrar`

- [ ] T1.4 — Sesiones de servidor y control de permisos en el proxy y la API de inicio de sesión, en reemplazo de APP_PASSWORD · repositorio: pictures · después de: T1.3 · verificar: `npm run cuentas:test-sesion -- --test-name-pattern=cookie` · archivos: src/lib/cuentas/sesion.ts, src/lib/cuentas/guardia.ts, src/proxy.ts, src/lib/auth/session.ts, src/lib/auth/request.ts, src/app/api/login/route.ts, src/app/api/cuentas/ingresar/route.ts, src/app/api/cuentas/salir/route.ts, src/app/sin-acceso/page.tsx, scripts/cuentas/probar-acceso.ts, scripts/test/test-sesion-guardia.ts, scripts/test/test-proxy-matcher.ts · recursos: scripts de package.json, contract:session-guard, contract:account-service, contract:permission-map · cubre: R1, R2 · tipo: implementación · subplan: SP-1 · ui: no

  Clasificación: complejidad alta; alcance large_change; riesgo alto; acoplamiento alto; confianza media; estimación: 150 minutos.
  `sesion.ts`: `crearSesion(cuentaId)` establece la cookie `pictures_sesion` (httpOnly, SameSite=Lax, Secure salvo que el host sea localhost/127.0.0.1, Max-Age 30 días, vencimiento absoluto); `obtenerSesion(request)` → `{ cuenta, rol, permisos } | null` con una consulta (sesiones × cuentas × roles; permisos de roles personalizados desde `rol_permisos`, y los del sistema desde `permisos.ts`), rechazando sesiones revocadas o vencidas, o cuentas inactivas, y actualizando `ultimo_acceso_en` como máximo una vez por hora; `cerrarSesion`.
  `guardia.ts`: `exigirPermiso(request, permiso)` → `{ cuenta } | Response` (401 `SESION_REQUERIDA` / 403 `SIN_PERMISO`, JSON). `src/proxy.ts`: las entradas públicas y de autenticación propia pasan sin cambios (las mismas excepciones del comparador actual); en los demás casos, resuelve la sesión y el mapa: sin sesión → redirección de página a `/login?from=<path>` y API 401; sin permiso → reescritura de página a `/sin-acceso` (página de servidor simple, solo texto) y API 403. Elimina `APP_PASSWORD`, `sessionToken`, `loginOmitidoEnDesarrollo` y `DEV_REQUIRE_LOGIN`; se elimina `/api/login` en favor de `POST /api/cuentas/ingresar` (JSON con correo y contraseña, misma regla de redirección relativa que hoy para formularios) y `POST /api/cuentas/salir`. Las API que modifican datos conservan `isSameOriginRequest`.
  `npm run cuentas:probar-acceso -- --base http://localhost:3000 --correo <email>` lee la contraseña sin mostrarla, inicia sesión e imprime los permisos permitidos o denegados para una página y una API representativas de cada área del mapa. El script npm `cuentas:test-sesion` = `tsx --conditions=react-server --test scripts/test/test-sesion-guardia.ts`; `test-proxy-matcher` se actualiza al nuevo comparador.

  - Criterio de aceptación / funcional: Una cookie de sesión tiene el atributo httpOnly, SameSite=Lax, Secure fuera de localhost, dura 30 días y solo se almacena el hash SHA-256 de su token aleatorio. Comprobación: `npm run cuentas:test-sesion -- --test-name-pattern=cookie`
  - Criterio de aceptación / funcional: Desactivar una cuenta, cambiar su contraseña o cerrar sesión finaliza sus sesiones en la siguiente solicitud, y un cambio de rol se aplica en la siguiente solicitud sin volver a iniciar sesión. Comprobación: `npm run cuentas:test-sesion -- --test-name-pattern=revocacion`
  - Criterio de aceptación / funcional: Sin una sesión válida, una solicitud a una página redirige a /login conservando la ruta, y una solicitud a una API recibe JSON con estado 401; con una sesión que carece del permiso asignado, una página muestra la página de acceso denegado y una API responde con JSON de estado 403. Comprobación: `npm run cuentas:test-sesion -- --test-name-pattern=proxy`
  - Criterio de aceptación / regresión: Una cookie o un formulario creados a partir del valor anterior de APP_PASSWORD ya no otorgan acceso, y ninguna ruta del código lee APP_PASSWORD. Comprobación: `npm run cuentas:test-sesion -- --test-name-pattern=sin-clave-compartida`
  - Criterio de aceptación / integración: npm run cuentas:probar-acceso inicia sesión contra un servidor en ejecución con un correo electrónico y una contraseña leída sin mostrarla en pantalla, e imprime, para cada área asignada, si la cuenta tiene permiso o no. Comprobación: `npm run cuentas:test-sesion -- --test-name-pattern=probar-acceso`

- [ ] T1.5 — Modo local sin restricciones que impide el inicio fuera de next dev en loopback · repositorio: pictures · después de: T1.4 · verificar: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback` · archivos: src/lib/cuentas/modo-local.ts, src/instrumentation.ts, next.config.ts, services/ai-api/app/main.py, scripts/test/test-modo-local.ts, services/ai-api/tests/test_modo_local.py · recursos: scripts de package.json · cubre: R2 · tipo: implementación · subplan: SP-1 · UI: no

  Clasificación: complejidad media; alcance small_change; riesgo alto; acoplamiento medio; confianza alta; estimación: 60 minutos.
  `modo-local.ts`: `validarModoLocal({ nodeEnv, vercel, fase })` genera el error `AUTH_LOCAL_SIN_RESTRICCIONES solo funciona con next dev en tu máquina` a menos que `NODE_ENV=development`, `VERCEL` no esté definida y la fase sea el servidor de desarrollo; se invoca desde `next.config.ts` (cubre `next build`) y `register()` en `src/instrumentation.ts` (cubre `next start` y el contenedor de VPS). ai-api impide el inicio si la variable está definida, incluso si su valor está vacío. En cada solicitud, la guardia de sesión trata la solicitud como si fuera la cuenta local Administrador solo cuando el modo está activado y la dirección de conexión es loopback (127.0.0.1, ::1); nunca se confía en el encabezado Host.
  La cuenta local Administrador (`es_local = true`, correo `admin-local@localhost.invalid`, rol Administrador, sin contraseña, por lo que nunca puede iniciar sesión de forma remota) se crea en el primer uso en la base de datos a la que apunte el proceso local; esto también cubre la nota de la ronda 6 del propietario sobre ejecutar localmente contra la base de datos de producción para crear administradores.
  El script npm `cuentas:test-modo-local` = `tsx --conditions=react-server --test scripts/test/test-modo-local.ts`.

  - Criterio de aceptación / funcional: Con AUTH_LOCAL_SIN_RESTRICCIONES=1 bajo next dev, una solicitud desde 127.0.0.1, ::1 o localhost se ejecuta como la cuenta local Administrador sin iniciar sesión, y una solicitud desde cualquier otra dirección debe iniciar sesión. Comprobación: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback`
  - Criterio de aceptación / funcional: Con AUTH_LOCAL_SIN_RESTRICCIONES definida, next build, next start, un entorno de Vercel y el despliegue de ai-api impiden el inicio con un error que menciona la variable. Comprobación: `npm run cuentas:test-modo-local -- --test-name-pattern=rechazo-arranque`
  - Criterio de aceptación / regresión: Sin la variable, next dev solicita iniciar sesión igual que en producción, y DEV_REQUIRE_LOGIN ya no tiene ningún efecto. Comprobación: `npm run cuentas:test-modo-local -- --test-name-pattern=sin-variable`

- [ ] T1.6 — Aplicar la guardia de permisos a cada controlador de API y migrar las suites existentes a una sesión de prueba compartida · repositorio: pictures · después de: T1.4 · verificar: `npm run cuentas:test-rutas` · archivos: src/app/api/**/route.ts, src/lib/feedback-ia/acceso.ts, src/lib/guiada-motor/manejadores.ts, src/lib/happie/panel-prueba.ts, src/lib/shared-quotes/dependencies.server.ts, src/lib/taller/cotizacion-taller.ts, src/lib/asesor/voice.ts, scripts/test/lib/sesion-prueba.ts, scripts/test/test-guardias-rutas.ts, scripts/test/*.ts, scripts/e2e/humo/configuracion.ts, scripts/e2e/humo/pasos-asistente.ts, scripts/e2e/humo/navegacion.ts, scripts/eval/eval-chat-jerga.ts · recursos: scripts de package.json, contract:session-guard, contract:permission-map · cubre: R2 · tipo: implementación · subplan: SP-1 · UI: no

  Clasificación: complejidad baja; alcance large_change; riesgo alto; acoplamiento alto; confianza alta; estimación: 180 minutos.
  Cada controlador fuera de las excepciones `publica`/`auth-propia` comienza con `const acceso = await exigirPermiso(request, '<permiso>'); if (acceso instanceof Response) return acceso;`, usando el permiso que `resolverAcceso` asigna a su ruta; los controladores de biblioteca que llamaban a `isAuthenticatedRequest` reciben la cuenta desde su controlador en su lugar. `test-guardias-rutas.ts` lee cada `route.ts`, comprueba que cada método HTTP exportado invoque `exigirPermiso` con exactamente el permiso asignado antes de cualquier otro await, e invoca una muestra de controladores en el mismo proceso sin sesión, con una sesión Plan 1 y con una sesión Administrador.
  `scripts/test/lib/sesion-prueba.ts`: `conSesionDePrueba(rolClave)` crea una cuenta y una sesión en el esquema de prueba aislado y devuelve el encabezado de cookie; ninguna variable de entorno omite la autenticación. La prueba smoke de e2e (`npm run e2e:humo`) inicia sesión con `E2E_CORREO`/`E2E_CONTRASENA` en lugar de APP_PASSWORD. El script npm `cuentas:test-rutas` = `tsx --conditions=react-server --test scripts/test/test-guardias-rutas.ts`.

  - Aceptación / funcional: Cada controlador de ruta de API, excepto las rutas públicas y las excepciones de autenticación propia, llama al guardián de permisos con el permiso que el mapa asigna a su ruta antes de realizar cualquier trabajo. Comprobación: `npm run cuentas:test-rutas`
  - Aceptación / regresión: Las suites existentes que iniciaban sesión con APP_PASSWORD pasan usando el helper compartido de sesión de prueba y ninguna configura APP_PASSWORD. Comprobación: `npm run test-cotizacion-unica`
  - Aceptación / estática: El lint y la comprobación de TypeScript pasan en todo el repositorio una vez aplicados los guardianes. Comprobación: `npm run taller:test-estatico`

- [ ] T1.7 — Comprobación de extremo a extremo de las cuentas y los permisos en una compilación de producción, y las suites de SP-1 en CI · repositorio: pictures · después de: T1.5, T1.6 · verificar: `npm run cuentas:test-integracion` · archivos: scripts/test/test-integracion-cuentas.ts, .github/workflows/checks.yml, .evidence/REQ-021/SP-1.integration.json · recursos: scripts de package.json, contract:session-guard · cubre: R1, R2, R3, R16 · tipo: prueba · subplan: SP-1

  Clasificación: complejidad media; alcance small_change; riesgo alto; acoplamiento medio; confianza media; estimación: 120 minutos.
  `test-integracion-cuentas.ts`: crea el esquema aislado, carga una cuenta por rol mediante el servicio, ejecuta `next build` y luego `next start` en un puerto de loopback disponible con `DATABASE_URL` = la URL del esquema y, usando `fetch` directamente: inicia sesión mediante `/api/cuentas/ingresar`, comprueba las páginas permitidas y denegadas (redirección o `/sin-acceso`) y las API (401/403) para Plan 1, Plan 3, Empleado interno y Administrador; desactiva la cuenta de Plan 3 mediante el servicio y comprueba que su siguiente solicitud recibe 401; envía el formulario de la contraseña compartida anterior y comprueba que se rechaza; luego inicia `next start` con `AUTH_LOCAL_SIN_RESTRICCIONES=1` y comprueba que finaliza con el error. Escribe `.evidence/REQ-021/SP-1.integration.json` y solo finaliza sus propios procesos.
  `checks.yml`: el trabajo de Postgres ejecuta `cuentas:test-esquema`, `cuentas:test-permisos`, `cuentas:test-servicio`, `cuentas:test-sesion`, `cuentas:test-modo-local` y `cuentas:test-rutas`, además de un paso que ejecuta `next build` con la variable configurada y solo pasa si la compilación falla. El script de npm `cuentas:test-integracion` = `tsx scripts/test/test-integracion-cuentas.ts`.

  - Aceptación / integración: Con una compilación de producción iniciada con next start sobre la base de datos de prueba de REQ-021, cada cuenta de Plan 1, Plan 3, Empleado interno y Administrador llega exactamente a las páginas y API que le corresponden según el mapa; una cuenta desactivada pierde el acceso en su siguiente solicitud y se rechaza la contraseña compartida anterior. Comprobación: `npm run cuentas:test-integracion`
  - Aceptación / estática: El flujo de comprobaciones de CI ejecuta las suites de SP-1 contra su servicio de Postgres y falla cuando se inicia una compilación con AUTH_LOCAL_SIN_RESTRICCIONES configurada. Comprobación: `npm run cuentas:test-integracion -- --solo-ci`

- [ ] T1.8 — Auditoría de seguridad de SP-1: cuentas, sesiones, permisos, modo local y comandos de un solo uso · repositorio: pictures · después de: T1.7 · verificar: `bitacora.py audit-ledger check .evidence/REQ-021/SP-1.findings.json` · archivos: .evidence/REQ-021/SP-1.audit.md, .evidence/REQ-021/SP-1.findings.json · recursos: ledger:SP-1 · cubre: R1, R2, R3, R16 · tipo: auditoría · subplan: SP-1

  Clasificación: complejidad alta; alcance small_change; riesgo alto; acoplamiento medio; confianza media; estimación: 90 minutos.
  Comprueba, como mínimo: los tokens y las contraseñas nunca se registran en logs ni se almacenan sin cifrar; las comparaciones son seguras frente a ataques de temporización; el bloqueo no se puede eludir usando mayúsculas o espacios en el correo electrónico; los enlaces son de un solo uso incluso con solicitudes concurrentes; cada route.ts y page.tsx está asignado y protegido; las excepciones de autenticación propia no cambian; el modo local no se puede activar en ninguna compilación, inicio o despliegue e ignora encabezados Host falsificados; `primer-admin` no puede crear un segundo administrador; eliminar una cuenta borra sus datos personales. Cada defecto confirmado indica la tarea que debe rehacerse.

  - Aceptación / estática: Una auditoría de seguridad independiente de SP-1 registra cada defecto confirmado con la tarea que debe rehacerse en el registro de hallazgos de SP-1, y el registro no tiene hallazgos críticos o altos abiertos. Comprobación: `bitacora.py audit-ledger check .evidence/REQ-021/SP-1.findings.json`

<!-- /SP-1 tasks -->

- **SP-2 — Pantallas de inicio de sesión, invitación y administración** (UI: `cuentas-admin@v1`): Una persona inicia sesión con correo electrónico y contraseña, activa un enlace de invitación y acepta el aviso sobre el tratamiento de datos; un administrador invita a personas, les asigna un rol o plan de acceso, crea roles seleccionando permisos y desactiva o elimina cuentas. Cubre R1, R3, R16.

<!-- SP-2 tasks -->

  Tareas de SP-2 (borrador pendiente de confirmación del propietario). Las pantallas siguen el contrato `cuentas-admin@v1` del Diseñador una vez que el propietario lo apruebe. Solo el Administrador gestiona usuarios y roles (ronda 6, pregunta 2). Las pantallas se escriben ahora en español, con todas las cadenas de texto en un módulo por pantalla para que SP-8/SP-10 las traduzcan; el aviso sobre el tratamiento de datos se publica en español e inglés desde el inicio (ronda 5, pregunta 6).
  DAG: T2.1 (diseño) ∥ T2.2 (API, después de session-guard T1.4 de SP-1) → {T2.3, T2.4, T2.5} (UI) → T2.6 (integración) → T2.7 (revisión visual) → T2.8 (auditoría). Consume account-service@1, session-guard@1 y permission-map@1 de SP-1; la barrera de composición CG-1 comprueba SP-1 y SP-2 juntos en el árbol integrado de M1.

- [ ] T2.1 — Copiar al repositorio el contrato cuentas-admin@v1 aprobado por el propietario · repositorio: pictures · después de: T1.4 · verificar: `test -s design/contracts/cuentas-admin@v1.md` · archivos: design/contracts/cuentas-admin@v1.md · recursos: design:cuentas-admin@v1 · cubre: R1, R3, R16 · tipo: diseño · subplan: SP-2 · ui: no

  Clasificación: complejidad baja; alcance isolated_fix; riesgo bajo; acoplamiento medio; confianza alta; estimación: 10 minutos.
  El planificador proporciona el borrador aprobado para el plan; la tarea lo copia sin cambios.

  - Aceptación / estática: El contrato cuentas-admin@v1 aprobado por el propietario se copia byte por byte en design/contracts/cuentas-admin@v1.md. Comprobación: `test -s design/contracts/cuentas-admin@v1.md`

- [ ] T2.2 — API de cuentas: activación, restablecimiento, aceptación del aviso, cambio de contraseña propia y administración de cuentas y roles · repo: pictures · después de: T1.4 · verificar: `npm run cuentas:test-api -- --test-name-pattern=enlaces` · archivos: src/lib/cuentas/aviso-datos.ts, src/app/api/cuentas/activar/route.ts, src/app/api/cuentas/restablecer/route.ts, src/app/api/cuentas/aviso/route.ts, src/app/api/cuentas/mi-cuenta/route.ts, src/app/api/admin/cuentas/route.ts, src/app/api/admin/cuentas/[id]/route.ts, src/app/api/admin/roles/route.ts, src/app/api/admin/roles/[id]/route.ts, src/lib/cuentas/dependientes.ts, src/lib/cuentas/regenerar-enlace.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-cuentas-api.ts · recursos: scripts de package.json, contract:account-service, contract:session-guard · cubre: R1, R3, R16 · tipo: implementación · subplan: SP-2 · ui: no

  Clasificación: complejidad media; alcance cambio grande; riesgo alto; acoplamiento alto; confianza media; estimación 120 minutos.
  `aviso-datos.ts` exporta `AVISO_DATOS = { version: 1, es, en }` con el texto de la SPEC «Aviso sobre el tratamiento de datos» literalmente, incluidos los marcadores de posición. Rutas: `POST /api/cuentas/activar` {token, contrasena, versionAviso}; `POST /api/cuentas/restablecer` {token, contrasena}; `GET /api/cuentas/activar?token=` devuelve el nombre y el correo electrónico solo para una invitación válida; `POST /api/cuentas/aviso` acepta la versión actual para la cuenta de la sesión; `PATCH /api/cuentas/mi-cuenta` {actual, nueva} (el servicio de SP-1 revoca todas las sesiones de la cuenta; luego, la ruta abre una sesión nueva para el navegador solicitante). Administración (`cuentas.administrar`): `GET/POST /api/admin/cuentas` (lista con búsqueda y filtros; invitar), `PATCH/DELETE /api/admin/cuentas/[id]` (rol, estado, enlace de restablecimiento; para eliminar, `confirmarCorreo` debe coincidir con el correo electrónico). Roles (`roles.administrar`): `GET/POST /api/admin/roles`, `PATCH/DELETE /api/admin/roles/[id]`. Todas las operaciones de modificación mantienen `isSameOriginRequest`; los errores usan códigos estables (`LINK_INVALIDO`, `CORREO_REGISTRADO`, `ULTIMO_ADMIN`, `ROL_EN_USO`, `ROL_SISTEMA`).
  Regla de eliminación (propietario, ronda 7 q1): `src/lib/cuentas/dependientes.ts` exporta un registro de tablas que contienen el trabajo guardado de una cuenta (vacío aquí; SP-4 agrega proyectos y SP-5 agrega decoraciones guardadas); `DELETE /api/admin/cuentas/[id]` rechaza la solicitud con `CUENTA_CON_TRABAJO` cuando alguna tabla registrada contiene una fila de la cuenta, por lo que esas cuentas solo se desactivan. Las filas de gasto de IA (SP-6) nunca se consideran trabajo: conservan sus totales, con la referencia a la cuenta establecida en null, y muestran «Cuenta eliminada». Ronda 8: `regenerar-enlace.ts` revoca todos los enlaces sin usar del mismo tipo para la cuenta y genera uno nuevo (`POST /api/admin/cuentas/[id]` acción `enlace-nuevo`, para cuentas invitadas y para restablecimientos); los roles personalizados necesitan al menos un permiso (`ROL_SIN_PERMISOS`, validado en el esquema de la API); `POST /api/cuentas/activar` inicia la sesión con `crearSesion` de SP-1 y devuelve el primer destino permitido. La ruta de aceptación del aviso también permite volver a aceptarlo cuando aumenta `AVISO_DATOS.version` (ronda 7 q3). El mapa de T1.2 incorpora las rutas nuevas (públicas: activar, restablecer; sesion: aviso, mi-cuenta). El script de npm `cuentas:test-api` = `tsx --conditions=react-server --test scripts/test/test-cuentas-api.ts`.

  - Aceptación / funcional: Las API de activación, restablecimiento y aceptación del aviso aceptan solo un token válido sin usar o una sesión iniciada, validan todos los cuerpos, responden a un enlace usado o vencido con LINK_INVALIDO sin especificar cuál es el problema, y una activación exitosa inicia una sesión de inmediato. Comprobar: `npm run cuentas:test-api -- --test-name-pattern=enlaces`
  - Aceptación / funcional: Las API de administración de cuentas y roles rechazan a quien no tenga el permiso de usuarios o de roles con 403 y aceptan solo solicitudes del mismo origen con cuerpos validados. Comprobar: `npm run cuentas:test-api -- --test-name-pattern=admin`
  - Aceptación / funcional: Generar un enlace nuevo de invitación o restablecimiento para una cuenta invalida todos los enlaces anteriores sin usar del mismo tipo para esa cuenta, y se rechaza un rol personalizado sin permisos con ROL_SIN_PERMISOS. Comprobar: `npm run cuentas:test-api -- --test-name-pattern=regenerar`
  - Aceptación / funcional: Cambiar la contraseña propia requiere la contraseña actual, finaliza todas las sesiones de esa cuenta e inicia de nuevo la sesión del navegador solicitante con una sesión nueva. Comprobar: `npm run cuentas:test-api -- --test-name-pattern=mi-cuenta`
  - Aceptación / funcional: El aviso sobre el tratamiento de datos existe en español e inglés con un número de versión, sus marcadores de posición entre corchetes siguen marcados para revisión legal, y al aceptarlo se guardan la versión y la fecha en la cuenta. Comprobar: `npm run cuentas:test-api -- --test-name-pattern=aviso`
  - Aceptación / funcional: Se rechaza la eliminación de una cuenta propietaria de alguna fila en una tabla registrada como trabajo de cuenta con CUENTA_CON_TRABAJO y no se modifica nada; al eliminar una cuenta sin trabajo guardado, se elimina y se conservan sus filas de gasto de IA sin datos personales. Comprobar: `npm run cuentas:test-api -- --test-name-pattern=borrar`

- [ ] T2.3 — Pantallas de inicio de sesión, activación de invitación, restablecimiento de contraseña y nueva aceptación del aviso · repo: pictures · después de: T2.1, T2.2 · verificar: `npm run cuentas:test-ui-acceso -- --solo ingreso` · archivos: src/app/login/page.tsx, src/app/login/LoginForm.tsx, src/app/activar/[token]/page.tsx, src/app/restablecer/[token]/page.tsx, src/app/aviso-datos/page.tsx, src/components/cuentas/FormularioContrasena.tsx, src/components/cuentas/AvisoDatos.tsx, src/components/cuentas/textos-acceso.ts, src/proxy.ts, scripts/test/test-ui-acceso.ts · recursos: scripts de package.json, contract:session-guard · cubre: R1 · tipo: implementación · subplan: SP-2 · ui: sí

  Clasificación: complejidad media; alcance funcionalidad completa; riesgo alto; acoplamiento medio; confianza media; estimación 150 minutos.
  Las cadenas de texto están en `textos-acceso.ts` (por ahora en español, con claves listas para SP-8). El aviso se muestra en el idioma del navegador (`Accept-Language`: en → inglés; de lo contrario, español). El proxy redirige a `/aviso-datos?from=` la sesión cuya cuenta aceptó una versión anterior del aviso, antes de abrir cualquier página excepto la de cierre de sesión. Después de iniciar sesión, el destino es `from` si está permitido; de lo contrario, se usa la primera opción permitida entre Taller 3D, chat y catálogo; si ninguna está permitida, se usa `/cuenta` (todas las cuentas activas pueden abrirla). La pantalla de inicio de sesión nunca indica que un correo electrónico está bloqueado: SP-1 devuelve un único rechazo genérico y el mensaje siempre agrega la indicación de esperar quince minutos. El script de npm `cuentas:test-ui-acceso` = `tsx scripts/test/test-ui-acceso.ts` (renderizado en el servidor de todos los estados y una ejecución con Playwright en un servidor de desarrollo contra el esquema aislado).

  - Aceptación / funcional: En /login, una persona inicia sesión con correo electrónico y contraseña; una contraseña incorrecta, un correo electrónico desconocido, una cuenta desactivada y un correo electrónico bloqueado muestran el mismo mensaje, que siempre indica que, después de varios intentos fallidos, se deben esperar quince minutos; si el inicio de sesión es exitoso, se vuelve a la página solicitada o a la primera área permitida por el rol, o a Mi cuenta cuando el rol no permite ninguna de ellas. Comprobar: `npm run cuentas:test-ui-acceso -- --solo ingreso`
  - Aceptación / funcional: Al abrir un enlace de invitación, se muestran el nombre y el correo electrónico de la persona invitada, se solicita ingresar dos veces una contraseña de al menos ocho caracteres y se muestra el aviso sobre el tratamiento de datos en el idioma del navegador con una casilla de aceptación; no se puede activar la cuenta sin aceptar el aviso y, después de activarla, la persona llega con la sesión iniciada a la primera herramienta permitida por su rol; si el enlace ya se usó o venció, se muestra un mensaje para solicitar uno nuevo al administrador. Comprobar: `npm run cuentas:test-ui-acceso -- --solo activacion`
  - Aceptación / funcional: Al abrir un enlace de restablecimiento, la persona puede establecer una contraseña nueva y luego iniciar sesión; si el enlace ya se usó o venció, se muestra el mismo mensaje que para una invitación no válida. Comprobar: `npm run cuentas:test-ui-acceso -- --solo restablecer`
  - Aceptación / funcional: Cuando cambia la versión del aviso, la persona con la sesión iniciada debe aceptar la versión nueva antes de que se abra cualquier otra página. Comprobar: `npm run cuentas:test-ui-acceso -- --solo aviso`

- [ ] T2.4 — Menú de cuenta en todas las páginas con sesión iniciada y página Mi cuenta · repo: pictures · después de: T2.1, T2.2 · verificar: `npm run cuentas:test-ui-mi-cuenta` · archivos: src/components/cuentas/MenuCuenta.tsx, src/app/layout.tsx, src/app/cuenta/page.tsx, src/components/cuentas/textos-cuenta.ts, scripts/test/test-ui-mi-cuenta.ts · recursos: scripts de package.json, contract:session-guard · cubre: R1 · tipo: implementación · subplan: SP-2 · ui: sí

  Clasificación: complejidad media; alcance cambio pequeño; riesgo medio; acoplamiento medio; confianza media; estimación 75 minutos.
  El diseño raíz lee la sesión en el servidor y muestra `MenuCuenta` solo en las páginas con sesión iniciada, en la ubicación definida por el contrato. El script de npm `cuentas:test-ui-mi-cuenta` = `tsx scripts/test/test-ui-mi-cuenta.ts`.

  - Aceptación / funcional: Todas las páginas con sesión iniciada muestran un menú de cuenta con el nombre y el rol de la persona, Mi cuenta y cerrar sesión; en Mi cuenta se cambia la contraseña ingresando la actual. Comprobar: `npm run cuentas:test-ui-mi-cuenta`

- [ ] T2.5 — Pantallas de administración: lista de cuentas, invitaciones, acciones de cuenta y editor de roles · repo: pictures · después de: T2.1, T2.2 · verificar: `npm run cuentas:test-ui-admin -- --solo lista` · archivos: src/app/admin/cuentas/page.tsx, src/app/admin/roles/page.tsx, src/components/admin/cuentas/ListaCuentas.tsx, src/components/admin/cuentas/DialogoInvitar.tsx, src/components/admin/cuentas/AccionesCuenta.tsx, src/components/admin/cuentas/EditorRol.tsx, src/components/admin/cuentas/textos-admin-cuentas.ts, src/components/admin/AdminTabs.tsx, scripts/test/test-ui-admin-cuentas.ts · recursos: scripts de package.json, contract:permission-map · cubre: R1, R3, R16 · tipo: implementación · subplan: SP-2 · ui: sí

  Clasificación: complejidad media; alcance funcionalidad completa; riesgo alto; acoplamiento medio; confianza media; estimación 180 minutos.
  Los enlaces de invitación y restablecimiento se muestran una sola vez, con un botón para copiarlos y un aviso de que no volverán a mostrarse. Las casillas de permisos se obtienen de `permisos.ts` junto con sus etiquetas, agrupadas por herramienta. Los enlaces a ambas pantallas solo aparecen para las cuentas que tienen el permiso correspondiente. El script de npm `cuentas:test-ui-admin` = `tsx scripts/test/test-ui-admin-cuentas.ts`.

  - Aceptación / funcional: Un administrador ve todas las cuentas con nombre, correo electrónico, empresa, rol, estado y último acceso; puede buscar por nombre o correo electrónico y filtrar por rol y estado. Comprobar: `npm run cuentas:test-ui-admin -- --solo lista`
  - Aceptación / funcional: Un administrador invita a una persona ingresando su nombre, correo electrónico, empresa opcional y rol, y obtiene una sola vez el enlace de un solo uso con un botón para copiarlo; se rechaza un correo electrónico ya registrado con un mensaje claro. Comprobar: `npm run cuentas:test-ui-admin -- --solo invitar`
  - Aceptación / funcional: Un administrador cambia el rol de una cuenta, la desactiva y la reactiva, genera un enlace de restablecimiento y elimina una cuenta sin trabajo guardado después de ingresar su correo electrónico; la pantalla explica por qué no se puede eliminar al último administrador ni a una cuenta con trabajo guardado. Comprobar: `npm run cuentas:test-ui-admin -- --solo acciones`
  - Aceptación / funcional: Un administrador crea y edita un rol personalizado por nombre y mediante casillas de permisos agrupadas por herramienta, ve los cinco roles del sistema en modo de solo lectura con sus permisos y no puede eliminar un rol que aún tenga cuentas asignadas. Comprobar: `npm run cuentas:test-ui-admin -- --solo roles`

- [ ] T2.6 — Browser end-to-end: invite, activate, sign in and change plan on a production build · repo: pictures · after: T2.3, T2.4, T2.5 · verify: `npm run cuentas:test-integracion-ui` · files: scripts/test/test-integracion-cuentas-ui.ts, .evidence/REQ-021/SP-2.integration.json · resources: package.json scripts · covers: R1, R3, R16 · kind: test · subplan: SP-2

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 90 minutes.
  Seeds one Administrador in the isolated schema, builds and starts the app, drives the administrator browser to invite a Plan 2 person and read the link, opens it in a second context, activates with the notice, signs in, checks chat and costs open and /3d does not, changes the role to Plan 3 in the first browser and reloads /3d in the second. npm script `cuentas:test-integracion-ui` = `tsx scripts/test/test-integracion-cuentas-ui.ts`.

  - Acceptance / integration: On a production build against the REQ-021 test database, an administrator invites a Plan 2 person through the screens, the person activates the link in a separate browser, accepts the notice, signs in and reaches the chat and the costs tool but not the Taller 3D, and after the administrator moves them to Plan 3 their next request opens the Taller. Check: `npm run cuentas:test-integracion-ui`

- [ ] T2.7 — SP-2 visual review against the cuentas-admin@v1 contract · repo: pictures · after: T2.6 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.visual.findings.json` · files: .evidence/REQ-021/SP-2.visual.md, .evidence/REQ-021/SP-2.visual.findings.json · resources: ledger:SP-2-visual · covers: R1, R3 · kind: audit · subplan: SP-2

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 60 minutes.
  Reviewer axis `visual` (rendered-ui-fidelity-audit).

  - Acceptance / static: The rendered sign-in, activation, account and administration screens match the approved cuentas-admin@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-2 visual ledger. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.visual.findings.json`

- [ ] T2.8 — SP-2 audit: account screens, administration APIs and the data notice · repo: pictures · after: T2.7 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.findings.json` · files: .evidence/REQ-021/SP-2.audit.md, .evidence/REQ-021/SP-2.findings.json · resources: ledger:SP-2 · covers: R1, R3, R16 · kind: audit · subplan: SP-2

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 75 minutes.
  Checks at least: admin APIs refuse without the permission and cross-origin; links shown once and never logged; generic sign-in errors; notice version stored; delete requires typing the email.

  - Acceptance / static: An independent audit of SP-2 records every confirmed defect with the task that must redo it in the SP-2 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.findings.json`

<!-- /SP-2 tasks -->

- **SP-3 — Taller essentials: rectangular tables, Backing and Blender export** (UI: `taller-esenciales@v1`): A user adds and edits a rectangular table with its size and chairs and the shopping list reflects it; the catalogue and the Taller show one Backing category with every existing party prop; the exported GLB opens in Blender with the same layout, sizes in metres and colours. Covers R9, R10, R11.

<!-- SP-3 tasks -->

  Draft behavior and task breakdown; round 9 choices are explicitly pending and must be resolved before confirmation. No focus change or approval is implied.

- [ ] T3.1 — Copy the approved Taller essentials design contract · repo: pictures · after: T1.8 · verify: `cmp -- design/contracts/taller-esenciales@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/taller-esenciales@v1.md` · files: design/contracts/taller-esenciales@v1.md · resources: design:T3.1 · covers: R9, R10, R11 · kind: design · subplan: SP-3 · ui: no

  Classification: complexity low; scope small_change; risk low; coupling medium; confidence medium; estimate 20 minutes.
  Copy the exact pinned owner-approved artifact without rewriting its content; compare SHA-256 with that approved source.

  - Acceptance / static: The repository contract is byte-identical to the owner-approved taller-esenciales@v1 artifact. Check: `cmp -- design/contracts/taller-esenciales@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/taller-esenciales@v1.md`

- [ ] T3.2 — Add rectangular tables through the existing table editor · repo: pictures · after: T3.1 · verify: `npx tsx scripts/test/test-taller-mesas-piloto.ts` · files: src/components/tres-d/FondosYMuebles.tsx, src/components/tres-d/EditorConjuntoMesa.tsx, src/lib/globos3d/mobiliario-conjunto-escena.ts, src/components/tres-d/textos-taller-esenciales.ts, scripts/test/test-taller-mesas-piloto.ts · resources: taller:scene, taller:scene · covers: R9 · kind: implement · subplan: SP-3 · ui: yes

  Classification: complexity medium; scope full_feature; risk medium; coupling medium; confidence low; estimate 110 minutes.
  Pending round 9 q1/q2: proposed one card per existing parametric type, default values from PARTIDA_MESA (rectangular 240 × 90 × 75 cm), then the existing inspector. Do not invent an Imperial parametric type; existing catalogue Imperial pieces remain. Alternative q1=b requires a pre-creation form instead. Shopping list proposal: quantities and dimensions, no invented rental price.
  Reuse mesaDePedido, agregarConjuntoPorDefecto extended with a typed request, EditorConjuntoMesa and chair placement. Keep cm in the model and metres in the UI; rectangular limits 100–600 cm length, 40–150 cm depth, 40–110 cm height; chairs 0–40, actual capacity controls the list. Preserve supported dispositions, parent transforms and objects on the table; refuse MAX_NODOS overflow without half a table.
  Implement and register taller:test-mesas-piloto = tsx scripts/test/test-taller-mesas-piloto.ts; test creation, limits, requested versus placed chairs, movement/rotation, undo and deterministic tool parity. Strings in textos-taller-esenciales.ts for later translation.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.

  - Acceptance / functional: Adding a rectangular table exposes length, depth and chair count, selects it in the inspector and updates the real shopping list with placed chairs, including capacity warnings and undo. Check: `npx tsx scripts/test/test-taller-mesas-piloto.ts`
  - Acceptance / functional: The existing agregar_mesas, cambiar_mesas and cambiar_sillas tools produce the same table dimensions and actual chair counts as manual editing without a paid AI call. Check: `npx tsx scripts/test/test-taller-mesas-piloto.ts`

- [ ] T3.3 — Group existing party props under Backing without changing their identities · repo: pictures · after: T3.2 · verify: `npx tsx scripts/test/test-backing-piloto.ts` · files: src/components/tres-d/FondosYMuebles.tsx, src/lib/catalogo/backing.ts, src/components/tres-d/textos-taller-esenciales.ts, scripts/test/test-backing-piloto.ts · resources: taller:scene, taller:scene · covers: R11 · kind: implement · subplan: SP-3 · ui: yes

  Classification: complexity medium; scope full_feature; risk medium; coupling medium; confidence low; estimate 80 minutes.
  Pending round 9 q3: proposed presentation group in the Taller Fondos y muebles, not Shopify /catalogo. Keep semantic GrupoCatalogo and ASIGNACION_FONDOS unchanged: compute a display grouping from the explicit seven-ID set so RAG and photo readers do not need recategorization. If the owner wants aliases, support both presentation entries without duplicate IDs in scene state.
  Update search and panel counters together; searching Backing finds all seven, original names still find each, and escenografia/mobiliario repository filters keep ownership. Preserve adding by click, drag and keyboard. Register taller:test-backing-piloto; compare all before/after IDs, original search terms, addability and repository consistency. Do not add imaginary Shopify products or prices.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.

  - Acceptance / functional: Backing lists panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico, each addable; existing IDs, saved scenes, repository ownership, search and AI/photo discovery remain compatible. Check: `npx tsx scripts/test/test-backing-piloto.ts`

- [ ] T3.4 — Verify and repair the GLB geometry and material export · repo: pictures · after: T3.3 · verify: `npx tsx scripts/test/test-exportadores-escena-taller.ts` · files: src/components/tres-d/exportar-escena-glb.ts, src/components/tres-d/exportadores-escena-globos.ts, src/components/tres-d/ExportarEscenaTaller.tsx, scripts/test/test-exportadores-escena-taller.ts, scripts/test/fixtures/req021-export-scene.json · resources: taller:scene · covers: R10 · kind: implement · subplan: SP-3 · ui: yes

  Classification: complexity high; scope full_feature; risk medium; coupling medium; confidence low; estimate 140 minutes.
  Extend existing exporter tests with a deterministic real-scene fixture: translated/rotated rectangular table and chairs, Backing, balloons with distinct colours/finishes, nested attachments and room. Decode GLB accessors and transforms; do not test only the magic header or a synthetic group. Compare model-space cm converted once to metres, all world bounds/positions within 1 mm and base-colour channels within 1/255 in the same colour space.
  Keep editor-only lights/gizmos out, retain intended room visibility and instancing where the importer supports it. A real Blender importer must decide whether EXT_mesh_gpu_instancing or material extensions need a compatibility path; preserve the source scene and document any appearance limitation. No claim of identical lighting/rendering.

  - Acceptance / functional: The exported GLB preserves actual scene world transforms, dimensions in metres, visible instances and base colours without mutating the editor or calling the network; export failure is visible and retryable. Check: `npx tsx scripts/test/test-exportadores-escena-taller.ts`

- [ ] T3.5 — Implement the Taller browser and Blender verification harness · repo: pictures · after: T3.4 · verify: `npm run taller:test-harness-esenciales` · files: scripts/test/test-integracion-taller-esenciales.ts, scripts/test/blender/verificar_glb.py, scripts/test/test-harness-taller-esenciales.ts, docs/req021-blender.md, package.json · resources: package.json scripts, taller:scene · covers: R9, R10, R11 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity high; scope full_feature; risk medium; coupling medium; confidence low; estimate 120 minutes.
  Author scripts and npm commands taller:test-harness-esenciales (deterministic harness tests) and taller:test-integracion-esenciales (real flow). Pin an explicit Blender LTS version and checksum only after round 9 q4 resolves acquisition; no installation is authorized by this draft. BLENDER_EXECUTABLE is an optional location, never download implicitly. Blender option b leaves automated GLB checks plus a documented owner Blender import attestation; do not report a missing importer as success.
  Use SP-1 isolated-schema and session fixtures, no paid AI and no production access. Build/start on loopback, create a table through UI, adjust size/chairs, add each Backing prop and download the scene GLB. Blender runs background with bounded timeout, opens that downloaded file, verifies evaluated world-space instances, orientation, bounds and base colours at the T3.4 tolerances and records importer/version/limitations. Output .evidence/REQ-021/SP-3.integration.json with source revision, exact command and measurements. Clean up server/schema in finally. Package scripts register T3.2/T3.3 test commands here before T3.6 runs; local implementation checks may invoke tsx directly until registration.
  Own package.json registration for all new SP-3 npm aliases. Preserve scripts registered by other subplans.
  Also author taller:test-composicion-esenciales, the same real entrypoint flow with a Plan 3 session and an unauthorized Plan 1 direct API request; record .evidence/REQ-021/CG-2.integration.json on the integrated candidate.

  - Acceptance / functional: The harness starts a real next start build, drives table and Backing operations in Chromium, downloads the actual GLB and compares Blender-imported positions, metre dimensions and base colours against the fixture; missing Blender is reported as blocked. Check: `npm run taller:test-harness-esenciales`

- [ ] T3.6 — Run the real Taller essentials integration scenario · repo: pictures · after: T3.5 · verify: `npm run taller:test-integracion-esenciales` · files: .evidence/REQ-021/SP-3.integration.json · resources: taller:scene · covers: R9, R10, R11 · kind: test · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 50 minutes.
  Execute the already-authored harness only; report failures without repairing source in this task. The owner manual Blender check in SPEC Pruebas is separate product evidence.

  - Acceptance / integration: A user adds and edits a rectangular table with its size and chairs and the shopping list reflects it; the catalogue and the Taller show one Backing category with every existing party prop; the exported GLB opens in Blender with the same layout, sizes in metres and colours. Check: `npm run taller:test-integracion-esenciales`
  - Acceptance / integration: A production build on loopback completes the real table-to-Backing-to-GLB flow, recording Blender import evidence or an explicit external block; no unexecuted check is reported as passed. Check: `npm run taller:test-integracion-esenciales`

- [ ] T3.7 — Review rendered Taller essentials against the design · repo: pictures · after: T3.6 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-3.visual.findings.json` · files: .evidence/REQ-021/SP-3.visual.md, .evidence/REQ-021/SP-3.visual.findings.json · resources: ledger:T3.7 · covers: R9, R10, R11 · kind: audit · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 60 minutes.
  Independent rendered visual review, including keyboard/focus, capacity warning, loading/error export and both themes. Reference the integration evidence and exact source tree.

  - Acceptance / static: Phone, tablet and desktop renderings of table creation/editing, Backing and export states match the approved taller-esenciales@v1 contract, with actionable findings mapped to their owning tasks. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-3.visual.findings.json`

- [ ] T3.8 — Audit Taller essentials and export compatibility · repo: pictures · after: T3.7 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-3.findings.json` · files: .evidence/REQ-021/SP-3.audit.md, .evidence/REQ-021/SP-3.findings.json · resources: ledger:T3.8 · covers: R9, R10, R11 · kind: audit · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 90 minutes.
  Review R9/R10/R11, old furniture IDs, correct actual-chair shopping counts, instance/transform/material importer behavior, no paid calls, and task-local regressions. Run repository lint, workspace builds, application types and build plus affected existing furniture/export scripts as required by AGENTS.md; retain baseline failures separately.

  - Acceptance / static: An independent SP-3 spec and standards audit has no open critical or high findings, maps each defect to its introducing task and distinguishes GLB structural evidence from real Blender and owner evidence. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-3.findings.json`

<!-- /SP-3 tasks -->


<!-- CG-1 tasks -->

  Composition gate CG-1: SP-1, SP-2.

- [ ] T91 — M1 composition check: first administrator to a Plan 1 user on the integrated tree · repo: pictures · after: T1.8, T2.8 · verify: `npm run m1:test-composicion` · files: scripts/test/test-composicion-m1.ts, .evidence/REQ-021/CG-1.integration.json · resources: package.json scripts · covers: R1, R2, R16 · kind: test

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 60 minutes.
  Reuses the helpers of T1.7 and T2.6; npm script `m1:test-composicion` = `tsx scripts/test/test-composicion-m1.ts`.

  - Acceptance / integration: On the integrated M1 tree started with next start against the REQ-021 test database, cuentas:primer-admin creates an administrator who activates through the activation screen, invites a Plan 1 person who activates and signs in, and that person reaches the chat and the catalogue but gets the no-access page on the Taller 3D and 403 on its APIs. Check: `npm run m1:test-composicion`

<!-- /CG-1 tasks -->

<!-- CG-2 tasks -->

  Composition of accepted subplans on the integrated candidate.

- [ ] T92 — Composition check CG-2: accounts and Taller essentials · repo: pictures · after: T91, T3.8 · verify: `npm run taller:test-composicion-esenciales` · files: .evidence/REQ-021/CG-2.integration.json · resources: candidate:CG-2 · covers: R2, R9, R10, R11 · kind: test · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  Execute the composition mode authored by T3.5 on the integrated candidate. Record candidate/tree identity; no harness authoring or repairs here.

  - Acceptance / integration: The integrated candidate passes Plan 3 table, Backing and GLB operations and Plan 1 direct access denial. Check: `npm run taller:test-composicion-esenciales`

<!-- /CG-2 tasks -->

### M2 — Saved work, spend per user and the chat tools
Each signed-in user saves and reopens projects and decorations from any browser, every paid AI call is attributed to a user and a session, and the assisted chat is three separate tools gated by access plan.

- **SP-4 — Saved projects** (UI: `proyectos@v1`): A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss. Covers R6, R7.

<!-- SP-4 tasks -->

  Draft behavior and task breakdown; round 9 choices are explicitly pending and must be resolved before confirmation. No focus change or approval is implied.

- [ ] T4.1 — Copy the approved saved-projects design contract · repo: pictures · after: T92 · verify: `cmp -- design/contracts/proyectos@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.md` · files: design/contracts/proyectos@v1.md · resources: design:T4.1 · covers: R6, R7 · kind: design · subplan: SP-4 · ui: no

  Classification: complexity low; scope small_change; risk low; coupling medium; confidence medium; estimate 20 minutes.
  Copy the pinned owner-approved contract without rewriting it.

  - Acceptance / static: The repository contract is byte-identical to the owner-approved proyectos@v1 artifact. Check: `cmp -- design/contracts/proyectos@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.md`

- [ ] T4.2 — Implement versioned project storage and scene validation · repo: pictures · after: T4.1 · verify: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts` · files: scripts/migrations/038_proyectos.sql, src/lib/proyectos/contrato.ts, src/lib/proyectos/servicio.ts, src/lib/proyectos/repositorio.ts, src/lib/proyectos/validar-escena.ts, src/lib/cuentas/dependientes.ts, scripts/test/test-proyectos-servicio.ts · resources: proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: no

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 170 minutes.
  Use getRagPool and SP-1 isolated schema helper. Migration 038 creates proyectos with UUID id, owner FK RESTRICT, name, schema_version=1, JSONB scene, revision >=1 and created/updated timestamps plus owner/update index. Register it as work in dependientes.ts. Name trimmed 1–120 characters, document UTF-8 limit 2 MiB; enforce existing MAX_NODOS=150 and room limits, complete Pieza variants and references using runtime validation, never the shallow legacy type guard as server validation. Unsupported schema is a stable recoverable error; do not silently drop fields or normalize away user work.
  Update WHERE id AND owner_id AND revision; increment in same statement, zero rows on stale yields conflict. For create/retry use client mutation UUID unique per account, reject different content under reused key; imports additionally use a unique account+raw-source SHA-256. Lock the owner row in the write transaction with a lock mode conflicting with deletion; FK RESTRICT is the final barrier so delete cannot erase work even if registry precheck races. Service derives caller identity from trusted session context; no client owner id. Proposal pending q6: document is name + complete Escena (including salon, room, materials and attachments), not conversation/media. Extra scope needs a plan revision after response.
  Expose project-document@1: {schemaVersion:1, nombre, escena}; stored result adds id, ownerId, revision and timestamps. Register proyectos:test-servicio = tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts. Tests cover migrations twice, cross-account ownership, CAS race, idempotency, validation, rollback and delete race.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.
  Migration 038 also creates account-scoped mutation receipts and legacy-import receipts: UNIQUE(account_id, mutation_id) binds payload SHA-256 and committed project/revision; UNIQUE(account_id, raw_source_sha256) binds one imported project. A repeated identical create/update returns the committed receipt without another write or revision increment; a reused key with different payload fails. Import receipt and project insert commit together; do not rely on browser-only markers. Receipts are included in account-work cleanup/constraints and are not exposed across accounts.

  - Acceptance / functional: A project is stored in Postgres under the session account with a versioned complete scene document; conditional updates atomically increment revision and reject stale writes without changing stored data. Check: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts`
  - Acceptance / functional: Account deletion is refused when projects exist, including a project-save/account-delete race; malformed or oversized documents, duplicate node IDs, nonfinite dimensions and broken or cyclic parent links are refused without writes. Check: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts`

- [ ] T4.3 — Implement project APIs with per-resource authorization · repo: pictures · after: T4.2 · verify: `npm run proyectos:test-api` · files: src/app/api/proyectos/route.ts, src/app/api/proyectos/[id]/route.ts, src/lib/proyectos/http.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-proyectos-api.ts, package.json, scripts/test/test-checkpoint-proyectos.ts · resources: package.json scripts, proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: no

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 100 minutes.
  GET /api/proyectos?cursor= returns paginated metadata only (50 max, updatedAt/id ordering); scope=all requires proyectos.ver_todos and includes owner display identity. GET /api/proyectos/[id] returns authorized document. POST /api/proyectos creates for the session account (also used for Save copy/import). PATCH /api/proyectos/[id] requires baseRevision and mutationId. Proposed round 9 q7: foreign reads only, copy becomes caller-owned; no foreign edit or transfer. If owner selects shared editing, replan write authorization and authorship before implementation.
  Route permission map: own project routes require taller.usar; read-all may be allowed to proyectos.ver_todos even for custom roles without taller.usar, and the service checks resource ownership independently. Same-origin guard for mutations, schema validation on every request, no-store responses; invalid JSON 400, unauthenticated 401, unauthorized collection scope 403, inaccessible/missing item 404, stale revision 409, too large 413. No deletion UI/API in this pilot draft; it is not required by R6/R7. Register proyectos:test-api using real isolated database and Request-based route tests.
  Author proyectos:test-checkpoint = tsx --conditions=react-server scripts/test/test-checkpoint-proyectos.ts: start next start on loopback against the isolated schema and run real HTTP ownership/CAS/delete-race checks, emitting SP-4.storage.json. No import-only check is called integration.

  - Acceptance / functional: Project APIs list and read only owned projects unless proyectos.ver_todos is granted, refuse unauthorized writes and cross-origin mutations, and return stable version conflicts without leaking another owner document. Check: `npm run proyectos:test-api`

- [ ] T4.31 — Run the project storage and authorization checkpoint · repo: pictures · after: T4.3 · verify: `npm run proyectos:test-checkpoint` · files: .evidence/REQ-021/SP-4.storage.json · resources: proyectos:document · covers: R6, R7 · kind: test · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence medium; estimate 35 minutes.
  Execute the checkpoint runner authored by T4.3 against the isolated database; write exact observed API/database outcomes and tree identity. Stop downstream UI work on failure; no source repairs in this task.

  - Acceptance / integration: Before UI work, the real project service and API checks pass atomic stale-write rejection, account isolation, validation, import retry keys and the project-save/account-delete race. Check: `npm run proyectos:test-checkpoint`

- [ ] T4.4 — Implement the project list and conflict-safe Taller saving · repo: pictures · after: T4.31 · verify: `npx tsx scripts/test/test-proyectos-cliente.ts` · files: src/app/proyectos/page.tsx, src/components/proyectos/ListaProyectos.tsx, src/components/proyectos/EstadoGuardado.tsx, src/components/proyectos/ConflictoProyecto.tsx, src/components/proyectos/useProyecto.ts, src/components/proyectos/textos-proyectos.ts, src/components/tres-d/Taller3D.tsx, src/app/3d/page.tsx, src/lib/proyectos/borrador-local.ts, scripts/test/test-proyectos-cliente.ts, src/app/proyectos/[id]/page.tsx · resources: proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: yes

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 180 minutes.
  Pending q5/q7: proposed initial explicit Save with name, then 500 ms debounced serialized autosave and explicit Save now; list route /proyectos and deep link /3d?proyecto=<uuid>. Staff all-project list can be read with proyectos.ver_todos; custom roles lacking taller.usar need a read-only project view, not a bypass that grants editing tools. Owner-only editable project route checks both permissions and ownership server-side.
  Keep one in-flight update per project, latest scene queued behind it, bind response to account+project+request identity and submitted edit generation. A response acknowledges only its submitted generation; older completions cannot clear newer dirty work. On 409 stop queue until explicit resolution; no automatic overwrite or retry with fetched revision. Network/401/permission failure retains a namespaced local draft and exposes retry. Switching/new project or navigation with dirty/pending edits asks to save, keep local draft or cancel; ignore completions for previous identity.
  Namespace new drafts by account and project; never auto-open the old global scene after account switch. On sign-out/auth loss clear scene state and query caches; a different account cannot enumerate/open drafts. Keep recovery drafts for the same account; do not delete original legacy data. Reset undo history and scene conversation identity on project switch; preserve the full document and do not silently attach another project conversation. Register proyectos:test-cliente with out-of-order replies, offline/reload, account switch and conflict reducer tests. UI states per proyectos@v1.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.
  Provide /proyectos/[id] as a server-authorized read-only scene view for proyectos.ver_todos without taller.usar; link staff reads there, never bypass the /3d Taller permission. Save copy also requires taller.usar. Register both project pages in the T4.3 permission map and test custom staff read-only access.

  - Acceptance / functional: The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`
  - Acceptance / functional: Two open copies cannot silently overwrite each other: a 409 stops autosaving, keeps the unsent local scene and offers loading the server version or saving a new owned copy; foreign projects follow the owner-approved editing rule. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`

- [ ] T4.5 — Implement a lossless and idempotent legacy-scene import · repo: pictures · after: T4.4 · verify: `npx tsx scripts/test/test-proyectos-importacion.ts` · files: src/lib/proyectos/importar-local.ts, src/components/proyectos/ImportarEscenaLocal.tsx, src/components/tres-d/guardado-escena.ts, src/components/proyectos/useProyecto.ts, scripts/test/test-proyectos-importacion.ts · resources: proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: yes

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 110 minutes.
  Read raw taller3d:escena:v1 before legacy leerGuardada can normalize/discard it. Show import on first authenticated Taller visit with legacy data, not in login handlers; an account without Taller access keeps it until access is granted. Not now is reversible via project list. Consent belongs to the current account; explain the browser scene may be from another person on shared devices. Do not upload until explicit consent.
  Validate complete supported legacy schema on server. Use account+SHA-256 of original raw bytes for durable idempotency, mapping to imported project in the create transaction; response loss/reload/double-click returns that same project. A different account sees a fresh explicit consent, never a prior import association. Keep the original legacy key unchanged even after success; store separate account-scoped import receipt only after server acknowledgement. Invalid/unknown-version data gets a recoverable explanation and raw JSON download, never empty-scene replacement. Do not depend on existing leerGuardada silently returning null. Register proyectos:test-importacion with malformed/old versions, denial, two tabs and interrupted response tests.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.

  - Acceptance / functional: A signed-in account with a legacy browser scene is offered an explicit import; acceptance creates exactly one owned project even after retry, refusal or validation failure preserves raw local data, and no account receives a legacy scene automatically. Check: `npx tsx scripts/test/test-proyectos-importacion.ts`

- [ ] T4.6 — Implement the multi-browser saved-project integration harness · repo: pictures · after: T4.5 · verify: `npm run proyectos:test-harness` · files: scripts/test/test-integracion-proyectos.ts, scripts/test/test-harness-proyectos.ts, package.json · resources: package.json scripts, proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: no

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 120 minutes.
  Author proyectos:test-harness and proyectos:test-integracion, no paid AI. Seed owner A/B, staff and administrator with SP-1 helpers; next build and next start loopback. A creates scene fixture with table, Backing, attachments, colours and room; fresh A context reopens and compares canonical document and computed scene counts. B attempts list/read/write guessed IDs (also direct API); staff opens A read-only and saves copy. Two A contexts start same revision: second write gets 409 and draft survives. Simulate lost create/import response and retry, malformed legacy data, then account switch and verify no scene disclosure.
  Emit .evidence/REQ-021/SP-4.integration.json with exact tree, commands, browser contexts, expected/observed version and access results, preserve screenshots for visual audit; teardown processes and isolated schema in finally. Use deterministic seeded fixture/test doubles only at paid-provider boundary, not persistence/auth APIs.
  Own package.json registration for remaining SP-4 aliases (service, client and import); preserve the checkpoint/API aliases already registered in T4.3.
  Also author proyectos:test-composicion, combining sign-in, a rectangular-table/Backing scene, project persistence, staff read/copy and deletion refusal on the integrated candidate; record .evidence/REQ-021/CG-3.integration.json.

  - Acceptance / functional: The project harness starts real Next entrypoints against an isolated test schema and drives independent authenticated browser contexts through persistence, access denial, conflicts and legacy import. Check: `npm run proyectos:test-harness`

- [ ] T4.7 — Run the cross-browser project and import integration scenario · repo: pictures · after: T4.6 · verify: `npm run proyectos:test-integracion` · files: .evidence/REQ-021/SP-4.integration.json · resources: proyectos:document · covers: R6, R7 · kind: test · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence medium; estimate 60 minutes.
  Run the existing T4.6 harness, record command-level evidence and failures; no source repair or acceptance verdict in this execution task.

  - Acceptance / integration: A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss. Check: `npm run proyectos:test-integracion`
  - Acceptance / integration: A real production build passes persistence across fresh browser contexts, per-account denial, staff read/copy, competing-save conflict, import retry and account-switch isolation checks on the REQ-021 database. Check: `npm run proyectos:test-integracion`

- [ ] T4.8 — Review the rendered project and import interfaces · repo: pictures · after: T4.7 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-4.visual.findings.json` · files: .evidence/REQ-021/SP-4.visual.md, .evidence/REQ-021/SP-4.visual.findings.json · resources: ledger:T4.8 · covers: R6, R7 · kind: audit · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence medium; estimate 75 minutes.
  Independent visual-axis review on rendered source; link screenshots, source identity and SP-4.integration.json. Map each mismatch to T4.4/T4.5 rather than blanket rework.

  - Acceptance / static: Project list, saving/offline/conflict states, foreign read-only view and import prompt match approved proyectos@v1 at phone, tablet and desktop widths with keyboard and focus behavior verified. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-4.visual.findings.json`

- [ ] T4.9 — Audit project isolation, concurrency and import preservation · repo: pictures · after: T4.8 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-4.findings.json` · files: .evidence/REQ-021/SP-4.audit.md, .evidence/REQ-021/SP-4.findings.json · resources: ledger:T4.9 · covers: R6, R7 · kind: audit · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling high; confidence medium; estimate 90 minutes.
  Review R6/R7 against accepted round 9 answers and source; challenge direct API bypass, metadata leakage, stale-response ordering, project-switch races, delete/save race and invalid legacy recovery. Run required lint, workspace builds, app types/build and affected existing scene tests; distinguish baseline defects and unavailable external resources from passes.

  - Acceptance / static: An independent SP-4 spec and standards audit has no open critical or high findings and verifies ownership, atomic version control, import idempotency and preservation, deletion registration and account-switch isolation. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-4.findings.json`

<!-- /SP-4 tasks -->

- **SP-5 — Saved decorations** (UI: `decoraciones@v1`): A user saves a selection or composition from the scene with a name to their personal library on the server and places it in any of their projects; items already in the browser's own library are imported. Covers R8.
- **SP-6 — AI spend per user and session** (UI: `gasto-ia@v1`): Every paid AI call (Next and ai-api) is stored with user, sign-in session, work item (project or conversation), tool and kind (text or image); employees and administrators see totals grouped by project or conversation, filtered by user and kind; a usuario cannot open the view. Covers R4, R5.
- **SP-7 — Assisted chat as three tools and the decorations explorer** (UI: `herramientas-chat@v1`): The assisted chat becomes a balloon counter, a cost calculator and the normal chat, each with its own prompts and spend measured separately and never inventing counts or prices; a ready-made decorations explorer lists existing 3D decorations; each tool is reachable only with its access plan. Covers R13, R16.

<!-- CG-3 tasks -->

  Composition of accepted subplans on the integrated candidate.

- [ ] T93 — Composition check CG-3: accounts and saved projects · repo: pictures · after: T92, T4.9 · verify: `npm run proyectos:test-composicion` · files: .evidence/REQ-021/CG-3.integration.json · resources: candidate:CG-3 · covers: R2, R6, R7, R9, R11 · kind: test · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 45 minutes.
  Execute the composition mode authored by T4.6 on the integrated candidate. Record candidate/tree identity; no harness authoring or repairs here.

  - Acceptance / integration: The integrated candidate passes account-scoped project save/reopen with rectangular tables and Backing, staff read/copy, conflict rejection and account deletion refusal. Check: `npm run proyectos:test-composicion`

<!-- /CG-3 tasks -->

### M3 — Inglés / español
La interfaz usa el idioma del navegador durante la primera visita y luego la elección de la cuenta; el Taller 3D y la navegación se traducen completamente primero, seguidos por los textos de los productos, las pantallas restantes y las respuestas de IA.

- **SP-8 — Selector de idioma, Taller 3D y navegación en inglés** (UI: `idioma-taller@v1`): Un mecanismo de idioma con detección en la primera visita, un selector que recuerda la elección por cuenta y todas las cadenas del Taller 3D y la navegación en ambos idiomas. Cubre R12.
- **SP-9 — Textos de productos y decoraciones en inglés** (UI: `textos-producto@v1`): Los nombres y las descripciones en inglés de cada producto y decoración se generan una vez a partir del original en español, se almacenan y se muestran cuando el idioma es inglés, con el texto en español como alternativa; un administrador puede corregirlos. Cubre R12.
- **SP-10 — Pantallas restantes y respuestas de IA en inglés** (UI: `idioma-resto@v1`): Las pantallas de las herramientas del chat, el catálogo, la administración, el gasto y las estadísticas están completamente en inglés; la IA de la escena y las herramientas del chat responden en el idioma del usuario. Cubre R12.

### M4 — Módulos editables y chat → 3D
Los usuarios editan módulos y cuartetos más allá de sus colores, y el chat normal recomienda decoraciones 3D prediseñadas que se abren en el Taller.

- **SP-11 — Módulos y cuartetos editables** (UI: `modulos-editables@v1`): Un usuario edita un módulo o cuarteto de la escena más allá de sus colores (las ediciones exactas se acuerdan con el propietario en este subplan) y se actualizan las cantidades y la lista de compras. Cubre R15.
- **SP-12 — El chat normal recomienda decoraciones 3D prediseñadas** (UI: `chat-a-3d@v1`): En dos o tres mensajes, el chat normal define la necesidad y recomienda decoraciones 3D existentes que se abren en el Taller 3D como un nuevo proyecto, usando el catálogo y el motor reales. Cubre R13.

### M5 — Lanzamiento del piloto
El piloto funciona en producción con cuentas reales: existe el primer administrador, se publica cada subplan incluido, se supera una prueba de humo en producción y se enumeran los elementos recortados.

- **SP-13 — Lanzamiento del piloto en producción**: Cada subplan aprobado se publica en producción con sus migraciones, se crea el primer administrador, se supera en producción un flujo de extremo a extremo (invitar → activar → guardar proyecto y decoración → aparece el gasto → exportar GLB) y se registra la lista de recortes. Cubre R14.
