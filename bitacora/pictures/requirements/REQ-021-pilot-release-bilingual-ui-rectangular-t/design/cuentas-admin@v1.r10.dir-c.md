---
name: Nudos — acceso en tensión
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
subplan: SP-2
requirements: [R1, R3, R16]
revision: r10.dir-c
chosen_thumbnail: cuentas-admin@v1.r10.dir-c.html.candidate-1.html
---

# Nudos — direction C

Unapproved tactile/playful exploration. This is an axis note, not the canonical twelve-section contract. No plan, shared contract, production source, history or approval state is changed. The owner chooses a direction; a separate finalizer writes the canonical contract.

## Concept and memorable move

A balloon decorator joins soft material at a firm knot. Here the account is a long **tensioned latex band**, and the role is the connection that determines what tools it reaches. The account list is a continuous run of readable bands with yellow valve anchors, rather than a dashboard of identical cards. The sign-in form uses the same stretched silhouette. The large local rounded face gives the work screen its inflatable character without turning form labels into display lettering.

The memorable move is a band stretching into place, the little valve twisting, and the selected navigation peg seating at an angle. Presses compress the material; errors release sideways pressure; success lands like a seal. A decorative latex loop can be dragged with the installed spring or moved using two equivalent labelled buttons. Moving it changes no account or permission. All account operations remain explicit text actions; no security-sensitive operation depends on a gesture.

## Two thumbnails, drawn first

1. **Chosen:** `cuentas-admin@v1.r10.dir-c.html.candidate-1.html`, tension rig with a left identity and material sample, right aligned sign-in band, and linear account band. The rectangular working field accommodates email addresses and validation while the shaped outer edge supplies the material identity.
2. `cuentas-admin@v1.r10.dir-c.html.candidate-2.html`, a constellation of inflated person pods around a central invitation action. It has a stronger playful silhouette but makes email, role, last access and safe account actions harder to compare. Kept as a visual sketch, not expanded.

Both thumbnails have inline CSS, a theme switch and phone reflow. They are visual sketches, not claims to be shadcn implementations. The full mockup uses the actual installed libraries and offline builder.

## Why this is not the default

The ownable material language is not a purple SaaS palette or a carousel of rounded cards. Yellow is a physical anchor, petrol is actionable, and a pale blue ground ties the working scene to the latex sample. The heading's inflated roundness, asymmetric band corners and small attachment valves belong together. The full-width account bands preserve practical scanning rather than making a decorative bubble the navigation target. There are no invented statistics or decorative charts.

## Look ledger and shared identity

Read the sibling `proyectos@v1.r8.dir-a/b/c.md` notes: editorial collection, stage/ribbon and material archive. Their notes also document the Taller cutting bench and accounts permission-pass explorations. This direction does not repeat the archive's folder tabs, the stage's thumbnail ribbon, the cutting bench's ruler or the perforated permission pass. It uses a tensioned band, a latex knot and seated navigation pegs. Pictures/Sempertex naming, linked-circle mark, domain vocabulary, readable form controls and explicit account protections remain shared. New colour and type values below are exploratory proposals responding to the owner's latest feedback, not edits to project tokens.

## Eight axes

| Axis | Observable proposal | Evidence |
|---|---|---|
| concept | Nudos: latex bands link people to the tools they may use; the soft valve is the shared product-world signature. | `.latex-loop`, `.person-band` |
| layout | Asymmetric tension rig: sticky 38% identity rail and 62% continuous working column. Account rows stretch between two rounded anchors; phone stacks identity, navigation and rows. | `.workbench`, `.rubber-band`, `.person-band` |
| navigation | Left peg-shaped spool buttons for Personas, Roles and Mi cuenta; selected peg tilts. Account menu stays in the masthead; form and destructive actions use modal confirmations. | `.spool-nav`, `.user-menu` |
| typography | Embedded Rounded Mplus 1c ExtraBold, 43–72px tightly set display; embedded Adwaita Sans for 13–17px controls and data. Rounded letterforms echo inflated latex without a geometric SaaS grotesk. | `.big-title`, `.person-name` |
| density | Generous 38px form inset, 22px people-band inset and 17px row gaps. Long low bands expose all six account facts; no KPI or equal-card dashboard. | `.rubber-band`, `.account-stack` |
| components | Real shadcn Button, Input and Skeleton; Animate UI checkbox and Base UI modal/alert-dialog primitives. Custom latex loop SVG, compressed action surfaces, band-shaped account rows and grouped permission selector. | `[data-slot=button]`, `[data-slot=checkbox]`, `.dialog-box` |
| colour | Proposal: pale pool blue #dfeded and deep petrol #075e60, with latex yellow #f7ce45 for material anchors only. Dark: #10282b/#193b3e with mint #8ce0d5 controls. Text #123b3f or #f0f9f7; no purple, cream/terracotta or shared default accent. | `:root`, `html[data-theme=dark]`, `.initial` |
| motion | Elastic tension grammar, cubic-bezier(.22,1.35,.55,1), expressive 680ms composition and 190ms controls: stretched-band entry, knot torsion, display compression, peg seating, plug engagement, error pressure release, success seal press, empty rocking, hover lift/press squash and profile-driven spring dragging. Natural 440/160ms; subtle 240/120ms. Reduced motion and still=1 settle immediately. | `.rubber-band`, `.latex-loop`, `.big-title`, `.press` |

## Existing design system and actual libraries

Read-only inspection covered both workspace repositories' `AGENTS.md` and `src/app/globals.css`, their semantic shadcn aliases and the current SPEC/PLAN/SP-2 behavioural source. The source plan defines twelve permissions and five fixed roles; system roles are Plan 1, Plan 2, Plan 3, Empleado interno and Administrador. The initial SPEC's three actor categories are not three editable system roles.

| Existing project token | Kit role | Exploratory light / dark values |
|---|---|---|
| `--fondo` | `--background` | `#dfeded` / `#10282b` |
| `--superficie` | `--card`, `--popover` | `#ffffff` / `#193b3e` |
| `--texto` | `--foreground` and surface foregrounds | `#123b3f` / `#f0f9f7` |
| `--texto-suave` | `--muted-foreground` | `#36595d` / `#bad3d1` |
| `--superficie-2` | `--secondary`, `--muted`, `--accent` | `#d2e7e6` / `#21474a` |
| `--acento` | `--primary`, `--ring` | `#075e60` / `#8ce0d5` |
| `--sobre-acento` | `--primary-foreground` | `#ffffff` / `#10282b` |
| `--borde` | `--border` | `#729496` in both themes |
| strong control edge role | `--input` | `#46787a` / `#92b3b3` |
| `--error`, `--exito`, `--aviso` | destructive, success, warning roles | theme-specific text/fill pairs defined in TSX |
| `--ease-rebote` | proposed tension easing `--snap` | `cubic-bezier(.22,1.35,.55,1)` |
| new local material role | `--latex` with `--ink` | `#f7ce45` with `#123b3f` in both themes |

This table maps the existing semantic responsibilities; it proposes new visual values only for this exploration. It does not assert these colours are already present in Pictures. If chosen, the finalizer must make the theme proposal explicit in the canonical contract. Rounded Mplus 1c ExtraBold and Adwaita Sans are installed local fonts, subset to Latin and embedded as data URIs in memory, with no new font file, package installation or network request. Existing production typography remains unchanged.

Actual components: `shadcn:button default/outline/disabled` from `@/components/ui/button`; `shadcn:input default/invalid/disabled` from `@/components/ui/input`; `shadcn:skeleton loading` from `@/components/ui/skeleton`; `animate-ui:checkbox checked/unchecked/disabled` through `@/components/ui/checkbox`; installed `@animate-ui/react/primitives/base-ui/dialog` and `alert-dialog` for modal focus/inertness and destructive confirmation. Direct primitives supply profile-aware entry **and exit** transitions. `motion/react` and `@kit/motion` provide the voluntary drag spring. Planning shell: `mountMockup` / `useMockup` from `@kit/mockup`. Native selects are deliberately retained. Custom components are the SVG knot, band wrappers, grouped permission selector and spool navigation. No fallback HTML library was used for the full mockup.

## Behaviour retained and simulation limits

Sources: `cuentas-admin@v1.r10.behavior.md` digest `abde9480c2f8d545`, current SPEC, PLAN and PLAN.json. This fresh composition preserves the behavioural requirement; it does not copy any previous visual draft.

| Native Vista | User goal and key states |
|---|---|
| `login` | Email/password sign-in. All credential, unknown-email, disabled and locked failures share one error including the fifteen-minute wait. No open registration or self-service email sending is invented. The local success fixture shows Plan 2 destinations and the person’s account menu; real requested-page and first-permitted-area routing belongs to implementation. |
| `activar` | Invited name, email and Plan 2; matching 8–200-character passwords; versioned notice and unchecked acceptance. Activation remains disabled until acceptance. The used/expired state asks for a new administrator link. |
| `restablecer` | Administrator-issued single-use link, two matching new passwords, 24-hour validity and a clear session-revocation consequence. Invalid links share the same explanation. |
| `aviso` | Versioned ES/EN notice with visibly bracketed legal-review placeholders. The account menu is disabled until acceptance; no other destination appears before acceptance. Signing out remains possible. Acceptance exposes the version/date acknowledgement and a continuation action. |
| `cuenta` | Person name, email, role, accepted notice version/date and password change requiring the current password. Success explains other-session revocation and browser-session renewal. |
| `cuentas` | Five fictional people with name, email, company, role, state and last access; real local search and role/state filters. Invitation asks name/email/optional company/role, refuses duplicates, and displays one fictional single-use link with copy control. Account actions show role change, deactivation/reactivation, reset, invitation renewal and guarded deletion. |
| `roles` | Five immutable system roles and one sample custom role. Read-only permissions or editable name/checkboxes. Tool-group select exposes the twelve permissions in four groups without a long mobile modal. Selections persist when changing groups. No-permission save is refused with `ROL_SIN_PERMISOS`; deletion of the assigned sample role is blocked. |
| `sinacceso` | Written permission denial, administrator guidance, Mi cuenta and sign-out. This does not claim to enforce real API permissions. |

The global state selector exposes normal, structural loading, empty, error, success, validation, offline, permission-denied and used/expired link. Empty applies to account search and custom roles, used/expired to token forms, and permission denial to signed-in views; unrelated states retain the normal fixture. There is no stale remote-data fixture: all records are local demonstration data. Offline shows a written warning and retry; mutation entry points are disabled. Loading substitutes structural Skeleton content with a written live status. Every dialog is also independently reachable through the native Diálogo selector: invitation, one-time link, account management, deactivate/reactivate, account deletion, role editor, assigned-role deletion and account menu.

Person fixtures: Camila (saved work), Julián (invited, no work), Lucía (staff, saved work), Tomás (inactive, no work), Ana (last active administrator). Deletion asks for the exact email and explains irreversible personal-data removal with anonymised AI spend retained. Saved work and last-administrator protections are visible before an action can proceed. Last administrator also cannot lose their role or be deactivated. A new invitation/reset link states that older unused links of the same kind become invalid. Invitations last seven days; reset links last twenty-four hours.

The mockup calls no account API and creates no real link or authenticated session. Sign-in success is a bounded Plan 2 destination demonstration, not working navigation to the production tools. Account edits and invitation creation operate on local fixture state until a view/state change; the role editor demonstrates selection, validation and success feedback but is not a persistent role store. Native view/state switches deliberately remount fixtures. Direct scene selection can exhibit a dialog on any view for review; it grants no real permission. Clipboard fallback asks for manual selection if browser permission prevents copying. Link text is clearly fictitious and is shown as text, not an external navigation link.

## Responsive, accessibility and motion targets

- 360–767px: one column, 20px outer gutter, 22px form inset, 22px modal inset, full-width account menu, no decorative knot, wrapping account bands with a labelled action below the data. The control navigation stays inline and wraps; it is not hidden in an unlabeled icon menu.
- 768–1023px: 270px identity rail and flexible content, 24px outer gutter, search above two filters; people actions below the name block when needed.
- 1024–1599px: 0.72/1.28 two-column rig, 40px gutter and 54px gap; 38px form inset and aligned supporting footer. At 1600px+ the rig stays capped at 1280px and its gap grows to 85px.
- Native controls, text labels, live success/error messages, 46–48px primary targets, visible 3px focus outlines and established modal focus/inertness. Destructive operations use the real AlertDialog primitive. Text and control edges are checked in both themes. WCAG 2.2 AA is a target, not a certification from an automated audit.
- Expressive motion is the default. Content never fades through unreadable text, and transforms do not change surrounding layout. Eight authored finite keyframes, repeated-control hover/press/focus feedback and a Motion spring distinguish the tension grammar. CSS timelines pause in hidden tabs; there is no decorative autonomous infinite loop. Loading uses a bounded-region breathing skeleton. OS reduced motion, Quieto and `?still=1` remove travel and loops and settle modal entry/exit without losing controls or selected fields. No six-step decorative fade-up sequence.

## Verification

- Real offline builder: PASS, 2,148 bundled source files. The builder emitted an 861KB bundle; the final standalone HTML is 1,167,893 bytes after the exact authored CSS is also placed in a head style block so the static token checker reads the same values as the runtime. No stylesheet, font, asset or package was fetched.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass` (exit 0).
- Final `audit_mockup.py --max-combos 300`: **544 renders / 544 planned combinations**, 11,476 text measurements and 1,544 keyboard focus stops at 1280px and 390px in both themes (exit 0). No combinations were sampled away.
- **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**
- Final `compare_directions.py A.html B.html C.html --json`: exit 0, `ok: true`, `evidence_ok: true`, no missing selectors. A/C layout similarity .006; B/C .053. Both differ in typography and motion. B/C share the first-screen navigation measurement, but their compositions, typography and motion differ; all pairs pass. This is a mechanical distinction check, not owner approval or proof of visual preference.
- `INTERACTION RESULT: PASS — 27 checks`: notice acceptance and password mismatch, Plan 2 destinations without Taller, updated-notice navigation lock, search/empty recovery, duplicate invitation refusal, one-time-link presentation, local invitation insertion and plan changes, saved-work refusal, last-administrator protection, exact-email deletion, read-only system permissions, no-permission role refusal, tool-group selection retention, Escape/focus return, generic fifteen-minute sign-in guidance, and reflow at 360/390/768/1024/1280px. No runtime page errors or HTTP(S) requests were observed.
- `MOTION AND MODAL RESULT: PASS`: actual 680ms `letter-pressure`, `knot-in` and `band-tension` timelines were observed running. The signed-in Plan 2 preview shows the person's account menu and sign-out returns to the sign-in fixture. Both `?still=1` and `?rm=1` have no running animations after 150ms, including modal entry/exit. Role-editor bounds stay within 390/1280px viewports in both themes under OS reduced motion.
- `ENTRY TYPECHECK: PASS`: in-memory strict/noEmit TypeScript check of diagnostics belonging to this TSX, using explicit installed-library/runtime aliases and skipLibCheck. This is not a production repository typecheck. The first checker invocation needed the installed Animate UI declaration exports mapped explicitly; it was a resolver setup issue, not a suppressed source error.
- Rendered visual review: desktop light sign-in/accounts, dark phone accounts, dark desktop role editor, and full light phone invitation activation. The sign-in footer shares the form inset; dark control edges and checkbox fills remain visible. All JSON evidence selectors were independently accepted by the comparison tool.
- Final HTML SHA-256: `179b1593ee5d3c1b62d6c68e883f07dde4766ceb67b0bf2d4593981e041e55fb`.

The first audit found four legend-on-frame padding cases and a long phone role editor. Replacing the border-crossing legends with inset named permission groups and exposing one tool group at a time resolved those findings. A later click-through found that the installed modal's inline Motion transform replaced CSS centring: the dialog could extend below the viewport even though the automated audit passed. Positioning now uses the independent CSS `translate` property, and explicit viewport-bound/click checks pass. Modal text overrides the stock opacity/blur effect so text remains fully opaque; entry and exit still use the profile transition.

An initial sign-out probe expected the old view's Spanish button after a view switch; the runtime intentionally remounts the fixture and reapplies browser language. The corrected probe asserts the sign-in destination and selects Spanish explicitly before checking its label. This does not establish per-account language persistence.

No production tests, deployment, database, real authentication, token invalidation or security enforcement were run by this design task. Those remain implementation/acceptance responsibilities, not unreported passes.

## Open questions and assumptions

Q: Who supplies the final data-controller name, legal basis, retention policy and contact details for the bilingual notice? Owner/legal must replace the bracketed placeholders before pilot publication; the draft keeps them visible.
Q: Does the owner choose this petrol/yellow latex direction and the rounded display pairing for the canonical account contract, or retain another exploration? No palette or font change is approved by this artifact.

Confirmed, not reopened: invited accounts only; copied links shared by the administrator; five immutable system roles; exact tool-plan grants; server-side permission enforcement; eight-character password minimum; fifteen-minute generic wait guidance; next-request revocation; protected last administrator; deletion only without account work; anonymised AI spend retained.

Assumptions: all people, companies, dates, email addresses and links are fictional fixtures. Notice copy is a visibly provisional legal-review sample. Language initially follows the browser, and the local ES/EN control demonstrates switching; persisted account language and production translations belong to SP-6. System role labels and fixture dates may retain their source Spanish display in this exploratory mockup; it is not a full SP-6 bilingual acceptance claim.

## Impact and approval state

Draft only. Affected SP-2 consumers if chosen: T2.1 copies the final owner-approved contract; T2.3 implements sign-in, invitation/reset and notice; T2.4 implements account/menu/password; T2.5 implements administration and role editing; T2.6 exercises the two-browser flow; T2.7 compares rendered fidelity; T2.8 audits behaviour/security. R1 maps to token/account screens, R3 to role editing/protections and R16 to exact plan descriptions and role changes. T2.2 remains the API implementation and is not implemented here. Compatibility is **undetermined until direction selection and canonical finalisation**. No implementation task may consume this exploration as an approved contract.
