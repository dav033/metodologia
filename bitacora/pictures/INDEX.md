# Index — pictures

_Generated 2026-10-18 11:08 by `bitacora.py index`. Do not edit by hand._

**Central:** [Summary](SUMMARY.md) · [Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · [Pending](PENDING.md) · [Tools](TOOLS.md)  
**Web:** [project](http://127.0.0.1:8765/p/pictures) · [graph](http://127.0.0.1:8765/p/pictures/graph)  
**Last activity:** 2026-10-18

## Workspace

- **demo-decoracion** → `/home/david/dev/pictures-wt/t7/C:/Users/davidt/Downloads/pictures-workspace/demo-decoracion` (not cloned here)
- **t7** → `/home/david/dev/pictures-wt/t7` (not cloned here)
- **audit** → `/home/david/dev/pictures-wt/audit` (not cloned here)
- **t12** → `/home/david/dev/pictures-wt/t12`
- **pictures** → `/home/david/dev/pictures`

## Needs attention

- REQ-015: executor finished — review & merge
- REQ-016: executor finished — review & merge
- REQ-017: question round waiting for answers
- REQ-017: executor finished — review & merge
- REQ-018: question round waiting for answers

## Requirements

| ID | Title | Spec | Plan | |
|---|---|---|---|---|
| [REQ-001](requirements/REQ-001-photo-to-scene/SPEC.md) | Photo to scene (Pinterest → 3D) + flexible organic structures | `approved` | [?](requirements/REQ-001-photo-to-scene/PLAN.md) |  |
| [REQ-002](requirements/REQ-002-workshop-library-rag/SPEC.md) | RAG for the 3D workshop library (decorations, structures, templates) | `draft` | [?](requirements/REQ-002-workshop-library-rag/PLAN.md) |  |
| [REQ-003](requirements/REQ-003-scene-agent-v2/SPEC.md) | Scene agent v2 (sees inside pieces, targets by format/size/part, many more tools) | `in` | — |  |
| [REQ-004](requirements/REQ-004-users-and-spend-control/SPEC.md) | Users and AI spend tracking (Gemini + fal.ai) | `planned` | [?](requirements/REQ-004-users-and-spend-control/PLAN.md) |  |
| [REQ-005](requirements/REQ-005-decorations-from-scratch/SPEC.md) | Decorations from scratch (compose anything) + photo → model → library | `clarifying` | — |  |
| [REQ-006](requirements/REQ-006-venue-photo-to-3d/SPEC.md) | Venue photo → 3D space | `clarifying` | — |  |
| [REQ-007](requirements/REQ-007-engine-behind-the-customer-journey-2d-vi/SPEC.md) | The globos3d engine behind the customer journey (2D views, basic edits, two products) | `done 2026-10-11 (phases 0-6 merged, D-039 production default)` | [draft v2 — rewritten after the antagonistic architecture panel (3 reviewers: boundaries, contracts/truth,](requirements/REQ-007-engine-behind-the-customer-journey-2d-vi/PLAN.md) |  |
| [REQ-008](requirements/REQ-008-complex-event-compositions-wedding-hall/SPEC.md) | Complex event compositions ("I want a wedding") | `done 2026-10-11 (merged, 4ff9bdd4)` | [in progress 2026-10-09 — owner asked to build it now ("Gemini only put a table and a chair on the existing](requirements/REQ-008-complex-event-compositions-wedding-hall/PLAN.md) |  |
| [REQ-009](requirements/REQ-009-voice-input-whisper/SPEC.md) | Voice input everywhere there is free text (Whisper) | `done 2026-10-11 (merged fb8477b6; VOZ_* flags unconfirmed)` | — |  |
| [REQ-010](requirements/REQ-010-ai-feedback/SPEC.md) | AI feedback: rate every AI action and keep its full state | `done 2026-10-11 (merged 3a8f56e2; migration 030 status unconfirmed)` | — |  |
| [REQ-011](requirements/REQ-011-module-studio-with-cached-ai-renders/SPEC.md) | Module studio with cached AI renders | `done 2026-10-11 (merged 03049ca7)` | — |  |
| [REQ-012](requirements/REQ-012-furniture-freedom-tables-and-chairs-deco/SPEC.md) | Furniture freedom: tables and chairs decoupled | `merged to main 2026-10-10 (78638080, 386b0cdc)` | — |  |
| [REQ-013](requirements/REQ-013-catalogue-repositories/SPEC.md) | Catalogue repositories (ADR) | `done 2026-10-11 (phases 1-5 merged, migration 034)` | [in-progress (phases 1-5 built, 6-7 pending)](requirements/REQ-013-catalogue-repositories/PLAN.md) |  |
| [REQ-014](requirements/REQ-014-72h-marathon-autonomous-product-developm/SPEC.md) | 72h marathon — autonomous product development | `in-progress` | [in-progress](requirements/REQ-014-72h-marathon-autonomous-product-developm/PLAN.md) |  |
| [REQ-015](requirements/REQ-015-judge-fix-guided-chat-honesty-and-count/SPEC.md) | judge-fix: guided chat honesty and count/price parity (D1-D5, D8) | `done (local branch awaiting owner review)` | [done](requirements/REQ-015-judge-fix-guided-chat-honesty-and-count/PLAN.md) | report ✓ |
| [REQ-016](requirements/REQ-016-guided-3d-edit-leftovers-exact-undo-and/SPEC.md) | Guided 3D edit leftovers: exact undo and colour resolver (P-042, P-058) | `ready` | [done](requirements/REQ-016-guided-3d-edit-leftovers-exact-undo-and/PLAN.md) | report ✓ |
| [REQ-017](requirements/REQ-017-activity-aware-guided-chat-decoration-re/SPEC.md) | Activity-aware guided-chat decoration recommendations | `in-progress` | [done](requirements/REQ-017-activity-aware-guided-chat-decoration-re/PLAN.md) | report ✓ · round open |
| [REQ-018](requirements/REQ-018-category-based-recommendations-of-assemb/SPEC.md) | Category-based recommendations of assembled decorations | `clarifying` | — | round open |

## Top pending (urgency, then complexity)

- P-010 · Commit photo-reading work (uncommitted) and merge e3-rapido f1198efd (precise AI size edit · high/M
- P-015 · REQ-002 remaining rollout verification: current read-only Neon audit proves 028 tables and · high/M
- P-021 · Refine acceptance feat/refinar-aceptacion (e4m) — approved, base of integ/foto-taller (was · high/M
- P-110 · `main` red after push 6649f75 (payload: shared Taller quotes, 3D sign compositing, Kontext · high/M
- P-062 · After the prod fixes: /api/generate legacy product ids (productosPorIdConFuente) still rea · med/S
- P-086 · `tamano_pieza` shrink (-1) enlarges a piece whose start size is below the constructor mini · med/S
- P-002 · FLUX photo color fidelity: residual ΔE ~15 after hex prompt (c25490f1); next: photoreal ca · med/M

## Recent decisions

- D-058 — The guiada_motor cookie does not beat the 3D cut unless explicitly allowed
- D-057 — Do not persist workshop stock yet; leftoverInventory stays quote output
- D-056 — Remove the separate feedback administrator password; the app session is the admin gate
- D-055 — Limit REQ-014 synchronization to the approved Ship #1 payload
- D-054 — Preserve the existing Happie v1 contract while adding opt-in services

## Timeline

- **2026-10** — [month summary](2026-10/MONTH.md)
  - [W3](2026-10/W3/WEEK.md): [18](2026-10/W3/2026-10-18.md), [16](2026-10/W3/2026-10-16.md), [15](2026-10/W3/2026-10-15.md), [14](2026-10/W3/2026-10-14.md), [13](2026-10/W3/2026-10-13.md)
  - [W2](2026-10/W2/WEEK.md): [11](2026-10/W2/2026-10-11.md), [10](2026-10/W2/2026-10-10.md), [09](2026-10/W2/2026-10-09.md), [08](2026-10/W2/2026-10-08.md)
