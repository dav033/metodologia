# Task DZ-code — `design` kind and Designer awareness across routing, telemetry, CLI and prompts

Read first, binding: `/home/david/dev/.designer-wt/RULES.md`, then `CONTEXT.md` and `INVENTORY.md` there.
Worktree branch `dz/DZ-code` from origin/main. Parallel tasks: DZ-docs (markdown only) and DZ-approval (approval
CLI/web/gate in `bitacora.py`/`bt_rounds.py`/`bt_server.py`/`bt_page_req.py`/`bt_page_plans.py`/`bt_planstatus.py`/
`bt_planblock.py`/`bt_notify.py`/`bt_handoff.py`/`bt_scheduler_executor/{core_port,gates}.py`/`bt_flow_bus.py`/
`bt_page_graph.py`). Do NOT edit those files.
You own: `bt_agent_models.py`, `bt_routing_policy.py`, `bt_role_routing.py`, `bt_cli_delegate.py`, `bt_cli_accounts.py`,
`bt_events.py`, `bt_efficiency.py`, `bt_runprompt.py`, `bt_context.py`, `bt_agents.py`, `bt_scheduler_executor/prompt.py`
(+ executor README lines for prompt content), and their tests.
Implement INVENTORY.md "Code" items for these files with fail-first tests:
- `design` is a first-class kind everywhere kinds are listed/inferred/validated/aggregated (KINDS, infer_kind word
  patterns such as design/mockup/wireframe/UI contract, MAX_KIND_TIER, CLI `--kind` choices, telemetry buckets and
  efficiency metrics) — a `design` task must never be counted or routed as `implement`.
- `--role designer` appears in delegate hints; routing for `design` → `designer` consistent with `bt_role_policy.py`
  (Designer is a producer: no provider-independence requirement like reviewer/antagonist).
- Executor prompt: a `design` task gets its contract path `design/contracts/<c>@v<N>.md`, version, write scope
  (`design/` only, preview only if enabled) and the rule that it never approves its own contract; a `ui:true` task gets
  the approved contract path/version and "read it before implementing; report conformance"; a visual-review task gets
  the contract plus the instruction to request Runner screenshots per breakpoint × state.
- Session context (`bt_context.py`/`bt_agents.brief()`): one line that the Designer exists, owner approves contracts
  (`bitacora.py design approve`), and `design.preview` is configurable.
Legacy behaviour for other kinds unchanged. Run focused tests, the executor module suite, and the full root suite.
