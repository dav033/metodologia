---
id: REQ-025
status: clarifying
created: 2026-10-16
track: standard
---
# REQ-025 — M2 quota-aware provider and account routing

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The Scheduler's initial M1→M2 route map sent five of seven tasks from the frozen Opus REQ-017 plan to Claude Sonnet xhigh, one audit to Sonnet medium, and one low-risk test task to Haiku. M2 currently raises every `risk: medium` task to tier 1, and the full-plan adapter asks for an independent decision per task. The run therefore repeated one route instead of allocating the DAG jointly.

The local quota cache showed why Codex and Gemini could not be considered: both Codex profiles had stale observations and `app_server_unavailable`; Antigravity's last observation was about 9.4 hours old, beyond its two-hour eligibility TTL. Claude observations were fresh. Gemini is also intentionally ranked behind Claude/Codex for implementation work under D-004. Those are separate causes: stale quota makes a route ineligible, while the provider-role rule demotes Gemini even when quota is better.

M2 already records the selected `profile` and opaque `account_ref`, but the full-DAG path makes per-task decisions and does not jointly balance recommendations across effective accounts. The account-specific recommendation is present in route metadata; the routing policy and its explanation need to make account headroom and task fit useful across the whole plan.

**Goal:** revise Scheduler route assignment so each task gets a justified provider, model, effort, and effective account based on its validated task requirements and fresh account quota, with a transparent reason when other accounts cannot be selected. Preserve M1's dispatch-time revalidation and reservation authority.

**Success looks like:** offline cases with fresh quota for Claude, Codex and Antigravity demonstrate that route choice follows task-tier requirements and account headroom rather than a fixed Claude preference; the frozen seven-task artifact no longer maps medium-risk labels alone to five Sonnet xhigh routes; every recommendation names its profile/account and records why it won, while stale/unavailable alternatives show explicit exclusion reasons. No live model turn is needed to verify this behavior.

## Users / actors / stakeholders
- David: owns routing priorities, scope and approval.
- M1 Scheduler: sends the full approved DAG, later revalidates READY-task assignments, and owns capacity reservations and dispatch.
- M2 Decision Engine: applies deterministic task-fit, quota, history and account-allocation policy.
- Configured providers and profiles: Claude Personal/Work, Codex-1/Luis, and Antigravity are candidate sources only when their runtime, authorization and quota evidence permit.

## Scope (in)
### US-1 (P1, Must) — Match route tier to task needs
As a Scheduler, I want the minimum model/effort tier to reflect the task's validated complexity, reach and risk so simple work is not promoted solely by a broad medium-risk label.
**Acceptance:**
- Given the frozen seven-task REQ-017 artifact, when M2 derives task floors, then the decision records the exact classification fields and rule that set each floor.
- Given a high-risk, architecture-level or full-system task, when M2 enumerates routes, then no route below its approved minimum tier is eligible.

### US-2 (P1, Must) — Choose across configured providers and effective accounts
As an owner, I want each task assigned to a specific capable profile/account using fresh quota and verified route evidence so unused eligible subscriptions can be used deliberately.
**Acceptance:**
- Given fresh available quota for multiple providers/accounts, when M2 plans the DAG, then the selected routes follow the approved policy and are not statically restricted to Claude/Codex.
- Given a profile alias for an already represented account, when candidates are built, then its quota and account capacity are counted once.

### US-3 (P1, Must) — Plan the DAG jointly and explain outcomes
As an operator, I want all task recommendations planned as one deterministic allocation and to see the selected profile/account plus exclusions, so repeated per-task decisions do not silently consume the same account.
**Acceptance:**
- Given a bounded full plan and explicit account facts, when M2 returns the route map, then it returns exactly one recommendation or stable no-route reason per task without reserving M1 capacity.
- Given stale, failed, unknown or exhausted quota, when M2 filters routes, then the route map or decision record exposes the corresponding reason and never treats the old percentage as current capacity.

### US-4 (P1, Must) — Keep execution gates authoritative
As M1, I want dispatch-time eligibility and reservation checks to remain authoritative so an up-front route recommendation cannot launch on expired quota or conflict with current capacity.
**Acceptance:**
- Given quota or profile state changes after the initial map, when a task becomes READY, then M1 receives a fresh M2 recommendation and reserves only through its existing atomic path.
- Given absent or unusable quota-refresh data, when the route preflight runs, then no model process is started and the outcome states which evidence was unavailable.

## Out of scope
- Launching any live implementation, planner or benchmark task; calling models to compare quality; or claiming quota savings from synthetic data.
- Enabling Laya or any learned/LLM-based route chooser; M2 stays deterministic.
- Changing credentials, adding provider accounts, or changing the frozen Planner `PLAN.json` contract.
- Forced round-robin distribution or inferred cross-provider token/dollar conversions without evidence.
- Changes to Planner V2 benchmark requirements gated by P-103, except additive M1/M2 compatibility needed by this routing change.

## Requirements
- R1. When M2 enumerates routes, it shall retain the current provider/profile authority and hard-filter project authorization, effective-account duplication, runtime availability, authentication, cooldown, model support and fresh quota for every required window.
- R2. When M2 derives a minimum tier, it shall use the approved task kind and validated PLAN classification fields, record the rule used, and avoid raising every medium-risk task by default unless the owner confirms that floor.
- R3. When multiple routes meet the task floor, M2 shall rank eligible provider/model/effort/account routes using the owner-approved priority order; no provider-name preference may override hard eligibility or an explicit task floor.
- R4. When M1 asks for the full-plan route map, M2 shall produce a bounded joint allocation over tasks and effective accounts without creating reservations; M1 shall continue to revalidate the route when a task becomes READY.
- R5. When M2 emits or excludes a route, the decision evidence shall include the selected profile, opaque effective-account reference, model, effort, quota observation/validity and stable selection/exclusion reason, without credential material or task prose in the durable ledger.
- R6. When a quota source is stale, unknown, failed or malformed, M2 shall fail closed for that route and surface the source status; it shall not substitute a percentage from an expired sample.
- R7. When the batch exceeds its declared task/candidate bounds, M2 shall return a stable bounded error or partitioning result; it shall never silently omit tasks.
- R8. When the route implementation is tested, all quota refresh/provider interactions shall be faked or isolated; this requirement authorizes no live model calls or real task execution.

## Edge cases & errors
- Codex usage refresh returns `app_server_unavailable` while an older cache contains low utilization.
- Antigravity quota is fresh enough at run start but expires while a full plan is being routed or before a READY task dispatches.
- Claude aliases map to one effective account; two Codex profiles are distinct accounts; Antigravity exposes one account.
- A task's classification is incomplete, unsupported or internally inconsistent; all eligible routes are below a high-risk floor; or every route is stale/exhausted.
- A plan exceeds the joint allocator's bound, contains more tasks than M2 can represent, or has a dependency/resource shape that prevents a safe allocation.
- One account has substantial quota but its provider/model tier is unsupported or below the task floor.

## Constraints
Keep M1 authoritative for state and reservations. Preserve D-045's evidence-backed lexicographic policy and do not invent cross-provider token/dollar equivalence or numeric quality floors. Preserve D-049 effective-account deduplication and persisted quota-cache keys. M2's core remains deterministic and does not perform provider model calls. D-050 still prohibits live task/provider experiments under the failed T24 registration. The current worktree contains broad uncommitted Scheduler/M2 changes; implementation must preserve them and edit only files assigned to the approved requirement.

## Priorities & phases
- Must: resolve the policy questions below; make full-plan account allocation deterministic, quota-aware and explainable; preserve READY-time revalidation; offline regression coverage.
- Should: expose the selected profile and stale/eligibility explanations through the Scheduler projection/view.
- Could: report empirical route comparison/quality once sufficiently correlated real attempt data exists.
- Won't: run a live provider experiment or activate Laya as part of this requirement.

## Timeline & dependencies
Depends on the current M1/M2 contract in the dirty methodology worktree and REQ-020 T13–T23 artifacts. P-041 remains a separate gate for any live experiment; P-103 remains the Planner V2 benchmark gate.

## Assumptions
- Codex/Gemini's displayed lower percentages were stale observations and therefore cannot establish current headroom; M2's fail-closed exclusion was correct for those snapshots.
- The owner wants all configured providers, including Gemini, reconsidered as normal task candidates when their declared capability/tier and quota evidence permit; Gemini's measured latency remains an explicit selection factor, not a silent hard exclusion. Confirm against D-004 in the decision round.
- Initial assignment should remain deterministic and non-reserving; actual dispatch always uses current eligibility and M1's reservation path.
- Quota demand estimates remain unused for cross-provider balancing until there is real, attributable sample coverage; percentage headroom and source freshness are available now.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Partial — route trade-off decisions pending |
| Out of scope | Clear |
| Flows & behavior | Partial — quota-refresh boundary pending |
| Edge cases | Clear |
| Acceptance criteria | Partial — policy thresholds pending |
| Constraints | Clear |
| Priorities & phases | Partial — agreed after round |
| Timeline | Clear — no fixed date |

## Clarifications
<!-- ### Round N — YYYY-MM-DD
- Q: … → A: … -->
