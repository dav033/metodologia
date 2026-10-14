# Learnings

## Confirmed

_None._

## Candidates

- **L-001 · pitfall** In maros-nest, jest does not type-check specs: run 'npx tsc --noEmit -p tsconfig.json' as well, it caught a spec calling a helper with an ignored argument that jest passed
  - 2026-10-14T12:51:54.732234-05:00 · REQ-005/T3: REQ-005 M1: jest 215/215 green while tsc reported TS2554 twice in roles.service.spec.ts

- **L-002 · pitfall** MCP attribution identity has no role or permissions; use it for authorship, and retain the established trusted service context for administrator-wide financial reads.
  - 2026-10-14T14:16:33.952489-05:00 · REQ-005/T7: T7 antagonist reproduced get_projects_financials always returning [] with installed system actor; real ProjectsService regression now covers this in 588f35b.

- **L-003 · pitfall** get_task_workspace_options is a mutating MCP operation: listOptions lazily provisions the General workspace, so dry-run and attribution must cover it despite its get_ name.
  - 2026-10-14T14:37:25.155812-05:00 · REQ-005/T8: Antagonist A1 traced listOptions -> ensureGeneral -> createIfMissing. workspace-write-policy.spec.ts initially reproduced an insertion during dry_run, then passed with write classification and actor propagation.

## Rejected

_None._
