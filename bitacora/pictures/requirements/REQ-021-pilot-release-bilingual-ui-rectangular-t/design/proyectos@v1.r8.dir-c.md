---
name: Archivo de muestrarios
status: draft
kind: direction-exploration
contract_ref: proyectos@v1
subplan: SP-4
requirements: [R6, R7]
revision: r8.dir-c
owner: David
chosen_thumbnail: proyectos@v1.r8.dir-c.html.candidate-1.html
---

# Archivo de muestrarios — direction C

Independent tactile/playful exploration, **unapproved**. This note is not the canonical twelve-section contract and is not an implementation input. The owner chooses the direction before a separate finalizer writes the shared contract. The scoped exploration brief supersedes the canonical output pair: only this direction's six files and the required delegation RESULT are written. No production source, SPEC, PLAN, shared contract, history, other direction, project memory or approval state is changed.

## Concept, memorable move and choice

A decorator returns to a complete arrangement as they return to a sample in a studio archive. Projects become **filed material samples**: a projecting date tab, a small scene illustration, the montage's name, its owner and a direct opening action. The main screen answers “Which montage am I continuing?” without a dashboard, decorative statistics or a carousel. Saving opens the same sample as a folio with a binding note; conflict choices unfold above it, where they cannot be confused with a successful save.

The memorable move is **a folder sliding into its place while its date tab rises, followed by a compressed save stamp**. Folders settle with a small overshoot instead of disappearing into fade-up sequences. In the open folio the balloon arch can be moved directly; two text-labelled buttons provide the same voluntary change. The installed spring settles that manipulation. Reduced motion immediately shows the same geometry, status and actions.

Two thumbnail compositions were written before the TSX:

- **Candidate 1, selected:** [Archivo de muestrarios](proyectos@v1.r8.dir-c.html.candidate-1.html). Full-width folder rows keep the whole name, ownership and opening action together. Each project is directly available without advancing a deck.
- [Candidate 2, retained](proyectos@v1.r8.dir-c.html.candidate-2.html): Caja de muestras. A large recent sample and smaller samples below create a stronger featured-project hierarchy, but make the collection less evenly scannable. It was not developed further.

The thumbnails are small inline visual sketches with both themes and responsive CSS, not substitute library components. The full HTML uses the real installed toolchain. Neither thumbnail is approved.

### Why this is not the default

The folder silhouette has a purpose: its tab exposes time, its sample shows the product's material world and its body groups the project with its account. There is no generic dashboard grid, metric tile or ornamental trend. The collection reads vertically; opening a project reveals a bound folio rather than an inspector-led editor clone. Neutral text navigation surrounds the one mauve primary action. Playfulness lives in the physical silhouette and response to touch, while input controls remain familiar.

### Look ledger

Read sibling notes `cuentas-admin@v1.r7.dir-a/b/c.md` and `taller-esenciales@v1.r6.dir-a/b/c.md`. Accounts explores an editorial register, a two-leaf access pass/bottom dock and perforated permission passes. Taller explores a work sheet, an axonometric measured stage and a cutting bench with tools along its joint. This direction uses none of those compositions, no permission slots, bottom dock, ruler or cutting grid. Its signature is the **vertical sample archive, projecting date tabs and bound save folio**. Shared ring/dot mark, Pictures tokens, direct Spanish language, familiar controls and balloon/Backing subject matter intentionally connect the subplans. A stage-like scene illustration is shared product data, not a repeated navigation or layout skeleton.

## Eight axes

| Axis | Observable expression | Rendered evidence |
|---|---|---|
| Concept | Filed material samples for saved montages; ownership remains next to the scene and name. | `.project-file`, `.file-tab`, `.file-info` |
| Layout / composition | A vertical stack of horizontal folders: 200 px sample, flexible name, trailing action. The open folio has a wide scene and a 300 px binding note. Phone moves the folder action below sample/name and stacks the binding note. | `.file-stack`, `.project-file`, `.file-action`, `.folio-body` |
| Navigation | Quiet top workspace tools, direct “Abrir proyecto” on each folder, project-name search, staff-only owner filter, explicit back action. Every fixture also has the required native planning selectors. | `.global-nav`, `.archive-tools`, `.project-file .press` |
| Typography | Offline Arial/Helvetica body; title 32/28 px, folder name 20/17 px, body 14–15 px; monospaced 12 px dates and counts. Long project names wrap. | `.page-heading h1`, `.file-info h2`, `.file-tab` |
| Density / shape | 24 px folder/panel padding, 20 px on phones; 40 px between folders to expose tabs; 44 px minimum actions and 46 px fields; 18/14 px folio corners and dashed bindings. | `.project-file`, `.folio-band`, `.binding-note`, `.input`, `.press` |
| Components | Real shadcn/Base UI buttons, inputs, skeletons; real Animate UI Dialog and AlertDialog. Custom folder, SVG scene sample, save stamp, conflict fold and binding note. No checkbox is needed: import consent is the explicit named action. | `[data-slot=button]`, `[data-slot=input]`, `.mini-scene`, `.conflict-fold` |
| Colour | Existing Pictures backgrounds, surfaces and text; mauve action and lavender materials. Neutral navigation. Warning/error/success have written explanations as well as colour. Strong control edges are separate from subtle dividers. | `.sample`, `.press[data-variant=default]`, `.notice`, `.global-nav` |
| Motion | Expressive folder insertion, rising tabs, hinged folio and compressed stamp; press response; voluntary spring drag with button parity. 520 ms expressive entrance, 45 ms folder stagger, 200 ms repeated-control feedback; natural 320/140 ms and subtle 200/90 ms. | `.project-file`, `.file-tab`, `.press`, `.stamp-ink`, `.scene-piece` |

The sibling JSON contains exactly the eight axes and selector evidence. Every selector was checked against rendered elements. Chromium reported active `folio-open`, `folder-seat` and `tab-seat` animations with 520 ms duration. `useMotionProfile()` supplies the drag spring (expressive stiffness 220, damping 16, mass .9); the CSS uses the profile duration/easing tokens. The entrance overshoot uses cubic-bezier(.34,1.4,.64,1), never makes text transparent and does not animate layout dimensions. Hidden tabs pause CSS timelines; the scene has no autonomous or offscreen loop. OS reduced motion, Quieto and `?still=1` settle the scene without changing available actions. Voluntary drag remains voluntary; no action requires drag.

## Existing system and actual libraries

Read-only inspection covered both repositories' `AGENTS.md`, `src/app/globals.css`, `src/app/layout.tsx`, local scene saving and its `Taller3D.tsx` consumers. Both use Pictures semantic aliases; both layouts load Geist through Next. This artifact deliberately uses installed local sans/monospace fallbacks and does not fetch font files. Production should retain its existing loaded Geist, with the same role sizes; exact font metrics need the implementation's visual review.

| Existing project token | Kit role / use | Light / dark in this exploration |
|---|---|---|
| `--fondo` | `--background` | `#faf9fc` / `#0b0c10` |
| `--superficie` | `--card`, `--popover` | `#ffffff` / `#16181f` |
| `--texto` | foreground roles | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | `--muted-foreground` | `#6b6178` / proposed lighter metadata `#adb3c0` |
| `--superficie-2` | `--muted`, `--secondary` | `#efe9f8` / `#242733` |
| `--acento`, dark `--taller-acento` | `--primary`, `--ring` | `#6d3fe0` / `#b9a4ff` |
| `--sobre-acento` | `--primary-foreground` | `#ffffff` / `#120b24` |
| `--borde` | subtle divider `--border` | `#e3daef` / `#383c48` |
| `--texto-suave`, `--taller-medio` | strong control edge `--input` | `#6b6178` / `#a59db5` |
| `--taller-visor` | scene-ground adaptation | `#ebe7f1` / proposed neutral `#24212d` |
| `--ease-rebote` | expressive settling grammar | cubic-bezier(.34,1.4,.64,1) |

The lighter dark metadata and scene-ground adaptation are local visual proposals, not edits to shared tokens. No extra persisted scene data or new project API is proposed.

Actual sources: `shadcn:button default/outline/ghost`, import `@/components/ui/button`; `shadcn:input default/invalid`, import `@/components/ui/input`; `shadcn:skeleton loading`, import `@/components/ui/skeleton`; `shadcn:dialog default` with installed Animate UI primitive, import `@/components/ui/dialog`; `shadcn:alert-dialog confirmation` with installed Animate UI primitive, import `@/components/ui/alert-dialog`. Motion comes from `motion/react` and `@kit/motion`; planning shell from `@kit/mockup`. Actual component exports were inspected. **No fallback HTML kit, installation or network asset was used.**

## Behaviour, views and simulation boundaries

Sources: current `SPEC.md`, `PLAN.md`, `PLAN.json` revision 1, and the shared `proyectos@v1.r8.behavior.md`. The current source assigns R6/R7 to SP-4 and confirms round 9 saving, ownership, full-scene and import decisions. The behavioural source is preserved; this exploration creates no new approvals.

| Native Vista value | Fixture and job |
|---|---|
| `propios` | Ana's own project list; name search, empty search, incremental loading, retry and return to legacy import. Own projects open the save folio. |
| `todos` | Ana as authorized internal employee; all authorized project fixtures, owner selector and names. Foreign projects open the read-only consultation. The selector represents the staff entry point; it is not a permission granted by this artifact. |
| `taller` | First named save, pending/saving/saved status, Save now, offline/error retry, stale acknowledgement, concurrency conflict and recovery. The diagram illustrates the surrounding saved-project UI, not a new 3D engine. |
| `consulta` | Camila's original shown read-only; no move/edit tools. Save owned copy requires Taller access. `sin-taller` removes the Taller destination and disables the copy action with a written explanation. |
| `importar` | Explicit consent for Ana, shared-device warning, first named import, Not now, retry-safe completion and incompatible-data recovery. No automatic upload. |

The collection uses six small realistic mock records, never a fake production total. Search and filtering operate over that entire fixture before slicing it. Filter changes reset the slice. “Cargar más” adds rows; partial-page retry retains visible rows. **This does not verify server-wide search past 50 records, cursor binding or out-of-order network responses**; T4.3/T4.4/T4.6 own those actual requirements. No remote endpoints are called.

First save asks for a name and shows inline validation. Later simulated changes debounce for 500 ms, then show saving and completion; 500 ms is the Planner default, not an owner timing decision. Pending changes are not presented as confirmed. A conflict disables Save now and stops the ordinary save path while retaining the local illustration. “Guardar como copia” opens the named-save Dialog. “Cargar versión guardada” uses AlertDialog, then exposes “Recuperar borrador local” for the same-account fixture. Leaving with pending changes offers save-and-leave, keep draft-and-leave, or cancel; saving is unavailable offline or during a conflict. Scene/account persistence, idempotent receipts and real queue semantics remain implementation responsibilities.

Import error/offline notices use flat ruled strips within the folio; on phones notice icons sit above full-width copy. The import illustration is explicitly a sample; it does not parse or access the user's storage. Incompatible data exposes a labelled **example JSON** download rather than pretending to export a real legacy scene. The production download must contain the original raw bytes. The original must remain unchanged after refusal, validation failure or success. Names and complete scenes are portable; AI conversations and generated images remain browser-local. No deletion, transfer, version-history UI, hidden overwrite or automatic account reassignment is added.

The runtime's fixtures intentionally remount on view/state changes. Theme/motion preserve the mounted UI. Page-local variables demonstrate selection/copy and recovery; they are not account-isolated storage or an authenticated session. “Volver a entrar · simulación” resets a fixture and is not a real login flow.

### State and dialog coverage

Native selectors retain **Mockup**, `view`/Vista, `state`/Estado, `scene`/Diálogo, `theme`/Tema and `motion`/Movimiento. All sixteen declared state values are reachable. Views contextualize states; irrelevant combinations retain the normal fixture instead of inventing a new workflow.

| Estado values | Applicable fixture and visible recovery |
|---|---|
| `normal` | All views, populated fixture and ordinary enabled actions. |
| `cargando` | Lists and save folio: stable real Skeletons; `guardando` is the import's in-progress fixture. |
| `vacio` | Lists: create first project. Taller: unsaved scene, first Save opens name Dialog. |
| `error` | List retry; Taller retains pending work and offers save retry; import retry explains that an uncertain response must not duplicate a project. |
| `guardando`, `guardado`, `pendiente` | Save status and disabled duplicate action; import processing/completion as applicable. Pending and saving do not imply server acknowledgement. |
| `sin-conexion` | List warns stale data; Taller retains same-account local work, disables Save now and offers reconnection; import disabled with original preserved. |
| `conflicto` | Taller: persistent two-choice conflict fold, retained local scene and halted normal save. |
| `validacion` | Taller error notice plus native Nombre scene: empty name, field association and recoverable inline error. |
| `sin-permiso`, `sesion-caducada` | All views redact project content and explain return to own list or same-account sign-in; dialogs stay closed. |
| `parcial` | List retains rows and retries next page. Taller describes older acknowledgement with newer edits pending. |
| `incompatible`, `importado` | Import-only failure with raw-download example, or acknowledged success with original retained and Open project action. |
| `sin-taller` | Consultation has no edit tools and no enabled copy; import is denied; new-project action is disabled. |

Diálogo options: Ninguno, Nombre / guardar copia (`nombre`), Salir con cambios (`salir`), Cargar versión guardada (`servidor`). These use actual modal primitives with accessible titles/descriptions, inert background and focus containment. Escape closes the ordinary save Dialog and returns focus to its invoker; explicit Cancel is also available. AlertDialog is used for potentially replacing an open scene and for leaving pending work. Their fixtures are not account authorization checks.

## Reflow, accessibility and review targets

- **360–767 px:** 20 px shell/panel padding; stacked heading actions; 96 px sample beside wrapped folder name; opening action moves below and fills available width. Folio, import and conflict choices become a single column. Modal actions stack; modal width is bounded by 20 px side margins and its contents scroll vertically when necessary.
- **768–1023 px:** 24 px shell padding; 150 px folder sample; opening action sits under the folder's text; folio note is 260 px. No hidden owner-filter control or gesture-only action.
- **1024 px and above:** shell max-width 1160 px including 32 px side padding; 200 px folder sample, flexible title, trailing action; 300 px folio binding note. Header, content and footer share the same outer axis.
- **Targets:** WCAG 2.2 AA text 4.5:1, large text 3:1 and visible control/focus edges 3:1; 44 px actions; labelled inputs/selects, live save/retry information, explicit ownership and read-only copy, keyboard alternatives to drag, native selectors and reduced-motion parity. Real modal keyboard behavior was exercised. Automated evidence does not certify full WCAG conformance or screen-reader/production semantics.

| Direction criterion | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-01 | 1024+ | normal list | A date tab projects above each horizontal folder; name, owner and opening action belong to the same folder. |
| C-02 | 360–767 | normal list | The opening action sits below sample/name, with no horizontal page scrolling. |
| C-03 | 360+ | loading | The list shows stable skeleton rows rather than an isolated spinner. |
| C-04 | 360+ | empty/error | Explanation, recovery and support content stay on the page's left axis. |
| C-05 | 360+ | conflict | The conflict explanation and two labelled alternatives appear before the open folio; Save now is disabled. |
| C-06 | 360+ | foreign/sin-taller | The original's owner and read-only explanation are visible; move tools are absent and copy is disabled without Taller. |
| C-07 | 360+ | incompatible import | The original-preservation explanation and example-download action are visible; no enabled Import action is shown. |
| C-08 | 360+ | validation dialog | The name input exposes its inline error, keyboard focus remains in the modal and Cancel is reachable. |
| C-09 | 360+ | expressive/reduced | Folders and tabs animate in expressive mode; reduced/still mode shows the final content and retains all actions. |
| C-10 | 360+ | both themes | Input, outlined-action and focus edges remain visible on their actual surfaces. |

## Verification and honest limits

Tooling status: installed and built, **96/96 entries available**. Built with the absolute-path `components mockup build` command from this direction's TSX to this direction's HTML: **568 KB, 2135 bundled source files, offline**, exit 0. No package installation or fetched asset.

`contrast.py proyectos@v1.r8.dir-c.html`: **158 pairs checked in light and dark, all pass**, exit 0.

The first rendered audit found incorrect primary-button variants and alignment issues around centered empty states and a trailing account-scope line. Real variant attributes, coherent left-aligned empty-state content and an aligned scope line fixed the causes. A 12-example focused rendered probe subsequently found no contrast, non-text, alignment, padding or overflow findings. The next complete audit retained eight phone-alert alignment findings: its icon left the text in a narrow centered strip. Phone notices now stack icon above full-width text. Screenshot inspection also exposed a list-error fixture that reported hidden rows as visible; the count now correctly reads zero and no next-page action appears. One intermediate audit was intentionally interrupted before completion to include that correction; it is not a passing result. The final focused phone-error probe passed all five measured visual categories and the count/retry assertions. A further six alignment findings identified duplicate padding in import notices nested inside the folio. Those notices are now flat ruled strips aligned with the import form, rather than another framed card. A complete supplementary sweep of **320 view/state/theme/width examples found zero contrast, non-text, alignment, padding or overflow findings** before the final full keyboard audit.

Final exact-output audit: **380 renders / 380 planned combinations**, **8,788 text measurements**, **618 focus stops**, exit 0. Both themes and all view/state combinations plus each dialog were rendered at 1280/390 px.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Audited HTML SHA-256: `027271537e5df104e1268c5aab386875fa9885eef22125986ea1203f084e9a6b`.

Additional Playwright smoke: **PASS** for search, empty search, pagination, owner filtering, foreign read-only, no-Taller permission fixture, Dialog Escape/focus return, conflict confirmation/local-draft recovery, first-save name validation, simulated autosave, explicit import and incompatible-data recovery. No browser errors or HTTP(S) requests were observed. After the visual fixes, a responsive probe checked **30 combinations at 360/768/1024 px**, both themes, across list, partial staff list, conflict, no-Taller consultation and incompatible import: no horizontal page overflow. All axis selectors matched rendered elements; expressive keyframes were observed and `?still=1` reported zero running animations.

Rendered screenshots were inspected in memory at 1280/light, 390/dark, 1280/dark conflict and 390/light incompatible import, then the final phone error and name-validation Dialog. They are not additional output files. No production tests, server persistence, real permissions, cross-browser restoration, screen-reader testing, Blender/3D fidelity, API concurrency, source-raw import or more-than-50-row server search is attested by this design artifact.

## Impact, questions and next owner decision

SP-4 consumers remain `proyectos@v1`: T4.1 copies the later approved contract; T4.4 consumes list/save/consultation/conflict UI; T4.5 consumes import; T4.8 reviews rendering; T4.6/T4.7 verify actual browser integration and T4.9 audits isolation/concurrency. Behaviour remains tied to R6/R7. **Compatibility classification: undetermined until a direction is selected and finalized.** If selected, the folder composition, folio and all stated responsive/focus/motion expectations must enter the canonical contract and its visual review. No consumer is redirected by these files.

Q: Should the list show a scene-derived preview when an authorized source is available, or a neutral material sample until then? No persisted thumbnail field, extra scene upload or expensive per-row scene fetch is authorized by this exploration; the current sample illustrations are mock data. Decision owner: David with the Planner for the data boundary.

Confirmed decisions are not reopened: named first save, subsequent autosave, complete scene portability, foreign originals read-only, Taller permission for owned copies, conflict stop/preservation, account-scoped drafts and explicit lossless/idempotent import. Direction selection and canonical finalization remain pending owner review. This task grants no approval.
