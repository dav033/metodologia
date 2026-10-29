# decoraciones@v1 · r1 · Direction A — Biblioteca de trabajo

Exploration draft for REQ-021 / SP-5 “Saved decorations” (R8). Not a contract, not approved. The owner compares
directions; only the chosen direction's finalizer writes `decoraciones@v1.md`.

Files: `decoraciones@v1.r1.dir-a.tsx` (entry), `decoraciones@v1.r1.dir-a.html` (built mockup),
`decoraciones@v1.r1.dir-a.json` (axes + selector evidence), thumbnails `…dir-a.html.candidate-1.html` and
`…candidate-2.html`.

## Existing surface changed

Located read-only in t12 (`/home/david/dev/pictures-wt/t12`): `src/components/tres-d/Biblioteca.tsx`
(`taller3d:biblioteca-propia:v1` localStorage library, `AccionesPieza` save form with Nombre + Ocasión,
«Guardar en mi biblioteca», «Guardar toda la escena en mi biblioteca», `FichaDialogo` with «Abrir en Escena»,
«Añadir a mi escena», «Quitar de mi biblioteca»), `PanelAnadir.tsx` (panel «Añadir a la escena»: search
«Buscar: columna, flor, dorado…», tabs Estructuras/Decoraciones/Utilería/Ideas, «Ocasión: todas» filter) and
`ui-taller.ts` / `globals.css` (`--taller-*` tokens, 36–44px Taller buttons, `taller-rotulo`). The app shell
(masthead, Idioma, Mi cuenta, Taller 3D / Proyectos route rule, Taller save header) is reused from the sibling
`proyectos@v1` (chosen direction c) and `cuentas-admin@v1` / `planes@v1`, with identical tokens and Geist fonts.

What this direction changes, and only this:

1. **A fifth tab «Mi biblioteca»** in the existing «Añadir a la escena» panel lists the account's personal library
   as a dense list grouped by the existing item types (Escenas, Estructuras, Decoraciones, Utilería), with a summary
   line «N en tu cuenta · Al día con tu cuenta». Own items keep appearing in the other tabs marked «Tu biblioteca»
   (existing `Fuente` label), so nothing is lost from today's flow.
2. **The ficha moves into the inspector column** (master-detail) instead of covering the scene: miniature, name,
   tipo/ocasión, globos, an ownership line and the existing actions. «Ver ficha completa» still reaches the existing
   full `FichaDialogo` (products, source) — shown as a Mockup notice.
3. **Save to account**: the existing inspector form (Nombre, Ocasión, Guardar) now states the destination «Se guarda
   en tu cuenta…». While saving, the row appears in the list with a spinner and «Guardando…», never a check; only the
   confirmation adds the check and the message «Guardado en tu biblioteca: «…» (tipo). Está en tu cuenta.»
4. **Owner-only controls**: rename (pencil → inline field, Escape/Cancelar restore focus) and «Quitar de mi
   biblioteca» (AlertDialog). Staff with «Biblioteca de: Cuenta de ejemplo» see a lock per row, «Solo lectura» and
   no rename/delete.
5. **Browser-local entries stay local**: a folded «Solo en este navegador · N» group under the account list explains
   they are not imported in the pilot and not visible in other browsers; their ficha keeps the existing place
   actions and «Quitar de este navegador», with no import action.
6. **Account switch / sign-out**: the list is replaced by skeletons («Cargando la biblioteca de la cuenta elegida…»);
   no previous account's rows remain on screen.

## Interaction and motion

Grammar: precise quick cuts, deceleration only (`cubic-bezier(.2,0,0,1)`), no overshoot — deliberately unlike the
sibling's tactile springs because this is a repeated, list-driven tool.

| Move | Expressive | Natural | Subtle |
|---|---|---|---|
| Rows enter `translateX(-8px)→0`, staggered | 150ms, +16ms/row | 120ms, +10ms | 90ms, +5ms |
| Ficha body swap on selecting another row `translateY(6px)→0` | 150ms | 120ms | 90ms |
| Sync text / notices tick `translateY(-4px)→0` | 150ms | 120ms | 90ms |
| Freshly confirmed row: bottom bar `scaleX(0→1)` in taller-valido | 260ms | 200ms | 140ms |
| Tab indicator (Motion `layoutId`) slides between tabs | 150ms | 120ms | 90ms |
| Spinner only while a save/rename/delete is pending | 900ms/turn | same | same |

Press: buttons translate 1px down; hover changes the Taller surface step. Reduced OS motion, «Quieto» and
`?still=1` remove every animation and transition while keeping every word and control; hidden tabs pause CSS
animations. Content is never hidden mid-animation (no opacity entrances).

Keyboard: rows are a name button (`aria-pressed`) plus a separate «Añadir a mi escena: <name>» button; Cerrar la
ficha returns focus to its row; the AlertDialog traps focus and Escape returns to «Quitar de mi biblioteca»;
search keeps focus while typing (probe-verified).

## Why it fits the product

The personal library already lives in the Taller's «Añadir» panel and inspector; this direction keeps it there,
adds the one location R8 needs to find account items, and keeps the scene visible while placing — the main job
(«put my saved thing into this project»). Density, the existing `taller-rotulo` group labels and 40px Taller buttons
match the editor's working vocabulary; the shell is byte-for-byte the siblings'.

## Eight axes

| Axis | Observable in the mockup |
|---|---|
| concept | Library as a working list inside the Taller: fifth «Mi biblioteca» tab + ficha in the inspector; save confirms only what the account accepted. |
| layout | Desktop 60 / 330 / canvas / 300px columns; tablet: ficha becomes a full-width strip (200px miniature + detail) below panel and canvas; phone: rail row, canvas, panel, ficha stacked. |
| navigation | Shared masthead and Taller 3D/Proyectos rule; segmented tabs with sliding shared indicator; row → ficha in place, Cerrar returns to row; staff «Biblioteca de» native select. |
| typography | Geist: H1 24px, panel 15px, ficha name 18px, row name 14px/600, meta 12–13px, group labels 11px uppercase (existing `taller-rotulo`), Geist Mono counts. |
| density | 52px rows (56px phone) with 44×36 miniature, type·occasion, state icon and 40/44px add button; grouped counts; local group folded. |
| components | Real Input, Skeleton, Button, AlertDialog (shadcn/Base UI/Animate UI), Motion `layoutId`; custom rows, ficha, local disclosure, save form with Taller button styles. |
| colour | Pictures/Taller tokens only: primary on Añadir a mi escena/Guardar; taller-valido = saved in account; taller-medio = local / read-only; error on remove and failures. |
| motion | Deceleration-only quick cuts: row stagger, ficha swap, sync tick, confirmation sweep, sliding tab indicator; profile-scaled; reduced/still parity. |

## Views, states and dialog in the mockup

Vista: «Taller · Mi biblioteca», «Taller · Guardar en mi biblioteca», «Taller · Biblioteca de otra cuenta (personal)».
Estado: Al día, Cargando, Vacía, Error al cargar, Sin conexión, Solo en este navegador, Guardando, Guardado en tu
cuenta, Error al guardar, Rechazado por la cuenta, Cambiando el nombre, Error al cambiar el nombre, Quitando, Error al
quitar, Cambio de cuenta, No disponible, Sesión terminada. Diálogo: «Quitar de mi biblioteca». Meaningful pairs:
save states with the save view; rename/delete states with the library view; Cambio de cuenta with any view.

## Chosen thumbnail

**Candidate 1** (tab in the «Añadir» panel + ficha in the inspector). Candidate 2 (sortable table tray under the
canvas) shrinks the canvas, loses columns on phone and moves the library away from where it lives today.

## Open questions (for the owner)

- Q: May employees/administrators place another account's saved item into their own scene (Añadir a mi escena / Abrir en Escena) while it stays read-only? The mockup allows it.
- Q: Should the browser-local «Solo en este navegador» entries stay visible in the Taller (mockup: folded group with place and remove-from-this-browser), or be hidden?
- Q: Rename is listed in T5.3 but does not exist in today's `Biblioteca.tsx`; confirm owner rename belongs in the pilot (mockup: inline in the ficha, 120-character limit borrowed from proyectos@v1).
- Q: Where do staff open another account's library — the «Biblioteca de» selector in the Taller (mockup), or from a foreign project/accounts screen?
- Q: PLAN T5.4/T5.5 still mention importing legacy entries and an «import» state, contradicting SPEC round 11 and T5.3 (no import); the mockup follows SPEC (no import UI).
- Q: Does removing an item from the library need to say anything about projects where it was already placed? The mockup states they do not change (placement copies the content, as today).

## Audit (actual results, final build)

- Build: `bitacora.py components mockup build … --out decoraciones@v1.r1.dir-a.html` → 660 KB, 2132 source files, offline.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass` (exit 0).
- `audit_mockup.py --widths 1280,390,768`: 324 renders / 324 planned, 15678 text measurements, 2847 focus stops.
  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- Earlier runs found and fixed: button vertical padding 7px (<8px) in the save view; «Decoraciones» tab breaking
  mid-word at 390px; destructive AlertDialog action rendering in the accent colour.
- Probe (inline Playwright, screenshots only in /tmp): search keeps focus while typing; row selects ficha; delete
  AlertDialog opens and Escape returns focus to «Quitar de mi biblioteca»; place shows «Añadida a tu escena»; save
  shows a pending row with spinner, then the confirmation; staff view has no rename/delete; 7 running animations at
  ~60ms in expressive, 0 with `?still=1`; zero external requests. Screenshots inspected: 1280 light library, 1280
  dark saved, 768 light local, 390 dark library, 390 light delete dialog.
- Not proven: real persistence, cross-browser behaviour, ownership enforcement, account-switch clearing — owned by
  T5.2–T5.4 and the audits.
