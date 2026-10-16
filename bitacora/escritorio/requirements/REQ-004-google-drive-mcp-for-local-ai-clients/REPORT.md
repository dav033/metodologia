# REQ-004 — Google Drive MCP for local AI clients

Plan status: done. Spec status: done. This is a user-level machine configuration; no product repository code was changed or committed. The bitácora and static site files remain local and uncommitted.

## Built

- Installed `workspace-mcp==1.29.0` as an enabled systemd user service at `http://127.0.0.1:8000/mcp`.
- Authenticated `david.theran03@gmail.com` with Drive access and registered the endpoint in Codex, Claude Code, and Gemini CLI. Other local MCP clients can use the same URL.
- Enabled Drive read, create, edit, organize, and share tools. Deletion is recoverable trash through `update_drive_file.trashed`; permanent deletion is not exposed.
- Disabled the OAuth bootstrap tool after consent so MCP clients see Drive operations only. Reauthorization requires temporarily removing the filter and restarting the service.
- Disabled direct local file-path access. The tool list omits `file_path`, and the pinned source rejects `file://` inputs.
- Kept OAuth client/token files in owner-only locations outside repositories.

## Verification evidence

- OAuth callback page confirmed authentication as `david.theran03@gmail.com`.
- OAuth metadata contains the three Drive scopes (`drive`, `drive.file`, `drive.readonly`) plus base identity scopes. No Gmail, Calendar, or other Workspace scopes are present.
- `systemctl --user is-active google-drive-mcp.service` → `active`; `is-enabled` → `enabled`.
- `ss -ltn 'sport = :8000'` → `127.0.0.1:8000` only.
- Codex lists `google_drive` enabled at the shared endpoint; Claude and Gemini report `Connected` at that endpoint.
- MCP initialize/tools-list returned 16 Drive operations; editing/sharing/trash are present, while the OAuth bootstrap helper, permanent delete, and direct local paths are absent.
- OAuth client/token files are `0600`; credential/config directories are `0700`.
- Independent spec and standards review found no remaining issues after hiding the OAuth bootstrap helper.
- The latest Vercel production deployment returned HTTP 200 for the homepage and privacy page; the privacy page includes the reviewed DuckDNS data disclosure.
- `bitacora.py --project escritorio trace --node REQ-004 --no-commits` listed REQ-004, its R/US/T nodes, and P-003 without uncovered/unknown/dangling warnings; scoped `git diff --check` passed.
- Installation verification did not read or change Drive files. In a later user-requested demonstration, the local MCP listed 10 recent items using metadata only; on request, it moved the two listed WhatsApp ZIP archives to recoverable trash and verified both with a `trashed = true` query. An older duplicate from July was left untouched. No file content was read or downloaded, and no test suite was run.

## Rulings

- “Delete” means move to recoverable Drive trash. The server does not expose permanent deletion.
- “Any AI” means local MCP-capable clients. Hosted AI cannot reach the loopback service.
- The MCP endpoint has no MCP-level client authentication; any process running locally can call it. It remains bound to loopback and client confirmation defaults were preserved.
- Google blocked Production publishing without valid public homepage/privacy-policy URLs on a verified domain. At David's request, genuine bilingual pages were published at `https://local-file-manager-three.vercel.app/` and `/privacy.html`; both returned HTTP 200. Vercel's free hostname is not a domain verified as David's, so OAuth remains External/Testing with David as the only test user. Google expires Testing refresh tokens after seven days. A DNS-controlled free subdomain remains under evaluation; no DuckDNS account/domain or DNS record has been created.

## Needs your eyes

- Security-sensitive local configuration: `~/.config/systemd/user/google-drive-mcp.service`, `~/.config/google-workspace-mcp/`, and `~/.google_workspace_mcp/credentials/`. The secret and token contents were not copied into this report.

## Proposals

1. Complete DNS-domain ownership verification, use that domain for the public homepage and privacy policy, then move the OAuth app to Production and reauthorize. This should avoid the seven-day Testing refresh-token expiry; Google may still show its unverified-app warning for personal use.

## Pending

- P-003 tracks DNS-domain verification and the Production OAuth transition. DuckDNS account authorization and Google Cloud reauthentication are still human steps; until the transition completes, Drive access must be reauthorized after Google's Testing refresh-token lifetime expires.

## Walkthrough

1. A user-level systemd service starts the pinned MCP package and loads only Google Drive tools.
2. OAuth credentials select `david.theran03@gmail.com`; the MCP shares one loopback endpoint among configured clients.
3. Each local AI client connects to `127.0.0.1:8000/mcp` using Streamable HTTP.
4. The server can read and write Drive content, organize items, and manage sharing permissions.
5. “Delete” moves an item to recoverable Drive trash; no permanent-delete operation is exposed.
6. Direct filesystem paths are disabled, so `file://` inputs are rejected.
7. The current Google Testing app requires reauthorization after seven days unless it is moved to Production.
