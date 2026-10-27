# Pliegues de consulta · información abierta

## 1. Identity and traceability

- Artifact: `planes@v1.r2.dir-a`, independent planning exploration, **status: draft**, not an approved contract.
- Intended contract: `planes@v1`; SP-14, R17–R20. Owner: David. Design date: 2026-10-27.
- Behavioral authority: `planes@v1.r2.behavior.md`, SPEC “Behavior — access plans and plans section” and “Behavior — SP-14 extra view (round 13 answered)”, PLAN.json SP-14.
- Fresh composition, not a patch or copy of a previous planes draft. This exploration retains the owner-selected consultation-fold idea while removing folding controls entirely.
- Scope supersedes the canonical-output request: only the two revision-specific candidate HTMLs, this direction's TSX/built HTML/MD/JSON and delegated RESULT are written. No canonical contract, history, production code, shared log, SPEC or PLAN changes.

## 2. Purpose and users

Answer “What tools and monthly price does each plan include?” for a visitor or signed-in person. A second view answers “Which plan am I comparing?” without acquiring it, requesting it, registering or changing account assignment. The full comparison remains readable without selecting anything.

The preview also demonstrates the existing sign-in plans link and account-menu plans link. Authentication/account editing remain SP-2 behavior; entry-point screens are contextual mock snapshots, not a replacement design for SP-2.

## 3. Approach, hierarchy and chosen thumbnail

**Chosen: `planes@v1.r2.dir-a.html.candidate-1.html`.** Its continuous ruled sheet preserves comparison order and avoids fitting four long columns onto tablet. Candidate 2 explores two-by-two plan blocks; the separated blocks make cumulative reading less direct. Both thumbnails were drawn before the complete TSX.

Preserve Pictures/Sempertex masthead, ring-and-dot mark, language control, rounded paper, neutral horizontal section navigation and native account disclosure from `cuentas-admin@v1`. The consulted `proyectos@v1` and `taller-esenciales@v1` reinforce the same production token/font vocabulary; their library/editor-specific rails are not added to this public section.

Change only plans-specific content: four ordered open folds, each comprising plan name → monthly price → complete included-tools list. Desktop places a short in-page index beside the single paper. Tablet moves that index above the paper. All tools are in normal document flow. No accordion, hide/show control, plan recommendation, promotional badge, invented benefit or marketing headline.

Plan order: Entusiasta / Enthusiast, Designer, Designer Plus, Master Designer. Each block repeats its full cumulative list, avoiding memory-dependent “everything above” references. Designer's higher-limit chat replaces the lower-limit chat line. Plus and Master display all three unavailable tools individually with the exact unavailable label.

## 4. Design system and eight-axis evidence

| Axis | Present expression |
|---|---|
| Concept | Open consultation folds; dense working information with all tools present and selection limited to comparison. |
| Layout | One divided paper, horizontal name/price and tools blocks, 192px desktop index, two-column index above tablet content, stacked phone blocks. |
| Navigation | Existing Pictures/Sempertex header; neutral comparison/selection route rule; plan anchors; account/login links and explicit return. |
| Typography | Existing Geist Sans / Geist Mono embedded from the t12 production build. Page title and prices 24px; plan names 20px; tools 14px; availability 12px. Tabular price figures. |
| Density | 12px tool gaps, 24px row separation, 28px paper padding, 20px phone insets. No nested cards. |
| Components | Installed shadcn/Base UI Button, Input and Skeleton; native disclosure/select/radio; custom ruled plan list. No accordion. |
| Colour | Production light/dark Pictures tokens; neutral navigation, accent selection heading/rule and primary comparison-return action. No exploration palette. |
| Motion | Quick registration: 12px row translation, 45ms stagger and rule scaleX(.45→1), 300ms expressive cubic-bezier(.23,1,.32,1); 180ms controls, reduced/still parity. |

Sources inspected read-only in t12 and asesor: `src/app/globals.css`, `src/app/layout.tsx`, login and shell components, sibling canonical MD/HTMLs. Repository status/diff inspected; t12 has existing local changes, asesor was clean. No repository was edited. SP-1's planned `src/lib/planes/catalogo.ts` is absent in both inspected trees; the preview uses one clearly identified, static `plan-catalogue@1` fixture matching the brief and SPEC. Production must read SP-1's catalogue rather than copy this fixture.

| Product token | Kit role | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--superficie-suave` | soft surface | #faf8fd / #1c1e26 |
| `--superficie-2` | secondary, muted, neutral accent | #efe9f8 / #242733 |
| `--texto` | foregrounds | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted foreground | #6b6178 / #9aa1ad |
| `--texto-tenue` | input edge, as in sibling contracts | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primary, primary foreground | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| `--acento` | ring | #6d3fe0 / #9479ff |
| `--borde`, `--borde-suave` | decorative borders, rules | #e3daef / #efe9f8; #383c48 / #2a2d38 |
| `--error`, `--error-suave` | destructive, destructive-soft | #b23a45 / #ffeaec; #ff979f / #43252a |

Shape vocabulary follows the selected sibling: 32px paper, 24px floating disclosure, 18px fields and pill actions. Font files are embedded as data URIs from existing local Geist Latin WOFF2 files; no font fetch. Outline focus uses `--ring`, 2px with 4px offset. Decorative rules do not serve as form control boundaries.

Real components: `shadcn:button default|outline default|hover|focus|pressed` from `@/components/ui/button`; `shadcn:input email|password default|focus` from `@/components/ui/input`; `shadcn:skeleton loading` from `@/components/ui/skeleton`. Native language selector, account disclosure, fieldset and radio labels are identified honestly as native. Custom `.consultation`, `.plan-row`, `.tools`, `.plan-index` provide layout. `mountMockup/useMockup` come from `@kit/mockup`, `useMotionProfile` from `@kit/motion`, and row animation from `motion/react`. No fallback snippets or package installation.

## 5. Navigation, interaction and motion detail

- The sign-in screen adds exactly one `Planes` / `Plans` link to `/planes`. The existing form's wording and controls remain the SP-2 reference.
- The account disclosure retains Mi cuenta / My account and Cerrar sesión / Sign out and adds one Planes / Plans entry. No staff role or permission key appears in the plans section.
- Comparison and selection are local sibling views of `/planes`; a second top-level app destination is not added. The preview uses native Vista options to expose signed-out/signed-in variants separately.
- The index scrolls to a visible plan heading and focuses it without a second scroll. Tabs/buttons take focus to the new page heading. The public return goes to sign-in; signed-in return uses the originating product page. This isolated preview uses Mi cuenta as the signed-in origin fixture.
- In selection, native radios form one fieldset. Checking a plan updates only in-memory comparison selection. Name/rule accent and the text “Seleccionado para comparar” / “Selected for comparison” identify it independently of color. A polite status names the selected plan. All four complete tool lists stay visible.
- “Volver a la comparación” / “Return to comparison” works with or without a choice. A choice survives that return and focus moves to the chosen plan heading. With no choice, focus returns to the page heading. It does not label the choice as an account's current plan or claim successful assignment.
- Row entrance registers horizontally by 12px; stagger 45ms, without fading text. A horizontal rule draws from scaleX(.45) to 1. Expressive: 300ms, natural: 220ms, subtle: 140ms; easing uses the existing `--ease-out` curve. Hover index shifts 3px; button press shifts 1px; controls 180/140/100ms. Finite animations finish promptly; there is no persistent decorative animation. Hidden tabs pause CSS effects. MotionProfile and OS reduced motion, Quieto, and `?still=1` show final content immediately with every action intact.

## 6. Flows

1. **Public:** sign-in → Planes → read four full blocks → optionally choose for comparison → return to highlighted full comparison → return to sign-in.
2. **Signed in:** account menu → Planes → compare or highlight → return to original product page. The example account remains Entusiasta regardless of the highlight.
3. **Language:** initial ES/EN follows browser language; a preview language control exposes both variants. ES displays only COP; EN displays only USD. Language changes retain comparison selection. The selector is for inspecting SP-8's future shared control and does not add a separate currency choice.
4. **Failure/recovery:** loading → ready, empty or error. Empty/error offer Reintentar / Retry and preserve exit/navigation. Retrying the planning fixture restores ready. No incomplete catalogue is presented as a complete successful comparison.

## 7. Views and exact data

| Vista selector | Product view | Content and behavior |
|---|---|---|
| `plans` | Public comparison | No account menu; ordered four-plan paper, complete tools, index and return to sign-in. |
| `choose` | Public selection | Same shell/data; fieldset radios, explicit comparison-only explanation, selected status, return to comparison. |
| `plans-in` | Signed-in comparison | Same catalogue; named account disclosure present, return to origin. |
| `choose-in` | Signed-in selection | Same comparison-only radio flow with account disclosure; account assignment remains unchanged. |
| `login` | Existing sign-in entry | SP-2's centered access paper with email/password, invitation-only and administrator-reset wording, plus one /planes link. Form submission reports only that operations are simulated. |
| `account` | Account-menu context | Existing shell/disclosure and neutral example account metadata to demonstrate the /planes entry. Full SP-2 account editing is outside this exploration. |

| Plan | ES monthly price | EN monthly price | Complete visible tools |
|---|---|---|---|
| Entusiasta / Enthusiast | Gratis | Free | Chat con límites / Chat with limits; Contador de globos / Balloon counter; Catálogo / Catalogue. |
| Designer | 20.000 COP / mes | 7 USD / month | Chat con límites más altos / Chat with higher limits; counter; catalogue. |
| Designer Plus | 45.000 COP / mes | 14 USD / month | Higher-limit chat; counter; catalogue; Calculadora de costos / Cost calculator; Chat extendido / Extended chat; Detección de estructuras / Structure detection; Detección avanzada de globos / Advanced balloon detection. |
| Master Designer | 70.000 COP / mes | 25 USD / month | All Plus lines plus Taller 3D / 3D workshop. No separate ready-made decorations explorer line. |

Each of the last three tools in Plus and Master has “aún no disponible” / “not available yet”, with a clock icon rather than an availability check. No numeric chat limits. Actual fixture values are kept once in the TSX catalogue; every preview view consumes them. “Un administrador asigna el plan.” / “An administrator assigns the plan.” is the only acquisition explanation.

## 8. States

The native Estado selector exposes all declared catalogue states across the four plans views. It does not redesign the two SP-2 entry-point snapshots.

| State | Rendered behavior / recovery |
|---|---|
| ready | Four plan blocks with all tool lists and appropriate currency; zero or one highlighted comparison choice. |
| loading | “Cargando planes…” / “Loading plans…” and four skeleton groups with status/busy semantics; no fabricated prices or successful empty result. |
| empty | “Planes no disponibles” / “Plans unavailable”, retry instruction and Reintentar / Retry. Empty means unavailable catalogue, never zero-priced paid plans. |
| error | “No se pudieron cargar los planes” / “Could not load plans”, alert semantics and Reintentar / Retry. Exit remains available. |
| selected / unselected | Real radios and the adjacent live selection status, reached by interaction inside ready. Resetting the document clears the temporary choice; no persistence or account mutation is promised. |
| hover / pressed / focus | Real control states; index and buttons have quick spatial feedback, native inputs have visible focus. |

Success is ready or the acknowledged comparison highlight, not assignment success. Validation, permission-denied and mutation-pending are inapplicable: public read-only data and a local optional selection do not require permission or submission. Offline with no confirmed catalogue uses error/retry. Partial/stale data must not impersonate the complete four-plan catalogue; implementation can reuse error until a complete current catalogue is available. There is no state that changes privileges.

## 9. Responsive behavior

| Width | Concrete layout |
|---|---|
| 320–639px | 20px app/paper gutters, wrapping masthead, language/account tools on their own line, title/return stacked. Four-plan index in two compact columns; single-column plan blocks, all tools below their own name/price. Vertical scrolling only. |
| 640–1023px | 24px app gutters; index above paper in two columns. Each open plan is a 200px identity/price column beside one full tool column; no four-card squeeze. Paper padding 28px. At 768 and 834px all text and lists fit in normal flow. |
| 1024–1100px | 192px side index, 28px gutter; plan identity 190px, one tool column. |
| 1101–1439px | Side index retained; plan identity 208px, two tool columns. |
| ≥1440px | Same bounded 1520px app; plan identity 240px. No type or brand change. |

Long plan names and translated tools wrap. No fixed plan heights, carousel or horizontally scrolling comparison. Selected status and action footer wrap without overlapping tools. On phone the comparison is intentionally long because all tools stay available. At 320 CSS px, stacked blocks retain readability; tablet gets its own specified composition instead of inheriting desktop columns. A low-height viewport scrolls normally; no sticky footer covers tools. The inspection bar is separate mockup chrome.

## 10. Accessibility targets

Target WCAG 2.2 AA; automated preview checks are not a conformance certification. Logical landmarks, one H1, visible plan H2s, semantic tool lists, labelled selects and fieldset/legend radios. Radio keyboard arrows and Space use native behavior. Choice labels provide ≥44px target height. Buttons, exit links, disclosure and index links have ≥44px targets. Skip link reaches the page heading. Availability and selection have explicit text, not color alone.

Text ≥4.5:1; large text and meaningful form-control edges/focus ≥3:1. Price figures use tabular numerals. Entry labels remain associated with inputs. New navigation moves focus to the new heading, and returning to comparison focuses its visible selected heading. Account disclosure keeps native disclosure semantics; it does not claim an incomplete ARIA menu pattern. Error is an alert and selection updates a polite status. Reduced-motion/still preserves all content and keyboard actions. No external font/image, pointer-only interaction, hidden tool list, purchase action or required hover-only information.

## 11. Visual acceptance criteria and audit evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| A-01 | 320–1520px | ready | Four plan names appear in the required order. |
| A-02 | 320–1520px | ready, ES | Paid prices show COP / mes and no USD; Entusiasta says Gratis. |
| A-03 | 320–1520px | ready, EN | Paid prices show USD / month and no COP; Enthusiast says Free. |
| A-04 | 320–1520px | ready | Every plan has a complete visible tool list and no hide/show-tools control. |
| A-05 | 320–1520px | ready | Plus and Master each show three unavailable labels, including advanced balloon detection. |
| A-06 | 320–1520px | ready | Entusiasta uses limited-chat wording and Designer uses higher-limit wording, without a limit number. |
| A-07 | 768 / 834px | ready | Plan index is above the paper in two columns. |
| A-08 | 768 / 834px | ready | Open plan rows have 200px identity column beside one tool column with no page-wide horizontal scroll. |
| A-09 | 390px | ready | Plan title/price and all tools stack vertically inside 20px paper insets. |
| A-10 | 1280px | ready | Side index accompanies one paper and tools form two columns within each horizontal plan block. |
| A-11 | 320–1520px | ready, selection | One labelled radio per plan is present alongside all its tools. |
| A-12 | 320–1520px | selected | A plan name and explicit comparison-selected text identify the choice. |
| A-13 | 320–1520px | selected → comparison | Return preserves the chosen highlight and focuses its visible plan heading. |
| A-14 | 320–1520px | ready, signed in | Selecting another plan leaves the example account's assigned Entusiasta plan unchanged. |
| A-15 | 320–1520px | entry | Login has one /planes link and account disclosure has one /planes entry. |
| A-16 | 320–1520px | public | Account disclosure is absent. |
| A-17 | 320–1520px | loading | Skeletons and loading status replace catalogue prices. |
| A-18 | 320–1520px | empty / error | A retry control appears with a truthful unavailable/error message. |
| A-19 | 320–1520px | keyboard | Plan-index activation moves focus to the visible associated heading. |
| A-20 | 320–1520px | reduced / still | All plan content remains visible with no running movement effect. |
| A-21 | 320–1520px | ready | No purchase, request, sign-up, account assignment or permission control exists. |
| A-22 | 320–1520px | both themes | Product foreground/background and control tokens match sibling/production mappings. |
| A-23 | 320–1520px | all | Mockup label and labelled native Vista, Estado, Tema and Movimiento selectors remain visible. No dialog is declared. |

Verification applies to the planning artifact, not production implementation:

- Offline real builder: PASS, 531KB self-contained HTML, 2,031 bundled source files. No install or external asset fetch.
- `contrast.py`: **contrast: 158 pairs checked in light and dark, all pass**.
- Full rendered audit on final HTML: 96/96 combinations across six views, four states, two themes and 1280/390px; 2,488 text measurements and 404 focus stops.
- **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**
- An earlier audit found a centered-entry footer alignment mismatch; footer copy now shares its entry column's left edge. Final audit supersedes that failed result.
- Supplementary Playwright: 112 combinations across ES/EN, light/dark, public/signed-in comparison/selection and widths 320/390/640/768/834/1024/1280; all four plan blocks, 21 tool rows, six unavailable labels and correct single currency present; no horizontal overflow, page exceptions or HTTP(S) requests. This matrix preceded the final semantic heading improvement; final audit covers that improvement.
- Final-markup focused checks: visible-heading focus from selection/index, return-to-highlight, 390/768/834/1024/1280 reflow PASS. Actual five entrance animations observed (rule plus four rows), each 300ms; reduced-motion running animations: zero.
- Interaction checks also exercised sign-in/account-menu entry links and verified the preview account remains Entusiasta after selecting Designer Plus. No real account system is contacted.
- Screenshots inspected in memory: 1280px light/dark comparison, 834px dark selection, 390px light comparison and dark selection. No screenshot files were written outside the allowed artifact list.
- All JSON evidence selectors were checked against the default rendered view; all match. The account-menu selector was removed from default-view evidence because the public view correctly has no account disclosure.
- Limitations: native account-menu keyboard dismissal beyond native details, full SP-2 editing/authentication, production catalogue refresh, actual permissions and real navigation origin restoration require implementation review. No production lint/types/build or real account integration test was run; this delegation is design-only.

## 12. Open questions, assumptions and impact

**Open owner questions: none.** Round 13 q1 has resolved selection semantics. Approval is still pending; no contract or plan approval is inferred. Direction notes are ready for comparison/finalization, not implementation authority.

Confirmed: public and informative, four plans, all tools visible, exact prices and currency by language, no numeric chat limits, unavailable tools marked, Master Taller includes the full 3D editor, and only an administrator assigns an account plan. Browser language is the initial pre-SP-8 source. Temporary in-page selection is independent of session identity.

Presentation assumptions: comparison selection is kept in memory only; signed-in origin is Mi cuenta in this isolated preview; error recovery is a fixture reset; English UI labels translate existing requirement terms. Login/account snapshots establish the added links, while SP-2 owns their complete behavior and cannot be replaced by this preview.

Impact is limited to SP-14: T14.1 eventual approved-contract copy, T14.2 plans/selection/responsiveness, T14.3 entry links and T14.5 rendered review; T14.4 is the Planner's integration verification consumer, outside design execution. Responsive restructuring and the added selection view require implementation adaptation and are **breaking visual expectations** relative to an earlier hideable-tool comparison. This exploration does not change the account-assignment contract. SP-1 catalogue and permissions stay unchanged. SP-2's canonical contract, layout and existing destinations stay unchanged; this direction demonstrates only its already-required plans links. No extra SP-2 navigation entry is introduced. Canonical files and histories remain untouched.
