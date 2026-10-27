---
name: Planos de consulta
status: draft
subplan: SP-14
contract: planes@v1
exploration: r3.dir-b
chosen_thumbnail: planes@v1.r3.dir-b.html.candidate-1.html
---

# Planos de consulta — Spatial exploration B

This is an independent planning exploration, not an approved contract. It does not replace the owner-selected Direction C or edit the canonical planes@v1 pair. Sources: planes@v1.r3.behavior.md, SPEC “Behavior — SP-14 extra view (round 13 answered)”, current SP-14 PLAN.json, owner feedback file, current planes@v1 and sibling cuentas-admin@v1 / taller-esenciales@v1 / proyectos@v1. The latest exploration-only write scope governs this delivery.

## Approach and chosen thumbnail

The product question is unchanged: which tools and monthly price belong to each plan? Keep the Pictures/Sempertex ring-and-dot masthead, shared language/account controls, access/account forms and footer. Recompose only the plans work area into a local index beside a single ruled comparison sheet, divided into four peer quadrants. The index becomes a temporary comparison selector in the additional view; all four complete tool lists remain visible.

Two thumbnail HTMLs were drawn before the full TSX and inspected in Chromium at 1280px:

- **Candidate 1 — chosen:** lateral plan index and 2×2 comparison sheet. The four plan headings and first tool rows appear earlier; the comparison selector has an explicit spatial home beside the content.
- Candidate 2: upper index and long horizontal plan bands. It preserves the previous consultation rhythm but requires more vertical travel before Master Designer and distinguishes the additional view less clearly.

The selected composition fits the existing product’s working-paper pattern and SP-2’s compact header. It reuses the production palette, local Geist assets, semantic pill controls, source ring mark, neutral navigation and rounded paper vocabulary; it introduces no brand, palette or font. Workshop-specific palettes are not imported into this account/public surface. The plan quadrant arrangement and local navigation are the exploration variables.

## Eight axes

| Axis | Rendered expression |
|---|---|
| Concept | A spatial consultation workspace: a local plan index beside one continuous four-panel comparison sheet; the optional selector highlights an informational comparison only. |
| Layout | At >=1100px a 216px left rail sits beside a ruled 2-by-2 sheet. At 640-1099px the rail becomes an upper dock and the sheet stays two columns. Below 640px plan panels stack. |
| Navigation | Preserved access/account entry links and masthead; a neutral in-page comparison/selection rule; anchor index in comparison changes into pressed-state choice buttons in selection, with a persistent full-comparison return. |
| Typography | Existing embedded Geist Sans and Geist Mono only. Page 24px, plan heading 20px, tabular monthly price 22px (20px phone), tools 14px, availability 12px. No display typography. |
| Density | One outer 32px sheet with shared rules, 24px peer-panel insets (20px phone) and compact fully visible cumulative tool lists. A narrow catalogue index keeps the main working area distinct from navigation. |
| Components | Real installed shadcn/Base UI Button, Input and Skeleton; source-compatible ring-and-dot masthead and account disclosure. Native buttons/anchors form the plan dock; no plan-tools disclosure. |
| Colour | Unchanged Pictures globals.css semantic palette in both themes; source accent marks only the comparison selection/focus/links, neutral paper and navigation, existing warning token labels unavailable tools. |
| Motion | Opposing spatial entrance: rail translates from -16px while plan quadrants arrive from +22px with 45ms staggering; expressive 440ms cubic-bezier(.16,1,.3,1). Selection has a shared spring marker and a short underline settle. Reduced motion and still=1 settle immediately. |

Selector evidence is in planes@v1.r3.dir-b.json. Layout selectors identify the rail and sheet, navigation selectors identify actual controls, typography selectors identify visible hierarchy, and motion selectors identify elements with CSS animations or the Motion shared-element marker. No axis uses body as generic evidence.

## Views, states and behavior

| Native view | Purpose / retained context |
|---|---|
| compare | Public /planes comparison, no account menu; back to sign-in. |
| compare-signed | Same public information with the retained account disclosure; return to the originating account context in this bounded fixture. |
| select | Additional public selection view. Four single-choice pressed-state buttons highlight one plan for comparison only. |
| select-signed | Same informational selection with the current account disclosure retained; the account’s existing assigned plan never changes. |
| login | Existing SP-2 invitation-only sign-in form with exactly one /planes entry after reset guidance. |
| menu | Existing SP-2 Mi cuenta surface with its account disclosure initially open to show the single /planes entry between Mi cuenta and sign-out. |

The external planning bar retains the **Mockup** label and native `view`, `state`, `theme` and `motion` selectors, with Spanish labels. No dialog is declared, so a scene selector is inapplicable. The product language control independently demonstrates Spanish and English; browser language sets the initial locale. Native states: `normal`, `selected`, `loading`, `empty`, `error`, `offline`. `selected` seeds Designer Plus only as an inspectable fixture when no comparison preference exists. Catalogue states apply to the plans views; entry contexts remain SP-2 demonstrations rather than parallel authentication specifications.

Every valid catalogue view lists all tools, without an Ocultar/Mostrar herramientas control. Entusiasta/Enthusiast has Chat con límites / Chat with limits, Contador de globos / Balloon counter and Catálogo / Catalogue. Designer uses the higher-limits chat phrase, without numeric limits. Designer Plus adds the cost calculator and the three unavailable tools. Master Designer adds the single Taller 3D / 3D workshop line, including its explorer, without a duplicate explorer row. Three unavailable labels appear in each upper plan: Chat ampliado / Extended chat, structure detection and advanced balloon detection. They read “aún no disponible” / “not available yet”. The cost calculator is available.

Names, ordering, prices and labels are represented by one requirements-derived illustrative fixture. COP prices are 20,000 / 45,000 / 70,000 per month, formatted in Spanish as 20.000 / 45.000 / 70.000; USD prices are 7 / 14 / 25 per month. Entusiasta is Gratis / Free. Only the active language’s currency appears. Production must consume SP-1’s plan-catalogue@1; src/lib/planes/catalogo.ts is not yet present in either read-only input worktree, so this artifact does not attest catalogue integration.

Comparison index links move to the named plan and focus its article. Selection buttons expose aria-pressed, keep focus on the activated choice, announce the selected plan and mark the same plan in the sheet. “Volver a la comparación completa” retains that in-memory highlight. Opening either /planes entry preserves its signed-in/out context. Selection changes no role, account field, permission, storage, cookie or remote data. No purchase, request, contact, sign-up or assignment action exists in the section. The only assignment explanation is “Un administrador asigna el plan.”

Loading presents four skeleton groups and a loading announcement instead of a successful empty catalogue. Empty/error/offline replace the sheet with the inherited explanation and Retry. Retry restores the complete local fixture. No missing price is guessed. Choice buttons are disabled when catalogue data is unavailable. Missing catalogue values do not produce partial plan comparison. The entry-context forms only show a Mockup explanation and never submit credentials.

## Responsive and accessibility behavior

| Width | Composition |
|---|---|
| 320–639px | Shared compact wrapping header; 20px outer gutters; 2×2 local index/selector; one continuous stacked plan sheet with 20px insets; full-width comparison return. |
| 640–839px | 24px gutters; local dock in 2×2; plan sheet in two equal columns with 24px insets. Selection summary and return wrap in normal flow. |
| 840–1099px | Dock becomes four columns; sheet stays two columns; header wraps where needed. No side rail competes with plan text at tablet widths. |
| ≥1100px | 40px gutters; 216px sticky local rail, 28px gap and flexible 2×2 sheet. Rail offset accounts for the Mockup bar. |

Plan order is Entusiasta, Designer, Designer Plus, Master Designer in DOM and reading order. Text and controls wrap without horizontal page scrolling. Account disclosure, navigation and return remain in normal document flow on narrow screens. Selected styling adds a textual status, pressed-state control, check and short accent rule; color is not the sole signal. Use standard links/buttons, header/nav landmarks and a single page H1. Focus outlines use the source accent, with no hidden hover-only action. New targets are at least 44px high. Escape closes the account disclosure and returns focus to its summary. The mockup explicitly controls the summary toggle to avoid a race between the browser’s deferred details toggle and rapid Escape.

WCAG 2.2 AA is a target, not a conformance claim. Contrast, focus, padding and reflow are measured below. Production authentication, catalogue integration and full assistive-technology testing remain implementation/reviewer work.

## Component and token provenance

Read-only source inspection: t12 globals.css, layout.tsx, login/page.tsx, login/LoginForm.tsx, CabeceraApp.tsx and MenuApp.tsx; same product sources in asesor; selected sibling contracts and HTML. Input repository changes were left untouched.

- Real installed `shadcn:button` outline/default: @/components/ui/button; `shadcn:input`: @/components/ui/input; `shadcn:skeleton`: @/components/ui/skeleton. ButtonPrimitive is Base UI. The real builder bundles React, Motion and local font assets offline.
- App-specific custom composition: masthead/ring mark and account details disclosure inherited from the prior planes draft’s SP-2 context; neutral route rule; native plan index/choice dock; shared comparison sheet with semantic articles and lists. This is not a new kit component or a production implementation.
- `--background`←`--fondo` (#faf9fc / #0b0c10); `--card`, `--popover`←`--superficie` (#ffffff / #16181f); foregrounds←`--texto` (#1c1425 / #f4f5f7); muted text←`--texto-suave` (#6b6178 / #9aa1ad); secondary←`--superficie-2` (#efe9f8 / #242733).
- Primary/ring←`--acento` (#6d3fe0 / #9479ff); primary foreground←`--sobre-acento` (#ffffff / #120b24). Source `--aviso` labels unavailable tools; source `--error` labels load failure. Input edges use the sibling’s existing `--texto-tenue` alias (#766c85 / #8a91a0), while decorative borders retain `--borde`/`--borde-suave`.
- Embedded existing local Geist Sans/Geist Mono WOFF2 assets, no font request. Sibling radius roles: panel 32px, inset 24px, field 18px and pill 999px. No token source is missing and no new color is proposed.

## Interaction and motion detail

The changed area uses opposing spatial arrivals: the local rail settles from -16px, plan quadrants from +22px with 45ms staggering; opacity stays at least .85. Expressive duration 440ms with cubic-bezier(.16,1,.3,1), natural 280ms, subtle 160ms. Selecting a plan moves a shared check marker with the installed Motion spring and settles a short accent rule in the corresponding panel. Repeated source controls retain quick 180/140/100ms feedback. No continuous decorative animation or offscreen timer exists; document-hidden CSS animations pause. Reduced-motion preferences, the Quieto selector and ?still=1 settle all content immediately without removing information or feedback.

## Observable review checks

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-01 | ≥1100px | normal | A 216px local index sits to the left of the two-column comparison sheet. |
| B-02 | 640–839px | normal / selected | Index choices form two columns above a two-column plan sheet, with all tool lists visible. |
| B-03 | 840–1099px | normal | Four index choices share one row above the two-column sheet without horizontal page scroll. |
| B-04 | 320–639px | normal / selected | Panels stack in catalogue order and every tool wraps within the viewport. |
| B-05 | 320–1280px | normal / selected | Four full lists contain 3, 3, 7 and 8 tools; no hide-tools control exists. |
| B-06 | 320–1280px | ES / EN | Exactly one currency is shown in prices; Entusiasta is Gratis / Enthusiast is Free. |
| B-07 | 320–1280px | selected | Exactly one choice has aria-pressed=true and its plan is marked for comparison. |
| B-08 | 320–1280px | selection → comparison | Returning keeps the highlight and leaves the account identity and storage unchanged. |
| B-09 | 320–1280px | normal | Both upper plans mark exactly the three unavailable tools in visible text. |
| B-10 | 390–1280px | loading / empty / error / offline | No incomplete successful comparison is shown; failure states expose Retry. |
| B-11 | 390–1280px | login / menu | One /planes link at each assigned entry opens the proper public/signed-in context. |
| B-12 | all | reduced / still | Content and selection feedback remain available with no finite animation still running. |

## Audit evidence

- Real offline builder: PASS. The installed workspace reported 96/96 component entries available. Final HTML bundles 2,031 source files into approximately 553 KB, including the source fonts; no package installation or asset fetch was used.
- Static contrast: **158 pairs checked in light and dark, all pass**.
- Final rendered command: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py planes@v1.r3.dir-b.html --widths 1280,390,768,1024 --max-combos 100`.
- **288 renders / 288 planned combinations**, 9,120 text measurements and 560 keyboard focus stops. All six views, six states and both themes were measured at all four widths; no sampling was needed.

RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

- Supplementary final Playwright check: **141 scenarios passed**, including **128 responsive cases** across 320/390/640/768/840/1024/1100/1280px, ES/EN, both themes and all four comparison/selection views. Assertions covered four full lists with 3/3/7/8 tools, six unavailable labels, language-specific currency/free naming, each of four local choices, highlight retention, both /planes entry links, contextual return, Escape closure, catalogue-state recovery, no external requests, no browser exceptions and unchanged local/session storage.
- Thumbnail 1 and 2 were visually inspected at 1280px before choosing. Full mockup screenshots were inspected in memory at 1280/390 in both themes, plus tablet 768px selection and 1024px comparison. No screenshot files or other artifacts were written outside the assigned output list.
- The first rendered audit found one phone selected-button inset at 11px; it was corrected to at least 13px. The initial immediate-Escape interaction check exposed a deferred native-toggle race; the mockup toggle was repaired without changing the entry layout. The final 288-render audit and 141-scenario check above cover the rebuilt artifact after both corrections.
- Selector/motion evidence check: every JSON evidence selector matched rendered elements; railArrive and four paperArrive animations were observed running, and Quieto left zero finite animations running.
- These are planning-artifact checks, not production lint/typecheck/build, backend permissions, live authentication or real catalogue integration. No product checks are claimed.

## Impact, concerns and open questions

Only SP-14 consumes planes@v1 (T14.1 copy, T14.2 plans area/extra selection, T14.3 entry links, T14.5 visual review; T14.4 integrates browser behavior and T14.6 audits). This exploration is a **breaking visual alternative** in layout/local navigation/responsive arrangement if chosen; it is behavior-compatible with the shared r3 brief. No approved contract or consumer reference changes. SP-1 data contracts and SP-2’s selected access/account contract remain untouched; no additional global navigation entry is proposed.

Open owner questions: **none**. Round 13’s comparison-only behavior is resolved. Numeric chat limits remain explicitly deferred and absent, rather than becoming a repeated question. Selection of this direction and plan/design approval remain owner decisions. The canonical owner-selected C design remains authoritative until a separate finalization. No production build, lint, authorization, network persistence or live catalogue check is attested by this design-only work.
