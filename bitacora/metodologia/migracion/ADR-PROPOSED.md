---
type: architecture-decision
status: proposed
requirement: REQ-007
---
# Make the platform the owner, keep harness skills as adapters

## Context
An operating supervisor, CLI, web server, provider integrations and durable documentation live under skill/scripts. Paths depend on that physical layout; flat imports and process entrypoints amplify coupling. The dirty worktree also contains recent relay/quota/quality functionality that must not disappear.

## Proposed decision
Install `bitacora` as a Python package exposing bt/bitacora/module entrypoints. CLI, web and provider hooks are transports over shared use cases; state stays in BITACORA_ROOT. Domain transition/routing rules do not load provider SDKs, shell commands or environment globals. Provider/process/filesystem adapters own those effects. Refactor one responsibility at a time, preserving one implementation behind legacy shims. Package templates/assets and canonical policy as resources. Thin optional skills choose context and invoke platform capabilities; they do not own state or lifecycle.

The current monorepo and local data placement are preserved. A skill suite alone does not achieve the goal; CLI/web operation must be proved without skills installed. A Protocol at the provider boundary is justified by three existing variants; a generic extension framework is not.

## Alternatives
1. Rename skill/ to workspace/: low cost, leaves path coupling and does not establish an independent product. Rejected as insufficient.
2. Big-bang src/ rewrite plus new provider/worktrees/diagram policies: highest simultaneous uncertainty, difficult regression attribution. Rejected.
3. Remote service plus database: changes actors/security/deployment/data model without a stated requirement. Deferred unless owner chooses it.
4. Staged package extraction, compatibility, then additions: recommended; more temporary shims but measurable rollback.

## Consequences
Wheel/resource packaging and schema compatibility become explicit contracts. Build tooling is distinct from stdlib runtime; optional Node adds a capability dependency. Compatibility shims have tracked consumers and retirement criteria. Live data is not moved for aesthetic consistency. Existing owner decisions remain authoritative; the attachment cannot override them by labeling itself approved.

## Rollback
Retain previous runtime and managed config preimages; quiesce new writers before switching. Preserve newly written state and acknowledged task history; schemas must be backward-readable or have a tested non-lossy reverse transform before activation. Keep worker refs/worktrees on any uncertain integration. Never force-reset branches or restore a stale full snapshot over later work.

## Approval state
Proposed only. On implementation approval, allocate an ADR ID using the existing bitácora tool and append to DECISIONS with a link here; do not reuse the duplicated historic D-004 or edit its meaning.
