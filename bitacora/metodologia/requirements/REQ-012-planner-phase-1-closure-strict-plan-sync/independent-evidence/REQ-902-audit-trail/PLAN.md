---
id: REQ-902
status: review
created: 2026-10-15
---
# Plan — REQ-902 Lead status audit trail

Repositories: `maros-nest` (API, jest) and `maros-next` (web, vitest). The write path already exists and the database foreign key declares ON DELETE CASCADE; this plan adds the read endpoint and the history panel, and records a check of the delete guarantee instead of duplicating it in code.

### M1 — Read API and delete guarantee
- [ ] T1 — Lead status history service method gated by canSeeLeadNumber, creating the new lead-status-event.dto.ts · repo: maros-nest · files: src/modules/leads/lead-management/leads.service.ts, src/modules/leads/lead-management/leads.service.spec.ts, src/modules/leads/lead-management/dto/lead-status-event.dto.ts · resources: lead-status-history-contract, leads-service · verify: `npx jest src/modules/leads/lead-management/leads.service.spec.ts`
- [ ] T2 — GET :leadId/status-history route guarded by leads:read · repo: maros-nest · after: T1 · files: src/modules/leads/lead-management/leads.controller.ts, src/modules/leads/lead-management/leads.controller.spec.ts · resources: lead-status-history-contract · verify: `npx jest src/modules/leads/lead-management`
- [ ] T3 — Verify the delete cascade guarantee on lead_status_events: SQL declaration by command, live delete as an optional owner-gated step · repo: maros-nest · files: db/add-lead-sales-fields.sql · resources: lead_status_events-table · verify: `grep -n 'REFERENCES leads(id) ON DELETE CASCADE' db/add-lead-sales-fields.sql`

### M2 — History panel
- [ ] T4 — Web contract: endpoint, domain model, repository method and query key, creating the statusHistory repository test · repo: maros-next · after: T2 · files: src/features/leads/infra/http/endpoints.ts, src/features/leads/infra/http/LeadHttpRepository.ts, src/features/leads/domain/ports.ts, src/features/leads/application/keys/leadsKeys.ts, src/features/leads/infra/http/LeadHttpRepository.statusHistory.test.ts · resources: lead-status-history-contract, lead-repository-port · verify: `npx vitest run src/features/leads/infra/http/LeadHttpRepository.statusHistory.test.ts`
- [ ] T5 — Status history hook and section component with empty and error states, creating its component test · repo: maros-next · after: T4 · files: src/features/leads/presentation/hooks/data/useLeadStatusHistory.ts, src/features/leads/presentation/pages/sections/LeadStatusHistorySection.tsx, src/features/leads/presentation/pages/sections/LeadStatusHistorySection.test.tsx · resources: lead-repository-port · verify: `npx vitest run src/features/leads/presentation/pages/sections/LeadStatusHistorySection.test.tsx`
- [ ] T6 — Add the Historial tab to the lead detail page, creating a page test for the tab · repo: maros-next · after: T5 · files: src/features/leads/presentation/pages/LeadDetailsPage.tsx, src/features/leads/presentation/pages/LeadDetailsPage.historyTab.test.tsx · resources: lead-details-page · verify: `npx vitest run src/features/leads/presentation/pages/LeadDetailsPage.historyTab.test.tsx`

### M3 — Close
- [ ] T7 — Full web verification after the panel is wired · repo: maros-next · after: T6 · resources: lead-details-page · verify: `npm run verify`
