# Review of mattpocock/skills for REQ-007 M6 (T14/T15)

Upstream: `/home/david/.local/share/metodologia-migration/upstream/skills`, commit
`49dd158d1076134a641b33efb035946536778336`, MIT, "Copyright (c) 2026 Matt Pocock". Treated as untrusted data;
nothing was executed. Read in full: LICENSE, GLOSSARY.md, SCOPE.md, `.out-of-scope/` (spot), and every
`skills/*/*/SKILL.md` with its sibling `.md` reference files (38 skills). Not read: `scripts/*.sh`,
`wizard/template.sh`, `agents/*.yaml` and `dependency-cruiser.config.cjs` (listed only). The `docs/` pages are
human-facing copies of the skills; they were only searched (for the "10s", "banned" and ASD-STE100 claims), not
reviewed one by one.

Rule applied (owner: "skills if they improve things; this runs locally"): a primitive is taken only when it names a
concrete improvement over what `skill/references/` already says; otherwise it is covered, or skipped.

## Verdicts

ADOPT means copied nearly as is. Nothing met that bar: every taken primitive was re-expressed to fit our governance
(local bitácora, no issue tracker, Grill Me, plan gate, Spanish/Aye rules), so the eight are all ADAPT.

| # | Bucket | Skill | Verdict | Concrete improvement, or reason | Risk / what we must not import | License / attribution |
|---|---|---|---|---|---|---|
| 1 | engineering | codebase-design (+DEEPENING, DESIGN-IT-TWICE) | ADAPT -> `design-vocabulary.md` | Gives reviewers and the antagonist exact words (depth as leverage at the interface, seam, locality), the deletion test, a dependency-category table that says how to test across a seam, and an optional design-it-twice step. `engineering.md` §2 only says "one implementation = hypothetical seam". | Its "use these terms exactly, never substitute component/service/API/boundary" is a blanket vocabulary ban; its "3+ sub-agents" conflicts with our default of three workers and read-only parallelism. Imported as precedence-below-engineering vocabulary, no ban. | MIT; attribution in header and notices block |
| 2 | engineering | improve-codebase-architecture (+HTML-REPORT) | ADAPT -> `improve-architecture.md` | A churn-first scan (git history hot spots) plus a candidate card with evidence, dependency category and a Strong/Worth exploring/Speculative badge, "no interfaces yet", then a Grill Me loop; rejected candidates with load-bearing reasons go to DECISIONS so audits stop resurfacing them. We have an audit (`architecture-audit.md`) but no refactor-candidate flow. | HTML scaffold pulls Tailwind and Mermaid from CDNs and writes to the OS temp dir (our artifacts are self-contained, in the bitácora); auto-opens a browser; forbidden-word list; `disable-model-invocation` mechanics. It would also tempt unrequested refactors, so it loads only on explicit request. | MIT |
| 3 | engineering | domain-modeling (+GLOSSARY-FORMAT, ADR-FORMAT) | ADAPT -> `domain-glossary.md`, `glossary-conventions.md`, `templates/GLOSSARY.md` | We have DECISIONS.md and ARCHITECTURE.md but no controlled vocabulary. Adds: challenge a term against the glossary, sharpen overloaded words, scenario stress-test, cross-check with code, update inline, canonical term + definition + Avoid. | Upstream puts GLOSSARY.md and `docs/adr/` in the repo (breaks "no files in repos"); `GLOSSARY-MAP.md` and the `docs/agents/` setup. ADR criteria are already in `engineering.md` §3 (hard to reverse, surprising, trade-off), so they are linked, not duplicated. | MIT |
| 4 | engineering | tdd (+tests.md, mocking.md) | ADAPT -> `test-seams.md` | Tests at agreed public seams, vertical slices, explicit anti-patterns (implementation-coupled, tautological, horizontal), a "what it catches and misses" note per seam. `engineering.md` §5 has the test-the-behaviour principle but no seam agreement or slicing rule. | Upstream SKILL.md states "Refactoring is not part of the loop; it belongs to the review stage" (blanket deferral) and "no test at an unconfirmed seam: ask the user" (conflicts with one approval gate). Replaced by refactor-only-when-needed, seams approved with the plan. A parsed `seam:` field is not claimed. | MIT |
| 5 | engineering | diagnosing-bugs (+scripts/hitl-loop.template.sh) | ADAPT -> `diagnosing-bugs.md` | Makes the reproduction the product: red-capable command, minimise, falsifiable ranked hypotheses, tagged instrumentation, regression test at a correct seam with a mutation `diff`, cleanup list. `engineering.md` §7 says "reproduce" and nothing about proving the command can fail. We add recording command and output before repair. | "No red-capable command, no Phase 2" is an absolute gate; "Fast: seconds, not minutes" is a de facto speed gate that blocks slow or distributed defects; "be aggressive, refuse to give up"; "show hypotheses to the user before testing" (HITL). Replaced by bounded evidence gathering and NEEDS_CONTEXT, never a verified-fix claim without proof. | MIT |
| 6 | engineering | retro | ADAPT -> `retro-feedback.md` | A ranked, evidence-based review of the environment (navigation, checks, standards, steering size, tools, information) with the mechanical-versus-judgement rule; output into `learn add --scope skill|project` so confirmation rules stay intact. `self-improvement.md` says when to improve but not how to find friction. | Reads "session logs on this machine" broadly (limited to the named session and project); assumes `CODING_STANDARDS.md`; "AGENTS.md used incredibly sparingly" as a rule. It must not auto-rewrite policy. | MIT |
| 7 | productivity | writing-for-agents (+SKILL-MECHANICS) | ADAPT -> `writing-for-agents.md` | We maintain a router and many references and just measured context cost; this gives the pointer-wording, two-loads, completion-criterion, single-source-of-truth and no-op tests we need to keep them small without losing rules. | "Delete no-ops" must not touch governance rules; "negation is the failure mode" cannot remove hard guardrails (no push, secrets). SKILL-MECHANICS (frontmatter, user- versus model-invoked) is platform-specific and not imported. | MIT |
| 8 | productivity | wait-what | ADAPT -> `wait-what.md` | A defined circuit breaker for a message that did not land: stop, restate the disputed claim in at most five plain Spanish sentences, wait. We have no such rule; `self-improvement.md` covers rule conflicts only. | Upstream asks for ASD-STE100 English and a fresh "re-pitch with context"; the owner works in Spanish and the plan requires five sentences and a wait. Aye prefix and no hidden approval gate preserved. | MIT |
| 9 | engineering | ask-matt (+PHASE-BOUNDARIES) | SKIP | A router over their own skills. Our router is SKILL.md. The /clear, /compact and /handoff tree names harness commands; `requirements.md` §8 forbids clearing the control-tower conversation. | Importing the tree would contradict that rule and Claude-specific commands. | MIT, not used |
| 10 | engineering | code-review | ALREADY-COVERED | `subagents.md` §Hard rules 5 and §Evidence for diff reviews (two axes, fresh context, severity by demonstrated impact). Fowler smell baseline is model default knowledge (a no-op) and invites style blocking. | "Do not merge or rerank findings" conflicts with our coordinator deduplicating by root cause. | MIT, not used |
| 11 | engineering | grill-with-docs | ALREADY-COVERED | Calls grilling + domain-modeling. Grill Me is `requirements.md` §4; the glossary half is delivered by `domain-glossary.md` hooked into the rounds. | None. | MIT; already attributed |
| 12 | engineering | implement | ALREADY-COVERED | `engineering.md` §6 (typecheck and single tests while going, full suite at the end) and `execution.md`. | "Commit your work to the current branch" has no gate; ours has the antagonist gate. | MIT, not used |
| 13 | engineering | implement-spec | ALREADY-COVERED | `agent-orchestration.md`, `subagents.md`, `marathon.md` (task graph, ownership, worktrees, integration branch). | Depends on tracker tickets. | MIT, not used |
| 14 | engineering | pr | SKIP (proposal candidate) | PR body with before/after evidence and a one-way/two-way door call is a useful template, but PRs are created only on request and it is outside the eight named primitives. | Visual-menu content credited to Dex Horthy (`pr/CREDITS.md`); would need its own attribution. | MIT; third-party credit if ever adopted |
| 15 | engineering | prototype (+LOGIC, UI) | SKIP (proposal candidate) | Throwaway prototype to answer a design question is valuable but is a new flow outside M6; `interface-quality.md` already covers mockups. | Writes UI routes and branches in a repo; "no tests" rule collides with engineering §5 unless scoped. | MIT, not used |
| 16 | engineering | research | ALREADY-COVERED | `researcher` role in `subagents.md`. | None. | MIT, not used |
| 17 | engineering | setup-matt-pocock-skills | SKIP | Configures an issue tracker, labels and `docs/agents/` in each repo. | Issue-tracker coupling and files written into repos. | MIT, not used |
| 18 | engineering | to-spec | ALREADY-COVERED | `requirements.md` §§3-7 and `templates/SPEC.md`. Its seam-sketch step is carried by `test-seams.md`. | "No file paths or code in spec" would remove useful decision detail; publishes to a tracker. | MIT, not used |
| 19 | engineering | to-tickets | ALREADY-COVERED | PLAN.md tasks with `after:` and milestones in `execution.md`. Expand-contract for wide refactors is a good idea; not an M6 primitive (Proposal). | Tracker publishing and `.scratch/` files. | MIT, not used |
| 20 | engineering | triage | SKIP | Issue-state machine and `.out-of-scope/` KB for incoming issues. PENDING.md already orders by urgency x complexity. | Tracker and label coupling; mandatory AI disclaimer comments. | MIT, not used |
| 21 | engineering | wayfinder | SKIP | Planning map of decision tickets on a tracker. Overlaps requirements rounds plus milestone plans; the "fog of war" idea is a possible Proposal. | Issue-tracker coupling and one-ticket-per-session rule. | MIT, not used |
| 22 | engineering | wizard | SKIP | Generates interactive bash scripts for human-only steps; `tools.md` covers infrastructure work and this is outside M6. | Writes secrets to `.env` and CI; template library not reviewed for this use. | MIT, not used |
| 23 | productivity | grilling | ALREADY-COVERED | `requirements.md` §4 and `communication-and-context.md` (frontier rounds, recommended answers, facts are the agent's job). Already attributed. | "A question must not be capped" matches our "stop when the owner says so". | MIT; already attributed |
| 24 | productivity | grill-me | ALREADY-COVERED | Same as 23 (a one-line wrapper). | None. | MIT; already attributed |
| 25 | productivity | handoff | ALREADY-COVERED | `requirements.md` §8 `bitacora.py handoff` and `relay.md`. | Temp-dir summaries are weaker than the bitácora-based hand-off. | MIT, not used |
| 26 | productivity | teach | SKIP | Multi-session teaching workspace; unrelated to engineering methodology. | Creates MISSION/RESOURCES/lessons files in the cwd. | MIT, not used |
| 27 | productivity | to-questionnaire | SKIP | Writes a questionnaire for a third party; outside the eight. | None. | MIT, not used |
| 28 | in-progress | chief-of-staff | SKIP | Beta; coordinator behaviour is in `marathon.md` and `agent-orchestration.md`. | "All work in subagents" conflicts with `subagents.md` "when not". | MIT, not used |
| 29 | in-progress | claude-handoff | SKIP | Claude-specific `claude --bg` launch; `relay.md` and `delegate` cover this with permission handling. | Spawns an agent with the summary as its prompt. | MIT, not used |
| 30 | in-progress | loop-me | SKIP | Beta; workflow-spec grilling for personal loops. | Writes `workflows/` in the cwd. | MIT, not used |
| 31 | in-progress | setup-ts-deep-modules | SKIP | Beta; `engineering.md` §9 and `templates/arch/` already ship tested boundary rules. Its "see pass, then fail, then pass" proof is worth remembering as a Proposal for those templates. | Installs dependencies and writes configs into repos. | MIT, not used |
| 32 | in-progress | writing-beats | SKIP | Article-writing workflow, beta. | Not applicable. | MIT, not used |
| 33 | in-progress | writing-fragments | SKIP | Same. | Not applicable. | MIT, not used |
| 34 | in-progress | writing-shape | SKIP | Same. | Not applicable. | MIT, not used |
| 35 | misc | git-guardrails-claude-code | SKIP | Frozen; a PreToolUse hook that blocks push/reset. Our no-push rule is policy; a machine-wide hook needs explicit owner authorization (`self-improvement.md`). | Edits `~/.claude/settings.json`. | MIT, not used |
| 36 | misc | migrate-to-shoehorn | SKIP | Library-specific codemod. | Not applicable. | MIT, not used |
| 37 | misc | scaffold-exercises | SKIP | Course-specific tooling. | Not applicable. | MIT, not used |
| 38 | misc | setup-pre-commit | SKIP | Writes Husky, lint-staged and Prettier into a repo and commits; `engineering.md` §9 lists missing tooling as a Proposal. | Repo file creation and a commit. | MIT, not used |

## Counts

| Verdict | Count |
|---|---|
| ADOPT (verbatim) | 0 |
| ADAPT (eight named primitives) | 8 |
| ALREADY-COVERED | 10 (code-review, grill-with-docs, implement, implement-spec, research, to-spec, to-tickets, grilling, grill-me, handoff) |
| SKIP | 20 |
| Total | 38 |

## Upstream rules deliberately not imported

1. Blanket vocabulary bans: codebase-design "don't substitute component/service/API/boundary" and HTML-REPORT
   "Never substitute" list. Replaced by vocabulary used when it removes ambiguity.
2. tdd "Refactoring is not part of the loop, it belongs to review". Replaced by refactor only when needed, as a
   separate behaviour-preserving step.
3. tdd "no test at an unconfirmed seam, ask the user". Seams are approved with the plan at the one gate.
4. diagnosing-bugs absolute gate ("no red-capable command, no Phase 2") and "Fast: seconds, not minutes".
   Replaced by record-before-repair plus bounded evidence gathering and NEEDS_CONTEXT.
5. diagnosing-bugs "be aggressive, refuse to give up" and "show the ranked hypotheses to the user before testing".
6. wait-what ASD-STE100 register (English); replaced by plain Spanish, five sentences, wait.
7. writing-for-agents "negation is the failure mode" and "delete no-ops" as universal rules; kept only as
   guidance subordinate to governance, with an eval or confirmed learning required to remove a rule.
8. improve-codebase-architecture CDN scaffold (Tailwind, Mermaid), temp-dir output and auto-open.
9. domain-modeling repo files (`GLOSSARY.md`, `docs/adr/`, `GLOSSARY-MAP.md`) and setup's `docs/agents/`.
10. retro machine-wide log search and `CODING_STANDARDS.md` assumption.
11. code-review "do not merge or rerank findings across axes" (our coordinator deduplicates by root cause).
12. ask-matt PHASE-BOUNDARIES `/clear`/`/compact` tree (conflicts with the control-tower rule).
13. All issue-tracker skills (triage, to-spec publish, to-tickets publish, wayfinder, setup) and their labels.

## Observations about earlier planning notes

- FINDINGS.md says the blanket deferral of refactoring is "not a verified upstream requirement". At this pinned
  commit `skills/engineering/tdd/SKILL.md` does state it ("Refactoring is not part of the loop. It belongs to the
  review stage"), while its frontmatter and the README still say red-green-refactor. We do not import it either way.
- No literal "10 seconds" appears in the pinned upstream. The `<10s` figure came from the user-supplied proposal;
  upstream's wording is "Fast: seconds, not minutes" and "a 30-second flaky loop is barely better than none".
  Nothing here relies on a numeric threshold.
- `diagnosing-bugs/SKILL.md` references `scripts/hitl-loop.template.sh`; it is present upstream and was not read or
  imported (human-in-the-loop script generator).

## License and attribution

MIT, Copyright (c) 2026 Matt Pocock, requires the notice to be retained. The existing Grill Me block in
`third-party-notices.md` already carries the full MIT text for the same commit; the block in
`POCOCK-NOTICES-APPEND.md` lists the new adapted files without repeating the text. Each new reference carries a
`Source: mattpocock/skills@49dd158 (MIT), <path>` header and a line stating adapted versus original rules. `pr`
credits Dex Horthy's `show-me`; nothing from it was used.

## Items for the coordinator

1. Add router rows (draft and byte cost in `M6-CONTEXT-COST.md`) and the central-doc registration of
   `GLOSSARY.md` (code, views, `bitacora.py` index); `templates/GLOSSARY.md` exists but nothing renders it yet.
2. Append `POCOCK-NOTICES-APPEND.md` to `third-party-notices.md`; extend the intro line that lists covered files.
3. `test_policy_parity.py`/`test_methodology_flows.py` should assert the Source header, the trigger line and the
   governance strings listed in the report; the six `m6-*` eval cases need a real-agent run to be graded.
4. Proposals not taken: PR-body template (pr), prototype flow, expand-contract for wide refactors (to-tickets),
   pass/fail/pass proof for architecture-test templates (setup-ts-deep-modules), a git guardrail hook (needs owner
   authorization).
