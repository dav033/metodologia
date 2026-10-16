---
req: REQ-004
status: review
created: 2026-10-16
---
# Plan — REQ-004 — Configure a Google Drive MCP for local AI clients

## Approach
Install the upstream community `workspace-mcp` package at a pinned PyPI version and run one user-level Streamable HTTP service on loopback. Register that endpoint in every installed MCP client so Codex, Claude Code, Gemini CLI, and compatible local clients share the same Drive connection. A per-client stdio setup would avoid a shared listener but would duplicate server processes; the shared listener is chosen to meet the computer-wide goal, with the explicit tradeoff that any local process can call it. No public listener or tunnel.

## Global constraints
- User-space only; no `sudo`.
- Bind only to `127.0.0.1`; use port 8000 while it remains available and keep one endpoint URL consistent in every client.
- Pin `workspace-mcp==1.29.0` only after verifying the published artifact and its source; do not treat registry manifest version `2.1.0` as the PyPI version.
- Configure only Drive with `drive:full`; OAuth only for `david.theran03@gmail.com`; do not add Gmail, Calendar, or other Workspace services/scopes.
- Set `WORKSPACE_MCP_DISABLE_LOCAL_FILES=1`; do not expose server-side local-file reads or writes.
- Store the OAuth client file and token store outside repositories with owner-only directory/file permissions. Never put secrets in shell history, logs, command output, or bitácora.
- Preserve unrelated Codex, Claude Code, and Gemini settings/MCP servers. Do not use Gemini `--trust`, Codex approvals overrides, or any blanket tool auto-approval.
- Keep “delete” mapped to recoverable Drive trash; do not advertise or call permanent file deletion.
- Do not read or mutate live Drive files for verification. Treat Drive data returned to an AI as data sent to that provider.
- Do not commit, push, merge, or delete files. Do not bind to or control David's personal Firefox; use the agent browser only if OAuth needs browser interaction.

## Tasks
### M1 — Validate runtime and OAuth setup
- [ ] T1 — Verify PyPI `1.29.0` artifact provenance, CLI options, tool inventory and `WORKSPACE_MCP_DISABLE_LOCAL_FILES` support; if the package artifact cannot be tied to upstream source, stop and update the pin before installation · files: upstream PyPI `workspace-mcp==1.29.0`, upstream Drive tool reference · verify: `uvx --from workspace-mcp==1.29.0 workspace-mcp --help` plus source/metadata review · covers: R2, R3, R4, R8, US-2
- [ ] T2 — Create or select a Google Cloud project, enable only Drive API, configure an External audience in Production for personal use, create a Desktop OAuth client, and store its client JSON under `~/.config/google-workspace-mcp/` with mode `0600` (directory `0700`) · files: `~/.config/google-workspace-mcp/client_secret.json` · after: T1 · verify: Google Cloud Console shows Drive API only, External/Production audience and a Desktop OAuth client; no other users or scopes are added and no secret values enter logs · covers: R4, R5, US-3

### M2 — Install the shared local service and clients
- [ ] T3 — Install the pinned server as a user-level systemd service with `--transport streamable-http --single-user --permissions drive:full`; set `WORKSPACE_MCP_HOST=127.0.0.1`, selected port, `USER_GOOGLE_EMAIL=david.theran03@gmail.com`, `GOOGLE_CLIENT_SECRET_PATH`, and `WORKSPACE_MCP_DISABLE_LOCAL_FILES=1`; create owner-only token storage and start it · files: `~/.config/systemd/user/google-drive-mcp.service`, `~/.config/google-workspace-mcp/`, `~/.google_workspace_mcp/credentials/` · after: T2 · verify: `systemctl --user is-active google-drive-mcp.service` · covers: R1–R6, R8, US-1–US-3
- [ ] T4 — Register the same endpoint at user scope in Codex (`codex mcp add --url`), Claude Code (`claude mcp add --transport http --scope user`), and Gemini CLI (`gemini mcp add --scope user --transport http`), preserving existing config; Code OSS extensions use their corresponding CLI user config · files: `~/.codex/config.toml`, `~/.claude.json`, `~/.gemini/settings.json` · after: T3 · verify: `codex mcp list`, `claude mcp list`, and `gemini mcp list` · covers: R1, R7, US-1

### M3 — Authenticate and verify without touching Drive files
- [ ] T5 — Complete Google consent for `david.theran03@gmail.com`, then verify service binding, MCP tool inventory, client connectivity and credential permissions; do not call Drive file tools · files: local service/client configuration and token metadata only · after: T4 · verify: `systemctl --user is-active google-drive-mcp.service`; `ss -ltnp`; all three clients list the same endpoint; an MCP `initialize` + `tools/list` exchange shows Drive tools only, write/share tools and recoverable trash, no local-file operations, and no permanent delete tool · covers: R1–R8, US-1–US-3

## Verification
Run the user service and inspect its listening socket; it must be `127.0.0.1:<selected-port>`, not `0.0.0.0` or a LAN address. Confirm Codex, Claude Code, and Gemini CLI each recognize the same endpoint. Complete only the MCP initialize/tools-list handshake to prove the server advertises Drive read/write/share/trash tools, no other Workspace services, no local-file operations, and no permanent delete tool. Verify OAuth account identity and owner-only credential permissions from local metadata without reading or changing Drive content. Do not run a test suite or create/edit/trash a real Drive file.

## Rollback
Stop and disable only `google-drive-mcp.service`, then remove only the `google-drive` MCP registration from Codex, Claude Code, and Gemini CLI and reconnect those clients. If access must be revoked, revoke the app grant from the Google Account security page. Leave OAuth/token files untouched unless David separately requests their removal; no Drive files are created for verification.

## Rulings
- “Delete” means move to recoverable Drive trash — reversible default; if David intended irreversible deletion, the server tool set must be reconsidered before execution; cost if wrong: medium.
- “Any AI” means installed local MCP clients plus other local clients that can be configured for Streamable HTTP; hosted AI remains excluded because it cannot reach loopback; cost if wrong: medium.
- The local HTTP endpoint has no MCP-level client authentication — any local process can call it. Loopback binding and unchanged client confirmation behavior are accepted for this personal computer; cost if wrong: high.
- Pin PyPI `1.29.0` only if the artifact review confirms it is the published upstream package; registry manifest `2.1.0` is not the install version; cost if wrong: medium.

## Progress log
- 2026-10-16: Drafted after reviewing local Codex, Claude Code, Gemini CLI, Code OSS, free port 8000, and the community server docs. Spec-review port finding fixed; added explicit trash, local-file-disable, and unauthenticated-loopback assumptions. No MCP config, OAuth project, service, or Drive content changed.
- 2026-10-16: Set plan status to `review` through the local status helper and refreshed generated indexes directly. Skipped `bitacora.py plan review`: its CLI handler commits and pushes automatically, which is prohibited by David's workspace rules. Owner approval will be requested in chat; no web review server was started.
