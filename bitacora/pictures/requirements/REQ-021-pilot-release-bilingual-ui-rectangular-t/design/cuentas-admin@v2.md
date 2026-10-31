---
contract: cuentas-admin
version: 2
status: draft
subplan: SP-2
requirements: [R1, R3, R16, R17]
owner: David
author: Designer
date: 2026-10-31
direction: Ficha en su sitio — direct manipulation (c)
source_revision: amend-1 (from r1.dir-c, owner-chosen)
source_behavior: cuentas-admin@v2.amend-1.behavior.md
amends: cuentas-admin@v2 finalization draft (design/cuentas-admin@v2.md, unchanged)
compatibility: breaking (scoped UI/interaction replacement)
supersedes_for: [own-account /cuenta identity and password area, shared signed-in account menu]
incorporates_by_reference: cuentas-admin@v1 (every other view, unchanged)
---

# cuentas-admin@v2 — Ficha en su sitio

## 1. Identity and traceability

**Draft; not approved for implementation.** Finalization of the owner's web-selected direction **Ficha en su sitio — direct manipulation (c), r1**. Choosing a direction does not approve this contract; owner visual approval is still pending (SPEC «Behavior — SP-2 account amendment (P-209)»: behavior confirmed 2026-10-31 13:08 with «Confirmar todo»). Designer grants no approval. After independent approval, **T2.11** copies the exact approved snapshot into `design/contracts/cuentas-admin@v2.md`; **T2.1** keeps owning v1 and v1 is never overwritten or regenerated.

Version scope: v2 replaces v1 **only** for the ordinary own-account surface (`/cuenta` identity and password area) and the shared signed-in account menu (presentation, identity, dismissal and focus). Sign-in, invitation activation, password reset, the mandatory data-notice gate, accounts/invitations administration and the role editor are **incorporated into v2 by reference** to the unchanged `cuentas-admin@v1` sections (F1–F6 and their views, states and acceptance criteria). Compatibility: **breaking — a scoped visual/interaction replacement** of those two surfaces, not a compatible additive change: v1's V6 identity grid, notice-version row, always-open password card and native-`details` menu without outside/Escape dismissal are no longer valid targets. No route, API, permission, consent or password-policy change.

Consumers: **every SP-2 UI task binds v2** — T2.3 (sign-in, activation, reset, notice re-acceptance: v1 sections by reference), T2.4 (account menu and Mi cuenta, as amended), T2.5 (administration screens: v1 sections by reference, under the v2 shared menu), T2.57 (redesign Mi cuenta and repair menu dismissal), T2.7 (visual review against v2) and T2.11 (copies the approved snapshot). T2.1 keeps owning v1, which stays unchanged. Shared menu composition: SP-8 owns the language selector inside the menu (round 15), SP-14 the Planes entry (round 10); theme stays the existing shell's responsibility; SP-10 supplies only the remaining-language composition (English copy of other screens), not theme ownership. v2 changes the menu's presentation and dismissal only and retains those controls.

Plan-change delta folded in this finalization (direction was drawn from `cuentas-admin@v2.r1.behavior.md`; current brief `cuentas-admin@v2.r1.chosen.behavior.md`): published source commit `6ec74192`; language stays in the account menu; Planes stays available to every signed-in role including staff/custom; theme composition unchanged; explicit Name row keeps the email fallback; EN system-role labels Administrator / Internal employee, custom-role names untranslated; 8–200 hints and too-long copy allowed; network errors reuse the generic failure; no acknowledgment button after success; T2.1 replaced by T2.11 as the v2 copy task. No composition, navigation, motion or token change was needed for this delta.

**Amendment 1 delta** (previous brief `cuentas-admin@v2.r1.chosen.behavior.md` → current `cuentas-admin@v2.amend-1.behavior.md`; owner feedback 2026-10-31 15:34). Not a redesign: the owner-chosen C composition, motion, tokens and every untouched decision stay as finalized.

1. *Classification* — v2 is a breaking scoped replacement (above); all SP-2 UI tasks bind v2 with unchanged v1 sections by reference; SP-10 is remaining language, not theme.
2. *Host shell* — the mockup now inherits the exact SP-8 composed host shell: layout-level account bar, then the page content. The page-level `CabeceraCuentas` (mark + «Idioma» select) and `NavegacionCuentas` route rule, removed by the SP-8 composition, are no longer reproduced on `/cuenta` or on the v1 Cuentas view (§5).
3. *ARIA repair* — the repeat-password field referenced `pw-repeat-help` while that node was absent (blank or unequal input). Each password field now references only a help/error node rendered at that moment (§7, §10, UI-AC-34…37). The same class of defect on the closed menu trigger (`aria-controls` to the unmounted popup) is repaired: `aria-controls` is present only while the popup is rendered.
4. *Q1–Q4 closed* with the settled SPEC/Planner dispositions (§12); no new owner interview.
5. *Mockup* — one added «Estado» switch, «Clave · coinciden» (editor open with equal values), so the blank / equal / mismatch descriptions are all reachable; «Clave · editor abierto» is relabelled «(vacío)».

Inputs (SHA-256; SPEC/PLAN re-hashed at amendment 1, finalization values superseded):

| Input | SHA-256 |
|---|---|
| `SPEC.md` (at amendment 1) | `6259a47b39e3de21a6364f99d5dd5012631279957945531f55fc4569d3a613ae` |
| `PLAN.json` (at amendment 1) | `aaa5941d5578487a3a026f728a23b2f281c511bfb03e904da1adf5f19b2e08c6` |
| `design/cuentas-admin@v2.amend-1.behavior.md` | `8b36dc144cd765106fecd6f4c7f1ce3b444a507af175079535c35ec3cb19ba31` |
| `design/cuentas-admin@v2.md` (finalization draft, unchanged) | `da3b799d4881c2e9431d2666a2680a0d665e336162b98570e2b0a3b3aa37339b` |
| `design/cuentas-admin@v2.html` (finalization mockup, unchanged) | `7c79e1c3b0c9a91412067b690b06b4ab802775e79a80f7c7c899d180ca079344` |
| `design/cuentas-admin@v2.r1.behavior.md` | `90d1d19cabf7d52cdbfc1ad8fd40b101cc0ec23e522e97affd4cd1a35e591a1f` |
| `design/cuentas-admin@v2.r1.chosen.behavior.md` | `2602333e9f000e666123b74e08049e5595dde9bdb56885b7098f4174675ac411` |
| `design/cuentas-admin@v2.r1.dir-c.md` | `cbf4ef8e91a61670725a057ef587432a24585cb02d0cbe17e8fd4181a450a9f8` |
| `design/cuentas-admin@v2.r1.dir-c.tsx` | `5808b43ba87915a5a7e847c5edc9a833a345562b6b0c86b0acb740eca3b44c65` |
| `design/cuentas-admin@v2.r1.dir-c.styles.ts` | `125dcd96b4bf8ea16dcda0e27c4343ead202eb156eff901f4ee8494283e3ce71` |
| `design/cuentas-admin@v2.r1.dir-c.html` | `7566cd4d4130c42cef81cd5d0648d2d022047a6afa054077f2ccbaa469f03649` |

Mockup: `design/cuentas-admin@v2.amend-1.html` (SHA-256 `63f4a7e014bcd9d053f10f09cd54ec8f51446a307ec6d09c67ce86528f6490a1`), built with the current offline builder (556 KB, 2032 source files, offline) from `design/cuentas-admin@v2.amend-1.tsx` (469 lines, SHA-256 `93299c609d6b8ed279f2c63eaf3b966eefbb20e93845da3eb748965ae8b9fd66`), a copy of `cuentas-admin@v2.r1.dir-c.tsx` edited only for this delta; it reuses the unchanged adjacent `cuentas-admin@v2.r1.dir-c.styles.ts`. Production surface read read-only at published commit `6ec74192eb0175827a9005ae2c152955cb0d220d` (via `/home/david/dev/.pictures-wt/login-redirect`, `git show`) and the composed SP-8-v2 verification snapshot (`afe025e3`: `src/app/layout.tsx` renders `BarraCuenta` before every page; `src/app/cuenta/page.tsx` starts with the H1; no `src/app` page renders `CabeceraCuentas`/`NavegacionCuentas`; `MenuCuenta` holds `SelectorIdioma`). `/home/david/dev/pictures` was not read or written.

## 2. Purpose and users

| View | User | Goal | Observable success |
|---|---|---|---|
| V6′ Mi cuenta (`/cuenta`) | Any signed-in person (four plan accounts, Administrador, Empleado interno, custom role) | Check who they are and what access they hold; occasionally change their password. | Name, email and the real access identity are readable at once; the password changes after service acknowledgment, this session is renewed and other sessions end. |
| Shared account menu (every signed-in page) | Same | Confirm identity, switch language, reach Mi cuenta, permitted administration, Planes, or sign out. | The popup opens from the header trigger, shows full name/email/access, and closes predictably without trapping focus. |

R1/R3/R16/R17 trace: the menu and profile display the access identity assigned under R16 using catalogue names from R17 (`plan-catalogue@1`); administration links appear only with the R3 permissions; R1's invitation/sign-in flows remain v1.

## 3. Information architecture and hierarchy

**Mi cuenta** — one sheet («Tu identidad» / «Your identity», 13px muted heading), in this order:

1. **Identity plate** (primary): 64px initial disc; then a `dl` with **Nombre / Name** (20px/600 — the sheet's largest text) and **Correo / Email** (15px).
2. **Ruled rows** (secondary): **Plan · <catalogue name>** for a catalogue plan account, otherwise **Rol / Role · <actual role>**; **Empresa / Company** only when the authenticated account projection carries a company.
3. **Contraseña / Password row** (the only action): masked `••••••••`, outline «Cambiar contraseña». The editor is progressive disclosure: hidden until requested, opened in place under its own row inside the same paper.

Removed from the ordinary profile: the «Aviso de datos aceptado» version/date row and the separate always-open «Cambiar contraseña» card. Consent storage, activation/re-acceptance text and route enforcement are unchanged (v1).

**Account menu** — popup groups, top to bottom: identity (40px initial, full name wrapping, email, access chip «Plan Designer Plus» / «Rol Administrador»); language row («Idioma» + ES/EN pair, SP-8); links (Mi cuenta, Administración*, Roles y permisos*, Planes); ruled «Cerrar sesión» with its inline alert. *Only with the corresponding permission.

Rationale: the page is visited to confirm identity; the always-open three-field form dominated it. Emphasis goes to the name; colour is reserved for the primary submit, focus, success and errors.

## 4. Design system and visual language

Tokens: exact Pictures `src/app/globals.css` tokens, both themes, no new value — `fondo`, `superficie`, `superficie-suave` (open password row and drawer), `superficie-2` (access chip, meter track), `borde`, `borde-suave` (rules), `texto`, `texto-suave` (labels), `texto-secundario` (subtitle), `acento` (primary submit, focus ring, active trigger edge, meter fill), `acento-suave` (initial discs, active-trigger halo), `exito`/`exito-suave` (meter in range, «Coinciden.», success seal), `error`/`error-suave` (invalid fields, summary). No theme control is added to the menu or page; theme remains the existing shell's responsibility (stored choice applied before first paint in `layout.tsx`, `prefers-color-scheme` otherwise) and is unchanged. SP-10 supplies only remaining-language composition, not theme.

Typography: Geist Sans / Geist Mono only. H1 24px/600; identity name 20px/600 (18px below 640px); email 15px; row labels 13px `texto-suave`; row values 15px/550; field labels 14px/600; help/errors 13px; mono 12px only for the mockup footnote (not product copy).

Shape and spacing: 676px centred column (unchanged); paper radius 32px (24px phone), 1px `borde-suave`; row grid `132px | 1fr | auto`, min-height 64px, insets 28px desktop / 20px phone; password fields 48px tall, 18px gaps; pill buttons; popup 304px wide, radius 24px, 16px padding, `shadow-float`.

Components (`source:id variant state`, import):

| Component | Use | Import |
|---|---|---|
| `shadcn:button outline idle/hover/pressed/focus` | «Cambiar contraseña» row action, «Cancelar» | `import { Button } from "@/components/ui/button"` |
| `shadcn:button primary idle/pending/disabled` | editor submit «Cambiar contraseña» / «Guardando…» with spinner | same |
| `shadcn:input password idle/invalid/disabled` | Contraseña actual, Contraseña nueva, Repite la contraseña nueva (`aria-invalid`, `aria-describedby`) | `import { Input } from "@/components/ui/input"` |
| `shadcn:skeleton default loading` | loading sheet (disc, two lines, two rows) | `import { Skeleton } from "@/components/ui/skeleton"` |
| `motion:AnimatePresence default enter/exit` | popup and drawer presence | `import { AnimatePresence, motion } from "motion/react"` |
| `pictures:SelectorIdioma pair es/en` | language pair inside the menu (SP-8, existing) | `@/lib/idioma/cliente` |
| `custom:account-trigger pill closed/open/pressed` | header disclosure button, initial + one-line name + chevron | — |
| `custom:account-popup default open/sign-out-pending/sign-out-error` | popup container and groups | — |
| `custom:access-chip plan/role` | menu access identity | — |
| `custom:identity-plate default named/fallback/long` | initial + Nombre/Correo `dl` | — |
| `custom:ruled-row default/editing` | Plan/Rol, Empresa, Contraseña rows | — |
| `custom:length-meter below/in-range` | 4px meter under Contraseña nueva (decorative, `aria-hidden`) | — |
| `custom:field-error inline` / `custom:form-summary alert` / `custom:success-seal status` | errors and success | — |

Icons (lucide): `ChevronDown` (trigger), `CircleAlert` (errors), `Check` (help/match), `LoaderCircle` (pending); all `aria-hidden`.

Motion — tactile press/settle grammar: presses compress quickly (trigger `scale(.95)`, row/menu actions `.95–.97`, ES/EN `.92`; 90ms `cubic-bezier(.4,0,.7,1)`); arrivals settle with small overshoot `cubic-bezier(.34,1.42,.64,1)` at 460ms expressive / 300ms natural / 170ms subtle: sheet rise, initial press-settle, rows staggered 55ms, popup spring from the trigger's top-right corner (`opacity 0, y −10, scale .94` → rest; exit 120ms), drawer height spring with staggered fields, 260ms sideways nudge on an invalid field, success seal with drawn check stroke. Chevron rotates 180° when open. Transform/opacity only; content legible mid-motion. Production default is the natural profile unless the product already defines another.

Focus: 2px `acento` outline, 2px offset, on every interactive element; active trigger also shows `acento` border and a 3px `acento-suave` halo.

## 5. Navigation and interaction model

Entry: the account trigger in the full-width 64px signed-in bar (`BarraCuenta` → `MenuCuenta`) on every signed-in page; `/cuenta` from «Mi cuenta» in the menu.

Header and page shell: v2 inherits the **exact integrated host shell of the SP-8 composition** and neither adds nor removes shell controls: the layout-level 64px account bar (`BarraCuenta` → `MenuCuenta`) on every signed-in page, then the page's own content in the 676px column (H1, subtitle, sheet). The page-level `CabeceraCuentas` (mark + «Idioma» select) and `NavegacionCuentas` route rule present at published `6ec74192` were removed by the SP-8 composition and **must not be reintroduced** on `/cuenta` or the administration pages; navigation between Mi cuenta, Administración, Roles y permisos and Planes is the account menu's. Language switching lives in the account menu (round 15) and may not move out of it; theme stays with the existing shell.

Menu trigger: a disclosure control with `aria-expanded`; `aria-controls` names the popup id only while the popup is rendered (absent when closed, so it never references a missing node); no `role="menu"`/`menuitem`, no focus trap. Accessible name «Cuenta: <full display name>» / «Account: <full display name>». Native `<details>/<summary>` or a button is a technical choice, acceptable only when layout, every dismissal and every focus behaviour below are identical (settled, §12).

Menu outcomes:

| Action | Result |
|---|---|
| Click / Enter / Space on trigger (closed) | Opens; focus stays on trigger. |
| Repeated trigger activation (open) | Closes; focus stays on trigger. |
| Escape while open (focus anywhere) | Closes; focus returns to trigger. |
| Pointer down outside the popup and trigger | Closes without `preventDefault`; the clicked focusable target receives focus and performs its action. |
| Tab / Shift+Tab out of popup | Focus moves normally; the popup closes once focus is outside trigger+popup. |
| Mi cuenta / Administración / Roles y permisos / Planes | Navigate to `/cuenta`, `/admin/cuentas`, `/admin/roles`, `/planes`; current page link has `aria-current="page"`. |
| ES / EN | Existing SP-8 language switch (`aria-pressed`). |
| Cerrar sesión | Existing `POST /api/cuentas/salir`; pending label, then `/login`, or inline `role="alert"` error. |

Mi cuenta outcomes: «Cambiar contraseña» (row) opens the editor and moves focus to «Contraseña actual». «Cancelar» or Escape inside the editor (not while pending) collapses it, clears all three secrets and returns focus to the row's «Cambiar contraseña». Submit runs §6 F3. After success focus returns to «Cambiar contraseña».

## 6. Flows

**F1 — Unchanged v1 flows.** Sign-in, invitation activation with explicit notice consent, reset, mandatory notice re-acceptance, accounts/invitations, role editor: exactly `cuentas-admin@v1`.

**F2 — Account menu.** 1) Person activates trigger → popup settles under it. 2) Reads full name (wrapping), email, access chip. 3) Chooses a link, ES/EN or sign-out — or dismisses by repeated trigger, Escape, outside pointer or tabbing out (§5).

**F3 — Change password.**
1. Press «Cambiar contraseña» → editor opens; focus on «Contraseña actual».
2. Type; live feedback: meter fills toward 8 characters and turns `exito` inside 8–200 with «Entre 8 y 200 caracteres.» marked with a check; «Repite la contraseña nueva» shows «Coinciden.» when equal and non-empty. Typing after an error clears the error state.
3. Submit → client validation in production order: any empty → «Completa los tres campos de contraseña.» summary + «Este campo es obligatorio.» on each empty field; new < 8 → too-short; new > 200 → too-long; new ≠ repeat → mismatch. The first failing rule wins.
4. Valid → pending: fields and both buttons disabled, submit shows spinner + «Guardando…», form `aria-busy`.
5. Service responses: wrong current password → «Contraseña actual» marked invalid with its message, values kept for correction; service or network failure → generic summary «No se pudo cambiar la contraseña. Inténtalo de nuevo.», values kept, retry allowed; acknowledged success → editor collapses, secrets cleared, success seal (role=status) under the row, focus to «Cambiar contraseña».
6. Server keeps current-password verification, 8–200 validation, current-browser session renewal and invalidation of other sessions. No client-only simulated success in production (the mockup simulates: current password «incorrecta» → wrong-password state).

## 7. View specifications

### V6′ Mi cuenta (`/cuenta`)

- Shell: inherited SP-8 host shell (§5) — 64px account bar with trigger at right; 676px column; H1 «Mi cuenta» / «My account»; subtitle «Tu cuenta está activa.» / «Your account is active.»; the sheet 24px below the subtitle; no page-level header, «Idioma» select or route rule.
- Sheet `section[aria-labelledby]` heading «Tu identidad» / «Your identity».
- Identity plate: initial = first character of the display name, upper-cased (`aria-hidden`). `dl`: «Nombre»/«Name» → stored name trimmed, or the email when the stored name is null, empty or whitespace (the Name row is kept even though email is also shown); «Correo»/«Email» → email. Both wrap (`overflow-wrap:anywhere`), never truncate.
- Access row: catalogue plan account → label «Plan», value from `plan-catalogue@1` (ES Entusiasta / Designer / Designer Plus / Master Designer; EN Enthusiast / Designer / Designer Plus / Master Designer). Otherwise label «Rol»/«Role», value the actual role: ES «Administrador» / «Empleado interno», EN «Administrator» / «Internal employee»; custom roles show their user-authored name as written in both languages. Never infer a plan for staff/custom accounts, even with every tool or a plan-like role name.
- Empresa/Company row: optional and read-only, only when the local authenticated projection supplies the account's actual company (settled); no editor; no change to the shared account-service contract; never invented.
- Password row: «Contraseña»/«Password», masked value with accessible name «Contraseña guardada»/«Saved password», outline «Cambiar contraseña»/«Change password».
- Editor (in-paper drawer, `role="region"` labelled by the Contraseña row label, `superficie-suave`, dashed top rule): optional summary; three labelled password fields (`autocomplete` current-password / new-password / new-password; `maxLength=200` on new/repeat); help/error under each; actions primary «Cambiar contraseña» + outline «Cancelar»/«Cancel».
- Field descriptions (amendment 1): `aria-describedby` on each password input names **only a node rendered at that moment**, recomputed on every render, in ES and EN:

  | Field | Blank / typing, no error | Equal (repeat = new, non-empty) | Error state |
  |---|---|---|---|
  | Contraseña actual | none | none | its error («Este campo es obligatorio.» or wrong-current message) |
  | Contraseña nueva | the always-rendered hint «Entre 8 y 200 caracteres.» | hint | its error (required / too short / too long) |
  | Repite la contraseña nueva | **none** (no help node exists while blank or unequal) | «Coinciden.» / «They match.» | its error (required / mismatch) |

  The help and error of one field share one id slot (`pw-<field>-help`) but only one of them is rendered at a time; when neither is rendered the attribute is omitted, never left pointing at an absent id.
- No profile, plan or role editing; no notice version/date.

### Shared account menu

- Trigger pill (min-height 44px, max-width `min(260px, 100vw − 32px)`): 28px initial disc, display name on one line (owner-selected C truncation: first 25 characters + ellipsis; full name in the accessible name, the open popup and the profile), chevron.
- Popup (304px, `max-width: calc(100vw − 32px)`, anchored right, 8px below trigger; below 640px a fixed non-modal sheet 16px from both viewport edges under the bar, overlapping page content without inert background):
  - identity: 40px initial; full name (wraps, no truncation); email (wraps); access chip `<label> <value>` per §7 V6′ rules;
  - «Idioma»/«Language» + ES/EN pair (`role="group"`, `aria-pressed`);
  - links: «Mi cuenta», «Administración» (needs `administracion_usuarios`), «Roles y permisos» (needs `administracion_roles`), «Planes»/«Plans» (every signed-in role, including staff and custom);
  - ruled «Cerrar sesión»/«Sign out»; pending «Cerrando sesión…»; error `role="alert"` «No se pudo cerrar la sesión. Inténtalo de nuevo.».
- Copy source: `textos-cuenta.ts` plus the v2 labels in §7/§8 (Nombre/Name, Correo/Email, Plan, Empresa/Company, Contraseña/Password, Cancelar/Cancel, help, «Coinciden.»/«They match.» and too-long copy).

## 8. States

| State | What appears | What can be done / recovery |
|---|---|---|
| Menu closed | Trigger only, `aria-expanded=false`. | Open. |
| Menu open | Popup per §7; trigger halo. | Links, ES/EN, sign-out, dismiss (§5). |
| Restricted / no admin links | Plan, employee and custom accounts without permissions: only Mi cuenta and Planes. | — |
| Administrator | Administración and Roles y permisos also shown. | — |
| Sign-out pending | Button disabled, «Cerrando sesión…». | Wait. |
| Sign-out error | Alert under the button; button re-enabled. | Retry. |
| Named account | Name in Nombre, menu and trigger. | — |
| Absent name (null/empty/whitespace) | Email in Nombre row, menu name and trigger; initial from email. | — |
| Long name/email/company | Wrap in profile and popup; trigger truncates with ellipsis. | — |
| Four plans / Administrador / Empleado interno / custom role | Plan or Rol row and chip per §7. | — |
| Loading | Sheet skeleton: 64px disc, two lines, two 44px rows; `aria-busy`. | Wait. |
| Password idle (closed) | Masked row + «Cambiar contraseña». | Open editor. |
| Editor open (blank) | Three empty fields, meter at 0, hint. Only Contraseña nueva is described (by the hint). | Type, submit, cancel/Escape. |
| Editor open, values equal | Meter full in `exito`, hint with check, «Coinciden.»/«They match.» under the repeat field, which is now described by it. | Submit, cancel/Escape. |
| Required | Summary «Completa los tres campos de contraseña.» (`role=alert`); each empty field invalid with «Este campo es obligatorio.». | Fill fields. |
| Too short | New field invalid: «La contraseña nueva debe tener al menos 8 caracteres.». | Correct. |
| Too long | New field invalid: «La contraseña nueva debe tener como máximo 200 caracteres.» (restates the existing rule). | Correct. |
| Mismatch | Repeat field invalid: «Las contraseñas nuevas no coinciden.». | Correct. |
| Wrong current password | Current field invalid: «La contraseña actual no es correcta. Inténtalo de nuevo.». | Correct, resubmit. |
| Pending | Fields/buttons disabled, spinner «Guardando…», `aria-busy`. Help text keeps ≥4.5:1 (no opacity on text). | Wait; Escape ignored. |
| Service / network error | Summary «No se pudo cambiar la contraseña. Inténtalo de nuevo.» (`role=alert`); values kept. | Retry or cancel. |
| Acknowledged success | Editor collapsed, secrets cleared; seal (`role=status`) «Contraseña cambiada. Esta sesión se renovó; tus otras sesiones terminaron.» with check; stays until the editor reopens or the page changes. No dismiss button. | Continue; reopen editor. |
| Empty | Not applicable: a signed-in person always has an email and an access identity. | — |
| Permission-denied | Not applicable to `/cuenta` (every signed-in person); unauthenticated → existing redirect to `/login`. | — |
| Offline | Covered by the generic network failure state. | Retry. |

EN copy: «Complete all three password fields.», «This field is required.», «The new password must be at least 8 characters.», «The new password must be at most 200 characters.», «The new passwords do not match.», «The current password is incorrect. Try again.», «Could not change the password. Please try again.», «Password changed. This session was renewed; your other sessions ended.», «Saving…», «Between 8 and 200 characters.», «They match.», «Signing out…», «Could not sign out. Please try again.».

Transitions: see §4 motion; error nudge only on the field that became invalid; reduced motion shows final states instantly.

## 9. Responsive behavior

Supported: 1280×900 and 390×844 (explicit dismissal/focus cases), 768px tablet, 360px contractual floor. No horizontal page overflow or clipped control at any width.

| Range | Layout |
|---|---|
| ≥1024px | Bar padding 32px; column 676px, insets 28px; rows `132px | 1fr | auto`; popup 304px anchored right under trigger. |
| 640–1023px | Bar padding 24px; otherwise as desktop. |
| <640px | Bar padding 16px; column insets 20px; paper radius 24px; plate disc 48px, name 18px; rows stack label above value, row action full width; editor actions full width; popup becomes fixed non-modal sheet 16px from both edges under the bar; trigger max-width `100vw − 32px`, name truncates. |

Long strings wrap everywhere except the trigger name. No page-level header exists to wrap (SP-8 host shell); the bar holds only the right-aligned trigger.

## 10. Accessibility targets

Target WCAG 2.2 AA (awaiting rendered verification in production):

- Semantics: `section` + `h2` for the sheet; `dl/dt/dd` for identity and rows; `form noValidate` with labelled inputs; drawer `role="region"` labelled by the row label; disclosure trigger with `aria-expanded`/`aria-controls`; no menu roles.
- Errors: invalid inputs carry `aria-invalid="true"` and `aria-describedby` pointing to their rendered message. Every IDREF (`aria-describedby`, `aria-labelledby`, `aria-controls`) references only ids rendered at that moment, per the §7 field table; when no description node is rendered the attribute is omitted. The dangling repeat-field reference demonstrated in the finalization mockup is repaired in this amendment's mockup and must not exist in production (UI-AC-34…37). Summary uses `role="alert"`; success uses `role="status"`; sign-out error `role="alert"`.
- Keyboard: every control reachable in visual order; Enter/Space open the trigger; Escape as in §5; no focus trap; focus moves per §5/§6.
- Accessible names: trigger «Cuenta: <full name>»; masked value «Contraseña guardada»; language group «Idioma»; decorative icons/meter `aria-hidden`.
- Contrast: text ≥4.5:1, control edges and focus ≥3:1 in light and dark; pending must not lower text contrast.
- Targets ≥44px tall for trigger, menu links, sign-out and row action; fields 48px.
- Reflow to 320 CSS px without loss (360px contractual floor verified); 200% zoom without clipping.
- Reduced motion: OS preference removes travel/overshoot and shows final states; animations pause in hidden tabs.
- `lang` attribute follows the selected language on bar, popup and main.

## 11. Visual acceptance criteria and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | 1280 | Mi cuenta, Designer Plus + empresa | One sheet shows initial, Nombre, Correo, «Plan · Designer Plus», «Empresa», Contraseña row; no «Aviso de datos aceptado» row. |
| UI-AC-02 | 1280 | Mi cuenta | The identity name is the largest text inside the sheet. |
| UI-AC-03 | 1280 | Each of four plans | Access row label «Plan» with the catalogue name (Entusiasta, Designer, Designer Plus, Master Designer). |
| UI-AC-04 | 1280 | Administrador / Empleado interno / custom | Access row label «Rol» with the actual role; no «Plan» row. |
| UI-AC-05 | 1280 | EN, Administrador / Empleado interno / custom | Values read «Administrator», «Internal employee», and the custom name unchanged. |
| UI-AC-06 | 390 | Absent name | Nombre row is present and shows the email; Correo row also shows the email; no dash or invented name. |
| UI-AC-07 | 360 | Long data, menu open | Full long name and email wrap inside the popup; trigger name ends in an ellipsis; no horizontal page scroll. |
| UI-AC-08 | 1280 | No company | No Empresa row is rendered. |
| UI-AC-09 | 1280 | Password closed | Only one «Cambiar contraseña» control is visible on the page and no password field is rendered. |
| UI-AC-10 | 1280, 390 | Editor open | After pressing «Cambiar contraseña», the editor appears under the Contraseña row inside the same paper and focus is on «Contraseña actual». |
| UI-AC-11 | 1280 | Editor open, Cancelar | Pressing «Cancelar» collapses the editor, the three fields are empty on reopen, and focus is on «Cambiar contraseña». |
| UI-AC-12 | 390 | Required | Summary alert at top of editor plus «Este campo es obligatorio.» under each empty field. |
| UI-AC-13 | 390 | Too short | Contraseña nueva has a red edge and the too-short message directly under it. |
| UI-AC-14 | 1280 | Too long | Contraseña nueva shows «La contraseña nueva debe tener como máximo 200 caracteres.». |
| UI-AC-15 | 1280 | Mismatch | The mismatch message is under «Repite la contraseña nueva». |
| UI-AC-16 | 1280 | Wrong current password | The message is under «Contraseña actual» and the field is marked invalid. |
| UI-AC-17 | 768 | Typing a valid new password | Meter is full and success-coloured; «Entre 8 y 200 caracteres.» shows a check; equal repeat shows «Coinciden.». |
| UI-AC-18 | 1280 | Pending | All three fields and both buttons are disabled; submit shows a spinner and «Guardando…». |
| UI-AC-19 | 1280 | Service/network error | Summary alert «No se pudo cambiar la contraseña. Inténtalo de nuevo.»; entered values remain. |
| UI-AC-20 | 768 | Success | Editor collapsed; success seal with check under the Contraseña row; focus on «Cambiar contraseña»; no dismiss button. |
| UI-AC-21 | 1280, 390 | Menu open | Popup shows initial, full name, email, access chip, Idioma ES/EN pair, Mi cuenta, Planes, Cerrar sesión. |
| UI-AC-22 | 1280 | Administrador, menu open | Administración and Roles y permisos appear; for plan/employee/custom without permission they do not. |
| UI-AC-23 | 1280 | Empleado interno or custom, menu open | «Planes» link is present. |
| UI-AC-24 | 1280, 390 | Menu open, Escape | Popup closes and focus is on the trigger. |
| UI-AC-25 | 1280, 390 | Menu open, trigger pressed again | Popup closes and focus stays on the trigger. |
| UI-AC-26 | 1280, 390 | Menu open, click on page «Cambiar contraseña» | Popup closes and the clicked control both receives focus and performs its action. |
| UI-AC-27 | 1280, 390 | Menu open, Shift+Tab / Tab out | Focus leaves to the adjacent element and the popup is closed. |
| UI-AC-28 | 390 | Menu open | Popup spans the viewport with 16px side margins beneath the bar; page content behind stays interactive (non-modal). |
| UI-AC-29 | 1280 | Sign-out error | Alert «No se pudo cerrar la sesión. Inténtalo de nuevo.» under «Cerrar sesión». |
| UI-AC-30 | 1280 | Loading | Skeleton disc, two lines and two rows inside the sheet. |
| UI-AC-31 | All | Light and dark | Text ≥4.5:1, control edges/focus ≥3:1, visible 2px `acento` focus ring. |
| UI-AC-32 | All | Reduced motion | Popup, drawer, rows and seal appear in final position without travel or overshoot. |
| UI-AC-33 | 1280 | Cuentas page (v1), admin, menu open | The same popup renders over the unchanged v1 Cuentas page; «Administración» carries `aria-current="page"`, «Mi cuenta» does not. |
| UI-AC-34 | 1280, 390 · ES, EN | Editor open, blank | Contraseña actual and Repite la contraseña nueva have no `aria-describedby`; Contraseña nueva references the rendered hint. |
| UI-AC-35 | 1280, 390 · ES, EN | Editor open, equal values (preset or typed) | Repite la contraseña nueva references the rendered «Coinciden.»/«They match.» node; not `aria-invalid`. |
| UI-AC-36 | 1280, 390 · ES, EN | Unequal while typing; then submitted mismatch | While typing: repeat field has no `aria-describedby`. After submit: `aria-invalid="true"` and it references the rendered mismatch message. |
| UI-AC-37 | All | Every view and state, menu open or closed | No `aria-describedby`, `aria-labelledby` or `aria-controls` references an id absent from the DOM; the closed trigger has no `aria-controls`. |
| UI-AC-38 | 1280, 390 | `/cuenta` and Cuentas (v1) | No page-level brand header, «Idioma» select or account route rule under the bar; the H1 is the first page content (SP-8 host shell). |

Verification run on the exact artifact `design/cuentas-admin@v2.amend-1.html` (SHA-256 `63f4a7e0…90a1`, 2026-10-31):

- `contrast.py`: **158 pairs checked in light and dark, all pass** (exit 0).
- `audit_mockup.py` (default widths): **276 renders (276 planned), 6008 text measurements, 806 focus stops — RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems** (exit 0).
- `audit_mockup.py --widths 1280,768,390,360`: **552 renders (552 planned), 12016 text measurements, 806 focus stops — RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems** (exit 0).
- Scripted Playwright ARIA + interaction check (`?motion=still`, 1280×900 and 390×844, each in ES and EN): **72/72 pass** — no dangling `aria-describedby`/`aria-labelledby`/`aria-controls` in any of 3 views × 23 states; blank, preset-equal, typed-unequal, typed-equal, cleared and submitted-mismatch descriptions per UI-AC-34…36; closed trigger without `aria-controls`; open by click, Planes and ES/EN present, Escape closes with focus on trigger, repeated trigger closes with focus kept, outside pointer closes while the clicked «Cambiar contraseña» acts, Shift+Tab out closes; no page-level header/«Idioma» select/route rule; no horizontal overflow. The same script run on the unchanged finalization mockup `design/cuentas-admin@v2.html` fails (repeat field → absent `pw-repeat-help`; closed trigger → absent `account-menu-panel`), so the check detects the repaired defects.
- Screens inspected: 1280 light «Clave · coinciden»; 390 dark «Menú abierto · Datos largos».

Mockup controls: «Vista» Mi cuenta (/cuenta) · Menú abierto · Menú en Cuentas (v1). «Estado» Designer Plus + empresa, four plans, Administrador, Empleado interno, Rol personalizado, Sin nombre, Datos largos, Menú cerrado, Cargando, ten password states (editor abierto (vacío), coinciden, obligatorios, corta, larga, no coinciden, actual incorrecta, guardando, error servicio/red, cambiada), Salida pendiente/error. «Tema» light/dark; motion profiles expressive/natural/subtle/Quieto (reduced-motion parity). ES/EN is switched in the product through the account menu's language pair. Mock data is clearly sample (`@prueba.local`).

## 12. Open questions and assumptions

Confirmed decisions (owner/Planner, not open): language in the account menu (round 15); Planes for every signed-in role (round 10); theme stays the existing shell's responsibility; explicit Name row with email fallback; EN system-role labels; custom-role names untranslated; 8–200 hints and too-long copy; generic copy for network errors; no acknowledgment button after success; non-modal popup overlap on phones, one-line truncated trigger and account/password grouping are visible choices of this composition; v2 is a breaking scoped replacement bound by every SP-2 UI task.

Settled finalization dispositions (former Q1–Q4, closed by the SPEC/Planner dispositions in the amendment brief; no new owner interview):

- Former Q1 — host shell: **inherit the exact SP-8 composed host shell**. The page-level «Idioma» select and `CabeceraCuentas`/`NavegacionCuentas` are not resurrected; language remains in the account menu (§5, UI-AC-38).
- Former Q2 — company: **optional, read-only actual company is allowed** through the local authenticated projection; shown only when that projection carries it; no editor, no shared-contract change (§7).
- Former Q3 — trigger element: native `<details>/<summary>` versus an equivalent button is a **technical choice**, valid only with identical layout, dismissal and focus semantics (§5).
- Former Q4 — truncation: **owner-selected C truncation accepted**; the full name stays in the popup, the profile and the trigger's accessible name (§7).

Open questions: **none.** Pending (not a question): owner visual approval of this draft and of SP-2; P-209 stays open until the owner approves a later published version. Permission, password, session and consent rules are unchanged.

Assumptions: the account read model already exposes display name, email, roles and permissions; plan accounts expose a canonical plan id resolvable through `plan-catalogue@1`; EN system-role labels are presentation-only mappings (production stores Spanish names).
