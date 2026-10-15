---
id: REQ-903
title: Decoration assistant first response latency
status: review
---

# REQ-903 — Decoration assistant: first response feels slow

## Goal

In the Pictures project (`pictures`, Next.js app plus `services/ai-api` FastAPI), the guided decoration assistant's
first response feels slow and nobody knows where the time goes. Find out where it goes with measurements, then
reduce the time to the first useful response noticeably, without changing answer quality and with the behaviour
covered by tests.

## Measurement

What exists today (read in the repository, not guessed):

- The guided turn is `POST /api/asistente-guiado` (`src/app/api/asistente-guiado/route.ts`). It reads the customer's
  facts with rules, then streams one model conversation through `ejecutarConversacionStream`
  (`packages/agente-core/src/ejecutar.ts`) with up to 8 rounds; text only reaches the customer in the round that ends
  without tool calls, and the SSE filter (`FiltroFlujoGuiado`) releases whole sentences only.
- `PROMPT_GUIADO` (`src/lib/ia/guiado/prompt-guiado.ts`) tells the model to call `guardar_brief_guiado` and then
  `buscar_decoraciones_sempertex` once event and theme are known, so a complete first message can cost three
  sequential model rounds. This is a hypothesis until T2 measures it.
- The model call goes direct to Gemini or, with `CHAT_PYTHON_ENABLED=true`, through `services/ai-api`
  (`app/omoikane/turno_stream.py`), which builds a new `genai.Client` per turn. Which path and which
  `GEMINI_CHAT_THINKING_LEVEL` production uses is not visible in the repository (`.env.example` sets the flag false and
  does not mention the level).
- Per-model-round `ms` and `vuelta` already go to telemetry (`ejecutar.ts`), and the audit log
  (`src/lib/registro/tipos.ts`) records `respuesta_ia`, `herramienta` and `python` events with `ms` and the request
  id; `npm run registros` reads them locally and from the VPS. The local `data/registros` holds no assistant turn
  today, so a baseline must be generated, not looked up.
- Time to first streamed token is NOT recorded anywhere; the harness (T1) measures it from the client side of the
  SSE stream.

Measurement scenarios (same for baseline and final): a complete first message (event and theme given), a vague
opener, and a one-piece direct request. At least 10 runs per scenario. Report p50 and p95 per stage.

## Quality

"Answer quality unchanged" is made checkable in two layers, never by asserting exact model wording:

1. Deterministic: a scripted-model test pins the tool trace, the sanitised reply invariants and the `fin` payload
   shape of the first turn (T4). It runs without network or paid provider.
2. Probabilistic: the existing `scripts/eval/eval-chat-thinking.ts` precedent (tool trace and structural invariants
   against the real prompt) is the reference if the chosen lever touches model parameters or prompt text.

## Decision rule

T3 chooses ONE primary lever from the stage that dominates the measured time to first useful response. Candidate
levers visible in the code today, none chosen in advance: (a) production default of the thinking level, (b) fewer
sequential model rounds for a complete first message, (c) reuse of the provider client and connection on the Python
path, (d) system prompt size, (e) sentence-level buffering of the SSE filter. A lever whose stage is not measurably
significant is rejected with its number. The budget is strictly below the measured p50 and the stage p95 comparison carries an explicit tolerance from the baseline spread; the budget is set from the measured p50, as `AGENTS.md` requires, not
invented.

## Constraints

- The repository `pictures` is edited only by plan tasks that name their files; `AGENTS.md` rules apply (measured
  performance changes, no `any`, no weakened tests, fast tests independent of paid providers).
- Real Gemini calls (baseline and final measurement) are paid and external; reading VPS logs over SSH is
  external too. Both need the owner's go-ahead at approval time; nothing else in the plan needs it.
- Live-call tasks T2 and T6 depend on available Gemini quota and a local dev server. Their machine-checkable outputs are
  `eval/latencia-asistente/baseline.json` and `after.json`; T3's is `eval/latencia-asistente/decision.json`. They live in the tracked `eval/` folder (`/data/*` is gitignored) so they are committed with the work and survive worktree isolation. The T1 harness checkers
  (`summary-check`, `decision-check`, `budget-check`) fail when a file does not meet its rule.
- No `git push`, no merge to `main`, no file deletion. Findings and the decision are recorded in the bitácora, not
  as new documents in the repository.

## Out of scope

Real-browser rendering time (React paint, network from the customer's device) is not measured by this plan; only
the server and the SSE stream are. Proposals found on the way become numbered items in the final report.

## Acceptance

- A table of measured per-stage p50/p95 exists and names where the time goes.
- A recorded decision links the chosen lever to those numbers and sets the budget.
- The final measurement (T6, not T5) meets the budget at p50 with the same scenarios and harness.
- The existing guided, agent-core and Python suites plus the new first-turn test pass.
