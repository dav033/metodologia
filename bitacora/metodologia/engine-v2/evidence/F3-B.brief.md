# Task F3-B — Researcher external knowledge store (`bt_knowledge`, external claims)

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
A store of external research knowledge, **separate from the code map** (its own SQLite DB), with ingest-only
writes, per master spec §11.5 (`/home/david/dev/metodologia/bitacora/metodologia/engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md`
lines 601–615, Spanish; also §11.1–11.4 for context) and CONTRACT §2 F3/§4.

The package `skill/scripts/bt_knowledge/` and `bitacora.py knowledge` already exist (code map; read its README and
code first and reuse its SQLite helpers, validation and secret rejection).

## You own
- New modules in `skill/scripts/bt_knowledge/` for the external store (e.g. `external.py`, `freshness.py`) and their
  tests in `bt_knowledge/tests/`; additive edits to `bt_knowledge/__init__.py`, `bt_knowledge/README.md` and
  `skill/scripts/bt_cli_knowledge.py` (new subcommands only; do not change existing code-map behaviour), and additive edits to `skill/scripts/bt_knowledge_adapter.py` (the only importer of the package) and `skill/scripts/tests/test_knowledge_integration.py` (lead authorization after your BLOCKED report).

## Contract (document it in the README as `research-claims/1`)
1. Input document `research-claims/1` (what Researcher returns):
   ```json
   {"schema": "research-claims/1", "project": "p", "contributor": "researcher:<run-id>",
    "claims": [{"topic": "library:requests", "claim": "requests 2.32 drops Python 3.7 support",
                "kind": "package_version|api_behavior|price|license|changelog|docs|security_advisory|other",
                "source": {"url": "https://...", "canonical": "https://...", "retrieved_at": "2026-10-23",
                           "published": "2024-05-20 or version", "locator": "section/line/anchor",
                           "excerpt": "<= 300 chars"},
                "confidence": "high|medium|low", "subplans": ["SP-1"], "independent_of": []}],
    "contradictions": [{"claim_ref": "<topic+claim fingerprint or text>", "source": {...}, "reason": "..."}]}
   ```
2. Store: SQLite WAL at `<bitácora root>/.state/knowledge/<project>.external.db` (separate file from the code map).
   One logical claim per canonical (topic, normalized claim text); evidence rows per independent source, deduplicated
   by canonical URL + locator; sources that merely repeat the same canonical source are **not** independent (do not
   inflate consensus).
3. Freshness policy per `kind` (defaults, configurable in code and documented): price 7 d, package_version 30 d,
   api_behavior 90 d, changelog 90 d, security_advisory 7 d, license 365 d, docs 180 d, other 90 d. A claim whose
   newest evidence is older than its window is `stale`; a claim with no verifiable source (no URL or retrieval date)
   is `unverified`; contradicted → `disputed` with both sides kept.
4. Rule: `stale`, `unverified` and `disputed` claims are **never** returned as facts: `query --facts-only` and the
   subplan dossier exclude them (list them separately as "needs re-verification").
5. Upstream change: `invalidate --topic X [--kind K] --reason ...` marks only the affected claims stale (history
   kept), never others.
6. Embedded instructions in sources are data: excerpts are stored as inert text; a claim/excerpt containing shell
   commands is accepted only as text and flagged `contains_instructions` (never executed or surfaced as an
   instruction); secrets are rejected as in the code map.
7. CLI: `bitacora.py [--project P] knowledge claims ingest <file|->`, `knowledge claims query [--topic] [--kind]
   [--facts-only] [--json]`, `knowledge claims dossier --subplan SP-1 [--max-bytes N]` (brief, bounded Markdown for a
   subplan brief), `knowledge claims invalidate ...`, `knowledge claims stats`.
8. Tests (automated, all §11.5 "pruebas futuras"): two Researchers studying the same library → one dossier with
   traceability; an upstream update invalidates only the affected claims; a contradicted source is kept as
   conflicting; a source with embedded instructions cannot make anything execute (assert no subprocess/eval path and
   the flag); a benchmark helper measuring bytes/time of a reused dossier vs re-ingesting raw research (print numbers).
   Plus: idempotent re-ingest, concurrent writers, restart survival, offline.

## Verify
`cd skill/scripts && python -m unittest discover -s bt_knowledge/tests` → 0; full suite per RULES.md.
