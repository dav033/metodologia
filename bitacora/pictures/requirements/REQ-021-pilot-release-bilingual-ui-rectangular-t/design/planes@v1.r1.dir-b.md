---
contract: planes
version: 1
status: draft
kind: exploration
subplan: SP-14
requirements: [R17, R18, R19, R20]
direction: b
revision: 1
name: Índice y paneles
owner: David
author: Designer
date: 2026-10-27
---

# Índice y paneles — spatial direction B

Complete **draft exploration**, not an approved contract or an implementation instruction. The owner has not selected this direction. Only the six assigned revision-specific design files are produced. No canonical `planes@v1.md` / `planes@v1.html`, repository, plan, shared contract or other project log is written.

## Approach and the existing surface

The question is “What does each access plan include, and what is its monthly price?” A continuous document answers it without a checkout, request, contact, sign-up or plan-changing control.

Preserve the existing Pictures/Sempertex ring-and-dot masthead, language control, account disclosure, 24px task heading, rounded working paper, form axis and footer from the chosen **Parte de acceso** sibling. The changed area is a single paper with a **price index and tool document**, using the sibling role-list/editor composition rather than a promotional card grid. The public page has no account menu. The signed-in fixture is an Entusiasta account; it adds no staff/custom role or permission-key content to the section.

The four price anchors stay in catalogue order at the left of desktop content. The right side contains all four full tool lists, separated by rules; no benefits are hidden behind plan selection. The price index stays available while scrolling. On a phone, the same index becomes four compact rows above the complete tool document. This is a new `/planes` route inside the existing product shell, not a new identity or landing page.

Both entry surfaces remain recognizable: the login form retains its invitation-only explanation, email/password fields, entry action and administrator-reset guidance; the account menu retains identity, Mi cuenta and sign-out. Each gains exactly one **Planes / Plans** link. The account view is a neutral, simulated source fixture, not additional SP-14 account behavior.

## Two thumbnails and the choice

- **Chosen: `planes@v1.r1.dir-b.html.candidate-1.html`.** A lateral price index beside every full tool list. It exposes all four plan names/prices immediately and keeps cumulative tools readable together.
- `planes@v1.r1.dir-b.html.candidate-2.html`. A top shelf of four prices above one focused inspector. It is a viable spatial composition, but conceals the other tool lists behind selection. It is weaker for this explicit comparison job and was not developed.

The two standalone compositions were written before the complete TSX and generated HTML. Thumbnail 1 is the design source for the full direction; the complete artifact, not the thumbnails, carries the audited behavior and motion.

## Eight axes

| Axis | Observable direction |
|---|---|
| concept | A continuous plan document with a spatial price index: compare the four monthly prices while reading every cumulative tool list. |
| layout | One shared rounded paper, a sticky 264px plan index at left and ruled tool sections at right; one column below 761px, with all four price rows before the tool document. |
| navigation | Four real in-page anchors in catalogue order; an active location follows scroll, anchors focus the corresponding heading, and return links restore the originating entry focus. Existing login and account disclosure each gain one Plans link. |
| typography | Existing embedded Geist Sans and Geist Mono only; 24px page title, 20px section names, 24px desktop / 20px phone prices, 14px tools, 12px availability and cumulative labels. |
| density | A calm index of 100px desktop rows / 72px phone rows beside compact two-column tools at 1101px and above; single-column tools at narrower widths. No feature carousel or collapsed benefits. |
| components | Installed shadcn Button, Input and Skeleton; native account details and language select retained; custom anchor index and ruled sections recompose the sibling role-list/editor vocabulary. |
| colour | Unchanged Pictures light/dark tokens. Neutral secondary fill locates the reading position; source accent appears on links and focus. Availability remains explicit muted text with a distinct outline icon. |
| motion | Expressive spatial springs move the index marker between anchors, settle the document from -8px and sections from 26px with 63ms offsets; rules extend from 80% width over 500ms. Hover arrows move 4px over 180ms; reduced motion and still mode keep every destination and final layout without travel. |

The JSON contains live selector evidence for layout, navigation, typography and motion. Every selector was found in the default rendered public view. Motion evidence was measured with motion enabled, not inferred from class names.

## Existing tokens, typography and real components

Production `src/app/globals.css` is the color source. The accounts/proyectos/taller sibling contracts and bundled HTMLs were read; the accounts chosen direction governs shared non-workshop chrome. The production font binaries already available in t12's Next build are embedded by the offline builder, with their same **Geist Sans / Geist Mono** families. No asset is fetched. No new palette, font family or identity is proposed.

| Project source | Mockup / kit role | Light / dark |
|---|---|---|
| `--fondo` | background | `#faf9fc` / `#0b0c10` |
| `--superficie` | card, popover | `#ffffff` / `#16181f` |
| `--texto` | foreground and surface foregrounds | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | muted foreground | `#6b6178` / `#9aa1ad` |
| `--superficie-2` | secondary, muted, neutral index marker | `#efe9f8` / `#242733` |
| `--superficie-suave` | index hover | `#faf8fd` / `#1c1e26` |
| `--acento` / `--sobre-acento` | primary / primary foreground | `#6d3fe0` / white; `#9479ff` / `#120b24` |
| `--borde`, `--borde-suave` | decorative boundaries / rules | `#e3daef`, `#efe9f8` / `#383c48`, `#2a2d38` |
| `--texto-tenue` | meaningful control edge (sibling accessible alias) | `#766c85` / `#8a91a0` |
| `--error`, `--error-suave` | account error notice | `#b23a45`, `#ffeaec` / `#ff979f`, `#43252a` |
| `--sombra` | floating account disclosure only | existing source shadow in each theme |

Other semantic roles retain the accounts mapping to existing success/warning/error/accent source values. Source color is mapped once per theme; decorative borders are not used as the only identifying edge of input controls. The shared selected shape vocabulary is preserved: panel 32px, inset 24px, field 18px and pill 999px. Shell padding is 40px desktop, 28px intermediate and 20px phone; paper padding 28px / 20px. Page title 24px, section names 20px, tool text 14px and supporting copy 12–13px. Phone currency units are 11px. Numbers use tabular figures.

| Real component / state | Import or honest custom composition |
|---|---|
| `shadcn:button default / outline default, hover, focus, disabled, pending` | `@/components/ui/button`; existing pill action composition |
| `shadcn:input email / password default, focus, disabled, validation` | `@/components/ui/input`; unchanged account/login fixture vocabulary |
| `shadcn:skeleton plan-index / tools loading` | `@/components/ui/skeleton` |
| `native:select language ES / EN` | Associated visible label; existing header control |
| `native:details account closed / open` | Existing non-modal disclosure; no fabricated ARIA menu |
| `custom:plan-index anchor normal / current / hover / focus` | `.plan-index`, `.index-item`, real anchors with `aria-current="location"` |
| `custom:plan-document cumulative normal` | Four semantic sections, headings and lists; `.plan-document`, `.plan-section` |
| `motion:spatial-marker / section / rule` | `motion/react`, shared marker and profile-scaled transitions |

Runtime imports `mountMockup` / `useMockup` from `@kit/mockup` and `useMotionProfile` from `@kit/motion`. Installed real components were used; no fallback snippets, package installation or external asset requests.

## Navigation, information and data

### Views

| Native `view` value | Surface / entry behavior |
|---|---|
| `planes-publico` | `/planes`, signed out; four plans; no account menu; return to `/login` |
| `planes-cuenta` | Same `/planes`, signed in; same plan data; account menu present; source fixture is `/cuenta` |
| `login` | Chosen login composition with exactly one added `/planes` link |
| `cuenta` | Chosen own-account composition, representative fixture; account menu has exactly one `/planes` entry |

The language control initially follows browser language: Spanish → COP, English → USD, then changing ES/EN updates all plan names/prices/tools together. English Entusiasta is **Enthusiast**. Free remains **Gratis / Free**, without a price amount. No simultaneous currencies, numeric chat limits, counters, plan-assignment control, staff/custom roles, or permission keys appear in the plan document.

All displayed names, prices, tools and availability come from one explicit mock fixture. Prices are the requirement's exact COP 20,000 / 45,000 / 70,000 and USD 7 / 14 / 25 per month. The production catalogue path `src/lib/planes/catalogo.ts` is not yet present in the inspected worktrees; production must replace this fixture with `plan-catalogue@1`, without another page-owned catalogue. This exploration does not verify catalogue propagation or authorization.

Each section lists its complete effective tool set. Designer's higher-limits wording replaces the basic chat wording, rather than claiming two separate usable chats. Designer Plus and Master Designer each repeat the unavailable lines **Chat ampliado / Extended chat**, **Detección de estructuras / Structure detection** and **Detección avanzada de globos / Advanced balloon detection**, each with **aún no disponible / not available yet**. The calculator is available under Plus and Master. Master adds only the **Taller 3D / 3D workshop** line for the whole editor, including the decorations explorer; there is no separate explorer benefit. The base **Catálogo / Catalogue** line follows current SPEC's base grants and is identified as an owner question below.

Clicking an index anchor scrolls to and focuses the matching heading. All sections remain rendered. Scroll updates the current location independently of account access. A plan anchor is navigation, never an entitlement selection. Keyboard Tab reaches each link; Enter activates it. Return restores focus to the login Planes link or the account disclosure. In production, preserve the actual safe same-origin source page when entering from its account menu; `/cuenta` is this mockup's example source. The direct signed-in entry fallback is still an explicit question.

### States

The visible native `state` selector reaches `normal`, `cargando`, `vacio` and `error`. Native `view`, `theme` and `motion` controls retain the runtime's labels **Vista, Estado, Tema, Movimiento** and **Mockup** label. There is no dialog and therefore no `scene` selector.

| State | Plan section behavior / recovery |
|---|---|
| normal | All four ordered prices and all tool lists; successful read, no mutation-success state |
| cargando | Shape-matched index/tools skeletons and localized loading status; `aria-busy`; no guessed prices |
| vacio | Explicit “No hay planes disponibles.” / “No plans are available.” and Retry; never a valid zero-plan comparison |
| error | Localized catalogue-load refusal and Retry; no stale or incomplete tiers presented as authoritative |

Retry returns to the normal mock fixture only; it performs no request. Empty, partial, invalid and offline catalogue responses must fail closed in implementation, without pretending fewer plans are the catalogue. An incomplete catalogue maps to the error presentation. “Success” means a complete successful read, so no separate confirmation screen is useful. Purchase, request, assignment, permission-denied, quota, numeric-limit and contact states are inapplicable. The public route requires no permission. Login/own-account forms are simulated sibling fixtures; SP-2 remains their behavior owner.

## Responsive interaction and motion

- **1101–1519px:** 264px sticky price index, 40px divider gap, flexible document with two-column tools. All four index names/prices remain together. At 1520px and above the index becomes 288px and the gap 48px within the existing 1520px shell cap.
- **761–1100px:** 232px sticky index, 28px gap and one-column tools. Header controls wrap using the same sibling behavior.
- **Up to 760px:** 20px outer/paper padding, non-sticky index of four 72px-minimum rows with prices aligned right, then one-column tool document. No horizontal strip, swipe-only control, hidden plan or side inspector. Account identity hides its inline role suffix as in the sibling and retains it inside the disclosure.
- Measured widths are **390, 768 and 1280px**. Full browser zoom, screen-reader reading and deployed rendering are not attested by these mockup checks.

The direction's memorable detail is a **shared neutral reading marker** that travels between index entries as the reader moves through the document. Motion does not imply a chosen or assigned plan. The full paper settles from -8px; four sections settle horizontally from 26px in the expressive profile, staggered by 63ms. Spring stiffness 220, damping 16, mass .9 comes from `useMotionProfile`; natural/subtle use their installed profile springs and shorter distances. Section rules extend from 80% to full width over 500/300/160ms. Repeated controls use the source's 180/140/100ms timing and spatial ease `cubic-bezier(.22,1,.36,1)`; arrows move 4px on hover. Content remains legible during travel.

Reduced-motion preference, Quieto and `?still=1` remove travel, repeated skeleton effects and animated scrolling while preserving every destination, current-location cue, tool, retry and focus outcome. Hidden-tab CSS animations pause; offscreen repeating child effects pause. No background animation, parallax, autoplay carousel or perpetual decorative animation is added. In the measured normal view, finite Motion transforms settle and still mode has zero running animations.

## Accessibility and provisional visual acceptance

Targets: WCAG 2.2 AA for applicable content, text ≥4.5:1 (large text ≥3:1), meaningful control edges/focus ≥3:1. Anchors and form controls are native, lists are semantic, headings are associated with sections, icons are decorative and unavailable tools have text labels. Focus uses the shared 3px source-accent outline with 4px offset. Main actions/entry targets are at least 44px high. Loading/error feedback uses status/alert semantics. These are targets supported by the measurements below, not a claim of complete WCAG conformance.

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| SP14-B-01 | 390, 768, 1280px | normal, ES | Four ordered plan names and Gratis / 20.000 / 45.000 / 70.000; only COP monthly units |
| SP14-B-02 | 390, 768, 1280px | normal, EN | Enthusiast / Designer / Designer Plus / Master Designer; Free / 7 / 14 / 25; only USD monthly units |
| SP14-B-03 | 1280px | normal | Sticky index occupies the left pane and full tool sections remain visible in the right document |
| SP14-B-04 | 390px | normal | Four compact price rows precede all single-column tool lists without horizontal page scrolling |
| SP14-B-05 | all measured widths | normal | Three unavailable-tool labels appear in each of Plus and Master, with the required localized availability copy |
| SP14-B-06 | all measured widths | normal | Entusiasta and Designer chat descriptions have no numerical limit values |
| SP14-B-07 | all measured widths | normal | Master has one Taller 3D line and no separate decorations-explorer line |
| SP14-B-08 | all measured widths | login / menu | Exactly one Plans link on each entry surface opens the corresponding public/signed-in plan view |
| SP14-B-09 | all measured widths | normal | Index activation focuses the matching section heading; Return restores the source entry focus |
| SP14-B-10 | 390, 1280px | loading / empty / error | Every native state selection reaches a localized, measured presentation with the specified recovery |
| SP14-B-11 | 390, 1280px | light / dark | Foreground/control/focus measurements meet the audit thresholds without theme-specific font or palette changes |
| SP14-B-12 | 1280px | expressive / reduced | Section and marker travel is observable with motion on; still mode has no running animations and retains all content |

## Verification and honest limitations

Final generated snapshot was built with the real installed workspace: **550 KB, 2031 source files, offline**. Commands used the assigned absolute paths. Both required tools were run on **`planes@v1.r1.dir-b.html`**, not the canonical output.

- Offline builder: exit 0.
- `contrast.py`: exit 0 — **158 pairs checked in light and dark, all pass**.
- `audit_mockup.py`: exit 0 — **64 renders / 64 planned combinations**, **1,536 text measurements**, **178 focus stops**. Includes every native view/state/theme combination at 390 and 1280px, plus motion/reduced-motion checks.

```text
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

- Supplemental browser checks: **24 localized normal-plan renders**, **12 open account menus**, **24 entry/return flows** across **390/768/1280px**, both languages and both themes. Verified browser-language initialization, exact names/prices, single currency, all six unavailable labels, public/account-menu separation, both `/planes` entry links, destination-heading focus, restored return focus, no runtime exceptions and no external requests. Source audit layout/contrast probes report zero findings in these localized normal/menu states.
- Motion/selector probe: all JSON selectors resolve in the default rendered view; a section's measured transform changes from `matrix(1, 0, 0, 1, 26, 0)` to `none`; hovered arrow translation is 3.59px during its 4px travel; `?still=1` has zero running animations; zero runtime errors.
- Visual inspection: in-memory screenshots at 1280 and 390px in light/dark, with Spanish and English examples, and the 390px login entry. No screenshot files were created outside the assigned output list.

The first supplemental test found focus loss after plan-anchor navigation because a locally declared React component remounted its DOM. It is fixed by stable render helpers; the final focus checks pass. An intermediate field-hoisting edit left an outer-scope reference; the supplemental test caught the runtime failure, it was fixed, and the final complete checks were rerun. The shared audit printed PASS during that intermediate runtime failure because an empty `#app` survived; that result was rejected, not used as acceptance. The final 64-render audit above was rerun against the corrected populated views and backed by runtime/content assertions. Strengthening the toolkit's empty-root/runtime guard is an out-of-scope follow-up.

No production lint, build, backend tests, catalogue edit propagation, database, real account authentication, deployment, full screen-reader session, full zoom matrix or owner approval is claimed. No source repositories were changed and no commit/push/deploy was made. The canonical pair remains absent and untouched.

## Open questions and assumptions

**Q1 — Owner:** Should **Catálogo / Catalogue** appear as a public included-tool line in all four plans? Current SPEC keeps it in the base grants, whereas the behavioral brief does not explicitly name the line. This mockup includes it visibly and leaves that decision open; it does not add a new capability.

**Q2 — Owner / Planner:** On a direct signed-in visit to `/planes` with no source page, should Return open **Mi cuenta**? The mockup uses Mi cuenta as its source fixture. Normal entry from an account menu must return to the actual originating safe page, as the brief requires.

Confirmed: exactly four cumulative tiers; free Enthusiast; language-specific currency; no purchase/request/sign-up or plan mutation; no numeric chat limits; the three unavailable tools marked in both top tiers; whole editor/explorer inside Master's Taller 3D line. Numeric chat-limit values are deliberately deferred and are not a question for this exploration. Shell/entry forms and account menu remain SP-2-owned.

Assumptions: catalogue-load/empty/error copy is provisional functional copy, not a new marketing claim; the illustrative source account and forms only allow inspection of the two plan entry points. SP-1 must supply authoritative localized catalogue records before implementation. Any owner choice or subsequent finalizer must resolve Q1/Q2 and write the canonical twelve-section contract; this artifact does not approve itself.

## Source snapshots

The shared behavioral source governs scope; SPEC/PLAN provide only supporting context. Fingerprints captured when closing this exploration:

| Read-only source | SHA-256 |
|---|---|
| `design/planes@v1.r1.behavior.md` | `15d876a533b5c4f184f022dc07071ef93bb2ca8c90e83a01a8b84961d2fbc07f` |
| `design/cuentas-admin@v1.md` | `465f35b2da29f91f4b024ef82d1b6fa71c9a60824462b97ee5ca55dfc370b1b5` |
| `design/taller-esenciales@v1.md` | `50d823239d182ee1362687317d6d27823ae532282ab69c95993095023df16631` |
| `design/proyectos@v1.md` | `5dbe092fdc220552e38b68169f397af89942dab87313a397fc91c21224ef4c98` |
| `SPEC.md` | `c5ccaae83dad325ac83a7c0b02b4606ca13c0e1ade469ab47041a971ee18a9a0` |
| `PLAN.json` | `ff69d95a94c09b1799d946bda70c85d2a693a9f6772c73e0cb84f43b037c0fa6` |
