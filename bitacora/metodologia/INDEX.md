# Index — metodologia

_Generated 2026-10-15 11:43 by `bitacora.py index`. Do not edit by hand._

**Central:** [Summary](SUMMARY.md) · [Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · [Pending](PENDING.md) · [Tools](TOOLS.md)  
**Web:** [project](http://127.0.0.1:8765/p/metodologia) · [graph](http://127.0.0.1:8765/p/metodologia/graph)  
**Last activity:** 2026-10-15

## Workspace

- **skill** → `/home/david/dev/metodologia`
- **ops-matrix-cujggjqq** → `/tmp/ops-matrix-cujggjqq` (not cloned here)
- **ops-matrix-gwx4a4rl** → `/tmp/ops-matrix-gwx4a4rl` (not cloned here)
- **ops-matrix-pduh5t5x** → `/tmp/ops-matrix-pduh5t5x` (not cloned here)

## Needs attention

- REQ-003: executor finished — review & merge
- REQ-004: executor finished — review & merge
- REQ-005: executor finished — review & merge
- REQ-006: plan waiting for approval
- REQ-009: executor finished — review & merge
- REQ-010: executor finished — review & merge
- REQ-011: executor finished — review & merge
- REQ-012: executor finished — review & merge
- REQ-013: executor finished — review & merge
- REQ-015: plan waiting for approval

## Requirements

| ID | Title | Spec | Plan | |
|---|---|---|---|---|
| [REQ-001](requirements/REQ-001-deep-workspace-onboarding-and-architectu/SPEC.md) | Deep workspace onboarding and architecture assessment | `in-progress` | [done](requirements/REQ-001-deep-workspace-onboarding-and-architectu/PLAN.md) |  |
| [REQ-002](requirements/REQ-002-proactive-skill-guidance-and-permanent-i/SPEC.md) | Proactive skill guidance and permanent improvement | `in-progress` | [done](requirements/REQ-002-proactive-skill-guidance-and-permanent-i/PLAN.md) |  |
| [REQ-003](requirements/REQ-003-caveman-rtk-grill-me-integration/SPEC.md) | Integrate Caveman, RTK and Grill Me | `in-progress` | [done](requirements/REQ-003-caveman-rtk-grill-me-integration/PLAN.md) | report ✓ |
| [REQ-004](requirements/REQ-004-measured-context-efficiency/SPEC.md) | Measured context efficiency | `implemented` | [done](requirements/REQ-004-measured-context-efficiency/PLAN.md) | report ✓ |
| [REQ-005](requirements/REQ-005-rtk-runtime-measurement/SPEC.md) | RTK runtime installation and measurement | `implemented` | [done](requirements/REQ-005-rtk-runtime-measurement/PLAN.md) | report ✓ |
| [REQ-006](requirements/REQ-006-automatic-requirement-to-milestones-flow/SPEC.md) | Automatic requirement-to-milestones flow with learning | `ready` | [review](requirements/REQ-006-automatic-requirement-to-milestones-flow/PLAN.md) |  |
| [REQ-007](requirements/REQ-007-engineering-workspace-migration-without/SPEC.md) | Engineering workspace migration without capability or data loss | `planned` | [approved](requirements/REQ-007-engineering-workspace-migration-without/PLAN.md) |  |
| [REQ-008](requirements/REQ-008-fresh-milestone-orchestration-and-bounde/SPEC.md) | Fresh milestone orchestration and bounded context execution | `in-progress` | [paused](requirements/REQ-008-fresh-milestone-orchestration-and-bounde/PLAN.md) | report ✓ |
| [REQ-009](requirements/REQ-009-planner-plan-json-classification-contrac/SPEC.md) | Planner PLAN.json classification contract | `ready` | [done](requirements/REQ-009-planner-plan-json-classification-contrac/PLAN.md) | report ✓ |
| [REQ-010](requirements/REQ-010-isolated-planner-contract-module/SPEC.md) | Isolated planner-contract module | `ready` | [done](requirements/REQ-010-isolated-planner-contract-module/PLAN.md) | report ✓ |
| [REQ-011](requirements/REQ-011-scheduler-core-m1-isolated-deterministic/SPEC.md) | Scheduler Core M1: isolated deterministic module `bt_scheduler_core` | `ready` | [done](requirements/REQ-011-scheduler-core-m1-isolated-deterministic/PLAN.md) | report ✓ |
| [REQ-012](requirements/REQ-012-planner-phase-1-closure-strict-plan-sync/SPEC.md) | Planner phase 1 closure: strict PLAN sync, launch gate, evidence, real planning trials | `in-progress` | [done](requirements/REQ-012-planner-phase-1-closure-strict-plan-sync/PLAN.md) | report ✓ |
| [REQ-013](requirements/REQ-013-scheduler-m2-decision-engine-with-local/SPEC.md) | Scheduler M2 Decision Engine with local Laya | `implemented` | [done](requirements/REQ-013-scheduler-m2-decision-engine-with-local/PLAN.md) | report ✓ |
| [REQ-014](requirements/REQ-014-scheduler-m3-agent-executor/SPEC.md) | Scheduler M3 Agent Executor | `done` | [approved](requirements/REQ-014-scheduler-m3-agent-executor/PLAN.md) | report ✓ |
| [REQ-015](requirements/REQ-015-train-and-evaluate-local-laya-for-schedu/SPEC.md) | Train and evaluate local Laya for Scheduler routing | `clarifying` | [review](requirements/REQ-015-train-and-evaluate-local-laya-for-schedu/PLAN.md) |  |
| [REQ-016](requirements/REQ-016-train-and-validate-an-english-only-laya/SPEC.md) | Train and validate an English-only Laya Planner complexity classifier | `ready` | [approved](requirements/REQ-016-train-and-validate-an-english-only-laya/PLAN.md) |  |
| [REQ-017](requirements/REQ-017-scheduler-m4-agent-monitor/SPEC.md) | Scheduler M4 Agent Monitor | `in-progress` | [approved](requirements/REQ-017-scheduler-m4-agent-monitor/PLAN.md) |  |

## Top pending (urgency, then complexity)

- P-013 · Live bitácora backup: `~/bitacora` is now a symlink into the `metodologia` repo (origin =  · high/M
- P-017 · REQ-007 migration: T2 closed by D-015; T5/T6 done; T7 and F-M1-01 closed 2026-10-14; remai · high/L
- P-003 · Visual review of the local web UI · med/S
- P-001 · Executor status/heartbeat + notifications (toast/ntfy) + resume of crashed executors · med/M
- P-018 · [paused by owner] REQ-008: T4 implementation verified; acceptance/default activation and T · med/L
- P-005 · Prune SKILL.md after a few weeks of real use (eval-driven no-op test) · low/S
- P-006 · Marathon: pass the claude prompt via stdin instead of argv (cmd-shim 8191-char / newline r · low/S

## Recent decisions

- D-034 — M4 detector defaults remain deterministic, configurable, and advisory
- D-033 — M4 minimizes persisted data and uses bounded retention
- D-032 — M4 incidents are advisory and M1 remains authoritative
- D-031 — M3 exposes a separate bounded nonblocking stream to M4
- D-030 — M4 is an isolated observer with its own SQLite store

## Artifacts

- [council-report-20261008](http://127.0.0.1:8765/p/metodologia/view/council-report-20261008.html)
- [diagram-automejora-telemetria](http://127.0.0.1:8765/p/metodologia/view/diagram-automejora-telemetria.html)
- [diagram-automejora-telemetria.visual-check](http://127.0.0.1:8765/p/metodologia/view/diagram-automejora-telemetria.visual-check.html)
- [diagram-continuidad](http://127.0.0.1:8765/p/metodologia/view/diagram-continuidad.html)
- [diagram-continuidad.visual-check](http://127.0.0.1:8765/p/metodologia/view/diagram-continuidad.visual-check.html)
- [diagram-flujo-auditado](http://127.0.0.1:8765/p/metodologia/view/diagram-flujo-auditado.html)
- [diagram-flujo-auditado.visual-check](http://127.0.0.1:8765/p/metodologia/view/diagram-flujo-auditado.visual-check.html)
- [diagram-herramienta](http://127.0.0.1:8765/p/metodologia/view/diagram-herramienta.html)
- [revision-flujo](http://127.0.0.1:8765/p/metodologia/view/revision-flujo.html)

## Timeline

- **2026-10** — [month summary](2026-10/MONTH.md)
  - [W3](2026-10/W3/WEEK.md): [15](2026-10/W3/2026-10-15.md), [14](2026-10/W3/2026-10-14.md), [13](2026-10/W3/2026-10-13.md), [12](2026-10/W3/2026-10-12.md)
  - [W2](2026-10/W2/WEEK.md): [10](2026-10/W2/2026-10-10.md), [09](2026-10/W2/2026-10-09.md), [08](2026-10/W2/2026-10-08.md)
