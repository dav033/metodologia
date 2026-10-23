---
name: subplan-dependency-analysis
description: Inspect a codebase read-only to map producer-consumer relationships among functional subplans and return deduplicable graph observations with revision-bound evidence.
---

# Subplan dependency analysis — Explorer private skill

## Trigger
Load when the request mentions a subplan dependency, API consumer, transitive caller, changed contract, design-to-code relation or blast radius. Remain **read-only**; no file, database, index, ref or graph write. Graph persistence belongs to a separate deterministic ingestor.

## Procedure
1. **Anchor the question.** Record project/repository, observed Git SHA, focused subplan IDs and public contract revision(s), if supplied. Do not invent missing subplans for a legacy plan.
2. **Reuse curated evidence.** Query the existing project knowledge map for the same SHA/contract before exploring. Treat stale observations as leads only, not current facts. Do not assume map availability.
3. **Search narrowly.** Use CodeGraph for symbol and call paths when indexed, otherwise Grep/Glob/Read. Verify each crucial reference in source with `path:line`; mark dynamic imports, reflection, runtime wiring and generated routes as completeness limits.
4. **Identify surfaces.** Discover producer interfaces, consumers, callers/callees, events, schemas, DB/queue contracts, tests, UI contract references and shared state. Separate a direct edge from a plausible transitive impact.
5. **Form facts, not judgments.** Emit normalized triples `(subject, relation, object)` and evidence, observed SHA, entity kind, verification level (`observed`, `inferred`, `unknown`), and an optional proposed impact query. Do not pronounce other subplans incompatible or order implementation changes.
6. **Reduce duplication.** Prefer one canonical relation identity per subject/relation/object; list additional **independent** evidence separately. Avoid replaying identical observations already present in the map; corrections and contradictions are explicit deltas.
7. **Deliver to ingestor.** Return a compact structured report. The ingestor validates schema, version, deduplicates, upserts transactionally and marks stale entries; Explorer never calls its mutation API directly unless the runtime exposes a read-only submission channel with separate authorization.

## Output sketch (not an implemented runtime schema)
```yaml
observed_commit: '<SHA or unknown>'
observations:
  - subject: 'subplan:checkout'
    relation: 'CONSUMES'
    object: 'contract:auth/session@v1'
    status: 'observed'
    evidence: ['src/checkout/session.ts:42']
    prior_observation: 'same|additional_evidence|changed|unknown'
gaps: ['dynamic consumers not established']
```

## Safety and scope
Reading `.env`/secrets, running mutating scripts or indexing CodeGraph autonomously is prohibited. Graph-engineering provides evidence discipline, **not** authority to invent a fresh competing graph DB. Planner/M6 decide impact and acceptance; information is always indexed to a source revision.
