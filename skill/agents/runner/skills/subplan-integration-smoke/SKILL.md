---
name: subplan-integration-smoke
description: Execute a previously approved, bounded real-entrypoint smoke scenario on a named subplan or integration candidate; report contract-boundary evidence without deployment, repair or autonomous acceptance.
---

# Subplan integration smoke — Runner private skill

## Trigger
Load only when the brief includes a smoke/integration verification for an approved `subplan_id@revision` or candidate composition and a bounded scenario. **This skill does not define the test, approve promotion, deploy, or launch a service without authorization.**

## Preconditions
- Identify `subplan_id`, revision, `base_sha`, candidate composition digest/ref (when relevant), verification ID and the exact Planner/M6-approved workflow.
- Require entrypoint commands, permitted target/CWD, startup/cleanup rules, health/readiness criteria, ports, timeout and expected contract result. The executor supplies isolation and permitted side effects.
- Require explicit authorization for network, external staging and production checks. Treat credentials by variable **names** and safe references only; never inspect or print values. Production checks are read-only unless a higher privilege policy explicitly permits a particular isolated operation; Runner never makes that privilege decision.
- If absent, return `STATUS: BLOCKED` plus missing prerequisite. No invented test endpoints or inferred credentials.

## Procedure
1. **Bind composition:** Confirm the intended snapshot/composed build, including versions for producers and consumers. Never run on the current random branch or silently substitute an older snapshot.
2. **Select the approved smoke:** One or a few critical journeys with observable expected behavior. The scenario must traverse actual shipped entrypoints (HTTP server, CLI, worker, events/queue as applicable) rather than merely import modules or ping an unrelated health route.
3. **Classify boundaries:** Do not mock the **interface whose integration is under test**. External third-party dependencies may use explicitly approved local fixtures, but label this as simulated and not production evidence.
4. **Start only approved processes:** Run entrypoints in the assigned isolation using declared command/timeouts; observe readiness. Never install tools, seed production, run migrations, deploy, change shared network/ports or mutate Git state on your own.
5. **Execute scenario:** Capture request/response shape, outputs or event correlation that directly proves the contract. Use approved Playwright suite if the scenario is browser-based; collect trace/screenshot only if configured and store via executor's permitted artifacts.
6. **Stop and clean up safely:** Terminate **only** processes started by this check under executor authority; do not kill other users' servers, delete unknown paths or alter application files. Record cleanup failure as limitation.
7. **Report evidence:** Include per-entrypoint startup, scenario checks, exit status, `path:line`/request trace, environment class, candidate digest, executed vs missing checks, and any block. PASS means the **executed smoke** succeeded, not that the subplan is accepted. M6 adjudicates.

## Status and follow-up
`STATUS: PASS | FAIL | BLOCKED` remains the old Runner enum. Optional `NOTES.reason_code`: `BLOCKED_EXTERNAL`, `BLOCKED_ENV`, `FAIL_CODE`, `TIMEOUT`, `NOT_RUN`, `FLAKY_SUSPECTED` (details only). Never retry, roll back production, redeploy, widen network, select another provider, or schedule another task. M5/M6 handle those decisions.

## Public techniques, never imported as authority
- Existing browser smoke: [magnus919 Playwright](https://github.com/magnus919/agent-skills/blob/main/playwright/SKILL.md) (MIT), read-only tool operation and bounded evidence.
- Smoke-scenario selection and local-vs-production separation: [j4flmao quality-smoke-testing](https://github.com/j4flmao/agent-skills/blob/main/skills/quality/smoke-testing/SKILL.md) (MIT); **exclude** its automatic rollback/deploy, unilateral gate decisions, test creation, CI changes, and hardcoded time/test-count policy. M6 controls thresholds.
See `../../references/public-testing-techniques.md`.

## Test examples
- `S1@v2 + S2@v1`: start real app and verify producer-consumer flow; no reuse of `S1@v1 + S2@v1` success as if equivalent.
- UI preview built by Designer: do not call a preview successful production E2E; operate on actual implementation when so requested.
- Local test passes, production secret missing: record local PASS separately and production `BLOCKED`, never collapse into universal PASS.
