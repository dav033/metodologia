# Implementer pilot: eight configurations, six increasing-difficulty cases

Owner-authorized native implementation pilot; outside formal REQ-024. Single repetition per cell. No role assignment or runtime policy change.

Evidence: 48/48 calls returned; 48 started.

| Configuration | I1 | I2 | I3 | I4 | I5 | I6 | Fully passed | Seconds | Tokens (coverage) |
|---|---|---|---|---|---|---|---:|---:|---:|
| luna-medium | PASS | PASS | PASS | PASS | PASS | FAIL | 5/6 | 142.644 | 696,169 (6/6) |
| luna-high | PASS | PASS | PASS | PASS | PASS | PASS | 6/6 | 204.846 | 882,938 (6/6) |
| luna-xhigh | PASS | PASS | PASS | PASS | PASS | PASS | 6/6 | 392.907 | 1,058,540 (6/6) |
| sol-medium | PASS | PASS | PASS | PASS | PASS | PASS | 6/6 | 248.202 | 421,245 (6/6) |
| haiku-medium | PASS | PASS | PASS | PASS | PASS | FAIL | 5/6 | 286.373 | 609,338 (6/6) |
| haiku-high | PASS | PASS | PASS | PASS | PASS | PASS | 6/6 | 397.807 | 969,297 (6/6) |
| haiku-xhigh | PASS | PASS | PASS | PASS | PASS | FAIL | 5/6 | 694.700 | 1,740,646 (6/6) |
| sonnet-medium | PASS | PASS | PASS | PASS | PASS | PASS | 6/6 | 124.608 | 175,569 (6/6) |

## Cases and verification

I1 interval bugfix; I2 repository/service/CLI cursor pagination; I3 deterministic DAG state; I4 atomic SQLite migration; I5 concurrent lease claims/fencing; I6 crash recovery/dependencies/retry/atomic outbox/replay/deduplication.

Frozen reference suite: 12 + 14 + 14 + 11 + 11 + 17 = 79 tests. Every reference passes and every starting fixture fails intended behavior. Representative mutants fail. Fresh spec/standards audit corrections were applied before freezing.

Candidate runs receive the same prompt/code per case in independent working trees. Native Bubblewrap masks benchmark artifacts/oracles and sibling /tmp cells; other host files remain read-only, and CLI profile state is writable. The shared instructions prohibit inspecting other repositories/accounts. The coordinator grades submitted app/ with original public and withheld private tests in a separate, minimal, networkless sandbox. Protected-file/scope violations prevent a full pass. Per-cell test output, native status, identity evidence, quota observations, patch and source hashes are retained.

## Interpretation limits

- These are synthetic Python/SQLite backend cases. Results do not establish general superiority, frontend quality or equivalent performance in other languages.
- Native tools, caches, tokenizers and harness prompts differ. Equal effort names are not equal compute.
- Model/effort requests are pinned. Claude stream-reported model identities are retained; absence of runtime attestation is not proof of an effective model/effort.
- Tokens include cached context. Codex total = input + output; Claude total also includes cache read/write. Partial counters are lower bounds, unknown counters are null. Tokens are not subscription quota or invoices.
- Time/consumption comparisons are meaningful among equally successful configurations; account quota may include simultaneous unrelated sessions.
- No coordinator code repairs, quality retries or silent route substitutions. Read execution-summary.json for operational incidents before ranking results.

## Separate posthoc adjudication

The original table above is unchanged. I6 did not explicitly fix outbox.body encoding; Luna medium and Haiku medium used JSON {id,result}; Haiku xhigh used {job_id,result}, while five original assertions per candidate expected the raw result. Those mismatches reflect one oracle ambiguity, not five demonstrated model defects each. A separate, uniformly applied supplement accepts raw results or minimal JSON with exact result and an optional matching id/job_id, while preserving atomicity, order, replay and byte-for-byte inbox deduplication. No submissions were repaired and no native model calls repeated.

A second posthoc witness tracks real SQLite connections and checks closure on return/error, as explicitly required in I4–I6. This reveals an independent I6 Luna medium defect: sqlite3.Connection used as a context manager commits/rolls back but does not close. References pass both supplements; an incorrect JSON-result mutant fails. An initial optional-I5-API resource probe was excluded and preserved in supplement-resources-excluded-v1.json; the valid witness gates APIs by case ID.

| Configuration | Original cases | Cases after semantic/resource adjudication | I6 semantic | I6 connection closure |
|---|---:|---:|---|---|
| luna-medium | 5/6 | 5/6 | True | failed |
| luna-high | 6/6 | 6/6 | True | passed |
| luna-xhigh | 6/6 | 6/6 | True | passed |
| sol-medium | 6/6 | 6/6 | True | passed |
| haiku-medium | 5/6 | 6/6 | True | passed |
| haiku-high | 6/6 | 6/6 | True | passed |
| haiku-xhigh | 5/6 | 6/6 | True | passed |
| sonnet-medium | 6/6 | 6/6 | True | passed |

Resource witness `I6-luna-medium`: 21 failing subtests, 23 usable connection observations across operations. These are distinct counts: the publish operation leaves three connections usable.

Runtime model identity is unattested in saved CLI output for: luna-medium, luna-high, luna-xhigh, sol-medium. Requested identities are preserved; no effective identity is inferred. Claude streams report claude-haiku-5-5 or claude-sonnet-5-5 as requested. No CLI stream attests effective effort for any configuration.

Closure audit: all 48 result cells, 48 START/DONE pairs, eight complete six-case configurations, 79 mandatory methods per configuration and frozen input hashes verified. All eight I6 semantic supplements pass; 23/24 resource witnesses pass, with only I6 Luna medium failing. Original native results are immutable. See closeout-audit.json for integrity checks and regeneration exit codes.

Supplemental evidence is labeled posthoc and is distinct from the frozen benchmark score. See supplement-provenance.json, supplement-semantics.json and supplement-resources.json.
