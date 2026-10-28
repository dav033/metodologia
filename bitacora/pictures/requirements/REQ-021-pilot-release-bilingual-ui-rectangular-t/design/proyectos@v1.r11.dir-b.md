---
contract: proyectos
version: 1
status: draft
artifact: direction-exploration
subplan: SP-4
requirements: [R6, R7]
owner: David
author: Designer
date: 2026-10-28
direction: b
name: Mesa de escenas
revision: r11
source_behavior: proyectos@v1.r11.behavior.md
source: proyectos@v1.r11.dir-b.tsx
mockup: proyectos@v1.r11.dir-b.html
chosen_thumbnail: proyectos@v1.r11.dir-b.html.candidate-1.html
---

# Mesa de escenas — direction B / r11

## 1. Identity and traceability

**Draft exploration, not approved and not the canonical proyectos@v1 contract.** Only the assigned r11/B artifacts are written. The owner chooses a direction; a separate finalizer produces the canonical contract. No repository, plan, sibling contract, shared history or project-memory file is changed.

Scope: `proyectos@v1.r11.behavior.md`, read first; SPEC's “Behavior — SP-3 and SP-4 (round 9 answered)” and SP-4 in PLAN.json. R6 maps to project list/open/save/read-only/conflict; R7 maps to explicit legacy import/refusal/recovery. Affected proposed consumers: T4.1 design copy, T4.4 project list and Taller saving, T4.5 import, T4.8 visual review. Engineering-only tasks remain outside this exploration.

Existing product sources inspected read-only in t12 and asesor: `src/app/globals.css`, `src/app/3d/page.tsx`, `src/components/tres-d/Taller3D.tsx`, `guardado-escena.ts`, `ia/PestanasLaterales.tsx`, `src/components/ui/shell/CabeceraApp.tsx` and `MenuApp.tsx`. The prescribed source excerpt establishes separate conversation/image storage. Current canonical `cuentas-admin@v1.md/.html` and `planes@v1.md/.html`, plus their selected-source TSX, establish the sibling shell, typography, shape roles and accessible control edges. The HTMLs were read as bundled artifacts rather than treated as new production behavior.

The latest brief fixes palette, fonts, shell and component vocabulary. It therefore governs over historical feedback requesting independent palettes/typefaces. This direction spends its variation on the changed area's arrangement, density, local navigation and spatial motion. It uses real installed libraries rather than the older HTML stand-in fallback.

Compatibility: an alternative draft with a different list composition, **breaking relative to a differently arranged list implementation**; no approved version is superseded. Required action remains owner selection and subsequent exact-plan approval, followed by implementation and independent review. This note grants neither.

## 2. Purpose and users

The owner finds and reopens a named scene, then continues in Taller with truthful account-save status. Authorized staff search across accounts and open foreign originals read-only. A person signing in with a legacy browser scene decides whether it belongs in the current account. Success is a complete reopened scene or a confirmed save/import, with unsent work and raw source preserved on failure.

Only name and complete scene travel between browsers. Conversation and generated images stay in their browser. No deletion, transfer or version-history surface is introduced.

## 3. Approach, composition and hierarchy

The existing account/application shell surrounds **one working sheet**: compact project index on the left, selected-scene canvas in the centre and project identity/owner/action on the right. Selection inspects; **Abrir proyecto** explicitly enters the Taller. The local preview is derived from the complete saved scene, not a stored screenshot, media-sync feature or separate editable canvas.

This makes the scene the principal content, unlike a thumbnail-card gallery or a full-width editorial register. Search and owner selection stay with the records they filter. Owner and read-only meaning sit beside the action that opens the project. No decorative counters, dates or marketing copy are added; the small record count derives from the same neutral fixture.

Two thumbnails were drawn before the full TSX:

- **Candidate 1, selected:** index / scene / inspector. Continuous spatial context and a clear explicit open action; it accommodates both owned and foreign projects without introducing a gallery.
- Candidate 2: scene with a bottom horizontal strip and side detail. It competes with Taller's existing lower phone sheet and provides less room for search/owner filters. It remains a thumbnail for comparison, not another implemented direction.

The central SVG is an illustrative mock scene, not a functioning 3D renderer. Production must derive its preview from the selected authorized scene without promising cloud image storage.

## 4. Fixed design system and eight axes

| Axis | Rendered evidence and approach |
|---|---|
| Concept | A scene workbench for reopening saved work: a persistent project index, derived scene view and selected-project inspector inside the established Pictures shell. |
| Layout | One continuous sheet with 276px / flexible / 238px columns; tablet keeps the index beside a stacked scene/detail area; phone stacks index, scene and detail. |
| Navigation | Shared horizontal Taller 3D / Proyectos guardados routes; local pressed-state project selection followed by explicit Open project; phone anchors connect project list and scene preview. |
| Typography | Existing local Geist Sans and Geist Mono; 24px page title, 20px inspector, 16px index heading, 14–15px body and 12–13px metadata. No new family. |
| Density | Compact divided project records beside a dominant scene and a sparse reading inspector. Existing 32px sheet, 18px field and pill control shapes; 24px desktop and 20px phone insets. |
| Components | Installed shadcn/Base UI Button and Input, Skeleton and Animate UI Dialog; native selects/account disclosure, semantic project rows and a local illustrative scene SVG. |
| Colour | Exact Pictures background/surface/text/accent and semantic state tokens; workshop-visor surface for the scene. Control edges use the sibling texto-tenue alias. No new palette. |
| Motion | Spatial indexHinge 620ms cubic-bezier(.22,.85,.3,1.08), lateral inspectorDock, 775ms sceneDolly, 65ms rowDepth stagger, statusRegister, shared spring marker and 180ms hover/press. Natural/subtle scale timing; Quieto/still/reduce eliminate movement. |

Shared shell: Pictures ring-and-dot mark, Sempertex wordmark separator, language select, named account disclosure, horizontal route rule, 24px title and aligned footer. It follows the chosen/finalised sibling vocabulary; it does not import their account forms or plan comparison layout.

| Production source token | Kit role / usage | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--superficie-2` | muted, secondary, selected row | #efe9f8 / #242733 |
| `--texto` | foregrounds | #1c1425 / #f4f5f7 |
| `--texto-suave` | supporting text | #6b6178 / #9aa1ad |
| `--texto-tenue` | input/control edge, inherited sibling alias | #766c85 / #8a91a0 |
| `--acento` / `--sobre-acento` | primary/ring and primary text | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| `--acento-hover` | primary hover | #5530b8 / #a58dff |
| `--borde` / `--borde-suave` | decorative frames/rules | #e3daef / #efe9f8; #383c48 / #2a2d38 |
| `--taller-visor` | scene canvas | #ebe7f1 / #1a1722 |
| `--taller-barra` / `--taller-panel` | existing Taller chrome | #ffffff / #faf9fc; #121018 / #16131d |
| `--exito` / `--exito-suave` | confirmed success | #1f7a55 / #dcf5e9; #78d6a8 / #173b31 |
| `--aviso` / `--aviso-suave` | pending/offline | #8f5f12 / #fff3d8; #f7c46b / #3f311c |
| `--error` / `--error-suave` | conflict/error | #b23a45 / #ffeaec; #ff979f / #43252a |

Geist and Geist Mono are embedded from existing local Next WOFF2 assets; no network font or installation. Body is 15px/1.5; project rows 14px, supporting labels 12–13px, headings 16/20/24px. Mono is confined to count/wordmark metadata. Panels/fields/pills reuse the siblings' 32/24/18/999px roles. Framed group insets are 24px desktop, 20px phone; dialogs are 28px desktop, 24px phone. Decorative borders do not substitute for visible control edges.

Real component provenance, using `real/manifest.json`:

| Source:id / variants / states | Actual import or custom composition |
|---|---|
| `shadcn:button default/outline/ghost ready/hover/focus/pressed/disabled` | `@/components/ui/button`, Base UI; Action forwards explicit data-variant for the project mapping |
| `shadcn:input text empty/filled/invalid/focus` | `@/components/ui/input` |
| `shadcn:skeleton project/scene loading` | `@/components/ui/skeleton` |
| `shadcn:dialog save/copy/rename/new/leave/load open/closed` | `@/components/ui/dialog`, installed Animate UI/Base UI enhancement |
| `custom:project-index selection/filter/pagination` | semantic aside, native labelled owner select, pressed-state row buttons |
| `custom:scene-preview illustrative normal/empty` | local SVG and figure, not a third-party 3D-component claim |
| `custom:account-disclosure closed/open` | native details/summary retained from sibling shell, Escape returns focus |
| `custom:local-navigation route/fragment` | semantic anchors; phone anchors focus the target without losing selection |
| `custom:selection-marker selected` | `motion.span` from `motion/react`; profile from `@kit/motion` |
| `custom:planning-controls view/state/scene/theme/motion` | `mountMockup/useMockup` from `@kit/mockup` |

## 5. Navigation and motion detail

Entry: account product navigation → `/proyectos`; selected project → `/proyectos/[id]` / Taller context. The planning artifact uses local view switches instead of network routing. The import view represents the first authenticated Taller visit, not a new public route. Account links resolve to the sibling local mockups; sign-out is explicitly simulated.

Desktop index selection updates the derived scene and owner inspector without entering edit mode. On phone, “Lista de proyectos” and “Vista previa” anchors connect the stacked parts; keyboard activation focuses the named destination. The inspector keeps the sole primary **Abrir proyecto** action. Taller retains its scene-name/status header, undo/redo/photo/shopping controls, 60px tool rail, scene and Pieza/IA panel context. Existing editor controls are contextual stand-ins; their production behavior is not redesigned.

Distinct animated behaviors:

1. `.project-index`: finite perspective hinge, x=-16px / rotateY(9deg), slight overshoot, settles at 620ms.
2. `.project-row`: rowDepth registration, x=-8px with 65ms stagger; always full text opacity.
3. `.scene-art`: 775ms camera-like dolly from scale(.94)/y=12px with a small settling overshoot.
4. `.project-inspector` and `.import-panel`: 620ms right dock from x=32px, then x=-3px, then rest.
5. `.selection-pin`: shared layout spring between selected records, expressive stiffness 220 / damping 16 / mass .9.
6. `.status` / `.status-line`: scaleX(.8) registration on state change; the status text stays readable.
7. `.project-row` hover shifts 4px; Buttons lift -2px, compress to .975 on press and move their inline icon 2px. Focus has an immediate 3px ring.
8. Loading skeleton group uses a 3px scan instead of opacity flashing; modal opening uses installed Animate UI behavior.

The spatial CSS easing is `cubic-bezier(.22,.85,.3,1.08)`, intentionally separate from the siblings' access-register or comparison-sheet grammar. Natural uses 360/140/35ms and subtle 180/100/15ms for settle/quick/stagger. Default is expressive. Reduced motion, `?still=1` and Quieto remove travel/transitions, including pseudo-elements; content, focus and feedback remain. Hidden-tab CSS animation pauses. There is no heavy continuous ambient effect; other entrances are finite.

## 6. Flows and preservation rules

1. **First save:** work in an unsaved scene → Guardar proyecto → labelled name dialog → validate nonblank name → confirm → account-confirmed saved status. Only then may later edits autosave. The existing name input's 120-character constraint is retained. Cancelling a name dialog leaves the visible name unchanged.
2. **Later save:** change scene → Guardando… → Guardado en tu cuenta only for the latest acknowledged revision. Guardar ahora remains available. Obsolete responses may never confirm newer pending work.
3. **New scene/template/library:** save pending edits of the open named project first; if that cannot finish, retain the current scene and explain recovery. A never-saved scene asks whether to save, continue without saving, or cancel. All three entrances then create an unlinked **Escena nueva / Sin guardar**; no server write until its first named save.
4. **List/reopen:** authorized server search and owner filters apply before pagination. Filter changes reset pagination. Keep current results on next-page failure and retry that page. Ignore stale query responses. Open the complete scene with its saved name.
5. **Conflict:** stop autosaving, keep the local draft, show the conflict beside the visible scene. Offer Cargar versión del servidor with explicit confirmation or Guardar copia into the current account. Loading the server retains a visible Guardar borrador como copia recovery for the preserved local draft. Neither choice silently overwrites the foreign/competing original.
6. **Offline/error:** continue local work, show not-saved state, keep pending changes and offer retry. New-scene replacement is blocked while the current named project's pending work cannot be saved. Local simulated edits retain the offline/conflict label instead of manufacturing success.
7. **Foreign read:** show owner and Solo lectura; no editable original-name or scene controls. Only taller.usar permits Guardar copia. Permission-denied list views reveal no project content. Permission checks remain server-owned.
8. **Legacy import:** current account identity precedes explicit import/refuse actions. Success creates one owned project, even after retry; refusal/error/invalid input leave raw local data unchanged. Invalid data explains its format failure, offers Descargar original and lets the person continue without import. Only name/scene import; conversation/images stay local.

## 7. View specifications

| Native `view` | Structure and primary action |
|---|---|
| `list` | Shared shell → project heading/route rule → labelled mock-data note → project index / selected scene / owner inspector → Abrir proyecto |
| `staff` | Same sheet; Cuenta propietaria filter appears above rows and spans authorized owners. Foreign selection identifies Solo lectura before opening. |
| `taller` | Existing Taller context with inline scene name and save status; explicit Guardar proyecto/Guardar ahora; conflict/offline recovery sits above the scene without replacing it. |
| `foreign` | Taller scene readable; owner banner and Solo lectura; original name/edit controls disabled; Guardar copia requires Taller permission. |
| `import` | First-visit prompt in Taller context: browser scene preview / current-account import decision, preservation explanation, success/refusal/error recovery. |

Neutral mock data uses only “Escena de ejemplo” with ordinal suffixes, Cuenta Master Designer / Cuenta de ejemplo, and `master@prueba.local` / `admin@prueba.local` inherited test vocabulary. No dates, customer claims, real identities or screenshots are fabricated. The illustration's balloons are scene content, not a new visual identity.

## 8. Declared states and switches

The visible native state selector reaches every state below. Irrelevant cross-products retain that view's base state; the following mapping defines the meaningful scenarios. Dialogs are independently reachable through native `scene` and through actual actions.

| `state` | Applicable view / expected recovery |
|---|---|
| `normal` | All views; ordinary ready fixture |
| `loading` | List/staff skeleton rows and preview; import source loading; no fake saved data |
| `empty` | List/staff: explanation and Ir al Taller 3D |
| `no-match` | List/staff: no authorized matches; Limpiar filtros |
| `next-page` | List/staff: second fixture page loaded |
| `page-error` | List/staff: earlier rows retained; Reintentar página |
| `saving` | Taller header Guardando…; import Importando… with submission disabled |
| `saved` | Taller header Guardado en tu cuenta |
| `unsaved` | Taller Escena nueva / Sin guardar; first save asks name |
| `offline` | Taller changes pending with retry; import preserves source on failure |
| `error` | List retry / Taller save retry / import retry, scoped to active view |
| `conflict` | Taller stops autosave; server-version or owned-copy recovery |
| `invalid` | Import format failure with original download; named-save dialog validation |
| `imported` | Import confirmation and Abrir proyecto |
| `forbidden` | List/staff refusal with no restricted metadata; foreign copy disabled without Taller permission |

Native dialogs: none, first save, owned copy, start another scene, load server version, leave an unsaved scene and rename. The first-save form's validation is triggered by submitting an empty name. Closed dialogs are absent/inert; focus returns to the originating control. Permanent delete/transfer/history controls are inapplicable and absent.

## 9. Responsive behavior

- **1100px and wider:** three-column sheet (276px / flexible / 238px), 40px outer gutters. Taller retains rail / scene / side panel. Record list and open action share one viewport at 1280px.
- **640–1099px:** 24px gutters, 240px index beside the scene; inspector moves below the scene in the same second column. Owner/name facts use two columns. Taller side panel moves below its scene, preserving DOM order. Import remains two columns with flexible text wrapping.
- **320–639px:** 20px outer gutters and insets. Index → preview → inspector form one stacked sheet. Phone anchors connect the list and preview; controls wrap and primary action fills the available width. Import stacks preview then decision, and dialogs use a viewport-bounded scroll region. Header wraps brand and account/language controls onto aligned rows. No horizontal page scrolling.

Spanish is initial. The retained language control demonstrates translated labels and longer English strings; implementation centralizes all new copy in `src/components/proyectos/textos-proyectos.ts`. No locale persistence is newly claimed.

## 10. Accessibility targets and evidence limits

Target WCAG 2.2 AA, subject to independent implementation review. Semantic headings/regions, associated input/select labels, SVG alternative descriptions, named icon controls, 44px controls, 3px visible focus, keyboard route/fragment navigation, pressed-state project selection, modal trapping/Escape/focus return, polite save status and explicit validation/recovery are required. Text ≥4.5:1 and meaningful control edges/focus ≥3:1 in both themes, including mid-animation; entrance text uses no opacity fade.

The static fixture never reads or writes actual localStorage, IndexedDB, cookies, sessions or server projects. It cannot prove server authorization, atomic revision control, source-hash deduplication, cross-browser completeness, durable local draft retention, deletion races, stale network-response rejection or assistive-technology conformance. Those remain production verification work. First save is an immediate fixture action; saving/offline/conflict are explicitly demonstrated by the state inspector and simulated later edits. Production must also disable pending first-save submissions and show its real server pending/result state.

The Taller's pre-existing photo/shopping/history controls and Pieza/IA context are visual stand-ins, labelled as outside the changed interaction; this exploration does not implement editor tooling. There is no package installation, network fetch, fallback HTML kit substitution or separate preview directory.

## 11. Observable visual acceptance criteria

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-AC-01 | 1280px | list normal | The shared masthead and route rule precede one continuous three-column project sheet. |
| B-AC-02 | 1280px | list normal | The scene occupies the central flexible column; the explicit Open project action is in the right inspector. |
| B-AC-03 | 768/1024px | list normal | Index stays left, inspector appears below the scene, with no horizontal page scroll. |
| B-AC-04 | 320/390px | list normal | Index, preview and inspector stack; phone anchors target the list/preview and set keyboard focus. |
| B-AC-05 | All supported | list/staff filtering | Search/filter changes restart pagination and the preview belongs to a matching authorized project. |
| B-AC-06 | All supported | list loading | Labelled skeletons replace rows and selected-scene content. |
| B-AC-07 | All supported | list empty/no-match/error | Each state gives the appropriate create, clear-filter or retry recovery. |
| B-AC-08 | All supported | page-error | Existing records remain visible above Retry page. |
| B-AC-09 | All supported | taller unsaved | Header reads Escena nueva / Sin guardar and Save project opens the name dialog. |
| B-AC-10 | All supported | first-save invalid | Empty submission exposes an associated name error without closing the dialog. |
| B-AC-11 | All supported | rename cancel | The previous scene name remains visible and focus returns to the name control. |
| B-AC-12 | All supported | saving/saved | The header distinguishes Guardando… from Guardado en tu cuenta. |
| B-AC-13 | All supported | offline | Local changes remain visibly pending; retry and new-scene safety retain the current scene. |
| B-AC-14 | All supported | conflict | Local scene remains visible beneath recovery; no autosave success replaces the conflict. |
| B-AC-15 | All supported | server-version recovery | Loading the server leaves a visible Save local draft as copy action. |
| B-AC-16 | All supported | foreign | Owner/read-only banner is visible; scene/name edits are disabled and copy is permission-dependent. |
| B-AC-17 | All supported | import normal | Current destination account is visible before Import/Do not import controls. |
| B-AC-18 | All supported | import refusal/error | Preservation copy appears and refusal allows continuing to Taller. |
| B-AC-19 | All supported | import invalid | Invalid source explanation, Download original and Continue without importing are present. |
| B-AC-20 | All supported | import completed | Success replaces import submission and offers Open project. |
| B-AC-21 | All supported | modal open | Tab remains inside the dialog; Escape cancels and restores focus. |
| B-AC-22 | 390/1280px | light/dark | Source tokens, embedded Geist and accessible control edges match the sibling vocabulary. |
| B-AC-23 | 1280px | expressive initial | Index hinge, row registration, scene dolly, inspector docking and status registration visibly animate. |
| B-AC-24 | All supported | Quieto/still/reduce | No active entrance/travel remains; data, selected project and recoveries remain visible. |
| B-AC-25 | All supported | new/template/library | Never-saved scene confirms before replacement; next scene starts unlinked and not saved. |

### Actual verification

- Offline real-component builder: PASS; final source bundles 2,126 source files into one approximately 646KB HTML with inline assets. No fetch/install/fallback.
- `contrast.py`: **158 pairs checked in light and dark, all pass**, exit 0.
- First complete audit: 630 renders at 1280/390/768; PASS. Subsequent four-width audit: 840 renders, 28,136 text measurements and 1,517 focus stops; PASS. The final fixture then enabled local simulated edits while offline/conflicted without confirming a save; a fresh final audit is recorded below.
- Supplemental cached Playwright: **18 groups PASS**, covering pagination, match beyond first fixture page, owner filtering, foreign read-only/no-copy permission, first save/validation, rename cancellation/focus, autosave, retained-conflict copy, offline replacement/retry, all three new-scene entrances, refusal/continuation, import success, invalid-data download and modal trapping. Responsive samples cover ES/EN at 320/390/640/768/1024/1280 in both themes with no page overflow. No page errors or HTTP requests were observed. A first immediate Tab assertion observed Base UI's intermediate focus sentinel; a diagnostic probe and rerun waiting 40ms for its focus-manager microtask confirmed the 12-stop trap. No production check was weakened.
- Screenshots inspected in memory, without writing extra files: list at 1280 light and 390 dark; Taller conflict at 1280 dark; invalid import at 390 light. Common axes, generous insets and readable controls are retained. Extra final light-phone/dark-desktop list inspection is recorded in the session.
- Selector evidence: `compare_directions.py` with B alone passed (`ok=true`, `evidence_ok=true`, no missing evidence); this proves B's claims, not pairwise distinctness. Three-direction comparison initially could not run because sibling JSON metadata was not yet available. Final comparison status is recorded below.

Final rebuilt-artifact audit, `--widths 1280,390,768,1024 --max-combos 240`: **840 renders (840 combinations planned), 28,152 text measurements, 1,530 focus stops**, exit 0; no sampling warning.

**RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**

Supplement after the final local-edit change: **5 further checks PASS** — offline editing stays unsaved, conflict editing stays unsaved, expressive mode has live effects, `?still=1` has zero running effects, and OS reduced-motion has zero running effects. These supplement the earlier 18 interaction groups; they do not establish server behavior.

Final HTML SHA-256: `fdb6dbc9425219ea4658ed0c352d85851ba235a75d111855352514bfca564b77`.
Final three-direction `compare_directions.py A.html B.html C.html --json`: **PASS**, exit 0, `ok=true`, `evidence_ok=true`, no missing selector evidence. All pairs pass: A/B layout similarity **0.131**, B/C **0.156**, A/C **0.114**. B differs in actual motion from both peers; B/C also differ in density. Shared route navigation remains intentionally consistent with the product shell. Sibling files were read only, not changed.

## 12. Open questions, assumptions and concerns

**Open owner questions: none introduced.** First-save/autosave policy, complete scene content, staff copy rights, new-scene semantics and whole-collection filtering are already settled in the supplied brief/SPEC. Direction choice and independent plan approval remain outstanding and are not granted by this exploration.

Assumptions for this candidate: a selected scene can be rendered read-only from its authorized document; no additional cloud image is needed. Preview layout and the phone's fragment navigation are proposed direction-specific arrangements awaiting owner choice. Example names, identity and illustration are fixture-only; the full scene's actual dimensions, references and colors remain the persisted source of truth. The immediate local submit and downloaded fixture data do not establish live server behavior or actual raw browser import fidelity.

**CONCERNS:** Draft remains unapproved; backend/real editor/assistive technology are unverified. Final audit/comparison evidence above must be read with those limits. Canonical contract/HTML, SPEC, PLAN, production repositories and other directions are untouched.
