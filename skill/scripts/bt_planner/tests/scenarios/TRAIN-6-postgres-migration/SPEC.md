# TRAIN-6 — Move the Training API persistence from SQLite to PostgreSQL

The API stores projects and assets in SQLite through `better-sqlite3` (synchronous), with schema migration by
`PRAGMA user_version`, JSON validity enforced by a CHECK, consistent copies taken with `db.backup`, and a Docker/EC2
deployment that mounts the database file. Move persistence to PostgreSQL without losing data or availability.

## Requirements
- R1. All existing data is migrated and verified (row counts and content hashes).
- R2. The API behaves identically for clients, including revision conflicts.
- R3. Backups and rollback keep working on the new store.
