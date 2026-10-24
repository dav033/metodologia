# Engine v2 lead continuation — session 01a16b88

Owner requested a handoff. This is state/evidence, not new authorization. Original authorization is CONTRACT.md and
PROMPT.md in this directory; continue the entire Engine v2 effort outside the normal REQ/scheduler flow.

## Verified repository state

- Main remains `48f45935e` (code head `28e3a831d`). This session made NO main code merge/push or real agent install.
- Main has uncommitted bitacora changes: existing/generated dev logs/indexes, the metodologia day log/SUMMARY and
  this continuation. Preserve all. Do not sweep unrelated initial dev-log changes into a code commit.
- Worktree root/tooling: `/home/david/dev/.engine-v2-wt/`; original RULES.md/launch.sh/status.sh remain.
  RULES now explicitly forbids worker relay/handoff: hooks inherit the lead session/quota identity.
- Protected runs/PIDs remain outside scope: david-ui REQ-001, pictures REQ-020, pid 2108326 and pid 917.
  Do not resume/signal them or touch their .state. Final owner resume instructions are in the day log's
  PAUSED BY OWNER ORDER entry, as required by PROMPT.md.

## Completed evidence and branches

- Original main work from the first relay is retained; do not redo P0 or merged F1-C/F2-D/C/R/E/G/F3-A.
- INT-4 at `a02434ced`: root suite 2414 tests, 15 known baseline failures, 6 skips; all 8 module suites OK;
  total 1445 seconds. Log `suite-INT-4-resumed.log`. Original script's live terminal result confirmed no MODULE FAIL.
- F2 completion candidate `ev2/INT-5`, worktree `INT-5`, target `e55426709`:
  F2-A integration `71a9b6484`; central provenance/Designer exact paths `6ab19f9d3`;
  role inventory/ingestion-command fixes `c1b0257d9`; installer/static tests `e55426709`.
  Underlying worker commits are on F2-H: `949823755`, `6a28476fe`, `05d02454` (plus original F2-A base).
  A fresh ROOT suite is still running to `suite-INT-5.log`; do not mutate this snapshot until it finishes.
  Module/adapter/package files are byte-identical between old INT and INT-5, so INT-4 module evidence applies to this delta.
  F2-H static9, profile7, role-routing22, migration parity12 passed. Its earlier full suite:2423/15 baseline/6 skips.
- F4-4 routing: `3544d295` on `ev2/F4-4`, both independent axes APPROVED. Module173 and focused31 pass;
  root2408/15 baseline/6 skips. An isolated source test's PLAN_CHECKS_UNMAPPED failure was reproduced identically on main;
  discovery from skill/scripts is required to resolve test helpers.
- F4-6 initial `8ecc57cc`, repaired `ac83315d6ef84fcf1e0df0c688f47f0fb6f25089` on `ev2/F4-6`.
  Repairs final-verdict reason classification, legacy replay/UNCLASSIFIED round-trip, paired composition schema fields,
  and extracts cache/history persistence to check_history.py. Report `F4-6-fix.result.md`; untracked full log is
  INSIDE its worktree at `F4-6/F4-6-fix-tests.log`. Focused module168 and other49 reported passing.
  IMPORTANT: worker calls 2228 tests/zero failures a full suite, unlike root ~24xx/15 baseline. Verify cwd/collection before
  accepting that claim; likely legacy-only discovery from skill/scripts. Needs independent repair review and correct ROOT proof.
  Initial full evidence was2409/15 baseline/6 skips. Cross-ledger owner wiring stays F4-9; external metadata F4-7.

## F2 new phase blocker — not repaired yet

F2-H individual spec/standards approved, but consolidated F2 spec audit reproduced a marked symlink escape in installer:
Antigravity private SKILL.md symlink to an external marked file is followed by write_text. Fix leaf/ancestor symlink escape
and resolved-root ownership (including --force) with isolated regression tests. Apply scoped fix on F2-H or a new branch,
NOT live INT-5 while its suite runs. Check Claude/Codex destinations consistently; preserve intentionally configured top-level
agent-directory aliases and Planner's special methodology link. No real profile writes until verified integration.

The phase review's final result file was overwritten by a Stop-hook response. REAL report is in
`F2-phase-review-spec.log` around lines2761 onward: AXIS spec / CHANGES_NEEDED / F2-1 medium, symlink escape reproduced;
14 focused tests passed after correct PYTHONPATH. Recover that report, do not accept the last hook-response as audit evidence.
Consolidated phase standards still needs to run. Central provenance is now in third-party-notices.md; no need to fetch it again.

## Native workers interrupted for this handoff; tests may still run

Native F1-A3 and F3-B repair agents were INTERRUPTED explicitly before handoff so successor can take over without duplicate
writers. Their uncommitted changes remain. Their already launched root unittest processes may continue: check /proc cwd and
process inventory before relaunching. No process was killed. Native team handles do not transfer reliably to another session.

### F1 schema

- `ev2/F1-A`, committed latest `3f4d4b7c`; uncommitted F1-A3 changes in schema_13.py, new schema_13_inputs.py and
  test_schema_13_review_regressions.py. New module/compat checks passed before its root suite began.
- `F1-A3-tests.log` contains complete tests; root process at handoff was pid1466326 (verify alive/cwd).
- Accepted review repairs being finished: validate/normalize graph containers/identifiers BEFORE traversal so produces=null,
  consumes=null, audit_task=[] with real gates/consumers never throw; generative malformed-field regression matrix.
  Publication ordering is forall consumer task, exists qualifying gate in THAT task's ancestors (not one common gate).
  Mixed implementation+contract cycles are errors in either subplan ordering; only all-contract cycles warn.
  Always validate composition_gates even without subplans; `[{}]` must not pass. Preserve all legacy reports/hashes, default1.2.
- Earlier module351 and compat3 passed; its root2407 had15 baseline + platform process-group failure (see below).
- After current suite finishes, inspect diff, commit completed repairs, independent spec/standards/Antagonist review, integrate;
  then launch already-written F1-B.brief.md. F1-B not started.

### External research store

- `ev2/F3-B`, latest committed `cc693ca4`; uncommitted repair in external.py, external_contract.py, freshness.py,
  tests/test_external.py and README. `F3-B-fix-tests.log`; root process pid1468883 at handoff (verify).
- Accepted repairs: invalidation cannot clear without verifiable later evidence; future dates not fresh; preserve complete
  old provenance/excerpts before deduplicated refresh; malformed kind/confidence/URL becomes stable KnowledgeError;
  inline/backtick/prose commands marked and source text delimited as untrusted; read queries/dossier/stats never initialize
  schemas/directories/DB/WAL configuration, even querying absent or code-map-only stores.
- Earlier module31/integration5 passed; root2409 had15 baseline + platform process failure. After repair tests finish,
  inspect/commit and independently review before integration.

## External CLI workers still active — do not launch duplicates

- F4-3 M1: task `F4-3-resume`, account codex, worktree F4-3, uncommitted implementation. CLI pid1178028 and root-suite
  pid1419005 at handoff; report will be `F4-3-resume.result.md`, complete log `F4-3-resumed-tests.log`.
  Wait for report and review both axes/Antagonist where needed. In review inspect full immutable subplan metadata (produces/
  consumes/checkpoints), malformed input, state schema migration, and stale published-version facts after rework/revision.
- F4 composition: prior repair `6c936b4e`; native repair worker stopped on a misleading inherited quota relay and left
  partial changes. Its accidental relay `RELAY-20261023-210406.md` is NOT the lead handoff.
  Reassigned via CLI task `F4-1c-resume`, account codex-luis, SAME worktree F4-1; CLI pid1503677 at handoff.
  Exact self-contained `F4-1c-resume.brief.md` records all eight accepted fixes; wait for its result/log before doing anything.
  Fixes: owned/proven-orphan cleanup and bidirectional repo/root overlap refusal, no rmtree after Git failure; symref no-deref
  namespace protection; atomic migration DDL; durable version/request/manifest reservation before Git publication; publish/reject
  serialization/reconciliation; rejected-member conflict interactions; stable manifest with typed bound verdict proofs;
  empty-path EvidenceKey cannot reuse. Public API may change before M3/owner consumers exist.
  DISMISSED spec finding: run_base is bootstrap fallback; published current must remain preferred (ENGINE-F4 §1).

## Baseline and evidence pitfalls

- Keep the accepted baseline EXACTLY15 failures from RULES.md/baseline-failures.txt; never weaken checks or add extra failures.
- Platform test `test_kill_tree_ends_a_group_that_ignores_sigterm_and_its_children` intermittently fails with
  `ProcessLookupError not raised` under concurrent suites. It occurred on original F4-1 and F1-A2/F3-B, passes isolated,
  and platform code/test are unchanged from pre-engine-v2. Do not call those 16-failure runs green; final integration must
  reverify under reduced contention. INT-4, F2-H, F4-4 and F4-1b root runs had only the15 baseline failures.
- ROOT suite: run from worktree root `python -m unittest discover -s tests`; module suites from skill/scripts without -I.
  Focused tests often require discovery or PYTHONPATH=tests; direct module-name import can fail on helper modules.
- New external `verify_snapshot.py` captures full root+module logs, raw exits and before/after code hashes. It has not yet
  been used; inspect before using. Never modify a running suite script. Existing run_suite.v2.sh masks module exit details
  in tail output; INT-4 terminal completion explicitly said all8 checked without MODULE FAIL.
- Do not lose raw audit reports when a CLI final is a hook response; recover the actual report from its log.
- Near handoff /home had roughly6 GB free; do not delete user files or snapshots. Original P0 backups remain intact.

## Next — lead order

1. Revalidate git status, running CLI/test processes and all current log tails. Do NOT repeat completed implementations.
   Collect live F4-3/F4-1c results; wait for already running INT-5/F1-A3/F3-B suites before resuming their worktrees.
2. Repair F2 installer symlink blocker, run independent consolidated standards and repair review, verify fresh combined
   snapshot; integrate/push only verified code. Actual install_agents.py run is authorized, --help first, no --force without backup.
3. Finish/review/integrate F1 schema and F1-B; F3 external repairs; M6 repair review with correct root proof; composition
   repair review. Do not merge with open demonstrated blockers. Keep main bitacora/code commits separate and preserve unrelated changes.
4. Queued briefs already written: F1-B, F4-2 M5, F4-5 M3, F4-7 policy/capability/default, F4-9 owner wiring, F4-8 benchmark.
   Respect their dependency base and ownership; inspect accepted APIs after repairs. Particularly F4-9 must bind publication
   to exact M6 evidence, invalidate stale SP publication facts after redo, wire multi-ledger dedup and code-retry accounting.
5. Close phases in order per D-125, run F5 real-entrypoint stub-agent demo/docs/benchmark, archive evidence then clean only
   authorized temp worktrees/branches. Final report <=30 Spanish lines with decisions/metrics and held-run resume commands.

Communication: Spanish, every user-facing message starts Aye. Bitacora English. No owner questions unless a genuinely
irreversible action falls outside original CONTRACT. Native team is stopped; CLI workers/background tests may survive.
