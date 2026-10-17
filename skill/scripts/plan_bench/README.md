# Planner benchmark store

`plan_bench` validates the frozen REQ-024 benchmark records and produces descriptive observed/judged reports. It does
not launch providers, execute generated plans, score model quality automatically, or select a model/account.

## Boundary and public API

- `validate_manifest(value)` validates the v1.1.0 frozen design and returns the parsed mapping.
- `verify_store(path, reviews=False)` verifies the manifest digest first, then pinned input/oracle/retrospective
  bytes, scheduled cells and (when requested) blind reviews.
- `score_store(path)` summarizes recorded O1–O9 observations and computes O10 stability without filling missing data.
- `build_report(path)` separates observed and judged evidence and applies the per-metric directional guard.
- `load_rubric()` returns the packaged rubric only when its pinned SHA-256 matches.
- `parse_check_output(bytes_or_text)` validates `bt_planner check --json`; `parse_quality_report(bytes_or_text)` validates
  the full PLAN.json 1.2.0 `bt_planner report` JSON, including `coverage`, `interfaces`, `verification_categories` and
  `criteria_without_command` for downstream metric extraction.
- JSON input is size-bounded and workspace snapshots are hash-verified from the directory passed by the caller. The
  package uses only the Python standard library and itself; it does not access environment variables, network, provider
  CLIs, other methodology modules or home paths.

## Store layout

The caller supplies a store containing `manifest.json` and `manifest.sha256`. Case input/oracle files and retrospective
outputs are copied into that store and named by relative POSIX paths in the frozen manifest. Every included case also
pins `workspaces/<case>/source.tar` in `input_files`; its SHA-256 must equal `repository_sha256`, so the repository view
used for a run is retained and hash-verified with the corpus. Verification inspects the archive without extracting it
and rejects path traversal, duplicate entries, links, special files, environment files, `bitacora` content and Planner
scenario fixtures. Environment templates ending in `.example`, `.sample` or `.template` are allowed.
Large snapshot hashes are streamed; the 8 MiB JSON limit does not cap repository archives. Each planned cell is
`runs/<case>/<arm>/<replicate>/` with `meta.json`; each frozen arm pins its configured profile, runtime ID and runtime
version, and every cell must repeat those values. This records whether both arms used the same configured profile and
CLI version without storing credential material or local configuration paths. Completed cells also contain
`PLAN.md`, `PLAN.json`, and `observed.json`. A missing cell after the first recorded cell is an error; remaining work must be recorded with
`status: incomplete`, never inferred as zero. Each observed metric O1–O9 stores its value/status/unit, exact source
command, a relative source-output path and that output's SHA-256. O10 is derived by `score` and records per-metric
ranges plus per-requirement coverage agreement.

Blind reviews live at `reviews/<blind-output-id>/<reviewer-id>.json`. The private `review-map.private.json` maps each
completed output to its blind ID; reviewers receive only the blinded artifacts. Each numeric score is 0–3 and requires
a quoted artifact location. J5 keeps oracle detections itemized yes/no and new risks evidence-backed; J8 keeps review
findings categorical. Review identity and model are pinned by the frozen manifest before scoring.
The two reviewer records must use distinct reviewer IDs, profiles, and model IDs. Identity strings must not have
surrounding whitespace; two labels for the same runtime do not count as independent reviewers.

The only files written by this package's CLI are `observed-summary.json` (`score`) and `report.json` (`report`) at the
store root. `verify` is read-only. Writes replace these two generated reports atomically; input evidence and the frozen
manifest are never modified.

## Commands

```sh
python3 skill/scripts/bt_plan_bench.py rubric
python3 skill/scripts/bt_plan_bench.py verify <store>
python3 skill/scripts/bt_plan_bench.py score <store>
python3 skill/scripts/bt_plan_bench.py verify <store> --reviews
python3 skill/scripts/bt_plan_bench.py report <store>
```

`verify` checks `manifest.sha256` before reading any cell, then validates cell identities, controls, plan hashes and
metric provenance; `--reviews` adds blind review completeness and rubric checks last. `report` emits no cross-metric
score or overall-superiority claim. A per-metric descriptive direction is reported only with at least four complete
cases, a better B median in at least four, no B run worse than A's worst run in any complete case, and reviewer agreement
for judged metrics. Three repetitions remain descriptive, not causal. Retrospectives never enter directional claims.

## Stable errors

The CLI reports `MANIFEST_HASH_MISMATCH`, `MANIFEST_INVALID`, `RUBRIC_HASH_MISMATCH`, `CELL_MISSING`,
`CELL_CONTROL_MISMATCH`, `CELL_OUTPUT_HASH_MISMATCH`, `METRIC_SOURCE_MISSING`, `REVIEW_INVALID`,
`OBSERVED_MISSING`, `REPORT_AGGREGATE_REFUSED`, and `WORKSPACE_ARCHIVE_INVALID` with exit status 2. Other `BenchmarkError` codes are similarly
stable and identify the first failed verification phase.
