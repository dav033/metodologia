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
- **Tasks:** small steps (minutes, not hours) in dependency order, each with its repo role (`[backend]`,
  `[frontend]`) when the workspace has several, files (or for business work:
  deliverable/owner), how to verify it, and which requirements (R1, US-2…) it covers. Every requirement must be
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

## 1c. Run the approved plan as a loop / goal

**From the HQ (planning room)** — the session runs inside the bitácora root (`~/bitacora`), the SessionStart
context says HQ MODE: don't execute here. Set PLAN.md `status: approved`, then launch a separate executor session:

```
python <skill>/scripts/bitacora.py --project <project> launch REQ-NNN [--agent codex] [--mode goal] [--repo <path>]
```

It writes `HANDOFF.md` next to the plan (everything the executor needs), and opens a new Windows Terminal window in
the project's repo running Claude Code with `--dangerously-skip-permissions` and a self-paced `/loop` (or Codex with `--yolo`
and `/goal`). Executor sessions always start with these flags — that's the user's rule; never launch one without them. The repo path is remembered per project
(`<project>/project.json`); pass `--repo` the first time or for a new project (the folder is created). Then log the
launch in today's log, tell the user in one line, and stay available in the HQ for the next requirement.
Default agent: Claude Code unless the user says Codex.

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
- **Before every commit, the antagonist gate** (`subagents.md` §The antagonist gate): it attacks the staged
  change, you triage — fix what's relevant now, defer the rest to PENDING.md with urgency/complexity — one review
  plus at most one re-review, never more.
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
