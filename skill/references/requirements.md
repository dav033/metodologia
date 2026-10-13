# Requirements flow

Goal: turn a vague request into a spec precise enough that you can plan and build it without coming back to the
user. The user's time is the scarce resource — every question must earn its place.

If the user's goal directly matches a methodology capability that could change the approach or outcome, briefly
explain that capability in context before continuing. Avoid generic feature pitches and repeated explanations; see
[`self-improvement.md`](self-improvement.md).

## 1. Size the request

The interview is where questions belong: front-load them here so planning and execution can run without
interrupting the user. Not every request needs a full interview. Pick a track; when unsure, pick the heavier one.

| Track | When | What you do |
|---|---|---|
| **Quick** | One obvious change, no real decisions (rename, small bug with clear repro, copy change) | No interview. State your understanding in one line, log it in today's file, go build. |
| **Agile** | A mid-size technical change with a clear goal and few decisions (a contained feature, a bug with several causes, a refactor of one module) | No interview rounds and no PLAN.md. Write the objective and 2–5 acceptance criteria (one of them a command that can verify it) in today's log, ask only what blocks, then build directly or delegate single tasks (`delegate`, see `execution.md` §Agile). |
| **Standard** | A feature, a process change, anything with 2+ real decisions | Full flow below. |
| **Deep** | New product/system, cross-team process, money/security/data at stake, irreversible choices | Full flow + the extra lenses in §6 before closing. |

**Sizing is your call, made on your own and stated in one line** ("Standard: three decisions to settle"). Small and
clear → build it. Broad or with real decisions → interview, spec, plan in milestones. Unsure which → ask the user
one question about scope before anything else, then decide. Do not ask the user to pick the track.

The track (how much to specify) and the execution mode (how the work runs: `direct` in this session, `coordinated`
with a leader plus delegated tasks, or `marathon`) are different axes. Never start a marathon only because the track
is Deep, and never require an interview or a plan only because the work is delegated. Pick the mode from the plan:
a few hours or fewer tasks → direct/coordinated; days of independent work → marathon.

## 2. Explore before asking

Finding facts is your job; making decisions is the user's. Before the first question:

- **Software:** read **every repo of the workspace** the request may touch (README, structure, related code, tests, configs), git log for the area, and the
  project's bitácora (`SUMMARY.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `PENDING.md`). Send the `explorer` subagent for
  wide sweeps so your context stays clean (`references/subagents.md`).
- **Business / process:** read whatever exists — docs, spreadsheets, previous requirements, the bitácora — and, if
  useful, research the domain on the web (standard practice, regulations, competitors).

Never ask something you could have looked up. If a lookup is slow, send the questions that don't depend on it
meanwhile.

## 3. Coverage checklist

This defines "done". Keep it as a mental (or written) table, each topic marked **Clear / Partial / Missing /
Deferred**. Topics that don't apply are marked Clear with "n/a".

1. **Goal & problem** — what pain, for whom, why now; what success looks like (measurable when possible).
2. **Users / actors / stakeholders** — who uses it, who is affected, who approves.
3. **Scope** — what's in. Broken into capabilities or user stories.
4. **Out of scope** — what's explicitly NOT in (as important as scope; prevents creep).
5. **Flows & behavior** — main path, triggers, inputs → outputs. For processes: steps, handoffs, owners.
6. **Edge cases & errors** — empty, huge, invalid, concurrent, offline, partial failure, abuse, "what if X says no".
7. **Acceptance criteria** — how we'll verify it's done (Given/When/Then).
8. **Constraints** — tech stack, integrations, data, security/privacy, compliance, budget, people, tools.
9. **Priorities & phases** — MoSCoW; what's the MVP vs later.
10. **Timeline** — deadlines, dependencies on other work or people.

For business requirements also cover: KPIs, process owner, rollout/communication, what happens to the current way
of doing it.

## 4. Ask in rounds

Think of the open decisions as a tree. A round contains the **frontier**: the questions whose prerequisites are
already settled. Questions that depend on an unanswered one wait for a later round — asking them now wastes the
user's time because the answer may make them moot.

- **Order by impact × uncertainty.** Scope and goal first; details last. Skip questions whose answer wouldn't change
  what gets built or how it's tested.
- **Max ~5 questions per round.** More than that and answers get sloppy.
- **Every question carries your recommended answer, worded so "sí" accepts it.** The user should be able to answer a
  whole round with "1 sí, 2 sí, 3 b, 4 no porque…".
- **Mix formats:** multiple choice (a/b/c, recommended one marked) when the options are enumerable; open question
  with a suggested answer when they aren't. When the `AskUserQuestion` tool is available and a round has ≤4 closed
  questions, you may use it; otherwise write the round as text.
- **Talk in Spanish.** Files stay in English.

Round format:

```
**Ronda 2 — alcance y usuarios** (cobertura: 4/10 claros)

1. **¿Quién aprueba los pedidos?** a) el jefe de área b) finanzas c) ambos según monto
   ➡️ Recomiendo **c**: es lo que hace hoy el Excel de compras (columna "Aprobador").
2. **¿Qué pasa si el proveedor no responde en 48 h?** (abierta)
   ➡️ Sugiero: se escala al comprador y queda marcado en rojo.
...
```

Before round 1, play back in 2–4 lines what you understood and what you found while exploring, separating **what the
user said** from **what you're assuming**. That surfaces wrong assumptions cheaply.

### Grill Me depth check

When the user says "grill me", "grill-me", "interrógame" or asks to stress-test a design, use this same interview
with extra attention to the weakest unresolved decisions. After each answer, recompute the frontier: an answer
can invalidate a branch or expose a new dependency. Resolve facts from the code/tools before putting a decision
to the user; independent questions need not wait for unrelated exploration.

Challenge a consequential assumption with its concrete failure case or trade-off, then offer a recommended
answer. Do not invent objections to settled decisions. Track each branch as decided, deferred or an explicit
assumption; "exhaustive" does not mean an endless interview. The existing Quick track, five-question bound and
user stop conditions (§5) still apply. Before planning, play back the resulting understanding; plan approval
confirms it without adding another approval gate. A request to stress-test an existing approved plan does not
authorize implementation of proposed changes.

This adapts Matt Pocock's Grill Me/grilling prompts; source excerpts, revisions and license notices are in
[communication-and-context.md](communication-and-context.md). Do not call an unavailable `grilling` skill:
the interview lives here and works across harnesses.

### Rounds as files + web form (always, once a spec exists)

Every round is also posted as a file so the user can answer from the local web UI (works the same for Claude
Code, Codex or any agent — it doesn't depend on any vendor's artifacts):

1. Write the round as JSON (schema at the top of `scripts/bt_rounds.py`: `title`, `intro`, `coverage`,
   `questions[]` with `text`, `options[{key,label}]` + `recommended` + `why` for choices, or `suggested` + `why`
   for open ones) to a temp file, then `bitacora.py round new REQ-NNN --file <tmp.json>`. It prints the URL.
2. Show the same round in the conversation (format above) and add the URL: "o respóndela aquí: <url>".
3. Wait for whichever comes first:
   - **Claude Code:** run `bitacora.py round wait REQ-NNN` in the background (`run_in_background`); when it
     finishes you're notified with the answers. If the user answers in the chat instead, record them with
     `bitacora.py round answer REQ-NNN --file <answers.json>` (`{"q1": {"choice": "a", "note": ""},
     "q2": {"text": "..."}}`).
   - **Codex / others:** end your turn; when the user says they answered, `bitacora.py round show REQ-NNN`.
4. Continue with the next round from the recorded answers.

## 5. Record as you go, and when to stop

- Create the spec early: `py -3 <skill>/scripts/bitacora.py req new "<title>"` → gives you
  `requirements/REQ-NNN-<slug>/SPEC.md`. After each round, write the answers into the right sections (replace
  contradicted text, don't append duplicates) and add `Q → A` lines under `## Clarifications`.
- **Stop when** every topic is Clear or Deferred, **or** when the user says "listo / suficiente / dale / avanza".
  Remaining gaps become explicit **Assumptions** (your best guess + why) — never a blocker.
- If the user stops you early, still ask yourself: is there a single question whose wrong guess would waste days?
  If so, ask that one only.

## 6. Extra lenses (Deep track)

Pick 1–3 that fit, apply them yourself, and turn what you find into questions or assumptions:

- **Pre-mortem:** it's 3 months later and this failed — why?
- **5 whys** on the stated goal, to reach the real need.
- **Inversion:** what would guarantee failure?
- **Stakeholder round:** how does each actor (user, admin, finance, support, ops) see it?
- **Working backwards (business):** write the 5-line announcement for when it ships; does everyone agree?

## 7. Close the spec

Before moving on, run a self-check on `SPEC.md`:

- Every in-scope item has at least one acceptance criterion.
- Requirements are testable (EARS style: "When <trigger>, the system shall <response>").
- Out of scope is explicit. Success criteria are measurable.
- No placeholders, no contradictions, no "TBD" without an assumption next to it.

For Deep track, also send the `reviewer` subagent (axis `spec`) to read **only** the spec and list what's
ambiguous or contradictory; fix what it finds.

Then show the user a short summary (5–8 lines: what will be built, what won't, key assumptions) and **continue
straight into planning** — the approval gate is on the plan, not the spec (unless the user asked to review the
spec too). Log the
requirement and its key decisions in today's file. Next: `references/execution.md`.

## 8. Automatic hand-off

Once the spec and the plan are written, the work leaves this conversation: the interview filled this context with
exploration the implementation does not need. Plan in **milestones** — `### M1 — title` headings in PLAN.md, each a
small or medium, independently verifiable step (roughly 1–5 tasks that one clean session can finish) — and run:

```
bitacora.py --project P handoff REQ-NNN            # --dry-run first if you want to see the decision
```

It validates the plan (tasks, dependencies, repo roles) and decides:

- **No risk reasons → it approves the plan itself and starts the execution in the background** (a detached tmux
  session; notifications as usual). Tell the user in two lines what was started and how to watch or stop it.
- **Risk reasons → the plan goes to `review`** and the command lists them: more than 8 milestones or 40 pending tasks,
  a `level: architecture` or `risk: high` task, no machine-runnable verify anywhere, or text in the plan or spec that
  names an irreversible, production, git-remote, money, credentials or external-communication action. Show the user
  the plan summary and those reasons; when they approve (chat or web), run `handoff` again.

Each milestone then runs in a fresh session that receives only references: the spec, the plan, the bitácora
pointers, a context bundle, the agents available and the confirmed learnings. Everything that must survive is in
files: tasks and progress in PLAN.md/RUN.json, permanent decisions in `DECISIONS.md`, what was learned in the
project's learnings (`agents.md`). Stay in the conversation only for Quick and Agile work.

When user feedback or exploration reveals a reproducible defect, an agreed-requirement mismatch, or recurring
friction in this skill, investigate and make the smallest validated persistent improvement in the canonical skill
source as part of the approved scope. Record speculative ideas as proposals. If a user-controlled rule blocks the
requested behavior, pause that behavior and ask whether the user wants a one-time exception or a permanent change;
follow [`self-improvement.md`](self-improvement.md) for source boundaries and higher-priority rules.
