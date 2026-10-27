---
contract: planes
version: 1
status: draft
artifact: ui-ux-contract
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
author: Designer
date: 2026-10-27
direction: Planos de consulta (b)
source_revision: r4.dir-b
source_behavior: planes@v1.r4.behavior.md
source: planes@v1.r4.dir-b.tsx
mockup: planes@v1.html
---

# planes@v1 — Planos de consulta

## 1. Identity and traceability

**Draft; not approved for implementation.** Finalization of the owner's web-selected **Planos de consulta (b), r4**. Direction selection does not approve this contract. This replaces the previous unapproved canonical direction-C draft with the selected B composition and behavior, including the round-13 comparison-only selection view and the r4 initial visible motion reference. It preserves the selected composition, navigation, typography, palette and motion. The HTML is rebuilt directly from the immutable selected TSX with the current offline builder; no exploration edit, source patch or fallback is used.

Inputs: SPEC.md (`status: ready`), PLAN.json schema 1.3.0 / REQ-021 revision 2, `planes@v1.r4.behavior.md`, and the selected r4.dir-b Markdown, TSX and self-contained HTML. SPEC's “Behavior — access plans and plans section” and “Behavior — SP-14 extra view (round 13 answered)” govern. The explicit R18 availability list governs over the older ambiguous Priorities parenthetical: extended chat, structure detection and advanced balloon detection are unavailable; the cost calculator is available. Catálogo remains a base-plan tool, as confirmed in the SPEC behavior and SP-1 catalogue contract.

| Input snapshot | SHA-256 |
|---|---|
| SPEC.md | `7087fe226abd34699d6e0b5e4e4ad12c4d2cf67571e067506c38d41184f69792` |
| PLAN.json | `caa26fa2012bdf9e133483a40d6f2150f8a27ac9ed884054bdbbba134f548aa6` |
| planes@v1.r4.behavior.md | `3f69cc0a465ac74b71a63cf247d9b1d38dbb87e0139ab13b8e52076fdf0b8239` |
| planes@v1.r4.dir-b.md | `8eb1aae36c8c2b417e7c855c0bd446fc65a28550d3ffbb9cbf6da456048c829a` |
| planes@v1.r4.dir-b.tsx | `6aa8d9aee13fd2ef7468f7d0930c4b5ca4cc9fa86a69b331f4246de47cf15ba7` |
| planes@v1.r4.dir-b.html | `174233f344c1f5c55c54a5abfae1ec89d3785a76641a65cdb2bfbfcd6eb8cb41` |

Only SP-14 binds `ui.contract=planes`, version 1: T14.1 design-copy, T14.2 public page and extra selection view, T14.3 entry links, T14.5 visual review. T14.4 verifies integrated browser behavior and T14.6 audits catalogue/public-route/copy invariants. SP-1 T1.2 owns `plan-catalogue@1`; SP-1 supplies `permission-map@1` and `session-guard@1`. SP-2 owns the access/account surfaces through `cuentas-admin@v1`; SP-14 adds exactly one plans entry at each agreed location. CG-4/T94 checks composition with catalogue, account assignment and permission enforcement, without becoming another UI-contract consumer.

| Requirement | Views / flows | Acceptance |
|---|---|---|
| R17 single catalogue | V1–V4 / F1–F5 | UI-AC-01–08, 26; T14.2/T14.6 verify real catalogue reads |
| R18 public informative section | V1–V4 / F1–F5 | UI-AC-01–13, 17–22 |
| R19 access/account links | V5–V6 / F1–F2 | UI-AC-14–16, 25 |
| R20 language and currency | V1–V6 / F3 | UI-AC-03–05, 24 |

Embedded version/impact record, **2026-10-27 — planes@v1, draft**: compatible with the chosen r4 B exploration; **breaking relative to the superseded unapproved C draft** because hierarchy, local navigation, responsive composition, permanently visible lists and comparison selection differ. Affected implementation: T14.2 plans/comparison/selection and T14.3 entry-link composition; acceptance: T14.4/T14.5/T14.6. Required action: independent owner/plan approval of this exact pair, then T14.1 copies the approved snapshot to `design/contracts/planes@v1.md`, T14.2/T14.3 implement it and T14.5 compares rendered output. No existing approved contract is edited or approval granted. A separate changelog, history or PLAN edit is outside this canonical-pair delegation; this embedded record supplies the impact assessment without changing consumer references.

## 2. Purpose and users

A visitor or signed-in person answers: which tools and monthly price belong to each access plan? Success means comparing the four complete tool lists, distinguishing unavailable tools and returning to the originating surface. The additional selection view lets the person highlight one plan as a temporary comparison preference. It never assigns access.

The same plans information appears for visitors, plan accounts, custom-role accounts, employees and administrators. No account's current plan is marked in the comparison. The account identity in the inherited masthead is contextual identity, not a comparison recommendation. Buying, paying, subscribing, requesting, contacting, registering and changing account access have no controls here. An administrator assigns plans on SP-2's accounts surface. Numeric chat limits, usage counters and limit-enforcement messages remain outside this requirement.

## 3. Information architecture and hierarchy

Retain the Pictures/Sempertex ring-and-dot masthead, language control, signed-in account disclosure and footer. Follow with the page H1 and contextual back link; two neutral route links (“Comparar planes” and “Seleccionar para comparar”); the explanatory sentence; then a local plan index beside **one continuous rounded comparison sheet**. Four ruled peer quadrants display Entusiasta, Designer, Designer Plus and Master Designer in DOM/reading order. At desktop they occupy top-left, top-right, bottom-left and bottom-right respectively. No tier is promoted as recommended or current.

Each quadrant contains H2 plan name, monthly price, the comparison-reference/selection label when applicable, then “Herramientas incluidas / Included tools” and its complete cumulative tool list. Every list stays visible. There is no fold, accordion, hide/show-tools control or separate ready-made-explorer row. The dock repeats the same name and price from the same catalogue data.

In full comparison, the dock contains anchors to the four articles. Initially Entusiasta has a check marker, subtle highlighted surface, accent rule and **Plan resaltado / Highlighted plan** label. This reference provides the owner's requested initial visible motion evidence; it is identical for visitors and signed-in people and does not initialize a comparison choice. In selection mode the same dock becomes four single-choice pressed-state buttons; a summary and full-comparison return appear below it. All four quadrants and lists remain present even after a choice.

## 4. Design system and visual language

Fixed inputs inspected read-only: `src/app/globals.css`, `layout.tsx`, `login/page.tsx`, `login/LoginForm.tsx`, `CabeceraApp.tsx` and `MenuApp.tsx` in t12 and asesor, plus sibling `cuentas-admin@v1` and the chosen direction's provenance. The current sibling “Parte de acceso” shell governs the invitation-only access/account context over the old shared-password form. Keep the existing Pictures identity, neutral route navigation, paper vocabulary and local Geist fonts. Do not import workshop-specific palettes into this surface.

| Pictures token | Kit role / responsibility | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--superficie-suave` | selected comparison quadrant | #faf8fd / #1c1e26 |
| `--superficie-2` | secondary, muted, neutral hover/disabled | #efe9f8 / #242733 |
| `--texto` | foreground, card/popover/secondary foreground | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted-foreground, supporting text | #6b6178 / #9aa1ad |
| `--texto-tenue` | input/control boundary, inherited SP-2 accessible alias | #766c85 / #8a91a0 |
| `--acento` | primary, ring, links, comparison marker | #6d3fe0 / #9479ff |
| `--sobre-acento` | primary-foreground | #ffffff / #120b24 |
| `--acento-hover` | source primary hover | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | decorative sheet outline and shared rules | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--aviso`, `--aviso-suave` | unavailable status text/source surface | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | error text/source surface | #b23a45, #ffeaec / #ff979f, #43252a |

The control-edge alias uses the retained accessible sibling treatment rather than decorative `--borde`. These are mappings of the selected design, not a new palette. Keep radius roles: panel 32px, inset 24px, field 18px, pill 999px. Geist Sans body 15px/1.5; H1 24px/1.25 weight 600; plan H2 20px/1.3 weight 600; price 22px weight 600 with tabular figures (20px below 640px); tools 14px; captions, unavailable status and footer 12px; supporting form copy 13px. Geist Mono is confined to inherited metadata/wordmark treatment. Bundle existing local WOFF2 assets; no remote fonts.

Components are named **source:id variant state**:

| Component | Actual import / responsibility |
|---|---|
| `shadcn:button outline ready\|hover\|focus\|pressed\|disabled` | `@/components/ui/button`, real shadcn/Base UI; retry, comparison return and inherited account actions |
| `shadcn:button default ready\|hover\|focus\|pressed` | Same import; inherited sign-in/password action fixtures only |
| `shadcn:input default empty\|filled\|focus\|invalid` | `@/components/ui/input`; inherited labelled email/password fields |
| `shadcn:skeleton default loading` | `@/components/ui/skeleton`; four non-pulsing catalogue placeholders |
| `custom:plan-index anchor ready\|hover\|focus\|reference\|unavailable` | Native anchors in `.rail-options`; fragment targets and programmatic article focus |
| `custom:plan-selector single-choice unselected\|selected\|hover\|focus\|disabled` | Native buttons with plan-qualified names and `aria-pressed`; no radio or assignment semantics |
| `custom:comparison-sheet ruled normal\|reference\|selected` | Semantic articles, H2/H3 headings and lists in `.sheets`; full cumulative data |
| `custom:account-disclosure details closed\|open\|focus` | Retained native details/summary shell; links/actions, Escape and outside-click dismissal; no new kit menu claim |
| `custom:language-select native es\|en\|focus` | Labelled native `select#language`, independent from planning selectors |
| `custom:catalogue-message inline empty\|error\|offline` | Heading, recovery copy and real retry Button |
| `custom:comparison-marker shared-layout reference\|selected\|settled` | `motion.span` from `motion/react`, layoutId `comparison-marker`, Check icon from `lucide-react`; profile from `@kit/motion` |
| `custom:mockup-controls inspector view\|state\|theme\|motion` | `mountMockup/useMockup` from `@kit/mockup`; native external planning selectors |

Motion preserves B's opposing spatial entrances: rail from x=-16px; four quadrants from x=+22px with 45ms staggering; opacity .85→1; 440ms cubic-bezier(.16,1,.3,1). The reference/selected marker, label and 44px accent rule settle from scaleX(.85), opacity .8. Selecting moves the shared spring marker (expressive stiffness 220, damping 16, mass .9). Quick control feedback uses 180ms cubic-bezier(.23,1,.32,1): rail hover moves +4px, buttons lift -2px and press +1px/scale(.975). Natural uses 280/140/25ms settle/quick/stagger; subtle uses 160/100/12ms. These CSS timings are distinct from the Motion shared-marker spring. Do not replace them with generic transitions. Quieto, `?still=1` and OS reduced motion settle immediately, including pseudo-elements through the current runtime; hidden-tab CSS animations pause. Entrances are finite, with no continuous offscreen effect.

## 5. Navigation and interaction model

`/planes` is public without authentication. `/planes?vista=seleccionar` represents the additional informational selection view. Both share the same signed-in/out context. Route navigation shows the active link with `aria-current=page` and a neutral underline. Product navigation focuses the H1 (`tabIndex=-1`) and starts at the top of the view. The extra view changes no role, permission, account field, cookie, storage or server data.

The comparison index uses `#plan-entusiasta`, `#plan-designer`, `#plan-designer-plus` and `#plan-master-designer`. Activation scrolls to and focuses the named article without selecting it; the sticky offset clears the inspector in this artifact and persistent chrome in production. Choice buttons retain focus when activated, expose only one `aria-pressed=true`, highlight the corresponding quadrant and announce its name in the polite selection summary. The full-comparison return preserves that in-memory comparison highlight; it never becomes “current plan.” Entering the extra view on a fresh session starts with no choice, regardless of the initial Entusiasta visual reference.

One “Planes / Plans” link appears after the sign-in form's reset guidance. The account disclosure has one “Planes / Plans” entry between “Mi cuenta / My account” and “Cerrar sesión / Sign out.” Signed-out return goes to `/login`. Signed-in return goes to the page from which the person opened the plans section, without altering session/access. The fixture demonstrates Mi cuenta (`/cuenta`) as that origin; production must retain the actual internal origin. Direct signed-in entry uses the existing safe account return, not an external URL. SP-2 owns account navigation, authentication and sign-out behavior; only the two plans links are added here.

## 6. Flows

**F1 — Visitor comparison.** Open sign-in → follow its sole plans link → read the four plans and full tool lists → optionally use a plan anchor → return to sign-in. Neither entry nor reading requires credentials.

**F2 — Signed-in comparison.** Open the inherited account disclosure → follow its sole plans entry → keep the signed-in masthead → compare the same public data → return to the internal originating page. Escape closes the disclosure and returns focus to its summary; outside click closes it.

**F3 — Language.** On initial visit, English browser language yields EN/USD; Spanish or an unsupported language yields ES/COP. Until SP-8, the browser-language rule governs; the fixture uses `navigator.language`, while production follows its established Accept-Language/data-notice policy. The visible ES/EN control switches all product copy and prices together without changing view, comparison preference or account assignment. This fixture retains language in memory only; SP-8 owns account-wide language persistence. Never show both currencies together.

**F4 — Comparison-only choice.** From either comparison context follow “Seleccionar para comparar / Select to compare” → read the explicit no-account-change explanation → initially see no choice → activate any of the four plan buttons → see its pressed state, marker, quadrant label and summary → choose another if desired → “Volver a la comparación completa / Back to full comparison.” All lists remain visible throughout. Returning retains the comparison preference in memory; a fresh document load resets it. The mock `selected` state may seed Designer Plus for inspection only.

**F5 — Catalogue failure/recovery.** Loading displays skeletons and announces progress. Empty, malformed/error or offline catalogue replaces the sheet with the corresponding explanation and Retry. Choice controls are disabled while data is unavailable and index anchors do not move focus to missing articles. Retry loads the complete catalogue again; the mock restores its complete local fixture. Never infer a missing price, render a misleading partial comparison or treat unavailable data as a successful empty list.

## 7. View specifications

| ID / native view | Structure, actions and scope |
|---|---|
| V1 `compare` | Public signed-out `/planes`: masthead without account disclosure; H1 Planes/Plans and access return; two route links; “Un administrador asigna el plan. / An administrator assigns the plan.”; anchor dock; four-quadrant sheet; inherited footer. Initial Entusiasta reference is visual only. F1, F3, F5. |
| V2 `compare-signed` | Same data and composition as V1 with inherited account disclosure and contextual signed-in return. No current-plan badge or extra staff information. F2, F3, F5. |
| V3 `select` | Signed-out extra view; H1 “Seleccionar para comparar / Select to compare”; active route link; “La selección solo resalta un plan para comparar. No cambia el plan de tu cuenta. / Selection only highlights a plan for comparison. It does not change your account plan.”; pressed-state dock; full sheet; live summary; full-comparison return. F3–F5. |
| V4 `select-signed` | Same as V3 with account disclosure/context retained. Selecting Master Designer never changes the fixture's Entusiasta identity or the real account's assignment/access. F2–F5. |
| V5 `login` | Retained centered SP-2 access paper, email/password fields, invitation-only/reset guidance and action; exactly one added Plans link after guidance. Form submissions show a mock explanation and send no credentials. SP-2 governs real sign-in states. F1. |
| V6 `menu` | Retained SP-2 Mi cuenta paper and account disclosure, initially open for entry inspection; identity and password fixture remain contextual. The sole Plans entry sits between Mi cuenta and sign-out. Password form is simulated; SP-2 governs real account behavior. F2. |

One requirements-derived mock catalogue supplies both dock and sheet. Production reads names, translations, order, prices, tools and availability exclusively from `src/lib/planes/catalogo.ts` (`plan-catalogue@1`), not from a second page-owned array. At finalization that file is not present in either input worktree; this static artifact does not prove catalogue integration.

| Order / name ES → EN | Monthly ES / EN | Full visible tool list in order |
|---|---|---|
| 1 Entusiasta → Enthusiast | Gratis / Free | Chat con límites; Contador de globos; Catálogo |
| 2 Designer | 20.000 COP / mes; 7 USD / month | Chat con límites más altos; Contador de globos; Catálogo |
| 3 Designer Plus | 45.000 COP / mes; 14 USD / month | Chat con límites más altos; Contador de globos; Catálogo; Calculadora de costos; Chat ampliado; Detección de estructuras; Detección avanzada de globos |
| 4 Master Designer | 70.000 COP / mes; 25 USD / month | Same seven entries as Designer Plus, then Taller 3D |

The table documents both locales; the rendered interface shows only its active one. Free has no charged amount. Paid amounts use the active locale's separators and explicit currency/month suffix. English tool labels are “Chat with limits”, “Chat with higher limits”, “Balloon counter”, “Catalogue”, “Cost calculator”, “Extended chat”, “Structure detection”, “Advanced balloon detection” and “3D workshop”. The three unavailable tools each carry **aún no disponible / not available yet** under both upper plans, six status labels total. They have no activation control. The cost calculator is available. Taller 3D includes the ready-made decorations explorer without a separate row. No limit numbers appear.

## 8. States

| Native state / applicability | Visible result, actions and transition |
|---|---|
| `normal`, V1–V4 | Complete 3/3/7/8 tool lists and four prices. Fresh comparison shows Entusiasta reference; fresh selection has no pressed choice and summary “Ningún plan seleccionado / No plan selected.” |
| `selected`, V1–V4 | Inspectable comparison preference: Designer Plus if none exists; otherwise retain the chosen preference. Production reaches this through F4. Label is “Seleccionado para comparar / Selected for comparison”, never account assignment. |
| `loading`, V1–V4 | Four skeleton groups replace data; `aria-busy=true` and “Cargando planes… / Loading plans…” status. No guessed price or active choice. |
| `empty`, V1–V4 | “No hay planes disponibles / No plans available”; “Vuelve a intentarlo para consultar los planes. / Try again to view the plans.”; “Reintentar / Retry.” |
| `error`, V1–V4 | Alert: “No se pudieron cargar los planes / Could not load plans”; recovery sentence and Retry. Missing or malformed required catalogue fields use failure, never partial success. |
| `offline`, V1–V4 | “Sin conexión / Offline”; “Conéctate y vuelve a cargar los planes. / Connect and reload the plans.”; Retry. No stale prices are represented as current. |
| Disabled choice, V3–V4 unavailable-data states | Buttons expose native disabled semantics, neutral surface/readable text, no selection action. Return and context navigation remain available. |
| Hover/focus/pressed, interactive controls | Visible accent focus outline, short retained motion and pressed-state feedback; no information or action exists only on hover. |
| Recovery/success, V1–V4 | Successful retry returns to `normal` with complete data. A choice announces its name without a toast or assignment-success claim. |
| Validation/permission-denied | No plans form or permission requirement exists on a public read-only section; these are inapplicable here. Inherited authentication/account validation belongs to SP-2; V5/V6 do not implement its backend. |
| Partial/stale/pending write | Partial/stale catalogue presentation is deliberately unsupported: use error/offline recovery. No account write is started, so pending-write, assignment confirmation and assignment-denied states are inapplicable. |

External inspector: native `view`, `state`, `theme`, `motion` selects labelled Vista, Estado, Tema, Movimiento; theme values light/dark, profiles expressive/natural/subtle/still. No dialog is declared, so no `scene` selector is needed. All six catalogue states are reachable through the inspector; on V5/V6 the state selector does not invent parallel authentication states. The inspector, source-revision title and “Mockup · Datos y operaciones simulados / Mockup · Simulated data and operations” footer establish fixture status and are not new production flows.

## 9. Responsive behavior

| Width | Layout and adaptations |
|---|---|
| 320–639px, including required 390px | 20px outer gutters; masthead wraps, language/account tools in their next row as needed; heading/back stack; route links wrap; dock 2×2; one-column continuous plan sheet in catalogue order; 20px panel insets and 20px prices. Selection summary stacks, full-width return. No horizontal page scroll. |
| 640–839px, including 768px | 24px gutters; dock above sheet in 2×2; sheet two equal columns, 24px insets; summary/return wrap in normal flow. No fixed-width side rail. |
| 840–1099px, including 1024px | Dock above sheet in four columns; two-column sheet; 24px gutters. Summary alongside return where space permits; header wraps. |
| ≥1100px, including required 1280px | App max-width 1520px; 40px outer gutters; sticky 216px rail, 28px gap, flexible 2×2 sheet. Rail top is persistent chrome height +20px. 24px quadrant insets. |

Names, status labels, translated copy and prices wrap within min-width:0 grid tracks. Account disclosure stays within viewport width; it floats from the masthead without modal behavior. New controls are at least 44px tall; dock items have greater height for name/price. At desktop all four headings and first rows appear in the first viewport, while long lists remain available through normal vertical scrolling. Reflow at 320px and enlarged text must preserve all content and controls; no fixed height clips a tool list.

## 10. Accessibility targets

Target applicable WCAG 2.2 AA behavior; this draft and automated checks do not certify conformance. Production uses header/navigation/main/footer landmarks, one H1, H2 per named plan, H3 for tools and semantic lists. The current offline builder supplies `main#app` around the selected `.app` composition; this main landmark was verified in the canonical rendered DOM. Decorative ring/check/arrow icons have `aria-hidden=true`; visible text carries plan and availability meaning.

Keyboard order follows DOM: shared controls, contextual return, route navigation, dock, content, selection return and footer/entry controls as applicable. Links activate with Enter; choice buttons with Enter/Space; summary toggles with Enter/Space. Programmatic H1/article targets use `tabIndex=-1`. Choice keeps focus; account Escape closes and restores summary focus. No modal focus trap applies. Disclosure actions are normal Tab-reachable controls; do not assign menu roles without implementing their keyboard pattern.

Focus is a 3px accent outline, offset 4px, visible on links/buttons/inputs/selects/summary. Ensure index-target focus is not clipped or hidden beneath chrome. Text contrast target ≥4.5:1; essential control edges/focus/selection markers ≥3:1. Decorative paper rules are not the sole control boundary. Comparison selection has a pressed state, check, explicit label and live summary, rather than color alone. Loading/status/recovery are announced politely; errors use `role=alert`. Native disabled controls communicate unavailable-data state. Target sizes are at least 44px tall, exceeding the applicable 24px minimum; provide adequate separation and wrapping.

Reduced motion/Quieto/still mode must stop CSS, pseudo-element and Motion animations while preserving the same visible data, selection and focus. No animation gates access to text. Test reflow, 200% text enlargement, keyboard and screen-reader reading/announcement behavior in implementation; static fixture forms do not establish accessible authentication conformance.

## 11. Visual acceptance criteria and verification evidence

All criteria refer to both themes and both languages unless the state says otherwise. “All supported” means 320px and above with the adaptations in §9; 390/768/1024/1280px are the core rendered checks.

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | All supported | V1–V4 normal/selected | Four articles appear in Entusiasta/Enthusiast, Designer, Designer Plus, Master Designer DOM order. |
| UI-AC-02 | All supported | V1–V4 normal/selected | Full 3/3/7/8 tool lists remain visible without a hide/show-tools control. |
| UI-AC-03 | All supported | ES normal/selected | Paid plans show 20.000, 45.000 and 70.000 with COP / mes, and no USD. |
| UI-AC-04 | All supported | EN normal/selected | Paid plans show 7, 14 and 25 with USD / month, and no COP. |
| UI-AC-05 | All supported | ES/EN normal | First plan is Entusiasta/Enthusiast and displays Gratis/Free respectively. |
| UI-AC-06 | All supported | V1–V4 normal/selected | Each upper plan has three unavailable labels on extended chat, structure detection and advanced balloon detection. |
| UI-AC-07 | All supported | V1–V4 normal/selected | Entusiasta uses the with-limits phrase and Designer the with-higher-limits phrase, without limit numbers. |
| UI-AC-08 | All supported | V1–V4 normal/selected | Only Master Designer lists Taller 3D/3D workshop, with no separate explorer row. |
| UI-AC-09 | All supported | Fresh comparison normal | Entusiasta shows a rail marker and Plan resaltado/Highlighted plan label before visitor input. |
| UI-AC-10 | All supported | Fresh selection normal | No button is pressed and summary says Ningún plan seleccionado/No plan selected. |
| UI-AC-11 | All supported | Selection after a choice | Exactly the activated plan button is pressed and its name appears in the polite summary and highlighted quadrant. |
| UI-AC-12 | All supported | Return after selection | Full comparison retains the comparison highlight and all tool lists. |
| UI-AC-13 | All supported | V1–V4 every state | No purchase, request, contact, sign-up or account-plan-change control appears. |
| UI-AC-14 | 390/1280px | V5 login | Exactly one Plans link appears after reset guidance and opens signed-out comparison. |
| UI-AC-15 | 390/1280px | V6 account disclosure open | Exactly one Plans entry sits between My account and Sign out and opens signed-in comparison. |
| UI-AC-16 | All supported | Signed-in/out return | Back retains context: sign-in for visitor, originating internal page for signed-in person. |
| UI-AC-17 | 1280px | V1–V4 normal | A 216px lateral rail and 28px gap precede one rounded 2×2 ruled sheet. |
| UI-AC-18 | 768px | V1–V4 normal | A 2×2 top dock precedes a two-column sheet without horizontal page overflow. |
| UI-AC-19 | 1024px | V1–V4 normal | A four-column top dock precedes a two-column sheet. |
| UI-AC-20 | 320/390px | V1–V4 normal/selected | Dock has two columns and plan articles stack in one column without horizontal page overflow. |
| UI-AC-21 | All supported | loading | Four skeleton groups replace successful data and loading status is announced. |
| UI-AC-22 | All supported | empty/error/offline | Recovery heading/copy and Retry replace the sheet, and plan-choice controls are disabled. |
| UI-AC-23 | All supported | Keyboard focus | Each interactive control has a visible outline; comparison anchor activation focuses its target article. |
| UI-AC-24 | All supported | Language switch | Product copy and currency switch together while comparison choice is retained. |
| UI-AC-25 | 390/1280px | Account disclosure open | Escape closes the disclosure and restores focus to its summary. |
| UI-AC-26 | All supported | Catalogue-backed implementation | Changing one catalogue price updates both dock and sheet without editing page data. |
| UI-AC-27 | 1280px | Initial expressive comparison | Rail, quadrants, reference marker and highlighted label visibly animate with the preserved opposing entrance grammar. |
| UI-AC-28 | 390/1280px | Quieto / still / OS reduced motion | No active entrance, marker or pseudo-element motion remains; data and chosen comparison stay visible. |
| UI-AC-29 | All supported | V4 choice then return | Comparison choice leaves account identity, assigned plan and next-request permissions unchanged. |

Fresh canonical-artifact verification on 2026-10-27:

- Current offline build: `python3 /home/david/.agents/skills/metodologia/scripts/bitacora.py components mockup build <design>/planes@v1.r4.dir-b.tsx --out <design>/planes@v1.html` — **PASS**, 553 KB, 2,031 bundled source files. The exact source was unchanged. No package install, network asset fetch, fallback or generated-HTML patch.
- `python3 <kit>/kit/contrast.py <design>/planes@v1.html` — **contrast: 158 pairs checked in light and dark, all pass**, exit 0.
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/planes@v1.html --widths 1280,390,768,1024` — **288 renders (288 combinations planned), 9136 text measurements, 560 focus stops**, exit 0. All six views/six states, both themes, four widths; no sampling warning.

**RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**

- Supplemental cached Playwright against the canonical HTML — **144 scenarios PASS**, including 128 responsive combinations at 320/390/640/768/840/1024/1100/1280px, ES/EN, both themes and the four comparison/selection contexts. Verified 3/3/7/8 lists, six unavailable labels, currency, breakpoint composition, initially empty selection, all four choice/return paths, unchanged account identity and storage, failure recovery, both entry links and contextual returns, article focus, Space selection, account Escape/focus restoration, Quieto, `?still=1` and OS reduced motion. No page errors or external HTTP requests. This establishes fixture behavior; it does not prove real account assignment or server permissions.
- A fresh expressive first-load probe found running `railArrive` on the rail, four `paperArrive` effects on quadrants, and `selectionLine` on both initial reference marker and label, without visitor input. Reduced modes had zero running animations, including pseudo-element effects under the current runtime.
- Settled screenshots were inspected in memory at **1280/390px in both themes**: ES light comparison and EN dark signed-in selection. They retain the chosen rail/sheet arrangement, stacked phone plans, shared masthead, readable full lists and selection summary/return. No screenshot files or separate preview were written.
- Canonical HTML SHA-256: `418c789b8994b99a38cffae95326087d7ad72210026299054993fccd3c7bd58d`. Its bundled inspector retains the selected-source r4/B/Draft title; the document is the canonical rebuilt artifact. No verified behavioral defect required a local source or HTML patch.

`<design>` is this requirement's design directory; `<kit>` is `/home/david/.agents/skills/metodologia/agents/designer/skills/david-ui-kit`. Production catalogue/authentication/permissions, assistive technology and full WCAG conformance remain T14.2–T14.6 verification work.

## 12. Open questions and assumptions

**Open owner questions: none.** Round 13 resolved comparison-only choice, permanently visible tools and tablet behavior. The delegated brief records B as the new selected direction; references to the older selected C inside immutable exploration history are historical. Neither selection nor this draft grants approval.

Confirmed/deferred boundaries: no numeric limit values or enforcement; no current-plan marker; no buying/requesting/contact/registration; Master Designer owns the whole 3D toolset; SP-2 retains account/access behavior; SP-1 owns the catalogue. Account-wide locale persistence remains SP-8. These are not new questions.

Fixture assumptions and limits: neutral `@prueba.local` identities and catalogue values are mock data; comparison/language are in-memory; recovery restores the local fixture; Mi cuenta is the demonstrated signed-in origin; forms never submit credentials. The final HTML intentionally retains its selected-source r4/B/Draft inspector label. No separate preview is created because preview is unset/off and only the canonical pair is assigned. Missing live catalogue integration is expected implementation work, not evidence of a working backend. Full origin-return behavior and session/permission invariants must be checked against production by T14.4/T94.

**CONCERNS:** Draft remains unapproved; independent approval is still required. Actual offline audit: **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems** (288 renders, exit 0); contrast: 158 pairs, all pass. No fallback/toolchain concern remains. Real catalogue integration, arbitrary originating-page return, authentication, server permissions and assistive-technology conformance are not established by this static mockup and remain assigned implementation/integration checks. No material design question is unresolved.
