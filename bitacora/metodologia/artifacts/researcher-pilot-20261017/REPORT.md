# Researcher pilot: native matched comparison

Native calls: 18/18; saved operational records: 19; content evaluations: 18/18.

Complete comparison.

The table includes the separately labeled posthoc source adjudication below; original reviewer grades remain preserved.

| Configuration | Native calls | Frozen content+cites | Live content+cites | Full criteria (adjudicated) | Supported criteria (adjudicated) | JSON contract | Seconds | Tokens (coverage) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sonnet-medium | 6/6 | 3/4 | 2/2 | 36/36 | 35/36 | 6/6 | 162.380 | 218,177 (6/6) |
| sol-medium | 6/6 | 4/4 | 2/2 | 36/36 | 36/36 | 6/6 | 213.775 | 625,696 (6/6) |
| luna-high | 6/6 | 4/4 | 2/2 | 36/36 | 36/36 | 6/6 | 137.044 | 597,123 (6/6) |

## Protocol and grading

Owner authorized this comparison after the web-research proposal. Three pinned models/efforts, six tasks each, one call/cell; no retries, repair turns or model substitution. Profiles: Sonnet claude-work; Sol/Luna R1 on codex-2. Owner then explicitly authorized codex-luis for the ten never-invoked R2-R6 cells. One active call per account. Native results and original quota preflight are preserved independently from content judgements.

R1 asyncio concurrency; R2 cross-version SQLite lifetime; R3 Node HTTP deadlines; R4 PostgreSQL concurrent-index failures; R5 Node release dates as of2026-10-17; R6 uv synchronization and network guarantees. Frozen extracts have original line numbers. Live tools differ by provider; interpret frozen and live results separately.

Each of36 criteria per route is graded full/partial/missing and separately source-supported or unsupported. A content+citation case passes only when all six criteria are full and supported, with no scope violations. JSON contract is a separate column; original responses are never repaired. Labels are hidden for content grading where practical; coordinator may know routes, so this is not a fully blind or statistical comparison.

Case-pass and JSON columns use planned cases as denominators; unattempted cases are unknown, not model failures. Full/supported criterion columns use only graded cases. See grades.json for original criterion judgements, supplemental-grades.json for source adjudication, protocol.json for hashes/commands, results/ and continuation-codex-luis/results/ for native evidence, and corresponding submissions/ for original notes.

## Operational stop and concrete findings

Codex-2 reached100% five-hour usage (weekly16%) before R2 Luna. That original preflight record is not a native invocation or a model failure. The original lane stopped with ten unattempted cells. The owner explicitly authorized codex-luis, recorded in continuation-codex-luis/authorization.json. Current native calls: 18/18; unattempted: 0. Original execution-summary.json is historical; continuation status is separate. The eight initial calls, original preflight and partial report remain preserved; no call was repeated.

Sonnet R1 covers all six requested facts, but adds historical ExceptionGroup/except* details unsupported by the frozen extract while acknowledging that limitation: full content, one unsupported-evidence criterion. Sonnet live cases each record two successful WebFetch calls with no tool errors; R6 CLI reference was truncated and the candidate disclosed this. Codex records search/open/find events but not full page bodies; exact retrieval and rendered locators cannot all be independently attested from saved native events. Coordinator primary-source checks corroborated the requested facts and extra Node patch/Docker claims without new native calls.

A separate coordinator adjudication makes R2/C5 full: the answer correctly handles the explicitly asked Python3.11 compatibility/version question; an extra hidden-rubric distinction about SQLite autocommit was not an explicit question. Frozen rubric, source, candidate response and initial reviewer partial remain preserved in grading-spec-original.json and grading-adjudications.json. No native response was repaired.

## Separate posthoc published-source adjudication

Initial source reviewers marked R6/C5 partial for Sonnet and Luna because their wording differed from the upstream GitHub snapshot. Direct coordinator verification found that the published official concepts page uses the lockfile wording and the published CLI page uses the project-dependency wording, including the stated conflict/build-isolation qualifications. These LIVE responses should not be penalized for accurately reflecting those published sources. All three routes therefore receive full/supported R6/C5 in a separate supplement; frozen rubric, source snapshots, original grades and native responses remain unchanged. This is source adjudication, not proof of all runtime synchronization edge cases.

[Published concepts](https://docs.astral.sh/uv/concepts/projects/sync/), [published CLI](https://docs.astral.sh/uv/reference/cli/). See supplemental-source-adjudication.json for exact coordinator checks, source drift and limitations.

| Configuration | Original content+citation cases | After source adjudication |
|---|---:|---:|
| sonnet-medium | 4/6 | 5/6 |
| sol-medium | 6/6 | 6/6 |
| luna-high | 5/6 | 6/6 |

## Effective accounts

| Configuration | Effective profile: native calls |
|---|---|
| sonnet-medium | claude-work: 6 |
| sol-medium | codex-2: 1, codex-luis: 5 |
| luna-high | codex-2: 1, codex-luis: 5 |

The account change is a comparison limitation: Sol/Luna totals combine two profiles. Model/effort, prompts and frozen corpora remain fixed; no account-quota equivalence or controlled account-effect claim is made.

## Per-cell outcomes

| Cell | Profile | Native status | Content full | Evidence full | JSON |
|---|---|---|---|---|---|
| R1-sonnet-medium | claude-work | completed | True | False | True |
| R2-sonnet-medium | claude-work | completed | True | True | True |
| R3-sonnet-medium | claude-work | completed | True | True | True |
| R4-sonnet-medium | claude-work | completed | True | True | True |
| R5-sonnet-medium | claude-work | completed | True | True | True |
| R6-sonnet-medium | claude-work | completed | True | True | True |
| R1-sol-medium | codex-2 | completed | True | True | True |
| R2-sol-medium | codex-luis | completed | True | True | True |
| R3-sol-medium | codex-luis | completed | True | True | True |
| R4-sol-medium | codex-luis | completed | True | True | True |
| R5-sol-medium | codex-luis | completed | True | True | True |
| R6-sol-medium | codex-luis | completed | True | True | True |
| R1-luna-high | codex-2 | completed | True | True | True |
| R2-luna-high | codex-luis | completed | True | True | True |
| R3-luna-high | codex-luis | completed | True | True | True |
| R4-luna-high | codex-luis | completed | True | True | True |
| R5-luna-high | codex-luis | completed | True | True | True |
| R6-luna-high | codex-luis | completed | True | True | True |

## Limits

- One sample per synthetic task. This does not establish general model superiority or a permanent Researcher assignment.
- Full/partial/missing content judgements are evaluation decisions, not deterministic benchmark test results. Live sources may change; retrieval/tool errors must not be relabeled as model factual defects.
- Tokens include cached context under provider-specific definitions. Codex input already includes cache reads; Claude input/cache counters are added once. Missing usage remains unknown. No invoice price or equivalent subscription quota is inferred.
- Codex streams may not attest effective model identity; absent reported identity is unknown, not confirmation. Effective effort is unknown without an explicit native attestation.
- Provider/account/runtime/tools differ. Account quota can include unrelated concurrent sessions. No security-control or credential changes were made.
