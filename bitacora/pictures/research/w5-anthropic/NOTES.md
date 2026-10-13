# W5 — Local-only Anthropic Claude provider (Haiku) for demo-decoracion

Date of research: 2026-10-09.
**Repo of record: `C:/Users/davidt/Downloads/e6f` (origin/main b4433bc9).** The older checkout `C:/Users/davidt/Downloads/pictures-workspace/demo-decoracion` was read first and is stale (missing recent audit wrappers and tools). Its line numbers are noted where they differ.
Scope: research only. No project code was edited. No .env file was opened; no secret was printed.

Sources used (primary): platform.claude.com docs fetched on 2026-10-09 (URLs in §8). Repo files cited with paths.

---

## 0. Repo facts that shape the design (verified on e6f)

| Fact | Where (e6f) |
|---|---|
| Only LLM SDK in deps: `@google/genai ^2.16.0`. No `@anthropic-ai/sdk`. Zod is used (`z.toJSONSchema` = Zod 4 API). | `package.json` L224 |
| `proveedoresDisponibles()` returns `["gemini"]` iff `GEMINI_API_KEY` is set. `resolverProveedor` precedence: body override > cookie > global meta > `IA_PROVEEDOR` > first available. Override and cookie come from the client. `obtenerAjusteGlobal` accepts only `"gemini"`. | `src/lib/ia/nucleo/registro.ts` L14-51 |
| **`chatDe(id, proposito)` and `chatLecturaFotoDe(id)` ignore `id` (`void id;`) and always build Gemini.** Adding Claude requires changing these dispatchers. | `registro.ts` L77-92 |
| `/api/escena-ia` bypasses the registry: it calls `getGeminiClient("escena_ia")` (L124) and `cliente.models.generateContent` (L182) in a manual loop (max 12 steps, 40 calls). It also streams NDJSON via `responderEnFlujo` (L109; `src/lib/globos3d/flujo-escena-ia.ts`). | `src/app/api/escena-ia/route.ts` |
| Scene loop uses `thinkingConfig: LOW`, and `FunctionCallingConfigMode.ANY` with `allowedFunctionNames: [MODELAR_DESDE_FOTO, PREGUNTAR_USUARIO]` on step 0 when a photo is attached. | same, L183-185 |
| Cost estimate is in helper `costeUsd(...)` (called L253) with Gemini Flash prices (`* 0.5` input, `* 3` output+thinking). Must be replaced for Claude. | same L93, L253 |
| Tool declarations: `DECLARACIONES_ESCENA` (L363-368) builds `parametersJsonSchema` as `paraGoogleSchema(z.toJSONSchema(schema, {target:"draft-7"}))`. The Gemini transform is applied at build time, so the raw zod JSON Schema is not exported. | `src/lib/globos3d/herramientas-escena.ts` |
| Refine reporte schema also uses `paraGoogleSchema` (moved on e6f). | `src/lib/globos3d/refinado/ronda-servidor.ts` L65 |
| `paraGoogleSchema` strips `$schema`, `additionalProperties`, `exclusiveMinimum/Maximum`, and converts const-unions to `enum`. These are Gemini-API limits, not Anthropic limits. | `src/lib/ia/nucleo/esquema-google.ts` |
| Neutral chat contract `ChatPort { id, modelo, thinkingLevel?, turno(PeticionChat), turnoStream(PeticionChat) }`. `PeticionChat { sistema, historial: Mensaje[], herramientas: Herramienta[{nombre, descripcion, esquema}], temperatura?, maxTokens?, signal? }`. `Mensaje` = usuario(texto, imagenes[base64,mime,id?,descripcion?]) / asistente(texto) / asistente(llamadas[{id?, nombre, args, meta?}]) / herramienta(nombre, llamadaId?, resultado). `FragmentoChat` = texto delta \| fin(TurnoChat). `ProveedorId = "gemini" \| "fal"` (L1). | `packages/agente-core/src/tipos.ts` |
| The Gemini adapter carries Gemini's `thoughtSignature` through `LlamadaHerramienta.meta`, so the neutral type already supports per-provider replay metadata. | `packages/agente-core/src/gemini/chat.ts` |
| Audit wrappers: `envolverChatPort` (ChatPort level), `auditarLlamadaIa` / `iniciarLlamadaIa` (generic), `extraerRespuestaGemini` (raw response extractor), `crearFetchAuditado` (http/python bodies), `envolverRegistroHerramientas`. Images are hashed with `huellaBase64`. | `src/lib/registro/envoltorios.ts` |
| Guard test inventories raw SDK/host/process calls. Detectors include `from "@anthropic-ai/sdk"` (`sdk-otro-proveedor`, L94) and `api.anthropic.com` (`host-proveedor-ia`, L95). **A Claude adapter will fail the guard until it is inventoried and wrapped.** There is no detector for `.messages.create(` / `.messages.stream(`, so an unwrapped Claude call would pass silently. | `scripts/test/test-guardia-proveedores-ia.ts` |
| Photo prep normalizes to JPEG q85 with a `lado` limit (`LADO_MAXIMO_FOTO`, value not read). Vision part is `inlineData` base64 `image/jpeg`. | `src/lib/taller/normalizar-foto.ts`; `src/lib/globos3d/escena-ia-foto.ts` |
| Embeddings (`gemini-embedding-2`) for RAG and photo search. Anthropic has no embeddings API in this research, so those stay on Gemini. | `src/lib/rag/embeddings.ts`; `src/lib/taller/indice.ts` |

---

## 1. Models, pricing, limits

**Model ID: `claude-haiku-5-5`** (exists; latest Haiku; released 2026-10-07, i.e. two days before today).
- Model page: https://platform.claude.com/docs/en/models/haiku-5-5/overview — "Model ID: `claude-haiku-5-5`"; "Context window: 1M tokens · Max output: 128K tokens · Input pricing: From $0.10 / MTok · Output pricing: From $0.50 / MTok"; "Released October 7, 2026"; retirement not sooner than October 7, 2027. Input: text and images. Output: text.
- The ID is fixed with no date suffix and no separate alias (migration guide: https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide).
- Lineup (models overview: https://platform.claude.com/docs/en/models/overview): Fable 5.1 `claude-fable-5-1` ($10/$50), Opus 5.5 `claude-opus-5-5` ($4/$20), Sonnet 5.5 `claude-sonnet-5-5` ($2/$10), Haiku 5.5 `claude-haiku-5-5` ($0.10/$0.50).
- Previous Haiku: `claude-haiku-4-5` / `claude-haiku-4-5-20251001`, $1 / $5 per MTok. Per token it costs more than 5.5, though 5.5's tokenizer uses about 30% more tokens for the same text (§1.3).

**Pricing, Haiku 5.5 (USD per MTok), prompts up to 100,000 tokens:**
- Base input $0.10; 5-minute cache write $0.125; 1-hour cache write $0.20; cache read $0.01; output $0.50. Batch API is 50% off (not useful here).
- Prompts **over 100,000 tokens**: input $0.50; cache write 5m $0.625, 1h $1; cache read $0.05; output $2.50.
- Sources: https://platform.claude.com/docs/en/models/haiku-5-5/overview (Pricing table) and https://platform.claude.com/docs/en/about-claude/pricing (full table, read partially).
- Thinking tokens bill as output tokens (https://platform.claude.com/docs/en/build-with-claude/thinking).
- Versus the Gemini estimate in code (US$0.50 in / US$3 out): Haiku 5.5 input is 5x cheaper and output 6x cheaper.

**Limits:** context 1M tokens; max output 128K tokens synchronous (300K on Batch API with beta header). Minimum cacheable prompt 512 tokens.

**Tokenizer:** the same text is about 30% more tokens on Haiku 5.5 than on Haiku 4.5. Recount budgets and `max_tokens`.

### 1.3 Haiku 5.5 request constraints (migration guide)
- `temperature` must be `1` or omitted. `top_p` must be `0.99` or omitted. `top_k` is rejected. `temperature` and `top_p` together is a 400. The adapter must drop any temperature.
- Assistant prefill as the last turn is rejected with 400. `messages` must end with a user turn.
- `thinking: {type:"enabled", budget_tokens}` is a 400. Use `{type:"adaptive"}` or omit `thinking`.
- Adaptive thinking is **on by default**. Default `display` is omitted (empty `thinking` text, only `signature`); `display:"summarized"` returns a summary.
- `stop_reason: "refusal"` can occur (safety classifiers; no server fallback). Handle it.
- Thinking blocks are account-bound: they work only in the account that produced them.
- Earlier-turn immutability: a request that changes `system`, `tools` or earlier `messages` while sending thinking blocks returns 400 (accounts created after 2026-08-31). Keep conversations append-only.
- Priority Tier is not supported on Haiku 5.5.

---

## 2. Effort and thinking (`IA_LOCAL_ESFUERZO=low|medium|high`)

- Request field: `output_config: { effort: "low" | "medium" | "high" | "xhigh" | "max" }`. Haiku 5.5 supports all five; default `medium` (https://platform.claude.com/docs/en/build-with-claude/effort).
- **There is no thinking budget on Haiku 5.5.** Effort is the only depth control. Migration mapping (https://platform.claude.com/docs/en/build-with-claude/extended-thinking): "remove `budget_tokens`, set `thinking: {type:"adaptive"}`, and control reasoning depth with `output_config: {effort: ...}`".
- **Mapping:** `IA_LOCAL_ESFUERZO` → `output_config.effort` verbatim (`low`, `medium`, `high` are valid). Optional `IA_LOCAL_PENSAMIENTO=off` → `thinking:{type:"disabled"}`, allowed at `high` or lower (400 at `xhigh`/`max`).
- Docs guidance: `low` suits chat, short tool tasks and high-volume simple requests. "In long agent prompts, the model is more likely to skip a search, stop early, or skip a check at `low`." Use `high` for longer agent tasks and strict instruction following.
- Gemini equivalents in repo: `ThinkingLevel.LOW` in the scene route, and `GEMINI_CHAT_THINKING_LEVEL=low` (chosen by `scripts/eval/eval-chat-thinking.ts`, 7 dialogues). Anthropic `low` is the closest analogue, not identical. Re-run the same eval before choosing a default.
- **Forced tool choice skips thinking.** `tool_choice` `any`/`tool` is accepted on Haiku 5.5, but the response starts with the tool call and has no thinking block (https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools). This matters for the photo step 0 (Gemini `mode: ANY`).
- **Thinking replay (required):** within a tool-use turn, pass every `thinking` block back unmodified, alongside its `tool_use` (https://platform.claude.com/docs/en/build-with-claude/thinking, "Preserving thinking blocks"). Store the assistant turn's `content` array verbatim. This is the analogue of the existing `thoughtSignature` handling.
- Thinking blocks from earlier turns stay in context and count as input tokens on Haiku 5.5. Over a 12-step scene loop this grows the prompt. Measure; consider `thinking: disabled` for the scene loop if the cost is too high.

---

## 3. Tool use vs Gemini functionDeclarations

**Shape mapping** (Gemini → Anthropic):
- `functionDeclarations[].name / description / parametersJsonSchema` → `tools[].name / description / input_schema`. Name regex `^[a-zA-Z0-9_-]{1,128}$` (define-tools page). Check repo tool names against it.
- `input_schema` is JSON Schema. The Gemini OpenAPI subset (uppercase `"STRING"`, `nullable`) does not apply; the repo already emits lowercase JSON Schema via `paraGoogleSchema`. **Recommendation: export the raw `z.toJSONSchema(..., {target:"draft-7"})` for Anthropic** and strip only top-level `$schema`. (`paraGoogleSchema` drops `exclusiveMinimum`, which the Anthropic non-strict path likely accepts; unverified.)
- `functionCall` → `tool_use` (`id`, `name`, `input`). Anthropic always returns `id`; Gemini sometimes omits it.
- `functionResponse` → `tool_result` (`tool_use_id`, `content` string or array, `is_error`). Put `JSON.stringify(response)` in `content`, set `is_error: !ok` (handle-tool-calls page).
- Ordering: all `tool_result` blocks of one assistant turn go in the **next user message, before any text block**. Text first is a 400 (handle-tool-calls page, Note).

**Strict mode (`strict: true`) — do not use for the scene tools:**
- Limits: max **20 strict tools per request**; max **24 optional parameters** across all strict tools and JSON output schemas; max 16 union-type parameters. Unsupported: `minimum/maximum`, `minLength/maxLength`, external `$ref`, `additionalProperties` other than `false`.
- Sources: https://platform.claude.com/docs/en/build-with-claude/structured-outputs and https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use.
- The scene toolset has far more than 20 tools and many optional properties, so keep tools **non-strict** and keep the zod validation that already runs in `aplicarHerramientaAsincrona`. Non-strict acceptance of the full subset is **unverified**; test with the real declarations.

**tool_choice:** `auto` (default), `any`, `tool` (name), `none` (define-tools page).
- Gemini `mode: ANY` with `allowedFunctionNames` (photo step 0): Anthropic has no allow-list. Equivalent: pass only the two declarations for that request and use `tool_choice: {type:"any"}`, or `{type:"tool", name}` for one. This changes `tools` for one request (cache miss for that step only).
- Parallel tool use is on by default. Disable with `tool_choice: {type:"auto", disable_parallel_tool_use: true}` (https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use). The scene loop already runs calls sequentially, so this is compatible.

**Limits on the tool list:** no hard cap on non-strict tool count or total schema size found in the pages read. **UNVERIFIED.** The scene list is roughly 120 KB, about 30-40k tokens (estimate, not measured). Keep it under 100k prompt tokens to avoid the long-context surcharge.

**Prompt caching for large tool lists** (https://platform.claude.com/docs/en/build-with-claude/prompt-caching):
- Put `cache_control: {type:"ephemeral"}` on the last tool object (caches all tools) and optionally on the system block. Up to 4 breakpoints. Prefix order: `tools` → `system` → `messages`.
- Any change to tool definitions invalidates all caches. Keep the array deterministic (`DECLARACIONES_ESCENA` is static).
- Haiku 5.5 pricing: 5m write 1.25x base ($0.125/MTok); 1h write 2x ($0.20/MTok); read $0.01/MTok (0.1x). Minimum cacheable prompt 512 tokens.
- The scene system prompt plus tool list is well above 512 tokens; expect later steps of the loop to read from cache.

**Other differences:**
- No `thoughtSignature`; use thinking blocks (§2).
- Consecutive same-role turns: merging behaviour **unverified**. Merge them in the adapter.

---

## 4. Vision (photo read and scene photo)

- Image block: `{type:"image", source:{type:"base64", media_type:"image/jpeg"|"image/png"|"image/gif"|"image/webp", data}}`, or `source:{type:"url"}` or `source:{type:"file", file_id}` (https://platform.claude.com/docs/en/build-with-claude/vision). Put images before text (docs recommendation).
- Limits: 10 MB base64 per image (Claude API); 600 images per request (100 for 200k-context models). Max 8000×8000 px. Above 20 images per request a 2000 px long-edge limit applies to all. Our flow sends 1 image (at most 2 in refine rounds), so this does not bind.
- **Resolution tiers:** Haiku 5.5 uses the high-resolution tier automatically: max long edge 2576 px, max 4784 visual tokens. Older Haiku: 1568 px / 1568 tokens. Visual tokens = ⌈w/28⌉×⌈h/28⌉ before downscaling.
- **Recommended:** send the JPEG already produced by `normalizarFotoA` if its long side is ≤ 2576 px. Max ~4784 visual tokens ≈ US$0.0005 per photo at $0.10/MTok. A 1568–2000 px long edge is fine for latency.
- Anthropic does not return image metadata; keep the `[IMAGEN_ID=...]` text labels as text parts, as the Gemini adapter does.
- Structured output for the photo read (Gemini `ESQUEMA_LECTURA_FOTO`, JSON): (a) a single forced tool with the lectura schema (`tool_choice: {type:"tool"}`; skips thinking, acceptable for extraction), or (b) `output_config.format` JSON output. The migration guide mentions `output_config.format` as a structured-output mechanism not available on Amazon Bedrock for Haiku 5.5. Its exact shape on the Claude API is **not verified**. Prefer (a) for the first version.

---

## 5. Streaming, abort, SDK

- **SDK:** `@anthropic-ai/sdk` is not in `package.json`. Latest version read from the GitHub `main` package.json: `0.133.0` (fetched 2026-10-09; verify with `npm view @anthropic-ai/sdk version`). No `engines` field. https://github.com/anthropics/anthropic-sdk-typescript/blob/main/package.json
- **Plain fetch** is also viable: `POST https://api.anthropic.com/v1/messages` with `x-api-key`, `anthropic-version: 2023-06-01`, `content-type: application/json` (cURL examples in the effort and vision pages).
- **Streaming** (`"stream": true`, SSE; https://platform.claude.com/docs/en/build-with-claude/streaming): `message_start` (input usage), `content_block_start`, `content_block_delta` (`text_delta`, `input_json_delta` with `partial_json`, `thinking_delta`, `signature_delta`), `content_block_stop`, one or more `message_delta` (`stop_reason`; usage is **cumulative**), `message_stop`. `ping` events can appear anywhere; `error` events can appear mid-stream.
- Tool input arrives as partial JSON; concatenate `partial_json` per `index` and parse on `content_block_stop`.
- Map to `FragmentoChat`: `text_delta` → `{tipo:"texto", delta}`; at `message_stop` → `{tipo:"fin", texto, llamadas, uso, modelo, finishReason}`. Keep thinking blocks in `LlamadaHerramienta.meta`.
- **Abort:** with plain fetch, pass `signal` to `fetch`; aborting closes the stream. The SDK's option name is not verified.
- Retry: reuse `conReintento` from `packages/agente-core/src/retry.ts`. Retry 429 and 5xx; do not retry 400. 401/403 → `sin_llave`.

---

## 6. Concrete adapter design

### 6.1 Provider id and dispatch
- Add `"claude"` to `ProveedorId` (`packages/agente-core/src/tipos.ts` L1) and to `proveedoresDisponibles()`. Make `chatDe` and `chatLecturaFotoDe` **dispatch on `id`** (they ignore it today, `registro.ts` L77-92).
- Give `/api/escena-ia` a provider-neutral path: it must resolve the provider through `resolverProveedor` (today it calls `getGeminiClient` directly).

### 6.2 Local-only enforcement (choke point = `proveedoresDisponibles`)
Gate **at availability**, because body override and cookie can name any available provider:
```ts
// src/lib/ia/nucleo/registro.ts (proposal, not applied)
function claudeLocalPermitido(): boolean {
  return process.env.IA_PROVEEDOR === "claude"          // explicit opt-in, not just a key
    && !process.env.VERCEL                               // never on Vercel
    && process.env.NODE_ENV !== "production"             // dev server only
    && Boolean(process.env.ANTHROPIC_API_KEY);           // presence only; never print the value
}
export function proveedoresDisponibles(): ProveedorId[] {
  const d: ProveedorId[] = [];
  if (process.env.GEMINI_API_KEY) d.push("gemini");
  if (claudeLocalPermitido()) d.push("claude");
  return d;
}
```
Notes:
- `next start` sets `NODE_ENV=production`, so a local production-mode run would be refused. The user's workflow is the dev server on :3010, so this fits. Say so if they want a local `next start`.
- `VERCEL` is the standard Vercel env var (convention; not checked in docs).
- Also make `obtenerAjusteGlobal` ignore `"claude"` unless `claudeLocalPermitido()`; otherwise a DB flag from a deployment could select Claude.
- Refuse the Python paths (`CHAT_PYTHON_ENABLED`, `chatOmoikaneDe` Python branch) for `claude`: the Python ai-api is Gemini-only.
- Embeddings and photo embeddings stay Gemini. For a "Claude only" mode the RAG and photo-search routes need `GEMINI_API_KEY` or must degrade. Decide with the user.
- Env vars to add (never print values): `ANTHROPIC_API_KEY`, `ANTHROPIC_CHAT_MODEL` (default `claude-haiku-5-5`), `IA_LOCAL_ESFUERZO` (`low|medium|high`; proposal default `low`, to be validated by eval), optional `IA_LOCAL_PENSAMIENTO`.

### 6.3 Transport
Option A (recommended): plain `fetch` in a new `packages/agente-core/src/anthropic/chat.ts` (ChatPort, mirroring `gemini/chat.ts`). No new dependency. Option B: `@anthropic-ai/sdk` 0.133.0 (typed, built-in retries), which needs a guard-test inventory entry for `sdk-otro-proveedor`.

Either way the guard test flags the host `api.anthropic.com` or the SDK import until the adapter is in `INVENTARIO` with an enganche requiring `envolverChatPort(` or `iniciarLlamadaIa(`. **Also add a detector** for `/\.messages\.(create|stream)\(/`.

### 6.4 Request mapping (ChatPort → Messages API)
```jsonc
{
  "model": "claude-haiku-5-5",
  "max_tokens": 4096,                                  // room for thinking (counts toward max_tokens)
  "system": [{ "type": "text", "text": "<sistema>", "cache_control": {"type":"ephemeral"} }],
  "tools": [ /* Herramienta[] → name, description, input_schema (JSON Schema minus $schema); last one gets cache_control */ ],
  "tool_choice": { "type": "auto" },                   // {type:"any"} or {type:"tool",name} on forced steps; optional disable_parallel_tool_use:true
  "thinking": { "type": "adaptive" },                  // or {type:"disabled"} if IA_LOCAL_PENSAMIENTO=off
  "output_config": { "effort": "low" },                // from IA_LOCAL_ESFUERZO
  "messages": [ /* §6.5; must end with role "user" */ ]
}
```
Do not send `temperature`, `top_p`, `top_k`.

### 6.5 Turn mapping (Mensaje[] → messages)
- `usuario{texto, imagenes}` → `{role:"user", content:[ image blocks for each imagen (preceded by its "[IMAGEN_ID=...]" text), {type:"text", text} ]}`.
- `asistente{texto}` → `{role:"assistant", content:[{type:"text", text}]}`.
- `asistente{llamadas}` → `{role:"assistant", content:[ ...thinking blocks from meta (unmodified, with signature), ...{type:"tool_use", id, name, input: args} ]}`. Keep `id`; generate one if missing (`toolu_` + counter) and reuse it in the matching `tool_result`.
- `herramienta{nombre, llamadaId, resultado}` → consecutive ones merged into one `{role:"user", content:[ {type:"tool_result", tool_use_id, content: JSON.stringify(resultado), is_error?}, ... ]}`, results first, then any text.
- Merge consecutive same-role messages in the adapter.
- Last message must be `user`; never send an assistant prefill.

### 6.6 Response mapping (message → TurnoChat)
- `content[]`: `text` → `texto`; `tool_use` → `llamadas[{id, nombre:name, args:input, meta:{thinking: turn thinking blocks}}]`; `thinking` / `redacted_thinking` → kept in `meta` for replay (not shown).
- `stop_reason` → `finishReason`: `tool_use`, `end_turn`, `max_tokens`, `refusal` (handle, do not retry), `model_context_window_exceeded`.
- `usage` → `uso`: `entrada = input_tokens`, `salida = output_tokens` (includes thinking), `cacheados = cache_read_input_tokens`, plus `cache_creation_input_tokens`; `pensamiento` from `output_tokens_details.thinking_tokens` (field named in the thinking page).
- `modelo` = response `model`.

### 6.7 Scene loop (`/api/escena-ia`, e6f)
Same loop shape: generate → if tool calls, apply each via `aplicarHerramientaAsincrona` / `aplicarModeladoDeFoto` / `aplicarReporte` → push the assistant turn verbatim (with thinking) → push tool results → `verificarCambios` attached to the last changing result. The NDJSON stream (`responderEnFlujo`) wraps this and should keep working if the loop yields the same events.
- Provider branch: `chatDe(proveedor, "escena_ia")` or a raw Anthropic branch.
- Step 0 with photo: `tool_choice` `{type:"any"}` with only the two allowed declarations, or `{type:"tool"}`.
- Cost (`costeUsd`, L93): replace with Claude prices. Input $0.10, output incl. thinking $0.50, cache write $0.125, cache read $0.01 per MTok. Use $0.50 / $2.50 when a request exceeds 100,000 prompt tokens.
- Audit: keep `decidir(...)`; add `llamada_ia` / `respuesta_ia` per step with `iniciarLlamadaIa` or `envolverChatPort`. Add `extraerRespuestaAnthropic` analogous to `extraerRespuestaGemini`. Hash images with `huellaBase64`.
- `modelo:escena_ia` decision: record `proveedor` and `modelo`.

### 6.8 Errors (`categorizarError` analogue)
- 401/403 → `sin_llave`, not retryable. 429 → `cuota`, retryable with backoff. 5xx → `desconocido`, retryable. 529 (overloaded) is typical but **not verified** in the pages read.
- 400 with an image in the request → non-retryable, with a prefix like `PREFIJO_IMAGEN_RECHAZADA`.
- `stop_reason: "refusal"` → a distinct error or user message; do not retry.
- Add `"claude"` to `ProveedorId`; `ErrorIA(causa, proveedor, mensaje, reintentable)` already takes a provider id.

### 6.9 Vision prompt
Single user message: image first, then the existing text (`textoUsuario` / `REGLAS_FOTO`). Wording needs no change, but re-test photo cases (ranges, plantillas), since the photo read currently runs on Gemini vision with a JSON schema.

### 6.10 Tests and cost discipline
- Guard: update `INVENTARIO` and `RUTAS_FLUJO`. The `gemini-escena-ia` entry needs a Claude counterpart.
- Eval: reuse `scripts/eval/eval-chat-thinking.ts` (7 dialogues) against `claude-haiku-5-5` at `low`, `medium`, `high`; measure cost and steps. Per the memory note "Pruebas que pagan", filter paid-API tests before sweeps; the guard test is free.
- Audit: after a run, check `npm run registros` shows `llamada_ia` / `respuesta_ia` with `proveedor:"claude"`.

---

## 7. Open questions and risks

1. **Quality:** Haiku 5.5 is two days old. Tool selection, honesty on NO_MATCH and the scene CRUD rules are untested on it. Run the eval before any default switch.
2. **Thinking replay and cost:** thinking blocks accumulate in context on Haiku 5.5. A 12-step loop may cost more than the per-token prices suggest.
3. **Non-strict schema acceptance:** unverified for `$schema`, `additionalProperties:false`, `exclusiveMinimum`, numeric `const` unions. Test with the real list.
4. **Embeddings:** the feature set needs Gemini embeddings. A Claude-only mode is not fully local-only unless RAG and photo search are disabled or re-embedded elsewhere.
5. **Unverified:** consecutive same-role message merging; `output_config.format` request shape.
6. **Account-bound thinking** and the append-only rule: fine for one key; key rotation or multi-account replay breaks thinking continuity.
7. **Guard blind spot:** no detector for `.messages.create(`. Add one.
8. `chatDe` ignoring `id` and the scene route bypassing the registry are existing defects, not Claude-specific. Both must be fixed for any second provider to work.
9. Rate limits and 529 behaviour for the account: not checked.
10. Measured token size of the scene tool list: not measured (≈120 KB is the brief's figure).

---

## 8. Sources (URLs read on 2026-10-09)

- Models overview: https://platform.claude.com/docs/en/models/overview
- Haiku 5.5 model page: https://platform.claude.com/docs/en/models/haiku-5-5/overview
- Haiku 5.5 migration guide: https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide
- Pricing: https://platform.claude.com/docs/en/about-claude/pricing (read partially)
- Effort: https://platform.claude.com/docs/en/build-with-claude/effort
- Extended thinking (migration to adaptive): https://platform.claude.com/docs/en/build-with-claude/extended-thinking
- Thinking: https://platform.claude.com/docs/en/build-with-claude/thinking
- Define tools / tool_choice: https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
- Handle tool calls / tool_result: https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls
- Parallel tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use
- Strict tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
- Structured outputs (JSON Schema limitations; strict limits): https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Vision: https://platform.claude.com/docs/en/build-with-claude/vision
- Streaming: https://platform.claude.com/docs/en/build-with-claude/streaming
- TypeScript SDK package.json (0.133.0): https://github.com/anthropics/anthropic-sdk-typescript/blob/main/package.json

## 9. Unverified (summary)

- Non-strict tool schema keyword acceptance; any tool count or total size limit.
- Merging of consecutive same-role messages by the API.
- `output_config.format` request shape on the Claude API.
- SDK `signal` option name; SDK latest version (0.133.0 from GitHub main, not npm).
- 529 / overload behaviour; account rate limits.
- `VERCEL` env var convention (not checked in docs).
- Haiku 5.5 quality vs Gemini 3.6 Flash on this app's tasks (not measured).
- Token size of the scene tool list (not measured).
