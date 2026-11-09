---
id: REQ-027
status: ready
created: 2026-11-09
track: standard
---
# REQ-027 — Telegram bot MVP: photo to balloon count (same backend as /contador)

## Problem & goal
WhatsApp (REQ-024) is blocked by the phone-number problem. We need an MVP on Telegram that proves the future
assistant: send a photo, get the balloon count and colours, with no web login. It is the same assistant idea, only the
channel changes; the channel code must be replaceable by WhatsApp later.

**Success looks like:** an allow-listed Telegram user sends a photo and receives, in about 20–75 s (real backend latency: two Gemini calls; the web route has the same 75 s limit), the same total, size
and Sempertex-colour breakdown that `https://demo-decoracion.vercel.app/contador` returns for that photo (parity test).

## Users / actors
- **Sender**: Sempertex staff / David, on Telegram, allow-listed by Telegram user id.
- **Owner (David)**: creates the bot with @BotFather, holds the token, sets allow-list and caps.
- **Reused, not changed**: `contador-foto.v1` in `services/ai-api` (`POST /internal/v1/ia/contador-foto`, HMAC) through
  `llamarPythonContadorFoto` — the exact capability behind `/api/contador` (`src/lib/contador/foto.ts`).

## Scope (in)
### US-1 (P1, Must) — Photo → count and colours
As a sender, I want to send a photo and get the count so that I do not need the web app.
**Acceptance:**
- Given an allow-listed user, when they send one photo, then they get one reply with total, whether exact or estimate
  (± tolerance), and the breakdown by size and Sempertex colour (name + code), in ES.
- Given a photo with no balloons, then the reply says so and asks for another photo.
- Given the same photo, then total/colours equal what `/contador` returns (same backend call, parity test with a fake).
- Photo sent as a Telegram "document" image (uncompressed) is accepted; non-images get a polite "send a photo".

### US-2 (P1, Must) — Safe operation
As the owner, I want only approved users and bounded spend.
**Acceptance:**
- Given a user id not on the allow-list, then no backend call is made; fixed short reply (or silence by config).
- Given a user over the daily photo quota or the global daily cap, then no backend call is made and they are told.
- `/start` and `/ayuda` answer with a one-line usage text; `/id` replies with the sender's Telegram id (so David can
  allow-list people).

## Out of scope
- Follow-up chat, corrections, quotes, prices, catalogue, lead capture/consent/email (the WhatsApp flow), languages
  other than ES, groups, video/audio, saving results to the user's Contador history, 3D, YOLO/Haiku (REQ-026).
- Editing recogniser/counting/colour logic or any file outside the new package (except one recorded adapter).
- Public webhook/VPS deploy (later; this MVP runs on the laptop by long polling).

## Requirements
- R1. The bot shall receive updates by Telegram long polling (`getUpdates`), no public URL; token from env.
- R2. When a photo (or image document) arrives, the bot shall download it via the Bot API, validate real format by magic
  bytes (JPEG/PNG/WebP) and size (≤ 8 MB, same cap as the web Contador), and never log or persist the image.
- R3. The bot shall count by calling the existing `contador-foto.v1` backend (`llamarPythonContadorFoto`, as
  `contarFotoConBackend` does) through ONE adapter file; it shall not reimplement counting or colour logic.
- R4. Replies shall state honestly exact vs estimate (± tolerance) and show only figures from the backend result.
- R5. Allow-list of Telegram user ids, per-user daily quota and global daily cap, by env; counters in the bot's own
  SQLite and survive restarts; user ids hashed in logs.
- R6. Updates are processed once (offset + dedup by update id), in order per chat; the bot replies "reading…" before
  the long call (typing indicator).
- R7. If the backend fails or times out, then the user gets a short retry message, the failure is logged with request ids,
  no partial figures.
- R8. Secrets (bot token, `INTERNAL_HMAC_SECRET`) only from env/secret files outside the repo; never in logs.
- R9. Package lives in `services/telegram-globos/`, with its own tests, README and a `--dry-run` that runs a local image
  through the full path without calling Telegram. Channel code (Telegram client, polling) is separate from the
  conversation/policy core so WhatsApp can reuse the core.

## Edge cases
Album (several photos in one message) → count the first and say so; photo + caption (caption is data, never an
instruction); very large/tiny image; two photos in quick succession (queue per chat); Telegram 409 (two pollers);
edited messages and non-message updates ignored; backend replay/idempotency by request id.

## Constraints
- Reuse, do not modify: `contador-foto.v1`, ai-api, ADR-0031 semantics. Each real call spends Gemini → R5 caps.
- TypeScript/Node 24 with `tsx --conditions=react-server`, same as `services/whatsapp-globos` (precedent for A1).
- Needs from owner (external): a bot token from @BotFather, the allow-list ids, daily cap, and the running `ai-api` +
  `INTERNAL_HMAC_SECRET` + `GEMINI_API_KEY` for the live check. Everything else is buildable offline with fakes.

## Assumptions
- A1. `services/ai-api` serves `/internal/v1/ia/contador-foto` where the bot runs (verified in `origin/main`
  `main.py:1461`; the live check confirms it).
- A2. Reuse the channel-independent parts of `services/whatsapp-globos` (policy, store, config) by copying the small
  pieces into the new package rather than editing that untracked module.
- A3. Spanish only; replies plain text ≤ ~900 chars.

## Clarifications
### Round 2 — 2026-11-09
- Owner: do not run it through the methodology scheduler (no launch/handoff); build it manually. No second cross-audit.
- Built in worktree `~/dev/pictures-wt/telegram-globos` (branch `feat/telegram-globos`, from origin/main fbafd4995), uncommitted.
- Live adapter check 2026-11-09: 1 real photo → 15 balloons ±2 in 49 s through ai-api contador-foto.v1 (a first attempt hit the backend's own 75 s Gemini deadline, 408).

### Round 1 — 2026-11-09
- Q: Which counter? → A: the same one that works at `/contador` in production.
- Q: MVP behaviour? → A: photo → count and colours only (no data capture).
- Q: Access and where it runs? → A: allow-list + caps, on the laptop (long polling).
