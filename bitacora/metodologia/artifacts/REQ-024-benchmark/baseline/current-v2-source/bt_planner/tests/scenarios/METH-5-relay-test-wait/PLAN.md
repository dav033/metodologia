---
status: approved
---
# Plan — METH-5

### M1 — Find the cause
- [ ] T1 — Identify which test calls the real multiplexer and why it blocks · repo: metodologia · files: skill/scripts/bt_relay_launch.py, skill/scripts/bt_relay_client.py, skill/scripts/tests/test_relay.py

### M2 — Remove the host dependence
- [ ] T2 — Isolate the offending test from the host multiplexer · repo: metodologia · after: T1 · files: skill/scripts/tests/test_relay.py · verify: `python3 -m unittest tests.test_relay` · resources: relay-test-fixtures
- [ ] T3 — Prove the suite is independent of the host terminal · repo: metodologia · after: T2 · verify: `python3 -m unittest discover -s tests`
