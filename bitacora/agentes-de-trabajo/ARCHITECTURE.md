# agentes-de-trabajo — Architecture

One local instruction-only package at /home/david/dev/agentes-de-trabajo. The coordinator owns discovery, lifecycle and orchestration; task-agent folders own their approved procedures and scoped memory. Root WORKSPACE.md records owner and persistence scope; agent and connection registries support selective loading. Connections are shared by ID, with actual environment, grants, authentication/read/write states, evidence and pending actions. No hosted runtime, background jobs or provider connector is included.

Confirmed contextual learning can be saved within existing grants. Consequential changes remain proposals until owner approval and a passing check. Persistence guidance separates local/prepared/pending/uncertain/verified remote states, handles concurrent edits and avoids partial activation. One repository belongs to one owner/team; folders are not reader isolation.

Three blueprints support new records. An isolated invoice-draft example uses fictional USD values and is outside the active registry. Behavioral evaluation uses temporary copies and mocked capability results, never actual Work/GitHub/MCP calls. Live installation and remote destination remain unconfigured.
