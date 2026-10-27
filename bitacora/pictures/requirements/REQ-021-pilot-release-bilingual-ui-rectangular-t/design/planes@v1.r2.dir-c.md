---
name: Pliegues de consulta
contract_candidate: planes@v1
revision: r2
direction: c
status: draft
artifact_kind: exploration
ready: true
stale: false
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
date: 2026-10-27
source_behavior: planes@v1.r2.behavior.md
source_behavior_sha256: 3f69cc0a465ac74b71a63cf247d9b1d38dbb87e0139ab13b8e52076fdf0b8239
chosen_thumbnail: planes@v1.r2.dir-c.html.candidate-1.html
---

# Pliegues de consulta — direction C, r2

## 1. Identity and traceability

**Draft exploration, complete for owner comparison; not an approved contract or implementation input.** This fresh composition addresses the already owner-selected direction C and the feedback from 14:19, `/tmp/REQ-021-planes-feedback-1.md`, and the 14:44 clarification. It does not reuse or patch a previous planes draft. Canonical files, history, plans, sibling contracts and project repositories remain untouched.

Scope is `planes@v1.r2.behavior.md`, R17–R20, and SPEC “Behavior — SP-14 extra view (round 13 answered)”. The extra view only selects/highlights for comparison; no purchase, request, sign-up, account assignment, permissions change or limit values. All tools stay visible. Round 13 is answered and is not reopened here.

Read-only product evidence: both t12 and asesor `globals.css`; t12 `layout.tsx`, login page/LoginForm, CabeceraApp and MenuApp. Sibling canonical Markdown and HTML for cuentas-admin, taller-esenciales and proyectos were inspected. Current cuentas-admin **Parte de acceso** supplies the masthead, native language/account controls, neutral horizontal navigation, rounded working sheets and access axis. The production palette and Geist fonts govern where older sibling HTML explorations differ from their written token mappings. No production plan catalogue file exists in the inspected worktrees yet; the fixture derives only from the shared brief. Production must read SP-1's catalogue, not copy this fixture as a second owner.

Only SP-14 consumes `ui.contract=planes`, version 1: T14.1 copies the subsequently approved contract, T14.2 implements comparison/selection, T14.3 adds entry links, T14.5 reviews. T14.4 is the integration verification consumer. Relative to the earlier requested behavior, the selection view and tablet reflow require implementation adaptation (breaking visual/interaction change); tokens and entry-link destinations are compatible. SP-1 data ownership and SP-2 account behavior are unchanged. This note neither redirects consumers nor approves a contract.

## 2. Purpose and users

Public visitors and signed-in people compare four cumulative plans, prices and tool availability. Successful consultation means every plan can be read without authentication and without collapsed lists. A separate view lets the visitor choose one comparison highlight and return to all four plans. “Un administrador asigna el plan” / “An administrator assigns the plan” explains account assignment without offering it.

Neutral account data is explicitly mock: Cuenta Entusiasta / Enthusiast account, `entusiasta@prueba.local`, Empresa de ejemplo. Account-entry forms reproduce the sibling context only; their submissions show a mock boundary notice and send no data. This is not account-service verification.

## 3. Approach, hierarchy and chosen thumbnail

The existing product gains **open consultation sheets**, not a marketing landing page. Each desktop sheet puts the plan name and monthly price at the left fold and its complete tools at the right. “Pliegues” describes the sheet's settling gesture; it never means a collapsed tool section. The additional selection view recomposes the same content as two-by-two peer sheets with a pressable comparison control. No factual catalogue content is editable.

Two thumbnail HTMLs were created **before** the full TSX and rendered at 1280px. **Candidate 1 was chosen:** horizontal sheets expose all four plan headers in a compact vertical scan and align identities against the tool area. Candidate 2 uses two-by-two sheets even on desktop; it is retained as visual evidence but gives up that comparison axis. The full version uses candidate 1 for comparison and the peer-sheet arrangement for the explicitly separate selection view.

| Axis | Rendered expression |
|---|---|
| Concept | Press/select a comparison highlight directly on open plan sheets; catalogue data remains read-only. |
| Layout | At ≥1100px, four full-width sheets with 248px identity columns and two-column lists. Tablet comparison and desktop/tablet selection use two-by-two sheets; phone uses a single stack. |
| Navigation | Existing masthead/account disclosure; neutral Compare / Select links; four plan jump anchors in comparison; explicit return to full comparison and original entry surface. |
| Typography | Existing Geist Sans and Geist Mono from local production WOFF2 files. H1 24px, plan headings 20px, prices 22px/tabular, tools 14px, context/availability 12–14px. |
| Density | Content-sized open sheets with 28px desktop, 24px tablet and 20px phone insets, 16px gaps, existing 32px panel and pill shapes. Tablet lists have a full text column per plan. |
| Components | Installed shadcn/Base UI Button, Input, Skeleton; native selectors/account disclosure; semantic links/articles/lists; Lucide checks/arrows. No toolkit fallback. |
| Colour | Exact Pictures light/dark tokens; neutral chrome, acento on actions/selection and aviso on unavailable labels. No palette, font or identity replacement. |
| Motion | 440ms open/settle, 45ms sheet offsets, existing ease-out, interruptible press spring and selected-label stamp; 180ms controls. Natural/subtle reduce timings; reduced/still preserves all content without travel. |

## 4. Fixed design system and interaction detail

| Pictures tokens | Kit roles | Light / dark |
|---|---|---|
| `--fondo`, `--superficie` | background, card/popover | #faf9fc / #0b0c10; #ffffff / #16181f |
| `--texto`, `--texto-suave` | foregrounds, muted-foreground | #1c1425 / #f4f5f7; #6b6178 / #9aa1ad |
| `--superficie-2` | secondary, muted, accent | #efe9f8 / #242733 |
| `--borde`, `--borde-suave` | border, decorative rules | #e3daef / #383c48; #efe9f8 / #2a2d38 |
| `--texto-tenue` | input/control edge, as siblings | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primary/ring, primary foreground | #6d3fe0 / #9479ff; #ffffff / #120b24 |
| `--error`, `--aviso` | destructive, availability warning | #b23a45 / #ff979f; #8f5f12 / #f7c46b |

Existing source `--ease-out: cubic-bezier(.23,1,.32,1)` drives the sheet unfolding and settling. The expressive gesture moves 12px and rotates −3° to +0.4° to settled over 440ms; stagger 45ms. Selection uses the installed Motion spring from `useMotionProfile`; pointer press compresses to .965 and moves 2px, then settles on release. A selected label stamps into place while the selected border remains explicit. Default content opacity never falls below .8 during sheet entrance. Control hover/press lasts 180ms; natural 140ms, subtle 100ms. Natural sheet timing 280ms/25ms offsets; subtle 160ms/12ms. The gesture is interruptible; nothing waits for animation to become usable. Reduced motion or `?still=1` removes animation/transition and keeps selection labels, borders, focus and all tool text. Hidden tabs pause CSS animation; there is no perpetual decorative animation or render loop.

Source components: `shadcn:button outline/default default|hover|focus|pressed|selected|disabled` from `@/components/ui/button`; `shadcn:input email/password default|focus` from `@/components/ui/input`; `shadcn:skeleton sheet loading` from `@/components/ui/skeleton`. Custom composition: `.plan-sheet` = semantic article + heading/price + full semantic list, not a fake accordion. Native selectors carry Vista/Estado/Tema/Movimiento, outside the product, and Idioma inside it. There is no dialog axis because no dialog is declared. The runtime's **Mockup** label remains visible.

## 5. Navigation and interaction model

- `/login`: retain SP-2's centered access panel, fields, sign-in action and recovery copy; add exactly one “Planes” / “Plans” link to `/planes` beneath the existing form. Its form is illustrative; authentication remains SP-2-owned.
- Shared account disclosure: retain identity, Mi cuenta and Cerrar sesión, adding exactly one `/planes` link. The menu-entry view is shown over the existing Mi cuenta context, not a new navigation hub. Escape and outside click close it; Escape returns focus to its summary.
- `/planes`: signed-out has no account menu; signed-in retains it. Neutral in-page navigation offers “Comparar planes” and “Seleccionar para comparar”. The latter is represented as `/planes?vista=seleccionar`; this is a local view, not a new acquisition route.
- Four hash anchors scroll/focus the named sheet in full comparison; no anchor filters/hides any other plan. The selection view preserves all four sheets and their lists. Each selection button has `aria-pressed`; only one sheet is highlighted at a time. “Volver a la comparación completa” returns without changing order or hiding the other plans. Selection is transient, in memory only; it never stores an account field, persists a preference or sends a request.
- Back returns to the originating entry surface in the mock (login or Mi cuenta). Production retains the actual validated same-origin return location from the caller; direct signed-out opening falls back to login, and direct signed-in opening to Mi cuenta. Browser Back remains available.

## 6. Flows

1. Signed out: choose the access view → activate its Plans link → read all four sheets → enter Select to compare → press any plan → return to full comparison with that sheet highlighted → return to access.
2. Signed in: choose the account-menu entry view → follow Plans → compare/select as above → Back returns to Mi cuenta. The account fixture remains Cuenta Entusiasta throughout, even when Master Designer is highlighted.
3. English: initial browser language starting `en` selects English; other initial languages use Spanish. Idioma changes the same catalogue fixture between ES/COP and EN/USD, preserving the comparison highlight. Free becomes Free and Entusiasta becomes Enthusiast. Production language resolution composes with SP-2; no alternate currency selector exists.
4. Catalogue loading/empty/error/offline: use the visible Estado selector. Loading displays skeleton sheets and a loading announcement. Empty/error/offline display a specific explanation and Retry; mock Retry restores normal fixture data. No fabricated partial catalogue is presented as a successful comparison.

## 7. Views and catalogue content

| Native Vista option | Product context | Content |
|---|---|---|
| `compare` | /planes, signed out | Four complete open sheets, comparison anchors, return to login, no account menu. |
| `compare-signed` | /planes, signed in | Same sheets plus existing account disclosure and return context. |
| `select` | Extra view, signed out | All four full lists, one pressable highlight per sheet and return to full comparison. |
| `select-signed` | Extra view, signed in | Same informational selection; account identity unchanged. |
| `login` | SP-2 access entry context | Existing access axis plus exactly one Plans link. |
| `menu` | SP-2 Mi cuenta entry context | Existing account-menu pattern plus exactly one Plans entry; underlying form is a scope-marked illustrative sibling context. |

Order and prices: Entusiasta/Enthusiast Gratis/Free; Designer 20.000 COP / mes or 7 USD / month; Designer Plus 45.000 COP / mes or 14 USD / month; Master Designer 70.000 COP / mes or 25 USD / month. Exactly one language/currency is rendered at a time. Free has no misleading zero price.

Tools are fully repeated to communicate cumulative inclusion: Entusiasta lists Chat con límites and Contador de globos; Designer lists Chat con límites más altos and the same counter. Designer Plus adds Calculadora de costos, Chat extendido, Detección de estructuras and Detección avanzada de globos. The last three listed here (extended chat, structure detection, advanced balloon detection) carry the explicit “aún no disponible” / “not available yet” text. Master Designer repeats that list and adds Taller 3D, which includes the ready-made decorations explorer without a separate explorer line. There are 17 tool rows and six unavailable labels across the four sheets. Availability follows the current shared brief; inconsistent older SPEC history is not used as a second authority. No numeric chat limits, staff roles, custom roles, permission keys, marketing claims or account mutation controls appear in the plans section.

## 8. States

| Estado | Rendered effect / recovery |
|---|---|
| Normal | Complete four-plan fixture; no initial highlight in a fresh document. A previously chosen in-memory highlight remains during navigation. |
| Plan resaltado | Makes an illustrative Designer Plus highlight reachable without interaction; a real selection takes precedence. This is comparison feedback, not an assigned-plan success. |
| Cargando | Four skeleton sheets, `aria-busy`, loading status. No guessed prices or actionable selection controls. |
| Catálogo vacío | “No hay planes disponibles” / “No plans available”, brief retry guidance and Retry. No free-tier fabrication. |
| Error | Alert “No se pudieron cargar los planes” / “Could not load plans”, retry guidance and Retry. |
| Sin conexión | “Sin conexión” / “Offline”, reconnect/reload guidance and Retry. No stale prices advertised as current. |

The six-state selector applies to catalogue views. Account/login entry snapshots retain their normal forms because their loading/error/validation/permission states belong to SP-2 and are not redefined here. Not applicable to SP-14: permission-denied (public page), account mutation success, purchase pending, sign-up validation and destructive confirmation. Unavailable tools are informational text, not disabled acquisition buttons. No partial/stale catalogue state is invented; an unconfirmed/partial catalogue must use the error treatment pending authoritative data.

## 9. Responsive behavior

| Width | Full comparison | Extra selection view |
|---|---|---|
| 390–639px | Single column, every list single-column, 20px outer/sheet insets; plan anchors wrap in pairs; header controls use a second line; footer stacks. | Single column; selection below name/price; full-width return action; all tool labels wrap. |
| 640–1099px | **Explicit tablet rule:** 2×2 sheets in row-major catalogue order; 24px outer/sheet insets; name/price above a full-width one-column list. No four squeezed desktop columns, carousel or horizontal table. | Same 2×2 grid; selection below identity; tool lists never collapse. Header wraps when needed. |
| ≥1100px | Four full-width horizontal sheets; identity 248px, remaining area a two-column tool list, 28px sheet/40px outer insets, max app width 1520px. | Two-by-two peer sheets with one-column tool lists and comparison controls adjacent to identity when space allows. |

Entry forms retain the sibling 676px outer/620px inner form axis, 28px desktop and 20px phone insets, heading and stacked footer aligned to that axis. No fixed sheet height or clipped tool text. Reading order is DOM order at every breakpoint. Reflow was tested at 390, 639, 640, 768, 820, 1024, 1099, 1100 and 1280px.

## 10. Accessibility targets and evidence boundary

Target WCAG 2.2 AA: semantic headings/articles/lists/navigation; native links, selectors and disclosure; explicit focus outline of 3px acento with 4px offset; ≥44px controls; selected state conveyed through text/check/`aria-pressed`, not colour alone. Unavailable status is literal text associated with the tool label. Tab/Enter/Space operate controls; changing view focuses H1; hash links focus the relevant sheet; selection keeps focus on its control; Escape returns to account disclosure. Status selection uses a polite live region; catalogue error uses alert. Reduced-motion feedback is immediate and complete.

Contrast target is ≥4.5:1 body text and ≥3:1 meaningful control boundaries/focus. Both themes map dark primary foreground to #120b24, preserving the production contrast rule. Automated audits supplement rendered screenshot/interaction checks; they do not establish full assistive-technology conformance, production catalogue integration or real account authorization. Screen-reader announcement quality and 200–400% browser zoom were not manually tested in this delegation.

## 11. Visual acceptance criteria and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-AC-01 | ≥1100px | normal | Four horizontal sheets appear in catalogue order, each with name/price in a left 248px column and all tools to the right. |
| C-AC-02 | 640–1099px | normal | Comparison is a row-major 2×2 grid with single-column tool lists and no horizontal page scrolling. |
| C-AC-03 | 390–639px | normal | Four sheets stack in order; every tool and availability label wraps within 20px sheet insets. |
| C-AC-04 | All supported | normal / selected | No show/hide-tools control or collapsed tool list exists. |
| C-AC-05 | All supported | normal ES | Prices are Gratis, 20.000, 45.000 and 70.000 with paid prices labelled COP / mes; USD does not appear. |
| C-AC-06 | All supported | normal EN | Enthusiast is Free; paid prices are 7, 14 and 25 USD / month; COP does not appear. |
| C-AC-07 | All supported | normal | Each upper plan visibly includes all its lower-tier tools; the three future tools each have an unavailable label under both upper plans. |
| C-AC-08 | All supported | selecting / selected | Pressing any plan highlights exactly one sheet and announces its comparison name without changing the account identity. |
| C-AC-09 | All supported | selected | Returning to full comparison retains the chosen border/text highlight and all four complete lists. |
| C-AC-10 | All supported | loading | Four skeleton sheets and loading status appear without guessed catalogue values. |
| C-AC-11 | All supported | empty / error / offline | Specific explanation and Retry are visible; Retry restores the normal mock fixture. |
| C-AC-12 | All supported | entry points | Login and the account disclosure each contain exactly one link with destination /planes. |
| C-AC-13 | 390 / 768 / 1024 / 1280px | normal | Signed-out has no account disclosure; signed-in has the same shared disclosure and no staff/custom-role or permission-key exposure in /planes. |
| C-AC-14 | All supported | any catalogue state | No purchase, request, contact, sign-up, numeric limit or account-plan assignment action is rendered. |
| C-AC-15 | All supported | keyboard | Tab shows visible focus, native activation works and Escape dismisses account disclosure with focus restored. |
| C-AC-16 | All supported | expressive / reduced / still | Sheet settling/press feedback animates in expressive mode; reduced/still keeps settled content and selected feedback with no movement. |
| C-AC-17 | Desktop/tablet | access entry | Access heading, panel and stacked footer share the sibling 676px axis; the added Plans link follows the unchanged form. |

### Actual offline verification

- Real builder: PASS, self-contained 547 KB HTML, 2,031 source files bundled offline from the installed workspace. Entry imports `mountMockup`, `useMockup` and `useMotionProfile`; no fallback or package install.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass`.
- Required `audit_mockup.py` against this revision-specific output, widths `1280,390,768,1024`: **288/288 renders, 7,456 text measurements, 456 focus stops**; no sampling. The default browser locale is English. Exit 0.
- Second run of the same audit with Playwright `Browser.new_page(locale="es-CO")`, same four widths: **288/288 renders, 7,456 text measurements, 456 focus stops**. Exit 0. This wrapper changes only browser locale; it does not edit the audit or skip checks.
- Both actual audit result lines: `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- Additional offline Playwright exercise: **240 assertions PASS** across ES/COP and EN/USD, selection of every plan signed in/out, 17 visible tool rows, six unavailable labels, entry links, full-comparison return with highlight, unchanged account identity, account Escape/focus, nine viewport widths, expressive/still behavior. Zero HTTP requests and zero page errors observed. This ran before the final access-only footer stacking/context-row correction; the final audit covers those rendered changes. It is not production authorization verification.
- Selector evidence: PASS using the comparison tool's actual EVIDENCE probe across every declared view. All 16 selectors match visible elements; motion selectors animate or transition. Computed product typography is Geist.
- Screenshots inspected: both candidate compositions at 1280px; complete comparison/selection at 768px; selection at 390px dark; full comparison at 1280px dark; access at 1280px light and account-entry at 1280px dark. They show open readable lists, working-sheet geometry and the shared product shell. Ephemeral screenshots/logs are under `/tmp/planes-c-*`; they are evidence, not additional project artifacts.

Initial audits reported six access-axis alignment findings, then two residual footer findings. The heading and footer were aligned to the sibling form axis and the footer stacked; the final two locale audits above are clean. No checks were suppressed, and no production edit or generated-HTML patch was used.

## 12. Open questions, assumptions and impact

**Open owner questions: none.** Round 13 explicitly resolves comparison-only selection. Direction/plan approval remains with David; this draft grants no approval. The finalizer may consume this revision-specific exploration only after the owner's selection/approval flow.

Confirmed: direction C; public/informative behavior; four complete lists; ES/COP and EN/USD; comparison-only extra view; no per-plan disclosure control; tablet-specific readable layout; SP-1/SP-2 contracts unchanged. The in-memory selection and `?vista=seleccionar` are proposed navigation mechanics within this direction, not new account behavior. On refresh the highlight resets. Initial language uses browser language; the native selector demonstrates both languages.

The static account/login forms illustrate only entry-link placement. Password validation, real authentication, account menu destinations and account service operations remain the exact SP-2 contract's responsibility. Production catalogue integration, permission invariance and deployed behavior require T14.4; this offline fixture cannot prove them. Production tests/build/lint were not run because no production code is in scope. Full screen-reader/zoom acceptance remains for the implementation review.
