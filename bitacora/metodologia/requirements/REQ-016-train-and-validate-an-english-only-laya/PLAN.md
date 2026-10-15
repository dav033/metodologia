---
req: REQ-016
status: approved
created: 2026-10-15
---
# Plan — REQ-016 — Train and validate an English-only Laya Planner complexity classifier

## Approach
Freeze the Planner reasoning-complexity rubric and generate a controlled English task suite from structured
scenarios whose labels are assigned before their prose is rendered. Mix fresh simulations grounded in project
bitacoras with invented engineering scenarios. The v1 pilot has only 16 development families, and its Naive Bayes
errors include two whole failed `low` families; preserve it and keep its locked test unopened. Build an independent
v2 with at least 252/100/200 train/development/test scenario families, split by context and wording template, before
model selection. The locked v2 test contains 1000 cases (250 per class). This validates agreement with this synthetic
rubric distribution only, not real production-task accuracy. Keep the experiment separate from M1/M2 runtime
authorization.

## Global constraints
Only English task text and the pinned `english` checkpoint. Use the installed Laya offline on the RTX A3000; begin
with its encoder frozen. No paid/provider APIs, hosted teachers, uploads, deployment, commits, historical-run changes,
or M1/M2 code, routing, quotas, allowlist, and authorization edits. Preserve prior REQ-015 evidence. Task data and
checkpoints remain local under `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-016/`. Never train on
locked-test rows or tune after opening their labels.

## Tasks

### M1 — Freeze rubric and build data
- [x] T1 — Record the four Planner reasoning definitions, explicit boundary cases, deterministic synthetic label
  oracle, and production-claim limitation · verify: oracle tests cover each class and boundary; its hash is in the
  manifest · covers: R2, R3, R9
- [x] T2 — Author project-grounded and invented scenario families; render 1008 train, 400 development, and 1000
  locked-test cases in English, with exactly 250 per test class · after: T1 · verify: generator checks family/template
  disjointness, exact balance, no label leakage, English-only text, uniqueness, and prior-input near-duplicates ·
  covers: R1, R2, R4, R5
- [ ] T2b — Build independent suite v2 from structured project simulations and invented domains; render 1008 train,
  400 development, and 1000 locked-test rows from 252/100/200 task families (63/25/50 per class), with four/four/five
  wording variants per family · after: T2 · verify: 138 disjoint project contexts are split 63/25/50, 69 project-
  simulated and 69 invented contexts overall, exact class/source balance, no label leakage, English-only text,
  unique tasks, and no prior-input near-duplicates · covers: R1, R2, R4, R5, R11
- [x] T3 — Freeze the blind model inputs, private label key, source/family map, and hashes before any new Laya call ·
  after: T2 · verify: independent validator reproduces hashes and proves split disjointness; test key is not passed
  to training or inference · covers: R4, R5
- [ ] T3b — Independently audit and freeze v2 data and manifest before training · after: T2b · verify: regenerate all
  hashes and family/context/template counts from saved files, compare prior Laya inputs, and verify blind inputs omit
  labels/provenance · covers: R2, R4, R5, R11

### M2 — Train and choose on development data
- [x] T4 — Run Laya dry-run and base-model development evaluation offline on CUDA · after: T3 · verify: exact
  English revision/hash and actual CUDA device are recorded; no locked-test input is scored · covers: R1, R6
- [x] T5 — Fine-tune the English checkpoint with its encoder frozen for three fixed seeds, then compare on development
  only · after: T4 · verify: immutable logs record the update budget, data/base hashes, CUDA placement, elapsed time, peak VRAM
  and offline checkpoint reload · covers: R6
- [x] T5b — Compare one- and two-final-layer partial-unfreeze Laya recipes on development after full-encoder CUDA OOM ·
  after: T5 · verify: only explicitly listed final encoder layers and decision heads receive gradients; CUDA memory cap,
  AMP, checkpointing, elapsed time, warning log and offline reload are recorded; no locked-test input is scored · covers: R6
- [x] T5c — Implement and evaluate a deterministic unigram/bigram Naive Bayes reference on development · after: T5 ·
  verify: it trains on the frozen training split only, accepts blind task text without reading labels, emits reproducible
  predictions under a fixed smoothing/tie-break configuration, and its source hash is recorded · covers: R7
- [x] T5d — Audit development accuracy by task family and inspect source diversity · after: T5b, T5c · verify: saved
  v1 family metrics show 16 development families, with Naive Bayes at 0/25 on two low families; the 79.25% row score
  therefore does not transfer consistently across all families · covers: R4, R7, R11
- [ ] T5e — Train v2 Laya candidates offline on CUDA and score only v2 development data · after: T3b · verify: at least
  three fixed frozen-encoder seeds, plus a partial-unfreeze recipe if still safe; record successful optimizer steps and
  resolve or avoid the v1 GradScaler/scheduler warning; reload checkpoints offline · covers: R1, R6
- [ ] T5f — Train and score the deterministic unigram/bigram reference on v2 development data · after: T3b · verify:
  same v2 training split, fixed tokenizer/smoothing/tie-breaks and frozen implementation hash · covers: R7
- [ ] T6 — Select the best Laya checkpoint from v2 development, freeze class mapping and both baselines, then freeze
  the one-time test command and all hashes · after: T5e, T5f · verify: lock stores blind test hashes from the suite
  manifest without reading the private key; a preflight proves the label-key file is not opened until all model and
  deterministic predictions are saved and hashed · covers: R5, R7, R11

### M3 — One locked evaluation and audit
- [ ] T7 — Score base and selected fine-tuned English checkpoints once on the v2 locked 1000 cases; compare with the
  25% balanced-majority baseline and frozen deterministic Naive Bayes reference · after: T6 · verify: report exact accuracy, Wilson interval, per-class
  precision/recall, family-cluster bootstrap interval, macro-F1, confusion matrix, ordinal error, invalid outputs,
  latency and peak memory · covers:
  R7, R8
- [ ] T8 — Audit label derivation, family/template leakage, prior-input similarity, hashes, English-only and
  no-runtime-change invariants; record point-target and lower-bound verdict separately · after: T7 · verify: a
  standalone audit script reproduces each verdict from frozen artifacts · covers: R2, R4, R5, R7, R9, R10

## Verification
The validator must pass before model access and again against the frozen artifacts: exactly 1008 train / 400 dev /
1000 test, 250 examples per class in test, at least 252 / 100 / 200 families in train / dev / test, and no shared
scenario family, project context, or wording template across splits. Check for class-word leakage, exact or near-
duplicate test text in prior Laya inputs, and labels/provenance in blind inputs.
Run at least three offline frozen-encoder CUDA seeds; compare partial-unfreeze recipes if full-encoder tuning does not
fit. Evaluate both the 25% majority and deterministic Naive Bayes reference. Select on development only. Open the test
once after freezing the model, prompt, mapping, reference policy and hashes. Require at least 850/1000 for the
85% point target. Show the ordinary Wilson interval as descriptive and use family-cluster bootstrap for any claim
about transfer beyond these scenario families. State that synthetic results do not estimate natural production accuracy.

## Rulings
- Use labels derived from a frozen structured scenario rubric before text generation: this makes the synthetic suite
  reproducible without human adjudication; it does not make labels independent evidence about production tasks.
- Split by authored scenario family and wording template: this tests transfer to unseen scenarios and language forms;
  it is stricter than random-row splitting and may lower scores.
- Keep 1000 balanced test rows: this provides 250 examples/class and useful uncertainty reporting; results estimate
  only the deliberately balanced suite.
- Human reviewers are not a prerequisite for this synthetic benchmark. A later claim about real tasks requires a
  separate naturally sampled English set with independent human labels.
- The v1 locked test remains unopened: its development split has only 16 scenario families and family-wise NB errors
  show that the 79.25% row average hides complete failures on two low families. A fresh v2 must meet the family minimum
  before selection; this ruling uses only v1 development labels, never its locked key.

## Progress log
- 2026-10-15 — Owner requested an English-only task suite and Laya training/evaluation, clarified an approximately
  85% exact-match target and that a five-task sample is too small. The owner authorized locally building and testing
  the suite; no paid API, deployment or runtime change is in scope. Replaced the human-review gate with a synthetic,
  pre-render label oracle and explicitly bounded the resulting claim. Dataset and model work had not started at plan
  approval.
- 2026-10-15 — Built the frozen v1 suite outside the repository: 1008 train / 400 development / 1000 locked test,
  250 per class per split, from 48 / 16 / 32 disjoint scenario families and 50% project-grounded / 50% invented
  cases. Independent audit passed 14 checks across 1076 previously saved Laya input texts with zero exact/near
  matches; seven unit tests passed. The pinned English base scored 122/400 (30.5%) on development, versus the
  deterministic balanced baseline's 25%; CUDA inference used the RTX A3000 (sampled 2657 MiB peak). Locked test
  remains unscored.
- 2026-10-15 — Laya dry-run validated 1008 train and 400 development rows and budgeted 912 updates for the planned
  eight epochs (908 train rows after Laya reserves 100 for internal calibration). Frozen-encoder CUDA training has
  started with seeds 7, 17, and 42; seed 7 completed in 394.813 s at 2427 MiB sampled whole-GPU peak. The pinned
  training log contains a PyTorch GradScaler/scheduler warning; preserve and audit it before accepting checkpoints.
- 2026-10-15 — All frozen-encoder seeds completed offline on CUDA and were independently reloaded/scored on the 400
  development tasks: 50.25% (seed 7), 43.75% (seed 17), and 49.0% (seed 42), all above the 25% deterministic
  baseline but far below the 85% target. Every log records one initial GradScaler/scheduler warning; Laya reports the
  912-update budget but not successful optimizer-step count. Do not open the test yet; next assess full-encoder memory
  with a small throwaway CUDA run, then continue development-only tuning if it fits safely.
- 2026-10-15 — The development-only unigram/bigram Naive Bayes reference scored 317/400 (79.25%) with fixed alpha
  0.1, greatly exceeding the best Laya head-only seed (50.25%) and the 25% majority baseline. Most reference errors
  are low/extreme boundary confusions; medium recall is 99% and high recall is 97%.
- 2026-10-15 — Two full-encoder probes on CUDA failed at the optimizer update: the 88% allocator-cap run peaked at
  5307 MiB and requested 22 MiB beyond its artificial cap; the 94% run with max_len 256 peaked at 5675 MiB, had
  182 MiB device memory free, and failed under its 5.38 GiB allocator cap. Preserve both artifacts. Full-encoder
  AdamW tuning is not safe on this 6 GiB device; continue with final-layer partial-unfreeze and the deterministic
  development reference. Locked test remains unopened.
