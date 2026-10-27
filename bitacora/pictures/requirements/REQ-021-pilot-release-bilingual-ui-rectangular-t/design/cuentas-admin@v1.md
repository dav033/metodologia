---
contract: cuentas-admin
version: 1
status: draft
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
author: Designer
date: 2026-10-26
---

# cuentas-admin@v1 — Sign-in, invitation and administration

## 1. Identity and traceability

This is a revision of the existing v1 planning draft, **not approved for implementation**. Approval belongs to the owner with the plan; the planning workflow copies this snapshot unchanged to `design/contracts/` after approval. The previous v1 draft is revised in place because it has never been approved; no approved contract is changed. This task deliberately writes only this contract and its adjacent HTML mockup, plus the required delegation result; it does not create a changelog or repository preview.

Source snapshot: REQ-021 `SPEC.md`, including Clarifications rounds 4–9 and the owner-approved bilingual data-processing notice v1; Planner rulings Q6–Q8 dated 2026-10-26T16:02 as incorporated in PLAN.md/PLAN.json; `PLAN.md` status draft; `PLAN.json` schema 1.3.0, revision 1. SHA-256 at inspection:

- SPEC: `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4`.
- PLAN.md: `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3`.
- PLAN.json: `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8`.

Exact consumer search: only SP-2 names `ui.contract: cuentas-admin`, `version: 1`, `design_task: T2.1`, `visual_review_task: T2.7`. T2.1 copies the approved snapshot unchanged; UI consumers are T2.3 (V1–V3, V11), T2.4 (V10, C1 account menu on every signed-in pilot page), T2.5 (V4–V8). T2.2 supplies APIs, current notice content and deletion eligibility; T2.6 validates integrated flows; T2.7 checks rendered fidelity; T2.8 audits the result. Upstream: SP-1 T1.2 `permission-map@1`, T1.3 `account-service@1`, T1.4 `session-guard@1`. T1.4 already owns the plain `/sin-acceso` response; V9 styles and actions require coordination with that task, without duplicating server authorization.

| Requirement | Views / flows | Acceptance |
|---|---|---|
| R1 invited accounts, no open registration | V1–V6, V10–V11, C1; F1–F4, F7–F8 | UI-AC-01–09, 13, 18, 35–44 |
| R3 choose permissions and manage roles | V7–V8; F6 | UI-AC-14–17, 23 |
| R16 assign exactly one role/access plan | V5–V6, V8; F3, F5 | UI-AC-10–12, 15 |

Compatibility: **breaking relative to the prior unapproved draft**, because the plan adds account-menu/password and mandatory re-acceptance flows, fixes route locations/deletion policy, unifies invalid-link handling, adds replacement links and signs in immediately after activation (round 8). There is no approved predecessor or production conformance claim. T2.3 must include V11, T2.4 V10/C1, T2.5 the saved-work deletion guard and company in the listing. T2.2 must provide notice-version, own-password and eligibility results. To render V2’s existing role readout, its valid-invitation metadata also needs the assigned role’s display label alongside the currently listed name/email; this is a presentation-field dependency for the Planner to align, not public access to role administration. T2.6/T2.7/T2.8 must include these cases; CG-1/T91 covers composition. SP-1 T1.2/T1.4 require explicit route/session mappings. SP-8/SP-10 later translate the interface; no unrelated Taller or spend UI is changed.

Revision record (kept here because the delegated planning boundary permits no extra changelog): 2026-10-26 — align with rounds 7–8, T2.1–T2.8 and Planner rulings Q6–Q8 at 16:02. This revision removes the separate lockout fixture, adds the neutral fifteen-minute hint to every generic sign-in refusal, specifies requesting-browser re-sign-in after own-password change, resolves the no-tool destination to `/cuenta`, and labels invitation regeneration “Generar enlace nuevo”. These behavior/copy changes affect T2.3 (V1/V2), T2.4 (V10), T2.5 (V6), and T2.2 session/destination results; T2.6–T2.8 must verify them. Compatibility remains breaking relative to the prior unapproved draft. Preserve tokens, component language, breakpoints and all unaffected flows. Owner approval of the plan promotes this draft; the Designer does not approve it.

Earlier revalidation record — 2026-10-26, before round 9: the then-current SPEC/PLAN hashes were unchanged and there was no new owner feedback. Preserve the previous design. This revision aligns two mock interactions with existing requirements: V6 disables saving an unchanged role and enables it after a different role is selected; V10 required-field validation asks for the current password instead of claiming an empty password is incorrect. These are **compatible corrections** to the existing draft expectations, affecting T2.4/T2.5 and their T2.7 visual checks only; the earlier breaking-draft assessment above remains historical. No new behavior or owner decision is introduced.

Current planning revision — 2026-10-26: re-read the current SP-2 outcome, T2.1–T2.8 and round-9 project decisions; the three source hashes above pin this inspection. SP-2 flows, routes, tokens, breakpoints and all unaffected copy are retained. Clarify the `proyectos.ver_todos` helper: other people’s originals are read-only, and a person with `taller.usar` can save an owned copy. Correct the mockup’s V6/V8 `conflict` state to disable mutations until its explicit refresh action, as section 8 already required. These are **compatible clarifications/corrections** to the existing draft, affecting T2.5 help copy and T2.7 rendered checks; no new permission or SP-4 project screen is introduced. T2.2 still supplies authoritative conflict data. UI-AC-57/58 make the existing expectations explicit. Earlier breaking-draft assessments remain historical; approval is still pending.

## 2. Purpose and users

- Invited person: identify the invitation, create a password, read and accept the data notice, and enter Pictures directly. Observable success: an active account, consent version/date recorded by the service and a session and the first permitted destination after activation. When the notice version changes, acceptance of the current version is required before returning to any other page.
- Returning person: email/password login, recovery guidance, password reset via a link supplied by an administrator, sign out. No open signup, self-service email sender, payment, upgrade or plan prices.
- Signed-in person: open the account menu, see their name and role, visit Mi cuenta, change their own password using the current password, or sign out.
- Account administrator (`cuentas.administrar`): find an account, invite it, copy its activation/reset link, review its access, change its single role, deactivate/reactivate or explicitly delete it when the deletion policy permits.
- Role administrator (`roles.administrar`): inspect five system roles, create/edit a custom role using named permissions, and delete only an unassigned custom role. A custom role may grant either administration permission independently; do not rely on a role name or `internas.usar` to grant these screens.
- A person who lacks a permission gets an explanation and a safe return destination, without seeing restricted account data.

## 3. Information architecture and hierarchy

Public shell: Pictures mark → page title → identifying context → fields → one primary action → recovery/invitation guidance. Password forms remain narrow; the data notice is full-length inline disclosure, never hidden behind an acceptance checkbox.

Management shell: Pictures header with theme and the shared current-account menu C1 → “Administración” heading → permission-filtered “Cuentas” / “Roles” navigation → page title and primary action → search/filters → list → detail page. The existing catalogue/internal administration is a separate destination, not a new miscellaneous tab in this flow.

Account detail: identity and status → role with exact permission summary → account dates and notice acceptance → recovery link → separated danger section. Invitations emphasize recipient and access **before** link creation. The resulting link is the main content, accompanied by expiry and manual-sharing instructions.

Mi cuenta: read-only name/email/role → password section with current/new/confirmation fields → session consequence → save. Notice re-acceptance: current version and reason → full notice in browser language → unchecked consent → accept and continue or sign out. The gate omits administration tabs and home links.

Role editor: name → grouped permission checkboxes → live exact access summary → save/cancel → delete section for custom roles. Never display an unexplained permission key as the only label. Counts are secondary; no decorative analytics cards or fabricated adoption metrics.

## 4. Design system and visual language

Read-only evidence: `t12` HEAD `fb872bce` and `pictures`/asesor HEAD `fa101a47`, both `src/app/globals.css`; `src/app/layout.tsx`; `src/app/login/{page.tsx,LoginForm.tsx}`; `src/components/ui/shell/{CabeceraApp.tsx,MenuApp.tsx}`; existing admin entry. These worktrees are references, not the execution base. Semantic palette is shared; asesor additionally extracts icon-button CSS. Reuse the product palette rather than replacing the app with desktop-theme colors.

| Existing tokens | Light | Dark | Use |
|---|---|---|---|
| `--fondo`, `--superficie` | #faf9fc, #ffffff | #0b0c10, #16181f | canvas / panels |
| `--superficie-suave`, `--superficie-2` | #faf8fd, #efe9f8 | #1c1e26, #242733 | sections / secondary fills |
| `--borde`, `--borde-suave` | #e3daef, #efe9f8 | #383c48, #2a2d38 | decorative borders / separators |
| `--texto`, `--texto-suave`, `--texto-tenue` | #1c1425, #6b6178, #766c85 | #f4f5f7, #9aa1ad, #8a91a0 | headings, body, metadata |
| `--acento`, `--acento-hover`, `--acento-suave` | #6d3fe0, #5530b8, #ece3fb | #9479ff, #a58dff, #241f3d | primary, hover, selected |
| `--sobre-acento` | #ffffff | #120b24 | primary text (dark theme must not use white) |
| `--exito`, `--exito-suave` | #1f7a55, #dcf5e9 | #78d6a8, #173b31 | completed / active |
| `--error`, `--error-suave` | #b23a45, #ffeaec | #ff979f, #43252a | failure / danger |
| `--aviso`, `--aviso-suave` | #8f5f12, #fff3d8 | #f7c46b, #3f311c | stale, pending legal input |

Reuse `.ui-button-primary`, `.ui-button-secondary`, `.ui-button-ghost`, `.ui-card`, `.ui-input`, `.ui-alert`, `.ui-chip`, existing checkbox/select/menu patterns and focus-return behavior. Card radius 1.25rem, control radius 0.7–0.8rem; `--radius` remains 0.8rem. Spacing uses 4/8/12/16/24/32/48px steps. Shell max-width 1200px, auth form max-width 440px, notice/activation max-width 640px, management form max-width 760px. These are layout rules, not new global tokens.

Typography: existing Geist sans through `--font-sans`/`--font-geist-sans`; mono only links/IDs. Standalone mockup uses local `system-ui` and `ui-monospace` fallbacks because no font/network asset is permitted. Body 14–16px/1.5, labels 14px/600, page title 28–32px/1.2, section title 18px/1.35, supporting copy minimum 13px. Do not introduce a new brand font.

New proposed semantic token `--control-borde`: `--texto-tenue` in both themes, for input and checkbox boundaries when the existing low-contrast decorative `--borde` cannot supply 3:1 contrast. Keep `--borde` on panels. Focus is existing 2px `--acento` outline with 2px offset. Use text-labelled status chips; icons optional, decorative icons hidden from AT. Use the existing ring-and-dot mark. Hover/focus transitions ≤160ms; no decorative looping animation; reduced motion removes transitions.

## 5. Navigation and interaction model

Route contract aligned to T2.3–T2.5 (query parameters for management subviews are presentation proposals, with no additional page files):

| View | Proposed path | Access / exit |
|---|---|---|
| V1 sign in | `/login?from=<relative-path>` | public; success returns to safe same-origin relative `from`, otherwise first permitted area: Taller 3D, chat, then catalogue; `/cuenta` if none is allowed |
| V2 activate | `/activar/<token>` | public; consumes invitation only on explicit submit; success → first permitted tool with an active session, or `/cuenta` when none is allowed |
| V3 reset password | `/restablecer/<token>` | public; consumes reset only on submit; success → V1 |
| V4 accounts | `/admin/cuentas` | `cuentas.administrar`; exits to permitted home |
| V5 invite / created link | `/admin/cuentas?vista=invitar` | `cuentas.administrar`; back → V4 |
| V6 account detail | `/admin/cuentas?cuenta=<id>` | `cuentas.administrar`; back → V4 |
| V7 roles | `/admin/roles` | `roles.administrar`; back → permitted home |
| V8 create / edit / inspect role | `/admin/roles?rol=nuevo`, `/admin/roles?rol=<id>` | `roles.administrar`; back → V7 |
| V9 access denied | `/sin-acceso` response | existing SP-1 denied response; “Volver al inicio”, “Cerrar sesión” |
| V10 own account | `/cuenta` | any active session with current notice; C1 → Mi cuenta; back to permitted home |
| V11 notice re-acceptance | `/aviso-datos?from=<relative-path>` | active session with outdated notice; accept → revalidated destination; sign out → V1 |

No administration links in unauthorized navigation. Direct requests still rely on server guards. Do not place all account routes under the existing `/admin/*` rule (`internas.usar`) without explicit permission overrides. A role-only administrator must reach V7/V8 even without account permissions. SP-1 owns sign-in/sign-out; T2.2 owns activation/reset/notice/own-password and admin APIs. Administration forms are full content subviews of the two planned page routes; the mockup view switch exposes them independently. Query parameters must never contain activation/reset tokens.

Navigation moves focus to the new H1 (`tabindex=-1`); form validation focuses the first invalid field after announcing the summary. Search does not steal focus. Native select keyboard behavior; labelled controls. Confirmation uses a modal dialog, traps focus, starts on Cancel, closes on Escape except while a committed request is pending, and returns focus to the trigger. No modal for ordinary forms. Browser back preserves non-secret filters; never persist passwords, tokens or full forms to storage. The mockup has its own labelled view/state bar outside the product shell and no external destinations.

C1 shared account menu: align to the trailing edge of each signed-in pilot header, including V9, V10 and V11. Trigger “Cuenta” exposes name and role in the expanded panel at all widths. Panel order: name/role, “Mi cuenta”, permission-filtered “Cuentas” and “Roles y permisos”, then “Cerrar sesión”. At V11 the same identity and sign-out remain but all navigation entries are disabled with “Acepta el aviso para continuar”. Native disclosure/non-modal panel, no nested ARIA menu unless the full menu keyboard pattern is implemented. Enter/Space opens, Tab traverses links, Escape closes and returns focus; clicking outside closes. Opening never navigates. The independent mock “Menú: Cerrado/Abierto” switch exposes both states on every signed-in view; public auth pages have no menu. C1 adds no second header to existing shells. The mock Session selector supplies Administrator, internal employee, Plan 3, accounts-only and roles-only fixtures to inspect independently filtered links; it never changes real permissions.

On the next request after a notice-version change, V11 replaces the requested page; no underlying account/admin/workshop data is rendered. Preserve only a safe same-origin relative destination and re-check permissions after acceptance. Sign-out stays available without acceptance. Changing the notice again while V11 is open shows `conflict`, requires a fresh unchecked acceptance of the new content and never records acceptance for unread text.

## 6. Flows

**F1 sign in.** 1) Enter email and password with password-manager support. 2) Submit once; label becomes “Ingresando…”. 3) On success use the safe requested destination if permitted, otherwise the first permitted area of Taller 3D, chat, catalogue; if none is permitted, use `/cuenta` (Mi cuenta). Re-acceptance takes precedence. Direct unauthorized visits still use V9. 4) Wrong password, unknown email, deactivated account and locked email show exactly the same refusal: “No pudimos iniciar sesión. Revisa el correo y la contraseña o consulta con tu administrador. Si has tenido varios intentos fallidos, espera 15 minutos antes de volver a intentarlo.” This is the only service-refusal fixture (`error`); the neutral hint is always present, regardless of the underlying cause. There is no distinct locked state, attempt counter, account-existence disclosure or client-side lockout inference. 5) Recovery disclosure: “Pide a tu administrador un enlace para restablecer tu contraseña.” Session expiry uses V1 with “Tu sesión terminó. Inicia sesión para continuar.” The 30-day session has no “remember me” toggle.

**F2 activate.** 1) Validate link without consuming it; show read-only recipient and assigned role from server. 2) Set password (8–200 characters), confirmation and show/hide control; paste allowed. 3) Read full supplied notice, explicit unchecked acceptance checkbox “He leído el aviso y autorizo el tratamiento descrito.” 4) “Activar cuenta” validates and submits password plus notice version. 5) Only confirmed service success creates the session and redirects to the first permitted tool (round 8, T2.2/T2.3). The mockup stops on “Tu cuenta está activa. Ya iniciaste sesión” with “Continuar” because the destination tool is outside SP-2; it never asks for a second sign-in. A custom role without any of the three tools lands on `/cuenta` with the new session. The same deterministic destination rule applies to sign-in, activation, safe return after notice acceptance and “Volver al inicio”; it never loops to a forbidden tool. The mock Session selector’s accounts-only/roles-only fixtures expose this fallback; tool destinations stay explicit handoffs outside SP-2. Expired/used/invalid links all replace the form with the same “Este enlace no es válido o ya no está disponible. Pide a tu administrador un nuevo enlace.” and “Ir a iniciar sesión”. The API gives only LINK_INVALIDO; do not reveal a cause, identity or role. Never consume on page load.

**F3 invite.** 1) V4 “Invitar persona”. 2) Required name/email, optional company, required single-role select initially unselected. 3) Preview exact permissions before creation; five system choices plus custom roles, no separate additive plan control. 4) “Crear invitación” → service → same V5 result showing recipient, role, server expiry and selectable link. 5) “Copiar enlace” performs a user-initiated copy; if unavailable, select/copy manually. Announce “Enlace copiado” only after copy succeeds. Explain “Compártelo directamente con esta persona. No se envió ningún correo.” No mail-sent fiction. 6) Return to V4; link is not redisplayed from a hash. Lost/expired invitation recovery: V6 of an invited account → “Generar enlace nuevo” → confirmation explaining that older unused invitations will stop working → fresh seven-day link shown once. Cancel leaves existing links valid. No action revokes or consumes links before confirmed server success.

**F4 reset.** 1) V6 active account “Crear enlace de restablecimiento”. 2) Confirm recipient and explain “Válido por 24 horas. Al cambiar la contraseña se cerrarán sus sesiones.” 3) Generate → copyable result in V6 with expiry/manual sharing. 4) Recipient V3 enters and confirms new password; no repeated legal acceptance. 5) Server success revokes sessions and shows “Contraseña actualizada. Inicia sesión con tu nueva contraseña.” Self-service email reset is out of scope; own-password editing is F7. Expired/used/invalid handling matches F2. Creating a new reset link invalidates every older unused reset link (round 8); explain this in its confirmation. Invitation and reset replacements are independent kinds, never cross-revoke. V6 result offers a selectable/copyable link once; leaving removes it. Server errors retain the old valid link and never show a new one.

**F5 manage account.** 1) Search name/email; filter by status and role. 2) Open V6; identity is read-only (profile editing not scoped). 3) Change single role: show new exact permissions, “Guardar rol”; confirm if administrative permissions are added or this removes one's own access; explain applies on next request. 4) “Desactivar cuenta” confirmation states sessions end on next request, data is retained; on success status becomes Desactivada and reactivation replaces deactivation. 5) “Reactivar cuenta” uses service confirmation and returns active; no invitation creation implied. 6) Delete uses separate danger dialog with recipient email and typed-email confirmation. Last active Administrador cannot be deactivated, deleted or demoted; display reason next to disabled controls; stale server rejection refreshes authoritative status. Account deletion follows round 7: any saved project or personal decoration blocks deletion (`CUENTA_CON_TRABAJO`); explain “Esta cuenta tiene trabajo guardado. Puedes desactivarla para conservarlo.” Accounts without saved work can be deleted after typing the email. Explain “Se eliminarán la cuenta y sus datos personales. El gasto de IA se conservará sin datos personales como Cuenta eliminada. Esta acción no se puede deshacer.” Spend is never saved work. Unknown eligibility (`eligibility_unknown`) disables delete with retry; no guess of zero work. Recheck on the server at confirm; a concurrent saved project replaces the dialog with the saved-work explanation and changes nothing.

**F6 manage roles.** 1) V7 separates five “Del sistema · Solo lectura” rows and custom roles. 2) V8 “Crear rol” requires name, explicit permission choices; none is preselected. At least one permission is required (round 8); zero permissions shows “Selecciona al menos un permiso” and maps service ROL_SIN_PERMISOS to that fieldset. 3) Checkboxes are independent capabilities, not an enforced inheritance tree: selecting a capability never silently adds another. `taller.usar` is intentionally coarse and its helper lists scene AI, export, own projects/decorations, assembly plans/sheet. 4) Summary lists precisely selected names and count; “Guardar rol” shows service success. 5) Edit custom role keeps assigned-account count visible and confirms that affected accounts change on next request. 6) System role renders the same matrix read-only with no save/delete. 7) Delete custom role only when assigned count is zero; otherwise “Este rol está asignado a N cuentas. Asígnales otro rol antes de eliminarlo.” No bulk reassignment tool is implied.

**F7 own password.** 1) C1 → Mi cuenta shows the session account, never the administrator's selected account. 2) Enter current password and new password twice; all allow paste and show/hide. 3) Validate current required, new 8–200 and confirmation equal, then “Cambiar contraseña”; duplicate submit disabled. 4) Incorrect current password (`current_incorrect`) identifies only that field and offers retry without ending the session. 5) Confirmed success clears all password fields, announces “Contraseña actualizada. Se cerraron tus otras sesiones. Sigues conectado en este navegador.” The service revokes all sessions and the route opens a new session for the requesting browser, so the visible experience stays signed in and every other browser must sign in again. Admin-generated resets still end all sessions and return to V1 without this automatic re-sign-in. Do not imply a changed password before success. No profile, email or role self-editing.

**F8 re-accept notice.** 1) Outdated acceptance → V11 on next page request. 2) Explain “Actualizamos el aviso de tratamiento de datos. Léelo y acepta la versión actual para continuar.” Show full current approved version; draft v2 fixture uses v1 body unchanged to avoid inventing legal copy. 3) Accept checkbox begins unchecked, “Aceptar y continuar” validates and sends exactly the displayed version. 4) Only confirmed success restores the revalidated permitted destination; success mock shows a handoff CTA. 5) Error/offline retains unchecked/checked choice for the same version, offers deliberate retry; changed version clears it. 6) Refusal means remaining on V11 or “Cerrar sesión”; no bypass, “Más tarde” or pre-consent home link.

## 7. View specifications

| View | Structure, data and visible copy | Primary / secondary actions | Responsive treatment |
|---|---|---|---|
| V1 | Pictures; “Iniciar sesión”; “Usa el correo con el que te invitaron”; visible Correo/Contraseña labels; helper “El acceso es por invitación.” | “Entrar”; show/hide; recovery disclosure | 440px column, full-width primary; page scroll with keyboard/zoom |
| V2 | “Activa tu cuenta”; recipient/role; new password + confirmation; “Aviso de tratamiento de datos · versión 1”; full notice and acceptance; legal-input warning in mock | “Activar cuenta”; show/hide; success → permitted tool | 640px column; notice full width; no nested legal scrollbox |
| V3 | “Restablecer contraseña”; identified link recipient; 8–200 helper and two password fields; link expiry | “Guardar contraseña”; V1 after success | 440px column |
| V4 | “Cuentas”; invitation CTA; search, status and role filters; list shows name/email, company, role, status, last access; total/filtered result text | “Invitar persona”; per-row “Ver cuenta” | ≥640px semantic table; <640px equivalent labelled cards, no hidden identity/access/status |
| V5 | Back; “Invitar persona”; name/email/company/role; exact-access preview; result recipient, expiry, full link | “Crear invitación”; Cancel; result “Copiar enlace”, “Volver a cuentas” | ≥1024px form + 300px access sidebar; below stack preview before submit |
| V6 | Back; name/email/company/status; invitation/activation/last-access dates; notice version/date or “Aún no ha aceptado”; single-role select and preview; reset or invitation-replacement section; danger section | “Guardar rol”; reset / replace invitation; deactivate/reactivate; delete | ≥1024px identity rail + main; below stack; destructive controls never icon-only |
| V7 | “Roles y permisos”; “Crear rol”; system-role rows with permission counts; custom-role rows with assigned counts | “Ver rol” or “Editar rol” | One readable list at all widths; counts wrap rather than clip |
| V8 | Back; “Crear rol” / role name; custom name field; grouped permission matrix, independent checks with explanations; summary; assigned count | “Guardar rol”; Cancel; delete unassigned custom role | ≥1024px matrix + 300px summary; smaller one column, full checkbox label hit target |
| V10 | “Mi cuenta”; read-only name/email/role; current/new/confirm password with length helper and other-session explanation | “Cambiar contraseña”; “Volver al inicio”; C1 sign out | 640px maximum content, one column at every width |
| V11 | “Revisa el aviso actualizado”; account identity, version, full notice, explicit acceptance; gate reason | “Aceptar y continuar”; “Cerrar sesión” | Same 640px notice layout as V2; no administration tabs |
| V9 | “No tienes acceso a esta sección”; “Tu rol actual no incluye este permiso. Consulta con tu administrador si necesitas acceso.” No restricted resource details | “Volver al inicio”; “Cerrar sesión” | 440px column, buttons wrap |

Permission labels from SP-1 catalogue (one source at implementation):

| Group | Key → visible ES label / helper |
|---|---|
| Herramientas | `chat.usar` → Chat asistido; `contador.usar` → Contador de globos; `catalogo.ver` → Catálogo; `costos.usar` → Calculadora de costos; `decoraciones.explorar` → Explorador de decoraciones |
| Taller y proyectos | `taller.usar` → Taller 3D / Incluye IA de escena, planes y hoja de armado, exportación, proyectos y decoraciones propios; `proyectos.ver_todos` → Proyectos de todas las cuentas / Lectura de proyectos ajenos. Con Taller 3D puedes guardar una copia propia; el original no se modifica. |
| Equipo interno | `gasto.ver` → Gasto de IA; `internas.usar` → Herramientas internas |
| Administración | `cuentas.administrar` → Administrar cuentas; `roles.administrar` → Administrar roles; `textos.corregir` → Corregir textos en inglés |

System role summary: Usuario · Plan 1 = first three; Usuario · Plan 2 adds costs/explorer; Usuario · Plan 3 adds Taller; Empleado interno adds all-projects, spend, internal; Administrador adds all three administration permissions. These have 3/5/6/9/12 permissions respectively, exactly the service catalogue. No sixth generic Usuario role. Product copy is Spanish in SP-2; every screen keeps its strings together as T2.3–T2.5 specify for SP-8/SP-10. The mockup separately offers the **already supplied** ES/EN legal notice as a content inspection control, not an account language preference or a claim that the whole UI is translated.

Legal content: reproduce SPEC “Data-processing notice (v1, SP-2)” ES/EN **verbatim**, retaining bracketed fields for the legal name, rights email and policy URL. Show “Aviso v1 aprobado por el propietario · datos legales y revisión de Sempertex pendientes” beside the mock notice. Never turn a placeholder into a fake policy link or invent legal advice. `notice_pending` disables activation/re-acceptance until the remaining legal review and fields are complete; the normal valid-notice scenario is explicitly simulated for design review only. Owner approval of v1 text is confirmed in round 7; legal identity/contact/URL and Sempertex review remain outstanding before real users are invited. Implementers must use approved content/version and actual URL. This is the existing SPEC gate, not a new approval flow.

## 8. States

State names below are exact mockup selector values. Every applicable pair is reachable with the visible “Vista” and “Estado” selectors; dialog variations have a separate “Diálogo” selector. Selector changes are design controls, not product features. Mockup data uses fictional people and `example.com`/`.invalid`; nothing is stored or sent.

| State | Applicable views | Appearance, available action, transition / recovery |
|---|---|---|
| `ready` | V1–V11 | Normal view; V9 is already a denial response. Blank forms count as ready, not an empty data state. |
| `loading` | V1–V8, V10–V11 | Labelled static skeleton / “Cargando…”; no data flashes or enabled mutation. V1 loading represents session/destination check, not remote form data. |
| `error` | V1–V8, V10–V11 | Alert; auth uses generic refusal, others “No pudimos cargar/guardar…” with safe retry and preserved non-secret inputs. A mutation error never shows success. |
| `offline` | V1–V8, V10–V11 | “Sin conexión. Vuelve a conectarte y reintenta.” Form drafts remain in memory; mutation disabled; no queued saves or automatic replay. |
| `pending` | V1–V3, V5–V6, V8, V10–V11 | In-flight submit; changing fields/repeating submit disabled; verb-specific label. Enter cannot duplicate the request. Outcome comes only from confirmed service response. |
| `validation` | V1–V3, V5–V6, V8, V10–V11 | Summary and inline labelled errors, first invalid field focused; email syntax, required name/role, 8–200 password, matching confirmation, required consent. Role requires at least one permission; focus the permission group on ROL_SIN_PERMISOS. |
| `success` | V1–V3, V5–V6, V8, V10–V11 | Explicit completed action; V5 retains copy result until navigation; V6/V8 refreshed authoritative data. Auth success CTA goes to the scoped handoff; mockup does not pretend to render the home product. |
| `empty` | V4, V7 | V4 no accounts: “Aún no hay cuentas” + Invite. This fixture represents a permitted empty listing, not deletion of the current admin. V7 no custom roles: five system roles remain + Create. |
| `no_results` | V4 | Search/filter matching zero: “No hay cuentas con estos filtros” + “Limpiar filtros”; distinct from no accounts. |
| `stale` | V4, V6–V8 | Timestamp and “No pudimos actualizar. Estos datos pueden haber cambiado.” Read-only cached data, mutation disabled; “Actualizar” fetches fresh state. Partial responses use the same warning, identify unavailable fields as “No disponible”; never show false zero. |
| `denied` | V4–V8 | Replace view with V9; discard restricted data, no form underneath. 401 instead returns V1/session-ended. |
| `expired`, `used`, `invalid` | V2–V3 | Replace password form with the identical LINK_INVALIDO explanation for all three fixtures, “Ir a iniciar sesión”, ask administrator for a new link; no token, cause or account information. |
| `notice_pending` | V2, V11 | Legal placeholders/warning visible; checkbox and acceptance/activation disabled with adjacent reason. |
| `conflict` | V5–V6, V8, V11 | Duplicate invite email: identify existing account only to authorized admin and offer list; concurrent role/status change: refresh authoritative record before resubmitting. Preserve proposed input separately; never overwrite silently. V11 means a newer notice version: reload its full content and clear the checkbox before another submit. |
| `invited` | V6 | Invited account shows Generar enlace nuevo, seven-day expiry and an invalidation warning; reset-password creation is absent until activated. Replacement result follows confirmed success and is shown once. |
| `last_admin` | V6 | Last active Administrator; role-change, deactivation and delete disabled with the same explanation; reset stays available. Server refusal remains authoritative. |
| `fixed` | V8 | System role name/permissions read-only, “Rol del sistema · Solo lectura”; no save or delete. |
| `role_in_use` | V8 | Custom role editable; delete disabled with assigned-account count and required next step. |
| `session_expired` | V1 | “Tu sesión terminó. Inicia sesión para continuar.” No restricted data retained. |
| `has_work` | V6 | Delete disabled with saved-project/decoration explanation; deactivate stays available unless last admin. |
| `eligibility_unknown` | V6 | “No pudimos comprobar si tiene trabajo guardado.” Delete disabled; “Comprobar de nuevo” refreshes eligibility. Other actions follow their own permission/session checks. |
| `current_incorrect` | V10 | Inline “La contraseña actual no es correcta”; focus current field, retain only in-memory non-secret context and retry, no success. |
| `closed`, `open` | C1 | Independent visible Menú selector; identity, role and Mi cuenta/sign-out visible in open state at all widths. On V11 only sign-out navigates. |
| `disabled` | V1–V3, V5–V6, V8, V10–V11 | Primary action disabled with visible reason (incomplete input, unchanged role, or pending legal requirement). No unexplained disabled icon. |

Dialogs selectable in the mockup: `change_role`, `deactivate`, `reactivate`, `delete_account`, `reset_link`, `replace_invite` in V6; `edit_role`, `delete_role` in V8. Each has `confirm`, `pending`, `error` phases. Final deletion/reset/role changes never execute on opening the dialog. Password and token secrets are never echoed into alerts. Clipboard failure remains a local error with selectable link, not a recreated invitation.

Genuinely inapplicable: V9 has no list, mutation, loading, empty, success or offline state; it is a server denial explanation. No infinite scroll/pagination required by the current plan: data-volume/pagination must be specified if the implementation API is paginated; never silently truncate accounts. V10–V11 have no list/empty state because identity and mandatory content are either present or loading/error. V10 has no permission-denied state for an active current-notice session: an expired/deactivated session returns V1. C1 has no remote loading or empty state because identity comes with the server session.

No optimistic destructive operations or background offline queue. No email delivery/loading/delivery error because no sender exists. No spending caps or billing state.

## 9. Responsive behavior

Breakpoints are explicit proposed layout rules for this subplan, grounded in existing `body { min-width: 320px }` and Tailwind `sm`/`lg` conventions, not inferred support for only certain devices:

- **Compact 320–639px:** 16px page gutter; single column; mock controls wrap; account list becomes cards with labelled fields; search/status/role filters stack. Header brand and actions wrap; C1 remains visible, its open panel shows the full name and role at compact widths too. Cuentas/Roles links remain visible and wrap (no hidden hamburger navigation required). All form/action groups can wrap, main actions fill width. Dialog width `calc(100% - 32px)`, max-height `calc(100dvh - 32px)`, internal scroll; Cancel precedes destructive confirm. Page remains scrollable with virtual keyboard and at 200% text size.
- **Medium 640–1023px:** 24px gutter; semantic account table with wrapping email/role (no truncation-only identity); controls wrap in rows; forms and access previews stack; dialogs max-width 520px.
- **Wide ≥1024px:** 32px gutter, max-width 1200px; invitation/account/role form and summary can use 1fr/300px columns; account table stays full width; auth remains narrow rather than stretching. No sticky summary that can cover actions on short viewports.

Full URLs/emails use `overflow-wrap:anywhere`; no page-level horizontal scroll at any declared width including 320px. 639/640 and 1023/1024 boundaries must be tested. At 400% desktop zoom (equivalent 320px CSS viewport), compact reflow applies. No element depends on hover alone; mobile has the same operations. No full-screen navigation takeover.

## 10. Accessibility targets

Target **WCAG 2.2 AA**, awaiting rendered product verification; a draft/mockup is not a conformance claim.

- One H1; header/nav/main landmarks, skip link, table captions and scoped headers; compact cards preserve labels and equivalent operation. Use anchors for real navigation, buttons for actions. Mockup scene controls are labelled selects outside the product.
- Visible form labels, required indicators in text, correct autocomplete (`username`/email, `current-password`, `new-password`, name/organization); no password composition puzzle, paste blocking or timer challenge. Show/hide buttons expose current state and field association.
- Native controls or existing accessible Radix patterns. Group permission checkboxes in fieldsets/legends; helper describes coarse permission implications. Tab/Shift+Tab reach every action; Space toggles a checkbox; Enter submits once. Focus ring 2px, offset 2px, never clipped.
- Error summary/live alert plus field `aria-invalid` and `aria-describedby`; generic auth rejection does not reveal account existence. Announce loading/completion/copy status politely; no announcement of complete rerendered tables per keystroke. `aria-busy` during pending/loading.
- Dialog labelled title/description, inert background, focus trap, Cancel-first initial focus, Escape close and trigger focus return; visible close/cancel. During pending, explain why closing is temporarily disabled. Destructive action requires email confirmation; it is never prefilled with the target email.
- Text contrast ≥4.5:1 (large text ≥3:1), meaningful controls/focus ≥3:1. Use `--control-borde` on control boundaries and existing semantic pairs; decorative panel borders are not interactive boundaries. Disabled controls additionally have a readable adjacent reason. Do not communicate status only by hue.
- Target 44×44px touch controls in this subplan (at least WCAG 24×24px including spacing exceptions); label hit areas ≥44px. Text resize 200%, reflow at 320px CSS width, no forced viewport zoom restriction. Reduced motion disables nonessential transitions/animations.
- Rendered verification still required: keyboard and focus sequence, native dialog behavior, screen-reader announcements, measured color combinations in both themes, high zoom and legal-policy link once supplied. English notice uses `lang=en`; interface remains `lang=es` until SP-10 translation.

## 11. Visual acceptance criteria

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | 320–639px | V1 ready | Correo and Contraseña labels and Entrar fit without horizontal scroll. |
| UI-AC-02 | ≥320px | V1 error | Unknown email, wrong password, deactivated account and locked email display the same generic refusal including the neutral fifteen-minute wait hint. |
| UI-AC-03 | ≥320px | V1 pending | Entrar becomes Ingresando… and repeat submission is disabled. |
| UI-AC-04 | ≥320px | V1 ready | The invitation-only guidance is visible and there is no signup action. |
| UI-AC-05 | ≥320px | V2 ready | Recipient, assigned role and full data notice precede the activation action. |
| UI-AC-06 | ≥320px | V2 validation | Unaccepted notice is identified beside the unchecked checkbox. |
| UI-AC-07 | ≥320px | V2 notice_pending | Legal placeholders carry a pending-content warning and activation is disabled. |
| UI-AC-08 | ≥320px | V2/V3 expired/used/invalid | The password form is replaced by recovery guidance and a sign-in action. |
| UI-AC-09 | ≥320px | V3 success | The page confirms the password change and offers sign-in rather than showing another password form. |
| UI-AC-10 | ≥1024px | V5 ready | A single role choice and its exact permission preview are simultaneously visible in two columns. |
| UI-AC-11 | 320–1023px | V5 ready | The same access preview stacks before submit without removing permissions. |
| UI-AC-12 | ≥320px | V5 ready | Plan 1/2/3 previews show respectively 3/5/6 named permissions and no price or payment control. |
| UI-AC-13 | ≥320px | V5 success | Recipient, seven-day/server expiry, selectable link and manual-sharing instructions appear together. |
| UI-AC-14 | ≥320px | V7 empty | Five read-only system roles remain visible when there are no custom roles. |
| UI-AC-15 | ≥320px | V8 ready | Checking one permission updates the exact summary without selecting other permissions. |
| UI-AC-16 | ≥320px | V8 fixed | A system role has a read-only label and no save/delete control. |
| UI-AC-17 | ≥320px | V8 role_in_use | Delete is disabled beside the assigned-account count and reassignment guidance. |
| UI-AC-18 | ≥320px | V6 ready/reset_link | The reset dialog states 24-hour validity and session closure only after password change. |
| UI-AC-19 | ≥320px | V6 last_admin | Role change, deactivate and delete are disabled beside the last-admin explanation. |
| UI-AC-20 | 320–639px | V4 ready | Each account card retains name, email, company, role, status and Ver cuenta. |
| UI-AC-21 | 640–1023px / ≥1024px | V4 ready | Table headers identify person, company, role, status, last access and action; long email wraps. |
| UI-AC-22 | ≥320px | V4 no_results | Limpiar filtros restores the unfiltered list without creating an account. |
| UI-AC-23 | ≥320px | V8 ready/edit_role | The custom-role save confirmation states that assigned accounts change on next request. |
| UI-AC-24 | ≥320px | V4/V6–V8 stale | A stale-data warning includes a last-update time and mutations are disabled. |
| UI-AC-25 | ≥320px | V1–V8, V10–V11 offline | No mutation is offered as queued or successful; retry requires a deliberate action. |
| UI-AC-26 | ≥320px | V6 ready/delete_account | Delete confirmation requires typing the shown email and retains a visible Cancel action. |
| UI-AC-27 | ≥320px | V6 disabled | The generic disabled account fixture explains that an unchanged role has no save action; saved-work guards use UI-AC-39/40. |
| UI-AC-28 | ≥320px | V4–V8 denied | Only the access-denied explanation and safe exits remain; restricted data is absent. |
| UI-AC-29 | 320 / 639 / 640 / 1023 / 1024 / 1440px | all reachable states | The document has no horizontal overflow. |
| UI-AC-30 | ≥320px | all interactive states | Keyboard focus remains visible on every actionable control in both themes. |
| UI-AC-31 | ≥320px | dialogs confirm/error | Escape closes the dialog and restores focus to its trigger. |
| UI-AC-32 | ≥320px | dialogs pending | Dialog confirmation is disabled and no duplicate action is possible. |
| UI-AC-33 | ≥320px | ready/error/success | Status messages use text labels and measured foreground/background pairs meet AA contrast. |
| UI-AC-34 | ≥320px | all mockup states | The Mockup/draft label and view/state selectors remain visible and usable. |
| UI-AC-35 | ≥320px | C1 open | The panel shows account name, role, Mi cuenta and Cerrar sesión, with denied administration destinations absent. |
| UI-AC-36 | 320–639px | V10 ready | Current, new and confirmation password labels fit in one column without horizontal scroll. |
| UI-AC-37 | ≥320px | V10 current_incorrect | Only the current-password field carries the incorrect-password message and receives focus. |
| UI-AC-38 | ≥320px | V10 success | Password fields are absent and the success message says other sessions closed while this browser stays signed in. |
| UI-AC-39 | ≥320px | V6 has_work | Delete is disabled with the saved-work reason and deactivation is available. |
| UI-AC-40 | ≥320px | V6 eligibility_unknown | Delete is disabled and Comprobar de nuevo is offered without claiming there is no saved work. |
| UI-AC-41 | ≥320px | V11 ready | The full current notice, version and unchecked consent appear with no route to another page before acceptance. |
| UI-AC-42 | ≥320px | V11 conflict | Acceptance is disabled until the newer version is loaded and the checkbox is cleared. |
| UI-AC-43 | ≥320px | V11 pending | Aceptando… replaces the primary label and repeat submission is disabled. |
| UI-AC-44 | ≥320px | V2/V11 ready | Switching notice language displays the supplied ES or EN text verbatim with the matching lang attribute. |
| UI-AC-45 | ≥320px | V1 error | The sole refusal fixture shows “Si has tenido varios intentos fallidos, espera 15 minutos antes de volver a intentarlo.” and the state selector has no locked fixture. |
| UI-AC-46 | ≥320px | V1 session_expired | The expired-session explanation appears above the sign-in form. |
| UI-AC-47 | ≥320px | C1 open | Escape closes the panel and returns focus to Cuenta. |
| UI-AC-48 | ≥320px | V5/V6 success | The created link warns that it will not be shown again after leaving the result. |
| UI-AC-49 | ≥320px | V6 invited/replace_invite | The invited-account action reads “Generar enlace nuevo” and its confirmation explains that older unused invitation links stop working; the new link lasts seven days. |
| UI-AC-50 | ≥320px | V6 ready/reset_link | The reset confirmation states that old unused reset links will stop working. |
| UI-AC-51 | ≥320px | V8 validation | Saving a role with no checked permission shows Selecciona al menos un permiso beside the permission group. |
| UI-AC-52 | ≥320px | V2 success | Activation confirms the new session and offers Continuar without requiring another sign-in. |
| UI-AC-53 | ≥320px | V1/V2 success · accounts-only/roles-only fixture | Continuar opens Mi cuenta when the assigned role allows none of Taller 3D, chat or catalogue. |
| UI-AC-54 | ≥320px | V6 ready/reset_link | Reset copy says all sessions end when the recipient changes the password; no automatic re-sign-in is promised. |
| UI-AC-55 | ≥320px | V6 ready | Guardar rol is disabled with the unchanged-role explanation until a different role is selected. |
| UI-AC-56 | ≥320px | V10 validation | An empty current-password field says Escribe tu contraseña actual; only current_incorrect claims the password is incorrect. |
| UI-AC-57 | ≥320px | V6/V8 conflict | Save and mutation actions are disabled until Actualizar datos reloads the authoritative record. |
| UI-AC-58 | ≥320px | V8 ready/fixed | The Proyectos de todas las cuentas helper states that foreign originals are read-only and an owned copy requires Taller 3D. |

## 12. Open questions and assumptions

**Open questions for the owner:** none in this revision. Q1 is an outstanding input, not a repeated question: the legal entity name, privacy-policy URL and rights-contact email remain visible bracketed placeholders tracked in SPEC Inputs. David supplies those fields and Sempertex legal reviews before real users are invited; the v1 text is already owner-approved. Q2–Q5 were resolved by rounds 7–8; Q6–Q8 were resolved by the Planner on 2026-10-26T16:02.

**Confirmed:** single-role accounts; five system roles; fixed system roles/custom roles editable per current Planner ruling; invitation copied manually (7 days), admin-generated reset (24 hours), password 8–200, 30-day server session; one generic login refusal for wrong password, unknown email, deactivated and locked accounts, always including the neutral fifteen-minute wait hint; no public registration; `/asesor` and `/happie` remain separate; account/role mutation enforced by the server; first administrator is created outside these screens by the owner-run command. Round 7 confirms saved-work accounts cannot be deleted (deactivate only), spend is retained without personal data as Cuenta eliminada, notice v1 text is owner-approved, and changed notice versions require re-acceptance on the next request. Round 8 confirms regeneration invalidates older unused links of the same kind, roles require at least one permission, and activation opens a session directly. Typed-email deletion confirmation is required by T2.2/T2.5. Own-password change revokes all sessions then opens a new session for the requesting browser; admin resets end all sessions. The fallback when no Taller/chat/catalogue permission exists is `/cuenta`. Former Q1–Q8 are not open questions. Do not reopen them.

**Proposals awaiting plan approval:** management query parameters and breakpoints in sections 5/9, and the presentation/interaction choices in this draft. Chosen mock data is illustrative, not a discovered customer list. Dates/expiry in the product come from the server, formatted in the user's locale with timezone available; the mockup fixes 26 Oct 2026 15:40 America/Bogota for reproducibility.

**Planner handoff:** exact consumers are now assigned (T2.1–T2.8). Implement the resolved Q6–Q8 rules consistently across SP-1 and SP-2, confirm the remaining presentation proposals, map session-only `/cuenta` and `/aviso-datos` without permission leakage, and decide list API pagination if needed. SP-4/SP-5 register saved-work ownership checks and SP-6 anonymizes retained spend as already ruled; do not reopen that policy as a question. Normal/success mock scenarios simulate completed legal inputs, never authorize real activation while the legal fields/review tracked in SPEC Inputs are pending. Version 2 in V11 is an illustrative next-version fixture using the exact v1 body, not new approved legal content. This task finishes planning artifacts; approval and production validation remain outside the Designer's authority.

Earlier mockup verification — 2026-10-26 (prior draft): local headless Chromium through the existing `pictures` worktree Playwright dependency, opening the standalone file URL. Before the two compatible corrections, all 11 views and 105 view/state pairs passed at 320/639/640/1023/1024/1440px in light/dark themes (1,260 rendered combinations), with no page errors, network requests, horizontal document overflow or broken `aria-describedby` references. After the corrections, 322 assertions passed, including 288 affected-view combinations for V6/V10 across the same widths/themes; checks covered unchanged-role enablement, required versus incorrect current-password feedback, password-change completion, generic sign-in refusal, indistinguishable invalid links, notice language, notice-menu gating, Escape focus return, no-tool fallback, saved-work deletion guards and read-only system roles. An additional 36 dialog state/width combinations passed at 320/1024px, including confirmation/pending/error, Cancel-first focus and Escape focus return; invitation replacement copy and independent permission selection passed. Static inspection confirmed twelve numbered sections, draft status, 56 acceptance rows, no external assets and exact SPEC ES/EN notice text. Rendered images inspected: V4 wide/light and V10 compact/dark. This evidence concerns only the planning mockup: production API behavior, full screen-reader coverage, measured contrast and production visual acceptance remain for T2.6–T2.8.

Current mockup verification — 2026-10-26: after the round-9 helper clarification and conflict-state correction, headless Chromium through the existing `/home/david/dev/pictures-wt/asesor/node_modules/playwright` dependency opened the standalone `file://` artifact. All 11 views and 105 view/state pairs at 320/639/640/1023/1024/1440px in light/dark themes passed (1,260 combinations): no horizontal document overflow, missing H1, broken `aria-describedby`, JavaScript page error or network request. A separate interaction run passed 195 assertions, including eight dialog variants at 320/1024px and all three phases (48 dialog-phase combinations), Cancel-first focus, pending-request protection, Escape focus return, conflict refresh gating, saved-work and last-administrator guards, read-only system roles, no-tool fallback, generic sign-in refusal, indistinguishable invalid links, own-password validation and exact ES/EN notice text. Static checks confirmed twelve numbered sections, draft status, 58 unique acceptance rows, labelled `view`/`state`/`scene`/`theme` selectors, no external assets and network-blocking CSP. `git diff --check` passed for the two artifacts. Rendered images inspected before revision: V4 wide/light and V2 compact/dark; after revision: V6 conflict wide/light and V8 project-permission help compact/dark. No production code, repository tests, build, live account/API behavior, screen-reader audit or measured contrast audit was run; those remain outside this planning-artifact verification.
