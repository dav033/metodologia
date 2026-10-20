---
id: REQ-020
status: clarifying
created: 2026-10-20
track: deep
---
# REQ-020 — Happia chat v2 event advisor that ends in a brief

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Sempertex/Happia "Pilot 1" (client document, Oct 2026). Today a person (Diana) gathers each event request by phone and
writes it up for decorators. Leonidas (14 Oct): "I want a party for ten kids. I talk to it and at the end I get a brief
that says: this is how we'll organise it." Build a Spanish, mobile-first advisor chat that a customer opens from a link,
talks to by text, photos or voice notes, and that ends in a one-page **brief** the customer approves.

A **brief** = a one-page summary of the event (what, for whom, when, where, guests, likes/dislikes per photo, venue,
priorities, budget, requests, proposed standard Happia package with price, photos), with a vendor version that omits
the customer's name, contact and budget.

**Success looks like:** (client metrics, baselines agreed with Sempertex in week 1) conversations ending in an approved
brief; briefs sent to vendors without a call; Diana's time per brief vs today; customer rating of the advisor.

## Users / actors / stakeholders
- Customer (parent organising a birthday; also corporate and school events), on a phone.
- Diana (Happia operator): reviews/approves briefs — her screen is OUT of this REQ for now (owner, 2026-10-20).
- Decorators/vendors: receive the vendor brief (sending is out of this REQ for now).
- Stakeholders: Leonidas, Rodrigo (a real person stays accountable), William (Happia platform / API).
- Owner of this REQ: David.

## Scope (in)
Owner scope decision 2026-10-20: a **new section "Happia chat v2"** inside the Pictures app (`dav033/pictures`),
with the new flow and all the new capabilities; it reuses Pictures pieces. The existing `/happie` chat, its webhook and
the `happie.v1`/`happie.v2` contracts stay untouched.

Candidate capabilities (from the client doc, minus the removed blocks):
- Conversation: opens on mobile from a link without an account; short privacy notice; warm, never a form; progress
  toward finishing the brief; leave and come back; "test version" notice for testers.
- Understand the event: always gathers what vendors need (event and for whom, date and time, city and exact address,
  venue, guest count, contact); birthdays plus corporate and school events; brand/vendor requests; budget help;
  organiser priority (impress, personalise, simple, best price).
- Photos and voice notes: inspiration photos and a venue photo from camera or gallery; asks likes/dislikes per photo;
  first look (describes what it sees and asks to confirm); photos go to the brief as received; voice notes transcribed
  and used as text; the advisor answers in text.
- Ideas and packages: directions for undecided customers from an initial group of 10–15 chosen by Diana; themed items
  Happia sells; a standard package/service first when it fits, with its price from the Happia catalogue read daily,
  with a Diana list as fallback; only what Happia vendors can do.
- Brief: customer approves or corrects a summary; one-page brief with photos, likes/dislikes, venue, priorities,
  budget and requests; vendor version without name, contact and budget.

## Out of scope
- Diana's operator screen (live list, needs-attention queue, takeover/handback, edit/approve, send to vendors) —
  removed temporarily by the owner (2026-10-20).
- Soft-launch safety block (per-link limits, per-conversation AI caps, end rating, drop-off analytics, ~50 testers) —
  removed temporarily by the owner (2026-10-20).
- Any change to the `/happie` webhook or the `happie.v1`/`happie.v2` contracts.
- Client doc exclusions: deep photo reading (reliable element recognition, colour matching, fit-in-venue warnings,
  closest known design); brief → quote, vendor quotes, availability, draft package or cart link (Pilot 2); creating or
  editing images; counting balloons from photos (William's tool); payments; hardened security for a full public
  launch; voice replies; growth dashboard (Pilot 1B).

## Requirements
_To be written after the interview rounds (EARS)._

## Edge cases & errors
_Pending interview._

## Constraints
- Lives in the Pictures repo (Next 16 app, Python ai-api on the VPS, Neon Postgres, S3 Garage on the VPS), deployed to
  Vercel and the VPS through the existing CI gate.
- Personal data (name, phone, address, budget) — Colombian Ley 1581 (habeas data): privacy notice and minimal data.
- Happia Integrations API today exposes paginated `GET /services` and `GET /packages` only (HappiaClient); real prices,
  themed items and carts depend on William's platform session.

## Priorities & phases
_Pending interview._

## Timeline & dependencies
- Client calendar: work starts Sun 25 Oct; Halloween test Thu 29 Oct (first text conversation ending in a brief);
  2–19 Nov photos, voice, venue photo, ideas and packages; rehearsal week of 23 Nov; soft launch Thu 26 Nov.
- Colombian holidays inside the window: Mon 2 Nov, Mon 16 Nov.
- Dependencies: William (Happia API capabilities), Diana (10–15 directions, fallback price list, brief format).

## Reuse map (exploration 2026-10-20, origin/main 54d176a3)
- Agent: `packages/agente-core` + the tool agent in `src/app/api/asistente-guiado/route.ts`; `BriefGuiadoSchema`
  (`src/lib/ia/contracts/asistente-guiado-v1.ts:31`) and the `guardar_brief_guiado` tool as the seed of the brief slots.
- Chat UI: `src/components/guiado/` (Burbujas, Compositor, ChipsOpciones, RespuestasRapidas, IndicadorEscribiendo) and
  the mobile viewport of `src/app/asistente/page.tsx`.
- Photos: `foto-subida.ts`, `src/lib/imagen-cliente/preparar-foto.ts`, `/api/references/analyze` (Gemini vision) and
  `lectura-foto.ts`; storage via `src/lib/almacen/objetos-s3.ts` (photos are not stored today).
- Voice: `src/components/voz/*` and `/api/voz/transcribir` (faster-whisper on the VPS, off by default; service not in
  this repo — verify it is alive).
- Ideas: `src/lib/biblioteca-sempertex/decoraciones.json` (46 decorations with theme, event, age, photos, palette);
  vendors directory `proveedores.json` (13, four cities) for later.
- Happia catalogue: `packages/happie-package-ia/src/cliente.ts` (read-only reuse); no daily cache or fallback today.
- Patterns: shared-quote token/approval (`src/lib/shared-quotes/`, migration 036); printable sheets (`HojaArmado.tsx`).
- Not reusable for Pilot 1: 3D engine, Taller, FLUX/Kontext, Sempertex colour resolver, single quote pricer.
- Note: the local checkout `~/dev/pictures` is on an old branch (`feat/req-014-…`); work must start from origin/main.

## Assumptions
_Pending interview._

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Partial |
| Out of scope | Clear |
| Flows & behavior | Partial |
| Edge cases | Missing |
| Acceptance criteria | Missing |
| Constraints | Partial |
| Priorities & phases | Missing |
| Timeline | Partial |

## Clarifications
### Round 0 — 2026-10-20 (conversation)
- Q: Modify the `/happie` webhook/contracts? → A: No; build a new "Happia chat v2" section.
- Q: Diana's screen and soft-launch safety? → A: Removed temporarily from this scope.
- Q: Where? → A: Linked to (inside) the Pictures project.
