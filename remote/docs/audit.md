# Independent security and specification audit — T18

**Rework remains required. F2, F26, F32 and F33 are high and open.** The acceptance criterion
“Confirmed high findings are fixed” is not met. This read-only audit changes only this report and
`audit.findings.json`; prerequisite owners must repair the implementation. No risk is accepted here.

Audited tree: `ef3e83a595c4ce541ee9aaa25f96cdcd359905f7` (HEAD at entry), 2026-10-21,
America/Bogota. Primary auditor: OpenAI Codex. Fresh independent other-provider review: Anthropic Claude,
receipt and all dispositions below. Final acceptance belongs to the independent checker.

## Overlap reconciliation and scope

Initial git status/diff were clean. Both supplied documents were opened and scanned: neither contained conflict
markers, despite the carried-result warning. Their conclusions were stale against 20 changed implementation/test
files relative to the previous T18 result `0af07a73e86087e921eff62169ec5db12a5ab68d`.
This report retains all F1–F32 identities and both intents: recheck the new prerequisites while preserving the
previous confirmed defects and repairs. F28 is now rechecked fixed; F26 and F32 still fail at different, later
boundaries. F31's old exposure disappeared with the removal of production streaming; that functional regression
remains F21. New F33 records the omitted command fields; F34 records the deleted frozen verification tests.

Read the full frozen SPEC/PLAN.md and every PLAN.json objective/acceptance/verification. Compared the supplied
attempt outcomes #8–#13 and reachable ledgers/reports at `dcfc5a59`, `13d914a6`, `15f1a318`, `088cefb3`,
`81a29c39` and `0af07a73`. Earlier omitted attempts and raw m6 URI contents were not available in this task.
The earlier 240-second source review and historical receipts are not current-tree verdicts.

The ledger contains **34 findings: 13 rechecked fixed/superseded exposures and 21 open (4 high, 15 medium,
2 low); 0 accepted**. An open medium/low finding is recorded, not an owner-approved risk exception.
Only the two authorized documents are deliverable changes; task notes remain here under the explicit read-only
boundary rather than modifying bitácora, source, tests or configuration.

Reviewed keyed/private laptop listener, OAuth/state/session/Origin/logging/throttling, command translation,
preconditions/idempotency/concurrency, real scheduler recovery, shared snapshot/review/events, gateway polling/cache,
stream integration, notifications/bot, phone consumers versus mocks, installed distributions and deployment kit.
Dynamic requests and state used synthetic loopback fixtures and temporary roots; no real credentials, live project
state, desktop profile, SSH host or deployed service was read or changed. Deployment/go-live remains outside scope.

## Fresh command evidence

Python 3.14.7; Node 24.21.0. Python 3.12 is unavailable. Installed the lockfile first with
`cd remote/web && npm ci --offline`: exit 0, 320 packages; lockfile unchanged. No added verification installs
packages or writes to node_modules. Browser tests/builds ran sequentially.

Python laptop/gateway/local-panel suites used a wrapper setting BITACORA_ROOT to an empty TemporaryDirectory
before discovery/import. The wrapper changes no source and prevents access to the real project registry.
Wildcard/combined discovery includes the frozen individual prerequisite commands; T14's missing test is reported
separately rather than hidden by wildcard discovery.

| Command / execution | Actual result |
|---|---|
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py'` (isolated root wrapper) | Exit 0; 54 tests in 7.885 s, including wheel/sdist/installed preconditions and concurrent ledger regression. |
| `cd remote/gateway && python -m unittest discover -s tests -p 'test_*.py'` (isolated root wrapper) | Exit 0; 45 tests in 13.116 s. Stream replay tests exercise the unconnected StreamHub; this does not prove production SSE. |
| Combined discovery of `test_platform.py` and `test_page*.py` in skill/scripts (isolated root wrapper) | Exit 0; 68 tests in 13.412 s, including listener reload and local-panel regression tests. |
| `cd remote/web && npm run verify` | Exit 0; lint, strict typecheck, 14/14 tests (0 skipped/cancelled; test duration 50.833 s), production build. Browser assertions use the mock gateway. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 1; 1 test in 18.521 s. Build succeeds, then line 401 fails on empty events/cursor (F2). Later assertions are not reached. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 0; 18 tests in 6.638 s, 1 explicit skip: Caddy executable unavailable. Includes browser OAuth/cookie test. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` | Exit 5; 0 tests, `NO TESTS RAN` (F34). |
| `bash remote/deploy/deploy.sh --check`; `bash remote/deploy/rollback.sh --check` | Each exit 0; host bridge topology 172.20.0.1:8790 and rollback unit. No deployment performed. |
| `python -m json.tool remote/contract/command.schema.json`; event-schema equivalent | Each exit 0; syntax only, not semantic schema compliance. |
| `test -s remote/docs/route-pin.md`; architecture.md and contract.md equivalents | Each exit 0. |
| Report probes A–D and F below | Each final execution exit 0; observations are evidence, not a passing product verdict. |
| `test -s remote/docs/audit.md` (all three frozen T18 checks) | Each exit 0; these check existence only. |
| Ledger schema/IDs/status/evidence checks, conflict scan and `git diff --check` | Exit 0; only the authorized report and ledger changed. |

One preliminary Probe B used `laptop=object()` while a new runtime defaults online; its lazy snapshot read raised
AttributeError. That was an audit harness error, not product evidence. The corrected final probe explicitly puts
both synthetic runtimes offline before checking cached restart behavior. The first fresh Anthropic whole-source
request timed out at 240 seconds without a result; the smaller independent boundary review completed below.

Not run: unrelated repository suites, Python 3.12, real Caddy validation/Docker connectivity, deployed OAuth or
Telegram, Vercel rewrite stream lifetime, PWA installation and exhaustive 44 px touch-target measurement.
No live dependency advisory scan was run; npm offline output is not claimed as one. None of these omissions is
reported passing. T17's failure and T14's absent tests remain visible.

## Findings and verdicts

### F1 — high / fixed — Caddy container-loopback upstream is corrected in the audited prerequisites.

Tasks: `T16`. Evidence: cd remote/deploy && python -m unittest discover -s tests -p test_kit.py: exit 0, 18 tests in 6.638 s, 1 skip (Caddy unavailable). bash remote/deploy/deploy.sh --check: exit 0, topology 172.20.0.1:8790; rollback.sh --check: exit 0. No live container connectivity was tested.

### F2 — high / open — Required built-web E2E still fails because its forced-failure fixture emits no failure event.

Tasks: `T17`. Evidence: cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py: exit 1, 1 test in 18.521 s; production build succeeds, then line 401 fails on events=[], nextCursor="". Probe C independently confirms the empty production feed. The fixture seeds one failure below the retry budget and an M5 retry decision; do not weaken production retry-budget alert suppression. Later cancellation, OAuth, offline and notification assertions are not reached.

### F3 — medium / open — The runbook restarts an uninstalled gateway unit on first install and reloads host Caddy although the approved service is containerized.

Tasks: `T16`. Evidence: Source recheck: remote/docs/runbook.md steps 3/4 deploy (systemctl restart) before installing the unit. Step 5 reloads host Caddy although the approved topology uses a Docker container. Private listener/key/tunnel instructions and hostname replacement are present; those historical subclaims remain withdrawn.

### F4 — medium / open — Gateway request logging exposes OAuth code/state query values in its purported status field.

Tasks: `T11a`. Evidence: Probe A: exit 0; callback query code=SYNTHETIC_CODE&state=SYNTHETIC_STATE appears in captured logging. remote/gateway/server.py:38 assigns the request line args[0] to status. Independent Anthropic finding 1 confirms the source defect; primary severity remains medium because no usable session credential or account takeover was demonstrated.

### F5 — medium / open — The mutation marker accepts arbitrary nonempty values, and GET logout clears the cookie without guards or revoking its server session.

Tasks: `T11a`, `T15a`. Evidence: Probe A: exit 0; X-Flow-Request: wrong passes the real HTTP guard (200 with an isolated successful runtime), foreign-Origin GET logout returns 302/clearing cookie, and the token still resolves afterward. server.py:189 checks nonempty marker rather than value 1; logout has no server-side revocation. No Origin bypass for command POST was demonstrated.

### F6 — medium / open — Telegram alerts still omit a working review URL and safe inline actions, and retry callbacks remain unsupported.

Tasks: `T14a`, `T14b`. Evidence: Probe B: exit 0; submit_telegram_command rejects retry with INVALID_COMMAND. Source recheck: app.py:107 permits pause/resume only; telegram_bot.py /estado supplies only those callbacks; notifications.py TelegramSender sends chat_id/text without reply_markup, review URL, task or classified cause. Telegram bot/send suites pass within the 45 gateway tests; they do not establish the missing alert actions.

### F7 — medium / open — The public note command is still advertised and validated without a laptop dispatcher.

Tasks: `T5a`. Evidence: Probe B: exit 0; real Ledger.submit returns COMMAND_NOT_IMPLEMENTED for note. Both command registries and command.schema.json advertise it; dispatch_handlers has no note. Existing retry reason/RUN.notes reuse remains valid, as PLAN.md specifies; it does not execute the advertised standalone command.

### F8 — medium / open — The phone brief form still cannot edit acceptance criteria.

Tasks: `T15f`. Evidence: Source recheck: page.tsx:372-380 always submits field=objective and a string value; renderTask has only a brief textarea. Laptop bt_remote_edit supports acceptance_criteria lists. The current recovering-only form gate and failed reopen are F26; dropped edit fields are F33.

### F9 — medium / open — Run-level Reabrir ejecución supplies no task identity to a task-scoped operation.

Tasks: `T15d`. Evidence: Source recheck: run-level commandForm(reopen, kind:run) has no taskId. bt_remote_commands.TASK_SCOPED, _member_state and dispatch_run_command require params.task; such a run-level command cannot satisfy the member precondition. Task-specific recovery is independently recorded as F26.

### F10 — medium / fixed — Ordinary plans waiting for approval previously emitted no plan.waiting event without a scheduler decision.

Tasks: `T6`. Evidence: Probe B: exit 0; build_events for a review plan with no scheduler decisions emits plan.waiting. cd skill/scripts && python -m unittest discover -s tests -p test_remote_*.py (isolated BITACORA_ROOT wrapper): exit 0, 54 tests in 7.885 s; collect still passes plans to build_events.

### F11 — medium / open — Gateway restart still loses the last snapshot; the replacement replay hub is not integrated into production.

Tasks: `T12`. Evidence: Probe B: exit 0; a runtime with an offline cached snapshot serves it, but a newly constructed runtime using the same database returns None. app.py keeps snapshot_cache only in memory. stream.py now has a bounded StreamHub and resync support, but main.py/app.py/server.py never instantiate or serve it (F21); do not carry forward claims about the removed SnapshotEventStream as current production evidence.

### F12 — medium / open — Delivered/dropped Telegram history and abandoned expired sessions remain unbounded.

Tasks: `T11`, `T14a`, `T5`. Evidence: Probe B: exit 0; creating a new session leaves an expired abandoned row. Source recheck: notifications.py has no 90-day deletion of telegram_outbox/delivery_history; SessionStore expires sessions only on presentation. Laptop Ledger.rows loads the complete history before endpoint slicing. Withdraw the old unbounded production SSE deque claim: it was removed, replacement StreamHub has maxlen=1000 and is unused. Its unbounded subscriber queues are not a demonstrated production exposure.

### F13 — medium / open — No stable offline-start timestamp reaches the phone.

Tasks: `T12`, `T15b`. Evidence: Probe B: exit 0; cached snapshot retains generatedAt while laptop exposes only online=False, with no offlineSince/cachedAt. app.py:211-228 serializes only online; page.tsx:424 says LAPTOP SIN CONEXIÓN without sin conexión desde HH:MM. LivenessMonitor has a monotonic offline_since internally but never translates it into a public wall-clock timestamp.

### F14 — medium / fixed — Laptop-side redaction previously missed provider-key assignments and bearer authorization text before transmission.

Tasks: `T7`, `T6`. Evidence: Probe B: exit 0; synthetic provider-key assignment and bearer value become OPENAI_API_KEY=[REDACTED] Authorization: [REDACTED]. Isolated laptop remote suite: exit 0, 54 tests, including real review response redaction. Snapshot, events and reviews retain the shared recursive redactor; no exhaustive secret-detection claim.

### F15 — medium / fixed — The local panel previously had no inherited systemd listener implementation.

Tasks: `T9`. Evidence: Combined isolated unittest discovery in skill/scripts for test_platform.py and test_page*.py: exit 0, 68 tests in 13.412 s, including inherited-listener reload and activation-environment regressions. No live systemd restart was performed.

### F16 — medium / open — The phone still discards unknown-outcome command envelopes and creates a fresh idempotency key on resubmission.

Tasks: `T15d`. Evidence: Source recheck: page.tsx:275-320 sendCommand retains neither the exact envelope nor UNKNOWN_OUTCOME key. Every form generates a new web UUID. An uncertain HTTP failure is presented as generic Rechazado and resubmission uses a new key. Gateway/laptop replay tests pass but do not reconcile the client. Independent Anthropic finding 5 confirmed after inspecting the full sendCommand implementation.

### F17 — low / open — Public command schema disagrees with production commands, fields and key limits.

Tasks: `T3`. Evidence: Source recheck plus Probe B: schema lacks answer-decision, uses string route and singular answer, and models edit-brief as brief; phone uses route object, answers and field/value. Schema max key length is 128; laptop validate rejects 121 characters (limit 120). JSON syntax checks exit 0 and are not semantic schema validation. Event target normalization remains repaired.

### F18 — medium / fixed — The required browser verification previously failed and asserted obsolete singular round answers.

Tasks: `T15`, `T15e`. Evidence: cd remote/web && npm run verify: exit 0; lint, tsc --noEmit, all 14 tests (0 skipped/cancelled), and next build pass. Test duration 50.833 s. panel-browser.test.mjs asserts plural answers, real {login} dialect, selected review and new five-second mock snapshot polling. These mock tests do not prove real gateway command dispatch.

### F19 — high / fixed — The integrated phone app previously failed strict typing and production build due to overlapping implementations.

Tasks: `T15a`, `T15c`, `T15d`. Evidence: cd remote/web && npm run verify: exit 0, lint/typecheck/14 tests/production build pass. The production build also succeeds inside the fresh T17 execution before F2. One refreshCommandHistory remains; no missing FailureReview or invalid Attempt predicate is reproduced.

### F20 — high / fixed — The phone previously rejected the real gateway's successful {login:'dav033'} session response.

Tasks: `T15a`. Evidence: cd remote/web && npm run verify: exit 0; browser test observes {login:"dav033"} and renders the authenticated panel. Probe A independently observes real gateway HTTP 200 {login:"dav033"}. No production OAuth deployment was exercised.

### F21 — medium / open — Production gateway serves neither SSE route; the replacement tested StreamHub is disconnected from runtime and HTTP.

Tasks: `T12`, `T6`, `T15b`. Evidence: Probe A: exit 0; authenticated GET /api/remote/v1/events/stream?after=abc AND /api/remote/v1/events both return 404. main.py creates GatewayRuntime; app.py never imports/instantiates StreamHub; server.py has no stream handler. StreamHub unit replay/resync tests pass in the 45-test gateway suite but do not cover production. Phone page.tsx:260 still opens the first route, so the feed remains empty; its new five-second snapshot polling does not supply feed events. Laptop feed also filters ordinary flow transitions. Keep the working poll fallback; wire a real stream and explicit cursor/replay adapter.

### F22 — medium / fixed — The earlier env-startup allegation assumed blank optional settings despite the current runbook requiring every uncommented key to be filled.

Tasks: `T16`. Evidence: Probe B: exit 0; fill every uncommented gateway.env.example key with synthetic/standard nonsecret values as runbook step 2 requires; GatewayConfig.from_env and OAuthConfig.from_env succeed with bind 172.20.0.1:8790. Deployment suite exit 0, 18 tests, 1 Caddy skip. No live startup claim.

### F23 — medium / fixed — Overlapping phone command-history implementations previously broke compilation and mislabeled origin.

Tasks: `T15d`. Evidence: cd remote/web && npm run verify: exit 0, including browser history origin/result assertions. Isolated laptop remote suite: exit 0, 54 tests including read-model coverage; gateway suite: exit 0, 45 tests including authenticated reads. One /commands normalizer retains command, target, time, origin and outcome; obsolete incompatible history reader is absent.

### F24 — high / fixed — Installed planning-command preconditions previously failed because bt_remote_preconditions was absent from distributions.

Tasks: `T18.6`. Evidence: Isolated cd skill/scripts unittest discovery test_remote_*.py: exit 0, 54 tests in 7.885 s, including test_installed_wheel_serves_remote_api_and_resolves_round_and_decision_preconditions. It builds wheel/sdist, checks remote modules and exercises installed keyed API and round/decision state readers. This confirms packaging, not gateway public-envelope adaptation (F33).

### F25 — medium / fixed — The failed-task link previously opened only an unrelated static review fixture.

Tasks: `T15c`. Evidence: cd remote/web && npm run verify: exit 0, selected rejected-attempt review browser assertions pass. Isolated laptop remote suite: exit 0, 54 tests including HTTP review against synthetic M6/executor evidence. Probe C sees rejected reviewAttempt att-0001 in the real projection. Task-specific /review links remain; inline failed-only guard does not prevent that separate route.

### F26 — high / open — Rejected-task reopen passes its new precondition alias but fails in the real scheduler; recovery forms still cannot be used end to end.

Tasks: `T5`, `T5a`, `T15f`. Evidence: Probe C: exit 0; real fixture projects rejected, authoritative member state is recovering. Exact phone reopen envelope now passes _matches_precondition, but real dispatch_handlers -> ops.apply -> Scheduler.reopen returns FAILED/EFFECT_FAILED: NOT_ALLOWED: only a blocked task of a live run can be reopened (T1 is recovering). Only stop_owner/resume are stubbed to prevent agents/process control. Source: core operations.py:60-69 permits blocked only; page.tsx:401 exposes retry/edit only for recovering after a successful reopen. Browser mock fabricates success; the new ledger regression also replaces the reopen handler, so neither checks the real transition. Separate review access remains fixed.

### F27 — low / open — Command rate limits remain shared by owner login across sessions rather than per session as R17 specifies.

Tasks: `T11a`. Evidence: Source recheck: server.py:141 keys commands/challenges on authenticated login (dav033), shared across sessions, rather than token/session identity. This is a stricter aggregate cap, not an authorization bypass. No owner-approved R17 amendment is evidenced.

### F28 — high / fixed — Concurrent distinct-key stale preconditions are now serialized with the ledger effect.

Tasks: `T5`. Evidence: Probe D: exit 0; two simultaneously submitted running-precondition commands execute exactly one handler (entry state running); results are OK and REJECTED/STALE_PRECONDITION, with two audit rows. _EFFECT_LOCK now encloses state read/check, challenge/reservation, handler and outcome write. Isolated laptop remote suite: exit 0, 54 tests including test_concurrent_commands_recheck_state_under_the_effect_lock. This verifies process-local ledger command concurrency, not every possible external scheduler race.

### F29 — medium / open — Production snapshots omit the timestamp fields the phone uses for last signal of life and discard plan detail/revision metadata.

Tasks: `T4a`. Evidence: Probe C: exit 0; production run has lastActivityAt but lastSeenAt/updatedAt are None; phone only consumes the latter fields and attempt.updatedAt, while production emits last_activity_at. Source recheck: bt_remote_api._snapshot still emits plan tasks=[] without revision/criteria and omits run/task revision. Browser fixtures supply the missing metadata.

### F30 — medium / open — Stalled-attempt notifications start after 15 minutes although the specification requires more than 10 minutes.

Tasks: `T6`. Evidence: Probe B: exit 0; a live attempt emits no attempt.stalled at +660 s and does at +901 s. bt_remote_events.py:10 still uses 15*60, against SPEC R10 >10 min. Independent Anthropic review of this full source was not completed; this is the primary auditor's own source/runtime finding.

### F31 — low / fixed — The previously exposed post-expiry SSE continuation is no longer reachable because production streaming was removed.

Tasks: `T11`, `T12`. Evidence: Probe A: exit 0; both authenticated candidate SSE endpoints return 404. Full server.py contains no stream/wait/write loop, so the old post-expiry delivery reproduction no longer applies. This closes that exposure only; it does not approve removing streaming. Lost required functionality is open F21, and session-expiry enforcement must be rechecked when a stream is restored.

### F32 — high / open — Every phone pinned retry still fails: the new gateway selector adapter does not recognize route_id.

Tasks: `T13`. Evidence: Probe F: exit 0; exact page.tsx:368 route object {route_id,provider,model,account} becomes params.route=None because app.py:50 accepts only id/routeId/route. Real GatewayRuntime -> LaptopClient -> keyed HTTP route_post returns REJECTED/INVALID_COMMAND (params.route must be nonempty text), stored=False, before state/effects. The new gateway test uses route.id and therefore passes without testing the phone dialect. model/account copying is preserved; do not drop the selected route.

### F33 — high / open — Gateway public-envelope adapter drops the round number and edited brief/criteria fields, breaking both phone operations.

Tasks: `T13`. Evidence: Probe F: exit 0; a real open round has target_state={state:open}, but translating the exact phone command drops round and real laptop HTTP returns STALE_PRECONDITION with the round unchanged. A valid server challenge plus current real run state and phone edit-brief task/field/value yields params={task:T1} and FAILED/EFFECT_FAILED: edit-brief requiere un brief de tarea no vacío. app.py:36-42 omits round/field/value; target.taskId preserves task. These fail independently of F26 and the current precondition can be valid. Anthropic finding 2 independently confirms both omissions.

### F34 — medium / open — The frozen T14 notification verification references a test file removed from the audited prerequisites.

Tasks: `T14`, `T13`. Evidence: cd remote/gateway && python -m unittest discover -s tests -p test_notify.py: exit 5 under Python 3.14.7, Ran 0 tests, NO TESTS RAN. git diff 0af07a73 HEAD -- remote/gateway/tests/test_notify.py shows deletion of 128 lines, including runtime restart dedupe and production delayed-offline-alert tests. Remaining sender/bot/cursor tests do not replace that frozen command. Restore/adapt the behavior tests; do not treat empty discovery as a passing gate.

## Independent other-provider review and dispositions

A fresh Anthropic source-only review received the frozen requirements and numbered current-tree excerpts from
app.py, server.py, the phone command forms, laptop dispatch, edit validation and scheduler reopen. It received
neither this report nor the ledger nor the primary auditor's conclusions. Tools/write access were disabled.
This is a different provider from the primary auditor; it is not a claim about who authored every prerequisite.
The completed review covers those boundaries only; the primary auditor performed the other source/runtime checks.

Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`, source bundle on stdin.
Receipt: exit 0, subtype success, is_error false, 1 turn, provider duration 42,620 ms, wall time 43.714 s;
reported model `claude-sonnet-5-5`.
Input SHA-256: `e2b2a8666fdd66eef5943022beb9f3167eec7fb91350bd555c63294cbed12913`.
Output JSON SHA-256: `07e440b7b83d3e5e76e410320d6d6ade1edc808cca81f1ed1385fdb4fac98a40`.
No independent passing tests are inferred from source review. Its six findings receive these verdicts:

| Provider finding | Primary verdict and reason |
|---|---|
| 1 high: OAuth query logging | Confirmed F4 by A. Primary severity medium: queries contain short-lived one-use code/state; successful callback state is consumed before response logging. No usable session token leak or takeover was demonstrated. Logging still violates R17 and remains open. |
| 2 high: omitted round/field/value | Confirmed high F33 by real gateway-to-laptop F. Correction to provider's route: round fails during the actual state-reader precondition, before its handler, while edit fails at dispatch validation. Both still block the phone operation. |
| 3 high, conditional: typed confirmation missing/no server challenge | Rejected after full-source review: Ledger.submit validates/consumes the target-bound 120 s challenge and copies typed_req into params before dispatch; page.tsx sendCommand obtains a challenge when only typedReq is supplied. Challenge/one-use/replay tests pass. The provider explicitly lacked these collaborators; F33 is unrelated to confirmation. |
| 4 medium: lost route selector; pin persistence before retry error | Lost selector confirmed as high F32: F shows actual laptop validation rejects route=None, so reject the provider's suggestion that this exact request can run unpinned. Ordering of set_pin before ops.retry is real, but no separate R6 violation is confirmed: availability is checked first, stale preconditions are checked before dispatch, and R6 does not promise rollback of every partial failed effect. No failed command causing a later wrong-route attempt was demonstrated. |
| 5 medium, conditional: fresh UUID after unknown result | Confirmed F16 after inspecting complete sendCommand: it has no envelope/key reconciliation cache. Reject examples of duplicate standalone note effects: note is currently unimplemented (F7). Server-side replay protection remains valid. |
| 6 low: marker/logout/rate limits | Marker and GET logout confirmed F5 by A; owner-wide rather than session-wide command quota is F27. Full do_POST invokes the guard before authentication/dispatch. No command Origin bypass, authenticated cross-site mutation, or deployed proxy-induced sign-in lockout was demonstrated; those implications are rejected. |

## Frozen acceptance coverage and rejected/superseded candidates

| Requirement / boundary | Evidence or remaining gap |
|---|---|
| R1/R3: single owner, OAuth state/cookies, private keyed listener | Gateway auth/browser and laptop remote/listener/installed suites pass on fixtures. No live deployment claim. |
| R2/R17: mutation and logging guards | Foreign/missing Origin/header tests pass; exact marker/logout/logging/per-session deviations remain F4/F5/F27. |
| R4: real runs/activity/tasks/feed/plan detail | Snapshot/browser tests pass on their own fixtures; real timestamp/metadata and production stream gaps remain F21/F29. Five-second mock polling is retained. |
| R5/R13: control, rounds, recovery, brief/criteria/note | F7/F8/F9/F26/F32/F33 remain; isolated successful laptop dispatch tests do not establish the phone-to-gateway envelope. |
| R6: idempotency and stale-command safety | Existing replay/conflict and fresh concurrent-key D pass (F28 fixed); client unknown-outcome reconciliation is F16. |
| R7: offline refusal/cache | Liveness/offline tests pass; restart persistence/outage timestamp remain F11/F13. |
| R8: confirmation challenge | Target-bound, typed, expiring, one-use/replay tests pass. No bypass demonstrated. |
| R9: actual selected failure review | Laptop review/phone tests pass (F25 fixed); recovery failure is separately F26. |
| R10/R11/R12: alerts, deterministic delivery, bot safety | Sender/bot tests pass; forced-failure E2E fails (F2), missing actions F6, threshold F30 and removed runtime verification F34 remain. |
| R14: mobile/PWA/theme | Web build/14 tests pass, including 360 px mock browser. Real installation/complete touch-size measurement remain untested. |
| R15: quotas/history | Current parser/read-model/history regression suites pass (F23 fixed); retention remains F12. |
| R16/R18: deployment/local panel | Kit and 68 local regression tests pass with the Caddy skip; no secrets inspected and no live services touched. |

| Inherited candidate | Current verdict and reason |
|---|---|
| Caddy container-loopback upstream / missing private listener instructions | F1 fixed structurally; runbook step 6 contains the private keyed listener/tunnel. F3 still concerns initial ordering/container reload. |
| Blank optional example keys necessarily break a compliant install | Superseded F22: current runbook requires filling every uncommented key; final B validates both complete configs. |
| Web cannot compile or consume real {login} | Fixed F18/F19/F20 with fresh complete verify and A; no broad current failure inferred from old attempts. |
| Missing installed precondition dependency | Fixed F24 by fresh installed wheel/sdist/API test. F33 concerns public command adaptation instead. |
| Rejected attempt has no accessible review | Fixed F25 for selected review links/real read model. Failed real recovery is independently F26. |
| Callback state cookie must be Strict | Rejected: Lax permits cross-site top-level OAuth callback; state is browser-bound and one-use, resulting session is Strict. |
| Same-key replay executes twice / edit-brief lacks a challenge | Rejected on tested paths: real ledger enforces challenge/replay and passes these regressions. F28's distinct-key race is now also fixed. |
| Tunnel exposes the unauthenticated panel | Rejected: remote-only listener 8766, keyed API and panel-route denial tests pass; panel 8765 stays separate. |
| Current production SSE replay deque is unbounded | Withdrawn: old class was removed; unused replacement is bounded. Production has no stream at all (F21); F12 retains confirmed database retention gaps. |
| Post-expiry SSE still delivers (old probe E) | Superseded F31: both production paths now return 404 in A. This removes that exposure, not the requirement to restore a secure live feed. |
| Shared .next alone proves current web test failure | Rejected: fresh serialized verify passes all 14 tests/build. |
| T17 cancellation fixture still reserved | Withdrawn: both fixtures ingest execution_started. T17 fails earlier on the non-exhausted forced-failure fixture (F2). |

## Handoff

Return **F2 to T17; F26 to T5/T5a/T15f; F32 and F33 to T13**. F34 names T14 and the T13 integration
that removed its tests. Preserve all other recorded open items until repaired or explicitly accepted by the owner.
Keep the fixed process-local serialization, installed dependencies, selected failure review, redaction, local
listener, strict web build/session/history and new snapshot poll fallback. Do not repair the E2E by weakening the
real retry-budget notification rule, fabricate scheduler reopen success, or drop the chosen route/operation fields.
Recheck commands through the real gateway/laptop/scheduler; mocks currently hide those boundary failures.
No source/test/configuration repair was made by this audit, and no task is declared independently verified.

## Reproduction probes

Run from repository root with installed dependencies. Inputs are synthetic. Each probe uses temporary state and
only loopback; no real scheduler/agent may be started. E2E fixture seeding invokes only a FakeExecutor.
The temporary fixture root is set before importing production modules. A successful reproduction means the stated
observation was obtained, not that the feature passed acceptance. Old post-expiry probe E is retired (see F31).

### Probe A — real gateway HTTP boundaries

```bash
python - <<'PY'
import http.client, io, json, logging, pathlib, sys, tempfile, threading
from http.server import ThreadingHTTPServer
sys.path.insert(0, str(pathlib.Path('remote/gateway').resolve()))
from auth import OAuthConfig, OAuthService, SessionStore
from server import make_handler
class Runtime:
    def submit_command(self, value): return {'status': 'OK'}
with tempfile.TemporaryDirectory() as tmp:
    db = str(pathlib.Path(tmp)/'sessions.db')
    secret = 'synthetic-secret-at-least-32-characters'
    store = SessionStore(db, secret)
    service = OAuthService(OAuthConfig('synthetic', 'synthetic', secret, 'https://frontend.test', db), store)
    token = store.create_session('dav033')
    server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(service, Runtime()))
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    capture = io.StringIO(); sink = logging.StreamHandler(capture)
    log = logging.getLogger('server'); log.addHandler(sink); log.setLevel(logging.INFO)
    def request(method, path, headers=None, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
        connection.request(method, path, body, headers or {})
        response = connection.getresponse()
        result = response.status, response.read().decode(), response.getheader('Set-Cookie')
        connection.close(); return result
    try:
        cookie = {'Cookie': 'flow_session='+token}
        print('session', request('GET', '/api/auth/session', cookie)[:2])
        wrong = request('POST', '/api/remote/v1/commands', {**cookie, 'Origin': 'https://frontend.test',
                        'X-Flow-Request': 'wrong', 'Content-Type': 'application/json'}, '{}')
        print('wrong marker', wrong[:2]); assert wrong[0] == 200
        logout = request('GET', '/api/auth/logout', {**cookie, 'Origin': 'https://foreign.test'})
        print('foreign logout', logout[::2]); assert logout[0] == 302 and store.get_session(token)
        for path in ('/api/remote/v1/events/stream?after=abc', '/api/remote/v1/events'):
            result = request('GET', path, cookie); print('SSE', path, result[:2]); assert result[0] == 404
        request('GET', '/api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE')
        leaked = 'code=SYNTHETIC_CODE&state=SYNTHETIC_STATE' in capture.getvalue()
        print('query logged', leaked); assert leaked
    finally:
        server.shutdown(); server.server_close(); worker.join(); log.removeHandler(sink)
PY
```

### Probe B — cache, retention, redaction, events, commands and example configuration

```bash
python - <<'PY'
import os, pathlib, sqlite3, sys, tempfile
from datetime import datetime
root = pathlib.Path.cwd(); sys.path[:0] = [str(root/'remote/gateway'), str(root/'skill/scripts')]
with tempfile.TemporaryDirectory() as tmp:
    os.environ['BITACORA_ROOT'] = tmp
    import bt_remote_commands as commands, bt_remote_events as feed
    from app import GatewayRuntime
    from auth import OAuthConfig, SessionStore
    from config import GatewayConfig
    from liveness import LaptopStatus
    cfg = GatewayConfig('http://127.0.0.1:1', 'synthetic-key', 'synthetic-token', 'synthetic-chat', pathlib.Path(tmp)/'gateway.db')
    runtime = GatewayRuntime(cfg, laptop=object(), sender=lambda _: None)
    again = GatewayRuntime(cfg, laptop=object(), sender=lambda _: None)
    runtime.liveness.status = again.liveness.status = LaptopStatus.OFFLINE
    runtime.snapshot_cache = {'runs': [], 'generatedAt': '2026-10-20T00:00:00Z'}
    print('cached offline', runtime.web_snapshot()); print('restart cache', again.web_snapshot())
    assert again.web_snapshot() is None and runtime.web_snapshot()['laptop'] == {'online': False}
    store = SessionStore(str(pathlib.Path(tmp)/'sessions.db'), 'synthetic-secret-32-characters-long')
    store.create_session('dav033', now=1); store.create_session('dav033')
    with sqlite3.connect(store.database_path) as db:
        expired = db.execute('SELECT COUNT(*) FROM sessions WHERE expires_at < 10000000').fetchone()[0]
    print('expired rows', expired); assert expired == 1
    redacted = feed.redact('OPENAI_API_KEY=SYNTHETIC_KEY_123456789 Authorization: Bearer SYNTHETIC_BEARER_123456789')
    print('redacted', redacted); assert 'SYNTHETIC_' not in redacted
    events = feed.build_events({'plans': [{'project': 'demo', 'req_id': 'REQ-001', 'plan_status': 'review'}]})
    print('waiting events', [e['type'] for e in events]); assert [e['type'] for e in events] == ['plan.waiting']
    envelope = {'idempotency_key': 'a'*121, 'command': 'pause', 'target': 'demo/REQ-001', 'origin': 'web', 'params': {}, 'precondition': {'state': 'running'}}
    print('long key', commands.validate(envelope)); assert commands.validate(envelope)
    note = {**envelope, 'idempotency_key': 'synthetic-note-command', 'command': 'note', 'params': {'note': 'synthetic'}}
    result = commands.Ledger(pathlib.Path(tmp)/'ledger.db').submit(note, commands.dispatch_handlers(), lambda _: {'state': 'running'})
    print('note', result['code']); assert result['code'] == 'COMMAND_NOT_IMPLEMENTED'
    result = runtime.submit_telegram_command({'schemaVersion': 1, 'idempotencyKey': 'synthetic-retry-key', 'type': 'retry', 'target': {'kind': 'run', 'project': 'demo', 'req': 'REQ-001'}, 'precondition': {'state': 'running'}})
    print('Telegram retry', result); assert result['code'] == 'INVALID_COMMAND'
    stamp = '2026-10-20T00:00:00Z'; epoch = datetime.fromisoformat(stamp).timestamp()
    state = {'runs': [{'project': 'demo', 'req_id': 'REQ-001', 'tasks': [{'id': 'T1', 'attempt': {'id': 'a', 'live': True, 'last_activity_at': stamp}}]}]}
    for elapsed in (660, 901):
        kinds = [e['type'] for e in feed.build_events(state, now=epoch+elapsed)]
        print('stall', elapsed, kinds); assert kinds == ([] if elapsed == 660 else ['attempt.stalled'])
    values = dict(line.split('=', 1) for line in (root/'remote/deploy/gateway.env.example').read_text().splitlines() if line and not line.startswith('#'))
    values.update(LAPTOP_ORIGIN='http://127.0.0.1:18765', FLOW_GATEWAY_KEY='synthetic-key-123456789012345', TELEGRAM_BOT_TOKEN='synthetic', TELEGRAM_CHAT_ID='synthetic', GATEWAY_DATABASE=str(pathlib.Path(tmp)/'env.db'), GATEWAY_BIND='172.20.0.1', GITHUB_CLIENT_ID='synthetic', GITHUB_CLIENT_SECRET='synthetic', SESSION_SECRET='synthetic-secret-32-characters-long', FLOW_FRONTEND_ORIGIN='https://frontend.test', GATEWAY_PORT='8790', UPSTREAM_TIMEOUT='5', PROBE_INTERVAL='5', GITHUB_AUTHORIZE_URL='https://github.com/login/oauth/authorize', GITHUB_TOKEN_URL='https://github.com/login/oauth/access_token', GITHUB_USER_URL='https://api.github.com/user')
    assert all(values.values())
    print('fully filled config', GatewayConfig.from_env(values).bind_host, OAuthConfig.from_env(values).bind_port)
    runtime.outbox._db.close(); again.outbox._db.close()
PY
```

### Probe C — authoritative rejected-task projection and real reopen effect

```bash
python - <<'PY'
import json, os, pathlib, sys, tempfile
from unittest.mock import patch
root = pathlib.Path.cwd(); sys.path[:0] = [str(root/'remote/e2e/tests'), str(root/'skill/scripts')]
from test_local_e2e import LocalEndToEndTests as Fixture
with tempfile.TemporaryDirectory() as tmp:
    Fixture.root = pathlib.Path(tmp)/'bitacora'; Fixture.root.mkdir()
    os.environ['BITACORA_ROOT'] = str(Fixture.root); os.environ['FLOW_GATEWAY_KEY'] = 'synthetic-audit-key'
    Fixture._seed_retry_event_fixture(); Fixture._seed_cancel_run_fixture()
    import bt_remote_api as api, bt_remote_commands as commands, bt_subscriptions, bt_scheduler_ops as ops
    class Handler:
        headers = {'Authorization': 'Bearer synthetic-audit-key'}
        def send(self, payload, status=200, *args): self.result = status, json.loads(payload)
    handler = Handler()
    with patch.object(bt_subscriptions, 'summary', return_value=[]):
        handler.path = '/api/remote/v1/snapshot'; api.route_get(handler)
        run = next(r for r in handler.result[1]['runs'] if r['req'] == 'REQ-001'); task = run['tasks'][0]
        print('task', task['state'], 'review', task['reviewAttempt']['id'])
        print('signal fields', {k: run.get(k) for k in ('lastActivityAt', 'lastSeenAt', 'updatedAt')})
        handler.path = '/api/remote/v1/events?limit=100'; api.route_get(handler); print('events', handler.result)
        print('real member state', commands.target_state('demo/REQ-001', 'reopen', {'task': 'T1'}))
        with patch.object(ops, 'stop_owner', return_value=0), patch.object(ops, 'resume', return_value='synthetic-no-start'):
            result = commands.Ledger(pathlib.Path(tmp)/'ledger.db').submit(
                {'idempotency_key': 'synthetic-reopen-key', 'command': 'reopen', 'target': 'demo/REQ-001', 'origin': 'web', 'params': {'task': 'T1'}, 'precondition': {'state': task['state']}},
                commands.dispatch_handlers(), commands.target_state)
        print('real reopen dispatch', result)
        assert result['code'] == 'EFFECT_FAILED' and 'only a blocked task' in result['outcome']['error']
PY
```

### Probe D — concurrent distinct-key command preconditions

```bash
python - <<'PY'
import pathlib, sys, tempfile, time, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path('skill/scripts').resolve()))
from bt_remote_commands import Ledger
with tempfile.TemporaryDirectory() as tmp:
    ledger = Ledger(pathlib.Path(tmp)/'ledger.db'); state = {'state': 'running'}; effects = []; gate = threading.Barrier(2)
    def read(*args): return dict(state)
    def effect(*args):
        effects.append(state['state']); time.sleep(.1); state['state'] = 'paused'; return {'changed': True}
    def send(number):
        gate.wait(timeout=5)
        return ledger.submit({'idempotency_key': f'synthetic-race-{number}', 'command': 'pause', 'target': 'demo/REQ-001', 'origin': 'web', 'params': {}, 'precondition': {'state': 'running'}}, {'pause': effect}, read)
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(send, [1, 2]))
    print('effects', effects, 'results', [(r['status'], r['code']) for r in results], 'rows', len(ledger.rows()))
    assert effects == ['running'] and sorted(r['status'] for r in results) == ['OK', 'REJECTED']
    assert next(r for r in results if r['status'] == 'REJECTED')['code'] == 'STALE_PRECONDITION'
PY
```

### Probe F — exact phone command envelopes through the real gateway/laptop adapter

```bash
python - <<'PY'
import json, os, pathlib, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
root = pathlib.Path.cwd(); sys.path[:0] = [str(root/'remote/e2e/tests'), str(root/'remote/gateway'), str(root/'skill/scripts')]
from test_local_e2e import LocalEndToEndTests as Fixture
with tempfile.TemporaryDirectory() as tmp:
    Fixture.root = pathlib.Path(tmp)/'bitacora'; Fixture.root.mkdir()
    os.environ['BITACORA_ROOT'] = str(Fixture.root); os.environ['FLOW_GATEWAY_KEY'] = 'synthetic-audit-key'
    Fixture._seed_retry_event_fixture()
    import bt_remote_api as api, bt_remote_commands as commands
    from app import GatewayRuntime, _ledger_command
    from config import GatewayConfig
    rdir = Fixture.root/'demo/requirements/REQ-001-forced-failure'
    round_path = rdir/'rounds/round-01.json'; round_path.parent.mkdir()
    round_path.write_text(json.dumps({'round': 1, 'status': 'open', 'questions': [{'id': 'q1', 'type': 'open', 'text': 'Question'}], 'answers': {}}))
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def send(self, body, status=200, content_type='application/json'):
            body = body.encode(); self.send_response(status); self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
        def do_POST(self): api.route_post(self)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    runtime = GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{server.server_port}', 'synthetic-audit-key', 'synthetic', 'synthetic', pathlib.Path(tmp)/'gateway.db'), sender=lambda _: None)
    try:
        target = {'kind': 'run', 'project': 'demo', 'req': 'REQ-001', 'taskId': 'T1'}
        retry = {'schemaVersion': 1, 'idempotencyKey': 'synthetic-pinned-retry', 'type': 'retry', 'target': {**target, 'kind': 'task'}, 'precondition': {'state': 'recovering'}, 'route': {'route_id': 'synthetic-route', 'provider': 'codex', 'model': 'synthetic', 'account': 'synthetic'}}
        print('retry params', _ledger_command(retry)['params']); result = runtime.submit_command(retry)
        print('retry result', result); assert result['code'] == 'INVALID_COMMAND' and not result['stored']
        round_command = {'schemaVersion': 1, 'idempotencyKey': 'synthetic-round-command', 'type': 'answer-round', 'target': {**target, 'kind': 'round', 'roundId': '1'}, 'precondition': {'state': 'open'}, 'round': 1, 'answers': {'q1': {'text': 'synthetic answer'}}}
        print('proper round state', commands.target_state('demo/REQ-001', 'answer-round', {'round': 1}))
        print('round forwarded params', _ledger_command(round_command)['params']); result = runtime.submit_command(round_command)
        print('round result', result); assert result['code'] == 'STALE_PRECONDITION' and json.loads(round_path.read_text())['status'] == 'open'
        challenge = runtime.issue_challenge({'target': 'demo/REQ-001', 'typedReq': 'REQ-001'})
        current = commands.target_state('demo/REQ-001', 'edit-brief', {'task': 'T1'})
        edit = {'schemaVersion': 1, 'idempotencyKey': 'synthetic-edit-command', 'type': 'edit-brief', 'target': target, 'precondition': {'state': current['state']}, 'task': 'T1', 'field': 'objective', 'value': 'New objective', 'confirmation': {'challengeId': challenge['challengeId'], 'typedReq': 'REQ-001'}}
        print('edit forwarded params', _ledger_command(edit)['params']); result = runtime.submit_command(edit)
        print('edit result', result); assert result['code'] == 'EFFECT_FAILED' and 'brief' in result['outcome']['error']
    finally:
        server.shutdown(); server.server_close(); worker.join(); runtime.outbox._db.close()
PY
```
