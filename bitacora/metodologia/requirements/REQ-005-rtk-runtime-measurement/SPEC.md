---
id: REQ-005
status: implemented
track: quick
created: 2026-10-12
---
# RTK runtime installation and measurement

Install official RTK in user space and compare native commands with supported explicit RTK filters on identical local workloads. Preserve failure diagnostics and exit codes; verify recovery without rerunning. Record pinned release/checksum, exact tokenizer counts, bytes, timings and quality limits. No global hooks, automatic command interception, commits, pushes, production actions or total-session/billing savings claims. The user explicitly requested installation and measurement.

## Clarified scope
David clarified that this must belong to the parent-skill repository, not be an additional standalone skill. Include an explicitly invoked repository-owned RTK installer, measured use guidance and a reproducible benchmark. Preserve normal installer behavior and existing configuration; use a dedicated RTK-only path on this machine.
