---
req: REQ-020
status: launched
created: 2026-10-20
---
# Plan — Happia chat v2 event advisor that ends in a brief

<!-- bitacora:status:begin -->
> Bloque generado, no editar a mano. Plan: launched · ejecución: running · hitos 3/4 · tareas 21/23 · generado: 2026-10-23T10:17:54-05:00

**M1 — Text conversation to an approved brief, admin watching (Halloween, Thu 29 Oct)** · dificultad alta · 7/7

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T1 | Worktree from origin/main; Supabase pool (`src/lib/asesor/db.ts`), migrations folder `scripts/migrations-asesor/` + runner (`npm run asesor:migrate`), schema: accounts, conversations, messages, attachments, briefs; `npm run asesor:test` script wired into the gate | alta | completada | gpt-6-luna | codex-luis | 7 |
| T2 | Own auth: scrypt-hashed accounts `user`/`admin`, seed script with generated passwords, `/asesor/login`, signed session cookie, proxy matcher exclusion for `/asesor` + `/api/asesor`, role guard helpers | alta | completada | gpt-6-luna | codex-luis | 1 |
| T3 | Advisor agent: `EventBrief` schema (R3 fields, event kinds incl. corporate/school), system prompt, tools (save fields, propose summary, approve), progress calculator, streaming route `/api/asesor/conversar` persisting every turn, retry on provider failure; deterministic tests with a fake `ChatPort` | alta | completada | gpt-6-luna | codex-2 | 2 |
| T4 | Chat UI `/asesor`: guiado components, privacy + test-version notices, progress bar, resume by conversation id in localStorage (transcript reloaded from the server) | alta | completada | gpt-6-luna | codex-luis | 2 |
| T5 | Brief: summary to approve/correct, stored full brief + vendor version without name/contact/budget, printable one-page view | alta | completada | gpt-6-luna | codex-2 | 2 |
| T6 | Admin monitor `/asesor/admin`: conversation list (status, progress, last question, 5 s refresh) and read-only detail (transcript, brief); `user` gets 403 | media | completada | gpt-6-luna | codex-2 | 2 |
| T7 | M1 acceptance: e2e script (login → conversation → approved brief → visible to admin), one real Gemini conversation, `/happie` regression (`npm run happie:test-webhook`), env vars on Vercel + VPS, deploy | alta | completada | gpt-6-luna | codex-luis | 2 |

**M2 — Photos and voice notes (~Fri 6 Nov)** · dificultad alta · 4/4

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T8 | Photo upload from camera/gallery (`capture` + gallery), `preparar-foto`, bytea storage, inline to the model for first look, confirm + likes/dislikes per photo, venue photo flag, photos in brief/admin | alta | completada | gpt-6-luna | codex-1 | 4 |
| T9 | Voice notes: `BotonVoz`/`useDictado` + `/api/voz/transcribir` for advisor sessions (VOZ_* env from the `voz-decoracion` container), transcript stored as the customer's text | alta | completada | gpt-6-luna | codex-1 | 2 |
| T10a | Extend the e2e runner with the M2 photo and voice scenarios | media | completada | gpt-6-luna | codex-luis | 1 |
| T10 | M2 acceptance on a phone viewport (photo + voice conversation to brief), deploy | alta | completada | gpt-6-luna | codex-2 | 13 |

**M3 — Directions, themed items and standard packages (~Thu 19 Nov)** · dificultad alta · 4/4

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T11 | Happia catalogue daily cache in Postgres (refresh when older than 24 h) + fallback list seeded from the last good read; read-only reuse of `HappiaClient` | alta | completada | gpt-6-luna | codex-luis | 2 |
| T12 | Directions: editable config of 12 decorations from `biblioteca-sempertex/decoraciones.json` (with photos) + themed items, tool to show them to undecided customers | media | completada | gpt-6-luna | codex-luis | 8 |
| T13 | Standard package/service first: tool matching event/theme/city/guests, card with estimated price + notice, recorded in the brief | alta | completada | gpt-6-luna | codex-2 | 9 |
| T14 | Scripted conversation set (birthday, corporate, school, undecided, photo-led, refusals, prompt injection) run against the real model; fix prompt gaps | alta | completada | gpt-6-luna | codex-1 | 10 |

**M4 — Acceptance and close (before the 23 Nov rehearsal)** · dificultad alta · 6/8

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T14a | Run full advisor entry-point integration and protected happie regression; record outcomes without fixes | baja | completada | gpt-6-luna | codex-luis | 20 |
| T15 | Full acceptance on production: every R1–R14 check, `/happie` unchanged, report with evidence, bitácora updated | alta | en curso | gpt-6.1-sol | codex-luis | 17 |
| T15b | Cross-check audit of T15: Full acceptance on production: every R1–R14 check, `/happie` unchanged, report with evidence, bitácora updated | alta | pendiente | — | — | 0 |
| T14.1a | Repair what blocks T14a | alta | completada | sonnet | claude-work | 2 |
| T14.2a | Integrate reviewed summary lifecycle and deployed evidence correction | media | completada | gpt-6-luna | codex-luis | 1 |
| T14.3a | Repair what blocks T14a | alta | completada | sonnet | claude-work | 1 |
| T14.4a | Repair what blocks T14a | alta | completada | sonnet | claude-work | 2 |
| T15.1 | Repair what blocks T15 | alta | completada | gpt-6-luna | codex-luis | 3 |
<!-- bitacora:status:end -->

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
- Evidence/report files under `docs/req-020/` are working artifacts for the verifiers: never commit them to the
  repo (cerebro rule: no non-code files in repos); copy them to `~/bitacora/pictures/artifacts/REQ-020/`.

## Contract enrichment
The scope in SPEC.md is unchanged. This is a draft classification of the already approved scope, not a new approval or execution authorization. Existing status and revision are preserved. T14a separates established command execution from the original T15 acceptance review. T7/T10 include operational deployment work and therefore are implement tasks; T14 authors evaluation fixtures/prompt fixes and is implement; T15 is read-only audit.

## File ownership
Paths below are planned outputs relative to the pictures implementation checkout, not claims that advisor files already exist. Each file has one producing task. Consumers import the declared contracts; media/catalogue producers fill optional contract fields rather than rewriting the shared page, brief view or agent transport. Shared_resources lists mutable or coordination-sensitive outputs; read-only imports of frozen producer contracts are described by interfaces and do not create a write conflict. T1 alone owns package/gate/env wiring; later tests and scenarios are discovered by its runner and the T7 harness.

| Owner | Paths | Responsibility |
|---|---|---|
| T1 | `package.json`, `scripts/test/gate.mjs`, `.env.example`, `src/lib/asesor/db.ts`, `src/lib/asesor/repository.ts`, `scripts/migrate-asesor.ts`, `scripts/migrations-asesor/001_initial.sql`, `scripts/test/asesor/run.ts`, `scripts/test/asesor/db.test.ts`, `scripts/integration/asesor-db.test.ts` | Provide an isolated advisor Postgres schema and repeatable migration/test entry points without using the Neon migration ledger. |
| T2 | `src/lib/asesor/auth.ts`, `src/app/asesor/login/page.tsx`, `src/app/api/asesor/login/route.ts`, `src/proxy.ts`, `scripts/seed-asesor.ts`, `scripts/test/asesor/auth.test.ts`, `scripts/test/test-proxy-matcher.ts` | Authenticate the two advisor roles independently of APP_PASSWORD and enforce server authorization before advisor data is exposed. |
| T3 | `src/lib/asesor/contracts.ts`, `src/lib/asesor/agent.ts`, `src/lib/asesor/tools.ts`, `src/lib/asesor/progress.ts`, `src/lib/asesor/prompts/base.ts`, `src/app/api/asesor/conversar/route.ts`, `src/app/api/asesor/conversations/route.ts`, `src/app/api/asesor/conversations/[id]/route.ts`, `scripts/test/asesor/agent.test.ts` | Turn free text into a durable EventBrief through validated tools, emit coherent streaming state, and recover provider failure without duplicate turns. |
| T4 | `src/app/asesor/page.tsx`, `src/components/asesor/ChatView.tsx`, `src/components/asesor/Composer.tsx`, `src/components/asesor/useConversation.ts`, `scripts/test/asesor/chat-ui.test.ts`, `scripts/e2e/asesor/scenarios/text.ts` | Deliver the mobile advisor text experience with notices, authoritative progress and server-backed same-device restoration. |
| T5 | `src/lib/asesor/brief.ts`, `src/app/api/asesor/briefs/[id]/route.ts`, `src/app/asesor/brief/[id]/page.tsx`, `src/components/asesor/BriefView.tsx`, `src/components/asesor/brief-print.css`, `scripts/test/asesor/brief.test.ts` | Persist customer approval of a current summary and render full and redacted vendor briefs in a printable one-page view. |
| T6 | `src/lib/asesor/admin.ts`, `src/app/api/asesor/admin/conversations/route.ts`, `src/app/api/asesor/admin/conversations/[id]/route.ts`, `src/app/asesor/admin/page.tsx`, `src/app/asesor/admin/[id]/page.tsx`, `scripts/test/asesor/admin.test.ts` | Expose a read-only admin monitor whose list and detail reflect durable customer state and reject the user role. |
| T7 | `scripts/e2e/asesor/run.ts`, `scripts/e2e/asesor/check-findings.ts`, `scripts/e2e/asesor/scenarios/m1.ts`, `docs/req-020/deployment.md`, `scripts/test/asesor/harness.test.ts` | Build the real-entry-point acceptance harness, complete M1 deployment configuration and verify the text flow against the approved production dependencies. |
| T8 | `src/lib/asesor/photos.ts`, `src/app/api/asesor/photos/route.ts`, `src/app/api/asesor/photos/[id]/route.ts`, `scripts/test/asesor/photos.test.ts`, `scripts/e2e/asesor/scenarios/photos.ts` | Accept inspiration/venue photos, preserve original bytes, collect first-look confirmation and per-photo preferences, and include them in durable briefs and monitoring. |
| T9 | `src/app/api/voz/transcribir/route.ts`, `src/lib/asesor/voice.ts`, `scripts/test/asesor/voice.test.ts`, `scripts/e2e/asesor/scenarios/voice.ts` | Authorize advisor dictation through the existing Whisper route and persist its transcript as an ordinary customer turn with text-only replies. |
| T10a | `scripts/e2e/asesor/run.ts`, `scripts/e2e/asesor/scenarios/photos.ts`, `scripts/e2e/asesor/scenarios/voice.ts`, `scripts/e2e/asesor/scenarios/m2.ts` | Make the e2e runner support --milestone M2 with the photo, voice and combined scenarios in fake-model and live modes. |
| T10 | `docs/req-020/m2-deployment.md` | Complete the approved M2 deployment using the combined photo/voice phone flow and record reproducible operational checks. |
| T11 | `src/lib/asesor/catalogue.ts`, `src/lib/asesor/catalogue-fallback.json`, `scripts/migrations-asesor/002_catalogue.sql`, `scripts/test/asesor/catalogue.test.ts` | Serve a validated daily Happia catalogue snapshot from advisor Postgres and a seeded last-good fallback without modifying the shared Happia package. |
| T12 | `src/lib/asesor/directions.ts`, `src/lib/asesor/directions.json`, `scripts/test/asesor/directions.test.ts`, `scripts/e2e/asesor/scenarios/directions.ts` | Offer undecided customers twelve editable curated directions with photos and only verified themed catalogue items. |
| T13 | `src/lib/asesor/packages.ts`, `scripts/test/asesor/packages.test.ts`, `scripts/e2e/asesor/scenarios/packages.ts` | Propose a fitting standard Happia package before bespoke options, show a sourced COP estimate and preserve the proposal in the brief. |
| T14 | `src/lib/asesor/prompts/catalogue.ts`, `scripts/eval/asesor/run.ts`, `scripts/eval/asesor/scenarios.json`, `scripts/test/asesor/prompt.test.ts`, `scripts/e2e/asesor/scenarios/m3.ts` | Integrate the optional direction/package tool adapters and tune advisor prompts using versioned real-model conversations and deterministic invariants. |
| T14a | `docs/req-020/integration-results.json` | Run the established full advisor entry-point flow and regression checks, reporting actual failures without changing code or judging product acceptance. |
| T15 | `docs/req-020/T15.md`, `docs/req-020/T15.findings.json` | Review R1 through R14 against the delivered production behavior and record a task-linked findings ledger and evidence report without changing the implementation. |

## Tasks

### M1 — Text conversation to an approved brief, admin watching (Halloween, Thu 29 Oct)
Acceptance: A real authenticated text conversation supports correction, same-device restore and explicit approval; the persisted brief appears in the read-only admin monitor within five seconds. Invalid sessions and user access to admin are rejected; provider failure preserves the conversation and protected happie regression checks pass.

- [ ] T1 — Worktree from origin/main; Supabase pool (`src/lib/asesor/db.ts`), migrations folder `scripts/migrations-asesor/` + runner (`npm run asesor:migrate`), schema: accounts, conversations, messages, attachments, briefs; `npm run asesor:test` script wired into the gate · repo: pictures · verify: `ASESOR_TEST_DATABASE_URL=postgresql://rag:rag_local_only_change_me@127.0.0.1:5432/rag npx tsx --conditions=react-server --test scripts/integration/asesor-db.test.ts`; `npm run asesor:test` · files: package.json, scripts/test/gate.mjs, .env.example, src/lib/asesor/db.ts, src/lib/asesor/repository.ts, scripts/migrate-asesor.ts, scripts/migrations-asesor/001_initial.sql, scripts/test/asesor/run.ts, scripts/test/asesor/db.test.ts, scripts/integration/asesor-db.test.ts · resources: advisor-persistence-contract, advisor-command-contract · covers: R6 · kind: implement

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 240 min (provisional). Advisor database isolation, transaction-pooler compatibility and replay constraints cross the runner and repository; high rather than medium, but this is not an exceptional replacement of existing persistence.

  Acceptance: Applying advisor migrations twice to a disposable Postgres target preserves records and creates accounts, conversations, messages, bytea attachments and versioned briefs without changing the Neon migration ledger. Repository round trips preserve message IDs, order, photo bytes and brief state; duplicate conversation/message IDs do not insert twice, and database failure is surfaced without a success acknowledgement. The advisor pool reads only SUPABASE_DB_URL with TLS; migrations and tests have explicit test targets; asesor:test runs deterministic suites and is required by gate. At the T1 gate, origin/main is an ancestor of the implementation worktree HEAD.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/db.test.ts` [functional, created by T1]; `npx tsx --conditions=react-server --test scripts/integration/asesor-db.test.ts` [integration, created by T1]; `git merge-base --is-ancestor origin/main HEAD` [static].

- [ ] T2 — Own auth: scrypt-hashed accounts `user`/`admin`, seed script with generated passwords, `/asesor/login`, signed session cookie, proxy matcher exclusion for `/asesor` + `/api/asesor`, role guard helpers · repo: pictures · after: T1 · verify: `npm run asesor:test` · files: src/lib/asesor/auth.ts, src/app/asesor/login/page.tsx, src/app/api/asesor/login/route.ts, src/proxy.ts, scripts/seed-asesor.ts, scripts/test/asesor/auth.test.ts, scripts/test/test-proxy-matcher.ts · resources: advisor-session-contract, advisor-persistence-contract · covers: R1, R12 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 180 min (provisional). Advisor cookies, role guards and proxy exclusions cross independent trust boundaries; high instead of medium because bypassing the outer proxy must never bypass handler authorization.

  Acceptance: Only user/admin seed credentials succeed; hashes are scrypt-based, generated passwords are delivered locally, signed cookies are HttpOnly/Secure in production, and missing secrets or tampered cookies fail closed. Uncredentialed advisor pages redirect to advisor login, APIs reject access, user gets 403 on admin resources, and admin can access both customer and monitor flows. Proxy exclusions cover exact advisor route boundaries without exempting similarly prefixed unrelated routes; the voice endpoint can reach its handler without APP_PASSWORD while that handler continues to require its existing authentication until T9 adds advisor support.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/auth.test.ts` [functional, created by T2].

- [ ] T3 — Advisor agent: `EventBrief` schema (R3 fields, event kinds incl. corporate/school), system prompt, tools (save fields, propose summary, approve), progress calculator, streaming route `/api/asesor/conversar` persisting every turn, retry on provider failure; deterministic tests with a fake `ChatPort` · repo: pictures · after: T2 · verify: `npm run asesor:test` · files: src/lib/asesor/contracts.ts, src/lib/asesor/agent.ts, src/lib/asesor/tools.ts, src/lib/asesor/progress.ts, src/lib/asesor/prompts/base.ts, src/app/api/asesor/conversar/route.ts, src/app/api/asesor/conversations/route.ts, src/app/api/asesor/conversations/[id]/route.ts, scripts/test/asesor/agent.test.ts · resources: advisor-session-contract, advisor-persistence-contract, event-brief-contract, advisor-stream-contract · covers: R3, R4, R6, R13 · kind: implement

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 360 min (provisional). Advisor streaming, validated tool effects, summary revisions, retry idempotency and database replay interact; high is necessary, while bounded domain states and an existing ChatPort avoid extreme uncertainty.

  Acceptance: EventBrief validates birthdays, corporate and school events and all R3 fields; required-field progress is computed by the server, never inferred from model wording. Saving fields invalidates a stale summary/approval; propose requires complete required fields and approve requires explicit customer confirmation of the current summary version. Refused contact/address leaves approval unavailable with a Spanish explanation. Authenticated turns persist stable message IDs before acknowledgement; retries replay existing IDs instead of inserting duplicates, two-tab edits follow last committed field write, and provider timeout/disconnect preserves committed state and offers retry without silently replaying partial effects. SSE text/tool events terminate with exactly one final or error event carrying authoritative conversation state; malformed tool inputs and injection cannot grant permissions or disclose other conversations; logs/telemetry omit personal data and transcript bodies.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/agent.test.ts` [functional, created by T3].

- [ ] T4 — Chat UI `/asesor`: guiado components, privacy + test-version notices, progress bar, resume by conversation id in localStorage (transcript reloaded from the server) · repo: pictures · after: T3 · verify: `npm run asesor:test`; `npx tsc --noEmit` · files: src/app/asesor/page.tsx, src/components/asesor/ChatView.tsx, src/components/asesor/Composer.tsx, src/components/asesor/useConversation.ts, scripts/test/asesor/chat-ui.test.ts, scripts/e2e/asesor/scenarios/text.ts · resources: advisor-stream-contract, advisor-media-ui-contract · covers: R2, R4, R5 · kind: implement

  Classification: complexity high; scope full_feature; risk medium; coupling high; confidence medium; estimate 240 min (provisional). Advisor streaming UI reconciles final state, reloads and localStorage with mobile input; high instead of medium because this crosses transient and durable state rather than just adapting markup.

  Acceptance: At a phone viewport the privacy and test-version notices precede the first warm Spanish question; progress comes from server state, and loading, retry and completed states remain usable with the keyboard open. Only the conversation ID is stored in localStorage; reloading restores transcript, last question, progress and current brief version from the authenticated server without duplicating turns; an invalid ID shows a recoverable state. The advisor Composer is the single UI owner for capability-gated photo/voice controls and typed direction/package cards; M1 works with unavailable media/catalogue endpoints and later producers populate the already declared contract without editing the page.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/chat-ui.test.ts` [functional, created by T4].

- [ ] T5 — Brief: summary to approve/correct, stored full brief + vendor version without name/contact/budget, printable one-page view · repo: pictures · after: T3 · verify: `npm run asesor:test` · files: src/lib/asesor/brief.ts, src/app/api/asesor/briefs/[id]/route.ts, src/app/asesor/brief/[id]/page.tsx, src/components/asesor/BriefView.tsx, src/components/asesor/brief-print.css, scripts/test/asesor/brief.test.ts · resources: event-brief-contract, advisor-brief-projection · covers: R11 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 210 min (provisional). Advisor summary versioning, approval persistence and privacy-safe projections must agree across server and print views; high instead of medium because redacting UI labels alone cannot ensure privacy.

  Acceptance: Correcting any summarized field creates a new summary version and requires fresh approval; repeated approval of the same version persists only one approved result. Full brief retains all supplied R11 fields and photo references; vendor projection omits name, contact and budget and, under the approved global privacy constraint, exact address and personal data echoed inside notes/requests. The server returns the appropriate authorized projection, and print preview fits the agreed one-page summary with photo references/thumbnails without sending hidden personal fields to the vendor client.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/brief.test.ts` [functional, created by T5].

- [ ] T6 — Admin monitor `/asesor/admin`: conversation list (status, progress, last question, 5 s refresh) and read-only detail (transcript, brief); `user` gets 403 · repo: pictures · after: T5 · verify: `npm run asesor:test` · files: src/lib/asesor/admin.ts, src/app/api/asesor/admin/conversations/route.ts, src/app/api/asesor/admin/conversations/[id]/route.ts, src/app/asesor/admin/page.tsx, src/app/asesor/admin/[id]/page.tsx, scripts/test/asesor/admin.test.ts · resources: advisor-session-contract, advisor-brief-projection · covers: R12 · kind: implement

  Classification: complexity medium; scope full_feature; risk high; coupling high; confidence medium; estimate 150 min (provisional). Advisor monitoring is read-only polling over contracts already defined by T2/T3/T5; medium rather than high because it neither mutates the agent state nor defines a new streaming or replay boundary.

  Acceptance: Admin list shows status, server progress and last advisor question and refreshes every 5 seconds; detail shows persisted transcript, attachment references and approved brief. Anonymous sessions are rejected and user sessions get 403 from both monitor pages and APIs, including direct conversation IDs; the monitor exposes no edit/takeover/approval actions. An admin polling failure shows an error and preserves the last displayed snapshot rather than fabricating fresh data.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/admin.test.ts` [functional, created by T6].

- [ ] T7 — M1 acceptance: e2e script (login → conversation → approved brief → visible to admin), one real Gemini conversation, `/happie` regression (`npm run happie:test-webhook`), env vars on Vercel + VPS, deploy · repo: pictures · after: T4, T6 · verify: `npm run gate`; `npm run happie:test-webhook` · files: scripts/e2e/asesor/run.ts, scripts/e2e/asesor/check-findings.ts, scripts/e2e/asesor/scenarios/m1.ts, docs/req-020/deployment.md, scripts/test/asesor/harness.test.ts · resources: advisor-command-contract, pictures-production-deployment · covers: R1, R2, R3, R4, R5, R6, R11, R12, R13, R14 · kind: implement

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 300 min (provisional). Advisor browser harness construction, production startup, provider checks and deployment cross process and environment boundaries; high instead of medium because the current smoke harness does not start the app or cover advisor auth.

  Acceptance: The new CLI --start builds/starts the shipped Next application with npm run start, waits for readiness, drives browser/HTTP login to persisted approval and admin visibility against disposable Postgres, and closes child processes on success or failure. The M1 scenario checks same-device reload, corrected summary, admin denial, provider failure and one real Gemini text conversation; required live dependencies missing or any required skipped step cause nonzero exit, never a green report. Vercel/VPS configuration documents required variable names and same-revision deployment/rollback; credentials are supplied outside the repo, and M1 is deployed only after the existing gate, build, lint, types and webhook regression checks pass. The findings checker rejects malformed audit-findings/1, absent task references and open critical/high findings; it does not treat report existence as audit success. It also validates revision/command/outcome/task linkage in integration-results and rejects audit edits outside the report/ledger.

  Focused verification: `npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M1` [integration, created by T7]; `npm run lint`; `npm run build --workspaces --if-present`; `npx tsc --noEmit`; `npm run build` [static]; `npx tsx --conditions=react-server --test scripts/test/asesor/harness.test.ts` [functional, created by T7].


### M2 — Photos and voice notes (~Fri 6 Nov)
Acceptance: A phone customer sends inspiration/venue photos and voice notes; first-look confirmation/preferences and transcript text survive reload and appear in approved brief/admin. Invalid media and voice permission/service failure show recoverable errors; the tested revision is deployed.

- [ ] T8 — Photo upload from camera/gallery (`capture` + gallery), `preparar-foto`, bytea storage, inline to the model for first look, confirm + likes/dislikes per photo, venue photo flag, photos in brief/admin · repo: pictures · after: T7 · verify: `npm run asesor:test` · files: src/lib/asesor/photos.ts, src/app/api/asesor/photos/route.ts, src/app/api/asesor/photos/[id]/route.ts, scripts/test/asesor/photos.test.ts, scripts/e2e/asesor/scenarios/photos.ts · resources: advisor-photo-capability · covers: R7, R6, R11, R12 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 300 min (provisional). Advisor photo bytes, derivative preparation, multimodal history and per-attachment confirmation must stay consistent after replay; high instead of medium because storage and interpretation have different fidelity contracts.

  Acceptance: Camera and gallery inputs accept supported photos up to the approved 6 MB boundary, reject invalid/corrupt/oversize inputs with a Spanish error, and enforce authentication on uploads and byte reads. Original received bytes round-trip unchanged through Postgres bytea and the brief; prepararFotoReferencia is used only for the model/display derivative, so JPEG normalization cannot replace the stored original. The agent receives inline photo content for first look, asks for confirmation and records likes/dislikes separately by attachment ID, including venue vs inspiration; resumed transcripts, brief and admin consume the same metadata.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/photos.test.ts` [functional, created by T8].

- [ ] T9 — Voice notes: `BotonVoz`/`useDictado` + `/api/voz/transcribir` for advisor sessions (VOZ_* env from the `voz-decoracion` container), transcript stored as the customer's text · repo: pictures · after: T7 · verify: `npm run asesor:test` · files: src/app/api/voz/transcribir/route.ts, src/lib/asesor/voice.ts, scripts/test/asesor/voice.test.ts, scripts/e2e/asesor/scenarios/voice.ts · resources: advisor-session-contract, voice-transcription-contract · covers: R8, R6, R13 · kind: implement
- [ ] T10a — Extend the e2e runner with the M2 photo and voice scenarios · repo: pictures · after: T8, T9 · verify: `npm run asesor:test` · files: scripts/e2e/asesor/run.ts, scripts/e2e/asesor/scenarios/photos.ts, scripts/e2e/asesor/scenarios/voice.ts, scripts/e2e/asesor/scenarios/m2.ts · covers: R7, R8, R11 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 180 min (provisional). Advisor voice crosses an existing synchronous auth dependency, the outer proxy and remote Whisper behavior; high instead of medium because a simple component reuse does not establish dual-session authorization.

  Acceptance: The existing voice route accepts a valid advisor session or its existing Pictures authentication, rejects anonymous/cross-origin requests, and keeps existing Pictures clients working after the proxy exclusion prepared by T2. BotonVoz/useDictado captures at most 60 seconds, existing 2 MB MIME/type limits remain enforced, denial/empty audio/disabled service/timeout produce recoverable Spanish errors, and no audio or transcript is logged. Whisper transcript becomes one idempotent persisted customer text message; the advisor response is text only, and unavailable VOZ_* configuration is reported explicitly rather than pretending transcription succeeded.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/voice.test.ts` [functional, created by T9].

- [ ] T10 — M2 acceptance on a phone viewport (photo + voice conversation to brief), deploy · repo: pictures · after: T8, T9, T10a · verify: `npm run gate` · files: docs/req-020/m2-deployment.md · resources: pictures-production-deployment, advisor-media-ui-contract · covers: R7, R8, R11 · kind: implement

  Classification: complexity high; scope small_change; risk high; coupling high; confidence medium; estimate 150 min (provisional). Advisor media deployment combines browser permissions, image transport and an external voice service; high instead of medium because local unit success cannot establish the phone-to-VPS flow.

  Acceptance: On a phone viewport a camera/gallery photo and a real voice note survive reload, feed a corrected/approved brief and appear in admin; the photo is retained as received and the stored voice message is the transcript. The M2 deployment uses the tested revision and configured VOZ_* variables; phone microphone/camera permissions and a failure/retry path are recorded with redacted evidence. Operational changes and verification are recorded; source defects are returned to T8/T9 or their named prerequisite rather than silently repaired in this deployment task.

  Focused verification: `npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M2` [integration, created by T7]; `npm run lint`; `npm run build --workspaces --if-present`; `npx tsc --noEmit`; `npm run build` [static].


### M3 — Directions, themed items and standard packages (~Thu 19 Nov)
Acceptance: Undecided customers receive twelve editable photo directions and verified themed items; fitting standard packages precede bespoke options with sourced COP estimate and notice. Daily cache/fallback and no-match behavior pass deterministic checks; versioned real-model scenarios do not violate approval, privacy or catalogue invariants.

- [ ] T11 — Happia catalogue daily cache in Postgres (refresh when older than 24 h) + fallback list seeded from the last good read; read-only reuse of `HappiaClient` · repo: pictures · after: T7 · verify: `npm run asesor:test` · files: src/lib/asesor/catalogue.ts, src/lib/asesor/catalogue-fallback.json, scripts/migrations-asesor/002_catalogue.sql, scripts/test/asesor/catalogue.test.ts · resources: advisor-persistence-contract, advisor-catalogue-contract · covers: R10 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 210 min (provisional). Advisor daily refresh needs persistent freshness, concurrent-reader control and last-good failure semantics; high instead of medium because in-memory TTL alone cannot enforce the once-daily rule across instances.

  Acceptance: Read-only HappiaClient reuse populates an advisor-owned Postgres snapshot; at 24-hour freshness boundary a cross-instance lock/refresh marker permits at most one API refresh attempt per day, with no provider request inside a long database transaction. Concurrent cold/stale reads do not stampede; an API timeout/invalid payload keeps the last validated snapshot or seeded last-good JSON fallback, and an absent valid source returns an explicit unavailable result without invented prices/items. Fallback values retain catalogue IDs, supplied item/provider metadata and price provenance; snapshot age/source are recorded without personal customer data and Neon tables are untouched.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/catalogue.test.ts` [functional, created by T11].

- [ ] T12 — Directions: editable config of 12 decorations from `biblioteca-sempertex/decoraciones.json` (with photos) + themed items, tool to show them to undecided customers · repo: pictures · after: T11 · verify: `npm run asesor:test` · files: src/lib/asesor/directions.ts, src/lib/asesor/directions.json, scripts/test/asesor/directions.test.ts, scripts/e2e/asesor/scenarios/directions.ts · resources: advisor-direction-contract · covers: R9 · kind: implement

  Classification: complexity medium; scope full_feature; risk medium; coupling high; confidence medium; estimate 150 min (provisional). Advisor directions adapt inspected catalogue records into a bounded curated list; medium rather than high because T11 owns freshness/failure state and T3/T4 own agent/UI orchestration.

  Acceptance: Editable config references exactly twelve distinct existing decoration IDs with photo URLs; invalid/missing references fail validation, and illustrative/example provenance is retained rather than presented as a real themed photograph. An undecided conversation displays direction photos and themed items backed by the validated Happia snapshot; unavailable themed-item data is reported rather than invented. Selecting an offered direction preserves existing event fields and records its reference in the conversation; unrelated or prompt-injected catalogue text cannot create tools or permissions.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/directions.test.ts` [functional, created by T12].

- [ ] T13 — Standard package/service first: tool matching event/theme/city/guests, card with estimated price + notice, recorded in the brief · repo: pictures · after: T11 · verify: `npm run asesor:test` · files: src/lib/asesor/packages.ts, scripts/test/asesor/packages.test.ts, scripts/e2e/asesor/scenarios/packages.ts · resources: advisor-catalogue-contract, advisor-package-contract · covers: R10, R11 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 240 min (provisional). Advisor package eligibility, model recommendations, price provenance and persisted brief cards must agree; high instead of medium because guest counts and missing city/service metadata cannot be treated as guaranteed availability.

  Acceptance: Candidates come only from active validated Happia packages/items; event/theme/city restrictions use supplied metadata, guest count orders by proximity to base_guests rather than inventing a hard capacity, and unknown coverage is disclosed instead of guaranteed. A fitting standard candidate is offered before bespoke directions/services; no fit returns an explicit no-match result, and the model cannot create catalogue IDs, prices or unsupported vendor capabilities. The card and persisted brief carry the same package ID, source/freshness and estimated subtotal COP before VAT/commission with the existing notice; missing price data produces unavailable pricing rather than a fabricated estimate.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/packages.test.ts` [functional, created by T13].

- [ ] T14 — Scripted conversation set (birthday, corporate, school, undecided, photo-led, refusals, prompt injection) run against the real model; fix prompt gaps · repo: pictures · after: T12, T13, T10 · verify: `npm run asesor:test` · files: src/lib/asesor/prompts/catalogue.ts, scripts/eval/asesor/run.ts, scripts/eval/asesor/scenarios.json, scripts/test/asesor/prompt.test.ts, scripts/e2e/asesor/scenarios/m3.ts · resources: advisor-direction-contract, advisor-package-contract · covers: R3, R7, R9, R10, R13 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 240 min (provisional). Advisor real-model evaluations must connect direction/package tools, image context and refusal/approval rules without hiding nondeterminism; high rather than medium because fixtures alone cannot establish model behavior.

  Acceptance: Versioned birthday, corporate, school, undecided, photo-led, contact/address refusal, off-topic and prompt-injection scenarios run against the already selected real model and record outcomes separately from deterministic fake-ChatPort tests. Scenario assertions check completeness, approval gating, photo confirmation and only sourced direction/package IDs and prices; they do not assert exact free-form model wording or treat a single run as a quality metric. Prompt fixes stay within advisor-owned prompt fragments; auth, persistence or pricing defects are returned to their owning tasks, and scenarios never reveal other conversation data or log real customer PII.

  Focused verification: `npx tsx --conditions=react-server --test scripts/test/asesor/prompt.test.ts` [functional, created by T14]; `npx tsx --conditions=react-server scripts/eval/asesor/run.ts --live` [product, created by T14].


### M4 — Acceptance and close (before the 23 Nov rehearsal)
Acceptance: The full shipped-entry-point flow and protected regressions run with actual outcomes recorded. Read-only final production review traces all R1-R14 and its valid findings ledger contains no open critical/high finding.

- [ ] T14a — Run full advisor entry-point integration and protected happie regression; record outcomes without fixes · repo: pictures · after: T10, T14 · verify: `ASESOR_TEST_DATABASE_URL=postgresql://rag:rag_local_only_change_me@127.0.0.1:5432/rag npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --fake-model --milestone all` · files: docs/req-020/integration-results.json · resources: advisor-command-contract, pictures-production-deployment · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14 · kind: test

  Classification: complexity low; scope full_feature; risk medium; coupling high; confidence medium; estimate 120 min (provisional). Advisor execution runs fixed commands produced and locally verified by T7/T8/T9/T14; low rather than medium because it authors no harness, changes no configuration and makes no repair or acceptance decision. Environment failures are reported to owners.

  Acceptance: The T7 runner starts the shipped production Next entry point and drives a real login, text/photo/voice conversation, reload, correction, approval and admin read through Postgres, configured AI and real Whisper; it fails on missing live dependencies or required skipped assertions. Gate, package builds, lint, application types, production build and unchanged webhook regressions run with recorded exit status; source comparison checks the protected happie paths/contracts against the implementation base. The redacted integration result identifies revision, commands, actual outcomes and failed owning task; this task creates no tests/configuration, applies no fixes and makes no product acceptance decision.

  Focused verification: `npm run gate`; `npm run happie:test-webhook`; `npm run lint`; `npm run build --workspaces --if-present`; `npx tsc --noEmit`; `npm run build` [regression]; `npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --live --deployed --milestone all` [integration, created by T7]; `npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --check-results docs/req-020/integration-results.json` [functional, created by T7].

- [ ] T15 — Full acceptance on production: every R1–R14 check, `/happie` unchanged, report with evidence, bitácora updated · repo: pictures · after: T14a · verify: `npm run gate`; `npm run happie:test-webhook` · files: docs/req-020/T15.md, docs/req-020/T15.findings.json · resources: advisor-command-contract, pictures-production-deployment · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14 · kind: audit
- [ ] T15b — Cross-check audit of T15: Full acceptance on production: every R1–R14 check, `/happie` unchanged, report with evidence, bitácora updated · repo: pictures · after: T15 · verify: `npm run gate`; `npm run happie:test-webhook` · files: docs/req-020/T15-crosscheck.md, docs/req-020/T15-crosscheck.findings.json · resources: advisor-command-contract, pictures-production-deployment · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14 · kind: audit

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 150 min (provisional). Advisor acceptance must correlate production behavior, permission boundaries, model outputs and protected contracts; high instead of medium because green scripts cannot establish the complete user/privacy acceptance.

  Acceptance: The read-only production review traces each R1-R14 criterion to actual integration evidence and phone behavior, including privacy/redaction, required-field refusal, provider retry and unchanged happie behavior; unexecuted checks remain unaccepted. Exactly one audit-findings/1 ledger records findings with severity, status, summary and affected plan task IDs; malformed data or an open critical/high finding rejects acceptance and returns the named producer tasks for rework. The audit changes only its report and ledger; the report includes redacted closure/bitacora notes and does not approve, edit, deploy or repair any product artifact.

  Focused verification: `npx tsx --conditions=react-server scripts/e2e/asesor/check-findings.ts docs/req-020/T15.findings.json` [functional, created by T7]; `npx tsx --conditions=react-server scripts/e2e/asesor/check-findings.ts docs/req-020/T15.findings.json --check-audit-diff --integration-results docs/req-020/integration-results.json` [static, created by T7].

T3 owns the authoritative summary/approval state machine and version checks. T5 consumes that approved revision to store/render projections; it imports those rules rather than reimplementing approval precedence. T1 records the origin/main implementation base before product changes; T7 retains it for protected-source comparison.

## Interfaces
PLAN.json contains the precise inputs, outputs, invariants and integration criteria. These are contracts, not additional tasks.

| Contract | Producer | Consumers | Integration acceptance |
|---|---|---|---|
| IF-1 Advisor persistence | T1 | T2, T3, T11 | Repeated migration and duplicate message tests fail on loss or duplication. |
| IF-2 Advisor session and voice compatibility | T2 | T3, T9 | Customer and admin succeed, user monitor reads return 403, anonymous/tampered sessions fail, and old voice callers retain behavior. |
| IF-3 EventBrief and stream | T3 | T4, T5, T8, T13 | Reload, correction, timeout and repeated message IDs preserve the same committed state and approval version. |
| IF-4 Vendor brief projection | T5 | T6, T8, T13 | Server JSON and print view are checked with synthetic PII in structured and free-text fields. |
| IF-5 Media capability and UI slots | T4 | T8, T9 | T10 and T14a drive combined camera/gallery, first look, voice, reload and approval on a phone viewport. |
| IF-6 Daily catalogue snapshot | T11 | T12, T13 | Clock-boundary, concurrent refresh, API outage and missing-data tests produce honest cards and brief metadata. |
| IF-7 Directions and model integration | T12 | T14 | Undecided real-model scenario shows known directions/items without inventing IDs. |
| IF-8 Package suggestions and model integration | T13 | T14 | M3 model scenario and T14a full flow produce identical package provenance in card and approved brief. |
| IF-9 Runnable acceptance and audit gate | T7 | T10, T14a, T15 | T14a starts the app and drives real persistence/provider/voice; T15 rejects open critical/high task-linked findings. |

## Verification
All commands execute from the future pictures implementation checkout. `npm run gate`, `npm run lint`, `npm run build --workspaces --if-present`, `npx tsc --noEmit`, `npm run build` and `npm run happie:test-webhook` exist in the inspected package.json. The current gate does not contain advisor checks; T1 adds them. `asesor:migrate`, `asesor:test`, every `scripts/test/asesor/*` check, the new advisor e2e/eval runners and the findings checker are planned implementation work, explicitly marked `created_by` in PLAN.json. Their passing is not claimed here.

T1's default test runner discovers only task-owned deterministic suites under scripts/test/asesor; the separate scripts/integration/asesor-db.test.ts creates fixtures, invokes the migration runner twice with an intervening record, and asserts real repository/bytea/idempotency behavior against the explicit disposable target. It is excluded from the fast gate. T1's test runner discovers task-owned deterministic suites; each producer runs its focused failing assertions as part of its own implementation cycle. Database checks require an explicitly configured disposable advisor Postgres target and synthetic records. Required fast checks use fake ChatPort/controlled fixtures, not paid providers or production credentials. Full integration and real-model checks are separate explicit live commands.

The T7 runner also provides `--check-results <path>` (nonzero for missing/invalid revision, command, outcome or failed-task linkage, or required failure/skip) and its findings checker provides `--check-audit-diff --integration-results <path>` (nonzero for edits outside the report/ledger or invalid referenced integration evidence); audit footprint is compared against the integrated revision recorded by T14a, not the original implementation base. Harness tests exercise failed startup, required skips, child cleanup, malformed ledgers and open critical/high findings. The T7 runner owns portable Playwright launch/readiness/cleanup, captures the original implementation-base ref, loads task-owned scenario modules, and records revision/exit outcomes with synthetic data only. `--start` builds/launches the shipped Next production server with `npm run start`, connects to the configured disposable Postgres and selected real model, and drives authenticated browser/HTTP flows rather than importing handlers. M2/all additionally connects to the real configured Whisper VPS service; that external service and managed database are dependencies, not invented local entry points. `--deployed` checks the approved deployment target and compares protected `/happie`, `src/lib/happie/*`, webhook and happie.v1/v2 sources/contracts with the captured base. Missing dependencies, permission failures and required skipped steps are failures. Existing smoke tooling's permissive SKIPPED behavior is not copied.

T14a runs the completed harness and established checks only: no test writing, source/config repair or acceptance verdict. T15 performs product review and writes only `docs/req-020/T15.md` plus `docs/req-020/T15.findings.json`. The report includes the closure/bitacora notes for later recording; this read-only audit does not modify runtime or separate bitacora state. Ledger format: `{"schema":"audit-findings/1","findings":[{"id":"F1","severity":"high","status":"open","summary":"...","tasks":["T3"]}]}`. Every finding names the tasks whose result is wrong; open critical/high findings reject acceptance and return those tasks for rework. Fixed findings need evidence; accepted risk needs owner attribution/reason. The report's existence never establishes acceptance.

## Evidence and estimation limits
Observed on 2026-10-20: SPEC.md, the original PLAN.md/PLAN.json, project workspace mappings, both available repository AGENTS.md files, package scripts, existing pg pool/migration runner, proxy/request guards, ChatPort/agent loop, guided API/contract/composer, image preparation, voice route/config/limits/handler, shared approval contracts, printable view, Happia client/public exports/guest ordering/recommendation rules, decoration data and browser smoke configuration/executor/webhook tests were opened. The t12 assistant entry point was also inspected; t12 and pictures have identical AGENTS.md. Both checkouts have unrelated changes and are read-only evidence sources. New work still starts from origin/main as SPEC A2 says; these local branches are not a claim about the future implementation base.

The registered audit, demo-decoracion and t7 checkouts are absent locally; no evidence is attributed to them. All task repositories resolve to the available pictures role. No production service, database, secret or deployment was changed or probed by this planning session.

`plan-json history --kind implement`, `--kind test` and `--kind audit` were run for pictures: status unknown; duration unit seconds, source_quality unknown, median/range/sample count unavailable; retry, quality and consumption metrics also unknown. There are no verified comparable samples. Minute estimates are explicit provisional engineering breakdowns including local verification; they are neither calibrated measurements nor deadlines, and exclude waiting for credentials/content/provisioning. Every task keeps medium estimate confidence with task-specific limitations in PLAN.json. Execution history sample counts are unavailable, not zero.

Observed integration risks and retained assumptions:
- Voice currently authenticates only Pictures APP_PASSWORD requests, and the proxy intercepts the route. T2 owns exact proxy exclusions; T9 extends the handler to advisor sessions while preserving existing callers. Removing only the proxy is insufficient (src/proxy.ts; src/app/api/voz/transcribir/route.ts; src/lib/auth/request.ts).
- Photo preparation accepts 20 MB raw files and converts to JPEG; the approved advisor boundary is 6 MB and photos as received. T8 preserves original bytes and uses preparation only for a derivative. No change to the shared preparer is planned (src/lib/imagen-cliente/preparar-foto.ts; SPEC Edge cases & errors).
- The public Happia client exposes listarPackages, not a services API. Item descriptions/provider/category can be null. Themed items and city/coverage/price data cannot be promised from nonexistent fields. T11-T13 consume supplied catalogue/fallback data, disclose missing coverage and never invent prices; William/Diana data remains the existing external dependency (SPEC Timeline & dependencies; packages/happie-package-ia/src/cliente.ts).
- The existing guest sorter ranks by distance to base_guests; it explicitly rejects treating this field as a hard capacity. T13 preserves that rule, existing restrictions and the approved subtotal COP notice (packages/happie-package-ia/src/filtros.ts; SPEC A6).
- Library data includes example records with reused photos/provenance warnings. T12 retains this provenance in the twelve-entry curation instead of presenting illustrative imagery as exact inventory (src/lib/biblioteca-sempertex/decoraciones.json).
- SPEC R11 requires omission of name/contact/budget; the already approved PLAN global constraint also excludes personal data including exact address. T5 applies that stricter existing constraint to vendor output and copied free text; this clarification adds no new product scope.
- Optional media/tool integration must be exposed through T3/T4 extension contracts and T14's catalogue prompt fragments without copying domain rules or sharing file ownership. Their exact internal factoring stays local to the implementer, but fresh task checks must pass with absent later capabilities as well as once those capabilities are present.

## Review focus
1. Tampered/absent sessions and prefix lookalikes — T2 auth/proxy tests; T9 dual-session voice regression.
2. Partial streams, repeated IDs, two tabs and reload after a correction — T3 agent state tests and T4 browser text scenario.
3. Refused required fields, stale approval and PII echoed in notes/requests — T3 approval gating and T5 projection fixtures.
4. Corrupt/oversize photos, original-vs-derived bytes, denied microphone and Whisper timeout — T8 photo and T9 voice suites/scenarios.
5. Simultaneous stale catalogue reads, API outage/no valid fallback, unknown city/price and illustrative photos — T11 clock/concurrency fixtures, T12 source validation and T13 no-match/provenance tests.

## Semantic self-review
This is same-context adversarial self-review, not independent approval. Demonstrated defects in the skeleton (missing classification, milestone acceptance and collapsed requirement ranges) are corrected. The full entry-point test is explicit before final audit, which owns exactly one findings ledger. All fourteen requirements have individual covers IDs and an observable final review. Missing auth dependency is corrected transitively: T3 follows T2; T4/T5 follow T3; T6 follows T5; T7 joins customer and monitor. T12 follows T11 because verified themed items require catalogue data. M2 and M3 join at T14a before T15. No provider/account/model/effort or concurrency assignment is introduced.

Responsibility check: T7 creates the missing harness and deployment material, T10 performs operational deployment work, and T14 authors fixtures/prompt fixes, so all are implement. T14a only executes established checks and remains low complexity: fixed commands, no implementation or acceptance decisions; its full_feature scope describes coverage, not reasoning demand. T15 only reviews and records findings, with no repair authority. Calibration check: streaming/replay UI (T4), durable agent state (T3), dual-auth voice (T9), photo fidelity (T8), cross-instance cache (T11) and missing process harness (T7) retain high complexity. Read-only monitor (T6) and bounded curated adapter (T12) retain medium because their mutation/state boundaries are produced upstream. Live service/content availability remains a plausible risk, not fabricated evidence or an accepted test.

Publication notes: `created_by` diagnostics are intentional because advisor checks do not yet exist. T7 deployment inspection, T10 device/deployment review and the T15 product verdict retain manual verification and therefore NEEDS_REVIEW for those criteria; they are not an automatic PASS. The single final audit is retained from the approved scope; a second independent audit is not silently added to classification.

Deterministic validation: the project plan-json check was run after enrichment and returned exit 0, no errors, and `OK: PLAN.json is publishable`. Planned-verification and manual-acceptance warnings are intentional and are reported in the final classification result. Whitespace validation also passed. These checks validate the planning contract, not application behavior.

## Rulings
<!-- Judgment calls made during execution without asking. -->
- Run start: first T1 attempt was based on the old local branch (5f910498, feat/req-014) instead of origin/main —
  cancelled; created worktree `~/dev/pictures-wt/asesor` (branch `feat/req-020-asesor-happia` at origin/main 54d176a3,
  `npm ci` + workspace build, `.env.local` copied) and pointed workspace role `pictures` there; T1 retried on 54d176a3
  — cost if wrong: low (point the role back to `~/dev/pictures` after REQ-020).
- T1 blocked after 3 verify failures caused only by sandbox-incompatible checks (`git merge-base` with no git
  metadata; `asesor:migrate` needing SUPABASE_DB_URL; DB integration test skipping without a target). Code checks pass
  (asesor:test 6/6, db.test 6/6, integration 3/3 against local Postgres). Revision 2 (pending owner approval): DB checks
  use the local disposable Postgres inline; live Gemini/Supabase/deploy checks become coordinator-run manual checks
  with offline `--fake-model` equivalents (T1, T7, T10, T14, T14a). No scope change.

## Progress log
- 2026-10-20 Plan drafted after rounds 1–2; Supabase pooler connection verified (prior planning record, not rerun in classification).
- 2026-10-20 Contract classification added against inspected local code; approved scope and existing status/revision preserved. No approval, freeze, handoff, launch or implementation performed.
- 2026-10-20 12:14 plan APPROVED (terminal)
- 2026-10-20 12:14 launched Scheduler supervisor from HQ in `/home/david/dev`

- 2026-10-22 Owner requested integration: local commit 915a75af, antagonist: 2 fixed, 0 deferred, 0 dropped; re-review SOUND. Plan r7 adds T14.2a to import the reviewed diff after accepted T14.1a and before T14a; no requirement expansion. Rebase kept16 accepted, reset3 pending, added1. Old T14a att-0089 superseded; new att-0090 running.
