# `bt_scheduler_quality` — M6 Quality & Integration

An isolated verifier for one M1 `VerifyOrder` and its matching M3 handoff. It checks the approved plan's exact
commands against a disposable copy of the preserved snapshot, writes a durable evidence manifest, and returns an
internal result. It does not own task state, retries, worktree allocation, plan approval, or predecessor merging.

The package imports only itself and Python's standard library. The adapter
`skill/scripts/bt_scheduler_quality_adapter.py` translates M1/M3 contracts into the package API and submits M1
verdicts through the unchanged M1 contract. It reaches those public types through `bt_scheduler_adapter` and
`bt_scheduler_executor_adapter`; it does not import either implementation package directly.

The supported Scheduler owner runtime (`scheduler-run` and `launch --scheduler`) always supplies a distinct durable M6
store before attempts can dispatch; it does not fall back to a custom verifier. The lower-level
`bt_scheduler_executor_wiring.wire(..., quality_store_path=...)` seam remains opt-in for isolated tests and explicit
custom compositions. The path must name a durable file in a private directory and must be separate from M1, M4 and M5
stores. Omitting it preserves that caller's existing `VerificationPort`; supplying both it and a custom verifier is
rejected before the runtime opens. An optional `quality_policy` mapping configures the local checker policy. M6 drains
its verification queue and closes its worker and store before M3 shuts down.

## Contract v1

Input is the JSON-compatible `VerifyOrder` already created by M1:

```json
{
  "idempotency_key": "verify:T-001:att-001",
  "plan_id": "PLAN-TEST",
  "revision": 1,
  "task_id": "T-001",
  "attempt_id": "att-001",
  "token": 1,
  "acceptance_criteria": ["unit tests pass"],
  "verification": [
    {"type": "command", "value": "python3 -m unittest -q", "purpose": "unit tests pass"}
  ]
}
```

M6 also accepts these optional additive order fields: `contract_identities` maps contract identity names to lowercase
SHA-256 values; `environment_fingerprint` is a lowercase SHA-256 supplied by the order and is combined with M6's local
environment fingerprint; `composition_id` and `manifest_sha256` must appear together. They are included in evidence
and cache binding only when present, leaving legacy request hashes and cache keys unchanged.

verification accepts the approved Planner v1 shape: type=command|manual, value, purpose, optional created_by, and for
manual, expected. It also accepts an optional 1.2.0 category (static, functional, integration, regression or product).
M1 requires and validates the category when loading a 1.2.0 plan; M6 validates and preserves it as typed evidence
metadata. When absent, M6 omits it from serialization and the request hash, preserving legacy hashes. The command
value is parsed to argv without shell=True; the only
compound syntax supported is a leading `cd <relative-path> && <argv>`. Shell operators, substitutions, absolute
working directories and paths escaping the snapshot are rejected. Each command's `purpose` must exactly equal an
acceptance criterion string to cover it. A manual item or uncovered/ambiguous criterion is `unknown` and cannot
PASS. This conservative rule avoids changing the shared M1/Planner contract.

For schema 1.3.0, M6 additionally validates and preserves `environment`, name-only `requires`, and optional
`authorization_needed`. Absent fields stay absent in the serialized order and its hash. `requires` accepts only
environment variable names or `service:<slug>`; raw maps and values are rejected. Environment variables are checked
against the trusted M6 operator environment by name, while services are checked through
`VerificationAuthority.resource_available(name)`. A missing resource returns `BLOCKED_EXTERNAL` before command launch.
`external_authorized` and `production` also require an explicit true result from
`VerificationAuthority.authorize_environment(environment, authorization_needed)`; a plan's classification string
never grants permission. Missing or failing ports block without running commands. `human_attestation` remains manual
and is settled only by the existing attestation receipt port. The 1.3 capability is M6-local: the overall Planner
gate remains closed until M1, M2, M3 and M6 all declare and prove their exact consumer support.

Every non-sandbox policy entry must include an `authorization` field matching the requested authorization text. An
entry that matches the environment and requirement but omits that field is denied with
`POLICY_ENTRY_MISSING_AUTHORIZATION`. In `secrets.env`, `NAME=""` and `NAME=''` are treated as unavailable resources.

The M3 adapter supplies trusted repository and artifact paths plus the captured handoff identity:

```json
{
  "attempt_id": "att-001",
  "repository": "/trusted/project/repository",
  "base_sha": "<git commit>",
  "snapshot_sha": "<git commit>",
  "manifest_path": "/trusted/m3/attempts/att-001/handoff/manifest.json"
}
```

The package validates this data against M3's handoff manifest, confirms the base commit is an ancestor of the
snapshot, and archives the snapshot into an owned temporary directory. The source repository, worktree and M3
artifact are read-only inputs. `PredecessorIntegrator` remains the only merge/conflict implementation; M3 records
the base it used before execution.

Result schema is `m6.verify-result/1.1`; PASS, FAIL, NEEDS_REVIEW and STALE are internal statuses. Version 1.1 adds a
per-check/result `reason_code` taxonomy and tree plus optional contract, environment and composition bindings. Stored
version 1 results remain readable; a missing classification reads as `UNCLASSIFIED`. The full shape and
illustrative examples live in `api-contract.json` and `tests/fixtures/`. Each check carries its own stable `issue_code`
so aggregate metrics distinguish checks that were not run from checks that returned unknown for another reason.
Mapping to M1 is deliberately binary:

| Internal status | M1 behavior |
|---|---|
| PASS | Submit current correlated `Verdict(accepted=True, evidence="m6://...")` |
| FAIL | Submit current correlated `Verdict(accepted=False, evidence="m6://...")` |
| NEEDS_REVIEW | Persist a review item and M1 hold; send no verdict; M5 may resume the same verification once, wait, or block |
| STALE | Record stale identity; send no verdict for a replacement attempt |

An M1 Ack acknowledges only durable request admission. A check's exit 0 does not become PASS unless every criterion
is covered and all provenance/integration guards pass. A completed nonzero command is FAIL; a timeout, absent
dependency, missing evidence or unavailable sandbox is NEEDS_REVIEW. M1 rejection/error remains in the M6 outbox
until reconciled or is marked stale with the actual M1 response.

## Proportional verification (REQ-030)

- **Pass cache** (`reuse.py`, `QualityPolicy.cache_seconds`, default one day): a check that passed on this exact git tree
  with the same command and the same operator environment is not run again; its recorded output is returned with a note.
  Failures are never reused. The existing `check_pass_cache` table also retains fail/flaky status for the same evidence key;
  a later pass is classified `FLAKY_SUSPECTED` and is not cached. **Expensive checks last** (`defer_expensive`, `expensive_check_seconds`): a check that took
  that long the last time, or that looks like a whole suite (`unittest discover -s tests`, `npm run gate`), runs after the
  cheaper ones and is skipped (`CHECK_DEFERRED`) once one of them failed: the verdict is FAIL either way.
- **Mixed evidence** (`mixed_evidence`, default on): a criterion may be backed by several checks with its exact text as
  purpose; it passes when every command passes and every `manual` check carries an attestation receipt. The engine
  learns about receipts through the `attestations(order, spec)` port; `bt_attestation` mints them (`scheduler-op REQ
  attest TASK`, HMAC-sealed, bound to task + purpose + value + expected) and the receipt digests go into the evidence
  manifest. `QualityStore.retry_attested` requeues an open review that only waited for manual evidence, once.

## Process isolation

Command checks run in bubblewrap with unshared mount, network, PID, IPC and UTS namespaces, all capabilities dropped,
a read-only `/usr`, a writable bounded `/workspace` tmpfs populated from the archived snapshot, a separate bounded
`/tmp`, `/proc` and `/dev`, and no host home or network. The verifier checks bubblewrap's namespace IDs before it
releases a startup gate; a failed setup never starts the check. The child gets a clean environment plus only
operator-configured entries. Loader, Python and Git configuration variables cannot be overridden. Values with
secret-like environment names require explicit registration for output redaction; a configured secret cannot be
embedded in a plan command. Wall time, CPU/address-space/file-size, process count, output bytes, tmpfs sizes and
per-runner concurrency are bounded. A Git worktree alone is never treated as a sandbox.

Runner outcomes are `pass` (exit 0), `fail` (a started command exits nonzero), or `unknown`. Stable unknown issue
codes include `SANDBOX_UNAVAILABLE`, `CHECK_UNAVAILABLE`, `CHECK_TIMEOUT`, `OUTPUT_LIMIT`, `CHECK_MANUAL`,
`CHECK_UNSUPPORTED`, `SNAPSHOT_INVALID`, and `RUNNER_BUSY`. A missing binary, denied namespace, failed workspace
copy or failed `exec` never becomes a test failure or pass. Output is capped across both streams and exact registered
secret values are replaced with `[REDACTED]` before the outcome is returned.

Deployment, publishing, release and migration commands are classified as operator review and are not launched. Offline
checks such as `check_migrations.py` remain eligible when they inspect the snapshot without performing those actions.
The legacy undeclared policy remains unchanged. The owner wires trusted callbacks into
`QualityVerificationPort(verification_authority=...)`: resource names are checked against the owner process
environment and `~/.config/flow/secrets.env` without persisting values; `sandbox` is allowed without an operator
policy; `staging` and `production` require a matching entry in `<bitacora root>/<project>/verification-policy.json`.
Missing, unreadable or unmatched policy denies before command launch. Authorization is never derived from PLAN.json,
task text or an agent-supplied environment map.

Artifacts are local, mode `0700` directories and mode `0600` files in a separate M6 store. The SQLite WAL ledger and
verdict outbox are private to M6; neither M1 nor M3 stores are opened for writing by the package. A durable
NEEDS_REVIEW item is handed to M5 with its content-addressed evidence reference. M5 may ask M6 to resume the same
verification attempt once for timeout/flaky evidence, wait for a blocker to clear, or block the task. A resumed flaky
result is never accepted from its earlier single pass. Other unresolved review items still require explicit operator
resolution with identity and rationale; M1 never spends an implementation retry for review handling. The identity
entered by the local operator is audit metadata, not cryptographic proof of a human account.

After repairing an engine crash, an operator may explicitly call
`QualityStore.retry_interrupted(request_key, operator, reason)` while the scheduler owner is stopped. This
accepts only an open review whose sole cause is `ENGINE_INTERRUPTED`, once per request. The prior result and
operator rationale remain in `verification_retries`; no verdict is emitted. On restart normal dispatch rechecks
snapshot provenance and command policy and runs the checks in the sandbox. Other unknown outcomes and resolved
reviews cannot use this recovery path. Queued work that never started remains queued during startup recovery.
Permission refresh never opens or closes SQLite-managed database/WAL/shared-memory files: closing another fd for
those inodes releases SQLite's process-scoped POSIX locks and can corrupt concurrent-reader coordination.


M6 metrics keep `not_run`, `unknown` and `unmeasured` separate; `defect_count` remains `null` until it is measured.
The existing `bt_quality` ledger records findings and rework attributed to accepted milestone audits. A failed
verification command is not an audit finding, so M6 does not write command outcomes into that ledger or count them
as defects.

No provider calls, paid tests, live deployment, production database or migration are part of M6 verification.

## Pass cache and a task's own reports
The cache key is the snapshot's git tree + the command + the operator environment. For a task of kind `test` or `audit`, the report files it declares in `expected_paths` (`.md .json .txt .log .csv .html`, no globs) are left out of the tree of every check that does not name them (`reuse.own_outputs`, `reuse.tree_id(..., ignore)`; a temporary index, nothing in the repository changes), so a retry that only rewrote its report reuses the passes of the earlier attempt. `QualityPolicy.cache_ignores_outputs` / `verifier.cache_ignores_outputs` (default on); if git cannot tell, the whole tree is the key.
