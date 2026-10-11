# Index — pictures

_Generated 2026-10-11 03:46 by `bitacora.py index`. Do not edit by hand._

**Central:** [Summary](SUMMARY.md) · [Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · [Pending](PENDING.md) · [Tools](TOOLS.md)  
**Web:** [project](http://127.0.0.1:8765/p/pictures) · [graph](http://127.0.0.1:8765/p/pictures/graph)  
**Last activity:** 2026-10-11

## Workspace

- **demo-decoracion** → `C:/Users/davidt/Downloads/pictures-workspace/demo-decoracion`

## Needs attention

- REQ-014: plan waiting for approval

## Requirements

| ID | Title | Spec | Plan | |
|---|---|---|---|---|
| [REQ-001](requirements/REQ-001-photo-to-scene/SPEC.md) | Photo to scene (Pinterest → 3D) + flexible organic structures | `approved` | [?](requirements/REQ-001-photo-to-scene/PLAN.md) |  |
| [REQ-002](requirements/REQ-002-workshop-library-rag/SPEC.md) | RAG for the 3D workshop library (decorations, structures, templates) | `draft` | [?](requirements/REQ-002-workshop-library-rag/PLAN.md) |  |
| [REQ-003](requirements/REQ-003-scene-agent-v2/SPEC.md) | Scene agent v2 (sees inside pieces, targets by format/size/part, many more tools) | `in` | — |  |
| [REQ-004](requirements/REQ-004-users-and-spend-control/SPEC.md) | Users and AI spend tracking (Gemini + fal.ai) | `planned` | [?](requirements/REQ-004-users-and-spend-control/PLAN.md) |  |
| [REQ-005](requirements/REQ-005-decorations-from-scratch/SPEC.md) | Decorations from scratch (compose anything) + photo → model → library | `clarifying` | — |  |
| [REQ-006](requirements/REQ-006-venue-photo-to-3d/SPEC.md) | Venue photo → 3D space | `clarifying` | — |  |
| [REQ-007](requirements/REQ-007-engine-behind-the-customer-journey-2d-vi/SPEC.md) | The globos3d engine behind the customer journey (2D views, basic edits, two products) | `draft (awaiting antagonistic architecture review + owner approval)` | [draft v2 — rewritten after the antagonistic architecture panel (3 reviewers: boundaries, contracts/truth,](requirements/REQ-007-engine-behind-the-customer-journey-2d-vi/PLAN.md) |  |
| [REQ-008](requirements/REQ-008-complex-event-compositions-wedding-hall/SPEC.md) | Complex event compositions ("I want a wedding") | `clarifying (after REQ-007 D1 and the furniture branch merge)` | [in progress 2026-10-09 — owner asked to build it now ("Gemini only put a table and a chair on the existing](requirements/REQ-008-complex-event-compositions-wedding-hall/PLAN.md) |  |
| [REQ-009](requirements/REQ-009-voice-input-whisper/SPEC.md) | Voice input everywhere there is free text (Whisper) | `in progress 2026-10-09` | — |  |
| [REQ-010](requirements/REQ-010-ai-feedback/SPEC.md) | AI feedback: rate every AI action and keep its full state | `in progress 2026-10-09` | — |  |
| [REQ-011](requirements/REQ-011-module-studio-with-cached-ai-renders/SPEC.md) | Module studio with cached AI renders | `in-progress` | — |  |
| [REQ-012](requirements/REQ-012-furniture-freedom-tables-and-chairs-deco/SPEC.md) | Furniture freedom: tables and chairs decoupled | `in-progress` | — |  |
| [REQ-013](requirements/REQ-013-catalogue-repositories/SPEC.md) | Catalogue repositories (ADR) | `ready` | [planned](requirements/REQ-013-catalogue-repositories/PLAN.md) |  |
| [REQ-014](requirements/REQ-014-72h-marathon-autonomous-product-developm/SPEC.md) | 72h marathon — autonomous product development | `ready` | [review](requirements/REQ-014-72h-marathon-autonomous-product-developm/PLAN.md) |  |

## Top pending (urgency, then complexity)

- P-066 · Verify on prod that the Taller «Precio en la tienda» equals the /asistente card and plan p · high/S
- P-045 · GUIADA_MOTOR rollback is not graceful: after flipping back to python, open 3D conversation · high/M
- P-010 · Commit photo-reading work (uncommitted) and merge e3-rapido f1198efd (precise AI size edit · high/?
- P-015 · REQ-002 go-live checklist: apply migrations 028 + 029 on Neon (with notice), run indexer - · high/?
- P-018 · Photo fidelity (lote-02 photo 01, then 02–05): branch feat/foto-fidelidad (e4n) — implemen · high/?
- P-021 · Refine acceptance feat/refinar-aceptacion (e4m) — approved, base of integ/foto-taller (was · high/?
- P-031 · Taller AI-UX redesign — owner picked B (D-021), IN PROGRESS e4x feat/ia-panel — was: owner · high/?

## Recent decisions

- D-039 — Beta: production is the same for everyone, everything on everywhere (owner) · 2026-10-10
- D-038 — One quote everywhere — pick the best model (owner) · 2026-10-10
- D-037 — Owner: not real production — VPS deploy approved, go hard (owner) · 2026-10-10
- D-036 — Review stop-rule and model start for M tasks (marathon, taken alone) · 2026-10-10
- D-035 — Persisted guided-plan fields: the reader ships one deploy before the writer (marathon, taken alone) · 2026-10-10

## Timeline

- **2026-10** — [month summary](2026-10/MONTH.md)
  - [W2](2026-10/W2/WEEK.md): [11](2026-10/W2/2026-10-11.md), [10](2026-10/W2/2026-10-10.md), [09](2026-10/W2/2026-10-09.md), [08](2026-10/W2/2026-10-08.md)
