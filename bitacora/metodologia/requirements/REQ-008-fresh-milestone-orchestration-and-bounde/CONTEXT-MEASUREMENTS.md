# REQ-008 — Context baseline

Measured 37 stored `prompt*.txt` files under `~/bitacora/.state/runs/` using filesystem size metadata, without copying their private contents.

| Measurement | Bytes |
|---|---:|
| Minimum prompt | 1,708 |
| Median prompt | 9,019 |
| p90 prompt | 11,191 |
| p95 prompt | 12,119 |
| Maximum prompt | 12,931 |
| All prompts | 314,832 |
| REQ-008 SPEC at measurement | 8,023 |
| REQ-008 PLAN at measurement | 5,802 |
| Full SKILL body/file | 12,904 |

SPEC + PLAN + SKILL alone total 26,729 bytes before task prompts, repository instructions, conversation turns or tools. These are entry-size measurements, not model context occupancy or token counts. They do not justify a model capacity, a turn limit, or a reserve on their own.

The current Codex text invocation reports only closing token totals. Claude's driver currently reads usage from its terminal result. The supervisor does not currently prevent oversized tool results before the model receives them. A runtime implementation must establish an enforceable boundary; posthoc log accounting alone cannot prove the requirement.

Baseline regression command: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v`. Result: 639 tests, OK, exit 0, 60.589 seconds; log `/tmp/req008-baseline-tests.log`. Discovery excluded the newly created T1 tests. No live providers invoked. No repository lint command/configuration found by the runner.
