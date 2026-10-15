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
- 2026-10-15 — Ran a separate Planner-complexity diagnostic at the owner's requested ~85% target. The frozen 80-case
  bilingual synthetic set scored 37.5% / 28.75% / 32.5% top-1 on the three pinned checkpoints, all on CUDA. The
  corrected v1.1 option schedule reused the same cases after an exploratory v1 pass, so neither pass is confirmatory.
  See `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/` for corpus, protocol, runner and raw results.
  `laya-train --dry-run` calculated eight optimizer updates from 72 training items and eight calibration items; no
  model weights were loaded, no gradient updates ran and no checkpoint was produced. Do not fine-tune on this corpus.
- 2026-10-15 — Audited all available approved Planner JSON plans: only 35 unique labelled tasks across three plans,
  English only, with labels 2 low / 21 medium / 12 high / 0 extreme. A separate frozen archive evaluation scored
  42.9% / 45.7% / 42.9% against stored Planner labels, below its 60% majority baseline. Labels were not independently
  adjudicated; this is a consistency diagnostic, not a release test. Its frozen dataset, manifest, runner and raw
  results are under `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/`.
- 2026-10-15 — Collapsed that frozen archive to easy/complex: the 65.7% not-complex majority baseline was matched
  only by multilingual Laya, which had 0% complex recall. English and typed-decisions recalled every complex example
  but scored 48.6% / 51.4% overall and recalled only 21.7% / 26.1% of not-complex tasks. Derived report:
  `plan-archive-binary-summary.json`; this is not independent gold or an 85% result.
- 2026-10-15 — Evaluated a separate, frozen 25-task set from six Planner test-scenario plans that was not present in
  the prior local evaluation files. Four-class accuracy was 40% / 48% / 28% versus a 48% majority baseline; binary
  accuracy was 64% / 76% / 56% versus 76% majority, with multilingual complex recall 0%. CUDA inference had zero
  errors. Fixture labels are not independent gold; checkpoint pretraining exposure is unknown; the set lacks Spanish
  and `extreme`. It strengthens diagnosis only, not production/final-test evidence. Artifacts are under
  `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/planner-fixture-*`.
- 2026-10-15 — Prepared a blinded annotation batch of those 35 task texts with no source labels or task IDs, SHA-256
  `d8a112e8cd598845a5dde7df3ca660493dadb6dcd6ea6113370ce629b62694be`. It may seed training/dev after human review,
  but cannot serve as final test because Laya has already seen the texts. Real-plan `laya-train --dry-run` produced
  only four default optimizer updates; a 32-epoch dry-run yields 32 updates on the same small set. No training ran.
  Keep the 85% objective active; collect new, independently labelled, bilingual tasks and an untouched test set before
  any training or success claim.
- 2026-10-15 — Separately ran a disposable, label-revealing positive-control fine-tune on CUDA to verify the local
  Laya training path and A3000 resource use. It completed 144 updates in 69.432 s, sampled 2,075 MiB whole-GPU peak,
  and its offline-reloaded checkpoint reproduced 39/40 on the deliberately trivial holdout. This does not satisfy
  T3/T5/T7, does not train a Scheduler checkpoint, and does not support the 85% real-task claim. Calibration warned
  on only 16 rows and a temperature at the 0.5 clamp. Detailed source-backed protocol and raw evidence:
  `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/TRAINING-PROTOCOL.md` and `positive-control-v1/`.
- 2026-10-15 — Reviewed the other project bitacoras and built corpus v1.3: 10 projects, 33 dated logs / 113 Goal
  sections, 45 plans / 363 task lines, and 167 PENDING rows; 723 unique candidates, 34 prior-evaluated methodology
  tasks excluded, 689 unlabeled texts evaluated by the three pinned checkpoints on CUDA (0 errors). Found and
  corrected v1.1's unqualified numeric REQ exclusion, which had dropped 75 unrelated Pictures/Proposal Studio tasks.
  v1.3's 40 simulated cases now use actual project slugs across all ten workspaces, alongside 40 separate invented
  cases; both groups have 10 cases per complexity level and 20 English / 20 Spanish. The 200-task blind development
  annotation batch is balanced across plans, PENDING, logs, simulated, and invented sources.
- 2026-10-15 — v1.3 balanced synthetic exact accuracy was 26.2% / 31.2% / 25.0% (English / multilingual /
  typed-decisions) versus 25% baseline; complex recall 22.5% / 5% / 25%, extreme recall 0% for all. On 129 weak
  historical size proxies accuracy was 41.9% / 41.1% / 38.0%, below the 46.5% majority baseline. No ~85% evidence;
  do not train aggressively on these provisional labels. v1.3 has not been fine-tuned; prior group-held-out training
  maxed at 32.5% on 40 cases/fold. Report, raw predictions, hashes, resource measurements, and source manifest:
  `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/mixed-bitacora-corpus-v1.3/`; human batch:
  `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/human-review-batch-02-v1.2/`.
- 2026-10-15 — Ran a paired context diagnostic over the same 35 archived Planner tasks and pinned CUDA checkpoints.
  English accuracy changed 42.9% → 51.4% (+3 cases), multilingual 45.7% → 40.0% (-2), and typed-decisions
  stayed 42.9%; pooled gain was only 1/105 decisions. The 60% majority baseline still exceeds each result. Adding
  M1 dependencies, shared resources, and sanitized verification purposes therefore did not show a reliable lift.
  No `extreme` or Spanish cases; report and frozen scores: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/archive-context-paired-v1-report.md`.
- 2026-10-15 — Applied provisional single-assistant labels to the 200-row blind development packet only after the
  label choices were frozen without viewing model outputs or source mappings. Counts: 39 low / 56 medium / 77 high /
  28 extreme; 30 incomplete, stale, or truncated rows are flagged. The packet itself is unchanged. Exact text matching
  linked every row to predictions already produced by the v1.3 CUDA run; labels were never sent to Laya. Four-class
  accuracy was 31.5% / 29.5% / 31.0% against 38.5% majority; binary accuracy was 53.5% / 45.0% / 55.0% against
  52.5% majority. Complex recall was only 25.7% / 1.9% / 26.7%, and `extreme` recall was 0% for every checkpoint.
  Excluding the 30 flagged rows still scored 30.0% / 27.6% / 28.8%, below the 39.4% majority. Labels are one
  annotator's provisional judgment with standardized class-level reasons, not independent human gold or a locked test.
  Full report, metrics, hashes, labels and scoring script:
  `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/human-review-batch-02-v1.2/`.
- This leaves independent adjudication and a prospective, untouched test set open. Complexity is measured separately
  from scope, duration, risk, coupling, confidence, evidence, and M2 route preference/outcomes. Plan remains in
  `review`; this diagnostic does not authorize a Scheduler checkpoint, M2 routing change, or completion claim.
