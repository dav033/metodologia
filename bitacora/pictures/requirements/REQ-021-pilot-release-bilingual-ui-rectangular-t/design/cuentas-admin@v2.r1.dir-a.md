---
name: Ficha dividida
contract: cuentas-admin
version: 2
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v2
revision: r1.dir-a
subplan: SP-2
requirements: [R1, R3, R16, R17]
author: Designer
date: 2026-10-31
stance: "Operational: dense working information in the existing shell; hierarchy by type scale and grouping, precise quick transitions."
---

# Ficha dividida — direction A (cuentas-admin@v2, r1)

**Draft exploration; not approved.** This is one of three directions for the SP-2 v2 amendment. The owner picks one,
and a later finalization writes the canonical `cuentas-admin@v2` contract. This direction does not write that contract,
the plan or any repository file. `cuentas-admin@v1` (sign-in, activation, reset, notice gate, accounts, invitations,
roles) is unchanged and is not redrawn here.

Files: `cuentas-admin@v2.r1.dir-a.tsx` (entry), `.html` (built offline), `.json` (axes and evidence),
`.html.candidate-1.html` / `.candidate-2.html` (thumbnails).

## Approach — how it changes the existing surface

Current `/cuenta` (verified snapshot `SP-2-v2`, `src/app/cuenta/page.tsx`): a 676px column under the account bar, a
second Pictures header with Idioma, H1, a route rule, then two stacked 32px cards. «Tu identidad» shows Cuenta, Correo
electrónico, Rol and «Aviso de datos aceptado», and the password card stacks three full-width fields.

Direction A keeps the sibling shell (masthead with ring-and-dot brandmark, «Pictures | Sempertex», Idioma select, account
trigger, simulated-data footer). It changes only the following:

- **One divided paper instead of two cards.** On the left, a 340px identity ledger; on the right, the password form.
  Both answer the page's question in the first viewport at 1280px. Below 840px the ledger stacks above the form.
- **Identity ledger with explicit labels.** The rows are **Nombre** (stored name, 20px; the email in Geist Mono is the fallback only for a null, empty or blank name),
  **Correo**, then **Plan** + catalogue name for a plan account, or **Rol** + actual identity (Administrador,
  Empleado interno, custom role name with the caption «Rol personalizado»). **Empresa** appears only when the account
  data supplies one. «Aviso de datos aceptado» is removed from this view. There are no edit controls.
- **Denser password form.** «Contraseña actual» spans the full width. Nueva and Repite share one row from 1100px.
  «Entre 8 y 200 caracteres.» sits under Nueva. Each error appears under its own field, and service and network
  failures appear as a band above the fields. The submit button keeps a 196px minimum width, so «Guardando…» and the
  spinner do not shift the layout. On success the fields are cleared, focus moves to the status band and its check is drawn.
- **Heading row.** The H1 and the existing permission-scoped route nav (Cuentas / Roles y permisos / Mi cuenta) share
  one row over a drawn rule. The production page has a second Pictures header; it is dropped because the shared masthead already carries brand and Idioma.
- **Account popup.** The trigger stays a pill with the person's initial and real name (the visible name is hidden below 400px and kept in
  `aria-label`). The popup has four groups:
  1. Identity: initial, name (wraps), email in mono, and a neutral access pill («Plan · Designer Plus» or «Rol · Administrador»).
  2. Destinations: Mi cuenta (current page, check and weight), Planes, Administración and Roles y permisos (only with permission).
  3. Preferences: Cambiar tema.
  4. Session: Cerrar sesión.

  Idioma stays in the masthead, where the siblings put it.

## Interaction and motion detail

The grammar is precise quick cuts with the easing `cubic-bezier(.32,.72,0,1)`. Expressive is the default; natural and
subtle scale the durations down.

| Element | Trigger | Motion | Expressive / natural / subtle |
|---|---|---|---|
| `.acct-menu` | open | clip-path reveal from its top-right corner and opacity .4→1; closes instantly (no exit animation) | 200 / 160 / 110ms |
| `.menu-group > *` | open | rows step down 4px into place, staggered | 260ms, 28ms step / 200, 20 / 140, 12 |
| `.acct-trigger .chev` | expanded | 180° flip | 150 / 130 / 100ms |
| `.head-rule` | view load | rule draws from left (scaleX) | 1.6 × row duration |
| `.ficha-row` | load or fixture change | ledger rows register 6px from the left in sequence | 260ms + 28ms × index |
| `.pw-msg` | field error | height opens through grid-template-rows 0fr→1fr | 260 / 200 / 140ms |
| `.form-status` | error or success | band rises 4px; the success check draws its stroke | 260ms; 364ms draw |
| `.swap` | view change | quick opacity cut .2→1 | 260ms |

Reduced motion (OS setting, the «Quieto» option or `?still=1`) turns off every animation and transition; the final state shows immediately, including the drawn check.
Hidden tabs pause animations. Hover, press and focus feedback stays quick (150ms or less), and focus is a 3px accent outline with a 4px offset.

Dismissal and focus, verified in Chromium at 1280px:

- Escape closes the popup and returns focus to the trigger.
- Pressing the trigger a second time closes the popup; focus stays on the trigger.
- An outside pointer closes the popup and does not steal focus: clicking «Contraseña actual» leaves focus in that field.
- Enter and Space open the popup natively.
- Tab and Shift+Tab leave the popup without a trap and close it.

The popup is a disclosure group, not `role="menu"`, so arrow-key roving and focus trapping do not apply.

## Why it fits the existing product

- It uses the same masthead, tokens, Geist families, 32px paper, 18px fields, pill controls and neutral route nav as the
  sibling contracts and the production code. Nothing new is branded or coloured.
- The change is in composition and hierarchy: one paper instead of two cards, the name as the largest datum, explicit
  Nombre/Correo/Plan/Rol labels and grouped popup destinations. This matches the owner's «complete new layout» request
  without introducing a new page or a profile editor.
- The density follows the stance: hairline-ruled ledger rows, both tasks visible at once and no empty right half, while
  every target stays at least 44px.

## Eight axes

| Axis | Direction A |
|---|---|
| Concept | Operational account sheet: the ledger says who you are in Pictures, and the password form sits beside it in one paper. The popup is a dense identity header plus grouped destinations. |
| Layout | Shared masthead. The page is capped at 1040px. The H1 and route nav share one row over a drawn rule. One paper is split 340px \| flexible (300px from 840 to 1099px); below 840px it stacks. The new and repeated password fields pair from 1100px. Below 480px the ledger becomes label-over-value and the masthead wraps. |
| Navigation | The trigger is a native button with aria-expanded and aria-controls. The popup groups identity, destinations (Mi cuenta, Planes, plus Administración and Roles y permisos when permitted), the theme control and sign-out. Escape, repeated trigger, outside pointer and focus-out all close it. The in-page route nav keeps permission scoping. |
| Typography | Geist and Geist Mono. Sizes: H1 24px; section titles 17px; name 20px semibold; access 15px semibold; email 13px mono; labels 12px; form labels 14px medium. |
| Density | Ledger rows have 12px padding and hairline rules. Paper insets are 28px (20px on phone) and form gaps 16px. Controls are 44px; the popup is 320px wide. |
| Components | shadcn/Base UI Input, Button, Spinner, Skeleton and Separator; native selects; a custom disclosure popup; Lucide icons. |
| Colour | Pictures tokens only, mapped onto the shadcn roles. Accent appears only on the submit button, focus rings and the trigger initial. Errors and success use error/exito with their soft backgrounds. Navigation is neutral. |
| Motion | Clip-cut popup with instant close, stepped rows, drawn rule, ledger register, error height reveal, status rise with stroke-drawn check, chevron flip. Full reduced-motion parity. |

## Thumbnails

- **Candidate 1 — divided sheet (chosen).** Ledger on the left, form on the right in one paper. It stacks cleanly down to
  360px, keeps errors readable under each field, and shows identity and the task together.
- **Candidate 2 — identity strip.** Name, email and role in a three-column band, with the three password fields and the
  submit button on one row. It is denser at 1280px, but the inline errors crowd and it has to be rebuilt for phones
  anyway. Rejected.

## Views, states and fixtures in the mockup

- **Vista:**
  - Mi cuenta with the popup closed
  - Mi cuenta with the popup open
  - Another signed-in page («Herramientas» placeholder) with the popup open
- **Estado:**
  - idle
  - loading (page and trigger skeleton)
  - required
  - short
  - too long (>200)
  - mismatch
  - wrong current password
  - pending
  - service error
  - network error
  - success
- **Tema:** light and dark. **Movimiento:** expressive, natural, subtle, still. **Idioma** in the masthead: ES and EN.
- **«Mockup · Cuenta de ejemplo»** in-page fixture select:
  - Administrador, with name; both admin links
  - Empleado interno; no admin links
  - Custom role «Rol de prueba»; only Roles y permisos
  - Entusiasta, blank name; email fallback
  - Designer, long name
  - Designer Plus, long email plus «Empresa de ejemplo»
  - Master Designer

All data is neutral `@prueba.local` mock data. A free submit with valid input simulates the server-confirmed path. The
error results come from the Estado selector, so there is no client-only success claim beyond the labelled mock.

## Audit results (actual)

- Build: `bitacora.py components mockup build` produced 419 KB from 2036 source files, offline.
- `contrast.py`: «contrast: 158 pairs checked in light and dark, all pass».
- `audit_mockup.py`, default widths: «132 renders (132 combinations planned), 3872 text measurements, 720 focus stops». The
  first run reported `RESULT: FAIL — alignment 4, overflow 1`:
  - error icons made the error lines read as centred;
  - the trigger skeleton overflowed by 4px at 390px.

  After those fixes the run passed.
- `audit_mockup.py --widths 1280,768,390,360`, final run: «264 renders (264 combinations planned), 8008 text measurements,
  720 focus stops», **`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`**. Intermediate runs
  failed and were fixed:
  - alignment at 360px, the mismatch error;
  - padding on the trigger at 360px and then at 390px, caused by the truncated name. The name is now hidden below 400px.
- Behaviour script (Chromium, 1280px): all ten dismissal and focus checks pass. All 15 evidence selectors are visible,
  and all four motion selectors animate. No page errors.
- Screenshots inspected at 1280px (light idle; dark, popup open, mismatch), 768px (other page, popup open) and 390px (light, popup
  open, success, long email and company; dark loading). They led to four fixes:
  - the 8px vertical misalignment of the repeated-password field;
  - the phone popup sitting under the inspector bar;
  - the success check being invisible in still mode;
  - Sempertex being hidden on phone.

## Open questions for the owner

1. Should the hint «Entre 8 y 200 caracteres.» appear before the person types? It restates the existing validation and is not a new policy.
2. Should the line «Al cambiarla, esta sesión se renueva y tus otras sesiones terminan.» appear before submitting, or only in the success message as today?
3. Copy for the new error states: «La contraseña nueva debe tener como máximo 200 caracteres.» and the network-error
   text. Today's product has neither; the service-error text reuses the existing copy.
4. Empresa: `accounts.company` exists, but `OwnAccountRecord`/`getCurrentAccount` do not expose it. Should the
   loader expose it so the row can appear, or should the row stay absent for now?
5. Below 400px the trigger shows only the initial and the name stays in the popup and `aria-label`. Is that acceptable, or should the
   name stay visible on phones by moving Idioma?
6. Should «Tu cuenta está activa.» stay under the H1? It is kept as existing copy.

## Concerns

- The component paths the brief names (`src/components/cuentas/*`, `src/app/cuenta/page.tsx`, `src/lib/planes/catalogo.ts`)
  do not exist in the listed repositories `pictures-wt/t12` or `pictures-wt/asesor`. I read them read-only from the
  SP-2 verification snapshot `~/.local/share/bitacora-verify/pictures/REQ-021/SP-2-v2/`. Tokens and fonts come from
  t12 `globals.css` and its built Geist woff2 files.
- The sign-out action in the popup shows a labelled mock message instead of navigating.
