# Sol / Sonnet medium versus high: three difficult cases

## Interpretation

Within these three cases, high did not increase seeded detection or verified extra findings for either model. Sol medium and high both found the additional remote-worker epoch-fencing defect and proposed a suitable guard. Both Sonnet efforts treated that risk as uncertainty and their convergence/key suggestions do not prevent the demonstrated stale-command regression. Sonnet high improved some E1 detail but added an unsupported E2 cardinality aside; there is no consistent measured quality gain from high here.

Sonnet medium used the fewest raw total tokens (41,002); Sol medium produced the fewest output/thinking tokens (7,000) and had the strongest grounded correction record in these particular answers, with nearly equal time to Sonnet medium. High raised Sol total tokens/output/time by 4.5%/44.6%/55.1%, and Sonnet by 11.0%/26.8%/29.2%. This supports starting these review workloads at medium and escalating on a demonstrated unresolved issue, while leaving general production effort policy undecided.

## Scope and method

The owner authorized 12 native calls: identical input per case to each model/effort route. Cases contain 31 frozen expected roots (11/10/10). Each response has the same one-JSON/12-findings/1,800-word ceiling and 900s deadline plus 30s watchdog allowance. Codex-2 and Claude Work run one call at a time each, in parallel account lanes; effort order alternates per case and between lanes. Every cell uses a fresh ephemeral session with tools disabled/requested unused. Full Claude IDs are checked; requested effort is captured in flags, not independently attested by response metadata. Codex effective identity is not separately retained by this collector.

Oracle SHA-256: `a3d9f7b9386ec04c4918d2f993db71d6fcd9ff477d9b8e05834d840ec3c14902`. Thirty-one deterministic arithmetic/modeled-trace checks ran before provider calls. These are synthetic dossier witnesses, not product integration tests. `PLAN.md` fixes adjudication criteria. Answers were shuffled and stripped of route/effort before coordinator adjudication; the saved blind judgements preceded unblinding. Writing style may reveal identity. This is not independent external judging, a statistically powered benchmark, or the formal REQ-024 corpus.

## Dossiers

| Case | Scenario | Frozen roots |
|---|---|---:|
| E1 | Multi-region transfer cutover, replicated decisions and escrow recovery | 11 |
| E2 | Bitemporal marketplace settlement, exact optimization and adversarial rounding | 10 |
| E3 | Hermetic build reuse, attested deployment and concurrent artifact garbage collection | 10 |

## Results

| Route | Roots found | Valid JSON | Total tokens | Input incl. cache | Cache-read subset | Output incl. thinking | Thinking subset | Wall sum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sol 6.1 medium | 31/31 | 3/3 | 58,840 | 51,840 | 36,864 | 7,000 | 1,086 | 124.927s |
| Sol 6.1 high | 31/31 | 3/3 | 61,491 | 51,369 | 36,864 | 10,122 | 4,310 | 193.713s |
| Sonnet 5.5 medium | 31/31 | 3/3 | 41,002 | 24,134 | 13,544 | 16,868 | 5,155 | 128.546s |
| Sonnet 5.5 high | 31/31 | 3/3 | 45,530 | 24,135 | 9,225 | 21,395 | 8,797 | 166.021s |

Input includes cache creation/read where applicable. Thinking is already included in output and is never added twice. Wall sums include native startup/provider latency; they are not the parallel experiment duration. Tokenizers, hidden CLI context and cache differ; raw totals are not equal monetary or subscription cost.

## Matched effort differences

| Model | High minus medium roots | High vs medium total tokens | High vs medium output | High vs medium time |
|---|---:|---:|---:|---:|
| sol | +0 | +4.5% | +44.6% | +55.1% |
| sonnet | +0 | +11.0% | +26.8% | +29.2% |

## Per-case results

| Case | Route | Roots | Total tokens | Output | Time |
|---|---|---:|---:|---:|---:|
| E1 | Sol 6.1 medium | 11/11 | 19,857 | 2,463 | 42.072s |
| E1 | Sol 6.1 high | 11/11 | 21,609 | 4,211 | 78.386s |
| E1 | Sonnet 5.5 medium | 11/11 | 14,818 | 6,862 | 52.529s |
| E1 | Sonnet 5.5 high | 11/11 | 16,416 | 8,459 | 66.495s |
| E2 | Sol 6.1 medium | 10/10 | 19,640 | 2,230 | 41.292s |
| E2 | Sol 6.1 high | 10/10 | 19,518 | 2,585 | 49.221s |
| E2 | Sonnet 5.5 medium | 10/10 | 13,102 | 5,085 | 38.813s |
| E2 | Sonnet 5.5 high | 10/10 | 14,205 | 6,186 | 47.623s |
| E3 | Sol 6.1 medium | 10/10 | 19,343 | 2,307 | 41.563s |
| E3 | Sol 6.1 high | 10/10 | 20,364 | 3,326 | 66.106s |
| E3 | Sonnet 5.5 medium | 10/10 | 13,082 | 4,921 | 37.204s |
| E3 | Sonnet 5.5 high | 10/10 | 14,909 | 6,750 | 51.903s |

## Correction quality, additional findings and uncertainty

Seeded detection and correction soundness are separate. The following notes preserve the route-hidden judgements; supported extras do not enlarge the denominator. Absence of a note means no concrete additional error was established in this review, not a proof of universally correct repairs.

- **E1 / Sonnet 5.5 high**: Findings 10 and 11 separately discuss miss-path and cache-path branch binding. Both count once toward frozen root E1-D10; the cache recommendation adds useful repair detail without increasing seeded coverage.

- **E1 / Sonnet 5.5 medium**: Finding 11: the primary permanent transfer-tombstone fix is sound, but the alternative of merely never pruning source ledger operation-key dedup is insufficient under G2's epoch namespace if completed transfer rows are still removed. A retry in a new epoch can consume rights again. The counterexample in correction-checks.json assumes no unmentioned global lookup/uniqueness mechanism; retaining one would repair this alternative.

- **E1 / Sonnet 5.5 medium**: Finding 3: an across-epoch lookup alone must not be interpreted as atomic uniqueness or proof that no delayed prior append can still succeed. The explicit global-dedup option is sound; original-epoch reuse is conditional on the ledger accepting/reconciling that namespace, which the answer acknowledges.

- **E2 / Sonnet 5.5 high**: Finding 6's parenthetical claim that cheapest-first can potentially fail the primary cardinality objective is unsupported under the complete independent eligible list and nonnegative costs. It does maximize count; the secondary-net counterexample is correct and still establishes the frozen root. See the minimal-prefix proof in correction-checks.json.

- **E2 / Sonnet 5.5 high**: Finding 8 correctly identifies premature money release, but its witness conflates a resource cost of 10 with released monetary funds/capacity. B8 does not establish resource-capacity release; use a separate concrete monetary reservation witness.

- **E2 / Sonnet 5.5 medium**: Finding 8 correctly establishes unsafe reuse of money, but its witness describes release of daily resource capacity. B8 releases money, and G1 independently guarantees resource-capacity accounting. State the witness in monetary units; daily capacity release is not established by the snippet.

- **E3 / Sol 6.1 high**: Finding 9 supplies the same supported additional remote-fencing root with a concrete delayed-command trace and sound epoch fence or serialization fix. This remains separate from frozen E3-D8 (ACK-before-CAS).

- **E3 / Sol 6.1 high**, finding 9: extra `remote-epoch-fence`; see judgement notes.

- **E3 / Sol 6.1 medium**: Finding 9 supplies a supported additional failure independent of ACK ordering: distinct-key delayed older remote activation can overwrite a newer worker epoch. Its worker-side atomic epoch fence/complete serialization fix addresses the supplied R5 constraint. Kept separate from the frozen denominator.

- **E3 / Sol 6.1 medium**, finding 9: extra `remote-epoch-fence`; see judgement notes.

- **E3 / Sonnet 5.5 high**: Finding 4 repairs ACK ordering, but its wider CAS-before-dispatch/epoch-bearing-key/eventual-reconciliation recommendation does not guarantee R5's remote monotonicity. Coordinator 11 can win its CAS, pause, then dispatch after coordinator 12 has committed and activated; distinct keys do not fence this. The uncertainty acknowledges the missing worker fence but does not present it as the independently proven extra. Preserve this limit rather than treating eventual convergence as prevention.

- **E3 / Sonnet 5.5 medium**: Finding 8 repairs the local ACK issue, but epoch-bearing keys and re-pushing authoritative state alone do not prevent a delayed previously winning coordinator from remotely overwriting a newer activation. The answer leaves this as uncertainty despite the supplied API semantics permitting the counterexample. A worker-side fence or complete per-worker command serialization is needed for the separate R5 remote invariant.

## Account quota before and after

Percentages are USED. Efforts interleave on the same account; first/last route boundary readings overlap other effort calls and cannot identify effort-specific consumption. Rounded service telemetry can lag and include unrelated activity. Missing or HTTP429 readings remain unknown; unchanged displayed values do not mean zero cost. Every before/after/reset/status sample is preserved in its cell.

| Account | 5h before → delayed after | Weekly before → delayed after | Status |
|---|---:|---:|---|
| codex-2 | 4% → 7% | 1% → 1% | ok / ok |
| claude-work | 10% → 14% | 88% → 88% | ok / ok |

Non-ok per-call quota reads: `[]`.

## Evidence and limits

`cases.json` contains the frozen input/oracle; `oracle-checks.json` the pre-call witness checks; `protocol.json` the routes, order, limits and executable hashes; `runtime-versions.json` the native versions; 12 cell records contain final answers, usage and metadata. Raw/private thinking text is not saved. `blind-answers.json`, `blind-judgements.json` and `blind-key.json` expose the grading/unblinding trail; `adjudication.json` records exact root mappings, extras and metrics. `validation.json` retains actual closeout checks.

One run per route/case cannot estimate failure probability or prove general effort superiority. Cases are dense with explicit snippet/contract references; this helps isolate review reasoning but does not measure repository exploration, coding, long-session execution or undisclosed production complexity. Fixes are judged against the supplied contracts, not implemented in product code. Cache/order and runtime overhead remain confounders. No reviewer selection, formal benchmark freeze, Scheduler dispatch, source implementation or routing-policy change occurred.
