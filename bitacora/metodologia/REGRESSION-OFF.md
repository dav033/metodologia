# Integrations without regression (D-261)

Owner, 2026-10-31 17:05: until further notice metodologia integrations run no regression tests (`integrate.regression: none`). Every integration made that way is listed here, and so is every defect found later that a regression would have caught, to decide with evidence whether to turn regressions back on.

## Integrated without regression

- 2026-10-31 17:09 · `ccb1d77e4e50` · Integrations merge main into the branch and keep their turn; no regression until further notice, escaped defects recorded (D-260, D-261) · 3 path(s): skill/scripts/bt_config.py, skill/scripts/bt_integrate.py, skill/scripts/tests/test_integrate.py
- 2026-10-31 17:12 · `babb137e38fa` · Owner rejections carry images the agents open; a double-submitted rejection opens one P-item (D-258) · 16 path(s): pyproject.toml, skill/agents/planner.md, skill/agents/solver.md, skill/assets/planning-live.js, skill/assets/planning.css, skill/assets/verify-run.js …
- 2026-10-31 17:52 · `e2146bbcd7e8` · Iterating a direction after a plan change carries the delta; refusals keep the owner's text (D-263) · 5 path(s): skill/scripts/bt_design_amend.py, skill/scripts/bt_design_follow.py, skill/scripts/bt_design_iterate.py, skill/scripts/tests/test_design_amend.py, skill/scripts/tests/test_design_directions.py
- 2026-10-31 18:07 · `c87dd0e9a54f` · Durable: transitive readiness, retries catch up, UI contract gate, no-change and heap-limit classification (D-262) · 31 path(s): skill/scripts/bt_design_approval.py, skill/scripts/bt_design_web.py, skill/scripts/bt_durable/README.md, skill/scripts/bt_durable/adapters/briefs.py, skill/scripts/bt_durable/adapters/integration.py, skill/scripts/bt_durable/adapters/m3.py …
- 2026-10-31 18:10 · `7e8d4e638d7f` · bt_integrate --escaped needs no --branch/--title (D-264) · 2 path(s): skill/scripts/bt_integrate.py, skill/scripts/tests/test_integrate.py
- 2026-10-31 19:04 · `89b1a87f120f` · One source per test variable; dead test resources stop the start, not an attempt (D-265) · 14 path(s): skill/scripts/bt_config.py, skill/scripts/bt_durable/README.md, skill/scripts/bt_durable/adapters/agent_env.py, skill/scripts/bt_durable/adapters/m3.py, skill/scripts/bt_durable/control/classify.py, skill/scripts/bt_durable/execution/steps.py …
- 2026-10-31 19:11 · `81138e36582c` · Every role session runs the model its role policy names; no route hard-codes Opus (D-267) · 3 path(s): skill/scripts/bt_agent_terminal.py, skill/scripts/bt_durable/solver.py, skill/scripts/tests/test_planner_account.py
- 2026-10-31 19:31 · `8386b0a6fe48` · Attempt worktrees removed once captured; disk floor before a start or a check (D-266) · 13 path(s): skill/scripts/bt_config.py, skill/scripts/bt_durable/README.md, skill/scripts/bt_durable/adapters/m6.py, skill/scripts/bt_durable/cli.py, skill/scripts/bt_durable/control/classify.py, skill/scripts/bt_durable/execution/steps.py …
- 2026-10-31 19:33 · `bec779163d30` · A rejected subplan version shows where its correction is (D-268) · 9 path(s): skill/assets/planning.css, skill/scripts/bt_live_api.py, skill/scripts/bt_page_correction.py, skill/scripts/bt_page_now.py, skill/scripts/bt_page_planning.py, skill/scripts/bt_page_verification.py …
- 2026-10-31 19:53 · `2e6ae4e7cfde` · A republished older version does not end a rejected subplan's correction (D-268) · 5 path(s): skill/scripts/bt_live_api.py, skill/scripts/bt_page_verification.py, skill/scripts/bt_subplan_status.py, skill/scripts/bt_verification_correction.py, skill/scripts/tests/test_verification_correction.py

## Escaped defects

- 2026-10-31 18:07 · merge `33d94f389` · test_durable_upgrade.test_a_run_started_by_the_previous_engine_continues_on_the_new_one fails on unmodified main ('reverify' unexpectedly found in the previous engine's request); introducing merge not bisected (observed at 33d94f389 by the D-262 subagent); the durable upgrade/replay suite would have caught it
- 2026-10-31 19:35 · merge `bec779163` · D-268 rejected-phase showed no label on live: rows are outdated+retest after a rejection; only an end-to-end check on live data would have caught it
