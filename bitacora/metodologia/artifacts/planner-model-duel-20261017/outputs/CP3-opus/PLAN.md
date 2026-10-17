---
status: draft
---
# REQ-CP3 — Show the PLAN.json quality summary where the plan is reviewed (DRAFT, revision 1)

Draft for owner review. Nothing here is approved, frozen or launched. No commands were run while planning, and every estimate is a guess with no comparable execution history behind it.

## Scope
- **Goal (SPEC.md):** when the owner reviews a plan, they should see its critical path, widest level and low-confidence tasks. Today `bt_planner report` only exposes these through a module command.
- **In scope:** R1 terminal summary through the adapter (`bitacora.py plan-json report REQ-NNN`); R2 summary block on the web **Plan** tab when `PLAN.json` exists; R3 plans without `PLAN.json` render byte-for-byte as before.
- **Out of scope:** changing `bt_planner` analysis (`quality.analyze`); changing the approval or launch gates (`publishable_problem`, `launch_problem`); the post-execution **Revisar** tab (`bt_page_review.py`); changing `bitacora.py plan review` output (see D3); any scheduling or provider choices.

## Inspected findings (provenance)
1. **R1 appears to work already, but nothing tests its output.** `skill/scripts/bt_cli_plan.py:15` accepts `report`. `adapter.run_cli` forwards it to `planner_cli.run` (`skill/scripts/bt_plan_adapter.py:98-102`). The `report` branch prints `json.dumps(quality.analyze(plan))` after a `pc.validate` gate, and an invalid or missing PLAN.json gets exit 2 and `INVALID` (`skill/scripts/bt_planner/cli.py:97-104`). `skill/scripts/tests/test_plan_integration.py:220` checks only the exit code, not the content.
2. **`quality.analyze` already returns the values R2 needs:** `critical_path {tasks, minutes}`, `widest_level` and `low_confidence` (`skill/scripts/bt_planner/quality.py:184-232`). `bt_planner/__init__.py` does not re-export `quality`. The adapter already imports submodules this way (`from bt_planner import cli`).
3. **The web plan review page is `plan_panel`** in `skill/scripts/bt_page_req.py:99-115`. It renders `md("doc", read(plan)) + form` and is reached from `req_page` tab `plan` (`bt_page_req.py:36-38`), which is served by `bt_server.py:112`. Approval goes through `bt_rounds.plan_decide` (`bt_rounds.py:116-133`). The terminal review is `bitacora.py plan review|approve` (`bt_cli_flows.py:52-63`).
4. **Boundary rule:** only `bt_plan_adapter.py` (plus listed tests) may import `bt_planner`. Even a string constant starting with `bt_planner` in another file fails `skill/scripts/tests/test_plan_boundary.py:38-60`. So the page must use the adapter.
5. **The adapter's full `check` is too heavy for a page render.** It uses `repo_roots`/`ref_verifier`, which can spawn `git` subprocesses (`bt_plan_adapter.py:39-95`).
6. **No test exists for `bt_page_req`.** Page tests elsewhere call the page function directly and assert on the HTML (`skill/scripts/tests/test_metrics_page.py`). `skill/scripts/tests/` is not a package, so the commands use `discover -p`.

## Decision gates, assumptions, unknowns
- **D1 (product, recommended):** the web summary uses the same structural gate as `plan-json report` (`pc.validate`), not the full `check`. That keeps the terminal and web consistent with each other and keeps the page free of subprocesses. Alternative: full `check` (slower, needs the repository). T2 follows D1.
- **D2 (product, recommended):** if PLAN.json exists but is invalid or unreadable, the Plan tab shows a warning with at most 5 errors and the hint `bitacora.py plan-json check REQ-NNN`, and the plan prose still renders. Alternative: hide the block silently. T3 follows D2.
- **D3 (product, assumption):** "in the terminal" is met by R1 alone. `bitacora.py plan review` output (`{plan, url}` JSON) stays unchanged. If the owner wants the summary there too, a new requirement and task are needed.
- **A1:** the summary shows for any plan status whenever PLAN.json exists, because R2 has no status condition.
- **A2:** UI labels are in Spanish, like the rest of `bt_page_req.py`.
- **A3:** "exactly as before" (R3) means byte-identical HTML from `plan_panel` and `req_page(tab="plan")` when PLAN.json is absent, for every status.
- **Unknown:** whether the owner also wants the other analysis fields shown, such as distributions and `without_command_verification`. Kept out of scope.

## Milestones and tasks

### M1 — Adapter summary contract
Acceptance: `plan-json report` output is locked by tests, and `adapter.quality_summary` follows IF-1 for the legacy, valid and invalid cases.
- [ ] T1 — Lock the plan-json report CLI output · repo: repository · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_integration.py` · files: skill/scripts/tests/test_plan_integration.py · covers: R1 · kind: test
- [ ] T2 — Add adapter quality_summary for display · repo: repository · after: T1 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_boundary.py` · files: skill/scripts/bt_plan_adapter.py, skill/scripts/tests/test_plan_integration.py · resources: plan-quality-summary-contract · covers: R2, R3 · kind: implement

### M2 — Plan tab summary
Acceptance: the Plan tab shows critical path, widest level and low-confidence tasks for a valid PLAN.json, a warning for an invalid one, and unchanged HTML without one.
- [ ] T3 — Render the summary block in plan_panel · repo: repository · after: T2 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_review_page.py` · files: skill/scripts/bt_page_req.py, skill/scripts/tests/test_plan_review_page.py · resources: plan-quality-summary-contract · covers: R2, R3 · kind: implement
- [ ] T4 — Integration and regression check of the Plan tab · repo: repository · after: T3 · verify: `cd skill/scripts && python3 -m unittest discover -s tests` · files: skill/scripts/tests/test_plan_integration.py · resources: plan-quality-summary-contract · covers: R1, R2, R3 · kind: test

### M3 — Documentation
Acceptance: the plan-contract reference says where the owner sees the summary (terminal and web).
- [ ] T5 — Document where the summary is shown · repo: repository · after: T4 · files: skill/references/plan-contract.md · covers: R1, R2 · kind: docs

Dependencies: T1 → T2 → T3 → T4 → T5. The order is strictly linear because T1, T2 and T4 all edit `test_plan_integration.py`, and T3 and T4 consume IF-1.

## Task behavior

**T1 (R1).** Add Cli cases to `test_plan_integration.py`:
- For a valid plan (`good_plan()`), `dispatch(report)` stdout is valid JSON with `critical_path.tasks` (list), `critical_path.minutes` (int), `widest_level` (int) and `low_confidence` (list).
- With no PLAN.json, exit is 2 and output contains `INVALID`.

If either fails, fix only the plumbing in `bt_cli_plan.py` or `bt_plan_adapter.run_cli`. Do not touch module analysis.

**T2 (IF-1 producer).** `quality_summary(rdir) -> None | dict`:
- (1) If `rdir/PLAN.json` does not exist, return `None` and do no other I/O.
- (2) Read it with the planner reader. Unreadable, a non-object, or `validate` errors → `{"ok": False, "errors": [<=5 strings]}`.
- (3) Valid → `{"ok": True, "summary": quality.analyze(plan)}`, identical to the `plan-json report` JSON (D1).
- (4) Any unexpected exception → `{"ok": False, "errors": ["PLAN.json could not be summarised (<ExcType>)"]}`. It never raises.
- It never writes, never calls `repo_roots`/`ref_verifier`/subprocess, and leaves existing adapter functions unchanged. This is display only, not a gate.
- Add tests for the three states and a parity test: `summary == json.loads(report stdout)`.

**T3 (IF-1 consumer).**
- First, add a characterization test in the new `tests/test_plan_review_page.py`. It captures the current `plan_panel` HTML for statuses `draft`, `review` and `approved` without PLAN.json, using a temporary `PLAN.md`.
- Then change `plan_panel` to call `bt_plan_adapter.quality_summary(plan.parent)`:
  - `None` → return exactly the previous string (R3).
  - `ok` → insert a block before the form with critical path task IDs joined by `→` plus minutes, widest level, and low-confidence IDs (or `ninguna`).
  - not ok → warning per D2.
- HTML-escape every value with `e()`.
- Page tests patch the adapter. Keep the signatures of `plan_panel` and `req_page`. No string in this file may start with `bt_planner`.

**T4.** Add to `test_plan_integration.py`:
- With the real adapter and `good_plan()`, `plan_panel` output contains the critical-path IDs and the widest-level value from `json.loads(report stdout)`.
- A skeleton (invalid) PLAN.json gives the warning.
- No PLAN.json leaves the HTML unchanged.

Then run the full `skill/scripts/tests` suite and a manual product check on the local web UI.

**T5.** Add one or two sentences near `plan-json report` in `skill/references/plan-contract.md`. They should say that the web Plan tab shows critical path, widest level and low-confidence tasks when PLAN.json exists, and that the summary is not an approval verdict.

## Verification (planned, none executed)
- Static: `test_plan_boundary.py` (adapter-only import) after T2 and T3.
- Functional: T1 CLI cases; T2 adapter state tests; T3 page tests (new file created by T3).
- Integration: T4 real adapter → page, plus report/summary parity.
- Regression: full `python3 -m unittest discover -s tests` from `skill/scripts`; T3 golden HTML for R3.
- Product: manual check of the Plan tab with and without PLAN.json. A passing test is not product acceptance.

## Risks
- **Plausible risk:** a page change alters legacy HTML, breaking R3. Mitigation: the T3 characterization test is written first.
- **Plausible risk:** a string that starts with `bt_planner` in page code trips the boundary test (`test_plan_boundary.py:55-58`). Mitigation: T2 and T3 verify with that test.
- **Plausible risk:** an invalid PLAN.json raises inside the page and breaks the review tab. Mitigation: T2 never raises.
- **Fact:** R1 behaviour already exists (`bt_planner/cli.py:97-104`). T1 is mostly a regression lock, not new behaviour.

## Self-review note
I reviewed this plan against the code myself in the same session. That is not an independent approval, and host validation runs after capture.
