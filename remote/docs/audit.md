# Independent security and specification audit — T18

**F72 is rechecked fixed in the new prerequisites; no confirmed critical/high finding remains open.**
Fresh wheel and sdist include the snapshot and scheduler-projection modules. Probe AM2 runs the real keyed HTTP
snapshot regression using only the installed implementation and passes. This audit changes only this report and
`remote/docs/audit.findings.json`. The independent checker decides the outcome; this is not a deployment approval.

Audited entry HEAD: `33e76ecc127ee3f10ebf22d09ba1b394996f6ade` (att-0430), 2026-10-21, America/Bogota.
Primary auditor: OpenAI Codex; a fresh Anthropic source review is adjudicated separately below.
Ledger: **77 findings: 31 rechecked fixed, 46 open (36 medium, 10 low), zero accepted**.
All inherited F1–F76 identities and responsible task IDs are retained; F77 records the newly confirmed Caddy
runbook mismatch. Open medium/low findings remain unresolved;
none is silently accepted, removed or attributed to an unspecified future auditor.

## Reconciliation and prior attempts

Opened both supplied documents before edits: **zero conflict markers**, valid ledger JSON and clean git status.
Their contents match the earlier T18 result `7641cfc1376a2aeebc7ed3d892349ccb8d612de5`. There was no textual merge
conflict to resolve. The semantic conflict was the inherited F72 conclusion against the new prerequisite repair.
The complete source delta from that result to entry HEAD is two `pyproject.toml` entries: `bt_remote_snapshot`
and `bt_scheduler_projection`. Both intents are retained: keep those packaging repairs and all established
snapshot/editor/review/alert behavior, and keep the audit findings with conclusions supported by current checks.
No product source, test, configuration, requirement or frozen verification was rewritten or deleted.

Read the supplied failure notes and reachable historical ledgers before final adjudication:

| Attempt / snapshot | Recorded blockers | Current disposition |
|---|---|---|
| #20 / d629327c9 | F2/F36/F63/F66/F67 | Fixed by current E2E, AG/AC/AH and production build. |
| #21 / fe4ba03b1 and #22 / 8bf81c180 | Previous five plus F41/F42 | Fixed; current E2 also proves field aliases and safe publication. |
| #23 / 1d43a322a | F2/F19/F62 | Fixed by current production build, real scoped review and E2E. |
| #24 / c937870c6 | User gate says same as #23; saved ledger opens F41/F42/F72 | Historical discrepancy retained explicitly; current evidence overrides neither receipt retroactively. All three are now fixed. |
| #25 / 7641cfc13 (att-0428) | F72 only | AM2 proves the new installed snapshot works, including its projection dependency. |

Raw m6 receipts and omitted attempts were not provided as worktree artifacts; no external retrieval is claimed.
Earlier source-tree checks hid the omitted module. This attempt checks both distribution membership and an actual
installed HTTP snapshot, including active task, review history, criteria, shared cache and all imported bt_ modules.
The T8a approved-base editor repair also remains exercised by E2/AL2/AQ and 12 recovery tests. Medium F70 remains a
post-publication I/O reconciliation gap; it does not authorize deleting published history or undoing the safe-base repair.

## Current commands and limits

Read complete checked-in SPEC R1–R18, clarifications, PLAN.md/PLAN.json revision 3, all task objectives/acceptance/
verification instructions and the owner amendment. The scheduler's r9 directory name does not amend that contract.
Every unique prerequisite verification command ran. Identical commands shared by several criteria ran once;
the three T18 artifact commands run separately after writing. T19 is a successor, outside this task's acceptance.

Dependencies: `cd remote/web && npm ci --offline` exits 0 (320 packages; lockfile unchanged).
`UV_PROJECT_ENVIRONMENT=bitacora/.state/audit-att0430/python-env uv sync --offline --frozen --no-install-project`
exits 0 (no Python runtime dependencies). Python suites use 3.14.7; Node is v24.21.0. uv selects 3.13.15.
Tests use installed dependencies directly and do not install or write into node_modules.

All state/credentials are synthetic. Scratch files are inside this worktree; Chromium uses a short
`/proc/<audit-process>/fd/<directory-fd>` TMPDIR alias to an internal directory to satisfy Unix socket path limits.
No production service, external deployment, live account action, credential file, paid scheduler/agent execution,
other worktree, remote branch or owner bitácora document was touched. The independent reviewer receives tracked
source/specification and fixture literals only, with tools disabled.

| Command | Exit | Current observed result |
|---|---:|---|
| `test -s remote/docs/route-pin.md` | 0 | Nonempty artifact; 0.004 s wall. |
| `python -m json.tool remote/contract/command.schema.json` | 0 | JSON syntax only; semantic mismatch F17 remains; 0.064 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py` | 0 | 6 tests in 8.213 s; 8.531 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py` | 0 | 25 tests in 1.799 s; 2.369 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py` | 0 | 16 tests in 0.240 s; 0.966 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py` | 5 | 0 tests in 0.000 s; NO TESTS RAN (F69); 0.114 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py` | 0 | 12 tests in 0.948 s; 1.517 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` | 0 | 28 tests in 2.002 s; 2.619 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py` | 0 | 5 tests in 11.041 s; 11.287 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_auth.py` | 0 | 3 tests in 3.520 s; 3.722 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_guard.py` | 0 | 7 tests in 3.796 s; 4.023 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_stream.py` | 0 | 14 tests in 3.287 s; 3.521 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py` | 0 | 13 tests in 5.818 s; 6.026 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` | 0 | 3 tests in 0.060 s; 0.265 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_send.py` | 0 | 3 tests in 0.018 s; 0.164 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_bot.py` | 0 | 4 tests in 0.053 s; 0.214 s wall. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | 0 | 14 tests in 7.167 s; 13 pass, one missing-Caddy skip; 7.329 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p "test_page*.py"` | 0 | 43 tests in 11.453 s; 12.189 s wall. |
| `cd skill/scripts/bt_scheduler_core && python -m unittest discover -s tests -p test_operations.py` | 0 | 18 tests in 0.758 s; 0.966 s wall. |
| `python -m unittest discover -s tests/migration -p test_package_install.py` | 1 | 21 tests in 13.181 s; 19 pass, two path-assumption failures under required internal scratch (see below); 13.490 s wall. |
| `cd remote/web && npm run verify` | 1 | Lint/typecheck pass; 14/15 tests pass, zero skips; 366 !== 360 at panel-browser.test.mjs:165 (F18); build not reached; 21.256 s wall. |
| `cd remote/web && npm run build` | 0 | Production build succeeds; / and /review emitted; 16.301 s wall. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | 0 | 1 tests in 21.918 s; 22.108 s wall. |

Frozen/regression Python suites: **215 tests, 214 pass and one Caddy skip**, plus the separate missing review-test
command (zero tests, exit 5). Web verification remains exit 1 for F18; separate production build and the frozen
loopback E2E pass. E2E asserts owner OAuth/foreign refusal, authenticated snapshot, real cancellation and stale
rejection, exactly one terminal-failure notification and offline within 20 s. Its build succeeds too.
AM2 separately passes one real snapshot regression in an isolated installed runtime.

Additional packaging suite: `python -m unittest discover -s tests/migration -p test_package_install.py` runs
21 tests, 19 pass and two fail. `test_no_module_resolves_from_the_checkout` forbids the repository path anywhere
in resolved installed paths, but this task requires temporary installs inside the repository.
`test_context_names_policy_files_inside_the_installed_package` compares resolved resource paths with a lexical
/proc alias. These are explicitly **not passing evidence**; no tests or assertions were altered. AM2 instead
asserts canonical membership in the installed site for every loaded bt_ implementation, and runs actual HTTP.
A packaging-suite run with scratch outside the allowed worktree was not attempted.

An initial accidental overlap between deploy-kit's nested OAuth browser test and the web commands interfered
with their shared .next output: kit/browser startup and a production build failed. Re-ran kit, verify and build
strictly in sequence: kit passes, verify reproduces only F18, build passes. Those initial failures are disclosed
and are not product findings. Source assertions/CSS were unchanged; SQLite fixture ResourceWarnings remain visible.

Ran all **30 inherited reproduction blocks**: 29 exit 0; old AM exits 1 at its obsolete assertion that the sdist
omits bt_remote_snapshot.py. Replaced that defect assertion with AM2 and executed it (exit 0, 5.144 s).
Those 30 retained report blocks and new AR (31 total) have current successful execution evidence. AR independently
rejects fresh-decision expiry on the real producer and confirms the low Caddy runbook mismatch F77. Success means each block's
explicit repair/defect assertion holds, not that the whole product satisfies every requirement.
All final evidence and runnable probes are in these documents; ignored logs under
`bitacora/.state/audit-att0430/` are supplementary, not required by a clean copy.

Not run: Python 3.12 (unavailable), Caddy executable/container connectivity (one skip), live deployed
OAuth/Telegram/Vercel/SSE, paid selected-route execution, physical-phone installation, exhaustive 44 px target
measurements, online dependency-advisory scanning, or multiprocess/local-writer stress. The rewrite spike is prior
evidence only. No live deployment or complete end-to-end recovery approval is inferred.

## Fresh independent provider review

Invocation, with tools disabled:
`claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
Provider: Anthropic. CLI modelUsage reports `claude-sonnet-5-5` (requested alias: sonnet).
Packet: **38 tracked files, 396,318 UTF-8 bytes**, including complete SPEC/PLAN/amendment, every gateway production
module, native remote API/snapshot/commands/editor/events/recovery/views/pins, phone entrypoint/recovery/both review
callers/CSS, Next config, E2E, pyproject, architecture/contract/schema and deployment scripts/runbook.
No earlier report, ledger, primary verdict, secret file or previous receipt was supplied. The prompt identifies the
two packaging additions and asks for a fresh full-scope review. No tool or execution result is claimed by this provider.

Receipt: **exit 0**, subtype success, is_error=false, num_turns=1, terminal_reason=completed;
duration_api_ms=348475, duration_ms=348667; **350.019 s wall**.
Input SHA-256: `41469f7b78a405ae1ca0aff578e42ea15dc64fa5a097574147c5fd37b308e02e`.
Output JSON SHA-256: `f38a2b330c73f44cdae248fe295b43fbf88cb4873dca8167df38b4352571ca3e`.
Its omitted implementation closure (server/listener, plan/round/operation/decision APIs, scheduler/prompt pin
consumers, subscription summary, assets/layout/manifest and deploy units/Caddy/tests) is covered by primary source
inspection and current suites/probes. It is not assumed covered by another auditor. Live go-live remains untested.

Provider-local F numbers below are **not ledger IDs**. Every item and conditional claim is adjudicated:

| Provider item | Current verdict and evidence |
|---|---|
| F1 SSE, high | Confirm ledger F21 at medium: AG proves wrong route; source proves named-event/onmessage and cursor mismatch. Snapshot polling still works in E2E, bounding severity. Up to ~10 s staleness is an inference; no new measured timing finding. T17's missing stream scenario does not itself repair the T12/T15b boundary. |
| F2 Telegram content, high | Confirm F6 at medium: AI/B and source prove missing link/cause/buttons/retry; E2E proves failure notification delivery. Missing required content/actions remains unresolved, but total alert loss is not reproduced. |
| F3 old event/decision expiry | Existing old events expire intentionally after 1 h (N/F43), as the frozen edge case requires. AP proves command timestamps are epoch (F76), but command.updated is not notifying. **Reject fresh-decision expiry claim on the tested producer**: AR uses a real newly blocked M1 task and two-hour-old PLAN.md; actual plans_payload uses the current projection heartbeat, and the alert is sent. No fresh producer with stale plan timestamp demonstrated. F63 fresh-round repair still passes. |
| F4 retrospective alerts | Confirm F37 at medium by AB: a three-failure history yields three failure events at final exhaustion. Same-event SQLite dedupe does not collapse distinct producer identities. |
| F5 shared login throttle | Confirm F47 at medium by L: six forwarded clients hit the same peer bucket. Do not accept arbitrary forwarded headers as a repair. F27 separately records login-scoped command throttling. |
| F6 OAuth request logs | Confirm F4 at medium by A and actual logger source: args[0] contains the request line/query, not HTTP status. No live credential or account takeover demonstrated. |
| F7 secret text shapes | Confirm F56 at medium by S: quoted JSON and database URL text survive redaction. F14 plain-assignment/bearer repair remains fixed. No actual live secret read. |
| F8 note/prompt | Confirm standalone note failure F7 via B. **Bound the broader claim**: retry reasons use existing RUN.notes, and bt_scheduler_executor_wiring reads operator_notes. Standalone note failure does not prove all note/prompt injection paths absent. |
| F9 schema drift | Confirm F17 at low by B/schema/source. JSON syntax alone does not check command families, key sizes or response dialect. Actual command paths pass the ledger/relay/E2E tests, bounding impact. |
| F10 phone controls/offline | Confirm F46/F9/F16/F13 by current form source, C/AG/AK and I. Real task-scoped reopen works; run-level form is defective. UNKNOWN_OUTCOME same-key safety on the server does not repair lost client envelopes. |
| F11 delivery/poll/deadline | Confirm F51 via Y and F52 via default config/source (medium and low respectively). ~100 s is a calculated upper bound, not a real outage measurement. A separate production SQLite-lock crash or false-timeout execution timeline was not reproduced; no additional confirmed high. |
| F12 snapshot restart | Confirm memory-only cache F11 by B. Persisted-outage/hub-online subclaim does not prove a false online snapshot on restart: without a snapshot the hub returns unavailable. No new independently confirmed presentation defect beyond F11/F13. |
| F13 half-applied edits/pins | Confirm medium F70 by AL2, preserving the approved-base F42 repair. Conditional pin persistence on later I/O failure is not a reproduced production failure here. **Reject absent pin consumer inference**: scheduler adapter uses bt_route_pins.get/narrow, and C persists the selected route/model/account through real native dispatch (process start/availability stubbed). |
| F14 config/marker/identity/targets | Confirm low F48 and medium F5 by filled-config/source/A. Numeric GitHub ID binding is extra hardening outside the frozen login requirement. AN and real req_dir/project_dir reject path escape; absence of gateway charset validation does not establish arbitrary path writes. |
| F15 smaller drifts | Confirm F30/F58/F75/F76/F12/F71/F68 with B/U/AP/N/AJ/source; severities remain as ledgered. No current producer generates a problematic digit-bearing roundId: C exercises real numeric rounds. No new round-misrouting defect confirmed. |
| F16 go-live drift | Confirm fresh-install ordering F3 by J; production origin fallback F74 by AO. **New low F77**: AR/source prove Step 5 and rollback prescribe host systemctl reload for the documented Docker Caddy. Actual unit/env/runbook paths agree within the kit; the frozen PLAN uses older names. No deployed host state assumed. |
| C1 gateway authority/action-bound challenge | Gateway-key authority is an explicit trust decision (R3/R5/R8), not a new demonstrated exploit. Target/expiry/one-use challenge checks pass; action/signature binding is not a frozen requirement. |
| C2 stale tunnel | Conditional live migration risk only. Checked unit explicitly forwards AdvIn 18765 to laptop remote-only 8766; kit/API/platform/E2E checks pass. No deployed stale forward inspected. |
| C3 multiprocess ledger | D and current ledger tests establish process-local guarantees only. No actual multiprocess different-key race or same-key IntegrityError reproduced; report the stress-test limit without inventing a new high finding. |
| C4 target paths | AN and real path resolver reject '..'; review paths have scoped IDs and bounded regular-file reads. No arbitrary write demonstrated. |
| C5 implicit resume | The dispatch and existing ops intentionally apply/resume operator moves. A paused-run cancellation preserving a prior hold is not specified by this frozen contract; no distinct acceptance violation is established from source alone. No paid dispatch used to resolve the hypothetical. |
| C6 terminal producer facts | AH and E2E use the actual M1 producer and show attempts_used=max_attempts=1, retries_remaining=0, one terminal event and one alert. F67 is rechecked fixed; missing-facts hypothesis is rejected for that path. Multi-retry behavior remains F37. |
| C7 replay backlog | Confirm existing medium F57 by AF: fresh round first queues on poll 16 (75 s at configured 5 s cadence). Stable same-key dedupe passes N/T. |
| C8 connection/heavy-read exhaustion | Conditional resource risk, no valid slowloris or per-read quota-stress failure reproduced. No blanket availability guarantee is inferred. |
| C9 Telegram group sender | Configured owner chat_id is the frozen requirement; group-member binding is additional hardening. Existing message/callback allowlist checks and bot tests pass. |
| C10 rewrite/OAuth state | Local real-browser OAuth and E2E pass; deployed 120 s SSE remains untested. Confirm low F60 for non-ASCII state request-thread TypeError by X. No OAuth authentication bypass follows. |
| Packaging section | Provider confirms the two list additions statically and correctly withholds installed-behavior claims. AM2 supplies current fresh wheel/sdist + isolated installed actual HTTP snapshot; API suite covers installed health/events/history/quotas. Real C/AG/E2E cover checkout review/challenge/commands. No complete installed/deployed consumer matrix is claimed. |
| Process/verification section | Agree: nonempty-file and JSON-syntax commands are weak evidence. This task's explicit read-only ledger contract routes confirmed high defects back to owners; it does not authorize source edits. Full R1–R18 scope was audited regardless of T18's shorter covers array. Frozen verification was retained and its failures disclosed. |

Provider rejection list is supported within inspected/tested boundaries: parameterized SQL, constant-time nonempty
gateway key, one-use cookie-bound OAuth state, hashed random session tokens, fixed frontend redirects, process-local
same-key at-most-once/challenge consumption, guarded POST Origin/custom header/cookie, React text escaping,
scoped O_NOFOLLOW review reads, no Telegram token in exception-type logs, authenticated reads/SSE, fixed rewrite
host and configured Telegram chat allowlist. These are bounded conclusions; F5/F31/F56/F60 remain open.

## Previous provider hypotheses, independently rechecked

The following hypotheses came from the earlier att-0428 Anthropic review recorded in the inherited report
(reported model claude-sonnet-5-5). They are retained as historical hypotheses, not a new invocation receipt.
Every confirmed item was rechecked against this tree with the probes and suites above. The new packaging repair
supersedes that provider's original F72 conclusion. Other provider claims remain bounded to actual evidence.

| Provider item | Primary verdict, evidence and rationale |
|---|---|
| 1 installed snapshot, high | **Now fixed F72** by AM2 fresh wheel/sdist and isolated installed real HTTP snapshot. Source-tree E2E alone was insufficient; new prerequisites repair both snapshot and projection packaging. |
| 2 SSE/live, high | Confirm F21 at **medium** by AG/source: wrong URL, named-event/onmessage mismatch, incompatible cursors. Polling still updates runs/tasks and passes E2E, bounding impact. Feed remains unavailable. Two-loop ~10 s worst case is an inference, not a measured new finding. |
| 3 Telegram content/buttons, high | Confirm F6 at **medium** by B/AI/E2E: required alerts are delivered, but lack context/link/buttons and retry callback. This is missing content/control, not demonstrated total alert loss. |
| 4 synchronous delivery | Confirm F51 by Y/source. The 20×5 s upper bound is arithmetic; no real Telegram outage latency measured. |
| 5 proxy throttle/client logs | Confirm F47 by L, with six forwarded clients sharing the actual peer bucket. Logged client is also peer address; not a new exposure. Do not trust arbitrary forwarded headers. |
| 6 thresholds/quota/decision/dedupe | Confirm F30/F58 by B/U, F59 by U and retrospective F37 by AB. **New F75**, medium, by AP: real blocked-task decision is mislabeled as plan approval waiting. F10's actual-plan notification repair remains fixed. |
| 7 timestamps | **New F76**, low, by AP: real ledger received_at becomes epoch command.updated because build_events reads created_at. This event is not notifying, so claimed Telegram expiry consequence is unconfirmed. No actual numeric-quota producer was demonstrated; fresh round UTC repair F63 remains fixed. |
| 8 cache/offline/retention/public drops | Confirm F11/F13/F12/F71 by B/AK/N/source. Ten-attempt backoff can terminate before the one-hour maximum; the frozen phrase “up to 1 h” does not independently establish a minimum retry duration, so no new confirmed finding for that inference. F43's bounded expiry/backoff/history remains fixed. |
| 9 controls/round IDs/error text | Confirm F46/F9 by current forms/target-state source and C/AG. No current producer was shown generating the hypothetical r2-2026 roundId; real numeric round answers pass C. Generic command-error display is observed, but no separate frozen requirement for echoing native exception text was established; raw-error boundary remains low F68. |
| 10 recovery/note/criteria/pins | Confirm F7/F8/F64 by B/AQ/AD. C and 12 recovery tests prove actual task reopen, pinned retry and persisted route/model/account; assignment wiring invokes pins.narrow. Retry notes use existing RUN.notes; standalone note failure does not prove every note path fails. |
| 11a stale compatibility | **Reject demonstrated-bypass claim**: adapter report checks schema capabilities; allowed objective/criteria edits do not change schema. publishable_problem runs full Planner.check on the written candidate; E2 invalid criteria and AQ repeated-title rejection exercise it. No unsupported candidate escaped publication. |
| 11b publication/locking | Confirm medium F70 by AL2, no compatibility stub: authorized r2 persists on later rebase I/O failure; follow-up fails PLAN_BASE_STALE. ops.apply's member target defaults to an empty string; revise is run-scoped. Shared local-writer locking remains untested, not a new proved race. F42 prepublication approved-base/rollback repair passes E2. |
| 11c title overwrite | AQ confirms incorrect title prefill under **F8**, but **rejects silent overwrite**: first short-title probe hits minimum-length validation; a valid five-word title hits repeats-the-title validation. Both leave approved/bound r1 and original bytes. No corrupted approved r2. |
| 12 revision pin/action-bound challenge/status | Action binding is not required by frozen R8; target/expiry/one-use checks pass AG/commands. R6 requires an expected target state; it does not specify a content-hash approval pin. No valid same-revision bypass or actual unsupported lifecycle producer was reproduced. No new confirmed finding. |
| 13 timeout/in-flight/key/lock | Confirm F52 (low) and F16/F40 by defaults/source/I/I2. No valid late-effect timeline or multiprocess/hung-effect exploit reproduced. At-most-once process-local serialization is intentional and tested D. UNKNOWN_OUTCOME does not prove an effect did not execute. |
| 14 contract/raw errors | Confirm F17 (low) by schema/source, and F68 (low) by AJ fault injection. JSON syntax command alone is not semantic validation. Actual public history omits injected raw error. No built-in live-secret leak was demonstrated. |
| 15 origin variable/fallback | Confirm low F74 by AO. PLAN's old variable name differs from current config/runbook; current filled config/build/E2E work. No live misconfigured deployment inspected; T19 is a successor. |
| 16 separate listener/trust path | No new security defect: architecture deliberately retains the existing reverse SSH service as sole transport, retargeted to remote-only 8766. Frozen API/platform/kit/E2E and source confirm separate handler, loopback and panel regressions. No unseen AdvIn dependency or deployed stale unit is alleged. |
| 17 malformed record breaks parser | No valid production decision/round causing this was reproduced. Fail-closed schema parsing is observed; it is not itself proof of a frozen per-record isolation requirement. No blanket robustness guarantee. |
| 18 Unicode/header | Confirm low F60 by X and medium F5 by A. No authentication bypass follows. |
| 18 mutable login/chat binding | Frozen owner login dav033/configured chat_id are explicit requirements. Numeric-ID/group-member binding is additional hardening, not a confirmed scope violation. |
| 18 dataclass repr/http origin/default ledger | Sensitive repr fields and permissive http configuration are observed; no production logging or public cleartext topology demonstrated. Actual configured upstream is loopback reverse tunnel. Default ledger-root divergence is conditional on unseen installation env; no split-store failure reproduced. Do not read live env files to fill these gaps. |
| 18 project/liveness threading | Reject arbitrary write claim: req_dir/project_dir validates paths, AN refuses '..'. Confirm F53 by Z for the real Telegram-induced transition bookkeeping gap; no new concurrent-memory race reproduced. |

Independent rejection corrections: “request logs use path only” is false because the logging status argument contains
the full request line (A/F4). Strict cookies limit cross-site logout forgery, but do not satisfy the frozen guard on
all state-changing routes (F5); no command CSRF bypass is claimed. Same-key restart dedupe passes N/T, while U/AB
show distinct producer keys can still duplicate alerts. Other provider rejections (OAuth replay, key timing,
challenge replay, scoped SQL/file reads, plain Telegram/React text, callback allow-list and configured redirects)
are bounded to the inspected paths and passing tests. No provider statement is accepted on trust.

## Rejected or bounded hypotheses

| Hypothesis | Verdict and reason |
|---|---|
| F2/F19/F62 still block on this tree | Rejected by fresh production build, matching target props/callers, AG real scoped review and passing E2E. Supplied old gate receipts are not current execution. |
| Phone aliases still fail or unapproved working drift is frozen by an edit | Rejected by E2 and 12 recovery tests. F41/F42 are fixed. F70 only concerns failure after an authorized revision is published. |
| Every edit failure rolls back an already published revision | Rejected: AL2 leaves approved r2 ahead of bound r1 after injected rebase I/O failure. Subsequent edit fails PLAN_BASE_STALE; no unapproved run is claimed. |
| Snapshot is nested, frozen criteria absent, or offline is always labeled EN VIVO | Rejected by C/AG/AK against the exact parser. Missing offline-start/activity fields remain F13/F29. |
| Importing bt_remote_api proves installed snapshots work | A bare import remains insufficient; AM2 now invokes real installed HTTP and passes. The old missing-module conclusion is superseded; F72 is fixed. |
| Foreign-Origin command execution follows from wrong marker/GET logout | Not reproduced: foreign/missing-Origin POST guards pass. F5 is bounded to exact-header mismatch and state-changing GET logout. |
| OAuth replay or a foreign GitHub user obtains a session | Rejected in tested paths by auth/E2E one-use state binding and foreign-user refusal. Non-ASCII state disconnect remains F60. |
| Scoped review IDs collide across runs or traverse arbitrary files | Rejected in tested paths by AA and source: target validation, scoped attempt resolution, bounded regular-file/O_NOFOLLOW reads. |
| Textual target syntax alone permits arbitrary-path writes | Rejected: real req_dir/project_dir rejects leading-dot projects and outside-root paths; AN tests project '..'. |
| Same-key replay or tested different-key simultaneous actions duplicate an effect | Rejected by ledger tests/D within one process. Multiprocess/local-writer guarantees were not tested. |
| Offline commands are deliberately queued | Rejected by liveness/relay/E2E immediate rejection; no deferred queue found. Ambiguous in-flight results remain F16/F40. |
| Missing headers, absent socket caps or username/chat-ID auth prove a new exploit | Not demonstrated. Strict cookies/Origin checks, typed target and configured owner are explicit frozen controls; no socket exhaustion or authenticated cross-site action reproduced. Numeric ID/group-sender binding is not in the agreed contract. |
| Challenge must bind to an action as well as a REQ | Rejected as a spec violation: R8 requires target binding, expiry and one use. Action binding is not required. |
| Telegram/React text content executes HTML, or callback data executes arbitrary commands | Rejected in inspected paths: plain text rendering and strict owner-chat/callback allow-list. No general sanitization guarantee beyond the tested F14 repair; F56 remains. |
| Current unit necessarily breaks flat gateway imports | Rejected: systemd uses absolute main.py plus its WorkingDirectory, not isolated/zipapp import execution. No deployed stale unit was inspected. |
| Same-key notification restart dedupe proves all producers dedupe | Rejected by U/AB: flow/projection duplicates and retrospective historical failure alerts persist F59/F37. |
| Malformed data or generic local-writer races establish additional high findings | No valid producer/global isolation failure, cross-process race, slowloris, or late-effect timeline was demonstrated. This is a bounded nonconfirmation, not robustness approval. |

## Findings and verdicts

Each item is independently adjudicated. Fixed means rechecked already fixed in this tree, not repaired by this
audit. Evidence is bounded as stated; probe letters refer to the complete executable commands below.

### F1 — high / fixed — The private Caddy bridge upstream and gateway bind match the container-to-host topology.

Tasks: T16. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. B exits 0 with all example keys filled synthetically, bind 172.20.0.1. The frozen deploy-kit command exits 0: 14 tests, one Caddy skip. No deployed connectivity claim.

### F2 — high / fixed — The frozen built-web loopback end-to-end scenarios now execute and pass.

Tasks: T17. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` exits 0: 1 test in 21.918 s, 22.108 s wall. Production build, owner OAuth/foreign-login refusal, real keyed cancellation/stale rejection, exactly one terminal-failure alert, authenticated snapshot and offline within 20 s are asserted. AH independently confirms real max-attempts=1 producer exhaustion facts. No multi-retry or deployed scenario is implied.

### F3 — medium / open — The runbook still deploys and restarts before installing the service on a fresh host.

Tasks: T16. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. J exits 0 using fake systemctl and mode-600 synthetic env: missing unit makes deploy exit 5 after switching current; deploy --dry-run exits 0, rollback --dry-run exits 2 without previous release. No host service touched.

### F4 — medium / open — Gateway request logs expose OAuth code/state query values in the status field.

Tasks: T11a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. A exits 0: a real synthetic callback query appears in captured logging. server.py log_message uses the full request line in args[0] as status. No live credential or account takeover was demonstrated.

### F5 — medium / open — Any nonempty mutation marker is accepted, and foreign-Origin GET logout bypasses mutation guards.

Tasks: T11a, T15a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. A exits 0 with a relay_command tuple fixture matching the current adapter: wrong X-Flow-Request gets HTTP 200; foreign-Origin GET logout gets 302 and revokes the session. Real POST foreign-Origin guards pass the 7-test guard suite. No command CSRF bypass alleged.

### F6 — medium / open — Failure alerts lack a review link, cause and safe inline actions; Telegram retry is unsupported.

Tasks: T14a, T14b. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AI/B exit 0: notification_for_event now returns only generic text plus REQ; the previously added relative review URL was removed. TelegramSender sends only chat_id/text, with no reply_markup. submit_telegram_command rejects retry with INVALID_COMMAND. Preserve run-scoped event IDs while restoring context and actions.

### F7 — medium / open — The public standalone note command has no laptop dispatcher.

Tasks: T5a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. B exits 0: actual Ledger.submit(note) with commands.dispatch_handlers returns COMMAND_NOT_IMPLEMENTED. Retry reason/RUN.notes is a separate path.

### F8 — medium / open — The phone brief form lacks criteria editing and prefills the task title instead of its objective.

Tasks: T15f. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Static page.tsx trace: one brief textarea submits field=objective and a string, with no criteria editor. The repaired native editor now accepts objective/criteria/acceptance_criteria (E2 exits 0); that does not add a criteria input to the phone UI. AQ exits 0 using a real approved task and native snapshot: objective is absent from the phone task model, textarea defaultValue is task.title, and submission targets objective. The real publication validator rejects the title-only objective and restores original bytes, so the provider's claimed silent overwrite is rejected; approved/bound revision stays r1.

### F9 — medium / open — Run-level reopen supplies no identity to the task-scoped operation.

Tasks: T15d. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. page.tsx commandForm(reopen) omits taskId, while TASK_SCOPED/_member_state and dispatch_run_command require params.task. C exits 0 for a task-scoped reopen; that does not repair the run-level form.

### F10 — medium / fixed — A plan awaiting approval emits plan.waiting without a scheduler decision.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. B exits 0: plan_status=review produces plan.waiting. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py` exits 0: 16 tests.

### F11 — medium / open — Gateway restart loses the last snapshot despite production stream-hub wiring.

Tasks: T12. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. B exits 0: old generatedAt remains offline in one runtime, but a replacement runtime using the same SQLite database returns None. StreamHub snapshot and runtime.snapshot_cache remain memory-only.

### F12 — medium / open — Expired sessions and command/Telegram history are not pruned after 90 days.

Tasks: T11, T14a, T5, T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. B exits 0: creating another session leaves an abandoned expired row. Static auth.py, notifications.py and Ledger.rows/history inspection finds no 90-day command/outbox/telegram_history prune. Timestamped delivery history is present and retained. bt_remote_events._observe also creates/inserts observed_events without retention or DELETE; this expands the recorded retention gap, not the repaired cursor semantics.

### F13 — medium / open — The phone recognizes offline state but still has no offline-start time.

Tasks: T12, T15b. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AK exits 0: actual public snapshot has root online=false AND laptop.online=false; the exact phone parser recognizes it. The previous EN VIVO subclaim is withdrawn. No offline-start/checkedAt timestamp is supplied or displayed as sin conexion desde HH:MM. B confirms the retained generatedAt cache is separate.

### F14 — medium / fixed — Laptop redaction handles plain provider assignments and bearer authorization text.

Tasks: T7, T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. B exits 0: synthetic OPENAI_API_KEY assignment and Authorization: Bearer text are redacted. JSON-quoted strings and database URLs remain the separate F56. The absent test_remote_review.py is not passing evidence.

### F15 — medium / fixed — Local-panel inherited systemd listener activation and reload remain implemented.

Tasks: T9. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` exits 0: 28 tests. `cd skill/scripts && python -m unittest discover -s tests -p "test_page*.py"` exits 0: 43 tests. These cover ownership, inherited socket and local-panel regressions without touching host services.

### F16 — medium / open — The phone discards uncertain command envelopes and generates a new key on resubmission.

Tasks: T15d. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Static submitControl/commandForm trace: UNKNOWN_OUTCOME HTTP 503 is labeled Rechazado, history retains summaries rather than a replayable exact envelope, and form submitters call crypto.randomUUID again. Same-key server at-most-once is preserved; no specific duplicate effect sequence demonstrated.

### F17 — low / open — The published command schema differs from production command families, fields and key limits.

Tasks: T3. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. JSON syntax command exits 0 only. command.schema.json omits answer-decision, expects singular answer/route text/edit brief, while phone sends answers/round, route object, field/value. B rejects a 121-character ledger key although schema permits 128. contract.md review/status dialects remain incomplete.

### F18 — medium / open — The mobile browser test measures 366 px on a 360 px viewport.

Tasks: T15. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd remote/web && npm run verify` exits 1: lint and typecheck pass, 14/15 tests pass, zero skips; panel-browser.test.mjs:165 fails 366 !== 360. Wall 21.256 s. The verify chain does not reach build; a separate npm run build exits 0. Assertions and CSS were not changed.

### F19 — high / fixed — FailureReviewPanel again accepts the run target and the integrated web typechecks and builds.

Tasks: T15c. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd remote/web && npm run verify` completes lint/typecheck before the unrelated F18 browser failure. `cd remote/web && npm run build` exits 0, 16.301 s wall, emitting / and /review. The frozen E2E also builds successfully. FailureReviewPanel now declares target:string and the call site supplies it.

### F20 — high / fixed — The phone accepts the actual gateway login-session response.

Tasks: T15a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. A exits 0: authenticated GET /api/auth/session returns 200 {login:dav033}. Frozen auth command exits 0: 3 tests. E2E exits 0 and checks the actual same-origin session. Browser session assertion also passes before F18.

### F21 — medium / open — Production SSE routing and event dialect still disagree with the phone.

Tasks: T12, T6, T15b. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AG exits 0: public events and phone events/stream return 404; explicit /api/remote/v1/stream serves named event/resync frames and epoch:sequence IDs. page.tsx requests events/stream?after=<snapshot cursor> and handles onmessage. Polling fallback remains, bounding impact. Static page.tsx poll success never clears setError; the dead SSE sets a banner that remains during successful polling until another action clears it. This additional presentation symptom is retained under the same broken live-feed finding.

### F22 — medium / fixed — A completely filled example configuration parses successfully.

Tasks: T16. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. B exits 0: every example key filled with synthetic values parses in GatewayConfig and OAuthConfig. Frozen deploy-kit command exits 0: 14 tests, one missing-Caddy skip. Optional empty bind remains F54.

### F23 — medium / fixed — Native keyed command history is exposed through the authenticated gateway.

Tasks: T4a, T15d. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. C and AG exit 0: commands/history return HTTP 200 with commands/nextCursor; AJ confirms public history omits injected exception text. Frozen remote-command command exits 0: 25 tests. Actual E2E cancellation succeeds.

### F24 — high / fixed — Wheel and sdist contain the edit and route-pin implementation modules.

Tasks: T8, T8a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. P exits 0: fresh wheel and sdist contain bt_remote_edit.py/bt_route_pins.py; isolated imports of bt_remote_api, bt_remote_commands, bt_remote_edit and bt_route_pins exit 0. AM2 additionally confirms snapshot/projection modules in both artifacts and the installed snapshot endpoint, repairing F72.

### F25 — medium / fixed — The selected failed-attempt review now forwards its run target.

Tasks: T15c. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. C and AG exit 0. Both failure-review-panel.tsx and review/page.tsx fetch review?target=<encoded project/REQ>; panel effect depends on attemptId and target. Actual authenticated att-0001 review for demo/REQ-001 returns 200 with all four sections. Target-less negative control returns 400 INVALID_TARGET. Browser selected-attempt/fixture assertions pass before F18; production build exits 0.

### F26 — medium / open — Ready recovery controls disappear after reload or in another tab.

Tasks: T15f, T15d. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. C exits 0: actual reopen projects ready and pinned retry succeeds with process-start/route-availability seams. page.tsx still gates forms on recovering/reopenedForRecovery with reopenedTasks in a useRef. A new tab cannot recover that in-memory marker.

### F27 — low / open — Command rate limits are shared by login across sessions.

Tasks: T11a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. server.py uses authenticated login as commands/challenges bucket. Frozen guard suite exits 0: 7 tests. This is stricter than per-session R17, not an auth bypass; proxy-shared anonymous login exhaustion is F47.

### F28 — high / fixed — Different-key concurrent preconditions serialize with the ledger effect.

Tasks: T5. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. D exits 0: two concurrent running-to-paused requests with distinct keys produce exactly one handler effect and one STALE_PRECONDITION, with two ledger rows. This proves process-local serialization only; multiprocess local writers were not exercised.

### F29 — medium / open — Snapshot activity timestamps still do not match phone fields; frozen task criteria are repaired.

Tasks: T4a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. C exits 0: bound T1 acceptance_criteria equals projected acceptanceCriteria, so the missing-criteria subclaim is withdrawn. build_snapshot still emits lastActivityAt and live._attempt last_activity_at, while parseSnapshot consumes lastSeenAt and attempt.updatedAt/updated_at; task timestamps are absent in run.tasks. The UI falls back to run.updatedAt or no task activity time.

### F30 — medium / open — Stalled-attempt alerts start after 15 minutes rather than more than 10 minutes.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. B exits 0: at 660 seconds no event; at 901 seconds attempt.stalled. The frozen R10 threshold is greater than 10 minutes.

### F31 — low / open — An authenticated SSE connection continues after session revocation.

Tasks: T11, T12. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AG exits 0: open /stream, revoke session through SessionStore.delete_session, then publish synthetic.after.logout; the existing connection receives the named frame. Fresh requests are authenticated; stream is read-only, so severity remains low.

### F32 — high / fixed — Gateway translation preserves route, model and account pins.

Tasks: T13. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. C exits 0: a real ready-task retry traverses the gateway/native ledger and persists synthetic route/model/account. Only route availability and process startup are stubbed. Frozen recovery command exits 0: 12 tests. No paid agent execution claim.

### F33 — high / fixed — Gateway translation preserves question answers, decision aliases and edited field/value.

Tasks: T13. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. C exits 0: answer-round round/answers completes the real round; objective/value is preserved. AI exits 0 for requestId and request_id aliases. Frozen gateway command suite exits 0: 13 tests. E2 exits 0 through the real gateway/native HTTP path: preserved objective and both criteria aliases now publish approved revisions and rebase the run (F41 repaired).

### F34 — medium / fixed — Frozen notification and delivery test files exist and execute.

Tasks: T14, T14a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` exits 0: 3 tests. The same command with test_telegram_send.py exits 0: 3 tests. Both frozen commands run tests, unlike F69.

### F35 — high / fixed — The native nonempty snapshot is accepted by the exact phone parser.

Tasks: T4a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. C exits 0: actual native API read model with a real M1 run and frozen plan parses to one run through transpiled parseSnapshot from page.tsx. Frozen remote API command exits 0: 6 tests. AM2 separately rechecks the installed HTTP snapshot; F72 is fixed.

### F36 — high / fixed — The real gateway flattens its cached snapshot for the phone.

Tasks: T12. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AG exits 0: authenticated production snapshot returns 200 with runs/plans/schemaVersion at the root, one real run, and laptop.online. The exact phone parseSnapshot accepts it. Frozen stream command exits 0: 14 tests.

### F37 — medium / open — Final exhaustion again emits retrospective failure alerts for earlier attempts.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AB exits 0 after replacing the obsolete one-alert expectation: task max=3/current=a3/history=a1,a2 produces three attempt.failed events instead of one terminal a3 event. The terminal-attempt filter was removed from build_events. Single-attempt E2E passes and does not cover this scenario.

### F38 — medium / fixed — Structured HTTP INVALID_CURSOR reaches the gateway reset branch.

Tasks: T13, T12. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. G exits 0: actual loopback HTTP error is translated to UpstreamResponseError and resets event_cursor to empty. Frozen gateway command and stream suites exit 0: 13 and 14 tests.

### F39 — medium / fixed — The public relay preserves native failed-effect HTTP status.

Tasks: T13, T15d. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AK exits 0: injected native handler failure through actual laptop and authenticated public gateway returns HTTP 500, status FAILED, code EFFECT_FAILED. G separately preserves a status tuple. Frozen command suite exits 0: 13 tests.

### F40 — medium / open — Ambiguous or truncated successful upstream responses are misclassified or escape the runtime.

Tasks: T13. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. I and I2 exit 0 reproducing malformed successful JSON classification and truncated-response propagation. Normal timeout tests pass; an ambiguous accepted response is not proof the effect did not execute. Retain the idempotency key when reporting uncertainty.

### F41 — high / fixed — The native editor accepts phone objective and both criteria aliases and rebases the bound run.

Tasks: T8a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py` exits 0: 12 tests. Report Probe E2 fenced Python command exits 0: actual gateway/native HTTP commands using field=objective, criteria and acceptance_criteria plus value each return HTTP 200/status OK; frozen remote-owner revisions r2/r3/r4 contain the exact edits and the bound run reaches each matching revision. Only process stopping/startup is stubbed; validation, challenge, publication and rebasing are real.

### F42 — high / fixed — Remote editing rejects unapproved drift or review status and rolls back prepublication refusal.

Tasks: T8a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py` exits 0: 12 tests including real native HTTP drift/review rejection. Report Probe E2 fenced Python command exits 0: an unrelated unapproved T2 edit returns PLAN_DRIFT, review status returns PLAN_NOT_APPROVED, bytes and approved/bound r4 remain unchanged. Injecting refusal only at publishable_problem restores exact original PLAN.json bytes and creates no r5. Source uses the approved bound base, remote-edit lock, atomic replace and prepublication rollback. Postpublication I/O reconciliation remains F70, separately reproduced by AL2; this repair does not claim cross-process writer serialization.

### F43 — medium / fixed — Telegram delivery retains bounded expiry, backoff and timestamped attempt history.

Tasks: T14a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. N exits 0: failures back off, messages over one hour drop, and telegram_history records timestamped sent/retry/dropped attempts. Frozen telegram_send command exits 0: 3 tests. Public visibility and 90-day retention remain separate F71/F12.

### F44 — medium / open — Actual quota windows are returned as an array that the phone discards.

Tasks: T4a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Q exits 0: real quota projection windows array produces zero accounts through the exact parseQuotaAccounts phone parser. Source fixtures with another dialect do not repair the public producer.

### F45 — medium / fixed — The gateway entrypoint liveness fixture includes mandatory OAuth settings.

Tasks: T10. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py` exits 0: 5 tests, including entrypoint/config. No real deployment or OAuth app was used.

### F46 — medium / open — Phone cancel/delete plan controls require a challenge ID the UI never obtains.

Tasks: T15d. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. page.tsx plan controls are disabled until a manually supplied challengeId exists, with no automatic challenge fetch/display for cancel-plan/delete-plan. AG confirms public native challenge issuance itself is fixed and returns 201 (F66).

### F47 — medium / open — Anonymous Caddy clients share one login bucket and can exhaust owner sign-in availability.

Tasks: T11a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. L exits 0: six real requests with distinct synthetic X-Forwarded-For addresses from one proxy peer return [302,302,302,302,302,429]. Limiter keys on connection peer; Caddy is the shared peer. Do not fix by trusting arbitrary forwarded headers.

### F48 — low / open — The documented gateway-key minimum is not enforced at startup.

Tasks: T16. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. W/Y/Z/O exits 0: GatewayConfig accepts a short nonempty synthetic key despite the documented 24-character minimum. No real credentials read or strength attack attempted.

### F49 — medium / open — A malformed authenticated native command disconnects before deliberate validation.

Tasks: T5. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Report Probe V fenced Python command exits 0: a real keyed native POST containing idempotency_key and command=pause but no target disconnects with KeyError before deliberate validation. The identical unauthenticated request returns HTTP 401. Ledger.validate also performs unguarded command membership for unhashable input; that additional TypeError is a source observation, not V's measured exception. Valid/unknown-command suite paths pass.

### F50 — medium / open — Telegram /estado skips real snapshot runs because it reads req_id.

Tasks: T14b. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. W exits 0: the actual native serializer uses req/reqId, while TelegramBot reads req_id; the rendered status has only its heading and no run controls. Existing four bot tests use their own dialect.

### F51 — medium / open — Inline Telegram delivery can block five-second liveness polling.

Tasks: T14a, T10. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Y exits 0: a deterministic sender/clock seam consumes delivery time inside poll_once. Source run_forever calls poll_once synchronously and sleeps afterward; sender defaults to five-second network timeout per delivery with no separate worker. No measured real Telegram latency claim.

### F52 — low / open — The upstream command deadline defaults to five seconds rather than fifteen.

Tasks: T10, T13. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. W/Y/Z/O exits 0: default GatewayConfig.request_timeout is 5, shared by the upstream client, against the frozen suspended-command 15-second deadline. Normal timeout still returns UNKNOWN_OUTCOME with a key.

### F53 — medium / open — Telegram-induced offline transition can suppress the active-run outage alert.

Tasks: T10, T13, T14. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Z exits 0: the tested Telegram timeout path changes liveness state before the poll transition bookkeeping; subsequent offline polls do not enqueue the required active-run alert. Durable same-outage restart dedupe separately passes R/S/T/U/X.

### F54 — medium / open — An explicitly empty gateway bind becomes a wildcard HTTP bind.

Tasks: T10. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. W/Y/Z/O exits 0: GatewayConfig.from_env accepts GATEWAY_BIND empty and passes it as the listener address instead of rejecting it or choosing the private bridge. Completely filled example parsing remains repaired F22.

### F55 — high / fixed — Persisted first-observation cursors deliver late-derived events.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. R exits 0: a late stall and newly observed round appear after a saved cursor despite older occurredAt timestamps; runtime.event_cursor advances. Frozen remote-events command exits 0: 16 tests. Old backlog scheduling is separately F57.

### F56 — medium / open — JSON-quoted credentials and database URL passwords remain visible inside text logs.

Tasks: T6, T7, T15c. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. S exits 0: stringified JSON password/refresh_token and postgres URL password remain after laptop redaction and phone review-text sanitizer; structured dict password is redacted. Synthetic values only. This does not invalidate plain assignment/bearer fix F14.

### F57 — medium / open — Cursor reconstruction starts at the beginning and can delay fresh notifications beyond 60 seconds.

Tasks: T14. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. T/AF exit 0: new runtime initially polls after empty cursor and sends a historical run.finished event. With 3000 preceding command events, the fresh round is queued only at poll 16 (75 s at the production five-second cadence), with no send at polls 1 through 13.

### F58 — medium / open — Quota alerts trigger per exhausted account without requiring every account to be exhausted.

Tasks: T6, T14. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. U exits 0: one exhausted account plus one available account still produces a quota notification. Frozen R10 requires every account out of quota.

### F59 — medium / open — The same failed attempt can enqueue twice when flow and projection arrive sequentially.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. U exits 0: observe flow failure, persist cursor, then observe its run projection; two different dedupe keys produce two outbox rows. Restart same-ID dedupe still works. AB separately shows retrospective historical-attempt alerts (F37).

### F60 — low / open — Unicode OAuth state disconnects the unauthenticated callback instead of returning an invalid-state error.

Tasks: T11. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. X exits 0: a synthetic matching non-ASCII state query/cookie reaches compare_digest and raises TypeError, closing the connection. No session bypass or live credential demonstrated.

### F61 — high / fixed — Blocked-event identities remain run-scoped for repeated attempt IDs.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AA exits 0: two real M1 runs both allocate att-0001; scoped reviews return each run distinct failure. Generated blocked events have distinct keys, yielding two outbox rows. Frozen remote-event command exits 0: 16 tests.

### F62 — high / fixed — Both phone failure-review callers now supply the required run target.

Tasks: T15c. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AG exits 0: real keyed laptop/public authenticated review?target=demo%2FREQ-001 for att-0001 returns 200 with cause/verification/diff/logTail. Missing-target control returns 400. Source inspection confirms target forwarding in both /review and embedded panel, including effect dependency. npm run build exits 0; browser fixture review assertions pass before the unrelated width failure.

### F63 — high / fixed — Fresh Bogota round timestamps are UTC and delivered before expiry.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AC exits 0 under TZ=America/Bogota: new_round writes an explicit Z timestamp; collect emits round.waiting at that timestamp despite a two-hour-old PLAN.md, and outbox delivery records sent. Frozen remote-events command exits 0: 16 tests.

### F64 — medium / open — Routes with unknown quota are shown as available although retry refuses them.

Tasks: T8. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AD exits 0: the same synthetic candidate with quota_status=unknown is marked available by route_options but omitted by pins.available. C confirms an explicitly available pinned route still works.

### F65 — medium / fixed — Absent systemctl preserves panel startup; uncertain service ownership fails closed.

Tasks: T9. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AE2 exits 0: absent executable yields one detached startup and zero systemctl calls; discovered executable raising FileNotFoundError yields no competing loose server. Frozen platform suite exits 0: 28 tests.

### F66 — high / fixed — Native/public keyed challenge issuance returns HTTP 201.

Tasks: T5b. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AG exits 0: actual native POST challenges and authenticated gateway relay both return 201 with challengeId, bound target and expiresIn=120. Frozen command suite exits 0: 13 tests. Manual challenge UI gap remains F46.

### F67 — high / fixed — Actual M1 projection exposes exhaustion facts and produces a terminal event.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AH exits 0: the current fixture has one real failed att-0001 with attempts_used=max_attempts=1 and retries_remaining=0; build_events emits exactly one attempt.failed with those facts. The raw retry_exhausted flag is false, but the explicit remaining count satisfies the event predicate. Frozen E2E exits 0 and asserts that event and one delivered alert. Multi-retry retrospective alerts remain F37.

### F68 — low / open — Immediate command errors forward raw handler exception text.

Tasks: T5. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AJ exits 0: injecting ValueError with a synthetic secret-shaped assignment returns it verbatim through actual HTTP; public history withholds it and feed.redact would sanitize it. This is bounded failure injection, not a reproduced built-in live-secret leak; severity remains low.

### F69 — medium / open — Frozen failure-review verification names a missing test file and runs zero tests.

Tasks: T7. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py` exits 5: Ran 0 tests / NO TESTS RAN. Other review tests/probes do not make this frozen command execute.

### F70 — medium / open — A post-publication edit failure leaves the approved revision ahead of the bound run.

Tasks: T8a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Report Probe AL2 fenced Python command exits 0: injecting OSError solely at ops.apply, without bypassing the publication compatibility gate, leaves latest approved r2 and bound run r1. PLAN.json remains r2; a subsequent edit fails closed with PLAN_BASE_STALE and does not mutate bytes. No durable completion/reconciliation is present. Prepublication drift/status/rollback is now repaired F42. Preserve published history rather than deleting an approved revision.

### F71 — medium / open — Telegram no-entregado status exists internally but is not exposed in public history or the web.

Tasks: T14a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. N exits 0 with timestamped dropped history. Static trace: public commands/history relay native command ledger only; TelegramBot/web do not read outbox.history, and read_routes allow-list exposes no notification-history endpoint. No claim that internal history is absent.

### F72 — high / fixed — Fresh wheel and sdist include snapshot/projection modules, and the installed snapshot endpoint works.

Tasks: T4a. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Report Probe AM2 fenced Python command exits 0 in 5.144 s: fresh wheel/sdist contain bt_remote_snapshot.py and bt_scheduler_projection.py alongside existing recovery modules. A fresh venv invokes the real HTTP snapshot regression using installed modules under python -I; 1 test passes (1.061 s), asserting HTTP 200, active T1, frozen criteria, rejected-review history, shared now-frame caching and response below 1 s. Every loaded bt_ module resolves inside installed site-packages; no checkout implementation is importable. Checkout remote API (6 tests), parser/public probes C/AG, production build and frozen E2E (1 test) also pass. The earlier AM defect assertion fails because the sdist now includes the module; it is replaced by AM2, without changing product/tests/configuration.

### F73 — medium / open — A built-in approval-gate SystemExit escapes the command ledger and strands the command as PENDING.

Tasks: T5b. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AN exits 0 using a real review-state plan with invalid PLAN.json, real target_state, issued one-use challenge and dispatch_handlers. approve enters bt_rounds.plan_decide, its real publication gate raises SystemExit(PLAN_INVALID), Ledger._apply catches only Exception, and the caller receives no normal result. The sole ledger row remains PENDING; same-key replay returns UNKNOWN_OUTCOME although no approval or launch occurred. No injected SystemExit or agent process was used.

### F74 — low / open — Production frontend configuration silently defaults a missing gateway origin to loopback.

Tasks: T15. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. AO exits 0: transpile and evaluate the actual next.config.ts with NODE_ENV=production and no FLOW_GATEWAY_ORIGIN; rewrites returns http://127.0.0.1:8790/api/:path*. This unconditional development fallback violates the fail-closed mandatory-production-config engineering rule and builds a frontend with the wrong API destination instead of refusing configuration. No live misconfigured deployment or data exposure is claimed.

### F75 — medium / open — Blocked-task decision requests are notified as plans awaiting approval.

Tasks: T6, T14. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Report Probe AP fenced Python command exits 0: a real M1 blocked task produces a real open_requests decision with options; build_events maps it to plan.waiting, and notification_for_event renders plan esperando aprobación, not a decision notice. The decision payload is retained, but the Telegram renderer ignores it. The distinct decision.requested mapping is never reached. Actual plan approval waiting remains fixed F10.

### F76 — low / open — Command activity events use a missing created_at field and are timestamped in 1970.

Tasks: T6. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Report Probe AP fenced Python command exits 0: actual successful Ledger.submit stores a current received_at and no created_at; passing the real Ledger.rows result to build_events emits command.updated occurredAt=1970-01-01T00:00:00Z. The schema-field mismatch is concrete. command.updated is not a notifying event, so no dropped Telegram command alert is claimed; numeric quota timestamp loss remains unconfirmed.

### F77 — low / open — The runbook reloads Docker-hosted Caddy through a host systemd unit in Step 5 and its rollback.

Tasks: T16. Rechecked on 33e76ecc127ee3f10ebf22d09ba1b394996f6ade (att-0430), 2026-10-21. Report Probe AR fenced Python command exits 0 in 0.932 s. Static assertions read remote/docs/runbook.md and remote/deploy/Caddyfile: both document Docker-hosted Caddy, but Step 5 and rollback prescribe sudo systemctl reload caddy. That controls a host service rather than the specified container; container-specific validation/reload and rollback instructions are missing. No host service command, container connection or deployed failure was attempted.

## Frozen coverage and handoff

| Requirement / boundary | Current verdict |
|---|---|
| R1/R2/R3/R16/R17 authentication/trust | Auth/guard/API/kit/E2E paths pass. F4/F5/F12/F27/F31/F47/F48/F54/F60/F68 remain with bounded severities; no credential or arbitrary-command exploit inferred. |
| R4/R7/R14 reads/live/offline/mobile | C/AG/AK parse real snapshots; local panel/platform/page checks pass. F11/F13/F18/F21/F29 remain, and installed snapshot repair F72 passes AM2. |
| R5/R6/R8/R13 commands/recovery | Ledger/relay/recovery and E2 pass. F41/F42 fixed. F7/F8/F9/F16/F26/F40/F46/F64/F70/F73 remain; terminal side effects/failure reconciliation are not inferred from happy paths. |
| R9 review | Scoped real four-section review and build pass; F19/F25/F62 fixed. Frozen missing review-test command F69 and quoted text redaction F56 remain. |
| R10/R11/R12 alerts | Real current single-attempt exhaustion and one delivered alert pass. F6/F30/F37/F50/F51/F53/F57/F58/F59/F75 remain; internal expiry/backoff is repaired F43. |
| R15 history/quotas | Native/public command history works; F44 quota dialect, F71 public dropped-delivery history and F76 activity-event timestamp remain. |
| Packaging/deployment/regression | P proves original recovery modules installed; AM2 proves installed snapshot/projection repair F72. F3 fresh-install ordering/F74 production origin fallback/F77 Caddy runbook remain. Local-panel pages and core operations pass. |

No confirmed critical/high finding remains open. F72 is fixed in the prerequisites, not by this read-only audit.
All 46 medium/low findings remain recorded for their named task owners; only the owner can accept a risk.
Preserve approved-base editing, review target propagation, gateway flattening, UTC/scoped event IDs and terminal
attempt facts. No source, test, frozen requirement or gate was changed to obtain these conclusions.

## Reproduction commands

Run from the repository root with installed web dependencies. All values are synthetic. Temporary build/state
artifacts are isolated and removed by the probes. No credential file is opened. Probe labels are stable references
used above. A successful reproduction asserts the observed behavior, including an open defect when stated.

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
    def relay_command(self, value): return 200, {'status': 'OK'}
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
  assert frozen['tasks'][0]['acceptance_criteria'] and snapshot['plans'][0]['tasks'][0]['acceptanceCriteria']==frozen['tasks'][0]['acceptance_criteria']
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
  print('Edit adapter preserves field/value; E2 exercises successful edits and approved-base protections.')
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

### Probe E2 — repaired phone dialect, approved-base checks and rollback

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
   for n,field,value in [(1,'objective','Owner edits only the selected task'),(2,'criteria',['Owner criterion is observable']),(3,'acceptance_criteria',['New owner criterion is observable'])]:
    result=send(n,field,value)
    assert result['status']=='OK',result
    assert revisions.latest(rdir)['revision']==n+1 and ops.bound_plan(rdir).revision==n+1
    saved=revisions.load_revision(rdir,n+1)
    assert saved['tasks'][0]['objective' if field=='objective' else 'acceptance_criteria']==value
   print('E2 objective and both criteria aliases publish and rebase r2/r3/r4')
   original=path.read_bytes();working=json.loads(original);working['tasks'][1]['objective']='UNAPPROVED unrelated T2 change';path.write_text(contract.dumps(working));drift=path.read_bytes()
   result=send(4,'objective','Owner edits only the selected task')
   assert result['status']=='FAILED' and 'PLAN_DRIFT' in str(result)
   assert path.read_bytes()==drift and revisions.latest(rdir)['revision']==4 and ops.bound_plan(rdir).revision==4
   print('E2 unrelated drift rejected without publication or byte changes')
   path.write_bytes(original);md=rdir/'PLAN.md';approved=md.read_bytes();md.write_bytes(approved.replace(b'status: approved',b'status: review'))
   result=send(5,'objective','Owner edits only the selected task')
   assert result['status']=='FAILED' and 'PLAN_NOT_APPROVED' in str(result)
   assert path.read_bytes()==original and revisions.latest(rdir)['revision']==4
   md.write_bytes(approved)
   print('E2 review status rejected without publication or byte changes')
   with patch('bt_plan_adapter.publishable_problem',return_value='synthetic publication refusal'):
    result=send(6,'objective','Owner edits only the selected task')
   assert result['status']=='FAILED' and 'synthetic publication refusal' in str(result)
   assert path.read_bytes()==original and revisions.latest(rdir)['revision']==4 and ops.bound_plan(rdir).revision==4
   print('E2 injected prepublication rejection restores exact PLAN.json bytes, no r5')
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
 def relay_command(self,value):return 200, {'status':'OK'}
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
 ev=feed.build_events(state);print('AB task finally exhausted failure alerts',len(ev));assert len(ev)==3 and {e['target']['attemptId'] for e in ev}=={'a1','a2','a3'}
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
  for path in ['commands','history','attempts/att-0001/review?target=demo%2FREQ-001','events']:
   with patch.object(bt_subscriptions,'summary',return_value=[]):status,body=call('GET',path)
   print('AG public read',path,status,sorted(body));assert status==(404 if path=='events' else 200)
  status,body=call('GET','attempts/att-0001/review');print('AG negative control review without target',status,body);assert status==400 and body['code']=='INVALID_TARGET'
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

### Probe AH — current real single-attempt terminal producer

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
 assert task['attempts']==1 and len({a['id'] for a in task['history']})==1
 assert task['attempts_used']==task['max_attempts']==1 and task['retries_remaining']==0
 events=feed.build_events({'runs':runs});print('AH real exhausted feed',events)
 failures=[e for e in events if e['type']=='attempt.failed'];assert len(failures)==1 and failures[0]['target']['attemptId']=='att-0001'
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

### Probe AI — preserved decision aliases and removed review link

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
assert key=='event:synthetic-failure'
assert '/review' not in message
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
print('AI review path removed; alert lacks URL, cause or reply_markup')
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

### Probe AK — public effect status and recognized offline state without timestamp

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
        assert response.status==200 and body['online'] is False and body['laptop']['online'] is False
        js="""const fs=require('node:fs'),vm=require('node:vm'),ts=require('./remote/web/node_modules/typescript');const source=fs.readFileSync('remote/web/src/app/page.tsx','utf8');const code=source.slice(source.indexOf('type Target'),source.indexOf('function prettyTime'));const sandbox={input:JSON.parse(fs.readFileSync(0,'utf8')),exports:{}};vm.createContext(sandbox);const parsed=vm.runInContext(ts.transpileModule(code+';parseSnapshot(input)',{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,sandbox);if(parsed.laptop?.online!==false)process.exit(2);console.log('AK exact phone parser recognizes laptop.online=false; offline-start timestamp still absent')"""
        check=subprocess.run(['node','-e',js],input=json.dumps(body),capture_output=True,text=True);print(check.stdout,check.stderr);assert check.returncode==0
    finally:
        rt.hub.close();gateway.shutdown();gateway.server_close();gt.join()
        server.shutdown();server.server_close();worker.join();rt.outbox._db.close()
PY_AUDIT
```

### Probe AL2 — postpublication rebase I/O failure and stale-base guard

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
 try:
  with patch.object(bt_core,'ROOT',base),patch('bt_lock._lock_dir',return_value=base/'.state/locks'),patch.object(ops,'stop_owner',return_value=0),patch.object(ops,'resume',return_value='synthetic-no-start'):
   sync.approve_freeze(rdir,'REQ-001',('approved',));run=scheduler.open_scheduler(rdir);run.step();scheduler.write_projection(rdir,run);bt_scheduler_run._runtime_binding(rdir,resume=False)
   import bt_remote_edit as editor
   with patch.object(ops,'apply',side_effect=OSError('synthetic rebase I/O failure')):
    try:editor.dispatch_edit_brief('demo/REQ-001',{'task':'T1','brief':'Owner approves a task edit','typed_req':'REQ-001'})
    except OSError as e:assert 'synthetic rebase' in str(e)
    else:raise AssertionError('injected revise failure should propagate')
   before=path.read_bytes()
   try:editor.dispatch_edit_brief('demo/REQ-001',{'task':'T1','brief':'Another owner-approved task edit','typed_req':'REQ-001'})
   except ValueError as e:assert 'PLAN_BASE_STALE' in str(e)
   else:raise AssertionError('mismatched approved/bound revision should fail closed')
   assert path.read_bytes()==before
   print('AL latest',revisions.latest(rdir)['revision'],'bound',ops.bound_plan(rdir).revision)
   assert revisions.latest(rdir)['revision']==2 and ops.bound_plan(rdir).revision==1
   print('AL2 postpublication injected I/O failure strands approved r2 while run stays r1 (F70); prepublication F42 is separately repaired')
 finally:server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY_AUDIT
```

### Probe AM2 — installed distribution snapshot over real HTTP

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil
audit_scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'))
tempfile.tempdir=str(audit_scratch.resolve());atexit.register(shutil.rmtree,audit_scratch,ignore_errors=True)
import pathlib, subprocess, sys, zipfile, tarfile
root=pathlib.Path.cwd();sys.path.insert(0,str(root/'tests/migration'))
import installed_wheel
installed=installed_wheel.get()
required={'bt_remote_edit.py','bt_route_pins.py','bt_remote_api.py','bt_remote_snapshot.py','bt_scheduler_projection.py'}
with zipfile.ZipFile(installed.wheel) as archive:
 assert required.issubset(set(archive.namelist()))
with tarfile.open(installed.sdist) as archive:
 assert required.issubset({pathlib.Path(p.name).name for p in archive.getmembers()})
print('AM2 fresh wheel and sdist contain snapshot, projection and recovery modules')
code='''
import sys,pathlib,runpy,unittest
site=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(site))
import bt_core,bt_remote_api,bt_remote_snapshot,bt_scheduler_projection
for module in (bt_core,bt_remote_api,bt_remote_snapshot,bt_scheduler_projection):
 assert pathlib.Path(module.__file__).resolve().is_relative_to(site),module.__name__
namespace=runpy.run_path(sys.argv[2])
suite=unittest.TestSuite([namespace['RemoteApiTests']('test_snapshot_uses_shared_now_frame_and_exposes_rejected_review_attempt')])
result=unittest.TextTestRunner(verbosity=2).run(suite)
for name,module in list(sys.modules.items()):
 if name.startswith('bt_') and getattr(module,'__file__',None):
  assert pathlib.Path(module.__file__).resolve().is_relative_to(site),name
raise SystemExit(0 if result.wasSuccessful() else 1)
'''
result=subprocess.run([str(installed.python),'-I','-c',code,str(installed.site),str(root/'skill/scripts/tests/test_remote_api.py')],cwd=installed.work,capture_output=True,text=True)
print(result.stderr)
assert result.returncode==0,result.stderr
print('AM2 isolated installed real keyed HTTP snapshot: 1 test passes, HTTP 200, active T1, criteria, rejected review history, shared now-frame cache and <1 s response; all bt_ modules resolve inside installed site (F72 fixed)')
PY_AUDIT
```

### Probe AN — real approval-gate SystemExit and target traversal rejection

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil,sys,os,json
scratch=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/'remote',prefix='.audit-repro-'));tempfile.tempdir=str(scratch.resolve());atexit.register(shutil.rmtree,scratch,ignore_errors=True)
sys.path.insert(0,str(pathlib.Path('skill/scripts').resolve()))
from unittest.mock import patch
with tempfile.TemporaryDirectory() as tmp:
 base=pathlib.Path(tmp);os.environ['BITACORA_ROOT']=str(base)
 import bt_core,bt_remote_commands as commands,bt_plans_api
 rdir=base/'demo/requirements/REQ-001-audit';rdir.mkdir(parents=True)
 (rdir/'PLAN.md').write_text('---\nstatus: review\n---\n# Plan\n')
 (rdir/'PLAN.json').write_text('{"invalid":true}')
 with patch.object(bt_core,'ROOT',base):
  try:bt_plans_api.project_dir(base,'..')
  except bt_plans_api.PlanError:print('AN traversal project .. rejected by real project_dir')
  else:raise AssertionError('project traversal was not refused')
  state=commands.target_state('demo/REQ-001','approve',{});print('AN actual plan state',state);assert state['state']=='review'
  ledger=commands.Ledger();challenge=ledger.issue_challenge('demo/REQ-001','REQ-001')
  envelope={'idempotency_key':'synthetic-approve-invalid','command':'approve','target':'demo/REQ-001','origin':'web','params':{},'precondition':{'state':'review'},'confirmation':{'challenge_id':challenge['challengeId'],'typed_req':'REQ-001'}}
  try:ledger.submit(envelope,commands.dispatch_handlers(),commands.target_state)
  except SystemExit as e:assert 'PLAN_INVALID' in str(e);print('AN real approval gate SystemExit escapes native ledger')
  else:raise AssertionError('expected built-in gate SystemExit')
  rows=ledger.rows();assert len(rows)==1 and rows[0]['status']=='PENDING'
  result=ledger.submit(envelope,commands.dispatch_handlers(),commands.target_state)
  assert result['code']=='UNKNOWN_OUTCOME' and result['replayed']
  print('AN row remains PENDING; replay returns UNKNOWN_OUTCOME although no approval/launch happened')
PY_AUDIT
```

### Probe AO — production frontend configuration fallback

```bash
node --input-type=commonjs - <<'JS'
const fs=require('node:fs'),vm=require('node:vm'),ts=require('./remote/web/node_modules/typescript');
const source=fs.readFileSync('remote/web/next.config.ts','utf8');
const sandbox={exports:{},process:{env:{NODE_ENV:'production'}}};
vm.createContext(sandbox);
vm.runInContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,sandbox);
sandbox.exports.default.rewrites().then(r=>{
 if(r[0].destination!=='http://127.0.0.1:8790/api/:path*')throw new Error('unexpected fallback');
 console.log('AO production config without FLOW_GATEWAY_ORIGIN silently rewrites API to loopback');
});
JS
```

### Probe AP — real decision notification and command-event timestamps

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil,sys,os
root=pathlib.Path.cwd();scratch=pathlib.Path(tempfile.mkdtemp(dir=root/'remote',prefix='.audit-repro-'));tempfile.tempdir=str(scratch.resolve());atexit.register(shutil.rmtree,scratch,ignore_errors=True)
sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway'),str(root/'skill/scripts/bt_scheduler_core/tests')]
from unittest.mock import patch
import bt_remote_commands as commands,bt_remote_events as feed,bt_scheduler_decisions as decisions,bt_scheduler_adapter as adapter,bt_run_stores
from notifications import notification_for_event
from support import Harness,indep
with tempfile.TemporaryDirectory() as tmp:
 base=pathlib.Path(tmp);os.environ['BITACORA_ROOT']=str(base)
 ledger=commands.Ledger(base/'commands.db')
 request={'idempotency_key':'synthetic-event-clock','command':'pause','target':'demo/REQ-001','origin':'web','params':{},'precondition':{'state':'running'}}
 result=ledger.submit(request,{'pause':lambda target,params:{'ok':True}},lambda *args:{'state':'running'})
 assert result['status']=='OK'
 [row]=ledger.rows();assert row['received_at'].startswith('2026-') and 'created_at' not in row
 [event]=feed.build_events({'commands':[row]})
 assert event['type']=='command.updated' and event['occurredAt']=='1970-01-01T00:00:00Z'
 print('AP real ledger received_at is current but command.updated occurredAt is 1970 (F76); this event is not notifying')
 db=base/'SCHEDULER.db';h=Harness([indep('T1'),indep('T2',['T1'])],repository=adapter.core.SqliteRepository(db),max_attempts=1)
 h.core.step();h.send('T1','execution_failed',reason='boom');h.core.step();assert h.state('T1')=='blocked'
 rdir=base/'REQ-001-audit';rdir.mkdir()
 with patch.object(adapter,'run_db_path',return_value=db),patch.object(bt_run_stores,'paths',return_value={}),patch.object(decisions,'_newer_revision',return_value=False):
  [decision]=decisions.open_requests(rdir)
 assert decision['task']=='T1' and decision['options']
 [event]=feed.build_events({'decisions':[{'project':'demo','req':'REQ-001','at':'2026-10-21T19:00:00Z','request':decision}]})
 assert event['type']=='plan.waiting' and event['data']['decisionRequest']['id']==decision['id']
 key,message=notification_for_event(event)
 assert 'plan esperando aprobación' in message and 'decisión' not in message
 print('AP real blocked-task decision is rendered as plan approval waiting (F75)')
PY_AUDIT
```

### Probe AQ — wrong brief prefill and rejected title-only overwrite

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil,sys,os,json
root=pathlib.Path.cwd();scratch=pathlib.Path(tempfile.mkdtemp(dir=root/'remote',prefix='.audit-repro-'));tempfile.tempdir=str(scratch.resolve());atexit.register(shutil.rmtree,scratch,ignore_errors=True)
sys.path[:0]=[str(root/'skill/scripts/tests'),str(root/'skill/scripts')]
from unittest.mock import patch
from test_remote_recovery import RemoteRecoveryTests
import bt_remote_edit as editor,bt_scheduler_ops as ops
from bt_planner import revisions
case=RemoteRecoveryTests();case.setUp()
try:
 import test_plan_integration as fixture
 with patch.object(fixture,'PLAN_MD',fixture.PLAN_MD.replace('Reject expired sessions','Reject expired sessions without delay')):
  core,rdir,doc=case.real_approved_edit_run()
 before=revisions.load_revision(rdir,1)['tasks'][0];assert before['objective']!=before['title']
 with patch.dict(os.environ,{'BITACORA_ROOT':str(case.root)}),patch.object(core,'ROOT',case.root),patch.object(ops,'stop_owner',return_value=0),patch.object(ops,'resume',return_value='synthetic-no-start'):
  from bt_remote_snapshot import build_snapshot
  snapshot=build_snapshot(case.root);task=snapshot['runs'][0]['tasks'][0]
  assert task['title']==before['title'] and 'objective' not in task
  source=(root/'remote/web/src/app/page.tsx').read_text()
  assert 'defaultValue={task.title ?? ""}' in source and 'field: "objective", value: String(values.get("brief")' in source
  original=(rdir/'PLAN.json').read_bytes()
  try:editor.dispatch_edit_brief('demo/REQ-001',{'task':'T1','field':'objective','value':task['title'],'typed_req':'REQ-001'})
  except ValueError as error:assert 'repeats the title' in str(error)
  else:raise AssertionError('expected real publication validation to reject title-only objective')
  assert revisions.latest(rdir)['revision']==1 and ops.bound_plan(rdir).revision==1
  assert (rdir/'PLAN.json').read_bytes()==original
  print('AQ phone prefill is title rather than full objective (F8), but real validator rejects title-only overwrite and restores bytes; no approved r2')
finally:case.tearDown()
PY_AUDIT
```

### Probe AR — fresh decision expiry hypothesis and container-Caddy runbook

```bash
python - <<'PY_AUDIT'
import pathlib,tempfile,atexit,shutil,sys,os,json,time
root=pathlib.Path.cwd();scratch=pathlib.Path(tempfile.mkdtemp(dir=root/'remote',prefix='.audit-repro-'));tempfile.tempdir=str(scratch.resolve());atexit.register(shutil.rmtree,scratch,ignore_errors=True)
sys.path[:0]=[str(root/'skill/scripts'),str(root/'remote/gateway'),str(root/'skill/scripts/bt_scheduler_core/tests')]
from unittest.mock import patch
import bt_core,bt_scheduler_adapter as adapter,bt_scheduler_core as core,bt_plans_api as plans,bt_live_api as live,bt_remote_events as feed
from support import Harness,indep
from notifications import NotificationOutbox,notification_for_event,event_timestamp
with tempfile.TemporaryDirectory() as tmp:
 base=pathlib.Path(tmp);os.environ['BITACORA_ROOT']=str(base)
 rdir=base/'demo/requirements/REQ-001-audit';rdir.mkdir(parents=True)
 (rdir/'PLAN.md').write_text('---\nstatus: approved\n---\n# Plan\n')
 old=time.time()-7200;os.utime(rdir/'PLAN.md',(old,old))
 db=adapter.run_db_path(rdir);db.parent.mkdir(parents=True,exist_ok=True)
 h=Harness([indep('T1'),indep('T2',['T1'])],repository=core.SqliteRepository(db),max_attempts=1,plan_id='REQ-001')
 (rdir/'PLAN.json').write_text(h.text)
 h.core.step();h.send('T1','execution_failed',reason='fresh blocked task');h.core.step();adapter.write_projection(rdir,h.core)
 assert h.state('T1')=='blocked'
 with patch.object(bt_core,'ROOT',base),patch.object(live,'flow_events',return_value=([],[],{})):
  [plan]=plans.plans_payload(base)
  events=feed.collect(base,[],[plan],[],[])
 [decision_event]=[event for event in events if 'decisionRequest' in event.get('data',{})]
 assert abs(time.time()-event_timestamp(decision_event))<30
 out=NotificationOutbox(str(base/'outbox.db'));sent=[]
 out.enqueue(*notification_for_event(decision_event),created_at=event_timestamp(decision_event));out.deliver_due(sent.append)
 assert len(sent)==1 and out.history()[0]['outcome']=='sent';out._db.close()
 print('AR fresh real blocked-task decision uses current projection heartbeat despite two-hour-old PLAN.md; sent before expiry. F75 wrong label remains; no new premature-expiry finding.')
runbook=(root/'remote/docs/runbook.md').read_text()
assert 'Caddy runs in Docker' in runbook and 'sudo systemctl reload caddy' in runbook
assert 'Caddy runs in Docker' in (root/'remote/deploy/Caddyfile').read_text()
print('AR Step 5/rollback document a host systemctl reload for Docker-hosted Caddy (F77); static mismatch only, no host command executed.')
PY_AUDIT
```

## Final artifact checks

`test -s remote/docs/audit.md` ran separately for each of the three T18 acceptance entries, exit 0 each.
The ledger parses as `audit-findings/1`, contains exactly F1–F77 with unique IDs, valid task IDs, severities/statuses,
current command/result evidence for every fixed item, zero accepted risks and **zero open critical/high findings**.
Its 77 summaries, task sets and verdicts match this report (31 fixed, 46 open). Both documents contain no conflict
markers. `git diff --check` exits 0, and git status lists only the two authorized audit documents.

These artifact checks establish document integrity only. The prerequisite failures remain explicitly recorded:
web F18 (366 px versus 360 px), missing review-test command F69 (exit 5), and two additional packaging-test path
assumptions under the mandated internal scratch directory. Caddy validation and live deployment were not run.
Final task acceptance belongs to the independent checker.
