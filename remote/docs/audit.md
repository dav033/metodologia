# Independent security and specification audit — T18

**Rework required: F1, F24, F26, F35 and F36 are high and open.** Their causes are in prerequisite
implementation, packaging and deleted deployment files, outside this task's explicit read-only boundary.
The criterion “Confirmed high findings are fixed” is not met. Repeating the previous report cannot fix them.
Only this report and `audit.findings.json` are changed; no risk is accepted and no independent verdict is claimed.

Audited tree: `1ecc1fee7c227504e84c098772230a61323b11fd` (HEAD at entry), 2026-10-21.
Primary auditor: OpenAI Codex. Fresh other-provider review: Anthropic Claude Sonnet, receipt below.
The ledger contains **40 findings: 13 rechecked fixed/superseded exposures and 27 open
(5 high, 20 medium, 2 low); 0 accepted**.

## Carried overlap, earlier failures and scope

Initial git status/diff were clean. Both supplied documents were opened before editing and neither contained
conflict markers. Their inherited conclusions were stale against 44 changed implementation/test/configuration
files relative to the earlier task result `108efc35f370dd19fe3cabbafe85bc60a7e69084`.
This reconciliation keeps every F1–F34 identity, acknowledges repairs, and records regressions rather than
discarding either side's intent or changing working implementation. No source, tests or configuration were edited.

Read the supplied #9–#14 outcomes and reachable report history at `13d914a6`, `15f1a318`, `088cefb3`,
`81a29c39`, `0af07a73` and `108efc35f`. Raw m6 URI results and omitted older attempts were not available.
Read the frozen SPEC, PLAN.md and every PLAN.json task objective, acceptance criterion and verification.
Historical provider receipts and passing checks are not current-tree evidence.

The previous empty-event E2E failure is no longer reproduced (F2); its production notification regression is
explicitly F37. Gateway route/round/edit field omissions are repaired (F32/F33). Real core reopen succeeds,
but the subsequent phone flow still fails (F26). The supplied tree also removed deployment files (F1/F3),
omitted actual installed recovery modules (F24), broke the real phone snapshot (F35), and removed read models
needed for history, quota and route selection (F23/F36). These are different, traced causes, not another retry
of the previous same report.

Audited laptop listener/key isolation, OAuth/state/session/Origin/logging/throttling, ledger/challenge/replay,
concurrency and real scheduler recovery; producer/consumer snapshot, review and event contracts; gateway
polling/cache/stream, notifications/bot; installed distributions, web and deployment artifacts.
Fixtures used temporary state, synthetic credentials and loopback only. No real account/quota source, project
state, credential file, browser profile, SSH host or deployed service was read or modified.
Audit notes remain in these documents under the user-imposed two-file boundary rather than writing external
bitácora or project-memory files.

## Fresh verification evidence

Python 3.14.7, Node 24.21.0; Python 3.12 was unavailable.
Installed the existing lockfile first: `cd remote/web && npm ci --offline`, exit 0, 320 packages; lock unchanged.
Subsequent verification does not install dependencies or write inside node_modules.
Browser tests, builds and E2E ran sequentially.

Laptop/gateway/local-panel discovery ran with BITACORA_ROOT set to an empty TemporaryDirectory before imports.
It does not change source or access the real registry. Combined discovery includes the frozen individual test
patterns; missing patterns are explicitly reported, never hidden behind a green wildcard suite.

| Command / execution | Actual result |
|---|---|
| `cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py'`, plus `test_platform.py` and `test_page*.py` in one isolated discovery process | Exit 0; 124 tests in 21.184 s: 54 remote, 27 platform, 43 page. Installed health, real revision editing and concurrency tests included. |
| `cd remote/gateway && python -m unittest discover -s tests -p 'test_*.py'` (isolated root) | Exit 0; 45 tests in 22.627 s. Fake typed cursor errors and disconnected hub tests do not establish real HTTP cursor reset or production SSE. |
| `cd skill/scripts/bt_scheduler_core && python -m unittest discover -s tests -p test_operations.py` | Exit 0; 18 tests in 0.762 s, including recovering reopen. |
| `cd remote/web && npm run verify` | Exit 0; lint, strict typecheck, 14/14 tests (0 skipped/cancelled, 46.251 s), optimized production build. Browser uses mock models. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 0; 1 test in 19.630 s, build/OAuth/stale cancellation/offline/Telegram assertions execute. Does not hydrate the phone parser with the real snapshot. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 1; `ImportError: Start directory is not importable: 'tests'`. Kit tests and most kit files have been deleted (F1). |
| `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` | Exit 5; 0 tests, `NO TESTS RAN` (F34). |
| `bash remote/deploy/deploy.sh --check`; rollback equivalent | Each exit 127, script absent. No deploy or rollback performed. |
| `python -m json.tool remote/contract/command.schema.json`; event equivalent | Each exit 0; syntax only, not semantic schema compliance. |
| `test -s remote/docs/route-pin.md`; architecture.md and contract.md equivalents | Each exit 0. |
| Report probes A, B, C, D, G, H, I and P below | Each exit 0 reproducer; specific findings/limited repairs observed. Probe P's two expected missing-module import subprocesses each exit 1. |
| Three frozen `test -s remote/docs/audit.md` checks | Each exit 0; existence only. |
| Ledger validation, artifact conflict scan, changed-path restriction and `git diff --check` | Exit 0; only the authorized two documents changed. |

187 Python regression tests, 14 web tests and one E2E passed. These do not cancel the explicitly failing kit and
notification gates or substitute for cross-boundary probes. E2E emits ResourceWarnings for HTTPError/SQLite
cleanup; they are not hidden as failing assertions.

Not run: unrelated repository suites, Python 3.12, Caddy validation/Docker connectivity (kit absent), deployed
OAuth/Telegram, real selected-route agent execution, live Vercel SSE lifetime, PWA installation, exhaustive touch
target measurement or a live dependency advisory scan. Offline npm output is not claimed as a fresh advisory
audit. No missing check is reported passing.

## Fresh independent other-provider audit

The first tools-disabled whole-source Anthropic request (175,631 characters; input SHA-256
`8a08fd8a2f6071d7abf8339395f0c1495636b6f39325bbf38e114662baa14886`) timed out at 210 seconds.
No findings or verdict are inferred from it. A smaller request provided the governing requirements and numbered
producer/consumer excerpts for the phone, gateway HTTP/client/adapter, laptop snapshot/ledger and scheduler
reopen. It received neither the primary report nor the ledger or findings, and had no tools/write access.

Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`, source bundle on stdin.
Receipt: exit 0, subtype success, is_error false, 1 turn; provider duration 106,308 ms, wall 107.650 s;
reported provider/model `firstParty / claude-sonnet-5-5`.
Input SHA-256: `07805c46755e0d0ce2839ad9c78c428555a6cb34a4dcc505f8545c087049358e`.
Output JSON SHA-256: `fe3eeec3dd79b58a571ebb1d0ddcb51b23fd2b3c932351f646ed44a1fc0d9ce1`.

This satisfies a fresh review by another provider, not proof of who built every prerequisite. That review covers
the supplied boundaries only; the primary auditor checked the other scope and independently reproduced defects.

| Anthropic finding | Primary verdict and reason |
|---|---|
| 1 high: real snapshot cannot parse | Confirmed high F35 by real producer + exact TypeScript parser in C. |
| 2 medium: missing metadata/plans/criteria | Confirmed F29/F8. Missing rounds/decisions also confirmed in the full source. The speculative failed→retried→failed ABA implication is not a separate confirmed race: R6 allows state preconditions and no concurrent interleaving was demonstrated here. |
| 3 medium: OAuth query in status log | Confirmed F4 by A. No account takeover/session-token leak demonstrated. |
| 4 medium: failed effect returned 200 | Confirmed F39 by G and actual phone control flow. |
| 5 low-medium: unknown result labelled rejected | Confirmed medium F16; same-key server replay is still valid. |
| 6 low-medium: upstream outcome classification | Confirmed medium F40 by I. Truncated HTTP body/IncompleteRead consequence was not exercised and is not claimed as separate evidence. |
| 7 low: nonempty header instead of 1 | Confirmed within F5 by A; no Origin bypass demonstrated. |
| 8 low: GET logout/no revocation | Confirmed within F5 by A; a clearing-cookie response is not an authenticated command exploit. |

All uncertain provider observations were checked against collaborators:

| Candidate | Verdict and reason |
|---|---|
| Null confirmation crashes ledger | Rejected: full validate() rejects non-string challenge/typed_req before `.strip()`/`.encode()`; current confirmation regressions pass. |
| Failed/rejected reopen necessarily fails in core | Rejected for current rejected projection: C shows authoritative recovering and successful real reopen to ready; rejected alias exists. Remaining UI/next-step failure is F26. |
| `live._attempt(None)` crashes snapshot | Rejected: collaborator explicitly handles None; real C snapshot succeeds. |
| Pin set before retry can fail | Ordering confirmed; no additional wrong-route attempt demonstrated. Full-flow readiness/wait issue is F26; existing strict route-availability test remains valid. |
| Cancel/reopen auto-resumes owner pause | Observed explicit ops.resume; not raised as a separate spec violation without an agreed contradictory operation contract. |
| Read 400/404 becomes 503 | Confirmed error flattening; actionable cursor-reset failure is F38, removed real read models are F36. No extra duplicate finding. |
| Local scheduler can race process-local effect lock | Lock scope is accurately limited in F28; no concrete external race reproduced, so no claim it is fixed globally or a new proven bypass. |

## Findings and verdicts

### F1 — high / open — The current prerequisites removed the deployment kit, including the previously corrected Caddy topology.

Tasks: `T16`. Evidence: Frozen T16 command `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 1, ImportError: Start directory is not importable: 'tests'. Caddyfile, bitacora-gateway.service, deploy.sh, rollback.sh and remote/docs/runbook.md are absent. `git diff 108efc35f HEAD` confirms their deletion. Historical topology tests cannot establish the missing kit; restore it with its tests and container-host bridge configuration.

### F2 — high / fixed — The frozen built-web E2E command now completes; its previous empty-event failure is no longer reproduced.

Tasks: `T17`. Evidence: `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py`: exit 0, 1 test in 19.630 s, production build succeeds; fake OAuth owner/foreign account, ledger cancellation/stale precondition, offline cache and single fake Telegram assertion execute. This does not parse the real snapshot in the phone. New F35 records that failure; F37 records that the E2E became green while retry-exhaustion filtering was removed.

### F3 — medium / open — The required go-live runbook has been removed.

Tasks: `T16`. Evidence: Current tree has no remote/docs/runbook.md; `git diff 108efc35f HEAD -- remote/docs/runbook.md` shows all 61 lines deleted. Previous first-install/reload ordering defects cannot be rechecked in an absent runbook. Restore the runbook with first-install-before-restart and containerized Caddy instructions; F1 records the blocking kit loss.

### F4 — medium / open — Gateway request logging exposes OAuth code/state query values in its purported status field.

Tasks: `T11a`. Evidence: Fresh report Probe A: exit 0; synthetic callback code/state appear in captured server logging. server.py:38 uses args[0] (request line) as status. Fresh Anthropic finding 3 independently confirms the leak. Short-lived OAuth values are exposed; no session-token theft/account takeover was demonstrated.

### F5 — medium / open — The mutation marker accepts arbitrary nonempty values, and GET logout clears the cookie without guards or revoking its server session.

Tasks: `T11a`, `T15a`. Evidence: Fresh Probe A: exit 0; wrong nonempty X-Flow-Request passes with HTTP 200, foreign-Origin GET logout clears the cookie with 302, and its server token still resolves. server.py:189-191 checks bool(marker). Anthropic findings 7/8 confirm. Command POST Origin guards still run; no cross-site command bypass is claimed.

### F6 — medium / open — Telegram alerts still omit a working review URL and safe inline actions, and retry callbacks remain unsupported.

Tasks: `T14a`, `T14b`. Evidence: Fresh Probe B: exit 0; Telegram retry returns INVALID_COMMAND. Source: app.py submit_telegram_command allows only pause/resume; notifications.py TelegramSender sends chat_id/text with no reply_markup, review URL, task/cause detail. The 45 gateway tests pass, covering sender/bot but not these omitted alert controls.

### F7 — medium / open — The public note command is still advertised and validated without a laptop dispatcher.

Tasks: `T5a`. Evidence: Fresh Probe B: exit 0; real Ledger.submit(note) returns COMMAND_NOT_IMPLEMENTED. dispatch_handlers has no note although laptop/gateway registries and public schema advertise it. Existing retry reason/RUN.notes support does not implement the standalone note command.

### F8 — medium / open — The phone brief form still cannot edit acceptance criteria.

Tasks: `T15f`. Evidence: Fresh page.tsx:368-377 always sends field=objective and a string value; no acceptance-criteria editor is rendered. bt_remote_edit supports list criteria, and the current 54-test laptop remote suite exercises revision edits. Anthropic finding 2 independently confirms the phone omission. F33's field adapter repair is retained.

### F9 — medium / open — Run-level Reabrir ejecución supplies no task identity to a task-scoped operation.

Tasks: `T15d`. Evidence: Current page.tsx run-level commandForm(reopen, kind:run) omits taskId; bt_remote_commands.TASK_SCOPED/_member_state and dispatch_run_command require params.task. Its state precondition cannot resolve. Probe C separately confirms task-scoped real reopen succeeds; do not conflate that with the invalid run-level form.

### F10 — medium / fixed — Ordinary plans waiting for approval previously emitted no plan.waiting event without a scheduler decision.

Tasks: `T6`. Evidence: Fresh Probe B: exit 0; review plan with no scheduler decisions emits plan.waiting. Combined isolated laptop tests: exit 0, 124 tests, including all 54 test_remote_*.py cases. collect still supplies plans to build_events.

### F11 — medium / open — Gateway restart still loses the last snapshot; the replacement replay hub is not integrated into production.

Tasks: `T12`. Evidence: Fresh Probe B: exit 0; offline runtime serves its memory snapshot, newly constructed runtime with the same database returns None. app.py snapshot_cache is not persisted; production never instantiates the otherwise tested StreamHub. F21 records absent production streaming.

### F12 — medium / open — Delivered/dropped Telegram history and abandoned expired sessions remain unbounded.

Tasks: `T11`, `T14a`, `T5`. Evidence: Fresh Probe B: exit 0; creating a session leaves an expired abandoned row. notifications.py never prunes telegram_outbox/telegram_delivery_history after 90 days; SessionStore removes expired sessions only on presentation, and Ledger.rows reads all rows. Old production SSE-deque claim remains withdrawn; StreamHub is bounded and unused.

### F13 — medium / open — No stable offline-start timestamp reaches the phone.

Tasks: `T12`, `T15b`. Evidence: Fresh Probe B: exit 0; cached generatedAt remains but laptop object is only {online:false}; no offline-start wall-clock timestamp. app.py web_snapshot serializes only online and page.tsx renders LAPTOP SIN CONEXIÓN without HH:MM. Monotonic liveness.offline_since is not exposed.

### F14 — medium / fixed — Laptop-side redaction previously missed provider-key assignments and bearer authorization text before transmission.

Tasks: `T7`, `T6`. Evidence: Fresh Probe B: exit 0; synthetic provider-key assignment and bearer become [REDACTED]. Combined isolated laptop suite: exit 0, 124 tests, including all 54 remote cases and real review redaction. Shared recursive redactor remains in snapshot/events/reviews. No exhaustive secret-scanning guarantee.

### F15 — medium / fixed — The local panel previously had no inherited systemd listener implementation.

Tasks: `T9`. Evidence: Combined isolated unittest discovery of test_remote_*.py, test_platform.py and test_page*.py in skill/scripts: exit 0, 124 tests in 21.184 s (54 remote, 27 platform, 43 page). Includes inherited listener and activation/reload regressions. No real systemd restart performed.

### F16 — medium / open — The phone still discards unknown-outcome command envelopes and creates a fresh idempotency key on resubmission.

Tasks: `T15d`. Evidence: Fresh source inspection page.tsx:272-316: every form makes a new web UUID, sendCommand retains no replayable exact envelope/key; UNKNOWN_OUTCOME HTTP 503 is labelled Rechazado. Anthropic finding 5 confirms. Existing server replay tests and fresh Probe D pass but do not reconcile the phone's uncertain submission.

### F17 — low / open — Public command schema disagrees with production commands, fields and key limits.

Tasks: `T3`. Evidence: Current command.schema.json lacks answer-decision, requires singular answer, models route as text and edit as brief; phone sends plural answers/round, route object and field/value. Fresh Probe B rejects 121-character laptop key while schema permits 128. JSON-tool checks validate syntax only.

### F18 — medium / fixed — The required browser verification previously failed and asserted obsolete singular round answers.

Tasks: `T15`, `T15e`. Evidence: `cd remote/web && npm run verify`: exit 0; lint, tsc --noEmit, 14/14 tests (0 skipped/cancelled; 46.251 s) and production next build pass. These browser tests use fixtures; they do not refute real snapshot parser failure F35.

### F19 — high / fixed — The integrated phone app previously failed strict typing and production build due to overlapping implementations.

Tasks: `T15a`, `T15c`, `T15d`. Evidence: Fresh `cd remote/web && npm run verify`: exit 0, lint/strict typing/14 tests/production build pass; production build also succeeds in T17. No duplicate refreshCommandHistory or invalid Attempt predicate reproduced. Runtime integration remains separately F35/F36.

### F20 — high / fixed — The phone previously rejected the real gateway's successful {login:'dav033'} session response.

Tasks: `T15a`. Evidence: Fresh Probe A: exit 0, real gateway session returns HTTP 200 {login:'dav033'}. Fresh npm run verify: exit 0, including browser handling of that dialect. No deployed OAuth claim; F35 concerns the later real snapshot, not authentication.

### F21 — medium / open — Production gateway serves neither SSE route; the replacement tested StreamHub is disconnected from runtime and HTTP.

Tasks: `T12`, `T6`, `T15b`. Evidence: Fresh Probe A: exit 0; authenticated GET /api/remote/v1/events/stream?after=abc and /api/remote/v1/events both return 404. Full server.py/main.py/app.py contain no stream handler or production StreamHub instance. Phone still opens events/stream. 45 gateway tests exercise the disconnected hub; mock SSE and five-second phone polling do not restore the production feed.

### F22 — medium / fixed — The earlier env-startup allegation assumed blank optional settings despite the current runbook requiring every uncommented key to be filled.

Tasks: `T16`. Evidence: Fresh Probe B: exit 0; filling every uncommented gateway.env.example setting with synthetic/standard values makes GatewayConfig.from_env and OAuthConfig.from_env succeed at 172.20.0.1:8790. This closes the earlier mandatory-blank-config allegation only. The current runbook is absent (F3) and deployment suite fails (F1); no startup/deploy success is claimed.

### F23 — medium / open — Phone command-history compilation remains repaired, but its production read endpoint has been removed.

Tasks: `T4a`, `T15d`. Evidence: Fresh npm run verify exits 0 and the single history normalizer compiles. Fresh Probe C: keyed GET /api/remote/v1/commands returns 404; bt_remote_api.route_get no longer routes it. Gateway turns that upstream failure into 503. Fixture history assertions do not establish real command history. F36 groups the removed read models.

### F24 — high / open — Installed distributions include the old precondition helper but omit the actual retry and edit implementation modules.

Tasks: `T18.6`, `T8`, `T8a`. Evidence: Fresh packaging probe builds wheel/sdist with tests/migration/installed_wheel.get. Both archives omit bt_remote_edit.py and bt_route_pins.py; isolated wheel imports exit 1 with ModuleNotFoundError for each, while bt_remote_preconditions imports with exit 0. pyproject.toml omits those modules. Real dispatch imports them dynamically. Existing installed test checks health/imports of six other modules, so its green result misses this. Add both modules and exercise installed retry/edit dispatch.

### F25 — medium / fixed — The failed-task link previously opened only an unrelated static review fixture.

Tasks: `T15c`. Evidence: Fresh npm run verify exits 0 including selected review assertions. Probe C projects rejected reviewAttempt att-0001; current task link includes its attempt hash and review/page.tsx consumes it directly. All 54 laptop remote tests pass including real failure review/redaction. The global snapshot failure F35 and recovery defect F26 remain separate.

### F26 — high / open — Real reopen now succeeds, but leaves the task ready while the phone exposes recovery controls only for recovering.

Tasks: `T15f`, `T8`, `T5a`. Evidence: Fresh Probe C: exact task reopen via GatewayRuntime -> real keyed HTTP -> ledger -> ops.apply -> Scheduler.reopen returns OK; authoritative recovering becomes ready and real snapshot projects ready. Only process stop/resume are stubbed. page.tsx:397 shows retry/edit only for recovering; reopenedTasks overrides failed/blocked/rejected, not ready, so controls disappear. In addition ops.retry waits up to 180 s for blocked and does not accept ready/recovering. Browser mock preserves the synthetic recovering state. Keep the real scheduler fix; repair/recheck the complete recovery flow.

### F27 — low / open — Command rate limits remain shared by owner login across sessions rather than per session as R17 specifies.

Tasks: `T11a`. Evidence: Current server.py:142 uses authenticated login, not session token, as command/challenge rate-limit key. Multiple owner sessions share a cap; this is stricter than R17 and not an auth bypass. Fresh guard tests pass in the 45-test gateway suite; no owner-approved amendment found.

### F28 — high / fixed — Concurrent distinct-key stale preconditions are now serialized with the ledger effect.

Tasks: `T5`. Evidence: Fresh Probe D: exit 0; simultaneous distinct-key commands execute one handler at running; results OK and REJECTED/STALE_PRECONDITION, two audit rows. Current _EFFECT_LOCK encloses state check/reservation/effect/outcome. Combined 124-test laptop suite passes concurrency regression. This is process-local remote-command serialization, not proof against every external scheduler mutation.

### F29 — medium / open — Real snapshot omits life-sign/revision/criteria metadata and now all plans, rounds and decision requests.

Tasks: `T4a`. Evidence: Fresh Probe C lists actual run fields: active,activeTask,id,lastActivityAt,project,reqId,status,tasks,title. No lastSeenAt/updatedAt/revision; tasks lack revision/criteria. bt_remote_api._snapshot no longer collects any plans/rounds/decisionRequests; GatewayRuntime inserts plans=[] only. page.tsx needs those fields for the signals, revision preview and planning forms. Anthropic finding 2 confirms. F35 is the separate fatal run-dialect mismatch.

### F30 — medium / open — Stalled-attempt notifications start after 15 minutes although the specification requires more than 10 minutes.

Tasks: `T6`. Evidence: Fresh Probe B: exit 0; a live attempt has no attempt.stalled event at +660 s and has one at +901 s. bt_remote_events.STALL_SECONDS remains 15*60 despite SPEC R10 requiring more than 10 minutes.

### F31 — low / fixed — The previously exposed post-expiry SSE continuation is no longer reachable because production streaming was removed.

Tasks: `T11`, `T12`. Evidence: Fresh Probe A: exit 0; both candidate authenticated SSE routes return 404. Current HTTP server has no stream wait/write loop, so old post-expiry delivery is unreachable. This supersedes that exposure only; lost functionality remains F21. Recheck session expiry when streaming is restored.

### F32 — high / fixed — The gateway now preserves the phone route_id selector and forwards the selected pin.

Tasks: `T13`. Evidence: Fresh Probe C: exit 0; exact phone route {route_id:'synthetic-route',provider:'codex',model:'synthetic',account:'synthetic'} translates to route/model/account, passes real keyed HTTP/ledger validation and persists the exact pin. Availability/ops.retry/resume are stubbed to avoid account reads and agent starts; no real attempt launch claimed. Fresh 54 remote and 45 gateway tests pass, including pin assignment and exact phone dialect. F24/F26/F36 independently block installed/full recovery paths.

### F33 — high / fixed — The gateway now forwards the phone round number and edited field/value.

Tasks: `T13`. Evidence: Fresh Probe C: exit 0; exact phone round/answers travels through real GatewayRuntime/keyed HTTP/ledger/round file and returns OK/answered. edit-brief forwards task/field/value with valid real challenge, reaching plan validation instead of the former empty-brief error (minimal fixture returns PLAN_INVALID, not a product defect). Current 54 remote tests include real brief/criteria freeze and rebase. Fresh 45 gateway tests include exact public fields. F24/F26/F29/F35 limit complete phone recovery.

### F34 — medium / open — The frozen T14 notification verification references a test file removed from the audited prerequisites.

Tasks: `T14`, `T13`. Evidence: Fresh frozen command `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py`: exit 5, Ran 0 tests, NO TESTS RAN. File remains absent. 45 other gateway tests do not replace the required runtime restart/offline notification verification; restore/adapt it.

### F35 — high / open — The production snapshot run dialect makes the real phone parser reject every nonempty runs list.

Tasks: `T4a`. Evidence: Fresh Probe C: exit 0 reproducer; real fixture laptop snapshot -> GatewayRuntime.web_snapshot -> exact TypeScript parseSnapshot transpiled with installed TypeScript throws 'El snapshot contiene una ejecución inválida.' Laptop emits reqId/status; phone page.tsx:89 requires req/state; gateway only adds plans=[]. npm mock tests and HTTP-only T17 both pass without crossing this parser boundary. Restore compatible producer fields or aliases and add a real producer-to-parser regression. Anthropic finding 1 independently confirms.

### F36 — high / open — Removing the production keyed command-history, quotas and routes endpoints disables phone history and route selection.

Tasks: `T4a`. Evidence: Fresh Probe C: exit 0 reproducer; authenticated real keyed HTTP GET /api/remote/v1/commands, /quotas and /routes each returns 404. bt_remote_api.route_get removed their _read_model dispatch; gateway still relays them and raises 503. Phone recovery-panels.tsx depends on /routes to enable selected retry and /quotas for accounts, and page.tsx requests /commands. Restore all read models with their contract/consumer tests; fixture responses do not establish production support.

### F37 — medium / open — Failure notifications no longer require exhausted retries, so the green E2E sends a false no-retries-left alert.

Tasks: `T6`, `T17`. Evidence: Fresh Probe H: exit 0 reproducer; one failed attempt with attempts_used=1/max_attempts=3 emits attempt.failed and notification_for_event renders 'Una tarea falló sin reintentos pendientes.' Diff from 108efc35f removes _retry_budget_exhausted and live max_attempts. T17's one-failure fixture now passes by observing that false alert. Restore exhaustion-aware notifications and seed an exhausted fixture without weakening R10.

### F38 — medium / open — Real HTTP INVALID_CURSOR errors no longer reach the gateway cursor-reset branch.

Tasks: `T13`, `T12`. Evidence: Fresh Probe G: exit 0 reproducer; loopback laptop HTTP 400 {code:INVALID_CURSOR} leaves runtime.event_cursor='stale-cursor'. upstream.LaptopClient.get_json flattens HTTPError into UpstreamError, so app.py/_poll_events and StreamHub's UpstreamResponseError branch are unreachable for actual HTTP. Current tests inject the exception directly. Preserve structured HTTP errors and test with real client/HTTP.

### F39 — medium / open — Gateway HTTP 200 for failed effects makes the phone clear forms and treat failed reopen as successful.

Tasks: `T13`, `T15d`. Evidence: Fresh Probe G: exit 0 reproducer; authenticated gateway command receives laptop {status:FAILED,code:ROUTE_UNAVAILABLE} and returns HTTP 200. server.py status map also omits EFFECT_FAILED, STATE_UNAVAILABLE and COMMAND_NOT_IMPLEMENTED. page.tsx sendCommand checks only response.ok then adds failed reopen to reopenedTasks and clears form. Map failure codes and validate semantic outcome before success UI. Anthropic finding 4 confirms.

### F40 — medium / open — Upstream command errors misclassify known connection failure and an uncertain malformed successful response.

Tasks: `T13`. Evidence: Fresh Probe I: exit 0 reproducer; real HTTP 200 with invalid JSON after POST is reported FAILED/LAPTOP_UNAVAILABLE, while mocked URLError(ConnectionRefusedError) becomes UNKNOWN_OUTCOME. upstream.py catches URLError in its earlier OSError branch; malformed post-success JSON goes to plain UpstreamError even though effects may have run. Preserve UNKNOWN_OUTCOME and exact key when execution is uncertain. Anthropic finding 6 confirms; IncompleteRead was not dynamically tested.

## Frozen acceptance coverage and rejected/superseded candidates

| Requirement | Evidence or remaining gap |
|---|---|
| R1/R3 | Gateway auth/browser, keyed listener and installed health tests pass; real fake OAuth E2E passes. No deployed claim. |
| R2/R17 | Origin/auth guard tests pass; logging/marker/logout/per-session discrepancies F4/F5/F27 remain. |
| R4 | Real producer-to-phone parsing fails F35; planning/life-sign metadata F29, stream F21 remain. Poll fallback preserved. |
| R5/R13 | Field adapter repairs F32/F33 retained; standalone note F7, criteria editor F8, invalid run reopen F9, recovery flow F26, installed modules F24 and read models F36 remain. |
| R6/R8 | Same-key replay/challenge/stale/concurrent tests pass; process-local race F28 fixed. Client reconciliation F16 and result semantics F39/F40 remain. |
| R7 | Offline E2E/cache/refusal pass; restart persistence and offline-start time remain F11/F13. |
| R9 | Real selected review projection/link and remote review tests pass (F25); general dashboard failure is independently F35. |
| R10/R11/R12 | Sender/bot and one fake alert E2E pass; controls F6, threshold F30, exhaustion F37, absent required notification test F34 and HTTP cursor recovery F38 remain. |
| R14 | 360 px mock browser/theme/build pass. Real install and exhaustive 44 px targets untested. |
| R15 | Real command/quota read endpoints removed F23/F36; database retention F12 remains. |
| R16/R18 | Existing listener/local-panel tests pass; deployment kit is absent F1/F3. Only synthetic credentials used. |

Historical candidates retained with explicit dispositions:
- Callback state cookie need not be Strict: Lax supports cross-site top-level OAuth return; resulting session is Strict and state is browser-bound/one-use. No regression shown.
- Current web cannot compile or consume {login}: rejected by fresh complete verify and A; F35 occurs later.
- Installed precondition helper is absent: withdrawn for that helper, which imports successfully; actual installed retry/edit modules are absent F24.
- Duplicate same-key execution or edit without challenge: rejected on tested paths; ledger enforces replay and a target-bound one-use challenge.
- Tunnel exposes local unauthenticated panel: rejected by private-listener/key/panel-denial tests. No tunnel was retargeted.
- Current production SSE deque is unbounded or post-expiry continuation leaks: old production stream was removed. Old exposure F31 is superseded; required functionality remains missing F21. Unused hub subscriber queues are not a demonstrated production exposure.
- Blanket env startup failure: complete synthetic configs succeed B (F22). Missing kit/runbook F1/F3 is not dismissed.
- T17 still fails at reserved cancellation/empty feed: withdrawn by fresh full T17 execution (F2); false exhaustion alert remains F37.
- Every prior field-adapter omission still exists: rejected by C, preserving route_id/round/field/value repairs (F32/F33). This does not assert complete recovery works.
- Passing report-existence checks establishes “all high fixed”: rejected. It cannot establish substantive acceptance with five high open.

## Handoff

Return **F1 to T16; F24 to T18.6/T8/T8a; F26 to T15f/T8/T5a; F35 and F36 to T4a**.
Keep all other open findings until repaired or explicitly accepted by the owner; none is self-accepted.
Restore deploy artifacts, installed implementation modules and real read contracts, then check the full phone
recovery transition. Preserve the real core reopen, process-local command serialization, redaction, listener,
strict web build, selected review, and route/round/edit adapter repairs.
Restore retry-budget alert filtering and seed an exhausted failure instead of treating a green fixture as R10
compliance. Add real producer-to-consumer and installed-dispatch coverage; mocks currently hide those boundaries.
Only an independent checker decides acceptance. This audit makes no source/test/configuration repair.

## Reproduction commands

Run from repository root with installed dependencies. All credentials/data are synthetic and all network is
loopback. Probes return zero when their documented observations hold, including defect reproduction.
A FakeExecutor seeds fixture state; real agent starts/process control are suppressed.
The old C/F assertions against obsolete failures are replaced by C below; no working implementation is removed.

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

### Probe C — real producer/parser, keyed read models, reopened state and phone fields

```bash
python - <<'PY'
import json, os, pathlib, sys, tempfile, threading, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
root=pathlib.Path.cwd()
sys.path[:0]=[str(root/'remote/e2e/tests'),str(root/'remote/gateway'),str(root/'skill/scripts')]
from test_local_e2e import LocalEndToEndTests as Fixture
with tempfile.TemporaryDirectory(dir=root/'remote',prefix='.audit-boundary-') as tmp:
 Fixture.root=pathlib.Path(tmp)/'bitacora';Fixture.root.mkdir()
 os.environ['BITACORA_ROOT']=str(Fixture.root);os.environ['FLOW_GATEWAY_KEY']='synthetic-audit-key'
 Fixture._seed_retry_event_fixture()
 import bt_remote_api as api, bt_remote_commands as commands, bt_scheduler_ops as ops, bt_route_pins as pins
 from app import GatewayRuntime, _ledger_command
 from config import GatewayConfig
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args): pass
  def send(self,body,status=200,content_type='application/json'):
   body=body.encode();self.send_response(status);self.send_header('Content-Type',content_type)
   self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  def do_POST(self): api.route_post(self)
  def do_GET(self): api.route_get(self)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
 runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{server.server_port}','synthetic-audit-key','synthetic','synthetic',pathlib.Path(tmp)/'gateway.db'),sender=lambda _:None)
 rdir=Fixture.root/'demo/requirements/REQ-001-forced-failure'
 try:
  snapshot=runtime.web_snapshot()
  run=snapshot['runs'][0];task=run['tasks'][0]
  print('snapshot run fields',sorted(run),'plan count',len(snapshot['plans']))
  js="""const fs=require('node:fs'),vm=require('node:vm'),ts=require('./remote/web/node_modules/typescript');const source=fs.readFileSync('remote/web/src/app/page.tsx','utf8');const code=source.slice(source.indexOf('type Target'),source.indexOf('function prettyTime'));const sandbox={input:JSON.parse(fs.readFileSync(0,'utf8')),exports:{}};vm.createContext(sandbox);try{vm.runInContext(ts.transpileModule(code+';parseSnapshot(input)',{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,sandbox);process.exit(2)}catch(e){console.log('PHONE PARSER:',e.message);if(!e.message.includes('ejecución inválida'))process.exit(3)}"""
  check=subprocess.run(['node','-e',js],input=json.dumps(snapshot),text=True,capture_output=True,check=True)
  print(check.stdout.strip())
  import urllib.request,urllib.error
  for route in ('commands','quotas','routes'):
   request=urllib.request.Request(f'http://127.0.0.1:{server.server_port}/api/remote/v1/{route}',headers={'Authorization':'Bearer synthetic-audit-key'})
   try: urllib.request.urlopen(request,timeout=3);raise AssertionError('expected 404')
   except urllib.error.HTTPError as exc:
    print('keyed read',route,exc.code);assert exc.code==404;exc.close()
  round_path=rdir/'rounds/round-01.json';round_path.parent.mkdir()
  round_path.write_text(json.dumps({'round':1,'status':'open','questions':[{'id':'q1','type':'open','text':'Question'}],'answers':{}}))
  target={'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'}
  round_command={'schemaVersion':1,'idempotencyKey':'synthetic-round-command','type':'answer-round','target':{**target,'kind':'round','roundId':'1'},'precondition':{'state':'open'},'round':1,'answers':{'q1':{'text':'synthetic answer'}}}
  print('round params',_ledger_command(round_command)['params'])
  result=runtime.submit_command(round_command);print('round result',result);assert result['status']=='OK'
  state=commands.target_state('demo/REQ-001','reopen',{'task':'T1'})
  reopen={'schemaVersion':1,'idempotencyKey':'synthetic-reopen-key','type':'reopen','target':target,'precondition':{'state':task['state']}}
  with patch.object(ops,'stop_owner',return_value=0),patch.object(ops,'resume',return_value='synthetic-no-start'):
   result=runtime.submit_command(reopen)
  print('reopen result',result,'before',state,'after',commands.target_state('demo/REQ-001','reopen',{'task':'T1'}))
  assert result['status']=='OK'
  runtime.snapshot_cache=None;after=runtime.web_snapshot()['runs'][0]['tasks'][0]['state']
  print('projected task after reopen',after);assert after=='ready'
  retry={'schemaVersion':1,'idempotencyKey':'synthetic-pinned-retry','type':'retry','target':target,'precondition':{'state':'ready'},'route':{'route_id':'synthetic-route','provider':'codex','model':'synthetic','account':'synthetic'}}
  params=_ledger_command(retry)['params'];print('retry params',params);assert params['route']=='synthetic-route'
  # Do not execute the 180-second retry loop or launch agents; observe real relay validation and dispatch selectors.
  with patch.object(pins,'available',return_value=(object(),)),patch.object(ops,'retry',return_value=['synthetic retry suppressed']),patch.object(ops,'resume',return_value='synthetic-no-start'):
   result=runtime.submit_command(retry)
  print('retry relay',result,'persisted pin',pins.get(rdir,'T1'));assert result['status']=='OK' and pins.get(rdir,'T1')['route']=='synthetic-route'
  challenge=runtime.issue_challenge({'target':'demo/REQ-001','typedReq':'REQ-001'})
  current=commands.target_state('demo/REQ-001','edit-brief',{'task':'T1'})
  edit={'schemaVersion':1,'idempotencyKey':'synthetic-edit-command','type':'edit-brief','target':target,'precondition':{'state':current['state']},'task':'T1','field':'objective','value':'New objective','confirmation':{'challengeId':challenge['challengeId'],'typedReq':'REQ-001'}}
  params=_ledger_command(edit)['params'];print('edit params',params)
  assert params['field']=='objective' and params['value']=='New objective'
  result=runtime.submit_command(edit);print('edit real validation',result)
  assert 'brief de tarea no vacío' not in str(result)
 finally:
  server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY
```

### Probe G — real HTTP cursor error and semantic command failure

```bash
python - <<'PY'
import http.client,json,pathlib,sys,tempfile,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
sys.path.insert(0,str(pathlib.Path('remote/gateway').resolve()))
from app import GatewayRuntime
from config import GatewayConfig
from auth import OAuthConfig,OAuthService,SessionStore
from server import make_handler
class LaptopHandler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  body=b'{"code":"INVALID_CURSOR"}'
  self.send_response(400);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
with tempfile.TemporaryDirectory() as tmp:
 laptop=ThreadingHTTPServer(('127.0.0.1',0),LaptopHandler)
 lt=threading.Thread(target=laptop.serve_forever,daemon=True);lt.start()
 runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{laptop.server_port}','synthetic-key','synthetic','synthetic',pathlib.Path(tmp)/'db'),sender=lambda _:None)
 runtime.event_cursor='stale-cursor'
 runtime._poll_events()
 print('cursor after real HTTP INVALID_CURSOR',runtime.event_cursor)
 assert runtime.event_cursor=='stale-cursor'
 class FakeLaptop:
  def post_json(self,*args):return {'status':'FAILED','code':'ROUTE_UNAVAILABLE','outcome':{'error':'synthetic route unavailable'}}
 runtime.laptop=FakeLaptop()
 store=SessionStore(str(pathlib.Path(tmp)/'auth.db'),'synthetic-session-secret-32-characters')
 token=store.create_session('dav033')
 service=OAuthService(OAuthConfig('synthetic','synthetic','synthetic-session-secret-32-characters','https://frontend.test',store.database_path),store)
 gateway=ThreadingHTTPServer(('127.0.0.1',0),make_handler(service,runtime))
 gt=threading.Thread(target=gateway.serve_forever,daemon=True);gt.start()
 try:
  conn=http.client.HTTPConnection('127.0.0.1',gateway.server_port,timeout=3)
  command={'schemaVersion':1,'idempotencyKey':'synthetic-failed-retry','type':'retry','target':{'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'},'precondition':{'state':'ready'}}
  conn.request('POST','/api/remote/v1/commands',json.dumps(command),{'Cookie':'flow_session='+token,'Origin':'https://frontend.test','X-Flow-Request':'1','Content-Type':'application/json'})
  response=conn.getresponse();payload=json.loads(response.read());print('failed effect public response',response.status,payload)
  assert response.status==200 and payload['status']=='FAILED'
  conn.close()
 finally:
  gateway.shutdown();gateway.server_close();gt.join();laptop.shutdown();laptop.server_close();lt.join();runtime.outbox._db.close()
PY
```

### Probe H — failure before retry exhaustion

```bash
python - <<'PY'
import pathlib,sys
sys.path[:0]=[str(pathlib.Path('skill/scripts').resolve()),str(pathlib.Path('remote/gateway').resolve())]
import bt_remote_events as feed
from notifications import notification_for_event
stamp='2026-10-20T00:00:00Z'
state={'runs':[{'project':'demo','req_id':'REQ-001','max_attempts':3,'tasks':[{'id':'T1','attempts_used':1,'max_attempts':3,'attempt':{'id':'a1','state':'failed','ended_at':stamp,'failure':'synthetic retryable failure'}}]}]}
events=feed.build_events(state);messages=[notification_for_event(e) for e in events]
print('one failure / budget 3 ->',[(e['type'],m[1]) for e,m in zip(events,messages) if m])
assert any(m and 'sin reintentos pendientes' in m[1] for m in messages)
PY
```

### Probe I — ambiguous command outcome classification

```bash
python - <<'PY'
import json,pathlib,sys,tempfile,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.error import URLError
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path('remote/gateway').resolve()))
from app import GatewayRuntime
from config import GatewayConfig
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  self.rfile.read(int(self.headers['Content-Length']))
  self.send_response(200);self.send_header('Content-Length','1');self.end_headers();self.wfile.write(b'{')
with tempfile.TemporaryDirectory() as tmp:
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
 runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{server.server_port}','synthetic-key','synthetic','synthetic',pathlib.Path(tmp)/'db'),sender=lambda _:None)
 command={'schemaVersion':1,'idempotencyKey':'synthetic-unknown-key','type':'pause','target':{'kind':'run','project':'demo','req':'REQ-001'},'precondition':{'state':'running'}}
 try:
  result=runtime.submit_command(command);print('malformed 200 after request accepted',result)
  assert result['code']=='LAPTOP_UNAVAILABLE'
  with patch('upstream.urlopen',side_effect=URLError(ConnectionRefusedError('synthetic refusal'))):
   result=runtime.submit_command(command)
  print('connection refused',result);assert result['code']=='UNKNOWN_OUTCOME'
 finally:
  server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY
```

### Probe P — real installed distributions

```bash
python - <<'PY'
import pathlib, subprocess, sys, zipfile, tarfile
root=pathlib.Path.cwd();sys.path.insert(0,str(root/'tests/migration'))
import installed_wheel
installed=installed_wheel.get()
with zipfile.ZipFile(installed.wheel) as archive:
 names=set(archive.namelist())
 assert 'bt_remote_preconditions.py' in names
 assert 'bt_remote_edit.py' not in names and 'bt_route_pins.py' not in names
 print('wheel omits bt_remote_edit.py and bt_route_pins.py')
with tarfile.open(installed.sdist) as archive:
 names={pathlib.Path(p.name).name for p in archive.getmembers()}
 assert 'bt_remote_edit.py' not in names and 'bt_route_pins.py' not in names
 print('sdist omits both recovery implementation modules')
for name in ['bt_remote_preconditions','bt_remote_edit','bt_route_pins']:
 result=subprocess.run([str(installed.python),'-I','-c',
  f'import sys;sys.path.insert(0,sys.argv[1]);__import__("{name}")',str(installed.site)],
  cwd=installed.work,capture_output=True,text=True)
 print('isolated import',name,'exit',result.returncode)
 assert result.returncode == (0 if name=='bt_remote_preconditions' else 1)
PY
```
