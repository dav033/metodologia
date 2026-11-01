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

The engine's environment is what every attempt inherits and where the checks' toolchain (`node`, `uv`) is found, so
give it a stable PATH in a drop-in (`~/.config/systemd/user/bt-durable.service.d/env.conf`): `Environment=BITACORA_ROOT=%h/bitacora`
and a `PATH=` that names fnm's alias (`%h/.local/share/fnm/aliases/default/bin`), never a version directory or a
`/run/user/…/fnm_multishells/…` entry (`bt_autostart.stable_path`, D-256).

Hooks, the bitácora CLI and the legacy runtime keep running under the system interpreter (stdlib only,
`test_stdlib_boundary`). Only the engine, the CLI below and the new tests need the uv environment.

## Use

```sh
uv run bt-durable start pictures REQ-031          # a NEW run: pre-flight, owner record, enqueue (idempotent)
uv run bt-durable status pictures REQ-031         # summary, task states, open decisions with their request ids
uv run bt-durable answer pictures REQ-031 T2 T2:d1 retry_with_note --note "…"   # stale request ids are refused
uv run bt-durable pause|resume|cancel pictures REQ-031
uv run bt-durable retry-task pictures REQ-031 T2 --note "…"
uv run bt-durable answer pictures REQ-031 T2 T2:d1 reverify      # verify the same snapshot again, no agent run
uv run bt-durable attest pictures REQ-031 T2 --request T2:d1 --evidence "what was done and seen"   # receipt + reverify
```

- **Pause** stops every new agent attempt: the run starts no task, and a running task workflow waits before routing a
  retry (its state shows `paused`); verifications and agents already running finish.
- **Briefs** carry what the legacy owner puts in them (`adapters/briefs.py`, built by the legacy `owner_notes` and
  `contract_notes`): the owner's indications (`RUN.notes/<task>.md`), the audit's findings, the attempt history (legacy
  M1 document of a migrated run plus `RUN.notes/<task>.history.jsonl`, which the durable verifier appends to), the
  failure analysis, the last verification failure (left out when the workflow hands the agent that same failure as its
  note), the audit ledger help and the UI contract with its approval state; a retry from a snapshot is told so (also
  when that attempt committed its work itself).
- **Retries build on the latest attempt** (D-254): every new attempt of a task starts from the newest snapshot an
  earlier attempt of it left (or its reconciled legacy snapshot), whatever decided the retry: an automatic retry, an
  owner or healing answer (`retry`, `retry_with_note`, `retry_other_route`), a quota wait or a memory raise. An attempt
  that left no snapshot keeps the earlier one. Only `RECONCILE_INTEGRATION` starts again from the line tip. Behind
  `bt-task-continues-latest-tree`: a pass recorded before it keeps the base it had.
- **Readiness, retry bases and the UI contract** (D-262, pictures REQ-021 r32 T2.57/T3.91): a task is ready only when
  every ancestor is done, not just its direct dependencies (an inherited dependency whose own ancestor runs again in
  this stage does not count); before another attempt a round the frontier started asks the run whether its ancestors
  are still done, and when not it hands the task back (`task_requeued`; it keeps no resource claim while it waits). A
  continuing retry starts from its earlier attempt's snapshot with the newer work of its line merged in
  (`bt.continue_base`; a conflicting line is left out). A `ui: true` task checks its contract on that base before an
  agent runs (`bt.contract_gate`): not approved → no agent, a decision naming `DESIGN_CONTRACT_MISSING`/`_UNAPPROVED`/
  `_HASH_MISMATCH`. An attempt that changed nothing and failed its checks is `AGENT_NO_CHANGE` (the agent's own reason,
  to the owner), not a retried `CHECK_FAILED`; a Node heap-limit abort in a check the task wrote is an implementation
  failure with a NODE_OPTIONS note (`CHECK_HEAP_LIMIT`), and in another check, once the relaxed heap did not help, a
  check problem for the owner (`CHECK_HEAP_LIMIT_PLAN`); a sandbox memory kill keeps the relaxed re-verification.
- **One source per test variable** (D-265, pictures REQ-021 r32 T3.91): an attempt gets the verifier's value for every
  variable the checks' environment sets explicitly (`verifier.env_file`, the plan's `requires`) and for every variable
  it would hold anyway that the checks inherit (`verifier.inherit_env`); the owner's agent env file
  (`execution.agent_env_file`) only adds keys the checks lack (`bt_verifier_env.one_source`). A key both define with
  different values gets the verifier's value, a brief note, telemetry `agent_env_divergent` and an activity line (names,
  host:port and database only). Before an agent starts, `bt.env_probe` opens (TCP, 2 s, reachable results cached 30 s
  per run) each network URL among the variables the task's checks `require` (or, with none declared, those from the
  agent env file and the verifier's explicit settings): one that does not answer → no agent, no attempt used, a decision
  `AGENT_ENV_UNREACHABLE` naming key, host:port and source; `retry` probes again. Healing leaves that decision, and any
  decided attempt whose agent said it could not run its checks (`checks_not_run`), to the owner.
- **Manual checks** (`type: manual`): M6 accepts a coordinator receipt (`bt_attestation`, the same one the legacy owner
  uses) for its own check only. Without one, the task does not fail: it opens a decision `MANUAL_EVIDENCE_REQUIRED`
  with its request id, the attempt the receipt must be bound to (`verify_attempt`) and the `bt-durable attest` command;
  `reverify` then verifies the same snapshot again (a migrated task's legacy snapshot included). A reconciled legacy
  task whose only doubt is manual evidence or a permission asks the owner first instead of launching an agent.

## Panels and remote control (M7)

`bt_durable.projection` derives one JSON read model per run from DBOS only (workflow statuses, inputs/outputs, the
`summary`/`state`/`decision` events): `<root>/.state/durable/projections/<project>/<REQ>-r<N>.json` (0600 file, 0700
directories; `bt_durable_panel.path`). The engine refreshes it every 5 s (`serve(project_seconds=…)`) and
`bt-durable project PROJECT REQ` rebuilds it; no workflow reads it back. `sequence` is monotonic (+1 per change, a
rebuild without the file starts at the current time in ms); `status_seq` / `tasks[].seq` / `decisions[].seq` are the
sequence of each subject's last change. Task states: `pending queued waiting_quota running verifying recovering
needs_decision blocked failed completed cancelled`; run: `running paused completed blocked failed cancelled`.

The Flow page (`/flow`, and each subplan's «Ejecución» in the Plan tab, D-150) reads the run's telemetry through
`bt_flow_durable` (stdlib only): every record of the run becomes a message between the same parties as the legacy stores
(M1 the workflows, M2 the router, M3 the attempt, M5 recovery, M6 verification and audits, the owner).

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

## Subplans and composition gates (plan 1.3.0)

The legacy definitions are reused as they are: `Plan.subplans`/`composition_gates` (parsed by the core), the scope of
a subplan line (`bt_integration_line.scoped_task_ids`: members plus their frozen-plan ancestors) and the composition
engine (`bt_composition`, through `bt_composition_adapter`).

- Each subplan has its line `refs/bt/subplan/<project>/<req>/r<rev>/<role>/<SP>`, started at the run line's base pin
  (`refs/bt/line/…/<role>-base`, created with the run line in one ref transaction). A member task starts from its
  subplan's line; an accepted snapshot is merged (CAS, all merges computed before any ref moves, one `update-ref --stdin`
  transaction) into the run line and into every existing subplan line whose scope holds it. A member that conflicts
  only on the run line (another subplan changed the same lines) is still accepted, as in the legacy
  `SubplanLineRouter`: the conflict is reported (`run_line_conflict`) and left to the composition gates. The same holds
  for another subplan's line in the member's scope (a member that a later stage made an ancestor of that subplan's
  accepted work): once its own line takes it, that line is left as it was and reported (`subplan_line_conflict`), since a
  rebuild from its own line could never hold that line's work. The run
  workflow seeds and catches the lines up from the accepted snapshots (migrated runs and joined stages included).
- Line merges settle conflicts as the composer does (D-164): `package.json` merged by key and the recorded resolutions
  in `<state>/composition/resolutions`; a criss-cross history is merged against a virtual base built with the same
  rules (D-169, D-174). An open resolution request (no `.resolved` file) starts the Solucionador after
  `solver.resolution_after_seconds` (D-175).
- A gate task starts only when every member subplan is complete (members, UI design and visual review tasks, audit):
  the run workflow publishes each member's line tip as a subplan version (`refs/subplans/<req>.bt-r<rev>/<SP>/v<N>`)
  and builds the candidate (`refs/compositions/<req>.bt-r<rev>/candidates/C<N>`). The gate task runs on that candidate
  caught up with the newer work of the subplan lines it will be integrated into (a line that conflicts with it is left
  out, D-173), and nothing after the gate starts before the gate task is accepted. A text conflict between members, or
  a composition that fails `COMPOSE_TURNS` turns, is a rejected candidate: the gate task is held and the run summary
  says why (`gates.rejected`); the owner's `retry-task` of the gate task composes the gate again.
- Subplan lines keep up with the subplans they build on (D-297, `reconcile.py`): every maintenance pass folds each line,
  in plan order, with its predecessors' lines by the composer's rules. A fold that changes the tree moves the line by CAS
  (the same commit «Probar» offered, so the version and the owner's decision stand; an earlier subplan never moves for a
  later one). A conflict moves nothing and opens the recorded-resolution requests, bound to the run, which the Solucionador
  answers; a line whose predecessor is pending waits for it. A moved line sends `recheck_gates`. While a gate's member is
  not reconciled the composer returns `RECONCILE_PENDING` instead of asking an agent to settle the same clash twice, and
  the run does not end. A merge whose conflict is left out by design (`_caught_up`, `continuation_base`, `sync`, another
  subplan's line, the run line) opens no request.
- A gate that already passed is composed again when one of its members' lines takes newer accepted work (a repair a
  later stage added to that subplan, D-213) and no later gate that judged, is judging or can compose now holds all its
  members (D-245, `bt-run-fresh-gates`; D-297, `bt-run-live-gates`: a later gate waiting for members not built verifies
  nothing yet), and a passed gate rejected on recomposition no longer counts as passed: what follows it waits and the
  summary shows its task `blocked`. Cumulative gates need this only for the newest one that passed; a gate not composed
  yet composes from the current lines anyway. Once per accepted set, and whenever `recheck_gates` arrives, the run asks `bt.gate_freshness` which members' line trees differ from the version commits the gate
  task's snapshot was built on (the candidate's `compose <plan> <SP>@v<N>` commits); a stale gate reports `gate_stale`,
  is composed again and its gate task runs a new round on the new candidate, so its checks judge the new combination
  (nothing after the gate starts meanwhile). A rejected recomposition holds the gate as above. The re-run is at least
  once, never exactly once: an engine restart mid-round replays the recorded steps.
- Not ported: the legacy owner publishes a composition only with an M6 proof bound to the candidate's exact tree; here
  the gate passes when the gate task is accepted on a snapshot built on the candidate. The durable composition store
  and refs are namespaced and never touch the legacy owner's.

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
  runs. Composition gates compose again from the copied subplan lines, under the new revision's namespace. An accepted
  attempt that changed nothing (snapshot == base: its work was already in its base) is inherited as it is; only an
  accepted snapshot whose commit no longer exists is refused (`JOIN_MATERIAL_MISSING`, D-272).
- A stage that changes accepted tasks is refused (`JOIN_NEEDS_CONFIRM`) unless `--confirm` (everything) or
  `--confirm-tasks T1,T2` (exactly those; the panel's «Confirmar y unir», owner only, loopback). The tasks of a subplan
  the OWNER reconfirmed after the running stage are confirmed by that reconfirmation when the stage holding it is in the
  join and holds the task as joined (D-275, «Reconfirmar = confirmar»; `bt_stage_confirmations`). The result, the
  `stage_joined` telemetry and the requirement's activity say who confirmed each redone task.
- The engine joins on its own a frozen stage a durable run is behind (`stage_join.behind`, in the drain pass): once per
  revision, after the CLI's frozen-plan checks; a refusal is recorded and that revision waits for the owner or a newer stage.
- With live attempts the current run is paused and `RUN.join.json` records the request; the engine's reaper pass
  completes it once they end (a refusal is written into the file). Any refused join leaves `RUN.join.refused.json`
  (revision, code, message) until a later join is not refused; the panel shows it while the confirmed subplan is
  «por unir a la ejecución» (D-272).
- Then the current run's workflows are cancelled (its open owner decisions end with it), `RUN.owner.json` moves by
  compare-and-swap and the new run starts with the current run's settings; `RUN.durable-run.json` moves last.
  `RUN.join.json` is written before the cancel and removed after the pointer moved, so a join cut anywhere in between
  is finished by the engine's next pass. `RUN.join.lock` serialises the joins of a requirement (the CLI waits, the
  engine's pass skips a requirement being joined).
- The owner's pause carries over (`LegacyProgress.paused`): a stage joined to a paused run starts nothing until resumed.
- No running workflow changes its step sequence: only a new run's input can carry `integrated` or `paused`, so no patch
  is needed.

## Healing and the Solucionador (D-167, REQ-031)

The maintenance pass answers an open decision with the diagnosing model's `retry`/`retry_with_note` once per failure
signature (`healing.py`). What it leaves for a person, a signature that comes back, a task that does not move, a run
that waits for nothing (`stalled`: nothing live, nothing to answer, not paused), a run that ended blocked by a rejected
gate or a task the owner did not stop (`ended`), a task the run holds blocked while it goes on (`blocked`, an audit
no round cleared, after `solver.blocked_after_seconds`, once per block, D-235) and a run workflow in ERROR start the Solucionador (`solver.py`): one full-access Claude Opus session per run in tmux
(`tmux -L bitacora attach -t bit-<project>-<REQ>-solver`), with its brief in `<rdir>/RUN.solver/<id>/`, which integrates
metodologia fixes only through `skill/scripts/bt_integrate.py`. Switch: `bitacora.py config set solver.enabled false`.
The `solver.max_minutes` watchdog and the account move never cut a session's own integration (`bt_integrate.py --session
<id>`, a child of its agent in tmux): they wait for it, at most `solver.integrate_grace_minutes` (120) more. A session
whose run a stage join superseded is told once (its old decision is gone; finish and integrate the fix) and kept. A
session whose triggers were all resolved elsewhere (an operator answered them, the task settled) is told once to write
`result.json` with outcome `superseded` and closed so after `solver.resolved_grace_minutes` (5) unless it is integrating;
that outcome does not count against `solver.max_per_task` (D-271).
Details: `references/modules.md` §Solver.

## Recovery and rollback

- Engine stop: SIGTERM ends the loop, DBOS is destroyed and the process exits at once (`service.exit_now`) instead of
  waiting for workflow threads blocked in `DBOS.recv` or a long step; steps that had not recorded their result run
  again after recovery, as after a kill. A verification an engine stop cut short is queued again once at the next
  start (D-171); a second interruption of the same request is a review for the owner.
- Engine crash/kill: systemd restarts it; DBOS recovers this executor's PENDING workflows. An agent that kept running
  in its unit is adopted (the launch step is idempotent per attempt key), never started twice. An observation the user
  manager does not answer (`unknown`) is looked at again for up to 30 s before the agent workflow acts on it, so a
  `systemctl` hiccup never terminates a healthy agent (`execution/steps.py`; the reaper still acts at once). `bt.run` and `bt.task`
  have no `max_recovery_attempts` (DBOS counts every recovery and would dead-letter a run after 100 deploys); the
  agent, verify and integrate children keep DBOS's default.
- Database outage: DBOS retries its connections; the run continues when the database is back (tested with PostgreSQL).
- Cancel: workflows are cancelled with their children; the engine's reaper terminates any unit whose workflow is
  terminal and the supervisor proves no marked process remains (otherwise the attempt stays busy).
- Rollback of the whole runtime: `migrate --rollback` per run, `execution.backend=legacy`, stop `bt-durable.service`.
  Legacy state was never modified, so the legacy owner resumes from where it stopped.

## An attempt worktree starts as the verifier's copy (D-273)

`bt.prepare` (step implementation, no workflow change) prepares the allocated worktree before the agent starts, as
M6 prepares its clean copy before every check (`adapters/worktree_prepare.py`): with a `package-lock.json`, the
verifier's toolchain and at least one `sandbox_prepare.detect_steps` step, it installs the lockfile with M6's own
arguments (`sandbox_provision.NPM_CI_ARGS`, skipped when `node_modules` is complete) and runs those steps (workspace
builds, `next typegen`) with the checks' environment, at most 900 s in all, stopping at the first failure. Nothing
blocks the start: the brief names what ran, what failed (exit, last lines, `<attempt>/worktree-prepare.log`) and any
generated file the repository does not git-ignore (it would be captured). `<attempt>/worktree-prepare.json` keeps the
result, so a retried step writes the same brief and runs nothing again. pictures (169 MB, 576 packages): 11.7 s.

## Disk space: attempt worktrees, the free-space floor, the scratch subvolume (D-266)

Each attempt works in its own git worktree under `<scratch>/ws/<project>/worktrees/` (`<scratch>` =
`execution.scratch_root`, default `<state>/durable/attempts-root`); what it leaves that matters lives elsewhere: its
snapshot commit (`refs/m3/handoff/…`), its branch and `<scratch>/attempts/<key>/` (prompt, log, handoff manifest).
Until D-266 nothing removed a worktree: on 2026-10-31 ~480 of them (each with `node_modules` and a Next build) filled
`/` and `/home` and T3.91 a9 died with «No space left on device».

- **Collection** (`scratch.py`). Every 10 minutes (`service.GC_SECONDS`, the first pass 10 minutes after a start;
  `execution.worktree_gc`, on by default) a background pass removes, at most 100 per pass, the worktrees of attempts
  whose capture is complete (the manifest's snapshot ref still names its snapshot) and that nothing needs: the task
  round ended (task workflow terminal) or a later attempt of the same round exists. A retry continues from the snapshot
  ref, never from an earlier checkout; the only reader of a checkout after its capture is M6 (it mounts the attempt's own
  `node_modules`), always for the latest attempt of an open round, which is kept. Also kept, with the reason: agent
  workflow not terminal (`running`), unit still held (`unit-held`), a process working inside it (`in-use`), capture
  missing or ref moved (`no-snapshot`), unknown to DBOS (`no-workflow`). `git worktree remove --force` + `prune` under
  the repository's workspace lock; branch, refs and the attempt folder stay. Folders no attempt names are listed as
  orphans and never removed. Telemetry: `worktree_removed`, `worktree_remove_failed`, `worktrees_collected`.
- **By hand**: `uv run bt-durable gc-worktrees` is a dry run (counts, allocated GB, why each one is kept);
  `--apply` removes; `--json` lists every attempt; `--no-size` skips measuring. Exit 1 when a removal failed.
- **Floor** (`execution.min_free_gb`, default 10; 0 = off). Before an agent starts (step `bt.disk_guard`, behind
  `DBOS.patch("bt-task-disk-guard")`, right after `bt.env_probe`) and before M6 runs a check, the free space of the
  scratch and state filesystems is read. Below the floor no agent starts and no attempt is used: the task opens the
  environment decision `DISK_LOW` (free bytes, path, the engine's biggest scratch consumers by count); a verification
  returns `NEEDS_REVIEW DISK_LOW` (environment decision with `reverify`). Free space, then answer `retry`/`reverify`;
  healing leaves `DISK_LOW` to the owner.

**The rest of the scratch (D-270).** Every `disk_gc.interval_min` (60; the first pass that long after a start) a second
background pass (`gc_scratch.py`, `disk_gc.enabled`) reclaims three places D-266 left growing; `uv run bt-durable
gc-scratch` is the same pass as a dry run (per area: counts, allocated GB, why each item is kept; `--area`, `--json`,
`--no-size`), `--apply` removes and records it in the telemetry (`disk_gc_removed`, `disk_gc_failed`, `disk_gc_area`).

- `legacy_executor` — `<state>/executor/<run>/ws/worktrees` (`bt_scheduler_executor.retention`, `preserve=True`). A
  checkout is retired once everything it holds beyond its snapshot is preserved: unknown ignored data (reports, local
  data files) up to `disk_gc.legacy_archive_mb` goes into `attempts/<dirname>/retained-ignored.tar.gz`; staged content,
  edits or commits after the capture, or a checkout never captured become one commit under
  `refs/m3/retained/<run>/<dirname>` (tree = the checkout, parents HEAD and the staged tree). An attempt the ledger still
  calls live is retired only in a run a later revision superseded, with its supervisor gone and untouched for three
  days. Kept and reported: ignored data over the cap, locked/unregistered worktrees, submodules, a moved snapshot ref, a
  process inside, the executor's lock held. Absent checkouts are settled in `retention-index.json` and never inspected
  again. At most `disk_gc.legacy_limit` removals per pass. `bt-workspace-retention.timer` keeps its old fail-closed rules
  (`retention_cli` without `--preserve`); the engine pass supersedes it.
- `verify_copies` — «Probar» copies (`gc_verify.py`). Removed: a subplan version a newer published version superseded,
  a version the owner decided more than `disk_gc.verify_grace_days` ago, a task copy whose manual decision closed (after
  the grace). Kept: a running server (its `BITACORA_VERIFY_ID` mark, a process inside, its tmux session), a held
  `.lock`, sidecars touched within the hour, edits or new files git would keep, the latest undecided version, unknown
  names. Sidecars go with their copy.
- `deps_cache` — M6's `npm ci` per lockfile (`gc_deps.py`; each use touches `.m6-ready`). Kept: keys of the lockfiles in
  live runs' current tips (`refs/bt/line|subplan/…/r<rev>/…` of non-terminal projections) and entries used in the last
  `disk_gc.deps_min_idle_hours`; removed least recently used first when unused for `disk_gc.deps_cache_max_age_days` or
  while the cache exceeds `disk_gc.deps_cache_max_gb`.

The two folders outside the bitácora are only touched for the live bitácora or when `BITACORA_VERIFY_DIR` /
`M6_DEPS_CACHE` names them. Test labs default to a tmpfs (`durable_support.lab_dir`: `BT_LAB_DIR`, else
`bt_regress.fast_tmp()`), not `$TMPDIR` on /home.

**Snapshots.** Snapper takes hourly/daily snapshots of `@home`, so everything the engine writes and deletes under
`/home` stays pinned until those snapshots expire: deleting 190 worktrees freed 481 MB. A btrfs subvolume nested inside
`@home` is not part of `@home`'s snapshots. Make the scratch one, IN PLACE (same path: no recorded path changes, no
replay impact). Operator procedure (not run by the engine):

```sh
cd ~/dev/metodologia
uv run bt-durable gc-worktrees && uv run bt-durable gc-worktrees --apply   # smaller copy first
uv run bt-durable pause <PROJECT> <REQ>             # every durable run with live attempts; agents keep running
systemctl --user list-units --state=active 'bt-att-*'   # wait until it lists none (agents live in their own units)
systemctl --user stop bt-durable.service
S=~/bitacora/.state/durable/attempts-root           # or execution.scratch_root if set
stat -f -c %T "$S"                                  # btrfs
btrfs subvolume show "$S" >/dev/null 2>&1 && echo "already a subvolume: stop here"
btrfs subvolume create "$S.new"
chmod --reference="$S" "$S.new"
cp -a --reflink=always "$S/." "$S.new/"
mv "$S" "$S.old" && mv "$S.new" "$S"
btrfs subvolume show "$S" | head -3                 # it is a subvolume now
git -C <repository> worktree list | grep -c attempts-root    # the remaining worktrees still resolve
systemctl --user start bt-durable.service
uv run bt-durable resume <PROJECT> <REQ>
rm -rf "$S.old"                                     # after a check; its blocks return when the old snapshots expire
```

The same in-place swap fits the other high-churn folders (stop their writers first): the legacy executor's
`<state>/executor` (its worktrees: `python -m bt_scheduler_executor.retention_cli --root <state>/executor`, hourly as `bt-workspace-retention.timer`), Probar's copies in
`~/.local/share/bitacora-verify`, M6's dependency cache `~/.cache/m6-deps`, the integration deploy/regression roots in
`~/.local/share/bitacora-integrate`.

**Another path** (`execution.scratch_root`, e.g. a separate subvolume mounted elsewhere) works for new attempts, but
recorded values name the old one: `bt.prepare`'s output and the verify children's inputs hold absolute paths
(`Prepared.worktree`, `attempt_dir`, `prompt_path`, `env_file`, `stdin_path`; `Snapshot.manifest_path`), and git's
worktree metadata holds each worktree's path. Move it only with every run paused and no attempt unit alive, and leave a
symlink at the old path (`ln -s <new> "$S"`) so those paths still resolve. New attempts' branches then carry a new
scope suffix (it hashes the resolved root), so the brief's continuation note cannot name an attempt from before the
move that committed its own work (the base itself is unaffected: it is a commit).

## Upgrading workflows

The engine sets `enable_patching=True` (DBOS pins the application version, so code changes do not orphan PENDING
workflows). A change to a workflow's sequence of steps goes behind `if DBOS.patch("<name>"):`. **Place a patch right
before a plain step, never right before `DBOS.recv`, `DBOS.sleep`, `get_result` or `set_event`**: a workflow blocked in
such a wait has no checkpoint at the patch position yet, takes the patch, and its next step lands where the wait's own
records are (`DBOSUnexpectedStepError`, reproduced on DBOS 3.3.0 and 3.4.0). `tests/test_durable_versioning.py` is the
template for proving an upgrade, and `tests/test_durable_upgrade.py` proves a real one: a run started by the previous
engine code (exported with `git archive`) is recovered by the current code from the same database. When no workflow can
still be on the old path, `deprecate_patch`, then remove it.

Patches in use: `bt-run-subplans`, `bt-run-audit-remediation`, `bt-run-survives-step-failures`, `bt-run-reopened`,
`bt-run-recompose-gate`, `bt-run-fresh-gates`, `bt-run-live-gates` (run workflow); `bt-task-respects-pause`, `bt-task-owner-reverify`,
`bt-task-reconcile-asks-owner`, `bt-task-continues-latest-tree` (task workflow); D-262: `bt-run-transitive-readiness`,
`bt-run-requeues-unready-task` (run workflow), `bt-task-rechecks-ancestors`, `bt-task-retry-catches-up`,
`bt-task-contract-gate`, `bt-task-no-change-is-not-check-failed`, `bt-task-heap-limit-is-not-sandbox-oom` (task
workflow); D-265: `bt-task-probes-agent-env` (task workflow); D-266: `bt-task-disk-guard` (task workflow); `bt-task-interrupted-reverify` and D-269
`bt-task-answer-opens-attempt-window` (task workflow, in `execution/recovery_policy.py`, right before `bt.emit_decision`). A workflow body reads the plan only through `steps.workflow_plan()`:
the `bt.plan_text` step must run (or replay) every time, or a run recovered after another workflow warmed the process
cache skips its first step. The control plane (`control/`: frontier, policy, classifier, subplan scopes) decides what a
workflow does next from recorded step results, so a change to its decisions is a sequence change too.

A run line created before the base pin existed (pictures REQ-021 r15, 2026-10-28) has no `<line>-base`: until it is
pinned the run reports `subplan_lines_unavailable` and goes on without subplan lines. Pin where the line began:
`git -C <repo> update-ref refs/bt/line/<project>/<req>/r<rev>/<role>-base <commit>`. Lines created since get their pin
in the same transaction, and a stage join copies the pins with the lines.

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
| an integration conflict has a recorded resolution | `reverify` observes integration again for that verification profile (`bt-task-reverify-reintegrates`, D-221); replay keeps the same child ID, and older histories retain their recorded ID |
| a check is `BLOCKED_ENV CHECK_UNSUPPORTED` | M6 refuses inline code (`python3 -c …`): put the check in a script of the repository |
| `SANDBOX_UNAVAILABLE` | `bwrap` missing or an invalid sandbox environment (duplicate variables are now resolved policy-first) |
| `DISK_LOW` / «No space left on device» | `uv run bt-durable gc-worktrees` and `gc-scratch` (dry runs), then `--apply`; old snapper snapshots of `/home` pin deleted blocks; see «Disk space» |
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
  (`retry-task` on a blocked audit grants one more); dependents wait meanwhile. A blocking finding that names only the
  audit itself is a gap in the audit's own coverage, not a product defect: it reruns the audit, told what to complete,
  within the same rounds (D-234). Not ported: the legacy plan revision
  that adds remediation tasks to the frozen plan (the durable repair is a round of an existing task, so its checks are
  that task's own; the other named tasks' probes are in the brief and the re-audit judges them), and the audit evidence
  cross-check of `quality_audit_evidence`. Behind `DBOS.patch("bt-run-audit-remediation")`.
- The panels show durable runs from a projection refreshed every few seconds: they can lag DBOS by one refresh, which
  is why every command is checked against a fresh build first. Route pins, cancel-attempt, revise and edit-brief are
  not offered for durable runs (refused with a reason); cancelling a durable run stays `bt-durable cancel`.
- The process-group fallback enforces only the runtime limit (see `bt_supervisor/README.md`).
- Real provider CLIs were not run under the durable runtime during REQ-030 (the lab uses a fake `claude` through the real
  driver); the first real run should be a small plan.
