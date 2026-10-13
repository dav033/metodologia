---
req: REQ-007
status: done
created: 2026-10-11
---
# Plan — REQ-007 — Production MCP server for Proposal Studio

## Approach
Mount the official MCP TypeScript SDK's stateless Streamable HTTP handler at `/api/mcp` in the existing Astro production app. Validate a dedicated bearer token before handing a request to MCP, resolve the allowlisted administrator ID, apply shared Postgres request limits, then expose narrowly scoped wrappers around existing proposal, capture, GitHub, publish and sharing services. Configure this machine's Claude Code and Codex user settings to the HTTPS endpoint; both use a local header helper reading a mode-600 secret file. Deploy to production without a database migration, verify both clients, then create Oraldenti's unpublished draft using the already captured PNGs.

## Security / operational rulings
- Use a single high-entropy, revocable bearer token for this one-owner environment; do not implement a new OAuth authorization server.
- Store the token only as Vercel Production environment secret and in `~/.config/proposal-studio/mcp-token` (mode 600). The helper prints the Authorization header only to the MCP client process and never logs it.
- Use the already configured verified `ADMIN_EMAIL` user ID for actor/audit data; no caller-controlled actor IDs.
- Mark mutating tools with MCP annotations; client configuration prompts for writes. Require explicit `confirm: true` parameters for archive, publish, share creation/revocation and GitHub disconnection.
- Reuse existing `admin_rate_limit_bucket`; its prior production migration is already applied. Apply per-minute MCP limits for captures (3), GitHub reads (30), GitHub imports/disconnect (3), share creation (10), plus an overall request limit (120). No migration is part of this change.
- Never automatically retry MCP mutations. Use slug uniqueness and current-state reconciliation for captures, imports, and publication. If link creation has an ambiguous timeout, list links and revoke any orphan before creating a replacement because its secret cannot be recovered.
- Codex requires write approval (`default_tools_approval_mode = "writes"`); Claude retains its normal tool approval prompts. Server-side `confirm: true` remains mandatory for consequential tools.
- MCP exposes application operations only; no raw SQL, general filesystem, shell, Git writes, mail, settings, or notification operations.
- Oraldenti is only created as a draft; absent prototype repository means no publish/share actions.

## Tasks
- [x] T1 — Add MCP SDK and production endpoint with authenticated, typed tool handlers · files: `package.json`, `package-lock.json`, `src/features/mcp/`, `src/pages/api/mcp.ts` · verify: `npm run check`, `npm run lint` · covers: R1–R7, R10–R12
- [x] T2 — Configure secure token storage and connect this machine's Claude Code and Codex to production · files: ignored/user-owned secret, local header helper, `~/.claude.json`, `~/.codex/config.toml`, Vercel Production secret · verify: Claude reports MCP HTTP connected; Codex executed a read-only MCP call; configs contain helper paths, not the credential · covers: R2, R8
- [x] T3 — Deploy MCP endpoint and verify production authentication, rate limiting, private capture persistence, and client interoperability · files: Vercel deployment/configuration · verify: invalid and absent credentials return 401; authenticated `tools/list` returns 17 tools; read-only calls succeed; Vercel deployment READY; no migration · covers: R1–R8, R10
- [x] T4 — Use MCP tools to create and inspect the Oraldenti draft with three source routes and captures · files: production proposal data · verify: MCP read returns proposal `083cb2df-1f95-4efd-8a04-c69bd8f7b7c9`, all three capture statuses and route paths; state remains draft · covers: R9
- [x] T5 — Record operational credential rotation, tool catalog, evidence and limitations · files: project memory, REQ-007 and day log · verify: `git diff --check`; credentials not shown or logged

## Verification
Run check/lint/format and the production build. Do not run automated tests unless requested. Exercise the actual Streamable HTTP MCP protocol, rejection of bad credentials, and both configured clients. Verify created draft through the same MCP server. Never print credentials, proposal share tokens or provider secrets.

## Progress log
- 2026-10-11: User approved the plan and creation of the Oraldenti draft. Spec review findings incorporated: existing rate-limit table, server-side confirmations, no automatic mutation retries, and explicit reconciliation for ambiguous writes.
- 2026-10-11: Implemented and deployed production MCP as `dpl_AHu7vv6KVPMtbArpSNKp5WoUQw9B`. Codex invoked `list_proposals`; Claude MCP health check reported connected. Claude's non-interactive model invocation could not run because the local Claude OAuth session is expired; this does not block its configured MCP transport, but requires reauthentication before asking Claude to make a model call.
- Oraldenti draft `oraldenti` is created with Inicio, Servicios, Contacto and their private PNGs; no prototype was supplied, so it remains unpublished and has no share link.
