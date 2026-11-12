---
id: REQ-031
status: clarifying
created: 2026-11-12
track: deep
---
# REQ-031 — Distributors and MBP tables, sketch cart with simulated Shopify, pending orders answered by WhatsApp, nearest-distributor order e-mail with PDF

## Problem & goal
A person who gets a balloon sketch (web `/boceto` or the WhatsApp assistant) receives a list of balloons and nothing
else: there is no way to buy them. Sempertex has no Shopify connection for this channel and will not have one soon.
The distributor and MBP directories exist only as spreadsheets; the app holds 69 example records.

Goal: the sketch ends in a cart. The person either buys (the order lands in a table; an administrator builds the
real Shopify cart by hand and sends its link back by WhatsApp) or sends the order to a nearby distributor (who gets
it by e-mail as a designed PDF). The product source is the B2B crosswalk JSON today and must be replaceable by a
real Shopify connection without touching the cart.

**Success looks like:** from a finished sketch, on the web and on WhatsApp, a person reaches «pedido recibido» in
under a minute; every order is visible to an administrator with its SKUs; the administrator's link reaches the
person; a distributor order produces an e-mail with a PDF; distributors and MBP are rows an administrator edits.

## Users / actors / stakeholders
- **Person with a sketch** — web account (permission `taller_3d` on `/boceto`) or registered WhatsApp contact
  (`whatsapp_contactos`: name, e-mail, number).
- **Orders administrator** — Sempertex staff with the new orders permission: reads pending orders, builds the Shopify
  cart outside this system, pastes the link, closes the order.
- **Directory administrator** — edits distributors and MBP.
- **Distributor** — receives an order e-mail with a PDF. Has no account.
- **Owner** — David; approves each subplan.

## Scope (in)
### US-1 (P1, Must) — Distributors and MBP in the database
As a directory administrator, I want the two received spreadsheets as tables I can list, search, create, edit and
deactivate, so that the directory is real data and contacts can be completed over time.

### US-2 (P1, Must) — Cart from a sketch
As a person with a sketch, I want its balloon list as a cart of real products with pack quantities and prices that I
can change, so that I can order what the sketch needs.

### US-3 (P1, Must) — Buy: pending order answered with a Shopify link
As a person, I want to press buy and later receive a payment link on WhatsApp; as an orders administrator, I want
the pending orders with their SKUs and a place to paste the link that sends it.

### US-4 (P1, Must) — Send the order to a nearby distributor
As a person, I want to type my address, see the nearest distributors and choose one, so that the distributor
receives my order as a PDF by e-mail.

## Out of scope
- A real Shopify connection (catalogue, cart, checkout, payment webhooks). Only the seam for it.
- Payment, stock, shipping cost, taxes, invoices.
- Meta template messages (needed to write after WhatsApp's 24 h window): proposal, not built.
- Sending anything to a distributor by WhatsApp; distributor accounts or a distributor portal.
- MBP in the nearest search or in the order flow; MBP are only listed and edited.
- Obtaining the Colombian distributors' e-mails and phones (the owner will supply them later).
- The Telegram bot, the Vercel WhatsApp webhook path and the untracked `services/whatsapp-globos` folder.
- Replacing the example directory `proveedores.json` used by the guided chat.

## Requirements
- R1. The system shall store distributors in a Postgres table with name, status, country, region, city, address,
  postcode, latitude, longitude, phone, e-mail, WhatsApp number, website, social links, map groups, tags, source and
  timestamps, and shall import the 670 rows of the received locations export keeping every country and the coordinates.
- R2. The system shall store MBP in a separate Postgres table with name, distributor name, optional link to a
  distributor row, continent, country, city, social links, e-mail, address, phone, event city, event date, year,
  juror, shirt size, birthday, identification number, publication note and timestamps, and shall import the 472 rows
  of the received MBP file (Latin-1, `;` separated, multi-line cells).
- R3. When an import is run again, the system shall add new rows and update unchanged ones without overwriting a row
  an administrator edited by hand, and shall report added, updated, skipped and rejected rows with the reason.
- R4. While signed in with the directory permission, an administrator shall be able to list with paging, search by
  text, filter (country, city, status, has e-mail; for MBP also distributor and year), create, edit and deactivate
  distributors and MBP; without that permission the pages and APIs shall refuse.
- R5. The system shall read products only through one catalogue port; the first adapter shall resolve a sketch line
  (format, Sempertex colour code, balloon count) to a B2B product variant from the crosswalk with its title, pack
  size, packs needed, unit price in COP and, when `catalog_variants` has it, its SKU. A line with no product shall be
  returned as not available with its reason, never dropped silently.
- R6. When a person adds a sketch to the cart, the system shall create or extend that person's cart with one line
  per resolved variant; the person shall be able to change pack quantities, remove lines, empty the cart and see
  each line's price and the total, labelled as reference prices. The cart shall persist on the server per web
  account or WhatsApp contact.
- R7. After a WhatsApp sketch result the assistant shall offer to add it to the cart, and shall let the person see
  the cart, change a quantity, remove a line, empty it, buy, or send it to a distributor, within WhatsApp's limits
  (3 buttons, 10 list rows).
- R8. When a person buys, the system shall create an order in state `pending` with an immutable snapshot of the
  lines (variant id, SKU, title, packs, units, unit price, total), the channel, the sketch reference and the contact
  (name, e-mail, WhatsApp number when known), empty the cart and tell the person an adviser will send the link.
- R9. While signed in with the orders permission, an administrator shall be able to list orders by state, open one,
  copy its SKUs and quantities, paste a Shopify link and send it. If the person's last WhatsApp message to the
  assistant is under 24 h old the link shall go by WhatsApp from the assistant's number; otherwise it shall go to
  the person's e-mail. The panel shall show which route was used and any delivery failure.
- R10. The administrator shall be able to mark an order as paid or cancelled; a paid or cancelled order is closed
  and accepts no more sends. Every state change shall record who and when.
- R11. When a person chooses to send the cart to a distributor and types an address, the system shall geocode it
  through a geocoding port (first adapter: OpenStreetMap Nominatim), and return up to five active Colombian
  distributors ordered by straight-line distance, with name, address, city and distance. If the address is not
  found the system shall ask for the city and list that city's distributors.
- R12. When the person chooses a distributor, the system shall create an order of kind `distributor`, generate a
  PDF and e-mail it: to the distributor's e-mail when the row has one, with the configured fixed mailbox in copy;
  to the fixed mailbox alone when it has none. While no fixed mailbox is configured and the distributor has no
  e-mail, the order shall be recorded as `not sent: no recipient`, shown as such to administrators, and resendable.
- R13. The PDF shall carry the Sempertex brand, order number and date, the person's name and contact, the
  distributor's name and address, a table of products (colour swatch and name, format, SKU, packs, units, reference
  price) with the total, and the sketch image when one exists.
- R14. The e-mail adapter shall accept attachments.
- R15. After a distributor order the person shall receive the distributor's name, address and a map link, and be
  told their name and contact were shared with that distributor; before sending, the person shall be shown that
  notice and confirm.
- R16. Phone numbers and e-mails shall not be written to logs; every external call (geocoder, e-mail, WhatsApp)
  shall have a deadline and a recorded failure state; each part shall sit behind a flag that defaults to off in
  production.

## UI / design contract
- UI scope / users: (a) administration of distributors and MBP; (b) cart on `/boceto`; (c) orders panel;
  (d) address, distributor choice and confirmation on the web; (e) the order PDF. WhatsApp screens are copy only.
- Visual direction / existing system: the app's shell and `@bitacora/ui` (project opted in); administration pages
  follow `/admin/roles` and `/admin/subidas`. Spanish and English as the rest of the pilot.
- Accessibility or interaction constraints: phone first for the cart and the distributor flow; keyboard and screen
  reader labels on tables and dialogs.

## Edge cases & errors
- Sketch line without product (39 known gaps) → shown in the cart as not available; buying is allowed with the rest.
- Empty cart → buy and send are disabled. Two sketches in one cart → lines of the same variant add up.
- Crosswalk price or product changed after the order → the order keeps its snapshot.
- Person on the web without a WhatsApp number → asked for it at buy; link goes by e-mail unless that number wrote to
  the assistant in the last 24 h.
- WhatsApp send refused by Meta (window closed between check and send) → falls back to e-mail, recorded.
- Geocoder down, slow or ambiguous → city question; city unknown → nearest by the city's own coordinates when the
  directory has it, else «no encontramos puntos cerca» with the option to buy instead.
- Distributor row without coordinates (1 of 670) or inactive → never offered.
- Double tap on buy/send → one order (idempotency key).
- Import: duplicate rows, rows without name, broken encoding → rejected and reported, import continues.

## Constraints
- Repository `pictures` (Next 16 on Vercel, Postgres through `pg`, raw SQL, migrations `scripts/migrations/NNN_*.sql`,
  next free number 066); live WhatsApp assistant is `services/telegram-globos` on VPS `advin`, own role `whatsapp_bot`.
- AGENTS.md: features under `src/features/<name>/{domain,application,infrastructure,presentation}`; handlers only
  authenticate, authorise, validate and call a use case; zod at boundaries; catalogue data is authoritative for
  prices; additive migrations with rollback; UI from `@bitacora/ui`; every route in `MAPA_PERMISOS_RUTAS`.
- MBP rows hold personal data (birthday, identification number, address): directory permission only, never sent to
  a model, never logged.
- Nominatim usage policy: one request per second, identified client, results cached.
- Production changes need a database backup first; nothing reaches `main` before its subplan is approved.

## Priorities & phases
Must: US-1 to US-4. MVP order: directory (M1) → cart and buy (M2, M3) → distributor (M4). Later (proposals): Meta
templates, real Shopify adapter, distributor WhatsApp, MBP in the flow.

## Timeline & dependencies
- No date given. Depends on the owner for: the fixed mailbox address (R12), the Colombian distributors' contacts,
  Resend sender domain already verified.

## Assumptions
- A1. «BTB JSON» is `src/lib/globos3d/motor/datos/crosswalk-vigente.json` (owner, round 1).
- A2. Prices shown are the crosswalk's B2B prices in COP, labelled «precio de referencia» (owner chose prices; the
  label is mine: the real cart is built by hand and may differ).
- A3. The fixed mailbox is an environment value left empty until the owner supplies it (owner: «haz la
  configuración, luego conseguimos los correos»); R12 covers the empty case.
- A4. The address is typed (owner, round 1); the WhatsApp location pin and browser geolocation are not built.
- A5. Nearest search covers Colombia only: the 596 Colombian rows; international rows are stored and editable.
- A6. Web cart requires a signed-in account (the page already does); no anonymous cart.
- A7. «Cuando se haga efectiva la compra, muere» = the administrator marks the order paid and it closes; nothing
  detects the payment automatically.
- A8. Orders and carts live in Postgres so the Vercel panel and the VPS assistant share them; `whatsapp_bot` gets
  grants only on the cart and order tables it needs.

## Inputs
Locations only, never values. Empty Subplan = plan-wide.

| Item | Subplan | Where it lives | Supplier | Status |
|---|---|---|---|---|
| Locations export CSV | SP-1 | `~/recibidos/distribuidores/locations-export-1793894386941.csv` | Owner | available |
| MBP CSV | SP-1 | `~/recibidos/distribuidores/MBP BASE DE DATOS -educacion(OK).csv` | Owner | available |
| Fixed mailbox for distributor orders (may stay empty: R12 covers it) | SP-7 | env `PEDIDOS_DISTRIBUIDOR_CORREO` (Vercel and `/etc/pictures-whatsapp/whatsapp.env`) | Owner | available |
| Resend key and sender | SP-6, SP-7 | env `RESEND_API_KEY`, `CORREO_REMITENTE` (already in Vercel) | Operator | available |
| Meta token for sends from the panel | SP-6 | the assistant's env on the VPS; the panel calls the assistant with `BOT_SERVICE_SECRET` | Operator | available |

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Partial (per subplan) |
| Edge cases | Partial (per subplan) |
| Acceptance criteria | Partial (per subplan) |
| Constraints | Clear |
| UI / design direction | Partial (per subplan) |
| Priorities & phases | Clear |
| Timeline | Deferred (no date) |

## Clarifications
### Round 1 — 2026-11-12
- Q: Which JSON is «BTB»? → A: the crosswalk.
- Q: Does the cart show prices? → A: yes.
- Q: Where does a distributor order go, given that Colombian distributors have no e-mail or phone? → A: build the
  configuration now; the e-mails come later.
- Q: How is the address turned into coordinates? → A: the person types the address (OpenStreetMap geocoding).
- Q: How does the administrator answer with the link? → A: from the panel through the assistant's number within
  24 h, otherwise by e-mail.
