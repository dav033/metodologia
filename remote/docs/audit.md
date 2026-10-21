# Independent security and specification audit — T18

**Rework required: F2, F36, F41, F42, F63, F66 and F67 remain high/open.**
The substantive “Confirmed high findings are fixed” criterion is unmet. This read-only task changes only
`remote/docs/audit.md` and `remote/docs/audit.findings.json`; source repairs belong to the named prerequisite tasks.
No owner risk acceptance or independent verification verdict is claimed.

Audited entry HEAD: `212abc5a76f2f852b06d45763b9640b0babc67b6` (att-0402), 2026-10-21, America/Bogota.
Primary auditor: OpenAI Codex. Fresh separate provider: Anthropic `firstParty / claude-sonnet-5-5`, tools disabled.
Scope: complete frozen SPEC R1–R18, PLAN.md, PLAN.json r3 and amendments, task objectives, acceptance and verification,
including the new prerequisites. The primary audit checks the actual producers and consumers independently.

Ledger: **68 findings: 22 rechecked fixed, 46 open (7 high, 32 medium, 7 low), zero accepted.**
All 67 earlier IDs and both sides' substantive intents are retained. New F68 records the confirmed, bounded error
response issue from this provider pass. F6 records the new relative failure-review path without overstating it as a
usable Telegram link. None of the previous high findings is closed merely because a local unit suite passes.

## Reconciliation and prior attempts

Opened both supplied audit files before changes. Entry `git status --short` was empty, and neither file had literal
conflict markers. Thus no conflict text needed removal. Compared `fe4ba03b1008a10fa7b40100441bab9cb86fa581` to entry HEAD:
14 source/test/config paths changed. This report reconciles that new behavior with the earlier audit; no source,
test, schema, configuration, lockfile or working implementation is rewritten or deleted.

New prerequisite behavior retained and rechecked: requestId/request_id forwarding, relative task/attempt review paths,
expanded flow-transition recognition with strict exhaustion filtering, separate failed-review versus live-attempt identity,
native snapshot plans/rounds/decision collection, and removal of obsolete packaging entries. Existing stream fan-out,
session revocation, Caddy bridge topology, env permissions, route pinning, scoped review IDs, observation cursors,
durable outage dedupe, expiry/backoff/history and missing-systemctl ownership behavior are also preserved.

Read all six supplied earlier-attempt failure notes and their reachable ledger contents before editing:

| Attempt / historical result | Historical blocking IDs | Fresh disposition |
|---|---|---|
| #16 att-0317 / b3de1b8ce | F1/F41/F42 | F1 repaired; E reconfirms editor dialect and approval/rollback defects. |
| #17 att-0322 / d9e83adc6 | F41/F42 | Both remain open; this audit does not repeat source edits in a read-only task. |
| #18 att-0331 / 8ccc09c9b | F41/F42/F55 in ledger | F55 rechecked fixed; F41/F42 open. The supplied note groups this with #16. |
| #19 att-0344 / 7b11b3a89 | F2/F61/F62/F63 | F61/F62 rechecked fixed; E2E and fresh Bogota round still fail. |
| #20 att-0352 / d629327c9 | F2/F36/F63/F66/F67 | All remain open at actual public/native boundaries. The supplied note additionally names F36. |
| #21 att-0383 / fe4ba03b1 | F2/F36/F41/F42/F63/F66/F67 | All seven freshly reproduced in this tree. |

Raw m6 receipts and the 15 omitted attempts are unavailable inside this worktree; no retrieval is claimed.
Historical accepted wording is not current evidence. Preserve the repairs above while returning the wrong prerequisite
results for rework; an existence gate cannot substitute for the substantive acceptance criteria.

## Current verification

Ran `cd remote/web && npm ci --offline`: exit 0, 320 packages, lockfile unchanged. Checks then use those installed
dependencies; no test installs packages or needs a running server left by this audit. All fixture state and build
outputs are disposable and stay inside this worktree. No credentials were read or printed; only synthetic values
were used. No deployed services, other worktrees, remotes, host service ownership or real agent execution was touched.

The initial workspace-backed absolute TMPDIR exceeded Chromium's Unix socket path limit. Auth and kit failed for
that reason; initial web verification hit the same error and a 90 s panel timeout, then its owned subprocesses were
terminated. Repeated only those affected commands using a short `/proc/<audit-process>/cwd/remote/.audit-t18/...`
alias to the same workspace directory. This changes temp-path length, not tests, assertions or browser behavior.
Auth and kit then pass; final web failure is the actual width assertion below. Browser builds/checks ran sequentially.
Python suites used synthetic BITACORA_ROOT directories. Caddy binary validation remains skipped.

| Exact frozen command (shared commands executed once, except affected browser rechecks) | Fresh result |
|---|---|
| `test -s remote/docs/route-pin.md` | exit 0; 0.002 s wall. |
| `python -m json.tool remote/contract/command.schema.json` | exit 0; 0.062 s wall; JSON syntax only. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py` | exit 0; 6 tests, 9.469 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py` | exit 0; 23 tests, 4.571 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py` | exit 0; 14 tests, 1.776 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py` | exit 0; 3 tests, 3.167 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py` | exit 0; 10 tests, 2.026 s wall. |
| `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py` | exit 0; 28 tests, 2.566 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py` | exit 0; 5 tests, 11.277 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_auth.py` | exit 0; 3 tests, 3.411 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_guard.py` | exit 0; 7 tests, 4.091 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_stream.py` | exit 0; 13 tests, 5.495 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py` | exit 0; 12 tests, 3.515 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py` | exit 0; 4 tests, 0.252 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_send.py` | exit 0; 3 tests, 0.140 s wall. |
| `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_bot.py` | exit 0; 4 tests, 0.210 s wall. |
| `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py` | exit 0; 14 tests, 8.863 s wall; one skip: Caddy executable unavailable. |
| `cd skill/scripts && python -m unittest discover -s tests -p "test_page*.py"` | exit 0; 43 tests, 12.265 s wall. |
| `cd skill/scripts/bt_scheduler_core && python -m unittest discover -s tests -p test_operations.py` | exit 0; 18 tests, 0.993 s wall. |
| `cd remote/web && npm run verify` | Exit 1; lint/types pass; 13/14 node tests pass, zero skips; 20.589 s wall. panel-browser.test.mjs:165: 366 !== 360. Build not reached; F18. |
| `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py` | Exit 1; 1 test, 24.527 s / 24.696 s wall; optimized production build succeeds, line 403 fails empty events/nextCursor. Later scenarios not reached; F2/F67. |
| `test -s remote/docs/audit.md` (three frozen T18 entries) | Each exit 0. File existence is not evidence that high findings are repaired. |

The 17 Python suites execute 210 tests: 209 pass and one Caddy skip. The failing E2E adds one test.
All 21 inherited reproduction blocks ran against entry HEAD, each exit 0. Extended E then also tests both criteria
aliases; new AI checks both decision-id aliases and the new relative review path; new AJ checks exception forwarding.
Every final embedded block was executed, including E after extension. Exit 0 means its observed defect or repair
reproduces, not that the product meets acceptance. AJ's first draft incorrectly expected history to expose errors;
inspection and a corrected probe show the public history correctly withholds them. Only the immediate response is F68.

An extra `test -s remote/docs/tools-entries.md` returned exit 1: that future T19 artifact is absent. T19 follows T18
and is not a failed prerequisite or a new finding. No claim of complete future-task verification is made.

Not run: Python 3.12 (unavailable; local interpreter 3.14.7), Caddy executable/container connectivity, deployed OAuth,
Telegram, Vercel/SSE, selected-route agent execution, phone PWA installation, exhaustive 44 px touch measurement,
dependency advisory scan, or multiprocess/local-writer stress. The historical spike document is read-only prior
evidence, not a deployed recheck in this attempt.

## Fresh independent other-provider receipt and adjudication

Invocation: `claude -p --safe-mode --no-session-persistence --setting-sources '' --model sonnet --effort medium --tools '' --max-turns 1 --output-format json`.
The provider received a fresh numbered current packet: SPEC, PLAN.md/PLAN.json/amendments, packaging, all gateway
modules, laptop remote API/ledger/editor/feed/recovery/live projection/server, phone components, deployment kit,
runbook, command schema and E2E. It received no prior findings, ledger or primary conclusions. Tools were disabled;
its review was static. Primary audit separately ran the commands and traced consumers outside that packet.
The contract prose, deployed spike, next.config and some scheduler adapters were inspected by the primary auditor;
they were not supplied to the provider, and its related hypotheses are bounded accordingly.

Receipt: exit 0, subtype `success`, is_error `False`, 1 turn,
provider 239294 ms / 240.584 s wall; source 449,863 characters.
Input SHA-256: `447cfe4dabe98dffec76aec9079b15e5e2182fd0afcc9cb1a2d04475540b9660`.
Output JSON SHA-256: `46c2eada7fa8898bcfb5a1a3a64347af60eb1a865330be9bdfde21a442a63f8e`.

Provider numbers below are local to that response, not ledger IDs. Each is adjudicated against demonstrated impact.

| Provider item | Primary verdict and reason |
|---|---|
| 1 high: public snapshot | Confirmed high F36 by AG: actual native model has a run, gateway wraps it, exact phone parser rejects it. F35 remains fixed at the native boundary. |
| 2 high: live stream | Confirmed F21, medium: actual phone route 404, server named events versus onmessage and mismatched cursor dialect. Polling fallback exists; no added high severity for this path alone. |
| 3 high: Telegram context/buttons | Confirmed F6, medium: AI proves new relative path survives, but sender has text/chat_id only, no absolute URL/cause/buttons; B rejects retry. /estado has separate controls. |
| 4 high: edit dialect/criteria | Confirmed high F41 by extended E, and medium F8 for absent criteria UI. Gateway forwarding is intact (F33); downstream editor requires brief. |
| 5 medium: failed effect HTTP 200 | Confirmed F39 by G and actual page response.ok path. Upstream classification/truncation remains F40, I/I2. |
| 6 medium: manual challenge UI | Confirmed F46 by required id and disabled-button path. Separately high F66: AG proves native HTTP issuance absent even for automatic challenge forms. |
| 7 medium: alerts | Confirmed high F63 for an actually fresh Bogota round and high F67 for an actual exhausted M1 task; medium F30/F37/F58 for stall threshold, retrospective retry alerts and per-account quota rule. Reject treating deterministic one-hour expiry itself as an unconditional bug or removing it; N confirms bounded backoff/expiry/history. No separate old-event reconnect failure was reproduced. Decision-as-plan wording belongs to F6 context. |
| 8 medium: offline/cache/retention | Confirmed F11/F12/F13 by B and current memory-only hub: restart loses snapshot, no offline-start timestamp, no bounded history/session cleanup. Durable outage dedupe is separately repaired (T). |
| 9 medium: proxy rate bucket | Confirmed F47 by six actual requests L. Per-owner rather than per-session command bucket remains F27. Do not trust arbitrary forwarded headers as a repair. |
| 10 medium: deadlines/retry keys | Confirmed medium F16 and low F52 by page source and O/I. No concrete duplicate business effect on a new key was reproduced. Within-process distinct-key serialization remains repaired F28 (D). |
| 11 medium: contract/note | Confirmed low F17 for schema/document dialect drift and medium F7 for a missing standalone note handler. Retry-note injection is a separate existing path; no claim that all next-attempt notes are absent. |
| 12 medium: routes/unused stores | Confirmed medium F64 by AD: unknown-quota route offered but retry refuses it. Unused alternate pin code alone has no reproduced product impact. Reject absent consumer: bt_scheduler_adapter.py:393-395 calls get/narrow; C persists selected route/model/account. |
| 13 low/medium: edit atomicity | Confirmed high F42 by E: failed commands publish r2/r3 and include unapproved unrelated T2 changes. Demonstrated unauthorized approval scope and rollback damage justify high, not merely the provider's label. |
| 14 low/medium: kit | Confirmed F3/F48/F54 by J/B/O and source; filled private-interface configuration remains F1/F22 fixed. Host-Caddy reload is wrong for the documented container. Tunnel name replacement needs rollout care, but architecture.md specifies intentional remote-only ports and safe disable rollback; no compliant-install exposure/local-panel loss is demonstrated. FLOW_GATEWAY_ORIGIN is the actual next.config name; older PLAN naming alone is not a new broken deploy finding. |
| 15 low: auth hardening | Marker/logout confirmed F5 by A; already-open session streams confirmed low F31 by AG. Reject numeric GitHub user-ID pinning, callback.from.id and command/key-bound challenges as frozen requirements: the spec names login dav033, configured chat_id and target-bound one-use 120 s challenges. No bypass of those stated boundaries shown. |
| 16 low: raw exception text | Confirmed new low F68 by AJ's injected failing handler through real native HTTP/relay. Immediate error text is raw; public history correctly excludes it. No real built-in secret-bearing exception or deployed secret theft demonstrated. |
| Test gaps | Confirmed high F2 and exact AG/AH boundaries missing from T17; the exact E2E fails before its later assertions. Existence-only T18 checks do not establish high-fixed acceptance. Full R1–R18 audited despite narrower covers metadata; no self-approved plan revision. |
| H1: deployed rewrites | Local browser OAuth rewrite tests pass after temp fix, next.config.ts has same-origin rewrites, and historical spike exists. Fresh deployed behavior remains unrun, not newly confirmed broken. |
| H2/H3/H4: pin/revise/exhaustion | H2 missing-consumer claim rejected by actual adapter; selected-agent execution unrun. H3 TypeError rejected: ops.apply has target='', reason='' defaults. Actual failures are E's publication gate and lack of rollback. H4 confirmed as F67 by actual M1 producer/AH, plus F37's distinct fixture problem. |
| H5/H6/H7: omitted components/errors/freshness | Actual review route and remote listener exist and are exercised by suites/C/AG; quotas are tested via synthetic source, F44 shows real shape mismatch. No valid new malformed-plan producer or bounded 5+5 s freshness reproduction established; no additional confirmed finding. Public snapshot/SSE/five-second delivery blockers are already F36/F21/F51. |

The provider's rejection of OAuth-code logging is **incorrect**: A captures the full synthetic callback query in
GatewayHandler.log_message's status/request-line field (F4), despite a sanitized path field. Redaction of quoted
credential text is also independently reproduced (F56). Telegram retry logging of exception types does not by
itself expose the bot token; no such token leak is claimed.

Other bounded rejections: laptop bearer bypass (fails closed, constant-time); OAuth state replay/fixation (single-use,
cookie-bound state); command CSRF bypass (actual Origin guards); arbitrary upstream-read SSRF (route allowlist);
review traversal/symlink read (validated target/IDs, O_NOFOLLOW regular files, bounded reads and correlated ledger);
same-key/challenge repeated effects within the tested process (PENDING reservation, serialization and challenge
transaction). Session logout revocation works (A); the already-open stream behavior is separate F31. No blanket
claim about arbitrary secret forms, cross-process writers or unsupported malformed producers is made.

## Current findings and verdicts

Every confirmed finding has a ledger entry. Fixed means already repaired and freshly rechecked in entry HEAD;
this read-only audit changes no implementation. Open findings are not accepted risks.

### F1 — high / fixed — The Caddy upstream and gateway bind instructions match the frozen container-to-host topology.

Tasks: T16. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 14 tests, one Caddy-unavailable skip. Probe B (`python -`): exit 0; both parsers accept the filled example with 172.20.0.1:8790, matching Caddyfile. Container connectivity unrun.

### F2 — high / open — The frozen built-web E2E still fails at the empty feed before OAuth/control/offline/Telegram assertions.

Tasks: T17. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py`: exit 1, 1 test in 24.527 s (24.696 s wall), line 403: nextCursor is empty, events=[]. Optimized production build succeeds. Current AH confirms the real T6 producer cannot satisfy exhaustion (F67). OAuth/control/offline/Telegram assertions after line 403 are not reached. T17 never GETs the production snapshot or issues a challenge, missing F36/F66; its three-alert expectation includes earlier retryable failures (F37). Preserve real producer semantics and the no-alert-with-retries invariant.

### F3 — medium / open — The restored runbook deploys and restarts before installing the service on a fresh host.

Tasks: T16. Probe J (`python -`), current mode-600 synthetic env: exit 0; fake missing-unit systemctl makes deploy exit 5 after current is switched, deploy --dry-run exits 0, rollback --dry-run exits 2 with no previous release. Initial probe with default env-file permissions correctly failed the new mode-600 guard before deployment; corrected only the synthetic fixture. Runbook still deploys/restarts in step 3 before unit installation in step 4, and reloads host caddy although Caddy is containerized. Preserve the new env permission check.

### F4 — medium / open — Gateway request logging still exposes OAuth code/state query values in its status field.

Tasks: T11a. Probe A: exit 0; real loopback synthetic callback query appears in captured server logging. GatewayHandler.log_message uses args[0], the complete request line, as status despite separately sanitizing the path field. No account takeover or session-token theft demonstrated.

### F5 — medium / open — The mutation marker accepts arbitrary nonempty values and foreign-Origin GET logout bypasses mutation guards.

Tasks: T11a, T15a. Probe A (`python -`): exit 0; wrong X-Flow-Request yields HTTP 200, foreign-Origin GET logout yields 302 and clears the cookie. The new delete_session repair DOES revoke the session, independently checked; the previous nonrevocation subclaim is withdrawn. Actual command POST Origin checks remain effective; no command CSRF bypass alleged.

### F6 — medium / open — Telegram failure alerts now include a relative review path but still lack an actionable absolute link, cause and safe inline actions; retry callbacks are unsupported.

Tasks: T14a, T14b. Fresh Probes B/AI (`python -`, report): exit 0. The new notification_for_event appends /review?project=demo&req=REQ-001&taskId=T1#attempt-a1 and retains run-scoped failure dedupe. Preserve that repair. TelegramSender still sends only chat_id/text; there is no absolute frontend URL, cause, readable task/run context or reply_markup. GatewayRuntime.submit_telegram_command accepts pause/resume only; retry returns INVALID_COMMAND. The current four bot tests pass, but cover their own fixtures. /estado keyboard is separate.

### F7 — medium / open — The public standalone note command has no laptop dispatcher.

Tasks: T5a. Rechecked in this attempt: Fresh Probe B: exit 0; real Ledger.submit(note) with commands.dispatch_handlers() returns COMMAND_NOT_IMPLEMENTED. dispatch_handlers advertises no standalone note handler despite COMMANDS and schema listing it. Retry reason/RUN.notes is separate.

### F8 — medium / open — The phone brief form cannot edit acceptance criteria.

Tasks: T15f. Fresh page.tsx:371-380/410-415 still offers only a brief text area and sends field=objective with a string value; there is no acceptance-criteria control. Extended Probe E (`python -`, report): exit 0; actual gateway/native ledger reject objective, acceptanceCriteria and acceptance_criteria field/value requests as EFFECT_FAILED. The criteria UI omission remains distinct from downstream F41.

### F9 — medium / open — Run-level Reabrir ejecución supplies no task identity to the task-scoped operation.

Tasks: T15d. Rechecked in this attempt: page.tsx run-level commandForm(reopen) omits taskId; bt_remote_commands.TASK_SCOPED/_member_state and dispatch_run_command require params.task. Fresh Probe C confirms task-scoped reopen succeeds; that repair does not provide an identity for the run-level form.

### F10 — medium / fixed — A plan waiting for approval emits plan.waiting without a scheduler decision.

Tasks: T6. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe B (`python -`): exit 0; plan_status=review emits plan.waiting without a scheduler decision. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py`: exit 0, 14 tests.

### F11 — medium / open — Gateway restart still loses the last snapshot despite the newly wired production stream hub.

Tasks: T12. Probe B (`python -`): exit 0; current runtime keeps old generatedAt offline, replacement runtime with same SQLite database returns None. StreamHub is now instantiated and passed by main, but its snapshot and snapshot_cache are memory-only. Production hub snapshot after restart is empty, not the last persisted state. Retain fan-out wiring while persisting the latest model.

### F12 — medium / open — Expired sessions and Telegram outbox/history remain unbounded beyond the required 90 days.

Tasks: T11, T14a, T5. Probe B: exit 0; creating a session leaves an abandoned expired row. SessionStore prunes sessions only when presented. Current notifications.py now has telegram_history with timestamped rows (F43 fixed), but no 90-day prune of that table/outbox; Ledger.rows still reads all rows. Retention is separate from the now-wired SSE hub and its revocation issue F31.

### F13 — medium / open — The phone receives no stable offline-start timestamp.

Tasks: T12, T15b. Rechecked in this attempt: Updated Probe B: exit 0; cached generatedAt is retained and laptop is only {online:false}, with no checkedAt or offline-start timestamp. GatewayRuntime.web_snapshot does not expose the persisted outage start or liveness offline_since. The phone still renders LAPTOP SIN CONEXIÓN with no HH:MM. Actual T17 currently fails before offline checks, so no passing integrated timestamp assertion is claimed.

### F14 — medium / fixed — Laptop-side redaction handles the previously missed provider assignments and bearer authorization text.

Tasks: T7, T6. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe B (`python -`): exit 0; synthetic plain OPENAI_API_KEY assignment and Authorization: Bearer values removed. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py`: exit 0, 3 tests. Quoted values remain F56.

### F15 — medium / fixed — The local panel implements inherited systemd listener activation/reload.

Tasks: T9. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py`: exit 0, 28 tests, including inherited listener/reload/ownership. Same discovery with test_page*.py: exit 0, 43 tests. No host service touched. Missing-systemctl case is independently repaired, F65.

### F16 — medium / open — The phone discards uncertain command envelopes and generates a new key on resubmission.

Tasks: T15d. Rechecked in this attempt: Fresh page.tsx checks response.ok, labels UNKNOWN_OUTCOME HTTP 503 Rechazado, and retains history summaries rather than an exact replayable envelope/key; form submitters always call crypto.randomUUID(). Server at-most-once remains valid for a reused key; no duplicate effect through a specific ABA sequence was reproduced, so severity stays medium.

### F17 — low / open — The public command schema differs from production command families, fields and key limits.

Tasks: T3. Rechecked in this attempt: Fresh schema syntax commands exit 0 only. command.schema.json omits answer-decision, expects singular answer/route text/edit brief; actual phone sends answers/round, route object and field/value. Fresh Probe B rejects a 121-character ledger key despite schema maximum 128. contract.md also omits the required review target query and advertises command success/error shapes different from the actual synchronous HTTP responses. This is contract mismatch, not proof of arbitrary execution.

### F18 — medium / open — The required web verification fails the 360 px browser assertion.

Tasks: T15. `cd remote/web && npm run verify`: exit 1, 20.589 s wall; lint/typecheck pass; node tests 13/14 pass, zero skips, 14.837 s. Chromium panel-browser.test.mjs:165 measures 366 !== 360. Build is not reached in verify; the separate exact E2E production build succeeds. This result uses the corrected short workspace-backed TMPDIR; earlier long-path Chromium failures were audit harness artifacts. Preserve the width assertion.

### F19 — high / fixed — The integrated phone app compiles, typechecks and builds without the previous overlapping declarations.

Tasks: T15a, T15c, T15d. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: `cd remote/web && npm run verify`: lint and strict typecheck pass; 13/14 node tests pass, only the 366 !== 360 width assertion fails. `cd remote/e2e && python -m unittest discover -s tests -p test_local_e2e.py`: optimized Next.js production build succeeds before the empty-feed failure. No overlapping declarations remain.

### F20 — high / fixed — The phone accepts the real gateway login session dialect.

Tasks: T15a. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe A (`python -`): exit 0; actual authenticated gateway session returns HTTP 200 {login:dav033}. `cd remote/web && npm run verify`: browser sessionContractObserved and selected review assertions pass before width failure. Public snapshot is separately broken, F36.

### F21 — medium / open — The newly wired production SSE still disagrees with the phone path, event names and cursor.

Tasks: T12, T6, T15b. Probe AG (`python -`): exit 0; actual main-equivalent wiring returns 404 for phone /api/remote/v1/events/stream; actual /api/remote/v1/stream returns HTTP 200 named event frames. page.tsx:256-257 opens events/stream?after=<snapshot cursor> and only assigns onmessage; server.py:113-129 reads Last-Event-ID and emits event/resync. The source-time snapshot cursor also differs from hub epoch:sequence IDs. Plain events/read_remote are repaired; retain production hub/fan-out while aligning the public dialect and resync handling.

### F22 — medium / fixed — A completely filled example configuration starts parsing; the prior mandatory-blank allegation is superseded.

Tasks: T16. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe B (`python -`): exit 0; all example keys filled with synthetic values parse in GatewayConfig and OAuthConfig. `cd remote/deploy && python -m unittest discover -s tests -p test_kit.py`: exit 0, 14 tests, one Caddy skip. Empty optional bind remains F54.

### F23 — medium / fixed — Native keyed command history and its web compilation are restored.

Tasks: T4a, T15d. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probes C/AG (`python -`): exit 0; actual keyed and authenticated public commands/history return commands/nextCursor without disconnect. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py`: exit 0, 5 tests. Web lint/types pass.

### F24 — high / fixed — Wheel and sdist include the actual edit and route-pin implementation modules.

Tasks: T8, T8a. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe P (`python -`, report): exit 0; fresh wheel and sdist include bt_remote_edit.py and bt_route_pins.py; isolated -I imports of bt_remote_api, bt_remote_commands, bt_remote_edit and bt_route_pins all exit 0. The obsolete bt_remote_snapshot/bt_remote_preconditions pyproject entries are now removed; the running implementation is inlined. Packaging remains repaired.

### F25 — medium / fixed — The failed-task link consumes the selected real review attempt instead of only a static fixture.

Tasks: T15c. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: `cd remote/web && npm run verify`: Chromium selected real rejected-attempt hash/content assertions pass before F18. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py`: exit 0, 3 tests. Probe AA (`python -`): exit 0, native target-specific causes; AG returns actual public review HTTP 200.

### F26 — medium / open — Reopen/retry now work in the same tab, but ready recovery controls disappear after reload or in another tab.

Tasks: T15f, T15d. Rechecked in this attempt: Updated C: exit 0; real task reopen moves recovering -> ready and pinned ops.retry succeeds. Source page.tsx still gates recovery on recovering/reopenedForRecovery, with reopenedTasks only an in-memory useRef. Reload/new tab loses the ready task controls. The source-level ready-state fixture test passes before the browser-width failure, but it does not prove a reload of a real producer snapshot. F41/F42 separately regressed and are high/open in this tree.

### F27 — low / open — Command limits remain shared by owner login across sessions instead of per session.

Tasks: T11a. Current server.py uses authenticated login as the commands/challenges rate bucket, sharing quota between all dav033 sessions; exact auth/guard tests pass (3/7). This is stricter than R17 but not an authentication bypass; shared anonymous login availability remains F47.

### F28 — high / fixed — Distinct-key concurrent preconditions serialize with the remote ledger effect.

Tasks: T5. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe D (`python -`): exit 0; two distinct-key concurrent pauses produce one effect, one OK, one STALE_PRECONDITION and two audit rows. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_commands.py`: exit 0, 23 tests. Independent processes/local writers unrun.

### F29 — medium / open — The restored snapshot still loses run life-sign/revision fields and reads plan criteria from the wrong task level.

Tasks: T4a. Probe C (`python -`): exit 0; actual seeded frozen task has nonempty acceptance_criteria, but actual snapshot plan task acceptanceCriteria=[] because serializer reads task.acceptance_criteria instead of task.detail. Runs expose lastActivityAt and attempts last_activity_at; exact phone parser reads lastSeenAt/updatedAt. Run/task revision remains absent. Plans/rounds/decisions now collected; no blanket missing-model claim or new ABA exploit.

### F30 — medium / open — Stalled-attempt notifications start after 15 minutes rather than the required more than 10 minutes.

Tasks: T6. Rechecked in this attempt: Fresh Probe B: exit 0; live attempt has no attempt.stalled at +660 s and does at +901 s. bt_remote_events.STALL_SECONDS=15*60 conflicts with SPEC R10. The emitted text says more than 10 minutes but the threshold does not.

### F31 — low / open — The restored authenticated SSE connection continues after its session is revoked.

Tasks: T11, T12. Probe AG (`python -`): exit 0; actual /api/remote/v1/stream accepts a valid synthetic session; SessionStore.delete_session revokes it; publishing a new synthetic event still sends its data frame over the same connection. server.py stream loop never rechecks the session. The prior fixed verdict depended on absent production streaming and is superseded. No stolen-cookie or process-wide denial claim; terminate or periodically revalidate revoked/expired sessions.

### F32 — high / fixed — The gateway preserves the phone route_id selector and selected model/account pin.

Tasks: T13. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe C (`python -`): exit 0; phone route_id/model/account survive translation; actual keyed retry on ready stores selected pin and returns OK with only availability and process start stubbed. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_recovery.py`: exit 0, 10 tests. Actual agent execution unrun.

### F33 — high / fixed — The gateway preserves phone round/answers and edited field/value.

Tasks: T13. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe C (`python -`): exit 0; actual keyed answer-round stores answers; field/value survive gateway translation. This fixes the gateway forwarding defect only: current E demonstrates the separate downstream T8a regression F41. `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py`: exit 0, 12 tests.

### F34 — medium / fixed — Both frozen notification and delivery test files are restored and execute.

Tasks: T14, T14a. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: `cd remote/gateway && python -m unittest discover -s tests -p test_notify.py`: exit 0, 4 tests; same discovery with test_telegram_send.py: exit 0, 3 tests. Both frozen test files exist and execute. Bot discovery also exits 0 with 4 tests; passing test presence does not resolve the production gaps.

### F35 — high / fixed — The real laptop snapshot now passes the exact phone parser for a nonempty runs list.

Tasks: T4a. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe C (`python -`): exit 0; exact TypeScript parseSnapshot from page.tsx accepts one actual laptop run and plans. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py`: exit 0, 5 tests. This is the native serializer boundary; public gateway envelope regression is high F36.

### F36 — high / open — The production gateway wraps its snapshot in a hub envelope that the real phone parser rejects.

Tasks: T12. Probe AG (`python -`): exit 0; real laptop seeded with one run, GatewayRuntime.poll_once and main-equivalent make_handler(service,hub=runtime.hub,runtime=runtime) yield authenticated snapshot HTTP 200 with keys cachedAt,lastEventId,online,snapshot and one nested run. Exact page.tsx parseSnapshot transpiled by installed TypeScript throws "La respuesta del gateway no cumple el contrato de snapshot v1." server.py:98-107 shadows read_routes and never calls web_snapshot. Missing read_remote is repaired; public history/commands/events/targeted review now return HTTP 200. T12 must flatten/normalize the cached snapshot and liveness to the real phone contract; T17 must assert this actual boundary.

### F37 — medium / open — Exhaustion fixtures still retrospectively alert for earlier retryable failures once a task exhausts its budget.

Tasks: T6. Probes H/AB (`python -`): exit 0, one failure within budget yields no alert, but three historic/current failures with authoritative exhausted counters yield three alerts. Current T17 expects three messages after final exhaustion; frozen US-4 requires one for the failure with no retries left. Actual live projection currently produces no failure alerts at all (distinct high F67); keep filtering retryable failures.

### F38 — medium / fixed — Real structured HTTP INVALID_CURSOR now reaches the gateway cursor-reset branch.

Tasks: T13, T12. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe G (`python -`): exit 0; real HTTP 400 structured INVALID_CURSOR resets GatewayRuntime.event_cursor to empty. `cd remote/gateway && python -m unittest discover -s tests -p test_commands.py`: exit 0, 12 tests. Rebuild-from-now policy remains F57.

### F39 — medium / open — HTTP 200 for failed command effects still makes the phone clear forms and treat failed reopen as successful.

Tasks: T13, T15d. Rechecked in this attempt: Fresh updated Probe G: exit 0; authenticated gateway receives FAILED/ROUTE_UNAVAILABLE and returns HTTP 200. server.py status map omits ROUTE_UNAVAILABLE, EFFECT_FAILED, STATE_UNAVAILABLE and COMMAND_NOT_IMPLEMENTED. page.tsx checks response.ok before setting reopenedTasks and clearing forms.

### F40 — medium / open — The upstream client misclassifies ambiguous success and known refusal, and lets truncated success escape the runtime.

Tasks: T13. Probe I: exit 0; real accepted POST returning HTTP 200 invalid JSON becomes FAILED/LAPTOP_UNAVAILABLE, while synthetic URLError(ConnectionRefusedError) becomes UNKNOWN_OUTCOME because OSError is caught first. I2: exit 0; actual loopback truncated HTTP 200 with Content-Length 100 and two response bytes raises uncaught http.client.IncompleteRead from GatewayRuntime.submit_command. No duplicate effect is claimed; ordinary UpstreamError is caught, so not every transport failure crashes a handler.

### F41 — high / open — The redone edit dispatcher again rejects the actual phone objective and criteria field/value dialect.

Tasks: T8a. Extended Probe E (`python -`, report): exit 0. Real keyed HTTP through GatewayRuntime returns FAILED/EFFECT_FAILED for the actual phone objective field/value and both acceptanceCriteria/acceptance_criteria array aliases, with edit-brief requiere task y brief no vacíos; latest revision stays 1. app.py preserves field/value (C/AI), but bt_remote_edit.py:24 requires brief. No criteria edit implementation exists. Exact recovery suite still passes its legacy brief fixtures (10 tests).

### F42 — high / open — The redone editor freezes unrelated working-plan drift and leaves mutated revisions after failure.

Tasks: T8a. Fresh extended Probe E (`python -`, report): exit 0. With the existing legacy brief dialect, unrelated unapproved T2 working-plan drift is frozen into revision 2 before PLAN_CONSUMER_INCOMPATIBLE returns FAILED. A subsequent refused edit publishes revision 3 and leaves changed working bytes (before != after). bt_remote_edit.py:35-48 loads mutable PLAN.json, writes/freezes before the publication gate and has no rollback. Owner-approved-base and atomicity safeguards remain absent; no successful rebase is claimed.

### F43 — medium / fixed — Telegram delivery restores one-hour expiry, exponential backoff and timestamped per-attempt history.

Tasks: T14a. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe N (`python -`): exit 0; expiry drops at attempt 0, failed delivery records timestamped retry, later expiry preserves attempts and drops. `cd remote/gateway && python -m unittest discover -s tests -p test_telegram_send.py`: exit 0, 3 tests. No 90-day retention claim.

### F44 — medium / open — The restored quota endpoint returns an array of windows that the phone discards.

Tasks: T4a. Rechecked in this attempt: Fresh Probe Q: exit 0; actual keyed route_get /quotas with one synthetic account/five_hour window returns windows=[{window,usedPercent,resetsAt}], observedAt string. Exact QuotasPanel parser transpiled with installed TypeScript calls record(account.windows), which rejects arrays: parsed account count is 0. Phone expects a windows object with used_percent/resets_at and numeric observedAt. Restore compatible projection or normalize both dialects; mock browser data currently hide the mismatch.

### F45 — medium / fixed — The liveness entrypoint fixture now includes its OAuth settings and passes.

Tasks: T10. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: `cd remote/gateway && python -m unittest discover -s tests -p test_liveness.py`: exit 0, 5 tests, including complete synthetic OAuth-configured entrypoint. No deployed provider/host service used.

### F46 — medium / open — Phone cancel/delete plan actions require a challenge ID the interface never obtains or displays.

Tasks: T15d. Rechecked in this attempt: Fresh source inspection page.tsx: buttons disabled unless confirmation text is nonempty and typedReq matches; user must enter Id del reto. sendCommand only auto-fetches a challenge when challengeId is absent, but these forms require it present. No UI requests/displays an ID for copying. Approve/launch auto-challenge behavior remains valid. ; normal forms need the same server-issued challenge flow.

### F47 — medium / open — Anonymous callers behind Caddy share a login throttle and can exhaust the owner login bucket.

Tasks: T11a. Rechecked in this attempt: Fresh Probe L: exit 0; six synthetic forwarded client addresses reaching one proxy socket receive 302,302,302,302,302,429. server.py keys both login-start and callback buckets on client_address[0]; deployed Caddy is the common upstream peer. An unauthenticated requester can keep the shared five-per-minute start bucket full. Do not trust arbitrary public forwarded headers; derive identity only at the trusted proxy boundary.

### F48 — low / open — The documented gateway minimum key length is not enforced by gateway or native listener startup.

Tasks: T16. Rechecked in this attempt: Source config.py checks nonempty gateway key; bt_server.serve_remote directly constructs loopback ThreadingHTTPServer without checking key length. Runbook steps 2/6 claim refusal below 24. All 5 test_remote_api.py tests pass but no longer test startup minimum length. Probe B parses the gateway with a synthetic key. Keyed requests still fail closed when expected key is empty; no authentication bypass is alleged.

### F49 — medium / open — A malformed authenticated native command drops the HTTP connection before validation instead of returning INVALID_COMMAND.

Tasks: T5. Rechecked in this attempt: Fresh Probe V: exit 0 reproducer. A real loopback POST to bt_remote_api.route_post with synthetic valid gateway key and {idempotency_key:'synthetic-valid-key',command:'pause'} drops the connection with KeyError('target'); the same request without the key returns HTTP 401. bt_remote_commands.fingerprint:264 indexes required fields before validate:268, and Ledger.submit:385-387 catches TypeError/ValueError but not missing-field KeyError. Validate required envelope fields before fingerprinting and return HTTP 400/INVALID_COMMAND. The public gateway fills these keys, so this is native-boundary robustness, not an unauthenticated access bypass.

### F50 — medium / open — Telegram /estado skips every real snapshot run because it reads req_id instead of req/reqId.

Tasks: T14b. Rechecked in this attempt: Updated W: exit 0; actual inlined bt_remote_api._snapshot projects a synthetic active run with req/reqId; real TelegramBot._send_status sends only the Ejecuciones activas header and no run/keyboard because it reads req_id. Only the snapshot data provider is substituted; real serializer and bot parser execute.

### F51 — medium / open — Inline Telegram delivery can block the production five-second liveness polling cadence.

Tasks: T14a, T10. Rechecked in this attempt: Fresh report Probe W/Y/Z/O: exit 0; GatewayRuntime.poll_once with 20 due messages and a deterministic sender advancing the clock by the default 5-second request timeout consumes 100 simulated seconds while making exactly one health probe. app.py calls deliver_due inline and notifications.py sends up to 20 sequential messages before returning. This is a deterministic scheduling reproduction, not a measured real Telegram outage; isolate delivery or give it a budget compatible with the five-second health cadence.

### F52 — low / open — The production command deadline defaults to five seconds instead of the specified fifteen seconds.

Tasks: T10, T13. Rechecked in this attempt: Fresh report Probe W/Y/Z/O: exit 0, GatewayConfig.from_env with required synthetic values and omitted optional overrides returns request_timeout=5.0. app.py passes that same timeout to LaptopClient and upstream.py applies it to command POST. SPEC edge case requires the gateway to time out after 15 seconds. Use a separate 15-second command deadline; the shorter timeout fails safely as UNKNOWN_OUTCOME and does not itself prove duplicate execution.

### F53 — medium / open — An offline transition caused by a command or challenge suppresses the required long-offline active-run alert.

Tasks: T10, T13, T14. Rechecked in this attempt: Fresh report Probe W/Y/Z/O: exit 0. With cached active-run state, three synthetic UpstreamError command failures mark the laptop offline but leave offline_generation=0; a subsequent health poll at offline_since+901 seconds emits no outbox row. Repeated through issue_challenge with the same result. app.py/180 discard the transition; only poll_once advances the generation, so _notify_long_offline_with_active_run returns early. Handle every transition through one owner and preserve one alert per outage.

### F54 — medium / open — An explicitly empty gateway bind is accepted and passed to the HTTP server as a wildcard address.

Tasks: T10. Rechecked in this attempt: Fresh report Probe W/Y/Z/O: exit 0. GatewayConfig.from_env and OAuthConfig.from_env accept required synthetic configuration with GATEWAY_BIND=''; create_server passes ('',8790) to the mocked ThreadingHTTPServer constructor (Python IPv4 wildcard bind semantics). No wildcard listener was actually opened. config.py uses get without rejecting the empty value; deploy.sh required-key checks omit GATEWAY_BIND. The runbook correctly instructs 172.20.0.1 (F1 fixed), but malformed production config still fails open at this boundary. Reject empty/wildcard binds or normalize deliberately to the documented private interface. No unauthenticated command bypass is alleged.

### F55 — high / fixed — Persisted first-observation cursors deliver late-derived events after an earlier saved cursor.

Tasks: T6. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe R (`python -`): exit 0; persisted observation cursor delivers late stall/round after an older saved cursor and advances sequence. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py`: exit 0, 14 tests.

### F56 — medium / open — Quoted JSON credentials and database connection passwords remain visible inside log and verification strings.

Tasks: T6, T7, T15c. Rechecked in this attempt: Fresh Probe S: exit 0; feed.redact leaves synthetic password and refresh_token values in serialized JSON and the synthetic DATABASE_URL password unchanged. The exact phone redactReviewText also leaves the quoted JSON password; structured dict password is correctly redacted. bt_remote_events.py,34-42 requires an unquoted name adjacent to colon/equal inside strings; bt_remote_api.py passes logTail and verification text through it. F14 remains fixed only for its original plain provider assignment and bearer-text cases, both freshly rechecked. The observed gap is bounded to these synthetic known credential forms, not a claim that arbitrary secret detection is exhaustive.

### F57 — medium / open — Gateway cursor reconstruction starts from the beginning and lets old feed pages delay fresh notifications beyond 60 seconds.

Tasks: T14. Rechecked in this attempt: Updated Probe T: exit 0; a fresh runtime calls events with empty cursor and sends a run.finished that predates startup but is within the restored one-hour expiry. Gateway still keeps event_cursor only in memory and invalid-cursor reset also starts from beginning. The former continuous-outage generation-reset component is now repaired: with one durable database and simulated wall/monotonic clocks, outage generation stays 1 across replacement runtimes and total sends stays 1. Same-ID outbox dedupe also remains effective. Only rebuild-from-now remains open; no accepted risk. New Probe AF: exit 0; 3,000 older non-notifying command events precede a fresh round in the persisted feed. _poll_events consumes only one 200-event page per five-second poll and ignores hasMore: no alert after thirteen polls (t=60 s), new round queued on poll sixteen (t=75 s). This is deterministic page/cadence arithmetic, not a live latency measurement.

### F58 — medium / open — Quota notifications have per-account triggers without the frozen all-accounts-exhausted condition.

Tasks: T6, T14. Rechecked in this attempt: Fresh Probe U: exit 0; build_events receives one exhausted account and one available account, yet notification_for_event creates a quota-exhaustion alert. bt_remote_events.py emits independently per profile and notifications.py renders each; neither checks whether every account is exhausted as required by R10. This is an alert-condition/spec gap, not proof that all-account exhaustion receives no messages. Preserve source freshness and dedupe when introducing the aggregate condition.

### F59 — medium / open — The same failed attempt can enqueue two alerts when first observed in the flow bus and later in the run projection.

Tasks: T6. Rechecked in this attempt: Fresh Probe U: exit 0; failure of demo/REQ-001 T1/a1 is first represented by flow row flow-1, then by the run-state attempt with its ended_at one second later. Real build_events/page and NotificationOutbox store two different dedupe-key rows. bt_remote_events.py suppresses flow duplicates only inside one current projection; from_flow identity at 176-178 differs from the attempt identity at 79, so sequential observations bypass durable dedupe. These fixtures demonstrate one semantic failure under both producer forms, not a measured frequency in a deployed run. R11 requires a stable key for the same event.

### F60 — low / open — An unauthenticated Unicode OAuth state drops the callback connection instead of returning a controlled invalid-state response.

Tasks: T11. Rechecked in this attempt: Fresh Probe X: exit 0; real loopback gateway GET callback with synthetic code, query state=%C3%A9 and cookie flow_oauth_state="é" terminates its request with TypeError from hmac.compare_digest on non-ASCII strings. The handler error hook records TypeError and HTTP client gets RemoteDisconnected. server.py does not validate ASCII before comparison. No state bypass, session issuance or whole-process denial of service is demonstrated; the existing one-use/replay protections remain.

### F61 — high / fixed — Blocked events now have run-scoped identities, including when runs reuse att-0001.

Tasks: T6. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe AA (`python -`): exit 0; two actual M1 runs allocate att-0001, run-scoped blocked events have distinct dedupe keys and outbox keeps both rows. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_events.py`: exit 0, 14 tests.

### F62 — high / fixed — Native failure reviews and the phone request now include the selected run target.

Tasks: T7. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe AA (`python -`): exit 0; actual runs sharing att-0001 return their respective distinct causes via target-specific native review. `cd skill/scripts && python -m unittest discover -s tests -p test_remote_review.py`: exit 0, 3 tests including actual HTTP second-run selection/missing/foreign target refusal. Both phone callers include target; AG confirms public review HTTP 200.

### F63 — high / open — Fresh rounds created in the laptop local timezone still expire before Telegram delivery because their naive timestamps are interpreted as UTC.

Tasks: T6. Probe AC (`python -`): exit 0 with TZ=America/Bogota/time.tzset; actual bt_rounds.new_round creates a fresh naive local created_at on a two-hour-old plan; feed.collect now correctly chooses created_at instead of PLAN.md time, but event_timestamp treats naive time as UTC. Real GatewayRuntime/outbox records dropped/expired at attempt 0 and sends nothing: apparent age is five hours. UTC-source timestamp component is repaired, timezone normalization is not. Preserve truthful creation time and one-hour expiry; produce an explicit timezone/UTC contract.

### F64 — medium / open — The routes endpoint lists unknown-quota routes as available while retry refuses those same candidates.

Tasks: T8. Rechecked in this attempt: New Probe AD: exit 0; one synthetic candidate with valid authorization/runtime/source and quota_status=unknown is listed available by actual bt_remote_recovery.route_options, but actual bt_route_pins.available with identical candidate/route returns []. The former checks quota != exhausted; the latter requires quota == available. No actual account/quota source was read. Use the same availability rule; refusal is safe but contradicts the selectable route list.

### F65 — medium / fixed — Linux without systemctl retains the local panel startup path while uncertain systemd ownership fails closed.

Tasks: T9. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe AE (`python -`): exit 0; shutil.which(systemctl)=None causes one mocked detached startup and no systemctl call. Present-but-failing systemctl still fails closed without a competing server. `cd skill/scripts && python -m unittest discover -s tests -p test_platform.py`: exit 0, 28 tests, including the missing-systemctl startup regression. Earlier AE stubbed subprocess failure while leaving discovery reporting an installed binary; that no longer models an absent binary.

### F66 — high / open — The keyed laptop challenge endpoint was removed, making all challenged web operations unreachable.

Tasks: T5b. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe AG (`python -`, report): exit 0; actual bt_server.RemoteHandler POST /api/remote/v1/challenges with valid synthetic bearer returns HTTP 404 NOT_FOUND; main-equivalent authenticated public gateway returns HTTP 200 NOT_FOUND without challengeId. route_post handles commands only; Ledger.issue_challenge is not exposed over HTTP. Approve/launch/revise/edit-brief cannot obtain required challenges. Preserve target-bound one-use 120 s enforcement when restoring issuance.

### F67 — high / open — The actual laptop run projection cannot satisfy the new exhaustion predicate, so exhausted failures never notify.

Tasks: T6. Rechecked on 212abc5a76f2f852b06d45763b9640b0babc67b6: Probe AH (`python -`, report): exit 0. Real T17/M1 scheduler fixture exhausts max_attempts=3 and actual live projection has attempts=3 and three failed history records, but omits attempts_used/max_attempts/retries_remaining/retry_exhausted required by _retry_exhausted. Actual build_events returns []. The exact T17 test also fails with empty real keyed events. Current from_flow expansion still requires the same absent budget evidence; no fabricated producer fields or relaxed retry filtering are a repair.

### F68 — low / open — Immediate command error responses forward handler exception text without redaction.

Tasks: T5. Fresh Probe AJ (`python -`, report): exit 0. Injecting a handler ValueError with a synthetic FLOW_GATEWAY_KEY assignment into the real native HTTP command path produces FAILED/EFFECT_FAILED with that text unchanged through GatewayRuntime; the existing redactor removes it when explicitly called. Ledger.submit catches str(exc)[:300] without sanitizing. Public command history correctly excludes the exception value. This confirms the error boundary with an injected failure, not a built-in secret-bearing exception, live credential leak or theft; severity stays low.

## Frozen coverage and handoff

| Scope | Current disposition |
|---|---|
| R1/R2/R3/R16/R17 | Key/OAuth/Origin/kit checks run; F4/F5/F12/F27/F31/F47/F48/F54/F60 remain. No deployed claim. |
| R4/R7/R9/R15 | Native model/review/history repaired; high F36 blocks phone snapshots. Cache/offline time/SSE F11/F13/F21, metadata F29, quota F44, redaction F56 and polling/delivery F51/F53 remain. |
| R5/R6/R8/R13 | Native reopen/ready retry/round work in C; gateway field forwarding repaired. High F41/F42 editor and high F66 challenge issuance remain. F7/F8/F9/F16/F26/F39/F40/F46/F49/F64 remain. |
| R10/R11/R12 | Run-scoped blocked identities and observation cursors fixed; high F63/F67 lose fresh round/final failure alerts. F6/F30/F37/F50/F51/F53/F57/F58/F59 remain; expiry/backoff/history repaired. |
| R14 | Lint/types/production build pass; browser width F18 fails; installed PWA and exhaustive touch targets unrun. |
| R18/T17 | 28 platform, 43 page and 18 operations tests pass, absent-systemctl F65 fixed. E2E F2 fails before claimed scenarios; the other missing production boundaries are directly checked by AG. |

Return T17 (F2), T12 (F36), T8a (F41/F42), T6 (F63/F67) and T5b (F66) for rework. Preserve repaired Caddy topology,
module packaging, field forwarding, run-scoped identity/review, observation cursors, retry filtering, durable
outage dedupe, one-hour expiry/backoff/history, stream fan-out, session revocation and env permissions.
No source fix can be made by this read-only task. Medium/low findings, including new F68, stay recorded until fixed or owner-accepted.

## Reproduction commands

Run blocks from repository root after the lockfile installation. Each creates temporary scratch state inside this
worktree and cleans it on exit. They use no real account readers or services. Exit 0 confirms the stated observation,
including defects; it does not mean product acceptance. C/E seed real Ledger challenges directly to isolate commands;
AG separately proves HTTP issuance unavailable. Agent starts/availability are stubbed only where explicitly stated.

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
  print('Edit adapter preserves field/value; current E independently checks downstream failures.')
 finally:
  server.shutdown();server.server_close();worker.join();runtime.outbox._db.close()
PY_AUDIT
```

### Probe G — structured HTTP cursor reset and failed-effect HTTP 200

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
  def post_json(self,*args):return {'status':'FAILED','code':'ROUTE_UNAVAILABLE','outcome':{'error':'synthetic route unavailable'}}
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
  assert response.status==200 and payload['status']=='FAILED'
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
  print('connection refused',result);assert result['code']=='UNKNOWN_OUTCOME'
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
   assert result['status']=='FAILED' and 'brief' in str(result)
   print('CURRENT F41: phone field/value rejected, revision unchanged',revisions.latest(rdir)['revision'])
   for n,field in enumerate(('acceptanceCriteria','acceptance_criteria'),2):
    result=send(n,field,['Owner edits T1 criteria']);assert result['status']=='FAILED' and 'brief' in str(result)
   assert revisions.latest(rdir)['revision']==1
   # Exercise legacy brief contract independently to inspect the approved-base/rollback safeguards.
   def legacy(key,brief):
    challenge=commands.Ledger().issue_challenge('demo/REQ-001','REQ-001')
    state=commands.target_state('demo/REQ-001','edit-brief',{'task':'T1'})
    result=runtime.submit_command({'schemaVersion':1,'idempotencyKey':key,'type':'edit-brief','target':{'kind':'task','project':'demo','req':'REQ-001','taskId':'T1'},'precondition':{'state':state['state'],'revision':state['revision']},'brief':brief,'confirmation':{'challengeId':challenge['challengeId'],'typedReq':'REQ-001'}})
    print('legacy edit',result);return result
   original=path.read_bytes();working=json.loads(original);working['tasks'][1]['objective']='UNAPPROVED unrelated T2 change';path.write_text(contract.dumps(working))
   result=legacy('synthetic-drift-key','Owner edits only T1')
   latest=revisions.latest(rdir)['revision'];frozen=revisions.load_revision(rdir,latest)
   print('CURRENT F42 drift latest',latest,'T2',frozen['tasks'][1]['objective'])
   assert latest==2 and frozen['tasks'][1]['objective']=='UNAPPROVED unrelated T2 change'
   (rdir/'PLAN.md').write_text(plan_md.format(status='review'));before=path.read_bytes()
   result=legacy('synthetic-refused-key','Edit must roll back')
   print('CURRENT F42 refused status',result['status'],'working bytes retained',path.read_bytes()==before,'latest revision',revisions.latest(rdir)['revision'])
   assert result['status']=='FAILED' and path.read_bytes()!=before and revisions.latest(rdir)['revision']==3
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
  status,body=call('GET','snapshot');print('AG production snapshot',status,'keys',sorted(body),'nested runs',len(body['snapshot']['runs']))
  assert status==200 and len(body['snapshot']['runs'])==1 and 'runs' not in body
  js="""const fs=require('node:fs'),vm=require('node:vm'),ts=require('./remote/web/node_modules/typescript');const source=fs.readFileSync('remote/web/src/app/page.tsx','utf8');const code=source.slice(source.indexOf('type Target'),source.indexOf('function prettyTime'));const sandbox={input:JSON.parse(fs.readFileSync(0,'utf8')),exports:{}};vm.createContext(sandbox);try{vm.runInContext(ts.transpileModule(code+';parseSnapshot(input)',{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,sandbox);process.exit(2)}catch(e){console.log('AG phone rejects public snapshot:',e.message)}"""
  p=subprocess.run(['node','-e',js],input=json.dumps(body),text=True,capture_output=True);print(p.stdout.strip());assert p.returncode==0
  for path in ['commands','history','attempts/att-0003/review?target=demo%2FREQ-001','events']:
   with patch.object(bt_subscriptions,'summary',return_value=[]):status,body=call('GET',path)
   print('AG public read',path,status,sorted(body));assert status==200
  status,body=call('GET','events/stream');print('AG phone SSE route',status,body);assert status==404
  challenge={'target':'demo/REQ-001','typedReq':'REQ-001'}
  for native in [True,False]:
   status,body=call('POST','challenges',challenge,native);print('AG challenge native',native,status,body);assert 'challengeId' not in body
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
 assert 'attempts_used' not in task and 'max_attempts' not in task
 events=feed.build_events({'runs':runs});print('AH real exhausted feed',events)
 assert not any(e['type']=='attempt.failed' for e in events)
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

## Final artifact checks

All three exact frozen `test -s remote/docs/audit.md` entries exit 0. JSON parses as `audit-findings/1`, with 68 unique
IDs, valid frozen task references, permitted status/severity values, fresh command/result evidence on every fixed
entry and no accepted risks. Report and ledger verdicts agree. Both files have no conflict markers.
`git diff --check` and an allowed-path assertion pass; only these two documents differ from entry HEAD.

Seven high findings remain open. Return T17 (F2), T12 (F36), T8a (F41/F42), T6 (F63/F67) and T5b (F66).
Their repair cannot be performed within this read-only task. The independent checker decides the outcome;
this report does not declare the task verified or the substantive high-fixed criterion satisfied.
