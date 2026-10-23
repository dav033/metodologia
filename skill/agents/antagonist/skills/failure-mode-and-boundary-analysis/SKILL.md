---
name: failure-mode-and-boundary-analysis
description: Examine high-risk partial failure, concurrency, retry, timeout, data-integrity and trust-boundary scenarios using evidence-backed adversarial analysis.
---

# Failure-mode and boundary analysis — Antagonist private skill

## Trigger
Select for work involving auth, secrets, money, migrations, distributed state, background jobs, external APIs, high-concurrency paths, production criticality or an explicit high-risk brief. Use structured threat-modeling/premortem techniques only in that scope.

## Procedure
1. Inventory trusted/untrusted inputs, privilege transitions, persistence and side-effect boundaries touched by the diff.
2. Construct a small threat/failure matrix: `boundary`, `asset/invariant`, `trigger`, `existing control`, `plausible failure`, `verified evidence`, `severity`, `rollback/detection`.
3. Challenge execution order, retry+idempotency, cancellation, duplicate delivery, stale cache, network partitions, partial commit, delayed cleanup and failure recovery according to actual design.
4. For auth/permission/data exfiltration, apply STRIDE categories only where they improve coverage; avoid generic threat catalogs without code paths. Never attempt intrusive exploits on production.
5. Check mitigations already in code. Report only evidence-backed risks with paths/lines and a bounded remediation; explicitly classify hypothetical scenarios as unverified and do not promote them to blocking findings.

## Output and limits
Respect one-pass, no delegation, no writes, max eight meaningful findings. The final gate and rework decision are external to this skill. Do not acquire network or prod access solely to test a theory.
