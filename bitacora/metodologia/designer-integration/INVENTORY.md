# Designer gap inventory (explorer, 2026-10-24; paths relative to skill/)

## Docs
- references/interface-quality.md:3-5 says "adds no approval gate, mandatory design file" — contradicts plan-contract.md:87-89. Rewrite: with UI subplans the contract and owner approval are mandatory; this file is the guidance Designer and Reviewer apply.
- references/requirements.md — no design/ui/visual: add UI-detection + visual-direction question in the interview, a UI-scope section in the spec, and that the plan carries a design task + owner contract approval (§8 handoff too).
- templates/SPEC.md, templates/PLAN.md — add optional "UI / design contract" spec section; PLAN task-line comment lacks `kind:`, `subplan:`, `ui:` and the `design` kind; add design + visual-review example lines.
- references/execution.md (§1c ~60, ~192 role list) — add "UI subplans" paragraph (design → approval → ui implement → visual review → audit; DESIGN_CONTRACT_MISSING / awaiting approval) and `designer` in the role list.
- references/agent-orchestration.md — add Designer, its design/-only scope and the serial dependency.
- references/agents.md:~6-23 role policy table lacks a Designer row (Opus high, Sol high).
- references/subagents.md:~103 — add a design-task brief example and the "implementer reads the contract" rule.
- references/documentation.md — add design/contracts/ as a project artifact, contract changelog and optional preview.
- references/engineering.md — "done" checklist: UI contract conformance + Reviewer visual axis.
- references/modules.md:186-196, SKILL.md (HQ/plan-approval text) — mention the contract approval step once it exists.
- architecture-audit.md (UI inventory includes design/contracts), tools.md (design preview server if enabled) — low priority.

## Prompts
- agents/planner.md:48 — ensure task-classification examples include `kind: design`.
- agents/runner.md — owns visual evidence capture (screenshots per breakpoint × state, evidence ids) for the Reviewer visual axis; reviewer.md:67 references screenshot evidence ids.
- agents/explorer.md (look for design/contracts/ on UI questions), agents/antagonist.md (contract drift is a finding), researcher.md — low priority.
- scripts/bt_runprompt.py:72 delegate hint lists --kind/--role without design/designer.

## Code
- scripts/bt_agent_models.py:8 KINDS lacks `design`; infer_kind (51-69) — add design + word patterns; check bt_routing_policy.MAX_KIND_TIER.
- scripts/bt_cli_delegate.py:16, scripts/bt_cli_accounts.py:20 --kind choices lack design.
- scripts/bt_events.py (75, 289, 384, 399, 536), scripts/bt_efficiency.py:63 — missing kind defaults to implement; add design buckets.
- scripts/bt_role_routing.py:108 avoid-provider list ('reviewer','antagonist') — decide designer (independence from implementer provider is NOT required; Designer is a producer).
- scripts/bt_planstatus.py:125,162, bt_planblock.py, bt_page_plans.py, Mermaid diagram — show contract/version and design-gate/approval state for UI subplans.
- scripts/bt_handoff.py:149-169 approval reasons — add a reason when the plan has UI subplans (owner will approve contracts during the run).
- scripts/bt_notify.py — notification "design contract awaiting approval".
- scripts/bt_scheduler_executor/prompt.py:44-45 — design and ui:true tasks get contract path, version, approval state and "read the contract" / design-scope instructions.
- scripts/bt_context.py:18-32,60, bt_agents.brief() — one-liner that Designer exists and design.preview is configurable.
- scripts/bt_config.py:106 design {preview, preview_projects} — no approval key needed (owner approval is always required).
- scripts/bt_page_review.py, bt_page_req.py — contract view + preview link + approval form on the requirement page.
- scripts/bt_flow_bus.py, bt_page_graph.py — render design tasks/approval in the flow/graph.

## Approval mechanism today
- Plan: CLI `bitacora.py plan approve|changes|review|wait REQ-NNN` (bitacora.py:91); web bt_page_req.py:~101-113 form posts `plan` → bt_server.py:299,349-352 → bt_rounds.py:118 plan_decide (status line in PLAN.md, front-matter status, validate + freeze). bt_launch.py:63-65 requires approved; bt_handoff.py:168-217 auto-approve or hold.
- Design contracts: only core_port.py:53 DESIGN_CONTRACT_MISSING on blob absence. No approved flag/hash/owner sign-off.
