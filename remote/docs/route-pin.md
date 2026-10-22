# Per-task route pin: where it enters M2 routing and the executor

Research note (REQ-027 T2). No per-task pin exists in the code today; this note says where one would enter and what
already covers that path. Paths are under `skill/scripts/`.

## Routing functions (M2 -> M1 -> M3)

| Stage | Function | File |
|---|---|---|
| Whole-plan route map (non-reserving) | `DecisionAssignmentPort.plan` -> `core.PlannedRoute` | `bt_scheduler_adapter.py` |
| Core consumes the map | `Scheduler._plan_all_routes` (+ `_valid_planned_route`) sets `route_metadata` / `route_status` = recommended or unavailable | `bt_scheduler_core/scheduler.py` |
| Dispatch-time choice | `DecisionAssignmentPort.propose` -> `core.Assignment(task_id, "route:<ref>", reason, route_metadata)`; helper `_route_metadata` | `bt_scheduler_adapter.py` |
| Batch ranking | `plan_ready_batch`, `persist_dispatch_batch`, `rank_with_route_policy` | `bt_scheduler_plan_routing.py`, `bt_scheduler_decision/` |
| Operator stand-in | `PinnedRoute.propose`: gives EVERY ready task one operator-written reference (`direct:<provider>/<model>[@profile][#effort]`) | `bt_scheduler_executor_adapter.py` |
| Reference -> route (executor) | `RouteResolver.resolve`, `check_context`, `gate_repository`, `validate_route` | `bt_scheduler_executor_adapter.py` |
| M2 reference lookup | `resolve_m2_route` (read-only ledger lookup) | `bt_scheduler_adapter.py` |

## Where a per-task pin enters

The seam is the `AssignmentPort.propose` result: the pin is just a `core.Assignment` whose `executor` reference is
the pinned route for that task. Two options:

1. As a `direct:` reference (like `PinnedRoute`, but keyed by task id). `RouteResolver.resolve` accepts it only when
   `allow_direct` is true (the default only without an M2 lookup), and it still passes `validate_route` and
   `gate_repository`.
2. As an M2 decision (`route:`/`m2:v1:` reference). It is then bound by `check_context` to plan id, revision,
   task id, `plan_sha256`, not superseded, and fresh quota.

`DecisionAssignmentPort.plan` would also have to return the pinned route as the task's `PlannedRoute`, otherwise
the recommended map disagrees with what is dispatched.

## Precedence

Proposed (not implemented):

1. Per-task pin, if present.
2. M2 selection (`DecisionAssignmentPort`).
3. Operator-wide `PinnedRoute` (a stand-in used when M2 is not wired).

Whatever wins, these always apply and a pin never bypasses them: `validate_route`, the work-only gate
(`gate_repository`), the `plan_sha256`/task/revision checks for M2 references, and the direct-reference refusal
when M2 selects routes unless `allow_direct` is set. A route already assigned to a started attempt is not replaced
(`_plan_all_routes` skips tasks with attempts).

## Covering tests (`skill/scripts/tests/`)

- `test_scheduler_executor_adapter.py`: `PinnedRoute("direct:claude/haiku").propose` (line ~375) and route resolution.
- `test_scheduler_executor_integration.py`: `TaskRoutes`, per-task references end to end through the executor.
- `test_scheduler_route_resolution.py`: M2 reference resolution, direct refused while M2 selects
  (`test_direct_references_are_refused_while_m2_selects_routes_unless_the_operator_allows_them`), wrong
  plan/task/revision/expired refused, superseded decision refused, policy still applies, launch revalidates.
- `test_scheduler_decision_integration.py`, `test_scheduler_decision_sources.py`, `test_scheduler_dispatch_generation.py`:
  `DecisionAssignmentPort` decisions and dispatch.
- `test_plan_amendments.py`: per-task classification overlay (`effective_meta`) affecting only the next decision.
- `bt_scheduler_core/tests/test_routing.py`: the core's route map (`_plan_all_routes`).
- `test_scheduler_executor_real.py`, `scheduler_executor_support.py`: wiring with `PinnedRoute`.

No test covers a per-task pin versus an M2 selection; that would be new.
