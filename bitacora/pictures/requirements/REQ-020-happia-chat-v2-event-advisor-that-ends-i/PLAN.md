---
req: REQ-020
status: review
created: 2026-10-20
---
# Plan — Happia chat v2 event advisor that ends in a brief

## Approach
New section **Asesor Happia** (`/asesor`, APIs under `/api/asesor/*`) inside the Pictures Next app, built from
`origin/main` on branch `feat/req-020-asesor-happia` (worktree `~/dev/pictures-wt/asesor`). A tool-calling agent on
`@sempertex/agente-core` (same pattern as `/api/asistente-guiado`) fills a typed `EventBrief` through tools; progress is
computed from its required fields. Persistence in Supabase Postgres via `pg` and its own migrations folder/runner.
Own auth: two hashed accounts (`user`, `admin`), signed cookie, `/asesor` excluded from the `APP_PASSWORD` proxy and
guarded by its own check. Chat UI reuses `src/components/guiado/*`; photos via `preparar-foto` stored as bytea and sent
inline to the model; voice via the existing Whisper route. `/happie` and its contracts are not touched.

## Global constraints
- Do not modify `/happie`, `src/lib/happie/*`, the webhook or `happie.v1`/`happie.v2` contracts (R14).
- Supabase = Postgres only (`SUPABASE_DB_URL`, transaction pooler, `ssl`); no Supabase Auth/Storage/SDK.
- Spanish customer copy, warm "tú"; mobile-first (viewport from `src/app/asistente/page.tsx`); Catppuccin-compatible
  existing design tokens.
- No secrets in the repo; new env vars documented in `.env.example`: `SUPABASE_DB_URL`, `ASESOR_SESSION_SECRET`.
- Every task keeps `npm run gate`, `npx tsc --noEmit` (no new errors) and `npm run lint` (0 errors) green.
- Personal data (name, phone, address, budget) never appears in the vendor brief, logs or telemetry payloads.

## Tasks

### M1 — Text conversation to an approved brief, admin watching (Halloween, Thu 29 Oct)
- [ ] T1 — Worktree from origin/main; Supabase pool (`src/lib/asesor/db.ts`), migrations folder `scripts/migrations-asesor/` + runner (`npm run asesor:migrate`), schema: accounts, conversations, messages, attachments, briefs; `npm run asesor:test` script wired into the gate · verify: `npm run asesor:migrate && npm run asesor:test` · covers: R6
- [ ] T2 — Own auth: scrypt-hashed accounts `user`/`admin`, seed script with generated passwords, `/asesor/login`, signed session cookie, proxy matcher exclusion for `/asesor` + `/api/asesor`, role guard helpers · after: T1 · verify: `npm run asesor:test` · covers: R1, R12
- [ ] T3 — Advisor agent: `EventBrief` schema (R3 fields, event kinds incl. corporate/school), system prompt, tools (save fields, propose summary, approve), progress calculator, streaming route `/api/asesor/conversar` persisting every turn, retry on provider failure; deterministic tests with a fake `ChatPort` · level: architecture · after: T1 · verify: `npm run asesor:test` · covers: R3, R4, R6, R13
- [ ] T4 — Chat UI `/asesor`: guiado components, privacy + test-version notices, progress bar, resume by conversation id in localStorage (transcript reloaded from the server) · after: T2, T3 · verify: `npm run asesor:test && npx tsc --noEmit` · covers: R2, R4, R5
- [ ] T5 — Brief: summary to approve/correct, stored full brief + vendor version without name/contact/budget, printable one-page view · after: T3 · verify: `npm run asesor:test` · covers: R11
- [ ] T6 — Admin monitor `/asesor/admin`: conversation list (status, progress, last question, 5 s refresh) and read-only detail (transcript, brief); `user` gets 403 · after: T2, T5 · verify: `npm run asesor:test` · covers: R12
- [ ] T7 — M1 acceptance: e2e script (login → conversation → approved brief → visible to admin), one real Gemini conversation, `/happie` regression (`npm run happie:test-webhook`), env vars on Vercel + VPS, deploy · after: T4, T5, T6 · verify: `npm run gate && npm run happie:test-webhook` · covers: R1–R6, R11–R14

### M2 — Photos and voice notes (~Fri 6 Nov)
- [ ] T8 — Photo upload from camera/gallery (`capture` + gallery), `preparar-foto`, bytea storage, inline to the model for first look, confirm + likes/dislikes per photo, venue photo flag, photos in brief/admin · after: T7 · verify: `npm run asesor:test` · covers: R7, R11
- [ ] T9 — Voice notes: `BotonVoz`/`useDictado` + `/api/voz/transcribir` for advisor sessions (VOZ_* env from the `voz-decoracion` container), transcript stored as the customer's text · after: T7 · verify: `npm run asesor:test` · covers: R8
- [ ] T10 — M2 acceptance on a phone viewport (photo + voice conversation to brief), deploy · after: T8, T9 · verify: `npm run gate` · covers: R7, R8

### M3 — Directions, themed items and standard packages (~Thu 19 Nov)
- [ ] T11 — Happia catalogue daily cache in Postgres (refresh when older than 24 h) + fallback list seeded from the last good read; read-only reuse of `HappiaClient` · after: T7 · verify: `npm run asesor:test` · covers: R10
- [ ] T12 — Directions: editable config of 12 decorations from `biblioteca-sempertex/decoraciones.json` (with photos) + themed items, tool to show them to undecided customers · after: T7 · verify: `npm run asesor:test` · covers: R9
- [ ] T13 — Standard package/service first: tool matching event/theme/city/guests, card with estimated price + notice, recorded in the brief · after: T11 · verify: `npm run asesor:test` · covers: R10, R11
- [ ] T14 — Scripted conversation set (birthday, corporate, school, undecided, photo-led, refusals, prompt injection) run against the real model; fix prompt gaps · after: T12, T13 · verify: `npm run asesor:test` · covers: R3, R9, R10

### M4 — Acceptance and close (before the 23 Nov rehearsal)
- [ ] T15 — Full acceptance on production: every R1–R14 check, `/happie` unchanged, report with evidence, bitácora updated · after: T10, T14 · verify: `npm run gate && npm run happie:test-webhook` · covers: R1–R14

## Verification
- `npm run asesor:test` (unit + fake-model conversation tests) and `npm run gate` green; `npx tsc --noEmit` no new
  errors; `npm run lint` 0 errors; `npm run happie:test-webhook` unchanged.
- Production walkthrough on a phone viewport: login as `user` → conversation by text, photo and voice → summary
  corrected once and approved → brief + vendor version (no name/contact/budget) visible to `admin` within 5 s; `user`
  gets 403 on admin routes.

## Rulings
<!-- Judgment calls made during execution without asking. -->

## Progress log
- 2026-10-20 Plan drafted after rounds 1–2; Supabase pooler connection verified.
