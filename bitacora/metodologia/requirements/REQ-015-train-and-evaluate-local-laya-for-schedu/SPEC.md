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
**Acceptance:** the report evaluates the full held-out sample, reports paired quality/regret and uncertainty, language
and task-family slices, confidence calibration and selective coverage, hard-filter violations, latency and memory.
The held-out labels are not used for model, threshold or prompt selection.

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
- Research playback 2026-10-15: the installed Laya 0.4.7 includes `laya-train`; upstream's pinned fine-tuning guide supports a frozen encoder on small GPUs and calls for a separately held-out evaluation. No training was run during this investigation.
