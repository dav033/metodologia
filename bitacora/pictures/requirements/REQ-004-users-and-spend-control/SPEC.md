> **CANCELLED 2026-10-18 by the owner (all open requirements).** Nothing deleted: code, branches and reports are kept.
---
id: REQ-004
status: cancelled (2026-10-18, owner)
created: 2026-10-08
track: standard
---
# REQ-004 — Users and AI spend tracking (Gemini + fal.ai)

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Today the app has one shared password (`APP_PASSWORD`, SHA-256 token in a cookie) and no notion of who did what.
Paid AI calls (Gemini text/vision/embeddings, fal.ai FLUX.2 and FLUX.1 i2i) are logged as telemetry and in JSONL
audit files, with partial cost estimates (escena-ia hard-codes $0.5/$3 per M tokens; FLUX.2 records only
`unidadesFacturadas=1`; FLUX.1 records USD per MP), but nobody can see how much is spent, by whom, or on what.
The owner: "I just want to see how much is spent, have it recorded, and see it visually."

**Success looks like:** every paid call (Gemini and fal.ai, from Next, Python or batch scripts) lands in one spend
ledger with user, provider, model, feature and USD; an admin page shows spend per day/user/provider/feature/model
and matches the providers' consoles within ±10 % for a sample month.

## Users / actors / stakeholders
- **Admin** (owner and internal team): manages accounts, sees all spend.
- **Staff** (Sempertex personnel): uses the app with their own account, sees their own consumption.
- **Sistema**: batch scripts, evals, webhooks (Happie) — recorded under a system actor, not a person.

## Scope (in)
### US-1 (P1, Must) — Personal accounts
As an admin, I create accounts (email + password, role admin|staff) so each person logs in as themselves.
**Acceptance:** Given an account, when the person logs in with email + password, then every page and API knows
their user id and role; a disabled account cannot log in and its sessions die.

### US-2 (P1, Must) — Spend ledger
As the owner, I want every paid AI call recorded with who/what/how much so the spend is auditable.
**Acceptance:** Given any paid call (all entry points listed in Constraints), then one ledger row exists with
user (or `sistema`), provider, model, feature, conversation id, units (tokens / images / megapixels), USD and
whether the cost is estimated or reconciled.

### US-3 (P1, Must) — Spend dashboard
As an admin, I open «Gastos» and see visually: today / 7 days / month totals, a daily chart stacked by provider,
breakdowns by user, feature and model, the most expensive conversations, and a filterable detail table (CSV).

### US-4 (P2, Should) — My consumption
As staff, I see my own spend this month in my account menu.

### US-5 (P2, Should) — Reconciliation
As an admin, I enter the provider's real monthly total (Google AI / fal.ai invoice) and see the gap vs the ledger.

## Out of scope
- Spend caps, alerts and blocking (owner: "no caps yet") — the ledger is designed so caps can be added later.
- Self sign-up, Google login, magic links, password-reset email (admin resets passwords).
- External decorators / customers as users.
- Billing customers for usage.

## Requirements
- R1. The system shall authenticate by email + password (scrypt hash, per-user salt) and keep server-side
  sessions (random id in an httpOnly cookie, revocable, 30-day expiry).
- R2. While `AUTH_USUARIOS_ENABLED` is off, the system shall keep today's shared-password login (migration path).
- R3. When `next dev` runs without `DEV_REQUIRE_LOGIN=1`, the system shall act as a fixed local dev user (today's
  behaviour, now with an identity so dev spend is attributable and filterable).
- R4. When any paid AI call completes or fails after billing, the system shall write one ledger row; the write
  must never fail or slow the user request (async, errors only logged).
- R5. The system shall compute USD from one versioned price table per model (input, output, thinking, cached
  tokens; per image; per megapixel), store the price version used, and never hard-code prices at call sites.
- R6. Python-service calls shall carry the caller's user id and feature (signed internal header) and be recorded
  in the same ledger.
- R7. Batch scripts and evals shall record under `sistema` with their run id and declared cap.
- R8. Only admins shall see other users' spend and manage accounts.

## Edge cases & errors
- Streaming responses: record on stream end; aborted streams record tokens actually billed (if reported).
- Tool loops (escena-ia): one row per model call, grouped by conversation.
- FLUX failures after billing (timeouts with a result) → recorded; 402/403 (no balance) → not billed, logged.
- Unknown model in price table → row with `costo_usd = null` + warning, visible in the dashboard as "sin precio".
- Deleted/disabled users keep their history.

## Constraints
- Entry points to cover (explorer, 2026-10-08): `/api/chat`, `/api/escena-ia`, `/api/asistente-guiado`
  (+ amaterasu vision), `/api/generate`, `/api/guiada-imagen`, `/api/render-3d-imagen` / FLUX.1 i2i
  (`kagutsuchi/flux.ts`), RAG embeddings, Python `services/ai-api` (chat, vision, FLUX), Happie webhook,
  eval/batch scripts. Hooks: `registrarGemini` (`ia/nucleo/telemetria-llamadas.ts`), `envolverClienteGemini`
  (`registro/servidor.ts`), the FLUX `registrar()` callback.
- Persistence in Neon Postgres (Vercel SQLite in /tmp is ephemeral). Never print .env values. No customer data in
  the repo. VPS deploy by hand, with notice. TypeScript without `any`.

## Priorities & phases
MVP = US-1 + US-2 + US-3. Then US-4, US-5. Caps are a later REQ.

## Timeline & dependencies
After REQ-003 is merged; **before REQ-002's paid runs** (classification US$1, embeddings) so they are recorded.
Needs the Python service updated (VPS deploy with notice).

## Assumptions
- Admin creates accounts and sets an initial password; user can change it (no email provider needed).
- Gemini prices from the public price list for the models in use; fal.ai per image/MP from its pricing page —
  checked by the researcher agent at implementation time and dated in the table.
- History before the ledger is backfilled from Postgres telemetry where tokens exist (user = "anterior").

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered |
| Edge cases | Covered |
| Acceptance criteria | Covered |
| Constraints | Covered |
| Priorities & phases | Covered |
| Timeline | Covered |

## Clarifications
### Round 1 — 2026-10-08
- Q: Who gets accounts? → A: internal team (admins) + Sempertex staff.
- Q: Login method? → A: email + password.
- Q: What happens at the cap? → A: no caps; "I just want to see how much is spent, recorded, and shown visually".
- Q: How are caps set? → A: "no caps yet".
