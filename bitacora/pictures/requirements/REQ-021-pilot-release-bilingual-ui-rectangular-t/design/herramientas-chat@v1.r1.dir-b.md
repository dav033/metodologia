---
name: Lienzo e inspector
contract_candidate: herramientas-chat@v1
revision: r1.dir-b
status: draft
subplan: SP-7
requirements: [R13, R16]
owner: David
approval: pending
---

# Direction B — Lienzo e inspector

Exploration only. This is a revision-specific design option, not the canonical twelve-section contract and not approved for implementation. Only a later owner-selected finalization may create the canonical pair. No production code, shared contract, plan, repository file or other direction was changed.

## Approach and existing surface

Keep the Pictures/Sempertex masthead, ring-and-dot mark, horizontal route navigation, language/account controls and paper-panel vocabulary established by `cuentas-admin@v1`, `planes@v1` and `proyectos@v1`. Change the working area into a spatial workspace: entry on the left, a scene or materials in the middle, and results on the right. The scene remains the visual bridge between an input and the balloon count. This is a change to the existing guided chat/Taller surfaces, not a new visual identity or landing page.

The counter uses input / scene / shopping-list panes. The professional quote uses a section index / editable materials and expenses / totals inspector. The decorations explorer uses filters / grouped existing ideas / selected preview, under Taller-local navigation. Inicio contains only authorized tool cards. The guided chat retains a conversation and composer with an adjacent existing-idea preview; it is contextual evidence, not a replacement chat interaction specification.

The changed area borrows the Taller's familiar canvas-and-inspector arrangement while preserving the siblings' masthead. Normal chat and the Taller's existing library/editor remain owned by their current surfaces. The workshop view here is an illustrative destination, not an editor redesign.

## Evidence inspected read-only

- Behavioral source: `herramientas-chat@v1.r1.behavior.md`, all stated outcomes, copy rules, flows and screen states. SPEC R13/R16 and round 15; PLAN SP-7, UI binding and tasks T7.1/T7.5–T7.8/T7.10.
- Sibling canonical Markdown and HTML: `cuentas-admin@v1`, `planes@v1`, `proyectos@v1`; selected project TSX `proyectos@v1.r12.dir-c.tsx` provides the exact local font imports, semantic token mapping, shared shell and focus vocabulary.
- t12: `src/app/globals.css`, `layout.tsx`, `CabeceraApp.tsx`, `MenuApp.tsx`, `VistaGuiada.tsx`, `CotizacionProfesional.tsx`, `CampoGanancia.tsx`, `ResumenPrecio.tsx`, `IdeasDelAsistente.tsx`, `Biblioteca.tsx` and existing decoration names from `src/lib/biblioteca-sempertex/decoraciones.json`.
- asesor: existing `src/app/globals.css` confirms the same source palette. No repository edits. Pre-existing t12 modifications were observed and left intact.
- Installed kit manifest/runtime/reference, `directions.md`, `mockup-craft.md`, UI contract authoring and version/impact skills. Real offline kit status: `installed=True built=True entries ok=96/96`.

## Eight axes

| Axis | Observable choice |
|---|---|
| Concept | A decoration between its inputs and its result: a spatial working surface inside Pictures. |
| Layout | 260px entry / flexible scene / 270px result. Gallery keeps the three panes; calculator adapts them to 230px index / material form / 290px totals. Home pairs a 260px contextual column with tool cards. |
| Navigation | Existing neutral horizontal routes; Inicio opens each authorized tool. Method buttons stay in the counter entry pane, cost section anchors jump within the material form, and Taller-local links enter/leave Decoraciones. |
| Typography | Existing Geist Sans, page title 24px, tool titles 18–20px, body 14–15px, metadata 12–13px, result 30px with tabular figures. Existing Geist Mono only for Sempertex. |
| Density | All desktop work areas remain visible side by side. Tablet moves the result below; phone stacks entry, scene, result. Padding 24px desktop and 20px phone; no nested decorative card grids. |
| Components | Real shadcn/Base UI Button/Input/Skeleton and Animate UI AlertDialog. Recompose the existing pills, native account disclosure, divided panels and contextual SVG scene. |
| Colour | Exact Pictures tokens and source Taller scene surface, both themes. Accent identifies primary actions and the clearly illustrative balloon drawing; navigation stays neutral. |
| Motion | Opposing lateral arrivals for entry and inspector, center lifted 18px with .985→1 scale. Expressive 620ms cubic-bezier(.16,1,.3,1), 65ms card stagger; quick 180ms control feedback. Natural 340/140/30ms and subtle 180/100/12ms. Reduced/still removes travel and leaves every state readable. |

## Two thumbnails and selection

1. **Chosen:** `herramientas-chat@v1.r1.dir-b.html.candidate-1.html` — three simultaneous panes: form, scene, shopping list. Keeps measures and results visible together; provides the strongest common structure for the counter, quote and gallery.
2. `herramientas-chat@v1.r1.dir-b.html.candidate-2.html` — enlarged scene with a bottom entry dock and right inspector. It gives the canvas more area but disperses the counter's fields along the bottom edge and requires a larger change when the quote needs many editable rows.

Both were drawn before the full entry, then inspected as rendered compositions. Both retain local embedded Geist and source light/dark tokens; thumbnail controls are composition evidence only. The full mockup develops candidate 1.

## Tokens and actual components

No new palette, font family, brand or dependency. The entry embeds local Next WOFF2 assets. The built HTML embeds all assets and JS; no remote font/image, package install or runtime request is required.

| Project tokens | Kit roles | Light / dark |
|---|---|---|
| fondo | background | #faf9fc / #0b0c10 |
| superficie | card, popover | #ffffff / #16181f |
| superficie-suave | local subtle grouping | #faf8fd / #1c1e26 |
| superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| texto | foregrounds | #1c1425 / #f4f5f7 |
| texto-suave | muted-foreground | #6b6178 / #9aa1ad |
| texto-tenue | accessible input edge, inherited sibling treatment | #766c85 / #8a91a0 |
| acento / sobre-acento | primary, ring / primary-foreground | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| borde / borde-suave | decorative outlines / rules | #e3daef / #efe9f8; #383c48 / #2a2d38 |
| error / error-suave | error text / surface | #b23a45 / #ffeaec; #ff979f / #43252a |
| taller-visor | illustrative canvas | #ebe7f1 / #1a1722 |

Radii: panels 32px, inset 24px, fields 18px and pills 999px, inherited from the chosen siblings. Other success/warning/sidebar/chart roles are the same mapped sibling tokens, not a new colour system.

- `shadcn:button default|outline ready|hover|focus|pressed|disabled` — `@/components/ui/button`; real Base UI-backed actions, styled with the product pill treatment.
- `shadcn:input default empty|filled|invalid|focus` — `@/components/ui/input`; measurements, costs, search and named-save illustration.
- `shadcn:skeleton default loading` — `@/components/ui/skeleton`; static placeholders and visible loading text, no indefinite motion.
- `shadcn:alert-dialog unsaved open|closed|invalid` — `@/components/ui/alert-dialog`; installed Animate UI/Base UI modal with inert background, focus containment and explicit cancellation. Custom action grouping preserves the project's button vocabulary.
- Custom native method buttons, section anchors, permission fixture select, file input and details/summary account disclosure. These are not claimed as additional kit components.
- Custom SVG neutral decoration preview: an illustrative scene, never the real engine/photograph or a source of counts.
- `@kit/mockup` supplies the visible Mockup label and native `view`, `state`, `scene`, `theme`, `motion` inspectors. `@kit/motion` supplies the profile/reduced state and `motion.strong` numeral spring.

## Views, flows and state coverage

| View | States / recovery | Main flow |
|---|---|---|
| Inicio | Available tools only; no empty state because every signed-in role has tools. Other global inspector states are inapplicable here. | Account fixture selects Entusiasta/Designer (2), Designer Plus (3), Master Designer or staff (5). No locked card, upgrade plan name or price appears. Tool selection preserves the fixture account. |
| Chat | Initial, normal conversation, missing-measure question, loading, error/retry, no-costs. Other global states leave the normal fixture. | Existing guided conversation/composer; counter shortcut; authorized Taller connection. Price-free contextual fixture for all accounts. |
| Counter | Initial, missing measure, counting, result, file-too-large, non-image, engine error/retry, no-costs. | Form / phrase / photo → quantity per size/colour + shopping list, no prices. Only `costos.usar` gets Calcular costo → calculator imported state. |
| Calculator | Empty, imported from counter, editing, calculating, totals, quote error/retry, permission refusal. | Manual or imported materials → editable unit price/quantity + labour/equipment/transport/indirect costs + existing Tu ganancia → totals inspector. Editing suppresses old totals until recalculation. |
| Gallery | Loading, results, no filter matches, load error/retry, unknown decoration id, current scene unsaved, permission refusal. | Search + occasion + size filter → choose an existing idea → preview → real anchor destination `/3d?decoracion=<id>` with simulated in-mockup opening. |
| Taller context | Current scene with unsaved work or newly opened unsaved scene. | Decoration open starts an unsaved new project. Existing editor/library are contextual, not redesigned or fully implemented. |
| Unsaved-work modal | Open, invalid empty project name, cancel, simulated save/continue, explicit discard/continue. | In Gallery's unsaved state, opening asks before changing the scene. Cancel preserves the current scene. Save requires a name; discard is a separate action. |

Every listed state has a native inspector option; the scene inspector independently opens the modal. Shared state values are contextual, not a claim that every screen has every state. Home empty, gallery unfiltered empty catalogue and offline-specific states are not introduced by the brief. All original catalog items must be listed in production; the gallery fixture intentionally contains only three clearly marked sample records.

Counter inputs, file-type validation, method switching, quantities, price editing, filtering, preview selection, retry buttons, section anchors and scenario selectors are interactive local examples. Form changes suppress the previous fixture count. Counts do not recompute real engine geometry. The full artifact labels every count/price/operation as simulated. Photo tolerance ±10% is a labelled fixture, never a proposed production tolerance.

## Responsive and accessibility targets

- **360–639px (390px check):** 20px gutters, wrapping masthead/routes, all workspace panes stack in reading order. Gallery list follows filters and precedes preview. Quote rows place product identity above two numeric fields. Modal width viewport minus 40px, 24px inset, actions wrap and content scrolls vertically.
- **640–1099px (768px check):** 24px gutters, 230px input beside the flexible working area; result/preview moves below and uses two columns. Chat stacks conversation/context. Home tools become one column beside context. No fixed panel covers content.
- **1100px+ (1280px check):** 40px gutters, maximum app width 1520px; simultaneous three-pane workspace. Forms/results have 24px insets.

Targets: WCAG 2.2 AA, labelled semantic controls, visible 3px focus outlines, ≥44px control height, text ≥4.5:1 and control boundaries ≥3:1, no page horizontal scrolling. Number/unit/colour remain textual; no colour-only quantity meaning. Error and loading messages use alert/status semantics. Native filters/method buttons work by keyboard. AlertDialog must contain focus and restore it on cancellation; Escape account disclosure returns focus to summary. Real screen-reader, 200–400% zoom and production WebGL/access enforcement need independent verification. The visible ES/EN control is inherited shell context; full translation remains SP-10, and its mock response explicitly says so.

Motion is finite and transform-first; content is legible throughout. Hidden-tab CSS animation pauses. OS reduced motion, Quieto and `?still=1` remove CSS travel and the installed Motion profile jumps to final content; no indefinite loading animation is used. The JSON evidence selectors identify real moving elements rather than the document root.

## Observable acceptance examples

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-01 | All | All | The Pictures/Sempertex masthead and inherited Geist/token vocabulary remain visible. |
| B-02 | 1100px+ | Counter result | Input, scene and shopping list form three adjacent panes. |
| B-03 | 640–1099px | Counter result | The result pane appears below the input and scene. |
| B-04 | 360–639px | All | Content stacks with no horizontal page scroll. |
| B-05 | All | No-costs | Counter and chat show no money; counter has no Calcular costo action. |
| B-06 | All | Calculator editing | Previous totals are hidden and a recalculation instruction is visible. |
| B-07 | All | Counter imported | Calculator shows the counter-material origin. |
| B-08 | All | Gallery results | Ideas del asistente and Ideas Sempertex stay identifiable. |
| B-09 | All | Gallery filtered | Search, occasion and size narrow the sample records; preview belongs to a matching record. |
| B-10 | All | Unknown id | Not-found message states that the open scene has not changed. |
| B-11 | All | Opening with unsaved work | The modal separates save, discard and cancel; empty-name save shows validation. |
| B-12 | All | New project opened | Taller context reads Escena nueva and Sin guardar todavía. |
| B-13 | All | Reduced/still | All actions/state text remain available without travel or numeral spring. |
| B-14 | All | Inicio authorization fixture | Tools lacking permission are absent rather than locked or promoted. |

## Open questions and assumptions

Q: ¿Se conserva «Tu ganancia» como porcentaje añadido al costo, tal como hace hoy CotizacionProfesional, aunque el brief lo llame «margen», o se quiere cambiar esa regla?
Q: ¿Qué límite de tamaño y formatos de foto debe mostrar el contador, y qué datos de tolerancia devuelve el motor para cada estimación?
Q: ¿Decoraciones debe tener también una tarjeta directa en Inicio, además de vivir dentro del Taller, como en esta propuesta de cinco herramientas?

Decision owner: David/Planner. Questions are recorded without stopping the exploration. Assumptions shown explicitly: preserve the existing additive-gain rule; account/permission controls are mock-only; illustration/count/photo tolerance/prices are fixture data. No real price source, AI response, server authorization, engine computation, ledger row, project save or idempotency is asserted by this static artifact.

## Impact and approval boundary

SP-7 candidate for T7.1, UI implementation T7.5–T7.8 and visual review T7.10. Compatible with the inherited shared shell; the new tool home, counter, calculator and gallery are a breaking interaction/layout addition relative to the existing single entry surface and require their planned implementations. SP-2/SP-4/SP-14 shared shell is reused; no sibling contract consumer was modified. SP-10 owns new-string extraction/translation. SP-1 owns real permissions and source catalogue. Approval remains pending; this exploration cannot be copied as an approved contract.

## Honest verification

The full TSX entry uses the real installed offline builder, without HTML fallback or package installation. The final phone modal was visually corrected to stack its actions; no production build/lint/API tests were appropriate for this read-only design exploration.

| Check | Actual evidence |
|---|---|
| Offline build | Exit 0; 642 KB, 2,132 source files, all assets inline. |
| Token contrast | Exit 0; `contrast: 158 pairs checked in light and dark, all pass`. |
| Final rendered audit | Exit 0; 648 renders / 648 planned combinations at 1280/390/768px in both themes, 19,176 text measurements, 2,146 focus stops. No combination sampling. One focus walk reached the 60-stop cap; later controls in that walk were not measured. |
| Focused flow probes | `INTERACTIONS: PASS 8 groups; page errors=0; external HTTP(S) requests=0`. Covers authorized tool counts/account retention, calculator refusal, counter handoff, price edit retention and COP 82,800 fixture total, phrase/photo method retention, explicit photo tolerance, grouped gallery search/filter/matching preview/link, unsaved-name validation/cancel focus/save/new-unsaved state, unknown link, permission refusal and account Escape dismissal. |
| Final phone modal | `FINAL MODAL: PASS full-width actions, 12 settled keyboard containment checks and cancel focus return`. All three action boxes are 300px × 44.25px at 390px viewport. The initial immediate focus probe caught Base UI's transient focus sentinel; after its focus-redirection task settles, Tab cycles input → save → discard → cancel → input. No custom trap or library override was needed. |
| Motion | At 120ms, expressive has 6 running animations; OS reduced motion has 0; `?still=1` has 0. |
| Axis evidence | `JSON EVIDENCE: PASS 16 selectors match rendered elements across declared views`. Motion selectors are real animated panes/cards; JSON is parseable. |
| Reflow spots | `REFLOW: PASS 360/390/768/1280px counter spot checks`; rendered audit also traverses every declared combination at its three widths. |
| Visual inspection | Both candidate thumbnails; desktop light counter/calculator, desktop dark home/gallery, phone light counter, phone dark calculator/modal, tablet light gallery. Screenshots were inspected in memory, without additional artifact files. The inspected final phone modal has three full-width actions and visible name/error context. |
| Whitespace | Scoped working/staged `git diff --check` passed. |

Earlier checks exposed a light chat-placeholder contrast failure (3.43:1), a local calculation completion that reset edited prices, and cramped phone-dialog action labels. These were corrected with source tokens, local state completion and stacked phone actions respectively; the focused checks above verify the corrections. A first mouse automation locator waited on stability; the completed flow walkthrough uses actual keyboard activation and does not assert a complete mouse walkthrough.

Reproduce the build and required audits:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.r1.dir-b.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.r1.dir-b.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.r1.dir-b.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.r1.dir-b.html --widths 1280,390,768 --max-combos 240
```

Final HTML SHA-256: `7ca3a5308ef53c50320fab56d784effc7fd2fd5fb3e4e505f70099667af06332`.

CONCERNS: owner questions above remain open; approval and production authorization/calculation/storage/translation verification remain outside this exploration. No canonical contract, shared HTML, preview directory or production source was written.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

`warning: 1 focus walks stopped at 60 stops; later controls were not checked`

This is the final HTML audit result. The cap limits automated focus coverage for that one traversal; it is not a claim that every possible keyboard stop was checked. The separate settled modal checks establish the specific four-control focus cycle and return behavior described above. Full accessibility/production acceptance remains pending.
