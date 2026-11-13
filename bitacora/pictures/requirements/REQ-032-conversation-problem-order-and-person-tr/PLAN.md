---
req: REQ-032
status: done
created: 2026-11-13
---
# Plan — REQ-032 — Conversation, problem, order and person tracking (WhatsApp bot, web assistant, orders)

## Approach
One append-only event table in the existing Postgres (`seguimiento_eventos`) plus a small problems-state table (`seguimiento_problemas`). The bot tees its existing `log` events and its inbound customer texts into a bounded async queue (never blocks, drops on failure). The web admin reads them through new permission-guarded API routes and pages under `/admin/seguimiento`; problems are derived by queries over events and orders, with reviewed/resolved state stored separately. Alternative rejected: shipping `docker logs` to a log stack (more infrastructure, no link to orders/people).

## Global constraints
- Admins only; `no-store`; texts ≤ 1000 chars, masked, 90-day expiry. No bot replies, images or keys stored.
- Never block or fail a customer turn because tracking failed (R3).
- Additive migration, production only after a backup; rollback drops the new tables.
- Follow AGENTS.md: handlers validate and call use cases; UI from `@bitacora/ui`; tests for contracts and permissions.

## Tasks

### M1 — Event store and writer
- [ ] T1 — Migration 071 `seguimiento_eventos` + `seguimiento_problemas` with indexes and grants · kind: implement · files: scripts/migrations/071_seguimiento.sql · verify: `npm run rag:migrate -- --dry-run` · covers: R2, R7, R8
- [ ] T2 — Event contract (zod), classifier (log event → type/severity/step), text masking · kind: implement · files: src/features/tracking/domain/** · verify: `npx tsx --test src/features/tracking/**/*.test.ts` · covers: R1, R2
- [ ] T3 — Bot writer: bounded queue, deadline, drop counter, conversation id (6 h rule) · kind: implement · files: services/telegram-globos/src/seguimiento/** · after: T1, T2 · verify: `npm test -w services/telegram-globos -- seguimiento` · covers: R3, R4

### M2 — Bot instrumentation
- [ ] T4 — Tee `log` into the writer; record inbound texts; link `pedido_id` on order events · kind: implement · files: services/telegram-globos/src/** · after: T3 · verify: `npm test` in services/telegram-globos · covers: R1, R2, R6
- [ ] T5 — Disposable-DB integration test: a sketch + count + order produces the expected timeline; a dead DB does not break a turn · kind: implement · after: T4 · verify: `REQ031_TEST_DATABASE_URL=… npm test` · covers: R3, R6

### M3 — Admin API and UI (timeline, person)
- [ ] T6 — Author UI contract seguimiento@v1 (list, timeline, person page, states) · kind: design · subplan: ui-seguimiento · files: design/contracts/seguimiento@v1.md · covers: R5
- [ ] T7 — Read APIs: conversations list, person timeline, person summary (permission, no-store, pagination, zod) · kind: implement · after: T1 · files: src/app/api/admin/seguimiento/** · verify: `npx tsx --test src/features/tracking/**/*.test.ts` · covers: R5, R6
- [ ] T8 — Pages `/admin/seguimiento` (Conversaciones) and Persona, linked from `/admin/whatsapp` and `/admin/pedidos` · kind: implement · subplan: ui-seguimiento · ui: true · after: T6, T7 · verify: `npx tsc --noEmit` · covers: US-1, US-3
- [ ] T9 — Review rendered UI against seguimiento@v1 · kind: audit · subplan: ui-seguimiento · review_axis: visual · after: T8

### M4 — Problems
- [ ] T10 — Derived problems queries (errors, stuck orders, stuck/abandoned conversations, limits), grouping, reviewed/resolved state API · kind: implement · after: T7 · verify: `npx tsx --test src/features/tracking/**/*.test.ts` · covers: R7, R8
- [ ] T11 — Problems page with filters, counts, links, review/resolve with note · kind: implement · subplan: ui-seguimiento · ui: true · after: T6, T10, T8 · covers: US-2

### M5 — Web assistant and retention
- [ ] T12 — Explore and instrument web assistant / counter / sketch events with account id (`canal = 'web'`) · kind: implement · after: T7 · covers: R10, US-4
- [ ] T13 — Retention job: clear texts > 90 days (idempotent, bounded, logged), scheduled · kind: implement · after: T1 · verify: `npx tsx --test src/features/tracking/**/*.test.ts` · covers: R9, US-5

### M6 — Release
- [ ] T14 — Production: backup, apply 071 alone, grant to bot role, deploy web (push to main) and bot; smoke check with the owner's own number · kind: implement · after: T5, T9, T11, T12, T13 · covers: all
- [ ] T15 — Independent audit of the consolidated diff (privacy: masking, permission, retention; reliability: non-blocking) · kind: audit · after: T14

## Verification
Bot suite and tracking tests green; with a disposable DB, a scripted conversation yields timeline + problems as specified; admin without permission gets 403 on every route; killing the DB leaves bot replies unaffected; texts older than 90 days are NULL after the job; production smoke with the owner's number shows the timeline within seconds.

## Rulings
<!-- Judgment calls made during execution without asking. -->

## Progress log
- 2026-11-13: spec and plan written from the owner's four answers (events + texts 90 d; bot errors, stuck orders, stuck customers; admins only; WhatsApp bot + both channels' orders + web assistant). Awaiting plan approval.
- 2026-11-13: built manually in one session (owner: no methodology flow). Shipped as main c57a554fa + migration 071; see the pictures day log.
