---
req: REQ-024
status: draft
created: 2026-11-05
revision: 1
---
# Plan — REQ-024 — WhatsApp conversational module: balloon count and colour detection

## Approach
New isolated package `services/whatsapp-globos/` (TypeScript, Node 24) in the Pictures repo. It receives WhatsApp
Cloud API webhooks, downloads the photo, and obtains count and colours **by running the existing recogniser itself and
calling `ai-api` directly** (owner ruling: option b). It adds no counting or colour logic.

Evidence from the code (read-only, branch `feat/req-014-72h-marathon-…`):
- `scripts/eval/estructuras/conteo.ts` already does exactly this outside Next: `tsx --conditions=react-server`, imports
  `analizarReferenciasV2` (`src/lib/ia/amaterasu/analizar-referencias-v2.ts`) and `llamarPythonConteoReferencia`
  (`src/lib/ia/nucleo/python-adapter.ts`), disables DB telemetry, signs with `INTERNAL_HMAC_SECRET`. So assumption A1
  has precedent; T4 proves it for this package.
- `ai-api` exposes `POST /internal/v1/ia/conteo-referencia` (`services/ai-api/app/main.py:2097`), HMAC-signed,
  1–12 structures per photo, exact only up to 40 balloons (`MAX_GLOBOS_EXACTO`, ADR-0031).
- Colours come from the recogniser blueprint (`appearance.observed_colors`, `measured_colors`) and
  `analisis_color` (`src/app/api/references/analyze/route.ts`).

**Isolation.** One adapter file, `services/whatsapp-globos/src/adapters/reconocedor.ts`, is the only place that imports
`src/lib/**`. Everything else depends on a plain `LecturaGlobos` type and on ports (Meta client, recogniser, store,
LLM), so the whole module is testable with fakes and a change under `src/lib/ia` breaks one file and one contract test.
No other repo file is edited (the `matcher` in `src/proxy.ts` is not touched: the module never goes through Next).

**Order.** M1 is a walking skeleton that runs end to end in `--dry-run` with fixed-template replies; M2 adds the
conversation (follow-ups, corrections, guard); M3 hardens, proves parity with the web path and ships the deploy recipe.
Live Meta/Gemini steps are isolated in M3 so M1–M2 need no external credentials.

Alternatives (recorded): Next route behind a machine secret (rejected by owner: touches shared `proxy.ts`); Python
module next to `ai-api` (rejected: duplicates typed clients).

## Global constraints
- Reuse, never modify: recogniser, `ai-api` conteo-referencia, ADR-0031 semantics (SPEC Constraints).
- Work in a dedicated worktree/branch; touch only `services/whatsapp-globos/**` (R12). Another agent edits other files.
- No secrets in code, logs or plan; env names only (R11). Photos never persisted or logged (R4, R8).
- Every reply figure comes from the stored reading or a labelled user correction (R7).
- Spend: live vision calls only in M3 under a US$1 cap; any other test uses fakes.

## Tasks
### M1 — Walking skeleton (webhook → reading → template reply, dry-run)
- [ ] T1 — Scaffold `services/whatsapp-globos` package (tsconfig, test runner, lint, env schema, README) · kind: implement · repo: pictures · files: services/whatsapp-globos/package.json, services/whatsapp-globos/src/config.ts · verify: `npm --prefix services/whatsapp-globos test` · covers: R11, R12
- [ ] T2 — Webhook server: GET challenge, POST signature check on raw body, fast 200, idempotent queue per message id · kind: implement · repo: pictures · after: T1 · files: services/whatsapp-globos/src/webhook/server.ts, services/whatsapp-globos/src/webhook/signature.ts · verify: `npm --prefix services/whatsapp-globos test -- webhook` · covers: R1, R2, R3
- [ ] T3 — Meta media client and image validation (media id → URL → authenticated fetch, magic bytes, size, no logging of bytes) · kind: implement · repo: pictures · after: T1 · files: services/whatsapp-globos/src/meta/media.ts, services/whatsapp-globos/src/meta/image.ts · verify: `npm --prefix services/whatsapp-globos test -- media` · covers: R4
- [ ] T4 — Recogniser adapter: `LecturaGlobos` type, the single `src/lib` import boundary, exact/estimate normalisation, contract test against a recorded reading · kind: implement · repo: pictures · after: T1 · files: services/whatsapp-globos/src/adapters/reconocedor.ts, services/whatsapp-globos/src/lectura.ts · verify: `npm --prefix services/whatsapp-globos test -- adapter` · covers: R5, R6, R12
- [ ] T5 — Policy and state store (own SQLite): allow-list, per-number daily quota, global daily cap, hashed phone, restart-safe counters · kind: implement · repo: pictures · after: T1 · files: services/whatsapp-globos/src/policy/policy.ts, services/whatsapp-globos/src/store/sqlite.ts · verify: `npm --prefix services/whatsapp-globos test -- policy` · covers: R8, R10
- [ ] T6 — Pipeline, ES/EN template replies, Meta sender and `--dry-run` CLI · kind: implement · repo: pictures · after: T2, T3, T4, T5 · files: services/whatsapp-globos/src/pipeline.ts, services/whatsapp-globos/src/replies/templates.ts, services/whatsapp-globos/bin/dry-run.ts · verify: `npm --prefix services/whatsapp-globos test -- pipeline` · covers: R6, R13, R14
- [ ] T7 — Integration test: start the real server, post signed recorded Meta payloads against fake Meta and fake recogniser servers, assert reply, idempotency, allow-list and cap · kind: test · repo: pictures · after: T6 · files: services/whatsapp-globos/test/integration/m1.test.ts · verify: `npm --prefix services/whatsapp-globos run test:integration` · covers: R1, R2, R3, R4, R5, R10, R14
- [ ] T8 — M1 audit (findings ledger) · kind: audit · repo: pictures · after: T7 · files: services/whatsapp-globos/audit/m1.findings.json · verify: `bitacora.py audit-ledger check services/whatsapp-globos/audit/m1.findings.json` · covers: R2, R4, R10, R11

### M2 — Conversation (follow-ups, corrections, guarded phrasing)
- [ ] T9 — Conversation state: last reading, user corrections (labelled, confirmation above threshold), retention job · kind: implement · repo: pictures · after: T8 · files: services/whatsapp-globos/src/conversation/state.ts · verify: `npm --prefix services/whatsapp-globos test -- state` · covers: R8, R7
- [ ] T10 — Conversational layer: intent routing (follow-up, correction, off-topic), LLM phrasing from structured reading, post-generation number/colour guard, language detection · kind: implement · repo: pictures · after: T9 · files: services/whatsapp-globos/src/conversation/router.ts, services/whatsapp-globos/src/conversation/guard.ts · verify: `npm --prefix services/whatsapp-globos test -- conversation` · covers: R7, R13
- [ ] T11 — Multi-photo bursts (1–3 images read together, per-number queue) · kind: implement · repo: pictures · after: T9 · files: services/whatsapp-globos/src/pipeline-burst.ts · verify: `npm --prefix services/whatsapp-globos test -- burst` · covers: R3, R5
- [ ] T12 — Integration test: scripted multi-turn conversations with a fake LLM, including a guard-trip case and prompt-injection caption · kind: test · repo: pictures · after: T10, T11 · files: services/whatsapp-globos/test/integration/m2.test.ts · verify: `npm --prefix services/whatsapp-globos run test:integration -- m2` · covers: R7, R8, R13
- [ ] T13 — M2 audit (findings ledger) · kind: audit · repo: pictures · after: T12 · files: services/whatsapp-globos/audit/m2.findings.json · verify: `bitacora.py audit-ledger check services/whatsapp-globos/audit/m2.findings.json` · covers: R7, R8

### M3 — Hardening, parity and deploy
- [ ] T14 — Failure paths (recogniser/ai-api/LLM timeout and error → retry message, no partial figures), health endpoint, structured logs · kind: implement · repo: pictures · after: T13 · files: services/whatsapp-globos/src/errors.ts, services/whatsapp-globos/src/health.ts · verify: `npm --prefix services/whatsapp-globos test -- failure` · covers: R9, R14
- [ ] T15 — Parity test: fixed photo set, module reading vs web `/api/references/analyze` reading (live Gemini, US$1 cap, external) · kind: test · repo: pictures · after: T14 · files: services/whatsapp-globos/test/parity/parity.test.ts · verify: `npm --prefix services/whatsapp-globos run test:parity` · covers: R5, R6
- [ ] T16 — Deploy recipe (Dockerfile, compose service on the VPS next to `ai-api`, env template, runbook with Meta setup steps) · kind: docs · repo: pictures · after: T14 · files: services/whatsapp-globos/Dockerfile, services/whatsapp-globos/RUNBOOK.md · verify: `docker build -t whatsapp-globos:test services/whatsapp-globos` · covers: R11, R14
- [ ] T17 — Live acceptance with the owner's Meta test number (human attestation: send photos, check replies and caps) · kind: test · repo: pictures · after: T15, T16 · covers: R1, R2, R4, R5, R10
- [ ] T18 — Final audit (findings ledger) · kind: audit · repo: pictures · after: T17 · files: services/whatsapp-globos/audit/final.findings.json · verify: `bitacora.py audit-ledger check services/whatsapp-globos/audit/final.findings.json` · covers: R9, R10, R11, R12

## Verification
- Per task: the focused command in each line. Whole suite only on audits.
- End to end (M1/M2): integration tests start the real server and drive signed Meta payloads; `--dry-run` processes a
  local photo through the real path without calling Meta.
- Parity (T15): same photos through the module and the web route give the same count and colour set.
- Acceptance (T17): from an allow-listed real number a photo gets count and colours; a non-listed number gets no vision
  call; going over the cap blocks the call. Needs owner credentials (below).

## Open inputs from the owner (batched, only needed from T15/T17)
Meta developer app and test number, permanent token, app secret, verify token, public HTTPS URL for the webhook,
initial allow-list, per-number and global daily caps, VPS deployment approval. Workspace note: the registered role
`pictures` points at a worktree, not `~/dev/pictures`; confirm the repo path at launch.

## Rulings
<!-- Judgment calls made during execution without asking. -->
- Planning: TypeScript and allow-list+quota taken as recommended defaults (owner did not object) — cost if wrong: low.

## Progress log
<!-- One line per meaningful step. -->
- 2026-11-05 Draft written from SPEC REQ-024; not classified (no PLAN.json yet), not approved.
