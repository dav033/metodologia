---
req: REQ-016
status: approved
created: 2026-10-15
---
# Plan — REQ-016 — Train and validate an English-only Laya Planner complexity classifier

## Approach
Freeze the Planner reasoning-complexity rubric and generate a controlled English task suite from structured
scenarios whose labels are assigned before their prose is rendered. Mix fresh simulations grounded in project
bitacoras with invented engineering scenarios. Split by scenario family and wording template, not random rows. The
locked test contains 1000 cases (250 per class); separate training and development sets support local CUDA training
and model selection. This validates agreement with this synthetic rubric distribution only, not real production-task
accuracy. Keep the experiment separate from M1/M2 runtime authorization.

## Global constraints
Only English task text and the pinned `english` checkpoint. Use the installed Laya offline on the RTX A3000; begin
with its encoder frozen. No paid/provider APIs, hosted teachers, uploads, deployment, commits, historical-run changes,
or M1/M2 code, routing, quotas, allowlist, and authorization edits. Preserve prior REQ-015 evidence. Task data and
checkpoints remain local under `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-016/`. Never train on
locked-test rows or tune after opening their labels.

## Tasks

### M1 — Freeze rubric and build data
- [ ] T1 — Record the four Planner reasoning definitions, explicit boundary cases, deterministic synthetic label
  oracle, and production-claim limitation · verify: oracle tests cover each class and boundary; its hash is in the
  manifest · covers: R2, R3, R9
- [ ] T2 — Author project-grounded and invented scenario families; render 1008 train, 400 development, and 1000
  locked-test cases in English, with exactly 250 per test class · after: T1 · verify: generator checks family/template
  disjointness, exact balance, no label leakage, English-only text, uniqueness, and prior-input near-duplicates ·
  covers: R1, R2, R4, R5
- [ ] T3 — Freeze the blind model inputs, private label key, source/family map, and hashes before any new Laya call ·
  after: T2 · verify: independent validator reproduces hashes and proves split disjointness; test key is not passed
  to training or inference · covers: R4, R5

### M2 — Train and choose on development data
- [ ] T4 — Run Laya dry-run and base-model development evaluation offline on CUDA · after: T3 · verify: exact
  English revision/hash and actual CUDA device are recorded; no locked-test input is scored · covers: R1, R6
- [ ] T5 — Fine-tune the English checkpoint with its encoder frozen for three fixed seeds, then compare on development
  only · after: T4 · verify: immutable logs record updates, data/base hashes, CUDA placement, elapsed time, peak VRAM
  and offline checkpoint reload · covers: R6
- [ ] T6 — Select the checkpoint and fixed class mapping from development results, then freeze the evaluation command
  and all hashes · after: T5 · verify: lock manifest identifies the blind test input hash but contains no test labels
  or predictions · covers: R5, R7

### M3 — One locked evaluation and audit
- [ ] T7 — Score base and selected fine-tuned English checkpoints once on the locked 1000 cases; compare with the
  deterministic balanced-class baseline · after: T6 · verify: report exact accuracy, Wilson interval, per-class
  precision/recall, macro-F1, confusion matrix, ordinal error, invalid outputs, latency and peak memory · covers:
  R7, R8
- [ ] T8 — Audit label derivation, family/template leakage, prior-input similarity, hashes, English-only and
  no-runtime-change invariants; record point-target and lower-bound verdict separately · after: T7 · verify: a
  standalone audit script reproduces each verdict from frozen artifacts · covers: R2, R4, R5, R7, R9, R10

## Verification
The validator must pass before model access and again against the frozen artifacts: exactly 1008 train / 400 dev /
1000 test, 250 examples per class in test, no shared scenario family or wording template across splits, no direct
class-word leakage, no exact or near-duplicate test text in any prior Laya input, and no labels in blind inputs.
Run at least three offline frozen-encoder CUDA seeds; select on development only. Open the test once after freezing the
model, prompt, mapping and hashes. Report the 25% balanced deterministic baseline. Require at least 850/1000 for the
85% point target; claim benchmark accuracy is at least 85% only if the 95% Wilson lower bound also clears 85%
(approximately 873/1000). State that synthetic results do not estimate natural production accuracy.

## Rulings
- Use labels derived from a frozen structured scenario rubric before text generation: this makes the synthetic suite
  reproducible without human adjudication; it does not make labels independent evidence about production tasks.
- Split by authored scenario family and wording template: this tests transfer to unseen scenarios and language forms;
  it is stricter than random-row splitting and may lower scores.
- Keep 1000 balanced test rows: this provides 250 examples/class and useful uncertainty reporting; results estimate
  only the deliberately balanced suite.
- Human reviewers are not a prerequisite for this synthetic benchmark. A later claim about real tasks requires a
  separate naturally sampled English set with independent human labels.

## Progress log
- 2026-10-15 — Owner requested an English-only task suite and Laya training/evaluation, clarified an approximately
  85% exact-match target and that a five-task sample is too small. The owner authorized locally building and testing
  the suite; no paid API, deployment or runtime change is in scope. Replaced the human-review gate with a synthetic,
  pre-render label oracle and explicitly bounded the resulting claim. Dataset and model work had not started at plan
  approval.
