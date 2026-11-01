---
contract: planes
version: 2
status: draft
artifact: ui-ux-contract
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
author: Designer
date: 2026-10-31
direction: Cartas al pie — direct manipulation of the existing /planes page (c)
source_revision: r4.dir-c
source_behavior: planes@v2.r4.behavior.md
source: planes@v2.r4.dir-c.tsx
mockup: planes@v2.html
---

# planes@v2 — Cartas al pie

## 1. Identity and traceability

**Draft; not approved for implementation.** Finalisation of the owner's web-selected direction **Cartas al pie (c), r4** for SP-14. Selecting a direction does not approve this contract; the owner approves it together with the SP-14 reconfirmation (P-211 stays open until the owner approves a later published version). This contract preserves the chosen composition, navigation, typography, colour mapping and motion. `planes@v2.html` was rebuilt from the immutable `planes@v2.r4.dir-c.tsx` with the current offline builder (`bitacora.py components mockup build`, 525 KB, 1955 source files, offline); no exploration file was edited, no source patch and no fallback HTML were used. No behavioural defect was found in the chosen exploration (section 11 evidence), so nothing was changed relative to it.

| Input snapshot | SHA-256 |
|---|---|
| SPEC.md | `6259a47b39e3de21a6364f99d5dd5012631279957945531f55fc4569d3a613ae` |
| PLAN.json (schema 1.3.0, revision 31) | `0b7cfbe815858e060ae661527666e2c6c054274162aa07195bbfefc228dfa6e0` |
| planes@v2.r4.behavior.md | `80864d06e320f379b8cb3817b2794e54656b247fb41e3bd709c85e7a084144be` |
| planes@v2.r4.dir-c.md | `4bf593a6c7bf889558036565afb0a04694a87973aeab31f2a0dcddeb27b08256` |
| planes@v2.r4.dir-c.tsx | `25989111fb13227a36e08907f6b3dd36f8bd1fcfa23010ea89b0a9c9c4be4dda` |
| planes@v2.r4.dir-c.html (owner-selected) | `7863880fa664f572704dad6daacba354e9255ac1f67b46ea32f232be3ed0be99` |
| planes@v2.html (this rebuild) | `b7f121a16a1925a424e883dbea479158a24ef0907aebac3eb1ca5c6ff02aeef2` |

Governing text: SPEC «Behavior — SP-14 subscription cards (P-211 supersedes round13 extra view)», the SP-14 Clarifications rows (plan names, prices, tools, chat wording without numbers, Taller 3D scope, ES=COP / EN=USD) and the r4 UI brief. Owner feedback recorded on direction C (`design/drafts.json`, all consumed by the explorations):

1. 2026-10-31 17:59 — each card shows a choose button like a normal subscription card («Escoger» / «Choose»).
2. 2026-10-31 18:27 — that button does «absolutamente nada»: purely visual, focusable, plan in its accessible name, press motion only; no status message, administrator sentence, navigation, request or account change. The owner states that this resolves the brief/SPEC conflict: cards still have no *functional* action.
3. 2026-10-31 19:13 — «el botón tiene que estar abajo del todo»: the button is the last element of each card.

Consumers (only SP-14 binds `ui.contract=planes`, `version: 2`): T14.11 copies the owner-approved snapshot to `design/contracts/planes@v2.md`; T14.2 replaces comparison/selection with the cards; T14.3 keeps exactly one plans entry on `/login` and in the shared account menu; T14.5 reviews rendered output against this contract. T14.4 (browser end-to-end) and T14.6 (catalogue/public-route/copy audit) verify integrated behaviour. T14.1 and the approved/historical `planes@v1` artifacts stay untouched. SP-1 owns `plan-catalogue@1` (`src/lib/planes/catalogo.ts`, validated at module load by `validarCatalogoPlanes(PLANES)`); SP-2 owns the account menu through `cuentas-admin@v2` (currently draft, composed here unchanged).

| Requirement | Views / flows | Acceptance |
|---|---|---|
| R17 one catalogue | V1–V3 / F1–F4 | UI-AC-01, 02, 03, 04 |
| R18 public informative section, unavailable markers, no purchase/access change | V1–V3 / F1–F4 | UI-AC-01, 05–11, 15 |
| R19 sign-in and account-menu links | V4–V5 / F1–F2 | UI-AC-12, 13, 14 |
| R20 COP in Spanish, USD in English | V1–V5 / F3 | UI-AC-03, 04 |

**Version/impact record, 2026-10-31 — planes@v2, draft.** Breaking presentation/interaction revision relative to `planes@v1`: the comparison sheet, «Comparar planes / Seleccionar para comparar» route tabs, «Ir a un plan» index, «Plan resaltado» default highlight, selection pressed state and selection summary are removed; `?vista=seleccionar` stops being a mode. Unchanged: catalogue data, permissions, public route, entry links, account behaviour. Required action: owner approval of this exact pair with SP-14 → T14.11 copy → T14.2/T14.3 implement → T14.4/T14.5/T14.6 verify. A changelog entry and PLAN/brief alignment (section 12, Q1) are outside this canonical-pair delegation.

## 2. Purpose and users

One question: *what does each access plan cost per month and which tools does it include?* Users are anyone — signed-out visitors arriving from `/login`, and every signed-in role (plan accounts, custom roles, internal employees, administrators) arriving from the account menu. All see identical public plan information; no account's current plan is marked and no plan is recommended.

Observable success: the person reads four peer cards in catalogue order, each with name, monthly price in the interface language's currency and the complete cumulative tool list with explicit «aún no disponible» / «not available yet» markers, then leaves through the existing back link or account navigation. Nothing on the page buys, pays, requests, contacts, registers, selects, assigns or changes access. Only an administrator assigns plans, on SP-2's accounts surface.

## 3. Information architecture and hierarchy

Order on `/planes` (unchanged published `ComparadorPlanes` shell, minus the comparison features):

1. Signed in only: account bar with the `cuentas-admin@v2` account menu trigger (right-aligned).
2. Masthead: Pictures · Sempertex ring-and-dot mark (left), «Idioma / Language» native select ES/EN (right).
3. Heading row: H1 «Planes / Plans» (left), back link «Volver al acceso / Back to sign in» (right).
4. Context line: «Un administrador asigna el plan. / An administrator assigns the plan.» (existing factual statement).
5. Deck: four `article` cards — Entusiasta/Enthusiast, Designer, Designer Plus, Master Designer — in DOM and reading order.
6. Footer: «Pictures · Sempertex» (the mockup's right-hand Geist Mono note is mockup chrome, not product copy).

Card hierarchy (all four identical in styling; no promoted tier):

1. Identity block (equal height in a row so prices share one line): H2 plan name; price — amount in tabular figures plus unit «COP / mes» or «USD / month»; Entusiasta shows «Gratis / Free» with no unit. A rule closes the block.
2. H3 «Herramientas incluidas / Included tools», then the complete cumulative list in catalogue order; unavailable tools carry a second line with the marker. No accordion, fold, hide-tools control, count badge or separate explorer row (Taller 3D stands for the whole 3D editor including the ready-made decorations explorer).
3. Card foot, pushed to the card bottom: the inert «Escoger / Choose» button (owner decisions 1–3).

## 4. Design system and visual language

Tokens are the product's `src/app/globals.css` values, mapped once per theme onto shadcn roles (`--background:var(--fondo)`, `--card:var(--superficie)`, `--primary:var(--acento)`, `--primary-foreground:var(--sobre-acento)`, `--muted:var(--superficie-2)`, `--muted-foreground:var(--texto-suave)`, `--accent:var(--acento-suave)`, `--border:var(--borde)`, `--input:var(--texto-tenue)`, `--ring:var(--acento)`, `--destructive:var(--error)`). No new token, palette, font or brand.

| Role | Token (light / dark) |
|---|---|
| Page ground | `--fondo` #faf9fc / #0b0c10 |
| Card surface, select, button ground | `--superficie` #ffffff / #16181f |
| Card border, identity rule, footer rule | `--borde-suave` #efe9f8 / #2a2d38 |
| Text | `--texto` #1c1425 / #f4f5f7 |
| Units, tools label, context, back link | `--texto-suave` #6b6178 / #9aa1ad |
| Select border | `--texto-tenue` #766c85 / #8a91a0 |
| Available check, button text/border, focus ring | `--acento` #6d3fe0 / #9479ff |
| Button hover, back-link hover | `--acento-suave` #ece3fb / #241f3d |
| Unavailable check and marker text | `--aviso` #8f5f12 / #f7c46b |

Typography: product Geist (body 15/1.5), Geist Mono only in mockup chrome. H1 24/600, letter-spacing −.03em; H2 plan name 18/600; amount 30/600 tabular-nums (26 px below 640 px); unit 13; tools label 12/550; tool rows 14/1.45; unavailable marker 12; back link 14; button 600 weight.

Shape and spacing: cards radius 24 px, 1 px border, no shadow; padding 24 px (20 px below 640 px); deck gap 16 px (12 px below 640 px); identity block min-height 96 px (none below 640 px), 18 px bottom padding; tools label 18 px above, 6 px below; tool rows 6 px vertical padding, 16 px icon column, 8 px gap; card foot ≥20 px above the button; button full card width, min-height 44 px, pill radius. Page width `min(100% − 48px, 1440px)` (100% − 40 px below 640 px).

Icons: lucide `Check` 16 px for every tool row (accent when available, `--aviso` when not yet available), `ChevronLeft` 18 px in the back link, `ChevronDown` in the account trigger. One stroke weight; no emoji.

Components (`source:id variant state`, import path):

| Component | Name | Import / origin |
|---|---|---|
| Card button | `shadcn:button outline-restyled default/hover/focus-visible/active` | `@/components/ui/button` — restyled to `--acento` border/text on `--superficie`, `--acento-suave` hover; **no handler** |
| Language select | `native:select idioma default/hover/focus-visible/active` | existing `ComparadorPlanes` masthead (`#planes-language`) |
| Back link | `custom:back-link default/hover/focus-visible/active` | existing `ComparadorPlanes` heading row |
| Plan card | `custom:plan-card peer default` | existing card vocabulary in `comparador-planes.module.css`; article + H2/H3 |
| Tool row | `lucide:check available/unavailable` | `lucide-react` |
| Account menu | `cuentas-admin@v2:account-menu closed/open` | `src/components/cuentas/MenuCuenta.tsx` — unchanged, SP-2 owns it |
| Sign-in plans link | `custom:plans-link default/hover/focus-visible/active` | existing `LoginForm` link — unchanged |

Motion (press/settle grammar shared with `cuentas-admin@v2` direction C; transform/opacity only; content stays legible mid-animation):

| Move | Spec (expressive / natural / subtle) |
|---|---|
| Card arrival | `card-drop` translateY(18px) scale(.97), opacity .4 → rest; `cubic-bezier(.34,1.42,.64,1)`; 460 / 300 / 170 ms; stagger 70 / 45 / 15 ms in catalogue order |
| Tool row arrival | `row-in` translateY(−6px), opacity .4 → rest; base delay 160 ms + card stagger + row stagger 35 / 22 / 8 ms |
| Language change | select `lang-settle` scale .92 → 1.04 → 1 on the settle spring; each price rolls (old figure out up −70% in 140 ms, new in from +70% on the profile spring); lists remount and re-settle with no base delay |
| Back link | press scale .96 (90 ms, `cubic-bezier(.4,0,.7,1)`); chevron nudges −3 px on hover (settle) |
| Card button | press scale .97, 90 ms; hover background 180 ms; no other feedback |
| Account menu | `cuentas-admin@v2` spring (unchanged) |

Reduced motion (`prefers-reduced-motion`, «Quieto», `?still=1`): all animations and transitions removed; language change swaps instantly. Hidden tab pauses animations.

## 5. Navigation and interaction model

Entry points: the single plans link on `/login` («Planes / Plans», below the sign-in form) and the single «Planes / Plans» entry in the shared account menu (`aria-current="page"` while on `/planes`). The public route needs no session. Legacy `/planes?vista=seleccionar` and obsolete selected-plan query parameters render the same page; no parameter restores a mode, pressed plan or highlight.

| Control | Outcome |
|---|---|
| «Idioma» select ES/EN | Changes the page language in place: names, tools, units and currency switch together (ES → COP, EN → USD; never both). Uses the existing `idioma` mechanism; the account menu's ES/EN pair follows the same mechanism. |
| Back link «Volver al acceso / Back to sign in» | Navigates to `/login` for both session states, as the host does today; no origin/history tracking is added. |
| «Escoger / Choose» (one per card) | **Inert.** Focusable button; pointer, Enter or Space only play the press motion. No navigation, URL change, focus move, status/live-region message, request, pressed/selected state or account change. |
| Account menu | Unchanged `cuentas-admin@v2` behaviour (open/close, Escape returns focus to trigger, outside-click/blur dismissal, identity, language pair, «Mi cuenta», «Planes», «Cerrar sesión»). |

Focus order: (account trigger) → language select → back link → card 1 button → card 2 button → card 3 button → card 4 button. Tool rows and headings are not focusable.

## 6. Flows

- **F1 — Signed-out visitor.** `/login` → «Planes» link → `/planes` (signed out) → reads four cards → back link → `/login`. Nothing selected or requested.
- **F2 — Signed-in person.** Any signed-in page → account menu → «Planes» → `/planes` with account bar → reads four cards → leaves via existing account navigation or back link. No current-plan marker on any card.
- **F3 — English visitor.** `/planes` with English browser language (or select EN) → «Plans», «Enthusiast … Master Designer», «Free», «7 / 14 / 25 USD / month», «not available yet». Switching back to ES restores COP with the price roll.
- **F4 — Legacy selection URL.** `/planes?vista=seleccionar` or an obsolete selected-plan query → identical cards; no comparison, selection, highlight or summary; account unchanged.
- **F5 — Pressing «Escoger / Choose».** Any card button by pointer/Enter/Space → press motion only; page, URL, focus and account unchanged (owner decision 2).

## 7. View specifications

**V1 — `/planes`, signed out (ES default).** Masthead, heading row, context line, deck, footer as in section 3. Card content (from `plan-catalogue@1`, punctuation preserved):

| Plan (ES / EN) | Price ES | Price EN | Tools in order (unavailable marked †) |
|---|---|---|---|
| Entusiasta / Enthusiast | Gratis | Free | Chat asistido con límites. · Contador de globos · Catálogo |
| Designer | 20.000 COP / mes | 7 USD / month | Chat asistido con límites más altos. · Contador de globos · Catálogo |
| Designer Plus | 45.000 COP / mes | 14 USD / month | Chat asistido con límites más altos. · Contador de globos · Catálogo · Calculadora de costos · Chat extendido† · Detección de estructura† · Detección avanzada de globos† |
| Master Designer | 70.000 COP / mes | 25 USD / month | Designer Plus tools · Taller 3D |

English tool names: Assisted chat with limits. / Assisted chat with higher limits. · Balloon counter · Catalog · Cost calculator · Extended chat† · Structure detection† · Advanced balloon detection† · 3D workshop. † shows «aún no disponible» / «not available yet» on a second line in `--aviso`. Amount formatting: `es-CO` / `en-US`, no decimals. Each card's foot holds «Escoger» / «Choose» with accessible name «Escoger: <plan>» / «Choose: <plan>».

**V2 — `/planes`, signed in.** V1 plus the account bar (64 px min-height, bottom `--borde-suave` rule) carrying the `cuentas-admin@v2` trigger. Card content identical for every role (mock states: Designer Plus account; internal employee). Back link copy and target unchanged.

**V3 — `/planes?vista=seleccionar` (legacy).** Identical to V1/V2 for its session state.

**V4 — `/login` plans link.** Unchanged sign-in surface; exactly one «Planes / Plans» link (bordered, 44 px, accent text) inside the sign-in card below the reset guidance; activates F1.

**V5 — Account menu plans entry.** Unchanged `cuentas-admin@v2` panel; exactly one «Planes / Plans» entry between «Mi cuenta» and «Cerrar sesión»; activates F2.

Mock data is illustrative (two mock accounts `designerplus@prueba.local`, `empleado@prueba.local`); plan data is the real catalogue copy.

## 8. States

| State | Applies | Behaviour |
|---|---|---|
| Default (ES / COP) | V1–V5 | As specified; the Spanish browser default. |
| English (USD) | V1–V5 | English copy and USD; never both currencies. |
| Signed in, plan account / internal employee | V2, V5 | Account bar present; cards identical; no current-plan marker. |
| Legacy query | V3 | Same cards; no mode. |
| Account menu open | V5 | `cuentas-admin@v2` open panel; Planes entry `aria-current="page"`. |
| Button hover / focus / active | all cards | Hover `--acento-suave` ground; focus 3 px `--acento` outline, 3 px offset; active scale .97. No pressed/selected persistence. |
| Reduced motion / still | all | No travel; instant swaps. |
| Light / dark | all | Token mapping of section 4. |
| Loading, empty, catalogue error, retry | **Inapplicable** | The catalogue is a static import validated at module load (`validarCatalogoPlanes(PLANES)`); malformed data fails build/validation. No catalogue request, skeleton, empty success or Retry is invented. Existing host error handling (framework error page) stays as is. |
| Disabled, validation, success, permission-denied | **Inapplicable** | No form, mutation or protected content; the route is public. The inert button is not `disabled` (owner wants a focusable, pressable button). |
| Offline / stale | **Inapplicable** | Server-rendered static catalogue; no client fetch. |

## 9. Responsive behaviour

| Range | Layout |
|---|---|
| ≥1100 px | Four columns, `align-items:stretch`; identity blocks equal (96 px min) so all prices share one line; card foot `margin-top:auto` so all four buttons share one bottom line. Measured at 1280 px: button bottoms equal (858 px signed-out ES, 838 px EN). |
| 640–1099 px | 2×2 grid; each row shares a price line and a button line. Measured at 768 px: rows at 624 / 1203 px (signed-out ES). Account bar padding 24 px. |
| <640 px | One column, 12 px gap, 20 px card padding, 26 px amounts, no identity min-height; masthead wraps with the language select pushed right; heading row stacks (H1 then back link); each button is the card's last element; account menu panel becomes fixed full-width (16 px insets). |

All widths: normal vertical scrolling, no horizontal page scroll, tool names wrap (`overflow-wrap:anywhere`), never truncate or collapse. Verified at 360, 390, 768 and 1280 px, ES and EN, signed in/out and legacy.

## 10. Accessibility targets

Target WCAG 2.2 AA; these are targets checked on the mockup, not a conformance claim for the implementation.

- Semantics: one `main`; H1 «Planes»; each card is an `article` labelled by its H2; H3 tools label; tools are a `ul` with `aria-label` «Herramientas incluidas: <plan>»; check icons `aria-hidden`; `lang` reflects the interface language on `main` and `html`.
- Keyboard: all controls reachable in the section 5 order; visible 3 px `--acento` focus outline with 3 px offset; account menu Escape returns focus to its trigger.
- Accessible names: card buttons «Escoger: <plan>» / «Choose: <plan>»; language select labelled «Idioma / Language»; account trigger «Cuenta: <name>».
- Inert button: no `aria-pressed`, no live region, no `disabled`. It is announced as a button that has no effect — an owner decision recorded in section 1 and Q1, not a defect to be fixed by implementers.
- Unavailable status is text, not colour alone.
- Contrast: text ≥4.5:1, control edges ≥3:1 in both themes (158 pairs pass).
- Target size: interactive controls ≥44 px high.
- Reflow: 320 CSS px equivalent through the <640 px layout without horizontal scroll.
- Reduced motion: section 4.

## 11. Visual acceptance criteria and verification evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | 360–1280 px | V1 ES | Four `article` cards appear in the order Entusiasta, Designer, Designer Plus, Master Designer. |
| UI-AC-02 | 360–1280 px | V1 ES/EN | Cards show 3, 3, 7 and 8 tool rows respectively, all visible without any expand/hide control. |
| UI-AC-03 | 360–1280 px | ES | Prices read Gratis, 20.000, 45.000, 70.000 with «COP / mes» on the paid plans; no «USD» text on the page. |
| UI-AC-04 | 360–1280 px | EN | Prices read Free, 7, 14, 25 with «USD / month»; no «COP» text on the page; plan 1 reads «Enthusiast». |
| UI-AC-05 | 360–1280 px | ES / EN | Exactly six «aún no disponible» / «not available yet» markers (three each on Designer Plus and Master Designer), under Chat extendido, Detección de estructura and Detección avanzada de globos. |
| UI-AC-06 | 360–1280 px | ES | Chat rows read «Chat asistido con límites.» (Entusiasta) and «Chat asistido con límites más altos.» (others), with no numbers. |
| UI-AC-07 | 360–1280 px | any | All four cards share the same border, surface and button styling; no badge, highlight, check-marked plan or current-plan marker. |
| UI-AC-08 | 360–1280 px | any | No «Comparar planes», «Seleccionar para comparar», «Ir a un plan», «Plan resaltado», selection summary, buy/request/register control, and no `aria-pressed="true"`/`aria-selected="true"`/`aria-current` inside the page content. |
| UI-AC-09 | 360–1280 px | any | Each card's last element is the foot with «Escoger» / «Choose», below the full tool list; its accessible name includes the plan name. |
| UI-AC-10 | ≥640 px | any | Buttons of cards in the same grid row share one bottom edge (±1 px); at ≥1100 px all four share it. |
| UI-AC-11 | 360–1280 px | button pressed by pointer, Enter, Space | Only the press motion plays; page markup, URL and focused element are unchanged; no `role=status` node appears; account assignment unchanged. |
| UI-AC-12 | 360–1280 px | V1/V2 | The back link reads «Volver al acceso» / «Back to sign in» and navigates to `/login`. |
| UI-AC-13 | 360–1280 px | V4 | The sign-in screen shows exactly one «Planes / Plans» link and it opens `/planes`. |
| UI-AC-14 | 360–1280 px | V5 | The open account menu shows exactly one «Planes / Plans» entry and it opens `/planes`; the rest of the menu matches `cuentas-admin@v2`. |
| UI-AC-15 | 360–1280 px | V3 | `/planes?vista=seleccionar` shows the same cards as `/planes` with no extra controls. |
| UI-AC-16 | 360, 390, 768, 1280 px | ES/EN, light/dark | `document.scrollWidth` ≤ viewport width; no clipped tool text; keyboard focus outline visible on every control. |
| UI-AC-17 | 360–1280 px | reduced motion | No transform travel occurs on load, language change or press; content is fully present. |

Evidence on `planes@v2.html` (2026-10-31, this finalisation):

- `contrast.py`: «contrast: 158 pairs checked in light and dark, all pass».
- `audit_mockup.py` (offline Playwright): «60 renders (60 combinations planned), 3036 text measurements, 150 focus stops» — **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**.
- Extra Playwright pass driving the «Vista»/«Estado» selects at 360/390/768/1280 × ES/EN × public/signed-in/legacy (reduced motion): order and names per UI-AC-01/04; tool counts [3,3,7,8]; 6 markers; prices per UI-AC-03/04; every card's last child `.card-foot`; button bottoms equal per row; no horizontal overflow; 0 pressed/selected/current nodes in page content; at 1280 px a click + Enter + Space left `.app` markup and URL unchanged with 0 `role=status`. Screenshots at 1280 dark and 390 light inspected.

## 12. Open questions and assumptions

Open (decision owner: David, with the Planner for PLAN/SPEC text):

- **Q1.** The r4 brief and SPEC still say «no card action is rendered» / «do not add disabled or decorative purchase CTA», while the owner explicitly asked for the inert «Escoger / Choose» button (decisions 1–2) and stated it resolves the conflict. Should the SPEC/brief and T14.2/T14.5 acceptance be amended to name this inert button explicitly, so the implementer and the visual reviewer do not remove or flag it? This contract follows the owner's decision.
- **Q2.** Assistive technology announces «Escoger: <plan>» as an actionable button that does nothing. Keep as decided, or should the button carry an accessible description? Default here: keep exactly as decided (no description, no status).

Assumptions (confirmed from existing authority/code unless stated):

- Back link copy and `/login` target are the host's current behaviour for both session states; no origin tracking is added.
- Unavailable tools keep the `Check` icon (they are included in the plan) in `--aviso` plus explicit text; availability is never implied by colour alone.
- The language comes from the browser until SP-8 and is switchable in place via the existing `idioma` mechanism.
- `cuentas-admin@v2` is still a draft; V2/V5 compose it unchanged and follow whatever version the owner approves.
- The mockup bar title still reads «r4» because the HTML is a faithful rebuild of the unedited exploration source; the route strip and footer note are mockup chrome, not product UI.
