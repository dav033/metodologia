# metodologia — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — No guard hook limiting the executor
- **Date:** 2026-10-08 · **Status:** Accepted
- **Context:** Research recommended a PreToolUse hook blocking destructive commands (force push, `reset --hard`, `rm -rf` outside the repo, reading `.env`/`~/.ssh`), since the Claude sandbox doesn't run on native Windows.
- **Decision:** Not adopted. The user wants agents without limitations; safety stays in the skill's prose rules (stop-and-ask list) plus secret scanning.
- **Alternatives:** guard hook (rejected by the user: "no quiero limitaciones"); devcontainer/WSL sandbox for executors (not pursued).
- **Consequences:** + full autonomy, no false blocks / − destructive mistakes are only prevented by instructions.
- **Source:** [day log](2026-10/W2/2026-10-08.md)

## D-002 — One private monorepo for skill + bitácora
- **Date:** 2026-10-08 · **Status:** Superseded by D-007
- **Context:** Work happens on several computers; skill and bitácora were local-only.
- **Decision:** `github.com/dav033/metodologia` (private) holds `skill/` and `bitacora/`; junctions keep the usual paths; `install.py` sets up any machine; bitácora auto-commits (scoped) and pushes, pulls at session start.
- **Alternatives:** two repos (rejected: nothing will be shared; simpler with one); company org for Sempertex docs (not needed per user).
- **Consequences:** + one clone, versions aligned / − all project docs in one repo (fine: private, not shared).
- **Source:** [day log](2026-10/W2/2026-10-08.md)

## D-003 — Hefesto retired; everything moves to metodologia
- **Date:** 2026-10-08 · **Status:** Accepted
- **Decision:** eventos migrated (hefesto/ kept as archive); hefesto skill links removed (code intact in ~/hefesto).
- **Source:** [eventos day log](../eventos/2026-10/W2/2026-10-08.md)

## D-004 — Graphs: derive from our own IDs, no knowledge-graph database
- **Date:** 2026-10-08 · **Status:** Accepted
- **Context:** Research (2025–2026) shows modest/mixed evidence for graph context; KG stacks (Graphiti, GraphRAG, cognee) need infra and LLM edge extraction of links the bitácora already declares.
- **Decision:** a stdlib trace graph built from IDs (REQ/US/R/T/D/P), commits and files, with lint + web view; optional CodeGraph MCP for code navigation, A/B-tested first.
- **Source:** research notes, [day log](2026-10/W2/2026-10-08.md)

## D-005 — Antagonist gate before every commit, parent decides
- **Date:** 2026-10-09 · **Status:** Accepted
- **Context:** The user wants harsh architectural review before each commit without infinite loops.
- **Decision:** `antagonist` subagent reviews the staged diff; the parent agent triages each finding — fix if relevant now, otherwise defer to PENDING.md (urgency × complexity) or drop. One review + at most one re-review per commit; the antagonist can't delegate or edit.
- **Alternatives:** blocking review until clean (rejected: loops, interruptions).
- **Consequences:** + design issues caught pre-commit, deferred work tracked / − extra tokens and time per commit.
- **Source:** [day log](2026-10/W2/2026-10-09.md)

## D-006 — Multi-day runs: marathon supervisor, fresh session per task
- **Date:** 2026-10-09 · **Status:** Accepted
- **Context:** /goal and /loop alone can't run for days (loops expire after 7 days and aren't restored on resume, --bg doesn't survive reboot, compaction loses detail — Codex goal completes early after compaction).
- **Decision:** `bitacora.py run` supervisor: state on disk (RUN.json), one fresh headless session per task (Haiku 5.5 + ultracode by default), external verify, caps and stuck detection in the supervisor, usage-limit backoff, autostart after reboot, Windows toast. Loop mode stays for hours-long work.
- **Alternatives:** one long /goal session (rejected: context rot, no reboot survival).
- **Consequences:** + days of unattended work with bounded risk / − more moving parts to maintain.
- **Source:** [day log](2026-10/W2/2026-10-09.md)

## D-007 — The bitácora lives in `~/bitacora`, outside the repo
- **Date:** 2026-10-13 · **Status:** Accepted · **Supersedes:** D-002 (bitácora location only)
- **Context:** Remote commit `4cfd74f` (2026-10-12) removes the embedded `bitacora/` from the repo, and `install.py` creates `~/bitacora` as a plain folder "never linked into this repo". Pushing the local legacy bitácora would have brought it back. 112 bitácora files changed locally since `07a8113` existed only on this machine.
- **Decision:** the live bitácora is `~/bitacora` (`$BITACORA_ROOT` overrides it). The monorepo keeps `skill/`, `evals/`, `install.py` and `README.md`; its history keeps the legacy `bitacora/` commits. The user approved the move, with a backup first.
- **Alternatives:** keep the bitácora embedded (rejected: contradicts `4cfd74f`); discard the 228 local commits (rejected: the only copy of 112 files; backed up instead); keep the history in a local branch only (rejected by the user, who chose to push it).
- **Consequences:** + the repo's tip carries no bitácora, and the legacy history is on GitHub / − the live bitácora has no remote or backup yet (P-013), so sync between machines is undefined.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · P-013

## D-008 — Pictures bitácora goes into the metodologia repo (full copy)
- **Date:** 2026-10-13 · **Status:** Accepted · **Supersedes:** D-007 (pictures project only)
- **Context:** The owner asked for the pictures bitácora to be part of the `metodologia` repo, not a separate repo. D-007 had moved the whole bitácora out of the repo.
- **Decision:** `bitacora/pictures/` in the `metodologia` repo receives a full copy of `~/bitacora/pictures`. Git ignore rules still apply, so the casos photos stay out. The commit is local; nothing is pushed until the owner decides. `~/bitacora/pictures` stays the live copy until one link is chosen.
- **Alternatives:** keep it in `~/bitacora` (D-007); move the whole bitácora into the repo (not requested); let the bitácora code push after each commit (rejected: `push_async` would publish `main` automatically).
- **Consequences:** + one versioned copy of pictures in the methodology history / − two copies until the live one is linked; the repo copy is a snapshot at its commit.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · P-013

## D-009 — Integrate the other clone's bitácora into the repo (owner's choice)
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** Commits `c683665` ("bitacora: moved back into the metodologia monorepo (temporary)") and `1a72518` ("pictures: reconstruction …") from another clone of the repo (10:20 and 10:44 -05:00) reached `origin/main` while the local pictures commit `c1e39c0` was ready. The push was rejected as non-fast-forward. No clone of the repo exists on this machine except this one.
- **Decision:** integrate them (merge `904a1e7`). The repo now carries the bitácora of 16 top-level entries, including four projects that are not in `~/bitacora`. On the nine add/add conflicts in `bitacora/pictures` the local copy was kept; the other clone's versions stay in history (`c683665`, `1a72518`).
- **Alternatives:** keep `c1e39c0` local (not chosen by the owner); take the other clone's pictures and drop the local copy (not recommended: 3546 lines of ours would be missing).
- **Consequences:** + one complete history on GitHub / − contradicts D-007 for the projects not in `~/bitacora`; repo copies and the live copies can diverge; the other clone must be stopped before it pushes again.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · D-007 · D-008

## D-010 — Keep the other clone's bitácora copies; the other agent does the controlled merge
- **Date:** 2026-10-13 · **Status:** Superseded by D-011
- **Context:** After D-009 the repo copies of eventos, maros, metodologia and signature-extraction, which come from the other clone, may differ from the live copies in `~/bitacora`.
- **Decision:** keep the repo copies as they are. Nothing is aligned from this session. The controlled merge between both sides is done by the other agent, which the owner put in charge of it. The live copies stay unchanged until it finishes (P-015).
- **Alternatives:** align the live copies to the repo from here (rejected: it would overwrite them without review); align the repo to the live copies from here (rejected: the same problem on the other side).
- **Consequences:** + no data is lost while the merge is pending; one owner for the merge / − the divergence stays until the merge is done.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · D-009 · P-015

## D-011 — Publish the live bitácora to main over the other clone's copies
- **Date:** 2026-10-13 · **Status:** Accepted · **Supersedes:** D-010
- **Context:** The owner decided to send everything to `main`. The other clone's agent runs on another computer and cleans up there. Commit `9d1b796` overwrites the other clone's versions of eventos, maros, metodologia and signature-extraction, plus the root `INDEX.md` and `TOOLS.md`, with the live copies. The other computer pushed `6ed2c4f` (pictures) meanwhile; the commit was rebased on it without conflicts.
- **Decision:** the live copies are the content of `main` for these paths. Files that exist only in `main` are not deleted (maros 7, metodologia 14). The other computer's agent does the cleanup and the merge there.
- **Alternatives:** keep the two sides apart and wait (rejected by the owner); publish to a separate branch (rejected by the owner).
- **Consequences:** + `main` matches the live bitácora for these paths and the history keeps both sides / − `main` holds files that exist only in the other clone until its cleanup; the other computer must fetch and rebase before its next push.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · D-010 · P-015

## D-012 — The pictures bitácora is a junction into the metodologia repo
- **Date:** 2026-10-13 · **Status:** Accepted · **Supersedes:** D-008 (the separate live copy of pictures)
- **Context:** The owner asked for the whole pictures bitácora to be inside `metodologia`. The repo copy already held everything the live copy had: no live-only files, and the only live-only line was a generated timestamp in `INDEX.md`.
- **Decision:** `~/bitacora/pictures` is a Windows junction to `metodologia/bitacora/pictures`. The former live folder is kept as `~/bitacora/pictures.live-old` and nothing was deleted. `~/bitacora` no longer tracks `pictures/`; its history is kept and both folders are ignored there. Changes to pictures are committed in `metodologia`, by hand.
- **Alternatives:** keep a separate live copy and sync it by hand (rejected by the owner); let the bitácora commit pictures into the repo (rejected: the bitácora would then push `main` on each commit).
- **Consequences:** + one copy of pictures, inside the repo, and the hooks keep the same path / − pictures changes stay uncommitted in `metodologia` until someone commits them; the bitácora's session-end commits no longer cover pictures.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · D-008 · D-011

## D-004 — Gemini 3.8 Flash (Antigravity) is the default auditor; it builds only as a reserve
- **Date:** 2026-10-13 · **Status:** Accepted · **Supersedes:** D-003 point 5 (Antigravity removed because of the free quota)
- **Context:** The owner now has a Google AI Pro subscription (separate quota pool from Claude and Codex). 73 benchmark runs: Flash low solved every task (8 hard types, two passes) and was the only agent with no false positives and no empty answer in a security review with decoys; effort never improved accuracy and High timed out twice on a task Low solved; Flash is 3–6× slower than Claude/Codex and spends 115–140k input tokens per run. Google's FAQ says wrapping `agy -p` in applications or rotating accounts is not supported under consumer plans.
- **Decision:** Flash **low** audits every milestone and the final review by default (`audit.provider`, config), still preferring a provider other than the builder's; Sonnet medium / Opus high / Sol medium remain the fallback and the escalation. Flash builds only as a reserve (it ranks behind Claude and Codex for implement/test/docs/research). The router never raises Flash to medium/high on its own (ladder low, low, medium at tier 2 only); a failure moves work to another provider. Antigravity is a machine-local profile (`profiles add antigravity --provider antigravity`), one Google account, no rotation, `--print-timeout` = session timeout, quota read from `agy --print=/usage` and refreshed at most every 15 minutes (above 85 % used it stops being preferred; 100 % excludes it).
- **Alternatives:** Integrate through a Gemini API key from AI Studio (pay per use, ≈ $0.11/task at low, explicitly allowed for third-party agents) — kept as the way out if the provider's terms are enforced against `agy -p`. Use Flash only as a reserve — safer for the terms, but not what the owner asked for. Medium/High by default (Google's recommended default is medium for long-horizon agent work) — no measured benefit in bounded tasks; revisit if long-horizon work shows otherwise.
- **Consequences:** + audits stop consuming Claude/Codex subscriptions and are independent of the builder; + measured precision; − audits take 1–3 minutes longer; − residual terms-of-service risk on the owner's Google account (accepted); − Flash's long-horizon and architecture behaviour is NOT measured.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · benchmark and web research in `pending-artifacts/agy-benchmark-2026-10-13/`

## D-013 — Audit routing order after the preferred auditor (REQ-007 T3)
- **Date:** 2026-10-13 · **Status:** Accepted (coordinator ruling under REQ-007, owner said `continua`) · **Refines:** D-004
- **Context:** The two baseline failures of the legacy suite (`test_audit_routing`, `test_subscription_usage`) came from two sessions writing different audit orders: provider diversity from the builder (D-004) versus "Claude first" (agents.md rule 4, other session's audit budget work). Codex headroom was also pushing audits to the most expensive fallback.
- **Decision:** For audits the sort key is: busy, avoid builder's provider (D-004 diversity kept), preferred auditor, measured audit success band (5+ judged), budget order (Codex Sol last), then headroom. For implementation the order is unchanged. Test that asserted Claude over diversity was rewritten to assert diversity, plus a test for Claude-first with no builder to avoid.
- **Alternatives:** make Claude beat diversity (contradicts D-004 and R8 audit independence); leave headroom first (spends Codex on audits while Claude has room).
- **Consequences:** + baseline 579/579 green; − an audit built by Claude goes to Codex when Flash is unavailable, even if Claude has more room.
- **Source:** `skill/scripts/bt_agents.py` `_quality_order`; `skill/scripts/tests/test_audit_routing.py` (untracked file of another session).

## D-014 — ADR-PROPOSED direction provisionally adopted for REQ-007; owner ratification pending
- **Date:** 2026-10-13 · **Status:** Provisional (decided by the debate panel + judge the owner asked for, LG-002) · **Refines:** REQ-007 plan approval
- **Context:** The owner said `continua` on the REQ-007 plan and left. The ADR (`migracion/ADR-PROPOSED.md`) is still "proposed" and T2 asks for owner acceptance, yet T3–T6 already ran. An independent review flagged the out-of-order execution. Three debaters (A accept now, B keep proposed, C restructure to src/ now) and a judge ruled on 2026-10-13.
- **Decision:** The ADR's direction is the working basis under the plan approval; it is NOT recorded as accepted. T2 stays open until the owner ratifies. Until then: no physical move to `src/bitacora`, no shim replacing the contents of flat files, no rewiring of live routing or supervisor call sites, no T8 scheduling change, no M4 onward, and no commit, push, deletion, live install or config change. Allowed: closing the reopened T5/T6 gaps, additive identity-preserving namespace aliases, and the T7 contract spec plus fake-CLI contract tests.
- **Alternatives:** A (mark accepted by inference) rejected: the ADR itself says acceptance is the owner's; C (move files now) rejected: other sessions have uncommitted work in those files and the PLAN forbids big-bang; B pure rejected: it leaves the reopened M2 gaps and a staged M3 idle.
- **Consequences:** + the plan keeps moving on reversible work; + the owner returns to one ratification question; − M3 adapters land as new modules not yet used by the supervisor.
- **Source:** debate panel and judge 2026-10-13 · [ADR](migracion/ADR-PROPOSED.md) · [PLAN](migracion/PLAN.md)

## D-015 — ADR of REQ-007 ratified by the owner: local platform, thin optional skills
- **Date:** 2026-10-14 · **Status:** Accepted · **Supersedes:** D-014 (provisional adoption) · **Closes:** T2
- **Context:** D-014 left the ADR direction provisional and asked the owner one question: ratify it, change it (no skills at all, or a remote service) or reject it.
- **Decision:** The owner answered: skills are wanted when they improve the work, and the platform runs locally. That keeps the ADR as written (`migracion/ADR-PROPOSED.md`): local CLI + web + supervisor are the product, harness skills stay as thin optional adapters, no remote service, no database. SPEC assumption A1 is confirmed. The blocks of D-014 are lifted: the incremental move to `src/`, wiring the driver contract into the supervisor, the T8 scheduling change and M4 onward may proceed, each under the PLAN's own gates. Still gated separately: any commit/push the owner has not asked for, live install or config changes, real-account activation, M8 cutover and M9.
- **Alternatives:** no skills at all and a remote service were offered and not chosen.
- **Consequences:** + T2 closed; + structural work unblocked; − "skills when they improve" means each adapter must show a measured benefit (M6 records context bytes and behavior, no invented reduction target).
- **Source:** owner's answer in session 862a2e59 · [ADR](migracion/ADR-PROPOSED.md) · D-014

## D-016 — Versioned durable requirements revalidation before execution
- **Date:** 2026-10-14 · **Status:** Accepted
- **Context:** REQ-008 R1 requires entry/continue to preserve unchanged approval while rejecting material drift; approved execution children must not restart owner interviews. Existing launch/run/handoff only relied on plan approval.
- **Decision:** Introduce opt-in `execution_contract: requirements-v1` and durable schema-1 REQUIREMENTS.json with reviewed goal, scope, requirements, limits, acceptance, approval reference, evidence fingerprints and unresolved decisions. Gate actual launch/run/handoff before effects; render live entry diagnostics. Existing snapshots activate enforcement even if the marker is removed. Use atomic locked writes, bounded local evidence, strict versions and fail-closed validation. Operational status/checkmarks/progress do not revoke approval. Snapshot persistence never grants plan approval.
- **Alternatives:** Always reinterview (repeats settled decisions); trust approval frontmatter alone (misses drift); enable the new default immediately (bypasses the verified foreground transition required by M2).
- **Consequences:** + durable provider-independent review and a small T2 API; + unchanged legacy plans remain usable during bootstrap; − semantic contradictions still require an agent/owner ruling. Canonical DECISIONS.md is fingerprinted when present: unrelated additions conservatively require an agent reread and snapshot refresh, retaining existing approval without another owner interview. M2 must activate the contract by default only after its terminal checks pass.
- **Rollback:** Remove runtime/entry gate calls and opt-in for future plans; retain snapshots as evidence. Do not silently downgrade already opted-in execution or broaden permissions. Existing RUN schema and approvals are unchanged.
- **Source:** [REQ-008 SPEC](requirements/REQ-008-fresh-milestone-orchestration-and-bounde/SPEC.md) · T1 approved PLAN. ID allocated with `bt_core.next_id`, `bt_vcs.pull` mocked to avoid unauthorized network/rebase.

## D-017 — Enforceable bounded milestone orchestration with structured decisions
- **Date:** 2026-10-14 · **Status:** Accepted under approved REQ-008
- **Context:** A prompt-size cap or closing token total cannot prevent native tools from inserting large results into a coordinator's context. Claude has a locally supported safe-mode/tool-free/schema invocation; one real Haiku medium smoke succeeded. Codex 0.162.1 has no demonstrated equivalent: disabling shell does not remove model-dependent apply_patch, and a static catalog needs further effective-tool verification.
- **Decision:** Reuse the existing supervisor, routing, delegation, task verification and relay lifecycle. Each milestone orchestrator takes fresh structured decisions over validated, byte-bounded scope and receipts. The deterministic executor admits only bounded delegation/documentation/verification/checkpoint actions; it never forwards raw worker transcripts. Start with the tool-free Claude capability boundary, verifying its effective tool inventory before calling it proven. Unsupported coordinator backends are ineligible with an explicit resumable wait, never a silent native-tool fallback. Worker/provider routing remains separate; Codex can continue as a bounded worker. The milestone owns its durable state, documentation and integration; individual model invocations do not inherit conversation history.
- **Alternatives:** B: pinned public Codex model metadata with patch disabled, shell disabled and a complete effective-tool test. Promising but not yet proved; eligibility requires its own implementation evidence. C: native orchestrators plus wrappers/hooks. This cannot prove bounds when another tool route can bypass the wrapper. Three Luna medium agents proposed A/B/C and exchanged critiques; the coordinator chose A based on the demonstrated boundary, not their agreement.
- **Consequences:** + context does not accumulate across reasoning invocations; + input admission and structured actions are testable before delivery; − coordinator availability initially depends on a verified capability, with honest waits; − bounded receipts must retain decisive errors and mandatory constraints, rejecting overflow rather than silently omitting them. Exact tool-free behavior and terminal lifecycle remain acceptance obligations, not completed claims.
- **Rollback:** Keep legacy execution explicit during bootstrap; disable the new execution path without discarding requirements snapshots or checkpoints. Do not silently downgrade an opted-in run or broaden tools/permissions. No global installation, credentials changes, push or commits authorized.
- **Evidence:** REQ-008 CONTEXT-MEASUREMENTS.md; `/tmp/req008-provider-boundary.md`; `/tmp/req008-claude-reasoning-smoke.json`; council `boundary_proposal_a/b/c` proposal and critique rounds. ID from `bt_core.next_id` with remote pull mocked.

## D-018 — Verified completion can be superseded without resetting execution history
- **Date:** 2026-10-14 · **Status:** Accepted under approved REQ-008
- **Context:** Independent T4 reviews reproduced two recovery defects: a durable FINAL finish failed a new-start freshness check after a crash, and a task finish prevented repair after independent settlement verification rejected it. Deleting checkpoints or resetting the run would lose evidence and budgets.
- **Decision:** Bind FINAL completion to a bounded, validated REPORT identity/digest for the same run. Record task/final rejection explicitly with run identity, finish digest, rejecting session and reason. Permit checkpoint completion supersession only after validating that rejection against the durable finish; retain the previous revision as evidence. Preserve the journal, decision/session counts, receipt sequence and budget monotonicity. Callers without a proven supersession keep the original no-regression rule. Put shared journal/proof validation below action execution and checkpoint persistence, without instantiating an action engine from storage.
- **Alternatives:** Delete or overwrite history (forbidden and hides the cause); create a fresh run for every verification failure (resets recovery budgets); always require manual inspection (unnecessary interruption for a verified recoverable defect); trust a new boolean marker (does not establish identity or evidence).
- **Consequences:** + repair remains possible without replaying already accepted effects; + FINAL crash recovery admits the exact previously verified report and rejects modifications; − rejection and archive publication are additional durable contracts requiring strict validation and regression evidence. Report/invalidations have explicit schema versions; checkpoint consumers and legacy callers must remain compatible.
- **Consumers / rollback:** `save_checkpoint/load_checkpoint`, the structured action runtime, settlement, hooks, tests and packaged module aliases. Roll back supersession admission while retaining checkpoints, archives and invalidations as evidence; never delete history or reset counters. Existing unmarked execution stays unchanged. No global install/configuration or VCS permission is granted.
- **Evidence:** REQ-008 T4 spec/standards reviews; `/tmp/req008-t4-review-behavior-red.log`, `/tmp/req008-t4-reopen-red.log`, `/tmp/req008-t4-review-targeted-green.log`. Final interruption/validation corrections still require fresh checks. ID from `bt_core.next_id`, `bt_vcs.pull` mocked to avoid an unauthorized remote update.

## D-019 — PLAN.json is the planner's classified contract; Python-only validator; opt-in per requirement
- **Date:** 2026-10-14 · **Status:** Accepted under REQ-009 (owner's `/goal`, PLAN-SUPERIA-FASE-1-PLANES.md)
- **Context:** Plans were free Markdown; a deterministic scheduler could not read complexity, risk, duration, coupling or shared resources without reinterpreting prose. The project is stdlib-only (`dependencies = []`).
- **Decision:** `PLAN.json` (schema 1.0.0, `skill/schemas/plan.schema.json`) carries the mandatory classification; `bt_plan_contract.py` validates it by hand (no `jsonschema`), the schema file is the published document kept in step by a parity test. `plan-json init` derives a skeleton from PLAN.md and never defaults classification; `check` is the gate (schema, DAG, PLAN.md consistency by ids/milestones/`after`, frozen-revision integrity). Approved revisions are frozen in `plan-revisions/` with sha256 (`launch` freezes; `handoff` refuses an invalid PLAN.json). New runs copy only `plan_ref`; no existing RUN.json is touched. A task with no defensible duration blocks publication (add a research task or split); `full_system` needs `scope_exception`. Opt-in: plans without PLAN.json keep the old flow.
- **Alternatives:** add `jsonschema` as a dependency (breaks stdlib-only); extend PLAN.md task-line grammar with all fields (unreadable, bt_runstate/bt_run are at the 500-line limit); make PLAN.json mandatory now (breaks every historical plan); put revisions in RUN.json (mixes plan and execution state).
- **Consequences:** + one validated contract for the future scheduler; + classification can never be silently defaulted; − the schema file is declarative only (the Python validator is the gate); − the foreground launch path (`bt_orchestration_transition`) does not freeze yet (P-019).
- **Rollback:** delete `PLAN.json`/`plan-revisions/` of a requirement and it reverts to the legacy flow; remove the two opt-in hooks in `bt_launch.launch` and `bt_handoff.assess`.
- **Evidence:** `artifacts/plan-contract-map.md`, `artifacts/plan-contract-compat.md`, tests `skill/scripts/tests/test_plan_*.py`, independent spec and standards reviews (11 findings fixed with regression tests). ID from `bitacora.py id D`.

## D-020 — The methodology is divided into modules; the planner is the first (`bt_planner`)
- **Date:** 2026-10-14 · **Status:** Accepted under REQ-010 (owner: "esto va a ser parte de la metodología, pero vamos a dividirla por módulos")
- **Context:** REQ-009 left the planner spread over `bt_plan_contract/revisions/sync`, importing `bt_runstate`, `bt_lock` and `bt_core`. The owner wants it isolated, verifiable end to end and working independently, with no dependency mixing or coupling, but still part of the methodology.
- **Decision:** A module is a package `skill/scripts/bt_<name>/` with README, public API, bundled data, CLI and its own tests; it imports only the standard library and itself and names nothing of the rest (AST/text-enforced), takes explicit inputs, and proves isolation by passing its suite when copied alone and run with `python -I`. The methodology reaches it through exactly one adapter (`bt_plan_adapter.py`; argument plumbing in `bt_cli_plan.py`), never the other way. The planner keeps its own small PLAN.md parser and lock (a parity test against `bt_runstate.parse_plan` on every real plan guards drift). Convention in `references/modules.md`.
- **Alternatives:** a separate project with its own pyproject (rejected by the owner: it is part of the methodology); keep importing `bt_runstate`/`bt_lock` (coupling); put the package under `skill/modules/` with a path hack (not importable in an installed wheel without extra wiring).
- **Consequences:** + the planner can be read, run, tested and reasoned about alone; + a repeatable recipe for splitting the rest; − a deliberate small duplication (PLAN.md grammar, lock) paid for with a parity test; − `PLAN.md` status words are passed by the adapter, so a change of vocabulary is a one-line adapter edit.
- **Rollback:** the adapter is the only seam: restoring the previous behaviour means reverting `bt_plan_adapter.py` to call the old modules (kept in this decision's evidence only as REQ-009's REPORT). No data format changed; `PLAN.json`/`plan-revisions/` are identical.
- **Evidence:** `requirements/REQ-010-*/REPORT.md`; module suite (`bt_planner/tests`, isolated copy included); methodology suite; packaging tests with the wheel. Supersedes the file layout of D-019 (contract unchanged). ID from `bitacora.py id D`.

## D-021 — Planner phase 1 closes with schema 1.1.0 (argued classifications) and one launch gate
- **Date:** 2026-10-14 · **Status:** Accepted under REQ-012 (owner's `/goal` closing PLAN-PLANNER-001)
- **Context:** After REQ-009/010 a PLAN.json was checked only for ids, milestones and `after` against PLAN.md; titles, repos, verifications and duplicated ids in PLAN.md passed. Classifications were bare labels plus one free sentence. Only `bt_launch.launch` froze a plan; the foreground transition and a direct `run` did not, and a launch froze whatever PLAN.json held, including an unreviewed edit with a bumped revision.
- **Decision:** (1) PLAN.md is parsed with its silent drops reported and `check` compares ids (once each side), milestone titles/membership, task titles, `repo`/`repository`, `after`, stated `verify` against a command verification and a legacy same-scale `risk`; what PLAN.md does not state is not a contradiction. (2) Approval (`plan approve`, web, handoff) validates then freezes the approved bytes; `bind_approved` is the single launch gate (valid, consistent, exactly the latest frozen revision; `PLAN_DRIFT` instead of freezing an edit; `PLAN_NOT_FROZEN` when nothing was ever frozen: a launch never creates the approval record, only the approval act or an explicit `--force` does) and runs in standard (after the repositories exist, so evidence is verifiable), web, handoff, foreground (+ its successor helper) and `bt_run._open` for NEW runs; a RESUMED run is not rewritten but refuses unapproved content; the gate fails closed. (3) Schema 1.1.0 makes `classification_evidence` mandatory: per dimension a justification (>= 4 words, no placeholder, not repeated) and typed references with recognisable shape (`file` concrete, `command: cmd -> seen`, `precedent` id/commit/URL, `spec` with heading anchor, `task`, `assumption`); unverifiable `file:` evidence is an error at approval/launch; `confidence: high` cannot rest on assumptions; unordered tasks sharing a path/resource cannot claim `coupling: low`; 1.0.0 documents keep loading (findings are warnings) and new revisions below 1.1.0 are refused by `check`.
- **Alternatives:** keep evidence optional (the owner asked to require it); make 1.0.0 invalid (breaks the frozen REQ-009/010 revisions); freeze at launch without a drift refusal (approves unreviewed edits); judge evidence with a model (not deterministic, not stdlib-only); compare prose (false positives).
- **Consequences:** + a scheduler can trust task titles, repos, dependencies, verification and classification arguments; + no launch path runs content nobody approved; − textual rules cannot judge truth (a fluent but false justification passes; only existence of cited files/specs/tasks is verified); − a plan approved by hand-editing `status:` must be frozen explicitly (`plan-json freeze`) before it can launch; the manifest records `source` (approval|launch-forced); − `command:`/`precedent:` references are verified for existence only through the methodology adapter, never for truth.
- **Rollback:** the gate is `bt_plan_adapter.launch_problem` called from four places; removing those calls restores the previous behaviour. `evidence.py`/`quality.py` are additive; set `schema_version` 1.0.0 to opt out per plan (publication gate then refuses new revisions, existing frozen ones stay valid).
- **Evidence:** `requirements/REQ-012-*/REPORT.md`, `ACCEPTANCE.md`, `AC-TRACE.md`, `planning-trials/RESULTS.json` (6 implementer trials, 182 checks), `independent-evidence/` (3 context-free planner plans verified 3/3, Gemini delegated audit C1-C4 hold); module suite 201 tests; methodology 953. ID from `bitacora.py id D`.

## D-022 — The Scheduler Core (M1) is an isolated module with one authority per requirement; approval is a hash
- **Date:** 2026-10-14 · **Status:** Accepted under REQ-011 (owner's `/goal`, `PLAN-SCHEDULER-CORE-M1.md`)
- **Context:** The marathon supervisor schedules from PLAN.md and `RUN.json` with four unrelated locks, resource tags that are not locks, and a `plan_ref` that is recorded but not enforced on resume. The Scheduler needs a deterministic core that other modules (decision, executor, monitor, recovery) can plug into without AI inside it.
- **Decision:** `skill/scripts/bt_scheduler_core/` (stdlib only, ports as Protocols, SQLite WAL or in-memory repository, write-ahead outbox, fencing tokens, independent verdicts) reached only through `bt_scheduler_adapter.py`. A run is owned by the core's database xor the legacy `RUN.json`; the database decides. Approval is a caller-supplied sha256 of the frozen revision (no hash, no run). The projection is `RUN.projection.json`, never `RUN.json`; the database lives in `<root>/.state/scheduler/`. Only an independent verdict completes a task; uncertainty keeps the reservation.
- **Alternatives:** extend `bt_run*` in place (couples the core to the supervisor and live `RUN.json`); migrate historical runs (rewrites evidence); write the projection as `RUN.json` (legacy web controls could write into it); keep the database beside the plan (a live SQLite file in versioned documents).
- **Consequences:** + the core is testable alone (234 module tests, fuzzed invariants, crash at every commit, real processes); + legacy runs stay byte-identical; − two run models coexist until adoption (P-026); − M2–M5 are only simulated (P-020).
- **Rollback:** remove the two-line guard in `bt_runentry.supervise` and the adapter; the package is additive and nothing else imports it. Run databases under `.state/scheduler/` can be deleted.
- **Evidence:** `requirements/REQ-011-*/REPORT.md` (SC-AC01..20 map, three independent reviews A1–A8 fixed); module 234, integration 28, methodology 797, packaging 11 OK.

## D-023 — Local Laya requires code-reviewed benchmark evidence; deterministic fallback stays authoritative (2026-10-14)
- **Date:** 2026-10-14 · **Status:** Accepted under REQ-013
- **Context:** M2 recalculates quality metrics from local artifacts, but tests demonstrated that self-authored perfect predictions could claim the canonical corpus and declare CUDA without running Laya. Real RTX A3000 measurements also found no confidence cutoff and no held-out improvement over the deterministic route reference.
- **Decision:** Keep deterministic recommendations active unless calibration and the paired held-out gate both pass and the exact digest of all five evidence artifacts appears in `laya_quality_gate.approved_evidence_sha256`. Updating that allowlist is an explicit reviewed contract change; an artifact cannot authorize itself. Keep the current allowlist empty. Local CUDA inference remains available for benchmark and diagnosis; M1 stays the sole authority to accept and reserve a route.
- **Alternatives:** Trust internally consistent reports and rehashed fixtures (rejected: synthetic outputs reproduced a passing gate); enable Laya despite inconclusive/negative evidence (rejected: contradicts the approved quality gate); remove Laya and its benchmarks (rejected: retain reproducible local evaluation and future guarded use).
- **Consequences:** + fabricated or edited results cannot activate route selection; + negative quality evidence remains visible; − Laya does not make live M2 recommendations until a new reviewed benchmark digest is explicitly approved.
- **Rollback:** Do not remove the deterministic fallback or digest check. A future benchmark can add a reviewed evidence digest; to retire Laya, remove its opt-in integration and preserve the evidence files.
- **Source:** [REQ-013 report](requirements/REQ-013-scheduler-m2-decision-engine-with-local/REPORT.md) · [REQ-013 plan](requirements/REQ-013-scheduler-m2-decision-engine-with-local/PLAN.md)

## D-024 — M3 agent executor: isolated module, shim-owned agents, no model choice (2026-10-14)
- **Decision:** `bt_scheduler_executor` (stdlib only, own types, five ports) reached only through `bt_scheduler_executor_adapter.py`; each agent runs under a detached double-forked shim so exit status/output survive an executor restart; work is preserved at every end as a snapshot commit under `refs/m3/*`; Gemini = Antigravity `agy`; M3 rejects any route reference it cannot resolve (never defaults a model).
- **Alternatives:** agents as direct children (lose exit status on restart); reuse `bt_worktree.allocate` (random suffix, not idempotent per attempt); standalone `gemini` CLI (no profile/quota support).
- **Consequences:** + exactly-once start and recoverable work under crash tests; − POSIX only; events reach M1 through the adapter until M4 exists.
- **Evidence:** `requirements/REQ-014-*/REPORT.md` (3 independent reviews, ~45 findings fixed; 243 module + 132 integration tests; real CLI run).
- **Addendum (2026-10-14, round-2 audit):** branches and handoff refs are scoped by executor root (`m3/<attempt>-<root hash>`, `refs/m3/handoff/<attempt>-<root hash>`) because they live in the shared repo and two runs of one plan reuse attempt ids; `exit.json`/`shim.json` are shape-checked (forged = `lost`); PREPARING attempts are re-driven; cwd sweep only for an exclusive worktree; routes carry `account_ref`/`single_use` and are re-validated at launch (TOCTOU). Residual gaps are P-029 and README §Known limits.

## D-025 — Scheduler hand-over of prerequisite work is on by default; routes are bound to their task; the sweep spares terminal processes (2026-10-15)
- **Decision:** `wire(integrate_predecessors=True)` is the default: a dependent task starts from a commit merging its accepted same-repository predecessors' handoff snapshots, and a predecessor accepted WITHOUT a captured snapshot (for example resolved by hand) rejects its dependents with `PREDECESSOR_HANDOFF_MISSING` instead of running on a stale tree (`integrate_predecessors=False` restores the old behaviour). M2 exposes `resolve_executor_binding` (plan/revision/task + `superseded_by`) and M3 refuses a decision made for another task or already replaced. The M3 cwd sweep spares a process with a controlling terminal that is not a live descendant of the attempt (`Config.spare_interactive`, default True).
- **Alternatives:** keep integration opt-in (silent stale trees); auto-resolve merge conflicts (guessing); track the agent's descendants from the shim (see P-033).
- **Consequences:** + dependent tasks see their predecessors' work; + a stale or foreign route cannot launch; − an agent that daemonises onto its own terminal (tmux/screen) is spared by the sweep and may write during the handoff; − an M2 ledger file must be per project.
- **Evidence:** commits on `feat/scheduler-m2-m3`; two antagonist reviews (A1-A7, then A1-A4) with fixes; 372+ tests, 8-way stress clean.

## D-026 — The 85% Laya complexity investigation is English-only
- **Date:** 2026-10-15 · **Status:** Superseded by D-027
- **Context:** The owner narrowed the task-complexity target after multilingual comparisons produced weak results and added evaluation cost without useful progress toward the English target.
- **Decision:** Use only English task text and the pinned `english` Laya checkpoint for all remaining inference, training, model selection, and final evaluation for the approximately 85% four-class Planner-complexity objective. Keep previous multilingual and typed-decisions results only as historical diagnostics. Keep the separate M2 route-quality gate distinct.
- **Alternatives:** Continue multilingual/typed-checkpoint comparisons (rejected by the owner as wasted effort); claim language coverage without English-only evidence (unsupported).
- **Consequences:** + narrower, reproducible goal / − no Spanish or other-checkpoint performance claim; independent labels and an untouched English test remain required.
- **Source:** [day log](2026-10/W3/2026-10-15.md) · REQ-015

## D-027 — All remaining Scheduler Laya experiments use the English checkpoint on English tasks
- **Date:** 2026-10-15 · **Status:** Accepted
- **Context:** The owner narrowed the work to improving the English Laya path and directed that it be the only path used. The approximately 85% Planner classifier target and M2 route-quality target remain separate metrics.
- **Decision:** For all remaining REQ-015/REQ-016 experiments, use only the pinned `english` checkpoint and English task text. Keep multilingual and typed-decisions measurements as historical diagnostics only. Do not infer route quality from complexity accuracy or modify M1/M2 runtime authorization.
- **Alternatives:** Continue Spanish/multilingual or typed-checkpoint experiments (rejected by the owner); combine the two quality targets (invalid because they measure different decisions).
- **Consequences:** + one model/input path for reproducible work / − no language-coverage claim outside English; independent labels and an untouched English holdout remain required.
- **Source:** [day log](2026-10/W3/2026-10-15.md) · REQ-015, REQ-016

