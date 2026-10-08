# pictures — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex balloon-decoration demo (`demo-decoracion`, Next 16 on Vercel + Python `plan.py` on a VPS). The active
product is the **3D workshop** at `/3d`: a parametric three.js editor (balloon → module → structure → hanging
decorations) whose shopping list comes from the leaves, plus a FLUX photo render of the 3D view and a Gemini Flash
agent that builds and edits scenes with tools. Users: Sempertex staff and decorators.

## Current state (main = `bfe3447f`, 2026-10-08)
- Library: 26 lots of Sempertex ideas (~423/987), 20 organic web bases, **13 owner Pinterest references** (read by hand
  in the photo-reading format, compiled to scenes), predefined decorations, utilería, backdrops & furniture.
- New structures/decorations: free organic stroke garland (any silhouette, editable by its `generador`), four column
  types (classic / organic XV / irregular / freeform), foliage (monstera, palm, fern, eucalyptus, pampas), grape
  clusters / R-5 ball / collar, orb with fringe, backdrop catalog; decorator colour names (navy, emerald, blush…).
- Editor: redesign live; drag & drop from the whole sidebar; chrome balloons render in colour; AI photos persist.
- FLUX: closed inventory, official hex, silhouettes of any organic piece + empty-wall gaps (no more closed frames).
- AI: `ajustar_tamanos` (precise size mix); **parts contract** — every balloon can carry `parte`, selector/inventory
  in `partes-globos.ts`.

## Active focus
- **REQ-003 scene agent v2** — 5 agents running in worktrees (see today's log «Handoff»).
- **REQ-002 library RAG + celebrations taxonomy** — planned (SPEC + PLAN), starts after REQ-003.
- REQ-001 photo → scene: steps 7–10 (Gemini vision reading → compiler, upload in AI bar, refinement, paid eval) pending.

## Top pending (see PENDING.md)
- REQ-003, REQ-002, REQ-001 · P-012 occasion ids · P-002 FLUX colour/exactness · P-008 split organico.ts/escena.ts.

## Recent decisions (see DECISIONS.md)
- D-007 organic pieces keep a `generador` · D-008 photo → scene = structured reading + deterministic compiler.
- Owner: stay on Gemini Flash; "more tools, rules, semantics"; everything made of identifiable balloon types/products.
- RAG split: Python = batch (embeddings text+image, analysis, rerank); Next = online query to Neon; code = source.

## Known issues
- FLUX.2 still redraws (not pixel-exact); colour drift ΔE ~15.
- «Más tupida» barely changes stroke garlands (P-011).

_Last updated: 2026-10-08_
