# Independent security and specification audit — T18

**Rework required: F2 (T17), F61 (T6), F62 (T7) and F63 (T6) are high/open.**
The substantive criterion “Confirmed high findings are fixed” is not met. This read-only audit changes only this
report and `audit.findings.json`; prerequisite owners must repair their results. No risk is accepted and no
independent verification verdict is claimed.

Audited tree: `9ca9ac9ea5ebee3fa1e434222de713f8404cde35`, HEAD at entry for att-0344, 2026-10-21,
America/Bogota. Primary auditor: OpenAI Codex; fresh independent static reviewer: Anthropic
`firstParty / claude-sonnet-5-5`, with tool access disabled. Neither audit assumes the other covers an omitted area.

Ledger: **65 findings; 23 rechecked fixed/superseded exposures; 42 open (4 high, 33 medium, 5 low); 0 accepted**.
F1–F60 retain their identities. F41/F42/F55, the previous blockers, are now rechecked fixed. F34/F43/F45 are also
fixed. F37 is narrowed: direct retryable failures no longer notify, but historical failures notify retrospectively
when a task eventually exhausts its budget. F57 is narrowed: continuous-outage restart dedupe is repaired; cursor
reconstruction and backlog delays remain. F2 and F18 reopen because current frozen checks fail.

## Reconciliation, prerequisites and boundaries

Opened both supplied audit artifacts before editing. Contrary to the carry-forward warning, the initial worktree
was clean and neither file had conflict markers: HEAD already contains the carried result. Compared with the
supplied prior result `8ccc09c9becf486efb169f18a6ddda84ce88e677`, the new prerequisites change 30 implementation/test/
configuration paths. They restore edit aliases and rollback, persist feed observation order, restore delivery
expiry/history and exact notification checks, change the gateway cache owner back to `snapshot_cache`, add the
snapshot module and planning models, and change listener/platform behavior. No implementation change is discarded.
All changes in this attempt remain within the two permitted artifacts.

Read the supplied prior attempt outcomes #13–#18 and reachable ledgers at `0af07a73e`, `108efc35f`, `f674c6a29`,
`b3de1b8ce`, `d9e83adc6` and `8ccc09c9b`. Raw m6 receipts and the twelve omitted attempts are unavailable.
Read the complete repository SPEC, PLAN.md, PLAN.json (revision 3, the contract present in this tree), its
amendments and every upstream objective, acceptance criterion and verification command, plus this task's frozen
headless instructions. Prior success does not establish current correctness. Historical provider receipts and
rejected hypotheses are retained below, explicitly superseded by the current ledger.

Scope: separate loopback-only keyed laptop listener versus the unauthenticated local panel, native validation,
challenge/replay/preconditions/concurrency, installed distributions, real edit/freeze/rebase, event production and
paging, failure evidence selection, gateway OAuth/session/Origin/limits/logging/cache/client, Telegram notifications/
bot/delivery/restart, phone producer/consumer contracts, go-live kit and local built-web E2E. T19 is downstream.
Only synthetic credentials, owned loopback servers and temporary fixture state are used. No real agents run; no
credential file, live account/quota source, host deployment, SSH target or other worktree is accessed. The other
provider receives source listings through stdin, never credentials. Temporary test/build output is not delivered
as a source/configuration change. Documentation remains in these artifacts under the explicit read-only boundary.

## Current verification

Python 3.14.7, Node 24.21.0. Installed the existing web lockfile first with
`cd remote/web && npm ci --offline`: exit 0, 320 packages; no lockfile change. Later checks reuse dependencies and
neither install nor write inside node_modules. Web/browser and E2E builds run sequentially. Laptop/gateway Python
checks run with BITACORA_ROOT set to an empty temporary directory before imports. Shared frozen commands execute
once unless a failure or edited reproducer justifies a recheck.

| Current command | Result |
|---|---|
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py` | Exit 0; 7 tests, 8.205 s. |
| Same directory/discovery, `test_remote_commands.py` | Exit 0; 29 tests, 0.238 s. |
| Same directory/discovery, `test_remote_events.py` | Exit 0; 12 tests, 0.713 s, including production-route late stall/round/decision and cursor recovery. |
| Same directory/discovery, `test_remote_review.py` | Exit 0; 3 tests, 1.573 s. |
| Same directory/discovery, `test_remote_recovery.py` | Exit 0; 12 tests, 4.180 s, including installed dispatch, owner edit, drift refusal and approval rollback. |
| Same directory/discovery, `test_platform.py` | Initial exit 1, 27 tests, 2.014 s: process-group disappearance assertion. Rerun exit 0, 27 tests, 1.996 s. Separate owned-process diagnostic found leader -9, group gone, child reaped. Timing-sensitive result retained, not hidden. |
| Same directory/discovery, `test_page*.py` | Exit 0; 43 tests, 11.465 s. |
| `cd skill/scripts/bt_scheduler_core && python -m unittest discover -s tests -p test_operations.py` | Exit 0; 18 tests, 0.766 s. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py` | Exit 0; 5 tests, 11.017 s. |
| Same directory/discovery, `test_auth.py`, `test_guard.py`, `test_stream.py`, `test_commands.py` | Each exit 0: 3/7/8/11 tests in 3.004/3.626/0.512/3.063 s respectively. |
| Same directory/discovery, `test_notify.py`, `test_telegram_send.py`, `test_telegram_bot.py` | Each exit 0: 3/3/4 tests in 0.006/0.004/0.005 s respectively. No absent-file pseudo-pass. |
| `cd remote/web && npm run verify` | Twice exit 1; lint/strict typecheck pass, 13/14 tests pass, Chromium viewport assertion fails `366 !== 360` at panel-browser.test.mjs:165. Node tests 21.730/13.657 s; no skips. F18. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 0; 16 tests, 7.550 s; one skip: caddy unavailable. Browser OAuth cookie check executes. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 1; 1 test, 27.031 s. Optimized Next.js production build passes, then empty feed/cursor assertion fails at line 401 before OAuth/control/offline/delivery checks. F2. |
| `python -m json.tool remote/contract/command.schema.json` and event equivalent | Each exit 0; syntax only. |
| `test -s` route-pin.md, contract.md and architecture.md | Each exit 0. |
| Current reproduction commands below | 18 Python blocks, run from repository root; synthetic behavioral probes, including regressions and confirmed defects. Final block/ledger/path checks below. |

The initial old reproducer run failed B/C/E/H/N/L/W/R because it referenced a removed private snapshot function,
the prior cache attribute, an incomplete frozen fixture or defect behavior now corrected. Updated only the report's
reproducers to use current production boundaries, valid frozen fixtures, actual observation persistence and
restored clock/expiry behavior. These failures were not product regressions; the unchanged frozen web/E2E failures
are product/test acceptance failures. Probe success means an observation reproduced, not that the product passed.

Not run: Python 3.12 (unavailable), actual Caddy binary/container validation (one skipped test), deployed OAuth/
Telegram/Vercel SSE lifetime, live route-selected agent launch, PWA installation, exhaustive 44 px targets or a
current dependency advisory scan. Offline npm's audit summary is not independent advisory evidence. T17's scenarios
after its first failed assertion remain unexecuted in that check; real keyed command/edit probes cover their stated
boundaries independently. The first platform failure remains a timing limitation despite the passing rerun.

## Fresh independent other-provider review

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

## Rejected security hypotheses and remaining limits

No gateway-key bypass: every remote route checks nonempty bearer authorization with constant-time comparison;
serve-remote exposes only versioned paths on 127.0.0.1, separate from the local panel, and the kit tunnel forwards
8766 through loopback 18765. Short-key configuration mismatch is F48, not proof of unauthenticated access.
No OAuth state replay/fixation or foreign login demonstrated: one-use transactional state, cookie-bound callback,
new session token and dav033 restriction pass tests. Unicode callback disconnect remains F60, not state bypass.
Fixed-origin redirects and keyed read-model allowlists reject the proposed redirect/SSRF injection. No command
CSRF bypass through exact Origin, a required custom header and Strict cookies is shown; literal marker/logout
mismatches remain F5. Query logging is still F4.

One-use, target-bound 120-second challenges reject replay/cross-target reuse. A same-key PENDING reservation
replays UNKNOWN_OUTCOME without another effect; D checks distinct-key preconditions serialize. Independent
multiprocess SQLite effects, crash recovery, operation-bound step-up and unrelated local writer races are not
proved by those tests. Review reads use bounded O_NOFOLLOW regular files, correlated ledgers, parameterized SQLite
and argv/stdin git diff; no symlink/path/SQL/command injection demonstrated. Those file protections do not repair
the confirmed cross-run identity ambiguity F62. React renders text, with no demonstrated HTML injection. Telegram
checks configured chat and one-use callback tokens; group-chat human identity is not proven safe by private-chat
checks. No actual duplicate business effect from a new-key uncertain retry is claimed.

## Current findings and verdicts

Each confirmed issue is retained in the machine ledger. Fixed means already fixed in this audited tree and freshly
rechecked with the named command/result. Open medium/low findings remain unaccepted risks, not owner waivers.

### F1 — high / fixed — The Caddy upstream and documented gateway bind now match the frozen container-to-host topology.

Tasks: T16. Rechecked on 9ca9ac9ea: `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 16 tests in 7.550 s, one skip (Caddy unavailable). Caddyfile targets 172.20.0.1:8790 and runbook requires GATEWAY_BIND=172.20.0.1. Updated Probe B: exit 0, GatewayConfig/OAuthConfig parse that same bind. Actual container connectivity/Caddy binary validation remain unrun.

### F2 — high / open — The frozen built-web E2E fails before exercising OAuth, controls, offline behavior or Telegram delivery.

Tasks: T17. `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py`: exit 1, one failure in 27.031 s at line 401: nextCursor is empty and events=[]. Build phase succeeds. _seed_retry_event_fixture still creates one failure with a three-attempt budget; the corrected T6 exhaustion filter appropriately emits no failure alert. Fix the T17 fixture to exhaust its real budget rather than restoring the false alert; its stale-precondition assertion also expects HTTP 200 although current gateway returns 409. This blocking integration gate has not passed on the new prerequisites.

### F3 — medium / open — The restored runbook deploys and restarts before installing the service on a fresh host.

Tasks: T16. remote/docs/runbook.md steps 3/4 call deploy.sh before installing the unit; deploy.sh:27 unconditionally restarts under set -e. Fresh local synthetic missing-unit simulation: deploy exit 5 with current already switched; rollback --dry-run exit 2 without previous release; deploy --dry-run exit 0. Kit checks pass but do not check this order. Reorder first-install steps and document containerized Caddy reload/rollback rather than host systemctl reload caddy.

### F4 — medium / open — Gateway request logging still exposes OAuth code/state query values in its status field.

Tasks: T11a. Probe A: exit 0; real loopback synthetic callback query appears in captured server logging. GatewayHandler.log_message uses args[0], the complete request line, as status despite separately sanitizing the path field. No account takeover or session-token theft demonstrated.

### F5 — medium / open — The mutation marker accepts arbitrary nonempty values; GET logout neither checks guards nor revokes its session.

Tasks: T11a, T15a. Fresh Probe A: exit 0; wrong X-Flow-Request yields HTTP 200, foreign-Origin GET logout yields 302/cookie removal and the original session token still resolves. server.py tests bool(marker). Origin checks on actual command POST remain effective; no command CSRF bypass is claimed.

### F6 — medium / open — Telegram alerts omit review links, task/cause details and safe inline actions; retry callbacks are unsupported.

Tasks: T14a, T14b. Probe B: exit 0, Telegram retry returns INVALID_COMMAND. Current TelegramSender posts chat_id/text only, notification_for_event appends only REQ; app.py accepts Telegram pause/resume only. Existing four bot tests pass. Alert review/task/cause/buttons remain missing, while /estado pause/resume keyboard is separate.

### F7 — medium / open — The public standalone note command has no laptop dispatcher.

Tasks: T5a. Fresh Probe B: exit 0; real Ledger.submit(note) with commands.dispatch_handlers() returns COMMAND_NOT_IMPLEMENTED. dispatch_handlers advertises no standalone note handler despite COMMANDS and schema listing it. Retry reason/RUN.notes is separate.

### F8 — medium / open — The phone brief form cannot edit acceptance criteria.

Tasks: T15f. Fresh page.tsx editBriefForm still sends only objective/string, without an acceptance criteria editing control. Updated E: both backend field aliases create approved revisions correctly. The remaining criteria UI omission is separate from repaired F41.

### F9 — medium / open — Run-level Reabrir ejecución supplies no task identity to the task-scoped operation.

Tasks: T15d. page.tsx run-level commandForm(reopen) omits taskId; bt_remote_commands.TASK_SCOPED/_member_state and dispatch_run_command require params.task. Fresh Probe C confirms task-scoped reopen succeeds; that repair does not provide an identity for the run-level form.

### F10 — medium / fixed — A plan waiting for approval emits plan.waiting without a scheduler decision.

Tasks: T6. Rechecked on 9ca9ac9ea: Updated Probe B: exit 0; plan_status=review generates exactly plan.waiting without a decision; exact `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py`: exit 0, 12 tests in 0.713 s.

### F11 — medium / open — Gateway restart loses the last snapshot; the separately tested stream hub is not wired into production.

Tasks: T12. Updated Probe B: exit 0; offline runtime returns its cached generatedAt using snapshot_cache, while a new runtime sharing the same database returns None, leading the actual snapshot route to HTTP 503. snapshot_cache is memory-only; main/server do not instantiate StreamHub. The previous newly timestamped empty-model behavior has been replaced, but last-state persistence is still absent. F21 separately records missing production streaming.

### F12 — medium / open — Expired sessions and Telegram outbox/history remain unbounded beyond the required 90 days.

Tasks: T11, T14a, T5. Probe B: exit 0; creating a session leaves an abandoned expired row. SessionStore prunes sessions only when presented. Current notifications.py now has telegram_history with timestamped rows (F43 fixed), but no 90-day prune of that table/outbox; Ledger.rows still reads all rows. No unbounded unwired SSE exposure is alleged.

### F13 — medium / open — The phone receives no stable offline-start timestamp.

Tasks: T12, T15b. Updated Probe B: exit 0; cached generatedAt is retained and laptop is only {online:false}, with no checkedAt or offline-start timestamp. GatewayRuntime.web_snapshot does not expose the persisted outage start or liveness offline_since. The phone still renders LAPTOP SIN CONEXIÓN with no HH:MM. Actual T17 currently fails before offline checks, so no passing integrated timestamp assertion is claimed.

### F14 — medium / fixed — Laptop-side redaction handles the previously missed provider assignments and bearer authorization text.

Tasks: T7, T6. Rechecked on 9ca9ac9ea: Updated Probe B: exit 0; OPENAI_API_KEY assignment and Authorization: Bearer synthetic values are both removed. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py`: exit 0, 3 tests in 1.573 s, plus the 12 event tests. Quoted JSON/database-string credentials remain separate F56.

### F15 — medium / fixed — The local panel implements inherited systemd listener activation/reload.

Tasks: T9. Rechecked on 9ca9ac9ea: `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py`: rerun exit 0, 27 tests in 1.996 s, including inherited socket/listener activation and enabled-unit tests. Initial run had one process-group disappearance assertion failure (26/27); a separate owned-process diagnostic then found leader exit -9, group gone and child reaped. `test_page*.py`: exit 0, 43 tests in 11.465 s. No systemd service was touched; the earlier timing failure is retained as a check limitation.

### F16 — medium / open — The phone discards uncertain command envelopes and generates a new key on resubmission.

Tasks: T15d. Fresh page.tsx checks response.ok, labels UNKNOWN_OUTCOME HTTP 503 Rechazado, and retains history summaries rather than an exact replayable envelope/key; form submitters always call crypto.randomUUID(). Server at-most-once remains valid for a reused key; no duplicate effect through a specific ABA sequence was reproduced, so severity stays medium.

### F17 — low / open — The public command schema differs from production command families, fields and key limits.

Tasks: T3. Fresh schema syntax commands exit 0 only. command.schema.json omits answer-decision, expects singular answer/route text/edit brief; actual phone sends answers/round, route object and field/value. Fresh Probe B rejects a 121-character ledger key despite schema maximum 128. This is contract mismatch, not proof of arbitrary execution.

### F18 — medium / open — The required web verification fails the 360 px browser assertion.

Tasks: T15. `cd remote/web && npm run verify` twice exits 1: lint/typecheck pass, 13/14 tests pass, Chromium real panel test fails at tests/panel-browser.test.mjs:165 with 366 !== 360 (window.innerWidth). Durations 21.730 s and 13.657 s for node tests. Production build succeeds separately during T17. Restore R14 viewport/overflow behavior with the existing browser assertion intact.

### F19 — high / fixed — The integrated phone app compiles, typechecks and builds without the previous overlapping declarations.

Tasks: T15a, T15c, T15d. Rechecked on 9ca9ac9ea: `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` compiles/typechecks and completes the optimized Next.js 15.5.28 production build (build subprocess exit 0) before failing in its feed assertion (F2). `cd remote/web && npm run verify` also passes lint and strict typecheck before the independent browser-width failure F18. No duplicate declaration/type error remains.

### F20 — high / fixed — The phone accepts the real gateway login session dialect.

Tasks: T15a. Rechecked on 9ca9ac9ea: Probe A: exit 0, real gateway session returns HTTP 200 {login:dav033}. Both current `npm run verify` invocations reach and pass the Chromium sessionContractObserved assertion at line 158, selected review and login-dependent render checks before failing width at line 165 (F18). Source load accepts login=dav033. No deployed OAuth claim.

### F21 — medium / open — Production gateway still serves neither SSE route; tested StreamHub remains disconnected.

Tasks: T12, T6, T15b. Fresh Probe A: exit 0; authenticated GET events/stream?after=abc and GET events each return 404. Full server.py/main.py/app.py contain no production stream route/instance; phone opens events/stream. Passing stream unit tests exercise the isolated hub. Five-second phone polling does not restore the missing feed.

### F22 — medium / fixed — A completely filled example configuration starts parsing; the prior mandatory-blank allegation is superseded.

Tasks: T16. Rechecked on 9ca9ac9ea: Updated Probe B: exit 0; every example key is filled with synthetic values and GatewayConfig/OAuthConfig parse 172.20.0.1:8790. `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 16 tests, one Caddy skip. Missing mandatory config is still rejected; blank optional overrides are not a demonstrated compliant-install failure.

### F23 — medium / fixed — Command-history compilation and the production keyed history endpoint are restored.

Tasks: T4a, T15d. Rechecked on 9ca9ac9ea: Updated Probe C: exit 0; real GatewayRuntime/LaptopClient/keyed HTTP returns commands/nextCursor. Exact `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py`: exit 0, 7 tests in 8.205 s, including real stored history and cursor checks. Web lint/typecheck passes; full web verification still fails F18.

### F24 — high / fixed — Wheel and sdist include the actual edit and route-pin implementation modules.

Tasks: T8, T8a. Rechecked on 9ca9ac9ea: Expanded Probe P: exit 0; built wheel/sdist include bt_remote_edit.py and bt_route_pins.py, wheel also includes bt_remote_snapshot.py/bt_remote_preconditions.py; isolated -I imports of all four exit 0. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py`: exit 0, 12 tests including installed real dispatch. This covers the newly split snapshot module as well as recovery.

### F25 — medium / fixed — The failed-task link consumes the selected real review attempt instead of only a static fixture.

Tasks: T15c. Rechecked on 9ca9ac9ea: Both current `cd remote/web && npm run verify` invocations pass the real Chromium selected-review URL/hash and selected failed-attempt content assertions before the later width failure (F18). Probe C: exit 0, real rejected attempt is projected; `test_remote_review.py`: exit 0, 3 tests. Review link and component read the selected attempt, not solely a fixture.

### F26 — medium / open — Reopen/retry now work in the same tab, but ready recovery controls disappear after reload or in another tab.

Tasks: T15f, T15d. Updated C: exit 0; real task reopen moves recovering -> ready and pinned ops.retry succeeds. Source page.tsx still gates recovery on recovering/reopenedForRecovery, with reopenedTasks only an in-memory useRef. Reload/new tab loses the ready task controls. The source-level ready-state fixture test passes before the browser-width failure, but it does not prove a reload of a real producer snapshot. F41/F42 are now independently fixed.

### F27 — low / open — Command limits remain shared by owner login across sessions instead of per session.

Tasks: T11a. Current server.py uses authenticated login as the commands/challenges rate bucket, sharing quota between all dav033 sessions; exact auth/guard tests pass (3/7). This is stricter than R17 but not an authentication bypass; shared anonymous login availability remains F47.

### F28 — high / fixed — Distinct-key concurrent preconditions serialize with the remote ledger effect.

Tasks: T5. Rechecked on 9ca9ac9ea: Probe D: exit 0; two distinct-key concurrent pause submissions produce one effect, one OK and one STALE_PRECONDITION, with two audit rows. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py`: exit 0, 29 tests in 0.238 s.

### F29 — medium / open — The restored snapshot still loses run life-sign/revision fields and reads plan criteria from the wrong task level.

Tasks: T4a. Updated C: real snapshot contains one run and one plan. Updated E projects a real r3 task with nonempty frozen acceptance_criteria yet plan task acceptanceCriteria=[]: bt_planstatus stores criteria under task.detail, while bt_remote_snapshot reads task.acceptance_criteria. Runs expose lastActivityAt and attempts last_activity_at, while the phone reads lastSeenAt/updatedAt; run/task revision is absent, so run brief preview lacks the next revision. Plans, rounds and decisionRequests are now collected; the earlier blanket missing-model claim is withdrawn. State-only preconditions remain permitted; no new ABA exploit is asserted.

### F30 — medium / open — Stalled-attempt notifications start after 15 minutes rather than the required more than 10 minutes.

Tasks: T6. Fresh Probe B: exit 0; live attempt has no attempt.stalled at +660 s and does at +901 s. bt_remote_events.STALL_SECONDS=15*60 conflicts with SPEC R10. The emitted text says more than 10 minutes but the threshold does not.

### F31 — low / fixed — The historical post-expiry SSE continuation is unreachable because production streaming was removed.

Tasks: T11, T12. Rechecked on 9ca9ac9ea: Probe A: exit 0; both authenticated candidate SSE routes return 404 and server.py has no streaming loop. This supersedes the old session-expiry continuation exposure; missing streaming is open F21. Recheck expiry whenever streaming is restored.

### F32 — high / fixed — The gateway preserves the phone route_id selector and selected model/account pin.

Tasks: T13. Rechecked on 9ca9ac9ea: Probe C: exit 0; phone route_id, model and account survive _ledger_command, real keyed HTTP/ledger and ops.retry; selected pin persists and ready task retry succeeds. Only candidate availability and process start/stop are stubbed. Exact gateway test_commands.py: exit 0, 11 tests; laptop test_remote_recovery.py: exit 0, 12 tests.

### F33 — high / fixed — The gateway preserves phone round/answers and edited field/value.

Tasks: T13. Rechecked on 9ca9ac9ea: Probe C: exit 0, actual round/answers reaches its round file and returns OK/answered; params retain field=objective/value. Updated Probe E: exit 0, exact public phone objective and acceptance_criteria travel through GatewayRuntime/LaptopClient/keyed HTTP/ledger/real dispatcher and freeze/rebase r2/r3. No state-reader mock; only process start/stop and lock directory are isolated.

### F34 — medium / fixed — Both frozen notification and delivery test files are restored and execute.

Tasks: T14, T14a. Rechecked on 9ca9ac9ea: `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py`: exit 0, 3 tests in 0.006 s; same command with test_telegram_send.py: exit 0, 3 tests in 0.004 s. Dedupe/restart/active-outage and exponential backoff/expiry/timestamped history run. Updated N/T independently recheck behavior.

### F35 — high / fixed — The real laptop snapshot now passes the exact phone parser for a nonempty runs list.

Tasks: T4a. Rechecked on 9ca9ac9ea: Updated Probe C: exit 0; real bt_remote_snapshot producer -> keyed HTTP/LaptopClient -> runtime cache/web_snapshot -> installed TypeScript exact page.tsx parseSnapshot yields one nonempty run and one plan. Producer retains reqId/status alongside req/state. Seven remote API tests pass. Missing run metadata/plan criteria remain F29.

### F36 — high / fixed — Production keyed command-history, quotas and routes read routes are restored.

Tasks: T4a. Rechecked on 9ca9ac9ea: Updated Probe C: exit 0; real runtime/LaptopClient/keyed HTTP supplies commands/nextCursor, accounts/checkedAt and routes. Only quota/candidate providers supply synthetic data. Seven exact remote API tests pass. F44 still records the quota consumer dialect mismatch.

### F37 — medium / open — Exhaustion gating is restored, but eventual exhaustion retrospectively alerts for earlier retryable failures.

Tasks: T6. Updated Probe H: exit 0, one failure with retries remaining now emits no alert and a genuinely exhausted current attempt emits one. New Probe AB: exit 0; once task attempts_used/max_attempts=3 and remaining=0, build_events applies these task totals to a1/a2 history as well as current a3 and emits three distinct failure events. Thus the original direct gating exposure is repaired, but earlier retryable attempts acquire false exhaustion alerts later. Exact event tests pass but cover only one failed attempt. Preserve exhaustion gating while restricting notification to the actual terminal exhaustion event.

### F38 — medium / fixed — Real structured HTTP INVALID_CURSOR now reaches the gateway cursor-reset branch.

Tasks: T13, T12. Rechecked on 9ca9ac9ea: Probe G: exit 0; real HTTP 400/INVALID_CURSOR reaches runtime reset branch, event_cursor becomes empty. Twelve exact remote event tests include actual keyed-client cursor recovery and subsequent queue insertion; gateway test_stream.py also passes 8 tests.

### F39 — medium / open — HTTP 200 for failed command effects still makes the phone clear forms and treat failed reopen as successful.

Tasks: T13, T15d. Fresh updated Probe G: exit 0; authenticated gateway receives FAILED/ROUTE_UNAVAILABLE and returns HTTP 200. server.py status map omits ROUTE_UNAVAILABLE, EFFECT_FAILED, STATE_UNAVAILABLE and COMMAND_NOT_IMPLEMENTED. page.tsx checks response.ok before setting reopenedTasks and clearing forms.

### F40 — medium / open — The upstream client misclassifies ambiguous success and known refusal, and lets truncated success escape the runtime.

Tasks: T13. Probe I: exit 0; real accepted POST returning HTTP 200 invalid JSON becomes FAILED/LAPTOP_UNAVAILABLE, while synthetic URLError(ConnectionRefusedError) becomes UNKNOWN_OUTCOME because OSError is caught first. I2: exit 0; actual loopback truncated HTTP 200 with Content-Length 100 and two response bytes raises uncaught http.client.IncompleteRead from GatewayRuntime.submit_command. No duplicate effect is claimed; ordinary UpstreamError is caught, so not every transport failure crashes a handler.

### F41 — high / fixed — The edit dispatcher accepts the actual phone objective and acceptance_criteria field aliases.

Tasks: T8a. Rechecked on 9ca9ac9ea: Updated Probe E: exit 0; exact public phone envelope is relayed through real keyed HTTP/ledger/state reader and creates r2 objective then r3 acceptance criteria; real freeze marks approval and ops.bound_plan reports r2/r3 after rebase. Exact `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py`: exit 0, 12 tests in 4.180 s. Only process stop/resume and lock directory are isolated; no real agent launches.

### F42 — high / fixed — Working-plan drift is refused and a rejected approval restores the original working bytes.

Tasks: T8a. Rechecked on 9ca9ac9ea: Updated Probe E: exit 0; valid plan first freezes/rebases r2/r3 via phone aliases and actual keyed HTTP/ledger. Unrelated T2 drift then returns FAILED/PLAN_DRIFT without changing bytes or frozen r3. After restoring r3 and changing PLAN.md status to review, real approval returns FAILED/PLAN_NOT_APPROVED; PLAN.json bytes and latest revision remain unchanged. Exact test_remote_recovery.py: exit 0, 12 tests. Crash recovery or simultaneous unrelated local writers were not demonstrated safe by this check.

### F43 — medium / fixed — Telegram delivery restores one-hour expiry, exponential backoff and timestamped per-attempt history.

Tasks: T14a. Rechecked on 9ca9ac9ea: Updated Probe N: exit 0; two-hour-old item drops without send; failed send at t=100 schedules t=105 then drops on expiry, history records dropped/retry/dropped with timestamps. Exact `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_send.py`: exit 0, 3 tests, including 5xx backoff, terminal expiry and durable history.

### F44 — medium / open — The restored quota endpoint returns an array of windows that the phone discards.

Tasks: T4a. Fresh Probe Q: exit 0; actual keyed route_get /quotas with one synthetic account/five_hour window returns windows=[{window,usedPercent,resetsAt}], observedAt string. Exact QuotasPanel parser transpiled with installed TypeScript calls record(account.windows), which rejects arrays: parsed account count is 0. Phone expects a windows object with used_percent/resets_at and numeric observedAt. Restore compatible projection or normalize both dialects; mock browser data currently hide the mismatch.

### F45 — medium / fixed — The liveness entrypoint fixture now includes its OAuth settings and passes.

Tasks: T10. Rechecked on 9ca9ac9ea: `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py`: exit 0, 5 tests in 11.017 s, including the production entrypoint with all required synthetic OAuth settings. No real provider credentials used.

### F46 — medium / open — Phone cancel/delete plan actions require a challenge ID the interface never obtains or displays.

Tasks: T15d. Fresh source inspection page.tsx: buttons disabled unless confirmation text is nonempty and typedReq matches; user must enter Id del reto. sendCommand only auto-fetches a challenge when challengeId is absent, but these forms require it present. No UI requests/displays an ID for copying. Approve/launch auto-challenge behavior remains valid. ; normal forms need the same server-issued challenge flow.

### F47 — medium / open — Anonymous callers behind Caddy share a login throttle and can exhaust the owner login bucket.

Tasks: T11a. Fresh Probe L: exit 0; six synthetic forwarded client addresses reaching one proxy socket receive 302,302,302,302,302,429. server.py keys both login-start and callback buckets on client_address[0]; deployed Caddy is the common upstream peer. An unauthenticated requester can keep the shared five-per-minute start bucket full. Do not trust arbitrary public forwarded headers; derive identity only at the trusted proxy boundary.

### F48 — low / open — Runbook claims the gateway rejects keys shorter than 24 characters, but gateway config checks only nonempty.

Tasks: T16. Source config.py has no length check; the passing test_upstream_client_uses_configured_timeout calls GatewayConfig.from_env with a short synthetic key. Runbook step 2 says the gateway refuses shorter keys. Probe B confirms fully filled config succeeds, not key-strength validation. this documentation/config discrepancy; the laptop serve-remote startup length guard remains separate.

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

Tasks: T6. Rechecked on 9ca9ac9ea: Updated Probe R: exit 0; gateway consumer using actual _observe/build_events/page receives late stall and round behind their old occurredAt timestamps and advances the saved v2 sequence. Exact `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py`: exit 0, 12 tests, including real route_get -> collect -> persistent observation store -> page across late stall/decision/round and identical-ID replay. No timestamp-only ordering is assumed.

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

### F61 — high / open — Blocked-event dedupe keys collide across runs that reuse the same attempt id.

Tasks: T6. New Probe AA: exit 0; two real independent M1 SQLite runs each allocate att-0001. build_events emits two attempt.blocked events for demo/REQ-001 and demo/REQ-002 with identical id/dedupeKey because identity is only attempt.id. Real NotificationOutbox retains one row. Durable _observe also keys by id, so the second run loses its required owner alert. Include project/REQ/task in blocked identity; no foreign-user exploit is alleged.

### F62 — high / open — Failure reviews identify an attempt globally even though attempt ids are local to a run.

Tasks: T7. New Probe AA: exit 0; real independent M1 runs demo/REQ-001 and demo/REQ-002 both have failed att-0001 with distinct causes. Actual _failure_review(att-0001), using real run discovery and attempt facts, returns REQ-001 cause; the phone selecting REQ-002 sends the same /attempts/att-0001/review URL and labels that response with its selected REQ/task. The route accepts no run identity, so it cannot choose REQ-002 evidence and may instead return 404 if the first match is not failed. Namespace the API/query by run and validate the selected target. Same owner scope; no cross-user disclosure is claimed.

### F63 — high / open — A newly created question round on an old plan is immediately dropped as expired before any Telegram send.

Tasks: T6. New Probe AC: exit 0; actual bt_rounds.new_round creates an open round now on a fixture whose PLAN.md timestamp is two hours old. Real plans_payload and feed.collect assign the plan updated_at to round.waiting instead of the round creation time. Actual GatewayRuntime._poll_events -> NotificationOutbox.deliver_due records dropped/expired at attempt 0, sender receives nothing. A fresh required R10 owner event is therefore permanently lost even though its cursor is delivered (F55 fixed). Preserve truthful event creation time and restored message expiry; do not undo the one-hour drop.

### F64 — medium / open — The routes endpoint lists unknown-quota routes as available while retry refuses those same candidates.

Tasks: T8. New Probe AD: exit 0; one synthetic candidate with valid authorization/runtime/source and quota_status=unknown is listed available by actual bt_remote_recovery.route_options, but actual bt_route_pins.available with identical candidate/route returns []. The former checks quota != exhausted; the latter requires quota == available. No actual account/quota source was read. Use the same availability rule; refusal is safe but contradicts the selectable route list.

### F65 — medium / open — The local panel cannot start on Linux without systemctl after the new ownership guard.

Tasks: T9. New Probe AE: exit 0; with Linux, no running panel and subprocess.run raising FileNotFoundError for missing systemctl, actual ensure_server treats _unit_enabled as true then tries systemctl --user restart and propagates FileNotFoundError, with zero detached starts. This changes the existing systemd-less startup path under R18. Only subprocess/platform boundaries are stubbed; no host service is started/stopped. Keep the enabled-unit ownership guard while distinguishing unavailable systemctl from an enabled service.

## Frozen acceptance coverage and handoff

| Requirement | Current disposition |
|---|---|
| R1/R2/R3/R16/R17 | OAuth/key/isolation/challenge guards and kit checks run; logging F4, marker/logout F5, retention F12, session throttle F27, proxy throttle F47, short-key claim F48, empty bind F54 and callback Unicode F60 remain. No real secret/deployment check is claimed. |
| R4/R7 | Actual snapshot parses, plans/rounds/decisions are restored; metadata/criteria F29, restart cache/time F11/F13, stream F21, inline delivery F51 and non-probe outage F53 remain. |
| R5/R6/R8/R13 | Real reopen/pinned retry, answer round and owner edit/freeze/rebase pass C/E; drift/rollback F41/F42 repaired. Note F7, criteria UI F8, run reopen F9, retry envelope F16, reload controls F26, effects HTTP F39, exception handling F40, manual challenge F46, malformed native command F49 and route-list mismatch F64 remain. |
| R9 | Four review sections/actual selected rejection and bounded artifacts work, but global attempt identity F62 is high/open. Quoted text sanitization F56 remains. |
| R10/R11/R12 | Exact notification/delivery/bot checks now execute; F34/F43/F45/F55 repaired. Alert content F6, threshold F30, historical exhaustion F37, bot dialect F50, lost command-induced outage F53, first-start/lag F57, quota condition F58, sequential failure dedupe F59, cross-run blocked collision F61 and lost fresh-round expiry F63 remain. |
| R14/R15 | Production compiles and other mock checks run; actual 360 px check fails F18. Quotas F44 and history/failure handling remain documented; real PWA/targets unrun. |
| R18/T17 | Local page suites and final platform rerun pass; initial platform timing failure retained. Systemd-less local-panel regression F65 remains. T17 fails before its advertised integrated scenarios (high F2). |

Return **T17 for F2**, **T6 for F61/F63**, and **T7 for F62**. Do not reopen the corrected F41/F42/F55 or undo
expiry, retry-budget filtering, topology, installed-module, forwarded-field and ledger fixes. In particular, repair
the E2E fixture/assertions instead of reintroducing false exhaustion events. Keep every medium/low issue recorded
until its owning task changes or the owner explicitly accepts it. Further audits must recheck the whole integrated
tree; this report and the other provider's static receipt are observations, not the independent gate's verdict.

## Historical receipts and adjudications

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
  challenge=runtime.issue_challenge({'target':'demo/REQ-001','typedReq':'REQ-001'})
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
state['runs'][0]['tasks'][0].update(attempts_used=3,retry_budget_remaining=0)
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
  challenge=runtime.issue_challenge({'target':'demo/REQ-001','typedReq':'REQ-001'})
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
 flow={'flow':[{'id':'flow-1','kind':'state_change','run':'demo/REQ-001','task':'T1','at':stamp,'data':{'state':'failed','attempt':'a1','retry_budget_remaining':0}}]}
 first_events=feed._observe(pathlib.Path(tmp)/'dedupe',feed.build_events(flow));assert len(first_events)==1
 last=first_events[0]['cursor']
 later=copy.deepcopy(flow);later['runs']=[{'project':'demo','req_id':'REQ-001','tasks':[{'id':'T1','retry_budget_remaining':0,'attempt':{'id':'a1','state':'failed','ended_at':'2026-10-20T00:00:01Z'}}]}]
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

Observed: the persisted observation cursor delivers late stall/round events; quoted synthetic credentials still survive both sanitizers. First-start history is sent, but a continuous outage now retains generation 1 and is not resent across restart. One exhausted account triggers despite another being available; a sequential flow/state failure still acquires two keys. Unicode state disconnects one callback. These are deterministic probes, not deployed incidence measurements.

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
  review=api._failure_review(ids[0]);print('AA ambiguous review',review)
  assert review and any(run['req_id'] not in str(review['cause']) for run in rows)
 events=feed.build_events({'runs':[{'project':'demo','req_id':req,'tasks':[{'id':'T1','attempt':{'id':ids[0],'state':'blocked'}}]} for req in ('REQ-001','REQ-002')]})
 assert len(events)==2 and events[0]['dedupeKey']==events[1]['dedupeKey']
 out=NotificationOutbox(':memory:')
 for e in events:out.enqueue(*notification_for_event(e))
 count=out._db.execute('SELECT COUNT(*) FROM telegram_outbox').fetchone()[0]
 print('AA two blocked runs outbox rows',count);assert count==1;out._db.close()
 state={'runs':[{'project':'demo','req_id':'REQ-003','tasks':[{'id':'T1','attempts_used':3,'max_attempts':3,'retry_budget_remaining':0,'attempt':{'id':'a3','state':'failed'},'history':[{'id':'a1','state':'failed'},{'id':'a2','state':'failed'}]}]}]}
 ev=feed.build_events(state);print('AB task finally exhausted failure alerts',len(ev));assert len(ev)==3
 import bt_plans_api,bt_rounds,time
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
 print('AC new open round from two-hour-old plan',[(e['type'],e['occurredAt']) for e in events],rt.outbox.history(),sent)
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

## Final artifact checks

Final run: all **18 documented Python reproduction blocks exit 0**; all 18 also compile in memory. Three frozen
`test -s remote/docs/audit.md` invocations exit 0. Ledger validation passes schema `audit-findings/1`, 65 unique IDs,
valid frozen task references, enum/status checks, evidence with command/results for every fixed finding, zero
accepted risks, and exact current finding-heading/verdict parity with this report. Both artifacts contain zero
conflict markers. `git diff --check` and the allowed-path assertion pass: changed paths are exactly the report and
ledger, with no nonignored untracked files. Implementation/tests/configuration match HEAD.

These artifact results cannot satisfy the unresolved all-high-fixed criterion. F2/F61/F62/F63 remain high/open;
only the independent checker decides the task outcome. No finding is accepted on the owner's behalf.
