# F4-6 review fixes — same ev2/F4-6 worktree

Read RULES.md and original F4-6.brief.md. Work only in existing /home/david/dev/.engine-v2-wt/F4-6 on ev2/F4-6.
You are not alone: preserve other work. No push, bitacora edits or delegation. Previous implementation is committed
as 8ecc57cc. Original full-suite evidence has been recovered; do not reimplement it or repeat checks without cause.

Read independent reports F4-6-review-spec.result.md and F4-6-review-standards.result.md in this directory.
Fix these accepted findings, with fail-first behavior tests:
1. Aggregate classification must respect FINAL verdict. With all checks pass but independent review rejects,
   overall_reason_code currently returns PASS for FAIL. Rejected/undetermined evidence cannot have aggregate PASS;
   derive a compatible reason from actual final status/issues. Test public QualityEngine review rejection and other
   NEEDS_REVIEW cases, not just a helper. Preserve legacy verdict values.
2. Idempotent replay of stored legacy results bypasses read_result migration in QualityStore.reserve. Make every
   public read/replay return UNCLASSIFIED for old aggregate/per-check records while preserving original content-addressed
   bytes and hashes. Test engine.verify replay of a completed legacy result, not only get_result.
3. Lead-confirmed adjacent migration bug: validate_result_contract(read_result(old result-pass.json fixture)) raises
   RESULT_INVALID: result check reason_code is invalid because UNCLASSIFIED is rejected per check. Make normalized old
   reads valid compatibly; reject invalid classifications for current records. Cover round-trip read/validate and replay.
4. Published api-contract.json must require composition_id and manifest_sha256 together, matching runtime. Keep legacy
   payloads valid; prove malformed one-field identity is rejected by contract/runtime.
5. Extract newly introduced check-cache/history persistence and migration responsibility from the existing 810-line
   store into focused module(s), retaining store's public API, lock/transaction atomicity, old-store migration and module
   boundary. Do not add further logic to the oversized module; new modules <500 lines. A full unrelated store rewrite is
   unnecessary, but this change must stop growing the monolith and actually relocate the touched persistence responsibility.

Spec finding 3 (no production multi-ledger caller) is retained as explicit F4-9 owner-wiring work: existing evaluate_many
is the accepted M6 API; do not invent an untrusted path-list contract just to create a caller. External verification
metadata support is assigned to F4-7, do not overlap it in this repair.

Run M6 module, audit-gate/ledger/adapter tests and full suite after fixes with complete output to
/home/david/dev/.engine-v2-wt/F4-6-fix-tests.log; report totals/non-baseline failures. Commit fixes with required coauthor.
Return RULES.md format and exact final commit(s).
