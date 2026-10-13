# Handoff — executor

You are the **executor** for REQ-001 — REQ-001 — Invoice list: filters and shared-element motion (project `maros-lab`).
A planning session (the HQ) already interviewed the user, wrote the spec and the plan, and the user **approved the plan**. Do not ask for approval again and do not re-run the interview.

## Read first
- Spec: `/home/david/bitacora/maros-lab/requirements/REQ-001-invoice-list-filters-and-shared-element/SPEC.md`
- Plan: `/home/david/bitacora/maros-lab/requirements/REQ-001-invoice-list-filters-and-shared-element/PLAN.md` (its Progress log tells you what's already done if this is a resume)
- Project bitácora: `/home/david/bitacora/maros-lab` — SUMMARY.md, ARCHITECTURE.md, PENDING.md, DECISIONS.md
- Workspace (project `maros-lab`), working directory `/home/david/dev/maros-lab`. Repos by role:
  - **frontend** → `/home/david/dev/maros-lab/maros-next`
- Tools & infra: `/home/david/bitacora/maros-lab/TOOLS.md` and shared `/home/david/bitacora/TOOLS.md` (servers, hosting CLIs, storage — see references/tools.md)

## How to work
- Follow the `metodologia` skill: references/execution.md §2–§5 and references/engineering.md (+ the matching stacks/*.md).
- Permission prompts are disabled for this session. That makes you fast, not reckless: the stop-and-ask list in execution.md §2 still applies (destroying unrecoverable data, push/deploy/publish, external messages, payments, credentials). Everything else: decide, record a ruling, keep going.
- Delegate per references/subagents.md: explorer / researcher / runner for context-heavy reads, an implementer per task (one at a time), reviewer x2 (spec + standards) after each phase, and the antagonist before EVERY commit (one review + at most one re-review; you triage: fix now or defer to PENDING.md with urgency/complexity).
- Start every message to the user with `Aye`.
- Git, per repo: create branch `feat/req-001-invoice-list-filters-and-shared-element` in **every** repo you touch (same name in all), commit there after each green phase, run each repo's own verification; never push without asking. The change ships as one unit: all those branches get merged together.
- Each plan task says which repo (role) it belongs to; keep cross-repo contracts (API shapes, types) in sync within the same phase.
- Keep PLAN.md's checkboxes and Progress log current after every phase: it's how a resumed or new session continues.
- Log to the bitácora as you go (your session section is created by the SessionStart hook).

## Done means
Every task ticked, the plan's Verification passes with evidence, fresh-eyes review done, spec/plan statuses updated, bitácora updated (day log + walkthrough, PENDING, SUMMARY), and a final report in Spanish (built / verified / rulings / needs your eyes / proposals / pending). Also write that report to `/home/david/bitacora/maros-lab/requirements/REQ-001-invoice-list-filters-and-shared-element/REPORT.md` (sections: Built, Verification evidence, Rulings, Needs your eyes, Proposals, Pending, Walkthrough) and set PLAN.md `status: done` — the web UI's Review tab shows it and offers the merge.

## Run mode
A marathon supervisor runs this plan: each session is fresh and handles exactly what its prompt names: ONE task, or every pending task of ONE milestone (`### Mn` group), or the audit of a milestone. Do only that, give each task its verdict with `bitacora.py task done` or `task fail`. Do not run the final review or write REPORT.md unless the prompt says so.
