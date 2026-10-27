---
contract: planes
version: 1
revision: r1.dir-c
status: draft
artifact: independent-direction-exploration
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
date: 2026-10-27
name: Pliegues de consulta
chosen_thumbnail: planes@v1.r1.dir-c.html.candidate-2.html
---

# Pliegues de consulta — direction C

## 1. Identity and traceability

This is a completed independent exploration, **draft and unapproved**. It does not create or replace `planes@v1.md`, `planes@v1.html` or a canonical implementation contract. Owner selection and later finalization are separate. Scope: `planes@v1.r1.behavior.md`, R17–R20, SP-14; context: current SPEC, PLAN and SP-14 in PLAN.json. Copy task T14.1, public plans T14.2, entry links T14.3 and independent visual review T14.5 are the affected UI consumers. No engineering tasks or production files are modified.

Read-only product evidence: t12 `src/app/globals.css`, `layout.tsx`, `login/page.tsx`, `login/LoginForm.tsx`, `CabeceraApp.tsx` and `MenuApp.tsx`; asesor is the second product source. The selected/finalized `cuentas-admin@v1`, `taller-esenciales@v1` and `proyectos@v1` Markdown and HTML were inspected as shared surface inputs. The selected SP-2 Parte de acceso masthead, centered form axis, copy and shapes take precedence over the older production password-only login and exploratory sibling styling. The entry reuses the exact SP-2 r13 CSS foundation, production font asset imports and app/header structure; only scoped plan bands and entry links are added. It does not propose an alternative account design.

## 2. Purpose and users

A signed-out or signed-in person answers: which tools does each plan include, and what is its monthly price in this interface language? Success means reading four plans in catalogue order, including every unavailable feature annotation, then returning to the originating surface. There is no purchase, request, registration, contact, subscription or access-change action.

The direct-manipulation seed is applied to **presentation**: fold a list in place, reopen it, or focus a plan from the local navigation. Prices, tools and plan assignment are never editable here. This preserves the brief's informative-only behavior.

## 3. Composition, hierarchy and thumbnail choice

**Candidate 1:** a four-plan left selector and one active tool reader. It preserves a compact price comparison, but hides the other plans' tools and makes cumulative comparison depend on repeated selection.

**Chosen candidate 2:** four continuous ruled bands. Identity and monthly price stay on the left and full cumulative tool lists on the right. Every list starts expanded. Independent folding reduces repetition without removing a plan or its price. A wrapping plan index expands, scrolls to and focuses a folded destination. It keeps comparison in the same reading position, without a checkout-shaped card grid, promoted tier, tab replacement or a separate landing-page shell.

Both thumbnail compositions were drawn before building the entry and visually inspected at 1280px. They are intentionally small composition studies, not complete interactive contracts; the full TSX/HTML carries both themes, selectors, states and responsive behavior.

### Eight-axis table

| Axis | Rendered approach |
|---|---|
| concept | Pliegues de consulta: directly fold and reopen the tool lists in their original plan bands; catalogue data remains informative and immutable. |
| layout | One ruled paper with four full-width bands. Desktop bands place identity and price in a 28% left column, full cumulative tools in a two-column right region; phone bands stack identity above a single tool list. |
| navigation | Four wrapping in-page plan links expand their destination band, scroll it into view and focus its heading. Each plan has an independent disclosure. Retained login/account entry links and contextual back link. |
| typography | Existing embedded Geist Sans and Geist Mono. Fixed 24px H1, 20px plan names, 22px tabular prices (20px on phones), 14px tools and 12px availability annotations; no new font family. |
| density | Compact 24px ruled bands inside one 32px-radius paper, 28px desktop and 20px phone inset. Every tool is initially visible; folding removes its list without removing name or monthly price. |
| components | Existing Pictures masthead and native account disclosure, real shadcn/Base UI Button and Input, real Skeleton, semantic article and tool list. Button disclosures replace any plan acquisition action. |
| colour | Exact Pictures globals.css palette mapped to kit roles with sibling input-edge alias --texto-tenue. Neutral navigation and checkmarks; accent limited to existing brand, links, focus and retained access form action. |
| motion | Tactile compressed/settled bands: 480ms translateY/scaleY registration staggered by 65ms, 180ms press feedback, rotating disclosure chevrons and spring-settled tool-list reveal. Profile-aware Motion, quiet/reduced final-state parity and hidden-tab CSS pause. |

## 4. Fixed design system and component vocabulary

Reuse Pictures/Sempertex ring-and-dot masthead, language control, account disclosure, rounded centered access paper, footer and neutral ruled content. No new palette, identity, font, asset download or dependency is introduced. All font files are existing local Next assets, embedded as data URIs by the real builder.

| Product token | Kit role | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--texto` | foreground | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted-foreground | #6b6178 / #9aa1ad |
| `--superficie-2` | secondary, muted, neutral hover | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primary, primary-foreground | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--borde`, `--borde-suave` | paper edge, row rule | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | input/control edge, inherited accessible sibling alias | #766c85 / #8a91a0 |

Retain Geist Sans / Geist Mono and sibling shapes: panel 32px, inset 24px, field 18px, pill 999px. Body 15px; role-specific text sizes are in the axes table. No accent fill marks a preferred plan. Availability is readable text rather than a color or disabled action. Decorative rules are not controls.

| Component | Installed source and role |
|---|---|
| `shadcn:button outline expanded/collapsed` | `@/components/ui/button`; real Base UI Button, independent tool-list disclosure, `aria-expanded` and `aria-controls` |
| `shadcn:button outline ready` | Same import; catalogue retry and retained account actions |
| `shadcn:button default ready/disabled` | Same import; unchanged access form context only |
| `shadcn:input default/disabled` | `@/components/ui/input`; retained centered login/account form context |
| `shadcn:skeleton loading` | `@/components/ui/skeleton`; four neutral bands, no fabricated price |
| `native:details account closed/open` | Existing SP-2 account disclosure, with exactly one added Plans link |
| `native:select language/theme/view/state/motion` | Existing product language selector plus runtime inspection controls |
| `custom:plan-band` | Semantic article, heading, price, real disclosure Button and tool list; composition specific to SP-14 |
| `motion:tool-list` | `motion/react` with `useMotionProfile` from `@kit/motion`; press/settle feedback, no drag-only action |

## 5. Navigation and interactions

Runtime native inspection controls retain ids `view`, `state`, `theme`, `motion`, Spanish labels and Mockup label. No dialog is declared, so a scene selector is inapplicable. Product ES/EN changes names, tool text and monthly currency together; initial language follows an English browser or otherwise Spanish. Switching view/state in this exploration retains an explicitly selected product language.

Public `/planes`: no account menu; back goes to `/login`. Signed-in `/planes`: retains the account disclosure; back restores the origin. Mi cuenta is the illustrative originating signed-in surface in this scoped exploration. Production must retain the safe same-origin entry path rather than always force Mi cuenta. Direct signed-in entry without an origin may fall back to Mi cuenta.

In-page links expand their destination, focus its H2 and scroll with clearance for the sticky inspection bar. On reduced motion scrolling is immediate. Fold/unfold keeps keyboard focus on the same Button; collapsed content is hidden, not visually clipped while still keyboard-readable. Multiple bands can stay open. Plan state is presentation only and does not label an assigned, active or selected access plan.

## 6. Flows

1. **Public entry:** login → its sole Plans link → public plans → four expanded bands → optionally fold/reopen → Back to sign in. The login form and reset guidance retain the chosen SP-2 structure and copy; no registration control is added.
2. **Signed-in entry:** Mi cuenta → native account disclosure → its sole Plans link → signed-in plans → back → Mi cuenta. Menu identity is neutral fixture Cuenta Entusiasta / entusiasta@prueba.local, matching the account fixture. No staff role or permission key appears in the plans section.
3. **Language:** English browser → Enthusiast / Free, 7 / 14 / 25 USD per month; Spanish → Entusiasta / Gratis, 20.000 / 45.000 / 70.000 COP per month. Only the active currency is visible.
4. **Disclosure:** activate Hide tools → same band retains identity/price and Show tools → activate again or its local index link → cumulative tools return in place. Enter/Space and pointer activation have the same result.
5. **Catalogue failure:** select error, empty, partial or offline → no unconfirmed plan prices/tool comparison → retry → complete four-plan catalogue. This is a local fixture transition, not proof of a production service.

## 7. Views and content

| View selector | Surface | Visible change |
|---|---|---|
| `public` | `/planes`, signed out | Existing masthead without account menu; noun H1, contextual back, wrapping plan index, one ruled plan paper, assignment explanation and existing footer |
| `signed` | `/planes`, signed in | Same comparison plus existing account disclosure with one Plans link |
| `login` | `/login` entry context | Existing centered SP-2 access layout/copy, one added Plans link after password-reset guidance |
| `account` | `/cuenta` entry context | Existing centered account form and native account disclosure with one added Plans link; not an account redesign |

Every plan lists all its cumulative tools, rather than an inherited-benefits shorthand. One mock catalogue fixture owns names, currency prices and tool rows. Entusiasta shows Chat con límites; Designer and higher plans show Chat con límites más altos. Designer Plus and Master Designer each show Chat ampliado, Detección de estructuras and Detección avanzada de globos with the exact availability annotation. Calculadora de costos remains available per the UI brief. Master has a single Taller 3D entry encompassing the whole editor, including the ready-made decoration explorer; there is no second explorer line. Product catalogue inclusion is explicitly questioned below because it exists in the sibling fixture but is not enumerated in R16.

Available checkmarks are decorative and repeated text carries all meaning. No numeric chat threshold, promotional headline, fake proof, best-plan claim or plan-acquisition CTA appears. The account/login forms are visual context, not full authentication/reset/password-change implementations. Their simulated submission never sends credentials or writes storage.

## 8. States

| State selector | Plans behavior | Entry-context applicability |
|---|---|---|
| `ready` | Four bands expanded with full data | Ordinary login/account context |
| `folded` | Four headers/prices retained with independently hidden lists | Presentation-only catalogue state; entry context stays unchanged |
| `loading` | Four skeleton bands, Loading plans status, no price guesses | Login fields/action disabled with Working label; account context is retained |
| `empty` | Catalogue unavailable message + retry, not a legitimate zero-plan result | Not applicable to identity/form; entry context retained |
| `error` | Alert + retry, no fabricated catalogue | Illustrative SP-2 credential/account refusal; forms are outside SP-14 implementation scope |
| `offline` | Explicit connection explanation + retry | Catalogue-specific; entry context retained |
| `partial` | Fail closed on incomplete catalogue; explanation + retry | Catalogue-specific; entry context retained |
| `menu-open` | Signed-in disclosure visibly open; public page still has no disclosure | Open account menu on Mi cuenta; not applicable to signed-out login |

Success equals the normal complete comparison; no mutation-success toast exists. Disabled/loading form controls belong to retained entry context. A plan availability annotation is not a disabled plan-selection control. Permission-denied is inapplicable because the comparison is public and identical across roles. Validation is an upstream catalogue invariant: missing fields never become blank/free prices. Stale data and offline data are not silently presented as current; the partial/offline previews show a recoverable failure. No optimistic plan changes, purchase pending state or dialogs exist.

## 9. Responsive behavior

Preserve the chosen SP-2 breakpoints: **360–760px**, **761–1100px**, **1101px+**. The exploration additionally stress-tests 320px reflow.

- At 1101px+, app max width 1520px, 40px outer gutters; plan paper 28px inset; bands have 28% identity and flexible tools columns; tools have two columns, ordered row-major.
- At 761–1100px, app gutters 28px; identity at least 190px beside one tool column; wrapping local links remain above the paper. No horizontal table or carousel is introduced.
- At 360–760px, app gutters and paper inset 20px; header tools wrap; back follows H1; plan links wrap; identity precedes a single tool list. Name spans the band width, price and disclosure share the next row when possible. At 320px the disclosure stacks. Tool text and unavailable annotations wrap at safe opportunities.
- All price values use tabular figures. Currency/month wraps without clipping. Account menu fits viewport width. Vertical content scroll is expected; no sticky bottom overlay hides the final plan or footer.

## 10. Accessibility and motion

Targets: WCAG 2.2 AA for rendered product review, readable text ≥4.5:1, meaningful control edges/focus ≥3:1 and new controls ≥44px high. Native links/selects/buttons/details preserve standard keyboard operation, one H1 and sequential H2s establish the comparison; each article is labelled by its H2. Disclosure accessible names include the plan name. Loading uses a status and busy region, failure uses an alert, tool availability is visible text. Route changes focus H1; in-page jumps focus H2; disclosure toggles keep focus on their trigger. No hover-only, drag-only or color-only operation is introduced.

Motion grammar: settled compression, not a new app identity. `.plan-band` registers with a finite 480ms translate/scale settle, staggered 65ms; controls respond with 180ms press transitions and chevron rotation; the real Motion tool list reveals through a short spring. Subtle/natural/expressive profiles are wired. Quiet, OS reduced-motion and `?still=1` remove travel and animation, expose final content immediately and preserve the exact same interactions. CSS registration pauses in hidden tabs; there are no perpetual or heavy effects. Rendered audits use the settled/reduced state; a separate interaction/animation inspection is recorded below.

## 11. Observable visual criteria and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-AC-01 | 1101px+ | ready, either theme | Four ruled bands occur in catalogue order inside one paper; identity/price is beside the tool region. |
| C-AC-02 | 360–760px | ready ES/EN | Every band stacks above a one-column tool list without horizontal page scrolling. |
| C-AC-03 | 761–1100px | ready | Tools form one column beside plan identity; local plan links wrap. |
| C-AC-04 | 320–1280px | ready ES | Gratis and 20.000 / 45.000 / 70.000 COP per month appear, without USD. |
| C-AC-05 | 320–1280px | ready EN | Enthusiast / Free and 7 / 14 / 25 USD per month appear, without COP. |
| C-AC-06 | 320–1280px | ready | Exactly three unavailable feature annotations appear in each of Designer Plus and Master Designer. |
| C-AC-07 | 320–1280px | ready | Chat copy distinguishes limits/higher limits and contains no numeric threshold. |
| C-AC-08 | 320–1280px | ready | Only Master Designer has the Taller 3D row; there is no separate explorer row. |
| C-AC-09 | 320–1280px | folded | Every plan name and price remains visible; activating its button restores the same band’s tools. |
| C-AC-10 | 320–1280px | folded → ready | A local plan link expands its destination, focuses its H2 and keeps it clear of the inspection bar. |
| C-AC-11 | 320–1280px | login | Exactly one Plans link opens the public comparison, with no account menu. |
| C-AC-12 | 320–1280px | menu-open | Exactly one Plans entry opens signed-in comparison; contextual back returns to Mi cuenta in this fixture. |
| C-AC-13 | 320–1280px | loading | Four neutral skeleton bands and a loading status replace the comparison prices. |
| C-AC-14 | 320–1280px | empty/error/partial/offline | A reason and retry action replace the comparison; retry restores all four bands. |
| C-AC-15 | 320–1280px | both themes | Focus ring and disclosure control edges remain visibly distinguishable. |
| C-AC-16 | 320–1280px | quiet/reduced | No entrance travel persists; all plan content and controls have the same outcomes. |

Final planning-artifact verification (2026-10-27):

- Real offline builder: **PASS**, final HTML 559 KB, 2,031 source files bundled; no fallback, installation, asset fetching or runtime network dependency.
- `contrast.py`: **158 pairs checked in light and dark, all pass**.
- Final `audit_mockup.py`: **128 renders / 128 planned combinations**, 3,300 text measurements, 402 focus stops, both themes at 1280/390px. No sampling warning.
- **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**
- Supplementary interaction/reflow run: **917 assertions PASS**, including **896 reflow combinations** across 320/360/390/760/768/1100/1280px, both themes, both languages, all four views and all eight inspection states; no page exceptions or external HTTP requests. Assertions covered ES/EN prices, catalogue order, six unavailable annotations, Master-only Taller row, public/signed entry links, return navigation, keyboard folding, index expansion/focus and recovery. This run preceded the final one-declaration mobile-label wrap correction.
- The final localized correction was verified with the rendered audit above plus **56 focused rendered cases / 224 disclosure-chevron containment checks**, all PASS, across the same seven widths, both themes, both languages and expanded/folded comparison. No contrast, edge, alignment, padding, overflow or unmeasured finding. Visual inspection had found the Spanish phone chevron outside its pill; allowing the label to wrap keeps it inside, as the final screenshot and containment checks confirm.
- Motion/evidence inspection: four running `band-settle` animations on load; two active tool-list reveal animations on reopening; every JSON selector matched its declared view (account disclosure on signed-in only); quiet mode leaves the band transform at `none`. Screenshots were inspected in memory for thumbnails, desktop comparison, dark phone comparison, public login and signed-in account-menu context. No extra screenshot files were written.

These checks attest the planning mockup only. No product lint/types/tests/build, real catalogue service, account authorization, live origin restoration or full WCAG conformance is established. Owner direction selection, canonical finalization and the subsequent implementation/review tasks remain pending.

## 12. Open questions, assumptions and impact

**Q: Should Catálogo / Catalogue be listed as an included public tool in every plan?** The current selected SP-2 mock catalogue explicitly includes it in the base tools; R16 enumerates chat and counter instead. This exploration inherits that existing row rather than inventing another benefit. David/Planner must confirm the public catalogue contents before finalization; removing it would remove one row in each band without changing this composition.

Confirmed: four plans and order, exact COP/USD monthly prices, free Enthusiast, three named unavailable tools in Plus/Master, qualitative chat limits and the combined Master Taller entry. The UI brief explicitly overrides the ambiguous older SPEC Priorities parenthetical about which three additions are unavailable; the cost calculator is available and extended chat is unavailable.

Presentation decisions within this exploration: all bands initially expanded; independent folding; one wrapping plan index; full cumulative lists; no featured tier or assigned-plan badge. Recovery copy is functional mockup copy, not a claim that an online catalogue API is required. Production catalogue may be statically read, in which case loading/offline previews document the failure surface rather than prescribing an unnecessary client fetch.

Impact classification: **undetermined until owner direction selection; no previous planes contract exists**. A future canonical contract affects only SP-14 T14.1/T14.2/T14.3/T14.5 and the two SP-2 entry-link locations. SP-1 remains the sole catalogue owner. Shared shell, navigation, fonts, tokens and unrelated sibling views are preserved; approval and engineering work remain outside this delegation. No standalone changelog or shared memory file is written because the exploration brief permits only revision-specific outputs and its delegation report.
