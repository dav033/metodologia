# Pliego — archivo de montaje

Status: **draft exploration**, not the canonical proyectos@v1 contract and not approved for implementation. Revision: r10 / direction A. Sources: PLAN.json revision 1 and shared SP-4 digest 749be52ec4afc053. Subplan SP-4, R6/R7. Date: 2026-10-27. Owner decides the direction; Designer owns this bounded exploration only.

## Concept and memorable move

The working metaphor is a folded installation record. A project is the decorator's complete arrangement, with its owner and save state attached. The memorable move is an **in-place unfolding record**: selecting a project name opens a scene plate and a precise contents slip inside that row. Opening the actual project remains a separately named action. Silver foil seams, orange latex and the small balloon mark retain Pictures/Sempertex identity without adding a decorative dashboard.

This is the operational/editorial stance: dense names, owner metadata, timestamps and revisions; a serif noun at an asymmetric scale; precise lateral and folding sequences. The risk is concentrated in the editorial type, the cold-stock/signal-orange logic and the fold/register movement. Controls remain familiar and legible. It is not a safe SaaS default: no purple near-white treatment, equal card grid, ornamental metrics, generic hero illustration or repeating fade-up stack.

## Two thumbnails, then selection

- Candidate 1: `proyectos@v1.r10.dir-a.html.candidate-1.html`. A ruled, date-indexed collection with an inline scene/specification fold. **Chosen** because the scene's context stays attached to its owner and row, and the fold has a direct information-retrieval purpose.
- Candidate 2: `proyectos@v1.r10.dir-a.html.candidate-2.html`. A two-column cabinet index beside a permanent featured scene. Rejected because a persistent featured preview competes with the complete collection and repeats the static inspector composition already explored in other subplans.

Both candidates were authored before the full TSX; they are small compositions, not text-only direction lists. Their coarse objects are visual studies, not interaction prototypes.

## Look ledger and shared identity

Read the shared r10 behavioural source, SPEC round 9, PLAN/PLAN.json SP-4 and the current notes for cuentas-admin r10 A/B/C and taller-esenciales r9 A/B/C. The account directions already use a cobalt operational call sheet, a blue/yellow inflatable gate and petrol elastic knots. Taller explores registration-red measured drawings, orbital stage palettes and raspberry molded trays. Pliego uses a different serif/mono hierarchy, narrow left index, in-place record fold and source-ticket import, rather than their top route rule, orbital navigation, bottom toolbelt or 38% identity rail. A scene drawing and the balloon mark are intentional shared product objects; the composition and navigation are new.

## Eight-axis design table

| Axis | Observable choice |
|---|---|
| concept | A decorator's folded installation record: reopen the complete balloon installation, not a thumbnail detached from its ownership and save state. Foil seams and a ruled production register connect the working information to Sempertex materials. |
| layout | A narrow 154px index beside a broad continuous register. A large serif noun anchors the upper left; the named row unfolds in place into a scene plate and two-column contents slip. Taller uses a broad scene and narrow inventory; browser import is a source ticket beside consent. At 760px the index becomes three in-flow stations and record metadata reorders below the name. |
| navigation | A left in-flow vertical Archivo / En el Taller / Del navegador index, changing to a three-station strip on phone. Project names unfold context; separate Abrir/Consultar buttons enter the owned editor or foreign read-only view. No fixed bottom belt, orbiting palettes, carousel or permanent hero inspector. |
| typography | Embedded local DejaVu Serif Condensed Regular as Archive at 57–84px for the editorial noun and 25–36px for content headings. Embedded Adwaita Sans as Work at 13–19px carries actual project names and controls; embedded Liberation Mono as Measure at 11–14px registers dates and revisions. Dark graphite typography stays fully opaque during motion. |
| density | Compact 108px ruled metadata rows, an intentionally expanded first record, square 2px control corners and no project-card grid. Desktop main inset 38px and phone inset 20px; source ticket inset 26/22px, modal inset 28/24px. Actions meet a 44px minimum, with real names, owners, timestamps and revisions visible together. |
| components | Real installed shadcn/Base UI Button, Input and Skeleton; Animate UI Base UI Dialog and AlertDialog with explicit cancellation and focus management. Custom inline SVG scene plate, ruled project records, folded source ticket, foil seam and a native consent checkbox with authored checked/unchecked appearance in both themes. No HTML fallback kit. |
| colour | Proposed Pictures semantic role mapping: cold stock #e8eceb and #f8faf9, graphite #202c2b, signal orange #a43800 for the primary action. Dark evergreen stock #192522/#24332e, pale ink #f2f6f4 and peach-orange #ffb386 actions. Silver foil and orange latex belong to the illustrative installation. Production purple tokens are read-only and not changed. |
| motion | Mechanical fold/register grammar: cubic-bezier(.86,0,.14,1), expressive 640ms registration, 45ms row offsets, 180ms controls; title typesetting, lateral record sequencing, perspective unfolding, plate rise, table registration, latex seating, foil's seven-second stepped drift, rule extension, feedback stamp, source-ticket straightening, empty outline settlement, save rotation and scroll registration. Natural 420/150ms, subtle 220/120ms. Reduced/still removes travel, loops and transitions; offscreen/hidden suspension applies to ambient foil. |

## Source system and real component inventory

Both read-only repositories expose Pictures semantic tokens in `src/app/globals.css`, with `--fondo`, `--superficie`, `--texto`, `--texto-suave`, `--borde`, `--acento`, `--sobre-acento` and the existing shadcn aliases. The exploration maps those **same roles** to a proposed palette, once per theme; no production token or repository is edited. The existing purple is not treated as an approved exploration constraint, following explicit owner feedback. Future implementation requires owner selection of this proposal.

| Project role | Kit role | Light | Dark |
|---|---|---|---|
| fondo | background | #e8eceb | #192522 |
| superficie | card / popover | #f8faf9 | #24332e |
| superficie-2 | muted / secondary / accent | #dce2df | #31443c |
| texto | foreground | #202c2b | #f2f6f4 |
| texto-suave | muted-foreground | #485c56 | #c1d2c9 |
| borde | input / border | #71827b | #91a89b |
| acento | primary / ring | #a43800 | #ffb386 |
| sobre-acento | primary-foreground | #ffffff | #302016 |

Real installed components: `shadcn:button` (primary/secondary/plain, normal/disabled), `shadcn:input` (default/validation/disabled), `shadcn:skeleton` (loading), and Animate UI's installed Base UI Dialog/AlertDialog through `@/components/ui/dialog` and `@/components/ui/alert-dialog`. Imports and mounting use `@kit/mockup` and `@kit/motion`. Custom pieces: register rows, folding scene plate, SVG installation, source ticket, motion rules and native checkbox. No HTML snippet fallback; no package or asset fetching. Local DejaVu Serif Condensed, Adwaita Sans and Liberation Mono are embedded as data URIs. Lucide provides consistent stroke icons. The standalone file includes the exact authored CSS in the head as well as runtime style, so token and browser checks inspect the same palette.

## Views, navigation and behaviours retained

| View / native selector | Structure and main outcome |
|---|---|
| Archivo de proyectos / lista | Name search; own/all collection and authorized owner filter; named records with owner, date/time, revision and open/consult action; inline fold; load more; browser-import recovery entry. Default fixture is employee Marina's own collection. Foreign rows appear under Todos los proyectos and enter Consulta. |
| Taller / taller | Named personal project, explicit first named save, rename, visible saved/saving/pending/offline/conflict status and Guardar ahora; broad scene with complete-document contents; protected exit with pending work. The scene controls are bounded illustrative interactions, not a replacement design of SP-3. |
| Consulta ajena / consulta | Owner named before the scene; explicit Solo lectura explanation; no editing controls. Save owned copy requires taller.usar. The sin-taller state hides that action and explains consultation-only access, matching /proyectos/[id]. |
| Importar del navegador / importar | Source ticket, current destination account, shared-device warning, editable name and explicit unchecked consent. Import only after confirmation; Ahora no returns to the collection and leaves a recoverable entry. Unsupported data gets an explanation and raw-data download rather than an empty project. |

Planning selectors retain the native ids `view`, `state`, `scene`, `theme`, Spanish labels Vista/Estado/Diálogo/Tema and the visible Mockup label; Movimiento starts expressive unless reduced motion is requested. Four dialog scenes are separately inspectable: naming/copying, version conflict, confirm loading the saved version and leaving with pending changes. The template's native selectors remain outside the product.

Functional source of truth is unchanged: /proyectos lists server-authorized metadata, owned editing enters /3d?proyecto=<uuid>, and foreign consultation enters /proyectos/[id]. First save explicitly asks for a name; later edits autosave with the Planner's 500ms serialized debounce. Save now is always identifiable. Responses acknowledge only their submitted generation; stale completions cannot mark later work saved. Search and authorized owner filters apply over the **whole server collection before pagination**, reset cursors on changes and reject obsolete responses; a next-page failure preserves visible rows and offers retry. The static demo filters its finite fixtures locally and adds one example next-page row. It does not claim to demonstrate the server query, authorization or cursor implementation.

On 409, saving stops and local changes remain. The conflict dialog offers an owned copy or server-version load; loading requires AlertDialog confirmation and preserves a recovery draft. Pending exit offers save/continue, keep a namespaced local draft/exit, or cancel. Offline/conflict prevent save/continue. In production a project or account switch must clear scene/conversation identity and caches; another account must never see previous drafts. The mockup's fixture memory is ephemeral, with no authentication or real persistence.

Only the name and complete project-document@1 scene travel across browsers: room, environment, salon, materials, node relationships and references. AI conversation and generated images stay in the browser. Nothing adds deletion, ownership transfer or version-history UI. A revision shown in the list is metadata, not a history browser.

Legacy import remains explicit for the current account on the first permitted authenticated Taller visit. Server validation and account plus original-source-hash deduplication prevent duplicates after response loss, retries, reloads or two tabs. The legacy key remains unchanged; separate receipts follow server acknowledgment. The example download is visibly an **original of the fixture**, not any real person's browser file. No source data is read, uploaded or deleted by this exploration.

## State reachability

All states are selectable in the native Estado control; relevance is contextual. A state that does not apply to a view leaves that view in its normal form rather than inventing a new product behaviour.

| Native state | Applicable rendering and recovery |
|---|---|
| normal | Working list, owned editor, foreign consultation or unchecked import consent. |
| cargando | List, scene or import skeleton; submission and duplicate actions disabled. |
| vacio | No projects/no query match; empty scene; no local source. Each has a named next step. |
| error | First-page, project-open or import failure; originals/drafts retained; retry or download. Naming scene also exposes a failed-save explanation. |
| guardado | Acknowledged-save fixture; list receipt; import receipt and open imported project. |
| guardando | Owned-save status and disabled repeat submit; import submission disabled. |
| pendiente | Owned-save status plus Save now; navigation guard. |
| sin-conexion | Owned local-draft banner, save retry without a false saved label; import failure preserving source. |
| conflicto | Owned autoguardado detenido status; resolution, copy and confirmed server load. |
| sin-permiso | No scene or project metadata; return to own collection. |
| sesion | No scene contents; same-account sign-in recovery explanation. |
| incompatible | Original-preservation explanation and fixture download; import disabled. |
| validacion | Naming dialog error and import name/unchecked-consent validation. |
| error-pagina | Existing collection remains visible; retry following page. |
| sin-taller | Consultation works; editing and owned-copy actions absent. |

No selected state implies that security or persistence is enforced in static HTML. A regular account's production list must omit staff scope/owner filters; the supplied collection fixture is explicitly an employee with those permissions. No new permissions are introduced.

## Responsive and accessibility targets

Above 1100px: 154px index, 38px main inset, five-part row and two-column fold. From 761–1100px: 130px index, 28px inset, revision is supporting metadata and may be omitted from the compact row; filter name spans the first line. At ≤760px: in-flow three-station navigation, 20px outer gutters, 57px display title, metadata and open action below the name; scene/specification fold, editor and import stack. No horizontal page scroll or gesture dependency. Dialogs use viewport-relative bounds and internal overflow; cancellation remains reachable. Screens must also tolerate long localized project names; full EN translation belongs to the later language subplans and is not claimed complete here.

Targets: WCAG 2.2 AA text contrast ≥4.5:1, control/focus contrast ≥3:1, visible 3px focus with 4px offset, semantic labels and current navigation state, native search/select/checkbox operation, aria-expanded names, polite save receipts and alert recovery errors. Buttons are at least 44px high. Base UI handles modal inertness/focus containment; manual checks must verify closing and return focus. Confirmation uses AlertDialog. Checkbox rendering is authored in both themes, including the checked mark, avoiding browser-dependent invisible edges. The scene is a labelled illustrative SVG; all quantities are also text.

Motion remains fully opaque: transforms do not fade text through unreadable intermediate frames. Six or more different behaviours are implemented, not just described: title registration, lateral row sequence, perspective fold, scene-plate rise, table registration, latex seating, foil drift, dashed seam extension, status stamping, source-ticket straightening, empty outline settlement, save rotation and scroll-position line. CSS profile tokens control 640/420/220ms sequencing and 180/150/120ms interactions. Ambient foil pauses when the document is hidden and its drawing is offscreen. OS reduced motion, Quieto and ?still=1 remove animations/transitions while keeping final content, focus and actions intact.

## Observable design checks if this direction is chosen

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| A-01 | 1280px | normal/lista | A narrow left index precedes the continuous record; the first project unfolds inside its own row. |
| A-02 | 390px | normal/lista | Navigation, filters, owner and Abrir action remain within the viewport; the drawing precedes its text inventory. |
| A-03 | 390/1280px | error-pagina/lista | Visible rows remain present and Reintentar siguiente página is available. |
| A-04 | 390/1280px | conflicto/taller | Autoguardado detenido is visible and Guardar ahora is disabled; resolution exposes the two choices. |
| A-05 | 390/1280px | sin-conexion/taller | The status calls the work a local draft, with no saved-in-account claim. |
| A-06 | 390/1280px | normal/consulta | The owner and Solo lectura appear before the scene; no editing control is shown. |
| A-07 | 390/1280px | sin-taller/consulta | Guardar copia is absent and consultation-only access is explained. |
| A-08 | 390/1280px | normal/importar | Destination Marina Solano and shared-device warning appear before unchecked consent; import is disabled until name and consent are supplied. |
| A-09 | 390/1280px | incompatible/importar | The original download is available and importing is disabled; no empty scene substitutes for invalid data. |
| A-10 | 390/1280px | cargar dialog | A separate confirmation names scene replacement and local-draft preservation; Cancel remains reachable. |
| A-11 | 390/1280px | dark/all | Native field/checkbox boundaries, body text and keyboard focus remain visibly distinct. |
| A-12 | 390/1280px | reduced/all | Every view shows final content immediately; no running finite entrance animation or ambient loop remains. |

## Verification evidence

- Offline real-library builder: exit 0, 2,596 KB before authored-CSS mirroring, 2,135 bundled source files; no install or asset fetch. Exact final standalone HTML is 4,741,676 bytes. Entry: `proyectos@v1.r10.dir-a.tsx`; output: `proyectos@v1.r10.dir-a.html`.
- `python3 .../kit/contrast.py proyectos@v1.r10.dir-a.html`: **contrast: 158 pairs checked in light and dark, all pass**, exit 0. The authored palette is present in head CSS, so these measurements use this direction's role values.
- `UV_OFFLINE=1 uv run --offline --with playwright python .../kit/audit_mockup.py proyectos@v1.r10.dir-a.html --max-combos 304`: **304 renders / 304 planned**, 11,100 text measurements, 598 keyboard focus stops; 1280px and 390px, both themes, all four views, all fifteen states and all four dialog scenes; exit 0. No combinations were sampled away.
- **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**
- `compare_directions.py` on the current r10 A/B/C HTMLs with `--json`: exit 0, `ok: true`, `evidence_ok: true`, no missing selectors. A/B layout similarity .007; A/C .003; B/C .050. All pairs differ in measured typography, navigation and motion. The result verifies measurable distinction, not owner preference or approval.
- **INTERACTION RESULT: PASS — 12 checks**: unnamed draft, name validation, explicit first save, pending-exit/cancel, conflict stop/confirmation/recoverable draft, foreign consultation/copy permission separation, consent/import receipt, unsupported source/download, staff filtering/consultation, next-page retry retaining rows, offline edit/retry without a false saved label, and all-view reflow at 360/390/768/1024/1280px in both themes. No page errors or HTTP(S) requests were observed. These are fixture interactions, not persistence/API tests.
- **MOTION EVIDENCE: 8 distinct running CSS animations** observed together: foil-register, type-register, record-register, unfold, plate-register, balloon-register, table-register and rule-register.
- **MOTION/MODAL RESULT: PASS**: ?still=1 and ?rm=1 have no running animations after 150ms; all 16 dialog/theme/width combinations remain inside 390/1280px viewports and contain keyboard focus after Base UI's focus guards settle. Denied consultation hides the foreign owner's metadata. A first focus-loop probe sampled the guard synchronously; waiting for its scheduled focus return confirmed the installed focus trap, with no product-code workaround.
- **IMPORT NAME RESULT: PASS**: a custom import name survives the receipt and opening the imported project.
- **ENTRY TYPECHECK: PASS**: in-memory strict/noEmit diagnostics for this entry, installed dependency aliases, skipLibCheck. This is not a production workspace typecheck.
- Visual inspection used in-memory rendered captures, without writing extra files: desktop light archive, phone light archive, phone dark import and checked-consent/action/footer segment. The footer follows the form's inset; checkbox check/fill/edge remain distinct in dark mode. The original thumbnails are retained as the permitted visual evidence.
- Final HTML SHA-256: `0d1dce11f823c34eb9da3ebf29120d9b4a0b44f55026cf25a7becbc07cb80fa8`.

Honest correction trail: the first sampled audit failed on one tight navigation inset and a long preview label causing phone overflow; both were fixed. The first full audit identified status-content alignment cases in the session-ended fixture; expanding the notice content to the full working column resolved them. A click-through also found the fixture runtime remount losing an appended next-page row; fixture continuity was corrected and its retry test now passes. All reported final checks above passed; earlier failures are not hidden as passes.

No production code, repositories, database, API, authentication, real import or integration harness was exercised or changed. Security, cross-browser storage, full-document fidelity and idempotency remain requirements for T4.2–T4.7 and the independent T4.8/T4.9 acceptance cycle.

## Open decisions and scope

Q: Does the owner select Pliego's cold-stock/orange register, serif display and in-place fold for finalization, or choose another exploration? This is the only open direction decision; R6/R7 behaviour and round-9 choices are retained, not reopened.

All people, company/event names, quantities and dates are illustrative. Complete-scene and raw-data preservation are implementation requirements, not proven by a static SVG or fixture memory. The local preview does not call persistence/auth APIs, validate scene schemas, implement real autosave or prove cross-browser concurrency. No contract is approved here.

Impact if chosen: T4.1 copies only the later owner-approved canonical artifact; T4.4 consumes list/save/consult/conflict/pending-exit layouts; T4.5 consumes import/invalid/receipt layouts; T4.8 reviews rendered fidelity. T4.2/T4.3 remain the data and API owners; T4.6/T4.7 verify real persistence and authorization. Compatibility is **undetermined until owner choice and canonical finalization**. This direction cannot replace an approved consumer input by itself. No shared contract, PLAN, repository or other direction was edited.
