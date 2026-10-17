# Three difficult analyses across five model routes

## Outcome

Sonnet high returned all three valid reviews, found 24/24 frozen roots, and led this batch in raw total tokens (44,821) and summed latency (161.529s): 26.9% fewer tokens and 16.1% less time than Sol high. This measures the tested configurations, not general superiority or exact subscription cost. Four routes completed all cases; Gemini returned two reviews and timed out on the third. Correct root detection does not guarantee every proposed correction is safe.

## Protocol and scope

The owner requested three additional, very complex analyses with every model from the prior ladder. Fifteen target calls use identical user input per dossier. The three dossiers cross authoritative requirements, verified protections, candidate code, lifecycle traces and superseded design memos. Each has eight predeclared independent defects; 24 frozen roots in total. Oracle SHA-256: `89191bd81ed11151889cd62d5dfcc94111be3cbf5a281af869889c3558853e15`. Arithmetic and modeled counterexample checks ran before model calls. Models never receive the oracle.

Sol, Sonnet and Gemini remain at high; Luna and Haiku at max. Full Claude model IDs are used with an effective-model guard. Codex-2 runs both OpenAI models; Claude Work runs both Claude models; Antigravity runs Gemini. There is one native call per account at a time, at most three accounts concurrently. Within accounts the model groups run sequentially. No fallback or automatic model retry is configured.

The common output contract is one JSON object, at most 12 independent findings and 1,800 whitespace-delimited words. The protocol has a 900-second deadline with a 30-second CLI watchdog allowance; Antigravity additionally receives native --print-timeout=900s. This is a new condition, not the previous ladder's 900-word/300-second setting.

This pilot is outside the formal REQ-024 corpus, frozen manifest and T19 reviewer records. One synthetic run per cell is not a statistical capability ranking. Coordinator adjudication is explicit and non-blind. Quota is coarse account telemetry, can lag or include other activity; hidden CLI contexts/tokenizers/cache accounting differ.

## Dossiers

| ID | Analysis | Frozen defects |
|---|---|---:|
| H1 | Concurrent accounting migration and historical replay | 8 |
| H2 | Durable scheduling, budget accounting and cancellation linearizability | 8 |
| H3 | Signed encrypted export with revocation, retries and local restoration | 8 |

## Coverage and execution per dossier

Each completed cell shows frozen roots found/expected and wall seconds. Supported post-hoc discoveries are separate. A failed/no-answer cell is not scored as an intellectual miss; it delivered no review within the measured attempt.

| Dossier | Sonnet 5.5 high | GPT-6.1 Sol high | GPT-6 Luna max | Haiku 5.5 max | Gemini 3.8 Flash high |
|---|---|---|---|---|---|
| H1 | 8/8 · 45.8s | 8/8 · 62.2s | 8/8 +1 extra · 85.6s | 8/8 +1 extra · 416.8s | 8/8 · 186.3s |
| H2 | 8/8 · 60.0s | 8/8 · 69.5s | 8/8 · 79.2s | 8/8 · 358.1s | 8/8 · 130.4s |
| H3 | 8/8 · 55.7s | 8/8 · 60.8s | 8/8 · 82.2s | 8/8 · 386.3s | timeout · 930.1s |

## Measured tokens and time

Time is the sum of native call wall times, including startup/provider latency, not the total parallel experiment duration. Input includes cache creation/read. Output includes thinking; thinking is a subset, not an extra charge added to output. Missing usage is unknown, never zero. No API-dollar equivalence is inferred from subscription calls.

| Route | Graded roots | Usable JSON | Input incl. cache | Cache-read subset | Output incl. thinking | Thinking subset | Reported total | Time sum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sonnet 5.5 high | 24/24 graded | 3/3 | 24,146 | 4,986 | 20,675 | 9,242 | 44,821 | 161.5s |
| GPT-6.1 Sol high | 24/24 graded | 3/3 | 51,787 | 36,864 | 9,521 | 4,472 | 61,308 | 192.4s |
| GPT-6 Luna max | 24/24 graded | 3/3 | 48,761 | 34,944 | 31,011 | 26,427 | 79,772 | 247.1s |
| Haiku 5.5 max | 24/24 graded | 3/3 | 26,481 | 7,326 | 286,386 | 274,733 | 312,867 | 1161.2s |
| Gemini 3.8 Flash high | 16/16 graded | 2/3 | 28,728 + unknown | 0 | 47,980 + unknown | 43,507 + unknown | 76,708 + unknown | 1246.8s |

## What seeded recall does not show

The 24-root denominator stays frozen. Luna and Haiku also provide concrete finite-precision witnesses for H1: rounded Decimal division before aggregation can change the final cent. Luna's precision-28 witness and Haiku's three one-third contributions followed by -0.995 are verified in separate post-hoc JSONs; the latter is checked at precision28 and50. Sol and Sonnet raise the precision question as uncertainty. This additional finding is reported separately, with the unspecified actual precision/domain bounds disclosed.

Two kinds of correction weakness matter independently of root detection. Gemini H2 permits cleanup on local lease expiry without remote termination proof; a job can remain live/uncertain afterward. Its hash-only quota-evidence alternative cannot reproduce a lost cache snapshot. Sonnet H2 has a correct primary reconciliation rule, but its alternative of only coupling reservation expiry to the lease needs that same reconciliation rule retained. Explicit counterexamples are in `fix-counterexamples.json`.

Detailed review caveats (including arithmetic/unit slips) follow. They are not silently converted into false-positive root findings or hidden by the all-seeds-found score.

- `H2-sonnet.json`, finding 7 (unsafe_alternative): The primary rule correctly keeps uncertain executions reserved until remote reconciliation. The alternative of merely extending reservation expiry with the lease is insufficient if cleanup then frees capacity after a local lease expires while the remote job remains live/uncertain. Retain the primary reconciliation rule even with coupled renewal.
- `H2-gemini.json`, finding 6 (insufficient_alternative): Persisting allowlisted quota observations is sound. An immutable hash alone cannot reproduce inputs whose only cache copy was overwritten; a hash alternative needs retained immutable content. The dossier explicitly requires input evidence, so this is not merely an unspecified downstream preference.
- `H2-gemini.json`, finding 7 (unsafe_main_fix): The proposed cleanup rule permits release after lease expiry without requiring confirmed remote termination. A paused worker or remote job may remain live/uncertain after local expiry. R7 requires keeping its capacity occupied until reconciliation; extending the lease does not resolve that failure.
- `H1-luna.json`, finding 4 (supported_extra_with_context): The finite-precision counterexample is verified with precision28 in additional-precision-witness.json. The dossier does not specify the actual precision or domain precision bounds; do not claim a production configuration was observed. The answer says 0.01 cents where the normalized result is EUR0.01=1 cent.
- `H1-haiku.json`, finding 5 (supported_extra_with_context): The three one-third contributions followed by -0.995 expose premature rounding before the required final half-away rounding. The post-hoc witness is checked separately; Sol/Sonnet raised precision uncertainty without this concrete witness.
- `H1-haiku.json`, finding 8 (witness_unit_slip): 1000 cents plus EUR50 is 6000 cents, not1050. Replacing the delta with EUR0.50 or the new balance with6000 restores the valid stale-overwrite trace; the root and proposed version guard remain correctly identified.
- `H3-haiku.json`, finding 5 (unconfirmed_finding): This asserts a page-cache bug assuming E2 caches individual continuation pages and that signed cursors carry positions. The dossier does not specify cache granularity or that HTTP cursors are page cursors; the worker may page internally and cache the complete export. Sonnet raised this as uncertainty. It should remain conditional, not a proven independent defect.

## Before/after account quota

Percentages are USED. Each model row uses the reading immediately before its first call and after its last call. Models sharing an account run serially, but delayed service accounting can cross model boundaries; zero displayed change does not mean zero cost. All observation/reset timestamps and statuses are in the per-call records.

| Route | Account | 5h used before → after | 7d used before → after | Read status |
|---|---|---:|---:|---|
| Sonnet 5.5 high | claude-work | 7.0 → unknown% | 87.0 → unknown% | ok / http_429 |
| GPT-6.1 Sol high | codex-2 | 2.0 → 4.0% | 0.0 → 1.0% | ok / ok |
| GPT-6 Luna max | codex-2 | 4.0 → 4.0% | 1.0 → 1.0% | ok / ok |
| Haiku 5.5 max | claude-work | unknown → 10.0% | unknown → 88.0% | http_429 / ok |
| Gemini 3.8 Flash high | antigravity | 2.0 → 2.0% | 1.0 → 1.0% | ok / ok |

Final delayed account snapshot:

- codex-2: 5h 4.0%, 7d 1.0% used; status=ok.
- claude-work: 5h 10.0%, 7d 88.0% used; status=ok.
- antigravity: 5h 2.0%, 7d 1.0% used; status=ok.

## Completion evidence and limits

`cases.json` contains the frozen dossiers/oracle. `protocol.json` pins instructions, routes, output ceilings, deadlines and executable hashes. `oracle-checks.json` records the pre-call deterministic checks. Per-cell JSON retains final response, numeric usage, prompt hash, requested/effective model evidence and quota; private thinking text/raw CLI streams are not persisted by this harness.

`adjudication.json`/`grade.py` expose every manual finding-to-root mapping, supported extra and correction caveat. `execution-summary.json` retains native lane completion/failure. `validation.json` records actual closing checks. Claude response metadata confirms effective model IDs; other providers retain explicit requested IDs without separately retained effective-ID confirmation in this collector.

- `H3-gemini.json`: timeout; elapsed 930.118s; usage not reported. A failed attempt is not a passing analysis.

No Pictures/product implementation, Scheduler dispatch, approval, frozen plan, formal benchmark manifest or reviewer pair changed. P-109 remains owner-selected. This experiment measures the requested route configurations, not every possible effort level of each model.
