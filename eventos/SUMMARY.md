# eventos — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex event management system: create and manage events, teams and attendees; record attendance by manager or
QR self check-in; capture signature/photo with facial verification; satisfaction surveys; Excel/PDF reports. Frontend
`FrontSempertexEventos` (Next.js 15) and backend `ViveSempertexEventos` (NestJS 11, MSSQL, SharePoint via Graph) are
built and deployed separately. See ARCHITECTURE.md.

## Current state
Knowledge migrated from Hefesto (2026-10-08; archive at C:/Users/davidt/Desktop/eventos/hefesto). As of the last
Hefesto handoff (2026-09-23): the legacy `PLAN.md` (phases 0–8) was cross-checked against the code — everything is
written but nothing committed (~60 uncommitted files per repo; backend on branch `limpieza-campo-capacidad`, frontend
on `main`). Phases 0, 1, 3, 4 done; 2, 5, 6, 8 nearly; 7 half-done and against its decision (auto re-verification
instead of manual admin resolution). The handoff was picked up by a session on 2026-09-28; nothing after that is
recorded in Hefesto, so verify repo state first. Production operation (deploy, rollback, backups, monitoring) is
undocumented.

## Active focus
- Get the user's approval of the handoff proposal before creating anything.
- Save the in-progress work on a `wip/plan-vive-eventos` branch per repo (no push; leave certs/keys/`.env` out; ask
  about the change in `ViveSempertexEventos/certs/`).
- Then one requirement per PR of `PLAN.md`'s suggested work order (seven), starting with phases 0+1.

## Top pending (see PENDING.md)
- P-001 · Remove secrets from docker-compose and define a secrets manager (high)
- P-002 · Reconcile production MSSQL with the Compose PostgreSQL (high)
- P-003 · Formalize migrations and the real MSSQL schema (high)
- P-004 · Fix event deletion and cleanup of external data (high, bug)
- P-009 · Review protection of signatures and biometric data (high)

## Recent decisions (see DECISIONS.md)
- D-001 · Pending-verification photos are resolved manually by an admin (current code auto re-verifies: must change).
- D-004 · "Legacy" = events before the fixed cutoff 2026-09-07 (replaces PLAN.md's "before yesterday" rule).
- D-006 · `fechaFin` mandatory in DTO + UI, no NOT NULL or backfill.
- D-009 · "Sin acceso" screen lists ADMIN contacts only (PLAN.md had ADMIN + SUPERADMIN).
- D-010 · Half-done work goes on `wip/plan-vive-eventos` per repo (no push, no certs/keys/`.env`).

## Known issues
- Compose starts PostgreSQL but the API needs MSSQL `zeus:1433`; `docker compose up` does not give a working system.
- No migrations (`synchronize:false`, loose SQL script); schema changes need an external procedure.
- Event deletion leaves survey/verification/evidence rows and SharePoint files (P-004).
- AES helper unusable (empty password, `decrypt` returns empty) (P-009).
- CORS open, issuer accepted by prefix, TLS at IIS undocumented (P-006).
- No CI/CD, health check, alerts or documented rollback (P-005).

_Last updated: 2026-10-08_
