---
req: REQ-027
status: launched
created: 2026-10-19
---
# Plan — REQ-027 — Remote flow control: Vercel frontend, AdvIn API, local or VPS execution

<!-- bitacora:status:begin -->
> Bloque generado, no editar a mano. Plan: launched · ejecución: running · hitos 1/6 · tareas 25/37 · generado: 2026-10-20T07:28:23-05:00

**M1 — Contracts** · dificultad extrema · 2/2

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T2 | Research where a per-task route pin enters M2 routing and the executor | media | completada | sonnet | claude-work | 3 |
| T3 | Remote API contract, command and event schemas, and the architecture note | extrema | completada | gpt-6-luna | codex-luis | 6 |

**M2 — Laptop: remote API, ledger and feed** · dificultad alta · 8/10

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T4 | Remote API skeleton behind the gateway key, with health | media | completada | gpt-6-luna | codex-2 | 3 |
| T4a | Snapshot endpoint over the shared live caches | media | completada | gpt-6-luna | codex-luis | 2 |
| T5 | Command ledger store: idempotency keys, preconditions and audit rows | alta | completada | sonnet | claude-work | 4 |
| T5a | Ledger dispatch for run moves and decision answers | media | completada | gpt-6-luna | codex-luis | 4 |
| T5b | Ledger dispatch for plans and rounds with the confirmation challenge | media | completada | gpt-6-luna | codex-luis | 4 |
| T6 | Event feed with stable ids and a cursor, including decision requests | alta | en curso | gpt-6-luna | codex-luis | 10 |
| T7 | Failure review read model per attempt | media | completada | gpt-6-luna | codex-luis | 3 |
| T8 | Retry pinned to a route, model or account | alta | completada | gpt-6-luna | codex-1 | 3 |
| T8a | Brief or criteria edit as an owner-approved plan revision | alta | pendiente | sonnet | claude-work | 3 |
| T9 | One owner of port 8765 and reloads that keep the listening socket | media | completada | gpt-6-luna | codex-2 | 3 |

**M3 — Gateway (tested against a fake laptop)** · dificultad alta · 7/8

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T10 | Gateway skeleton: config, upstream client and liveness state | media | completada | gpt-6-luna | codex-1 | 7 |
| T11 | GitHub OAuth for dav033 and server-side sessions | media | completada | gpt-6-luna | codex-luis | 4 |
| T11a | CSRF header, Origin check, rate limits and request log | baja | completada | gpt-6-luna | codex-luis | 4 |
| T12 | Snapshot cache and SSE fan-out with Last-Event-ID | alta | completada | gpt-6-luna | codex-2 | 6 |
| T13 | Command relay with challenge, LAPTOP_OFFLINE and UNKNOWN_OUTCOME | media | completada | gpt-6-luna | codex-2 | 3 |
| T14 | Deterministic notification rules with dedupe keys | alta | pendiente | sonnet | claude-work | 3 |
| T14a | Telegram delivery with retries, backoff and history | media | completada | sonnet | claude-work | 3 |
| T14b | Telegram bot: long polling, chat allowlist, safe buttons and /estado | media | completada | sonnet | claude-work | 3 |

**M4 — Mobile web (tested against a mock gateway)** · dificultad media · 6/7

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T15 | Web scaffold: Next.js, theme tokens, local fonts, PWA manifest, rewrites, mock gateway | media | completada | gpt-6-luna | codex-2 | 13 |
| T15a | Login screen and runs list | baja | completada | gpt-6-luna | codex-luis | 3 |
| T15b | Run view: activity strip, tasks and feed on flow-core.js | media | completada | gpt-6-luna | codex-1 | 5 |
| T15c | Failure review screen | baja | completada | gpt-6-luna | codex-1 | 3 |
| T15d | Control sheet with typed confirmations and command history | media | completada | gpt-6-luna | codex-1 | 3 |
| T15e | Plans, question rounds and decision requests screens | media | completada | sonnet | claude-personal | 4 |
| T15f | Recovery forms and live quotas | media | pendiente | sonnet | claude-work | 3 |

**M5 — Go-live kit and audit** · dificultad alta · 2/5

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T16 | Go-live kit: systemd unit, Caddy block, env example, deploy and rollback scripts, runbook | media | completada | sonnet | claude-work | 3 |
| T17 | Offline end-to-end: real laptop API, gateway and built web wired locally on loopback | alta | pendiente | sonnet | claude-work | 3 |
| T18 | Independent security and spec audit by another provider | alta | completada | sonnet | claude-work | 4 |
| T18b | Cross-check audit of T18: Independent security and spec audit by another provider | alta | pendiente | gpt-6.1-sol | codex-1 | 3 |
| T19 | Documentation: remote README, references and TOOLS entries to copy at go-live | baja | pendiente | gemini-3.8-flash-low | antigravity | 2 |

**M6 — Production environment** · dificultad alta · 0/5

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T20 | Create the AdvIn production environment: service user, directories, units and Caddy block | alta | pendiente | — | — | 0 |
| T21 | Create the Vercel project and deploy the frontend to production | media | pendiente | — | — | 0 |
| T22 | Create the identity and messaging prerequisites and place the secrets | media | pendiente | — | — | 0 |
| T23 | Release the gateway and the Telegram bot to AdvIn and switch them on | alta | pendiente | — | — | 0 |
| T24 | Live smoke test of the production environment and handover | media | pendiente | — | — | 0 |
<!-- bitacora:status:end -->

## Approach
Three pieces, one direction of trust. **Laptop** (the only executor): `bt_server` gains a remote API
`/api/remote/v1/` guarded by a gateway key, a command ledger (idempotency + preconditions, dispatching to the existing
operator moves and to D-020's decision answers) and an append-only event feed; it stays bound to `127.0.0.1` and is
reached from AdvIn only through the existing reverse SSH tunnel (`advin-bitacora-tunnel.service`). **Gateway** on AdvIn
(`remote/gateway`, Python 3.12 **standard library only**, like `bt_server`: a threading HTTP server, `urllib` for
GitHub and Telegram, SQLite; systemd on the host, bound to `172.20.0.1:8790`, published by the existing Caddy container
as `flow-api.185-147-157-25.sslip.io`): GitHub OAuth for `dav033`, sessions, liveness, snapshot cache, SSE fan-out,
command relay, deterministic notification rules and a Telegram bot by long polling. **Web** on Vercel (`remote/web`,
Next.js 15 + React 19 + Tailwind 4, project `flow-remote`, local fonts): mobile-first PWA that reaches the gateway
through same-origin rewrites (`/api/*` → gateway), as `lotm-frontend` does. Pure flow logic is reused from
`skill/assets/flow-core.js`.
**How it runs (r3):** the scheduler builds and tests everything against fakes (a fake laptop for the gateway, a mock
gateway for the web); no task touches `main`, the live panel, AdvIn, Vercel or the bitácora. Then the run ends and the
**go-live** happens once, with the owner (section below). Every task is ≤90 min (owner: always split) and every
`verify` runs offline in the verifier sandbox (no network, no home, no `$|;<>`, no `PYTHONPATH=`).
Alternatives weighed (recorded in `remote/docs/architecture.md` by T3, copied to DECISIONS.md at go-live): exposing
the laptop or an outbound WebSocket agent (rejected: the tunnel exists and exposes nothing); Auth.js on Vercel
(rejected: the gateway would still need its own trust of the caller); Starlette/uvicorn for the gateway (rejected:
`uv` and third-party packages cannot run in the offline verifier, and one user needs no async stack); queuing commands
while offline (rejected by the owner).

## Global constraints
- Execution never leaves the laptop; AdvIn holds no Claude/Codex credentials (SPEC §Out of scope).
- The local panel keeps its behavior and tests (R18); the laptop never listens beyond `127.0.0.1`.
- T1-T19 never edit `bitacora/`, never merge to `main`, never deploy, never ssh to AdvIn: notes go to `remote/docs/`. M6 (T20-T24) may ssh to AdvIn and deploy to Vercel, only as its criteria describe (owner decision 2026-10-19, D-078).
- Secrets only in mode-600 env files and Vercel env vars, never in git or the bitácora (R16). Gitleaks stays on.
- Every command: idempotency key + precondition; no queue while offline (R6, R7).
- UI: Spanish copy, Catppuccin Mocha + mauve `#cba6f7`, JetBrainsMono (local font files), 360 px without horizontal
  scroll, ≥44 px targets (R14).
- Verify commands: `cd <dir> && <argv>` only; laptop tests as `cd skill/scripts && python -m unittest discover -s tests -p <file>`.

## Keys and access (references only, never values)
| What | Where / how | Status |
|---|---|---|
| AdvIn shell | `ssh advin` → `root@185.147.157.25`, key `~/.ssh/id_ed25519_advin` (`~/.ssh/config`) | works |
| Laptop → AdvIn tunnel | `advin-bitacora-tunnel.service` (user unit, `-R 127.0.0.1:8765:127.0.0.1:8765`) | active |
| Caddy on AdvIn | Docker container `caddy`; config `/etc/caddy/Caddyfile` inside it (host path found at go-live 3) | running |
| Vercel | `vercel` CLI logged in as `dav033`, scope `dav033s-projects`; new project `flow-remote` | works |
| GitHub | `gh` logged in as `dav033`; OAuth App `flow-remote` → `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | **to create** (go-live 2) |
| Telegram | bot from @BotFather → `TELEGRAM_BOT_TOKEN`; owner sends `/start` → `TELEGRAM_CHAT_ID` | **owner creates** (go-live 2) |
| Gateway ↔ laptop | `FLOW_GATEWAY_KEY` (generated, 48 bytes): laptop `~/.config/bitacora/remote.env`, AdvIn `/etc/flow-gateway/env` | generated at go-live 2 |
| Sessions | `SESSION_SECRET` (generated) in `/etc/flow-gateway/env` | generated at go-live 2 |
| Frontend config | Vercel env `GATEWAY_ORIGIN=https://flow-api.185-147-157-25.sslip.io` (not secret) | set at go-live 4 |
| DNS (later) | NS1 `my.nsone.net`, needs the owner's login; only for a custom domain | deferred |

## Tasks

### M1 — Contracts
- [ ] T2 — Research where a per-task route pin enters M2 routing and the executor · repo: skill · files: remote/docs/route-pin.md · verify: `test -s remote/docs/route-pin.md` · covers: R13 · kind: research
- [ ] T3 — Remote API contract, command and event schemas, and the architecture note · repo: skill · files: remote/docs/contract.md, remote/docs/architecture.md, remote/contract/** · after: T2 · verify: `python -m json.tool remote/contract/command.schema.json` · covers: R3, R5, R6, R10 · kind: implement

### M2 — Laptop: remote API, ledger and feed
- [ ] T4 — Remote API skeleton behind the gateway key, with health · repo: skill · files: skill/scripts/bt_remote_api.py, skill/scripts/bt_server.py, skill/scripts/tests/test_remote_api.py · after: T3 · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py` · covers: R3, R18 · kind: implement
- [ ] T4a — Snapshot endpoint over the shared live caches · repo: skill · files: skill/scripts/bt_remote_api.py, skill/scripts/tests/test_remote_api.py · after: T4 · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py` · covers: R4 · kind: implement
- [ ] T5 — Command ledger store: idempotency keys, preconditions and audit rows · repo: skill · files: skill/scripts/bt_remote_commands.py, skill/scripts/tests/test_remote_commands.py · after: T4a · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py` · covers: R6, R15 · kind: implement
- [ ] T5a — Ledger dispatch for run moves and decision answers · repo: skill · files: skill/scripts/bt_remote_commands.py, skill/scripts/tests/test_remote_commands.py · after: T5 · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py` · covers: R5, R6 · kind: implement
- [ ] T5b — Ledger dispatch for plans and rounds with the confirmation challenge · repo: skill · files: skill/scripts/bt_remote_commands.py, skill/scripts/tests/test_remote_commands.py · after: T5a · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py` · covers: R5, R8 · kind: implement
- [ ] T6 — Event feed with stable ids and a cursor, including decision requests · repo: skill · files: skill/scripts/bt_remote_events.py, skill/scripts/tests/test_remote_events.py · after: T5b · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py` · covers: R10, R11 · kind: implement
- [ ] T7 — Failure review read model per attempt · repo: skill · files: skill/scripts/bt_remote_api.py, skill/scripts/tests/test_remote_review.py · after: T6 · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py` · covers: R9 · kind: implement
- [ ] T8 — Retry pinned to a route, model or account · repo: skill · files: skill/scripts/bt_remote_commands.py, skill/scripts/tests/test_remote_recovery.py · after: T7 · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py` · covers: R13 · kind: implement
- [ ] T8a — Brief or criteria edit as an owner-approved plan revision · repo: skill · files: skill/scripts/bt_remote_commands.py, skill/scripts/tests/test_remote_recovery.py · after: T8 · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py` · covers: R13 · kind: implement
- [ ] T9 — One owner of port 8765 and reloads that keep the listening socket · repo: skill · files: skill/scripts/bt_server.py, skill/scripts/bt_platform.py, skill/scripts/tests/test_platform.py · after: T8a · verify: `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` · covers: R7, R18 · kind: implement

### M3 — Gateway (tested against a fake laptop)
- [ ] T10 — Gateway skeleton: config, upstream client and liveness state · repo: skill · files: remote/gateway/** · after: T3 · verify: `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py` · covers: R7, R17 · kind: implement
- [ ] T11 — GitHub OAuth for dav033 and server-side sessions · repo: skill · files: remote/gateway/** · after: T10 · verify: `cd remote/gateway && python -m unittest discover -s tests -p test_auth.py` · covers: R1, R2 · kind: implement
- [ ] T11a — CSRF header, Origin check, rate limits and request log · repo: skill · files: remote/gateway/** · after: T11 · verify: `cd remote/gateway && python -m unittest discover -s tests -p test_guard.py` · covers: R2, R17 · kind: implement
- [ ] T12 — Snapshot cache and SSE fan-out with Last-Event-ID · repo: skill · files: remote/gateway/** · after: T11a, T4a · verify: `cd remote/gateway && python -m unittest discover -s tests -p test_stream.py` · covers: R4, R7 · kind: implement
- [ ] T13 — Command relay with challenge, LAPTOP_OFFLINE and UNKNOWN_OUTCOME · repo: skill · files: remote/gateway/** · after: T12, T5b · verify: `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py` · covers: R5, R6, R7, R8 · kind: implement
- [ ] T14 — Deterministic notification rules with dedupe keys · repo: skill · files: remote/gateway/** · after: T13, T6 · verify: `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` · covers: R10, R11 · kind: implement
- [ ] T14a — Telegram delivery with retries, backoff and history · repo: skill · files: remote/gateway/** · after: T14 · verify: `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_send.py` · covers: R10, R15 · kind: implement
- [ ] T14b — Telegram bot: long polling, chat allowlist, safe buttons and /estado · repo: skill · files: remote/gateway/** · after: T14a · verify: `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_bot.py` · covers: R12 · kind: implement

### M4 — Mobile web (tested against a mock gateway)
- [ ] T15 — Web scaffold: Next.js, theme tokens, local fonts, PWA manifest, rewrites, mock gateway · repo: skill · files: remote/web/** · after: T3 · verify: `cd remote/web && npm run verify` · covers: R14 · kind: implement
- [ ] T15a — Login screen and runs list · repo: skill · files: remote/web/** · after: T15 · verify: `cd remote/web && npm run verify` · covers: R1, R4 · kind: implement
- [ ] T15b — Run view: activity strip, tasks and feed on flow-core.js · repo: skill · files: remote/web/** · after: T15a · verify: `cd remote/web && npm run verify` · covers: R4, R14 · kind: implement
- [ ] T15c — Failure review screen · repo: skill · files: remote/web/** · after: T15b, T7 · verify: `cd remote/web && npm run verify` · covers: R9 · kind: implement
- [ ] T15d — Control sheet with typed confirmations and command history · repo: skill · files: remote/web/** · after: T15c, T13 · verify: `cd remote/web && npm run verify` · covers: R5, R8, R15 · kind: implement
- [ ] T15e — Plans, question rounds and decision requests screens · repo: skill · files: remote/web/** · after: T15d · verify: `cd remote/web && npm run verify` · covers: R5, R8 · kind: implement
- [ ] T15f — Recovery forms and live quotas · repo: skill · files: remote/web/** · after: T15e, T8a · verify: `cd remote/web && npm run verify` · covers: R13, R15 · kind: implement

### M5 — Go-live kit and audit
- [ ] T16 — Go-live kit: systemd unit, Caddy block, env example, deploy and rollback scripts, runbook · repo: skill · files: remote/deploy/**, remote/docs/runbook.md · after: T14b, T15f, T9 · verify: `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` · covers: R16, R3 · kind: implement
- [ ] T17 — Offline end-to-end: real laptop API, gateway and built web wired locally on loopback · repo: skill · files: remote/e2e/** · after: T16 · verify: `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` · covers: R1, R4, R5, R6, R7, R10, R11, R12, R18 · kind: test
- [ ] T18 — Independent security and spec audit by another provider · repo: skill · files: remote/docs/audit.md, remote/docs/audit.findings.json · after: T17 · verify: `test -s remote/docs/audit.md` · covers: R1, R2, R3, R16, R17 · kind: audit
- [ ] T18b — Cross-check audit of T18: Independent security and spec audit by another provider · repo: skill · files: remote/docs/audit-crosscheck.md, remote/docs/audit-crosscheck.findings.json · after: T17, T18 · verify: `test -s remote/docs/audit-crosscheck.md` · covers: R1, R2, R3, R16, R17 · kind: audit
- [ ] T19 — Documentation: remote README, references and TOOLS entries to copy at go-live · repo: skill · files: remote/README.md, remote/docs/tools-entries.md · after: T18, T18b · verify: `test -s remote/docs/tools-entries.md` · covers: R16, R18 · kind: docs

### M6 — Production environment
- [ ] T20 — Create the AdvIn production environment: service user, directories, units and Caddy block · repo: skill · files: remote/deploy/**, remote/docs/runbook.md · after: T19 · verify: `cd remote/deploy && python verify_receipt.py advin-provision --check snapshot-before` · covers: R16, R3, R19 · kind: implement
- [ ] T21 — Create the Vercel project and deploy the frontend to production · repo: skill · files: remote/deploy/** · after: T20 · verify: `cd remote/deploy && python verify_receipt.py vercel-frontend --check project-linked` · covers: R16, R19 · kind: implement
- [ ] T22 — Create the identity and messaging prerequisites and place the secrets · repo: skill · files: remote/deploy/** · after: T21 · verify: `cd remote/deploy && python verify_receipt.py identity --check oauth-app` · covers: R16, R1, R19 · kind: implement
- [ ] T23 — Release the gateway and the Telegram bot to AdvIn and switch them on · repo: skill · files: remote/deploy/**, remote/docs/runbook.md · after: T22 · verify: `cd remote/deploy && python verify_receipt.py gateway-release --check release-active` · covers: R3, R16, R17, R19 · kind: implement
- [ ] T24 — Live smoke test of the production environment and handover · repo: skill · files: remote/deploy/receipts/** · after: T23 · verify: `cd remote/deploy && python verify_receipt.py live-smoke --check signin-start` · covers: R1, R2, R10, R19 · kind: test

## Go-live with the owner (superseded by milestone M6 where noted)
_Steps 2-5 are now tasks T20-T24; steps 1 and 6 (merge to `main`, copy the notes) stay with the owner._
One stop, together, in this order; each step has its rollback in `remote/docs/runbook.md`:
1. Review the diff of the run and merge it to `main` (owner's OK), restart `bitacora-web`, check `/flow` and `/plans`.
2. Owner creates the Telegram bot (@BotFather) and sends `/start`; the GitHub OAuth App is created (agents' Firefox
   if a GitHub session is there, otherwise the owner); keys generated into the env files (Keys table).
3. Gateway on AdvIn: back up the Caddyfile, install the unit, add the site block, reload Caddy, check `healthz` and the
   other sites.
4. Vercel production deploy with `GATEWAY_ORIGIN`.
5. Real end-to-end at 360 px: sign-in as dav033 (a foreign account refused), live view, a command, offline banner
   after stopping the tunnel, one Telegram alert from a forced failure on a sandbox plan.
6. Copy `remote/docs/architecture.md` into DECISIONS.md and `remote/docs/tools-entries.md` into TOOLS.md.

## Spike (coordinator, before resuming)
The old T1: check that Vercel external rewrites forward `Set-Cookie` and keep an SSE stream open, and how long; result
in `remote/docs/spike-rewrite-sse.md`, committed before the run resumes so T3 can read it.

## Verification
- Per task: the offline `verify` above (unit tests of laptop modules, gateway `unittest`, `npm run verify` =
  typecheck + lint + unit + build without network).
- T17: everything wired on loopback with a fixture bitácora: sign-in through a fake GitHub, runs list within 5 s,
  cancel an attempt through the ledger, stale precondition refused, gateway marks the laptop offline when the fake
  tunnel stops, exactly one notification per forced failure through a fake Telegram.
- Go-live step 5 is the real end-to-end; the local panel keeps passing its suites.

## Proposals — deterministic systems for execution
Built into this plan: the command ledger with preconditions (T5), the event feed with stable ids (T6), the liveness
state machine (T10) and the notification rules (T14). Proposed next, each as its own requirement:
1. **Failure triage table.** One versioned table: evidence pattern (exit code, stderr signature, verify output,
   timeout, quota message) → cause → action (retry, wait for reset, reroute, block for owner). M5 already classifies
   causes; this makes the table explicit, testable with fixtures and visible on the phone, so "why did it retry?" has
   a single answer.
2. **Declarative autopilot with dry run.** Owner rules such as "if T fails twice by timeout, raise the timeout to
   120 min and retry" or "if every account is out of quota, hold until the earliest reset". The engine shows what it
   *would* do before it is switched on.
3. **Preflight gate before every dispatch.** A fixed checklist (clean worktree, disk free, quota left, credentials
   valid, tunnel and panel up) that produces go/no-go with the failing item, instead of discovering it mid-attempt.
4. **Invariant doctor.** Periodic assertions with known fixes: one owner per plan, one process on 8765, no orphan
   agents, ledger and SCHEDULER.db agree, no attempt running without a lease. Reports and repairs only the listed cases.
5. **Golden replay.** Record a run's bus and replay it through the feed, the rules and the UI in CI, so a change to
   notifications or the flow page is checked against real runs.
6. **Budget governor.** Hard caps per task and per run (tokens, minutes, attempts) that hold the run when crossed.
7. **Panel supervisor.** A single systemd-owned server with socket activation and graceful reload, so code updates
   never drop the page (T9 starts this; the proposal makes it the only way the panel runs).

## Rulings
- New code lives in the methodology repo under `remote/` (`gateway/`, `web/`, `deploy/`, `e2e/`, `docs/`, `contract/`),
  because it is a feature of the skill and the plan contract only knows the `skill` repository.
- r3: the gateway uses only the Python standard library (the verifier sandbox has no network or home, so `uv run` and
  third-party packages cannot be checked there); the old T1 spike moves to the coordinator; external steps become the
  go-live section; T5/T8/T14/T15 are split (owner: always split); laptop tasks run in sequence because they share
  `bt_remote_api.py`/`bt_remote_commands.py`; operator notes already exist (D-020, `RUN.notes`), so recovery keeps only
  the route pin and the brief edit.

## Progress log
- 2026-10-19: r3 — round 3 (execution risks): offline verifies, stdlib gateway, all tasks ≤90 min, go-live with the owner after the run, spike by the coordinator, D-020 decision requests reused.
- 2026-10-19: r2 — T3 reclassified kind docs → implement, complexity high → extreme (owner approved): as docs, the D-066 tier-0 ceiling routed the architecture contract to Gemini Flash.
- 2026-10-19: spec and plan written after two interview rounds.
- 2026-10-19 14:45 plan APPROVED (terminal)
- 2026-10-19 14:46 launched Scheduler supervisor from HQ in `/home/david/dev/metodologia`
