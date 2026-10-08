# eventos — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — Cross-verification: pending photo with manual resolution by an administrator
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** When the facial-recognition service fails, the manager still needs to record attendance (PLAN.md phase 7). The 2026-09-23 cross-check found the half-done code re-verifies automatically, against this decision.
- **Decision:** The photo goes to SharePoint plus a row in the pending table (`EVENTOS_VERIFICACION_PENDIENTE`); an ADMIN/SUPERADMIN approves or rejects it **manually**. While pending: attendance marked, signature + timestamp stored, `Firmado = 0`. Approve → `Firmado = 1` and image moved to `Eventos/{evento}/Asistentes/`; reject → attendance and signature cleared in one `UPDATE`, row `RECHAZADA`.
- **Alternatives:** automatic re-verification (what the half-done code does) — rejected by the user on 2026-09-23.
- **Consequences:** + attendance is not lost when the face service is down / − needs admin follow-up; the table stores only the final state, not who resolved it or when.
- **Source:** C:/Users/davidt/Desktop/eventos/PLAN.md § "Decisiones ya cerradas con el usuario" and § "Fase 7"; C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md

## D-002 — Satisfaction survey answered by each attendee after QR check-in
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** Events need satisfaction feedback (PLAN.md phase 6).
- **Decision:** Each attendee answers right after marking attendance by QR self check-in; optional ("Ahora no"); one answer per event and person (unique index), idempotent; requires marked attendance (otherwise 403).
- **Alternatives:** not recorded.
- **Consequences:** + inline step, no extra call (`selfCheckin` returns `encuestaRespondida`) / − no admin summary view of surveys (open point; a separate phase if wanted).
- **Source:** C:/Users/davidt/Desktop/eventos/PLAN.md § "Decisiones ya cerradas con el usuario" and § "Fase 6"; C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md

## D-003 — Legacy report: coordinator fills the Trainer block only when no trainer is assigned
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** Legacy training events lack an assigned trainer, which breaks the efficacy blocks of the PDF report (PLAN.md phase 4).
- **Decision:** For a legacy training event **without** an assigned trainer, the coordinator goes into the *Capacitador* block and *Responsable evaluación de eficacia* stays empty (filled by hand in the PDF). With an assigned trainer, or for non-legacy events, behavior is unchanged.
- **Alternatives:** not recorded.
- **Consequences:** + legacy reports can be completed / − PDFs already uploaded to SharePoint are not rewritten (accepted risk).
- **Source:** C:/Users/davidt/Desktop/eventos/PLAN.md § "Decisiones ya cerradas con el usuario", § "Fase 4" and § "Riesgos aceptados"; C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md

## D-004 — "Legacy" means events before the fixed cutoff 2026-09-07
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** D-003 needs a definition of a legacy event.
- **Decision:** An event is legacy if it is before the fixed cutoff date 2026-09-07.
- **Alternatives:** PLAN.md's `esEventoLegacyParaEficacia` rule (start date earlier than yesterday, `America/Bogota`) — replaced by the user's fixed cutoff.
- **Consequences:** + stable classification that does not shift with time / − the phase 4 helper must use the cutoff, not the "before yesterday" rule.
- **Source:** C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md; C:/Users/davidt/Desktop/eventos/hefesto/bitacora/2026-09-23.md

## D-005 — Report observations are not persisted; only ADMIN/SUPERADMIN can write them
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** The PDF field `observaciones` is hard-coded to "No aplica" (PLAN.md phase 2).
- **Decision:** Observations are a field of the report-generation form (`ReportePreviewModal`), written straight into the PDF at generation; no DB column, endpoint or history. Visible/editable only for ADMIN/SUPERADMIN; default "No aplica".
- **Alternatives:** a DB column (earlier version of the plan; dropped, so phase 2 no longer depends on phase 0).
- **Consequences:** + no schema change / − text is lost if the modal closes without generating; no record of who wrote it or when.
- **Source:** C:/Users/davidt/Desktop/eventos/PLAN.md § "Decisiones ya cerradas con el usuario" and § "Fase 2"; C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md

## D-006 — End date (fechaFin) mandatory in DTO + UI, without NOT NULL or backfill
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** Events must have an end date (PLAN.md phases 0–1); the range check existed only in the frontend.
- **Decision:** `fechaFin` required in the backend DTOs and the UI, with server-side range validation (`assertRangoFechasValido`); the column stays nullable in `EVENTOS_EVENTO`.
- **Alternatives:** `ALTER COLUMN ... NOT NULL` + backfill — rejected to avoid a schema lock on `EVENTOS_EVENTO` and rewriting historical event dates.
- **Consequences:** + effective for every new write / − old rows keep a null `fechaFin`; read code and reports must keep tolerating it (accepted risk).
- **Source:** C:/Users/davidt/Desktop/eventos/PLAN.md § "Decisiones ya cerradas con el usuario", § "Fase 0", § "Fase 1" and § "Riesgos aceptados"; C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md

## D-007 — External trainer position shown as "Capacitador externo · {empresa}"
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** The report must show the company of an external trainer (PLAN.md phase 4).
- **Decision:** Internal → `cargo`; external with company → `Capacitador externo · {empresa}`; external without company → `Capacitador externo`. Written with `setFieldFitWidth`; company truncated with ellipsis only as a last resort.
- **Alternatives:** not recorded.
- **Consequences:** + no overflow in the PDF field / − long company names may be truncated.
- **Source:** C:/Users/davidt/Desktop/eventos/PLAN.md § "Decisiones ya cerradas con el usuario" and § "Fase 4"; C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md

## D-008 — Evidence photo origin: UI guarantee plus minimal server validations, no cryptographic signature
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** Event evidence photos (max 3 per event, 5 MB each) must be taken in the app (PLAN.md phase 8).
- **Decision:** The client only allows `CameraCapture` (no file input). The server checks permission, size ≤ 5 MB, mimetype + magic bytes (JPEG/PNG), `capturadaAt` within 10 minutes, rejects JPEG with EXIF, generates the file name, and records `subidaPor`/`created_at`.
- **Alternatives:** cryptographic signature of the capture — not adopted.
- **Consequences:** + cheap content/path integrity / − origin is heuristic: someone with a session and `curl` can still post an arbitrary image (accepted risk).
- **Source:** C:/Users/davidt/Desktop/eventos/PLAN.md § "Decisiones ya cerradas con el usuario", § "Fase 8" and § "Riesgos aceptados"; C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md

## D-009 — "Sin acceso" screen lists ADMIN contacts only
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** Users without access need to know whom to ask (PLAN.md phase 3: endpoint outside `AccesoGuard` returning only name + email).
- **Decision:** The contact list shows only ADMIN users.
- **Alternatives:** PLAN.md phase 3 returned ADMIN and SUPERADMIN — narrowed by the user on 2026-09-23.
- **Consequences:** + minimal exposure to unauthorized users / − phase 3 code and tests must exclude SUPERADMIN.
- **Source:** C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md; C:/Users/davidt/Desktop/eventos/PLAN.md § "Fase 3"

## D-010 — Save half-done work on a wip branch per repo
- **Date:** 2026-09-23 · **Status:** Accepted
- **Context:** All PLAN.md phases were written but uncommitted (~60 files per repo).
- **Decision:** Commit the in-progress work on a `wip/plan-vive-eventos` branch in each repo, without attribution, no push, `main` untouched; leave certificates, keys and `.env` out.
- **Alternatives:** not recorded.
- **Consequences:** + work is safe and reviewable per PR / − the `ViveSempertexEventos/certs/` change must be clarified with the user first. Whether this was carried out after 2026-09-23 is not recorded.
- **Source:** C:/Users/davidt/Desktop/eventos/hefesto/traspasos/2026-09-23-1710.md; C:/Users/davidt/Desktop/eventos/hefesto/bitacora/2026-09-23.md
