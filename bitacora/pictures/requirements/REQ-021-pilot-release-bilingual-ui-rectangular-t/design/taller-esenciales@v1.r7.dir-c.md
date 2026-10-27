---
name: Molde de montaje
contract: taller-esenciales@v1
revision: r7
direction: C
status: exploration (not a contract, not approved)
seed: Tactile/playful — material and tool metaphors, direct manipulation, spring and press feedback
---

# Molde de montaje — direction C

Exploration for SP-3 (R9 rectangular tables, R10 GLB export to Blender, R11 Backing group). The shared behavioural
source is `taller-esenciales@v1.r7.behavior.md`; this note does not change it. Mockup:
`taller-esenciales@v1.r7.dir-c.html`, entry `taller-esenciales@v1.r7.dir-c.tsx`.

## Concept

A decorator assembles an event the way a workshop presses latex into a mould: every table type and every Backing prop
is a **silhouette slot** in one soft silicone mould, and the composition sits in a rounded scene well beside it.
Pressing a slot seats the piece at its default real size (rectangular 240 × 90 × 75 cm) and opens the existing
inspector; chairs fit independently around the table, a measuring line feeds under it, and the list and GLB export
read from the same mock model. The screen answers «what fits, at what size, and what do I need to bring?».

## Memorable move

**Press-in silhouettes.** The catalogue is not a card grid with images; each piece is its own outline pressed into a
rounded slot (round, square, oval, cocktail, half moon, serpentine, U, plus the seven Backing props). Hover lifts and
tilts the slot, press squashes its corners (border-radius changes with a spring), and the scene answers with a
latex-like snap of the table (squash → overshoot → settle) and chairs seating one by one.

## Why not the default

- No sidebar, no KPI tiles, no purple: colour logic is cool blue mould + cherry red action, with sunflower latex and
  foil pink only on scene materials. Dark theme is navy with high-contrast foil-pink actions.
- Type has character: rounded ExtraBold display (M PLUS Rounded 1c) for titles and the `.glb` object, Adwaita Sans
  for work text, tabular figures for measurements.
- Motion is a tactile grammar (squash/settle springs), not fade-up: different from sibling directions' quick cuts
  (A, teal/ruled registration) and spatial sweeps (B).
- Look ledger: `cuentas-admin r7 dir-c` (Mesa de pases) and `proyectos r8 dir-c` (Archivo de muestrarios) use pass
  counters and filed samples; this direction does not repeat their composition or navigation.

## Eight axes

| Axis | This direction (present in the mockup) |
|---|---|
| Concept | Reusable silicone assembly mould: silhouettes are push-in pieces around a real-scale composition, latex and foil outlines. |
| Layout | One broad mould `.work-mould` (1.25 : 1): scene well `.scene-frame` (64px radius) left, two-column `.slot-grid` right; ≤1050px tighter; ≤760px stacks with tools first, scene after. |
| Navigation | Four latch tabs `.mould-nav` (Mesas, Backing, Lista, Exportar) with a moulded active shape; adding a table enters the Inspector (Mesas stays current); «Tipos» returns. |
| Typography | Rounded Mplus 1c ExtraBold display clamp(36px, 4.4vw, 62px), 24–25px section heads, Adwaita Sans 14–15px body, 18–20px tabular measurements. |
| Density / shape | Generous: 28px mould padding desktop, 20px phone; slots 132px+ with 28/14px asymmetric radii; 44px+ targets; table rules for the list. |
| Components | Real shadcn/Base UI `Button`, `Input`, `Skeleton`, `Dialog` (scale & export help), Motion spring; custom SVG silhouettes and scene; native selects for table type, placement and language. |
| Colour | Light: `#e4eef4` ground, `#a11935` cherry action/selection, `#efcb56` latex, `#eab0bb` foil. Dark: `#15252e` navy, `#ff97ac` action. Project roles mapped once per theme. |
| Motion | Elastic fit-and-release: mould seats (620ms, overshoot cubic-bezier(.2,1.5,.45,1)), slots settle with 45ms offsets, balloons settle then float (4.2s, paused offscreen/hidden/hover), table snaps (720ms squash), chairs fit 35ms apart, measuring line feeds, Backing settles, status stamps, export crate rocks, skeleton breathes. Press/hover/focus 120–200ms. Subtle/natural profiles shorten; reduced motion and `?still=1` remove all animation with the same content. |

## Thumbnails

- **Candidate 1 — Molde de montaje** (`…dir-c.html.candidate-1.html`): one mould holding scene well and silhouette
  slots side by side. **Chosen.**
- **Candidate 2 — Banco de inflado** (`…dir-c.html.candidate-2.html`): an arched stage with a pump gauge for chairs and a
  bottom drawer tray of pillow pieces. Rejected: the bottom tray becomes a dock that hides measurements and the list on
  phones, and the gauge duplicates the inspector's chair count.

## Views and states covered

Views: Mesas, Inspector, Backing (search, seven props with dimensions), Lista de compras (quantities and dimensions,
no rental prices), Exportar GLB. States: Normal, Cargando (skeleton), Vacío, Error (retry, scene intact), Éxito,
Capacidad excedida (8 de 40 sillas; list counts placed chairs), Medida inválida (keeps last valid size), Sin permiso
(editing disabled). Dialog: «Escala y exportación» (cm → m). Language select previews English copy.

## Audit (actual results, 2026-10-27)

- Build: `bitacora.py components mockup build` → built offline (6440 KB, 2126 source files).
- `contrast.py`: 158 pairs checked in light and dark, all pass.
- `audit_mockup.py`: 180 renders, 8100 text measurements, 952 focus stops —
  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- `compare_directions.py` against r7 dir-a/dir-b: **not run** — their JSON notes did not exist yet. Run against
  r6 dir-a, r6 dir-b and this file: `ok: true`, layout similarity 0.018 / 0.023, no shared typography, navigation
  or motion; `evidence_ok: true`, every selector in the JSON found and every motion selector animated.
- Screenshots inspected at 1280 (light Mesas, dark Inspector + Capacidad, dark Lista) and 390 (light Backing,
  dark Exportar + Éxito).

## Limits and open questions

- The scene is a 2D composition illustration; the product keeps its 3D viewport. Silhouettes are custom SVG.
- Q: Should the table-type cards show the silhouette only, or also the existing 3D thumbnail when available?
- Q: Is a chair-placement select (alrededor / un lado / dos lados / cabeceras / frente al escenario) in scope for SP-3,
  or does the existing inspector already cover it unchanged?
- Q: Should the export view state the cm → m scale inline (as here) or only in the help dialog?
