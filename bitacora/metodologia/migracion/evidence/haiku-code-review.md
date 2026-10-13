**Bottom line:** Don't execute the attached spec as written. Its agy and account changes contradict code that tests pin. Its git steps can lose work. The repo already has an owner-authored migration spec (`bitacora/metodologia/migracion/SPEC.md`, marked authoritative at line 55) and a findings file that overlap with this review. I note where I add detail. I could not run tests (no shell tool in this session), so everything below comes from reading and grep. "§" is a section of the attached spec. Short refs are under `/home/david/dev/metodologia/skill/scripts/` unless noted.

### 1. Factual contradictions

- **`bt_worktree.py` does not exist**, and no code runs `git worktree` (§2, §4.5). The only "worktree" hit is a docstring (`bt_runsession.py:108`).
- **Listed as to-do but already present:** agy in `LAUNCHABLE` and `DEFAULT_BIN` (`bt_profiles.py:26,28`). The spec names `DEFAULT_BINS`, and `PROVIDERS` lives in `bt_agents.py:24`. Agy usage extraction exists (`bt_events.py:100-108`). `DBUS_SESSION_BUS_ADDRESS` is already kept, since only `ANTIGRAVITY_*` is stripped (`bt_profiles.py:143-144`).
- **`files:` is not preserved.** `parse_task_line` ignores it (`bt_runstate.py:46-65`), and drift checks skip it (`:183`).
- **Cold-start diagnosis is wrong (§4.4).** Rates are keyed by `(agent, model, kind)`, with no profile (`bt_agents.py:251,294`). So 3→4 cannot separate `claude-1` from `claude-2`. The per-account lever is pressure, and unknown pressure sorts last (`bt_agents.py:299`). `poll()` samples every named claude/codex profile (`bt_subscriptions.py:99-103`), so "starve forever" is unsupported. This matches FINDINGS F07.
- **"80% idle" (§4.5) describes the default config.** `workers` defaults to 1 (`bt_runstate.py:25`, `bt_run.py:248`). `MAX_WORKERS` only caps an explicit `--workers`.
- **The agy ladder (§4.3) names models the code lacks** (`gemini-3.1-pro`, `gemini-4-argon`). Code has only `gemini-3.8-flash-low/medium/high` (`bt_agents.py:43-49`). It also makes Flash the tier-0 builder, which D-004 forbids (`bt_profiles`-neutral: `bitacora/metodologia/DECISIONS.md:110`).
- **Z.ai cost (§5.4) has no call site.** `_effective_cost` is never called. Cost feeds only the load term (`bt_agents.py:261-262`), which sorts after pressure and rate (`:296-301`), so zai is not "naturally prioritized." Reading the clock inside `_stats()` also reprices past load.
- **Commands and paths.** There is no `bt` command; the entry point is `bitacora.py` (`bt_core.py:39`). There is no `pyproject.toml`, root `tests/`, or root `bitacora.py`. M1's `-s tests` path doesn't exist, and "100% of existing tests pass" conflicts with the recorded baseline of 578 tests and 2 failures (`bitacora/metodologia/migracion/FINDINGS.md:33-34`). M2's `diagram` and M5's `zai-glm` don't exist anywhere in the scripts. M3's `installed: true` isn't in `doctor()` output (`bt_profiles.py:307-313`), and `ops_matrix_check.py` has no agy check. M4's `ops_parallel_check.py` is a manual two-repo SIGKILL check (`:1-3`), not a same-repo worktree test.
- **Account IDs** (`claude-1`, `claude-2`, `codex-2`, `agy-main`) match neither the test fixtures (`claude-personal`/`claude-work`, `test_profiles.py:32,169`) nor, per FINDINGS F06 (not re-checked), the machine.
- **"Status: Approved"** is not an owner approval. `migracion/SPEC.md:12` says the planning request does not authorize implementation.
- **Minor:** "40+ modules" versus 69 top-level (`FINDINGS.md:3`). §1 lists eight primitives, §3.2 says seven, and §2 has no `writing-for-agents` directory. `D-004` is used twice (`DECISIONS.md:37,107`), so the citations in `bt_agy.py:3` and `bt_agents.py:41` are ambiguous.
- **What holds:** M2's eval syntax is valid (`evals/run.py:236`).

### 2. Lost capabilities

- **Named Claude accounts.** §5.3 gives `zai` the same tuple as `claude`, and that tuple includes `CLAUDE_CONFIG_DIR`. `_foreign_selectors("claude")` then contains it (`bt_profiles.py:84-85`). So `add()` refuses it (`:66-67`, which breaks the fixture at `test_profiles.py:32`), and `session_env` drops it (`:149-150`). Named sessions silently run on the default config. zai falls back to `~/.claude` too, which violates R12 (`migracion/SPEC.md:29`).
- **Work gate on ambient accounts.** `ambient()` requires the environment's selector set to equal the profile env exactly (`bt_profiles.py:110,118`). With `ANTHROPIC_*` in the list, any exported `ANTHROPIC_MODEL` stops a work-only account from being recognized. Then `authorize_ambient` (`:165-171`) and the no-profile strip (`:152-157`) stop applying. `test_profiles.py:172-179` also becomes host-dependent.
- **Single-account agy.** `bt_agy.py:3-7` and `test_agy.py:68` pin one account, with `ACCOUNT_VARS == ()`. §4.3 adds account dirs, which D-004 excludes (`DECISIONS.md:110`). The signed-in check hardcodes the default token path (`bt_agents.py:228-230`).
- **Same-repo serialization.** `ready_batch`'s docstring promises "never editing the same repository" (`bt_runstate.py:375-378`). §4.5 replaces this with filename prefixes, which cannot see shared generated outputs (F08). `test_milestones.py:196-206` pins the current rule.
- **Human-gated merge.** Merges run only on an explicit web decision (`bt_server.py:208`) and refuse dirty repos (`bt_review.py:62-64`). §4.5 replaces this with an automatic `--no-ff` merge that has no dirty check.
- **Verify target.** Repo-scoped verify runs in the registered repo path, not the session's `workdir` (`bt_runsettle.py:182-187`). §4.5 says verify runs inside `.trees/`, which the code does not do.
- **Prompt contract.** Every session is told to commit on `feat/<req>` (`bt_runprompt.py:111,146,159`; `bt_review.py:14-15`). The spec doesn't change this for worktree sessions. The prompt has the agent create `feat/<req>` if missing, but `worktree add` needs it to exist first.

### 3. Unsafe migration instructions

- **`git worktree add -B`** (§4.5) resets an existing `feat/<req>-<unit>` branch, so commits from an earlier attempt drop off it. Use `-b` and fail if the branch exists (F10).
- **`git worktree remove --force`** (§4.5) discards uncommitted and untracked work, which `migracion/SPEC.md:33` forbids.
- **Merging under `central_lock`** (§4.5). The lock breaks any file older than 60 s, even if its holder is alive (`bt_lock.py:16,51-53`). After the 30 s timeout it runs the body unlocked (`:30,56-59`). Merges need a fail-closed lock with owner identity (F09).
- **Deleting `update.lock` by age** (§4.3). Age doesn't prove the owner is dead (F16). The file is in Google's CLI state directory, outside the repo.
- **More headless writers with skip-permissions** (§4.3). `bt_agy.py:35` already passes `--dangerously-skip-permissions`, and Claude and Codex bypass too (`bt_runprompt.py:267,270`). Adding worktrees, pool rotation, and `MAX_WORKERS=3` widens that exposure. It needs explicit owner acceptance.
- **Secrets.** §5.3 makes `ANTHROPIC_AUTH_TOKEN` an account selector, and `account_key()` writes env values into `quota.json` keys (`bt_agents.py:190-192,156`). A token in a profile env would land on disk. An empty `ANTHROPIC_API_KEY` doesn't prove billing isolation (F12).
- **1113 as quota.** §5.5 maps it to a cooldown via `quota_mark` (`bt_run.py:143`). FINDINGS:28 says 1113 can mean a wrong endpoint or unsupported usage, so a cooldown would hide misrouting.
- **Global env in the wrong module.** §3.1 sets `ARCHIFY_UPDATE_CHECK_DISABLED=1` "globally in bt_profiles.py." It should be scoped to the Archify subprocess.
- **Provisioning without rollback.** §2 and §4.2 install skills into `~/.claude/skills` and `~/.agents/skills` and auto-create profile directories, with no manifest or rollback (R7).

### 4. Acceptance criteria needed

1. **Baseline first** (R1, R13). Record the current run with `-s skill/scripts/tests`. M1 becomes "no new failures; the two known failures closed by owner decision (A4)."
2. **Characterization stays green:** `test_profiles` (`:32`, `:158-179`), `test_agy` (`:66-68`, `:101-104`, `:309-315`), `test_milestones` (`:196-206`), `test_agents` (`:243-261`).
3. **Profile tests in both directions.** Named claude keeps `CLAUDE_CONFIG_DIR`. Claude and zai selector sets are disjoint or split into driver families (F12). Ambient detection ignores non-selector env. No secret value appears in `account_key` or `quota.json`.
4. **Scheduler.** `files:` is parsed, frozen like verify/after/repo (`bt_runstate.py:167-169`), and included in drift (`:183`). Add positive and negative disjointness tests, including in-progress units. Target `ready_units` (production path, `bt_run.py:249`). `ready_batch` has no production caller and is tested only at `test_parallel.py:27,53`.
5. **Worktree crash tests** (R9). Use `-b` only. No forced removal. Check a clean state before merge. Retain the branch on conflict. Run verify in the worktree. Change and test the prompt branch. Isolate the first worker too.
6. **Integration lock:** fail-closed, with owner identity and liveness, plus contention and crash tests (F09).
7. **Agy protocol.** Capture the installed CLI's behavior before changing argv (F03). Keep `--print=` until then, keep one account (D-004), and never delete a lock without verified dead ownership (F16).
8. **Routing.** A cold-start test for bounded exploration (F07). Cost is computed from event time, not `_stats()`'s wall clock.
9. **Z.ai.** 1113 is classified as ambiguous, not an automatic cooldown. Cost is null when unknown. The endpoint is verified before routing (FINDINGS:27-28).
10. **Packaging** (R2, R3). A wheel install from an empty directory runs `bitacora.py`, `python -m bitacora`, and resources. Old commands and paths keep working (`SPEC.md:19-20`). Missing Node gives a clear error and doesn't stop the supervisor (`SPEC.md:39`). Moved tests keep their `sys.path` (`test_config.py:11-12`).
11. **Governance and evidence.** Fix the duplicate D-004. Record owner approval before implementation. Pin archify and mattpocock/skills, and update `references/third-party-notices.md`. Treat "99 checks" as a claim to test, not to cite (FINDINGS:25, :30).

Suggested order: baseline and characterization, then profile and selector fixes, then lock and integration design, then worktree with crash tests, then agy protocol capture, then routing, then Phase 2.

### Limits

- No shell tool here, so no tests or CLI runs. The 578/2 baseline is from `FINDINGS.md` and was not re-run.
- External claims (Z.ai pricing and 1113, the agy protocol, archify) are unchecked. I cite FINDINGS' external section.
- I did not read credential files or machine state (`~/.claude*`, `~/.codex*`, `~/.gemini`, `~/bitacora/.state`). Hooks, `install.py`, and `file_guard.py` are outside your list, so F04, F05, and F11 come from FINDINGS.
- `migracion/SPEC.md:55` asks that findings be kept in `migracion/`. You asked for no edits, so I wrote nothing. Do you want me to add a findings addendum there?