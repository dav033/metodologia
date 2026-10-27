---
name: Molde — piezas a presión
status: draft
kind: direction-exploration
contract_ref: taller-esenciales@v1
subplan: SP-3
requirements: [R9, R10, R11]
revision: r9.dir-c
chosen_thumbnail: taller-esenciales@v1.r9.dir-c.html.candidate-1.html
---

# Molde — direction C

This is an unapproved independent exploration, not the canonical contract. It preserves the shared behavioural source and leaves all shared contracts, plans, history and production repositories unchanged. The owner selects the direction before a separate finalizer authors the twelve-section contract.

## Concept, memorable move and why not default

Event decorators work with shaped pieces, soft latex, folded cloth, foil and tools. Molde turns the working surface into a molded packing tray: each object has its cavity, a table lands with its chairs, and the four working destinations seat in a lower toolbelt. The memorable move is the table and its chairs compressing into place while the specification tag unfolds next to them. Buttons press with material resistance; an optional horizontal table drag settles on the installed spring, with explicit left/right alternatives.

The composition is a working overhead assembly plane and a molded toolbelt, not a generic dashboard with navigation at the left. Large italic serif letterforms introduce a sculpted voice; raspberry and plum come from balloon material rather than the default purple SaaS palette. Decorative colour is confined to the scene/parcel materials; colour also names success, warning and error. Every warning includes words.

## Thumbnails drawn first

1. **Chosen:** `taller-esenciales@v1.r9.dir-c.html.candidate-1.html` — wide scene plus specification tag and lower toolbelt. It gives the scene room and leaves a predictable place for numeric editing.
2. `taller-esenciales@v1.r9.dir-c.html.candidate-2.html` — orbit of circular tool pucks around a circular scene. Kept as an exploratory composition; its navigation consumed space needed by dimensions and longer Spanish labels.

Both are self-contained visual thumbnails with theme switches and phone reflow. They are sketches, not representations of installed shadcn components. The full direction uses the actual installed toolchain without a fallback.

## Eight axes

| Axis | Observable design |
|---|---|
| concept | Molde: a decorator presses, seats and packs event pieces in a molded tool tray. Latex and foil inform the rounded cavities, table silhouette and responsive press feedback. |
| layout | A wide overhead scene occupies the upper left, a specification tag seats at its right, and an eight-shape cavity tray follows below. Backing becomes a broad specimen tray, the shopping list a quantity-first packing slip, and export a two-part parcel. At 700px these planes stack; the four-tool belt stays near the bottom. |
| navigation | A fixed lower four-station molded toolbelt selects Tables, Backing, List and Export. Table cards add at default dimensions and enter the inspector immediately; inline Return and Undo keep the working context. A separate help dialog explains Blender import; native planning selectors remain outside the product. |
| typography | Embedded local FreeSerif Bold Italic at 54–88px gives the working title a sculpted, compressed silhouette; embedded Liberation Sans at 13–26px handles labels and data. Quantity-first packing numerals use the expressive serif at 38–45px. This pairing differs from sibling condensed and rounded sans directions. |
| density | Generous scene field and 26px inspector insets, four 20px-inset cavities across desktop and two 16px-inset cavities on phone. Working controls have at least 44px targets; selection, capacity and next action remain explicit text. No KPI dashboard or ornamental metrics. |
| components | Real installed shadcn/Base UI Button, Input and Skeleton; Animate UI Base UI Dialog primitives, Motion drag and profile springs. Custom SVG table/balloon/prop silhouettes, molded toolbelt and packaging composition. Existing pure table normalization, contours, chair placement and repository ownership are bundled read-only from Pictures. |
| colour | Proposed raspberry #a20c48 actions on pink packing material #f4dfe7, dark plum #381526 ink, foil #c79750 restricted to decorative material. Dark plum ground #28131f and #3a2030 surfaces use pale rose #ffc0d7 actions and #fff1f7 text. Existing Pictures semantic roles map onto kit roles; purple production values are not silently changed. |
| motion | Press-and-seat grammar with cubic-bezier(.18,1.38,.48,1), expressive 720ms plane/label choreography and 180ms controls; tray perspective seating, italic type compression, label torsion, staggered cavity/chair clips, toolbelt engagement, parcel unrolling, ambient latex breathing, error pressure release, success stamp and interruptible direct dragging. Natural 460/160ms, subtle 260/120ms; reduced/still has immediate parity. Ambient effects pause offscreen and in hidden tabs. |

## Look ledger and shared identity

Read sibling direction notes and JSON for `cuentas-admin@v1.r10.dir-a/b/c` and `proyectos@v1.r8.dir-a/b/c`: production register, inflatable entrance, tension bands, unfolding archive, stage ribbon and sample folders. Molde preserves Pictures, the linked-circle mark, event vocabulary, metre labels, explicit recovery and usable controls. It does not repeat their left identity rig, permission bands, folder tabs, project ribbon, or top station conveyor. The planning toolbar is intentionally identical because the comparison host drives its native selectors.

## Sources and actual library use

Read SPEC.md, PLAN.md, SP-3/tasks from PLAN.json and the shared r9 behavioural source. Shared behavioural source SHA-256: `4113589a9342573e5a6a3e16661117ce6e982908a43a9736aad8b12c1540846f`.

Read-only repository inspection covered both t12 and asesor `globals.css`, existing table editor, furniture creation, parametric types/defaults/limits, chair placement, Backing catalogue and explicit repository assignment. Both repositories use `--fondo`, `--superficie`, `--texto`, `--texto-suave`, `--acento`, `--sobre-acento`, `--borde` and Taller roles. This exploration maps their responsibilities onto `--background`, `--card`, `--foreground`, `--muted-foreground`, `--primary`, `--primary-foreground`, `--input` and `--ring`. The proposed raspberry/plum values are local design proposals responding to owner feedback, not claims about current production values. Text target is 4.5:1, control edges/focus 3:1. No native checkbox is used.

Actual imports: `shadcn:button default/outline/disabled` (`@/components/ui/button`); `shadcn:input default/invalid/disabled` (`@/components/ui/input`); `shadcn:skeleton loading` (`@/components/ui/skeleton`); installed `@animate-ui/react/primitives/base-ui/dialog` for keyboard containment, inert background and dismiss/focus return; `motion/react` for drag feedback; `@kit/motion` for profile spring and reduced state; `mountMockup` / `useMockup` from `@kit/mockup`. Custom components are the molded tray/toolbelt, SVG schematic, quantity slip and export parcel. No package installation, network asset or snippet fallback.

FreeSerif Bold Italic and Liberation Sans Regular are local installed fonts embedded as data URIs in memory. Build output is self-contained. The same entry CSS is also embedded in a static `<style data-direction="c">` after the offline build so the static contrast checker measures the proposed role mapping, not only the bundled kit defaults.

## Behaviour and reachable views

| View | Preserved outcome |
|---|---|
| Mesas | One creation card per existing parametric type: round, square, rectangular, oval, cocktail, half-moon, serpentine and U. A card immediately adds the table at PARTIDA_MESA dimensions and opens its inspector. Rectangular starts at 2.40 × 0.90 × 0.75m. No pre-creation form. Fixed Imperial pieces remain in their established catalogue. |
| Inspector | Default selected rectangular table, metres in controls/model conversion to centimetres, length/depth/height constraints, 0–40 requested chairs, actual placed quantity/capacity, seven existing chair types and five dispositions. A forty-chair fixture demonstrates the warning. Table/chairs move and rotate together; undo restores the previous local model. The SVG uses real table contours and chair coordinates, not invented chair totals. |
| Backing | Exactly seven original IDs: panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal, arco_metalico. Search accepts familiar names, IDs and Backing. The repository filter uses the real ASIGNACION_FONDOS map (all seven currently belong to escenografia). Each appears once and can be added. No Shopify products or catalogue aliases are invented. |
| Shopping list | Quantities and dimensions of tables and actual placed chairs, followed by added Backing quantities and source dimensions (largest arch/blue pedestal identified when describing a set). No rental prices. Capacity truncation is reflected in the count. |
| Export | Complete-scene GLB intent, metres, base colours, positions and editor-only light/control exclusion; explicit idle, preparing, empty-disabled, retryable error and success. Help gives Blender glTF import steps. The simulation does not generate or validate a GLB. |

Sample project: Cumpleaños de Lucía. Initial fixture: one rectangular table, eight chairs, no placed Backing; the three balloons at the top of the schematic are a decorative material study, not counted scene objects. All values remain local mock data. Table normalization, contour, actual chair placement and repository mapping come from the inspected repository as read-only imports. AI tool parity, saved IDs/search/photo compatibility, world-space GLB export, real Blender import and undo in production remain implementation/integration responsibilities (T3.2–T3.6); this mockup does not claim to verify them.

## States, navigation and recovery

The visible native selectors are Vista `view`, Estado `state`, Diálogo `scene`, Tema `theme` and Movimiento `motion`; default motion is expressive. A product language select demonstrates Spanish/English copy reflow. The lower toolbelt routes Mesas / Backing / Lista / Exportar; the inspector is entered by adding a table, the Edit table action or the planning selector.

State selector: normal; structural loading/preparing; empty/no results; retryable error; success; capacity-insufficient; invalid size; scene piece limit; offline. Loading substitutes structural Skeletons and announces progress. Empty inspector/list/export expose a next action and export stays disabled. Empty scene on the table catalogue keeps creation cards available. Backing no-results clears search and repository filters. Errors preserve local data and retry. Capacity warning says requested/capacity/placed separately; invalid size preserves the last valid value. Piece limit refuses additions without partial objects. Offline preserves editing and local export while remote catalogue discovery is disabled. Unrelated global fixtures retain the normal local content rather than inventing permissions or remote state. Authentication/permission denial belongs to SP-2, and server persistence/conflicts to SP-4; they are not newly introduced here.

Every help dialog is independently reachable through Diálogo and the product Help/Open in Blender controls. It closes with Escape or Got it, isolates the background and uses reduced/profile-aware transitions. No essential action depends on dragging. Explicit move buttons are in the position disclosure; Tab and Enter operate all destinations and creation controls.

## Responsive and accessibility expectations

Desktop above 1000px: 40px outer gutters, 1.65:1 scene/inspector plane, four-column object cavities. Between 701–1000px: 26px gutters, 1.2:1 plane, three-column cavities and stacked inspector dimension controls. At 700px and below: 20px outer gutters, scene then inspector, two-column cavities and compact icon/text lower toolbelt. At 370px and below: single-column cavities and dimension fields. No page horizontal scroll; labels wrap. The bottom page padding leaves room for the fixed toolbelt; the help dialog is bounded by the viewport and scrolls internally.

Targets: WCAG 2.2 AA text and control contrast, 44px working targets, visible 3px focus outline, semantic headings/labels, polite change announcements, assertive warnings and error recovery. Decorative SVG is hidden where appropriate; the schematic has a scene description. Under prefers-reduced-motion, still=1 and the Quieto profile, travel, spring settling, infinite breathing and transitions are removed while the final information and actions remain. Hidden-tab and IntersectionObserver suspension pause ambient work. Entry motion uses transforms without making text transparent, keeping intermediate frames readable.

## Visual acceptance examples for finalization

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-01 | 1280px | normal / Mesas | Broad scene and specification tag share one upper row; four table-shape cavities fit below. |
| C-02 | 390px | normal / Inspector | Scene, tag and lower toolbelt fit the viewport with 20px product gutters and no horizontal scroll. |
| C-03 | all | normal | Rectangular creation goes directly to its 2.40 × 0.90 × 0.75m inspector. |
| C-04 | all | capacity | Requested forty, real capacity and placed quantity are separately visible; shopping list uses placed quantity. |
| C-05 | all | normal / Backing | The seven original IDs appear once; filtering by Mobiliario gives no Backing results under the inspected assignment. |
| C-06 | all | loading / Export | Structural placeholders and preparing text replace the editable/export action area. |
| C-07 | all | error / Export | Error says the scene is intact and provides retry. |
| C-08 | both themes | keyboard | Controls gain a contrasting 3px outline; help traps focus and closes with Escape. |
| C-09 | all | reduced / still | Titles, trays, labels and scene reach the same final position without ongoing animation. |

## Honest audit evidence

- Offline real-library builder: pass, 1,989 KB bundled HTML before duplicate static role stylesheet embedding; no fallback. The final self-contained HTML includes embedded fonts and the identical static role CSS.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass`.
- Completed first full corrected audit: 200 renders / 200 planned combinations, 6,616 text measurements and 786 focus stops at 1280/390 in both themes.
- `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- A subsequent reduced-motion interaction check exposed hover transforms despite immediate transitions. Those transforms were removed under reduced/still, and the final full audit was rerun; its final measurements are recorded below.
- Interactive browser smoke: pass for eight type cards, rectangular creation/default inspector, actual forty-requested/ten-placed chair fixture and list quantities; seven Backing cards, ID search and repository filter, add/move/rotate/undo, modal/Escape, English switch and simulated export success. No console errors and no external requests.
- Rendered screenshots inspected at 1280 light Mesas, 1280 dark Export, 390 light Backing and 390 dark Inspector. The phone layouts stack and preserve readable edges; the fixed belt has page-bottom clearance.
- Final audit after the reduced-hover correction: 200/200 renders, 6,616 text measurements, 786 focus stops. `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- Additional responsive check: twenty English normal-view combinations at 320/768px in both themes passed without horizontal overflow or console errors.
- Full `compare_directions.py A.html B.html C.html --json` executed after all three sidecars existed. All pair geometry/distinctness checks passed: A/B 0.006, A/C 0.019, B/C 0.024 layout similarity; typography, navigation and motion differ for every pair. Every C selector claim was measured successfully, including all six animated selectors.
- **Global comparator exit 1 / FAIL:** `evidence_ok: false`, solely `taller-esenciales@v1.r9.dir-a.html: .chapter` missing evidence. This is an A-owned selector issue; no A/B file was edited. The earlier attempt before B wrote its sidecar returned `COMPARE NOT RUN` for the missing B JSON; the completed comparison above supersedes that attempt. Do not report global comparison as passed.

## Impact, questions and approval

Consumers remain SP-3 ui contract version 1, design task T3.1, implementation T3.2/T3.3/T3.4, visual review T3.7 and audit T3.8. No consumer is redirected. Compatibility is **undetermined until selection/finalization**; this composition changes hierarchy, navigation, shape, tokens, typography and motion and will need explicit implementation/review if selected. It does not authorize a production redesign outside SP-3.

Q: If Molde is selected, should its raspberry/plum palette and serif display stay local to Taller, or become a shared identity proposal for later admin/project finalization? Decision owner: David; no cross-subplan change is made here.

Confirmed owner decisions are not reopened: per-type default creation, actual chair counts, no rental prices, one Backing group retaining IDs/discovery and existing GLB verified in real Blender. Direction choice and canonical contract finalization remain pending.
