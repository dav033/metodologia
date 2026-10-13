---
id: REQ-007
status: done 2026-10-11 (phases 0-6 merged, D-039 production default)
created: 2026-10-08
track: standard — CRITICAL
---
# REQ-007 — The globos3d engine behind the customer journey (2D views, basic edits, two products)

## Problem & goal
Owner (2026-10-08): "integrate this engine into the customer journey, but capped: the user will not see it; behind the
scenes it uses the engine for everything; you show 2D representations of what you build; the user can only make basic
manual edits (colours, structure type, etc.). Plan this well, it is critical. These are two separate products — be very
careful." Plus: "be completely serious with the architecture"; "antagonistic agents everywhere"; and the historic defect
to kill: **properties that are read/requested, then lost along the chain and regenerated from defaults** (orphan
properties).

**Success looks like:** every customer decoration (guided `/asistente` and classic `/`) is built by the same globos3d
engine the workshop uses; the customer sees 2D views (and the FLUX photo) of exactly what the engine built; basic edits
re-run the engine; quotes/materials come from one source of truth; the workshop can evolve without breaking the
customer product; no field the customer (or a photo) gave is silently dropped.

## Current state (explorers, 2026-10-08)
- Customer: `/asistente` (VistaGuiada → `/api/asistente-guiado`, Omoikane agent tools) and `/` (classic chat →
  `/api/chat`), both converge on `/api/generate` (Python `plan.py` resolve → `armado_*.py` recipes → `guia_escena.py`
  2D disc guide → FLUX via fal.ai). Plan contract `PlanGuiadoSchema` (piezas, armados, cantidades, plan_hash,
  approval_token). Customer edits today: colours (COLORES_PROPUESTA_V2), structure type (ESTRUCTURAS_OFICIALES), quantity
  1–12, reference photos.
- globos3d (~170 TS files) is used ONLY by the workshop (`/3d`, `/api/escena-ia`, `/api/render-3d-imagen`); not imported by
  `components/guiado`. Python owns customer geometry and quantities (memory: «plan.py es el único dueño de cantidades»).
- Shared and unversioned: `src/lib/plan/*` (tipos, estructuras-oficiales, cotizacion/motor, armado-*), Python internal
  endpoints, feature flags (no per-product override), `ai_call_log` (no product tag), one `vercel-build`.
- Existing 2D: SVG disc guides (`guia-estructura.ts`, `guia-escena.ts`) rasterised with sharp (`rasterizar-guia.ts`),
  fed to FLUX `/edit` as `structure_guide`/`scene_guide`. No GPU anywhere server-side.

## Scope (in)
- US-1 Engine as a versioned product boundary: a workspace package (`packages/motor-globos`, pure TS: no React, no
  three, no network) with a small public API (`v1`): build a scene, bill of materials, 2D views, basic edits. The
  workshop may use internals; the customer product may import ONLY the public entry (enforced by lint/CI).
- US-2 Plan → scene adapter: the customer plan (or what the customer agent proposes) becomes an engine `Escena`
  deterministically; every plan field is consumed (sensitivity contract tests: changing any field changes the scene or
  is explicitly declared non-visual).
- US-3 2D representations for the customer: pure-TS SVG projection of the built scene (front view, depth-sorted shaded
  discs with real Sempertex colours, legend/BOM), served as SVG to the client and as PNG (sharp) to FLUX as the guide.
- US-4 Basic edits (colour per piece/part, structure type, size, remove/add piece from an allowed list) → edit the plan →
  re-run the engine → new 2D views + quote. No free 3D manipulation.
- US-5 One source of truth for quantities/quote (see Q1), with a shadow period that logs engine-vs-Python differences.
- US-6 Product separation: route groups, per-product feature flags, `producto` tag on telemetry/spend, no shared client
  state, contract versioning between products and with Python.
- US-7 Rollout: shadow → flag per step → default; instant rollback by flag.

## Out of scope (for now)
Customer-visible 3D; workshop UI changes; REQ-004 auth (but the design must not block it).

## Open questions (round 1 — owner)
1. **Source of truth for quantities & quote**: engine BOM (the engine places every balloon, so it can count them) vs
   Python `plan.py` (today's owner). Rec: engine becomes the owner for structures it builds, Python keeps pricing and
   stock; shadow-compare first.
2. **2D style for customers**: technical (flat discs + legend with codes and counts), illustrative (shaded, room
   context), or both (illustrative view + technical sheet). Rec: both.
3. **Basic edits list**: colours (per piece and per part), structure type, size (width/height), remove piece, add from a
   short list — anything else? (sizes/format mix, density?)
4. **Separation depth**: one app with strict route groups + import boundaries (rec), or two Vercel projects/domains?
