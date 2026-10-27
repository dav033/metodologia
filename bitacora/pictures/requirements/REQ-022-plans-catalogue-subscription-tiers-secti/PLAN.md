---
req: REQ-022
status: draft
created: 2026-10-27
---
# Plan — Plans catalogue: an informative section to compare Free, the second tier, Designer and Designer Max, then access by plan

Draft (planning phase: skeleton plus SP-1 detailed). SP-1 is the plans section the owner asked for and comes first;
SP-2 to SP-4 (entitlements, Free limits, plan awareness) are skeleton subplans without tasks until the owner answers
the open questions that shape them. Nothing here is approved.

## Approach
Code base inspected read-only: `dav033/pictures` origin/main `a9f3d6e5` (Next on Vercel, design tokens in
`src/app/globals.css`, shared-password guard in `src/proxy.ts`, header menu `src/components/ui/shell/MenuApp.tsx`,
static-render UI tests such as `scripts/test/test-ui-armado-columna.ts`, Playwright smoke `scripts/e2e/humo.ts`).
REQ-021 (read-only) plans the accounts, the five system roles and the permission keys (`chat.usar`, `contador.usar`,
`catalogo.ver`, `costos.usar`, `decoraciones.explorar`, `taller.usar`, ...) in its SP-1 and the three chat tools in its
SP-7; none of it is on main yet.

**Order.** SP-1 first: one plan catalogue (data module) and an informative section that renders only from it. It
survives any answer about purchase (no action in SP-1) and about role mapping (the catalogue uses its own tool keys,
mapped to permissions later in SP-2). SP-2, SP-3 and SP-4 consume the catalogue contract `plan-catalogue@1` produced by
T1.2 and come after SP-1's audit.

**Dependency on REQ-021.** Implementation of every subplan lands after REQ-021 SP-1 is on main (it replaces the
`APP_PASSWORD` guard that T1.4 extends; SP-1 declares the external contract `permission-map@1`). SP-2 also needs
REQ-021 SP-1 roles/permissions; SP-3 and SP-4 need the REQ-021 SP-7 tool screens.

## Proposed requirements (to be copied into SPEC `## Requirements` once the owner confirms them)
The SPEC has no numbered requirements yet; PLAN.json uses these ids. The Planner did not edit that SPEC section.
- R1. The system shall define the four plans — Free, the second tier, Designer and Designer Max — in one catalogue holding, for each, its name in Spanish and English, its monthly price in COP and USD, its included tools and its limits; second tier COP 20,000 / USD 7, Designer COP 45,000 / USD 14 (owner).
- R2. When a person opens the plans section, the system shall show the four plans in order with name, monthly price, included tools and limits, read from the catalogue, without any purchase or access change.
- R3. The plans section shall be reachable from the entry points, and open for the audience, that the owner decides.
- R4. When an account is on a plan, the system shall grant exactly that plan's tools on the server and refuse every other tool.
- R5. While an account is on Free, if it reaches a Free limit, then the system shall refuse further use of that tool with a message naming the limit and when it resets.
- R6. When a signed-in person opens the plans section, the system shall mark their current plan.
- R7. When a person opens a tool their plan does not include, the system shall name the plan that includes it and link to the plans section.
- Conditional R8 (only if open question 2 is answered «request» or «purchase»): the action on a plan; it becomes its own subplan then.

## Inputs (pending; locations only)
| # | Item | Subplan | Status |
|---|---|---|---|
| 1 | Second tier name and contents | SP-1, SP-2 | pending (open question 1) |
| 2 | Free limits: what is counted, how many, per day or month, what happens at the limit | SP-1, SP-3 | pending (open question 1) |
| 3 | Designer Max monthly price (COP / USD) | SP-1 | pending (new open question 7) |
| 4 | Whether each plan includes everything in the plans below it | SP-1, SP-2 | pending (new open question 8) |
| 5 | Audience and entry points of the section | SP-1 | pending (open question 4) |
| 6 | Whether extended chat, structure detection and advanced balloon detection exist or are future work | SP-1, SP-2 | pending (open question 5) |
| 7 | Mapping of tiers onto REQ-021 roles | SP-2, SP-4 | pending (open question 3) |
| 8 | Informative only, request or purchase | conditional R8 | pending (open question 2) |
| 9 | Pilot timing | all | pending (open question 6) |
| 10 | How COP and USD are shown (by language or both) | SP-1 | pending (new open question 9) |
| 11 | Test database for SP-2..SP-4 (accounts) | SP-2..SP-4 | location known from REQ-021 (`PICTURES_REQ021_DATABASE_URL` in `~/.config/flow/secrets.env`); confirm reuse when SP-2 is in focus |

No secret values are recorded. SPEC `## Inputs` is not written here (the Planner was limited to the SPEC sections
Open questions, Clarifications and Coverage); the HQ should copy this table into SPEC so the Plan tab can gate it.

### M1 — Plans section (informative)
Subplan SP-1 · Plans section: look at and compare the four plans (informative) · covers R1, R2, R3 · UI contract
`planes@v1` (design T1.1, visual review T1.6) · integration T1.5 · audit T1.7 · produces `plan-catalogue@1` (T1.2).

- [ ] T1.1 — Copy the owner-approved planes@v1 contract into the repository · repo: pictures · verify: `test -s design/contracts/planes@v1.md` · files: design/contracts/planes@v1.md · resources: design:planes@v1 · covers: R2 · kind: design · subplan: SP-1 · ui: no
- [ ] T1.2 — Plan catalogue: the four plans, prices, tools and limits in one module · repo: pictures · verify: `npx tsx scripts/test/test-catalogo-planes.ts` · files: src/lib/planes/catalogo.ts, scripts/test/test-catalogo-planes.ts · resources: contract:plan-catalogue · covers: R1 · kind: implement · subplan: SP-1 · ui: no
  - Inputs: plan ids `free`, `segundo`, `disenador`, `disenador-max` (internal, never shown); display names in ES and EN; `precioMensual {cop, usd}` (Free 0); ordered tool keys from the catalogue's own declared list (`chat-basico`, `contador-globos`, `chat-extendido`, `calculadora-costos`, `deteccion-estructuras`, `deteccion-globos-avanzada`, `taller-3d`, plus whatever the owner names for the second tier); limits as structured entries `{tool, amount, unit, period}` with ES/EN labels.
  - Invariants: exactly four plans in that order; the catalogue is the only place prices, names, tools and limits are written; tool keys are display keys, not REQ-021 permission keys (SP-2 maps them); load-time validation throws naming plan and field.
  - **Blocked by** inputs 1, 2, 3, 4 and 6: the module cannot be completed until the owner supplies them; the implementer must not fill any of them.
- [ ] T1.3 — Plans section page: compare the four plans from the catalogue · repo: pictures · after: T1.1, T1.2 · verify: `npx tsx scripts/test/test-ui-planes.ts` · files: src/app/planes/page.tsx, src/components/planes/ComparadorPlanes.tsx, src/components/planes/textos-planes.ts, scripts/test/test-ui-planes.ts · resources: contract:plan-catalogue, design:planes@v1 · covers: R2 · kind: implement · subplan: SP-1 · ui: yes
  - Renders only from `plan-catalogue@1`; strings outside the catalogue live in `textos-planes.ts` and are limited to the headings the approved contract fixes. No action buttons. Route `/planes` is a Planner technical default (assumption, revisable). Currency display follows input 10.
- [ ] T1.4 — Entry points and access rule of the plans section, and its browser check script · repo: pictures · after: T1.3 · verify: `npx tsx scripts/test/test-ui-planes-entrada.ts` · files: src/proxy.ts, src/lib/cuentas/mapa-rutas.ts, scripts/test/test-proxy-matcher.ts, src/app/login/page.tsx, src/components/ui/shell/CabeceraApp.tsx, scripts/test/test-ui-planes-entrada.ts, scripts/test/test-integracion-planes.ts · resources: contract:permission-map, design:planes@v1 · covers: R3 · kind: implement · subplan: SP-1 · ui: yes
  - **Blocked by** input 5 (audience, entry points) and by REQ-021 SP-1 on main. Public: add the route to the guard's public list and a case to `test-proxy-matcher.ts`. Signed-in only: declare it in REQ-021's route map. Only the entry points recorded in SPEC get a link. Also authors `scripts/test/test-integracion-planes.ts` (next build + next start, Playwright, 390 and 1280 px, writes `.evidence/REQ-022/SP-1.integration.json`).
- [ ] T1.5 — Production-build browser check of the plans section · repo: pictures · after: T1.4 · verify: `npx tsx scripts/test/test-integracion-planes.ts` · files: .evidence/REQ-022/SP-1.integration.json · resources: port:3000 · covers: R2, R3 · kind: test · subplan: SP-1
  - If the owner makes the section signed-in only, this check also needs `PICTURES_REQ021_DATABASE_URL` and a REQ-021 test account; the `requires` list is added then.
- [ ] T1.6 — SP-1 visual review against the planes@v1 contract · repo: pictures · after: T1.5 · verify: `bitacora.py audit-ledger check .evidence/REQ-022/SP-1.visual.findings.json` · files: .evidence/REQ-022/SP-1.visual.md, .evidence/REQ-022/SP-1.visual.findings.json · resources: ledger:SP-1-visual · covers: R2 · kind: audit · subplan: SP-1
- [ ] T1.7 — SP-1 audit: catalogue data, section copy and access rule · repo: pictures · after: T1.6 · verify: `bitacora.py audit-ledger check .evidence/REQ-022/SP-1.findings.json` · files: .evidence/REQ-022/SP-1.audit.md, .evidence/REQ-022/SP-1.findings.json · resources: ledger:SP-1 · covers: R1, R2, R3 · kind: audit · subplan: SP-1

### M2 — Access by plan, Free limits and plan awareness
Skeleton only: outcome, covers and UI block; tasks are written when each subplan is in focus and its questions are
answered. Each consumes `plan-catalogue@1` after SP-1's audit (a composition gate per consumer is added with the tasks).

- **SP-2 — Access by plan: each account reaches exactly its plan's tools** · covers R4 · no UI of its own. Maps the
  catalogue tool keys onto REQ-021 permissions and makes the account's plan grant them on the server. **Blocked by**
  open question 3 (tiers replace Plan 1/2/3 as roles, extend them, or live apart) and 5 (new permission keys for
  extended chat, structure detection, advanced balloon detection only if those tools exist). If tiers are roles, the
  administrator assigns them in the REQ-021 SP-2 screens and no new UI is needed; if they live apart, a UI subplan is
  added.
- **SP-3 — Free plan limits** · covers R5 · UI contract `limites-free@v1`. **Blocked by** open question 1 (limit units,
  values, period, behavior at the limit); likely consumes the REQ-021 SP-6 per-user usage records (decided in focus).
  REQ-021 states «No caps or blocking in this plan» for AI spend; Free usage limits are a different rule owned here.
- **SP-4 — Plan awareness: current plan marked and locked tools name their plan** · covers R6, R7 · UI contract
  `plan-en-uso@v1`. **Blocked by** open questions 3 and 4; consumes SP-2 (the account's plan) and SP-1 (section).
- **Conditional (not in PLAN.json): plan action** — only if open question 2 is «request» or «purchase». «Request»:
  the person asks for a plan and an administrator sees it and assigns it. «Purchase»: payment provider, currencies,
  trial, cancellation and webhooks, with its own inputs round (credentials by location only).

## Open question → subplan blocking
| Question | Blocks |
|---|---|
| 1 Second tier contents and Free limits | SP-1 (T1.2 data), SP-2, SP-3 |
| 2 Informative, request or purchase | only the conditional plan-action subplan (SP-1 is informative by owner instruction) |
| 3 Mapping to REQ-021 roles | SP-2, SP-4 |
| 4 Audience and location | SP-1 (T1.4, T1.5), SP-4 |
| 5 Do the Designer tools exist | SP-1 (T1.2 tool list and "not available yet" state), SP-2 |
| 6 Pilot timing | ordering of all subplans against REQ-021 |
| 7 Designer Max price (new) | SP-1 (T1.2) |
| 8 Cumulative plans (new) | SP-1 (T1.2), SP-2 |
| 9 COP / USD display (new) | SP-1 (T1.3) |

## Review focus
Five likeliest uncovered input classes, each with its owning test:
1. A plan with a missing price, name or tool, or an unknown tool key → T1.2 `test-catalogo-planes.ts` (load fails naming plan and field).
2. A price retyped in the page instead of read from the catalogue → T1.3 `test-ui-planes.ts` (changed catalogue value appears).
3. Copy beyond names, prices, tools, limits and contract headings (invented marketing) → T1.3 `test-ui-planes.ts` and T1.7 audit.
4. The new route opening other routes without a session → T1.4 `test-proxy-matcher.ts` regression.
5. Phone width overflow and focus order → T1.5 `test-integracion-planes.ts`.

## Proposals for REQ-021 (not applied; REQ-021 untouched)
- Remove the plan rail («Cada persona. Sus herramientas.», `.rail`/`.plan-lines` in `design/cuentas-admin@v1.md`) from SP-2's contract, as the owner asked; the plans section lives in REQ-022 SP-1.
- If open question 3 is answered «the four tiers replace Plan 1/2/3», REQ-021 R16, round 6 and T1.2's five system roles (`src/lib/cuentas/permisos.ts`) need a revision so both requirements do not define plans twice.

## Semantic self-review (same context, not an independent approval)
- SP-1 is coherent and independent of questions 2 and 3; its data (T1.2) and placement (T1.4) are honestly blocked.
- Fake independence risk: T1.4 edits `src/proxy.ts`, which REQ-021 T1.4 rewrites; ordering after REQ-021 SP-1 is required, not optional.
- Estimates are uncalibrated agent guesses; `plan-json history` has no comparable samples.
