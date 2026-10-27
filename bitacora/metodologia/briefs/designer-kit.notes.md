# Notes — designer-kit brief (session 6756889e, 2026-10-26)

## Acceptance baseline: REQ-021 SP-2 `cuentas-admin@v1.html` (rev 6), rendered in Chromium

Screens: 11 views × light/dark × 1280/390 px (`/tmp/claude-1000/.../scratchpad/base/sp2/`).

- **Alignment.** Login/activate/reset: the form column is centred (x 420–860) but the page footer starts at x 40 and
  «¿Olvidaste tu contraseña?» is centred while every label, hint and note above and below is left-aligned. The form floats
  on the page with no card, so the centred column has no edge to read against. Role editor aside: «7 de 12 permisos
  seleccionados» is right-aligned in a left-aligned column; group headings («Herramientas») sit 2 px right of the checkboxes.
- **Table.** Status badges sit lower than the row's text baseline; the «Empresa» column uses a smaller size than its
  neighbours; the action column has no header and its ghost «Ver cuenta» reads as disabled grey text in dark.
- **Padding.** Tabs are a filled grey pill with no underline and touch the divider; the planning toolbar wraps into two
  ragged rows; on 390 px each account becomes a loose label/value list with a full-width outlined button per row.
- **Contrast (dark).** Native checkboxes render as bright white squares on Mocha; outlined inputs and the «Cuenta» button
  rely on a thin grey edge; ghost actions («Ver cuenta», «Tema claro») look disabled; muted helper text is low on the
  raised surfaces.
- **Affordance.** «Tema oscuro/claro» is plain bold text in the header with no control shape.

## Work log
- D-135 written with the kit design before coding.
- Kit built (replaces the draft `mockup-kit.css`, deleted): `tokens.css` (shadcn role names, Latte/Mocha, 158 AA pairs pass),
  `components.css` (33 components: the 30 P1 + Radio Group, Input Group, Progress; roles only), `kit.js` (layers, tabs, toast,
  combobox filter, mobile sidebar, theme/motion selects, `data-show-view|state|scene` switcher), `components/*.html` +
  `manifest.json`, `templates/mockup.html` (`.mockup-bar` with the select contract), `reference/{acceso,cuentas,invitar}.html`,
  `inline.py`, `contrast.py` (cascade-aware, reads a mockup's effective tokens), `audit_mockup.py` (rewritten).
- Gallery `/components` (+ `/components/frame/<id>`, `/components/ref/<id>`, sandboxed); nav «Componentes»; CLI
  `bitacora.py components`. Checked on a temporary server at :8811 (:8799 was taken by another session's server; not touched).

## Audit on the current REQ-021 drafts (read-only, final audit version)
- SP-2 `cuentas-admin@v1` (352 renders, 1370 focus stops): FAIL alignment 11 — planning footer at x 40 under the centred
  login/activate column; «¿Olvidaste tu contraseña?» a lone centred line in the login card; frameless full-width buttons with
  centred labels («Volver a iniciar sesión», «Volver al inicio», «Cerrar sesión», «Ver rol», «Editar rol» at 390 px) among
  left-aligned content; a lone right-aligned description in the role editor at 390 px. Advice: 13 native checkboxes in dark.
  No text under 4.5:1 was measured: the dark complaint there is muted/ghost actions and native controls, not AA ratios.
- SP-4 `proyectos@v1` (480 of 720 combinations sampled, 2144 focus stops): PASS. The earlier alignment and padding hits
  were false positives of the first audit version (two-line checkbox label; invisible transparent border).
- SP-3 `taller-esenciales@v1` (240 renders): FAIL contrast 6 (search placeholders 3.74:1 in dark; SVG «HAPPY birthday» text
  3.5:1 dark / 4.14:1 light), padding 15 (catalogue cards with 10 px side padding).

## Independent review (antagonist, read-only)
CONCERNS, 7 findings, all fixed: colours read through a canvas (oklch etc.) and unreadable text colours fail; inline links
judged against their block; focus compares focused vs unfocused; chrome detection no longer hides a product sharing the
selects' wrapper (+ warning without `<main>`); phone gutter and field-text inset checked; every rendered state walked with
Tab, 0 stops fails, caps and sampling warned; brief gives absolute kit paths. Each has a fixture test. The fixed audit then
caught a real kit defect (focused invalid field: 25 % halo only, 1.55:1), fixed in `components.css`.
