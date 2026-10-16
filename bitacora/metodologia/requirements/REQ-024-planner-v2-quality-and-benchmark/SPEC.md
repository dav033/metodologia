---
id: REQ-024
status: ready
created: 2026-10-16
track: deep
---
# REQ-024 — Planner V2 quality and reproducible benchmark

## Problem & goal
The current methodology Planner has a strict, isolated plan-contract module and a new Planner-only profile. Its
latest Opus rerun found a real structure-name collision that the earlier Pictures plan missed, but its task plan is
less explicit about implementation algorithms and checks. The earlier Pictures plan now contains later coordinator
revisions, partial implementation, verification results and review findings, so it is not a clean record of the
original model output.

Evolve the existing Planner V2 architecture so plans are technically precise, traceable, verifiable, safely
parallelizable, operationally useful and economical to execute. Do not restore or copy V1. Prove what improves with
a reproducible benchmark; do not claim superiority when the available evidence cannot support it.

The Planner role must also be launchable through every AI runtime and account profile already configured on the
computer. Keep one provider-neutral source of Planner instructions and let the caller select the provider, account
and model. A model may plan poorly; this requirement does not promise equal quality or benchmark every model. Handle
model-specific failures when they are observed.

**Success looks like:** New plans preserve the current contract and scheduler boundaries unless a versioned change
is justified; every in-scope requirement maps to actionable work and objective evidence; known V1/V2 REQ-017 failure
cases are represented; deterministic quality checks reject reproducible counterexamples; benchmark outputs record
their provenance, repeat conditions and actual results; and any comparison separates measured facts from human
judgment. The same Planner role can be invoked from each locally configured AI runtime/account profile, with model
selection owned by the caller and no cross-model quality guarantee.

## Users / actors / stakeholders
- David: owns product decisions, scope approval and the final benchmark interpretation.
- Planner agent: inspects a repository and produces SPEC/PLAN artifacts; it must not implement, approve or launch.
- Implementer agents and Scheduler: consume task contracts and dependency edges without inventing architectural
  decisions or reconstructing the DAG from prose.
- M1/M2/M3/M4/M6: retain their current state, assignment/quota, process, observation and verification boundaries.

## Scope (in)
### US-1 (P1, Must) — Evidence-backed planning
As an owner, I want the Planner to preserve technically important behavior and expose unresolved decisions so
implementers can act without inventing business rules.

### US-2 (P1, Must) — Executable task graph
As a Scheduler and implementer, I want requirement links, dependencies, safe parallel boundaries and shared
interface contracts expressed explicitly so work can be assigned, retried, reviewed and integrated.

### US-3 (P1, Must) — Defect-detecting plan review
As an owner, I want deterministic checks to catch structural defects and a bounded semantic review to catch
contradictions, regressions, risk and avoidable complexity before a plan is returned.

### US-4 (P1, Must) — Reproducible quality evaluation
As an owner, I want matched, versioned benchmark cases and a transparent rubric so V1, current V2 and improved V2
are compared without attributing later edits to a model or inventing scores.

### US-5 (P1, Must) — Observed execution learning
As a Planner, I want access to relevant verified history about duration, failures, retries, quality and consumption
when sufficient comparable data exists, while M2 remains responsible for route and quota decisions.

### US-6 (P1, Must) — Provider-independent Planner launch
As an owner, I want to launch the same Planner through any AI runtime/account profile already configured on this
computer, so the chosen subscription or model does not determine whether the Planner role is available.

## Out of scope
- Changes to Pictures' functional REQ-017 behavior or implementation. REQ-017 is a planning benchmark only.
- Restoring V1, copying its prompt, or replacing the isolated bt_planner module.
- Letting Planner choose a provider, model, account, effort, worker count, reserve quota, supervise or change run state.
- Comparing models or promising equivalent planning quality across providers; handle poor model behavior as a separate
  issue when it is observed.
- Installing new AI clients, creating accounts or subscriptions, or storing provider credentials.
- Unrelated Scheduler features, broad methodology refactors, global hook/settings changes without evidence that a
  hook change is required, and new third-party dependencies without a demonstrated need.
- Claiming superiority from a single output, unmatched contexts, synthetic results presented as real, or subjective
  scores without rubric evidence.

## Requirements
- R1. The diagnostic shall distinguish executable code, configured instructions, observed plan behavior, later
  coordinator/reviewer edits, implementation activity and proposed improvements.
- R2. Before changing Planner behavior, the work shall inspect the current Planner profile, private skills, hook and
  installer paths, bt_planner, its adapter, Scheduler/telemetry consumers, contracts, tests and generation
  configuration. Claims about V1 shall be limited to artifacts or source actually recovered.
- R3. Each plan shall trace every numbered requirement to one or more task IDs, dependency paths, task/milestone
  acceptance criteria and verification evidence; the quality gate shall report uncovered requirements, orphan work
  and invalid references.
- R4. For non-trivial logic, plans shall state required inputs/outputs, precedence, algorithms, invariants, preserved
  contracts, error/exception behavior, unresolved decisions and observable acceptance without dictating local
  implementation details that do not affect those outcomes.
- R5. Verification shall distinguish static, functional, integration, regression and product-level evidence where
  applicable. Every command shall exist in the inspected repository; planned tests shall be labeled as work, not
  reported as passing; passing tests alone shall not be represented as proof of product acceptance.
- R6. Before returning a plan, the review shall check requirement coverage, graph consistency, shared paths/resources,
  parallel safety, interface ownership and handoff contracts, contradictions, ambiguous tasks, regressions,
  persistence compatibility, security/privacy, reversibility, assumptions, cost and unnecessary work. It shall
  separate demonstrated defects, plausible risks, facts and product decisions.
- R7. Parallel task interfaces shall define producer/consumer task IDs, owner, inputs, outputs, invariants and
  integration criteria before execution when tasks share an interface. after edges and resources shall encode real
  prerequisites/conflicts; the Scheduler shall not need to infer task ordering from narrative prose.
- R8. Any contract/schema change shall identify consumers, compatibility behavior, migration and rollback before
  implementation. Existing plans and current Scheduler boundaries shall continue working unless an approved,
  versioned migration says otherwise.
- R9. Plans shall declare each task's model-agnostic work kind using the existing Scheduler-supported kind
  vocabulary; unsupported specialist capabilities remain explicit constraints or unknowns, never invented routing
  eligibility. Where verified and comparable observations exist, Planner estimates and risk notes shall use observed
  duration, outcomes/retries, quality and consumption with source quality, per-metric sample count, units,
  comparability and uncertainty stated. Sparse, synthetic, missing or incomparable data shall remain unknown.
  Planner shall not
  duplicate M2 routing, capability eligibility or quota logic.
- R10. Quality checks shall use deterministic validation first. A semantic model review may run only when it adds
  demonstrable value; its claims, provenance and result shall be separate from the structural validator.
- R11. The benchmark shall use REQ-017 plus multiple representative non-Pictures scenarios, a pinned rubric and
  versioned input/context/provenance. It shall compare equivalent repository snapshots, model/effort/tool budgets
  and equal review opportunities wherever a controlled baseline is available. Historical V1/V2 artifacts with
  unequal edit histories shall be scored as retrospective evidence, not as a controlled experiment.
- R12. The benchmark shall report coverage, technical precision, verifiability, architecture, parallelism, risk
  detection, ambiguity, efficiency, between-run stability and observed execution/rework separately. It shall retain
  per-case evidence and raw results, distinguish measured values from human judgments, and make no unsupported
  aggregate or superiority claim.
- R13. Implementation shall preserve reversibility and isolation, make no unrelated changes, add behavior tests for
  validator/contract changes, and record real check results and remaining limitations.
- R14. On completion, generate a fresh Pictures REQ-017 plan using Claude Opus 5.5 high and the updated Planner
  instructions as a fixed reference run for reproducibility. This model choice does not restrict Planner invocation.
  Preserve the result as a draft for comparison; do not approve, freeze, launch, or implement Pictures work.
- R15. The shared Planner role shall be launchable through every AI runtime and account profile configured in the
  local methodology launcher when the baseline inventory is recorded. Keep its instructions and private resources
  provider-neutral; pass the caller-selected provider, account, model and effort through without substitution. Use a
  provider-native agent definition where available and a thin invocation adapter otherwise. If a runtime or account
  cannot launch, return its explicit error; never silently fall back. Verify launch and response only; do not compare
  model quality, rank providers or require equivalent plan quality. Do not install AI clients or create subscriptions.

## Edge cases & errors
- The raw V1 plan, delegated prompt and session log are recoverable from
  `D-20261016-090752-bc5d`, but this was a one-off generic Claude Work delegation, not a runnable V1 Planner profile.
  It used a follow-up prompt with pre-digested evidence, a `bypassPermissions` session with broad tools, injected
  SessionStart project context, and no pinned repository SHA. Treat it as retrospective evidence, not a controlled
  V1 arm. The live V1-labeled Pictures PLAN.md also includes later edits and partial implementation; do not treat
  that file as raw model output.
- Historical outputs may use different prompts, permissions, repo states or review counts. Mark them retrospective
  and exclude them from controlled causal claims.
- No or sparse metrics, changed comparability keys, missing M4/M2 stores, invalid telemetry, synthetic samples and
  claimed-but-unverified outcomes must not become numeric estimates or evidence of success.
- Shared expected paths, API contracts or generated tests may make apparently independent tasks unsafe to run
  concurrently.
- A new PLAN.json version may break older plans, parser consumers, M2 classification, review UI, run handoffs or
  frozen hashes if migration and compatibility are incomplete.
- Product verification may require a paid/live model turn. Prefer deterministic fixtures; label unperformed product
  checks as unverified.
- A configured runtime may have no native agent-profile format or a selected account/model may be unavailable. Use
  the shared Planner instructions through an invocation adapter where needed; surface launch/authentication errors
  without substituting another provider or account. Launch smoke checks are not quality evaluations.
- Benchmark quota may be insufficient for the full proposed sample. Record the actual run cap and mark missing cells
  incomplete; do not silently substitute a different model, effort, budget or review count.

## Constraints
- Keep bt_planner dependency-free and isolated; methodology reaches it through the existing adapter unless evidence
  justifies a narrow, versioned boundary change.
- M1 owns run/task state and authorization; M2 owns route/model/account/effort and quota decisions; M3 owns process
  lifetime; M4 owns observation/metrics; M6 owns verification/integration.
- The caller or existing launcher owns provider/account/model/effort selection. The Planner profile must not pin a
  model or account, and the generic Planner instructions must not duplicate provider routing.
- Support the AI runtimes/accounts already configured through the local launcher. Do not create accounts, subscribe,
  install new provider clients, or persist credentials as part of this requirement.
- Do not store raw prompts, private conversations or secrets in benchmark records. Store only the plan artifacts,
  bounded evidence, model/config identifiers and metric provenance needed for reproducibility.
- Do not add dependencies without a demonstrated need. Do not modify or test the Pictures product implementation.
- Never push, merge to main, commit without a separate request, discard local edits or include unrelated worktree
  changes.

## Priorities & phases
1. Diagnose artifacts, actual code/configuration, local AI runtime/account profiles, consumer boundaries and baseline
   checks.
2. Design the smallest compatible Planner/profile/validator/telemetry evolution and provider invocation adapter.
3. Implement with focused regression tests and update only relevant Planner resources and integration contracts.
4. Evaluate on controlled scenarios and historical REQ-017 evidence; correct findings and repeat affected checks.
5. Generate and validate the final Opus 5.5 high REQ-017 draft; leave product behavior untouched.

## Timeline & dependencies
- No calendar deadline was provided.
- Contract and telemetry boundary decisions depend on the Phase A consumer audit. Benchmark claims depend on recovering
  the exact baseline instructions or explicitly classifying the evidence as retrospective.
- Provider-neutral invocation work depends on the M1 inventory of local launchers, account profiles and their native
  agent or prompt-injection mechanisms. Any live smoke call cap must be approved after that inventory.
- The final REQ-017 generation depends on the updated Planner profile and passed deterministic gates.

## Assumptions
- The raw V1 output is recoverable from `D-20261016-090752-bc5d/RESULT.json`; the live Pictures PLAN.md has
  post-generation revisions and implementation data, and the isolated 2026-10-16 Planner-profile Opus rerun is the
  current V2 reference. The V1 task/session records contain no runnable V1 Planner profile or pinned repository
  SHA, so the raw result is a retrospective reference rather than a controlled baseline.
- V1 is a historical quality reference; controlled comparisons will use a pinned current-V2 baseline and the
  improved V2 where source/configuration can be held constant.
- Existing Planner-only skills can be extended before creating another skill. No separate hook-specific skill or
  hook configuration change is assumed unless Phase A finds the hook path causes a reproducible planning defect.
- Product choices in Pictures REQ-017 remain untouched and unanswered.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Deferred |

## Clarifications
- Source directive: /home/david/.codex/attachments/e4325016-cb8c-4d9f-a42a-5c6e74d563ab/pasted-text-1.txt (2026-10-16).
- No product decisions are inferred from the open Pictures REQ-017 round; its choices remain assumptions for planning comparison only.
