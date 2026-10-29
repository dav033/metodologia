---
exploration: gasto-ia@v1.r1.dir-b
name: Sesiones e inspector
status: draft
subplan: SP-6
requirements: [R4, R5]
stance: spatial
chosen_thumbnail: gasto-ia@v1.r1.dir-b.html.candidate-1.html
owner: David
date: 2026-10-29
---

# Sesiones e inspector — spatial exploration B

## 1. Identity and traceability

Planning exploration only, **draft and unapproved**. This direction is a candidate for the future `gasto-ia@v1` contract, not the canonical contract and not an implementation approval. No canonical contract, shared HTML, PLAN, production repository or other bitácora file was changed. Owner feedback: none supplied.

Scope: `gasto-ia@v1.r1.behavior.md`, R4/R5 and SPEC “Behavior — SP-6 (round 12 pending)”. Current PLAN identifies SP-6, contract `gasto-ia`, version 1, design-copy T6.1 and visual review T6.6; T6.4 builds the dashboard and T6.5 checks real entry points. These are the affected consumers if this direction is chosen. Compatibility is **undetermined** until independent selection and plan approval; there is no previous gasto-ia draft to supersede.

Read-only product evidence: t12 and asesor surfaces and globals.css; t12 `src/components/admin/AdminTabs.tsx`, `src/components/ui/shell/CabeceraApp.tsx`, `src/app/layout.tsx`, production provider/model vocabulary; canonical sibling Markdown/HTML for `cuentas-admin@v1`, `planes@v1`, `proyectos@v1`, plus the selected accounts r14 source for exact shell/token/font composition. Existing admin contains operational tabs but no account-linked AI spend screen. The proposed spend area is an addition to that admin context, using the siblings' updated shared shell. Its route remains an owner question.

## 2. Purpose and users

An Empleado interno or Administrador with `gasto.ver` reviews known estimated spend and reported tokens by session, work item, user, kind and tool. User and call-kind filters constrain every displayed total and group. Success is finding a group and tracing its amounts to individual paid calls without opening conversation content.

The ordinary Usuario, signed-out visitor and any caller without `gasto.ver` receive no spend data. The denied fixture contains a refusal and no totals, filters, groups or calls. This static artifact demonstrates presentation only; it does not implement authentication or server authorization. Production must enforce permission before returning ledger data and independently hide inaccessible navigation destinations.

## 3. Approach and hierarchy

Keep the Pictures/Sempertex ring-and-dot masthead, language/account controls, 24px task heading, neutral horizontal administration navigation, rounded working paper and footer established by the siblings. Add the Gasto IA destination in that context; do not redesign other admin screens.

Inside the changed area, place the filtered total and filters above a two-pane workspace. The left pane is a group register; the wider right pane is an inspector with selected-group total, kind subtotals and attributed call rows. This replaces a flat report with a spatial relationship between a group and its calls. There is no chart, promotional panel, budget editor, limit, invoice or invented billing workflow.

**Two thumbnails were written and rendered first.** Candidate 1 places a compact register and a wide call inspector inside one paper. Candidate 2 places a wide project register beside a separate narrow inspector. Candidate 1 was selected because the inspector can show provider/model, session, work item and missing metadata without compressing them into a narrow column. Both thumbnail HTMLs remain available; their composed data are illustrative rather than additional behavioral contracts.

## 4. Eight-axis direction and fixed design system

| Axis | Expression in this artifact |
|---|---|
| Concept | Select a spend group and inspect the paid calls that produce its known amount. Project totals retain conversation attribution; independent calls remain grouped by conversation. |
| Layout | One working paper; filters across the top; 330px register and fluid inspector at 1100px+, 270px register at 768–1099px. Below 768px, a single-pane group-to-detail sequence reuses the same content. |
| Navigation | Local “Agrupar por” controls for Sesión, Trabajo, Usuario, Tipo, Herramienta; pressed group rows update the adjacent inspector. Phone selection opens the inspector and its back control restores focus to the selected row. |
| Typography | Existing Geist Sans; 24px page H1, 20px section/selected-group headings, 28px selected amount (26px phone), 15px call titles/body and 12–13px metadata. Geist Mono only for source identifiers/model metadata. USD uses tabular figures. |
| Density | 28px desktop and 20px phone paper padding, 18px register-row padding, 20px call spacing and ruled rows. Two initial calls keep the inspector finite; an explicit more-calls action discloses remaining fixture calls. No repeated KPI-card grid. |
| Components | Real installed shadcn/Base UI Button and Skeleton, native labeled selectors, native attribution disclosures and custom register/inspector compositions. Same sibling 32px panels, 24px inset vocabulary, 18px fields and pill controls. |
| Colour | Exact production globals.css and sibling mappings in both themes. Neutral chrome, primary/ring for identity and focus, warning tokens only for actual partial/error usage. Unknown values remain neutral text. No new palette or font family. |
| Motion | Spatial seating: inspector moves from +22px through −2px to rest; rows enter from −10px; calls settle 8px vertically; sheet opens from scaleX(.99). 460ms expressive / 300ms natural / 160ms subtle, 45ms row offsets, 180/140/100ms controls; cubic-bezier(.23,1,.32,1). Hover shifts groups 3px and lifts buttons 2px. |

Source-token mapping is copied from the retained accounts shell, not from kit palette defaults:

| Pictures source | Kit role / usage | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--texto` | foregrounds | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted-foreground | #6b6178 / #9aa1ad |
| `--superficie-2` | secondary, muted, accent | #efe9f8 / #242733 |
| `--superficie-suave` | selected register row, disclosure | #faf8fd / #1c1e26 |
| `--acento`, `--sobre-acento` | primary, primary-foreground | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | primary hover | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | decorative border, rule | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | accessible input boundary, inherited sibling alias | #766c85 / #8a91a0 |
| `--aviso`, `--aviso-suave` | warning, warning-soft | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | destructive, destructive-soft | #b23a45, #ffeaec / #ff979f, #43252a |

Geist Sans/Mono WOFF2 files are embedded from the existing t12 Next build. No assets or packages were downloaded. Components: `shadcn:button outline default|hover|pressed|focus|disabled` from `@/components/ui/button`; `shadcn:skeleton record loading` from `@/components/ui/skeleton`. `native:select user|kind|language`, `native:details account|attribution`, `custom:spend-register` and `custom:call-inspector` are explicitly custom compositions, not claims of library components. `mountMockup/useMockup` and `useMotionProfile` are real kit runtime imports.

## 5. Navigation and interaction

The product grouping controls preserve user/kind filters; selecting a row preserves the current grouping and filters. A mixed-account group reports its user count rather than attributing the whole group to the first account. Native view/state/theme/motion selectors are visible inspection controls outside the product, retaining the Mockup label. Changing inspection views/states resets the fixture; product interactions preserve their own state.

The admin destinations Cuentas / Roles y permisos / Mi cuenta and account disclosure copy are retained shell context, represented as non-navigating labels: this exploration does not simulate those sibling workflows or issue requests to their routes. ES/EN changes product labels and metadata formatting locally. No dialogs are needed, so no `scene` selector is declared.

A group row is a real button with `aria-pressed` and `aria-controls`. Phone activation focuses the inspector heading; return focuses the same row. Attribution uses a native keyboard disclosure. More-calls expansion adds the remaining mock records without changing the selected group or issuing a request. Production pagination must preserve the server's cursor semantics; this fixture does not claim to implement them.

## 6. Flows

1. **Review a session:** enter permitted spend view → choose user and kind if needed → choose Sesión → select a server session → inspect known total, text/image subtotals and its calls → expand attribution where needed.
2. **Review a project:** switch to Trabajo with filters preserved → select Proyecto pro_01 → inspect calls carrying con_01 and con_03 → disclose remaining calls. Standalone con_02 is a distinct work item, not a project.
3. **Compare other totals:** choose Usuario, Tipo or Herramienta → select group → inspect its calls. Totals and counts derive from the same filtered fixture.
4. **Recover:** load error → keep user/kind selectors usable → Reintentar → replace failure with results while preserving filters. Empty → change filters or Ver todos. Loading disables duplicate filter actions.
5. **Inspect partial usage:** select Datos parciales in the inspector bar → known error usage remains included → one call with unknown cost is explicitly reported → expand its attribution; never substitute a missing cost/token/model with zero or a guessed value.
6. **Phone inspection:** select a register row → replace register with inspector → focus its heading → back → restore selected-row focus. Reduced motion retains this sequence without travel.

## 7. View specifications and mock data

Five views share the same filters, known-total summary and inspector: Sesión, Trabajo, Usuario, Tipo, Herramienta. Each selected group shows estimated known USD, text/image amounts, call count and its call rows. Each row shows kind, tool, provider/model when reported, project or standalone-conversation context, conversation id, account label, server-session id, date, input/output tokens, estimated cost and explicit completion/partial/error status. Attribution disclosure adds email and record id. No prompt, response, generated asset, API key or unrelated personal profile data is present.

The four normal fixture calls belong to two existing sibling mock accounts (`master@prueba.local`, `admin@prueba.local`), three server sessions, one project with two conversations, and one independent conversation. The known normal total is **0.0560 USD**, project total **0.0480 USD**, ses_01 **0.0420 USD**. Normal reported tokens total **6,100**; the image call's unreported tokens remain “No informado”. Data are explicitly labeled mock; provider/model vocabulary comes from the repository. The displayed date is this delegation's supplied 2026-10-29, not an invented event chronology; no fictional person/event names or times are added.

Partial fixture adds 0.0010 USD and 100 known input tokens from a provider error, plus an image error with unknown model/tokens/cost. Filtered known total becomes **0.0570 USD**, known tokens **6,200**, with one explicitly unknown cost. Integer fixture values represent ten-thousandths of USD to make sums deterministic; they do not establish production storage or pricing. Four decimal places are a visual proposal pending Q3.

## 8. States

| Native state value | Visible behavior / recovery |
|---|---|
| `normal` | Successful results, derived totals, selected-group inspector; clear-filters disabled when filters already include all records. |
| `cargando` | Register/inspector skeletons, loading status and disabled user/kind/clear controls; no stale currency presented as current. |
| `vacio` | “No hay llamadas registradas para estos filtros.” and Ver todos; no invented record or zero-usage call. The same state is reached by a real fixture filter combination with no calls. |
| `error` | Scoped load failure, existing filters remain usable and Reintentar recovers locally while keeping them. Production offline/fetch failure uses the same recoverable presentation. |
| `parcial` | Warning text explains known amounts are retained and missing values are not zero; per-call partial/error status and unknown metadata remain visible. |
| `sin-permiso` | Scoped refusal; no ledger totals, filters, groups or calls are rendered. Server enforcement is outside the static mockup. |

No editable ledger mutation, form validation, saving success, destructive confirmation or payment flow is introduced; those states are inapplicable. Successful review is the normal state. Collapsing/expanding attribution and phone list/detail are reachable local substates. A failed provider call is a record status, distinct from failing to load the dashboard.

## 9. Responsive behavior

Supported design range: **360px upward**; automated audit checkpoints 390px and 1280px; additional 360px dark/EN interaction check performed. At 1100px+, 40px shell gutters, 330px register, fluid inspector, and three-column filter strip. At 768–1099px, 24px gutters, 270px register, two filter fields with the clear action below, and stacked disclosure metadata. Below 768px, 20px shell/paper gutters, wrapped masthead/route labels, stacked filters, and a single active register or inspector. The selected-group detail remains fully available after selection and back; it is not removed as unsupported on phone. Long account names, models and ids wrap. Call price can wrap below its title. There is vertical page scrolling and no horizontal page scrolling.

## 10. Accessibility and motion parity

WCAG 2.2 AA is the design target; this mockup audit is evidence for measured properties, not a blanket compliance claim. Associated labels, actual native selects/disclosures, semantic headings, live totals/statuses, alert on load failure, visible 3px focus outline and minimum 44px control height are present. Selected groups use a text/outline change plus pressed state, not color alone. Monetary figures name USD and estimation/coverage. Neither permission nor call status is inferred from color.

Expressive motion remains legible without hiding text. `useMotionProfile` supplies profile/reduced state; CSS uses those timings. OS reduced motion, Quieto and `?still=1` suppress travel, skeleton looping and transitions while preserving every control and final state. Hidden tabs pause CSS animation. Only finite spatial transitions and a loading skeleton run; no offscreen heavy renderer, canvas or decorative loop is introduced.

## 11. Observable acceptance and evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-AC-01 | 1280px | normal | Pictures/Sempertex masthead, language/account context, neutral route rule and one rounded paper match the sibling shell. |
| B-AC-02 | 1280px | normal | Register is left of the wider inspector, with a shared filter strip above them. |
| B-AC-03 | 360–767px | normal | Choosing a group exposes its inspector and back action without horizontal page scrolling. |
| B-AC-04 | 390px | normal | Back from inspector restores focus to the selected register row. |
| B-AC-05 | all supported | normal | User/kind filters update the overall total and every group from the same records. |
| B-AC-06 | all supported | normal | Group navigation and load-error retry preserve the selected product filters. |
| B-AC-07 | all supported | partial | Known total is 0.0570 USD; one unknown-cost call is named separately. |
| B-AC-08 | all supported | partial | Unknown tokens/model/cost say No informado; known provider-error usage remains included. |
| B-AC-09 | all supported | normal / partial | Project grouping keeps conversation ids on call rows and independent conversations separate. |
| B-AC-10 | 390 / 1280px | loading / empty / error | Skeletons, empty explanation and retry action are reachable through Estado. |
| B-AC-11 | all supported | denied | No ledger amount, filter, group or call appears. |
| B-AC-12 | all supported | all | Both themes and ES/EN retain labels, readable text and focus indication. |
| B-AC-13 | all supported | normal | Inspector has a running spatial entrance in expressive mode; reduced/still shows its settled state with no running travel animation. |
| B-AC-14 | 390px | normal, attribution open | Expanded attribution stays inside the paper without contrast, padding or overflow findings. |

Final offline builder: **PASS**, 393 KB self-contained HTML, 1,956 source files bundled. No plain-HTML fallback or package installation used for the full mockup.

`contrast.py`: **158 pairs checked in light and dark, all pass**.

Final `audit_mockup.py`: **120 renders (120 combinations planned), 4,062 text measurements, 384 focus stops**; exit 0.

**RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**

Additional Playwright checks passed: totals/filter derivation; project/conversation attribution; preservation across grouping/retry; mixed-account group labels; partial-call disclosure; denied-state data hiding; native disclosure expansion; phone heading/return focus; 360px dark/EN reflow; active inspector animation and reduced-motion parity; zero JavaScript errors and zero HTTP requests. Open-attribution probe at 390px measured 67 text elements with no contrast, non-text, alignment, padding, overflow or unmeasured-color findings. Rendered screenshots inspected at 1280px in both themes and 390px list/detail; both thumbnail compositions were visually inspected before the full build. Screenshots were inspected in memory; no unassigned screenshot/log files were written.

## 12. Open questions and concerns

Q: Should Gasto IA be a peer destination alongside account administration, with its own permitted page, or an additional tab inside the current operational AdminTabs? The mockup proposes the sibling shared navigation; no route is approved here.
Q: Should the initial query include all retained history or a bounded reporting period? The fixture date only scopes illustrative data and does not establish a default production date window or a new date-filter requirement.
Q: Is four-decimal USD display acceptable, and how should smaller known nonzero costs be presented without rounding them to an apparent zero? The mockup precision is illustrative, not a decision about ledger precision or tariffs.

Decision owner: David with Planner. These questions do not block this bounded planning exploration. Confirmed: project totals retain conversation detail; standalone calls group by conversation; known billable provider-error usage remains included, with missing values unknown. No plan or direction has been approved by Designer.

Concerns: this static mockup does not validate server authorization, provider billing completeness, retry idempotency, true cursor pagination, account identities or real timestamps. Those remain with SP-6 engineering and independent acceptance. Canonical finalization and sibling-workflow implementation remain outside this exploration. No repository code or shared contract was modified.
