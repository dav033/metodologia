# Runner pilot — partial closeout report

PARTIAL: 15/24 authorized native cells executed; nine never invoked. Claude stopped on an HTTP429 from its usage telemetry endpoint before N2 Haiku, not a native model limit. Codex completed its lane. No native repair/retry or account switch. See RESUME.md and pending-cells.json.

Owner-authorized four configurations × six local cases. Original results and full fixture logs are preserved separately from grades. The table uses the explicit adjudicated semantic assessment.

| Configuration | Content passed/evaluated | Strict passed/evaluated | Full criteria/evaluated | Native time (s) | Recorded tokens | Cases/6 |
|---|---:|---:|---:|---:|---:|---:|
| luna-high | 6/6 | 5/6 | 35/36 | 58.113 | 240,248 | 6/6 |
| luna-medium | 5/6 | 4/6 | 34/36 | 47.468 | 227,149 | 6/6 |
| haiku-medium | 1/1 | 1/1 | 6/6 | 4.830 | 15,745 | 1/6 |
| sonnet-medium | 1/2 | 1/2 | 11/12 | 16.326 | 43,369 | 2/6 |

Content requires execution, real exit codes, aggregate status and both semantic findings. Strict also requires the frozen scope/format contract and a completed native call. Partial criteria do not count as full. See rubric.json and grades.json for individual evidence.

Original blind grades are preserved in grades-original.json. Correction-only blind review withdrew hidden successful-test-count requirements and unsupported1.89s timing penalties; grading-adjudications.json records the four corrections without altering fixtures or native outputs. Original strict cases: luna-high 3/6; luna-medium 3/6; haiku-medium 1/1; sonnet-medium 1/2.

## Concrete findings
- luna-high/N6: All executions/exits and findings correct; 3–6µs durations contradict fixture runtimes exceeding 230µs.
- luna-medium/N5: Withdrawal of1.89s penalty: native wall-time metadata and completed hang duration were not retained, and no tolerance was frozen. Incorrect FAIL versus BLOCKED remains a status defect.
- luna-medium/N6: All three executions/exits corroborated. Reported 4–6µs durations contradict fixture runtimes exceeding 250µs.
- sonnet-medium/N1: Single execution corroborated; reports unknown exit instead of actual 0. Other findings correct.

## Measurement limits
- Preflight-only blocked records are not native attempts and are never graded as model failures. Missing cells are unknown; unequal coverage prevents a four-model ranking. See closeout-audit.json for never-invoked cells and lane reasons.
- Single sample on six synthetic standard-library fixtures; no production repository/network workload or statistical quality ranking. No permanent model selection.
- Native wall time includes CLI/model/tool work; quota reads are excluded. Fixture end-event duration excludes shell startup and the killed hang; it is not model-only overhead. N5 intentionally waits two seconds per configuration.
- Both Luna N6 summaries report microsecond command durations below the contained fixture runtime. These are unreliable complete-command timings. Native tool wall-time metadata was not retained, so responsibility between the model and native CLI measurement is unknown; fabrication is not established. Content and strict contract results remain separate.
- Same account per provider, alternating within-provider route order by case; different providers have different native tools, caching and subscriptions. Raw tokens are not invoices, cost estimates or quota equivalents.
- Requested model/effort are pinned in protocol.json. Effective identity/effort is only attested when native events report it; absent fields remain unknown. Codex may not attest its effective model; no inference from its answer.
- Tool calls/results are retained without private thinking. Fixture logs corroborate invocation and full outputs; immutable fixture/task mounts prevent their edits. Post-run hashes and tool review detect scope breaches, not every possible malicious transient action.
- grades.json contains the anonymous semantic assessment; blind-map.json restores route identities after grading. Original evidence hashes are in original-evidence-hashes.json; frozen hashes in protocol.json. See final-review.json for independent closeout review status.

## Identity evidence
- luna-high: observed models=[]; observed efforts=[]. Empty means unattested.
- luna-medium: observed models=[]; observed efforts=[]. Empty means unattested.
- haiku-medium: observed models=['claude-haiku-5-5']; observed efforts=[]. Empty means unattested.
- sonnet-medium: observed models=['claude-sonnet-5-5']; observed efforts=[]. Empty means unattested.
