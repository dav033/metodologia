---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
designer: Codex
date: 2026-10-26
---

# proyectos@v1 — Saved projects

## 1. Identity and traceability

Planning draft for REQ-021 / M2 / SP-4, covering R6, R7 and US-3. **Not approved for implementation.** The owner approves this draft with the plan; the Designer grants no approval. This is the first version, with no approved predecessor; this revision preserves the existing planning draft and the accepted round 9 answers. This revision addresses the owner’s 2026-10-26 19:36 visual-redesign request: rebuild the visual layer using mockup-craft.md in full while retaining the agreed behavior, views, states and criteria. The earlier pending-save and dialog-focus corrections remain in place. SP-2 remains the planning focus: this work neither confirms SP-4 nor changes plan approval. The companion `proyectos@v1.html` is a self-contained planning mockup, not `design/preview/` or a product implementation. No network requests, external fonts or images, backend or real customer data are used.

Source snapshot read on 2026-10-26:

| Input | Revision / SHA-256 |
|---|---|
| SPEC.md, status ready | `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4` |
| PLAN.md, status draft | `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3` |
| PLAN.json, schema 1.3.0, revision 1 | `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8` |

Exact consumer: SP-4 `ui.contract=proyectos`, `ui.version=1`, `design_task=T4.1`, `visual_review_task=T4.8`. UI consumers: **T4.4** (V1–V4, D1–D3, saving and local drafts) and **T4.5** (V5 import). T4.2/T4.3 own versioned project-document@1, validation, authorization, durable mutation/import receipts and paginated APIs; T4.31 is the required storage checkpoint before UI work. T4.6/T4.7 exercise real cross-browser integration, T4.8 independently reviews visual fidelity and T4.9 audits spec/standards. These tasks remain draft; round 9 behavior is settled, while design/subplan approval remains pending. SP-1 owns authentication and permission semantics; SP-2 owns the shared account menu. SP-6/SP-12 consume project identity, not this UI contract automatically. SP-8/SP-10 own language rollout. SP-5's library remains separate. SP-13 consumes the accepted saved-work release flow.

Version record, embedded because this delegation permits only the two named design files: **2026-10-26, owner feedback 19:36 — full visual-layer rebuild**. Compatibility: **compatible visual change** against this unapproved draft: V1–V5/V4b and D1–D3 retain their content, destinations, permissions, interaction model, state vocabulary and breakpoint structure. Neutral shell/navigation, flat ruled notices and import/conflict groups, compact sentence-case typography, consistent inline SVG, and right-aligned tabular save figures replace the earlier tinted chrome, uppercase eyebrows, nested cards and decorative empty-state glyph. Existing semantic palette remains unchanged. Affected consumers: SP-4 T4.4 (V1–V4b/D1–D3), T4.5 (V5), and independent T4.8 rendered review; T4.1 copies this exact draft after owner approval. No API/storage change or new dependency is implied for T4.2/T4.3; T4.6/T4.7 still own real runtime evidence. No approved implementation is claimed compatible without T4.8 review. Required action: owner approval together with the plan, then implementation/rendered review. Earlier revision record retained: current inspection revision — no product behavior or layout change; the mockup now applies the existing dirty/pending/unknown departure guard to “Nuevo proyecto” and keeps the originating focus target across D2 → D1/D3, with an in-context fallback if that target no longer exists. D3 now displays its existing pending/unknown/offline reason beside the disabled save-and-continue action. Compatibility: **compatible correction against this same draft contract**; affected UI consumer T4.4, F4 and D1–D3. T4.8 must verify both behaviors in production implementation. Markdown table continuity is repaired for all states and visual criteria. Previous draft revision record follows unchanged: 2026-10-26 — preserve the initial draft and static mockup; revise after 18:53 owner/Planner feedback. Compatibility: **breaking behavior relative to the prior planning mockup** for V1/V2 search/pagination, now modeled across more than 50 fixtures with normalized query boundaries, filter reset, late-response rejection and next-page recovery. Resolving provisional save/content/copy copy preserves the intended V3–V5/D1–D3 design. **Undetermined** against production: server persistence is new; no approved consumer exists to migrate. Exact affected consumers: SP-4 T4.4 (V1/V2 queries, V3/V4 save/copy states and D1), T4.5 (V5 complete-scene import explanation), T4.6/T4.7 (integration evidence) and T4.8 (rendered review); T4.2/T4.3 supply the settled document/query contracts. Shared tokens, breakpoints and unaffected layouts remain unchanged. Required action: owner approval of this draft with the plan, T4.1 byte-identical copy, then implementation and independent T4.8 review of full-staff and read-only custom-role variants. No separate CHANGELOG or PLAN edits are authorized in this delegation; this record carries the required draft impact assessment. Do not promote this draft to approved.

## 2. Purpose and users

| View | User / goal | Observable success |
|---|---|---|
| V1 My projects | A signed-in account with own-project access finds saved work | Opens the chosen server project and continues the same scene on another browser |
| V2 All projects | An employee/admin, or custom role with the corresponding permission, finds another account's project | Owner is explicit in every row/card and the selected project opens without changing its owner |
| V3 Own project in Taller | An authorized owner saves and continues work | Server acknowledgment identifies the saved project and time; failure never appears as saved |
| V4 Another owner's project, read-only | Authorized staff inspect saved work | Owner and viewing mode remain visible; foreign original remains read-only and a personal copy requires `taller.usar` |
| V5 Browser import review | A signed-in person decides whether a local scene belongs to them | Explicit import creates an account-owned server project; original browser data survives every outcome |

Each screen has one question and one main job; these decisions drive its largest block and primary action:

| Screen | One question | Main job / visual answer |
|---|---|---|
| V1 | “Which decoration project do I want to continue?” | Find and open a saved scene from the project grid; “Nuevo proyecto” is the single colored action. |
| V2 | “Whose project am I looking for?” | Search/filter authorized projects with the owner visible on each peer card. |
| V3 | “Are my scene changes saved in my account?” | Continue the scene with a persistent truthful save status beside its save action. |
| V4 / V4b | “Whose scene is this, and what can I do with it?” | Inspect the original read-only; only eligible accounts can create a personal copy. |
| V5 | “Is this browser scene mine, and which account will receive it?” | Review source and destination, then explicitly consent to import. |
| D1 | “What will this project be called in my account?” | Name and save it, with the destination account visible. |
| D2 | “How do I preserve my work when another version was saved?” | Compare two plainly labelled version rows and choose a safe resolution. |
| D3 | “How can I leave without losing these changes?” | Save, keep an account-scoped local draft, or stay; disabled choices explain why. |

V4b is the same read-only project view for a custom role with `proyectos.ver_todos` but without `taller.usar`: no Taller navigation, own-project actions or copy action.

R6 maps to V1–V4 (including V4b), F1–F4 and UI-AC-01–15. R7 maps to V1/V5, F5 and UI-AC-16–19. Concurrency maps to D2/F3; permission changes to S8/F4. Names, account names and dates in the mockup are fictional fixtures.

## 3. Information architecture and hierarchy

Project library: shared Pictures shell → section navigation → title and one primary action (“Nuevo proyecto”) → optional browser-import notice → name search (and owner filter in V2) → result count/order → projects. Each project shows a nonessential scene illustration, name, last server-save time, owner in V2, and “Abrir proyecto”. Most recent save first (`updatedAt DESC`, then `id DESC`); no unsupported business metrics or prices. A missing thumbnail uses a neutral scene placeholder; it never blocks opening. No thumbnail-generation AI is implied.

Taller: back to library → project name and owner/mode → truthful save status → “Guardar proyecto” / “Guardar ahora” → existing workspace. Keep scene objects, dimensions and placement as the work, not an extra project dashboard. “Guardar decoración” belongs to SP-5 and must remain distinctly labelled; it cannot serve as the project-save action. Project metadata stays outside the 3D canvas and is available to assistive technology.

Import review: provenance (“Solo en este navegador”) → destination signed-in account → local scene name and validation result → explicit ownership checkbox → import action → result and recovery. Never suggest that a scene on a shared browser necessarily belongs to the current account.

No deletion, sharing, folders, collaboration, project history browser, global publication or bulk actions are introduced. Existing in-scene name editing remains; no separate rename flow is added.

## 4. Design system and visual language

Read-only evidence: `t12` HEAD `fb872bce` and `pictures`/asesor HEAD `fa101a47`, `src/app/globals.css`, `src/app/layout.tsx`, `src/components/tres-d/{Taller3D.tsx,ui-taller.ts,DialogoTaller.tsx,guardado-escena.ts,archivo-escena.ts}` and shared `src/components/ui/shell/CabeceraApp.tsx`. Both repositories use the same semantic palette. Existing product design takes precedence over desktop preferences. The accounts draft `cuentas-admin@v1` is a consistency reference, not an approved dependency.

| Existing token | Light | Dark | Role |
|---|---|---|---|
| `--fondo`, `--superficie` | #faf9fc / #ffffff | #0b0c10 / #16181f | canvas, panels |
| `--superficie-suave`, `--superficie-2` | #faf8fd / #efe9f8 | #1c1e26 / #242733 | inset areas, secondary fill |
| `--texto`, `--texto-suave`, `--texto-tenue` | #1c1425 / #6b6178 / #766c85 | #f4f5f7 / #9aa1ad / #8a91a0 | text hierarchy |
| `--borde`, `--borde-suave` | #e3daef / #efe9f8 | #383c48 / #2a2d38 | panel borders, dividers |
| `--acento`, `--acento-hover`, `--acento-suave` | #6d3fe0 / #5530b8 / #ece3fb | #9479ff / #a58dff / #241f3d | actions, hover, selection |
| `--sobre-acento` | #ffffff | #120b24 | text on primary; do not use white in dark library buttons |
| `--exito`, `--exito-suave` | #1f7a55 / #dcf5e9 | #78d6a8 / #173b31 | acknowledged save/import |
| `--error`, `--error-suave` | #b23a45 / #ffeaec | #ff979f / #43252a | error |
| `--aviso`, `--aviso-suave` | #8f5f12 / #fff3d8 | #f7c46b / #3f311c | unsaved, offline, conflict |
| `--overlay` | rgb(28 20 37 / .4) | rgb(0 0 0 / .6) | modal backdrop |

Inside the real `.taller-3d`, keep `--taller-*` scoped equivalents and `BTN`/`BTN_PRI`/`BTN_ICO`, including their existing dark primary with white text. The standalone shell uses the generic tokens above, without mixing a generic dark accent with white button text. Preserve native `DialogoTaller` focus/modal behavior. Reuse `.ui-button-primary`, `.ui-button-secondary`, `.ui-input` and native dialog/control semantics. This owner-requested screen-specific visual treatment adapts the existing `.ui-card`/alert patterns to flat peer cards and ruled groups: use a border without a shadow, neutral secondary-action text, and no tinted navigation or alert backgrounds. Do not change shared component defaults across the product. The mockup uses native semantic controls with the existing palette and control radius.

Proposed semantic control-border alias `--control-borde: var(--texto-tenue)` matches the accounts draft: use on inputs/selects where low-contrast decorative borders cannot identify a control. No other new color tokens. Compact working palette: `--superficie` for flat working surfaces, `--fondo` for quiet navigation/scene grounds, `--texto` and `--texto-suave` for hierarchy, `--borde` for separation, and `--acento` only for the current primary action and keyboard focus. Semantic `--exito`/`--aviso`/`--error` color state words, always with a textual reason; default notices, avatars, brand mark and active navigation remain neutral. Existing `--sombra` applies only to floating menus, dialogs and transient toasts. Scene illustration colors are mock scene data, never semantic UI colors. Use the existing .8rem control radius (the project’s `--radius`) for new peer cards, canvas and dialogs; import groups, inspector and conflict-version rows are unboxed and divided by rules. Spacing 4/8/12/16/24/32/48px. Library max-width 1200px, readable import content max-width 760px, dialogs max-width 560px. These are layout decisions, not new global tokens.

Production typography remains Geist sans (`--font-sans`, `--font-geist-sans`), with mono only for technical identifiers when needed. Offline mockup uses system-ui/ui-monospace fallbacks. Page titles 24–28px/1.2, section headings 18–20px/1.35, card titles 16px/1.4, body 14–16px/1.5, metadata 12–13px; only mockup controls/disclaimers and illustrative scene stamps may be 11px. Labels use sentence case, without tracked uppercase eyebrows. All counts, dates and times use tabular figures; loaded counts align to the trailing edge of the result summary, and save dates align right beside “Guardado el” on cards. Each card has its name, date, visible owner where applicable and a full-width opening hit area divided by a rule; the whole first card row is visible at the 1440×1000 inspection viewport. Icons are consistent 1.5px-stroke inline SVG, supplement visible labels and are hidden from AT; no emoji or Unicode icon substitutes. The deliberate departure from a generic dashboard is scene-led recognition: a compact balloon/Backing illustration identifies the saved work, rather than KPIs, decorative cards or generic workspace banners. Keep the surrounding chrome quiet. Focus: existing 2px accent outline with 2px offset. Transitions ≤160ms; no continuous skeleton shimmer or decorative motion; reduced motion removes transitions.

## 5. Navigation and interaction model

The library and editable deep-link paths follow T4.4; the remaining query/dialog destinations describe UI routing within that surface. Permission keys and API contracts belong to SP-1/SP-4 tasks.

| View / dialog | Proposed destination / entry | Exit |
|---|---|---|
| V1 | `/proyectos`, navigation “Mis proyectos”, Taller “Mis proyectos” | Open → V3; New → unsaved V3; review local scene → V5 |
| V2 | `/proyectos?ambito=todos`, permission-filtered “Todos los proyectos” | Open own → V3, another owner's → V4; “Mis proyectos” → V1 |
| V3 | `/3d?proyecto=<id>` or `/3d` for a new unsaved scene | Library, new/open action and navigation pass F4 dirty guard |
| V4 / V4b | `/proyectos/<id>` | Authorized read-only page; copy only when `taller.usar` is also granted; never bypass `/3d` permission |
| V5 | `/proyectos?importar=navegador`, notice after first sign-in and persistent local-scene link | “Ahora no” → V1; successful “Abrir proyecto” → V3 |
| D1 Save first project / copy | “Guardar proyecto” for a new scene, or “Guardar una copia” | Submit → V3 success; Cancel/Escape returns to unchanged workspace |
| D2 Save conflict | A save receives a newer server revision | “Guardar una copia” → D1; “Abrir versión guardada” → D3 if dirty; “Seguir aquí” retains unsaved local work |
| D3 Unsaved departure | Open another project, new project or leave library with dirty scene | “Guardar y continuar”, “Conservar borrador y salir”, “Seguir aquí” |

Shared account menu/theme control follows SP-2 and existing shell. Do not create separate sign-in, account, catalogue or decoration screens here. The mockup marks these destinations as outside SP-4 when activated; actual product navigation uses their existing routes. Missing own-project access hides project navigation; direct requests still return a permission-denied response. List data and owner filters come only from authorized results, never from client-side filtering of everyone's records.

Enter submits save forms; search applies after a short debounce and Enter applies immediately. Search filters project names across the **entire authorized server collection**, before pagination. V2 owner filter is independent, initially “Todas las cuentas”; preserve both filters while opening/backing from a project. T4.3 accepts `q` (trimmed literal name substring, at most 120 characters; `%` and `_` are literal characters), `scope=mine|all` (default `mine`), and `ownerId` (UUID, only with authorized `all`). Never send `ownerId` from V1. `all` requires `proyectos.ver_todos`. Owner choices come only from authorized project-owner metadata across the permitted collection, including owners whose matches are beyond the current page; never enumerate unrelated accounts or derive choices only from the loaded page. Do not reinterpret the UI as a global account directory.

The server returns metadata only, at most 50 rows, ordered by `updatedAt DESC` then `id DESC`. A validated opaque cursor is bound to normalized `scope/q/ownerId`; cursor/filter mismatch returns 400. On any name/owner/scope/account change: invalidate old request identities immediately (before debounce), reset rows and cursor, then request the first page of the new normalized query. Retain the typed filters and show S23 in the results region; rows from the prior query never masquerade as current matches. Responses may update the UI only when their account, normalized filters and request generation are current. An obsolete response causes no visible status/title/row change and no toast. Clearing filters starts a fresh first-page request. A cursor mismatch shows “La lista cambió. Vuelve a cargarla.” / “Recargar lista”, restarts at page one, and never loops the rejected cursor.

Show a **loaded** count (“50 proyectos cargados”), not an invented total, and “Cargar más proyectos” only while a next cursor exists. While the next page is pending, retain current-query rows, announce “Cargando más proyectos…” and disable repeated pagination. On next-page failure keep rows, filters and retryable cursor with “Reintentar carga”; retry appends without duplicates. On a changed query, those old rows/cursor are discarded. Never fetch full scene documents for filtering or claim a loaded page represents the whole library. F6/S13/S23–S26 and UI-AC-41–51 govern these transitions.

## 6. Flows

**F1 — First save and continue (R6; owner round 9 q5).** 1) New scene has “Sin guardar en tu cuenta”. 2) “Guardar proyecto” opens D1 with the existing scene name. 3) Require a trimmed name, 1–120 characters (same limit as existing Taller name input); duplicate display names do not identify a project and do not replace one. 4) “Guardar en mi cuenta” disables repeated submission while pending. 5) Only confirmed server success shows “Guardado en tu cuenta · 26 oct, 14:32” and a persistent project identity. Failure retains scene/name and offers retry; unknown outcome is reconciled before retry, not blindly duplicated. 6) After the first named save: serialize automatic account saves 500ms after the last edit, with “Guardar ahora” available; show “Cambios sin guardar” until the corresponding edit generation is acknowledged. Keep one request in flight and queue the latest scene behind it. An older response never clears newer dirty work: while a submitted generation is pending, subsequent edits show “Guardando cambios anteriores · hay cambios nuevos sin guardar”, remain editable and wait behind that request. Any response is bound to account, project and request identity. After switching projects, a previous completion must not change the current title, canvas, dirty state, revision, conversation identity or undo history. There is no product success toast for a project that is no longer active; reconciliation of the old request stays scoped to that old project. F4 governs departure even when only pending edits remain. The owner confirmed explicit first named save followed by autosave and visible status; 500ms is the Planner technical default, not an owner-specified timing. The static mockup freezes these states for inspection; its state selector simulates pending/success instead of running a background upload timer.

**F2 — Reopen (R6).** 1) Enter V1 or authorized V2. 2) Search/filter; open a specific named project. 3) If current scene is dirty, resolve F4 first. 4) Show project loading, then replace workspace only after data validation/loading succeeds. 5) Restore name and the complete scene, including room, environment, salon, materials, scene-node relationships, placements, dimensions, colors and all valid fields/references, without silently converting away unsupported data. Failure leaves the prior workspace intact and explains whether retry is possible; no “empty scene” success fallback. Reset the undo stack and scene-conversation identity at the successful project boundary; never display the previous project’s AI thread in the new one. The separately stored AI conversation/generated images remain local and are not promised on another browser. Preserve existing local data; scene-node references are part of the scene even when they refer to media. No valid field/reference may be dropped to enforce the separate-AI-data boundary.

**F3 — Concurrent save (R6 edge case).** 1) Another session changes the project after this session's read. 2) Save refuses a stale revision; D2 says “Hay una versión más reciente” and shows last server save and author only when returned by authorized data. 3) Keep local work and the newer server scene. 4) Stop the autosave queue on a 409 until explicit resolution. Recovery: save local work as a new project, or explicitly open the newer version through D3. No overwrite/force-save action or automatic field merge. A server compare-and-save check is required; the modal alone cannot enforce concurrency safety.

**F4 — Leave / permission change.** 1) A dirty local scene or an unconfirmed in-flight save triggers D3 before in-app replacement/navigation. 2) Save-and-continue resumes the intended action only after acknowledged success; conflict/failure cancels the departure and preserves local work. 3) “Conservar borrador y salir” retains the unsent scene as an account/project-scoped local recovery draft (new unsaved scenes use a separate temporary identity), changes no server revision, and then continues; never delete the legacy import source. On return by the same account offer “Recuperar borrador” before replacing saved data, and reconcile its base revision. Other accounts must not enumerate or open it. If browser storage is full or blocked, show “No pudimos conservar el borrador en este navegador”; stay in the current project and retain the scene in memory. The keep-draft departure completes only after local persistence succeeds, and never labels the server state as saved. 4) Full-tab close uses the browser's native unsaved prompt when available, without promising reliable custom text or guaranteed persistence. 5) A revoked session goes to SP-2 sign-in with a safe return path; removed resource permission shows S8 without owner/title metadata and must not retry writes or copy account data to a different signed-in account. Clear visible scene state and query caches on sign-out/auth loss, ignore prior-identity completions and offer retained recovery only to the same account. These are boundaries in T4.4; the accepted autosave cadence grants no permission to disclose drafts.

**F5 — Browser import (R7).** 1) Detect raw `taller3d:escena:v1` after first sign-in without mutating it; repository evidence is one current scene, not an invented multi-project browser library. 2) Offer only on the first authenticated Taller visit with local data (T4.5), not inside the login handler. An account without Taller access retains the source until access is granted. Offer “Hay una escena en este navegador” / “Revisar importación”; do not auto-assign it. 3) V5 shows signed-in destination account, local scene name when safely readable and an unchecked “Esta escena es mía y quiero guardarla en esta cuenta”. 4) “Importar a mi cuenta” enables only after confirmation and valid supported data; importing is explicit. 5) Preserve the raw legacy source before any normal Taller autosave can replace it; read-only detection must not call the normal loader that normalizes/discards malformed content. 6) Server acknowledgment creates a new project and a per-account/source import receipt; repeated review shows the existing result rather than duplicating it. 7) “Ahora no” defers without hiding the persistent review entry; no source deletion after success. 8) Unsupported/corrupt source remains local, with a truthful reason and “Descargar copia original” (raw JSON, not a claim that it can open). No empty-project substitution. Copy explains “Se guardan el nombre y la escena completa. La conversación y las imágenes de IA siguen en este navegador.” This excludes only the separately stored AI data, not valid scene fields or references.

**F6 — Search and paginate (R6; Planner resolution of Q4).** 1) Open V1 or authorized V2 with the first ≤50 metadata rows. 2) Type a literal name, optionally select an authorized owner in V2; reset pagination and show S23 while querying the entire authorized collection. 3) Show returned matches even when they were beyond row 50 of the unfiltered list; no-results S14 is a successful empty query, not an empty account. 4) Load more only with the current filter-bound cursor (S25). 5) On page failure retain rows and retry (S13); a filter change invalidates the failed cursor. 6) A slow obsolete query must not replace current rows or filters; S24 is an inspection fixture for this otherwise silent rejection. The mockup simulates the server over an in-memory collection with >50 owned fixtures, 50-row pages and generation-bound query application; it makes no network requests and is not API evidence.

## 7. View specifications

**V1 — Mis proyectos.** H1 “Mis proyectos”; lead “Retoma tu trabajo desde cualquier navegador.”; primary “Nuevo proyecto” when `taller.usar` is granted. Optional import notice precedes search. Labelled input “Buscar proyecto”, count “50 proyectos cargados” for a full first page, sort text “Guardados más recientes primero”. Cards: “Quince años · Valentina”, “Boda · Jardín Botánico”, “Lanzamiento · Coral”; timestamp “Guardado el 26 oct 2026, 14:32”; visible button “Abrir proyecto” with accessible name including title. A cursor shows “Cargar más proyectos”; S13 covers next-page failure with previously loaded results retained. Illustrations are optional/decorative. Empty uses “Aún no tienes proyectos guardados” / “Crea un proyecto en el Taller 3D y guárdalo en tu cuenta.” / “Nuevo proyecto”. Zero search results differ: “No encontramos ese proyecto” / “Limpiar filtros”. F1/F2/F5; S1–S5/S8/S10/S13/S14/S23–S26.

**V2 — Todos los proyectos.** H1 “Todos los proyectos”; support “Consulta los proyectos guardados de cada cuenta.”; same structure as V1 plus owner filter and visible owner per card (“Lucía Torres · Eventos Lila”, “Mateo Ruiz · Montajes Norte”). Fixture account in this view is an employee, not an ordinary user with an exposed role toggle. Only V2 and V4 present staff identity in the mockup. No create-on-behalf action or ownership transfer. F2/F4; S1–S5/S8/S10/S13/S14/S23–S26.

**V3 — Project workspace.** Library link, project title, textual account-save status and save action stay visible outside the canvas. Show saved time, not relative-only “hace poco”; dates use active locale and labelled local timezone if an exact comparison is shown. Main region is existing Taller canvas, scene tree and inspector; mockup intentionally represents them as labelled illustration/context, not a functional 3D engine. “Simular edición” is a mockup-only control. New project starts with “Proyecto sin título”, never appears in V1 before server success. Save action is disabled with a nearby reason when unchanged, loading or pending. F1–F4; S1/S2/S4–S12.

**V4 — Read-only foreign project view (owner round 9 q7).** Separate `/proyectos/<id>` read-only scene page with persistent “Proyecto de Mateo Ruiz” and “Solo lectura”. No editable scene controls or update-original action. “Guardar una copia en mi cuenta” opens D1 and explicitly changes destination ownership to the current account; copy requires `taller.usar` and creates a new project owned by the signed-in account; it never updates or transfers the original. Copy stays disabled while loading, after a read error or offline, with the corresponding loading/error/connectivity reason visible. V4b omits the copy button and Taller/own-project navigation when `taller.usar` is absent, while retaining account menu, owner and “Todos los proyectos”. F2/F4; S1/S2/S4/S6/S8/S10/S17. Loading and failure describe reading, never saving; no account-save success banner appears on a foreign original. Never imply that opening grants write permission.

**V5 — Revisar importación.** H1 “Trae tu escena a tu cuenta”; subtitle “La encontramos en este navegador. Revisa que sea tuya antes de importarla.” Show destination “Lucía Torres · lucia@example.test”, source “Este navegador”, scene name and status. Checkbox from F5; primary “Importar a mi cuenta”; secondary “Ahora no”; recovery “Descargar copia original”. Success shows “Escena importada a tu cuenta”, confirmed project name and “Abrir proyecto”; source-retention message remains. Already imported source shows “Esta escena ya está en tu cuenta” and opens the previously confirmed project. F5; S1–S8/S10/S11/S16/S21. “Esta escena ya está en tu cuenta” is distinct from a newly acknowledged import; its receipt belongs to the currently signed-in account. Another account gets a fresh unchecked consent, never the prior project association.

**D1 — Guardar proyecto / Guardar una copia.** Native modal with heading, “Nombre del proyecto”, 120-character limit, destination account, “Cancelar” and “Guardar en mi cuenta”. Copy starts with “[original name] · copia”. Inline blank-name message “Escribe un nombre para el proyecto.”; keep user input on failure. Pending says “Guardando…” and prevents repeated submits. Close/Escape during a pending request does not claim cancellation of an operation already sent; background result must still reconcile. No form nested inside another form.

**D2 — Hay una versión más reciente.** Explain “Otra sesión guardó cambios después de que abriste este proyecto. Tu trabajo sigue aquí.” Show two labelled rows: “Tu trabajo · sin guardar” and “En tu cuenta · 26 oct 2026, 14:36”. Actions “Guardar una copia”, “Abrir versión guardada”, “Seguir aquí”. No ambiguous “Aceptar”, destructive default, automatic reload or forced overwrite. First focus is heading.

**D3 — Tienes cambios sin guardar.** Explain that a retained local draft is visible only to this account on this browser; buttons “Guardar y continuar” (primary), “Conservar borrador y salir” (secondary), “Seguir aquí” (secondary, initial focus). A failed/pending/conflicted save cannot complete the intended departure. When “Guardar y continuar” is disabled, D3 itself explains the pending acknowledgment, unknown result or offline condition; do not rely on a status hidden behind the modal. Closing/Escape equals “Seguir aquí”.

## 8. States

The mockup exposes native selects `view`, `state`, `scene`, `theme` with visible labels “Vista”, “Estado”, “Diálogo”, “Tema”. Views are V1–V5 plus permission variant V4b (`foreign-limited`). Scene values are `none`, `save`, `copy` (D1 copy variant), `conflict`, `leave`. Inapplicable inspection combinations normalize to the applicable view; they must never turn a read-only original into an editable project. Theme values are `light`, `dark`. State values below are exact integration vocabulary. Selecting a state with a specific context takes the mockup to that context; this is planning navigation, not a product state transition.

| ID / switch value | Applies | Visible result and recovery |
|---|---|---|
| S1 `ready` | all | Loaded library/workspace; reviewable local source. Product actions enabled according to permission/dirty state |
| S2 `loading` | all | Static skeleton plus “Cargando proyectos…” / “Abriendo proyecto…” / “Revisando escena…”; `aria-busy`; do not render an empty success or activate writes |
| S3 `empty` | V1/V2/V5 | True library empty state, or “No hay escenas para importar en este navegador”; useful return/create action. Selector moves editor to V1 |
| S4 `error` | all / D1 | “No pudimos cargar los proyectos” or “No pudimos guardar el proyecto”; inline reason, “Reintentar”; preserve existing scene and form. Failed reopen does not replace scene |
| S5 `success` | V1/V2/V3/V5 | Confirmed save/import message with title and time; no fake confirmation before response. Opening itself is a loaded state, not a save success |
| S6 `disabled` | V3/V4/V5 | Unchanged own scene (“No hay cambios para guardar”), foreign read-only, or missing ownership confirmation; reason is visible, not just opacity |
| S7 `validation` | D1 or V5 | Name error in D1, or unsupported/corrupt local source with preserved original; field error announced and associated. Mockup selects V3/D1 by default |
| S8 `permission-denied` | all | “No tienes acceso a estos proyectos” without title/owner/thumbnail; “Volver al inicio” and account navigation; controls cannot bypass guard |
| S9 `stale` | V3 / D2 | Conflicting server revision; both scenes retained; see F3. Selector opens V3/D2 |
| S10 `offline` | all | “Sin conexión. No podemos confirmar el guardado en tu cuenta.” Local editing remains enabled; account writes stay disabled until an explicit retry/reconciliation. Local work stays; list only shows explicitly identified already-loaded data, not a fabricated cache. “Reintentar conexión”; no automatic account queue |
| S11 `pending` | V3/V5/D1 | “Guardando en tu cuenta…” / “Importando…”; repeated mutation disabled. Timeout with unknown result says “No pudimos confirmar el resultado”; reconcile before resubmission. Mockup selects V3 |
| S12 `dirty` | V3 / D3 | “Cambios sin guardar”; save enabled; leave requires D3. Local backup success must not change this label |
| S13 `partial` | V1/V2 | The next page failed; previously loaded projects remain, with loaded count, reason and “Reintentar carga”. Cursor retry does not repeat existing rows. Selector opens V1 unless already in V2 |
| S14 `no-results` | V1/V2 | Name/owner filters have zero matches; show active filter and “Limpiar filtros”; never offer import as if no projects exist |
| S15 `recovery` | V3 | “Hay un borrador de esta cuenta en este navegador” with “Recuperar borrador”; recovery marks dirty and checks the stored base revision before writing. Selector opens V3 |
| S16 `unknown` | V3/V5/D1 | “No pudimos confirmar el resultado”; preserve local work, disable a new mutation and offer “Comprobar guardado” to reconcile the existing mutation/import receipt before retry. Selector opens V3 unless already in V5 |
| S17 `unavailable` | V3/V4/V4b | “Proyecto no disponible”; inaccessible and missing items share this 404 presentation, without title, owner or thumbnail; return to authorized list |
| S18 `too-large` | V3/D1 | “El proyecto supera el límite de 2 MiB”; unsent scene/name retained, never retry unchanged automatically; return to editing before another save |
| S19 `draft-error` | V3/D3 | “No pudimos conservar el borrador en este navegador”; keep current work visible and remain here; “Reintentar respaldo” retries only local persistence and completes the stored departure only if it succeeds |
| S20 `late-response` | V3 | Inspection fixture: after switching from Valentina to Boda, an obsolete Valentina completion leaves Boda’s title/scene and “Cambios sin guardar” unchanged. Explanation is mockup-only; product stays quiet |
| S21 `already-imported` | V5 | “Esta escena ya está en tu cuenta”; open the existing receipt-bound project, no second import; original remains; consent and receipt never cross accounts |
| S22 `pending-newer` | V3 | “Guardando cambios anteriores · hay cambios nuevos sin guardar”; save stays disabled while serialized request is in flight, scene editing remains available; older acknowledgment cannot label all edits saved |
| S23 `query-loading` | V1/V2 | Filters remain usable; results region shows “Buscando proyectos…” with `aria-busy`, prior-query rows removed, no empty-result claim; latest query replaces this pending state |
| S24 `query-late-response` | V1/V2 | Inspection fixture: current query “Horizonte” still shows “Ceremonia · Horizonte”, originally beyond unfiltered row 50, after a simulated old “Boda” response; only the mockup explains the ignored response, product remains quiet |
| S25 `page-loading` | V1/V2 | Current rows/count remain, “Cargando más proyectos…” announced and load-more disabled; success appends, failure transitions to S13 |
| S26 `cursor-invalid` | V1/V2 | “La lista cambió. Vuelve a cargarla.” retains visible current-query rows; “Recargar lista” restarts at page one with the same filters, never retries the rejected cursor |

Offline durable upload queue, live multi-user presence, background AI generation status and project deletion states are inapplicable: no such feature is assigned to SP-4. Thumbnails are optional; failure displays a placeholder, never a fatal project error. A malformed scene is an error, never silently dropped into an empty project. Session expiry reuses SP-2, not a new login dialog. A partial state is not used to fabricate a partly loaded scene.

## 9. Responsive behavior

Supported width starts at the product's existing 320px minimum. Content breakpoints align with existing Tailwind `sm` (640), `md` (768), `lg` (1024) and Taller's narrow/landscape behavior. Test 320, 390, 768, 1024 and 1440px, plus 844×390 landscape.

| Range | Library / import | Taller / dialogs |
|---|---|---|
| 320–639px | Compact header, horizontally wrapping section navigation; H1/action stack; labelled filters one column; cards one column, full names wrap; 16px gutters | Save status on its own wrapping row, explicit labelled save action; canvas then contextual scene summary; dialog fills viewport width/height with internally scrolling body, safe action area |
| 640–767px | Navigation above content; 24px gutters; two-card grid if available width fits; filters wrap | Dialog centered ≤560px, max-height 92dvh; editor context remains below canvas |
| 768–1023px | Two-card grid, filter search/owner on one line; import readable max-width 760px | Canvas and scene summary fit side by side; header wraps rather than clipping |
| ≥1024px | 200px section nav rail, main max-width 1200px, three-card grid; filters full row | Existing Taller rail and canvas/inspector layout retained; centered dialogs |

At ≤1023px landscape and height ≤540px, prioritize canvas space and put context beside it if content fits; do not force a tall mobile bottom panel. At zoom/reflow 320 CSS px, stack again. No page-wide horizontal scrolling. Long names wrap at safe opportunities; ellipsis is permitted only where full name is otherwise available to touch/keyboard, never only a hover tooltip. Dialog actions wrap; no fixed footer covers content; body has overscroll containment. EN expansion up to roughly 35% is a layout stress case, not a translation guarantee. ES copy is specified here; SP-8/SP-10 wire account language and complete translations. No RTL support is declared by this pilot.

## 10. Accessibility targets

Target WCAG 2.2 AA; conformance awaits rendered product review. Use header/nav/main landmarks, one H1, semantic project list, labelled inputs/selects, real buttons/links and a skip link. Accessible open names include the project name. Scene illustration is `aria-hidden`; all project/save data exists in text. Account identity is never conveyed solely by an avatar/color.

Use native modal dialog semantics (or the existing accessible equivalent), labelled title/description, trapped focus, Escape, and focus return to trigger. For D2 → D1/D3, retain the original page trigger through the dialog transition; if that trigger no longer exists after rendering, focus the conflict-resolution control or current view heading, never the document body or a hidden dialog control. Initial focus: D1 name; D2 heading; D3 “Seguir aquí”. On validation focus first invalid field; on permission/data loading completion move focus to the page heading only after actual navigation. Do not repeatedly steal focus on save-status updates. Background is inert while modal. Saving status uses polite live region; actionable errors use an alert once. Offline/stale/disabled/success labels include words as well as color.

All new clickable targets ≥44×44 CSS px; existing narrow Taller controls are outside this mockup redesign but the added save/library controls meet that target. Standard keyboard activation, logical DOM/tab order, no drag-only project action, no hover-only menu. Text contrast ≥4.5:1 (large text ≥3:1); meaningful controls/focus indicators ≥3:1. Decorative panel borders are not control affordances. Preserve 200% text zoom and 400% reflow; no hidden focus under sticky headers. Honor reduced motion. Contrast must be measured for actual foreground/background pairs in both themes; a token name is not evidence. 3D engine keyboard access is existing scope, but every added project action must be usable without operating its canvas.

## 11. Visual acceptance criteria

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | ≥1024px | ready / V1 | The library displays three columns of project cards beside the section rail. |
| UI-AC-02 | 320–639px | ready / V1 | Cards, search and the new-project action fit one column without horizontal page scrolling. |
| UI-AC-03 | 640–1023px | ready / V1 | The project grid has two columns and navigation sits above content. |
| UI-AC-04 | 320–1440px | ready / V2 | Every project card shows its owner as visible text. |
| UI-AC-05 | 320–1440px | no-results | A clear-filters action is shown with the zero-results explanation. |
| UI-AC-06 | 320–1440px | empty / V1 | “Aún no tienes proyectos guardados” appears with “Nuevo proyecto”. |
| UI-AC-07 | 320–1440px | loading | Skeletons and a loading label appear instead of an empty-library success. |
| UI-AC-08 | 320–1440px | dirty / V3 | “Cambios sin guardar” is visible adjacent to the enabled save action outside the canvas. |
| UI-AC-09 | 320–1440px | success / V3 | Account-save confirmation includes the saved time in visible text. |
| UI-AC-10 | 320–1440px | validation / D1 | Submitting a blank name keeps the modal open and associates its error with the name input. |
| UI-AC-11 | 320–1440px | pending / D1 | The submit button reads “Guardando…” and cannot issue a second save. |
| UI-AC-12 | 320–1440px | stale / D2 | Both local-unsaved and server-saved versions are labelled without a force-overwrite action. |
| UI-AC-13 | 320–639px | dirty / D3 | All three departure choices remain reachable through vertical scrolling. |
| UI-AC-14 | 320–1440px | disabled / V4 | Owner and “Solo lectura” are visible and no update-original action is offered. |
| UI-AC-15 | 320–1440px | permission-denied | Restricted project names, owners and thumbnails are absent from the denied view. |
| UI-AC-16 | 320–1440px | ready / V5 | Import shows the signed-in destination account above the unchecked ownership confirmation. |
| UI-AC-17 | 320–1440px | disabled / V5 | Import is disabled until the ownership checkbox is checked. |
| UI-AC-18 | 320–1440px | validation / V5 | An incompatible source shows its reason and the original-copy download action. |
| UI-AC-19 | 320–1440px | success / V5 | Confirmed import shows an open-project action and says the browser original is retained. |
| UI-AC-20 | 320–1440px | partial / V1 | Previously loaded cards remain visible beside a next-page retry control. |
| UI-AC-21 | 320–1440px | offline | The account-save status explicitly says that saving cannot be confirmed. |
| UI-AC-22 | 320–1440px | error | A labelled retry control appears without replacing existing scene contents with an empty scene. |
| UI-AC-23 | 320–1440px | ready / D1–D3 | Escape closes the dialog and restores focus to the activating control. |
| UI-AC-24 | 320–1440px | ready / both themes | Focus on each project/save control is visible against its actual background. |
| UI-AC-25 | 844×390px | dirty / V3 | Save controls and status remain reachable while the workspace reflows for the low-height viewport. |
| UI-AC-26 | 320–1440px | ready / dark | Generic primary buttons use `--sobre-acento` rather than white. |
| UI-AC-27 | 320px at reflow | ready / V1 | Long project names wrap without requiring a hover tooltip to read them. |
| UI-AC-28 | 320–1440px | ready / V4b | The read-only custom-role view has no copy or Taller action. |
| UI-AC-29 | 320–1440px | recovery / V3 | The recovery banner identifies this account and exposes an explicit recover action. |
| UI-AC-30 | 320–1440px | unknown | An outcome-reconciliation action appears while new mutations are disabled. |
| UI-AC-31 | 320–1440px | late-response / V3 | The Boda project title remains visible with “Cambios sin guardar” after the mocked previous-project completion. |
| UI-AC-32 | 320–1440px | pending-newer / V3 | The save badge explicitly distinguishes submitted changes from newer unsaved edits. |
| UI-AC-33 | 320–1440px | offline / V3 | The mockup’s edit control remains enabled while account saving is unavailable. |
| UI-AC-34 | 320–1440px | already-imported / V5 | The existing-import message offers opening a project without another import submission. |
| UI-AC-35 | 320–1440px | ready / V5 | Changing the fixture account clears ownership consent and never reveals another account’s import result. |
| UI-AC-36 | 320–1440px | error / V4b | The failure describes loading the project and offers no save or copy action. |
| UI-AC-37 | 320–1440px | unavailable | The unavailable-project screen contains no project title, owner or scene illustration. |
| UI-AC-38 | 320–1440px | draft-error | A failed local backup leaves the current project visible and offers retrying the local backup. |
| UI-AC-39 | 320–1440px | too-large | The size-limit message states 2 MiB and does not claim successful saving. |
| UI-AC-40 | 320–1440px | stale / D1 copy | The copy dialog names the current destination account and never offers overwriting the original. |
| UI-AC-41 | 320–1440px | ready / V1 | Searching “Horizonte” finds “Ceremonia · Horizonte” before loading page two of the unfiltered fixture collection. |
| UI-AC-42 | 320–1440px | ready / V1 | The initial 50-row fixture page shows “50 proyectos cargados”. |
| UI-AC-43 | 320–1440px | ready / V1 | “Cargar más proyectos” appends the next page without duplicate cards. |
| UI-AC-44 | 320–1440px | query-loading / V1/V2 | The results region displays “Buscando proyectos…” while the labelled filters remain operable. |
| UI-AC-45 | 320–1440px | query-late-response / V1/V2 | “Horizonte” and its matching card remain after the mock obsolete “Boda” response. |
| UI-AC-46 | 320–1440px | partial / V1/V2 | Changing a filter removes the failed old page's retry control and starts a first-page query. |
| UI-AC-47 | 320–1440px | ready / V2 | The owner selector includes the authorized fixture owners Lucía, Mateo and Ana. |
| UI-AC-48 | 320–1440px | page-loading / V1/V2 | “Cargando más proyectos…” appears below retained cards with a disabled pagination button. |
| UI-AC-49 | 320–1440px | ready / V1 | After loading page two, changing the name filter resets pagination to at most 50 matching rows. |
| UI-AC-50 | 320–1440px | ready / V5 | Import explains that the complete scene is saved and separately stored AI conversation/images remain in this browser. |
| UI-AC-51 | 320–1440px | cursor-invalid / V1/V2 | “Recargar lista” restarts the first page while preserving the visible name/owner filters. |
| UI-AC-52 | 320–1440px | pending / unknown / V3 | Choosing “Nuevo proyecto” opens D3 and retains the current title until departure is resolved. |
| UI-AC-53 | 320–1440px | stale / D2 → D1 or D3 | Cancelling the second dialog restores focus to the original page trigger or the current conflict-resolution control. |
| UI-AC-54 | 320–1440px | pending / pending-newer / unknown / offline / D3 | A visible explanation inside D3 states why “Guardar y continuar” is disabled. |
| UI-AC-55 | 320–1440px | ready / V1–V5 / both themes | Active section navigation has neutral surface/text tokens, without an accent fill or colored rail. |
| UI-AC-56 | 320–1440px | ready / V1–V5 / both themes | Default notices, account avatar and destination groups have no accent-colored background. |
| UI-AC-57 | 320–1440px | ready / V1/V2 | Every card save date is right-aligned and uses tabular figures. |
| UI-AC-58 | 320–1440px | ready / V1–V5 | Page headings and supporting section labels use sentence case without tracked uppercase eyebrows. |
| UI-AC-59 | 320–1440px | ready / D2 | Local-work and account-version details are separated by rules instead of nested cards. |
| UI-AC-60 | 1440×1000px | ready / V1/V2 | The first project row includes visible titles, save dates, owner where applicable and opening actions within the viewport. |
| UI-AC-61 | 320–1440px | empty / V1/V2 | The empty-state instruction and next action appear without a decorative icon tile. |
| UI-AC-62 | 320–1440px | ready / V1–V5 | Nonfloating peer cards and scene panels have borders without shadows. |
| UI-AC-63 | 320–1440px | ready / V1/V2 | The loaded count is right-aligned at the end of the result summary and uses tabular figures. |
| UI-AC-64 | 320–1440px | success / V3 | The visible save time matches the selected project’s save timestamp in the library. |

## 12. Open questions and assumptions

**Open questions for the owner: none.** Q1–Q3 are resolved by the accepted round 9 q5–q7 answers; Q4 is resolved by the Planner's technical ruling and T4.3/T4.4/T4.6. The design and subplan remain unapproved; SP-2 remains the planning focus. No repeated owner confirmation is requested for these settled behaviors.

| Resolved decision | Authority | Effective contract |
|---|---|---|
| Q1 — Save mode | Owner, round 9 q5 | First explicit named save; subsequent autosave with visible state and “Guardar ahora”. 500ms debounce remains the Planner technical default. Account/project draft isolation and truthful pending/offline/conflict handling remain. |
| Q2 — Foreign originals | Owner, round 9 q7 | Staff/admin with read-all access inspect originals read-only. “Guardar una copia en mi cuenta” requires `taller.usar` and creates a caller-owned project. No original update or ownership transfer. |
| Q3 — Saved content | Owner, round 9 q6 | Name plus complete scene including room/environment/salon/materials/scene-node relationships. Separately stored AI conversation/generated images remain local. No local erasure or dropped valid scene field/reference. |
| Q4 — Search/filter scope | Planner ruling, T4.3/T4.4/T4.6 | Global authorized server filtering before 50-row cursor pagination, literal trimmed `q` ≤120, `mine|all`, authorized UUID `ownerId`, filter-bound cursor mismatch 400, metadata-only owner choices, reset/late-response/page-retry handling in F6. |

Confirmed: users see their own projects; authorized staff can open everyone's; browser scenes are offered for explicit import; original data must not be lost; later saves must not silently overwrite earlier concurrent saves. Saving requires server acknowledgment. Plan 3 includes own Taller projects; custom roles are evaluated by actual permissions, not display names.

Presentation assumptions retained from the prior draft: one detected current browser scene from the evidenced key; no delete/share/history UI; optional nonessential scene illustrations; ES copy with translation rollout in SP-8/SP-10; search debounce is a UI implementation timing, not a new owner decision. The self-contained mockup uses system fonts, fictional metadata and illustrative scenes; save/import states remain manually inspectable and do not write real storage. Search/pagination alone simulate asynchronous responses locally. Source receipt/deduplication and raw-source preservation remain implementation requirements for lossless import. T4.2/T4.3 specify project-document@1, trimmed names of 1–120 characters, 2 MiB limit, complete scene validation, atomic revision compare-and-save and account-scoped durable mutation/import receipts.

Authoritative errors: missing/inaccessible item 404 (generic “Proyecto no disponible” without metadata), collection-scope denial 403, unauthenticated 401 (SP-2), conflict 409, too-large 413 (retain scene and explain 2 MiB limit), cursor/filter mismatch 400 (restart the list as specified in section 5). CSS illustrations and simulated queries cannot prove identical 3D round trips, database pagination, concurrency, access control, storage retention, import idempotency or accessibility compliance. Those need task-level integration tests and independent rendered review. No preview setting is required for these explicitly requested planning files.

Planning artifact verification (2026-10-26, 19:36 visual revision): Playwright used the installed `/usr/bin/chromium` against the self-contained file URL, without a server. The six view variants, 26 states, two themes and widths 320/390/640/768/1024/1440px passed 1,872 structure/heading/overflow checks; all four dialog variants passed another 32 layout/44px-target checks. After visual inspection found a clipped illustrative scene at narrow widths, its scale was corrected and 1,248 checks were rerun over the affected 320/390/640px widths plus 844×390 landscape; all passed, including scene-art bounds. A final 72 ready-view/theme/width checks verified every illustration fits its preview after adjusting the smaller import thumbnail. Zero page exceptions and zero network requests were observed during the recorded matrix and interaction runs.

Forty-two focused interaction assertions passed: first named save and blank-name validation, saved-project listing, global search beyond the first 50 rows, pagination from 50 to 56 owned fixtures without duplicates, query reset and late-response rejection, authorized owner filtering, foreign read/copy and custom-role limits, conflict-to-copy Escape focus, pending/unknown departure guard, failed local-backup retention, explicit account-scoped import consent/receipt isolation, offline editing with account save disabled, and denied/unavailable metadata suppression. The first library row fits at 1440×1000 with right-aligned tabular dates and no card shadow. Eighteen actual semantic text/background token pairs measured 4.94:1–17.85:1 in the two themes; reduced-motion transitions measured 0s. D1 initially focused its name field and Escape returned to the actual save trigger. Native modal Tab reached only dialog controls and Chromium’s browser-chrome/body stop, with no background product control reached; this is not a claim of full accessibility conformance.

Desktop library/all-projects/workspace/foreign/import screens, 320px import and read-only scenes, 320px conflict/pending-departure dialogs, 390px name validation and 844×390 landscape were visually inspected. The corrected narrow scene and import thumbnail were rendered and inspected again. Screenshots were captured in memory and viewed in the session; no extra design/preview or screenshot files were created. These checks attest the planning mockup only. Product lint/types/build, actual persistence/authorization, complete 3D round trips and WCAG conformance were not run or established; T4.6–T4.9 and owner plan/design approval remain pending.
