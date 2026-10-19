---
req: REQ-002
status: done
created: 2026-10-10
---
# Plan — REQ-002 — Proactive skill guidance and permanent improvement

## Approach
Make capability discovery and self-maintenance explicit in the canonical skill source. The skill will surface only directly relevant features, apply evidenced low-risk fixes in the tracked methodology repository, validate them, and pause when a user-controlled rule blocks the requested behavior.

## Global constraints
- Canonical source: `/home/david/dev/metodologia`; do not edit generated installed copies as the source of truth.
- Preserve unrelated local changes. No commits or pushes.
- Apply only evidenced, low-risk, reversible skill-owned changes without asking; ask before global permissions/security, credentials, external services, destructive data or unrelated system settings.
- A rule conflict must be surfaced before the blocked action; ask one-time exception vs permanent change. Never offer to change higher-priority non-editable instructions.

## Tasks
- [x] T1 — Define contextual feature discovery, proactive self-improvement triggers, canonical-source boundaries and rule-conflict handling · files: `skill/SKILL.md`, `skill/references/self-improvement.md`, `skill/references/requirements.md`, `skill/references/execution.md`, `install.py` (only if its canonical defaults need alignment) · verify: `git diff --check` · covers: R1, R2, R3, R4, R5, R6, US-1, US-2, US-3
- [x] T2 — Add behavior evaluation cases for contextual feature discovery, evidence-based self-improvement and rule conflicts; validate case/grader structure · files: `evals/cases/`, `evals/graders.py`, `evals/README.md` · after: T1 · verify: `python evals/run.py --list` · covers: R1, R2, R3, R5, R6, US-1, US-2, US-3
- [x] T3 — Define the safe agent orchestration and long autonomous run playbook, adapt useful public patterns with attribution, and add no-cost evaluation cases · files: `skill/references/agent-orchestration.md`, `skill/references/subagents.md`, `skill/references/marathon.md`, `skill/SKILL.md`, `evals/cases/` · after: T1 · verify: `python evals/run.py --list` · covers: R7, R8, R9, US-4
- [x] T4 — Run full deterministic tests, review scope and document results; run the focused model evals only with the approved cost cap · files: `skill/scripts/tests/`, `evals/`, `bitacora/` · after: T1, T2, T3 · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v` · covers: R1-R9, US-1, US-2, US-3, US-4

## Verification
- Review the rendered skill instructions for clear contextual triggers, no repeated generic pitch, and a crisp split between skill-owned and global configuration.
- Verify rule-conflict examples ask whether to make a one-time exception or permanent change before acting, and keep higher-priority instructions out of scope.
- Run `python evals/run.py --list`, the full deterministic unittest suite and `git diff --check`.
- The focused model eval run may consume up to USD 1.50; it will run only if the user explicitly approves that cap. Otherwise record it as not run, not passed.

## Rulings
- User-owned global config is not modified by the general self-improvement authorization; the specific proposed change must be clearly authorized.
- A one-time exception never edits a persistent rule.

## Progress log
- 2026-10-10: Scope approved in requirements interview; Deep spec reviewed and aligned with user-controlled rules.
- 2026-10-10: David added orchestration/concurrency and long-autonomous-work requirements plus public-repo research. Added US-4 and R7–R9 to this plan by direct instruction; implementation stays inside methodology docs/evals and avoids external runtime or global-setting changes.
- 2026-10-10: T1 and T2 implemented: contextual guidance/self-improvement rules added; eval case list includes k/l cases and validates without model calls.
- 2026-10-10: T3 orchestration playbook added using DAGs, bounded waves, file ownership, isolated writers, durable checkpoints, and independent verification; no external runtime/config changes.
- 2026-10-10: T4 passed: full deterministic suite (80 tests) passed; focused onboarding suite (5 tests) passed after adding the re-audit check; `evals/run.py --list`, JSON parsing, `git diff --check`, and trace coverage for both REQs passed; the only trace issue is the existing dangling `P-012` entry. Paid model evals were not run (cost cap not authorized).

- 2026-10-10: Plan approved by David in chat (“procede”); execution started without using the CLI approval flow because that flow creates a commit.
