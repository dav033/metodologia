STATUS: DONE

SUMMARY:
Agent-authored markdown is rendered with raw HTML escaped, and dashboard responses carry a CSP with `script-src 'self'`; inline scripts now load from static assets.
Contract approvals display and submit the SHA256 of the `HEAD` blob. Approval checks the clean regular-file blob, completed design task, matching UI-task repository, and submitted digest; decisions are locked.
Design notices now fire when the scheduler observes completion. Approval only releases UI tasks held for this contract; a scheduler-level test covers rejection, zero retry-budget use, owner approval, and successful start.
Worktree is clean on `dz/INT`.

CHANGES:
`bt_design_approval.py`, `bt_design_web.py`, `bt_cli_design.py` — blob pinning, completion/repository checks, locking, and scoped hold release.
`bt_page_req.py`, `bt_pages.py`, `bt_page_plans.py`, `bt_server.py`, `skill/assets/*` — inert markdown rendering, CSP, external scripts, unique contract IDs, and displayed digests.
`bt_scheduler_run.py`, `bt_scheduler_core/dispatch.py` — scheduler completion notices and explicit environment-hold reasons.
`skill/scripts/tests/*` — regression, HTTP, and scheduler-chain coverage; theme tests updated for external script loading.

VERIFICATION:
`PYTHONPATH=skill/scripts python -m unittest …` focused design/web/gate/contract-notes/prompt suite → exit 0 (112 tests, 22.0s).
`python -m unittest discover -s bt_scheduler_executor/tests` → exit 0 (303 tests, 295.6s).
`python -m unittest discover -s bt_scheduler_core/tests` → exit 0 (333 tests, 53.0s).
`python -m unittest discover -s tests` → exit 1 (2,591 tests, 1,098.3s; 18 failures, 6 skipped: 15 documented baseline failures and 3 P-189 disk-space failures; no other failures).
`git diff --check` and `py_compile` on changed Python modules → exit 0.
Logs: `/home/david/dev/.designer-wt/logs/DZ-fix-focused-final.log`, `DZ-fix-executor-module.log`, `DZ-fix-core-module.log`, `DZ-fix-root-final-final.log`.

COMMITS:
`109dd5a9` fix(design): harden dashboard markdown and approvals
`9d304d6a` test(design): keep scheduler gate fixture behind adapter
`7dfa5ee8` test(web): expect the external theme script

PROVENANCE:
None.

CONCERNS:
The 3 P-189 failures occurred with 2.9 GiB free on `/home`, below the documented 5 GiB threshold.