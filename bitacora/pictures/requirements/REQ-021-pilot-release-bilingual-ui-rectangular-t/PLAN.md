---
req: REQ-021
status: draft
created: 2026-10-26
---
# Plan — Pilot release: accounts and access plans, saved work, AI spend, Taller essentials, English, modules and chat

Skeleton (collaborative planning, phase Esqueleto). Milestones and subplans only; tasks are defined subplan by subplan
with the owner.

## Approach
Code base: origin/main `a9f3d6e5` of `dav033/pictures` (Next 16 on Vercel, Python ai-api on the VPS, Neon Postgres with
`scripts/migrations/NNN_*.sql` applied by `npm run rag:migrate`). Work branches from origin/main in new worktrees;
`~/dev/pictures` is never used.

**Order backwards from the pilot (2026-11-16).** Accounts come first because saved projects, saved decorations, spend
per user, the access plans and the per-account language all need a signed-in user. The Taller items that do not need
accounts (rectangular tables, Backing, Blender export, editable modules) run in parallel from day one. Language runs
from its own foundation in parallel and is the first to be cut.

| Milestone | Target | Never cut? | Cut date (owner, round 4) |
|---|---|---|---|
| M1 — Accounts, access plans and Taller essentials | 2026-11-01 | yes | — |
| M2 — Saved work, spend per user and the chat tools | 2026-11-07 | yes | — |
| M3 — English / Spanish | 2026-11-09 | no (cut 1) | 2026-11-09: only SP-8 (Taller 3D and navigation) ships |
| M4 — Editable modules and chat → 3D | 2026-11-12 | no (cuts 2 and 3) | 2026-11-11 modules out; 2026-11-12 chat beyond split and reliability out |
| M5 — Pilot release | 2026-11-16 | yes | — |

**Dependencies.** SP-1 (accounts) → SP-2, SP-4, SP-5, SP-6, SP-7, SP-8. SP-4 (project identity) → SP-6 and SP-12.
SP-6 (spend tagging) → SP-7. SP-8 (language mechanism) → SP-9, SP-10. SP-7 (chat tools, decorations explorer) →
SP-10, SP-12. SP-3 and SP-11 depend on nothing. SP-13 consumes every shipped subplan.

**Fit, said plainly.** Rough size: about 70 tasks for the whole SPEC, about 45 for the never-cut part (SP-1 to SP-7 and
SP-13). Agent time is not the limit; waits are: retries, usage limits and the owner's per-subplan test (under 24 h,
D-131). It fits only if the scheduler runs two or more subplans at once and retries stay low. If M1 slips past
2026-11-03, the cut dates above apply as agreed; never-cut work is never traded for language, modules or chat→3D.

**Security.** SP-1 (identity, sessions, permissions, server-side enforcement, local flag, first administrator) is its
own subplan with its own audit; SP-4 audits that a usuario can only reach their own projects.

Out of this plan: 3D space, Illustrator/vector export, AI spend caps (D-072).

### M1 — Accounts, access plans and Taller essentials
Real people sign in with their own invited account and each one reaches exactly what their role or access plan allows; the shared APP_PASSWORD no longer opens the app; tables, Backing and the Blender file work in the Taller.

- **SP-1 — Accounts, sessions and server-side permissions**: Invited accounts with hashed passwords and revocable server sessions replace the shared APP_PASSWORD; every page and API of the pilot checks the permission it needs on the server; roles and the three access plans are sets of permissions; the local no-restrictions flag cannot be enabled in production; the first administrator is created by a one-off command. Covers R1, R2, R3, R16.

<!-- SP-1 tasks -->

  SP-1 tasks (draft for owner confirmation). Owner rulings, rounds 5–6: access plans are roles (Usuario · Plan 1, Usuario · Plan 2, Usuario · Plan 3, Empleado interno, Administrador; one role per account); permissions as in SPEC Clarifications round 6; session 30 days; password at least 8 characters; 5 failures per email in 15 min lock it 15 min; invitation link 7 days, reset link 24 h, both copied by the administrator (no email service); `AUTH_LOCAL_SIN_RESTRICCIONES=1` only under `next dev` on loopback; first production administrator by a one-time command the owner runs himself.
  Planner rulings (revisable at confirmation): the five system roles are fixed in code and read-only in the pilot (custom roles are editable), so no administrator can lock everyone out and plans always match R16; a path missing from the map is administrator-only; pages are enforced in `src/proxy.ts` (no server actions exist) and API handlers also call the guard themselves; SP-1 has no new screens: the sign-in, activation and admin screens are SP-2, so SP-1 is tried with the local mode in the browser and `npm run cuentas:probar-acceso` in the terminal. Until SP-2 lands the old /login page cannot sign in; nothing reaches `main` before M1's subplans are all approved.
  Contracts produced: permission-map@1 (T1.2: `src/lib/cuentas/permisos.ts` catalogue and system roles, `src/lib/cuentas/mapa-rutas.ts`), account-service@1 (T1.3: `src/lib/cuentas/servicio.ts`), session-guard@1 (T1.4: `obtenerSesion(request)`, `exigirPermiso(request, permiso)` in `src/lib/cuentas/guardia.ts`). Consumers: SP-2, SP-4, SP-5, SP-6, SP-7, SP-8. DAG: T1.1 → T1.2 → T1.3 → T1.4 → {T1.5, T1.6} → T1.7 → T1.8.
  Test database: every database test reads `PICTURES_REQ021_DATABASE_URL` (or, only in CI, `DATABASE_URL` with `APP_ENV=test`) through `scripts/test/lib/base-prueba.ts`, which creates a throwaway schema (`search_path` = that schema, public) so runs never see each other's rows. Audit evidence lives under `.evidence/REQ-021/` because the engine needs the ledger in the repository.

- [ ] T1.1 — Accounts schema: migration 037 and the isolated test-schema helper · repo: pictures · verify: `npm run cuentas:test-esquema -- --test-name-pattern=migracion` · files: scripts/migrations/037_cuentas.sql, scripts/test/lib/base-prueba.ts, scripts/test/test-cuentas-esquema.ts · resources: package.json scripts · covers: R1, R2, R3 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence high; estimate 60 minutes.
  Tables (additive only, `IF NOT EXISTS`, rollback comment like 036): `roles` (id, `clave` unique for the five system roles `usuario_plan_1`, `usuario_plan_2`, `usuario_plan_3`, `empleado_interno`, `administrador`, nombre, `sistema` boolean); `rol_permisos` (rol_id, permiso; custom roles only, system role permissions live in code); `cuentas` (id, correo with a unique index on `lower(correo)`, nombre, empresa nullable, rol_id, estado `invitada|activa|desactivada`, hash_contrasena nullable, invitada_en, activada_en, ultimo_acceso_en, aviso_datos_version, aviso_datos_aceptado_en, idioma nullable `es|en`, es_local boolean, creada_por nullable); `sesiones` (id, cuenta_id ON DELETE CASCADE, hash_token char(64) unique, creada_en, expira_en, revocada_en); `enlaces_cuenta` (id, cuenta_id ON DELETE CASCADE, tipo `invitacion|restablecer`, hash_token unique, expira_en, usado_en, creado_por); `intentos_ingreso` (correo normalizado, en, exitoso) indexed by (correo, en).
  Personal data kept is only what round 5 q6 lists. `base-prueba.ts` exports `crearBasePrueba()` → `{ url, pool, cerrar() }`: it refuses unless the URL comes from `PICTURES_REQ021_DATABASE_URL`, or from `DATABASE_URL` with `APP_ENV=test`; creates schema `prueba_<random>`, applies every migration of `scripts/migrations/` into it with the runner's logic, returns a URL whose `options` set `search_path=<schema>,public`, and drops the schema in `cerrar()`.
  npm script added: `cuentas:test-esquema` = `tsx --test scripts/test/test-cuentas-esquema.ts`.

  - Acceptance / integration: Migration 037 applies on an empty isolated schema and again on an already migrated one without error, creates the account, role, session, link and sign-in attempt tables, and seeds exactly the five system roles. Check: `npm run cuentas:test-esquema -- --test-name-pattern=migracion`
  - Acceptance / functional: The database rejects a second account whose email differs only in letter case and removes an account's sessions and links when the account is deleted. Check: `npm run cuentas:test-esquema -- --test-name-pattern=restricciones`
  - Acceptance / functional: Each test run works in its own throwaway schema of the REQ-021 test database, drops it at the end, and refuses to run against any database other than PICTURES_REQ021_DATABASE_URL or a CI database marked APP_ENV=test. Check: `npm run cuentas:test-esquema -- --test-name-pattern=aislamiento`

- [ ] T1.2 — Permission catalogue, the five system roles and the route permission map · repo: pictures · after: T1.1 · verify: `npm run cuentas:test-permisos -- --test-name-pattern=cobertura` · files: src/lib/cuentas/permisos.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-mapa-rutas.ts · resources: package.json scripts, contract:permission-map · covers: R2, R3, R16 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling high; confidence medium; estimate 90 minutes.
  Permissions (keys stable, labels ES/EN for SP-2): `chat.usar`, `contador.usar`, `catalogo.ver`, `costos.usar`, `decoraciones.explorar`, `taller.usar`, `proyectos.ver_todos`, `gasto.ver`, `internas.usar`, `cuentas.administrar`, `roles.administrar`, `textos.corregir`. System roles: Plan 1 = chat, contador, catálogo; Plan 2 = Plan 1 + costos, decoraciones; Plan 3 = Plan 2 + taller; Empleado interno = Plan 3 + proyectos.ver_todos, gasto.ver, internas.usar; Administrador = everything.
  Map entries: `{ patron, acceso }` with `acceso` = `{ permiso }`, `'sesion'` (any signed-in account: home page, sign-out), `'publica'` (login, activation, `/cotizacion-compartida/*` and its public APIs) or `'auth-propia'` (today's proxy exceptions: asesor, Happie recommend/webhook, Shopify webhook, feedback cron, voice transcription). Classification: /asistente, chat and guided-engine APIs → chat.usar; /catalogo and catalogue/product read APIs → catalogo.ver; cotizacion-profesional → costos.usar; decorations read API → decoraciones.explorar; /3d, scene AI, plan-armado-*, plan-patron, plan-dibujo-estructura, plan-idea, plan-editar, taller/*, modulos-*, render and image generation, escena-desde-foto, hoja-armado → taller.usar; /admin, /api/admin/*, write APIs of products and decorations, /estadisticas, laboratorios, Happie test, IA provider, feedback admin, internal AI → internas.usar. The balloon counter has no route of its own until SP-7. A route whose tool is unclear goes to internas.usar and is listed in the task report.
  `resolverAcceso(path)` returns the single matching entry or `null` (= administrator-only, permission `cuentas.administrar`). npm script `cuentas:test-permisos` = `tsx --test scripts/test/test-mapa-rutas.ts`.

  - Acceptance / static: Every page.tsx and route.ts under src/app matches exactly one entry of the route permission map, and the test fails naming any file that matches none or several. Check: `npm run cuentas:test-permisos -- --test-name-pattern=cobertura`
  - Acceptance / functional: The five system roles hold exactly the permissions of the owner's table: Plan 1 chat, balloon counter and catalogue; Plan 2 adds costs and the decorations explorer; Plan 3 adds the Taller 3D; Empleado interno adds everyone's projects, AI spend and internal tools; Administrador adds users, roles and text corrections. Check: `npm run cuentas:test-permisos -- --test-name-pattern=roles-sistema`
  - Acceptance / functional: A path the map does not list is reachable only with the users-administration permission, and the public and own-auth exceptions of today's proxy matcher stay public or own-auth. Check: `npm run cuentas:test-permisos -- --test-name-pattern=excepciones`

- [ ] T1.3 — Account service: invitations, activation, sign-in with lockout, reset links, roles and the one-time commands · repo: pictures · after: T1.2 · verify: `npm run cuentas:test-servicio -- --test-name-pattern=invitacion` · files: src/lib/seguridad/scrypt.ts, src/lib/asesor/auth.ts, src/lib/cuentas/servicio.ts, src/lib/cuentas/enlaces.ts, src/lib/cuentas/limite-intentos.ts, scripts/cuentas/primer-admin.ts, scripts/cuentas/sembrar-prueba.ts, scripts/test/test-cuentas-servicio.ts · resources: package.json scripts, contract:account-service, contract:permission-map · covers: R1, R3, R16 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 150 minutes.
  Move the scrypt hash/verify of `src/lib/asesor/auth.ts` into `src/lib/seguridad/scrypt.ts` unchanged; the advisor login imports it and keeps its behavior.
  Service API (`src/lib/cuentas/servicio.ts`, server-only): `invitar({correo, nombre, empresa?, rolId}, porCuentaId)` → link; `activar(token, {contrasena, versionAviso})`; `ingresar(correo, contrasena, ip)` → cuenta or the generic error `CREDENCIALES_INVALIDAS`; `crearEnlaceRestablecer(cuentaId, porCuentaId)`; `restablecer(token, contrasena)`; `cambiarRol`, `desactivar`, `reactivar`, `eliminar`; `crearRol({nombre, permisos})`, `editarRol`, `eliminarRol`. Tokens: 32 random bytes base64url, only SHA-256 stored; invitation 7 days, reset 24 h, single use under a row lock. Passwords: minimum 8 characters, maximum 200, scrypt. Lockout: 5 failures for one normalised email within 15 min → that email refused 15 min (checked before verifying the password, same generic error). The last active Administrador cannot be deactivated, deleted or moved to another role. Deleting an account removes its row, sessions, links and sign-in attempts; later subplans decide what happens to its projects.
  `npm run cuentas:primer-admin -- --correo <email>` (owner runs it at release against the database in `DATABASE_URL`): refuses without changes if an active Administrador exists; otherwise creates the invited Administrador and prints the activation link once to the terminal, never to a log file. `npm run cuentas:sembrar-prueba`: refuses unless the target is `PICTURES_REQ021_DATABASE_URL`; creates `plan1@prueba.local`, `plan2@prueba.local`, `plan3@prueba.local`, `empleado@prueba.local` and `admin@prueba.local`, active, with one password typed without echo. npm script `cuentas:test-servicio` = `tsx --conditions=react-server --test scripts/test/test-cuentas-servicio.ts`.

  - Acceptance / functional: An administrator's invitation creates an invited account with a single-use link valid seven days; activating it sets a password of at least eight characters, records the data-notice version and date, and a second use of the same link is refused. Check: `npm run cuentas:test-servicio -- --test-name-pattern=invitacion`
  - Acceptance / functional: Signing in with the right email and password of an active account creates a session; a wrong password, an unknown email and a deactivated account all get the same generic refusal. Check: `npm run cuentas:test-servicio -- --test-name-pattern=ingreso`
  - Acceptance / functional: After five failed sign-ins for one email within fifteen minutes that email is refused for fifteen minutes even with the right password, and other emails are unaffected. Check: `npm run cuentas:test-servicio -- --test-name-pattern=bloqueo`
  - Acceptance / functional: An administrator-generated reset link is single-use, expires after 24 hours, sets a new password and revokes every open session of that account. Check: `npm run cuentas:test-servicio -- --test-name-pattern=restablecer`
  - Acceptance / functional: Deactivating, deleting or changing the role of the last active Administrador is refused; deleting an account removes its personal data rows. Check: `npm run cuentas:test-servicio -- --test-name-pattern=ultimo-admin`
  - Acceptance / functional: An administrator creates a role from permissions of the catalogue only; the five system roles cannot be edited or deleted; a role still assigned to accounts cannot be deleted. Check: `npm run cuentas:test-servicio -- --test-name-pattern=roles`
  - Acceptance / integration: npm run cuentas:primer-admin creates an invited Administrador for the given email and prints its activation link once, and refuses without changes when an active Administrador already exists. Check: `npm run cuentas:test-servicio -- --test-name-pattern=primer-admin`
  - Acceptance / functional: npm run cuentas:sembrar-prueba creates one active account per system role with a password read from the terminal without echo, and refuses when the target database is not the REQ-021 test database. Check: `npm run cuentas:test-servicio -- --test-name-pattern=sembrar`

- [ ] T1.4 — Server sessions and the permission guard in the proxy and the sign-in API, replacing APP_PASSWORD · repo: pictures · after: T1.3 · verify: `npm run cuentas:test-sesion -- --test-name-pattern=cookie` · files: src/lib/cuentas/sesion.ts, src/lib/cuentas/guardia.ts, src/proxy.ts, src/lib/auth/session.ts, src/lib/auth/request.ts, src/app/api/login/route.ts, src/app/api/cuentas/ingresar/route.ts, src/app/api/cuentas/salir/route.ts, src/app/sin-acceso/page.tsx, scripts/cuentas/probar-acceso.ts, scripts/test/test-sesion-guardia.ts, scripts/test/test-proxy-matcher.ts · resources: package.json scripts, contract:session-guard, contract:account-service, contract:permission-map · covers: R1, R2 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 150 minutes.
  `sesion.ts`: `crearSesion(cuentaId)` sets cookie `pictures_sesion` (httpOnly, SameSite=Lax, Secure unless the host is localhost/127.0.0.1, Max-Age 30 days, absolute expiry); `obtenerSesion(request)` → `{ cuenta, rol, permisos } | null` with one query (sessions × accounts × roles, custom role permissions from `rol_permisos`, system ones from `permisos.ts`), rejecting revoked, expired or non-active accounts and updating `ultimo_acceso_en` at most once per hour; `cerrarSesion`.
  `guardia.ts`: `exigirPermiso(request, permiso)` → `{ cuenta } | Response` (401 `SESION_REQUERIDA` / 403 `SIN_PERMISO`, JSON). `src/proxy.ts`: public and own-auth entries pass untouched (same matcher exceptions as today); otherwise resolve the session and the map: no session → page redirect to `/login?from=<path>` and API 401; missing permission → page rewrite to `/sin-acceso` (plain server page, text only) and API 403. Remove `APP_PASSWORD`, `sessionToken`, `loginOmitidoEnDesarrollo` and `DEV_REQUIRE_LOGIN`; `/api/login` is deleted in favor of `POST /api/cuentas/ingresar` (JSON email + password, same relative redirect rule as today for forms) and `POST /api/cuentas/salir`. Mutating APIs keep `isSameOriginRequest`.
  `npm run cuentas:probar-acceso -- --base http://localhost:3000 --correo <email>` reads the password without echo, signs in and prints allowed/denied for one representative page and API per map area. npm script `cuentas:test-sesion` = `tsx --conditions=react-server --test scripts/test/test-sesion-guardia.ts`; `test-proxy-matcher` is updated to the new matcher.

  - Acceptance / functional: A session cookie is httpOnly, SameSite=Lax, Secure outside localhost, lasts 30 days, and only the SHA-256 of its random token is stored. Check: `npm run cuentas:test-sesion -- --test-name-pattern=cookie`
  - Acceptance / functional: Deactivating an account, changing its password or signing out ends its sessions on the next request, and a role change applies on the next request without signing in again. Check: `npm run cuentas:test-sesion -- --test-name-pattern=revocacion`
  - Acceptance / functional: Without a valid session a page request redirects to /login keeping the path and an API request gets 401 JSON; with a session lacking the mapped permission a page shows the no-access page and an API gets 403 JSON. Check: `npm run cuentas:test-sesion -- --test-name-pattern=proxy`
  - Acceptance / regression: A cookie or form built from the old APP_PASSWORD no longer grants access, and no code path reads APP_PASSWORD. Check: `npm run cuentas:test-sesion -- --test-name-pattern=sin-clave-compartida`
  - Acceptance / integration: npm run cuentas:probar-acceso signs in against a running server with an email and a password read without echo and prints, for every mapped area, whether that account is allowed or denied. Check: `npm run cuentas:test-sesion -- --test-name-pattern=probar-acceso`

- [ ] T1.5 — Local no-restrictions mode that refuses to start outside next dev on loopback · repo: pictures · after: T1.4 · verify: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback` · files: src/lib/cuentas/modo-local.ts, src/instrumentation.ts, next.config.ts, services/ai-api/app/main.py, scripts/test/test-modo-local.ts, services/ai-api/tests/test_modo_local.py · resources: package.json scripts · covers: R2 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence high; estimate 60 minutes.
  `modo-local.ts`: `validarModoLocal({ nodeEnv, vercel, fase })` throws `AUTH_LOCAL_SIN_RESTRICCIONES solo funciona con next dev en tu máquina` unless `NODE_ENV=development`, `VERCEL` unset and the phase is the dev server; called from `next.config.ts` (covers `next build`) and `register()` in `src/instrumentation.ts` (covers `next start` and the VPS container). The ai-api refuses to start if the variable is present at all. Per request, the session guard treats the request as the Administrador local account only when the mode is on and the connection address is loopback (127.0.0.1, ::1); the Host header is never trusted.
  The Administrador local account (`es_local = true`, correo `admin-local@localhost.invalid`, role Administrador, no password, so it can never sign in remotely) is created on first use in whatever database the local process points at; this also covers the owner's round-6 note of running locally against the production database to create administrators.
  npm script `cuentas:test-modo-local` = `tsx --conditions=react-server --test scripts/test/test-modo-local.ts`.

  - Acceptance / functional: With AUTH_LOCAL_SIN_RESTRICCIONES=1 under next dev, a request from 127.0.0.1, ::1 or localhost runs as the Administrador local account without signing in, and a request from any other address must sign in. Check: `npm run cuentas:test-modo-local -- --test-name-pattern=loopback`
  - Acceptance / functional: With AUTH_LOCAL_SIN_RESTRICCIONES set, next build, next start, a Vercel environment and the ai-api deployment refuse to start with an error naming the variable. Check: `npm run cuentas:test-modo-local -- --test-name-pattern=rechazo-arranque`
  - Acceptance / regression: Without the variable next dev asks to sign in like production, and DEV_REQUIRE_LOGIN no longer changes anything. Check: `npm run cuentas:test-modo-local -- --test-name-pattern=sin-variable`

- [ ] T1.6 — Apply the permission guard to every API handler and move the existing suites to a shared test session · repo: pictures · after: T1.4 · verify: `npm run cuentas:test-rutas` · files: src/app/api/**/route.ts, src/lib/feedback-ia/acceso.ts, src/lib/guiada-motor/manejadores.ts, src/lib/happie/panel-prueba.ts, src/lib/shared-quotes/dependencies.server.ts, src/lib/taller/cotizacion-taller.ts, src/lib/asesor/voice.ts, scripts/test/lib/sesion-prueba.ts, scripts/test/test-guardias-rutas.ts, scripts/test/*.ts, scripts/e2e/humo/configuracion.ts, scripts/e2e/humo/pasos-asistente.ts, scripts/e2e/humo/navegacion.ts, scripts/eval/eval-chat-jerga.ts · resources: package.json scripts, contract:session-guard, contract:permission-map · covers: R2 · kind: implement · subplan: SP-1 · ui: no

  Classification: complexity low; scope large_change; risk high; coupling high; confidence high; estimate 180 minutes.
  Each handler outside `publica`/`auth-propia` starts with `const acceso = await exigirPermiso(request, '<permiso>'); if (acceso instanceof Response) return acceso;`, with the permission `resolverAcceso` gives its path; library helpers that called `isAuthenticatedRequest` receive the account from their handler instead. `test-guardias-rutas.ts` reads each `route.ts`, checks that every exported HTTP method calls `exigirPermiso` with exactly the mapped permission before any other await, and calls a sample of handlers in-process with no session, a Plan 1 session and an Administrador session.
  `scripts/test/lib/sesion-prueba.ts`: `conSesionDePrueba(rolClave)` creates an account and a session in the isolated test schema and returns the cookie header; no environment variable bypasses authentication. The e2e smoke (`npm run e2e:humo`) signs in with `E2E_CORREO`/`E2E_CONTRASENA` instead of APP_PASSWORD. npm script `cuentas:test-rutas` = `tsx --conditions=react-server --test scripts/test/test-guardias-rutas.ts`.

  - Acceptance / functional: Every API route handler outside the public and own-auth exceptions calls the permission guard with the permission the map assigns to its path before doing any work. Check: `npm run cuentas:test-rutas`
  - Acceptance / regression: The existing suites that signed in with APP_PASSWORD pass using the shared test-session helper and none of them sets APP_PASSWORD. Check: `npm run test-cotizacion-unica`
  - Acceptance / static: Lint and the TypeScript check pass on the whole repository after the guards are applied. Check: `npm run taller:test-estatico`

- [ ] T1.7 — End-to-end check of accounts and permissions on a production build, and the SP-1 suites in CI · repo: pictures · after: T1.5, T1.6 · verify: `npm run cuentas:test-integracion` · files: scripts/test/test-integracion-cuentas.ts, .github/workflows/checks.yml, .evidence/REQ-021/SP-1.integration.json · resources: package.json scripts, contract:session-guard · covers: R1, R2, R3, R16 · kind: test · subplan: SP-1

  Classification: complexity medium; scope small_change; risk high; coupling medium; confidence medium; estimate 120 minutes.
  `test-integracion-cuentas.ts`: creates the isolated schema, seeds one account per role through the service, runs `next build` then `next start` on a free loopback port with `DATABASE_URL` = the schema URL, and with plain `fetch`: signs in through `/api/cuentas/ingresar`, asserts allowed and denied pages (redirect or `/sin-acceso`) and APIs (401/403) for Plan 1, Plan 3, Empleado interno and Administrador; deactivates the Plan 3 account through the service and asserts its next request gets 401; posts the old shared password form and asserts refusal; then starts `next start` with `AUTH_LOCAL_SIN_RESTRICCIONES=1` and asserts it exits with the error. Writes `.evidence/REQ-021/SP-1.integration.json` and kills only its own processes.
  `checks.yml`: the Postgres job runs `cuentas:test-esquema`, `cuentas:test-permisos`, `cuentas:test-servicio`, `cuentas:test-sesion`, `cuentas:test-modo-local` and `cuentas:test-rutas`, plus a step that runs `next build` with the variable set and passes only if it fails. npm script `cuentas:test-integracion` = `tsx scripts/test/test-integracion-cuentas.ts`.

  - Acceptance / integration: Against a production build started with next start on the REQ-021 test database, one Plan 1, one Plan 3, one Empleado interno and one Administrador account each reach exactly their mapped pages and APIs, a deactivated account loses access on its next request, and the old shared password is refused. Check: `npm run cuentas:test-integracion`
  - Acceptance / static: The CI checks workflow runs the SP-1 suites against its Postgres service and fails when a build is started with AUTH_LOCAL_SIN_RESTRICCIONES set. Check: `npm run cuentas:test-integracion -- --solo-ci`

- [ ] T1.8 — SP-1 security audit: accounts, sessions, permissions, local mode and the one-time commands · repo: pictures · after: T1.7 · verify: `bitacora.py audit-ledger check .evidence/REQ-021/SP-1.findings.json` · files: .evidence/REQ-021/SP-1.audit.md, .evidence/REQ-021/SP-1.findings.json · resources: ledger:SP-1 · covers: R1, R2, R3, R16 · kind: audit · subplan: SP-1

  Classification: complexity high; scope small_change; risk high; coupling medium; confidence medium; estimate 90 minutes.
  Checks at least: tokens and passwords never logged or stored in clear; timing-safe comparisons; lockout cannot be bypassed by case or spaces in the email; links are single-use under concurrency; every route.ts and page.tsx is mapped and guarded; own-auth exceptions unchanged; the local mode cannot activate in any build, start or deployment and ignores forged Host headers; `primer-admin` cannot create a second administrator; deleting an account removes its personal data. Each confirmed defect names the task to redo.

  - Acceptance / static: An independent security audit of SP-1 records every confirmed defect with the task that must redo it in the SP-1 findings ledger, and the ledger has no open critical or high finding. Check: `bitacora.py audit-ledger check .evidence/REQ-021/SP-1.findings.json`

<!-- /SP-1 tasks -->

- **SP-2 — Sign-in, invitation and administration screens** (UI: `cuentas-admin@v1`): A person signs in with email and password, activates an invitation link and accepts the data notice; an administrator invites people, assigns role or access plan, creates roles by choosing permissions, and deactivates or deletes accounts. Covers R1, R3, R16.

<!-- SP-2 tasks -->

  SP-2 tasks (draft for owner confirmation). Screens follow the Designer's `cuentas-admin@v1` contract once the owner approves it. Only the Administrador manages users and roles (round 6 q2). Screens are written in Spanish now with every string in one module per screen so SP-8/SP-10 translate them; the data notice ships in Spanish and English from the start (round 5 q6).
  DAG: T2.1 (design) ∥ T2.2 (APIs, after SP-1's session-guard T1.4) → {T2.3, T2.4, T2.5} (UI) → T2.6 (integration) → T2.7 (visual review) → T2.8 (audit). Consumes account-service@1, session-guard@1 and permission-map@1 from SP-1; composition gate CG-1 proves SP-1 and SP-2 together on the integrated M1 tree.

- [ ] T2.1 — Copy the owner-approved cuentas-admin@v1 contract into the repository · repo: pictures · after: T1.4 · verify: `test -s design/contracts/cuentas-admin@v1.md` · files: design/contracts/cuentas-admin@v1.md · resources: design:cuentas-admin@v1 · covers: R1, R3, R16 · kind: design · subplan: SP-2 · ui: no

  Classification: complexity low; scope isolated_fix; risk low; coupling medium; confidence high; estimate 10 minutes.
  The scheduler supplies the plan-approved draft; the task copies it unchanged.

  - Acceptance / static: The owner-approved cuentas-admin@v1 contract is copied byte for byte into design/contracts/cuentas-admin@v1.md. Check: `test -s design/contracts/cuentas-admin@v1.md`

- [ ] T2.2 — Account APIs: activation, reset, notice acceptance, own password and the administration of accounts and roles · repo: pictures · after: T1.4 · verify: `npm run cuentas:test-api -- --test-name-pattern=enlaces` · files: src/lib/cuentas/aviso-datos.ts, src/app/api/cuentas/activar/route.ts, src/app/api/cuentas/restablecer/route.ts, src/app/api/cuentas/aviso/route.ts, src/app/api/cuentas/mi-cuenta/route.ts, src/app/api/admin/cuentas/route.ts, src/app/api/admin/cuentas/[id]/route.ts, src/app/api/admin/roles/route.ts, src/app/api/admin/roles/[id]/route.ts, src/lib/cuentas/dependientes.ts, src/lib/cuentas/regenerar-enlace.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-cuentas-api.ts · resources: package.json scripts, contract:account-service, contract:session-guard · covers: R1, R3, R16 · kind: implement · subplan: SP-2 · ui: no

  Classification: complexity medium; scope large_change; risk high; coupling high; confidence medium; estimate 120 minutes.
  `aviso-datos.ts` exports `AVISO_DATOS = { version: 1, es, en }` with the SPEC «Data-processing notice» text verbatim, placeholders included. Routes: `POST /api/cuentas/activar` {token, contrasena, versionAviso}; `POST /api/cuentas/restablecer` {token, contrasena}; `GET /api/cuentas/activar?token=` returns name and email for a valid invitation only; `POST /api/cuentas/aviso` accepts the current version for the session's account; `PATCH /api/cuentas/mi-cuenta` {actual, nueva} (the SP-1 service revokes every session of the account; the route then opens a new session for the requesting browser). Admin (`cuentas.administrar`): `GET/POST /api/admin/cuentas` (list with search and filters; invite), `PATCH/DELETE /api/admin/cuentas/[id]` (role, state, reset link; delete requires `confirmarCorreo` equal to the email). Roles (`roles.administrar`): `GET/POST /api/admin/roles`, `PATCH/DELETE /api/admin/roles/[id]`. All mutations keep `isSameOriginRequest`; errors are stable codes (`LINK_INVALIDO`, `CORREO_REGISTRADO`, `ULTIMO_ADMIN`, `ROL_EN_USO`, `ROL_SISTEMA`).
  Delete rule (owner, round 7 q1): `src/lib/cuentas/dependientes.ts` exports a registry of tables that hold an account's saved work (empty here; SP-4 adds projects and SP-5 saved decorations); `DELETE /api/admin/cuentas/[id]` refuses with `CUENTA_CON_TRABAJO` when any registered table has a row for the account, so such accounts are only deactivated. AI spend rows (SP-6) are never work: they keep their totals with the account reference set to null and show «Cuenta eliminada». Round 8: `regenerar-enlace.ts` revokes every unused link of the same kind for the account and issues a new one (`POST /api/admin/cuentas/[id]` action `enlace-nuevo`, for invited accounts and for resets); custom roles need at least one permission (`ROL_SIN_PERMISOS`, checked in the API schema); `POST /api/cuentas/activar` opens the session with SP-1 `crearSesion` and answers the first allowed destination. The notice-acceptance route also serves re-acceptance when `AVISO_DATOS.version` grows (round 7 q3). The map from T1.2 gets the new paths (public: activar, restablecer; sesion: aviso, mi-cuenta). npm script `cuentas:test-api` = `tsx --conditions=react-server --test scripts/test/test-cuentas-api.ts`.

  - Acceptance / functional: The activation, reset and notice-acceptance APIs accept only a valid unused token or a signed-in session, validate every body, answer a used or expired link with LINK_INVALIDO without saying which, and a successful activation opens a session at once. Check: `npm run cuentas:test-api -- --test-name-pattern=enlaces`
  - Acceptance / functional: The account and role administration APIs refuse anyone without the users or roles permission with 403 and accept only same-origin requests with validated bodies. Check: `npm run cuentas:test-api -- --test-name-pattern=admin`
  - Acceptance / functional: Generating a new invitation or reset link for an account invalidates every older unused link of the same kind for that account, and a custom role with no permission is refused with ROL_SIN_PERMISOS. Check: `npm run cuentas:test-api -- --test-name-pattern=regenerar`
  - Acceptance / functional: Changing one's own password requires the current password, ends every session of that account and signs the requesting browser in again with a new session. Check: `npm run cuentas:test-api -- --test-name-pattern=mi-cuenta`
  - Acceptance / functional: The data notice exists in Spanish and English with a version number, its bracketed placeholders are still marked for legal review, and accepting stores the version and date on the account. Check: `npm run cuentas:test-api -- --test-name-pattern=aviso`
  - Acceptance / functional: Deleting an account that owns any row of a table registered as account work is refused with CUENTA_CON_TRABAJO and changes nothing, while deleting an account without saved work removes it and keeps its AI spend rows without personal data. Check: `npm run cuentas:test-api -- --test-name-pattern=borrar`

- [ ] T2.3 — Sign-in, invitation activation, password reset and notice re-acceptance screens · repo: pictures · after: T2.1, T2.2 · verify: `npm run cuentas:test-ui-acceso -- --solo ingreso` · files: src/app/login/page.tsx, src/app/login/LoginForm.tsx, src/app/activar/[token]/page.tsx, src/app/restablecer/[token]/page.tsx, src/app/aviso-datos/page.tsx, src/components/cuentas/FormularioContrasena.tsx, src/components/cuentas/AvisoDatos.tsx, src/components/cuentas/textos-acceso.ts, src/proxy.ts, scripts/test/test-ui-acceso.ts · resources: package.json scripts, contract:session-guard · covers: R1 · kind: implement · subplan: SP-2 · ui: yes

  Classification: complexity medium; scope full_feature; risk high; coupling medium; confidence medium; estimate 150 minutes.
  Strings live in `textos-acceso.ts` (Spanish now, keys ready for SP-8). The notice is shown in the browser language (`Accept-Language`: en → English, else Spanish). The proxy redirects a session whose account accepted an older notice version to `/aviso-datos?from=` before any page except sign-out. After sign-in the destination is `from` when allowed, else the first allowed of Taller 3D, chat, catalogue, else `/cuenta` (every active account can open it). The sign-in screen never distinguishes a locked email: SP-1 returns one generic refusal, and the message always adds the fifteen-minute wait hint. npm script `cuentas:test-ui-acceso` = `tsx scripts/test/test-ui-acceso.ts` (server render of every state plus a Playwright pass on a dev server against the isolated schema).

  - Acceptance / functional: On /login a person signs in with email and password; a wrong password, an unknown email, a deactivated account and a locked email all show the same message, which always adds that after several failures one must wait fifteen minutes, and success returns to the requested page or the first area the role allows, or Mi cuenta when the role has none of them. Check: `npm run cuentas:test-ui-acceso -- --solo ingreso`
  - Acceptance / functional: Opening an invitation link shows the invited name and email, asks for a password of at least eight characters twice and shows the data notice in the browser language with an accept checkbox, activation is impossible without accepting, and after activating the person lands signed in on the first tool their role allows; a used or expired link shows a message to ask the administrator for a new one. Check: `npm run cuentas:test-ui-acceso -- --solo activacion`
  - Acceptance / functional: Opening a reset link lets the person set a new password and then sign in; a used or expired link shows the same message as an invalid invitation. Check: `npm run cuentas:test-ui-acceso -- --solo restablecer`
  - Acceptance / functional: When the notice version changes, a signed-in person must accept the new version before any other page opens. Check: `npm run cuentas:test-ui-acceso -- --solo aviso`

- [ ] T2.4 — Account menu on every signed-in page and the Mi cuenta page · repo: pictures · after: T2.1, T2.2 · verify: `npm run cuentas:test-ui-mi-cuenta` · files: src/components/cuentas/MenuCuenta.tsx, src/app/layout.tsx, src/app/cuenta/page.tsx, src/components/cuentas/textos-cuenta.ts, scripts/test/test-ui-mi-cuenta.ts · resources: package.json scripts, contract:session-guard · covers: R1 · kind: implement · subplan: SP-2 · ui: yes

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 75 minutes.
  The root layout reads the session on the server and renders `MenuCuenta` only for signed-in pages, at the place the contract defines. npm script `cuentas:test-ui-mi-cuenta` = `tsx scripts/test/test-ui-mi-cuenta.ts`.

  - Acceptance / functional: Every signed-in page shows an account menu with the person's name and role, Mi cuenta and sign out, and Mi cuenta changes the password by asking for the current one. Check: `npm run cuentas:test-ui-mi-cuenta`

- [ ] T2.5 — Administration screens: accounts list, invitations, account actions and the role editor · repo: pictures · after: T2.1, T2.2 · verify: `npm run cuentas:test-ui-admin -- --solo lista` · files: src/app/admin/cuentas/page.tsx, src/app/admin/roles/page.tsx, src/components/admin/cuentas/ListaCuentas.tsx, src/components/admin/cuentas/DialogoInvitar.tsx, src/components/admin/cuentas/AccionesCuenta.tsx, src/components/admin/cuentas/EditorRol.tsx, src/components/admin/cuentas/textos-admin-cuentas.ts, src/components/admin/AdminTabs.tsx, scripts/test/test-ui-admin-cuentas.ts · resources: package.json scripts, contract:permission-map · covers: R1, R3, R16 · kind: implement · subplan: SP-2 · ui: yes

  Classification: complexity medium; scope full_feature; risk high; coupling medium; confidence medium; estimate 180 minutes.
  The invitation and reset links are shown once with a copy button and a note that they are not shown again. Permission checkboxes come from `permisos.ts` with their labels, grouped by tool. Links to both screens appear only for accounts holding the permission. npm script `cuentas:test-ui-admin` = `tsx scripts/test/test-ui-admin-cuentas.ts`.

  - Acceptance / functional: An administrator sees all accounts with name, email, company, role, state and last access, searches by name or email and filters by role and state. Check: `npm run cuentas:test-ui-admin -- --solo lista`
  - Acceptance / functional: An administrator invites a person by name, email, optional company and role, and gets the single-use link once with a copy button; an email already registered is refused with a clear message. Check: `npm run cuentas:test-ui-admin -- --solo invitar`
  - Acceptance / functional: An administrator changes an account's role, deactivates and reactivates it, generates a reset link and deletes an account without saved work after typing its email, and the screen explains why the last administrator or an account with saved work cannot be deleted. Check: `npm run cuentas:test-ui-admin -- --solo acciones`
  - Acceptance / functional: An administrator creates and edits a custom role by name and permission checkboxes grouped by tool, sees the five system roles read-only with their permissions, and cannot delete a role that still has accounts. Check: `npm run cuentas:test-ui-admin -- --solo roles`

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

- **SP-3 — Taller essentials: rectangular tables, Backing and Blender export** (UI: `taller-esenciales@v1`): A user adds a rectangular table from its type card, edits size and chairs and sees actual quantities and dimensions without rental prices in the shopping list; Taller Fondos y muebles has one Backing group containing the seven existing props moved from their former visual groups, with saved IDs and AI/photo discovery preserved; the exported GLB opens in portable Blender LTS with the same layout, sizes in metres and base colours. Covers R9, R10, R11.

<!-- SP-3 tasks -->

  Behavior and task breakdown reflect the owner answers to round 9. Subplan and design confirmation remain separate owner actions; focus stays SP-2.

- [ ] T3.1 — Copy the approved Taller essentials design contract · repo: pictures · after: T1.8 · verify: `cmp -- design/contracts/taller-esenciales@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/taller-esenciales@v1.md` · files: design/contracts/taller-esenciales@v1.md · resources: design:T3.1 · covers: R9, R10, R11 · kind: design · subplan: SP-3 · ui: no

  Classification: complexity low; scope small_change; risk low; coupling medium; confidence medium; estimate 20 minutes.
  Copy the exact pinned owner-approved artifact without rewriting its content; compare SHA-256 with that approved source.

  - Acceptance / static: The repository contract is byte-identical to the owner-approved taller-esenciales@v1 artifact. Check: `cmp -- design/contracts/taller-esenciales@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/taller-esenciales@v1.md`

- [ ] T3.2 — Add rectangular tables through the existing table editor · repo: pictures · after: T3.1 · verify: `npx tsx scripts/test/test-taller-mesas-piloto.ts` · files: src/components/tres-d/FondosYMuebles.tsx, src/components/tres-d/EditorConjuntoMesa.tsx, src/lib/globos3d/mobiliario-conjunto-escena.ts, src/components/tres-d/textos-taller-esenciales.ts, scripts/test/test-taller-mesas-piloto.ts · resources: taller:scene, taller:scene · covers: R9 · kind: implement · subplan: SP-3 · ui: yes

  Classification: complexity medium; scope full_feature; risk medium; coupling medium; confidence low; estimate 110 minutes.
  Owner round 9 q1/q2: one card per existing parametric type, default values from PARTIDA_MESA (rectangular 240 × 90 × 75 cm); selecting the card adds the table and opens its existing inspector. No pre-creation form. Existing fixed Imperial catalogue pieces remain, without inventing a new parametric type. Shopping list shows quantities and dimensions, without rental pricing.
  Reuse mesaDePedido, agregarConjuntoPorDefecto extended with a typed request, EditorConjuntoMesa and chair placement. Keep cm in the model and metres in the UI; rectangular limits 100–600 cm length, 40–150 cm depth, 40–110 cm height; chairs 0–40, actual capacity controls the list. Preserve supported dispositions, parent transforms and objects on the table; refuse MAX_NODOS overflow without half a table.
  Implement and register taller:test-mesas-piloto = tsx scripts/test/test-taller-mesas-piloto.ts; test creation, limits, requested versus placed chairs, movement/rotation, undo and deterministic tool parity. Strings in textos-taller-esenciales.ts for later translation.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.

  - Acceptance / functional: Adding a rectangular table exposes length, depth and chair count, selects it in the inspector and updates the real shopping list with placed chairs, including capacity warnings and undo. Check: `npx tsx scripts/test/test-taller-mesas-piloto.ts`
  - Acceptance / functional: The existing agregar_mesas, cambiar_mesas and cambiar_sillas tools produce the same table dimensions and actual chair counts as manual editing without a paid AI call. Check: `npx tsx scripts/test/test-taller-mesas-piloto.ts`

  - Acceptance / functional: Each existing parametric table type has a creation card that adds its default-sized table and opens the inspector; rectangular tables use 240 × 90 × 75 cm by default and the shopping list contains quantities and dimensions without rental prices. Check: `npx tsx scripts/test/test-taller-mesas-piloto.ts`

- [ ] T3.3 — Group existing party props under Backing without changing their identities · repo: pictures · after: T3.2 · verify: `npx tsx scripts/test/test-backing-piloto.ts` · files: src/components/tres-d/FondosYMuebles.tsx, src/lib/catalogo/backing.ts, src/components/tres-d/textos-taller-esenciales.ts, scripts/test/test-backing-piloto.ts · resources: taller:scene, taller:scene · covers: R11 · kind: implement · subplan: SP-3 · ui: yes

  Classification: complexity medium; scope full_feature; risk medium; coupling medium; confidence low; estimate 80 minutes.
  Owner round 9 q3: move the seven cards from their old visual groups to one Backing group in Taller Fondos y muebles; do not retain duplicate card aliases and do not add them to Shopify /catalogo. Keep semantic GrupoCatalogo and ASIGNACION_FONDOS unchanged: compute the display grouping from the explicit seven-ID set so existing saved IDs, RAG and photo readers remain compatible.
  Update search and panel counters together; searching Backing finds all seven, original names still find each, and escenografia/mobiliario repository filters keep ownership. Preserve adding by click, drag and keyboard. Register taller:test-backing-piloto; compare all before/after IDs, original search terms, addability and repository consistency. Do not add imaginary Shopify products or prices.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.

  - Acceptance / functional: Backing lists panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico, each addable; existing IDs, saved scenes, repository ownership, search and AI/photo discovery remain compatible. Check: `npx tsx scripts/test/test-backing-piloto.ts`

  - Acceptance / functional: The seven Backing cards appear once in the new Taller group and no longer in their previous visual groups; Shopify /catalogo is unchanged and the original names and AI/photo discovery still resolve the same IDs. Check: `npx tsx scripts/test/test-backing-piloto.ts`

- [ ] T3.4 — Verify and repair the GLB geometry and material export · repo: pictures · after: T3.3 · verify: `npx tsx scripts/test/test-exportadores-escena-taller.ts` · files: src/components/tres-d/exportar-escena-glb.ts, src/components/tres-d/exportadores-escena-globos.ts, src/components/tres-d/ExportarEscenaTaller.tsx, scripts/test/test-exportadores-escena-taller.ts, scripts/test/fixtures/req021-export-scene.json · resources: taller:scene · covers: R10 · kind: implement · subplan: SP-3 · ui: yes

  Classification: complexity high; scope full_feature; risk medium; coupling medium; confidence low; estimate 140 minutes.
  Extend existing exporter tests with a deterministic real-scene fixture: translated/rotated rectangular table and chairs, Backing, balloons with distinct colours/finishes, nested attachments and room. Decode GLB accessors and transforms; do not test only the magic header or a synthetic group. Compare model-space cm converted once to metres, all world bounds/positions within 1 mm and base-colour channels within 1/255 in the same colour space.
  Keep editor-only lights/gizmos out, retain intended room visibility and instancing where the importer supports it. A real Blender importer must decide whether EXT_mesh_gpu_instancing or material extensions need a compatibility path; preserve the source scene and document any appearance limitation. No claim of identical lighting/rendering.

  - Acceptance / functional: The exported GLB preserves actual scene world transforms, dimensions in metres, visible instances and base colours without mutating the editor or calling the network; export failure is visible and retryable. Check: `npx tsx scripts/test/test-exportadores-escena-taller.ts`

- [ ] T3.5 — Implement the Taller browser and Blender verification harness · repo: pictures · after: T3.4 · verify: `npm run taller:test-harness-esenciales` · files: scripts/test/test-integracion-taller-esenciales.ts, scripts/test/blender/verificar_glb.py, scripts/test/test-harness-taller-esenciales.ts, docs/req021-blender.md, package.json · resources: package.json scripts, taller:scene · covers: R9, R10, R11 · kind: implement · subplan: SP-3 · ui: no

  Classification: complexity high; scope full_feature; risk medium; coupling medium; confidence low; estimate 120 minutes.
  Author scripts and npm commands taller:test-harness-esenciales (deterministic harness tests) and taller:test-integracion-esenciales (real flow). Owner round 9 q4 authorizes portable Blender LTS under ~/.local/opt/blender, without pacman/system-package changes, for automatic background import plus one owner manual opening. T3.5 owns explicit provisioning: select and document an official supported LTS release for this platform, pin its archive URL/version and published checksum, verify the download and expose the executable via BLENDER_EXECUTABLE. Do not replace an existing installation without preserving it. Provisioning is an explicit setup step, never an implicit harness download; missing executable is blocked, never skipped or passed. No installation is performed in this HQ planning session.
  Use SP-1 isolated-schema and session fixtures, no paid AI and no production access. Build/start on loopback, create a table through UI, adjust size/chairs, add each Backing prop and download the scene GLB. Blender runs background with bounded timeout, opens that downloaded file, verifies evaluated world-space instances, orientation, bounds and base colours at the T3.4 tolerances and records importer/version/limitations. Output .evidence/REQ-021/SP-3.integration.json with source revision, exact command and measurements. Clean up server/schema in finally. Package scripts register T3.2/T3.3 test commands here before T3.6 runs; local implementation checks may invoke tsx directly until registration.
  Own package.json registration for all new SP-3 npm aliases. Preserve scripts registered by other subplans.
  Also author taller:test-composicion-esenciales, the same real entrypoint flow with a Plan 3 session and an unauthorized Plan 1 direct API request; record .evidence/REQ-021/CG-2.integration.json on the integrated candidate.

  - Acceptance / functional: The harness starts a real next start build, drives table and Backing operations in Chromium, downloads the actual GLB and compares Blender-imported positions, metre dimensions and base colours against the fixture; missing Blender is reported as blocked. Check: `npm run taller:test-harness-esenciales`

  - Acceptance / functional: An explicit setup step provisions a checksum-verified official portable Blender LTS under ~/.local/opt/blender without system-package changes, records its version and executable, and the real import harness never treats a missing executable as a pass. Check: `npm run taller:test-harness-esenciales`

- [ ] T3.6 — Run the real Taller essentials integration scenario · repo: pictures · after: T3.5 · verify: `npm run taller:test-integracion-esenciales` · files: .evidence/REQ-021/SP-3.integration.json · resources: taller:scene · covers: R9, R10, R11 · kind: test · subplan: SP-3 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 50 minutes.
  Execute the already-authored harness only; report failures without repairing source in this task. The owner manual Blender check in SPEC Pruebas is separate product evidence.

  - Acceptance / integration: A user adds a rectangular table from its type card, edits size and chairs and sees actual quantities and dimensions without rental prices in the shopping list; Taller Fondos y muebles has one Backing group containing the seven existing props moved from their former visual groups, with saved IDs and AI/photo discovery preserved; the exported GLB opens in portable Blender LTS with the same layout, sizes in metres and base colours. Check: `npm run taller:test-integracion-esenciales`
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

  Behavior and task breakdown reflect the owner answers to round 9. Subplan and design confirmation remain separate owner actions; focus stays SP-2.

- [ ] T4.1 — Copy the approved saved-projects design contract · repo: pictures · after: T92 · verify: `cmp -- design/contracts/proyectos@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.md` · files: design/contracts/proyectos@v1.md · resources: design:T4.1 · covers: R6, R7 · kind: design · subplan: SP-4 · ui: no

  Classification: complexity low; scope small_change; risk low; coupling medium; confidence medium; estimate 20 minutes.
  Copy the pinned owner-approved contract without rewriting it.

  - Acceptance / static: The repository contract is byte-identical to the owner-approved proyectos@v1 artifact. Check: `cmp -- design/contracts/proyectos@v1.md /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.md`

- [ ] T4.2 — Implement versioned project storage and scene validation · repo: pictures · after: T4.1 · verify: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts` · files: scripts/migrations/038_proyectos.sql, src/lib/proyectos/contrato.ts, src/lib/proyectos/servicio.ts, src/lib/proyectos/repositorio.ts, src/lib/proyectos/validar-escena.ts, src/lib/cuentas/dependientes.ts, scripts/test/test-proyectos-servicio.ts · resources: proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: no

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 170 minutes.
  Use getRagPool and SP-1 isolated schema helper. Migration 038 creates proyectos with UUID id, owner FK RESTRICT, name, schema_version=1, JSONB scene, revision >=1 and created/updated timestamps plus owner/update index. Register it as work in dependientes.ts. Name trimmed 1–120 characters, document UTF-8 limit 2 MiB; enforce existing MAX_NODOS=150 and room limits, complete Pieza variants and references using runtime validation, never the shallow legacy type guard as server validation. Unsupported schema is a stable recoverable error; do not silently drop fields or normalize away user work.
  Update WHERE id AND owner_id AND revision; increment in same statement, zero rows on stale yields conflict. For create/retry use client mutation UUID unique per account, reject different content under reused key; imports additionally use a unique account+raw-source SHA-256. Lock the owner row in the write transaction with a lock mode conflicting with deletion; FK RESTRICT is the final barrier so delete cannot erase work even if registry precheck races. Service derives caller identity from trusted session context; no client owner id. Owner round 9 q6: document is name + complete Escena (including salon, room, materials and scene-node attachments). Separately stored AI conversations and generated images remain in the browser and are not promised across browsers. Preserve all valid scene fields and references; no local data is erased.
  Expose project-document@1: {schemaVersion:1, nombre, escena}; stored result adds id, ownerId, revision and timestamps. Register proyectos:test-servicio = tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts. Tests cover migrations twice, cross-account ownership, CAS race, idempotency, validation, rollback and delete race.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.
  Migration 038 also creates account-scoped mutation receipts and legacy-import receipts: UNIQUE(account_id, mutation_id) binds payload SHA-256 and committed project/revision; UNIQUE(account_id, raw_source_sha256) binds one imported project. A repeated identical create/update returns the committed receipt without another write or revision increment; a reused key with different payload fails. Import receipt and project insert commit together; do not rely on browser-only markers. Receipts are included in account-work cleanup/constraints and are not exposed across accounts.

  - Acceptance / functional: A project is stored in Postgres under the session account with a versioned complete scene document; conditional updates atomically increment revision and reject stale writes without changing stored data. Check: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts`
  - Acceptance / functional: Account deletion is refused when projects exist, including a project-save/account-delete race; malformed or oversized documents, duplicate node IDs, nonfinite dimensions and broken or cyclic parent links are refused without writes. Check: `npx tsx --conditions=react-server scripts/test/test-proyectos-servicio.ts`

- [ ] T4.3 — Implement project APIs with per-resource authorization · repo: pictures · after: T4.2 · verify: `npm run proyectos:test-api` · files: src/app/api/proyectos/route.ts, src/app/api/proyectos/[id]/route.ts, src/lib/proyectos/http.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-proyectos-api.ts, package.json, scripts/test/test-checkpoint-proyectos.ts · resources: package.json scripts, proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: no

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 100 minutes.
  GET /api/proyectos accepts cursor, q (trimmed name substring, at most 120 characters), scope=mine|all (default mine) and ownerId (UUID, only with scope=all and proyectos.ver_todos). Filter the entire authorized server collection before pagination, never only the loaded page. Return metadata only, at most 50 rows, ordered by updatedAt DESC then id DESC; use a validated opaque cursor bound to scope/q/ownerId and reject cursor/filter mismatch with 400. Escape SQL wildcard characters so name search is literal and parameterized. scope=all requires proyectos.ver_todos and includes owner display identity. The owner selector contains only authorized project-owner metadata; never enumerate unrelated accounts. A forged foreign ownerId in own scope is refused without disclosure. Filter changes reset the cursor/results; stale responses from the previous query cannot replace current results. Show a loaded count, not an invented total, and preserve loaded rows on next-page failure. GET /api/proyectos/[id] returns authorized document. POST /api/proyectos creates for the session account (also used for Save copy/import). PATCH /api/proyectos/[id] requires baseRevision and mutationId. Owner round 9 q7: foreign originals are read-only; Save copy creates a caller-owned project and requires taller.usar. Opening never transfers ownership and staff/admin cannot update another owner original.
  Route permission map: own project routes require taller.usar; read-all may be allowed to proyectos.ver_todos even for custom roles without taller.usar, and the service checks resource ownership independently. Same-origin guard for mutations, schema validation on every request, no-store responses; invalid JSON 400, unauthenticated 401, unauthorized collection scope 403, inaccessible/missing item 404, stale revision 409, too large 413. No deletion UI/API is included in this pilot scope; it is not required by R6/R7. Register proyectos:test-api using real isolated database and Request-based route tests.
  Author proyectos:test-checkpoint = tsx --conditions=react-server scripts/test/test-checkpoint-proyectos.ts: start next start on loopback against the isolated schema and run real HTTP ownership/CAS/delete-race checks, emitting SP-4.storage.json. No import-only check is called integration.

  - Acceptance / functional: Project APIs list and read only owned projects unless proyectos.ver_todos is granted, refuse unauthorized writes and cross-origin mutations, and return stable version conflicts without leaking another owner document. Check: `npm run proyectos:test-api`

  - Acceptance / functional: Project-name search and authorized owner filters apply to the whole server collection before pagination; filter-bound cursors, literal name matching and per-account authorization prevent skipped later-page matches and metadata disclosure. Check: `npm run proyectos:test-api`

- [ ] T4.31 — Run the project storage and authorization checkpoint · repo: pictures · after: T4.3 · verify: `npm run proyectos:test-checkpoint` · files: .evidence/REQ-021/SP-4.storage.json · resources: proyectos:document · covers: R6, R7 · kind: test · subplan: SP-4 · ui: no

  Classification: complexity medium; scope small_change; risk medium; coupling high; confidence medium; estimate 35 minutes.
  Execute the checkpoint runner authored by T4.3 against the isolated database; write exact observed API/database outcomes and tree identity. Stop downstream UI work on failure; no source repairs in this task.

  - Acceptance / integration: Before UI work, the real project service and API checks pass atomic stale-write rejection, account isolation, validation, import retry keys and the project-save/account-delete race. Check: `npm run proyectos:test-checkpoint`

- [ ] T4.4 — Implement the project list and conflict-safe Taller saving · repo: pictures · after: T4.31 · verify: `npx tsx scripts/test/test-proyectos-cliente.ts` · files: src/app/proyectos/page.tsx, src/components/proyectos/ListaProyectos.tsx, src/components/proyectos/EstadoGuardado.tsx, src/components/proyectos/ConflictoProyecto.tsx, src/components/proyectos/useProyecto.ts, src/components/proyectos/textos-proyectos.ts, src/components/tres-d/Taller3D.tsx, src/app/3d/page.tsx, src/lib/proyectos/borrador-local.ts, scripts/test/test-proyectos-cliente.ts, src/app/proyectos/[id]/page.tsx · resources: proyectos:document · covers: R6, R7 · kind: implement · subplan: SP-4 · ui: yes

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence low; estimate 180 minutes.
  Owner round 9 q5/q7: first Save explicitly asks for a name; subsequent edits autosave with visible status and Save now. The 500 ms serialized debounce is a Planner technical default inherited from the local saver, not a user-specified timing. List route /proyectos and deep link /3d?proyecto=<uuid>. Staff all-project list can be read with proyectos.ver_todos; custom roles lacking taller.usar need a read-only project view, not a bypass that grants editing tools. Owner-only editable project route checks both permissions and ownership server-side.
  Keep one in-flight update per project, latest scene queued behind it, bind response to account+project+request identity and submitted edit generation. A response acknowledges only its submitted generation; older completions cannot clear newer dirty work. On 409 stop queue until explicit resolution; no automatic overwrite or retry with fetched revision. Network/401/permission failure retains a namespaced local draft and exposes retry. Switching/new project or navigation with dirty/pending edits asks to save, keep local draft or cancel; ignore completions for previous identity.
  Namespace new drafts by account and project; never auto-open the old global scene after account switch. On sign-out/auth loss clear scene state and query caches; a different account cannot enumerate/open drafts. Keep recovery drafts for the same account; do not delete original legacy data. Reset undo history and scene conversation identity on project switch; preserve the full document and do not silently attach another project conversation. Register proyectos:test-cliente with out-of-order replies, offline/reload, account switch and conflict reducer tests. UI states per proyectos@v1.
  Use the direct tsx command for focused verification before harness registration; do not edit package.json here. The harness later registers the stated npm alias for convenient use.
  Provide /proyectos/[id] as a server-authorized read-only scene view for proyectos.ver_todos without taller.usar; link staff reads there, never bypass the /3d Taller permission. Save copy also requires taller.usar. Register both project pages in the T4.3 permission map and test custom staff read-only access.

  Project-list name search and owner filtering use T4.3 server queries over the entire authorized collection. Debounce search, reset cursors on filter change, key requests by normalized query and ignore late responses; preserve loaded rows and expose retry for a failed next page. Do not perform page-only client filtering.

  - Acceptance / functional: The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`
  - Acceptance / functional: Two open copies cannot silently overwrite each other: a 409 stops autosaving, keeps the unsent local scene and offers loading the server version or saving a new owned copy; staff/admin read foreign originals without write access and may save an owned copy only with taller.usar. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`

  - Acceptance / functional: The first named save is explicit and later edits autosave; a project list search finds authorized matches beyond the first loaded page, filter changes reset pagination and obsolete query responses cannot replace current results. Check: `npx tsx scripts/test/test-proyectos-cliente.ts`

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

  Seed at least 51 authorized project metadata rows and place a uniquely named match beyond the first unfiltered page. Verify server search finds it, staff owner filtering is authorization-bound, regular accounts cannot query foreign owner metadata, filter changes discard stale cursors/responses, and next-page failure preserves visible results with retry.

  - Acceptance / functional: The project harness starts real Next entrypoints against an isolated test schema and drives independent authenticated browser contexts through persistence, access denial, conflicts and legacy import. Check: `npm run proyectos:test-harness`

  - Acceptance / functional: The browser harness seeds more than fifty projects and verifies a matching project beyond the first page, authorized owner filtering, next-page retry and stale search-response rejection without leaking foreign metadata. Check: `npm run proyectos:test-harness`

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

### M3 — English / Spanish
The interface follows the browser language on the first visit and the account's choice afterwards; the Taller 3D and navigation are fully in English first, then product texts, the remaining screens and the AI replies.

- **SP-8 — Language switch, Taller 3D and navigation in English** (UI: `idioma-taller@v1`): A language mechanism with first-visit detection, a switch remembered per account, and every string of the Taller 3D and the navigation in both languages. Covers R12.
- **SP-9 — Product and decoration texts in English** (UI: `textos-producto@v1`): English names and descriptions for every product and decoration are generated once from the Spanish source, stored, shown when the language is English with the Spanish text as fallback, and correctable by an administrator. Covers R12.
- **SP-10 — Remaining screens and AI replies in English** (UI: `idioma-resto@v1`): The chat tools, catalogue, administration, spend and statistics screens are fully in English, and the scene AI and the chat tools reply in the user's language. Covers R12.

### M4 — Editable modules and chat → 3D
Users edit modules and quartets beyond colours, and the normal chat recommends ready-made 3D decorations that open in the workshop.

- **SP-11 — Editable modules and quartets** (UI: `modulos-editables@v1`): A user edits a module or quartet in the scene beyond its colours (the exact edits are settled with the owner in this subplan) and the counts and shopping list update. Covers R15.
- **SP-12 — Normal chat recommends ready-made 3D decorations** (UI: `chat-a-3d@v1`): In two or three messages the normal chat defines the need and recommends existing 3D decorations that open in the Taller 3D as a new project, using the real catalogue and engine. Covers R13.

### M5 — Pilot release
The pilot runs in production with real accounts: the first administrator exists, every shipped subplan is published, a production smoke passes and anything cut is listed.

- **SP-13 — Pilot release in production**: Every approved subplan is published to production with its migrations, the first administrator is created, an end-to-end flow (invite → activate → save project and decoration → spend appears → export GLB) passes against production, and the cut list is recorded. Covers R14.
