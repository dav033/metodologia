# dev — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — Plan progress in PLAN.md and a live plans view; no single-active-plan rule
- **Date:** 2026-10-18 · **Status:** Accepted
- **Context:** Owner wants plans to show completed milestones/tasks, difficulty, model and account, a live server view, and the marathon removed.
- **Decision:** Progress goes in a marker-delimited generated block in PLAN.md (PLAN.json is hash-frozen and its contract forbids state/model/account keys) plus a live web view (`/plans`, SSE). Milestone difficulty derives from task complexity. Plans are immutable for the user; cancel and delete (to a recoverable trash) only. Any number of plans may be active.
- **Alternatives:** one active plan at a time — owner declined; state inside PLAN.json — breaks the frozen hash and the contract.
- **Consequences:** + one data layer (`bt_planstatus.py`) feeds block, context and web; − PLAN.md gains a generated region that sync/drift checks must ignore.
- **Source:** [day log](2026-10/W3/2026-10-18.md) · session 8c9cf122

## D-002 — Router: high complexity prefers Sonnet medium, and sessions spread across accounts
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** First scheduler run (pictures REQ-019): every task, high complexity included, was routed to `gpt-6-luna high` on `codex-1`. Causes: `implementer` ignored complexity by design; the family was ranked by its best account (`codex-luis` 17%) but the account inside the family was picked by pool order (`codex-1` 46%); nothing remembered sessions already placed, so every task got the same answer.
- **Decision:** In `bt_role_routing.py`, high complexity follows the role order for every role (Implementer: `sonnet medium` first, Luna as quota fallback). Each account ranks by its own paced pressure plus 4 points per session ended in the last 5 h (cap 40), then by session count, then role priority and pool order. Quota blocks, exhaustion, busy and ≥85% pressure still outrank load.
- **Alternatives:** only reorder `_HIGH` — does not fix concentration; round-robin counter — ignores quota and survives restarts badly.
- **Consequences:** + a plan's sessions spread across similar-quota accounts; + high tasks use Sonnet while Claude has headroom; − sessions still running are not counted (they are not in the event log until they end); − three `test_audit_routing` tests already failed before this (audit tier escalation vs role policy) and remain.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-003 — Scheduler restart: replayed M3 input must not rewind the M4 store
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** `scheduler-run --resume` of REQ-019 failed twice: `gap_id replay has different or regressing content` (batch path treated `recorded_at` as immutable, unlike `record_stream_gap`) and `cursor cannot regress sequence or byte offset` (the queue replays gaps behind the stored cursor).
- **Decision:** `append_batch` no longer treats `recorded_at` of a replayed gap as immutable (first write wins, as in `record_stream_gap`); `M4StreamIngestor._cursors_not_behind_store` keeps the stored cursor when a replay is behind it on the same boot. The store still rejects a real regression or a changed boot id.
- **Alternatives:** relax the store's cursor check — weakens the integrity invariant for every caller.
- **Consequences:** + a killed or crashed scheduler can resume; − none known. Tests added in `bt_scheduler_monitor/tests/test_store.py` and `tests/test_scheduler_m3_stream_wire.py`.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-004 — M6 snapshot: export-subst files are restored to the pinned blob, then verified exactly
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** pictures marks `version-codigo.json` and `services/ai-api/app/version_codigo.json` `export-subst`. `git archive` expands `$Format:%H$`, so their bytes never match the blob and every verification of a pictures attempt ended `SNAPSHOT_INVALID` → `needs_review` (REQ-019 T1). `git archive` reads attributes from the archived tree: `core.attributesFile`, `GIT_ATTR_SOURCE` and `attr.tree` do not switch it off. A test fixed "export-subst must be rejected".
- **Decision:** On a digest mismatch of a regular file, if `git check-attr --source=<snapshot> export-subst` says `set`, `SnapshotTreeVerifier` rewrites that file with the raw blob (`git cat-file blob`, bounded by the remaining byte cap) and verifies it with the same exact digest. Any other mismatch, and `export-ignore`, still fail closed. Test replaced; a new one proves other differences are still rejected.
- **Alternatives:** skip the digest for those files — weakens the exactness guarantee; strip `.gitattributes` from the archived tree — changes the tree.
- **Consequences:** + repos with `export-subst` become verifiable; − the verifier now reads blobs from the repo for those files only.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-005 — M6 verifier sandbox gets the Node toolchain, the attempt's dependencies and its git metadata (read-only)
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** The sandbox mounted only `/usr`, so every check of a JS project ended `CHECK_UNAVAILABLE` (`M6_SETUP_ERROR:EXEC`) and the run stopped at `needs_review`. The owner requires runs that need no human. A manual `bwrap` showed Node, Playwright and Chromium work inside the same isolation with read-only mounts.
- **Decision:** `QualityPolicy.toolchain` (default on) mounts read-only the operator's Node install (found on `PATH`, only if under the home), the Playwright browser cache, the attempt worktree's `node_modules` at `/workspace/node_modules` and, for a linked worktree, its `.git` file plus the repository's git directory at the same absolute path. Node gets `--max-old-space-size=6144`. Limits fit Node and Chromium: no address-space cap (V8 and Chromium reserve far more than they use) but `RLIMIT_DATA` 12 GiB, 1024 files, 512 processes; command 600 s, total 1800 s. The same command serving several criteria runs once. Still no network, no home contents, nothing writable on the host.
- **Alternatives:** run checks outside the sandbox — drops the isolation; let the operator resolve every review by hand — contradicts the unattended goal.
- **Consequences:** + JS projects verify automatically; − the verifier reads the attempt's own `node_modules` and the whole git directory (read-only, no network); − memory is bounded by `RLIMIT_DATA`, not by a cgroup.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-006 — REQ-019 plan revision 2: no manual checks, one command per criterion
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** M6 can only run `command` checks, `manual` ones always stop the run, one criterion with several commands is ambiguous, a check whose purpose matches no criterion forces review, and T1/T4 verified commands that fail by design until later tasks. Owner (session 8eef50ee): "nada sea manual, el sistema debe poder trabajar sin intervención de un humano".
- **Decision:** Revision 2 turns every `manual` into a command or drops it when it is a follow-up the executor performs (CI watch, bitácora notes); T1 verifies `--base` (the harness reproduces the bug on unfixed code), T4 `--autoprueba` and `--listar-checks`; T5-T7 use `--solo <check>`; T8 keeps remaining issues in a checked fixture; T13 checks a measurement fixture; T14 uses clean-snapshot scripts (`taller:test-gate`, `taller:test-estatico`, `taller:test-ui-final`); T15 keeps the owner-authorized push and checks it with git. T7 low → medium.
- **Alternatives:** keep `manual` checks for the owner — blocks the run; skip verification — loses independence.
- **Consequences:** + the plan can finish unattended; − three criteria that a person judged (phone feel, screenshots, CI result) are now emulated or logged, not judged.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-007 — Scheduler: rebase and retry continuation fixes found on the first plan revision (REQ-019 r1 → r2)
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** `scheduler-run --rebase` on a run with attempts failed three ways: (1) it continued as `--resume` but the runtime marker kept the revision-1 hash (`PLAN_MISMATCH`); (2) the first attempt of the new revision was treated as a retry of the old revision's attempt and blocked (`PREDECESSOR_HANDOFF_MISSING: retry is not authorised`), and each revision has its own executor ledger that cannot see older attempts; (3) a predecessor that the executor never accepted (start rejected) also blocked the retry.
- **Decision:** `rebind_runtime` rewrites the marker with the new plan identity and keeps the `runtime_id`, called by the CLI after a rebase. `RetryContinuation._previous` ignores attempts whose key belongs to another revision (`<plan>:r<rev>:`), and `_handoff` returns nothing to continue when the executor has no record of the predecessor. Same-revision rules are unchanged: a cancelled predecessor still blocks, a failed one with a verified snapshot is continued.
- **Alternatives:** relax the authorisation for every cancelled predecessor — hides a real operator cancel; reopen with a fourth revision — noise to dodge a bug.
- **Consequences:** + a plan can be revised mid-run; − the old revision's partial work is not carried over (it cannot be: another executor root).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-008 — Machine health: btrfs nearly full makes SQLite die with SIGBUS
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** The scheduler died twice with `Fatal Python error: Bus error` inside an SQLite query on the M6 store's `-shm`. `/` is btrfs at 97 % with 93 MiB unallocated (all chunks allocated): a write to a memory-mapped file cannot get space and raises SIGBUS.
- **Decision:** Free scratch data and run `btrfs balance -dusage=10` then `-dusage=30` (unallocated 93 MiB → 2.09 GiB), then resume. The disk still has only ~14 GiB free: the owner should free space.
- **Alternatives:** wrap SQLite in a crash handler — SIGBUS is not catchable in Python; move the state to tmpfs — loses durability.
- **Consequences:** + runs survive; − the cause (a full disk) stays until the owner frees space (P-006).
- **Source:** [day log](2026-10/W4/2026-10-19.md)

## D-009 — REQ-019 plan revision 3: UI oracles must be self-contained; a rebase keeps reaching the snapshots of kept tasks
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** T4's audit waited for a Next dev server on `127.0.0.1:3012`; the verifier sandbox has no running app, so every later check ended `ERR_CONNECTION_REFUSED` (T5). The plan already said «fixtures». Rebasing r2 → r3 with T1–T3 kept then blocked T4's start: `PREDECESSOR_HANDOFF_MISSING … left no snapshot`, because every plan revision gets its own executor root and the kept attempts live in the earlier one.
- **Decision:** Revision 3 rewrites T4's objective and criteria (the audit bundles the real components with esbuild, needs no server, network, database or env file, and exits non-zero when it could not run) and adds a plan-wide constraint; T1–T3 are kept, T4 onwards redone. `_snapshot_sha` falls back, read-only, to the executor roots of the same core run (same run birth) when the current root has no record of an attempt.
- **Alternatives:** start a Next server inside the sandbox — needs env files, a database and fonts the sandbox does not have; one executor root for the whole run — would orphan the existing roots and worktree paths.
- **Consequences:** + audits are deterministic and cheap; − T4's earlier work is discarded; − a rebase now depends on sibling roots staying on disk.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-010 — REQ-019 plan revision 4: the phone audit must prove what T6 promises (T16)
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** T6 was accepted on `taller:test-movil-ui -- --solo hoja` and `--solo lienzo`, written by T4's agent. `hoja` moves the sheet with ArrowUp/ArrowDown and asserts the three heights (127, 380 and 717 px of 844); nothing drags with touch, checks velocity snapping, live reduced motion or the camera view offset, which are T6's criteria. The verifier trusts exit codes, so a weak oracle passes weak work.
- **Decision:** New task T16 (after T7 and T8, before T14) adds the checks `arrastre`, `movimiento-reducido` and `desplazamiento-camara` to the audit and fixes any sheet or camera defect they expose. Accepted tasks keep their state; only T14 changes (waits for T16).
- **Alternatives:** reopen T4 and T6 — discards accepted work; trust the milestone audit — it reads a diff, it does not drag a sheet.
- **Consequences:** + the verifier checks behaviour, not only heights; − one more task; − oracles written by the same agent that builds the feature stay a risk (see P-008).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-011 — M4 monitor: plain text on stderr is not an incident; WAL has a size limit
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** The scheduler died with `StoreError: storage_pressure: measured_bytes=536864600 limit_bytes=536870912`. After ~2.5 h the M4 store held 47 262 `stream_gap` events with cause `malformed_json` on stderr (every progress line of a CLI that prints plain text), 47 377 incidents, as many outbox rows and thousands of `incident_observed` audit rows in M1; the WAL alone was 365 MiB because it never shrank.
- **Decision:** `detect_events` raises no `stream_gap` incident for `malformed_json` on stderr (invalid UTF-8, oversized lines and any stdout gap still do). Each store connection sets `journal_size_limit` to 64 MiB so a checkpointed WAL shrinks back. The oversized WAL was truncated by hand (`wal_checkpoint(TRUNCATE)`, 525 MiB → 171 MiB) and the run resumed.
- **Alternatives:** raise the 512 MiB cap — hides the flood; stop storing the gap events — the bridge acknowledges frames through them, so skipping them would stall the queue.
- **Consequences:** + the store grows with real events only; − the ~47 k stored gap events remain until retention; − stderr diagnostics (quota, connection) are still not parsed from plain text (they never were).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-012 — M4: stderr plain text keeps its cursor, not an event; the verifier generates Next route types; agents are told to create missing check scripts
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** (1) After D-011 the M4 store still reached its 512 MiB cap: the incidents stopped, but ~12 000 stored gap events per attempt and a 313 MiB WAL (checkpoint starvation) remained. (2) `npx tsc --noEmit` failed in the verifier on `LayoutProps`, a type that `next typegen` generates (git-ignored), plus type debt left by earlier tasks. (3) T10 and T11 failed their first attempts only because their agent never created the test script its own verification runs; T11 failed twice, the plan named no path for it and the prompt never said it was theirs to write.
- **Decision:** (1) `M4StreamIngestor._make_write` advances the cursor for a `malformed_json` gap on stderr but stores no event. (2) The sandbox preparation runs `npx --no-install next typegen` for Next projects after the workspace build; plan revision 6 makes T9 clear the type debt and adds `tsc` to T10–T12. (3) The agent prompt now says the checks run from a clean copy (untracked files included, nothing git-ignored, no network, no server) and that a named script that does not exist yet is the agent's to create; revision 7 lists the test paths of T10–T12 and says T11/T12 create theirs.
- **Alternatives:** raise the store cap — postpones the failure; add the missing test files ourselves — the work is the agent's and the verifier must judge it.
- **Consequences:** + the WAL stays in the tens of KiB and the store grows with real events; + type debt cannot accumulate silently; − stderr text is not kept at all (it never carried a diagnostic).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-013 — The plan's publication step may push once to main; no other task may push
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** T15 («rebase, push to main») could not be met: every agent prompt said «do not push … remotes». The owner authorised the push in the requirements round (REQ-019 SPEC, Q2 → «push directly to `main` after the local gate (owner authorization for this plan)», R11) and approved the plan that contains T15.
- **Decision:** `Brief.publishes` is true when a task's frozen verification contains exactly `git merge-base --is-ancestor HEAD origin/main`. Only then the prompt adds a «Publication» section (fetch, rebase onto `origin/main`, run the checks, `git push origin HEAD:main` once, fast-forward only, retry once if `main` moved, never `--force`, no other branch or tag, no remote changes) and replaces the «do not push» rule by «the only remote action allowed is the publication above». T15 only starts after T14's gate (its prerequisite) is accepted.
- **Alternatives:** a push by the supervisor after the gate — needs a human or this session alive; a new `publish` field in PLAN.json — a planner contract change for one task.
- **Consequences:** + the plan can finish unattended within what the owner authorised; − the publication step is detected from the verification text, not a declared field; − a push to `main` of pictures is an outward action (Vercel is expected to build Production from `main`, `checks.yml` runs).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-017 — `/flow` shows one run at a time; provider detail is folded per attempt, never listed
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** The owner asked for the clearest possible `/flow` with no noise. The page showed 5 000 rows of `stream_gap` (99.8 % of 179 000 bus rows for pictures/REQ-019), froze at 11:39 because `/api/flow` kept the OLDEST `limit` events of ONE bus cycle (2 000 rows per store), and every live client recomputed plan-status, which decoded 50 000 M4 rows each time (0.9 s).
- **Decision:** The bus marks the raw M3→M4 stream and info-only incidents `quiet`. The live API reads each run's bus to the end once (`_RunLog`, shared, warmed at server start), keeps the newest 5 000 real messages and folds quiet rows into one digest per attempt; `/api/flow` returns messages + digests + runs from plan-status (the authority on task state). The page: run cards, a one-sentence state, a task strip (click = follow), a weighted map (self-messages as node badges, click filters), category chips as the filter, grouped messages, a per-attempt «Recorrido» tab; provider detail only behind «Mostrar detalle del proveedor». M4 also treats `unsupported_event` on stderr (text that parses as a JSON scalar) as plain text. Attempt usage from M4 is read incrementally per store.
- **Alternatives:** hide noise only in the browser — the API would still ship and the server still parse 179 k rows; delete the old noise rows — destructive, left to the owner (P-128).
- **Consequences:** + 662 real messages served in ~0.05 s; + attempt token totals are complete (were cut at 50 000 rows); − the first read after a server start costs ~5–8 s in a background thread; − per-run memory cache (≤ 5 000 messages per run).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · session 71481911


## D-014 — Agent wall-clock limit is configurable and defaults to 2 h; /home cleaned
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** T14 (final gate) lost two attempts, on `codex-2` and on `sonnet`, to the executor's 30 min wall-clock limit (`m5:timeout_repeated` → blocked). Their work was real: the gate and the type and lint checks exposed debt left by T3 and T12 (`Taller3D.tsx` refs, types in the AI chat test), and the full gate alone takes over 10 min.
- **Decision:** `scheduler.attempt_timeout_minutes` (default 120) feeds the executor `Config.timeout_seconds`; T14 was reopened and continues from the preserved snapshot. Separately, at the owner's request the Baldur's Gate 3 installer files in `~/Downloads/dtest` (218 GB) and the 8 snapper snapshots of `/home` that held them were deleted, then `btrfs balance -dusage=0/20` returned 219 GiB to unallocated space; `/home` went 98 % → 52 %.
- **Alternatives:** shrink T14 — the debt has to be cleared somewhere; raise the limit per task — needs a PLAN.json field.
- **Consequences:** + heavy final tasks can finish; − a hung agent now holds a slot for up to 2 h.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-015 — Up to 3 tasks at once; a large scope runs alone in its repository
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** The owner wants the executor to run at most 3 tasks concurrently, «solo si el alcance lo permite». `scope` is a plan field (isolated_fix, small_change, large_change, full_feature, full_system); the core already serialises by dependencies (`after`), overlapping `expected_paths`, declared `shared_resources` and unknown surfaces, but never read classification.
- **Decision:** `scheduler.max_parallel_tasks` defaults to 3 and the M3 executor ceiling (`max_running`) follows it. New core option `Config.exclusive_scopes` (default empty, so the core stays classification-blind unless told): a task whose `scope` is listed claims its repository exclusively, so it waits for the others and runs alone there. `bt_config` default `scheduler.exclusive_scopes = [large_change, full_feature, full_system]`.
- **Alternatives:** translate scope into `shared_resources` in the plan — every small task would need the same resource name; infer exclusivity from `coupling` — not what the owner named.
- **Consequences:** + independent small tasks run side by side; + big refactors never overlap other work in the same repo; − up to 3 worktrees (with `node_modules`) at once (P-011); the «disk at 98 %» first written here was stale: it was 52 % by then (measured 10:25, cleaned 10:41); − the running pictures/REQ-019 scheduler keeps 1 until its next start (only T15, which depends on T14, is left).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · session 71481911

## D-016 — A watchdog keeps a run alive; operator moves are commands; the verifier has an end-to-end smoke test
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** The first real run (REQ-019) needed a human for every crash (the owner died five times) and for every move on the run (6 attempts cancelled, 5 tasks reopened, 7 plan revisions), each a throwaway Python snippet. The owner asked for a system that works without human intervention.
- **Decision:** `bitacora.py scheduler-watch REQ` (`bt_scheduler_watch`) runs the owner and restarts it with backoff (5 s doubling to 5 min), waits while the disk has < 1 GiB free or a hold exists, treats exit 2 (refusal a restart cannot fix) as final, and gives up with a notification after 5 failures in 30 min (a run longer than 10 min resets the budget). One watchdog per run (flock); autostart now launches the watchdog. `scheduler-op REQ status|stop|resume|cancel-attempt ATT|reopen T|revise` (`bt_scheduler_ops`) puts a hold on the run, stops the owner, applies the move through M1 (`resolve_attempt`, `reopen`, `rebase_to_latest` + `rebind_runtime`), kills the attempt's agent (shim, process group, stragglers in its worktree), releases the hold and makes sure a watchdog runs. `bt_scheduler_quality/tests/test_smoke_node.py` runs real Node, npm and bubblewrap on a minimal JS monorepo.
- **Alternatives:** a systemd unit per run — needs privileges and a unit per requirement; restart inside `scheduler-run` — a SIGBUS or OOM kills that process too.
- **Consequences:** + a crash no longer stops a run; + plan revisions are one command; + the smoke test already caught a real bug (a workspace directory without `package.json` made the verifier skip every build); − a hung but alive owner is not detected (no heartbeat check yet); − the smoke test covers the verifier, not a whole run with a fake agent.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-017 — The verifier accepts a publication snapshot already on origin/main; `scheduler-op retry`
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** T15 (rebase onto origin/main and push) did its job — origin/main became the branch tip — but M6 returned NEEDS_REVIEW (`SNAPSHOT_INVALID`): the rebase rewrote history, so the attempt's pinned base was no longer an ancestor of its snapshot. With nobody to resolve the review the run would have waited forever. Retrying also showed that a cancel needs a reopen once M5 has blocked the task.
- **Decision:** `SnapshotResolver._validated_commits` accepts a snapshot that is an ancestor of `origin/main` even when the base is not (the archive and tree check still read exactly the snapshot commit). `scheduler-op REQ retry TASK` cancels the task's live attempt, waits until M5 blocks it and reopens it. The «a cancelled attempt of the same revision blocks a retry» rule stays.
- **Alternatives:** resolve the review by hand — a human step; skip the ancestry guard for every task — weakens provenance for all work.
- **Consequences:** + a rebasing publication task verifies on its own; − the guard now trusts the local `origin/main` ref, which the repository's own fetch updates.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-018 — A port that is not composed yet says «not ready», not «unknown»
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** On every resume `SchedulerCore.start()` reconciles all live attempts, but the wiring built the core before the executor existed (the executor's root needs the run identity). The execution port answered `AttributeError` (`None.query`), the core read it as «unknown» and flagged every live attempt `uncertain`; M1 then did not know what its running attempt was doing (REQ-019 T15 sat 17 min in `uncertain` while its agent worked). This was P-007.
- **Decision:** the core has `PortNotReady`; `CoreExecutionPort.query` raises it while `executor is None`; the dispatcher then leaves the attempt as it is and flags it `needs_reconcile`, so the first step after the wiring asks the real executor. Fake `FakeExecutor.not_ready` and tests in the core and the adapter.
- **Alternatives:** reorder the wiring — the executor needs the run identity, which exists only after `start()` created the run; reconcile twice — the first pass still writes a false `uncertain`.
- **Consequences:** + a resume no longer marks live attempts uncertain; − a second port that can be not-ready must raise the same exception.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

## D-019 — M4 treats a replayed event as the same event when only its read time differs
- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** At 14:19 the REQ-019 owner died with `ValueError: event_id replay has different content` (M4 `stream_store`). The event id is stable (execution, stream, sequence, offsets) but the body carries `received_at` and `received_monotonic_ns`, the time the frame was read, which differ when a restart re-reads it. D-003 fixed the same shape for gaps (`recorded_at`).
- **Decision:** `stream_store._same_replay` compares replayed event bodies ignoring those two fields; any other difference still raises. Applied to `append_event` and `append_batch`.
- **Alternatives:** drop the fields from the stored body — loses the read time of the first sighting.
- **Consequences:** + a resume no longer kills the owner when it re-reads frames; − the field list is the only evidence that no other volatile field exists: the failing event was not captured, so this is the best-supported cause, not a proven one.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-019 (pictures)

