# Brief de interfaz — SP-2 · Sign-in, invitation and administration screens

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

A person signs in with email and password, activates an invitation link and accepts the data notice; an administrator invites people, assigns one of the four access plans or another role, creates roles by choosing permissions, and deactivates or deletes accounts.

## Requisitos que cubre

- R1: When an administrator invites an email, the system shall let that person create a password and sign in; open registration shall not exist.
- R3: When an administrator creates a role, the system shall let them choose its permissions from a defined list; the three initial roles shall exist.
- R16: When an administrator assigns one of the four access plans to a Usuario account, the system shall grant on the server exactly that plan's tools, cumulatively: Entusiasta the assisted chat and the balloon counter; Designer the same tools (its higher chat limits wait for the limit values); Designer Plus adds the cost calculator; Master Designer adds the Taller 3D; Empleado interno and Administrador shall hold every plan tool (amended 2026-10-27, round 10).
- R17: The system shall hold the four access plans in one plan catalogue — name, monthly price in COP and USD (Entusiasta free; Designer COP 20,000 / USD 7; Designer Plus COP 45,000 / USD 14; Master Designer COP 70,000 / USD 25), included tools in cumulative order and whether each tool is available yet — and every screen and permission that names a plan shall read it from that catalogue.

Secciones de SPEC.md que nombran este subplan (léelas): «Data-processing notice (v1, SP-2)»; «Behavior — SP-2 account amendment (P-209)»

## Criterios de producto

- Full new /cuenta and password composition, actual identity and correct access label, no consent metadata in ordinary profile, responsive ES/EN, all password states, unchanged security invariants and tested dismissal/focus.
- Only SP-2 changes contract; analyze shared menu composition with SP-8, SP-10 and SP-14, retaining their language/theme/plans controls without blanket contract replacement.
- Password-field aria-describedby references only help/error nodes actually rendered in blank, matching and mismatching states in ES/EN; the final mockup and production target must not retain a demonstrated dangling ARIA reference.

## Flujos de usuario

1. Existing sign-in, activation, reset, mandatory notice and administration
   1. Preserve cuentas-admin@v1 outside F7/V6 and the shared account menu.
   2. Keep six system roles, catalogue-owned plan assignments, custom permissions and all existing consent/security behavior.
2. Account menu and identity
   1. Open from the existing product header; show the real person name, email and actual access identity.
   2. Close by repeated trigger, outside pointer or Escape; preserve native keyboard activation and predictable focus.
   3. Choose Mi cuenta, permitted administration, plans, language/theme controls where currently composed, or sign out.
3. My account and password redesign
   1. Read a clearly labelled name and email in a redesigned identity area.
   2. Read Plan plus the catalogue name only for a catalogue plan account; otherwise read actual administrator, internal employee or custom-role identity.
   3. Read optional company only when actual existing account data supplies it; add no field editor.
   4. Enter current password, new password and confirmation; correct validation or current-password errors.
   5. Confirm service success, clear secrets and remain signed in with a renewed session; other browser sessions end.

## Pantallas y estados

- Keep unchanged login, activation, reset, mandatory data-notice gate, accounts/invitations and role administration from v1.
- Redesign /cuenta identity and password area as the complete owner-requested new layout within existing Pictures shell/tokens.
- Shared menu closed/open; named/absent-name/long-name/long-email fixtures; each of four plans, administrator, employee, custom role; restricted/no administrator links.
- Password idle, required/short/too-long/mismatch, wrong current password, pending, service/network error, acknowledged success; ES/EN, light/dark, reduced motion.
- 390x844 and1280x900 explicit dismissal/focus cases,768px tablet and360px contractual floor; no clipped controls or horizontal page overflow.

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/cuenta`, `existing shared signed-in account menu`
- paths: `src/components/cuentas/MenuCuenta.tsx`, `src/app/cuenta/page.tsx`, `src/components/cuentas/CambiarContrasena.tsx`, `src/components/cuentas/textos-cuenta.ts`, `src/components/cuentas/BarraCuenta.tsx`, `src/lib/cuentas/cuenta-actual.ts`, `src/lib/planes/catalogo.ts`
- components: `MenuCuenta`, `CambiarContrasena`, `BarraCuenta`, `CabeceraCuentas`, `NavegacionCuentas`
- screenshots: `/home/david/.local/share/bitacora-solver/pictures/20261031-123425-067d/account-open-1280.png`, `/home/david/.local/share/bitacora-solver/pictures/20261031-123425-067d/account-open-390.png`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: Read published immutable commit6ec74192eb0175827a9005ae2c152955cb0d220d via /home/david/dev/.pictures-wt/login-redirect; never read/write /home/david/dev/pictures. Extend approved cuentas-admin@v1 (selected Parte de acceso); preserve all views/shell/navigation not affected by the owner request. Preserve every v1 artifact unchanged. Evidence: evidence/owner-rejected/SP-2-v2.md and RUN.solver/20261031-123425-067d/AMENDMENT.md. Owner confirmed behavior at13:08 with Confirmar todo; visual approval remains pending. Existing named-account rendering already falls back to email; current synthetic administrator has no display_name. Show both actual-name and absent-name states; never invent a person name or infer data loss.

## No debe cambiar

- No new route, product rebrand, new font/palette, self-service profile/plan/role editing, plan purchases or permission policy.
- No UI disclosure of accepted-notice version/date in ordinary profile; keep activation/reacceptance text, explicit consent, authoritative version/date storage and route enforcement unchanged.
- Keep current-password verification,8–200-character password validation, mismatch handling, session renewal for current browser and invalidation elsewhere; no client-only simulated success.
- Keep every existing sign-in/invitation/reset/admin flow, plan links, permission-scoped navigation and ES/EN composition; no production actions or real personal data.
- The new version is a breaking scoped UI/interaction replacement, not a compatible additive change. All SP2 UI tasks bind v2, incorporating unchanged v1 sections by reference. Preserve the exact integrated host shell; do not reintroduce page-level account navigation/header removed by SP8 composition. Theme remains existing shell responsibility; SP10 supplies remaining language composition.

## Reglas de copy

- Spanish owner-facing preview with English parity. Explicit Nombre/Name and Correo/Email. Catalogue-backed Plan label/name for real plan identities only. Use real role identity for staff/custom accounts without inventing a subscription.
- Email fallback only for null/empty/whitespace name. No invented full name and no claim that the synthetic unnamed account proves loss of an invitation name.
- No data-notice accepted/version/date summary in the ordinary account view. No marketing copy, invented profile editing or new password-policy claims.
- Dropdown Escape returns focus to trigger; repeated-trigger closure leaves focus there; outside-pointer closure preserves focus on the clicked focusable target; Tab/Shift+Tab can leave without trapping focus and closes when focus leaves.
- Resolved existing-owner decisions for finalization: per round15 the language switch belongs in the account menu, and per round10 the public Plans menu entry is available to signed-in staff/custom accounts too. Preserve current theme composition. A chosen direction may not move language out of the account menu or restrict the plans link.
- Name fallback is already owner-confirmed: keep the explicit Name row and email when the stored name is absent, even when email is also separately shown. Translate canonical system-role labels for EN as Administrator and Internal employee; never translate user-authored custom-role names or infer a plan.
- Hints and too-long copy may restate the existing8–200-character rule; no new password policy. Network errors can reuse existing generic change-password failure copy. Service-acknowledged success does not require a new human acknowledgment button. Non-modal popup overlap, initial-only narrow trigger and account/password grouping are visible choices in the mockup; preserve full name in the open popup and profile, accessible trigger name, outside/Escape/focus behavior and existing security.
- Q1–Q4 finalization dispositions are settled: inherit the exact candidate host shell, optional read-only actual company is allowed through the local projection, equivalent disclosure HTML is technical if every required behavior matches, and owner-selected C truncation is accepted with full name in popup/profile/accessible name. No new owner interview for those settled points.
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T2.11 — Copy the independently owner-approved cuentas-admin@v2 amendment
  - Objetivo: Copy only the exact independently owner-approved cuentas-admin@v2 planning artifact into design/contracts/cuentas-admin@v2.md. The existing T2.1 still owns and preserves v1; never overwrite or regenerate it. Version2 supersedes v1 only for the ordinary account/password surface and shared menu interactions; unchanged views keep their prior requirements. Owner visual approval is mandatory before copy/UI consumption.
- T2.3 — Sign-in, invitation activation, password reset and notice re-acceptance screens
  - Objetivo: A person signs in, activates an invitation accepting the data notice, resets a password from an administrator's link and re-accepts a new notice version, with the states the contract defines.
- T2.4 — Account menu on every signed-in page and the Mi cuenta page
  - Objetivo: Every signed-in person sees who they are and their role, signs out, and changes their own password from Mi cuenta.
- T2.5 — Administration screens: accounts list, invitations, account actions and the role editor
  - Objetivo: An administrator manages every account and custom role from two screens that show exactly what each action will do and why one is refused.
- T2.57 — Redesign Mi cuenta and repair account-menu dismissal under cuentas-admin@v2
- T2.7 — SP-2 visual review against the cuentas-admin@v2 contract
  - Objetivo: A fresh reviewer compares the rendered screens with the approved contract at three widths and records every mismatch with the task to redo.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T2.1, T2.2, T2.55, T2.6, T2.56, T2.58, T2.8.
