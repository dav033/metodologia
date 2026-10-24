# Task F2-H — `install_agents.py` for eight roles and their private skills + static skill tests

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
The installer supports the new `designer` role and the private skill folders of every role for Claude, Codex and
Antigravity, and a static test suite keeps every role prompt and skill consistent.

Sources: master (Spanish) `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md`
§20.3–20.6 (lines 1884–1941) and §20.7 "Regla de resolución de rutas" (lines 1997–1999); CONTRACT §3 (Designer
install for Claude, Codex and Antigravity). Current `skill/scripts/install_agents.py` and its tests (find them, e.g.
`grep -rl install_agents skill/scripts/tests tests`). Role files `skill/agents/*.md`, skills
`skill/agents/<role>/skills/*/SKILL.md`, references `skill/agents/<role>/references/*.md`.

## You own
- `skill/scripts/install_agents.py` and its existing tests; a new test file
  `skill/scripts/tests/test_agent_skills_static.py`.
- If the installed agent count or role list is asserted elsewhere (e.g. `bt_agents`, routing parity tests), you may
  update those assertions only, and report it.

## Requirements
1. Every role with a `skill/agents/<role>/skills/` folder (not only Planner) gets its private skills wherever the
   provider needs them: Antigravity copies them into the role directory (as it does for Planner today; Planner keeps
   its `skills/metodologia` link); for Claude and Codex the generated role text resolves `agents/<role>/skills/...`
   against the installed Metodología skill root (master §20.7 path rule) — make sure the generated file states that
   root (absolute installed path) so a role can find its skills; a skill that cannot be resolved is reported, never
   searched for elsewhere.
2. `designer` installs for Claude, Codex and Antigravity like any role (with `--agent designer` and in the default
   all-roles run, following the existing per-provider rules). Note `skill/agents/designer.md` may not be merged yet
   in your base; write the installer and tests generically and include a fixture role with skills in your tests.
3. Safety: only files carrying the generator marker are overwritten; a hand-authored file or skill path is skipped
   with a message (test both); `--force` behaviour unchanged; dry runs/tests write only into temp directories
   (never `~/.claude`, `~/.codex` or real Antigravity dirs during tests).
4. Static tests over the real repository (all roles, all skills): frontmatter present with `name` = folder name and
   a non-empty `description`; every `agents/<role>/skills/...` or `references/...` path mentioned in a role prompt or
   skill exists; every private skill folder of a role is referenced by that role's prompt with a conditional-load
   sentence (the prompt names the path); Runner's prompt keeps `STATUS: PASS | FAIL | BLOCKED`; Implementer's prompt
   names the three exclusions (`systematic-debugging`, `verification-before-completion`, `receiving-code-review`) as
   excluded; no skill file contains an obvious secret shape. Tests must pass on the current tree; where a role's
   wiring is still being merged by other tasks, the test must still be correct (it checks what exists; do not skip
   roles by name).
5. `python skill/scripts/install_agents.py --help` documents the role list and options.

## Verify
Installer tests, the new static tests, and the full suite per RULES.md.
