# REQ-008 — Reasoning-provider capability evidence

## Claude candidate

Installed Claude 2.1.299 accepts `--print --safe-mode --tools '' --strict-mcp-config --disable-slash-commands --no-session-persistence --json-schema <schema>`. Use `--output-format stream-json --verbose` to inspect effective inventory and structured results. Run in an isolated temporary working directory with ordinary account/profile authentication; no API-key-only bare mode is assumed.

One real Haiku medium inventory check returned `tools=["StructuredOutput"]`, `mcp_servers=[]`, `skills=[]`, `slash_commands=[]`; only the schema-return mechanism was invoked. `StructuredOutput` is bounded by the declared response schema and is not an implementation/data-loading tool. Builtin plugins were listed, so eligibility must inspect capabilities rather than assuming the plugin list is empty. No hook-specific evidence was emitted.

The implementation still needs to reject unexpected inventory, malformed actions, oversized output and unsupported CLI versions/capabilities, and prove that a successor has a distinct provider session. The smoke alone does not prove the orchestration loop.

## Codex candidate and limitation

Installed Codex 0.162.1 supports `--ignore-user-config`, `--ephemeral`, `--output-schema` and `--json`. `--ignore-user-config` preserves ordinary account auth. No documented general disable-all-tools flag was found.

- [Pinned tool registration](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/tools/spec_plan.rs): `features.shell_tool=false` removes shell execution; apply_patch registration also depends independently on model metadata. Do not infer that removing shell removes patch or every data path.
- [Pinned feature declarations](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/features/src/lib.rs): `apply_patch_freeform` is retired, so treating it as an active gate would fabricate a boundary.
- [Pinned model metadata](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/protocol/src/openai_models.rs): complete `model_catalog_json` metadata can express `apply_patch_tool_type: null` and empty experimental tools. A static catalog preserves the auth manager but is not a selective model override; it needs a versioned, legitimate catalog and effective-tool tests.
- [Official configuration schema](https://developers.openai.com/codex/config-schema.json): current schema differs from some examples (for example, view-image capability is a feature rather than `tools.view_image`). Check the installed-version schema/source before using keys.

Codex remains eligible for existing bounded worker paths. A new constrained reasoning adapter must not advertise a proven boundary until effective-request/runtime tests demonstrate every exposed route is bounded or disabled. A wait for compatible capacity is an explicit supported outcome.

## Evidence retention

Original research: `/tmp/req008-provider-boundary.md`; raw local capability smokes: `/tmp/req008-claude-reasoning-smoke.json` and `/tmp/req008-claude-inventory-smoke.jsonl`. These paths are diagnostic evidence, not a replacement for deterministic fixtures and regression tests in M2.
