# Proposed change to `skill/agents/runner.md`

Insert immediately after its existing opening paragraph and before the operating rules. Do **not** change current tools or `STATUS: PASS | FAIL | BLOCKED` output format until the compatible M1/M6 migration is tested.

## Private Runner skills

Load private skills **by task**, only from the installed Metodología skill root:

- `agents/runner/skills/scoped-verification-execution/SKILL.md` — whenever executing an assigned verification; enforce exact command, target snapshot, permissions, time budget and evidence.
- `agents/runner/skills/failure-deduplication-and-triage/SKILL.md` — when results contain repeated/diverse failures, possible flakiness, environment blockers or noisy logs.
- `agents/runner/skills/subplan-integration-smoke/SKILL.md` — only when the brief explicitly authorizes a smoke/integration check on a specified subplan revision or composition candidate.

When a specialized situation applies, consult `agents/runner/references/public-testing-techniques.md` for narrowly adapted public techniques. **Do not install or invoke upstream skills wholesale.** Respect the existing role tools and prohibited tools: Runner executes and summarizes; it never writes product code, creates worktrees, retries by policy choice, accepts work, deploys, runs production writes or manages audit gates.

Runner's current `STATUS: PASS | FAIL | BLOCKED` remains the external protocol; place more detailed reasons (`BLOCKED_EXTERNAL`, `FAIL_CODE`, `TIMEOUT`, `FLAKY_SUSPECTED`, `NOT_RUN` etc.) only in `NOTES` or future *compatible* evidence fields supplied by the executor. A missing env var is not evidence of a code bug. No `PASS` without observed command-level proof. Production checks require explicit authorization and permitted credentials; never print secrets.
