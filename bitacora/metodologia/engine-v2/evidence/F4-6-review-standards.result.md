## AXIS

Standards — Engine v2 F4-6, `9bdfeabe89814e71121f1a13859a18eb20c6442e` → `8ecc57ccdae5af10418d76a15dea871466f49d17`.

## VERDICT

CHANGES_NEEDED

## FINDINGS

1. **[low, defect] The published schema accepts incomplete composition identity.** At [api-contract.json](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality/api-contract.json:35), `composition_id` and `manifest_sha256` are optional properties with no pair constraint. A payload containing either field alone therefore satisfies this JSON Schema, while runtime validation rejects it because the fields must be supplied together ([contracts.py](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality/contracts.py:218)). Consumers validating M6 evidence against the published schema can accept a composition binding M6 itself considers invalid. Add a JSON Schema dependency requiring both fields when either is present.  
   `semantic_fingerprint`: `composition-identity-pair-required`

2. **[low, defect against engineering standards] The change adds persistence logic to an oversized store module without splitting it.** [store.py](/home/david/dev/.engine-v2-wt/F4-6/skill/scripts/bt_scheduler_quality/store.py:613) adds check-history persistence and migration logic to an 810-line file; the parent version was already 788 lines. The supplied engineering standard requires splitting a file already over 500 lines before adding code. Extract the check-cache/history persistence responsibility into a focused module.  
   `semantic_fingerprint`: `oversized-store-expanded-with-new-persistence-responsibility`

## CHECKED

- Read the requested standards, reviewer skill, `CONTRACT.md`, and `ENGINE-F4.md` from `main`; reviewed the commit diff and traced M6 validation, execution, evidence serialization, store migration, cache/history behavior, adapter delivery, and audit-ledger deduplication.
- Verified old stores load additively and missing historical reason codes read as `UNCLASSIFIED`. The taxonomy, cache/history behavior, and fingerprint deduplication had no other proven defect in the inspected paths.
- `bt_scheduler_quality` tests: 164 passed. Audit-gate tests: 27 passed. `git diff --check` passed; worktree remained clean.
- Full integration and owner wiring were not checked. In particular, future M5 policy and F4-9 owner wiring are outside this F4-6 review; no finding is based on their absence.