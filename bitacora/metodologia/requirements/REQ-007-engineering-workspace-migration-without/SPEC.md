---
id: REQ-007
status: planned
created: 2026-10-13
track: deep
---
# Engineering workspace migration without capability or data loss

## Problem and goal
David wants metodologia to become an engineering platform rather than a skill containing an engine. The platform must own orchestration, durable state, provider adapters, documents and the web UI. Agent skills are optional, thin integration surfaces; operating the platform must not depend on discovering or loading a SKILL.md.

This request delivers an inspected migration plan. Implementing it, configuring real accounts, buying Z.ai, publishing, deleting legacy files and changing live processes are not authorized by this planning request.

## Actors and flow
David sets intent and approves consequential changes; the coordinator creates requirements and plans; workers execute scoped tasks; an independent auditor evaluates evidence. Existing flow remains: intent → interview/spec → review/approval → task graph → dispatch → supervisor verification → milestone audit → report/bitácora. CLI, hooks and web invoke the same use cases. Interactive relay remains a separate continuity mechanism with durable handoff.

## Requirements
- R1. Before moving code or changing installers, capture all tracked, modified and untracked source, document/resource consumers, local state and install configuration in a restorable inventory. Preserve concurrent work and secrets outside published evidence.
- R2. After installation from a wheel, `bt`, `bitacora` and `python -m bitacora` work from any directory with all resources, without the source checkout or a skill directory. Editable install is convenience, not proof of packaging.
- R3. During the compatibility period, existing script paths, commands, JSON outputs, exit codes, hooks, URLs, environment variables and external launchers continue to work or have an explicit versioned adapter. Each old/new entry point invokes one implementation.
- R4. Migration preserves projects, requirements, IDs/high-water marks, plans, runs, rounds, decisions, learnings, artifacts, events, profile identities, quotas, quality metrics, relay state and local workspace maps. Unknown fields survive round trips. New readers reject unsupported schemas; an incompatible schema may activate only after older writers are verifiably excluded. An old executable cannot be assumed to honor a newly introduced version field.
- R5. All current execution capabilities survive: multi-repo workspaces, work-only gates, delegation, quotas and backoff, model/audit routing, verification, resumable marathon, task ownership, relay, platform launchers, notifications, secret scanning and trace links. Unknown telemetry stays null.
- R6. A provider adapter validates capabilities and owns invocation, environment filtering, streaming/result normalization, quota-error classification and cancellation. Provider identity, executable and account identity are distinct. Existing Antigravity behavior is characterized before replacement.
- R7. Provisioning is idempotent, diffable and reversible; preserves unrelated hooks/settings; separates “binary found”, “directory provisioned”, “authenticated”, “authorized for project” and “smoke verified”. No live config changes during plan generation.
- R8. Routing gives eligible new accounts a bounded opportunity without bypassing work-only, capability, quota, audit-independence or owner preference rules. Actual profile IDs are retained; aliases for a single account must not increase capacity.
- R9. Same-repo parallel writers each use a separate worktree and unique ref, including the first worker. Durable integration verifies the combined result and survives crashes without losing a branch, dirty file or acknowledged task. Serial operation remains supported.
- R10. Workflow disciplines become versioned platform-owned policy/resources with a small always-on router and optional adapters. Preserve existing governance, six agent roles, evals and user corrections. Adopt the eight named primitives with explicit invocation and attribution; no duplicate instruction ownership.
- R11. A pinned Archify adapter validates IR and output, stores source IR plus standalone HTML atomically, preserves the prior valid artifact on failure and registers links in the bitácora/web. Support the five requested diagram types; audit map/core flows and improve-architecture before/after reports are acceptance flows.
- R12. Optional phase 2 supports Z.ai as a distinct family using an isolated compatible CLI profile. Host auth cannot route to the wrong endpoint; quota errors differ from endpoint/auth/balance errors; unknown token breakdowns remain null. Credit scheduling uses verified rules and event-time semantics.
- R13. Cutover passes baseline, installed-package, contract, restore, crash-recovery, security and complete owner-workflow tests. A release report lists every capability, evidence and exception. Legacy removal is a later explicit decision, never an automatic cleanup.

## Definition of no loss
No missing bytes in preserved user-owned files; no reset IDs/history; no dropped unknown state fields; no duplicated acknowledged work after resume; no lost dirty/untracked changes; no silently removed commands or rules; no account identity or billing cross-contamination. Intentional behavior changes require separate evidence and acceptance, not relabeling them as refactoring.

## Scope and priorities
Must: R1–R9 and R13; migration and compatibility before expansion. R10–R11 remain planned phase-1 deliverables, but do not block validating core extraction in isolation. R12 is phase 2 and cannot block delivery of the existing provider platform. Local-first single-owner operation, current web server and Markdown/JSON storage remain. No SaaS, new database, plugin framework, custom credentials store or remote multiuser service in this proposal.

## Constraints and errors
Keep stdlib-only Python runtime if feasible; build tooling and optional Node renderer are separate dependencies. Python 3.12+ is a proposed support floor to prove in CI; observed baseline runs on Python 3.14.7. Windows/macOS claims require actual platform tests. Tests with provider billing/network are separate from deterministic gates. Missing Node disables diagram generation with a clear error, never the supervisor.

Cover invalid/truncated state, failed atomic replacement, full disk, stale/live locks, symlink/junction roots, non-ASCII/space paths, no shell PATH, partial stream events, quota windows, missing binaries/auth, signal interruption, merge conflicts and interrupted install/rollback. Do not infer dead processes from lock age alone.

## Assumptions and open choices
A1 (recommended, asked in chat): local CLI + web + durable supervisor is the product; lightweight skill adapters remain optional. If David wants no adapters at all or a remote service, revise R3/R10 before implementation.
A2: retain project/repo name metodologia and CLI names bt/bitacora; no rename of profile IDs or live data root.
A3: no deadline was supplied; order by risk and dependencies. Calibrate task durations after M0 instead of inventing delivery dates.
A4: retain current audited Gemini preference; reconcile conflicting test expectations in M1 with current owner decisions. Do not silently enforce the attachment's proposed model ladder.

## Coverage
Goal, actors, scope, flows, errors, acceptance, constraints and phases: clear in this proposal. Product surface: explicit A1 pending optional feedback. Timeline: deferred, no delivery deadline promised. Account purchase/activation and legacy deletion: outside this planning scope, phase gates recorded.

## Clarifications
- David requested analysis against code, a migration plan, milestones and acceptance without loss.
- David requested Claude Haiku with max effort for support; review runs record invocation and results.
- David requested all findings persisted under a folder named `migracion`; this folder is authoritative.
