# Runner pilot — approved bounded experiment

Owner authorization: “haz las prubas, tambien intentemos con sonnet medium”. This accepts the proposed six-case comparison and adds Sonnet medium: 24 native calls, one per case/configuration.

Configurations: GPT-6 Luna medium/high on codex-luis (the owner's current experimental Codex profile); Claude Haiku5.5 medium and Sonnet5.5 medium on claude-work. One call at a time per account; two provider lanes. No account rotation, automatic waiting, retries, repair turns or model substitutions. Stop the affected lane on quota/auth/challenge/collector failure. Grade failed native outcomes rather than repairing them. No permanent role assignment, installation, commit or push.

1. Prepare six deterministic local command fixtures and a six-criterion rubric per case. Validate real subprocess exit codes, timeout, long-log recovery and sandbox isolation without model calls.
2. Independently review the fixture, collector and grading contract; fix harness defects before freezing. Freeze scripts/cases/rubric/prompts/dependencies by hash.
3. Execute only never-started cells with durable START/DONE records and a process lock; save original answers, command events, tool evidence, scope hashes, timing, quota and normalized usage. Preserve unknown effective identities/efforts.
4. Evaluate command execution and semantic summaries separately from scope/format. Audit all24 records and frozen hashes, publish REPORT.md/comparison.json and update day/SUMMARY/week/indexes.

Acceptance: six matched cases per configuration where quota allows; disclose missing/blocked cells and do not rank unequal coverage. Real command exits take precedence over printed PASS. All requested commands must execute even after a previous failure. Retain raw fixture output independently of model summaries; command fixtures are immutable in the candidate sandbox. Native wall time includes tools; controlled command duration is separately recorded, not an exact measure of model-only latency. Recorded tokens are not invoices or quota equivalence.

Cases: N1 success plus warning; N2 nonzero with misleading PASS; N3 repeated plus distinct failures; N4 failure in the middle of long output with saved full log; N5 bounded timeout plus missing entrypoint; N6 explicit pipefail plus independent successful and unavailable-dependency commands.
