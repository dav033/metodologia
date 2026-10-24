# `bt_knowledge` — revision-bound project knowledge

This deterministic package validates Explorer deltas, preserves evidence and conflicts in SQLite, and produces filtered
queries and generated views. It does not call an agent, CodeGraph or a network service. The database is the source of
truth; Markdown, Mermaid and JSON are generated projections.

## Boundaries

- Package code imports only the Python standard library and this package. It accepts a database path and optional
  repository path; it does not resolve a user, project directory or environment variable.
- Git verification is limited to argument-list `git cat-file`, `git show` and `git diff --quiet` calls, each with a
  10-second timeout. There is no shell invocation or network access.
- SQLite writes use WAL, a 30-second busy timeout and `BEGIN IMMEDIATE`. The package writes only its database and
  SQLite-managed WAL/SHM files next to it.
- Run its tests from any directory with `python -m unittest discover -s bt_knowledge/tests`; run its standalone CLI
  with `python -m bt_knowledge --db <path> ...`.

## Contract: `knowledge-delta/1`

Top-level required fields are `schema`, `project`, `repository`, `observed_commit`, `contributor` and `observations`.
The schema literal is `knowledge-delta/1`; commit is a full lowercase 40-hex SHA. Optional arrays `contradictions` and
`stale` default to empty. Entity ids use the closed `kind:name` vocabulary from the task contract, and names contain no
whitespace. Relations are exactly `IMPORTS`, `CALLS`, `IMPLEMENTS`, `PUBLISHES`, `CONSUMES`, `PRODUCES`, `CONFIGURES`,
`TESTS`, `DEPENDS_ON`, `DEFINES`, `EXPOSES`, `CONTAINS`, `OWNS` and `REFERENCES`. Observation statuses are
`observed`, `inferred`, `proposed` and `unknown`; `disputed` is derived from recorded conflicts.

An evidence reference is a safe relative `path`, `path:line[-line]`, `symbol:<id>` or `test:<id>`. Absolute paths,
parent traversal and sensitive paths (`.env*`, `*.pem`, `*.key`, `id_rsa*`, `credentials*`, `secrets*`) are rejected.
The entire delta is rejected if any value matches a supported secret shape; errors never echo the value.

`content_fingerprint` is SHA-256 over canonical JSON containing the relation identity `(project, repository, subject,
relation, object)`, evidence reference and observed commit. A logical relation is unique within project/repository.
Repeated evidence at the same commit is deduplicated; additional contributors are retained on that evidence record.
An explicit contradiction is retained in `conflicts`, marks its relation disputed, and marks any same-subject,
same-relation alternative object disputed as well. Nothing is resolved by majority. Stale marks and all state changes
are appended to `history`. Exact retries make no state or history change.

With a repository path, file evidence is checked with Git at the observed commit and an optional line range is checked
against that blob's line count. Missing repository access, symbols/tests, absent files or invalid lines are recorded as
`unverified`; without a repository path every item is `unverified`. A commit-filtered query labels matching evidence
`current`, older evidence `historical`, or older evidence `unchanged_since:<observed-commit>` only when Git confirms the
file did not change. A stale mark is retained independently. `inferred`, `unknown`, `unverified`, `historical`,
`disputed` and `stale` labels are explicit so consumers can exclude them from facts. `validity` and `status` stay
separate: a relation can be both `current` and `disputed`.

## Public API

- `ingest(db_path, delta, repo_path=None)` → counts: `added`, `relations_added`, `evidence_added`,
  `conflicts_added`, `stale_marked`, `duplicates_avoided`.
- `query(db_path, project, *, commit=None, area=None, status=None, repository=None, repo_path=None)` → relation rows
  with evidence provenance and validity. Relation rows expose `subject`, `relation`, `object`, `validity`, optional
  `disputed`, and evidence items expose `ref`, `commit`, `contributors`, `status`, `verification`, `validity`, and
  optional stale metadata. The compact field names keep machine-readable views bounded. `area` matches a relative
  evidence-path prefix or entity-id prefix.
- `stats(db_path, project)` → relation/evidence/conflict/stale/history counts.
- `export(db_path, project, fmt, *, commit=None)` → generated `md`, `mermaid` or `json` text. Markdown includes each
  evidence item's observation, verification and validity labels.
- `benchmark(db_path, *, explorers=3, observations=40)` → synthetic overlap metrics and serialized byte sizes.
- `KnowledgeError` carries a stable `code`; invalid CLI input exits 2.

Stable validation codes: `INVALID_DELTA`, `INVALID_ENTITY`, `INVALID_RELATION`, `INVALID_STATUS`, `INVALID_COMMIT`,
`INVALID_EVIDENCE`, `UNSAFE_PATH`, `SENSITIVE_PATH`, `SECRET_SHAPE`, `INVALID_FORMAT`.
