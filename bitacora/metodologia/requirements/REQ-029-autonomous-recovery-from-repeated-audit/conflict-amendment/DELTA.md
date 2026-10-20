# Amendment delta and rebase impact

Candidate revision 2; planning only while owner goal is paused. No application, activation, approval or freeze was performed.

## Scope delta

- Preserve R1–R10; add R11–R16 for both conflict entry points, authoritative complete evidence, root-cause precedence, actual convergence bootstrap and both-side proof, one-cycle safety, replay/UI/migration.
- Preserve three milestones and extend from 20 to 24 tasks. New tasks: T3a structural contracts/policy; T3b full evidence/integrator/bootstrap; T4a executable convergence strategy; T6a dedicated real-entrypoint historical conflict replay.
- Existing unaccepted T4/T5 implement general M1 authorization/application and adapter/runtime wiring; T6 packaging/shared harness; T10 UI plus prefix classification; T11 HTTP/receipt checks; T12 policy docs; test/audit/rollout criteria include the structural mode.
- Future dependency shape: T3 -> T3a -> T3b -> T4 -> T4a -> T5 -> T5a -> T6 -> T6a -> T7 -> existing audit/final/rollout chain. No provider, account, model, effort or worker assignment was chosen.
- T3b is sole future quality-adapter writer after historical accepted T2. T2 expected_paths, criteria, verification, objective, evidence and every other task field remain unchanged; the lifecycle extension is documented, not implemented by removing frozen scope.

## Accepted-work preservation and pure rebase preview

Used official read-only M1 SQLite state and pure `bt_scheduler_core.rebase.plan_rebase(state, old, new)`, never `rebase_run` or an operator command. The draft was parsed with its own computed digest solely for structural comparison, not treated as approved.

Full T1–T3 JSON object equality: `{"T1": true, "T2": true, "T3": true}`. Operational fingerprints:

- T1: old and candidate `1c642b9ffaa1e27141c1c010c80aec902278f4d0d42cb0553b5abfdfa073d039`; equal=True.
- T2: old and candidate `c91761e0defb7ab0c8d8e50e87a6f8be32b5d25032929c006321a63b1986f5a6`; equal=True.
- T3: old and candidate `a12c4901d1bea898fb9d132f933ec8793c8b61f203617bba76e856f6095782cc`; equal=True.

Actual pure report:

```json
{
  "from_revision": 1,
  "to_revision": 2,
  "kept": [
    "T1",
    "T2",
    "T3"
  ],
  "reset": [
    "T4",
    "T5",
    "T5a",
    "T6",
    "T7",
    "T8",
    "T9",
    "T10",
    "T11",
    "T12",
    "T13",
    "T14",
    "T15",
    "T16",
    "T17",
    "T18",
    "T19"
  ],
  "added": [
    "T3a",
    "T3b",
    "T4a",
    "T6a"
  ],
  "removed": []
}
```

The three accepted tasks remain kept. All other original tasks were unaccepted and would reset/replan; four tasks are added and none removed. T4 att-0004 is not an accepted implementation; its preserved worktree may inform a fresh task but does not satisfy r2. Preserve `/home/david/bitacora/.state/executor/metodologia-REQ-029-r1-64d87fff-1792528582644/ws/worktrees/att-0004-6c689221dc39750a`.

Existing ordinary `rebase_run` resets budget_base/waits/reworks for reset tasks; this preview does not endorse invoking that path for automatic structural recovery. T4 must implement validated counter-preserving M1 authority before the new runtime applies automatic target-plan revisions. Applying this development-plan amendment itself remains an owner/workflow operation after the pause ends; this report neither runs it nor resets its counters.

## Verified immutable source identities

- Accepted REQ029 r1 plan SHA-256: `64d87ffffa199c2240e52026d51885f7aca88dfcb10d95b77c00ea834efb3e8b`. T4 official order base: `0310c7dc4a78b2589fa5044476470342dd8b583d`. T1–T3 accepted contracts were inspected there using `git show`, never inferred from unfinished T4 files.
- Official REQ027 M1 store: `/home/david/bitacora/.state/scheduler/metodologia-REQ-027.db`, opened with `mode=ro`. r9 plan hash: `e2d7030f678abcca2c1e3f0cee1cba62f85fd471c1274c6171e7ad26f257510c`.
- Parent forensic evidence: `/home/david/bitacora/metodologia/requirements/REQ-029-autonomous-recovery-from-repeated-audit/CONFLICT-EVIDENCE.json`, SHA-256 `c457011b0700a817a39c8af2b4856da492fd202b3133d9d42c188878e57bda36`. This is inspected source evidence, not a preexisting executable replay test.
- REQ027 T15a:8 = att-0208, token 208, rejected by integration gate after M6; earlier att-0206/0207 carry the same clipped collision. T15b att-0124 start failed with T3 vs T15a and exact recorded four contract/doc paths; its rejected-start record is not a captured accepted handoff.
- Ordinary clash `T6+T7+T15a vs T15b for T15c` selects only T15b for give-way; `gates.max_reworks=2`, T15b reworks=2; exact refusal `limit: T15b was already sent back 2 time(s)`. T6 reworks=3, T7=0, T15a=1; their existence does not authorize resetting any of them.

### att-0130 — T3 (accepted)

- Manifest: `/home/david/dev/metodologia/bitacora/.state/executor/metodologia-REQ-027-r7-17522cd6-1792439172092/attempts/att-0130-7566aace6ede8836/handoff/manifest.json`.
- Manifest SHA-256: `e658e63f1d0ee5ff188c6c8330f13ff46287b170283e904d6864615e4e970829`.
- Original base SHA: `cd42bd381ddbae74aac9b8fabb0870133e612a58`.
- Snapshot SHA: `5f5eb8992add64332e737bbead83ebc36b78dee0`.
- Exact base-to-snapshot changed paths (these are diff paths, not an invented full merge-conflict set):

  - `remote/contract/command.schema.json`
  - `remote/docs/contract.md`
  - `skill/scripts/bt_server.py`
  - `skill/scripts/tests/test_remote_listener.py`

### att-0142 — T15b (accepted)

- Manifest: `/home/david/dev/metodologia/bitacora/.state/executor/metodologia-REQ-027-r7-17522cd6-1792439172092/attempts/att-0142-e3672dbcad582706/handoff/manifest.json`.
- Manifest SHA-256: `6288a3d9e064590c2dc81a62031753466282fb1e12035903d4c5c57d8cbb4aa6`.
- Original base SHA: `f5e5a89a07a162083be78f98413f6e5c2d747593`.
- Snapshot SHA: `9f5ab702d6c0786579e3ac8c87e75857c08f4cb5`.
- Exact base-to-snapshot changed paths (these are diff paths, not an invented full merge-conflict set):

  - `remote/web/mocks/gateway.mjs`
  - `remote/web/src/app/page.tsx`
  - `remote/web/tests/panel-browser.test.mjs`

### att-0204 — T15 (accepted)

- Manifest: `/home/david/dev/metodologia/bitacora/.state/executor/metodologia-REQ-027-r9-e2d7030f-1792439172092/attempts/att-0204-bfc872a4a37a8894/handoff/manifest.json`.
- Manifest SHA-256: `275ebd04b5c0d6dbf2bfd5a1ee1decbee07b3876c82f7cc38332aae496960de0`.
- Original base SHA: `5f5eb8992add64332e737bbead83ebc36b78dee0`.
- Snapshot SHA: `ee9651bd70c4d00752a406be434d107634ef0e67`.
- Exact base-to-snapshot changed paths (these are diff paths, not an invented full merge-conflict set):

  - `remote/web/.env.example`
  - `remote/web/.gitignore`
  - `remote/web/README.md`
  - `remote/web/eslint.config.mjs`
  - `remote/web/mocks/fixtures/snapshot.json`
  - `remote/web/mocks/gateway.mjs`
  - `remote/web/next-env.d.ts`
  - `remote/web/next.config.ts`
  - `remote/web/package-lock.json`
  - `remote/web/package.json`
  - `remote/web/postcss.config.mjs`
  - `remote/web/public/apple-icon.svg`
  - `remote/web/public/fonts/JetBrainsMono-400-latin.woff2`
  - `remote/web/public/fonts/Manrope-400-latin.woff2`
  - `remote/web/public/icon.svg`
  - `remote/web/public/manifest.webmanifest`
  - `remote/web/src/app/globals.css`
  - `remote/web/src/app/layout.tsx`
  - `remote/web/src/app/page.tsx`
  - `remote/web/tests/mock-gateway.test.mjs`
  - `remote/web/tests/scaffold.test.mjs`
  - `remote/web/tsconfig.json`

### att-0208 — T15a (rejected)

- Manifest: `/home/david/dev/metodologia/bitacora/.state/executor/metodologia-REQ-027-r9-e2d7030f-1792439172092/attempts/att-0208-911a6344be4e13b3/handoff/manifest.json`.
- Manifest SHA-256: `bd23bcccf87d08c8bec86cbf2ef89d73bb16a9469053fdcebcc5a25792ee592b`.
- Original base SHA: `2042712ff0a27bacca9a644c9855f61da268b47e`.
- Snapshot SHA: `4b65b6ed88bdfdafe5ec4ff6a0cd6f70083a44c2`.
- Exact base-to-snapshot changed paths (these are diff paths, not an invented full merge-conflict set):

  - `remote/web/tests/login-runs-browser.test.mjs`

## Causal limits and remaining assumptions

The current T15 snapshot is not an ancestor of old T15b base (git merge-base --is-ancestor exit 1 recorded in the forensic evidence). T15b/T15/T15a latest exact diffs have 3/22/1 paths respectively, all remote/web; there is no demonstrated scope escape in those three deltas. Historical T3 includes backend changes, so any scope judgment must compare that attempt against its actual original frozen authority, not current scopes. Existing ordered overlap alone never permits an ownership rewrite.

Full historical collision paths were lost before persistence by the six-path/170-character clipping. The inspected forensic file explicitly does not claim full merge reconstruction. The proposed runtime/replay must derive them from the exact source objects in a disposable repository and retain full provenance; failure to reproduce means evidence_incomplete, not guessed paths or a false structural conclusion.

Independent review and deterministic validation are recorded in REVIEW.md. No planned production/integration test was executed and no real REQ027 convergence is claimed. Current owner pause remains controlling even though the inspected core state paused boolean is false: operational hold and goal pause are separate authorities.
