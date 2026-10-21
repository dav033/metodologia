# Independent security and specification audit — T18

**Rework required: F2, F26, F28 and F32 are high and open.** The criterion “Confirmed high findings are fixed”
is not met. This read-only audit records the prerequisite tasks to redo; it changes no source, tests or configuration.

Audited tree: `697120c394c4f34b727267a1f223accbb2328b52` (HEAD at entry). Audit date: 2026-10-20, America/Bogota.
Primary auditor: OpenAI Codex. Independent other-provider review: see the provider receipt and dispositions below.

## Carried overlap, history and scope

Read both inherited audit files, the full SPEC/PLAN.md, every PLAN.json task's objective/acceptance/verification,
and the supplied #7–#12 outcomes before editing. Reviewed reachable att-0185 (`dcfc5a59`),
att-0198 (`13d914a6`), att-0201 (`15f1a318`), att-0202 (`088cefb3`) and att-0226
(`81a29c39`) reports. att-0181 was cancelled; omitted older attempts and raw m6 URI contents are unavailable.

Initial git status was clean. Neither requested document actually contained conflict markers. The overlap was stale
audit conclusions carried over 48 changed implementation/test/configuration files relative to att-0226. This report
reconciles both intents: retain every inherited F1–F27 identity, acknowledge and recheck prerequisite repairs, and
record remaining/new defects instead of overwriting working implementation. In particular, preserve the real shared
snapshot cache, reviewer history, installed dependencies, request adapters, event targets, provider redaction,
command-history normalizer, working strict web build and selected rejected-attempt review.

The ledger contains 32 findings: 11 rechecked fixed; 21 open (4 high, 14 medium, 3 low). None is accepted.
Historical att-0180 IDs differ: its F1 cursor repair remains in passing laptop/gateway tests; F2 inaccessible review
is repaired but recovery remains current F26; F3/F4 decisions/rounds are covered by current installed/relay tests;
F14 package omission is current fixed F24; F12 owner-shared rate limit remains current F27.
Only the report and findings ledger are deliverable edits. Notes remain here under the explicit read-only boundary.

Reviewed laptop key/private-listener isolation, OAuth/state/session/Origin/logging/throttling, ledger/dispatch and
recovery, shared snapshots/events/review, gateway cache/poll/SSE, Telegram rules/delivery/bot, actual phone consumers
versus mocks, packaging and deployment kit. All dynamic requests/state are synthetic and loopback. No live project
state, real browser profile, SSH host or deployed service was accessed; credential contents were not inspected. Deployment/go-live is outside
this task's frozen scope. Provider source review does not replace this auditor's own findings or runtime checks.

## Fresh command evidence

Python 3.14.7; Node 24.21.0. Target Python 3.12 was unavailable. Before testing, `cd remote/web && npm ci --offline`
installed 320 packages with exit 0; the lockfile is unchanged. No added check installs dependencies.
Python suites run in subprocesses with BITACORA_ROOT set to an empty temporary root before imports.
Wildcard unittest runs include the frozen per-file prerequisite checks; repeated plan commands share that execution.

| Command | Result |
|---|---|
| `cd remote/gateway && python -m unittest discover -s tests -p 'test_*.py'` | Exit 0; 41 tests, 14.161 s, including real-browser OAuth and owner-rate/relay regressions. |
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py'` | Exit 0; 52 tests, 11.770 s, including installed wheel/sdist and installed planning preconditions. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` | Exit 0; 25 tests, 1.996 s, including inherited-listener reload. |
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_page*.py'` | Exit 0; 43 tests, 11.444 s, local panel regression coverage. |
| `cd remote/web && npm run verify` | Exit 0; 67.612 s; lint/typecheck, all 12 tests (0 skipped/cancelled), production build. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 1; 1 test, 19.022 s. Actual production build succeeds; line 401 fails on empty events/cursor (F2). Later cancel/OAuth/offline/notification assertions are not reached by this run. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 0; 18 tests, 9.549 s; 1 explicit skip: Caddy executable unavailable. Includes separate browser cookie check. |
| `bash remote/deploy/deploy.sh --check` and `bash remote/deploy/rollback.sh --check` | Each exit 0: host-bridge topology / rollback unit. Use Bash, matching their shebang. |
| `python -m json.tool remote/contract/command.schema.json` and event-schema equivalent | Each exit 0; JSON syntax only. |
| `test -s remote/docs/route-pin.md`, architecture.md and contract.md equivalents | Each exit 0. |
| Report probes A–F below | Each exit 0; observations and boundaries recorded beside each probe. |
| `test -s remote/docs/audit.md` (all three frozen acceptance checks) | Each exit 0; existence only. |
| Ledger schema/IDs/verdict consistency; document conflict scan; `git diff --check` | Exit 0; only the two authorized documents changed. |

The first gateway/browser run used a TMPDIR beneath the long worktree path; Chromium aborted with “Socket path too long.”
That environment-induced attempt is not product evidence. Its web process group was stopped after 51.826 s, then both
suites were repeated with Chromium's normal short temporary directory, producing the complete passing results above.
Web verify, built-web E2E and deployment browser tests ran sequentially to avoid concurrent builds during this audit.
Some Python tests emit SQLite ResourceWarnings; none of those warnings is treated as a passing result or a new defect.

Not run: complete unrelated repository suites, Python 3.12 execution, real Caddy syntax validation, live Docker/VPS
connectivity, production OAuth/Telegram, Vercel rewrite lifetime/reconnect, PWA installation or exhaustive 44 px target
measurement. No live dependency advisory scan was performed; npm's offline advisory output is not such evidence.
These omissions are not claimed passing and do not hide the recorded E2E failure.

## Findings and verdicts

### F1 — high / fixed — Caddy used container loopback instead of the host Docker bridge upstream.

Tasks: `T16`. Evidence: cd remote/deploy && python -m unittest discover -s tests -p test_kit.py: exit 0, 18 tests in 9.549 s, one skip (Caddy binary unavailable); host-bridge structural assertions pass. bash remote/deploy/deploy.sh --check: exit 0, deployment topology: 172.20.0.1:8790. Unit and Caddyfile agree; actual Docker connectivity was not tested.

### F2 — high / open — The required built-web E2E still fails: its forced-failure fixture produces no failure event or notification.

Tasks: `T17`. Evidence: cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py: exit 1, one test in 19.022 s; production build passes, then line 401 fails because events=[], nextCursor=''. Report probe C reproduces the empty production feed. Both fixtures now ingest execution_started and cancel target_state is running; those earlier defects are corrected. The failure fixture has one attempt below max_attempts=3 and an M5 retry decision; alert suppression is correct.

### F3 — medium / open — The runbook restarts an uninstalled gateway unit on first install and reloads host Caddy although the approved service is containerized.

Tasks: `T16`. Evidence: remote/docs/runbook.md step 3 invokes deploy.sh, which runs systemctl restart bitacora-gateway; step 4 installs that unit afterward. Step 5 instructs sudo systemctl reload caddy, while the approved topology uses an existing Docker Caddy. Step 6 now documents the private laptop listener/key and tunnel, and step 5 explains placeholder replacement; those inherited subfindings are withdrawn.

### F4 — medium / open — Gateway request logging exposes OAuth code/state query values in its purported status field.

Tasks: `T11a`. Evidence: Report probe A: exit 0; requesting /api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE puts both synthetic values in the captured log. server.py make_handler.log_message reads args[0] (the full request line) as status.

### F5 — medium / open — The mutation marker accepts arbitrary nonempty values, and GET logout clears the cookie without guards or revoking its server session.

Tasks: `T11a`, `T15a`. Evidence: Report probe A: exit 0; authenticated command POST with X-Flow-Request: wrong returns 200; foreign-Origin GET logout returns 302 and a clearing session cookie. server.py uses bool(request_marker); page.tsx uses an ordinary logout link. The server-side session remains valid; the earlier report's claim that its row was removed is no longer true. Anthropic source review #9 independently confirms no server-side revocation call; probe A verifies the token still resolves after logout.

### F6 — medium / open — Telegram alerts still omit a working review URL and safe inline actions, and retry callbacks remain unsupported.

Tasks: `T14a`, `T14b`. Evidence: app.py submit_telegram_command permits pause/resume only; report probe B returns CommandValidationError for retry (the former NameError is fixed). telegram_bot.py /estado constructs only pause/resume callbacks. notifications.py sends chat_id/text only and renders generic message plus REQ, with no task/cause, review URL or reply_markup.

### F7 — medium / open — The public note command is still advertised and validated without a laptop dispatcher.

Tasks: `T5a`. Evidence: Report probe B confirms note is absent from bt_remote_commands.dispatch_handlers while both validators and command.schema.json advertise it. Ledger.submit refuses such a command with COMMAND_NOT_IMPLEMENTED. PLAN.md explicitly reuses retry reason/RUN.notes for operator notes; that working path is preserved, but it does not make the advertised standalone command executable.

### F8 — medium / open — The phone brief form still cannot edit acceptance criteria.

Tasks: `T15f`. Evidence: page.tsx editBriefForm always sends field='objective' and string value; renderTask has a brief textarea only. bt_remote_edit.dispatch_edit_brief supports acceptance_criteria lists. Failed/blocked task identity and run-state preconditions remain present; rejected-state recovery is F26.

### F9 — medium / open — Run-level Reabrir ejecución supplies no task identity to a task-scoped operation.

Tasks: `T15d`. Evidence: page.tsx run-level commandForm('reopen', kind:'run') has no taskId. bt_remote_commands.TASK_SCOPED includes reopen, _member_state requires params.task, and dispatch_run_command also explicitly requires it. The current path fails preconditions before reaching that dispatcher; task-level reopen is separately affected by F26.

### F10 — medium / fixed — Ordinary plans waiting for approval previously emitted no plan.waiting event without a scheduler decision.

Tasks: `T6`. Evidence: Report probe B (runnable Python block in audit.md): exit 0, build_events with a review plan and no decisions produces ['plan.waiting']. Current collect passes plans to build_events. cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py': exit 0, 52 tests in 11.770 s.

### F11 — medium / open — Gateway restart loses the last cached snapshot and restarts SSE IDs without a reset/resynchronization protocol.

Tasks: `T12`. Evidence: Report probe B: exit 0; a second GatewayRuntime with the same SQLite database has snapshot None, and a new stream's event 1 is invisible to after('1'). SnapshotEventStream is memory-only and server.py _stream_events provides no epoch/reset handshake.

### F12 — medium / open — Gateway event replay memory, delivered/dropped outbox history and abandoned expired sessions remain unbounded.

Tasks: `T11`, `T12`, `T14a`. Evidence: Report probe B: exit 0; stream deque.maxlen is None and creating a fresh session leaves one expired abandoned session row. notifications.py contains no 90-day deletion/pruning of telegram_outbox or telegram_delivery_history. SessionStore deletes an expired session only when that token is presented. Full laptop command ledgers are also loaded before endpoint slicing. Full server.py source also confirms no per-session concurrent SSE cap; this is a source-confirmed resource-bound aspect, not a demonstrated external denial of service.

### F13 — medium / open — The stable cachedAt repair remains, but no stable offline-start timestamp reaches the phone.

Tasks: `T12`, `T15b`. Evidence: Report probe B: exit 0; updating laptop status preserves cachedAt=2026-10-20T00:00:00Z and exposes only online/checkedAt. stream.py has no serialized offlineSince; page.tsx still says LAPTOP SIN CONEXIÓN without sin conexión desde HH:MM. Gateway suite passes the cache/liveness regressions.

### F14 — medium / fixed — Laptop-side redaction previously missed provider-key assignments and bearer authorization text before transmission.

Tasks: `T7`, `T6`. Evidence: Report probe B (runnable Python block in audit.md): exit 0; OPENAI_API_KEY=SYNTHETIC_KEY_123456789 Authorization: Bearer SYNTHETIC_BEARER_123456789 becomes OPENAI_API_KEY=[REDACTED] Authorization: [REDACTED]. bt_remote_events now covers provider names/token shapes recursively; snapshot/events/review use it. cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py': exit 0, 52 tests.

### F15 — medium / fixed — The local panel previously had no inherited systemd listener implementation.

Tasks: `T9`. Evidence: cd skill/scripts && python -m unittest discover -s tests -p test_platform.py: exit 0, 25 tests in 1.996 s, including test_web_server_reload_uses_the_inherited_listener and test_systemd_listener_requires_its_activation_environment. cd skill/scripts && python -m unittest discover -s tests -p 'test_page*.py': exit 0, 43 tests. No live service restart was performed.

### F16 — medium / open — The phone still discards unknown-outcome command envelopes and creates a fresh idempotency key on resubmission.

Tasks: `T15d`. Evidence: page.tsx sendCommand extracts message/status but retains no exact envelope or unknown-outcome key; commandForm/roundForm/decisionForm/retryTask/editBriefForm generate a new web UUID per submission. UNKNOWN_OUTCOME is treated as a generic rejection. Passing gateway and ledger tests prove server-side key preservation/replay, not client reconciliation.

### F17 — low / open — The public command schema still disagrees with production commands and key limits; event target normalization has been repaired.

Tasks: `T3`. Evidence: Report probe B: exit 0; gateway accepts a 121-character key and laptop validate rejects its 120 limit. command.schema.json omits answer-decision, specifies string route, requires singular answer, and models edit-brief as brief rather than task/field/value. Current events now use kind/project/req and event.schema.json admits system targets; the inherited event-target allegation is withdrawn.

### F18 — medium / fixed — The required browser verification previously failed and asserted obsolete singular round answers.

Tasks: `T15`, `T15e`. Evidence: cd remote/web && npm run verify: exit 0 in 67.612 s; lint/typecheck pass, all 12 tests pass (0 skipped/cancelled), production build succeeds. panel-browser.test.mjs now asserts answers and exercises the real {login} session dialect plus selected rejected-attempt review. The two dev tests still share .next, but this fresh run does not reproduce a race; shared output alone is not evidence of a current defect.

### F19 — high / fixed — The integrated phone app previously failed strict typing and production build due to overlapping implementations.

Tasks: `T15a`, `T15c`, `T15d`. Evidence: cd remote/web && npm run verify: exit 0 in 67.612 s; lint, tsc --noEmit, 12 tests and next build pass. The actual build also passes inside the T17 run before its independent fixture failure. page.tsx has one refreshCommandHistory; FailureReviewPanel owns review parsing and the invalid Attempt predicate is gone.

### F20 — high / fixed — The phone previously rejected the real gateway's successful {login:'dav033'} session response.

Tasks: `T15a`. Evidence: cd remote/web && npm run verify: exit 0; panel-browser.test.mjs overrides /api/auth/session with {login:'dav033'}, asserts that contract was observed and renders authenticated phone runs/review/actions. Report probe A independently confirms the real HTTP session is 200 {login:'dav033'}. page.tsx now handles that dialect.

### F21 — medium / open — The phone still opens an SSE route the production gateway does not serve and does not resume using its replay IDs.

Tasks: `T4a`, `T6`, `T15b`. Evidence: Report probe A: exit 0; authenticated GET /api/remote/v1/events/stream?after=abc returns 404. page.tsx opens that route/query; gateway server.py serves /api/remote/v1/events and parses numeric Last-Event-ID. Laptop snapshot cursor is now a nonempty timestamp and event targets now decode correctly, closing those inherited subdefects. Normal flow messages are still filtered by notification-only from_flow. Anthropic source review #8 also identifies that onerror only sets text and never recreates an EventSource after terminal CLOSED; the effect depends on a truthy cursor, not changing cursor values. This source-confirmed aspect is grouped here; no browser CLOSED recovery success is claimed. Snapshot cursors are ISO timestamps, while gateway replay IDs are integers, so cursor handover also needs an explicit adapter.

### F22 — medium / fixed — The earlier env-startup allegation assumed blank optional settings despite the current runbook requiring every uncommented key to be filled.

Tasks: `T16`. Evidence: Report probe B, final filled-all-keys case (runnable Python block in audit.md): exit 0; all gateway.env.example assignments receive synthetic/standard nonsecret settings as runbook step 2 requires, GatewayConfig.from_env and OAuthConfig.from_env both succeed with bind 172.20.0.1:8790. Blank numeric/endpoint assignments still fail, but leaving them blank is not following the current documented procedure. Deployment suite: exit 0, 18 tests, one Caddy skip. No live startup claim.

### F23 — medium / fixed — Overlapping phone command-history implementations previously broke compilation and mislabeled origin.

Tasks: `T15d`. Evidence: cd remote/web && npm run verify: exit 0, including browser history assertions; cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py': exit 0, including real read-model regression. page.tsx has one /commands normalizer that reads item.origin and keeps command, target, submittedAt and result; the incompatible /history reader is gone. Authenticated gateway read-model tests also pass in the 41-test suite.

### F24 — high / fixed — Installed planning-command preconditions previously failed because bt_remote_preconditions was absent from distributions.

Tasks: `T18.6`. Evidence: cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py': exit 0, 52 tests in 11.770 s, including test_installed_wheel_serves_remote_api_and_resolves_round_and_decision_preconditions. It builds wheel and sdist, checks all six remote modules, resolves both planning states in an isolated installed interpreter, and starts keyed installed serve_remote. pyproject.toml also includes new bt_remote_edit and bt_route_pins dependencies.

### F25 — medium / fixed — The failed-task link previously opened only an unrelated static review fixture.

Tasks: `T15c`. Evidence: cd remote/web && npm run verify: exit 0; panel browser navigates /review?project=lotm&req=REQ-027&taskId=T15c and renders the selected rejected task's fetched review; another rejected task review is also checked. page.tsx supplies project/req/taskId; review/page.tsx resolves reviewAttempt from authenticated snapshot and fetches its review. Fixture fallback stays explicitly labeled sample and unavailable responses show an error.

### F26 — high / open — Rejected failure review is now reachable, but authoritative rejected tasks still cannot be recovered from the phone.

Tasks: `T4a`, `T5`, `T15f`. Evidence: Report probe C: exit 0; real failed fixture snapshot exposes task state rejected and reviewAttempt, while target_state(reopen, T1) returns recovering. Submitting the exact phone precondition rejected to the real ledger returns STALE_PRECONDITION without invoking a handler. The web's reopen button is now visible, but retry/edit forms and inline review still allow failed/blocked (inline review: failed only). The separate rejected review route works and is not reported broken.

### F27 — low / open — Command rate limits remain shared by owner login across sessions rather than per session as R17 specifies.

Tasks: `T11a`. Evidence: cd remote/gateway && python -m unittest discover -s tests -p 'test_*.py': exit 0, 41 tests in 14.161 s, including test_command_quota_is_shared_by_owner_across_sessions. server.py keys command/challenge quotas by login. This stricter aggregate cap is not an authentication bypass; no owner-approved per-session specification amendment is evidenced.

### F28 — high / open — The command ledger checks preconditions before its effect lock and accepts a second concurrently stale command.

Tasks: `T5`. Evidence: Report probe D: exit 0; two threads use distinct keys and barrier-synchronized state reads against the real Ledger.submit. Effect handler entry states are ['running','paused']; both results are OK and two rows are committed despite both requests pinning running. submit reads state before its second _LOCK and never rechecks inside it. This proves the ledger race, not a claimed duplicate production launch.

### F29 — medium / open — Production snapshots omit the timestamp fields the phone uses for last signal of life and discard plan detail/revision metadata.

Tasks: `T4a`. Evidence: Report probe C: exit 0; real snapshot has lastActivityAt but lastSeenAt and updatedAt are None. page.tsx parses lastSeenAt/updatedAt and attempt.updatedAt (production _attempt emits last_activity_at), so it renders Sin actividad registrada for real signals. bt_remote_api._snapshot also constructs plan rows with tasks=[] and no revision/criteria, and run/task rows omit revision. The browser mock supplies these fields and cannot establish the real contract.

### F30 — medium / open — Stalled-attempt notifications start after 15 minutes although the specification requires more than 10 minutes.

Tasks: `T6`. Evidence: Report probe B: exit 0; a live attempt with a fixed last_activity_at produces no attempt.stalled event at +660 seconds and does produce one at +901 seconds. bt_remote_events.STALL_SECONDS is 15*60; SPEC R10 requires more than 10 minutes. notifications.py's message still promises 10 minutes.

### F31 — low / open — An already authenticated SSE connection continues to deliver after the session expires.

Tasks: `T11`, `T12`. Evidence: Anthropic source review #10, independently rechecked in full remote/gateway/server.py: session validation occurs only before _stream_events; its unbounded wait/write loop never calls SessionStore.get_session again. Report probe E: expire the synthetic session row after the stream opens, publish an event, and observe HTTP 200 delivery while get_session returns None. No anonymous-stream authorization bypass is claimed.

### F32 — high / open — Every phone pinned-retry command is rejected because the gateway forwards a route object to a laptop validator requiring string selectors.

Tasks: `T13`. Evidence: Report probe F: exit 0; the exact page.tsx retryTask envelope passes GatewayRuntime.submit_command and real LaptopClient/HTTP route_post, then returns 400 INVALID_COMMAND before target state or effects. app.py copies route unchanged into params; bt_remote_commands.validate requires params.route/model/account to be strings, as bt_route_pins.normalize expects. The browser mock accepts the object; isolated laptop pin tests use strings. Adapt the boundary while preserving route id, model and account.


## Independent other-provider review and dispositions

Anthropic Claude completed a separate, source-only boundary review with no tools or write access. It received frozen
requirements and numbered excerpts of actual ledger, HTTP, stream, snapshot, phone, event and notification code,
without the inherited report, ledger or this auditor's conclusions. This is a different provider from the primary
OpenAI auditor; it is not proof that every historical prerequisite was authored by a different provider.
Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format stream-json --verbose`,
with the source bundle on stdin. Receipt: exit 0; subtype success; is_error false; one turn; 92,567 ms provider duration
(93.876 s wall time); reported model `claude-sonnet-5-5`. Final-result SHA-256:
`c4f441b7462a8c4976f16c7d9d588a117caa9a18982d9db6358dba5dcd2a2572`.
An earlier whole-source request was stopped at its 240 s supervisor limit without a result; it supplies no verdict.
The completed review covers the supplied boundaries only; the primary auditor separately inspected full implementations,
fixtures, packaging and deployment. No independent passing tests are inferred from the provider's source review.
Its 12 findings all receive a disposition here:

| Provider finding | Primary auditor's disposition |
|---|---|
| 1 high: precondition race | Confirmed, F28, reproduced by D. Corrected subclaim: the full method **does** hold its process lock through the handler. The read/check still happens before that lock, so the reproduced race stands. No double production launch was proved. |
| 2 medium: request-line secret logging | Confirmed F4; A captures synthetic code/state. |
| 3 medium: 15-minute stall threshold | Confirmed F30; B checks 660/901 s. |
| 4 medium: Telegram actions/links absent | Confirmed F6. “View” should be a safe URL; no new review mutation command is required. |
| 5 medium: missing signal timestamp | Confirmed F29; C checks the actual producer's fields. |
| 6 medium: missing outage timestamp | Confirmed F13. The last cached snapshot is served during an in-process outage; reject an implication that it is always lost then. Runtime immediately reapplies laptop status after a successful snapshot refresh; no separate incorrect-online defect was reproduced. |
| 7 medium: restart replay/cursor mismatch | Confirmed F11/F21; B and actual routing/source show it. |
| 8 low-medium: terminal EventSource never recreated | Confirmed source behavior under F21; no runtime reconnection success is claimed. |
| 9 medium: GET logout/no revoke | Confirmed F5; A also shows the old token remains valid. SameSite limits cross-site cookie delivery; no authenticated command bypass is claimed. |
| 10 low: open stream ignores expiry/no bounds | Confirmed expiry F31 with E; unbounded replay/no session stream cap recorded in F12. No anonymous-stream bypass or external DoS was demonstrated. |
| 11 low-medium: missing revision/plan metadata | Confirmed F29; full snapshot source discards it. |
| 12 low: rejected task lacks retry/inline review | Confirmed remaining form guards within F26. Reject “review unavailable” as a general claim: selected review route works. Primary C additionally proves reopen fails on the rejected/recovering mismatch, justifying high severity for recovery. |

The provider declined to confirm several candidates because its excerpts omitted collaborators. Full-source adjudication:
empty preconditions and malformed confirmation objects are rejected by validate; production target_state has the required
three-argument signature; commandForm uses fresh UUIDs (which instead causes F16); upstream read_model is allowlisted.
Speculative exception leaks, proxy-throttle degradation or blocked-event identity collisions are not recorded without
a concrete cross-boundary reproduction. Actual dav033/state/cookie enforcement has passing full backend/browser tests.
The provider's missing-excerpt observation about POST guards is not a finding; A independently checks the real guard.

## Rejected or superseded inherited candidates

| Candidate | Verdict and reason |
|---|---|
| Container-loopback Caddy upstream | Fixed F1: host bridge/unit agree; public connectivity still untested. |
| No private listener/key/tunnel instructions | Withdrawn: runbook step 6 now supplies them. F3 concerns first-install order/container reload. |
| Blank optional example fields necessarily break a compliant install | Superseded F22: runbook requires filling every uncommented key; both fully filled configurations validate in B. |
| Web cannot compile or consume the real session dialect | Fixed F19/F20 with fresh complete verify and actual {login} browser contract. |
| Missing installed preconditions dependency | Fixed F24 by wheel/sdist plus isolated installed state-reader test. |
| Rejected attempt has no accessible review | Fixed review projection/link, F25; rejected recovery remains high F26. |
| Generic provider/bearer redaction absent | Fixed F14; B removes both synthetic values before transmission. No exhaustive secret-detection claim. |
| Required default browser tests still fail / singular answer assertion remains | Fixed F18 with 12/12 and updated answers assertion. Shared .next alone does not prove a current race. |
| Callback state cookie must be Strict | Rejected: Lax enables the cross-site top-level callback; state is bound and one-use; actual session is Strict. |
| Tunnel exposes unauthenticated laptop panel | Rejected: remote-only 8766 destination, keyed listener and route-denial tests pass; 8765 remains separate. |
| edit-brief has no destructive confirmation / same-key replay runs twice | Rejected for tested paths: laptop CHALLENGED includes edit-brief; one-use/target-bound challenge and replay/conflict tests pass. F28 is a distinct concurrent-key race. |
| T17 still reserves its supposedly running cancellation fixture | Withdrawn: C sees running after execution_started. The complete test still fails earlier on its notification fixture (F2). |

## Handoff

Return F2 to T17; F26 to T4a/T5/T15f; F28 to T5; F32 to T13. Keep every other open item recorded until a
prerequisite repair or explicit owner acceptance. No risk was accepted here. Fix the genuine exhausted-failure fixture
rather than weakening retry-budget alert suppression. Re-run built-web E2E, phone-to-real-laptop pinned retry,
authoritative rejected recovery, and concurrent-key preconditions after changes; keep the working packaging, review,
web/session/history, redaction and local listener regressions. Final acceptance remains with the independent checker.

## Reproduction probes

Run each block from the repository root. They use synthetic inputs and temporary state, and do not start agents.
Probe assertions reproduce defects; a successful probe is evidence of the stated observation, not acceptance.

### Probe A — real gateway HTTP boundaries

```bash
python - <<'PY'
import http.client, io, json, logging, pathlib, sys, tempfile, threading
from http.server import ThreadingHTTPServer
root = pathlib.Path.cwd()
sys.path.insert(0, str(root / "remote/gateway"))
from auth import OAuthConfig, OAuthService, SessionStore
from server import make_handler
class Runtime:
    def submit_command(self, value): return 200, {"status": "OK"}
with tempfile.TemporaryDirectory() as tmp:
    db = str(pathlib.Path(tmp) / "sessions.db")
    secret = "synthetic-secret-at-least-32-characters"
    store = SessionStore(db, secret)
    service = OAuthService(OAuthConfig("synthetic", "synthetic", secret,
                                      "https://frontend.test", db), store)
    token = store.create_session("dav033")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service, Runtime()))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    capture = io.StringIO(); sink = logging.StreamHandler(capture)
    log = logging.getLogger("server"); log.addHandler(sink); log.setLevel(logging.INFO)
    def request(method, path, headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        connection.request(method, path, body, headers or {})
        response = connection.getresponse()
        value = response.status, response.read().decode(), response.getheader("Set-Cookie")
        connection.close(); return value
    try:
        cookie = {"Cookie": "flow_session=" + token}
        print("session", request("GET", "/api/auth/session", cookie)[:2])
        print("wrong marker", request("POST", "/api/remote/v1/commands",
              {**cookie, "Origin": "https://frontend.test", "X-Flow-Request": "wrong",
               "Content-Type": "application/json"}, "{}")[:2])
        print("foreign logout", request("GET", "/api/auth/logout",
              {**cookie, "Origin": "https://foreign.test"})[::2])
        print("session retained after logout", store.get_session(token) is not None)
        print("phone SSE route", request("GET", "/api/remote/v1/events/stream?after=abc", cookie)[:2])
        request("GET", "/api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE")
        print("logged query", "code=SYNTHETIC_CODE&state=SYNTHETIC_STATE" in capture.getvalue())
    finally:
        server.shutdown(); server.server_close(); thread.join(); log.removeHandler(sink)
PY
```

Observed: session 200 with login; wrong marker 200; foreign logout 302 with clearing cookie; SSE 404; logged query True.
The synthetic runtime isolates the header guard; session, HTTP routing, cookie mutation and logging are real.

### Probe B — restart, retention, redaction, schemas, configuration and notification timing

```bash
python - <<'PY'
import os, pathlib, sqlite3, sys, tempfile
from datetime import datetime
from unittest.mock import patch
root = pathlib.Path.cwd()
sys.path[:0] = [str(root / "remote/gateway"), str(root / "skill/scripts")]
with tempfile.TemporaryDirectory() as tmp:
    os.environ["BITACORA_ROOT"] = tmp
    import bt_remote_commands as commands, bt_remote_events as feed
    from app import GatewayRuntime
    from auth import OAuthConfig, SessionStore
    from commands import validate_command
    from config import GatewayConfig
    from stream import SnapshotEventStream
    cfg = GatewayConfig("http://127.0.0.1:1", "synthetic-gateway-key", "synthetic-token",
                        "synthetic-chat", pathlib.Path(tmp) / "gateway.db")
    runtime = GatewayRuntime(cfg, laptop=object(), sender=lambda _: None)
    runtime.stream.update_snapshot({"runs": []}, "2026-10-20T00:00:00Z")
    runtime._update_laptop_status()
    print("cache", runtime.stream.snapshot())
    again = GatewayRuntime(cfg, laptop=object(), sender=lambda _: None)
    print("restart snapshot", again.stream.snapshot())
    stream = SnapshotEventStream(); stream.publish([{"id": "new"}])
    print("restart replay", stream.after("1"), "maxlen", stream._events.maxlen)
    store = SessionStore(str(pathlib.Path(tmp) / "sessions.db"), "synthetic-secret-32-characters-long")
    store.create_session("dav033", now=1); store.create_session("dav033")
    with sqlite3.connect(store.database_path) as db:
        print("abandoned expired sessions",
              db.execute("SELECT COUNT(*) FROM sessions WHERE expires_at < 10000000").fetchone()[0])
    print("redacted", feed.redact("OPENAI_API_KEY=SYNTHETIC_KEY_123456789 "
                                  "Authorization: Bearer SYNTHETIC_BEARER_123456789"))
    print("waiting plan", [e["type"] for e in feed.build_events({"plans": [
          {"project": "demo", "req_id": "REQ-001", "plan_status": "review"}]})])
    web = {"schemaVersion": 1, "idempotencyKey": "a" * 121, "type": "pause",
           "target": {"kind": "run", "project": "demo", "req": "REQ-001"},
           "precondition": {"state": "running"}}
    validate_command(web)
    envelope = {"idempotency_key": "a" * 121, "command": "pause", "target": "demo/REQ-001",
                "origin": "web", "params": {}, "precondition": {"state": "running"}}
    print("long key laptop validation", commands.validate(envelope))
    note = {**envelope, "idempotency_key": "synthetic-note-command", "command": "note",
            "params": {"note": "synthetic"}}
    print("note result", commands.Ledger(pathlib.Path(tmp) / "ledger.db").submit(
          note, commands.dispatch_handlers(), lambda _: {"state": "running"})["code"])
    with patch.object(commands, "_run_target", return_value=("demo", "REQ-001", pathlib.Path(tmp))):
        try: commands.dispatch_run_command("reopen", "demo/REQ-001", {})
        except ValueError as error: print("run reopen", str(error))
    try: runtime.submit_telegram_command({**web, "idempotencyKey": "synthetic-retry-key", "type": "retry"})
    except Exception as error: print("Telegram retry", type(error).__name__, str(error))
    values = dict(line.split("=", 1) for line in
                  (root / "remote/deploy/gateway.env.example").read_text().splitlines()
                  if line and not line.startswith("#"))
    values.update(LAPTOP_ORIGIN="http://127.0.0.1:18765", FLOW_GATEWAY_KEY="synthetic-key-123456789012345",
        TELEGRAM_BOT_TOKEN="synthetic", TELEGRAM_CHAT_ID="synthetic", GATEWAY_DATABASE=str(pathlib.Path(tmp)/"env.db"),
        GATEWAY_BIND="172.20.0.1", GITHUB_CLIENT_ID="synthetic", GITHUB_CLIENT_SECRET="synthetic",
        SESSION_SECRET="synthetic-secret-32-characters-long", FLOW_FRONTEND_ORIGIN="https://frontend.test")
    try: GatewayConfig.from_env(values)
    except ValueError as error: print("env error", str(error))
    values.update(GATEWAY_PORT="8790", UPSTREAM_TIMEOUT="5", PROBE_INTERVAL="5")
    try: OAuthConfig.from_env(values)
    except ValueError as error: print("OAuth env error", str(error))
    values.update(GITHUB_AUTHORIZE_URL="https://github.com/login/oauth/authorize",
                  GITHUB_TOKEN_URL="https://github.com/login/oauth/access_token",
                  GITHUB_USER_URL="https://api.github.com/user")
    assert all(values.values())
    print("fully filled example valid", GatewayConfig.from_env(values).bind_host,
          OAuthConfig.from_env(values).bind_port)
    stamp = "2026-10-20T00:00:00Z"; epoch = datetime.fromisoformat(stamp).timestamp()
    state = {"runs": [{"project": "demo", "req_id": "REQ-001", "tasks": [{"id": "T1",
             "attempt": {"id": "a", "live": True, "last_activity_at": stamp}}]}]}
    for elapsed in (660, 901):
        print("stall", elapsed, [e["type"] for e in feed.build_events(state, now=epoch+elapsed)])
    runtime.outbox._db.close(); again.outbox._db.close()
PY
```

Observed: cachedAt preserved, no offlineSince; restarted snapshot None; replay [] with unbounded deque; one expired row;
provider key and bearer redacted; plan.waiting emitted; long key rejected only by laptop; note COMMAND_NOT_IMPLEMENTED;
run reopen requires task; Telegram retry rejected with CommandValidationError; numeric and OAuth endpoint errors for incomplete values, but fully filled documented example validates;
no stalled event at 660 s, one at 901 s.

### Probe C — current real scheduler fixtures through the production laptop projection and ledger

```bash
python - <<'PY'
import json, os, pathlib, sys, tempfile
from unittest.mock import patch
root = pathlib.Path.cwd()
sys.path[:0] = [str(root / "remote/e2e/tests"), str(root / "skill/scripts")]
from test_local_e2e import LocalEndToEndTests as Fixture
with tempfile.TemporaryDirectory() as tmp:
    Fixture.root = pathlib.Path(tmp) / "bitacora"; Fixture.root.mkdir()
    os.environ["BITACORA_ROOT"] = str(Fixture.root)
    os.environ["FLOW_GATEWAY_KEY"] = "synthetic-audit-key"
    Fixture._seed_retry_event_fixture(); Fixture._seed_cancel_run_fixture()
    import bt_remote_api as api, bt_remote_commands as commands, bt_subscriptions
    class Handler:
        headers = {"Authorization": "Bearer synthetic-audit-key"}
        def send(self, payload, status=200, *args): self.result = status, json.loads(payload)
    handler = Handler()
    with patch.object(bt_subscriptions, "summary", return_value=[]):
        handler.path = "/api/remote/v1/snapshot"; api.route_get(handler)
        status, snapshot = handler.result; print("snapshot status", status)
        failed_run = next(r for r in snapshot["runs"] if r["req"] == "REQ-001")
        task = failed_run["tasks"][0]
        print("task", task["state"], "review attempt", task["reviewAttempt"]["id"])
        handler.path = "/api/remote/v1/events?limit=100"; api.route_get(handler)
        print("production events", handler.result)
        print("cancel state", commands.target_state("demo/REQ-002", "cancel-attempt", {"attempt": "att-0001"}))
        print("reopen current state", commands.target_state("demo/REQ-001", "reopen", {"task": "T1"}))
        def must_not_run(*args): raise AssertionError("unexpected effect")
        result = commands.Ledger(pathlib.Path(tmp) / "ledger.db").submit(
            {"idempotency_key": "synthetic-reopen-key", "command": "reopen", "target": "demo/REQ-001",
             "origin": "web", "params": {"task": "T1"}, "precondition": {"state": task["state"]}},
            {"reopen": must_not_run}, commands.target_state)
        print("phone reopen", result)
        print("signal fields", {key: failed_run.get(key) for key in ("lastActivityAt", "lastSeenAt", "updatedAt")})
PY
```

Observed: rejected task with reviewAttempt; empty events/cursor; cancel state running; reopen current state recovering;
phone reopen STALE_PRECONDITION; only lastActivityAt is supplied. Only quota sampling is stubbed; fixtures, read models,
projection/state reader, SQLite ledger and command precondition evaluation are real. This does not replace the failing E2E.

### Probe D — concurrent precondition enforcement in the actual ledger

```bash
python - <<'PY'
import pathlib, sys, tempfile, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path("skill/scripts").resolve()))
from bt_remote_commands import Ledger
with tempfile.TemporaryDirectory() as tmp:
    ledger = Ledger(pathlib.Path(tmp) / "ledger.db")
    barrier = threading.Barrier(2); state = {"state": "running"}; effects = []
    def read(*args):
        observed = dict(state); barrier.wait(timeout=5); return observed
    def effect(target, params):
        effects.append(state["state"]); state["state"] = "paused"; return {"changed": True}
    def send(number):
        return ledger.submit(
            {"idempotency_key": f"audit-race-command-{number}", "command": "pause", "target": "demo/REQ-001",
             "origin": "web", "params": {}, "precondition": {"state": "running"}},
            {"pause": effect}, read)
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(send, [1, 2]))
    print("effect entry states", effects)
    print("results", [(item["status"], item.get("code")) for item in results])
    print("rows", len(ledger.rows()))
    assert effects == ["running", "paused"] and all(item["status"] == "OK" for item in results)
PY
```

Observed: effects enter running then paused; both requests return OK; two rows committed. The barrier controls scheduling
at the real ledger's state-reader seam. It demonstrates stale authorization at effect time; it does not claim a double
production launch. Move/recheck preconditions within the same serialization boundary as the mutation, including scheduler races.

### Probe E — SSE authorization after session expiry

```bash
python - <<'PY'
import http.client, pathlib, sqlite3, sys, tempfile, threading
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
sys.path.insert(0, str(pathlib.Path("remote/gateway").resolve()))
from auth import OAuthConfig, OAuthService, SessionStore
from server import make_handler
from stream import SnapshotEventStream
with tempfile.TemporaryDirectory() as tmp:
    db = str(pathlib.Path(tmp) / "sessions.db")
    secret = "synthetic-secret-at-least-32-characters"
    store = SessionStore(db, secret); token = store.create_session("dav033")
    service = OAuthService(OAuthConfig("synthetic", "synthetic", secret, "https://frontend.test", db), store)
    runtime = SimpleNamespace(stream=SnapshotEventStream())
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service, runtime))
    server.daemon_threads = True
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    try:
        connection.request("GET", "/api/remote/v1/events", headers={"Cookie": "flow_session=" + token})
        response = connection.getresponse()
        assert response.status == 200
        with sqlite3.connect(db) as database: database.execute("UPDATE sessions SET expires_at=0")
        assert store.get_session(token) is None
        runtime.stream.publish([{"id": "synthetic-after-expiry"}])
        first, second = response.readline().decode().strip(), response.readline().decode().strip()
        print("session invalid; stream delivers", response.status, first, second)
        assert "synthetic-after-expiry" in second
    finally:
        connection.close(); server.shutdown(); server.server_close(); worker.join()
PY
```

Observed: expired session rejected by SessionStore, but the previously open stream delivers event 1 with HTTP 200.
This is post-expiry continuation, not an unkeyed/anonymous stream.

### Probe F — the phone's pinned retry through the real gateway adapter and laptop HTTP handler

```bash
python - <<'PY'
import os, pathlib, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
root = pathlib.Path.cwd()
sys.path[:0] = [str(root / "remote/gateway"), str(root / "skill/scripts")]
with tempfile.TemporaryDirectory() as tmp:
    os.environ["BITACORA_ROOT"] = tmp; os.environ["FLOW_GATEWAY_KEY"] = "synthetic-audit-key"
    import bt_remote_api
    from app import CommandRelayError, GatewayRuntime
    from config import GatewayConfig
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def send(self, body, status=200, content_type="application/json"):
            body = body.encode(); self.send_response(status)
            self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        def do_POST(self): bt_remote_api.route_post(self)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    runtime = GatewayRuntime(GatewayConfig(f"http://127.0.0.1:{server.server_port}",
        "synthetic-audit-key", "synthetic", "synthetic", pathlib.Path(tmp)/"gateway.db"), sender=lambda _: None)
    try:
        runtime.submit_command({"schemaVersion": 1, "idempotencyKey": "synthetic-pinned-retry",
            "type": "retry", "target": {"kind": "task", "project": "demo", "req": "REQ-001", "taskId": "T1"},
            "precondition": {"state": "failed"},
            "route": {"route_id": "synthetic-route", "provider": "codex", "model": "synthetic", "account": "synthetic"}})
        raise AssertionError("Expected current laptop validation to reject the unadapted route object")
    except CommandRelayError as error:
        print("phone pinned retry", error.status, error.code)
        assert (error.status, error.code) == (400, "INVALID_COMMAND")
    finally:
        server.shutdown(); server.server_close(); worker.join(); runtime.outbox._db.close()
PY
```

Observed: 400 INVALID_COMMAND. The gateway forwards params.route as an object, while laptop validate and bt_route_pins
require route/model/account string selectors. Rejection precedes state reading or effects, so it is independent of F26.
