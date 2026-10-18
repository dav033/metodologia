---
id: REQ-018
status: draft
created: 2026-10-18
execution_contract: requirements-v1
---
# REQ-018 — Category-based recommendations of assembled decorations

Draft for owner review; not approved, frozen or launched. Product decisions C1-C5/C2a in SPEC are confirmed; the plan itself has no approval. This planning session changes only SPEC.md, PLAN.md and PLAN.json. Round files, workflow state, bitácora, product code and isolated REQ-017 work remain coordinator-owned/untouched.

## Scope and inspected baseline

Deliver category-only discovery on `/asistente` using complete visible guided-library ideas and the existing gallery; enforce actual matches, honest empty results, customer intent and current-plan safeguards. Reflect source additions/modifications through normal publication/build/deploy without a second list/cache. No admin, acquisition pipeline, runtime hot reload, provider addition, product model/image calls, deployment or REQ-017 integration.

Inspected root: `/home/david/dev/pictures`, HEAD `5f9104980d31e0074c6bbb5ed16cae1e8c92a723`, 197 dirty entries. Read AGENTS/CLAUDE, current library/schema/search, guided turn/API/tool/prompt/stream sanitation, customer facts and edit intent, v1 request/SSE consumers, gallery/session/widgets, saved-plan contract, publication scripts/docs, package commands and affected deterministic/browser tests. Prior wider catalogue research E1-E14 is retained in SPEC as historical evidence. Project SUMMARY/PENDING/DECISIONS and relevant memory were read; checkout code governs branch availability.

Key facts: `biblioteca.ts` statically imports/validates the source and `bibliotecaVisible()` derives current visible records. There is no runtime refresh job. The route supplies real records; the sample-photo list is a separate picker. Existing complete-brief tool gate, approximate search/padding, photo/explicit-browse branches and final no-failure fallback all need scoped treatment. The v1 wire brief already permits missing theme. The UI currently adds a carousel only for a nonempty array, while `ideasALaVista` scans backwards to the last carousel: an explicit empty widget is needed to prevent stale textual choices after an empty turn, without adding session fields.

The future implementer must preserve all pre-existing work and use the supplied baseline, never reset/clean the shared tree or copy REQ-017 helpers. No branch/commit/deploy operation is part of these tasks. Library materials/saved-plan drift is recorded in project memory and outside this slice.

## Behavioral contract and ownership

SPEC Matching and decision contract rules 1-10 are normative for these tasks. In particular, category matches explicit event labels/known aliases, optional preferences are conjunctive and evidence-based, the upper limit is six with no minimum, and latest affirmative customer facts beat stale brief. Explicit action guards win over discovery. An empty discovery result is authoritative data and text, not an invitation to force a style question or approximate search.

Ownership below assigns files/responsibilities to task IDs, not execution agents. New paths are planned outputs; file evidence always names inspected existing files. No public DTO extension is planned: reuse partial `brief`, `decoraciones: []` and the already-supported empty decoration widget. Consumers are the guided route/tools, option/response validation, VistaGuiada, selection, session restore and existing plan actions. Preserve their v1 wire/session schema. A later rollback restores scoped implementation changes without data migration; it is not executed here.

## Milestones and tasks

### M1 — Strict matching and turn policy

Milestone acceptance:

- Category-only queries return only complete eligible matches, with no padding and with source-derived additions/modifications reflected in controlled inputs.
- Turn precedence and partial-brief decisions pass deterministic positive, negative and existing-plan cases without effects.

- [ ] T1 — Strict catalogue matching · repo: pictures · covers: R1, R2, R3, R4 · kind: implement · verify: `node --import tsx scripts/test/test-recomendaciones-categoria.ts`

Return only complete visible ideas satisfying category and explicit refinements, derived from the authoritative catalogue without padding or copied IDs.

Ownership / expected paths: `src/lib/biblioteca-sempertex/categorias.ts`, `src/lib/biblioteca-sempertex/recomendaciones-categoria.ts`, `src/lib/biblioteca-sempertex/biblioteca.ts`, `src/lib/ia/guiado/ideas-guiadas.ts`, `scripts/test/test-recomendaciones-categoria.ts`, `scripts/test/test-ideas-boda-guiada.ts`. Shared resources: `strict-category-matching`.

Acceptance:

- A pure matcher takes validated visible records and category/preferences as arguments; the application obtains bibliotecaVisible without a separate cache or ID whitelist. Source edits enter via normal publication and build/deploy, not runtime polling.
- Implement SPEC Matching rules 1-5: normalized complete event labels and same-celebration aliases (never legacy affinity-group substitutions such as bautizo/comunion), all supplied explicit theme/style/colours and tones, age/gender constraints and foreign-motif exclusion; never match solely by title event text, typical character colours or partial colour overlap.
- Move shared event normalization/alias ownership into the pure category module as needed and preserve existing exported helpers; exact new event labels are derived from catalogue records and require no hardcoded-category edit. Domain modules import no environment, HTTP, SDK or React runtime.
- Filter before ID/equivalent-title deduplication, keep stable source order, limit six and no minimum; preserve original design identity/title/photo/composition. Category unknown, empty catalogue or unsatisfied preference returns no ideas. Validation failures remain errors.
- ideasGuiadas and option counting use the strict matcher for category recommendations; legacy buscarDecoracionesSempertex may retain its other-consumer contract but cannot feed approximate candidates into this path. Update only superseded wedding padding assertions; retain customer-theme fidelity and independent photo helper regressions.
- Controlled tests exercise category-only wedding/baby-shower/birthday, one Navidad/Bautizo result, zero Spiderman/jubilacion, all requested colours, tones, unknown style, gender, age 0, seasonal exclusion, duplicate IDs/titles and unchanged inputs.
- Successive injected catalogues add a new visible design and event label, modify title/theme/event, then hide/remove it; result membership and metadata reflect every input without changing code or assuming 31 records.

Planned verification (not run as implementation checks):

- functional / command: `node --import tsx scripts/test/test-recomendaciones-categoria.ts` — Strict matcher category, preference, thin/empty and successive-catalogue behavior; created by T1 (does not exist yet).
- regression / command: `node --import tsx scripts/test/test-ideas-boda-guiada.ts` — Strict wedding expectations replace padding while customer fidelity and standalone photo behavior remain covered.
- regression / command: `node --import tsx scripts/test/test-busqueda-biblioteca-sempertex.ts` — Preserved lower-level legacy search contract for other consumers.

Contract acceptance (exact verification-purpose mapping):

- Controlled matcher tests pass for category-only, conjunctive explicit preferences, sparse/empty, identity, motif, tone/age/gender and successive source additions/modifications without a fixed ID/category whitelist or cross-celebration alias match.
- Wedding regression passes with only matching designs while literal customer-theme fidelity and independent photo helper invariants remain covered.
- Existing lower-level legacy search regression passes for other consumers without becoming a fallback for active-category recommendations.


Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimated 140 minutes. Uncalibrated engineering estimate: 25 minutes trace/extract shared category logic, 65 implement strict predicates/adapter, 50 controlled tests and focused regression. Queried history has unknown comparable durations/sample count; no historical median or execution budget inferred.

- [ ] T2 — Discovery turn decisions · repo: pictures · after: T1 · covers: R1, R3, R5 · kind: implement · verify: `node --import tsx scripts/test/test-turno-recomendaciones.ts`

Resolve category discovery and partial brief changes without intercepting explicit customer actions or modifying selected designs and plans.

Ownership / expected paths: `src/lib/ia/guiado/turno-recomendaciones.ts`, `scripts/test/test-turno-recomendaciones.ts`. Shared resources: `discovery-turn-outcome`.

Acceptance:

- A pure turn use case consumes validated customer messages, partial brief, catalogue and already-detected plan/edit/choice/proposal/photo/action facts. It emits a discriminated outcome with reason, resolved partial-brief snapshot and actual matching records; it never calls providers or writes plan/selection state.
- Apply SPEC rules 6-8 in order: explicit plan/idea cost-learn/query/edit and selection, deliberate proposal/direct complete-piece and actual photo-analysis intent retain priority; explicit browse is read-only, otherwise a new or explicitly refined category triggers discovery in that turn.
- Latest unambiguous affirmative customer category overrides stale brief; negated labels never select a category and multiple competing categories produce ambiguity rather than first-match guessing. Recognize new full event labels from visible source records through T1.
- Keep explicit customer refinements, use latest explicit replacements, never turn the whole conversational sentence into an invented theme, and never adopt model-selected colours. Unknown refinements remain unsatisfied. Unknown/ambiguous category offers no designs; clarification is allowed for real ambiguity only.
- Category-only outcome has an absent theme/age/gender rather than a fabricated complete brief. Return a resolved partial-brief snapshot retaining unrelated confirmed customer facts, plan and selected idea; result.brief must not be a delta because the UI replaces its brief. An explicit unsupported replacement category produces no designs and never reuses the stale category. No theme, age or gender question blocks known-category discovery.
- Tests cover all precedence branches, category changes with stale brief, no/versus multiple events, source-derived event, explicit colour/theme replacement, existing plan browsing and category mention during an edit. Frozen input plan/selection are unchanged and effect-call spies remain zero.

Planned verification (not run as implementation checks):

- functional / command: `node --import tsx scripts/test/test-turno-recomendaciones.ts` — Turn decision precedence, customer facts, partial briefs and plan preservation; created by T2 (does not exist yet).
- regression / command: `node --import tsx scripts/test/test-asistente-guiado-contrato.ts` — Existing v1 partial brief and explicit action input contracts remain valid.

Contract acceptance (exact verification-purpose mapping):

- Turn tests pass for explicit-action precedence, partial category-only brief, latest affirmative category, negation/ambiguity, explicit unsupported replacement, retained customer preferences and resolved brief snapshot and immutable plan/selection with zero effect calls.
- Existing v1 request tests accept partial briefs and retain deliberate invalid-input and explicit-action validation.


Classification: complexity high; scope small_change; risk medium; coupling high; confidence medium; estimated 120 minutes. Uncalibrated estimate: 25 minutes trace existing intent facts, 50 implement the pure decision table, 45 precedence/negative-input tests. History returned unknown comparable duration and sample count; no statistical projection claimed.

### M2 — Guided response and API integration

Milestone acceptance:

- Actual validated SSE publishes same-turn strict matching or honest empty data with category alone.
- Stream/final text, tools, browse/photo-suggestion branches and sanitation cannot reintroduce generic alternatives or intercept explicit actions.

- [ ] T3 — Honest matching and empty responses · repo: pictures · after: T2 · covers: R1, R3, R5, R6 · kind: implement · verify: `node --import tsx scripts/test/test-respuesta-recomendaciones.ts`

Make presentation and instruction rules consume the discovery outcome without generating padded alternatives or compulsory clarification.

Ownership / expected paths: `src/lib/ia/guiado/respuesta-recomendaciones.ts`, `src/lib/ia/guiado/respuesta-guiada.ts`, `src/lib/ia/guiado/prompt-guiado.ts`, `src/lib/ia/guiado/opciones-catalogo.ts`, `scripts/test/test-respuesta-recomendaciones.ts`, `scripts/test/test-respuesta-guiada-sin-fracaso.ts`, `scripts/test/test-cambio-tematica-guiada.ts`, `scripts/test/test-opciones-catalogo-guiado.ts`. Shared resources: `discovery-response-policy`.

Acceptance:

- A deterministic response formatter consumes T2 outcomes. Matching describes existing ideas with explicit choice and no prerequisite question; empty publishes a short honest no-match message and no automatic theme/style/photo/decoration alternative or compulsory clarification.
- Known-category discovery bypasses or explicitly scopes the legacy no-failure/style-fill sanitation in both streamed and final response paths. A zero-result reply never claims these ideas exist; neither stream chunks nor final text can suggest an absent design.
- Align prompt instructions with category-only discovery and strict matching; remove contradictions that require theme first, generalize unsupported events or convert unsupported themes to typical colours. Preserve explicit bespoke/photo/plan action instructions.
- Option validation for category discovery uses T1 strict matches and never substitutes themes from another category or pads options to hide empty results; no styles need be offered when designs already appear.
- Update only obsolete guided fallback assertions in response/theme tests, replacing them with honest empty/strict assertions. Keep literal colour fidelity, same-theme behavior, unrelated flow options, private plan actions and standalone non-category helper contracts.
- Tests push arbitrary fragmented model-like text through the actual discovery response boundary and final formatter; both suppress false offers and forced style questions, while normal plan/proposal/selection replies remain unaffected. A real ambiguous-category reply may ask which category.

Planned verification (not run as implementation checks):

- functional / command: `node --import tsx scripts/test/test-respuesta-recomendaciones.ts` — Matching and empty presentation agree across final and fragmented stream boundaries; created by T3 (does not exist yet).
- regression / command: `node --import tsx scripts/test/test-respuesta-guiada-sin-fracaso.ts` — Updated empty-outcome expectations preserve unrelated response safeguards.
- regression / command: `node --import tsx scripts/test/test-cambio-tematica-guiada.ts` — Explicit theme changes and customer fidelity survive removal of typical-colour fallback.
- regression / command: `node --import tsx scripts/test/test-opciones-catalogo-guiado.ts` — Category option handling retains unrelated option contracts.

Contract acceptance (exact verification-purpose mapping):

- Controlled response tests pass for matching/empty and fragmented stream behavior without invented designs, compulsory style questions or changed suppressed-action replies.
- Response regressions pass with strict honest-empty assertions replacing category fallback assertions while unrelated flow safeguards remain covered.
- Theme-change regressions pass without typical-colour suggestions for an absent theme and preserve literal customer preferences.
- Option regressions pass without generic category fill while unrelated age/city/flow options remain unchanged.


Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimated 110 minutes. Uncalibrated estimate: 20 minutes trace streaming/final sanitation, 45 formatter and instruction alignment, 45 update conflicting assertions with strict replacements. History metrics remain unknown; prose changes alone do not establish product acceptance.

- [ ] T4 — Integrate category discovery into the guided API · repo: pictures · after: T3 · covers: R1, R2, R3, R4, R5, R6 · kind: implement · verify: `node --conditions=react-server --import tsx scripts/test/test-ruta-recomendaciones-categoria.ts`

Publish authoritative matching or empty outcomes through the existing SSE/tool contracts while preserving validation and intentional plan actions.

Ownership / expected paths: `src/app/api/asistente-guiado/route.ts`, `src/lib/ia/guiado/pedido-ideas.ts`, `scripts/test/test-ruta-recomendaciones-categoria.ts`. Shared resources: `guided-recommendation-sse-v1`.

Acceptance:

- After existing request/auth validation and explicit-action detection, invoke T2 with bibliotecaVisible; route delegates matching/precedence/text to T1-T3 rather than duplicating domain predicates. Discovery with known category produces results in the same response before any style/age/gender question.
- Use the existing respuestaSinModelo SSE behavior for deterministic matching/empty discovery before provider initialization; keep request/correlation IDs, schema validation, texto/fin framing and stable error handling. Text is T3 output and result includes validated partial brief plus decoraciones, including an explicit empty array.
- The search tool schema/instructions allow event without theme and its implementation calls strict matching with customer-confirmed facts; do not weaken complete-brief validation for operations needing it. A missing theme stays absent, never blank or synthesized from category. Retain asistente-guiado.v1 and existing decoration fields.
- Cover category/theme change, explicit browse, photo-suggestion and model-tool paths using the same authoritative strict outcome. No branch may call legacy approximate ordering/fill to add rejected candidates. Remove or gate the final ideas_sin_fracaso fallback for category discovery, including zero results.
- Explicit plan edits/queries, idea choice/cost/learn, direct complete-piece proposals and real photo analysis retain their prior intent path. Read-only browsing cannot publish ideaElegida, edicionPlan, propuesta, cotizacion or image operations; only explicit selection can select.
- Deterministic route integration tests drive validated requests and consume actual SSE events with controlled catalogue/provider/audit doubles. Verify same-turn category-only and empty behavior, partial brief, stale category replacement, invalid JSON/input, deliberate suppression paths and zero external calls/effects for matching/empty discovery.
- Adapter test obtains a modified authoritative-library double on consecutive calls, proving fresh source data is consumed without an extra recommender cache; do not claim this demonstrates runtime hot reload or deployed source edits.

Planned verification (not run as implementation checks):

- integration / command: `node --conditions=react-server --import tsx scripts/test/test-ruta-recomendaciones-categoria.ts` — Actual guided handler dispatch, tool paths and validated SSE with no live providers; created by T4 (does not exist yet).
- regression / command: `node --import tsx scripts/test/test-asistente-guiado-contrato.ts` — Partial v1 brief, invalid inputs and deliberate action compatibility.
- regression / command: `node --import tsx scripts/test/test-edicion-plan-chat-guiada.ts` — Plan edit and explicit idea-selection behavior remains intact.

Contract acceptance (exact verification-purpose mapping):

- Actual-handler tests pass for same-turn category-only/empty SSE, authoritative source updates, tool/browse/photo-suggestion strictness, partial brief, invalid inputs and explicit-action suppression with zero external discovery calls.
- Existing v1 contract tests pass with no new wire field/version or weakening of complete-brief validation.
- Existing plan edit and explicit idea-selection regressions pass without browsing side effects.


Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimated 160 minutes. Uncalibrated estimate: 30 minutes map route entry/fallback branches, 65 integrate existing SSE and tool adapters, 65 execute controlled route and action regressions. Shared route is large, so extra trace/integration work is included; comparable duration/history samples remain unknown.

### M3 — Gallery compatibility and verification

Milestone acceptance:

- One/empty/current recommendations render in the existing gallery; stale cards never become active after an empty result and selected plan/session data remains intact.
- R1-R6 acceptance evidence, relevant regressions, lint, workspace builds, types and application build have actual recorded outcomes, with blockers separated honestly.

- [ ] T5 — Preserve gallery identity and empty-turn selection · repo: pictures · after: T4 · covers: R1, R2, R3, R5, R6 · kind: implement · verify: `node --import tsx scripts/test/test-ui-recomendaciones-categoria.ts`

Render strict current recommendations in the existing gallery and prevent an empty turn from reactivating older suggestions while retaining the selected design and plan.

Ownership / expected paths: `src/components/guiado/VistaGuiada.tsx`, `src/components/guiado/CarruselDecoraciones.tsx`, `scripts/test/test-ui-recomendaciones-categoria.ts`, `scripts/test/fixtures/recomendaciones-categoria-ui/arnes.tsx`. Shared resources: `guided-recommendation-sse-v1`, `guided-session-widgets`.

Acceptance:

- Consume the existing optional partial brief and decoration records; no second gallery, copied catalogue or sample-photo list is introduced. A single real result shows its actual title/reference image and explicit Me gusta esta action.
- Distinguish absent decoraciones from present empty array. Persist an existing-schema decoraciones widget with [] as the empty discovery boundary, have its carousel render no cards/actions, and let ideasALaVista stop at that boundary rather than selecting older results.
- Positive results replace the active selectable recommendation set. Historical transcript cards remain historical; empty results and category changes preserve seleccionada, plan, approval context and unrelated session data. Existing retry and restore honor the empty boundary.
- No public DTO/session field or version is added. Existing WidgetGuiadoSchema already accepts an empty decoration array; old saved sessions remain valid. Explicit textual selection uses only the current ideasMostradas; button selection stays deliberate and no automatic plan request is added.
- Use a browser harness mounting the actual guided view/carousel with controlled SSE, storage and request interception, following the inspected esbuild/Playwright local harness pattern. Assert zero/one/many results, keyboard/button selection, stale-to-empty next request, retry/restore and an existing plan unchanged.
- Harness aborts unhandled external requests; no paid image, model, pricing or production backend calls. If the browser is unavailable, report product verification blocked and retain deterministic schema/render checks; do not claim product acceptance from a static source assertion.

Planned verification (not run as implementation checks):

- integration / command: `node --import tsx scripts/test/test-ui-recomendaciones-categoria.ts` — Actual guided gallery and saved-session behavior using a controlled local browser harness; created by T5 (does not exist yet).
- regression / command: `node --import tsx scripts/test/test-sesion-guardada-accion-idea.ts` — Old saved sessions and explicit action restore remain readable.
- product / manual: `Review harness cases AC1, AC2, AC6 and AC9 in desktop and narrow viewport, including keyboard choice` — Observable category-only, thin and empty gallery behavior. Expected: Correct identity/photo, explicit choice, no empty-turn cards/options, and the existing selection/plan unchanged.

Contract acceptance (exact verification-purpose mapping):

- Controlled browser tests pass on actual gallery/view for zero/one/many designs, visible identity/photo, explicit choice, persisted empty widget boundary, next-request ideasMostradas and retry/restore with unchanged plan/selection.
- Existing saved-session regression passes with old sessions and explicit-action restoration intact.
- Desktop and narrow-viewport product review confirms category-only and sparse designs are selectable by keyboard/button and empty turns expose no active decoration alternatives while retaining plan/selection.


Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimated 130 minutes. Uncalibrated estimate: 25 minutes trace active-gallery/session behavior, 35 implement empty boundary, 70 construct and run controlled browser cases. Existing local Playwright/esbuild harness demonstrates feasibility; browser availability and full-view bundle setup remain estimate uncertainty.

- [ ] T6 — Register regressions and verify the complete slice · repo: pictures · after: T5 · covers: R1, R2, R3, R4, R5, R6 · kind: test · verify: `npm run lint`

Make deterministic category regressions routinely runnable and verify static, integration and product acceptance against R1-R6 without live providers.

Ownership / expected paths: `package.json`, `scripts/test/test-recomendaciones-categoria.ts`, `scripts/test/test-turno-recomendaciones.ts`, `scripts/test/test-respuesta-recomendaciones.ts`, `scripts/test/test-ruta-recomendaciones-categoria.ts`, `scripts/test/test-ui-recomendaciones-categoria.ts`. Shared resources: `strict-category-matching`, `discovery-turn-outcome`, `discovery-response-policy`, `guided-recommendation-sse-v1`, `guided-session-widgets`.

Acceptance:

- Register the provider-free matcher/turn/response/route regressions in the existing test workflow and a separately named local browser script, following the repository browser-test convention. No skip, lower threshold, catalogue snapshot rewrite or live-provider prerequisite is introduced.
- Execute the six acceptance clusters: same-turn category-only, real identity/single structures, strict sparse/empty, source-derived additions/modifications, deliberate intent/plan preservation, and compatible SSE/gallery/old-session state. Every R1-R6 and AC1-AC9 maps to observed evidence; planned tests or a green legacy suite alone are not product proof.
- Run lint, workspace builds, application types, affected guided regressions and application build. Separate pre-existing environment/suite failures from regressions with exact failing command/result; do not repair unrelated dirty work or regenerate saved plans/goldens.
- Inspect cross-module imports and diff for duplicated catalogue IDs/cache/taxonomy, HTTP domain rules, changed wire versions, secrets/new dependencies, accidental provider calls and REQ-017 imports. Only scoped implementation files from T1-T5 plus test registration belong to this future slice.
- Confirm fresh recommendation lifecycle is documented as source publication plus normal build/deploy. No runtime hot-reload claim, deployment, data migration or external experiment is part of acceptance verification.

Planned verification (not run as implementation checks):

- static / command: `npm run lint` — Repository lint for all changed TypeScript and test registration.
- static / command: `npm run build --workspaces --if-present` — Workspace declarations required before application type checking.
- static / command: `npx tsc --noEmit` — Application types after workspace declarations exist.
- regression / command: `npm run guiada:test` — Registered deterministic guided regressions including REQ-018 cases.
- integration / command: `node --conditions=react-server --import tsx scripts/test/test-ruta-recomendaciones-categoria.ts` — Integrated category decisions through actual SSE boundaries; created by T4 (does not exist yet).
- integration / command: `node --import tsx scripts/test/test-ui-recomendaciones-categoria.ts` — Controlled browser verifies selectable gallery and restored empty-turn boundary; created by T5 (does not exist yet).
- static / command: `npm run build` — Application integration build without changing deployment/runtime state.
- static / command: `git diff --check` — Scoped changes have no whitespace errors.
- product / manual: `Review AC1-AC9 evidence and source publication lifecycle against SPEC and actual implementation diff` — Product acceptance and update semantics beyond schema/test-count success. Expected: Every acceptance case has observable evidence, only actual matches are shown, and no hot reload or plan mutation is claimed.

Contract acceptance (exact verification-purpose mapping):

- Repository lint completes without new errors in the scoped change.
- Workspace builds complete and emit declarations required for application types.
- Application TypeScript check completes after workspace builds without new type errors.
- Registered deterministic guided suite passes including the new category matcher, turn, response and route regressions without live providers.
- Actual-handler regression passes through validated SSE for all category acceptance branches.
- Controlled gallery browser regression passes including the restored empty-turn selection boundary.
- Application build completes with the existing deployment/runtime state unchanged.
- Scoped implementation diff has no whitespace errors.
- Product acceptance review finds observable evidence for AC1-AC9 and no duplicated catalogue/cache, changed wire contract, hidden provider calls, REQ-017 imports, scope leakage or hot-reload promise.


Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimated 120 minutes. Uncalibrated estimate: 20 minutes registration, 70 command execution/triage, 30 evidence and consumer review. History returned unknown duration in seconds with null verified comparable samples, unknown consumption units/quality/retries; these 120 minutes are a provisional work breakdown, not a measured projection or limit.

## Dependencies and interfaces

DAG: `T1 → T2 → T3 → T4 → T5 → T6`. M1 owns matching/turn policy; M2 consumes that outcome for presentation and actual API dispatch; M3 consumes validated route results for gallery/session compatibility and final verification. Every edge consumes a concrete predecessor output; there is no dependency on REQ-017 or an external experiment. No parallel execution guarantee or execution assignment is made. A separate diagram adds no value to this linear graph.

**IF-1 — Strict category catalogue query**. Owner: Guided-library matching domain (T1). Producer: T1; consumers: T2, T3, T4; integration verification: T6 (implementation integration remains in T4/T5).

- inputs: Validated visible library records, customer category, optional explicit refinements, current catalogue event labels.
- outputs: Stable ordered actual design records, zero to six, with preserved identity and no approximate fill.
- invariants: Only current visible eligible records; no fixed ID/category whitelist or extra cache; Known category is required; absent refinements are unconstrained and supplied preferences are conjunctive; Source edits arrive through normal publication/build/deploy; injected successive inputs prove derivation, not runtime hot reload.
- integration_criteria: Category-only route and option queries call the same predicates; Thin/empty and new/modified-source cases retain their exact result membership through route integration.

**IF-2 — Read-only discovery turn outcome**. Owner: Guided application turn policy (T2). Producer: T2; consumers: T3, T4; integration verification: T6 (implementation integration remains in T4/T5).

- inputs: Validated customer messages/partial brief and existing explicit action facts; Current validated visible catalogue through IF-1.
- outputs: Suppressed, unknown/ambiguous, matching or empty outcome with reason, resolved partial-brief snapshot and actual design records.
- invariants: No plan/selection mutation and no provider calls; Latest affirmative unambiguous customer category beats stale brief; explicit action precedence wins over automatic discovery.
- integration_criteria: Actual route dispatch preserves all explicit-action branches and produces category-only data in the same response; Empty and matching outcomes are authoritative and cannot be replaced by model/generic fallback.

**IF-3 — Discovery response policy**. Owner: Guided response layer (T3). Producer: T3; consumers: T4, T5; integration verification: T6 (implementation integration remains in T4/T5).

- inputs: Typed IF-2 outcome and customer-visible category/preferences.
- outputs: Short matching or honest empty text; no automatic alternative/compulsory clarification for empty.
- invariants: Stream chunks and final text agree on which designs exist; Suppressed turns preserve existing intentional flow text.
- integration_criteria: Handler uses deterministic discovery text before provider initialization; Sanitation/options and model-tool paths never turn empty into generic alternatives.

**IF-4 — Existing v1 SSE and gallery empty boundary**. Owner: Guided API adapter (T4) and gallery state consumer (T5). Producer: T4; consumers: T5; integration verification: T6 (implementation integration remains in T4/T5).

- inputs: Validated IF-2/IF-3 result and request/correlation IDs.
- outputs: Existing texto/fin SSE; result.brief partial and result.decoraciones actual records or explicit [].
- invariants: No new wire/session fields or versions; Empty array persists as existing decoration widget boundary; missing field means no discovery update; Selected idea and plan unchanged until explicit existing actions.
- integration_criteria: Real gallery receives zero/one/many actual records without copied sources; After empty result and reload/retry, ideasMostradas excludes older transcript candidates; old sessions remain readable.

## Requirement traceability

| Requirement | Producing / integration tasks | Acceptance | Verification evidence planned |
|---|---|---|---|
| R1 category-only | T1,T2,T3,T4,T5; T6 verifies | AC1,AC2,AC8,AC9; M1/M2/M3 | functional matcher/turn/response; route/gallery integration; product review |
| R2 real complete designs | T1,T4,T5; T6 verifies | AC1,AC2,AC5,AC9 | source/identity assertions, route records, rendered photo/title |
| R3 strict thin/empty | T1,T2,T3,T4,T5; T6 verifies | AC2,AC3,AC4,AC6,AC8 | conjunctive/empty regressions; fragmented text; actual SSE; stale-gallery negative cases |
| R4 source updates | T1,T4; T6 verifies | AC5 | successive catalogue fixture inputs, authoritative adapter double, publication lifecycle review |
| R5 intentional actions | T2,T3,T4,T5; T6 verifies | AC3,AC6,AC7,AC8,AC9 | precedence/effect spies, old edit/choice/session regressions, gallery interaction |
| R6 coherent integration | T3,T4,T5; T6 verifies | AC1,AC4,AC6,AC7,AC9 | static checks, actual handler/SSE, browser and acceptance evidence review |

No orphan requirement or task: every task declares covers, observable acceptance and categorized verification; interfaces declare integration ownership. Strict alias matching must not change unrelated legacy event-helper consumers; keep their compatibility through the distinct strict matcher boundary. T2 resolves the entire partial-brief snapshot before T4 sends it: VistaGuiada replaces brief state, so sending a delta could silently erase known preferences.

The deterministic check validates declared structure/evidence and coverage, not whether future implementation will satisfy these criteria.

## Estimates and uncertainty

History was queried read-only with `python3 skill/scripts/bitacora.py --project pictures plan-json history --kind ...` for implement medium/small/medium/medium, implement high/small/medium/high, implement high/large/medium/high, and test medium/small/medium/medium. All returned exit 0 and `status: unknown`: duration native unit seconds, null median/range/sample count with `cross_route_duration_comparability_unproven`; consumption unit/sample count unknown with `cross_provider_token_units_not_comparable`; quality/retries unknown. No measured cost, quota, quality rate or comparable historical estimate is inferred.

Required integer estimates are provisional engineering work breakdowns in minutes including local verification; rationale and all six typed-evidence dimensions are in PLAN.json. Confidence stays medium. Browser availability and full-view controlled bundling, negative/refinement parsing and the existing dirty build environment are uncertainty sources. They do not require another owner product decision. Do not convert the estimates into execution assignments or a promised schedule.

## Risks and bounded corrections

- Strict matching rejects legacy same-colour/nearby behavior. Keep the lower-level legacy contract for other consumers; route every active-category discovery path through the strict owner, replacing contradictory tests with explicit new-policy assertions.
- Model/tool or sanitation fallbacks can refill an empty set. T3/T4 use a deterministic matching/empty response before provider setup and forbid alternative additions in all category entry paths. Test both streamed and final events, not just prompt wording.
- Empty UI responses currently omit the carousel, so the backward scan can revive earlier ideas. T5 persists an existing-schema empty widget boundary and tests the next request plus retry/restore; no new public field is needed.
- Source additions/modifications are reflected at the source's normal publication/build/deploy boundary. Do not run catalogue publishers or rebuild saved plans here, add a cache/index or promise runtime refresh. Controlled source fixtures prove derivation, not a production rollout.
- REQ-017 isolated shared-route changes are outside the supplied baseline. Preserve them, do not import them, and require a later combined integration review if both slices are merged.
- Browser/API tests use controlled doubles and block unhandled external requests. Lack of Chromium or isolated dependency/build limitations must be reported as blocked evidence, never silently skipped or called passed.

## Verification performed during planning

- Existing `node --import tsx scripts/test/test-busqueda-biblioteca-sempertex.ts`: exit 0 (legacy behavior).
- Existing `node --import tsx scripts/test/test-ideas-boda-guiada.ts`: exit 0 (legacy behavior).
- Local JSON and git inspection reconfirmed 46/31/23 records and canonical HEAD/dirty status. No product implementation tests are claimed.
- First actual `bt_planner check`: exit 2, four errors because each interface assigned its integration task as a consumer. Corrected integration verification ownership to T6, distinct from consumer tasks. Also aligned task acceptance text to exact verification purposes; removed the misleading missing-purpose warnings without claiming tests exist.
- Repaired check: `PYTHONPATH=skill/scripts python3 -m bt_planner check bitacora/pictures/requirements/REQ-018-category-based-recommendations-of-assemb --repo pictures=/home/david/dev/pictures --json` from `/home/david/dev/metodologia`: exit 0, `ok: true`, zero errors, nine warnings: seven `created_by` entries are future tests rather than existing evidence, and two explicit manual product criteria (T5/T6) require review and cannot produce automatic PASS. The final check after semantic corrections also returned exit 0 with exactly these nine warnings; no structural error remains.
- Application lint/types/full suite/build and browser acceptance remain future implementation verification, not checks performed in this planning session.
- Local artifact whitespace/final-newline and evidence-link checks passed; scoped `git diff --check` exited 0. The round-01 SHA-256 stayed `cf2fe617b19de06789a72af97aafd929970dbaebd97774c891348a027ce2e2e3`. Canonical Pictures and isolated REQ-017 status plus all initially dirty/untracked file hashes are unchanged. Coordinator updates to shared Pictures SUMMARY/day logs appeared during this pass and were preserved, not written or reverted by Planner.

## Adversarial semantic self-review

This is the same Planner's semantic self-review after deterministic validation, not independent review or approval. No owner approval, freeze, launch or execution is inferred from it.

| Category / severity | Trigger and provenance | Bounded correction in this draft |
|---|---|---|
| Demonstrated defect / medium, corrected | Initial deterministic check returned four interface errors: integration task was also a consumer (`bt_planner/interfaces.py:99-116`). | T6 is the declared integration-verification task; implementation consumers remain T2-T5. Repaired check exits 0. |
| Fact / medium | Current strictness is defeated by lower-level fill (`biblioteca.ts:190-223`), guided padding/fallback (`ideas-guiadas.ts:190-208`) and route fallback (`route.ts:583-609`). | T1 owns strict matching; T3/T4 align instructions, options, stream/final text and every category entry path. Preserve independent lower-level contracts without letting them refill this path. |
| Demonstrated defect / medium, corrected | Original alias reuse wording could classify primera comunión as bautizo because `biblioteca.ts:40-50` and `ideas-guiadas.ts:224-237` group them. This contradicts strict actual-match acceptance. | Genuine same-celebration aliases only in the strict matcher, with a negative cross-event test; retain unrelated legacy helper compatibility. No new broad taxonomy or product approval is invented. |
| Plausible risk / medium, corrected | `VistaGuiada.tsx:721` replaces brief with `setBrief(datos.brief)`. A patch containing event alone could erase existing customer fields. | T2 emits a resolved validated partial snapshot; T4 publishes it. Test retained facts and category-only absent theme. |
| Plausible risk / medium, corrected | A new unsupported event after an old brief can fall through to the stale category; `route.ts:420` currently prefers the brief to customer event detection. | T2 latest explicit replacement wins even when unsupported; unsupported gives zero designs, not old-category designs. Cover negation/ambiguity separately. |
| Fact / medium | `VistaGuiada.tsx:728` omits empty carousels and `ideasALaVista` at 2238-2248 scans older carousels. | T5 persists an already-valid empty decoration widget boundary and verifies the next selection request plus restore/retry. Plan and selected design stay intact. |
| Product decision / binding | Owner Q5 choice b plus “si faltan coincidencias no ofrecer nada”; original Q5 recommendation allowed nearby designs. | Strict thin/empty acceptance replaces padding expectations; no compulsory fill clarification, implicit alternatives or fabricated approvals. |
| Fact / low | Static JSON import/module validation (`biblioteca.ts:1,321-334`); explicit publication (`scripts/biblioteca/README.md:3-11`, publisher 890-903). | Additions/changes reflect normal publication/build/deploy with no new lists/cache; runtime reload is not promised. |
| Plausible risk / medium | Full-view browser harness is planned, while the inspected local browser precedent covers another component (`test-hoja-armado-ui.ts:36-80`). | Keep estimate confidence medium, block unhandled network requests, and report unavailable browser or bundling evidence honestly; no test existence or product success fabricated. |

R1-R6 all have producers, dependent integration paths, task/milestone acceptance and categorized checks. No orphan task/requirement or undeclared shared wire contract remains. Path ownership and chain order prevent conflicting tasks from being left unordered. New tests are marked created_by; two manual product criteria intentionally remain human-review work. Pure matching/turn policy, transport integration and presentation responsibilities are distinct. No provider/account/model/effort/worker assignment, approval, REQ-017 integration or experiment execution is present. No material owner decision remains blocking for this draft.

## Coordinator publication check

- Canonical `bitacora.py --project pictures plan-json check REQ-018` initially exited2: its command-evidence verifier parsed the operand of `node --import tsx` as the script path. The referenced script exists. The Planner module check had passed without that adapter-specific command verification; these are distinct checks.
- Coordinator ran the equivalent actual command `node --import=tsx scripts/test/test-ideas-boda-guiada.ts` in Pictures; exit0. Updated only T1 confidence command evidence to that newly executed command. Original observations and baseline commands remain above and in SPEC. No test or validation was disabled; no product code changed.
- Final canonical publication check after the evidence correction: exit0, `OK: PLAN.json is publishable`; nine warnings retained (seven future-test references, two manual product criteria). `plan-json report REQ-018` exit0. Approval/freeze and execution remain absent.
