# pictures — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._

## Open
- P-045 · GUIADA_MOTOR rollback is not graceful: after flipping back to python, open 3D conversations get edits refused (409 MOTOR_PYTHON), Python routes refuse 3D tokens, and adding an idea/redoing silently re-prices in Python (~×1.4). Design a graceful rollback (keep 3D plans priced by the engine until the conversation ends, or tell the customer) — BLOCKER for the switch · urgency: high · complexity: M · added 2026-10-09 · W7 dossier review
- P-010 · Commit photo-reading work (uncommitted) and merge e3-rapido f1198efd (precise AI size edits) · urgency: high · complexity: ? · added 2026-10-08 · REQ-001
- P-015 · REQ-002 go-live checklist: apply migrations 028 + 029 on Neon (with notice), run indexer --aplicar + upsert vectors, rebuild agente-core dist, visual review of Library filters/photo search, turn TALLER_RAG_ENABLED on only after the tuned eval beats today's search · urgency: high · complexity: ? · added 2026-10-08 · REQ-002
- P-018 · Photo fidelity (lote-02 photo 01, then 02–05): branch feat/foto-fidelidad (e4n) — implementer fixing 4 BLOCKER/9 MAJOR + orphan-field ledger test; then Claude reference → Gemini parity per photo · urgency: high · complexity: ? · added 2026-10-08
- P-021 · Refine acceptance feat/refinar-aceptacion (e4m) — approved, base of integ/foto-taller (was: fixing review (rule misses pared→piso/delete, verdict not audited server-side, margin uncalibrated → calibration script); owner-labelled A/B rounds (ROC) pending · urgency: high · complexity: ? · added 2026-10-08
- P-031 · Taller AI-UX redesign — owner picked B (D-021), IN PROGRESS e4x feat/ia-panel — was: owner to pick A or B (proposal artifact Nuv9GST6YR9HmGgAMoDdMr); common base first: scene diff by piece id, per-turn undo of only AI-touched pieces, abort, optional streamed steps · urgency: high · complexity: ? · added 2026-10-09
- P-041 · ajustar_salon reports grid capacity («40 invitados, caben 96») while only 5 tables of 8 are placed — confusing; report the placed capacity · urgency: med · complexity: S · added 2026-10-09 · W2 owner-phrases corpus
- P-042 · Guided 3D edits undo: inverse size edits drift (enlarge-then-shrink ≠ identity) and name-based colour returns can change the code — undo must restore the stored previous spec, not apply an inverse edit · urgency: med · complexity: S · added 2026-10-09 · W7 integration test
- P-039 · Finish library ideas 29/30/31 fix (branch fix/biblioteca-feedback 998a7b18, e7f): re-resolve stored plans with a live Python (precomputar-planes-ideas.ts --verificar needs PYTHON_BACKEND_URL + INTERNAL_HMAC_SECRET; this PC can't reach sslip → run where Python is reachable), write nueva-sempertex-09/10/11.plan.json, regenerate planes-ideas.json, align decoraciones.json cards, regenerate only 29/30/31 goldens · urgency: med · complexity: M · added 2026-10-09 · marathon
- P-048 · Scenario matrix gaps: 18 % of representable pieces fall to noRepresentables («colour doesn't reach the materials list») and skip geometry checks; seed 11 E-00146 arco+arco_no_denso overlap 8 cm (anchoEstimadoCm underestimates arc + flower overhang); seed 3 E-00077 garland sencilla under band · urgency: med · complexity: M · added 2026-10-09 · matrix re-review
- P-049 · Kill switch (guiada_motor_corte) never tells customers who already hold a wrong 3D plan, and the imagen/armada routes ignore it — proactive notice + block those routes under the kill · urgency: med · complexity: M · added 2026-10-10 · P-045 review A9
- P-051 · TS motor builds 0 balloons for pared_organica, figura, pared_no_densa, centro_mesa (fall back to Python / curated price) · urgency: med · complexity: M · added 2026-10-10 · property tests
- P-052 · Guided 3D colour resolver limits (after P-047 rewrite): (a) needless «dime cuál» when the plan has a single shop-only shade (Metal Dorado) and the new colour is already in the piece — needs stored repeat state; (b) Fashion Rosa 011 / Rosado 009 alternate on repeated «rosa»; (c) wording «no lleva azul claro; lleva azul» → «no encontré «azul claro»; tu plan lleva azul: ¿es ese?»; (d) test-propiedades-herramientas still uses additive seeds and a 10 % invalid-accept tolerance · urgency: med · complexity: M · added 2026-10-10 · resolver review 4
- P-054 · Taller «más R-24» on an arch converted to organico is measured with the mean radius (≈half the arch measure); three calls on a 120 cm arch reach ≈150 cm and the third took 128 s (pre-existing on main); density up to 2.5 not counted in the volume budget · urgency: med · complexity: M · added 2026-10-10 · W4 capabilities opus report
- P-002 · FLUX photo color fidelity: residual ΔE ~15 after hex prompt (c25490f1); next: photoreal capture or per-piece correction · urgency: med · complexity: ? · added 2026-10-08 · D-003, D-006
- P-003 · Resume idea digitization: 110 covered ideas left after lot 26, then new generators · urgency: med · complexity: ? · added 2026-10-08 · D-005
- P-007 · Split Taller3D.tsx (1022 lines) by responsibility: top bar, rail panels, viewer overlay, inspector, solo editor wiring · urgency: med · complexity: ? · added 2026-10-08
- P-008 · Split organico.ts (1529 lines) and escena.ts (740) by responsibility · urgency: med · complexity: ? · added 2026-10-08
- P-014 · 14 factory library items have no ficha/render (extractor dedups them against derived pieces: decoracion:mono_fucsia, flor_corazones, idea:forky/gallina/pollito…) · urgency: med · complexity: ? · added 2026-10-08 · REQ-002
  REQ-005 · Decorations from scratch (mural from image, free sculpture, bulk placement) + photo → model → save to Library (documented, questions pending) · high · added 2026-10-08 · requirements/REQ-005-decorations-from-scratch
  REQ-006 · Venue photo → 3D space (MVP: photo backdrop with matched camera) (documented, questions pending) · med · added 2026-10-08 · requirements/REQ-006-venue-photo-to-3d
- P-016 · Photo refine round: add an acceptance criterion (keep a round only if photo↔capture similarity rises and no wall piece drops/hides), then re-enable 1 automatic round · urgency: med · complexity: ? · added 2026-10-08 · REQ-001
- P-017 · Cursive gold foil «Love» (metalizado letras script, dorado) renders black in the viewer · urgency: med · complexity: ? · added 2026-10-08 · REQ-001 E2E
- P-022 · Owner: blind A/B labelling of ~30 refine rounds (photo vs before/after) to set the acceptance threshold; until then automatic refinement stays OFF (calibration 2026-10-08: embeddings can't separate small changes) · urgency: med · complexity: ? · added 2026-10-08
- P-023 · Confetti colour as data (`confeti: {colores}` in ColorOrganico/GloboDecoracion, ColorLeido.colorConfeti, SKU per confetti product) replacing the viewer heuristic — at integration · urgency: med · complexity: ? · added 2026-10-08
- P-026 · Pampas foliage (real plumes) — feat/pampas (e4t) in progress; needed by photos 02, 03, 05 · urgency: med · complexity: ? · added 2026-10-09
- P-034 · BalloonBuilder ideas (artifact SH28k1k2DhKHHDA2JMhApt): owner to pick; quick-win batch (S) pump seconds/dimensions/helium/recipe cards/size profiles/light presets, then build sheet, palette→Sempertex ΔE, 3-tier quote · urgency: med · complexity: ? · medium/M
- P-035 · ~~ (closed by D-026) · urgency: med · complexity: ? · Pricing policy for the 3D engine BOM: cheapest pack that covers the merma'd quantity (engine) vs Python's bigger packs (26 ideas: engine 0.67× Python in COP) — owner decision before switching GUIADA_MOTOR · high/S
- P-046 · Shopping list «Por pieza» lists identical decorations one per row («Ojo con venas 1…14 · urgency: low · complexity: S · 1 globo»): group identical pieces (× 14) · added 2026-10-09 · judge
- P-053 · Photo→3D scale notes never reach the user (foto.notas not rendered; only the agent context) — decide whether/how to tell the decorator when the scale is a bound, not a measurement · urgency: low · complexity: M · added 2026-10-10 · scale review
- P-004 · Viewer: export depth map and limit capture crop margin · urgency: low · complexity: ? · added 2026-10-08 · D-003
- P-005 · [bug] Selecting a piece costs 60–90 ms in dev (side-panel re-render) · urgency: low · complexity: ? · added 2026-10-08 · D-002
- P-006 · [bug] test-figuras3d fails: rizo_resorte uses 970 in T-160 (pre-existing, also on 6b2a4391) · urgency: low · complexity: ? · added 2026-10-08
- P-011 · «Más tupida» barely changes stroke garlands (engine saturated at density 1.25) · urgency: low · complexity: ? · added 2026-10-08
- P-013 · Scene-AI bank: 1 request left (estilo-30, size mix on one leg only: needs per-tramo RNG/colour quotas in organico.ts) · urgency: low · complexity: ? · added 2026-10-08 · bank
- P-027 · Burgundy chrome: no wine Reflex in the Sempertex table (915 used) and 915 renders too bright/red in the viewer — check swatch fidelity · urgency: low · complexity: ? · added 2026-10-09
- P-030 · RAG: `taller_taxonomia` (migration 028) has no writer and the search reads the taxonomy from code — orphan table: drop it or load it from src/lib/taller/taxonomia (decide with the reader) · urgency: low · complexity: ? · added 2026-10-09
- P-032 · Laya fine-tune for routing / customer pro-guardrail — researched (laya.train, head-only CPU or RLCD Kaggle; ~3–5k Gemini-labelled Spanish rows, US$1–3); not worth it vs Gemini today; revisit when the customer chat has volume · urgency: low · complexity: ? · added 2026-10-09

## Blocked
_None_

## Recently closed
- P-037 · Prerender guard now scans 28 server components too (connection()/"use cache" escapes); no offenders found; still one call hop (082a34fb) · urgency: med · complexity: M · closed 2026-10-10
- P-050 · ajustar_tamanos formats: premise not reproduced (declaration and zod share FORMATOS_AJUSTABLES); rejection now names valid sizes (390ac0a2) · urgency: med · complexity: S · closed 2026-10-10
- P-047 · Colour name→code audit + resolver rewrite (568/568 matrix, repeat changes 184→6) · urgency: med · complexity: ? · closed 2026-10-10
- P-043 · Ideas 30/31 same stored price — NOT a bug: both are 3 × (6164 + 13037) = 57,603 from their own plan lines · urgency: med · complexity: ? · closed 2026-10-10
- P-029 · /P-036 · urgency: med · complexity: ? · CI fully green on main (first time) · closed 2026-10-10 · 77b4af27
- P-040 · Pump section one row per size, collapsed (judge 6/10 fixed) · urgency: med · complexity: ? · closed 2026-10-09 · 21ba148c
- P-038 · Kontext resume by request_id · urgency: med · complexity: ? · closed 2026-10-09 · 9f8687a7
- P-033 · Prerender guard (partial; server components → P-037) · urgency: med · complexity: ? · closed 2026-10-09 · 53502782
- P-019 · Furniture (37+2 items, agregar_mobiliario) — MERGED into integ/foto-taller b6f58535 (was: fixing review (params lost on placement, Gemini schema size) · urgency: high · complexity: ? · added 2026-10-08
- P-020 · Materials/ambience feat/realismo-ambiente (e4q) — MERGED into integ/foto-taller d138cf83 (was: fixing review (global env map → per-viewer, Sala.ambiente orphan, confetti colour/cost, squash knot) · urgency: high · complexity: ? · added 2026-10-08
- P-024 · DONE 2026-10-09 (APP_ORIGINS set on advin-vps, web recreated healthy) — was: VPS: set APP_ORIGINS=https://<public domain> in /etc/demo-decoracion/demo.env and verify with curl -X POST -H "Origin: …" on happie/recomendar (pre-existing 403 risk behind nginx; hand deploy, owner notice required) · urgency: high · complexity: ? · added 2026-10-08
- P-025 · Cursive text signs + `marco_tela` — MERGED into integ/foto-taller (was: feat/rotulos (e4s) in progress; needed by photos 02, 04, 05 · urgency: high · complexity: ? · added 2026-10-09
- P-028 · FIXED in main a0fad72a — was: BUG in main: an agreeing/plural foliage colour in a photo reading ("monstera rosadas", "pampas doradas") throws in floresPedidas and drops the whole garland — fix in feat/pampas (two-level: normalise + never drop the piece) · urgency: high · complexity: ? · added 2026-10-09
- P-012 · Occasion ids unified to the taxonomy (REQ-002 step 0) · urgency: med · complexity: ? · closed 2026-10-08 · 5fd36426
- P-009 · Chrome/metal balloons rendered almost black · urgency: med · complexity: ? · closed 2026-10-08 · 89857ada
- P-001 · Implement the approved 3D editor redesign · urgency: med · complexity: ? · closed 2026-10-08 · commits 5adaa808..f0c2895a

## Notes
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._
REQ-003 · Scene agent v2 — merged and pushed (main 0046ab80); left: paid eval (cap US$0.50) + P-013 · high · added 2026-10-08 · requirements/REQ-003-scene-agent-v2
REQ-004 · Users (email+password, admin|staff) + AI spend ledger & dashboard for Gemini and fal.ai (no caps yet) · high · added 2026-10-08 · requirements/REQ-004-users-and-spend-control
REQ-002 · Workshop library RAG + celebrations taxonomy — LIVE 2026-10-09 (Neon indexed + vectors, flag on in Vercel; photo-search eval pending) — started 2026-10-08 (steps 0–2 in worktrees e4a/e4b + embeddings research + infra map; no code merged yet) · high · added 2026-10-08 · requirements/REQ-002-workshop-library-rag
REQ-001 · Photo → scene + flexible structures (13 owner photos) · high · added 2026-10-08 · requirements/REQ-001-photo-to-scene
REQ-007 · Engine behind the customer journey (hidden 3D, 2D views, basic edits, two products) — PLAN v2 after 3 antagonistic architects; BLOCKED on owner decisions D1–D5 (canonical engine, real separation, 2D style, edits, approved quotes) · critical · added 2026-10-08 · requirements/REQ-007-engine-behind-the-customer-journey-2d-vi
REQ-008 · Complex event compositions ("quiero una boda": venue layout, centrepiece per table, ceiling) — IN PROGRESS 2026-10-09 (e4v + e4w) · high · added 2026-10-08 · requirements/REQ-008-complex-event-compositions-wedding-hall
