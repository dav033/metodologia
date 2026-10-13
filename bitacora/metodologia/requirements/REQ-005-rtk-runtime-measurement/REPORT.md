# REQ-005 — Integrate and measure RTK in the parent methodology

## Integrated

RTK 0.51.0 is installed at `~/.local/bin/rtk` through the methodology repository's `--rtk-only` path. The official x86_64 Linux MUSL archive and extracted binary both match fixed SHA-256 digests. The repo owns the pinned installer, RTK usage guidance, CLI options and reproducible command-output benchmark. No standalone skill, sudo, hook, automatic interceptor or global setting was added; RTK telemetry consent remains unset and benchmark processes explicitly opt out.

Commands:

- `python install.py --rtk-only`: install only RTK; leave methodology setup alone.
- `python install.py --with-rtk`: explicitly include RTK in full methodology setup.
- Benchmark instructions live in the root README; harness at `evals/benchmark_rtk.py`.

## Measurements

Three paired runs of six commands against the same worktree or isolated fixture. Counts tokenize combined stdout/stderr with `tiktoken` `o200k_base`; this is command output only, not model input or session billing.

| Command | Native tokens (median) | RTK tokens | Output change | Median runtime |
|---|---:|---:|---:|---:|
| `git status` | 539 | 391 | -27.5% | 4 ms → 10 ms |
| `git diff -- skill/SKILL.md` | 2,142 | 2,134 | -0.4% | 2 ms → 8 ms |
| `git log -n 20` | 2,188 | 773 | -64.7% | 2 ms → 5 ms |
| `pytest -vv`, 300 passing | 5,538 | 13 | -99.8% | 404 ms → 411 ms |
| `pytest -vv`, 300 pass / 3 fail | 5,873 | 212 | -96.4% | 423 ms → 422 ms |
| `pytest -q`, same 3 failures | 320 | 212 | -33.8% | 406 ms → 402 ms |

Codes matched on all 36 command runs. All three failure names and exact diagnostic markers appeared in all 12 failing-command outputs; totals were retained in RTK output. Recalling the full 5,770-token failed-test log required no pytest re-execution, but raised combined RTK + recall output from 212 to 5,982 tokens (1.9% more than native). Therefore retrieve a narrow saved excerpt when possible; if the entire log is needed, RTK may save nothing. RTK's additional process time was measurable on Git commands, but negligible relative to the test workload in this sample.

The result supports selective use on noisy tests and history. It shows little value on a small focused diff or an already quiet command. It does not establish fewer total session tokens, universal savings or lower cost.

## Verification and evidence

- PASS: methodology CLI `--rtk-only` recognized the exact installed binary; no global setup ran.
- PASS: focused installer tests 9/9, covering fixed checksums, extraction, idempotence, preservation of existing files/symlinks, unsupported architecture and CLI scope.
- PASS: benchmark 18/18 command pairs (36 runs), expected statuses, diagnostics and recovery-without-rerun invariants.
- PASS: scoped `git diff --check` and Python compilation.
- NOT RUN: broader existing suite; benchmark utility is already exercised end to end; no RTK hooks or user projects were changed/run.
- APPROVE: independent standards review, including one addressed atomic-publication finding and successful re-review. Spec review of the strengthened recovery/status and binary-identity checks is pending.

[Raw metrics, outputs, fixture, installer evidence and SHA metadata](../../artifacts/metodologia-rtk-2026-10-12/).
