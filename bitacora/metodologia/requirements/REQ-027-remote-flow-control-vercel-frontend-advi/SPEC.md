---
id: REQ-027
status: planned
created: 2026-10-19
track: deep
---
# REQ-027 — Remote flow control: Vercel frontend, AdvIn API, local or VPS execution

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The owner can only watch and steer scheduler runs from the laptop's loopback panel (`/flow`, `/plans` at
`127.0.0.1:8765`, no login). Runs last hours or days; when a task fails or blocks while he is away, nothing tells him
and he cannot act until he is back at the laptop. He wants the same view and control from his phone: a frontend on
Vercel, a simple control server on the AdvIn VPS, failure alerts, and failures he can review and fix remotely.

Execution itself stays on the laptop (round 1, q1 = a). AdvIn is a control plane only: it never runs agents and holds
no Claude/Codex credentials.

**Success looks like:**
- From the phone (360 px wide, mobile data), the owner signs in with GitHub and sees every run's live state within
  5 s of the laptop panel.
- A failed or blocked task reaches him on Telegram within 60 s, with a link that opens the failure review.
- He can pause, resume, cancel an attempt, reopen/retry a task (optionally on another route), edit a task's brief,
  leave a note, approve/launch a plan and answer a question round without touching the laptop.
- While the laptop is offline the web shows the last known state with "sin conexión desde HH:MM" and rejects
  commands; nothing he taps executes later.
- The laptop is never exposed to the internet; the local panel keeps working unchanged.

## Users / actors / stakeholders
- **Owner (David, GitHub `dav033`)**: the only human user; phone (PWA + Telegram) and laptop.
- **Laptop panel (`bt_server`)**: source of truth for runs; gains a remote API behind a gateway key.
- **Gateway on AdvIn**: login, cache of the last state, command relay, notification rules, Telegram bot.
- **Vercel frontend**: mobile-first web app; talks only to the gateway, through same-origin rewrites.
- **Telegram bot**: alerts and safe actions; obeys only the owner's `chat_id`.

## Scope (in)
### US-1 (P1, Must) — See runs from the phone
As the owner, I want the runs list and each run's live flow (who works now, tasks, feed, agent activity) on my phone
so that I know where a run is without the laptop.
**Acceptance:**
- Given an active run, when I open it on a 360 px viewport, then I see the active module, task, attempt and last sign
  of life, updated within 5 s, with no horizontal scroll.

### US-2 (P1, Must) — Control a run
As the owner, I want pause, resume, cancel attempt, reopen/retry task and revise from the phone so that I can steer a
run remotely.
**Acceptance:**
- Given a running attempt, when I cancel it from the phone, then the laptop's scheduler records an operator cancel with
  my reason and the command appears in the history as `done`.
- Given the run changed after my screen loaded, when I send a command whose precondition no longer holds, then it is
  rejected with "el estado cambió" and nothing changes.

### US-3 (P1, Must) — Review a failure
As the owner, I want a failed attempt's cause, verification output, diff and log tail so that I can decide what to do.
**Acceptance:**
- Given a failed attempt, when I open it, then I see the classified cause, the failing verification command with its
  output, the changed files and the last lines of the agent log.

### US-4 (P1, Must) — Telegram alerts with safe buttons
As the owner, I want a Telegram message for every event that needs me, with buttons for safe actions.
**Acceptance:**
- Given a task fails with no retries left, when the event is produced, then within 60 s one Telegram message arrives
  with the run, task, cause, a link and buttons (ver, reintentar, pausar).
- Given the same event is seen twice, then only one message is sent.

### US-5 (P2, Should) — Plans and rounds from the phone
As the owner, I want to approve/launch a plan and answer question rounds from the phone.
**Acceptance:**
- Given a plan in review, when I approve it, then I must confirm by typing its REQ id, and the plan is frozen and
  launched exactly once.

### US-6 (P2, Should) — Extended recovery
As the owner, I want to retry a task with another route/model/account, edit its brief or criteria before retrying,
and leave a note the next attempt reads.
**Acceptance:**
- Given a failed task, when I retry it pinned to another route, then the next attempt runs on that route.
- Given I edited a task's brief, then a new plan revision is recorded, frozen with my approval, and the run rebases.
- Given I left a note, then the next attempt's prompt contains it.

### US-7 (P3, Could) — Quotas and command history
As the owner, I want live account quotas and the history of every remote command (what, when, from where, result).

## Out of scope
- Running the scheduler or agents on AdvIn (q1 = a); Claude/Codex logins on AdvIn.
- Multi-user access, roles or sharing; anyone but `dav033`.
- Custom domain (`marosconstruction.com` via NS1) — later, as an env var + CNAME (q2 = a).
- Queued/deferred commands while the laptop is offline (q1 round 2 = a).
- Launching, approving or deleting plans from Telegram (q3 = b): web only.
- Rewriting the local panel; it stays as it is at `127.0.0.1:8765`.
- Native mobile apps.

## Requirements
- R1. When a request reaches the gateway without a valid session, the gateway shall answer 401 and offer GitHub
  sign-in; when the GitHub login is not `dav033`, it shall refuse the session.
- R2. The gateway shall keep sessions in HttpOnly, Secure, SameSite=Strict cookies bound to the frontend host,
  and shall reject state-changing requests that lack the custom header `X-Flow-Request: 1` or carry a foreign Origin.
- R3. The laptop shall expose a remote API under `/api/remote/v1/` that answers only requests carrying the gateway key
  (constant-time compare) and is reachable from AdvIn only through the existing reverse SSH tunnel.
- R4. When the owner opens the web, it shall show the runs list, each run's flow (activity, tasks, feed, agent now),
  plan detail and attempt detail from the laptop's data, refreshed within 5 s while the laptop is online.
- R5. When the owner sends a control command (pause, resume, cancel-attempt, reopen, retry, revise, approve, launch,
  answer round, cancel plan, delete plan, edit brief, note), the laptop shall apply it through the existing operations
  (`bt_scheduler_ops`, `bt_plans_api`, `bt_rounds`, plan approval/launch) and record it in a command ledger.
- R6. Every command shall carry an idempotency key and a precondition (expected state of its target); the laptop shall
  apply a key at most once and reject a command whose precondition no longer holds with `STALE_PRECONDITION`.
- R7. If the laptop does not answer three consecutive health probes (5 s apart), then the gateway shall mark it offline,
  serve the last cached state with its timestamp and reject commands with `LAPTOP_OFFLINE`; it shall never queue them.
- R8. Destructive commands (approve, launch, cancel plan, delete plan, revise) shall require a server-issued
  confirmation challenge answered by typing the target's REQ id within 120 s.
- R9. When a failed attempt is opened, the system shall show its classified cause (M5/M4 facts), the verification
  command and output, the changed files/diff stat and the last 200 lines of the agent log.
- R10. When any of these events occurs, the gateway shall send one Telegram message to the owner's `chat_id`: task
  failed with no retries left or blocked; run finished; question round or plan approval waiting; every account out of
  quota; attempt without signs of life for more than 10 min; laptop offline for more than 15 min with an active run.
- R11. Notification rules shall be deterministic functions of the event feed and gateway liveness state, with a stable
  dedupe key per event; a restart of the gateway or a re-read of the feed shall not resend a message.
- R12. Telegram messages shall carry inline buttons only for safe actions (ver, pausar, reanudar, reintentar) and the
  bot shall answer `/estado`; it shall ignore every chat except the configured `chat_id`.
- R13. The owner shall be able to retry a task pinned to another route/model/account, edit a task's brief or
  acceptance criteria (as a new plan revision approved by him), and leave a note that the next attempt's prompt includes.
- R14. The web shall be usable at 360 px width without horizontal scroll, with touch targets of at least 44 px, be
  installable as a PWA, use Catppuccin Mocha with the mauve accent and Spanish copy.
- R15. The web shall show live account quotas and a command history (command, target, time, origin web/telegram,
  result).
- R16. Secrets (GitHub client secret, Telegram token, gateway key, session key) shall live only in mode-600 env files on
  AdvIn/laptop and in Vercel env vars; never in git or the bitácora.
- R17. The gateway shall rate-limit sign-in attempts and commands per session, and log every request without secrets.
- R18. The local panel at `127.0.0.1:8765` shall keep its current behavior and tests.

## Edge cases & errors
- Laptop suspended mid-command: the gateway times out after 15 s and reports `UNKNOWN_OUTCOME` with the idempotency
  key; resending the same key is safe (R6).
- Tunnel up but panel restarting: health probe fails → offline after 15 s; recovers automatically.
- Two phones/tabs act on the same attempt: the second command fails its precondition.
- SSE through the Vercel rewrite is cut at 120 s: the client reconnects with `Last-Event-ID` and loses no events.
- Feed cursor lost on the gateway: the rebuilt cursor starts from now, with dedupe keys preventing resends.
- Telegram API down: messages are retried with backoff up to 1 h, then dropped and shown as "no entregado" in history.
- GitHub OAuth state mismatch or replay: refused.
- Disk on AdvIn at 85 %: the gateway's SQLite stays bounded (history pruned after 90 days, snapshots keep the latest).

## Constraints
- Laptop side: Python stdlib server (`bt_server`), existing modules; no new runtime dependencies there.
- Gateway: Python 3.12 on AdvIn host (systemd), managed with uv, ruff, pytest; behind the existing Caddy container.
- Frontend: Next.js 15 + React 19 + Tailwind 4 + TypeScript (same stack as `lotm-frontend`), Vercel team
  `dav033s-projects`, deployed with the CLI (no `git push`).
- Hostnames: `flow-api.185-147-157-25.sslip.io` (gateway, Caddy TLS) and a `*.vercel.app` frontend.
- Credentials referenced, never written (see PLAN.md §Keys).
- AdvIn: 8 cores, 15 GB RAM, disk 85 % used (24 GB free) on 2026-10-19.

## Priorities & phases
Must: R1–R12, R14, R16–R18 (US-1..US-4). Should: R13 (US-5, US-6). Could: R15 (US-7).
MVP = read + control + alerts; extended recovery and quotas follow in the same plan.

## Timeline & dependencies
- No deadline given.
- Owner prerequisites (batched, before deploy): Telegram bot token from @BotFather plus a `/start` to the bot; GitHub
  OAuth App (the agent can create it in the agents' Firefox if a GitHub session is there).

## Assumptions
- Vercel external rewrites forward cookies and stream SSE (with the 120 s cap); verified by a spike before building on it.
- The existing reverse tunnel (`advin-bitacora-tunnel.service`) stays the only path from AdvIn to the laptop.
- The scheduler can accept a per-task route pin and the executor prompt can include operator notes; a research task
  confirms the injection points before implementation.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear (no deadline) |

## Clarifications
### Round 1 — 2026-10-19
- Q: Where does execution run? → A: always on the laptop; AdvIn is control plane only.
- Q: Claude/Codex credentials on AdvIn? → A: AdvIn does not have them (moot).
- Q: Web login? → A: GitHub OAuth restricted to dav033 + extra confirmation for destructive actions.
- Q: Phone actions? → A: full control (view, control runs, approve/launch, rounds) and extend functionality.
- Q: Failure alerts? → A: Telegram bot.
### Round 2 — 2026-10-19
- Q: Laptop offline? → A: show last state with "sin conexión desde" and reject commands (no queue).
- Q: Domains? → A: vercel.app + sslip.io now; custom domain later.
- Q: Telegram scope? → A: alerts + buttons for safe actions + /estado.
- Q: New functions? → A: all six: retry on another route; edit brief before retry; failed attempt diff/verify/cause;
  note for next attempt; live quotas; command history.
- Q: Telegram events? → A: all six suggested, no quiet hours.
