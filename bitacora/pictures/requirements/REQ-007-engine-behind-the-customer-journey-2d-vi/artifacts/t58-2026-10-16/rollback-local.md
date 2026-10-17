# Local rollback drill — T58 — 2026-10-16

- Target: disposable PostgreSQL `pgvector/pgvector:pg16`, container `pictures-t58-postgres`, bound only to `127.0.0.1:5435`, no volume, `--rm` lifecycle. Only migration `032_ajustes_runtime.sql` was applied.
- Production Neon was not queried or modified. The running Python service on port 8000 was left untouched. No provider or paid call was made.
- Starting row: `ajustes_runtime.guiada_motor=python`.
- Flip: updated the local row to `3d`; with environment `GUIADA_MOTOR=python`, the actual `leerMotorGuiada()` resolver returned `{"motor":"3d","fuente":"ajuste"}`. This verifies that the database row overrides the environment.
- Restore: updated the local row to `python`; with environment `GUIADA_MOTOR=3d`, the resolver returned `{"motor":"python","fuente":"ajuste"}`.
- Final row: `guiada_motor=python`, written by `t58-local-drill-restore`.
- Teardown: stopped the disposable container after the drill; `--rm` removed it and released port 5435. The local Next dev server on 3015 was also stopped. Port 8000 remained listening.

This drill proves the flag precedence and local flip/restore path. It is not a production write, multi-instance propagation measurement, or a timing test of the 30-second cache.
