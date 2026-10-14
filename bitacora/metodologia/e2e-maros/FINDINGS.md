---
type: e2e-findings
project: metodologia
subject: first real project run on Maros (REQ-005, roles/permissions UX + admin MCP)
started: 2026-10-14
---
# E2E on Maros: findings (what is wrong or missing in the tool)

Format: `F-NN · severity (high/med/low) · where · what happened · proposed fix`. Observed facts only; fixes are proposals.

## Before launch
- F-01 · med · `handoff` risk gate · The gate is a keyword scan of SPEC/PLAN. A safety constraint that says "never touch production" and an out-of-scope line mentioning "billing" or "notify users" force `needs_approval`, exactly as a risky plan would. · Proposal: ignore matches inside "Out of scope" and "Constraints" sections, or require the keyword in a task line, and show the matched sentence.
- F-02 · high · `handoff` / `launch` · Neither exposes `--isolation`; only `run` does and the default is `run.isolation=off`. A plain `handoff` therefore runs sessions directly in the registered repo path. `maros-next` has 213 uncommitted files of the owner's own work; unattended sessions would write into that tree. · Proposal: `handoff` should refuse (or default to worktree) when a target repo is dirty or on a feature branch, and accept `--isolation`.
- F-03 · med · `req new` · Leaves SPEC in `status: clarifying`; the HQ must flip it by hand. · Proposal: a `spec ready` command or auto-flip when the plan is written.
- F-04 · low · workspace hints · `workspace show` prints `hint: ~/maros-next` while the repos are in `~/dev/maros/...`; the real paths come from another resolver, so the output misleads. · Proposal: print the resolved path.
- F-05 · med · base selection · Both repos are on feature branches with unmerged work (`feat/req-003-...`, `feat/req-001-...`); there is no prompt or flag to pick the base branch for the worktrees, so the new work would be based on whatever is checked out. · Proposal: `--base <branch>` and a warning that names the branch.
