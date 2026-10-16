---
id: REQ-004
status: done
created: 2026-10-16
track: deep
---
# REQ-004 — Configure a Google Drive MCP for local AI clients

## Problem & goal
David wants the Google Drive account `david.theran03@gmail.com` available to the MCP-capable AI clients on this computer, with read and write operations, without making the service public or exposing arbitrary local paths to the MCP.

**Success looks like:** one local MCP endpoint is available to the installed local clients; it can search, read, create, edit, share, and move Drive files to the recoverable trash; OAuth is completed for the specified Google account and requests only Drive access; the endpoint listens only on loopback; direct local path parameters are omitted and `file://` inputs are rejected.

## Users / actors / stakeholders
- David, the owner of the Google account and desktop.
- Local MCP clients installed for this user: Codex CLI and its Code OSS extension, Claude Code CLI and its Code OSS extension, and Gemini CLI.
- Google Cloud OAuth and Drive API.
- `google_workspace_mcp`, an independent open-source MCP server, not a Google product.

## Scope (in)
### US-1 (P1, Must) — Use the same local Drive service from AI clients
As David, I want local MCP-capable clients to reach one user-level Drive server so each can work with the same Google account.
**Acceptance:** Codex (CLI/Code OSS), Claude Code (CLI/Code OSS), and Gemini CLI each use the same MCP endpoint on `127.0.0.1`; use port 8000 when free, otherwise choose one available loopback port and apply its URL consistently; the server runs as a systemd user service without root. Any other local MCP client can connect if registered with that endpoint; there is no OS-wide MCP registry.

### US-2 (P1, Must) — Manage Drive files
As David, I want AI clients to search, read, create, edit, organize, and share my Drive files.
**Acceptance:** The advertised tools include Drive search/read/create/edit/move/share operations and recoverable trash via `update_drive_file.trashed`; no permanent Drive file-delete tool is advertised. Direct `file_path` parameters are omitted, and local `file://` inputs are rejected by the path validator when local file access is disabled.

### US-3 (P1, Must) — Limit the connection to this account and Drive
As David, I want this integration to use only `david.theran03@gmail.com` and Google Drive permissions.
**Acceptance:** OAuth consent is completed for that account; its token is the only account token stored for this integration; the MCP exposes Drive tools only and requests the Drive scope required for full access, with no Gmail, Calendar, or other Workspace scopes.

## Out of scope
- ChatGPT web, Claude.ai, Gemini web, or other hosted AI products that cannot reach a loopback service. Supporting them would require a separately approved public HTTPS deployment and authentication design.
- Permanently deleting Drive files. The default interpretation of “eliminar” is moving them to Drive trash, where Google says they can be restored within 30 days.
- Gmail, Calendar, Sheets, Docs, Slides, and other Workspace services except files handled through Drive.
- Google's hosted Drive MCP preview, which does not match the personal-account and write/delete requirements.
- Changing client-wide tool-approval policies to auto-approve operations.

## Requirements
- R1. When the desktop user session starts, the system shall run a user-level MCP service that listens only on `127.0.0.1` and serves Streamable HTTP at the selected loopback port, preferring port 8000 when available.
- R2. When a configured local MCP client connects, the server shall expose only Google Drive tools with full Drive read/write permissions, omit direct `file_path` inputs, and reject `file://` inputs.
- R3. When a client requests deletion of a Drive file, the available operation shall move it to recoverable trash; the tool list shall not expose permanent file deletion.
- R4. When Google OAuth runs, the user shall authorize `david.theran03@gmail.com`; the OAuth client shall request only the Google Drive scope required by the configured tools, and the integration shall store no other Google account token.
- R5. When server credentials are stored locally, the OAuth client secret and token store shall be outside repositories and limited to the user by filesystem permissions.
- R6. When the endpoint is unavailable, clients shall report a connection failure rather than a fabricated successful Drive action.
- R7. When existing Codex, Claude Code, and Gemini user configuration is edited, unrelated settings and MCP servers shall be preserved.
- R8. When the local MCP endpoint is running, it shall bind only to loopback; it shall not listen on a LAN or public interface.

## Edge cases & errors
- Port 8000 may be occupied; inspect it before starting and choose a free loopback port if necessary, then keep the same URL in all clients.
- Google may reject OAuth because the Drive API or consent configuration is incomplete; report the exact Google error and do not broaden scopes to work around it.
- An OAuth app left in Testing has refresh tokens that expire after seven days for non-identity scopes; the recommended personal-use setup is Production without verification, accepting Google's unverified-app warning and personal-use limit.
- If the user cancels OAuth or chooses a different account, do not treat authentication as complete.
- Clients may need restart/reconnect after their user MCP settings change.
- A local server bound to loopback is not reachable by hosted AI services; do not open a public listener or tunnel as a workaround.
- The legacy Streamable HTTP mode has no MCP-level client authentication; any local process that can reach loopback can call the server. Keep the endpoint local, preserve client confirmation behavior, and do not publish or tunnel it.
- Set `WORKSPACE_MCP_DISABLE_LOCAL_FILES=true`. This removes direct `file_path` parameters and makes the path validator reject all local paths, including `file://`; leave `ALLOWED_FILE_DIRS` unset. Use inline content or HTTPS URLs for uploads that need content.

## Constraints
- Use only user-space installs and a systemd user service; no `sudo`.
- Use the current `uv` installation and pin the published PyPI package `workspace-mcp==1.29.0`; the package source directories and entry points were compared with upstream tag `v1.29.0`. Newer releases, including `2.1.0`, exist; keep the exact version from the approved plan.
- Set the server host explicitly to `127.0.0.1`; do not enable OAuth 2.1 public/multi-user mode for this local-only setup. Configure the default user as `david.theran03@gmail.com` and store only that account's token.
- Configure `drive:full` only. The server is community-maintained and not affiliated with Google; review its current source/release before installation.
- Preserve per-client default confirmation behavior; do not configure blanket tool auto-approval.
- Treat Drive content returned to an AI client as data sent to that client's model provider.
- Do not commit, push, merge, or delete files. Do not expose OAuth secrets or Drive contents in logs or the bitácora.

## Priorities & phases
- Must: local shared endpoint, exact Google account, Drive-only full read/write tools, recoverable trash, and user-level client registrations.
- Must: confirm loopback-only binding, OAuth account, owner-only credential permissions, direct local path inputs disabled, and `file://` rejected, without reading or changing a real Drive file as a test.
- Later only if requested: connect hosted AI products through an independently secured public deployment.

## Timeline & dependencies
- Depends on David approving the plan, creating/authorizing a Google Cloud OAuth client for personal use, and completing Google consent for the specified account.
- No deadline stated.

## Assumptions
- “Para cualquier IA” means local applications that implement MCP; the initial clients are Codex CLI, Claude Code, and Gemini CLI. A web AI cannot access this local-only endpoint.
- “Eliminar” means move to recoverable Drive trash, not permanent deletion; the selected Drive tool set supports moving files to/from trash but does not expose permanent file deletion.
- Use the independent `taylorwilsdon/google_workspace_mcp` server, pinned to PyPI `1.29.0`, whose key source directories and entry points match upstream tag `v1.29.0`. PyPI also publishes newer releases, including `2.1.0`; the approved plan remains pinned to `1.29.0`. The server supports personal Google accounts, local Streamable HTTP, and full Drive tools; it requires a Google Cloud OAuth client.
- Google Cloud rejected Production publishing until valid public homepage and privacy-policy URLs on a verified domain were configured. The working installation uses External/Testing with David as the only test user; Google expires Testing refresh tokens after seven days. At David's request, genuine bilingual pages were published at `https://local-file-manager-three.vercel.app/`; this free Vercel hostname does not prove David owns the domain. Move to Production only after Search Console verifies a DNS-controlled domain and both app URLs use that domain.
- Register one shared loopback service in each installed local client; there is no OS-wide MCP registry that all clients automatically read.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
- 2026-10-16: David explicitly requested modifying and deleting Drive files. Deletion is interpreted as recoverable Drive trash; this was the recommended option, but permanent deletion was not explicitly requested.
- 2026-10-16: “Any AI” is interpreted as installed local MCP-capable clients plus other local clients configured with the endpoint. There is no system-wide MCP registry; hosted AI access remains out of scope because it cannot reach loopback.
- 2026-10-16: A loopback Streamable HTTP endpoint is not authenticated per client. Any local process can reach it; preserve the clients' default tool confirmations and do not expose the port outside this computer.
- 2026-10-16: Disable direct local path parameters with `WORKSPACE_MCP_DISABLE_LOCAL_FILES=true`; this also rejects `file://` paths. Use inline content or HTTPS URLs where upload content is needed.
- 2026-10-16: Google blocked Production publishing because the consent screen lacked valid public homepage and privacy-policy URLs on a verified domain. OAuth is completed in External/Testing with only David as a test user; the refresh-token lifetime is seven days. At David's request, the real public pages were deployed to Vercel, but `vercel.app` does not establish domain ownership. Moving to Production remains pending a DNS-controlled domain verified in Search Console and URLs on that domain.

## Research sources
- [Google Workspace MCP project](https://github.com/taylorwilsdon/google_workspace_mcp), [PyPI package release](https://pypi.org/project/workspace-mcp/1.29.0/), and [Drive tool reference](https://workspacemcp.com/google-drive).
- [Google personal-use OAuth verification exception](https://support.google.com/cloud/answer/13464323?hl=en), [OAuth testing token lifetime](https://support.google.com/cloud/answer/15549945?hl=en), [OAuth production readiness](https://developers.google.com/identity/protocols/oauth2/production-readiness/policy-compliance?hl=en), and [brand verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification).
- [Google Drive trash and permanent deletion behavior](https://developers.google.com/workspace/drive/api/guides/delete).
