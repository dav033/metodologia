# Product judge: guided chat /asistente on production, 2026-10-11
Target https://demo-decoracion.vercel.app/asistente (worktree e7q = origin/main; Python plan engine is up now). Playwright + system Chrome via the repo's
e2e/humo helpers (login, hydration wait, paid-route policy), desktop 1280x900 and phone 390x844 (touch, DPR 2). Script: scratchpad/juez/*.mts. Repo untouched.
Never clicked «Ver cómo quedaría», «Recalcular mi plan», «Comprar» or checkout; no paid route was called.
Phone: the 3 chat turns that need Gemini were replayed from the desktop session (sessionStorage) so they were not paid twice; plan creation, edits,
colour picker, quotes and one typed turn ran live on the phone. (A saved plan replayed from ANOTHER session gets 409 on edit; a plain reload works, so not scored.)
Spend: 14 Gemini turns (gemini-3.6-flash): 4 typed + 10 chip taps / «Cuánto cuesta» / use question. The chip steps are NOT free as assumed. Client cannot
see tokens; estimate US$0.04-0.07, so at or slightly over the 0.05 cap. FLUX/Python spend: none.

## Overall 7/10 (last judge 5/10, blocked by Python). The flow now works end to end, both viewports, no console errors or failed requests in live runs.
- (a) Understands what to do: 7. Chips lead every step, big primary buttons (44-48 px), «Me gusta esta» -> «Crear mi plan» is obvious. But: after picking an idea the
  other cards lose their button and the chips vanish (no compare, no swap; only ⋯ > «Empezar de nuevo»); free text «¿cuántos globos lleva?» got the wrong answer (D1).
- (b) Prices: 6. Chat quote = plan-card quote to the peso ($176.591 / $181.975) and follows edits ($177.802 bigger; $163.038 after colour). Leftovers explained per line
  («Usas 10 · compras 1 paquete de 12 · te sobran 2») and in the footer («te sobran 124 para reponer…»; IVA incluido, sin montaje). But the card shows no price and its
  balloon count (101/102) disagrees with plan and quote (115) for both ideas tried (D2, D3).
- (c) Edits: 7. «Hacerla más grande» and colour swap work live in ~1.5-2 s, green banner «Listo: …», «Último ajuste: …» label, counts and 3D update. But «lo demás quedó igual»
  is false (D4), the height capped at 3 m silently (2,91 -> 3 m under a «10 %» label), and the price change is never announced.
- (d) Phone layout: 8. No horizontal overflow in 14 states, primary taps 44-48 px, text 12-16 px, picker is a clean bottom sheet. Misses: rating pills 25x36, «Calificar»
  55x32, «Contar por qué» 90x32, stepper −/+ 36x36, «?» help icons 20x20, «¿Es para tu negocio?» link 20 px high; 11 px badges («Referencia»/«Parecida»); the floating
  ↓ button covers prices in the quote (D8).
- (e) Spanish: 8. Warm and natural; no R-12, cuartetos or «motor» anywhere in the customer copy. Weak spots: unexplained «Referencia»/«Parecida» tags, a fake user bubble
  «Quiero saber cuánto cuestan los materiales.» after tapping «Cuánto cuesta», and one colour with three names («Reflex Verde Lima» chip, «Verde lima cromado» list,
  «reflex verde lima» in the message).
- (f) Speed: 7. Landing 1.8-2.1 s (login 3.3-5.2 s). Each chip turn 2.7-4.7 s. First ideas: dinosaurs 3 taps ≈ 9.7 s of waiting, XV rosa y dorado 2 taps ≈ 9.5 s.
  Quote: «Me gusta» 1.3 s + «Cuánto cuesta» 3.8 s + use choice 5.7-7.4 s ≈ 11-12 s (the slow step is a model turn). Plan 2.3-4.6 s; plan-card quote 1.8 s; edits 1.5-2 s.
- (g) Nothing broken: 8. 0 console errors, 0 failed requests in live desktop and phone runs; 3D plan drew. Defects are logic/content (D1, D2, D4, D6), not crashes.

## Journeys
1. Dinosaur 7-year-old: Cumpleaños > 7 a 12 años > Infantil de dinosaurios > 2 ideas > «Me gusta esta» (Semiarco, 101 globos) > «Cuánto cuesta» > use > $176.591 > plan 115 globos
   > más grande (121, 2,71x3 m) > Fashion Naranja for lime (121) > «Cuánto cuesta» $163.038. Works on both viewports.
2. XV rose-gold: 6 ideas (carousel + «Ver más ideas»), no side-by-side compare is possible; picked #1 (102 globos); typed «¿cuántos globos lleva?» -> bot asked «¿Es para tu negocio o uso personal?» (D1).
3. Edge: «algo bonito para una fiesta» -> friendly «¿Qué temática, estilo o colores…?» + 6 theme chips (desktop and phone). «¿me ayudas a elegir un teléfono celular barato?» -> polite redirect to decorations + chips. Both good.

## Top 8 defects (where | what | why it hurts | fix | size)
- D1 | Free-text turn, /api/asistente-guiado | «¿cuántos globos lleva?» with an idea chosen is answered with the business/personal question (card above already says 102) | the customer's direct question is ignored and looks like a loop | answer count/size/colour questions from the chosen idea or plan by rule before the model (like edicion-plan-chat) | M
- D2 | Idea card «TU ELECCIÓN» vs plan | card says 101 (dino) and 102 (XV) globos; plan and quote say 115 for both; per colour 30/26/15/15/15 vs 35/33/15/11/21 | «¿cuántos globos lleva?» has two answers; trust drops at the quote | show the plan engine's number on the card, or label «aprox.» and say the plan recalculates | M
- D3 | Idea card, plan card | no price on either; it takes «Cuánto cuesta» + use question + 6-7 s | the mother compares ideas without knowing the cost | show «Materiales desde $X (uso personal)» on card and plan using the same costing | M
- D4 | Colour swap banner and picker | «lo demás quedó igual» / «los demás colores quedan igual», but 3 other colours lost 3 balloons each (36>33, 36>33, 22>19) and Naranja got 20 vs the 11 lima had | breaks the honest-edit promise (c) | print the real diff («Naranja 20 (antes 11); −3 azul naval, −3 verde, −3 dorado») or keep the others fixed; also mention the price change and the 3 m cap | M
- D5 | Chips, «Cuánto cuesta», use choice | each is a Gemini turn (3-7 s, paid), 10 of my 14 turns; the brief and the owner assume they are deterministic | slow quote and spend on steps that need no model | send the canned chip/quote requests straight to the rules/costing path, skip the model | M
- D6 | Ideas for «Infantil de dinosaurios» | only 2 ideas, the 2nd is «Guirnalda verde salvia con flores naranjas» tagged «Parecida» | off-theme card for a dinosaur party; tag unexplained | show ≥4 on-theme ideas or say «Parecida a lo que pediste» | S/M
- D7 | After choosing an idea | other cards lose «Me gusta esta», chips vanish, no «Cambiar de idea» (only ⋯ > «Empezar de nuevo», which wipes everything) | no way to compare 2 ideas as journey 2 asks | keep the carousel live with a visible «Cambiar de idea» and a 2-up compare (globos + precio) | M
- D8 | Rating widget + phone polish | «¿Qué tal quedó? 1-10» sits above the reply chips after every answer (≈240 px on phone), pills 25x36; «?» icons 20x20; ↓ button covers prices | actionable chips are pushed down; small taps | one collapsed «¿Te sirvió?» after the quote; ≥40 px targets; hide ↓ over cards | S

## Price-consistency table (production, personal use)
| Idea | Idea card | Chat «Cuánto cuesta» | Plan card | Quote inside plan | After edits (plan card quote) |
| Semiarco selvático de dinosaurios | 101 globos, no $ | $176.591, usa 115, sobran 124 | 115 globos | $176.591 (same, 115) | más grande: 121 > $177.802; + naranja: 121 > $163.038, sobran 128 |
| Semiarco oro rosa, dorado y amarillo pastel | 102 globos, no $ | $181.975, usa 115, sobran 106 | 115 globos | $181.975 (same, 115) | not edited |
Verdict: card vs plan/quote 101/102 vs 115 (FAIL); chat quote vs plan quote vs plan count (PASS); quote vs edited plan 121 usados = 121 globos (PASS).

## Screenshots (14, next to this file)
JUEZ-ASISTENTE-2026-10-11-01..07 desktop (ideas, elección 101, cotización, cambio de color, 6 ideas XV, pregunta libre mal respondida, fuera de tema); -08..14 phone (inicio, ideas, plan 115, ajustar, costo, selector de color, mensaje vago).
