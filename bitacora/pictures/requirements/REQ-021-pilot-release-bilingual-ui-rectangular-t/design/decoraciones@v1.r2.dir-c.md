---
name: Edición en el lugar
contract_target: decoraciones@v1
status: draft
artifact: exploration
direction: c
revision: r2
subplan: SP-5
requirements: [R8]
owner: David
date: 2026-10-29
behavior_source: decoraciones@v1.r2.behavior.md
chosen_thumbnail: decoraciones@v1.r2.dir-c.html.candidate-1.html
---

# Direction C — Edición en el lugar

## 1. Identity and scope

Planning exploration only; unapproved. This note is not the canonical `decoraciones@v1` contract and does not authorize implementation. The owner chooses the direction before a finalizer writes that contract. No canonical contract, plan, production source, shared log or preview directory was changed.

Behavioral authority: `decoraciones@v1.r2.behavior.md`, SPEC “Behavior — SP-5 (round 11 answered)” and the SP-5 outcome/product criteria in PLAN.json. The owner's 2026-10-29 feedback governs: no browser-library import, server-confirmed saved status, staff read-only originals, placement as an owned-scene copy, Taller permission and immediate account-switch isolation. T5.1 is the subsequent contract-copy gate; T5.3 implements the UI; T5.5 owns independent visual review. This exploration neither edits those tasks nor claims their acceptance.

## 2. Purpose and approach

The working question is: “Which part of this scene should I save, and which saved decoration should I add here?” Keep the existing Taller visible while answering it. Selecting the scene's piece unfolds the save form in the existing inspector. Saved items sit in a thumbnail shelf attached below that same workspace. Opening a tile reveals its preview, placement and optional metadata editing in place, without a new route or full-screen details page.

Users are signed-in Master Designers and staff with Taller access. The account-owned library is separate from the global/admin catalogue. Staff inspect another account's original with a read-only badge and no rename/edit/delete controls; “Añadir a mi escena” creates a copy in their own open scene. The inspector still addresses their current scene, never the foreign library original. Account-deletion restrictions remain in the existing SP-2 account surface; this exploration adds no account administration page.

## 3. Existing surface, composition and thumbnail choice

Read-only production references: both repositories' `src/app/globals.css`; t12 `src/app/layout.tsx`; `src/components/tres-d/Biblioteca.tsx` (`AccionesPieza`, `Ficha`, `FiltrosCompactos`, local library); its Taller consumers. Existing controls supply “Guardar en mi biblioteca”, “Guardar toda la escena en mi biblioteca”, “Nombre”, “Ocasión”, “Añadir a mi escena” and the occasion/colour/balloon filter vocabulary.

Sibling references: `cuentas-admin@v1.md/.html`, `planes@v1.md/.html`, `proyectos@v1.md/.html`, and the selected projects source `proyectos@v1.r12.dir-c.tsx`. Preserve the Pictures ring-and-dot mark, Sempertex wordmark, account/language controls, 24px task title, neutral horizontal Taller 3D / Proyectos navigation and the workshop tool/canvas/inspector vocabulary. Account-menu and project destinations outside SP-5 show a Mockup scope notice instead of pretending to implement those subplans.

Two actual HTML compositions were drawn before the full TSX:

- **Candidate 1, chosen:** existing rail/canvas/inspector above an attached thumbnail shelf. Piece-save fields remain beside the current scene. Its thumbnails open one detail below the shelf. It preserves the existing scene inspector and keeps the library a contextual addition.
- **Candidate 2:** a library column to the left of the scene with the save form below the canvas. This consumes the space normally used by the existing scene layout and separates the piece-save controls from the scene inspector. It is weaker for this brief.

The complete artifact develops candidate 1; both thumbnail files remain available. Thumbnail HTMLs are deliberately small composition sketches; full interactive state coverage, both themes, real-library composition and audit evidence belong to the built HTML, not to the sketches.

## 4. Fixed visual system and eight axes

Exact production tokens, light / dark: `--fondo` #faf9fc / #0b0c10; `--superficie` #ffffff / #16181f; `--superficie-suave` #faf8fd / #1c1e26; `--superficie-2` #efe9f8 / #242733; `--borde` #e3daef / #383c48; `--texto` #1c1425 / #f4f5f7; `--texto-suave` #6b6178 / #9aa1ad; `--texto-tenue` #766c85 / #8a91a0; `--acento` #6d3fe0 / #9479ff; `--sobre-acento` #ffffff / #120b24. Success/error/warning and workshop-scene colours also come from `globals.css`. No palette or font-family proposal is introduced.

Kit mapping: background→fondo, card/popover→superficie, foreground→texto, muted/secondary→superficie-2, muted-foreground→texto-suave, primary/ring→acento, primary-foreground→sobre-acento, input→texto-tenue, destructive→error, success→exito, warning→aviso. Nonessential separators use borde; meaningful control edges use texto-tenue. Existing local Geist Sans / Geist Mono WOFF2 assets are embedded offline. Sibling shape roles remain panel 32px, inset 24px, field 18px and pill 999px.

| Axis | Direction C, observable in the artifact |
|---|---|
| Concept | Save the current piece/scene and reuse saved items within the existing working Taller. |
| Layout | Rail, scene and inspector remain above a three-column library shelf. One chosen tile unfolds a preview and metadata/placement area beneath the shelf. |
| Navigation | Canvas selection opens the inspector form; tile buttons expand/collapse their detail; local entries and colour/balloon filters use native disclosures. The product's horizontal routes remain. |
| Typography | Existing Geist: title 24px, library 20px, detail 18px, item name 15px, controls 14px and support 12–13px. Geist Mono is limited to Sempertex. |
| Density | Thumbnail + identity + ficha affordance share each compact peer tile. Save and metadata forms appear only on demand. No new dashboard, KPI tiles or promotional material. |
| Components | Installed shadcn/Base UI Button, Input and Skeleton; Animate UI AlertDialog for removal. Native selects/details retain filter and disclosure semantics. |
| Colour | Existing accent identifies save/placement and selected items. Navigation remains neutral; confirmed success and failure use production semantic colours plus words. |
| Motion | Tactile compression and settling, finite 480ms tile choreography with 50ms stagger, hinged form/detail reveal and a success stamp. Repeated actions use 180ms feedback. Reduced-motion parity is explicit. |

Real imports: `@/components/ui/button` (`shadcn:button default/outline`, normal/hover/focus/pressed/disabled), `@/components/ui/input` (`shadcn:input`, editable/invalid/disabled), `@/components/ui/skeleton` (loading), `@/components/ui/alert-dialog` (`shadcn:alert-dialog` with installed Animate UI transitions). Custom composition: `.studio-body`, `.inline-save`, `.library-grid`, `.piece-detail`; SVG scene/thumbnail fixtures are illustrations, not a WebGL renderer or a thumbnail-generation feature.

## 5. Interaction and motion detail

Clicking the scene's named piece or “Guardar en mi biblioteca” reveals the form next to the scene and focuses its name. “Guardar toda la escena…” uses the same location with the entire-scene scope. Fields stay mounted while typing. Trimming to an empty name exposes an associated error; a valid submission disables duplicate submission and shows “Guardando…”. Only the simulated acknowledgement changes that text to “Guardado en tu biblioteca.” and adds the named item.

Each thumbnail is a keyboard button with `aria-expanded`/`aria-controls`. At most one detail is expanded. Name and occasion editing happen beside that item's preview; Cancel preserves the original metadata. Placement inserts an illustrative copy and announces that the original is unchanged. Removal requires the real AlertDialog, preserves project copies, and restores focus to the invoking control on cancellation or the library heading after removal.

The tactile gesture compresses a tile to .975, or a control to .965, before settling. CSS tile keyframes move 8px down → 2px up → rest, with `cubic-bezier(.34,1.4,.64,1)` and finite 480ms choreography. Save/detail forms hinge from the top by 6px, never disappear behind opacity. Success stamps .96 → 1.02 → 1. Natural/subtle profiles reduce durations/stagger. Motion's installed profile supplies press/placement springs. Hidden tabs pause CSS effects. OS reduced motion, Quieto and `?still=1` remove transitions/travel and retain every status word and action; no perpetual scene animation is added.

## 6. Flows

1. **Save:** select piece or whole scene → inspect scope/destination → enter name and occasion → submit → pending → confirmation and new tile. Failure preserves input and offers “Reintentar guardado”. The confirmed item is the account-owned server item in production; the HTML uses an explicit in-memory fixture.
2. **Find and place:** search by name and filter occasion/type; disclose colour and balloon filters when needed → choose tile → inspect preview → “Añadir a mi escena” → owned-project copy feedback. Clear-search/filter actions restore the permitted list.
3. **Owner update/remove:** expand owned tile → change name/occasion in place → confirm; or request removal → confirm/cancel. Busy controls prevent a second mutation. Content-replacement behavior is an open question below, not an invented control.
4. **Staff consultation:** Vista selects the staff fixture → choose authorized owner → expand foreign item → read-only original → place copy into the staff member's current project. No foreign edit or removal control appears. The prototype's owner selector is illustrative, never authorization.
5. **Browser-local entries:** explicitly open “En este navegador” → see browser-only fixture and place it if wanted. No import action, progress or error state exists. The mockup never writes or migrates `taller3d:biblioteca-propia:v1`.
6. **Account change/sign-out:** the Mockup account control switches account → prior tiles, open detail, save form and scene context are removed → loading surface → current account's own library. Sign-out hides the workshop/library. No previous account's server list is shown while the next account loads.

## 7. Views and visible controls

Native Vista exposes `library` (Mi biblioteca), `save-piece` (Guardar pieza), `save-scene` (Guardar escena), `staff` (Personal · Solo lectura). All are states of the same Taller shell; no decoration landing page or new global route is introduced. Native Diálogo exposes none or `delete`. Native Tema exposes light/dark; Idioma offers ES/EN for expansion checks. Mockup labels stay outside the product.

The library hierarchy is identity/scope → name search and occasion/type selectors → disclosed existing colour/balloon filters → peer thumbnails → selected-item detail → separate browser-only group. A loading/error/empty message replaces the server list without fabricating results. Staff see authorized owner context and read-only scope where an owner sees “En mi cuenta”. In the foreign fixture, the current-scene inspector can save the staff member's own scene; it does not edit the library original.

## 8. State coverage

Every declared state is reachable through native Estado. View/state combinations that concern another surface retain the context rather than invent a permission rule.

| State | Visible behavior and recovery |
|---|---|
| `normal` | Permitted mock account items; select, search, filter, place. Forms start disclosed only on save-specific views. |
| `loading` | Skeleton list and “Cargando biblioteca…”; no saved-item rows/counts. |
| `empty` | Empty account-server list; owner can save from the current scene. Browser-only entries remain separate. Foreign empty list offers owner-selection guidance. |
| `error` | List-load error and Reintentar; no fabricated successful list. |
| `saving` | Disabled duplicate save, busy form and Guardando; no success claim. |
| `saved` | Explicit confirmed-save fixture; success text with check. Ordinary interactive save reaches this only after its acknowledgement timer. |
| `save-failed` | Input retained, visible failure and retry; retry goes pending then confirms. |
| `no-results` | No matches and clear-search recovery; distinct from an empty account library. |
| `editing` | Owner's expanded ficha and inline name/occasion form. Staff never gain that form. |
| `validation` | Associated invalid-name message, corrected through input; no failed submission becomes a saved item. |
| `account-switch` | Previous account data removed; current-account loading surface only. Mockup continuation reveals an empty second account. |
| `permission-denied` | No workshop, scene or personal-library data; Taller-access explanation. |
| `session-expired` | Session-ended explanation; no scene or library metadata. |
| `delete-failed` | Original remains; failure and removal retry reopen the confirmation. |

Controls include hover, pressed, visible focus, disabled and busy. Import/import-progress/import-error are deliberately absent. Offline connectivity maps to the relevant list/save failure with explicit retry; the artifact makes no offline-success promise. The global catalogue, account deletion, server pagination, autosave, purchases and provider states are outside this direction's UI scope.

## 9. Responsive behavior

Supported design range: 360px upward; rendered audit checkpoints 390/768/1280px, both themes. At 1100px+ preserve the 60px rail, flexible scene and 310px inspector; library has three columns, search and native selectors share one row. At 640–1099px keep rail/canvas, move the inspector below the scene, arrange its form in two columns, use two library columns and wrap search above the remaining filters. At 360–639px hide the rail, stack scene → inspector → library, use one-column fields/tiles/detail, wrap masthead and title actions, and stack destructive-dialog actions. The scene remains in its bounded frame.

Outer gutters are 40px desktop, 24px tablet and 20px phone. Library padding is 28px desktop / 20px phone. Long labels and English expansion wrap; no horizontal page scrolling. Longer save/error/detail states scroll vertically without hiding an action. AlertDialog caps height at viewport minus 48px and width at viewport minus 40px, maximum 540px. In a tall working Taller, the library follows the canvas; it is reachable by normal vertical scrolling rather than a second route.

## 10. Accessibility targets

Target applicable WCAG 2.2 AA; these checks do not certify production conformance. Headings, navigation/current route, labels, associated invalid fields, polite save/placement status and actionable error alerts are semantic. Tiles and disclosures support keyboard operation. Focus is a 3px product-accent outline with 4px offset. Buttons/fields target at least 44px height. Text targets ≥4.5:1; meaningful edges/focus ≥3:1; colour is accompanied by words. Selected tiles expose expansion state and an associated detail.

Use the installed modal behavior for inert background, focus containment, Escape and return. Busy mutations cannot be dismissed as completed work. Save fields receive focus when opened and preserve focus while typing. Removal cancellation returns to its trigger; successful removal focuses the surviving library heading. Reduced-motion behavior preserves task completion and visible status. Screen-reader testing, zoom and the actual production WebGL/API/permission behavior remain implementation acceptance responsibilities.

## 11. Visual acceptance and actual verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-AC-01 | 360px+ | All | Pictures/Sempertex, Geist, language/account controls and neutral Taller/Proyectos navigation retain the sibling vocabulary. |
| C-AC-02 | 1100px+ | Normal | Scene and inspector remain above a three-column thumbnail shelf. |
| C-AC-03 | 640–1099px | Normal | Inspector follows the scene and the shelf has two columns. |
| C-AC-04 | 360–639px | Normal / error | Fields, tiles and detail stack without horizontal page overflow. |
| C-AC-05 | All | Save piece / scene | Named scope, account destination, name and occasion appear within the inspector. |
| C-AC-06 | All | Saving | Guardando is visible and duplicate save is disabled; confirmed-save text is absent. |
| C-AC-07 | All | Save failed | Entered metadata remains alongside Reintentar guardado. |
| C-AC-08 | All | Staff expanded | Solo lectura is visible; original rename/edit/remove controls are absent. |
| C-AC-09 | All | Placement | A copy appears in the mock scene and feedback states that the original is unchanged. |
| C-AC-10 | All | Account switch / sign-out | Previous server tiles, selected ficha and save form are absent. |
| C-AC-11 | All | Local group open | Browser-only entries have their own explanation and no import action. |
| C-AC-12 | All | Loading / empty / error | Skeleton, empty guidance or retry explanation replaces the server list as appropriate. |
| C-AC-13 | All | Filters open | Existing colour and balloon selectors remain labelled, keyboard reachable and clearable. |
| C-AC-14 | All | Remove dialog | Cancel preserves the item and returns focus; confirmed removal removes only that item. |
| C-AC-15 | All | Reduced / Quieto / still | Final content and status words remain while travel and perpetual effects are absent. |

Evidence for this direction's final HTML:

| Check | Actual result |
|---|---|
| Installed real kit | `installed=True built=True entries ok=96/96`. |
| Offline build | Exit 0; 639 KB, 2,132 source files bundled. React, actual installed controls and both local fonts are inline. No package installation or asset fetch. |
| Token contrast | Exit 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Final rendered audit | Exit 0: 360 renders / 360 planned combinations; 16,092 text measurements and 2,322 focus stops at 1280/390/768px in both themes, no sampling. |
| Expanded filter/local disclosures | `EXPANDED DISCLOSURES: PASS 4 renders`, 390/1280px light/dark, using the audit's actual rendered probes. |
| Focused interactions | `INTERACTIONS: PASS 15 groups; 0 page errors; 0 external HTTP(S) requests`. Includes input focus/validation, pending→confirmed save, retry, metadata update, filters/search, local separation, staff read-only/copy, owner change, removal cancel/focus/confirm, account switch/sign-out and English reflow at 360/390/768/1280px in both themes. |
| Motion probe | At 120ms: 3 active expressive animations, 0 with OS reduced motion and 0 with `?still=1`. |
| Axis evidence | `compare_directions.py` on this artifact: `RESULT: PASS`, `evidence_ok=true`, no missing selectors. This is a single-direction selector check; no pairwise distinctness claim is made. |
| Visual inspection | Both candidate compositions, default 1280/390px light/dark, expanded 1280px dark staff ficha and 390px light save failure inspected from in-memory screenshots. No screenshot files added. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

The initial audit returned `RESULT: FAIL — alignment 18`: the phone empty/error message's nested framed inset created an inconsistent alignment axis. The list message was flattened onto the shelf's existing alignment, then the final build and full audit above passed. An initial TSX composition build caught a JSX helper-call syntax error; it was corrected before rendering. Neither check was suppressed, sampled down or reclassified as passing.

Reproduction:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.html --widths 1280,390,768
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/compare_directions.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.html
```

## 12. Open questions, limits and impact

Q: Should updating an owned saved decoration replace its composition with the current piece/scene, or only change its name and occasion? Owner: David/Planner. This exploration demonstrates the confirmed metadata controls and does not invent content-replacement behavior.

Confirmed: browser-local decorations are not imported; only the owner updates/removes originals; staff placement creates a copy; the personal library requires Taller; saved status waits for acknowledgement; account changes remove prior server items. The staff owner selector's two entries are neutral fixture data, not a new role/grant or a claim about the account-list API.

Fixture limits: in-memory timers illustrate server acknowledgements; reload/cross-browser persistence, authorized server queries, account identity, real storage isolation, retry idempotency and content fidelity are not implemented or proven by this HTML. Colour/balloon fixtures are explicitly labelled examples, not catalogue claims. The real legacy browser key remains untouched. No app server, paid provider or credentials were used. No production lint/typecheck/build/test suite was run because both repositories are read-only inputs and production code was unchanged.

Impact: SP-5 Taller save/list/detail/staff/local/account-switch surfaces, future T5.1/T5.3/T5.5. Compatibility is **undetermined until selection and approval**; the exploration changes hierarchy, disclosure and responsive arrangement relative to today's local-only library, so implementation will require adaptation. Sibling shell/tokens/fonts/navigation are reused; no consumer reference is redirected. The canonical contract, independent approval, production implementation, API guarantees and cross-direction comparison remain with their assigned owners.

CONCERNS: one owner question above; draft exploration, not approved. No toolchain fallback or missing token source. Final artifact audit passes; its evidence applies only to this static planning artifact.
