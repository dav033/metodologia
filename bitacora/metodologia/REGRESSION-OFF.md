# Integrations without regression (D-261)

Owner, 2026-10-31 17:05: until further notice metodologia integrations run no regression tests (`integrate.regression: none`). Every integration made that way is listed here, and so is every defect found later that a regression would have caught, to decide with evidence whether to turn regressions back on.

## Integrated without regression

- 2026-10-31 17:09 · `ccb1d77e4e50` · Integrations merge main into the branch and keep their turn; no regression until further notice, escaped defects recorded (D-260, D-261) · 3 path(s): skill/scripts/bt_config.py, skill/scripts/bt_integrate.py, skill/scripts/tests/test_integrate.py
- 2026-10-31 17:12 · `babb137e38fa` · Owner rejections carry images the agents open; a double-submitted rejection opens one P-item (D-258) · 16 path(s): pyproject.toml, skill/agents/planner.md, skill/agents/solver.md, skill/assets/planning-live.js, skill/assets/planning.css, skill/assets/verify-run.js …
- 2026-10-31 17:52 · `e2146bbcd7e8` · Iterating a direction after a plan change carries the delta; refusals keep the owner's text (D-263) · 5 path(s): skill/scripts/bt_design_amend.py, skill/scripts/bt_design_follow.py, skill/scripts/bt_design_iterate.py, skill/scripts/tests/test_design_amend.py, skill/scripts/tests/test_design_directions.py
- 2026-10-31 18:07 · `c87dd0e9a54f` · Durable: transitive readiness, retries catch up, UI contract gate, no-change and heap-limit classification (D-262) · 31 path(s): skill/scripts/bt_design_approval.py, skill/scripts/bt_design_web.py, skill/scripts/bt_durable/README.md, skill/scripts/bt_durable/adapters/briefs.py, skill/scripts/bt_durable/adapters/integration.py, skill/scripts/bt_durable/adapters/m3.py …
- 2026-10-31 18:10 · `7e8d4e638d7f` · bt_integrate --escaped needs no --branch/--title (D-264) · 2 path(s): skill/scripts/bt_integrate.py, skill/scripts/tests/test_integrate.py

## Escaped defects

- 2026-10-31 18:07 · merge `33d94f389` · test_durable_upgrade.test_a_run_started_by_the_previous_engine_continues_on_the_new_one fails on unmodified main ('reverify' unexpectedly found in the previous engine's request); introducing merge not bisected (observed at 33d94f389 by the D-262 subagent); the durable upgrade/replay suite would have caught it
