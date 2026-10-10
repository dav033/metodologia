# pictures — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex balloon-decoration demo (`demo-decoracion`: Next 16 on Vercel + Python ai-api on a VPS). Two products on one
engine: the **Taller 3D** (`/3d`, pro tool with a scene AI agent) and the **guided customer chat** (`/asistente`,
quotes priced by Python; the 3D engine sits behind `GUIADA_MOTOR=python`).

## Current state (main = `ad6a3710` pending push / `0c7cc72e` pushed, 2026-10-10 ~07:00)
- **72 h marathon running** (since 2026-10-09 16:44, session 83576a42; owner away all weekend, D-032/D-033).
  Live state: `research/ciclo/STATE.md`.
- **CI fully green for the first time** (77b4af27). VPS deploy is manual and gated on green CI (D-031); no VPS deploy
  this weekend (D-034) — main carries Python quote changes never deployed there.
- **Local AI = Claude Haiku via Claude Code CLI** (no API key; `.env.local` IA_PROVEEDOR=claude, IA_CLAUDE_TRANSPORTE=cli,
  IA_LOCAL_ESFUERZO=medium); production stays on Gemini. Dev server :3010 runs origin/main.
- **Shipped this marathon:** REQ-007 Phase 5 (customer 3D edits) + P-045 graceful rollback; REQ-013 catalogue
  repositories Phases 1–3 (Neon migrations 033/034 applied; furniture fichas not indexed yet); Taller helium/pump/
  measures, recipe cards, size profiles, light/lens; Kontext resume (no double charge) + metallic tint; AI rating fix;
  honesty tests (CUS-04); scenario matrix + property tests; colour resolver rewrite; prerender guard; W4 training harness.
- **W4 training baseline** (30 owner photos, Haiku CLI, US$0): proporciones 0.446, colores 0.366, IoU 0.525.

## Active focus
- W4 fixes (capabilities, scale/metric) → re-run the 30 photos; build sheet (PRO-01); switch dossier evidence.

## Top pending (see PENDING.md)
- P-039 library ideas 29–31 need live Python; P-045 follow-ups P-049; P-050/P-051 tool/engine gaps; P-052 resolver
  limits; owner on Monday: VPS deploy note, REQ-013 Phase 3 Neon apply, D-027…D-034 review, R-36→R-24 wording.

## Recent decisions (see DECISIONS.md)
- D-027 helium sphere volume · D-028/D-030 product judge timing · D-029 class-prefixed ids · D-031 manual VPS deploy ·
  D-032 owner-away defaults · D-033 dev servers allowed · D-034 no VPS deploy this weekend.

_Last updated: 2026-10-10_
