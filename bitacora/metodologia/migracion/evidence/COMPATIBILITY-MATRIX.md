# Legacy compatibility matrix — M1 / T4 (2026-10-13)

Executable form: `tests/migration/test_legacy_contracts.py` (24 tests, stdlib, throwaway HOME and BITACORA_ROOT,
subprocess boundary). `BITACORA_ENTRYPOINT=<path>` points the same file at another entry point (installed
package, shim) for old-versus-new parity in M2/M6.

| Contract | Pinned behavior | Test class |
|---|---|---|
| Command set | 36 top-level commands registered; each answers `--help` with exit 0; unknown command/argument exit 2, usage on stderr, empty stdout | CommandMatrixTests |
| `init` / `where` | idempotent (`created` true then false); central docs, day/week/month paths, INDEX.md, `Wn` week folder | DocumentsAndIdsTests |
| IDs | `id` is "next free", never consumes; `req new` slugs the title; high-water mark survives a pruned item | DocumentsAndIdsTests |
| Config | dotted key stored nested in `.state/config.json`; invalid key/value exit 1 and write nothing; `get`/`set`/`unset` round trip | ConfigTests |
| Hooks | `hook start` stdout is `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":…}}`; stop/end exit 0; garbage stdin exits 0 | HookTests |
| Session binding | recorded in `.state/sessions.json` | HookTests |
| RUN.json | historical file without newer fields loads; unknown fields round-trip through `save`; unreadable file raises `RunStateError` and is not replaced | HistoricalRunStateTests |
| Web | loopback only; `/` serves HTML; POST without the token is rejected (4xx); `server-token` and `server.json` written | WebTests |
| Shell mutation heuristic | writes/commits/heredocs count as work; read-only commands do not; known misses (`cp`, `mv`, `rm`, `python x.py`) and one false positive pinned; writes into the bitácora root count as logging | ShellMutationHeuristicTests |
| Size policy | advisory only: >500 lines on source files prints PostToolUse context, exit 0; 500 exactly, exempt dirs/suffixes and garbage input stay silent; Codex `apply_patch` paths checked | FileGuardTests |

## Findings from characterization
- **F-M1-01 · config drops unknown data.** `bt_config._write` rebuilds `config.json` from validated non-default overrides. A
  `config set` removes unknown sections, invalid values and values equal to the default. Pinned as current behavior. R4
  asks that unknown fields survive round trips: M2 must either preserve unknown sections in config or record an
  explicit exception with owner approval. Not changed here (characterization, not repair).
- **F-M1-02 · shell mutation misses.** `cp`, `mv`, `rm` and interpreters that write files are not counted as work, and a
  quoted `>` followed by a dotted token is. Pinned; any change is a behavior change with its own evidence.

## Not covered yet (stated, not hidden)
- Historical RUN.json is a synthetic fixture; real archived runs in the bitácora were not copied into the test tree
  (they hold project content). A restore-based drill against the M0 backup belongs to T18.
- Codex and Antigravity hook payload variants (`--harness`) and the relay/launch/handoff/delegate commands need
  fake-CLI fixtures; they belong to T7/T8 where the driver contract is defined.
- Web: only the dashboard and token gate; plan approval, rounds and graph pages are not exercised end to end.
