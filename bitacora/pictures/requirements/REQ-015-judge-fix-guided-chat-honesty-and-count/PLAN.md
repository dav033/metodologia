---
req: REQ-015
status: in-progress
created: 2026-10-13
---
# Plan — REQ-015 — judge-fix: guided chat honesty and count/price parity

## Approach
Branch `feat/req-015-judge-fix` from origin/main 65edd83b, local only. One milestone per defect, smallest blast radius first; each milestone: failing test → fix → gate subset → antagonist review → commit (Spanish message, repo trailers). Alternative (one big patch) rejected: reviewability. Code map: research/2026-10-13 explorer report summarised in tasks below.

## Global constraints
AGENTS.md rules; no `any`; no paid calls; no push; `npm run gate` green before the last commit; customer copy in Spanish, no engine jargon.

## Tasks
- [x] T1 — Measure why idea card (resumenIdea, idea-vista.ts:76, detalles-ideas.json) says 101/102 and plan (generarPasosPlan) says 115; make the card use the plan engine's total or label it «aprox.»; test that card total = plan total for the 28 golden ideas · files: src/components/guiado/idea-vista.ts, TarjetaEleccion.tsx · verify: `npx tsx scripts/test/test-detalles-ideas.ts` (no --conditions flag) · covers: R1, US-1
- [x] T2 — Show «Materiales desde $X» on idea and plan cards from cotizarBom/costearDecoracion; parity test card = quote · after: T4 · files: TarjetaEleccion.tsx, TarjetaPlan.tsx, costear-idea.ts · verify: `npm run test-cotizacion-unica` · covers: R2, US-2
- [x] T3 — Colour-swap banner prints the real per-colour diff and price change (ajuste-plan-guiado.ts:966/986, AjustarPlan.tsx:209, edicion-chat-guiada.ts:122); never «igual» when a count moved · after: T1 · verify: `npx tsx --conditions=react-server scripts/test/test-ajuste-plan-guiado.ts` · covers: R3, US-3
- [x] T4 — ROOT FIX of D2/D5 (found in T1): chip «Cuánto cuesta»→«usar» goes through /api/chat where the model proposes and Python builds a NEW plan (115) instead of the idea's stored exact plan (101/102); answer canned chips by rules in elegirOpcion (VistaGuiada.tsx ~1480-1505) using planDesdeIdea/stored plan, no model turn · after: T1 · verify: `npx tsx --conditions=react-server scripts/test/test-precio-chat-guiado.ts` · covers: R4, US-4
- [ ] T5 — Count/size/colour questions on a chosen idea answered by rule (route.ts:150-191, consulta-plan-chat.ts:86) · after: T1 · verify: `npx tsx --conditions=react-server scripts/test/test-asistente-guiado-contrato.ts` · covers: R5, US-5
- [ ] T6 — Rating row: one collapsed «¿Te sirvió?» after the quote, ≥40 px targets (CalificacionGuiada.tsx, VistaGuiada.tsx:1881-1890) · verify: `npm run ui:test-calificacion-chat` · covers: R6, US-6
- [ ] T2b — Idea card price (D3 second half), owner chose option A: after «Me gusta» request the idea's exact plan via /api/plan-idea and show «Materiales desde $X» with the same total as the quote; if Python is down the card says «precio al elegir» (never a number that can differ) · after: T3 · files: TarjetaEleccion.tsx, VistaGuiada.tsx, agregar-idea.ts · verify: `npx tsx scripts/test/test-opcion-idea-guiada.ts` · covers: R2
- [ ] T8 — Wiring tests for T4 (VistaGuiada effect): one user bubble per chip click, no model call, fallback when /api/plan-idea fails is explicit, chip not marked chosen if blocked by caps (T4 concerns 1-3) · after: T4 · verify: `npx tsx scripts/test/test-opcion-idea-guiada.ts` · covers: R4
- [ ] T7 — Register the unscripted guided tests (edicion-plan-chat, crud-plan-chat, precio-chat, ajuste-plan, usabilidad-97) in package.json/gate so they run · verify: `npm run gate` · covers: all

## Verification
`npm run gate` green; `npx tsc --noEmit`; `npm run lint`; a before/after table of card vs plan vs quote counts and prices for the judge's dino and XV ideas.

## Rulings
- 2026-10-13 owner approved the approach («adelante») and answered: scope D1-D5 + D8; tsc/test debt separate (P-075); delivery = local branch for owner review, no push/PR.
- Plan self-approved (owner away, autonomy delegated in the loop request).

## Progress log
- 2026-10-13: owner decisions: price on idea card = option A (T2b); AGENTS.md/CLAUDE.md restored (commit separate); T3 runs on Opus. T2 done d4759335.
- 2026-10-13: spec ready, plan written, code map from explorer.
- 2026-10-13: T1 done (card labelled «aprox.» + recalculation note; exact count not computable in TS, Python owns it; stored plans give 101/102 while chat path re-resolves to 115).
- 2026-10-13: T1 done 03b77699 (card says «aprox.»). Finding: 115 comes from the chip→/api/chat→Python new plan, not from local data; T4 promoted before T2 as the root fix. Baseline: `npx tsc --noEmit` has 180 pre-existing errors; test-colores-claros-guiada and test-ui-cotizacion-guiada fail on main.
- 2026-10-13: T4 done: chips «Cuánto cuesta»/«Aprender» with a chosen idea now build the idea's stored exact plan via /api/plan-idea (no model turn, Python at runtime for the plan itself) and answer price from the card's cotizacion; with a plan already containing the idea they resolve on it; free text unchanged. Antagonist: fixed plan-ajeno route (A1), pending ref guarded by idea id (A2), double scroll (A5). Open: duplicate user bubble (A4), chip marked chosen if blocked (A6), plan-idea failure still falls back to model.
- 2026-10-13: T2 done: plan card shows «Materiales desde $X (uso personal, con IVA)» = cotizacion.total (same as quote/chat; hidden for negocio use and while recalculating). Idea card NOT priced: no local price exists (needs the Python plan via /api/plan-idea / costearDecoracion); price appears after «Cuánto cuesta». Antagonist: fixed negocio mismatch (A1). Open: «desde» wording (A3), CotizacionPersonalGuiada hardcodes «con IVA» (A2).
- 2026-10-13: T3 done 47effb65: shared pure `diferencia-colores.ts` (picker + chat) prints the real per-colour diff, partial-swap location and price change (uso personal, con IVA; none for negocio); «igual» only when no count moved; pre-change texts and the model tool description no longer promise other colours stay. Root cause measured: on the stored dino plan Python's participation count does not move others on a swap (102→102, 108→108); the judge's 36→33 came from the model-built 115/121 plan counted by pattern/motor, so keeping the others fixed needs a Python change (pin per-colour counts on reemplazar_color). Antagonist: applied A1-A4, A6, part of A5. Open: 3D-motor path confirmation comes from its server; protagonismo/quitar_color/colores_pieza still say «lo demás queda igual»; «más grande» 3 m cap not announced.
