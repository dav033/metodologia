# Independent security and specification audit — T18

**Rework required: high findings F41 and F42 (T8a) remain open.**
The criterion “Confirmed high findings are fixed” is not met. This is a read-only audit: prerequisite owners must
fix those results. Only this report and `audit.findings.json` change; no risk is accepted and this task does
not declare an independent verification verdict.

Audited tree: `85f4fe33d` (HEAD at entry), 2026-10-21, America/Bogota. Primary auditor: OpenAI Codex.
A fresh independent Anthropic Claude Sonnet 5.5 review is adjudicated below; it does not replace the primary audit.

Ledger: **54 findings, 19 rechecked fixed/superseded exposures, 35 open (2 high, 29 medium, 4 low), 0 accepted**.

## Reconciliation and scope

Opened both supplied artifacts before editing. Initial `git status --short` was clean and neither file contained
conflict markers, despite the carry-forward warning. Relative to the supplied earlier result
`b3de1b8cec5d54bfdb06a19fe9165a84c9983caa`, implementation changes occupy five paths: Caddyfile, gateway env
example, kit tests, runbook and the event generator. Preserve both intents: the Caddy upstream and explicit bind
are now corrected (F1 fixed), while earlier edit-boundary findings F41/F42 reproduce unchanged. The event-generator
change only renames variables; it does not fix the 15-minute stall threshold F30 or retry-exhaustion semantics F37.
All F1–F48 identities are retained; independently confirmed F49–F54 are added. No source, tests or configuration change.

Read the supplied attempt outcomes #11–#16 and reachable prior ledgers at `13d914a6c`, `15f1a318f`, `088cefb37`,
`81a29c39c`, `0af07a73e`, `108efc35f`, `f674c6a29` and `b3de1b8ce` before editing. Raw m6 URI receipts and
the ten omitted attempts are unavailable. Read the full SPEC, frozen PLAN.md and every PLAN.json objective,
acceptance criterion and verification command. Historical passes are not current evidence.

Scope: laptop key/listener/local-panel isolation, native validation, ledger/challenge/replay/concurrency and recovery;
OAuth/session/Origin/limits/logging; producer-to-consumer snapshot/review/feed boundaries; gateway cache/stream/client;
notification delivery and bot; installed distributions, phone UI and kit. T19 is downstream, not claimed implemented.
Tests and probes use temporary state and synthetic credentials. No real project is mutated or agent launched; no
credential file, live host, real account/quota source, SSH or deployment is accessed. Existing gateway tests start
Telegram polling with synthetic test credentials and emit HTTPError warnings; this is not real delivery evidence.
The new bind probe mocks the server constructor rather than opening a wildcard listener. Audit notes remain here,
within the two-artifact boundary, rather than modifying bitácora or other worktrees.

## Fresh verification

Python 3.14.7 and Node 24.21.0; Python 3.12 unavailable. First installed the existing lockfile with
`cd remote/web && npm ci --offline`: exit 0, 320 packages; lockfile unchanged. Later checks neither install
dependencies nor write inside node_modules. Web verification, kit browser check and E2E builds ran sequentially.
Combined laptop and gateway discovery set BITACORA_ROOT to an empty TemporaryDirectory before imports.

| Command / execution | Current result |
|---|---|
| Isolated `cd skill/scripts && python -m unittest discover -s tests -p 'test_remote_*.py'`, plus `test_platform.py` and `test_page*.py` combined | Exit 0; 128 tests in 22.555 s, 0 skips: 62 remote, 23 platform, 43 page. Installed wheel/sdist/dispatch, revisions and concurrency execute. |
| `cd skill/scripts/bt_scheduler_core && python -m unittest discover -s tests -p test_operations.py` | Exit 0; 18 tests in 0.758 s. |
| Isolated `cd remote/gateway && python -m unittest discover -s tests -p 'test_*.py'` | Exit 1; 42 tests in 17.098 s, 1 failure: liveness entrypoint returns 2 because its fixture omits OAuth configuration (F45). |
| `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py` | Exit 1; 5 tests in 5.512 s, same F45 failure. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` | Exit 5; 0 tests, NO TESTS RAN (F34). |
| `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_send.py` | Exit 5; 0 tests, NO TESTS RAN (F34). |
| `cd remote/web && npm run verify` | Exit 0; lint, strict typing, 14/14 tests in 45.821 s, 0 skipped/cancelled, optimized production build. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | Exit 0; 16 tests in 6.688 s, 1 skipped: caddy unavailable. Chromium OAuth cookie check executes; corrected topology assertions pass F1. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 0; 1 test in 19.069 s, production build/fake owner and foreign OAuth/cancel/stale/offline/fake Telegram. False exhaustion remains F37. |
| `python -m json.tool remote/contract/command.schema.json` and event schema equivalent | Each exit 0; syntax only. |
| All 13 retained Python probes A/B/D/C/G/H/I/P/E/N/Q/L/J | Each exit 0; current observations reproduce, including defects. Reproducer success is not product acceptance. |
| New native HTTP probe V and grouped provider probes W/Y/Z/O | Each exit 0; native disconnect, /estado dialect, inline send scheduling, lost outage generation, empty bind and five-second default reproduced. |
| Three frozen `test -s remote/docs/audit.md` checks, ledger validation, marker scan, path restriction and `git diff --check` | See final artifact checks. |

Not run: Python 3.12, actual Caddy validation/container connectivity, deployed OAuth/Telegram, a real route-selected
agent launch, live Vercel SSE lifetime, PWA installation, exhaustive 44 px touch targets or a live dependency advisory
scan. npm's offline install summary is not an independent security scan. Existing HTTPError/SQLite cleanup
ResourceWarnings are retained. No failing or missing check is described as passing.

## Fresh independent other-provider review

Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
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

## Findings and verdicts

### F1 — high / fixed — The Caddy upstream and documented gateway bind now match the frozen container-to-host topology.

Tasks: T16. Rechecked on 85f4fe33d: `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 16 tests in 6.688 s, 1 skip (Caddy unavailable). remote/deploy/Caddyfile:15 now targets 172.20.0.1:8790 and runbook steps 2/5 explicitly require GATEWAY_BIND=172.20.0.1. Fresh Probe B: exit 0, filled GatewayConfig/OAuthConfig parse the matching 172.20.0.1:8790 bind. Container network connectivity and actual Caddy validation were not exercised; first-install/reload instructions remain the separate F3.

### F2 — high / fixed — The frozen built-web E2E command completes in the current tree.

Tasks: T17. `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py`: exit 0; 1 test in 19.069 s, production build succeeds, fake owner/foreign OAuth, ledger cancellation/stale rejection, offline cache and fake Telegram execute. It does not hydrate the actual phone against every production model; F37 records its false retry-exhaustion alert.

### F3 — medium / open — The restored runbook deploys and restarts before installing the service on a fresh host.

Tasks: T16. remote/docs/runbook.md steps 3/4 call deploy.sh before installing the unit; deploy.sh:27 unconditionally restarts under set -e. Fresh local synthetic missing-unit simulation: deploy exit 5 with current already switched; rollback --dry-run exit 2 without previous release; deploy --dry-run exit 0. Kit checks pass but do not check this order. Provider finding 2 confirms. Reorder first-install steps and document containerized Caddy reload/rollback rather than host systemctl reload caddy.

### F4 — medium / open — Gateway request logging still exposes OAuth code/state query values in its status field.

Tasks: T11a. Fresh report Probe A (`python` heredoc): exit 0; real HTTP synthetic callback query appears in captured server logging. server.py:38 uses args[0], which is the complete request line, as status. The provider mistakenly rejected this based on path sanitization; the real HTTP reproducer overrides that rejection. No account takeover or session-token theft was demonstrated.

### F5 — medium / open — The mutation marker accepts arbitrary nonempty values; GET logout neither checks guards nor revokes its session.

Tasks: T11a, T15a. Fresh Probe A: exit 0; wrong X-Flow-Request yields HTTP 200, foreign-Origin GET logout yields 302/cookie removal and the original session token still resolves. server.py:189-192 tests bool(marker). Provider findings 7/11 confirm. Origin checks on actual command POST remain effective; no command CSRF bypass is claimed.

### F6 — medium / open — Telegram alerts omit review links, task/cause details and safe inline actions; retry callbacks are unsupported.

Tasks: T14a, T14b. Fresh Probe B: exit 0, Telegram retry returns INVALID_COMMAND. Current notifications.py TelegramSender posts only chat_id/text; notification_for_event appends only REQ. app.py allows Telegram pause/resume only. telegram_bot.py has /estado pause/resume keyboard separately; it does not supply required alert ver/reintentar controls. Existing bot tests pass within the 42-test gateway run.

### F7 — medium / open — The public standalone note command has no laptop dispatcher.

Tasks: T5a. Fresh Probe B: exit 0; real Ledger.submit(note) with commands.dispatch_handlers() returns COMMAND_NOT_IMPLEMENTED. dispatch_handlers advertises no standalone note handler despite COMMANDS and schema listing it. Retry reason/RUN.notes is separate.

### F8 — medium / open — The phone brief form cannot edit acceptance criteria.

Tasks: T15f. Fresh source inspection remote/web/src/app/page.tsx:370-380 always sends a string and field objective; no criteria editing control exists. Laptop test_http_owner_edit_freezes_approved_revision_and_rebases_real_run passes within the 62 remote tests and exercises criteria arrays, so the missing UI remains distinct from the new brief dialect regression F41.

### F9 — medium / open — Run-level Reabrir ejecución supplies no task identity to the task-scoped operation.

Tasks: T15d. page.tsx:440 run-level commandForm(reopen) omits taskId; bt_remote_commands.TASK_SCOPED/_member_state and dispatch_run_command require params.task. Fresh Probe C confirms task-scoped reopen succeeds; that repair does not provide an identity for the run-level form.

### F10 — medium / fixed — A plan waiting for approval emits plan.waiting without a scheduler decision.

Tasks: T6. Fresh Probe B: exit 0; feed.build_events with a review plan and no decisions emits exactly plan.waiting. Isolated combined laptop discovery: exit 0, 128 tests including all 62 test_remote_*.py cases. collect still includes plans.

### F11 — medium / open — Gateway restart loses the last snapshot; the separately tested stream hub is not wired into production.

Tasks: T12. Fresh Probe B: exit 0; offline runtime returns its cached snapshot, new runtime sharing the database returns None. app.py snapshot_cache remains memory-only; main.py/server.py do not instantiate StreamHub. F21 separately records absent production streaming.

### F12 — medium / open — Expired sessions and Telegram outbox/history remain unbounded beyond the required 90 days.

Tasks: T11, T14a, T5. Fresh Probe B: exit 0; creating a new session leaves the expired abandoned session row. SessionStore prunes expired sessions only on presentation. notifications.py has no retention prune; sent/dropped outbox rows remain indefinitely. Fresh delivery probe also confirms no telegram_delivery_history table after two-hour scenarios. Ledger.rows reads all rows. No unused SSE-queue exposure is alleged.

### F13 — medium / open — The phone receives no stable offline-start timestamp.

Tasks: T12, T15b. Fresh Probe B: exit 0; old generatedAt is preserved but laptop is only {online:false}. app.py/web_snapshot never exposes liveness.offline_since or a wall-clock equivalent; page.tsx renders LAPTOP SIN CONEXIÓN with no HH:MM. E2E passing offline refusal does not establish the missing timestamp.

### F14 — medium / fixed — Laptop-side redaction handles the previously missed provider assignments and bearer authorization text.

Tasks: T7, T6. Fresh Probe B: exit 0; synthetic provider-key assignment and bearer text become [REDACTED]. Isolated laptop suite: exit 0, 128 tests including all 62 remote tests and failure-review redaction. Recursive snapshot/event/review redaction remains. No exhaustive secret-scanning claim.

### F15 — medium / fixed — The local panel implements inherited systemd listener activation/reload.

Tasks: T9. Isolated combined discovery of test_remote_*.py, test_platform.py and test_page*.py: exit 0, 128 tests in 22.555 s, including 23 platform and 43 page tests. Platform activation/listener regressions execute with 0 skips. No real systemd service was restarted.

### F16 — medium / open — The phone discards uncertain command envelopes and generates a new key on resubmission.

Tasks: T15d. Fresh page.tsx:274-329 checks response.ok, labels UNKNOWN_OUTCOME HTTP 503 Rechazado, and retains history summaries rather than an exact replayable envelope/key; form submitters always call crypto.randomUUID(). Provider finding 3 confirms. Server at-most-once remains valid for a reused key; no duplicate effect through a specific ABA sequence was reproduced, so severity stays medium.

### F17 — low / open — The public command schema differs from production command families, fields and key limits.

Tasks: T3. Fresh schema syntax commands exit 0 only. command.schema.json omits answer-decision, expects singular answer/route text/edit brief; actual phone sends answers/round, route object and field/value. Fresh Probe B rejects a 121-character ledger key despite schema maximum 128. This is contract mismatch, not proof of arbitrary execution.

### F18 — medium / fixed — The required web verification succeeds with current round-answer assertions.

Tasks: T15, T15e. `cd remote/web && npm run verify`: exit 0; lint, strict typecheck, 14/14 tests (45.821 s, 0 skipped/cancelled) and optimized production build pass. Tests use mock snapshots/recovery models; F41 and F44 cover production-only mismatches.

### F19 — high / fixed — The integrated phone app compiles, typechecks and builds without the previous overlapping declarations.

Tasks: T15a, T15c, T15d. `cd remote/web && npm run verify`: exit 0, lint/typing/14 tests/production build pass; T17 also builds production successfully. No duplicate refreshCommandHistory or invalid Attempt predicate reproduced.

### F20 — high / fixed — The phone accepts the real gateway login session dialect.

Tasks: T15a. Fresh Probe A: exit 0, actual gateway returns HTTP 200 {login:dav033}. `cd remote/web && npm run verify`: exit 0, including Chromium test deliberately returning that dialect. No deployed GitHub OAuth claim.

### F21 — medium / open — Production gateway still serves neither SSE route; tested StreamHub remains disconnected.

Tasks: T12, T6, T15b. Fresh Probe A: exit 0; authenticated GET events/stream?after=abc and GET events each return 404. Full server.py/main.py/app.py contain no production stream route/instance; phone opens events/stream. Passing stream unit tests exercise the isolated hub. Five-second phone polling does not restore the missing feed.

### F22 — medium / fixed — A completely filled example configuration starts parsing; the prior mandatory-blank allegation is superseded.

Tasks: T16. Fresh Probe B: exit 0; fill every uncommented gateway.env.example key with synthetic/standard values, GatewayConfig.from_env and OAuthConfig.from_env both succeed at 172.20.0.1:8790. Restored runbook explicitly requires those values filled. F1/F3 still block the documented deployment; F48 records the inaccurate minimum-key claim.

### F23 — medium / fixed — Command-history compilation and the production keyed history endpoint are restored.

Tasks: T4a, T15d. Fresh updated Probe C: exit 0; real GatewayRuntime/LaptopClient/keyed HTTP /commands returns commands/nextCursor. Isolated laptop discovery: exit 0, 62 remote tests including test_keyed_read_models_are_served_by_the_real_http_listener with a stored ledger row and cursor checks. Fresh npm run verify exit 0 includes history normalizer/browser assertions.

### F24 — high / fixed — Wheel and sdist include the actual edit and route-pin implementation modules.

Tasks: T8, T8a. Fresh updated Probe P: exit 0; installed_wheel.get builds wheel/sdist, both contain bt_remote_edit.py and bt_route_pins.py, isolated -I imports of both and bt_remote_preconditions exit 0. Isolated laptop discovery: exit 0, 62 remote tests including installed retry/edit dispatch reaching the expected missing-project guard and real HTTP health. This closes packaging only, not edit behavior F41/F42.

### F25 — medium / fixed — The failed-task link consumes the selected real review attempt instead of only a static fixture.

Tasks: T15c. Fresh npm run verify: exit 0 including Chromium selected-review assertions. Fresh Probe C projects the real failed/rejected attempt; current task link includes its attempt hash and review/page.tsx consumes it. All 62 remote tests pass, including real review artifact/redaction tests.

### F26 — medium / open — Reopen/retry now work in the same tab, but ready recovery controls disappear after reload or in another tab.

Tasks: T15f, T15d. Fresh updated Probe C: exit 0; exact phone task reopen travels through real runtime/keyed HTTP/ledger/ops.apply/core from recovering to ready, then real ops.retry returns already ready with the exact pin; only route availability and process starts/stops are stubbed. npm run verify passes the ready-state browser fixture. Remaining source defect page.tsx:168,177-179,303-305,399: reopenedTasks is only an in-memory useRef; after reload/other device a ready task is neither recovering nor reopenedForRecovery, so retry/edit controls vanish. Provider finding 9 confirms. Reduce high to medium for this narrower residual; F41/F42 separately record current blocking edit failures.

### F27 — low / open — Command limits remain shared by owner login across sessions instead of per session.

Tasks: T11a. Current server.py:143 uses authenticated login as command/challenge bucket identity, so all dav033 session tokens share one bucket. Gateway auth/guard tests pass within the 42-test suite. This is stricter than R17; it is not an authentication bypass. F47 is the separate anonymous login availability issue.

### F28 — high / fixed — Distinct-key concurrent preconditions serialize with the remote ledger effect.

Tasks: T5. Fresh Probe D: exit 0; two simultaneous distinct-key commands execute one running-state handler; outcomes OK and REJECTED/STALE_PRECONDITION, two ledger rows. Isolated 128-test laptop suite passes concurrency regression. _EFFECT_LOCK encloses check/reservation/effect/outcome. This is process-local serialization, not a proof against every external scheduler mutation.

### F29 — medium / open — The real snapshot still omits phone life-sign/revision/criteria metadata and planning/round/decision models.

Tasks: T4a. Fresh updated Probe C: exit 0; run fields are active,activeTask,id,lastActivityAt,project,req,reqId,state,status,tasks,title; plans is empty. Full _snapshot does not collect plans/rounds/decisionRequests or revision/criteria. Phone parseSnapshot expects lastSeenAt/updatedAt/activeAttempt, not lastActivityAt/activeTask, so last life sign/revision preview are missing even though F35 parsing now succeeds. State-only preconditions are permitted by R6; no separate ABA race is claimed.

### F30 — medium / open — Stalled-attempt notifications start after 15 minutes rather than the required more than 10 minutes.

Tasks: T6. Fresh Probe B: exit 0; live attempt has no attempt.stalled at +660 s and does at +901 s. bt_remote_events.STALL_SECONDS=15*60 conflicts with SPEC R10. The emitted text says more than 10 minutes but the threshold does not.

### F31 — low / fixed — The historical post-expiry SSE continuation is unreachable because production streaming was removed.

Tasks: T11, T12. Fresh Probe A: exit 0; both candidate authenticated SSE routes return 404. Current server has no production stream wait/write loop. This supersedes the old exposure only; missing functionality remains F21. Session expiry must be rechecked when streaming is restored.

### F32 — high / fixed — The gateway preserves the phone route_id selector and selected model/account pin.

Tasks: T13. Fresh updated Probe C: exit 0; exact phone route object translates to route/model/account, traverses real keyed HTTP/ledger/retry and persists synthetic-route/model/account. Real ops.retry runs on ready; candidate availability and agent/process start are stubbed. Isolated 62 remote tests include pin assignment/unavailability. No real selected-route agent was launched.

### F33 — high / fixed — The gateway preserves phone round/answers and edited field/value.

Tasks: T13. Fresh updated Probe C: exit 0; exact round/answers reaches the real round file and returns OK/answered. The field objective/value reaches the real edit dispatcher unchanged and now fails its new field restriction, separately F41. Isolated 62 remote tests cover owner-approved brief/criteria revisions; gateway command tests cover public field translation. This closes adapter loss only.

### F34 — medium / open — Frozen notification/delivery checks reference absent test files.

Tasks: T14, T14a. Fresh exact `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` and the same command with test_telegram_send.py: each exits 5, Ran 0 tests, NO TESTS RAN. test_telegram_send.py was deleted by the new prerequisites; wildcard discovery cannot cover absent tests. Restore both frozen gates without weakening restart/dedupe, offline-active and delivery behavior.

### F35 — high / fixed — The real laptop snapshot now passes the exact phone parser for a nonempty runs list.

Tasks: T4a. Fresh updated Probe C (report python heredoc): exit 0; fixture real laptop _snapshot -> keyed HTTP/LaptopClient -> GatewayRuntime.web_snapshot -> installed TypeScript transpilation of the exact page.tsx parseSnapshot yields one run. Producer now emits req/state aliases while retaining reqId/status. Isolated 62 remote tests and full npm run verify pass. Remaining missing metadata is F29.

### F36 — high / fixed — Production keyed command-history, quotas and routes read routes are restored.

Tasks: T4a. Fresh updated Probe C: exit 0; real runtime/LaptopClient/keyed HTTP yields commands/nextCursor, accounts/checkedAt and routes. Only quota/candidate data providers return synthetic rows, avoiding real accounts. Isolated 62 remote tests include real history, route validation and quota-unavailable behavior. F44 independently proves the restored quota payload still mismatches its phone parser.

### F37 — medium / open — Failure alerts ignore remaining retries, making the green E2E send a false exhaustion alert.

Tasks: T6, T17. Fresh Probe H: exit 0; attempts_used=1/max_attempts=3 emits attempt.failed and renders Una tarea falló sin reintentos pendientes. Current build_events has no exhaustion filter. Fresh T17 is green with one forced failure but does not assert a genuinely exhausted fixture. Restore exhaustion-aware rules and test both retryable and exhausted failures.

### F38 — medium / fixed — Real structured HTTP INVALID_CURSOR now reaches the gateway cursor-reset branch.

Tasks: T13, T12. Fresh updated Probe G: exit 0; actual loopback laptop HTTP 400 {code:INVALID_CURSOR} through LaptopClient.get_json resets stale-cursor to empty. upstream.py preserves UpstreamResponseError and app.py handles it. The isolated gateway wildcard suite has one unrelated liveness test failure F45; no overall gateway pass is claimed.

### F39 — medium / open — HTTP 200 for failed command effects still makes the phone clear forms and treat failed reopen as successful.

Tasks: T13, T15d. Fresh updated Probe G: exit 0; authenticated gateway receives FAILED/ROUTE_UNAVAILABLE and returns HTTP 200. server.py status map omits ROUTE_UNAVAILABLE, EFFECT_FAILED, STATE_UNAVAILABLE and COMMAND_NOT_IMPLEMENTED. page.tsx checks response.ok before setting reopenedTasks and clearing forms; confirmed by provider finding 8.

### F40 — medium / open — The upstream client misclassifies ambiguous malformed success and known connection refusal.

Tasks: T13. Fresh Probe I: exit 0; real POST accepted then HTTP 200 with invalid JSON becomes FAILED/LAPTOP_UNAVAILABLE, whereas synthetic URLError(ConnectionRefusedError) becomes UNKNOWN_OUTCOME. Runtime catches plain UpstreamError, so provider blanket handler-crash claim is not established for this path. Keep exact key/UNKNOWN_OUTCOME after uncertain execution; IncompleteRead was not tested.

### F41 — high / open — The new edit dispatcher rejects the actual phone objective field, disabling remote brief editing.

Tasks: T8a. Fresh updated Probe C: exit 0 reproducer; actual phone field objective/value + target task + valid real challenge traverses runtime/keyed HTTP/ledger and returns FAILED/EFFECT_FAILED: edit-brief requiere task y field brief o criteria. page.tsx:377 sends objective; bt_remote_edit.py:25 accepts only brief/criteria. Diff from f674c6a29 removed the objective/acceptance_criteria aliases while phone was unchanged. Preserve both dialects and test producer-to-real-dispatch. Provider finding 5 independently confirms the mismatch; typed_req is correctly injected by Ledger and is not an additional defect.

### F42 — high / open — Editing one task silently approves unrelated working-plan drift, and failed edits leave unapproved changes on disk.

Tasks: T8a. Fresh Probe E: exit 0 with a valid classified/frozen plan and real scheduler/runtime binding. Change only working T2 objective without approval; owner edits T1 using supported brief dialect; real freeze/rebase succeeds at r2 and frozen T2 contains the unapproved unrelated change. Change PLAN.md to review then repeat: real PLAN_NOT_APPROVED raises but PLAN.json remains modified at r3 while frozen revision is r2. bt_remote_edit.py:41-54 removed drift/symlink/atomic/lock/rollback guards from earlier implementation. Restore approved-base validation, locking/atomic publish and rollback, preserving current compatibility gate. No external concurrency/crash exploit was needed. Provider finding 6 confirms the design defect.

### F43 — medium / open — Telegram delivery no longer expires messages at one hour or records delivery attempts with timestamps.

Tasks: T14a. Fresh Probe N: exit 0; message enqueued at synthetic t=100 is sent at t=7300; failing another message at t=100 and t=7300 leaves pending with attempts=2. notifications.py has no created_at/expires_at and drops only after 11 failed attempts, not after one hour. SQLite contains only telegram_outbox and gateway_state, no prior delivery history table; status/attempt count remain but per-attempt delivery timestamps/history were removed. Restore age-based drop/history and its missing frozen test (F34).

### F44 — medium / open — The restored quota endpoint returns an array of windows that the phone discards.

Tasks: T4a. Fresh Probe Q: exit 0; actual keyed route_get /quotas with one synthetic account/five_hour window returns windows=[{window,usedPercent,resetsAt}], observedAt string. Exact QuotasPanel parser transpiled with installed TypeScript calls record(account.windows), which rejects arrays: parsed account count is 0. Phone expects a windows object with used_percent/resets_at and numeric observedAt. Restore compatible projection or normalize both dialects; mock browser data currently hide the mismatch.

### F45 — medium / open — The frozen gateway liveness command fails on missing OAuth fixture configuration.

Tasks: T10. Fresh exact `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py`: exit 1, 5 tests/1 failure. test_production_entrypoint_alerts_from_cached_active_run_when_laptop_is_offline clears env and supplies no GITHUB_CLIENT_ID/GITHUB_CLIENT_SECRET/SESSION_SECRET/FLOW_FRONTEND_ORIGIN, so main returns 2 versus asserted 0. Independent wildcard gateway run: exit 1, 42 tests/1 same failure in 17.098 s. Supply complete synthetic config and stub the bot network; do not weaken production auth validation.

### F46 — medium / open — Phone cancel/delete plan actions require a challenge ID the interface never obtains or displays.

Tasks: T15d. Fresh source inspection page.tsx:458-459: buttons disabled unless confirmation text is nonempty and typedReq matches; user must enter Id del reto. sendCommand only auto-fetches a challenge when challengeId is absent, but these forms require it present. No UI requests/displays an ID for copying. Approve/launch auto-challenge behavior remains valid. Provider finding 12 confirms; normal forms need the same server-issued challenge flow.

### F47 — medium / open — Anonymous callers behind Caddy share a login throttle and can exhaust the owner login bucket.

Tasks: T11a. Fresh Probe L: exit 0; six synthetic forwarded client addresses reaching one proxy socket receive 302,302,302,302,302,429. server.py keys both login-start and callback buckets on client_address[0]; deployed Caddy is the common upstream peer. An unauthenticated requester can keep the shared five-per-minute start bucket full. Provider finding 10 confirms. Do not trust arbitrary public forwarded headers; derive identity only at the trusted proxy boundary.

### F48 — low / open — Runbook claims the gateway rejects keys shorter than 24 characters, but gateway config checks only nonempty.

Tasks: T16. Source config.py:37-51 has no length check; the passing test_upstream_client_uses_configured_timeout calls GatewayConfig.from_env with a short synthetic key. Runbook step 2 says the gateway refuses shorter keys. Probe B confirms fully filled config succeeds, not key-strength validation. Provider finding 16 confirms this documentation/config discrepancy; the laptop serve-remote startup length guard remains separate.

### F49 — medium / open — A malformed authenticated native command drops the HTTP connection before validation instead of returning INVALID_COMMAND.

Tasks: T5. Fresh Probe V: exit 0 reproducer. A real loopback POST to bt_remote_api.route_post with synthetic valid gateway key and {idempotency_key:'synthetic-valid-key',command:'pause'} drops the connection with KeyError('target'); the same request without the key returns HTTP 401. bt_remote_commands.fingerprint:264 indexes required fields before validate:268, and Ledger.submit:385-387 catches TypeError/ValueError but not missing-field KeyError. Validate required envelope fields before fingerprinting and return HTTP 400/INVALID_COMMAND. The public gateway fills these keys, so this is native-boundary robustness, not an unauthenticated access bypass.

### F50 — medium / open — Telegram /estado skips every real snapshot run because it reads req_id instead of req/reqId.

Tasks: T14b. Fresh report Probe W/Y/Z/O: exit 0. Production bt_remote_api._snapshot projects a synthetic active run with req/reqId; real TelegramBot._send_status consumes it and sends only {'text':'Ejecuciones activas:'}, with no run or keyboard. telegram_bot.py:140 expects req_id while bt_remote_api.py:147 emits req and reqId. Align the consumer dialect and test an actual projected snapshot; the synthetic snapshot reader is the only substituted data source. Fresh other-provider item 3 independently identifies this mismatch.

### F51 — medium / open — Inline Telegram delivery can block the production five-second liveness polling cadence.

Tasks: T14a, T10. Fresh report Probe W/Y/Z/O: exit 0; GatewayRuntime.poll_once with 20 due messages and a deterministic sender advancing the clock by the default 5-second request timeout consumes 100 simulated seconds while making exactly one health probe. app.py:100 calls deliver_due inline and notifications.py:77-106 sends up to 20 sequential messages before returning. This is a deterministic scheduling reproduction, not a measured real Telegram outage; isolate delivery or give it a budget compatible with the five-second health cadence. Fresh other-provider item 9 corroborates.

### F52 — low / open — The production command deadline defaults to five seconds instead of the specified fifteen seconds.

Tasks: T10, T13. Fresh report Probe W/Y/Z/O: exit 0, GatewayConfig.from_env with required synthetic values and omitted optional overrides returns request_timeout=5.0. app.py:73 passes that same timeout to LaptopClient and upstream.py:79 applies it to command POST. SPEC edge case requires the gateway to time out after 15 seconds. Use a separate 15-second command deadline; the shorter timeout fails safely as UNKNOWN_OUTCOME and does not itself prove duplicate execution. Fresh other-provider item 10 corroborates.

### F53 — medium / open — An offline transition caused by a command or challenge suppresses the required long-offline active-run alert.

Tasks: T10, T13, T14. Fresh report Probe W/Y/Z/O: exit 0. With cached active-run state, three synthetic UpstreamError command failures mark the laptop offline but leave offline_generation=0; a subsequent health poll at offline_since+901 seconds emits no outbox row. Repeated through issue_challenge with the same result. app.py:152/180 discard the transition; only poll_once advances the generation, so _notify_long_offline_with_active_run returns early. Handle every transition through one owner and preserve one alert per outage. Fresh other-provider item 11 corroborates.

### F54 — medium / open — An explicitly empty gateway bind is accepted and passed to the HTTP server as a wildcard address.

Tasks: T10. Fresh report Probe W/Y/Z/O: exit 0. GatewayConfig.from_env and OAuthConfig.from_env accept required synthetic configuration with GATEWAY_BIND=''; create_server passes ('',8790) to the mocked ThreadingHTTPServer constructor (Python IPv4 wildcard bind semantics). No wildcard listener was actually opened. config.py:58 uses get without rejecting the empty value; deploy.sh required-key checks omit GATEWAY_BIND. The runbook correctly instructs 172.20.0.1 (F1 fixed), but malformed production config still fails open at this boundary. Reject empty/wildcard binds or normalize deliberately to the documented private interface. No unauthenticated command bypass is alleged. Fresh other-provider item 14 corroborates.

## Frozen acceptance coverage and dispositions

| Requirement | Current evidence or remaining gap |
|---|---|
| R1/R3 | Owner/foreign fake OAuth, key isolation, installed dispatch/health pass; F1 topology corrected and kit checks pass; actual container connectivity remains unrun. |
| R2/R17 | Auth/Origin guards tested; F4/F5/F27/F47 remain. No command Origin bypass demonstrated. |
| R4 | Real nonempty runs parser now succeeds F35; missing metadata/planning models F29 and production streaming F21 remain. |
| R5/R13 | Real reopen/pinned retry and gateway field/round forwarding repaired; note F7, criteria UI F8, run reopen F9, reload controls F26, edit dialect F41 and unintended approval/failed-write F42 remain. |
| R6/R8 | Same-key replay/challenge/concurrent stale tests pass; native malformed envelope F49, uncertain phone replay F16, command deadline F52 and upstream/public result semantics F39/F40 remain. |
| R7 | Offline E2E/cache/refusal pass; restart cache F11, offline-start timestamp F13 and send-blocked probes F51 remain. |
| R9 | Real selected review projection/link and remote review/redaction pass F25. |
| R10/R11/R12 | Existing bot/dedupe checks and fake alert E2E run; alert controls F6, threshold F30, missing frozen tests F34, false exhaustion F37, delivery-age/history F43, liveness fixture F45, /estado dialect F50 and lost outage alert F53 remain. HTTP cursor reset is repaired F38. |
| R14 | 360 px mock browser, local fonts/theme/build pass; PWA install/touch-target exhaustive checks unrun. |
| R15 | Command history restored F23; quota parsing F44 and retention F12 remain. |
| R16/R18 | Listener/private-env/local-panel checks pass; minimum-key documentation F48, empty gateway bind F54 and kit install/reload order F3 remain. F1 is rechecked fixed. |

Historical rejected/superseded candidates: current build and login dialect failures are not reproduced F18/F19/F20;
installed helper and actual edit/pin modules now import F24; production read routes exist F23/F36. Null confirmation
is validated before strip/encode; no challenge bypass demonstrated. Real task reopen succeeds and ready retry returns
without the old 180-second blocked wait; no failing core reopen claim remains. live._attempt(None) is handled.
Process-local lock scope is stated in F28; no global external scheduler race is asserted fixed. Production SSE
post-expiry continuation is unreachable F31, but this does not satisfy F21. Fully filled example parsing succeeds
F22, with topology now corrected F1 and first-install/reload order still defective F3. Route/round/field forwarding is preserved F32/F33, without claiming
the consumer accepts every forwarded field (F41). Passing report-existence commands cannot establish all high fixed.

## Handoff

Return T8a for F41/F42. Do not reopen corrected T16 topology F1. Keep the restored kit, downstream aliases/read models, packaging fixes and
scheduler ready-state retry; repair their actual remaining boundaries. Rerun end-to-end production producers and
consumers after repairs, not only independent mocks. F49 also records native-envelope validation failure under T5. All open medium/low findings remain recorded for their owners;
none is accepted by this auditor. This audit intentionally leaves implementation unchanged.

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
  snapshot=runtime.web_snapshot()
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
  runtime.snapshot_cache=None;after=runtime.web_snapshot()['runs'][0]['tasks'][0]['state']
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
  result=runtime.submit_command(edit);print('edit real validation',result)
  assert result['status']=='FAILED' and 'field brief o criteria' in str(result)
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
assert any(m and 'sin reintentos pendientes' in m[1] for m in messages)
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
 assert 'bt_remote_preconditions.py' in names
 assert 'bt_remote_edit.py' in names and 'bt_route_pins.py' in names
 print('wheel contains bt_remote_edit.py and bt_route_pins.py')
with tarfile.open(installed.sdist) as archive:
 names={pathlib.Path(p.name).name for p in archive.getmembers()}
 assert 'bt_remote_edit.py' in names and 'bt_route_pins.py' in names
 print('sdist contains both recovery implementation modules')
for name in ['bt_remote_preconditions','bt_remote_edit','bt_route_pins']:
 result=subprocess.run([str(installed.python),'-I','-c',
  f'import sys;sys.path.insert(0,sys.argv[1]);__import__("{name}")',str(installed.site)],
  cwd=installed.work,capture_output=True,text=True)
 print('isolated import',name,'exit',result.returncode)
 assert result.returncode == 0
PY
```

### Probe E — approved-base drift and failed-edit persistence

```bash
python - <<'PYCODE'
import pathlib,os,sys,tempfile,json
from unittest.mock import patch
root=pathlib.Path.cwd();sys.path.insert(0,str(root/'skill/scripts'))
with tempfile.TemporaryDirectory() as tmp:
 os.environ['BITACORA_ROOT']=tmp
 import bt_core,bt_remote_edit as edit,bt_scheduler_adapter as scheduler,bt_scheduler_ops as ops,bt_scheduler_run
 from bt_planner import contract,revisions,sync
 from bt_planner.tests.support import PLAN_MD,classify
 base=pathlib.Path(tmp);rdir=base/'demo/requirements/REQ-001-demo';rdir.mkdir(parents=True)
 (rdir/'SPEC.md').write_text('# Spec\n## Requirements\n- R1. Demo\n')
 (rdir/'PLAN.md').write_text(PLAN_MD.replace('REQ-042','REQ-001').format(status='approved'))
 doc=classify(sync.skeleton(rdir,plan_id='REQ-001'));(rdir/'PLAN.json').write_text(contract.dumps(doc))
 with patch.object(bt_core,'ROOT',base):
  sync.approve_freeze(rdir,'REQ-001',('approved',));run=scheduler.open_scheduler(rdir);run.step();scheduler.write_projection(rdir,run);bt_scheduler_run._runtime_binding(rdir,resume=False)
  working=json.loads((rdir/'PLAN.json').read_text());working['tasks'][1]['objective']='UNAPPROVED unrelated T2 change';(rdir/'PLAN.json').write_text(contract.dumps(working))
  with patch.object(ops,'stop_owner',return_value=0),patch.object(ops,'resume',return_value='synthetic-no-start'):
   result=edit.dispatch_edit_brief('demo/REQ-001',{'typed_req':'REQ-001','task':'T1','field':'brief','value':'Owner only edits T1'})
  frozen=revisions.load_revision(rdir,result['revision']);print('freeze result',result)
  print('frozen unrelated task',frozen['tasks'][1]['objective']);assert frozen['tasks'][1]['objective']=='UNAPPROVED unrelated T2 change'
  (rdir/'PLAN.md').write_text(PLAN_MD.replace('REQ-042','REQ-001').format(status='review'))
  before=(rdir/'PLAN.json').read_bytes()
  try:edit.dispatch_edit_brief('demo/REQ-001',{'typed_req':'REQ-001','task':'T1','field':'brief','value':'Should fail without changing disk'})
  except Exception as exc: print('failed edit guard',type(exc).__name__,str(exc).splitlines()[0])
  else:raise AssertionError('expected approval guard')
  after=json.loads((rdir/'PLAN.json').read_text());print('changed disk despite failure',(rdir/'PLAN.json').read_bytes()!=before,'working revision',after['revision'],'frozen revision',revisions.latest(rdir)['revision'])
  assert (rdir/'PLAN.json').read_bytes()!=before and after['revision']==3 and revisions.latest(rdir)['revision']==2
PYCODE
```

Observed: real r2 freezes the unapproved unrelated T2 objective; the subsequent rejected edit leaves working r3
while frozen remains r2. Only process stop/resume are suppressed; freeze, rebase and real approval guard execute.

### Probe N — Telegram age cutoff and delivery history

```bash
python - <<'PYCODE'
import pathlib,sys,tempfile
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path('remote/gateway').resolve()))
from notifications import NotificationOutbox
with tempfile.TemporaryDirectory() as tmp:
 out=NotificationOutbox(str(pathlib.Path(tmp)/'out.db'))
 with patch('notifications.time.time',return_value=100): out.enqueue('old','synthetic old message')
 sent=[];n=out.deliver_due(sent.append,now=100+7200)
 print('delivered two-hour-old message',n,sent);assert n==1
 out.enqueue('retry','synthetic delivery failure')
 def fail(_):raise RuntimeError('synthetic')
 out.deliver_due(fail,now=100);out.deliver_due(fail,now=100+7200)
 status=out._db.execute("SELECT status,attempts FROM telegram_outbox WHERE dedupe_key='retry'").fetchone()
 print('still pending after two hours',status);assert status==('pending',2)
 tables=[r[0] for r in out._db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
 print('tables',tables);assert 'telegram_delivery_history' not in tables
 out._db.close()
PYCODE
```

Observed: two-hour-old message is delivered; failed delivery remains pending after two hours; no per-attempt
history table. No Telegram request is sent by this probe.

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
  assert res.status==400 and not server.errors;conn.close()
 finally:server.shutdown();server.server_close();thread.join()
PYCODE
```

Observed: sixth login receives 429 regardless of distinct forwarded client identities; nested JSON receives 400
without crashing the handler on the audited Python 3.14 runtime.

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

## Final artifact checks

Fresh results: three `test -s remote/docs/audit.md` invocations exit 0; ledger JSON schema is
`audit-findings/1`, with 54 unique IDs, valid frozen task references, no accepted risks and evidence for every
fixed finding. All report finding headings/verdicts match the ledger. Both artifacts have zero conflict markers;
all 15 documented Python reproduction scripts compile in memory. `git diff --check` exits 0; tracked changes
are exactly `remote/docs/audit.md` and `remote/docs/audit.findings.json`, with no nonignored untracked files.
Support-document existence checks for route-pin.md, architecture.md and contract.md succeed. Implementation paths
remain unchanged from HEAD, preserving both prerequisite and earlier audit intents.

These artifact checks do not satisfy the unresolved substantive acceptance criterion: F41/F42 remain high/open
under T8a. Medium/low findings remain recorded without owner risk acceptance. The scheduler's independent check
decides the task outcome.
