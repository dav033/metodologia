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
- **SP-3 — Taller essentials: rectangular tables, Backing and Blender export** (UI: `taller-esenciales@v1`): A user adds and edits a rectangular table with its size and chairs and the shopping list reflects it; the catalogue and the Taller show one Backing category with every existing party prop; the exported GLB opens in Blender with the same layout, sizes in metres and colours. Covers R9, R10, R11.

### M2 — Saved work, spend per user and the chat tools
Each signed-in user saves and reopens projects and decorations from any browser, every paid AI call is attributed to a user and a session, and the assisted chat is three separate tools gated by access plan.

- **SP-4 — Saved projects** (UI: `proyectos@v1`): A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss. Covers R6, R7.
- **SP-5 — Saved decorations** (UI: `decoraciones@v1`): A user saves a selection or composition from the scene with a name to their personal library on the server and places it in any of their projects; items already in the browser's own library are imported. Covers R8.
- **SP-6 — AI spend per user and session** (UI: `gasto-ia@v1`): Every paid AI call (Next and ai-api) is stored with user, sign-in session, work item (project or conversation), tool and kind (text or image); employees and administrators see totals grouped by project or conversation, filtered by user and kind; a usuario cannot open the view. Covers R4, R5.
- **SP-7 — Assisted chat as three tools and the decorations explorer** (UI: `herramientas-chat@v1`): The assisted chat becomes a balloon counter, a cost calculator and the normal chat, each with its own prompts and spend measured separately and never inventing counts or prices; a ready-made decorations explorer lists existing 3D decorations; each tool is reachable only with its access plan. Covers R13, R16.

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
