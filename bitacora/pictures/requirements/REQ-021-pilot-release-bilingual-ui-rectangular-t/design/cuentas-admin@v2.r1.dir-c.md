---
name: Ficha en su sitio — direct manipulation
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v2
subplan: SP-2
requirements: [R1, R3, R16, R17]
revision: r1.dir-c
source_behavior: cuentas-admin@v2.r1.behavior.md
chosen_thumbnail: cuentas-admin@v2.r1.dir-c.html.candidate-1.html
files: [cuentas-admin@v2.r1.dir-c.tsx, cuentas-admin@v2.r1.dir-c.styles.ts, cuentas-admin@v2.r1.dir-c.html, cuentas-admin@v2.r1.dir-c.json]
---

# Ficha en su sitio — direction C

Unapproved exploration for the owner's comparison. This is an axis note, not the twelve-section `cuentas-admin@v2` contract. No plan, shared contract, history, production source or approval state was touched. If the owner picks this direction, a finalizer writes the contract.

## What changes on the existing surface

Scope is only what the v2 brief changes: the **/cuenta identity and password area** and the **shared signed-in account menu**. Sign-in, invitation activation, reset, the mandatory data-notice gate, accounts/invitations and roles stay exactly as `cuentas-admin@v1` (the third mockup view shows the menu over the unchanged Cuentas page to prove the menu is shared).

Shell reproduced from the current product (`MenuCuenta`, `CabeceraCuentas`, `NavegacionCuentas`, `src/app/cuenta/page.tsx`, the 2026-10-31 screenshots `account-open-1280/390.png`): full-width 64px account bar with the pill trigger at the right, then the 676px centred column with the Pictures ring-and-dot mark · Sempertex, «Idioma» select, H1 «Mi cuenta», «Tu cuenta está activa.» and the route rule.

**Mi cuenta.** The two current cards («Tu identidad» grid with «Cuenta», «Correo electrónico», «Rol», «Aviso de datos aceptado»; separate «Cambiar contraseña» form always open) become **one sheet**:

1. Identity plate — 64px initial (existing `acento-suave` circle), then labelled **Nombre** (20px, the sheet's largest text) and **Correo**. Name falls back to the email only when the stored name is null/empty/whitespace (fixture «Sin nombre»).
2. Ruled rows — **Plan · <catalogue name>** for the four catalogue plans (Entusiasta/Enthusiast, Designer, Designer Plus, Master Designer from `plan-catalogue@1`), otherwise **Rol · Administrador / Empleado interno / <custom role name>**. **Empresa** appears only when the fixture carries it. The accepted-notice version/date row is gone from the ordinary profile.
3. **Contraseña** row — masked dots and one outline action «Cambiar contraseña». Pressing it opens the editor **in place under the row**, inside the same paper; it is the only editable fact on the page (no name/plan/role editing).

**Account menu.** The popup keeps its production vocabulary (identity, ES/EN pair from SP-8, Mi cuenta, permission-scoped Administración and Roles y permisos, Planes from SP-14, Cerrar sesión) and changes presentation: 40px initial with wrapping full name and email (no truncation inside the popup), an access chip «Plan Designer Plus» / «Rol Administrador», grouped language row, links, and a ruled sign-out. The trigger truncates long names to one line; its accessible name carries the full name. On phones the popup becomes a fixed sheet 16px from both edges under the bar.

## Interaction and motion detail

- **Direct manipulation, one thing at a time.** Closed, the page reads as three or four facts. «Cambiar contraseña» expands its own row: focus goes to «Contraseña actual»; «Cancelar» or Escape collapses it, clears the three secrets and returns focus to «Cambiar contraseña». Pending disables fields and actions and shows «Guardando…».
- **Errors at the point of use.** Production order is kept (required → under 8 → over 200 → mismatch → server). Each failure marks its field (`aria-invalid`, `aria-describedby`) with the message directly under it; «Completa los tres campos de contraseña.» and the service/network error also appear as one summary at the top of the editor. Wrong current password marks «Contraseña actual».
- **Live feedback while typing.** A thin meter under «Contraseña nueva» fills toward 8 characters and turns success-green inside 8–200 with «Entre 8 y 200 caracteres.»; «Repite la contraseña nueva» shows «Coinciden.» when equal. Icons hang in the left gutter so text never shifts.
- **Success.** The editor collapses, secrets are cleared, focus returns to «Cambiar contraseña», and a success seal under the row (role=status) shows «Contraseña cambiada. Esta sesión se renovó; tus otras sesiones terminaron.» with a drawn check. The mockup simulates the service (current password «incorrecta» → wrong-password state); production keeps server verification, current-browser renewal and other-session invalidation.
- **Menu dismissal.** Disclosure button with `aria-expanded`/`aria-controls`, no menu roles and no focus trap. Repeated trigger closes and leaves focus on it; Escape closes and returns focus to it; an outside pointer closes without preventing default, so the clicked focusable target keeps focus; Tab/Shift+Tab leave freely and the popup closes once focus is outside.
- **Tactile press/settle grammar.** Presses compress quickly (trigger `scale(.95)`, row and menu actions `.95–.97`, ES/EN `.92`; 90ms `cubic-bezier(.4,0,.7,1)`); arrivals settle with a small overshoot (`cubic-bezier(.34,1.42,.64,1)`, 460ms expressive / 300ms natural / 170ms subtle): sheet rise, initial press-settle, rows staggered 55ms, popup spring from the trigger's corner, drawer height spring with staggered fields, a 260ms sideways nudge on an invalid field, success seal with check stroke. OS reduced motion, «Quieto» and `?still=1` remove all travel and show final states; the spinner and skeleton pause in hidden tabs.

## Why it fits Pictures

It keeps the shell, column width, rounded 32px paper, 18px fields, pill buttons, neutral route rule and Geist type the owner already sees on /cuenta. It removes the always-open three-field form that dominates today's page and turns the page into a quiet identity sheet with one deliberate action — a better match for a page people visit to check who they are and occasionally change a password. Colour stays on the primary submit, focus, success and errors.

## Eight axes

| Axis | Present expression |
|---|---|
| Concept | Direct manipulation in place: a read-only ruled identity sheet whose only editable fact, the password, opens under its own row; the shared popup carries the real identity and settles under the trigger. |
| Layout | Unchanged bar + 676px column. One paper: 64px initial plate (Nombre/Correo stacked), 132px label / value rows, Contraseña row with an in-paper drawer. Phone: labels above values, full-width actions, 20px insets. |
| Navigation | Retained route rule (permission-scoped). Disclosure-button popup with repeated-trigger, outside-pointer, Escape and focus-leave closure; links Mi cuenta, Administración, Roles y permisos, Planes, Cerrar sesión; in-page reveal/collapse with explicit focus moves. |
| Typography | Geist Sans/Mono only: H1 24px/600, identity name 20px/600 (18px phone), email 15px, labels 13px muted, field labels 14px/600, help/errors 13px. |
| Density | Sparse closed sheet (three–four 64px rows); dense open editor (48px fields, 18px gaps); 28px/20px insets. |
| Components | shadcn/Base UI Button, Input, Skeleton; Motion AnimatePresence; native Idioma select; custom plate, ruled rows, meter, inline errors, success seal. |
| Colour | Production globals.css tokens only, both themes; `superficie-suave` marks the open row and drawer; accent only on submit/focus/active trigger edge. |
| Motion | Press 90ms compress / settle 460ms overshoot, 55ms stagger; popup and drawer springs; invalid nudge; drawn success check; reduced/still/hidden-tab parity. |

## Thumbnails

1. **Chosen — `cuentas-admin@v2.r1.dir-c.html.candidate-1.html` «Ficha que se abre».** Stays in the existing 676px column; the password row opens in place; the popup shows identity, access chip, ES/EN and links.
2. `cuentas-admin@v2.r1.dir-c.html.candidate-2.html` «Mesa de identidad». A 260px identity tile beside a settings list with a password panel sliding over it. Rejected: it widens /cuenta beyond the existing column, hides the settings list while editing and on phones covers the whole page.

## Mockup controls

«Vista»: Mi cuenta (/cuenta), Menú abierto, Menú en Cuentas (v1). «Estado»: Designer Plus + empresa (default), each of the four plans, Administrador (admin links), Empleado interno, Rol personalizado, Sin nombre, Datos largos (long name/email/company), Menú cerrado, Cargando, nine password states (editor abierto, obligatorios, corta, larga, no coinciden, actual incorrecta, guardando, error servicio/red, cambiada), Salida pendiente / error. «Tema» light/dark; «Movimiento» expressive/natural/subtle/Quieto. ES/EN is switched inside the product (Idioma select or the menu's ES/EN pair). On «Menú en Cuentas (v1)» the fixture is always the administrator, since that page needs the permission. «Cerrar sesión» is simulated and ends in its error state so the preview never navigates away.

## Checks actually run (2026-10-31)

- Build: `bitacora.py components mockup build cuentas-admin@v2.r1.dir-c.tsx --out cuentas-admin@v2.r1.dir-c.html` — built offline, 556 KB, 2032 source files.
- `contrast.py`: **158 pairs checked in light and dark, all pass.**
- `audit_mockup.py` (default 1280/390): **264 renders, 7168 text measurements, 1096 focus stops — RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems.**
- `audit_mockup.py --widths 1280,768,390,360`: **528 renders, 14336 text measurements, 1096 focus stops — RESULT: PASS.**
- Scripted Playwright interaction check at 1280×900 and 390×844: **36/36** — open by click/Enter/Space, Escape closes and returns focus to the trigger, repeated trigger closes and keeps focus, outside pointer closes and the clicked target keeps focus, Tab and Shift+Tab out close it, editor focus on open, short and mismatch errors, success status with focus back on «Cambiar contraseña», secrets cleared, Escape collapses the editor, no horizontal overflow.
- `compare_directions.py` with dir-a and dir-b: ok, evidence ok, layout similarity 0.055 (a–c) and 0.048 (b–c); typography/navigation/motion/density all differ.
- Settled screenshots inspected at 1280 (light/dark), 768, 390 and 360: Mi cuenta closed, admin menu, long-data menu at 360, short-password error at 390, success at 768, service error and wrong current password at 1280, menu over Cuentas at 390. Earlier findings fixed before these runs: too-long selector labels overflowing at 390, pending-state opacity lowering help-text contrast, a duplicated Cancelar, and «Mi cuenta» marked current over the Cuentas page.

## Concerns

- The repositories named in the brief (`pictures-wt/t12`, `pictures-wt/asesor`) do not contain `MenuCuenta`, `/cuenta` or `CambiarContrasena`. The current surface was read read-only from the verification snapshot `~/.local/share/bitacora-verify/pictures/REQ-021/SP-2-v2` (commit `6ec74192`) and the SP-8-v2 snapshot for the composed ES/EN pair and Planes link, plus the brief's two screenshots. Tokens come from that snapshot's `src/app/globals.css`; fonts are the existing t12 build's local Geist WOFF2 files.
- During this run another process moved the TSX's CSS into `cuentas-admin@v2.r1.dir-c.styles.ts` (after the 500-line file guard fired) and changed the error-icon placement. I kept the split, since the entry imports it, and restored the left-hanging icon. That file is part of this direction's source.
- Copy not in production yet: «Nombre/Name», «Correo/Email», «Plan», «Empresa/Company», «Contraseña/Password» row label, «Cancelar/Cancel», the too-long message, «Entre 8 y 200 caracteres.», «Coinciden./They match.», «Este campo es obligatorio.» (see questions). English names for the system roles are not stored in production.

## Open questions for the owner

- Q: Is the too-long message «La contraseña nueva debe tener como máximo 200 caracteres.» / «The new password must be at most 200 characters.» acceptable? Production has no copy for that case.
- Q: Keep the live helpers «Entre 8 y 200 caracteres.» and «Coinciden.» with the length meter? They restate the existing 8–200 rule and add no policy.
- Q: Should «Empresa» show at all? It appears only when the account record actually has a company; please confirm that data exists for invited accounts.
- Q: For English, should the system roles read «Administrator» / «Internal employee»? Production stores only Spanish role names, and custom role names stay as written.
- Q: The success message stays under the Contraseña row until the editor is reopened or the page changes. Is that enough «acknowledged success», or do you want an explicit dismiss?
- Q: On phones the open menu is a sheet over the page, 16px from both edges. Is covering the page acceptable while it is open?
- Q: The production trigger is a native `<details>`; this direction uses a disclosure button with `aria-expanded`. Can the implementer choose either, as long as the dismissal and focus behaviour is identical?
