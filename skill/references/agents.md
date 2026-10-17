# Agents, routing and learning

Which agent does what, on which account, with how much effort — and how the system gets better at deciding. Any agent
can print the live version of this page for a project with `bitacora.py --project P context`.

## Documented owner Planner policy (2026-10-17; D-064)

The default Planner is GPT-6 Astra (`gpt-6-astra`) **high**; its fallback is Claude Opus 5.5 (`claude-opus-5-5`) **xhigh**. Astra high was measured in the native Planner pilot; Opus xhigh was not. This documents the selected policy without changing runtime configuration. Account profiles and fallback activation conditions are not yet pinned. Preserve D-054's explicit caller selection and prohibition of silent substitution within a pinned request.

## Documented owner reviewer policy (2026-10-17; D-063)

The selected review pair is GPT-6.1 Sol (`gpt-6.1-sol`) **medium** and Claude Sonnet 5.5 (`claude-sonnet-5-5`) **medium**. For more difficult reviews, use the respective model's **high** variant. The owner has not specified a numerical difficulty threshold. This supersedes earlier reviewer-model proposals as the desired policy.

This decision is documented only, at the owner's request. The runtime routing/catalog descriptions below have not been changed to implement it. Formal REQ-024 account profiles still require explicit pinning; the experiment's accounts are not automatically the formal reviewer identities.

## Documented owner Explorer policy (2026-10-17; D-065)

Default: GPT-6 Luna (`gpt-6-luna`) **high**. For complicated exploration, use GPT-6.1 Sol (`gpt-6.1-sol`) **medium**; Claude Sonnet 5.5 (`claude-sonnet-5-5`) **medium** is an alternative to Sol medium. Haiku is not selected. No numerical complexity threshold or production account is specified; future Sol comparisons use `codex-2` by owner instruction.

This is the selected policy, not a runtime rollout. The source Explorer still declares Claude `haiku` and Codex `low` effort; checked installations retain those values, and generated Codex roles inherit the model unless otherwise selected. P-110's experiment closure remains pending independently of this decision. See `artifacts/explorer-ladder-20261017/matched-comparison.json` for the bounded quality and format evidence.

## The catalog

| Model | Provider (CLI) | Tiers | Use it for |
|---|---|---|---|
| `haiku` — Haiku 5.5 | Claude Code | 0 | mechanical edits, docs, small well-specified tasks, running and reading tests |
| `sonnet` — Sonnet 5.5 | Claude Code | 1 (`--effort xhigh`) | everyday implementation, debugging, reviews |
| `opus` — Opus 5.5 | Claude Code | 2 (`--effort xhigh`) | architecture, hard debugging, audits of risky changes |
| `gpt-6-luna` — GPT-6 Luna | Codex | 0 (`medium`; docs `low`) | fast subagent work: well-specified modules, tests, docs, exploration |
| `gpt-6.1-sol` — GPT-6.1 Sol | Codex | 1 (`high`), 2 (`xhigh`) | implementation that needs judgment, independent audits, architecture |
| `gemini-3.8-flash-low` — Gemini 3.8 Flash low | Antigravity CLI (`agy`, Google AI Pro) | 0–1 | **default auditor** (D-004); reserve builder when Claude and Codex are exhausted; not for interactive or urgent work |
| `gemini-3.8-flash-medium` | Antigravity CLI | 2 (only on escalation) | long-horizon agentic work; not measured, 2.5× slower than low |
| `gemini-3.8-flash-high` | Antigravity CLI | never automatic | avoid: timed out (900 s) twice on a task that low solved |

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
4. **Order:** for implementation, another provider than the one that just failed this task. For audits: another
   provider than the builder's first (D-004 independence), then the configured auditor (`audit.provider`) while it
   has room, then the best
   measured audit success rate (5+ judged attempts), then the audit budget order (Claude Sonnet and Flash before
   Codex Sol; subscription headroom does not push an audit to Codex), then fresh real subscription headroom. For
   implementation, headroom comes before the measured success rate, and a provider/model with fewer than five
   judged attempts of that kind is tried first (bounded cold start: five attempts, then its own rate decides; it
   never overrides avoidance after a failure, cooldowns, work-only gates or the audit order). Last tie-breakers: the account
   least used in the last 5 hours (weighted by model cost); then pool order.

The provider a session runs on never limits whom it may call: a Claude session delegates to Codex and a Codex
session to Claude with the same command. A run without a pool (`run --agent X` / `--profile X` alone) is pinned to
that agent and follows the historical ladder (`marathon.md`).

`bitacora.py --project P agents route --kind audit --tier 1` previews the choice with its reason.

## Antigravity (Gemini 3.8 Flash): the default auditor (D-004)

Antigravity is a **machine-local account**, like `claude-work`: `bitacora.py profiles add antigravity --provider
antigravity` (needs `agy` installed and signed in; `agy` over SSH prints a URL and asks for the pasted code). It is not
a built-in profile, so a machine without it routes exactly as before. The pool only includes it while its OAuth token
exists.

- **Audits go to Flash low first** (`audit.provider`, default `antigravity`; `claude`, `codex` or `none` change or
  disable the preference). The audit still prefers a provider other than the builder's. The Sonnet-medium / Opus-high /
  Sol budget below is the fallback and the escalation.
- **Flash builds only as a reserve**: for implement/test/docs/research it ranks behind Claude and Codex, so it is chosen
  when they are exhausted or avoided after a failure.
- **Never medium/high automatically**: the ladder is low, low, medium (tier 2). A failure moves work to another
  provider instead of raising Flash's effort (measured: higher effort costs 2.5–3.5× the time without better answers).
- **Quota**: `agy --print=/usage` reports the Gemini pool (five-hour and weekly) and the shared Claude+GPT pool of
  Antigravity, with no model turn. The router refreshes it at most every 15 minutes; above 85 % used Flash stops being
  the preferred auditor, at 100 % the account is excluded until its reset. Stale or missing data is unknown headroom.
- **Safety rails for the provider's terms**: Google's FAQ says wrapping `agy -p` in applications or rotating accounts
  is not supported under consumer plans. This setup uses **one account, no rotation**, one headless session per audit,
  with `--print-timeout` set to the session timeout. The owner accepted that risk on 2026-10-13.
- Measured behaviour (73 runs, `pending-artifacts/agy-benchmark-2026-10-13/`): 1.00 on 8 hard tasks at low, no false
  positives in the security review with decoys; 3–6× slower than the other providers; ~0.2 % of the weekly Gemini quota
  per run.

## Audit budget policy

| Situation | Model and effort |
|---|---|
| Normal milestone audit or final review | Sonnet 5.5 `medium` |
| High-risk/architecture milestone or a concrete failure needing escalation | Opus 5.5 `high` |
| Provider | The router's best measured route, different from the builder's provider (Sol `medium`/`high` when it is Codex) |

Audit routing uses its own ladder; it never inherits the builder's model or xhigh/max effort. A run pinned to a
provider keeps that provider but uses its audit defaults. Explicit model/effort flags on a delegation remain
overrides. High-risk (`risk: high`) or architecture members raise their milestone audit to tier 2; ordinary audits
start at tier 1. On resume, preserve a prior escalation. Quota exhaustion changes accounts, not capability tiers.

Keep small changes as inline self-review. For substantive milestones, perform one fresh audit session with the
existing spec/standards lenses, rather than adding full audits per task. Independence means a separate clean
session with requirements, diff and relevant consumers; another provider is optional, not a reason to override the
budget. Review corrections and affected paths on follow-up instead of repeating unaffected investigation.
The final review consolidates milestone evidence and remaining cross-milestone risks, rather than restarting every
completed audit. No xhigh/max by default; escalate for recorded risk or demonstrated difficulty, not file count.

## Scheduler M2 route recommendations (D-057)

D-057 applies only when the Scheduler routes an approved task DAG through M2. That path uses the validated task
floor and fresh effective-account quota to recommend a provider, model, effort, profile and account reference. Its
projection reports the quota observation, validity, usage and stable selection or unavailable reason. M1 still
revalidates READY work and owns reservations and dispatch. This policy does not change standalone or pinned legacy
routing, and D-004's independent audit routing and default auditor remain in force.

## Quotas

`bitacora.py usage poll` samples subscription counters without model calls; `usage show` reads the cache. On Linux,
`usage install-timer` explicitly installs/enables an hourly user-systemd timer, and `usage timer-status` shows its
state. The timer survives logouts/reboots according to the user's systemd session; it runs when the machine/user
manager is available, with a catch-up after missed hours. No inference session or agent is used for sampling.
The hourly due guard allows the timer's 120-second accuracy/jitter margin, so a slightly earlier tick does not skip
an entire hour. Provider Retry-After deadlines remain authoritative.

Codex uses `app-server` initialization and `account/rateLimits/read` only, never thread/turn creation. Claude uses
its existing local OAuth credentials for `GET https://api.anthropic.com/api/oauth/usage`; that endpoint is not a
stable public API and can fail. Do not refresh credentials, change accounts or attempt a browser challenge workaround
from the collector. Auth/network/schema errors remain explicit per-account statuses; challenges stop automatic
requests for that account until manually resolved and the collector error state is explicitly cleared.

Latest schema-v1 samples live in `.state/subscription-usage.json`; monthly metadata history lives in
`.state/events/subscription-usage-YYYY-MM.jsonl`. Store percentages, reset timestamps, profile and safe error codes,
never tokens, raw API responses or account identities. Profiles selecting the same configured account share a sample.

The router uses the largest consumed percentage of the active 5-hour and weekly windows, including Sonnet/Opus
weekly quotas when supplied. Lower usage gets priority within otherwise eligible routes, before historical success
and local load; provider/audit preferences and work-only gates still apply. Data older than two hours, a failed
latest read, missing windows or an elapsed reset means unknown headroom, not zero usage. Known exhaustion continues
to exclude an account until its reported reset even if a subsequent read fails. Routing never performs network
calls. Explicit account pins remain pins; automatic selection and quota rerouting use the cache.

Primary protocol references: [Codex rate limits](https://learn.chatgpt.com/docs/app-server#6-rate-limits-chatgpt)
and [Claude usage endpoint report](https://github.com/anthropics/claude-code/issues/31021). These are subscription
utilization percentages, not literal remaining-token counts or API-dollar estimates.

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

**No host preference (owner rule, 2026-10-13).** Choose the best model for the situation, never the provider that
hosts the current session. The host's own subagent tool (e.g. Claude Code's `Agent`) only reaches its own provider,
so use `delegate` (router) for anything that should be able to land on another provider, and for every audit pick a
provider different from the builder's. The only reasons to exclude a route are quota cooldown, an account not allowed
for the project, or a measured worse success rate for that kind.

```
bitacora.py --project P delegate start "<one bounded task>" --kind test --verify "<cmd>"       # router chooses
bitacora.py --project P delegate start "<task>" --profile codex-luis --model gpt-6-luna --effort high --allow src/x
bitacora.py --project P delegate start "<task>" --kind audit            # Sonnet medium; Sol medium fallback
```

## Normal sessions

From an interactive session, use `delegate start` for one bounded task; add `--retries 1..3` to climb one tier after
failures or `--worktree` to isolate it on a branch. Use `bitacora review [--base REF] [--focus TEXT] [--provider ...]`
for an independent read-only audit, and `delegate resume ID` after an interrupted process. Read the compact JSON
result and its attempt/route fields; never read the session log as the result.

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
(`M1-audit`): a fresh session under the audit budget policy reviews the diff against the spec,
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
| `usage.quality` = `partial` | a Claude session cut by a limit or a kill has no final result event: tokens are the sum of the assistant messages seen (a lower bound, source `claude-stream-json-partial`) |
| `loss` | `usage_limit`, `out_of_credits` or `auth` when the PROVIDER cost the attempt (quota, credits, sign-in), else null. Telemetry only: it never changes how a session is settled |
| `error_excerpt` | the last error line the provider printed (bounded, secrets filtered), so a failed attempt says why in its own words |
| `change_size` | files, insertions, deletions, commits and test files the session changed, to compare models on similar work |
| `origin` | `real`, or `synthetic` for smoke and matrix checks (`BITACORA_ORIGIN=synthetic`); `metrics --origin real` leaves those out |

`model` remains the requested route for compatibility; new rows also carry `requested_model`,
`reported_model` (currently null without provider identity evidence), and `identity_source: requested`.
Do not describe a requested alias as a verified effective model. Codex JSON `turn.completed` usage is supported
alongside the textual total; cached input is already included in Codex's input count and must not be added again.
Invalid JSONL rows are counted and skipped with a diagnostic, preserving valid later rows. Invalid session numbers
cannot enter quality histories. Duration aggregates include `seconds_measured` and `seconds_coverage`; missing
durations stay null, and averages use measured durations only. Model advice compares elapsed time only with
enough duration measurements in every candidate group. Daily `globalusage` uses the same reader/aggregator and
shows token/cost coverage rather than turning unknown measurements into zero.

- `bitacora.py metrics` — per agent, profile, model and effort. `--by kind,complexity,agent,model,effort` regroups
  (`agent, profile, model, effort, kind, tier, project, complexity, outcome`). `--advice` prints plain-language
  observations.
- `bitacora.py metrics --attempts 5` — the last attempts, each as a key/value table (what, who, cost, outcome, why).
- `bitacora.py metrics --why` — per agent/model/effort/kind/complexity: how attempts ended, the reasons they failed
  and the evidence when they worked.
- Web: `/metrics` — the same tables (by agent, by kind, by kind and complexity, why it failed / why it worked, each
  recent attempt key by key), account/quota state and the ladder.
- `provider_loss`, `failed_by_loss` and `success_rate_excl_loss` show how much of the failure rate was the provider's
  (credits, sign-in) and not the model's; `success_rate` itself is unchanged because the router reads it.
- `audits_done` and `audits_unreported` count supervised audits and how many never reported `--findings`: with
  `audits_unreported == audits_done` the quality columns have no data, and that is a process gap, not a clean record.
- `success_rate` only counts attempts that had a verdict (a usage limit is not the agent's failure);
  `tokens_per_done` appears only when every attempt of the group was measured.
- The router reads the same rows: a route with a clearly better record for a kind of work is preferred.

**Quality by defects.** `success_rate` only says the verify command passed. A milestone audit (synthetic
`Mn-audit` task) reports `task done REQ Mn-audit --evidence ... --findings N --severity high=N,med=N,low=N` (N >= 0,
severities add up to N, 0 when clean). On an accepted audit the supervisor appends one row to
`.state/events/defects-YYYY-MM.jsonl` (idempotent per audit attempt): auditor, findings, severity, and the builder
attempts it is attributed to (each done task's last accepted attempt, any kind except audit; earlier failed attempts
count as rework). The auditor is never judged on its own findings. `metrics` adds per group `audited`, `findings`,
`findings_per_audited_task`, `high_findings`, `rework_attempts`, `rework_rate` (attempts of the summary's failed class
that failed before the accepted one, over done + failed; an escalation counts in `rework_attempts` only) and
`tokens_per_clean_task` (tokens of the audited attempts with 0 high findings only, over their count; null if any
of them lacks a token count); unknown is `null`, and
`advice` mentions quality only for groups with enough audited tasks. Limits: findings exist only for audits that
reported the flag (an audit without it is `null`, not 0); a milestone's findings (and each severity bucket) are split into equal
shares across the attributed attempts, so fractional values are normal and group totals add up to the audits' totals; samples are small; Claude's tokens exclude cache and Codex reports no cost.

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
- SessionStart (including generic cwd/HQ), supervised prompts and `context` share `learn.inject_max`.
  Project, owner and skill rules are interleaved; a large global history cannot exclude all project rules.
  Only cosmetic spelling differences deduplicate: negation, order and comparison operators preserve identity.
  Rejection reasons also pass the secret filter. Invalid storage yields an explicit warning in context.
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
| `audit.provider` | `antigravity` | provider preferred for audits (`claude`, `codex`, `none`) while it is available |
| `learn.promote_after` / `learn.inject_max` | 3 / 12 | sightings to confirm; learnings injected per session |
| `quota.default_cooldown_min` | 30 | cooldown when a usage limit does not announce its reset |
