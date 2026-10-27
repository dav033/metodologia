# cuentas-admin@v1 · r8 · direction A — Mesa de acreditación

Status: **exploration** (not a contract, not approved). Seed: operational/editorial — dense working information,
asymmetric typographic hierarchy, precise kinetic sequencing. Behaviour source:
`cuentas-admin@v1.r8.behavior.md` (SP-2, R1/R3/R16); nothing here changes it.

Files: `cuentas-admin@v1.r8.dir-a.tsx` (entry) → `cuentas-admin@v1.r8.dir-a.html` (offline build),
`cuentas-admin@v1.r8.dir-a.json` (axes + selector evidence), thumbnails `….html.candidate-1.html` /
`….html.candidate-2.html`.

## Concept

Before a Sempertex event, someone runs the accreditation desk: a list of named people, what each one may touch,
and passes that are handed out once. Pictures' access screens are that desk, set like a newsroom page. Every
person is a ruled line in a register; every permission is written down with a check or a cross; every invitation
or reset link is a single-use pass with a stamped receipt. The one object on the desk is a foil balloon that
swings in and keeps swaying slowly — the product's world in a single, quiet piece.

**Memorable move:** the oversized condensed title (*Accesos*, *Roles*, *Tu próximo montaje.*) set at 108–112px
against 12px tabular data, with a heavy ink rule that draws itself in and the whole sheet cutting in sideways on
every view change, like a page being set.

**Why not the default:** the safe version of these screens is a centred card on a purple-tinted white page plus a
generic data table. This direction drops the centred card (sign-in becomes a two-column typographic spread), drops
the purple (sage paper + one viridian spot), uses a condensed grotesque display face with real scale contrast, and
turns account administration into a register with a docked action rail instead of row menus.

## Eight axes

| Axis | What is in the mockup |
|---|---|
| Concept | Event accreditation desk run like a newsroom: named register lines, written permissions, single-use passes, one foil balloon. |
| Layout / composition | Masthead → 108px title with a mono counter and the balloon → 3px ink rule → tabs → filters → working rail of the chosen person → five-column register (person/company, role, state, last access, action). Roles: index column + permission sheet. Sign-in, activation, reset and notice: typographic spread left, ruled form sheet right; stacked on phone. |
| Navigation | Two baseline text tabs (Cuentas, Roles) with a drawn underline, mono running head right, corner account summary (name + role) opening Mi cuenta and Cerrar sesión. Actions are named buttons in the rail; no sidebar, dock, cards or kebab menus. |
| Typography / scale | Bricolage Grotesque Variable 800 at 76% width (108px admin, 112px auth, 64px tablet, 58px phone; 34px section heads, 30px dialog titles); Instrument Sans Variable 13–17px working copy; JetBrains Mono Variable 12px tabular for running heads, counters, timestamps. All embedded as data URIs. |
| Density / shape | Six people per register, 20px row padding, 2px corners, 44px controls, 1px rules plus one 3px ink rule; 48px desktop gutters, 28px tablet, 20px phone. |
| Signature components | shadcn Button/Input/Skeleton; Animate UI Checkbox, Dialog, AlertDialog restyled square; native selects (filters, notice language, role); custom register, working rail, permission sheet with check/cross proof, pass receipt stamp, CSS foil balloon. |
| Colour logic | Proposal. Light: sage paper `#edf1ec`, ink `#111c17`, card `#ffffff`, viridian spot `#0a5a4c` only on the primary action, focus ring, counter, chosen-row bar and register underline. Dark: forest night `#0d1412` / `#17211d`, text `#ecf3ef`, mint spot `#83d8bf`. States: leaf `#2f6413`/`#b9e394` active, amber `#7a4d00`/`#f1cf7c` invited, red `#a8202f`/`#ffabb6` destructive, grey deactivated. Control edges `#5c6d64` / `#8ea69a`. Pictures role names (`--primary`, `--muted-foreground`, …) are kept; values are not a token migration. |
| Motion | One easing family `cubic-bezier(.76,0,.24,1)` (typesetter registration). See the list below. |

### Motion inventory (expressive default; natural/subtle scale it)

1. **Title registration** — `h1` slides 22px and un-skews from −7° (580 / 340 / 210ms).
2. **Ink rule and register underline** — `.desk-nav:before` and `.register-head:after` draw in with `scaleX`.
3. **View cut** — `.sheet` is re-keyed per view and cuts in 28px on every Vista change.
4. **Row registration** — `.person` rows slide 14px with 35ms offsets; status dots grow (`scaleY`) after them.
5. **Rail docking** — `.working-line` and the permission sheet settle 9px.
6. **State stamp** — notices are re-keyed per Estado and stamp in from −2°; the one-use pass receipt does the same.
7. **Dialog cut** — dialogs and alert dialogs enter with a 22px sideways cut.
8. **Foil balloon** — swings −12° → +13° → 10°, then ambient sway every 7.2s; paused when the tab is hidden.
9. **Micro-interactions** — buttons lift 2px on hover, press 1px, arrow icons nudge; tab underline draws on hover;
   role rows nudge 3px. Controls run 160 / 140 / 90ms.

Reduced motion (`prefers-reduced-motion`, `?still=1`, or Movimiento = Quieto): every animation and transition is
removed, including the infinite sway; final content, focus and feedback appear immediately. All motion is
transform-only, so text keeps full contrast mid-animation.

## Views, states and dialogs covered

- **Vista:** Cuentas, Roles y permisos, Iniciar sesión, Activar invitación, Restablecer contraseña, Aceptar nuevo aviso, Mi cuenta.
- **Estado:** Normal, Cargando (skeleton rows), Vacío / sin resultados, Error (sign-in error always adds the 15-minute wait), Éxito, Validación (including `ROL_SIN_PERMISOS`), Sin permiso, Enlace usado o vencido (same message for invitation and reset), Sin conexión, Cuenta con trabajo guardado (`CUENTA_CON_TRABAJO`).
- **Diálogo:** Invitar persona, Enlace de un uso (shown once, copy button, clipboard fallback), Cambiar rol (last-administrator guard), Eliminar cuenta (type the email; refused with saved work or for the last administrator, offers deactivation), Desactivar o reactivar, Regenerar enlace (invalidates older unused links of the same kind), Ayuda de acceso.
- Durations shown come from SPEC round 6: invitation 7 days, reset 24 h, password ≥ 8, lock 15 min. People, companies and timestamps are illustrative.

## Thumbnails

- **Candidate 1 — register desk (chosen):** masthead, big title + counter, ink rule, tabs, ruled register with the chosen person highlighted. It answers the screen's question («who has access, and what can I do with this person?») in the first viewport and scales to roles and sign-in.
- **Candidate 2 — cast sidebar:** a left «Elenco» column with the title and tabs, a plaque for the latest invitation and the directory below. Rejected: the plaque pushes the register under the fold and the narrow title column wastes the expressive type.

Both thumbnails were drawn before the full build; after the build their palette and type stack were updated to the final sage/viridian and Bricolage/Instrument/JetBrains choice so they show the same world.

## Audit (actual results, 2026-10-27)

- Build: `bitacora.py components mockup build` → `cuentas-admin@v1.r8.dir-a.html` (1048 KB, 2150 source files, offline).
- `kit/contrast.py`: **158 pairs checked in light and dark, all pass**.
- `kit/audit_mockup.py`: 476 renders (476 planned), 12830 text measurements, 1092 focus stops —
  **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**.
  An earlier run failed on alignment (a long permission label wrapping at 390px); fixed by moving the Taller 3D scope into its group title.
- `kit/compare_directions.py` (A, B, C): A↔B and A↔C pairs ok (layout similarity 0.012, typography, navigation and motion all different); all of A's evidence selectors match. The overall run reports `ok: false` because direction C's JSON names selectors that are absent from its HTML (`.access-mat`, `.tool-tab`, `.balloon-piece`, …) — C's problem, not A's.
- Screenshots inspected at 1280 (Cuentas light/dark, Roles dark, Iniciar sesión, Invitar dialog, Mi cuenta) and 390 (Cuentas light, Activar dark).

## Open questions for the owner

- Q: Is a non-Pictures palette (sage paper + viridian spot, mint in dark) acceptable for the pilot, or must the final contract map back to the Pictures mauve tokens?
- Q: For people without administration permissions, is the corner account menu the only route to Mi cuenta (no tabs shown), as drawn here?
- Q: Does the administrator see accounts as a register with a single docked action rail (choose a row, then act), or do you prefer actions on every row?
- Q: Should the data notice's language switch stay visible (defaulting to the browser language) or be hidden, showing only the browser language?
- Q: Should the account register show the AI spend or saved-work count per person, so the reason a delete is refused is visible before opening the dialog?
