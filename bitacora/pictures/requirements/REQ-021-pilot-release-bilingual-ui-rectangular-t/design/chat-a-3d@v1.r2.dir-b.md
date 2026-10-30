# Escena junto al chat — SP-12, direction B, revision r2

Status: **draft exploration; unapproved**. Candidate for `chat-a-3d@v1`, revision r2 (reason: plan changed). Owner: David. Scope: SP-12 / R13, exactly `chat-a-3d@v1.r2.behavior.md`. This direction writes only its revision-specific files; it does not create or amend the canonical contract, SPEC, PLAN, sibling designs or production code. Owner choice and plan approval are pending.

## What changed from r1

The r2 brief adds T12.3's test scope (Entusiasta, Master Designer and staff, English cards, new-unsaved-project opening, save, no-match, permission-denied), and the sibling list now includes the finalised `herramientas-chat@v1`, whose tool sidebar wraps `/asistente` (its V5). r2 therefore keeps r1's spatial stance but:

- replaces r1's horizontal route row with the **herramientas-chat@v1 shell**: masthead + 248px tool sidebar with per-role tool lists (Chat current) and the phone «Herramientas · Chat» toggle;
- adds role views (Master Designer, staff, Entusiasta), the **Taller arrival with save** (proyectos@v1 D1 «Guardar proyecto», empty-name error, Guardando…, «Guardado en tu cuenta»), the **unsaved-work guard** reused from herramientas-chat D1 and the **direct-link refusal** reused from herramientas-chat V7;
- uses the product's real restart copy («¿Empezar de nuevo?» / «Se borra esta conversación y vuelves al inicio.», t12 `ConfirmarEmpezarDeNuevo.tsx`) in an AlertDialog;
- replaces a shared-layout claim with a working FLIP scene transfer (the kit runtime remounts the product per view/state, so a Motion `layoutId` across views cannot animate).

## Approach and existing surface

Change the existing normal guided chat at `/asistente` (t12 `src/app/asistente/page.tsx`, `src/components/guiado/VistaGuiada.tsx`; greeting `SALUDO`, «Ideas de decoración» from `CarruselDecoraciones.tsx`, composer `Compositor.tsx`) inside the herramientas-chat@v1 shell. Only the changed area is rearranged: the conversation stays docked at the left of the main column while the recommendation area becomes a scene stage (one enlarged gallery decoration) with a card index of the two or three recommendations. Each card shows preview, name in the session language and the engine's balloon count; «Abrir en el Taller» appears only for accounts with `decoraciones.explorar` and opens `/3d?decoracion=<id>` as a new unsaved project. No new page, catalogue browser, filter, price, plan comparison or upsell.

Preserved: Pictures/Sempertex masthead, Idioma select, account disclosure (with its inherited Planes entry), tool sidebar and its motion, Geist fonts, tokens, rounded papers and pill controls. The Taller is context only (existing tool rail, canvas, panel); its editor and save rules belong to proyectos@v1.

## Thumbnails

Both written before the full TSX and rendered at 1280px:

- **Chosen: candidate 1** — `chat-a-3d@v1.r2.dir-b.html.candidate-1.html`: sidebar | 300px conversation | enlarged stage with a 3-card index below. Recommendations read as peer cards (the product criterion), and conversation, enlarged scene and all three cards fit the first 1280px viewport.
- Candidate 2 — `chat-a-3d@v1.r2.dir-b.html.candidate-2.html`: wide conversation | 360px "scene inspector" with enlarged preview and compact rows. The rows read as a list, not cards, and the open action exists only on the selected item; weaker against the card criterion.

## Why it fits Pictures

Same app as herramientas-chat@v1: identical masthead, sidebar, H1-plus-«Datos de ejemplo» heading, papers and button feedback. The stage reuses the gallery preview language of herramientas-chat V4 (taller-visor ground, illustrative schematic, open-as-new-project) and the Taller arrival mirrors V6/proyectos@v1 («Escena nueva», «Sin guardar todavía», «Guardar proyecto»). Only the recommendation area's hierarchy and its transitions are new.

## Eight axes

| Axis | Rendered expression |
|---|---|
| Concept | Conversation docked beside a spatial scene stage; opening grows the chosen preview into the Taller canvas. |
| Layout | Shell 248px sidebar + main. Main >820px: 300px sticky conversation \| stage + 3-column (2 with two results) card index. 600–820px: 260px \| stage + single-column card rows. <600px: stacked. Container query on the main column. |
| Navigation | Inherited sidebar links (`aria-current`), phone toggle. In-page preview buttons with `aria-pressed`, «Vista actual» text and a spring marker gliding between cards; focus stays on the pressed card. «Abrir en el Taller» on the stage and on every authorised card; «Volver al chat» from the Taller. |
| Typography | Geist Sans 24/20/17/14–15/12–13px; tabular counts; Geist Mono only in the wordmark. |
| Density | One enlarged scene, compact cards with full wrapping names; narrow widths turn cards into rows rather than squeezing. |
| Components | Real Sidebar, Button, Input, Skeleton, Dialog, AlertDialog; native select/details; custom card-preview buttons and labelled SVG previews. |
| Colour | Project tokens only; acento on the primary open/save action, focus and illustrative balloons; error for failures; exito for the saved status. |
| Motion | Opposed docking (−18px / +28px), card seating cascade (+18px, .6deg, 70ms stagger), scene re-seat on selection (+24px, .975), spring selection marker, FLIP scene transfer into the Taller (680/420/200ms). Reduced/Quieto/still: no travel. |

Selector evidence: `chat-a-3d@v1.r2.dir-b.json`; every selector matched a rendered element in the probe below.

## Interaction and motion detail

Easing `cubic-bezier(.16,1,.3,1)` for spatial moves; sidebar and buttons keep the sibling's `cubic-bezier(.23,1,.32,1)` precise cuts (rows −8px, buttons ±1px, 150ms). Profiles: expressive 600ms settle / 70ms stagger, natural 360/35ms, subtle 180/12ms. Selecting a card keeps focus on it, swaps the stage (re-seat keyframe) and announces name · count politely; the selection marker springs (stiffness 260 / damping 26 expressive; 380/34 natural; 520/34 subtle; duration 0 reduced). Opening stores the clicked thumbnail's (or stage preview's) rectangle and, on the Taller mount, animates the canvas from that rectangle to its own (translate + scale, transform only), so the decoration visibly travels from the chat into the workshop. With `prefers-reduced-motion`, «Quieto» or `?still=1` the transfer and all keyframes are skipped and content is final immediately; hidden tabs pause CSS animation. No infinite animation.

Flows shown: two-to-three-message exchange (Cumpleaños → «¿Qué tamaño y qué colores?» → example reply) → «Ideas de decoración» with 2–3 cards → select → open (Master Designer/staff) → Taller «Escena nueva» / «Sin guardar todavía» → «Guardar proyecto» D1 (blank name keeps it open with «Escribe un nombre para el proyecto.»; Guardando…) → «Guardado en tu cuenta». With unsaved Taller work, opening first shows «Tienes cambios sin guardar» (Cancelar / Descartar escena y continuar / Guardar y continuar; Escape returns focus to the invoking card). Entusiasta sees the same cards with no open action and no plan text in the recommendation area; its sidebar lists only Herramientas, Chat, Contador de globos. A direct `/3d?decoracion=…` link without permission shows «No tienes acceso a esta herramienta» / «Tu cuenta no tiene permiso para abrirla.» / «Volver a herramientas», with no decoration data.

## Views, states and dialogs (native selectors)

Vista: Chat · Master Designer; Chat · Personal interno; Chat · Entusiasta; Taller · proyecto nuevo desde el chat; Enlace directo sin permiso. Estado: ready (3), two-results, initial, conversation, loading (skeleton, «Buscando decoraciones…», stop), empty (no match: «No hay coincidencias» + explanation, no cards), error, offline, preview-error (name/count stay), count-error («Conteo no disponible», never zero, opening disabled), opening («Abriendo…»), unavailable, unsaved (Taller has unsaved changes; open triggers the guard), saved (Taller). Diálogo: restart, unsaved guard, first save. Tema light/dark; Movimiento expressive/natural/subtle/Quieto; product Idioma ES/EN.

## Data and language

Names and counts come from t12 `BIBLIOTECA_FABRICA` and `productosDe(item).totalGlobos` (read-only, as in r1): «Arco orgánico con dos columnas y guirnalda» 530, «Pared de globos al fondo y dos columnas» 346, «Techo con tiras y flores colgando» 188. One fixture feeds stage, cards, announcement and Taller panel. Preview SVGs are labelled illustrative mock art, not gallery renders. English names are provisional stand-ins for SP-9 `textos-ingles`; production consumes localized gallery data, never chat-generated names.

## Fixed design system

Tokens copied exactly from t12 `src/app/globals.css` (light/dark), mapped once onto shadcn roles as in herramientas-chat@v1 (background/card → fondo/superficie, primary → acento/sobre-acento, input → texto-tenue, sidebar-* → superficie/superficie-2/borde). Geist Sans/Mono embedded from t12 `.next/static/media`. Radii 32/24/18/999px. No new palette, font or brand.

## Verification (final HTML)

| Check | Actual result |
|---|---|
| Offline build | `components mockup build` exit 0; 748 KB, 2,194 source files, offline. |
| Contrast | `contrast: 158 pairs checked in light and dark, all pass` (exit 0). |
| Rendered audit | Exit 0: 340 renders / 340 planned, 9,348 text measurements, 716 focus stops. |
| Interaction probe | 43/43 PASS: selection updates stage and keeps focus; open carries the identity (/3d?decoracion=escena%3Apared_fondo_columnas) into «Escena nueva / Sin guardar todavía»; blank-name error; save → «Guardado en tu cuenta»; Entusiasta: 3 cards, no «Abrir», no «plan», 3-item sidebar; denied refusal with no cards; guard opens, Escape returns focus, discard opens the right decoration; restart cancel/confirm; two results; count-error disabled without zero; no-match without cards; English names with unchanged counts; all JSON selectors present; zero page errors and zero HTTP(S) requests; phone toggle opens/Escape; no horizontal overflow at 390px. |
| Motion | 12 running animations at 120ms expressive; 0 with `?still=1`; 0 with OS reduced motion; FLIP transfer animates on open (1 animation on `.studio-canvas`) and does not run with `?still=1`. |
| Visual inspection | Screenshots inspected: Master light 1280/1024/768/390, Entusiasta dark 1280, Taller dark 1280, count-error dark 390. A first build showed no accent balloons (nth-child inside `<g>`), a cramped conversation header and a heading focus outline after programmatic focus; all three were fixed before the final audit. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

The first probe run failed because the runtime remounts the product per view/state, which dropped the arrival feedback and made a Motion `layoutId` transfer impossible; feedback and the transfer origin now live in module memory and the transfer is a FLIP. Two later probe failures were the probe's own selectors colliding with the Diálogo option labels. Screenshots and probes stayed in `/tmp`. These checks validate this planning artifact only, not ranking, gallery fidelity, permissions, routing or saving.

## Questions

- Q1 — If the engine count fails for one recommendation, omit the card until it recovers, or show it as «Conteo no disponible» with opening disabled (this draft)?
- Q2 — Who supplies the English gallery names (SP-9), and what shows when a localized name is missing?
- Q3 — Which recommendation is enlarged first: the recommender's first-ranked one (this draft) or none until the person picks?
- Q4 — Should the stage and every card both carry «Abrir en el Taller» (this draft), or only the enlarged stage?
- Q5 — For staff, does opening from the chat behave exactly like Master Designer (this draft), with no extra owner/account context?

Assumptions: selection is presentational and changes no ranking; opening never overwrites the open project; save behaviour, autosave and conflicts are proyectos@v1's; the guard and refusal are herramientas-chat@v1's.
