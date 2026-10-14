# REQ-008 — Context baseline

Measured 37 stored `prompt*.txt` files under `~/bitacora/.state/runs/` using filesystem size metadata, without copying their private contents.

| Measurement | Bytes |
|---|---:|
| Minimum prompt | 1,708 |
| Median prompt | 9,019 |
| p90 prompt | 11,191 |
| p95 prompt | 12,119 |
| Maximum prompt | 12,931 |
| All prompts | 314,832 |
| REQ-008 SPEC at measurement | 8,023 |
| REQ-008 PLAN at measurement | 5,802 |
| Full SKILL body/file | 12,904 |

SPEC + PLAN + SKILL alone total 26,729 bytes before task prompts, repository instructions, conversation turns or tools. These are entry-size measurements, not model context occupancy or token counts. They do not justify a model capacity, a turn limit, or a reserve on their own.

The current Codex text invocation reports only closing token totals. Claude's driver currently reads usage from its terminal result. The supervisor does not currently prevent oversized tool results before the model receives them. A runtime implementation must establish an enforceable boundary; posthoc log accounting alone cannot prove the requirement.

Baseline regression command: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v`. Result: 639 tests, OK, exit 0, 60.589 seconds; log `/tmp/req008-baseline-tests.log`. Discovery excluded the newly created T1 tests. No live providers invoked. No repository lint command/configuration found by the runner.

## Reasoning backend capability checks

Two distinct minimal real Haiku medium checks verified subscription auth and then effective tool inventory with `--print --safe-mode --tools '' --strict-mcp-config --disable-slash-commands --no-session-persistence --json-schema`.

- Structured response smoke: exit 0, `structured_output={"decision":"wait"}`, 3.567 seconds. This final-JSON output alone does not enumerate tools.
- Inventory smoke (`--output-format stream-json --verbose`): exit 0, 2.478 seconds. `system/init.tools=["StructuredOutput"]`; `mcp_servers=[]`, `skills=[]`, `slash_commands=[]`. Only the schema return tool was called. No Read, Bash or MCP data tool was exposed. Builtin plugins were named; no specific hook evidence was emitted.

The bounded schema return mechanism is allowed; “tool-free” here means no tool that can load external data or execute implementation. These checks establish a candidate backend capability, not completed terminal or orchestration verification. Original evidence: `/tmp/req008-claude-reasoning-smoke.json`, `/tmp/req008-claude-inventory-smoke.jsonl`.

## T2 byte policy and public checkpoint contract

`bt_orchestration_context.BudgetPolicy` defaults to `entry_bytes=16384`, `runtime_bytes=16384`,
`checkpoint_bytes=8192`. Configure all three explicitly with `RUN.json.context_policy` for session prompts,
or pass a policy to the public Python API. These are UTF-8 JSON byte ceilings, never model capacity or tokens.
The entry ceiling rounds the measured maximum 12,931 B up to the next 4 KiB boundary (16,384 B), providing
3,453 B of entry headroom. Runtime allowance is conservatively one additional entry-sized envelope aggregate;
checkpoint allowance is half an entry (compact progress and artifact references). Those two allowances are
explicit engineering policy, not a telemetry-derived guarantee of sufficient model space. Reject oversized
mandatory authority/checkpoints and adjust policy deliberately; never shorten scope, limits or acceptance.

Generated data arithmetic per instance: entry <=16 KiB + admitted runtime envelopes <=16 KiB + reserved
checkpoint <=8 KiB =40 KiB. The supervised hook is a separate pointer <=1 KiB, so including that pointer gives
<=41 KiB. Provider/system/repository instructions are outside this generated-data accounting; repeated hooks,
provider messages and tool output require the M2 runtime boundary. This does not claim that an existing native
tool session has an enforced 41 KiB context window. An embedded checkpoint must ALSO fit the entry ceiling.

- `build_package(rdir, state, unit, milestone, policy, checkpoint)` returns schema-v1 mandatory reviewed authority,
  task contracts, current authority identity and references to full SPEC/PLAN/decisions/RUN artifacts. Optional
  notes/errors share the remaining entry budget and omissions are counted. Whole transcripts and full skill are
  excluded. `bt_runprompt.session_prompt` uses this package for requirements-v1; legacy prompts stay unchanged.
- `Budget(policy, used_bytes=0, sequence=0, generation=0).admit(envelope)` measures the entire serialized envelope
  (including caller-supplied tool metadata/errors), returns `Receipt(sequence, bytes, digest)`, or raises
  `ContextPressure` BEFORE delivery without changing the budget. Receipt metadata is host bookkeeping; if sent
  to the model it must itself be admitted. `snapshot()` persists consumption. Restore with `Budget(policy,
  **checkpoint['runtime'])`. `successor()` resets only per-instance bytes, advances generation and preserves the
  receipt sequence; T4 must call it only after checkpointing and actually starting a distinct fresh instance.
- `save_checkpoint(..., completed, remaining, delegation_refs, evidence_refs, budget, expected_revision=0)`
  uses a strict exclusive lock, compare-and-swap revision, fsync and atomic replacement. `load_checkpoint`
  rejects unknown fields/versions, oversized input, different run/milestone/authority, invalid task partitions,
  rollback of reported completion/consumption and skipped context generations. Run identity is additive
  `context_run_id` initialized by `bt_runstate.init_state`. Old runs without it cannot silently enter new-mode
  checkpoint execution. A lock left by a crash requires explicit writer inspection; it is never broken by age.
  Checkpoints are reported progress and evidence references, never proof of verification or authorization.

T2 provides the admission contract and initial package/hook integration. T3/T4 still must enforce admission on
all runtime model-visible reads, results and debate envelopes, rotate processes and prove independent effects;
posthoc closing token totals cannot substitute for that boundary.
