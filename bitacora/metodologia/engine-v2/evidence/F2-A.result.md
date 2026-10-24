STATUS: PARTIAL

SUMMARY: Wired conditional private skills into the Antagonist, Runner and Explorer prompts.
Added pinned, license-verified public technique references and updated the Explorer knowledge-delta contract.
Aligned the antagonist gate documentation with `bt_review_policy.py`, including future F4 subplan-audit coverage.
Merged the Runner addendum into `runner.md`; retained the addendum file as provenance.
The parallel knowledge package README is not present in this worktree, so its referenced path could not be verified.

CHANGES:
skill/agents/antagonist.md — added risk-based private skill loading and gate guidance.
skill/agents/antagonist/skills/adversarial-contract-breakage/SKILL.md — adapted invariant-first and contract-test checks.
skill/agents/antagonist/skills/cross-subplan-failure-scenarios/SKILL.md — added localized pre-mortem checks.
skill/agents/antagonist/skills/failure-mode-and-boundary-analysis/SKILL.md — added focused STRIDE guidance.
skill/agents/antagonist/references/public-adversarial-techniques.md — added four pinned sources with license, borrow and exclude details.
skill/agents/explorer.md — added conditional dependency analysis, map query and `knowledge-delta/1` output requirements.
skill/agents/explorer/skills/subplan-dependency-analysis/SKILL.md — adapted graph-engineering and documented the JSON delta; cited the other two sources as candidates only.
skill/agents/runner.md — merged conditional skill loading and preserved Runner’s status protocol.
skill/agents/runner/references/public-testing-techniques.md — pinned four sources and recorded verified licenses.
skill/agents/runner/runner.prompt-addendum.md — retained and labeled as provenance for the merged prompt.
skill/references/subagents.md — corrected the gate heading and table row, documented private skills, and noted planned F4 coverage.

VERIFICATION:
`git diff --check` → exit 0.
`cd skill/scripts && PYTHONPATH=tests python -m unittest tests.test_harness_optimization` → exit 0 (36 tests, 0.56s).
`python -m unittest tests.migration.test_policy_parity.PolicyParityTests.test_headings_of_every_baseline_reference_still_exist` → exit 0 (1 test, 0.15s).
`python -m unittest discover -s tests` → exit 1 (872.029s): 2,404 tests, 16 failures, 6 skipped. Fifteen failures match the `RULES.md` baseline; the additional precommit heading-parity failure passed after commit against the updated baseline.

COMMITS:
`aa373f69 Wire F2-A subagent skills and align review policy docs`

PROVENANCE:
PriNova/pi-agent-codebase-workflows, `skills/arch-code-review/SKILL.md`, `35cad6fb3a3e559a2519beed3887cb02497de5b2`, MIT — adapted invariant-first architecture and contract checks.
UnitOneAI/SecuritySkills, `skills/appsec/threat-modeling/SKILL.md`, `70bc259bb01abb3015ad2ad859ad5253cbf0bcab`, MIT — adapted a conditional, focused STRIDE lens.
vibeeval/vibecosystem, `skills/premortem/SKILL.md`, `3b763b1fb288f57bfa3cce76ef18184b96461a78`, MIT — adapted localized composition risk checks.
ultimatile/development-skills, `skills/codex-contract-test-review/SKILL.md`, `f68aaf63fa077906a7e4d62e9747d262a4c9c4fd`, MIT — adapted checks that contract tests exercise the claimed invariant.
magnus919/agent-skills, `playwright/SKILL.md`, `7f446e60055b335dd26831371a027fa6b59da3e2`, MIT (`LICENSE.md`) — adapted bounded execution and evidence guidance.
voidmatcha/e2e-skills, `skills/playwright-debugger/SKILL.md`, `4ff48ba91ba5ef228e96852adcfb156b1ad49047`, Apache-2.0 — adapted failed-report classification.
apache/magpie, `plugins/magpie-repo-health/skills/flaky-test-triage/SKILL.md`, `27268f28a253978137e0cfa17bc19ef6e8897c28`, Apache-2.0 — adapted history-based flake triage.
j4flmao/agent-skills, `skills/quality/smoke-testing/SKILL.md`, `5a19d636db60d2f7e08f036037a5b49c0a4ae8bd`, MIT — adapted bounded smoke-scenario guidance.
douinc/agent-skills, `skills/graph-engineering/SKILL.md`, `99ec1c314078a37a55a8534682b20a7a52683907`, MIT — adapted evidence-backed graph practices for read-only delta output.
Data-System-School/agent-skills, `investigate-codebase/SKILL.md`, `a117418ab3596c59d641cab4cb89bdbe560fb277`, MIT — cited as an Explorer candidate only.
event4u-app/agent-config, `src/skills/blast-radius-analyzer/SKILL.md`, `4502d328ff6402f0dfb7bc1b970007179587282f`, MIT — cited as an Explorer candidate only.

CONCERNS:
`skill/scripts/bt_knowledge/README.md` is absent from this worktree. The prompts reference it as required, but this task did not own the parallel knowledge-package files. The full suite retains the 15 baseline failures documented in `RULES.md`.