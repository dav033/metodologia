# REQ-024 read-only matched-arm candidates

These pre-freeze candidates match the approved controls in REQ-024 PLAN.md: Claude Opus 5.5 high, `Read/Grep/Glob`, permission mode `plan`, no session persistence. They use `--safe-mode --restricted` and append a hash-pinned prompt so user/project hooks, discovered skills, and custom agents are not loaded. The four Planner skills and method references are embedded in each arm prompt. Plan artifacts are returned as labeled blocks and captured by the host; the model has no write tool.

Arm A sources the T1 snapshot at `196196ef427ab1f066d22faaeece2a40f8aa182c`. Arm B uses the current improved Planner worktree bytes. The shared task template is at `task-prompt-template.md`. Each arm pins nine source files and hashes its prompt and invocation candidate.

**Not frozen or runtime-verified.** The local CLI `--help` parser can validate option syntax without a provider call, but does not prove session startup, configured account preservation, or hook/tool isolation. The account profile and actual runtime version must be pinned in T17. P-108 and P-109 remain open. No manifest, cell, reviewer record, quota refresh, or model call exists.

Candidate flags: `claude --safe-mode --restricted --append-system-prompt-file <prompt-bundle> --tools Read,Grep,Glob --permission-mode plan --no-session-persistence --model claude-opus-5-5 --effort high --print --output-format json`.

Sources: [Claude CLI reference](https://code.claude.com/docs/en/cli-reference), [Claude sub-agent reference](https://code.claude.com/docs/en/sub-agents).
