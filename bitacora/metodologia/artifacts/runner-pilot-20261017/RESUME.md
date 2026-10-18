# Runner pilot — partial native execution

Execution ended with process exit0 and explicit PARTIAL outcome: Codex lane complete12/12; Claude lane stopped after3/12. Fifteen native calls completed once. `results/N2-haiku-medium.json` is a quota-query-only preflight record, not a native attempt. Nine cells were never invoked; see pending-cells.json.

The stop was HTTP429 from Anthropic's OAuth usage endpoint, not a native model response, exhausted model quota, authentication failure or quality defect. The generic status `quota_auth_blocked` alone is misleading; inspect quota_before.status=http_429 and absence of workspace_before/START. No Retry-After value was retained by the shared read_row adapter, so the retry time is unknown.

Collector limitation: the frozen runner queries quota before and after every cell. The shared live quota helper documents rate-limit sensitivity and a separate60-second all-account cache; this pilot used direct uncached read_row. Frequent polling is a plausible contributor, not a proved exclusive cause. No further Claude quota reads, account switches or model retries were issued after its lane stopped; the healthy Codex lane continued independently. Fix future telemetry polling rather than attributing the stop to Haiku/Sonnet.

Do not rerun run.py or delete/overwrite the preflight record. A safe continuation must preserve all originals and all15 native cells, retain frozen tasks/prompts/models/efforts/commands, use a separate reviewed continuation directory/protocol and admit only the nine truly never-invoked cells. Refresh telemetry subject to the provider's actual retry policy; retain unknown Retry-After as unknown. Use a bounded cache so before/after checks do not hammer the usage endpoint. Do not bypass a provider challenge, auth block, native usage limit or active Retry-After. The original protocol does not authorize automatic waiting, account rotation, retries or repair.

No continuation has been launched. Owner-facing status must say PARTIAL and avoid ranking four models from unequal coverage. Native usage/time totals cover only completed cells. Missing cases are unknown, not failed model cases. P-116 tracks completion.
