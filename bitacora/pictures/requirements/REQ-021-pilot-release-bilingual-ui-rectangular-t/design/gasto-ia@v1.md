---
contract: gasto-ia
version: 1
status: draft
subplan: SP-6
requirements: [R4, R5]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: c
name: Desglose en el lugar
source_revision: r1
source_behavior: gasto-ia@v1.r1.behavior.md
source: gasto-ia@v1.r1.dir-c.tsx
plan_revision: 17
---

# gasto-ia@v1 — Desglose en el lugar

## 1. Identity and traceability

Canonical planning **draft; not approved for implementation**. The owner chose direction c, “Desglose en el lugar”, in the web comparison. That choice authorizes this finalization only; it does not approve this contract, SP-6 or the plan. Version 1; no approved predecessor exists, so nothing approved is replaced. This task writes only `design/gasto-ia@v1.md` and `design/gasto-ia@v1.html` (plus the delegation RESULT). No exploration, history, SPEC, PLAN, changelog, preview or production file is changed.

Scope: REQ-021 / M2 / SP-6 “AI spend per user and session”, R4 and R5, from SPEC § “Behavior — SP-6 (round 12 pending)” and owner decisions round 12 q1/q2, PLAN.json revision 17 (schema 1.3.0), `gasto-ia@v1.r1.behavior.md` and the chosen r1 direction-c Markdown, JSON, TSX and HTML. No owner feedback items were recorded against the directions. One later owner decision applies: **round 16 q4 (answered 2026-10-29) / PLAN SP-10 — staff-only screens, AI spend included, stay in Spanish**. The exploration (written before that answer) translated the whole spend page to English; this finalization corrects that behaviour only (§11 lists the exact change).

| Requirement / criterion | Contract coverage | Consuming tasks |
|---|---|---|
| R4 — a completed paid AI call stores tokens and estimated cost against user and session | Data semantics §7, call metadata V1, partial/unknown rules §8, UI-AC-05–07 | T6.4 (render); T6.5 verifies attribution/idempotency |
| R5 — employee/administrator see totals per session, kind and user | V1 filters + grouping, F1–F2, UI-AC-02–04, 08 | T6.4; visual review T6.6 |
| Filter by user and kind; totals by session and work item; no prompts, generated content, secrets or unnecessary personal data | V1, F2, §7, UI-AC-04, 13 | T6.4; T6.6 |
| Usuario, signed-out or no `gasto.ver` cannot reach page or API; server-side check | V2/V3, F6, UI-AC-10 | T6.4; T6.5 |
| Provider error with known billable usage kept as partial/error; missing fields stay unknown | `partial` state, F3, UI-AC-06–07 | T6.4; T6.5 |

PLAN consumers: SP-6 `ui = {contract: gasto-ia, version: 1, design_task: T6.1, visual_review_task: T6.6}`. T6.1 copies the owner-approved contract byte for byte to `design/contracts/gasto-ia@v1.md` only after independent approval. T6.4 builds the `gasto.ver`-protected page and server-filtered API. T6.5 owns real-entrypoint attribution and authorization evidence; T6.6 reviews the rendered dashboard against this contract. T6.2/T6.3 (ledger, recording) and T6.7 (audit) are not UI and are not evidenced by this mockup. SP-10 T10.4 must list this screen among the Spanish-only staff screens.

Read-only product evidence: t12 (HEAD `fb872bce`) and asesor `src/app/globals.css`, `src/app/layout.tsx`, `src/app/admin/page.tsx` → `src/components/admin/AdminTabs.tsx` (H1 «Panel de administración», «← Volver al chat», horizontal Tabs), `CabeceraApp`. Sibling contracts `cuentas-admin@v1`, `planes@v1`, `proyectos@v1` (approved) supply the shared masthead, account disclosure, 24px heading, neutral route rule and rounded working paper; `decoraciones@v1` (draft) uses the same vocabulary.

Impact: **additive UI** — a new administration destination «Gasto de IA» inside the existing administration surface; no existing view's behaviour changes. No approved contract is affected.

## 2. Purpose and users

Working question: “Where did paid AI spend go, by whom and in which session or work item?”

- **Empleado interno and Administrador with `gasto.ver`**: open Administración → «Gasto de IA», read one known-cost total with its completeness, narrow by account («Usuario») and call kind («Tipo de llamada»), optionally by tool («Herramienta»), group by session, project/conversation or user, open a group to see its kind and tool subtotals and expand a call for its ledger metadata. The ledger is read-only.
- **Usuario accounts, signed-out visitors and anyone without `gasto.ver`**: receive no ledger, filters, other users' identities or totals — only a refusal or sign-in explanation with an existing recovery destination. The server enforces this for page and API; the mockup only shows the presentation.

Success: an authorized staff member sees totals that add up, can tell known cost from unknown cost, can locate a call's account/session/work item/provider/model/date, and never sees prompts, responses or generated content.

## 3. Information architecture and hierarchy

The change sits inside the existing administrative surface; it is not a new standalone page or landing. Order, top to bottom:

1. Inherited shell: Pictures/Sempertex ring-and-dot masthead, «Idioma» ES/EN select, account disclosure («Mi cuenta», «Planes», «Cerrar sesión»).
2. Page heading: H1 «Gasto de IA» with «Volver al chat» (ghost, arrow-left icon) on the right.
3. Administration route rule: «Cuentas» / «Roles y permisos» / «Gasto de IA» (current). Links render only when the viewer holds the matching permission (Q1).
4. One continuous **working paper** (32px radius):
   - Context line: «Datos de ejemplo · Solo lectura» (mockup only) and «Fecha de las llamadas · UTC · <fecha>».
   - Filter workbench (inline): «Usuario» select → «Tipo de llamada» Todos/Texto/Imagen → «Herramienta» disclosure → «Limpiar filtros» (right).
   - Total strip (1.2 : 1): left «Coste estimado conocido · USD», amount, «N / M llamadas con coste informado»; right «N llamadas · N cuentas · N sesiones», «Tokens totales conocidos: X · n/m llamadas», «Total de todos los resultados filtrados; importes estimados, no factura.»
   - Grouping control «Agrupar gasto»: «Por sesión» / «Por proyecto o conversación» / «Por usuario».
   - Spend stack: full-width group bands; one expanded at a time, containing kind subtotals → call list (native disclosures) → tool subtotals.
   - Pagination: «n / m grupos · Los totales incluyen todos los resultados.» + «Cargar más».
   - Privacy note: «Solo metadatos de uso. Sin prompts, respuestas ni contenido generado.»
5. Page footer (shell).

Hierarchy: primary = the filtered known-cost total and its completeness; secondary = group bands with their subtotal; supporting = call metadata, kind/tool subtotals, tool filter. Progressive disclosure: tool filter behind a disclosure, call metadata behind each call's disclosure, one group open. There are no KPI cards and no side inspector.

## 4. Design system and visual language

No new palette, font, identity or semantic token. Tokens are the production `globals.css` names; each theme defines them once and maps them onto shadcn roles (`--background`←`--fondo`, `--card`/`--popover`←`--superficie`, `--primary`←`--acento`, `--muted`/`--secondary`/`--accent`←`--superficie-2`, `--muted-foreground`←`--texto-suave`, `--border`←`--borde`, `--input`←`--texto-tenue`, `--ring`←`--acento`, `--destructive`←`--error`).

| Product token | Role / use | Light / dark |
|---|---|---|
| `--fondo`, `--texto` | background, foreground | `#faf9fc`/`#0b0c10`, `#1c1425`/`#f4f5f7` |
| `--superficie`, `--superficie-suave`, `--superficie-2` | paper/menu, call list inset, selected controls & skeleton | `#ffffff`/`#16181f`, `#faf8fd`/`#1c1e26`, `#efe9f8`/`#242733` |
| `--texto-suave`, `--texto-tenue` | supporting text & unknown values; control edges (≥3:1) | `#6b6178`/`#9aa1ad`, `#766c85`/`#8a91a0` |
| `--acento`, `--acento-hover`, `--sobre-acento` | primary button, brand mark, focus ring | `#6d3fe0`/`#9479ff`, `#5530b8`/`#a58dff`, `#ffffff`/`#120b24` |
| `--borde`, `--borde-suave` | paper, band and strip rules; shell rules | `#e3daef`/`#383c48`, `#efe9f8`/`#2a2d38` |
| `--exito` | «Completada» status | `#1f7a55`/`#78d6a8` |
| `--aviso`, `--aviso-suave` | partial status text, partial notice | `#8f5f12`/`#f7c46b`, `#fff3d8`/`#3f311c` |
| `--error`, `--error-suave` | error status text | `#b23a45`/`#ff979f`, `#ffeaec`/`#43252a` |
| `--overlay` | account menu shadow | `rgb(28 20 37/.4)` / `rgb(0 0 0/.6)` |

Typography: Geist Sans body 15px/1.5; Geist Mono for amounts (group and call cost 14–16px) with tabular figures. H1 24px/600 (−0.4px); group title 20px/600 (18px phone); empty/error H2 20px; total 32px/600 (−0.7px), tabular; labels 13px/600; metadata 12–14px; `dt` 12px muted. No uppercase eyebrows.

Shape and spacing: paper radius 32px, call list 24px, notices 24px, buttons/selects/disclosure summaries pill 999px, skeleton rows 24px. Paper inset 28px desktop / 20px phone; band padding 24px; outer gutters 40px (≥1101px), 28px (761–1100px), 20px (≤760px). All controls ≥44px tall.

Iconography: lucide-react 18px, `aria-hidden`, always beside text (ChevronDown, ChevronRight, UserRound, ArrowLeft, RotateCcw, Info, CircleAlert).

Focus: 3px `--acento` outline with 4px offset on every interactive element. Selected kind/grouping buttons use `aria-pressed` with `--superficie-2` surface and a `--texto` outline, not colour alone.

Components (`source:id variant state`, import path):

| Component | Variants / states | Import |
|---|---|---|
| shadcn:button | default (primary: «Reintentar», «Cargar más», «Abrir Mi cuenta», «Iniciar sesión», «Limpiar filtros» in empty), outline (kind control, account menu items), ghost («Volver al chat», grouping, «Limpiar filtros» in workbench) / normal, hover, focus, pressed (`aria-pressed`), disabled | `@/components/ui/button` |
| shadcn:skeleton | row 88px / loading | `@/components/ui/skeleton` |
| kit:motion | expressive, natural, subtle, reduced; profile spring on band press | `useMotionProfile` from `@kit/motion`; `motion.button` from `motion/react` |
| native:select user-filter / tool-filter / language | default, focus, disabled (loading) | native `select` with `label` |
| native:details more-filters / call / account-disclosure | closed, open | native `details/summary` |
| custom:filter-workbench | idle, filtered, loading (disabled) | `div` labelled «Filtros» |
| custom:total-strip | known, partial-coverage | `div` `aria-live=polite` `aria-atomic` |
| custom:group-tabs | sessions, work, users / pressed | `nav` «Agrupar gasto» + buttons |
| custom:usage-band | collapsed, expanded, unknown-cost | `section` + `h2 > button[aria-expanded]` |
| custom:call-row | success, partial, error / closed, open | `details` with `dl` metadata |
| custom:notice | partial (warning), scope (neutral) | `role=status` |
| custom:empty-block | empty, load-error (`role=alert`), denied, signed-out | `div` with H2, text, primary action |
| custom:brandmark | ring-and-dot | inline SVG from sibling shell |

Production AdminTabs uses `@/components/ui/tabs`; the route rule here follows the sibling contracts' neutral link rule (`aria-current=page`), as already approved in `cuentas-admin@v1`.

Motion (direction signature — “tactile compression and settle”), easing `cubic-bezier(.34,1.4,.64,1)`:

| Element | Movement | expressive / natural / subtle |
|---|---|---|
| Group bands | scaleY .975 + 5px → slight overshoot → rest, staggered | 520 / 320 / 160 ms; step 55 / 30 / 12 ms |
| Total amount | scaleX .965 → 1.012 → 1 on every filter change | settle duration |
| Expanded group body | translateY −5px, scaleY .985 → rest | settle duration |
| Call metadata, tool field | scaleX .975 → rest | settle duration |
| Notices | scaleY .97 → rest | settle duration |
| Buttons | hover −1px; press scale .965 + 1px | 170 / 140 / 100 ms |
| Band toggle | press scale .993 with profile spring | spring |

Only transform animates; no opacity drop, text legible throughout. OS reduced motion, «Quieto» and `?still=1` remove all animations/transitions/transforms and show final content. CSS animations pause while the tab is hidden. No infinite loop.

## 5. Navigation and interaction model

- **Entry:** Administración → «Gasto de IA» (route rule). The exact product route is not specified (Q1); `#gasto` in the mockup is an artifact anchor, not a route contract.
- **Exit:** «Volver al chat» (existing), «Cuentas» / «Roles y permisos» (sibling `cuentas-admin@v1`), account disclosure → «Mi cuenta», «Planes», «Cerrar sesión» (siblings). In the mockup these show a scope notice «<destino> · Destino existente fuera de este contrato.»
- **Language:** the masthead «Idioma» select and the footer follow the shared language mechanism (SP-8). The heading, route rule, working paper, notices and all spend copy stay **Spanish in both languages** (SP-10, round 16 q4); those regions carry `lang="es"` while `html[lang]` follows the request language. Number formatting in the spend region uses the Spanish (es-CO) grouping in both languages.
- **Filters** apply immediately on change. Changing «Usuario», «Tipo de llamada» or «Herramienta» collapses the open group and resets pagination to the first page; focus stays on the changed control. «Limpiar filtros» resets all three, restores pagination and reopens the first group; it is disabled when no filter is set (except in the empty state) and while loading.
- **Grouping** buttons switch the arrangement in place (not routes); the active one keeps `aria-pressed=true` and focus returns to it after the switch. Filters persist across groupings.
- **Groups:** activating a band opens it and closes any other; activating the open band closes it. On first load and after clearing filters the first group is open.
- **Calls:** each call is a native disclosure; opening reveals metadata in place; focus stays on its summary.
- **«Cargar más»** appends the next groups; the total keeps describing all filtered results.
- No dialog exists, so there is no focus trap and no `scene` selector.

## 6. Flows

**F1 Review spend.** Authorized entry → loading skeleton → total + completeness → choose grouping → open a group → read kind subtotals («Texto: $…», «Imagen: $…») and tool subtotals («Chat: $…», «Taller 3D: $…») → expand a call → metadata.

**F2 Narrow review.** Choose «Usuario» and/or «Tipo de llamada»; optionally open «Herramienta: Todas» and choose a tool → total, coverage, counts and groups update together, the amount re-seats → «Limpiar filtros» returns to the full scope. No match → empty state (F5).

**F3 Investigate incomplete provider usage.** A partial/error call appears with its status («Error · uso parcial» or «Error · coste desconocido») and the notice «Hay errores del proveedor con uso facturable conocido y metadatos incompletos. / El coste conocido se incluye. Lo no informado queda desconocido; no equivale a cero.» Known cost and known tokens are included; missing fields show «No informado»; a group whose calls all lack cost shows «Desconocido», never `$0.0000`.

**F4 Recover a fetch failure.** «No se pudo cargar el gasto» / «No se muestran totales sin confirmar. Conservamos los filtros para que puedas reintentar.» + «Reintentar» → re-runs the authorized server query with the same filters → normal.

**F5 Empty.** «No hay llamadas para estos filtros» / «Cambia o limpia los filtros para revisar otras llamadas. Si no hay llamadas registradas, aparecerán cuando haya uso de IA.» + «Limpiar filtros». No total is shown.

**F6 Denied / signed out.** Usuario or no `gasto.ver`: «Sin acceso» / «Tu cuenta no tiene permiso para ver el gasto de IA.» + «Abrir Mi cuenta». Signed out: no account disclosure; «Inicia sesión para continuar» / «El gasto de IA requiere una sesión y permiso de acceso.» + «Iniciar sesión»; focus moves to the H1. The route rule, filters and ledger are absent; the server never sends forbidden data to be hidden client-side.

## 7. View specifications

All views share §3; the inspection selector `view` switches the grouping (production: the grouping buttons).

**V1a `sessions` — Por sesión.** Band: title «Sesión …<sufijo>», caption = account, meta «N llamadas» + work item (project name, or «Conversación …<sufijo>»), cost + «USD estimados», chevron.

**V1b `work` — Por proyecto o conversación.** Project calls group under the project (all its conversations and sessions); calls without a project group under «Conversación …<sufijo>». Meta «N llamadas» + «N sesiones». Each call keeps conversation, account and session (round 12 q1).

**V1c `users` — Por usuario.** Title = account, caption «Gasto de esta cuenta», meta «N llamadas» + «N sesiones».

**Call row (all views).** Summary: «<Tipo> · <Herramienta>», subtitle «<Proyecto> / Conversación …<sufijo> · Sesión …<sufijo>», status tag («Completada», «Error · uso parcial», «Error · coste desconocido»), tokens («2.800 tokens» or «No informado»), cost (or «Desconocido»). Metadata `dl`: Usuario, Sesión, Proyecto / conversación, Proveedor / modelo, Tokens de entrada, Tokens de salida, Tokens totales informados, Fecha · UTC, Estado («Completada», «Error del proveedor · uso parcial facturable», «Error del proveedor · coste desconocido»). Input, output and total tokens are independent fields; none is derived from the others.

**V2 denied, V3 signed-out.** Heading and «Volver al chat» remain; route rule and paper content replaced by the empty-block of F6.

Data semantics: USD estimated cost with 4 decimals (Q3); a sum covers only known values and always shows its coverage («n / m llamadas con coste informado», «n/m llamadas» for tokens). Grouping uses stable server ids; the UI shows short display suffixes, not full ids, and no email or other personal data beyond the account display name. Dates labelled UTC (Q2).

Mock data (illustrative, synthetic): normal = four completed calls, two accounts («Cuenta de ejemplo», «Cuenta de ejemplo · 2»), sessions …a41/…b72: `0.0042 + 0.0600 + 0.0030 + 0.0360 = $0.1032`; Texto `$0.0072`, Imagen `$0.0960`; …a41 `$0.0642`, …b72 `$0.0390`; tokens 4.800 across 2/4 calls. Partial adds a partial call (`$0.0010`, 300 tokens) and an error call in session …c13 (1.200 tokens, cost unknown): total `$0.1042`, 5 / 6 cost-known, 6.300 tokens across 4/6. Providers/models (Google / gemini-3.6-flash, fal.ai / FLUX.2) are existing repository vocabulary; costs are not price claims. All dates 2026-10-29.

## 8. States

| State | What appears | What can be done / recovery |
|---|---|---|
| `normal` | Total, coverage, groups (first open), pagination, privacy note | F1, F2 |
| `loading` | «Cargando gasto…», three skeleton rows, `aria-busy=true`; no totals; filters and «Limpiar filtros» disabled | Wait |
| `empty` | F5 explanation and «Limpiar filtros»; no monetary total. Covers no matching calls and no recorded usage | Clear/change filters |
| `error` | F4 alert, filters retained and enabled, no figures | «Reintentar» |
| `partial` | Warning notice (F3), known usage included, unknowns labelled; a third session with unknown cost reachable via «Cargar más» | Inspect calls; load more |
| `denied` | V2 | «Abrir Mi cuenta» |
| `signed-out` | V3 | «Iniciar sesión» |
| control states | hover, focus, pressed, disabled, open/closed disclosures on the real controls | — |

Inapplicable: validation (only enumerated selects), save/success, edit/delete, budgets/caps (SPEC: caps out), export, dialogs. Offline/stale: an unavailable read uses `error`; no cached figures are shown. Failure of a later page («Cargar más») is undecided (Q4); the mockup's append is local and instantaneous.

Transitions: filter change re-seats the total and resets groups; state changes replace content without stale figures; reduced motion shows final states immediately.

## 9. Responsive behavior

Supported from 360px; transitions at 760px and 1100px (sibling shell).

| Range | Layout |
|---|---|
| ≥1101px | App max-width 1520px, 40px gutters, paper inset 28px. Filters inline in one row with «Limpiar filtros» right-aligned; total strip two columns 1.2fr/1fr; band grid `identity | meta (≥160px) | cost 150px | chevron`; call grid `title | tokens | cost 125px | chevron`; call metadata three columns. |
| 761–1100px | 28px gutters. Band meta moves under identity; cost and chevron stay right on the first row; call metadata two columns. |
| 360–760px | 20px gutters and paper inset. Masthead stacks; header tools span the width; account role label hidden; account menu aligns to its left edge. Filters stack in one column, selects full width; kind control a three-column row; «Limpiar filtros» left. Total strip one column. Grouping buttons a vertical list. Band: identity, meta, then cost below (left-aligned), chevron top-right; group title 18px. Call: title, tokens, cost stacked, chevron top-right; metadata one column. Pagination stacks. |

No horizontal page scroll in any range, theme or language; long model/identity labels wrap (`overflow-wrap:anywhere`). No content is dropped on phones.

## 10. Accessibility targets

Target WCAG 2.2 AA, to be verified on the rendered implementation.

- Landmarks/structure: `header`; `nav` «Administración» with `aria-current=page`; `section` «Revisión de gasto» with `aria-busy` while loading; `nav` «Agrupar gasto»; each band a `section` labelled by its `h2 > button`; metadata as `dl`.
- Keyboard: all controls in DOM order; bands toggle with Enter/Space (`aria-expanded`, `aria-controls`); native disclosures and selects; focus retained on the changed filter, restored to the pressed grouping button; H1 (`tabindex=-1`) focused on signed-out.
- Announcements: total strip `aria-live=polite aria-atomic`; loading, empty and partial `role=status`; load failure `role=alert`.
- Language: `lang="es"` on the staff regions when the shell is English, so assistive technology pronounces Spanish copy correctly.
- Contrast: text ≥4.5:1; control edges, focus and selection ≥3:1 in both themes. Status is always written in words, never colour alone; unknown values are words («Desconocido», «No informado»).
- Target size ≥44×44px; reflow at 360px (320px and 200–400% zoom remain production checks).
- Reduced motion as §4.

## 11. Visual acceptance criteria and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | 360px+ | all | Masthead with ring-and-dot mark, «Idioma» select, H1 «Gasto de IA», «Volver al chat» and footer are visible in both themes. |
| UI-AC-02 | ≥1101px | normal | Filters sit in one inline row above a two-column total strip and full-width group bands; there is no side inspector and no KPI-card grid. |
| UI-AC-03 | 360–760px | normal | Filters stack in one column with a three-button kind row, grouping buttons stack vertically, each band's amount appears below its identity and the page has no horizontal scroll. |
| UI-AC-04 | 360px+ | normal | Choosing «Texto» shows `$0.0072`; then choosing account «Cuenta de ejemplo» shows `$0.0042`; focus stays on the changed control. |
| UI-AC-05 | 360px+ | normal | Expanding a call shows Usuario, Sesión, Proyecto / conversación, Proveedor / modelo, Tokens de entrada, Tokens de salida, Tokens totales informados, Fecha · UTC and Estado. |
| UI-AC-06 | 360px+ | partial | The total reads `$0.1042`, «5 / 6 llamadas con coste informado» and «Tokens totales conocidos: 6.300 · 4/6 llamadas», with the warning notice above. |
| UI-AC-07 | 360px+ | partial | «Cargar más» adds session …c13 whose cost reads «Desconocido» (not `$0.0000`); the total stays `$0.1042`. |
| UI-AC-08 | 360px+ | loading / error | Loading shows three skeleton rows and «Cargando gasto…»; error shows «No se pudo cargar el gasto» with «Reintentar»; neither shows a total. |
| UI-AC-09 | 360px+ | empty | «No hay llamadas para estos filtros» and «Limpiar filtros» are visible; no monetary total is rendered. |
| UI-AC-10 | 360px+ | denied / signed-out | The route rule, filters, total and groups are absent; «Abrir Mi cuenta» (denied) or «Iniciar sesión» (signed-out) is offered. |
| UI-AC-11 | 360px+ | any grouping | Switching «Por sesión» / «Por proyecto o conversación» / «Por usuario» keeps filters, the total and the active button pressed and focused. |
| UI-AC-12 | 360px+ | shell EN | With «Idioma» EN, the masthead, account menu and footer are English while the H1, route rule and every string in the working paper remain Spanish and carry `lang="es"`. |
| UI-AC-13 | 360px+ | all | No prompt, response or generated content appears anywhere; the privacy note «Solo metadatos de uso…» is shown under the groups. |
| UI-AC-14 | 390 / 1280px | expanded | Expanded metadata, the account menu and the tool selector stay inside the viewport in both themes and both shell languages. |
| UI-AC-15 | 360px+ | reduced / still | Every field, control and status is present with no running animation. |
| UI-AC-16 | ≥1101px | first render | Bands settle with a visible stagger and the total re-seats on each filter change within ~520ms (expressive). |
| UI-AC-17 | 360px+ | any | Every interactive control is ≥44px tall and shows the 3px accent outline on keyboard focus. |

Verification of the canonical HTML built in this finalization:

- Source: the chosen `gasto-ia@v1.r1.dir-c.tsx`, copied to a scratch directory outside the bitácora (`/tmp/gasto-ia-final.ktCO/gasto-ia@v1.tsx`, temporary, not part of the record) with one behavioural fix: (1) a `shell()` translator for the masthead language label, account disclosure and footer, while all staff-region copy uses Spanish only; (2) `lang="es"` on heading, route rule, scope notice and paper; (3) Spanish number grouping always in the staff region; (4) total re-seat key no longer includes language; (5) scope-notice copy «fuera de esta exploración» → «fuera de este contrato». Layout, CSS, tokens, components, mock data and motion are unchanged. The exploration files are untouched.
- Build: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /tmp/gasto-ia-final.ktCO/gasto-ia@v1.tsx --out design/gasto-ia@v1.html` → 526 KB, 1,956 source files, offline, exit 0. Workspace: installed, built, 96/96 entries.
- Contrast: `python3 <kit>/kit/contrast.py design/gasto-ia@v1.html` → 158 pairs in light and dark, all pass, exit 0.
- Audit: `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py design/gasto-ia@v1.html` → 84 renders (84 planned), 2,648 text measurements, 432 focus stops, exit 0. **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems.**
- Behaviour probe (inline Playwright, `?still=1`): 34/34 checks — totals `$0.1032`/`$0.0072`/`$0.0042`, focus retained, clear filters; EN shell with Spanish heading/route/paper, `html[lang=en]`, paper `lang=es`, EN footer and account menu; partial `$0.1042`, 5 / 6, 6.300, 4/6; «Cargar más» adds an unknown-cost group without changing the total; all three groupings; call metadata fields; denied/signed-out without ledger; loading, error + retry, empty; no horizontal overflow at 1280/390 in both themes; no page errors; no network requests. Screenshots at 1280 light and 390 dark inspected: composition matches the chosen direction.

| Artifact | SHA-256 |
|---|---|
| `design/gasto-ia@v1.r1.dir-c.tsx` (chosen source) | `b8bc764b05127c34cd7f43d1d0965532e0f9bec34887b94a4cf9202b98f0182e` |
| `design/gasto-ia@v1.r1.dir-c.html` (exploration) | `a7f43154cc781c45b7cb16e2108c83cc399e51ece7bb2d9aa19ee9ec98eae037` |
| scratch TSX with the fix | `7658718e25f75c3ee479eed943e7e0618311044d51232d7882a802210f8adca1` |
| `design/gasto-ia@v1.html` (canonical rebuild) | `b685b198f2992c232399d2159fe7f25f60fd6788696dbab4659198f81e9e781c` |

Inspection selectors: `view` (sessions, work, users — «Vista»), `state` (normal, loading, empty, error, partial, denied, signed-out — «Estado»), `theme` («Tema»), `motion` («Movimiento»); no `scene`. Static fixtures do not prove server authorization, ledger correctness, idempotency or cursor paging; those belong to T6.4/T6.5.

## 12. Open questions and assumptions

Open questions (decision owner: David with the Planner):

- Q1: What is the spend route, and how does the administration entry look for an Empleado interno who lacks the users/roles permissions (hide «Cuentas» / «Roles y permisos» as drawn, or another entry)? Until answered, links render only for granted permissions.
- Q2: Should staff read dates in UTC (as drawn) or in America/Bogota like the sibling account register?
- Q3: Are four USD decimals enough, or should amounts below $0.0001 use finer precision so a non-zero cost never reads `$0.0000`? Related: the Spanish region groups thousands with «.» («4.800») while USD amounts use «.» as decimal («$0.1032»); confirm whether USD should keep the «$0.1032» notation or follow es-CO («US$ 0,1032»). Until answered, T6.4 renders as drawn.
- Q4: What copy and recovery appear when a later page («Cargar más») fails, and do already loaded groups stay visible? Proposal for decision: keep loaded groups, inline error under them with «Reintentar».

Confirmed decisions: access requires `gasto.ver` on page and API (server-side); metadata only, no prompts/responses/generated content; filters by user and kind, totals by session, work item and user; project total with conversation detail, standalone calls by conversation (round 12 q1); known billable usage from provider errors kept as partial/error, missing fields unknown, never zero (round 12 q2); no spend caps (round 2); staff screens including AI spend stay in Spanish (round 16 q4, SP-10); the ledger is read-only.

Assumptions (provisional visual choices, not new API or settings): one group expanded at a time, first open initially; three grouping modes; optional tool filter behind a disclosure; the total covers all filtered results above paginated groups (needs a server-side aggregate); account display name is the only personal datum shown; the mockup's «Datos de ejemplo», scope notices and inspection selectors are inspection aids, not product copy.
