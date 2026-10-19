---
req: REQ-001
status: done
created: 2026-10-10
---
# Plan — REQ-001 — Deep workspace onboarding and architecture assessment

## Approach
Keep deterministic workspace discovery in a new CLI module and architectural judgment in the AI workflow. New-project initialization triggers an owner interview; `bitacora.py audit` provides a repeatable inventory for existing projects. The agent then performs per-repo analysis, cross-repo synthesis, one independent review and documented coverage.

## Global constraints
- Treat all owner-confirmed frontend/backend repositories as one product workspace.
- Scan only registered repositories, shared workspace documents and candidates inside the configured workspace root; ask before including candidates.
- Never read secret values, edit product code, run networked/state-changing checks, commit or push.
- Inspect local check commands before running them; record skipped/blocked checks and preserve unrelated working-tree changes.
- Do not declare a complete audit if an owner-confirmed repo or independent reviewer is missing.

## Tasks
- [x] T1 — Add deterministic workspace audit inventory and `bitacora.py audit` output, including stale/missing registered paths and likely unregistered repo candidates within the configured root · files: `skill/scripts/bt_audit.py`, `skill/scripts/bitacora.py`, `skill/scripts/bt_workspace.py`, `skill/scripts/tests/test_audit.py` · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest skill.scripts.tests.test_audit -v` · covers: R3, R4, US-2
- [x] T2 — Trigger onboarding for a new bitácora and persist confirmed product intent for later audits · files: `skill/scripts/bt_views.py`, `skill/scripts/tests/test_onboarding.py`, `skill/templates/SUMMARY.md`, `skill/SKILL.md` · after: T1 · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest skill.scripts.tests.test_onboarding -v` · covers: R1, R2, R3, US-1, US-2
- [x] T3 — Add the deep architecture-audit workflow and result rules for multi-repo synthesis, independent review, safe checks, coverage and PENDING updates · files: `skill/references/architecture-audit.md`, `skill/references/documentation.md`, `skill/templates/ARCHITECTURE.md`, `skill/SKILL.md` · after: T2 · verify: `git diff --check` · covers: R5, R6, R7, R8, R9, R10, R11, R12, R13, US-1, US-2, US-3
- [x] T4 — Run the end-to-end audit fixture and full deterministic suite; update the methodology bitácora with evidence and remaining gaps · files: `skill/scripts/tests/`, `bitacora/` · after: T1, T2, T3 · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v` · covers: R1-R13, US-1, US-2, US-3

## Verification
- Unit-test the CLI against a temporary project with frontend/backend repos, an unregistered candidate, a missing registered repo and a project with no implementation repos.
- Confirm JSON inventory is stable, bounded by the configured root, read-only and explicit about missing paths.
- Exercise new-project context and a repeated audit; verify purpose answers are reused and coverage is partial when a repo/reviewer is unavailable.
- Run the full Python unit suite and `git diff --check`.

## Rulings
- CLI inventory is deterministic and read-only; only the AI agent conducts the interview, interprets architecture and writes prose.
- Candidate repositories inside the root are presented for owner confirmation and are not auto-registered.

## Progress log
- 2026-10-10: Scope approved in requirements interview; Deep spec reviewed with no blocking findings.
- 2026-10-10: T1 implemented and independently verified: audit inventory is read-only and bounded; 5 focused tests pass, including remote credential redaction.
- 2026-10-10: T2 implemented and independently verified: new-project context triggers interview; SUMMARY records owner-confirmed date; 3 focused tests pass.
- 2026-10-10: T3 workflow and templates added; independent reviewer and coverage rules, safe inspections/checks, and partial-audit handling are explicit.
- 2026-10-10: T4 passed: the full deterministic suite (80 tests at that point) passed; the focused onboarding suite (5 tests) also passed after the final re-audit assertion; inventory fixture covers registered frontend/backend, missing/stale/mismatched paths, bounded candidate discovery, no source reads and no state writes. `git diff --check` passed.

- 2026-10-10: Plan approved by David in chat (“procede”); execution started without using the CLI approval flow because that flow creates a commit.
