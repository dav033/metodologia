---
id: REQ-020
status: done
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
Owner scope decision 2026-10-20: a **new section "Asesor Happia" (route `/asesor`)** inside the Pictures app (`dav033/pictures`),
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

- Access (rounds 1–2): own authentication, two accounts only — a general account `user` and an `admin` account, each
  with its own password. `admin` can do everything `user` can plus read-only monitoring of conversations and briefs.
  No Supabase Auth, no public sign-up. The rest of Pictures keeps `APP_PASSWORD`.
- Storage: **Supabase used only as managed Postgres** (project `byepzsrbjgvrmsmfuzhj`, us-east-2, transaction pooler);
  conversations, messages, photos (bytea) and briefs live there. The customer resumes on the same device only.
- Milestone M1 = Halloween test (Thu 29 Oct): a text conversation that ends in a brief; photos, voice and ideas after.

## Out of scope
- Diana's full operator screen (needs-attention queue, takeover/handback, edit/approve, send to vendors) — removed
  temporarily by the owner (2026-10-20); only read-only monitoring by the admin profile stays in.
- Soft-launch safety block (per-link limits, per-conversation AI caps, end rating, drop-off analytics, ~50 testers) —
  removed temporarily by the owner (2026-10-20).
- Any change to the `/happie` webhook or the `happie.v1`/`happie.v2` contracts.
- Client doc exclusions: deep photo reading (reliable element recognition, colour matching, fit-in-venue warnings,
  closest known design); brief → quote, vendor quotes, availability, draft package or cart link (Pilot 2); creating or
  editing images; counting balloons from photos (William's tool); payments; hardened security for a full public
  launch; voice replies; growth dashboard (Pilot 1B).

## Requirements
- R1. When someone opens `/asesor` without a valid advisor session, the system shall show the advisor login and accept
  only the `user` or `admin` credentials; passwords are stored hashed and the session cookie is signed.
- R2. When a conversation starts, the system shall show a short privacy notice and a "versión de prueba" notice before
  the first question, and shall greet warmly asking what is being celebrated and for whom.
- R3. While a conversation is open, the system shall collect, in free conversation (never a form): event type and for
  whom, date and time, city and exact address, venue type, guest count and contact name/phone; plus, when given,
  budget, organiser priority (impress / personalise / simple / best price), brand or vendor requests and notes. It
  shall support birthdays, corporate and school events.
- R4. While a conversation is open, the system shall show progress toward a complete brief, computed from the required
  fields of R3.
- R5. When the customer leaves and returns on the same device, the system shall restore the conversation where it was.
- R6. Every customer and advisor message, photo and brief state shall be persisted in Supabase Postgres.
- R7. When the customer sends a photo (camera or gallery; inspiration or venue), the system shall describe what it sees
  (first look), ask the customer to confirm, and ask what they like and dislike about it; the photo goes to the brief as
  received.
- R8. When the customer sends a voice note, the system shall transcribe it and treat it as the customer's text; the
  advisor always answers in text.
- R9. If the customer does not know what they want, the system shall offer directions from a curated group of 10–15
  decorations (with photo) and themed items Happia sells.
- R10. When a standard Happia package or service fits, the system shall offer it first, with its estimated price from
  the Happia catalogue (read live from the Happia API on each use; when the API fails, no package or catalogue price is
  offered — owner decision D-065, 2026-10-25, replaces the daily cache and fallback list), and only offer what Happia
  vendors can do.
- R11. When the required fields are complete, the system shall show the customer a summary to approve or correct; on
  approval it shall store a one-page brief (photos, likes/dislikes, venue, priorities, budget, requests, proposed
  package) and a vendor version without the customer's name, contact or budget.
- R12. While logged in as `admin`, the user shall see the list of conversations (in progress and finished) with
  progress, status and last advisor question, refreshed every few seconds, and open any conversation's transcript,
  photos and brief (read-only). The `user` account shall not reach these views or APIs.
- R13. If the AI provider fails or times out, the system shall show a retry message without losing the conversation.
- R14. The `/happie` UI, webhook and `happie.v1`/`happie.v2` contracts shall remain byte-for-byte unchanged in behaviour.

## Edge cases & errors
- Customer corrects a field after the summary → summary regenerated, approval required again.
- Customer refuses to give contact/address → brief cannot be approved; advisor explains why it is needed (vendors).
- Invalid or oversize photo/audio → friendly error (reuse 6 MB photo / 60 s audio limits).
- Off-topic or abusive messages → the advisor redirects politely; prompt injection cannot change role or reveal data.
- Happia API down → fallback list; Supabase down → clear error, no silent loss.
- Two tabs on the same conversation → last write wins per message; no duplicates (idempotent message ids).

## Constraints
- Lives in the Pictures repo (Next 16 app, Python ai-api on the VPS, Neon Postgres, S3 Garage on the VPS), deployed to
  Vercel and the VPS through the existing CI gate.
- Personal data (name, phone, address, budget) — Colombian Ley 1581 (habeas data): privacy notice and minimal data.
- Happia Integrations API today exposes paginated `GET /services` and `GET /packages` only (HappiaClient); real prices,
  themed items and carts depend on William's platform session.

## Priorities & phases
- M1 (Must, Halloween Thu 29 Oct): R1–R6, R11, R12, R13, R14 — text conversation → approved brief, admin watching.
- M2 (Must, ~6 Nov): R7, R8 — photos with first look and likes/dislikes, venue photo, voice notes.
- M3 (Must, ~19 Nov): R9, R10 — directions, themed items, standard package first with catalogue price.
- M4: hardening and end-to-end acceptance before the 23 Nov rehearsal.

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
- A1. Model: Gemini (`gemini-3.6-flash`, the production chat model) through `@sempertex/agente-core`; locally the
  existing provider registry (Claude CLI) may be used. Photos go inline to the model for the first look (no blueprint).
- A2. Code from `origin/main` on a new branch/worktree `feat/req-020-asesor-happia`; deploy to Vercel
  (`demo-decoracion`) and the VPS as today, after the green gate (owner authorised production pushes/deploys).
- A3. Separate migrations folder and runner for the Supabase database (never mixed with Neon `schema_migrations`).
- A4. Initial directions: 12 decorations picked from `biblioteca-sempertex/decoraciones.json`, in an editable config
  file Diana can revise later. Fallback price list: a JSON file seeded from the last good catalogue read.
- A5. Account passwords are generated, stored as hashes in Postgres (seed script) and handed to the owner locally.
- A6. Catalogue price = existing estimate (subtotal COP before VAT/commission, with the existing notice).

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear (R1–R14 + plan verification) |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
### Round 2 — 2026-10-20
- Q: Supabase project → A: owner's project `byepzsrbjgvrmsmfuzhj`; Supabase only as an easy Postgres (no Auth, no
  Storage). Verified: transaction pooler works (Postgres 17.11); direct host is IPv6-only.
- Q: Admin login → A: own solution; two accounts, `user` (general) and `admin`, different passwords.
- Q: Monitoring → A: (default) read-only.
- Q: Photos/voice/deploy defaults → A: yes, but photos in Postgres instead of Supabase Storage.
### Round 1 — 2026-10-20
- Q: Route/name → A: "Asesor Happia", `/asesor`.
- Q: Access without the safety block → A: behind the current `APP_PASSWORD`.
- Q: Where are conversation, photos and brief stored → A: browser only for the customer for now; but an admin profile
  must monitor conversations, so they are saved to Postgres on Supabase.
- Q: Brief outputs without Diana's screen → A: customer summary + full brief + vendor version, visible to a new
  "admin" profile whose only extra power is monitoring conversations.
- Q: Halloween milestone → A: yes, M1 = text → brief by 29 Oct. Owner: ask for every connection, key, password and
  credential before starting.

### Round 0 — 2026-10-20 (conversation)
- Q: Modify the `/happie` webhook/contracts? → A: No; build a new "Happia chat v2" section.
- Q: Diana's screen and soft-launch safety? → A: Removed temporarily from this scope.
- Q: Where? → A: Linked to (inside) the Pictures project.
