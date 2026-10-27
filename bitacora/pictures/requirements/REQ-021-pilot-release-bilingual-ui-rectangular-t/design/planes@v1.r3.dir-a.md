---
contract: planes
version: 1
status: draft
artifact: direction-exploration
subplan: SP-14
requirements: [R17, R18, R19, R20]
revision: 3
direction: a
name: Pliegues de consulta · Operativa
owner: David
date: 2026-10-27
source: planes@v1.r3.dir-a.tsx
mockup: planes@v1.r3.dir-a.html
chosen_thumbnail: planes@v1.r3.dir-a.html.candidate-1.html
---

# planes@v1 — r3 direction a: Pliegues de consulta · Operativa

## 1. Identity and traceability

**Draft exploration, complete for comparison; not approved and not the canonical contract.** This direction-specific artifact follows the r3 behavioral brief, current SPEC access-plan behavior and round 13 answer, SP-14 in PLAN.md/PLAN.json, and the owner's selected direction C. The exploration key `a` is an output identifier, not a reversal of the owner's choice of Pliegues de consulta. Only revision-specific files are written. The finalizer alone may update the canonical pair after owner selection.

The amended scope removes tool-collapse controls, repairs tablet composition and adds informational plan selection. It preserves the continuous bands, full cumulative catalogue lists, in-page index, Pictures shell, entry/return paths, and both-language currency behavior. There is no purchase, request, contact, subscription, sign-up or account-plan action.

Consumer impact: only SP-14 binds `ui.contract=planes`, `version=1`, design-copy T14.1 and visual-review T14.5. T14.2 consumes comparison/selection/responsive behavior; T14.3 consumes the two entry links; T14.4/T14.6 verify browser/catalogue behavior. Relative to the old draft this is a **breaking visual change** for T14.2 because interaction and tablet structure change; T14.3 links stay compatible. SP-1 catalogue/permission contracts and SP-2 account contract are unchanged. No approval or plan mutation is granted.

## 2. Purpose and users

Any visitor, signed in or out, compares Entusiasta, Designer, Designer Plus and Master Designer. They can optionally select one plan for visual comparison, return to the full comparison and return to their entry surface. Selection is transient presentation state, independent of assigned role, account plan, permissions, authentication and payment. No save or confirmation of account assignment exists.

## 3. Information architecture and hierarchy

Retained masthead → 24px task title with contextual return → compact plan index and view switch → one paper with four continuous plan bands → explanatory sentence → existing footer. Each band has identity/price, Included tools caption and its full cumulative tool list. Lists are always visible in ready and selected states in both views. Unavailable features use a visible text label below their name. There is no promoted tier or recommendation.

**Thumbnail 1 chosen:** continuous ruled bands preserve the owner's chosen reading order and alignment of identity and tools. **Thumbnail 2 retained for comparison:** a two-column sheet of peer blocks loses the continuous reading axis and puts long advanced lists beside short base lists. Candidate 1 is the stronger fit for the selected C composition. Both thumbnail files were created before the TSX/full build and contain actual miniature compositions, not textual direction lists.

## 4. Design system and visual language

Read-only product sources: t12 login/page.tsx, LoginForm.tsx, globals.css, layout.tsx, CabeceraApp.tsx and MenuApp.tsx; matching asesor design-token source; sibling cuentas-admin@v1, taller-esenciales@v1 and proyectos@v1 Markdown and bundled HTML. SP-2's selected access shell governs sign-in/account context over the old shared-password login. Its production Geist fonts and general Pictures tokens govern the public section; workshop-specific tokens do not replace public/auth tokens. Some sibling HTMLs use older exploratory fonts/layouts; no new brand is inferred from them.

| Project source | Kit role | Light / dark |
|---|---|---|
| --fondo | background | #faf9fc / #0b0c10 |
| --superficie | card, popover | #ffffff / #16181f |
| --texto | foregrounds | #1c1425 / #f4f5f7 |
| --texto-suave | muted-foreground | #6b6178 / #9aa1ad |
| --superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| --acento | primary, ring | #6d3fe0 / #9479ff |
| --sobre-acento | primary-foreground | #ffffff / #120b24 |
| --acento-hover | primary-hover | #5530b8 / #a58dff |
| --borde, --borde-suave | decorative panel borders, rules | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| --texto-tenue | input/control edge, existing sibling alias | #766c85 / #8a91a0 |
| --error, --error-suave | destructive text/surface | #b23a45, #ffeaec / #ff979f, #43252a |

Production Geist Sans/Geist Mono WOFF2 files are embedded from the existing local Next build. No external font, image, package or asset request. Radius roles follow SP-2: 32px paper, 24px inset, 18px field, pill controls. Body 15px/1.5; title 24px/1.25/600; plan names 20px/1.3/600; prices 22px/500 with tabular figures (20px phone); tools 14px; supporting text 12–13px. No new palette or font family.

Real components: `shadcn:button outline ready|pressed|focus|hover` from `@/components/ui/button` for selection/view switch/retry, `shadcn:button default ready|disabled|loading` for retained SP-2 form context, `shadcn:input email|password` from `@/components/ui/input`, `shadcn:skeleton loading` from `@/components/ui/skeleton`. The installed Button uses Base UI; no fallback snippets. Plan bands, semantic lists, wrapping anchor index and native details menu are custom compositions of the existing product vocabulary, not new library components. Native inspect selectors are supplied by mountMockup/useMockup from @kit/mockup; motion profile comes from @kit/motion.

### Eight-axis direction table

| Axis | Rendered expression |
|---|---|
| concept | Operational reading of the owner-selected Pliegues de consulta; public plan information without account mutation. |
| layout | One continuous paper with four ruled bands. Desktop uses a 240px identity column; tablet moves identity above a two-column tool list; phone uses a single column. |
| navigation | Wrapping in-page plan index and a separate informational selection view; contextual return to sign-in or Mi cuenta; no new app destination in sibling navigation. |
| typography | Production Geist Sans; 24px page title, 20px plan names, 22px tabular prices (20px phone), 14px tool lines, 12–13px supporting text. |
| density | Dense grouped catalogue reading with 20px desktop band padding and 12px tool-row gaps; all cumulative tools remain visible. |
| components | Installed Base UI/shadcn Button, Input, Skeleton; retained native language selector and account disclosure; custom semantic plan bands, index and tool lists. |
| colour | Exact Pictures globals.css light/dark tokens. Neutral chrome and separators; existing accent marks the comparison highlight and keyboard focus. No new palette. |
| motion | Precise 480ms horizontal band registration with 35ms offsets and ease-out (.23,1,.32,1), counter-direction 180ms index cut, quick hover/press feedback; natural/subtle profiles and reduced/still parity. |

Motion is finite: band-cut translates 10px to zero in 480ms with 35ms offsets; index-cut counter-translates 8px in 180ms. Natural uses 300/140ms, subtle 160/100ms. Button feedback is quick and interruptible. Tool groups retain the existing profile-aware Motion spring. Hidden tabs pause CSS animations. Reduced motion, Quieto and ?still=1 remove travel and transitions, settle existing animations and retain all information/selection. No looping ornamental animation.

## 5. Navigation and interaction model

- Sign-in contains exactly one Planes/Plans link with destination /planes. The static preview opens the signed-out comparison.
- The signed-in account disclosure contains exactly one Planes/Plans link with destination /planes, alongside retained Mi cuenta and sign-out actions. Public variants have no account menu.
- The plan index focuses the target H2 and scrolls its band into view. It never changes selection or hides other tools.
- Elegir para comparar / Choose for comparison switches to the extra view. Each plan has Seleccionar para comparar / Select for comparison, with a plan-qualified accessible name and aria-pressed. Selecting replaces only the local comparison highlight; it immediately exposes a checkmark, explanatory text and a status announcement.
- Volver a la comparación / Return to comparison preserves the chosen highlight and renders the full four-plan comparison, with all lists visible. A new page load clears transient selection. The mock uses module memory to retain it across preview view changes; no account or server state is written.
- The contextual back link returns to sign-in or the same validated signed-in entry surface. Mi cuenta is the static signed-in example; production must restore a safe same-origin destination. Selecting a plan does not change that origin.
- Account disclosure closes with Escape and restores focus to its summary. View changes focus H1. Links are actual anchors with route/hash destinations; static click interception prevents network requests in the artifact.

## 6. Flows

F1: Sign-in → Planes → read four ordered plans and full tools → contextual return to sign-in.

F2: Mi cuenta → account disclosure → Planes → read comparison → contextual return to Mi cuenta. Production retains the actual originating permitted route.

F3: Comparison → Elegir para comparar → select any plan → selected outline/check/status appears → Volver a la comparación → all four plans remain, chosen one highlighted. No assigned plan, role, permission or account field changes.

F4: Browser/selected ES → COP / mes and Gratis; EN → USD / month and Free, with Entusiasta becoming Enthusiast. Other plan names stay. No view displays both currencies. Non-ES/EN falls back to ES; account language persistence belongs to SP-8.

F5: Loading → skeleton bands; empty/error/offline/incomplete → no partial authoritative prices → retry → ready comparison/selection. The static retry simulates a valid catalogue, not a live API response.

## 7. View specifications

| Native view | Surface | Visible structure and actions |
|---|---|---|
| public | /planes signed out | Masthead/language, Planes, return to sign-in, index, extra-view button, four full bands, explanation/footer |
| signed | /planes signed in | Same public content, account disclosure, contextual signed-in return |
| choose | /planes informational subview signed out | Same shell/index/bands, Elegir para comparar title, explicit non-mutation explanation, one selection control per plan, return to comparison |
| choose-signed | Informational subview signed in | Same selection behavior; account remains the same and only disclosure/return differ |
| login | SP-2 entry context | Retained centered 676px access paper, email/password/Entrar/reset hint; one Planes link. Authentication remains SP-2 scope |
| account | SP-2 entry context | Retained account paper and personal identity/password context with account disclosure; one Planes link in the disclosure. No editable plan field |

Single illustrative catalogue fixture, clearly identified by the Mockup footer. Implementation reads SP-1 plan-catalogue@1; it must not copy this fixture into a second production catalogue. Both inspected repository paths do not yet contain src/lib/planes/catalogo.ts; this is a declared future producer, not a verified live data source.

| Plan ES / EN | ES monthly | EN monthly | Full cumulative tools |
|---|---|---|---|
| Entusiasta / Enthusiast | Gratis | Free | Chat con límites / Chat with limits; Contador de globos / Balloon counter; Catálogo / Catalogue |
| Designer | 20.000 COP / mes | 7 USD / month | Chat con límites más altos / Chat with higher limits; balloon counter; catalogue |
| Designer Plus | 45.000 COP / mes | 14 USD / month | Designer list; Calculadora de costos / Cost calculator; Chat ampliado / Extended chat; Detección de estructuras / Structure detection; Detección avanzada de globos / Advanced balloon detection |
| Master Designer | 70.000 COP / mes | 25 USD / month | Designer Plus list; Taller 3D / 3D workshop |

Extended chat, structure detection and advanced balloon detection each show aún no disponible / not available yet under both upper plans. Cost calculator is available. Taller 3D represents the entire balloon editor including the ready-made decorations explorer; no separate explorer line. Entusiasta/Designer differ only in qualitative chat wording; no numerical limit value or counter. There are 21 cumulative tool rows and six unavailable annotations in each complete view. Explanatory copy: Cada plan incluye las herramientas del anterior. Un administrador asigna el plan. / Each plan includes the tools of the previous plan. An administrator assigns the plan.

## 8. States

The visible native Estado selector exposes ready, highlighted, loading, empty, error, offline, partial and menu-open.

| State | Output / recovery |
|---|---|
| ready | Four bands and all cumulative lists; extra selection view starts with no selection on a fresh load |
| highlighted | Designer Plus is a neutral fixture selection; same tools, check/status in selection view, outline/label in comparison; can select any other plan |
| loading | aria-busy catalogue region, Cargando planes / Loading plans status and four band skeletons; no fabricated prices or enabled selection action |
| empty | No plan cards/prices. Catalogue unavailable message and Reintentar/Try again; absence is a recovery condition, not a fifth plan |
| error | No unconfirmed catalogue. Error heading, retry and retained contextual return |
| offline | Sin conexión/Offline and connection/retry instruction; no stale prices presented as current |
| partial | No unconfirmed data; explicit retry, no incomplete plan comparison |
| menu-open | Signed-in disclosure open; absent from public variants; Escape closes and restores summary focus |

Empty/error/offline/partial/loading apply to both comparison and selection. Entry forms are context illustrations; only their inherited loading/error context is simulated. Permission denial, purchase success, sign-up, assignment pending and account mutation validation are inapplicable to a public informative section. Selection success is represented by highlighted state and status, not a purchase-success screen. No collapsible-tool state exists.

## 9. Responsive behavior

| Width | Observable layout |
|---|---|
| 1101px+; checked at 1280px | 40px outer gutters; paper inset 28px. Band identity column 240px beside a fluid two-column tool region. Toolbar index and view switch share a row |
| 761–1100px; checked at 768/820/1024px | 28px outer gutters; paper inset 24px. Identity/price/optional selection control wrap above the two-column tool list. No squeezed side column. Toolbar action moves below the wrapping index. Four plans stay in document order |
| 360–760px; checked at 390px | 20px outer/paper gutters. Header controls wrap; title/return stack. Index becomes a two-column link group, view-switch and selection buttons fill available width. Each plan stacks name, price, optional selection feedback and one-column full tools. No carousel or horizontal comparison table |

No horizontal page scrolling, clipped prices, offscreen selection controls or fixed-height tool panels. Labels wrap naturally in ES/EN. Vertical scrolling is expected to read long cumulative lists. Planning bar wraps independently of the product shell.

## 10. Accessibility targets

Target WCAG 2.2 AA for applicable content. Real button semantics, heading order H1/H2, ul/li tools, associated form labels, labelled native selects, skip link, context return and labelled plan navigation. Selection buttons expose aria-pressed; selected text/check/outline do not depend on colour alone. Changing selection announces its plan through role=status. Errors use role=alert; loading uses aria-busy and status.

Keyboard: Tab/Shift+Tab, Enter/Space on buttons and disclosure, native select operation, Escape account-menu close, plan-index focus to destination H2, view-change focus to H1. Actions have minimum 44px height; focus ring 3px with 4px offset. Text target ≥4.5:1, control-identifying edges/focus ≥3:1. Decorative row rules need not identify controls. Keyboard focus and content remain visible when motion is reduced. Full screen-reader/cross-browser/200–400% zoom acceptance remains implementation verification, not a design conformance claim.

## 11. Visual acceptance criteria and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | 390/768/820/1024/1280px | ready | Four bands are ordered Entusiasta, Designer, Designer Plus, Master Designer |
| UI-AC-02 | all supported | ready/highlighted | All 21 cumulative tool rows are visible; no hide/show-tools control is present |
| UI-AC-03 | all supported | ready ES | Prices are Gratis, 20.000/45.000/70.000 COP per month; no USD |
| UI-AC-04 | all supported | ready EN | First plan is Enthusiast/Free; paid values 7/14/25 USD per month; no COP |
| UI-AC-05 | all supported | ready/highlighted | Both upper plans show the three unavailable annotations in the active language |
| UI-AC-06 | all supported | ready | Chat uses qualitative limit wording and displays no numeric quota |
| UI-AC-07 | all supported | choose | Each plan has one plan-qualified comparison-selection button |
| UI-AC-08 | all supported | choose highlighted | Selected button has aria-pressed=true, checkmark and named status |
| UI-AC-09 | all supported | return from choose | Full comparison retains exactly one chosen outline/label and every tool row |
| UI-AC-10 | all supported | any plans | No purchase, request, contact, sign-up or account assignment control exists |
| UI-AC-11 | 761–1100px | ready/choose | Identity sits above two fluid tool columns, with no narrow identity side rail |
| UI-AC-12 | 390px | ready/choose ES/EN | Tool lists are single column and document width does not exceed viewport |
| UI-AC-13 | 1280px | ready | Identity is 240px beside two-column tools in one continuous paper |
| UI-AC-14 | all supported | login | One Planes link opens signed-out comparison; return goes to sign-in |
| UI-AC-15 | all supported | account/menu-open | One menu Planes link opens signed-in comparison; return restores entry context |
| UI-AC-16 | all supported | public/choose | No signed-in account disclosure is rendered |
| UI-AC-17 | all supported | loading | Four skeleton bands and busy/status presentation replace prices/selection |
| UI-AC-18 | all supported | empty/error/offline/partial | No unconfirmed plan prices are shown; retry restores ready content |
| UI-AC-19 | all supported | keyboard index | Activating an index link focuses that plan H2 without hiding tools |
| UI-AC-20 | all supported | reduced/still | No continuing travel animation; tools and comparison selection stay usable |
| UI-AC-21 | all supported | both themes | Existing Pictures palette/Geist, header, radius and footer vocabulary remain |
| UI-AC-22 | all supported | ready | Master has one Taller 3D line, no separate explorer line |

### Actual offline evidence

- Offline builder: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/planes@v1.r3.dir-a.tsx --out <design>/planes@v1.r3.dir-a.html` → exit 0, 562 KB, 2031 source files; real installed React/Base UI/shadcn/Motion bundled locally.
- Contrast: `python3 <kit>/kit/contrast.py <design>/planes@v1.r3.dir-a.html` → exit 0, 158 pairs checked in light and dark, all pass.
- Final snapshot audit: `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/planes@v1.r3.dir-a.html --widths 1280,1024,820,768,390 --max-combos 192` → exit 0, **480 renders / 480 combinations planned**, 14,260 text measurements, 608 focus stops. No sampling.
- **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**
- Supplementary Playwright behavior probe: **80 ready layouts** = four plan views × five widths × both themes × ES/EN. Every case has four plans, all 21 tool rows, six unavailable labels, the correct sole currency, correct account-menu presence and no horizontal page scrolling. Actual selection and preset selection persist on return; both entry/return links, five failure/loading states, retry and H2 index focus pass. Monitored pages: zero page errors and zero HTTP requests.
- In-memory screenshot inspection: desktop 1280px light/dark, phone 390px light/dark and tablet 820px dark selection. The final rendered paper, responsive tool columns, button borders and selection feedback were visually inspected; no screenshot files were written. The native selectors remain visible outside product content.

`<kit>` is `/home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit`. The initial successful audit measured the pre-border-refinement snapshot (14,204 text measurements); the final evidence above comes from a fresh complete audit after rebuilding the improved light button edges and preset-selection persistence. No old result substitutes for the final snapshot.

Build/audit scope is the static artifact only. No production lint, typecheck, tests or application build was run because production files were not changed. No real authentication, catalogue mutation, permission, server request or safe-origin route integration is established by a mockup. T14.2–T14.6 retain those responsibilities.

## 12. Open questions and assumptions

**Open owner questions: none for this scoped behavior.** Round 13 q1 is answered: selection only highlights comparison and never assigns an account plan. The administrator assignment sentence, free base tier, qualitative chat wording, unavailable trio and single Master 3D/explorer line are confirmed. No decision is deferred to the implementer.

Assumptions: the extra view is local to /planes and needs no new top-level menu entry or persistence API. Selection is transient across view changes and clears on a fresh load; it is never sourced from or saved to the account. Mi cuenta is the explicit safe return example; production validates the actual origin. The static account fixture remains Entusiasta while selecting any comparison plan. Browser language starts the product; changing the visible language selector is a preview of the existing language control. No new legal/marketing copy, named customer, date or promotion is invented.

CONCERNS: owner/plan approval remains outstanding. Static catalogue fixture and entry forms are illustrative; the production catalogue path is planned, not present in the inspected worktrees. All canonical and sibling artifacts, project repositories and plans remain untouched. The only additional write outside the six exploration artifacts is the explicitly required delegation RESULT.json. This exploration must be selected/finalized before T14.1 consumes a canonical approved snapshot.
