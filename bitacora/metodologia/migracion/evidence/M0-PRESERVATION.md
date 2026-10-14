# M0 preservation evidence — 2026-10-13 (session 862a2e59)

Tool: `skill/scripts/migration_inventory.py` (untracked, 306 lines) with
`tests/migration/test_inventory_restore.py` (7 tests, all pass, 0.015s).
Backup root (private, mode 0700, outside repo and outside the bitácora):
`~/.local/share/metodologia-migration/baseline-m0-01/`

## What was captured
| Item | Result |
|---|---|
| Source tree `/home/david/dev/metodologia` (tracked, dirty and untracked, minus `.git` and caches) | 1558 entries, 3 matching observations |
| Live state `bitacora/.state` (the `~/bitacora` symlink target) | 432 entries, 3 matching observations |
| Git history | `repo-all-refs.bundle`, `git bundle verify`: complete history, HEAD `f5f66ba` |
| Installed surfaces (hooks/agents/config/wrappers) | `installed-surfaces.json`: path, mode, symlink target, sha256 only; no contents |

Checksums: manifest `62983b18…edeb5`, bundle `7e1b3302…f65cc`, surfaces `6fd56cab…c6a3`.

## Restore rehearsal (gate G0)
Restored to a new scratch root (never over live data): exit 0; 1690 user files re-hashed, 0 mismatches;
symlinks and modes preserved; backup tree has no group/other permissions.

## Limits (not hidden)
- Observed-consistency only: three matching passes, not a process checkpoint. Other sessions keep writing
  to the repo and `.state`; before cutover (M8) writers must be drained and capture repeated.
- Dirty tree at capture: 56 changed/untracked paths (routing, quota, relay, Antigravity work owned by other
  sessions). They are preserved byte-for-byte in `payload/source`; none was modified.
- `.git` is not in the payload; history is only in the bundle. Stashes are not bundled.
- Credentials live in provider directories (`~/.claude*`, `~/.codex*`); only hashes of config surfaces are
  recorded. Rollback of installer changes (M4) needs real preimage copies of the files it will touch.
- POSIX only (`O_NOFOLLOW`); the Windows machine needs its own port before capture there.
