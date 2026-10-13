# REQ-004 — Plan (users + AI spend ledger and dashboard)

Order: after REQ-003 merge, before REQ-002 paid runs. Each step = one commit, verified in e3-verif, pushed to main.

## 1. Prices (no code at call sites)
- Researcher agent: current prices for every model in use (Gemini chat/vision models incl. thinking and cached
  tokens, gemini-embedding, FLUX.2 text/edit, FLUX.1 i2i/ControlNet per MP), with source URL and date.
- `src/lib/gastos/precios-ia.ts`: versioned table `{modelo, proveedor, desde, entrada, salida, pensamiento,
  cacheado, porImagen, porMegapixel}` + `costoDe(uso) → {usd, versionPrecio}`; mirrored as JSON for Python.
  Tests: known token/MP counts → expected USD; unknown model → null.

## 2. Database (Neon, new migration)
- `usuarios` (id uuid, email unique citext, nombre, rol admin|staff|sistema, hash, sal, activo, creado, ultimo_acceso).
- `sesiones` (id random 32 B, usuario_id, creada, expira, ip, agente, revocada).
- `gastos_ia` (id, ts, usuario_id, proveedor gemini|fal, modelo, funcion, conversacion_id, run_id, tokens_entrada,
  tokens_salida, tokens_pensamiento, tokens_cacheados, imagenes, megapixeles, costo_usd numeric(12,6),
  version_precio, fuente estimado|conciliado, resultado ok|error, ms) + indexes (ts), (usuario_id, ts), (funcion, ts).
- `conciliaciones` (mes, proveedor, total_real_usd, nota, cargado_por).
- Seed script `scripts/usuarios/crear-admin.ts` (asks email/password interactively; nothing in the repo).

## 3. Auth (flag `AUTH_USUARIOS_ENABLED`)
- `src/lib/auth/usuarios.ts` (scrypt hash/verify, constant-time), `sesiones.ts` (create/read/revoke),
  `usuarioDeRequest(request)` → `{id, rol, email} | null`; `src/proxy.ts` and `isAuthenticatedRequest` read it.
- `/login` gains email field; `/api/login` and `/api/logout`; account menu (name, change password, logout).
- Dev: fixed `dev-local` user unless `DEV_REQUIRE_LOGIN=1`. Old shared password stays while the flag is off.
- Admin «Usuarios» tab: create, disable, reset password, change role.
- Tests: hash/verify, session expiry/revocation, role guard, flag off = old behaviour.

## 4. Ledger writer + instrumentation
- `src/lib/gastos/registrar-gasto.ts`: `registrarGasto(fila)` async fire-and-forget into Neon (batching, never
  throws); request context (`usuario`, `funcion`, `conversacion`) via AsyncLocalStorage set at each route.
- Hook the three existing choke points instead of every call site: `registrarGemini`, `envolverClienteGemini`,
  the FLUX `registrar()` callback; remove the hard-coded escena-ia price (use `costoDe`).
- Python service: accept signed `x-usuario-id` / `x-funcion` headers (HMAC with the existing internal secret),
  write the same row (shared price JSON); VPS deploy announced beforehand.
- Batch/eval scripts: `sistema` user + `run_id`.
- Audit test: a static check that every module importing the Gemini/fal clients goes through the wrapped client
  (fails if a new unwrapped call site appears).
- Backfill script from existing Postgres telemetry (user `anterior`), dry-run first.

## 5. Dashboard «Gastos» (`/admin/gastos`, admin only)
- API `/api/admin/gastos` (SQL aggregates with filters: range, user, provider, feature, model).
- Page: totals today / 7 d / month (+ vs previous period), daily stacked bars by provider, bars by user / feature /
  model, top 10 conversations (link to the audit log), detail table with filters and CSV export, "sin precio" rows
  flagged. Charts with the project's existing chart approach (or lightweight SVG).
- «Mi consumo» in the account menu (own month total + by feature).
- Reconciliation form (US-5): real monthly total per provider vs ledger, gap %.

## 6. Verification
- Unit tests per module; integration test with a fake provider through each wrapped client → exactly one row.
- Browser check on 127.0.0.1:3010: two users, a scene-AI turn and one FLUX render each → dashboard shows both.
- One paid smoke run (cap US$0.10: 2 Gemini turns + 1 FLUX image), compare ledger vs provider console.
- Bitácora: decision on auth design (D-0xx), SUMMARY, PENDING.

## Later (not in this REQ)
Caps per user / provider / feature, alerts at 80 %, blocking — the ledger and `usuarioDeRequest` are the hooks.
