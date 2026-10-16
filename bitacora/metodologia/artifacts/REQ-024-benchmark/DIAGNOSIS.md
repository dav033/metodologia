# REQ-024 evidence diagnosis

Captured for T2 after the owner approved plan r1. This classifies evidence; it does not grade product decisions or treat later edits as model output.

## Evidence classes

| Evidence class | Source | What it supports | Limits |
|---|---|---|---|
| Executable implementation | `skill/agents/planner.md`, four private skills, `skill/scripts/bt_planner/`, `bt_plan_adapter.py`, M1/M2/M4/M6 consumers | Claims about current code, contracts, hooks, installers and checks when verified against source | Source presence does not prove model behavior or product acceptance. T1 snapshots this current state. |
| Configured instructions | Shared Planner role and private skills in the T1 snapshot; installed profiles under local Claude, Codex and Antigravity directories | What current Planner sessions are instructed to do and where the role is available | Installed profile files are generated copies; source remains canonical. Current profile inventory is a point-in-time snapshot. |
| Observed model output, retrospective V1 | `~/.state/delegations/D-20261016-090752-bc5d/RESULT.json` evidence field; raw plan is 18,134 characters | The exact recovered V1-labelled plan output can be assessed retrospectively | Generic Claude Work/Opus high research delegation; follow-up prompt used pre-digested prior evidence; no repository SHA or runnable V1 Planner profile; session log shows broad `bypassPermissions` tools and injected SessionStart context. Not a controlled V1 Planner run. |
| Observed model output, current V2 | `artifacts/REQ-017-planner-rerun-opus55-high-20261016/{PLAN.md,PLAN.json,RUN.md}` | One read-only Opus 5.5 high Planner-profile rerun; artifact can be revalidated and reviewed | One output only; its later owner approval was limited to the isolated M1/M2 test. It is not Pictures product approval or evidence of implementation. |
| Coordinator/reviewer edits | `bitacora/pictures/requirements/REQ-017-*/PLAN.md`, REQ-024 `SPEC.md`/`PLAN.md`, and V2 `RUN.md` follow-up sections | What was added or corrected after model generation, including assumptions and review findings | Must not be attributed to the model. Pictures live plan is status `done` and contains checked implementation tasks and later revisions. |
| Implementation activity | Pictures REQ-017 report, source history and checked tasks | What was implemented and recorded in the product project | This is downstream project evidence, not raw plan quality and not a clean baseline. REQ-024 does not change it. |
| Deterministic verification | `bt_planner` suite, contract checks, parser/consumer suites | Contract behavior under executable tests and pinned fixtures | Does not establish semantic quality of an arbitrary plan or product-level acceptance. |
| Synthetic benchmark oracles | `bt_planner/tests/scenarios/*`, `EXPECT.json` fixtures for training cases | Deterministic expected behavior for controlled test cases | Synthetic labels are not production outcomes, live quota, model quality, or measured rework. |
| Owner decisions | REQ-024 approved plan r1, D-054/D-055/D-059, Pictures round-01 | Scope, approval and benchmark caps | Product choices q1–q5/A6–A8 remain unanswered; this benchmark cannot decide them. |

## Provenance fingerprints

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `/home/david/bitacora/.state/delegations/D-20261016-090752-bc5d/RESULT.json` | 20052 | `16e636c7cf41002346c8252392683ff10b505e335981b3437a98d14882a7fef2` |
| `/home/david/bitacora/.state/delegations/D-20261016-090752-bc5d/prompt.txt` | 2497 | `817268c1b19530ec605ef1dad937bb41d7996261d195d72754a950ad1664bc11` |
| `/home/david/bitacora/.state/delegations/D-20261016-090752-bc5d/session.log` | 316767 | `415b6b6d42cea40ca2249a8be496b0ddf1c88c2eb527f053f1a1f6ee815793be` |
| `bitacora/metodologia/artifacts/REQ-017-planner-rerun-opus55-high-20261016/PLAN.md` | 7329 | `78af6ea550fedaff732831f36beb82793bd0ce310999dbcaea69886fb23eda8a` |
| `bitacora/metodologia/artifacts/REQ-017-planner-rerun-opus55-high-20261016/PLAN.json` | 24541 | `724e90831fb356800d0fc122cd9468b85abd3e6376fb2c8ba0ace6639983210e` |
| `bitacora/metodologia/artifacts/REQ-017-planner-rerun-opus55-high-20261016/RUN.md` | 8096 | `de34a9a0ce5d7f2fe6cff52320e8b96738b11bc6f5e263b4785982c96d3b1ce6` |
| `bitacora/pictures/requirements/REQ-017-activity-aware-guided-chat-decoration-re/PLAN.md` | 15842 | `298c0d2793371f424141aec348bdd59ea42b25fd4065110e7a3d82656e5bc6d9` |
| `bitacora/pictures/requirements/REQ-017-activity-aware-guided-chat-decoration-re/SPEC.md` | 6022 | `0cf8fc835a71641004cf0e49cdf3b499fb1e1ab123fc46b089676369c1248b8c` |
| `bitacora/pictures/requirements/REQ-017-activity-aware-guided-chat-decoration-re/rounds/round-01.json` | 3938 | `b45cfb778dfc6a0630440136f8227e1b1ef7a8ad027da09725a54be758577bbf` |

## V1 delegation record

```json
{
  "delegation_id": "D-20261016-090752-bc5d",
  "profile": "claude-work",
  "model_label": "opus",
  "effort": "high",
  "kind": "research",
  "worktree_mode": true,
  "repository_sha_recorded": false,
  "result_status": "done",
  "raw_plan_characters": 18134,
  "raw_plan_sha256": "ff6ed54d3158fd8c3360dd7be1f02725a03ae6b8f6a3b59f64468284e5348100"
}
```

The RESULT evidence is retained as a historical artifact. `TASK.json`, `prompt.txt` and `session.log` fingerprints above are provenance identifiers; raw prompt/session content is not copied into this report.

## Benchmark interpretation

- Controlled arms are current V2 at the T1 snapshot versus improved V2 after the approved changes, with matched case bytes, repository state, model, effort, tools, timeout and review opportunity as defined in the plan.
- V1-labelled and later-edited REQ-017 plans remain retrospective evidence. Do not calculate a causal V1-versus-V2 win from them.
- The Opus V2 rerun and the frozen M1/M2 simulation remain distinct artifacts; neither proves execution quality or product acceptance.
- Quality, duration, retries, token usage and consumption stay separate measures. Missing, synthetic, cross-project, unverified or non-comparable evidence remains unknown.
- T1 source snapshot includes Planner instructions changed before approval and the D-055 rollout. That is the declared current V2 baseline; the historical pre-edit profile is not reconstructed.
