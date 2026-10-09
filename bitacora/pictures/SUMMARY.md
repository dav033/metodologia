# pictures — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex balloon-decoration demo (`demo-decoracion`, Next 16 on Vercel + Python `plan.py` on a VPS). The active
product is the **3D workshop** at `/3d`: a parametric three.js editor (balloon → module → structure → hanging
decorations) whose shopping list comes from the leaves, plus a FLUX photo render of the 3D view and a Gemini Flash
agent that builds and edits scenes with tools. Users: Sempertex staff and decorators.

## Current state (main = `3bb9b5fc`, 2026-10-09)
- **Library RAG LIVE** (REQ-002): Neon indexed (3 217 items, 12 567 parts, 6 447 vectors), `TALLER_RAG_ENABLED` on in
  Vercel; on the gold set RAG beats in-memory (acierto@5 97.5 % vs 87.5 %, nDCG@10 0.687 vs 0.564). Found and fixed:
  no vector uploader existed; TS/Python text-hash mismatch. Orphan table `taller_taxonomia` (P-030).
- **Photo → scene** (REQ-001, main a0fad72a + integ): tilted photo camera, cluster-box review (Gemini counts balloons
  in oversized boxes), same-colour giants, clear acrylic, fragment boxes, signs in front of balloons, pedestal
  counting; proportion metric + rounds 1–2 on integ/foto-taller (not yet on main: last review fix in progress).
- **Furniture** (39 items + agregar_mobiliario), cursive signs, pampas, studio materials — on main.
- **In parallel branches (not merged):** REQ-008 complete events (e4v: halls to 30×30×10 m, armar_salon/ajustar/
  mover/quitar zona, planificar_evento with alcance solo_decoracion|rincon|salon, venue registry; merged with e4w
  centrepieces decorar_mesas… + techo_por_zona + golden snapshot test; + empty starting scene and varied
  decorations by theme in progress); Taller AI panel B (e4x, D-021: per-turn change cards, undo only AI-touched
  pieces, NDJSON steps + stop, phone sheet; review fixes in progress).
- VPS advin-vps: APP_ORIGINS set (P-024 done); Whisper + Laya benchmark being set up in an isolated compose project.

## Active focus
- REQ-008 merge + variety → hostile review → push. Panel B review fixes → push. Photo zone fix → verify → push.
- Whisper/Laya benchmark → decide integration.

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
