---
name: Archivo de montajes
status: draft
kind: direction-exploration
contract_ref: proyectos@v1
revision: r8.dir-a
subplan: SP-4
requirements: [R6, R7]
owner: David
date: 2026-10-27
chosen_thumbnail: proyectos@v1.r8.dir-a.html.candidate-1.html
---

# Archivo de montajes — direction A

## 1. Identity and traceability

An independent **exploration**, pending owner selection. This is not the canonical contract, an approved revision, an implementation or an instruction to consume a draft. Only the six revision-specific direction artifacts and the delegation RESULT are written. SPEC, PLAN, shared contracts, history and repositories remain untouched.

Sources: `SPEC.md` (SHA-256 prefix `65b1e5ecc06f20d9`), `PLAN.md` (`cc7e53f2abf3c23c`), `PLAN.json` (`7a2c833a7e711508`), and `proyectos@v1.r8.behavior.md` (`378c0aa4a41164c6`). The shared source identifies SP-4, R6/R7, future contract `proyectos@v1`, design task T4.1 and visual audit T4.8. The plan is still being discussed; round 9 settles behavior, not design approval.

## 2. Purpose, concept and memorable move

**Concept:** a working archive of balloon installations. A project is a named montage, with an owner, a complete scene and a saved revision. The screen answers “Which montage can I continue, and where are my changes?” Ownership and save status are working information, not decorative statistics.

**Memorable move:** the selected record **unfolds in place** into a scene/detail spread. The title and revision remain on the record's header; a shallow perspective fold opens below them. During conflict, the local and server sheets collate side by side with an 80 ms offset. This is a short registration sequence, without elastic bounce or disappearance of the text.

Users: owners continue their own scenes; employees/admins with `proyectos.ver_todos` inspect the authorized collection; staff without `taller.usar` have a read-only view and cannot create a copy. Import asks the current account's consent. Opening another person's project never changes its owner.

## 3. Composition, candidates and look ledger

Two fresh visual thumbnails were written **before** the TSX:

- **Chosen: [candidate 1](proyectos@v1.r8.dir-a.html.candidate-1.html)** — full-width compact records with an inline scene/detail fold. Names, owners and revisions remain comparable. A primary continuation action belongs to the open record.
- [Candidate 2](proyectos@v1.r8.dir-a.html.candidate-2.html) — one large recent-project plate and a smaller image-led stack. It gives the illustrations more area, but weakens scan consistency and puts less ownership/revision information on screen.

The thumbnails are small original compositions, not production screens or an HTML-snippet fallback. The complete mockup uses the real offline library builder.

**Why this is not a generic default:** no dashboard statistics, wallpaper illustration or equal preview-card grid. Montage records unfold within their collection. A large project name, a narrow timestamp, a complete-scene diagram and the save receipt form the hierarchy. The list, not a decorative hero, owns the page.

**Look ledger:** SP-2 `cuentas-admin@v1.r7.dir-a/b/c.md` and SP-3 `taller-esenciales@v1.r6.dir-a/b/c.md` were read. Accounts A uses an editorial side margin/register; B uses an unfolding access pass and bottom dock; C uses perforated passes and permission slots. Taller A uses two assembly bands; B a tool spine/stage/folio; C a cutting bench and bottom tool tray. This exploration shares Pictures' ring-and-dot mark, product words, token mapping and neutral navigation. It uses neither their side margin, access pass, bottom dock, tool spine nor assembly tray. The fold here opens a project record in a collection, rather than a two-leaf identity pass. Its precise nonelastic collating motion differs from the access pass's spring/hinge choreography.

## 4. Eight axes, system mapping and real components

| Axis | Present expression | Rendered evidence |
|---|---|---|
| Concept | A live archive of named installations; owner and saved version travel with each record. | `.record`, `.record-sub`, `.folio-info` |
| Layout | Full-width stacked records; an open record spreads into scene/details at approximately 44:56. Scene editing and import use their own contextual work surfaces. | `.archive`, `.record-fold`, `.editor-layout`, `.import-layout` |
| Navigation | In-flow neutral collection underline, collection-wide name search, staff-only owner filter and keyboard-operated record disclosures. Project-local return appears beside its title. | `.scope-nav`, `.search-field`, `.record-toggle`, `.backline` |
| Typography | Arial/Helvetica offline fallback; page title 32 px, record names 21 px desktop/23 px phone, fold/conflict title 24 px, body/control 14–15 px, tabular monospace timestamp 12 px. | `.intro-copy h1`, `.record-title`, `.record-date` |
| Density and shape | Desktop records start at 91 px, phone at 110 px. Ruled rows, 24 px unfolded gutters, 44 px controls; only diagrams and decisions need rounded frames. | `.record-toggle`, `.record-fold`, `.stage`, `.btn` |
| Components | Real Button, Input, Skeleton, Dialog and AlertDialog; custom record disclosure, installation SVG, version spread and import receipt. | `[data-slot=button]`, `[data-slot=input]`, `.compare-versions`, `.import-receipt` |
| Colour | Pictures light/dark mapping; mauve for the main action and balloons, green for saved, amber for unsent/conflict, red for failure; neutral collection navigation. | `.status`, `.notice`, `.scope-link`, `.balloon` |
| Motion | 9 px horizontal registration, row stagger 45 ms, -4° perspective fold, 80 ms sheet collation; easing `cubic-bezier(.16,1,.3,1)`. Cut/fold expressive 420/588 ms, natural 220/308 ms, subtle 140/196 ms; control press/hover 160 ms. | `.record`, `.record-fold`, `.archive-tools`, `.record-arrow`, `.version-sheet` |

The companion JSON supplies all eight axes and 14 selectors for the four measurable axes. Each motion selector has an actual animation or transition. `useMotionProfile()` sets the timing/reduced state; finite CSS animations provide this direction's grammar. There are no infinite decorative animations. Hidden-tab handling pauses them; reduced motion, Quieto and `?still=1` remove travel/rotation and preserve every action and final layout.

Both repositories were inspected read-only: `src/app/globals.css`, `src/components/tres-d/guardado-escena.ts` and the `Taller3D.tsx` save consumer. The existing 500 ms debounce is a technical default; the new UI does not claim the existing browser writer is a server save. The old reader can discard incompatible scene data, so SP-4 must read raw legacy data before that parser, as the behavior source requires.

| Pictures token | Kit role | Light / dark |
|---|---|---|
| `--fondo` | `--background` | `#faf9fc` / `#0b0c10` |
| `--superficie` | card/popover | `#ffffff` / `#16181f` |
| `--texto` | foregrounds | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | muted foreground | `#6b6178` / local proposal `#adb3c0` |
| `--superficie-2` | secondary/muted | `#efe9f8` / `#242733` |
| `--acento`, `--sobre-acento` | primary/primary foreground/ring | `#6d3fe0`, white / `#9479ff`, `#120b24` |
| `--acento-suave` | primary soft | `#ece3fb` / `#241f3d` |
| `--borde` | decorative border | `#e3daef` / `#383c48` |
| `--texto-tenue` / `--texto-suave` | local stronger input edge | `#766c85` / `#9aa1ad` |
| `--taller-visor` | diagram ground | `#ebe7f1` / `#1a1722` |
| `--exito`, `--aviso`, `--error` | status text and soft grounds | Existing Pictures values by theme |

The stronger input edge, darker decorative rule and lighter dark metadata are explicit mockup-local accessibility adaptations. They do not alter the production design system. The page, header and footer share the same outer axis; fold content has its own consistent inset. The design uses no checkboxes, so it introduces no native-checkbox contrast dependency.

Component provenance: `shadcn:button default/outline/ghost` from `@/components/ui/button`; `shadcn:input` from `@/components/ui/input`; `shadcn:skeleton` from `@/components/ui/skeleton`; `shadcn:dialog` from `@/components/ui/dialog` and `shadcn:alert-dialog` from `@/components/ui/alert-dialog` (installed Animate UI over Base UI). `@kit/mockup` supplies `mountMockup/useMockup`; `@kit/motion` supplies `useMotionProfile`; `motion/react` is bundled. The record disclosure is a custom semantic button, not a claimed upstream Accordion. Bencho gestures and React Bits marketing effects are not needed for this operational screen.

## 5. Navigation and interaction model

The native planning selectors retain **Mockup**, Vista, Estado, Diálogo, Tema and Movimiento. The plan-page bridge can drive their stable IDs `view`, `state`, `scene`, `theme`, `motion`. They are demonstration controls outside the product, not an authorization model.

Product navigation is contextual: collection switch/search/filter, a record disclosure, Continue/Open read-only, project-local back, and import review. The regular-user collection hides the staff scope and owner filter. The five native Vista options expose the authorized scenarios for comparison; they do not add a staff-navigation item to a regular user's product.

Each record toggle exposes `aria-expanded` and `aria-controls`. Named modal actions use real modal primitives, trap Tab/Shift+Tab and support Escape with focus return. The server-load confirmation uses AlertDialog; it is not dismissible by a casual outside click. No drag, hover-only action or icon-only navigation is required.

## 6. Flows and behavioral boundaries

1. **First named save:** New project opens a draft; Save project requests a nonblank name and identifies Ana Torres as the destination account. Confirm adds one owned demo record. Later edits demonstrate pending → saving → saved with the inherited 500 ms debounce and an illustrative request delay. Save now remains available for existing owned projects.
2. **Find and reopen:** Search covers the whole authorized collection before paging; changing query or owner resets the page. The mock fixture contains 57 records across two owners; “Terraza azul” is record 57 and can be found without loading preceding pages. Staff scope exposes the owner filter. Later-page failure retains earlier records and offers retry. Production must use server-wide literal search, filter-bound cursors and stale-response rejection, not copy this in-memory filter into a client-only search.
3. **Conflict:** A 409 stops saving; local unsent work remains. The two sheets name local changes and server version 13. Save as copy creates a new owned scene; load-server asks confirmation and retains the previous local scene as an account/project-scoped draft. The demo allows saving that retained displacement as a copy after loading version 13. It does not offer an overwrite action or a version-history browser.
4. **Offline/failure:** Unsent edits remain visible and labelled unsent, with retry/reconnection. They are never represented as a successful server save. Production acknowledgements must be matched to the current account, project, revision and edit generation; an obsolete response cannot change the newest draft's status.
5. **Foreign original:** Authorized staff read the scene without mutation controls. Copy requires `taller.usar`, belongs to the current account and leaves the original unchanged. Opening does not transfer ownership. Disabled explicitly demonstrates the read-only role without Taller access.
6. **Legacy import:** Review names the origin and destination account. Consent imports once; “Ahora no” retains raw local data and offers a later review. Repeated consent/revisit does not duplicate the mock record. Invalid legacy data explains why it cannot be imported and offers downloading its unchanged raw sample. Real retry safety requires account plus raw-source hash and a transaction; the mockup is not persistence evidence.
7. **Switching away:** The project-local back action with unsent changes opens a preservation decision, offering continued work or an owned copy. Production must retain drafts/receipts by account and project and clear the visible prior-account surface after account switch. No account switcher or deletion flow is added to SP-4.

The persisted payload remains **name plus complete scene**: room, environment, salon, materials, attachments and node relationships. AI conversation and generated images remain browser-local. Account-deletion refusal with existing projects, server validation, atomic conditional updates, cross-origin mutation checks and ownership isolation remain T4.2/T4.3/T4.31/T4.6/T4.9 obligations; they are not proven by this illustration. No delete, ownership transfer or version-history feature is introduced.

## 7. View inventory and consumers

| Vista / id | Contents and primary outcome | Traceability |
|---|---|---|
| Mis proyectos / `mine` | Personal collection, name search, expandable montage, saved owner/revision, new project, page continuation, local import entry. | R6/R7 · T4.4/T4.5 |
| Consulta del equipo / `all` | Authorized collection, current-owner filter, foreign read-only entry and collection-wide search. | R6 · T4.3/T4.4 |
| Proyecto propio / `editor` | Named save, visible save receipt, illustrative complete-scene diagram, conflict comparison and retained-draft recovery. | R6 · T4.4 |
| Proyecto ajeno / `foreign` | Named owner, read-only scene, owned copy gated by Taller permission. | R6 · T4.4 |
| Importar del navegador / `import` | Raw-source preservation promise, destination account, explicit naming/consent, refusal, retry, incompatible-data explanation/download. | R7 · T4.5 |

The four modal scenes are `first-save`, `copy`, `load-server`, `leave`. The final two are recovery decisions, not an expanded product scope. The schematic only shows a representative table, eight chairs, a panel and balloons; it is a local SVG, not a 3D engine, thumbnail-generation service or validated project serialization.

## 8. State inventory

All thirteen states are reachable from Estado. Context-specific states affect only relevant controls; choosing a fixture does not assert that every state can occur in every production view.

| Estado / id | Visible behavior and recovery |
|---|---|
| Normal / `ready` | Collection and continuation; owned editing; voluntary import. |
| Cargando / `loading` | Stable row/scene skeletons; request-dependent controls disabled; existing named fixtures keep their last known revision. |
| Vacío / `empty` | Collection explanation with next action and local-import entry. In editor/import this fixture does not invent an empty foreign payload. |
| Error / `error` | Failure text, retained work and retry; collection content is not fabricated. |
| Éxito / `success` | Saved/imported confirmation; import explains that raw source remains. |
| Guardando / `saving` | Pending status or import action text; repeated request controls disabled. |
| Cambios sin guardar / `dirty` | Explicit unsent status on an owned project. Not a new save status for a foreign original. |
| Sin conexión / `offline` | Local work remains visible; remote operations disabled; reconnect action explains recovery. |
| Conflicto / `conflict` | Owned save halted, two version sheets, copy/load choices, no silent overwrite. Foreign originals do not get an original-edit conflict action. |
| Datos no válidos / `invalid` | Field/payload explanation; import raw download; no lossy migration or manufactured success. |
| Sin permiso / `denied` | Scene and foreign metadata hidden; return to owned projects. |
| Sin Taller / `disabled` | In foreign view the original is inspectable, edits/copy disabled, missing permission explained. |
| Página siguiente fallida / `next-error` | Existing list retained, continuation retry; query/filter changes reset the displayed page. |

The sample list is synchronous, so stale-query response rejection, two-browser races and account isolation are specified requirements for implementation rather than simulated backend claims. The illustrative fixture selection remains independent of product interactions; use Normal to inspect natural local transitions.

## 9. Responsive rules

- **≥1024 px:** shared shell up to 1360 px, 40 px outer gutters (48 at ≥1500); horizontal record title/owner/time/disclosure columns; fold scene/details at approximately 44:56; project editor scene plus 280 px context column; import in two columns.
- **768–1023 px:** 24 px gutters; collection scope moves to its own row; search and filter/action remain aligned; editor context is 250 px; record metadata narrows.
- **360–767 px:** 20 px outer gutters; stacked search/filter/action; each record has a name/ownership line and timestamp line; fold, editor and import become one column. Version sheets stack. Controls are ≥44 px and long copy wraps. The page scrolls vertically; no fixed product dock obscures content.
- **320–359 px:** 20 px outer gutters retained; facts reduce to two columns and the ornamental brand ring is removed to keep the account label readable. No horizontal page scrolling.
- **Landscape height ≤540 px, width <1024 px:** editor scene and 240 px context sit beside each other; modal height is bounded below the planning chrome and scrolls internally.

Dialogs use 20 px outside margins and ≤560 px width, with internal scrolling and planning-bar clearance. Modal actions stack on phone. Header, page and footer share their outer axis rather than centering unrelated lines.

## 10. Accessibility targets and observed evidence

Target WCAG 2.2 AA: readable text ≥4.5:1; interactive edges/focus ≥3:1; 3 px visible focus with 3 px offset; semantic disclosures, modal titles/descriptions, status/alert messaging and labelled inputs/selectors. Minimum body/metadata labels 12 px; small diagram dimension 11 px. Disabled controls remain opaque and readable. No native checkbox is required. Reduced motion removes the fold/travel but retains all data and decisions.

The automated audit measures focus, padding, alignment, contrast and overflow; it is not a full WCAG certification. A focused keyboard test verified 12 consecutive Tab moves remain inside the dialog, Escape dismisses it and focus returns to the actual trigger. Screen-reader speech, 200–400% zoom, touch-assistive technologies and translated production strings remain future rendered acceptance, not completed evidence here.

## 11. Observable criteria and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| SP4-A-01 | ≥1024 px | ready | An open record keeps its name/owner/revision in the header and shows a scene/details spread directly below. |
| SP4-A-02 | 320–767 px | ready | Records use two text rows and the fold stacks without horizontal page scrolling. |
| SP4-A-03 | all supported widths | loading | Skeletons occupy the final content area and the request-dependent save action is disabled. |
| SP4-A-04 | all supported widths | empty | A visible next action starts a new montage and a second action reviews the browser scene. |
| SP4-A-05 | all supported widths | conflict | Local unsent work and server version 13 are distinguished; copy and load-server are named actions; Save now is disabled. |
| SP4-A-06 | all supported widths | offline | The owned scene stays visible with unsent status and disabled server save. |
| SP4-A-07 | all supported widths | disabled, foreign | The owner remains Luisa; edit/copy controls are disabled and the Taller permission limitation is stated. |
| SP4-A-08 | all supported widths | invalid, import | Incompatibility explanation and original download are visible; import is unavailable. |
| SP4-A-09 | all supported widths | denied | No scene or foreign original metadata is rendered. |
| SP4-A-10 | all supported widths | next-error | Previously loaded records remain and continuation retry is reachable. |
| SP4-A-11 | all supported widths | copy/load modal | Dialog decisions fit within viewport margins and remain keyboard-operable. |
| SP4-A-12 | all supported widths | reduced motion | No entrance travel/rotation continues, while records, controls and decisions remain available. |
| SP4-A-13 | ≥1024 px and phone | ready, both themes | Header/page/footer share an outer axis; controls have visible edges and focus. |
| SP4-A-14 | all supported widths | recovery | Loading the server version retains the local displacement and exposes saving that draft as an owned copy. |

Real offline build: **588,871 bytes**, approximately 575 KB, 2,135 bundled source files. No package install, asset fetch, external font, CDN or HTML fallback. Only the assigned output path was built.

Commands executed:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <proyectos@v1.r8.dir-a.tsx> --out <proyectos@v1.r8.dir-a.html>
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py <proyectos@v1.r8.dir-a.html>
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <proyectos@v1.r8.dir-a.html>
```

The contrast CLI reported `contrast: 158 pairs checked in light and dark, all pass`. Since TSX injects the project overrides at runtime, an additional `contrast.check` combined the installed theme CSS with the exact entry CSS: **158 effective Pictures-role pairs, PASS**. Its first run found an inherited, unused dark `primary-soft` pair at 3.67:1; mapping it explicitly to Pictures' `--acento-suave` fixed that token inconsistency. The rendered audit measures the actual computed colours.

Final rendered audit, exit 0, against the final build:

```text
audit: proyectos@v1.r8.dir-a.html — 340 renders (340 combinations planned), 11348 text measurements, 896 focus stops
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

All 340 planned combinations were measured without sampling: five views, thirteen state fixtures, four dialogs, both themes and 1280/390 px. Audit checks also passed reduced-motion settlement and expressive-load layout stability. Final HTML SHA-256: `8731d9a316dd7a4fd24177a95ebc2d3145a7ccc684d98309d0a146d0485025ff`.

Additional evidence: ten interaction groups pass (whole-collection search including record 57, owner filter/page reset, edit/save sequence, offline retention, conflict-owned copy, foreign read-only permission gate, refusal/consent/import deduplication, incompatible raw download, denial without scene, first named save with empty-name validation). The final recovery change also passes: local displacement survives loading revision 13 and can be saved as an owned copy. Offline receipt wording explicitly describes paused saving.

A responsive probe passed **50 layouts** (5 views × 5 widths 320/390/768/1024/1280 × 2 themes) and **40 modal fits** (4 scenes × 5 widths × 2 themes). No page errors or HTTP/HTTPS requests were observed in these probes or the interaction smoke. The measurement was rerun after its first selector incorrectly matched an outgoing closed dialog as well as the active AlertDialog; it now checks the active `data-open` popup. A separate initial smoke assertion expected “sin acceso al Taller” while actual copy says “Tu rol no tiene acceso al Taller”; correcting that expectation made the complete interaction smoke pass. Neither test-script failure was hidden as a pass or worked around by changing product behavior.

Four rendered screenshots were inspected in memory: desktop/light collection, phone/dark collection, desktop/dark conflict and phone/light import. The initial search icon overlapped the placeholder; the final entry uses a 44 px left inset. The masthead's duplicate new-project action was replaced with contextual collection navigation. No screenshot/log files were added. The direction-evidence probe validated **14 selectors**, with no missing evidence. Pairwise comparison with sibling directions was not run as part of this task. Expressive load exposed **10 active finite animations**; `?still=1` settled with **zero active animations** and the same content.

Production lint/types/build, database/authorization, cross-browser persistence, atomic conflicts, idempotent raw import and stale-response protection were **not run**: no production code was changed and the mockup has no service connection. These remain the plan's independent checks, not a reason to label this artifact as implemented.

## 12. Open questions, assumptions and impact

**Q: Does David want to select “Archivo de montajes”, with records unfolding inside the collection, as the SP-4 direction?** Decision owner: David, through the visual comparison. This is the only open owner choice identified in this exploration. No question reopens round-9 save mode, cross-browser payload or staff write restrictions.

Assumptions are illustrative only: Ana Torres/Luisa Rojas, 57 sample records, timestamps, revisions 12/13, room dimensions, eight chairs, raw JSON download sample and request delay. No real user data or secrets were read. The SVG is a schematic; the raw-download sample is mock data, not David's browser storage. The design does not add an import format or validation limit.

**Impact:** a potentially **breaking visual composition** if selected, with compatible behavioral requirements. SP-4 is the sole consumer of `proyectos@v1` in this snapshot: T4.1 will copy only the eventually approved canonical contract; T4.4 implements list, naming, state receipt, read-only/copy and conflict/recovery; T4.5 implements import; T4.8 re-renders the selected composition. T4.2/T4.3/T4.31 own storage/API prerequisites, T4.6/T4.7 the real browser integration evidence and T4.9 independent isolation/concurrency audit. CG-3 later checks the composition with accounts and Taller. This exploration changes none of those references or approvals.

Spanish UI copy follows the product; SP-8 owns complete bilingual production copy. Header navigation to the broader product and the real Taller engine belong to their existing surfaces. No repository preview, shared changelog, canonical contract, canonical HTML, plan or approval was written. The owner selection/finalization gate remains pending.
