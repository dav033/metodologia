---
id: REQ-015
status: clarifying
created: 2026-10-15
track: standard
---
# REQ-015 — Train and evaluate local Laya for Scheduler routing

## Problem & goal
M2 is integrated with local Laya, but the frozen v1 benchmark is synthetic: 200 cases, five eligible routes per
case, and a generated weighted-utility oracle. Its 100-case held-out result (Laya 14%, deterministic reference 21%)
does not estimate success on real Scheduler tasks. Laya currently has no training data carrying independent,
Scheduler-specific labels. The goal is to create a defensible, privacy-bounded training/evaluation set, fine-tune the
local Laya decision head on CUDA, and establish whether the resulting checkpoint improves route choice over the
existing deterministic policy.

**Success looks like:** a pinned local checkpoint trained from independent Scheduler-domain labels; a frozen,
group-disjoint real-task evaluation that compares the base and fine-tuned model with the deterministic reference;
zero hard-filter violations; a predeclared practically meaningful paired improvement and calibrated selective
coverage; reproducible GPU, memory and latency evidence; and the existing deterministic route remains active unless
the complete evidence passes M2's reviewed gate. A negative or underpowered result is a valid report, not a reason to
lower the gate.

## Users / actors / stakeholders
- M2 consumes a qualified local checkpoint only for ambiguous choices among deterministically eligible candidates.
- M1 continues to authorize and reserve every assignment.
- David reviews labels, the quality gate and whether the local checkpoint may enter the reviewed evidence allowlist.
- Existing verified Scheduler telemetry supplies observed context and outcomes; it does not represent outcomes for
  candidates that were never executed.

## Scope (in)
### US-1 (P1, Must) — Build independent Scheduler decision labels
As the Scheduler owner, I want a versioned, redacted dataset of real task/candidate snapshots with independently
reviewed route preferences, so training targets the intended routing trade-offs rather than a generated formula.
**Acceptance:** each retained case has the pre-decision READY task facts, only M2-eligible route candidates, a fixed
rubric, independently recorded labels/adjudication, source provenance and a content hash; related tasks cannot cross
train/calibration/test partitions.

### US-2 (P1, Must) — Fine-tune Laya locally
As the Scheduler owner, I want a reproducible local fine-tuning run on the A3000, so Laya can learn the reviewed
Scheduler-domain choices without an external teacher or hosted decision API.
**Acceptance:** the run records base checkpoint/revision, training data digest, configuration, seed, device, peak
VRAM/RSS and resulting artifact hashes; an offline load check succeeds; no artifact is uploaded.

### US-3 (P1, Must) — Evaluate route-choice value independently
As the Scheduler owner, I want a locked, independently labeled comparison of the fine-tuned model, its base model and
the deterministic reference, so we can tell useful generalization from memorization or calibration-only changes.
**Acceptance:** the report evaluates the full held-out English sample, reports paired quality/regret and uncertainty,
task-family/provider/effort slices, confidence calibration and selective coverage, hard-filter violations, latency and
memory. The held-out labels are not used for model, threshold or prompt selection.

### US-4 (P1, Must) — Preserve the safe M2 gate
As M1, I want the reviewed quality gate and deterministic fallback to remain authoritative, so training cannot silently
change routing or M1 authorization.
**Acceptance:** a new checkpoint remains diagnostic-only unless the validated artifacts pass all predeclared gates and
their exact digest is added through a reviewed code change; M1 continues to validate and reserve the selected route.

## Out of scope
- Using Claude, Codex, Gemini, hosted LLMs or Laya itself to generate gold labels or act as an external teacher.
- Calling provider APIs, spending subscription quota, or charging a paid API for data collection, training or evaluation.
- Rewriting historical runs, fabricating counterfactual outcomes for unchosen routes, or changing M1 authorization,
  reservation or capacity rules.
- Uploading/publishing a trained checkpoint, deploying it to shared/production runs, or enabling it by default for
  legacy tasks.
- Treating Laya confidence as a probability of real task success.
- Training on the frozen synthetic v1 corpus as evidence of real-world route-selection quality. It remains available
  for deterministic smoke tests and input-contract regressions only.

## Requirements
- R1. The new training/evaluation corpus shall use real, redacted pre-decision task and eligible-candidate snapshots;
  generated v1 utility labels shall not enter its supervised targets or held-out quality claims.
- R2. Human preference labels shall be collected without seeing Laya or deterministic predictions. Cases with reviewer
  disagreement shall retain the disagreement distribution or be adjudicated under the frozen rubric; they shall not be
  silently converted to one certain label.
- R3. Existing telemetry may provide observed verified outcome, duration, token and quota features. An outcome shall
  attach only to the route actually executed; unexecuted candidates shall remain counterfactual-unknown.
- R4. Dataset splits shall be frozen and content-addressed before any fine-tuned checkpoint evaluates them, grouped by
  task/thread or near-duplicate and separated by project/repository or time where the sample permits.
- R5. The training converter shall produce the pinned Laya JSONL `state`/`questions` plus `expected` or reviewed
  `gold` distributions, randomize choice order without leaking route rank, redact secrets and raw credentials, and
  reject malformed, duplicated or split-leaking cases.
- R6. Fine-tuning shall use the installed pinned Laya runtime offline. The first A3000 run shall freeze the encoder and
  train the decision head with a CUDA memory profile; full encoder tuning may be attempted only if a measured dry run
  fits the 6 GiB GPU budget without swap or violating the host safety margin.
- R7. Training seeds, optimizer-update count, base checkpoint, loss, option-order augmentation, lengths, calibration
  split and all artifacts shall be recorded. At least three seeds shall be compared on development data to expose
  seed-sensitive collapse; only development results may choose a recipe.
- R8. The final sample size shall be determined before unsealing test labels by a paired power calculation for a
  practically meaningful improvement. The provisional minimum effect is +5 percentage points over the deterministic
  reference; this is an explicit planning assumption to confirm before evaluation.
- R9. The held-out gate shall require the lower bound of a case-clustered 95% paired interval to exceed zero and the
  point estimate to meet the predeclared minimum effect, with zero hard-filter violations. Calibration thresholds
  shall be fit on separate calibration data and reported with Brier/ECE or equivalent, selective accuracy and
  coverage; all eligible cases, including fallbacks, remain in the production-hybrid comparison.
- R10. A failed, underpowered or non-calibrated experiment shall keep the current M2 deterministic policy and empty
  approved-evidence allowlist unchanged; no confidence cutoff shall be fitted on the final test set.
- R11. No M1 or M2 authorization boundary shall change: hard eligibility remains deterministic, M1 remains final
  authority, and the trained model can only rank the remaining eligible candidates.
- R12. All remaining REQ-015 Laya experiments shall use English task text and only the pinned `english` checkpoint;
  previous multilingual and typed-decisions results remain historical diagnostics and cannot guide model selection.

## Edge cases & errors
- Too few independent labels or a failed power calculation: do not train for a release claim; report sample limits and
  keep M2 deterministic.
- Historical data contains a selected route but no outcome, or a failed attempt was not independently verified: label
  the outcome unknown/claimed rather than successful/failed.
- Candidate quota/auth/capacity is unknown or stale: exclude it before Laya; do not make it a training-time choice.
- Duplicate/near-duplicate tasks, project overlap, rubric drift, inconsistent route IDs or malformed JSONL: fail
  dataset validation before training/evaluation.
- Reviewers disagree or no candidate is acceptable: preserve the distribution or abstention; do not fabricate a
  winner.
- Training OOM, CUDA loss, checkpoint corruption, offline cache miss, non-finite loss or seed collapse: preserve the
  base checkpoint and do not alter the runtime allowlist.
- A test label is consulted during hyperparameter, prompt, checkpoint or threshold selection: invalidate that test
  report and require a new independently frozen test set.

## Constraints
- Arch Linux host with NVIDIA RTX A3000 Laptop GPU, 6 GiB VRAM; local pinned runtime is Laya 0.4.7, Python 3.12.14,
  PyTorch 2.14.0+cu132. Local `laya-train` supports `--freeze-encoder`, `--dry-run`, `--eval`, `--device cuda`,
  micro-batch/gradient accumulation and `soft-ce`/`rlcd`.
- Prefer the documented frozen-encoder small-GPU path first; no assumption is made that full-encoder tuning fits.
- Task snapshots and annotations can contain private repository/work details; redact secrets, credentials, absolute
  home paths and unrelated task text, and keep the corpus/checkpoints local and access-controlled.
- Existing `bt_agents`, profiles, quota freshness and M1 limits remain the source of candidate/eligibility truth.
- No provider API, paid inference, checkpoint upload, deploy, commit or historical-run mutation.

## Priorities & phases
- Must: independently labeled dataset protocol; local CUDA head fine-tune; locked benchmark against base and reference;
  preserve deterministic fallback unless every gate passes.
- Later: full encoder tuning, more elaborate preference optimization or additional Laya architectures, only if a
  head-only model learns useful generalization and measured memory permits.
- Out: hosted teacher labeling, online exploration that consumes provider quotas, model publication and default
  production activation.

## Timeline & dependencies
- Depends on REQ-013's M2 interface and D-023 evidence gate. Training/evaluation cannot begin before the annotation
  source, utility rubric, practical effect threshold and required sample size are frozen.
- Requires independent human review capacity for labels. Existing selected-route telemetry alone cannot establish
  the counterfactual best route for unexecuted candidates.

## Assumptions
- Recommended label source is blinded human route preference over redacted, real M1/M2 candidate snapshots, with
  verified local telemetry used as factual candidate context and a separate secondary outcome analysis. This avoids
  using a hosted teacher and avoids treating the deterministic baseline as its own gold label.
- The +5 percentage-point minimum useful gain is provisional; it must be accepted or replaced before the locked test
  is evaluated.
- The first practical model is a frozen-encoder fine-tune on CUDA, not a claim that the full 421M-parameter encoder is
  trainable inside 6 GiB.
- Existing v1 synthetic artifacts remain immutable and cannot authorize a future trained checkpoint.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Partial — depends on independent human labels and sample-size calculation |

## Clarifications
- Initial research playback 2026-10-15: the installed Laya 0.4.7 includes `laya-train`; upstream's pinned fine-tuning guide supports a frozen encoder on small GPUs and calls for a separately held-out evaluation. No training had run at that point; a later, explicitly label-revealing control is recorded below.
- Owner steering 2026-10-15 (D-027): all remaining Scheduler Laya experiments use English task text and only the pinned `english` checkpoint. Do not use multilingual or typed-decisions checkpoints for further inference, training, model selection, or final evaluation. Existing non-English and other-checkpoint measurements remain historical diagnostics only. The Planner complexity target and M2 route-quality acceptance remain distinct.
- Owner target clarification 2026-10-15: success means approximately 85% exact-match top-1 accuracy across `low`, `medium`, `high`, and `extreme`, including when representative evaluation suites vary in size. This is expected performance over the task distribution, not a guarantee that every arbitrary five-task sample lands at 85%: five cases only permit 20-point accuracy steps, and 4/5 has a 95% Wilson interval of 37.6–96.4%. At 170/200, the interval is 79.4–89.3%; at 850/1000, it is 82.7–87.1%. Always report exact accuracy, sample size, a 95% interval, and class/source slices. This Planner target is separate from M2 route-choice quality.
- Classification diagnostic 2026-10-15: 80 curated synthetic vignettes (20 per class; 10 English and 10 Spanish per class), dataset SHA-256 `1e4e5bcdd555753ce54717e71a3ea4399e087b192f124358f56f87ce29a02920`. Pinned local English, multilingual and typed-decisions checkpoints ran on the RTX A3000 with CUDA and zero inference errors. Four-class top-1 was 37.5%, 28.75% and 32.5%; no checkpoint approached the 85% target or recalled any `extreme` examples with English/typed-decisions. These are exploratory rubric-comprehension results, not real-task, route-choice or success evidence; v1.1 reuses cases after an exploratory v1 pass.
- Training feasibility 2026-10-15: `laya-train --dry-run` read 80 formatted items, left 72 train items and 8 calibration items, and budgeted only 8 optimizer updates over four default epochs. It loaded no weights and performed no training. The calibration slice is below the documented minimum of 10 items for temperature fitting. No training was run because this hand-authored diagnostic corpus is not an appropriate training or locked-test source.
- Real-archive consistency check 2026-10-15: the three available approved Planner plans contribute 35 unique English tasks with stored labels (21 `medium`, 12 `high`, 2 `low`, no `extreme`). The frozen archive SHA-256 is `22b4d4870c71db7524f30f574f8a87062ca95885d52c43a001ecdbd13812ab35`; source-plan hashes are in its local manifest. Zero-shot CUDA accuracy against those existing Planner labels was 42.9% / 45.7% / 42.9% for English / multilingual / typed-decisions, below the 60% majority-class baseline; zero inference errors. These are not independently adjudicated labels or a four-class/Spanish test.
- Easy/complex collapse from that same frozen archive: majority `not_complex` baseline 65.7%; English 48.6% (complex recall 100%, not-complex recall 21.7%), multilingual 65.7% (complex recall 0%), and typed-decisions 51.4% (complex recall 100%, not-complex recall 26.1%). None reaches 85%; multilingual's baseline match is from predicting every task not-complex. Reproducible derivation is `plan-archive-binary-summary.json` beside the frozen results.
- Supplementary Planner fixture check 2026-10-15: six scenario `PLAN.json` files add 25 tasks absent from earlier local evaluation sets: 12 low / 7 medium / 6 high / 0 extreme, English only. Against fixture labels, four-class CUDA accuracy was 40% / 48% / 28% for English / multilingual / typed-decisions; the majority-low baseline was 48%. Binary majority-not-complex was 76%; multilingual matched it with 0% complex recall, English scored 64% (83.3% complex recall), and typed-decisions 56% (66.7% recall). Zero inference errors. These fixture labels are not independent human gold; checkpoint pretraining exposure to public repository text is unknown. This is a supplementary diagnostic, not a production or final-test result. Frozen rows, source hashes and raw results are in `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/planner-fixture-*`.
- Human-label bottleneck 2026-10-15: created a blinded 35-task review packet at `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/human-label-batch-01.jsonl`, SHA-256 `d8a112e8cd598845a5dde7df3ca660493dadb6dcd6ea6113370ce629b62694be`. It hides existing Planner labels/source IDs; it is a training/development seed only because Laya has already seen these task texts. More new real tasks are required to cover `extreme`, Spanish, and the locked test.
- Real-plan training dry-run: 35 items produced only 32 training items, 3 calibration items, and 4 optimizer updates over four epochs; 32 epochs would only raise the budget to 32 updates on the same 32 items. No model weights or gradients were used. Do not treat an aggressive epoch count as a substitute for a larger representative dataset.
- Training-path positive control 2026-10-15: trained a disposable, explicitly label-revealing dataset (160 train / 40 held out) with the multilingual checkpoint, frozen encoder, CUDA, `soft-ce`, option shuffling, seed 7, 8 epochs and 144 updates. It completed in 69.432 s on the RTX A3000; 250 ms `nvidia-smi` samples saw whole-GPU memory peak at 2,075 MiB from a 1 MiB baseline, and the output checkpoint was 1.3 GB. Laya reported held-out 62.5% before / 97.5% after, but every input disclosed its target, so this proves only the local train/save/load path. Offline reload on CUDA independently reproduced 39/40; p50/p95 was 25.38/28.40 ms and inference peak CUDA allocated/reserved memory was 1.57/1.59 GB decimal. Calibration had only 16 items and temperature reached the 0.5 clamp; confidence is not approved for gating. Dataset, log, checkpoint hashes and reports are in `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/positive-control-v1/`.
- Training-method finding 2026-10-15: upstream documents optimizer-update accounting, the small-GPU frozen-encoder path, a separate `--eval` set, calibration warnings, and seed-sensitive collapse. More epochs on 32 real archive examples would still repeat insufficient, three-class data. The reproducible collection/training/benchmark protocol is `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/TRAINING-PROTOCOL.md`.
- Metric boundary: the owner's provisional ~85% target is being explored as Planner complexity classification, while REQ-015's M2 objective is route-choice quality. Neither metric substitutes for the other. No model trained in this diagnostic work changes M2 runtime behavior, its approved checkpoint list, or M1 authorization.
- Bitacora review and corpus v1.3 (2026-10-15): reviewed 10 project workspaces (33 dated logs / 113 Goal sections, 45 plans / 363 task lines, 167 PENDING rows); 723 deduplicated candidates, 34 previously evaluated methodology tasks excluded, and 689 unlabeled inputs scored by all three local checkpoints on RTX A3000 CUDA with zero errors. v1.1 had wrongly excluded 75 Pictures/Proposal Studio tasks by numeric REQ collision; v1.2 fixed project-qualified exclusions. v1.3 grounds all 40 project simulations in the ten actual project slugs and keeps 40 invented tasks as a separate group, each group with 10 examples per class and 20 English / 20 Spanish.
- v1.3 quality result: on the balanced 80 provisional cases, exact accuracy is 26.2% / 31.2% / 25.0% (English / multilingual / typed-decisions) versus 25% baseline; complex recall is 22.5% / 5% / 25%, and extreme recall is zero for all. On 129 weak historical S/M/L proxy labels, accuracy is 41.9% / 41.1% / 38.0%, below 46.5% majority. This is not independent gold; no 85% claim is supported. Full details and 68 source-file hashes: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/mixed-bitacora-corpus-v1.3/CORPUS-REPORT.md`.
- A new 200-row blind packet (40 each of historical PLAN, PENDING, dated-log Goal, project-simulated, and invented) is available for development-label review. Laya has already seen every item, so it cannot be a locked test. Scope remains complexity-only; scope, duration, risk, coupling, confidence, evidence, and M2 route-choice quality still need separately defined/collected labels. No v1.3 fine-tuning was run; the earlier 40-per-fold fine-tune peaked at 32.5% exact and had only 0–5% complex recall, insufficient to justify more epochs.

- Paired context test 2026-10-15: 35 frozen English Planner tasks were scored task-text-only and with additional M1 dependencies, shared resources, and sanitized verification purposes. The English checkpoint moved 42.9%→51.4% (3 cases), multilingual 45.7%→40.0% (-2), typed-decisions stayed 42.9%; pooled change was +1/105, below the 60% majority baseline. No `extreme` or Spanish examples. Additional context alone does not explain or fix the low result. Full measurements: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/archive-context-paired-v1-report.md`.
- Assistant-provisional annotation diagnostic 2026-10-15: 200 tasks from the five-source blind batch received labels without consulting per-task Laya predictions or the source map; the existing CUDA predictions were joined only afterward by exact text and stable ID checks. Counts are 39 low / 56 medium / 77 high / 28 extreme, with 30 incomplete/stale/truncated tasks flagged. Against this single annotator, four-class accuracy is 31.5% / 29.5% / 31.0% versus 38.5% majority; binary easy/complex accuracy is 53.5% / 45.0% / 55.0% versus 52.5% majority. Complex precision is 64.3% / 22.2% / 68.3%, but complex recall only 25.7% / 1.9% / 26.7%; `extreme` recall is 0%. Removing the 30 flagged rows leaves 30.0% / 27.6% / 28.8%, below the 39.4% majority. Explanations are standardized by class rather than independently adjudicated per item; these are agreement diagnostics, not true accuracy, training gold, or a locked test. Preserve the 85% objective as unmet; do not increase epochs on these pseudo-labels. Artifacts: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/human-review-batch-02-v1.2/assistant-prelabels-v1.1-score.md` and `.json`.
- Ordinal score-head diagnostic 2026-10-15: on the same 200 assistant-provisional development labels, fixed nearest-level rounding scored 40.5% / 27.5% / 42.5% four-class for English / multilingual / typed-decisions, vs. 31.5% / 29.5% / 31.0% for `choice`; majority was 38.5%, with overlapping Wilson intervals. Typed-decisions binary easy/complex was 68% vs. 52.5% majority, but it predicted no `low` or `extreme` labels (both recalls 0%); high/extreme recall was 85.7% with 64.7% precision. Thus neither 85% four-class accuracy nor per-class precision is demonstrated. All 600 predictions used CUDA with zero invalid outputs; p50/p95 and memory are in the ordinal report. English and typed-decisions emitted invalid-temperature warnings, so confidence was not used. No training was run on assistant pseudo-labels.
- Paired head/language comparison 2026-10-15: the ordinal head changed correct→wrong / wrong→correct counts versus `choice` by 30/12 (English), 10/14 (multilingual), and 47/24 (typed-decisions). On English/Spanish slices, `score` accuracy was 41.5%/36.6% for English, 30.2%/17.1% for multilingual, and 45.3%/31.7% for typed-decisions; Spanish support is only 41. This is checkpoint/language-sensitive development evidence, not a generalizable gain. Full paired counts and metrics: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/human-review-batch-02-v1.2/ordinal-score-v1-comparison.md`.
- Owner confirmation and cross-source training reanalysis 2026-10-15: the target is exact-match four-class accuracy expected to remain near/above 85% across representative suite sizes. Paired base-vs-trained analysis of six existing group-held-out seeds found at most 3 net extra correct cases in a 40-task fold; exact McNemar p-values were 0.25–1.00. Binary accuracy stayed 50%, complex recall 0–5%, and each trained run predicted `medium` for 35–38/40 items. This does not justify increasing epochs on provisional labels. Reproducible analysis: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/analyze_cross_source_paired.py` and `cross-source-paired-seed-analysis.md`.
