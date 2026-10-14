---
type: release-report
project: metodologia
requirement: REQ-007
status: local-release
date: 2026-10-14
---
# REQ-007 release report: local platform, capability by capability

Session 862a2e59 and its Codex Luna helpers. Everything below ran on this machine (Linux, Python 3.12/3.13/3.14, Node 24,
Chromium). Nothing was committed or pushed. Z.ai (M9, R12) was explicitly excluded by the owner and is not activated.

## Verification commands
| What | Command | Result |
|---|---|---|
| Whole suite (legacy collected in place + migration) | `cd ~/dev/metodologia && python -m unittest discover -s tests -q` | 776 tests, OK (2026-10-14) |
| Legacy suite alone | `python -m unittest discover -s skill/scripts/tests -q` | 591 tests, OK |
| Migration tests alone | `python -m unittest discover -s tests/migration -q` | 185 tests, OK |
| Real-agent full flow (Claude builds, Gemini Flash audits, Codex available) | `python skill/scripts/ops_flow_check.py` | RESULT OK, 27 PASS (2026-10-13 23:07) |
| Account x model x delegation matrix | `python skill/scripts/ops_matrix_check.py --project pictures` | 17 of 18 cells verified; the 18th is the script's own work-project cell, which fails because the script passes a parent directory that is not a registered repo; the same check passed by hand inside `pictures-wt/t12` (no files changed) |
| Install dry run / apply / undo | `python install.py --dry-run`, `python install.py`, `python install.py --rollback <journal>` | applied once; journal under `~/.local/share/metodologia-migration/installs/` |
| Preservation backup restore drill | `python -m unittest discover -s tests/migration -p test_inventory_restore.py` and `test_cutover_restore.py` | pass |

## Requirements
| Req | Capability and owner | Where it lives now | Evidence | Status | Limits and rollback |
|---|---|---|---|---|---|
| R1 | Restorable inventory of source, state, installed surfaces | `skill/scripts/migration_inventory.py`; backup `~/.local/share/metodologia-migration/baseline-m0-01/` | 13 inventory tests; restore of 1690 files with 0 mismatches; cutover rehearsal on restored state | **verified** | Observed consistency, not a process checkpoint; POSIX only. Repeat the capture before any further cutover |
| R2 | Install from a wheel, run anywhere with resources | `pyproject.toml`, `bt_resources.py`, `bitacora_platform` | wheel + sdist rebuild; `uv pip install` on 3.12/3.13/3.14 with generated launchers; checkout hidden | **verified on Linux** | Windows/macOS not tested. Editable `uv tool` install is what runs on this machine |
| R3 | Legacy paths, commands, hooks, URLs keep working through one implementation | the legacy script files are the canonical modules; console scripts map to them | 24 characterization tests; 12 old-vs-installed parity tests; hooks for Claude, Codex, Antigravity | **verified** | No shim removal planned |
| R4 | Data, IDs, unknown fields, relay state preserved | state files untouched; ID high-water mark | cutover rehearsal: old and new runtimes read identically, new writes readable by old, IDs never decrease | **partial** | F-M1-01: `config set` drops unknown config sections (pinned, not fixed) |
| R5 | Execution capabilities survive (workspaces, gates, routing, verify, resume, relay, trace) | unchanged supervisor, routing, relay | legacy suite plus flow check and matrix with real agents | **verified** | Windows launchers untested |
| R6 | Provider adapter contract | `bt_driver.py` contract v1; shadow-mode `contract` field per attempt | 15 fake-CLI tests; shadow tests | **partial** | The supervisor records the contract status but does not act on it; no opt-in real versioned samples; Codex `completed` is best effort |
| R7 | Idempotent, diffable, reversible provisioning | `bt_install_tx.py` wired into `install.py` steps 1-3; `bt_profile_matrix.py` | 11 transaction tests, 4 wiring tests, 4 matrix tests; real apply with journal | **verified on Linux** | No Windows PowerShell launcher or macOS test; `authenticated` is never claimed without evidence |
| R8 | Bounded cold start without bypassing gates | `bt_agents._quality_order` | 5 cold-start tests, 8 routing characterization tests; D-013 | **verified** | Exploration is bounded by 5 judged attempts per provider/model/kind |
| R9 | Same-repo parallel writers in worktrees, serialized verified integration | `bt_worktree.py`, `bt_integration_lock.py`, `bt_run_isolated.py`, `run --isolation worktree` (off by default) | 12 worktree, 7 lock, 5 capacity, 28 isolated-run tests; four independent reviews, four fix rounds | **verified, opt-in** (fourth independent review APPROVED; 5 consecutive full-file runs). Residual: stale git metadata of worker/integration worktrees is not pruned after a hard kill | Opt-in. No measured throughput claim: three workers is a cap, not a benchmark. Never merges to main |
| R10 | Methodology as platform policy, thin optional skills | 9 references, GLOSSARY on demand, router rows, `third-party-notices.md` | 38 upstream skills reviewed (8 adapted, 10 already covered, 20 skipped); parity test; 6 evals written | **partial** | The 6 `m6-*` evals were not run against a live agent; no measured pass rate |
| R11 | Pinned diagram capability | `skill/vendor/archify` (PIN.json), `bt_diagram.py`, `bitacora diagram` | 13 contract tests, five types, hostile IR, atomic publish, sandbox CSP, Chromium light/dark capture | **verified** | Human visual review done on the architecture page only; others have the automated capture |
| R12 | Optional Z.ai family | not built | n/a | **not activated by owner decision** | Phase 2 stays unavailable; nothing to roll back |
| R13 | Cutover evidence and legacy retention | this report, `install.py --rollback`, M0 backup, rehearsal | cutover rehearsal tests; flow check; matrix | **verified on this machine** | No legacy shim was removed; nothing deleted |

## What is installed and active on this machine
- `install.py` applied through the transaction layer: skill links, hooks for Claude and Codex accounts, always-on blocks
  (already present, not duplicated), subagent definitions, secret-scanning hooks including linked worktrees.
- Commands on PATH: `bitacora`, `bt`, `globalusage`, `relay-run`, `file-guard`, `install-agents`, `install-rtk`,
  `bitacora-inventory` (editable `uv tool` install pointing at this checkout, so there is one implementation).
- Web dashboard restarted on the new code (127.0.0.1:8765); usage poll timer already active; relay hooks untouched.

## Open items
1. Windows and macOS: launcher, hooks and installer paths are untested. They are pending, not passing.
2. R6: decide when to move the contract from shadow to enforcing; collect real-provider samples first.
3. R10: run the `m6-*` evals against a live agent and record the pass rate.
4. R4/F-M1-01: decide whether config must preserve unknown sections.
5. Nothing is committed. The working tree also holds other sessions' uncommitted work; separate before committing.
