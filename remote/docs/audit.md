# Independent security and specification audit — T18

**Rework required: five high findings remain open: F2, F19, F20, F24 and F26.**
The audit is read-only. Their fixes belong to the prerequisite tasks named in the ledger; no source, test or
configuration is changed here. The three report-existence checks do not establish substantive acceptance.

Audited tree: `e4b5617454199e151d8eb1f606ae343bdbe9bf75`. Date: 2026-10-20.
Auditor: Codex / OpenAI, in its isolated T18 worktree. A fresh audit session is evidenced; **another-provider
coverage is not established**. No second provider was invoked, and neither commit authors nor requested model
aliases prove provider diversity. The scheduler must resolve that task-assignment requirement; this report does
not claim it fulfilled or substitute another auditor's coverage for its own.

## Retry history and resolution of the carried overlap

Read the supplied #6–#11 attempt outcomes and reachable report/ledger history: att-0180 (`e8730609`), att-0185
(`dcfc5a59`), att-0198 (`13d914a6`), att-0201 (`15f1a318`) and att-0202 (`088cefb3`). att-0181 was cancelled;
the five omitted older attempts and raw m6 evidence URI contents are unavailable here. Earlier results are context,
not current verification. Attempts #8–#10 repeated the same F1/F2; repeating their reports cannot repair source.

The worktree started clean. Both requested audit files were opened; **neither contained literal conflict markers**.
The overlap is semantic: the carried att-0202 report describes an older tree, whereas the new prerequisites change
19 implementation/test/configuration files relative to `088cefb3`. This report and ledger replace stale conclusions,
retain all inherited F1–F23 identities and add F24–F27 for confirmed gaps. No implementation was rewritten/deleted.
The new cache timestamp preservation, owner-keyed quota, original five-module package inclusion, history normalizer,
failed-history review handling and sample-review label are preserved in the inspected tree and acknowledged below.

There are 27 ledger entries: two rechecked fixes (F1, F15), five open high, eighteen open medium and two open low.
No finding is accepted. Partial fixes remain open with the corrected and remaining portions distinguished.
The early att-0180 ledger used F1/F2/F14 for different defects; those historical labels are explicitly mapped in the
remediation table below, rather than silently confused with the retained att-0202 IDs.

## Frozen scope and method

Read the full SPEC and PLAN.md plus the task objectives, acceptance criteria and verification instructions in
PLAN.json, including the real-ledger cancel/stale/once-only-notification T17 scenarios and the remediation tasks.
Audited the private listener/key boundary, OAuth/session/Origin/rate-limit/logging paths, ledger/preconditions and
dispatchers, recovery, snapshots/events/review, gateway polling/cache/SSE, Telegram rules/outbox/bot, actual phone
consumers versus mocks, installation artifacts and deployment instructions. M6 provisioning/deploy/credential/live
smoke tasks T20–T24 are future scope, so their production receipts are not asserted missing from completed work.

Only `remote/docs/audit.md` and `remote/docs/audit.findings.json` are deliverable edits. All probe identities,
credentials and HTTP requests are synthetic/loopback. Suites were run in isolated subprocesses with BITACORA_ROOT
set to empty temporary directories before imports; packaging uses a temporary source copy and isolated venv.
No real credential file, live bitácora state, personal browser, SSH host or production service was accessed or
changed; no other implementation worktree was inspected. Test/install/build artifacts remain ignored. No external bitácora edits are made under this
task's explicit two-file/read-only boundary; this report records the session and handoff.

Environment: Python 3.14.7 and Node 24.21.0. Target Python 3.12 was not available/tested.
`cd remote/web && npm ci --offline`: exit 0, 320 packages installed; lockfile unchanged. Its cached advisory
output is not a live vulnerability assessment. No installation is performed by an added acceptance check.

## Fresh verification

Commands below are from the repo root unless prefixed by a working directory. Wildcard unittest runs execute all
of the frozen per-file prerequisite commands' tests, including the new regressions; duplicate plan commands share
that one execution. No skipped test was reported by these suites.

| Command | Actual result |
|---|---|
| `cd remote/gateway && python -m unittest discover -s tests -p 'test_*.py'` | Exit 0; 36 tests, 11.778 s; SQLite ResourceWarnings. |
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py'` | Exit 0; 56 tests, 11.039 s; includes the installed-wheel health test; SQLite ResourceWarnings. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` | Exit 0; 25 tests, 2.005 s; inherited-listener regressions executed. |
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_page*.py'` | Exit 0; 43 tests, 11.463 s; local panel pages. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 0; 4 tests, 0.157 s. Caddy absent: structural fallback, not actual Caddy syntax validation. |
| `sh remote/deploy/deploy.sh --check` | Exit 0; `deployment topology: 172.20.0.1:8790`. |
| `cd remote/web && npm run verify` | Exit 2; lint passes, typecheck emits 9 diagnostics (F19); nested tests/build not reached. |
| `cd remote/web && npm test` (separate diagnostic because verify stops first) | Supervisor cutoff at 180 s, elapsed 180.098 s; partial output: two mock tests pass, OAuth browser fails at 16.003 s, panel times out at 90.001 s. No final totals and no passing web-suite claim. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 1; 0 tests, 7.724 s. Actual `npm run build` fails on duplicate `refreshCommandHistory`; no built-web scenario runs. |
| Report probes A, B, C | Each exits 0; observed defects listed below. B adapted to the new `_update_laptop_status` method and shows the cache timestamp subdefect corrected. |
| Report probe D | Exit 0; wheel and sdist lack `bt_remote_preconditions`; both installed planning-state calls raise ModuleNotFoundError. |
| Report probe E | Exit 0; authoritative recovering maps to rejected; real API retains rejected/history but has no activeAttempt; phone guard allows failed only. |
| `python -m json.tool remote/contract/command.schema.json` and event schema equivalent | Each exits 0; syntax checks only, not producer/consumer schema conformance. |
| `test -s remote/docs/audit.md` (three identical acceptance checks) | Exit 0 for all three; document existence only. |
| Ledger/report consistency, nonempty ledger, conflict-marker scan and `git diff --check` | Exit 0; 27 unique IDs, matching report verdicts/evidence, no accepted risks, no conflict markers or whitespace errors. Final git status lists only the two authorized audit documents. |

The browser test supervisor hit its deadline; its immediate npm process was killed by subprocess timeout. Subsequent
PID-specific checks found the known test, Next dev and Next server descendants already exited; no broad kill was
used. Browser tests were not retried against the same noncompiling source. E2E ran after that check, without a
concurrent web build. Complete legacy-repository tests, live Caddy/Docker connectivity, OAuth/Telegram accounts,
Vercel rewrite/SSE lifetime, PWA install and full 44 px touch-target measurements were not run. No network secrets
scanner or fresh dependency-advisory service was invoked; no claim of a complete credentials/vulnerability scan.

## Findings and verdicts
### F1 — high / fixed — The prior Caddy container-loopback upstream defect is corrected in the supplied prerequisite tree.

Tasks: `T16`.

R1/R3/R4. Caddy, unit and runbook now agree on the host Docker bridge. This closes the former container-loopback upstream defect, not operational readiness (F3/F22).

Evidence: cd remote/deploy && python -m unittest discover -s tests -p test_kit.py: exit 0, 4 tests in 0.157 s, including Caddy host-bridge upstream and unit bind assertions. sh remote/deploy/deploy.sh --check: exit 0, deployment topology: 172.20.0.1:8790. Real Docker connectivity was not exercised; F3/F22 remain separate.

### F2 — high / open — The E2E fixture still yields no failure event and its supposedly valid cancel command pins running against a reserved attempt; full E2E also stops at the web build.

Tasks: `T17`.

R5/R6/R10/R11 and T17. Keep the newly added isolation and cancel/stale assertions. Seed a truly running attempt and authoritative exhausted failure facts, then run the actual built-web suite after F19. The current M5 action is retry, so suppressing its alert is correct; weakening that rule to pass this fixture would be wrong.

Evidence: cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py: exit 1, 0 tests in 7.724 s; setUpClass npm run build fails on duplicate refreshCommandHistory (F19). Fresh report probe C: production fixture events=[], nextCursor=''; att-0001 state reserved; stale and supposedly valid cancel both 409 STALE_PRECONDITION; cancelled transitions=0.

### F3 — medium / open — Runbook still omits installing/configuring the private laptop API and reverse tunnel; public Caddy hostname remains an unexplained placeholder.

Tasks: `T16`.

R3/R7. Install-before-start is corrected. Still document listener/key startup, tunnel installation and the approved sslip.io hostname, with rollback. deploy.sh also prints host-Caddy reload instructions although Caddy is containerized.

Evidence: Current remote/docs/runbook.md Go-live steps 1-5 cover host gateway and Docker Caddy only; no serve-remote startup, laptop FLOW_GATEWAY_KEY loading, or tunnel installation/start. Caddyfile uses flow.example.com instead of the approved sslip.io hostname; runbook never instructs substitution.

### F4 — medium / open — Request logging still writes OAuth code/state query values into the status field.

Tasks: `T11a`.

R16/R17. Log the numeric response status, not args[0] (the request line); keep safe path logging. Probe A uses synthetic code/state only.

Evidence: Report probe A, exit 0: status=GET /api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE HTTP/1.1. server.py log_message takes args[0], the full request line, as status.

### F5 — medium / open — GET logout bypasses mutation guards, and the CSRF marker accepts any nonempty value rather than 1.

Tasks: `T11a`, `T15a`.

R2. Require marker value 1 and matching Origin for a session mutation; update the web logout action. SameSite=Strict limits browser cross-site cookie delivery; this finding does not demonstrate a cross-site authenticated command bypass.

Evidence: Report probe A, exit 0: wrong marker POST 200; foreign Origin logout 302; session retained False. server.py uses bool(request_marker); page.tsx still links GET /api/auth/logout.

### F6 — medium / open — Telegram retry and alert action/deep-link integration are missing; the previous bad retry envelope was removed rather than repaired.

Tasks: `T14a`, `T14b`.

R10/R12. Owner-only /estado and pause/resume callbacks exist and pass isolated tests. Retry removal does not satisfy the specified retry action. Alerts still omit run/task/cause, working full review URL and inline safe actions. Import the intended validation exception rather than raising NameError.

Evidence: Report probe B: submit_telegram_command(retry) raises NameError because CommandValidationError is not imported; app.py allows only pause/resume. telegram_bot.py _send_status constructs only pause/resume callbacks; notifications.py TelegramSender sends chat_id/text only, no reply_markup, and notification_for_event produces at most a fragment, not a frontend URL.

### F7 — medium / open — The advertised note command remains accepted by validators but has no laptop dispatcher.

Tasks: `T5a`.

R5/R13. Retry reasons already persist operator notes. The standalone command is still advertised in both command validators but has no dispatch owner; the removed UI note form does not implement it.

Evidence: Report probe B, exit 0: GatewayRuntime._web_command(validate_command(note)) -> real Ledger/dispatch_handlers -> COMMAND_NOT_IMPLEMENTED. note is still in both command enums.

### F8 — medium / open — Task brief editing now supplies the task and run precondition, but the phone still cannot edit acceptance criteria.

Tasks: `T15f`.

R13. Task identity, run-state precondition and visible editing for failed/blocked tasks are corrected. Acceptance-criteria editing is still absent. Rejected production task handling is separately F26.

Evidence: Current page.tsx editBriefForm sends task, field='objective', value and run.state; renderTask shows a brief textarea for failed/blocked tasks. No acceptance_criteria editing field or selector exists. bt_remote_commands.dispatch_edit_brief supports acceptance_criteria.

### F9 — medium / open — Run-level Reabrir ejecución still sends no task to a dispatcher that requires one.

Tasks: `T15d`.

R5. Task-level reopen has taskId. The run-level button does not, while dispatch_run_command requires params.task. Supply task selection or remove the unsupported action.

Evidence: Report probe B: dispatch_run_command('reopen', 'demo/REQ-001', {}) raises reopen requiere params.task. page.tsx run-level commandForm('reopen', {kind:'run',...}) supplies no taskId.

### F10 — medium / open — An ordinary plan waiting for approval still emits no plan.waiting event without a scheduler decision.

Tasks: `T6`.

R10. Existing decision-derived plan.waiting events do not cover an ordinary plan in review. Derive a stable approval-waiting event independently of scheduler decision requests.

Evidence: Report probe B: decision_events([{project:'demo',req_id:'REQ-001',plan_status:'review',decisions:[]}]) returns []; route_get events calls decision_events(plans) and from_snapshot(runs, rounds), which has no plans input.

### F11 — medium / open — Restart still loses the cached snapshot and resets SSE IDs without a resynchronization protocol.

Tasks: `T12`.

R4/R7 and reconnect edge case. Persist last good snapshot and cursor continuity or provide an explicit restart resynchronization path. Notification dedupe persistence is separate from snapshot/replay durability.

Evidence: Report probe B: two GatewayRuntime instances with one database yield snapshot before/after restart True/None; a new stream with event 1 returns [] after old Last-Event-ID 1. HTTP _stream_events has no reset event/protocol.

### F12 — medium / open — Gateway event history, delivered/dropped outbox/history and abandoned expired sessions remain unbounded.

Tasks: `T11`, `T12`, `T14a`.

SPEC disk/90-day retention edge case. Bound replay memory and prune retained history while preserving necessary dedupe guarantees. The current endpoints also load complete command ledgers.

Evidence: Report probe B: stream deque.maxlen None; expired session count 1 after a later login. Source inspection: NotificationOutbox has no 90-day pruning/deletion; SessionStore prunes only a session whose token is presented.

### F13 — medium / open — The cachedAt rewrite is corrected, but the gateway still exposes no stable outage-start timestamp and the phone omits sin conexión desde HH:MM.

Tasks: `T12`, `T15b`.

R7. Preserve the new cachedAt behavior. Expose a stable wall-clock offlineSince and render the outage-start time; checkedAt changes per probe and is not that time.

Evidence: Fresh report probe B: failed-probe cachedAt changed=False after _update_laptop_status; that subdefect is corrected. stream.update_laptop_status replaces laptop with online/checkedAt for each probe; no offlineSince is serialized. page.tsx banner remains LAPTOP SIN CONEXIÓN without the outage-start time. Gateway stream tests pass, including offline status and checkedAt.

### F14 — medium / open — Laptop redaction still misses provider API-key assignments and bearer authorization text before transmission.

Tasks: `T7`, `T6`.

R9/R16 and T7 redaction acceptance. Named gateway/OAuth/session/Telegram assignments are filtered. Provider keys and Authorization bearer text still cross the laptop boundary; frontend redaction happens after transmission.

Evidence: Report probe B: redact('OPENAI_API_KEY=SYNTHETIC Authorization: Bearer SYNTHETIC') returns both values unchanged. bt_remote_api applies this redactor to review/events; _SECRET_NAMES lists only four credential names.

### F15 — medium / fixed — The earlier absence of an inherited-listener path is corrected in the supplied prerequisite tree.

Tasks: `T9`.

R7/R18. Inherited systemd descriptor reuse and activation guards pass. No real socket unit installation or live restart is claimed.

Evidence: cd skill/scripts && python -m unittest discover -s tests -p test_platform.py: exit 0, 25 tests in 2.005 s, including test_web_server_reload_uses_the_inherited_listener and test_systemd_listener_requires_its_activation_environment. create_http_server adopts the inherited systemd descriptor; ensure_server uses the unit. No live service was restarted.

### F16 — medium / open — The web still discards unknown-outcome envelopes and generates a fresh key on every retry.

Tasks: `T15d`.

R6 and suspended-mid-command edge case. Retain the exact envelope and idempotency key for reconciliation/retry. No duplicate production effect is asserted; the real ledger replay tests pass.

Evidence: Current page.tsx sendCommand keeps only the returned message, not the command/idempotencyKey; commandForm, roundForm, decisionForm, retryTask and editBriefForm create a new web UUID for every submission.

### F17 — low / open — Published command/event schemas still disagree with production dialects, field names and key limits.

Tasks: `T3`.

T3/R3/R5/R6/R10. Validate real produced/consumed envelopes, not only JSON syntax. Public schema omits answer-decision, specifies string route and singular answer; runtime dialects differ. No current task.progress/task.completed producer is claimed.

Evidence: Report probe B: gateway accepts a 121-character key rejected by laptop's 120 limit; produced run.finished target lacks kind/project/req required by the referenced schema. Source schemas omit answer-decision, specify string route rather than the current route object, and require answer while the web now submits answers.

### F18 — medium / open — Default browser verification shares Next.js output and does not terminate successfully; the round assertion still expects answer while the phone sends answers.

Tasks: `T15`, `T15e`.

T15/T15e. Keep bounded test shutdown and isolate/serialize Next output. Align the stale answer assertion with the agreed answers collection. The observed browser failures cannot isolate a shared-output race while F19 prevents app compilation.

Evidence: cd remote/web && npm test: stopped by the auditor's 180 s supervisor (180.098 s); before cutoff TAP reported two passing mock tests, OAuth failure at 16.003 s, panel timeout at 90.001 s; no complete totals. Both browser files spawn next dev in the same cwd/.next. panel-browser.test.mjs still asserts command.answer; page.tsx sends answers. Current compilation errors prevent attributing this run to an output race or claiming the old assertion was reached.

### F19 — high / open — The integrated web fails strict typechecking and production compilation: missing FailureReview type, invalid Attempt predicate and duplicate incompatible command-history implementations.

Tasks: `T15a`, `T15c`, `T15d`.

T15/T15a/T15c/T15d. Resolve the source overlap without discarding either history behavior: keep origin/target/type/time and one compatible reader, restore the review type, and correct Attempt narrowing. No strictness suppression or test weakening. The audit cannot perform these source edits.

Evidence: cd remote/web && npm run verify: exit 2 after lint passes; tsc reports 9 diagnostics: TS2304 page.tsx:36/:57, TS7006 :83 twice, TS2677 :130, TS2322 :135, TS2451 :227/:251, TS2353 :260. T17 invokes the actual npm run build: exit 1, webpack Identifier 'refreshCommandHistory' has already been declared; 0 E2E tests run.

### F20 — high / open — Successful real OAuth sessions cannot load the phone panel because the gateway and web disagree on the session response.

Tasks: `T15a`.

R1/R4. Align the real session producer and consumer, then run an authenticated React panel against the real gateway. The mock payload and E2E HTTP session assertions do not exercise this load branch.

Evidence: Fresh report probe B: real authenticated GET /api/auth/session -> 200 {login:'dav033'}. page.tsx load still requires parsedSession.authenticated to be boolean and throws Respuesta de sesión inválida; its initial session===null branch does not render this error. The mock supplies authenticated:true. Runtime browser confirmation is blocked by F19; the real HTTP/consumer contract mismatch is independently reproduced.

### F21 — medium / open — The real phone feed cannot connect or decode production events despite mock SSE coverage.

Tasks: `T4a`, `T6`, `T15b`.

R4 and SSE reconnect. Align endpoint, cursor startup/reconnect and target dialect. Gateway serves events while the phone opens events/stream, snapshot cursor is empty, and events use run/task instead of project/req/taskId. Normal flow activity is also filtered out by the notification projection.

Evidence: Report probe B: authenticated GET /api/remote/v1/events/stream?after=abc returns 404. Gateway streams only /api/remote/v1/events and reads Last-Event-ID, while page.tsx uses the former path/query. Laptop snapshot cursor is always empty, and the web refuses to create EventSource without a truthy snapshot cursor. Production event targets use run/task, but parseFlowEvent requires project/req and reads taskId/task_id.

### F22 — medium / open — Filling the required env-example values still leaves blank optional settings that prevent gateway startup.

Tasks: `T16`.

T16 operability. Omit unset optional values or supply non-secret defaults in the configuration loader; the test requiring all assignments blank does not prove the documented filled-required example starts.

Evidence: Report probe B: parsing the checked-in example after filling required synthetic values and GATEWAY_BIND raises Gateway port and timeouts must be numeric; filling numeric settings then raises GitHub OAuth endpoints must use https because blank endpoint assignments override defaults.

### F23 — medium / open — A new command-history normalizer preserves origin, but an incompatible duplicate old implementation remains and still substitutes target/command for origin.

Tasks: `T15d`.

R15. Preserve the newly correct normalizer while resolving the incompatible duplicate. Its old reader still labels target/command as origin and cannot satisfy CommandHistoryItem. This is linked to F19, not a claim that the repaired reader itself loses origin.

Evidence: page.tsx:227 defines a commands-endpoint reader with real origin/type/target/submittedAt; :251 redeclares the same const with a history-endpoint reader constructing origin from target/command and an incompatible at field. npm run verify produces TS2451 at both declarations and TS2353 at :260. Neither a working integrated history nor a runtime provenance fix can be claimed until the overlap is resolved (F19).

### F24 — high / open — Installed remote API still cannot answer decisions or rounds: the package manifest omits the new bt_remote_preconditions dependency.

Tasks: `T18.6`.

R5/R18 and T18.6. Include the sixth dependency and test installed round/decision behavior in isolation. Preserve the five-module manifest and health regression; passing imports for only those modules cannot close a deferred import failure.

Evidence: Fresh report probe D builds wheel and sdist with tests/migration/installed_wheel.py: bt_remote_preconditions.py absent in both. Isolated installed bt_remote_commands.target_state for answer-round and answer-decision each raises ModuleNotFoundError: No module named 'bt_remote_preconditions'. The five original remote modules import and installed health test passes; that partial fix does not include the sixth transitive module.

### F25 — medium / open — The displayed Ver intento fallido link navigates to a static sample review rather than the selected attempt.

Tasks: `T15c`.

R9 and T15c. Keep the sample label, but bind the user action to the selected attempt and actual authenticated review response. The inline review path remains separate and must keep working.

Evidence: page.tsx renderTask links every failed attempt to /review with no attempt identity. remote/web/src/app/review/page.tsx imports reviewFixture directly, never fetches an authenticated attempt review, and displays hardcoded att-0019. It now labels DATOS DE MUESTRA, which avoids presenting sample data as live but does not meet the selected-attempt review requirement; static fixture tests pass without exercising the real review endpoint.

### F26 — high / open — The real rejected task state still hides failure review and recovery controls despite the added failed-state/history handling.

Tasks: `T4a`, `T15c`.

R9/R13; historical att-0180 F2. Support the real rejected vocabulary (and history/reviewAttempt identity) through producer and consumer. Current regression tests use failed, concealing this production case. Repairing TypeScript alone will not make these controls appear.

Evidence: Fresh report probe E: bt_planstatus._SCHEDULER_TASK['recovering']='rejected'; production bt_remote_api._mobile_run preserves that state and emits activeAttempt:null for a non-live rejected attempt, retaining its history. page.tsx review guard requires task.state==='failed'; retry/edit/reopen guards allow failed/blocked only, and no rejected branch exists. bt_remote_views.task_view now returns reviewAttempt, but production _mobile_run does not use it and the phone does not parse it. Current API regression fixture uses failed, not production rejected; F19 independently blocks browser execution.

### F27 — low / open — Command quota is deliberately shared by GitHub login across sessions, rather than maintained per session as R17 specifies.

Tasks: `T11a`.

R17; historical att-0180 F12. Clarify/implement the required per-session limit while preserving authentication-before-throttle and an intentional owner-wide cap if desired. Stronger aggregate throttling is not an authorization flaw and is low severity.

Evidence: Fresh gateway suite: 36 tests pass, including test_command_quota_is_shared_by_owner_across_sessions: 30 commands in owner session A exhaust session B (429); another login remains independent (404 on the test runtime). server.py keys authenticated command/challenge limits by login. This is an aggregate restriction, not an authorization bypass; no owner-approved change to the per-session requirement was found.

## Prior remediation scopes and rejected candidates

Historical labels below belong to the referenced attempt, not the retained current ledger namespace.

| Historical scope or candidate | Fresh verdict and limit |
|---|---|
| att-0180 F1: resolved event cursor stops the feed | The real route's cursor-disappearance regression and gateway-reset regression execute in the passing 56-test laptop suite. Preserve that repair. Restart replay and phone transport remain F11/F21. |
| att-0180 F2: non-live rejected attempt inaccessible | Partial repair only: history and failed-state review anchors were added. Rejected production task remains hidden (F26); alert still has fragment only (F6). |
| att-0180 F3: decision allowlist/translation/state reader | Checkout regressions pass for allowlist, requestId -> request_id and open-decision state. Installed state reader still fails (F24); browser integration is blocked (F19/F20). No end-to-end closure claimed. |
| att-0180 F4: round answers/state | Checkout regressions pass for round-file writes, open-round preconditions and answer -> answers adapter; phone now sends answers. Installed state reader fails (F24) and browser assertion remains stale (F18). |
| att-0180 F14: all five remote modules absent | Those five modules are now packaged and installed health passes. The newly added sixth transitive module is absent (F24); do not erase the partial fix or claim installed planning commands work. |
| att-0180 F12: shared command quota | Reproduced by the new owner-sharing regression. It remains a low per-session spec deviation (F27), not an auth bypass. |
| Older T18.4 task/attempt precondition defect | The retry and cancel member-state regressions execute in the passing laptop suite. Preserve them. F2 is a reserved fixture pinned as running, not proof those readers are wrong. |
| Caddy still proxies container loopback | Rejected for this tree: F1 is rechecked fixed. Actual public connectivity is untested. |
| T17 has no isolation or cancel/stale cases | Rejected: these were added; their fixtures/outcomes remain defective (F2). |
| T9 has no inherited listener implementation | Rejected: F15 is rechecked fixed; 25 platform tests pass. |
| New brief form still omits task or uses plan state | Rejected by current source; criteria UI and rejected-state behavior remain F8/F26. |
| CachedAt still changes on failed health probes | Rejected by fresh probe B: False. Outage-start timestamp still absent (F13). |
| Tunnel exposes the unauthenticated local panel | Rejected: checked-in destination is the separate remote-only 8766 listener; unkeyed health and nonremote routes are refused by passing listener tests. |
| OAuth state cookie must use Strict | Rejected: Lax enables the top-level cross-site callback; state is bound/one-use. The actual host-only session cookie uses HttpOnly/Secure/Strict; backend auth tests pass. Current browser OAuth run fails and is not claimed passing. |
| Edit-brief bypasses destructive confirmation | Rejected as a bypass: laptop CHALLENGED includes edit-brief; one-use target-bound confirmation is checked before effect. Recovery tests pass. |
| Same-key replay must apply the effect twice | Rejected for tested ledger path: replay/conflict/pending regressions pass. F16 concerns the client's discarded key. |
| SESSION_SECRET assignments remain unredacted | Rejected for that named key; fresh HTTP-boundary regression passes. Other key/bearer forms remain F14. |
| Mock OAuth/panel success proves real phone access | Rejected by the actual session payload and mismatched real SSE path (F20/F21). |
| Static review is live attempt evidence | Rejected: explicitly marked sample, loaded from a fixture; the selected-attempt link still needs repair (F25). |

## Requirement coverage and handoff

R1/R3 have direct passing backend authentication/private-listener tests; real phone access remains blocked by
F19/F20 and operational setup by F3/F22. R2/R17 retain F4/F5/F27. R4/R7 retain F11/F13/F21; socket reuse F15 and
cache timestamp preservation were rechecked. R5/R6/R8 have isolated passing ledger/challenge/member-state tests,
but F2/F7/F9/F16/F17/F24 remain at boundaries. R9/R16 have a bounded four-section laptop review model but retain
F14/F25/F26. R10–R12 have isolated deterministic delivery/backoff/dedupe and owner-bot coverage, but
F2/F6/F10/F12 remain. R13 retains criteria editing (F8) and rejected-state recovery (F26). R14 production build
fails and current mobile browser verification does not complete. R15 retains history integration/provenance
(F19/F23) and retention limits (F12).

Return F2 to T17; F19 to T15a/T15c/T15d; F20 to T15a; F24 to T18.6; F26 to T4a/T15c.
Keep all recorded medium/low issues open unless corrected or explicitly accepted by the owner. Re-run the frozen
commands against changed prerequisites, including the actual built-web E2E and installed planning commands.
The substantive criterion **Confirmed high findings are fixed is not met**. Provider diversity, production smoke,
independent final acceptance and any decision to accept risk remain outstanding. No task-verified declaration.

## Reproducible synthetic probes A–C

These are the inherited report probes, re-executed here. Only B's obsolete cache method was adapted to the current
source. A reproduces callback query logging, arbitrary marker acceptance and GET logout. B reproduces note/reopen,
missing approval event, provider/bearer redaction gap, lost restart snapshot/replay, unbounded history/sessions,
contract mismatches, Telegram NameError, session payload/SSE mismatch and env-example startup errors; its
failed-probe cachedAt comparison now returns False. C reproduces the exact T17 fixture failure without building
or replacing the web. These are diagnostics, not replacement passing E2E tests.
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
    runtime.stream.update_snapshot({'runs':[{'state':'running'}]},'2026-10-20T00:00:00Z')
    runtime._update_laptop_status(); first=runtime.stream.snapshot()['cachedAt']
    with patch('app.datetime') as date:
        date.now.return_value=dt.datetime(2026,10,21,tzinfo=dt.UTC)
        runtime._update_laptop_status()
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

## Probe D — installed planning-command dependencies

Run from the repository root. The packaging helper creates and cleans its own temporary copy, wheel, sdist and
isolated venv; it does not install into or edit the source checkout. Its installed health test passes independently.

```bash
python - <<'PYPROBE'
import os, sys, subprocess, tempfile, tarfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path('tests/migration').resolve()))
import installed_wheel
with tempfile.TemporaryDirectory(dir='.') as scratch:
    tempfile.tempdir = str(Path(scratch).resolve())
    installed = installed_wheel.get()
    with zipfile.ZipFile(installed.wheel) as wheel:
        print('wheel missing preconditions:', 'bt_remote_preconditions.py' not in wheel.namelist())
    with tarfile.open(installed.sdist) as archive:
        print('sdist missing preconditions:', not any(
            name.endswith('/bt_remote_preconditions.py') for name in archive.getnames()))
    code = """import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
import bt_remote_commands as commands
import bt_plans_api
for command in ('answer-round', 'answer-decision'):
    with patch.object(commands, '_run_target', return_value=('demo', 'REQ-001', Path.cwd())), patch.object(
        bt_plans_api, 'status_of', return_value={'run': {'authority': 'scheduler', 'status': 'waiting'}, 'plan': {}}):
        try:
            print(command, commands.target_state('demo/REQ-001', command, {'round': 1, 'request_id': 'd1'}))
        except ModuleNotFoundError as error:
            print(command, type(error).__name__, str(error))
"""
    result = subprocess.run([str(installed.python), '-I', '-c', code, str(installed.site)],
        cwd=installed.work, env={'PATH': '/usr/bin:/bin', 'HOME': str(installed.work/'home'),
            'BITACORA_ROOT': str(installed.work/'root'), 'PYTHONDONTWRITEBYTECODE': '1'},
        capture_output=True, text=True, timeout=30)
    print('isolated probe exit:', result.returncode)
    print(result.stdout + result.stderr)
PYPROBE
```

Observed in this audit: both missing-module comparisons True; both commands raise
`ModuleNotFoundError: No module named 'bt_remote_preconditions'`; isolated probe exits 0 because it explicitly
records that expected defect. The two patched collaborators select a planning-state path without starting an
agent or mutating a live plan; the installed dependency import and failure are real.

## Probe E — authoritative rejected-task vocabulary and consumer guards

```bash
python - <<'PYPROBE'
import os, sys, json, tempfile
from pathlib import Path
sys.path.insert(0, str(Path('skill/scripts').resolve()))
with tempfile.TemporaryDirectory(dir='.') as scratch:
    os.environ['BITACORA_ROOT'] = str(Path(scratch).resolve())
    import bt_planstatus, bt_remote_api, bt_remote_views
    state = bt_planstatus._SCHEDULER_TASK['recovering']
    attempt = {'id': 'attempt-rejected', 'state': 'rejected', 'live': False}
    task = {'id': 'T1', 'state': state, 'attempt': attempt, 'history': [attempt]}
    projected = bt_remote_api._mobile_run({'run': 'demo/REQ-001', 'req_id': 'REQ-001',
        'status': 'running', 'tasks': [task]})['tasks'][0]
    print('recovering projects to:', state)
    print('API task:', json.dumps(projected, sort_keys=True))
    print('alternate reviewAttempt:', bt_remote_views.task_view(task)['reviewAttempt'])
    page = Path('remote/web/src/app/page.tsx').read_text()
    print('failed-only review guard:',
        'task.state === "failed" && (task.activeAttempt ?? task.history?.at(-1))' in page)
    print('static sample review:', 'import { reviewFixture }' in
        Path('remote/web/src/app/review/page.tsx').read_text())
PYPROBE
```

Observed: `rejected`; API `activeAttempt: null`, with rejected task/history retained; the alternate projection
provides `reviewAttempt`, but is not used by that API. Both source guard checks return True. Source inspection of
`renderTask` additionally confirms retry/edit/reopen guards only admit failed/blocked. This probe establishes a
producer/consumer mismatch without claiming to execute the blocked React application.
