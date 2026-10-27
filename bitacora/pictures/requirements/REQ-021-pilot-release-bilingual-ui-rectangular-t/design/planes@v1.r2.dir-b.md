---
name: Paneles de consulta
contract: planes@v1
subplan: SP-14
revision: r2
direction: b
status: draft
artifact: independent-exploration
owner: David
created: 2026-10-27
---

# Paneles de consulta — spatial exploration B

## 1. Identity and traceability

This is an **unapproved exploration**, not the canonical `planes@v1` contract. The final scoped exploration instruction supersedes the earlier canonical-output request. Earlier owner selection of direction C is preserved as history; this fresh spatial candidate does not replace or approve it. No shared contract, sibling, history, SPEC, PLAN or production code is changed. The later explicit Stop-hook request records this direction in the existing session day log only; it introduces no new decision or pending item.

Scope: SP-14, R17–R20 and the answered round-13 selection behavior. Source of truth: `planes@v1.r2.behavior.md`, SHA-256 `3f69cc0a465ac74b71a63cf247d9b1d38dbb87e0139ab13b8e52076fdf0b8239`. Context: current SPEC (including “Behavior — SP-14 extra view”), PLAN/SP-14, `/tmp/REQ-021-planes-feedback-1.md` and the three supplied sibling contracts/HTMLs. The selected sibling account surface is **Parte de acceso**; production token mapping takes precedence over older exploratory styling in sibling HTML.

Read-only product inspection: both registered worktrees' globals/theme, t12 login/LoginForm/layout, CabeceraApp and MenuApp; planned account-menu surface supplied by SP-2. The assigned worktrees do not yet contain the plan catalogue file. This preview therefore uses one explicit in-memory catalogue fixture containing the requirement's four names, prices and tool lists. It is not evidence that production consumes SP-1's catalogue.

Consumers: SP-14 `ui.contract=planes`, version 1, T14.1 design copy, T14.2 page and T14.3 entry links; T14.5 visual acceptance. SP-1 remains the data owner. Existing P-207 is closed: the shared Catálogo row belongs in every plan, as confirmed by current SPEC/T1.2; this exploration follows that resolved wording. SP-2 owns sign-in and account surfaces; this direction adds only their Planes entry and illustrates the existing context. T14.4 browser integration and T14.6 audit remain engineering evidence, outside this design task.

## 2. Purpose and users

Visitors, with or without a session, compare the four cumulative access plans without purchasing, requesting access, signing up or changing any account. The extra view answers which plan to highlight while comparing, not which plan to assign. Successful use means reading full tools/prices in the current language, optionally highlighting a plan and returning to the comparison, and leaving through the original entry context.

## 3. Information architecture and hierarchy

Reproduce the compact ring-and-dot Pictures mark, Sempertex label, language control, signed-in account disclosure, sober page title, horizontal route rule and invitation-pilot footer established by the selected SP-2 contract. Recompose only the new plans content.

Comparison: title/return → Compare / Select for comparison → informative assignment sentence → optional selected-plan feedback → local plan-name index → one continuous sheet containing Entusiasta, Designer, Designer Plus and Master Designer. Each row has an identity/price column and full cumulative tools. There are no tool-hide buttons, accordions, truncated lists, recommended-plan badges or marketing panels.

Selection: same shell and horizontal navigation → explicit comparison-only explanation → optional selected-plan summary/return action → four native radio options with every price and tool list visible → return to comparison even when no option is selected. A selected plan receives a border and text status; no default winner is preselected in the normal fixture. Its radio state does not represent an account's assigned plan.

### Candidate evidence and choice

Both thumbnail compositions were written first and inspected at 1280px, before the full entry was built:

- **Chosen thumbnail:** `planes@v1.r2.dir-b.html.candidate-1.html`. A local index beside horizontal identity/tools rows preserves one reading order and makes tablet reflow explicit. Full lists occupy a shared sheet instead of four narrow columns.
- `planes@v1.r2.dir-b.html.candidate-2.html`: two-by-two full-plan panels. Retained as alternative evidence; its peer-option geometry suits the extra radio selection view, while the first composition is stronger as the main reference sheet.

Thumbnails are static composition studies, not audited interaction contracts. Full states, themes and controls are in the built TSX/HTML.

## 4. Design system and visual language

The project's palette and fonts are fixed. Actual production **Geist Sans** and **Geist Mono** are embedded from existing local Next WOFF2 assets; no assets or packages are fetched. Geist Sans is the product body/control family. Mono is available but not introduced as a new visible hierarchy. The runtime's separate Mockup inspection bar retains its own planning appearance.

| Pictures token | Kit role | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card/popover | #ffffff / #16181f |
| `--texto` | foregrounds | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted foreground | #6b6178 / #9aa1ad |
| `--superficie-2` | muted/secondary | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primary / primary foreground | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| `--acento-suave` | accent | #ece3fb / #241f3d |
| `--borde`, `--borde-suave` | decorative borders / row rules | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | input / control edges | #766c85 / #8a91a0 |
| `--acento` | ring | #6d3fe0 / #9479ff |
| `--error` | destructive | #b23a45 / #ff979f |

Shapes repeat the selected SP-2 vocabulary: 32px paper/option panels, 24px feedback/menu, 18px fields/index items and pill controls; 28px desktop and 20px phone insets. Neutral navigation uses a text-colour underline. Accent identifies the selected comparison item and the single local return action. Text availability markers use existing muted text rather than a low-contrast disabled treatment.

### Eight-axis table

| Axis | Rendered expression |
|---|---|
| concept | One public plan reference organised as a spatial consultation sheet; comparison selection is local, reversible and unrelated to account assignment. |
| layout | A 180px plan index beside one rounded sheet of four horizontal plan rows; each row pairs identity/price with its full tool list. The extra selection view uses a two-by-two set of full plan options. |
| navigation | Preserved Pictures/Sempertex header, horizontal comparison/selection navigation, plan-name anchor index, existing sign-in/account links and explicit return to full comparison. |
| typography | Existing embedded Geist Sans: 24px page title and prices, 20px plan names, 14px tools, 12px availability/monthly metadata; tabular prices. No new family or display treatment. |
| density | One shared comparison surface with 28px row insets and 24px tool spacing; full lists rather than disclosures. Tablet retains a 200px identity column and one tool column; phone stacks each row. |
| components | Real installed shadcn/Base UI Button, Input and Skeleton, production ring-and-dot mark, native language selector, details-based account disclosure and native radio selection inside rounded sibling panels. |
| colour | Exact Pictures light/dark semantic tokens, including acento/sobre-acento for primary controls and selection; neutral section navigation and readable texto-suave availability labels. No palette changes. |
| motion | Alternating horizontal row registration, vertically settling selection panels, a short selected-summary arrival and reversible hover/press response. Expressive 520ms/65ms stagger, 180ms controls; profile and reduced/still parity. |

### Real component provenance

| Component / variants / states | Installed import |
|---|---|
| `shadcn:button default, outline default/hover/focus/pressed` | `@/components/ui/button` |
| `shadcn:input email/password default/focus` | `@/components/ui/input` |
| `shadcn:skeleton loading` | `@/components/ui/skeleton` |
| `kit:mockup native view/state/theme/motion selectors` | `@kit/mockup` → supplied real/runtime/mockup.tsx |
| `kit:motion profile/reduced state` | `@kit/motion` → supplied real/runtime/motion.tsx |

The index, plan sheet, native radio options and account details are custom semantic compositions using the existing product vocabulary, not claimed as upstream kit components. Lucide supplies Check/Circle/UserRound/return icons. There is no fallback HTML component library in the complete mockup; thumbnails are intentionally small native compositions.

Motion uses the existing `--ease-out` curve (.23,1,.32,1). Expressive: 520ms row/panel registration, 65ms stagger, 28px travel and 180ms controls; natural: 300/35/14/140; subtle: 160/15/4/100. Odd/even desktop rows enter from opposite sides; selection options settle vertically; status panels register from −8px; selection borders settle from .985 scale. Text remains opaque throughout. Hover shifts index items 3px; button press .98 scale. No perpetual decorative effects. Reduced motion, Quieto and `?still=1` remove travel/animation; hidden tabs pause CSS motion.

## 5. Navigation and interaction model

Production entries remain **`/login` → `/planes`** and the existing account disclosure → **`/planes`**. The HTML anchors carry real `/planes`, `/login`, `/cuenta` hrefs; handlers prevent navigation solely to operate offline preview views. The production return must preserve the safe originating route; this mock demonstrates `/login` and `/cuenta` as its two bounded origins, not a forced `/cuenta` destination for every product page.

Comparison/selection are two in-page modes within `/planes`, not an added marketing route or another global navigation item. Native buttons in a labelled nav identify the current mode with `aria-current=page`. Mode changes focus the page heading. The plan-name index scrolls and focuses its target section. At narrow widths the index moves above content; it never becomes a horizontally scrolling carousel.

Radio selection changes only the local comparison highlight. Arrow keys choose a peer radio; Tab leaves the group. Returning preserves the chosen highlight; “Quitar selección” removes it. Neither selection nor clearing selection changes the signed-in identity, account data, granted tools or permissions. No account-assignment API is represented. The account disclosure retains Mi cuenta / Cerrar sesión and adds Planes once; Escape closes it and restores summary focus. No staff role or permission key appears in the public plans section.

## 6. Flows

1. **Public comparison:** Iniciar sesión → Planes → four plans/full tools → Volver a iniciar sesión. Authentication is not required.
2. **Signed-in comparison:** Mi cuenta's existing disclosure → Planes → comparison → return to Mi cuenta. In production, the same entry works from any existing signed-in shell and returns to its origin.
3. **Highlight only:** Seleccionar para comparar → select any one radio → textual “Seleccionado para comparar” status → Volver a la comparación → corresponding row bordered and labelled → Quitar selección restores the complete unhighlighted sheet. No signup, purchase, request or assignment step.
4. **English:** use existing language selector in the inspection fixture → all plan content changes to English, Entusiasta becomes Enthusiast, prices become USD only; mode/selection is retained. Production initial language follows the browser per R20.
5. **Catalogue recovery:** loading placeholders → normal catalogue, or error/empty/offline explanation with Reintentar → normal fixture. This action simulates recovery; real network/cache policy remains implementation responsibility.

## 7. View specifications

| Native `view` | Structure and actions | Requirement |
|---|---|---|
| `comparison` | Public comparison, no account menu, login return, four full plan rows, index and selection mode | R17/R18/R20 |
| `comparison-account` | Same reference content with account disclosure and return to its illustrated account origin | R18/R19/R20 |
| `selection` | Public four-option radio view, all full tool lists, selection feedback and return to full comparison | Answered round 13 |
| `selection-account` | Same comparison-only selection with signed-in shell; account assignment remains Entusiasta | Answered round 13 |
| `login` | SP-2's centred 676px access form, existing labels/help/footer, one added Planes link | R19 |
| `account` | SP-2 own-account context, existing identity/password/help/notice structure and account disclosure containing Planes | R19 |

Login and own-account forms are contextual entry-point illustrations, not a redesign or an implementation of SP-2 authentication/password behavior. Their independent failure/success/notice flows remain entirely owned by the SP-2 contract; global catalogue state choices do not alter these contextual forms. Fixture identity is neutral and explicitly marked simulated. The full plans page is public for every account; it never filters the comparison by access rights.

| Plan | ES monthly price | EN monthly price | Visible cumulative tools |
|---|---|---|---|
| Entusiasta / Enthusiast | Gratis | Free | Chat con límites / Chat with limits; Contador básico de globos / Basic balloon counter; Catálogo / Catalogue |
| Designer | 20.000 COP por mes | 7 USD per month | Chat con límites más altos / Chat with higher limits; same basic counter and catalogue |
| Designer Plus | 45.000 COP por mes | 14 USD per month | Designer tools plus Chat extendido / Extended chat, Calculadora de costos / Cost calculator, Detección de estructuras / Structure detection, Detección avanzada de globos / Advanced balloon detection |
| Master Designer | 70.000 COP por mes | 25 USD per month | Every Designer Plus tool plus Taller 3D / 3D workshop |

Extended chat, structure detection and advanced balloon detection each have **“aún no disponible” / “not available yet”** underneath, in both higher plans. Cost calculator is available; no numeric chat-limit value appears. Taller 3D includes the complete editor and ready-made decorations explorer; there is no extra explorer line. The table above documents both languages; the rendered product shows only one language/currency at a time. The fixture is centralized and reused between modes; production data must come from SP-1's catalogue rather than copying this fixture into a page.

## 8. States

| Native `state` | Applicable content | Observable behavior |
|---|---|---|
| `normal` | Four plans modes | All four full tool lists, no initial comparison highlight on a fresh page; selection can be changed interactively |
| `selected` | Four plans modes | Inspection example highlights Designer Plus and announces comparison-only selection; does not assert it is the account plan |
| `loading` | Four plans modes | Four name/price/tools skeleton rows and labelled Cargando planes status; unknown prices/tools are not fabricated |
| `empty` | Four plans modes | No hay planes disponibles, catalogue-unavailable explanation, Reintentar; no assignment/purchase action |
| `error` | Four plans modes | No pudimos cargar los planes in an alert, recovery explanation and Reintentar; no stale factual price rendered as current |
| `offline` | Four plans modes | Sin conexión, connect-to-consult explanation and Reintentar; no invented cached prices |

Every declared state has a native inspection switch. Authentication-context views remain normal when unrelated catalogue states are inspected. A separate “saved” success, permission-denied, checkout, validation, assignment-pending or account-update state is inapplicable: the public surface performs no mutation and accepts no submitted personal data. Selection feedback is its only completion status. Unavailable tools remain readable information, not disabled purchase controls. No partial/stale set of plans is shown as a complete catalogue; unusable catalogue data follows error/empty recovery.

## 9. Responsive behavior

Supported floor: **360px**, matching selected SP-2. Tested widths: 360, 390, 768, 1024, 1280px. Both languages/themes reflow without page-wide horizontal scrolling; vertical scrolling is intentional for the complete lists.

| Range | Comparison | Selection / shared shell |
|---|---|---|
| 1101px+ | 40px outer gutters; 180px sticky local index + flexible paper, 32px gap; each row identity 180–220px and two-column tools | Two equal full-plan option panels per row, two-column tools; 28px panel insets; compact product header |
| 761–1100px | 28px gutters; index becomes four wrapping-name controls above one full-width paper; identity 200px beside **one** tool column | Two options per row with single-column tools; 24px option insets; header wraps as needed |
| 360–760px | 20px gutters; index two columns, each plan identity above one full tool list; paper 20px insets | One complete radio option per row; feedback/action stack; product header/language/account controls wrap; 20px panels; no fixed overlay footer |

The tablet solution never compresses four full tool columns into one viewport. The index does not hide plans or replace the full lists. Prices and Master Designer wrap rather than truncate. Account/login forms retain the centred 676px cap and existing 620px internal axis when space allows; at phone width they contract within 20px gutters.

## 10. Accessibility targets

Target WCAG 2.2 AA for the implemented surface; this exploration is not a conformance certificate. Semantic nav/section/headings/lists, native labelled selectors, radio group/legend, visible checked state and textual selection status provide keyboard and assistive-technology structure. Status updates use role=status; load errors use role=alert. Controls generally have ≥44px height; radio labels are full name/price areas around the 22px visual radio. Colour is supplemented by radio state and selected text. Keyboard focus uses a 2px accent outline with 3px offset; target sections/headings receive programmatic focus after navigation. There is no mandatory drag gesture, hover-only disclosure of tool content, horizontal carousel or hidden selection action.

Text and controls were measured in both themes. Full reflow was checked at 360–1280px and in ES/EN. Reduced motion retains identical content/controls and zero running animations. Real screen-reader announcements, browser back/origin restoration, zoom settings, cross-browser focus behavior and service-driven errors require implementation verification.

## 11. Visual acceptance criteria and honest verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-AC-01 | 360px+ | normal, public | Pictures ring-and-dot header, Sempertex label and existing language control remain; no account disclosure appears |
| B-AC-02 | 360px+ | normal, signed-in | Existing account disclosure contains Mi cuenta, exactly one Planes link and Cerrar sesión |
| B-AC-03 | 360px+ | comparison | Four headings appear in catalogue order and every full tool list is visible without toggling any disclosure |
| B-AC-04 | 360px+ | ES | Gratis and 20.000/45.000/70.000 COP per month are visible; USD is absent |
| B-AC-05 | 360px+ | EN | Enthusiast/Free and 7/14/25 USD per month are visible; COP is absent |
| B-AC-06 | 360px+ | normal | Both higher plans each mark three unavailable tools; calculator and Taller are not marked unavailable |
| B-AC-07 | 1101px+ | comparison | A 180px plan-name index sits beside one rounded sheet of four horizontal plan rows |
| B-AC-08 | 761–1100px | comparison | Index sits above the sheet; each row has a 200px identity column and a readable single tool column |
| B-AC-09 | 360–760px | comparison | Identity/price precede each single-column tool list; the local index forms two columns |
| B-AC-10 | 761px+ | selection | Four radio options form two columns, with every cumulative tool list present |
| B-AC-11 | 360–760px | selection | Four full options stack in catalogue order and no action extends outside the viewport |
| B-AC-12 | 360px+ | selecting | Radio choice adds only a comparison border/status; returning highlights the same row in full comparison |
| B-AC-13 | 360px+ | selected | Quitar selección removes the highlight while all four lists remain visible |
| B-AC-14 | 360px+ | loading | Four skeleton groups and a loading status replace unresolved names/prices/tools |
| B-AC-15 | 360px+ | empty/error/offline | Catalogue explanation and Reintentar appear, with no invented prices or account action |
| B-AC-16 | 360px+ | entry links | The login Plans link and signed-in menu Planes entry have /planes hrefs and open the comparison in preview |
| B-AC-17 | 360px+ | keyboard | Plan index focuses its target; radio arrow operation and return/clear work without a pointer |
| B-AC-18 | 360px+ | both themes | Selection border, text, native fields and focus indicator remain distinguishable against the actual background |
| B-AC-19 | 360px+ | expressive | Row/option/status registration actually animates with the documented timing; motion evidence selectors identify these elements |
| B-AC-20 | 360px+ | reduced/still | Content reaches the same final position with zero running animation and usable controls |
| B-AC-21 | 360px+ | all plans views | No purchase/request/signup/assignment control, numeric chat limit or hide-tools control appears |

### Commands and observed results

Tool root: `/home/david/dev/metodologia/skill`; kit root: `<tool>/agents/designer/skills/david-ui-kit`. All commands ran on **this direction's final output**. No package installation, downloads or server launch.

1. `python3 <tool>/scripts/bitacora.py components status` → installed=True, built=True, **96/96 entries OK**.
2. `python3 <tool>/scripts/bitacora.py components mockup build <design>/planes@v1.r2.dir-b.tsx --out <design>/planes@v1.r2.dir-b.html` → **413 KB, 2031 source files, offline**, exit 0.
3. `python3 <kit>/kit/contrast.py <design>/planes@v1.r2.dir-b.html` → **contrast: 158 pairs checked in light and dark, all pass**, exit 0.
4. `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/planes@v1.r2.dir-b.html --max-combos 100` → **144 renders (144 combinations planned), 3896 text measurements, 448 focus stops**, exit 0. This is the full 6-view × 6-state × 2-theme × 2-width matrix, not sampling.

**RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**

Supplementary cached Playwright/Chromium check on the final HTML: **120 reflow cases PASS** (6 views × 5 widths × 2 themes × 2 languages), exact four-plan order, four full lists and six unavailable labels on plans modes, exclusive currency, four selection/return flows, native radio arrow operation, clear-selection behavior, /planes entry hrefs, unchanged simulated Entusiasta identity/role, index focus and reduced-motion parity. **0 HTTP(S) requests and 0 page errors.** This only establishes mock behavior; account authorization/persistence is not implemented.

Visually inspected in-memory screenshots without writing extra image files: both candidates; desktop 1280px light comparison and dark signed-in selection; tablet 768px dark comparison; phone 390px light EN selection and dark ES comparison. Tablet shows four complete readable rows with no overflow. Mobile lists stack, translated labels wrap and both themes preserve price/tool hierarchy. Screenshots are visual evidence of the preview, not production acceptance.

An initial read-only inspection of the sibling's own-account view used an incorrect selector option and timed out; reading its actual option list identified `cuenta`, and the inspection then succeeded. This was a source-inspection command error, not a failure of the direction or its audits. A first complete direction audit passed; the final audit above was rerun after aligning the account-context copy and route hrefs with SP-2. Earlier audit statistics are not presented as final evidence. The final catalogue-row audit also includes the already-resolved P-207 shared Catálogo line in all four plans; this corrects the initial exploration fixture omission without reopening the owner decision.

Production lint/types/tests/build and live routing/catalogue tests were not run because production code is read-only and unchanged. No claim of account mutation safety on a real service follows from this static preview.

## 12. Open questions, assumptions and impact

**Open product questions for the owner: none.** Round 13 resolved the selection/assignment ambiguity. The design choice and eventual contract/plan approval remain the owner's independent gate; completing this exploration grants no approval.

Confirmed: four plans/prices/order, cumulative visible tools, three unavailable tools in both higher plans, bilingual currency/name behavior, no numeric limits, whole Taller/editor/explorer under Master Designer, no purchase/request/signup or account mutation, no hide-tools controls and a tablet-specific readable arrangement.

Assumptions limited to the artifact: single centralized catalogue fixture; local highlight/language retained across mock modes but not across browser reload; selected inspection state seeds Designer Plus solely for review; errors/empty/offline are selectable simulations; authentication/password controls are contextual SP-2 illustrations. Production must use the authoritative catalogue, browser language and safe actual return origin. No public permission-key/staff-role disclosure or hidden server operation is introduced.

Compatibility is **undetermined until a direction is chosen**. If adopted, the comparison/selection hierarchy and tablet/phone structure require SP-14 T14.2 implementation and T14.5 rendered review; T14.3 adds only the already-required links. SP-1 is unchanged, and this exploration does not mutate the selected SP-2 or SP-3/SP-4 sibling contracts. This is a ready-to-compare, behavior-aligned draft; the canonical planes contract remains untouched.

CONCERNS: owner choice/approval and production integration remain outstanding. No unresolved material behavior ambiguity, missing token source, unavailable builder, fallback dependency or unrun mock audit remains. The static artifact does not prove catalogue synchronization, server permissions, browser-history restoration, live authentication or complete WCAG compliance.
