---
contract: gasto-ia
version: 1
revision: r1
artifact: direction-exploration
status: draft
subplan: SP-6
requirements: [R4, R5]
owner: David
author: Designer
date: 2026-10-29
direction: Desglose en el lugar (c)
source_behavior: gasto-ia@v1.r1.behavior.md
chosen_thumbnail: gasto-ia@v1.r1.dir-c.html.candidate-1.html
---

# Desglose en el lugar — direction C

## 1. Identity and traceability

Planning exploration, **draft; unapproved**. This is a candidate direction for `gasto-ia@v1`, not the canonical contract and not an implementation approval. The shared behavior brief is authoritative. Inputs: that brief, SPEC “Behavior — SP-6 (round 12 pending)”, PLAN SP-6 and the canonical sibling `cuentas-admin@v1`, `planes@v1`, `proyectos@v1` Markdown and HTML artifacts. Other directions, shared contracts, planning files and production repositories are untouched.

Scope: T6.1 contract selection/copy, T6.4 staff dashboard, T6.6 rendered review; T6.5 supplies later production authorization/attribution verification. The visual artifact neither implements nor verifies a ledger or API. Compatibility is **undetermined until owner selection and finalization**; no approved version is replaced and no plan consumer is redirected.

## 2. Purpose and users

An Empleado interno or Administrador with `gasto.ver` reviews where paid AI spend occurred, then narrows it by account and call kind. The same filtered data can be grouped by session, work item or account. Work-item identity is project plus conversation detail when a project exists; otherwise the conversation. Tool subtotals are shown in expanded groups, with provider/model and date available in each call.

Ordinary Usuario accounts, signed-out visitors and people without the permission receive no ledger, filters, identities of other users or totals. Static refusal fixtures demonstrate presentation only; actual authorization must be enforced by the server for both the page and its API.

## 3. Approach and information hierarchy

The change sits inside the existing administrative surface, **not a new standalone product or landing page**. The current reference is `t12/src/app/admin/page.tsx` → `src/components/admin/AdminTabs.tsx`; `asesor` supplies the same product tokens/font setup and related shell. Existing administration already has a heading, chat return and horizontal navigation. The sibling chosen contracts establish its updated Pictures/Sempertex ring-and-dot masthead, language/account controls, 24px heading, neutral route rule and rounded working paper. Reuse those, adding only the Gasto de IA destination and spend content.

Reading order: mock/data/date context → account/kind filters and optional tool filter → one known-cost total with completeness and token coverage → grouping controls → full-width group disclosures → load-more/status → metadata-only notice. The total strip uses two columns, not separate KPI tiles. Each session/work/account group owns its subtotal, call rows and type/tool breakdown.

**Chosen thumbnail: candidate 1.** Both small compositions were authored and rendered before the full entry. Candidate 1 keeps all manipulation on the working paper and preserves width for metadata. Candidate 2 uses a permanent user subtotal rail, competing with the existing horizontal navigation and reducing record width. Both use the product tokens, embedded production Geist and the existing brand mark; their six-call partial-data snapshot is intentionally broader than the normal full mockup's four successful calls.

## 4. Eight-axis direction and design system

| Axis | Observable expression in this direction |
|---|---|
| Concept | Change the filters where their current values are displayed; open a group and call exactly where its spend is listed. Ledger values stay read-only. |
| Layout | Existing masthead/title/route rule; one 32px-radius paper; inline filter workbench, 1.2:1 total strip, then continuous full-width bands. No side inspector. |
| Navigation | Administration route rule plus three local grouping buttons; one expanded group; nested native call disclosure; optional tool filter. |
| Typography | Existing embedded Geist/Geist Mono; 24px H1, 20px desktop/18px phone group names, 32px amount, 12–15px details. Numbers use tabular figures. |
| Density | 28px desktop and 20px phone paper insets; 24px group padding; 44px interactive targets; phone records reflow rather than becoming a scrollable table. |
| Components | Real installed shadcn/Base UI Button and Skeleton, native selects/details and Lucide icons; existing pill controls, ring-and-dot mark and account disclosure. |
| Colour | Exact Pictures theme tokens; neutral active-group surface; purple brand/focus; existing green, warning and error for recorded status; unknown data muted. |
| Motion | Finite compression/settle choreography with spring-driven group press, independent total/disclosure seating, delayed bands and immediate reduced-motion equivalents. |

Token sources inspected read-only: both repositories' `src/app/globals.css`, the existing `AdminTabs`, `CabeceraApp`, layout/font definitions and sibling contracts. No new palette, font family, package or remotely fetched asset.

| Product token | Kit role / usage | Light / dark |
|---|---|---|
| `--fondo` | background | `#faf9fc` / `#0b0c10` |
| `--superficie` | card/popover | `#ffffff` / `#16181f` |
| `--texto` | foreground | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | muted foreground | `#6b6178` / `#9aa1ad` |
| `--superficie-2` | secondary, muted, selected controls | `#efe9f8` / `#242733` |
| `--superficie-suave` | call inset | `#faf8fd` / `#1c1e26` |
| `--acento`, `--sobre-acento` | primary, primary foreground | `#6d3fe0`, white / `#9479ff`, `#120b24` |
| `--texto-tenue` | input edge; sibling accessible alias | `#766c85` / `#8a91a0` |
| `--borde`, `--borde-suave` | panel and decorative rules | `#e3daef`, `#efe9f8` / `#383c48`, `#2a2d38` |
| `--exito` | completed status | `#1f7a55` / `#78d6a8` |
| `--aviso`, `--aviso-suave` | partial/billable-error status | `#8f5f12`, `#fff3d8` / `#f7c46b`, `#3f311c` |
| `--error`, `--error-suave` | error status/surface | `#b23a45`, `#ffeaec` / `#ff979f`, `#43252a` |

Installed components: `shadcn:button outline/ghost/default disabled/pressed/focus` from `@/components/ui/button`; `shadcn:skeleton loading` from `@/components/ui/skeleton`. Product-specific group bands, totals and metadata lists are custom compositions, not falsely labelled library components. The native tool/account/call disclosures are HTML `details`, not shadcn Accordion. Motion uses `motion/react` and `@kit/motion`. Local production font files are imported and embedded by the real builder.

## 5. Navigation and direct interaction

The existing shell remains recognizable: Pictures/Sempertex masthead, language control, account disclosure, heading, Volver al chat and neutral administration rule. This admin fixture shows Cuentas / Roles y permisos / Gasto de IA; production must omit sibling links when their independent permissions are absent. Mi cuenta, Planes and sign-out remain sibling-owned destinations. The mockup honestly shows a scope notice for those links rather than claiming those pages are implemented.

The exact product URL for spend has not been specified; local `#gasto` is an artifact anchor, **not a route contract**. Grouping is local in-page navigation, not three new product routes. Native planning selectors outside the product expose `view`, `state`, `theme`, `motion`, labelled Vista/Estado/Tema/Movimiento. No modal/dialog is introduced, so `scene` is inapplicable.

Account selection and Texto/Imagen/Todos buttons change filters immediately. The optional Herramienta disclosure reveals its labelled native selector. Changing filters closes the expanded group and resets visible pagination. Clearing filters restores all matching calls and initial first-group disclosure. The clear action is visibly disabled when no filter is applied and while loading.

One group opens at a time. Calls inside it disclose attribution, provider/model, token fields, date and explicit completion/partial/error status; prompts and generated output never appear. Disclosures preserve the triggering element's focus. Grouping buttons retain their semantic pressed state. The static runtime remounts views when its external view/state inspector changes. Local inspection choices preserve filters and language across those remounts; product grouping buttons restore focus to the new pressed grouping control without interrupting filter typing. This is in-memory prototype state only, with no storage write.

## 6. Flows

1. **Review spend:** authorized entry → known total and completeness → choose session/work/account grouping → open a group → inspect type/tool subtotals → expand a call for ledger metadata.
2. **Narrow review:** choose account and kind; optionally reveal tool selector → derived total, coverage and all groups update together → clear filters to recover the full scope. No edit/save operation exists on financial records.
3. **Investigate incomplete provider usage:** select partial/error state in inspection → billable known cost is included → unknown fields retain explicit unknown/not-reported labels → load more to see an entirely unknown-cost session. Unknown is never a fabricated zero.
4. **Recover a fetch failure:** no unconfirmed total is shown → filters stay available → Reintentar restores the successful fixture. Production must re-run the authorized server query with those filters.
5. **Review additional groups:** Cargar más appends two fixture groups without duplicate totals. The total always describes all filtered results, not only the visible page. Production needs server-derived complete filtered aggregates and cursor-safe detail paging.
6. **Denied/signed out:** render the appropriate refusal/sign-in explanation with no ledger → offer Mi cuenta or sign-in recovery through existing destinations. Never fetch then merely hide forbidden data.

## 7. Views and data semantics

| Inspector view | Main group identity | Detail retained |
|---|---|---|
| `sessions` | Session display suffix, account, work item and cost | Individual calls include project/conversation, provider/model, input/output/total tokens and date. |
| `work` | Project when present; otherwise conversation | Every call retains conversation, account and session attribution, including multiple sessions of the same project. |
| `users` | Account identity and its cost | Sessions, project/conversation and kind/tool attribution remain inside the account group. |

All are arrangements of the same metadata-only dashboard. Production grouping must use stable server IDs, not display suffixes or project names. Full IDs are not required to be exposed to review spend.

Synthetic normal data: four successful calls across two accounts and two sessions. Costs in USD are `0.0042 + 0.0600 + 0.0030 + 0.0360 = 0.1032`. Text totals `0.0072`; image totals `0.0960`. Session …a41 totals `0.0642`, …b72 `0.0390`. Two calls report total tokens, summing to 4,800; the other two do not. Coverage is always shown so the sum cannot be mistaken for a complete token total.

Partial/error data adds a provider-error call with known cost `0.0010` and known total 300 tokens, and another provider-error session with 1,200 known total tokens but unknown cost. The known cost becomes `0.1042` across **5/6 cost-known calls**, total tokens 6,300 across **4/6 token-known calls**. The wholly unknown-cost session displays “Desconocido”, not `$0.0000`. Available input/output/total token fields are reported independently; unavailable fields remain “No informado”. No assumption that input + output is complete is made.

All fixture dates use the supplied session date **2026-10-29**, labelled UTC, without invented historical dates, customer names or emails. Google/gemini-3.6-flash and fal.ai/FLUX.2 are existing provider/model vocabulary found in the repositories. Sample costs are illustrative ledger amounts, not provider pricing claims. No network research, provider call or package installation was required.

## 8. States

| Inspector state | Presentation / recovery |
|---|---|
| `normal` | Successful calls, one initially open group, totals and coverage; unknown token metadata stays visible as unknown. |
| `loading` | Three row-shaped real Skeletons, Cargando gasto status, `aria-busy`; no stale totals and filter mutations disabled. |
| `empty` | No-call explanation and clear/change-filter recovery; no misleading zero total. Covers both no matching calls and no recorded usage. |
| `error` | No unconfirmed figures, explicit load-failure explanation, filters retained and Reintentar. |
| `partial` | Explicit provider partial/error notice, known billable usage included, unknowns preserved; third session available through Cargar más. |
| `denied` | Ordinary account fixture, no ledger/filters, Sin acceso and Mi cuenta recovery. |
| `signed-out` | No account disclosure or ledger; sign-in explanation and existing sign-in destination. |

Hover, focus, pressed, disabled and open/closed disclosures are exercised with their actual controls. Filter validation errors are inapplicable to the enumerated selectors. Save success, editing, deletion, budget setting, exports and approval dialogs are out of scope. No separate offline cache or refresh promise is invented: an unavailable initial read uses the load-error state and withholds totals. In-flight page-two fetch and page-two retry remain production behavior requiring a decision; the artifact's local append is instantaneous and is not evidence of networking reliability.

## 9. Responsive behavior

Preserve the sibling 760px/1100px transitions and **360px minimum**.

| Range | Behavior |
|---|---|
| 1101px+ | App cap 1520px, 40px outer padding, 28px paper inset; inline filters; two-column total strip; group identity/metadata/cost/chevron grid; three-column expanded metadata. |
| 761–1100px | Outer padding 28px; group metadata flows under identity; cost and disclosure stay aligned on the right; expanded metadata becomes two columns. |
| 360–760px | Outer/paper padding 20px; header wraps naturally; filters and total strip stack, kind buttons remain a three-control row; grouping buttons become a vertical labelled group; amount follows its identity; call metadata becomes one column. Account dropdown aligns to its left edge within the viewport. No horizontal page scrolling. |

Spanish and English are selectable in both themes; the prototype changes no persisted language preference. Long model/identity labels wrap. Vertical page scrolling is expected for details. No custom drag-only interaction or mobile-only loss of metadata.

## 10. Accessibility and motion

WCAG 2.2 AA is the implementation target, not a certification. Labelled native selects, native disclosures, semantic headings/dl, pressed-state grouping/kind buttons, busy/status/alert announcements and 44px minimum controls support keyboard review. Focus uses a 3px accent outline with 4px offset. Selected controls retain an outline, not colour alone. Partial/error states also have explicit words. There is no focus trap because no dialog is introduced.

Motion grammar: band registration compresses and settles with 55ms offsets; the total seats horizontally when filters change; the expanded group seats vertically; expanded call/filter fields compress horizontally; notices settle independently. Expressive is 520/170/55ms, natural 320/140/30ms, subtle 160/100/12ms (settle/control/stagger). Product easing is `cubic-bezier(.34,1.4,.64,1)`. Group press uses the real profile spring; controls compress on press, preserving legibility without opacity drops. Animations are finite and transform-only; hidden tabs pause CSS motion. No ambient loop is added.

OS reduced motion, Quieto and `?still=1` disable travel, scaling, keyframes and transitions and retain the same fields, controls and statuses. The runtime's reduced state is passed to Motion; nothing depends on motion to communicate state.

## 11. Observable acceptance and actual evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-01 | 360px+ | all | Pictures/Sempertex mark, language control, 24px task heading and existing footer remain recognizable in both themes. |
| C-02 | 1101px+ | normal | Inline filters precede one two-column total strip and full-width groups; no permanent side inspector or KPI-card grid. |
| C-03 | 360–760px | normal | Every filter and grouping control fits the page; a record's amount follows its identity without horizontal scrolling. |
| C-04 | 360px+ | normal | Selecting Texto yields `$0.0072`; intersecting account A yields `$0.0042`; focus stays on the changed control. |
| C-05 | 360px+ | normal | Expanding a call exposes account/session/work-item/provider/model/date and separate available token fields. |
| C-06 | 360px+ | partial | Total shows `$0.1042`, 5/6 cost coverage and 6,300 known total tokens across 4/6 calls. |
| C-07 | 360px+ | partial | Cargar más exposes the third session; its cost is unknown and the all-results total does not change. |
| C-08 | 360px+ | loading / error | Skeletons or load-failure recovery replace figures; no unconfirmed total is rendered. |
| C-09 | 360px+ | denied / signed-out | Neither ledger nor filters are present; the appropriate existing account/sign-in recovery is offered. |
| C-10 | 360px+ | empty | No-call explanation and clear-filter recovery are visible; no fabricated monetary zero. |
| C-11 | 390 / 1280px | expanded | Metadata, account menu and tool selector remain readable and inset from screen edges in ES/EN and both themes. |
| C-12 | 360px+ | reduced / still | All content and feedback remain available with no finite motion running. |

### Honest verification

- Real installed workspace status: installed/built, **96/96** entries available. Used the required absolute-path offline builder on this direction's TSX/output path. No fallback, install, external asset or canonical write.
- `contrast.py`: **158 pairs checked in light and dark, all pass**.
- Required Playwright audit: **84 renders / 84 planned combinations**, **2,648 text measurements**, **432 focus stops**. Final rebuilt output: `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- Supplemental interaction run: **43 checks passed** (filters and focus retention, tool disclosure, metadata, totals, partial/unknown semantics, load more, all three groupings, denied/signed-out suppression, load retry, 24 ES/EN/theme/width overflow checks, no runtime errors and no network requests).
- Rendered screenshots inspected in memory at 1280/390 in both themes; thumbnails also rendered before the full composition. No screenshot artifact was written outside the assigned files.
- Additional expanded metadata/account/tool probes initially found a phone account dropdown too close to the screen edge. Fixed left alignment below 760px and translated the role label in EN; the repeated check passed all **8 expanded metadata/account/tool combinations** across ES/EN, both themes and 390/1280px. The initial failure is not counted as a pass.
- Final rebuilt-output regression checks also passed: grouping retains the same filters/language and restores focus to the active button; retry retains filters. The 24 responsive combinations and 8 expanded probes passed again after this change.
- Live animation sampling observed actual `total-seat`, `band-settle`, `disclosure-seat` keyframes with 520ms duration. JSON evidence selectors identify rendered controls and motion, not the body.
- Production lint/typecheck/tests/build were not run: repositories were read-only and no production code changed. The static build and browser audit do not establish server authorization, ledger correctness, idempotency or actual cursor behavior; T6.5/T6.6 retain those responsibilities.

## 12. Open questions, assumptions and concerns

**Confirmed:** metadata-only access with `gasto.ver`; account/kind filtering; session/user/work grouping; project plus conversation detail or standalone conversation; known billable error usage retained; unknown provider fields never fabricated. The ledger is read-only in this scope.

**Provisional visual choices:** one initially expanded group, three grouping modes, optional tool filtering, four decimal places in USD, date explicitly labelled UTC, total completeness alongside token completeness, complete filtered aggregate above paginated groups. These do not authorize a new API contract or product setting.

Q: What is the final spend route and permission-aware administration entry for Empleado interno, preserving the sibling shell while hiding Cuentas/Roles links when their grants are absent?
Q: Should staff review dates in UTC, as explicitly labelled in this exploration, or in America/Bogota like the sibling account register?
Q: Are four decimal places sufficient for the displayed USD estimate, or should sub-$0.0001 amounts use a finer precision while preserving non-zero values?
Q: What copy and recovery should appear when loading a subsequent cursor page fails, and should already confirmed groups stay available? The local mock append does not simulate that asynchronous state.

Decision owner: David with the Planner. These questions do not block exploration and must be resolved or explicitly carried into finalization before implementation. No permission, account, plan or navigation changes outside SP-6 are approved here. The artifact remains **draft and awaiting direction selection**, and the canonical `gasto-ia@v1.md`/`.html` are untouched.
