---
name: Parte de acceso
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
revision: r13.dir-a
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
date: 2026-10-27
source_revision: r12.dir-a
feedback: "2026-10-27T09:08 direction=a: correct left-heavy alignment and use available space better"
---

# Parte de acceso — direction A

## 1. Identity and traceability

Single-direction iteration **r13 of r12 A**, status **draft**, awaiting owner selection with the plan. This twelve-section direction note is not the canonical contract or an approved implementation input. Direction name stays “Parte de acceso”. No new direction, thumbnails, shared contract, plan or repository changes.

Behavior source: `cuentas-admin@v1.r13.behavior.md` SHA-256 `3fb1bbc78c83aae3`. Context snapshots: `SPEC.md` SHA-256 `65b1e5ecc06f20d9`; `PLAN.md` SHA-256 `cc7e53f2abf3c23c`; `PLAN.json` SHA-256 `7a2c833a7e711508`. SP-2 covers R1 invitation-only accounts, R3 role management and R16 assigned access. The existing SP-1 contracts remain account-service@1, session-guard@1 and permission-map@1. Design tasks are T2.1, T2.3–T2.5 and visual review T2.7; no engineering path is added to design scope.

## 2. Purpose, concept and memorable move

The administrator answers “Who has access, what is their role, and what needs changing?” Each ruled row keeps name, email, optional company, assigned role, state, last access and contextual action together. Access forms handle sign-in, activation, reset and mandatory notice acceptance; Mi cuenta identifies the person and changes their password.

The existing kinetic registration remains the memorable interaction: the working panel seats vertically, rows register horizontally and feedback makes a short registration stroke. The removed plan rail and “De la idea al montaje” card have no replacement. This is an administration surface, with ordinary task titles and no slogan or decorative total. All rows and operations are labelled as mock data; neutral account descriptions and `@prueba.local` fixtures replace fictional people, businesses and dates. Row totals still derive from the visible fixture list.

## 3. Preserved composition and the look ledger

Started from a copy of `cuentas-admin@v1.r12.dir-a.tsx`. Applied the owner’s 2026-10-27T09:08 direction=A feedback: centred all five form-oriented views in a content-sized 676px panel instead of anchoring a 620px form to the left of a full-width sheet. Their page titles, form surfaces, feedback and stacked footer share that axis; desktop forms retain their readable 620px width and equal outer gutters. Accounts retain the full working register, with search/role/state filters now sharing space in flexible 2:1:1 columns. The role selector expands from 200px to 240px on desktop so its labels balance the permission sheet. Below the existing breakpoints, the established stacking remains. Shell, navigation, content, fixtures, tokens, typography, shapes, flows and kinetic registration stay as in r12.

The immutable sibling `taller-esenciales@v1` and `proyectos@v1` Markdown and HTML were inspected. Their Markdown establishes Pictures' existing semantic palette, Geist/system-sans typography, neutral navigation and account/header vocabulary. Their current bundled HTML still contains older exploratory palettes, typography and hero copy that disagree with those written contracts. This revision follows the production token/font sources and the written sibling contracts, rather than importing that drift. No sibling file is changed. The direction keeps its existing horizontal navigation and working-register composition as explicitly requested.

Read-only product references: both worktrees' `src/app/globals.css`, `src/app/layout.tsx`, `src/app/login/{page,LoginForm}.tsx`, `src/components/admin/AdminTabs.tsx` and `src/components/ui/shell/CabeceraApp.tsx`. Existing login is a password form; email/invitation/role controls are the scoped additions. Existing administration uses a sober title and in-flow tabs; the header's ring-and-dot mark is reused, with the required account menu. No brand, display face or exploration palette is proposed. Production and other local changes remain untouched.

## 4. Eight axes, visual language and real components

| Axis | Present expression |
|---|---|
| Concept | An operational access register: invited accounts, assigned role, access state and the next management action. No marketing panels or plan promotion. |
| Layout | Compact Pictures/Sempertex header, sober 24px page title and preserved horizontal route rule. Accounts fill the register width with balanced 2:1:1 search/role/state filters; roles use a 240px selector beside the permission sheet. Access, activation, reset, notice and Mi cuenta use a centred 676px panel and a shared 620px form/feedback axis, eliminating the empty right half. |
| Navigation | Preserved neutral horizontal Cuentas / Roles y permisos / Mi cuenta navigation, contextual account dialogs and named account disclosure. Invitation-only access has no registration route. Planning selectors remain outside the product shell. |
| Typography | Production Geist Sans and Geist Mono embedded from the existing local build. Page title 24px, section titles 20px, body 14–16px and metadata 11–13px; no display family or hero. ES is the initial language; EN appears through the language selector. |
| Density | Preserved 24px account-row padding, 28px desktop / 20px phone paper insets, 32px panels, 24px inset surfaces, 18px inputs, 8px checkboxes and pill controls/status chips. Content-sized form panels have equal outer gutters; wide management views retain available working space and flexible filters. |
| Components | Installed shadcn/Base UI Button, Input, Checkbox, Skeleton, Dialog and AlertDialog, composed as account rows and permission fieldsets. Production ring-and-dot mark; rounded panels, semantic pill statuses and neutral navigation. Dialog close text follows ES/EN. |
| Colour | Exact Pictures globals.css palette mapped as in proyectos@v1: light #faf9fc / #ffffff with #6d3fe0 actions; dark #0b0c10 / #16181f with #9479ff actions and #120b24 foreground. Existing success/warning/error tokens; input edges alias texto-tenue. No exploration palette. |
| Motion | Preserved kinetic registration: cubic-bezier(.76,0,.24,1), 480ms paper/row/rule/status registration, 55ms row offsets and 180ms controls, natural 300/140ms and subtle 160/100ms. Skeleton scan and hover/press arrow shift remain; retired rail/foil motion is removed. Reduced/still disables movement and hidden tabs pause animation. |

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

Installed components: `shadcn:button` default/outline/destructive, `shadcn:input` text/email/password, `shadcn:checkbox` checked/unchecked/disabled, `shadcn:skeleton`, `shadcn:dialog` and `shadcn:alert-dialog`; imports are `@/components/ui/{button,input,checkbox,skeleton,dialog,alert-dialog}`. Installed Base UI/Animate UI primitives provide focus containment and destructive confirmation. The real DialogClose is recomposed with a translated accessible name so ES does not expose the library's English “Close”. The table-like account rows, role sheet, fieldsets and header are existing custom compositions; native language/role/state selects remain native. `@kit/mockup` supplies mountMockup/useMockup and `@kit/motion` supplies useMotionProfile. No snippets, installation or fallback builder.

## 5. Navigation and interaction

The seven native preview views are Cuentas, Roles y permisos, Iniciar sesión, Activar invitación, Restablecer contraseña, Mi cuenta and Nuevo aviso obligatorio. The template's visible **Mockup** bar retains `view`, `state`, `scene`, `theme` and the expressive-default movement selector. The product has its own ES/EN native language selector, set to ES for this planning artifact; EN is an explicit selector choice.

Signed-in views have neutral in-flow account routes and an account disclosure naming the neutral administrator fixture and its role, with Mi cuenta and sign out. The phone summary shows the name; opening it reveals the role and the same actions. Mi cuenta's identity matches admin@prueba.local in the account menu; activation identifies plan3@prueba.local. In the product, the invitation notice initially follows browser language with the selected language visible; this mockup deliberately opens in ES for the owner’s inspection and allows EN through the selector. The mandatory-notice view withholds other product navigation and offers acceptance or sign out. Preview controls remain external to that product barrier.

Management is contextual to the selected account. Dialogs retain keyboard focus and return it when dismissed. Invitation, management and one-time-link dialogs permit Escape; account/role deletion uses AlertDialog and an explicit Cancel. The mockup simulates outcomes locally and does not implement authenticated routing, token issuance or permission checks.

## 6. Flows retained

1. **Sign in:** invited email and password → requested permitted page, first permitted tool, or Mi cuenta when the role has no tools. The error fixture uses one generic message for wrong password, unknown email, deactivated account and locked email; it always explains the fifteen-minute wait after repeated failures. Password recovery asks the administrator for a single-use 24-hour link; no automatic email delivery or public registration is introduced.
2. **Activate:** invited name/email → new password and repeated password, minimum eight characters → full browser-language notice v1 → explicit unchecked acceptance → activation and direct signed-in first-tool destination. Used, expired or replaced links instead ask for a new administrator-issued link. Invitation lifetime is seven days.
3. **Notice update:** the new version blocks every other product page until acceptance. The completion copy records the obligation to store version and date. The supplied notice text remains exact in ES/EN, including bracketed legal placeholders.
4. **My account:** read personal identity and role → current password plus new password twice → password change and sign in again. Acceptance version/date are visible example metadata. Changing the password ends sessions.
5. **Invite/manage:** search and filter → invite name, email, optional company and one role → generate → copy a link shown once → close. Registered email is refused. For an existing account, change role, deactivate/reactivate, generate a fresh invitation/reset link or request deletion. Fresh links invalidate older unused links of the same kind; that consequence is stated before generation and on the receipt. Clipboard refusal explains manual selection/copy.
6. **Delete:** saved work refuses deletion without changing the account (`CUENTA_CON_TRABAJO`); the last administrator cannot be deleted, deactivated or stripped of the administrator role. An account without saved work requires its exact email before permanent deletion. AI spend is retained without personal data as “Cuenta eliminada”. The mockup illustrates the choice; it does not attest database integrity.
7. **Roles:** select one of five read-only system roles to inspect permissions grouped by tool, or create/edit a custom name and checkbox selection. A custom role with no permission is refused with `ROL_SIN_PERMISOS`. Assigned custom roles cannot be deleted; an unassigned custom role can be deleted after confirmation. Every account has one role, including access plans.

## 7. View specifications

| View | Main hierarchy and controls | Supporting information |
|---|---|---|
| Cuentas | Sober page title, invitation action, name/email search, role/state filters, complete account rows, visible result count. | Company, last access in Bogotá time; neutral mock fixtures; contextual account actions. |
| Roles | Five read-only system roles plus custom examples; selected role, name, tool-grouped checkboxes and custom-role save/delete. | Read-only explanation, minimum-permission validation, assigned-role refusal. |
| Login | Email, password, Enter. | Invitation-only access; administrator-issued password reset; generic error; destination completion copy. |
| Activation | Invited identity, new password twice, full notice, unchecked consent, disabled-until-consent Activate. | Eight-character rule; seven-day invitation; expired/used/replaced recovery. |
| Reset | New password twice, save and return to sign in. | Single-use 24-hour administrator-issued link; invalid-link recovery. |
| Mi cuenta | Administrator fixture identity/company/role, current password, new password twice, change action. | Sessions end on password change; example notice version/date. |
| Notice update | Full notice v1 in selected/browser language, unchecked consent, accept/continue, sign out. | Version/date storage; bracketed text awaiting legal review; other product routes absent. |

Scene selector: invitation form, management sheet, one-time link, account deletion and role deletion. Every scene is reachable directly for inspection as well as through its applicable product flow.

## 8. States and scope

| Preview state | Applicable scope / observable result |
|---|---|
| Normal | Editable working state; read-only system roles remain read-only. |
| Cargando | Account/role skeletons; form skeleton and disabled submission/fields; no duplicate action. |
| Vacío | Account list: no matching accounts, clear-filter recovery or invitation guidance. System roles are never an empty dataset. |
| Error | Account/role reads hide unconfirmed rows and provide retry. Login uses the uniform error with fifteen-minute wait. Other forms explain failure and preserve typed data. |
| Éxito | View-specific result: sign-in/activation destination, password sign-in recovery, accepted notice or saved management change. |
| Validación | Actionable error announcement; invalid password/name controls and required/permitted selection; custom-role zero-permission validation also works by submitting the form. |
| Sin permiso | Scoped refusal, no management data/actions, Mi cuenta recovery. This visual fixture does not grant server permission. |
| Enlace vencido o usado | Activation/reset form replaced by recovery text; no password submission. |
| Correo duplicado | Refusal explains how to manage the existing account; no new invitation. |
| Cuenta con trabajo | Deletion refusal names saved work, deactivation alternative and stable error code. |
| Último administrador | Deletion/deactivation/reassignment refusal. |
| Rol en uso | Assigned-role deletion refusal; system roles stay read-only. |

The global preview deliberately permits unrelated view/state combinations; their product scope is defined above. Hover, pressed, keyboard focus, disabled, unchecked/checked consent, one-time link and clipboard fallback are reachable through real controls. Offline and partial-read variants are represented by the recoverable error state: the design makes no unconfirmed “saved” claim or stale-count promise. Real network, session and race handling belong to the implementation tasks.

## 9. Responsive behavior

At **1101px and above**, one full-width register has four aligned columns; there is no sidebar or edition cell. The role sheet has a 240px selector and grouped permission editor. Search, role and state filters divide available desktop width in 2:1:1 flexible columns, with minimum widths 240/180/160px. Outer padding is 40px, paper padding 28px. Header contains Pictures/Sempertex, language selector and the signed-in account disclosure; ordinary 24px page title precedes the same horizontal account routes.

At **761–1100px**, outer padding is 28px, the register remains full-width, filters use two columns with full-width search, account actions move below the record, and permission groups become single-column.

At **360–760px**, outer/paper padding is 20px and panel corners stay 32px. Identity spans the record; role and status share the next line and the management action follows. Filters, role choices, permissions, identity and form fields stack. Routes wrap in flow. Dialogs keep 16px viewport margins, 24px padding and vertical scrolling. Register feedback retains the r12 phone alignment treatment: full paper width with 20px internal inset. Form feedback spans the phone paper with a 20px internal inset, keeping its text aligned to the field labels and using the available width. Header wraps with account role available inside its disclosure. Page title remains 24px; there is no hero or material card on any width.

Supported floor is 360px. No horizontal page scroll; ES/EN reflow. Login, activation, reset, Mi cuenta and notice use a centred panel capped at 676px (620px form plus two 28px paper insets). Their heading follows the same 676px outer axis. At narrower widths the panel takes available space and its form contracts without overflow. Desktop form feedback has the same centred 620px maximum width, including error/success states; on phones its band fills the paper and its text keeps the 20px field inset; expired-link and permission-refusal states inherit the same panel geometry. Accounts and roles retain full-width workspaces. Legal notices remain fully visible by vertical scrolling. Mockup controls remain outside product geometry.

## 10. Accessibility and motion targets

Targets are WCAG 2.2 AA for applicable interactions: text 4.5:1, meaningful control edges/focus 3:1, visible three-pixel focus ring with four-pixel offset, 44 px actions, programmatically named inputs/checks, labelled groups and announced errors/results. System-role checkbox state remains visually readable although disabled. Destructive effects are explained before confirmation; exact-email confirmation applies to account deletion.

Permission IDs are normalized into space-free identifiers so Base UI's generated `aria-labelledby` resolves each checkbox label. Search and forms retain focus during typing. Dialog/AlertDialog use the real installed primitives for focus containment, inert background and dismissal restoration. Screen-reader conformance is a target, not attested by browser measurements alone.

Motion vocabulary: 480 ms precise sheet registration, 55 ms row offsets, 180 ms control travel; natural 300/140 ms, subtle 160/100 ms. Paper, rows, rules, status feedback, skeleton scan and hover/press arrow movement remain distinct behaviors. Rail/foil animation is removed with its retired content. Remaining repeating loaders and all animations pause when the tab is hidden. No offscreen decorative animation remains. `useMotionProfile()` supplies the profile/reduced state. Reduced motion, Quieto and `?still=1` remove travel and repeating effects while retaining the same content and actions. Navigation/filter animation moves readable content rather than clipping it. No text opacity fade or flashing is used.

## 11. Observable acceptance and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| A-01 | 1101+ | accounts normal | Name/email/company, role, state, last access and Manage share each ruled record; counts come from the same rows. |
| A-02 | 360–760 | accounts normal | Identity spans the record; role/state and Manage reflow below without horizontal page scrolling. |
| A-03 | 360+ | login error | One generic message includes the fifteen-minute wait and reveals no account-existence/state distinction. |
| A-04 | 360+ | activation normal | Both password inputs and full notice precede consent; Activate is disabled until consent is checked. |
| A-05 | 360+ | link expired | Password entry is absent and asking the administrator for a new link is the visible recovery. |
| A-06 | 360+ | invitation | Name/email/optional company/one role precede generation; duplicate email is refused. |
| A-07 | 360+ | link receipt | Copy action, one-use/lifetime and older-link invalidation are visible; closing removes the receipt. |
| A-08 | 360+ | saved-work / last-admin | Refusal explains the invariant and destructive submission remains disabled. |
| A-09 | 360+ | account delete | A work-free account requires its exact email before Delete permanently is enabled. |
| A-10 | 360+ | role editor | Five system roles are read-only, grouped permission labels are accessible, custom roles require at least one permission. |
| A-11 | 360+ | notice update | Other product routes are absent; consent or sign out is reachable; placeholders remain explicit. |
| A-12 | 360+ | Mi cuenta | Identity matches the account menu; current password precedes new passwords and session-ending copy. |
| A-13 | 360+ | dark / light | Input edges, custom checkboxes, outlined actions and focus are visible on their actual surfaces. |
| A-14 | 360+ | reduced / expressive | Expressive registration is measurable; reduced/still has no running animation and preserves every action. |
| A-15 | 360+ | dialog open / dismissed | Tab remains in the real dialog; Escape on invitation restores the initiating action's focus after dismissal. |
| A-16 | 360+ | normal, either theme | Main paper and dialog have 32px computed corner radii; inner notice and feedback have 24px radii. |
| A-17 | 360+ | normal, either theme | Buttons, native selects, account disclosure and status chips have pill radii; text inputs have 18px radii and visible edges. |
| A-18 | 1101+ | accounts normal | Paper has 28px inner padding and account rows have 24px vertical padding; every row stays aligned to the shared register columns. |
| A-19 | 360+ | roles normal | Selected role has an 18px rounded soft surface, role choices are separated by 8px, and permission checkboxes retain distinct checked/unchecked states with 8px corners. |

| A-20 | 360+ | accounts normal | H1 is “Cuentas” at 24px; no slogan, edition counter, plan sidebar or material card is rendered. |
| A-21 | 1101+ | accounts normal | Workspace has one column; the register fills the space previously occupied by the annotation rail. |
| A-22 | 360+ | ES / EN | Initial language is ES; English UI labels appear only with EN selected; DialogClose is named “Cerrar” in ES. |
| A-23 | 360+ | both themes | Computed body font is Geist and colours resolve to Pictures' globals.css values, with texto-tenue control edges. |
| A-24 | 360+ | accounts / account / activation | Only neutral labelled fixtures are displayed; account-menu and Mi cuenta identities match. |

| A-25 | 761+ | login / activation / reset / Mi cuenta / notice, both themes | The workspace is at most 676px wide and has equal left/right viewport gutters; its fields are at most 620px wide and centred on that same axis; its footer is stacked on the panel axis. |
| A-26 | 761+ | form error / success / expired link | Feedback and recovery stay inside the centred form panel; no blank full-width right-hand sheet remains. |
| A-27 | 1101+ | accounts normal | Search/role/state filters fill the row in flexible 2:1:1 columns instead of a very wide search and two fixed narrow controls. |
| A-28 | 1101+ | roles normal | The role selector is 240px wide and the permission editor fills the remaining width with its existing two-column permission groups. |
| A-29 | 360–760 | all form views | The centred panel contracts to available width with 20px phone padding, without horizontal scrolling or hidden actions. |

Final r13 verification (final HTML SHA-256 `6fbc92b149739f55e4e467be53ec85385bd150a2524b35ea8ec8feb5e4895931`):

- Current offline toolchain: installed/built, **96/96 entries available**. Absolute-path `bitacora.py components mockup build` rebuilt the assigned r13 TSX into its assigned self-contained HTML: **678KB, 2150 source files**, exit 0. Installed real shadcn/Base UI components and local embedded production fonts; no package installation, asset fetch or fallback snippets.
- Absolute-path `contrast.py`: **158 pairs checked in light and dark, all pass**, exit 0.
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/audit_mockup.py <r13.html> --max-combos 476`: **476 renders / 476 planned combinations**, **12,598 text measurements / 1,396 focus stops**, exit 0, with the current kit-selected `/usr/bin/chromium`. Every view/state/theme combination plus every dialog in its normal state, at 390/1280px; no sampling.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Supplementary cached-Playwright checks: **494 assertions PASS**, including **112 responsive ES/EN cases** (seven views × two themes × two languages × 360/768/1024/1440px). Form and panel centring, 676px panel cap, actual Geist typography and absence of horizontal overflow were measured. All **18 JSON evidence selectors** match their intended rendered views. Consent gates activation; an expired link suppresses password entry; the invitation dialog opens and Escape closes it. Expressive loading exposes **eight running animations**, Quieto exposes **zero**, and OS reduced motion exposes **zero**. No page exceptions or HTTP(S) requests occurred. A source comparison confirms **all interaction logic remains byte-identical to r12** after excluding CSS, layout attributes and the revision label. The note has twelve sections and the JSON retains its exact three-key/eight-axis shape.

Final screenshots were inspected in memory using the audit's system Chromium: 1280/light login, 1280/dark accounts, 390/light login error and 390/dark roles. The final footer follows the form panel axis, filter widths are balanced, and phone error copy aligns with field labels. Earlier in-memory screenshots also covered dark activation and desktop roles. No screenshot files were written.

Audit history: the first r13 full sweep returned **FAIL — alignment 30**. The full-width footer did not follow the new centred form panel, and narrower phone error bands introduced a competing inner axis. The footer now stacks on the panel axis; phone feedback fills the paper while its copy keeps the field inset. The rebuilt final artifact passes the full audit above without changing any check or threshold. A cached-browser exploratory probe also reported a consent-label alignment heuristic reproduced unchanged in r12; the current kit/system-browser audit reports no such finding. The first supplementary interaction probe targeted Base UI's hidden native checkbox and timed out; using the visible accessible checkbox role corrected the probe, and the complete final supplement passes. Failed/incomplete probes are not counted as passing checks.

Production lint/types/tests/build, authenticated routing, backend permissions, secure token expiry, persistence and legal or full WCAG compliance are outside this static design verification. R12 evidence remains in its immutable note; owner selection and canonical approval remain pending.

## 12. Open questions, assumptions and impact

Q: Which legal entity, rights-contact email and policy URL replace the bracketed fields before real external activation? Owner: David with Sempertex legal; deferred legal fields remain unchanged in both approved notice-language texts.
Q: After changing a password in Mi cuenta, should this browser keep a newly issued session or return to sign-in? Owner: Planner/David; the inherited mockup asks for sign-in again, while the prior note identified a T2.2 acceptance mismatch. This content revision preserves the inherited flow pending reconciliation before canonical approval.

Confirmed behavior is retained: one role per account, five system roles including the three access plans, eight-character passwords, generic fifteen-minute lock guidance, seven-day invitations and 24-hour resets, single-use admin-generated links with no automatic email, mandatory notice reacceptance, saved-work/last-admin protections and at least one permission for custom roles. Removing the promotional plan panel does not remove required role/plan assignment controls or read-only system permission inspection. Mock data and operations are illustrative; no real account or session is changed. The initial ES planning selection is an inspection default, not a replacement for the product's browser-language notice requirement.

**Impact: breaking responsive-layout iteration r12 → r13** confined to SP-2; product meaning, navigation, content and motion remain compatible. Future T2.1 may copy only the later owner-selected/finalized artifact. T2.3 must adapt the centred login, activation, reset and mandatory-notice workspace; T2.4 must adapt Mi cuenta to the same form axis; T2.5 must adapt desktop filter proportions and the 240px role selector. T2.7 must re-render these views at phone, tablet and desktop against the owner-selected revision. No other subplan or approved contract is redirected. This note carries the draft impact record because separate changelog/plan writes are outside this delegation.

CONCERNS: sibling bundled HTMLs disagree with their written production-token contracts; current product globals/layout and the written sibling mappings take precedence. The password-completion question and deferred legal fields remain open. No production UI behavior, schema or plan is edited. No optional repository design preview is created. The real builder and cached browser are available; no fallback or external assets are required.

Only this direction's four r13 files and the mandatory delegation RESULT are written. R12 sources, shared behavior, canonical files, siblings, repositories and other bitácora files remain unchanged.
