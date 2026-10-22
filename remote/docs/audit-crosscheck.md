# T18b — Independent security and specification cross-check

Audited tree: `ddcad27cfc3478f16b366ca15915124ac58b36af`, 2026-10-21.
Auditor: this OpenAI Codex executor, in its isolated `att-0437` worktree.
Only this report and `audit-crosscheck.findings.json` are changed. No risk is accepted on the owner's behalf.
The independent checker determines acceptance; this report does not declare the task verified.

The cancellation defects behind the supplied F31 failure and the newer cancel-attempt repair are **rechecked
fixed**. A rejected pinned retry still persists a route change (F33, medium). There are also unresolved
specification and verification findings: the browser suite fails, and E2E failed once before passing once.
Those failures are not converted to passing evidence by successful builds or file-existence checks.

## Independence, scope and prior attempts

I first read the specification, task definition, implementation and tests, and ran independently authored probes
for command concurrency, OAuth logging, mutation guards, malformed input and notes. Only afterwards did I open
T18's report/ledger to compare hypotheses. I did not copy its 77 verdicts as my own evidence. IDs in this ledger
are local to this cross-check; F31/F32 retain the concurrency identifiers used by the remediation regressions.

Scope includes the full remote implementation against R1–R18, emphasizing the T18 security requirements
R1/R2/R3/R16/R17: gateway OAuth/session/CSRF/rate limiting, laptop keyed API and command dispatch, tunnel/deploy
configuration, redacted failure views, notifications and actual phone consumers. Current source, real loopback
HTTP, synthetic Scheduler stores, browser checks and installed distributions were inspected.

Before any report edit, I read the supplied histories: att-0115 accepted then returned; att-0117 failed with four
high findings; att-0431/0434 failed with F31; att-0432/0435 were cancelled. Their report bodies are not present in
this hydrated worktree or its reachable cross-check file history. The run's available attempt directories contain
only att-0436 and att-0437. I therefore do not invent the old F1–F4 contents or treat old acceptance as current proof.
The current ancestor commits `f562e4279` and `ddcad27cf` supply the retry and cancel-attempt remedies respectively;
both were inspected and tested. The supplied historical M6 URIs were not fetched.

This is a fresh, independently derived second pass. The inherited T18 report identifies an OpenAI coordinator and
an Anthropic review. This attempt also obtained a **fresh Anthropic source review**, without giving it either
auditor's report or findings. Its current receipt, limited source scope and independently checked verdicts are
recorded below; no inherited provider receipt is treated as a fresh invocation.

## Findings and verdicts

The JSON ledger is the complete list of findings confirmed in this pass: **43 findings; 6 high findings rechecked
fixed, 37 open (29 medium, 8 low), zero critical, zero accepted**. This is not a claim that all other T18 findings
were disproved. Each ledger entry gives the affected approved-plan task, evidence and a bounded conclusion.

| IDs | Verdict and scope |
|---|---|
| F30–F32, F34–F36 | High / fixed: installed snapshot packaging, stale retry/cancellation, review prop/build compatibility, gateway field translation, safe native edit aliases/drift checks. Only already-fixed behavior is marked fixed. |
| F33 | Medium / open: a stale retry returns 409 and preserves the newer active task, but writes its pin before validation. Future assignment consumes that durable pin. This does not reopen the repaired claim that the command cancels the newer attempt. |
| F1–F2, F13, F15–F16 | Medium / open: OAuth query logging, incomplete mutation guards, empty wildcard bind, incomplete text redaction and malformed-command exception. No authentication bypass or live credential disclosure was demonstrated. |
| F3–F12 | Medium / open: standalone note, SSE interoperability, offline restart cache/timestamp, retention, stalled/quota predicates, Telegram content/status/polling. |
| F18–F22, F25, F28–F29, F38, F40–F41 | Medium / open: uncertainty replay UX, missing/mismatched controls, route/quota interoperability, install order, real browser/E2E check failures, absent frozen review test and delivery-history visibility. |
| F42–F43 | Medium / open: shared proxy login throttle and terminal-task retry holding the global command lock during its long wait. Independently checked after the fresh provider review. |
| F14, F17, F23–F24, F26–F27, F37, F39 | Low / open: deadline, schema dialect, aggregate throttling, stream revocation, Caddy instructions, production origin fallback, raw errors and epoch command events. |

Notable corrections to inherited hypotheses: this run passes the browser's earlier 360px width assertion and
fails later at `panel-browser.test.mjs:270`, so the old 366px measurement is not repeated as current fact. The native
snapshot works from the installed wheel, not merely from checkout imports. The E2E failure was `2 != 1` at the
post-offline Telegram assertion; its passing rerun does not establish a deterministic fix or the extra event's identity.

| Requirements | Evidence boundary and remaining findings |
|---|---|
| R1–R3: authentication, mutation protection, keyed tunnel boundary | Auth/guard/API/listener/deploy-kit tests pass within loopback fixtures. F1/F2/F13/F23/F24 remain; a live tunnel is untested. |
| R4/R7: live/offline views | Actual snapshot and installed snapshot regressions pass. F4/F5/F6/F12 retain stream, restart-cache, outage-time and polling limitations. |
| R5/R6/R8/R13: commands, preconditions, confirmation, recovery | Ledger, real command and native recovery tests pass; F30–F36 document specific high repairs. F3/F16/F18–F22/F33/F37 remain. No live agent was dispatched. |
| R9: failed-attempt evidence | Native snapshot/review assertions, installed snapshot and review component typecheck/build run. F15/F28/F38 retain redaction and test gaps. |
| R10–R12: event predicates and Telegram | The 52-test gateway suite and real producer/event tests run; E2E is intermittent. F8–F12/F24/F29/F40 retain specific alert, bot, revocation and history gaps. |
| R14: mobile presentation/PWA | Scaffold/PWA/theme/local-font tests pass. Browser width assertion passes this time, but its later review assertion fails (F28); no blanket mobile acceptance is claimed. |
| R15: quotas/history | Keyed read-route and ledger history tests pass; actual native quota windows do not match the phone parser (F41). |
| R16/R17: secrets and request controls | Tracked placeholder unit/env references and mode-600 deploy fixture checks run; synthetic redaction/logging probes expose F1/F7/F15/F37. No credential files are read. |
| R18: existing panel | Native local panel checks plus 28 platform and 43 page regressions pass. This is bounded to those suites, not the entire repository collection. |

## Fresh review by another provider

The methodology's read-only route selector chose provider `claude`, authorized profile `claude-work`, requested
model alias `sonnet`, effort `medium`. The normal review helper would create another worktree, which this task
forbids, so the routed account was invoked in the existing isolated tree with restricted/no-session-persistence
CLI settings. It could not write files or run commands. No audit report or ledger was supplied.

| Invocation | Actual receipt and boundary |
|---|---|
| Restricted source-file review, only Read/Grep/Glob tools | Timed out at **300 seconds**; no report. Not counted as successful review evidence. |
| Narrowed source bundle on stdin, **no tools** | Exit **0**, **93 seconds**, `is_error=false`. CLI metadata reports `modelUsage` key **claude-sonnet-5-5**. The input was the full SPEC and line-numbered auth.py, security.py, server.py, bt_remote_commands.py, app.py lines 1–165 and bt_scheduler_ops.py lines 209–306, at this exact HEAD. It returned three medium findings and explicit limitations. |

This is a focused security/spec source review, not a second claim to have run all tests. The provider explicitly
did not inspect the omitted read routes, stream/upstream/liveness/notification modules, laptop API, edit module,
plan APIs or Scheduler core. This coordinator independently inspected/tested those boundaries as documented above.

| Provider hypothesis | Independent adjudication |
|---|---|
| F1: stale retry writes/clears a pin before Scheduler precondition validation | **Confirmed medium, our F33**, by independently authored Probe E and actual Scheduler pin consumers. The provider also ranks this medium, not a renewed high cancellation defect. |
| F2: retry's long wait holds the global effect lock and delays other commands | **Narrowed confirmation, our F43.** The provider's proposed ordinary live-cancel sequence was not reproduced: actual ops.apply cancellation immediately leaves T1 recovering. A separate valid terminal-task fixture reaches the wait under the same global lock. The probe completes the task through M1, submits matching completed/revision preconditions, and instruments the actual sleep: sleep_seconds=2 and nonblocking lock acquire=false. It stops there rather than waiting 180s; default wait=180 is static evidence. The exact in-flight timeout/delayed-pause timeline was not measured, and UNKNOWN_OUTCOME alone does not prove forbidden offline queuing. |
| F3: proxy-peer login throttling lets anonymous traffic exhaust the owner's bucket | **Confirmed medium, our F42.** Actual HTTP requests representing six distinct forwarded clients yield `[302,302,302,302,302,429]`. Tracked Caddy configuration establishes the reverse-proxy peer topology; no deployed attack is asserted. A repair must establish trusted proxy identity rather than trust arbitrary forwarded headers. |
| One-use challenge, same-key replay, foreign login and stale cancel defenses | Source conclusions agree with the coordinator's passing native/auth/concurrency tests, within their respective limits. Action-binding beyond target/expiry/one-use is not a frozen requirement. |
| CSRF/log-out rejection | **Bounded/corrected:** the existing Origin check rejects foreign-Origin POST, and Strict cookies limit cross-site logout. That does not satisfy exact `X-Flow-Request: 1` or guard the mutating GET route. Probe A keeps F2 open; no command CSRF exploit is inferred. |
| Reopen without expected_task_state, or note possibly registered elsewhere | No demonstrated new high reopen race. The standalone note hypothesis is independently settled by the real dispatcher and Probe B (F3); no alternative registration exists in the inspected call path. |

Every confirmed provider finding is recorded in this ledger; rejected/bounded parts are explained here. No claim
is delegated to an unnamed auditor, and no provider rating is accepted without checking the actual code/path.

## Executed checks

All commands below ran against this tree. Python is the machine's **3.14**; target Python 3.12 execution is not
claimed. Python runtime code has no third-party dependencies. Web dependencies were installed in this worktree
using the existing lockfile: `cd remote/web && npm ci --offline --ignore-scripts --no-audit --no-fund` exited 0,
324 packages. No dependency file was edited, and checks do not install or write inside `node_modules`.

| Command, from repository root unless stated | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=remote/gateway python -m unittest discover -s remote/gateway/tests -q` | Exit 0; 52 tests, 25.904s. An initial invocation without PYTHONPATH failed with 8 import errors; the corrected command is the evidence. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_remote*.py' -q` | Exit 0; 63 tests, 11.020s, including installed health, listener isolation, ledger, events and recovery tests. |
| `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s remote/deploy/tests -q` | Exit 0; 14 tests, **1 skipped**, 11.595s. `caddy validate` is skipped because Caddy is unavailable; systemd static verification and browser cookie checks run. No live deployment occurred. |
| `cd remote/web && npm run verify` | Exit 1. ESLint and TypeScript pass; 14/15 tests pass, zero skips. Failure: `real failure review should render CAUSA`, line 270. The chained build is not reached. |
| `cd remote/web && npm run build` | Final sequential invocation exits 0, emits `/` and `/review`. An earlier standalone build overlapped E2E's `.next` build and failed `ENOENT ... pages-manifest.json`; that orchestration collision is disclosed, not attributed to product code. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s remote/e2e/tests -p test_local_e2e.py -q` | First invocation exits 1: 1 test, 23.421s, `test_local_e2e.py:470`, `2 != 1`. Production build completed; OAuth owner/refusal, real stale/cancel commands and offline snapshot assertions preceding that line ran. |
| Diagnostic E2E rerun, same test class/assertions with only `TextTestResult.addFailure` logging added in memory | Exit 0; 1 test, 21.245s. No additional diagnostic output was produced because that run passed. F29 remains open; there was no third attempt to obtain a clean-looking run. |
| Focused Python calls to native `_quotas` and `TelegramBot._send_status` using synthetic provider/snapshot data | Exit 0; quotas return HTTP 200 with list windows/ISO observedAt, while the phone requires object windows/numeric time. The actual bot emits only `Ejecuciones activas:` for a native-dialect active run (F11/F41). No Telegram request is sent. |
| Explicit F31/F32 command below | Exit 0; 2 tests, 0.734s. |
| Probe D, fresh wheel/sdist plus isolated installed HTTP snapshot | Exit 0; installed snapshot regression: 1 test, 1.098s. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_platform.py' -q` | Exit 0; 28 tests, 1.994s. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_page*.py' -q` | Exit 0; 43 tests, 11.426s. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_remote_review.py' -q` | Exit **5**, 0 tests, `NO TESTS RAN`; F38. |

Several passing Python runs emit ResourceWarnings about existing unclosed SQLite/HTTP objects. They are disclosed
without suppressing them or changing assertions. The broad repository test collection, live GitHub OAuth sign-in,
AdvIn/Vercel deployment, real GitHub/Telegram credentials and a deployed 120-second SSE reconnect were not exercised.

The independent probes below use synthetic values only. Exit 0 means they reproduced the stated observation,
including defects; it is not a clean-product verdict. Static findings are explicitly identified in the ledger.

### Probe A — gateway guards and safe synthetic logging capture

Run from repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=remote/gateway python - <<'PY'
import http.client, tempfile, threading
from pathlib import Path
from unittest.mock import Mock, patch
from http.server import ThreadingHTTPServer
from auth import OAuthConfig, OAuthService, SessionStore
from server import make_handler
with tempfile.TemporaryDirectory() as tmp:
    cfg = OAuthConfig('client', 'test-secret', 'synthetic-session-secret-at-least-32',
                      'https://flow.example.test', str(Path(tmp)/'g.db'))
    store = SessionStore(cfg.database_path, cfg.session_secret)
    token = store.create_session('dav033')
    runtime = Mock(); runtime.relay_command.return_value = (200, {'status':'OK'})
    srv = ThreadingHTTPServer(('127.0.0.1',0), make_handler(OAuthService(cfg,store), runtime=runtime))
    thread = threading.Thread(target=srv.serve_forever, daemon=True); thread.start()
    client = http.client.HTTPConnection(*srv.server_address, timeout=3)
    try:
        client.request('POST','/api/remote/v1/commands','{}',
                       {'Cookie':'flow_session='+token, 'Origin':cfg.frontend_origin,
                        'X-Flow-Request':'incorrect-marker'})
        response = client.getresponse(); response.read()
        assert response.status == 200 and runtime.relay_command.call_count == 1
        with patch('server.logger.info') as logged:
            client.request('GET','/api/auth/callback?code=synthetic-code&state=synthetic-state')
            response = client.getresponse(); response.read()
            capture = str(logged.call_args_list)
        assert 'code=synthetic-code' in capture and 'state=synthetic-state' in capture
        client.request('GET','/api/auth/logout', headers={
            'Cookie':'flow_session='+token, 'Origin':'https://foreign.example.test'})
        response = client.getresponse(); response.read()
        assert response.status == 302 and store.get_session(token) is None
        print('A: wrong marker accepted, OAuth query logged, unguarded GET logout reproduced')
    finally:
        client.close(); srv.shutdown(); srv.server_close(); thread.join()
PY
```

Actual observation: wrong-marker POST **200**, one relay call; synthetic query logged; foreign-Origin logout **302**,
session deleted. POST foreign-Origin and missing-marker refusals separately pass the gateway guard suite.

### Probe B — native validation, text redaction, predicates and cache

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:remote/gateway python - <<'PY'
import tempfile, sqlite3
from pathlib import Path
from unittest.mock import Mock
from app import GatewayRuntime
from auth import SessionStore
from config import GatewayConfig
from liveness import LaptopStatus
from notifications import notification_for_event
import bt_remote_commands as commands
import bt_remote_events as events
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    cfg = GatewayConfig('http://127.0.0.1:18765','test-key','test-token','test-chat',root/'g.db')
    laptop = Mock(); laptop.snapshot.return_value = {'schemaVersion':1,'runs':[],
                                                      'generatedAt':'2026-10-21T12:00:00Z'}
    runtime = GatewayRuntime(cfg,laptop=laptop,sender=lambda _:None)
    runtime._refresh_active_run_cache(); runtime.liveness.status = LaptopStatus.OFFLINE
    replacement = GatewayRuntime(cfg,laptop=laptop,sender=lambda _:None)
    replacement.liveness.status = LaptopStatus.OFFLINE
    assert runtime.web_snapshot() is not None and replacement.web_snapshot() is None
    store = SessionStore(str(root/'sessions.db'),'synthetic-session-secret-at-least-32')
    store.create_session('dav033',now=0); store.create_session('dav033')
    with sqlite3.connect(store.database_path) as db:
        assert db.execute('SELECT count(*) FROM sessions WHERE expires_at<10000000').fetchone()[0] == 1
    ledger = commands.Ledger(root/'commands.db')
    malformed = {'idempotency_key':'synthetic-command-001','command':'pause','origin':'web',
                 'params':{},'precondition':{'state':'running'}}
    try:
        ledger.submit(malformed,commands.dispatch_handlers(),lambda _: {'state':'running'})
    except KeyError:
        pass
    else:
        raise AssertionError('recheck malformed-command finding')
    note = {**malformed,'target':'demo/REQ-001','command':'note'}
    assert ledger.submit(note,commands.dispatch_handlers(),lambda _: {'state':'running'})['code'] == 'COMMAND_NOT_IMPLEMENTED'
    values = {'LAPTOP_ORIGIN':cfg.laptop_origin,'FLOW_GATEWAY_KEY':'test-key',
              'TELEGRAM_BOT_TOKEN':'test-token','TELEGRAM_CHAT_ID':'test-chat',
              'GATEWAY_DATABASE':str(root/'g.db'),'GATEWAY_BIND':''}
    assert GatewayConfig.from_env(values).bind_host == ''
    for value in ['{"FLOW_GATEWAY_KEY": "synthetic-secret-value"}',
                  'postgres://synthetic_user:synthetic_password@db.test/db']:
        assert events.redact(value) == value
    feed = events.build_events({'quotas':[{'profile':'one','exhausted_until':'future',
        'observed_at':'2026-10-21T12:00:00Z'},{'profile':'two'}]})
    assert any(event['type']=='quota.exhausted' for event in feed)
    assert events.STALL_SECONDS == 900 and cfg.request_timeout == 5
    message = notification_for_event({'type':'attempt.failed','id':'synthetic-event',
        'dedupeKey':'synthetic-event','target':{'req':'REQ-001','taskId':'T1'},
        'data':{'failure':'synthetic-cause'}})[1]
    assert 'synthetic-cause' not in message and '/review' not in message
    row = {**note,'command':'pause','received_at':'2026-10-21T12:00:00Z','outcome':'{}'}
    assert events.build_events({'commands':[row]})[0]['occurredAt'] == '1970-01-01T00:00:00Z'
    runtime.outbox._db.close(); replacement.outbox._db.close()
    print('B: cache, retention, validation, redaction, predicate and timestamp gaps reproduced')
PY
```

All those observations reproduced. The additional static polling/retention/phone traces in the ledger name the
actual producer and consumer; they are not inferred from a provider's report alone.

### Probe C — SSE URL and revoked session

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=remote/gateway python - <<'PY'
import http.client, tempfile, threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from auth import OAuthConfig, OAuthService, SessionStore
from server import make_handler
from stream import StreamHub
with tempfile.TemporaryDirectory() as tmp:
    cfg = OAuthConfig('client','test-secret','synthetic-session-secret-at-least-32',
                      'https://flow.example.test',str(Path(tmp)/'g.db'))
    store = SessionStore(cfg.database_path,cfg.session_secret)
    token = store.create_session('dav033')
    hub = StreamHub(); hub.update_snapshot({'schemaVersion':1,'runs':[]})
    srv = ThreadingHTTPServer(('127.0.0.1',0),make_handler(OAuthService(cfg,store),hub=hub))
    thread = threading.Thread(target=srv.serve_forever,daemon=True); thread.start()
    connection = http.client.HTTPConnection(*srv.server_address,timeout=3)
    try:
        headers = {'Cookie':'flow_session='+token}
        connection.request('GET','/api/remote/v1/events/stream?after=ev_1',headers=headers)
        response = connection.getresponse(); response.read(); assert response.status == 404
        connection.request('GET','/api/remote/v1/stream',headers=headers)
        response = connection.getresponse(); assert response.status == 200
        store.delete_session(token)
        hub.publish({'schemaVersion':1,'id':'synthetic-event','type':'run.finished'})
        data = b''
        while b'event: event' not in data:
            data += response.fp.readline()
        print('C: phone URL 404; revoked existing session still receives named stream event')
    finally:
        hub.close(); connection.close(); srv.shutdown(); srv.server_close(); thread.join()
PY
```

Actual observations: phone stream URL **404**; native stream **200**, and an event is delivered after revocation.

### Probe D — installed snapshot, not checkout imports

```bash
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
from pathlib import Path
import subprocess, sys, tarfile, zipfile
root = Path.cwd(); sys.path.insert(0,str(root/'tests/migration'))
import installed_wheel
installed = installed_wheel.get()
required = {'bt_remote_api.py','bt_remote_edit.py','bt_route_pins.py',
            'bt_remote_snapshot.py','bt_scheduler_projection.py'}
with zipfile.ZipFile(installed.wheel) as archive:
    assert required.issubset({Path(name).name for name in archive.namelist()})
with tarfile.open(installed.sdist) as archive:
    assert required.issubset({Path(item.name).name for item in archive.getmembers()})
code = '''
import pathlib, runpy, sys, unittest
site=pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0,str(site))
import bt_core, bt_remote_api, bt_remote_snapshot, bt_scheduler_projection
namespace=runpy.run_path(sys.argv[2])
suite=unittest.TestSuite([namespace['RemoteApiTests']('test_snapshot_uses_shared_now_frame_and_exposes_rejected_review_attempt')])
result=unittest.TextTestRunner(verbosity=2).run(suite)
for name,module in list(sys.modules.items()):
    if name.startswith('bt_') and getattr(module,'__file__',None):
        assert pathlib.Path(module.__file__).resolve().is_relative_to(site),name
raise SystemExit(not result.wasSuccessful())
'''
result = subprocess.run([str(installed.python),'-I','-c',code,str(installed.site),
    str(root/'skill/scripts/tests/test_remote_api.py')],cwd=installed.work,
    capture_output=True,text=True,timeout=90)
print(result.stderr); assert result.returncode == 0
print('D: fresh wheel/sdist membership and installed-only HTTP snapshot pass')
PY
```

Actual result: archives contain all five modules; isolated installed HTTP snapshot test passes. This does not
claim every remote endpoint or live deployment was tested from an installation.

### Probe E — stale retry and the residual pin write

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python - <<'PY'
import json, os
from unittest.mock import patch
import bt_remote_api as api
import bt_remote_commands as commands
import bt_route_pins as pins
import bt_scheduler_ops as ops
from test_remote_recovery import RemoteRecoveryTests, candidate
from test_remote_commands import FakeHandler
case = RemoteRecoveryTests(); case.setUp()
try:
    module, rdir, harness = case.real_blocked_run()
    request = case.request(route='route-a'); request['precondition']['revision'] = 1
    def advance(target, command, params):
        observed = commands.target_state(target,command,params)
        assert observed['state'] == 'blocked'
        harness.core.reopen('T1','scheduler','synthetic concurrent progress')
        harness.core.step()
        return observed
    handler = FakeHandler(json.dumps(request).encode())
    with patch.dict(os.environ,{'FLOW_GATEWAY_KEY':'test-gateway-key-0123456789',
         'BITACORA_ROOT':str(case.root)}), patch.object(module,'ROOT',case.root), \
         patch.object(api,'_target_state',advance), \
         patch.object(pins,'candidates_for',return_value=(candidate(),)), \
         patch.object(ops,'stop_owner',return_value=0), \
         patch.object(ops,'resume',return_value='mock resumed'):
        api.route_post(handler)
    status, result = handler.sent
    assert (status,result['code'],harness.state('T1')) == (409,'STALE_PRECONDITION','active')
    assert pins.get(rdir,'T1') == {'route':'route-a'}
    print('E: stale retry rejected, newer task preserved, durable route pin nevertheless changed')
finally:
    case.tearDown()
PY
```

Candidates and process lifecycle are stubbed to keep this local and unpaid; the M1 store, progression, ledger,
pin persistence and native POST dispatch are real. This demonstrates F33 without inferring a new cancellation.

The separate cancel regression uses a real HTTP listener and asserts that no agent-kill callback runs:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest \
  test_remote_commands.EntryPointTests.test_f31_route_post_rejects_stale_retry_after_scheduler_starts_new_attempt \
  test_remote_commands.EntryPointTests.test_f32_native_http_rejects_cancel_attempt_that_progressed_after_precondition_read -v
```

## Rejected and bounded hypotheses

| Hypothesis | Independent disposition |
|---|---|
| F31 still allows stale retry to cancel a newer attempt | Rejected on this tree by the explicit regression and Probe E. The residual pin effect is separately retained at medium. |
| Cancel-attempt still acts after dispatched changes to running | Rejected by the real HTTP F32 regression, including unchanged running state and no kill call. |
| Installed health passing alone proves snapshot packaging | Rejected as an evidence standard; Probe D independently executes the installed snapshot and pins every bt_ import to the installed site. |
| A non-1 marker proves command CSRF or foreign-Origin POST bypass | Not established. Actual wrong/absent Origin tests reject POST; F2 records the exact marker and logout contract gaps only. |
| Any GitHub user can authenticate, OAuth state can replay, or remote laptop API needs no key | Rejected within tested boundaries: owner/refusal, cookie-bound single-use state, keyed API and remote-only listener tests pass; the loopback/tunnel topology is explicit in the unit and architecture. No live provider or tunnel is certified. |
| OpenAI/Claude credentials are required on AdvIn | Not supported by the selected control-plane architecture; agents execute on the laptop. Only tracked placeholder configuration and synthetic test values were inspected. |
| Missing phone criteria UI means native edit aliases/drift safeguards still fail | Rejected by actual native recovery tests. F19 retains only the phone defect; no silent title overwrite was demonstrated. |
| The route-pin consumer is missing | Rejected by the actual Scheduler adapter's bt_route_pins.get/narrow calls. This consumer is why F33 is a durable effect. |
| The E2E count proves a particular duplicate-delivery or cross-run identity bug | Not established: first run failed, second passed, and the extra message was not captured. F29 records the unresolved check failure rather than inventing a root cause. |
| A successful build makes npm run verify pass | Rejected. F28 remains open and the complete failing command is disclosed. |
| Numeric GitHub identity, action-bound signatures or Telegram group-sender rules are required | Not frozen requirements: SPEC explicitly names login dav033, a target-bound/expiring challenge and configured chat_id. No exploit is inferred from additional hardening ideas. |

## Handoff and artifact checks

No source, tests, deployment, configuration, plan or primary-audit files were changed. No push, merge, rebase,
service restart, real notification or secret access was performed. Test-only servers were stopped by their fixtures.
This report is the durable handoff inside the two-file write allowance; shared project memory outside this worktree
was not edited. Open findings stay open for the owner/orchestrator; none is marked accepted.

The task's three supplied acceptance commands are identical: `test -s remote/docs/audit-crosscheck.md`. All three
were executed individually and exited 0. JSON/schema-field, uniqueness, fixed-evidence and status checks also pass;
the ledger has no self-accepted risk. All six executable Bash fences above were extracted from this exact report
and run sequentially: six exit-0 results, including reproduction of the open defects. The installed snapshot and
two concurrency regressions also pass in that replay. `git diff --check` exits 0 and final status shows only the
two allowed untracked report files. These existence/format checks establish artifacts, not security or end-to-end
correctness. Remaining work includes the open findings, unavailable Caddy validation, target-Python testing and
independent acceptance. The fresh focused provider receipt is recorded above, including its first timeout.
