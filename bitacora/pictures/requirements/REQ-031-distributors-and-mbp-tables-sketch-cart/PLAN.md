---
req: REQ-031
status: draft
created: 2026-11-12
---
# Plan — Distributors and MBP tables, sketch cart, pending orders and distributor order e-mail

Skeleton (collaborative planning, phase Esqueleto). Milestones and subplans only; tasks are defined subplan by subplan.

## Approach
One new feature folder per concern (`src/features/directory`, `src/features/cart-orders`), Postgres tables shared by
the Vercel app and the VPS assistant, and three ports so sources can change later: product catalogue (crosswalk now,
Shopify later), geocoder (Nominatim now) and outbound message (WhatsApp or e-mail). The WhatsApp assistant
(`services/telegram-globos`) reuses the same application use cases through the database; it never duplicates rules.
Each subplan lands behind its own flag, off in production until the owner approves it.

## Global constraints
AGENTS.md of `pictures`; additive migrations from 066 with rollback; every route in `MAPA_PERMISOS_RUTAS`; no phone or
e-mail in logs; MBP personal data only under the directory permission; production database backup before migrating;
nothing reaches `main` before its subplan is approved.

## Tasks

### M1 — Directory: distributors and MBP as editable data
The two received spreadsheets are rows in Postgres and an administrator lists, searches, creates, edits and deactivates them.

- **SP-1 — Distributor and MBP tables and import**: Postgres holds the 670 points of sale with coordinates and the 472 MBP; a repeatable import command reports added, updated, skipped and rejected rows and never overwrites a hand-edited row.
- **SP-2 — Directory administration screens**: an administrator with the directory permission lists, searches, filters, creates, edits and deactivates distributors and MBP from Administración.

### M2 — Cart from a sketch
A finished sketch becomes a cart of real B2B products with packs and reference prices, on the web and on WhatsApp, and «buy» leaves a pending order.

- **SP-3 — Catalogue port, cart and orders core**: one catalogue port (crosswalk adapter, SKU from `catalog_variants`) turns sketch lines into product lines; carts and orders persist in Postgres with an immutable order snapshot; buy is idempotent.
- **SP-4 — Cart on the web sketch**: on `/boceto` a person adds the sketch to the cart, changes packs, removes lines, sees prices and total, and buys.
- **SP-5 — Cart in the WhatsApp assistant**: after a sketch result the assistant offers the cart; the person views it, changes it and buys without leaving the chat.

### M3 — Pending orders answered with a link
An administrator works the pending orders and the person receives the Shopify link.

- **SP-6 — Orders panel and link reply**: an administrator with the orders permission lists orders, copies SKUs, pastes the Shopify link and sends it (WhatsApp inside 24 h, otherwise e-mail), and marks orders paid or cancelled.

### M4 — Order to a nearby distributor
A person types an address, picks one of the nearest distributors and that distributor (or the fixed mailbox) receives the order as a PDF.

- **SP-7 — Nearest distributors, order PDF and e-mail**: typed address → up to five nearest active Colombian distributors; a distributor order produces the designed PDF and an e-mail with it attached, routed by the recipient rule, with the «no recipient» state when nothing is configured.
- **SP-8 — Distributor flow on the web and WhatsApp**: from the cart, on both surfaces, the person types the address, chooses a distributor, confirms the data-sharing notice and gets the distributor's name, address and map link.

## Verification
Per subplan, in SPEC `## Pruebas` (written when each subplan is in focus).

## Rulings

## Progress log
