---
id: REQ-006
status: in-progress
created: 2026-11-08
track: standard
---
# REQ-006 — Luis Lozano automation backlog (14 tasks, MCP capabilities)

## Problem & goal
Five emails from Luis Lozano (owner, `llozano@marosconstruction.com`, Maros user id 1) were decomposed by the owner's assistant into 14 tasks. They are **our decomposition, not 14 confirmed commissions**. Goal: give Claude concrete, validated tools in the MAROS MCP (instead of visual automation or manual steps) for invoices, reports and email drafts, and coordinate the human-dependent items.

**Success looks like:** Claude can find invoices by project/vendor, file them under a standard name, save weekly reports to Drive and leave Gmail drafts with the right PDF attached, with no send/modify/delete capability beyond each tool's scope.

## Scope (in) — status per task (2026-11-08)
Phase 1 (agent-built, `maros-nest`, MCP):
- T1 Unify the two daily Claude tasks — **open** (needs the current Claude scheduled-task configs).
- T2 Standard names `Proyecto-Proveedor-Valor.pdf` — **done and verified live with a real 064P Lion invoice -> `064P-LionPlumbingSupply-980.89.pdf`** (`bb1db26e`): short project code, PascalCase vendor, 2 decimals, non-USD suffixed; missing field aborts and names it; collisions numbered `-2`, `-3`, never overwritten.
- T3 Save JFB weekly reports to Drive — **done in code**: `save_report_to_drive` with `addDate`, create-only, folder `Maros/Reports/<sub>`; **verified live 2026-11-08** (dated name, same key does not duplicate, repeated name becomes `-2`).
- T4 Gmail drafts with PDFs — **done in code**: `create_draft_with_attachment` accepts a Drive file id (only files the app saved: `drive.file`), an invoice scan or inline base64; never sends; **verified live** (correct PDF attached, message stays DRAFT, a file the app did not create is refused with a clear message). Limitation: forms Claude saved with its own Drive connector are invisible to the app; they must be saved through `save_report_to_drive` or the scope widened (owner decision).
- T5 Gmail label -> Receipts — **blocked on decision**: reading mail needs `gmail.readonly` (restricted scope on the whole mailbox) or an Apps Script running inside Luis's account limited to one label (recommended).
- T6 Central invoice index — **partial**: `invoice_scans` is the index (project, vendor, total, dates, status, file) but has no Drive link, location state ("in Receipts / categorised / moved") or history. Needs a migration (owner applies SQL by hand, see P-010/P-012 convention).
- T7 Search by project/vendor — **done** (`f0a2155`, `search_invoices`).
- T8 Expose through the MCP — **done for T3/T4/T7 and the naming of T2**; remaining tools follow T5/T6.
Phase 2 (human): T9 Chase alerts, T10 QuickBooks bank reconnections (Chase, Business Gold 1008 err 324, Home Depot Pro Xtra err 108), T11 restricted Drive permissions (largely satisfied by `drive.file` + create-only tools), T12 Claude in Chrome / local folders.
Phase 3: T13 QuickBooks For Review queue (investigate API; read-only), T14 WhatsApp Business with human approval.

## Constraints and decisions
- QuickBooks stays READ-ONLY for the For Review queue (T13 acceptance: Claude cannot categorise or modify). The owner answered "todas" to "which QuickBooks writes?"; that conflicts with T13 and is **not acted on** until he names concrete writes.
- Actor for Google tools: Luis Lozano (user id 1). His stored Google token only has `calendar.events`; he must reconnect via `https://api.marosconstruction.com/api/google-calendar/connect?returnTo=/calendar` (the UI hides the connect button once Calendar is connected).
- See D-007 (scopes) and D-008 (naming).

## Open questions
- T5: Apps Script in Luis's account (recommended) vs `gmail.readonly` in the app.
- T4: widen to `drive.readonly` (restricted scope) to attach files Claude saved through its own connector, or keep `drive.file`.
- T6: approve a migration for Drive link, state and history.
- QuickBooks: which writes, if any.
