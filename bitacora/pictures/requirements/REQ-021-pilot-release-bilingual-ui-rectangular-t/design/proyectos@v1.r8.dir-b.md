---
name: Bastidor
status: draft
kind: independent-direction-exploration
contract: proyectos@v1
revision: r8.dir-b
subplan: SP-4
requirements: [R6, R7]
source_plan_revision: 1
approval: pending-owner-direction-choice
---

# Bastidor

A front-elevation frame for the installations a decorator wants to resume. The scene occupies the broad surface; its name, owner, last save and room dimensions answer which project this is. A thumbnail ribbon chooses the next installation. This is an independent draft exploration, not the approved contract or production Taller.

## Two thumbnail candidates, composed first

1. **Chosen: candidate 1** — `proyectos@v1.r8.dir-b.html.candidate-1.html`. Broad elevation, project caption beside it and an in-flow thumbnail ribbon. The main project is recognisable while its named action remains explicit. On phone these elements stack without requiring a gesture.
2. **Candidate 2** — `proyectos@v1.r8.dir-b.html.candidate-2.html`. Side index with a tilted freestanding stage. Rejected because its persistent vertical navigation repeats the Taller tool spine and devotes more phone space to navigation before showing the installation.

Both are original small HTML compositions. Neither copies a previous projects draft. The final entry was built after these thumbnails.

## Memorable move and why this is not a default gallery

The chosen installation enters the frame on a spring while the Backing, balloon cluster and table settle independently. Selecting another thumbnail remounts that project's stage; labelled arrows offer the same selection without dragging. Physical materials take colour while the rest of the interface stays neutral. Unlike a generic project-card grid, one installation has a broad physical elevation and a quiet working caption; the ribbon is a selector, not a grid of equal dashboards.

The shared identity is Pictures' existing tokens and product vocabulary. The look ledger was read across Cuentas r7 directions a/b/c and Taller esenciales r6 a/b/c. This direction keeps their physical materials but avoids their access pass, perforation, editorial register, bottom dock, vertical tool spine and horizontal inspector bench. A top masthead is deliberately shared orientation, while project selection is specific to this subplan.

## Eight axes

| Axis | Present in the mockup |
|---|---|
| concept | Bastidor: a saved installation is brought back onto its physical frame, with balloon clusters, Backing and a rectangular table. Projects are scenes to resume rather than dashboard statistics. |
| layout | A broad front-elevation stage and a narrower project caption form a 1.6:1 composition; a four-thumbnail ribbon sits below. Below 768px the stage, caption and two-column ribbon stack. Editor has a 280px summary; import uses a 1.3:1 consent spread. |
| navigation | Choose projects directly in the thumbnail ribbon or with labelled previous/next buttons; the selected title and Continue action stay beside the stage. The header returns to Projects. There is no sidebar, floating dock, drag dependency or tool-station rail. Native preview and language selectors remain visible. |
| typography | Shared system sans: 30px collection title, 34px light-weight selected project title, 24px editor title, 22px dialog title and 14–15px working text. Metadata is 12–13px. Project titles wrap freely on phone; no display face or decorative KPI numerals. |
| density | One selected project receives a 325px stage and 40px separation from its caption. Desktop structure uses 24px outer padding, phone 20px. Dialogs have 28/24px padding and controls are at least 44px tall. Four thumbnail objects form a compact ribbon rather than equal information cards. |
| components | Installed shadcn/Base UI Button, Input and Skeleton; shadcn Dialog/AlertDialog roots and titles with real Animate UI Portal/Backdrop/Popup composed locally to pass profile-aware enter/exit transitions. Custom SVG installation, stage, thumbnail ribbon, scene summary and native filters. No stand-in HTML fallback. |
| colour | Existing Pictures roles: light #faf9fc/#ffffff/#1c1425 and primary #6d3fe0; dark #0b0c10/#16181f/#f4f5f7 and primary #9479ff with #120b24 text. Controls use readable project text tokens #766c85/#8a91a0 as edges. Lavender/pink in the scene represent materials; green/amber/red carry written save/recovery status. |
| motion | Spatial spring brings the selected stage 39.6px sideways with -5deg perspective rotation and .98 scale in expressive mode; its rig registers 30px/3deg over 832ms, balloon cluster drops 24px/7deg over 936ms, and table settles 18px over 650ms. Ribbon enters with 45ms offsets and lifts 5px on hover. Controls use 200ms; dialogs use the profile ease (420/220/140ms). Reduced motion and still=1 remove travel and use zero-duration modal backdrop/popup transitions; CSS pauses on hidden tabs. |

## Behaviour retained from the shared r8 source

Sources: `proyectos@v1.r8.behavior.md`, SPEC US-3/R6/R7 and round 9, PLAN SP-4 and tasks T4.1–T4.9/T4.31. The exploration does not change those requirements.

- Own projects: `/proyectos`, name search over the whole authorised collection, followed by pagination. The fixture has 63 projects, 62 owned by Ana, and an Aurora match beyond the first 50 own records. The full fixture is filtered before the first four thumbnails are displayed; this demonstrates semantics, not a server implementation.
- Staff list: owner filtering appears only in the explicit staff view. Logged-in example remains Ana Morales throughout. Elena Ríos' original opens read-only. `taller.usar` controls owned-copy availability; the mock permission selector is explicitly labelled as an example.
- Named first save, later autosave and Save now: a new project opens an explicit name dialog; blank names fail validation. The simulated edit waits 500ms before saving and then acknowledges the submitted name. A ticket/project context guard prevents a stale simulated completion from updating a different view. Actual conditional revisions and server request ordering remain implementation obligations.
- A competing save pauses autosave and retains the local scene; the user may save an owned copy or confirm loading the server version. Confirmation says the draft remains local. No overwrite, delete, ownership transfer or version-history UI is introduced.
- Offline/error states never say saved. Navigation with pending/offline/conflicting work offers Save and leave, Keep draft and leave, or Cancel. Saving is disabled while disconnected, conflicted or already saving.
- Import names the current account, warns about shared devices, requires an explicit action and offers reversible Not now. Unknown legacy data can be downloaded; invalid/offline upload is disabled. The illustrative download is marked as mock data. A success acknowledgement leads to Taller. Original preservation and retry-safe deduplication are expressed in copy; no real localStorage, upload, database or migration runs here.
- Only name and complete scene travel between browsers. Conversation and generated AI images remain local; that boundary is visible in project, editor and import views.
- Proposed list route `/proyectos`, owner deep link `/3d?proyecto=<uuid>` and foreign read-only `/proyectos/[id]` remain PLAN destinations. This static exploration switches views without pretending to navigate or authenticate against production.

## Reachable views and states

Native `view`, `state`, `scene`, `theme` and `motion` selectors come from the real `mountMockup` runtime; labels remain Vista, Estado, Diálogo, Tema and Movimiento. `#language` switches product copy ES/EN. The Mockup label remains visible.

| View | Primary states and recovery |
|---|---|
| Mis proyectos | Normal, loading skeleton, empty collection/no search matches, load error with retry, offline/stale warning, failed next-page retry preserving loaded rows, saved success and access denial |
| Todos · equipo interno | Same collection states, authorised owner filter, foreign read-only open |
| Taller · guardado | Pending, saving, saved, offline, save error, conflict resolution, interrupted permission and named-save validation |
| Proyecto ajeno · lectura | Read-only scene, permission/loading/error fixtures and copy disabled without Taller permission |
| Importar del navegador | Explicit consent, browser-empty, loading, importing, incompatible data, interrupted response/retry explanation, offline, success and reversible refusal |

Global state options: `normal`, `loading`, `empty`, `error`, `pending`, `saving`, `offline`, `conflict`, `denied`, `invalid`, `page-error`, `success`. States apply where the view has that operation; irrelevant combinations preserve the view rather than inventing a conflict on a read-only record. Dialog options: first save, save copy, load server version and leave with changes. An owner-confirmed canonical contract should retain an applicability matrix rather than treat every Cartesian combination as a product flow.

## Reflow, accessibility and feedback addressed

- Desktop ≥1024px: 1.6:1 selected-project spread; four-column ribbon; 280px editor summary. Tablet 768–1023px: 1.2:1 spread, reduced gaps and 230px editor summary. Phone 360–767px: stage before caption, two thumbnails per row, single-column editor/import, wrapped heading actions and full-width dialog actions. Long Spanish and English copy can wrap.
- Outer padding is 24px on larger widths and 20px on phone. Scene caption has its own 24/20px inner edge. Footer stays inside the same workspace with the same outer x-axis; no detached centred footnote.
- Dialogs have 28px desktop/24px phone padding, a constrained viewport width, scrolling when necessary, real modal focus handling, a named title/description and explicit Cancel. Escape dismisses; focus returns to the invoking control. Loading uses a structural Skeleton, not a centred spinner.
- Text and native control edges use contrast-checked project roles; focus is a 3px accent outline offset by 4px. No native checkbox is introduced. Destructive/load-current decisions use the installed AlertDialog primitive. Statuses have written meanings and live/error roles.
- Preview drawings are inline SVG. No fonts, images, scripts or stylesheets are fetched; no package was installed. The installed real-component builder was available, so no fallback snippets or `inline.py` substitution was used.

## Verification and limits

- Offline real builder: PASS; final HTML 585,511 bytes, 2,135 bundled source files. React, styles and SVGs are inlined; no package installation or asset fetch.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass` (exit 0).
- Final `audit_mockup.py`: 320 renders / 320 combinations planned at 1280px and 390px, 7,252 text measurements and 873 keyboard focus stops (exit 0). No combinations were sampled away.
- `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- Focused browser click-through: `INTERACTION RESULT: PASS`; search beyond record 50, staff filtering/read-only/copy access, named save validation, simulated autosave, conflict dialog, offline guarded navigation, reversible import refusal/download, English controls and 360/390/768/1024/1280px reflow passed. No page errors or HTTP(S) requests.
- Motion follow-up: entrance and selected-project spring observed running; `still=1` and `rm=1` have no running animations after 130ms. Foreign read-error recovery hides scene content. Every JSON evidence selector matches a rendered element in its declared view; all motion selectors are present in the collection.
- Final HTML SHA-256: `bc66cbdd228286273d35a870c2fd7c16da745761aab96b0aa51702d3a2b40250`.

Rendered review covers collection at 1280/390 in both themes, phone conflict and desktop dark named-save dialog. Extra interaction checks cover the complete search fixture, staff owner filter, read-only copy permission, explicit first save, validation, 500ms simulated autosave, conflict confirmation, reduced-motion Escape dismissal/focus return, offline navigation, import refusal/download, English controls and reflow at 360/390/768/1024/1280px. No browser page errors or HTTP(S) requests were observed in that click-through.

One click-through initially found a 400ms backdrop exit under reduced motion in the stock component composition. The exploration now composes the installed Animate UI Portal/Backdrop/Popup directly with profile transitions and zero durations when reduced. The repeated focused interaction test passed, including no running animation 120ms after Escape. This is a local composition; installed libraries were not changed.

The mockup demonstrates presentation and bounded local interactions. Real account isolation, scene validation, conditional revision writes, durable draft recovery, raw-byte preservation, import idempotency, account-switch isolation and pagination request ordering require T4.2–T4.7 tests in the implementation. No product tests, production build, deployment or database checks were run by this design task.

## Open questions and assumptions

Q: Should project selection show a preview derived from the saved scene, or a neutral illustration until opening the project? The drawings here are illustrative; generation/storage of preview assets is not established by the current PLAN. Owner/Planner should settle this before finalisation without changing scene preservation or permissions.

Confirmed: first explicit named save then autosave, name plus complete scene only, foreign read-only originals and owned copies with Taller permission, reversible consent-based import, full-collection search, and no delete/transfer/history are already settled. They are not reopened as questions.

Assumption for the exploration: sample people, project titles, timestamps, room sizes and drawings are fictional. Selection previews may be a neutral schematic if actual scene previews would expand the implementation scope.

## Impact and approval

This writes only the r8.dir-b exploration files and its delegated result report. It does not modify `proyectos@v1.md`, `proyectos@v1.html`, history, SPEC, PLAN, production code or any other direction.

If chosen and finalised, T4.1 copies the approved canonical artifact; T4.4 consumes collection/save/read-only/conflict views; T4.5 consumes import states; T4.6/T4.7 verify the real flows; T4.8 reviews rendered fidelity; T4.9 independently audits isolation and preservation. Compatibility is **undetermined until owner choice and canonical finalisation**. No implementation is authorised to consume this draft.
