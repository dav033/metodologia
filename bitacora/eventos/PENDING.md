# eventos — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._

## Open
- P-001 · Remove secrets from docker-compose and define a secrets manager · urgency: high · complexity: ? · added 2026-09-23 · hefesto N001
  - Remove embedded DB credentials from `ViveSempertexEventos/docker-compose.yml`, rotate them if used outside local, define per-environment injection. Deferred until the secrets provider/owner is confirmed.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N001-retirar-secretos-compose-y-definir-gestor.md
- P-002 · Reconcile production MSSQL with the Compose PostgreSQL · urgency: high · complexity: ? · added 2026-09-23 · hefesto N002
  - API uses MSSQL `zeus:1433`; Compose starts PostgreSQL on 5434 that no code uses. Needs a human decision on the official engine and what Compose is for.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N002-reconciliar-mssql-de-produccion-con-postgresql-de-compose.md
- P-003 · Formalize migrations and the real MSSQL schema · urgency: high · complexity: ? · added 2026-09-23 · hefesto N003
  - Turn `db/2026-09-verificacion-encuesta-evidencias.sql` and the existing `GESTION_HUMANA` schema into versioned, auditable migrations with rollback/restore. Needs schema inventory + change control for the shared DB.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N003-formalizar-migraciones-y-esquema-real-de-mssql.md
- P-004 · [bug] Fix event deletion and cleanup of external data · urgency: high · complexity: ? · added 2026-09-23 · hefesto N004
  - `DeleteEvent` removes attendees, managers, trainers and event but not surveys, pending verifications, evidence (FKs to the event) nor SharePoint files. Deferred until retention/deletion of personal data and files is decided.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N004-corregir-borrado-de-eventos-y-limpieza-de-datos-externos.md
- P-005 · Define deploy, rollback, backups, health checks and alerts · urgency: high · complexity: ? · added 2026-09-23 · hefesto N005
  - Commit→production path, coordinated code/DB rollback, restorable backups, health checks, alerts. Deferred until documented environment access exists; never write to or change production.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N005-definir-despliegue-rollback-backups-healthchecks-y-alertas.md
- P-006 · Harden CORS, TLS, issuer and service exposure · urgency: high · complexity: ? · added 2026-09-23 · hefesto N006
  - Restrict CORS origins, verify TLS at the IIS edge, review accepted issuer prefixes, limit port exposure. Deferred until official domains, tenants and TLS termination are confirmed; no security changes by inference.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N006-endurecer-cors-tls-issuer-y-exposicion-de-servicios.md
- P-009 · Review protection of signatures and biometric data · urgency: high · complexity: ? · added 2026-09-23 · hefesto N009
  - AES helper has an empty password and `decrypt` returns nothing; images live outside the DB. Deferred until legal requirements, retention and recovery are defined.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N009-revisar-proteccion-de-firmas-y-datos-biometricos.md
- P-007 · Pin dependency, image and runtime versions · urgency: med · complexity: ? · added 2026-09-23 · hefesto N007
  - `^` ranges and `postgres:latest`; pin Node/PM2/IIS/packages and add an update policy once a compatible runtime matrix is agreed.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N007-fijar-versiones-dependencias-imagen-y-runtime.md
- P-008 · Split modules over the size threshold (400 lines in Hefesto) · urgency: med · complexity: ? · added 2026-09-23 · hefesto N008
  - Prerequisite before new feature work in `EventoService`, `AsistenteService`, management/PDF pages (e.g. `src/app/Evento/gestionar/[id]/page.tsx`, 1248 lines).
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N008-dividir-modulos-que-superan-400-lineas.md

## Blocked
_None_

## Recently closed
_None_

## Notes
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._
