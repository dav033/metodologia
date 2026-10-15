---
req: REQ-016
status: paused
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
- [x] T3b — Independently audit and freeze v2 data and manifest before model comparison · after: T2b · verify: regenerate all
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
- [x] T5e — Train and independently score corrected v4 Laya candidates offline on CUDA · after: T3b · verify: three
  frozen-encoder seeds and four one/two-layer partial-unfreeze runs record 912/912 successful updates, no warnings,
  checkpoint hashes, VRAM, latency, and development predictions · covers: R1, R6
- [x] T5f — Compare three predeclared deterministic smoothing values on v4 development · after: T3b · verify:
  alpha 1.0/0.1/0.01 score 338/400, 339/400 and 336/400; alpha 0.1 remains the fixed reference · covers: R7
- [x] T6 — Select the best Laya checkpoint from v4 development, freeze class mapping and both baselines, then seal
  the one-time test command and hashes · after: T5e, T5f · verify: lock selects `v4-partial-last2-seed-7` at 227/400;
  preflight validates 1000 blind inputs and confirms the label key remains unread · covers: R5, R7, R11

### M3 — One locked evaluation and audit
- [x] T7 — Score base and selected fine-tuned English checkpoints once on the v4 locked 1000 cases; compare with the
  25% balanced-majority baseline and frozen deterministic Naive Bayes reference · after: T6 · verify: report exact
  accuracy, Wilson and family-cluster intervals, per-class precision/recall, macro-F1, confusion matrix, invalid
  outputs, latency and CUDA memory; all models miss the 85% point target · covers:
  R7, R8
- [x] T8 — Audit the one-time v4 result, label derivation, split/leakage evidence, hashes, English-only and
  no-runtime-change invariants; record point-target and lower-bound verdict separately · after: T7 · verify:
  standalone audit reproduces prediction seals, confusion aggregates and one key read without rereading its contents ·
  covers: R2, R4, R5, R7, R9, R10

## Verification
The validator must pass before model access and again against the frozen artifacts: exactly 1008 train / 400 dev /
1000 test, 250 examples per class in test, at least 252 / 100 / 200 families in train / dev / test, and no shared
scenario family, project context, or wording template across splits. Check for class-word leakage, exact or near-
duplicate test text in prior Laya inputs, and labels/provenance in blind inputs.
Run at least three offline frozen-encoder CUDA seeds and safe partial-unfreeze candidates. Evaluate the 25% majority
and deterministic Naive Bayes reference. Select on development only. Open the test once after freezing the model,
prompt, mapping, reference policy and hashes. The v4 one-time test returned deterministic 787/1000 (78.7%) and
selected Laya 656/1000 (65.6%); both fail the 850/1000 point target and their family-bootstrap upper bounds are
83.2% and 69.0%. State that synthetic results do not estimate natural production accuracy.

## Rulings
- Use labels derived from a frozen structured scenario rubric before text generation: this makes the synthetic suite
  reproducible without human adjudication; it does not make labels independent evidence about production tasks.
- Split by authored scenario family and wording template: this tests transfer to unseen scenarios and language forms;
  it is stricter than random-row splitting and may lower scores.
- Keep 1000 balanced test rows: this provides 250 examples/class and useful uncertainty reporting; results estimate
  only the deliberately balanced suite.
- Human reviewers are not a prerequisite for this synthetic benchmark. A later claim about real tasks requires a
  separate naturally sampled English set with independent human labels.
- The v2 deterministic 400/400 development result is diagnostic evidence of lexical shortcuts, not a model-quality
  result; no Laya candidate was trained on v2. Preserve v2 unchanged.
- Preserve v3 after detecting its malformed 63-character base-checkpoint hash before any Laya call. Corrected v4
  pins the local checkpoint manifest and was independently audited before training and again before selection.
- Repeated partial-unfreeze runs raised Laya development results over frozen-encoder seeds but did not approach the
  deterministic reference. The one-time v4 test confirms more of the same recipe is not justified for this 85%
  target; new work would need a materially different representation/data approach and a fresh untouched test.
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
- 2026-10-15 — v2 passed its independent suite audit but deterministic Naive Bayes scored 400/400 on development,
  revealing class-specific lexical shortcuts; it was retained as a diagnostic and not used for Laya training. v3 was
  preserved after its manifest exposed an invalid 63-character checkpoint digest before any model call. Corrected
  v4 binds the checkpoint to the trusted local manifest, passed its independent audit, and preserves the English-only
  1008/400/1000 split.
- 2026-10-15 — On v4 development, the pinned base scored 116/400 (29.0%), frozen Laya seeds 185/400 (46.25%),
  184/400 (46.0%), and 192/400 (48.0%); deterministic alpha 0.1 scored 339/400 (84.75%). Three smoothing rounds
  scored 338/400, 339/400, and 336/400, so alpha 0.1 remained best.
- 2026-10-15 — Four partial-unfreeze checkpoints ran locally on the RTX A3000: final-two-layer seed 7 scored
  227/400 (56.75%); the three additional user-requested rounds scored 213/400 (53.25%, final-one-layer seed 7),
  224/400 (56.0%, final-two-layer seed 17), and 218/400 (54.5%, final-two-layer seed 42). Each completed 912/912
  updates without warnings; observed whole-GPU peaks were 2599–2751 MiB. Three same-recipe seeds averaged 55.75%.
- 2026-10-15 — Sealed `selection-lock-v4.json`, opened the v4 gold key once only after all 3000 model predictions
  were saved and hashed, and evaluated the 1000-case blind test. Deterministic Naive Bayes scored 787/1000 (78.7%,
  Wilson 76.1–81.1%, family bootstrap 74.1–83.2%); selected Laya scored 656/1000 (65.6%, Wilson 62.6–68.5%,
  family bootstrap 62.1–69.0%); base scored 264/1000 (26.4%). All miss the 85% point target. A standalone post-open
  audit passed without rereading the key. Full evidence: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-016/REPORT-v4.md`.
- 2026-10-15 — Ran Laya's official answer-tag positive control on the same train/development split, with the gold
  class deliberately exposed as `label=<gold>;`. Three two-layer partial-unfreeze CUDA seeds scored 367/400 (91.75%,
  seed 7), 364/400 (91.00%, seed 17), and 365/400 (91.25%, seed 42); mean 91.33%. Two passed the frozen warning
  gate. Seed 7 retained its rejected status because the calibration temperature hit the 0.5 clamp; a separate scorer
  preserved the warning and measured it for diagnosis only. The prefix parser scored 400/400 by construction. The
  independent audit passed and did not read the locked test. This is a label-leakage control, not task accuracy; v4
  task accuracy still misses 85%. Evidence: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-016/positive-control-v2-answer-tag/REPORT.md`.
- 2026-10-15 — At the owner's direction, paused further Laya training while returning focus to Scheduler M2. The
  final-four-layer AMP/checkpointing diagnostic (`v4-partial-last4-amp-ckpt-seed-7`) was interrupted with Ctrl-C at
  epoch 4/8, step 400, after 544.4 seconds. Sampled whole-GPU usage was 3,175 MiB of 6,144 MiB; no OOM occurred.
  PyTorch had warned that `lr_scheduler.step()` ran before `optimizer.step()`, consistent with GradScaler skipping an
  update. No completed development score or accepted checkpoint exists. Preserve but do not select the partial
  `checkpoint_latest/model.safetensors` (SHA-256 `150cb79b7b31fe442f45028634f207b34d81856f962baa55a0dcac8698b0925d`).
  The locked test was not reopened or changed. Resume only after M2 closeout and a new owner-directed priority.
