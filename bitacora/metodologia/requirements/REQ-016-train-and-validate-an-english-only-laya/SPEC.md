---
id: REQ-016
status: ready
created: 2026-10-15
track: standard
---
# REQ-016 — Train and validate an English-only Laya Planner complexity classifier

## Problem & goal
The owner wants to know whether local Laya can classify Planner task complexity reliably enough to help the workflow.
The best current English-only development result is 41.5% (66/159), equal to the majority baseline; recall is zero
for `low` and `extreme`. Those labels are provisional, and Laya has already seen all 159 task texts. They cannot
establish the behavior of a new benchmark or justify more epochs.

**Goal:** determine whether a locally fine-tuned Laya `english` checkpoint can reach at least 85% exact-match
four-class accuracy on a new, locked English benchmark, without changing Planner or M2 runtime behavior.

**Success looks like:** at least 850/1000 correct on a class-balanced benchmark with 250 tasks in each of `low`,
`medium`, `high`, and `extreme`; report its 95% Wilson interval and every class's precision/recall. A statistical
claim that underlying accuracy is at least 85% requires the lower 95% Wilson bound to clear 85% (approximately
873/1000 correct). A five-task run is only a smoke check: its score moves in 20-point steps and cannot validate the
target. Because the benchmark labels are generated from a frozen scenario rubric, this measures agreement with that
synthetic English benchmark, not accuracy on future production tasks.

## Users / actors / stakeholders
- David owns the Planner rubric and decides whether the measured behavior is useful.
- The local benchmark generator assigns its gold label from a frozen structured scenario before rendering task text;
  it never reads Laya outputs.
- M2 remains a separate route-choice system with its own quality gate.

## Scope (in)
### US-1 (P1, Must) — Create a controlled English benchmark
As the Planner owner, I want a large suite of English engineering tasks with labels fixed by the Planner rubric before
inference, so I can measure whether Laya understands the four complexity levels.
**Acceptance:** the frozen test has 1000 unique tasks, 250 per class, generated from held-out scenario families and
wording templates; the 1008-task training set and 400-task development set use disjoint families/templates; no test
text or near-duplicate was previously sent to Laya; the generator and rubric hashes are recorded.

### US-2 (P1, Must) — Fine-tune the English checkpoint locally
As the Planner owner, I want a reproducible offline CUDA fine-tune using a separate labeled training set, so training
can be compared against the unchanged English base without provider calls.
**Acceptance:** data, checkpoint, prompt, seeds, optimizer updates, memory, device and artifact hashes are recorded;
at least three seeds are compared on development data; selected checkpoints load offline on the RTX A3000.

### US-3 (P1, Must) — Measure the locked 85% target
As the Planner owner, I want a one-time locked evaluation, so I can see exact-match accuracy, uncertainty and class
failures without selecting the test to fit the model.
**Acceptance:** evaluate the base English checkpoint and selected fine-tuned English checkpoint on the same 1000 test
items; report exact accuracy, 95% Wilson interval, 25% balanced-majority baseline, confusion matrix, per-class
precision and recall, macro-F1, ordinal error, latency, memory and invalid outputs.

### US-4 (P1, Must) — Keep classifier results out of runtime authorization
As M1, I want the complexity experiment to remain diagnostic-only, so its score cannot authorize a route or alter
Scheduler behavior.
**Acceptance:** no M1/M2 code, checkpoint allowlist, routing policy, historical run, or production task is changed.

## Out of scope
- Spanish, multilingual, or typed-decisions checkpoints.
- Claims about real-task prevalence, future task success, M2 route quality, or production accuracy based on the
  synthetic benchmark alone.
- Enabling the fine-tuned model in Planner or Scheduler runtime.
- Using Laya outputs to create labels or selecting a model/prompt after test results are seen.
- Full-encoder tuning unless frozen-encoder results show useful generalization and a separate memory dry-run fits.

## Requirements
- R1. Every inference, training and evaluation input for this requirement shall be English, and the only checkpoint
  shall be the pinned `english` Laya checkpoint.
- R2. Each synthetic gold label shall be assigned from the structured scenario and frozen rubric before the task text
  is rendered; neither labels nor class names may be present in Laya's input.
- R3. The complexity rubric shall measure reasoning needed (`low`, `medium`, `high`, `extreme`), not task duration,
  file count, scope, risk, coupling or model strength.
- R4. The locked test shall contain 1000 new English tasks, 250 per class, generated from scenario/wording families
  absent from the 1008-task training set and 400-task development set. No test task or near-duplicate may appear in
  prior Laya inputs.
- R5. Before test inference, freeze task-family splits, generator/rubric hashes, model revision, checkpoint hash,
  prompt, score-to-class mapping and primary metric. Test data cannot be used for training or tuning.
- R6. Training shall use the installed pinned Laya runtime offline, first with the encoder frozen on CUDA. Compare at
  least three seeds on development data; run full-encoder tuning only after a measured safe dry run fits the 6 GiB
  GPU budget and host safety margin.
- R7. The primary test metric shall be exact four-class accuracy with a 95% Wilson interval and per-class metrics.
  The point target is at least 850/1000; claim underlying benchmark accuracy of at least 85% only if the interval's
  lower bound is also at least 85% (approximately 873/1000 at n=1000).
- R8. A five-task score may be reported as a smoke check only; it shall not count as evidence that the 85% target is
  met.
- R9. Report synthetic-benchmark accuracy separately from any future, independently labeled natural-task estimate.
- R10. No result from this requirement shall authorize or alter M1/M2 routing, reservation, quotas, or checkpoint
  allowlists.

## Edge cases & errors
- Generator emits non-English text, class-name leakage, exact/near duplicates, or a split-family overlap: reject the
  dataset before inference.
- A scenario cannot be confidently assigned to one rubric class from its structured facts: reject it rather than
  force a gold label.
- The wording makes the class obvious through a repeated template rather than task semantics: diversify or remove the
  family using development data only; never repair the locked set after model results.
- CUDA OOM, non-finite loss, seed collapse, offline cache miss, invalid outputs or a corrupted checkpoint: preserve
  the base model and do not touch Scheduler runtime state.

## Constraints
Arch Linux, RTX A3000 Laptop GPU with 6 GiB VRAM, local pinned Laya 0.4.7, Python 3.12 and PyTorch CUDA. All model
work is offline and local. No provider APIs, paid inference, hosted teachers, uploads, deployment, commits or
historical-run edits. New task text, labels and checkpoints remain permission-restricted under the existing
`/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-016/` directory.

## Priorities & phases
Must: freeze rubric/generator; build disjoint English train/development/locked sets; compare the English base with at
least three frozen-encoder training seeds; test once and report class behavior and uncertainty; retain diagnostic-only
status. Later: full encoder tuning only if the head-only model generalizes and a measured run fits safely. Out:
multilingual support and runtime activation.

## Timeline & dependencies
- Depends on the existing Planner four-class rubric and the pinned local Laya 0.4.7 English checkpoint.
- All dataset generation, fine-tuning, and evaluation can run locally. Human labeling is not a prerequisite for the
  synthetic benchmark; it would be required for a separate claim about real-task accuracy.

## Assumptions
The 1000-case benchmark is deliberately class-balanced to expose collapse on `low` or `extreme`; its score estimates
agreement on this generated benchmark distribution, not natural production prevalence. Task families and wording
templates are split before rendering/inference. Historical bitacora tasks can inform project contexts, but exact or
near-duplicate text already sent to Laya is excluded from the locked set.

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
| Timeline | Clear — local work; natural-task validation is a later requirement |

## Clarifications
- Owner steering 2026-10-15 (D-027): focus exclusively on English task text and the `english` Laya checkpoint; do not
  spend effort on multilingual precision.
- Owner target clarification 2026-10-15: aim for approximately 85% exact-match accuracy over all four Planner
  complexity labels across task suites; a five-item suite is too noisy to validate this, so use a locked 1000-item
  suite and report its confidence interval.
- Synthetic-benchmark boundary: generated labels are a controlled test oracle, not independent human labels or proof
  of production accuracy. If a production claim is later needed, create a separate naturally sampled and independently
  reviewed English benchmark.
