---
name: safe-worktree-contribution
description: Operate safely inside a worktree assigned by M3, protecting base identity and handing off task changes without managing Git integration.
---

# Safe worktree contribution — Implementer private skill

## Trigger
Use when assigned a temporary Git worktree. The M3 executor—not the skill—owns worktree creation, branch leases, composition refs and cleanup.

## Procedure
1. Inspect the assigned worktree, branch/HEAD, `subplan_id@subplan_revision` and `base_sha`; stop on identity
   mismatch rather than switching checkout or creating another worktree.
2. Inspect preexisting dirty/untracked paths and avoid overwriting another contributor's work. Respect path ownership and protected assets.
3. Make only task-owned changes; keep tests and generated outputs within the runtime's allowed paths.
4. Commit only if the brief explicitly requires it, following repository rules. M3 exclusively owns worktree
   lifecycle and Git integration: never create/delete a worktree, merge, cherry-pick, push, force, reset or rebase.
5. Report exact changed paths, commit/snapshot identity, base SHA and unresolved conflicts to M3; never publish a
   subplan version or delete the assigned worktree autonomously.

## Negative tests
Existing unrelated dirty changes, mismatched base or lease, conflict with owned paths, inability to establish expected SHA -> stop and report `BLOCKED`/`NEEDS_CONTEXT` with evidence. A harmless-looking Git conflict is not permission to overwrite semantic contracts.
