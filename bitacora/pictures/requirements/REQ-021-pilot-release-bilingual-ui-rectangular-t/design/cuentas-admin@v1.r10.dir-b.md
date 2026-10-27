---
name: Umbral de aire
status: draft
kind: independent-direction-exploration
contract_ref: cuentas-admin@v1
revision: r10.dir-b
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
approval: pending-owner-selection
chosen_thumbnail: cuentas-admin@v1.r10.dir-b.html.candidate-1.html
---

# Umbral de aire — direction B

## 1. Identity and traceability

This is the kinetic/spatial **exploration**, not the canonical contract, an approved version or an implementation input. No shared contract, plan, history, repository or other direction is changed. The owner chooses a direction before a separate finalizer writes the canonical contract.

Sources read: SPEC.md (`65b1e5ecc06f20d9`), PLAN.md (`cc7e53f2abf3c23c`), PLAN.json (`7a2c833a7e711508`) and the shared `cuentas-admin@v1.r10.behavior.md` (`c665ab01443531a7`); hashes are SHA-256 prefixes. SP-2 covers R1/R3/R16 and T2.1–T2.8. Proposed visual impact: T2.3 access, T2.4 account and T2.5 administration; T2.6 tests, T2.7 visual review and T2.8 audit remain independent. T2.1 must eventually copy the owner-approved canonical artifact, never this exploration. Compatibility with a future implementation is undetermined until selection/finalization; the new composition requires implementation and visual review. No consumer is retargeted here.

## 2. Concept, memorable move and two thumbnails

**Concept:** entering a decorator’s working space through an inflatable threshold. The stage is made from the product’s physical things: inflated latex, a yellow foil balloon, a tether and an installation surface. Large forward-leaning type expresses the pressure and momentum of those materials. Working information stays on an opaque plane.

**Memorable move:** the cobalt gate rotates into its footing, the foil balloon arrives diagonally and tensions its tether, and the working plane seats beside it with a small perspective correction. The form remains present and readable. After arriving, the foil moves gently against its tether, rather than making the form itself float.

Both original small HTML compositions were written **before** the full TSX/build:

- **Chosen: candidate 1**, `cuentas-admin@v1.r10.dir-b.html.candidate-1.html`: asymmetric threshold and legible work plane. The form, its heading and help share one left axis; the page footer shares the outer stage axes. This remains understandable when the sculpture becomes a small phone accent.
- Candidate 2, `cuentas-admin@v1.r10.dir-b.html.candidate-2.html`: a broad team stage under a three-stop track. Rejected because the track and second large title compete with the roster; its horizontal sculpture/roster combination leaves less room for account metadata on a phone.

**Why not a default:** no purple, pale cream, terracotta, generic dashboard metrics or ornamental card grid. The blue/yellow physical volumes, condensed italic display, asymmetric threshold corner and spatial seating choreography belong together. Operational fields remain familiar real controls. Material highlights are on objects; text never sits on a gradient.

## 3. Look ledger and hierarchy

Read sibling exploration notes: projects r8 A (working archive), B (front elevation and thumbnail ribbon), C (filed material samples); Taller r6 B (measurement stage and tool spine), C (cutting bench and bottom tray), and r7 C (silhouette mould). This direction does not repeat their archive, ribbon, sample folders, vertical tool spine, bottom tray, measurement rulers or push-in catalogue.

Shared identity: Pictures naming, the ring-like brand silhouette, direct Spanish product words, invitation-only access and the actual balloon-decoration world. The existing purple is deliberately replaced only in this exploration in response to the owner’s request for distinct colour worlds. No production token changes are proposed as an accomplished fact.

Each working plane answers one question: can I enter; can I accept; who has access; what can this account do; or what does this role allow? A single primary action follows that question. The large display remains outside the operational plane. The account list uses ruled records, not KPI tiles. Role permissions are grouped by tool.

## 4. Eight axes, visual system and provenance

| Axis | Present in this direction |
|---|---|
| Concept | Inflatable entry threshold, foil balloon and tether around the decorator’s access surface. |
| Layout / composition | Two planes: `.stage` uses .78fr story/sculpture and 1.6fr opaque work plane with 32px gap. The plane has a 72px entrance corner, while the other corners stay 18px. At ≤760px the story compacts above the working plane. |
| Navigation | An upper in-flow conveyor, not a sidebar or bottom dock: Cuentas, Roles, Mi cuenta. Its active station is an opaque puck. Account rows open details; direct labelled controls open dialogs. Public access has no registration or invitation-creation navigation. |
| Typography / scale | Embedded DejaVu Sans Condensed Bold Oblique for 48–78px display; embedded Liberation Sans Regular/Bold for working copy. Working headings 24–26px, body 15px, secondary copy 12–14px; role metadata reaches 11px. |
| Density / shape | Open stage; desktop plane padding 34px, intermediate 28px, phone 22px with 20px outside gutters. Fields 48px; buttons ≥44px; checkboxes 24px inside ≥44px labels. Account rows reflow into name, company, role, state and last-access lines. |
| Components | Real shadcn/Base UI Button, Input, Skeleton, DropdownMenu; Animate UI Checkbox, Dialog and AlertDialog. Custom CSS gate/foil/tether, entrance plane and station puck; Motion spring display. Native planning and language selectors. |
| Colour logic | Light: blue ground #d9e7fb, plane #f3f7ff, navy text #10294f, cobalt action #1545cc and yellow foil #ffcf49. Dark: stage #081d42, plane #102b56, white text #f3f7ff and yellow actions. Navigation is neutral; semantic errors/success remain text plus colour. |
| Motion | Gate rotation/stretch, diagonal foil arrival, tether uncoiling, perspective plane seating, spring display squaring, lateral row seating, compressed feedback, empty-ring settling, hover lift and press compression. After entry the foil has a 6s tethered sway. Expressive stage 800ms; natural 480ms; subtle 240ms. Row delay 55ms; controls 180ms. |

Read-only repository evidence: both t12 and asesor `src/app/globals.css`, including the shared semantic aliases and Taller roles. Mapping retains the project’s role names: `--fondo` → background, `--superficie` → card/popover, `--texto` → foreground, `--texto-suave` → muted-foreground, `--acento`/`--sobre-acento` → primary pair, `--borde` → border/input and `--error` → destructive. Values above are an explicit exploration palette, not the existing production values. Interactive borders are #54709a in light and #a3b8e0 in dark. Focus uses the primary colour with a 3px outline and 4px offset. Spacing is semantic at the plane, group and field levels rather than arbitrary per-field overrides.

Component sources: `shadcn:button` (`@/components/ui/button`, default/outline/ghost/destructive and disabled); `shadcn:input`, `shadcn:skeleton`, `shadcn:dropdown-menu`; Animate UI-backed `shadcn:checkbox`, `shadcn:dialog`, `shadcn:alert-dialog`. A local Button adapter adds `data-variant` because the installed component consumes its variant prop without rendering that attribute; the real button still owns semantics and keyboard interaction. Custom material illustration is CSS, not an image-generation or HTML-kit fallback. Fonts are embedded by the real offline builder from existing local files. No installation, fetch, CDN, remote image or remote font is used.

## 5. Navigation and interaction

The native runtime selectors remain `view`, `state`, `scene`, `theme`, plus `motion`, with the Mockup label. They are planning controls outside the product. The product language selector previews ES/EN; initial language follows the browser. Navigation within the mock retains the selected person and account changes; password inputs are not persisted across screen remounts.

Signed-in pages show Ana Restrepo / Administradora, Mi cuenta and Cerrar sesión through a real dropdown. Updated-notice acceptance blocks the product navigation and disables Mi cuenta until acceptance; sign-out remains available. Navigation focuses the large page heading. Dialogs are real Base UI/Animate UI primitives with modal background, keyboard operation and Escape dismissal. Destructive actions use AlertDialog, with an explicit Cancelar action.

The active station is measured as a static selection shape. The runtime remounts the product on view/state changes, so **a travelling shared-element puck is not claimed**; view/state choreography is demonstrated by the newly seating plane, display, material and rows instead.

## 6. Behavioural flows preserved

1. **Sign in:** email/password → requested page if allowed → otherwise first permitted area, or Mi cuenta. Wrong password, unknown email, deactivated account and lock share the same refusal, including the fifteen-minute wait. There is no public registration or email reset sender.
2. **Activate:** invited name/email → password twice, 8–200 characters → visible browser-language notice and unchecked consent → activate → session starts and the first permitted tool opens. The sample Plan 2 destination is Chat asistido. The static mock reports the destination rather than implementing that tool.
3. **Reset:** administrator-generated link → new password twice → confirmation → sign-in. Invalid, used and expired links share the same renewal message. Reset does not claim an automatic signed-in session.
4. **Accept updated notice:** blocking notice → explicit acceptance → recorded version/date confirmation → continue. The mock offers the sample administrator’s Cuentas destination.
5. **My account:** identity, role and notice date → current/new/confirmed password → confirmation explaining that all old sessions end and this browser receives a new one.
6. **Invite/manage:** search/filter roster → invite name/email/optional company/one role → reject duplicate email → show copyable link once. Invitation links last 7 days, resets 24 hours; regeneration invalidates unused earlier links of the same kind. Copy failure offers manual selection/copy.
7. **Account actions:** change role → next-request effect; deactivate/reactivate with explanation; exact-email deletion only without work. Camila demonstrates CUENTA_CON_TRABAJO; Ana demonstrates the last-administrator restriction; Julián demonstrates eligible deletion. AI spend is retained without personal data as Cuenta eliminada. No backend enforcement is claimed by a mock.
8. **Roles:** inspect five read-only system roles; create/edit custom name and checkbox grants; reject zero permissions with ROL_SIN_PERMISOS; prevent deletion while assigned to accounts. The existing custom role has two accounts; a newly created role has none and can be removed in the demonstration.

The **12** controls correspond exactly to PLAN T1.2’s permission catalogue, grouped 3/2/1/3/3. Plan 1 has 3 grants, Plan 2 has 5, Plan 3 has 6, employee has 9, administrator has 12. Taller 3D is one permission, including scene AI, plans, assembly sheet, export and own saved work. Its features are not invented independent grant switches.

## 7. View inventory

| Runtime view | Working content / primary action |
|---|---|
| login | Email, password, admin-reset explanation; Entrar. |
| activate | Invited identity, password/confirmation, full notice, consent; Activar cuenta. |
| reset | Password/confirmation, invalid-link recovery; Restablecer contraseña, then sign-in. |
| notice | Blocking full notice and consent; Aceptar y continuar. |
| mine | Name, email, role, accepted notice version/date; current/new/confirmed password. |
| accounts | Name/email search, role/state filters; all account metadata, details action and Invitar persona. |
| invite | Name, email, optional company, role/access summary; create link once and copy. |
| detail | Identity/company/state/last access, editable role, regenerate link, deactivate/reactivate, protected deletion. |
| roles | Five system roles plus custom example; grouped permissions, role name and validation; create/save/delete. |

Mock fixtures use reserved `.example` addresses, fabricated access dates and a visibly invalid token. Real access, token revocation, session expiry, password verification, privacy storage, role authorization, CSRF protection and database deletion remain production responsibilities of SP-1/SP-2. No legal conformance or backend acceptance is inferred.

## 8. States and dialogs

Visible Estado options: normal, loading (stable skeleton), empty, error, success, validation, invalid link, permission denied and offline/pending. Scene options: none, notice, new link, deactivate/reactivate, delete account, role with accounts. Each is reachable with the native selectors; in-product controls also reach their relevant dialogs.

Empty applies to roster results and custom roles; system roles remain visible. Authentication forms have no empty collection state, so selecting empty leaves their ordinary form. Invalid-link applies to activation/reset; on other views it does not invent a token condition. Validation is specific to password/consent, duplicate email or missing role grants. Offline keeps visible input and stale data, explains that nothing was sent/saved and disables submission; retry is explicit. Denied replaces protected content with recovery guidance. Disabled includes consent not accepted, immutable system roles, offline submission, protected last admin, owned work and unmatched deletion email.

Loading, normal success and fixture states never pretend to prove API behavior. Regenerated links are deliberately invalid demonstration tokens. Clipboard permission can fail; that failure is visible rather than fabricated success.

## 9. Responsive behavior

- **>1100px:** outer gutters 40px, 32px stage gap, 34px plane padding, full roster columns.
- **761–1100px:** 28px outer/plane padding, 24px gap, narrower story and company metadata reflow within each record.
- **≤760px:** 20px outer gutters, compact headline/material, one full-width plane with 22px padding, stacked filters and form pairs, roster metadata below identity, single-column permission groups. Conveyor remains in flow, never overlays the roster.
- Supported exploratory lower width: **360px**. Natural vertical scrolling handles long consent and permissions. No horizontal page scroll or gesture-only content. Text, form, help and footer use explicit shared container axes.

## 10. Accessibility and motion targets

WCAG 2.2 AA is the target, not a conformance claim. Text targets ≥4.5:1, large text ≥3:1 and interactive edges ≥3:1 in both themes. Opaque work surfaces preserve text contrast throughout choreography. Fields have visible labels; feedback has alert/status semantics; invalid fields identify feedback. The notice is available inline rather than hidden behind a small legal link. Disabled controls have nearby explanations.

Motion is expressive by default. Measured gate duration is .8s expressive, .48s natural, .24s subtle. The final-content geometry is reserved; transform-based motion does not move the layout. Foil sway pauses on sculpture hover, when the stage leaves the viewport and in a hidden tab. `prefers-reduced-motion`, Quieto and `?still=1` remove travel, sway and transitions and show the same content and actions immediately. The headline, gate, foil, tether, plane, rows, feedback and control gestures have distinct triggers; there is no flashing or animated text opacity.

## 11. Observable acceptance and actual evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-AC-01 | 1280px | normal | The story and working plane are separate columns; header/footer share the stage’s outer axes. |
| B-AC-02 | 360–390px | normal | Filters, fields and permission groups stack with no horizontal scroll; record metadata stays visible. |
| B-AC-03 | all | activation | Activar cuenta is disabled before consent; eight-character matching passwords and consent enable the demonstration flow. |
| B-AC-04 | all | login/error | One generic refusal includes the fifteen-minute wait; it does not identify the reason for failure. |
| B-AC-05 | all | notice | Cuentas/Roles navigation is absent before acceptance; sign-out remains available. |
| B-AC-06 | all | account detail | Owned-work and last-admin explanations are visible beside disabled destructive actions. |
| B-AC-07 | all | deletion dialog | A wrong email cannot enable permanent deletion; the exact eligible account email can. |
| B-AC-08 | all | roles | Twelve permission controls exist; Plan 3 has six read-only grants; an empty custom grant set is refused. |
| B-AC-09 | all | new-link dialog | A renewed invitation uses activar and 7 days; a reset uses restablecer and 24 hours; the revocation explanation precedes generation. |
| B-AC-10 | both themes | loading/error/offline | Stable skeleton, explicit retry and unsent/stale-data explanations are visibly distinguishable. |
| B-AC-11 | all | reduced motion | No active animation remains; all normal content and controls are still available. |
| B-AC-12 | 1280/390px | dialogs | A real modal/alertdialog opens with title/description and reachable cancel/close controls. |

The final tool results are recorded below. Initial findings were retained in the session: compressed account trigger, Retry contrast 4.42:1 and View action padding 5px. The causes were corrected in the actual composition: explicit trigger dimensions, a rendered variant style hook and a wider row-action column. The reset screen’s secondary return action also received a visible outline so its centered label is an explicit control, not a stray centered text line. No thresholds or checker rules were changed.

- Build: final real offline builder, installed libraries; **2637KB**, 2292 source files. Final HTML SHA-256 prefix `a93dc792617df618`; TSX `33f8fef4bd85dad7`.
- Contrast: final HTML, **158 pairs across light/dark, all pass**.
- Focused rendered probes: **160 renders**, ES/EN, light/dark, widths 360/390/768/1280, normal/error on five representative views; **0 contrast, non-text, alignment, padding or overflow findings**.
- Interaction checks: activation consent/password; generic sign-in refusal; notice gate/continuation; selected-account identity; renewed invitation route/7-day expiry/Escape; exact-email deletion; work guard/deactivation; last-admin guard; 12 permissions/Plan 3 six grants; zero-grant rejection and new-role deletion; duplicate email; invitation/link and roster update. All passed. The initial test locator hit Base UI’s hidden input; the corrected check uses the visible checkbox role and passed without forced clicks.
- Runtime request observation: **zero HTTP(S) requests**, **zero browser errors** during those interactions.
- Reduced-motion and `?still=1`: zero active animations, with the same five login controls as expressive mode. Natural/subtle durations measured .48s/.24s. The active station is static, as documented above.
- Screenshots inspected in memory: 1280 light login and dark roles/custom editor; 390 dark accounts and light activation. Screenshots are not extra files outside the assigned output scope.
- Final audit: **504 renders of 504 planned combinations**, 10,622 text measurements, 1,366 focus stops at 1280/390px, light/dark, every view/state and dialog. Command: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r10.dir-b.html --max-combos 300`.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

- Final ambient-motion checks: `foil-arrive, foil-sway` measured; hover and simulated hidden-tab state both reported `paused`. Reduced motion and `?still=1` reported zero active animations.
- Direction comparison: current r10 A/B/C initially returned `ok: true`, `evidence_ok: true`, no missing selectors. A/B layout similarity .006; B/C .053; typography and motion differ in both pairs. The probe finds no first-screen navigation in either B or C, so `same_navigation: true` for B/C is recorded honestly; their actual signed-in navigation claims were separately found. Final rebuilt-HTML comparison also returned **`ok: true`, `evidence_ok: true`, `missing_evidence: []`**, with the same .006/.053 A/B and B/C layout similarities. The actual `compare_directions.py A.html B.html C.html --json` command ran offline against the current r10 siblings; it passed. An intermediate Python convenience import used a nonexistent helper name and did not run; the direct CLI comparison above is the successful verification.

## 12. Open question and boundaries

Q: Which final data-controller identity, privacy contact, policy URL and ES/EN notice text will Sempertex legal approve to replace the bracketed illustrative content before real invitations?

The privacy text is a visible illustrative draft, not a legal approval or a claim that placeholders are release-ready. Source acceptance and security must be verified in the implemented product. No repository lint, typecheck, production build, backend test or deployed acceptance is claimed for a design-only task. Fonts come from existing local files and are bundled for review; final product font selection/licensing review belongs to finalization. Owner direction selection and plan approval remain pending.
