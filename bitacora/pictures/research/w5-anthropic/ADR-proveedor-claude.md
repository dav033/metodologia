# ADR: Claude (Haiku) as a local-only AI provider

Status: accepted (implemented; verified by tests listed below). Date: 2026-10-14. Source research: NOTES.md in this folder.

## Problem
Production runs Gemini Flash. The owner wants the AI used inside the app to be Claude Haiku 5.5 (medium effort) **locally and only locally**, to evaluate quality and cost without touching Vercel or the VPS. The registry used to build Gemini unconditionally, so a second provider had to be added without any path that can reach it in production.

## Decision
1. **Gate.** `claudeLocalPermitido()` (src/lib/ia/claude/config.ts) is true only when `!VERCEL && NODE_ENV === "development" && IA_PROVEEDOR === "claude"` and there is an `ANTHROPIC_API_KEY` (or `IA_CLAUDE_TRANSPORTE=cli`). A process with no `NODE_ENV` is not local: scripts must set it explicitly. `configClaudeLocal()` re-checks the gate and throws a non-retryable `ErrorIA("sin_llave")` that never prints a secret.
2. **Resolver.** `proveedoresDisponibles()` and `resolverProveedor()` in src/lib/ia/nucleo/registro.ts offer `claude` only through that gate. The request-body override, the `ia_proveedor` cookie and the global setting (`meta` table, which only accepts `gemini`) choose among the available providers, so outside local they cannot reach Claude. When Claude is available it wins over client hints (a stale cookie must not silently send local AI back to Gemini). `/api/escena-ia` and the one-shot callers use `destinoGenerativo()`, which applies the same gate from the environment only.
3. **Dispatch.** `chatDe(id)` and `chatLecturaFotoDe(id)` dispatch by id; `chatDe("claude")` returns the Claude ChatPort already wrapped by `envolverChatPort` (audit rows `llamada_ia`/`respuesta_ia` with the estimated cost at Haiku prices). Python-backed paths are skipped for Claude (`usaPython`).
4. **Model and effort.** Model `claude-haiku-5-5` by default (`ANTHROPIC_CHAT_MODEL` overrides; the plan text called it `IA_LOCAL_MODELO`, the code uses `ANTHROPIC_CHAT_MODEL`). Effort from `IA_LOCAL_ESFUERZO` = low | medium | high, default medium (low with the CLI transport). Invalid values throw an error naming the variable, never the value.
5. **Transport.** Plain `fetch` to the Messages API (no new SDK) in src/lib/ia/claude/cliente.ts, exposed with the SDK shape (`messages.create/stream`) so the provider guard detects each call. Optional `cli` transport (Claude Code with the owner's subscription), local only.
6. **ChatPort.** The neutral contract (`ChatPort`, `Mensaje`, `Herramienta`) is the boundary; Anthropic specifics (thinking blocks replayed through `LlamadaHerramienta.meta`, `tool_result` pairing, image blocks) live inside src/lib/ia/claude/.

## Alternatives considered
- `@anthropic-ai/sdk`: rejected, a new dependency for a local-only provider; the guard already knows the SDK call shape.
- Choosing the provider by cookie/body in production for A/B: rejected, it is exactly the path that must not exist.
- Replacing Gemini globally: rejected, embeddings and Python paths still need Gemini.

## Consequences
- Production and Vercel behave exactly as before; Gemini requests are unchanged.
- Embeddings, the Python ai-api and image generation stay on Gemini/other providers.
- Cost telemetry for Claude is an estimate from a price table (Haiku 5.5: $0.10 in / $0.50 out per MTok, long-prompt tier above 100k tokens).

## Rollback
Unset `IA_PROVEEDOR` (or leave it as `gemini`) in `.env.local`: Claude disappears from the registry. Removing the provider means deleting src/lib/ia/claude/ and the `claude` branches in registro.ts, crear-modelo.ts and cliente-generativo.ts.

## Verification
- scripts/test/test-proveedor-local.ts: full environment matrix (VERCEL, NODE_ENV, IA_PROVEEDOR, key, transport) plus every override path refusing Claude.
- scripts/test/test-proveedor-claude-local.ts, test-chat-claude.ts, test-agente-escena-claude.ts, test-lectura-foto-claude.ts, test-generativo-claude.ts (all with a mocked transport, no network).
- scripts/test/test-guardia-proveedores-ia.ts: every `messages.create/stream` call and the Anthropic host are inventoried and wrapped.
