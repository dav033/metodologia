# REQ-029 final audit (2026-10-22)

Two independent read-only reviews of the integrated tree (a spec-axis reviewer over R1-R16 and an adversarial reviewer over the new
control surface), with probes run in temporary directories. The coordinator who implemented the work did not write the verdicts; he
fixed what they reproduced and re-ran the suites (`req029-final-checks.md`). Ledger: `req029-final-audit.findings.json`.

**Verdict: CHANGES_NEEDED for the autonomous structural recovery; the supervision, evidence, control and hardening parts are done.**

- Satisfied or fixed: R11 (full conflict evidence published before clipping, from both sources), R8 coverage (a command covers a surface only
  if it runs something over it), R6/R14 for ordinary stops (self-healing, bounded, idempotent, recorded), R7 for the plan page and the
  feed, R15's stop fence (the operator's stop always wins), F3-F4, F6-F8, F12-F13, F15, F21 of the first audit, and A1-A10 of the adversarial review.
- Open, with their exact blocker: G1/G2 (R3, R4, R12, R13, R16) — a model-authored diagnosis step and a redesign of three contracts
  are needed before an autonomous convergence can close; G3-G6 are consequences of it.
- Withdrawn: R9.
