# REQ-018 v2 T1 — actual M1/M2/native experiment

**Product acceptance: REJECTED.** Real launch, verification delivery and rejection gating observed. M1 ended blocked: T1 attempt att-0001 rejected; T2 pending/unreachable with zero attempts. Total native task attempts: one. No positive verdict or T2 launch was fabricated.

## Scope and actual components

David authorized an isolated actual T1 experiment, not canonical full-plan execution. The copied 8-task plan was approved/frozen with T1-only execution scope; canonical PLAN remains draft. Real M1 SchedulerCore and M2 DecisionAssignmentPort ran, using actual registered profiles/quota evidence. A scoped custom execution port used the canonical MethodologyDriver and M2 reference context/quota validation to launch Claude. A custom review port delivered M1's verification request to independent reviewers. M3/M4/M5/M6 production wiring was not exercised. In particular M3's commit-tree handoff was avoided under the owner's no-commit instruction.

M2 selected **claude-work / sonnet / medium**. CLI reported `claude-sonnet-5-5`; effective effort not independently attested. Native process exited successfully in 562.075s,33 turns, and claimed DONE_WITH_CONCERNS. Process exit is technical completion, not product acceptance. Usage/reported cost in native-attestation.json are provider metadata, not subscription invoices or comparative quality evidence.

## Initial real quota refusal and recovery

Initial M2 batch returned no_eligible_route. Claude-work had an age-valid cached sample whose five-hour reset had already passed; capacity therefore became unknown while the hourly preflight poll skipped refreshing it. Existing ensure_fresh refreshed that real account under its900s routing interval and produced status ok/5% bottleneck usage; no eligibility override, fabricated quota or policy change. Other accounts had stale auth/app-server observations. Pending methodology P-120 tracks the preflight refresh mismatch. The constructor laya_root error was confined to the external harness and repaired before launch.

## Independent checks

| Check | Original snapshot | Actual T1 snapshot |
| --- | --- | --- |
| Wedding / legacy search scripts | Both exit0 | Both exit0 |
| New strict matcher script | Not implemented originally; native red evidence preserved | exit0 independently |
| Theme-change, response and idea-request regressions | Not re-run as baseline | All three exit0 independently |
| npm run lint | exit0,50 warnings | exit0,same50 warnings, normalized output identical |
| npm run build --workspaces --if-present | exit0 | exit0 |
| npx tsc --noEmit | exit2, missing LayoutProps at src/app/layout.tsx:26 | exit1,same sole diagnostic |

Type checking does NOT pass. No full app build/browser/product-provider execution was performed for this pure matching task. Baseline and independent exact commands/exits/durations are in their respective summary.json files. Native red tests failed for missing module/export, establishing new surface absence rather than a complete behavioral red suite.

## Why acceptance was rejected

Both independent review axes returned CHANGES_NEEDED. Parent independently reproduced five bad outputs corresponding to four defects:

1. **F1:** requesting elegante accepts a solely black/gold design because the legacy synonym group encodes affinity rather than lexical equivalence.
2. **F2:** repeated negative cues fail to exclude gotico; a subsequent positive con dorado is incorrectly treated as an exclusion.
3. **F3:** explicit unknown style in the latest message disappears instead of yielding no match.
4. **F4:** no quiero nina becomes positive genero nina and returns the girl/fuchsia baby-shower design.

See reviews/verdicts.json for severity,path:line,triggers/remedies and reviews/reproductions.json for actual outputs. Passing planned scripts lacked these cases; no tests were weakened or adjusted to conceal them. Native output is preserved unchanged. No repairs were silently substituted for the model's first result.

## Preserved state and next work

Original Pictures source matches all4,164 captured hashes. Changes are only in the isolated copy, six expected source/test paths. before/,after/ and implementation.patch preserve that proposed implementation; package dist build output is excluded from the patch. Original isolated directory: `/home/david/.local/tmp/req018-t1-live-6ml2566g/pictures`.

Next: repair F1-F4 with failing behavioral regressions, re-run affected checks and independent acceptance before retrying T1; do not bypass the existing one-attempt rejection or launch T2. Pictures P-120 tracks this. This experiment proves real dispatch and rejection control, not a successful full workflow or model-quality ranking.

Child hooks were disabled and stream had zero hook events; local git mutation guard was active. No manual commits,pushes,merges,deploys,canonical integration or global configuration edits. Global automatic-VCS defect P-118 remains open; child-only protection is not a global fix. Full raw model transcript is intentionally excluded from persistent artifacts.
