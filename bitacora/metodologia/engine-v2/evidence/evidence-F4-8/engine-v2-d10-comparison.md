# Engine v2 D-10 benchmark

Commit: `ce8bf30b12d08fdd0f41fcd2bd8a5a38a0df7a48`

| Flow | Scenario | Accepted | Attempts | Redone tasks | Discarded accepted min | Wall seconds | Token proxy |
|---|---|---:|---:|---:|---:|---:|---:|
| legacy | clean | True | 24 | 0 | 0 | 36000.0 | 19200 |
| legacy | with_defects | True | 48 | 24 | 600 | 72000.0 | 38400 |
| subplans | clean | True | 24 | 0 | 0 | 36000.0 | 19200 |
| subplans | with_defects | True | 36 | 12 | 300 | 54000.0 | 28800 |

Token proxy: **32 proxy tokens per actual attempt minute**; no provider tokens or cost were observed.

## Recovery benchmark

| Metric | Pre-engine-v2 | Candidate |
|---|---:|---:|
| human_interventions | 1 | 1 |
| minutes_to_recovery | 51.9 | 51.9 |
| classified | 12 | 12 |
| as_expected | 12 | 12 |

No-regression metrics: PASS; known baseline issues remain separately represented in per-scenario rows.
