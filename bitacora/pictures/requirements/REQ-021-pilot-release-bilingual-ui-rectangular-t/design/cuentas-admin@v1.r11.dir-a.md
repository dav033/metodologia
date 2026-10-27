---
name: Parte de acceso
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
revision: r11.dir-a
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
date: 2026-10-27
source_revision: r10.dir-a
feedback: "2026-10-27T08:01 direction=a: generous radii, softer surfaces and more air"
---

# Parte de acceso — direction A

## 1. Identity and traceability

**Single-direction iteration r11 of r10 A; draft awaiting owner selection.** This note is not the canonical twelve-section contract or an approved implementation input. The eventual `cuentas-admin@v1` contract still requires selection and finalization with the plan. No shared contract, plan, history or repository was edited.

Sources read: `SPEC.md` (`65b1e5ecc06f20d9`), `PLAN.md` (`cc7e53f2abf3c23c`), `PLAN.json` (`7a2c833a7e711508`) and the shared `cuentas-admin@v1.r11.behavior.md` (`c665ab01443531a7`). These hashes identify the source snapshot, not approval. SP-2 covers R1 invited accounts, R3 role management and R16 access plans. Its contracts consumed from SP-1 are `account-service@1`, `session-guard@1` and `permission-map@1`.

## 2. Purpose, concept and memorable move

**Concept: an event production call sheet.** The administrator answers “Who is on the team, which tools can they use, and what do I need to change?” Each ruled row keeps the person's name, email, company, assigned role, state, last access and management action together. The annotation rail makes the three cumulative plans understandable while work stays in the register. Names, companies, email addresses, dates and counts are illustrative mock data; `.example` domains are reserved examples.

**Memorable move: kinetic registration.** The page seats into its working position in several deliberate directions: paper down, records horizontally, the annotation rail from above, then a foil seam stamps into place. Status changes make a short registration stroke. The readable content stays present through these transforms. This derives from lining up a production sheet and checking a finished balloon installation; it does not imitate a physical access badge or a project folder.

## 3. Preserved composition and the look ledger

This revision starts from an exact copy of the r10 TSX and changes CSS only. Owner feedback (2026-10-27T08:01, direction=a) asks for much rounder cards, buttons, inputs, chips and panels, softer surfaces, more air and a lighter hierarchy while retaining A’s composition, navigation and motion. No new direction or thumbnails were created. The two historical thumbnails below belong to r10 and remain immutable. Both original visual thumbnails were written before the r10 TSX. They include responsive CSS, offline embedded display type and system light/dark variants; they are composition studies, not snippet fallbacks for the complete mockup.

- **Chosen: [candidate 1](cuentas-admin@v1.r10.dir-a.html.candidate-1.html)** — a broad running head, complete comparable account rows and a narrow plan annotation rail. It makes the administrator's repeated job visible and carries naturally into the role editor.
- [Candidate 2](cuentas-admin@v1.r10.dir-a.html.candidate-2.html) — a left dispatch spine and an oversized selected-person sheet. It over-emphasizes one person and repeats a side-navigation composition already represented in the look ledger.

The ledger includes SP-4 `proyectos@v1.r8.dir-a/b/c.md` and SP-3 `taller-esenciales@v1.r7.dir-c.md`. The archive's inline scene fold, the spatial frame, sample folders and the workshop's silicone slots remain distinct from this broad account register and permission sheet. Pictures' ring-and-dot mark, Sempertex product language, cumulative plans, semantic role names and clear working controls provide continuity. New exploration colours are proposals, subject to the owner's selection.

## 4. Eight axes, visual language and real components

| Axis | Present expression |
|---|---|
| Concept | An event production call sheet: people are registered against their exact tools, access state and next action. The ring-and-dot Pictures mark and foil seam connect the operational page to Sempertex installations. |
| Layout | Broad asymmetric running head (large condensed title left, live account count right), horizontal route rule, full-width ruled register with a narrow plan annotation rail; role list and permission sheet replace the register without a dashboard-card grid. Phone stacks the register then plan annotation. |
| Navigation | Neutral horizontal in-flow Cuentas / Roles y permisos / Mi cuenta route buttons, contextual per-person Manage dialogs and a named account disclosure; invitation-only entry has no open-registration route. Native preview selectors remain outside the product. |
| Typography | Embedded DejaVu Sans Condensed Bold as Dispatch, 38–68px display, 23–28px section/dialog titles; embedded Adwaita Sans as Work at 14–16px, embedded Adwaita Mono as Measure at 11–13px for access timestamps and edition details. English and Spanish reflow. |
| Density | Airier ruled account rows with 24px vertical padding, 28px desktop / 20px phone paper padding, 32px panel corners, 24px inset surfaces, 18px input/role-control corners, 8px checkbox corners and pill actions/selects/status chips; no KPI tiles. |
| Components | Real installed shadcn/Base UI Button, Input, Checkbox and Skeleton; Animate UI Dialog and AlertDialog with focus containment. Custom register rows, production running head, permission fieldsets and foil seam; rounded paper/plan panels, softly filled role selection and semantic pill status chips. Native role/state/language selects, no snippet fallback. |
| Colour | Proposed local exploration mapping of Pictures semantic roles: cold steel #e4ebf2, ink #112c48, cobalt #12489e; dark navy #0b1c2e with #a6caff action. Copper foil is confined to a Sempertex material sample; green/amber/red name status meaning. Softer neutral rules and a low-contrast plan surface lighten the hierarchy without changing the palette or accessible control edges. Neutral navigation uses text and a rule, not the accent. |
| Motion | Precise kinetic registration, cubic-bezier(.76,0,.24,1), expressive 480ms sheets with 55ms row offsets and 180ms controls; distinct paper registration, row registration, rule registration, rail counter-motion, 900ms foil stamp, 6s ambient foil registration, status stamping, skeleton scan and hover/press arrow shift. Subtle/natural shorten timings. Content remains visible during travel. Reduced/still removes all animation; hidden/offscreen suspension. |

Why this earns its structure: accounts are production information. A large title and live account total establish scope, while one ruled register carries every person's working facts. The expressive display type stays in titles; small labels and controls use Adwaita Sans. The foil sample has a stitched inflatable seam, restrained copper colouring and its own registration motion. It connects to the decorator's materials without competing with account data.

The r11 revision rechecked the same files in both `t12` and `asesor` read-only. Both repositories were inspected read-only for their `AGENTS.md`, `src/app/globals.css` and `src/components/admin/AdminTabs.tsx` patterns. The current product maps Spanish token names onto shadcn roles already. The exploration preserves those semantic responsibilities while proposing the following local values; it does not change production tokens:

| Pictures role | Kit role | Light / dark exploration mapping |
|---|---|---|
| `--fondo` | `--background` | `#e4ebf2` / `#0b1c2e` |
| `--superficie` | card / popover | `#f9fbff` / `#142b42` |
| `--texto` | foregrounds | `#112c48` / `#e6effa` |
| `--texto-suave` | muted foreground | `#405771` / `#b6c9df` |
| `--superficie-2` | secondary / muted | `#dce5ef` / `#203b54` |
| `--acento`, `--sobre-acento` | primary / primary foreground | `#12489e`, white / `#a6caff`, `#0b1c2e` |
| `--borde` | border | `#8292a4` / `#829cb5` |
| Accessible control edge | input | `#64788f` / `#96aec7` |
| `--exito`, `--aviso`, `--error` | success / warning / destructive | `#205d43`, `#755000`, `#a62434` / `#a1dfbe`, `#f2d591`, `#ffafb8` |
| Proposed material-only foil | `--foil`, `--foil-ground` | `#8c2b15`, `#f3c2ac` / `#ffb899`, `#51382c` |
| Proposed decorative separators | `--rule` | `#c4d0dd` / `#405a73`; decorative rules only, never required control boundaries |
| Proposed soft panel surface | `--surface-soft` | `#edf3fa` / `#193149`; annotation panel and selected-role background |

R11 shape tokens are local draft proposals shared across component classes: `--radius` / `--radius-field:18px`, `--radius-panel:32px`, `--radius-inset:24px`, `--radius-check:8px`, and `--radius-pill:999px`. They replace r10’s 2px corners and extend the production `--radius:0.8rem` convention; they do not edit production tokens. Paper, rail and dialogs use panel radii; material sample, legal notice, feedback and account dropdown use inset radii; input/role items/link receipt use field radii; buttons, native selects, account disclosure and status chips use pills. Text-only horizontal routes keep their existing underline model. Account rows retain shared columns and lighter rules with 24px vertical padding; role choices gain 8px separation and a soft selected surface. Meaningful input and focus edges keep the original accessible colours.

Installed manifest components: `shadcn:button` default/outline/destructive, `shadcn:input` text/email/password, `shadcn:checkbox` checked/unchecked/disabled, `shadcn:skeleton` loading, `shadcn:dialog` invitation/management/link and `shadcn:alert-dialog` permanent deletion. Their imports are `@/components/ui/{button,input,checkbox,skeleton,dialog,alert-dialog}`. Dialog, AlertDialog and Checkbox use the installed Animate UI/Base UI implementation. `mountMockup`/`useMockup` come from `@kit/mockup`; `useMotionProfile` comes from `@kit/motion`. The custom account register, plan rail, running head, permission fieldsets and seam are named custom compositions, not claimed as stock library components. No fallback snippets, package installation or fetched assets were used.

## 5. Navigation and interaction

The seven native preview views are Cuentas, Roles y permisos, Iniciar sesión, Activar invitación, Restablecer contraseña, Mi cuenta and Nuevo aviso obligatorio. The template's visible **Mockup** bar retains `view`, `state`, `scene`, `theme` and the expressive-default movement selector. The product has its own ES/EN native language selector, initialized from browser language.

Signed-in views have neutral in-flow account routes and an account disclosure naming David and his administrator role, with Mi cuenta and sign out. The phone summary shows the name; opening it reveals the role and the same actions. Mi cuenta's identity is the same David account, while the invitation fixture identifies Valentina. The mandatory-notice view withholds other product navigation and offers acceptance or sign out. Preview controls remain external to that product barrier.

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
| Cuentas | Scope title/live total, invitation action, name/email search, role/state filters, complete account rows, visible result count. | Company, last access in Bogotá time, cumulative plan rail; contextual account actions. |
| Roles | Five read-only system roles plus custom examples; selected role, name, tool-grouped checkboxes and custom-role save/delete. | Read-only explanation, minimum-permission validation, assigned-role refusal. |
| Login | Email, password, Enter. | Invitation-only access; administrator-issued password reset; generic error; destination completion copy. |
| Activation | Invited identity, new password twice, full notice, unchecked consent, disabled-until-consent Activate. | Eight-character rule; seven-day invitation; expired/used/replaced recovery. |
| Reset | New password twice, save and return to sign in. | Single-use 24-hour administrator-issued link; invalid-link recovery. |
| Mi cuenta | David's identity/company/administrator role, current password, new password twice, change action. | Sessions end on password change; example notice version/date. |
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

At **1101 px and above**, the main register has four aligned columns and a 280 px annotation rail; a broad title and 300 px edition cell share the running head. The roles sheet has a 200 px role selector and a grouped permission editor. Main outer padding is 40 px and paper padding 28 px. The 280px rail has 24px inner padding and a soft rounded surface.

At **761–1100 px**, outer padding becomes 28 px, the rail 220 px (24px inner padding), filters use two columns with full-width search, account actions move below each row, and permission groups become single-column.

At **760 px and below**, the paper and annotation rail stack with their 32px radii retained; outer/paper padding are both 20 px. Account identities span their row, role and pill status share a secondary row, and each pill management action follows. Phone rows retain the existing 20px vertical padding and 12px gaps. Filters, role selection, permissions, identity metadata and form fields stack. Navigation wraps in flow. Dialogs keep 24 px inner padding, 16 px viewport margins, and vertical scrolling when taller than the viewport. Feedback bands extend across the paper’s phone width while retaining 20px interior spacing, so their text stays on the same inner axis as the form instead of creating a second narrow column. Native selects remain native in both themes.

Supported floor: 360 px, with no horizontal page scrolling. Spanish and English labels reflow. All product sections and the footer share the outer axis; forms and notices share their paper's inner axis.

## 10. Accessibility and motion targets

Targets are WCAG 2.2 AA for applicable interactions: text 4.5:1, meaningful control edges/focus 3:1, visible three-pixel focus ring with four-pixel offset, 44 px actions, programmatically named inputs/checks, labelled groups and announced errors/results. System-role checkbox state remains visually readable although disabled. Destructive effects are explained before confirmation; exact-email confirmation applies to account deletion.

Permission IDs are normalized into space-free identifiers so Base UI's generated `aria-labelledby` resolves each checkbox label. Search and forms retain focus during typing. Dialog/AlertDialog use the real installed primitives for focus containment, inert background and dismissal restoration. Screen-reader conformance is a target, not attested by browser measurements alone.

Motion vocabulary: 480 ms precise sheet registration, 55 ms row offsets, 180 ms control travel; natural 300/140 ms, subtle 160/100 ms. Paper, rows, rules, rail, foil entrance, ambient foil, status feedback, skeleton scan and hover/press arrow movement are distinct behaviors. The ambient foil sequence is six seconds, transform-only, paused offscreen, on hover and when the tab is hidden. `useMotionProfile()` supplies the profile/reduced state. Reduced motion, Quieto and `?still=1` remove travel and repeating effects while retaining the same content and actions. Navigation/filter animation moves readable content rather than clipping it. No text opacity fade or flashing is used.

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
| A-16 | 360+ | normal, either theme | Main paper, annotation panel and dialog have 32px computed corner radii; inner notice, feedback and material sample have 24px radii. |
| A-17 | 360+ | normal, either theme | Buttons, native selects, account disclosure and status chips have pill radii; text inputs have 18px radii and visible edges. |
| A-18 | 1101+ | accounts normal | Paper has 28px inner padding and account rows have 24px vertical padding; every row stays aligned to the shared register columns. |
| A-19 | 360+ | roles normal | Selected role has an 18px rounded soft surface, role choices are separated by 8px, and permission checkboxes retain distinct checked/unchecked states with 8px corners. |

R11 evidence (this snapshot only; r10 verification remains in its immutable note): the current installed toolchain reports **installed/built, 96/96 entries available**. The current offline builder was run by absolute path on `cuentas-admin@v1.r11.dir-a.tsx` to produce `cuentas-admin@v1.r11.dir-a.html`: **4475 KB, 2150 bundled source files**, exit 0. Real installed shadcn/Base UI and Animate UI are retained; no fallback snippets, installation or fetched assets were used. Embedded local fonts remain offline.

`contrast.py`: **158 pairs checked in light and dark, all pass**, exit 0.

The final complete offline rendered audit passed **476/476 combinations, 19,738 text measurements, 1,395 focus stops**, exit 0, at 1280px and 390px across both themes, all seven views, twelve states and all five dialog scenes. It checks the settled reduced-motion rendering and expressive layout stability.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Audited HTML SHA-256: `03cc12f665c9e7740dffc150f20b0648bae496cbc3071e059d78899b8a9155dc`.

Audit history: the first r11 sweep failed with 98 distinct alignment findings, predominantly phone feedback introducing a narrower text axis. Full-width phone feedback bands restore the shared paper axis. A focused probe then exposed the inactive status chip’s inline formatting as a misleadingly centred line; block/fit-content chips retain left alignment. An intermediate full sweep was interrupted (exit 130) before the chip correction and is not counted as passing. Six focused mobile view/state probes then passed without contrast, non-text, alignment, padding or overflow findings before the final complete sweep above. No check or threshold was changed.

Supplemental browser coverage passed **84 ES/EN cases** (seven views × two themes × two languages × 360/768/1024px) with no horizontal page overflow. Every JSON evidence selector matched its intended rendered view. Computed radii were checked: paper/rail/dialog 32px, inputs 18px, buttons/selects/status 999px and material inset 24px. Search/no-results/clear, consent gating and activation, real dialog Escape dismissal and initiating-focus restoration passed. Early supplemental probes needed the correct language after a view remount and needed to wait for actual dialog unmount/focus restoration rather than a fixed 350ms pause; the final event-based assertions passed. No HTTP(S) requests or browser errors occurred in the focused interaction check.

Motion evidence is active: paper `register`, rows `row-register`, navigation `rule-register`, rail `rail-enter`, foil `foil-register`/`foil-drift`; buttons retain their 180ms transform/background/border transitions. Expressive entrance had **12 running animations**; `?still=1` had **zero**. Screenshots were inspected in memory at 1280/light accounts, 1280/dark roles, 390/dark accounts and 390/light activation. No screenshots were written. The TSX outside its CSS template remains byte-identical to r10, including routes, controls, data, state logic and mount options; keyframes/easings/durations are unchanged.

No production lint/types/build/test, API authorization, secure token expiry/invalidation, persistence, concurrency, automatic routing, legal approval, screen-reader session or cross-browser compliance is attested by this static design exploration.

## 12. Open questions, assumptions and impact

Q: Which legal entity, rights-contact email and policy URL should replace the bracketed fields before real external users activate? Decision owner: David with Sempertex legal. The approved draft notice wording is preserved; this question concerns only its unresolved placeholders.

Confirmed behavior is retained rather than reopened: one role per account; the five system roles including three cumulative plans; eight-character passwords; fifteen-minute lock guidance; seven-day invitation and 24-hour reset; single-use administrator-generated links; no automatic email; reacceptance on notice changes; saved-work/last-admin protection; custom roles need a permission.

Affected future consumers are SP-2 T2.1 (copy the later approved contract), T2.3 (login/activation/reset/notice), T2.4 (account menu/password change), T2.5 (accounts/invitation/actions/roles), T2.6 (integration), T2.7 (visual review) and T2.8 (audit). **This r10 → r11 change is a compatible visual iteration:** routes, content, data, behavior, responsive structure, focus and motion remain unchanged; radii, decorative rules, inset fills and spacing change. T2.3–T2.5 must apply the proposed shape/spacing tokens and T2.7 must re-render the selected revision. Canonical compatibility and implementation approval remain undetermined until direction selection and finalization. The existing Mi cuenta password-change completion asks the person to sign in again, while the current T2.2 acceptance calls for a new browser session automatically; that pre-existing behavior mismatch is outside this shape-only iteration and must be reconciled by the Planner/finalizer before canonical approval. This exploration redirects no consumers and grants no approval. Only this direction’s four r11 revision-specific files and the required delegation RESULT are written. The r10 sources, r11 shared behavior, canonical pair, other directions, plans and repositories remain unchanged.
