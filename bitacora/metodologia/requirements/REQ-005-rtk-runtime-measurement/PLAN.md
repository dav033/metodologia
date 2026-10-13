---
req: REQ-005
status: done
---
# Plan — RTK in the parent methodology

- [x] Inspect upstream release, telemetry defaults, current environment and parent repo.
- [x] Install and verify the exact release in user space, without hooks or settings changes.
- [x] Compare native and RTK on matched read-only Git plus controlled passing/failing tests, using one tokenizer and three paired runs.
- [x] Preserve diagnostics, exit codes and recovery without rerunning.
- [x] Add repository-owned pinned installer, explicit CLI routes, measured skill guidance, reproducible benchmark and focused installer tests.
- [x] Incorporate independent final reviews and close the report/bitácora.

The user said “instala y mide rtk” and clarified RTK must live in the parent skill repository. Scope excludes standalone skills, global hooks, changing telemetry consent, commits/pushes, and claims about total-session or billing savings.

- Re-review follow-up: standards identified partial destination risk. Replaced direct writes with an exclusive same-directory temporary plus atomic no-overwrite hard link; a focused test confirms temporary cleanup and destination preservation on publication failure. Focused installer suite now passes 9/9.

- Independent spec and standards reviewers approve without remaining findings.
