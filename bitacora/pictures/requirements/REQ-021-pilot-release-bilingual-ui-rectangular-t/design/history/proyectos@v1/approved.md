---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
author: Designer (Codex)
date: 2026-10-29
direction: c
name: Edición en contexto
source_revision: r12
source_behavior: proyectos@v1.r12.behavior.md
plan_revision: 15
---

# proyectos@v1 — Edición en contexto

## 1. Identity and traceability

Canonical planning **draft; not approved for implementation**. The owner chose direction c, “Edición en contexto”, through the web comparison. Direction choice authorizes this finalization; it does not approve the contract, subplan or plan. This is version 1, with no approved predecessor being changed. The only design outputs of this task are `design/proyectos@v1.md` and `design/proyectos@v1.html`; the required delegation RESULT is administrative evidence. No exploration, history, SPEC, PLAN, production file, contract changelog or preview is changed.

Scope: REQ-021 / M2 / SP-4 “Saved projects”, R6/R7 and US-3, from current SPEC (status ready), PLAN.json revision 15, `proyectos@v1.r12.behavior.md` and the chosen r12 direction's Markdown, TSX and HTML. SPEC § “Behavior — SP-3 and SP-4 (round 9 answered)” settles explicit first save followed by autosave, scene/name persistence, foreign-original read-only access, lossless import, collection-wide search and new-unsaved-project transitions. This contract specifies their UI, not a new persistence or authorization API.

| Requirement | Contract coverage | Consuming tasks |
|---|---|---|
| R6 — save under account, reopen unchanged; staff/admin open authorized projects | V1–V4, F1–F6, save/list/conflict/recovery states and UI-AC-01–19, 24–29 | T4.4; visual review T4.8 |
| R7 — explicit browser-scene import without loss | V5, D6, F7, import states and UI-AC-20–23 | T4.5; visual review T4.8 |

Exact PLAN consumers: SP-4 `ui.contract=proyectos`, `ui.version=1`, `design_task=T4.1`, `visual_review_task=T4.8`; UI implementation tasks T4.4 (list, saving, new scene, conflict, read-only) and T4.5 (import). T4.1 copies the owner-approved artifact only after independent approval. T4.2/T4.3 and T4.31 own/check storage and authorization; T4.6/T4.7 verify the real cross-browser behavior; T4.9 audits spec and standards. SP-6/SP-12 consuming project identity does not make them consumers of this visual contract.

**Impact:** composition is breaking relative to the superseded, unapproved canonical draft: stacked expandable bands, contextual details and inline name editing require T4.4 adaptation and T4.8 rendered review. Import presentation affects T4.5/T4.8. Relative to selected r12 c the composition, navigation and motion are preserved; the current builder incorporates kit runtime updates. No source-level behavioral change was required. Compatibility with any approved production implementation is undetermined; none is claimed. Do not redirect plan references, publish into `design/contracts/`, approve, or implement this draft in this delegation.

Read-only product evidence: t12 `src/app/globals.css`, `layout.tsx`, `/3d/page.tsx`, `Taller3D.tsx` and `guardado-escena.ts`, plus the supplied UI brief and sibling `cuentas-admin@v1` / `planes@v1` contracts. Existing Taller already has an inline scene name, local save status, tools and a 500 ms browser-save debounce. Project storage/list/identity/import/conflicts are new. Existing browser save text is not proof of account persistence. The selected TSX is rebuilt unchanged using the installed offline builder, not copied from its older generated HTML.

## 2. Purpose and users

V1 answers “Which saved scene do I want to continue?” V3 answers “What is this project called, and are these changes saved to my account?” Editing the name, checking the save boundary and resolving a failure keep the scene visible in context. Success is reopening the complete saved scene under the same account in another browser, while clearly distinguishing pending local work from confirmed account data.

Owners list, search, save and continue their own projects. Employees/administrators with `proyectos.ver_todos` may filter authorized owners and open foreign originals read-only; `taller.usar` additionally permits an owned copy. A custom role with read-all but without Taller permission remains read-only and cannot copy. A person using a shared browser chooses explicitly whether its legacy scene should enter the currently signed-in account. Opening or previewing a foreign project never changes its owner.

Only the project name and complete scene travel between browsers, including room, environment, salon, materials and scene-node relationships. The AI conversation and generated images remain in their browser. Existing Taller tools, shell, navigation and identity remain outside the redesign. No delete, transfer, merge, public sharing or version-history interface is added.

## 3. Information architecture and hierarchy

Keep the Pictures/Sempertex masthead, language/account controls, title/action row and neutral horizontal route rule established by the sibling contracts. The route destinations are Taller 3D and Proyectos; this scope does not replace the application's global navigation. In V3 retain the Taller toolbar, panel rail, scene/IA inspector, undo/redo, realistic-photo and shopping-list vocabulary as existing context.

V1/V2 order: title and Escena nueva; route navigation; labelled project-name search and, only for authorized staff, owner filter; import review/recovery entry when applicable; authorized project bands; pagination status/retry/load-more. Do not infer an owner filter from a client-selected role: server authorization determines the available scope.

Projects are full-width collapsible bands. Name, owner/save/read-only metadata and Ver escena/Abrir remain in the band header. Ver escena reveals its scene and account-versus-browser explanation inside that same band; a second preview closes the first. At most one is open. Preserve the selected composition's first authorized project initially expanded; if there is no result, none is expanded. Changing search or owner closes the preview and resets pagination. A preview is a local presentation aid and does not mark a project open for editing.

In desktop expanded bands, scene and explanation form a 1.8:1 layout; on phone they stack. “Qué se guarda” reveals the detailed persistence boundary at the point of use. In V3, the scene name itself becomes the input in the same header location. The current save state is adjacent to the identity, with first-save/Save now controls, and contextual failures appear immediately above the scene. In V4 the owner/read-only banner precedes the scene and optional owned-copy action. Import consent is a dialog, reached from V5's notice or list entry.

The selected candidate is the in-place band composition from r12 c. Candidate alternatives are historical inputs, not additional screens or deliverables. The canonical HTML retains native Vista/Estado/Diálogo/Tema/Movimiento inspectors outside the product shell. Their labels, revision marker and Mockup data notices identify a planning artifact, not production UI requirements.

## 4. Design system and visual language


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
| `custom:project-band band collapsed/expanded` | Semantic article and button with aria-expanded/aria-controls; no invented library attribution |
| `custom:account-disclosure native closed/open/focus` | Shared native details/summary with Escape/outside dismissal |
| `custom:owner-filter native all/mine/other` | Labelled native select; staff-only |
| `custom:scene-preview SVG illustrative` | Inline SVG depicting a neutral mock scene, not a WebGL renderer or stored thumbnail contract |
| `kit:motion expressive/natural/subtle active/reduced` | `@kit/motion` profile; `motion.button` from `motion/react`, spring from useMotionProfile |
| `kit:planning-controls native selected/focus` | `mountMockup/useMockup` from `@kit/mockup`; native view/state/scene/theme/motion selectors |


## 5. Navigation and interaction model


The list opens own projects in Taller and foreign projects in read-only view. The product destinations remain `/proyectos` for the list, `/proyectos/[id]` for opening a saved project and `/3d` for the Taller, as named by the UI brief. The HTML simulates navigation locally, with no network request. View changes focus H1; disclosures keep focus on the invoking control. Preview buttons expose expanded state and a target id. First save and copy require a trimmed non-empty name. Dialog Escape/cancel return to the exact surviving invoking control; there is a name/button/H1 fallback after the source view is replaced. Closed details explicitly hide their bodies, preserving disclosure visibility and measurement.

Motion grammar is tactile, finite and legible throughout. Expressive uses 520ms settle / 170ms controls / 55ms band offsets with cubic-bezier(.34,1.4,.64,1). Natural is 320/140/30ms and subtle 160/100/12ms. Distinct behaviors present in the artifact:

1. Band load/view choreography compresses .985, lifts briefly and settles; each subsequent band offsets 55ms.
2. The expanded scene seats from .965 through 1.008 to 1 without hiding its text.
3. Notices settle with a short vertical compression, independently of the scene.
4. Save status icons rotate -14° through 5° to zero and settle in scale.
5. Inline edit fields seat from scaleX(.96) through 1.01 to 1, anchored at the text edge.
6. Button hover raises its icon; press compresses to .965. The name control uses the installed Motion spring, stiffness 220/damping 16 for expressive.
7. Pending save/import has a rotating icon only while pending; keyboard feedback remains a static high-contrast outline.

Reduced OS preference, Quieto and `?still=1` remove travel, animated transitions and spinning while retaining every state, control and status word. Hidden-tab CSS animations are paused in the product; there is no persistent decorative ambient effect. Entrance motion uses transforms without layout changes, opacity reduction or mid-animation colour changes.



Additional navigation rules: opening an owned row restores its name and complete scene; foreign rows go to V4. The HTML simulates these destinations; production `/proyectos/[id]` must use authorized data. Returning to the list, creating a scene, selecting a template and opening a library scene must pass the same pending-work guard. Do not replace the scene or project identity on a failed, conflicted or unfinished save. A pristine saved scene may proceed directly. Account-menu destinations remain owned by SP-2/planes; retained contextual tools in the mockup display a scope notice.

The inline name accepts up to the existing 120-character limit. Enter/check confirms a trimmed non-empty name, Escape/Cancelar restores the prior name and returns focus. A blank inline name remains in editing without committing; first-save/copy blank names show the explicit field error in D1/D2. Renaming a never-saved scene does not create an account project or enable autosave. Renaming an owned saved project becomes a pending change and follows the same save/refusal rules as scene edits. Foreign originals have no rename control.

## 6. Flows

**F1 — First named save and autosave (R6).** Build or open a new unsaved scene in V3. Show “Escena nueva” and “Sin guardar todavía”; no account upload occurs. Guardar proyecto opens D1. Cancel leaves the scene intact; a blank trimmed name keeps D1 open with “Escribe un nombre para el proyecto.” Submit displays Guardando… and disables duplicate submission. Only confirmation of the current account, project identity and submitted edit generation may show “Guardado en tu cuenta”. Later edits autosave; Guardar ahora requests the same guarded save. The inherited 500 ms debounce is a technical default, not an additional owner promise. A late acknowledgement of an older generation never marks newer edits saved.

**F2 — Start a new project (R6).** Escena nueva, a template and Abrir en Escena use the same guard. If an owned project has pending edits, save them successfully before replacement; while saving, keep the destination pending. Failure/offline/conflict retains the scene and blocks replacement. A never-saved scene opens D3 with Guardar y continuar, Descartar escena y continuar, and Cancelar (visible artifact wording: “Descartar escena y continuar”). Save opens D1 and continues only after confirmation; explicit discard starts the requested scene without modifying a saved original. The result is “Escena nueva” with no saved project identity and no upload until first named save. Leaving to Proyectos uses D4 and continues to the original requested destination after save, rather than creating a fresh scene.

**F3 — Search and reopen (R6).** In another authenticated browser, enter V1 or authorized V2. Search names across the entire authorized server collection, including beyond the first loaded page. Owner filtering applies before pagination. Changing query/scope resets cursors and ignores obsolete responses. Loading more preserves existing rows; failure places a reason and Reintentar below them. Empty account and no-match search are distinct. Abrir restores the saved name and complete scene. Foreign originals use F6. A missing or unauthorized resource shows non-disclosing feedback without cached names/owners/scene content.

**F4 — Competing save (R6).** A stale revision yields conflict, stops autosave, keeps the unsent local scene and shows both Cargar versión del servidor and Guardar una copia. Normal save stays disabled. D5 explains that loading replaces the displayed scene while retaining the local recovery draft; cancel leaves local work visible. No automatic merge or silent overwrite occurs. Owned-copy D2 creates a separate project in the current account and does not write the original. If copy fails, local work remains available; only a confirmed copy becomes the active saved project.

**F5 — Offline, refusal and recovery (R6).** Show “Sin guardar · Sin conexión” or “Sin guardar · Error”, keep the scene/name and explain retry. Retry returns to Guardando… until confirmation; do not imply that local browser backup equals account save. A server refusal, including invalid/oversized data or forbidden mutation, preserves pending work and gives recovery guidance. Browser-backup failure explicitly asks the user to keep the view open and retry backup. Account-scoped recovery offers Recuperar borrador; loading a recovery draft makes it unsaved/pending. Session expiry directs sign-in with the same account; account/project switch never exposes another account's drafts or receipts. No cross-account local recovery is offered.

**F6 — Staff opens a foreign original (R6).** V2 filters permitted owners; Abrir leads to V4 with owner and Solo lectura. No editing tools, editable name or save-original action exists. With `taller.usar`, Guardar una copia opens D2, explains destination/current account and original retention, requests a name and creates an owned project after confirmation. Without the permission, the copy action is absent. Back returns to the authorized list; opening itself never transfers ownership.

**F7 — Import browser scene (R7).** On first authenticated entry with raw `taller3d:escena:v1` data, V5 offers review for the current account. D6 identifies the destination and warns that shared-device data may belong to someone else. Importar a mi cuenta is explicit consent; Ahora no/Escape dismisses without uploading or modifying the source, and a list entry allows returning later. Pending import disables duplicate submission. Acceptance creates exactly one owned project per account/raw source even after response loss and retry; production uses the existing specified account-plus-source deduplication. Confirmation says “Escena importada”, “Se ha creado un proyecto en tu cuenta” and that the original remains. Error allows safe retry and original download. Invalid JSON, unsupported schema or incompatible data explains why nothing was imported and exposes Descargar original without an import submit. Success, refusal and failure all preserve the raw source unchanged. Another account receives its own consent, not a previous account's receipt. AI conversation/images are explicitly excluded.

## 7. View specifications

| View | Route / purpose | Structure, copy and actions | Responsive / flow |
|---|---|---|---|
| V1 `projects` | `/proyectos`, own saved scenes | Proyectos title, Escena nueva; Buscar por nombre; browser-import entry; full-width project bands showing name, Mi cuenta and confirmed account status; Ver/Ocultar escena, Abrir; Cargar más or retry/end state. Expanded band: scene, Escena completa, scene/name persistence explanation, Qué se guarda disclosure. | Same band identity at every width; detail stacks on phone; F2/F3/F7. |
| V2 `staff` | `/proyectos`, authorized all-owner scope | V1 vocabulary plus labelled Propietario selector: Todas las cuentas, Mi cuenta and authorized owners. Foreign bands show owner + Solo lectura; search covers this authorized collection. The artifact uses neutral Cuenta de ejemplo fixtures rather than real identities. | Filters wrap before bands; F3/F6. |
| V3 `workshop` | `/3d` and an owned saved project's editing destination | Existing Taller context; inline scene-name control, visible save status, Qué se guarda, Guardar proyecto or Guardar ahora. Failure/recovery/import notices precede the canvas. Existing tools remain contextual, not redesigned. Footer creation/template/library entries share the guard. | Header/status/actions wrap; scene retains available width; F1/F2/F4/F5/F7. |
| V4 `readonly` | Authorized foreign `/proyectos/[id]` | Project title, owner and Solo lectura banner; complete scene; optional Guardar una copia; explanatory save boundary and Volver a proyectos. No editing or save-original controls. | Banner/actions wrap; scene scales within frame; F6. |
| V5 import presentation | Contextual notice in V1/V3; D6, not a new route | Escena guardada en este navegador, current-account explanation and shared-device warning; Revisar importación. Invalid/error/success variants preserve context and original-download recovery. V5 is represented by view+state, not a fifth Vista option. | Notice and dialog actions stack on phone; F7. |

| Dialog (`scene`) | Contents and outcomes |
|---|---|
| D1 `first-save` | Guardar proyecto; labelled Nombre del proyecto, existing 120-character limit; scene/name-only explanation; Guardar proyecto/Cancelar; associated empty-name error; Guardando… and disabled duplicate submit. |
| D2 `copy` | Guardar una copia; current-account destination and unchanged original; editable proposed copy name; copy/Cancelar; same validation/busy rules as D1. |
| D3 `new-scene` | Antes de abrir una escena nueva; pending account-save explanation; Guardar y continuar; explicit discard only for never-saved scene; Cancelar. Failure/conflict/pending save prevents replacement. |
| D4 `leave` | Guardar proyecto title in the selected artifact, pending-change explanation; Guardar y continuar, explicit discard only when never saved, Cancelar. Successful save continues to the requested list destination. |
| D5 `server-version` | Cargar versión del servidor; explains retained local draft and replacement of displayed scene; explicit load/Cancelar; no merging. |
| D6 `import` | Importar escena del navegador; current-account destination, shared-device warning, scene-only scope and raw-source retention; Importar a mi cuenta/Ahora no; invalid/error explanation plus Descargar original; pending submit disabled. |

The empty scene inspector means no dialog. Modal background is inert; focus stays inside, then returns to the surviving trigger (or scene name/heading fallback after navigation). Busy save/import controls prevent duplicate actions and accidental replacement while a submission is pending.

Spanish is the SP-4 production copy baseline. New strings belong in planned `src/components/proyectos/textos-proyectos.ts`; SP-8 owns language rollout and account preference. The mockup language control offers ES/EN for expansion checks, not a new implementation of language persistence. Project names are data and remain untranslated. Examples are marked mock: neutral scene/project/account names and an illustrative inline SVG. It is not a WebGL renderer, a server thumbnail field, a thumbnail-generation feature or evidence of persisted scene fidelity.

## 8. States

Native Estado exposes every id below; Vista selects V1/V2/V3/V4 and Diálogo independently reaches D1–D6. State/view pairs are meaningful only as listed; selecting an unrelated pair keeps the normal surface instead of inventing another business rule. Named dialogs can be inspected independently, including validation through submission. Status and failures use visible words plus semantic status/alert roles, never colour alone.

| State id | Applicable view | Visible presentation, available action and transition |
|---|---|---|
| `normal` | V1–V4 | Authorized project bands or confirmed account-save text; preview/open/name/copy as permissions allow. No pending edit is represented by saved text in production. |
| `loading` | V1/V2 | Skeleton bands and polite Cargando proyectos…; no fabricated results/counts. |
| `empty` | V1/V2 | Todavía no tienes proyectos; explains creating and naming a scene; Escena nueva remains the next action. |
| `no-results` | V1/V2 | No hay coincidencias; try another name/owner; Limpiar búsqueda restores the permitted list scope. |
| `next-page` | V1/V2 | Additional rows appended; end state No hay más proyectos disables load-more. |
| `next-page-error` | V1/V2 | Existing rows retained; No se cargó la siguiente página and Reintentar below them. |
| `unsaved` | V3 | Escena nueva / Sin guardar todavía; first save opens D1. Renaming alone does not create a saved identity. |
| `saving` | V3/D1/D2 | Guardando… and busy submission controls. Save or guarded transition waits; acknowledgement must match current project/account/edit generation. |
| `offline` | V1/V2/V3 | List: Sin conexión and Reintentar. Taller: Sin guardar · Sin conexión, scene retained and retry-when-connected action. No account-save claim. |
| `error` | V1/V2/V3 | Could not load/save explanation; visible retry; pending scene retained. Production mutation refusals use this recovery vocabulary without exposing implementation/security details. |
| `conflict` | V3 | Conflicto de guardado; autosave stopped and local draft retained; server-load/copy actions; Guardar ahora disabled. |
| `no-taller` | V4 | Foreign original remains readable to read-all permission holder; edit and copy actions absent. |
| `import-offer` | V1/V3/V5 | Legacy scene notice, current-account/shared-device explanation and Revisar importación. No automatic import. |
| `import-invalid` | V1/V3/D6 | Incompatible data/version explanation, Ver explicación and Descargar original; D6 has no import submit. Source unchanged. |
| `importing` | D6 with V1/V3 context | Importando…; duplicate import and dismissal actions disabled during the pending operation. This inspector is a static pending illustration, not a backend job. |
| `imported` | V1/V3/V5 | Escena importada, one-owned-project confirmation and original-retention message; Ver proyectos. |
| `import-error` | V1/V3/D6 | Failed confirmation explanation; safe import retry and original download. A retry does not create an extra project. |
| `recovery` | V3 | Account-scoped local draft notice, Recuperar borrador; recovered work becomes pending rather than account-saved. |
| `local-error` | V3 | No pudimos conservar el borrador en este navegador; keep view open and Reintentar respaldo. No false backup/account confirmation. |
| `permission-denied` | All | Access refusal; no project names/owners/scene content; recovery to authorized projects. |
| `unavailable` | All | Proyecto no disponible; non-disclosing recovery, with no foreign metadata. |
| `session-expired` | All | Tu sesión ha terminado; same-account sign-in guidance, no scene/project data exposed. |

Controls also cover default, hover, pressed, focus, disabled and busy. D1/D2 invalid names expose labelled `aria-invalid` fields and associated errors; cancellation preserves prior work. Inline rename cancellation keeps its prior name. Pending/local-unsent work is the applicable stale-data presentation; conflict is the stale-server-version recovery. There is no separate optimistic “saved” state. Offline list data are not labelled freshly loaded; if production retains earlier rows on refresh, their stale/loading status must be explicit.

Not applicable: purchase/plan changes, delete/transfer/history/merge confirmations, bulk selection, public sharing and publishing to the global decorations library. They are outside R6/R7. Dialogs need no additional consent checkbox: Importar a mi cuenta and Ahora no are explicit affirmative/refusal actions. Existing WebGL, AI-generation, undo/redo and shopping-list internal states are owned by their existing surfaces; their mockup controls are context and show an explanatory Mockup notice.

## 9. Responsive behavior

Supported design range is 360px upward; primary rendered checkpoints are 390px phone, 768px tablet and 1280px desktop in both themes. Layout follows the selected TSX's exact boundaries:

- **360–639px:** 20px outer gutter; masthead/account/language wrap; heading and action stack. Search/filter are full width. Band title/metadata precede wrapped preview/open actions; scene then explanation stack inside the same band. Band header padding 24px 20px, detail 0 20px 24px. Taller identity/name/status/save controls wrap; rail and inspector hide, existing phone tool context remains. Canvas stays inside the scene frame. Dialog width is viewport minus 40px, padding 24px, actions stack; vertical scrolling keeps every action reachable.
- **640–1099px:** 24px outer gutter; wrapping masthead; search/filter toolbar becomes one column with actions aligned at start. Expanded band is 1.3:1 with a 240px minimum explanation column; the Taller inspector hides, rail and canvas remain. Do not turn the project list into cards or a sidebar.
- **1100px and above:** 40px outer gutter within a 1520px maximum shell; band header identity/actions share a row; detail is 1.8:1 with a 260px minimum explanation column, 28px detail inset/gap. Taller rail/canvas/260px inspector remain visible. Dialog max width 580px, padding 28px.

Buttons remain at least 44px high. Long names and Spanish/English controls wrap, without horizontal page scrolling or truncating the save reason. Dialogs cap height at viewport minus 48px with internal vertical scrolling. Page content may scroll vertically; no hidden primary action is justified by a short viewport. At zoom/reflow the corresponding narrow composition applies. The real Taller's canvas interactions remain unchanged by this contract.

## 10. Accessibility targets

Target applicable WCAG 2.2 AA; this draft and mockup checks do not certify conformance. Preserve semantic heading order, navigation/current-route state, project articles and labelled search/owner/language controls. Every control has an accessible name; decorative icons/SVG shapes are hidden, scene illustrations have descriptive container labels. Preview buttons expose `aria-expanded`/`aria-controls`; disclosures retain keyboard Enter/Space and hide closed bodies.

Name fields have programmatic labels. D1/D2 validation uses `aria-invalid` and an associated error, preserves the entered value and keeps the task open. Save/load/import status is polite live feedback; actionable failures use alerts and a visible retry/recovery action. Do not repeatedly announce unchanged autosave text. Page/view changes move focus to H1; disclosure toggles retain invoking focus. Inline name confirmation/cancel returns focus to the name control. Dialogs have a programmatic title/description, inert background, keyboard containment, Escape/cancel and invocation-focus return; a surviving scene name/button/H1 provides fallback when navigation removes the trigger. During pending submission, do not let dismissal cause scene replacement or discard.

Focus is a 3px accent outline, 4px offset; focus and control edges target ≥3:1 against their adjacent surface. Body/support text targets ≥4.5:1 in both themes (large-text minimum ≥3:1); use texto-tenue for meaningful control edges and decorative borde only for nonessential rules. State is communicated with text/icon plus colour. Interactive targets in this artifact are at least 44px high, meeting the applicable 24px target minimum with spacing. Reflow, enlarged copy, short viewport access and bilingual labels must remain usable.

Reduced OS motion, Quieto and `?still=1` remove travel, spinning and transitions while preserving all words/actions; no flashing or animation-only message. Hidden-tab CSS effects pause; there is no heavy ambient animation. The installed Motion profile controls the name press spring and kit dialog motion. Rendered contrast/focus/layout checks and interaction probes are evidence about this HTML only; screen-reader behavior, 200–400% zoom, production WebGL keyboard access and all actual API/persistence/security guarantees still require their independent implementation reviews.

## 11. Visual acceptance criteria and verification

“All” below means the supported 360px+ range, checked at least at 390/768/1280px where applicable, in light and dark. Inspectors reach the named state/view/dialog; functional persistence claims require the real SP-4 integration evidence, not the fixture.

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | All | All | The Pictures/Sempertex masthead and shared Geist/account/navigation vocabulary are preserved. |
| UI-AC-02 | 1100px+ | V1/V2 normal, expanded | The expanded scene sits inside its full-width project band with explanation beside it. |
| UI-AC-03 | 360–639px | V1/V2 normal, expanded | Scene and explanation stack inside the same band without horizontal page overflow. |
| UI-AC-04 | All | V1/V2 normal | The first authorized band initially has its preview expanded. |
| UI-AC-05 | All | V1/V2 expanded/collapsed | Ver/Ocultar escena updates the selected band's expanded state and permits at most one preview. |
| UI-AC-06 | All | V1/V2 loading | Loading displays skeleton bands and Cargando proyectos status. |
| UI-AC-07 | All | V1/V2 empty | Todavía no tienes proyectos explains creating a named scene, with Escena nueva available. |
| UI-AC-08 | All | V1/V2 no-results | No hay coincidencias includes a clear-search recovery action. |
| UI-AC-09 | All | V1/V2 next-page-error | Already loaded rows remain visible above the next-page error and Reintentar. |
| UI-AC-10 | All | V2 normal | The owner filter is labelled Propietario and foreign entries show owner plus Solo lectura. |
| UI-AC-11 | All | V3 inline rename | The name control becomes an input in the same header position and returns focus on confirm/Escape. |
| UI-AC-12 | All | D1/D2 invalid | Empty-name submission keeps the dialog open and exposes the associated name error. |
| UI-AC-13 | All | V3 saving | Guardando… remains visible while save is pending. |
| UI-AC-14 | All | V3 unsaved after F2 | The new scene displays Escena nueva and Sin guardar todavía. |
| UI-AC-15 | All | D3/D4 unsaved | Cancel preserves the current scene; explicit discard is visibly separate from saving. |
| UI-AC-16 | All | V3 conflict | Server-load and owned-copy actions appear together while normal save is disabled. |
| UI-AC-17 | All | V3 offline/error | The unsaved reason appears with the scene context and an explicit retry. |
| UI-AC-18 | All | V4 normal | The foreign original has no editable name, editing tools or save-original action. |
| UI-AC-19 | All | V4 no-taller | Guardar una copia is absent. |
| UI-AC-20 | All | D6 import-offer | Current-account destination and shared-device warning appear before explicit import/refusal. |
| UI-AC-21 | All | D6 import-invalid | Explanation and original download are available, with no import submit. |
| UI-AC-22 | All | V5 importing | Importando feedback and disabled duplicate submit are visible. |
| UI-AC-23 | All | V5 imported | One-project confirmation explicitly states browser-original retention. |
| UI-AC-24 | 390/768px | D1–D6 | Modal content stays within its viewport frame and actions remain reachable by vertical scrolling. |
| UI-AC-25 | All | Keyboard dialogs | Escape/cancel returns focus to the surviving invoking control or declared navigation fallback. |
| UI-AC-26 | All | Reduced/Quieto/still | State words and actions remain visible with no travel/spinning. |
| UI-AC-27 | All | Expressive normal | Bands and previews use the chosen finite press/settle choreography without hiding content. |
| UI-AC-28 | All | Permission/session/unavailable | The refusal surface exposes no project metadata or scene. |
| UI-AC-29 | 640–1099px | V1/V2/V3 normal | The toolbar wraps and Taller inspector hides while the scene remains inside the content width. |

Evidence below belongs to the **canonical HTML rebuilt in this finalization**, not the exploration's historical audit. The selected TSX remained byte-identical; no behavioral source edit, fallback, package installation, network fetch or production change was required.

| Check | Actual observation |
|---|---|
| Installed kit | `installed=True built=True entries ok=96/96`. |
| Current offline build | Exit 0; 648 KB, 2,126 source files; real React/shadcn/Animate UI/Base UI controls with inlined CSS, JS and local fonts. |
| `contrast.py` | Exit 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Offline rendered audit | Exit 0: 672 renders / 672 planned combinations; 17,388 text measurements and 1,959 focus stops at 1280, 390 and 768px in both themes. No sampling. |
| Focused interaction walkthrough | Exit 0: `INTERACTIONS: PASS 17 groups`; zero page errors and zero external HTTP(S) requests. Covers native inspectors, keyboard search, single preview, owner filter/pagination reset, page retry, inline name confirm/Escape/focus, first-save validation/pending/confirmation, conflict copy/modal focus, offline retry, foreign read-only/copy permission, template guard, invalid import/download/Escape, explicit refusal/acceptance, pending-save guard, save-before-list navigation and English copy. |
| Motion probes | At 120ms: 3 active expressive animations; 0 with OS reduced motion; 0 with `?still=1`. |
| Visual inspection | In-memory screenshots inspected: 1280px dark project bands, 1280px light Taller, 390px dark conflict, 390px light invalid-import dialog. No screenshot files written. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Reproducible required commands (absolute paths are intentional):

```text
python3 /home/david/.agents/skills/metodologia/scripts/bitacora.py components status
python3 /home/david/.agents/skills/metodologia/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.r12.dir-c.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.html
python3 /home/david/.agents/skills/metodologia/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/.agents/skills/metodologia/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.html --widths 1280,390,768 --max-combos 240
```

The optional probes ran as inline Playwright scripts without saved test artifacts. Earlier probes had a diagnostic-expression typo, an ambiguous template-control locator and an immediate assertion before dialog dismissal settled; their expressions/locator/wait were corrected, with no HTML/TSX mutation. The final consolidated 17-group command completed successfully. These checks support this planning artifact's rendered behavior; they do not approve it or establish production storage/security conformance.

## 12. Open questions and assumptions

**Open product questions:** none prevents finalization under the supplied brief and owner-selected direction. The r12 note asked whether to start with the first preview expanded; this finalization preserves exactly that visible selected composition, as instructed. This is a carried presentation assumption, not a claim that the owner separately answered that question. Any later change must be an explicit draft amendment, not an implementer invention.

**Confirmed decisions:** first named explicit save then autosave; never-saved new-project identity; same guard for Escena nueva/templates/Abrir en Escena; server-confirmed current-revision status; conflict retains local work; foreign-original read-only and copy gated by Taller; only name/complete scene sync; explicit retry-safe lossless import for the current account. These come from SPEC/brief and are not reopened.

**Fixture limits / follow-up owners:** save/import timings, filtering, scene illustration and transitions are in-memory mock data. The downloaded `escena-original.mock.json` demonstrates a recovery control; it is not actual legacy recovery. No backend, storage, atomic revision validation, idempotency, full-collection server query, cross-browser scene fidelity, real permission enforcement or account-switch draft isolation is implemented or proven by this artifact. T4.2–T4.7 and the independent reviews own those checks. The current HTML preserves r12's title/footer provenance and contextual existing-tool placeholders; neither is production copy. ES/EN layout simulation does not claim full product translation or persisted language selection. No preview directory is produced.

**CONCERNS:** `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`. No fallback/toolchain blocker. The artifact remains an unapproved draft; production behavior and independent acceptance are unverified here, and the initially expanded first preview is carried from the selected composition as described above.

**Approval:** David/independent approver must approve this exact draft through the planning workflow before T4.1 copies it for consumption. Designer grants no approval. Canonical finalization is complete; implementation and independent acceptance remain with their assigned tasks.

### Input/artifact identity

| Input / artifact | SHA-256 |
|---|---|
| `SPEC.md` | `7f99f01dd99318864a66f99d85902e4b3de4b07ab0694b873125aee8a8331660` |
| `PLAN.json` | `63c04b811e851a3b056671e9c26e999228c6bb91c84bddf3497c91be8d109462` |
| `design/proyectos@v1.r12.behavior.md` | `1d89ee0c436645cf1af3f8ac62d888d9ad089801f688870a48344d862c1c2b65` |
| `design/proyectos@v1.r12.dir-c.md` | `880305b825c2859e469a88965c336f2c60aff7f1018f01e901bdb2a9e0321186` |
| `design/proyectos@v1.r12.dir-c.tsx` | `4de35ec0f1c7fbe4964d4d3b9c706dd96b721137ab503ddc32a3e6464c729b4f` |
| `design/proyectos@v1.r12.dir-c.html` | `403ac3672d0c14edf9f280ba26368b971bc09ce8227acd9ea9649db9236b465f` |
| `design/proyectos@v1.html` | `906852d5a0d4d04bd724e05302eab6ade35e65eae40ee2ebf4b230ed36b1a0b6` |
