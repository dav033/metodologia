# Designer integration — shared context for all tasks (owner-approved plan, 2026-10-24)

Goal: the `designer` role (skill/agents/designer.md + skill/agents/designer/skills/*) must be integrated 100% in the
methodology flow, visible and invisible. The engine already knows it: Planner plans a `design` task per UI subplan
(schema 1.3.0 `subplans[].ui {contract, version, design_task, visual_review_task}`), `bt_role_policy.py` routes kind
`design` → `designer`, `bt_design_scope.py` limits its writes to `design/`, the M3 gate
(`bt_scheduler_executor/gates.py`, `core_port.py:~53`) requires `design/contracts/<c>@vN.md` in the base tree before
`ui:true` tasks, Reviewer has a `visual` axis. Missing: human flow, docs, templates, CLI/telemetry kinds, approval.

Owner decisions (metodologia D-127):
1. The OWNER approves every design contract version (v1 and each later vN) before any `ui:true` task starts, from the
   web requirement page or CLI `bitacora.py design approve|changes REQ-NNN <contract>@vN`, mirroring plan approval
   (`bt_rounds.plan_decide`, `bt_page_req.py` plan panel, `bt_server.py`). Approval pins the contract blob sha256.
2. The M3 gate requires: contract present in the base tree AND approved AND the approved hash equals the blob. Missing
   approval holds UI tasks as a blocked/waiting state (attention: awaiting owner contract approval) — never a failure,
   never spending code-retry budget; approval releases them.
3. The Runner captures visual evidence (screenshots per breakpoint × state) for the Reviewer `visual` axis.
4. Plans without UI subplans: zero behaviour change.

Ordering inside a UI subplan: design task → owner contract approval → ui:true implement tasks → visual review → audit.
Inventory of gaps (explorer, 2026-10-24) is in /home/david/dev/.designer-wt/INVENTORY.md.
