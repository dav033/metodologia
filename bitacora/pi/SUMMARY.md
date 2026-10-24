# pi — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
David's personal Pi fork integrated with Metodología for local agent work.
Last confirmed with owner: 2026-10-24.

## Current state
Fork cloned at ~/dev/pi. Dependencies and model data installed. Local `pi` launcher,
canonical Metodología instructions/live context, and experimental Claude Code subscription
provider configured outside the fork. A real minimal request succeeded with the existing Pro login.

## Active focus
- Local setup verification. See ~/dev/pi-infra/README.md.

## Top pending (see PENDING.md)
- Deterministic scheduler-worker integration remains unimplemented; instruction loading is not enforcement.

## Recent decisions (see DECISIONS.md)
- Keep upstream packages intact; Metodología owns project task state and acceptance.

## Known issues
- npm audit reports six upstream dependency vulnerabilities (2 moderate, 4 high).
- `pi auth check` does not discover the extension provider; model listing and real inference do.

_Last updated: 2026-10-24_
