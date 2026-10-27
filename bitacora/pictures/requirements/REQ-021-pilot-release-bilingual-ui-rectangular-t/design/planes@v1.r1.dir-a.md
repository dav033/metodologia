---
contract: planes
version: 1
revision: r1.dir-a
status: draft
kind: exploration
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
date: 2026-10-27
name: Registro de herramientas
chosen_thumbnail: planes@v1.r1.dir-a.html.candidate-1.html
---

# Registro de herramientas — direction A

## 1. Identity and traceability

Planning exploration only, **draft and unapproved**. This is direction-specific evidence, not the canonical `planes@v1` contract. No shared contract, plan, repository, preview or changelog was written. The owner chooses the direction; finalization and approval remain separate.

Scope is `planes@v1.r1.behavior.md`, R17–R20 and current SP-14. SPEC.md and PLAN.json are contextual inputs. The brief overrides historical SPEC prose that inconsistently labels the cost calculator unavailable: the current brief requires extended chat, structure detection and advanced balloon detection unavailable, with the cost calculator included in Designer Plus. SP-1 is the catalogue producer. SP-14 consumers are T14.1 (copy approved design), T14.2 (public plans), T14.3 (entry links) and T14.5 (visual review). This exploration does not change those contracts or tasks.

## 2. Purpose and users

Visitors compare four access plans without signing in. Signed-in people open the same information from their account menu. Success means reading the monthly price in the interface currency, distinguishing included tools from tools not available yet, and returning to the originating page. Nothing here purchases, requests, subscribes, registers or assigns a plan.

## 3. Information architecture, approach and chosen thumbnail

The changed area sits under the existing Pictures/Sempertex masthead. Order: page title and contextual return link → plan anchor index → one divided register → cumulative-plan/administrator-assignment notes → existing pilot/mockup footer.

Each row contains plan name and monthly price, all currently included tools, and the tools not yet available. Available cumulative tools are repeated instead of requiring readers to reconstruct previous tiers. The higher chat label replaces the lower chat label rather than listing two chats. Master Designer adds only the Taller 3D line, covering the entire editor including its explorer. No separate explorer line is added.

Two visual compositions were written before the full entry:

- **Candidate 1, selected:** `planes@v1.r1.dir-a.html.candidate-1.html`, four plan rows with shared columns. It keeps price and availability in the same reading group and can stack without a horizontally scrolling matrix.
- Candidate 2: `planes@v1.r1.dir-a.html.candidate-2.html`, tools as rows and plans as columns. The comparison of a single tool is faster to scan, but long chat labels and unavailable statuses make the phone adaptation more demanding. This thumbnail is a discarded sketch, not an audited responsive deliverable.

The full mockup develops candidate 1. It fits a product used for working with decoration tools: factual lists, precise prices, repeated clear labels and ordinary navigation. It adds no landing-page hierarchy, featured tier, recommendation badge or invented benefit.

## 4. Fixed design system and eight axes

Read-only sources: both repositories' `src/app/globals.css` and layout/theme sources; t12 login, LoginForm, CabeceraApp and MenuApp; sibling `cuentas-admin@v1`, `taller-esenciales@v1` and `proyectos@v1` Markdown/HTML. The chosen account design takes priority over the earlier production password-only login. The TSX reuses the selected SP-2 shell CSS from `cuentas-admin@v1.amend-1.tsx`, with only scoped SP-14 additions. The amended source and canonical sibling establish the same masthead, language control, rounded forms and native account disclosure.

Tokens are not replaced. Kit background/foreground map to `--fondo/--texto`; card/popover to `--superficie`; primary/ring to `--acento`; primary foreground to `--sobre-acento`; muted to `--superficie-2`; muted foreground to `--texto-suave`; border to `--borde`. Like the sibling, control `--input` uses the existing stronger `--texto-tenue` token and `--rule` uses `--borde-suave`. Light canvas/surface/text/accent are #faf9fc/#ffffff/#1c1425/#6d3fe0; dark equivalents are #0b0c10/#16181f/#f4f5f7/#9479ff. Dark primary text is #120b24. No new palette, font family or brand identity.

The existing Geist and Geist Mono WOFF2 files are imported from local Next build assets and bundled as data URIs; there is no font request. Shared shell radii, panel/form spacing and native selectors remain those of SP-2. Production repositories were read only.

| Axis | Direction-specific decision |
|---|---|
| concept | An operational register: compare the complete contents of each access plan, without a sales hierarchy. |
| layout | Four horizontal plan rows in one shared panel; plan/price, available tools and unavailable tools form three desktop columns. Each row stacks on phones. |
| navigation | A local four-plan anchor index focuses the chosen plan heading; a contextual return link leads to the access screen or the originating account surface. The existing account disclosure adds one Plans link. |
| typography | Existing locally embedded Geist and Geist Mono; 24px page title/prices, 19px plan names, 14px tools and 12px availability labels. Phone prices are 21px. |
| density | One divided register rather than four promotional cards; all cumulative tools are repeated explicitly. Compact row groups expose both price and availability without expanders. |
| components | Real shadcn/Base UI Button and Input, real Skeleton, existing SP-2 native account disclosure, inline lucide checks and semantic lists. The comparison row is a custom composition, not an invented library component. |
| colour | Pictures semantic tokens unchanged in light and dark; neutral shell/rows, muted unavailable-tool text, existing accent only for links, focus and existing primary controls. |
| motion | Precise registration: 12px horizontal row settlement at 240ms in Expressive, 35ms row offsets, and rule expansion from .65 to 1 over 360ms. Index underlines use 150ms transforms. Reduced motion/still shows the final state immediately; hidden tabs suspend CSS motion. |

Real component inventory: `shadcn:button` default/outline from `@/components/ui/button`; `shadcn:input` email/password from `@/components/ui/input`; `shadcn:skeleton` loading from `@/components/ui/skeleton`. `mountMockup/useMockup` come from `@kit/mockup`; profile/reduced state from `@kit/motion`. No HTML-kit fallback, package installation or fetched asset was needed. The register, native anchors and existing account disclosure are explicit custom compositions.

## 5. Navigation and interaction

Native inspection selectors are Vista (`view`), Estado (`state`), Tema (`theme`) and Movimiento (`motion`); there is no dialog in this scope. The visible Mockup label remains. The header language selector is the existing product control, not an extra currency switch. Plan views expose ES/EN and signed-out/signed-in combinations explicitly.

The local index scrolls to a plan and focuses its heading; it changes no entitlement. The return link restores the access/account surface in this fixture. In production, retain the safe same-origin originating surface and scroll/focus when the page was opened internally; direct loads fall back to `/login` signed out or `/cuenta` signed in. Do not use an arbitrary external return URL. The mockup demonstrates `/cuenta` as its signed-in origin; other tool destinations are not simulated.

The native account disclosure preserves SP-2 semantics rather than pretending to be an ARIA menu. It has Mi cuenta, the added Planes link, and Cerrar sesión. Escape closes it and returns focus to its summary; outside click closes it. It is absent signed out. The public section shows no staff/custom-role names or permission keys. The fixture account is Cuenta Entusiasta, not a real person.

## 6. Flows

1. Access screen → its single Planes link → four-plan register without a session → return to access.
2. Mi cuenta → open existing account disclosure → its single Planes entry → the same register with account disclosure → return to Mi cuenta.
3. English plan view → English names/tools/statuses and only USD prices → language ES → same order/tools and only COP prices.
4. Local plan index → selected heading receives focus and scrolls clear of the mockup toolbar. Keyboard and pointer use the same destination.
5. Loading/error/empty/incomplete catalogue → truthful scoped state → Retry restores the complete fixture. No fabricated plan data fills a missing response.

Login/password changes are inherited SP-2 context. Their form controls only simulate the fixture flow; this design does not redefine authentication, password rules, notice acceptance or session security. The standalone mockup makes no authentication/storage/network claim.

## 7. View specifications and exact content

| Native view | Surface | Content |
|---|---|---|
| planes-es | Public `/planes`, signed out | Entusiasta, Designer, Designer Plus, Master Designer; Gratis, COP 20.000, COP 45.000, COP 70.000; por mes. |
| planes-en | Same, English | Enthusiast, Designer, Designer Plus, Master Designer; Free, USD 7, USD 14, USD 25; per month. |
| planes-es-cuenta | Signed-in `/planes` | Same Spanish register, existing account disclosure present. |
| planes-en-cuenta | Same, English | Same English register, existing account disclosure present. |
| login | Existing SP-2 access surface | Existing heading, invitation-only copy, email/password fields, sign-in and reset instructions; one added Planes link. |
| account | Existing own-account surface | Neutral `entusiasta@prueba.local` fixture, existing account form and disclosure with one Planes link. |

Entusiasta: Chat con límites / Chat with limits; Contador de globos / Balloon counter. Designer: Chat con límites más altos / Chat with higher limits; same counter. Designer Plus: those Designer tools plus Calculadora de costos / Cost calculator; Chat extendido / Extended chat, Detección de estructuras / Structure detection and Detección avanzada de globos / Advanced balloon detection each say **aún no disponible / not available yet**. Master Designer repeats those tools/statuses and adds Taller 3D / 3D workshop. No numeric chat limits, separate explorer benefit or invented service promise.

The register is a mock-only snapshot of brief facts. `src/lib/planes/catalogo.ts` is absent in the inspected t12 checkout: production must consume SP-1's catalogue rather than copy fixture constants or independently encode prices/availability. Catalogue-backed updates must change names, prices, tool names and statuses together without page edits. This data integration is not proven by a static mockup.

## 8. States

- **normal / Disponible:** all four plans and complete tool lists; no conversion action.
- **cargando / Cargando:** four groups of real Skeleton components, accessible busy label, no prices or purchasing/assignment controls. Index is absent while headings are unavailable.
- **vacio / Catálogo vacío:** “No hay planes disponibles.” / “No plans available.” with Retry and contextual return. Never interprets missing catalogue as free access.
- **error / Error:** catalogue loading failure, Retry and contextual return. No guessed prices.
- **parcial / Catálogo incompleto:** the two received rows remain, with an explicit incomplete warning and Retry. Index includes only received headings; completion restores four rows.

The fixture's states apply to the catalogue views; the access/account context retains its sibling contract and is not a new SP-2 state design. Retry is a local simulation. Unavailable tools are informative text, not disabled activation buttons. A separate success confirmation is inapplicable to the information-only section; complete read is normal. Validation/permission-denied states do not apply to public read-only plan data. Offline first load follows catalogue error; partially received data uses incomplete state. No stale prices are silently presented as current.

## 9. Responsive behavior

Supported inspection range 320–1280px and beyond. At >1100px the shell uses its existing 40px gutters; register columns are 220px / flexible / flexible with 28px gaps. At 761–1100px use existing 28px shell gutters, 190px first column and 24px gaps. At ≤760px the existing shell uses 20px gutters, header controls wrap, local plan index wraps, the column header disappears and each plan becomes one vertical section. Name → price/period → included tools → unavailable tools remain in that order. The price/period group shares a left baseline on phones. No horizontal comparison scroller, carousel, hidden plan or collapsed tool list.

The shared panel keeps 28px inner side padding on desktop and 20px on phones. Long English/Spanish names wrap. The account disclosure stays within the phone viewport. Mockup-bar height is measured by the runtime; heading anchor clearance follows it.

## 10. Accessibility and motion targets

Target WCAG 2.2 AA; automated checks are evidence, not a conformance claim. Use semantic headings, articles, lists, labelled native selects and links. All changed controls have at least 44px height, visible keyboard focus and readable labels. Text target ≥4.5:1, controls/focus ≥3:1. Unavailable status is explicit text, never colour alone; decorative checks are hidden from assistive technology. Load uses aria-busy, failures use alert semantics. Keyboard order follows shell → return → plan index → content/footer; signed-in disclosure adds its own ordinary disclosure traversal.

Rows remain readable during their 12px registration motion. Their dividing rules scale from .65 to 1, with the row stagger giving a quick ordered sweep. Finite animation only; no ongoing background animation. Existing profile controls, prefers-reduced-motion and `?still=1` remove travel and show final content immediately. Hidden-tab CSS motion is suppressed. Index hover/focus feedback and navigation remain available when still.

## 11. Observable acceptance and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| A-01 | 1280px | normal ES | Four article headings appear in required catalogue order with COP prices only. |
| A-02 | 390px | normal EN | Enthusiast reads Free; paid prices are USD 7, USD 14 and USD 25, with per month. |
| A-03 | 390/1280px | normal | Each upper plan repeats its complete tools; Master Designer has one Taller 3D line. |
| A-04 | 390/1280px | normal | Three unavailable labels occur in Designer Plus and again in Master Designer. |
| A-05 | 390/1280px | normal | Plan section has no buy, request, contact, subscription, sign-up or assignment control. |
| A-06 | 390/1280px | access | One Planes link opens the public plan fixture without signing in. |
| A-07 | 390/1280px | signed-in | Account disclosure contains one Planes link and remains present on the plan view. |
| A-08 | 390px | normal | Each register row stacks with all tools visible and no page overflow. |
| A-09 | 1280px | normal | Shared register columns align plan/price, available tools and unavailable tools. |
| A-10 | 390/1280px | loading | Four skeleton groups reserve the plan register and announce busy state. |
| A-11 | 390/1280px | empty/error | A scoped message and Retry appear; no invented prices appear. |
| A-12 | 390/1280px | partial | Two received plans and an incomplete warning remain until Retry restores four. |
| A-13 | 390/1280px | keyboard | Local index focuses the chosen heading; Escape closes disclosure and returns focus. |
| A-14 | 390/1280px | reduced/still | Final lists remain visible without running entrance animation. |
| A-15 | 390/1280px | light/dark | Both themes retain Pictures tokens and visible focus/control boundaries. |

Verification commands ran on **planes@v1.r1.dir-a.html**, built from its TSX using the absolute offline `components mockup build` CLI. Final build: **425 KB, 2031 source files, exit 0**. No installation, asset download or fallback.

- Contrast: **158 pairs checked in light and dark, all pass**.
- First audit: 120 renders, alignment 4 and padding 2 findings. Fixed the phone price/period baseline and loading-panel top inset in the TSX, then rebuilt.
- Final audit: **120 renders / 120 planned combinations**, 2960 text measurements and 292 focus stops; both themes, all six view/five state combinations at 1280/390px. No sampling omission.

RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

- Supplementary Playwright: **62 assertions passed**, including required plan order/prices/statuses, cumulative tool counts, absence of plan actions, both entry/return paths, disclosure Escape/focus restoration, anchor focus, all retries, loading semantics, reduced-motion settlement and actual `ledger-register`/`ledger-rule` animation names.
- Selector evidence: **12 selectors resolve in the default rendered view**; the motion selector has the actual `ledger-register` animation.
- **12 supplementary reflow/theme cases**: 320/390/760/768/1024/1280px × light/dark, zero horizontal overflow. Zero HTTP(S) requests and zero page exceptions in the interaction run.
- In-memory screenshot inspection: desktop in both themes, phone in both themes, English signed-in phone with account disclosure open, and existing access surface with the added link. No extra screenshot files were written.

The audit matrix measures the collapsed disclosure; its open layout and dismissal were separately inspected/tested. Product lint/types/tests/build, live catalogue updates, server auth, browser-language initialization in production and full assistive-technology testing were not run. This task modifies no production code.

## 12. Open decisions, assumptions and impact

Q: Should the public tool list explicitly include “Catálogo / Catalogue”, or stay with the chat/counter tools enumerated by this UI brief? SP-1's permission description includes catalogue access, while the brief and current public plan descriptions do not name a separate catalogue benefit. Decision owner: David with the Planner; current exploration follows the public brief and shows no additional catalogue line.

Confirmed: four named plans in order; currency follows interface language; Enthusiast is the English name; the three future tools remain marked unavailable; no numeric chat limits; explorer is covered by Master Designer's Taller 3D line; administrator assigns the plan. No pricing or availability decision is invented.

Assumptions for review: complete repeated tool lists, unavailable group split, wrapped anchor index, one return link, and incomplete-catalogue recovery are design proposals. English labels are literal translations of supplied terminology, subject to the project's shared bilingual catalogue. Browser-selected initial language is an implementation requirement; the visible language control and explicit views allow inspection here.

Impact: additive exploration for SP-14 T14.1/T14.2/T14.3/T14.5. The two entry links extend SP-2 access/account surfaces without changing their contracts. SP-1 supplies data. No token or shell redesign; no canonical contract has been superseded. Compatibility remains undetermined until the owner selects a direction and the finalizer produces the approved snapshot. Production integration and owner approval are pending outside this delegated exploration.
