# Contextual guidance and self-improvement

Use this reference when the user's goal may benefit from a methodology capability they may not know, when feedback
suggests the skill should change, or when a rule blocks the requested behavior.

## Surface a capability only when it matters

Explain a capability when all of these are true:

- The user's goal directly matches a feature or workflow this skill provides.
- That capability could change the approach, reduce meaningful effort, improve the result, or help the user make a
  decision.
- It has not already been explained in this workflow.

Name the capability and its practical effect in one short, contextual sentence, then continue with the task. Examples:
for a multi-repository product, explain that the architecture audit can map the repositories as one product; for a
request with a reviewed plan likely to run for days, explain that marathon mode checkpoints tasks and can resume after
interruption; for a project-status question, explain that SUMMARY, PENDING and recent logs provide the durable
status. Do not recite the skill's feature list, announce the skill on unrelated tasks, or repeat an explanation the
user has already received in the current workflow.

## When to make a permanent improvement

Treat these as evidence to investigate:

- Direct user feedback or correction.
- A defect that can be reproduced, or a deterministic check that exposes a failure.
- A confirmed mismatch between behavior and an agreed requirement.
- The same avoidable friction recurring across sessions.

Inspect the relevant implementation and its consumers before editing. Fix the cause with the smallest durable change
that meets the evidence: skill-owned code, instructions, tests, templates, defaults or preferences may be changed.
Preserve unrelated work, run meaningful checks, and report the exact result. If a check is blocked, report it as
unverified. An untested hunch or isolated speculative enhancement is a proposal, not authority to change behavior.

The canonical source is the tracked methodology repository at `~/dev/metodologia`. Installed copies and symlinks
are generated outputs; edit the canonical source. Run an installer only when the user has authorized that specific
installation update. General permission to improve the skill does not authorize changes to machine-wide Codex or
Claude settings. Change global settings only when the exact setting change is clearly authorized, and preserve
unrelated customizations. Ask before changing security permissions, credentials, external services, destructive
state, or unrelated system configuration.

## When a user-controlled rule blocks the goal

Before doing the blocked part, identify the exact rule and its source, explain the practical impact, and ask which
scope the user wants:

1. **One-time exception** for this task, leaving the standing rule intact; or
2. **Permanent rule change**, naming where it would apply (this skill, one repository, or a user-wide/shared
   preference).

Pause only the behavior that the rule blocks; continue independent work where possible. A permanent update to a
shared repository or global preference takes effect only after the user chooses it. Do not silently ignore, weaken,
or rewrite a rule to make the task pass. Do not offer to change or bypass higher-priority instructions that the skill
cannot edit; explain the limit and offer an allowed alternative. Apply the instruction hierarchy that governs the
current task when multiple rules conflict.

## Record and report

For accepted persistent skill improvements, update relevant tests and documentation along with the implementation.
Keep the repository's progress/requirement artifacts current when the work is already part of a tracked requirement.
Report what changed, why the evidence justified it, checks and their actual results, and anything still unverified.
Do not commit or push unless separately requested.
