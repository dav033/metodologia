# Researcher pilot: native matched comparison

Native calls: 8/18; saved operational records: 9; content evaluations: 8/18.

INCOMPLETE: provider quota/operational stops leave unattempted cells. Unequal task coverage prevents ranking route totals. Matched cases only: R1.

| Configuration | Native calls | Frozen content+cites | Live content+cites | Full criteria (graded) | Supported criteria (graded) | JSON contract | Seconds | Tokens (coverage) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sonnet-medium | 6/6 | 3/4 | 1/2 | 35/36 | 34/36 | 6/6 | 162.380 | 218,177 (6/6) |
| sol-medium | 1/6 | 1/4 | 0/2 | 6/6 | 6/6 | 1/6 | 34.753 | 64,882 (1/1) |
| luna-high | 1/6 | 1/4 | 0/2 | 6/6 | 6/6 | 1/6 | 16.224 | 60,852 (1/1) |

## Protocol and grading

Owner authorized this comparison after the web-research proposal. Three pinned routes, six tasks each, one call/cell; no retries, repair turns or route substitution. Profiles: Sonnet claude-work; Sol/Luna codex-2, one active call per account. Native results are preserved independently from content judgements.

R1 asyncio concurrency; R2 cross-version SQLite lifetime; R3 Node HTTP deadlines; R4 PostgreSQL concurrent-index failures; R5 Node release dates as of2026-10-17; R6 uv synchronization and network guarantees. Frozen extracts have original line numbers. Live tools differ by provider; interpret frozen and live results separately.

Each of36 criteria per route is graded full/partial/missing and separately source-supported or unsupported. A content+citation case passes only when all six criteria are full and supported, with no scope violations. JSON contract is a separate column; original responses are never repaired. Labels are hidden for content grading where practical; coordinator may know routes, so this is not a fully blind or statistical comparison.

Case-pass and JSON columns use planned cases as denominators; unattempted cases are unknown, not model failures. Full/supported criterion columns use only graded cases. See grades.json for exact criterion judgements and citations; protocol.json for hashes/commands; results/ for native status/usage/tool evidence; submissions/ for original notes.

## Operational stop and concrete findings

Codex-2 reached100% five-hour usage (weekly16%) before R2 Luna. That preflight record is not a native invocation or a model failure. Codex lane stopped with ten unattempted cells; Sonnet lane completed6/6. Saved reset:2026-10-17 23:12:26 America/Bogota; revalidate before any resume. No account rotation or repeat was attempted. P-115 tracks completion.

Sonnet R1 covers all six requested facts, but adds historical ExceptionGroup/except* details unsupported by the frozen extract while acknowledging that limitation: full content, one unsupported-evidence criterion. Sonnet R6 gets five criteria full and one partial: exact sync removes packages outside the installation selection, not merely packages absent from uv.lock. Both live cases record two successful WebFetch calls each with no tool errors; R6 CLI reference was truncated and the candidate disclosed this.

A separate coordinator adjudication makes R2/C5 full: the answer correctly handles the explicitly asked Python3.11 compatibility/version question; an extra hidden-rubric distinction about SQLite autocommit was not an explicit question. Frozen rubric, source, candidate response and initial reviewer partial remain preserved in grading-spec-original.json and grading-adjudications.json. No native response was repaired.

## Per-cell outcomes

| Cell | Native status | Content full | Evidence full | JSON |
|---|---|---|---|---|
| R1-sonnet-medium | completed | True | False | True |
| R2-sonnet-medium | completed | True | True | True |
| R3-sonnet-medium | completed | True | True | True |
| R4-sonnet-medium | completed | True | True | True |
| R5-sonnet-medium | completed | True | True | True |
| R6-sonnet-medium | completed | False | False | True |
| R1-sol-medium | completed | True | True | True |
| R2-sol-medium | unstarted | None | None | None |
| R3-sol-medium | unstarted | None | None | None |
| R4-sol-medium | unstarted | None | None | None |
| R5-sol-medium | unstarted | None | None | None |
| R6-sol-medium | unstarted | None | None | None |
| R1-luna-high | completed | True | True | True |
| R2-luna-high | quota_exhausted | None | None | None |
| R3-luna-high | unstarted | None | None | None |
| R4-luna-high | unstarted | None | None | None |
| R5-luna-high | unstarted | None | None | None |
| R6-luna-high | unstarted | None | None | None |

## Limits

- One sample per synthetic task. This does not establish general model superiority or a permanent Researcher assignment.
- Full/partial/missing content judgements are evaluation decisions, not deterministic benchmark test results. Live sources may change; retrieval/tool errors must not be relabeled as model factual defects.
- Tokens include cached context under provider-specific definitions. Codex input already includes cache reads; Claude input/cache counters are added once. Missing usage remains unknown. No invoice price or equivalent subscription quota is inferred.
- Codex streams may not attest effective model identity; absent reported identity is unknown, not confirmation. Effective effort is unknown without an explicit native attestation.
- Provider/account/runtime/tools differ. Account quota can include unrelated concurrent sessions. No security-control or credential changes were made.
