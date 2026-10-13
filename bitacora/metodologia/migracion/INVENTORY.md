# Preservation and ownership map

All paths below are relative to `/home/david/dev/metodologia`. Owners are future implementation responsibilities, not separate services. Machine paths and auth selectors are private state, not portable account credentials.

| Capability / source | Destination owner | Compatibility evidence required |
|---|---|---|
| `bitacora.py`, `bt_cli_accounts.py` | CLI transport | Command/option/exit/output inventory; old script versus installed CLI fixtures |
| `bt_core`, `bt_views`, `bt_index`, templates | documents + resources | IDs, slugs, dates, week grouping, central docs, template expansion, indexes |
| `bt_workspace` | workspace use cases + filesystem adapter | project.json portable metadata, local path overrides, worktree membership, multi-machine hints |
| `bt_rounds`, `bt_pending`, `bt_trace`, `bt_audit`, `bt_review` | planning/review use cases | Rounds, approval, graph IDs, commit trailers, reports, review/merge authorization |
| `bt_handoff`, `bt_launch`, `bt_watch` | orchestration | Risk gates, launch modes, observer behavior, no duplicate launches |
| `bt_run*`, `bt_runtask`, `bt_runtier` | supervisor | RUN.json, plan fingerprint, task ownership, auditing/final sessions, retry/timeout/restart |
| `bt_agents`, `bt_profiles`, `bt_delegate`, `bt_agy` | routing + provider adapters | Five real identities, work-only, account dedup, effort/model, failures, stdin lifecycle |
| `bt_events`, `bt_quality` | telemetry | JSONL schema, nulls, model/family attribution, defect/rework metrics |
| `bt_subscriptions`, `bt_subscription_sources`, `bt_subscription_schedule`, `bt_quota_live`, `globalusage` | quota adapters | 5h/7d windows, cache TTL, pressure, cooldown, wrappers and history |
| `bt_relay*`, `relay_run` | relay use cases + terminal/process adapters | Handoff files, pane identity, end-of-turn gate, process identity, no wrong-terminal typing |
| `bt_learn`, `bt_context` | memory/context | Accepted and candidate learnings, scope, evidence, global/project context |
| `bt_hooks`, `file_guard` | harness adapters | Claude/Codex schemas, start/stop/end, shell edits, warning policy, deadlines |
| `bt_server`, `bt_pages`, `bt_page_*`, assets | web transport/resources | Existing routes/forms, approval authorization, graph/artifact/metrics views, server start/readiness |
| `bt_config`, `bt_lock`, `bt_platform`, `bt_nowindow`, `bt_notify`, `bt_autostart` | infrastructure | Config defaults/overrides, locks, detached process/terminal behavior, notifications/startup |
| `bt_vcs`, `bt_secrets`, githooks | repository/security adapters | Scoped git actions, gitleaks, no unintended remote writes, readable errors |
| `install.py`, `install_agents.py`, RTK installation | installer | Links/junctions, Python executable, existing unrelated hooks, agents, wrappers, rollback |
| SKILL + references + six agent definitions | policy/resources + thin harness catalog | Rules by responsibility, trigger coverage, invocation tests, no duplicate contradictory instructions |
| tests, evals, `ops_*_check.py` | verification | Preserve fixtures, isolation and behavioral eval contracts; classify scripts that spawn agents before running |

## Persistent state classes
1. User records under `<BITACORA_ROOT>/<project>/`: central Markdown, requirements including SPEC/PLAN/RUN/HANDOFF/REPORT, rounds, daily/weekly/monthly logs, artifacts and source IR. Preserve IDs, links and history; no directory moves in core extraction.
2. Shared/local state under `<BITACORA_ROOT>/.state/`: discover every filename from source and filesystem metadata in M0, including profiles, config, workspace mappings, sessions, ID counters, events, quota caches, delegates and relay. `.gitignore` is NOT a backup strategy.
3. Per-requirement execution state, ownership locks, live PID/start identity, heartbeat and worktrees. Backup content does not transfer process ownership. New runtime must reconcile liveness before resuming.
4. Installed surfaces: skill symlink/junction, hooks/settings/agent files, wrappers, shell/terminal launchers and autostart entries. Record preimage/checksum for only owned changes and preserve unrelated edits on rollback.
5. Credentials remain in provider-owned directories/keyrings. Do not export to this dossier. Inventory references/permissions only; sensitive backups require restricted local storage and explicit activation procedure.

## Resource/package boundary
Use `src/bitacora/` with CLI, application responsibilities, provider adapters and infrastructure. Bundled templates/assets/policy use `importlib.resources` or explicit configured external roots. Writable data never lives in site-packages. `workspace/` may contain development sources for thin adapters, but wheel builds must include the resources needed by installed operation; editable checkout references are insufficient.

Do not mechanically reorganize every module into six folders in one commit. First establish an installable canonical implementation and compatibility entrypoints; then move responsibility groups with import/resource tests. A compatibility adapter must not create two independent module instances/global ROOT values. Existing tests monkeypatch module globals: protect behavior without creating dual implementations.
