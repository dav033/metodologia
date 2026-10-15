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

- **L-004 · pitfall** In multi-repo requirements, worktree integration verification must filter previous accepted tasks by matching repository role to prevent running cross-repo verify commands like backend Jest suites inside the frontend worktree.
  - 2026-10-14T20:10:14.814056-05:00 · REQ-005/T9: T9 integration verification failed with Jest looking for backend auth paths in the frontend repository because previous accepted M1-M3 tasks were included unconditionally.

## Rejected

_None._
