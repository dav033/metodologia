# SP-3 / SP-4 draft semantic self-review

This is the Planner's self-review, not an independent audit or owner acceptance.

- Product decisions: round 9 q1–q7 are open. Alternate table creation, pricing, Backing surface, Blender acquisition, save mode, project contents and foreign edits remain unresolved; scoped Inputs prevent confirmation until reconciled.
- Demonstrated planning defect corrected: direct dependencies on non-boundary tasks failed SUBPLAN_EDGE. New work follows declared implementation/publication boundaries and cumulative CG-2/CG-3 without changing SP-1, SP-2 or CG-1.
- Demonstrated planning defect corrected: ten-task SP-4 needed an early checkpoint. T4.31 executes the real HTTP/database harness authored by T4.3 before UI work; downstream tasks follow it.
- Plausible risk addressed: shallow legacy validation silently drops invalid data (guardado-escena.ts). T4.2 owns full runtime validation; T4.5 preserves raw source before normalization and deduplicates transactionally on account/source hash.
- Plausible risk addressed: saved work could be lost through concurrent updates or account deletion. T4.2 owns conditional revision updates, mutation receipts, FK restriction and owner-row locking; T4.31 exercises races before UI consumption.
- Plausible risk addressed: global browser scene leaks across account switches. T4.4 owns account/project namespaces, cache reset, response-generation guards and explicit legacy import consent; T4.6 drives separate browser contexts.
- Plausible risk addressed: adding Backing to semantic GrupoCatalogo can break repository/RAG/photo consumers. T3.3 uses presentation grouping with the original seven IDs and repository assignments retained.
- Plausible risk addressed: GLB structure tests do not prove Blender import. T3.5/T3.6 require actual downloaded-scene import evidence or an explicit block; owner manual Blender check stays separate in SPEC Pruebas. Acquisition is not authorized yet.
- Plausible risk addressed: proyectos.ver_todos alone must not grant Taller editing. T4.3 resource authorization and T4.4 read-only /proyectos/[id] cover a custom staff role without taller.usar.
- WBS responsibility: implementation tasks author checks/harnesses; T3.6/T4.31/T4.7/T92/T93 execute them, and visual/spec/standards audits are separate. High complexity retained for persistence/restoration, concurrency, import and real Blender harness boundaries; estimates are explicitly uncalibrated.
- Verification: plan-json check exits 2 with 66 errors confined to unfinished SP-5..SP-13 and their milestones/requirements. No errors in SP-1..SP-4 or composition gates. Full plan is not publishable. Remaining warnings include future test evidence and package script coordination; no product tests were run from HQ.
- Preservation: SP-1/SP-2 subplan data and tasks, plus T91, compare equal to HEAD; live focus remains SP-2 with 1/13 confirmed. No confirmation, launch, installation or project-source modification occurred.
