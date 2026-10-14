# METH-5 — The methodology suite waits on a real `zellij` call

The full methodology suite takes about 100 s and prints `Command 'zellij' timed out after 10 seconds` while the relay
tests run. `tests/test_relay.py` alone takes 7 s, so the wait is not in that file in isolation. Find the cause and, if it
is a test touching the host terminal multiplexer, make the suite independent of it.

## Requirements
- R1. The cause is identified with evidence (which test, which call, why 10 s).
- R2. If it is host dependence, the suite passes with no `zellij` on PATH and with one present.
- R3. Production relay behaviour does not change.
