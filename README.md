# metodologia

Personal working method for Claude Code and Codex: requirements by rounds → approved plan → autonomous executor,
engineering standards, subagent roles, and a per-project bitácora (in `bitacora/`) synced across machines.

## New machine

```
git clone https://github.com/dav033/metodologia ~/metodologia
python ~/metodologia/install.py
```

Then, in Codex, approve the hooks once with `/hooks`. Re-run `install.py` any time; it's idempotent.

- `skill/` — the skill (SKILL.md, references, templates, scripts, agents). Linked as `~/.claude/skills/metodologia`.
- `bitacora/` — project documentation. Linked as `~/bitacora`. Auto-committed and pushed; pulled at session start.
