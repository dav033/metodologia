# Independent security and specification audit — T18

Audited tree: `13d914a6c446b3d350a2d2b0883bd9470d165905` (HEAD and preserved snapshot at the start of this retry).
Auditor: Codex / OpenAI. Date: 2026-10-20. Provider diversity must be established by the scheduler's assignment metadata; commit authors do not establish it.

**Disposition: rework required.** This review confirms 18 findings: two high, fifteen medium and one low. All remain `open` in `audit.findings.json`. No risk has been accepted and no finding is claimed fixed. The audit changes only this report and the ledger. In accordance with the task's read-only rule, the high findings are recorded for rework, not repaired here. The nonempty-report checks do not establish that the implementation meets the specification.

## Retry provenance and acceptance boundary

This retry started at the exact preserved snapshot named in the task, with `git status --short` and
`git diff --stat` empty. `git diff dcfc5a59 HEAD --name-only` and `git diff 0ba9b657 HEAD --name-only` each list
only these two audit artifacts. The supplied implementation therefore has no dependency remediation relative to
the previous report's audited tree. The instruction that a dependency was redone is not evidence that its fix is
present here; no other branch, worktree or private attempt state was inspected.

The complete SPEC, PLAN.md (including global constraints and integration verification), every PLAN.json task's
objective/acceptance/verification, and the current task's stricter read-only ledger instructions were reread.
The previous output is unaccepted: useful probes and findings are retained only after fresh execution and source
review. F1–F17 are reconfirmed. F17 now also records event-schema incompatibilities, and F18 records independently
observed browser-test isolation/cleanup defects. No earlier test result is counted as a current pass.

The three artifact-existence commands pass. The substantive criterion **"Confirmed high findings are fixed" is
not met**: F1/T16 and F2/T17 remain open. The read-only audit must return these tasks for correction. Provider
diversity and final task acceptance remain for the independent scheduler/checker; this report cannot certify them.

## Scope and method

Reviewed REQ-027 `SPEC.md`, approved `PLAN.md`/`PLAN.json`, the API contracts, laptop remote listener/commands/events/read models, gateway authentication/relay/cache/notifications/bot, web interactions, deployment kit and local end-to-end harness. Compared production call paths across components, ran existing checks, and exercised additional cases with synthetic data. Other auditors' findings were not used as coverage or substituted for this review.

No production host, real OAuth provider, real Telegram chat, credential file or other worktree was accessed. Tests use their own fixtures; the integration harness's incomplete isolation is discussed in F2. All laptop/gateway/platform/page test subprocesses and reproduction probes ran with `BITACORA_ROOT` pointing at a new empty temporary directory inside this worktree, preventing reads of the owner's live bitácora. No live deployment, hosted Vercel rewrite or real Docker/Caddy connectivity was tested. Python here is 3.14.7 and Node is 24.21.0; the gateway target is Python 3.12. Dependency installation completed with `cd remote/web && npm ci --offline` (320 packages; lockfile unchanged). Its cached advisory output is not a current vulnerability assessment.

## Executed checks

| Command (from repository root) | Observed result |
|---|---|
| `cd remote/gateway && python -m unittest discover -s tests -p 'test_*.py'` | Exit 0; 42 tests in 14.310 s. Resource warning about an unclosed SQLite connection. |
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py'` | Exit 0; 55 tests in 8.730 s. Resource warnings about unclosed SQLite connections. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` | Exit 0; 23 tests in 1.999 s. |
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_page*.py'` | Exit 0; 43 tests in 11.420 s, including local plans/flow pages. |
| `cd remote/web && npm run verify` | Exit 1; lint/typecheck passed with two hook warnings at `page.tsx:260`. Browser test timed out at 60 s: eight passed, one cancelled; build stage was not reached. See F18. |
| `cd remote/web && node --test --test-concurrency=1 tests/*.test.mjs` | Exit 0; nine tests in 23.862 s, including real Chromium OAuth and 360 px panel scenarios. Diagnostic serialization only; the tracked verify command remains unchanged. |
| `cd remote/web && npm run build` | Exit 0; production build, same two hook warnings. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 0; 12 tests in 6.363 s, one skipped: Caddy binary unavailable. Browser OAuth test ran. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` (temporary `BITACORA_ROOT`; runner below) | Exit 1; one test failed in 36.867 s at line 294: `AssertionError: forced failure did not reach the fake Telegram before its deadline`. Offline assertions later in that test were not reached. See F2. |
| Report probes A–D below | Each exit 0; reproduced the stated defects using synthetic data, loopback HTTP and temporary databases. A probe exit 0 is reproduction evidence, not a product pass. |
| `python -m json.tool remote/contract/command.schema.json` | Exit 0; JSON syntax only, not wire compatibility (F17). |
| `test -s remote/docs/audit.md` | Exit 0 for each of the task's three identical acceptance commands. |

The web, kit and integration invocations were sequential; no separate audit command ran another Next.js server
concurrently with them. The default web test runner itself launches two browser test files concurrently against
one `.next` directory. After its panel timeout, cleanup stalled waiting for its own Next.js child to close; the
auditor sent SIGTERM to that child only, allowing the command to finish with exit 1 (test duration 97.816 s).
The subsequent serial run passed without source changes. It does not turn the original verify command into a pass.
The E2E command's build and standalone browser teardown completed; its forced-notification assertion failed.

Real `caddy validate`, Docker/container networking, Python 3.12, the entire legacy suite and live production checks
were not run. Caddy is not installed. No runtime authentication bypass or production credential exposure is claimed.

The E2E command was run from `remote/e2e` using this environment-isolation wrapper (it installs nothing when the
already installed dependencies are present):

```bash
python - <<'PY'
import os, subprocess, tempfile
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='.audit-e2e-', dir='.') as root:
    env = {**os.environ, 'BITACORA_ROOT': str(Path(root).resolve())}
    result = subprocess.run(['python', '-m', 'unittest', 'discover', '-s', 'tests',
                             '-p', 'test_local_e2e.py'], env=env)
    raise SystemExit(result.returncode)
PY
```

## Confirmed findings and verdicts

### F1 — High / open — Caddy cannot reach the host gateway in the approved topology

Tasks: **T16**. Requirements: R1, R3, R4; approved PLAN §Approach.

The plan explicitly places Caddy in the existing Docker container and the host gateway at `172.20.0.1:8790`. `remote/deploy/Caddyfile:11` instead proxies `127.0.0.1:8790`, and `remote/gateway/config.py`/`auth.py` default the gateway bind to host loopback. The env example lists an optional blank `GATEWAY_BIND` override, but gives no bridge address; the runbook supplies neither the bridge-bind setup nor container host networking. Overriding the gateway bind alone would still leave the Caddy upstream wrong. In the approved topology that Caddy upstream is the container itself, so login and every API request fail. The kit test even asserts this incorrect upstream.

Evidence: source inspection against `PLAN.md:74`; `rg -n 'reverse_proxy|bind_host|GATEWAY_BIND' remote/deploy/Caddyfile remote/gateway/config.py remote/gateway/auth.py remote/deploy/gateway.env.example`. No live Docker inspection is claimed. **Required correction:** make the gateway bind, Caddy upstream and runbook consistent with the approved container-to-host topology; preserve a private gateway listener. Exercise the actual network boundary rather than asserting a configuration string.

### F2 — High / open — The required end-to-end notification scenario fails

Tasks: **T17**. Requirements: R10, R11; T17 acceptance.

The T17 unittest command, with an isolated empty bitácora root, fails at `_wait_for_telegram(1, timeout=5)`. The fixture patches `_snapshot_runs` and `_plans`, but not `_runs`, which the real `/events` handler separately reads for retry context. Its synthetic `demo/REQ-001/T1` failure therefore does not have a matching authoritative exhausted-retry task in a clean fixture tree; `bt_remote_events.from_flow(row, {})` returns `None`. The harness itself also fails to provide an isolated bitácora root for this production read. Existing web tests send commands to a mock and do not close this coverage gap. The harness contains no real-ledger cancel-attempt or stale-precondition scenario, although PLAN §Verification explicitly requires both; passing mock web submissions would not establish either.

Evidence: executed command/result above; `remote/e2e/tests/test_local_e2e.py:146`, `skill/scripts/bt_remote_api.py:331`, and probe B below. With empty context, the real production-shaped failure is suppressed; with explicit exhausted-task context, it becomes `attempt.failed`. **Required correction:** isolate all read models, seed real retry context for the synthetic task, and exercise the required real-ledger command/stale scenarios; rerun the complete integration command, retaining the once-only Telegram assertion. Do not disable retry suppression to make the fixture pass.

### F3 — Medium / open — First-time go-live instructions cannot bootstrap the services

Tasks: **T16**. Requirements: R3, R7; kit operability.

Runbook step 3 invokes `deploy.sh`, which unconditionally executes `systemctl restart bitacora-gateway` at line 27. Step 4 only then installs the unit. On a first deployment, step 3 exits unsuccessfully because the unit does not exist. Separately, step 6 starts the SSH tunnel to laptop port 8766 without installing/starting `serve-remote` or configuring its `FLOW_GATEWAY_KEY`. The tunnel alone does not create that API listener. No laptop listener service or equivalent startup instruction appears in this kit.

Evidence: `remote/docs/runbook.md` steps 3, 4 and 6; `remote/deploy/deploy.sh:27`; `skill/scripts/bt_server.py:399`; `rg -n 'serve-remote|8766|FLOW_GATEWAY_KEY' remote/docs/runbook.md remote/deploy/advin-bitacora-tunnel.service`. **Required correction:** provide an ordered first-install path and explicit private laptop API startup/key references, with matching rollbacks. Existing update-path dry runs do not exercise a missing unit.

### F4 — Medium / open — Request logs disclose OAuth query values and misreport status

Tasks: **T11a**. Requirements: R16, R17.

`remote/gateway/server.py:48` treats `log_message`'s first argument as the response status. `BaseHTTPRequestHandler.log_request` actually passes the full request line there. Although the `path` field drops the query, `status` logs it again. A synthetic callback produced `status=GET /api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE HTTP/1.1`. OAuth authorization codes/state enter the journal and the real HTTP status is lost. No successful replay exploit or real credential exposure is asserted.

Evidence: probe A. **Required correction:** log the numeric status explicitly and omit query strings, cookies, authorization headers and provider response details.

### F5 — Medium / open — The state-changing guard does not cover logout or require marker value 1

Tasks: **T11a**, **T15a**. Requirement: R2.

Authenticated `GET /api/auth/logout` deletes a session without checking Origin or the custom header. A synthetic request with a foreign Origin returned 302 and revoked the session. `_valid_state_changing_request` also accepts any nonempty `X-Flow-Request` value; `not-one` reached the command handler with HTTP 200. This is a guard/spec defect, not evidence of an unauthenticated command bypass: commands still require a valid session and allowed Origin. Browser SameSite behavior narrows cross-site exploitation but does not implement the missing endpoint guard.

Evidence: probe A. **Required correction:** guarded logout mutation with a matching frontend action, and exact `X-Flow-Request: 1` validation.

### F6 — Medium / open — Telegram retry uses the run state instead of the target task state

Tasks: **T14b**. Requirements: R6, R12.

`telegram_bot.py:_handle_callback` builds a retry precondition from `run['state']`. The laptop's `TASK_SCOPED` state reader compares retries against the task state. A running run containing a failed task yields `{'state':'running'}` and the ledger rejects it as `STALE_PRECONDITION` with zero effects. `test_safe_callback_relays_a_telegram_origin_command_once_per_press` currently asserts the wrong run-state envelope against a fake laptop that accepts everything.

Evidence: probes B and C; C invokes the real bot, gateway translation, ledger and task-state reader over a synthetic running-run/failed-task snapshot and temporary Scheduler state table. Result: `STALE_PRECONDITION`, zero retry effects. **Required correction:** locate the task in the cached snapshot and pin its state/revision; exercise the real ledger on the bot path.

### F7 — Medium / open — The visible note action has no laptop dispatcher

Tasks: **T15f**. Requirements: R5, R13.

The web renders a note form and the gateway accepts `note`, but `bt_remote_commands.dispatch_handlers()` has no `note` handler. A valid translated note returns `COMMAND_NOT_IMPLEMENTED`, `stored: false`. Notes supplied through retry reasons exist, but they do not implement the separate advertised note action.

Evidence: probe B and `remote/web/src/app/page.tsx:387`. **Required correction:** define the note target, persist it through the existing operator-note mechanism, and demonstrate inclusion in the intended next prompt.

### F8 — Medium / open — The phone's brief editor cannot target or edit a real task

Tasks: **T15f**, **T8a**. Requirement: R13.

The form sends a plan-only target and `brief`, without `taskId` or `task`; the laptop requires `params.task` and raises `edit-brief requiere params.task.` It is shown only when `plan.state === 'approved'`, so an active failed run's launched plan has no edit form. For active scheduler runs the laptop compares `edit-brief` against run state while the web submits plan state. The UI also offers no acceptance-criteria edit although the laptop supports that field.

Evidence: `page.tsx:396`, `page.tsx:463`, `page.tsx:473`, `bt_remote_commands.py:233`; probe B. A separate synthetic `target_state` call with run `running` and plan `launched` returned `running`. **Required correction:** task selection, brief/criteria fields and a coherent revision/state precondition for the owner-approved edit/rebase workflow; exercise the actual dispatcher through the web envelope.

### F9 — Medium / open — “Reabrir ejecución” always omits the required task

Tasks: **T15d**. Requirement: R5.

`page.tsx:453` renders a run-level `reopen` form for failed/blocked/cancelled/finished runs. The laptop dispatches `reopen` only with `params.task`, so this action raises `reopen requiere params.task.` Task-level reopen is a different form and does supply the task. **Required correction:** provide the supported task-selection behavior or remove this unsupported run-level action. Evidence: probe B and the cited form.

### F10 — Medium / open — Plans waiting for approval do not produce notifications

Tasks: **T6**. Requirement: R10.

`decision_events(plans)` emits `plan.waiting` only by iterating scheduler decision requests. A normal plan with `state`/`plan_status` `review` and no decisions emits nothing; `derived_events` never inspects plans. Thus normal approval waiting, an explicit notification family, is absent. **Required correction:** derive a stable approval-waiting event from plan review state/revision, independently of scheduler decisions, and test delivery/dedupe. Evidence: probe B (`approval events: []`) and `bt_remote_api.py`'s full event assembly.

### F11 — Medium / open — Gateway restart loses offline state and breaks SSE cursor continuity

Tasks: **T12**. Requirements: R4, R7; reconnect edge case.

Snapshots/read caches and SSE events are memory-only. Recreating the runtime with the same SQLite database loses the last known snapshot; if the laptop is offline it serves 503 rather than the previous state. SSE sequence numbers also restart at 1. A reconnect with an old `Last-Event-ID` receives no new events until the new sequence overtakes it: publishing a new event as id 1 then requesting after old id 1 returned `[]`. There is no reset/resync protocol in the server handler.

Evidence: probe B for cursor reset; two real `GatewayRuntime` instances using one synthetic database produced `before restart snapshot: True`, `after restart snapshot: None`. **Required correction:** preserve the last good state and provide durable cursor continuity or an explicit client resynchronization protocol.

### F12 — Medium / open — Long-running gateway storage is not bounded

Tasks: **T11**, **T12**, **T14a**. Specification: disk-at-85% edge case, 90-day history pruning.

`SnapshotEventStream._events` is a deque without `maxlen` or eviction; every publish remains resident. The outbox and delivery-history tables retain sent/dropped messages indefinitely. Expired sessions are removed only when that exact token is queried, not by a sweep. No 90-day history pruning exists. Days-long execution therefore grows memory and SQLite storage without the promised bound. Evidence: `rg -n 'DELETE FROM|prune|retention|maxlen|expires_at' remote/gateway/auth.py remote/gateway/stream.py remote/gateway/notifications.py` and inspection of all store methods. **Required correction:** bounded replay/history/session retention with a documented cursor-expiry and notification-dedupe policy; do not lose restart dedupe while pruning.

### F13 — Medium / open — Offline timestamps represent failed probes rather than cached data age

Tasks: **T12**, **T15b**. Requirement: R7.

`update_laptop_status` overwrites `_snapshot_fetched_at` on every failed probe, so `cachedAt` keeps advancing even though no new laptop snapshot arrived. It has no stable `offlineSince`. The web displays only `LAPTOP SIN CONEXIÓN`; it never renders the required “sin conexión desde HH:MM”. Probe B moved `cachedAt` from 12:00:15 to 12:05:00 for the same snapshot. **Required correction:** keep capture time, probe time and outage start distinct and display the stable outage start in Spanish.

### F14 — Medium / open — Failure-review sanitization only recognizes four credential names

Tasks: **T7**, **T6**. Requirements: R16; control-plane constraint forbidding agent credentials on AdvIn.

The server's redactor only removes `FLOW_GATEWAY_KEY`, `TELEGRAM_BOT_TOKEN`, `GITHUB_CLIENT_SECRET` and `SESSION_SECRET`. Synthetic `OPENAI_API_KEY=SYNTHETIC_ONLY Authorization: Bearer SYNTHETIC_ONLY` passes through unchanged. Failure verification/log text is transmitted to AdvIn before the browser's broader assignment filter runs, and the browser does not remove bearer text either. This confirms a sanitization gap; it does not establish that a real log currently contains credentials.

Evidence: probe B and `_failure_review`/`route_get` in `bt_remote_api.py`. **Required correction:** sanitize common provider credentials and authorization/cookie material at the laptop boundary, using synthetic regression fixtures; do not inspect real credentials to test this.

### F15 — Medium / open — T9's promised socket-preserving reload is absent

Tasks: **T9**. Requirements: R7, R18; explicit T9 objective.

`bt_server._stale` still sends SIGTERM to the existing server. `ensure_server` then restarts the systemd unit or launches a replacement process; `serve` creates a fresh listening socket. No socket activation, inherited listener or reload path retains the socket. The 23 platform tests passing does not exercise preservation of an active connection/listener across reload. Evidence: `skill/scripts/bt_server.py:388`, `:414`, `:454`. **Required correction:** implement the approved reload/listener behavior and add a behavioral socket-continuity check, or have the owner amend that plan requirement; this audit does not waive it.

### F16 — Medium / open — The web cannot safely retry an unknown-outcome command with its existing key

Tasks: **T15d**. Requirement: R6; suspended-mid-command edge case.

Every form submission generates a new `web-${crypto.randomUUID()}`. `sendCommand` reports an error then drops the command envelope; it does not retain/display the original key or offer a same-key retry when `UNKNOWN_OUTCOME` occurs. A second tap becomes a different ledger operation, so the backend's correct same-key protection cannot protect that retry. This is a client recovery gap, not a demonstrated duplicate effect in production. Evidence: `page.tsx:295`, `:331`, `:356`, `:380`, `:401`; `rg -n 'UNKNOWN_OUTCOME|idempotencyKey|randomUUID' remote/web/src/app/page.tsx`. **Required correction:** retain uncertain submissions and reconcile/retry the identical envelope/key, including confirmation, before offering a new operation.

### F17 — Low / open — Published schemas disagree with the implemented wire contracts

Tasks: **T3**. Requirements: R3, R5, R10; versioned contract.

`docs/contract.md` calls the command schema the laptop body, but it defines the gateway camelCase envelope while
the laptop accepts snake_case (`idempotency_key`, `command`, string target). It permits 128-character keys while
laptop validation stops at 120, omits `answer-decision`, and disallows the `round` selector required by the working
translated answer path. `unevaluatedProperties: false` makes the latter additional field invalid.

The event schema also excludes production `task.progress`/`task.completed` events. Its target references the command
target schema, which requires `kind`, `project`, `req`: production flow events omit `kind`, and derived `run.finished`
events use `{run: 'demo/REQ-001'}`. These valid production payloads therefore violate explicit enum/required clauses.
This is a contract/documentation finding; no schema validator is claimed to run in the production relay.

Evidence: probes C/D, `remote/contract/{command,event}.schema.json`, `remote/docs/contract.md`,
`commands.to_laptop_command`, `bt_remote_commands.validate`/`dispatch_plan_command`, and event producer inspection.
**Required correction:** document the two command dialects and align both schemas/limits with actual producers,
adapters and all command/event families; validate representative producer output, not only JSON syntax.

### F18 — Medium / open — The advertised web verification shares browser build output and stalls on timeout

Tasks: **T15**. T15 acceptance: `npm run verify` builds offline. Supporting paths: the browser tests added by later UI tasks.

`npm test` invokes `node --test tests/*.test.mjs`, which runs test files concurrently. Both `oauth-browser.test.mjs`
and `panel-browser.test.mjs` spawn `next dev` with `cwd: root`, different mock gateway origins and no separate output
directory. They compete over the same `.next` artifacts/configuration. In this audit's unmodified tree,
`npm run verify` cancelled the panel test after 60000 ms, leaving eight passes and one cancellation. Cleanup also
waited for `once(next, 'close')` without a bound; the auditor had to terminate that invocation's Next.js server child
before the command returned exit 1. Its production build stage never ran.

A diagnostic `node --test --test-concurrency=1 tests/*.test.mjs` passed all nine tests in 23.862 s, and a separate
`npm run build` passed. This confirms the shipped verification is unreliable and the shared-output isolation
is defective; it does not prove that the artifact race alone caused this particular timeout, or that the panel
itself is broken in normal use. No other audit Next.js invocation overlapped either run.

Evidence: the command results above, `remote/web/package.json` test script,
`remote/web/tests/oauth-browser.test.mjs:112`/`:115`/`:155`, and
`remote/web/tests/panel-browser.test.mjs:79`/`:80`/`:286`.
**Required correction:** serialize these tests or isolate their Next.js output/configuration; bound cleanup of
server children, then rerun the actual `npm run verify` command. This read-only audit changes no test or script.

## Additional reproduction probes

These probes run from the repository root, use synthetic values, make only loopback requests and temporary local databases, and change no source. They demonstrate defects; a successful probe exit means the described behavior was reproduced, not that the product passed.

### Probe A — request logging, CSRF marker and logout

```bash
python - <<'PY'
import http.client, logging, sys, tempfile, threading
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, 'remote/gateway')
import server
from auth import OAuthConfig, SessionStore
out = StringIO()
sink = logging.StreamHandler(out)
server.logger.addHandler(sink)
server.logger.setLevel(logging.INFO)
Handler = server.make_handler(SimpleNamespace())
url = '/api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE'
Handler.log_message(SimpleNamespace(client_address=('127.0.0.1', 1), command='GET', path=url),
                    '"%s" %s %s', f'GET {url} HTTP/1.1', '400', '-')
print(out.getvalue().strip())
server.logger.removeHandler(sink)
class Runtime:
    def submit_command(self, value): return 200, {'status': 'OK'}
    def is_read_route(self, path): return False
with tempfile.TemporaryDirectory(dir='.') as tmp:
    cfg = OAuthConfig('synthetic-client', 'synthetic-secret', 's' * 32,
                      'https://flow.example.test', str(Path(tmp) / 'gateway.db'))
    store = SessionStore(cfg.database_path, cfg.session_secret)
    token = store.create_session('dav033')
    srv = server.create_server(cfg, ('127.0.0.1', 0), Runtime())
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    def request(method, path, headers, body=None):
        conn = http.client.HTTPConnection('127.0.0.1', srv.server_port, timeout=2)
        conn.request(method, path, body, headers)
        response = conn.getresponse()
        status = response.status
        response.read()
        conn.close()
        return status
    try:
        headers = {'Cookie': 'flow_session=' + token, 'Origin': cfg.frontend_origin,
                   'X-Flow-Request': 'not-one', 'Content-Type': 'application/json'}
        print('wrong marker POST:', request('POST', '/api/remote/v1/commands', headers, '{}'))
        print('foreign Origin logout:', request('GET', '/api/auth/logout',
              {'Cookie': 'flow_session=' + token, 'Origin': 'https://foreign.example.test'}))
        print('session retained:', store.get_session(token) is not None)
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(2)
PY
```

Observed: callback code/state in log; `wrong marker POST: 200`; `foreign Origin logout: 302`; `session retained: False`.

### Probe B — integration envelopes, event production and stream state

```bash
python - <<'PY'
import datetime as dt, json, sys, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, 'remote/gateway')
sys.path.insert(0, 'skill/scripts')
import bt_remote_commands as c, bt_remote_events as events, bt_flow_bus as bus
from commands import validate_command, to_laptop_command
from stream import SnapshotEventStream
with tempfile.TemporaryDirectory(dir='.') as tmp:
    ledger = c.Ledger(Path(tmp) / 'commands.db')
    note = {'schemaVersion': 1, 'idempotencyKey': 'synthetic-note-001', 'type': 'note',
            'target': {'kind': 'run', 'project': 'demo', 'req': 'REQ-001'},
            'precondition': {'state': 'running'}, 'note': 'SYNTHETIC NOTE'}
    print('note:', ledger.submit(to_laptop_command(validate_command(note)),
                                  c.dispatch_handlers(), lambda _: {'state': 'running'})['code'])
    retry = {**note, 'type': 'retry', 'idempotencyKey': 'synthetic-retry-001',
             'target': {**note['target'], 'kind': 'task', 'taskId': 'T1'}}
    retry.pop('note')
    print('bot run-state retry:', ledger.submit(to_laptop_command(validate_command(retry)),
          {'retry': lambda *_: None}, lambda _: {'state': 'failed'})['code'])
    with patch.object(c, '_run_target', return_value=('demo', 'REQ-001', Path(tmp))):
        for name, call in [
            ('UI brief edit', lambda: c.dispatch_edit_brief('demo/REQ-001',
                {'typed_req': 'REQ-001', 'brief': 'synthetic edit'})),
            ('UI run reopen', lambda: c.dispatch_run_command('reopen', 'demo/REQ-001', {}))]:
            try: call()
            except ValueError as exc: print(name + ':', str(exc))
plans = [{'project': 'demo', 'req_id': 'REQ-001', 'state': 'review',
          'plan_status': 'review', 'decisions': []}]
print('approval events:', events.decision_events(plans) +
      events.derived_events([], [], [], dt.datetime.now(dt.UTC)))
row = bus.audit_events('demo/REQ-001', [{'seq': 2, 'at': 1792497601.0,
    'kind': 'attempt_transition', 'task_id': 'T1', 'attempt_id': 'attempt-1',
    'detail': json.dumps({'from': 'running', 'to': 'failed', 'source': 'executor'})}],
    bus.Ctx(None, 'demo/REQ-001'))[0]
print('failure without fixture retry context:', events.from_flow(row, {}))
context = {('demo/REQ-001', 'T1'): {'state': 'failed', 'attempts': 3, 'maxAttempts': 3}}
print('failure with fixture retry context:', events.from_flow(row, context)['type'])
old = SnapshotEventStream()
old.update_snapshot({'runs': []}, '2026-10-20T12:00:00Z')
old.update_laptop_status(False, '2026-10-20T12:00:15Z')
print('first failed-probe cache time:', old.snapshot()['cachedAt'])
old.update_laptop_status(False, '2026-10-20T12:05:00Z')
print('later failed-probe cache time:', old.snapshot()['cachedAt'])
new = SnapshotEventStream()
new.publish([{'id': 'new-after-restart'}])
print('new events after old cursor 1:', new.after('1'))
print('snapshot after restart:', new.snapshot())
print('redaction:', events.redact('OPENAI_API_KEY=SYNTHETIC_ONLY Authorization: Bearer SYNTHETIC_ONLY'))
PY
```

Observed: `COMMAND_NOT_IMPLEMENTED`; `STALE_PRECONDITION`; missing-task errors for both UI envelopes; approval events `[]`; failure without context `None`, with context `attempt.failed`; cache time advances across failed probes; restarted stream returns `[]` and has no snapshot; synthetic provider/bearer values remain unredacted.

### Probe C — bot through the ledger, restart persistence, retention and schema boundary

Run from the repository root. This complements B's isolated examples with the actual bot/ledger/task-state path.
Only the plan-location/status lookup is stubbed; the task state is read from a real temporary SQLite state table.
The temporary `BITACORA_ROOT` is set before importing laptop modules. A and B were also run in subprocesses with an
empty temporary `BITACORA_ROOT`; none of the probes reads the live owner state.

```bash
python - <<'PY'
import json, os, sqlite3, sys, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path[:0] = ['remote/gateway', 'skill/scripts']
with tempfile.TemporaryDirectory(prefix='.audit-boundaries-', dir='.') as tmp:
    root = Path(tmp).resolve()
    os.environ['BITACORA_ROOT'] = str(root)
    import bt_remote_commands as c
    import bt_plans_api as plans
    from app import GatewayRuntime
    from auth import SessionStore, SESSION_TTL_SECONDS
    from commands import validate_command, to_laptop_command
    from config import GatewayConfig
    from stream import SnapshotEventStream
    from telegram_bot import TelegramBot
    from upstream import UpstreamResponseError
    cfg = GatewayConfig('http://127.0.0.1:1', 'synthetic-key', 'synthetic-token', '123', root/'gateway.db')
    run = {'project':'demo','req':'REQ-001','state':'running', 'tasks':[{'id':'T1','state':'failed'}]}
    ledger = c.Ledger(root/'commands.db')
    effects, results = [], []
    with sqlite3.connect(root/'SCHEDULER.db') as db:
        db.execute('CREATE TABLE state (id INTEGER PRIMARY KEY, doc TEXT)')
        db.execute('INSERT INTO state VALUES (1, ?)', (json.dumps({'tasks':{'T1':{'state':'failed'}}}),))
    class Laptop:
        def command(self, envelope):
            result = ledger.submit(envelope, {'retry': lambda *_: effects.append('retry')}, c.target_state)
            results.append((envelope['precondition'], result['code']))
            if result['code']: raise UpstreamResponseError(409, result)
            return 200, result
    class API:
        def call(self, *args, **kwargs): pass
    first = GatewayRuntime(cfg, laptop=Laptop(), sender=lambda *_:None)
    first.stream.update_snapshot({'runs':[run]}, '2026-10-20T12:00:00Z')
    status = {'run':{'authority':'scheduler','status':'running','plan_ref':{'revision':1}},
              'plan':{'status':'launched','revision':1}}
    with patch.object(c,'_run_target',return_value=('demo','REQ-001',root)), patch.object(plans,'status_of',return_value=status):
        TelegramBot(API(), '123', first).handle_update({'callback_query':{'id':'synthetic-callback-001',
            'message':{'chat':{'id':123}},'data':'retry|demo/REQ-001|T1'}})
        print('bot through task-state reader:', results, 'effects:', len(effects))
        print('active edit precondition state:', c.target_state('demo/REQ-001','edit-brief',{'task':'T1'})['state'])
    restarted = GatewayRuntime(cfg, laptop=Laptop(), sender=lambda *_:None)
    print('same database snapshot before/after restart:', first.stream.snapshot() is not None, restarted.stream.snapshot())
    first.outbox._db.close()
    restarted.outbox._db.close()
    sessions = SessionStore(str(root/'sessions.db'), 's'*32)
    sessions.create_session('dav033', now=0)
    sessions.create_session('dav033', now=SESSION_TTL_SECONDS+100)
    with sqlite3.connect(root/'sessions.db') as db:
        print('expired sessions retained after new login:', db.execute('SELECT count(*) FROM sessions WHERE expires_at<=?',(SESSION_TTL_SECONDS+100,)).fetchone()[0])
    print('SSE retention maxlen:', SnapshotEventStream()._events.maxlen)
    command={'schemaVersion':1,'idempotencyKey':'x'*121,'type':'pause','target':{'kind':'run','project':'demo','req':'REQ-001'},'precondition':{'state':'running'}}
    print('gateway accepts 121-char key; laptop:', c.validate(to_laptop_command(validate_command(command))))
    schema=json.loads(Path('remote/contract/command.schema.json').read_text())
    variants=[v.get('properties',{}).get('type',{}).get('const') for d in schema['$defs'].values() if isinstance(d,dict) for v in d.get('allOf',[])]
    print('answer-decision in schema:', 'answer-decision' in variants)
    print('gateway default bind:',cfg.bind_host)
PY
```

Observed (exit 0): bot precondition `{'state': 'running'}` → `STALE_PRECONDITION`, zero effects; active brief-edit
state `running`; same-database snapshot before/after restart `True None`; one expired session remains after another
login; SSE deque `maxlen: None`; gateway accepts a 121-character key that the laptop rejects with
`idempotency_key debe ser texto de 8 a 120 caracteres.`; schema has no `answer-decision`; gateway bind defaults to
`127.0.0.1`. Inspection of `NotificationOutbox` also confirms no outbox/history pruning method or deletion query.

### Probe D — event producer/schema boundary

Run from the repository root. This checks the schema's explicit enum and required-field clauses directly; it is
not presented as a full JSON Schema validator.

```bash
python - <<'PY'
import datetime as dt, json, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, 'skill/scripts')
with tempfile.TemporaryDirectory(prefix='.audit-contract-', dir='.') as tmp:
    os.environ['BITACORA_ROOT'] = str(Path(tmp).resolve())
    import bt_remote_events as events
    schema = json.loads(Path('remote/contract/event.schema.json').read_text())
    commands = json.loads(Path('remote/contract/command.schema.json').read_text())
    required = commands['$defs']['target']['required']
    event = events.project_event('task.progress', 'synthetic', '2026-10-20T12:00:00Z',
                                 {'project': 'demo', 'req': 'REQ-001'}, {'summary': 'synthetic'})
    print('progress type allowed:', event['type'] in schema['properties']['type']['enum'])
    print('progress missing required target fields:', [k for k in required if k not in event['target']])
    event = events.derived_events([{'run': 'demo/REQ-001', 'state': 'finished',
                                    'updated_at': '2026-10-20T12:00:00Z'}], [], [], dt.datetime.now(dt.UTC))[0]
    print('derived target:', event['target'])
    print('derived missing required target fields:', [k for k in required if k not in event['target']])
PY
```

Observed (exit 0): progress type is not allowed; progress target lacks `kind`; derived `run.finished` target is
`{'run': 'demo/REQ-001'}`, lacking `kind`, `project`, `req`. Producer/schema incompatibility is recorded in F17.

## Investigated candidates rejected as findings

These are rejected hypotheses, not accepted risks; they are deliberately excluded from the confirmed-findings ledger.

| Candidate | Verdict and evidence |
|---|---|
| Reverse SSH tunnel exposes unauthenticated laptop panel controls | Rejected for this tree. Tunnel targets 8766; `RemoteHandler` accepts only the remote prefix and every remote handler authenticates. The executed remote-listener tests check `/`, `/plans`, project routes and plan-launch POST return 404, health without key returns 401. |
| OAuth state cookie must be Strict like the session cookie | Rejected. This is the temporary callback binding, uses Lax for the cross-site top-level callback, and is consumed once. Session cookie remains host-only, HttpOnly, Secure, Strict. Auth tests and Chromium round-trip passed. |
| Gateway omission of `edit-brief` from its required-confirmation set bypasses laptop confirmation | Rejected as a bypass. The laptop includes `edit-brief` in `CHALLENGED` and verifies the one-use target-bound challenge before the effect. Executed recovery tests reject missing/mismatched confirmation. F8 addresses the separate unusable editor. |
| Retrying the same key executes a command twice | Rejected for the tested ledger path. Remote command tests exercise replay, mismatched bodies and pending outcomes. The client losing that key is a separate confirmed issue, F16. |
| Named `SESSION_SECRET` assignments are exposed by the current redactor | Rejected. `_SECRET_NAMES` explicitly includes it and the executed remote event/review tests passed. F14 concerns other credential formats. |

## Coverage and remaining work

R1/R3 authentication and listener isolation have direct passing tests; F1/F3 block the intended deployment. R2/R17 have F4/F5. R4/R7 have F11/F13/F15 and client recovery F16. R5/R6/R8 have passing ledger/challenge tests but F6–F9/F16/F17 at component boundaries. R9/R16 have F14. R10–R12 have passing isolated notification/bot tests but F2/F6/F10/F12. R13 has F7/F8. R14 has a passing serialized 360 px Chromium scenario, local fonts and manifest checks, while F18 affects the default verification; this does not establish every touch target or hosted install behavior. R15 has passing read/relay tests, with unbounded history in F12.

The scheduler should return F1 to T16 and F2 to T17 for rework, then request an independent audit again. Medium/low findings remain recorded and unresolved; only the owner can accept them. Recheck fixes against the actual cross-component envelopes, not only mocks. The required report/ledger files are delivered; product readiness, high-finding closure and the independent acceptance decision remain outstanding.
