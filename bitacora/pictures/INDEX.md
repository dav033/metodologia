# Index — pictures

_Generated 2026-10-14 14:18 by `bitacora.py index`. Do not edit by hand._

**Central:** [Summary](SUMMARY.md) · [Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · [Pending](PENDING.md) · [Tools](TOOLS.md)  
**Web:** [project](http://127.0.0.1:8765/p/pictures) · [graph](http://127.0.0.1:8765/p/pictures/graph)  
**Last activity:** 2026-10-14

## Workspace

- **demo-decoracion** → `/home/david/dev/pictures-wt/t7/C:/Users/davidt/Downloads/pictures-workspace/demo-decoracion` (not cloned here)
- **t7** → `/home/david/dev/pictures-wt/t7` (not cloned here)
- **audit** → `/home/david/dev/pictures-wt/audit` (not cloned here)
- **t12** → `/home/david/dev/pictures-wt/t12`
- **ops-matrix-jxjn7vd9** → `/tmp/ops-matrix-jxjn7vd9`
- **pictures** → `/home/david/dev/pictures`

## Needs attention

- REQ-014: plan waiting for approval
- REQ-015: executor finished — review & merge
- REQ-016: executor finished — review & merge

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
| [REQ-014](requirements/REQ-014-72h-marathon-autonomous-product-developm/SPEC.md) | 72h marathon — autonomous product development | `stopped 2026-10-11 06:14 at cycle 26 (planned end 2026-10-12 16:44); not resumed` | [review](requirements/REQ-014-72h-marathon-autonomous-product-developm/PLAN.md) |  |
| [REQ-015](requirements/REQ-015-judge-fix-guided-chat-honesty-and-count/SPEC.md) | judge-fix: guided chat honesty and count/price parity (D1-D5, D8) | `done (local branch awaiting owner review)` | [done](requirements/REQ-015-judge-fix-guided-chat-honesty-and-count/PLAN.md) | report ✓ |
| [REQ-016](requirements/REQ-016-guided-3d-edit-leftovers-exact-undo-and/SPEC.md) | Guided 3D edit leftovers: exact undo and colour resolver (P-042, P-058) | `ready` | [done](requirements/REQ-016-guided-3d-edit-leftovers-exact-undo-and/PLAN.md) | report ✓ |

## Top pending (urgency, then complexity)

- P-010 · Commit photo-reading work (uncommitted) and merge e3-rapido f1198efd (precise AI size edit · high/M
- P-015 · REQ-002 remaining rollout verification: current read-only Neon audit proves 028 tables and · high/M
- P-021 · Refine acceptance feat/refinar-aceptacion (e4m) — approved, base of integ/foto-taller (was · high/M
- P-062 · After the prod fixes: /api/generate legacy product ids (productosPorIdConFuente) still rea · med/S
- P-086 · `tamano_pieza` shrink (-1) enlarges a piece whose start size is below the constructor mini · med/S
- P-002 · FLUX photo color fidelity: residual ΔE ~15 after hex prompt (c25490f1); next: photoreal ca · med/M
- P-007 · Split Taller3D.tsx (1022 lines) by responsibility: top bar, rail panels, viewer overlay, i · med/M

## Recent decisions

- D-048 — 2026-10-13 · REQ-016 M2: retain requested untouched colour resolutions in versioned signed history
- D-047 — 2026-10-13 · REQ-016 T3 (P-058 A2–A4): sumar una idea conserva el origen; «rosa → rosado» con el rosado ya puesto no pregunta; `origen.tipo` se declara como `resolutor`
- D-046 — 2026-10-13 · REQ-016 T2 design: signed last-colour-order context replaces the origin heuristic for known history
- D-045 — 2026-10-13 · REQ-016 T1 (P-042): «Deshacer» a guided 3D adjustment restores the stored previous widget (signed plan + quote), in memory only; never an inverse edit
- D-044 — 2026-10-13 · REQ-015 audit P1-2: the rule path accionIdea:costear is bounded by a durable global hourly cap in Neon (topeDurable key costeo_idea_hora, no migration), checked before costearIdeaElegida; denied → rule answer (SSE 200, no model), store down → in-memory cap with the same N, never unlimited. Chosen by debate (A in-memory, B durable cap, C memo/dedupe; judge haiku-max: B). N default is a conservative guess, to be calibrated from COTIZACION_IDEA_* counts.

## Timeline

- **2026-10** — [month summary](2026-10/MONTH.md)
  - [W3](2026-10/W3/WEEK.md): [14](2026-10/W3/2026-10-14.md), [13](2026-10/W3/2026-10-13.md)
  - [W2](2026-10/W2/WEEK.md): [11](2026-10/W2/2026-10-11.md), [10](2026-10/W2/2026-10-10.md), [09](2026-10/W2/2026-10-09.md), [08](2026-10/W2/2026-10-08.md)
