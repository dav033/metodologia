STATUS: DONE

SUMMARY: Aye, added durable, immutable approval records for versioned design contracts, plus CLI and web approval workflows.  
M3 now blocks UI tasks when approval is missing or the contract hash differs; status, graph, notifications, and handoff expose pending approvals.  
Updated the design guidance, plan contract, and executor gate documentation. Committed on `dz/DZ-approval`; working tree is clean.

CHANGES:

skill/scripts/bt_design_approval.py — stores approvals atomically and checks contract hashes against repository trees.

skill/scripts/bt_cli_design.py, skill/scripts/bt_design_web.py, skill/scripts/bt_page_req.py, skill/scripts/bt_server.py — add CLI and web approval flows, comments, and preview links.

skill/scripts/bt_scheduler_executor/core_port.py, skill/scripts/bt_scheduler_executor/gates.py, skill/scripts/bt_scheduler_executor_wiring.py — gate UI task starts on approval and hash match.

skill/scripts/bt_planstatus.py, skill/scripts/bt_planblock.py, skill/scripts/bt_page_plans.py, skill/scripts/bt_page_graph.py, skill/scripts/bt_page_design.py, skill/scripts/bt_design_flow.py, skill/scripts/bt_flow_bus.py — expose per-contract approval state.

skill/scripts/bt_notify.py, skill/scripts/bt_handoff.py — notify about pending approvals and include approval in handoff reasons.

skill/scripts/bitacora.py, pyproject.toml, skill/scripts/bt_agent_models.py, skill/scripts/bt_agents.py, skill/scripts/bt_cli_accounts.py, skill/scripts/bt_cli_delegate.py, skill/scripts/bt_context.py, skill/scripts/bt_runprompt.py — register the design task kind and CLI wiring.

skill/references/modules.md, skill/references/plan-contract.md, skill/scripts/bt_scheduler_executor/README.md, skill/SKILL.md, skill/agents/, skill/references/, skill/templates/ — document approval requirements and workflow.

skill/scripts/tests/ — add approval, gate, web, notification, status, flow, and task-kind coverage; update owner E2E fixtures to include valid approval.

VERIFICATION:

`python -m unittest tests.test_design_approval tests.test_design_web tests.test_m3_subplan_gates tests.test_notify_tasks tests.test_flow_bus tests.test_planstatus tests.test_handoff` → exit 0 (63 tests, 7.606 s)

`python -m unittest tests.test_design_web` → exit 0 (3 tests, 0.132 s)

`python -m unittest tests.test_scheduler_owner_e2e_subplans` → exit 0 (9 tests, 429.485 s)

`python -m unittest discover -s bt_scheduler_executor/tests` → exit 0 (301 tests, 315.280 s)

`python -m unittest discover -s skill/scripts/bt_scheduler_core/tests` → exit 0 (333 tests, 59.313 s)

`python -m unittest discover -s tests` → exit 1 (2,555 tests, 1,164.462 s; 18 failures, 6 skips). The 18 failures are the 15 baseline failures listed in `RULES.md` plus 3 recovery benchmark failures with 3.9 GiB free on `/home` (below the documented 5 GiB threshold). No other failures remained.

`git diff --check` → exit 0.

COMMITS: 3d581e3a3e28363c5f4661462df653e12e578942 feat(design): require owner approval for UI contracts

PROVENANCE: None.

CONCERNS: The root suite exits nonzero for the documented baseline and disk-space failures. No push or merge was performed.