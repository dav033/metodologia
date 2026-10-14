# REQ-007 execution handoff

Owner explicitly requested continuation and transfer to **Claude personal,
Sonnet 5.5, high** as Codex credits run low. Continue reversible local execution
of M0–M8; M9 and live cutover/account activation remain separate gates.

Read SPEC.md, PLAN.md, INVENTORY.md, ACCEPTANCE.md and evidence/EXECUTION-REVIEW.md
here. Registered PLAN in ../requirements/REQ-007-engineering-workspace-migration-without
was marked approved following the owner's `continua`; authoritative dossier still
has stale proposed/review wording. Reconcile them locally, preserving the limits.

## Critical constraints

- Do not commit, push, merge to main, delete existing files, reset, or change live
  processes/config/accounts. Owner's instructions override skill defaults.
- **Do not invoke bitacora CLI commands that call bt_vcs.commit or pull.**
  Coordinator accidentally used `plan approve`: it committed and pushed f840519
  (only plan approval + bitacora session entry) to origin/main. Owner informed.
  Do not undo history. Direct local documentation edits are safe.
- Repo /home/david/dev/metodologia has substantial unrelated uncommitted routing,
  quota, relay, Antigravity and policy work. Preserve everything. No worktree
  from HEAD alone until dirty/untracked baseline is preserved.
- /home/david/bitacora is symlink to repo/bitacora. Its .state is private and
  ignored; credentials must never enter dossier or git. Restore only to new roots.
- Execute manually by milestones: current marathon treats optional M9 as mandatory
  and audit prompts allow fixes/commits. Use independent read-only reviewers.
- User communication Spanish, start with Aye; bitacora English. Runtime hooks
  must stay disabled for this successor invocation because they auto-commit/push.
  This is invocation-local; do not change global settings.

## Current work and next steps

1. M0 implementer owns only new skill/scripts/migration_inventory*.py and
   tests/migration/test_inventory_restore.py. Coordinator will add its final
   status below before launching successor. Review and verify its implementation;
   it has NOT captured live state yet and T1 must not be ticked prematurely.
2. Baseline runner output is /tmp/req007-baseline-01a1381d.log. Actual result:
   exit 1, 578 tests in 58.748s, exactly the two known routing failures:
   test_audit_routing.py:35 and test_subscription_usage.py:88 expect Claude
   but get Codex. No additional failures. HEAD at verification was f840519.
3. Finish M0 capture/restore with explicit inventory, private permissions,
   observed-consistency limits, concurrent ownership and source/consumer hashes.
   Then T2 ADR and M1 baseline repairs per current owner policy (Gemini audit).
4. Proceed by dependency, preserve compatibility and verify each milestone.
   Live cutover and optional account activation require later explicit approval.
5. Update bitacora directly, no VCS-enabled CLI. Existing session entry is
   2026-10/W3/2026-10-13.md section 01a1381d; successor creates its own section
   using safe mechanics with automatic VCS callbacks disabled if necessary.

## Verification state

Independent read-only plan review completed: two accepted automation findings,
no additional blocker for manual M0/M1. Actual implementation verification and
source/state restore are still pending. No implementation completion claimed.

M0 implementer will leave a report in /tmp/req007-m0-implementer.txt. Read it
as claims and independently inspect/test before capturing any real state.

## Status update — session 862a2e59 (claude-personal, Sonnet 5.5, high), 2026-10-13 22:25

Done locally, nothing committed or pushed: T1, T3, T4, T5, T6 (see PLAN progress log and
evidence/M0-PRESERVATION.md, evidence/COMPATIBILITY-MATRIX.md, DECISIONS D-013).

- Verify: `cd /home/david/dev/metodologia && PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -q`
  (627 tests; 579 legacy collected in place + 48 migration).
- Backup root `~/.local/share/metodologia-migration/baseline-m0-01/` is private (0700); repeat the capture
  before any cutover (observed consistency only).
- Open: T2 (ADR still "proposed"), independent review of M0-M2, then M3/T7 driver contract. M9 stays gated.
- Concurrent dirty work of other sessions was preserved; my hunks in shared files are listed in the day log.

## Status update 2 — session 862a2e59, 2026-10-14 00:15
T5 and T6 done (re-review APPROVED); T7 partial (additive `bt_driver.py` + 15 fake-CLI tests); T8 characterization only.
D-014 (debate + judge) keeps the ADR provisional: ratify T2 before any structural move, supervisor wiring, T8 scheduling
or M4+. Verify with `discover -s tests` (666 tests). The artifact summarizing the whole run is linked from the day log.

## 2026-10-14 — ADR ratified (D-015)
T2 closed. Next unblocked block: incremental src/ move behind sys.modules aliases, T7 supervisor wiring behind a flag, T8 bounded cold-start scheduling with tests, then M4 (dry-run first, no live config).

## 2026-10-14 — session 790c0548 (claude-personal)
T7 and F-M1-01 closed (see PLAN progress log). Suite 829 OK. Open: live `m6-*` evals, Windows/macOS (owner: not yet), src/ move (deferred), commit separation (owner). Still no commit/push.
