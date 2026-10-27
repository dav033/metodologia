---
name: Pase al montaje
contract: cuentas-admin@v1
revision: r7
direction: b
status: draft
subplan: SP-2
requirements: [R1, R3, R16]
date: 2026-10-26
---

# Pase al montaje — spatial exploration B

Independent planning exploration, **unapproved**. This is an axis/evidence note, not the canonical twelve-section contract. The owner chooses a direction before a separate finalization writes the shared contract. No canonical contract, historical artifact, plan, production source or preview directory was edited.

## Concept and memorable move

Pictures is a place to assemble balloon decorations, not an abstract organization dashboard. Its access screen is a two-leaf pass on a mounting stage. A perforated seam joins a balloon rig to a usable form; the rig settles into its arch while the pass unfolds from its left hinge. Tiny registration corners establish the spatial frame. The pass never rotates while someone is entering data. The form, support copy and footer share the same left edge. Administration uses the same stage as an open ruled crew sheet, with a persistent bottom tool dock instead of a sidebar. The lower dock has text labels and standard buttons; no gesture or drag is required.

**Why this is not the default:** the credential-like split is derived from invitation and physical assembly, its art is an actual balloon arrangement rather than a decorative generic blob, navigation sits underneath the work, and movement has a hinged/settling grammar. The account roster remains an ordinary scan-friendly list. Boldness is concentrated in the access pass and stage rather than spreading into unfamiliar controls.

## Two thumbnails and selection

Created first, before the full TSX:

1. `cuentas-admin@v1.r7.dir-b.html.candidate-1.html` — hinged access pass with balloon rig and bottom tool dock. **Chosen.** It keeps a single stable form axis, carries the invitation metaphor and collapses cleanly into a small-screen stacked pass.
2. `cuentas-admin@v1.r7.dir-b.html.candidate-2.html` — a fan of physical crew passes. Not chosen: its tilted records add visual energy but make account scanning and long names harder, and are less suitable as a common frame for legal notices and permission editing.

Both standalone thumbnails use only local HTML/CSS and respond to system light/dark preference. The complete chosen artifact adds explicit theme, view, state, scene, motion and language controls.

## Eight axes

| Axis | Direction B |
|---|---|
| Concept | A personal access pass unfolds onto a balloon-decoration assembly stage. Perforation, a simple physical rig and registration corners connect identity to the product’s world. |
| Layout / composition | Centred 950px access pass with approximately 40:60 visual/form leaves; 1120px administration stage with ruled crew rows. Roles have a local role index and grouped permissions, not a page sidebar. The compact bottom dock remains visible during scrolling. |
| Navigation | Text-and-icon bottom dock for Cuentas, Roles and Mi cuenta, plus the named account menu. Account detail and destructive decisions use real modal primitives. No swipe, pointer-only hotspot or drag-only operation. |
| Typography / scale | System sans: 32px page titles, 28px on phones, weight 550 and -1.3px tracking; physical-stage statement 26/18px, weight 450. Inputs 15px, working text 14px, supporting text 13px, location/pass metadata 12px monospace. No network font. |
| Density / shape | 36×40px form padding, 32px sheet padding, 20px phone inner padding, 20px form group gaps and 22px row padding. One containing outline, 12px pass corners, circular initials and small balloon ovals. No nested cards or KPI tiles. |
| Components | Real installed shadcn/Base UI controls and Animate UI checkbox/dialog behavior, recomposed into custom pass, rig, ruled roster and permission bench. Native preview selectors and language/role/status selectors remain visible. |
| Colour logic | Both repositories’ Pictures palette mapped onto kit roles. Mauve is for primary actions and the balloon rig; neutral navigation and surfaces. Green means active/success; red means error/destructive. Contrast-corrected control edges remain visible in both themes. |
| Motion | Pass unfolds around a left hinge; three balloons settle on separate 780/920/1060ms tracks using cubic-bezier(.22,1.3,.36,1). The stage uses the selected Motion spring. Roster rows enter from 18px right with 70ms offsets. Dock hover rises 3px and press compresses 1px. Finite one-shot effects only; reduced motion, Quieto and `?still=1` show the final geometry immediately. |

Rendered selector evidence lives in the companion JSON. Motion evidence identifies elements actually observed animating, rather than merely containing animation-related class names.

## Shared identity and look ledger

Read the shared behavioral source, SPEC, PLAN.md, PLAN.json, both repositories’ `src/app/globals.css`, the existing login structure and Pictures’ shell/brand. The repositories share the same light palette: `--fondo #faf9fc`, `--superficie #ffffff`, `--texto #1c1425`, `--texto-suave #6b6178`, `--acento #6d3fe0`. The dark background/surface/text/accent are `#0b0c10`, `#16181f`, `#f4f5f7`, `#9479ff`.

There were **no sibling `*dir*.md` direction notes in the supplied requirement design tree** at inspection. The available SP-3 and SP-4 draft contracts served as the look ledger: SP-3 uses a workshop rail, viewport and inspector; SP-4 uses a desktop rail and project grid. This exploration retains their palette, voice and familiar control semantics, while using a hinged pass, open crew sheet and lower dock. It does not copy another direction’s composition or motion. The application mark retains the existing ring-and-dot geometry.

| Kit role | Project token / adaptation |
|---|---|
| background / card / foreground | `--fondo` / `--superficie` / `--texto`, copied per theme |
| primary / primary-foreground / primary-hover | `--acento` / `--sobre-acento` / `--acento-hover`, copied per theme |
| secondary / muted | `--superficie-2`, copied per theme |
| border | `--borde`, structural separators only |
| input | Proposed interactive edge alias of existing `--texto-tenue`: #766c85 light / #8a91a0 dark. Structural `--borde` is not strong enough for control outlines. |
| muted-foreground | `--texto-suave` #6b6178 light; proposed #a8afbc dark to preserve contrast over grouped surfaces |
| ring | `--acento`; solid 2px outline with 2px offset on keyboard focus |
| destructive / success / warning | Existing `--error`, `--exito`, `--aviso` and matching soft surfaces |

Real component inventory: `@/components/ui/button` (default, outline, ghost, link and destructive); `input` (email/password/search/text); `checkbox` (Animate UI on Base UI, checked/unchecked/disabled); `skeleton` (loading); `dropdown-menu` (account menu); `dialog` (account management and single-use link); `alert-dialog` (account/role deletion). Each comes from the installed manifest, not handwritten stand-ins. Layout, balloon illustration, roster and grouping are custom CSS/semantic markup. No package or asset was installed or fetched. The older request for fallback snippets is superseded by this exploration’s explicit real-library-first brief; the available real builder was used.

## Behavioral preservation and reachability

The shared behavioral file remains the source of truth. All data are illustrative and all `.example` links are inert mock links. Success announcements describe simulated UI transitions, not server writes or real authentication. API authorization, same-origin validation, link invalidation, hashing, anonymization and actual routing remain implementation and integration obligations of SP-1/SP-2.

| Native Vista | Goal and behavior shown |
|---|---|
| Iniciar sesión | Email/password; no registration. The single generic error covers unknown email, wrong password, deactivation and lock, always including the fifteen-minute wait. Success explains safe return/first allowed tool/My account fallback. Reset recovery asks the administrator for a link. |
| Activar invitación | Invited Camila Ortiz and email; two passwords, minimum eight characters; complete ES/EN notice v1 with bracketed legal fields; explicit unchecked acceptance gate. Used/expired link has one neutral message requesting a new link. Activation success represents an immediately signed-in Plan 2 account. |
| Restablecer contraseña | Administrator-generated link, two new-password fields, 24-hour single use, matching invalid-link message. Success returns to sign-in rather than claiming automatic reset authentication. |
| Nuevo aviso de datos | Full versioned notice and mandatory acceptance before continuation; sign-out remains available. No administration dock bypass. Success displays version/date acceptance. |
| Mi cuenta | Signed-in Ana Restrepo’s own profile, role, accepted notice and password change with current password. Success explains termination of other sessions and renewal of this browser’s session. |
| Cuentas | Four named fixtures, companies, roles/plans and active/invited/deactivated status. Search by name/email and status filter. Account menu has name/role, Mi cuenta and sign out. Management supports role change, deactivation/reactivation and regeneration of invitation/reset link. |
| Invitar persona | Name, email, optional company and one role/access plan. Plan 2 explains that Taller 3D is excluded; Plan 3 includes it. Duplicate email is a clear error. Generation shows a single-use link once, copy outcome and manual-copy recovery, expiry and invalidation of older unused same-kind links. No automatic email delivery is promised. |
| Roles de sistema | All five system roles and their permissions are read-only. Plans accumulate tools exactly as the accepted requirements specify. A custom “Diseño de eventos” role shows grouped permissions. No-account custom role deletion can be confirmed; the Cuenta con trabajo/protegido state supplies two assigned accounts and blocks deletion until reassignment. |
| Crear / editar rol | Editable name and permission checkboxes grouped by tool. Validation refuses a blank name or zero permissions; the validation state explicitly renders all unchecked. Save produces a local confirmation. |

Native **Estado** offers Normal, Cargando, Vacío, Error, Éxito, Validación, Enlace usado/vencido, Sin permiso, Sin conexión, Cuenta con trabajo. Native **Diálogo** offers Ninguno, Gestionar cuenta, Eliminar cuenta (also role deletion in role views) and Enlace único. States apply where relevant: empty account/role collections, invalid invitation/reset links, current form validation, authenticated permission denial and offline write recovery. Non-applicable state/view combinations retain the base view rather than inventing domain outcomes.

In **Gestionar cuenta**, the explicitly labelled Mockup fixture selector exposes Pedro (no work, can reactivate/delete), Camila (saved work, delete blocked) and Ana (last administrator, delete/deactivate/demotion blocked). Deletion requires exact email and explains retained anonymized AI usage. The protected state initializes Camila; opening Delete from that state exposes the refusal without a destructive commit. In role views the same destructive scene concerns a role, not an account.

Important implementation invariants: `ROL_SIN_PERMISOS`, `CUENTA_CON_TRABAJO` and `LINK_INVALIDO` are server outcomes with human recovery copy; no code string is the only user explanation. Account/role APIs enforce permissions independently of this rendering. A role update affects the next request, not just navigation visibility. Production initial administrator provisioning and real invitation handling are not simulated by a frontend bypass.

## Responsive and accessibility targets

- **360–767px:** 20px outside and inside pass padding, physical leaf becomes a compact top strip; fields stack; account records retain name/email, role, status and action; company moves out of the scan row. Role index and permission groups stack. Dock fits within the same 20px side margins. Full document scroll remains available; 110px bottom reservation clears the fixed dock.
- **768–1023px:** two-leaf pass, 24px world and sheet padding; table omits company, not access role/status; permission groups use one column.
- **1024px and above:** 950px access pass and 1120px administrative stage, five roster columns, grouped permissions in two columns. Fixed dock reserves 120px at the document bottom.
- Visible labels, real field semantics, 44px action targets, named checkboxes, status/error announcements, text ≥4.5:1 and control/focus edges ≥3:1 are targets checked by the rendered audit where covered. System roles have disabled checkboxes with explicit read-only copy. Dialogs make background inert and restore focus on dismissal. No real personal data or external resources are used.
- All effects are finite transform animations, not perpetual background work. A hidden tab pauses CSS choreography. Motion provider receives the real selected profile and reduced state; `prefers-reduced-motion`, Quieto and `?still=1` remove travel and keep every state available.

## Traceability and visual checks

SP-2 covers **R1, R3, R16**. This exploration may inform T2.1 (copy approved artifact), T2.3 (access/activation/reset/notice), T2.4 (account menu/My account), T2.5 (administration and roles), T2.7 (visual review), T2.8 (independent audit); T2.2 owns API behavior and T2.6 owns real cross-browser integration. **Compatibility: undetermined until owner direction selection; composition/navigation changes require adaptation of those UI tasks.** No plan consumer or approval state was changed.

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-AC-01 | 1024px+ | login/normal | Brand, pass and footer sit on deliberate common axes; form labels, fields, recovery and footer share one left edge. |
| B-AC-02 | 360–767px | all | No horizontal document scroll; the lower dock leaves the final control reachable above its reserved bottom space. |
| B-AC-03 | all | activar/normal | Activation remains disabled until the labelled notice checkbox is checked. |
| B-AC-04 | all | login/error | One generic message includes a fifteen-minute wait without revealing account existence or status. |
| B-AC-05 | all | activar or restablecer/enlace-invalido | One used/expired-link message asks for a new administrator link. |
| B-AC-06 | all | gestionar/protegido | Saved-work deletion is disabled and explains deactivation as recovery. |
| B-AC-07 | all | gestionar/Ana fixture | Last-administrator role, deactivation and deletion controls are disabled with a visible reason. |
| B-AC-08 | all | roles/normal | All five system-role permission sets are read-only; custom role is separately editable. |
| B-AC-09 | all | rol/validacion | All permission checkboxes are unchecked and the zero-permission explanation is visible. |
| B-AC-10 | all | roles/protegido | A selected custom role with assigned accounts cannot be deleted; reassignment is the next step. |
| B-AC-11 | all | enlace dialog | Link is labelled illustrative, expiry and one-time presentation are explicit, and copy failure offers manual recovery. |
| B-AC-12 | all | dark/all | Inputs, selects, unchecked checkboxes and keyboard focus have visible boundaries against their surfaces. |
| B-AC-13 | all | reduced / still | Stage, pass, balloons and roster are settled with no ongoing animations; all controls remain usable. |

Source snapshots read for this exploration:

| Input | SHA-256 |
|---|---|
| SPEC.md | `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4` |
| PLAN.md | `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3` |
| PLAN.json | `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8` |
| Shared r7 behavior | `c665ab01443531a74cf5f1dc1cb936ab9e2d70f650308d6842f2cd4dd8072a43` |

## Audit evidence

Offline real builder completed successfully (about 760KB, 2292 source files). The TSX is self-contained; it carries custom CSS in a raw string rendered by React. After building, that exact CSS is also copied into a static `<style data-direction="b">` in the same output HTML so the non-browser token checker evaluates the project overrides. Rebuilding must repeat that extraction; no extra CSS file is required or authorized.

Command pattern:

```sh
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r7.dir-b.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r7.dir-b.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r7.dir-b.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r7.dir-b.html --max-combos 300
```

Token contrast: `contrast: 158 pairs checked in light and dark, all pass`.

First complete rendered audit: 468 renders / 468 combinations planned, 9798 text measurements, 1563 focus stops; `RESULT: FAIL — contrast 1, alignment 1`. Fixed the dark offline Retry link (inherited destructive text now meets contrast) and the isolated centred sign-out action in notice acceptance (now a standard outlined secondary action). A preliminary earlier run was interrupted while refining the composition; no pass is claimed for it.

Final rendered audit: **468 renders (468 combinations planned), 9806 text measurements, 1554 focus stops**.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Visually inspected in-memory screenshots at 1280 and 390 in both themes; no screenshot files were created outside the allowed list. Interactive Playwright checks passed acceptance gating, uninterrupted password/search typing and retained focus, successful activation, saved-work and last-administrator deletion restrictions, Escape/focus return, zero-permission validation, English notice placeholders and `?still=1`. Additional checks passed deletion of an unassigned custom role (the index updates), blocked deletion of an assigned role, selector evidence across account/role/activation views, and no horizontal overflow at 390, 768 and 1280px; dock bottom measured 888/880/880px in a 900px viewport. No JavaScript errors or HTTP(S) requests were observed in that traversal. Live motion inspection saw the pass, three balloons and stage running at 180ms after mount. These checks establish prototype behavior, not production security or legal approval.

## Open questions

Q: Owner / Sempertex legal: what legal entity name, rights-contact email and policy URL should replace the accepted notice’s bracketed fields, and who will confirm legal review before real invitations?
Q: Owner: should “Pase al montaje” and its persistent lower dock be selected for finalization, or should another r7 direction define the final shared contract?

Confirmed rather than reopened: one role per account; plans are system roles; minimum eight-character passwords; seven-day invitations; 24-hour resets; link regeneration invalidates older unused links of the same kind; acceptance version/date persistence; saved-work deletion refusal; AI spend retention without personal data; system roles read-only. These behaviors are not design alternatives.
