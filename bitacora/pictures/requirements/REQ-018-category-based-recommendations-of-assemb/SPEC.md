> **CANCELLED 2026-10-18 by the owner (all open requirements).** Nothing deleted: code, branches and reports are kept.
---
id: REQ-018
status: cancelled (2026-10-18, owner)
created: 2026-10-18
track: standard
---
# REQ-018 — Category-based recommendations of assembled decorations

**Planning draft v2; product choices confirmed, plan approval pending.** The original metadata is retained without changing workflow/approval state. The owner has answered Q1–Q5 and the update follow-up. `rounds/round-01.json` is historical answered evidence; its stale update-mechanism note is superseded by the owner's “si, reflejar” in the current instruction. Round files and bitácora remain coordinator-owned.

## Problem & goal

Owner request: “queremos implementar un sistema de recomendaciones en Pictures de decoraciones ya armadas según la categoría que esté requiriendo el usuario”.

In `/asistente`, show eligible existing guided-library designs as soon as a customer celebration/category is detected, without requiring theme, colours, age or gender first. Optional explicit preferences narrow the results. Show only actual matches, even if the result is small or empty; preserve customer intent, explicit design selection and existing plans.

The behavioral delta is category-only discovery plus strict relevance and an honest empty result. Current code already recommends real designs but requires event and theme in its tool path and deliberately fills with nearby/general ideas. Returning raw materials, bare structure IDs or newly generated designs does not meet this goal.

## Users / actors / stakeholders

- Guided-assistant customer at `/asistente`; David owns product decisions.
- Use the existing gallery, photos, design IDs and explicit selection actions.
- Existing complete visible guided-library ideas are eligible, including single-structure designs. Private saved scenes, Taller catalogue entries and legacy decoration CRUD records are outside this candidate set.

## Confirmed decisions

- C1 / Q1: `/asistente`, reusing the existing gallery.
- C2 / Q2: all complete visible guided-library ideas, including single-structure ideas. The current 31 visible records are a snapshot, never an ID whitelist or fixed count.
- C2a / follow-up: “si, reflejar” means reflecting additions and changes in the existing library source. No new administrator or acquisition pipeline. Updates follow the source's existing publication and normal build/deploy lifecycle described below; no runtime hot reload is promised.
- C3 / Q3: category means celebration/event (birthday, wedding, baby shower); theme/style/colours are optional refinements.
- C4 / Q4: offer assembled designs when category is detected; explicit intent, explicit design selection and plan safeguards retain precedence. Browsing never edits a plan.
- C5 / Q5: only actual matches; zero means no decoration suggestions, and fewer than the display target stays fewer. No nearby/general/padded/invented designs, automatic generic fallback, or required clarification just to fill results. This supersedes Q5's originally recommended nearby behavior.

## Research evidence


Paths below identify inspected files. Repository facts describe the supplied checkout, not a verified production deployment or live database.

| ID | Observed evidence | Consequence for this requirement |
|---|---|---|
| E1 | [Pictures instructions](/home/david/dev/pictures/AGENTS.md:13), including verification rules at line 79; `CLAUDE.md` imports this file. | Preserve unrelated edits, catalogue authority, layer boundaries, runtime validation, explicit actions and meaningful regression checks. |
| E2 | [Guided idea schema](/home/david/dev/pictures/src/lib/biblioteca-sempertex/esquemas.ts:23) defines an idea ID, title, theme, events, age range, photos, pieces, materials and steps; origins are defined at line 39. [Visibility](/home/david/dev/pictures/src/lib/biblioteca-sempertex/biblioteca.ts:333) excludes `origen: ejemplo`. | A library idea is a concrete candidate for an existing assembled design. It is not just an official structure ID. |
| E3 | Local JSON inspection of [guided catalogue](/home/david/dev/pictures/src/lib/biblioteca-sempertex/decoraciones.json:1232): 46 records, 15 examples and 31 visible `referencia_real` records. Of the visible records, 23 have a total piece quantity of 1, six have 2 and two have 3. The multi-piece example begins at line 1414. | “Assembled” cannot silently be equated with “multiple structures”: that choice would remove 23 of 31 current ideas. Counts use the sum of `piezas[].cantidad`, not scene geometry. |
| E4 | [Guided search](/home/david/dev/pictures/src/lib/biblioteca-sempertex/biblioteca.ts:138) accepts event, age and theme; it uses exact/cercana matching, colour/event scores, generic fill and title deduplication through line 223. [Available themes](/home/david/dev/pictures/src/lib/biblioteca-sempertex/biblioteca.ts:337) come from visible ideas, falling back to all visible themes if no event matches. | Basic catalogue recommendations already exist; the new requirement needs a demonstrable difference. Current search is not a strict category filter. |
| E5 | [Guided orchestration](/home/david/dev/pictures/src/lib/ia/guiado/ideas-guiadas.ts:190) combines theme and the latest user text, handles baby-shower gender, and falls back to nearby ideas. [Known events](/home/david/dev/pictures/src/lib/ia/guiado/ideas-guiadas.ts:224) form a separate guided vocabulary. | Reuse must preserve explicit customer preferences and account for existing fallback rules. |
| E6 | [Guided API search tool](/home/david/dev/pictures/src/app/api/asistente-guiado/route.ts:301) requires both event and theme, publishes real ideas and audits the search. [Explicit requests to see ideas](/home/david/dev/pictures/src/app/api/asistente-guiado/route.ts:448) search the catalogue without replacing the current plan. | Category-only discovery is now confirmed by Q4; this observed gate must change. Existing-plan precedence matters. |
| E7 | [Carousel](/home/david/dev/pictures/src/components/guiado/CarruselDecoraciones.tsx:131) shows a reference photo, `Referencia`/`Parecida` labels, title, theme and “Me gusta esta”. [Saved idea-plan contract](/home/david/dev/pictures/src/lib/plan/plan-de-idea.ts:5) preserves the idea's actual pieces and products rather than reconstructing them from structure names. | Existing display and selection contracts are relevant; browsing, selection, plan creation and quotation are distinct actions. |
| E8 | [Taller library types](/home/david/dev/pictures/src/lib/globos3d/biblioteca.ts:35) distinguish `escena` (complete scene), `conjunto` (decorated structure), bare `estructura`, small `decoracion`, and `utileria`. Own library items are described at lines 49 and 121. | In this library, a `decoracion` can be a small flower or balloon. Filtering that type would not implement the owner's goal. |
| E9 | [Taller taxonomy](/home/david/dev/pictures/src/lib/taller/taxonomia-celebraciones.ts:8) separates celebration from theme and explicitly distinguishes guided-chat and Shopify vocabularies. [Classification](/home/david/dev/pictures/src/lib/taller/clasificacion-biblioteca.ts:4) assigns celebration/theme labels to factory items; derived pieces inherit scene labels. | Q3 now selects celebration/event, with optional theme/style/colours. No universal category field across all these catalogues was established. |
| E10 | [Taller memory search](/home/david/dev/pictures/src/lib/globos3d/herramientas-escena-biblioteca.ts:123) filters by item type, occasion, piece type and colours. [Online search](/home/david/dev/pictures/src/lib/taller/buscar.ts:323) supports RAG with a memory fallback. | A broader assembled-scene recommender has existing search infrastructure, but sharing it with the guided assistant is a material scope/contract choice. No online query was executed. |
| E11 | [Catalogue registry adapter](/home/david/dev/pictures/src/lib/catalogo/repositorios/sempertex/entradas-guiada.ts:14) states that guided chat still reads its own files; [Taller adapter](/home/david/dev/pictures/src/lib/catalogo/repositorios/sempertex/entradas-biblioteca.ts:7) exposes factory/derived items separately. | The common Sempertex repository does not make the guided and Taller candidate sets interchangeable. |
| E12 | [Legacy decoration type](/home/david/dev/pictures/src/lib/types.ts:76) stores name, description, cover image and product IDs, with no event/theme fields in that type. [Legacy reader](/home/david/dev/pictures/src/lib/decoraciones.ts:39), [API](/home/david/dev/pictures/src/app/api/decoraciones/route.ts:14) and [admin form](/home/david/dev/pictures/src/components/admin/DecoracionForm.tsx:49) are a third decoration path. | Do not mistake this CRUD catalogue or its products for the guided ideas. Database contents and runtime availability were not inspected. |
| E13 | [REQ-017 scope and exclusions](/home/david/bitacora/pictures/requirements/REQ-017-activity-aware-guided-chat-decoration-re/SPEC.md:20) cover event-specific official-structure menus and free-composition constraints, and explicitly exclude changes to library search/carousel. [D-052](/home/david/bitacora/pictures/DECISIONS.md:304) keeps its defaults revisable. | REQ-018 can address discovery of existing designs without duplicating REQ-017's event-to-structure policy. Its open round is not approval for REQ-018. |
| E14 | [Project summary](/home/david/bitacora/pictures/SUMMARY.md:43), REQ-017 `REPORT.md` and [P-101](/home/david/bitacora/pictures/PENDING.md:27) report isolated completion and pending policy review. Direct inspection of [worktree event map](/home/david/dev/pictures-wt/req-017-v2/src/lib/plan/estructuras-por-evento.ts:8) and [proposal policy](/home/david/dev/pictures-wt/req-017-v2/src/lib/ia/guiado/politica-propuesta-evento.ts:23) confirms the structure-based approach. | Those files are isolated, uncommitted work, not functionality in the canonical supplied checkout. Prior reported checks were not rerun here. |

### Prior research provenance and limits (retained historical evidence)

- Canonical inspection root: `/home/david/dev/pictures`, branch `feat/req-014-72h-marathon-autonomous-product-developm`, HEAD `5f9104980d31e0074c6bbb5ed16cae1e8c92a723`. “Canonical” here means the owner-supplied checkout, not a clean `main` or production assertion.
- At inspection: 197 status entries (159 modified, two deleted, 36 untracked). `git diff --shortstat`: 161 files changed, 1,038 insertions and 748 deletions. The guided search/schema/API/UI paths inspected above have no local tracked diff. Existing changes were preserved.
- Related inspected worktree: `/home/david/dev/pictures-wt/req-017-v2`, branch `feat/req-017-activity-aware-v2`, HEAD `75c8749792b893f9e07cb4305d1c9ce2bbfd6a88`, 16 status entries. Its extracted normalizer/event helpers and structure policy are not assumed available in the canonical checkout.
- `project.json` lists the Pictures mapping and historical worktree hints; only the supplied Pictures checkout and the relevant REQ-017 worktree were used for code evidence. `git worktree list` and recent library history were inspected. No remotes were fetched.
- Read Pictures `SUMMARY.md`, `PENDING.md`, `DECISIONS.md`, relevant `ARCHITECTURE.md`, REQ-017 SPEC/PLAN/report/open round, global memory and Pictures memory index/known pitfalls. Historical summaries can describe other branches; code and the explicit checkout mapping govern observations here.
- Catalogue count: local Python JSON inspection; exact visible event labels include four Boda ideas, one Bautizo idea and one Navidad idea. These are label counts, not evaluated category relevance, stock or proof that every idea has complete 3D support.
- No secrets, environment files, database contents, private customer scenes, live model calls or production state were inspected.

### Revalidated source loading and refresh

- `src/lib/biblioteca-sempertex/biblioteca.ts:1,321-334` statically imports `decoraciones.json`, validates each item using `DecoracionSempertexSchema` at module initialization, and derives `bibliotecaVisible()` by excluding `origen: ejemplo`. It has no catalogue polling, runtime file read, database subscription or TTL refresh. Recommender calls can derive from this authoritative visible list without another cache.
- `scripts/biblioteca/README.md:3-11,39-46` and `construir-biblioteca-real.ts:890-903` describe an explicit offline publication script. It combines existing non-real records, resolved references and curated JSON, writes `decoraciones.json`, then generates details. It does not run when the app loads. Its analysis/resolution actions can call external services; none was executed here.
- `scripts/biblioteca/precomputar-detalles-ideas.ts:1-29` checks/regenerates selection detail data; `precomputar-planes-ideas.ts` separately handles saved plans. These are selection/material artifacts, not a recommendation index. REQ-018 adds no second publication stage or automatic analysis job and does not repair known saved-plan drift.
- `src/app/api/asistente-guiado/route.ts:185,311,458` gets visible library ideas and sends actual records in `datos.decoraciones`. `VistaGuiada.tsx:721-728` consumes that response into the existing carousel. Additions/modified metadata in the next normally published library build must be reflected on fresh recommendations without editing recommender lists. An already deployed process/bundle is not expected to reread an edited source file; existing historical conversation cards remain historical.
- `src/components/guiado/fotos-biblioteca.ts:1-9` is a separate generated static sample-photo list consumed by `FotosEjemploGuiada.tsx`, not the recommendation carousel's source. Do not use or duplicate it for recommendations. This requirement does not expand the sample-photo picker.
- `ideas-guiadas.ts:190-208`, route tool/schema lines 46-47/301-324, explicit browse/photo branch 448-477, and final sanitation fallback 583-609 contain independent ways to reintroduce approximate results. `prompt-guiado.ts:7-15` and `respuesta-guiada.ts:287-383` currently prohibit an honest empty message and substitute style questions. All category recommendation entry paths must respect the strict outcome, including streamed and final text.
- `asistente-guiado-v1.ts:32-45` already accepts a partial brief. The route's local `BriefCompletoSchema` requires a theme. Category-only discovery must use the existing optional wire field rather than inventing a theme or weakening validation. No public DTO/version change is needed.

Revalidated checkout: canonical HEAD remains `5f9104980d31e0074c6bbb5ed16cae1e8c92a723`, 197 dirty status entries; 46 library records, 31 visible, 23 with total piece quantity one. No product files or REQ-017 files changed during this planning pass. Prior E8–E14 remain historical research; summaries about other branches do not establish availability in this checkout.

## Scope (in)

- Derive eligible records and category labels from the authoritative visible guided library. Retain schema validation and the complete design as the recommendation unit.
- A pure deterministic matching rule, a pure turn-decision rule, response handling and thin route integration. Reuse existing validated contracts and gallery; keep domain decisions out of the HTTP handler.
- Category-only recommendations; later explicit preferences and category changes recompute using the same strict rule. Reuse existing aliases only when they denote the same celebration; exact normalized labels discovered from the library also work without maintaining a new category list. Legacy affinity groupings are not equivalence proof.
- Selection and plan/edit/proposal/quotation safeguards, historical sessions and explicit browse requests receive regression coverage.
- No deadline supplied; no new ranking KPI, minimum count or external dependency is imposed.

## Out of scope

- New admin/editor, catalogue acquisition/import pipeline, new data source, runtime polling/hot reload, embeddings/RAG, provider integrations, catalogue unification or private-scene discovery.
- New decoration generation as a substitute for a missing match, individual-material recommendations, official-structure recommendation policy, pricing/material/geometry changes or repair of saved-library plans.
- Expanding `/3d`, classic chat, Happie or the sample-photo picker. Explicit bespoke proposals, photo analysis and plan operations continue only through their existing intentional flows.
- Integrating or copying isolated REQ-017 code. Its event-to-structure policy is separate from discovering finished library designs.
- This session: implementation, experiments, M1/M2 execution, product model/image calls, new providers, deployment, approvals, freeze, handoff, launch, commits, push or runtime changes. Only this SPEC and draft PLAN files may be written.

## Requirements

- R1. When one customer celebration/category is known in a discovery turn, `/asistente` shall offer actual matching existing designs immediately through its current gallery, without requiring theme, colours, age or gender first.
- R2. Every recommended record shall be a complete visible guided-library idea with its authoritative ID, title, photo/provenance and composition, including eligible single-structure designs; recommendations shall never be newly invented designs, materials or structure menus.
- R3. Recommendations shall require the requested category and all supplied supported explicit preferences to match; no event/theme/colour approximation or result padding is permitted. A small or empty set shall stay small or empty, including after tool calls, retries, browsing, photo-suggestion paths, sanitation and streaming. Empty results shall not force a clarification or generic fallback.
- R4. When the existing library source is added to or modified and normally published/built/deployed, fresh recommendations shall derive the new data automatically without ID whitelists, fixed 31-record assumptions, copied lists or additional recommender cache invalidation. Runtime hot reload is not required.
- R5. Customer intent, explicit design selection, current plans, approval/access boundaries and saved-session compatibility shall be preserved. Browsing or a category change shall not silently select a design, modify a plan, quote, generate an image or invoke a proposal.
- R6. The route, tool instructions, streamed/final response and gallery shall agree on matching/empty outcomes and partial brief state, with deterministic functional, integration, regression, static and product evidence that uses controlled doubles rather than paid/live providers.

## Matching and decision contract

These planning rules resolve implementation choices that can affect acceptance; they do not approve execution.

1. Inputs are validated visible library records, a customer-confirmed category, optional age/preferences and existing turn-intent facts. A pure matcher receives records explicitly; an application adapter obtains `bibliotecaVisible()` for each search. No singleton derived candidate cache or independently authored IDs/categories.
2. Match category against each record's `eventos` using normalized full labels or genuine same-celebration aliases (for example boda/matrimonio/casamiento). Existing broad affinity groups are not strict equivalence: bautizo must not become primera comunión, nor an unsupported event a generic fiesta. Preserve unrelated legacy helper behavior through an explicit strict query boundary rather than changing every consumer. Use phrase/token boundaries, case/accent normalization and prefer the longest matching label. Discover additional event labels from current visible records. Do not substitute a generic party, infer a category from colour or treat a title-only event mention as its category. Example: wedding plus white/black does not admit a birthday-only design of those colours.
3. Explicit refinements are conjunctive: requested theme/style must be evidenced in title/theme (literal normalized words/phrases or equivalent existing lexical aliases), every explicit colour must be present according to existing literal colour/tone classifiers, and stated gender/positive age restrictions must hold. Keep existing baby-shower gender interpretation only within eligible event candidates. Do not turn an absent character/theme into typical colours, use partial colour overlap or add model-selected preferences. Explicit negative preferences exclude matching literal evidence and are never counted as positive requests; explicit colour-only restrictions reject extra colours. Extra colours are allowed unless explicitly excluded/limited by the customer; a stated tone such as celeste cannot be satisfied merely by broad azul. Unknown theme/style remains unsatisfied rather than disappearing from the request. Age 0/absent means unknown, never a mandatory question. An absent optional refinement imposes no filter.
4. Keep the existing foreign-motif exclusion: a Halloween/football/seasonal motif requires that motif in the customer's category/theme. Do not hide ordinary single-structure ideas, infer decoration completion from structure count or rewrite identities/titles to make another event appear eligible.
5. Filter before deduplication/limit. Preserve source order for eligible results, deduplicate repeated IDs and normalized equivalent titles within that set, cap at the existing upper display limit six. There is no minimum. Every emitted result is an actual match; `coincidencia: exacta` is valid only after these predicates, never by relabeling legacy search output. Validation failures remain real errors, not successful empty searches.
6. Turn precedence: retain explicit cost/learn/plan queries and edits, explicit design choice, deliberate bespoke proposal/direct complete-piece requests and actual photo-analysis intent before automatic discovery. Explicit browsing with a current plan is read-only. An ordinary new/refined category discovery turn may show matching designs even with a plan visible, but never changes that plan or selected design. A mere incidental category mention during another action does not interrupt it.
7. Customer facts govern search: the latest unambiguous affirmative category in customer messages overrides a stale brief; otherwise keep the confirmed category only if no explicit replacement was requested. An explicit unsupported replacement (for example “ahora es una jubilación” after boda) yields no designs instead of reusing the stale wedding category. Do not detect negated or multiple competing categories as one arbitrary first match. An unknown category yields no designs. Genuine ambiguity may use the ordinary clarification flow; no clarification is required merely because a valid category/preferences yields zero results. Theme/colour replacements use the latest explicit customer change; omit missing fields rather than inventing placeholders. Retain independent explicit preferences across category changes unless the customer changes/removes them.
8. A discovery result is explicit `matching`, `empty`, `unknown/ambiguous category`, or `suppressed by existing intent`. Its brief is a resolved snapshot of the customer-confirmed partial brief, retaining unrelated known fields. It is not a delta that the UI could mistake for a replacement snapshot. Matching/empty outcomes are authoritative for all category recommendation entry paths: category-only, explicit browse, changed theme/category, tool search and final fallback. Photo-suggestion requests with an active category cannot bypass strict constraints; actual photo analysis remains its explicit flow.
9. Empty result: publish `decoraciones: []`, a short honest statement that no library designs match that request, and no automatic decoration/style alternatives or compulsory follow-up. Both streaming and final text must avoid claiming ideas are present. Prior transcript cards remain historical; they must not become the active selectable list after an empty/new category turn. The selected idea and plan remain intact.
10. Reuse `asistente-guiado.v1` partial `brief`, decoration schema, SSE event framing and gallery. Search tools accept category without theme; complete-brief validation continues to protect operations actually needing it. Optional fields stay absent; clients and restored old sessions remain readable. No new public field is necessary. Rollback of a later implementation restores its scoped code changes and previous recommendation policy without data migration; no rollback or deployment is performed now.

## Acceptance cases

| Case | Inputs / trigger | Observable result | Requirements |
|---|---|---|---|
| AC1 | Fresh “Es para una boda”, no theme/age/gender | Gallery in the same turn with wedding-labelled eligible ideas; no precondition question. Category-only search includes single-structure `deco-real-28-aro-blanco-dorado-y-nude`. | R1,R2,R6 |
| AC2 | “Navidad” or “Bautizo” with no optional preferences | Respectively one present matching idea (`deco-real-27-aro-navideno-verde-salvia` / `deco-real-28-aro-blanco-dorado-y-nude`); no filling to four/six. Snapshot IDs are test anchors, not eligibility code. | R1,R2,R3 |
| AC3 | Controlled wedding category with white AND gold | Only candidates carrying both colours and wedding; a black/gold candidate and a birthday-only white/gold candidate are excluded. No inferred nude preference. | R3,R5 |
| AC4 | Birthday + Spiderman, or category “jubilación” absent from current events | `decoraciones: []`, honest empty text, no typical-colour or general-party designs, no compulsory style question; streamed/final responses agree. | R3,R6 |
| AC5 | Controlled new eligible ID/event label, then changed title/theme/category and hidden-as-example variants in successive catalogue inputs | Search reflects addition/modification/removal without changing code, count constant or a recommender list. The adapter uses the authoritative visible catalogue; new labels match without an alias-table edit. Build/deploy propagation is documented and distinct from hot reload. | R2,R4 |
| AC6 | Current plan + “Muéstrame decoraciones de boda”; then zero matches | Results/empty update active recommendations, while plan, selected design and approval context remain unchanged. No proposal, quote or image operation; selecting “Me gusta esta” or a valid textual choice remains explicit. | R3,R5,R6 |
| AC7 | Edit/price/learn/explicit choice/direct-piece/custom-proposal/photo-analysis turn mentioning a category | Existing action wins; automatic gallery does not intercept it or invoke another action. Existing unknown/invalid IDs and validation failures keep their deliberate error behavior. | R5,R6 |
| AC8 | Prior brief birthday, customer “Ahora es una boda”; ambiguous “boda o cumpleaños”; negated “no es boda, es cumpleaños” | Latest affirmative category wins; ambiguity is not guessed; negation is not positive evidence. Preferences remain customer-authored. Historical cards never become a new selection accidentally. | R1,R3,R5 |
| AC9 | Partial category-only brief and restored old saved session | Wire schemas and UI accept absent theme; carousel shows current authoritative identity/photo; empty turn has no active gallery options and retains saved selection/plan. | R1,R2,R5,R6 |

## Assumptions and risks

- A1 (revisable matching convention): retain stable source order and upper limit six, without a new ranking target. This minimizes behavioral invention while enforcing C5; no minimum is introduced.
- A2 (revisable text convention): conservative literal/lexical evidence and existing tone/gender rules define supported refinements. Unrecognized style/character terms do not authorize approximation. A future semantic matching system would need separate scope/evidence.
- Existing static imports imply normal publication/build/deploy for source edits; runtime catalogue refresh is neither present nor required by “reflejar”. Existing library maintenance remains responsible for valid photos/details/plans; recommending a design does not guarantee unsupported 3D geometry or repair purchase drift.
- Existing tests intentionally expect nearby padding and “never no results”. Update only the conflicting assertions with equivalent strict/empty behavior tests; preserve customer-fidelity, no-repeat, identity and explicit-action regressions. Do not skip or weaken checks.
- REQ-017 helpers are isolated and unavailable in the supplied baseline. Use inspected canonical helpers, keeping public exports compatible if moved. Later merging shared route changes requires a separate integration review; this plan has no REQ-017 dependency.
- No material owner decision remains blocking for a scoped draft. Product choices are confirmed; plan approval and implementation authorization are separate and absent here.

## Verification performed

Historical v1 baseline evidence is retained below. During v2 planning both commands were executed again using `--import=tsx`, each exit 0; these passing legacy assertions do not demonstrate the new strict behavior:

- `node --import=tsx scripts/test/test-busqueda-biblioteca-sempertex.ts`: exit 0; legacy exact/nearby behavior passes. This does not prove REQ-018 acceptance.
- `node --import=tsx scripts/test/test-ideas-boda-guiada.ts`: exit 0; legacy padding/photo alternatives and customer-theme fidelity pass. New strict cases remain planned.
- Local JSON inspection: 46 total / 31 visible / 23 single-piece-quantity ideas; HEAD and 197 status entries reconfirmed. Current wedding labels: four; Navidad and Bautizo: one each.
- Prior evidence-path/whitespace checks and previous test results are retained as historical research, not current product validation. Current draft contract check and semantic self-review are recorded in PLAN.md after execution.
- No application lint/build/full suite or live providers run for this documentation-only planning change. No product completion, production state or approval inferred.

## Clarifications

### Round 1 — historical questions answered

The historical question/options/recommendations remain intact in `rounds/round-01.json` (status `answered`); only this SPEC is updated. Q → A:

1. **Q1 — Where should the first release show recommendations?** → `/asistente`, reusing its gallery (choice a).
2. **Q2 — Which existing designs count as assembled?** → complete visible guided-library ideas, including single-structure designs (choice a). “31” was the observed snapshot. Owner additionally requested updates; follow-up “si, reflejar” confirms source additions/modifications, without a new admin or acquisition system.
3. **Q3 — What does category mean here?** → celebration/event with optional theme/style/colours (choice a).
4. **Q4 — What new behavior should distinguish this from the existing recommendations?** → offer already-assembled designs when category is detected; no mandatory theme/colours first; preserve explicit intent/selection/current-plan safeguards (choice a).
5. **Q5 — What happens when there are too few exact matches?** → only actual matches (choice b), no decoration suggestions when none match; never pad or demand clarification to fill. The original nearby recommendation was rejected.

Original owner answer: “1) asistente 2) si, ademas que se actualize 3)si exactamente asi, 4)si, cuando detecte alguna categoria ofrecer decoraciones ya hechas 5) si faltan coincidencias no ofrecer nada”. Follow-up: “si, reflejar”. These are requirement decisions, not fabricated plan approval.

## Coverage and readiness

Goal, audience, scope, exclusions, flows, edge cases, acceptance and constraints are clear for this draft. Timeline is deferred (none supplied). PLAN.md/PLAN.json decompose R1–R6; execution and any further M1/M2 experiment are outside this session. Existing frozen external simulation evidence is preserved and supplies no difficulty or acceptance proof. Workflow metadata, rounds, approval, frozen revision and run artifacts remain unchanged. Narrative v2 retains unfrozen contract revision 1; no canonical frozen revision exists.

## V2 planning delta and current evidence

- The six requirements and C1-C5/C2a remain unchanged. Negative-preference wording above makes the existing exclusion rule explicit; it adds no broader semantic matching capability. Full partial-brief snapshots, unsupported/stale category changes, unknown positive themes, honest empty responses and restored selection remain normative.
- Corrected canonical Planner/WBS responsibility rules were applied after inspecting methodology `skill/scripts/bt_role_policy.py:11,36-39` and `skill/agents/runner.md:21-27`: test means execute/report; test authoring, fixtures and package registration mean implement; evidence interpretation means audit. This invocation edits no Planner source or installed role.
- V2 reinspection: canonical Pictures HEAD `5f9104980d31e0074c6bbb5ed16cae1e8c92a723`, 197 dirty entries; catalogue 46 total, 31 visible, 23 single-quantity ideas. Paths E2-E7 and publication/loading were revisited; broader E8-E14 remain retained historical evidence. No product or REQ-017 worktree was written.
- An esbuild `build` of the real `src/components/guiado/VistaGuiada.tsx` with `bundle:true,write:false,platform:browser,format:iife,jsx:automatic`, the existing `@` alias and development define succeeded in memory (6,299,698 bytes). This checks import/bundle feasibility only. Playwright's default executable path was absent; `/usr/bin/chromium` exists and the existing test precedent accepts `PLAYWRIGHT_CHROMIUM_EXECUTABLE`. No browser was launched and no new harness is credited as existing proof.
- No bounded research prerequisite is needed: concrete bundling and the existing browser precedent bound harness construction. Browser launch, network stubbing, session fixtures and behavioral assertions are implementation/verification work in T5, with medium estimate confidence and explicit blocker reporting.
- A distinct T8 audit owns cross-contract/product interpretation. This Planner's semantic self-review is neither that future independent review nor owner approval. Real deterministic/publication check outcomes are in PLAN.md.
