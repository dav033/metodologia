# REQ-003 — Caveman, RTK and Grill Me integration

## Built
- `skill/SKILL.md`: concise communication rule, capability routing and shortened discovery description.
- `skill/references/communication-and-context.md`: selected upstream excerpts, adapted reporting/command-selection/design-interview prompts, pinned sources and explicit adaptation boundaries.
- `skill/references/requirements.md`: Grill Me depth check within the existing decision-tree interview.
- `skill/references/tools.md`: optional RTK guidance.
- `skill/references/third-party-notices.md`: retained copyright notices and MIT/Apache-2.0 terms.
- `evals/cases/n-*.json`, `o-*.json`, `p-*.json` and evals README entries: behavioral regressions for payload fidelity, failure recovery and dependency-aware interviewing.

## Verification evidence
- PASS: skill-creator quick_validate.py, with PyYAML in an ephemeral uv environment. Initial system Python lacked PyYAML; no global package installation was made.
- PASS: all local Markdown links resolve; new eval JSON and regex parse; 42 existing Python files parse (Python source unchanged).
- PASS: git diff --check for modified tracked files. Unrelated existing reference changes match the pre-edit snapshot.
- PASS: source notices checked against the downloaded pinned revisions. Caveman now uses Apache-2.0 and retains its legacy MIT notice; RTK uses Apache-2.0; Matt Pocock uses MIT.
- APPROVE: independent spec and standards reviews of the integration diff.
- Independent conversational forward test: supplied 2/18 test failures remained failures with exact payload; missing RTK fell back to git status; failed migration output was recovered without rerunning; payments were resolved before provider/refund questions and the interview ended when requested.
- NOT RUN: paid Claude behavioral eval suite; cases are added but have no measured paid-suite pass rate.
- NOT RUN: RTK runtime checks, binary absent from PATH. Scenarios are simulations, not executed migrations/tests.
- NOT APPLICABLE: application build/typecheck or runtime regression suite for this instruction/JSON-only change.

## Rulings
Natural concise Spanish retains Aye and required progress. RTK stays optional and adds no execution permission. Grill Me reuses existing rounds. Selected source material is attributed and adapted; no runtime, hook or proxy is imported.

## Needs your eyes
Use the new workflow in normal sessions and report unclear or overly brief answers. No security-sensitive runtime code was changed.

## Proposals
None added to implementation scope.

## Pending
Owner review/commit/merge, if wanted. RTK installation is outside this change. Paid eval cases n/o/p remain unexecuted.
The independent simulation also noted pre-existing instruction friction around conversation-only tasks versus mandatory bitácora files, and recommendation examples that do not uniformly accept yes. Explicit conversation-only instructions prevailed in this test; those unrelated rules were preserved.

## Walkthrough
The parent skill keeps the shared concise-output rule and dispatches noisy-output requests to the focused reference. Tools guidance discovers RTK and checks its installed command support; native commands work without it. Failed/truncated results lead to existing raw evidence before any repeat execution. Design questions continue through the existing dependency frontier with concrete trade-offs, recommended answers and explicit stop conditions. Third-party notices are separated so normal sessions do not load license text into their working context.
