# PM backlog - pictures (END CUSTOMER persona, demo-decoracion)

Append-only, one section per PM cycle. Read-only research: no code, servers or paid calls.

## PM-customer delta — 2026-10-09 cycle 0

Sources read: SUMMARY.md, PENDING.md, DECISIONS.md (D-019, D-020, D-022, D-023, D-024, D-025, D-026), day log 2026-10-09
(session 46a78670), REQ-007 PLAN-v3.md and PARIDAD-2026-10-09.md (incl. calibration 1.2.0). Code grep on
demo-decoracion `src` at HEAD df49d255 (branch fix/color-organico-conteo). Not in this checkout: `GUIADA_MOTOR`, the 3D
customer view, voice button and customer feedback. They live on branches (e4y voice, e4z feedback, e6c guided-motor)
that I did not inspect. No live feedback or logs were read (no network, no secrets). Market: one web search; vendor pages
form.jotform.com/212901914353148, addtoevent.co.uk/suppliers/balloon-wali, airtasker.com/uk/services/balloon-decoration.

Market observation (small sample): decorators sell through quote-request forms (event date, venue, colours, budget,
product type such as arch / table balloons / ceiling), ask for inspiration photos, promise a response window, and treat
a deposit as the booking. None of the sampled vendors offered an interactive photo preview before booking. "Ver como
quedaria" plus the 3D still is therefore a differentiator, not a parity item.

Ranked by value/effort (value first, then size):

### CUS-01 · Customer 3D still on the plan card in /asistente (D-024, PLAN-v3 Phase 3) · size M
- Problem: the guided customer sees a Python-drawn plan (`GraficaMotorGuiada`), not the same geometry the quote is built from.
- Evidence: PLAN-v3 §1.4 and Phase 3 (TarjetaPlan l.243/331; ModificarPieza hidden for 3D); D-020 (no drag/create); D-024 (switch now, flag `GUIADA_MOTOR=3d|python`).
- User value: highest. Owner's top UX priority and the visible part of the engine switch.
- Acceptance: with the flag on 3d, each plan card shows stills with frente or tres-cuartos camera; legend chips equal BOM colours; ModificarPieza is not rendered for 3D plans; with WebGL disabled the SVG fallback renders and the circle count per colour equals the BOM; `/asistente` first-load JS unchanged vs main (build check).

### CUS-02 · Count consistency: idea card, plan card and quote show the same balloon count · size S
- Problem: engine counts differ from Python (x1.41 before calibration; 1.2.0 lowers organic counts). The customer may see one number on the card and another in the quote.
- Evidence: PARIDAD §1 (engine 3,384 vs 2,403 on 28 ideas, pre-calibration); PLAN-v3 §9 Q1 (merma 8 % before package rounding) and Q2 (card label "cantidades del motor").
- User value: avoids a "why does the price differ" moment; protects quote trust.
- Acceptance: for the 28 golden ideas, card total = quote total (balloons) on the engine path; the label reads "cantidades del motor" when motor=3d; a test fails when the two sums diverge.

### CUS-03 · Say it when the engine cannot draw the requested structure (Python fallback per plan) · size S
- Problem: a customer can ask for something the engine cannot represent (figure, centro de mesa, bouquet, asymmetric ring, organic wall). Today the Python fallback would silently produce a different-looking plan.
- Evidence: PLAN-v3 §5 table (about 4–5 of 28 ideas not representable); §9 Q5 (photo plans fall back to Python per plan).
- User value: honesty, and no surprise change of look; same spirit as D-023.
- Acceptance: for each unrepresentable structure the card shows an aviso in customer words (no engine terms); a unit test lists the 18 official structures and asserts representable or unrepresentable with a reason.

### CUS-04 · Honesty tests for customer chat edits (D-023 extended) · size S
- Problem: the D-023 "No pude: ..." disclosure exists for the Taller path; PLAN-v3 Phase 5 requires it for customer edits, but no test covers customer failures yet.
- Evidence: D-023 (owner incident, 4 false confirmations); PLAN-v3 Phase 5 tests "failure disclosure".
- User value: the customer never believes a change happened when it did not.
- Acceptance: 10 forced-failure edits (one per HERRAMIENTAS_EDICION) each yield a "No pude: ..." line; a success reply never appears when the server result is an error.

### CUS-05 · Burgundy chrome renders red in the 3D customer view · size S
- Problem: "vino" chrome maps to 915 Reflex Cristal Rojo and renders bright red.
- Evidence: SUMMARY known issues; PENDING P-027; day log 2026-10-09 (photo 02 reference, material note).
- User value: colour is the first thing a customer checks against the balloons they buy.
- Acceptance: owner reviews captures of 915 against a vino reference swatch; a decision is recorded (accept, substitute, or label "aprox."); the 3D still follows the decision on 3 colour test cards.

### CUS-06 · Classic arch inflation: owner decision (arches 01, 02, 14) · size S decision / M build
- Problem: engine is 22 % under Python and 29 % under photos on classic arches (5 quartets/m at 25 cm).
- Evidence: PARIDAD §D "Classic arch (item 6)", owner question still open.
- User value: the arch is a core classic structure; a wrong count means a wrong quote.
- Acceptance: owner answers the inflation size (recorded as a D-number); after the chosen mapping, arch counts are within ±20 % of the photo estimates for 01, 02, 14.

### CUS-07 · Visual sign-off of sencilla / media / lujosa before the switch · size S
- Problem: density changes were measured, never looked at (no dev server during calibration).
- Evidence: PARIDAD §D caveats ("should be seen once in the Taller before the switch").
- User value: customers pick density from the card; holes in sencilla must read as intended.
- Acceptance: 3 captures per density (organic garland, column, semiarc) signed off by the owner as "looks right", or listed as fixes; decision recorded in the bitacora before PLAN-v3 Phase 7.

### CUS-08 · Voice dictation in the guided chat: confirm real state · size S
- Problem: no voice code in this checkout. SUMMARY says the Vercel env is still off (VOZ_ENABLED off), while D-023 says it goes live in production. The two sources conflict.
- Evidence: SUMMARY "Voice (REQ-009)"; D-023; no voice code under src/components or src/app.
- User value: owner asked for dictation everywhere; cost 0.
- Acceptance: owner confirms the real state; with VOZ_ENABLED on, a logged-in customer can dictate in /asistente on iOS Safari and Android Chrome; with it off, no mic button appears (no dead control).

### CUS-09 · Customer-only edits limited to the D-020 list · size M
- Problem: customers must ask for changes in words or use size and colour controls; the 3D edit ops are not mapped yet.
- Evidence: D-020 (AI requests, colour refs, colour proportions, size proportions); PLAN-v3 Phase 5 (10 tools).
- User value: the customer changes what matters without a pro-level control panel.
- Acceptance: each of the 10 HERRAMIENTAS_EDICION maps to one pure op; a test asserts no op adds geometry outside the official list; the size control maps to tamano_pieza and the colour slider to proporcion_color.

### CUS-10 · Phone performance of the lazy 3D chunk (about 200 KB gzip) · size M
- Problem: the first plan on 4G downloads the three.js chunk; WebGL context loss on mid-range phones.
- Evidence: PLAN-v3 Phase 3 risks; not measured yet.
- User value: the card must appear on first paint, even on weak phones.
- Acceptance: the 3D chunk loads only when a plan card is shown; the still appears within 3 s on a throttled 4G profile (documented run); webglcontextlost shows the SVG fallback, never a blank card.

### CUS-11 · "Ver cómo quedaría" photo from the same geometry (PLAN-v3 Phase 4) · size M
- Problem: the photo is generated from the Python plan today, so it can disagree with the 3D still.
- Evidence: PLAN-v3 Phase 4 (signed spec, prompts consumed not edited, `/edit` with capture as base); BarraPlanVigente.tsx l.21.
- User value: the photo the customer keeps matches what they were quoted; main differentiator.
- Acceptance: the prompt contains no customer free text; a token mismatch returns 4xx; a failed generation shows a retry button; cost per plan is logged and the hourly cap applies.

### CUS-12 · Customer rating per AI turn (D-022 full form in customer chat) · size M
- Problem: no customer feedback path yet; the owner wants every AI action rated with before/after state.
- Evidence: D-022; PLAN-v3 Phase 5 "forward-compatible with e4z" (PRODUCTOS_FEEDBACK = taller, cliente); not in this checkout.
- User value: finds AI gaps in the real customer journey, as the owner asked.
- Acceptance: each customer AI turn offers a 1–10 rating plus reasons, non-blocking (input stays enabled); the record stores before/after espec and captures; the form opens automatically after an undo.

### CUS-13 · Quote request fields and expectation copy (market check) · size M
- Problem: the quote path does not say what the decorator needs (date, venue, colours, budget, delivery) or when the customer will hear back; the meaning of the deposit is unclear.
- Evidence: market sample (quote-request forms ask these fields; one vendor asks for at least 48 h for a reply; a deposit books the date). Our CotizacionPersonalGuiada.tsx (161 lines) has no response-time copy.
- User value: fewer back-and-forth messages; the customer knows when to expect an answer.
- Acceptance: the quote request captures date, venue, colours, budget and delivery as required or optional fields; copy states the response window the owner confirms; a test covers required-field validation.

### CUS-14 · Explain leftover balloons and bag sizes on the quote · size S
- Problem: quotes use Sempertex standard presentations (D-026), so the customer may see spare balloons they did not ask for.
- Evidence: D-026; PARIDAD §1 (Python purchase cost 3.25 x consumption cost over 28 ideas).
- User value: the price makes sense; no hidden surplus.
- Acceptance: the quote lists packs and spare balloons per colour; a test asserts spares = packs total - needed.

Open owner questions (not blocking): CUS-06 inflation size; CUS-08 real voice state; CUS-05 burgundy substitution; CUS-13 response window.

> Lead note (16:58): PM-customer cycle 0 read the MAIN CHECKOUT, which is on the stale branch fix/color-organico-conteo (not origin/main b4433bc9). Items about GUIADA_MOTOR/Phase 3/voice/feedback "missing" are stale — those are on main. Next PMs read code from worktree C:/Users/davidt/Downloads/e6f (= origin/main).

## PM-pro delta — 2026-10-09 cycle 0

Scope: persona PRO DECORATOR (Sempertex decorator who quotes, builds and keeps stock). Code checked on
`C:/Users/davidt/Downloads/e6f` (origin/main b4433bc9), not the stale `pictures-workspace/demo-decoracion` checkout.
Overlap column refers to the 19 numbered ideas of the BalloonBuilder artifact `SH28k1k2DhKHHDA2JMhApt` (ideas 1–19,
the "qué copiar" table). The 15-item list in `research/balloonbuilder/notas.md` is a subset of it.

Already built on main, so NOT listed: professional quote with labour, equipment and indirect lines plus granel mode
(`components/cotizacion/`, `lib/cotizacion/`); profit field and margin summary (`CampoGanancia.tsx`, `ResumenPrecio.tsx`);
quote validity (`lib/cotizacion/vigencia.ts`); approve button for the client proposal (`components/propuesta/BotonAprobar.tsx`);
build sheets for plan types (`components/plan/*/HojaArmado*.tsx`); module studio with FLUX render (`app/3d/modulos`,
`components/modulos-estudio/`); ΔE candidate display against Sempertex (`components/referencia/DetalleTecnicoColores.tsx`);
Taller shopping list with copy (`components/tres-d/ListaCompra.tsx`).

Ranked by value to the decorator, then size.

- PRO-01 · Printable build sheet for a Taller scene or module: count per colour and size, one numbered ring diagram per layer, accessories listed.
  Problem: the Taller shopping list only copies text (`ListaCompra.tsx`, copy button). Printable build sheets exist only for plan types (`components/plan/patron/HojaArmado.tsx`, `HojaArmadoBouquet.tsx`, `HojaArmadoGuirnalda.tsx`), not for `/3d`.
  Evidence: e6f `components/tres-d/Taller3D.tsx:956` (ListaCompra mounted), `lib/globos3d/impresos-catalogo.ts` (only printed items).
  Value: the decorator takes it to the venue; it makes the 3D work usable on site. Overlap: idea 3 (exploded build sheet). Size M.
  Acceptance: from a saved scene, "Hoja de armado" opens a print view (`@media print`) with one row per (colour, size) whose totals equal the Taller totals; one diagram per layer; checked by hand on 2 scenes; printing to PDF gives at most 4 layers per page.

- PRO-02 · Helium and ribbon lines in the scene shopping list: litres at 7 % loss, tanks needed for the region, metres of ribbon.
  Problem: `ListaCompra.tsx` lists balloons only. Helium appears in plan bouquets (`components/plan/bouquet/`) and as a cost concept (`components/cotizacion/conceptos-gasto.ts`, "Tanque de helio"), not in the 3D list.
  Evidence: e6f `components/tres-d/ListaCompra.tsx`; BalloonBuilder helium calculator (`research/balloonbuilder/notas.md`, section Free Helium Calculator).
  Value: a helium bouquet or ceiling is bought by litres, not by balloon. Overlap: idea 11. Size S.
  Acceptance: a scene with at least one helium piece shows litres and tanks in the list; 10 helium balloons of 30 cm with 7 % loss give 97 L; with no helium piece the section is absent; the copied text carries the same lines.

- PRO-03 · Inflation seconds and inflated size per layer on the pump, with a per-workshop calibration.
  Problem: no pump-time figure in the 3D editor; the only "bomba" is an equipment label (`components/plan/guirnalda/leyenda-guirnalda.ts`).
  Evidence: BalloonBuilder pump calculator and 2D callouts "28.0 cm (R18: 2.4s)" (`research/balloonbuilder/full-15-pump-seconds-size-callouts-dims.png`).
  Value: the decorator inflates by seconds; it saves a test-and-fail per layer. Overlap: idea 1 (partly 4). Size S for a default table, M if a calibration form is added.
  Acceptance: each layer in the list or sheet shows inflated cm and seconds for the default table; changing the calibration changes the seconds; rounding to 0.1 s is tested.

- PRO-04 · Quote from a Taller scene: materials prefilled from the scene, using the professional quote lines already built.
  Problem: the professional quote is reachable only from the plan (`components/cotizacion/CotizacionProfesional.tsx`); a `/3d` scene cannot be priced. `components/tres-d/` has no quote or budget dialog.
  Evidence: e6f grep (cotiz/presupuesto in tres-d: none); `lib/cotizacion/borrador-profesional.ts` is the reusable draft.
  Value: one flow from design to price. Overlap: partly ideas 5 and 6. Size M.
  Acceptance: from a saved scene, "Cotizar" opens the professional quote with one material line per (product, size, colour) whose totals equal the shopping list; labour and margin start empty; total updates when the scene changes.

- PRO-05 · Three-tier quote (sencilla, estandar, lujosa) from one scene, with surcharges: urgency, outdoor, peak season, and delivery, setup and takedown fees.
  Problem: one price only; no tiers and no surcharge rules in `components/cotizacion/` or `lib/cotizacion/`.
  Evidence: `research/balloonbuilder/notas.md`, section Academy (outdoor +20-40 %, rush +25 % and +50 %, three-tier anchoring).
  Value: consistent quotes and less margin leakage. Overlap: idea 5. Size M.
  Acceptance: the three tiers differ only in material choice and labour lines; rush and outdoor surcharges apply from the event date and place flags and show as separate lines; an event 2 days ahead gets +50 % (tested); tiers are shown side by side in the proposal.

- PRO-06 · Export of the scene as PNG at 3000 px and as a GLB model.
  Problem: the scene can be captured (`components/tres-d/CapturaRender.tsx`) but no GLB export exists (grep glb/gltf in components, lib and app: no hits).
  Value: a proof for the client; GLB for AR viewers. Overlap: ideas 14 and 18. Size M.
  Acceptance: PNG at 3000 px long edge downloads from the Taller; GLB opens in a glTF viewer with the same piece count as the editor; file name carries the scene name; no server call.

- PRO-07 · Inventory of the decorator's own stock (balloons and accessories on hand), with deduction when a scene is marked as built.
  Problem: the shopping list assumes everything is bought. Stock appears only as `leftoverInventory` in the quote (`lib/cotizacion/granel.ts`, `components/cotizacion/MaterialesGranel.tsx`) and in prompts (`lib/ia/guiado/prompt-guiado.ts`); there is no stock store.
  Value: avoids buying twice; shows what is missing for next week. Overlap: none (BalloonBuilder tracks stock only inside layouts). Size L (store, UI, deduction rule).
  Acceptance: add and remove stock per (product, colour, size); marking a scene as built deducts its quantities and never goes below 0 without a warning; purchase = required minus stock; tests for deduction and warning.

- PRO-08 · Approval link for a quote or scene, so the client approves or asks for changes in writing.
  Problem: the approve button exists only for the customer proposal (`components/propuesta/BotonAprobar.tsx`); a decorator's scene or quote cannot be sent for approval.
  Value: closes the sale without a chat; the decorator sees the state. Overlap: none. Size M (reuses the proposal page).
  Acceptance: the link opens a read-only proposal with quote and scene render; approve records date and name; "pedir cambios" adds a comment the decorator sees; the link expires with the quote validity (`vigencia.ts`).

- PRO-09 · Named size profiles for columns and arches in the Taller (champagne, bottle, bowling pin, pencil, taper).
  Problem: layer sizes are set by hand; no named profiles found in `components/tres-d/ParametrosPieza.tsx` (not exhaustively checked).
  Evidence: BalloonBuilder has 13 profiles (`notas.md`, section Columns & Arches app, SIZES). Overlap: idea 9. Size S.
  Acceptance: a profile menu sets a column's layer sizes in one click; at least 5 named profiles; editing a layer after picking a profile renames it "personalizado".

- PRO-10 · Single-balloon paint with a live count per colour in the Taller. Overlap: idea 14. Size M.
  Status: NOT verified on e6f. Check existing paint tools (`components/tres-d/EditorTrazo.tsx`, `PanelPared.tsx`) before building.
  Acceptance (if missing): clicking a balloon sets its colour; per-colour count updates within 100 ms on a 500-balloon scene; undo restores the colour.

- PRO-11 · Recipe card for each inspiration example: count by size, Sempertex code and quantity, dimensions, inflation size; chip filters by occasion and technique.
  Evidence: `research/balloonbuilder/inspiration-3-recipe-cards.jpg`. e6f has `components/guiado/ficha-globo.ts` (per-balloon sheet, not per-example recipe). Overlap: idea 4. Size S.
  Acceptance: every catalogue example shows count by size and code; occasion chip returns only matching examples; counts equal the shopping list for that example.

- PRO-12 · Colour pins on the client's invitation or photo, each giving the nearest Sempertex colour with its ΔE label.
  Evidence: `research/balloonbuilder/color-matcher-1.jpg`. e6f already shows ΔE per candidate (`components/referencia/DetalleTecnicoColores.tsx`) and photo colour reading (`components/tres-d/ControlFotoIA.tsx`). Overlap: idea 13, and idea 2 (ΔE mapping partly built). Size M (pins are the new part).
  Acceptance: dragging a pin updates the swatch and nearest Sempertex with ΔE; up to 3 alternatives per pin; the chosen code appears in the shopping list.

- PRO-13 · Height and width marks on the Taller's view and in the printed sheet.
  Evidence: BalloonBuilder overall dims callouts (`research/balloonbuilder/full-15-pump-seconds-size-callouts-dims.png`). Overlap: idea 8. Size S.
  Acceptance: overall height and width in cm match the bounding box within 1 cm; the marks appear in the sheet from PRO-01.

- PRO-14 · "Plano vs armado" block in the proposal: render beside the real photo, same crop.
  Evidence: `research/balloonbuilder/inspiration-2-plan-vs-built.jpg`; e6f has side-by-side only inside the photo flow. Overlap: idea 19. Size S.
  Acceptance: a proposal with a scene photo shows two panels with the same crop; caption editable; no horizontal scroll at 360 px width.

Out of scope for the pro persona, kept for a later cycle: mosaic module for numbers and letters (idea 16, L) and wall
colour from photo (idea 17, customer-side). The mosaic detection code in e6f is detection only, not a module.
