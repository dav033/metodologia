AXIS: spec  
VERDICT: CHANGES_NEEDED

FINDINGS:

1. **[medium] A rejected verification review can be recorded as `PASS`.** When independent review returns `REVIEW_REJECTED`, M6 changes the verdict status to `FAIL` ([engine.py](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality/engine.py:264)). But if every check passed, `overall_reason_code` falls through to `PASS` for that non-PASS verdict ([evidence.py](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality/evidence.py:436)). This gives downstream recovery a passing classification for rejected evidence. Derive the aggregate code from the final verdict and review issue so a rejected result cannot be classified `PASS`, using the agreed taxonomy.  
   `semantic_fingerprint`: `45e67cc7b6d9def99d135aa7c7a205dffbd5835fab356db22d5d798146edfc03`

2. **[medium] Idempotent replay skips the legacy `UNCLASSIFIED` migration.** `QualityStore.reserve` returns the stored JSON unchanged for a completed request ([store.py](/home/david/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality/store.py:138)); `QualityEngine.verify` returns that value directly ([engine.py](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality/engine.py:90)). Thus, after upgrade, replaying a completed schema-1 request returns no aggregate or per-check `reason_code`, while `get_result` correctly adds `UNCLASSIFIED` ([store.py](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality/store.py:268)). Route the replay result through the compatibility reader and cover that path.  
   `semantic_fingerprint`: `22b670b20bc70cb60fb915c42bb4733c9758c48b561788e78a5b866e4b13dcc6`

3. **[medium] Cross-ledger deduplication is not used by the audit verdict path.** `evaluate_many` merges matching fingerprints ([bt_audit_gate.py](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_audit_gate.py:238)), but the adapter’s production audit path calls `evaluate` on one ledger ([bt_scheduler_quality_adapter.py](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality_adapter.py:414)); repository call-site search found no caller of `evaluate_many` outside its tests. When two auditor ledgers report the same finding, this path cannot deduplicate them before deciding rework. Pass the independent ledgers together through `evaluate_many` at the verdict gate.  
   `semantic_fingerprint`: `cab4aa7c81285197a996c2bb494b8311a3a5cc90ef102a85e5c96997186ffb9f`

CHECKED:

- Reviewed commit `8ecc57ccdae5af10418d76a15dea871466f49d17` against its parent, the specified F4 contract sections, ENGINE-F4 §§0, 2, 3 M6, the brief, and the evidence-based-findings skill. The brief’s `/home/david/dev/.engine-v2-wt/RULES.md` was absent.
- Traced reason-code creation, result/manifest persistence, `m6://result/<sha256>` verdict evidence, FAIL→PASS history on shared evidence keys, legacy order hashes, cache binding, finding validation/dedup, and composition/tree fields.
- Confirmed optional order fields are omitted from legacy serialization when absent; supplied contract/environment identities enter the cache fingerprint; composition identity and tree digest are included in evidence. No defect found in those paths.
- No tests run. Coverage gap: behavior when multiple auditor ledgers are combined through the actual verdict path is not exercised by a production caller in this revision.