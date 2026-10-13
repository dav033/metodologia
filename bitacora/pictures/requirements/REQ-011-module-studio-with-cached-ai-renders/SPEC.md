---
id: REQ-011
status: done 2026-10-11 (merged 03049ca7)
created: 2026-10-09
track: standard
---
# REQ-011 — Module studio with cached AI renders

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Owner (2026-10-09): «tenemos de dúo a sexteto… una herramienta que sea solo estas estructuras, que se puedan
modificar los colores y generar renders con IA; p. ej. "quiero un dúo de reflex rojo con azul mate" → lo pone y me
da la opción de generar con IA el render; presentado bonitamente sin ruido alrededor; se guarda en base de datos la
imagen con el tipo de estructura (dúo, trío, cuarteto…) para que cuando un usuario pida una petición igual se
devuelva esa imagen y no se genere de nuevo».

Modules (pareja/dúo, trío, cuarteto, quinteto, sexteto) are the atoms of every decoration; a clean, reusable,
photo-real image of each colour combination is sales material and avoids paying FLUX twice for the same request.

**Success looks like:** typing or picking "dúo reflex rojo + azul mate" shows the 3D module on a clean studio
backdrop in < 2 s; "Generar render con IA" produces a photo-real image once; the identical request (same module,
size, colours, finishes — in any equivalent order) returns the stored image instantly with zero AI cost.

## Users / actors / stakeholders
- Staff / owner (Taller pro) — primary user of the studio page.
- Customer chat (later) — reads the cache: an identical request returns the stored image.

## Scope (in)
### US-1 (P1, Must) — Configure a module
As staff, I pick module type (dúo…sexteto), balloon size, and per-balloon colour + finish (mate/fashion, reflex/
cromado, perlado, cristal…) from the real Sempertex catalogue, and see it in 3D on a clean backdrop.
### US-2 (P1, Must) — Natural-language request
"un dúo de reflex rojo con azul mate" (text or voice when REQ-009 lands) is parsed (Gemini Flash, audited) into the
same configuration; unknown colours/finishes are reported, never invented.
### US-3 (P1, Must) — AI render with cache
"Generar render con IA" → cache lookup by canonical key → hit: return stored image (no cost); miss: FLUX (fal.ai,
the existing render pipeline, 3D capture as guide) → store image + metadata → return.
### US-4 (P2, Should) — Gallery
Browse stored renders filtered by module type / colours; reuse from the customer chat by the same key.

## Out of scope
- Structures beyond modules (arcs, columns, walls) — they use the Taller.
- Customer-triggered generation (customers only read the cache for now; owner rule: limit customer AI later).
- Gemini generating images (forbidden; FLUX base only, no LoRA).

## Requirements
- R1. The studio shall offer exactly the five module types from `modulos.ts` (pareja shown as "Dúo").
- R2. Colours and finishes shall come from the catalogue the engine already uses; free text maps to catalogue codes.
- R3. The cache key shall be canonical: module type + size + the per-balloon (colour, finish) arrangement reduced
  over the module's symmetries (rotation/reflection) + render pipeline version. "rojo+azul" = "azul+rojo" for a dúo.
- R4. When the key exists, the system shall return the stored image without calling any paid API.
- R5. When the key is missing and the user asks for a render, the system shall generate once, store it (object
  storage + Neon row) and log the paid call through the existing audit (`registrarGemini`/render audit).
- R6. Two simultaneous requests for the same missing key shall produce one generation (row lock / unique key).
- R7. The 3D presentation shall show only the module: neutral seamless backdrop, soft shadow, centred, no room.
- R8. If generation fails or the per-hour cap is reached, the system shall say so and store nothing.

## Edge cases & errors
- Colour not in catalogue ("rojo vino tinto") → nearest catalogue colour with a visible note, or ask.
- Fewer colours than balloons ("dúo rojo") → all balloons that colour; more colours than balloons → error message.
- Pipeline/prompt change → bump pipeline version in the key so stale renders are not served.
- Storage up but Neon down (or vice versa) → no half-written cache entry is served.

## Constraints
- Next 16 on Vercel; three.js; FLUX via fal.ai (paid, every test run declares its cap); Gemini Flash only for parsing.
- Storage: the dedicated Garage on the VPS via the shared S3 module being built in REQ-010 (`src/lib/almacen/`),
  never the Maros Construction storage. Neon for metadata (new migration, applied with notice).
- TypeScript without `any`; no `next build` locally; files < 500 lines.

## Priorities & phases
MVP: US-1 + US-3 (page, config, 3D, render + cache). Then US-2 (text/voice), then US-4 (gallery + chat reuse).

## Timeline & dependencies
- Depends on REQ-010's shared S3 module + Garage bucket (in progress). Until then: storage port + in-memory adapter.

## Assumptions
- A1. Lives as its own page in the pro tool (`/3d/modulos` or similar) reusing the Taller's 3D engine — owner said
  "una herramienta que sea solo estas estructuras". Revisit if owner wants it inside the Taller panel.
- A2. Default size R-12 (11"); size is part of the key.
- A3. Arrangement order matters only up to the module's symmetry (owner can say otherwise).

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Partial |
| Flows & behavior | Clear |
| Edge cases | Partial |
| Acceptance criteria | Partial |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Partial |

## Clarifications
### Round 1 — 2026-10-09
- Owner request taken as-is; open points recorded as assumptions A1–A3 (owner asked for autonomy).
