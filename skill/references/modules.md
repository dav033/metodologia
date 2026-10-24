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
  `<requirement>/RUN.projection.json`. For schema 1.3.0 plans with subplans, read-only subplan/composition specs and
  derived statuses are exposed by M1; the adapter also exposes thin `record_subplan_version` and `record_composition`
  wrappers for F4-9. These audited facts gate composition tasks without changing task or attempt state. Publication
  binds to the accepted audit attempt and accepted member-task attempts, so rework or an affected revision makes the
  fact stale. Stale versions stay in audit history, show a stale-version attention reason, and keep the gate pending.
  An unaffected rebase can rebind the same version, commit, and manifest when the accepted identity is unchanged;
  changed work requires version N+1. Schema-4 facts without identity still load but count as stale. M1 demotes READY
  gates when their facts become stale and rechecks reserved starts before dispatch. Publishing requires accepted
  audit work. Composition candidate ids are immutable across manifests, so a different candidate needs a new id.
- **One authority per requirement**: the core's run database decides. The projection is never called `RUN.json`, so no
  legacy file can be overwritten by it. The adapter refuses to open a core over a legacy `RUN.json` (a run from before the
  marathon supervisor was removed); such files are historical, read-only and not migrated.
- The core is the only way an approved plan runs: `launch`/`handoff` call `scheduler-run`. It can also be driven directly
  through the adapter or `python -m bt_scheduler_core`.
- Tests: module suite `bt_scheduler_core/tests/` (boundaries, lone-copy isolation, CLI end to end, fuzzed invariants,
  crash-at-every-commit restarts) and `tests/test_scheduler_integration.py` (boundary from outside, frozen-plan hand-over,
  authority rules, historical `RUN.json` byte-identical).

### Composition engine (`bt_composition`, F4)

`bt_composition` is the isolated composition engine; `bt_composition_adapter.py` is its only methodology importer and
owns the real Git port. It publishes immutable `SP@vN` refs, creates disposable `C<N>` candidates from published
subplan versions, and advances `current` only after candidate-bound M6 verdict proofs pass. Rejected candidates leave
the published composition intact. Selective propagation returns only evidence-supported actions; ancestry alone never
triggers reimplementation. The package does not know project paths or launch agents.

The opt-in owner path lives in `bt_scheduler_owner_composition.py` and
`bt_scheduler_owner_propagation.py`, wired by `bt_scheduler_run.py`. It binds its composition store and owned workspaces
to the project, requirement, M1 run, frozen plan identity and one repository. Multi-repository plans fail closed until
there is a cross-repository candidate contract. M1 stores durable scheduler facts and gate holds; the composition
store owns candidate/version manifests and refs. M5 proposes a demonstrated downstream action, and the owner applies
that exact task frontier through M1 idempotently.

M1 persisted run-state schema 9 carries subplan version facts, composition facts and durable composition holds, M6
`NEEDS_REVIEW` holds, and structured executor failure classification/code-attempt accounting. Legacy schemas 1–8 load
and upgrade in memory; schema 9 is written on the next state change. Composition facts are bound to accepted audit and
member-task attempt identities; stale facts keep gates pending. A `NEEDS_REVIEW` hold lets M5 resume, wait or block the
same verification attempt without spending a code attempt.

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
- F4-9 adds an opt-in owner runtime for frozen `1.3.0` plans that declare subplans. `bt_scheduler_run.py` owns the
  reconciliation loop; `bt_scheduler_owner_composition.py` handles subplan versions, durable gate reservations and
  verified publication, while `bt_scheduler_owner_propagation.py` derives declared downstream consumers and calls
  M5's `composition_propagation` port before applying the exact returned frontier through M1. It creates a dedicated
  `.state/composition/<project>-<REQ>.db` and owned workspaces under `.state/composition/workspaces/`, bound to the
  project, requirement, M1 run, plan revision/hash and repository identity. Accepted M3 line refs and M6 result
  manifests are reconciled through public M1/M3/M6 and composition adapters; stale versions are filtered, candidates
  are reserved once and loaded by manifest identity after restart, and per-gate errors emit owner attention records.
  M6 PASS/FAIL proofs bind the candidate, manifest, contract identities and tree. Multi-repository plans fail closed
  with `OWNER_COMPOSITION_MULTI_REPOSITORY_UNSUPPORTED`; there is not yet a cross-repository commit/workspace contract.
  The planner default is `1.3.0` for subplan plans: stub-agent owner E2E and M6 review hold/resume are wired. Planner
  checks the owner's gate chain, exact contract paths and one-repository boundary before run start. M1 exposes
  an operation for applying an explicit M5 frontier to exactly its named tasks, bound to the current published
  composition manifest and tree; it does not expand descendants. Owner M6 checks resource names against the process environment and
  `~/.config/flow/secrets.env` without persisting values. Sandbox needs no authorization; staging and production
  require a matching entry in `<bitacora root>/<project>/verification-policy.json`, and missing, unreadable or
  unmatched policy denies before command launch. The owner propagation producer is wired for changed published
  subplan versions included by a published composition; M5 evidence must carry stable evidence ids, and M1 applies
  actions idempotently by change id. Schema 1.2.0 remains supported for legacy plans.

### Verification inputs, analyst stops and audit ledgers

The planner checks explicit verification input paths against `git check-ignore` in the repository checkout resolved by
its adapter. An ignored input needs a preceding producer command in the same task (an explicit output option, shell
redirection or `touch`); declaring it in `expected_paths` does not create it. Missing git or an unresolved checkout
leaves this check silent. The isolated planner receives repository facts as a callback and never starts a process.
Known reads of ignored paths are errors; arguments whose input/output role the planner cannot establish only warn.

A finished failure analysis with `not_the_task: true` and confidence other than `baja` also interrupts a ready or active
task, before its retry budget runs out. The watcher uses the operator's cancellation move and blocks the task under the
same hold, then feeds the ordinary decision card into `analyst_case` and the existing repair flow. `RUN.healing.json`
records the analysis fingerprint so a restart never repeats that interruption; an operator hold or `heal stop` wins.

`bitacora.py audit-ledger check <file>` validates the engine-owned `audit-findings/1` contract (exit 0 valid, 2 with
problems). Open findings can be structurally valid and still fail the audit gate. `tasks` and `taskReferences` are
compatible fields (`tasks` takes precedence); `fixed` and `closed` both require evidence. Severities are critical,
high, medium, low and info; accepting a risk still requires `accepted_by: owner` and a reason. Project-specific scripts
that check audit ledgers receive planner advice to use this command instead.

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
- For schema 1.3.0 `design` tasks, M3 gates snapshots before verification: changes stay in `design/`; preview needs
  `design.preview` or `design.preview_projects`. Refusals retain snapshots (`DESIGN_SCOPE_VIOLATION`,
  `DESIGN_PREVIEW_DISABLED`).
- For 1.3.0 plans with subplans, M3 folds accepted contributions into refs/m3/line/<run>/<repository-role>/<SP-id>;
  each scope includes its accepted member tasks and accepted ancestors from the frozen plan. Redos replace the prior
  delta and conflicts remain explicit. Tasks outside subplans require the injected owner `composition_base(task_id, order)`
  identity; absent/empty identities are rejected as `COMPOSITION_BASE_MISSING` and are never rebuilt from all accepted work.
  The start gate checks each `ui: true` task's exact `design/contracts/<contract>@v<version>.md` blob in that selected
  base tree before launch and its owner approval (D-127): `DESIGN_CONTRACT_UNAPPROVED` or `DESIGN_CONTRACT_HASH_MISMATCH`,
  returned as a blocked-environment `Ack.classification` so no code-retry budget is spent.
  Reviewer briefs derive `review_axis: visual` only for frozen `subplan.ui.visual_review_task` tasks. Workspaces explicitly
  identify attempt, reconstructable subplan, and candidate integration kinds; integration cleanup is idempotent.
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
reason (accepted), semantic_fingerprint?}]}`; the auditor's prompt carries this format). The optional fingerprint is
64 lowercase hexadecimal characters: SHA-256 of canonical compact JSON `[contract_id, failure_mechanism, trigger,
affected_frontier]`, after Unicode NFKC normalization, case-folding and whitespace collapse on each string; a frontier
list is normalized, sorted and deduplicated. The gate merges open blocking findings only when both carry the same
fingerprint, merging evidence references and task scope. Findings without fingerprints stay separate; different
fingerprints stay distinct even at the same location. `audit-ledger check` validates the field while older
`audit-findings/1` ledgers remain valid. `evaluate_many` combines independent ledgers and counts matching fingerprints
once across auditors. `bt_scheduler_quality_adapter` reads the ledger from
the verified snapshot after M6 says PASS and judges it with `bt_audit_gate.evaluate`:

- an open critical/high finding, a missing or malformed ledger, or a risk «accepted» by anyone but the owner turns the
  PASS into a **rejecting verdict** (evidence `audit gate: …`); a snapshot that cannot be read leaves the verdict
  pending instead of judging the ledger;
- **Evidence provenance is content, not commit identity.** An evidence JSON producer and the audit ledger may both
  record an optional `tree_digest` (`sha256:<64 lowercase hex>`). Generate it with
  `bitacora.py audit-ledger tree-digest <PLAN.json> --repository <git-root> --role <repository-role> --revision <commit>`.
  This read-only command hashes sorted tracked entries (path, mode, blob/submodule object id). Its shared scope excludes
  only exact report files (`.md/.json/.txt/.log/.csv/.html`, no globs) declared in `expected_paths` by **all** `test` and
  `audit` tasks in that repository, following quality reuse's `own_outputs` rule. Source, tests and configurations
  remain inputs. An evidence report produced by another task kind is also excluded when named by an audit's legacy
  `--integration-results` argument or by the digest command's repeatable `--evidence <path>` option; it must still
  be an exact report path owned by a task in that repository. For evidence named only in `integration_evidence`,
  both producer and auditor pass the same `--evidence` options when its producer is not a `test`/`audit` task.
  Commit any source edits before calculating provenance; the command reads a committed snapshot, not
  the working directory. Use the same frozen plan for producer and auditor. Changing exclusions requires regenerating
  the evidence; a different git revision alone does not.
  The ledger's optional `integration_evidence: ["docs/integration-results.json"]` names evidence from its audited
  repository. Without that field, old plans' `--integration-results <path>` or `--integration-results=<path>` command
  arguments supply those paths. `bt_audit_gate.evidence_gate` checks the evidence against the actual verified snapshot;
  a supplied ledger digest must also match that snapshot. Legacy evidence with only `revision` is compared by resolving
  that full commit id's **content** with the same exclusions (mutable refs such as `HEAD` are not provenance).
  A recorded digest takes precedence over a legacy revision.
  Missing, malformed, unresolvable or different evidence produces a `STALE_EVIDENCE` finding naming the tasks whose
  same-repository `expected_paths` contain that exact file. Those producers receive regeneration notes and go through
  `reject_and_rework`, with the existing limits/policy; stale evidence bypasses new implementation tasks from
  `bt_remediation`. The audit runs after regeneration. Undeclared ownership or an incorrect ledger digest rejects the
  audit with an actionable contract problem. Snapshot/tree-read outages remain pending. Ledgers without either
  provenance field or a legacy evidence argument keep their former behavior; no revision-string equality is imposed.
  When a standalone legacy `check-findings`/`validate-findings` script has current evidence content and the complete engine ledger/read-only gate passes,
  M6 records the engine's contract/provenance result in place of the private validator. Other commands still run,
  including a whole suite deferred on the earlier stale attempt; their failures still reject the audit. Without
  verified evidence provenance, a passing ledger gate does not override a failing command.
  Compatibility substitution accepts only recognized interpreter prefixes and contract arguments (`--ledger`,
  `--integration-results`, `--check-audit-diff`); unknown scripts, extra flags and compound commands still execute
  normally. New approvals use the engine command directly.
- when open findings name plan tasks, the same verdict calls `core.reject_and_rework(...)`: in one transaction M1
  rejects the audit attempt and sends back the named tasks, the `kind: test` tasks over them and the audit itself
  (`gates.rework_scope`: `named`, the default; `downstream` also resets **everything that depends on them**, which for a
  finding on a root task is the whole plan) to `pending` with a fresh attempt budget (`operations.rework`, audit
  `rework_requested`, `cascade`). What depends on a named task keeps its accepted result: the fix is a snapshot on top of
  the old one and the integrator merges it with theirs (a real overlap surfaces as `INTEGRATION_CONFLICT` naming both
  tasks). A task becomes `ready` only when **every ancestor** is completed. `scheduler-op REQ rework T1,T2 --only` does
  the same for the owner (without `--only`, everything downstream goes back).
  `scheduler-op REQ withdraw-rework T4,T5` takes a rework back for tasks that have redone nothing since (every attempt
  after the accepted one ended without a result): they return to `completed` on the verdict they already had, so no
  work is lost and no verdict is invented (audit `rework_withdrawn`); anything redone or never accepted is refused and
  nothing changes.
  A redo meets its dependents through the integrator: when a redone task clashes with a dependent that was built on
  the result it replaced, the two are merged over that earlier result as base (`merge-tree --merge-base`), which keeps
  the fix and the dependent's work; a real overlap still conflicts. A retry looks past cancelled attempts and refused
  starts to the last attempt that left work; a task with no prerequisites continues from its earlier result even
  when the plan was revised since or the repository head moved forward; and `scheduler-op REQ continue-from T3
  att-0042` directs the next start of one task to continue from a given accepted result. An owner note for a task
  goes in `RUN.notes/<task>.md`.
- an **integration gate** runs when a result is verified (`gates.integration_check`, default on): the integrator
  dry-runs (objects only) the integration of every task after it that is about to start, as if the result were
  accepted. If the result would clash with accepted work, the verdict becomes a rejection (`integration gate: T6+T10
  vs T13 for T14: files`) and the task gets a note to redo it as a small change; M5 retries it. The task that
  causes a clash is sent back at once, not a bystander blocked later when it tries to start; a clash the
  candidate takes no part in is not blamed on it. A task sent back also continues from its earlier result carried
  onto the redone prerequisites (`PredecessorIntegrator.carry`) instead of being rewritten; when the two overlap, the
  base is a **merge in progress** (git conflict markers in the overlapping files, kept under
  `refs/m3/integration/<run>/<task>-carried`) and the task resolves it in place, keeping both sides, rather than redoing
  its work from nothing; a result handed back with markers still in it (`PredecessorIntegrator.unresolved`) is
  rejected. `gates.integration_retries` (default 0) is how many times the task that caused a clash is retried before
  the accepted tasks it clashes with resolve the overlap on top of it. The merge
  fallback tries the earlier result of every prerequisite as merge base. Tasks whose prerequisites are
  still completed become `ready` at once; the scheduler redoes them, and the audit runs again at the end. Nothing is
  completed by the rework: each redone task needs a new independent verdict;
- an **integration line** (`gates.integration_line`, **default on since REQ-030**; REQ-028 part 1, `bt_integration_line`): the predecessor merge
  above keeps, per accepted task, the version of every file it was built on, so a redone task's fix can be lost behind a
  dependent that still carries the old text (REQ-027: T8a v3 never reached the audit through T15f). With the flag on (the default), each
  repository role of the run has one ref `refs/m3/line/<run>/<role>` holding the integrated tree, a deterministic fold (plan
  order) of every accepted task's own work (`start_base -> snapshot`, merge-tree with that merge base; objects only; the
  run base is pinned in `<ref>-base`). A new attempt starts from the tip without the task's own earlier result;
  acceptance applies the candidate to the tip, and a clash is the usual `integration gate:` rejection (`T vs line for T:
  files`), so the existing carry/resolve retry resolves it on top of the current tip. A task whose accepted result no longer
  fits after a redo is listed by `Line.needs_resolution` and left out of the tip (never silently resolved or dropped); its
  dependents are rejected with `PREDECESSOR_NEEDS_RESOLUTION` (permanent: a transient error would leave the attempt `uncertain`). A run that began with the flag on keeps it (`RUN.integration-line` marker). A run that already accepted tasks without it is **migrated** at the next start only when a dry-run fold (`bt_scheduler_executor_wiring._migration_probe`, in memory) holds every accepted contribution cleanly (`gates.integration_line_migrate`, default on); otherwise it stays on the predecessor merge and `RUN.integration-line.skipped` says which task does not fit. `recompute()` rebuilds the refs from persisted facts at
  owner start-up. Optional plan `generated_paths` allow conflicts in tracked build outputs to take the candidate's version,
  with `LineState.generated_stale` / `apply(...).generated_stale` listing those paths (no automatic rebuild;
  `generated_command` is metadata). Mixed conflicts still reject and list only undeclared paths. Resolution uses a
  private index, never the checkout or its index. See `plan-contract.md` for declaration limits and matching.
  If git fails the integrator falls back to the predecessor merge for that call and logs. Not done yet:
  a `resolve` attempt started by the line itself for an already accepted task (part 2), pinning each attempt's real start base;
- the **integration invariant** (`gates.integration_check_files`, default on; REQ-030, `bt_integration_invariant`): after every
  integration (predecessor merge and line fold) each file an accepted task left (`start_base -> snapshot`, added or changed)
  must be in the tree, and a file only that task changed must not be back at its old content. Exempt: a file another
  accepted task also changed (a merge may combine them), and a deletion that the deleting task declares in `expected_paths`
  or that a task built on the owner makes (the plan's own order). Anything else was lost silently (REQ-020 T14: a merge that
  trusted git ancestry dropped `directions.ts` and `packages.ts`); it is restored from the owner's snapshot as one repair
  commit, reported through `bt_interventions` (class `integration_defect`), and a repair that does not hold is
  `INTEGRATION_FILES_LOST` (permanent), never an incomplete tree. A candidate that deletes sibling files it does not
  declare is rejected at verification (`would_conflict`) with the owners and files;
- **parallelism by surface, not by size** (REQ-030): `scheduler.exclusive_scopes` is empty by default; what keeps two tasks
  apart is the overlap of their `expected_paths` and their `shared_resources` (a task that declares neither is serialised
  anyway). `gates.remediation_parallel` is on: the remediation tasks of disjoint components run side by side, and the core
  keeps apart any two that claim the same surface. Both apply only to a run on the integration line: a run in flight on
  the predecessor merge (no `RUN.integration-line`) keeps the old exclusive scopes (`bt_scheduler_run._run_config`) and chained
  remediation (`bt_remediation.parallel_for`, D-114) until it is migrated or ends; an explicit owner setting always wins. `bt_scheduler_replica` replays the recorded plans and attempt times of a
  night through the real core and reports minutes of attempt / wall minutes: REQ-020 went from 1.00 to 1.14 (-12 % wall
  time, the graph's own bound), REQ-029 stays at 1.01 because 34 of its 36 tasks claim `recovery-case-v1`; more slots
  (4 or 6) change nothing on either, so `max_parallel_tasks` stays 3;
- **minimal rework** (REQ-030): `gates.rework_confirm_over` (default 3) is the number of ACCEPTED tasks one action may send
  back without the owner: the audit gate blocks its own audit with `rework_impact` instead, and `scheduler-op rework|revise`
  refuse with the count and the estimated minutes until `--confirm`. `gates.rebase_cascade: content` makes `revise` keep every
  accepted task whose own content did not change (see the core README). The notes of a task sent back carry the real text
  and evidence of each finding even when the system did not send it back itself;
- **proportional verification** (REQ-030, `bt_scheduler_quality/reuse.py`, `bt_attestation`): see the quality README. The pass cache key leaves out the report files a `test`/`audit` task itself writes (`reuse.own_outputs`; `verifier.cache_ignores_outputs`, on): REQ-020's T14a rewrote `docs/req-020/integration-results.json` at every attempt, so three real attempts had 3 distinct trees but ONE tree ignoring that file, and its 10-minute `npm run gate` was paid each time. A check that names the file keeps it in its key; an implementing task's paths are never ignored. The
  environment guards are configurable and name their cause: `verifier.max_workspace_mb`, `scheduler.min_free_mb`;
- **M5 reason-aware recovery** (`bt_scheduler_recovery_adapter.py`): the optional `m6_evidence_reader` loads the persisted content-addressed M6 manifest and checks its request identity, revision, token and captured `snapshot_sha` before passing a closed reason code into `m5.recovery-case/2`; the snapshot is the binding identity, while tree digests are informational unless executor facts provide a comparable tree id, in which case M5 compares them. Absent reason codes remain `UNCLASSIFIED` with `/1` policy behavior. External/environment blocks return fixed actionable codes before retry exhaustion and never enter code-retry history; a verification `TIMEOUT` retries once, counted by reason across the task history; flaky and not-run evidence block; code failures use bounded rework; PASS never accepts. The optional `composition_propagation` port returns a validated `m5.demonstrated-frontier/1` with one preserved action identity (`reverify`, `reintegrate`, `audit`, `adapt_contract`, `modify`, `reimplement`) and only current scheduler task ids other than the source task; internal changes carry `none` and an empty frontier. M5 does not derive descendants or mutate M1. The F4-9 owner derives declared consumers in `bt_scheduler_owner_propagation.py` and applies actions through M1's idempotent demonstrated-frontier operation;
- **a refused verification order** (`Ack.permanent`, `bt_scheduler_core/dispatch.py`, `bt_scheduler_recovery_adapter.py`): the M6 adapter marks a malformed order, one that differs from the approved plan and an idempotency conflict as permanent; the core then fails the attempt (`verify rejected: <code>`) instead of re-sending it at every lease expiry, M5 blocks it as `m5:verify_rejected_<code>` (not owner-only, the work done stays for the retry) and the self-healing sees the text. A busy store stays transient. The watcher's notice for an attempt stuck in `verifying` after 3 identical rejections remains for ports that do not set the flag;
- **checks that map to criteria** (`bt_planner.quality.unmapped_checks`, `bt_plan_adapter.mapping_problem`): the verifier compares a check's `purpose` with the criteria of its task by exact text. Over four real runs the two most frequent stops were `CHECK_UNMAPPED` (59) and `CRITERION_MANUAL` (45), and REQ-020's plan carried 37 unmapped checks, 2 criteria without a check and 11 proven only manually. `plan-json check` now warns for each unmapped check with its closest criterion; `plan-json freeze` (the approval) refuses unmapped checks and criteria without a check (`planner.require_mapped_checks`, on by default; `--force` approves anyway); revisions the scheduler makes itself and plans already frozen are not gated. The Planner agent's instructions carry the rule;
- **self-healing** (REQ-030, `bt_scheduler_healing`, `bt_healing_classify`): the watchdog's `heal` runs a bounded cycle over the
  open stops. Each is placed in a closed taxonomy from the LAST real error and the evidence (`plan_defect`, `integration_defect`,
  `regression`, `environment`, `criterion_unmapped`, `quota`, `transient`; anything else is left for a person) and gets the smallest
  safe repair of its class: retry (`transient`, `quota`), redo the task built on a stale result (`integration_defect`), retry with the
  note the diagnosis wrote plus the evidence (`environment`), accept when every criterion passed and only an extra check is unmapped
  or give a check the exact text of its criterion in a new plan revision (`criterion_unmapped`), insert a repair task BEFORE a task
  that can only execute and record, built from the failing evidence (`regression`, `plan_defect`); an audit that still finds blocking problems after its `remediation_rounds` gets ONE extra round (`RUN.remediation.extra.json`) instead of a rework of accepted tasks; a full verifier workspace (ENOSPC while the host has >5 GiB free) doubles `verifier.max_workspace_mb` up to 8192 and retries (a full host disk is never touched). A case is its signature, so a
  restart never repeats a repair, and one that comes back after its repair is `exhausted` (the owner is notified, never the same
  strategy twice); `healing.max_per_task` and `healing.max_actions` bound it, `PER_CYCLE` bounds one pass. State and history are in
  `RUN.healing.json`, every intervention (automatic or by hand) in `RUN.interventions.jsonl` (`bt_interventions`).
  `scheduler-op REQ heal status|stop|start|run|revert CASE` is the owner's hand on it: `stop` switches it off at once, `revert`
  freezes a revision without the repair task and moves the run onto it. It never touches attempt counters. It never touches attempt counters.
  **Model step** (REQ-029 R3/R4, `healing.model_diagnosis`, off by default): a stop the rules cannot repair, or cannot place (class
  `unknown`), takes the validated option of the diagnosing model (`bt_block_agent`, `diagnosis.*`) — only `retry` / `retry_with_note`,
  only a task stop the owner could answer with a plain retry (never an owner-only decision or a review), never when the model is
  `baja` or its note is thinner than 20 characters (that becomes a plain `retry`), once per signature, then the owner decides.
  `gates.attestation_bind_attempt` (default on, REQ-029 A11): a manual-check receipt (`scheduler-op REQ attest`) covers only the attempt
  being verified, so a redone task has to be attested again; attesting needs a verification waiting for evidence;
- **structural recovery** (REQ-029, `bt_recovery_*`, `bt_scheduler_recovery_lifecycle`): for a conflict or an audit the ordinary budgets
  could not close, one bounded cycle per run and lineage: complete evidence (`conflict-observation/1` published before clipping),
  a constrained revision with convergence work (`convergence-work/1`), a run-scoped grant and a journaled application through one
  generic M1 primitive; only independent verification on the resulting integrated tree closes it. The plan page and the /flow feed show
  it with a stop control (a cycle's state change is a `recovery_cycle` event in the feed). The conflict observation carries the earlier results a side was built on (`carry_ancestry`); a recovery plan adds at most 8 corrective tasks (checked when it is compiled and again when it is applied, `CORRECTIVE_LIMIT`). **Audit path** (`bt_recovery_pipeline`, `bt_recovery_diagnosis`, `bt_recovery_export`; opt-in with `scheduler-op REQ recovery-enable`): an audit stop exhausted by `rework_limit` / `rework_impact` whose findings name at most 8 tasks, or an integration clash (below). The owner only queues the cycle (applying a revision stops the owner); the watchdog's `heal` takes it a step at a time from the durable `diagnostic_cycles` row: export the run's records as the five documents the collector reads (the plan document is the frozen plan's canonical bytes, a verdict given under another revision is refused), collect the evidence, show the model a bounded view of it (never the megabyte snapshot ledger), ONE invocation of the Planner-role route (`diagnosis.*` profile, authorized for the project), parse its answer as untrusted JSON, compile it (`bt_recovery_compiler`: only `correct_tasks` / `repair_verification` / `refresh_integrated_audit`, nothing weakened, a falsifiable `symptom_oracle`), issue a run-scoped grant and apply through the journaled `bt_recovery_apply`; then `executing` / `auditing` follow the ordinary scheduler and `succeeded` needs every corrective task and the independent audits accepted with the five-way proof of the resulting tree. Each stop is a durable blocker code (`evidence_unavailable`, `findings_too_broad`, `diagnosis_*`, `proposal_rejected`, `apply_blocked`, `corrective_task_blocked`, `independent_resulting_tree_proof_missing`). The **Conflict path** (`bt_recovery_lineage`, `bt_recovery_oracle`; `bt_interventions.record_conflict` writes every clash with ALL its paths to `RUN.conflicts.jsonl`): when the ordinary redo of a clash was exhausted, the facts are derived from the records (two unordered accepted tasks that both own the clashing paths, a consumer that waits for both; a stale side, a scope escape, ordered sides or more than two results are blocked with their own code), the model only judges whether the two requirements are compatible (if not: the owner's ruling) and writes the symptom oracle, whose red step is RUN in the verifier sandbox on an accepted side and must fail like a test; `plan_conflict_convergence` + the compiler then add ONE convergence writer (the owners' frozen checks, both acceptance contracts, a marker-free check per file, the oracle) that replaces the two sides in the consumers' prerequisites, and `PredecessorIntegrator` starts that writer from a merge in progress of both accepted sides measured from where each started (`unresolved` refuses a result that still holds a marker). Progress and proof are the audit path's. Details and rollback: `scripts/bt_scheduler_recovery/reviews/req029-rollout.md`;
- **no human in the loop** (the owner's rule, 2026-10-22): (1) `bt_watch_reload`: the watcher re-executes itself and restarts an idle owner when a COMMITTED engine fix lands (clean working copy only; owner immediately when idle, after 10 min with only verifications in flight, after 90 min while an agent works; marker `RUN.owner-code`), so nobody restarts anything by hand; (2) `healing.autonomous_default` (on): a task stop that neither the rules, the analyst nor the model placed gets the card's own recommended PLAIN retry (`retry`/`retry_with_note` only, never a review, an owner-only stop or a verdict), at most 3 times per task; after that the failure is not transient and the card stays. What still needs a person by nature: a production release, real-device checks, a mass rework past the ceiling, a full disk.
- **replica capture and attestation key** (P-163, P-162): the watcher saves `<project>/replicas/REQ.json` itself when its owner ends with every task `completed`/`cancelled` (a stalled run is not a replica), so the A/B settings grow with each real run; `bitacora.py attestation-key status|rotate` shows or rotates the HMAC key of the manual-check receipts: the previous key stays as `.prev` for one generation, a second rotation invalidates the receipts sealed under it (the task asks for its manual check again). The self-healing card shows up to three evidence lines per case;
- **optional RTK inspection** (`prompts.rtk`, default on): M3 checks PATH once per process and adds inspection/recovery guidance only when RTK exists; absent RTK leaves its prompt unchanged. Task verification commands and M6 evidence always run RAW, exactly as written.
- **concise engine prompts** (`prompts.concise`, default on): retries retain every distinct failure, with first/latest full text and `same failure ×N` for exact repeats; signatures never decide equality. New history records retain full text. Analyst/diagnosis/reviewer instructions shrink; reviewer verdict evidence and structured audit observations stay intact. The 80-line prompt budget removes adjacent identical lines with counts and yields to distinct evidence; repair excerpts keep complete commands, exit codes and distinct output lines. Off restores legacy prompt rendering and limits.
- **failure analyst** (P-138, D-115, `bt_attempt_analyst`): a task that failed MORE THAN TWICE is read by a model through the `diagnosis.*` profile (read-only; config `analyst.auto`, on): cause, what to do differently, whether the cause lies outside the task. It changes nothing; the answer is stored in `RUN.notes/<task>.analysis.json` and the next attempt's prompt carries it after the history, marked as an opinion to check against the code. The watcher starts at most one analysis per task (`scheduler-op REQ analyze TASK` does it by hand) and repeats it only after two more failures; an analysis that says the cause lies OUTSIDE the task with confidence above `baja` also places a stop the rules could not (`bt_scheduler_healing.analyst_case`): a regression whose repair task carries the analyst's cause and advice. The watcher's healing turn (healing, coordinator, analyst) runs also while the owner waits for a person, every 30 s (`HEAL_SECONDS`);
- **evolution** (REQ-030, `bt_evolution`, `scheduler-evolve [--propose|--apply|--revert|--capture REQ]`): a deterministic analysis of the
  interventions of a project turns repeated patterns into proposals with their evidence; HIGH-risk ones become numbered `P-NNN` items
  in PENDING.md, LOW-risk ones (an allowlist of bounded settings) are applied only if an A/B on the replicas saves time on one and
  costs none, and are recorded for `--revert`. `bt_recovery_benchmark` runs twelve stops of the REQ-020 / REQ-029 night through the
  current code (`tests/fixtures/recovery-scenarios-v1.json`); its results per version are in `recovery-benchmark-results.json` and
  a test fails when a version is worse than the previous one (v0, the night: 10 human interventions, 1,086 minutes waiting;
  v1: 2 interventions, 76 minutes; v2: 0 interventions, 8 minutes);
- **remediation** (`gates.audit_remediation`, default on; REQ-028, `bt_remediation`): a rejected audit does not reopen the tasks its blocking findings name. The gate records the findings (`RUN.remediation.json`), the owner exits, and the watcher turns them into the next plan revision: remediation tasks (`T18.1`, `T18.2`, ...; `T18.1b` for a second auditor) are appended on the tree the run already integrated, findings that share a task or overlapping paths are grouped and chained (up to 4 per task), independent groups run side by side, each finding is checked by the command of the task that owns it, and the audit is moved after them. The run is rebased (accepted work is kept) and the audit runs again from scratch. Each finding is still charged to the tasks that own it in the attempt log. An audit gets `gates.remediation_rounds` (default 2) rounds; with none left, or when a task cannot be built soundly (a finding names no task of the plan with a command), the named tasks are sent back as before. `scheduler-op REQ remediate` applies a pending request by hand. A task that is accepted clears the notes earlier rounds left for it;
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
verdicts through M1. Verdict values and meanings stay unchanged. Evidence is `m6.verify-result/1.1`; its additive
per-check and aggregate `reason_code` values are `PASS`, `FAIL_CODE`, `BLOCKED_EXTERNAL`, `BLOCKED_ENV`, `TIMEOUT`,
`FLAKY_SUSPECTED` and `NOT_RUN`. A check that fails then passes on the same evidence key is `FLAKY_SUSPECTED` and
leaves the verdict at `NEEDS_REVIEW`, never a clean PASS. Missing taxonomy in an old record reads as `UNCLASSIFIED`.
Evidence binds checks to snapshot/tree identity, contract identities and environment fingerprint. Pass reuse adds
contract and declared environment identities only when supplied, preserving legacy keys. Optional `composition_id` and
`manifest_sha256` must appear together; M6 records them with the candidate tree. M1 receives the taxonomy through its
existing `m6://result/<sha256>` evidence reference. `NEEDS_REVIEW` creates a durable review item and leaves M1 in
`VERIFYING`; an Ack means admission, not acceptance. The M6 package imports no methodology module.

- Sandbox policy (config `verifier.*`, D-095): checks share the host network by default (`QualityPolicy.network`, so live
  services and a database are reachable; name resolution and TLS files are mounted read-only) and may run deploy/migrate-style
  commands (`allow_production_actions`); either off restores the old offline / operator-review behaviour. The sandbox starts with an
  empty environment: `verifier.env_file` names a dotenv file outside the repositories whose variables the checks receive
  (`bt_verifier_env`; secret-looking values are registered for redaction). A check is one program per verification: shell
  syntax (`&&`, `|`, `;`) is rejected, only a leading `cd <dir> &&` and leading `NAME=value` assignments (run through `env`) are allowed, and one refused command makes M6 skip every check of the task; the plan check warns about it.

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

## Knowledge stores (`bt_knowledge`, F3)

The isolated `bt_knowledge` package backs both revision-bound project knowledge and Researcher's external research
claims. `bt_knowledge_adapter.py` owns the methodology boundary and database locations; Explorer produces a validated
delta and the ingestor writes it. The code map deduplicates relation evidence, preserves conflicts and stale history,
and supports commit/project/area queries with Markdown, Mermaid or JSON projections. The separate external store
keeps atomic sourced claims, retrieval/version/locator metadata, freshness, contradictions and subplan links; stale,
unverified or instruction-like claims do not enter facts-only dossiers. The package itself does not call agents, the
network or CodeGraph. See `skill/scripts/bt_knowledge/README.md` for its versioned contracts and stable errors.

## Engine benchmark (`bt_engine_benchmark`, D-10)

`bt_engine_benchmark.py` reproducibly replays the legacy and subplan plans against the real M1 `SchedulerCore`, with
and without injected P-177-shaped defects. It compares redone work, discarded accepted minutes, attempt minutes,
simulated wall time and a clearly labeled token proxy; it does not call providers or observe real token usage. The
command can also compare a supplied recovery baseline. Results are deterministic JSON/Markdown artifacts; see the
script's `--help` and `skill/scripts/tests/test_engine_benchmark.py`.

## UI design contract approval

For every `ui:true` task, M3 checks the versioned contract at `design/contracts/<contract>@v<N>.md` in the selected
base tree and the requirement's durable owner approval record (`design-approvals.json`). The record pins SHA256 of
`git show HEAD:<contract path>` in the repository assigned to the design task; M3 compares it with the selected
base-tree blob before dispatch. Missing approval returns `blocked_environment` with
`DESIGN_CONTRACT_UNAPPROVED`; a different or absent base-tree blob returns
`DESIGN_CONTRACT_HASH_MISMATCH`. These holds do not consume the code retry budget and are reconsidered after approval.
Every contract version needs its own approval. Use `bitacora.py design list|show|approve|changes REQ-NNN` or the
requirement page. A changes request records the owner's comments and reworks the accepted design task through the
M1 operator adapter so the Designer can publish a new version.
