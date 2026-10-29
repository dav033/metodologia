---
name: Bandeja de escena
status: draft
kind: exploration
subplan: SP-5
contract_target: decoraciones@v1
revision: r2
direction: b
---

# Bandeja de escena

Planning exploration only. This direction is not approved and does not create or replace the canonical contract. The owner chooses among directions before a finalizer writes `decoraciones@v1`.

## Approach and existing surface

The changed area is the existing Taller 3D personal-decoration library, not a new page. Keep its scene context, tool rail, save-scene/save-piece vocabulary, scene/IA context, realistic-photo and shopping-list controls. Place the personal library in a tray below the canvas and keep the selected decoration's preview, occasion and placement action in a right-hand inspector. Saving uses the same inspector in place, so the current project remains visible. A thumbnail selects an item; the accent action adds it to the current scene. This reduces repeated per-item actions while retaining a spatial relationship between library, selected object and destination.

The Pictures/Sempertex ring-and-dot masthead, account/language controls, task heading, neutral Taller 3D / Proyectos route navigation, rounded shape roles and footer reuse the sibling vocabulary. Existing-tool and sibling-route buttons explicitly report their Mockup context rather than pretending to navigate a running product.

Read-only sources inspected: both repositories' `src/app/globals.css`, t12 `src/app/layout.tsx`, `src/components/ui/shell/CabeceraApp.tsx`, `src/components/tres-d/Taller3D.tsx` and `Biblioteca.tsx`; the sibling cuentas-admin, planes and proyectos canonical Markdown and built HTML; selected proyectos source `proyectos@v1.r12.dir-c.tsx` for the shared shell/token/font mapping. Behavior comes from `decoraciones@v1.r2.behavior.md` and SPEC's “Behavior — SP-5 (round 11 answered)”. SP-5's UI consumers remain T5.1, T5.3 and T5.5; no engineering-only work is designed here.

## Two thumbnails and choice

- Candidate 1: `decoraciones@v1.r2.dir-b.html.candidate-1.html` — the library occupies a side panel and the placement action runs along the bottom. This leaves less room for selected-item detail and couples selection with a detached action.
- **Chosen candidate 2:** `decoraciones@v1.r2.dir-b.html.candidate-2.html` — library tray below the scene, selected-item preview/actions beside it. The full mockup adds the inherited tool rail, actual controls, state inspectors, filtering and responsive adaptation to this composition.

Both static thumbnail compositions were drawn first and rendered/visually inspected at 1280px before the full entry was built. They are sketches, not an audited substitute for the complete mockup.

## Eight axes

| Axis | Rendered decision |
|---|---|
| concept | Keep the current Taller as the working surface: choose a saved decoration below the canvas, inspect it beside the canvas, then place a copy into the current scene. |
| layout | Existing Pictures masthead, heading and Taller 3D / Proyectos route rule; changed workshop area has a 56px tool rail, flexible canvas above a library tray, and a 280px detail inspector. Below 768px the inspector follows the tray; below 640px the rail disappears. |
| navigation | Local Mi biblioteca / En este navegador pressed-button navigation changes the tray scope without leaving the Taller; staff also have a labelled Propietario native selector. Selecting a thumbnail changes the inspector; on phone selection focuses and reveals that inspector. |
| typography | Inherited embedded Geist Sans body 15px, H1 24px/600, inspector and library headings 18px/600, tile names 14px/600, metadata 12–13px. Geist Mono remains in Sempertex masthead metadata. |
| density | Three compact thumbnail peers per tray row at desktop; two at 768–1099px and on phones, with generous 24px desktop / 20px phone panel insets. One inspector carries the detailed actions instead of repeating them on every thumbnail. |
| components | Real shadcn/Base UI Button, Input, Skeleton, Animate UI-backed Dialog and AlertDialog; native scope buttons, native selects and the inherited account disclosure. Inline SVG illustrates scene/piece thumbnails, never a fake renderer. |
| colour | Exact Pictures globals.css light/dark tokens mapped to kit roles, including fondo, superficie, texto, acento and Taller canvas/panel roles. Primary colour identifies placing/saving; control edges use the inherited texto-tenue accessible alias. |
| motion | Finite spatial entrance: library tray rises 24px, inspector enters from 32px right, selected preview seats with scale/rotation, placement springs into the canvas. Expressive 520ms elastic settling and 170ms control gestures; natural/subtle scale down. OS reduced motion, Quieto and still=1 settle immediately; CSS effects pause in hidden tabs. |

## Behavioral coverage

| View or state | Visible behavior |
|---|---|
| `library` | Personal account library, name search, occasion filter, scene/piece thumbnails, detail preview and Añadir a mi escena. Existing scene remains visible. |
| `save-scene` / `save-piece` | Inspector shows the entire scene or selected piece, labelled Nombre/Ocasión fields, Guardar/Cancelar. Empty-name validation keeps the form open. |
| `staff` | Propietario selects the illustrated account. Foreign detail visibly says Cuenta de ejemplo · Solo lectura; edit/delete controls are absent. Añadir copia a mi escena places a copy into the staff member's own current scene. The original is unchanged. Save-piece/scene buttons belong to that own scene and explicitly open the own-account save inspector. |
| Local scope | Separate En este navegador group with Mi escena fixture and local-only explanation. No import action, import progress, import failure, merged list or automatic migration. Legacy editing is not redesigned. |
| `loading` | Account tray skeletons and Cargando biblioteca; no previous results or selected-item detail. Local group remains independently available. |
| `empty` | Empty account list with a next action to save a scene; no invented saved entries. Foreign empty view offers no mutation of the foreign collection. |
| `error` | Could not load the account library; explicit Reintentar. The project scene stays present. |
| `no-results` | No hay coincidencias with clear-search action. Typed search and occasion filtering are also functional. |
| `saving` | Guardando… and disabled duplicate-submit/cancel controls; no saved claim. The demo operation completes only through a simulated acknowledgement. The inspector state itself remains pending until changed. |
| `saved` | Guardado en tu biblioteca only in the acknowledged fixture or after the demo acknowledgement; Ver en mi biblioteca returns to the saved item. |
| `save-error` | Form values and scene retained, explicit failure and Reintentar; retry reaches pending then acknowledged save. |
| `account-switch` | Whole workshop data region clears: no old thumbnails, selected detail or scene. Continuation illustrates the next account's empty list. Signing out uses this clearing fixture without claiming a real authentication flow. |
| `no-access` | No decoration metadata, canvas or library. Explains that the library requires Taller access. |
| `edit` dialog | Owner-only name/occasion form, labelled validation, pending save, simulated acknowledgement. No scene-content update is silently invented. |
| `delete` AlertDialog | Owner-only confirmation, cancel/Escape and pending deletion. Original library item is removed from the in-memory fixture on acknowledgement. Existing placed copies are presented as independent. |

Native inspectors are the real runtime's `view`, `state`, `scene`, `theme` and `motion`, outside the product root. They expose all declared states; state meaning is contextual: loading/empty/error affect the account tray, saving states affect owner save forms, staff foreign entries remain read-only, and account-switch/no-access take precedence over content and dialogs. Local scope is reached by its visible button; Spanish/English expansion uses the labelled language control. No import state is declared or present.

## Tokens, components and interaction detail

Use the project mapping inherited from proyectos@v1, not kit defaults: light/dark fondo `#faf9fc/#0b0c10`, superficie `#ffffff/#16181f`, texto `#1c1425/#f4f5f7`, texto-suave `#6b6178/#9aa1ad`, texto-tenue `#766c85/#8a91a0`, acento `#6d3fe0/#9479ff`, sobre-acento `#ffffff/#120b24`, and all existing success/error/warning and Taller roles. The TSX contains the full paired mapping. Control edges use texto-tenue; decorative rules use borde. Embedded local Geist Sans/Mono WOFF2 files come from the existing t12 Next build. Panel/field/pill radii reuse the sibling 32/18/999px vocabulary, with 24px workshop/inset surfaces. There is no new palette, typeface or external asset.

Real installed manifest components: `shadcn:button outline|default default|hover|focus|disabled|busy` from `@/components/ui/button`; `shadcn:input default|invalid|disabled` from `@/components/ui/input`; `shadcn:skeleton loading` from `@/components/ui/skeleton`; `shadcn:dialog open|closed` from `@/components/ui/dialog`; `shadcn:alert-dialog open|closed` from `@/components/ui/alert-dialog`. Installed dialogs use Animate UI/Base UI primitives. Mount/runtime imports are `@kit/mockup` and `@kit/motion`; placement additionally reads `useMotionProfile` for Motion's spring/reduced setting. The shell, scope navigation, thumbnail selection, inspector and scene SVG are custom compositions, not claimed as installed standalone components.

The spatial signature is an interruptible selection-to-inspector change and copy placement into the existing canvas; finite CSS entrance effects move the tray up and the inspector from the side. Content remains opaque/readable during travel. Press/hover feedback is short; there is no ambient loop, fetch or animation-only message. Reduced OS motion, Quieto and `?still=1` preserve all final states/actions without travel; visibility changes pause CSS effects.

Dialog semantics, inert background and keyboard containment come from the real primitives. Escape/cancel returns focus to the invoking control. If deletion removes that control, focus moves to the library heading. Phone selection reveals/focuses the inspector heading; save actions reveal/focus the matching form heading. Status uses text plus polite status or alert semantics; fields have labels and associated error text. Visible 3px focus outlines and 44px controls follow the sibling target. These checks do not certify full WCAG conformance, screen-reader output or production WebGL keyboard behavior.

## Responsive decisions

- 1100px+: inherited 40px shell gutter; 56px rail, flexible scene/tray and 280px inspector. Three thumbnail peers per tray row; search and occasion share a row. Scene, library controls and inspector are part of the same scrollable working paper.
- 768–1099px: 24px shell gutter; 48px rail and 256px inspector; two thumbnail peers and stacked search/filter controls.
- 640–767px: rail remains; inspector moves below the tray in the scene column, previews grow, and controls share rows when they fit.
- 360–639px: 20px shell gutter, wrapped masthead and route navigation, hidden tool rail, stacked canvas/tray/inspector, full-width save controls, two thumbnail peers and stacked filters. Panels use 20px insets; dialogs use viewport minus 40px, 24px padding and reachable internal vertical scrolling. Full working-paper height uses ordinary vertical scrolling, not clipped panels.

Native controls, long names and ES/EN labels wrap without horizontal page overflow. At narrow widths, choosing an item or starting a save reveals its inspector rather than requiring a hidden side panel. Primary audited checkpoints are 390/768/1280px, both themes.

## Rendered acceptance observations

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-01 | 1280px | normal | Scene sits above the library tray; selected-item preview/actions occupy the right inspector. |
| B-02 | 390px | normal | Scene, tray and inspector stack with two thumbnail columns and no horizontal page scroll. |
| B-03 | All audited | staff | Foreign owner and Solo lectura appear; Editar and Eliminar are absent. |
| B-04 | All audited | saving | Guardando appears with no Guardado confirmation. |
| B-05 | All audited | save-error | Form and retry remain visible. |
| B-06 | All audited | local scope | En este navegador remains a separate group with no import action. |
| B-07 | All audited | account-switch | No previous library thumbnails, detail inspector or project canvas is shown. |
| B-08 | All audited | reduced/still | Final content and all state words remain visible with no active entrance motion. |

## Verification and honest limits

Final offline build: exit 0, 637 KB, 2,135 bundled source files. No packages installed, assets fetched, server started, repository edits, canonical contract writes or preview directory. Output uses inline CSS/JS and embedded local fonts; the browser test saw zero external HTTP(S) requests and zero JavaScript page errors.

`contrast.py`: exit 0 — `contrast: 158 pairs checked in light and dark, all pass`.

Final `audit_mockup.py --widths 1280,390,768 --max-combos 240`: exit 0; **288 renders / 288 planned combinations**, 9,594 text measurements, 1,473 focus stops, no sampling.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

The first full audit found one 11px phone-thumbnail padding issue; it was fixed. The following full audit passed; after adding the deletion-focus fallback, the final HTML was rebuilt and the full audit passed again. The result above belongs to that final HTML. An initial interaction script used a too-short fixed delay before checking dialog removal; the final script waits for the actual state and passes without changing the dialog behavior to satisfy the test.

Single-direction `compare_directions.py` evidence validation: exit 0, `ok=true`, `evidence_ok=true`, no missing selectors. This checks this direction only; no pairwise claim about other designers’ directions is made.

Final focused Playwright walkthrough: `INTERACTIONS: PASS — 13 groups; page_errors=0; external_requests=0`. Covers search/occasion filter, thumbnail selection, placement, required-name validation, pending then confirmed save, metadata edit, deletion cancellation/confirmation and focus return, save retry, foreign read-only/copy, own-account saving from staff context, account clearing, local separation and English copy. Motion probe at 120ms: 3 active animations in expressive mode, 0 with OS reduce, 0 with `?still=1`. Screenshots were inspected in memory: 1280px light library, 390px dark library, 1280px dark staff view and 390px light save-piece view. No screenshot files were written. An additional 360px English-copy reflow probe passed in light and dark.

State transitions, source lists, server acknowledgements and SVG geometry are clearly labelled mock data. This HTML does not implement or prove server persistence, reload/second-browser equivalence, ownership authorization, real account-switch isolation, backend mutation failures, atomic saved status, thumbnail generation, WebGL scene fidelity or account deletion guards. Those remain implementation/integration concerns. No production test, type/lint or build suite was run because no production repository was changed.

## Open questions, assumptions and impact

Q: ¿Editar una decoración debe actualizar también su composición, además del nombre y la ocasión? Esta exploración muestra solo la edición de metadatos; el propietario y el Planner deben definir la actualización del contenido antes de cerrar el contrato.

Confirmed: no import of browser-local entries; foreign staff access is read-only and placement copies to the staff member's own scene; only the owner mutates/deletes server items; Master Designer and staff have the library through Taller; saved status waits for server confirmation. Do not reopen these owner decisions.

Assumptions: sample occasions are General and Cumpleaños from the existing controls; the neutral examples are illustrations, not actual customer content. Existing scene insertion/copy behavior is preserved and global/admin catalogue management stays separate. The account-deletion restriction belongs to the accounts surface and is not an extra screen here. Existing tools and sibling destinations keep their prior contracts.

Impact: SP-5 only; candidate input for T5.1, UI implementation T5.3 and visual review T5.5 after owner selection/finalization. Compatibility is undetermined until a direction is chosen; this unapproved exploration cannot authorize implementation or supersede any approved artifact.
