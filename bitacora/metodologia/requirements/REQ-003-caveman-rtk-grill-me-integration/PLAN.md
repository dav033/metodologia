---
req: REQ-003
status: done
created: 2026-10-12
---
# Plan — Integrate Caveman, RTK and Grill Me

## Approach
Adapt selected prompts into existing routing and focused references, retaining source revisions and license notices. David approved the plan in chat; implementation and scoped verification are complete. No binary or global configuration installation.

## Global constraints
Preserve existing local work, Spanish/Aye and current permissions. No commits, pushes, external mutations or changes to prior review findings. Announce any new source folders before creating them.

## Tasks
- [x] T1 — Identify canonical sources, prompts, licenses and integration boundaries · covers: R4
- [x] T2 — Add attributed prompt reference and license notices; wire concision, optional RTK and design interrogation into existing SKILL/requirements/tools references · after: T1 · covers: R1, R2, R3, R4
- [x] T3 — Validate links/frontmatter and independently exercise concise reporting, absent RTK, failed compressed output and dependent-question scenarios in temporary workspaces; update documentation · after: T2 · covers: R5

## Verification
Run skill-creator quick_validate.py, resolve local Markdown links, inspect the incremental diff against a pre-edit snapshot and run independent behavioral review scenarios with no live commands or paid eval processes. RTK execution remains unverified when unavailable. No build applies to instruction-only changes.

## Progress log
- 2026-10-12: Source investigation completed; RTK not found in PATH. Source implementation untouched. Plan awaiting David's approval.

- 2026-10-12: David approved the plan in chat: "dale adelante". Integrated prompts, routing, license notices and eval cases n/o/p. Skill validator, local links, JSON/regex parsing and preservation checks pass. Independent reviews in progress.

- Independent spec review: APPROVE; independent standards review: APPROVE. Both were read-only and reviewed the incremental integration diff.
- Independent forward test: concise-report scenario, native RTK fallback/failed migration recovery, and two-turn decision-frontier/stop scenario behaved as intended. Simulated responses only; no RTK or migration executed.
- Verification: skill-creator quick_validate passes using ephemeral uv/PyYAML; local links valid; new eval JSON/regex valid; git diff --check passes for modified tracked files; existing reference changes preserved against pre-edit snapshot.
- Completed instruction-only implementation. No runtime test suite, paid eval suite, RTK installation/execution, commits or pushes. SPEC remains in-progress pending owner review/merge under the existing workflow.

## Rulings
- Shorten the existing oversized skill description to preserve its project-work triggers while adding the three capabilities and making frontmatter validation pass.
- Preserve selected source excerpts and adapt surrounding prompts; retain pinned revisions, full applicable license terms and relevant notices in a separate reference.
- Do not import upstream blanket RTK prefixing or claims that compressed output is complete; verify installed support and recover original evidence.
- Keep existing frontier rounds and user stop conditions; avoid duplicating Grill Me as another installed skill or adding an approval gate.
