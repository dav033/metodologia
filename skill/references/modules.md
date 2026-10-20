# Modules: how the methodology is divided

The methodology is one product split into modules. A module is a package `skill/scripts/bt_<name>/` that can be
understood, run and verified **without the rest**. Modules include `bt_planner` (plans), `bt_scheduler_core` (runs an
approved plan), `bt_scheduler_decision` (M2 route decisions), `bt_scheduler_executor` (M3 agent execution),
`bt_scheduler_monitor` (M4 stream observations), `bt_scheduler_recovery` (M5 retry recommendations), and
`bt_scheduler_quality` (M6 verification). Use this page when you extract, add or review a module.

## Rules (each one is enforced by a test, not by good intentions)

1. **Imports: standard library + itself.** No other `bt_*` module, no third-party package, no relative import that
   climbs out of the package. → `bt_<name>/tests/test_boundaries.py` (AST).
2. **No knowledge of the rest.** It never names another module, a bitácora path, `RUN.json`, a home directory or the
   environment, and does no network/subprocess work. It works on inputs you pass in (a directory, a file, arguments).
   Methodology vocabulary it needs (e.g. which `status:` words mean approved) is a parameter with a documented default.
3. **Self-contained.** Parser, lock, schema/data (`data/`), CLI (`python -m bt_<name>`), README and tests travel inside
   the package. Writes are confined to a short documented list and checked by a test.
4. **One public surface.** `__init__.py` exports the API (`__all__`); everything else is private. The README lists the
   API, the commands and the stable error codes, and a test keeps the README and the code in step.
5. **Verifiable end to end, alone.** Own suite in `bt_<name>/tests/` including (a) `test_boundaries.py`, (b) an end-to-end
   CLI session in `python -I` from an unrelated cwd, (c) `test_isolation.py`: the package copied ALONE to a temp directory
   passes its own suite there.

## Integration (one direction only)

- Exactly one adapter, `skill/scripts/bt_<name>_adapter.py`, imports the module; argument plumbing sits in
  `bt_cli_<name>.py`. The rest of the methodology calls the adapter. Dependency: methodology → adapter → module, never back.
- `tests/test_<name>_integration.py` in the methodology suite asserts: only the adapter imports the module; the module
  imports nothing of the methodology; the module suite passes as an isolated subprocess; each hook works; existing state
  files are untouched.
- If the module deliberately duplicates a small piece of knowledge to stay independent (the planner's PLAN.md parser), a
  parity test compares both on every real plan in the repository so they cannot drift silently.
- Packaging: list the package in `pyproject.toml` `packages` and its `data/*.json`/README in `package-data`; the adapter
  and CLI plumbing go in `py-modules`; the module's tests are not shipped.

## Checklist to split another part

Identify its inputs/outputs → write the README (purpose, boundaries, API, errors) first → move code, replacing every
import of another `bt_*` by a parameter or a data argument → add the five tests above → add the adapter and rewire the
callers → delete the old modules → run both suites → record the decision in `DECISIONS.md`.

## Scheduler core (`bt_scheduler_core`, REQ-011)

The second module, built under the same five rules. It is the deterministic heart of the Scheduler (system parent of
M1 core, M2 decision, M3 executor, M4 monitor, M5 recovery): it loads a hash-approved `PLAN.json`, resolves the DAG, runs the
task/attempt state machine on a transactional store (SQLite WAL), reserves capacity/resources atomically, dispatches through
ports, ingests events idempotently and reconciles after a restart. **No AI inside**: sibling modules implement the ports
(`PlanRoutingPort`, `AssignmentPort`, `ExecutionPort`, `RecoveryPort`, `VerificationPort`, `StateRepository`; contract in its README) and may
be simulated with `bt_scheduler_core.simulators`.

- Adapter: `skill/scripts/bt_scheduler_adapter.py` (only file that imports it). It hands the core the latest frozen plan
  revision (through `bt_plan_adapter`, hash from the planner's manifest — approval is the caller-supplied sha256, no hash,
  no run), opens the run database at `<bitácora root>/.state/scheduler/<project>-<REQ>.db` (local, untracked; outside that
  layout `<requirement>/SCHEDULER.db`), and can write a `RUN.json`-shaped read model marked `authority: "scheduler"` as
  `<requirement>/RUN.projection.json`.
- **One authority per requirement**: the core's run database decides. The projection is never called `RUN.json`, so no
  legacy file can be overwritten by it. The adapter refuses to open a core over a legacy `RUN.json` (a run from before the
  marathon supervisor was removed); such files are historical, read-only and not migrated.
- The core is the only way an approved plan runs: `launch`/`handoff` call `scheduler-run`. It can also be driven directly
  through the adapter or `python -m bt_scheduler_core`.
- Tests: module suite `bt_scheduler_core/tests/` (boundaries, lone-copy isolation, CLI end to end, fuzzed invariants,
  crash-at-every-commit restarts) and `tests/test_scheduler_integration.py` (boundary from outside, frozen-plan hand-over,
  authority rules, historical `RUN.json` byte-identical).

### Scheduler owner runtime (REQ-022)

- Start a run with `bitacora.py --project <project> launch <REQ>` (or `handoff`, or the web approval). There is no other
  mode and no `--force`: the launcher requires the normal project readiness gate and an already approved, frozen
  `PLAN.json` revision (`PLAN_NOT_FROZEN` otherwise).
- `bt_scheduler_run.py` composes one durable M1 owner with the existing M2 decision and M3 executor adapters.
  `bitacora.py --project <project> scheduler-run <REQ> --resume` reopens the same M1 run identity and lets M3
  reconcile its captured process state;
  it does not approve a plan or silently create a replacement run.
- On a new Scheduler run, M1 sends the full frozen DAG to M2 through `PlanRoutingPort` before executor reconciliation
  or dispatch. M2 records a non-reserving route recommendation for every task; the owner projection joins that map
  with the plan's complexity. Each READY task is routed again against current eligibility when it is dispatched.
- M1's SQLite database is the run authority. The owner writes an atomic `RUN.projection.json` with the frozen plan
  identity and heartbeat. `watch`, dashboard and requirement views read that projection only for Scheduler-owned
  requirements, validate it, and report unavailable or stale state with the exact resume command. They never fall back
  to legacy `RUN.json`.
- CLI and web pause/resume/stop controls route to M1 (stop means cancel). Notifications are deduplicated by the latest
  state-changing M1 audit sequence; unreadable local claim state skips delivery rather than interrupting execution.
- Status for people: `bt_planstatus` (read-only data layer) feeds `plan-status`, the generated PLAN.md block
  (`bt_planblock.refresh_plan_block`, at launch and whenever the projection is rewritten), the SessionStart "Planes"
  section and the web "Planes" view (`documentation.md`). PLAN.json never carries state, model or account.
  `scheduler-run` installs the matching per-user login entry unless `--no-autostart` is passed; it launches
  `scheduler-watch` (`bt_scheduler_watch`), the per-run watchdog that restarts the owner, and `scheduler-op`
  (`bt_scheduler_ops`) is the operator's hand on a live run (`execution.md` §1c). This is not a global service.
- REQ-022 originally left M4/M5/M6 inactive. REQ-023 supersedes that activation boundary: both supported owner
  commands (`scheduler-run` and `launch --scheduler`) now compose all three with separate private per-run stores.
  The owner loop drains M3 output into M4 and delivers its audit-only incidents through M1; M5 and M6 use M1's
  existing recovery and verification ports. The legacy launcher stays separate, and low-level compositions retain
  their optional port seam. `NEEDS_REVIEW` remains operator-owned.

## Agent executor (`bt_scheduler_executor`, REQ-014)

The third Scheduler module (M3), built under the same five rules. It receives the core's authorised, idempotent start/cancel/query
orders plus the route M2 selected, launches Claude Code, Codex or Gemini (Antigravity `agy`) in an **isolated git worktree per
attempt**, supervises the process through a detached shim, and **preserves the work whatever way the agent ends** (clean, failed,
out of quota, connection lost, timeout, killed, cancelled, lost) as a recoverable handoff of committed + uncommitted + untracked
state. It emits technical events with a classified cause, survives its own restart (re-attach / finalise from `exit.json` /
stop an orphan by process identity) and never decides: not who runs (M2), not state or capacity (M1), not what a stream means
(M4), not whether to retry (M5), not whether work is accepted (the independent verifier). `execution_finished` means "the
agent stopped"; no private reasoning is claimed to transfer between providers.

The detached shim also samples `/proc` while the agent runs and stores bounded PID/start identities for observed descendants.
At settle, the worktree sweep can stop the agent's orphaned terminal processes without treating an operator's terminal as agent work.
Sampling is best effort and identity-checked; see the executor README for caps and limits.

- Ports (own `typing.Protocol`s, own frozen types; no sibling class crosses the boundary): `RouteResolver`, `BriefSource`,
  `AgentDriver`, `WorkspaceManager`, `EventSink`. README: ports, life cycle, artefacts, cause classes, events, limits.
- Adapter: `skill/scripts/bt_scheduler_executor_adapter.py` (only importer). It validates M2's reference against the one
  catalogue (`bt_agents`) and the profile policy (`bt_profiles`: authorisation, work-only gate by the project's repository,
  account environment boundary), launches through `bt_driver`/`bt_runprompt`, builds the brief from the frozen plan, resolves
  repositories through `bt_workspace`, translates to the core's `Ack`/`ExecutionStatus`/`Event` (reached through
  `bt_scheduler_adapter`, the only importer of the core) and exposes workspaces in `bt_worktree`'s allocation shape
  (`worktree_allocation`) so its scope/integration tooling can consume what M3 produced. `wire(rdir, ...)` is the opt-in entry
  point; nothing in an existing command changes. State lives in `<bitácora root>/.state/executor/<project>-<REQ>/`.
- Predecessor hand-over (P-031): `skill/scripts/bt_scheduler_integrator.py`, used by `wire(..., integrate_predecessors=True)`. It merges
  the accepted same-repository ancestors' handoff snapshots into one commit (`git merge-tree`, no worktree touched, kept under
  `refs/m3/integration/<run>/<task>`) and passes it as the task's `base_ref`; a conflict or a missing snapshot rejects the order
  with a stated cause. On by default; with `integrate_predecessors=False` `after` only orders tasks in time.
- Until M2 exists `route:<id>` is delegated to a caller-supplied lookup, and the operator may write `direct:<provider>/<model>
  [@profile][#effort]` (`PinnedRoute` assigns one to every ready task). The core's FIFO label `local` is rejected: M3 never defaults a model.
- Tests: module suite `bt_scheduler_executor/tests/` (boundaries, lone-copy isolation, CLI, crash-at-every-step, concurrency,
  cancel/reconcile/classification matrices, real git handoff cases) and, in the methodology suite, `tests/test_scheduler_executor_adapter.py`,
  `tests/test_scheduler_executor_integration.py` (the real core + executor + fake provider binaries; boundary from outside;
  historical `RUN.json` byte-identical) and the opt-in `tests/test_scheduler_executor_real.py` (`BITACORA_M3_REAL=1`, bounded spend).

## Audit gate and rework (`bt_audit_gate`, `SchedulerCore.reject_and_rework`)

An audit task is accepted by what it **found**, not by the existence of its report. It lists one `*.findings.json`
ledger (`{"schema": "audit-findings/1", "findings": [{id, severity critical|high|medium|low, status
open|fixed|accepted, summary, tasks: [plan task ids whose result is wrong], evidence (fixed), accepted_by: "owner" +
reason (accepted)}]}`; the auditor's prompt carries this format). `bt_scheduler_quality_adapter` reads the ledger from
the verified snapshot after M6 says PASS and judges it with `bt_audit_gate.evaluate`:

- an open critical/high finding, a missing or malformed ledger, or a risk «accepted» by anyone but the owner turns the
  PASS into a **rejecting verdict** (evidence `audit gate: …`); a snapshot that cannot be read leaves the verdict
  pending instead of judging the ledger;
- when open findings name plan tasks, the same verdict calls `core.reject_and_rework(...)`: in one transaction M1
  rejects the audit attempt and sends the named tasks, **everything downstream of them** and the audit itself back to
  `pending` with a fresh attempt budget (`operations.rework`, audit `rework_requested`). Tasks whose prerequisites are
  still completed become `ready` at once; the scheduler redoes them, and the audit runs again at the end. Nothing is
  completed by the rework: each redone task needs a new independent verdict;
- the reworked tasks read the findings in their next prompt (`RUN.notes/<task>.audit.md`, a dependent reads why it was
  reset); the redo must prove each fix with a test over the real entry point;
- an audit is **read-only**: the adapter compares the snapshot with its base (`git diff`, exact) and rejects the audit if it changed any file other than the ones it declares (report, ledger; `gates.audit_read_only`, default true). An auditor that patches source hides the builder's defect from the router and, beside a second auditor, hands every later task an `INTEGRATION_CONFLICT` between the two patches (REQ-027, T18 vs T18b). It records the defect as an open finding naming the task that owns it, and the system sends that task back;
- bounded and owner-configurable (`bitacora.py config`): `gates.audit_blocking` (severities that reject, default
  critical+high), `gates.max_reworks` (times one task may be sent back by the system, default 2) and
  `gates.audit_ledger_required` (default true; set false only to let an old plan without a ledger through: each skip is
  recorded as `audit_gate_skipped`). When the rework cannot start: a **live attempt** in scope defers the whole verdict
  (nothing is applied; M6 offers it again later), **`max_reworks` reached** applies the rejection and blocks the audit
  at once with reason `rework_limit` (a decision card asks the owner; retrying the auditor cannot help), a cancelled
  run only applies the rejection. The owner can always send work back by hand past the limit:
  `scheduler-op REQ rework T1,T2 --reason …` (refused while a task in scope has a live attempt: cancel it first);
- a plan written before the gate is brought in line with `plan-json retrofit-audit REQ-NNN` (adds the ledger path to each
  audit task, in PLAN.json as a new working revision and on its PLAN.md line; then review, `freeze`, `scheduler-op REQ
  revise` and `scheduler-op REQ rework <audit task>`: the audit runs again and the system takes it from there).

**Second auditor.** One auditor's omissions must not decide the outcome, so with `gates.second_auditor` on (default) a
plan that has an audit also needs an independent cross-check audit: another `kind: audit` task over the same scope with its
own report and ledger. Each audit is gated by its own ledger, so the union decides and either one reopens work. The
launch/approval gate (`bt_plan_adapter.second_auditor_problem`, inside the consumer gate) refuses a plan with a single
audit and names the fix: `plan-json retrofit-audit REQ-NNN --cross-check` clones the audit (own report and ledger,
same prerequisites; whatever waited for the audit waits for both). The planner module itself only warns. Routing stays
with M2 (cost- and quota-aware, risk floors): the cross-check is meant to be a bounded pass, so classify it honestly.
Turn the policy off with `bitacora.py config set gates.second_auditor false`.

No agent and no operator has to reopen anything by hand: the system does it from the ledger.

## Quality verifier (`bt_scheduler_quality`, M6)

M6 checks the exact approved M1 `VerifyOrder` against the matching, validated M3 handoff snapshot. Its standard-library-only
package stores private durable evidence, runs commands in the required bubblewrap sandbox, and sends correlated PASS/FAIL
verdicts through M1. `NEEDS_REVIEW` creates a durable review item and leaves M1 in `VERIFYING`; an Ack means admission,
not acceptance. The M6 package imports no methodology module.

- Adapter: `skill/scripts/bt_scheduler_quality_adapter.py` reaches M1 and M3 public types only through
  `bt_scheduler_adapter` and `bt_scheduler_executor_adapter`. It admits work to M6, validates the exact approved plan
  and M3 handoff, and delivers the versioned verdict through M1's existing port.
- Composition: `skill/scripts/bt_scheduler_executor_wiring.py` accepts `quality_store_path` as an explicit opt-in for
  low-level isolated/custom compositions and optionally a `quality_policy` mapping. The supported Scheduler owner
  always passes the distinct private M6 path and does not fall back to a caller verifier. The durable store must be
  separate from M1, M4 and M5. Shutdown drains and closes M6 before its store, the M5 store, the M3 stream bridge and
  executor.
- Full local proof: `tests/test_scheduler_m1_m6_e2e.py` freezes a real Planner plan, routes through M2, launches local M3
  children, records M4 stream events, observes M6 FAIL → M1 rejection → M5 retry → fresh M2 decision → continued M3
  snapshot → M6 PASS → M1 completion. It uses no provider CLI or credentials.
- Package: `bt_scheduler_quality` and its JSON fixtures/contracts are declared in `pyproject.toml`; the methodology
  adapter and runtime composition are shipped as modules. M6 is mandatory for the supported Scheduler owner commands;
  the low-level composition seam stays opt-in.
