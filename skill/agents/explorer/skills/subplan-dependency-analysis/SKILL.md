---
name: subplan-dependency-analysis
description: Inspect a codebase read-only to map producer-consumer relationships among functional subplans and return deduplicable graph observations with revision-bound evidence.
---

# Subplan dependency analysis — Explorer private skill

## Trigger
Load when the request mentions a subplan dependency, API consumer, transitive caller, changed contract, design-to-code relation or blast radius. Remain **read-only**; no file, database, index, ref or graph write. Graph persistence belongs to a separate deterministic ingestor.

## Procedure
1. **Anchor the question.** Record project/repository, observed Git SHA, focused subplan IDs and public contract revision(s), if supplied. Do not invent missing subplans for a legacy plan.
2. **Reuse curated evidence.** Read `scripts/bt_knowledge/README.md` for the full contract, then query the project knowledge map using `bitacora.py knowledge query --commit <sha> --area <area> --json`. Treat stale observations as leads only, not current facts. If the map/query is unavailable, say so and continue without it. Explorer never calls `knowledge ingest`.
3. **Search narrowly.** Use CodeGraph for symbol and call paths when indexed, otherwise Grep/Glob/Read. Verify each crucial reference in source with `path:line`; mark dynamic imports, reflection, runtime wiring and generated routes as completeness limits.
4. **Identify surfaces.** Discover producer interfaces, consumers, callers/callees, events, schemas, DB/queue contracts, tests, UI contract references and shared state. Separate a direct edge from a plausible transitive impact.
5. **Form facts, not judgments.** Use the graph-engineering discipline of a smallest useful, evidence-backed map; keep observed facts separate from inference, proposals and unknowns. Emit canonical `kind:name` entity IDs and only these uppercase relations: `IMPORTS`, `CALLS`, `IMPLEMENTS`, `PUBLISHES`, `CONSUMES`, `PRODUCES`, `CONFIGURES`, `TESTS`, `DEPENDS_ON`, `DEFINES`, `EXPOSES`, `CONTAINS`, `OWNS`, `REFERENCES`. Status is `observed`, `inferred`, `proposed` or `unknown`. Do not pronounce other subplans incompatible or order implementation changes.
6. **Reduce duplication.** Prefer one canonical relation identity per subject/relation/object; list additional **independent** evidence separately. Avoid replaying identical observations already present in the map; corrections and contradictions are explicit deltas.
7. **Deliver to ingestor.** Return a `knowledge-delta/1` JSON block with top-level `schema`, `project`, `repository`, `observed_commit`, `contributor`, `observations`, `contradictions` and `stale`. Each observation has `subject`, `relation`, `object`, `status` and `evidence` (`path:line`). Include only new evidence, corrections, contradictions or staleness updates; an empty delta is valid. The executor/lead ingests the block with `bitacora.py knowledge ingest`. Explorer never writes to the map or calls its mutation API.

## Output block

Return valid JSON in this shape; use empty arrays when there are no deltas. This is an interface contract, not an
instruction to create or edit a file:

```json
{
  "schema": "knowledge-delta/1",
  "project": "<project-id>",
  "repository": "<repository-id>",
  "observed_commit": "<full Git SHA>",
  "contributor": "<agent or run identity>",
  "observations": [
    {
      "subject": "subplan:checkout",
      "relation": "CONSUMES",
      "object": "contract:auth-session-v1",
      "status": "observed",
      "evidence": ["src/checkout/session.ts:42"]
    }
  ],
  "contradictions": [],
  "stale": []
}
```

Use project/repository identities and the precise contradiction/stale item shapes defined by
`scripts/bt_knowledge/README.md`; do not invent aliases or optional keys. Put explanatory gaps in the normal short
answer, not in the JSON schema. Zero new deltas (`observations`, `contradictions` and `stale` empty) is valid.

## Safety and scope
Reading `.env`/secrets, running mutating scripts or indexing CodeGraph autonomously is prohibited. Graph-engineering provides evidence discipline, **not** authority to invent a fresh competing graph DB. Planner/M6 decide impact and acceptance; information is always indexed to a source revision.

## Upstream technique references

- **Adapted, approved:** [douinc/agent-skills — graph-engineering](https://github.com/douinc/agent-skills/blob/99ec1c314078a37a55a8534682b20a7a52683907/skills/graph-engineering/SKILL.md), commit `99ec1c314078a37a55a8534682b20a7a52683907`, MIT (`LICENSE`). Borrow the minimal question-scoped graph, evidence on claims, explicit epistemic status and no required graph database. Its persistence decision is replaced by the read-only delta/ingestor boundary above.
- **Candidates only; not adopted into Explorer's prompt or procedure:** [Data-System-School/agent-skills — investigate-codebase](https://github.com/Data-System-School/agent-skills/blob/a117418ab3596c59d641cab4cb89bdbe560fb277/investigate-codebase/SKILL.md), commit `a117418ab3596c59d641cab4cb89bdbe560fb277`, MIT (`LICENSE`); [event4u-app/agent-config — blast-radius-analyzer](https://github.com/event4u-app/agent-config/blob/4502d328ff6402f0dfb7bc1b970007179587282f/src/skills/blast-radius-analyzer/SKILL.md), commit `4502d328ff6402f0dfb7bc1b970007179587282f`, MIT (`LICENSE`). These are cited for future evaluation only; neither is loaded or applied here.
