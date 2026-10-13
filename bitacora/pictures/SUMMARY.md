# pictures — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex balloon-decoration demo (`demo-decoracion`: Next 16 on Vercel + Python ai-api on a VPS). Two products on one
engine: the **Taller 3D** (`/3d`, pro tool with a scene AI agent) and the **guided customer chat** (`/asistente`,
quotes priced by Python; the 3D engine sits behind `GUIADA_MOTOR=python`).

## Current state (last deployment record: `65edd83b`, 2026-10-11 06:14; local work: 2026-10-13)
- REQ-015 local branch `feat/req-015-judge-fix` at `4b7b5cab`, 21 commits ahead of tracked origin/main; T12 cap and audit #3 corrections integrated as uncommitted working-tree changes. No push/deploy in this session. Both independent review axes approve the corrected findings; all 10 gate suites pass (P-076 closed).
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

## REQ-015 judge-fix (2026-10-13)
- Branch `feat/req-015-judge-fix` (24 commits, local, not pushed): count/price parity, chips by rules (D-043), cost cap (D-044), honest colour-swap, rating row. Gate GATE OK, tsc 0, lint 0 errors. Owner decides push/PR. Report: requirements/REQ-015-*/REPORT.md.

## Active focus
- REQ-015 implementation and verification complete locally, ready for owner review/commit/publication: chosen-idea chips by rules, shared price, honest color counts, durable quote cap. Restored ambiguous/composite idea prices show “Precio al elegir”; no session contract change. REPORT.md contains evidence; visual rating UI 9/9, contract 27/27, final types/build pass.

## Top pending (see PENDING.md)
- P-075 remaining historical test debt; P-077 calibrate the 300/hour quote cap from production counts (not queried in this session). Historic type-error counts were stale generated Next route references; source types and application build now pass locally.

## Recent decisions (see DECISIONS.md)
- D-027 helium sphere volume · D-028/D-030 product judge timing · D-029 class-prefixed ids · D-031 manual VPS deploy ·
  D-032 owner-away defaults · D-033 dev servers allowed · D-034 no VPS deploy this weekend · D-035 reader-first persisted fields · D-036 review stop-rule · D-037 VPS approved · D-038 one quote · D-039 everything on.

_Last updated: 2026-10-13_
