# eventos — Pending

_One line per item: `P-001 · title · priority (high/med/low) · added YYYY-MM-DD · source`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Now
- P-001 · Remove secrets from docker-compose and define a secrets manager · high · added 2026-09-23 · hefesto N001
  - Remove embedded DB credentials from `ViveSempertexEventos/docker-compose.yml`, rotate them if used outside local, define per-environment injection. Deferred until the secrets provider/owner is confirmed.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N001-retirar-secretos-compose-y-definir-gestor.md
- P-002 · Reconcile production MSSQL with the Compose PostgreSQL · high · added 2026-09-23 · hefesto N002
  - API uses MSSQL `zeus:1433`; Compose starts PostgreSQL on 5434 that no code uses. Needs a human decision on the official engine and what Compose is for.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N002-reconciliar-mssql-de-produccion-con-postgresql-de-compose.md
- P-003 · Formalize migrations and the real MSSQL schema · high · added 2026-09-23 · hefesto N003
  - Turn `db/2026-09-verificacion-encuesta-evidencias.sql` and the existing `GESTION_HUMANA` schema into versioned, auditable migrations with rollback/restore. Needs schema inventory + change control for the shared DB.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N003-formalizar-migraciones-y-esquema-real-de-mssql.md

## Next
- P-005 · Define deploy, rollback, backups, health checks and alerts · high · added 2026-09-23 · hefesto N005
  - Commit→production path, coordinated code/DB rollback, restorable backups, health checks, alerts. Deferred until documented environment access exists; never write to or change production.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N005-definir-despliegue-rollback-backups-healthchecks-y-alertas.md
- P-006 · Harden CORS, TLS, issuer and service exposure · high · added 2026-09-23 · hefesto N006
  - Restrict CORS origins, verify TLS at the IIS edge, review accepted issuer prefixes, limit port exposure. Deferred until official domains, tenants and TLS termination are confirmed; no security changes by inference.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N006-endurecer-cors-tls-issuer-y-exposicion-de-servicios.md
- P-007 · Pin dependency, image and runtime versions · med · added 2026-09-23 · hefesto N007
  - `^` ranges and `postgres:latest`; pin Node/PM2/IIS/packages and add an update policy once a compatible runtime matrix is agreed.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N007-fijar-versiones-dependencias-imagen-y-runtime.md
- P-008 · Split modules over the size threshold (400 lines in Hefesto) · med · added 2026-09-23 · hefesto N008
  - Prerequisite before new feature work in `EventoService`, `AsistenteService`, management/PDF pages (e.g. `src/app/Evento/gestionar/[id]/page.tsx`, 1248 lines).
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N008-dividir-modulos-que-superan-400-lineas.md
- P-009 · Review protection of signatures and biometric data · high · added 2026-09-23 · hefesto N009
  - AES helper has an empty password and `decrypt` returns nothing; images live outside the DB. Deferred until legal requirements, retention and recovery are defined.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N009-revisar-proteccion-de-firmas-y-datos-biometricos.md

## Blocked
_None_

## Problems / known bugs
- P-004 · Fix event deletion and cleanup of external data · high · added 2026-09-23 · hefesto N004
  - `DeleteEvent` removes attendees, managers, trainers and event but not surveys, pending verifications, evidence (FKs to the event) nor SharePoint files. Deferred until retention/deletion of personal data and files is decided.
  - archive: C:/Users/davidt/Desktop/eventos/hefesto/pendientes/N004-corregir-borrado-de-eventos-y-limpieza-de-datos-externos.md

## Recently closed
_None_
