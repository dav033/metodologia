# Findings against the supplied blueprint

Observed 2026-10-13, checkout `/home/david/dev/metodologia`, initial HEAD `9139ec95a5bc9e883e3ee6b884d765825db1a1e8`. The worktree is active and dirty; include untracked files. Initial source inventory: 69 top-level Python modules and 34 test files, not merely “40+”. See evidence/source-manifest.json. These findings describe observations, not completed repairs.

| ID | Finding / evidence | Required plan correction |
|---|---|---|
| F01 | Actual path is `~/dev/metodologia`; `~/.agents/skills/metodologia` points to its `skill/`; `~/bitacora` points to repository `bitacora/`. SUMMARY contains older Windows/machine facts. | Resolve roots per machine; do not relocate data or overwrite links from stale prose. |
| F02 | `skill/scripts/bt_core.py:38–43` derives templates and script location from `__file__`; scripts are flat modules with absolute `bt_*` imports. | `packages.find where=skill/scripts` alone does not establish package discovery, resource inclusion or entrypoint correctness. Build a real package, resource accessor and wheel tests. |
| F03 | `bt_agy.py:33` already builds `--print=<prompt>` plus stream-json and timeout; `bt_runprompt.py:261` calls it. | The attachment's stream-JSON stdin rewrite is unproven and contradictory to this integration. Capture the installed CLI protocol before changing it. Do not hardcode speculative model IDs. |
| F04 | `bt_hooks.py:45` already detects redirects, tee, heredocs and PowerShell writes. | Characterize gaps and false positives; do not reimplement an allegedly missing feature. Stop logging and source-size checks are different capabilities. |
| F05 | `install.py:174` filters non-existent account directories; `_merge_hooks` identifies owned hooks by a string marker. | Provision directories explicitly in an installer transaction, with ownership manifest, validation and rollback. A directory is not proof of authentication. |
| F06 | Actual additional IDs: claude-personal, claude-work, codex-1, codex-luis, antigravity; generic claude/codex aliases also exist. claude-work is work_only. | Keep identities and dedup account keys; cannot promise five eligible accounts for every project. Do not rewrite IDs to claude-1/2 or agy-main. |
| F07 | `bt_agents.py:295` ranks busy, family avoidance, role and quota pressure before success band. `_stats():236` aggregates success by provider/model/kind, not account. | Changing unseen band 3→4 cannot guarantee fair scheduling. Add bounded exploration with tests, respecting role/work/quota constraints. |
| F08 | `bt_runstate.py:49` drops files metadata; MAX_WORKERS=2 at :343; bt_worktree.py does not exist. | Add versioned ownership/state contracts and recovery before raising concurrency. Disjoint filenames are insufficient for shared build/database/generated-output conflicts. |
| F09 | `bt_lock.py:1` deliberately proceeds unlocked after timeout; stale lock reclaimed at 60 seconds. | This lock MUST NOT be reused unchanged for merges. Introduce fail-closed integration ownership with process/host identity and liveness; test lease contention/crashes. |
| F10 | Attachment uses `worktree add -B` and forced removal, with only the second concurrent worker isolated. | No branch resetting or forced removal. Isolate every writer; retain dirty/conflicted work; integrate serially in a dedicated worktree and verify combined HEAD. |
| F11 | `file_guard.py:1` is explicitly nonblocking and warns above 500 lines. | A new hard 500-line gate changes policy; thresholds are review signals under owner standards. Keep advisory behavior until deliberately approved. Never blanket-block legacy files. |
| F12 | `bt_profiles.py:136` scrubs selectors and all ANTIGRAVITY_*; adding shared Claude/Z.ai selector sets interacts with `_foreign_selectors`. | Introduce driver auth families, distinguish known account selectors from session-only variables, test both directions and ambient inheritance. Empty API_KEY alone does not prove billing isolation. |
| F13 | `bt_vcs.py:52` can auto-commit/push; `next_id` invokes pull --rebase --autostash. | Planning forbids automatic git mutation. REQ allocation used the existing ID machinery with pull suppressed only in the invoking process; no product code changed. Migration policy must honor user authorization. |
| F14 | `bt_profiles.doctor():302` emits binary/launchable/auth, not attachment's `installed:true`. | Use actual output contract; add versioned diagnostics deliberately. Separate fake-CLI contract tests from authenticated live proof. |
| F15 | `bt_subscriptions*`, `bt_quota_live`, `globalusage`, `bt_relay*`, `relay_run` and `bt_quality` exist in the dirty tree. | Include quotas, relay and defect metrics in package and parity map; omission would lose current work. |
| F16 | Removing updater lock solely because it is 15 minutes old does not establish that its owner died. | Never unlink a live/unknown provider lock. Return actionable diagnostics; recovery requires verified ownership/death and authorized maintenance. |

## Additional findings from Claude Haiku max, checked by coordinator
- F17: `bt_agents.account_key():182–191` serializes every profile env key/value into the quota identity. Putting a Z.ai token in profile env would expose it in persisted keys. Account identity must use non-secret selectors/opaque IDs; include sentinel-secret tests across quota/events/logs. Ambient-account recognition also needs tests with unrelated ANTHROPIC_MODEL variables.
- F18: `bt_runsettle.verify_task():182–187` replaces workdir with the registered repo when a task has repo metadata. Worktree verification therefore needs an explicit immutable task→worktree mapping; changing only session cwd tests the wrong tree. Branch/ref instruction generation and review consumers must use the assigned branch. `RUN` must freeze files/ownership and report drift like verify/repo/after.
- F19: `ops_parallel_check.py:1` tests two different repos using stub agents; it cannot prove same-repo worktree correctness. Existing ops-matrix checks do not establish the proposed agy account matrix. New acceptance tests are required.
- F20: Current web merge is explicit (`bt_server.py:208` / `bt_review.py`). Future automated worker integration must be narrowly authorized for the dedicated feature integration branch and never substitute for final owner-controlled merge/publish.

Haiku's complete report is in evidence/haiku-code-review.md. It also read the dossier while it was being written; its citations of our findings are corroboration, not independent external verification. The wording “owner-authored” in its report is inaccurate: the coordinator authored the proposed SPEC from David's request, and it is not approved. Its recommendation to “fix duplicate D-004” is narrowed to preserving history and disambiguating links, not renumbering old records during extraction.

## External checks (primary sources, retrieved 2026-10-13)
- [Archify package](https://github.com/tt-a1i/archify/blob/main/archify/package.json): current layout is `archify/bin/archify.mjs`; package reports 3.1.0, Node >=18, ten diagram types and development dependencies. Vendor a pinned runtime closure, generated assets and notices; “zero runtime dependency” does not mean its build/test stack has none. The five requested types remain the product acceptance scope. Do not promise “99 checks” without pinning and executing the relevant validator.
- [Matt Pocock skills](https://github.com/mattpocock/skills): current catalog supports reusable disciplines and explicit orchestrators. Its TDD description retains red-green-refactor; the attachment's blanket deferral of refactoring is an adaptation, not a verified upstream requirement. Keep governance local; prove debug loops and avoid an arbitrary universal <10s gate that blocks distributed/slow defects.
- [Z.ai quotas](https://docs.z.ai/devpack/overview): published off-peak 0.5×, peak 1×, weekday 14:00–18:00 UTC+8. The attachment's 2.5× peak is not this published multiplier; it can only be a separately named preference. Use local weekday in Asia/Singapore and event time, not current wall time to reprice historical attempts.
- [Z.ai FAQ](https://docs.z.ai/devpack/faq): error 1113 can indicate wrong endpoint or unsupported usage, not just an exhausted quota. Do not retry/cool down every 1113 blindly. The documented compatible endpoint is `https://api.z.ai/api/anthropic`; avoid Markdown URL markup in JSON. Model availability, auth and returned token fields still need account-specific validation at activation.

Benchmarks and context-window figures in the source proposal are not migration acceptance evidence and were not validated here. Licensing must be checked at the selected immutable upstream revisions before copying files.

## Baseline verification
Executed `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -q` on Python 3.14.7: **578 tests, 2 failures**, 58.648 seconds. Existing discovery sets a temporary BITACORA_ROOT in `test_00_isolation.py`.
Failures: `test_audit_routing.AuditRoutingTests.test_automatic_audit_prefers_claude_over_provider_diversity_and_pool_order` and `test_subscription_usage.SubscriptionUsageTests.test_audit_provider_preference_is_not_overridden_by_codex_headroom`. Both expect Claude and receive Codex. They precede any implementation by this session; this does NOT establish failure on origin/main. Reconcile policy/test expectations before extraction; do not delete tests or lower checks.
The log also includes a thread RuntimeError("network") in the relay error-path test; classify its observability separately, not as a third unittest failure. No lint/type/build/platform/live-provider certification was executed for migration implementation, which does not exist yet.

## Trace check
The existing trace command exits 0 but reports global warnings/errors (including REQ-006 uncovered stories and relay references to absent IDs). No REQ-007 issue appears in this run. Full output is preserved; this is not a clean global trace certification. Historic DECISIONS also contains duplicate D-004 headings; do not reuse or silently renumber them during migration.

## M1 characterization findings (2026-10-13, session 862a2e59)
- F-M1-01: `config set` drops unknown sections, invalid values and defaults (R4 gap for machine settings).
- F-M1-02: shell-mutation heuristic misses `cp`/`mv`/`rm`/interpreter writes and flags quoted `>` text.
- F-M1-03: audit routing had two incompatible orders in the dirty tree; resolved by D-013.
Details: [COMPATIBILITY-MATRIX](evidence/COMPATIBILITY-MATRIX.md).

## M3 driver-contract findings (2026-10-13, session 862a2e59)
- F-M3-01: `bt_runsettle._TRY_AT` is case-sensitive: "Try again at Oct 13th, 2099 1:08 AM." yields no reset epoch (0) while
  "try again at ..." does. Providers observed so far print lowercase. Pinned by fixture choice, not changed (behavior change
  needs its own evidence).
- F-M3-02: `subprocess.TimeoutExpired.stdout` is bytes even with `text=True`; any runner must decode it (done in `bt_driver.py`).
