# Independent security and specification audit — T18

**Blocked on prerequisite T15c: three high findings remain open (F2, F19, F62).**
The substantive “Confirmed high findings are fixed” criterion is unmet. Only this report and
`remote/docs/audit.findings.json` are changed. Correcting source, tests or configuration in this read-only task would
violate its contract. The independent checker decides the outcome; this report does not declare the task verified.

Audited entry HEAD: `2e0d8c731b5bceb1975f7cb4e8284a938df0b7e6` (att-0408), 2026-10-21, America/Bogota.
Primary auditor: OpenAI Codex. Fresh independent provider: Anthropic `claude-sonnet-5-5`, tools disabled.
Complete scope: frozen SPEC R1–R18, PLAN.md, PLAN.json revision 3, its amendment, every prerequisite task's acceptance
and command verification, plus the changed producer/consumer boundaries. Current scheduler run revision r9 is not
mistaken for a change to the checked-in revision-3 requirements. T19 is a successor, not an audited prerequisite.

Ledger: **71 findings: 27 rechecked fixed, 44 open (3 high, 34 medium, 7 low), zero accepted.**
All 68 inherited IDs are preserved; F69–F71 record this pass's additional confirmed findings. No risk is accepted by
the auditor. A successful reproduction can demonstrate a defect; it is not a passing product verdict.

## Reconciliation, prior attempts and the repeated-failure cause

Opened both supplied files before editing. Entry `git status --short` and `git diff` were empty. Neither file
contained conflict markers, despite the carry-result warning. No source behavior is rewritten or deleted. Compared
the earlier audited tree `212abc5a76f2f852b06d45763b9640b0babc67b6` with this tree: 29 non-audit source/test/contract
paths changed. Reconciled those changes with every inherited verdict instead of carrying the previous seven open
high findings forward unchanged.

Read the six supplied failure notes and all reachable historical ledgers before edits:

| Attempt | Historical open high findings | Current disposition |
|---|---|---|
| #17 att-0322 / d9e83adc6 | F41, F42 | Actual phone objective/criteria edits and prepublication safeguards now pass E. |
| #18 att-0331 / 8ccc09c9b | F41, F42, F55 | E and persisted-cursor R checks pass. |
| #19 att-0344 / 7b11b3a89 | F2, F61, F62, F63 | Run scoping/timezone repaired; browser consumers lost the review target again. |
| #20 att-0352 / d629327c9 | F2, F36, F63, F66, F67 | Public snapshot, UTC round, HTTP challenges and real exhausted producer now pass. |
| #21 att-0383 / fe4ba03b1 | F2, F36, F41, F42, F63, F66, F67 | Six of these seven are now fixed; E2E reaches a different blocker. |
| #22 att-0402 / 8bf81c180 | Same seven | Fresh typecheck/build and real HTTP review probes expose T15c regressions. |

The repeated rejection cannot be fixed by editing audit labels or weakening the E2E. The old empty-feed producer
and gateway/editor failures have been repaired. The current source has a different integration break:
`page.tsx:406` supplies `target` to a component that now declares only `attemptId`; both review fetches also omit
that target. Consequently the production build fails and actual review requests return 400 INVALID_TARGET. Return
T15c for repair while retaining the correctly scoped native API. T17's updated assertions are useful and should be
rerun after that repair, rather than replaced. F2 is attributed to the root prerequisite T15c, not to an invented
need to weaken the T17 harness. F69 separately records the removed frozen T7 test file.

The 16 omitted older attempts and raw m6 receipts are not available inside this worktree; no retrieval is claimed.
Preserved repairs include: private Caddy bridge topology, remote-only laptop listener, strict challenge one-use/expiry,
owner-approved edit base, refused-edit byte restoration, request/round/edit aliases, selected route pin, selected
failed attempt, native target scoping, flattened public snapshot, UTC event timestamps, true terminal-exhaustion facts,
late-event observation cursors, stream fan-out, session revocation, delivery backoff/history, durable outage dedupe,
and missing-systemctl behavior. Remaining consumer gaps are listed explicitly below.

## Commands and actual results

Installed the existing lockfile with `cd remote/web && npm ci --offline`: exit 0, 320 packages, lockfile unchanged.
Tests use installed dependencies and disposable build/state output inside this worktree; none of the final verification
commands installs packages when dependencies are present. Python 3.14.7 and Node 24.21.0 were available.

The first auth/kit runs failed solely because this deeply nested workspace exceeded Chromium's Unix socket path
limit. Repeated those two affected suites with `TMPDIR=/proc/<audit-process>/fd/<directory-fd>` referring to a temporary
directory inside this same worktree. Both then pass; no browser flags, tests or assertions were relaxed. Browser
commands/builds ran sequentially. Each Python suite used a synthetic BITACORA_ROOT. Runtime artifacts are git-ignored
and are not required by the final reports or clean-copy checks. No real credentials, live server ownership, other
worktree, remote, deployment or agent execution was touched.

Identical frozen commands shared by multiple criteria are executed once, except the three explicit T18 entries:

| Frozen command | Exit | Result |
|---|---:|---|
| `test -s remote/docs/route-pin.md` | 0 | Nonempty file. |
| `python -m json.tool remote/contract/command.schema.json` | 0 | JSON syntax only; contract mismatch remains F17. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py` | 0 | 6 tests; 9.371 s wall.  |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py` | 0 | 25 tests; 6.390 s wall.  |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py` | 0 | 18 tests; 2.292 s wall.  |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py` | 5 | 0 tests; 0.071 s wall. NO TESTS RAN; file absent. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py` | 0 | 12 tests; 3.913 s wall.  |
| `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` | 0 | 28 tests; 2.636 s wall.  |
| `cd skill/scripts && python -m unittest discover -s tests -p test_page*.py` | 0 | 43 tests; 12.145 s wall.  |
| `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py` | 0 | 5 tests; 11.242 s wall.  |
| `cd remote/gateway && python -m unittest discover -s tests -p test_guard.py` | 0 | 7 tests; 3.926 s wall.  |
| `cd remote/gateway && python -m unittest discover -s tests -p test_stream.py` | 0 | 14 tests; 5.453 s wall.  |
| `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py` | 0 | 13 tests; 5.997 s wall.  |
| `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` | 0 | 4 tests; 0.241 s wall.  |
| `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_send.py` | 0 | 3 tests; 0.147 s wall.  |
| `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_bot.py` | 0 | 4 tests; 0.201 s wall.  |
| `cd skill/scripts/bt_scheduler_core && python -m unittest discover -s tests -p test_operations.py` | 0 | 18 tests; 0.938 s wall.  |
| `cd remote/gateway && python -m unittest discover -s tests -p test_auth.py` | 0 | 3 tests; 3.218 s wall.  |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | 0 | 14 tests; 10.017 s wall; one Caddy skip.  |
| `cd remote/web && npm run verify` | 2 | Lint passes; typecheck fails at TS2322 page.tsx:406. Tests/build not reached; 5.811 s wall. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | 1 | npm run build fails at the same type error; setUpClass error, 0 tests, 15.341 s wall. No scenario is claimed executed. |
| `test -s remote/docs/audit.md` (three T18 entries) | 0 each | Existence does not establish that high findings are repaired. |

Final Python suite executions run **217 tests: 216 pass, one Caddy skip**, plus one command running zero tests (F69).
ResourceWarnings about unclosed fixture SQLite connections were observed and not suppressed. The failing E2E adds a
setUpClass error and no executed tests. An extra `cd remote/web && npm test` exits 1: 12/13 tests pass, zero skips,
21.458 s wall; real Chromium measures 366 !== 360 at panel-browser.test.mjs:165 (F18). Thus both the type/build regression
and the pre-existing viewport defect are observed without one hiding the other.

All 23 inherited reproduction blocks were attempted before report edits. Six stopped because repaired behavior
invalidated old defect assertions (I, E, W/Z, AB/AC, AG, AH); these are not misreported as product failures. Corrected
the assertions to the actual current contracts and re-executed the affected blocks. AC's first update incorrectly
expected history outcome delivered; the actual defined outcome is sent, and the corrected final AC passes. G's old
fake returning a bare dict falsely implied the real failed-effect HTTP 200 bug persisted; current G uses a status
pair and AK additionally drives the actual native/public HTTP chain. E checks real revision gates/rebases while only
process stop/start are stubbed. AL explicitly injects a post-publication I/O failure. Final runnable blocks below
carry the current assertions and observed outcomes; exit 0 does not close unrelated criteria.

Not run: Python 3.12 (unavailable), Caddy executable/container connectivity, deployed OAuth/Telegram/Vercel/SSE,
selected-route paid agent execution, phone PWA installation, exhaustive 44 px touch measurements, a dependency advisory
scan, or multiprocess/local-writer stress. The historical rewrite spike is prior evidence only. No T19 artifact is
required to exist yet. No test, source or configuration repair is attempted here.

## Fresh independent other-provider receipt and adjudication

Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
A fresh numbered packet contained SPEC/PLAN/amendment, all gateway modules, actual laptop API/views/ledger/editor/feed/
round/live projection, phone components, Next rewrite config, architecture/contract/runbook/kit and current E2E.
It contained no prior reports, findings or primary conclusions. The provider was static and executed no tests;
the primary auditor independently traced consumers and executed the checks/probes. Omitted source, such as route-pin,
planner internals, CSS, and local listener tests, was inspected separately by the primary auditor where needed.

Receipt: exit 0, subtype success, is_error False, 1 turn,
model usage `claude-sonnet-5-5`, 439364 ms provider / 440.556 s wall,
40 source files, 446,132 characters (446,870 UTF-8 bytes).
Input SHA-256: `ca90def2c7aa7a77af47ebdfa48b11057b141f91c75d5eda4db4fdc61a4d77d6`.
Output JSON SHA-256: `9a15f075d80b1cbd5ac4e78986b35cb60370e8041879666af3f5934be3dc16f2`.

Provider-local H/M numbers below are not ledger IDs. Severity is adjudicated by demonstrated impact, and duplicate
symptoms retain their existing ledger IDs. No other auditor is assumed to cover missing scope.

| Provider item | Verdict, evidence and reason |
|---|---|
| H1 review and build | Confirm high F19/F62, with F2 blocked downstream. Actual TS2322 and actual HTTP 400; native run scoping works. Fixture rendering does not establish the real review path. |
| H2 alert context/buttons | Confirm medium F6 by B/AI: alerts exist but carry a relative path and lack cause/action buttons. No complete alert-delivery loss is shown; severity is medium. |
| H3 /estado | Confirm medium F50 by W: real serializer req/reqId is skipped by bot req_id reader, leaving only a header and no controls. Web control still exists, so not high system-wide control loss. |
| H4 offline | Confirm medium F13 by AK: public online=false is ignored by exact parser and the page selects EN VIVO; no HH:MM. Actual offline commands fail closed and are not queued, bounding the impact. |
| H5 stream | Confirm medium F21 by AG/source: phone path 404, named events versus onmessage and mismatched cursor. Polling fallback remains; no independently measured worst-case 10-second freshness claim. |
| M1 manual challenge | Confirm F46; cancel/delete disabled until an ID is manually supplied, bypassing automatic challenge issuance. Actual HTTP challenge issuance itself is repaired F66. |
| M2 note | Confirm F7 by B. A standalone note has no handler; retry reason/RUN.notes is distinct. Do not conclude all next-attempt notes are absent. |
| M3 quotas | Confirm F44 by Q: actual windows array produces zero parsed accounts. |
| M4 login bucket | Confirm F47 by six real requests L; Caddy clients share the connection peer. Do not trust arbitrary forwarded headers as a fix. |
| M5 OAuth query log | Confirm F4 by A; synthetic callback query is present in the captured request-line/status field. |
| M6 alert scheduling/restart | Confirm F51/F57 by Y/T/AF: delivery blocks the loop and fresh round queues at poll 16, not within 60 s at five-second cadence. Durable same-event restart dedupe itself passes. |
| M7 expiry/backoff | Bounded rejection of expiry itself: the frozen spec explicitly caps stale delivery at one hour; N confirms backoff/expiry/history. Ten attempts below an hour do not exceed that maximum. No valid current producer with a missing timestamp is reproduced. Missing public no-entregado history is independently confirmed as F71. |
| M8 predicates | Confirm F30/F58: stall threshold is 15 min and quota triggers per account. No additional non-exhaustion blocked-task producer defect is established; AA/AH verify current scoped blocked/final-exhaustion paths. |
| M9 snapshot fragility/metadata | Confirm actual criteria/activity mismatch F29 by C. Malformed external plan/round and arbitrary timestamp hypotheses lack a valid producing path in this pass; no extra confirmed failure is invented. |
| M10 edit failure window | Confirm medium new F70 by AL: injected revise failure leaves latest r5/bound r4 and subsequent PLAN_BASE_STALE. Prepublication drift/rollback F42 and actual objective/criteria edits F41 are fixed by E. Wrong default textarea/absent criteria belongs to F8 context. No arbitrary crash/lock-race reproduction is claimed. |
| M11 outcomes | Confirm F16/F40/F52 by I/I2/source. Actual failed-effect HTTP status is now preserved (AK/F39). |
| M12 run-level reopen | Confirm F9; task-scoped reopen works in C, but the run-level form has no taskId. |
| M13 BaseException | Unconfirmed: provider explicitly lacked run_plan internals and demonstrated no built-in escaping SystemExit. No new confirmed finding or blanket catch requirement. |
| Low: redaction/error text/key size | Confirm F56/F68/F48 by S/AJ/B/source, preserving the limits of synthetic tests. Immediate errors expose injected text; public history correctly excludes it. |
| Low: identity/chat hardening | Reject numeric GitHub ID pinning and callback.from.id as frozen requirements: SPEC names login dav033 and configured chat_id. No bypass is demonstrated. |
| Low: env/bind/kit | F3/F54 remain confirmed by J/O. Explicitly filled bridge config works (F1/F22); PLAN's older env spelling alone is not a second broken deployment claim because next.config and current runbook use FLOW_GATEWAY_ORIGIN. No live post-restart health proof is claimed. |
| Low: session/cache/schema | Confirm F31/F11/F17 by AG/B/schema/source; current logout revokes a session, but an existing stream continues. |
| Low: target validation/routes | Reject arbitrary traversal/read SSRF given actual validation/allowlists. Confirm narrower route availability disagreement F64 by AD with unknown quota; do not infer arbitrary route execution. |
| E2E critique | Current test source now explicitly asserts public snapshot and actual challenge issuance, unlike the provider's omission claim. Its control calls are direct-to-gateway and bot loop is disabled; UI offline/review/SSE/restart remain outside its assertions. None of these scenarios executes in this pass because the build fails first. |

Corrections to provider rejections: “only exception types are exposed” is too broad; AJ proves raw immediate handler
error text (F68), while delivery logging/history do avoid raw errors. “state and flow dedupe always unify” is too broad;
U proves two outbox rows when flow and state are observed sequentially (F59), despite same-ID restart dedupe passing.
“CSRF header check” does not mean the required literal 1 is enforced: A accepts wrong nonempty markers (F5). No actual
foreign-Origin command bypass is alleged.

Other rejections retain their bounded reasons: OAuth replay/mismatch is one-use and cookie-bound; foreign GitHub login
cannot get a session; missing/duplicate/foreign POST Origin is refused; target-bound 120-second challenges cannot be
reused in tested paths; same-key repeats and concurrent different-key stale commands do not execute a second tested
effect; review reads are ID/target/ledger-correlated, bounded regular files with O_NOFOLLOW; React renders text nodes,
not executable HTML; offline command relay rejects immediately. No blanket claim covers all secret forms, arbitrary
local writers, unsupported malformed producers or deployed behavior.

## Current findings and verdicts

Every confirmed finding is retained below and in the machine ledger. Fixed means rechecked already repaired in this
source tree; it never means this read-only audit implemented a repair. Evidence refers to the exact command or
embedded Python block and its observed result. Open medium/low findings are recorded, not accepted risks.

### F1 — high / fixed — The Caddy upstream and gateway bind instructions match the frozen container-to-host topology.

Tasks: T16. Rechecked on 2e0d8c731 (att-0408): Probe B (embedded `python -`): exit 0 with a fully filled synthetic env, bind 172.20.0.1. `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 14 tests, one skip because Caddy is absent. The gateway listens on the host bridge and Caddy targets that bridge. No deployed connectivity claim.

### F2 — high / open — The frozen built-web E2E cannot reach its scenarios because the integrated phone app fails production typechecking.

Tasks: T15c. Rechecked on 2e0d8c731 (att-0408): `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py`: exit 1, setUpClass errors, 0 tests, 15.341 s wall. The required npm run build fails at page.tsx:406 with TS2322: target is not a FailureReviewPanel prop. The earlier empty-event cause is repaired (AH); the current harness asserts exactly one exhausted alert, public snapshot and challenge issuance. Do not weaken it: repair T15c/F19, then rerun T17 end to end.

### F3 — medium / open — The restored runbook deploys and restarts before installing the service on a fresh host.

Tasks: T16. Rechecked on 2e0d8c731 (att-0408): Probe J (`python -`), current mode-600 synthetic env: exit 0; fake missing-unit systemctl makes deploy exit 5 after current is switched, deploy --dry-run exits 0, rollback --dry-run exits 2 with no previous release. Initial probe with default env-file permissions correctly failed the new mode-600 guard before deployment; corrected only the synthetic fixture. Runbook still deploys/restarts in step 3 before unit installation in step 4, and reloads host caddy although Caddy is containerized. Preserve the new env permission check.

### F4 — medium / open — Gateway request logging still exposes OAuth code/state query values in its status field.

Tasks: T11a. Rechecked on 2e0d8c731 (att-0408): Probe A: exit 0; real loopback synthetic callback query appears in captured server logging. GatewayHandler.log_message uses args[0], the complete request line, as status despite separately sanitizing the path field. No account takeover or session-token theft demonstrated.

### F5 — medium / open — The mutation marker accepts arbitrary nonempty values and foreign-Origin GET logout bypasses mutation guards.

Tasks: T11a, T15a. Rechecked on 2e0d8c731 (att-0408): Probe A (`python -`): exit 0; wrong X-Flow-Request yields HTTP 200, foreign-Origin GET logout yields 302 and clears the cookie. The new delete_session repair DOES revoke the session, independently checked; the previous nonrevocation subclaim is withdrawn. Actual command POST Origin checks remain effective; no command CSRF bypass alleged.

### F6 — medium / open — Telegram failure alerts now include a relative review path but still lack an actionable absolute link, cause and safe inline actions; retry callbacks are unsupported.

Tasks: T14a, T14b. Rechecked on 2e0d8c731 (att-0408): Fresh Probes B/AI (`python -`, report): exit 0. The new notification_for_event appends /review?project=demo&req=REQ-001&taskId=T1#attempt-a1 and retains run-scoped failure dedupe. Preserve that repair. TelegramSender still sends only chat_id/text; there is no absolute frontend URL, cause, readable task/run context or reply_markup. GatewayRuntime.submit_telegram_command accepts pause/resume only; retry returns INVALID_COMMAND. The current four bot tests pass, but cover their own fixtures. /estado keyboard is separate.

### F7 — medium / open — The public standalone note command has no laptop dispatcher.

Tasks: T5a. Rechecked on 2e0d8c731 (att-0408): Probe B: exit 0; real Ledger.submit(note) with commands.dispatch_handlers() returns COMMAND_NOT_IMPLEMENTED. dispatch_handlers advertises no standalone note handler despite COMMANDS and schema listing it. Retry reason/RUN.notes is separate.

### F8 — medium / open — The phone brief form still cannot edit acceptance criteria.

Tasks: T15f. Rechecked on 2e0d8c731 (att-0408): Static recheck of page.tsx:371-380 and 410-415: only a brief textarea sends field=objective with a string. There is no criteria editor. Probe E now succeeds for objective, criteria and acceptance_criteria through the gateway/native ledger, freezes and rebases real revisions r2-r4; F41 is repaired. The missing phone criteria UI remains.

### F9 — medium / open — Run-level Reabrir ejecución supplies no task identity to the task-scoped operation.

Tasks: T15d. Rechecked on 2e0d8c731 (att-0408): page.tsx run-level commandForm(reopen) omits taskId; bt_remote_commands.TASK_SCOPED/_member_state and dispatch_run_command require params.task. Probe C confirms task-scoped reopen succeeds; that repair does not provide an identity for the run-level form.

### F10 — medium / fixed — A plan waiting for approval emits plan.waiting without a scheduler decision.

Tasks: T6. Rechecked on 2e0d8c731b5bceb1975f7cb4e8284a938df0b7e6 (att-0408): Probe B (embedded `python -`): exit 0; plan_status=review emits plan.waiting without a decision. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py`: exit 0, 18 tests.

### F11 — medium / open — Gateway restart still loses the last snapshot despite the newly wired production stream hub.

Tasks: T12. Rechecked on 2e0d8c731 (att-0408): Probe B (`python -`): exit 0; current runtime keeps old generatedAt offline, replacement runtime with same SQLite database returns None. StreamHub is now instantiated and passed by main, but its snapshot and snapshot_cache are memory-only. Production hub snapshot after restart is empty, not the last persisted state. Retain fan-out wiring while persisting the latest model.

### F12 — medium / open — Expired sessions and Telegram outbox/history remain unbounded beyond the required 90 days.

Tasks: T11, T14a, T5. Rechecked on 2e0d8c731 (att-0408): Probe B: exit 0; creating a session leaves an abandoned expired row. SessionStore prunes sessions only when presented. Current notifications.py now has telegram_history with timestamped rows (F43 fixed), but no 90-day prune of that table/outbox; Ledger.rows still reads all rows. Retention is separate from the now-wired SSE hub and its revocation issue F31.

### F13 — medium / open — The production offline snapshot is read as live by the phone and has no offline-start time.

Tasks: T12, T15b. Rechecked on 2e0d8c731 (att-0408): Probe AK (embedded `python -`): exit 0. Actual authenticated public snapshot after hub.set_online(False) returns HTTP 200, root online=false and no laptop object. Exact page.tsx parseSnapshot leaves laptop undefined; the header condition selects EN VIVO. Probe B independently shows web_snapshot only supplies {online:false}, without offline-start/checkedAt. No public consumer displays the required sin conexion desde HH:MM.

### F14 — medium / fixed — Laptop-side redaction handles the previously missed provider assignments and bearer authorization text.

Tasks: T7, T6. Rechecked on 2e0d8c731b5bceb1975f7cb4e8284a938df0b7e6 (att-0408): Probe B: exit 0; synthetic plain provider assignments and Authorization: Bearer text are redacted. Quoted JSON/URL forms remain F56. The frozen test_remote_review.py command executes zero tests (F69), so it is not cited as passing evidence.

### F15 — medium / fixed — The local panel implements inherited systemd listener activation/reload.

Tasks: T9. Rechecked on 2e0d8c731 (att-0408): `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py`: exit 0, 28 tests, including inherited listener/reload/ownership. Same discovery with test_page*.py: exit 0, 43 tests. No host service touched. Missing-systemctl case is independently repaired, F65.

### F16 — medium / open — The phone discards uncertain command envelopes and generates a new key on resubmission.

Tasks: T15d. Rechecked on 2e0d8c731 (att-0408): Fresh page.tsx checks response.ok, labels UNKNOWN_OUTCOME HTTP 503 Rechazado, and retains history summaries rather than an exact replayable envelope/key; form submitters always call crypto.randomUUID(). Server at-most-once remains valid for a reused key; no duplicate effect through a specific ABA sequence was reproduced, so severity stays medium.

### F17 — low / open — The public command schema differs from production command families, fields and key limits.

Tasks: T3. Rechecked on 2e0d8c731 (att-0408): Fresh schema syntax commands exit 0 only. command.schema.json omits answer-decision, expects singular answer/route text/edit brief; actual phone sends answers/round, route object and field/value. Probe B rejects a 121-character ledger key despite schema maximum 128. contract.md also omits the required review target query and advertises command success/error shapes different from the actual synchronous HTTP responses. This is contract mismatch, not proof of arbitrary execution.

### F18 — medium / open — The required mobile browser test still measures 366 px on a 360 px viewport.

Tasks: T15. Rechecked on 2e0d8c731 (att-0408): `cd remote/web && npm test`: exit 1, 12/13 tests pass, zero skips, 21.458 s wall. Chromium panel-browser.test.mjs:165: 366 !== 360. Separate frozen npm run verify now exits 2 earlier at TS2322 (F19); lint passes, tests/build not reached there. Short TMPDIR avoids the unrelated Chromium Unix socket path limit. Preserve the width assertion.

### F19 — high / open — The integrated phone app does not typecheck or build because FailureReviewPanel lost its target prop.

Tasks: T15c. Rechecked on 2e0d8c731 (att-0408): `cd remote/web && npm run verify`: exit 2 after lint passes, 5.811 s wall. TypeScript src/app/page.tsx:406:131, TS2322: {attemptId:string;target:string} is not assignable to {attemptId:string}; target does not exist. failure-review-panel.tsx:52 declares only attemptId. T17 separately invokes npm run build and fails at the identical diagnostic before starting any scenario. No code was changed by this audit.

### F20 — high / fixed — The phone accepts the actual gateway login session dialect.

Tasks: T15a. Rechecked on 2e0d8c731 (att-0408): Probe A: exit 0; actual authenticated gateway GET /api/auth/session returns HTTP 200 {login:dav033}. Short-TMPDIR `cd remote/gateway && python -m unittest discover -s tests -p test_auth.py`: exit 0, 3 tests. `cd remote/web && npm test`: sessionContractObserved assertion passes before the width failure; the overall command fails (F18).

### F21 — medium / open — The production SSE and plain event routes disagree with the phone path and event dialect.

Tasks: T12, T6, T15b. Rechecked on 2e0d8c731 (att-0408): Updated Probe AG: exit 0. Authenticated GET /api/remote/v1/events returns 404, and phone /api/remote/v1/events/stream returns 404. The explicit /api/remote/v1/stream works but sends named event/resync frames and epoch:sequence IDs. page.tsx opens events/stream?after=<snapshot cursor> and only handles onmessage. Polling fallback exists. Preserve the hub/fan-out while aligning path, cursor and resync handling.

### F22 — medium / fixed — A completely filled example configuration starts parsing; the prior mandatory-blank allegation is superseded.

Tasks: T16. Rechecked on 2e0d8c731 (att-0408): Probe B (`python -`): exit 0; all example keys filled with synthetic values parse in GatewayConfig and OAuthConfig. `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 14 tests, one Caddy skip. Empty optional bind remains F54.

### F23 — medium / fixed — Native keyed command history is present and read through the authenticated gateway.

Tasks: T4a, T15d. Rechecked on 2e0d8c731 (att-0408): Probes C/AG: exit 0, actual keyed commands endpoint and public commands/history reads return HTTP 200 with commands/nextCursor; AJ confirms public history excludes injected exception text. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py`: exit 0, 25 tests. No successful current web build is claimed.

### F24 — high / fixed — Wheel and sdist include and import the edit and route-pin implementation modules.

Tasks: T8, T8a. Rechecked on 2e0d8c731 (att-0408): Probe P: exit 0. Fresh built wheel and sdist include bt_remote_edit.py and bt_route_pins.py; isolated imports of bt_remote_api, bt_remote_commands, bt_remote_edit and bt_route_pins each exit 0. Build/install outputs are disposable inside this worktree.

### F25 — medium / open — The failed-task review link identifies the selected attempt but its real detail request omits the required target.

Tasks: T15c. Rechecked on 2e0d8c731 (att-0408): `cd remote/web && npm test`: selected rejected-task link and its fixture review render before the width assertion. Static trace of review/page.tsx:82 and failure-review-panel.tsx:58 shows both fetch review without ?target=. Updated AG executes that exact missing-target URL and receives HTTP 400 INVALID_TARGET. Thus fixture selection alone does not restore actual laptop reviews; see high F62. Keep the selected attempt identity when fixing target forwarding.

### F26 — medium / open — Ready recovery controls disappear after reload or in another tab.

Tasks: T15f, T15d. Rechecked on 2e0d8c731 (att-0408): Probe C: exit 0; actual task reopen projects ready and pinned retry succeeds with synthetic availability/process-start seams. page.tsx still gates recovery on recovering/reopenedForRecovery; reopenedTasks is an in-memory useRef. Node source fixture passes, but does not prove a reload of the real snapshot. Editor F41/F42 are now repaired.

### F27 — low / open — Command limits remain shared by owner login across sessions instead of per session.

Tasks: T11a. Rechecked on 2e0d8c731 (att-0408): Current server.py uses authenticated login as the commands/challenges rate bucket, sharing quota between all dav033 sessions; exact auth/guard tests pass (3/7). This is stricter than R17 but not an authentication bypass; shared anonymous login availability remains F47.

### F28 — high / fixed — Distinct-key concurrent preconditions serialize with the remote ledger effect.

Tasks: T5. Rechecked on 2e0d8c731 (att-0408): Probe D: exit 0. Two concurrent different keys for running->paused produce exactly one handler effect and one STALE_PRECONDITION rejection, with two ledger rows. This checks process-local serialization, not arbitrary multiprocess writers.

### F29 — medium / open — The snapshot still omits frozen task criteria and phone-compatible activity metadata.

Tasks: T4a. Rechecked on 2e0d8c731 (att-0408): Probe C: exit 0; actual frozen T1 acceptance_criteria is nonempty but actual snapshot plan task acceptanceCriteria is []. Serializer reads the outer task rather than task.detail. Native run lastActivityAt/attempt last_activity_at also differ from phone lastSeenAt/updatedAt. Current collection of plans/rounds/decisions and the repaired public envelope are preserved; no blanket missing-snapshot claim.

### F30 — medium / open — Stalled-attempt notifications start after 15 minutes rather than the required more than 10 minutes.

Tasks: T6. Rechecked on 2e0d8c731 (att-0408): Probe B: exit 0; live attempt has no attempt.stalled at +660 s and does at +901 s. bt_remote_events.STALL_SECONDS=15*60 conflicts with SPEC R10. The emitted text says more than 10 minutes but the threshold does not.

### F31 — low / open — The restored authenticated SSE connection continues after its session is revoked.

Tasks: T11, T12. Rechecked on 2e0d8c731 (att-0408): Probe AG (`python -`): exit 0; actual /api/remote/v1/stream accepts a valid synthetic session; SessionStore.delete_session revokes it; publishing a new synthetic event still sends its data frame over the same connection. server.py stream loop never rechecks the session. The prior fixed verdict depended on absent production streaming and is superseded. No stolen-cookie or process-wide denial claim; terminate or periodically revalidate revoked/expired sessions.

### F32 — high / fixed — The gateway preserves the route selector, model and account pin.

Tasks: T13. Rechecked on 2e0d8c731 (att-0408): Probe C: exit 0. Actual phone route_id object translates to route, model and account; actual ready retry succeeds and bt_route_pins.get persists the chosen tuple. Candidate availability and process start are explicitly synthetic seams; no paid/live agent execution is claimed.

### F33 — high / fixed — The gateway preserves round/answers and edited field/value.

Tasks: T13. Rechecked on 2e0d8c731 (att-0408): Probes C/AI/E: exit 0. Actual keyed answer-round stores q1 answers; decision aliases requestId/request_id are retained; objective/criteria field/value reaches native edit, freezes and rebases real revisions. `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py`: exit 0, 13 tests.

### F34 — medium / fixed — Frozen notification and delivery test files exist and execute.

Tasks: T14, T14a. Rechecked on 2e0d8c731 (att-0408): `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py`: exit 0, 4 tests. Same discovery with test_telegram_send.py: exit 0, 3 tests; test_telegram_bot.py: exit 0, 4 tests. Passing these fixture suites does not repair the separately reported production notification gaps.

### F35 — high / fixed — The native snapshot parses with the real phone parser for a nonempty run list.

Tasks: T4a. Rechecked on 2e0d8c731 (att-0408): Probe C: exit 0; the exact parseSnapshot function transpiled from current page.tsx accepts an actual laptop snapshot with one seeded M1 run and plans. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py`: exit 0, 6 tests. Current public envelope independently checked in AG.

### F36 — high / fixed — The production gateway now returns the flattened snapshot accepted by the phone parser.

Tasks: T12. Rechecked on 2e0d8c731 (att-0408): Updated Probe AG: exit 0. Actual bt_server.RemoteHandler, GatewayRuntime.poll_once and main-equivalent make_handler(service,hub=runtime.hub,runtime=runtime) return authenticated HTTP 200 with schemaVersion=1 and one top-level run. Exact installed-TypeScript parseSnapshot accepts it. test_stream.py: exit 0, 14 tests. Offline liveness metadata remains distinct F13.

### F37 — medium / fixed — Final exhaustion emits one terminal failure rather than retrospective alerts for each earlier attempt.

Tasks: T6. Rechecked on 2e0d8c731 (att-0408): Updated AB and AH embedded `python -` probes: both exit 0. Fixture with failed a1/a2/a3 and exhausted authoritative budget emits only a3. Real M1 max_attempts=3 projection likewise emits exactly one attempt.failed for att-0003; Probe H confirms retryable failure emits none. Current T17 expectation is one alert. test_remote_events.py: exit 0, 18 tests.

### F38 — medium / fixed — Structured HTTP INVALID_CURSOR reaches the gateway cursor-reset branch.

Tasks: T13, T12. Rechecked on 2e0d8c731 (att-0408): Probe G: exit 0; real HTTP 400 {code:INVALID_CURSOR} resets GatewayRuntime.event_cursor to empty. `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py`: exit 0, 13 tests. Rebuilding from the beginning remains F57.

### F39 — medium / fixed — The public relay preserves actual native failed-effect HTTP status.

Tasks: T13, T15d. Rechecked on 2e0d8c731 (att-0408): Probe AK: exit 0. A real native handler raising a synthetic ValueError yields HTTP 500 FAILED/EFFECT_FAILED through actual LaptopClient, GatewayRuntime and authenticated GatewayHandler. Updated G additionally checks tuple status preservation. Historical G used an obsolete fake returning only a dict; current production post_json returns (status,body). Phone response.ok therefore rejects this actual failure. Ambiguous success remains F40.

### F40 — medium / open — Ambiguous or truncated successful upstream responses are still misclassified or escape the runtime.

Tasks: T13. Rechecked on 2e0d8c731 (att-0408): Updated I: exit 0; accepted POST with malformed HTTP 200 JSON returns LAPTOP_UNAVAILABLE without the replay key, not UNKNOWN_OUTCOME. Connection refusal now also returns LAPTOP_UNAVAILABLE, so the old refusal-as-unknown subclaim is withdrawn. I2: exit 0; truncated accepted Content-Length response raises uncaught IncompleteRead. Actual HTTP refusal statuses are preserved (AK/F39).

### F41 — high / fixed — The actual phone objective dialect and criteria aliases now edit and rebase approved revisions.

Tasks: T8a. Rechecked on 2e0d8c731 (att-0408): Updated Probe E: exit 0. Real keyed HTTP through GatewayRuntime accepts field=objective/value, then criteria and acceptance_criteria arrays; freezes r2/r3/r4 with source remote-owner and ops.bound_plan reaches each revision. Only owner process stop/start are stubbed; actual revision/consumer gates/rebase execute. test_remote_recovery.py: exit 0, 12 tests. acceptanceCriteria camelCase is not a documented current field; criteria UI remains F8.

### F42 — high / fixed — Remote edits reject unrelated working-plan drift and restore bytes when publication is refused.

Tasks: T8a. Rechecked on 2e0d8c731 (att-0408): Updated Probe E: exit 0. After successful actual edits through r4, unrelated T2 working drift returns FAILED/PLAN_DRIFT without modifying bytes or publishing r5. PLAN.md review-state refusal also preserves bytes/latest/binding. An injected publishable_problem refusal after temporary working write restores exact pre-edit bytes and keeps latest/bound r4. test_remote_recovery.py: exit 0, 12 tests. No arbitrary post-publication crash rollback is claimed.

### F43 — medium / fixed — Telegram delivery has bounded expiry, backoff and timestamped per-attempt history.

Tasks: T14a. Rechecked on 2e0d8c731 (att-0408): Probe N: exit 0. Expired message drops without delivery at attempt 0; failed delivery retries at +5 seconds, records timestamp/attempt, then drops at one hour preserving the attempted count. test_telegram_send.py: exit 0, 3 tests. Ninety-day pruning remains F12.

### F44 — medium / open — The restored quota endpoint returns an array of windows that the phone discards.

Tasks: T4a. Rechecked on 2e0d8c731 (att-0408): Probe Q: exit 0; actual keyed route_get /quotas with one synthetic account/five_hour window returns windows=[{window,usedPercent,resetsAt}], observedAt string. Exact QuotasPanel parser transpiled with installed TypeScript calls record(account.windows), which rejects arrays: parsed account count is 0. Phone expects a windows object with used_percent/resets_at and numeric observedAt. Restore compatible projection or normalize both dialects; mock browser data currently hide the mismatch.

### F45 — medium / fixed — The liveness entrypoint fixture includes required OAuth settings.

Tasks: T10. Rechecked on 2e0d8c731 (att-0408): `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py`: exit 0, 5 tests. The configuration-refusal test intentionally prints missing keys; the valid fake-laptop entrypoint starts and is stopped by its test. No deployed runtime assertion.

### F46 — medium / open — Phone cancel/delete plan actions require a challenge ID the interface never obtains or displays.

Tasks: T15d. Rechecked on 2e0d8c731 (att-0408): Fresh source inspection page.tsx: buttons disabled unless confirmation text is nonempty and typedReq matches; user must enter Id del reto. sendCommand only auto-fetches a challenge when challengeId is absent, but these forms require it present. No UI requests/displays an ID for copying. Approve/launch auto-challenge behavior remains valid. ; normal forms need the same server-issued challenge flow.

### F47 — medium / open — Anonymous callers behind Caddy share a login throttle and can exhaust the owner login bucket.

Tasks: T11a. Rechecked on 2e0d8c731 (att-0408): Probe L: exit 0; six synthetic forwarded client addresses reaching one proxy socket receive 302,302,302,302,302,429. server.py keys both login-start and callback buckets on client_address[0]; deployed Caddy is the common upstream peer. An unauthenticated requester can keep the shared five-per-minute start bucket full. Do not trust arbitrary public forwarded headers; derive identity only at the trusted proxy boundary.

### F48 — low / open — The documented 24-character gateway-key minimum is not enforced at startup.

Tasks: T16. Rechecked on 2e0d8c731 (att-0408): Probe B: exit 0 with short synthetic gateway keys. Static recheck: GatewayConfig only requires a nonempty key; bt_server.serve_remote opens its loopback handler without validating the documented key minimum. test_remote_api.py: exit 0, 6 tests, but has no startup length assertion. Empty expected key still fails authenticated requests closed; no bearer bypass is alleged.

### F49 — medium / open — A malformed authenticated native command drops the HTTP connection before validation instead of returning INVALID_COMMAND.

Tasks: T5. Rechecked on 2e0d8c731 (att-0408): Probe V: exit 0 reproducer. A real loopback POST to bt_remote_api.route_post with synthetic valid gateway key and {idempotency_key:'synthetic-valid-key',command:'pause'} drops the connection with KeyError('target'); the same request without the key returns HTTP 401. bt_remote_commands.fingerprint:264 indexes required fields before validate:268, and Ledger.submit:385-387 catches TypeError/ValueError but not missing-field KeyError. Validate required envelope fields before fingerprinting and return HTTP 400/INVALID_COMMAND. The public gateway fills these keys, so this is native-boundary robustness, not an unauthenticated access bypass.

### F50 — medium / open — Telegram /estado skips every real snapshot run because it reads req_id instead of req/reqId.

Tasks: T14b. Rechecked on 2e0d8c731 (att-0408): Updated W: exit 0; actual inlined bt_remote_api._snapshot projects a synthetic active run with req/reqId; real TelegramBot._send_status sends only the Ejecuciones activas header and no run/keyboard because it reads req_id. Only the snapshot data provider is substituted; real serializer and bot parser execute.

### F51 — medium / open — Inline Telegram delivery can block the production five-second liveness polling cadence.

Tasks: T14a, T10. Rechecked on 2e0d8c731 (att-0408): Fresh report Probe W/Y/Z/O: exit 0; GatewayRuntime.poll_once with 20 due messages and a deterministic sender advancing the clock by the default 5-second request timeout consumes 100 simulated seconds while making exactly one health probe. app.py calls deliver_due inline and notifications.py sends up to 20 sequential messages before returning. This is a deterministic scheduling reproduction, not a measured real Telegram outage; isolate delivery or give it a budget compatible with the five-second health cadence.

### F52 — low / open — The command deadline defaults to five seconds rather than the specified fifteen seconds.

Tasks: T10, T13. Rechecked on 2e0d8c731 (att-0408): Updated W/Y/Z/O: exit 0. Synthetic required config without overrides gives request_timeout=5.0, passed to LaptopClient POST. TimeoutError becomes UNKNOWN_OUTCOME; malformed success has the distinct F40 problem. Separate health and command deadlines are not implemented.

### F53 — medium / open — A Telegram-command-induced offline transition can suppress the long-offline active-run alert.

Tasks: T10, T13, T14. Rechecked on 2e0d8c731 (att-0408): Updated Z: exit 0. Three _submit_ledger_command UpstreamErrors with cached active-run state mark offline but leave offline_generation=0; a health poll after 901 seconds yields zero outbox rows. Current web/challenge relay no longer records those liveness failures, so the old challenge-offline subclaim is withdrawn (it remains online in the probe). Keep one durable transition owner and the repaired restart dedupe.

### F54 — medium / open — An explicitly empty gateway bind is accepted and passed to the HTTP server as a wildcard address.

Tasks: T10. Rechecked on 2e0d8c731 (att-0408): Fresh report Probe W/Y/Z/O: exit 0. GatewayConfig.from_env and OAuthConfig.from_env accept required synthetic configuration with GATEWAY_BIND=''; create_server passes ('',8790) to the mocked ThreadingHTTPServer constructor (Python IPv4 wildcard bind semantics). No wildcard listener was actually opened. config.py uses get without rejecting the empty value; deploy.sh required-key checks omit GATEWAY_BIND. The runbook correctly instructs 172.20.0.1 (F1 fixed), but malformed production config still fails open at this boundary. Reject empty/wildcard binds or normalize deliberately to the documented private interface. No unauthenticated command bypass is alleged.

### F55 — high / fixed — Persisted first-observation cursors deliver late-derived events after the saved cursor.

Tasks: T6. Rechecked on 2e0d8c731 (att-0408): Probes R/T: exit 0. Late stall and round appear after a previously persisted cursor and enter the outbox. Outage generation remains 1 across replacement runtimes sharing the database and total sends remain 1. test_remote_events.py: exit 0, 18 tests. This does not close from-now startup semantics F57.

### F56 — medium / open — Quoted JSON credentials and database connection passwords remain visible inside log and verification strings.

Tasks: T6, T7, T15c. Rechecked on 2e0d8c731 (att-0408): Probe S: exit 0; feed.redact leaves synthetic password and refresh_token values in serialized JSON and the synthetic DATABASE_URL password unchanged. The exact phone redactReviewText also leaves the quoted JSON password; structured dict password is correctly redacted. bt_remote_events.py,34-42 requires an unquoted name adjacent to colon/equal inside strings; bt_remote_api.py passes logTail and verification text through it. F14 remains fixed only for its original plain provider assignment and bearer-text cases, both freshly rechecked. The observed gap is bounded to these synthetic known credential forms, not a claim that arbitrary secret detection is exhaustive.

### F57 — medium / open — Gateway cursor reconstruction starts from the beginning and lets old feed pages delay fresh notifications beyond 60 seconds.

Tasks: T14. Rechecked on 2e0d8c731 (att-0408): Updated Probe T: exit 0; a fresh runtime calls events with empty cursor and sends a run.finished that predates startup but is within the restored one-hour expiry. Gateway still keeps event_cursor only in memory and invalid-cursor reset also starts from beginning. The former continuous-outage generation-reset component is now repaired: with one durable database and simulated wall/monotonic clocks, outage generation stays 1 across replacement runtimes and total sends stays 1. Same-ID outbox dedupe also remains effective. Only rebuild-from-now remains open; no accepted risk. Probe AF: exit 0; 3,000 older non-notifying command events precede a fresh round in the persisted feed. _poll_events consumes only one 200-event page per five-second poll and ignores hasMore: no alert after thirteen polls (t=60 s), new round queued on poll sixteen (t=75 s). This is deterministic page/cadence arithmetic, not a live latency measurement.

### F58 — medium / open — Quota notifications have per-account triggers without the frozen all-accounts-exhausted condition.

Tasks: T6, T14. Rechecked on 2e0d8c731 (att-0408): Probe U: exit 0; build_events receives one exhausted account and one available account, yet notification_for_event creates a quota-exhaustion alert. bt_remote_events.py emits independently per profile and notifications.py renders each; neither checks whether every account is exhausted as required by R10. This is an alert-condition/spec gap, not proof that all-account exhaustion receives no messages. Preserve source freshness and dedupe when introducing the aggregate condition.

### F59 — medium / open — The same failed attempt can enqueue two alerts when first observed in the flow bus and later in the run projection.

Tasks: T6. Rechecked on 2e0d8c731 (att-0408): Probe U: exit 0; failure of demo/REQ-001 T1/a1 is first represented by flow row flow-1, then by the run-state attempt with its ended_at one second later. Real build_events/page and NotificationOutbox store two different dedupe-key rows. bt_remote_events.py suppresses flow duplicates only inside one current projection; from_flow identity at 176-178 differs from the attempt identity at 79, so sequential observations bypass durable dedupe. These fixtures demonstrate one semantic failure under both producer forms, not a measured frequency in a deployed run. R11 requires a stable key for the same event.

### F60 — low / open — An unauthenticated Unicode OAuth state drops the callback connection instead of returning a controlled invalid-state response.

Tasks: T11. Rechecked on 2e0d8c731 (att-0408): Probe X: exit 0; real loopback gateway GET callback with synthetic code, query state=%C3%A9 and cookie flow_oauth_state="é" terminates its request with TypeError from hmac.compare_digest on non-ASCII strings. The handler error hook records TypeError and HTTP client gets RemoteDisconnected. server.py does not validate ASCII before comparison. No state bypass, session issuance or whole-process denial of service is demonstrated; the existing one-use/replay protections remain.

### F61 — high / fixed — Blocked-event identities remain run-scoped when runs share attempt IDs.

Tasks: T6. Rechecked on 2e0d8c731 (att-0408): Updated AA: exit 0. Two actual M1 runs both allocate att-0001; generated blocked-event dedupe keys differ and outbox keeps two rows. test_remote_events.py: exit 0, 18 tests. Semantic flow/state duplication is separately F59.

### F62 — high / open — Both phone failure-review callers omit the required run target and cannot load actual reviews.

Tasks: T15c. Rechecked on 2e0d8c731 (att-0408): Updated AG: exit 0. Authenticated /attempts/att-0003/review?target=demo%2FREQ-001 returns HTTP 200; the exact query-free URL fetched by both failure-review-panel.tsx:58 and review/page.tsx:82 returns HTTP 400 INVALID_TARGET. AA confirms native target scoping selects distinct causes for two runs sharing att-0001. Restore target forwarding in T15c, preserving native scope checks. The former native defect is repaired; the current browser-consumer regression is high because R9 failure review is unusable.

### F63 — high / fixed — Fresh Bogota rounds now have explicit UTC timestamps and are delivered before expiry.

Tasks: T6. Rechecked on 2e0d8c731 (att-0408): Updated AC: exit 0 with TZ=America/Bogota/time.tzset. Actual bt_rounds.new_round on a two-hour-old plan writes a fresh created_at ending Z. feed.collect derives round.waiting with that UTC creation time; actual GatewayRuntime/outbox sends once with outcome sent, attempt 1, rather than expired/dropped. test_remote_events.py: exit 0, 18 tests. One-hour expiry is retained.

### F64 — medium / open — The routes endpoint lists unknown-quota routes as available while retry refuses those same candidates.

Tasks: T8. Rechecked on 2e0d8c731 (att-0408): Probe AD: exit 0; one synthetic candidate with valid authorization/runtime/source and quota_status=unknown is listed available by actual bt_remote_recovery.route_options, but actual bt_route_pins.available with identical candidate/route returns []. The former checks quota != exhausted; the latter requires quota == available. No actual account/quota source was read. Use the same availability rule; refusal is safe but contradicts the selectable route list.

### F65 — medium / fixed — Missing systemctl preserves local-panel startup while uncertain ownership fails closed.

Tasks: T9. Rechecked on 2e0d8c731 (att-0408): Probe AE2: exit 0. shutil.which(systemctl)=None causes one mocked detached start and no service calls; present-but-failing service control starts no competing process. test_platform.py: exit 0, 28 tests. Live systemd ownership is not changed.

### F66 — high / fixed — Keyed native challenge issuance is restored and the real public relay preserves HTTP 201.

Tasks: T5b. Rechecked on 2e0d8c731 (att-0408): Updated AG: exit 0. Actual native POST /api/remote/v1/challenges with synthetic bearer and authenticated public gateway POST both return HTTP 201, challengeId, target demo/REQ-001 and expiresIn=120. test_remote_commands.py: exit 0, 25 tests, including challenge expiry/one-use/wrong target. Phone manual cancel/delete challenge UX remains F46.

### F67 — high / fixed — Actual M1 run projection now supplies exhaustion facts and produces the terminal failure event.

Tasks: T6. Rechecked on 2e0d8c731 (att-0408): Updated AH: exit 0. Actual T17 fixture exhausts three M1 attempts; live.run_summaries exposes attempts_used=max_attempts=3, retries_remaining=0, retry_exhausted=true, reason=attempts_exhausted. Real build_events emits one attempt.failed for att-0003 with retryExhausted. H confirms no alert for a retryable failure. test_remote_events.py: exit 0, 18 tests. Full E2E is blocked by unrelated F19 build failure.

### F68 — low / open — Immediate command error responses forward handler exception text without redaction.

Tasks: T5. Rechecked on 2e0d8c731 (att-0408): Probe AJ (`python -`, report): exit 0. Injecting a handler ValueError with a synthetic FLOW_GATEWAY_KEY assignment into the real native HTTP command path produces FAILED/EFFECT_FAILED with that text unchanged through GatewayRuntime; the existing redactor removes it when explicitly called. Ledger.submit catches str(exc)[:300] without sanitizing. Public command history correctly excludes the exception value. This confirms the error boundary with an injected failure, not a built-in secret-bearing exception, live credential leak or theft; severity stays low.

### F69 — medium / open — The frozen T7 failure-review verification file is absent, so its command executes no tests.

Tasks: T7. Rechecked on 2e0d8c731 (att-0408): `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py`: exit 5, Ran 0 tests, NO TESTS RAN. git diff from the previous audited tree shows that file removed. Native scoped review behavior is independently exercised in AA/AG, but those report probes do not restore the frozen prerequisite suite. Restore meaningful R9 regression tests; do not weaken discovery.

### F70 — medium / open — A failure after publishing an edited revision strands the run on its previous revision.

Tasks: T8a. Rechecked on 2e0d8c731b5bceb1975f7cb4e8284a938df0b7e6 (att-0408): Probe AL (embedded python): exit 0. After real owner edits freeze/rebase r2-r4, an injected OSError at ops.apply(revise) yields FAILED with latest approved revision r5 but bound run r4. The next owner edit returns PLAN_BASE_STALE. bt_remote_edit.py:99-109 has no durable post-publication reconciliation; its byte restoration covers only failures before freeze. This is a bounded failure-injection result, not a spontaneous production outage. Preserve the approved revision and reconcile the pending rebase; do not delete published history. The original unrelated-drift/prepublication defect F42 is separately repaired.

### F71 — medium / open — Undelivered Telegram status is stored internally but unavailable in the public history or web.

Tasks: T14a. Rechecked on 2e0d8c731b5bceb1975f7cb4e8284a938df0b7e6 (att-0408): Probe N: exit 0; expired/retried/dropped notifications exist in NotificationOutbox.history. AG public /history returns commands/nextCursor only. Static read_routes.py allowlist and bt_remote_api._command_history expose only the command ledger; the phone renders that ledger and has no delivery-history reader. Thus the frozen edge-case requirement to show no entregado in history cannot be met. One-hour expiry and durable delivery records are preserved (F43).

## Frozen coverage and handoff

| Scope | Current conclusion |
|---|---|
| R1/R2/R3/R16/R17 | Auth/key/tunnel/session guards checked through current suites and A/L/V; F4/F5/F27/F31/F47/F48/F49/F54/F60/F68 remain bounded hardening/robustness gaps. No live deployment claim. |
| R4/R7/R9/R15 | Native/public snapshot fixed; actual review consumers F62 high and build F19 high block usable web. Offline metadata F13, criteria/activity F29, quotas F44, stream F21 and redaction F56 remain. |
| R5/R6/R8/R13 | Real reopen, selected pin, round answer and approved edit/rebase checked in C/E. Challenge HTTP restored in AG. Standalone note, run-level reopen, recovery persistence, manual challenge UI, outcome replay and post-publication failure remain listed. |
| R10/R11/R12 | UTC fresh rounds, terminal exhaustion and observation cursors repaired. Bot/context, threshold/quota, sequential dedupe, delivery cadence, restart backlog and no-entregado history remain listed. |
| R14 | Lint passes, type/build fails, mobile browser measures 366 px on 360 px. Theme/local-font/manifest tests pass; PWA install and exhaustive touch targets not run. |
| R18 | Platform 28, page 43 and core operations 18 tests pass. Remote review frozen suite is absent (F69). Current exact E2E errors before executing scenarios. |

Return **T15c** for the open high findings: restore the typed target prop and forward project/REQ target in both
review HTTP callers. Retain the existing selected failed-attempt identity and native target authorization. Then rerun
T17's unchanged current end-to-end assertions. F69 requests meaningful restoration of T7's missing frozen tests;
F70 belongs to T8a's post-publication recovery; F71 belongs to T14a's public delivery status. Other open medium/low
items retain their named task attribution; no owner acceptance is invented.

## Reproduction commands

Run the following blocks from repository root with dependencies already installed. Each uses synthetic state under
this worktree and cleans its own scratch files. No paid provider or account/quota reader is required. C/E seed
confirmation in the native ledger to isolate command semantics; AG separately exercises real HTTP issuance. Agent
availability/starts and post-publication faults are stubbed only where stated. These are report-contained audit
probes, not substitutes for missing frozen tests. All final blocks exit 0 for their specified observations, including
open defects; this is not product acceptance.

### Probe A — real gateway HTTP boundaries

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import http.client, io, json, logging, pathlib, sys, tempfile, threading
from http.server import ThreadingHTTPServer
sys.path.insert(0, str(pathlib.Path('remote/gateway').resolve()))
from auth import OAuthConfig, OAuthService, SessionStore
from server import make_handler
class Runtime:
    def submit_command(self, value): return {'status': 'OK'}
    def read_remote(self, path): return {'events': [], 'nextCursor': ''}
with tempfile.TemporaryDirectory() as tmp:
    db = str(pathlib.Path(tmp)/'sessions.db')
    secret = 'synthetic-secret-at-least-32-characters'
    store = SessionStore(db, secret)
    service = OAuthService(OAuthConfig('synthetic', 'synthetic', secret, 'https://frontend.test', db), store)
    token = store.create_session('dav033')
    server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(service, runtime=Runtime()))
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
        print('foreign logout', logout[::2]); assert logout[0] == 302 and store.get_session(token) is None
        for path in ('/api/remote/v1/events/stream?after=abc',):
            result = request('GET', path, cookie); print('SSE', path, result[:2]); assert result[0] == 404
        request('GET', '/api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE')
        leaked = 'code=SYNTHETIC_CODE&state=SYNTHETIC_STATE' in capture.getvalue()
        print('query logged', leaked); assert leaked
    finally:
        server.shutdown(); server.server_close(); worker.join(); log.removeHandler(sink)
PY_AUDIT
```

### Probe B — cache, retention, redaction, events, commands and filled config

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
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
    assert again.web_snapshot() is None
    assert runtime.web_snapshot()['laptop'] == {'online': False}
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
PY_AUDIT
```

### Probe D — concurrent distinct-key preconditions

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
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
PY_AUDIT
```

### Probe C — real snapshot/parser, read routes, reopen/retry and edit dialect

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
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
  runtime._refresh_active_run_cache();snapshot=runtime.web_snapshot()
  run=snapshot['runs'][0];task=run['tasks'][0]
  print('snapshot run fields',sorted(run),'plan count',len(snapshot['plans']))
  frozen=json.loads((rdir/'plan-revisions/PLAN.r1.json').read_text())
  print('F29 bound task criteria',frozen['tasks'][0]['acceptance_criteria'],'projected',snapshot['plans'][0]['tasks'][0]['acceptanceCriteria'])
  assert frozen['tasks'][0]['acceptance_criteria'] and snapshot['plans'][0]['tasks'][0]['acceptanceCriteria']==[]
  js="""const fs=require('node:fs'),vm=require('node:vm'),ts=require('./remote/web/node_modules/typescript');const source=fs.readFileSync('remote/web/src/app/page.tsx','utf8');const code=source.slice(source.indexOf('type Target'),source.indexOf('function prettyTime'));const sandbox={input:JSON.parse(fs.readFileSync(0,'utf8')),exports:{}};vm.createContext(sandbox);const parsed=vm.runInContext(ts.transpileModule(code+';parseSnapshot(input)',{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,sandbox);if(parsed.runs.length!==1)process.exit(2);console.log('PHONE PARSER: parsed real nonempty runs',parsed.runs.length)"""
  check=subprocess.run(['node','-e',js],input=json.dumps(snapshot),text=True,capture_output=True,check=True)
  print(check.stdout.strip())
  with patch('bt_quota_live.read_all_live',return_value=[{'profile':'synthetic','provider':'codex','status':'available','windows':{}}]),patch('bt_remote_recovery.route_options',return_value=[{'route_id':'synthetic-route','provider':'codex','model':'synthetic','profile':'synthetic','account':'synthetic','available':True}]):
   for route in ('commands','quotas','routes?target=demo%2FREQ-001&task=T1'):
    model=runtime.read_model('/api/remote/v1/'+route)
    print('keyed read',route,sorted(model)); assert isinstance(model,dict)
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
  runtime._refresh_active_run_cache();after=runtime.web_snapshot()['runs'][0]['tasks'][0]['state']
  print('projected task after reopen',after);assert after=='ready'
  retry={'schemaVersion':1,'idempotencyKey':'synthetic-pinned-retry','type':'retry','target':target,'precondition':{'state':'ready'},'route':{'route_id':'synthetic-route','provider':'codex','model':'synthetic','account':'synthetic'}}
  params=_ledger_command(retry)['params'];print('retry params',params);assert params['route']=='synthetic-route'
  # Execute real retry on ready; suppress only availability and process start.
  with patch.object(pins,'available',return_value=(object(),)),patch.object(ops,'resume',return_value='synthetic-no-start'):
   result=runtime.submit_command(retry)
  print('retry relay',result,'persisted pin',pins.get(rdir,'T1'));assert result['status']=='OK' and pins.get(rdir,'T1')['route']=='synthetic-route'
  challenge=commands.Ledger().issue_challenge('demo/REQ-001','REQ-001')
  current=commands.target_state('demo/REQ-001','edit-brief',{'task':'T1'})
  edit={'schemaVersion':1,'idempotencyKey':'synthetic-edit-command','type':'edit-brief','target':target,'precondition':{'state':current['state']},'task':'T1','field':'objective','value':'New objective','confirmation':{'challengeId':challenge['challengeId'],'typedReq':'REQ-001'}}
  params=_ledger_command(edit)['params'];print('edit params',params)
  assert params['field']=='objective' and params['value']=='New objective'
  print('Edit adapter preserves field/value; current E checks actual successful frozen revisions and refused drift.')
 finally:
  server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY_AUDIT
```

### Probe G — structured cursor reset and preserved failure status

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
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
 assert runtime.event_cursor==''
 class FakeLaptop:
  def post_json(self,*args):return (500, {'status':'FAILED','code':'ROUTE_UNAVAILABLE','outcome':{'error':'synthetic route unavailable'}})
 runtime.laptop=FakeLaptop()
 store=SessionStore(str(pathlib.Path(tmp)/'auth.db'),'synthetic-session-secret-32-characters')
 token=store.create_session('dav033')
 service=OAuthService(OAuthConfig('synthetic','synthetic','synthetic-session-secret-32-characters','https://frontend.test',store.database_path),store)
 gateway=ThreadingHTTPServer(('127.0.0.1',0),make_handler(service, runtime=runtime))
 gt=threading.Thread(target=gateway.serve_forever,daemon=True);gt.start()
 try:
  conn=http.client.HTTPConnection('127.0.0.1',gateway.server_port,timeout=3)
  command={'schemaVersion':1,'idempotencyKey':'synthetic-failed-retry','type':'retry','target':{'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'},'precondition':{'state':'ready'}}
  conn.request('POST','/api/remote/v1/commands',json.dumps(command),{'Cookie':'flow_session='+token,'Origin':'https://frontend.test','X-Flow-Request':'1','Content-Type':'application/json'})
  response=conn.getresponse();payload=json.loads(response.read());print('failed effect public response',response.status,payload)
  assert response.status==500 and payload['status']=='FAILED'
  conn.close()
 finally:
  gateway.shutdown();gateway.server_close();gt.join();laptop.shutdown();laptop.server_close();lt.join();runtime.outbox._db.close()
PY_AUDIT
```

### Probe H — false retry-exhaustion notification

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,sys
sys.path[:0]=[str(pathlib.Path('skill/scripts').resolve()),str(pathlib.Path('remote/gateway').resolve())]
import bt_remote_events as feed
from notifications import notification_for_event
stamp='2026-10-20T00:00:00Z'
state={'runs':[{'project':'demo','req_id':'REQ-001','max_attempts':3,'tasks':[{'id':'T1','attempts_used':1,'max_attempts':3,'attempt':{'id':'a1','state':'failed','ended_at':stamp,'failure':'synthetic retryable failure'}}]}]}
events=feed.build_events(state);messages=[notification_for_event(e) for e in events]
print('one failure / budget 3 ->',[(e['type'],m[1]) for e,m in zip(events,messages) if m])
assert not any(messages)
state['runs'][0]['tasks'][0].update(attempts_used=3,retries_remaining=0)
messages=[notification_for_event(e) for e in feed.build_events(state)]
assert len(messages)==1 and messages[0]
print('exhausted budget -> exactly one alert')
PY_AUDIT
```

### Probe I — uncertain outcome classification

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
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
  print('connection refused',result);assert result['code']=='LAPTOP_UNAVAILABLE'
 finally:
  server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY_AUDIT
```

### Probe P — actual installed distributions

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib, subprocess, sys, zipfile, tarfile
root=pathlib.Path.cwd();sys.path.insert(0,str(root/'tests/migration'))
import installed_wheel
installed=installed_wheel.get()
with zipfile.ZipFile(installed.wheel) as archive:
 names=set(archive.namelist())
 assert 'bt_remote_edit.py' in names and 'bt_route_pins.py' in names
 print('wheel contains bt_remote_edit.py and bt_route_pins.py')
with tarfile.open(installed.sdist) as archive:
 names={pathlib.Path(p.name).name for p in archive.getmembers()}
 assert 'bt_remote_edit.py' in names and 'bt_route_pins.py' in names
 print('sdist contains both recovery implementation modules')
for name in ['bt_remote_api','bt_remote_commands','bt_remote_edit','bt_route_pins']:
 result=subprocess.run([str(installed.python),'-I','-c',
  f'import sys;sys.path.insert(0,sys.argv[1]);__import__("{name}")',str(installed.site)],
  cwd=installed.work,capture_output=True,text=True)
 print('isolated import',name,'exit',result.returncode)
 assert result.returncode == 0
PY_AUDIT
```

### Probe E — phone dialect, approved-base drift and failed-edit rollback over real keyed HTTP

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,os,sys,tempfile,json,threading
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway')]
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp;os.environ['FLOW_GATEWAY_KEY']='synthetic-audit-key'
 import bt_core,bt_remote_api as api,bt_remote_commands as commands,bt_scheduler_adapter as scheduler,bt_scheduler_ops as ops,bt_scheduler_run
 from bt_planner import contract,revisions,sync
 from bt_planner.tests.support import PLAN_MD,classify
 from app import GatewayRuntime
 from config import GatewayConfig
 base=pathlib.Path(tmp);rdir=base/'demo/requirements/REQ-001-demo';rdir.mkdir(parents=True)
 (rdir/'SPEC.md').write_text('# Spec\n## Requirements\n- R1. Demo\n')
 plan_md=PLAN_MD.replace('REQ-042','REQ-001')
 (rdir/'PLAN.md').write_text(plan_md.format(status='approved'))
 doc=classify(sync.skeleton(rdir,plan_id='REQ-001'));path=rdir/'PLAN.json';path.write_text(contract.dumps(doc))
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def send(self,body,status=200,content_type='application/json'):
   raw=body.encode();self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def do_POST(self):api.route_post(self)
  def do_GET(self):api.route_get(self)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
 runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{server.server_port}','synthetic-audit-key','synthetic','synthetic',base/'gateway.db'),sender=lambda _:None)
 def send(number,field,value):
  challenge=commands.Ledger().issue_challenge('demo/REQ-001','REQ-001')
  state=commands.target_state('demo/REQ-001','edit-brief',{'task':'T1'})
  result=runtime.submit_command({'schemaVersion':1,'idempotencyKey':f'synthetic-edit-{number}','type':'edit-brief','target':{'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'},'precondition':{'state':state['state'],'revision':state['revision']},'field':field,'value':value,'confirmation':{'challengeId':challenge['challengeId'],'typedReq':'REQ-001'}})
  print('edit',number,result);return result
 try:
  with patch.object(bt_core,'ROOT',base),patch('bt_lock._lock_dir',return_value=base/'.state/locks'),patch.object(ops,'stop_owner',return_value=0),patch.object(ops,'resume',return_value='synthetic-no-start'):
   sync.approve_freeze(rdir,'REQ-001',('approved',));run=scheduler.open_scheduler(rdir);run.step();scheduler.write_projection(rdir,run);bt_scheduler_run._runtime_binding(rdir,resume=False)
   result=send(1,'objective','Owner edits only T1')
   assert result['status']=='OK' and revisions.latest(rdir)['revision']==2 and ops.bound_plan(rdir).revision==2
   assert revisions.load_revision(rdir,2)['tasks'][0]['objective']=='Owner edits only T1'
   for n,field in enumerate(('criteria','acceptance_criteria'),2):
    result=send(n,field,['Owner edits T1 criteria'])
    assert result['status']=='OK' and revisions.latest(rdir)['revision']==n+1 and ops.bound_plan(rdir).revision==n+1
    assert revisions.load_revision(rdir,n+1)['tasks'][0]['acceptance_criteria']==['Owner edits T1 criteria']
   print('E phone objective/criteria edits freeze and rebase real run to r4')
   def legacy(key,brief):
    challenge=commands.Ledger().issue_challenge('demo/REQ-001','REQ-001')
    state=commands.target_state('demo/REQ-001','edit-brief',{'task':'T1'})
    return runtime.submit_command({'schemaVersion':1,'idempotencyKey':key,'type':'edit-brief','target':{'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'},'precondition':{'state':state['state'],'revision':state['revision']},'brief':brief,'confirmation':{'challengeId':challenge['challengeId'],'typedReq':'REQ-001'}})
   original=path.read_bytes();working=json.loads(original);working['tasks'][1]['objective']='UNAPPROVED unrelated T2 change';path.write_text(contract.dumps(working));before=path.read_bytes()
   result=legacy('synthetic-drift-key','Owner edits only T1')
   assert result['status']=='FAILED' and 'PLAN_DRIFT' in str(result) and path.read_bytes()==before and revisions.latest(rdir)['revision']==4
   assert revisions.load_revision(rdir,4)['tasks'][1]['objective']!='UNAPPROVED unrelated T2 change'
   path.write_bytes(original)
   (rdir/'PLAN.md').write_text(plan_md.format(status='review'));before=path.read_bytes()
   result=legacy('synthetic-refused-key','Edit must roll back')
   assert result['status']=='FAILED' and path.read_bytes()==before and revisions.latest(rdir)['revision']==4
   (rdir/'PLAN.md').write_text(plan_md.format(status='approved'))
   import bt_plan_adapter
   with patch.object(bt_plan_adapter,'publishable_problem',return_value='synthetic-publication-refusal'):
    result=legacy('synthetic-publication-failure','Must restore original bytes')
   assert result['status']=='FAILED' and path.read_bytes()==before and revisions.latest(rdir)['revision']==4
   print('E unrelated drift and review-state edits refused without publication; publication failure restores exact bytes; latest/bound stay r4')
 finally:server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY_AUDIT
```

### Probe N — restored Telegram expiry, backoff and timestamped history

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,sys,tempfile
sys.path.insert(0,str(pathlib.Path('remote/gateway').resolve()))
from notifications import NotificationOutbox
with tempfile.TemporaryDirectory() as tmp:
 out=NotificationOutbox(str(pathlib.Path(tmp)/'out.db'))
 out.enqueue('old','synthetic old message',created_at=100)
 sent=[];assert out.deliver_due(sent.append,now=7300)==0 and not sent
 out.enqueue('retry','synthetic delivery failure',created_at=100)
 def fail(_):raise RuntimeError('synthetic')
 out.deliver_due(fail,now=100)
 row=out._db.execute("SELECT status,attempts,next_attempt FROM telegram_outbox WHERE dedupe_key='retry'").fetchone()
 assert row==('pending',1,105.0)
 out.deliver_due(fail,now=7300)
 row=out._db.execute("SELECT status,attempts FROM telegram_outbox WHERE dedupe_key='retry'").fetchone()
 assert row==('dropped',1)
 history=out.history();print('history',history)
 assert [r['outcome'] for r in history]==['dropped','retry','dropped'] and all('at' in r for r in history)
 out._db.close()
PY_AUDIT
```

### Probe Q — actual quota projection into the exact phone parser

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,sys,os,json,tempfile,subprocess
from unittest.mock import patch
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway')]
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp
 import bt_remote_api as api
 class H:
  path='/api/remote/v1/quotas';headers={'Authorization':'Bearer synthetic-key'}
  def send(self,b,status,content_type):self.body=json.loads(b);self.status=status
 h=H()
 with patch.dict(os.environ,{'FLOW_GATEWAY_KEY':'synthetic-key'}),patch('bt_quota_live.read_all_live',return_value=[{'profile':'synthetic','provider':'codex','status':'available','observed_at':1000,'windows':{'five_hour':{'used_percent':25,'resets_at':2000}}}]):api.route_get(h)
 print('actual quota projection',h.status,h.body)
 js="""const fs=require('fs'),vm=require('vm'),ts=require('./remote/web/node_modules/typescript');const s=fs.readFileSync('remote/web/src/app/recovery-panels.tsx','utf8');const helpers=s.slice(s.indexOf('function record'),s.indexOf('export function RoutesPanel'));const a=s.indexOf('const parsed = body.accounts.flatMap');const b=s.indexOf('if (active)',a);const code=helpers+s.slice(a,b)+';parsed';const sandbox={body:JSON.parse(fs.readFileSync(0,'utf8')),exports:{}};vm.createContext(sandbox);const parsed=vm.runInContext(ts.transpileModule(code,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,sandbox);console.log('PHONE QUOTAS parsed account count',parsed.length);if(parsed.length!==0)process.exit(1);"""
 r=subprocess.run(['node','-e',js],input=json.dumps(h.body),text=True,capture_output=True);print(r.stdout,r.stderr);assert r.returncode==0
PY_AUDIT
```

### Probe L — proxy-shared login bucket and rejected JSON crash hypothesis

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import http.client,pathlib,sys,tempfile,threading
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(pathlib.Path('remote/gateway').resolve()))
from auth import OAuthConfig,OAuthService,SessionStore
from server import make_handler
class Runtime:
 def submit_command(self,value):return {'status':'OK'}
class Server(ThreadingHTTPServer):
 errors=[]
 def handle_error(self,*args):self.errors.append(sys.exc_info()[0].__name__)
with tempfile.TemporaryDirectory() as tmp:
 db=str(pathlib.Path(tmp)/'auth.db');secret='synthetic-session-secret-more-than-32'
 store=SessionStore(db,secret);token=store.create_session('dav033')
 service=OAuthService(OAuthConfig('synthetic','synthetic',secret,'https://frontend.test',db),store)
 server=Server(('127.0.0.1',0),make_handler(service, runtime=Runtime()));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  statuses=[]
  for number in range(6):
   conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=2)
   conn.request('GET','/api/auth/login',headers={'X-Forwarded-For':f'192.0.2.{number+1}'});res=conn.getresponse();statuses.append(res.status);res.read();conn.close()
  print('distinct forwarded clients same proxy login statuses',statuses);assert statuses==[302]*5+[429]
  conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=2)
  conn.request('POST','/api/remote/v1/commands',body='['*1200+'0'+']'*1200,headers={'Cookie':'flow_session='+token,'Origin':'https://frontend.test','X-Flow-Request':'1','Content-Type':'application/json'})
  res=conn.getresponse();body=res.read();print('nested JSON response',res.status,body.decode(),'handler errors',server.errors)
  assert res.status==200 and not server.errors;conn.close()
 finally:server.shutdown();server.server_close();thread.join()
PY_AUDIT
```

### Probe J — first-install ordering without touching system services

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,subprocess,tempfile,os
root=pathlib.Path.cwd()
with tempfile.TemporaryDirectory(dir=root/'remote',prefix='.audit-deploy-') as tmp:
 d=pathlib.Path(tmp);binpath=d/'bin';binpath.mkdir();state=d/'gateway';env_file=d/'synthetic.env'
 env_file.write_text(''.join(key+'=synthetic\n' for key in ['LAPTOP_ORIGIN','FLOW_GATEWAY_KEY','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID','GATEWAY_DATABASE','GITHUB_CLIENT_ID','GITHUB_CLIENT_SECRET','SESSION_SECRET','FLOW_FRONTEND_ORIGIN']))
 env_file.chmod(0o600)
 (binpath/'systemctl').write_text('#!/bin/sh\nprintf "synthetic first-install missing unit\\n" >&2\nexit 5\n');(binpath/'systemctl').chmod(0o755)
 env={**os.environ,'PATH':str(binpath)+':/usr/bin:/bin','GATEWAY_ROOT':str(state),'GATEWAY_ENV_FILE':str(env_file)}
 r=subprocess.run(['bash','remote/deploy/deploy.sh','remote/gateway'],env=env,capture_output=True,text=True)
 print('fresh install with missing-unit systemctl EXIT',r.returncode,'current switched',(state/'current').is_symlink(),r.stderr.strip());assert r.returncode==5 and (state/'current').is_symlink()
 r=subprocess.run(['bash','remote/deploy/deploy.sh','remote/gateway','--dry-run'],env=env,capture_output=True,text=True);print('deploy --dry-run EXIT',r.returncode);assert r.returncode==0
 r=subprocess.run(['bash','remote/deploy/rollback.sh','--dry-run'],env=env,capture_output=True,text=True);print('rollback without previous EXIT',r.returncode);assert r.returncode==2
PY_AUDIT
```

### Probe V — malformed authenticated native command

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,sys,tempfile,threading,http.client,json,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
sys.path.insert(0,str(pathlib.Path('skill/scripts').resolve()))
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp;os.environ['FLOW_GATEWAY_KEY']='synthetic-audit-key'
 import bt_remote_api as api
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def send(self,body,status,content_type):
   raw=body.encode();self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def do_POST(self):api.route_post(self)
 class Server(ThreadingHTTPServer):
  errors=[]
  def handle_error(self,*args):self.errors.append(sys.exc_info()[0].__name__)
 server=Server(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
 try:
  for authorized in (False,True):
   c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=2)
   headers={'Content-Type':'application/json'}
   if authorized:headers['Authorization']='Bearer synthetic-audit-key'
   c.request('POST','/api/remote/v1/commands',json.dumps({'idempotency_key':'synthetic-valid-key','command':'pause'}),headers)
   try:
    r=c.getresponse();print('authorized',authorized,'HTTP',r.status,r.read().decode());assert not authorized and r.status==401
   except http.client.RemoteDisconnected:
    print('authorized',authorized,'connection dropped',server.errors);assert authorized and server.errors==['KeyError']
   finally:c.close()
 finally:server.shutdown();server.server_close();worker.join()
PY_AUDIT
```

### Probes W/Y/Z/O — fresh provider interoperability, delivery, liveness and config

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import json,os,pathlib,sys,tempfile
from unittest.mock import patch
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'remote/gateway'),str(root/'skill/scripts')]
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp
 import bt_remote_api as api,bt_live_api as live,bt_core
 from app import GatewayRuntime
 from config import GatewayConfig
 from auth import OAuthConfig
 from server import create_server
 from telegram_bot import TelegramBot
 from upstream import UpstreamError
 class H:
  def send(self,body,status,content_type):self.body=json.loads(body);self.status=status
 h=H()
 rows=[{'run':'demo/REQ-001','project':'demo','req_id':'REQ-001','title':'Synthetic','status':'running','active':True,'tasks':[]}]
 with patch.object(live,'run_summaries',return_value=rows),patch.object(live,'now_frame_data',return_value={'items':[]}):api._snapshot(h)
 sent=[]
 class SnapshotLaptop:
  def snapshot(self):return h.body
 class Runtime:
  laptop=SnapshotLaptop()
 bot=TelegramBot(Runtime(),'synthetic','synthetic',api_call=lambda method,payload:sent.append((method,payload)) or {'ok':True})
 bot._send_status('synthetic')
 print('W real projection req keys',sorted(h.body['runs'][0]),'bot message',sent)
 assert sent==[('sendMessage',{'chat_id':'synthetic','text':'Ejecuciones activas:'})]

 class Laptop:
  def __init__(self):self.probes=0
  def health(self):self.probes+=1;return {'status':'ok'}
  def snapshot(self):return {'runs':[]}
  def events(self,*args):return {'events':[],'nextCursor':''}
 clock=[0.0];laptop=Laptop()
 cfg=GatewayConfig('http://127.0.0.1:1','synthetic','synthetic','synthetic',pathlib.Path(tmp)/'slow.db')
 def slow_sender(_):clock[0]+=cfg.request_timeout
 runtime=GatewayRuntime(cfg,laptop=laptop,sender=slow_sender)
 for n in range(20):runtime.outbox.enqueue(str(n),'synthetic')
 with patch('app.time.monotonic',side_effect=lambda:clock[0]),patch('notifications.time.time',side_effect=lambda:clock[0]):runtime.poll_once()
 print('Y simulated slow delivery elapsed',clock[0],'health probes',laptop.probes,'next 5-second probe overdue')
 assert clock[0]==100 and laptop.probes==1
 runtime.outbox._db.close()

 class Offline:
  def health(self):raise UpstreamError('synthetic unavailable')
  def post_json(self,*args):raise UpstreamError('synthetic invalid response')
 for action in ('command','challenge'):
  sent=[];runtime=GatewayRuntime(GatewayConfig('http://127.0.0.1:1','synthetic','synthetic','synthetic',pathlib.Path(tmp)/(action+'.db')),laptop=Offline(),sender=sent.append)
  runtime.has_cached_active_run=True
  with patch('app.time.monotonic',return_value=100):
   for _ in range(3):
    if action=='command':runtime._submit_ledger_command({'idempotency_key':'synthetic-key'})
    else:runtime.issue_challenge({'target':'demo/REQ-001','typedReq':'REQ-001'})
  with patch('app.time.monotonic',return_value=100+901):runtime.poll_once()
  rows=runtime.outbox._db.execute('SELECT COUNT(*) FROM telegram_outbox').fetchone()[0]
  print('Z third failure by',action,'status',runtime.liveness.status.value,'generation',runtime.offline_generation,'after 901 seconds outbox',rows,'sent',sent)
  assert runtime.liveness.status.value==('offline' if action=='command' else 'online') and runtime.offline_generation==0 and rows==0
  runtime.outbox._db.close()

 values={'LAPTOP_ORIGIN':'http://127.0.0.1:1','FLOW_GATEWAY_KEY':'synthetic','TELEGRAM_BOT_TOKEN':'synthetic','TELEGRAM_CHAT_ID':'synthetic','GATEWAY_DATABASE':str(pathlib.Path(tmp)/'config.db'),'GITHUB_CLIENT_ID':'synthetic','GITHUB_CLIENT_SECRET':'synthetic','SESSION_SECRET':'synthetic-session-secret-at-least-32','FLOW_FRONTEND_ORIGIN':'https://frontend.test','GATEWAY_BIND':''}
 cfg=GatewayConfig.from_env(values);oauth=OAuthConfig.from_env(values)
 with patch('server.ThreadingHTTPServer') as factory:
  create_server(oauth,(cfg.bind_host,cfg.bind_port),runtime=None)
  address=factory.call_args.args[0]
 print('O accepted empty bind passed to HTTP server',repr(address),'default command timeout',cfg.request_timeout)
 assert address==('',8790) and cfg.request_timeout==5
 print('No wildcard listener was opened; constructor mocked.')
PY_AUDIT
```

### Probes R/S/T/U/X — late events, redaction, restart semantics, notification predicates and malformed OAuth

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import copy,datetime as dt,os,pathlib,sys,tempfile,http.client,threading
from unittest.mock import patch
from http.server import ThreadingHTTPServer
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway')]
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp
 import bt_remote_events as feed
 from app import GatewayRuntime
 from config import GatewayConfig
 from upstream import UpstreamError
 from auth import OAuthConfig,OAuthService,SessionStore
 from server import make_handler
 stamp='2026-10-20T00:00:00Z';epoch=dt.datetime.fromisoformat(stamp).timestamp()
 state={'runs':[{'project':'demo','req_id':'REQ-001','tasks':[{'id':'T1','attempt':{'id':'a1','live':True,'last_activity_at':stamp}}]},
                {'project':'demo','req_id':'REQ-002','status':'done','updated_at':'2026-10-20T00:10:00Z'}]}
 class FeedLaptop:
  now=epoch+660
  def events(self,after):return feed.page(feed._observe(pathlib.Path(tmp)/'late-feed',feed.build_events(state,now=self.now)),after)
 laptop=FeedLaptop()
 cfg=GatewayConfig('http://127.0.0.1:1','synthetic','synthetic','synthetic',pathlib.Path(tmp)/'late.db')
 runtime=GatewayRuntime(cfg,laptop=laptop,sender=lambda _:None)
 runtime._poll_events();cursor=runtime.event_cursor;laptop.now=epoch+901
 derived=feed.build_events(state,now=laptop.now);late=next(e for e in derived if e['type']=='attempt.stalled')
 for _ in range(3):runtime._poll_events()
 keys=[r[0] for r in runtime.outbox._db.execute('SELECT dedupe_key FROM telegram_outbox')]
 print('R late stall derived',late['occurredAt'],'cursor',cursor,'outbox',keys)
 assert 'event:'+late['dedupeKey'] in keys and runtime.event_cursor!=cursor
 state['rounds']=[{'project':'demo','req':'REQ-001','round':1,'at':stamp}]
 runtime._poll_events();assert any(e['type']=='round.waiting' for e in laptop.events(cursor)['events'])
 print('R late stall and round delivered across persisted observation cursor');runtime.outbox._db.close()

 text='{"password": "synthetic-password", "refresh_token": "synthetic-refresh"} DATABASE_URL=postgres://synthetic:synthetic-db-password@db.local/demo'
 sanitized=feed.redact(text);print('S quoted/log string redaction',sanitized)
 assert 'synthetic-password' in sanitized and 'synthetic-refresh' in sanitized and 'synthetic-db-password' in sanitized
 structured=feed.redact({'password':'synthetic-password'});assert structured['password']=='[REDACTED]'
 print('S structured dict is redacted; JSON serialized inside log text is not')
 import subprocess
 check=subprocess.run(['node','--input-type=module','-e',
  "import {redactReviewText} from './remote/web/src/app/review/review-text.mjs';let t=process.argv[1];console.log(redactReviewText(t));if(!redactReviewText(t).includes('synthetic-password'))process.exit(2)",text],capture_output=True,text=True,check=True)
 print('S phone review sanitizer also leaves synthetic password')

 class Historical:
  seen=[]
  def events(self,after):
   self.seen.append(after)
   return feed.page(feed.build_events({'runs':[{'project':'demo','req_id':'REQ-009','status':'done','updated_at':(dt.datetime.now(dt.timezone.utc)-dt.timedelta(minutes=30)).isoformat()}]}),after)
 history=Historical();sent=[]
 cfg=GatewayConfig('http://127.0.0.1:1','synthetic','synthetic','synthetic',pathlib.Path(tmp)/'history.db')
 first=GatewayRuntime(cfg,laptop=history,sender=sent.append);first._poll_events();first.outbox.deliver_due(first.sender)
 assert history.seen==[''] and len(sent)==1
 print('T fresh runtime sends historical run.finished instead of starting from now')
 first.outbox._db.close()
 class Offline:
  def health(self):raise UpstreamError('synthetic offline')
 cfg=GatewayConfig('http://127.0.0.1:1','synthetic','synthetic','synthetic',pathlib.Path(tmp)/'restart.db')
 sent=[]
 for started in (0,1000):
  with patch('app.time.monotonic',return_value=started),patch('app.time.time',return_value=10000+started):
   runtime=GatewayRuntime(cfg,laptop=Offline(),sender=sent.append)
   runtime.has_cached_active_run=True;runtime.outbox.set_state_value('laptop_has_cached_active_run',1)
   for _ in range(3):runtime.poll_once()
  with patch('app.time.monotonic',return_value=started+901),patch('app.time.time',return_value=10000+started+901):runtime.poll_once()
  print('T offline generation after same-outage restart',runtime.offline_generation,'sent total',len(sent))
  assert runtime.offline_generation==1
  runtime.outbox._db.close()
 assert len(sent)==1

 events=feed.build_events({'quotas':[{'profile':'exhausted','exhausted_until':'later','observed_at':stamp},{'profile':'available','exhausted_until':None,'observed_at':stamp}]})
 from notifications import notification_for_event,NotificationOutbox
 messages=[notification_for_event(e) for e in events]
 print('U one exhausted plus one available produces',messages);assert len(messages)==1 and messages[0]
 flow={'flow':[{'id':'flow-1','kind':'state_change','run':'demo/REQ-001','task':'T1','at':stamp,'data':{'state':'failed','attempt':'a1','attempts_used':3,'max_attempts':3,'retries_remaining':0}}]}
 first_events=feed._observe(pathlib.Path(tmp)/'dedupe',feed.build_events(flow));assert len(first_events)==1
 last=first_events[0]['cursor']
 later=copy.deepcopy(flow);later['runs']=[{'project':'demo','req_id':'REQ-001','tasks':[{'id':'T1','attempts_used':3,'max_attempts':3,'retries_remaining':0,'attempt':{'id':'a1','state':'failed','ended_at':'2026-10-20T00:00:01Z'}}]}]
 second_events=feed.page(feed._observe(pathlib.Path(tmp)/'dedupe',feed.build_events(later)),last)['events'];assert len(second_events)==1
 outbox=NotificationOutbox(str(pathlib.Path(tmp)/'duplicate.db'))
 for e in first_events+second_events:outbox.enqueue(*notification_for_event(e))
 count=outbox._db.execute('SELECT COUNT(*) FROM telegram_outbox').fetchone()[0]
 print('U same T1/a1 failure flow then state enqueues rows',count)
 assert count==2;outbox._db.close()

 class Server(ThreadingHTTPServer):
  errors=[]
  def handle_error(self,*args):self.errors.append(sys.exc_info()[0].__name__)
 db=str(pathlib.Path(tmp)/'auth.db');secret='synthetic-session-secret-at-least-32'
 store=SessionStore(db,secret);service=OAuthService(OAuthConfig('synthetic','synthetic',secret,'https://frontend.test',db),store)
 server=Server(('127.0.0.1',0),make_handler(service));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
  conn.request('GET','/api/auth/callback?code=synthetic&state=%C3%A9',headers={'Cookie':'flow_oauth_state="é"'})
  try:response=conn.getresponse();response.read()
  except http.client.RemoteDisconnected:pass
  else:raise AssertionError('expected malformed state handler disconnect')
  conn.close();print('X unicode OAuth state handler errors',server.errors);assert server.errors==['TypeError']
 finally:server.shutdown();server.server_close();thread.join()
PY_AUDIT
```

### Probe I2 — truncated upstream success

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import http.client,pathlib,sys,tempfile,threading,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
root=pathlib.Path.cwd();sys.path.insert(0,str(root/'remote/gateway'))
from app import GatewayRuntime
from config import GatewayConfig
class Truncated(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  self.rfile.read(int(self.headers.get('Content-Length','0')))
  self.send_response(200);self.send_header('Content-Length','100');self.end_headers()
  self.wfile.write(b'{}')
with tempfile.TemporaryDirectory() as tmp:
 server=ThreadingHTTPServer(('127.0.0.1',0),Truncated)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{server.server_port}','synthetic','synthetic','synthetic',pathlib.Path(tmp)/'db'),sender=lambda _:None)
 try:
  command={'schemaVersion':1,'idempotencyKey':'synthetic-truncated-key','type':'pause','target':{'kind':'run','project':'demo','req':'REQ-001'},'precondition':{'state':'running'}}
  try:runtime.submit_command(command)
  except http.client.IncompleteRead as exc:print('I2 truncated accepted response escapes runtime:',type(exc).__name__,str(exc))
  else:raise AssertionError('expected uncaught IncompleteRead')
 finally:server.shutdown();server.server_close();thread.join();runtime.outbox._db.close()
PY_AUDIT
```

### Probes AA/AB/AC/AD/AE/AF — fresh provider findings, independently reproduced

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import os,sys,pathlib,tempfile,json,hashlib,datetime as dt
from unittest.mock import patch
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway'),str(root/'skill/scripts/bt_scheduler_core/tests')]
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp
 import bt_core,bt_remote_api as api,bt_scheduler_adapter as scheduler,bt_scheduler_core as core,bt_remote_events as feed,bt_live_api as live
 from support import Harness,indep
 from notifications import notification_for_event,NotificationOutbox
 from app import GatewayRuntime
 from config import GatewayConfig
 base=pathlib.Path(tmp);(base/'.state/scheduler').mkdir(parents=True)
 with patch.object(bt_core,'ROOT',base):
  for req in ('REQ-001','REQ-002'):
   rd=base/'demo/requirements'/f'{req}-audit';rd.mkdir(parents=True)
   (rd/'PLAN.md').write_text('---\nstatus: approved\n---\n# Plan\n')
   h=Harness([indep('T1')],repository=core.SqliteRepository(scheduler.run_db_path(rd)),plan_id=req)
   (rd/'PLAN.json').write_text(h.text);rev=rd/'plan-revisions';rev.mkdir();(rev/'PLAN.r1.json').write_text(h.text)
   (rev/'MANIFEST.json').write_text(json.dumps({'schema':1,'revisions':[{'revision':1,'sha256':hashlib.sha256(h.text.encode()).hexdigest(),'frozen_at':'2026-10-21T00:00:00Z'}]}))
   h.core.step();h.send('T1','execution_failed',reason=req+' distinct failure');h.core.step();scheduler.write_projection(rd,h.core)
  rows=live.run_summaries(base,'global');ids=[run['tasks'][0]['attempt']['id'] for run in rows]
  print('AA actual per-run attempt IDs',ids);assert len(ids)==2 and ids[0]==ids[1]
  for row in rows:
   review=api._failure_review('demo/'+row['req_id'],ids[0]);print('AA scoped review',row['req_id'],review['cause'])
   assert row['req_id'] in str(review['cause'])
 events=feed.build_events({'runs':[{'project':'demo','req_id':req,'tasks':[{'id':'T1','attempt':{'id':ids[0],'state':'blocked'}}]} for req in ('REQ-001','REQ-002')]})
 assert len(events)==2 and events[0]['dedupeKey']!=events[1]['dedupeKey']
 out=NotificationOutbox(':memory:')
 for e in events:out.enqueue(*notification_for_event(e))
 count=out._db.execute('SELECT COUNT(*) FROM telegram_outbox').fetchone()[0]
 print('AA two blocked runs outbox rows',count);assert count==2;out._db.close()
 state={'runs':[{'project':'demo','req_id':'REQ-003','tasks':[{'id':'T1','attempts_used':3,'max_attempts':3,'retries_remaining':0,'attempt':{'id':'a3','state':'failed'},'history':[{'id':'a1','state':'failed'},{'id':'a2','state':'failed'}]}]}]}
 ev=feed.build_events(state);print('AB task finally exhausted failure alerts',len(ev));assert len(ev)==1 and ev[0]['target']['attemptId']=='a3'
 import bt_plans_api,bt_rounds,time
 os.environ['TZ']='America/Bogota';time.tzset()
 rd=base/'demo/requirements/REQ-004-audit';rd.mkdir(parents=True)
 (rd/'PLAN.md').write_text('---\nstatus: approved\n---\n# Plan\n')
 (rd/'PLAN.json').write_text(h.text.replace('REQ-002','REQ-004'))
 old=time.time()-7200;os.utime(rd/'PLAN.md',(old,old))
 created=bt_rounds.new_round(rd,{'questions':[{'id':'q1','text':'Fresh question','type':'open'}]})
 plan=next(p for p in bt_plans_api.plans_payload(base) if p['req_id']=='REQ-004')
 print('AC actual fresh round created_at',json.loads(created.read_text())['created_at'],'old plan',plan['updated_at'])
 with patch.object(live,'flow_events',return_value=([],[],{})):
  events=feed.collect(base,[],[plan],[],[])

 class Laptop:
  def events(self,after):return feed.page(events,after)
 sent=[];rt=GatewayRuntime(GatewayConfig('http://127.0.0.1:1','synthetic','synthetic','synthetic',base/'late-round.db'),laptop=Laptop(),sender=sent.append)
 rt._poll_events();rt.outbox.deliver_due(rt.sender)
 print('AC fresh Bogota round normalized to UTC and delivered',[(e['type'],e['occurredAt']) for e in events],rt.outbox.history(),sent)
 assert events[0]['type']=='round.waiting' and len(sent)==1 and rt.outbox.history()[0]['outcome']=='sent';rt.outbox._db.close()
 import bt_remote_recovery as recovery,bt_route_pins as pins
 from types import SimpleNamespace
 row=SimpleNamespace(route_id='synthetic-route',provider='codex',model='synthetic',profile='synthetic',account_ref='synthetic',profile_authorized=True,source_status='available',runtime_status='available',auth_status='valid',quota_status='unknown')
 with patch.object(recovery,'task_candidates',return_value=(None,(row,))):options=recovery.route_options('demo',base,'T1')
 with patch.object(pins,'candidates_for',return_value=(row,)):selected=pins.available('demo',base,'T1',{'route':'synthetic-route'})
 print('AD unknown-quota route listed available',options[0]['available'],'retry candidates',selected)
 assert options[0]['available'] is True and selected==[]
 import bt_server
 with patch.object(bt_server,'platform',return_value='linux'),patch.object(bt_server.shutil,'which',return_value='systemctl'),patch.object(bt_server.subprocess,'run',side_effect=FileNotFoundError('synthetic missing systemctl')),patch.object(bt_server,'is_running',return_value=False),patch.object(bt_server.subprocess,'Popen') as popen:
  try:bt_server.ensure_server()
  except FileNotFoundError:print('AE discovered-but-failing systemctl raises FileNotFoundError, detached starts',popen.call_count)
  else:raise AssertionError('expected missing systemctl failure')
 # At the production five-second poll cadence, thirteen polls cover t=0 through t=60.
 stamp=dt.datetime.now(dt.timezone.utc).isoformat()
 commands=[{'idempotency_key':str(n),'target':'demo/REQ-005','outcome':'OK','created_at':'2026-10-20T00:00:00Z'} for n in range(3000)]
 pending=feed._observe(base/'backlog',feed.build_events({'commands':commands,'rounds':[{'project':'demo','req':'REQ-005','round':1,'at':stamp}]}))
 class BacklogLaptop:
  def events(self,after):return feed.page(pending,after)
 rt=GatewayRuntime(GatewayConfig('http://127.0.0.1:1','synthetic','synthetic','synthetic',base/'backlog.db'),laptop=BacklogLaptop(),sender=lambda _:None)
 for _ in range(13):rt._poll_events()
 count=rt.outbox._db.execute('SELECT COUNT(*) FROM telegram_outbox').fetchone()[0]
 assert count==0
 for _ in range(3):rt._poll_events()
 count=rt.outbox._db.execute('SELECT COUNT(*) FROM telegram_outbox').fetchone()[0]
 print('AF fresh round queued only at poll 16 (75 s at five-second cadence)',count);assert count==1
 rt.outbox._db.close()
PY_AUDIT
```

### Probe AG — production read routing and challenge issuance

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import os,sys,pathlib,tempfile,threading,http.client,json,subprocess
from http.server import ThreadingHTTPServer
from unittest.mock import patch
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway'),str(root/'remote/e2e/tests')]
with tempfile.TemporaryDirectory() as tmp:
 base=pathlib.Path(tmp);os.environ['BITACORA_ROOT']=tmp;os.environ['FLOW_GATEWAY_KEY']='synthetic-key-at-least-24-characters'
 from test_local_e2e import LocalEndToEndTests as Fixture
 Fixture.root=base;Fixture._seed_retry_event_fixture()
 import bt_server,bt_quota_live,bt_subscriptions
 from app import GatewayRuntime
 from auth import OAuthConfig,OAuthService,SessionStore
 from config import GatewayConfig
 from server import make_handler
 class QuietServer(ThreadingHTTPServer):
  daemon_threads=True
  def __init__(self,*args):super().__init__(*args);self.errors=[]
  def handle_error(self,*args):self.errors.append(sys.exc_info()[0].__name__)
 laptop=QuietServer(('127.0.0.1',0),bt_server.RemoteHandler);lt=threading.Thread(target=laptop.serve_forever,daemon=True);lt.start()
 runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{laptop.server_port}',os.environ['FLOW_GATEWAY_KEY'],'synthetic','synthetic',base/'runtime.db'),sender=lambda _:None)
 store=SessionStore(str(base/'auth.db'),'synthetic-session-secret-at-least-32')
 token=store.create_session('dav033');service=OAuthService(OAuthConfig('synthetic','synthetic','synthetic-session-secret-at-least-32','https://frontend.test',store.database_path),store)
 gateway=QuietServer(('127.0.0.1',0),make_handler(service,hub=runtime.hub,runtime=runtime));gt=threading.Thread(target=gateway.serve_forever,daemon=True);gt.start()
 def call(method,path,payload=None,native=False):
  port=laptop.server_port if native else gateway.server_port
  conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
  headers={'Authorization':'Bearer '+os.environ['FLOW_GATEWAY_KEY']} if native else {'Cookie':'flow_session='+token,'Origin':'https://frontend.test','X-Flow-Request':'1'}
  if payload is not None:headers['Content-Type']='application/json'
  conn.request(method,'/api/remote/v1/'+path,json.dumps(payload) if payload else None,headers);res=conn.getresponse();body=json.loads(res.read());conn.close();return res.status,body
 try:
  with patch.object(bt_subscriptions,'summary',return_value=[]):runtime.poll_once()
  status,body=call('GET','snapshot');print('AG production snapshot',status,'keys',sorted(body),'runs',len(body['runs']))
  assert status==200 and len(body['runs'])==1 and body['schemaVersion']==1
  js="""const fs=require('node:fs'),vm=require('node:vm'),ts=require('./remote/web/node_modules/typescript');const source=fs.readFileSync('remote/web/src/app/page.tsx','utf8');const code=source.slice(source.indexOf('type Target'),source.indexOf('function prettyTime'));const sandbox={input:JSON.parse(fs.readFileSync(0,'utf8')),exports:{}};vm.createContext(sandbox);const parsed=vm.runInContext(ts.transpileModule(code+';parseSnapshot(input)',{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,sandbox);if(parsed.runs.length!==1)process.exit(2);console.log('AG phone accepts real public snapshot')"""
  p=subprocess.run(['node','-e',js],input=json.dumps(body),text=True,capture_output=True);print(p.stdout.strip());assert p.returncode==0
  for path in ['commands','history','attempts/att-0003/review?target=demo%2FREQ-001','events']:
   with patch.object(bt_subscriptions,'summary',return_value=[]):status,body=call('GET',path)
   print('AG public read',path,status,sorted(body));assert status==(404 if path=='events' else 200)
  status,body=call('GET','attempts/att-0003/review');print('AG exact phone review missing target',status,body);assert status==400 and body['code']=='INVALID_TARGET'
  status,body=call('GET','events/stream');print('AG phone SSE route',status,body);assert status==404
  challenge={'target':'demo/REQ-001','typedReq':'REQ-001'}
  for native in [True,False]:
   status,body=call('POST','challenges',challenge,native);print('AG challenge native',native,status,body);assert status==201 and body['challengeId'] and body['target']=='demo/REQ-001'
  # Explicit stream path serves named frames and never rechecks the revoked session.
  conn=http.client.HTTPConnection('127.0.0.1',gateway.server_port,timeout=3);cursor=runtime.hub.live_cursor()
  conn.request('GET','/api/remote/v1/stream',headers={'Cookie':'flow_session='+token,'Last-Event-ID':cursor});res=conn.getresponse();assert res.status==200
  store.delete_session(token);runtime.hub.publish({'type':'synthetic.after.logout'})
  frame=[res.fp.readline().decode().strip() for _ in range(4)];print('AG existing SSE after session revocation',frame);assert 'synthetic.after.logout' in str(frame);conn.close()
  assert gateway.errors==[],gateway.errors
 finally:
  runtime.hub.close();gateway.shutdown();gateway.server_close();gt.join();laptop.shutdown();laptop.server_close();lt.join();runtime.outbox._db.close()
PY_AUDIT
```

### Probe AH — exhausted real producer versus the event predicate

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,sys,tempfile,os
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'remote/e2e/tests'),str(root/'skill/scripts')]
from test_local_e2e import LocalEndToEndTests as Fixture
with tempfile.TemporaryDirectory() as tmp:
 Fixture.root=pathlib.Path(tmp)/'bitacora';Fixture.root.mkdir();os.environ['BITACORA_ROOT']=str(Fixture.root)
 Fixture._seed_retry_event_fixture()
 import bt_live_api as live,bt_remote_events as feed
 runs=live.run_summaries(Fixture.root,'global');assert len(runs)==1
 task=runs[0]['tasks'][0];print('AH real exhausted task',task)
 assert task['attempts']==3 and len({a['id'] for a in task['history']})==3
 assert task['attempts_used']==task['max_attempts']==3 and task['retries_remaining']==0 and task['retry_exhausted']
 events=feed.build_events({'runs':runs});print('AH real exhausted feed',events)
 failures=[e for e in events if e['type']=='attempt.failed'];assert len(failures)==1 and failures[0]['target']['attemptId']=='att-0003'
PY_AUDIT
```

### Probe AE2 — absent systemctl versus uncertain ownership

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,sys,tempfile
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path('skill/scripts').resolve()))
with tempfile.TemporaryDirectory(dir='remote') as tmp:
 import os
 os.environ['BITACORA_ROOT']=tmp
 import bt_server
 with patch.object(bt_server,'platform',return_value='linux'),patch.object(bt_server.shutil,'which',return_value=None),patch.object(bt_server,'is_running',return_value=False),patch.object(bt_server.subprocess,'Popen') as spawn,patch.object(bt_server.subprocess,'run') as service:
  bt_server.ensure_server();assert spawn.call_count==1 and service.call_count==0
  print('AE absent systemctl: one detached startup, zero systemctl calls')
 with patch.object(bt_server,'platform',return_value='linux'),patch.object(bt_server.shutil,'which',return_value='systemctl'),patch.object(bt_server.subprocess,'run',side_effect=FileNotFoundError('synthetic race')),patch.object(bt_server,'is_running',return_value=False),patch.object(bt_server.subprocess,'Popen') as spawn:
  try:bt_server.ensure_server()
  except FileNotFoundError:pass
  else:raise AssertionError('enabled/uncertain ownership should fail closed')
  assert spawn.call_count==0;print('AE present-but-unavailable systemctl: no competing loose server')
PY_AUDIT
```

### Probe AI — new prerequisite aliases and relative failure-review path

```bash
python - <<'PY_AUDIT'
import pathlib, tempfile, atexit, shutil
scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(scratch.resolve());atexit.register(shutil.rmtree,scratch,ignore_errors=True)
import json,sys
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path('remote/gateway').resolve()))
from app import _ledger_command
from notifications import notification_for_event,TelegramSender
base={'schemaVersion':1,'idempotencyKey':'synthetic-alias-command','type':'answer-decision',
      'target':{'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'},
      'precondition':{'state':'blocked'},'option':'retry'}
for name in ('requestId','request_id'):
    result=_ledger_command({**base,name:'synthetic-decision'})
    assert result['params']['request_id']=='synthetic-decision'
    print('AI decision alias',name,'preserved')
event={'schemaVersion':1,'id':'synthetic-failure','dedupeKey':'synthetic-failure',
       'type':'attempt.failed','target':{'kind':'task','project':'demo','req':'REQ-001',
       'taskId':'T1','attemptId':'a1'},'data':{'failure':'synthetic cause'}}
key,message=notification_for_event(event)
assert key=='event:attempt.failed:demo/REQ-001:a1'
assert '/review?project=demo&req=REQ-001&taskId=T1#attempt-a1' in message
assert 'synthetic cause' not in message
captured=[]
class Response:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return b'{"ok":true}'
def send(request,**kwargs):
    captured.append(json.loads(request.data));return Response()
with patch('notifications.urlopen',side_effect=send):
    TelegramSender('synthetic','synthetic')(message)
assert set(captured[0])=={'chat_id','text'}
print('AI relative review path preserved; alert still has no absolute frontend URL, cause or reply_markup')
PY_AUDIT
```

### Probe AJ — raw immediate handler errors and correctly bounded public history

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(scratch.resolve());atexit.register(shutil.rmtree,scratch,ignore_errors=True)
import json,os,sys,threading
from unittest.mock import patch
from http.server import ThreadingHTTPServer
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway')]
with tempfile.TemporaryDirectory() as tmp:
    os.environ['BITACORA_ROOT']=tmp;os.environ['FLOW_GATEWAY_KEY']='synthetic-gateway-key'
    import bt_server,bt_remote_api as api,bt_remote_events as feed
    from app import GatewayRuntime
    from config import GatewayConfig
    secret_text='FLOW_GATEWAY_KEY=synthetic-error-value'
    def failing_handler(target,params):raise ValueError(secret_text)
    def state(*args):return {'state':'running'}
    server=ThreadingHTTPServer(('127.0.0.1',0),bt_server.RemoteHandler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    rt=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{server.server_port}',
        'synthetic-gateway-key','synthetic','synthetic',pathlib.Path(tmp)/'gateway.db'),sender=lambda _:None)
    try:
        command={'schemaVersion':1,'idempotencyKey':'synthetic-error-command','type':'resume',
                 'target':{'kind':'run','project':'demo','req':'REQ-001'},'precondition':{'state':'running'}}
        with patch.dict(api.HANDLERS,{'resume':failing_handler}),patch.object(api,'_target_state',state):
            result=rt.submit_command(command)
            history=rt.read_remote('/api/remote/v1/commands')
        assert result['status']=='FAILED' and result['outcome']['error']==secret_text
        assert 'synthetic-error-value' not in json.dumps(history)
        assert 'synthetic-error-value' not in feed.redact(secret_text)
        print('AJ real HTTP command result forwards injected handler exception verbatim')
        print('AJ real HTTP public history correctly withholds the injected exception value')
        print('AJ injection models a handler failure; no built-in secret-bearing exception or live leak established')
    finally:
        server.shutdown();server.server_close();worker.join();rt.outbox._db.close()
PY_AUDIT
```

### Probe AK — actual public failed-effect status and offline phone contract

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(scratch.resolve());atexit.register(shutil.rmtree,scratch,ignore_errors=True)
import json,os,sys,threading
from unittest.mock import patch
from http.server import ThreadingHTTPServer
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway')]
with tempfile.TemporaryDirectory() as tmp:
    os.environ['BITACORA_ROOT']=tmp;os.environ['FLOW_GATEWAY_KEY']='synthetic-gateway-key'
    import bt_server,bt_remote_api as api,bt_remote_events as feed
    from app import GatewayRuntime
    from config import GatewayConfig
    secret_text='FLOW_GATEWAY_KEY=synthetic-error-value'
    def failing_handler(target,params):raise ValueError(secret_text)
    def state(*args):return {'state':'running'}
    server=ThreadingHTTPServer(('127.0.0.1',0),bt_server.RemoteHandler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    rt=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{server.server_port}',
        'synthetic-gateway-key','synthetic','synthetic',pathlib.Path(tmp)/'gateway.db'),sender=lambda _:None)
    from auth import OAuthConfig,OAuthService,SessionStore
    from server import make_handler
    import http.client,subprocess
    store=SessionStore(str(pathlib.Path(tmp)/'auth.db'),'synthetic-session-secret-more-than-32')
    token=store.create_session('dav033')
    service=OAuthService(OAuthConfig('synthetic','synthetic','synthetic-session-secret-more-than-32','https://frontend.test',store.database_path),store)
    gateway=ThreadingHTTPServer(('127.0.0.1',0),make_handler(service,hub=rt.hub,runtime=rt))
    gt=threading.Thread(target=gateway.serve_forever,daemon=True);gt.start()
    try:
        command={'schemaVersion':1,'idempotencyKey':'synthetic-failure-public','type':'resume',
                 'target':{'kind':'run','project':'demo','req':'REQ-001'},'precondition':{'state':'running'}}
        conn=http.client.HTTPConnection('127.0.0.1',gateway.server_port,timeout=3)
        with patch.dict(api.HANDLERS,{'resume':failing_handler}),patch.object(api,'_target_state',state):
            conn.request('POST','/api/remote/v1/commands',json.dumps(command),{'Cookie':'flow_session='+token,'Origin':'https://frontend.test','X-Flow-Request':'1','Content-Type':'application/json'})
            response=conn.getresponse();body=json.loads(response.read());status=response.status;conn.close()
        print('AK actual native failing handler through public gateway',status,body['status'],body['code'])
        assert status==500 and body['status']=='FAILED' and body['code']=='EFFECT_FAILED'
        rt.hub.update_snapshot({'schemaVersion':1,'generatedAt':'2026-10-21T00:00:00Z','cursor':'','runs':[],'plans':[]})
        rt.hub.set_online(False)
        conn=http.client.HTTPConnection('127.0.0.1',gateway.server_port,timeout=3)
        conn.request('GET','/api/remote/v1/snapshot',headers={'Cookie':'flow_session='+token});response=conn.getresponse();body=json.loads(response.read());conn.close()
        print('AK offline public snapshot',response.status,'online',body.get('online'),'laptop',body.get('laptop'))
        assert response.status==200 and body['online'] is False and 'laptop' not in body
        js="""const fs=require('node:fs'),vm=require('node:vm'),ts=require('./remote/web/node_modules/typescript');const source=fs.readFileSync('remote/web/src/app/page.tsx','utf8');const code=source.slice(source.indexOf('type Target'),source.indexOf('function prettyTime'));const sandbox={input:JSON.parse(fs.readFileSync(0,'utf8')),exports:{}};vm.createContext(sandbox);const parsed=vm.runInContext(ts.transpileModule(code+';parseSnapshot(input)',{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,sandbox);if(parsed.laptop?.online===false)process.exit(2);console.log('AK exact phone parser ignores root online=false; page selects EN VIVO')"""
        check=subprocess.run(['node','-e',js],input=json.dumps(body),capture_output=True,text=True);print(check.stdout,check.stderr);assert check.returncode==0
    finally:
        rt.hub.close();gateway.shutdown();gateway.server_close();gt.join()
        server.shutdown();server.server_close();worker.join();rt.outbox._db.close()
PY_AUDIT
```

### Probe AL — post-publication rebase failure and subsequent edit refusal

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib,os,sys,tempfile,json,threading
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway')]
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp;os.environ['FLOW_GATEWAY_KEY']='synthetic-audit-key'
 import bt_core,bt_remote_api as api,bt_remote_commands as commands,bt_scheduler_adapter as scheduler,bt_scheduler_ops as ops,bt_scheduler_run
 from bt_planner import contract,revisions,sync
 from bt_planner.tests.support import PLAN_MD,classify
 from app import GatewayRuntime
 from config import GatewayConfig
 base=pathlib.Path(tmp);rdir=base/'demo/requirements/REQ-001-demo';rdir.mkdir(parents=True)
 (rdir/'SPEC.md').write_text('# Spec\n## Requirements\n- R1. Demo\n')
 plan_md=PLAN_MD.replace('REQ-042','REQ-001')
 (rdir/'PLAN.md').write_text(plan_md.format(status='approved'))
 doc=classify(sync.skeleton(rdir,plan_id='REQ-001'));path=rdir/'PLAN.json';path.write_text(contract.dumps(doc))
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def send(self,body,status=200,content_type='application/json'):
   raw=body.encode();self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def do_POST(self):api.route_post(self)
  def do_GET(self):api.route_get(self)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
 runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{server.server_port}','synthetic-audit-key','synthetic','synthetic',base/'gateway.db'),sender=lambda _:None)
 def send(number,field,value):
  challenge=commands.Ledger().issue_challenge('demo/REQ-001','REQ-001')
  state=commands.target_state('demo/REQ-001','edit-brief',{'task':'T1'})
  result=runtime.submit_command({'schemaVersion':1,'idempotencyKey':f'synthetic-edit-{number}','type':'edit-brief','target':{'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'},'precondition':{'state':state['state'],'revision':state['revision']},'field':field,'value':value,'confirmation':{'challengeId':challenge['challengeId'],'typedReq':'REQ-001'}})
  print('edit',number,result);return result
 try:
  with patch.object(bt_core,'ROOT',base),patch('bt_lock._lock_dir',return_value=base/'.state/locks'),patch.object(ops,'stop_owner',return_value=0),patch.object(ops,'resume',return_value='synthetic-no-start'):
   sync.approve_freeze(rdir,'REQ-001',('approved',));run=scheduler.open_scheduler(rdir);run.step();scheduler.write_projection(rdir,run);bt_scheduler_run._runtime_binding(rdir,resume=False)
   result=send(1,'objective','Owner edits only T1')
   assert result['status']=='OK' and revisions.latest(rdir)['revision']==2 and ops.bound_plan(rdir).revision==2
   assert revisions.load_revision(rdir,2)['tasks'][0]['objective']=='Owner edits only T1'
   for n,field in enumerate(('criteria','acceptance_criteria'),2):
    result=send(n,field,['Owner edits T1 criteria'])
    assert result['status']=='OK' and revisions.latest(rdir)['revision']==n+1 and ops.bound_plan(rdir).revision==n+1
    assert revisions.load_revision(rdir,n+1)['tasks'][0]['acceptance_criteria']==['Owner edits T1 criteria']
   print('E phone objective/criteria edits freeze and rebase real run to r4')
   def legacy(key,brief):
    challenge=commands.Ledger().issue_challenge('demo/REQ-001','REQ-001')
    state=commands.target_state('demo/REQ-001','edit-brief',{'task':'T1'})
    return runtime.submit_command({'schemaVersion':1,'idempotencyKey':key,'type':'edit-brief','target':{'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'},'precondition':{'state':state['state'],'revision':state['revision']},'brief':brief,'confirmation':{'challengeId':challenge['challengeId'],'typedReq':'REQ-001'}})
   original=path.read_bytes();working=json.loads(original);working['tasks'][1]['objective']='UNAPPROVED unrelated T2 change';path.write_text(contract.dumps(working));before=path.read_bytes()
   result=legacy('synthetic-drift-key','Owner edits only T1')
   assert result['status']=='FAILED' and 'PLAN_DRIFT' in str(result) and path.read_bytes()==before and revisions.latest(rdir)['revision']==4
   assert revisions.load_revision(rdir,4)['tasks'][1]['objective']!='UNAPPROVED unrelated T2 change'
   path.write_bytes(original)
   (rdir/'PLAN.md').write_text(plan_md.format(status='review'));before=path.read_bytes()
   result=legacy('synthetic-refused-key','Edit must roll back')
   assert result['status']=='FAILED' and path.read_bytes()==before and revisions.latest(rdir)['revision']==4
   (rdir/'PLAN.md').write_text(plan_md.format(status='approved'))
   import bt_plan_adapter
   with patch.object(bt_plan_adapter,'publishable_problem',return_value='synthetic-publication-refusal'):
    result=legacy('synthetic-publication-failure','Must restore original bytes')
   assert result['status']=='FAILED' and path.read_bytes()==before and revisions.latest(rdir)['revision']==4
   print('E unrelated drift and review-state edits refused without publication; publication failure restores exact bytes; latest/bound stay r4')
   with patch.object(ops,'apply',side_effect=OSError('synthetic rebase I/O failure')):
    result=legacy('synthetic-rebase-failure','Owner approved revision whose rebase fails')
   assert result['status']=='FAILED' and revisions.latest(rdir)['revision']==5 and ops.bound_plan(rdir).revision==4
   result=legacy('synthetic-after-rebase-failure','Further owner edit')
   assert result['status']=='FAILED' and 'PLAN_BASE_STALE' in str(result)
   print('AL injected revise boundary failure leaves approved latest r5 but bound r4; next edit returns PLAN_BASE_STALE')
 finally:server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY_AUDIT
```

## Final artifact checks

All three exact frozen `test -s remote/docs/audit.md` commands exit 0. The ledger parses as audit-findings/1 with
71 unique IDs, valid frozen task references, permitted severity/status values, command/result evidence on every
fixed entry and no accepted risks. Report and ledger verdicts agree. Neither document contains conflict markers.
`git diff --check` and the allowed-path assertion pass; only these two reports differ from entry HEAD.

The audit remains blocked on three high findings whose root task is T15c. No code outside the read-only audit scope
was changed to force a passing result. The independent checker decides the outcome.
