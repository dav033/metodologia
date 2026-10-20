# Candidate amendment review and validation

Draft revision 2; same-context semantic self-review plus separate read-only adversarial review. No owner approval, freeze, revision application, runtime change or live task repair occurred.

## Deterministic validation

Direct detached check: `python3 -m bt_planner check /home/david/bitacora/metodologia/requirements/REQ-029-autonomous-recovery-from-repeated-audit/conflict-amendment --plan-id REQ-029 --repo skill=/home/david/dev/metodologia --json` returned exit 2. Errors: `["plan.revision: next revision is 1, got 2"]`. The only remaining direct check error is expected: the detached candidate deliberately has no frozen revision store, so it expects revision 1. Its PLAN.json remains revision 2; no fake approval/store was added.

Contextual isolated check: `python3 -m bt_planner check /home/david/.local/tmp/req029-candidate-check-9gfdutgt/REQ-029-autonomous-recovery-from-repeated-audit --plan-id REQ-029 --repo skill=/home/david/dev/metodologia --json` returned exit 0, `ok=True`, 0 errors and 46 warnings. The temporary directory held exact candidate SPEC/PLAN bytes and exact read-only copies of existing canonical r1 MANIFEST/PLAN; no new revision or manifest entry was created. Temporary files were cleaned after the non-mutating official check.

Copied r1 source digests (source bytes equalled copy bytes):

- `PLAN.r1.json`: `64d87ffffa199c2240e52026d51885f7aca88dfcb10d95b77c00ea834efb3e8b`
- `MANIFEST.json`: `a250f11ddc77cc99a1c0c2b63c1f2b7dc50325400ce03e7f78c7a7ed760fa379`

Contextual check complete warnings (planned work is not proof):

- T1.verification[0]: created_by 'T1' is planned work, not existing evidence
- T2.verification[0]: created_by 'T2' is planned work, not existing evidence
- T3.verification[0]: created_by 'T3' is planned work, not existing evidence
- T3a.verification[0]: created_by 'T3a' is planned work, not existing evidence
- T3b.verification[0]: created_by 'T3b' is planned work, not existing evidence
- T4.verification[0]: created_by 'T4' is planned work, not existing evidence
- T4a.verification[0]: created_by 'T4a' is planned work, not existing evidence
- T5.verification[0]: created_by 'T5' is planned work, not existing evidence
- T5a.verification[0]: created_by 'T5a' is planned work, not existing evidence
- T6.verification[0]: created_by 'T6' is planned work, not existing evidence
- T6a.verification[0]: created_by 'T6a' is planned work, not existing evidence
- T7.verification[0]: created_by 'T6' is planned work, not existing evidence
- T7.verification[5]: created_by 'T6' is planned work, not existing evidence
- T7.verification[6]: created_by 'T6a' is planned work, not existing evidence
- T8.verification[0]: created_by 'T6' is planned work, not existing evidence
- T9.verification[0]: created_by 'T6' is planned work, not existing evidence
- T10.verification[0]: created_by 'T10' is planned work, not existing evidence
- T11.verification[0]: created_by 'T11' is planned work, not existing evidence
- T11.verification[1]: created_by 'T11' is planned work, not existing evidence
- T13.verification[0]: created_by 'T11' is planned work, not existing evidence
- T13.verification[1]: created_by 'T11' is planned work, not existing evidence
- T13.verification[6]: created_by 'T6' is planned work, not existing evidence
- T13.verification[7]: created_by 'T6a' is planned work, not existing evidence
- T14.verification[0]: created_by 'T6' is planned work, not existing evidence
- T15.verification[0]: created_by 'T6' is planned work, not existing evidence
- T16.verification[0]: created_by 'T6' is planned work, not existing evidence
- T17.verification[0]: created_by 'T11' is planned work, not existing evidence
- T17.verification[1]: created_by 'T6' is planned work, not existing evidence
- T18.verification[0]: created_by 'T6' is planned work, not existing evidence
- T19.verification[0]: created_by 'T6' is planned work, not existing evidence
- requirements.R1: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R2: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R3: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R4: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R5: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R6: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R7: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R8: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R9: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R10: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R11: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R12: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R13: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R14: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R15: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance
- requirements.R16: Planner review whether user-visible/product claims need product-level verification; product-category verification is only planned work, not existing evidence; lower-level tests are not product acceptance

`python3 -m bt_planner validate <candidate>/PLAN.json --json`: exit 0, ok=True. This validates schema/content alone; it does not compare SPEC or prove execution. The contextual full check above additionally compares SPEC/PLAN, graph, coverage, interfaces and inspected repository file references.


## Semantic self-review

This section is same-context self-review, not independent approval. Independent read-only review is reported separately below.

| Category | Severity | Concrete trigger and provenance | Correction in candidate |
|---|---|---|---|
| Demonstrated source defect | High | `bt_scheduler_integrator._merge` clips six paths/170 characters before any durable full publication | T3b captures immutable full source identities/paths before display clipping; incomplete legacy reconstruction blocks |
| Demonstrated source defect | High | `_dependents_to_redo` discards `limit: T15b was already sent back 2 time(s)` and `_deliver_one` rejects candidate | T3b retains exact refusal; T5 routes unchanged/exhausted structural observations to the existing case, T4 grants new scoped convergence work without resetting counters |
| Demonstrated source defect | Medium | `bt_block_diagnosis.CONFLICT` recognizes start prefix only; recorded M6 reproduction yields code/retry_with_note | T10 corrects both views/prefixes, retaining structured evidence as authority and testing actual origin wording |
| Demonstrated naive-plan defect | High | A convergence task after both incompatible sources would fail ordinary base_ref before starting | IF-10, T3b/T4/T4a/T5 define exact source-bound unresolved bootstrap, single-order M1 grant, M3 base resolver and accepted C downstream; T6a proves bootstrap and denies unauthorized use |
| Demonstrated contract contradiction corrected | Medium | A stale classification could take precedence over simultaneous scope or semantic blocker | T3a explicit stop/evidence/scope/semantic precedence; mixed cases in T3a/T6a deny actions |
| Demonstrated source fail-open risk | High | `_integration_problem` catches exception and returns empty string, allowing an otherwise PASS result | T3b requires evidence_unavailable pending/blocked for structural publication/recompute outage; T6a drives M6 PASS plus failing sink |
| Fact | High | REQ027 DAG already orders T3/T15/T15a/T15b/T15c; att0142 stale descendant precedes replacement att0204; exact web deltas show no demonstrated scope escape | T3a/T4a forbid overlap-only ownership rewrites and demand causal proof; T6a replays ordered stale lineage rather than fabricating a missing edge |
| Plausible risk | High | Revisions, new finding IDs or conflict labels mint a second cycle; owner rework resets budgets | T3a/T4/T5 correlate one cycle, prohibit owner=True/answer(by=owner) bypass, use explicit new-task authority and preserve all ordinary counters |
| Plausible risk | High | One-side-only green, marker-free text or an edge change looks resolved but drops accepted behavior | T4a/T6a/T11 require both frozen behavior checks and symptom oracle on the same actual accepted convergence tree, independent audit/cross-check and downstream base proof |
| Product decision retained | High | Candidate extends conditional REQ027 activation policy while owner goal is paused | Draft scope only: paused goal blocks activity, owner approval/workflow remains final, no freeze/rebase/resume occurred |

Responsibility review: T3a/T3b/T4a/T6a and amended implement tasks author code/tests/fixtures; T7/T13/T17 run established commands and report failures only; audits write their report/one findings ledger, never code or repairs. Documentation remains T12. Historical accepted T2 and future T3b adapter changes are ordered; no accepted scope was deleted and no four-task same-file chain was introduced.

Calibration review: all four new implementation tasks remain high because contract/state correlation, complete source lineage, grant bootstrap and real-process crash replay are substantive reasoning boundaries. Existing command-running tasks remain medium because they do not author the missing harness. No measured comparable duration, retry, quality or quota claim is made; queried history is unknown. File presence proves only T12 documentation existence, never behavioral acceptance. Every audit follows T7/T13/T17 real-entrypoint integration and owns one ledger.

Traceability review: all R1–R16 have covers paths and corresponding categorized verification; original accepted T1–T3 objects match exactly. New IF-7–IF-10 name producer/consumers and integration acceptance; T4 API precedes T4a strategy construction, and T5 consumes both without a compile-time cycle. No unowned type/function is assumed: T3a defines conflict envelope/policy, T3b evidence/bootstrap, T4 authorization/application, T4a convergence work, T5 composition. Review focus in PLAN.md gives five concrete uncovered input classes and owning test tasks.

## Independent adversarial review

A separate read-only agent reviewed candidate/source evidence and returned no open critical/high findings after corrections. It independently confirmed the full T1–T3 task objects are equal, audit file/ledger limits, test-vs-authoring responsibility and mandatory both-side integrated proof. Its detected bootstrap high issue and precedence medium issue were corrected before the final candidate. A follow-up read explicitly confirmed the M6 PASS + failing sink negative and mixed stale/scope/semantic cases in T3b/T6a, closing its last medium observation. Final reviewer statement: “No quedan hallazgos abiertos de esta revisión. El comportamiento sigue pendiente de implementación y pruebas.”

The independent review did not approve/freeze the plan and ran no live operations/providers or implementation tests. Its direct detached check encountered the expected revision-store context error; the planner additionally executed the isolated contextual official check documented above, with exact r1 evidence copies and no r2 manifest entry.

## Remaining limitations

No production/integration behavior has been implemented or tested by this planning task. Historical full collision paths still require exact disposable reconstruction; the approved-source diffs in DELTA.md are complete differences, not a complete merge-conflict list. Runtime bootstrap, counter-preserving grants, union-verification coverage and safe publication must fail the planned negatives before rollout. A genuine incompatible product meaning, missing authority or unprovable evidence remains a specific targeted blocker.

PLAN.mmd is derived only from the validated PLAN.json task IDs/after edges. ID and edge construction was checked deterministically; Mermaid syntax was not rendered in this planning task. The diagram does not contain schedules, execution assignments or a separate plan authority.
