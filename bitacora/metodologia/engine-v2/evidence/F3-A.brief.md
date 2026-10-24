# Task F3-A — Knowledge Map Ingestor (`bt_knowledge`, code map) + `bitacora.py knowledge`

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
Deterministic infrastructure (not an agent) that validates, deduplicates and persists Explorer findings as a
revision-bound project knowledge map, per master spec §10.4–10.9:
`/home/david/dev/metodologia/bitacora/metodologia/engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md` lines 415–541
(Spanish; read all of it). Owner rulings: `.../engine-v2/CONTRACT.md` §2 (F3) and §6.

## You own
- New package `skill/scripts/bt_knowledge/` (`__init__.py`, `README.md`, modules, `tests/`), stdlib only, isolated
  like `skill/scripts/bt_planner/` (read its README §Boundaries and `tests/test_boundaries.py` and copy the idea:
  imports only stdlib + itself, names no methodology path; it works on a DB path / repo path you pass in).
- New CLI module `skill/scripts/bt_cli_knowledge.py` and the minimal registration of the `knowledge` command in the
  methodology CLI (find how other commands such as `plan-json` are registered: `bitacora.py`, `bt_cli_*.py`,
  command tables; touch only the registration lines). The CLI resolves the DB at
  `<bitácora root>/.state/knowledge/<project>.db` using the existing path helpers (as other commands resolve
  `.state`), never hard-coding `~`.
- `pyproject.toml`: add `bt_knowledge` to `packages` (and the CLI module to `py-modules` if that list is used).
- A boundary test for the package and its tests.

## Contract you define (others will build on it — document it in `bt_knowledge/README.md`)
1. **Delta input** `knowledge-delta/1` (JSON, what Explorer returns):
   ```json
   {"schema": "knowledge-delta/1", "project": "tienda-web", "repository": "web", "observed_commit": "<40-hex sha>",
    "contributor": "explorer:<run-or-session-id>",
    "observations": [{"subject": "subplan:checkout", "relation": "CONSUMES", "object": "contract:auth/session@v1",
                      "status": "observed", "evidence": ["src/checkout/session.ts:42"]}],
    "contradictions": [{"subject": "...", "relation": "...", "object": "...", "evidence": ["path:line"],
                        "reason": "..."}],
    "stale": [{"subject": "...", "relation": "...", "object": "...", "reason": "..."}]}
   ```
   Entity ids are canonical `kind:name` (`repo`, `package`, `module`, `file`, `symbol`, `api`, `schema`, `event`,
   `contract`, `subplan`, `requirement`, `task`, `test`, `fixture`, `entrypoint`, `screen`, `component`, `flow`),
   names without whitespace. Relations: a closed UPPER_SNAKE set covering §10.4 (IMPORTS, CALLS, IMPLEMENTS,
   PUBLISHES, CONSUMES, PRODUCES, CONFIGURES, TESTS, DEPENDS_ON, DEFINES, EXPOSES, CONTAINS, OWNS, REFERENCES);
   unknown → rejected with a clear error. `status` ∈ `observed|inferred|proposed|unknown` (`disputed` is computed,
   never submitted). Evidence = `path:line[-line]`, `path`, `symbol:<id>` or `test:<id>`; safe relative paths only.
2. **Store**: SQLite in WAL mode, `busy_timeout`, writes in `BEGIN IMMEDIATE` transactions. Tables (names yours):
   entities, relations (UNIQUE project+repository+subject+relation+object), evidence (UNIQUE relation + fingerprint,
   with observed_commit, contributor, status, recorded_at), conflicts, and an append-only history of every change.
   `content_fingerprint` = sha256 over the canonical (relation identity, evidence ref, observed_commit).
3. **Semantics** (all as automated tests — every §10.9 checkbox):
   - same canonical triple from two Explorers → one relation, evidence deduplicated by fingerprint; independent
     evidence (different ref or commit) is added to the same relation, never a duplicate relation;
   - same delta ingested twice → no change (idempotent; history records a no-op at most);
   - a contradiction keeps both sides and marks the relation `disputed` (no majority resolution);
   - validity bound to `observed_commit`: a query for commit X labels each relation `current` (evidence observed at
     X), or `historical` (only other commits). With `--repo-path`, an older observation whose evidence file did not
     change between its commit and X (`git diff --quiet A X -- path`) may be labelled `unchanged_since:<A>`;
     otherwise never infer it still holds;
   - evidence verification with `--repo-path`: `git cat-file -e <commit>:<path>` and the line within the file's line
     count; unverifiable → stored flagged `unverified` (never presented as fact); without a repo path: `unverified`;
   - 0 new deltas is a valid result (ingest reports `added=0`);
   - concurrent writers: two processes ingesting overlapping deltas at once end with the same state as sequential
     ingest (test with `multiprocessing` or subprocesses);
   - survives restart (reopen the DB);
   - works without CodeGraph and offline (no network, no CodeGraph import);
   - secrets: evidence/paths to `.env*`, `*.pem`, `*.key`, `id_rsa*`, `credentials*`, `secrets*` are rejected, and
     any field matching common secret shapes (e.g. `AKIA…`, `ghp_…`, `sk-…`, `-----BEGIN … PRIVATE KEY`, `xox[bp]-`)
     rejects the whole delta without echoing the value;
   - queries filtered by project, commit and area (path prefix and/or entity prefix); `inferred`/`unknown`/
     `unverified` are labelled so a consumer (Planner) can exclude them as facts.
4. **Exports** (generated views, never the source of truth): `md`, `mermaid`, `json`.
5. **CLI**: `bitacora.py [--project P] knowledge ingest <delta.json|-> [--repo-path PATH] [--json]`,
   `knowledge query [--commit SHA] [--area X] [--status ...] [--json]`, `knowledge export --format md|mermaid|json`,
   `knowledge stats`. Exit 0 ok, 2 invalid input. Explorer never calls this; the executor/lead does.
6. **Benchmark helper + test** (§10.9 last bullet): replay N synthetic overlapping deltas (e.g. 3 Explorers × 40
   observations, 50% overlap, one changed commit, one contradiction) and report correct relations, duplicates
   avoided, stale labelled, bytes of `query --json` vs raw deltas, and time. The test asserts no duplicate relation
   and output smaller than the concatenated raw deltas; print the numbers in the test output for the lead.

Leave room for a separate *external research* store (another task, later): do not create its tables, but keep the
SQLite helpers reusable (e.g. `store.py`) and the CLI dispatch extensible.

## Verify
- `cd skill/scripts && python -m unittest discover -s bt_knowledge/tests` → 0
- `python skill/scripts/bitacora.py --project <tmp> knowledge --help` (and an end-to-end ingest/query in a temp
  bitácora root if the CLI supports an override such as an env var used by other tests; find how tests isolate it)
- full suite per RULES.md.
