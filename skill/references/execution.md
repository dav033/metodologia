# Plan & execute

The user wants you as independent as possible. The spec is the contract; inside it, you decide. Coming back with a
question costs the user a context switch — only do it when a wrong guess would be expensive or irreversible.

What makes autonomy safe is not asking more, it's **verifying more**: a clear pass/fail check defined before you
start, evidence before you claim, and small committed steps you can roll back.

## 1. Plan

Design with `references/engineering.md` (and the matching `references/stacks/*.md`) in mind.
`python <skill>/scripts/bitacora.py req plan REQ-NNN` → creates `PLAN.md` next to the spec. Fill it:

- **Approach:** the chosen design in a few lines. If you weighed real alternatives, log the choice in DECISIONS.md.
- **Global constraints:** copy from the spec what every task must respect.
- **Verification first:** the end-to-end check that proves the acceptance criteria — the exact command(s) or
  steps (tests, `npm run verify`, run the app and exercise the flow, a dry run of the process). Define it before
  writing code; it's your finish line.
- **Tasks:** small steps (minutes, not hours) in dependency order, one line each, in the template's format:
  ``- [ ] T3 — <what> · repo: backend · after: T1, T2 · verify: `npm test -- orders` · covers: R1, US-2``.
  `repo:` when the workspace has several, `after:` for dependencies, files (or for business work:
  deliverable/owner), how to verify it (a command inside backticks is machine-runnable — the scheduler's verifier runs it),
  and which requirements (R1, US-2…) it covers. Every requirement must be
  covered by some task. Group them in phases that each end in a green, committable state.

Keep the plan short enough to read in two minutes. Set the spec's `status: planned`.

## 1b. The one gate: plan approval

This is the single point where the user reviews — reading a 2-minute plan is far cheaper than reviewing hundreds of
lines of code built on a wrong plan. Show the user, in Spanish, a compact version of the plan:
- approach (2–3 lines), phases with their tasks (one line each), what's out of scope, the verification;
- the key decisions/assumptions you're making;
- the path to PLAN.md for the full version.

Run `bitacora.py plan review REQ-NNN` first: it marks the plan `review` and prints the web URL, where the user
can read the plan and press **Aprobar y lanzar ejecutor** or **Pedir cambios**. Give the URL along with the summary.

Then wait for their decision, from whichever side it comes:
- **In the chat** ("aprobado", "dale", "sí", or changes): record it with `bitacora.py plan approve REQ-NNN` (or
  `plan changes REQ-NNN --comments "..."`).
- **On the web:** in Claude Code run `bitacora.py plan wait REQ-NNN` in the background to be notified; elsewhere,
  check `PLAN.md` status when the user says so. A web approval **already launched the executor** (status
  `launched`) — don't launch again; just log it. Web change requests are appended to PLAN.md's Progress log.

Apply any changes and ask once more only if they changed the approach. Once approved, log the approval in today's
log, and from there on **run autonomously to the end** (§2) — no further check-ins.

Skip the gate only for Quick-track work (a change that fits in one sentence) or if the user said "hazlo directo".

**The gate is automatic when there is nothing to decide.** `bitacora.py handoff REQ-NNN` (see `requirements.md` §8)
approves and launches a plan on its own unless it finds a reason for the owner to look first (size, an architecture or
high-risk task, nothing verifiable, or an irreversible/external/financial/security action in the text). Use it as
the default way out of planning; the manual review above is what happens when it answers `needs_approval`.

## 1c. Run the approved plan: scheduler, loop or goal

**The scheduler is the only way an approved plan runs in the background.** `launch` and `handoff` (and the web approval)
start `scheduler-run`, which composes the scheduler core (state machine and `SCHEDULER.db`), the router (M2), the executor
(M3) and the independent verifier/audits. Prerequisites: PLAN.md `status: approved` and a frozen `PLAN.json`
(`plan-json init` -> `check` -> `freeze`); a plan without one is refused with `PLAN_NOT_FROZEN` and nothing is started.
Keep the **loop** (or Codex goal) for a plan of a few hours done inside the current session. Rule of thumb: more than ~8
tasks or "this will run overnight" -> `launch`/`handoff`. Design: `references/modules.md` §Scheduler core.

**Routing across agents:** for each task attempt the router picks provider, model, profile and effort from every account
allowed for the project — by tier, kind of work, usage limits and measured results — and closes each milestone with an
independent audit (reviewer role) by another agent. The whole model is in `agents.md`.
Audits use Sonnet 5.5 medium, Opus 5.5 high for escalation/high risk, or Sol medium when Claude is unavailable;
they do not inherit the implementation ladder's effort. Reuse milestone audits for closing review rather than
launching duplicate full passes; the final session consolidates evidence and cross-milestone risks.

**Account profiles** (`bitacora.py profiles list|doctor`, `launch --profile ID`): a profile is a provider plus the
env that selects its account (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`); credentials stay in each provider's own directory.
Only `work_only` profiles (`claude-work`) are gated: they run solely for projects with `"work": true` in
`project.json` (`bitacora.py --project P work true|false`; missing = false). The gate runs before the handoff, the
prompt or the first session, and again on every scheduler attempt. Every other profile may run any project. It is a
launcher guarantee, not a sandbox: calling the provider binary directly bypasses it. Over SSH (no display) the
launcher opens a `tmux` session (`BITACORA_TERMINAL=tmux` forces it) or a transient `systemd-run --user` unit.

### Agile: delegate one task, read a compact result

`bitacora.py [--project P] delegate start "<task>" --profile ID|--agent A [--workdir DIR] [--allow PATH]...
[--verify "<command>"] [--timeout MIN] [--model M] [--effort E] [--background]` runs ONE task in a headless session.
The work gate runs first (profile and folder); then the agent reports in `RESULT.json` and the supervisor, not the
agent, runs `--verify`. You receive only `status` (`verified` · `verify_failed` · `claimed` · `partial` · `blocked` ·
`failed` · `timeout` · `usage_limit`), a ≤400-character summary, changed files, files outside `--allow` and the
follow-ups; the full log stays in `.state/delegations/<id>/session.log`. `claimed` means done by the agent's word
only, so ask for a `--verify` command whenever one exists. `delegate status <id>` and `delegate list` read back.
Delegate only when the task is independent and checkable; edits to the same worktree must not run in parallel.

**Concurrency**: the scheduler decides how many ready tasks run at once from capacity and resource reservations
(M1/M2); a delegation is always a single task.

**Attempt telemetry**: every scheduler attempt and every delegation appends one line to `<root>/.state/events/attempts-YYYY-MM.jsonl`
(profile, agent, model, effort, seconds, result, tokens). A measure the provider did not report is `null`, never 0;
Codex only reports a grand total. `bitacora.py metrics` summarizes per agent/profile/model with the share of attempts
that carried usage. Counts are per-attempt and not comparable across task difficulty: do not rank models from them
without comparing like with like. Local and private; nothing here is a subscription balance.

**From the HQ (planning room)** — the session runs inside the bitácora root (`~/bitacora`), the SessionStart
context says HQ MODE: don't execute here. Set PLAN.md `status: approved`, then launch a separate executor session:

```
python <skill>/scripts/bitacora.py --project <project> launch REQ-NNN [--agent codex] [--profile ID] [--repo <path>] [--background] [--dry-run]
```

From the web UI, the plan-approval form launches it for you. Follow progress with `bitacora.py --project <p> watch REQ-NNN`
(waits for the next news: settled attempt, block, wait, end), `plan-status REQ-NNN` or the web "Planes" view
(`documentation.md`). After a reboot or crash, `bitacora.py --project <p> scheduler-run REQ-NNN --resume` reopens the same
durable run; it never approves a plan or creates a replacement run. To run unattended use
`bitacora.py --project <p> scheduler-watch REQ-NNN --detach`: the watchdog resumes the owner whenever it dies (backoff,
gives up with a notification after 5 failures in 30 min) and login autostart launches it. Moves on a live run are
commands, not scripts: `scheduler-op REQ-NNN status|stop|resume|cancel-attempt ATT|reopen TASK|rework T1,T2|revise` (stop the owner
under a hold, apply through M1, kill the attempt's agent, release the hold; `revise` cancels live attempts and rebases onto
the latest frozen plan revision). When a run cannot go on alone (a blocked task, an open verifier review) it asks:
`scheduler-op REQ-NNN decisions` lists the requests (what happened, evidence, closed options with their consequence, a
recommendation; some are marked «nadie puede responder por ti»: integrity anomalies, human overrides of the verifier and
reasons the system does not know) and `scheduler-op REQ-NNN decide <request> <option> [--reason …]` answers one. The
watchdog notifies each new request once and keeps the run waiting for the answer; no timeout ever answers for the owner.
`retry_with_note` puts the owner's text in the task's next prompt. Every request carries a **diagnosis** (D-097,
`bt_block_diagnosis`): what failed, where it comes from and the steps to fix it, read from the run's evidence (start
rejections, M6 failure notes, every attempt's failure) rather than the reason code, which is often only the last guard
that tripped. Known causes: a clash between tasks (offers `rework_conflict`: redo the task built on a replaced result),
a check M6 cannot run (git in a sandbox without .git, a command form it refuses), read-only node_modules, a missing
module or variable, a service down, quota, a cancellation, the same failure repeated. The watchdog also asks a cheap
model to diagnose each new request (`bt_block_agent`, config `diagnosis.profile|model|effort`, default Claude Haiku;
`scheduler-op REQ-NNN diagnose <request>` by hand); its answer is cached in `RUN.diagnoses/` and both show on the card
in /flow and the plan page, with the recommended option first and a «Pedir diagnóstico al agente» button. Cancelling a scheduler plan (web "Planes" view,
confirm with the REQ id) is irreversible. The routing (model, effort and the escalation after a failed attempt) is the
router's job and is recorded per attempt, not set here (`agents.md`, `modules.md` §Scheduler core).

**An audit that finds critical or high problems does not end the run as a success.** Its findings ledger rejects it
and the Scheduler itself sends the named tasks (and what depends on them) back for rework, then runs the audit again
(`modules.md` §Audit gate and rework). A run is `done` only when the last audit accepted a ledger with no open
critical/high finding; after `max_reworks` rounds the owner decides.

`launch` writes `HANDOFF.md` next to the plan (everything the executor needs), refreshes the PLAN.md status block, and
opens a native terminal window (Linux terminal, macOS Terminal, or Windows Terminal) in the project's repo running
`scheduler-run`, whose agent sessions start with `--dangerously-skip-permissions` (Claude Code) or `--yolo` (Codex).
Executor sessions always start with these flags — that's the user's rule; never launch one without them. The repo path
is remembered per project (`<project>/project.json`); pass `--repo` the first time or for a new project (the folder is
created). `--foreground` (with `--planning-session`) replaces a verified planning child in the same terminal instead of
opening a window. Then log the launch in today's log, tell the user in one line, and stay available in the HQ for the
next requirement. Default agent: Claude Code unless the user says Codex.

**Inside the project repo** (no HQ), run the plan in this session:

**Claude Code** (you have the `Skill` tool and a `loop` skill is listed): invoke the `loop` skill **without an
interval** (self-paced), passing this prompt with the real paths filled in:

```
Execute the approved plan <abs path to PLAN.md> (REQ-NNN) following the metodologia skill, references/execution.md §2–§4.
Each iteration: read PLAN.md (Progress log + unchecked tasks), take the next phase, implement it, run its verification,
commit, tick the tasks and add a Progress log line. Record judgment calls under Rulings; don't ask the user.
If a stop-and-ask item comes up (§2), work on everything independent of it, then ask once, batched, and stop the loop.
When every task is ticked and the plan's Verification passes: do §4 (fresh-eyes review, statuses, bitácora,
walkthrough, final report in Spanish) and stop the loop.
```

Do as much work as is sensible inside each iteration (a whole phase or more); the loop is there so the work
survives long runs and resumes from PLAN.md, not to slow you down. Stop the loop yourself when the plan is done or
blocked. If the `loop` skill isn't available, just execute the plan straight through in the current turn.

**Codex**: use a goal. If you have a goal tool (`create_goal`), create the goal yourself with the text below;
otherwise give the user this exact line to paste, and start working:

```
/goal Complete REQ-NNN by executing <abs path to PLAN.md> per the metodologia skill (references/execution.md) without stopping until every task is ticked, the plan's Verification passes with evidence, and the bitácora (today's log, PENDING, SUMMARY) is updated — or until a stop-and-ask item blocks progress.
```

The goal text is the stopping condition, so keep the verifiable end state in it. In Codex there are no bitácora
hooks: at the start run `bitacora.py where` yourself and read SUMMARY/PENDING; before finishing, update the
bitácora explicitly (the Stop hook won't remind you).

**Other harnesses:** execute the plan straight through, using PLAN.md's Progress log as your checkpoint.

## 2. Execute

- **One feature at a time.** Finish (verified, committed, logged) before starting the next; everything else waits
  in PENDING.md.
- Work task by task. Tick `[x]` in PLAN.md and add a line to **Progress log** after each verified phase. PLAN.md is
  the handoff: if the context resets, it's how you (or the next session) pick up exactly where you left off.
- **Keep your context clean with subagents** (`references/subagents.md`): `explorer` for code sweeps,
  `researcher` for docs and comparisons, `runner` for test suites/builds/logs. For long plans, an `implementer`
  per task — one at a time — then verify its result yourself before ticking the task. After each phase,
  `reviewer` ×2 (axes `spec` and `standards`) on the phase diff. Between unrelated pieces of work, or when the
  conversation gets very long, make sure PLAN.md and the bitácora are current and suggest a `/clear` to the user
  (one line, no waiting).
- **Default: don't ask.** Library choice, naming, file layout, how to split a module, which test to write, how to
  handle an edge case the spec didn't cover: decide, record a ruling, move on.
- **Rule conflict is an exception to that default.** If a user-controlled rule blocks the requested behavior, name
  the exact source and impact and ask whether the user wants a one-time exception or a permanent rule change before
  doing the blocked part. Pause only that part and continue independent work. Do not offer to change a higher-priority
  instruction this skill cannot edit; explain the constraint and an allowed alternative. See
  [`self-improvement.md`](self-improvement.md).
- **Rulings, not stalls.** Record each judgment call under **Rulings** in PLAN.md: `what — why — cost if wrong`.
  The user reviews rulings afterwards instead of being interrupted.
- **Stop and ask only for:** destroying data or work that can't be recovered (dropping tables, deleting files
  outside the repo, force-push, migrations on production data), actions visible outside the machine (push,
  deploy, publish, sending emails/messages, payments, spending money), credentials/security changes, or
  discovering the spec itself is wrong in a way that changes what gets built. Even then: batch the questions into
  one message and keep working on everything that doesn't depend on the answer.
- **Scope discipline.** Improvements you notice outside the spec go to PENDING.md and to "Proposals" in your final
  report — not into the code, and not as an interruption.
- **When an approach fails twice, don't pile on patches:** revert to the last green commit, rethink, update the
  plan, try a different approach.
- Log significant decisions to DECISIONS.md *when they are made*, not at the end.

## 3. Git (solo developer)

- If the repo is on `main`/`master`, create a short-lived branch per feature (`feat/<req-slug>`); in a repo
  with other active work, a worktree.
- **Workspaces with several repos:** the same branch name in every repo the requirement touches; commit and
  verify per repo; keep cross-repo contracts (API shapes, shared types) in sync within the same phase; the
  branches are merged together, as one change.
- **Before committing, apply `bt_review_policy.py`** (`subagents.md` §The antagonist gate): with a pending
  independent milestone audit (`Mn-audit`), routine tasks use that audit instead of a duplicate Antagonist pass
  per commit, including high-risk/architecture work: the audit uses the milestone's appropriate risk budget.
  Run the staged Antagonist review when no milestone audit covers the session; keep all security checks. Triage findings:
  fix what's relevant now, defer the rest to PENDING.md with urgency/complexity — one review plus at most one
  re-review, never more.
- Commit after every green phase (Conventional Commits, in the repo's language). Keep refactor commits separate from behavior
  commits.
- **Cite IDs in commits** so the trace graph links code to the bitácora: a trailer line `Refs: REQ-012 T3`
  (add `D-004` / `P-007` when the commit implements a decision or closes a pending item).
- `main` must stay deployable. Unfinished work that has to be merged goes behind a flag, off by default (and the
  flag removal goes to PENDING.md).
- Don't merge the feature branch yourself: the user merges from the web UI's **Revisar** tab (one click merges every
  repo of the workspace together; "merge and publish" also pushes). **Push and deploy only after asking.**

## 4. Verify & close

- Run the verification from the plan for real and read the output. "Should work" is not verification (see the
  excuse table in `engineering.md` §6).
- **Fresh-eyes review:** for anything beyond a small change, the `reviewer` subagent ×2 (axes `spec` and
  `standards`) sees only the spec, PLAN.md and the diff and reports **only** correctness problems, unmet
  requirements and out-of-scope changes. Fix those; everything else goes to PENDING.md, not into the code —
  chasing every review nit is how over-engineering happens.
  An existing milestone audit already covers those lenses: consolidate its evidence, investigate cross-milestone
  risks and missing/stale coverage, and review only affected corrections instead of launching duplicate full passes.
- **Trace check:** `bitacora.py trace` must show no `uncovered` / `unknown-ref` / `dangling` issue for this REQ.
- Update statuses (spec `in-progress` with what's missing, or leave it for the merge; plan `done`) and the bitácora
  (today's log, PENDING, SUMMARY; ARCHITECTURE if structure changed).
- Write **`REPORT.md`** in the requirement folder (sections: Built, Verification evidence, Rulings, Needs your eyes,
  Proposals, Pending, Walkthrough). The web UI's **Revisar** tab shows it next to each repo's commits and diff, and
  is where the user merges (plan → `merged`, spec → `done`) or asks for changes (which relaunches the executor).
- **Walkthrough against comprehension debt:** in today's log, 5–10 lines on how the feature works — entry points,
  data flow, the non-obvious decision, where it would break. The user must stay able to understand and debug
  their own system.
- Report to the user in Spanish, short:
  - what was built and how it was verified (with the evidence);
  - rulings worth their attention;
  - **Needs your eyes:** core business logic, auth, payments, migrations or security-sensitive code that a human
    should read (file list);
  - **Proposals:** out-of-scope improvements, missing tooling, refactors — numbered so they can answer
    "sí a 1 y 3";
  - what remains pending.

## 5. Learn from corrections

When the user corrects how you work, ask yourself whether it's a one-off or a pattern. If it's a pattern, at the
end of your report propose making it permanent, in the cheapest reliable form:
- must **always** happen → a hook, lint rule or test;
- a standard or habit → one line in this skill (`engineering.md`, a stack file, or the relevant reference) or in
  the project's CLAUDE.md;
- project knowledge → ARCHITECTURE.md or DECISIONS.md.

Rules that no longer change behavior should be proposed for deletion too — a lean skill gets followed.

For a confirmed defect or requirement mismatch, reproducible check failure, explicit correction, or recurring
friction in the methodology itself, inspect the cause and make a narrow, validated improvement in the canonical
`~/dev/metodologia` source. Update the relevant tests and instructions, preserve unrelated changes, and report actual
verification. This standing authorization covers reversible skill-owned changes only: generated installed copies
and machine-wide Codex/Claude settings are outside it unless the specific update is authorized. Ask before external,
destructive, security-sensitive or unrelated system changes. A speculative idea is a proposal, not a change request.
See [`self-improvement.md`](self-improvement.md) for the evidence thresholds and rule-conflict procedure.
