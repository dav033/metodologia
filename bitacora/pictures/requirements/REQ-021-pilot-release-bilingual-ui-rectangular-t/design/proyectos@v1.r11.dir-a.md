---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
direction: a
name: Registro de proyectos
source_revision: r11
source_behavior: proyectos@v1.r11.behavior.md
approval: pending-owner-selection-and-plan-approval
---

# Registro de proyectos — exploration A, r11

## 1. Identity and traceability

This is a revision-specific exploration for **proyectos@v1**, not the canonical contract and not an approved implementation input. It changes only the saved-project surfaces of the existing product. Choosing this direction does not approve the plan. No shared contract, PLAN, repository source, changelog or project-memory file is written by this delegation.

Behavioral authority: `proyectos@v1.r11.behavior.md` (SHA-256 `1d89ee0c436645cf1af3f8ac62d888d9ad089801f688870a48344d862c1c2b65`), R6/R7, and SPEC “Behavior — SP-3 and SP-4 (round 9 answered)”. SPEC and PLAN remain actively edited by their owners; their unrelated engineering sections are not design scope. Source snapshot at inspection: SPEC `032cbfb717c61ff8edc32160716a92fb925e8d41e1e31c8f62176f8da9decd7d`; PLAN.json `c7600864b9a1b48b9381622f346ca3e32e7e7cff61180ca20af10e7e6db2793f`.

Read-only product sources inspected in t12 and asesor: `src/app/globals.css`, `layout.tsx`, `3d/page.tsx`, `Taller3D.tsx`, `guardado-escena.ts`, `guardado-conversacion.ts`, `imagenes-guardadas.ts`, `Biblioteca.tsx`, `CabeceraApp.tsx` and `/api/decoraciones`. The latter is the decorations library, not project storage. The existing app has browser saving, an inline scene name and a save-status label; account-backed lists, conflict handling and legacy import are the scoped additions. Preserve separate browser-only AI conversation and image storage.

Shared shell authority: finalized sibling drafts `cuentas-admin@v1.md/.html` and `planes@v1.md/.html`. Their compact Pictures/Sempertex ring-and-dot mark, Geist type, neutral horizontal navigation, rounded papers, pill actions and account disclosure are retained. The latest brief explicitly supersedes the old feedback requesting separate palettes/fonts; those historic directions are not reused. No new brand, font or palette is introduced.

Affected consumers if the owner later chooses and approves this direction: SP-4 design copy T4.1, UI implementation T4.4/T4.5 and visual review T4.8. Compatibility versus the old unapproved exploratory layout is **breaking visual**: sidebar/archive composition becomes the shared product shell and a continuous register. R6/R7 semantics and round-9 behavior are preserved. No other subplan is implicitly redirected or approved.

## 2. Purpose and users

The owner answers “Which saved scene do I want to continue?” Staff can additionally find an authorized owner's project and inspect it without modifying their original. The Taller makes the name and actual save condition readable beside one another. A first-sign-in prompt asks whether this browser's legacy scene belongs in the current account; consent is explicit.

All fixtures are neutral and clearly marked Mockup: Mesa rectangular, Arco, Backing, Columna and Guirnalda with “· ejemplo”; Cuenta de ejemplo and Otra cuenta de ejemplo; `cuenta@prueba.local`. There are no invented customer identities, event dates, promotional slogans or history. Counts derive from the in-memory list. Projects saved during the mock interaction are added to that same list. Refreshing the HTML resets all operations; no application localStorage, IndexedDB, account or remote service is accessed.

## 3. Approach, composition and chosen thumbnail

Two small HTML compositions were drawn first. **Candidate 1 is chosen:** one continuous ruled register, with search and owner on a shared bar and an immediate Open action on each row. **Candidate 2** explored a list/detail split; it spends substantial width on a preview and adds a selection step before opening, so it is weaker for this operational stance. Both thumbnails remain immutable evidence in the assigned r11 paths.

The chosen composition changes the product only where saved projects need a new surface. It keeps the siblings' masthead, 24px page heading, neutral Proyectos/Taller route rule and aligned footer. Name, owner, status and Open share a baseline on desktop; phone rows stack the name above owner/status with Open beside them. No card grid, project-history timeline, promotional rail, delete or transfer action is added.

Taller preserves its existing editor anatomy: inline-editable scene name and status in the top toolbar, panel rail, scene canvas, scene/IA inspector and existing photo/shopping-list context. The save control, account/project navigation and persistent conflict/offline notices are the additions. The illustration and simplified existing tool fixtures are contextual, not a redesign or replacement for the production renderer/editors.

Import is a first-sign-in prompt above the project list, not a new /import page or permanent product route. The account receiving the scene is visible before consent. The Mockup access selector is an inspection fixture, never a product setting that grants staff permissions.

### Eight-axis table

| Axis | Rendered expression |
|---|---|
| concept | Operational project register: names, owners, true save state and opening remain aligned in one working surface. |
| layout | Pictures/Sempertex shell and horizontal route rule above one full-width ruled list; Taller preserves its toolbar, tool rail, canvas and inspector; import is an inline first-sign-in prompt above the list. |
| navigation | Shared account disclosure and Proyectos/Taller routes; rows open directly without a detail rail; owner filter and name search share a bar; contextual name/load/leave dialogs. |
| typography | Existing local Geist Sans: 24px page title, 20px section title, 17px project names, 14px actions and 12–13px supporting data; Geist Mono limited to existing metadata/count roles. |
| density | One continuous 28px-inset paper, 24px ruled rows, 20px phone insets, 44px actions. Desktop groups owner/status/open on the name baseline; phone stacks identity above owner and status beside Open. |
| components | Installed shadcn/Base UI Button, Input, Skeleton, Animate UI Dialog and AlertDialog; native role/owner/language selectors and account details; no ornamental card grid. |
| colour | Exact Pictures globals.css light/dark tokens, inherited SP-2/SP-14 role aliases and rounded shapes. Accent on primary action, semantic success/warning/error on actual status. Input and outline-control boundaries use texto-tenue. |
| motion | Precise registration: 360ms cubic-bezier(.77,0,.175,1) paper 8px, row 10px with 28ms offsets, feedback -6px, status -5px; 150ms button lift/press/arrow/focus. Saving rotates and skeleton compresses; reduced/still settles instantly, hidden-tab animations pause. |

## 4. Fixed design system and components

Use the existing Pictures light/dark tokens; do not import the kit's default palette. `--fondo` maps to background; `--superficie` to card/popover; `--texto` to foreground; `--texto-suave` to muted foreground; `--superficie-2` to secondary/muted/neutral hover; `--acento` and `--sobre-acento` to primary roles; `--exito`, `--aviso`, `--error` to real semantic status. `--borde` and `--borde-suave` remain decorative rules; `--texto-tenue` supplies the accessible input and outline-button edge, following SP-2/SP-14. No new colour values are proposed.

| Source token | Light | Dark |
|---|---|---|
| fondo / superficie | #faf9fc / #ffffff | #0b0c10 / #16181f |
| superficie-2 | #efe9f8 | #242733 |
| texto / texto-suave | #1c1425 / #6b6178 | #f4f5f7 / #9aa1ad |
| texto-tenue | #766c85 | #8a91a0 |
| acento / sobre-acento | #6d3fe0 / #ffffff | #9479ff / #120b24 |
| acento-hover | #5530b8 | #a58dff |
| borde / borde-suave | #e3daef / #efe9f8 | #383c48 / #2a2d38 |
| exito / aviso / error | #1f7a55 / #8f5f12 / #b23a45 | #78d6a8 / #f7c46b / #ff979f |

Local production Geist Sans and Geist Mono WOFF2 assets are bundled from t12's existing build, matching the siblings. No font request or installation occurs. H1 24px, H2 20px, project names 17px, actions 14px, labels/support 12–13px; counts use tabular mono only. Panel/inset/field/pill radii 32/24/18/999px are inherited from the selected sibling vocabulary. Papers use 28px desktop and 20px phone padding; dialogs 28/24px; controls have 44px minimum height.

| Component contract | Actual source / use |
|---|---|
| shadcn:button default ready/hover/focus/pressed/disabled/loading | `@/components/ui/button`; save/new/import, explicit status-dependent disabled state |
| shadcn:button outline ready/hover/focus/pressed/disabled | Same; Open, retry, cancel and contextual tool fixtures |
| shadcn:input text empty/filled/focus/invalid/disabled | `@/components/ui/input`; associated labels for search and project name |
| shadcn:skeleton register/scene loading | `@/components/ui/skeleton`; placeholders maintain content geometry |
| shadcn:dialog name/copy/pending open/closed | `@/components/ui/dialog`; real Animate UI/Base UI primitive, no HTML imitation |
| shadcn:alert-dialog load-server/discard-unsaved open/closed | `@/components/ui/alert-dialog`; explicit confirmation and initial Cancel focus |
| native:select language/owner/inspection default/focus/disabled | Labelled native selects; no shadcn Select claim |
| native:details account/biblioteca closed/open/focus | Existing account vocabulary and contextual library fixture; not an ARIA menu |
| custom:project-register ruled results/loading/empty/error | Semantic list of project articles with aligned data and per-project action names |
| custom:save-status inline saving/saved/pending/offline/error/conflict | Extends the existing scene-name/status position; text plus icon, never colour alone |
| custom:import-prompt account-scoped pending/success/refused/invalid | Explicit current-account consent and downloadable original fixture |
| custom:scene-illustration SVG contextual/empty | Inline static scene; not a working 3D engine or export promise |
| kit:mockup inspector | `@kit/mockup` mountMockup/useMockup and `@kit/motion` useMotionProfile |

## 5. Navigation, focus and motion

Product routes are /proyectos and /3d or the planned /proyectos/[id] identity opening into Taller; the mock stays in one self-contained document. The account disclosure includes the shared Mi cuenta/Proyectos/Planes/sign-out vocabulary, with out-of-scope destinations explicitly labelled as simulated. Import is exposed by the native Vista selector only for inspection. Proyectos and Taller route links stay neutral. Staff owner filtering is shown by “Mockup · Acceso → Empleado / administrador”; ordinary owners have no other-account control.

Search retains keyboard focus while typing. It searches the complete authorized mock collection, including Columna beyond the first loaded page. Search/owner changes reset pagination. Production must apply those filters before pagination and ignore obsolete responses; the local synchronous mock demonstrates the resulting UI but is not an API/concurrency test.

Dialog triggers retain their focus target; Cancel/Escape dismiss normal dialogs and restore focus. AlertDialog requires an explicit choice and starts on Cancel. Base UI supplies modal focus containment/background inertness. Route changes focus H1. Account disclosure supports Escape and outside-click closure, with visible focus. The product heading and footer share the same horizontal container.

**Motion grammar: precise registration.** Expressive defaults to 360ms cubic-bezier(.77,0,.175,1), with 28ms row offsets. Natural uses 240/120/18ms and subtle 140/90/8ms for registration/quick/stagger; expressive quick controls use 150ms cubic-bezier(.23,1,.32,1). Actual behaviors: (1) paper 8px vertical registration, (2) rows 10px horizontal stagger, (3) feedback -6px registration on state changes, (4) status -5px registration, (5) button hover -2px, (6) press +1px/scale(.98), (7) opening-arrow movement, (8) focus-outline settling 5→3px, (9) saving rotation and (10) skeleton horizontal compression. Modal transitions use the motion profile/reduced state. Body text stays visible at full opacity during entrance; no unreadable intermediate fade.

OS reduced motion, Quieto and ?still=1 remove movement/repeated effects and keep final content/actions. Hidden tabs pause CSS animations. Continuous effects exist only on loading/saving status, not decorative offscreen content. There is no scroll/parallax or ambient decoration to suspend.

## 6. User flows

1. **First save:** enter Taller → Escena nueva / Sin guardar → Guardar proyecto → labelled name input → blank name announces validation → explicit save → confirmed Guardado en tu cuenta. Later edits transition pending → Guardando… → confirmed saved. Guardar ahora is an explicit shortcut. Changing the scene during an in-flight simulation invalidates that earlier timer; only the latest pending scene becomes saved. Production uses server-confirmed revisions, never a stale-response success label.
2. **New scene:** Escena nueva, Plantillas or the contextual Biblioteca “Abrir en Escena” use the same new-project boundary. A named project's pending edit saves before the new scene appears. Offline/error/conflict prevents completion and preserves the draft. A never-saved scene requires Save, Cancel or explicit Discard; cancellation leaves it in place. The resulting name is exactly Escena nueva, with Sin guardar and no saved identity; nothing reaches the server until a first named save. Existing project revisions remain intact.
3. **Reopen:** visit Proyectos under the same account → search/browse/load more → per-row Abrir → complete scene and its name. Changes in filters return to the first page. Next-page errors retain the current rows and offer Reintentar siguiente página. Real cross-browser persistence is implementation acceptance, not claimed by this HTML.
4. **Conflict:** show a persistent “Hay otra versión guardada” panel and “Conflicto · autoguardado detenido” beside the scene name → either Save as a new owned project via the name dialog, or confirm loading the server version. Loading replaces the visible scene and keeps a recoverable local draft for this account. There is no overwrite/retry-current-revision action and no version-history interface.
5. **Offline/error:** “Sin guardar” remains visible; retry is contextual. The scene stays local. Reconnection moves to pending; only subsequent confirmation produces Guardado en tu cuenta. An unsent local draft must not appear after another account signs in.
6. **Foreign read-only:** staff searches all authorized owners → opens another account's row → visible owner/read-only notice → editing fixtures absent/disabled. Save copy is available only with taller.usar and writes to the viewer's own account. Without taller.usar the action is disabled with a visible explanation. Opening never transfers ownership or updates the original.
7. **Legacy import:** first sign-in detects a raw browser scene → prompt names this account and the browser-only exclusions → Importar a mi cuenta creates one owned project after confirmation; retries refer to the same source/receipt. Ahora no creates none. Invalid fixture explains that escena does not contain a valid scene and offers Descargar original. Raw source is never changed or erased after any outcome. The mock download is clearly an invalid example JSON, never the user's browser data.

## 7. Views and local state selectors

| Vista value | Surface / contents |
|---|---|
| lista | Shared app shell; project heading; list search; staff-only owner filter; ruled rows; pagination and recovery |
| taller | Existing workshop anatomy; inline scene name/status; Save now/first save; offline/conflict feedback; scene context |
| consulta | Same workshop scene; foreign owner/read-only notice; no editing; permitted own-copy action only |
| importar | Same shared list shell with an explicit import prompt above it, receiving account, consent and preservation explanation |

The inspector retains native view/state/scene/theme/motion ids and Spanish labels Vista/Estado/Diálogo/Tema/Movimiento. Each declared state is selectable; states irrelevant to the current view leave its normal layout unchanged rather than inventing unrelated product behavior. The access fixture and ES/EN control do not change backend permissions or stored preferences. Initial content is Spanish; ES/EN is an illustrative copy/reflow reference, with final strings to be grouped in `textos-proyectos.ts` by implementation.

## 8. State coverage

| State value | Applies to / observable UI and recovery |
|---|---|
| normal | Normal list, account-saved Taller, foreign read-only, pending first-sign-in import |
| cargando | List skeletons or scene skeleton; import actions pending/disabled; no confirmed saved claim while scene loads |
| vacio | Project list explanation and Taller entry; not a fabricated empty user scene |
| sin-resultados | No-match explanation with clear-search action |
| pagina-siguiente | Additional authorized rows on the next loaded page |
| error-pagina | Existing rows retained, inline error and retry-next-page control |
| error | Scoped list/open/import failure and explicit retry; local data remains |
| nuevo | Taller name Escena nueva, zero-piece fixture, Sin guardar; first save asks for a name |
| guardando | Guardando… beside name; duplicate save disabled; editing can create a newer pending change; import pending label |
| guardado | Guardado en tu cuenta only after the simulated current save confirmation |
| pendiente | Changes pending → autosave simulation; Save now available |
| sin-conexion | Explicit unsaved/offline condition, draft retained, reconnect/retry action |
| error-guardar | Persistent save error, no false saved state, draft retained and retry |
| conflicto | Autosave stops; current local draft retained; own copy or confirmed server-load choices |
| datos-invalidos | Invalid import shape explained, no project created, download-original action |
| importado | Exactly-one import receipt and Open project action; original kept |
| rechazado | No project created, original remains, Continue to projects |
| validacion + guardar/copia | Associated required-name error; field and buttons remain reachable |
| sin-taller + consulta | Foreign original read-only, copy disabled, missing Taller permission explained |
| sin-permiso | Refusal without scene content or protected project name; return to own projects |

Scenes: guardar (first name), copia (owned copy), cargar (confirmed server load), descartar (never-saved replacement), continuar (blocked/pending departure). Failed saves preserve the entered field/current scene until recovery; source state switches are inspection controls, not production transitions. No delete, transfer, version history or account-management editing exists here.

## 9. Responsive rules

At >1100px use the full four-column register, 40px shell gutters and Taller rail/canvas/280px inspector. At 761–1100px use 28px shell gutters, three register columns (status remains available on the opened scene), flexible name/owner data and a 240px workshop inspector. Search and owner retain a 2:1 split when space permits.

At ≤760px use 20px page/paper gutters; row status text aligns with the name/owner edge without an offset icon; the common masthead's account/language controls wrap as in the sibling contracts; title/tools and filters stack. Project identity spans the row; owner/status sit at the left and Open at the right. No horizontal table scroller or clipped action is introduced. Taller collapses its contextual side rail and places its inspector below the full-width illustration; name, status and save control wrap without ellipsis. Phone dialog actions stack in reverse visual order, with primary action first visually and all choices accessible. Dialog width is viewport minus 40px and height is bounded below the inspection bar with internal vertical scrolling.

Targets: 390px phone, 768px tablet, 1280px desktop; 320px reflow is a guardrail. Portrait/short windows must scroll to all controls; there is no forced fixed-height working card. The inspection bar is outside the product and does not represent production height requirements.

## 10. Accessibility targets and limits

Target WCAG 2.2 AA: text ≥4.5:1, meaningful control boundaries/focus ≥3:1; ≥44px main actions; text-and-icon state labels; keyboard-reachable links, inputs, disclosures and dialogs; complete Spanish/English labels; programmatic H1/invalid-field focus; aria-live polite save status and alert errors; modal focus containment/restoration and explicit destructive choices. No native checkbox is required by this scope, so the historical dark-checkbox issue is not reintroduced.

The rendered offline audit tests actual computed styles rather than palette descriptions. It covers both themes, all inspector combinations and keyboard stops. Static contrast.py reads the builder's inline role sheet; runtime project-token overrides are additionally assessed by the rendered audit. Passing these checks does not establish full application accessibility, authenticated authorization, assistive-technology interoperability or cross-browser persistence. Those remain implementation/review work.

## 11. Visual acceptance criteria and evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| A-AC-01 | 1280px | lista/normal | Pictures ring-and-dot mark, Sempertex, language, account and neutral route rule match the sibling shell. |
| A-AC-02 | 1280px | lista/normal | Name, owner, state and Open share each ruled row; no project-card grid or detail rail appears. |
| A-AC-03 | 390px | lista/normal | Project name, owner, state and Open reflow inside 20px gutters without horizontal scroll. |
| A-AC-04 | 390/1280px | lista/cargando | Content-shaped skeletons appear with Cargando proyectos; there is no isolated central spinner. |
| A-AC-05 | 390/1280px | lista/vacio | Empty-state explanation and Taller entry are present. |
| A-AC-06 | 390/1280px | lista/sin-resultados | Clear-search action restores available authorized results. |
| A-AC-07 | 768/1280px | lista/staff fixture | Owner filtering appears for staff; ordinary owner mode exposes only own projects. |
| A-AC-08 | 390/1280px | lista/error-pagina | Existing rows remain visible with a retry-next-page action. |
| A-AC-09 | 390/1280px | taller/nuevo | Name is Escena nueva, status is Sin guardar and Save opens the name dialog. |
| A-AC-10 | 390/1280px | guardar/validacion | Empty name submission shows an associated error; no saved state is shown. |
| A-AC-11 | 390/1280px | taller/guardando | Status remains beside the scene name, duplicate save is disabled and further editing is possible. |
| A-AC-12 | 390/1280px | taller/sin-conexion | Unsaved/offline state and retry remain visible while scene context stays present. |
| A-AC-13 | 390/1280px | taller/conflicto | Autosave-stopped status and both copy/server-load choices are visible; Save now is disabled. |
| A-AC-14 | 390/1280px | cargar | Confirmation identifies local/server versions and Cancel receives initial focus. |
| A-AC-15 | 390/1280px | consulta/sin-taller | Read-only notice names the foreign context and Save copy is disabled with explanation. |
| A-AC-16 | 390/1280px | importar/normal | Receiving account appears before consent; browser-only conversation/images and raw preservation are explained. |
| A-AC-17 | 390/1280px | importar/datos-invalidos | Specific invalid-scene explanation and downloadable original are present; no success receipt appears. |
| A-AC-18 | 390/1280px | descartar | Never-saved replacement requires Save, Cancel or explicit Discard. |
| A-AC-19 | all declared widths | reduced/still | Animation stops at final readable layout; actions and state text remain available. |
| A-AC-20 | 390/1280px | both themes | Inputs, outline actions and native selectors have visible boundaries and keyboard focus. |
| A-AC-21 | 390/1280px | sin-permiso | No scene/protected name is disclosed; returning to own projects is available. |

### Actual verification

- Installed real workspace available: installed=True, built=True, 96/96 entries. No fallback, installation or fetched asset.
- Offline builder succeeded for the assigned TSX and HTML, including local Geist fonts and installed React/Animate UI controls.
- contrast.py: **158 pairs checked in light and dark, all pass** (bundled role sheet); actual runtime styles checked by audit below.
- Initial full audit: 400/400 planned combinations, 13,790 text measurements, 1,367 focus stops; PASS. Later refinements add stronger outline boundaries and interactive fixture fidelity; final-build evidence follows.
- Playwright behavior checks: named save; newly saved list entry; retained search typing focus; matching beyond the initial loaded page; pending→saving→saved; obsolete-save timer cancellation after a newer edit; conflict pause; kept/restorable local draft; foreign original copy permission; import success and invalid-data download action. All passed with **zero page errors and zero network requests**. This is mock interaction evidence, not server/storage proof.
- Final screenshots inspected in-memory: 1280 light list, 390 light Taller, 1280 dark Taller and 390 dark import. The broader audit supplies all declared combinations; screenshots are not separate permitted deliverables.
- Additional responsive/English probe: the first 320px run found the status icon offset misaligned with name/owner text. Phone row icons were removed while retaining the full text status. The repeated 24-render check at 320/768/1024px in both themes passed with zero contrast, non-text, padding, overflow or alignment findings. The repaired 320px dark English list was visually inspected.
- Direction evidence: compare_directions.py on A alone found every layout/navigation/type/motion selector, with no missing evidence. The three-direction comparison then passed all pairs: A/B layout similarity 0.131; A/C 0.114; B/C 0.156. Navigation remains shared, while measured composition and motion differ. This is a comparison of the rendered peer snapshots, not approval of those artifacts.
- **Final audit: 400 renders / 400 planned combinations, 14,022 text measurements, 1,360 focus stops; exit 0.**

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

The final post-rebuild three-direction comparison also returned exit 0, `ok=true`, `evidence_ok=true`, zero missing selectors and the same passing pair metrics. No production tests, build, backend authorization, storage or cross-browser persistence checks were executed; this delegation owns only the offline design artifacts.

## 12. Open questions, assumptions and concerns

Q: After “Ahora no”, should the legacy-import prompt be offered again on a later sign-in, and where can it be reopened? Owner/Planner decision; this exploration adds no permanent import route or unsolicited navigation entry.
Q: If the legacy scene lacks a usable name, should import request one or use the existing “Escena nueva” name? Owner/Planner decision; the valid import fixture already has an illustrative name and does not decide that fallback.

The existing scene-name input's 120-character maximum is reused as a draft assumption, pending alignment with the project-name input contract. New strings use Spanish-first grouped copy with illustrative English counterparts; implementation must place final new strings in textos-proyectos.ts. No new product permission is granted by an inspection selector.

All save/import/offline/server behaviors are in-memory simulations. No raw user scene is read, erased, uploaded or changed. The plan still requires owner selection and independent approval; this direction cannot authorize T4.1 or production implementation. The peer-direction comparison was run read-only after both peer JSON/HTML outputs became available; no peer artifact was edited. All three pairs passed, which establishes exploration distinctness, not owner approval or production acceptance.
