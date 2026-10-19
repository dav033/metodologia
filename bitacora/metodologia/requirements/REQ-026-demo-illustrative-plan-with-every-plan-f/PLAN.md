---
req: REQ-026
status: in-progress
created: 2026-10-18
demo: true
---
# Plan — REQ-026 — DEMO — Illustrative plan with every plan feature (test only)

> **DEMO.** This plan is a sample made to show what the plans pages can display. Nothing in it is a real work item,
> its run state is simulated and no agent will ever execute it. Delete it from the plans page when it is no longer needed.

## Approach
Add a light and dark token layer with a manual override and a health line on the plan cards, in four milestones: understand, build, verify, close out. The scenario is invented; the files named in each task are real, so the evidence checks pass. The run is paused with nine tasks in five different states: completed, completed after a retry, running, blocked after two attempts on different accounts, and pending.

## Global constraints
- Read-only demo: no task may be launched, approved or frozen from this plan.
- Keep the tokens as the single source of color; no page may add a literal color.
- The owner's theme choice never leaves the browser.

## Tasks

### M1 — Understand the current UI
- [x] T1 — Inventory the color tokens and the places that hard-code colors · repo: skill · files: `skill/assets/style.css`, `skill/scripts/bt_page_plans.py` · risk: low · verify: `grep -c "var(--" skill/assets/style.css`
- [x] T2 — Research how the page can follow the system theme and keep a manual choice · repo: skill · files: `skill/scripts/bt_server.py` · risk: low · verify: `grep -q static skill/scripts/bt_server.py`

### M2 — Build the theme and the plan health badge
- [x] T3 — Add the light and dark token layer with a manual override attribute · repo: skill · files: `skill/assets/style.css`, `skill/scripts/bt_pages.py` · after: T1 · risk: medium · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_page_plans`
- [ ] T4 — Show progress and blocked work on each plan card · repo: skill · files: `skill/scripts/bt_page_plans.py`, `skill/scripts/tests/test_page_plans.py` · after: T1 · risk: medium · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_page_plans`
- [ ] T5 — Keep the owner's theme choice between sessions · repo: skill · files: `skill/scripts/bt_pages.py`, `skill/scripts/bt_server.py`, `skill/assets/style.css` · after: T2, T3 · risk: high · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_page_plans`
- [ ] T6 — Check contrast of every badge and chip in both themes · repo: skill · files: `skill/assets/style.css` · after: T5 · risk: low · verify: `grep -q -- --accent skill/assets/style.css`

### M3 — Verify the result
- [ ] T7 — Add regression tests for the token layer and the health line · repo: skill · files: `skill/scripts/tests/test_page_plans.py` · after: T3, T4 · risk: medium · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_page_plans`
- [ ] T8 — Independent audit of the M2 changes against the spec · repo: skill · files: `skill/assets/style.css`, `skill/scripts/bt_page_plans.py`, `skill/scripts/bt_pages.py`, `skill/scripts/bt_server.py`, `skill/scripts/tests/test_page_plans.py` · after: T6, T7 · risk: high · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_page_plans`

### M4 — Close out
- [ ] T9 — Update the documentation and the bitácora · repo: skill · files: `skill/references/documentation.md` · after: T8 · risk: low · verify: `grep -q web skill/references/documentation.md`

## Verification
Run the page tests (`test_page_plans`) after each build task, then the independent audit in T8. The demo's own checks are `echo` placeholders where a real check would need a browser.

## Rulings
- T2: the choice is stored in the browser, not on the server, because the web UI has no user accounts; cost if wrong: low.
- T5: confidence stays low until T2's assumption about browser storage is confirmed; the two blocked attempts record why.
