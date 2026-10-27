---
contract: cuentas-admin
version: 1
status: draft
subplan: SP-2
requirements: [R1, R3, R16, R17]
owner: David
author: Designer
date: 2026-10-27
direction: Parte de acceso (a)
source_revision: r13.dir-a + amend-1
amendment: 1
baseline: cuentas-admin@v1.md (immutable)
---

# cuentas-admin@v1 — Parte de acceso

## 1. Identity and traceability

**Draft; not approved for implementation.** Scoped amendment 1 of the owner-selected Parte de acceso (a), r13. The canonical `cuentas-admin@v1.md` and `.html` remain immutable; this complete amended snapshot retains contract id/version `cuentas-admin@v1` and requires independent plan approval. T2.1 may copy only the exact subsequently approved snapshot into the repository. No approval is granted by this amendment.

Sources: current SPEC.md and PLAN.json revision 1 (planning continues); amendment behavior brief; immutable canonical contract/mockup; required r13.dir-a TSX starting point. The amendment replaces the three old plans with four catalogue-backed plans and six read-only system roles, keeping composition, navigation, motion, tokens and every untouched decision. Source SHA-256 snapshots:

| Source | SHA-256 |
|---|---|
| `SPEC.md` | `777042bd633762995149f659869d70a43eb3132597c7627d286c9e3ad4094290` |
| `PLAN.json` | `a4261dcfb3ac4c6cef8cb92e5533abbb40cf6b7133873443536ba6360ba4ea49` |
| `design/cuentas-admin@v1.amend-1.behavior.md` | `76936ca02335918683373873e8e28c321f95ccf020761795865ffbbf3b7f5302` |
| `design/cuentas-admin@v1.r13.behavior.md` | `3fb1bbc78c83aae3a915983b47a7bee63aaf08c2e2a2c1bd3f976ecaa797f7f4` |
| `design/cuentas-admin@v1.md` | `52e5e8eaf0f2d7cc0da19841cbddabc2f20e50007df957c6296d95fb7bf569ba` |
| `design/cuentas-admin@v1.html` | `41de6620ad2ca6f4cdf18177cde91e72868bb70036768259912950a28045204b` |
| `design/cuentas-admin@v1.r13.dir-a.tsx` | `7ad4f5526859611950de1595e7d71ee1fcf37c86a7d899e0cf0082eb030fd238` |

Only **SP-2** binds `ui.contract=cuentas-admin`, version 1, design-copy **T2.1** and visual review **T2.7**. UI consumers: **T2.3** login/activation/reset/mandatory notice; **T2.4** shared account menu and Mi cuenta; **T2.5** accounts/invitations/roles. **T2.2** supplies APIs; **T2.6** integrates real browser flows; **T2.8** audits. SP-1 supplies account-service@1, session-guard@1, permission-map@1 and plan-catalogue@1. Its catalogue is the sole owner of plan names, ordering, prices, tool availability and permission membership; SP-2 reads it without independent plan logic. SP-14 owns the public plans section and its sign-in/account-menu entry links; adding those is outside this amendment brief. Other subplans do not become consumers merely by dependency.

| Requirement | Views / flows | Acceptance |
|---|---|---|
| R1 invited accounts | V1–V4, V6–V7 / F1–F5, F7–F8 | UI-AC-06–14, 19–24, 29–30 |
| R3 roles and permissions | V4–V5 / F5–F6 | UI-AC-15–19, 25, 31, 35 |
| R16 cumulative assigned plans | V4–V5 / F2–F3, F5–F6 | UI-AC-15–16, 25, 41–42 |
| R17 shared plan catalogue | V4–V6 / F3, F5–F6 | UI-AC-15, 25, 41–43 |

Embedded version/impact record (separate changelog is outside the assigned scope): **2026-10-27, amendment 1, draft. Compatibility: breaking content/permission expectations relative to the canonical draft; visually compatible composition.** V4 invitation/account role selectors and filter, V5 system-role list/permission selection and V6/shared account identity must consume six system roles, not five. T2.5 adapts plan assignments and read-only grants; T2.4 adapts catalogue-backed role display; T2.3 displays the new invited identity/destination where applicable. T2.1 must copy the independently approved snapshot; T2.7 must review the amended labels, order and permissions in both themes/languages and responsive ranges. SP-1's plan-catalogue@1 and permission-map@1 produce the data; no other UI subplan becomes a consumer by dependency alone. The current SPEC/PLAN resolves the explorer as Master Designer-only and the English name as Enthusiast. No new plan page, payment flow, new limit UI or price comparison is added here.

The required TSX begins as a copy of immutable r13.dir-a. Its two canonical-only corrections are preserved in source before rebuilding: own-password change renews this browser's session, and Taller has one grant with supporting capabilities (12 available permissions). The CSS remains byte-identical to the selected TSX; shell, navigation, hierarchy and motion keep their chosen composition. The amendment is rebuilt with the current offline builder; generated HTML is not hand-patched.

## 2. Purpose and users

The administrator answers “Who has access, what is their role, and what needs changing?” The complete ruled register keeps each person's identity, role, status and management action together. Invited people set a personal password, accept the notice and reach a permitted tool. Signed-in people identify themselves, change their own password and sign out.

Account administration requires `cuentas.administrar`; role administration independently requires `roles.administrar`. Role names or `internas.usar` never substitute for these permissions. Success means a server-confirmed change and an explicit next step. Denied users see a scoped refusal without restricted data.

The HTML labels mock data and simulated operations. Neutral `@prueba.local` account fixtures correspond to the SPEC test vocabulary, not real identities. Mi cuenta and the account menu both identify Cuenta administradora / admin@prueba.local; activation identifies Cuenta Master Designer / master@prueba.local. Reserved pictures.example links never issue live access. Counts derive from the same fixture rows; sample last-access values and notice dates are illustrative.

## 3. Information architecture and hierarchy

Preserve r13: compact Pictures/Sempertex ring-and-dot masthead with language/account controls → 24px task heading → neutral horizontal Cuentas / Roles y permisos / Mi cuenta navigation on permitted signed-in surfaces → a single working paper → aligned footer. There is no edition counter, plan rail, slogan, material sample or secondary promotional card.

Accounts fill the available register width: Cuentas del piloto / Datos de ejemplo and Invitar persona → search/role/state filters → ruled records → derived result count and Bogotá-time caption. Desktop filters share flexible 2:1:1 columns. Each row keeps name/email/company, assigned role, state, last access and Gestionar together.

Roles retain the role-list/editor composition: heading/Create role → six read-only system roles and custom examples → selected-role title and explanation → custom role name when editable → four tool fieldsets → save/delete and feedback. The desktop list is 240px wide; the editor fills remaining space. Taller sub-capabilities are explanatory text under the single Taller grant.

Login, activation, reset, Mi cuenta and mandatory notice use a centred workspace capped at 676px, with a 620px form axis, matching heading/feedback and stacked footer. Activation places invited identity before passwords, full notice before unchecked consent, and consent before submission. Mandatory notice withholds other product routes until acceptance. Contextual dialogs keep invitation, selected-account management, one-time receipt and permanent confirmation beside their originating workflow.

## 4. Design system and visual language

Production sources inspected read-only: t12 and asesor `src/app/globals.css`, layout/font setup, login form, AdminTabs and CabeceraApp; sibling proyectos@v1 and taller-esenciales@v1 contracts. The product's tokens/fonts and written sibling mappings govern. Some sibling bundled HTMLs retain older exploratory styling; that mismatch is not imported. The owner's selected r13 horizontal navigation, generous rounded forms and kinetic registration are preserved. No new palette or font family is introduced.

Project role mapping comes from both repositories' globals.css and the matching shared roles in proyectos@v1. Every value below already exists in the product; no new colour is introduced.

| Pictures source | Kit role | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--texto` | foregrounds | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted foreground | #6b6178 / #9aa1ad |
| `--superficie-2` | secondary, muted, accent | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primary, primary foreground | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover`, `--acento` | primary hover, ring | #5530b8, #6d3fe0 / #a58dff, #9479ff |
| `--borde`, `--borde-suave` | decorative border, rule | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | input (existing sibling accessible control alias) | #766c85 / #8a91a0 |
| `--superficie-suave` | soft selected-role surface | #faf8fd / #1c1e26 |
| `--exito`, `--exito-suave` | success, success-soft | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | warning, warning-soft | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | destructive, destructive-soft | #b23a45, #ffeaec / #ff979f, #43252a |
| Existing destructive foreground | destructive-foreground | #ffffff / #3a0f13 |
| `--fondo` | info-soft, primary-soft | #faf9fc / #0b0c10 |

Typography is the actual production Geist Sans / Geist Mono, embedded offline from the existing t12 Next build's local Latin WOFF2 assets. No font or asset is fetched. H1 is 24px/1.25 at every width, section title 20px/1.3 desktop, body 14–16px and metadata 11–13px; mono is limited to identifiers/metadata. Phone section sizing and the generous shapes are retained from r11. R11 shape roles stay `--radius-panel:32px`, `--radius-inset:24px`, `--radius-field:18px`, `--radius-check:8px`, `--radius-pill:999px`. These are the owner's retained draft shape choices, not new production palette or font choices. Paper and dialog padding remain 28px desktop, 20px phone paper / 24px phone dialogs; rows remain 24px desktop / 20px phone.

Components are named **source:id variant state**; all paths refer to actual installed components, not HTML snippets:

| Name | Import / composition |
|---|---|
| `shadcn:button default default\|hover\|focus\|pressed\|disabled\|loading` | `@/components/ui/button`, selected Action composition; primary submit/invite/copy |
| `shadcn:button outline default\|hover\|focus\|pressed\|disabled` | Same import; management, recovery, cancel/navigation |
| `shadcn:button destructive default\|hover\|focus\|disabled\|loading` | Same import; explicit permanent-delete confirmation |
| `shadcn:input text\|email\|password default\|focus\|invalid\|disabled` | `@/components/ui/input`; custom Field is associated label, control and hint, not stock shadcn Field |
| `shadcn:checkbox permission\|consent unchecked\|checked\|focus\|disabled` | `@/components/ui/checkbox`, installed Animate UI/Base UI enhancement |
| `shadcn:skeleton record\|form loading` | `@/components/ui/skeleton` |
| `shadcn:dialog invitation\|management\|link open\|closed` | `@/components/ui/dialog`, installed Animate UI/Base UI enhancement |
| `shadcn:alert-dialog account-delete\|role-delete open\|blocked\|pending\|closed` | `@/components/ui/alert-dialog`, installed Animate UI/Base UI enhancement |
| `native:select role\|status\|language default\|focus\|disabled` | Native HTML select with label; no shadcn Select claim |
| `native:details account closed\|open` | Named account disclosure with Mi cuenta/sign-out; non-modal |
| `custom:access-register ruled normal\|loading\|empty\|error` | `.register-head`, `.person-row`, `.identity`, `.footline` |
| `custom:permission-sheet grouped system-readonly\|custom-editable\|validation` | `.role-layout`, `.role-list`, `.role-editor`, fieldset/legend |
| `custom:app-header compact normal` | `.masthead`, `.heading`, `.route-nav`; Pictures ring-and-dot mark |
| `custom:message ruled error\|success` | `.message` with alert/status semantics |

`mountMockup` / `useMockup` import from `@kit/mockup`; `useMotionProfile` from `@kit/motion`. The real offline workspace bundles React, controls, fonts and motion. No CDN, package installation, external image/font request or plain-HTML fallback was used.


**Motion: kinetic registration, unchanged from r13.** `useMotionProfile()` supplies profile/reduced state. Cubic-bezier(.76,0,.24,1); expressive paper/row/rule/status 480ms with 55ms row offsets, controls 180ms; natural 300/140ms; subtle 160/100ms. Paper travels vertically 12px, rows horizontally 14px, rules/status 6px. Buttons lift −2px on hover, press 1px with scale(.98), arrows move 3px. Skeleton scan repeats at 1.4s. No retired rail/foil motion is reintroduced. Readable text stays present. Hidden tabs pause animation; no offscreen decorative animation remains. OS reduced motion, Quieto and `?still=1` suppress movement/repeating effects, preserve final layout and retain all actions.

## 5. Navigation and interaction model

| View | Product path / permission | Preview value |
|---|---|---|
| V1 sign in | `/login?from=<relative-path>`; public | `view=login` |
| V2 activate | `/activar/<token>`; public valid invitation | `view=activar` |
| V3 reset | `/restablecer/<token>`; public valid reset | `view=restablecer` |
| V4 accounts | `/admin/cuentas`; `cuentas.administrar` | `view=cuentas` |
| V5 roles/editor | `/admin/roles`; `roles.administrar` | `view=roles` |
| V6 own account | `/cuenta`; active session | `view=cuenta` |
| V7 mandatory notice | `/aviso-datos?from=<relative-path>`; active session | `view=aviso` |

Invitation/management/link are contextual dialogs of V4, and role editing is inline in V5. Do not retain the previous draft's invented query-subview routes as requirements. SP-1 owns `/sin-acceso`; the `sin-permiso` fixture shows its scoped visual refusal and Mi cuenta recovery. It does not authorize a new route or disclose a denied resource.

On successful login, use a permitted safe same-origin relative `from`, otherwise first allowed Taller 3D, chat, catalogue, then `/cuenta` when none is allowed (T2.3). Activation creates a session and uses the same allowed-tool fallback without requiring login again. After notice acceptance revalidate the saved destination and current permissions. No target tool outside SP-2 is mocked as a working authenticated page. Next request enforces deactivation, permission and role changes server-side.

Signed-in pages show the account name/role and Mi cuenta/sign out; compact summary keeps the name and disclosure reveals the role. Show Cuentas and Roles links only for their independent permissions. The static direction supplies the administrator fixture; it is not a permission service. On V7 preserve identity and sign out while withholding other product destinations until acceptance. Preview controls are external inspection chrome, never a product bypass.

Navigation focuses the new page heading; invalid submission announces the error and focuses the first invalid field. Search/filters preserve typing focus. Dialog opens focus inside, contains Tab, makes the background inert and restores focus to the initiating action after dismissal. Invitation/management/link support Escape; destructive dialogs require explicit Cancel/confirm and start on Cancel. If data mutation is pending, disable repeated submission; avoid dismissing an already committed request as if cancelled. The native account disclosure uses disclosure semantics, not a partial ARIA-menu pattern; keyboard actions retain visible focus.

The mockup bar retains native `view`, `state`, `scene`, `theme`, `motion`, labeled Vista, Estado, Diálogo, Tema, Movimiento. Every declared preview state/scene is reachable. The product language selector is ES/EN, initially ES in this selected inspection artifact, with EN explicitly selectable. In the product, the invitation notice initially follows browser language; later persisted language preference follows SP-8/SP-10. Preview selection does not persist account settings or change server permissions. Translation rollout follows PLAN: SP-2 Spanish strings remain grouped for SP-8/SP-10; the notice is bilingual from the start. This bilingual visual reference does not claim those later tasks are implemented.

## 6. Flows

**F1 — Sign in.** Enter invited email/password → submit once → loading → server-confirmed safe destination. Wrong password, unknown email, deactivated account and locked email use the same refusal: “Revisa el correo y la contraseña. Después de varios intentos fallidos debes esperar quince minutos.” English: “Check your email and password. After several failed attempts you must wait fifteen minutes.” Do not expose existence/state/attempt counters. SP-1 locks an email after five failures in fifteen minutes for fifteen minutes; the UI always supplies the neutral hint. Invitation-only copy and administrator-issued recovery are visible; no open registration or automatic email reset. Sessions last 30 days under SP-1 and end on sign-out/deactivation/password change as specified below.

**F2 — Activate.** Validate the invitation without consuming it on load → display invited name/email → new password and confirmation → full current notice in browser/selected language → unchecked consent → Activate disabled until checked → explicit valid submission. Password is 8–200 characters, confirmation equal; allow password-manager/paste. Only confirmed activation stores notice version/date, consumes the one-use seven-day token, creates a session and opens the first allowed tool or Mi cuenta. Expired, used or replaced links use one generic `LINK_INVALIDO` recovery, hide password entry and ask the administrator for a new link; do not disclose which condition or recipient data from an invalid link. The fixture's Taller 3D destination is an example for its Master Designer role, not a destination forced on all roles.

**F3 — Invite.** Cuentas → Invitar persona → required name/email, optional company, exactly one role/plan in catalogue order (Entusiasta, Designer, Designer Plus, Master Designer), then Empleado interno, Administrador and custom roles → Generar invitación → pending → server-confirmed one-time link receipt. Registered email returns `CORREO_REGISTRADO` and “Este correo ya está registrado. Gestiona su cuenta existente.” without creating another invitation. Receipt names recipient, one-use/lifetime and manual sharing; nothing claims email delivery. Copy reports success only after clipboard success; failure instructs selecting/copying the wrapping link manually. Closing/leaving removes the receipt. Generate a new invitation from an invited account's management dialog to recover a lost/expired receipt; explain before generation and on receipt that all older unused invitations for that account become invalid. Reset and invitation kinds do not cross-revoke.

**F4 — Administrator reset.** Manage an existing account → Generar restablecimiento → explain older unused resets become invalid, new link is single-use for 24 hours → generate/copy/close once. Recipient opens V3 → new password twice, 8–200 and matching → confirmed reset revokes sessions → sign in with the new password. No repeated notice consent is added to reset; invalid link recovery matches F2. Generating a reset does not itself assert that a password was changed.

**F5 — Account administration.** Search name/email and filter role/state → Manage selected row → read identity and choose one role from that same ordered catalogue/staff/custom list → Guardar rol; effects apply next request. Deactivate ends sessions and preserves saved work; Reactivate restores access subject to the same role and notice. Last active Administrator cannot be deactivated/deleted/demoted (`ULTIMO_ADMIN`); fixture Cuenta administradora is the last administrator, not a rule that all administrators are immutable. Saved projects/decorations or any registered saved-work row block deletion (`CUENTA_CON_TRABAJO`) and change nothing; explain deactivation as the alternative. Spend alone is not saved work. Only a work-free account can proceed to permanent-delete AlertDialog; require exact matching email, explain irreversibility and retention of anonymous spend as “Cuenta eliminada”. Unknown/stale eligibility never enables deletion; recheck on confirm. Handle a concurrent refusal in place with refreshed authoritative data and no success claim. Profile editing, bulk operations and account transfer are outside scope.

**F6 — Roles and plans.** Select one of six system roles to inspect its read-only permissions → or Crear rol → name and initially unselected independent checkboxes grouped by tool → require at least one permission (`ROL_SIN_PERMISOS`) → Save confirmed custom role. Editing loads that role's actual selected permissions; it never inherits another role's transient checkbox state. System roles cannot be edited/deleted (`ROL_SISTEMA`). Assigned custom roles refuse deletion (`ROL_EN_USO`) and explain assigning another role first; unassigned custom roles use permanent-delete confirmation. The displayed assigned count must come from real account assignments, not list position. No separate additive plan field exists: the four access plans are Usuario roles, one role per account; staff/custom roles follow them. Custom roles remain independent of plans. Read names, ordering and plan permissions directly from plan-catalogue@1 rather than copying tier logic into SP-2.

**F7 — Own password.** Account disclosure → Mi cuenta → read own identity/company/role and notice version/date → enter current password, new password and confirmation → validate → confirm service success. Wrong current password is actionable without ending the valid session. The service ends all old sessions and T2.2 opens a new one for the requesting browser; clear secret fields and announce “Contraseña cambiada. Esta sesión se renovó; tus otras sesiones terminaron.” The person remains signed in here; other browsers must sign in again. This is distinct from F4 reset. No self-editing of email/profile/role is introduced.

**F8 — Notice update.** On next request after a notice version change, replace requested content with V7 → show full displayed version and unchecked consent → accept and store exactly that version/date → permitted destination, or sign out to V1. No skip/later or underlying product links before consent. If displayed version changes while open, discard acceptance of the old text and ask for fresh consent. Failure/offline retains input for that version with explicit retry and no recorded-success fiction. The v1 body in the preview is an illustrative reacceptance scenario, not a newly invented v2 legal text.

## 7. View specifications

| View | Structure / copy and data | Actions and related flow |
|---|---|---|
| V1 | “Iniciar sesión” / “Sign in”; Iniciar sesión, email/password, invitation-only explanation, administrator reset guidance | Entrar; generic error/retry; F1 |
| V2 | “Activar cuenta” / “Activate account”; invited name/email, new/repeated password, full notice, unchecked consent, seven-day explanation | Activar cuenta disabled until consent; invalid-link replacement/Volver al acceso; F2 |
| V3 | “Restablecer contraseña” / “Reset password”; reset password twice; one-use 24-hour explanation | Guardar contraseña then sign in; invalid-link replacement; F4 |
| V4 | “Cuentas” / “Accounts”; Cuentas del piloto / Datos de ejemplo, filters and five illustrative complete account records, result count/timezone | Invitar persona, Gestionar, clear filters, retry; F3/F5 |
| V5 | “Roles y permisos” / “Roles and permissions”; six system roles/custom list, selected name, permission groups and explanatory Taller bundle | Crear rol, Guardar rol, Eliminar rol if custom; read-only system state; F6 |
| V6 | “Mi cuenta” / “My account”; current signed-in identity/company/role, current/new/repeated password, version/date | Cambiar contraseña; signed-in session-renewal feedback; shared account disclosure; F7 |
| V7 | “Aviso de tratamiento de datos personales” / “Personal data notice”; Aviso actualizado, gate explanation, full versioned text, unchecked consent | Aceptar y continuar, Cerrar sesión; no other product routes; F8 |

Contextual scenes (`scene`): `invitar` = name/email/company/one-role form; `gestionar` = selected identity, role, regenerate/reset, deactivate/reactivate and delete with inline reasons; `enlace` = recipient, selectable link, lifetime/one-use/replacement warning, Copy and Done; `eliminar` = account refusal or exact-email confirmation; `eliminar-rol` = role refusal or permanent-delete confirmation. Empty `scene` is Ninguno. No other exploratory view is required.

Permission catalogue is **12 permissions**, supplied once by SP-1. The six Taller capabilities are supporting text for one coarse `taller.usar`; they must never become independent checkboxes or fabricated permission keys. Preserve four grouped fieldsets and the chosen editor geometry.

| Tool group | Key → ES / EN label |
|---|---|
| Planificación | `chat.usar` → Chat asistido / Assisted chat; `contador.usar` → Contador de globos / Balloon counter; `catalogo.ver` → Catálogo / Catalogue; `costos.usar` → Calculadora de costos / Cost calculator; `decoraciones.explorar` → Explorador de decoraciones / Decoration explorer |
| Taller 3D | `taller.usar` → Taller 3D / 3D workshop. Includes scene AI, assembly plans/build sheet, export, own projects and decorations; no independently selectable sub-capabilities. |
| Herramientas internas | `proyectos.ver_todos` → Proyectos de todos / Everyone’s projects; `gasto.ver` → Consumo de IA / AI spend; `internas.usar` → Herramientas internas / Internal tools |
| Administración | `cuentas.administrar` → Gestionar usuarios / Manage users; `roles.administrar` → Gestionar roles / Manage roles; `textos.corregir` → Corregir textos en inglés / Correct English copy |

System roles, in exact picker/list order:

| System role ES / EN | Selected grants (read-only) | Count |
|---|---|---|
| Usuario · Entusiasta / User · Enthusiast | chat, counter, catalogue | 3 |
| Usuario · Designer / User · Designer | Same as Entusiasta; no additional grant or numeric chat limit | 3 |
| Usuario · Designer Plus / User · Designer Plus | Entusiasta grants + costs | 4 |
| Usuario · Master Designer / User · Master Designer | Designer Plus grants + Taller + ready-made decorations explorer | 6 |
| Empleado interno / Internal employee | All Master Designer grants + everyone's projects, spend and internal tools | 9 |
| Administrador / Administrator | All permissions, including account/role/text administration | 12 |

There is no seventh generic Usuario. Custom roles follow the six system roles and retain independent checkboxes without silent inheritance. `proyectos.ver_todos` permits reading foreign originals; with `taller.usar` an owned copy can be saved, never editing the original (SPEC round 9). Routes/services use keys, never translated labels. Availability is distinct from assignment: do not invent extra selectable grants for extended chat, structure detection or advanced balloon detection. T1.2 currently marks those three unavailable and keeps the cost grant with Designer Plus; no tool is made available by changing its role label.

**Shared catalogue data (R17, reference data, not a new SP-2 price screen):**

| Order | Name ES / EN | Monthly COP | Monthly USD |
|---|---|---|---|
| 1 | Entusiasta / Enthusiast | Free | Free |
| 2 | Designer / Designer | 20,000 | 7 |
| 3 | Designer Plus / Designer Plus | 45,000 | 14 |
| 4 | Master Designer / Master Designer | 70,000 | 25 |

The mock TSX contains one clearly marked plan-catalogue fixture (names, both currency prices, cumulative tools with availability and selected grants). Role options and plan checkmarks read that fixture; they do not maintain competing tier arrays. Production reads SP-1's real catalogue; this design fixture is not a new production owner. Neither invitation nor account management adds prices, purchase actions or a separate plan selector. Entusiasta/Designer have identical grants now; the owner deferred numeric chat limits, so no values or limit control are invented. The complete comparison, unavailable-feature copy and entry links are SP-14's scope.

Full notice is reproduced verbatim from SPEC. Bracketed text stays visibly pending legal review, not a fabricated policy hyperlink. It is mock content until David/Sempertex supply the legal fields before real invitations.

**ES — Aviso de tratamiento de datos personales (versión 1)**

[RAZÓN SOCIAL DE SEMPERTEX] tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a [CORREO PARA DERECHOS]. La política de tratamiento de datos está en [URL DE LA POLÍTICA]. Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012.

**EN — Personal data notice (version 1)**

[SEMPERTEX LEGAL NAME] will process your personal data —name, email, company (if you provide it), the role and plan assigned to you, and the dates of invitation, activation and last access— to give you access to Pictures during the pilot, manage your account and measure the use of the tools, including artificial-intelligence usage. The projects and decorations you save are linked to your account. You can access, update, correct or request deletion of your data, and withdraw this authorization, by writing to [RIGHTS CONTACT EMAIL]. The data-processing policy is at [POLICY URL]. By activating your account you confirm that you have read this notice and authorize the processing described, under Colombian Law 1581 of 2012.

## 8. States

The global preview intentionally permits unrelated view/state combinations. The applicable product behavior is defined below; do not implement a nonsensical cross-product solely because the inspector can select it.

| Preview id / label | Applicable result, action and recovery |
|---|---|
| `normal` / Normal | Editable form/register; valid read-only system roles; no request pending. |
| `cargando` / Cargando | Account/role/form skeletons and processing action; no duplicate submission or editable pending mutation. Never imply zero records from loading. |
| `vacio` / Vacío | Accounts no-match/initial-empty explanation. Filtered empty offers clear filters; true initial-empty points to Invite. Six system roles cannot be an empty catalogue. |
| `error` / Error | Account/role reads hide unconfirmed rows and offer Reintentar. Forms preserve safe input, describe failure and permit retry. Login uses the same fifteen-minute generic refusal for every service cause. |
| `exito` / Éxito | View-specific confirmed result: signed-in destination; activated/session; reset/sign-in; own-password/new session; notice version/date; saved role/account. No success before authoritative acknowledgement. |
| `validacion` / Validación | Announced error and invalid control, required identity/current password, 8–200/matching new password, name/role selection and at least one custom permission. Retain input, focus correction. |
| `sin-permiso` / Sin permiso | Scoped refusal with no restricted form/rows; request permission, open Mi cuenta or sign out. Service still enforces 403. |
| `enlace-vencido` / Enlace vencido o usado | V2/V3 form replaced with one invalid-link recovery; no password submission or cause/identity disclosure. |
| `duplicado` / Correo duplicado | Invitation refused; email marked, manage existing account; no new link/account. |
| `con-trabajo` / Cuenta con trabajo | Delete refused unchanged with `CUENTA_CON_TRABAJO`; explain deactivation; confirm disabled. |
| `ultimo-admin` / Último administrador | Cannot delete/deactivate/demote the last active administrator; explain guard and disable/refuse mutation. |
| `rol-en-uso` / Rol en uso | Assigned custom-role delete refused; reassign accounts first; system-role read-only remains separate. |

Control states include default, hover, focus, pressed, disabled, loading, invalid and checked/unchecked consent/permissions. One-time receipt has copy success and manual-copy fallback. The account disclosure has open/closed states. Exact-email delete is disabled until an exact match; “pending” also disables confirmation.

Offline, incomplete or stale reads share the recoverable error presentation: no unconfirmed save, misleading authoritative count or unrestricted mutation from stale eligibility. Keep local safe input, explain retry, refetch authoritative role/eligibility/notice as appropriate; a changed notice resets consent. Distinct new offline/conflict routes are unnecessary. An empty system-role dataset and self-service public registration are inapplicable, because the system roles are seeded and access is invited. Paid AI, spend charts, saving projects, legal completion, database race resolution and real token/session mechanics are not simulated proof of this artifact.

## 9. Responsive behavior

Supported contractual floor: **360px**. Vertical scrolling is expected for long notice/editor/dialog content. No horizontal page scrolling or clipped essential controls in either theme/language. The actual selected CSS uses 760px and 1100px transitions.

| Range | Layout |
|---|---|
| **1101px+** | `.app` max width 1520px, 40px side padding; paper inset 28px. One full-width accounts/register workspace; filters 2:1:1; four aligned record columns, 24px row padding. Role list 240px beside editor, two-column permissions. Form workspace/heading/footer capped at 676px and centred; form content max 620px. |
| **761–1100px** | Outer padding 28px; paper 28px; search spans both filter columns. Account action follows record fields; role list 200px beside editor; permissions one column. Form panel remains centred, cap 676px. |
| **360–760px** | Outer/paper padding 20px; header tools wrap, name stays visible, disclosure reveals role. H1 stays 24px. Filters and field/identity groups stack; account identity spans row, role/state reflow below, Manage follows. Rows have 20px vertical padding. Role selector stacks before editor, top divider replaces left divider. Actions stack full width. Form panel contracts to available space. Feedback spans the paper width while its text aligns with the field inset. |

Dialogs retain max width `min(560px, 100vw − 32px)`, 28px desktop / 24px phone padding, max height `100svh − 48px` and vertical scroll. Paper/dialog radii are 32px; notice/feedback 24px; fields/selected role 18px; checkboxes 8px; buttons/selects/status chips/account disclosure 999px. Phone notice has 16px padding. Main management footer uses the workspace axis; form footer stacks on its 676px axis. Inspect 390/768/1280px and the 360px floor; English strings must reflow without a new layout.

## 10. Accessibility targets

Target WCAG 2.2 AA for applicable content and interactions; this description and automated audit are not a conformance certificate. Text target ≥4.5:1, large text ≥3:1 under the applicable exception, meaningful control edges/focus ≥3:1. Keep the 3px focus ring with 4px offset. Primary working actions are at least 44px tall; checkbox labels expand the small visual square into a larger hit area. Test zoom/reflow at 200% and 320 CSS px equivalent; the contractual visual floor is 360px and browser zoom verification remains explicit evidence work.

Use headings in hierarchy, main/navigation landmarks, associated label/input/hint/error, type=email/password autocomplete, accessible named groups via fieldset/legend, and real native buttons/selects. Use status for successful results and alerts for errors; do not rely on icon/color. Permission IDs are normalized without spaces so Base UI's accessible labels resolve. In production associate summaries/field errors with their controls and expose request busy state. Password paste/autofill remains allowed; no forced timed interaction.

Maintain search/form typing focus, route focus, modal containment/inert background and dismissal return. Destructive confirmations start with safe Cancel and require exact-email account confirmation. Do not imply inaccessible read-only system controls can be changed. Consent is explicit and initially unchecked for each activation/new notice version. Reduced/still suppresses all animation while preserving final content, focus, dialog alignment and immediate feedback; no flashing, hidden text or mid-animation illegible state.

The offline inspector and automated checks measure rendered mechanics. Manual screen-reader sessions, all zoom levels, full disclosure keyboard behavior, cross-browser testing, real server errors and production routing require later implementation verification. Preserve those as targets instead of claiming that the illustrative local handlers implement them.

## 11. Visual acceptance criteria and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | 1101px+ | accounts normal | The 24px task title sits above one full-width ruled accounts paper; no edition cell, rail or material card is present. |
| UI-AC-02 | 1101px+ | accounts normal | Every record visibly groups name, email, company, role, status, last access and Manage. |
| UI-AC-03 | 360–760px | accounts normal | Identity spans its record; role/status and Manage reflow below without page overflow. |
| UI-AC-04 | 761–1100px | accounts normal | Search spans both filter columns and Manage follows the row's other fields. |
| UI-AC-05 | 360px+ | accounts filtered/empty | Result count matches displayed records; clear filters restores the unfiltered register. |
| UI-AC-06 | 360px+ | loading | Skeletons replace unresolved content and pending submission cannot repeat. |
| UI-AC-07 | 360px+ | accounts/roles error | Unconfirmed rows are absent and Reintentar is visible. |
| UI-AC-08 | 360px+ | login error | The same refusal and fifteen-minute wait hint appear for all four credential-refusal causes. |
| UI-AC-09 | 360px+ | activation normal | Two password controls and the full notice precede unchecked consent and disabled Activate. |
| UI-AC-10 | 360px+ | activation checked | Checking consent enables valid activation and success explains an active signed-in session. |
| UI-AC-11 | 360px+ | invalid invitation/reset | Password entry is replaced by administrator-issued-link recovery without a cause-specific disclosure. |
| UI-AC-12 | 360px+ | invitation | Name/email/optional company/one role precede generation; duplicate email produces a refusal. |
| UI-AC-13 | 360px+ | one-time receipt | Recipient, selectable wrapping link, Copy, one-use/lifetime and replacement warning are visible. |
| UI-AC-14 | 360px+ | receipt dismissed | The closed receipt cannot retrieve its previous link; regeneration is the recovery. |
| UI-AC-15 | 360px+ | role system | Exactly six system roles are read-only and have 3/3/4/6/9/12 selected permissions in catalogue/staff order. |
| UI-AC-16 | 360px+ | role custom | Four tool groups contain twelve available permissions; Taller is one checkbox with bundled-capability helper text. |
| UI-AC-17 | 360px+ | role validation | Saving a named custom role with no permission announces ROL_SIN_PERMISOS and preserves editing. |
| UI-AC-18 | 360px+ | role in use | Permanent deletion is disabled and the reassign-first explanation is visible. |
| UI-AC-19 | 360px+ | saved-work/last-admin | The refusal explains its invariant and permanent-delete confirmation is disabled. |
| UI-AC-20 | 360px+ | work-free account delete | Permanent deletion is disabled until the typed email exactly matches the selected account. |
| UI-AC-21 | 360px+ | own account | Identity matches the account disclosure and current password precedes the new password pair. |
| UI-AC-22 | 360px+ | own-password success | Feedback states this browser's session was renewed and previous sessions ended; no second-login requirement appears. |
| UI-AC-23 | 360px+ | reset success | Feedback asks the person to sign in with the new password. |
| UI-AC-24 | 360px+ | notice gate | Full versioned notice, unchecked consent and sign out are present while other product navigation is absent. |
| UI-AC-25 | 360px+ | account role changed | The selected single role updates with copy explaining next-request enforcement; plan labels remain cumulative. |
| UI-AC-26 | 360px+ | light/dark | Field edges, checkbox states, outline actions and focus are visible against their actual surfaces. |
| UI-AC-27 | 360px+ | expressive | Paper registers vertically, records horizontally and rule/status feedback by short strokes, with the r13 easing/timing and readable text. |
| UI-AC-28 | 360px+ | reduced/still | No running motion or displaced dialog remains; the same controls and content are usable. |
| UI-AC-29 | 360px+ | invitation open/dismissed | Tab stays inside the dialog; dismissal restores the initiating action's focus. |
| UI-AC-30 | 360px+ | ES/EN | Headings, labels, notices and dialog actions reflow without horizontal page scrolling. |
| UI-AC-31 | 360–760px | roles normal | The role selector stacks before the permission editor with its horizontal divider. |
| UI-AC-32 | 761px+ | login/activation/reset/Mi cuenta/notice | The form workspace is at most 676px, centred with equal outer gutters; fields stay within a 620px axis. |
| UI-AC-33 | 761px+ | form error/success/invalid link | Heading, feedback, recovery and stacked footer follow the centred form axis. |
| UI-AC-34 | 1101px+ | accounts normal | Search/role/state filters occupy flexible 2:1:1 columns across the register width. |
| UI-AC-35 | 1101px+ | roles normal | The role selector is 240px; the remaining editor width contains two permission columns. |
| UI-AC-36 | 360px+ | both themes | Paper/dialog radii are 32px, notice/feedback 24px, fields 18px and checkbox 8px, with pill actions. |
| UI-AC-37 | 1101px+ | accounts normal | Paper padding is 28px and record vertical padding is 24px. |
| UI-AC-38 | 360px+ | both themes | Body uses embedded Geist; semantic colours match the production mapping and input edges use texto-tenue. |
| UI-AC-39 | 360px+ | ES/EN, dialog | Initial inspection language is ES; EN translates labels; the ES dialog close accessible name is Cerrar. |
| UI-AC-40 | 360–760px | form views | Panel contracts with 20px paper padding and all essential actions remain reachable without horizontal scrolling. |
| UI-AC-41 | 360px+ | invitation/account role picker, ES/EN | The four catalogue plan names appear in plan order, then Empleado interno, Administrador and custom roles; EN uses Enthusiast. |
| UI-AC-42 | 360px+ | system role selected | Entusiasta and Designer show the same grants; costs first checks at Designer Plus, Taller and explorer first check at Master Designer; staff roles include all plan grants. |
| UI-AC-43 | 360px+ | accounts/roles, ES/EN | No Plan 1/2/3 label, invented numeric chat limit, payment action or additional additive plan field is displayed. |


Verification applies only to **cuentas-admin@v1.amend-1.html**, rebuilt from **cuentas-admin@v1.amend-1.tsx** with the current offline toolchain. Build: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/cuentas-admin@v1.amend-1.tsx --out <design>/cuentas-admin@v1.amend-1.html` → **679 KB, 2150 source files, exit 0**, offline. No packages installed, no assets fetched, no fallback, no generated-HTML patching. Canonical input hashes are retained in section 1.

Final source SHA-256: `3e0b23dc622f24233bff202f996687d258b77ae2e1924d4caff6dc64dfcae017`. Final HTML SHA-256: `e78373c1b2143abb364cb1d046ef027f191cbe1f4621500568a0169903232953`.

`python3 <kit>/kit/contrast.py <design>/cuentas-admin@v1.amend-1.html` → **contrast: 158 pairs checked in light and dark, all pass**, exit 0.

`UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/cuentas-admin@v1.amend-1.html --max-combos 476`, system `/usr/bin/chromium` → **476 renders (476 combinations planned), 12,454 text measurements, 1,463 focus stops**, exit 0. Both themes, all view/state combinations and dialog scenes at 1280/390px were measured without sampling omissions.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Supplementary offline Playwright on the final snapshot: **446 assertions passed**. Each system role has exactly **3/3/4/6/9/12** checked grants out of twelve, in both themes and languages; costs first belongs to Designer Plus, explorer first to Master Designer. Invitation, account management and filter share catalogue order, custom editing remains available after the system-role index shift, last-administrator protection and canonical own-session renewal remain intact. Initial account management selects the same Designer Plus role its recipient actually holds; invitation retains that corresponding default. **140 responsive cases** (seven views × two themes × two languages × 360/390/768/1024/1280px) passed page-overflow and Geist checks. No page exceptions or HTTP(S) requests were observed.

Motion probes on the final snapshot, both themes: expressive entrance **8 running animations**; `?still=1` **0**; Quieto (`?motion=still`) **0**; OS reduced motion **0**. Once the runtime is initialized, the invitation dialog is visibly opaque and has **0 running animations** in OS-reduced and Quieto modes. No new animation or styling was introduced.

Screenshots inspected in memory on the final snapshot: **1280/light accounts, 1280/dark roles, 390/light invitation, 390/dark roles**. The rounded paper, selected shell/navigation, six system roles and mobile invitation selector retain the chosen composition. No screenshot files were written. Static checks passed: twelve sections, draft status, 43 unique acceptance ids, all input hashes unchanged, byte-identical CSS versus r13 and verbatim ES/EN notice.

Probe history/limit: an immediate programmatic dialog open before the runtime's initial reduced-motion settling frames produced a transparent popup (animation time 0). A readiness probe that waits 300ms before opening, matching the audit's initialization approach, showed opacity 1 and no running animation in both reduced modes; the final screenshots use that readiness condition. This toolkit-startup race is recorded rather than claimed as an unconditional cold-start pass. No toolkit or production files were edited. The first full audit also passed; after aligning the initial management selection with its amended recipient role, the final rebuild, contrast check, full 476-render audit and focused checks above were rerun. Prior canonical evidence is not reused as amendment evidence.


**Not run:** production lint/types/tests/build, real authentication or server permission checks, durable role/session/token operations, database concurrency, full WCAG certification or legal review. Those belong to later implementation/integration/review tasks. This design task adds no production code and does not attest those checks.


## 12. Open questions and assumptions

**Q: Which legal entity, rights-contact email and policy URL replace the bracketed fields before real external activation?** Owner: David with Sempertex legal. The notice v1 body was approved in SPEC round 7; placeholders/review remain explicitly pending. They do not block this visual draft, and no valid policy URL or legal approval is fabricated.

**Resolved from current plan:** English Entusiasta = Enthusiast (owner 2026-10-27); explorer belongs only to Master Designer and staff; SP-1 owns the shared catalogue; numeric chat-limit values are explicitly deferred, not a design blocker. r13's inherited question about own-password completion is answered by T2.2: end old sessions and issue a new session to this requesting browser. Mi cuenta remains signed in; administrator reset separately returns to login. T1.2 defines 12 permission grants and cumulative system counts 3/3/4/6/9/12; Taller sub-capabilities are helper copy, not separately grantable permissions. These are corrections to verified discrepancies, not new owner decisions.

**Confirmed:** owner-selected r13 Parte de acceso; production palette and Geist; centred form hierarchy and retained motion; one role per account; six system roles/four cumulative catalogue plans; at least one permission for custom roles; eight-character minimum, seven-day invitations, 24-hour resets; admin-generated single-use links without automatic email; newer unused links revoke prior same-kind links; immediate session on activation; generic fifteen-minute login hint; mandatory notice reacceptance; saved-work/last-active-administrator protections.

**Limits:** fixture success demonstrates feedback, not authentication, server routing, durable roles, clipboard delivery, token expiry or legal compliance. The global inspector exposes unrelated state/view combinations for review, not valid product transitions. Role persistence/counts and saved-work eligibility must come from SP-1/T2.2, not fixture list position. Later implementation must verify route focus, pending mutations, stale/offline recovery, screen readers and full keyboard behavior. The product browser-language notice rule remains; this planning artifact deliberately starts ES for owner inspection. No optional production preview is enabled or created.

**CONCERNS:** Independent plan/contract approval remains outstanding. Legal placeholders remain pending the owner/Sempertex legal answer above. Sibling bundled HTML styling disagrees with its written production-token contracts; this amendment preserves the chosen canonical mapping. The two canonical-only behavioral corrections are now carried in the amendment TSX itself, avoiding their loss on rebuild. No unresolved plan-name/explorer decision is invented; latest SPEC clarifications/T1.2 settle both. The kit can leave a popup transparent if the inspector opens it before its initial reduced-motion settling frames; initialized reduced-mode dialogs pass (section 11). See section 11 for actual current audit evidence and its limits.

T2.1 must wait for independent approval of this exact amended snapshot; Designer does not approve it. The three requested amendment files and mandatory delegation RESULT are the entire write scope; no separate changelog, history, SPEC, PLAN, repository code, tests or memory file is written.
