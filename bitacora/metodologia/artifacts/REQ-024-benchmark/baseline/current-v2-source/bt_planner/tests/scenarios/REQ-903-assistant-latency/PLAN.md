---
id: REQ-903
title: Decoration assistant first response latency
status: approved
revision: 1
---

# Plan — Decoration assistant first response latency

Investigation with an unknown outcome: M1 measures and decides, M2 acts on the decision. Tasks after T3 stay
`confidence: low` until the measurement exists.

Machine-checkable outputs (tracked files under `eval/latencia-asistente/`, committed with the work because `/data/*` is gitignored): T2 writes `baseline.json`,
T3 writes `decision.json`, T6 writes `after.json`; the checkers are subcommands of the T1 harness. T2 and T6 make live,
paid Gemini calls and need available quota and a running local dev server. The `files:` list of T5 is the candidate set
of files the lever may touch, to be narrowed by T3's decision, not a prediction. T4 runs after T2 so the baseline is measured on the unmodified route. The budget is strictly below the baseline p50 and stage p95
comparison uses an explicit tolerance recorded in `decision.json`; T5 does not assert the speed-up, only T6 does.

### M1 — Measure where the first response time goes

- [ ] T1 — Build the first-turn latency harness · repo: pictures · files: scripts/eval/medir-latencia-asistente.ts, scripts/test/test-medir-latencia-asistente.ts, package.json · resources: package.json-scripts · verify: `npx tsx scripts/test/test-medir-latencia-asistente.ts`
- [ ] T2 — Measure the baseline first-turn latency by stage · repo: pictures · after: T1 · files: eval/latencia-asistente/baseline.json · resources: gemini-api-quota, local-next-dev-server · verify: `npx tsx scripts/eval/medir-latencia-asistente.ts summary-check eval/latencia-asistente/baseline.json --min-runs 10`
- [ ] T3 — Choose the reduction lever and budget from the baseline · repo: pictures · after: T2 · files: eval/latencia-asistente/decision.json · verify: `npx tsx scripts/eval/medir-latencia-asistente.ts decision-check eval/latencia-asistente/decision.json --baseline eval/latencia-asistente/baseline.json`

### M2 — Reduce the latency with behaviour pinned

- [ ] T4 — Pin the first-turn behaviour with a scripted model · repo: pictures · after: T2 · files: scripts/test/test-turno-inicial-guiado.ts, src/app/api/asistente-guiado/route.ts, package.json · resources: asistente-guiado-route, package.json-scripts, local-next-dev-server · verify: `npx tsx --conditions=react-server scripts/test/test-turno-inicial-guiado.ts`
- [ ] T5 — Apply the chosen latency reduction · repo: pictures · after: T3, T4 · files: src/app/api/asistente-guiado/route.ts, packages/agente-core/src/ejecutar.ts, src/lib/ia/nucleo/registro.ts, src/lib/ia/omoikane/chat-python.ts, services/ai-api/app/omoikane/turno_stream.py, services/ai-api/tests/test_omoikane_turno_stream.py · resources: asistente-guiado-route, chat-sse-contract · verify: `npm run guiada:test`
- [ ] T6 — Re-measure and confirm the gain with quality intact · repo: pictures · after: T5 · files: eval/latencia-asistente/after.json · resources: gemini-api-quota, local-next-dev-server · verify: `npx tsx scripts/eval/medir-latencia-asistente.ts budget-check eval/latencia-asistente/after.json --decision eval/latencia-asistente/decision.json --baseline eval/latencia-asistente/baseline.json`
