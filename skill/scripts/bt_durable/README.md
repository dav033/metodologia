# `bt_durable` — the durable execution runtime (REQ-030)

The legacy Scheduler (M1–M6) owns its state in a hand-built SQLite document, five outboxes, a second state machine in
the executor ledger, a watchdog, hold files and about seventeen retry/healing loops. `bt_durable` keeps Metodología's
decisions and hands the generic machinery to mature tools:

| Plane | Package | Owns | Does not own |
|---|---|---|---|
| Control | `bt_durable.control` | what is ready (legacy plan + resource rules), what a failure is (one 10-class taxonomy), what to do next (bounded policy) | anything durable; it imports no `dbos` (tested) |
| Execution | `bt_durable.execution` | DBOS workflows/steps/queues: run → task → agent / verify / integrate; durable waits for quota and for the owner | domain rules |
| Process | `bt_supervisor` | agent processes as systemd user units on cgroup v2 (process-group fallback): idempotent launch, tree kill, limits, OOM, exit record | deciding success |
| Evidence | M6 (`bt_scheduler_quality`), `adapters/telemetry.py` | sandboxed verification and its content-addressed evidence; JSON-lines telemetry | — |

Contracts between them are Pydantic models in `bt_contracts` (`execution`, `failure`, `owner`, `remote`). The
legacy core and executor are reached only through their adapters (`bt_durable/legacy.py`).

## What was delegated, what was kept

- **Delegated to DBOS**: run/attempt persistence, step checkpoints, crash recovery, queues and concurrency, durable
  sleeps (quota resets, backoff), durable messages (owner answers, run commands), cancellation, workflow identity.
- **Delegated to systemd/cgroups**: process identity, tree termination (`cgroup.kill`), memory/tasks/CPU/runtime limits,
  OOM detection, freezing, restart of the engine (`Restart=always` instead of the watchdog).
- **Kept (CONSERVAR)**: frozen-plan loading and validation, resource claims, worktrees per attempt (`GitWorkspaces`),
  briefs/prompts/provider drivers and account gates, deterministic handoff snapshots, the M6 verifier and its policy,
  the integration line (now compare-and-swap), owner decisions.
- **New Metodología logic**: evidence-based classifier, bounded recovery policy (re-verify instead of re-run for
  environment limits, durable quota waits, one coordinated remediation, escalation with options), migration bridge,
  plan pre-flight: the typed plan contract (`bt_contracts.plan`, `PLAN_CONTRACT`) then `bt_planner.preflight`.

## Install (Linux)

```sh
cd ~/dev/metodologia && uv sync            # pydantic, psutil, dbos (pinned in uv.lock); dev: hypothesis, ruff
# optional, recommended for durability: a loopback PostgreSQL for the DBOS system database
docker run -d --name metodologia-dbos-pg --restart unless-stopped -p 127.0.0.1:5435:5432 \
  -e POSTGRES_PASSWORD="$(openssl rand -hex 16)" -v metodologia-dbos-pg:/var/lib/postgresql/data postgres:16-alpine
python3 skill/scripts/bitacora.py config set execution.database_url 'postgresql://postgres:<pw>@127.0.0.1:5435/bt_durable'
# without it, the system database is SQLite under <state>/durable/dbos.sqlite3 (single host, polling waits)
install -Dm644 skill/scripts/bt_durable/deploy/bt-durable.service ~/.config/systemd/user/bt-durable.service
systemctl --user daemon-reload && systemctl --user enable --now bt-durable.service
```

Hooks, the bitácora CLI and the legacy runtime keep running under the system interpreter (stdlib only,
`test_stdlib_boundary`). Only the engine, the CLI below and the new tests need the uv environment.

## Use

```sh
uv run bt-durable start pictures REQ-031          # a NEW run: pre-flight, owner record, enqueue (idempotent)
uv run bt-durable status pictures REQ-031         # summary, task states, open decisions with their request ids
uv run bt-durable answer pictures REQ-031 T2 T2:d1 retry_with_note --note "…"   # stale request ids are refused
uv run bt-durable pause|resume|cancel pictures REQ-031
uv run bt-durable retry-task pictures REQ-031 T2 --note "…"
```

## Panels and remote control (M7)

`bt_durable.projection` derives one JSON read model per run from DBOS only (workflow statuses, inputs/outputs, the
`summary`/`state`/`decision` events): `<root>/.state/durable/projections/<project>/<REQ>-r<N>.json` (0600 file, 0700
directories; `bt_durable_panel.path`). The engine refreshes it every 5 s (`serve(project_seconds=…)`) and
`bt-durable project PROJECT REQ` rebuilds it; no workflow reads it back. `sequence` is monotonic (+1 per change, a
rebuild without the file starts at the current time in ms); `status_seq` / `tasks[].seq` / `decisions[].seq` are the
sequence of each subject's last change. Task states: `pending queued waiting_quota running verifying recovering
needs_decision blocked failed completed cancelled`; run: `running paused completed blocked failed cancelled`.

The stdlib panels read it through `bt_durable_panel` (stdlib only): `bt_planstatus` (plan pages, list, flow, now),
the run tab, `bt_remote_snapshot` (states mapped to the snapshot vocabulary: queued/waiting_quota → `ready`,
recovering/needs_decision → `rejected`, failed → `blocked`; `revision` = the subject's sequence; decision ids name
the task round, `T2:d1@k3`). Remote `pause`/`resume`/`reopen`/`retry` (no route pins)/`answer-decision` go through the
ledger to `bt-durable remote PROJECT REQ` (JSON on stdin; `execution.durable_cli` overrides how it is reached): it
rebuilds the projection, refuses a stale command (`expect.revision`/`state` differ, decision no longer open, command
not applicable) and sends a DBOS message keyed by the ledger's idempotency key, carrying `expect_paused` /
`expect_round`, which `bt.run` checks again on receipt (`command_refused` in telemetry). Commands without those
fields (every message recorded before M7) take exactly their old path.

`execution.backend` (`legacy` default | `dbos`) names the runtime for new runs; `execution.routes`
(`provider:profile:model[:effort]`, in order) the allowed routes; `execution.agent_concurrency` / `verify_concurrency`
the queue sizes. An existing run never changes owner implicitly: `RUN.owner.json` decides, and the legacy owner refuses a
run owned by the durable runtime (`OWNED_BY_DBOS`).

## Routing

`execution.router` (`m2` default | `static`). With `m2` each routing decision asks the M2 decision engine (through its
one door, `bt_scheduler_decision_adapter.durable_route_ranking`) to rank the allowed routes for the task: the list is the
authorization and the baseline order, the live subscription reading (`LiveQuota`, bt_quota_live, cached 60 s) is the
capacity. M2 applies its hard filters (profile authorization and work gate, runtime on PATH, sign-in, capacity,
cooldown marks when no live reading says otherwise), its route policy (baseline order kept except for docs tasks, which
prefer headroom) and one candidate per account.

- A route refused for a known reason (exhausted, cooling down, unauthorized, signed out, no runtime) is never chosen:
  no attempt is spent on it.
- A route whose capacity cannot be read runs only when no route has known capacity, in the operator's order (the
  static list's old behaviour; the agent's own usage-limit answer is then classified `quota` and waited for).
- Nothing can run: a durable `wait` until the earliest known reset or cooldown end, otherwise `unavailable` (the owner
  decides). A full window whose reset already passed is unknown, not full. No quota is ever invented.
- Every decision is a `route_decision` telemetry event: chosen route and basis (`m2` | `unknown_capacity` | `none`),
  ranked candidates and rejected ones with M2's reason codes and account references, each route's capacity reading,
  the M2 batch id and input hash, policy versions. The decision is the `bt.route` step's checkpointed result, so a
  recovered workflow replays it instead of deciding again.
- If M2 cannot be built (it refuses a route's identity, an import fails), the engine starts on the static list and
  emits `router_fallback` with the reason.

## Migration of legacy runs

```sh
uv run bt-durable migrate pictures REQ-021            # dry run: per task inherit | reconcile | redo, and blockers
python3 skill/scripts/bitacora.py --project pictures scheduler-op REQ-021 stop --reason "migrate"   # quiesce
uv run bt-durable migrate pictures REQ-021 --apply    # backup, pre-flight, owner → dbos, start with LegacyProgress
uv run bt-durable migrate pictures REQ-021 --rollback # cancel the durable workflows, owner → legacy
```

- *inherit*: the accepted attempt has an M6 PASS (evidence hash checked) for the same task specification and its
  snapshot exists — integrated into the new line in plan order, never re-run.
- *reconcile*: a snapshot exists but the evidence does not prove it — verified again in the sandbox first; a failure
  becomes the first attempt's note and the next attempt continues from that snapshot.
- *redo*: anything else. Blocked tasks keep their diagnosis in the inventory.
- The bridge never writes a legacy store (SQLite read-only) or a DBOS table. Backups use SQLite's online backup with a
  `SHA256SUMS`. Re-applying with the same inventory is a no-op; ownership moves by compare-and-swap.
- Refused while a legacy owner process or a live legacy attempt exists.

## Later stages of a durable run (stage join, D-149)

A durable run is bound to one frozen revision (`RunRef`: line refs, attempt keys and compositions carry `r<N>`). When
«Ejecutar subplan» approves a later stage (D-134), `bitacora.py` freezes it as before and asks `bt-durable join PROJECT
REQ` (`bt_durable.stage_join`) to continue the run there; the legacy Scheduler never takes a durable run.

```sh
uv run bt-durable join pictures REQ-021 --dry-run    # per task: inherit | reconcile | redo, live attempts, redone work
uv run bt-durable join pictures REQ-021              # joined | waiting | refused (JSON)
```

- The run of the new revision starts where the current one is: its run lines, base pins and subplan lines are copied
  (`r<old>` → `r<new>`, create-only), so accepted work and anything an operator committed on a line are kept.
- Accepted tasks whose specification did not change are inherited without a step (`LegacyTask.integrated`); a task with
  a captured snapshot that was not accepted is reconciled (verified again, then continued from its snapshot); the rest
  runs. Composition gates compose again from the copied subplan lines, under the new revision's namespace.
- A stage that changes accepted tasks is refused (`JOIN_NEEDS_CONFIRM`) unless `--confirm`.
- With live attempts the current run is paused and `RUN.join.json` records the request; the engine's reaper pass
  completes it once they end (a refusal is written into the file).
- Then the current run's workflows are cancelled (its open owner decisions end with it), `RUN.owner.json` moves by
  compare-and-swap and the new run starts with the current run's settings; `RUN.durable-run.json` moves last, so an
  interrupted join is finished by asking again.
- No running workflow changes its step sequence: only a new run's input can carry `integrated`, so no patch is needed.

## Recovery and rollback

- Engine crash/kill: systemd restarts it; DBOS recovers this executor's PENDING workflows. An agent that kept running
  in its unit is adopted (the launch step is idempotent per attempt key), never started twice.
- Database outage: DBOS retries its connections; the run continues when the database is back (tested with PostgreSQL).
- Cancel: workflows are cancelled with their children; the engine's reaper terminates any unit whose workflow is
  terminal and the supervisor proves no marked process remains (otherwise the attempt stays busy).
- Rollback of the whole runtime: `migrate --rollback` per run, `execution.backend=legacy`, stop `bt-durable.service`.
  Legacy state was never modified, so the legacy owner resumes from where it stopped.

## Upgrading workflows

The engine sets `enable_patching=True` (DBOS pins the application version, so code changes do not orphan PENDING
workflows). A change to a workflow's sequence of steps goes behind `if DBOS.patch("<name>"):`. **Place a patch right
before a plain step, never right before `DBOS.recv`, `DBOS.sleep`, `get_result` or `set_event`**: a workflow blocked in
such a wait has no checkpoint at the patch position yet, takes the patch, and its next step lands where the wait's own
records are (`DBOSUnexpectedStepError`, reproduced on DBOS 3.3.0 and 3.4.0). `tests/test_durable_versioning.py` is the
template for proving an upgrade. When no workflow can still be on the old path, `deprecate_patch`, then remove it.

Patches in use: `bt-run-subplans`, `bt-run-audit-remediation`, `bt-run-survives-step-failures` (run workflow);
`bt-task-respects-pause`, `bt-task-owner-reverify`, `bt-task-reconcile-asks-owner` (task workflow).

Steps the run workflow calls itself (`bt.sync_lines`, `bt.compose`, `bt.audit_gate`) must not end the run when their
retries are spent: DBOS never recovers a workflow in ERROR. Behind `bt-run-survives-step-failures` such a failure is
reported (`subplan_lines_unavailable`, `gate_compose_failed`, `audit_gate_failed`) and the run goes on: lines are synced
again next turn, a composition is tried again for `COMPOSE_TURNS` turns before the gate counts as rejected, and an audit
the gate could not judge is held as blocked (`retry-task` runs it again). Work that runs in child workflows needs no
such guard: `_enqueue` turns a child's failure into an `internal_error` fact.

## Troubleshooting

| Symptom | Look at |
|---|---|
| a task is `needs_decision` | `status` → `decision.reason`, `failure.code`, `limit_hit`; answer with its request id |
| a check is `BLOCKED_ENV CHECK_UNSUPPORTED` | M6 refuses inline code (`python3 -c …`): put the check in a script of the repository |
| `SANDBOX_UNAVAILABLE` | `bwrap` missing or an invalid sandbox environment (duplicate variables are now resolved policy-first) |
| an agent seems stuck | `python -m bt_supervisor show <attempt key>`; `systemctl --user status bt-att-*` |
| the engine does not start | `journalctl --user -u bt-durable`; the state directory must be private (0700) |
| metrics | `python -m bt_durable.bench durable <state>/durable/telemetry.jsonl` |
| an attempt left a source file over 500 lines | telemetry event `file_guard` (written at capture, whatever tool wrote the file); the same findings are `snapshot.oversized` (`new`/`crossed`/`grew`), and `adapters/size_guard.note()` turns them into text for the next note |

## Verified limitations (not claimed)

- Exactly-once for external effects is NOT claimed. What is proven: one agent process per attempt key across engine
  crashes (adoption), one integration per snapshot (CAS + ancestry check; the run line and the snapshot's subplan
  lines move in one `git update-ref --stdin` transaction), one M6 verdict per verify key.
- The subplan lines of a migrated run hold a superset of their scope: seeding merges each legacy snapshot with its
  history, which carries whatever the legacy line held when that snapshot was made.
- The M2 router decides per task from the allowed list; it does not reserve accounts or apply per-account concurrency
  limits (none is configured anywhere today), does not persist decisions to an M2 ledger (telemetry is the record) and
  does not use Laya.
- Milestone audits (REQ-030 item 4): an accepted `kind: audit` task is judged by its findings ledger with the legacy
  gate (`bt_audit_gate`: open critical/high findings block; a missing ledger or a change outside the audit's declared
  files is a problem of the audit). Related blocking findings are grouped as `bt_remediation` groups them and each group
  is ONE coordinated repair: a new round of the first task it names, whose brief lists every finding with the probes
  (the named tasks' check commands); then the audit runs again. At most `gates.remediation_rounds` rounds per audit
  (`retry-task` on a blocked audit grants one more); dependents wait meanwhile. Not ported: the legacy plan revision
  that adds remediation tasks to the frozen plan (the durable repair is a round of an existing task, so its checks are
  that task's own; the other named tasks' probes are in the brief and the re-audit judges them), and the audit evidence
  cross-check of `quality_audit_evidence`. Behind `DBOS.patch("bt-run-audit-remediation")`.
- The panels show durable runs from a projection refreshed every few seconds: they can lag DBOS by one refresh, which
  is why every command is checked against a fresh build first. Route pins, cancel-attempt, revise and edit-brief are
  not offered for durable runs (refused with a reason); cancelling a durable run stays `bt-durable cancel`.
- The process-group fallback enforces only the runtime limit (see `bt_supervisor/README.md`).
- Real provider CLIs were not run under the durable runtime during REQ-030 (the lab uses a fake `claude` through the real
  driver); the first real run should be a small plan.
