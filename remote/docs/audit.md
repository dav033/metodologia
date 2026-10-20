# Independent security and specification audit — T18

**Rework required: three high findings remain open (F2/T17, F19/T15a, F20/T15a).**
The required E2E exits 1 before running a test because the web build fails. A separate real-API fixture
probe also reproduces an empty notification feed and a rejected happy-path cancel. The read-only audit
cannot repair source, tests or configuration; these results must return to their named prerequisite tasks.

Audited tree: `4c20e6cb77611d16f610a44c108b84220236d857` (HEAD at checkout).
Date: 2026-10-20. Auditor: Codex / OpenAI. Provider diversity must be checked against scheduler assignment
metadata; this report does not infer providers from commit authors or claim a second provider was invoked.

## Retry provenance and conflict resolution

Read the supplied attempt history: #5 att-0172 had eleven blocking findings; #6 att-0180 had five;
#7 was cancelled; #8 att-0185, #9 att-0198 and #10 att-0201 repeated F1/F2. The four omitted attempts and
the contents behind the supplied m6 evidence URIs were not available in this worktree and are not claimed reviewed.
Read the inherited report/ledger, the reachable att-0185 report, and the subsequent report diffs.
Earlier test results are historical context only.

Unlike those last three retries, the current merge contains changed prerequisites: comparing `15f1a318`
with this HEAD lists 48 changed implementation/test/deployment files. The worktree was initially clean.
Both audit files were opened; neither contained literal conflict markers despite the task wrapper's warning.
The overlap was semantic: the carried report described the previous code and claimed that no prerequisites
had changed. This report replaces that stale claim, retains every inherited finding ID with an explicit current
verdict, and preserves partial remediation instead of erasing either the original defect or the new work.
New IDs F19–F23 belong to this review; they do not purport to identify findings from the omitted old reports.

There are 23 ledger entries: two rechecked fixes (F1, F15), three open high findings, seventeen open medium
findings and one open low finding. No risk is accepted. A partially corrected finding remains open with the
remaining defect stated. Rejected hypotheses are listed separately, not mislabeled accepted risks.

## Scope, permissions and method

Read the complete frozen SPEC and PLAN.md, and every PLAN.json task objective, acceptance criterion and verification
command, including PLAN Verification's real-ledger cancel/stale/notification scenarios. Reviewed authentication,
the private laptop listener, ledger/challenges and dispatchers, snapshot/event/review producers, gateway relay,
liveness/cache/SSE, notification outbox/bot, phone consumers and mocks, deployment kit, and the rewritten E2E.

Only this report and `audit.findings.json` are edited. All data in probes is synthetic, all HTTP requests are
loopback, and all SQLite/fixture roots are temporary. Laptop, platform, page and gateway suites ran in separate
subprocesses with `BITACORA_ROOT` set to an empty temporary directory inside this worktree before imports.
Probe B sets it before importing laptop modules; probe C uses T17's temporary fixture root for its real listener.
No live bitácora, credentials, OAuth account, Telegram chat, production host, other worktree or remote was accessed.
No deployment or user service restart was performed. Notes stay here under the frozen plan's read-only boundary.

Runtime: Python 3.14.7, Node 24.21.0; target Python 3.12 was not available/tested.
`cd remote/web && npm ci --offline` installed 320 packages, exit 0, with no tracked lockfile change.
Its cached advisory message is not a fresh vulnerability assessment.

## Fresh verification evidence

Commands are from the repository root unless a working directory is shown. Duplicate PLAN verification commands
share one execution of the same complete suite; none is represented by a narrower test.

| Command | Actual result |
|---|---|
| `cd remote/gateway && python -m unittest discover -s tests -p 'test_*.py'` | Exit 0; 35 tests, 11.146 s. SQLite ResourceWarnings. |
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py'` | Exit 0; 56 tests, 11.014 s. SQLite ResourceWarnings. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` | Exit 0; 25 tests, 2.001 s. Includes inherited-listener tests. |
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_page*.py'` | Exit 0; 43 tests, 11.417 s. Local flow/plans page regressions. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 0; 4 tests, 0.110 s. Caddy absent: test uses structural fallback, not real Caddy validation. |
| `sh remote/deploy/deploy.sh --check` | Exit 0; `deployment topology: 172.20.0.1:8790`. |
| `cd remote/web && npm run verify` | Exit 2. Lint completes with one unused-variable warning at page.tsx:297; typecheck fails TS2677 at :138 and TS2322 at :143. Tests/build in this command are not reached. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 1; 0 tests, 12.061 s; setUpClass's actual `npm run build` fails the same type predicate. No built-web scenario passes. |
| `cd remote/web && node --test --test-concurrency=1 tests/*.test.mjs` | Exit 1; 8 tests, 7 passed, 1 failed, 36.428 s. Panel assertion :223 expects `answer`, current command has `answers`. No cancellation or timeout in this run. |
| Diagnostic dev substitution for T17 | Exit 1; 1 test errors in 6.509 s on its first page request (4 s timeout). See limitations below; this is not a built-web E2E pass. |
| Report probe A | Exit 0: reproduces OAuth query logging, wrong-marker acceptance and unguarded logout. |
| Report probe B | Exit 0: reproduces boundary/storage/configuration issues below, including real authenticated session payload and SSE route 404. |
| Report probe C | Exit 0: real laptop API + real gateway client/adapter + real ledger return empty failure feed; attempt is reserved; stale and happy-path cancel both return 409; zero cancelled transitions. |
| `python -m json.tool remote/contract/command.schema.json` and corresponding event schema command | Each exit 0. Syntax only, not schema conformance of live payloads. |
| `test -s remote/docs/audit.md` (each of T18's three identical checks) | Each exit 0 after this report is written. |

The Python suites ran independently in parallel. Web verification, E2E build, diagnostic dev run and serial browser
tests ran sequentially; the audit did not start competing Next.js commands. The default web test script itself
still permits its browser files to race on shared output (F18). The bounded serial-run wrapper would stop only
its own process group after 110 s; the run finished normally with the assertion failure before that limit.

The optional diagnostic changed only in-memory harness methods: skipped `_build_web`, started `next dev` instead
of `npm start`, and ran the original unittest. Its first page request timed out while development compilation
was starting. That result establishes no downstream behavior and did not motivate any source/test change.
Probe C then isolated the actual notification/cancel boundaries without building or starting Next.js.

Not run: live Docker connectivity, real `caddy validate` (binary absent), actual AdvIn/Vercel deployment,
real GitHub/Telegram, Python 3.12, the entire unrelated legacy suite, or all remaining browser assertions after
the failure. Hosted rewrite behavior, complete 44 px touch-target coverage and production PWA installation
remain unestablished. The report's file-existence checks do not satisfy substantive high-finding closure.

## Finding verdicts and remediation

### F1 — high / fixed — The prior Caddy container-loopback upstream defect is corrected in the supplied prerequisite tree.

Tasks: `T16`.

R1/R3/R4; PLAN Approach. Caddyfile now targets the approved host bridge, the unit declares that bind address, and the runbook describes the same topology. The old container-loopback diagnosis is withdrawn for this tree. This closes that specific defect, not hosted deployment readiness.

Evidence: cd remote/deploy && python -m unittest discover -s tests -p test_kit.py: exit 0, 4 tests in 0.110s; test_caddy_block_and_deploy_entrypoint_use_host_gateway_offline checks reverse_proxy 172.20.0.1:8790 and service Environment=GATEWAY_BIND=172.20.0.1. sh remote/deploy/deploy.sh --check: exit 0, deployment topology: 172.20.0.1:8790. Live Docker connectivity was not tested; separate env-example defect F22 remains.

### F2 — high / open — The E2E fixture still yields no failure event and its supposedly valid cancel command pins running against a reserved attempt; full E2E also stops at the web build.

Tasks: `T17`.

R5/R6/R10/R11; T17 and PLAN Verification. Isolation and cancel/stale scenarios were added, so the previous assertion that those scenarios are absent no longer applies. However, _seed_retry_event_fixture writes only an audit table and a recovery action 'retry': the resulting run has no authoritative task state and produces no terminal failure notification. _seed_cancel_run_fixture calls scheduler.step(), leaving att-0001 reserved, whereas the happy-path command expects running. Correct the fixtures using real terminal/exhaustion and running-attempt transitions; keep the once-only notification and real-ledger checks. Re-run the unmodified built-web E2E after F19. Changing this report cannot repair either fixture.

Evidence: cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py: exit 1, Ran 0 tests, setUpClass build error (F19). Report probe C: real fixture feed events=[], nextCursor=''; fixture attempt state reserved; stale command 409 STALE_PRECONDITION; supposedly current cancel also 409 STALE_PRECONDITION; cancelled transitions 0.

### F3 — medium / open — Runbook still omits installing/configuring the private laptop API and reverse tunnel; public Caddy hostname remains an unexplained placeholder.

Tasks: `T16`.

R3/R7. The previous start-before-unit-install ordering is corrected: deploy.sh now installs the unit before enable --now. Preserve that improvement. Add an explicit secret-reference-only listener/tunnel setup at 127.0.0.1:8766 -> AdvIn 127.0.0.1:18765 and the approved public hostname, with rollback per step. deploy.sh also prints host-Caddy reload instructions despite the Docker topology; align the operator instructions.

Evidence: Current remote/docs/runbook.md Go-live steps 1-5 cover host gateway and Docker Caddy only; no serve-remote startup, laptop FLOW_GATEWAY_KEY loading, or tunnel installation/start. Caddyfile uses flow.example.com instead of the approved sslip.io hostname; runbook never instructs substitution.

### F4 — medium / open — Request logging still writes OAuth code/state query values into the status field.

Tasks: `T11a`.

R16/R17. The path field drops queries but the status field puts them back. Log the numeric response status and safe path only. No real authorization code was read or printed.

Evidence: Report probe A, exit 0: status=GET /api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE HTTP/1.1. server.py log_message takes args[0], the full request line, as status.

### F5 — medium / open — GET logout bypasses mutation guards, and the CSRF marker accepts any nonempty value rather than 1.

Tasks: `T11a`, `T15a`.

R2. Require the exact marker and matching Origin on logout through a guarded mutation; update the web action. This is a guard/spec defect; authenticated command access itself was not bypassed.

Evidence: Report probe A, exit 0: wrong marker POST 200; foreign Origin logout 302; session retained False. server.py uses bool(request_marker); page.tsx still links GET /api/auth/logout.

### F6 — medium / open — Telegram retry and alert action/deep-link integration are missing; the previous bad retry envelope was removed rather than repaired.

Tasks: `T14a`, `T14b`.

R10/R12. The former running-versus-failed retry mismatch is no longer reachable because no retry button is offered. Alerts need run/task/cause, a working failure-review URL and safe ver/reintentar/pausar actions; /estado must remain owner-only. Implement target-bound retry preconditions and exercise the bot through the real ledger; restore a deliberate validation error instead of NameError.

Evidence: Report probe B: submit_telegram_command(retry) raises NameError because CommandValidationError is not imported; app.py allows only pause/resume. telegram_bot.py _send_status constructs only pause/resume callbacks; notifications.py TelegramSender sends chat_id/text only, no reply_markup, and notification_for_event produces at most a fragment, not a frontend URL.

### F7 — medium / open — The advertised note command remains accepted by validators but has no laptop dispatcher.

Tasks: `T5a`.

R5/R13. The prior standalone web note form is gone; that UI claim is withdrawn. Retry reasons still persist operator notes and are not defective here. Either implement the documented standalone note through the existing note owner or obtain an explicit scope/contract change; an unsupported advertised command cannot be treated as implemented.

Evidence: Report probe B, exit 0: GatewayRuntime._web_command(validate_command(note)) -> real Ledger/dispatch_handlers -> COMMAND_NOT_IMPLEMENTED. note is still in both command enums.

### F8 — medium / open — Task brief editing now supplies the task and run precondition, but the phone still cannot edit acceptance criteria.

Tasks: `T15f`.

R13. The former missing-task, hidden-active-plan and plan-state-envelope subfindings are corrected by source inspection. Preserve those changes; expose criteria editing with the same owner-approved revision/challenge path. Full web-driven revision verification was not reached because of F19.

Evidence: Current page.tsx editBriefForm sends task, field='objective', value and run.state; renderTask shows a brief textarea for failed/blocked tasks. No acceptance_criteria editing field or selector exists. bt_remote_commands.dispatch_edit_brief supports acceptance_criteria.

### F9 — medium / open — Run-level Reabrir ejecución still sends no task to a dispatcher that requires one.

Tasks: `T15d`.

R5. Provide supported task selection, or remove the unsupported run-level action while retaining task-level reopen. Existing task-level controls do supply taskId.

Evidence: Report probe B: dispatch_run_command('reopen', 'demo/REQ-001', {}) raises reopen requiere params.task. page.tsx run-level commandForm('reopen', {kind:'run',...}) supplies no taskId.

### F10 — medium / open — An ordinary plan waiting for approval still emits no plan.waiting event without a scheduler decision.

Tasks: `T6`.

R10. Derive an approval-waiting event from review status and stable revision independently of scheduler decision requests. Delivery/deduplication of an already supplied plan.waiting event passes isolated tests.

Evidence: Report probe B: decision_events([{project:'demo',req_id:'REQ-001',plan_status:'review',decisions:[]}]) returns []; route_get events calls decision_events(plans) and from_snapshot(runs, rounds), which has no plans input.

### F11 — medium / open — Restart still loses the cached snapshot and resets SSE IDs without a resynchronization protocol.

Tasks: `T12`.

R4/R7 and reconnect edge case. Persist last good state and cursor continuity, or explicitly resynchronize clients after restart. Notification dedupe persistence does not persist the snapshot or SSE history.

Evidence: Report probe B: two GatewayRuntime instances with one database yield snapshot before/after restart True/None; a new stream with event 1 returns [] after old Last-Event-ID 1. HTTP _stream_events has no reset event/protocol.

### F12 — medium / open — Gateway event history, delivered/dropped outbox/history and abandoned expired sessions remain unbounded.

Tasks: `T11`, `T12`, `T14a`.

SPEC disk/90-day retention edge case. Bound the in-memory replay window and implement documented storage retention while preserving required dedupe/replay semantics. Command and history list endpoints also read full ledgers.

Evidence: Report probe B: stream deque.maxlen None; expired session count 1 after a later login. Source inspection: NotificationOutbox has no 90-day pruning/deletion; SessionStore prunes only a session whose token is presented.

### F13 — medium / open — Failed probes relabel cached data with the current time; offline start time is not exposed to the phone.

Tasks: `T12`, `T15b`.

R7. Preserve the successful snapshot capture time and expose a stable offlineSince timestamp for 'sin conexión desde HH:MM'. LivenessMonitor's internal monotonic timestamp is not a serialized wall-clock time.

Evidence: Report probe B: repeated _publish_liveness calls change cachedAt without fetching data. app.py publishes cached_snapshot with datetime.now on health failure; page.tsx displays LAPTOP SIN CONEXIÓN with no outage-start timestamp.

### F14 — medium / open — Laptop redaction still misses provider API-key assignments and bearer authorization text before transmission.

Tasks: `T7`, `T6`.

R9/R16; T7 Secrets are filtered from returned text. Frontend rendering redaction runs after the material has already crossed the laptop/gateway boundary and does not address bearer text. Broaden bounded redaction and test representative credential forms using synthetic values.

Evidence: Report probe B: redact('OPENAI_API_KEY=SYNTHETIC Authorization: Bearer SYNTHETIC') returns both values unchanged. bt_remote_api applies this redactor to review/events; _SECRET_NAMES lists only four credential names.

### F15 — medium / fixed — The earlier absence of an inherited-listener path is corrected in the supplied prerequisite tree.

Tasks: `T9`.

R7/R18; T9. The tested path reuses the listening descriptor when systemd socket activation is configured. No live user service was restarted; installation of an actual socket unit is not demonstrated by these tests and is part of operational setup.

Evidence: cd skill/scripts && python -m unittest discover -s tests -p test_platform.py: exit 0, 25 tests in 2.001s, including test_web_server_reload_uses_the_inherited_listener and test_systemd_listener_requires_its_activation_environment. Source create_http_server adopts systemd_listener; ensure_server restarts the unit without spawning a loose process.

### F16 — medium / open — The web still discards unknown-outcome envelopes and generates a fresh key on every retry.

Tasks: `T15d`.

R6 and suspended-mid-command edge case. Retain the exact envelope and provide a same-key reconciliation/retry path; do not create another logical command when the prior outcome is unknown. No production duplicate effect is asserted.

Evidence: Current page.tsx sendCommand keeps only the returned message, not the command/idempotencyKey; commandForm, roundForm, decisionForm, retryTask and editBriefForm create a new web UUID for every submission.

### F17 — low / open — Published command/event schemas still disagree with production dialects, field names and key limits.

Tasks: `T3`.

T3 every command family and R3/R5/R6/R10. Contract response/status/pagination descriptions also differ from the synchronous ledger API. Earlier claims about production task.progress/task.completed events are withdrawn: the current producer does not emit those types. Validate representative real producer/consumer envelopes against the schemas; JSON syntax alone does not do that.

Evidence: Report probe B: gateway accepts a 121-character key rejected by laptop's 120 limit; produced run.finished target lacks kind/project/req required by the referenced schema. Source schemas omit answer-decision, specify string route rather than the current route object, and require answer while the web now submits answers.

### F18 — medium / open — Browser checks still share Next.js output/configuration, and serial execution now reveals a stale answer-round contract assertion.

Tasks: `T15`, `T15e`.

Do not reuse the prior serial-pass claim. The current serial failure is an assertion mismatch, not evidence that concurrency caused this run. Align fixtures/assertions with the intended round wire contract and isolate/serialize browser output and bounded cleanup; then execute the tracked verify command. Remaining assertions after that failure were not reached.

Evidence: cd remote/web && node --test --test-concurrency=1 tests/*.test.mjs: exit 1, 8 tests, 7 passed, 1 failed in 36.428s; panel-browser.test.mjs:223 expects command.answer but current roundForm sends answers. Both browser tests spawn next dev in the same cwd/.next; default npm test remains concurrent.

### F19 — high / open — The current run-history parser does not typecheck, preventing the production build and every built-web E2E scenario.

Tasks: `T15a`.

T15/T15a offline build and R4/R14. Attempt has optional state/updatedAt, while the inferred parseAttempt result requires those properties with undefined values; it is not a valid narrowing predicate. Correct the type relationship without suppressing strict checks, then rerun verify and the actual built E2E.

Evidence: cd remote/web && npm run verify: exit 2 at typecheck; TS2677 page.tsx:138 and TS2322 page.tsx:143. E2E invokes npm run build, which exits 1 on the same invalid Attempt type predicate; Ran 0 tests in 12.061s.

### F20 — high / open — Successful real OAuth sessions cannot load the phone panel because the gateway and web disagree on the session response.

Tasks: `T15a`.

R1/R4; T15a owner signs in and sees runs. Align producer and consumer and add a browser scenario using the real gateway session route. Current E2E checks the session HTTP payload but does not execute the authenticated React panel, so its OAuth assertions cannot cover this failure.

Evidence: Report probe B: authenticated GET /api/auth/session returns HTTP 200 {login:'dav033'}. page.tsx load requires typeof parsedSession.authenticated === 'boolean' and otherwise throws Respuesta de sesión inválida before setting session or fetching snapshot. Mock returns authenticated:true and conceals the mismatch.

### F21 — medium / open — The real phone feed cannot connect or decode production events despite mock SSE coverage.

Tasks: `T4a`, `T6`, `T15b`.

R4 and SSE reconnect edge case. Align endpoint, initial/reconnect cursor and target dialect across components, and exercise the actual producer through the gateway. from_flow also discards normal activity events, so the notification-only feed cannot reproduce all /flow activity merely by correcting its path. Snapshot polling is present but does not repair the feed.

Evidence: Report probe B: authenticated GET /api/remote/v1/events/stream?after=abc returns 404. Gateway streams only /api/remote/v1/events and reads Last-Event-ID, while page.tsx uses the former path/query. Laptop snapshot cursor is always empty, and the web refuses to create EventSource without a truthy snapshot cursor. Production event targets use run/task, but parseFlowEvent requires project/req and reads taskId/task_id.

### F22 — medium / open — Filling the required env-example values still leaves blank optional settings that prevent gateway startup.

Tasks: `T16`.

T16 usable go-live kit; R16. The runbook says fill required values, but all optional variables are assigned empty strings. Document valid nonsecret values or omit optional assignments when retaining defaults. Explicitly cover the example-to-runtime path rather than only requiring every example line to be blank. A GATEWAY_BIND empty assignment can also override the unit's intended bind; the example comment explicitly asks to fill that one.

Evidence: Report probe B: parsing the checked-in example after filling required synthetic values and GATEWAY_BIND raises Gateway port and timeouts must be numeric; filling numeric settings then raises GitHub OAuth endpoints must use https because blank endpoint assignments override defaults.

### F23 — medium / open — Phone command history drops the stored web/telegram origin and displays target/command in its place.

Tasks: `T15d`.

R15; T15d history lists origin and result. Preserve command and target separately and display the actual stored web/telegram origin with timestamp and outcome. The real /history route now exists, so its availability is not a finding; presentation loses provenance.

Evidence: Current page.tsx refreshCommandHistory constructs item.origin from item.target and item.command without reading item.origin; history rendering labels that constructed text Origen. Laptop Ledger.rows retains the real origin field.

## Reproducible additional probes

Run these from the repository root with installed web dependencies. They read repository code and synthetic
temporary fixtures only. Exit 0 means the observed defect was reproduced; it is not a product pass.
Temporary directories and test-owned subprocesses are cleaned up by these probes.

### Probe A — HTTP logging and mutation guards

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

Observed: synthetic callback code/state appear in the log's status field; wrong-marker POST 200;
foreign-Origin logout 302; session retained False. No real token is printed.

### Probe B — producer/consumer, persistence, retention and configuration boundaries

```bash
python - <<'PY'
import os, sys, json, tempfile, datetime as dt, sqlite3, http.client, threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path[:0] = ['remote/gateway', 'skill/scripts']
with tempfile.TemporaryDirectory(prefix='.audit-boundaries-', dir='.') as tmp:
    root = Path(tmp).resolve()
    os.environ['BITACORA_ROOT'] = str(root)
    import bt_remote_commands as c, bt_remote_events as ev
    from app import GatewayRuntime
    from config import GatewayConfig
    from auth import OAuthConfig, SessionStore, SESSION_TTL_SECONDS
    from commands import validate_command, CommandValidationError
    from stream import SnapshotEventStream
    from server import create_server
    cfg = GatewayConfig('http://127.0.0.1:1', 'synthetic', 'synthetic', '123', root/'gateway.db')
    runtime = GatewayRuntime(cfg, laptop=SimpleNamespace(), sender=lambda *_: None)
    note={'schemaVersion':1,'idempotencyKey':'synthetic-note-001','type':'note',
          'target':{'kind':'run','project':'demo','req':'REQ-001'},'precondition':{'state':'running'},'note':'synthetic'}
    print('F7 note:',c.Ledger(root/'ledger.db').submit(runtime._web_command(validate_command(note)),c.dispatch_handlers(),lambda _: {'state':'running'})['code'])
    with patch.object(c,'_run_target',return_value=('demo','REQ-001',root)):
        try: c.dispatch_run_command('reopen','demo/REQ-001',{})
        except ValueError as exc: print('F9 run reopen:',str(exc))
    print('F10 review plan events:',ev.decision_events([{'project':'demo','req_id':'REQ-001','plan_status':'review','decisions':[]}]))
    print('F14 redaction:',ev.redact('OPENAI_API_KEY=SYNTHETIC Authorization: Bearer SYNTHETIC'))
    stream=SnapshotEventStream(); stream.publish([{'id':'new'}])
    print('F11 restarted stream after cursor 1:',stream.after('1'))
    runtime.cached_snapshot={'runs':[{'state':'running'}]}
    runtime._publish_liveness(); first=runtime.stream.snapshot()['cachedAt']
    with patch('app.datetime') as date:
        date.now.return_value=dt.datetime(2026,10,21,tzinfo=dt.UTC)
        runtime._publish_liveness()
    print('F13 failed probe rewrites cachedAt:',first != runtime.stream.snapshot()['cachedAt'])
    again=GatewayRuntime(cfg,laptop=SimpleNamespace(),sender=lambda *_:None)
    print('F11 snapshot before/after restart:',bool(runtime.stream.snapshot()),again.stream.snapshot())
    print('F12 stream maxlen:',stream._events.maxlen)
    sessions=SessionStore(str(root/'sessions.db'),'s'*32)
    sessions.create_session('dav033',now=0);sessions.create_session('dav033',now=SESSION_TTL_SECONDS+10)
    with sqlite3.connect(root/'sessions.db') as db:
        print('F12 expired rows:',db.execute('SELECT COUNT(*) FROM sessions WHERE expires_at<=?',(SESSION_TTL_SECONDS+10,)).fetchone()[0])
    longkey={**note,'type':'pause','idempotencyKey':'x'*121}
    print('F17 121-char key laptop:',c.validate(runtime._web_command(validate_command(longkey))))
    event=ev.from_snapshot([{'run':'demo/REQ-001','state':'finished','updated_at':'2026-10-20T12:00:00Z'}],[])[0]
    schema=json.loads(Path('remote/contract/command.schema.json').read_text())
    print('F17 missing target fields:',[k for k in schema['$defs']['target']['required'] if k not in event['target']])
    retry={**note,'type':'retry','target':{**note['target'],'kind':'task','taskId':'T1'}}
    try: runtime.submit_telegram_command(retry)
    except (CommandValidationError, NameError) as exc: print('F6 telegram retry:',type(exc).__name__, str(exc))
    auth=OAuthConfig('synthetic','synthetic','s'*32,'https://flow.example.test',str(root/'auth.db'))
    token=SessionStore(auth.database_path,auth.session_secret).create_session('dav033')
    srv=create_server(auth,('127.0.0.1',0),runtime)
    thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start()
    try:
        for path in ['/api/auth/session','/api/remote/v1/events/stream?after=abc']:
            conn=http.client.HTTPConnection('127.0.0.1',srv.server_port,timeout=3)
            conn.request('GET',path,headers={'Cookie':'flow_session='+token})
            response=conn.getresponse();print('HTTP',path,response.status,response.read().decode());conn.close()
    finally: srv.shutdown();srv.server_close();thread.join()
    values=dict(line.split('=',1) for line in Path('remote/deploy/gateway.env.example').read_text().splitlines() if line and not line.startswith('#'))
    values.update(LAPTOP_ORIGIN='http://127.0.0.1:18765',FLOW_GATEWAY_KEY='synthetic',TELEGRAM_BOT_TOKEN='synthetic',TELEGRAM_CHAT_ID='123',GATEWAY_DATABASE=str(root/'kit.db'),
                  GITHUB_CLIENT_ID='synthetic',GITHUB_CLIENT_SECRET='synthetic',SESSION_SECRET='s'*32,FLOW_FRONTEND_ORIGIN='https://flow.example.test',GATEWAY_BIND='172.20.0.1')
    try: GatewayConfig.from_env(values)
    except ValueError as exc: print('F22 filled-required example:',str(exc))
    values.update(GATEWAY_PORT='8790',UPSTREAM_TIMEOUT='5',PROBE_INTERVAL='5')
    try: OAuthConfig.from_env(values)
    except ValueError as exc: print('F22 example after numeric settings:',str(exc))
    runtime.outbox._db.close();again.outbox._db.close()
PY
```

Observed: note COMMAND_NOT_IMPLEMENTED; reopen requires params.task; review-plan events [];
synthetic provider/bearer assignments unredacted; restart replay []; snapshot True/None; failed-probe
cachedAt changes; deque maxlen None; expired sessions 1; key-limit disagreement; event target missing
kind/project/req; Telegram retry NameError; real session 200 with login only; web SSE path 404;
env example fails numeric validation, then OAuth endpoint validation.

An initial execution stopped at the product's unexpected NameError when the probe caught only the intended
CommandValidationError. The final probe additionally catches that specific NameError so the remaining
independent observations can run; the product error is preserved in F6, not suppressed in source.

### Probe C — exact T17 fixtures through the real laptop API and gateway adapter

```bash
python - <<'PY'
import sys,tempfile,http.client,json,os,subprocess
from pathlib import Path
sys.path[:0]=[str(Path('remote/e2e/tests').resolve()),str(Path('remote/gateway').resolve())]
import test_local_e2e as e
from app import GatewayRuntime,CommandRelayError
from config import GatewayConfig
C=e.LocalEndToEndTests
with tempfile.TemporaryDirectory(prefix='.audit-fixture-',dir='.') as tmp:
    root=Path(tmp).resolve(); C.root=root/'bitacora'; C.root.mkdir(); C.laptop_port=e.free_port()
    C._seed_retry_event_fixture(); C._seed_cancel_run_fixture()
    p=subprocess.Popen([sys.executable,str(e.SCRIPTS/'bitacora.py'),'serve-remote','--port',str(C.laptop_port)],cwd=e.SCRIPTS,env={**os.environ,'BITACORA_ROOT':str(C.root),'FLOW_GATEWAY_KEY':e.GATEWAY_KEY},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    runtime=None
    try:
        C._wait_port(C.laptop_port,p,'fixture laptop')
        runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{C.laptop_port}',e.GATEWAY_KEY,'synthetic','123',root/'gateway.db'),sender=lambda *_:None)
        feed=runtime.laptop.events('');print('F2 real fixture feed:',feed)
        import sqlite3
        with sqlite3.connect(C.root/'.state/scheduler/demo-REQ-002.db') as db:
            doc=json.loads(db.execute('SELECT doc FROM state WHERE id=1').fetchone()[0])
            print('fixture attempt state:',doc['attempts']['att-0001']['state'])
        command={'schemaVersion':1,'idempotencyKey':'audit-stale-cancel-001','type':'cancel-attempt','target':{'kind':'attempt','project':'demo','req':'REQ-002','attemptId':'att-0001'},'precondition':{'state':'running','revision':0},'reason':'Synthetic audit cancellation'}
        try: print('stale:',runtime.submit_command(command))
        except CommandRelayError as exc: print('stale:',exc.status,exc.code)
        command.update(idempotencyKey='audit-current-cancel-001',precondition={'state':'running','revision':1})
        try: print('cancel:',runtime.submit_command(command))
        except CommandRelayError as exc: print('cancel:',exc.status,exc.code)
        import sqlite3
        with sqlite3.connect(C.root/'.state/scheduler/demo-REQ-002.db') as db:
            n=db.execute("SELECT COUNT(*) FROM audit WHERE kind='attempt_transition' AND attempt_id='att-0001' AND detail LIKE '%cancelled%'").fetchone()[0]
            print('cancelled transitions:',n)
    finally:
        C._stop_process(p);p.communicate()
        if runtime: runtime.outbox._db.close()
PY
```

Observed: `{'events': [], 'nextCursor': '', 'hasMore': False}`; fixture attempt state `reserved`;
stale `409 STALE_PRECONDITION`; cancel `409 STALE_PRECONDITION`; cancelled transitions `0`.
The probe changes no fixture definition and invokes no agent provider. Source T17 itself seeds the same fixture
and checks for one cancellation transition. This pins the current failure to concrete fixture/production
state mismatches instead of reusing the obsolete retry-context function signature from the previous report.

## Rejected candidates and narrowed historical claims

These are rejected hypotheses or explicitly corrected parts of a broader finding, not owner-accepted risks.

| Candidate | Verdict and reason |
|---|---|
| Caddy still proxies its own container loopback | Rejected for this tree; F1 fixed by current Caddy/unit/runbook source and four fresh kit tests. F22 is separate startup configuration evidence. |
| T17 has no isolation or cancel/stale scenarios | Rejected for this tree: temporary root and scenarios were added. Their actual outcomes remain defective in F2; do not delete them. |
| T9 has no inherited listening-socket path | Rejected for this tree; F15 fixed, platform tests execute descriptor reuse and activation guards. No live socket unit deployment claimed. |
| The new brief form still omits its task or uses plan state | Rejected by current editBriefForm source: it supplies task, objective value, run state and confirmation. Only criteria editing remains open in F8. |
| The tunnel exposes the unauthenticated laptop panel | Rejected: checked-in tunnel targets 8766; RemoteHandler accepts only the remote prefix. Fresh remote API/listener tests reject panel routes and unkeyed health. |
| OAuth state cookie must be Strict | Rejected: Lax permits the top-level cross-site callback, the state is bound/consumed once, and the actual session cookie is host-only HttpOnly/Secure/Strict. Auth tests and separate mock browser round-trip pass. |
| Missing edit-brief in the gateway confirmation set bypasses laptop confirmation | Rejected as a bypass: laptop CHALLENGED includes edit-brief and ledger validates the target-bound one-use challenge before effect. Fresh recovery tests cover the laptop boundary. |
| Same-key replay necessarily executes twice | Rejected for the tested ledger path: fresh ledger tests cover replay/conflict/pending. F16 concerns losing the key at the client, not a demonstrated duplicate effect. |
| Current redactor fails to remove named SESSION_SECRET assignments | Rejected: that name is explicitly recognized and tests pass. F14 is about other assignments/bearer values before transfer. |
| Serializing browser tests is enough to make web verification pass | Rejected: current serial test fails the answer-round assertion; strict typecheck independently blocks verify/build. |
| Mock OAuth/panel success proves the real phone session works | Rejected: the mocks supply authenticated:true and a separate SSE path. Probe B tests the actual gateway, exposing F20/F21. |

## Requirement coverage and handoff

R1/R3 have direct passing authentication and private-listener tests; F1 is fixed, while the intended owner
phone flow is blocked by F19/F20 and operational setup by F3/F22. R2/R17 retain F4/F5.
R4/R7 retain F11/F13/F21, with F15's inherited-listener implementation rechecked fixed.
R5/R6/R8 have passing isolated ledger/challenge suites but F2/F7/F9/F16/F17 at boundaries.
R9/R16 have a tested bounded failure-review model but insufficient upstream redaction F14.
R10–R12 have passing isolated dedupe/backoff/bot suites but F2/F6/F10/F12.
R13 has implemented route pins and brief-revision handlers; criteria UI remains F8.
R14 has local fonts/theme/manifest checks and a Chromium panel run that reached its width and review assertions,
but the complete run failed and production build does not pass. R15 has a real history read route and quota UI;
retention and command provenance presentation remain limited (F12/F23).

Return F2 to T17 and F19/F20 to T15a. After remediation, rerun the full frozen commands and independently
audit the resulting tree again; do not repeatedly rewrite the same open findings without changed prerequisites.
All medium/low findings remain recorded and unresolved. Only the owner may accept a risk. No source fix,
deployment, final acceptance, provider-diversity verification or 'task verified' declaration is claimed here.
