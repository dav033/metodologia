# Agents, routing and learning

Which agent does what, on which account, with how much effort — and how the system gets better at deciding. Any agent
can print the live version of this page for a project with `bitacora.py --project P context`.

## The catalog

| Model | Provider (CLI) | Tiers | Use it for |
|---|---|---|---|
| `haiku` — Haiku 5.5 | Claude Code | 0 | mechanical edits, docs, small well-specified tasks, running and reading tests |
| `sonnet` — Sonnet 5.5 | Claude Code | 1 (`--effort xhigh`) | everyday implementation, debugging, reviews |
| `opus` — Opus 5.5 | Claude Code | 2 (`--effort xhigh`) | architecture, hard debugging, audits of risky changes |
| `gpt-6-luna` — GPT-6 Luna | Codex | 0 (`medium`; docs `low`) | fast subagent work: well-specified modules, tests, docs, exploration |
| `gpt-6.1-sol` — GPT-6.1 Sol | Codex | 1 (`high`), 2 (`xhigh`) | implementation that needs judgment, independent audits, architecture |

Accounts are **profiles** (`bitacora.py profiles list|doctor`): a provider plus the variable that selects its account
(`CLAUDE_CONFIG_DIR`, `CODEX_HOME`). Only `work_only` profiles are gated (projects with `"work": true`). The table and
the ladder live in `scripts/bt_agents.py` (`MODELS`, `LADDER`): edit them there when a provider ships a model.
`bitacora.py agents` shows models, ladder, accounts and which ones are waiting for a usage-limit reset.

## How a route is chosen

A **route** is account + model + effort. Work is described by a **tier** (0 light, 1 standard, 2 top) and a **kind**
(`implement`, `test`, `docs`, `audit`, `research`; the PLAN line's `kind:`, otherwise inferred from the title).

1. **Tier.** A task starts at 0; `level: architecture` starts at 2; an audit and a task declared `complexity: L`
   start at 1 (a milestone session runs at the highest tier among its tasks). Every failed attempt
   (`failed`, `verify_failed`, `timeout`) climbs one tier. A usage limit or a stop never moves it.
2. **Candidates.** One route per account of the pool at that tier (`run --pool auto`, the default of `handoff`: every
   account allowed for the project; `--pool a,b` to restrict; the `routing.pool` setting does it machine-wide).
3. **Drop** accounts cooling down after a usage limit and work-only accounts on a non-work project.
4. **Order:** another provider than the one that just failed this task (or, for an audit, than the one that built
   the milestone); then the best measured success rate for that kind (only with 5+ judged attempts); then the account
   least used in the last 5 hours (weighted by model cost); then pool order.

The provider a session runs on never limits whom it may call: a Claude session delegates to Codex and a Codex
session to Claude with the same command. A run without a pool (`run --agent X` / `--profile X` alone) is pinned to
that agent and follows the historical ladder (`marathon.md`).

`bitacora.py --project P agents route --kind audit --tier 1` previews the choice with its reason.

## Quotas

Each subscription has its own limits, so the unit of quota is the account. When a session ends with a usage-limit
message the account is recorded in `.state/quota.json` until the reset it announced (unknown reset: 30 min, doubling
on consecutive hits, capped at 4 h; `config set quota.default_cooldown_min N`). The next session simply runs on
another account. A run waits only when **every** account of its pool is cooling down, and then until the earliest
reset, when it **starts again by itself** (the wait survives a reboot through the login-resume entry). Reset
announcements are understood in both forms: relative ("Resets in 166h43m") and absolute ("try again at Oct 13th,
2026 1:08 AM"). A delegation the router placed is sent again to another account when it hits a limit; add
`--wait-quota` to make it wait for the earliest reset when every account is out, instead of returning `usage_limit`
with `retry_after`. `bitacora.py agents quota-clear <profile>` forgets a cooldown by hand.

## Delegating from any session

```
bitacora.py --project P delegate start "<one bounded task>" --kind test --verify "<cmd>"       # router chooses
bitacora.py --project P delegate start "<task>" --profile codex-luis --model gpt-6-luna --effort high --allow src/x
bitacora.py --project P delegate start "<task>" --kind audit            # goes to another provider than yours
```

`--tier 0|1|2` asks for a capability level, `--allow` bounds what may change, `--background` returns an id for
`delegate status`. The caller receives a compact result, never the transcript: `verified` (the verify command passed),
`verify_failed`, `claimed` (only the agent's word: no verify was given), `partial`, `blocked`, `failed`, `timeout`,
`usage_limit`. A delegation runs with the account it names: the caller's own account variables are not inherited,
and with no account named, an inherited work-only account is gated like its profile.

## Milestones, sessions and the independent audit

A plan groups its tasks under `### M1 — title` headings. Each milestone is **one fresh session**: it receives every
pending task of the milestone, works them in order and gives each its own verdict; the supervisor verifies each task
on its own. A task the session never reached because one it depends on failed is `skipped` (no attempt counted); the
next session continues the unfinished milestone. With a pool, every milestone is then closed by an **audit session**
(`M1-audit`): an agent that did not build it, of another provider when possible, reviews the diff against the spec,
checks tests and docs, fixes what is wrong, writes `AUDIT-M1.md`, and the supervisor re-runs every verify of the
milestone. `run --no-audit` or `config set audit.mode off` turns it off. Plans without milestone headings run exactly
as before: one session per task.

Every session — builder or auditor — owns the cross-cutting work of its tasks: tests that would fail without the
change, the documentation the change makes stale, decisions in `DECISIONS.md`, and learnings.

## Telemetry: deciding with measurements

Every marathon session and every delegation appends one row to `.state/events/attempts-YYYY-MM.jsonl`: agent,
profile, model, effort, kind, tier, tasks, result, seconds, and the provider's own usage figures (a figure it did not
report is `null`, never 0). Each row also says **what** the work was and **why** it ended as it did:

| Key | Meaning |
|---|---|
| `kind` | implement, test, docs, audit, research |
| `complexity` + `complexity_source` | S, M or L: `declared` on the PLAN line (`· complexity: M`, `delegate --complexity`), else `inferred` (architecture-level → L, a session with 3+ tasks → M, otherwise S) |
| `attempt`, `tier`, `route_why` | which try this was, at which capability tier, and why the router chose that account |
| `outcome` | `verified`, `verify_failed`, `timeout`, `no_verdict` (the session ended without reporting), `agent_reported_failure`, `usage_limit`, `blocked_needs_human`, `escalated_by_agent`, `skipped_dependency`, `partial`, `stopped_by_user`, `claimed_unverified` |
| `why` | for a failure: each task's error (the verify output, the agent's reason); for a success: the evidence given |
| `usage` | tokens in/out, cache read/write, reasoning, total, cost reported; `quality` says what the CLI actually reported |

- `bitacora.py metrics` — per agent, profile, model and effort. `--by kind,complexity,agent,model,effort` regroups
  (`agent, profile, model, effort, kind, tier, project, complexity, outcome`). `--advice` prints plain-language
  observations.
- `bitacora.py metrics --attempts 5` — the last attempts, each as a key/value table (what, who, cost, outcome, why).
- `bitacora.py metrics --why` — per agent/model/effort/kind/complexity: how attempts ended, the reasons they failed
  and the evidence when they worked.
- Web: `/metrics` — the same tables (by agent, by kind, by kind and complexity, why it failed / why it worked, each
  recent attempt key by key), account/quota state and the ladder.
- `success_rate` only counts attempts that had a verdict (a usage limit is not the agent's failure);
  `tokens_per_done` appears only when every attempt of the group was measured.
- The router reads the same rows: a route with a clearly better record for a kind of work is preferred.

Read it with care: stronger models get the harder tasks, and a few attempts prove nothing.

## Learning

The agent accumulates what it learns about a project and about how its owner wants things done, with evidence:

```
bitacora.py --project P learn add "Invoices are filtered server-side; the client never holds the full list" \
    --evidence "T3: /api/invoices paginates, tests assume it" --source REQ-012/T3 --kind convention
bitacora.py learn add "The owner wants UI text in Spanish and code in English" --scope owner --kind preference \
    --evidence "corrected twice in review" --source REQ-012
bitacora.py --project P learn list --status candidate      # then: learn confirm L-004 | learn reject L-004
```

- A learning starts as a **candidate**. It becomes **confirmed** when the owner confirms it, or when three
  independent sources observed it (`config set learn.promote_after N`). The same source repeating itself does not
  count. A rejected learning stays rejected.
- Scopes: `project` (`<project>/learnings.json` + `LEARNINGS.md`), `owner` (preferences valid everywhere) and `skill`
  (improvements to this methodology; see `self-improvement.md`) in the bitácora root.
- Only **confirmed** learnings are injected: into every supervised session's prompt and into the SessionStart context
  of interactive sessions, with the count of candidates waiting. Anything that looks like a secret is refused.
- A permanent choice is not a learning: it goes to `DECISIONS.md` with the alternatives rejected.

## Settings (`bitacora.py config get | set KEY VALUE | unset KEY`)

| Key | Default | Meaning |
|---|---|---|
| `executor.display` | `background` | `background`: detached tmux session / systemd unit; `window`: a terminal window |
| `approval.auto` | `true` | the hand-off may approve a plan with no risk reasons |
| `approval.max_milestones` / `approval.max_tasks` | 8 / 40 | above this the plan needs the owner |
| `routing.mode` | `auto` | `auto`: the hand-off runs with the account pool; `fixed`: pinned to one agent |
| `routing.pool` | `[]` | restrict the pool to these profiles (empty: every allowed account) |
| `audit.mode` | `milestone` | `off` disables the audit sessions |
| `learn.promote_after` / `learn.inject_max` | 3 / 12 | sightings to confirm; learnings injected per session |
| `quota.default_cooldown_min` | 30 | cooldown when a usage limit does not announce its reset |
