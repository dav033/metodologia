---
id: REQ-024
status: ready
created: 2026-11-05
track: standard
---
# REQ-024 — WhatsApp conversational module: balloon count and colour detection

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Customers and the sales team want to send a photo of a balloon decoration over WhatsApp and get back how many
balloons it has and which colours it uses, without opening the web app. Pictures already reads photos (Amaterasu
recogniser + `ai-api` balloon count) but only behind the web login. This requirement adds a **new, isolated
conversational module** that talks to WhatsApp and reuses that reading; it adds no new counting or colour logic.

**Success looks like:**
- A photo sent from an allow-listed number gets a reply with total count (exact or estimated, said honestly) and
  colours (Sempertex name/code when matched), in the user's language (ES default), in under ~45 s p95.
- The module's counts and colours are identical to what the web `/api/references/analyze` path returns for the
  same photo (parity test on a fixed photo set).
- Zero edits to files owned by other work in the repo, except the explicit single-purpose adapter boundary (R12).

## Users / actors / stakeholders
- **Sender**: customer or Sempertex staff, on WhatsApp, allow-listed by phone number.
- **Owner (David)**: operates the Meta app/number, the allow-list and the daily spend cap.
- **Existing services (reused, not changed)**: Amaterasu recogniser (`src/lib/ia/amaterasu`), `ai-api`
  `POST /internal/v1/ia/conteo-referencia` (HMAC-signed, Gemini vision).

## Scope (in)
### US-1 (P1, Must) — Count and colours from a photo
As a sender, I want to send a photo and get the balloon count and colours so that I can quote or check a decoration.
**Acceptance:**
- Given an allow-listed number, when it sends one image, then it receives one reply with total balloons, whether
  the figure is exact (≤40 visible per piece, per ADR-0031) or an estimate, and the colours with their share.
- Given a photo with several balloon structures (arch + column), then the reply lists each piece and the total.
- Given a photo with no balloons, then the reply says so and asks for another photo.

### US-2 (P1, Must) — Conversation around the result
As a sender, I want to ask follow-ups and correct the result in plain language so that I do not need a menu.
**Acceptance:**
- Given a result, when the sender asks "¿y de qué colores?" or "¿cuántos rojos?", then the module answers from the
  stored reading without a new vision call.
- Given a result, when the sender says "faltan 3 rojos", then the module applies it as a user-declared correction,
  labelled as such, and never presents it as detected.
- Off-topic requests (quotes, prices, other products) get a short refusal that states this number only counts
  balloons and detects colours.

### US-3 (P1, Must) — Safe operation
As the owner, I want only approved numbers and bounded spend so that the number cannot be abused.
**Acceptance:**
- Given a number not on the allow-list, then no vision call is made and a fixed reply (or silence, configurable) is sent.
- Given a number over its daily photo quota or the global daily cap, then no vision call is made and the sender is told.

### US-4 (P2, Should) — Several photos of one decoration
Up to 3 images in one message burst are read together (the recogniser accepts 1–3, ≤10 MB total).

## Out of scope
- Quotes, pricing, catalogue search, 3D scene, any Taller/guided-chat behaviour.
- Video, audio, documents, stickers (polite "send a photo" reply).
- Initiating conversations / template messages (customer-service window only: reply within 24 h of the user's message).
- Changing the recogniser, the count prompt or the colour logic; any web UI; groups; payments.
- Counting with a new engine (YOLO, etc.): reuse only.

## Requirements
- R1. When Meta calls the webhook GET with `hub.verify_token`, the module shall echo `hub.challenge`; otherwise 403.
- R2. When a webhook POST arrives, the module shall verify `X-Hub-Signature-256` (HMAC-SHA256, app secret, constant-time) over the raw body and reject invalid ones with 401, doing nothing else.
- R3. The module shall acknowledge the webhook with 200 within Meta's timeout and process asynchronously; duplicate deliveries of the same message id shall be processed once (idempotency).
- R4. When an image message arrives, the module shall download it with the Meta media API (media id → URL → authenticated fetch), validate real format by magic bytes (PNG/JPEG/WebP) and size, and never log the image.
- R5. The module shall obtain count and colours by running the existing recogniser and then calling `ai-api` conteo-referencia with the internal HMAC, reusing the repo's clients; it shall not reimplement counting or colour logic.
- R6. The module shall report a count as exact only when the reading says exact; otherwise as an estimate with the reading's tolerance/confidence stated in words.
- R7. The conversational model shall only phrase replies from the stored structured reading; every number and colour in a reply shall come from that reading or from an explicitly labelled user correction (checked by a post-generation guard).
- R8. The module shall persist per-conversation state (last reading, corrections, message ids, counters) in its own store, keyed by phone number hash, with a retention limit (default 30 days) and no raw images kept after processing.
- R9. If the recogniser, `ai-api` or the model fails or times out, then the sender shall get a short retry message and the failure shall be logged with request ids; no partial figures.
- R10. The module shall enforce an allow-list (R-US3), a per-number daily photo quota and a global daily spend cap, all configurable by env; counters survive restarts.
- R11. Secrets (Meta app secret, access token, verify token, `INTERNAL_HMAC_SECRET`, Gemini key) shall come from env/secret files outside the repo and never appear in logs.
- R12. The module shall live in its own directory (`services/whatsapp-globos/`) with its own package, tests and docs. It shall reach repo code only through one adapter file (`adapters/reconocedor.ts`) so a change in `src/lib/ia/...` breaks one place; no other repo file is edited without a recorded ruling.
- R13. Replies shall be in the sender's language (ES default, EN if the sender writes English), plain text, ≤ ~900 chars.
- R14. The module shall expose a health endpoint and structured logs; a `--dry-run` mode shall process a local image through the full path without calling Meta.

## UI / design contract (optional)
Not applicable: the interface is WhatsApp text. Reply copy is specified in the plan (templates in ES/EN).
- UI scope / users: n/a
- Visual direction / existing system: n/a
- Accessibility or interaction constraints: short messages, no tables, emojis optional and sparse.

## Edge cases & errors
- Image sent as "document" (uncompressed) vs photo; very large or tiny images; HEIC (unsupported → ask for JPEG/PNG).
- Photo with balloons but heavy overlap/dense walls: estimate with low confidence, say so, suggest a closer photo.
- Multi-colour/gradient pieces; colours that do not match a Sempertex reference (give the colour name only).
- Two photos in quick succession; photo followed by text before the reading finishes (queue per number).
- Meta retries / out-of-order webhooks; messages older than the 24 h window; status webhooks (ignore).
- Correction that contradicts the reading wildly (e.g. "faltan 500"): confirm before applying.
- Prompt injection in image text or caption: captions are data, never instructions.

## Constraints
- WhatsApp Cloud API (Meta) as the only channel; number and Meta app owned by the owner (external setup).
- Reuse, do not modify: Amaterasu recogniser, `ai-api` conteo-referencia, ADR-0031 semantics. Gemini via the existing providers; per-call cost is real, hence R10.
- TypeScript (Node 24), run with the repo's `--conditions=react-server` convention where needed (to be verified in T1).
- Another agent is editing other repo files concurrently: work in a dedicated branch/worktree, touch only the new directory.
- Privacy: phone numbers hashed at rest in logs/state; photos not stored; retention limit documented.

## Priorities & phases
- **M1 (MVP)**: webhook (R1–R3), media download (R4), adapter + reading (R5–R6), fixed-template reply, allow-list and caps (R10), dry-run (R14). Demonstrable end to end with a real WhatsApp test number.
- **M2**: conversational layer with guard (R7), state/corrections (R8), languages (R13), multi-photo (US-4).
- **M3**: hardening: failure paths (R9), observability, deployment recipe, parity test against the web path, runbook.

## Timeline & dependencies
- Needs from the owner (external, batched): Meta developer app + test phone number, permanent access token, app secret, verify token, public HTTPS URL for the webhook, initial allow-list, daily cap value. M1 can be built and tested fully with `--dry-run` and recorded Meta payload fixtures before these exist.
- Deployment target (VPS next to `ai-api`, or Vercel) is decided in the plan; recommendation: container on the existing VPS (long-running async work, shared network with `ai-api`).

## Assumptions
- A1. The recogniser can run outside Next via `tsx --conditions=react-server` (the repo's eval and `diagnosticar-foto.ts` scripts already do this). To be verified in T1; if false, the adapter falls back to a thin internal call to `ai-api` plus its own recognition prompt only with a recorded ruling.
- A2. TypeScript chosen over Python to reuse the typed clients (recommended; owner did not object).
- A3. Allow-list + per-number daily quota chosen over open access (recommended; owner did not object).
- A4. "Reuse the existing service" (owner) includes the recogniser step, since conteo-referencia needs its structures as input; owner chose option (b): the module runs the recogniser itself.
- A5. Meta customer-service window only; no outbound templates in this version.
- A6. Conversation model: the repo's existing Gemini provider; model choice and cost cap set in the plan.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered |
| Edge cases | Covered |
| Acceptance criteria | Covered |
| Constraints | Covered |
| UI / design direction | N/A (WhatsApp text) |
| Priorities & phases | Covered |
| Timeline | Covered (external inputs listed) |

## Clarifications
### Round 1 — 2026-11-05
- Q: Which project? → A: Pictures / Sempertex.
- Q: How does it connect to WhatsApp? → A: WhatsApp Cloud API (Meta).
- Q: Scope of v1? → A: customer sends a photo → counts balloons and detects colours.
- Q: Vision engine? → A: reuse the counting/colour service already in the system.
- Q: How to call the reading service (Next route vs module runs the recogniser)? → A: option (b), the module runs the recogniser itself and calls `ai-api` directly — cleanest long term.
- Q: Language / who can write? → A: not answered; recommended defaults taken (A2, A3).
