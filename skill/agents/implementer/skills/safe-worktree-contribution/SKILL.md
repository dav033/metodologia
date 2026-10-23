---
name: safe-worktree-contribution
description: Operate safely inside a worktree assigned by M3, protecting base identity and handing off task changes without managing Git integration.
---

# Safe worktree contribution — Implementer private draft (not approved)

## Trigger
Use when assigned a temporary Git worktree. The M3 executor—not the skill—owns worktree creation, branch leases, composition refs and cleanup.

## Procedure
1. Inspect the permitted worktree, branch/HEAD and assigned base ID; stop on identity mismatch rather than switching checkout or creating another worktree.
2. Inspect preexisting dirty/untracked paths and avoid overwriting another contributor's work. Respect path ownership and protected assets.
3. Make only task-owned changes; keep tests and generated outputs within the runtime's allowed paths.
4. Commit only if the brief explicitly requires it, following the repository rules and without push/force/reset/rebase of shared refs.
5. Report exact changed paths, commit/snapshot identity and unresolved conflicts to M3; never merge, cherry-pick, publish a subplan version or delete the worktree autonomously.

## Negative tests
Existing unrelated dirty changes, mismatched base or lease, conflict with owned paths, inability to establish expected SHA -> stop and report `BLOCKED`/`NEEDS_CONTEXT` with evidence. A harmless-looking Git conflict is not permission to overwrite semantic contracts.
