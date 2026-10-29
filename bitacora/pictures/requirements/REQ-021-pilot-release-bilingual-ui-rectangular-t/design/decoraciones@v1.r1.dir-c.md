---
contract: decoraciones
version: 1
status: draft
subplan: SP-5
requirements: [R8]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: c
name: Manipulación directa
source_revision: r1
source_behavior: decoraciones@v1.r1.behavior.md
---

# Manipulación directa — decoraciones@v1 · r1 · C

**Exploration only; draft, not approved and not an implementation contract.** This note accompanies
`decoraciones@v1.r1.dir-c.tsx`, the built `decoraciones@v1.r1.dir-c.html`, two candidate thumbnails and the axis JSON.
It does not write the canonical `decoraciones@v1.md`/`.html`, SPEC, PLAN or any repository. The owner chooses among
directions; a finalizer writes the twelve-section contract afterwards.

## Scope and existing surface

Scope: the UI brief `decoraciones@v1.r1.behavior.md` (R8 and SPEC «Behavior — SP-5 (round 11 answered)»). Existing
surface, located read-only in `pictures-wt/asesor`:

- `src/components/tres-d/Biblioteca.tsx` — `AccionesPieza` in the inspector: «Ver sola / Ver con sus decoraciones»,
  «Guardar en mi biblioteca», the link «Guardar toda la escena en mi biblioteca», inline form Nombre + Ocasión + Guardar
  and the status line «Guardado en tu biblioteca: «X» (tipo).». Persistence today is `taller3d:biblioteca-propia:v1`
  in `localStorage`. `FichaDialogo`/`Ficha`: «Abrir en Escena», «Añadir a mi escena», «Quitar de mi biblioteca»,
  «De dónde viene», products, «Volver a la biblioteca».
- `PanelAnadir.tsx` — «Añadir a la escena» panel with search and the segments Estructuras · Decoraciones · Utilería ·
  Ideas; own items are mixed into those tabs with the source label «Tu biblioteca» (`GrillaCompacta.tsx`).
- `MenuContextual.tsx` «Guardar en mi biblioteca» and `MenuMas.tsx` «Guardar la escena en mi biblioteca…» (same form).
- Tokens: `src/app/globals.css` (`--fondo`… and `--taller-*`), Geist/Geist Mono; shell, masthead, route navigation,
  workshop header and token mapping reused exactly from sibling `proyectos@v1` (chosen direction C) and
  `cuentas-admin@v1`/`planes@v1`. No new palette, font or brand.

## Approach — how this direction changes the surface

The changed controls are manipulated where they already live:

1. **Save in place.** «Guardar en mi biblioteca» in the inspector unfolds the existing form inside the inspector (no
   dialog). The form adds one destination line: «Se guarda en tu cuenta: la verás en «Mi biblioteca» desde cualquier
   navegador.» Guardar → «Guardando…» (disabled) → receipt «Guardado en tu biblioteca: «Arco» (estructura con
   decoraciones).» with «Ver en Mi biblioteca», which moves focus to the new row. Error/offline/session receipts keep
   the name and occasion and offer «Reintentar» or «Iniciar sesión».
2. **«Mi biblioteca» as a fifth segment** of «Añadir a la escena» with an account count. Personal saves are a separate
   group from the Taller catalogue (SPEC: separate from the global catalogue). Rows are compact; tapping a row expands
   it in place (one at a time) to a 3D-view placeholder, globos/piezas and actions: «Añadir a mi escena» (primary),
   «Abrir en Escena», «Ver ficha». Owner-only tools sit under a rule: «Cambiar nombre» turns the name into a field in
   place (Enter confirms, Escape cancels, empty → «Escribe un nombre para la decoración.»), and «Quitar de mi
   biblioteca» opens a real AlertDialog.
3. **Drag to place.** Own and local rows are draggable onto the viewer (dashed accent drop target); «Añadir a mi
   escena» is the equal keyboard/touch alternative. Placement confirms «Añadida a tu escena: «X».» in the viewer.
4. **Browser-local entries stay local.** A collapsed dashed group «En este navegador · 2» explains «Guardadas antes en
   este navegador. Siguen aquí y no se pasan a tu cuenta en el piloto.» No import control exists.
5. **Staff read-only.** For employee/administrator a native «Biblioteca de» selector picks another account. Its rows
   show «Solo lectura» and only «Ver ficha»; the ficha shows a read-only banner and no rename/remove/place actions. A
   refused mutation (direct API) has the state «No se cambió nada · Solo la cuenta dueña puede cambiar o quitar esta
   decoración.»
6. **Account switch.** Sign-out/switch empties the list and shows skeletons with «Cambiaste de cuenta · Las
   decoraciones de la cuenta anterior ya no se muestran.» before the next account's items.

## Interaction and motion detail

Tactile press/settle, finite and legible (content never hidden mid-animation; transform only):

- rows settle on load (translateY 8px, scale .985 → 1.004 → 1, 45ms stagger); a just-saved row drops from −14px and
  settles; the opened row's thumbnail seats .9 → 1.04 → 1; the detail and the save form unfold with scaleY
  .92 → 1.012 → 1 from the top edge; the rename field seats scaleX .95 → 1.012 → 1 from its text edge;
- the receipt icon rotates −16° → 6° → 0; the «Mi biblioteca» count bumps 1.3 → .92 → 1 after a save; the placement
  chip drops and settles in the viewer; buttons/rows press to .96–.975 (row and rename use `motion.button` with the
  profile spring);
- profiles: expressive 480/160/45ms, natural 300/130/25ms, subtle 150/90/10ms, easing cubic-bezier(.3,1.45,.6,1);
  Quieto, `?still=1` and OS reduced motion remove all animation and transition while keeping every word and control;
  hidden tabs pause CSS animation.

## Why it fits the existing product

It keeps the save form, its copy, the inspector placement, the «Añadir a la escena» panel and the ficha that users
already know, and changes only what R8 needs: destination (account, not browser), a place to find the account library,
owner-only controls and read-only access. It uses the same in-context grammar the owner chose for `proyectos@v1`
(«Edición en contexto»), so the Taller feels like one product. Drag-to-viewer already exists for «Nuevas» cards
(`PanelAnadir.tsx` `TarjetaNueva`).

## Eight axes

| Axis | This direction |
|---|---|
| concept | Manipulación directa: guardar en el inspector, y abrir/renombrar/quitar/arrastrar cada decoración desde su propia fila. |
| layout | proyectos@v1 workshop shell: rail 60 · Añadir panel 300–340 · viewer · inspector 280; tablet inspector full width below; phone stacked, order by task. |
| navigation | Inherited masthead/route nav; panel segments with «Mi biblioteca» + count; single-open rows (aria-expanded); «Ver en Mi biblioteca» focus jump; staff «Biblioteca de» select. |
| typography | Geist: 24 title, 15 panel, 14/600 row name, 12 meta; Geist Mono 12 for counts. |
| density | 64px rows, one expanded; local group folded; short inspector form. |
| components | shadcn Button/Input/Skeleton/Dialog/AlertDialog (Base UI), motion.button, native selects/details, draggable rows with button alternative. |
| colour | Pictures/Taller tokens only; accent on primary action, open row and drop target; success/error on receipts. |
| motion | Press/settle: row-settle, row-drop, mini-seat, detail/form unfold, field-seat, status-seat, count-bump, place-settle; reduced parity. |

## Views, states and dialogs in the mockup

- Vista: «Taller 3D · Guardar pieza» (`taller`), «Taller 3D · Mi biblioteca» (`biblioteca`), «Personal · Biblioteca de
  otra cuenta» (`personal`).
- Estado: normal, loading, empty, load-error, saving, saved, save-error, offline, rename (empty name), placed, legacy
  (browser group open), forbidden, switching, session-expired.
- Diálogo: ficha (own / local / foreign read-only), quitar (AlertDialog «¿Quitar «X» de tu biblioteca?» — «Se quita de
  tu cuenta en todos los navegadores. Lo que ya añadiste a tus escenas se queda en ellas.», «Conservar» / «Quitar de
  mi biblioteca»).
- Breakpoints: ≥1100 four columns; 640–1099 inspector below; <640 stacked; 20/24/40px gutters as in proyectos@v1.
- Mock data: neutral «… de ejemplo» names, «Cuenta de ejemplo», illustrative globos/piezas counts; occasion names
  from the existing taxonomy (General, Cumpleaños, Cumpleaños infantil, Baby shower, Boda). The 3D views are inline
  SVG placeholders.

## Thumbnails

- **Candidate 1 — chosen** (`decoraciones@v1.r1.dir-c.html.candidate-1.html`): in-place save in the inspector and
  expandable rows in a «Mi biblioteca» segment of the existing panel. It stays on the current surface and keeps every
  action reachable by keyboard.
- Candidate 2 (`…candidate-2.html`): a library tray docked under the viewer with a drop slot for saving. More
  spatial, but it adds a new region the product does not have and makes saving depend on dragging; rejected.

## Audit (actual results on this output)

- Build: `components mockup build` exit 0 — 660 KB, 2,135 source files, offline; real shadcn/Base UI/Animate UI.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass` (also for both thumbnails).
- `audit_mockup.py` (default 1280/390): first run `RESULT: FAIL — contrast 1, padding 1` (save-form description
  4.24:1 in dark; skeleton row padding). Fixed (text token `--texto-suave`, padding 12/14). Final: 192/192 renders,
  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- `audit_mockup.py --widths 1280,390,768`: 288/288 renders, same PASS; warning «1 focus walks stopped at 60 stops;
  later controls were not checked».
- Interaction probe (inline Playwright, no files kept besides /tmp screenshots): save → «Guardando…» → receipt and new
  row (count 3→4); empty rename shows the error, Escape returns focus to «Cambiar nombre»; rename confirms; AlertDialog
  remove deletes the row; drag of a row onto the viewer shows «Añadida a tu escena»; staff foreign view has 0 rename/0
  remove controls and the read-only tag; 6 running animations at load (expressive), 0 with `?still=1`; 0 external
  requests; no page errors.
- Screenshots inspected: 1280 light Taller, 1280 dark library, 768 dark staff, 390 light saved, 1280 ficha, 390 dark
  AlertDialog. A first pass showed crushed inspector buttons and the viewer hint overlapping the scene note; fixed
  before the final audit.

## Open questions for the owner

- Q: ¿Lo guardado en tu cuenta aparece solo en «Mi biblioteca» (como en este mockup) o también mezclado en Estructuras/Decoraciones/Ideas como hoy con la etiqueta «Tu biblioteca»?
- Q: ¿El personal (empleado/administrador) puede añadir a su propia escena una decoración de otra cuenta sin modificarla, o solo verla? El mockup solo deja «Ver ficha».
- Q: Las entradas «En este navegador» (antiguas): ¿se siguen pudiendo quitar y renombrar como hoy, o quedan solo para añadir/abrir? El mockup permite añadir, abrir y ver ficha, sin quitar.
- Q: T5.3 pide conservar «renombrar», pero la biblioteca actual no tiene renombrar; ¿se añade «Cambiar nombre» (como aquí) para el dueño?
- Q: T5.4/T5.5 hablan de «importar entradas del navegador» y de estados de importación, pero el SPEC (ronda 11 q1) dice que no se importan en el piloto; el mockup sigue el SPEC (sin importación). ¿Se corrigen esas tareas?
- Q: ¿Se pide confirmación al quitar (AlertDialog, como aquí) aunque la biblioteca actual quita sin confirmar?
- Q: ¿El nombre repetido en tu biblioteca está permitido (como hoy, con id distinto) o debe avisar?

## Concerns

- Contradiction between brief tasks (T5.4 «import legacy browser entries without loss», T5.5 «import» states) and SPEC
  round 11 q1 (no import). This direction follows SPEC; no import UI is drawn.
- «Abrir en Escena» is shown but its guard belongs to `proyectos@v1` (new unsaved project); the mockup only shows a
  Mockup notice for it.
- The AlertDialog copy «Lo que ya añadiste a tus escenas se queda en ellas» assumes placement copies content into the
  scene, as `Añadir a mi escena` does today; to confirm when T5.2 defines the API.
- The mockup proves rendered layout, contrast and interaction only; persistence across browsers, ownership enforcement
  and account-switch clearing are owned by T5.2–T5.4.
