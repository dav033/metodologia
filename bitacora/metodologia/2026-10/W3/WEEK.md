---
status: draft
---
# metodologia — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- Runner internet research recorded in `artifacts/runner-model-research-20261017.md`: Luna high provisional candidate; Luna medium and Haiku5.5 medium comparators. Official sources do not establish a Runner winner. No pilot, selection or runtime change; proposed validation remains unapproved.
- D-068 records owner-approved Luna high as default Researcher. Runner is the last role choice; Researcher fallback and coordinated runtime rollout remain separate. No installation/configuration changed.
- Researcher pilot COMPLETE18/18 after owner-authorized codex-luis continuation, no repeats. Published-source supplement corrects R6 wording discounts uniformly; original scores preserved. Final content/source cases: Sonnet5/6, Sol6/6, Luna6/6; all36/36 requested criteria, source coverage35/36,36/36,36/36. Independent final audit approves; P-115 closed. Mixed accounts and telemetry/source limits retained; Researcher subsequently selected under D-068.
- Researcher internet follow-up adds a primary search leaderboard and current official effort guidance: Sonnet medium / Sol medium broad-research candidates, Luna high for documentation, optional Haiku high challenger. External evidence only; Researcher remains unselected and no trial launched.
- D-067 selects Sonnet medium Implementer with Luna high fallback after both pass6/6 pilot cases. Documented policy; coordinated runtime rollout remains pending. Researcher/Runner still need final choices; Antagonist already has D-066.
- Implementer pilot closed:48/48 native cells, all eight configurations x6 cases audited without new calls. Original45/48 passes preserved; semantic/resource supplements yield Luna medium5/6, other seven6/6. I6 body-format ambiguity affects Luna medium and Haiku medium/xhigh; independent Luna medium leak remains (21 failed operation checks /23 connection observations). Full usage coverage; no invoice/quota equivalence, model/effort attestation limits retained. Final REPORT/comparison and integrity receipt in `artifacts/implementer-pilot-20261017/`; no permanent role selection.
- Owner's D-066 amendment consolidates active quota refresh, hard kind/group budgets and bounded headless sessions; 301 targeted tests and replay guards pass, two independent audits approve, isolated wheel verified. Existing broad-suite fixture/isolation failures remain outside scope (session411b81ed).
- D-066 replay/docs alignment and auth/challenge routing fix verified with 175 targeted tests; Antagonist costs are separate simulated units, installed agents regenerated (session 74ac99a7).
- D-065 records owner-approved Explorer Luna high, Sol medium for complicated work and Sonnet medium as its alternative; runtime stays unchanged. Researcher proposal is sourced and pending selection; no further experiment launched.
- Scheduler work advanced through M4 and now has one tested Planner→M1→M2→M3→M4 fixture flow; P-036 and P-038 closed under REQ-018.
- REQ-020 M2 T13–T23 offline integration, adversarial validation and synthetic benchmark are complete with independent review; the live-provider gate remains open.
- REQ-022 closed the Scheduler launcher/status/recovery gap with explicit frozen-plan opt-in, one durable M1 owner, a heartbeat projection, and M1-routed CLI/web controls. Legacy launch stays default; P-026 closed and P-001 now tracks only separate Maros and Relay follow-ups.
- M2 remains deterministic for live routing: the held-out Laya classifier did not beat the deterministic baseline and REQ-016 stays paused.
- REQ-008's T4 runtime fixes were verified, then the owner paused default activation and the remaining milestones.

## Done
- REQ-012 closed Planner phase 1 and its approval/plan synchronization gates.
- REQ-014/REQ-017 completed the Scheduler M3 executor and M4 observer; P-033, P-035, P-037 were closed, with measured host-local M4 fixture budgets.
- REQ-018 connected bounded M3 stream ingestion to M4, read-only metrics to M2, and audit incidents to M1; offline M4 recovery and the real two-profile P-036 smoke passed. Suites: M1 248, M2 65, M3 276, M4 135, Scheduler wildcard 236/4 skipped, package 15.
- REQ-021 wired opt-in M6 verification through the existing M1 boundary and proved Planner→M1→M2→M3→M4→M5→M6 rejection/recovery/acceptance. M6 package 67, integrated chain plus real-M3 test 6, and Scheduler wildcard 271 with 5 opt-in skips passed; the shutdown race found in review is fixed.
- REQ-019 T19 passed its fresh two-route gate and bounded live run in 74.351 s: one controlled quota failure, one real alternate-provider CLI invocation, two M5 decisions, continued snapshot and M1 completion. T20 spec and standards audits approved; acceptance matrix and final handoff are recorded, closing P-040.
- REQ-020 T13–T23 passed focused source, M1/M2/M3/M4/M5 E2E, adversarial and benchmark checks. Independent audit found and verified a fix for one eager M4 import; T20 metric history passed 5 tests and integrated T21 passed 8. The frozen benchmark labels/windows are synthetic and observed real quota/attribution coverage is 0%; T24–T26 remain gated.
- REQ-022 T1/T2/T3 passed 12, 8 and 15 focused tests; M1 integration 28, plan-launch guard 23, legacy web controls 1 and installed CLI helpers 2 also passed. Spec and standards audits approved all phases after an empty-`plan_ref` projection validation fix. The broad package module-list audit still finds the concurrent REQ-020 benchmark module absent from `py-modules`; no provider, Scheduler run, local server or per-user autostart was activated for REQ-022. D-051 records the boundary and P-026 is closed.
- REQ-007 migration proposal records M0–M9, a preservation inventory and rollback gates; implementation remains unapproved.

## Decisions
- D-043 keeps M6 opt-in through unchanged M1 `VerificationPort`; D-027 keeps remaining Laya experiments English-only and separate from M2 route quality; D-035 pauses REQ-016 training.
- D-051 keeps Scheduler execution behind explicit opt-in with one durable M1 owner; D-050 keeps M2 deterministic after the incomplete T24 experiment; D-049 preserves legacy quota-cache keys while deduplicating effective account aliases in memory.
- D-048 keeps M2 shadow comparison opt-in and side-effect-free.
- D-038 corrects the T12 sample count and retains its host-local budgets; D-039 keeps M1→M4 drain caller-driven; D-040 requires verified offline recovery candidates.

## Not done / dropped
- REQ-008 is paused at T4: default activation and T5–T8 remain pending the owner's explicit resume.
- REQ-015 remains awaiting plan approval; REQ-016 remains paused and no Laya checkpoint is enabled for live routing.
- REQ-007 implementation and the cross-platform matrix remain deferred; no repository push or deployment was part of this week's Scheduler closeout.
- M6 remains opt-in under D-043; the full Planner→M6 chain is verified locally, and no global activation was requested.
- REQ-020's separately authorized T24 real-provider attempt failed at T2's 300-second limit; P-041 tracks whether to prepare a new bounded authorization. REQ-022 itself used no live provider or quota operation.

## Carried over to next week
- P-013 bitácora backup/sync decision; P-017 migration follow-ups; P-003 visual review; P-001's Maros REQ-005 E2E and Relay F-23 helper tests; P-041's decision about a new REQ-020 experiment.
- P-026 closed under REQ-022. P-001's Scheduler lifecycle portion is closed; only its unrelated Maros/Relay follow-ups remain.
- P-036, P-038 and P-040 are closed. P-039 tracks existing M4 Ruff style findings. M4/M5/M6 stay opt-in; live callers must drain M3 from the owning M1 loop and manage their durable outbox cadence.

## REQ-008 — paused checkpoint
- M1/T3 implemented; T4 structured runtime and review fixes verified with 139 affected regressions and 10 wheel/install checks, plus scoped ruff.
- D-018 preserves completion history/counters through validated supersession. Owner paused execution; P-018 links the REPORT/HANDOFF. Defaults and T5–T8 remain pending; no active task writer/test handle or global installation.

## Migration planning — session 01a13754
- REQ-007: code-grounded platform migration proposal in [[../../migracion/README|migracion]], 10 milestones and 22 tasks, with no-loss inventory and rollback gates. Legacy baseline: 578 tests, 2 routing failures. Implementation remains unapproved.

## Runner selection — 2026-10-18
- D-069 records Luna high as default Runner and Sonnet5.5 low as alternative. Sonnet low is unmeasured. All role choices are recorded; coordinated runtime rollout remains pending. P-116 retains the independent partial-pilot continuation.

## Role policies activated — 2026-10-18
- D-070 activates owner-selected models/efforts, quota-family priority, arbitrary eligible accounts and explicit-complexity alternatives; Researcher fallback Sonnet low. Installed editable runtime and35 native files across five account config directories.296 affected tests and independent spec/standards reviews pass; installed CLI live quota-only preview selects Runner Sonnet low on Claude. No model/pilot call, commit or push; frozen experiments unchanged.
