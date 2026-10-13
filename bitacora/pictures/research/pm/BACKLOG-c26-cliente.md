## Delta c26 — PM customer (2026-10-11)

Sources read: research/pm/BACKLOG.md (c0, c8, c20), juez/JUEZ-ASISTENTE-2026-10-11.md (14 screenshots listed, not re-opened),
ciclo/STATE.md, ciclo/CRITICO-c24.md, ciclo/SIMULACRO-ROLLBACK-2026-10-11.md. `git fetch` then `origin/main` log -50: head 65edd83b.
The judge-fix task (e7x) is NOT on origin/main yet, so the fix is still open. Code checked with `git grep` / `git show` on
origin/main 65edd83b (no checkout, no writes). Production pulse: `npm run prod:pulso -- --horas 24` (read-only, no paid calls),
run 2026-10-11 11:01Z, verdict "sano". Market: 3 WebSearch (LatAm, Spanish), small sample, not verified line by line.

Caveat on the pulse: its filter removes only `+local` and `anthropic` rows. The owner's own browser tests on prod are NOT
removed, so the 39 "cliente" turns in 24 h are not proof of customers. None of them was rated (0 of 39). The pulse does not
sum cost (`coste n/d`); spend per turn must be read from ai_call_log.

Pulse 24 h (own excluded): feedback cliente 39 turnos, 0 calificados, deshechos 0; taller 3 turnos, 1 deshecho. plan_audit (includes
own): PLAN_3D_CREADO 31, PLAN_3D_EDITADO 22, COTIZACION_IDEA_3D 13, PLAN_3D_EDICION_RECHAZADA 4. Errors 5xx 0; IA errors 1 of 19
embedding calls (python:/internal/v1/embed). /login 200; Vercel Ready 11 min before the run.

### Status of earlier items (CUS-xx / NC-xx), with commit evidence

| Item | Status | Evidence |
|---|---|---|
| CUS-01 3D still on plan card | PART | Live for everyone since D-039 (b5f32b06; guiada_motor=3d). Drill and judge drew the 3D plan. WebGL fallback and legend=BOM not verified. |
| CUS-02 card count = quote | OPEN | Judge D2: card 101/102, plan and quote 115. In the fix task, not on main. |
| CUS-03 18 structures + aviso | DONE | 34f6fddf (pushed e4216c98): 11 built, 3 with aviso, 4 Python with «La vista 3D todavía no dibuja…». |
| CUS-04 honesty tests | DONE | eb17544e (21 forced-failure cases, wired in checks.yml). |
| CUS-05 burgundy 915 | OPEN | P-027 open; no owner decision recorded. |
| CUS-06 arch inflation | DONE (ruling) | D-032 Q1: keep 5 quartets/m. |
| CUS-07 density sign-off | OPEN | No captures or sign-off on main. |
| CUS-08 voice | PART | components/voz and VOZ_ENABLED in code (c4 says live); owner has not confirmed the flag. |
| CUS-09 edit ops | PART | Live in judge run (size, colour, 1.5–2 s). The "no op adds geometry outside the list" test not found. |
| CUS-10 lazy 3D chunk, 4G | OPEN | Not measured. |
| CUS-11 photo from same geometry | PART | 9f8687a7 (Kontext resume P-038). Never scored: judge did not click «Ver cómo quedaría» (paid). |
| CUS-12 rating per AI turn | PART | 34f6fddf / e4216c98 / 95a8ad57: one POST per turn. 0 ratings in 24 h. Judge D8: widget still sits above reply chips. |
| CUS-13 quote-request fields, response window | OPEN | Confirmed: «Elegir este decorador» only adds a chat line (VistaGuiada.tsx:1573–1595). No form, no response-time copy. |
| CUS-14 spares per colour | DONE | 34f6fddf (2 tests); D-038 capped spare rule 9550e897. |
| NC-1 plan creation with Python down | PART | 3D-flag path builds plans without Python (drill: POST /guiada/motor/plan 200). Flag-read timeout fixed 302d6e3d. Kill-on path still goes via Python; no Python-down test. |
| NC-2 reference relevance (theme) | OPEN | Judge D6: dinosaur party gets 2 ideas, one tagged «Parecida». No commit. |
| NC-3 server audit of guided-3D | DONE | 5e61dde6 (plan_audit_log via after()). Pulse: 31 PLAN_3D_CREADO in 24 h. |
| NC-4 rollback drill | DONE | SIMULACRO-ROLLBACK-2026-10-11: all PASS, flips 0–48 s, open plan keeps its data. «Recalcular mi plan» click not run (paid chat). |
| NC-5 one rating POST per turn | DONE (POST count) | 34f6fddf; layout still open (judge D8). |
| NC-6 CRUD by chat + undo identity | PART | Corpus 8 → 118 phrases (9b51c719, 0849a074, 65edd83b). P-042 undo is not identity (CRITICO-c24). |

Count: DONE 7 (CUS-03, 04, 06, 14; NC-3, 4, 5) · PART 7 (CUS-01, 08, 09, 11, 12; NC-1, 6) · OPEN 6 (CUS-02, 05, 07, 10, 13; NC-2).

### What comes after the judge fix (not re-listed here)

The fix task covers count parity, the honest edit banner, card price, deterministic answers and chips. After it, the next customer
step is the decision path (a visitor who wants to hire, send or share), then the go-live gate. Two judge defects sit outside the
fix task: D6 (theme coverage, = NC-2, open) and D7 (compare two ideas, = CUS-21 below).

### Market sample (small, 3 searches, LatAm)

- Spanish quote forms ask for name, WhatsApp, email, date (firm or approximate), venue and guests.
- Deposits of 20–50 % hold the date. One English form says the request holds nothing until the deposit arrives.
- A Mexican marketplace lets the customer compare up to four quotes free (cronoshare.com.mx, Azcapotzalco page).
- A Peruvian shop says quotes lost in chat and double-booked dates are the usual failure (kom.pe, reference only).
- Colombia: no online quote service for balloon decoration found (encarguelo.com is a product shop).
- Sources (search hits, claims not individually verified): cronoshare.com.mx, habitissimo.com.mx, cosmos.com.mx, kom.pe,
  bodas.net, fixando.es, tally.so/r/MeMPqp, form.jotform.com/223202631511338.

### Ranked list (new IDs CUS-15 to CUS-22; value first, then size)

### CUS-15 · The decorator choice reaches a person · size M · value H (contact)
- Problem: «Elegir este decorador» only adds a chat line. No form, no WhatsApp and no email goes to the decorator or the owner.
  The four decorators (Bogotá, Medellín, Cali, Barranquilla) all have `contacto: null`.
- Evidence: VistaGuiada.tsx:1573–1595 (solicitarProveedor: chat line + registrarAccion only); registro-guiado.ts:115 (journey log to
  /api/registro-cliente); src/lib/biblioteca-sempertex/proveedores.json: 13 records, `contacto` non-null 0/13; no lead or contact route under src/app/api.
- Customer value: a mother who has chosen a decorator can actually hire one.
- Acceptance: choosing a decorator opens a short form (name, WhatsApp, event date, city, guests; budget optional) or a prefilled
  wa.me link to that decorator's number. Each submit writes one lead row and sends one notice to the owner within 5 min. A decorator
  without a contact is not shown. Test with the four decorators: one lead row and one notice each.
- Owner question: the four WhatsApp numbers, and consent to receive leads.

### CUS-16 · WhatsApp handoff from the plan and the quote · size S/M · value H (contact)
- Problem: no WhatsApp path exists in customer code (`git grep -i "wa\.me|whatsapp"` on origin/main src: 0 files). Buyers in this market
  send plans and dates by WhatsApp; the quote is a screen they cannot send.
- Evidence: the git grep above; market sample (quote forms ask for WhatsApp as the contact field).
- Customer value: family and decorator see the same plan and total without retyping.
- Acceptance: «Enviar por WhatsApp» on the plan card and the quote opens a wa.me link with idea title, balloon count, and the quote
  total (equal to the card total, CUS-02 test), plus date and city if given. No internal terms (no «motor», «cuartetos», «Python»).
  Works on iOS Safari and Android Chrome. The link carries only what the customer typed.

### CUS-19 · Go-live gate: what must be true before the owner sends real customers · size M (decisions + checks) · value H
- Problem: no real customer has arrived. Access is one shared password; there are no accounts. There is no privacy or terms page,
  although visitors upload venue photos and chat text is stored. Lead delivery does not exist (CUS-15). No analytics package.
  Spend caps were per instance until 392fff68 (migration 035 applied 04:37); no real-traffic test yet.
- Evidence: src/app/login/LoginForm.tsx (one password field); STATE D-032 Q5 (shared password); owner question 5 (REQ-004 accounts,
  open); package.json has no analytics or speed-insights package; src/app/layout.tsx has only the theme script; no legal route under
  src/app (ls-tree check); 392fff68 and STATE spend table.
- Customer value: the first real customers are not lost or misled.
- Acceptance: one go-live checklist with evidence on each line.
  (a) Access model decided (open with rate limits, invite, or shared password), recorded in DECISIONS.
  (b) Privacy and terms pages live and linked. The photo and retention wording is the owner's call; we do not write legal text.
  (c) CUS-15 lead test passes on prod with a test lead.
  (d) Durable caps tested on prod with two instances: cap reached gives «No pude: límite…».
  (e) Customer judge ≥ 8 on the journey after the fix task.
  (f) Rollback drill recorded (done 2026-10-11, SIMULACRO).
  (g) Funnel readable (CUS-20).
  (h) Owner response time written in the customer confirmation.

### CUS-18 · Trust on the quote: what the price includes and what the deposit does · size S · value H (trust)
- Problem: the quote says «IVA incluido, sin montaje» but gives no montaje or retiro line, no deposit meaning, no cancellation rule and
  no response window. Market: a 20–50 % deposit holds the date; a request alone holds nothing.
- Evidence: judge (b), quote footer text; BACKLOG CUS-13 (response window open); no terms or cancellation route under src/app.
- Customer value: no surprise at the decorator's door, and a clear reason to pay the deposit.
- Acceptance: the quote shows «Incluye» and «No incluye» (montaje, retiro, entrega, helio) in customer words. Beside the total it
  states what the deposit does and the cancellation rule the owner picks (recorded as a D-number). /terminos and /privacidad exist
  and are linked from /asistente. A test checks the strings and a 200 on both routes.

### CUS-17 · Share the plan with family (read-only link) · size M · value H (sharing)
- Problem: no share function. A plan lives in one browser session: the judge saw a saved plan opened from another session return 409 on edit.
  A family decision needs one link.
- Evidence: git grep for navigator.share / copy-link in src/components/guiado: no hits; judge journey 1 («replayed from ANOTHER session gets 409»).
- Customer value: the mother gets opinions from the family without screenshots.
- Acceptance: «Compartir plan» creates a link that opens read-only in a clean browser: same idea, 3D still, balloon count and quote total
  as the source plan; no edit controls; expires in 30 days; the payload holds the plan spec only (no chat text, no contact data).
  Depends on the access model in CUS-19.

### CUS-20 · Owner funnel from the journey log · size S · value M (measurement)
- Problem: the journey is logged to /api/registro-cliente but nobody reads it as a funnel. The owner cannot see where mothers drop:
  landing → idea → plan → quote → decorator → WhatsApp.
- Evidence: registro-guiado.ts:115; no analytics package; the pulse reads ai_feedback and plan_audit_log only.
- Customer value: indirect, but it tells the owner what to fix before paid traffic.
- Acceptance: `npm run funnel` (read-only, aggregates only, excludes +local) prints per day: conversations started, idea chosen, plan created,
  quote shown, decorator chosen, WhatsApp sent (after CUS-16), contact sent (after CUS-15). No customer text printed. Runs on prod.

### CUS-21 · Compare two ideas side by side · size M · value M/H
- Problem: after one idea is chosen, the other cards lose their button and the chips vanish. No compare, no swap (judge D7).
  Journey 2 (XV, six ideas) cannot compare.
- Evidence: judge (a) and D7; judge journey 2.
- Customer value: the mother chooses between two real options, each with price and count.
- Acceptance: «Comparar» on two ideas shows two columns (balloons, price from the same pricer as the card) and a «Cambiar de idea» that keeps
  the current plan until confirmed. Test: switching keeps the plan total; no chip disappears.

### CUS-22 · Score the paid differentiator on prod: «Ver cómo quedaría» · size S · value H
- Problem: the photo is the main differentiator and has never been scored. The judge never clicked «Ver cómo quedaría» or «Recalcular mi plan»
  (paid routes).
- Evidence: judge «Never clicked» list; CUS-11 PART; FLUX about US$0.08 per render (BACKLOG c20, NP-3).
- Customer value: the photo the mother keeps shows the count and colours she was quoted.
- Acceptance: one judged prod run under a logged cap of US$0.25 (about three renders). Each photo scored ≥ 7 for count and colour against
  the plan; photo count within ±10 % of the plan; cost in ai_call_log; no render without a token from the plan.

### Ranking
1. CUS-15 decorator choice reaches a person (H, M)
2. CUS-16 WhatsApp handoff (H, S/M)
3. CUS-19 go-live gate (H, M decisions)
4. CUS-18 trust on the quote (H, S)
5. CUS-17 share the plan with family (H, M)
6. CUS-20 owner funnel (M, S)
7. CUS-21 compare two ideas (M/H, M)
8. CUS-22 score the paid photo on prod (H, S)

### Open owner questions (new)
(1) Four decorator WhatsApp numbers and consent to receive leads (CUS-15). (2) Access model: shared password or open with limits (CUS-19).
(3) Deposit and cancellation rule (CUS-18). (4) Response window (CUS-13). (5) Where the lead notice goes: email or WhatsApp (CUS-15).
