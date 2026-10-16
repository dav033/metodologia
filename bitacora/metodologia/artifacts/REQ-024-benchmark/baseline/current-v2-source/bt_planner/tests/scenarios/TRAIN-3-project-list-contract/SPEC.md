# TRAIN-3 — `GET /v1/projects` returns list items, paginated

`GET /v1/projects` returns every project as a full snapshot (including `data_json`), while the web client types the
result as `ProjectListItem` (id, externalKey, name, revision, updatedAt). Return only list items with cursor pagination.
An MCP client in another repository (`trainingApp-mcp`, not part of this workspace) may read the same endpoint.

## Requirements
- R1. The response contains `projects` (list items only) and `nextCursor`.
- R2. Existing web screens keep working.
- R3. No consumer outside this repository is broken without notice.
