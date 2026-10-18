---
id: REQ-018
status: draft
created: 2026-10-18
execution_contract: requirements-v1
---
# REQ-018 — Category-based recommendations of assembled decorations

Draft **v2** for owner review; unapproved and unfrozen. Schema 1.2.0 contract revision stays **1**: the replaced draft was never frozen canonically. The external frozen simulation and `artifacts/REQ-018-replan-20261018/before` remain historical immutable evidence, not an approved execution revision. SPEC workflow metadata is retained. Only SPEC.md, PLAN.md and PLAN.json are rewritten; coordinator owns rounds/bitácora/state. No implementation, Git mutation, hook, M1/M2 simulation or runtime action is authorized here.

## Scope and evidence

Deliver category-only discovery in `/asistente` and its current gallery, using all complete visible guided ideas including single structures. Enforce strict actual category/refinement matches and honest zero results; preserve explicit intent, selected design and current plan. Reflect source additions/modifications through existing publication/build/deploy, without an admin, separate catalogue/cache, runtime refresh, new provider or REQ-017 integration. SPEC Matching and decision contract is normative; task descriptions below specify ownership and verification rather than repeating its whole rule set.

Reinspected `/home/david/dev/pictures` at HEAD `5f9104980d31e0074c6bbb5ed16cae1e8c92a723`, 197 dirty entries. Library remains 46 total / 31 visible / 23 single-quantity ideas. Read the applicable instructions, memory/index/pitfalls, confirmed rounds, current summary/pending and relevant decisions; inspected library/schema/loading/publication, route tools/provider setup and SSE, response/prompt/options, intent/facts, v1 contracts, UI/session widgets, package scripts and focused regression/browser precedents. Wider catalogue and REQ-017 research E8-E14 remains historical in SPEC; no isolated worktree code is assumed available.

Observed defects shaping the plan: legacy category affinity and padding (`biblioteca.ts:40-50,138-223`, `ideas-guiadas.ts:83-122,190-208`); category+theme gate and independent browse/final fallbacks (`route.ts:301-334,448-477,583-609`); contradictory empty sanitation/stream state (`respuesta-guiada.ts:287-420`); replacement brief semantics and dropped empty arrays (`VistaGuiada.tsx:721-728`); active selection scans (`VistaGuiada.tsx:2238-2248`) and strict session schemas (`estado-guardado.ts:8-62`, `widgets.ts:18-20`). Source JSON is statically loaded/validated and normally published, not polled.

Responsibility evidence: actual `_KINDS` mapping in `skill/scripts/bt_role_policy.py:11,36-39` routes implement/test/audit to implementation/command execution/review roles; `skill/agents/runner.md:21-27` disallows code fixes and configuration changes. These facts determine task kinds, never execution assignments. The corrected private WBS/semantic-review resources require comparison with the adjacent higher complexity level; all eight tasks do that in classification_evidence.

Harness feasibility is bounded: real VistaGuiada bundled in memory with esbuild (write:false; 6,299,698 bytes; exit 0), and `/usr/bin/chromium` exists. Default Playwright executable was absent. The existing hoja-armado browser test accepts PLAYWRIGHT_CHROMIUM_EXECUTABLE. No browser/harness behavior was executed; T5 owns constructing that harness and reporting launch/stubbing failures. No genuine feasibility unknown justifies a research-only predecessor.

## Milestones and tasks

### M1 — Strict matching and turn policy

Milestone acceptance:

- Category-only queries return only complete eligible matches, with no padding and with source-derived additions/modifications reflected in controlled inputs.
- Turn precedence and partial-brief decisions pass deterministic positive, negative and existing-plan cases without effects.

- [ ] T1 — Strict catalogue matching · repo: pictures · covers: R1, R2, R3, R4 · kind: implement

Implement SPEC rules 1-5 in a pure strict query with a visible-library adapter. Category comes from `eventos`, current labels and genuine same-celebration aliases; retain unrelated legacy search contracts. Apply all supported positive/negative preferences before ID/title deduplication and six-result cap. No minimum, inferred motif/colour, whitelist or second cache. Fixtures cover same-colour wrong events, bautizo versus comunión, tones, unknown positive styles, literal exclusions, age/gender, seasonal motifs and successive new/modified/hidden records. Update only contradictory guided padding assertions; preserve fidelity and independent photo/no-repeat regressions.

Expected change paths: `src/lib/biblioteca-sempertex/categorias.ts`, `src/lib/biblioteca-sempertex/recomendaciones-categoria.ts`, `src/lib/biblioteca-sempertex/biblioteca.ts`, `src/lib/ia/guiado/ideas-guiadas.ts`, `scripts/test/test-recomendaciones-categoria.ts`, `scripts/test/test-ideas-boda-guiada.ts`. Shared resources: strict-category-matching.

Acceptance and planned checks (not current proof):

- Controlled matcher tests pass for category-only, all positive and negative explicit preferences, unknown theme, sparse/empty, identity, motif, tone/age/gender and successive source additions/modifications without fixed IDs or cross-celebration aliases. functional/command: `node --import=tsx scripts/test/test-recomendaciones-categoria.ts`; created by T1 (future work)
- Wedding regression passes with only matching designs while literal customer-theme fidelity and independent photo helper invariants remain covered. regression/command: `node --import=tsx scripts/test/test-ideas-boda-guiada.ts`
- Existing lower-level legacy search regression passes for other consumers without becoming a fallback for active-category recommendations. regression/command: `node --import=tsx scripts/test/test-busqueda-biblioteca-sempertex.ts`

Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; 140 provisional minutes. Estimate breakdown and typed evidence: PLAN.json.

- [ ] T2 — Discovery turn decisions · repo: pictures · after: T1 · covers: R1, R3, R5 · kind: implement

Implement SPEC rules 6-8 as a pure typed decision over validated messages, partial brief, visible candidates and existing intent facts. Respect explicit actions first; resolve the latest affirmative category and refinements, reject negated/ambiguous guesses, and return empty for an unsupported replacement rather than the stale category. Retain unrelated customer fields and explicit preferences until changed/removed. Output suppressed/unknown-or-ambiguous/matching/empty, a reason, actual records and the full resolved validated partial snapshot; no effects. Category alone remains sufficient; no fabricated age/theme placeholder.

Expected change paths: `src/lib/ia/guiado/turno-recomendaciones.ts`, `scripts/test/test-turno-recomendaciones.ts`. Shared resources: discovery-turn-outcome.

Acceptance and planned checks (not current proof):

- Turn tests pass for explicit-action precedence, category-only brief, latest affirmative or unsupported replacement, negation/ambiguity, retained and removed preferences, complete resolved partial snapshot and immutable plan/selection with zero effect calls. functional/command: `node --import=tsx scripts/test/test-turno-recomendaciones.ts`; created by T2 (future work)
- Existing v1 request tests accept partial briefs and retain deliberate invalid-input and explicit-action validation. regression/command: `node --import=tsx scripts/test/test-asistente-guiado-contrato.ts`

Classification: complexity high; scope small_change; risk medium; coupling high; confidence medium; 120 provisional minutes. Estimate breakdown and typed evidence: PLAN.json.

### M2 — Guided response and API integration

Milestone acceptance:

- Actual validated SSE publishes same-turn strict matching or honest empty data with category alone.
- Stream/final text, tools, browse/photo-suggestion branches and sanitation cannot reintroduce generic alternatives or intercept explicit actions.

- [ ] T3 — Honest matching and empty responses · repo: pictures · after: T2 · covers: R1, R3, R5, R6 · kind: implement

Implement the presentation side of SPEC rules 8-10: one response policy over T2 outcomes, aligned with prompt, option validation, sentence stream filter and final sanitation. Matching/empty use deterministic truthful text; suppressed intentional flows retain their existing text. No optional-question prerequisite or automatically offered alternative on empty. Where a model/tool path can still resolve discovery, prevent category recommendation claims/options from escaping before its strict outcome is known; fragmented sentences/options and final fallback must never add or temporarily announce ineligible designs. Preserve unrelated age/city/action options. Author split-chunk, late-outcome and suppressed-context tests, and replace conflicting fallback expectations with strict equivalents.

Expected change paths: `src/lib/ia/guiado/respuesta-recomendaciones.ts`, `src/lib/ia/guiado/respuesta-guiada.ts`, `src/lib/ia/guiado/prompt-guiado.ts`, `src/lib/ia/guiado/opciones-catalogo.ts`, `scripts/test/test-respuesta-recomendaciones.ts`, `scripts/test/test-respuesta-guiada-sin-fracaso.ts`, `scripts/test/test-cambio-tematica-guiada.ts`, `scripts/test/test-opciones-catalogo-guiado.ts`. Shared resources: discovery-response-policy.

Acceptance and planned checks (not current proof):

- Response tests pass for matching/empty, fragmented chunks, options split across chunks and outcome updates after tool completion; streamed and final claims agree without padding, compulsory questions or changed suppressed-action text. functional/command: `node --import=tsx scripts/test/test-respuesta-recomendaciones.ts`; created by T3 (future work)
- Response regressions pass with strict honest-empty assertions replacing category fallback assertions while unrelated flow safeguards remain covered. regression/command: `node --import=tsx scripts/test/test-respuesta-guiada-sin-fracaso.ts`
- Theme-change regressions pass without typical-colour suggestions for an absent theme and preserve literal customer preferences. regression/command: `node --import=tsx scripts/test/test-cambio-tematica-guiada.ts`
- Option regressions pass without generic category fill while unrelated age/city/flow options remain unchanged. regression/command: `node --import=tsx scripts/test/test-opciones-catalogo-guiado.ts`

Classification: complexity high; scope small_change; risk medium; coupling high; confidence medium; 160 provisional minutes. Estimate breakdown and typed evidence: PLAN.json.

- [ ] T4 — Integrate category discovery into the guided API · repo: pictures · after: T3 · covers: R1, R2, R3, R4, R5, R6 · kind: implement

Integrate T1-T3 into the actual POST route as thin validated adapters under SPEC rules 6-10. After existing action/selection/photo/proposal guards, resolve matching/empty before provider initialization and use existing rule-only texto/fin SSE. Tool declarations and argument validation permit category without theme; operations needing a complete brief keep their validation. Search, category/theme change, browse, photo-suggestion and final fallback consume the same strict rule. Publish actual records or explicit [], and the full partial snapshot; never replace known fields with an event-only delta. Preserve deliberate errors, request/correlation IDs, access/audit boundaries and existing deadlines. Build the actual-handler harness with controlled provider/catalogue/effect doubles, not merely source-text assertions. Test validation, all recommendation entry paths, fragmented SSE and action suppression; any unintended provider/quote/image/proposal call fails.

Expected change paths: `src/app/api/asistente-guiado/route.ts`, `src/lib/ia/guiado/pedido-ideas.ts`, `scripts/test/test-ruta-recomendaciones-categoria.ts`. Shared resources: guided-recommendation-sse-v1.

Acceptance and planned checks (not current proof):

- Actual-handler tests pass for same-turn category-only/empty SSE, authoritative source updates, tool/browse/photo-suggestion strictness, partial brief, invalid inputs and explicit-action suppression with zero external discovery calls. integration/command: `node --conditions=react-server --import=tsx scripts/test/test-ruta-recomendaciones-categoria.ts`; created by T4 (future work)
- Existing v1 contract tests pass with no new wire field/version or weakening of complete-brief validation. regression/command: `node --import=tsx scripts/test/test-asistente-guiado-contrato.ts`
- Existing plan edit and explicit idea-selection regressions pass without browsing side effects. regression/command: `node --import=tsx scripts/test/test-edicion-plan-chat-guiada.ts`

Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; 180 provisional minutes. Estimate breakdown and typed evidence: PLAN.json.

### M3 — Gallery compatibility and verification

Milestone acceptance:

- Live and restored gallery preserve authoritative identity, an explicit empty boundary and the selected idea/current plan without new session fields.
- Producer tests and separate package registration exist; command execution records actual outcomes without repairs or acceptance judgment.
- A distinct audit responsibility evaluates R1-R6, AC1-AC9 and IF-1..IF-4 against observed evidence, reporting any failure or blocker without owner approval.

- [ ] T5 — Preserve gallery identity and empty-turn selection · repo: pictures · after: T4 · covers: R1, R2, R3, R5, R6 · kind: implement

Implement SPEC rules 8-10 in the actual VistaGuiada and existing gallery. A present [] is an already-valid empty decoration widget boundary; an absent field means no discovery update. Persist that boundary, render no empty-card alternatives and stop backward textual-selection scans at it. Preserve selected design, plan, approval context and explicit selection actions. Historical cards stay historical. Trace hydration-before-save, retry removing/replaying the latest turn, selection restoration, old sessions without the boundary and newer sessions containing it.

Build `scripts/test/test-ui-recomendaciones-categoria.ts` and its `fixtures/recomendaciones-categoria-ui/arnes.tsx` in this implementation task. Bundle the real view/gallery using the inspected esbuild/Playwright precedent; controlled SSE and session fixtures must exercise real handling/selection, not a copied reducer. Block unexpected network including quote/image/model effects, stub photos and unrelated API reads, seed old/current selected-plan sessions, then test zero/one/many, absent versus [], keyboard/button choice, reload and failed-turn retry at desktop and narrow viewport. Use the existing executable-path option; report launch/environment blockers without skip or invented success. Do not add a runtime dependency or change production UI to make the harness work.

Expected change paths: `src/components/guiado/VistaGuiada.tsx`, `src/components/guiado/CarruselDecoraciones.tsx`, `scripts/test/test-ui-recomendaciones-categoria.ts`, `scripts/test/fixtures/recomendaciones-categoria-ui/arnes.tsx`. Shared resources: guided-recommendation-sse-v1, guided-session-widgets.

Acceptance and planned checks (not current proof):

- Controlled full-view browser tests pass at desktop/narrow widths for zero/one/many identities, keyboard/button choice, absent versus empty updates, persisted empty widgets, next-request ideasMostradas and retry/restore with unchanged plan/selection and blocked unexpected network. integration/command: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium node --import=tsx scripts/test/test-ui-recomendaciones-categoria.ts`; created by T5 (future work)
- Existing saved-session regression passes with old sessions and explicit-action restoration intact. regression/command: `node --import=tsx scripts/test/test-sesion-guardada-accion-idea.ts`

Classification: complexity high; scope small_change; risk medium; coupling high; confidence medium; 220 provisional minutes. Estimate breakdown and typed evidence: PLAN.json.

- [ ] T6 — Register category regression commands · repo: pictures · after: T5 · covers: R6 · kind: implement

Only package-script registration is owned here. Add the T1-T4 new and affected existing scripts named in the static registration check to guiada:test, retain every existing entry and correct React conditions, and add guiada:test-recomendaciones-ui for T5 separately from the default deterministic suite. Preserve unrelated dirty package edits. Tests/fixtures and fixes remain with T1-T5; no acceptance judgment belongs here.

Expected change paths: `package.json`. Shared resources: guided-test-registration.

Acceptance and planned checks (not current proof):

- Package registration adds T1-T4 new and affected existing deterministic scripts to guiada:test and a separate provider-free guiada:test-recomendaciones-ui entry for T5, preserving existing entries and required React conditions. static/command: `node -e "const p=require('./package.json'); for(const n of ['test-recomendaciones-categoria.ts','test-turno-recomendaciones.ts','test-respuesta-recomendaciones.ts','test-ruta-recomendaciones-categoria.ts','test-ideas-boda-guiada.ts','test-busqueda-biblioteca-sempertex.ts','test-respuesta-guiada-sin-fracaso.ts','test-cambio-tematica-guiada.ts','test-opciones-catalogo-guiado.ts','test-asistente-guiado-contrato.ts']) if(!p.scripts['guiada:test'].includes(n)) throw Error(n); if(p.scripts['guiada:test-recomendaciones-ui']!=='node --import=tsx scripts/test/test-ui-recomendaciones-categoria.ts') throw Error('UI script mismatch')"`

Classification: complexity low; scope small_change; risk low; coupling medium; confidence medium; 25 provisional minutes. Estimate breakdown and typed evidence: PLAN.json.

- [ ] T7 — Run established verification commands · repo: pictures · after: T6 · covers: R1, R2, R3, R4, R5, R6 · kind: test

Run the listed established commands after producer-local checks and registration. Return concise exit codes, exact failing assertions/paths and warnings or environment blockers. Do not author tests/config, classify causes, repair, weaken assertions, install dependencies, regenerate goldens or judge feature acceptance. Record any skipped/unavailable command as blocked; T8 distinguishes regression from pre-existing/environment debt using evidence. A failed check is never feature PASS.

Expected change paths: none; report-only responsibility. Shared resources: guided-test-registration, verification-results.

Acceptance and planned checks (not current proof):

- Lint command outcome is recorded with exit code and relevant diagnostics. static/command: `npm run lint`
- Workspace build command outcomes are recorded before application types. static/command: `npm run build --workspaces --if-present`
- Application type-check outcome is recorded with exact failures. static/command: `npx tsc --noEmit`
- Registered guided regression outcome is recorded including the new deterministic cases. regression/command: `npm run guiada:test`
- Actual-handler SSE integration outcome is recorded without live providers. integration/command: `node --conditions=react-server --import=tsx scripts/test/test-ruta-recomendaciones-categoria.ts`; created by T4 (future work)
- Controlled browser integration outcome is recorded or explicitly blocked by environment. integration/command: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run guiada:test-recomendaciones-ui`; created by T6 (future work)
- Application build outcome is recorded without deployment or runtime changes. static/command: `npm run build`
- Whitespace-check outcome is recorded without any Git mutation. static/command: `git diff --check`

Classification: complexity low; scope small_change; risk low; coupling medium; confidence medium; 90 provisional minutes. Estimate breakdown and typed evidence: PLAN.json.

- [ ] T8 — Review integration and product acceptance evidence · repo: pictures · after: T7 · covers: R1, R2, R3, R4, R5, R6 · kind: audit

Review the consolidated producer diff and T7 results against every interface and SPEC AC1-AC9. This responsibility is distinct from T1-T6 production and T7 command execution. Examine actual browser evidence at desktop/narrow viewport and keyboard/button paths, not a test-count summary; identify unavailable product evidence as blocked. Check catalogue authority/publication lifecycle, strict matching and empty behavior, complete partial snapshot, explicit action/selected-plan preservation, old/new sessions and wire compatibility. Review boundaries/imports, duplicated IDs/taxonomy/cache, secret/provider access, accidental REQ-017 coupling and unrelated dirty changes. Interpret failures with baseline evidence; return bounded findings to the responsible producer through the existing workflow, without taking repair or approval authority. No owner approval is inferred from a clean audit.

Expected change paths: none; report-only responsibility. Shared resources: strict-category-matching, discovery-turn-outcome, discovery-response-policy, guided-recommendation-sse-v1, guided-session-widgets, verification-results.

Acceptance and planned checks (not current proof):

- Integration review traces IF-1 through IF-4 across actual producer/consumer diffs and command evidence, with each criterion accepted, failed or blocked and missing evidence explicit. integration/manual: `Inspect IF-1..IF-4 producer and consumer diffs alongside actual SSE/browser evidence from T7`; expected: Every declared integration criterion has observed supporting evidence or an explicit failure/blocker; suite success alone does not establish integration acceptance.
- Product review traces R1-R6 and AC1-AC9 to observed behavior including desktop/narrow keyboard use, strict empty/source lifecycle and unchanged explicit actions, plan, selection and old sessions; scope and compatibility findings remain explicit. product/manual: `Review SPEC AC1-AC9 evidence, desktop/narrow browser behavior and scoped diff for R1-R6`; expected: Only actual matches; source-driven updates via normal publication; no stale active cards, silent plan/selection changes, new cache/DTO, hidden paid calls or REQ-017 imports. Report unmet criteria; review does not grant owner approval.

Classification: complexity high; scope small_change; risk medium; coupling high; confidence medium; 75 provisional minutes. Estimate breakdown and typed evidence: PLAN.json.

## Dependencies and interfaces

DAG: `T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8`. M1 produces matching/turn decisions; M2 integrates response/API; M3 implements gallery/session behavior and separates registration, command evidence and acceptance interpretation. Dependencies consume concrete predecessor outputs; T6 consumes producer test commands, T7 needs registration, and T8 needs observed results. Shared paths/resources are ordered. No dependency on REQ-017, external simulation or a future approval artifact; no execution assignment or concurrency guarantee. A second graph artifact adds no value to this chain.

**IF-1 — Strict category catalogue query**. Owner: Guided-library matching domain (T1). Producer T1; consumers T2, T3, T4; integration evidence review T8. T7 runs integration commands; T8 judges the declared criteria and is neither producer nor consumer.

- inputs: Validated visible library records, customer category, optional explicit refinements, current catalogue event labels.
- outputs: Stable ordered actual design records, zero to six, with preserved identity and no approximate fill.
- invariants: Only current visible eligible records; no fixed ID/category whitelist or extra cache; Known category is required; absent refinements are unconstrained and supplied preferences are conjunctive; Source edits arrive through normal publication/build/deploy; injected successive inputs prove derivation, not runtime hot reload; Aliases equate only the same celebration; broad legacy affinity groups cannot introduce a cross-event match.
- integration_criteria: Category-only route and option queries call the same predicates; Thin/empty and new/modified-source cases retain their exact result membership through route integration.

**IF-2 — Read-only discovery turn outcome**. Owner: Guided application turn policy (T2). Producer T2; consumers T3, T4; integration evidence review T8. T7 runs integration commands; T8 judges the declared criteria and is neither producer nor consumer.

- inputs: Validated customer messages/partial brief and existing explicit action facts; Current validated visible catalogue through IF-1.
- outputs: Suppressed, unknown/ambiguous, matching or empty outcome with reason, resolved partial-brief snapshot and actual design records.
- invariants: No plan/selection mutation and no provider calls; Latest affirmative unambiguous customer category beats stale brief; explicit action precedence wins over automatic discovery; Explicit unsupported category replacement never reuses stale category; resolved partial-brief snapshot retains unrelated confirmed fields.
- integration_criteria: Actual route dispatch preserves all explicit-action branches and produces category-only data in the same response; Empty and matching outcomes are authoritative and cannot be replaced by model/generic fallback.

**IF-3 — Discovery response policy**. Owner: Guided response layer (T3). Producer T3; consumers T4, T5; integration evidence review T8. T7 runs integration commands; T8 judges the declared criteria and is neither producer nor consumer.

- inputs: Typed IF-2 outcome and customer-visible category/preferences.
- outputs: Short matching or honest empty text; no automatic alternative/compulsory clarification for empty.
- invariants: Stream chunks and final text agree on which designs exist; Suppressed turns preserve existing intentional flow text.
- integration_criteria: Handler uses deterministic discovery text before provider initialization; Sanitation/options and model-tool paths never turn empty into generic alternatives.

**IF-4 — Existing v1 SSE and gallery empty boundary**. Owner: Guided API adapter (T4) and gallery state consumer (T5). Producer T4; consumers T5; integration evidence review T8. T7 runs integration commands; T8 judges the declared criteria and is neither producer nor consumer.

- inputs: Validated IF-2/IF-3 result and request/correlation IDs.
- outputs: Existing texto/fin SSE; result.brief partial and result.decoraciones actual records or explicit [].
- invariants: No new wire/session fields or versions; Empty array persists as existing decoration widget boundary; missing field means no discovery update; Selected idea and plan unchanged until explicit existing actions; result.brief is the resolved validated partial snapshot, consistent with VistaGuiada setBrief replacement semantics.
- integration_criteria: Real gallery receives zero/one/many actual records without copied sources; After empty result and reload/retry, ideasMostradas excludes older transcript candidates; old sessions remain readable.

## Traceability

| Requirement | Producer path | Acceptance | Verification and review |
|---|---|---|---|
| R1 category-only | T1→T2→T3→T4→T5 | AC1,2,8,9; M1-M3 | matcher/turn/response functional; SSE/browser integration; T7 runs, T8 reviews |
| R2 actual complete designs | T1→T4→T5 | AC1,2,5,9 | identity/source fixtures; actual records/photo/gallery; T8 product review |
| R3 strict thin/empty | T1→T2→T3→T4→T5 | AC2,3,4,6,8 | positive/negative/unknown prefs; split stream/options; empty persistence and next request |
| R4 source changes | T1→T4 | AC5 | successive fixture inputs, authoritative adapter, T8 publication/build lifecycle review |
| R5 explicit actions/compatibility | T2→T3→T4→T5 | AC3,6,7,8,9 | effect spies; edit/selection regressions; old/new session, retry/restore and full partial snapshot |
| R6 coherent system/evidence | T3→T4→T5→T6→T7→T8 | AC1,4,6,7,9 | static, functional, integration, regression commands and separate product judgment |

Every numbered requirement has producing work, dependent integration, acceptance cases and categorized checks; T6 covers R6 registration and T7/T8 cover observed evidence for R1-R6. All four interfaces have a distinct integration owner. Planned command coverage and green legacy suites do not establish product acceptance.

## Old-to-new mapping and calibration

| Archived task | V2 responsibility | Complexity decision |
|---|---|---|
| T1 matcher | T1, with its focused tests | medium retained: known pure conjunction/filter/dedupe rules and fixtures; higher state/integration work is explicitly elsewhere |
| T2 turn policy | T2, with precedence and snapshot tests | high retained: decisions cross action guards, stale/unsupported replacement and customer facts; no exceptional architecture to justify extreme |
| T3 responses | T3, with stream/options/final tests | medium→high: mutable context, sentence buffering and tool/final sanitizers can disagree; a typed outcome alone does not remove that reasoning |
| T4 route | T4, including actual-handler test authoring | high retained: several entry paths, provider-before-return and SSE validation; fixed contracts bound the adjacent extreme level |
| T5 gallery/session | T5, including full-view browser harness construction | medium→high: live→persisted→restored/retried transitions and active textual selection; no data migration/new architecture, so not extreme |
| T6 script registration | T6 implement | low: additive existing command wiring; no harness or test design hidden here |
| T6 suite running | T7 test | low: run/report exactly; execution time does not imply complex reasoning |
| T6 triage + acceptance | T8 audit interprets/locates findings; owning producer repairs through existing workflow | high: cross-contract/product reasoning across stream and persistence; no repair authority in T7/T8 |

Scope, risk, coupling and duration are separate axes. T3/T5 stay small_change because the responsibility is a bounded existing layer; high reasoning does not mean a new full system. T4 stays large_change due to multiple existing entry/fallback branches and actual-handler harness. T3/T5 coupling becomes high because outcome timing/SSE/session consumers interact, not because their estimates grew. Risk remains medium for behavior/compatibility inside unchanged validated schemas and no migration/payment/access change. Confidence remains medium: code and seams were inspected, future harnesses were not executed. Exact six-dimension typed evidence and adjacent-level rationale live in PLAN.json.

## Estimates and uncertainty

Reused unchanged historical queries from the archived draft: implement medium/small_change/medium/medium, high/small_change/medium/high and high/large_change/medium/high returned exit 0 and unknown comparable history. This supports no measured estimate; T3/T5 now use the already queried high/small_change/medium/high dimension, so it was not redundantly queried.

New read-only queries, each exit 0:

- `python3 skill/scripts/bitacora.py --project pictures plan-json history --kind implement --complexity low --scope small_change --risk low --coupling medium`
- `python3 skill/scripts/bitacora.py --project pictures plan-json history --kind test --complexity low --scope small_change --risk low --coupling medium`
- `python3 skill/scripts/bitacora.py --project pictures plan-json history --kind audit --complexity high --scope small_change --risk medium --coupling high`

All returned status unknown. Duration unit seconds, samples/median/range/source_quality unknown/null (`cross_route_duration_comparability_unproven`); consumption unit/samples/source quality unknown (`cross_provider_token_units_not_comparable`); quality and retries unknown with no usable samples. No measured quality, quota, consumption or simulation-based calibration is inferred. Required integer minutes are provisional engineering decompositions, including authoring and local verification; no dates or execution assignment are promised.

Task uncertainty: T1 lexical/negative preference fidelity; T2 intent precedence and customer replacement extraction; T3 split output and context changes; T4 actual-handler controlled doubles; T5 browser launch/network stubs plus restored-plan fixtures; T6 preserving dirty package scripts; T7 environment/build duration; T8 sufficiency of observed evidence. All are bounded implementation/verification risks, not missing owner product decisions. If actual feasibility contradicts the inspected seams, report it and revise the affected draft scope/estimate before taking unrelated work.

## Risks and compatibility

- Preserve legacy helper consumers through a strict boundary; broad aliases such as bautizo/comunión cannot be used as equivalence. Tests must retain motif, customer fidelity, tones, no-repeat and explicit-action protections.
- Model/option/sanitation fallback must not fill empty results or leak nearby recommendations in stream chunks. T3 defines policy, T4 owns real dispatch tests, T8 reviews combined evidence.
- Empty-array widgets already validate under the saved strict schema. Distinguish absent from []; retain this boundary through save/reload/retry while leaving selected design, plan and approval context intact. Do not add fields requiring a reader-first migration or fabricate missing old-session history.
- Public v1 request/SSE/record/session contracts remain. Consumers are tool registration, route, live view and saved-state reader. Rollback later restores scoped code/previous policy without migration; no rollback/deployment is performed by this draft.
- Source changes propagate through normal publication/build/deploy. Injected additions/modifications prove derivation, not production refresh or hot reload. Known saved-plan purchase drift remains out of scope.
- Dirty canonical and REQ-017 worktrees are preserved; no imports from isolated REQ-017 helpers. Later combination of shared-route changes needs its own integration review.
- Browser executable is an execution-environment dependency, not a new runtime dependency. Missing launch support or required evidence must be reported blocked; no auto-install, unhandled provider request, skip or fabricated PASS.

## Validation performed during planning

Current observed baseline, not feature acceptance:

- `node --import=tsx scripts/test/test-busqueda-biblioteca-sempertex.ts` in Pictures: exit 0, legacy behavior.
- `node --import=tsx scripts/test/test-ideas-boda-guiada.ts` in Pictures: exit 0, legacy fidelity/padding/photo assertions. --import=tsx is actually executed and avoids P-117 operand misparsing.
- In-memory esbuild of actual VistaGuiada: exit 0, 6,299,698 bytes; default Playwright executable absent; system Chromium path exists. No browser launched. Newly authored tests, registrations and all implementation checks above remain future work.
- Read-only catalogue/status inspection reconfirmed 46/31/23 and unchanged baseline HEAD/197 entries. No application lint/types/full-suite/build or product model/image call executed in planning.

Actual checks after writing the draft:

1. From `/home/david/dev/metodologia`: `PYTHONPATH=skill/scripts python3 -m bt_planner check bitacora/pictures/requirements/REQ-018-category-based-recommendations-of-assemb --repo pictures=/home/david/dev/pictures --json` — exit **0**, `ok:true`, **0 errors, 9 warnings**. No failed v2 structural attempt preceded this result.
2. Canonical publication/evidence check, executed directly through the adapter without workflow CLI/hooks:

```python
# PYTHONPATH=skill/scripts python3 - (executed from methodology root)
from pathlib import Path
import bt_plan_adapter
rdir = Path('/home/david/bitacora/pictures/requirements/REQ-018-category-based-recommendations-of-assemb')
raise SystemExit(bt_plan_adapter.run_cli('check', rdir, as_json=True))
```

Exit **0**, `ok:true`, **0 errors, 9 warnings**. The adapter resolved the canonical requirement into this workspace and Pictures evidence to `/home/david/dev/pictures`; it verified command/precedent targets in addition to module/file/schema/graph checks. This is the real canonical publication check, not a standalone schema pass. It ran no approval/freeze/launch or workflow mutation.

3. Same direct adapter with `run_cli('report', rdir, as_json=True, emit=outputs.append)` — exit **0**. Report: 8 tasks, 3 milestones, 6 covered requirements, 4 interfaces, all tasks have evidence; no unordered conflicts/shared resources, redundant edges or unconsumed results. T8 is intentionally the sole task without command verification and has two NEEDS_REVIEW criteria. The reported 1,010-minute path is the sum of provisional estimates, not a measured forecast.

Nine warnings are retained deliberately: five producer `created_by` tests (T1-T5), two future command references in T7 (actual-handler test from T4 and browser registration from T6), and two manual integration/product criteria in T8. Future work is not current proof; manual review cannot produce automatic PASS. No check or warning threshold was weakened.

Final checks after semantic corrections: module check exit 0; canonical adapter check exit 0 (0 errors / same 9 warnings); adapter report exit 0 (8 tasks / 3 milestones / 6 requirements / 4 interfaces / 0 conflicts / 2 manual criteria). Scoped `git diff --check` exit 0. Requirement extraction confirms R1-R6 byte-for-byte unchanged; original workflow metadata is unchanged.

Preservation checks compare initial/final SHA-256 inventories: archived draft `12614cccbc68dac97cd0a42c34e38424edbf81c624fe12b92c87ccc93d4622c6`; rounds `f86fc8aa05b4c744f597a45b8d64de9a4483577e2cccd5a9a43013c255a1cda1`; external simulation `b7e912ee1863abbad524524527ff01567c27ea71b380a71a09ad0eba9efcc78d`. All unchanged. Pictures remains 197 entries with unchanged status SHA-256 `01570bf1df4bffb821aed8a2ae687867a1bb2302768e40b742ec38561c9ff82e` and dirty-content SHA-256 `e42de2b2120901b7ce498acb9470b2827ae871526cab9953a3a841828291c595`. No product/REQ-017 write was performed. Coordinator-owned files and frozen evidence were preserved.

## Adversarial semantic self-review

Performed **after** deterministic validation by this same Planner. This is a semantic self-review, not independent approval; the coordinator's independent reviews follow.

| Category / severity | Trigger and provenance | Bounded correction or retained constraint |
|---|---|---|
| Demonstrated defect / high, corrected | Archived T6 owns package changes, execution/triage and product judgment, but actual kind consumers map test to command-only Runner (`skill/scripts/bt_role_policy.py:11,36-39`; `skill/agents/runner.md:21-27`). | Registration is T6 implement, execution is T7 test, integration/product interpretation is T8 audit. Focused test and harness authorship stays in T1-T5. T7/T8 never silently acquire repair authority. |
| Plausible risk / high, corrected | Archived T3 medium reasoning cites existing branches but spans pending sentence/options state, tool changes and final fallback (`respuesta-guiada.ts:287-420`, `route.ts:563-609`). | T3 high explicitly owns chunk/context transition tests and policy alignment; T4 tests real SSE/guards; T8 reviews convergence. Adjacent extreme not justified by fixed contracts and no new architecture. |
| Plausible risk / high, corrected | Archived T5 medium includes restoration and an unbuilt full-view harness (`VistaGuiada.tsx:347-389,721-728,2238-2248`; `estado-guardado.ts:8-62`). | T5 high counts harness construction, hydration/save/retry/next-request and selected-plan fixtures. Static bundling proves only imports; browser behavior remains planned. No migration makes extreme inappropriate. |
| Fact / medium | Actual view bundles in memory, system Chromium exists, existing browser precedent supports executablePath (`test-hoja-armado-ui.ts:36-59`). Default Playwright executable is absent. | Keep confidence medium, explicitly use the supported system executable, block unexpected network and report launch failures. A research-only task would add no unresolved feasibility result at present. |
| Plausible risk / medium, corrected | Stale brief can win over new unsupported category; negative or unknown preferences can disappear into broad matching (`route.ts:420`; `ideas-guiadas.ts:190-208,224-237`). | SPEC rules 2-3,7 and T1/T2 cases preserve literal exclusions/unknown positive styles, full resolved partial brief and explicit replacement semantics; no cross-celebration affinity aliases. |
| Fact / medium | Empty response arrays are dropped and the view searches historical carousels (`VistaGuiada.tsx:728,2238-2248`); empty widgets already validate (`widgets.ts:18-20`). | T5 persists existing-schema [] boundary and tests live/restore/retry selection requests; no new widget field or selected-plan reset. |
| Plausible risk / medium | A passing suite or in-memory bundle can be mistaken for end-user acceptance; prior checks do not execute newly authored cases. | T7 reports outcomes only, T8 reviews each interface and AC1-AC9 including desktop/narrow behavior. Missing evidence stays blocked; no baseline means a failure cannot be labelled pre-existing without proof. |
| Product decision / binding | Confirmed owner Q1-Q5 and round-02 update answer select existing guided ideas, category-only discovery and strict zero/sparse behavior. | Preserve all six requirements and scope; no minimum fill, compulsory refinement, separate catalogue or runtime hot reload. No new product approval inferred. |

WBS responsibility check: every kind fits its deliverable; T6 is real package implementation, T7 has no code paths or diagnosis/repair/approval scope, T8 is review-only and distinct from every interface producer/consumer. Local tests remain with producers. Calibration check: T1 medium is bounded by fixed pure predicates, T2/T4 high remain justified, T3/T5 now account for state/verification reasoning, T6/T7 low remain routine, T8 high reflects cross-contract judgments. File count, time, risk and coupling are not substitutes for reasoning complexity. All classification dimensions have typed evidence; no prior simulation is used as difficulty or quality proof.

Traceability/graph check: R1-R6→tasks→milestone criteria→AC1-AC9→categorized checks are present, no orphan requirement/work or cycles, and integration owner T8 is distinct from consumers. Registration depends on tests, execution on registration, audit on observed outcomes. No missing blocking owner decision remains. Remaining launch/browser/build uncertainties are explicit, not silently accepted. Review identifies no unresolved scope or responsibility defect in this draft.
