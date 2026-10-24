# Subagents

Subagents are for **context control**, not role-play. Use one when its work would flood your context with stuff you
only need the conclusion of (searching, reading docs, noisy test output), or when you need eyes without your bias
(review). Everything else stays in the main session.

## The eight roles

Defined in the skill's `agents/` folder (source of truth; after editing run `python <skill>/scripts/install_agents.py`).
All eight roles install for Claude Code and Codex. Planner and explicitly selected roles install for Antigravity;
Claude and Codex account profiles registered on this machine receive their own copy. Tool limits are enforced by the
definition, not by asking nicely.

| Role | Use for | Writes? | Private skills | Model |
|---|---|---|---|---|
| `planner` | Inspecting a requirement and codebase, then drafting a scoped milestone/task plan under `PLAN.json` | Requirement documents only | `functional-subplan-decomposition`, `adversarial-plan-review`, `plan-mermaid-view`, `socratic-elicitation`, `wbs-dag-decomposition` | Astra high / Opus xhigh |
| `designer` | Versioned UI/UX contracts and an optional mock-data preview before UI implementation | `design/` only, enforced by runtime | `ui-ux-contract-authoring`, `design-contract-versioning-and-impact`, `preview-prototype-maintenance` when enabled | Sol high / Opus high |
| `explorer` | Where is X, what calls Y, how is Z done here, find similar examples | No | `subplan-dependency-analysis` for contract, producer/consumer or impact questions | Luna high / Sonnet medium |
| `researcher` | External docs, library comparisons, API/version checks, web research | Notes file only | `external-research-memory`, `source-freshness-verification` | Luna high / Sonnet low |
| `implementer` | One plan task in a fresh context | Yes | `contract-driven-implementation`, `focused-verification-and-evidence`, `safe-worktree-contribution` | Sonnet medium / Luna high |
| `reviewer` | Fresh-eyes review on one axis: `spec`, `standards` or `visual` | No | `subplan-contract-review`, `integration-compatibility-review`, `evidence-based-findings`, `rendered-ui-fidelity-audit` for visual work | Sol medium / Sonnet medium; high for explicit complexity |
| `runner` | Test suites, builds, lint/typecheck, logs, server status — returns only failures | No | `scoped-verification-execution`, `failure-deduplication-and-triage`, `subplan-integration-smoke` | Luna high / Sonnet low |
| `antagonist` | When required by `bt_review_policy.py`, attacks the scoped change (architecture, correctness, security, tests) | No | `adversarial-contract-breakage`, `cross-subplan-failure-scenarios`, `failure-mode-and-boundary-analysis` | Sonnet medium / Opus high |

Load each private skill only under its role prompt's stated trigger; a skill file's presence alone does not activate it. These role-specific skills are not registered as generally discoverable skills. Planner may write requirement documents but never product code, approve or freeze a plan, or launch execution.

In Claude Code and Codex, invoke installed roles by name. In Antigravity, select Planner from the agent picker. If a role is not installed, use the harness's built-ins with the same briefs and contracts.

## Agents of another provider

For work that deserves **another model or another subscription** — an independent audit, a cheap fast worker for a
well-specified module, a stronger model for one hard piece, or simply because your account is near its limit — use
`bitacora.py delegate` (`agents.md`): it routes approved role configurations across eligible registered accounts by provider-family quota
unless you pin one, and returns a compact result.

## Normal sessions

Use `delegate start` for one task, with `--role ROLE` and `--complexity L` for approved alternatives, `--retries 1..3` for bounded retries or `--worktree` for branch isolation; use
`bitacora review` for an independent read-only audit and `delegate resume ID` after an interrupted process. Read the
compact result, never the session log.

## When — and when not

Use a subagent when:
- a search needs more than ~3 queries or reading many files → `explorer`;
- you need outside knowledge that takes several pages of reading → `researcher`;
- a command's output is long (full test suite, build, logs) → `runner`;
- a plan has more than ~4 tasks or a task is big enough to bloat your context → `implementer` per task;
- a phase or the whole change is finished → `reviewer` (×2 axes).

Don't when:
- you already know the file/symbol — just read it;
- the task is small (one or two edits, a quick fix) — do it yourself;
- the work is iterative or cross-cutting and needs the conversation's context — keep it in the main session;
- you'd spawn one per trivial step. Each agent costs roughly 4× the tokens of doing it inline, plus latency.

See [`agent-orchestration.md`](agent-orchestration.md) for task graphs, bounded concurrency, worktree ownership,
wave reconciliation, and long-running resume rules. In short: delegate only separable work, use three workers by
default (up to five only with a recorded reason), and let the coordinator own integration and proof of completion.

## Hard rules

1. **Writes are single-threaded.** Read-only roles (explorer, researcher, reviewer, runner) may run in parallel;
   implementers run one at a time. The only exception: independent tasks touching disjoint files, each implementer
   in its own git worktree (`isolation: worktree` / a worktree you create), merged by you afterwards.
2. **Bound concurrency.** Three workers is the default; raise it only when independence, machine capacity, review
   bandwidth, and usage budget justify it. Never exceed five without a concrete reason in the plan.
3. **Complete brief, pointers not pastes.** The subagent sees nothing of your conversation (template below).
4. **Verify, don't trust.** A subagent's report is a set of claims. Check implementer work against the diff and
   by running the verification yourself (or via `runner`); spot-check explorer `path:line` references before
   building on them.
5. **Reviewers get a clean context:** spec/plan paths + diff range + axis. Never your reasoning or the
   implementer's report as truth. Two axes in parallel: `spec` and `standards`. Fix real findings; anything that
   isn't correctness/requirements/security goes to PENDING.md, not into the code.
   Use `agents.md`'s audit budget. A milestone audit session covers both lenses itself; do not add two more full
   review sessions on top of it. Separate axes are for coordinated review without an existing milestone audit.
6. **Status drives the next step:** `DONE` → verify and continue; `DONE_WITH_CONCERNS` → read concerns, decide;
   `NEEDS_CONTEXT` → answer from the spec/plan/codebase and re-dispatch with a better brief (ask the user only if
   it's genuinely theirs to decide); `BLOCKED` → don't retry the same brief unchanged: change the approach, the
   model, or split the task.
7. **Only the main session talks to the user and writes the bitácora** (day log, DECISIONS, PENDING). Subagents
   report; you record.
8. **Dispatch by dependency and ownership.** Workers receive a complete brief because fresh contexts do not inherit
   the conversation. Parallel writers must own disjoint files/modules and use separate worktrees when available;
   shared contracts/files have one owner. Wait for every worker in a wave, inspect its diff/report, and run the
   planned verification before releasing dependent work.
9. **No unsupported capability assumptions.** Check the current harness for subagent support. If it is unavailable,
   proceed sequentially and report the limitation; do not edit global configuration or install runtimes to enable it
   without specific authorization.

## Delegation brief (template)

```
GOAL: <one sentence: what done looks like>
CONTEXT: <where this fits; decisions already made; what NOT to reconsider>
POINTERS: spec=<path> plan=<path> (task Tn) files=<paths> base=<git sha>
SCOPE: do <X>. Do NOT touch <files/areas>. No refactors outside scope.
AXIS (reviewer only): spec | standards
VERIFY: <command/test that proves done>
STOP IF: ambiguity that changes the design, missing context → return NEEDS_CONTEXT
OUTPUT: your role's output contract; full notes to <path> if any
```

## Evidence for diff reviews

Use this protocol within the existing `spec`/`standards` passes; do not launch a second pair just to emulate
another framework. Keep small changes inline. Reviewers receive the same scope/base and access to the relevant
files, acceptance criteria and contracts, without the implementer's conclusions. Inspect enough surrounding code
and consumers to establish impact, but report only problems introduced or worsened by the change.

Within `standards`, examine both behavior/security and maintainability:

- Trace changed contracts through callers, configuration and error paths. Check developer setup (renamed env
  vars, required scripts, ports), authorization and feature gates across UI, API and background work when affected.
  Confirm a suspected downstream safeguard in the actual consumer instead of reporting an unresolved "if".
- Look for a concrete simplification that removes states, branches or indirection while preserving behavior.
  Explain which complexity disappears and why the replacement is simpler. Existing layering, typing and size
  rules still govern: `unknown` at an unvalidated boundary is correct, and shorter code is not inherently better.
  An optional redesign or missed elegance alone is not a blocker; propose it without expanding the task.
- Distinguish an intentional, agreed behavior change from an accidental regression. Report unexpected wider
  consequences even when the local behavior was intentional. If code or a repository is unavailable, state the
  investigation limit instead of claiming certainty or an unconditional approval.

Each finding identifies severity, path:line, trigger, traced evidence and user/developer impact, plus a bounded
remedy. Severity follows demonstrated impact, not the review's aggressive tone or how many reviewers agree.
After the independent inspection, consult available PR discussion for substantive findings when relevant; verify
and attribute any incorporated external finding. Reading discussion does not authorize posting comments.

The coordinator deduplicates by root cause, checks disagreements against evidence and gives one concise verdict
with remaining uncertainty. Agreement is corroboration, not proof or an automatic severity increase. Fix proven,
in-scope violations; record optional simplifications and unrelated debt as proposals. Preserve existing review
limits and approval gates; no new mandatory review loop or installed agent is required.

Adapted as independently written workflow guidance from [cursor/plugins Thermos](https://github.com/cursor/plugins/tree/1dcc2bacde73ddd284803b7af28164d0436198fc/thermos)
(reviewed 2026-10-13, revision `1dcc2bacde73ddd284803b7af28164d0436198fc`): traced branch impact, fresh inspection
before external findings and consolidated evidence. No upstream files, runtime, 1k-line threshold or speculative
refactor blockers are adopted.

## The antagonist gate (per-commit or milestone audit)

Follow `bt_review_policy.py`. Run Antagonist before a commit only when no pending independent milestone audit
covers that work. If an audit covers it, the audit reviews the consolidated milestone diff and individual commits
do not receive repeated Antagonist passes. The task's verify, tests and linters still run before each commit under
that coverage. Security checks always apply, with or without audit coverage. This gate is deliberately hostile;
**you** are the judge.

When the per-commit gate applies:

1. **Stage** the change, then brief the antagonist: repo(s), `git diff --staged` (per repo in a workspace), the
   spec/plan task it implements. One antagonist pass per commit — for a multi-repo phase, one brief covering all repos.
2. **Triage every finding yourself** — the antagonist never decides:
   - **Relevant now** (blocker/major that is real, in scope, and cheaper to fix now than later) → fix it.
   - **Not now** (real but out of scope, minor, speculative, or bigger than the task) → record it as a pending
     item with urgency and complexity: `bitacora.py id P`, then a line in PENDING.md with source
     `antagonist <REQ/commit>` (see documentation.md §Pending).
   - **Wrong** (the antagonist misread the code) → drop it, one line why in the PLAN Progress log.
3. **Commit** and log in the PLAN Progress log: `antagonist: N fixed, M deferred (P-0xx…), K dropped`.

Hard stops against loops: one pass per commit when the per-commit gate applies; the antagonist can't delegate or
edit; do not run another pass for deferred items. If it times out or errors, commit anyway and note "antagonist skipped".

An independent pending milestone audit covers the unit's own milestone only; work without such coverage keeps the
per-commit gate. High risk or architecture level does not override audit coverage. The supervisor's prompts take
this rule from `bt_review_policy.commit_review_rule`. Engine v2 F4 is planned to extend this coverage to subplan
audits; that extension is not implemented yet.

## Where they plug into the flow

| Flow step | Subagent use |
|---|---|
| Requirements §2 — explore before asking | `explorer` sweeps the repo (and `researcher` the domain) while you prepare round 1 |
| Requirements §7 — Deep track | `reviewer` with axis `spec` reads only SPEC.md and lists ambiguities/contradictions |
| Execution — long plans | `implementer` per task, sequentially; you verify each before ticking it |
| Execution — end of each phase | `reviewer` ×2 (spec + standards) on the phase diff |
| Execution — verification | `runner` for the full suite/build; you read its summary, not the log |
| Debugging | `runner` reproduces and distills the failure; `explorer` traces the code path |
| Tools & infra | `runner` for read-only status/log checks on servers or hosting CLIs |
