---
name: Registro operativo
contract: gasto-ia
version: 1
revision: r1
direction: a
status: draft
subplan: SP-6
requirements: [R4, R5]
source_behavior: gasto-ia@v1.r1.behavior.md
author: Designer
date: 2026-10-29
---

# Registro operativo — direction a

This is a completed **exploration**, not the canonical twelve-section contract or an approval. The owner is still discussing the plan. Only this direction's revision-specific files are written; no shared contract, production repository, plan, preview directory or other direction is modified. A later finalizer must write the canonical draft after the owner's choice.

## Approach and chosen thumbnail

The main question is: **which user, session or work item incurred this estimated spend, and what is actually known?** The changed area is the staff administration workspace. A full-width operational ledger places filters, query totals and grouped rows on one working paper. Opening a session or work item keeps the masthead, navigation, filters and cost vocabulary in place. No prompt viewer, provider configuration, billing action, spend limit, export, date filter or new application shell is introduced.

**Chosen thumbnail: `gasto-ia@v1.r1.dir-a.html.candidate-1.html`.** Candidate 1 keeps both sessions comparable, provides room for all five grouping dimensions and lets the estimated-cost total stay visible while reviewing records. Candidate 2 (`…candidate-2.html`) explores a 260px session selector beside a detail inspector; it spends working width on a second navigation region and makes cross-session comparison less direct. Both thumbnails are retained as visual compositions with the inherited shell, both theme choices and the actual local Geist font embedded. They are sketches, not audited full-state mockups.

The source TSX mounts real installed components through `mountMockup/useMockup` from `@kit/mockup`; the offline builder inlines their CSS/JS and local fonts. Native external selectors retain `view`, `state`, `theme`, `motion`, labelled Vista, Estado, Tema, Movimiento, and the visible Mockup label. There are no dialogs, so no scene selector is applicable. The product ES/EN selector is separate from inspection controls.

## Existing product and fixed system

Read-only evidence: both repositories' `src/app/globals.css`; t12 `src/app/layout.tsx`, `src/components/admin/AdminTabs.tsx`, `src/app/admin/page.tsx`, `src/components/ui/shell/CabeceraApp.tsx`, and the existing model/default usage wrappers. Administration already has a title, contextual navigation and tabbed operational content. There is no existing account-linked AI-spend dashboard to copy. This direction adds its content within that administration vocabulary and the more recent shared sibling shell; it does not claim a new production route already exists.

Sibling sources read: `cuentas-admin@v1.md/.html`, `planes@v1.md/.html`, `proyectos@v1.md/.html`, plus the chosen project TSX for exact theme/font mapping. The shell preserves the Pictures ring-and-dot mark, Sempertex wordmark, labelled language control, named account disclosure, 24px heading, neutral horizontal route navigation, rounded paper and aligned footer. Account-management destinations appear only in the administrator fixture; the employee fixture retains Gasto IA / Mi cuenta. The actual implementation must derive visibility from effective permissions, not hard-code a role name.

| Pictures source | Kit role / use | Light / dark |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--superficie-suave` | supporting notice | #faf8fd / #1c1e26 |
| `--superficie-2` | muted, secondary, neutral badge | #efe9f8 / #242733 |
| `--texto` | foregrounds and selected grouping rule | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted foreground | #6b6178 / #9aa1ad |
| `--texto-tenue` | input/control edge, inherited accessible sibling alias | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primary, ring / primary foreground | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | primary hover | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | decorative outline / record rules | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--aviso`, `--aviso-suave` | partial usage | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | billable provider error / query error | #b23a45, #ffeaec / #ff979f, #43252a |
| `--exito`, `--exito-suave` | existing mapped success roles | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |

Geist Sans and Geist Mono are embedded from the existing t12 `.next/static/media/` local WOFF2 files named by the TSX; no fetch or new font is used. Panel 32px, supporting inset 24px, field 18px and pill 999px radii retain sibling roles. Desktop paper padding is 28px, phone 20px; numbers align right in tabular figures. Project token values govern over kit defaults. No fallback HTML kit, package installation or network asset was needed.

Actual component vocabulary: `shadcn:button outline ready|hover|focus|disabled` from `@/components/ui/button`; `shadcn:skeleton record loading` from `@/components/ui/skeleton`; native labelled selects for user/kind/language and inspection; semantic table records; native `details/summary` for account/work/conversation disclosure; `motion.span` from `motion/react` for the grouping marker; `useMotionProfile` from `@kit/motion`; Lucide icons. The ledger, totals strip, notices and responsive label/value composition are custom arrangements, not invented library components.

## Eight-axis table and interaction detail

| Axis | Rendered expression |
|---|---|
| Concept | A working ledger of estimated AI spend, with known and unknown metadata explicitly separated. |
| Layout | One full-width paper: user/kind filter row → totals strip → five grouping controls → ruled records. Details replace only the working content. No KPI card grid or persistent side inspector. |
| Navigation | Existing administration route rule plus Por sesión / Por usuario / Por trabajo / Por tipo / Por herramienta. Click a session or work item to drill in; Volver al resumen restores the summary with its filters. The first detail disclosure is initially open. |
| Typography | Existing Geist; H1 24px, H2 18–20px, totals 28–32px, records 14px, metadata 12–13px. Mono only for technical IDs; no new type identity. |
| Density | 2:1:auto desktop filter row, compact ruled data in the shared paper, metadata adjacent to identity, progressive disclosure for per-call detail. Mobile records reflow into labelled pairs; filters stack. |
| Components | Real shadcn/Base UI Button/Skeleton, native selects/details, semantic table, contextual billable-error chips, one moving grouping underline. |
| Colour | Exact project themes; accent only for inherited mark, links and focus; neutral active navigation; warning/error tokens only for their semantic data states. No new palette. |
| Motion | Quick registration with production ease-out `cubic-bezier(.23,1,.32,1)`: 320ms paper + totals, rows enter 10px from the right with 28ms offsets, 180ms grouping marker, 160ms hover/press. Natural 220/130ms and 18ms offsets; subtle 140/100ms and 8ms offsets. Reduced/still removes motion and retains all content. |

The signature interaction is regrouping an unchanged query: its total stays fixed while a single underline moves to the chosen grouping and rows register in quick succession. Session → project → conversation exposes attribution without showing AI input or output. Hover raises action buttons 2px; press settles 1px down; drill-in arrows shift 3px. Details enter 6px from above. All motion is finite; hidden tabs pause CSS animations. Profile durations/reduced state explicitly control the Motion marker. No ambient loops, flashing or animation-only feedback.

## Views, flows and data semantics

| Native view | Purpose and structure |
|---|---|
| `summary` — Resumen | Filter by authenticated account identity and call kind. Read estimated USD, known tokens and call count, then switch among session/user/work/kind/tool totals without changing the query. Session rows show user; work rows show project or standalone conversation ID. |
| `session` — Detalle de sesión | Retain selected session and filters. Show user, session totals and work disclosures. A work disclosure contains tool, text/image kind, provider/model, input/output tokens, estimated USD, call/session/conversation IDs and date context. Ver conversaciones opens that exact work item. |
| `work` — Detalle de trabajo | Retain project or standalone conversation context and filters. Project disclosures separate conversations; standalone work remains the conversation without a fabricated project. Each disclosure exposes only usage metadata. |

Flow: permitted employee/administrator enters Gasto IA → chooses Usuario and Tipo de llamada → reads totals → selects a grouping → opens a session/work record → opens conversation detail → returns to summary. Filter changes apply immediately in the fixture and preserve typing/control focus. The selected filters, language and clicked record survive view changes in memory. No browser-storage writes or remote calls occur. The initial grouping is Por sesión; the first work/conversation detail is expanded and can be closed/reopened with keyboard. The full implementation must filter and aggregate across the server query, not just the loaded page. Query totals are distinct from the visible group count. The cursor-error fixture preserves the first loaded group, shows a next-page failure and Reintentar, then restores all fixture groups on retry; the normal fixture has no next cursor or active Load more action.

Fixtures are neutral and explicitly marked Datos de ejemplo / Mock data. Five normal calls derive **USD 0.0492**, **4,200 known tokens**, **5 calls**: ses-001 USD 0.0430 / 2,800 known tokens; ses-002 USD 0.0062 / 1,400 known tokens. Text defaults use the inspected `gemini-3.6-flash`; unreported model values stay No informado. The supplied task date 2026-10-29 is the fixture date, labelled UTC; this does not claim a live date range or actual customer activity. No customer names, emails, prompt bodies, generated content, secrets, balance or invoice information appears.

In `partial`, one known billable error adds USD 0.0030 and 200 known input tokens, with output unknown; one partial image call has unknown cost/tokens. The total becomes **known estimated USD 0.0522**, **4,400 known tokens**, **7 calls**, with an incomplete-total explanation. Known error usage remains included. Unknown values display No informado, never zero; a group with no known tokens displays No informado. Sums use the fixture values before display formatting. Four decimal places and UTC are **presentation proposals pending the questions below**. Nothing here implements provider pricing or ledger integrity.

| Native state | Rendered behavior / recovery |
|---|---|
| `normal` | Administrator fixture, full summary or selected detail; administrator account disclosure and permitted administration navigation. |
| `employee` | Same spend access and data, employee identity; unrelated account/role management links are absent in this fixture. |
| `loading` | Loading status with static skeleton rows; filters and clear action disabled; no fabricated totals. |
| `empty` | No usage has been recorded; explain that calls appear after their usage is recorded; no numeric totals or irrelevant action. |
| `no-results` | No matching records, explain changing user/kind; Limpiar filtros returns to the normal fixture. |
| `error` | Query failed; retain filters and expose Reintentar. Hide totals and stale ledger values. |
| `partial` | Known billable provider errors included, unknown fields labelled, explicit incomplete aggregate and per-call partial/error labels. |
| `offline` | Sin conexión, retained query controls and retry; no claim that cached values are current. |
| `denied` | Ordinary account identity and Sin acceso; no staff route navigation, filters, totals, groups or call metadata; Mi cuenta recovery. |
| `expired` | No account disclosure or ledger metadata; session-ended explanation and sign-in recovery. |
| `next-page-error` | Summary retains its first loaded group, complete query totals and pending-more status with retry. On detail views this inspector state uses their normal layout because cursor paging belongs to the summary. |

Disabled controls are visible in loading/default clear-filter states. Form validation, destructive confirmation, save and editing states are inapplicable to this read-only review surface. There is no writable account, amount or model field. Authorization/session states are visual fixtures only; SP-6's server permission and API work remain independently necessary.

## Responsive and accessibility targets

Supported floor: 360px. At **1100px+**, the workspace is capped at 1520px with 40px outer insets; filters use 2:1:auto columns, summary uses a 1.5:1:1 totals strip and horizontal table records. At **640–1099px**, outer insets become 24px and filters wrap into two columns with clear below. At **360–639px**, outer/paper insets are 20px, masthead/route tools wrap, filters stack, estimated USD spans both metric columns, known tokens and calls share the next row, grouping controls wrap, and records become labelled value pairs. Long model IDs wrap. Mobile notices align directly to the paper's content axis rather than adding a second inset. Vertical scrolling is expected; there is no horizontal page scrolling.

Target WCAG 2.2 AA: labelled controls, semantic headings/tables/disclosures, visible 3px accent focus with 4px offset, 44px interaction targets, ≥4.5:1 text and ≥3:1 essential control/focus contrast, keyboard-operable grouping with `aria-pressed`, state text/icons alongside colour and polite totals/loading status. Query failures use alerts. Page navigation focuses H1; filters/grouping do not replace their initiating focus. Account disclosure supports Escape and returns focus to summary. Reduced OS motion, Quieto and `?still=1` retain all data/actions with zero finite animation. Full screen-reader behavior and production permission enforcement require independent acceptance; a static mockup does not establish them.

## Verification, impact and concerns

The scoped outputs are the two candidate thumbnails, entry TSX, built HTML, this note and axis-evidence JSON. New draft compatibility is **undetermined** until a direction and canonical contract are independently selected/approved. Only SP-6 consumes `ui.contract=gasto-ia`, version 1: T6.1 pins it, T6.4 implements the staff surface, T6.5 verifies entrypoint attribution/authorization and T6.6 performs the visual review. No sibling contract or production consumer is changed by this exploration.

Actual final evidence: installed kit `installed=True built=True entries ok=96/96`; offline build exit 0, 528 KB and 1,956 source files; token contrast exit 0, `contrast: 158 pairs checked in light and dark, all pass`. Initial 180-render audit reported 42 alignment findings from the double-inset mobile notice. The notice now shares the mobile paper's content axis; the next 180-render audit passed. The final full audit after adding the employee inspection state exited 0: **198 renders / 198 planned combinations**, **6,370 text measurements**, **470 focus stops**, at 1280/390/768px in both themes, without sampling.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

The focused interaction script passed 12 groups: account/kind filtering, all five groupings, exact session/work selection, unknown-token labeling, incomplete totals, denial, expiry, query retry, cursor-error recovery, EN copy, 360/390/768/1280 reflow and account Escape; zero page errors or external HTTP(S) requests. Final additional probes passed after the employee addition: employee navigation contains only Gasto IA / Mi cuenta, employee role disclosure/Escape works, every JSON evidence selector exists in its declared view, six expressive animations are active at the observation point and zero are active under OS reduced motion or `?still=1`. Screenshots inspected in memory: both candidate compositions, 1280 light summary, 1280 dark session, 390 dark partial summary and 390 light work detail. No screenshot files were written. These measurements describe this fixture only. There is no production test/build claim.

Reproducible final commands (all paths absolute):

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/gasto-ia@v1.r1.dir-a.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/gasto-ia@v1.r1.dir-a.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/gasto-ia@v1.r1.dir-a.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/gasto-ia@v1.r1.dir-a.html --widths 1280,390,768 --max-combos 100
```

CONCERNS: this direction and its proposed route/time-window/precision choices remain unapproved. Real server authorization, cross-page aggregation, exact cost arithmetic, idempotency, retry reconciliation, provider accounting and actual session isolation are outside this exploration and unverified. External sibling navigation names its real intended destinations; those pages are not implemented inside this static file. No fallback or toolchain blocker occurred. The full canonical twelve-section contract is intentionally not written by this exploration.

## Open questions for the owner

Q: Should Gasto IA use `/admin/gasto-ia` and join the existing staff administration navigation? This exploration proposes that destination; the brief does not fix its path.

Q: What date interval should the initial spend query cover? The mockup uses only the supplied task date as clearly marked fixture context; no production interval is inferred.

Q: Should displayed call dates use UTC or the Bogotá timezone used in the sibling account register? UTC is explicit in this exploration, while production storage remains UTC.

Q: Is four-decimal estimated USD presentation sufficient, or must smaller known amounts remain visible at greater precision? Finalization must fix formatting without converting unknown values to zero.

All questions belong to David/Planner. They do not block comparison of this draft direction. No approval is requested or granted here.
