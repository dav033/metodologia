# Resume F4-1c — complete the interrupted repair in the SAME worktree

Read /home/david/dev/.engine-v2-wt/RULES.md fully, original F4-1.brief.md and F4-1b.brief.md at that same external
directory, plus CONTRACT.md/ENGINE-F4.md §§0–1 under /home/david/dev/metodologia/bitacora/metodologia/engine-v2/.
Work ONLY in /home/david/dev/.engine-v2-wt/F4-1 on ev2/F4-1. Previous worker stopped for a misleading inherited
quota/relay reminder, NOT a technical blocker. It is no longer active. Inspect git status/diff first and preserve
its uncommitted tests/implementation; do not repeat completed work. You are not alone; other worktrees have other writers.
No bitacora writes, push, relay, handoff or delegation. No held-run state/process access.

Read independent reports F4-1-review-spec.result.md and /tmp/engine-v2-F4-4-standards-review.md only if relevant;
the exact accepted composition repair requirements below govern (the /tmp file is routing context, not composition).
Native Antagonist/standards reproduced these blockers; finish each with fail-first real-Git/crash/concurrency tests:

1. Unsafe cleanup: reject workspace_root/repository overlap in BOTH directions. prune_workspaces must delete ONLY
   durably owned allocations proven orphaned, never unknown/foreign/active/locked worktrees. Ignore no Git error;
   remove rmtree fallback after a failed git worktree remove. Conservative retention is correct without orphan proof.
   Preserve crash cleanup for genuinely owned orphans. Test main checkout nested under root, active/foreign/locked,
   owned dead-owner orphan and Git removal failure, all data retained when required.
2. Ref namespace symref escape: update-ref --stdin defaults to dereference. An admitted current→refs/heads/main can
   move main despite OID validation. Use transactionally no-deref operations/symref protection; real Git regression
   proves target branch remains unchanged. Validate all refs/OIDs, no newline injection.
3. Migration atomicity: explicit BEGIN IMMEDIATE before ANY DDL; crash after candidates→candidates_v0 rename must
   roll back/recover, never create empty candidates and mark upgraded. Reject unsupported schema without mutation.
4. Publication crash ownership: ref v1 may exist after SQLite failure; another request with same commit but different
   revision/contracts must NOT adopt it. Persist durable reservation binding number+request hash+manifest BEFORE Git
   publication, recover original request idempotently. Test competing same-OID requests and crash interleavings.
5. Serialize publish/reject read/transition/write. Reject cannot read candidate then overwrite published state after
   concurrent publish. Reconcile refs before reject after a publish crash; published refs and store stay consistent.
6. Diagnostic fold must retain interactions involving rejected members: A changes x; B changes x+y; C changes y;
   report both A/B:x and B/C:y, not only B:x. Rejected candidate never publishes; collect actual member/path conflicts.
7. Stable manifest identity: exclude mutable lifecycle state/verdicts from candidate identity hash, which must stay
   equal across open/verify/publish. publish accepts typed verdict proof bound to exact composition id, stable manifest,
   evaluated candidate commit/tree and verifier/evidence identity, NOT bare {'M6':'PASS'}. Stale/wrong-candidate proof
   cannot publish. Public API change is authorized before M3/owner consumers exist; update all module/integration callers.
   Interrupted work already introduced VerdictProof and partial migrations/reservations: inspect and complete them.
8. Empty EvidenceKey.paths can never prove equivalence/reuse, even with equal digest/contracts/environment. Fail closed
   at public boundary and prove propagate cannot suppress reverify with an empty relevant-path set.

The spec review's run_base override finding is DISMISSED: ENGINE-F4 §1 starts from published current and only uses
run_base for bootstrap. Preserve current-first semantics; clarify docs/test instead of dropping accepted composition.

Owned files remain composition package, adapter, tests and existing packaging entries. New small helpers allowed.
Run focused module+integration then full suite, capture COMPLETE /home/david/dev/.engine-v2-wt/F4-1c-tests.log. Commit
with required coauthor and structured final per RULES; if truly blocked, return precise state/Next to lead without relay.
