# pictures — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex balloon-decoration demo (`demo-decoracion`: Next 16 on Vercel + Python ai-api on a VPS). Two products on one
engine: the **Taller 3D** (`/3d`, pro tool with a scene AI agent) and the **guided customer chat** (`/asistente`,
quotes priced by Python; the 3D engine sits behind `GUIADA_MOTOR=python`).

## Current state (main = `65edd83b`, VPS = 65edd83b, 2026-10-11 06:14; prod smoke 13/0/3)
- **One quote everywhere (D-038) live:** same plan = same price on every surface; per-balloon spares with a cost cap;
  Python = engine (42-BOM shared fixture in CI). Every guided idea (engine and curated) is priced by the single pricer;
  prod e2e «paridad de precio» checks assistant = Taller on every release.
- **Beta, everything on for everyone (D-039):** guided chat runs the 3D engine for all customers, Taller build sheet on,
  solo-guiada mode removed, catalogue repositories on; VPS deploys follow every green main (D-037). Only the AI-feedback
  admin panel stays closed (third-party data).
- **Owner photo case (quinceañera backdrop) fixed (59a06582 + 9f86d67b):** the backdrop is the subject (no guest table),
  scale and floor come from the installation, the garland spans the real balloons with the photo's colour shares, a
  second glitter wall, plum chrome → Reflex. Left in P-068 (doors, pink roses, low camera).
- **Spend caps are global (392fff68):** paid-call hourly caps count in Neon `topes_gasto` (migration 035), not per Vercel instance.
- **Ship gate:** `npm run gate` locally + `escena:test` (405-scene golden, honesty, photo suites) in CI; free prod pulse `npm run prod:pulso`; rollback drill on prod 2026-10-11 all PASS (research/ciclo/SIMULACRO-ROLLBACK-2026-10-11.md).
- **72 h marathon STOPPED** at cycle 26 (2026-10-11 06:14; planned end 2026-10-12 16:44). Its state is in `research/ciclo/STATE.md`.
  From 2026-10-13 development runs entirely from this laptop (owner decision, D-041); origin/main is still `65edd83b` and the
  judge-fix task (card/quote count parity, honest edit banner, card price) never reached origin.
- **Local AI = Claude Haiku via Claude Code CLI** (no API key; `.env.local` IA_PROVEEDOR=claude, IA_CLAUDE_TRANSPORTE=cli,
  IA_LOCAL_ESFUERZO=medium); production stays on Gemini.
- **Shipped this marathon:** D-038 single quote; REQ-007 Phase 5 (customer 3D edits) + P-045 graceful rollback; REQ-013
  catalogue repositories Phases 1–5; Taller build sheet (complete: helium, positions, foil lines) + helium/pump/measures,
  recipe cards, size profiles, light/lens; Kontext resume + metallic tint; AI rating (one POST per turn); honesty tests
  (CUS-03/CUS-04); scenario matrix + property tests; colour resolver rewrite + limits; prerender guard; W4 training
  harness, scale policy, figures capability, diagnostics; scene-AI time bounds (P-054); kill switch on armada/imagen;
  production fixes (catalogue on Vercel, /3d id guard, guided-3D plan audit); e2e smoke per release.
- **W4 training** (30 owner photos, Haiku CLI, US$0): pass 1 → pass 2: proporciones 0.447 → 0.482, colores 0.365 →
  0.385, IoU 0.524 → 0.559.

## Active focus
- Curated ideas through the single pricer + «Ideas del asistente» in the Taller (e7x); P-067 photo gaps; PM top-8
  (NC-4 rollback drill, NP-4 copy, NC-1 plan creation without Python). Owner report:
  https://claude.ai/artifact/TD2Co1cSeN6i4GExCjvJhU (48 h update ≈ Sunday 16:44).

## Top pending (see PENDING.md)
- P-066 curated-idea price parity; P-067 photo case gaps; P-057…P-065 review leftovers; owner on Monday: D-027…D-039
  review, R-36→R-24 wording, feedback-panel decision.

## Recent decisions (see DECISIONS.md)
- D-027 helium sphere volume · D-028/D-030 product judge timing · D-029 class-prefixed ids · D-031 manual VPS deploy ·
  D-032 owner-away defaults · D-033 dev servers allowed · D-034 no VPS deploy this weekend · D-035 reader-first persisted fields · D-036 review stop-rule · D-037 VPS approved · D-038 one quote · D-039 everything on.

_Last updated: 2026-10-10_
