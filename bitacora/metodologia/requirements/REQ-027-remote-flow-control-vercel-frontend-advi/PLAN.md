---
req: REQ-027
status: launched
created: 2026-10-19
---
# Plan — REQ-027 — Remote flow control: Vercel frontend, AdvIn API, local or VPS execution

<!-- bitacora:status:begin -->
> Bloque generado, no editar a mano. Plan: launched · ejecución: running · hitos 0/5 · tareas 0/23 · generado: 2026-10-19T14:46:28-05:00

**M1 — Spikes and contracts** · dificultad alta · 0/3

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T1 | Spike: Vercel external rewrite forwards cookies and streams SSE from AdvIn | media | en curso | gpt-6-luna | codex-luis | 1 |
| T2 | Research the scheduler injection points for a per-task route pin and operator notes | media | en curso | gpt-6-luna | codex-luis | 1 |
| T3 | Write the remote API contract (endpoints, command schema, errors, event kinds) and the architecture decision | alta | pendiente | — | — | 0 |

**M2 — Laptop: remote API, ledger and feed** · dificultad alta · 0/6

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T4 | Remote API skeleton in `bt_server` behind the gateway key, with health and snapshot endpoints | media | pendiente | — | — | 0 |
| T5 | Command ledger: idempotency, preconditions, dispatch to scheduler/plan/round operations, audit | alta | pendiente | — | — | 0 |
| T6 | Event feed: the six notification kinds as deterministic events with stable ids and a cursor | alta | pendiente | — | — | 0 |
| T7 | Failure review read model: cause, verification output, diff stat, log tail per attempt | media | pendiente | — | — | 0 |
| T8 | Extended recovery: retry pinned to a route, brief edit as a plan revision, note in the next prompt | alta | pendiente | — | — | 0 |
| T9 | Stop the panel from flapping: one owner of port 8765 and restarts that do not drop clients | media | pendiente | — | — | 0 |

**M3 — Gateway on AdvIn** · dificultad alta · 0/5

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T10 | Gateway skeleton: config, upstream client, liveness probe and offline state | media | pendiente | — | — | 0 |
| T11 | GitHub OAuth for dav033, sessions, CSRF header and Origin checks, rate limits | media | pendiente | — | — | 0 |
| T12 | Read proxy with snapshot cache and SSE fan-out with Last-Event-ID | alta | pendiente | — | — | 0 |
| T13 | Command relay with confirmation challenge, LAPTOP_OFFLINE and UNKNOWN_OUTCOME | media | pendiente | — | — | 0 |
| T14 | Notification rules and Telegram bot: dedupe, retries, safe buttons, /estado, chat allowlist | alta | pendiente | — | — | 0 |

**M4 — Mobile web on Vercel** · dificultad media · 0/3

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T15 | Web foundation: Next.js app, theme tokens, PWA manifest, rewrites, login, runs list and run view | media | pendiente | — | — | 0 |
| T15a | Web failure review, control sheet with confirmations and command history | media | pendiente | — | — | 0 |
| T15b | Web plans, question rounds, extended recovery forms and live quotas | media | pendiente | — | — | 0 |

**M5 — Deploy, verify, close** · dificultad alta · 0/6

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T16 | Owner prerequisites and secrets: Telegram bot + chat id, GitHub OAuth App, generated keys in env files | baja | pendiente | — | — | 0 |
| T17 | Deploy the gateway on AdvIn: systemd unit, Caddy site block with backup and rollback | media | pendiente | — | — | 0 |
| T18 | Deploy the web to Vercel production with its env vars | baja | pendiente | — | — | 0 |
| T19 | End-to-end check on a phone viewport against production with a sandbox plan | alta | pendiente | — | — | 0 |
| T20 | Independent security and spec audit by another provider | alta | pendiente | — | — | 0 |
| T21 | Documentation: TOOLS.md entries, runbook, rollback, references | baja | pendiente | — | — | 0 |
<!-- bitacora:status:end -->

## Approach
Three pieces, one direction of trust. **Laptop** (unchanged executor): `bt_server` gains a remote API
`/api/remote/v1/` guarded by a gateway key, a command ledger (idempotency + preconditions) and an append-only event
feed; it stays bound to `127.0.0.1` and is reached from AdvIn only through the existing reverse SSH tunnel
(`advin-bitacora-tunnel.service`, AdvIn `127.0.0.1:8765` → laptop `127.0.0.1:8765`). **Gateway** on AdvIn
(`remote/gateway`, Python 3.12 + Starlette/uvicorn/httpx, systemd on the host, bound to `172.20.0.1:8790`, published by
the existing Caddy container as `flow-api.185-147-157-25.sslip.io`): GitHub OAuth for `dav033`, session cookies,
liveness probe, snapshot cache, SSE fan-out, command relay, deterministic notification rules and a Telegram bot by long
polling. **Web** on Vercel (`remote/web`, Next.js 15 + React 19 + Tailwind 4, project `flow-remote`): mobile-first PWA
that reaches the gateway through same-origin rewrites (`/api/*` → gateway), as `lotm-frontend` already does, so cookies
stay first-party and there is no CORS. Pure flow logic is reused from `skill/assets/flow-core.js`.
Alternatives weighed (→ DECISIONS.md at T3): exposing the laptop or a new outbound WebSocket agent (rejected: the
tunnel already exists, is SSH-authenticated and exposes nothing); auth on Vercel with Auth.js (rejected: the gateway
would still need its own trust of the caller); queuing commands while offline (rejected by the owner).

## Global constraints
- Execution never leaves the laptop; AdvIn holds no Claude/Codex credentials (SPEC §Out of scope).
- The local panel keeps its behavior and tests (R18); the laptop never listens beyond `127.0.0.1`.
- Secrets only in mode-600 env files and Vercel env vars, never in git or the bitácora (R16). Gitleaks stays on.
- Every command: idempotency key + precondition; no queue while offline (R6, R7).
- UI: Spanish copy, Catppuccin Mocha + mauve `#cba6f7`, JetBrainsMono, 360 px without horizontal scroll, ≥44 px
  targets (R14).
- Deploy with CLIs (`vercel deploy --prod`, `ssh advin`); no `git push`, no merge to `main`.
- Back up any AdvIn file before editing it (Caddyfile, units) and keep a rollback command next to each change.

## Keys and access (references only, never values)
| What | Where / how | Status |
|---|---|---|
| AdvIn shell | `ssh advin` → `root@185.147.157.25`, key `~/.ssh/id_ed25519_advin` (`~/.ssh/config`) | works |
| Laptop → AdvIn tunnel | `advin-bitacora-tunnel.service` (user unit, `-R 127.0.0.1:8765:127.0.0.1:8765`) | active |
| Caddy on AdvIn | Docker container `caddy`; config `/etc/caddy/Caddyfile` inside it (host path found in T17) | running |
| Vercel | `vercel` CLI logged in as `dav033`, scope `dav033s-projects`; new project `flow-remote` | works |
| GitHub | `gh` logged in as `dav033`; OAuth App `flow-remote` → `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | **to create** (T16) |
| Telegram | bot from @BotFather → `TELEGRAM_BOT_TOKEN`; owner sends `/start` → `TELEGRAM_CHAT_ID` | **owner creates** (T16) |
| Gateway ↔ laptop | `FLOW_GATEWAY_KEY` (generated, 48 bytes): laptop `~/.config/bitacora/remote.env`, AdvIn `/etc/flow-gateway/env` | generated in T16 |
| Sessions | `SESSION_SECRET` (generated) in `/etc/flow-gateway/env` | generated in T16 |
| Frontend config | Vercel env `GATEWAY_ORIGIN=https://flow-api.185-147-157-25.sslip.io` (not secret) | set in T18 |
| DNS (later) | NS1 `my.nsone.net`, needs the owner's login; only for a custom domain | deferred |

## Tasks

### M1 — Spikes and contracts
- [ ] T1 — Spike: Vercel external rewrite forwards cookies and streams SSE from AdvIn · repo: skill · files: remote/spikes/rewrite-sse/** · verify: `python remote/spikes/rewrite-sse/check.py` · covers: R2, R4
- [ ] T2 — Research the scheduler injection points for a per-task route pin and operator notes · repo: skill · files: skill/scripts/bt_scheduler_plan_routing.py, skill/scripts/bt_runprompt.py · verify: `test -s remote/docs/injection-points.md` · covers: R13
- [ ] T3 — Write the remote API contract (endpoints, command schema, errors, event kinds) and the architecture decision · repo: skill · files: remote/docs/contract.md, remote/contract/** · after: T1, T2 · verify: `python -m json.tool remote/contract/command.schema.json` · covers: R3, R5, R6, R10 · kind: implement

### M2 — Laptop: remote API, ledger and feed
- [ ] T4 — Remote API skeleton in `bt_server` behind the gateway key, with health and snapshot endpoints · repo: skill · files: skill/scripts/bt_remote_api.py, skill/scripts/bt_server.py · after: T3 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_remote_api` · covers: R3, R4, R18
- [ ] T5 — Command ledger: idempotency, preconditions, dispatch to scheduler/plan/round operations, audit · repo: skill · files: skill/scripts/bt_remote_commands.py · after: T4 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_remote_commands` · covers: R5, R6, R8, R15
- [ ] T6 — Event feed: the six notification kinds as deterministic events with stable ids and a cursor · repo: skill · files: skill/scripts/bt_remote_events.py · after: T4 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_remote_events` · covers: R10, R11
- [ ] T7 — Failure review read model: cause, verification output, diff stat, log tail per attempt · repo: skill · files: skill/scripts/bt_remote_api.py · after: T4 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_remote_api` · covers: R9
- [ ] T8 — Extended recovery: retry pinned to a route, brief edit as a plan revision, note in the next prompt · repo: skill · files: skill/scripts/bt_remote_commands.py · after: T5 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_remote_recovery` · covers: R13
- [ ] T9 — Stop the panel from flapping: one owner of port 8765 and restarts that do not drop clients · repo: skill · files: skill/scripts/bt_server.py · after: T4 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_platform` · covers: R7, R18

### M3 — Gateway on AdvIn
- [ ] T10 — Gateway skeleton: config, upstream client, liveness probe and offline state · repo: skill · files: remote/gateway/** · after: T3 · verify: `cd remote/gateway && uv run pytest -q tests/test_liveness.py` · covers: R7, R17
- [ ] T11 — GitHub OAuth for dav033, sessions, CSRF header and Origin checks, rate limits · repo: skill · files: remote/gateway/** · after: T10 · verify: `cd remote/gateway && uv run pytest -q tests/test_auth.py` · covers: R1, R2, R17
- [ ] T12 — Read proxy with snapshot cache and SSE fan-out with Last-Event-ID · repo: skill · files: remote/gateway/** · after: T4, T11 · verify: `cd remote/gateway && uv run pytest -q tests/test_stream.py` · covers: R4, R7
- [ ] T13 — Command relay with confirmation challenge, LAPTOP_OFFLINE and UNKNOWN_OUTCOME · repo: skill · files: remote/gateway/** · after: T5, T12 · verify: `cd remote/gateway && uv run pytest -q tests/test_commands.py` · covers: R5, R6, R7, R8
- [ ] T14 — Notification rules and Telegram bot: dedupe, retries, safe buttons, /estado, chat allowlist · repo: skill · files: remote/gateway/** · after: T6, T13 · verify: `cd remote/gateway && uv run pytest -q tests/test_notify.py tests/test_telegram.py` · covers: R10, R11, R12

### M4 — Mobile web on Vercel
- [ ] T15 — Web foundation: Next.js app, theme tokens, PWA manifest, rewrites, login, runs list and run view · repo: skill · files: remote/web/** · after: T12 · verify: `cd remote/web && npm run verify` · covers: R1, R4, R14
- [ ] T15a — Web failure review, control sheet with confirmations and command history · repo: skill · files: remote/web/** · after: T15, T7, T13 · verify: `cd remote/web && npm run verify` · covers: R5, R8, R9, R15
- [ ] T15b — Web plans, question rounds, extended recovery forms and live quotas · repo: skill · files: remote/web/** · after: T15a, T8 · verify: `cd remote/web && npm run verify` · covers: R13, R15

### M5 — Deploy, verify, close
- [ ] T16 — Owner prerequisites and secrets: Telegram bot + chat id, GitHub OAuth App, generated keys in env files · repo: skill · files: remote/deploy/env.example · after: T14, T15b · verify: `ssh advin 'test "$(stat -c %a /etc/flow-gateway/env)" = 600'` · covers: R16
- [ ] T17 — Deploy the gateway on AdvIn: systemd unit, Caddy site block with backup and rollback · repo: skill · files: remote/deploy/** · after: T16 · verify: `curl -fsS https://flow-api.185-147-157-25.sslip.io/healthz` · covers: R3, R7, R16
- [ ] T18 — Deploy the web to Vercel production with its env vars · repo: skill · files: remote/web/** · after: T17 · verify: `curl -fsS -o /dev/null https://flow-remote.vercel.app/login` · covers: R1, R14
- [ ] T19 — End-to-end check on a phone viewport against production with a sandbox plan · repo: skill · files: remote/e2e/** · after: T18, T9 · verify: `cd remote/e2e && npm test` · covers: R1, R2, R3, R4, R5, R6, R7, R9, R10, R11, R12, R14, R17, R18
- [ ] T20 — Independent security and spec audit by another provider · repo: skill · after: T19 · verify: `test -s remote/docs/audit.md` · covers: R1, R2, R3, R16, R17
- [ ] T21 — Documentation: TOOLS.md entries, runbook, rollback, references · repo: skill · files: remote/README.md · after: T20 · verify: `grep -q flow-gateway bitacora/dev/TOOLS.md` · covers: R16, R18

## Verification
- Unit/integration: `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_remote_api test_remote_commands test_remote_events test_remote_recovery test_platform`, the existing panel suites (`test_live_api`, `test_scheduler_ops`, page tests), `cd remote/gateway && uv run pytest -q`, `cd remote/web && npm run verify` (typecheck, lint, unit, build).
- End to end (T19, Playwright at 360×800 against production, sandbox plan with `echo`-style tasks): sign-in as dav033;
  a foreign GitHub user is refused; runs list and run view update within 5 s; cancel an attempt and see it in the
  ledger; a stale precondition is refused; stop the tunnel → "sin conexión" within 20 s and commands rejected;
  restart it → online again; a forced failure produces exactly one Telegram message whose button opens the review.
- Local panel unchanged: `http://127.0.0.1:8765/flow` and `/plans` still serve, full suite has no new failures.

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
- T3 (planned): new code lives in the methodology repo under `remote/` (`gateway/`, `web/`, `deploy/`, `e2e/`,
  `docs/`), because it is a feature of the skill and the plan contract only knows the `skill` repository.

## Progress log
- 2026-10-19: r2 — T3 reclassified kind docs → implement, complexity high → extreme (owner approved): as docs, the D-066 tier-0 ceiling routed the architecture contract to Gemini Flash.
- 2026-10-19: spec and plan written after two interview rounds.
- 2026-10-19 14:45 plan APPROVED (terminal)
- 2026-10-19 14:46 launched Scheduler supervisor from HQ in `/home/david/dev/metodologia`
