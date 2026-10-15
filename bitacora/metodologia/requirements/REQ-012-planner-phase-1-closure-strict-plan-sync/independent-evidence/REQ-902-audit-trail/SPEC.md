# SPEC — REQ-902 Lead status audit trail (Maros)

## Entity

The main business entity with a status workflow is the **lead** (`LeadStatus` pipeline: contacted, proposal sent,
won, lost...). Projects are born from a lead that becomes WON and are not the pipeline. Real code shows the *write*
half already exists: `LeadStatusEvent` (`lead_status_events`: lead_id, from_status, to_status, changed_by_id,
changed_at) is inserted inside the `updateLead` transaction, and `db/add-lead-sales-fields.sql` creates the table with
`ON DELETE CASCADE` and deliberately has no backfill. What is missing is the read path (no endpoint, no UI) and
proof that deletion cannot orphan rows. The requirement is therefore: read endpoint + history panel + delete safety,
not a new table.

## Scope

- maros-nest: `GET /leads/:leadId/status-history`, newest information first or chronological (chronological, the
  index order), returning who (id and name, null when the move had no signed-in user), when, old and new value.
- maros-next: a "Historial" tab on the lead detail page that lists those moves.
- Deleting a lead leaves no `lead_status_events` row: the foreign key already declares `ON DELETE CASCADE`, so the
  plan verifies it in the target database and adds no explicit deletion code.
- Out of scope: backfill of existing leads (owner decision, no stored evidence exists), project status history,
  editing or deleting events, MCP tools.

## Security

The endpoint must be visible to exactly who can already see the lead: the class-level `leads:read` permission plus
the per-user lead type scope, applied in the service with `canSeeLeadNumber(lead.leadNumber)` after loading the lead,
as `getLeadById` does (not a query filter). A lead outside the scope answers 404, not 403, like
`getLeadById`. Never expose events of a lead the caller cannot open.

## Contract

Wiring: `LeadsService` reads events with `this.dataSource.getRepository(LeadStatusEvent)` and a left join to `users`
(the entity keeps a scalar `changedById`); no constructor argument and no `leads.module.ts` change, since entities
are registered by glob.

Response item: `{ id, leadId, fromStatus: string|null, toStatus: string, changedAt: ISO string,
changedBy: {id, name|null, email} | null }`, ordered by `changedAt` then `id`. Statuses are plain strings because
the column is varchar and history must survive enum edits.

## Unknowns

1. Whether `lead_status_events` and its cascading foreign key exist in the production database (tables are
   managed by hand in Supabase; nothing in the repos or the bitacora records the migration as applied). The SQL
   declaration is checked by a command in T3; a live delete in a non-production database is an optional, owner-gated
   step. Neither blocks the endpoint or the UI.

## Acceptance

- A user with `leads:read` and an in-scope lead gets the ordered history; an out-of-scope or unknown lead is 404;
  a user without `leads:read` is refused by the permission metadata.
- The lead detail page shows the history, an empty state when a lead has no recorded move, and an error state.
- After `deleteLead` no row with that `lead_id` remains.
- No migration writes historical rows.
