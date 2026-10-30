---
contract: chat-a-3d
version: 1
status: draft
subplan: SP-12
requirements: [R13]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: b
name: Escena junto al chat
source_revision: r1
source_behavior: chat-a-3d@v1.r1.behavior.md
current_behavior: chat-a-3d@v1.r1.chosen.behavior.md
source: chat-a-3d@v1.r1.dir-b.tsx
plan_revision: 17
---

# chat-a-3d@v1 — Escena junto al chat

## 1. Identity and traceability

Canonical planning **draft; not approved for implementation**. The owner chose direction b, “Escena junto al chat” (revision r1), in the web comparison (`drafts.json` selected SHA-256 `bf3148b1…` = `chat-a-3d@v1.r1.dir-b.html`). That choice authorizes this finalization only; it does not approve this contract, SP-12 or the plan. Version 1; no approved predecessor exists, so no consumer migration. This task writes only `design/chat-a-3d@v1.md` and `design/chat-a-3d@v1.html`. No exploration, history, SPEC, PLAN, production file, contract changelog or preview was changed.

Scope: REQ-021 / M4 / SP-12 “Normal chat recommends ready-made 3D decorations”, from SPEC (round 16; SP-12 verification row), PLAN.json revision 17, the direction's brief `chat-a-3d@v1.r1.behavior.md`, the current brief `chat-a-3d@v1.r1.chosen.behavior.md` and the chosen r1 direction-b Markdown, JSON, TSX and HTML. This contract specifies the recommendation area of the existing guided chat at `/asistente`, the arrival in the Taller as a new unsaved scene and the refusal of a direct link without permission. It does not specify the recommender, the model tool, streaming sanitation, gallery metadata, server permissions or saving, which belong to T12.2, SP-7, SP-1 and SP-4.

| Requirement / criterion | Contract coverage | Consuming tasks |
|---|---|---|
| R13 — the normal chat connects to the 3D workshop | V1, V3, F1–F3, UI-AC-02–09, 17 | T12.3; review T12.5 |
| Cards with preview, name in the session's language and balloon count, to every plan | V1/V2 cards, F1, F4, UI-AC-06, 15, 16 | T12.3; T12.5 |
| «Abrir en el Taller» only with `decoraciones.explorar`, opens `/3d?decoracion=<id>` as a new project; others see no button and no plan mention | V1 vs V2, V3, V4, F2, F5, UI-AC-07, 09, 17, 18 | T12.3; T12.5 |
| SPEC SP-12 check: no match gives an explanation, never invented recommendations | `empty` state, F1, UI-AC-11 | T12.3 |

PLAN consumers: SP-12 `ui.contract=chat-a-3d`, `ui.version=1`, `design_task=T12.1`, `visual_review_task=T12.5`. T12.1 copies only the owner-approved artifact. T12.3 implements `TarjetaRecomendacion3D.tsx` and `textos/recomendaciones-3d.ts` against it. T12.4 (browser e2e) and T12.6 (audit) verify behaviour, not this visual contract.

**Plan change folded in (current brief vs the direction's brief).** The only delta is T12.3's objective: it now authors `scripts/test/test-integracion-recomendaciones-3d.ts` (SP-12 and CG-12 modes, deterministic provider fixtures, local REQ-021 database, no paid AI calls) and tests Entusiasta, Master Designer and staff, English cards, new-unsaved-project opening, save, no-match and permission-denied cases through real entrypoints. The harness itself is engineering work; its UI consequence is that every named case must have a defined, observable screen. The table below maps each case to this contract; changes 3–5 below were needed to make the save, no-match and permission-denied cases observable.

| T12.3 test case | Where it is specified |
|---|---|
| Entusiasta (also Designer, Designer Plus) | V2, §5 account table, UI-AC-07, 08 |
| Master Designer and staff (Empleado interno, Administrador) | V1, §5 account table, UI-AC-02, 09 |
| English cards | F4, §7 copy rules, UI-AC-15 |
| New-unsaved-project opening | F2, V3, UI-AC-09 |
| Save | F2 step 5, V3 «Guardar proyecto» → proyectos@v1 D1, UI-AC-10 |
| No-match | `empty` state, UI-AC-11 |
| Permission denied | V2 (no button, no route), V4 direct-link refusal, UI-AC-07, 08, 18 |

**Changes relative to the chosen r1 exploration.** Composition, navigation pattern, tokens, typography and motion are preserved. The canonical HTML was rebuilt with the current offline builder from a copy of the r1 TSX with these changes (patched source and diff kept as delegation evidence: `.state/delegations/D-20261029-163215-a3ef/chat-a-3d@v1.final.{tsx,diff}`):

1. *Account-named views (delta).* The Vista inspector names the accounts: “Chat · Master y personal”, “Chat · Entusiasta–Designer Plus”, “Taller · escena sin guardar”, “Enlace sin permiso”. Inspector chrome only.
2. *Taller 3D route shown to accounts without the explorer (verified defect).* r1 rendered the «Taller 3D» route link in the recommendations-only view. Approved `herramientas-chat@v1` renders only granted tools (Taller 3D is Master Designer/staff). The link is now absent in V2 and V4.
3. *Save entry in the arrival (delta: save).* V3 adds the existing proyectos@v1 «Guardar proyecto» primary action beside «Volver al chat». It stands for proyectos@v1 D1 (first named save); the mockup only reports that hand-off.
4. *Direct-link refusal (delta: permission denied).* New context view V4 reuses `herramientas-chat@v1` V7 copy for `/3d?decoracion=<id>` opened without `decoraciones.explorar`.
5. *No-match without explanation (delta: no-match; SPEC SP-12 check).* r1's `empty` body repeated its own button label (“Cuéntame qué quieres cambiar…”). The body now explains: “Ninguna decoración de la galería encaja con lo que describiste. Cambia el tamaño, los colores o la ocasión.”
6. *Error body repeated the action (verified defect).* r1's `error` body read “Intentar de nuevo”, the same as its button. It now says “La conversación se conserva.”
7. *Deep-link evidence lost on arrival (verified defect).* r1's note says the arrival displays the encoded route; the view change remounted the screen and dropped it. The route line now survives the transition.
8. Footer provenance reads “Contrato borrador · Sin aprobación”. The title bar keeps “Mockup · Chat · Taller 3D · B”; both are provenance chrome, not product copy.

No other source change. Read-only product evidence used by the exploration: t12 `src/app/asistente/page.tsx`, `src/components/guiado/{VistaGuiada,CarruselDecoraciones,Compositor,ConfirmarEmpezarDeNuevo}.tsx`, `src/components/ui/shell/{CabeceraApp,MenuApp}.tsx`, `src/app/globals.css`, `src/app/layout.tsx`; asesor `src/components/asesor/ChatView.tsx` (not the target).

## 2. Purpose and users

Users: signed-in Usuario accounts on Entusiasta, Designer, Designer Plus or Master Designer, and staff (Empleado interno, Administrador). Only Master Designer and staff hold `decoraciones.explorar`.

| View | User goal | Observable success |
|---|---|---|
| V1 Chat with opening (`/asistente`, Master Designer/staff) | Describe the event in two or three messages and start from a ready-made decoration | Two or three cards with preview, name and engine count; one enlarged; «Abrir en el Taller» on the enlarged card and on every card. |
| V2 Chat, recommendations only (`/asistente`, Entusiasta/Designer/Designer Plus) | Same description, see what fits | Identical cards and selection, no open action, no Taller route, no plan wording in the recommendation area. |
| V3 Taller arrival (`/3d?decoracion=<id>`, context) | Continue in the workshop from the chosen decoration | “Escena nueva / Sin guardar todavía” with that decoration's name and count; «Guardar proyecto» leads to the proyectos@v1 first save. |
| V4 Direct link without permission (context) | Understand that the link cannot be opened | Refusal without decoration data and without naming a plan; «Volver a herramientas». |

## 3. Information architecture and hierarchy

Global shell, unchanged from siblings: Pictures/Sempertex masthead (ring-and-dot mark, “Pictures”, Geist Mono “Sempertex”), Idioma select, «Mi cuenta» disclosure → H1 row (“Asistente de decoración” + «Empezar de nuevo») → horizontal route rule (Chat, Taller 3D only with the explorer, Proyectos) → content → footer. See Q1 about the SP-7 tool sidebar.

Content of V1/V2 at ≥1100px: **conversation column** (left, 280–340px, sticky) | **recommendation area** (right, flexible).

- Conversation: head “Chat” → thread (assistant greeting and “¿Qué vas a celebrar?”, user reply, “¿Qué tamaño y qué colores?”, user reply, answer line “Ideas de decoración” or the state title) → composer (label, optional suggestion chip, input, send/stop).
- Recommendation area: heading “Ideas de decoración” + count line (“3 decoraciones”) → **scene stage** (the largest object: enlarged preview, then name 20px + “<n> globos”, then «Abrir en el Taller» with the explorer) → **preview index** of compact cards (preview, full name, count, “Vista actual”/“Ver escena”, card «Abrir en el Taller» with the explorer).
- Primary information: the selected decoration's preview, name and count. Secondary: the other cards. Supporting: count line, state notices.

Progressive disclosure: the stage and index appear only after the brief is complete; before that a neutral placeholder stands in. Selecting a card replaces the enlarged scene in place; it never navigates or changes ranking. Rationale: the short conversation and the inspected decoration remain side by side (direction concept).

## 4. Design system and visual language

Fixed project system; no new palette, font or brand. Tokens (light / dark), from t12 `globals.css` and identical to sibling contracts: `--fondo` #faf9fc/#0b0c10; `--superficie` #ffffff/#16181f; `--superficie-suave` #faf8fd/#1c1e26; `--superficie-2` #efe9f8/#242733; `--borde` #e3daef/#383c48; `--borde-suave` #efe9f8/#2a2d38; `--texto` #1c1425/#f4f5f7; `--texto-suave` #6b6178/#9aa1ad; `--texto-tenue` #766c85/#8a91a0; `--acento` #6d3fe0/#9479ff; `--acento-hover` #5530b8/#a58dff; `--sobre-acento` #ffffff/#120b24; `--error` #b23a45/#ff979f; `--error-suave` #ffeaec/#43252a; `--taller-visor` #ebe7f1/#1a1722; `--taller-panel` #faf9fc/#16131d. shadcn roles map once per theme: background → fondo; card/popover/sidebar → superficie; foreground → texto; primary/primary-foreground → acento/sobre-acento; secondary/muted/accent → superficie-2; muted-foreground → texto-suave; input → texto-tenue (control edge ≥3:1); border → borde; ring → acento; destructive → error.

Typography: Geist Sans (local WOFF2) body 15px/1.5; H1 24px/600; selected decoration name 20px/600; panel headings 18px/600; thread and stage meta 14px; card name 14px/600 (15px on phone); metadata 12–13px. Counts use tabular figures. Geist Mono only for the inherited “Sempertex” mark. Radii: panels 32px, cards/insets 24px, fields 18px, pills/buttons 999px. Padding 24px desktop, 20px phone. Icons: lucide 18px (15px inside cards), decorative.

Colour use: accent only on the enlarged «Abrir en el Taller», send, «Guardar proyecto» and focus. Card «Abrir en el Taller» is outline. Selected card: `--texto-tenue` border on `--superficie-suave`; route current item: `--texto` with a 3px `--texto` underline (neutral). Error icons use `--error`; failure is always stated in words.

Focus: 3px `--acento` outline, 4px offset on every interactive element; H1 takes programmatic focus (tabindex −1) after view changes.

Components (`source:id variant state`, import path):

| Component | Use | Import |
|---|---|---|
| `shadcn:button default ready/hover/focus/pressed/disabled/busy` | Enlarged «Abrir en el Taller» (busy “Abriendo…”), send, «Guardar proyecto», dialog confirm | `@/components/ui/button` |
| `shadcn:button outline ready/hover/focus/pressed/disabled` | Card «Abrir en el Taller», «Empezar de nuevo», «Intentar de nuevo», «Volver a las recomendaciones», «Volver al chat», «Volver a herramientas», stop, suggestion chip, Cancelar | `@/components/ui/button` |
| `shadcn:input text empty/filled/focus` | Composer, labelled | `@/components/ui/input` |
| `shadcn:skeleton scene loading` | Reserved preview/name/count geometry | `@/components/ui/skeleton` |
| `shadcn:dialog restart open/closed` (installed Animate UI/Base UI implementation) | D1 restart confirmation | `@/components/ui/dialog` |
| `custom:scene-stage selected ready/preview-error/count-error/opening` | Enlarged preview + name/count + primary action | semantic `article` + tokens |
| `custom:recommendation-card index unselected/selected/focus/disabled-open` | Card with `custom:card-preview` native button (`aria-pressed`) and optional open action | semantic `article`/`button` |
| `custom:scene-preview svg illustrative` | Mock previews only; production uses the gallery's own preview image | inline SVG |
| `custom:status-box alert` | count-error notice, V4 refusal | semantic HTML |
| `custom:empty-stage placeholder/status/alert` | initial, conversation, empty, error, offline, unavailable | semantic HTML |
| `native:details account open/closed`, `native:select language es/en` | Inherited shell | native |
| `kit:planning-controls view/state/scene/theme/motion` | Mockup inspector, outside the product | `@kit/mockup` |

Motion (direction b, “opposed spatial docking”; transform only, content always readable): `.conversation` docks from x −18px, `.scene-stage` from x +26px, easing cubic-bezier(.16,1,.3,1); `.recommendation-card` seats from y +16px, rotate .6deg, overshoot to −2px, 65ms stagger; a newly selected scene (`.scene-object`) enters from x +24px, scale .975; `.status-box` enters from x +8px; card preview lifts 3px on hover; buttons scale 1.025 hover / .965 press, icons travel 2px. Profiles: expressive 580ms entrance / 180ms controls / 65ms stagger; natural 360/140/35; subtle 180/100/12. No infinite animation. OS reduced motion, «Quieto» and `?still=1` remove all travel and transitions; hidden tabs pause animation.

## 5. Navigation and interaction model

- **Entry:** `/asistente`, through the shell route row (or the SP-7 tool sidebar if Q1 resolves so). The chat flow and composer are the existing ones.
- **Account gating (UI only; the server guard is unchanged):**

| Account | Cards | «Abrir en el Taller» | Taller 3D route | `/3d?decoracion=<id>` |
|---|---|---|---|---|
| Entusiasta, Designer, Designer Plus | Yes, identical | Absent (not disabled, not replaced) | Absent | Refused → V4 |
| Master Designer, Empleado interno, Administrador | Yes | On the enlarged card and every card | Present | Opens V3 |

- **Selection:** each card's preview button selects it; focus stays on that button; `aria-pressed` and the text “Vista actual” mark it; the enlarged scene, name and count change; a polite live region announces “<name> · <n> globos”.
- **Open:** any authorized open action navigates to `/3d?decoracion=<id>` with that card's id, opens V3 as a new unsaved scene and focuses its H1. A previously open project keeps its identity (proyectos@v1). While opening, the enlarged action reads “Abriendo…” and every open action is disabled.
- **Arrival (V3):** «Volver al chat» returns to the recommendations; «Guardar proyecto» opens proyectos@v1 D1.
- **Refusal (V4):** «Volver a herramientas» → `/` (herramientas-chat@v1 V1). The Chat route remains.
- **Restart:** «Empezar de nuevo» (disabled in `initial`) opens D1; Cancelar/Escape keep the conversation and return focus to the invoker; confirming returns to `initial`.
- **Account menu and Proyectos route:** inherited shell context, not redesigned.

## 6. Flows

**F1 — Describe the event and get recommendations (every plan).** Greeting and “¿Qué vas a celebrar?” (`initial`; suggestion «Cumpleaños») → user reply → “¿Qué tamaño y qué colores?” (`conversation`) → user reply → `loading` (“Buscando decoraciones…”, skeleton, send becomes Detener; composer stays writable) → `ready` (three) or `two-results` (two; no empty third slot). At most three customer messages before cards appear. No match → `empty` with the explanation and «Cuéntame qué quieres cambiar…» focusing the composer; never a weak or invented card. Failure → `error`/`offline` with retry; the conversation is kept.

**F2 — Open and save (Master Designer, staff).** From `ready`, optionally select another card → «Abrir en el Taller» (enlarged or card) → `opening` → V3: H1 “Taller 3D”, “Escena nueva”, “Sin guardar todavía”, the decoration's preview, name and count → «Guardar proyecto» → proyectos@v1 D1 (name, Guardando…, “Guardado en tu cuenta” only after server confirmation; failure keeps the scene). Unknown or withdrawn id → `unavailable`, no substitute.

**F3 — Recommendations only (Entusiasta, Designer, Designer Plus).** Same as F1. Cards, selection and counts are identical; no open action, no Taller route, no upgrade prompt, no plan name in the recommendation area.

**F4 — English session.** With English selected, card names come from the gallery's English texts (SP-9 `textos-ingles`); a decoration without English text shows its Spanish name. Counts are identical in both languages; the chat never translates or invents names.

**F5 — Direct link without permission.** An account without `decoraciones.explorar` requests `/3d?decoracion=<id>` → V4: “No tienes acceso a esta herramienta”, “Tu cuenta no tiene permiso para abrirla.”, «Volver a herramientas». No decoration name, preview or count; no plan name.

**F6 — Partial data recovery.** Preview fails → `preview-error` (name/count stay, retry). Count fails → `count-error` (“Conteo no disponible”, never zero; opening disabled; retry) — see Q2.

**D1 — Restart.** Title «Empezar de nuevo», description “Se borrará esta conversación.”, actions Cancelar / Empezar de nuevo (existing `ConfirmarEmpezarDeNuevo`).

## 7. View specifications

| View | Structure and content | Actions | Responsive |
|---|---|---|---|
| V1 Chat with opening | §3 order. Stage: preview (16:7-ish, `--superficie-suave`), name h3 20px, “<n> globos” with the number bold, primary «Abrir en el Taller» (accessible name “Abrir en el Taller: <name>”). Index: three cards (preview 86px tall, h3 name, “<n> globos”, “Ver escena ↗”/“Vista actual ✓”, outline «Abrir en el Taller»). | Select, open, send/stop, suggestion, restart | §9 |
| V2 Recommendations only | V1 without any open action and without the Taller 3D route. Cards keep the same height rhythm; nothing replaces the button. | Select, send/stop, restart | §9 |
| V3 Taller arrival (context) | H1 “Taller 3D”; route Taller 3D current; studio panel: header “Escena nueva” / “Sin guardar todavía” + «Volver al chat», «Guardar proyecto»; body: rail, `--taller-visor` canvas with the decoration, inspector “Escena” / name / “<n> globos”. Editor itself is proyectos@v1/taller contracts, not redesigned here. | Volver al chat, Guardar proyecto | Inspector hidden below 1100px; rail hidden below 640px; actions wrap |
| V4 Direct-link refusal (context) | H1 “Taller 3D”; route without Taller 3D; alert box (max 720px): h2 “No tienes acceso a esta herramienta”, “Tu cuenta no tiene permiso para abrirla.”, «Volver a herramientas». | Volver a herramientas | Same at all widths |

Copy rules: Spanish source strings in `src/components/guiado/textos/recomendaciones-3d.ts` with English counterparts (SP-10). Decoration names and counts come only from the gallery (`galeria-index`) and the engine (`productosDe(item).totalGlobos`); the fixture's three decorations (Arco orgánico con dos columnas y guirnalda 530; Pared de globos al fondo y dos columnas 346; Techo con tiras y flores colgando 188) are a read-only snapshot used as illustrative data and must not ship. Their English names in the artifact are provisional layout translations; production uses SP-9 texts. The SVG previews are illustrative; production shows the gallery's preview image. User replies (“Cumpleaños”, “3 × 2,4 m · rosa y blanco”) are example data. Strings prefixed “Mockup ·”, “Datos de ejemplo” and the inspector labels are simulation chrome. Units stay cm/m.

## 8. States

Inspector `state` applies to V1/V2; V3 and V4 ignore it. Dialog `scene=restart` reaches D1 from V1/V2.

| State | What appears / can be done / recovery |
|---|---|
| `ready` | Three cards; first enlarged; selection in place. |
| `two-results` | Two cards, same hierarchy, no third placeholder. |
| `initial` | Greeting, “¿Qué vas a celebrar?”, chip «Cumpleaños»; recommendation area shows “Decoraciones Sempertex” placeholder; restart disabled. |
| `conversation` | First reply and the size/colour question; placeholder invites the reply; no card. |
| `loading` | Skeleton of preview/name/count, “Buscando decoraciones…”, `aria-busy`; composer writable; Detener replaces send. |
| `empty` (no match) | “No hay coincidencias” + “Ninguna decoración de la galería encaja con lo que describiste. Cambia el tamaño, los colores o la ocasión.” + «Cuéntame qué quieres cambiar…» (focuses composer). No cards. |
| `error` | Alert “No pudimos cargar las decoraciones” + “La conversación se conserva.” + «Intentar de nuevo». |
| `offline` | Alert “Sin conexión” + “Revisa tu conexión e intenta de nuevo.” + «Intentar de nuevo»; earlier messages kept. |
| `preview-error` | Enlarged preview replaced by “Vista previa no disponible” + «Intentar de nuevo»; name, count and open stay. |
| `count-error` | Alert “No pudimos cargar el conteo de globos.” + retry; every count reads “Conteo no disponible”, never 0; open actions disabled (Q2). |
| `opening` | Enlarged action “Abriendo…”, all open actions disabled. |
| `unavailable` | Alert “Decoración no disponible” + “Vuelve a las recomendaciones.” + «Volver a las recomendaciones»; no replacement name. |
| permission-denied | V2 (no action) for the chat; V4 for a direct link. Not an error state inside the chat. |
| success (open) | V3 new unsaved scene. Save success/failure is proyectos@v1. |

Inapplicable: validation errors (an empty composer only disables send); stale data (each answer is a fresh tool result); disabled open action for a lacking permission (the action is absent by rule).

## 9. Responsive behavior

Supported range 360px and up; checked at 1280, 768 and 390px.

- **≥1100px:** 40px gutters; conversation 280–340px sticky beside the recommendation area; index in three columns below the stage.
- **840–1099px:** 24px gutters; conversation 280px beside the area; index becomes one column of horizontal rows (80px preview | name/count/label | open action ≤140px); stage info stacks name above action.
- **640–839px:** conversation above the area (not sticky; thread replies in two columns); index three columns; stage info in one row.
- **360–639px:** 20px gutters; header controls wrap; H1 and restart stack; route gap 20px; everything stacks; cards are horizontal (85px preview | text), card open action aligned under the text; enlarged action left-aligned below the count.
- V3: inspector hidden below 1100px, rail hidden below 640px, header actions wrap. V4 unchanged.
- No horizontal page scrolling; names wrap by word and are never truncated; counts never wrap away from “globos”.

## 10. Accessibility targets

Target WCAG 2.2 AA, subject to rendered verification of the implementation.

- Landmarks: `header`, route `nav` (“Navegación del producto”), conversation `section` and recommendation `section` with headings, preview index `nav` (“Elegir vista previa”), `footer`. Cards are `article`.
- Preview buttons are native buttons with accessible name “Ver escena: <name>”, `aria-pressed`, `aria-controls` to the stage title; the current one also says “Vista actual” in text. Focus stays on the invoker after selection.
- Open actions have accessible names that include the decoration (“Abrir en el Taller: <name>”).
- Live regions: selected name/count polite; loading `role=status` + `aria-busy`; empty `role=status`; error/offline/unavailable/count-error/V4 `role=alert`.
- View change focuses H1 (tabindex −1). D1: modal, focus contained, Escape/Cancelar close and return focus to «Empezar de nuevo».
- Contrast: text ≥4.5:1, control edges and focus ≥3:1 in both themes. Targets ≥44px. Focus 3px accent outline, 4px offset.
- Previews: images have alt text naming the decoration; decorative icons `aria-hidden`.
- Reflow to 360px (and 320 CSS px) without loss; 200% zoom without clipping; reduced motion keeps identical content.

## 11. Visual acceptance criteria and verification

“All” means 360px and up, checked at least at 390/768/1280px, light and dark, Spanish unless stated.

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | All | All | Pictures/Sempertex masthead, Idioma, Mi cuenta, Geist fonts and tokens match sibling contracts. |
| UI-AC-02 | ≥1100px | V1 ready | The conversation is left of the enlarged scene and the three-card index is below that scene. |
| UI-AC-03 | 840–1099px | V1 ready | The index is a single column of horizontal rows inside the scene column; names and open labels wrap inside their card. |
| UI-AC-04 | 640–839px | V1 ready | The conversation sits above the stage; the index has three columns. |
| UI-AC-05 | 360–639px | V1/V2 ready | Conversation, stage and index stack with no horizontal page scroll; cards are preview-left, text-right. |
| UI-AC-06 | All | ready / two-results | Each card shows a preview, the full decoration name and “<n> globos”; two results show exactly two cards and no placeholder. |
| UI-AC-07 | All | V2 any | No «Abrir en el Taller», no disabled substitute, no upgrade text and no plan name appear in the recommendation area. |
| UI-AC-08 | All | V2, V4 | The route row shows Chat and Proyectos and no Taller 3D. |
| UI-AC-09 | All | V1 ready → open a non-first card | V3 shows “Escena nueva”, “Sin guardar todavía” and that card's name and count; the route requested is `/3d?decoracion=<that id>`. |
| UI-AC-10 | All | V3 | «Guardar proyecto» (primary) and «Volver al chat» are in the studio header; activating «Guardar proyecto» opens the proyectos@v1 first-save dialog. |
| UI-AC-11 | All | empty | “No hay coincidencias”, the explanation sentence and «Cuéntame qué quieres cambiar…» appear; no card, preview or count is shown. |
| UI-AC-12 | All | loading | Skeletons and “Buscando decoraciones…” appear; no name or count; send shows Detener. |
| UI-AC-13 | All | error / offline / unavailable | The alert title, explanation and its recovery action appear in the recommendation area; earlier messages stay in the thread. |
| UI-AC-14 | All | count-error | Every count reads “Conteo no disponible” (never 0) and every open action is disabled. |
| UI-AC-15 | All | ready, English | Names are English gallery texts (Spanish when missing), labels read “Open in workshop” / “balloons”, counts are identical to Spanish; long names wrap without overflow. |
| UI-AC-16 | All | selection | Choosing another preview changes the enlarged scene, name and count, marks the card “Vista actual” with `aria-pressed=true` and keeps focus on that button. |
| UI-AC-17 | All | V1 opening | The enlarged action reads “Abriendo…” and all open actions are disabled. |
| UI-AC-18 | All | V4 | “No tienes acceso a esta herramienta”, “Tu cuenta no tiene permiso para abrirla.” and «Volver a herramientas» appear with no decoration name, image, count or plan name. |
| UI-AC-19 | All | preview-error | “Vista previa no disponible” and retry replace the enlarged preview while name and count stay visible. |
| UI-AC-20 | All | D1 | Cancelar/Escape keep the conversation and return focus to «Empezar de nuevo»; confirming returns to `initial`. |
| UI-AC-21 | All | Reduced motion / Quieto / still | All content and controls are present with no running animation after load. |

**Evidence for the canonical HTML built in this finalization** (`design/chat-a-3d@v1.html`, SHA-256 `e11e8f52b7fde89d1a3d00af5ba1b9ed4f86639af854b1ef9b3e6d2083287a17`):

| Check | Actual observation |
|---|---|
| Installed kit | `components status`: `installed=True built=True entries ok=96/96`. |
| Offline build | Exit 0: `built … (633 KB, 2126 source files, offline)`; real shadcn/Base UI/Animate UI controls, inlined CSS/JS and local Geist WOFF2 from t12. No fallback, install or fetch. |
| `contrast.py` | Exit 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Rendered audit | First run: `RESULT: FAIL — overflow 1` (the mockup's Vista select was 36px wider than 390px because of long inspector labels). Labels shortened; final run exit 0: `312 renders (312 combinations planned), 8058 text measurements, 711 focus stops` at 1280/390/768, both themes. |
| Interaction probe | 30/30 PASS: V1 four open actions and Taller route; counts 530/346/188; selection keeps focus and updates stage; opening the second card shows Escena nueva/Sin guardar todavía/its name/346/`escena%3Apared_fondo_columnas`; «Guardar proyecto» present and hands off to D1; V2 no open action, no Taller route, no plan words in the recommendation area, same counts; V4 alert copy, no decoration data; empty explanation and no cards; error explanation and retry restores three cards; two-results two cards; count-error disables opening and shows no “0 globos”; English names and counts; restart dialog opens and Escape closes; no overflow at 390 in all four views; `?still=1` 0 running animations, OS reduced 0, expressive 6; zero page errors; zero external requests. |
| Visual inspection | Screenshots inspected: V3 light 1280, V4 dark 1280, V2 English dark 390 full page. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Reproducible commands:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components status
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/.state/delegations/D-20261029-163215-a3ef/chat-a-3d@v1.final.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.html --widths 1280,390,768
```

These checks validate the planning artifact only. Recommendation ranking, streamed-text sanitation, gallery image fidelity, SP-9 English coverage, server permission refusal and saving are verified by T12.2, T12.4 and T12.6, not by this fixture.

## 12. Open questions and assumptions

Open questions (decision owner: David with the Planner; implementers must not infer answers from fixture values):

- **Q1** — Shell navigation on `/asistente`: approved `herramientas-chat@v1` places the SP-7 left tool sidebar on V5 Chat `/asistente`, while the chosen direction keeps the sibling horizontal route row. This contract governs the recommendation area only; the page shell follows whichever approved shell contract applies. Confirm that SP-12 inherits the SP-7 sidebar (the two-column workspace then sits in the main column) or that the route row stays.
- **Q2** — If the engine count fails for one recommendation, should the card be omitted until it recovers, or shown as “Conteo no disponible” with opening disabled (this contract)?
- **Q3** — Which preview does a card show when the gallery has no image for a decoration: omit the card, or show a neutral “Vista previa no disponible” as in `preview-error`?

Confirmed decisions (SPEC/PLAN, not reopened): two or three existing gallery decorations or none; names and counts only from gallery and engine; every plan sees the cards; only `decoraciones.explorar` (Master Designer, staff) opens `/3d?decoracion=<id>` as a new unsaved project without overwriting existing work; others see no button and no plan mention; no-match gives an explanation; English names follow SP-9 and missing English falls back to Spanish (SPEC SP-9 check); saving is proyectos@v1/SP-4; server permissions refuse unauthorized Taller access.

Assumptions: the first returned recommendation is enlarged initially; selection is presentational and changes no ranking; V3 and V4 are context fixtures (editor and tool home owned by other contracts); retry, example replies and timings are in-memory fixture transitions with no network or model.

**Approval:** this is a draft. David/the independent approver must approve this exact draft through the planning workflow before T12.1 copies it. The Designer grants no approval.

### Input/artifact identity

| Input / artifact | SHA-256 |
|---|---|
| `SPEC.md` | `095f5311948eb1f9bd2d3039da276f3011eb4fff13a95686748aadf315e720f9` |
| `PLAN.json` (revision 17) | `59880c53f91e69a17befc303572f9d41024d466895b40a3f7cd8155af0387810` |
| `design/chat-a-3d@v1.r1.behavior.md` | `0b1fdc83c6c2b72f0e0e0997e5c654485cede943ad8089cc39bb475de3bc6082` |
| `design/chat-a-3d@v1.r1.chosen.behavior.md` | `bce9d700b43677d53b4002483168e2025cf27d411b960fa2df40827916ee1a52` |
| `design/chat-a-3d@v1.r1.dir-b.md` | `7a29adcdfd51ac515ba8da0e93a9fd795431a18e3ecf86d57b8222042f9ee07c` |
| `design/chat-a-3d@v1.r1.dir-b.json` | `041c55dc046381f4cfe48f0d31e53d5cd255176ffdb6627ff053ca679b05d650` |
| `design/chat-a-3d@v1.r1.dir-b.tsx` | `b0b84228a97cafb563884836d7136141fc82ec5649ea83ffbe99fa057fc27338` |
| `design/chat-a-3d@v1.r1.dir-b.html` (owner's selection) | `bf3148b1ed4657fc50160d1c7e7bb70054e77ba1690064aff37ca595aedea0d4` |
| Patched source (delegation evidence) `chat-a-3d@v1.final.tsx` | `ba263532f4cbc11a1dfd953436a0395b3e38caaa100298fe92295735f3293a7a` |
| `design/chat-a-3d@v1.html` | `e11e8f52b7fde89d1a3d00af5ba1b9ed4f86639af854b1ef9b3e6d2083287a17` |
