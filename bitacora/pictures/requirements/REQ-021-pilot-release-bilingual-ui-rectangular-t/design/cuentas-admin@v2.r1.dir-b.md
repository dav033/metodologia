---
exploration: cuentas-admin@v2.r1.dir-b
name: Pase y panel de seguridad
status: draft
subplan: SP-2
requirements: [R1, R3, R16, R17]
stance: spatial
chosen_thumbnail: cuentas-admin@v2.r1.dir-b.html.candidate-1.html
owner: David
date: 2026-10-31
---

# Pase y panel de seguridad — spatial exploration B

## 1. Identity and scope

Planning exploration only, **draft and unapproved**. It is a candidate for the future `cuentas-admin@v2` contract, not
the canonical contract. No canonical contract, shared HTML, PLAN, repository or other bitácora file was written.
Owner feedback: none supplied; no previous v2 draft.

Scope comes from `cuentas-admin@v2.r1.behavior.md` and SPEC «Behavior — SP-2 account amendment (P-209)»: only the
`/cuenta` identity and password area and the shared signed-in account menu change. Sign-in, invitation activation,
reset, mandatory notice re-acceptance, accounts/invitations and role administration stay exactly as
`cuentas-admin@v1` (its canonical HTML remains the reference for those views; this mockup does not redraw them).

Read-only product evidence: the most recent SP-2 verification snapshot
(`~/.local/share/bitacora-verify/pictures/REQ-021/SP-2-v2`) — `src/components/cuentas/{MenuCuenta,CambiarContrasena,BarraCuenta,CabeceraCuentas,NavegacionCuentas}.tsx`,
`textos-cuenta.ts`, `src/app/cuenta/page.tsx`, `src/lib/cuentas/cuenta-actual.ts`, `src/lib/planes/catalogo.ts`,
`src/app/globals.css`; the solver screenshots `account-open-1280.png` / `account-open-390.png`. The listed paths do
not exist in `pictures-wt/t12` or `pictures-wt/asesor` (those worktrees predate SP-2); see Concerns. Sibling shell,
tokens and component vocabulary come from the approved `herramientas-chat@v1` (r2 dir-a) and `cuentas-admin@v1`
(amend-1) sources.

## 2. Approach — how this direction changes the existing surface

The current `/cuenta` is a 676px single column: a «Tu identidad» card with a 2×2 grid (Cuenta, Correo, Rol, Aviso de
datos aceptado) followed by a «Cambiar contraseña» card with three stacked fields. The menu is a 256px popover with
the name twice (name + email both show the email when unnamed), «Rol», purple text links and «Cerrar sesión».

This direction keeps the same app shell (Pictures/Sempertex masthead, Idioma select, account disclosure, neutral
route navigation «Cuentas · Roles y permisos · Mi cuenta», paper panels) and rearranges only the changed area
**spatially**:

- **Two seated panels instead of a stack.** A 340px «pase» (identity pass) sits on the left and stays sticky; the
  password form becomes a wider security panel on the right. Both are visible on desktop (≥840px; 300px pass from
  840–1099px), so the main job — changing the password — is never hidden behind a click.
- **Identity pass.** Large monogram + «Tu identidad»; labelled rows **Nombre**, **Correo**, optional **Empresa**
  (only when the fixture supplies it); a ruled access block that reads **Plan + catalogue name** for the four plans
  or **Rol + actual role** for Administrador, Empleado interno and a custom role. The accepted-notice row is removed.
- **Security panel.** «Contraseña actual» stands alone; a rule separates the «Contraseña nueva / Repite la
  contraseña nueva» pair (side by side ≥1100px, stacked below). The 8–200 rule is a hint under the new field; errors
  sit under the field they belong to (`aria-invalid` + `aria-describedby`), the «required» message sits at the top of
  the form, service/network failure is an alert note above the button, success is a receipt that drops in under the
  panel title and the fields are cleared.
- **Alternative in-page navigation.** A segmented local rail «Identidad · Contraseña» sits on the heading row.
  On desktop it moves focus to the chosen panel heading and spotlights that panel (stronger edge; the other panel
  recedes to 98.5% scale). Focus entering either panel updates the rail. Below 840px the two panels become a
  horizontal **track**: the rail slides the track one panel width; the off-screen panel is `inert` + `aria-hidden`
  and focus lands on the arriving panel's heading.
- **Account menu.** Same native `details/summary` (no menu roles), trigger = monogram + real display name
  (truncated) + chevron. The sheet unfolds from the trigger's top-right corner: an identity header (monogram, name,
  email only when it differs from the displayed name, an access chip «Plan · Designer Plus» / «Rol · Administrador»),
  a navigation group (Mi cuenta [current], Planes, Administración and Roles y permisos only when permitted), and a
  preferences/session group (Cambiar tema, Cerrar sesión with pending and error). Idioma stays in the masthead as in
  the siblings. On phones the sheet anchors to the full header row so it never leaves the viewport at 360px.

## 3. Interaction and motion

Grammar: **glide and seat** — elements travel horizontally along the axis they live on and settle with a short
overshoot; nothing fades in from nothing.

| Moment | Element | Motion (expressive / natural / subtle) |
|---|---|---|
| Load | `.identity-pass` seats from −18px, `.security-panel` from +18px one step later; `.pass-row` glide from −10px with a 60ms stagger | 560 / 380 / 200ms, `cubic-bezier(.3,1.18,.4,1)` (natural `.25,1.05,.45,1`; subtle `.2,.8,.2,1`) |
| Rail | `.local-nav-indicator` (Motion `layoutId`) slides between the two segments | spring 300/24 · 420/34 · 120ms tween |
| Spotlight (≥840px) | receded panel `scale: .985`, edge colour change | same seat timing |
| Track (<840px) | `.account-track` `translateX(-100% − 16px)` | same seat timing |
| Menu | `.menu-sheet` unfolds from `translate(10px,−10px) scale(.96)`; `.menu-item` glide from +10px, 60ms stagger; `.chev` rotates 180° | seat timing / 180ms |
| Feedback | `.field-error` drops 4px (180ms); `.receipt` drops 12px (seat) ; buttons lift 1px on hover, press 1px + 0.98 | 180ms `cubic-bezier(.22,1,.36,1)` |

Content is present and legible at every frame (transform only, no opacity-from-zero). Reduced motion /
«Movimiento: Quieto» / `?still=1`: all CSS animation and transitions are removed, Motion skips to the end state; the
track jumps, the menu appears in place. The only looping effect (pending spinner) pauses in hidden tabs.

Dismissal and focus (verified in Chromium with a script): Enter on the trigger opens; **Escape** closes and focus
returns to the trigger; **repeated trigger** closes with focus kept on it; **outside pointer** closes and the clicked
field keeps focus; **Tab / Shift+Tab** leave the sheet freely and it closes when focus leaves.

## 4. Why it fits the existing product

It is the same Pictures app: masthead, Idioma select, route navigation, 32px-radius papers, 18px fields, pill
buttons, Geist / Geist Mono and the exact light/dark tokens from `globals.css`. The spatial move only changes the
arrangement of the two blocks the owner asked to redesign, makes the identity readable at a glance (a "pass" that
names who you are and what access you hold) and gives the password task its own wide panel. The menu reuses the
sibling disclosure and simply makes identity explicit.

## 5. Eight axes

| Axis | This direction |
|---|---|
| Concept | Identity as a sticky pass, password as a seated security panel; a local rail spotlights one, and becomes a sliding track on narrow screens. |
| Layout | Desktop two-column workspace 340px + fluid (300px at 840–1099px); new/repeat fields paired ≥1100px; <840px a two-panel horizontal track inside a clipped viewport. |
| Navigation | Unchanged masthead + route nav; new segmented local rail «Identidad · Contraseña» (aria-pressed buttons); account disclosure with permission-scoped links. |
| Typography | Geist only: 24px H1, 20px panel titles, 18px semibold name, 20px semibold access value, 13px labels/hints; Geist Mono kept for «Sempertex». |
| Density | 28px panel insets desktop, 24px tablet, 20px phone; 16px row rhythm in the pass, 20px field rhythm with a ruled split between current and new password. |
| Components | Real shadcn/Base UI Button, Input, Skeleton, Spinner, Avatar(Fallback); Motion `layoutId` indicator; native details/summary menu and native selects; custom pass/track arrangement. |
| Colour | Pictures tokens only; accent on the primary action, focus ring, monogram and access chip; error/éxito tokens only for field errors, alert note and receipt; neutral rail and nav. |
| Motion | Glide-and-seat: horizontal seats, gliding indicator, sliding track, corner-unfolding menu; 560/380/200ms profiles, overshoot easing, reduced-motion parity. |

## 6. States in the mockup

Vista: «Mi cuenta», «Menú de cuenta abierto». Estado: Normal, Cargando (skeletons), campos vacíos, corta, más de 200,
no coinciden, contraseña actual incorrecta, Guardando, Error del servicio, Error de red, Contraseña cambiada, Menú:
cerrando sesión, Menú: error al cerrar sesión. In-product mock selects: **Acceso** (four plans, Administrador,
Empleado interno, Rol personalizado with accounts permission only = restricted links; plans/employee = no admin
links) and **Persona** (with name and company, no name, long name, long email). Idioma ES/EN and Tema claro/oscuro
are live. Mock data is labelled «Datos y operaciones simulados»; the submit simulates pending then success
(production must call the service; no client-only success).

## 7. Thumbnails

- `cuentas-admin@v2.r1.dir-b.html.candidate-1.html` — **chosen**: pass + security panel side by side, local rail,
  corner-unfolding menu.
- `cuentas-admin@v2.r1.dir-b.html.candidate-2.html` — identity canvas with a password inspector that slides in from
  the right. Rejected: the password form, a main job, would be one extra click away and hidden by default.

## 8. Audit results (actual)

- Build: `bitacora.py components mockup build` → 561 KB single file, offline.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass`.
- `audit_mockup.py` (1280 + 390, both themes, 104 renders, 668 focus stops):
  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- Extra Playwright checks: no horizontal overflow at 1280/768/390/360; dismissal/focus sequence above; fixture
  switching (admin/custom/plan links, unnamed fallback, EN labels); submit validation focus and success clearing;
  phone track `inert` swap and focus. Screenshots inspected at 1280 light/dark, 768, 390 light/dark and 360.
- Earlier iterations failed and were fixed: alignment false positives (a field column centred on the viewport;
  monogram text), summary padding, a menu that left the viewport at 360px, and an invisible rail indicator.

## 9. Open questions for the owner

- Unnamed account: SPEC says the email is the fallback for a missing name; this draft shows the email in the
  **Nombre** row too (so it appears twice). Keep that, or hide the Nombre row / show «—» when no name is stored?
- The 8–200 hint «Entre 8 y 200 caracteres.» and the too-long message are new copy stating the existing rule — acceptable?
- Network failure reuses the existing «No se pudo cambiar la contraseña. Inténtalo de nuevo.»; should it say
  something different from a service error?
- Should the menu keep «Cambiar tema» (as composed by the sibling shell) and leave Idioma in the masthead, or move
  Idioma into the menu too?
- Should «Planes» appear in the menu for staff and custom roles, or only for plan accounts?
- On phones, should the track open on Identidad (current default) or on Contraseña?

## 10. Concerns

- The surface paths named in the brief are absent from both read-only worktrees (`t12`, `asesor`); the current
  surface was read from the latest SP-2 verification snapshot instead. Tokens there match the sibling contracts.
- Unchanged v1 views are not redrawn in this file; the finalizer must keep `cuentas-admin@v1` as their reference.
- Desktop spotlight scale and the track are new interactions; production must keep both panels in the DOM and in the
  accessibility tree on desktop and apply `inert` only to the off-screen panel on narrow screens.
