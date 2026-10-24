# Task DZ-approval — owner approval of design contracts (CLI, web, gate, notifications, status)

Read first, binding: `/home/david/dev/.designer-wt/RULES.md`, then `CONTEXT.md` (decision D-127) and `INVENTORY.md`.
Worktree branch `dz/DZ-approval` from origin/main. Parallel: DZ-docs (markdown except modules.md/plan-contract.md)
and DZ-code (kinds/telemetry/prompts files listed in its brief: bt_agent_models, bt_routing_policy, bt_role_routing,
bt_cli_delegate, bt_cli_accounts, bt_events, bt_efficiency, bt_runprompt, bt_context, bt_agents,
bt_scheduler_executor/prompt.py). Do NOT edit those.
You own: a new focused module (e.g. `bt_design_approval.py` + `bt_cli_design.py`), `bitacora.py` command registration,
`bt_rounds.py`, `bt_server.py`, `bt_page_req.py`, `bt_page_plans.py`, `bt_planstatus.py`, `bt_planblock.py`,
`bt_notify.py`, `bt_handoff.py`, `bt_scheduler_executor/{core_port,gates}.py` (+ executor README gate lines), the
owner composition/run modules only if the gate needs wiring, `bt_flow_bus.py` (≤500 lines), `bt_page_graph.py`,
`skill/references/modules.md`, `skill/references/plan-contract.md`, `pyproject.toml`, tests.

Implement, with fail-first tests (temp dirs, no real projects/schedulers):
1. Approval record: per requirement, a durable approval file (e.g. `<rdir>/design-approvals.json`, atomic writes) keyed
   by `<contract>@v<N>` with status approved|changes-requested, the approved blob sha256 (read from the repo at the
   contract path on the requested base/line, or the plan's repo HEAD — document which), who/via/when, comments.
   Immutable once approved; a new version needs its own approval. Mirror `bt_rounds.plan_decide` semantics.
2. CLI: `bitacora.py design list|show|approve|changes REQ-NNN [<contract>@vN] [--comments ...]` — list shows pending
   contracts for UI subplans whose design task is accepted; approve refuses if the contract file is absent.
3. Web: on the requirement page, a "Contratos de diseño" panel per UI subplan: contract rendered (markdown), version,
   preview link when `design.preview` is enabled, state, and Aprobar / Pedir cambios with comments (mirror the plan
   panel and its POST handling in bt_server.py; same CSRF/local-only protections the plan form has).
   "Pedir cambios" must send the design task back for a new contract version (use the existing M1 rework/redo
   public operation through the adapter; never mutate core state directly) — or, if that needs an M1 operation that
   does not exist, record changes-requested, keep UI tasks waiting and report the exact gap.
4. Gate: M3 starts a `ui:true` task only if the contract blob is in the base tree AND approved AND sha256 matches the
   approval; otherwise refuse with a classified blocked-environment/awaiting-owner Ack (`Ack.classification`, reason
   `DESIGN_CONTRACT_UNAPPROVED` or `DESIGN_CONTRACT_HASH_MISMATCH`) so no code-retry budget is spent and the task is
   re-tried when the approval lands. Legacy/non-UI tasks unchanged.
5. Visibility: plan status block, `/plans` page and Mermaid/graph show per UI subplan: contract@vN, approval state;
   flow bus maps approval events; `bt_notify` sends "Contrato de diseño esperando aprobación" once per version;
   `bt_handoff` adds an approval reason/notice when the plan has UI subplans (contracts will need owner approval).
6. Docs: modules.md (gate + approval), plan-contract.md (approval requirement), executor README gate lines.
Run: focused tests, executor + core module suites, web/server tests, full root suite.
