---
req: REQ-024
type: contract-change-record
date: 2026-10-16
status: confirmed-for-implementation
---
# PLAN.json contract 1.2.0 change record

## Decision

Proceed with the approved additive PLAN.json 1.2.0 proposal. New semantics are gated by `schema_version >= 1.2.0`; 1.0.0 and 1.1.0 retain their validation results, field behavior and frozen canonical bytes. The 1.2.0 canonical bytes are a new hash namespace and are not required to match the old reader's output.

This is safe only as a coordinated migration. The current Scheduler/M6 consumers are **not yet safe for 1.2.0**: M1 accepts major 1 but drops `kind` from task metadata, M2 therefore infers kind from the title, and M6 rejects verification `category`. Do not approve, hand off, launch or resume a 1.2.0 plan through these readers until T11 updates them and proves an explicit compatibility gate. The approved T6–T11 work supplies that migration; this record does not claim it is already implemented.

## Contract additions

| Field | Location and rule for 1.2.0 | Compatibility purpose |
|---|---|---|
| `requirements` | Top-level unique requirement IDs; must match the IDs under the referenced SPEC's `Requirements` heading, or warn when the heading is absent. | Lets the Planner compute requirement coverage instead of relying on prose. |
| `covers` | Each task declares one or more IDs from `requirements`; unknown IDs and uncovered work are errors. | Links scoped tasks to requirements. |
| `kind` | Each task may declare a value in the existing M2 vocabulary: `implement`, `test`, `docs`, `audit`, `research`. Required and validated for 1.2.0. | Passes declared work kind to M2; it does not select a model, provider or specialist capability. |
| `interfaces` | Optional top-level declarations for producer, consumer, inputs, outputs, invariants and integration criteria, with dependency proof. | Makes cross-task contracts and integration ownership checkable. |
| `category` | Each 1.2.0 verification item declares `static`, `functional`, `integration`, `regression` or `product`, separately from its execution `type`. | Distinguishes what a check demonstrates from how it runs. M6 stores it as evidence metadata and does not change verdict policy. |

The full shape and validation rules remain in `PLAN.md`'s Contract 1.2.0 proposal. No provider/model/account assignment, concurrency claim, execution permission or run state is added to PLAN.json.

## Consumer compatibility matrix

| Consumer from `CONSUMER_AUDIT.md` | Current behavior observed during T3/T5 | Required 1.2.0 behavior and rollout gate |
|---|---|---|
| `bt_planner` contract, check, report, init and compat | Current reader supports major 1 and does not implement the proposed 1.2.0 semantic checks. It deep-sorts nested data from 1.1.0 onward. | T6–T10 add 1.2.0-only validation/reporting and compatibility capability reporting. Keep 1.0.0/1.1.0 results and the T4 golden bytes unchanged. Do not emit 1.2.0 from `init` before the installed downstream capability check succeeds. |
| `bt_plan_adapter.py` and launch/handoff/resume callers | Sole supported `bt_planner` boundary; checks the frozen plan and binds its exact SHA-256. | Preserve this boundary and frozen-hash checks. T11 must reject 1.2.0 at approval/handoff/launch/resume when M1, M2 or M6 lacks the required capability; unknown capability fails closed. |
| M1 `bt_scheduler_core/plan.py` | Accepts any `1.x.y`; its `OPAQUE_KEYS` currently omits `kind`. A direct T5 load of the 1.2.0 golden input accepted two tasks but forwarded no `kind`. | T11 forwards the validated `kind` to M2 as opaque metadata and refuses 1.2.0 when the consumer capability is absent. M1 continues to own run state, authorization and task ordering. |
| M2 `bt_scheduler_decision_adapter.task_facts` | Calls `infer_kind(title)`; it cannot currently use a kind that M1 drops. | T11 uses validated explicit kind for 1.2.0 and retains title inference only for 1.0.0/1.1.0. M2 keeps ownership of route policy, tier and quota. |
| M6 `VerifyRequest` / `VerificationSpec` and `input_hash` | Verification objects have strict allowlists; a direct T5 request with `category` returns `ORDER_INVALID`. Typed serialization omits unknown metadata, so category is not hashed today. | T11 validates and preserves category in the typed request and its hash. For legacy orders, omit the absent field during serialization so existing hashes remain stable. Command execution and PASS/NEEDS_REVIEW policy stay unchanged. |
| Planner Markdown sync/report and Scheduler PLAN.md parser | Existing task-line grammar is stable; `covers:` is tolerated as metadata but is not checked against PLAN.json. | T10 adds new report/contract surfaces without changing legacy task-line interpretation. Keep parser parity tests green. |
| `bt_launch`, `bt_runstate`, frozen plan revisions | Launch is bound to an approved plan hash; run state stores plan identity/revision. Existing 1.0.0/1.1.0 revisions are immutable. | Old revisions remain byte-identical. A 1.2.0 revision gets a new SHA and can run only with the matching updated consumer set. Rollback selects a compatible approved 1.1.0 revision and matching M1/M2/M6 readers; never rewrite a frozen hash. |
| Planning history, M4 telemetry and provider profile/install paths | Read-only, exact-context inputs; none owns PLAN.json semantics or Planner quality judgement. | No contract change. Keep route selection in M2 and use `unknown` for insufficient planning-history evidence. |
| Other registered application repositories / review UI | T5 source search found no direct `PLAN.json` or `bt_planner` code consumer in Pictures, Maros, LOTM or Training App. No direct review-UI PLAN.json reader was found in the methodology source. | No additional migration target is identified. Re-run the targeted source search if another consumer is added before T11 closes. |

## Migration and rollback

1. T6–T10 implement and test Planner 1.2.0 validation, schema/example/report/docs, while T4 protects current canonical bytes.
2. T11 updates M1/M2/M6 and adds an explicit downstream capability check. The check covers plan approval, handoff, launch and resume; it must fail closed for an older or unknown consumer set.
3. Continue accepting existing 1.0.0/1.1.0 plans throughout. Do not create or freeze a 1.2.0 approved revision until the Planner and all required Scheduler/M6 capabilities are present and the compatibility tests pass.
4. Roll back by selecting an already approved compatible 1.1.0 revision and its matching consumer set. Never feed a 1.2.0 plan to old M2/M6 readers. Down-conversion is explicit and permitted only when legacy title inference matches the declared kind and dropped categories are recorded; otherwise stop.

## T5 evidence and disposition

- T3's actual audit artifact is `../../artifacts/REQ-024-benchmark/CONSUMER_AUDIT.md`; the approved plan's manual check called it `CONSUMERS.md`. T5 compared this record against the existing audit rather than creating a duplicate inventory.
- `cd skill/scripts && python3 -m unittest discover -s bt_scheduler_core/tests -p test_plan.py` — exit 0; 23 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-plan-loader.log`.
- T5 direct compatibility probes confirmed that current M1 accepts a proposed 1.2.0 input while dropping `kind`, and current M6 rejects `category` with `ORDER_INVALID`. These are reported migration requirements, not passing compatibility behavior.
- A source scan found no direct PLAN.json consumer in the other registered application repositories and no review-UI reader in methodology source.
- Disposition: proceed to T6 because the approved T11 migration explicitly addresses each incompatible consumer and prevents use of 1.2.0 until that migration passes. If T11 cannot demonstrate fail-closed compatibility, stop before any 1.2.0 approval or launch.
