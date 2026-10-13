# CodeGraph (optional code-graph MCP)

[CodeGraph](https://github.com/colbymchenry/codegraph) (`@colbymchenry/codegraph`, MIT) parses a repo with
tree-sitter into a local SQLite graph (symbols, calls, imports, inheritance) and serves it over MCP. Native on
Windows (bundles its own Node runtime + Rust parser; no build tools). Optional: everything works without it.

## When to use it (explorer and main session)

| Question | Prefer |
|---|---|
| "Who calls X?", "what does X call/depend on?", "what breaks if I change X?" (symbol / call-path / impact) | `codegraph_callers`, `codegraph_callees`, `codegraph_impact`, `codegraph_node` |
| "Where is feature Y implemented?" in a repo you don't know | `codegraph_explore` first, then Read the 1–3 files it points to |
| Literal strings, error messages, config keys, env vars, routes, comments, non-code files | Grep/Glob — the graph only knows symbols |
| Repo not indexed (tool replies "isn't indexed") | Grep/Glob. Don't index on your own — it's the user's call |

Tools are only available when the repo has a `.codegraph/` index. Results carry `path:line`; spot-check before
building on them, same as any explorer finding.

**Measured (maros-nest, 423 files, Haiku, 2 questions × 2 runs, 2026-10-08):** roughly neutral. Same answers,
similar wall time (13–21 s vs 15–33 s with grep), tool calls 7–15 vs 9–17, but ~20–60 % more context tokens
(explore returns whole files). Graph wins on caller/callee lists; grep wins on "which exception / which string".

## Index a repo (once per repo, per machine)

```bash
cd <repo>
codegraph init .                       # ~12 s for 420 files; writes <repo>/.codegraph/codegraph.db
echo ".codegraph/" >> .git/info/exclude   # local-only ignore; never edit the tracked .gitignore
```

`.codegraph/` contains its own `.gitignore` (`*` + `!.gitignore`), so without the exclude line git still shows
`?? .codegraph/`. Indexed so far: `maros-nest`.

Re-index: not normally needed — while an MCP session is open a per-project daemon watches files and syncs
incrementally, and on reconnect it catches up with edits made offline. Manual: `codegraph sync .` (incremental),
`codegraph index . --force` (full rebuild), `codegraph status .`. Remove: `codegraph uninit .`.

**Staleness:** the graph reflects the last sync. After a big branch switch/rebase with no session open, run
`codegraph sync .` (or trust Read over the graph when they disagree). Dynamic dispatch (DI tokens, string-keyed
handlers, decorators) is resolved heuristically — a missing caller is not proof there are none.

## Install on a new machine

`install.py` step 7 runs `npm i -g @colbymchenry/codegraph` (non-fatal, needs npm). Then, by hand:

```bash
codegraph telemetry off
claude mcp add --scope user codegraph -e CODEGRAPH_TELEMETRY=0 \
  -e CODEGRAPH_MCP_TOOLS=explore,node,search,callers,callees,impact -- codegraph serve --mcp
```

Codex — back up `~/.codex/config.toml`, then append:

```toml
[mcp_servers.codegraph]
command = "codegraph"
args = ["serve", "--mcp"]
env = { CODEGRAPH_TELEMETRY = "0", CODEGRAPH_MCP_TOOLS = "explore,node,search,callers,callees,impact" }
```

Don't use `codegraph install`: it also writes a block into CLAUDE.md/AGENTS.md and permission rules, which
duplicates this file. `CODEGRAPH_MCP_TOOLS` re-enables the call-path tools (by default only `explore` is listed).
Restart Claude Code / Codex sessions after registering.

## Operational notes

- Per-project daemon (~340 MB RAM) survives the session and exits after ~10 min idle. `codegraph daemon` lists/stops
  them; `CODEGRAPH_NO_DAEMON=1` disables it (then one `serve --mcp` per project).
- Unindexed repos: the server answers "not indexed" and does nothing — it never creates `.codegraph/` by itself.
- Uninstall: `claude mcp remove codegraph -s user`; remove the Codex block; `npm rm -g @colbymchenry/codegraph`;
  delete `<repo>/.codegraph/` and the exclude line.
