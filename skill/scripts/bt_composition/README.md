# `bt_composition`

Isolated, standard-library-only engine for immutable accepted subplan versions, disposable composition candidates,
and selective downstream work. It treats Git as text integration evidence; only contract checks and audits establish
compatibility.

## Public API

- `GitPort`: object-only Git operations and temporary candidate worktrees. Implemented outside this package.
- `Store(path)`: one caller-selected SQLite WAL database for one run. Call `close()` when the run ends.
- `CompositionEngine(git, store, workspace_root)`:
  - `publish_subplan_version(plan_id, plan_revision, subplan_id, commit, line_base, contracts, evidence)` allocates
    `SP@vN`, creates `refs/subplans/<plan>/<SP>/v<N>` with create-only CAS, and returns a manifest-bound version.
  - `build_candidate(plan_id, members, *, run_base=None, required_verdicts=("M6",), member_order=None)` folds changed
    member deltas in the supplied plan order (or mapping insertion order) and creates
    `refs/compositions/<plan>/candidates/C<N>`. A repeated identical live request reuses the same candidate; requesting
    the already-current member set returns that published composition. Text conflicts produce a `rejected` candidate
    with `reason_code="git_text_conflict"` and per-member conflict paths. A rejection permits a fresh candidate number.
  - `open_workspace(candidate_id)` and `close_workspace(path)` create and remove a temporary worktree under the
    caller-provided workspace root; opening moves the candidate to `verifying`. `prune_workspaces()` removes registered
    candidate worktrees left by a crash under that root.
  - `publish(candidate_id, verdicts)` atomically creates `refs/compositions/<plan>/C<N>` and moves `current` only
    when all candidate-required verdicts are `PASS`. It returns `False` and rejects the candidate otherwise.
  - `reject(candidate_id, evidence)` records a rejected candidate. Published compositions cannot be rejected.
- `EvidenceKey(tree_digest, contracts, environment, paths=())` and `reusable(old, new)` bind evidence to equal tree
  digests, contract hashes, environments and sorted relevant-path sets. The real Git port refuses an empty path list
  and names missing paths.
- `propagate(change, consumers, evidence)` returns `Action(consumer, operation, reason)` records. Operations are
  `reverify`, `reintegrate`, `audit`, `adapt_contract`, `modify`, and `reimplement`; reimplementation requires an
  explicit demonstrated finding that the consumer design cannot meet the contract.

`PropagationChange` identifies `producer` and may set `ancestry_only`, `contract_major_changed`,
`public_surface_changed`, `git_conflict`, `conflicting_members`, or `producer_broke_declared_major`. Consumer mappings
provide `id`, optional `contract_test_executed` / `contract_test_failed`, matching producer version and manifest fields,
and `old_evidence_key` / `new_evidence_key`. A Git conflict triggers `reintegrate` only for a consumer with conflict
paths. Finding mappings use
`demonstrated: true`, the matching `consumer`, and `design_cannot_meet_contract: true` to authorize `reimplement`.
An `ancestry_only` change always yields at most `reverify`, even if contradictory evidence is supplied.

## States and refs

Composition states are `candidate`, `verifying`, `published`, and `rejected`. A textual conflict is rejected during construction.
Candidate refs and immutable subplan refs are created with zero-old-value CAS. Publishing uses one atomic refs
transaction to create the numbered published ref and compare-and-swap `current` from the candidate's recorded base.
Candidate worktrees are temporary; durable identity is the object/ref, version and manifest, not its directory.

## Stable errors

Input and stored-fact errors are `INVALID_IDENTIFIER`, `INVALID_VERSION_INPUT`, `INVALID_VERSION_COMMIT`, `INVALID_CONTRACT_HASHES`,
`INVALID_VERSION_EVIDENCE`,
`INVALID_MEMBERS`, `REQUIRED_VERDICTS_MISSING`, `SUBPLAN_VERSION_MISSING`, `COMPOSITION_BASE_MISSING`,
`SUBPLAN_VERSION_CONFLICT`, `CANDIDATE_MISSING`, `CANDIDATE_NOT_OPENABLE`, `CONSUMER_ID_MISSING`,
`PUBLISHED_COMPOSITION_IMMUTABLE`, `COMPOSITION_CANDIDATE_CONFLICT`, `EMPTY_RELEVANT_PATHS`, `TREE_PATHS_MISSING`,
and `INVALID_RELEVANT_PATH`. Ref validation errors use `INVALID_REF_OID`; merge failures use `GIT_MERGE_TREE_FAILED`; textual
conflicts use `git_text_conflict`. Ref failures are surfaced by the `GitPort` implementation; the adapter reports Git
command/CAS failures without claiming success. `current` movement is reported as `COMPOSITION_CURRENT_MOVED` and a
missing parent as `COMPOSITION_PARENT_MISSING`. CLI validation uses `INVALID_MANIFEST`.

## CLI

`python -m bt_composition --help` describes the offline `manifest-sha256 <file.json>` command. It prints the SHA-256
of canonical JSON and does not read Git state or write files.

## Boundaries

Production package code imports only the standard library and this package. It does not inspect environment variables,
run subprocesses, or know methodology paths. `bt_composition_adapter.py` is the only methodology importer and owns the
real Git subprocess port. The module's tests and caller-supplied worktree paths are outside the shipped package API.
