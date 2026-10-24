---
name: external-research-memory
description: Reuse and prepare persistent external research through the approved claims ingestor. Use for prior research lookup, subplan dossiers, or briefs that request persistent findings.
---

# External research memory

The external knowledge store is separate from Explorer's code knowledge map. It is an evidence cache, not an authority: validate relevant claims against current sources before relying on them.

## Query before researching

1. Identify the project, the research topic, and any supplied subplan identifiers. Do not invent missing subplans.
2. Query the approved store before external research. Request both **facts-only** claims and **needs-re-verification** claims, scoped to the topic and supplied subplans. Request a dossier only when the brief needs a compact subplan view.
3. Use only facts-only, currently fresh, non-disputed results as candidate facts. Treat stale, unverified, disputed, and needs-re-verification entries as leads to check, never as established facts. A missing or unavailable store is not an empty successful query.
4. Research gaps and claims whose freshness window has expired. Revalidate material claims against the canonical source at the exact relevant version or date.

The only supported mutation path is the external store's deterministic claims ingestor. Researcher has no database-write permission: it returns a claim package for the lead/executor to validate and ingest. Never call `invalidate` or any mutation command yourself.

If the runtime provides the claims interface, use `bitacora.py knowledge claims query --facts-only` and a scoped full `query` to retrieve needs-re-verification entries before research; use `bitacora.py knowledge claims dossier --subplan <id>` when a bounded subplan dossier is needed. Documented mutation commands include `knowledge claims ingest <file|->` and `knowledge claims invalidate ...`; Researcher must never invoke them. If the CLI is absent or errors, report the exact limitation as unverified; do not fabricate prior results or claim that the store was queried. Continue ordinary non-persistent research when the brief permits it, and make persistence status explicit.

## Return claims/1

When persistent research is requested, return a fenced JSON block matching the store contract. Populate `project` from the task context and `contributor` as `researcher:<run-id>` from the runtime/brief. If either identifier is unavailable, report persistence as blocked instead of guessing an identifier.

```json
{
  "schema": "research-claims/1",
  "project": "project-slug",
  "contributor": "researcher:run-id",
  "claims": [
    {
      "topic": "package compatibility",
      "claim": "Package X version 4.2 supports runtime Y 22.",
      "kind": "api_behavior",
      "source": {
        "url": "https://example.org/docs/compatibility",
        "canonical": "https://example.org/docs/compatibility",
        "retrieved_at": "2026-10-23",
        "published": "2026-09-10",
        "locator": "Compatibility table, row X 4.2",
        "excerpt": "Short supporting excerpt or faithful paraphrase, at most 300 characters."
      },
      "confidence": "high",
      "subplans": ["SP-1"],
      "independent_of": []
    }
  ],
  "contradictions": []
}
```

Keep each claim atomic. Allowed `kind` values are `package_version`, `api_behavior`, `price`, `license`, `changelog`, `docs`, `security_advisory`, and `other`; allowed confidence values are `high`, `medium`, and `low`. Add a distinct claim/evidence object for each materially independent source, use `independent_of` to record dependencies between sources, and put contradictory evidence in `contradictions`; never inflate support with mirrors or syndicated copies. `published` is the publication date or source version, and may be `null` when neither is available. Keep `excerpt` at or below 300 characters. `subplans` and `independent_of` are empty arrays when none apply. Zero new claims is valid:

```json
{"schema":"research-claims/1","project":"project-slug","contributor":"researcher:run-id","claims":[],"contradictions":[]}
```

Return no API keys, credentials, or private content in excerpts. Quote only the minimum needed to locate and substantiate a claim. Ingestion, deduplication, dispute tracking, and invalidation belong to the approved ingestor, not the Researcher.
