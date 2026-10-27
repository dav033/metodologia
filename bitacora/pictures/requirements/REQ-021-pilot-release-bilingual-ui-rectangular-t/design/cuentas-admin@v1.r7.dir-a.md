---
name: Registro de acceso
status: draft
kind: independent-direction-exploration
subplan: SP-2
candidate-contract: cuentas-admin@v1
revision: r7
stance: operational-editorial
owner: David
date: 2026-10-26
---

# Registro de acceso — direction A

This is an **unapproved exploration**, not the canonical UI/UX contract or an implementation input. No shared contract, plan, repository, history artifact or approval state was changed. It preserves the shared SP-2 behaviour (digest `abde9480c2f8d545`), covers R1/R3/R16, and explores the operational/editorial seed. Approval and direction selection remain with the owner.

## Concept and memorable move

Pictures gives each invited decorator a particular set of working tools. This direction treats access as a carefully maintained register: people, role, status and last access remain visible together; the editorial margin answers “Quién puede entrar.” The **registration stroke** sweeps into its resting position before the working title locks and the ledger rows settle in a measured sequence. It is a single quiet piece of theatrical emphasis around everyday administration.

The margin is not a full-height application sidebar. It is part of the page's typographic composition, reflows above the work on phones and supplies a common baseline for the account form, consent text and footer. The larger margin heading and smaller task heading deliberately carry different jobs: orientation and action.

## Two thumbnails and selection

- **Chosen: candidate 1**, `cuentas-admin@v1.r7.dir-a.html.candidate-1.html`: editorial margin, short three-entry navigation and an adjacent ruled account register.
- Candidate 2, `cuentas-admin@v1.r7.dir-a.html.candidate-2.html`: full-width register below a large title and summary strip. Retained as an alternative, but the totals dominate a task whose purpose is identifying and changing a person's access.

Both are small visual HTML compositions, with inline assets, light/dark theme switch and phone reflow. They were created before the TSX/full mockup. The full design refines candidate 1 rather than copying a previous draft.

## Why this is not the default

There is no dashboard card grid, icon rail, ornamental KPI row, full-height coloured sidebar or centred authentication card. The title lives in an asymmetric margin; named tools and people occupy the working rail. Authentication uses exactly the same editorial alignment, so its supporting footer shares the form's x coordinate. Destructive actions require a separate confirmation layer. Colour stays off the neutral navigation.

The look-ledger search found **no sibling direction notes** in this requirement at exploration time. The existing SP-3 `taller-esenciales@v1.md` and SP-4 `proyectos@v1.md` drafts were read only for shared identity: Pictures palette, system-sans fallback, direct Spanish copy, and shared account-menu ownership. This direction uses neither the workshop's inspector/viewport composition nor a project browser/card grid. No claim is made that other concurrently produced directions have already passed comparison.

## Eight axes

| Axis | Implemented expression |
|---|---|
| Concept | An operational register for the people who imagine, calculate and build decorations: who can enter, and which tools they can use. |
| Layout | An asymmetric 232px editorial margin plus a fluid working ledger, separated by 48px; account forms and their footers share the working-column left edge. The margin becomes a compact heading above content below 768px. |
| Navigation | Three text entries in the editorial margin (Cuentas, Roles y permisos, Mi cuenta), with a neutral active baseline; a named account menu in the masthead. Phone navigation becomes one in-flow horizontal row, not a drawer. |
| Typography | Arial/system sans, 34px compact two-line margin heading against a 24px task title; 13px ledger records and 12px metadata. Monospace is reserved for access times, notice versions and links. |
| Density | Six accounts across six table columns on desktop; flat ruled records instead of cards. Phone records retain company, role, state and last access in a labelled hierarchy. Forms use 22px group gaps and 44px inputs. |
| Components | Real shadcn/Base UI buttons and inputs, Animate UI-backed checkboxes, dialogs, alert dialogs and account dropdown; a custom semantic HTML ledger and typographic rail. Grouped permission checkboxes act as a tool-access receipt. |
| Colour | Existing Pictures light lavender-neutral canvas and near-black dark canvas, mapped to kit roles. Purple identifies the primary action and registration rule; green/amber communicate account state. Readable project text tokens also supply control edges. |
| Motion | Precise registration rather than elastic bounce: a left-origin rule sweep, 12px pane cut, 5px title lock and 7px row settling with 35ms successive delays, cubic-bezier(.76,0,.24,1). Profile-scaled entrance ~340ms expressive / 178ms natural / 113ms subtle; repeat hover/press stays 150–160ms. Reduced motion and still=1 show the same final content immediately. |

Selector evidence is in `cuentas-admin@v1.r7.dir-a.json`; all four evidence categories identify rendered product elements. Motion selectors have actual CSS keyframes or hover/press transitions, not just names. There is no looping decorative animation. Finite entrances pause in a hidden tab; reduced-motion and `?still=1` remove travel and transitions while keeping content and feedback.

## Design-system mapping and real components

Read-only sources: `src/app/globals.css` and login components in both registered worktrees (`t12` and `asesor`); the installed real manifest/runtime/component exports; SPEC, PLAN and shared behaviour. Production Geist falls back to the offline system Arial/Helvetica/sans-serif stack; no font or asset was fetched.

| Pictures source | Kit role | Light / dark |
|---|---|---|
| `--fondo` | `--background`, `--sidebar` | `#faf9fc` / `#0b0c10` |
| `--superficie` | `--card`, `--popover` | `#ffffff` / `#16181f` |
| `--texto` | foreground roles | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | `--muted-foreground` | `#6b6178` / `#9aa1ad` |
| `--superficie-2` | `--secondary`, `--muted`, `--accent` | `#efe9f8` / `#242733` |
| `--borde` | decorative `--border` | `#e3daef` / `#383c48` |
| `--texto-tenue` light / `--texto-suave` dark | interactive `--input` | `#766c85` / `#9aa1ad` |
| `--acento`, `--sobre-acento` | `--primary`, `--primary-foreground`, `--ring` | `#6d3fe0`, white / `#9479ff`, `#120b24` |
| `--acento-hover` | `--primary-hover` | `#5530b8` / `#a58dff` |
| `--error`, `--exito`, `--aviso` | destructive, success, warning | source theme values |

The readable edge mapping is deliberate: source decorative borders do not identify input boundaries sufficiently. No production token was edited. Slightly darker light destructive-hover is a local proposed interaction value. Unused chart tokens retain kit defaults; no chart is drawn.

| Component provenance | Variant and purpose |
|---|---|
| `shadcn:button` — `@/components/ui/button` | primary, bordered secondary, text action and solid destructive; hover, focus, disabled |
| `shadcn:input` — `@/components/ui/input` | named email/password/text fields, validation, disabled |
| `shadcn:checkbox` — `@/components/ui/checkbox` | Animate UI/Base UI; explicit notice consent and grouped tool permissions; checked, unchecked, read-only |
| `shadcn:dialog` — `@/components/ui/dialog` | Animate UI/Base UI invitation, account editing and one-time links |
| `shadcn:alert-dialog` — `@/components/ui/alert-dialog` | separate deletion/deactivation confirmations |
| `shadcn:dropdown-menu` — `@/components/ui/dropdown-menu` | named account menu, Mi cuenta and Cerrar sesión |
| `shadcn:skeleton` — `@/components/ui/skeleton` | four stable loading bars, no spinning page replacement |
| Native HTML/custom composition | semantic account table, fieldset/legend permission groups, editorial rail, status rules, feedback and product selects |
| `@kit/mockup`, `@kit/motion`, `motion/react` | native planning selectors; profile/reduced-motion state; mounted product |

The real builder was available and used successfully. No fallback HTML kit, package installation, external font, remote image or runtime network request was used in the full mockup. The built HTML bundles the installed libraries; it retains the visible “Mockup” label and `view`, `state`, `scene`, `theme`, `motion` native selectors. The additional product locale selector explicitly controls the notice, whose full approved ES/EN wording is reproduced verbatim from SPEC. Whole-interface translation remains the plan's later language work.

## Behaviour preserved and reachable views

| View / scene | Observable behaviour retained | Source / consumer |
|---|---|---|
| Iniciar sesión | Email/password; one indistinguishable failure message with fifteen-minute wait; invitation/reset requested from administrator; no open registration | R1 / T2.3 |
| Activar invitación | Invited name/email, two passwords minimum eight characters, full versioned notice in browser language, explicit checkbox gates activation; signed-in landing is first allowed tool | R1 / T2.3 |
| Restablecer contraseña | Two matching new passwords; used/expired links use the same recovery as invitations; return to sign-in after reset | R1 / T2.3 |
| Aceptar aviso | Updated version blocks other pages; explicit new consent; sign-out alternative | R1 / T2.3 |
| Mi cuenta / menu | Name, email, role, company and accepted version/date; current password required to change it; other sessions end and this browser is renewed; sign out in named menu | R1 / T2.4 |
| Cuentas | Six illustrative people, name/email/company/role/state/last access; search and two filters; accessible person-specific Gestionar action | R1, R16 / T2.5 |
| Invitar persona / link | Name/email/optional company/one role; duplicate-email refusal; copy-once link, no automatic email; seven-day validity | R1, R16 / T2.5 |
| Gestionar cuenta | Role/plan change; deactivate/reactivate; reset-link generation; new invitation link for invited account; no edit of the user's existing password | R1, R16 / T2.5 |
| New invitation/reset link | Confirmation explains invalidation of every older unused link of the same kind; link shown once; reset twenty-four hours | R1 / T2.5 |
| Eliminar cuenta | Exact-email confirmation for account without work; saved-work and last-admin refusal; IA spend retained anonymized | R1 / T2.5 |
| Roles / Editor de rol | Five system roles read-only (3/5/6/9/12 permissions); custom role grouped by tool; no-permission refusal `ROL_SIN_PERMISOS`; role with accounts cannot be deleted | R3, R16 / T2.5 |

Permission keys are the twelve keys in PLAN T1.2: `chat.usar`, `contador.usar`, `catalogo.ver`, `costos.usar`, `decoraciones.explorar`, `taller.usar`, `proyectos.ver_todos`, `gasto.ver`, `internas.usar`, `cuentas.administrar`, `roles.administrar`, `textos.corregir`. The three external plans are system roles, not a second independent entitlement field. Plan 2 explicitly explains that it lacks Taller 3D. No extra permission, registration mechanism, email service or real account was added.

The preview is a **static fixture simulator**: server redirects, session revocation, API 403/same-origin validation, actual token invalidation, anonymization and clipboard delivery are not executed. Link copy explicitly announces simulation. External tool destinations remain outside SP-2; no tool page is fabricated. These behavioural obligations remain in the shared source for the final contract and implementation. Do not treat fixture interactions as backend test evidence.

## States and responsive rules

All twelve states are visible in the native Estado selector: Normal, Cargando, Vacío, Error, Éxito, Validación, Sin permiso, Sin conexión, Enlace usado o vencido, Cuenta con trabajo, Último administrador, Rol con cuentas. Every dialog scene is separately selectable. Loading shows skeleton content; success/error have announced feedback; offline disables mutation and offers retry; validation identifies fields or permission group. Empty account results retain filters; empty roles retain all five system roles and explain the absence of custom roles. Password forms use blank inputs for the empty fixture.

Link expiration applies to activation/reset. Saved-work and last-admin examples belong to account administration; role-in-use belongs to role administration. These specialised states do not invent corresponding failures on unrelated screens; the toolbar permits independent inspection axes. The account menu belongs to signed-in screens. Offline, loading and no-consent provide explicit disabled-control examples. A full production stale-data or retry/revocation model is not claimed by this static exploration.

- **1024px and up:** 232px editorial margin, 48px gap, 40px outer padding, six-column ledger. At 1440px the rail gap becomes 64px within a 1320px maximum container.
- **768–1023px:** 190px margin, 28px gap, 24px outer padding. Search spans the first filter row; company moves out of the desktop ledger's visible columns at this intermediate width.
- **360–767px:** 20px page padding; heading and three-entry navigation flow above work. The table becomes ruled stacked records, retaining company, role, state and last access. Form fields/permission groups stack. Auth form and footer keep the same left edge. Dialogs keep 20px outer gutters and 22px inner padding, using 14px internal gaps; modal content may scroll at shorter heights.

Targets: WCAG 2.2 AA text contrast, 3:1 interactive boundaries and focus, semantic labels and tables/fieldsets, visible keyboard focus, modal background inertness and focus restoration. Inputs are 44px high; buttons are at least 42px high with sufficient separation. System-role permission checkboxes remain visibly marked even when disabled. Full conformance, screen-reader verification, zoom and production-browser coverage require implementation review; this exploration does not certify them.

## Honest audit evidence

The first full audit measured 640 renders, 17,116 text samples and 1,762 focus stops. It reported `RESULT: FAIL — alignment 2, padding 32`: the narrow “Volver a roles” action had an isolated centred line, and long phone dialogs exhausted their bottom padding. Both were corrected: the return action aligns left, invitation spacing is compacted, and account management removes duplicated identity fields/extra footer in favour of one action row. A focused rerender at 390×900 then measured no alignment, padding or overflow finding; invitation/account dialogs fit their contents (669px/683px).

The latest offline build reports 757 KB, 2,292 source files. Token check: `contrast: 158 pairs checked in light and dark, all pass`.

Final full audit, after the corrections (exit 0):

```text
audit: cuentas-admin@v1.r7.dir-a.html — 640 renders (640 combinations planned), 17008 text measurements, 1771 focus stops
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

Command: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <assigned-html> --max-combos 400`. Every planned combination was rendered at 1280px and 390px in both themes; the audit also checked expressive-load layout shift and reduced-motion settlement. No sampling warning or capped focus walk was reported.

Focused Playwright checks subsequently passed: accessibly named consent checkbox gates activation; identical invalid-link recovery; search/filter count consistency; five read-only system-role permission counts (3/5/6/9/12); exact-email deletion gate; invitation cancellation restores its trigger's focus; no horizontal page overflow at 360/390/768/1024/1280px in both themes; actual running ledger animation; `still=1` removes running animations; zero page errors and zero HTTP requests. An initial smoke targeted Base UI's hidden submission input by id and timed out; rerunning against the accessible checkbox role passed without changing the product artifact.

The comparison tool's own `measure([this_direction])` confirmed all 17 selector claims (`evidence_ok: true`), including actual motion. Pairwise cross-direction comparison was not run: only this assigned direction was measured.

Screenshots were inspected in memory at 1280px and 390px in both themes: account ledger, activation/notice, login, grouped role permissions and invitation modal. No screenshot files were written outside the assigned paths. The focused checks and final audit counts above apply to the final built HTML.

## Impact, questions and provenance

Exploration only; canonical `cuentas-admin@v1.md` and `.html` remain untouched. If selected, the finalizer must produce the twelve-section draft contract and account for the changed hierarchy/navigation/responsive structure. That would be **breaking relative to an implementation of the earlier draft**, despite preserved product behaviour. Relevant consumers are SP-2 T2.1 (copy), T2.3 (auth/notice), T2.4 (account/menu), T2.5 (admin), T2.6 (integration) and T2.7 (visual acceptance); T2.8 owns independent acceptance. No downstream subplan is automatically required to adopt an unapproved exploration.

Q: Owner/Sempertex legal — What are the final legal entity name, privacy-policy URL and rights-contact email, and has Sempertex legal reviewed the notice before real users are invited?

Direction choice remains with the owner in the comparison flow; no approval is requested or granted by this artifact.

| Read input | SHA-256 |
|---|---|
| SPEC.md | `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4` |
| PLAN.md | `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3` |
| PLAN.json | `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8` |
| design/cuentas-admin@v1.r7.behavior.md | `c665ab01443531a74cf5f1dc1cb936ab9e2d70f650308d6842f2cd4dd8072a43` |

Final HTML SHA-256: `b75d76d3fc1749e933b2cbe580b536fd86e35f6af62894c6f72f8181cca4ac8b`.
