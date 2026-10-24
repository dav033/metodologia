# Task F2-S — installer must never write through symlinks outside the agent directory

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

Your worktree is branch `ev2/F2-S`, based on `ev2/INT-5` (`e55426709`), the verified F2 completion candidate.

## Finding to fix (reproduced by the consolidated F2 spec audit)
`skill/scripts/install_agents.py:204`: when an Antigravity private skill destination
`<agent_dir>/skills/<skill>/SKILL.md` is a symlink to an external file that contains the public generator marker,
`can_write()` accepts it and `write_text()` follows the symlink, overwriting the external file. Related: `can_write()`
returns True for a dangling symlink (`exists()` is False), so `write_text()` would create a file at the link target.
The same write pattern exists for Claude (`generated_claude`) and Codex (`generated_codex`) role files and for the
Antigravity `agent.md`.

## You own
- `skill/scripts/install_agents.py` and `skill/scripts/tests/test_install.py` (or a new focused test file
  `skill/scripts/tests/test_install_symlink_safety.py`; keep each file under 500 lines).

## Requirements
1. Before any write (agent files and private skills, all three providers), refuse a destination whose leaf is a
   symlink (live or dangling) or whose path from the configured agent directory down to the leaf passes through a
   symlinked ancestor, and refuse when the resolved destination is not inside the resolved agent directory. This
   holds with `--force` too: `--force` may overwrite a hand-authored regular file inside the agent directory, never
   a symlink and never anything outside. Refusal prints a SKIP/REFUSE message naming the path and the reason on
   stderr and leaves the target untouched; other roles keep installing.
2. Preserve intentionally configured top-level agent-directory aliases: the configured directory itself
   (e.g. `--claude-dir`, `--antigravity-dir`, or a configured account's agents dir) may be a symlink; containment is
   checked against its resolved path. Preserve Planner's special `skills/metodologia` link to the installed
   methodology root (existing behaviour; it must still be created/accepted only when it resolves to
   `resource_root()`), and do not write through it.
3. Prefer a write that does not follow a leaf symlink created between check and write (e.g. write a temp file in the
   same directory and `os.replace`, or open with `O_NOFOLLOW`); stdlib only, POSIX is the target, keep Windows-safe
   fallbacks if the module already has any.
4. Regression tests (temp dirs only, never real `~/.claude`, `~/.codex`, Antigravity dirs), each failing before your
   fix: marked external file behind a leaf symlink (with and without `--force`) stays unchanged; dangling leaf symlink
   creates nothing outside; symlinked ancestor (`skills/` or `skills/<name>/` linking outside) refused; same leaf
   check for Claude and Codex role files; aliased top-level agent dir still installs; Planner methodology link still
   created and a wrong-target link still refused.
5. No other behaviour change: marker rule, skip messages for hand-authored files, role lists, generated content.

## Verification
Focused: `PYTHONPATH=skill/scripts/tests:skill/scripts python -m unittest test_install test_agent_skills_static`
(plus your new file) from the worktree root, then the full root suite per RULES.md. Report totals and every
non-baseline failure. Do not run the real installer against real profiles.
