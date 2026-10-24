AXIS: standards

VERDICT: CHANGES_NEEDED

FINDINGS:

- **LOW — Incomplete CLI invocation.** [SKILL.md](/home/david/dev/.engine-v2-wt/INT/skill/agents/explorer/skills/subplan-dependency-analysis/SKILL.md:18) tells the lead to ingest with `bitacora.py knowledge ingest` but omits the required `delta` positional argument. The CLI requires a JSON file path or `-` for stdin ([bt_cli_knowledge.py](/home/david/dev/.engine-v2-wt/INT/skill/scripts/bt_cli_knowledge.py:15-16)); following the instruction literally exits with an argument error, so the returned delta is not ingested. Give the command’s required argument, such as `knowledge ingest <delta-file>`.

- **LOW — Required provenance ledger not updated.** This commit adds adapted public-source references in [public-adversarial-techniques.md](/home/david/dev/.engine-v2-wt/INT/skill/agents/antagonist/references/public-adversarial-techniques.md:9) and the Explorer skill, but does not update `skill/references/third-party-notices.md`. F2 point 7 requires each public source’s repository, path, pinned SHA, license and adaptation to be recorded there. The new reference files contain much of that information, but the required central ledger has no entries for these sources. Add the required provenance entries to that ledger.

CHECKED:

- Reviewed the target diff and parent; worktree remained clean.
- Checked Antagonist, Runner and Explorer prompts/skills against F2 points 5 and 7, `CONTRACT.md`, and the specified `PROMPT.md` points.
- Confirmed `bt_review_policy.py` is used by both prompt builders; the revised `subagents.md` gate description matches its milestone-scoped behavior.
- Verified the Explorer query command’s flags against the actual CLI parser; it accepts those options and resolves the project from context.
- `git diff --check` passed. No tests, installed-agent generation or runtime invocation was performed; those behaviors remain unverified.