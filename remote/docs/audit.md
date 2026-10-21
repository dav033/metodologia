# Independent security and specification audit — T18

**Rework required: F2, F36, F63, F66 and F67 are high/open.** The substantive criterion “Confirmed high findings
are fixed” is not met. Only this report and `audit.findings.json` change. No risk is accepted on the owner's behalf;
only the independent checker decides the task outcome.

Audited tree: `d17ce292a39950fd735764d724ce3edb92542081`, HEAD at entry for att-0352, 2026-10-21, America/Bogota.
Primary auditor: OpenAI Codex. Fresh independent provider: Anthropic `firstParty / claude-sonnet-5-5`, tools disabled.
Neither reviewer assumes another audit covers omitted scope.

Ledger: **67 findings; 24 rechecked fixed/superseded exposures; 43 open (5 high, 33 medium, 5 low); 0 accepted**.
F1–F65 retain their IDs and both prerequisite/review intents. F61/F62 are now fixed: cross-run blocked identities
and target-scoped native reviews work. F41/F42/F55 remain fixed at their stated boundaries. F36 reopens high because
the gateway dispatcher calls a method absent from its runtime. New F66 records missing HTTP challenge issuance;
new F67 records exhausted failures absent from the actual producer. F63 stays high: creation-time selection was
repaired, but a fresh Bogota round timestamp is misread as UTC and expires before send. F2/F18 still fail.

## Reconciliation and scope

Opened both supplied artifacts before editing. The entry worktree was clean; neither contained conflict markers,
despite the carry warning. Compared `d17ce292a39950fd735764d724ce3edb92542081` with the supplied earlier result
`7b11b3a8948b05d3bd8726fb443f996fc648241d`: 17 implementation/test/configuration paths differ. They change event
exhaustion and round times, run projection, targeted reviews, gateway dispatch, packaging and E2E expectations.
No implementation, test or configuration file is changed here. The carried artifacts were stale reports, not proof.

Read the supplied attempt #14–#19 outcomes and reachable historical ledgers at `0af07a73e`, `108efc35f`,
`f674c6a29`, `b3de1b8ce`, `d9e83adc6`, `8ccc09c9b` and `7b11b3a89`; historical highs included F1/F2/F24/F26/
F28/F32/F33/F35/F36/F41/F42/F55. Raw m6 receipts and omitted attempts are unavailable within this tree. The complete
repository SPEC, PLAN.md, PLAN.json (revision 3), amendments, upstream objectives/acceptance/verification and frozen
headless instructions were read. Prior receipts below are explicitly historical.

Scope covers R1–R18: keyed loopback isolation, input validation, OAuth/session/Origin/limits/logs, ledger/challenges/
preconditions, real edit/freeze/rebase, installed modules, event production/paging/dedupe, targeted failure artifacts,
gateway cache/client/read wiring, notification expiry/restarts/bot, phone contracts, deploy kit and built-web E2E.
Only synthetic credentials, temporary fixtures and owned loopback processes were used. No credential files, live
account/quota readers, SSH, deployment, host services or other worktrees were accessed. Documentation lives only
in these two permitted artifacts; canonical bitacora/cerebro are deliberately untouched per frozen read-only scope.

## Current verification

Python 3.14.7; Node 24.21.0. First installed the existing lockfile with `cd remote/web && npm ci --offline`:
exit 0, 320 packages, no lockfile change. Subsequent checks do not install dependencies or write node_modules.
Python suites use an empty temporary BITACORA_ROOT before imports. Browser/E2E builds ran sequentially.

| Command (shared frozen commands run once) | Actual result on this tree |
|---|---|
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py` | Exit 0; 5 tests, 7.424 s. |
| Same discovery, `test_remote_commands.py` | Exit 0; 29 tests, 3.898 s. |
| Same discovery, `test_remote_events.py` | Exit 0; 13 tests, 1.828 s. Synthetic exhaustion tests pass; real producer fails AH/F67. |
| Same discovery, `test_remote_review.py` | Exit 0; 3 tests, 2.039 s, target-scoped native HTTP. |
| Same discovery, `test_remote_recovery.py` | Exit 0; 12 tests, 4.585 s. |
| Same discovery, `test_platform.py` | Exit 0; 27 tests, 2.011 s, no rerun required. |
| Same discovery, `test_page*.py` | Exit 0; 43 tests, 11.442 s. |
| `cd skill/scripts/bt_scheduler_core && python -m unittest discover -s tests -p test_operations.py` | Exit 0; 18 tests, 0.766 s. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py` | Exit 0; 5 tests, 11.127 s. |
| Same discovery, `test_auth.py`, `test_guard.py`, `test_stream.py`, `test_commands.py` | Each exit 0; 3/7/8/11 tests, 3.263/3.749/2.029/3.231 s. Stream test uses Mock.read_remote and misses actual runtime failure. |
| Same discovery, `test_notify.py`, `test_telegram_send.py`, `test_telegram_bot.py` | Each exit 0; 3/3/5 tests, 0.052/0.015/0.064 s. Real /estado producer mismatch remains W/F50. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 0; 16 tests, 10.207 s; 1 skip: Caddy binary unavailable. |
| `cd remote/web && npm run verify` | Exit 1; lint and strict typecheck pass, 13/14 node tests pass, no skips; Chromium fails `366 !== 360` at panel-browser.test.mjs:165, 18.644 s. Build not reached by verify. F18. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 1; 1 test, 23.527 s; optimized production build passes, then line 403 fails empty events/nextCursor. Subsequent OAuth/command/offline/Telegram assertions unexecuted in this run. F2. |
| `python -m json.tool remote/contract/command.schema.json` and event equivalent | Each exit 0; syntax only, not semantic contract validation. |
| `test -s remote/docs/route-pin.md`, contract.md, architecture.md | Each exit 0. |
| All documented Python reproductions below | Current synthetic probes exercise both retained and repaired behavior; zero exit means asserted observations reproduce, including defects. See final artifact checks. |
| `test -s remote/docs/audit.md` (three frozen criteria) | Each exit 0; existence is not proof that high findings are fixed. |

Python suites total 211 tests with one skip, excluding the separately failing E2E test. Old probes were adapted only
inside this report: C/E seed challenges through the actual Ledger to isolate command/edit behavior, not to claim HTTP
issuance works. H/U/AB use current explicit exhausted counters. AA asserts corrected run identity; AC now controls
America/Bogota and exposes timezone expiry; AG uses actual GatewayRuntime, not the Mock from unit tests. AH initially
assumed history excluded the current attempt; the actual producer includes all three and the report assertion was
corrected without changing product tests. The first AC fixed-behavior hypothesis failed and demonstrated residual F63.

Not run: Python 3.12 (unavailable), real Caddy/container validation/connectivity, deployed GitHub/Telegram/Vercel SSE,
actual selected-route agent execution, installed PWA, exhaustive 44 px target checks, dependency advisory scan or
independent multiprocess/local-writer race stress. No successful deployed behavior is inferred from static/unit
checks. T17 additionally lacks production gateway GET/challenge coverage, even if its early feed failure is fixed.

## Fresh independent other-provider review

Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
Input: **451,396 characters**, numbered current SPEC/PLAN contracts, all gateway Python modules, laptop API/snapshot/
ledger/preconditions/edit/events/recovery/pins/server/live projection, phone/recovery/review components, runbook,
Caddyfile, pyproject and T17. No prior report, ledger, findings, credentials or live state supplied. Tools disabled:
static review only. Receipt exit 0, subtype success, is_error false, 1 turn, provider API duration 296,951 ms,
wall 299.799 s; reported model `firstParty / claude-sonnet-5-5`.
Input SHA-256: `61f895f3604f568626e15571a97958a4fefade30890fe1f60ef17ce9b3188102`.
Output JSON SHA-256: `0d52f6ae469f7c56351615d2ad2ed4c5aa5e204443d17497c583c8025cb1b537`.
Provider item numbers are local to its response, not ledger IDs.

| Provider item | Independent primary verdict and reason |
|---|---|
| 1 high, all reads fail | Confirmed high F36 by seven actual HTTP requests in AG. Missing method is not an UpstreamError. Renaming alone still leaves snapshot/events outside LaptopClient.read_model allowlist and bypasses cached web_snapshot. |
| 2 high, no challenges | Confirmed new high F66 by actual keyed/public HTTP AG; Ledger exists but route_post handles only commands. Manual cancel/delete UI is separate F46. |
| 3 high, offline cache unwired | Confirmed within high F36 plus medium F11/F13. B tests cache/restart; production reads never call web_snapshot. No extra duplicate finding. |
| 4 high, /estado dialect | Confirmed medium F50 by W with actual serializer and bot; authenticated web controls are a separate scope. No authorization bypass. |
| 5 high, alert actions/content | Confirmed medium F6 by notification_for_event and TelegramSender source/B; plain messages remain but required task/cause/link/safe buttons are absent. |
| 6 medium, SSE | Confirmed F21 by HTTP A. Named-frame/onmessage and timestamp/v2 cursor incompatibilities are restoration hazards in disconnected code, not additional currently reachable exposures. |
| 7 medium, error mapping | Confirmed F39 by actual HTTP G and page.tsx response.ok handling. Duplicate status maps are source hygiene, not an additional demonstrated effect. |
| 8 medium, uncertain outcome | Confirmed F40 by real loopback I/I2, F16 by source. No duplicate business effect from a new key is claimed. |
| 9 medium, quota/life sign | Confirmed F44 by Q exact phone parser, F29 by real snapshot C/E and phone field reads. |
| 10 medium, event predicates | Confirmed new high F67 by actual exhausted scheduler/producer AH and exact E2E; F37/H/AB capture retrospective synthetic history, F30 threshold, F58 aggregate quota. Missing producer timestamps/ledger-created_at are not claimed as a fresh required-owner alert defect without a valid producer counterexample. |
| 11 medium, restart/backlog | Confirmed F57 by T/AF: actual paging needs 16 polls (75 s at cadence) behind 3,000 non-notifying events. Same-ID durable dedupe and continuous-outage generation are separately rechecked and pass. |
| 12 medium, rate limits | Confirmed F47 by L for anonymous login behind Caddy. Reject provider wording that command buckets use peer address: current commands use login, yielding existing low F27. |
| 13 medium, OAuth logging | Confirmed F4 by captured real server log A; single-use OAuth values appear in status/request line. No account takeover demonstrated. |
| 14 medium, redaction | Confirmed F56 by synthetic serialized JSON/database-password strings through both exact sanitizers S. Additional PRIVATE_KEY/credential/cookie and unredacted effect-error forms not independently reproduced; no universal-secret-detector claim. |
| 15 medium, sample review | Reject as disguised live evidence: component explicitly says DATOS DE MUESTRA and reports unavailability. Current selected review browser assertions execute before F18. Public review availability is F36. |
| 16 medium, route split | Confirmed F64 by AD with identical unknown-quota candidate. Reject absent pin consumption: inspected scheduler adapter calls bt_route_pins.narrow at lines 393–395; C persists actual selected pin. Unused helper/automatic pin clearing is not a demonstrated frozen requirement violation. |
| 17 medium, note | Confirmed F7 by real Ledger B; standalone note has no dispatcher. Existing retry reason/operator-note path is separate; real next-attempt prompt unrun. |
| 18 medium, inline delivery | Confirmed F51 by Y: 20 synthetic five-second sends consume 100 simulated seconds with exactly one health probe. No real outage duration measured. |
| 19 hypothesis, preconditions/signature | Not confirmed. C executes actual rejected-to-recovering shim/reopen/ready retry; E runs real owner edit/rebase. run_plan(root,project,req,expected,by) checks expected action; dispatch passes approve/launch deliberately. Missing challenge issuance is F66, not proof this signature is wrong. Other raw-state/ABA cases remain unproven. |
| 20 hypothesis, tunnel exposes panel | Rejected for compliant kit: actual advin-bitacora-tunnel.service forwards loopback 18765 to loopback 8766 and runbook installs it; actual RemoteHandler excludes local panel routes. No deployed tunnel inspection done. |
| 21 low, key length | Confirmed F48: current gateway and serve_remote startup lack documented 24-character guard. Empty expected key still refuses every native request; no auth bypass alleged. |
| 22 low, logout/retention | Confirmed F5/F12 by A/B/source; foreign GET removes cookie without revoking stored token. No stolen session tested. |
| 23 low, Unicode state | Confirmed F60 by X: request thread disconnects with TypeError, no state bypass or process-wide denial demonstrated. |
| 24 low, marker/challenge/contracts/paths | Literal marker gap confirmed F5. Challenge bound to target rather than operation is not forbidden by R8; existing one-use checks remain. Schema drift is F17; runbook names versus older PLAN values are not a demonstrated compliant-deploy failure (actual next.config uses FLOW_GATEWAY_ORIGIN). Effect error redaction not independently reproduced. |
| 25 hypothesis, process-local lock | Not confirmed as an exploit; D proves only distinct-key serialization within the remote process, not panel/local writer or multiprocess races. Explicit coverage limit, no owner acceptance. |
| 26 low, unbounded history | Confirmed F12 by B/source; no 90-day sweep in sessions/outbox/history/ledger/observation store. |
| 27 hypothesis, parser/timeouts/errors | Malformed native command disconnect is confirmed F49 by actual HTTP V. Unsupported internal round/decision fixtures and proxy-reachable slow-body exhaustion not reproduced; not accepted risks or fabricated findings. |

The independent reviewer did not receive deploy units/CSS/panel tests/scheduler routing implementation. Primary audit
inspected those sources and ran the frozen checks to adjudicate those gaps; static “e2e covers” wording is superseded
by the current failing E2E receipt. Primary probes additionally retain F3/F8/F9/F18/F26/F48/F52/F53/F54/F63/F65.

## Rejected security hypotheses and remaining limits

No keyed remote bypass is demonstrated: native routes require nonempty bearer key with constant-time bytes compare;
listener/tunnel use loopback separately from local panel. OAuth foreign login/state mismatch/replay tests pass; state
is consumed transactionally and sessions are opaque hashed tokens. Unicode state is F60. Fixed-origin callback/read
allowlists prevent the proposed redirect/SSRF injection. Origin/header/Strict cookies enforce mutation origin; exact
marker/logout deviations remain F5 and query logging F4. Read-route crashes do not bypass authentication.

Real Ledger challenge tests check one-use, target binding and 120-second expiry, while issuance over HTTP is broken
F66. Same-key reservations return UNKNOWN_OUTCOME without another effect; D checks two distinct keys serialize.
Crash recovery, step-up bound to operation, multiprocess/local-writer races are not proved. Review bounded regular-file
reads, O_NOFOLLOW, correlated ledgers, SQLite parameters and git argv/stdin show no demonstrated path/SQL/command
injection. Targeted review repair is checked natively; gateway availability is F36. React text rendering shows no
HTML injection here. Bot allowlist/one-use callbacks pass, but group-chat human identity is not proven by private-chat
tests. No real credentials were used or disclosed.

## Current findings and verdicts

Fixed means rechecked as already fixed in this tree, with executable command/results in the ledger. Open medium/low
issues are unaccepted; none is silently waived. A fixed native component is not proof its public gateway route works.

### F1 — high / fixed — The Caddy upstream and gateway bind instructions match the frozen container-to-host topology.

Tasks: T16. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 16 tests, one Caddy-unavailable skip. Probe B (`python -`): exit 0, both config parsers accept the documented 172.20.0.1:8790 bind. Caddyfile targets that bind. Actual container connectivity remains unrun.

### F2 — high / open — The frozen built-web E2E still fails at the empty feed before OAuth/control/offline/Telegram assertions.

Tasks: T17. `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py`: exit 1, one failure in 23.527 s at line 403: nextCursor is empty, events=[]. Production build passes. The redone fixture now truly makes three failures and expects stale HTTP 409; failure persists because current T6 producer fields do not satisfy exhaustion (F67). T17 still never GETs a production gateway snapshot or tests HTTP challenges, missing F36/F66; it also expects three alerts after one task exhausts its budget (F37). Restore end-to-end acceptance without fabricating producer fields or weakening notification semantics.

### F3 — medium / open — The restored runbook deploys and restarts before installing the service on a fresh host.

Tasks: T16. remote/docs/runbook.md steps 3/4 call deploy.sh before installing the unit; deploy.sh:27 unconditionally restarts under set -e. Fresh local synthetic missing-unit simulation: deploy exit 5 with current already switched; rollback --dry-run exit 2 without previous release; deploy --dry-run exit 0. Kit checks pass but do not check this order. Reorder first-install steps and document containerized Caddy reload/rollback rather than host systemctl reload caddy.

### F4 — medium / open — Gateway request logging still exposes OAuth code/state query values in its status field.

Tasks: T11a. Probe A: exit 0; real loopback synthetic callback query appears in captured server logging. GatewayHandler.log_message uses args[0], the complete request line, as status despite separately sanitizing the path field. No account takeover or session-token theft demonstrated.

### F5 — medium / open — The mutation marker accepts arbitrary nonempty values; GET logout neither checks guards nor revokes its session.

Tasks: T11a, T15a. Fresh Probe A: exit 0; wrong X-Flow-Request yields HTTP 200, foreign-Origin GET logout yields 302/cookie removal and the original session token still resolves. server.py tests bool(marker). Origin checks on actual command POST remain effective; no command CSRF bypass is claimed.

### F6 — medium / open — Telegram alerts omit review links, task/cause details and safe inline actions; retry callbacks are unsupported.

Tasks: T14a, T14b. Probe B: exit 0, Telegram retry returns INVALID_COMMAND. Current TelegramSender posts chat_id/text only, notification_for_event appends only REQ; app.py accepts Telegram pause/resume only. The current five bot tests pass, but use their own fixtures. Alert review/task/cause/buttons remain missing, while /estado pause/resume keyboard is separate.

### F7 — medium / open — The public standalone note command has no laptop dispatcher.

Tasks: T5a. Fresh Probe B: exit 0; real Ledger.submit(note) with commands.dispatch_handlers() returns COMMAND_NOT_IMPLEMENTED. dispatch_handlers advertises no standalone note handler despite COMMANDS and schema listing it. Retry reason/RUN.notes is separate.

### F8 — medium / open — The phone brief form cannot edit acceptance criteria.

Tasks: T15f. Fresh page.tsx editBriefForm still sends only objective/string, without an acceptance criteria editing control. Updated E: both backend field aliases create approved revisions correctly. The remaining criteria UI omission is separate from repaired F41.

### F9 — medium / open — Run-level Reabrir ejecución supplies no task identity to the task-scoped operation.

Tasks: T15d. page.tsx run-level commandForm(reopen) omits taskId; bt_remote_commands.TASK_SCOPED/_member_state and dispatch_run_command require params.task. Fresh Probe C confirms task-scoped reopen succeeds; that repair does not provide an identity for the run-level form.

### F10 — medium / fixed — A plan waiting for approval emits plan.waiting without a scheduler decision.

Tasks: T6. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe B (`python -`): exit 0, plan_status=review emits plan.waiting without a scheduler decision. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py`: exit 0, 13 tests.

### F11 — medium / open — Gateway restart loses the last snapshot; the separately tested stream hub is not wired into production.

Tasks: T12. Updated Probe B: exit 0; offline runtime returns its cached generatedAt using snapshot_cache, while a new runtime sharing the same database returns None, leading the actual snapshot route to HTTP 503. snapshot_cache is memory-only; main/server do not instantiate StreamHub. The previous newly timestamped empty-model behavior has been replaced, but last-state persistence is still absent. F21 separately records missing production streaming.

### F12 — medium / open — Expired sessions and Telegram outbox/history remain unbounded beyond the required 90 days.

Tasks: T11, T14a, T5. Probe B: exit 0; creating a session leaves an abandoned expired row. SessionStore prunes sessions only when presented. Current notifications.py now has telegram_history with timestamped rows (F43 fixed), but no 90-day prune of that table/outbox; Ledger.rows still reads all rows. No unbounded unwired SSE exposure is alleged.

### F13 — medium / open — The phone receives no stable offline-start timestamp.

Tasks: T12, T15b. Updated Probe B: exit 0; cached generatedAt is retained and laptop is only {online:false}, with no checkedAt or offline-start timestamp. GatewayRuntime.web_snapshot does not expose the persisted outage start or liveness offline_since. The phone still renders LAPTOP SIN CONEXIÓN with no HH:MM. Actual T17 currently fails before offline checks, so no passing integrated timestamp assertion is claimed.

### F14 — medium / fixed — Laptop-side redaction handles the previously missed provider assignments and bearer authorization text.

Tasks: T7, T6. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe B (`python -`): exit 0; synthetic OPENAI_API_KEY assignment and Authorization: Bearer values are removed. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py`: exit 0, 3 tests. Quoted credentials remain F56.

### F15 — medium / fixed — The local panel implements inherited systemd listener activation/reload.

Tasks: T9. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py`: exit 0, 27 tests, 2.011 s; inherited listener/reload/ownership tests pass. `test_page*.py` with the same discovery command: exit 0, 43 tests, 11.442 s. No host service touched. Systemctl-unavailable path remains separate F65.

### F16 — medium / open — The phone discards uncertain command envelopes and generates a new key on resubmission.

Tasks: T15d. Fresh page.tsx checks response.ok, labels UNKNOWN_OUTCOME HTTP 503 Rechazado, and retains history summaries rather than an exact replayable envelope/key; form submitters always call crypto.randomUUID(). Server at-most-once remains valid for a reused key; no duplicate effect through a specific ABA sequence was reproduced, so severity stays medium.

### F17 — low / open — The public command schema differs from production command families, fields and key limits.

Tasks: T3. Fresh schema syntax commands exit 0 only. command.schema.json omits answer-decision, expects singular answer/route text/edit brief; actual phone sends answers/round, route object and field/value. Fresh Probe B rejects a 121-character ledger key despite schema maximum 128. This is contract mismatch, not proof of arbitrary execution.

### F18 — medium / open — The required web verification fails the 360 px browser assertion.

Tasks: T15. `cd remote/web && npm run verify`: exit 1; lint/typecheck pass, node suite 13/14 pass, zero skips, 18.644 s; Chromium panel-browser.test.mjs:165 fails 366 !== 360. npm verify does not reach build; separate production build succeeds in T17. Preserve 360 px assertion.

### F19 — high / fixed — The integrated phone app compiles, typechecks and builds without the previous overlapping declarations.

Tasks: T15a, T15c, T15d. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: `cd remote/web && npm run verify`: lint and strict typecheck pass, node tests fail only width F18. `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py`: optimized Next.js production build subprocess exit 0 before feed failure F2. No duplicate declarations remain.

### F20 — high / fixed — The phone accepts the real gateway login session dialect.

Tasks: T15a. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe A (`python -`): exit 0, real gateway returns HTTP 200 {login:dav033}. `cd remote/web && npm run verify`: browser passes sessionContractObserved and selected-review checks before width assertion F18. Production snapshot reads are independently broken, F36.

### F21 — medium / open — Production SSE remains absent; plain events is allowlisted but crashes in the current read dispatcher.

Tasks: T12, T6, T15b. Probe A (`python -`): exit 0, authenticated events/stream returns 404. Probe AG (`python -`): exit 0, plain events drops connection with AttributeError (F36). main/server do not instantiate StreamHub; the 8 passing stream tests exercise isolated hub or a Mock read_remote. Phone opens events/stream and polls snapshot every five seconds.

### F22 — medium / fixed — A completely filled example configuration starts parsing; the prior mandatory-blank allegation is superseded.

Tasks: T16. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe B (`python -`): exit 0, all example keys filled with synthetic values parse in both configs. `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 16 tests, one Caddy skip. Mandatory blanks still refused; optional blank overrides are not a demonstrated compliant-install failure.

### F23 — medium / fixed — Native keyed command history and its web compilation are restored.

Tasks: T4a, T15d. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe C (`python -`): exit 0, real LaptopClient/read_model reaches the keyed laptop history endpoint and receives commands/nextCursor. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py`: exit 0, 5 tests. Web lint/typecheck pass; public gateway dispatch is broken separately F36.

### F24 — high / fixed — Wheel and sdist include the actual edit and route-pin implementation modules.

Tasks: T8, T8a. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe P (`python -`): exit 0, built wheel/sdist contain bt_remote_edit and bt_route_pins; wheel contains bt_remote_preconditions and bt_remote_snapshot; all four isolated -I imports exit 0. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py`: exit 0, 12 tests.

### F25 — medium / fixed — The failed-task link consumes the selected real review attempt instead of only a static fixture.

Tasks: T15c. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: `cd remote/web && npm run verify`: selected real rejected-attempt hash/content assertions pass in Chromium before width failure F18; all 3 `test_remote_review.py` tests pass. Probe AA (`python -`): exit 0, target-specific native causes. This confirms selection/renderer, not public gateway availability (F36).

### F26 — medium / open — Reopen/retry now work in the same tab, but ready recovery controls disappear after reload or in another tab.

Tasks: T15f, T15d. Updated C: exit 0; real task reopen moves recovering -> ready and pinned ops.retry succeeds. Source page.tsx still gates recovery on recovering/reopenedForRecovery, with reopenedTasks only an in-memory useRef. Reload/new tab loses the ready task controls. The source-level ready-state fixture test passes before the browser-width failure, but it does not prove a reload of a real producer snapshot. F41/F42 are now independently fixed.

### F27 — low / open — Command limits remain shared by owner login across sessions instead of per session.

Tasks: T11a. Current server.py uses authenticated login as the commands/challenges rate bucket, sharing quota between all dav033 sessions; exact auth/guard tests pass (3/7). This is stricter than R17 but not an authentication bypass; shared anonymous login availability remains F47.

### F28 — high / fixed — Distinct-key concurrent preconditions serialize with the remote ledger effect.

Tasks: T5. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe D (`python -`): exit 0, two concurrent distinct-key pauses produce one effect, one OK, one STALE_PRECONDITION, two audit rows. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py`: exit 0, 29 tests.

### F29 — medium / open — The restored snapshot still loses run life-sign/revision fields and reads plan criteria from the wrong task level.

Tasks: T4a. Updated C: real snapshot contains one run and one plan. Updated E projects a real r3 task with nonempty frozen acceptance_criteria yet plan task acceptanceCriteria=[]: bt_planstatus stores criteria under task.detail, while bt_remote_snapshot reads task.acceptance_criteria. Runs expose lastActivityAt and attempts last_activity_at, while the phone reads lastSeenAt/updatedAt; run/task revision is absent, so run brief preview lacks the next revision. Plans, rounds and decisionRequests are now collected; the earlier blanket missing-model claim is withdrawn. State-only preconditions remain permitted; no new ABA exploit is asserted.

### F30 — medium / open — Stalled-attempt notifications start after 15 minutes rather than the required more than 10 minutes.

Tasks: T6. Fresh Probe B: exit 0; live attempt has no attempt.stalled at +660 s and does at +901 s. bt_remote_events.STALL_SECONDS=15*60 conflicts with SPEC R10. The emitted text says more than 10 minutes but the threshold does not.

### F31 — low / fixed — The historical post-expiry SSE continuation is unreachable because production streaming was removed.

Tasks: T11, T12. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe A (`python -`): exit 0, authenticated /api/remote/v1/events/stream is HTTP 404. `cd remote/gateway && python -m unittest discover -s tests -p test_stream.py`: exit 0, 8 tests; hub remains disconnected. The historical post-expiry SSE continuation is unreachable, not repaired streaming. Plain events now reaches broken F36 dispatch.

### F32 — high / fixed — The gateway preserves the phone route_id selector and selected model/account pin.

Tasks: T13. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe C (`python -`): exit 0, actual phone route_id/model/account becomes the laptop selectors; real keyed retry on ready stores the selected pin and returns OK with only candidate availability and agent start stubbed. `test_remote_recovery.py`: exit 0, 12 tests. Real selected agent launch unrun.

### F33 — high / fixed — The gateway preserves phone round/answers and edited field/value.

Tasks: T13. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probes C/E (`python -`): both exit 0; real keyed answer-round stores answers, field/value survive translation, both actual edit aliases freeze revisions/rebase. Challenges are seeded directly via real Ledger only to isolate dispatch: HTTP challenge issuance remains high/open F66.

### F34 — medium / fixed — Both frozen notification and delivery test files are restored and execute.

Tasks: T14, T14a. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py`: exit 0, 3 tests; same command with test_telegram_send.py: exit 0, 3 tests. Both frozen files exist and execute; no absent-file zero-test pass.

### F35 — high / fixed — The real laptop snapshot now passes the exact phone parser for a nonempty runs list.

Tasks: T4a. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe C (`python -`): exit 0; real seeded laptop snapshot with nonempty runs and plans passes the exact TypeScript parseSnapshot extracted/transpiled from page.tsx. `test_remote_api.py`: exit 0, 5 tests. Public gateway reads are separate F36.

### F36 — high / open — Every authenticated gateway data read drops its connection because the new dispatcher calls absent GatewayRuntime.read_remote.

Tasks: T7, T12. Probe AG (`python -`): exit 0, seven real authenticated loopback GETs (snapshot/history/commands/quotas/routes/targeted review/events) each disconnect; server hook records seven AttributeError values. read_routes.py:55 calls runtime.read_remote; actual app.py defines only read_model. Current stream unit test passes by using an unrestricted Mock with the nonexistent method. Behind that mismatch, LaptopClient.read_model does not allow snapshot/events, and forwarding snapshot would bypass web_snapshot cache/liveness. A rename alone does not restore R4/R7/R9/R15; wire actual runtime/cache and actual producer integration tests.

### F37 — medium / open — Exhaustion fixtures still retrospectively alert for earlier retryable failures once a task exhausts its budget.

Tasks: T6. Probes H/AB (`python -`): exit 0, one failure within budget yields no alert, but three historic/current failures with authoritative exhausted counters yield three alerts. Current T17 expects three messages after final exhaustion; frozen US-4 requires one for the failure with no retries left. Actual live projection currently produces no failure alerts at all (distinct high F67); keep filtering retryable failures.

### F38 — medium / fixed — Real structured HTTP INVALID_CURSOR now reaches the gateway cursor-reset branch.

Tasks: T13, T12. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe G (`python -`): exit 0, real loopback structured HTTP 400 INVALID_CURSOR reaches GatewayRuntime reset, event_cursor becomes empty. `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py`: exit 0, 11 tests. Rebuild-from-now/backlog policy remains F57.

### F39 — medium / open — HTTP 200 for failed command effects still makes the phone clear forms and treat failed reopen as successful.

Tasks: T13, T15d. Fresh updated Probe G: exit 0; authenticated gateway receives FAILED/ROUTE_UNAVAILABLE and returns HTTP 200. server.py status map omits ROUTE_UNAVAILABLE, EFFECT_FAILED, STATE_UNAVAILABLE and COMMAND_NOT_IMPLEMENTED. page.tsx checks response.ok before setting reopenedTasks and clearing forms.

### F40 — medium / open — The upstream client misclassifies ambiguous success and known refusal, and lets truncated success escape the runtime.

Tasks: T13. Probe I: exit 0; real accepted POST returning HTTP 200 invalid JSON becomes FAILED/LAPTOP_UNAVAILABLE, while synthetic URLError(ConnectionRefusedError) becomes UNKNOWN_OUTCOME because OSError is caught first. I2: exit 0; actual loopback truncated HTTP 200 with Content-Length 100 and two response bytes raises uncaught http.client.IncompleteRead from GatewayRuntime.submit_command. No duplicate effect is claimed; ordinary UpstreamError is caught, so not every transport failure crashes a handler.

### F41 — high / fixed — The edit dispatcher accepts the actual phone objective and acceptance_criteria field aliases.

Tasks: T8a. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe E (`python -`): exit 0, objective and acceptance_criteria aliases create approved/frozen r2/r3 and bind the run to r3 over real keyed command HTTP. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py`: exit 0, 12 tests. Challenges supplied via real Ledger directly; public issuance unavailable F66.

### F42 — high / fixed — Working-plan drift is refused and a rejected approval restores the original working bytes.

Tasks: T8a. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe E (`python -`): exit 0, unrelated working-plan drift returns EFFECT_FAILED/PLAN_DRIFT with identical working bytes and unchanged latest revision; refused approval returns PLAN_NOT_APPROVED and restores working bytes/revision. Real keyed command HTTP and real Ledger challenge are used. `test_remote_recovery.py`: exit 0, 12 tests.

### F43 — medium / fixed — Telegram delivery restores one-hour expiry, exponential backoff and timestamped per-attempt history.

Tasks: T14a. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe N (`python -`): exit 0, expiry drops before send at attempt 0, failed send records timestamped retry, later expiry drops with preserved count. Exact test_notify.py/test_telegram_send.py discoveries each exit 0 with 3 tests. No 90-day pruning claim (F12).

### F44 — medium / open — The restored quota endpoint returns an array of windows that the phone discards.

Tasks: T4a. Fresh Probe Q: exit 0; actual keyed route_get /quotas with one synthetic account/five_hour window returns windows=[{window,usedPercent,resetsAt}], observedAt string. Exact QuotasPanel parser transpiled with installed TypeScript calls record(account.windows), which rejects arrays: parsed account count is 0. Phone expects a windows object with used_percent/resets_at and numeric observedAt. Restore compatible projection or normalize both dialects; mock browser data currently hide the mismatch.

### F45 — medium / fixed — The liveness entrypoint fixture now includes its OAuth settings and passes.

Tasks: T10. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py`: exit 0, 5 tests in 11.127 s, including complete OAuth-configured entrypoint. No real runtime or host service started.

### F46 — medium / open — Phone cancel/delete plan actions require a challenge ID the interface never obtains or displays.

Tasks: T15d. Fresh source inspection page.tsx: buttons disabled unless confirmation text is nonempty and typedReq matches; user must enter Id del reto. sendCommand only auto-fetches a challenge when challengeId is absent, but these forms require it present. No UI requests/displays an ID for copying. Approve/launch auto-challenge behavior remains valid. ; normal forms need the same server-issued challenge flow.

### F47 — medium / open — Anonymous callers behind Caddy share a login throttle and can exhaust the owner login bucket.

Tasks: T11a. Fresh Probe L: exit 0; six synthetic forwarded client addresses reaching one proxy socket receive 302,302,302,302,302,429. server.py keys both login-start and callback buckets on client_address[0]; deployed Caddy is the common upstream peer. An unauthenticated requester can keep the shared five-per-minute start bucket full. Do not trust arbitrary public forwarded headers; derive identity only at the trusted proxy boundary.

### F48 — low / open — Runbook claims both gateway and laptop reject keys shorter than 24 characters, but current startup lacks that length guard.

Tasks: T16. Source config.py checks nonempty gateway key; bt_server.serve_remote directly constructs loopback ThreadingHTTPServer without checking key length. Runbook steps 2/6 claim refusal below 24. All 5 test_remote_api.py tests pass but no longer test startup minimum length. Probe B parses the gateway with a synthetic key. Keyed requests still fail closed when expected key is empty; no authentication bypass is alleged.

### F49 — medium / open — A malformed authenticated native command drops the HTTP connection before validation instead of returning INVALID_COMMAND.

Tasks: T5. Fresh Probe V: exit 0 reproducer. A real loopback POST to bt_remote_api.route_post with synthetic valid gateway key and {idempotency_key:'synthetic-valid-key',command:'pause'} drops the connection with KeyError('target'); the same request without the key returns HTTP 401. bt_remote_commands.fingerprint:264 indexes required fields before validate:268, and Ledger.submit:385-387 catches TypeError/ValueError but not missing-field KeyError. Validate required envelope fields before fingerprinting and return HTTP 400/INVALID_COMMAND. The public gateway fills these keys, so this is native-boundary robustness, not an unauthenticated access bypass.

### F50 — medium / open — Telegram /estado skips every real snapshot run because it reads req_id instead of req/reqId.

Tasks: T14b. Updated W: exit 0; actual bt_remote_snapshot.snapshot projects a synthetic active run with req/reqId; real TelegramBot._send_status sends only the Ejecuciones activas header and no run/keyboard because it reads req_id. Only the snapshot data provider is substituted; real serializer and bot parser execute.

### F51 — medium / open — Inline Telegram delivery can block the production five-second liveness polling cadence.

Tasks: T14a, T10. Fresh report Probe W/Y/Z/O: exit 0; GatewayRuntime.poll_once with 20 due messages and a deterministic sender advancing the clock by the default 5-second request timeout consumes 100 simulated seconds while making exactly one health probe. app.py calls deliver_due inline and notifications.py sends up to 20 sequential messages before returning. This is a deterministic scheduling reproduction, not a measured real Telegram outage; isolate delivery or give it a budget compatible with the five-second health cadence.

### F52 — low / open — The production command deadline defaults to five seconds instead of the specified fifteen seconds.

Tasks: T10, T13. Fresh report Probe W/Y/Z/O: exit 0, GatewayConfig.from_env with required synthetic values and omitted optional overrides returns request_timeout=5.0. app.py passes that same timeout to LaptopClient and upstream.py applies it to command POST. SPEC edge case requires the gateway to time out after 15 seconds. Use a separate 15-second command deadline; the shorter timeout fails safely as UNKNOWN_OUTCOME and does not itself prove duplicate execution.

### F53 — medium / open — An offline transition caused by a command or challenge suppresses the required long-offline active-run alert.

Tasks: T10, T13, T14. Fresh report Probe W/Y/Z/O: exit 0. With cached active-run state, three synthetic UpstreamError command failures mark the laptop offline but leave offline_generation=0; a subsequent health poll at offline_since+901 seconds emits no outbox row. Repeated through issue_challenge with the same result. app.py/180 discard the transition; only poll_once advances the generation, so _notify_long_offline_with_active_run returns early. Handle every transition through one owner and preserve one alert per outage.

### F54 — medium / open — An explicitly empty gateway bind is accepted and passed to the HTTP server as a wildcard address.

Tasks: T10. Fresh report Probe W/Y/Z/O: exit 0. GatewayConfig.from_env and OAuthConfig.from_env accept required synthetic configuration with GATEWAY_BIND=''; create_server passes ('',8790) to the mocked ThreadingHTTPServer constructor (Python IPv4 wildcard bind semantics). No wildcard listener was actually opened. config.py uses get without rejecting the empty value; deploy.sh required-key checks omit GATEWAY_BIND. The runbook correctly instructs 172.20.0.1 (F1 fixed), but malformed production config still fails open at this boundary. Reject empty/wildcard binds or normalize deliberately to the documented private interface. No unauthenticated command bypass is alleged.

### F55 — high / fixed — Persisted first-observation cursors deliver late-derived events after an earlier saved cursor.

Tasks: T6. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe R (`python -`): exit 0, persisted _observe/build_events/page delivers late stall/round after older cursor and advances sequence. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py`: exit 0, 13 tests including production-route late observations.

### F56 — medium / open — Quoted JSON credentials and database connection passwords remain visible inside log and verification strings.

Tasks: T6, T7, T15c. Fresh Probe S: exit 0; feed.redact leaves synthetic password and refresh_token values in serialized JSON and the synthetic DATABASE_URL password unchanged. The exact phone redactReviewText also leaves the quoted JSON password; structured dict password is correctly redacted. bt_remote_events.py,34-42 requires an unquoted name adjacent to colon/equal inside strings; bt_remote_api.py passes logTail and verification text through it. F14 remains fixed only for its original plain provider assignment and bearer-text cases, both freshly rechecked. The observed gap is bounded to these synthetic known credential forms, not a claim that arbitrary secret detection is exhaustive.

### F57 — medium / open — Gateway cursor reconstruction starts from the beginning and lets old feed pages delay fresh notifications beyond 60 seconds.

Tasks: T14. Updated Probe T: exit 0; a fresh runtime calls events with empty cursor and sends a run.finished that predates startup but is within the restored one-hour expiry. Gateway still keeps event_cursor only in memory and invalid-cursor reset also starts from beginning. The former continuous-outage generation-reset component is now repaired: with one durable database and simulated wall/monotonic clocks, outage generation stays 1 across replacement runtimes and total sends stays 1. Same-ID outbox dedupe also remains effective. Only rebuild-from-now remains open; no accepted risk. New Probe AF: exit 0; 3,000 older non-notifying command events precede a fresh round in the persisted feed. _poll_events consumes only one 200-event page per five-second poll and ignores hasMore: no alert after thirteen polls (t=60 s), new round queued on poll sixteen (t=75 s). This is deterministic page/cadence arithmetic, not a live latency measurement.

### F58 — medium / open — Quota notifications have per-account triggers without the frozen all-accounts-exhausted condition.

Tasks: T6, T14. Fresh Probe U: exit 0; build_events receives one exhausted account and one available account, yet notification_for_event creates a quota-exhaustion alert. bt_remote_events.py emits independently per profile and notifications.py renders each; neither checks whether every account is exhausted as required by R10. This is an alert-condition/spec gap, not proof that all-account exhaustion receives no messages. Preserve source freshness and dedupe when introducing the aggregate condition.

### F59 — medium / open — The same failed attempt can enqueue two alerts when first observed in the flow bus and later in the run projection.

Tasks: T6. Fresh Probe U: exit 0; failure of demo/REQ-001 T1/a1 is first represented by flow row flow-1, then by the run-state attempt with its ended_at one second later. Real build_events/page and NotificationOutbox store two different dedupe-key rows. bt_remote_events.py suppresses flow duplicates only inside one current projection; from_flow identity at 176-178 differs from the attempt identity at 79, so sequential observations bypass durable dedupe. These fixtures demonstrate one semantic failure under both producer forms, not a measured frequency in a deployed run. R11 requires a stable key for the same event.

### F60 — low / open — An unauthenticated Unicode OAuth state drops the callback connection instead of returning a controlled invalid-state response.

Tasks: T11. Fresh Probe X: exit 0; real loopback gateway GET callback with synthetic code, query state=%C3%A9 and cookie flow_oauth_state="é" terminates its request with TypeError from hmac.compare_digest on non-ASCII strings. The handler error hook records TypeError and HTTP client gets RemoteDisconnected. server.py does not validate ASCII before comparison. No state bypass, session issuance or whole-process denial of service is demonstrated; the existing one-use/replay protections remain.

### F61 — high / fixed — Blocked events now have run-scoped identities, including when runs reuse att-0001.

Tasks: T6. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe AA (`python -`): exit 0; two real M1 runs allocate att-0001, two blocked events have distinct dedupeKey and NotificationOutbox retains two rows. Exact test_remote_events.py discovery: exit 0, 13 tests including cross-run identity regression.

### F62 — high / fixed — Native failure reviews and the phone request now include the selected run target.

Tasks: T7. Rechecked on d17ce292a39950fd735764d724ce3edb92542081: Probe AA (`python -`): exit 0, two real runs share att-0001 and _failure_review(demo/REQ-001, id)/REQ-002 return their respective distinct causes. Exact `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py`: exit 0, 3 tests; real HTTP selects second run and refuses missing/foreign target. Both phone callers include target. Gateway availability remains F36.

### F63 — high / open — Fresh rounds created in the laptop local timezone still expire before Telegram delivery because their naive timestamps are interpreted as UTC.

Tasks: T6. Probe AC (`python -`): exit 0 with TZ=America/Bogota/time.tzset; actual bt_rounds.new_round creates a fresh naive local created_at on a two-hour-old plan; feed.collect now correctly chooses created_at instead of PLAN.md time, but event_timestamp treats naive time as UTC. Real GatewayRuntime/outbox records dropped/expired at attempt 0 and sends nothing: apparent age is five hours. UTC-source timestamp component is repaired, timezone normalization is not. Preserve truthful creation time and one-hour expiry; produce an explicit timezone/UTC contract.

### F64 — medium / open — The routes endpoint lists unknown-quota routes as available while retry refuses those same candidates.

Tasks: T8. New Probe AD: exit 0; one synthetic candidate with valid authorization/runtime/source and quota_status=unknown is listed available by actual bt_remote_recovery.route_options, but actual bt_route_pins.available with identical candidate/route returns []. The former checks quota != exhausted; the latter requires quota == available. No actual account/quota source was read. Use the same availability rule; refusal is safe but contradicts the selectable route list.

### F65 — medium / open — The local panel cannot start on Linux without systemctl after the new ownership guard.

Tasks: T9. New Probe AE: exit 0; with Linux, no running panel and subprocess.run raising FileNotFoundError for missing systemctl, actual ensure_server treats _unit_enabled as true then tries systemctl --user restart and propagates FileNotFoundError, with zero detached starts. This changes the existing systemd-less startup path under R18. Only subprocess/platform boundaries are stubbed; no host service is started/stopped. Keep the enabled-unit ownership guard while distinguishing unavailable systemctl from an enabled service.

### F66 — high / open — The keyed laptop challenge endpoint was removed, making all challenged web operations unreachable.

Tasks: T5b. Probe AG (`python -`): exit 0; actual RemoteHandler POST /api/remote/v1/challenges with a valid synthetic bearer returns HTTP 404 NOT_FOUND; the authenticated public gateway returns HTTP 200 NOT_FOUND without challengeId. route_post handles only commands. Real Ledger.issue_challenge exists but has no HTTP entrypoint. Phone approve/launch/revise/edit-brief require this issuance; cancel/delete also have independent UI F46. Restore validated/authenticated issuance, 120-second target-bound one-use semantics, and real HTTP tests.

### F67 — high / open — The actual laptop run projection cannot satisfy the new exhaustion predicate, so exhausted failures never notify.

Tasks: T6. Probe AH (`python -`): exit 0; real T17 scheduler fixture exhausts max_attempts=3 and projects attempts=3 with three failed history records, but lacks attempts_used/max_attempts/retries_remaining/retry_exhausted required by _retry_exhausted. Real build_events returns no attempt.failed. Exact T17 also fails with empty real keyed events. The redone bt_live_api removed budget fields while feed tightened their requirement. Expose authoritative per-run/per-task budget state (not guessed global defaults), preserve no-alert-with-retries invariant, and test the real producer/feed/outbox boundary.

## Frozen acceptance coverage and handoff

| Scope | Current disposition |
|---|---|
| R1/R2/R3/R16/R17 | OAuth/key/Origin/isolation and kit checks run; logging F4, marker/logout F5, retention F12, shared quotas F27/F47, key-strength documentation F48, empty bind F54 and Unicode state F60 remain. No deployed proof. |
| R4/R7/R9/R15 | High F36 blocks all actual gateway reads; targeted native review and snapshot parser are repaired. Cache/time/stream F11/F13/F21, snapshot metadata F29, review redaction F56, quotas F44, inline delivery F51 and non-probe outage F53 remain. |
| R5/R6/R8/R13 | Real native reopen/pinned retry/round/edit/freeze/rebase pass C/E; F41/F42 stay fixed. High F66 blocks web challenge issuance. Note F7, criteria UI F8, run reopen F9, retry envelope F16, reload controls F26, failed HTTP F39/F40, manual challenge UI F46, native validation F49 and route availability F64 remain. |
| R10/R11/R12 | Cross-run blocked identity F61 and observation cursor F55 repaired. High F67 loses real exhausted failure events; high F63 drops fresh local-time rounds. F6/F30/F37/F50/F51/F53/F57/F58/F59 remain. Delivery expiry/history F43 retained. |
| R14 | Lint/types/build pass; frozen browser test fails width F18. Mock/browser checks do not establish production gateway availability, installed PWA or exhaustive touch targets. |
| R18/T17 | Platform/page/operations suites pass. Systemd-less startup F65 remains; E2E fails F2 before advertised scenarios and does not check gateway reads/challenges at all. |

Return **T17 (F2)**, **T7/T12 (F36)**, **T6 (F63/F67)** and **T5b (F66)**. Do not undo corrected run-scoped
identities/reviews, edit aliases/rollback, persisted observation cursors, proper retry filtering, one-hour expiry,
Caddy topology, distribution modules or field forwarding. Restore actual producer/runtime boundaries and integration
coverage; changing a Mock to invent the missing production method is insufficient. Keep every medium/low issue
recorded until its owner repairs it or David explicitly accepts it. This read-only task cannot fix those sources.

## Historical receipts and adjudications

All text below this heading until “Reproduction commands” describes earlier snapshots and is superseded by the
current ledger/receipts above. Earlier present-tense judgments are not assertions about att-0352.

### Previous provider receipt on 9ca9ac9ea (att-0344; historical)


Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
Supplied current numbered-source input: **429,934 characters**. It includes SPEC, all PLAN.json contracts, gateway
modules, laptop API/snapshot/ledger/precondition/edit/feed/recovery, server and live projection, phone/recovery/review
components, deploy files/runbook, pyproject and T17 test. No report, ledger or primary findings are supplied.
Receipt: exit 0, subtype success, is_error false, 1 turn, provider duration 384,235 ms, wall 385.873 s;
reported model `firstParty / claude-sonnet-5-5`. Tools disabled; static analysis only.
Input SHA-256: `d72a3cdc354633550306d317e572afab76cc52ffb46ec43cf3b64000d0f18919`.
Output JSON SHA-256: `66264e11b7e9926b01c1425c86b78f7018ff075ea1e15e48793f951a11900b2a`.
Provider finding numbers in this table are local to its response, not ledger IDs.

| Provider item | Primary adjudication and reason |
|---|---|
| 1 high, /estado dialect | Confirmed F50, medium, by W. Bot status/buttons are absent for real snapshots; authenticated web controls remain available, and no authorization bypass occurs. |
| 2 high, alert content/buttons | Confirmed F6, medium, by B and actual TelegramSender payload. Text delivery remains; required task/cause/review/safe actions are absent. |
| 3 high, absent/incompatible stream | Confirmed F21, medium, by actual HTTP A; snapshot polling remains functional. Named-event/onmessage, timestamp/v2 cursor, sequence restart and hub reset/poller claims are restoration hazards in an unwired implementation, not additional currently reachable exposures. |
| 4 high, run-local ID collisions | Confirmed new high F61 and F62 by AA: two real M1 runs allocate att-0001, two blocked events dedupe into one, and actual review discovery returns the first run's cause. Separate producer and review owners T6/T7. |
| 5 high, historical failure alerts | Confirmed residual F37, medium, by AB: three historic/current failed attempts become three final-exhaustion messages. H confirms no false alert before exhaustion; final failure still notifies, so retain medium for repeated/misclassified alerts. |
| 6 high, failed effects HTTP 200 | Confirmed existing F39, medium, by actual HTTP G and phone response.ok branch. Result JSON still exposes failure and laptop guards remain; no unauthorized effect demonstrated. |
| 7 high, impossible E2E assertion | Confirmed high F2: exact T17 fails earlier on empty feed; source additionally expects stale HTTP 200 while server emits 409. Earlier passing receipt does not apply to this tree. |
| 8 high, command/challenge offline transition | Confirmed existing medium F53 by Z, with no alert after +901 s. Normal health-triggered outage alerts and their restart dedupe now pass T; this is a narrower lost-transition path. Concurrent monitor races are unproven, not asserted as a separate exploit. |
| 9 high, restart/lag/expiry | Confirmed new high F63 by AC using an actually created round, real plan/feed and real outbox; source age wrongly drops a fresh required alert. Existing F57 covers first-start cursor/lag; AF proves 75 s of pagination at the five-second cadence. F12 covers unpruned history. Mere changes in plan updated_at are not independently treated as duplicate semantic events without a supplied identity rule. |
| 10 medium, stall threshold | Confirmed F30 by B: no stall at 660 s, stall at 901 s. |
| 11 medium, exception order | Confirmed F40 by real loopback I and I2: refused connection becomes UNKNOWN; malformed success becomes FAILED; truncated success escapes as IncompleteRead. |
| 12 medium, quota dialect | Confirmed F44 by Q: exact phone parser discards real account/windows array. |
| 13 medium, note/criteria | Confirmed F7/F8 by B and exact form source. Reject missing retry-note support as proven by this item: run retry passes reason into existing operator-note handling; a live next-attempt prompt is unrun. |
| 14 medium, route availability mismatch | Confirmed new F64 by AD on identical synthetic unknown-quota candidate. Reject a broken scheduler pin-consumption assertion: bt_scheduler_adapter calls bt_route_pins.narrow; actual retry/pin tests and C pass. Unused older pin-write helper alone is not a defect. |
| 15 medium, manual challenge UI | Confirmed F46 by source: button requires an ID that nothing obtains/displays, preventing sendCommand's automatic issue path. |
| 16 medium, offline timestamp/cache | Confirmed F11/F13 by B/source. Current snapshot_cache is memory-only and restart offline returns unavailable; liveness has no stable web offline-start time. Snapshot errors retaining stale data are observed in source; no independent live-data freshness measure claimed. |
| 17 medium, inline delivery | Confirmed F51 by Y: 20 synthetic five-second sends consume 100 simulated seconds with one health probe. |
| 18 medium, deadline/new keys | Confirmed F16 and low F52 by source/O/I. Earlier timeout is safe and observable; no duplicate business effect with a new key is demonstrated. |
| 19 medium, proxy limits/logs | Confirmed F4/F27/F47 by A/L/source. Distinct forwarded addresses share sixth-login 429; OAuth query appears in the logged request-line status field. |
| 20 medium, logout/identity | Logout nonrevocation confirmed F5 by A. Reject numeric GitHub identity pinning as a frozen requirement: sole specified identity is login dav033. No stolen-cookie session exploit demonstrated. |
| 21 medium, blank bind/short key | Confirmed F48/F54 by B/O and actual listener source; only nonempty bearer key enforced. O mocks server construction and opens no wildcard listener. Prescribed install explicitly fills example keys and installs private env files, so no separate compliant-install blank-env/mode failure is asserted. |
| 22 medium, Caddy instructions | Confirmed within F3 by J/runbook: first-install restart precedes unit install; documented host systemctl reload does not target the known Docker Caddy. Actual installation unrun. |
| 23 medium, review fixture/failed alias | Reject disguised sample evidence: page explicitly labels DATOS DE MUESTRA and displays unavailability. Current selected rejected-attempt review assertions execute before F18, F25 remains fixed. Alternative raw failed-only projection is not demonstrated for the actual scheduler-to-planstatus dialect. Global review identity is independently confirmed F62. |
| 24 medium, secret redaction | Confirmed F56 by S, exact laptop and phone sanitizers with synthetic JSON/password/refresh/database URI strings. Additional truncated PEM/Basic/Cookie forms were not independently demonstrated here; no exhaustive sanitizer claim is made. |
| 25 medium, decision/quota semantics | Quota predicate confirmed F58 by U. Decision emitted as plan.waiting gets plan-approval wording, included in F6's missing alert context; no extra unique finding. |
| 26 medium, malformed internal feed/round | Not confirmed as a supported-producer failure or reachable unauthenticated attack. Provider uses malformed internal dictionaries/rounds; no current end-to-end counterexample from a valid producer is supplied. Record as robustness/coverage limitation, not an accepted risk or fabricated finding. Native malformed public command is independently confirmed F49. |
| 27 medium, systemd-less Linux | Confirmed new F65 by AE: actual ensure_server propagates FileNotFoundError without detached start when systemctl is unavailable. Preserve enabled-unit ownership guarantees while restoring this R18 path. |

Low/hygiene adjudication: retention is F12, first-install/rollback is F3. Stdlib/bare Python implements PLAN.md's
explicit offline-verifier ruling, which supersedes SPEC's earlier uv/ruff choice. Missing Docker ordering and
ignored Telegram retry_after are not proven compliant-install/permitted-backoff failures. Rotated-token 401 is a
configuration error; permanent rejection policy is not shown to violate the specified API-outage retries. Bot
offset replay is constrained by one-use ephemeral callback tokens; no duplicate effect is demonstrated. OK versus
done is naming, while actual failure/success handling is F39. Development rewrite fallback is not a demonstrated
configured-production failure. Weak report-existence/JSON checks are correctly identified as insufficient: this
report executes substantive checks and expressly reports all open highs; existence never implies acceptance.
The primary audit covers R1–R18 even though the task's covers metadata lists fewer requirements.

Unproven provider assumptions adjudicated: real command/member preconditions and accepted revision edits execute
C/E and 63 laptop tests, including correct operation signatures; scheduler narrowing is present in the actual
adapter. Source approval/launch remains guarded by challenges and tests. Post-freeze failure compensation/crash or
unrelated local-writer races were not demonstrated and are not claimed safe. Round/decision parsing, local assets,
CSS and OAuth cookies are partly covered by the actual browser/kit checks, with width failing F18. Wheel imports
cover the newly split snapshot module; the removed unused bt_remote_views name is not a runtime import failure.
Real Caddy/Vercel/Telegram and route-selected execution remain unrun. The approval of this headless assignment is
given by the user's frozen-plan instruction; SPEC frontmatter status is not evidence that the assignment lacks
authorization. The reviewer does not inspect user credentials, services or private state.



The following three prior source snapshots are preserved as historical evidence, including their original primary
judgments/rejections. They were not rerun as provider invocations today. Their present-tense wording applies to
those old trees only; current statuses, severities, evidence and repaired subcases are above and in the ledger.

## Historical other-provider review on af6a467ed (att-0331)

Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
Current numbered source bundle: 315,240 characters, including SPEC, all PLAN.json task contracts, every gateway
Python module, laptop API/ledger/preconditions/edit/event modules, phone page/recovery panels, Caddy/deploy/rollback,
gateway env example and runbook. The current audit report, ledger and primary conclusions were not supplied.
Receipt: exit 0, subtype success, is_error false, 1 turn; duration 331,078 ms, wall 332.377 s;
reported `firstParty / claude-sonnet-5-5`. Tools disabled, no dynamic checks or write access.
Input SHA-256: `606955d605eef0686061858d7996889d2207e8f68489615589b0b73aa5d80d88`.
Output JSON SHA-256: `1dc0a86ceadc8d6faca950222995a613749b2b4b390761181aa771cecfb26391`.

| Provider item | Primary verdict and independent evidence |
|---|---|
| 1 high, late event cursor | Confirmed new high F55 by R using real producer/page/gateway consumer. Assign T6, which owns discovery ordering. T14 consumes the supplied cursor correctly; absence of an additional T17 regression is not a separate faulty result. |
| 2 medium, OAuth log query | Confirmed existing F4 by real HTTP A; sanitizing only the path field does not sanitize the logged request line. |
| 3 medium, failed effects treated as success | Confirmed F39 by real HTTP G and exact phone response.ok branch. |
| 4 medium, blocking Telegram | Confirmed F51 by grouped Y, 100 simulated seconds and one probe for 20 sends. |
| 5 medium, timeout/ambiguous results/new keys | Confirmed F16/F40/F52. I tests malformed success and refusal; new I2 proves uncaught IncompleteRead after a truncated success. A duplicate business effect is not demonstrated: different keys alone do not defeat current preconditions or same-key at-most-once. |
| 6 medium, shared proxy throttle | Confirmed F47 by real HTTP L, including distinct forwarded addresses. |
| 7 medium, quoted credentials | Confirmed new F56 by exact laptop and phone sanitizers in S, with entirely synthetic values. Structured dictionary redaction remains effective. |
| 8 low–medium, logout revocation | Confirmed within existing F5 by A; no stolen-session exploit is claimed. |
| 9 low–medium, blank bind/key/mode | Empty bind and inaccurate key claim confirmed F54/F48 by O/B/source. Reject missing env-mode enforcement as a separate demonstrated installation defect: prescribed install uses mode 0600, and the service uses UMask=0077. Deployment does not validate mode, but no nonprivate secret file was accessed or demonstrated. |
| 10 medium, failed edit mutation | Confirmed F42 by real approval failure E; retain high because E additionally demonstrates freezing unrelated unapproved task drift and real run rebase. |
| 11 high, Telegram alert context/buttons | Confirmed existing F6, medium: alerts still deliver text, while task/cause/link/safe controls are absent. No loss of all delivery or unauthorized command demonstrated. |
| 12 medium, notification semantics | Threshold and false exhaustion confirmed F30/F37. New quota aggregate gap F58 and sequential flow/state identity gap F59 confirmed U. Decision-as-plan text is covered by F6; no additional issue is inferred solely from event naming. |
| 13 medium, restart progress | Confirmed new F57 by T for historical first start and same-outage generation reset. Existing same-event outbox dedupe is preserved and is not claimed broken. |
| 14 medium, missing/mismatched SSE | Production absence confirmed F21 by A/source. Named-event/onmessage, cursor, hub restart and queue observations concern an unwired implementation; record them as restoration hazards, not newly reachable production exposures. |
| 15 medium, missing plan/round/decision models | Confirmed F29 by real projection C and source; basic runs still parse and render. |
| 16 medium, edit dialect | Confirmed F41 by real keyed HTTP/ledger C; retain the blocking high verdict for the actual remote edit path. |
| 17 low–medium, manual challenge | Confirmed F46; the cancel/delete UI supplies an unissued challenge ID. |
| 18 low–medium, run reopen | Confirmed F9 by absent task identity; task-scoped reopen remains repaired C. |
| 19 low–medium, quotas dialect | Confirmed F44 by exact quota producer/parser Q. |
| 20 low, offline/history/age/header gaps | Confirmed existing F11/F13/F43/F5 by B/N/A; preserve their recorded medium severities and separate impacts. |
| 21 low, hygiene/Unicode state | Unicode input confirmed new low F60 by real HTTP X. Duplicate constants/dead helpers/unused symbols are rejected as standalone behavioral findings without a demonstrated effect. Missing-key native envelope failure is separately confirmed F49 by V. |
| 22 low, deployment instructions | Container reload/install ordering covered by F3/J. Reject absent state-directory provision: current unit has StateDirectory=bitacora-gateway, mode 0700, ReadWritePaths and UMask. Blank optional overrides fail parsing, but prescribed installation explicitly fills every key (F22 rechecked); no separate compliant-install failure. Live container env injection remains untested. |

Provider process observation is valid: report-existence and JSON-syntax checks cannot prove semantic acceptance.
All upstream unique frozen verification commands were actually executed, and this report expressly fails the
all-high-fixed criterion. Their weak acceptance coverage is not converted into a fabricated passing verdict.

Current rejected security hypotheses: no command CSRF bypass through Origin/custom-header/Strict-cookie guards;
OAuth replay/cross-target challenge reuse rejected by one-use stores and tests; no foreign login issued by
OAuthService; keyed routes and bounded read-model destinations prevent the proposed direct laptop auth/SSRF bypass;
review file access uses bounded no-follow regular files and parameterized queries; same-key reservations never
reexecute a PENDING effect; Telegram checks the configured chat and token-bound callbacks. These claims are
limited to the inspected implementation/tests: group-chat sender identity, command-bound step-up authentication,
numeric GitHub identity pinning and a duplicate effect after a new-key retry are not claimed proven safe or required
by the frozen contract. X confirms malformed Unicode handling without claiming OAuth state bypass.

Provider could not inspect units/listeners, rewrites/CSS/review component, scheduler/pin/plan internals, real
Vercel/OAuth/Telegram or tests. The primary audit independently checked the remote-only port 8766 handler and
18765-to-8766 tunnel (not the unauthenticated 8765 panel), state-directory unit, actual selected review and installed
packaging, exact parser/command/retry/edit boundaries, local-panel suites and kit. Actual deployment remains unrun.
The previous provider reviews below are retained as historical adjudication, not current execution evidence.

## Previous other-provider review on 85f4fe33d (historical)

Historical invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
A numbered source bundle of 206,155 characters was supplied on stdin, without the audit report, ledger or primary
conclusions. It contained SPEC, every gateway Python module, laptop API/ledger/preconditions/edit code, phone
page/recovery panels, Caddy/deploy/env example and runbook. No tools or write access.
Receipt: exit 0, subtype success, is_error false, 1 turn; provider duration 205,529 ms, wall 206.747 s;
reported `firstParty / claude-sonnet-5-5`.
Input SHA-256: `af9c4a49a479c0f4f1c7ca09aa96af949074177aa77579d342f0c151a6aa8c78`.
Output JSON SHA-256: `d1395e091a5f08ff7755c44b5ddb3961d27f2a9cfe2fc708b366a22cd5b4f825`.

| Provider item | Primary verdict and reason |
|---|---|
| 1 high, absent planning/round/decision models and manual challenge UI | Confirmed F29/F46. Retain medium: secondary plan/round controls are unavailable, while authenticated basic run read/control works; no authorization bypass is shown. Actual projected snapshot C and exact rendering conditions confirm the gap. |
| 2 high, Telegram alert details/buttons | Confirmed F6, medium: text alerts still arrive; required context/links/safe controls are missing. No loss of every alert or unsafe-command authorization is demonstrated. |
| 3 medium, /estado snapshot dialect | Confirmed new F50 by exact production projection into TelegramBot in W. |
| 4 medium, absent stream | Confirmed F21 by actual authenticated HTTP A; isolated StreamHub tests do not establish production wiring. |
| 5 medium, failed effects HTTP 200 | Confirmed F39 by G and phone response.ok branch. |
| 6 medium, brief/note and write-before-approval | Confirmed F7 and previously high F41/F42. C reproduces the real phone edit failure; E additionally proves freezing unrelated unapproved task drift. Preserve the high approval-boundary verdict. |
| 7 medium, run-level reopen | Confirmed F9: no task identity reaches task-scoped target_state/dispatch. Real task-scoped reopen still passes C. |
| 8 medium, refusal classified unknown | Confirmed F40 by I. Malformed-success ambiguity is also retained; no blanket handler-crash conclusion. |
| 9 medium, delivery blocks probes | Confirmed new F51 by Y: 20 sequential sends consume 100 simulated seconds with one health probe. No real outage latency is claimed measured. |
| 10 medium-low, command deadline | Confirmed new low F52: default config/client path is five seconds versus SPEC fifteen; the earlier failure is safe/observable, not a demonstrated duplicate effect. |
| 11 medium-low, non-probe offline transition loses alert | Confirmed new medium F53 by Z through both commands and challenges, then a real poll after simulated +901 s. |
| 12 medium-low, restart cache/offline timestamp | Confirmed existing F11/F13 by B and runtime/phone source. |
| 13 medium-low, shared proxy login bucket | Confirmed F47 by L; forwarded identities do not affect the bucket. |
| 14 low-medium, empty bind/blank overrides/short key | Empty bind confirmed medium F54 by O without opening a wildcard listener; short-key mismatch remains F48. Reject blank overrides as a separate prescribed-install failure: runbook says fill every key, and fully filled config succeeds B/F22. Actual Caddy topology is corrected F1. |
| 15 low, logout non-revocation/GET | Confirmed within F5 by A; no stolen-cookie exploit or cross-site command mutation demonstrated. |

Provider rejections checked against current source/tests: fixed-origin read-model allowlist and attempt regex
prevent the proposed path/SSRF injection; target-bound one-use 120-second challenges reject replay and spec does
not require command binding; same-key ledger reservations replay UNKNOWN_OUTCOME without another effect; OAuth
state is one-use/constant-time and foreign login refused; owner chat allowlist and random one-use callback tokens
prevent the alleged foreign-chat command; persisted outbox dedupe prevents ordinary restart reread resending;
review reads use bounded no-follow regular files; unset gateway key fails closed. Numeric GitHub ID pinning is an
enhancement beyond login dav033. The nonempty marker is still a literal R2 mismatch (F5) despite no demonstrated
command CSRF bypass. Delivery crash ambiguity and group-chat ownership are not asserted fixed by those rejections.

Provider limits: no dynamic tests; omitted event generator, listener, rewrite, review component, units/rollback,
scheduler/plan/pin internals and live.* models. The primary audit covers those using source and current
tests/probes; another auditor's scope is not assumed to cover them. Deferred-command-after-resume exploitation
and a group-chat deployment were not demonstrated.

## Prior other-provider receipt and adjudication (historical)

This receipt is retained from att-0317, not presented as a fresh invocation. References to numbered provider items
in retained finding evidence refer to this table; today's reproducers recheck the unchanged claims.

Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
Numbered source bundle supplied on stdin: 99,757 characters. It included requirements and full gateway HTTP/auth/
config/client, phone page/recovery panels, edit/recovery dispatch helpers and deployment/runbook files. It received
no existing audit report, findings ledger or primary conclusions, and had no tools/write access.

Receipt: exit 0, subtype success, is_error false, 1 turn; provider duration 136,983 ms, wall 138.261 s;
reported `firstParty / claude-sonnet-5-5`.
Input SHA-256: `b60a8f46b3bde89c30580c7dcbcb74f2c4243aa8d6fffa8f6e60ffe3a9653955`.
Output JSON SHA-256: `19542fe108c8de67f7ff4ca9902c5e2f3424a77e0a5b442b3c3783059616281a`.
This established an other-provider pass of that earlier supplied scope, not who authored every prerequisite. The primary
auditor independently checked the omitted runtime/ledger/Origin/laptop modules and complete acceptance scope.

| Provider item | Primary verdict and reason |
|---|---|
| 1 high, container loopback | Previously confirmed F1; now rechecked fixed by the corrected upstream, explicit bind and current kit checks. |
| 2 high, first-install restart | Confirmed F3, medium: local reversible install ordering defect, demonstrated with fake missing-unit systemctl. |
| 3 high, phone unknown outcome/new key | Confirmed medium F16. Missing exact replay is real; no demonstrated duplicate effect defeating state guards, and different keys do not themselves violate same-key at-most-once. |
| 4 high, upstream failures/handler crash | Confirmed ambiguous outcome classification F40; blanket crash rejected for tested malformed-200 path because runtime catches UpstreamError. Truncated IncompleteRead not dynamically exercised. |
| 5 high, edit field/typed_req | Field mismatch confirmed high F41 by real C. Separate typed_req allegation rejected: Ledger injects it from the validated one-use challenge. |
| 6 high, edit drift/write before validation | Confirmed high F42 by valid real freeze/rebase and real approval failure in E. External writer races/crash exploitation are not claimed proven. |
| 7 medium, marker accepts any nonempty value | Confirmed within F5; Origin still guards command POST. |
| 8 medium, failed effects HTTP 200 | Confirmed F39 by real gateway HTTP in G. |
| 9 medium, browser-only ready recovery flag | Confirmed narrowed F26. Immediate ready-state recovery was repaired; reload/other-tab loses flag. |
| 10 medium, shared proxy login bucket | Confirmed F47 by L and actual server bucket key. |
| 11 medium, logout does not revoke | Confirmed within F5 by A; no session-theft exploit claimed. |
| 12 medium, cancel/delete challenge not supplied | Confirmed F46 from exact form/disabled/auto-fetch control flow. |
| 13 medium, absent stream endpoint | Confirmed F21 by A and full production runtime source. |
| 14 medium, unconditional resume after edit | Explicit ops.resume observed. Rejected as separate spec violation: an agreed pause-preservation contract was not supplied; partial edit/freeze failure is already F42. |
| 15 medium, recovery helper pins fragile | Not confirmed for production dispatch: active path imports bt_route_pins, not bt_remote_recovery.write_pin. Corrupt-pin fail-closed/private helper usage alone is not a security/spec defect. Tested real selector persistence remains F32. |
| 16 medium, short key accepted/plain HTTP | Confirmed low documentation/config mismatch F48. Plain loopback HTTP through the prescribed SSH tunnel is intentional; arbitrary hostile config is not a demonstrated transport exploit. |
| 17 low, mutable GitHub login | Rejected as requirement violation: SPEC explicitly restricts login dav033. Numeric-ID pinning is an enhancement, not an observed unauthorized session. |
| 18 low, nested JSON crashes handler | Rejected on this tree/runtime: L sends 1,200 nested arrays and receives 400/INVALID_COMMAND, with no server handler error. Python 3.12 not exercised. |
| 19 low, refusal classified unknown | Confirmed as part of F40 by I. |
| 20 low, sessions never swept | Confirmed within medium retention finding F12 by B. |
| 21 low, missing revision weakens preconditions | Missing metadata confirmed F29; independent state-only violation rejected because R6 permits expected state. No concrete ABA interleaving shown. |
| Provider rejected OAuth query log leakage | Primary rejects that rejection: log status is args[0] (request line), even though path field is sanitized. Real HTTP A confirms F4. |

Other provider rejections retained: cookie flags/state one-use are tested compliant; review path regex rejects
traversal and file reader uses bounded/no-follow regular-file reads; no React raw-HTML XSS was found; shell `[ -n
previous ] && ...` does not itself cause first-install set-e failure (the actual restart does). Speculative Caddy
encoding/buffering and copied-file permission claims are unconfirmed. Provider omitted ledger/challenge/Origin/key
scope is independently covered by current tests/source, not assumed covered by another auditor.

## Reproduction commands

Run from repository root after dependency installation. All data/credentials are synthetic. A zero exit means each
asserted observation holds, including defects. Tests use temporary state; availability and agent/process starts are
stubbed only where explicitly stated. The following scripts replace obsolete failure assertions while preserving
previous reproduction coverage.

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
    def read_remote(self, path): return {'events': [], 'nextCursor': ''}
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
        for path in ('/api/remote/v1/events/stream?after=abc',):
            result = request('GET', path, cookie); print('SSE', path, result[:2]); assert result[0] == 404
        request('GET', '/api/auth/callback?code=SYNTHETIC_CODE&state=SYNTHETIC_STATE')
        leaked = 'code=SYNTHETIC_CODE&state=SYNTHETIC_STATE' in capture.getvalue()
        print('query logged', leaked); assert leaked
    finally:
        server.shutdown(); server.server_close(); worker.join(); log.removeHandler(sink)
PY
```

### Probe B — cache, retention, redaction, events, commands and filled config

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
PY
```

### Probe D — concurrent distinct-key preconditions

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

### Probe C — real snapshot/parser, read routes, reopen/retry and edit dialect

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
  runtime._refresh_active_run_cache();snapshot=runtime.web_snapshot()
  run=snapshot['runs'][0];task=run['tasks'][0]
  print('snapshot run fields',sorted(run),'plan count',len(snapshot['plans']))
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
  print('Edit adapter preserves objective; valid full revision, real HTTP and failure rollback are exercised by E.')
 finally:
  server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY
```

### Probe G — structured HTTP cursor reset and failed-effect HTTP 200

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
 assert runtime.event_cursor==''
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

### Probe H — false retry-exhaustion notification

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
assert not any(messages)
state['runs'][0]['tasks'][0].update(attempts_used=3,retries_remaining=0)
messages=[notification_for_event(e) for e in feed.build_events(state)]
assert len(messages)==1 and messages[0]
print('exhausted budget -> exactly one alert')
PY
```

### Probe I — uncertain outcome classification

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

### Probe P — actual installed distributions

```bash
python - <<'PY'
import pathlib, subprocess, sys, zipfile, tarfile
root=pathlib.Path.cwd();sys.path.insert(0,str(root/'tests/migration'))
import installed_wheel
installed=installed_wheel.get()
with zipfile.ZipFile(installed.wheel) as archive:
 names=set(archive.namelist())
 assert 'bt_remote_preconditions.py' in names and 'bt_remote_snapshot.py' in names
 assert 'bt_remote_edit.py' in names and 'bt_route_pins.py' in names
 print('wheel contains bt_remote_edit.py and bt_route_pins.py')
with tarfile.open(installed.sdist) as archive:
 names={pathlib.Path(p.name).name for p in archive.getmembers()}
 assert 'bt_remote_edit.py' in names and 'bt_route_pins.py' in names
 print('sdist contains both recovery implementation modules')
for name in ['bt_remote_preconditions','bt_remote_edit','bt_route_pins','bt_remote_snapshot']:
 result=subprocess.run([str(installed.python),'-I','-c',
  f'import sys;sys.path.insert(0,sys.argv[1]);__import__("{name}")',str(installed.site)],
  cwd=installed.work,capture_output=True,text=True)
 print('isolated import',name,'exit',result.returncode)
 assert result.returncode == 0
PY
```

### Probe E — phone dialect, approved-base drift and failed-edit rollback over real keyed HTTP

```bash
python - <<'PY'
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
   result=send(1,'objective','Owner edits only T1');assert result['status']=='OK' and result['outcome']['revision']==2
   assert revisions.load_revision(rdir,2)['tasks'][0]['objective']=='Owner edits only T1' and ops.bound_plan(rdir).revision==2
   result=send(2,'acceptance_criteria',['Owner approved criterion']);assert result['status']=='OK' and result['outcome']['revision']==3
   assert revisions.load_revision(rdir,3)['tasks'][0]['acceptance_criteria']==['Owner approved criterion'] and ops.bound_plan(rdir).revision==3
   runtime._refresh_active_run_cache();snapshot=runtime.web_snapshot()
   projected=next(t for plan in snapshot['plans'] for t in plan['tasks'] if t['id']=='T1')
   print('F29 current projected plan criterion',projected['acceptanceCriteria'],'run fields',sorted(snapshot['runs'][0]))
   assert projected['acceptanceCriteria']==[] and 'revision' not in snapshot['runs'][0]
   working=json.loads(path.read_text());working['tasks'][1]['objective']='UNAPPROVED unrelated T2 change';path.write_text(contract.dumps(working));before=path.read_bytes()
   result=send(3,'objective','Reject drift');assert result['status']=='FAILED' and 'PLAN_DRIFT' in str(result)
   assert path.read_bytes()==before and revisions.latest(rdir)['revision']==3
   path.write_bytes(revisions.revision_path(rdir,3).read_bytes());(rdir/'PLAN.md').write_text(plan_md.format(status='review'));before=path.read_bytes()
   result=send(4,'objective','Must roll back');assert result['status']=='FAILED' and 'PLAN_NOT_APPROVED' in str(result)
   assert path.read_bytes()==before and revisions.latest(rdir)['revision']==3
   print('F41/F42 rechecked: both public field aliases freeze/rebase; drift and refused approval preserve bytes/revision.')
 finally:server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY
```

### Probe N — restored Telegram expiry, backoff and timestamped history

```bash
python - <<'PY'
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
PY
```

### Probe Q — actual quota projection into the exact phone parser

```bash
python - <<'PYCODE'
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
PYCODE
```

Observed: a projected real account with one usage window is discarded; phone parsed account count is zero.
Only the quota data reader returns a synthetic row; projection and exact parser are production implementations.

### Probe L — proxy-shared login bucket and rejected JSON crash hypothesis

```bash
python - <<'PYCODE'
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
 server=Server(('127.0.0.1',0),make_handler(service,Runtime()));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
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
PYCODE
```

Observed: sixth login receives 429 despite distinct forwarded identities. Nested JSON reaches the synthetic runtime stub and receives 200 without a handler crash on Python 3.14; this is not a claim that the real command runtime accepts a nested list.

### Probe J — first-install ordering without touching system services

```bash
python - <<'PYCODE'
import pathlib,subprocess,tempfile,os
root=pathlib.Path.cwd()
with tempfile.TemporaryDirectory(dir=root/'remote',prefix='.audit-deploy-') as tmp:
 d=pathlib.Path(tmp);binpath=d/'bin';binpath.mkdir();state=d/'gateway';env_file=d/'synthetic.env'
 env_file.write_text(''.join(key+'=synthetic\n' for key in ['LAPTOP_ORIGIN','FLOW_GATEWAY_KEY','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID','GATEWAY_DATABASE','GITHUB_CLIENT_ID','GITHUB_CLIENT_SECRET','SESSION_SECRET','FLOW_FRONTEND_ORIGIN']))
 (binpath/'systemctl').write_text('#!/bin/sh\nprintf "synthetic first-install missing unit\\n" >&2\nexit 5\n');(binpath/'systemctl').chmod(0o755)
 env={**os.environ,'PATH':str(binpath)+':/usr/bin:/bin','GATEWAY_ROOT':str(state),'GATEWAY_ENV_FILE':str(env_file)}
 r=subprocess.run(['bash','remote/deploy/deploy.sh','remote/gateway'],env=env,capture_output=True,text=True)
 print('fresh install with missing-unit systemctl EXIT',r.returncode,'current switched',(state/'current').is_symlink(),r.stderr.strip());assert r.returncode==5 and (state/'current').is_symlink()
 r=subprocess.run(['bash','remote/deploy/deploy.sh','remote/gateway','--dry-run'],env=env,capture_output=True,text=True);print('deploy --dry-run EXIT',r.returncode);assert r.returncode==0
 r=subprocess.run(['bash','remote/deploy/rollback.sh','--dry-run'],env=env,capture_output=True,text=True);print('rollback without previous EXIT',r.returncode);assert r.returncode==2
PYCODE
```

Observed: deploy exits 5 after switching current when the first-install service is absent. It cannot roll back
without a previous release. The fake systemctl only prints a synthetic diagnostic; no service restart occurs.

### Probe V — malformed authenticated native command

```bash
python - <<'PY'
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
PY
```

Observed: unauthorized request is refused with 401; the keyed incomplete envelope drops the HTTP connection
with KeyError instead of returning structured INVALID_COMMAND. No effect handler runs.

### Probes W/Y/Z/O — fresh provider interoperability, delivery, liveness and config

```bash
python - <<'PY'
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
 with patch.object(live,'run_summaries',return_value=rows),patch.object(live,'now_frame_data',return_value={'items':[]}):__import__('bt_remote_snapshot').snapshot(h,api._problem,api._send_json)
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
  assert runtime.liveness.status.value=='offline' and runtime.offline_generation==0 and rows==0
  runtime.outbox._db.close()

 values={'LAPTOP_ORIGIN':'http://127.0.0.1:1','FLOW_GATEWAY_KEY':'synthetic','TELEGRAM_BOT_TOKEN':'synthetic','TELEGRAM_CHAT_ID':'synthetic','GATEWAY_DATABASE':str(pathlib.Path(tmp)/'config.db'),'GITHUB_CLIENT_ID':'synthetic','GITHUB_CLIENT_SECRET':'synthetic','SESSION_SECRET':'synthetic-session-secret-at-least-32','FLOW_FRONTEND_ORIGIN':'https://frontend.test','GATEWAY_BIND':''}
 cfg=GatewayConfig.from_env(values);oauth=OAuthConfig.from_env(values)
 with patch('server.ThreadingHTTPServer') as factory:
  create_server(oauth,(cfg.bind_host,cfg.bind_port),runtime=None)
  address=factory.call_args.args[0]
 print('O accepted empty bind passed to HTTP server',repr(address),'default command timeout',cfg.request_timeout)
 assert address==('',8790) and cfg.request_timeout==5
 print('No wildcard listener was opened; constructor mocked.')
PY
```

Observed: /estado sends only its header for an actual projected active run; 20 slow synthetic sends advance
100 simulated seconds with one health probe; command/challenge offline transitions leave outage generation zero
and no alert after 901 seconds; empty bind reaches the mocked constructor as ('',8790), with timeout default 5.
No live Telegram request, real sleep or wildcard listener is used.


### Probes R/S/T/U/X — late events, redaction, restart semantics, notification predicates and malformed OAuth

```bash
python - <<'PY'
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

PY
```

Observed in att-0344 (historical; current observations are in the current verification section): the persisted observation cursor delivers late stall/round events; quoted synthetic credentials still survive both sanitizers. First-start history is sent, but a continuous outage now retains generation 1 and is not resent across restart. One exhausted account triggers despite another being available; a sequential flow/state failure still acquires two keys. Unicode state disconnects one callback. These are deterministic probes, not deployed incidence measurements.

### Probe I2 — truncated upstream success

```bash
python - <<'PY'
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

PY
```

Observed: the accepted response with two bytes and Content-Length 100 raises uncaught IncompleteRead in
GatewayRuntime.submit_command. Its business effect is deliberately absent; ambiguity, not duplicate execution, is proven.

### Probes AA/AB/AC/AD/AE/AF — fresh provider findings, independently reproduced

```bash
python - <<'PY'
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
 ev=feed.build_events(state);print('AB task finally exhausted failure alerts',len(ev));assert len(ev)==3
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
 print('AC fresh Bogota round interpreted as UTC',[(e['type'],e['occurredAt']) for e in events],rt.outbox.history(),sent)
 assert events[0]['type']=='round.waiting' and not sent and rt.outbox.history()[0]['outcome']=='dropped';rt.outbox._db.close()
 import bt_remote_recovery as recovery,bt_route_pins as pins
 from types import SimpleNamespace
 row=SimpleNamespace(route_id='synthetic-route',provider='codex',model='synthetic',profile='synthetic',account_ref='synthetic',profile_authorized=True,source_status='available',runtime_status='available',auth_status='valid',quota_status='unknown')
 with patch.object(recovery,'task_candidates',return_value=(None,(row,))):options=recovery.route_options('demo',base,'T1')
 with patch.object(pins,'candidates_for',return_value=(row,)):selected=pins.available('demo',base,'T1',{'route':'synthetic-route'})
 print('AD unknown-quota route listed available',options[0]['available'],'retry candidates',selected)
 assert options[0]['available'] is True and selected==[]
 import bt_server
 with patch.object(bt_server,'platform',return_value='linux'),patch.object(bt_server.subprocess,'run',side_effect=FileNotFoundError('synthetic missing systemctl')),patch.object(bt_server,'is_running',return_value=False),patch.object(bt_server.subprocess,'Popen') as popen:
  try:bt_server.ensure_server()
  except FileNotFoundError:print('AE systemd-less Linux ensure_server raises FileNotFoundError, detached starts',popen.call_count)
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
PY
```

### Probe AG — production read routing and challenge issuance

```bash
python - <<'PY'
import os,sys,pathlib,tempfile,threading,http.client,json
from http.server import ThreadingHTTPServer
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway')]
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp;os.environ['FLOW_GATEWAY_KEY']='synthetic-key-at-least-24-characters'
 import bt_server
 from app import GatewayRuntime
 from auth import OAuthConfig,OAuthService,SessionStore
 from config import GatewayConfig
 from server import make_handler
 class QuietServer(ThreadingHTTPServer):
  def __init__(self,*args):super().__init__(*args);self.errors=[]
  def handle_error(self,*args):self.errors.append(sys.exc_info()[0].__name__)
 laptop=QuietServer(('127.0.0.1',0),bt_server.RemoteHandler)
 lt=threading.Thread(target=laptop.serve_forever,daemon=True);lt.start()
 runtime=GatewayRuntime(GatewayConfig(f'http://127.0.0.1:{laptop.server_port}',os.environ['FLOW_GATEWAY_KEY'],'synthetic','synthetic',pathlib.Path(tmp)/'runtime.db'),sender=lambda _:None)
 store=SessionStore(str(pathlib.Path(tmp)/'auth.db'),'synthetic-session-secret-at-least-32')
 token=store.create_session('dav033');service=OAuthService(OAuthConfig('synthetic','synthetic','synthetic-session-secret-at-least-32','https://frontend.test',store.database_path),store)
 gateway=QuietServer(('127.0.0.1',0),make_handler(service,runtime));gt=threading.Thread(target=gateway.serve_forever,daemon=True);gt.start()
 try:
  paths=['snapshot','commands','history','quotas','routes?target=demo%2FREQ-001&task=T1','attempts/att-0001/review?target=demo%2FREQ-001','events']
  for path in paths:
   conn=http.client.HTTPConnection('127.0.0.1',gateway.server_port,timeout=3)
   conn.request('GET','/api/remote/v1/'+path,headers={'Cookie':'flow_session='+token})
   try:response=conn.getresponse();response.read()
   except http.client.RemoteDisconnected:print('AG production read disconnected',path)
   else:raise AssertionError('expected missing runtime.read_remote disconnect')
   conn.close()
  assert gateway.errors==['AttributeError']*len(paths),gateway.errors
  assert not hasattr(runtime,'read_remote')
  conn=http.client.HTTPConnection('127.0.0.1',laptop.server_port,timeout=3)
  conn.request('POST','/api/remote/v1/challenges',json.dumps({'target':'demo/REQ-001','typedReq':'REQ-001'}),{'Authorization':'Bearer '+os.environ['FLOW_GATEWAY_KEY'],'Content-Type':'application/json'})
  response=conn.getresponse();payload=json.loads(response.read());print('AG keyed laptop challenge',response.status,payload);assert response.status==404 and payload['code']=='NOT_FOUND';conn.close()
  conn=http.client.HTTPConnection('127.0.0.1',gateway.server_port,timeout=3)
  conn.request('POST','/api/remote/v1/challenges',json.dumps({'target':'demo/REQ-001','typedReq':'REQ-001'}),{'Cookie':'flow_session='+token,'Origin':'https://frontend.test','X-Flow-Request':'1','Content-Type':'application/json'})
  response=conn.getresponse();payload=json.loads(response.read());print('AG public challenge',response.status,payload);assert response.status==200 and payload['code']=='NOT_FOUND' and 'challengeId' not in payload;conn.close()
 finally:
  gateway.shutdown();gateway.server_close();gt.join();laptop.shutdown();laptop.server_close();lt.join();runtime.outbox._db.close()
PY
```

### Probe AH — exhausted real producer versus the event predicate

```bash
python - <<'PY'
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
 assert 'attempts_used' not in task and 'max_attempts' not in task
 events=feed.build_events({'runs':runs});print('AH real exhausted feed',events)
 assert not any(e['type']=='attempt.failed' for e in events)
PY
```

## Final artifact checks

Final run: all **20 documented Python reproduction blocks exit 0** and compile in memory. They assert observations,
including defects; they do not establish product acceptance. All three frozen `test -s remote/docs/audit.md`
invocations exit 0. Ledger checks: schema `audit-findings/1`, 67 unique IDs, valid frozen task references/status/
severity, evidence with commands and actual results for all 24 fixed findings, zero accepted risks, and exact
current report-heading/ledger verdict parity. Neither artifact has conflict markers. `git diff --check` and the
allowed-path/no-untracked assertion pass: changed files are exactly this report and ledger. Source, tests, config
and lockfiles match entry HEAD. No implementation behavior was discarded during reconciliation.

The all-high-fixed criterion remains unmet: **F2/F36/F63/F66/F67 are high/open**. The independent checker decides
the task outcome; this report does not declare verification or acceptance. The owning tasks must repair their
results before this read-only audit can find those issues fixed.
