STATUS: PARTIAL
SUMMARY: Added `design` to kind inference, tier policy, CLI choices, routing hints, and context.
Designer routing follows the existing role policy and does not require provider independence.
Added prompt rules and tests for design, UI implementation, and visual review when contract metadata is supplied.
The scheduler `Brief` and adapter do not currently provide that metadata, so live prompts cannot yet include the declared contract path/version.
Committed as `325b8b6d8258e4208f25dffd83e44a58ce6ca3ec`.
CHANGES:
skill/scripts/bt_agent_models.py — added `design` kind and UI-related inference patterns.
skill/scripts/bt_routing_policy.py — added the design tier ceiling.
skill/scripts/bt_cli_delegate.py, skill/scripts/bt_cli_accounts.py — enabled `--kind design`.
skill/scripts/bt_runprompt.py — added `design` and `designer` to delegate hints.
skill/scripts/bt_context.py — documented Designer, owner approval, and configurable `design.preview`.
skill/scripts/bt_scheduler_executor/prompt.py — added conditional Designer, UI implementer, and visual review instructions.
skill/scripts/bt_scheduler_executor/README.md — documented the prompt behavior.
skill/scripts/tests/test_agents.py, skill/scripts/tests/test_role_routing.py, skill/scripts/tests/test_handoff.py, skill/scripts/tests/test_run_units.py, skill/scripts/bt_scheduler_executor/tests/test_prompt.py — added coverage for kinds, routing, context, hints, telemetry aggregation, and prompt rules.
VERIFICATION: `python -m unittest discover -s tests -p 'test_agents.py'` → 0, 42 tests (0.19s); `test_role_routing.py` → 0, 23 tests (0.19s); `test_handoff.py` → 0, 14 tests (1.01s); `test_run_units.py` → 0, 3 tests (0.00s); executor `test_prompt.py` → 0, 8 tests (1.02s)
VERIFICATION: `python -m unittest discover -s bt_scheduler_executor/tests` → 0, 302 tests (335.865s)
VERIFICATION: `python -m unittest discover -s tests` → 1, 2,541 tests, 18 failures, 6 skipped (1,311.916s): 15 documented baseline migration failures plus 3 documented low-disk recovery benchmark failures; no additional failures.
COMMITS: 325b8b6d Add design kind and Designer routing prompts
PROVENANCE:
CONCERNS: Completing live prompt metadata requires changes to `bt_scheduler_executor/model.py` and `bt_scheduler_executor_adapter.py`, which are outside my assigned ownership. The prompt supports the required metadata, but those fields are not currently supplied by the scheduler. `/home` had 3.9 GiB free during root verification.