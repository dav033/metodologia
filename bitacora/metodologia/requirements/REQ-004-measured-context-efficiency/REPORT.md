# REQ-004 — Measured context efficiency

## Built
Added the exact measured selective-context policy to `skill/SKILL.md`: load references for the next action with prerequisites, reuse unchanged context, batch independent reads, retrieve narrowly and preserve original diagnostics/status. Existing root sections, permissions, acceptance criteria, language rules and licenses remain intact. No runtime code or configuration changed.

## Measured outcomes
Eight fresh-context participants, same model/effort: three variants screened twice, followed by a held-out baseline/candidate pair. Selective policy screening medians improved total tokens by 5.55% and uncached input by 27.99%; output increased 16.41%. Held-out total tokens increased 0.86%, while uncached input fell 14.89% with different cache hits. The compact-entrypoint candidate increased consumption and was rejected. These are conditional observations, not guaranteed or monetary savings.

All six screening runs met 18/18 predeclared manual criteria; both held-out runs met 9/9. Grading was by the coordinator, not an independent blinded judge. The eight participants consumed 1,155,195 tokens; coordinator/research/review overhead is additional.

## Verification
- PASS: collector behavioral tests, 5/5; duplicate counters, cache accounting, incomplete runs, invalid totals and unrelated sessions covered.
- PASS: both held-out proposed functions, 6/6 actual isolated permission-matrix checks each after AST validation.
- PASS: skill-creator validator, internal Markdown links, exact integrated-policy match against measured candidate, unchanged reference bodies and scoped diff whitespace.
- APPROVE: independent spec and standards reviews, no findings; see retained reviews.md.
- NOT RUN: real product suites/deployments. Fixtures contained archived synthetic failing results; agents read those records rather than executing product checks.
- NOT RUN: paid evaluation CLI or RTK execution; RTK absent from PATH.
- NOT APPLICABLE: application lint/typecheck/build for the instruction-only canonical change. The benchmark collector was executed and behaviorally tested separately.

## Evidence and limitations
[Full benchmark and retained evidence](../../artifacts/metodologia-efficiency-2026-10-12/benchmark.md): frozen packages, tasks, logs, rubrics, eight responses, actual token records, collector/tests and incremental integration diff.

Two repetitions per screening variant and one held-out pair are exploratory. Cache warmth, scheduling, shared harness context and model variability remain confounders. Bundled policy changes cannot be credited individually. Unsuccessful results and inefficient/truncated reads are retained. Benchmark cost is distinct from any future savings.

## Pending
Normal-session adoption feedback and owner review of the existing uncommitted work. No commit, push, installation, global setting or production action performed.
