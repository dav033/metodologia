---
id: REQ-018
status: clarifying
created: 2026-10-18
track: standard
---
# REQ-018 — Category-based recommendations of assembled decorations

**Draft — research and elicitation only.** No owner answers or product approvals have been recorded for REQ-018. The recommendations below are proposals, not accepted defaults. No implementation-ready plan, milestones, task graph or execution estimates are published at this stage.

## Problem & goal

Owner request: “queremos implementar un sistema de recomendaciones en Pictures de decoraciones ya armadas según la categoría que esté requiriendo el usuario”.

The confirmed goal is to recommend existing assembled decoration designs relevant to the category requested by the user. Generating a new decoration, returning individual materials, or merely rearranging official structure IDs does not satisfy that goal.

The repository already searches and presents complete library ideas using event, theme, age and the latest message. What additional experience REQ-018 should provide is not yet confirmed: category-only discovery, stricter relevance, a different catalogue, or a different surface would produce different plans.

**Success looks like:** A user requesting an agreed category can discover relevant existing designs as identifiable, selectable designs. The eligible catalogue, category interpretation, recommendation trigger and treatment of approximate matches must be settled before this becomes a complete acceptance contract.

## Users / actors / stakeholders

- Confirmed: a Pictures user requesting a category; David is the product owner.
- Proposed actor for the first release: a customer in the guided assistant at `/asistente`. Taller users at `/3d`, classic-chat users and administrators are different possible audiences; Q1 remains open.
- No access to other customers' private saved content is implied by this request.

## Research evidence

Paths below identify inspected files. Repository facts describe the supplied checkout, not a verified production deployment or live database.

| ID | Observed evidence | Consequence for this requirement |
|---|---|---|
| E1 | [Pictures instructions](/home/david/dev/pictures/AGENTS.md:13), including verification rules at line 79; `CLAUDE.md` imports this file. | Preserve unrelated edits, catalogue authority, layer boundaries, runtime validation, explicit actions and meaningful regression checks. |
| E2 | [Guided idea schema](/home/david/dev/pictures/src/lib/biblioteca-sempertex/esquemas.ts:23) defines an idea ID, title, theme, events, age range, photos, pieces, materials and steps; origins are defined at line 39. [Visibility](/home/david/dev/pictures/src/lib/biblioteca-sempertex/biblioteca.ts:333) excludes `origen: ejemplo`. | A library idea is a concrete candidate for an existing assembled design. It is not just an official structure ID. |
| E3 | Local JSON inspection of [guided catalogue](/home/david/dev/pictures/src/lib/biblioteca-sempertex/decoraciones.json:1232): 46 records, 15 examples and 31 visible `referencia_real` records. Of the visible records, 23 have a total piece quantity of 1, six have 2 and two have 3. The multi-piece example begins at line 1414. | “Assembled” cannot silently be equated with “multiple structures”: that choice would remove 23 of 31 current ideas. Counts use the sum of `piezas[].cantidad`, not scene geometry. |
| E4 | [Guided search](/home/david/dev/pictures/src/lib/biblioteca-sempertex/biblioteca.ts:138) accepts event, age and theme; it uses exact/cercana matching, colour/event scores, generic fill and title deduplication through line 223. [Available themes](/home/david/dev/pictures/src/lib/biblioteca-sempertex/biblioteca.ts:337) come from visible ideas, falling back to all visible themes if no event matches. | Basic catalogue recommendations already exist; the new requirement needs a demonstrable difference. Current search is not a strict category filter. |
| E5 | [Guided orchestration](/home/david/dev/pictures/src/lib/ia/guiado/ideas-guiadas.ts:190) combines theme and the latest user text, handles baby-shower gender, and falls back to nearby ideas. [Known events](/home/david/dev/pictures/src/lib/ia/guiado/ideas-guiadas.ts:224) form a separate guided vocabulary. | Reuse must preserve explicit customer preferences and account for existing fallback rules. |
| E6 | [Guided API search tool](/home/david/dev/pictures/src/app/api/asistente-guiado/route.ts:301) requires both event and theme, publishes real ideas and audits the search. [Explicit requests to see ideas](/home/david/dev/pictures/src/app/api/asistente-guiado/route.ts:448) search the catalogue without replacing the current plan. | Showing designs when only the category/event is known is a possible new capability, not a confirmed requirement. Existing-plan precedence matters. |
| E7 | [Carousel](/home/david/dev/pictures/src/components/guiado/CarruselDecoraciones.tsx:131) shows a reference photo, `Referencia`/`Parecida` labels, title, theme and “Me gusta esta”. [Saved idea-plan contract](/home/david/dev/pictures/src/lib/plan/plan-de-idea.ts:5) preserves the idea's actual pieces and products rather than reconstructing them from structure names. | Existing display and selection contracts are relevant; browsing, selection, plan creation and quotation are distinct actions. |
| E8 | [Taller library types](/home/david/dev/pictures/src/lib/globos3d/biblioteca.ts:35) distinguish `escena` (complete scene), `conjunto` (decorated structure), bare `estructura`, small `decoracion`, and `utileria`. Own library items are described at lines 49 and 121. | In this library, a `decoracion` can be a small flower or balloon. Filtering that type would not implement the owner's goal. |
| E9 | [Taller taxonomy](/home/david/dev/pictures/src/lib/taller/taxonomia-celebraciones.ts:8) separates celebration from theme and explicitly distinguishes guided-chat and Shopify vocabularies. [Classification](/home/david/dev/pictures/src/lib/taller/clasificacion-biblioteca.ts:4) assigns celebration/theme labels to factory items; derived pieces inherit scene labels. | “Category” could mean occasion, theme or structure type. No universal category field across all these catalogues was established. |
| E10 | [Taller memory search](/home/david/dev/pictures/src/lib/globos3d/herramientas-escena-biblioteca.ts:123) filters by item type, occasion, piece type and colours. [Online search](/home/david/dev/pictures/src/lib/taller/buscar.ts:323) supports RAG with a memory fallback. | A broader assembled-scene recommender has existing search infrastructure, but sharing it with the guided assistant is a material scope/contract choice. No online query was executed. |
| E11 | [Catalogue registry adapter](/home/david/dev/pictures/src/lib/catalogo/repositorios/sempertex/entradas-guiada.ts:14) states that guided chat still reads its own files; [Taller adapter](/home/david/dev/pictures/src/lib/catalogo/repositorios/sempertex/entradas-biblioteca.ts:7) exposes factory/derived items separately. | The common Sempertex repository does not make the guided and Taller candidate sets interchangeable. |
| E12 | [Legacy decoration type](/home/david/dev/pictures/src/lib/types.ts:76) stores name, description, cover image and product IDs, with no event/theme fields in that type. [Legacy reader](/home/david/dev/pictures/src/lib/decoraciones.ts:39), [API](/home/david/dev/pictures/src/app/api/decoraciones/route.ts:14) and [admin form](/home/david/dev/pictures/src/components/admin/DecoracionForm.tsx:49) are a third decoration path. | Do not mistake this CRUD catalogue or its products for the guided ideas. Database contents and runtime availability were not inspected. |
| E13 | [REQ-017 scope and exclusions](/home/david/bitacora/pictures/requirements/REQ-017-activity-aware-guided-chat-decoration-re/SPEC.md:20) cover event-specific official-structure menus and free-composition constraints, and explicitly exclude changes to library search/carousel. [D-052](/home/david/bitacora/pictures/DECISIONS.md:304) keeps its defaults revisable. | REQ-018 can address discovery of existing designs without duplicating REQ-017's event-to-structure policy. Its open round is not approval for REQ-018. |
| E14 | [Project summary](/home/david/bitacora/pictures/SUMMARY.md:43), REQ-017 `REPORT.md` and [P-101](/home/david/bitacora/pictures/PENDING.md:27) report isolated completion and pending policy review. Direct inspection of [worktree event map](/home/david/dev/pictures-wt/req-017-v2/src/lib/plan/estructuras-por-evento.ts:8) and [proposal policy](/home/david/dev/pictures-wt/req-017-v2/src/lib/ia/guiado/politica-propuesta-evento.ts:23) confirms the structure-based approach. | Those files are isolated, uncommitted work, not functionality in the canonical supplied checkout. Prior reported checks were not rerun here. |

### Checkout provenance and limits

- Canonical inspection root: `/home/david/dev/pictures`, branch `feat/req-014-72h-marathon-autonomous-product-developm`, HEAD `5f9104980d31e0074c6bbb5ed16cae1e8c92a723`. “Canonical” here means the owner-supplied checkout, not a clean `main` or production assertion.
- At inspection: 197 status entries (159 modified, two deleted, 36 untracked). `git diff --shortstat`: 161 files changed, 1,038 insertions and 748 deletions. The guided search/schema/API/UI paths inspected above have no local tracked diff. Existing changes were preserved.
- Related inspected worktree: `/home/david/dev/pictures-wt/req-017-v2`, branch `feat/req-017-activity-aware-v2`, HEAD `75c8749792b893f9e07cb4305d1c9ce2bbfd6a88`, 16 status entries. Its extracted normalizer/event helpers and structure policy are not assumed available in the canonical checkout.
- `project.json` lists the Pictures mapping and historical worktree hints; only the supplied Pictures checkout and the relevant REQ-017 worktree were used for code evidence. `git worktree list` and recent library history were inspected. No remotes were fetched.
- Read Pictures `SUMMARY.md`, `PENDING.md`, `DECISIONS.md`, relevant `ARCHITECTURE.md`, REQ-017 SPEC/PLAN/report/open round, global memory and Pictures memory index/known pitfalls. Historical summaries can describe other branches; code and the explicit checkout mapping govern observations here.
- Catalogue count: local Python JSON inspection; exact visible event labels include four Boda ideas, one Bautizo idea and one Navidad idea. These are label counts, not evaluated category relevance, stock or proof that every idea has complete 3D support.
- No secrets, environment files, database contents, private customer scenes, live model calls or production state were inspected.

## Scope (in)

Confirmed intent: recommend existing assembled designs by the user's requested category, retaining the design as the recommendation unit. The following candidate slice is **proposed only**, pending Q1–Q5:

- Guided-assistant discovery using the existing visible idea catalogue, including finished designs built from a single structure.
- Category interpreted as event/celebration, with theme/style/colours refining relevance when supplied.
- Present existing designs when the event/category is known, without forcing a theme first; refine the same discovery flow as preferences arrive.
- Reuse photo/title/theme and explicit selection; browsing recommendations should preserve the current plan.
- Offer exact matches first and identifiable nearby existing designs when necessary, subject to the answer about strict matching.

Changing the surface or candidate set changes this slice; these bullets are not authorized implementation instructions.

## Out of scope

- Confirmed exclusions: treating newly generated designs, individual materials or an ordering of structure IDs as the requested recommendation system.
- Current planning-session exclusions: implementation, Scheduler execution, M1/M2 runs, paid AI/image calls, deployment, commit, push, approvals, freezing, handoff or installed configuration changes.
- Proposed MVP exclusions, not yet owner-approved: new catalogue authoring/imports, private saved scenes, catalogue unification, new taxonomies, pricing/material-engine changes, automatic plan replacement, Happie packages and a new admin/editor workflow. Revisit these if Q1–Q3 select a broader catalogue or surface.

## Requirements

Only the following goal-level requirements are established. Detailed rules and acceptance cases remain incomplete until Q1–Q5 are answered.

- R1. When a user requests an agreed category with eligible existing assembled designs, the system shall recommend relevant existing designs from the agreed catalogue.
- R2. When presenting a recommendation, the system shall retain an identifiable existing design as the recommendation unit; a generated replacement, raw materials list or bare structure-ID menu alone shall not satisfy R1.

### Acceptance anchors — incomplete, not an implementation contract

- AC1 (R1): Given an owner-agreed category and known eligible designs, requesting recommendations exposes the agreed relevant designs on the selected surface. Category examples, eligible IDs, ordering and trigger await Q1–Q4.
- AC2 (R2): Every recommended result resolves to an existing eligible design with its actual identity and composition; none is invented or replaced by a list of materials or structure IDs.
- AC3 (proposed, Q4): Merely browsing recommendations leaves an existing plan unchanged; choosing a design follows an explicit action. No new automatic quotation or image generation is implied.
- AC4 (proposed, Q5): Exact, nearby, unknown-category and empty-catalogue cases have distinct agreed outcomes; an alternative is never falsely asserted to be an exact category match.
- Before planning: record category→eligible-design examples, at least one thin/empty case, explicit preferences and category changes, plus the expected selectable result. An unchanged passing legacy search test does not by itself prove REQ-018 delivered a new capability.

## Edge cases & errors

- Category-only request versus a request that also names theme, colour, age or structure; choose the meaning/precedence in Q3–Q4.
- Finished single-structure design versus multi-piece scene; scope changes substantially depending on Q2.
- Sparse categories: the catalogue has only one explicitly labelled Navidad and one Bautizo idea. Do not impose a minimum result count by inventing designs.
- Unknown or ambiguous category, conflicting preferences, no exact results and no eligible results; Q5 determines whether to offer nearby items or ask for clarification.
- Existing plan and selected idea, a request to browse more designs, category change and reopened conversations; preserve applicable existing contracts and do not let a recommendation silently edit a plan.
- Missing/nonrepresentative photo, unavailable plan, or a design containing structures without 3D support: recommendation eligibility must not be equated with guaranteed render/quotation support. Follow the existing explicit selection/fallback path unless expanded by the owner.
- If a broader online catalogue is selected, define timeout, unavailability, authorization and fallback acceptance in the next draft; the current code-only inspection is not integration evidence.

## Constraints

- This session is the canonical Planner stage only. The caller pins `codex-luis / gpt-6.1-sol / high`; retain those pins, with no fallback, account switch or retries. This is a supplied execution constraint, not a Planner assignment or a product-model decision.
- Write only this requirement's `SPEC.md`, `PLAN.md`, `PLAN.json` and an optional directly derived diagram. This pass updates only `SPEC.md`; central logs, other requirements, approval/run/revision state and all product files stay untouched.
- Keep the present `clarifying` state. No prior Pictures approval, D-052 assumption or experiment authorizes REQ-018 implementation.
- Product contracts remain authoritative for IDs, photos/provenance, materials, prices, selection, saved sessions and plan approvals. Preserve existing privacy/access boundaries; never include another user's private library implicitly.
- No model-generated category taxonomy, catalogue expansion or paid embedding/reindexing work is assumed necessary. Select the actual source and semantics before choosing an algorithm.

## Priorities & phases

- Must: preserve the owner's existing-design/category intent and settle the five material choices below.
- Proposed first release: improve discovery on the agreed existing surface/catalogue. Ranking sophistication, result count and success metrics beyond the acceptance anchors remain unspecified rather than assigned arbitrary targets.
- Broader surfaces, private libraries and catalogue expansion depend on owner answers; no delivery milestones or task dependencies have been assigned yet.

## Timeline & dependencies

- No deadline supplied. No duration, cost or quota estimate made.
- Readiness depends on Q1–Q5, followed by concrete category/design acceptance examples and task decomposition.
- REQ-017 overlap is known, but integration is not automatically a prerequisite: determine the target baseline after the surface/catalogue choice. If its extracted helpers are needed, declare that dependency explicitly in the eventual plan; do not import isolated work as canonical functionality.
- Future owner intent: pass an approved real plan to isolated M1/M2 for an experiment. That later test is not a current execution instruction or implementation approval.

## Assumptions

No unanswered choice is treated as accepted. A1–A5 below are the revisable recommendations behind Q1–Q5, not permission to proceed with dependent implementation:

- A1: `/asistente` is the first surface, because it already exposes real design ideas and explicit selection.
- A2: Each visible guided-library idea is a complete recommendation unit, even if it contains only one structure. Include the full design rather than extracted pieces; do not include legacy CRUD records, private saved items or every Taller item implicitly.
- A3: “Category” primarily means event/celebration; optional theme/style/colours refine it. Taller and guided vocabularies remain distinct until an explicit mapping is justified.
- A4: The new product difference is category-first discovery without requiring theme/colours before showing designs. Exact existing designs are shown with photo/title and explicit choice; no automatic plan replacement.
- A5: Preserve the useful existing exact/nearby distinction and mark alternatives, while agreeing on unknown/empty behavior rather than pretending an unrelated design is exact.

## Verification performed

These checks ran in `/home/david/dev/pictures` during research, without network or model calls:

| Category | Command | Actual result and limit |
|---|---|---|
| Functional / existing behavior | `node --import tsx scripts/test/test-busqueda-biblioteca-sempertex.ts` | Exit 0. Existing real-idea visibility, supported themes, exact/nearby ordering and search regressions passed. Does not validate new REQ-018 behavior. |
| Regression / existing behavior | `node --import tsx scripts/test/test-ideas-boda-guiada.ts` | Exit 0. Existing customer-theme fidelity, nearby wedding ideas and photo-similarity/no-repeat regressions passed. No UI or live quotation validation. |
| Static / draft integrity | Local Python checks of Markdown evidence paths/line numbers, whitespace, metadata and question count | Exit 0. All 29 local evidence links resolve with in-range lines; no trailing whitespace/tabs; final newline present; original `clarifying` metadata retained; five open questions; only `SPEC.md` exists in this requirement directory. |

The scoped `git diff --no-index --check /dev/null <SPEC.md>` emitted no whitespace diagnostics and returned 1 for the new-file difference; the explicit Python whitespace check above passed with exit 0. Post-research Git status counts and tracked diff summaries in Pictures and `req-017-v2` match the initial inspection. No product edit was performed.

Lint, full type checks, build, full suite, browser/product acceptance and live integrations were not run for this draft-only change. `bt_planner check` was not run: no `PLAN.md` or `PLAN.json` is published while material product choices are unresolved. The draft is not contract-validated or ready for approval/execution.

## Semantic self-review

This is the same Planner's evidence-based self-review, not an independent audit or approval.

- **Fact:** Existing guided recommendations already use event/theme and real design IDs (E2–E7; both executed tests pass). Correction: require an explicit behavioral delta before scheduling implementation; do not claim the basic capability is missing.
- **Product decision, blocking:** Surface and eligible unit/catalogue are unconfirmed (owner wording; E2/E8/E12). Correction: Q1–Q2 before architecture or file ownership is assigned.
- **Product decision, blocking:** Category semantics, trigger and strict/nearby policy are unconfirmed (owner wording; E4–E6/E9). Correction: Q3–Q5 and concrete category/design acceptance examples.
- **Plausible risk:** A strict category filter may contradict the existing generic-fill and tone behavior, especially on thin categories (E4–E6 and E3 counts). Correction: define the owner-selected empty/nearby behavior and its regressions explicitly.
- **Plausible risk:** Reusing REQ-017 helpers without a baseline decision would depend on unintegrated local changes (E13–E14 and direct worktree diff). Correction: preserve isolation and declare any later integration prerequisite rather than assuming it is shipped.
- No orphan task, dependency or interface review is claimed: those artifacts do not exist yet. Deterministic plan validation belongs to the next planning stage after these choices are resolved.

## Coverage

| Topic | State |
|---|---|
| Goal & problem | Partial — existing-design/category goal clear; new behavioral delta open in Q4 |
| Users / actors | Partial — Pictures user confirmed; surface/audience open in Q1 |
| Scope | Partial — candidate catalogue/unit open in Q2 |
| Out of scope | Clear for this session and semantic exclusions; MVP boundaries proposed |
| Flows & behavior | Partial — category semantics and trigger open in Q3–Q4 |
| Edge cases | Partial — thin coverage established; fallback choice open in Q5 |
| Acceptance criteria | Partial — goal-level anchors only; category/design cases follow answers |
| Constraints | Clear for this planning session; product integration constraints depend on selected scope |
| Priorities & phases | Partial — proposed first release only; no milestones authorized |
| Timeline | Deferred — no deadline supplied; implementation and experiment are later stages |

## Clarifications

### Round 1 — catalogue, categories and experience — open

No answers received. The standard round's questions are kept in this permitted artifact and the conversation; no `rounds/` file, web round or workflow-state mutation is authorized for this pass.

1. **Q1 — Where should the first release show recommendations?** Recommended: the existing guided assistant `/asistente`, reusing its design gallery. Alternatives: Taller `/3d`, classic chat, or multiple surfaces. Evidence: E6–E8/E12; the choice changes actor, integration and acceptance.
2. **Q2 — Which existing designs count as assembled?** Recommended: the 31 currently visible guided ideas as complete designs, including single-structure designs, without extracting their components. Alternatives: only multi-piece compositions, the Taller's full scenes/decorated sets, or a specific catalogue supplied by the owner. Evidence: E2–E3/E8/E12; there are 23 single-piece-quantity ideas and eight multi-piece ones in the proposed set.
3. **Q3 — What does category mean here?** Recommended: event/celebration (birthday, wedding, baby shower), optionally refined by theme/style/colours (safari, elegant, white/gold). Alternatives: theme as the main category, structure type such as arches/columns, or another business taxonomy. Evidence: E2/E4/E9; these are different concepts in current code.
4. **Q4 — What new behavior should distinguish this from the existing recommendations?** Recommended: show relevant existing designs as soon as the event/category is known, without first requiring theme/colours, then refine them; keep explicit selection and the current plan. Alternatives: keep the trigger and improve relevance only, or specify another discovery flow. Evidence: E4/E6–E7; current tool search requires both event and theme.
5. **Q5 — What happens when there are too few exact matches?** Recommended: exact matches first, then existing alternatives explicitly marked “Parecida”; if there are no eligible designs or the category is ambiguous, ask the user to refine the category without inventing a design. Alternatives: strict category matches only, or offer alternatives only when the user requests them. Evidence: E3–E7; current behavior fills with nearby/general ideas and some event labels have only one design.
