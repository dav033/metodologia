---
req: REQ-015
status: review
created: 2026-10-15
---
# Plan — REQ-015 — Train and evaluate local Laya for Scheduler routing

## Approach
Build a new real-task, independently human-labeled corpus and keep the frozen synthetic v1 fixtures only for
contract/smoke regressions. Reuse M2's deterministic eligibility and verified telemetry, then fine-tune local Laya
with the encoder frozen first because the A3000 has 6 GiB; compare the bilingual multilingual and typed-decision base
models on development data before freezing one recipe. Fit any runtime confidence gate on separate calibration cases
and compare the complete production hybrid to `bt_agents` on a locked, powered holdout. The existing M2 evidence gate
and deterministic fallback stay authoritative unless every criterion passes and the exact evidence is independently
reviewed.

## Global constraints
No Claude/Codex/Gemini or hosted teacher, no paid provider calls or quota consumption, no checkpoint upload, no deploy,
no M1 authorization/reservation changes, and no historical run or `RUN.json` edits. Keep task data redacted and local;
never assign counterfactual outcomes to routes that were not executed. Do not train or claim real quality from the
synthetic v1 labels. Training artifacts stay outside the repository and are content-addressed. Preserve concurrent
REQ-014 changes in the shared worktree.

## Tasks
### M1 — Independent labels and immutable dataset
- [ ] T1 — Freeze annotation rubric, blind-review protocol, source-redaction rules, +5pp minimum useful effect and
  paired power-analysis inputs before labels/results are unsealed · repo: methodology · verify:
  `python -m unittest tests.test_scheduler_training_protocol` · covers: R1, R2, R8
- [ ] T2 — Add an M2-snapshot-to-Laya-JSONL converter and validator for hard-filtered candidate choices, reviewed
  expected/gold distributions, randomized option order, provenance, hash-disjoint grouped splits and privacy limits ·
  repo: methodology · after: T1 · verify:
  `python -m unittest tests.test_scheduler_training_dataset` · covers: R1, R3, R4, R5, R11
- [ ] T3 — Collect blinded human preferences on redacted real READY-task snapshots, retain disagreement/abstention,
  adjudicate the agreed rubric, and freeze the corpus only after the power target is reached · repo: methodology ·
  after: T2 · verify: `python skill/scripts/bt_scheduler_laya_dataset.py validate --frozen-dataset <path>` · covers:
  R1, R2, R4, R8

### M2 — Local CUDA fine-tuning
- [ ] T4 — Compare zero-shot multilingual and typed-decisions checkpoints on development data; run
  `laya-train --dry-run` and profile frozen-encoder CUDA memory using a tiny throwaway copy · repo: methodology ·
  after: T3 · verify:
  `HF_HUB_OFFLINE=1 python skill/scripts/bt_scheduler_laya_train.py dry-run --device cuda` · covers: R6, R7
- [ ] T5 — Fine-tune the selected bilingual base with frozen encoder, randomized choices and recorded soft-CE/RLCD
  variants across at least three seeds; save checkpoints outside the repo and retain per-run metrics/hashes · repo:
  methodology · after: T4 · verify:
  `HF_HUB_OFFLINE=1 python skill/scripts/bt_scheduler_laya_train.py train --device cuda --seeds 3` · covers: R6, R7
- [ ] T6 — Select a checkpoint and recipe on development data only, fit M2 confidence threshold on the isolated
  calibration split, then hash/freeze the exact candidate checkpoint and runtime policy · repo: methodology · after:
  T5 · verify: `python skill/scripts/bt_scheduler_laya_dataset.py freeze-evidence --split calibration` · covers: R4,
  R7, R9

### M3 — Locked quality and operational benchmark
- [ ] T7 — Compare the frozen fine-tuned checkpoint, the same base checkpoint and deterministic `bt_agents` reference
  on every locked holdout case; report top-1, weighted regret, paired cluster bootstrap, calibration/selective
  coverage and English/Spanish/family/provider/effort slices · repo: methodology · after: T6 · verify:
  `python skill/scripts/bt_scheduler_laya_train.py evaluate --split held-out --resamples 10000` · covers: R3, R8,
  R9, R10
- [ ] T8 — Measure CUDA cold/warm latency, peak VRAM/RSS, offline restart, multiple seeds and fallback; refuse
  runtime use on OOM, corruption, low calibration support or any hard-filter violation · repo: methodology · after:
  T7 · verify: `python skill/scripts/bt_scheduler_laya_train.py benchmark --offline --device cuda` · covers: R6, R7,
  R9, R10

### M4 — Audit and conditional M2 activation
- [ ] T9 — Independently audit label provenance, leakage tests, evaluation math, evidence hashes and gate decision;
  add the exact checkpoint/evidence digest to M2 only if all preregistered gates pass, otherwise preserve the empty
  allowlist · repo: methodology · after: T8 · verify:
  `python -m unittest tests.test_scheduler_decision_integration tests.test_scheduler_bench_quality` · covers: R4,
  R9, R10, R11
- [ ] T10 — Run M2, M1, Planner, package and full methodology regressions; update REQ report, decision log and
  project/day indexes with the actual verdict · repo: methodology · after: T9 · verify:
  `PYTHONPATH=. python -W error::ResourceWarning -m unittest discover -s tests` · covers: R1, R6, R9, R10, R11

## Verification
1. Validate schema, provenance, privacy redaction, no selected-vs-unselected outcome confusion and group-disjoint
   splits before fine-tuning; verify corpus/label/rubric SHA-256 before first training call.
2. Run `laya-train --dry-run` offline against a small real-format sample, then profile a frozen-encoder CUDA training
   smoke run under a recorded GPU-memory budget. No provider/model inference API is involved.
3. Train from the approved corpus with frozen encoder, controlled A/B objectives and at least three seeds; compare
   checkpoint revisions using development cases only and retain every run's original report.
4. On an untouched, power-sized holdout, compare base Laya and the frozen fine-tuned candidate with the deterministic
   reference on the same complete cases. Use case-clustered paired resampling, fixed seed and 10,000 replicates.
5. Pass only when hard-filter violations are zero, the 95% paired lower bound is positive, the point gain meets the
   preregistered +5 percentage-point floor, calibration is supported on a separate set, and measured latency/memory
   fit M2's documented limits. Otherwise keep deterministic recommendations and report the failed criterion.
6. Verify a corrupted/missing checkpoint, offline restart, low confidence, malformed response, timeout, OOM and open
   circuit all preserve deterministic routing; M1 remains final reservation authority.
7. Run the M2 module tests, Plan→M1→M2 integration tests, M1 core, Planner, installed-wheel checks and full
   methodology suite; `git diff --check`; preserve unrelated M3 work.

## Rulings
- Use blinded human preferences as primary route-choice labels; use existing verified telemetry as factual context and
  secondary outcome analysis because unselected routes have no observed task outcomes — cost if wrong: high.
- Start with the encoder frozen on CUDA; official pinned Laya docs say this supports smaller GPUs with lower expected
  gains than full fine-tuning — cost if wrong: low, since a measured follow-up can test full tuning later.
- Require +5pp point gain plus a positive 95% paired lower bound and zero hard-filter violations; the +5pp floor is a
  provisional practical threshold and must be accepted before the locked test — cost if wrong: medium.
- Preserve M2's code-reviewed digest gate; a trained checkpoint never self-authorizes — cost if wrong: high.

## Progress log
- 2026-10-15 — Researched the pinned upstream Laya fine-tuning guide and evaluation harness; confirmed local Laya
  0.4.7 `laya-train` and CUDA availability on the RTX A3000. Frozen-encoder training is documented for small GPUs;
  full fine-tuning examples use 16 GiB-class hardware. No training or provider API call was run.
- 2026-10-15 — Audited the v1 M2 corpus: 100 synthetic held-out cases, exactly five candidates each, labels generated
  from randomized features and explicit utility weights, 50 English/50 Spanish across five families. It is not an
  empirical route-success dataset and is excluded from REQ-015 training/quality claims.
- 2026-10-15 — Drafted this evidence-first plan. Status remains `review`; implementation waits for owner approval and
  an independently labeled dataset source.
