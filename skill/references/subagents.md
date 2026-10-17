# Subagents

Subagents are for **context control**, not role-play. Use one when its work would flood your context with stuff you
only need the conclusion of (searching, reading docs, noisy test output), or when you need eyes without your bias
(review). Everything else stays in the main session.

## The seven roles

Defined in the skill's `agents/` folder (source of truth; after editing run `python <skill>/scripts/install_agents.py`).
The six helper roles install for Claude Code and Codex. Planner installs for Claude Code, Codex, and Antigravity;
Claude and Codex account profiles registered on this machine receive their own copy. Tool limits are enforced by the
definition, not by asking nicely.

| Role | Use for | Writes? | Model |
|---|---|---|---|
| `planner` | Inspecting a requirement and codebase, then drafting a scoped milestone/task plan under `PLAN.json` | Requirement documents only | caller-selected |
| `explorer` | Where is X, what calls Y, how is Z done here, find similar examples | No | haiku |
| `researcher` | External docs, library comparisons, API/version checks, web research | Notes file only | sonnet |
| `implementer` | One plan task in a fresh context | Yes | sonnet (pass `opus` for hard tasks) |
| `reviewer` | Fresh-eyes review on one axis: `spec` or `standards` | No | sonnet (medium; audit budget in `agents.md`) |
| `runner` | Test suites, builds, lint/typecheck, logs, server status — returns only failures | No | haiku |
| `antagonist` | **Before every commit:** attacks the staged change (architecture, correctness, security, tests) | No | opus |

Only `planner` loads the private resources in `agents/planner/skills/`. They are not registered as generally discoverable skills. The role may write requirement documents but never product code, approve or freeze a plan, or launch execution.

In Claude Code and Codex, invoke installed roles by name. In Antigravity, select Planner from the agent picker. If a role is not installed, use the harness's built-ins with the same briefs and contracts.

## Agents of another provider

For work that deserves **another model or another subscription** — an independent audit, a cheap fast worker for a
well-specified module, a stronger model for one hard piece, or simply because your account is near its limit — use
`bitacora.py delegate` (`agents.md`): it routes across eligible registered accounts by quota and measured results
unless you pin one, and returns a compact result.

## Normal sessions

Use `delegate start` for one task, with `--retries 1..3` for tier climbs or `--worktree` for branch isolation; use
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

## The antagonist gate (before every commit)

Every commit of code (not bitácora-only commits, not pure docs/formatting) passes through the `antagonist` first.
It is deliberately hostile; **you** are the judge. The protocol is built so it can never loop:

1. **Stage** the change, then brief the antagonist: repo(s), `git diff --staged` (per repo in a workspace), the
   spec/plan task it implements. One antagonist per commit — for a multi-repo phase, one brief covering all repos.
2. **Triage every finding yourself** — the antagonist never decides:
   - **Relevant now** (blocker/major that is real, in scope, and cheaper to fix now than later) → fix it.
   - **Not now** (real but out of scope, minor, speculative, or bigger than the task) → record it as a pending
     item with urgency and complexity: `bitacora.py id P`, then a line in PENDING.md with source
     `antagonist <REQ/commit>` (see documentation.md §Pending).
   - **Wrong** (the antagonist misread the code) → drop it, one line why in the PLAN Progress log.
3. **At most one re-review**, and only if you fixed something: send the antagonist the fix diff with the earlier
   findings and say it's a re-review. Whatever it says then: fix if trivial, otherwise defer. **Never a third pass.**
   A finding that comes back after you fixed it → defer it, don't argue.
4. **Commit**, and log in the PLAN Progress log: `antagonist: N fixed, M deferred (P-0xx…), K dropped`.

Hard stops against loops: one review + at most one re-review per commit; the antagonist can't delegate or edit;
you don't re-run it on deferred items; if it times out or errors, commit anyway and note "antagonist skipped".
Quick-track one-liners (typo, config value, copy) skip the gate.

**With the independent milestone audit active** (a pool run with an `M<n>-audit` task still pending) that audit is the
milestone's adversarial review, so per-commit passes are not repeated: the task runs its verify, tests and linters
before each commit and calls the antagonist once only for `risk: high` / `level: architecture` work or changes to
authentication, secrets, permissions, data migration or payments. Without a milestone audit the gate above stays
mandatory. The supervisor's prompts take this rule from `bt_review_policy.commit_review_rule`.

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
