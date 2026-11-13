---
id: REQ-032
status: done
created: 2026-11-13
track: standard
---
# REQ-032 — Conversation, problem, order and person tracking (WhatsApp bot, web assistant, orders)

## Problem & goal
Today the WhatsApp bot's events exist only as JSON lines in `docker logs` (3 × 10 MB, rotated), conversation state is a hashed local SQLite, and the admin app has only a people panel (`/admin/whatsapp`) and an orders panel (`/admin/pedidos`). Nobody can answer «what happened with this customer», «what is failing», or «what is stuck» without SSH.

**Success looks like:** an administrator opens one page and, for any person, sees their conversation timeline, orders and problems; and sees a list of open problems (bot errors, stuck orders, stuck customers) with a link to the person and the order, without touching the server.

## Users / actors / stakeholders
- Administrators (David, William): read-only tracking of everything below. The only readers (owner decision 2026-11-13).
- Customers (WhatsApp, web): their data is protected; texts expire.

## Scope (in)
### US-1 (P1, Must) — Persistent event timeline per person
As an admin, I want every meaningful bot event and every customer message stored centrally so that I can follow a conversation after the fact.
**Acceptance:**
- Given a customer sketches, counts, shops or fails, when I open their timeline, then I see ordered events (step, choice, outcome, error) and the customer's own texts.
### US-2 (P1, Must) — Problems list
As an admin, I want one list of open problems so that I notice what needs attention.
**Acceptance:**
- Given bot errors, orders in `sin_destinatario`/`envio_fallido`/stale `pendiente`, abandoned or exhausted-quota conversations, when I open Problems, then each appears once (grouped), with counts, last occurrence, person and order links, and I can mark it reviewed or resolved with a note.
### US-3 (P1, Must) — Person page
As an admin, I want one page per person joining contact data, timeline, orders (web and WhatsApp) and problems.
### US-4 (P2, Should) — Web assistant events
As an admin, I want the web assistant (guided assistant, counter, sketch) events in the same timeline, keyed by account, so web and WhatsApp customers are followed alike.
### US-5 (P2, Should) — Retention
As the owner, I want customer texts to expire after 90 days automatically while events and counters stay.

## Out of scope
- E-mail or WhatsApp alerts to the team (owner did not select them; may come later).
- Storing the bot's replies, images or audio; transcripts beyond the customer's texts.
- Non-admin roles (advisers) seeing tracking; exports; real-time push.
- Changing what the bot says or does.

## Requirements
- R1. When the bot handles an inbound customer text, the system shall store it (≤ 1000 chars, secrets and card-like numbers masked) in the event store with the person's hash, channel and conversation id.
- R2. When the bot emits any existing log event, the system shall also append a classified event (type, severity, step, order id when known, minimal JSON detail) without blocking the conversation.
- R3. If the event store is unreachable or slow, then the bot shall keep answering customers, drop the event after a short deadline and count the drop in its stdout log.
- R4. While a person has been silent for 6 h, the next inbound message shall open a new conversation id.
- R5. The admin timeline shall be readable only with the existing administration permission (`PERMISOS.administracion_usuarios`), `no-store`, paginated, and shall show the phone only to admins.
- R6. When an order is created or changes state, its event shall carry the order id so the timeline links to the order and the order to the person.
- R7. The Problems list shall derive from: error-severity events; orders in `sin_destinatario`, `envio_fallido`, or `pendiente` older than 24 h; conversations with no completion after 24 h; quota/limit hits. Repeated identical problems group by (type, person, day).
- R8. When an admin marks a problem reviewed or resolved, the system shall record who, when and an optional note, and keep it out of the open list until the same problem recurs on a later day.
- R9. Customer texts older than 90 days shall be cleared (text set to NULL, event kept) by a bounded daily job; the job shall be idempotent and logged.
- R10. Web events (US-4) shall use the same store with `canal = 'web'` and the account id, never the browser-supplied user id.

## UI / design contract
- UI scope / users: admins, desktop first, phone usable. Routes under `/admin/seguimiento`: Conversaciones (list + timeline detail), Problemas, Persona.
- Visual direction / existing system: the admin area's current components from `@bitacora/ui`; Spanish UI; Catppuccin-compatible, same density as `/admin/pedidos`.
- Accessibility or interaction constraints: semantic tables/lists, keyboard-reachable filters, visible focus, loading/empty/error states.

## Edge cases & errors
- Person without a registered contact (hash only): shown as «Sin registrar» with a short hash.
- Event burst (album, retries): bounded queue; drop oldest with a counted log line.
- Bot restart mid-conversation: conversation id derives from the last event time, not memory.
- Timezone: stored UTC, shown in America/Bogota.

## Constraints
- AGENTS.md: no secrets or full conversations by default — this REQ is the owner's explicit, scoped authorization (texts only, 90 days, admins only). Do not log keys, tokens or full images.
- Migration is additive; applied to production alone with a prior backup (as 066/070); rollback = drop the new tables (no existing table altered). Role grants: the bot's DB user needs INSERT on the new tables.
- Bot code stays framework-light; the writer is one module with a bounded in-memory queue and deadlines (no new infrastructure).

## Priorities & phases
MVP: US-1, US-2, US-3 for WhatsApp. Later: US-4, US-5.

## Timeline & dependencies
Depends on migration 071 (new) and the bot's existing `WHATSAPP_DATABASE_URL` pool. No external services.

## Open questions / assumptions
- Assumption: conversation = same person within 6 h of silence.
- Assumption: «stuck customer» = conversation whose last event is a question step (colores…lugar) with no answer for 24 h.
