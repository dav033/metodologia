# pictures — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex balloon-decoration demo (`demo-decoracion`, Next 16 on Vercel + Python `plan.py` on a VPS). The active
product is the **3D workshop** at `/3d`: a parametric three.js editor (balloon → module → structure → hanging
decorations) whose shopping list comes from the leaves, plus a FLUX photo render of the 3D view and a Gemini Flash
agent that builds and edits scenes with tools. Users: Sempertex staff and decorators.

## Current state (main = `7e86acad`, 2026-10-09)
- **Library RAG LIVE** (REQ-002): Neon indexed (3 217 items, 12 567 parts, 6 447 vectors), `TALLER_RAG_ENABLED` on in
  Vercel; RAG beats in-memory on the gold set (acierto@5 97.5 % vs 87.5 %). Orphan table `taller_taxonomia` (P-030).
- **Taller AI panel B LIVE** (D-021): per-turn change cards, undo only AI-touched pieces, NDJSON steps + stop, phone
  sheet. Its first deploy broke the prod build (Date.now in prerender) → hotfix 7245991f, prod Ready (P-033 guard).
- **Photo → scene** (REQ-001): tilted camera, cluster review, proportion passes, colour-by-stretch — on main.
- **Voice (REQ-009):** Whisper service LIVE on the VPS (/opt/voz-decoracion); app button + /api/voz/transcribir done
  on e4y `fb8477b6`, hostile review running; then Vercel env (VOZ_URL/VOZ_SECRETO/VOZ_ENABLED off) + push.
- **REQ-008 complete events** (e4v, main merged at 4ff9bdd4): re-review BLOCKING (starter discard, variante once,
  foil letters overlap, ceiling clearance) + 2 post-merge test failures → back with the fix agent.
- **REQ-010 AI feedback** backend in e4z (dedicated Garage, migration 030 not applied, admin + analysis); S3 client
  being made shared (`src/lib/almacen/objetos-s3.ts`).
- **REQ-011 module studio** (new): dúo…sexteto, colours/finishes, clean studio 3D, FLUX render cached by canonical
  key (migration 031) — implementer in e5m feat/estudio-modulos.

## Active focus
- Review → push: voice (e4y), events (e4v). Then REQ-010 backend + migration, REQ-011 studio.

## Top pending (see PENDING.md)
- P-022 owner A/B labelling for refine · P-027 burgundy chrome · P-029 CI health · P-030 orphan taxonomy table ·
  REQ-005 / REQ-006 (room scan: import RoomPlan USDZ suggested by the market study).

## Recent decisions (see DECISIONS.md)
- D-019/D-020: 3D engine canonical via (b); two products; customer edits = AI requests + colour refs/proportions +
  size proportions. D-021: Taller AI direction B. Market study artifact 5i7KgEc4b9J5aSCmLnfqTb.

## Known issues
- Default workshop scene + CRUD rule made every new decoration the same arch+columns+garland (fix in progress).
- Burgundy chrome renders red (no wine Reflex in the table); photo metric biased by sparse small-balloon detections.

_Last updated: 2026-10-09_
