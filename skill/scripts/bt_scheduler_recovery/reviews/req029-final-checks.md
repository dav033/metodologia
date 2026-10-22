# REQ-029 — final checks (2026-10-22, run by the coordinator directly, outside the scheduler)

Tree: branch `feat/req029-direct` (merged to `main`), integrated accepted work tip `d877540f` + REQ-030 + the fixes of this session.

| Command | Result |
|---|---|
| `cd skill/scripts && python3 -m unittest discover -s tests` | 1972 tests; the only 2 failures (a source-text assertion about the token check, changed to a constant-time compare) were fixed and `tests.test_recovery_views` re-run: 15 OK. Every other test OK (6 skipped). |
| `... discover -s bt_scheduler_core/tests` | 291 OK |
| `... discover -s bt_scheduler_recovery/tests` | 52 OK |
| `... discover -s bt_planner/tests` | 297 OK |
| `... discover -s bt_scheduler_quality/tests` | 141 OK |
| `... discover -s bt_scheduler_executor/tests` | 293 OK |
| `python3 -m unittest discover -s tests/migration -p test_package_install.py` | 21 OK (installed wheel imports every recovery module, including `bt_recovery_preview`) |
| `... -p test_recovery_supervision_e2e.py` | 2 OK: real `scheduler-watch`/owner creates the run; `scheduler-op recovery-preview` as a subprocess leaves every run file unchanged; the real `serve` process refuses foreign Host names, oversized bodies and tokenless posts, and each control (heal stop/start, recovery enable bound to preview digest + stop generation, stop) leaves its effect on disk |
| `... -p test_recovery_req027_preview.py` | 6 OK: REQ-027 T18 ledgers (17, 23, 32 findings): Caddy fixed, E2E persistent, build typecheck and OAuth new; weak matches uncertain; no write, no model |

Not demonstrated here (see `req029-final-audit.md`): execution of the run to the end through the real owner/executor/verifier (the fake
provider is not routable without the M2 stores of the live machine), and automatic structural convergence (R12/R13/R16).
