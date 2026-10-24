# Task DZ-fix — security and correctness repairs from independent review of the Designer integration

Read first, binding: `/home/david/dev/.designer-wt/RULES.md`, `CONTEXT.md` (D-127). Worktree `dz/INT` at `e74dbbe7d`
(path `/home/david/dev/.designer-wt/DZ-approval`); commit on top. You may edit any file needed for these fixes
(web assets, server, page modules, design approval/web/CLI modules, notify, planstatus, tests); keep modules < 500
lines (`bt_server.py` 551 and `bt_page_plans.py` 632 are already over: do not grow them — move code out if you touch them).
Each fix starts with a failing test.

1. [high, security] Agent-authored markdown is rendered as raw HTML on the dashboard origin (`skill/assets/app.js:7`
   `target.innerHTML = marked.parse(src)`, marked 4.3.0 without sanitizer; no CSP on normal pages, `bt_server.py:~74`
   only for sandboxed .html). A contract (or PLAN.md, SPEC.md — any agent-written doc) containing
   `<img src=x onerror=...>` runs script that can read the CSRF `token` input and POST an approval (contract or plan),
   bypassing D-127. Fix both layers: (a) render markdown with raw HTML disabled/escaped (e.g. a marked renderer that
   escapes `html` tokens, or escape before parse) for every markdown view; (b) send a CSP on all dashboard pages that
   forbids inline/event-handler scripts (`script-src 'self'`; move any inline script to static files). Test: a markdown
   doc with an onerror payload renders inert; CSP header present on page responses.
2. [high] Approval pins the blob at `git show HEAD:path`, but the page shows the working-tree file (and follows
   symlinks) (`bt_design_approval.decide` vs `bt_page_req.py:~131`). Render the contract from exactly the bytes that are
   hashed (`git show <rev>:path`), show the sha256 next to Aprobar, and submit that sha256 with the form; `decide`
   refuses if the submitted digest differs from the blob it would pin (stale page), if the path is a symlink in the tree,
   or if the working tree has the contract dirty. Use the same revision rule the gate uses (document which: the repo
   line/branch the UI tasks will start from); if the design task's repository differs from the ui:true tasks'
   repository, refuse with a clear error instead of pinning a hash the gate cannot match.
3. [medium] Duplicate DOM id `doc`: each contract uses `md("doc", …)` (`bt_page_req.py:~132`) colliding with the plan
   view; contracts never render and the plan view is overwritten. Use unique ids per contract.
4. [medium] `DesignApprovalError` escapes `bt_server.py` do_POST (only SystemExit handled) → dropped connection. Return
   a 400 page with the message like the plan form does.
5. [medium] The "contrato esperando aprobación" notification fires only on a GET render (`bt_page_req.py:144`). Move
   the trigger to where design-task completion is observed (scheduler task-event notifications / plan-status refresh
   path), keep the O_EXCL claim dedupe per version; a page render must not consume it.
6. [low] Approve must require the design task to be completed (as `list` already does) — refuse a draft.
7. [low] `decide` read-check-write on `design-approvals.json` without a lock under ThreadingHTTPServer: take an
   `fcntl` lock around the whole decision (POSIX; keep a safe fallback).
8. [low] `_release_ui_holds` reopens every ui:true task blocked with `blocked_environment`: only reopen tasks whose
   block reason is DESIGN_CONTRACT_UNAPPROVED/HASH_MISMATCH for THIS contract.
9. [low, test gap] Add one scheduler-level test of the real chain: ui:true start rejected (unapproved) → task held
   without spending code-retry budget → owner approval → task becomes ready and starts.
Run: design/web/gate/contract-notes/prompt tests, executor + core module suites, full root suite (3 P-189 known).
Logs under /home/david/dev/.designer-wt/.
