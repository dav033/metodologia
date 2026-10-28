---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
author: Designer
date: 2026-10-28
direction: c
name: Edición en contexto
source_revision: r11
source_behavior: proyectos@v1.r11.behavior.md
---

# Edición en contexto — proyectos@v1 · r11 · C

## 1. Identity and traceability

**Exploration only; draft, not approved and not an implementation contract.** This direction-specific note accompanies the TSX, self-contained HTML, two candidate compositions and axis JSON. It does not replace or modify canonical `proyectos@v1.md` / `.html`, either sibling contract, SPEC or PLAN. The owner selects a direction; a separate finalizer writes the canonical pair after selection.

Behavioral scope: `proyectos@v1.r11.behavior.md`, R6/R7 and SPEC “Behavior — SP-3 and SP-4 (round 9 answered)”. Consumers, if this direction is selected and independently approved: SP-4 T4.1 copies the approved artifact, T4.4 implements list/save/conflict/read-only/new-scene views, T4.5 implements import, T4.8 reviews rendered fidelity. No other subplan acquires a UI dependency merely by consuming project identity. Compatibility with the old unapproved mockup: **breaking visual composition**, because list disclosure, hierarchy and in-place editing need implementation and review; product persistence/ownership rules are unchanged. Compatibility with an approved production implementation is undetermined; none is claimed.

Sources inspected read-only in t12 and asesor: `src/app/globals.css`, `layout.tsx`, `/3d/page.tsx`, `Taller3D.tsx`, local scene-saving logic and shell navigation. Existing local save uses one browser scene and a 500ms debounce; it is not account persistence. The sibling canonical cuentas-admin and planes Markdown/HTML and their selected TSX establish the shared account masthead, language control, account disclosure, neutral horizontal navigation, Geist and generous radius vocabulary. Older requests for independent palettes/typefaces yield to this delegation's explicit fixed-product-system scope.

Only revision-specific files are written. Production repositories are not edited. No package installation, network fetch, server, commit, plan edit or approval occurs.

## 2. Purpose and users

The list answers “Which saved scene do I want to continue?” The editing header answers “What is this project called, and are these changes saved to my account?” The scene stays in context while the person edits its name, reviews the save boundary, or resolves a failure.

Owners save, search, reopen and continue their projects. Authorized employees/administrators search across permitted owners and read foreign originals. Copying requires Taller permission and creates an owned project; it never edits or transfers the original. Read-only access without Taller permission has its own accessible presentation and no copy/edit controls. A person signing into a shared browser gives explicit consent before legacy import.

## 3. Information architecture and approach

Retain the Pictures/Sempertex masthead, language/account controls and neutral horizontal route rule from the siblings. Proyectos introduces two route destinations, Taller 3D and Proyectos, because the saved-project brief requires them; this is not a new global navigation model. The Taller retains the scene toolbar, panel rail, scene/IA inspector vocabulary, undo/redo, photo and shopping-list controls as contextual existing UI.

**Change specific to this direction:** projects are full-width collapsible bands, not a permanent table, a card grid or a master/detail sidebar. Opening “Ver escena” reveals the scene inside that project's band. Name/owner/open action stay on its original line. At most one preview is open. “Qué se guarda” reveals the local-versus-account explanation at its point of use. In the Taller, the editable name itself becomes the labelled field; Enter/check confirms and Escape cancels. New controls use press/settle feedback rather than a new visual identity.

Two HTML thumbnails were drawn first:

- **Candidate 1, chosen:** full-width project band with in-place preview and adjacent save-boundary disclosure. It preserves project identity and action alignment while progressive disclosure changes the density.
- Candidate 2: two-column scene-first sheets. It is a valid composition inside the system but repeats large previews and loses the first candidate's direct relationship between the closed row and its open state.

The full mockup develops candidate 1. Both thumbnails remain illustrative compositions; neither is the complete interactive artifact. The main HTML is built from real installed components, not the stand-in HTML fallback.

## 4. Fixed design system and eight axes

Project tokens are mapped onto the real kit's semantic roles; there is no new palette or font family.

| Project source | Kit responsibility | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--superficie-suave` | subtle local group | #faf8fd / #1c1e26 |
| `--superficie-2` | secondary, muted, accent | #efe9f8 / #242733 |
| `--texto` | foregrounds | #1c1425 / #f4f5f7 |
| `--texto-suave` | supporting copy | #6b6178 / #9aa1ad |
| `--texto-tenue` | accessible control edge, inherited sibling alias | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primary / text on primary | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | primary hover role | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | decorative outline / divider | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--exito`, `--exito-suave` | success roles | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | warning roles | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | error roles | #b23a45, #ffeaec / #ff979f, #43252a |
| `--taller-visor`, `--taller-panel`, `--taller-encima` | existing workshop scene context | #ebe7f1, #faf9fc, #f3eefb / #1a1722, #16131d, #231e2e |

Geist Sans and Geist Mono are embedded from the existing local Next WOFF2 assets. Mono remains limited to inherited metadata/wordmark treatment. Panel/field/pill radii 32/18/999px and 24px inset match the siblings. Desktop band padding is 28px; phone padding is 20px; modal padding is 28px desktop and 24px phone. Colour identifies primary action and real save/error states. It does not recolour route navigation.

| Axis | Observable direction |
|---|---|
| concept | Edición en contexto: abrir una escena dentro de su propia fila, renombrar en la cabecera y desplegar únicamente la explicación o recuperación necesaria. |
| layout | Una pila de bandas horizontales a todo el ancho. La banda abierta contiene escena y explicación en proporción 1.8:1; no existe un panel maestro-detalle lateral ni una cuadrícula permanente de tarjetas. |
| navigation | Cabecera y navegación horizontal compartidas; Ver escena/Ocultar escena expande el proyecto en su propio lugar, Abrir lleva al Taller o a solo lectura. Qué se guarda despliega la explicación junto al estado. |
| typography | Geist Sans del producto: título 24px, proyecto 20px, sección 16–18px, cuerpo 14–15px, metadatos 12–13px. Geist Mono solo en la identificación Sempertex heredada. |
| density | Proyectos cerrados de una fila y una única escena abierta. La información secundaria se revela a demanda; 28px de margen interior en escritorio y 20px en teléfono. |
| components | Button/Input/Skeleton/Dialog reales de shadcn y Base UI/Animate UI. Composición propia de bandas expandibles y renombrado in situ; botones con presión táctil, selector de propietario nativo y disclosure de cuenta heredado. |
| colour | Exactamente Pictures: fondo/superficie/texto/acento y tokens Taller para el visor; roles accesibles de borde de control heredados de cuentas-admin y planes. No hay nueva paleta ni familia tipográfica. |
| motion | Asentamiento táctil: bandas se comprimen .985 y asientan con 55ms de secuencia; escena .965→1.008→1; estado rota -14°→5°→0; avisos se asientan verticalmente; presión .965 con spring 220/16; hover de iconos y nombre editable. Expresivo 520/170ms, natural 320/140ms, sutil 160/100ms; reducción sin desplazamiento. |

Actual components, with import evidence:

| Component name | Source and use |
|---|---|
| `shadcn:button default default/hover/focus/pressed/disabled/loading` | `@/components/ui/button`; account save, import and owned copy |
| `shadcn:button outline default/hover/focus/pressed/disabled` | Same import; preview, navigation, retry and cancellation |
| `shadcn:input text empty/filled/focus/invalid/disabled` | `@/components/ui/input`; search, inline name and named save |
| `shadcn:skeleton record loading` | `@/components/ui/skeleton`; list skeleton bands |
| `shadcn:dialog project open/closed/validating/busy` | `@/components/ui/dialog`; actual installed Animate UI/Base UI dialog with focus containment |
| `custom:project-band collapsed/expanded` | Semantic article and button with aria-expanded/aria-controls; no invented library attribution |
| `custom:account-disclosure closed/open/focus` | Shared native details/summary with Escape/outside dismissal |
| `custom:owner-filter native all/mine/other` | Labelled native select; staff-only |
| `custom:scene-preview illustrative` | Inline SVG depicting a neutral mock scene, not a WebGL renderer or stored thumbnail contract |
| `custom:motion profile/reduced` | `@kit/motion` profile; `motion.button` from `motion/react`, spring from useMotionProfile |
| `custom:planning-controls` | `mountMockup/useMockup` from `@kit/mockup`; native view/state/scene/theme/motion selectors |

## 5. Navigation, interaction and motion

The list opens own projects in Taller and foreign projects in read-only view. The real destinations are `/proyectos`, `/3d?proyecto=<id>` and `/proyectos/[id]` as specified by the plan. The HTML simulates navigation locally, with no network request. View changes focus H1; disclosures keep focus on the invoking control. Preview buttons expose expanded state and a target id. First save and copy require a trimmed non-empty name. Dialog Escape/cancel return to the exact surviving invoking control; there is a name/button/H1 fallback after the source view is replaced. Closed details explicitly hide their bodies, preserving disclosure visibility and measurement.

Motion grammar is tactile, finite and legible throughout. Expressive uses 520ms settle / 170ms controls / 55ms band offsets with cubic-bezier(.34,1.4,.64,1). Natural is 320/140/30ms and subtle 160/100/12ms. Distinct behaviors present in the artifact:

1. Band load/view choreography compresses .985, lifts briefly and settles; each subsequent band offsets 55ms.
2. The expanded scene seats from .965 through 1.008 to 1 without hiding its text.
3. Notices settle with a short vertical compression, independently of the scene.
4. Save status icons rotate -14° through 5° to zero and settle in scale.
5. Inline edit fields seat from scaleX(.96) through 1.01 to 1, anchored at the text edge.
6. Button hover raises its icon; press compresses to .965. The name control uses the installed Motion spring, stiffness 220/damping 16 for expressive.
7. Pending save/import has a rotating icon only while pending; keyboard feedback remains a static high-contrast outline.

Reduced OS preference, Quieto and `?still=1` remove travel, animated transitions and spinning while retaining every state, control and status word. Hidden-tab CSS animations are paused in the product; there is no persistent decorative ambient effect. Entrance motion uses transforms without layout changes, opacity reduction or mid-animation colour changes.

## 6. Flows and behavioral invariants

1. **First save:** new scene → “Sin guardar todavía” → Guardar proyecto → name dialog → validation or Guardando… → only a confirmed current revision says Guardado en tu cuenta. Subsequent edits autosave; Guardar ahora remains available outside pending/conflict states. Production responses acknowledge only their submitted generation and identity.
2. **New project:** Escena nueva, template and Abrir en Escena share the same transition. A saved project finishes pending save first; an unsaved scene asks before discard. Failure/conflict keeps the scene and blocks replacement. The new scene is called Escena nueva, has no saved identity and does not upload until its first named save. No new delete or history interface is added.
3. **Reopen:** search the full authorized collection, use owner filter only when permitted, preserve visible rows on next-page failure, and reopen the complete scene. Filter changes reset pagination; late responses must not replace the current query. These are production requirements, not claims about the mock fixture's synchronous search.
4. **Conflict:** a stale write stops autosave, retains the local scene and exposes Cargar versión del servidor / Guardar una copia. Loading the server version confirms which scene will be displayed and leaves the local recovery draft available. Saving an owned copy requests its name and never updates the foreign/original document.
5. **Offline/failure:** show Sin guardar with the reason and retry; a retry shows Guardando… until acknowledgement. A local backup failure asks the person to keep the view open and retry backup. Auth loss shows no project metadata and directs recovery through the same account.
6. **Foreign original:** read-only scene/owner banner; no editable name, scene tools or save-original action. With Taller permission, Guardar una copia opens an explicit owned-copy dialog; without it, the copy action is absent.
7. **Legacy import:** first authenticated Taller entry offers review for the current account, warns about shared devices and explains the scene-only boundary. Import is explicit, retry-safe and creates exactly one owned project after response loss/retry. Ahora no preserves the original and the list offers a way back to import. Invalid/unknown data has explanation plus raw-original download. Success/refusal/failure never changes or erases the browser source. Another account receives a fresh consent prompt, never a prior receipt or draft.

Only the name and complete scene travel between browsers. AI conversation/generated images remain local. No merge, delete, transfer, public sharing or version-history UI is introduced. These invariants remain binding when the finalizer/implementer adopts a direction.

## 7. View and dialog specifications

| Inspector view | Surface and hierarchy | Main action / progressive detail |
|---|---|---|
| `projects` | Own project search, import recovery entry and stack of project bands | Escena nueva; per-row Abrir; Ver/Ocultar escena; Qué se guarda |
| `staff` | Same shared surface plus labelled owner filter | Open authorized owned or foreign scene; clear distinction of owner/read-only |
| `workshop` | Existing Taller context, scene name, account save status, contextual failure panel | In-place name, explicit first save/Guardar ahora, local save explanation and failure recovery |
| `readonly` | Foreign owner/read-only banner and complete scene context | Owned copy only with Taller permission; return to permitted list |

The scene preview is a neutral illustrative SVG, labelled “Vista de escena · Mockup”. No new server thumbnail field, screenshot-generation job or additional persisted project content is proposed.

| Inspector dialog (`scene`) | Contents and outcomes |
|---|---|
| empty | No dialog |
| `first-save` | Named-save field, validation, scene-only explanation, save/cancel |
| `copy` | Owned-copy name, original-retention explanation, save/cancel |
| `new-scene` | Save before replacement; explicit unsaved discard or cancel; blocked save has visible reason |
| `leave` | Preserve pending work before project-list navigation; save continues to the original requested destination |
| `server-version` | Explicit server load and local-draft-retention explanation; cancel |
| `import` | Current-account destination, explicit import/refusal, shared-device warning; invalid/error recovery and original download |

## 8. Reachable states

The native Estado switch exposes every state below. States apply to the named surface; unrelated combinations retain the normal surface rather than inventing new business behavior. The Diálogo switch independently reaches every dialog on any view. The native controls are outside the product shell and retain the Mockup label.

| State id | Relevant view | Visible outcome / recovery |
|---|---|---|
| `normal` | All | Authorized results or confirmed account-save text |
| `loading` | List | Skeleton bands and polite loading status |
| `empty` | List | No saved projects; existing Escena nueva action and brief next step |
| `no-results` | List | Explicit no-match feedback and clear search action |
| `next-page` | List | More fixture rows, end-of-list disabled control |
| `next-page-error` | List | Already loaded rows remain; failed next-page reason and retry |
| `unsaved` | Taller | Escena nueva / Sin guardar todavía; first named save required |
| `saving` | Taller | Guardando… with pending control state; no claim of confirmed persistence |
| `offline` | List/Taller | Query failure or unsaved scene; explicit retry, scene remains |
| `error` | List/Taller | Load/save failure, recoverable explanation and retry |
| `conflict` | Taller | Autosave stopped; local scene retained; server-load/copy panel |
| `no-taller` | Read-only | Foreign scene readable, no editing or copy action |
| `import-offer` | List/Taller | Legacy scene review entry with current-account explanation |
| `import-invalid` | List/Taller/import dialog | Incompatible data explanation, raw mock download, no import submit |
| `importing` | Import context/dialog | Importing status/disabled duplicate submit |
| `imported` | List/Taller | One-project acknowledgement and original-retention message |
| `import-error` | List/Taller/import dialog | Retry-safe failed confirmation plus original download |
| `recovery` | Taller | Account-local recovery draft available |
| `local-error` | Taller | Backup failure; stay in view and retry backup |
| `permission-denied` | All | Access refusal without project names/owners/scene metadata |
| `unavailable` | All | Non-disclosing unavailable-project surface |
| `session-expired` | All | Same-account sign-in/recovery guidance and no scene data |

Controls additionally expose normal/hover/focus/press, validation and disabled/busy behavior. No checkbox is needed for import: the distinct explicit Importar a mi cuenta and Ahora no actions give consent/refusal without a redundant consent checkbox.

## 9. Responsive behavior

- **360–639px:** 20px outer gutter; masthead/language/account controls wrap; heading/action stack; search/filter become full-width; preview moves below the row controls and explanation below the scene; Taller scene-name/status/save controls wrap, existing panel rail/inspector collapse to the phone tool context; dialogs use viewport-minus-40px width and 24px padding. Actions remain at least 44px high. Vertical scrolling is intentional; no horizontal page scroll is allowed.
- **640–1099px:** 24px outer gutter; filters wrap above the list; expanded band keeps a scene plus explanation when space permits; Taller inspector collapses, preserving the main scene and rail. Native account/header controls wrap without changing navigation semantics.
- **1100px and above:** 40px outer gutter, 1520px maximum shared shell; full-width project bands; 1.8:1 scene/explanation; existing scene/rail/inspector context visible.

Visual checks include 390, 768 and 1280px. Additional rendered probes at 360 and 1024px verify list reflow in both themes. English expansion is supported in the mockup's shared language selector; fixture project names remain data, not translated identities.

## 10. Accessibility targets and verification boundaries

Target applicable WCAG 2.2 AA, not a certification. Semantic headings/articles/navigation, programmatic names and state/error announcements are present; keyboard Enter/Space invoke buttons and disclosures. Named-save inputs have associated labels and aria-invalid/described error. Dialogs use the installed modal's inert background/focus containment. Escape returns to the invoking control. Focus uses a 3px product accent outline offset 4px. Control boundaries use the sibling's accessible texto-tenue alias rather than the decorative divider token. Text targets 4.5:1 and control edges/focus 3:1 in both themes. Reduced motion preserves information and actions.

This is a planning fixture: save/import timing, matching/owner-filtering and transitions are in-memory simulation. The downloaded JSON is explicitly `escena-original.mock.json`; it demonstrates recovery UI, not user-data recovery. No storage/API, atomic revision check, idempotency, cross-browser scene fidelity, full-collection server search, authentication or real account-switch isolation is implemented or verified here. Existing photo/shopping/tool controls show a Mockup scope notice; they are retained context, not redesigned or implemented. Real behavior belongs to the plan's implementation/integration tasks.

## 11. Observable acceptance and honest evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-AC-01 | 360–1280px | All | The Pictures/Sempertex masthead, Geist type and shared account/navigation vocabulary remain recognizable; no new palette appears. |
| C-AC-02 | 1100px+ | List normal | An expanded scene is inside its project's full-width band, with identity/actions above and save explanation beside it. |
| C-AC-03 | 360–639px | List normal | Scene and explanation stack within the same band without horizontal overflow. |
| C-AC-04 | All | List expanded/collapsed | Ver/Ocultar escena changes only the selected band and exposes aria-expanded; another band can replace the open preview. |
| C-AC-05 | All | Loading/empty/no-results | Each named list state has distinct visible feedback and an actionable next step; loading uses skeleton bands. |
| C-AC-06 | All | Next-page failure | Previously loaded rows stay visible while the next-page failure and Reintentar action appear below them. |
| C-AC-07 | All | Staff list | Only the staff view exposes the owner filter; foreign entries carry owner and Solo lectura copy. |
| C-AC-08 | All | Taller inline rename | The scene-name control becomes a labelled input in its current header position; confirm/Escape keep the context. |
| C-AC-09 | All | First save invalid | Empty names show the associated field error and keep the dialog open. |
| C-AC-10 | All | Saving/saved | Guardando… remains visible until acknowledgement; saved text is not shown for pending work. |
| C-AC-11 | All | New scene | All three creation entry points yield Escena nueva with Sin guardar todavía after protecting prior edits. |
| C-AC-12 | All | Conflict | The failure panel shows both server-load and owned-copy actions; normal save is stopped. |
| C-AC-13 | All | Offline | Sin guardar and the offline reason remain beside the project context, with an explicit retry. |
| C-AC-14 | All | Foreign original | No editable name or scene tool is present; copy is absent without Taller permission. |
| C-AC-15 | All | Import offer | The current-account destination and shared-device warning precede distinct import/refusal actions. |
| C-AC-16 | All | Invalid import | Explanation and original download remain available, while import submit is absent. |
| C-AC-17 | 390px | Dialogs | Modal content fits within its viewport frame, with readable padding and reachable actions in both themes. |
| C-AC-18 | All | Keyboard/reduced | Focus is visible, modal Escape restores invocation focus and reduced/still modes retain every action without travel. |

Build: real offline builder, 647KB self-contained HTML, 2126 source files bundled. No fallback or downloaded assets. `contrast.py`: **158 pairs checked in light and dark, all pass**. The first rendered audit found two band-padding findings caused by measurable closed-disclosure content; explicit hidden bodies fixed them. A complete subsequent audit measured 672 renders, 17,388 text measurements and 1,965 focus stops with a PASS. A focused interaction test found the invoking import button was being recreated; lifting the feedback component out of the render and retaining disclosure identity fixed the return target. The final source is re-audited after these fixes; final RESULT and counts are recorded below when complete.

The complete scripted mockup walkthrough passed 12 checks with zero page errors: first-save validation/acknowledgement, inline rename, offline retry, conflict copy, new/template guard, save-and-continue destination, focused search, authorized-owner/read-only/copy visibility, invalid import/download/Escape/focus, import refusal and English view. Initial walkthrough attempts had two locator/assertion mistakes (two Plantillas controls and two legitimate Escena matches), corrected without changing the UI's behavior. Additional 360/390/768/1024/1280px list probes found no contrast, control-edge, padding, alignment or overflow issues in either theme. Screenshots were inspected in memory for both candidates, desktop list/Taller, phone list/conflict/first-save/import and tablet list; no additional screenshot files were written.

`compare_directions.py` measured A/B/C: overall `ok=true`, selector evidence passes, no missing evidence. A–C layout similarity **0.114**, B–C **0.156**; both pairs have different motion; B–C also has different density. Shared route navigation intentionally remains the same. These measurements are visual distinction evidence, not proof of production behavior or owner approval.

Final snapshot audit: running; no final snapshot result claimed yet.

## 12. Open question and assumptions

Q: David, ¿debe abrirse la vista previa del primer proyecto al entrar en Proyectos, como en esta exploración, o deben comenzar todas las escenas contraídas?

Provisional assumption pending direction selection: the first authorized fixture opens for comparison; only one preview is expanded at a time. This affects initial presentation, not ownership, first-save/import consent or persistence semantics. The scope's account/save/conflict/import/new-scene decisions are already settled and are not reopened here.

The owner has not selected or approved this direction. The canonical artifacts and plan remain untouched. Production behavior, independent visual review and any later canonical finalization remain with their assigned plan tasks.

### Input/artifact identity

| File | SHA-256 |
|---|---|
| `SPEC.md` | `032cbfb717c61ff8edc32160716a92fb925e8d41e1e31c8f62176f8da9decd7d` |
| `PLAN.json` | `4807c95679b4a0802ec51f16e30a7726d7baf989c5eb308c04dc9f2b6b84edd7` |
| `design/proyectos@v1.r11.behavior.md` | `1d89ee0c436645cf1af3f8ac62d888d9ad089801f688870a48344d862c1c2b65` |
| `design/proyectos@v1.r11.dir-c.tsx` | `f081bd227ac4e420001cc7f3772a2d88a87e9a8f9c19a68f47e61022241a63f9` |
| `design/proyectos@v1.r11.dir-c.html` | `67054c904ffab4e227045695ee9737f2440ec3462d1499d17d8dc2a6d8b8c9a3` |
