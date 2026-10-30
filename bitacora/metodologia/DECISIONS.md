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
- **Decision:** (1) PLAN.md is parsed with its silent drops reported and `check` compares ids (once each side), milestone titles/membership, task titles, `repo`/`repository`, `after`, stated `verify` against a command verification and a legacy same-scale `risk`; what PLAN.md does not state is not a contradiction. (2) Approval (`plan approve`, web, handoff) validates then freezes the approved bytes; `bind_approved` is the single launch gate (valid, consistent, exactly the latest frozen revision; `PLAN_DRIFT` instead of freezing an edit; `PLAN_NOT_FROZEN` when nothing was ever frozen: a launch never creates the approval record, only the approval act or an explicit `--force` does) and runs in standard (after the repositories exist, so evidence is verifiable), web, handoff, foreground (+ its successor helper) and `bt_run._open` for NEW runs; a RESUMED run is not rewritten but refuses unapproved content; the gate fails closed. (3) Schema 1.1.0 makes `classification_evidence` mandatory: per dimension a justification (>= 4 words, no placeholder, not repeated) and typed references (cross-vendor audit hardened: file evidence concrete without wildcards, `command:` must name an existing executable AND the script/npm script it runs, precedent families this workspace keeps, no repeated placeholders, parallel-safety promises in titles/objectives refused, glued scheduling keys such as `modelhint` refused, JSON `null`/duplicate keys/surrogates/giant versions refused, PLAN.md prose digest bound at approval) with recognisable shape (`file` concrete, `command: cmd -> seen`, `precedent` id/commit/URL, `spec` with heading anchor, `task`, `assumption`); unverifiable `file:` evidence is an error at approval/launch; `confidence: high` cannot rest on assumptions; unordered tasks sharing a path/resource cannot claim `coupling: low`; 1.0.0 documents keep loading (findings are warnings) and new revisions below 1.1.0 are refused by `check`.
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
- **Date:** 2026-10-15 · **Status:** Superseded by D-029
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

## D-028 — The REQ-016 synthetic benchmark uses rubric-derived labels without a human-review gate
- **Date:** 2026-10-15 · **Status:** Accepted under the owner's request to build and test an English task suite locally
- **Context:** The provisional English classifier scored 41.5%, equal to its majority baseline, and its examples had
  already been shown to Laya. A fresh evaluation needs frozen labels before inference, family-disjoint splits, and a
  clear statement of what its score can establish. Requiring reviewers to validate a deliberately synthetic oracle
  would block the requested controlled benchmark without making it evidence about natural tasks.
- **Decision:** For REQ-016, derive labels from structured scenario facts through the frozen Planner reasoning rubric
  before rendering task text. Build disjoint English train/development/locked-test sets, use only the pinned `english`
  checkpoint, and do not require human review for claims limited to agreement on this synthetic suite. Any claim about
  real production tasks requires a separate naturally sampled English set with independent human labels. Keep
  complexity evaluation separate from M2 route quality and runtime authorization.
- **Alternatives:** Block synthetic evaluation on two reviewers (unneeded for a constructed oracle); label tasks from
  Laya predictions (circular); treat synthetic scores as production accuracy (unsupported).
- **Consequences:** + local suite and training can proceed reproducibly / − the benchmark cannot establish real-task
  accuracy, prevalence, or future task-success probability.
- **Source:** [REQ-016 plan](requirements/REQ-016-train-and-validate-an-english-only-laya/PLAN.md) · D-027

## D-029 — M3 predecessor hand-off, task-bound routes, and pidfd-safe terminal sweep (2026-10-15)
- **Date:** 2026-10-15 · **Status:** Accepted · **Supersedes:** D-025
- **Context:** D-025 combined three M3 decisions. Its predecessor hand-off and route-binding choices remain correct; its terminal rule spared an agent's terminal child after it re-parented before settle. Checking a saved PID/start identity and then calling `os.kill(pid, ...)` also left a PID-reuse race between validation and signal delivery.
- **Decision:** Keep `wire(integrate_predecessors=True)` as the default: a dependent task starts from a commit merging accepted same-repository predecessor handoff snapshots, and an accepted predecessor without a captured snapshot rejects its dependents with `PREDECESSOR_HANDOFF_MISSING` (`integrate_predecessors=False` restores the old behavior). M2 exposes `resolve_executor_binding` (plan/revision/task + `superseded_by`); M3 refuses a decision made for another task or already replaced. For the M3 cwd sweep, the shim samples Linux `/proc` every 0.1 seconds while the agent runs and atomically stores up to 4,096 observed descendant PID/start identities in a versioned `descendants.json`; scanning is bounded to 16,384 process entries per pass. Settle validates that record and spares an interactive process unless it remains below a verified attempt root or its PID/start identity matches the record. Before signaling an eligible terminal process, open a pidfd, recheck identity, cwd, terminal status and ownership, then signal through that pidfd. If pidfd support is unavailable, preserve terminal processes. `spare_interactive=False` continues to sweep all processes in the exclusive worktree.
- **Alternatives:** keep predecessor integration opt-in (stale trees); auto-resolve merge conflicts (guessing); skip task-bound route checks (foreign decisions); retain the terminal leak; signal by PID after an identity check (race); treat an unvalidated or stale process record as proof (unsafe).
- **Consequences:** + dependents see accepted predecessor work; + stale or foreign routes cannot launch; + orphaned agent terminals can be stopped without targeting recycled PIDs; + operator terminals remain protected; − sampling can miss a daemon re-parented between scans or one that changes cwd away; − on Linux kernels without pidfd support, interactive processes are spared even if they belonged to the agent; − an M2 ledger file must be per project.
- **Rollback:** use `integrate_predecessors=False` to restore the previous hand-off behavior. `spare_interactive=False` explicitly restores unconditional cleanup within an exclusive worktree. Roll back route binding or the pidfd sweep by reverting their corresponding code changes.
- **Evidence:** P-033 regressions, M3 module suite (272 tests) and integration suite (138 tests) in `requirements/REQ-014-scheduler-m3-agent-executor/REPORT.md`; Python 3.9+ `os.pidfd_open` and Linux 5.3+ `signal.pidfd_send_signal` official availability; the project requires Python 3.12+.
- **Source:** P-033 in `PENDING.md`; [REQ-014 report](requirements/REQ-014-scheduler-m3-agent-executor/REPORT.md); [Python `os.pidfd_open`](https://docs.python.org/3/library/os.html#os.pidfd_open); [Python `signal.pidfd_send_signal`](https://docs.python.org/3/library/signal.html#signal.pidfd_send_signal).

## D-030 — M4 is an isolated observer with its own SQLite store
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-017 (owner approval in chat)
- **Context:** M1, M2, and M3 own separate contracts and persistence; M4 needs restart-safe cursors, retention, and an incident outbox.
- **Decision:** Create `bt_scheduler_monitor` as an isolated standard-library package with its own project-scoped SQLite WAL database. Reach it through one methodology adapter; do not import sibling modules or write into M1/M3 stores.
- **Alternatives:** Put monitor state in M1 or M3 databases (breaks ownership); reuse legacy monthly JSONL (no transactional cursor/outbox); add a service database (unneeded deployment dependency).
- **Consequences:** + clear ownership and isolated tests; − a separate database lifecycle and idempotent cross-module delivery are required.
- **Rollback:** Stop monitor ingestion and adapters; preserve M4 history for export and leave M1/M3 stores untouched.
- **Source:** [REQ-017 plan](requirements/REQ-017-scheduler-m4-agent-monitor/PLAN.md) · ADR-001.

## D-031 — M3 exposes a separate bounded nonblocking stream to M4
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-017 (owner approval in chat)
- **Context:** M3 owns process pipes and currently reports lifecycle facts through M1; M4 needs live output without delaying M3 or changing lifecycle semantics.
- **Decision:** Add a versioned private POSIX FIFO per execution, keep it separate from M1 lifecycle events, use nonblocking frames no larger than `PIPE_BUF` (initial Linux payload cap 3,840 bytes), independent stream offsets, bounded 10,000-frame/16 MiB buffering, and explicit durable loss summaries.
- **Alternatives:** Have M4 read child pipes (breaks M3 process ownership); send chunks through M1 (mixes lifecycle and stream traffic); persist raw streams in M4 (unbounded and sensitive); use an external service (unneeded network boundary).
- **Consequences:** + M3 remains responsible for process I/O and can continue draining under backpressure; − M3/M4 require coordinated gap, cursor, and restart tests.
- **Rollback:** Disable M4 stream registration and retain existing lifecycle and bounded M3 output artifacts.
- **Source:** [REQ-017 plan](requirements/REQ-017-scheduler-m4-agent-monitor/PLAN.md) · ADR-002.

## D-032 — M4 incidents are advisory and M1 remains authoritative
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-017 (owner approval in chat)
- **Context:** Monitor detections may indicate quota, authentication, transport, or process inconsistencies but cannot own execution state or recovery.
- **Decision:** M4 stores full incidents and sends only an idempotent versioned audit reference to M1; M2 reads provenance-aware metrics. M1 task/attempt state and M3 process control stay authoritative; no incident triggers recovery or completion.
- **Alternatives:** Let M4 transition M1 state or trigger retries (duplicates M1/M5 authority); keep incidents only in M4 (loses the requested audit reference).
- **Consequences:** + future M5 can consume durable evidence without coupling M4 to recovery; − capability negotiation and retryable outbox delivery are required.
- **Rollback:** Stop outbox delivery and M2 metric reads; preserve M4 evidence without changing current M1 state.
- **Source:** [REQ-017 plan](requirements/REQ-017-scheduler-m4-agent-monitor/PLAN.md) · ADR-003.

## D-033 — M4 minimizes persisted data and uses bounded retention
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-017 (owner approval in chat)
- **Context:** Provider output can contain secrets, prompts, code, reasoning, tool arguments, and private project data; unbounded data also risks disk exhaustion.
- **Decision:** Persist only typed allowlisted metadata and bounded redacted evidence/digests; never store raw provider bytes. Limit normalized records to 16 KiB, evidence excerpts to 4 KiB, SQLite database plus WAL to 512 MiB, normalized event detail to 90 days, resolved incident detail to 365 days, and daily aggregates to 730 days. Keep open incidents and bounded undelivered outbox records. Under pressure, prune eligible detail and compact aggregates first; if the cap still prevents writes, expose degraded state and explicit gaps without fabricating resolution or delivery.
- **Alternatives:** Store raw JSONL indefinitely (sensitive and unbounded); delete all evidence at run end (insufficient audit trail).
- **Consequences:** + bounded storage and lower exposure; − evidence is less detailed and parser evolution relies on versioned normalizers.
- **Rollback:** Disable optional evidence capture or shorten retention; never restore raw stream persistence.
- **Source:** [REQ-017 plan](requirements/REQ-017-scheduler-m4-agent-monitor/PLAN.md) · ADR-004.

## D-034 — M4 detector defaults remain deterministic, configurable, and advisory
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-017 (owner approval in chat)
- **Context:** M4 needs testable defaults while avoiding false process-death or progress claims.
- **Decision:** Use an initial missed-heartbeat threshold of 90 seconds, an informational silent-but-live notice after five minutes, repetitive-activity notice at 20 matching events in five minutes, a two-second authorized-cancel drain grace, and a 30-second source-disagreement reconciliation window. Keep thresholds configurable and validate them with deterministic fixtures; establish CPU/RSS/throughput/p95 limits only from T12's simulated baseline. No threshold changes M1 state or signals a process.
- **Alternatives:** Treat silence as failure (false positives on long operations); set unmeasured runtime budgets (unsupported); infer progress semantically (violates the deterministic M4 boundary).
- **Consequences:** + deterministic and testable alerts with explicit confidence; − thresholds may need revision if fixture and measured workload evidence contradicts them.
- **Source:** [REQ-017 architecture](requirements/REQ-017-scheduler-m4-agent-monitor/M4-ARCHITECTURE.md) · owner approval in chat.

## D-035 — Pause REQ-016 Laya classifier training while Scheduler M2 is the active focus
- **Date:** 2026-10-15 · **Status:** Accepted at the owner's direction.
- **Context:** The v4 locked task test scored selected Laya at 65.6% versus 78.7% for the deterministic reference; the 91.33% answer-tag control deliberately exposed labels and is not task accuracy. A four-layer AMP/checkpointing run was interrupted before development evaluation, with an AMP scheduler-order warning.
- **Decision:** Keep REQ-016 paused, preserve but do not select its partial checkpoint, and focus on M2 closeout. M2 continues deterministic live recommendations under D-023; the Laya allowlist remains empty. Resume classifier experiments only after owner reprioritization and a materially new evaluation approach.
- **Alternatives:** Continue the interrupted recipe or treat the answer-tag control as accuracy (rejected: no completed task score and explicit label leakage); enable Laya routing despite the negative held-out comparison (rejected by D-023's quality gate).
- **Consequences:** + no more GPU time is spent on the current underperforming recipe; + M2 remains safe and usable; − the 85% Planner-complexity target remains unachieved and paused.
- **Source:** [REQ-016 plan](requirements/REQ-016-train-and-validate-an-english-only-laya/PLAN.md) · [REQ-013 report](requirements/REQ-013-scheduler-m2-decision-engine-with-local/REPORT.md).

## D-036 — M3 must recheck persisted M2 quota evidence at launch
- **Date:** 2026-10-15 · **Status:** Accepted as a correction to the M2/M3 route contract.
- **Context:** M2 excluded unknown and stale quota correctly, but its persisted selected route retained only a quota snapshot hash. The M2 lookup therefore omitted the sample expiry and M3 could launch a queued route after that evidence expired. The Codex usage schema also exposes explicit usage-denial state and model-specific quota buckets that its reader previously ignored.
- **Decision:** Persist each eligible route's quota observation time, measured usage percentage and validity deadline in the M2 route summary. Pass the deadline through the M3 route record and reject absent, malformed or expired evidence at resolution and immediately before launch. Honor explicit Codex usage-denial fields; include model-specific buckets by exact `normalModelSlug`, and fail closed when a returned bucket cannot be mapped or parsed. Read legacy 1.0.0 ledger records, but do not launch them without quota evidence.
- **Alternatives:** Trust the quota timestamp only at recommendation time (allows delayed queued routes past freshness); treat missing Codex permission/bucket fields as available (turns unknown quota into inferred headroom).
- **Consequences:** + expired or unknown quota can no longer pass the M2→M3 handoff; + stored decisions expose the exact sample/deadline used. − older route references without evidence fail closed and need a new M2 recommendation; quota can still change server-side after a valid usage read.
- **Rollback:** Disable the M2 route lookup and use an explicit operator route only when the caller deliberately permits direct routes; do not restore implicit quota trust.
- **Source:** REQ-013 M2 closeout and the Codex [app-server rate-limit schema](https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/schema/json/v2/GetAccountRateLimitsResponse.json).

## D-037 — M4 uses host-local fixture budgets from the T12 measurements
- **Date:** 2026-10-15 · **Status:** Accepted under the owner-approved REQ-017 plan; D-038 corrects the sample count.
- **Context:** REQ-017 requires runtime budgets to come from a reproducible three-agent fixture run. Thirteen 300-event runs on Linux 7.2.6, Python 3.14.7 and 16 logical CPUs measured 823.60–961.40 events/s, p95 289.45–339.40 ms, CPU 0.309–0.361 s and sampled RSS 26,344–26,640 KiB, with zero drops.
- **Decision:** Set the same-host fixture budget to throughput ≥800 events/s, p95 ≤350 ms, CPU ≤0.38 s, sampled RSS ≤27,000 KiB and zero loss for the 300-event fixture. These rounded limits extend beyond the slower/higher observed edge to accommodate measured run-to-run variation. They describe the synthetic burst/drain workload and are not production SLOs; remeasure when the host or workload changes.
- **Alternatives:** Leave budgets unset (misses the approved T12 deliverable); advertise them as production capacity (unsupported by the fixture workload).
- **Consequences:** + Provides measured host-local budget bounds; − does not establish sustained provider or SQLite contention capacity.
- **Rollback:** Replace the bounds only after repeating the fixture on the target host/workload and recording the measurements; keep them labeled as fixture evidence.
- **Source:** [REQ-017 plan](requirements/REQ-017-scheduler-m4-agent-monitor/PLAN.md), [M4 baseline](requirements/REQ-017-scheduler-m4-agent-monitor/REPORT.md).

## D-038 — Correct the T12 fixture sample count; retain D-037 budgets
- **Date:** 2026-10-15 · **Status:** Accepted as a measurement correction under the owner-approved REQ-017 plan.
- **Context:** A final audit found fourteen preserved 300-event reports with a 300-frame / 5,100-byte queue, three simulated producers, and the same host/fixture. The prior report counted thirteen. The separate direct-SQL report had no queued consumer and is excluded.
- **Decision:** Record fourteen comparable queue/consumer runs. Keep D-037's host-local fixture limits unchanged: throughput ≥800 events/s, p95 ≤350 ms, CPU ≤0.38 s, sampled RSS ≤27,000 KiB, and zero drops. These are synthetic burst/drain regression bounds, not production SLOs.
- **Alternatives:** Keep the thirteen-run count (inaccurate); include the direct-SQL check (different measurement path, with no queue).
- **Consequences:** + Aligns the documented sample count with preserved reports; − the budget still describes burst/drain behavior, not sustained SQLite contention.
- **Rollback:** Append a new correction if a preserved report is later shown not to meet the stated queue/fixture criteria; do not rewrite the evidence.
- **Source:** [REQ-017 report](requirements/REQ-017-scheduler-m4-agent-monitor/REPORT.md) · preserved `/tmp/req-017-m4-*.json` benchmark reports.

## D-039 — Keep M1–M4 ingestion caller-driven at the M1 ownership boundary
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-018.
- **Context:** The M3 FIFO, M4 durable store, M2 read-only metric history, and M1 incident reference port needed one integrated runtime path without changing the global Scheduler activation policy or duplicating module authority.
- **Decision:** Enable M4 only when the methodology `wire()` caller supplies a separate `monitor_store_path`. The owning M1 loop invokes `Wiring.drain_stream(attempt_id, run_id)` to drain bounded M3 batches into M4; M2 reads metric snapshots without mutation, and an owner-controlled retry cadence delivers M4 incident references to M1. Do not add a global/background poller or let M4 change task/attempt state.
- **Alternatives:** Have M4 read child pipes (breaks M3 ownership); auto-start an independent poller (silently changes activation and lifecycle); persist into M1/M3 databases (crosses ownership); let incidents trigger task state (turns observations into decisions).
- **Consequences:** + M1 remains the single run-state owner and the bridge is testable end to end; + M4 stays optional. − The caller must drain during execution and after terminal output; undrained in-memory frames can be lost on process restart.
- **Rollback:** Omit `monitor_store_path` to disable M4 runtime wiring while preserving M1–M3 execution and their existing contracts.
- **Source:** [REQ-018 plan](requirements/REQ-018-scheduler-m1-m4-integration-and-offline/PLAN.md) · [M4 operations](../../skill/scripts/bt_scheduler_monitor/README.md).

## D-040 — Recover M4 only through a verified offline candidate
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-018.
- **Context:** At the hard store cap, retention intentionally preserves open incidents and undelivered M1 outbox records. Recovery must not destroy the source database or those protected records.
- **Decision:** Stop all M4 writers, publish a no-overwrite owner-only full archive and integrity manifest, verify them, then prepare and verify a bounded candidate from a disposable copy. The workflow never edits the source, overwrites an artifact, or activates/restores the candidate; restore remains an explicit operator action.
- **Alternatives:** Delete protected rows or rewrite the live database in place (loses evidence and makes rollback uncertain); automatically replace the active store (unreviewed authority transfer); raise the cap or change journal mode (evades the approved store bound).
- **Consequences:** + Source and protected evidence remain recoverable and candidate integrity is independently checked. − Archive, preparation, and operator-managed restore require downtime and extra disk space.
- **Rollback:** Discard an unaccepted candidate and continue using the preserved source; if the operator later restores, retain the full archive for recovery.
- **Source:** [REQ-018 plan](requirements/REQ-018-scheduler-m1-m4-integration-and-offline/PLAN.md) · [M4 recovery operations](../../skill/scripts/bt_scheduler_monitor/README.md).

## D-041 — M5 advises through the unchanged RecoveryPort and preserves same-task snapshots
- **Date:** 2026-10-15 · **Status:** Accepted through David's explicit M5 implementation request.
- **Context:** M1 has a recovery port but lacks structured M3 evidence and a durable policy ledger; retries start
  from the original/predecessor base and do not automatically continue partial work.
- **Decision:** Add an isolated deterministic M5 package and one adapter, using unchanged M1 contract 1.2.0.
  Enrich cases from public, identity-checked M1/M3 read views; keep only opaque evidence hashes in M5. Bound waits,
  attempts, repeated causes and the private SQLite decision ledger. A full/unavailable ledger blocks visibly.
  Opt-in wiring resumes a failed/rejected task from its verified M3 snapshot and a sanitized note, while normal
  M1 assignment invokes M2 again. M4 stays advisory; M6 alone accepts work. Tighten finite wait validation in M1.
- **Alternatives:** Extend M1 failure types (unnecessary with existing reads); parse logs (untrusted and sensitive);
  embed routing/process control in M5 (duplicates owners); retry from HEAD (loses partial progress).
- **Consequences:** No M1 schema/signature migration; no M2/M4 dependency for pinned operation. Unknown/live/stale
  evidence blocks automatically. Decision-cap pressure needs operator intervention instead of losing dedupe history.
- **Rollback:** Omit recovery_store_path; preserve M5 history and M3 worktrees/refs. Existing recovery= ports remain
  supported; no legacy RUN or live configuration is migrated.
- **Source:** REQ-019 SPEC and `/home/david/PLAN-FASE-5-M5-RECOVERY-MANAGER.md`.


## D-042 — Add batch quota learning above the existing M1/M2 boundary

REQ-020 preserves the per-task M2 API and adds a versioned batch layer using cached, account-deduplicated quota windows. Only independent outcomes correlated to the same task attempt may inform learning; missing evidence remains unknown. M1 keeps task, reservation and retry authority; M5 advises only through M1; M2 never calls M5. M4/M6 observations stay optional. Laya remains guarded, and the real-provider experiment requires explicit owner authorization. Full context, alternatives, consequences and rollback: `requirements/REQ-020-scheduler-m2-learning-and-quota-optimiza/CONTRACTS.md` and the decision note.

## D-043 — Integrate M6 through the existing opt-in VerificationPort
- **Date:** 2026-10-15 · **Status:** Accepted by David's explicit request to wire all Scheduler phases through M6.
- **Context:** The isolated M6 package verifies M3 snapshots and returns correlated M1 verdicts, but the current shared
  M4/M5 checkout has no central runtime wiring. M6 was built on an older base; current M1 is contract 1.2.0 and its
  verification signatures remain compatible. The M6 worktree's REQ-020/D-042 identifiers conflict with current M2 work.
- **Decision:** Integrate only M6 code into the current tree and compose it through the existing `VerificationPort` when
  the caller explicitly supplies `quality_store_path`; otherwise keep the existing injected verifier. Use the public
  M1/M3 adapters, preserve M1 as the only state/verdict owner, and keep `NEEDS_REVIEW` in `VERIFYING` until an explicit
  operator resolution. Do not change M1 contracts or enable M6 globally.
- **Alternatives:** Leave M6 separately bindable (does not satisfy the owner's full-chain request); place verification
  inside M1/M5 (duplicates ownership); add a third M1 verdict state (unneeded contract migration).
- **Consequences:** + A full deterministic M3→M6→M1→M5→M2 retry loop can be exercised; + current caller-selected
  verification remains compatible. − Each M6-enabled caller must configure a private store path and bubblewrap; pending
  manual checks stay verifying and require operator action. The M5 live T19 provider gate remains separate.
- **Rollback:** Omit `quality_store_path` to restore caller-controlled verification; no schema or production-data
  migration is required. Preserve M6 evidence if any runtime has used the store.
- **Source:** David's active full-chain request; [REQ-021 SPEC](requirements/REQ-021-scheduler-m5-m6-runtime-integration/SPEC.md); M6 isolated SPEC at `/home/david/dev/metodologia-m6-quality/bitacora/metodologia/requirements/REQ-020-scheduler-m6-quality-integration/SPEC.md`.

## D-045 — Keep M2 route quality floors explicit and evidence-backed
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-020/T14.
- **Context:** T10 exposes contextual aggregates from correlated M1-applied outcomes, while the adapter's existing `bt_events` history lacks full attempt/decision/verdict correlation. The approved plan names quality floors but supplies no numeric thresholds by risk.
- **Decision:** Define `m2-route-policy-v1` as a fixed lexicographic policy after hard eligibility filters. Use only route- and API-matched contextual assessments with at least five correlated verified samples; treat Wilson bounds and interval width as descriptive features, not future success probabilities. Leave numeric risk floors unset until approved values exist; when quality evidence is unavailable, retain the existing deterministic baseline. Compare relative cost only when all eligible routes share a declared scale; prefer an upcoming reset only when its window is the most restrictive. Keep strategic reserves and router rank as explicit late objectives, with route ID as the stable final tie-break. Do not use a weighted sum.
- **Alternatives:** Promote legacy `bt_events` as verified quality (rejected: missing correlation); guess numeric floors or cost conversions (rejected: no approved threshold or common unit); let any short-window reset outrank weekly/model pressure (rejected: it can consume capacity needed by a stricter window).
- **Consequences:** + Hard eligibility remains irreversible; + unknown quality falls back safely; + typed policy facts are ready for T15. − No risk-specific quality floor is active until a threshold and correlated source are supplied; the existing per-task engine remains on its deterministic baseline until batch integration.
- **Rollback:** Stop calling `rank_with_route_policy` and retain `rank_candidates()`; no API or persisted-ledger migration is required.
- **Source:** [REQ-020 contract](requirements/REQ-020-scheduler-m2-learning-and-quota-optimiza/CONTRACTS.md) · T14 implementation and tests.

## D-046 — Select bounded READY batches with effective-account capacity matching
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-020/T15.
- **Context:** Selecting each READY task independently can let a flexible task consume the only account available to a constrained task. M1 provides one `free_slots` snapshot and remains the only reservation authority; the T14 route policy already ranks each task's hard-eligible routes.
- **Decision:** Define `m2-bounded-batch-v1` as a pure capacity-aware selector over the supplied task requests from one plan/revision/hash/time/slot snapshot. Collapse routes sharing an effective `account_ref` to the best route under T14, then use deterministic capacitated matching: tasks with fewer eligible accounts first, then task ID; route-policy order and route ID break route ties. Maximize feasible distinct-task assignments up to `free_slots`. A declared account limit grants `max(0, max_concurrent - active_assignments)` proposals; an absent limit adds no inferred per-account cap. Return canonical input/batch hashes and stable selection/no-assignment reasons, but create no durable reservations.
- **Alternatives:** Rank each task separately (can miss feasible assignments or overuse a shared constrained account); reserve capacity durably in M2 (duplicates M1 authority); guess a per-account limit when none is supplied (unsupported evidence).
- **Consequences:** + The helper is deterministic, bounded to 128 tasks and 4,096 candidates/edges, and can move a flexible task to an alternative account; + M1 remains final authority. − The current M1 adapter still uses its per-task loop until T18 wires this selector; missing concurrency data remains an explicit limit on what the selector can enforce.
- **Rollback:** Leave `plan_ready_batch()` unused and retain the current adapter flow; no persisted data or M1 state needs migration.
- **Source:** REQ-020/T15 implementation and `bt_scheduler_decision.tests.test_batch`.

## D-047 — Persist redacted M2 batch decisions in ledger schema 3
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-020/T16.
- **Context:** T16 needs replayable evidence for the T15 READY-batch planner. The existing M2 SQLite ledger contains immutable decisions and schema-2 learning snapshots; M1 remains the owner of reservations and dispatch.
- **Decision:** Add an immutable, content-addressed `batch_decisions` table in schema 3. Persist the normalized input fingerprint, canonical checksum-verified plan, selected assignments/reasons, route exclusions and stable unassignment evidence. Keep task prose, raw route-policy evidence and provider output out of storage. Exact replay returns the first verified plan; changed input creates a new row. Cap storage at 10,000 rows and 2 MiB per plan; reject writes at capacity and never prune. Writable schema-1 ledgers migrate through schema 2 to 3; writable schema-2 ledgers add only the batch table. Both migrations preserve existing rows, and read-only schema-1/2 access remains valid at the prior capability.
- **Alternatives:** A separate SQLite file (splits lifecycle and replay evidence); mutating existing decision/snapshot records (breaks immutability); adding a table without bumping schema (misstates compatibility); persisting reservations in M2 (duplicates M1 authority).
- **Consequences:** + M2 gains bounded replayable batch evidence under API 1.2.0 and exports the typed planner contract for T18; + redaction and append-only integrity are checked on read; + M1 continues validating every proposal and owns capacity. − Read-only schema-1/2 binaries must use an unmigrated file and cannot open schema 3; capacity eventually rejects new evidence.
- **Rollback:** Stop batch writes and preserve the schema-3 file. Do not downgrade/drop tables or prune rows. Restore a preserved schema-1/2 backup only if an older binary must be reactivated, retaining the schema-3 evidence separately.
- **Source:** REQ-020/T16, its `api-contract.json`, and batch-ledger/recorder/public-contract tests; full rationale in the [brain decision note](../../../../dev/cerebro/metodologia/decisiones/20261015-m2-batch-decision-ledger-schema-v3.md).

## D-048 — Keep M2 shadow comparisons opt-in and side-effect-free
- **Date:** 2026-10-15 · **Status:** Accepted under REQ-020/T17.
- **Context:** T17 compares the deterministic READY-order baseline with the T15 batch policy. The comparison must use the same input snapshot and capacity and must not let observation change M1/M3 state or dispatch behavior.
- **Decision:** Expose `compare_shadow_batch()` as an opt-in pure API. When disabled it returns `None` before inspecting requests, evidence or capacity. When enabled it returns an immutable in-memory `ShadowComparison` with baseline and proposed results, stable per-task difference codes, snapshot and comparison SHA-256 fingerprints, and explicit false side-effect fields. Both policies use the same normalized request, route-evidence, policy and capacity facts. The comparison is not persisted in M2's ledger; schema 3 remains unchanged. M1 remains final authority.
- **Alternatives:** Persist each shadow result in a new ledger table (adds durable state and a schema migration without a T17 requirement); dispatch the proposed assignment (violates the shadow acceptance boundary); compare different snapshots (makes differences non-attributable).
- **Consequences:** + Callers can replay and audit policy differences without dispatching, reserving capacity, changing task state, writing the ledger or calling a provider. + Disabled mode has no comparison-input traversal. − Shadow evidence is not durable unless a caller separately stores the returned record; M2 does not provide that persistence.
- **Rollback:** Stop calling `compare_shadow_batch()` or keep `enabled=False`; no schema/data migration or cleanup is required.
- **Source:** REQ-020/T17, `api-contract.json`, `test_shadow`, public-contract and boundary tests; full rationale in the [brain decision note](../../../../dev/cerebro/metodologia/decisiones/20261015-m2-opt-in-shadow-comparison.md).

## D-049 — Preserve legacy quota keys while deduplicating effective accounts
- **Date:** 2026-10-16 · **Status:** Accepted under REQ-020/T13.
- **Context:** Profile aliases can select the same provider account through different environment overlays. `account_key()` is also the stable key used by existing quota caches, so changing it to solve in-memory pool deduplication could orphan cached observations.
- **Decision:** Deduplicate `bt_agents.pool_for()` with a provider-specific, normalized account-selector identity, resolving known default account directories in memory. Keep `account_key()` and its persisted quota-cache format unchanged. M2 receives only the opaque `account_ref` derived from the legacy key; it does not own profile authorization or account selection.
- **Alternatives:** Use profile IDs (duplicates capacity for aliases); change the persisted `account_key()` format (breaks cache continuity); or reproduce provider identity logic inside M2 (duplicates the existing owner).
- **Consequences:** Preferred profile ordering still chooses one runtime alias per effective account while existing cache keys continue to resolve. The account-selector list and default-directory mapping remain owned by `bt_agents`.
- **Rollback:** Restore `pool_for()` to its former `account_key()` equality check. No quota cache migration or persisted-data cleanup is required.
- **Source:** REQ-020/T13, `bt_agents._pool_account_identity()`, `test_scheduler_decision_sources` and the effective-account pool-dedup regression.

## D-050 — Keep M2 optimization disabled after the failed T24 experiment
- **Date:** 2026-10-16 · **Status:** Accepted for this T24 closeout.
- **Context:** T24 stopped after T2 exceeded its 300-second attempt limit. Only T1 received an independent verifier result; T3/T4 were left unverified, T5–T8 were not dispatched, the historical artifact lost task-attempt attribution, and the verifier did not enforce declared changed paths. The preflight had two eligible models on one effective account, so account-level routing was not observable.
- **Decision:** Treat the receipt as a failed, partial experiment. Keep M2's deterministic route reference active and do not claim quota savings, improved verified quality or account-level routing. Do not repeat provider calls under this T24 registration. If more live evidence is wanted, define a new bounded experiment, pass a fresh quota preflight and obtain separate explicit owner authorization.
- **Alternatives:** Enable optimization from the one verifier PASS or the selected low model (rejected: the run did not meet its eight-task acceptance and lacks complete attribution/scope evidence); retry T2 in the same run (rejected by the stop-on-failure rule).
- **Consequences:** The current result documents the implementation and failure mode but does not close T24 or justify activation; T25/T26 closeout is recorded while REQ-020 remains in progress.
- **Rollback:** No production setting or code path was activated. A future accepted experiment and explicit owner ruling may supersede this operational decision; retain the private T24 receipt.
- **Source:** [REQ-020 T24 report](requirements/REQ-020-scheduler-m2-learning-and-quota-optimiza/REPORT.md), T24 artifact and P-041.

## D-051 — Expose a bounded Scheduler lifecycle behind explicit opt-in
- **Date:** 2026-10-16 · **Status:** Accepted under REQ-022.
- **Context:** M1/M2/M3 existed as separate modules, but the normal marathon launcher, status views and recovery controls still used the legacy `RUN.json` supervisor. Connecting them must preserve one authority per requirement, approved-plan boundaries and current launcher behavior.
- **Decision:** Add `launch --mode marathon --scheduler` as an explicit opt-in that requires the normal readiness gate and an existing approved, frozen `PLAN.json`. A durable M1 owner composes M2/M3, writes an atomic plan-identified heartbeat projection, resumes the same M1 run after restart and routes CLI/web controls through M1. Scheduler readers trust the database to determine authority, validate the projection, and never fall back to `RUN.json`. Legacy launch remains the default; M4/M5/M6 remain separately opt-in and `NEEDS_REVIEW` remains operator-owned.
- **Alternatives:** Change `launch --mode marathon` to Scheduler (rejected: silently changes existing runs); use the projection as authority or migrate `RUN.json` (rejected: creates split ownership and risks historical state); leave M1 without an owner loop (rejected: no durable composition, heartbeat or restart path).
- **Consequences:** + approved runs can make bounded autonomous progress and recover the same durable M1/M3 state; operators get current status and M1-owned pause/resume/cancel controls. + stale active projections (>2 minutes) and malformed/missing projection state are visible with an exact recovery command. − Starting Scheduler installs a per-user login resume entry unless `--no-autostart` is supplied; notification claims are persisted before best-effort delivery, so unreadable local claim state can skip a notification rather than interrupt execution.
- **Rollback:** Stop launching with `--scheduler`, remove the matching per-user entry through the existing autostart removal path, and preserve the Scheduler database/projection as evidence. Do not convert them into or overwrite historical `RUN.json` state.
- **Source:** REQ-022 SPEC/PLAN and REPORT; `skill/scripts/bt_scheduler_run.py`, `bt_scheduler_adapter.py`, CLI/web views and focused runtime/view/control regressions. Brain note: `decisiones/20261016-scheduler-opt-in-lifecycle.md`.

## D-052 — Require M4-M6 in every Scheduler-owned run
- **Date:** 2026-10-16 · **Status:** Accepted by owner under REQ-023.
- **Context:** M4 monitoring, M5 recovery advice and M6 verification were available only when a caller opted into their ports; the supported Scheduler owner omitted them and did not drain M3 streams or deliver M4 incidents.
- **Decision:** Every `scheduler-run` and `launch --scheduler` runtime composes durable, private M4/M5/M6 stores and connects their ports before M3 dispatch. The M1 owner loop drains bounded M3 output into M4 and delivers audit-only M4 incidents through M1. M5 remains advisory through the existing M1 `RecoveryPort`; M6 verifies through the existing `VerificationPort`, and `NEEDS_REVIEW` remains operator-owned. M1 remains the sole state/verdict authority. Preserve deterministic M2 routing and keep the legacy launcher/default `RUN.json` path separate. Low-level optional composition remains available for isolated tests and explicit custom compositions.
- **Supersedes:** D-043's M6 activation clause and D-051's M4/M5/M6 opt-in activation clause only. The unchanged M1 port contracts, explicit Scheduler opt-in, legacy default and operator-owned review boundary remain in force.
- **Alternatives:** Keep M4–M6 caller-opt-in (rejected: supported runs could silently omit monitoring, recovery advice and verification); migrate the legacy default to Scheduler (rejected: changes established launcher/state behavior); change M1 contracts (rejected: existing ports already provide the required authority boundary).
- **Consequences:** Scheduler-owned runs fail before dispatch if required stores or verifier setup are unavailable. Module stores are separate and resume with the stable runtime identity. Existing M1 authority, M2 route policy, legacy `RUN.json`, and manual review remain unchanged.
- **Rollback:** Stop requiring the three stores at the Scheduler owner boundary and restore the previous opt-in activation clauses; preserve any existing module databases as evidence and do not migrate them into `RUN.json`.
- **Source:** [REQ-023 report](requirements/REQ-023-require-m4-m6-in-the-scheduler-runtime/REPORT.md), owner-approved SPEC/PLAN and offline acceptance. Brain note: `decisiones/20261016-m4-m6-required-scheduler-runtime.md`.

## D-053 — Keep planning aids exclusive to the Planner profile
- **Date:** 2026-10-16 · **Status:** Superseded by D-060 (schema version and contract baseline only).
- **Context:** The owner requested existing skills be selected for the Planner workflow without adding skills indiscriminately, and asked to rerun the Planner on Pictures REQ-017 with Opus 5.5 high.
- **Decision:** Give the Planner profile four nested resources: Socratic elicitation, WBS/dependency decomposition, optional Mermaid flowchart projection, and adversarial plan review. Only the Planner profile is configured to load them; do not add them as generally assigned role skills. Mermaid remains optional: `PLAN.json` has dependency edges but no dates/durations for a Gantt. Preserve schema 1.1.0, milestones/tasks and `after`; do not add parent/child fields or a second DAG contract. The Planner may draft requirement artifacts but must not implement, approve/freeze, or launch work.
- **Alternatives:** Install the resources as global agent skills (rejected: breaks role-specific ownership); add Gantt dates or task hierarchy to the plan contract (rejected: unsupported by current planning needs and schema).
- **Consequences:** Planner runs receive a consistent elicitation, decomposition and self-review process while other profiles remain unchanged. The Opus 5.5 high rerun of REQ-017 passed `bt_planner check`; the preserved draft has one nonfatal unordered shared-resource warning for T2.1/T3.1. Product assumptions remain open and unapproved.
- **Source:** `skill/agents/planner.md`, `skill/agents/planner/skills/`, `skill/references/subagents.md`, and `artifacts/REQ-017-planner-rerun-opus55-high-20261016/RUN.md`. Brain note: `decisiones/20261016-planner-private-skills.md`.

## D-054 — Keep Planner invocation independent of local AI provider
- **Date:** 2026-10-16 · **Status:** Accepted by owner as a requirement scope; REQ-024 plan approval remains pending.
- **Context:** The owner clarified that the Planner should launch through any AI runtime/account already available and configured on this computer. Model-specific quality problems should be handled if and when they occur.
- **Decision:** Keep one provider-neutral Planner instruction source and invoke it through every runtime/account profile registered in the local launcher at the baseline inventory. The caller selects provider, account, model and effort; use a native profile or a thin adapter and never substitute another selection. Do not require quality parity or compare model quality across providers now. Opus 5.5 high remains only the fixed reference run in the existing benchmark. Do not install new AI clients or create accounts/subscriptions.
- **Alternatives:** Pin the Planner to Opus/Claude (rejected: makes availability depend on one client/subscription); require equal quality across all models now (rejected: the owner will address a concrete failure when it occurs); imply support for unconfigured clients with no local launch interface (rejected: the launcher must have a configured runtime/profile).
- **Consequences:** REQ-024 adds runtime/profile inventory, provider-neutral invocation and launch-only coverage. The current inventory is a snapshot of three registered runtimes and five effective accounts; refresh it before execution. This clarification does not approve profile writes, live calls or the complete REQ-024 plan.
- **Source:** Owner clarification in the 2026-10-16 REQ-024 session; `requirements/REQ-024-planner-v2-quality-and-benchmark/SPEC.md` R15 and `PLAN.md` T14–T15. Brain note: `decisiones/20261016-planner-provider-neutral-launch.md`.

## D-055 — Install Planner in every currently configured local AI profile
- **Date:** 2026-10-16 · **Status:** Accepted by owner for this scoped rollout
- **Context:** D-054 established the provider-neutral requirement but left profile writes unapproved. The owner then asked to implement what is needed for any configured local AI account to use Planner.
- **Decision:** Install the existing Planner role through each configured local runtime's native agent format, preserving one instruction source and caller-selected provider, account, model and effort. Cover every currently registered effective account; do not create accounts or install clients. This rollout does not invoke a model or grade model quality.
- **Alternatives:** Wait for the full REQ-024 benchmark plan approval (rejected for this narrow profile-installation scope); pin one provider/model (rejected by D-054).
- **Consequences:** Planner is installed for the current Claude, Codex and Antigravity profiles. The REQ-024 quality/benchmark plan, its review choices and any benchmark model calls remain separately gated by P-103.
- **Source:** Owner request and profile rollout in session `01a1457f`; D-054; `skill/scripts/install_agents.py`.

## D-056 — Route the full approved DAG through M2 at run startup
- **Date:** 2026-10-16 · **Status:** Accepted by owner for Scheduler M1/M2 implementation.
- **Context:** M1 previously asked M2 to choose only among currently READY tasks. The owner wants M2 to receive all tasks and milestones at the start so the run view has complexity and a model recommendation for every task.
- **Decision:** Add the versioned `PlanRoutingPort` as a non-reserving startup contract. M1 sends the full hash-bound DAG, including dependency-blocked tasks, and requires exactly one route result per task before executor reconciliation or dispatch. Persist the route metadata in M1 run-state schema 2 and join it with the frozen plan classification in `RUN.projection.json`. Keep `PLAN.json` immutable, retain the READY-task `AssignmentPort` for a fresh eligibility/quota decision at dispatch, and keep capacity/resource reservations exclusively in M1. M2 does not reserve accounts or concurrency for the future route map.
- **Alternatives:** Write model fields into `PLAN.json` (rejected: changes the approved artifact/hash); reuse the READY-only assignment request for the full DAG (rejected: its free-slot semantics would omit future tasks); let M2 reserve account capacity (rejected: duplicates M1 ownership and cannot be atomic with M1 state).
- **Consequences:** Operators can inspect complexity and the initial model recommendation for every task. The route can change when a task becomes READY, based on current eligibility; the projection marks it as revalidated. An unavailable or malformed initial map stops startup before M3 dispatch. New M1 reads and upgrades schema-1 state to schema 2; old M1 binaries must not open schema-2 state. Verification on 2026-10-16: an isolated simulation of frozen REQ-017 r1 routed all 7 tasks, revalidated T1.1, and retained an undispatched M1 intent; 28 focused offline tests and scoped Ruff passed. The live Scheduler owner process and M3/provider behavior remain untested; P-105 is closed for the isolated M1/M2 scope.
- **Rollback:** Keep the schema-2-aware M1 reader and disable the routing port for newly created runs if necessary. Preserve route decisions and M2 ledger rows; do not downgrade run-state schema or rewrite approved plans.
- **Source:** Owner instruction in session `01a1457f`; `bt_scheduler_core` `PlanRoutingPort`, `DecisionAssignmentPort`, Scheduler projection. Brain note: `decisiones/20261016-m2-full-plan-route-map.md`.

## D-057 — Assign Scheduler M2 routes by task fit and effective-account quota
- **Date:** 2026-10-16 · **Status:** Accepted by owner direction; REQ-025 plan r1 approved and implementation underway.
- **Refines:** D-004 for Scheduler M2 builder selection only; preserves D-045, D-049 and D-056.
- **Context:** The REQ-017 M1/M2 simulation routed five of seven tasks to Claude Sonnet xhigh. M2's generic medium-risk uplift set tier 1 for six tasks; the full-plan adapter then decided each task independently. Codex/Gemini quota snapshots were stale, so their old low percentages could not establish available headroom; Gemini also had a reserve-only builder rank.
- **Decision:** This D-057 policy applies only to Scheduler M2 builder recommendations for the approved DAG. Derive the minimum model/effort tier from task kind and validated complexity, scope, coupling and duration; a `risk: medium` label alone does not raise that floor. Make every project-authorized configured provider profile a normal candidate when its model meets the task floor and its runtime, authentication and fresh effective-account quota are valid, including OpenAI/Codex and Gemini/Antigravity. Use D-045's evidence-backed lexicographic route policy and current per-account quota; measured latency may affect ranking but cannot hard-exclude a provider. Produce deterministic account-specific recommendations for the full DAG without reserving capacity. M1 remains authoritative and revalidates the route before READY dispatch. Standalone and pinned legacy routing remain unchanged, as do D-004's audit independence and default auditor.
- **Alternatives:** Keep Gemini reserve-only (rejected for Scheduler M2: a capable profile with better verified headroom must be eligible); force equal account splitting or use a weighted quota/quality score (rejected: no comparable per-task consumption or common cross-provider scale).
- **Consequences:** Stale, failed or unknown quota continues to exclude a route with an explicit reason; fresh quota allows a capable provider/account to compete. The full route map is a recommendation only, and M1 may select another current route at dispatch. The due-only quota refresh mechanism is an implementation assumption in REQ-025's plan, not a model invocation.
- **Rollback:** Disable the M2-specific tier/rank and full-plan batch changes and retain the existing deterministic M2 route policy; preserve M1 state and M2 ledgers, with no migration or deletion.
- **Source:** Owner direction in session `01a1457f`; `requirements/REQ-025-m2-quota-aware-provider-and-account-rout/SPEC.md` and plan review. Brain note: `decisiones/20261016-m2-account-aware-route-policy.md`.

## D-058 — Persist allowlisted quota telemetry in M2 batch records
- **Date:** 2026-10-16 · **Status:** Accepted as the implementation ruling for REQ-025 R5/R6.
- **Supersedes:** Nothing; clarifies D-047's prohibition on storing raw route-policy evidence.
- **Context:** D-047 keeps task prose, raw route-policy evidence and provider output out of immutable batch rows. REQ-025 additionally requires durable proof of quota freshness and source failures for selected and excluded routes. Without that distinction, the route map cannot explain why cached percentages were rejected.
- **Decision:** Add a separate, versioned `BatchQuotaEvidence` telemetry record to batch algorithm v2 / batch record 1.3.0. Allow only task/route IDs, profile ID, opaque account reference, one finite state (`fresh`, `stale`, `missing`, `malformed`, `refresh_failed`, `exhausted`), finite `observed_at`, `valid_until`, `used_percent`, and a stable reason code. This is not `RoutePolicyEvidence`: do not persist raw policy objects, free text, credentials, tokens or provider output. Preserve state and old observation values explicitly when a refresh failed; never treat them as current eligibility. Keep the SQL table unchanged and the ledger append-only.
- **Alternatives:** Keep quota evidence ephemeral (rejected: cannot audit R5/R6 after mapping); persist raw quota/source payloads (rejected: unnecessary sensitive data and conflicts with D-047); mutate old rows or migrate table columns (rejected: breaks immutable-record compatibility without a need).
- **Consequences:** New readers accept legacy batch v1 / 1.2.0 records as records with empty quota evidence; v2 / 1.3.0 records are readable only by updated consumers. The old binary must not be given a v2 fingerprint; it can resume v1 writes using its prior fingerprint or a preserved ledger backup. New writes stay bounded by 128 tasks, 4,096 route/candidate edges, 2 MiB per plan and 10,000 rows.
- **Rollback:** Stop v2 writes and return to batch v1 fingerprints. Retain all rows; do not rewrite, downgrade or prune. An older binary reads only v1 records and must not be asked to replay a v2 hash.
- **Source:** REQ-025 R5/R6 audit correction, `bt_scheduler_decision/api-contract.json`, and batch-ledger compatibility tests. Brain note: `decisiones/20261016-m2-batch-quota-telemetry.md`.


## D-059 — Approve and bound the REQ-024 Planner V2 benchmark
- **Date:** 2026-10-16 · **Status:** Superseded by D-062 (Antigravity T15 smoke cap only; all other terms remain accepted).
- **Context:** REQ-024 improves Planner V2 traceability, contract validation, verification honesty, local runtime availability, and reproducible quality measurement without changing Pictures product behavior. The benchmark distinguishes controlled current-V2 versus improved-V2 runs from retrospective historical artifacts.
- **Decision:** Execute the approved six-milestone plan. Cap the matched benchmark at 30 runs plus one final Claude Opus 5.5 high REQ-017 reference run and 66 blind-review records. Use two independent reviewers under one hash-pinned rubric; pin their exact profiles/models in the frozen benchmark manifest before scoring. Cap launch-only smokes at one invocation per effective account, at most five under the current inventory; refresh that inventory before T15 and do not add newly configured accounts to the smoke set. Pictures q1–q5 and A6–A8 remain outside this approval.
- **Alternatives:** Leave the benchmark unbounded or compare provider quality across all runtimes (rejected: usage is finite and the owner deferred quality parity); treat historical V1 as a controlled arm (rejected: its prompt, permissions, repository SHA and runtime differ).
- **Consequences:** Implementation and offline verification may proceed under REQ-024. Provider calls are limited to the stated benchmark and smoke caps; report actual usage and incomplete cells without extrapolating a superiority claim.
- **Rollback:** Stop any unstarted benchmark calls and retain all completed records. A new plan/decision is required to increase caps, add providers/accounts or change the evaluator protocol. Existing plan and test artifacts remain immutable.
- **Source:** Owner approval in session `01a1457f`, REQ-024 PLAN.md r1 and RUN.md. Brain note: `decisiones/20261016-planner-v2-benchmark-approval.md`.

## D-060 — Adopt PLAN.json 1.2.0 after the coordinated consumer migration
- **Date:** 2026-10-16 · **Status:** Accepted under owner-approved D-059/REQ-024 r1 · **Supersedes:** D-053 (schema version and contract baseline only).
- **Context:** D-053 preserved schema 1.1.0 until a versioned migration was approved. D-059 authorized REQ-024, whose T10/T11 tasks add requirement coverage, interface declarations, explicit task kinds and verification categories, then update Planner/M1/M2/M6 with fail-closed capability checks. The migration is now implemented and the 1.2.0 compatibility suites pass.
- **Decision:** Use PLAN.json schema 1.2.0 for new Planner drafts. Keep 1.0.0/1.1.0 validation and frozen canonical bytes supported. Require Planner/M1/M2/M6 capability compatibility before a 1.2.0 plan is approved, handed off, launched, resumed or loaded. Keep the four planning aids exclusive to the Planner profile; the Planner still cannot select or rank a provider/service, account, model, effort, worker count or quota. Keep unsupported or incomparable planning history unknown.
- **Alternatives:** Keep new plans on 1.1.0 (rejected: it cannot machine-check REQ-024's traceability, kind, interface and verification-category requirements); replace the old contract in place (rejected: it would invalidate frozen hashes and legacy consumers).
- **Consequences:** New drafts use required `covers`, task `kind` and verification `category` under the versioned 1.2.0 gate; they may declare `interfaces` when cross-task contracts need validation. Existing 1.0.0/1.1.0 revisions remain readable and immutable. Unknown downstream capability fails closed.
- **Rollback:** Select an already approved compatible 1.1.0 revision and its matching consumers; never rewrite a frozen hash or feed a 1.2.0 plan to an older M1/M2/M6 reader. Follow the explicit down-conversion condition in `CONTRACT-1.2.0.md`; otherwise stop.
- **Source:** Owner-approved REQ-024 r1/D-059, T10/T11 implementation and compatibility evidence in `requirements/REQ-024-planner-v2-quality-and-benchmark/CONTRACT-1.2.0.md` and `RUN.md`. Brain note: `decisiones/20261016-planner-contract-1_2_0.md`.

## D-061 — Pin the configured profile and runtime in matched benchmark records
- **Date:** 2026-10-16 · **Status:** Accepted under the mission's internal-contract authorization.
- **Context:** REQ-024's frozen arms pinned the model, effort, tools and Planner configuration, but omitted the configured local profile and CLI runtime version. This left account/resource attribution and runtime reproducibility implicit. No frozen benchmark manifest or run cell existed yet.
- **Decision:** Version the benchmark manifest and cell metadata as 1.1.0. Require `profile_id`, `runtime_id` and `runtime_version` on both arms, require the same values across arms, and verify that every cell repeats the frozen values. Do not store credentials or absolute configuration paths.
- **Alternatives:** Leave account/runtime selection implicit (rejected: drift could go unnoticed); store configuration paths or authentication data (rejected: unnecessary sensitive data).
- **Consequences:** T17 can freeze only when the exact configured profile and runtime version are declared; cell metadata can reject profile/runtime drift. The approved call caps and reviewer decisions are unchanged.
- **Rollback:** Before any manifest is frozen, revert the schema/code change if the profile/runtime contract proves invalid. After freeze, introduce a new schema/manifest; never rewrite recorded cells.
- **Source:** REQ-024 `RUN.md`, “T16/T17 pre-freeze runtime and profile pinning”; 25 benchmark package tests, scoped Ruff, `py_compile` and `git diff --check` passed. Brain note: `decisiones/20261016-req024-benchmark-runtime-profile.md`.

## D-062 — Authorize necessary Antigravity T15 launch revalidation
- **Date:** 2026-10-16 · **Status:** Accepted by owner direction · **Supersedes:** D-059 (Antigravity T15 smoke cap only).
- **Context:** The first Antigravity T15 launch authenticated but failed before returning a response because the installed Planner exposed an unregistered tool. The tool mapping, wheel contents and model-selection validation were corrected locally. The owner authorized the necessary launch attempts and confirmed the configured accounts are authenticated.
- **Decision:** Permit launch-only calls for the existing `antigravity` profile using exactly `gemini-3.8-flash-low`, omitted effort, a 120-second timeout, and the fixed prompt `Responde únicamente con PLANNER_SMOKE_OK. No modifiques archivos.` Stop after a successful response whose stream reports the requested model. If an attempt fails, diagnose it and make another call only to validate a diagnosed issue or a concrete correction; do not repeat an unchanged failed setup. Do not refresh quota, change account/profile/model/effort, fall back, or store prompt/response text. This exception changes no benchmark call cap, other account's smoke count, reviewer rule, or Pictures scope.
- **Alternatives:** Retry blindly or substitute another profile/model (rejected: the call must validate the installed fix under the same explicit runtime); stop after the known local defect was corrected (rejected by the owner's authorization to continue as needed).
- **Consequences:** T15 may complete after the fixed launch returns the exact sentinel with a matching CLI-reported model; T17–T22 remain gated until the T15 acceptance criterion and P-109 reviewer selection are satisfied.
- **Rollback:** Stop further Antigravity T15 invocations and restore D-059's original smoke cap; preserve redacted attempt records.
- **Source:** Owner instruction in session `01a1457f`; REQ-024 `RUN.md`, T15 failure diagnosis and local correction. Brain note: `decisiones/20261016-req024-antigravity-launch-revalidation.md`.


## D-063 — Select Sol and Sonnet medium reviewers, with high for harder reviews
- **Date:** 2026-10-17 · **Status:** Accepted by explicit owner direction.
- **Decision:** The review pair is GPT-6.1 Sol (`gpt-6.1-sol`) at `medium` and Claude Sonnet 5.5 (`claude-sonnet-5-5`) at `medium`. Use their respective `high` variants when the review is more difficult. This is the owner's general reviewer model/effort policy, informed by the matched effort pilot; no quantitative difficulty threshold or automatic escalation algorithm was specified.
- **Evidence:** `artifacts/P109-effort-duel/REPORT.md`: both efforts found 31/31 roots; both Sol efforts found the same supported extra. High added consumption/time without additional coverage in those three synthetic cases. These observations do not establish universal effort equivalence.
- **Scope:** Documentation only, as requested. This records the selected models/efforts; it does not change runtime configuration, routing code, account defaults, an approved/frozen manifest or launch any review. Exact account profiles still need pinning for formal REQ-024 T17; the pilot's Codex-2/Claude Work accounts are not silently selected for that manifest.
- **Alternatives:** Always use high (not selected); retain Gemini/Haiku/Luna as the default review pair (not selected). Earlier unselected model-pair proposals are historical.
- **Consequences:** Model/effort selection under P-109 is resolved. Formal account/runtime pinning, the exact T17 isolation check, and any later implementation of this documented policy remain separate work.
- **Rollback:** A later explicit owner decision may supersede this selection; preserve the experiments and this decision.
- **Source:** Owner instruction in session `01a1457f`: both Sol and Sonnet medium review, their high variants for more difficult work; document only.


## D-064 · Planner default Astra high, fallback Opus xhigh (2026-10-17)

- **Status:** Accepted by the owner.
- **Decision:** Use GPT-6 Astra (`gpt-6-astra`) **high** as the default Planner and Claude Opus 5.5 (`claude-opus-5-5`) **xhigh** as its fallback. The owner's correction explicitly selects Astra high, not xhigh.
- **Evidence:** The native Planner pilot compared all candidates at high. Astra high was measured; Opus xhigh was not measured in that comparison.
- **Scope:** Model/effort policy documentation only. No runtime routing, configuration, formal benchmark manifest or account identity is changed. Exact account profiles and fallback activation conditions remain unspecified. Preserve D-054: a fallback requires an explicit caller/coordinator selection, never silent substitution within a pinned request. Keep the existing validation/correction gate.
- **Alternatives:** Astra xhigh was a transcription error, not the selected default. Sol high remains a measured alternative rather than the selected default.
- **Consequences:** Planner and reviewer model/effort policies are now selected (D-064 and D-063); runtime enforcement and formal account pinning are separate work.
- **Rollback:** Supersede with a later owner decision; retain the benchmark evidence.
- **Source:** Owner correction in session `01a1457f`: Astra high by default and Opus xhigh as fallback.


## D-065 — Select Luna high Explorer, with Sol/Sonnet medium for complicated exploration
- **Date:** 2026-10-17 · **Status:** Accepted by explicit owner direction.
- **Decision:** Default Explorer: GPT-6 Luna (`gpt-6-luna`) **high**. For complicated explorations: GPT-6.1 Sol (`gpt-6.1-sol`) **medium**; Claude Sonnet 5.5 (`claude-sonnet-5-5`) **medium** is an alternative to Sol medium. Haiku is not selected. No numerical complexity threshold, extra escalation condition or default account is introduced. Future comparisons involving Sol use `codex-2`, as explicitly requested; this is a comparison instruction, not a general production account selection.
- **Evidence:** `artifacts/explorer-ladder-20261017/matched-comparison.json`, `money-comparison.json`, `blind-judgements.json` and `operational-incidents.md`. Same hard tasks E4–E6: Luna 27 full + 1 partial criteria, Sol/Sonnet 28 full each, Haiku 25 full + 3 partial. One sample per cell; coordinator judgement with partly route-hidden grading. Content and strict format are separate: Luna/Sonnet each passed 2/3 strict contracts; Sol/Haiku 3/3. Tokens include cache/repeated input; API equivalents are not invoices or subscription-quota conversion.
- **Scope:** Policy documentation only. Source roles, installed agent files, routing ladders, account defaults and frozen manifests are not changed. Inspection found source Explorer `model: haiku` / `codex_effort: low`; the checked Claude/Codex-Luis installations retain those choices, with no explicit Codex role model. The installer does not emit a Codex model. This does not establish automatic enforcement of D-063/D-064 or this selection.
- **Alternatives:** Haiku medium was measured but not selected; model selection does not require declaring a universal benchmark winner.
- **Consequences:** Explorer selection is resolved independently of P-110's experimental closure. P-110 remains open: 23/24 measured cells returned, Gemini stopped after E5 strict-format failure and E6 was never launched; nine operational attempts remain excluded and repaired-Gemini per-cell quota remains unknown. No completed cell is repeated.
- **Rollback:** Supersede with a later owner decision; preserve all evidence. No runtime rollback is needed for this documentation-only change.
- **Source:** Owner's continuation instructions in `/home/david/Downloads/seguimiento-modelos-metodologia.txt`.


## D-066 — Harness quota optimisation: ladder without automatic xhigh, bounded exploration, tier-homogeneous sessions
- **Owner amendment (2026-10-17, session 411b81ed):** Active subscription refresh before pool routing, at most once every 900s/account under the existing lock/challenge/Retry-After rules; retain last effective sampling status during I/O. Claude/Codex model/window pressure >=85% is a fallback priority before quality ranking within independence/provider-role rules; 100% remains exclusion. Replace former uncapped kind floors with hard docs=0, test/research=1 ceilings for selection, pins, effort and retry/manual escalation. Group limits are hard 3/1/1 maxima (configuration may lower only). New sessions default to 25min at every tier with no task-count multiplier; explicit stored timeouts remain. Claude argv uses hidden supported --max-turns45. A pending own-milestone independent audit replaces all individual-commit Antagonist passes, including high-risk work; its inherited risk budget remains. This amendment supersedes conflicting earlier D-066 statements below.
- **Runtime alignment (2026-10-17, session 74ac99a7):** Unknown/stale quota remains neutral at 50%; explicit authentication/challenge sampling failures rank behind healthy accounts, including accounts with the +20 weekly burn penalty. Replay audit tiers inherit milestone risk/architecture and use the real audit ladder rung; task routing calls model_for with kind. Antagonist review cost is separate (one assumed commit per builder task): fixture 180→12 relative units, not measured consumption. Source/docs use conditional review with Sonnet/medium default and Opus/high for risk/architecture or escalation. Verified by 120 harness and 55 routing tests.
- **Date:** 2026-10-17 · **Status:** Accepted by the owner's master prompt (`PROMPT_MAESTRO_OPTIMIZACION_HARNESS.md`), executed directly in session `2d72194c`; exploration budget set by the owner to 5 attempts/week for costly routes, raisable.
- **Decision:** Ladder Claude haiku / sonnet medium / opus high, Codex luna medium / sol medium / sol high; xhigh only through an explicit per-task `effort:`. Start tier from kind, complexity, risk and level (floor, not ceiling). Cold-start exploration only on non-audit, non-high-risk work, cheap models freely and costly ones within `routing.explore_budget_week`. Quota headroom in 10-point buckets, unknown = 50 %, weekly-pace penalty, quality by the Wilson lower bound of verified success. Limit recovery re-asks the router for the limited session's tier and kind. Milestone sessions group only same tier/kind/risk tasks (3/1/1 per tier, configurable). Per-tier session timeouts for new runs. Stagnation block after two consecutive failed attempts with an identical working tree. With a pending milestone audit the per-commit Antagonist pass is dropped, except for high-risk or architecture work (one source: `bt_review_policy`).
- **Evidence:** `artifacts/harness-optimization-2026-10-17/replay.json` (deterministic replay, relative estimates only) and `tests/test_harness_optimization.py`.
- **Contradictions found in the prompt:** Claude Code 2.1.302 has no `--max-turns` (only API-only `--max-budget-usd`), so no turn limit was added; the timeout and the stagnation rule bound sessions instead. The prompt's Tier 0 Luna "low/medium" keeps medium (docs: low) because low was never measured for implementation.
- **Alternatives:** A hard per-kind tier ceiling (rejected: blocks legitimately hard docs/research); raw success rate for ranking (rejected: 5/5 reads as proven); a second decision engine (rejected: the M2 adapter already reads `bt_agents`).
- **Consequences:** More, lighter sessions per milestone (replay: 10 builder sessions vs 3) at lower estimated weight; session start cost is NOT modelled, so the net effect is unproven until measured on real runs (P-113). Runs already in flight keep their stored `session_timeout_min`; their grouping changes on the next resume.
- **Rollback:** Revert the commit; config keys `routing.group_max`, `routing.min_samples`, `routing.explore_budget_week`, `routing.effort_weight` only tune it.
- **Source:** Owner request in session `2d72194c`.


## D-067 — Select Sonnet medium Implementer, with Luna high as fallback
- **Date:** 2026-10-17 · **Status:** Accepted by explicit owner direction.
- **Decision:** Default Implementer: Claude Sonnet 5.5 (`claude-sonnet-5-5`) **medium**. Alternative/fallback: GPT-6 Luna (`gpt-6-luna`) **high**. This is the owner's role selection following the completed Implementer pilot; do not substitute Luna medium.
- **Evidence:** `artifacts/implementer-pilot-20261017/REPORT.md`, `comparison.json` and `closeout-audit.json`. Sonnet medium and Luna high both pass6/6 original and supplemental cases. Sonnet:124.608s /175,569 recorded tokens; Luna high:204.846s /882,938. Single sample/cell, synthetic Python/SQLite tasks; tokens are not invoices or equivalent quota. Codex effective model identity and every configuration's effective effort remain unattested.
- **Scope:** Record the selected role policy consistently with D-063/D-064/D-065. Runtime router enforcement, generated installed roles and exact production account profiles remain separate rollout work. Existing Implementer source already declares Claude sonnet, but does not enforce a cross-provider Luna high fallback. This decision does not change D-066's global tier ladder, quotas, independence rules or kind ceilings.
- **Fallback:** Luna high is the selected alternative. No new automatic quality-failure trigger or account-pressure threshold is inferred; retain existing operational guards and explicit caller/coordinator selection for a pinned request, without silent substitution.
- **Alternatives:** Retain Luna medium (not selected; independent I6 lifecycle defect), Luna xhigh or Haiku variants (measured but not selected), Sol medium (measured, not the chosen fallback).
- **Consequences:** Planner, Reviewer, Explorer and Implementer selections are recorded. Researcher and Runner still need owner-specific final selections; Antagonist already has Sonnet medium / Opus high under D-066. A coordinated runtime rollout remains pending for documented selections.
- **Rollback:** Supersede with another explicit owner decision; preserve all48 native results and supplemental evidence.
- **Source:** Owner instruction after pilot closeout: select Sonnet medium as Implementer and Luna high as fallback/alternative.


## D-068 — Select Luna high as the default Researcher
- **Date:** 2026-10-17 · **Status:** Accepted by the owner (“perfecto” after the Luna-high recommendation).
- **Decision:** Default Researcher: GPT-6 Luna (`gpt-6-luna`) **high**. No fallback model, escalation threshold or production account is selected by this acceptance.
- **Evidence:** Completed18-call pilot in `artifacts/researcher-pilot-20261017/REPORT.md`, comparison.json and closeout-audit.json. Luna high:6/6 content/source cases,36/36 criteria full and supported after the explicitly separate published-source adjudication,137.044s and597,123 recorded tokens. Sol medium:6/6,213.775s/625,696tokens; Sonnet medium:5/6 strict cases,162.380s/218,177tokens. Single sample/case; mixed Codex accounts and native search tools limit generalization. Codex effective identity and all effective efforts remain unattested.
- **Cost interpretation:** Official API rates support Luna's lower token price, not an equivalent subscription-quota conversion or an invoice for the native pilot. Tokens/cache distributions and tool charges matter; no actual subscription cost was measured.
- **Scope:** Selected role policy, consistent with D-063/D-064/D-065/D-067. Coordinated router enforcement, installed-role model/effort pins and default account selection remain separate rollout work. No global configuration, runtime ladder or installed role changed here. Preserve explicit pins and existing quota/independence safeguards; no silent substitution.
- **Alternatives:** Sonnet medium and Sol medium were measured but are not selected as default or automatically designated fallback. Runner remains the only helper role lacking the owner's final model selection; Antagonist already has D-066 policy.
- **Rollback:** Supersede with a later owner decision; preserve native results and both original/supplemental grades.
- **Source:** Owner accepted the recommendation of Luna high as the main Researcher after the full pilot and current official API-rate check.


## D-069 — Select Luna high and Sonnet low for Runner
- **Date:** 2026-10-18 · **Status:** Accepted by the owner.
- **Decision:** Default Runner: GPT-6 Luna (`gpt-6-luna`) **high**. Alternative/fallback: Claude Sonnet 5.5 (`claude-sonnet-5-5`) **low**, interpreting the stated order as primary then alternative.
- **Evidence:** Owner instruction: “hagamos que sea luna high y sonnet low”. Partial pilot REPORT.md records15/24 native calls, Luna high6/6 content and5/6 strict. Sonnet low was not tested; Sonnet medium results do not attest low.
- **Scope:** Document the selected role policy consistently with D-063–D-068. Coordinated runtime/router and installed-role rollout remains pending; no production account or automatic fallback trigger inferred. Preserve explicit pins and existing quota/independence safeguards.
- **Pilot:** P-116 remains experimental closeout work, independent of model selection. Do not relaunch any started cell, substitute low into the frozen medium protocol, or infer authorization for new native calls.
- **Rollback:** Supersede with a later owner decision; retain all original pilot evidence.


## D-070 — Activate role policies with provider-family quota priority
- **Date:** 2026-10-18 · **Status:** Accepted by explicit owner instruction; implementation and installation authorized.
- **Decision:** Automatic role routes use only the previously selected models/efforts. Prefer the eligible Claude/Codex family with more quota headroom; any eligible account within that family may be chosen. No fixed production accounts. Existing project/work gates, quota exhaustion/cooldown, explicit caller pins and review independence remain.
- **Quota interpretation:** Compare fresh model-relevant subscription bottlenecks in existing10-point pressure buckets; unknown/stale remains neutral50%. Family headroom is that of its best eligible account (aliases deduplicated); accounts at85% or above are fallback priority and100% excludes. Existing weekly pace penalties remain.
- **Alternative triggers:** Quota pressure/availability or an explicit high-complexity label (`complexity: L`, with API aliases `high`/`high_complexity`). Failures, risk, architecture and elapsed time alone do not substitute unselected models or increase role efforts. Reviewers use their approved high variants; Explorer uses Sol medium/Sonnet medium when explicitly complex. No automatic quality exploration for role routes.
- **Researcher fallback:** Sonnet5.5 low is selected as the alternative to Luna high, matching Runner. High complexity prefers the designated alternative among healthy eligible routes; quota protection can still force another approved route.
- **Scope:** Apply to automatic delegate, standard marathon, Scheduler route sources and Planner selection; install provider-native role defaults. Explicit provider/account/model calls remain pinned; native subagents cannot rotate provider families themselves and automatic cross-family routing uses the methodology router. Preserve the separate restricted orchestration reasoning boundary and documentation-only budget.
- **Evidence/acceptance:** Verify reverse quota imbalance, account dedup/work gating/cooldowns, explicit-complexity transitions, unchanged models after failures, pin preservation, Scheduler baseline, native generated models/efforts and installed CLI/package imports. No new pilot call required; P-116 remains independent.


## D-071 — Waive remaining Explorer and Runner experiments
- **Date:** 2026-10-18 · **Status:** Accepted by explicit owner instruction.
- **Decision:** Owner says “para explorer y runner ignoremos las pruebas”. Cancel remaining experimental execution and closeout for Explorer P-110 and Runner P-116, including grading and final reports. Do not resume without a new explicit request.
- **Consequences:** Close backlog items as waived/cancelled, never as experimentally passed. Preserve all existing evidence and partial results; D-065/D-069 selections and D-070 runtime stay in force. No new model calls or runtime changes.
- **Rollback:** A new owner instruction may authorize a separately scoped continuation that preserves prior evidence.


## D-072 — Separate Implementer availability fallback from complexity
- **Date:** 2026-10-18 · **Status:** Accepted by explicit owner instruction to fix assignments.
- **Supersedes:** Only D-070’s explicit-complexity preference inversion for Implementer; all other role choices, pins, work gates and quota rules remain.
- **Context:** Real-plan simulation put medium implementation on Sonnet medium and high implementation on Luna high solely because the fallback list was reversed. No evidence established the alternative as a capability upgrade.
- **Decision:** Implementer options stay Sonnet medium then Luna high for every complexity label. Select the eligible provider family through the existing quota/headroom rules; tied pressure uses the normal preference. Complexity must neither reverse the list nor override quota with an Implementer option-priority key. No new stronger model/effort is inferred.
- **Alternatives:** Retaining the inversion would preserve unsupported capability assumptions; inventing a new high-complexity model/effort would exceed the owner’s selected policy. Both rejected.
- **Consequences/verification:** Two pre-fix regression tests fail10 subcases;115 targeted tests, Ruff, offline wheel build and installed-module checks pass after the bounded policy/router correction. Ten-scenario matrix (20 runs/80 simulated tasks) and real REQ-018 (2 runs/12 tasks) pass. At Claude20%/Codex60% used, T1–T5 Sonnet medium; T6 Sonnet low. Reverse quota/exhaustion still permits Luna.
- **Rollback:** Supersede with another explicit owner decision and restore the two policy/ranking clauses plus corresponding behavioral expectations; preserve existing simulation evidence. No schema or data migration.


## D-073 — Planner responsibility and calibration review
- **Date:** 2026-10-18 · **Status:** Implemented under explicit owner request to fix Planner and regenerate the Pictures plan.
- **Context:** Pictures REQ-018 v1 T6 mixed test registration/code work, command execution and feature acceptance but kind:test routes to a non-editing Runner. T3 streaming/final sanitation and T5 persisted/restored UI plus unbuilt harness work needed stronger reasoning than their original medium justifications. Structural checks did not establish realistic classifications.
- **Decision:** Add responsibility-to-kind and evidence-based calibration checks to Planner's WBS/adversarial resources, with one role pointer. Existing runtime semantics remain: implement authors/changes code/tests/configuration; standalone test tasks execute/report established checks; audit interprets integration/product evidence; research addresses unresolved feasibility. Preserve local verification with producers and split mixed standalone responsibilities. Justify complexity against inspected paths and adjacent level, account for missing harness work, retain unknown history and provisional estimates.
- **Alternatives:** Raising every task to high would not fix responsibility boundaries or provide evidence. Treating structural validation or successful scheduler simulation as realism/model-quality proof was rejected. No heuristic schema gate or provider/model assignment was added.
- **Evidence:** Updated native generation on codex-luis / Sol high yields three milestones/eight tasks with original six requirements. Old T6 becomes registration implementation(low), command execution(test/low), acceptance review(audit/high); T3/T5 high with concrete state/stream evidence, T1 remains medium. Canonical check/report exit0 with9 explicit warnings; independent spec/standards reviews APPROVE. Runtime14 tests/offline resource build pass; one pre-existing profile test failure tracked P-119.
- **Limits:** This validates a regenerated case, not perfect general difficulty estimation. New draft remains unapproved/unfrozen; no implementation or simulation performed. Child hooks disabled only for this generation to prevent known P-118 Git automation; global configuration unchanged.
- **Rollback:** Supersede this decision and restore the three instruction resources, regenerate native Planner definitions, and retain both draft archives/verification evidence. No contract/schema/data migration.


## D-074 — Opt-in patch handoff for no-commit M3 execution
- **Date:** 2026-10-18 · **Status:** Implemented and independently reviewed for the owner-authorized isolated M1/M2/M3 smoke.
- **Context:** M3's default snapshot handoff creates a Git commit object, conflicting with the owner's no-commit scope. A native execution must still preserve recoverable changes.
- **Decision:** Add explicit `Config(handoff_mode="patch")`. Keep snapshot as the default and preserve positional Config compatibility. Patch capture uses an isolated index and capped binary diff against the pinned base; no new commit or snapshot ref. Patch manifests use schema2, snapshot manifests retain schema1. Failed capture must not advertise stale evidence or destroy a previous patch.
- **Consumers/compatibility:** M3 settle and prompt receive the selected mode; patch prompts prohibit commits. Snapshot-dependent predecessor integration cannot consume a patch automatically; isolated wiring explicitly disables that integration and the caller reapplies/verifies the patch. Existing callers keep default snapshot semantics.
- **Alternatives:** Disabling preservation loses work; creating hidden commit objects violates scope; replacing default snapshot would break existing integration. All rejected.
- **Consequences:** This mode provides recoverable artifacts, not automatic patch integration. Global automatic VCS defect P-118 remains separate. Actual no-commit enforcement in the smoke additionally disables child hooks and guards Git mutations.
- **Rollback:** Return callers to default snapshot only where commits are authorized, or stop their runs; preserve existing schema2 artifacts for manual restoration. Revert the opt-in config/capture/prompt changes together; no database migration.

<!-- D-074 verification: actual T1 accepted; native10/independent7 original+replay pass; final capture identical; final handoff23/README6 and adapter21 pass. Wider287-pass suite began before final correction. Build blocked by absent pip/setuptools;7 Ruff findings pre-existing, introduced import order fixed. -->

## D-075 — Verified patch-chain transfer and generation-bound retry references for the live product run

- **Date:** 2026-10-18.
- **Context:** Owner authorized full isolated Pictures REQ-018 M1/M2/M3 execution without Git commits or snapshot refs. D-074 patch mode preserved work but had no automatic predecessor integration. A real rejected T1 retry then exposed M2 reuse of a single-use M3 route.
- **Decision:** Keep snapshot defaults unchanged. Add explicit caller-owned PatchChainWorkspaces for this serialized common-base chain: trusted candidate origin provenance plus independently accepted prerequisites, manifest/patch digests, pinned base and exact target tree. Empty no-checkout materialization uses cached isolated indexes and checkout-index, avoiding deletion of already-absent baseline paths. Caller rejects forks and new source deletions; helper grants no acceptance.
- **Retry cause:** Add optional validated dispatch_generation=0 to M2 request, populated from persisted M1 TaskView.attempts. Nonzero generations bind decision and batch identity; zero preserves historical initial identities. No fake quota/time/policy changes; M3 single-use remains enforced.
- **Verification:**10 patch-chain unit tests, real three-workspace replay, actual dirty Pictures baseline and digest/missing/lineage negatives; independent review APPROVE.81 retry/decision/contract tests and Ruff pass; coordinator independently reran3 real M2/M3 ledger tests; independent retry review APPROVE. Actual T2 input tree equals freshly accepted T1 tree.
- **Operational correction:** Native diagnostic cleanup violated no-deletion instruction; preserve incident, reconstruct copies from originals, install process-local deletion-command guards in addition to Git guard. These are command wrappers, not a filesystem sandbox. Child hooks disabled only in necessary native processes; no global config change. Successful Next type checks require next typegen, confirmed independently. External verification waits terminal settlement to avoid M3 cwd-sweep overlap; first lint -9 is preserved and final post-terminal lint0 verified.
- **Limits:** No generic patch DAG merge/restart/fault-matrix claim; M4/M5/M6 and global P-118 remain separate. No full product completion, canonical integration or deployment.
- **Evidence:** ../pictures/artifacts/REQ-018-full-isolated-20261018/REPORT.md and linked artifacts.

## D-076 — Live Scheduler observability, evolving plans and a flow map (SUPERRR)

- **Date:** 2026-10-19 · **Status:** Implemented and independently reviewed (Codex luna ×2); uncommitted.
- **DD1** per-attempt record is a read model outside M1 (`bt_attempt_facts`: M1 state + M2 ledger + M4 usage): M1 stays free of model names. **DD2** live view = a bus that tails each module's own durable store with cursors (`bt_flow_bus`), read-only, no change to the modules or the owner. **DD3** classification changes (complexity, scope, risk, coupling, confidence, estimate) are append-only amendments needing no reapproval; scope changes still need revision N+1. **DD4** a run continues on N+1 through M1 `rebase_run`: accepted tasks with an unchanged fingerprint and kept prerequisites survive, everything else restarts with a fresh budget. **DD5** an agent may only raise a level, with evidence; lowering is the owner's. **DD6** the map is a fixed SVG with particles per real message. **DD7** ids are links: `/go/<ID>`, markdown links, OSC 8 in the CLI, kitty hints for plain text.
- **Also decided:** Scheduler attempts reach `/metrics` as rows derived on read (not a second writer next to the marathon's `bt_events`); tokens are shown as reported and a total is never computed; Shoelace and fonts are vendored (no runtime CDN).
- **Limits:** `--proposed-by owner` is not authenticated; M2 does not cite the amendment in its own record; desktop alerts are not wired into the runtime; the real-provider bounded run (T8.3) is the owner's.
- **Rollback:** the new modules are additive; remove the routes in `bt_server.py` and the overlay assignment in `bt_scheduler_run._wire`; `PLAN.amendments.jsonl` files are inert without the overlay.

## D-077 — Audits are accepted by their findings ledger and the Scheduler reopens the work

- **Date:** 2026-10-19 · **Status:** Accepted
- **Context:** REQ-027 finished with all 31 tasks green while its own audit (T18) said «PARTIAL, release blocked» with six open critical/high findings. T18 and T19 verified with `test -s file`; every other task verified its module in isolation; T17 («offline end-to-end») passed although the gateway entry point exits 0 and POSTs never reached the ledger.
- **Decision:** (1) `kind: audit` tasks declare one `*.findings.json` ledger (`audit-findings/1`); `bt_audit_gate` + `bt_scheduler_quality_adapter` turn an M6 PASS into a rejecting verdict while a critical/high finding is open, the ledger is missing/malformed, or a risk is «accepted» by anyone but the owner. (2) The same verdict calls the new M1 API `reject_and_rework`: in one transaction the audit attempt is rejected and the tasks named by the findings, everything downstream of them and the audit go back to `pending` with a fresh budget (`completed → pending` is now legal, only through `rework`); the reworked tasks read the findings in their prompt (`RUN.notes/<task>.audit.md`). Bounded by `Config.max_reworks` (2), live attempts and cancelled runs; refusal degrades to the normal recovery/blocked path. (3) `plan-json check` (schema 1.2.0) errors when an audit has no ledger or follows no `kind: test` task with an `integration` command verification.
- **Alternatives:** make M6 itself read the ledger — rejected: M6 imports no methodology module; a planner-only rule — rejected: it cannot see findings; reopening by revision/rebase — rejected: fingerprints ignore the audit outcome, so nothing would reset; having an agent or the operator reopen by hand — rejected by the owner («no tú, el sistema»).
- **Consequences:** + an audit can no longer be a green rubber stamp; the system loops fix → re-audit without a human. − a plan approved before this change whose audit declares no ledger now fails closed at runtime (replan it); the "integration" rule is structural, it cannot prove the test really starts the entry points (the audit is the net); a refused rework still burns auditor retries before blocking (proposal: block at once).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-027

## D-078 — Agents ship to production and run unrestricted by default

- **Date:** 2026-10-19 · **Status:** Accepted (owner's explicit instruction)
- **Context:** `gh` (dav033), `vercel`, `netlify` and SSH keys for `advin` and `marketplace` are available; the owner wants agents to use them freely and to run without permission prompts everywhere.
- **Decision:** Claude: `permissions.defaultMode = "bypassPermissions"` in `~/.claude` and `~/.claude-work` (scheduler sessions already use `--dangerously-skip-permissions`). Codex: `approval_policy = "never"` + `sandbox_mode = "danger-full-access"` in `~/.codex`, `~/.codex-luis`, `~/.codex-2` (scheduler already uses `--yolo`). Tools documented in `~/bitacora/TOOLS.md`; `references/tools.md` autonomy line rewritten; the «never git push / merge to main» lines in `~/.claude/CLAUDE.md`, `~/dev/cerebro/GLOBAL.md` and `~/.codex/AGENTS.md` now authorize push, merge and deploy. Kept: backup/rollback note before risky server changes, tests before pushing, verifying the deploy, no deleting the user's files or rebasing shared branches unasked.
- **Alternatives:** keep prompts for production actions — rejected by the owner (see D-001).
- **Consequences:** + no stalls on approvals; agents can deploy. − a mistaken push to `main` deploys automatically (several repos) and nothing but instructions prevents destructive commands. Backups of every edited config: `*.bak-20261019-*`.
- **Source:** [day log](2026-10/W4/2026-10-19.md)

## D-079 — Gate policy is configuration, refused rework never burns retries, old plans have a migration path

- **Date:** 2026-10-19 · **Status:** Accepted · **Refines:** D-077
- **Context:** D-077 shipped with hard-coded severities, a fail-closed rule that broke any pre-gate plan, a refused rework that still burned auditor retries, and REQ-027 left green with its own audit's findings unrecorded.
- **Decision:** (1) `bitacora.py config` section `gates`: `audit_blocking` (default critical+high), `max_reworks` (2, feeds the M1 `Config`), `audit_ledger_required` (true; false lets a ledger-less audit through and records `audit_gate_skipped`). (2) M1 `reject_and_rework` now distinguishes why a rework cannot start: a live attempt in scope DEFERS the verdict (status `deferred`, nothing applied, M6 redelivers); `max_reworks` reached applies it and BLOCKS the audit at once (`rework_limit`, decision card); a cancelling run only applies it. (3) Owner moves: `scheduler-op REQ rework T1,T2` (no limit, refused while a live attempt is in scope) and `plan-json retrofit-audit REQ` (adds the ledger path to every audit task, PLAN.json as a new working revision + PLAN.md line). (4) The auditor's prompt names the exact declared ledger path. (5) REQ-027 was brought in line with exactly these tools: retrofit → r4 frozen → `revise` (31 kept) → `rework T18` (T18+T19 back; the audit re-runs under the gate and the system reopens whatever its ledger names).
- **Alternatives:** keep the planner suffix configurable — rejected: the suffix is part of the plan schema, shared by planner and gate (a test pins them equal); per-REQ hard-coded fix — rejected by the owner.
- **Consequences:** + no hand reopening anywhere; legacy plans migrate in three commands. − the audit rerun costs a full audit plus whatever rework it triggers (quota); a ledger is only as honest as the auditor (the owner alone can accept a risk).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-027

## D-080 — Planner at high effort on gpt-6.1-sol, second auditor, planner guidance from the field

- **Date:** 2026-10-19 · **Status:** Accepted (owner's instruction) · **Refines:** D-077, D-079
- **Context:** the owner asked for `6.1 high`, `xhigh → high`, a better-optimised planner (researched on the web) and a cheap second auditor.
- **Decision:** (1) `bt_role_policy` planner = Codex `gpt-6.1-sol` high, Claude `opus` high (was `gpt-6-astra` high / `opus` xhigh; astra stays in the catalog as an explicit pin); `planner.md` no longer carries model/effort pins — the policy is the single source and a test pins the installed agents to it (this also resolves the old `planner_profile` failure). (2) Planner guidance, from the Anthropic agent docs and the superpowers `writing-plans` skill plus our own incident: verify behavior never existence (`test -s` only for docs), integration test over the real entry points before any audit, audit ledger, file map first, no placeholders, a *Review focus* of the five likeliest uncovered input classes, plan-size proportion, and stop conditions (two exploration passes). The adversarial-review skill hunts the "green-but-hollow" plan. (3) `gates.second_auditor` (default on): a plan with an audit needs an independent cross-check audit; `plan-json retrofit-audit --cross-check` adds it; the planner module only warns, the adapter enforces from configuration. Each audit has its own ledger, so the union decides.
- **Alternatives:** call a cheap model inside the verdict path — rejected: it would block verdict delivery for minutes and hide the second opinion from `/flow`; pin the cross-check to a provider in the plan — rejected: the planner never chooses routes (M2 does; route pins are not wired yet, F11).
- **Consequences:** + two independent ledgers, visible and retried like any task. − "cheap" depends on M2's routing and on classifying the cross-check honestly; plans approved before today need `--cross-check` (or the policy off) to launch/freeze a new revision.
- **Sources:** Claude Code subagent docs (code.claude.com/docs/en/sub-agents), Anthropic "Building effective agents", obra/superpowers `writing-plans`, Codex effort guidance (high for planning, xhigh only for high-stakes).

## D-081 — Role policy stays the router; escalated audits read at high; the learning router keeps its own tests

- **Date:** 2026-10-19 · **Status:** Accepted (owner: "si" to the recommendation) · **Refines:** D-070, D-080
- **Context:** 12 inherited tests assumed the older risk/exploration router while `bt_role_policy` ("risk does not change the options") routes every kind with an owner role.
- **Decision:** the role policy remains the router. One exception: an audit the run escalated (tier 2: high risk or architecture level) is read by the strongest reviewer of each provider at high (`gpt-6.1-sol` high, `opus` high) — `bt_role_policy.escalated_audit`, applied in `bt_agents.route`, `bt_role_routing.candidates` and `bt_delegate`, and NOT when the caller pinned a role explicitly. The exploration/effort-evidence tests now exercise the learning router with the role lookup switched off (`LearningRouter`), since that router still exists for kinds without a role.
- **Not decided here:** two M2 semantics still disagree with their tests — the full-DAG batch ranks by baseline/deterministic order instead of quota pressure, and the offline benchmark expects contextual == deterministic (P-129 narrowed to these 3 tests).
- **Source:** [day log](2026-10/W4/2026-10-19.md)

## D-082 — REQ-027 gets milestone M6: the Scheduler creates and verifies the production environment

- **Date:** 2026-10-19 · **Status:** Accepted (owner: "hay que asignar una tarea que suba todo a producción… y no solo subir sino crear el entorno de producción") · **Refines:** D-078
- **Context:** the plan kept go-live outside the Scheduler («Go-live with the owner») and forbade tasks to deploy or ssh to AdvIn. AdvIn also serves ~12 other production sites behind one Caddy, has no service user, no `uv`, no firewall, and the M6 verifier runs without network.
- **Decision:** requirement R19 and milestone M6 (T20 provision AdvIn: user, dirs, hardened units, Caddy block with snapshot/backup/validate/reload and auto-rollback if any other host changes, receipt verifier; T21 Vercel project + production deploy; T22 OAuth App + Telegram/keys placement from `~/.config/flow/secrets.env`; T23 hash-locked release, listeners only on 172.20.0.1, laptop tunnel retargeted to remote-only, rehearsed rollback; T24 live smoke + one manual phone confirmation). Evidence is a per-task receipt validated offline by `verify_receipt.py`. The revision is applied by `artifacts/REQ-027-production-milestone/apply_when_idle.sh` only after the audits pass and the run is idle (a `revise` would cancel live attempts); it stops if the run needs the owner.
- **Alternatives:** apply now — rejected: cancels the audits in verification; one big deploy task — rejected: one failure would hide which layer broke and the Caddy is shared.
- **Consequences:** + provisioning, release and rollback are reproducible and audited by receipts. − the receipt is self-reported (the verifier cannot reach the network), so T24's live smoke and the owner's phone check are the independent proof; T22 stops until the owner supplies the Telegram token (`~/.config/flow/secrets.env`, template created, mode 600, no values).
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-027

## D-083 — Rework fixes found on the live REQ-027 run: paired audits and continuation after rework

- **Date:** 2026-10-19 · **Status:** Accepted · **Refines:** D-077, D-079
- **Context:** the first live use of the rework mechanism exposed two defects of mine. (1) T18 and T18b both rejected; each verdict deferred because the other audit still had a live attempt in its rework scope, so both waited for each other (12 retries, 20 minutes). (2) After a second rework, the reset tasks could not start: the retry-continuation code only accepted a previous attempt that had failed or been rejected, and refused one that had been accepted («PREDECESSOR_HANDOFF_MISSING: retry is not authorised»), blocking T5, T10 and T15.
- **Decision:** (1) a live attempt that is only VERIFYING does not count as busy: the rework supersedes it (`superseded_by_rework`, its verdict becomes stale); only attempts still building defer. (2) `bt_scheduler_retry` continues from an accepted or superseded predecessor snapshot with a prompt note that an audit sent the work back (the audit's findings come first in the prompt). Tests reproduce both; the owner process was restarted with the fixes and the three tasks reopened (not real failures).
- **Consequences:** + two reject-at-once audits resolve (the first verdict wins, the other audit reruns after the rework). − the superseded audit's findings of that round are discarded; it audits again after the redo, so a real issue resurfaces.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-027

## D-084 — A reworked task continues from its own snapshot only on the base it was built on; the three inherited M2 tests follow the real contract

- **Date:** 2026-10-19 · **Status:** Accepted · **Refines:** D-083
- **Context:** after the continuation fix of D-083, T12 and T6 hit `INTEGRATION_CONFLICT`: the reworked tasks T5a, T5b, T11 and T11a continued from their OWN old snapshots (the old base) while the tasks upstream of them had been redone, so the predecessor merge could not reconcile. Separately, three tests had failed since before this session (REQ-017 frozen-DAG routing and two decision-benchmark tests); they assumed M2 reorders routes by quota pressure, but an earlier commit today made the full-DAG batch keep the router's order for every task except documentation (the router is already quota- and role-aware, D-081).
- **Decision:** (1) `bt_scheduler_retry` continues a sent-back task from its previous snapshot only when that snapshot's base equals the integrator's current base; otherwise it starts on the new base and the prompt points at the old snapshot (`git show <sha>`). (2) The three tests now assert the current contract (baseline order kept for non-docs; quota pressure steers docs; the benchmark models the production default). No production routing code changed. (3) `test_attempt_detail` no longer leaves `bt_notify` functions replaced for the rest of the suite.
- **Consequences:** + T6 and T12 completed by themselves on the live run; the full suite is green. − T5a, T5b, T11 and T11a keep results built on an older base; the T18 audit verifies the whole once more. Closes P-129.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-027

## D-085 — Telemetry that teaches: Codex in `--json`, a quiet monitor, and Scheduler attempts in the attempt log

- **Date:** 2026-10-19 · **Status:** Accepted · **Refines:** D-077
- **Context:** the owner asked for telemetry without noise that nourishes decisions. Measured on REQ-027: 928 of 929 M4 incidents were `info` stream gaps (96 attempts), 524 of them Claude `user` tool results the normalizer did not know, 229 plain-text lines from Codex (it ran without `--json`, so M4 saw no tool activity or token split for the provider that runs most tasks), 190 stderr buffer overflows; the attempt log had no row since 2026-10-16, so `metrics`, `--advice` and the learning router saw none of the Scheduler's 100+ attempts.
- **Decision:** (1) The executor launches Codex with `--json` (`agent_argv(..., structured=True)`); `bt_runsettle` and the Codex driver read that stream (final message, failure, limit with its reset, end-of-turn event, split usage) and still read text mode. (2) M4: Claude `user`/`rate_limit_event` are ignored as non-activity (an unknown type stays a gap); stderr `source_gap` is not an incident; gaps of one attempt, stream and cause collapse into one incident with a count. (3) `bt_attempt_log` projects every judged Scheduler attempt into the attempt log at each owner heartbeat: rejected → `verify_failed`; accepted and named by an audit-gate finding → `verify_failed/audit_rejected`; accepted and audited clean → `verified`; accepted with an audit pending → not written yet; redone without a finding, infrastructure and cancellations → `stopped` (unjudged). (4) The "Try again at" reset regex ignores case. (5) A finding that sends back more than `gates.attribute_max_tasks` (3) tasks at once is recorded as `stopped/systemic_audit_finding`, not charged to each builder: the first retrofitted REQ-027 audit named 12 and 22 tasks and would otherwise have shown gpt-6-luna at 9% success. (6) A Claude attempt that used all its turns (`error_max_turns`) is `incomplete_output`, which recovery retries from the snapshot, instead of an unnamed `agent_error` that blocked T15e after three tries; the cap is `scheduler.max_turns` (120; the legacy marathon keeps 45).
- **Consequences:** + the router and `metrics --advice` learn from Scheduler runs, and the strongest signal is the one the audit gate produces. + incident lists show real problems. + the owner was restarted on the new code (T15e's live attempt kept running) and the log holds 83 Scheduler rows. − accepted attempts show as `verified` only after the audit over them passes, so the success rates of REQ-027 stay low until T18 completes.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-027

## D-086 — Audits are read-only; REQ-027 plan r7 sequences the cross-check after the primary audit

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-077, D-080
- **Context:** T19 failed to start with `INTEGRATION_CONFLICT`. No task was stale: the only two extremes of the DAG were T18 and T18b, the parallel audits, and each had patched source (T18 alone changed 29 files) in the same files differently, so every task after both (T19 and all of M6) was unintegrable.
- **Decision:** (1) System rule: an audit may change only the files it declares (report, ledger). The M6 adapter compares the snapshot with its base (`git diff`) and rejects an audit that touched anything else (`gates.audit_read_only`, default on); the auditor prompt, the planner prompt and `modules.md` say so. (2) The integrator's conflict message now starts with the clashing tasks. (3) Only for REQ-027, with the owner's choice (option 1): plan r7 makes T18b run after T18; T18 is kept with its fixes, T18b (and T19, M6) are redone, so T18b audits the tree that already holds T18's fixes, read-only.
- **Consequences:** + two auditors can no longer collide in later projects; defects stay visible as findings the router can learn from. − T18b's own earlier fixes were discarded and may reappear as open findings, which the gate sends back to the builders (up to `gates.max_reworks`). − T18's source edits are grandfathered; the rule applies from now on.
- **Source:** [day log](2026-10/W4/2026-10-19.md) · REQ-027

## D-087 — Forward remediation: an audit rejection redoes the named tasks and the tests over them, not the whole downstream

- **Date:** 2026-10-20 · **Status:** Accepted (owner: "pausa y construye la remediación") · **Refines:** D-077, D-083
- **Context:** T18b found four real high defects; one named T3, the plan root, so the rework reset 30 tasks (everything downstream), when only 8 tasks were wrong and the rest of the accepted work was sound. A rework cascade also made a late finding as expensive as the first build.
- **Decision:** (1) `gates.rework_scope` (default `named`): the audit sends back the tasks its findings name, the `kind: test` tasks over them (their result no longer proves anything) and itself; what depends on a named task keeps its accepted result and the integrator merges the fix (a snapshot on top of the old one) with theirs. `downstream` keeps the old behaviour. M1 takes an explicit `cascade` flag and still never reads classifications. (2) A task is `ready` only when every ancestor is completed (needed once a middle task is not reset). (3) `scheduler-op REQ rework T1 --only` is the owner's version. (4) `scheduler-op REQ withdraw-rework T4,T5` takes a rework back for tasks that redid nothing (a guarded restore to `completed` on the verdict they already had; "completed only from active" stays true for every other path). (5) The integrator merges a redone task over the result it replaced when it clashes with a dependent built on that result (`earlier_of`, `merge-tree --merge-base`). (6) A retry looks past cancelled attempts and refused starts (a pause followed by a retry used to be refused for good), compares a root task's base by ancestry instead of the literal `HEAD`, continues from an accepted result of an earlier plan revision for a task with no prerequisites, and obeys `scheduler-op REQ continue-from TASK ATTEMPT`. (7) `reopen` sends a task to pending when an ancestor is being redone. Applied to REQ-027: 21 of the 30 reset tasks restored, 9 to redo (T3, T6, T8a, T10, T14, T15b, T15f, T17, T18b). T3's first redo started from scratch, dropped files its dependents were built on and had to be redone twice (continuing from att-0042, then contract-only with an owner note).
- **Consequences:** + a late finding costs the tasks that were wrong, not the plan. + the audit trail shows `rework_requested cascade=false` and `rework_withdrawn`. − dependents keep results built on the old version of the fix: the re-run integration test (kind test) and the audit are what catch a semantic mismatch, and a textual overlap surfaces as `INTEGRATION_CONFLICT` naming both tasks. − a finding that really invalidates a dependent must name it, or use `downstream`. − a fix that edits code another task later replaces overlaps with it (T3's guard in a stub): the note for the redo has to keep a contract fix to the contract.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027

## D-088 — An integration gate at acceptance: the task that causes a clash is the one sent back

- **Date:** 2026-10-20 · **Status:** Accepted (owner: patching is fine, but also make it not happen again) · **Refines:** D-087
- **Context:** after D-087 the redone tasks (T3, T6, T10, T15b) kept being accepted and then blocked their dependents later: the clash surfaced only when T8a, T14 or T15f tried to start (`INTEGRATION_CONFLICT`), stopping the run until the owner answered a card. Causes found: a redo that started from scratch rewrote files its dependents were built on (the rule continued only on an unchanged base), and the merge fallback only tried earlier results of the tasks in the clashing pair.
- **Decision:** (1) `gates.integration_check` (default on): when a result is verified, the integrator dry-runs the integration of every task after it that is about to start, as if it were accepted (`PredecessorIntegrator.would_conflict`, objects only); a clash the candidate takes part in turns the verdict into a rejection with the clash as evidence and an owner note («redo it as a small change, keep every file»), and M5 retries it. (2) A task sent back continues from its own earlier result carried onto the redone prerequisites (`rebase`: new base + what the earlier result added, merge base = its original base) instead of restarting on the new base; it restarts only when the carry overlaps. (3) The merge fallback tries the earlier result of every prerequisite as merge base, not only the pair's. (4) Escalation (`gates.integration_retries`, default 2): when a task has already been rejected that many times for the same kind of clash, its result is accepted and the accepted tasks on the other side of the clash are sent back (no cascade) with a note to rebuild on top of it. (5) The gate blames a task only for a clash its previous result did not already have (T15c was rejected twice for a gateway clash between T13 and T15d that it only travelled with). (6) A verification interrupted by an owner restart is rerun once at start (`_retry_interrupted_reviews`, store limit one retry per request) instead of waiting for a person. (7) The gate also merges the candidate with each accepted task built on the result it replaces (hidden until a task further down needed both), and the merge fallback uses the base a side was itself built on (`snapshot^1`), which carries a dependent onto redone prerequisites without needing their history. (8) A rework without cascade puts the dependents that are waiting to start (ready, blocked, recovering) back to pending, so they cannot start while a prerequisite is redone (T15f started with T12 unaccepted).
- **Consequences:** + a clash is caught where it is caused and costs one retry of that task, with the files named. + the same gate would have caught T18/T18b at T18b's acceptance. − the dry run adds a few git merges per verdict (objects only, no refs). − on REQ-027 this took T10 (rejected 4 times), then T12 and T13 rebuilt on it, instead of an owner card per clash. − it only sees clashes with accepted work; semantic mismatches without a textual overlap still depend on the tests and the audit.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027


## D-089 — A task redone over changed code resolves a merge in progress instead of rebuilding from nothing

- **Date:** 2026-10-20 · **Status:** Accepted (owner: do the conflict resolver first, then open a requirement for an integration branch per run and remediation tasks) · **Refines:** D-088
- **Context:** every audit finding that touches a base task makes its dependents give way and be redone one by one; when the redone code overlapped the dependent's earlier result, the carry returned nothing and the dependent restarted from the new base with the earlier result only as a reference (T15d, T15e, T15f; 6 attempts on T15c).
- **Decision:** (1) `PredecessorIntegrator.carry` returns the carried commit even when the two overlap: the tree is git's merge with conflict markers (new prerequisite code first, the earlier result second), kept under `refs/m3/integration/<run>/<task>-carried`, plus the conflicted files; `rebase` stays as the clean-only form. (2) The retry continuation has a new kind `resolve`: the task starts on that merge in progress and its prompt names the files, says to keep both sides' behaviour, to leave no marker and to run both sides' tests. (3) `PredecessorIntegrator.unresolved` finds markers in the result that the repository head does not have; the quality adapter rejects a result that still holds them (`merge conflict markers left in: ...`) with a note. (4) `gates.integration_retries` defaults to 0: a task that causes a clash is accepted at once and the accepted tasks it clashes with resolve the overlap on top of it, instead of the cause being redone first.
- **Consequences:** + a dependent pays one attempt that resolves a conflict rather than a rebuild. + works for every redo after an audit, not only for the gate. − the resolver is an agent: a wrong resolution is only caught by the task's tests and the audits. − still reactive: the structural fix (one integration branch per run, remediation tasks on the integrated tree) is a separate requirement.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027

## D-090 — A retry reads why the independent verification rejected the last attempt

- **Date:** 2026-10-20 · **Status:** Accepted (owner asked why T17 failed 6 times) · **Refines:** D-085
- **Context:** T17 was rejected by M6 three times in a row with the same error: its e2e test ran `npm ci --offline` in `remote/web`, and in the verification sandbox `node_modules` is a read-only mount, so npm failed with EROFS before any test ran (tests failed in under 2 s). The retry prompt only said «rejected by independent verification»; the evidence was an `m6://` reference the agent cannot read, so each attempt repeated the mistake and the task blocked with `attempts_exhausted`.
- **Decision:** (1) When M6 fails an attempt, the quality adapter writes `RUN.notes/<task>.verify.md` with up to three distinct failing checks (command, exit code, tail of stderr or stdout) and the sandbox rules; the next prompt of that task starts with it (`_with_owner_notes`); a pass clears it. (2) The task prompt now says `node_modules` is mounted read-only and a check must not run `npm install`/`npm ci`. (3) T17 was reopened with an owner note naming the cause and passed on the next attempt (att-0171).
- **Consequences:** + a retry fixes the cause instead of repeating it. − the note repeats the tail of the output (≤ 1500 chars per check); a secret printed by a test would reach the next prompt, so tests must not print secrets (existing rule).
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T17

## D-091 — Blocking audit findings become remediation tasks on the integrated tree (REQ-028)

- **Date:** 2026-10-20 · **Status:** Accepted (owner: «ejecuta req28 y soluciona t18») · **Refines:** D-087, D-089
- **Context:** the T18 audit of REQ-027 found 11 high and 8 medium defects naming about 25 tasks (some missing features, e.g. the Telegram bot). Sending those tasks back would rebuild everything above them again, and some had already used `gates.max_reworks`, so the run stopped on a `rework_limit` card whose options (retry, retry with note, stop) did not address it.
- **Decision:** (1) `gates.audit_remediation` (default on): when an audit has blocking findings, the gate records them (`RUN.remediation.json`) and rejects the audit without reopening any task; the owner exits, the watcher builds the next plan revision (`bt_remediation.build_revision`, validated and frozen) with one remediation task per group of findings, `kind: implement`, after the audit's prerequisites, checked by the commands of the tasks that own the findings, and moves the audit after them; then it rebases the run (accepted work kept) and starts the owner. (2) Findings that share a task or overlapping paths are chained (≤ 4 per task); independent groups run in parallel. (3) `gates.remediation_rounds` (default 2) per audit; with none left, or when a task cannot be built soundly, the previous behaviour (named tasks sent back) applies. (4) Each remediated finding is charged to the tasks that own it in the attempt log. (5) An accepted task clears the notes of earlier rounds (a stale give-way note was about to reach the independent T18 audit). (6) The `rework_limit` card says what happened.
- **Consequences:** + a late finding costs one remediation task and one re-audit, not a cascade; accepted tasks stay accepted. + the original tasks are not rewritten, so their dependents stay valid. − remediation tasks are checked by the existing commands of the owning tasks plus the regression tests the agent adds to them; a fix not covered by those commands relies on the re-audit. − the integration branch per run (REQ-028 part 1) is not built: the integrator still merges ancestor snapshots, which the resolver (D-089) makes cheap.
- **Applied:** REQ-027 T18 → plan r8 adds T18.1 (F1-F4), T18.2 (F5-F8), T18.3 (F9, F10) chained and T18.4 (F19); kept 29, redo 8 (T18, T18b, T19, T20-T24), new 4.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-028 · REQ-027

## D-092 — The verifier installs the locked dependencies when the attempt left none

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-090
- **Context:** the first remediation task of T18 (T18.1) was rejected three times with the same class of error: `Cannot find package ...` in `npm run verify`. The agent never ran `npm ci`, so its worktree had no `node_modules`, the sandbox fell back to the global eslint, and each retry «fixed» the ESLint config to dodge a different import. With the dependencies installed (`npm ci --offline`, 270 packages from the local cache) its code passed lint, typecheck, tests and build.
- **Decision:** (1) M6 provisions `node_modules` from the snapshot's `package-lock.json` when the attempt has none and the repository has no identical one: `npm ci --offline --ignore-scripts` in a scratch directory with only the manifest and lock, cached by content hash (`~/.cache/m6-deps`, `M6_DEPS_CACHE`), mounted read-only (`policy.provision_dependencies`, default on). (2) An attempt's own `node_modules` without npm's hidden lockfile (an install that stopped half-way) is ignored. (3) A failure that says a module/package is missing tells the agent, in the next prompt, to install its locked dependencies and not to edit configuration; the task prompt says to install the lockfile first.
- **Consequences:** + a missing install no longer burns attempts and no longer pushes agents into config edits. + offline and without install scripts, so no package code runs on the host. − a package that needs its install script (native build) fails the check instead of being built; the agent's own install in its worktree still takes precedence.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T18.1

## D-093 — The plan check warns about verifications that need the network

- **Date:** 2026-10-20 · **Status:** Accepted (the network warning is superseded by D-095; the planner file-ownership part stands) · **Refines:** D-090, D-092
- **Context:** reviewing Pictures REQ-020 before launch, seven command verifications (T7, T10, T14, T14a) run `--live`/`--deployed` against real Gemini, Whisper and the deployed app, and T1 needs a Postgres server. M6 runs every check offline in a sandbox (no network, no database), so they can never pass; the tasks would burn their attempts, like T17 did on `npm ci`.
- **Decision:** `plan-json check` warns for a command verification that uses `--live`/`--deployed`/`--remote`/`--prod`, a non-loopback URL or a network tool (`curl`, `ssh`, `gh`, `vercel`, `docker`, ...), and says to verify a receipt file the task leaves after running the live check. The planner prompt says the same. A warning, not an error: a plan can still be launched knowingly.
- **Consequences:** + the failure is found when the plan is written. − the check is a heuristic on the command text; a database or service reached through a plain `npm test` is not seen.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · pictures REQ-020

## D-094 — The panel's live streams share one computation instead of one per open tab

- **Date:** 2026-10-20 · **Status:** Accepted
- **Context:** the bitácora panel (`localhost:8765`) kept dropping and answering slowly. The service was alive but its process used 75–110 % of a core: each open tab holds a plans SSE stream that, on every change of any run file (the running scheduler writes constantly), re-parsed every plan of every project (`plan_status` → markdown plan parse → `infer_kind` recompiling regexes per task line) and re-stat'ed all run stores every 0.25 s. The unit also restarts itself whenever the skill code changes (`ensure_server` stale check), which, while editing, left short windows with the port closed.
- **Decision:** (1) `bt_plans_api._shared_value`: the fingerprint (0.5 s window) and the rendered plans/plan frame (1.5 s window, keyed by fingerprint) are computed once for all clients watching the same view; a busy run is coalesced per client, never dropped; entries older than 60 s are pruned. (2) `bt_planstatus._markdown_structure` is memoized by (path, mtime, size). (3) `bt_agent_models.infer_kind` uses precompiled patterns.
- **Consequences:** + steady CPU of the panel went from ~78 % to ~20 % with the same tabs open; page latency halved (`/` 0.35 s → 0.15 s). + N tabs cost about the same as one. − a plan view can lag a change by up to ~2 s. The per-client `flow_events` poll of the live stream (`bt_live_api`) is still not shared (residual ~20 %).
- **Source:** [day log](2026-10/W4/2026-10-20.md)

## D-095 — Independent checks run on the host network; the plan check warns about shell chains

- **Date:** 2026-10-20 · **Status:** Accepted · **Supersedes:** D-093 (network warning)
- **Context:** Pictures REQ-020 has live checks (Gemini, Whisper, the deployed app) and database tests. The owner does not need the checks offline and agents already run unrestricted with production deploys authorized (D-078), so the offline sandbox only made good plans unlaunchable. Testing the plan against the real parser also showed that M6 rejects shell syntax (`a && b`: 8 verifications of REQ-020 could never compile) and refuses any command naming `migrate`/`deploy` (`npm run asesor:migrate`).
- **Decision:** (1) `QualityPolicy.network` (config `verifier.network`, default on): the sandbox shares the host network and mounts `resolv.conf`, `hosts`, `nsswitch.conf`, `/etc/ssl`, `/etc/ca-certificates` read-only; the namespace handshake no longer demands a private network namespace then. (2) `allow_production_actions` (config `verifier.allow_production_actions`, default on) skips the deploy/migrate operator-review guard. (3) `verifier.env_file`: a dotenv file outside the repositories whose variables the checks receive (`bt_verifier_env`; secret-looking values and credential URLs redacted); the sandbox still starts with an empty environment. (4) The plan check no longer warns about live checks; it warns when a command verification uses shell syntax and the planner prompt says one command per verification. (5) Pictures REQ-020 plan: 5 chained verifications split (24 commands), T15b now after T15.
- **Consequences:** + live and database checks can pass; a retry of a live check costs real calls. − a check can fail for external reasons (provider down, quota); − a verification now reaches the internet and can mutate what it points at (the plan owns that choice). Both are switchable per owner config. M6 still does not support `&&` chains (only a leading `cd`); splitting is the rule.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · pictures REQ-020

## D-096 — A stopped task says what it needs from the owner, what the owner can do and the error

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-020 (decision requests)
- **Context:** the owner asked that a blocked task show clearly what it needs from them (or what they can do) and the error. Cards showed a reason code and a one-line summary; the real error (the failing check output) lived in a note file, and a cancelled attempt only said `cancelled_by_executor` although M1's audit trail held who cancelled it and why (Pictures REQ-020 T1 att-0001: another session cancelled it for a wrong base).
- **Decision:** every request carries `needs` (what the run waits for), `you_can` (concrete actions) and `error` (the M6 failure notes, the closure by hand and the last failure). Known reasons have guidance (transient/quota: not a code defect; code or environment: read the error, retry with a note or revise; integrity: look first; unknown: look). Verifier reviews say whether the verifier broke (reject so it retries), a manual check needs a person (the instruction is shown as «Comprobar a mano: …») or the checks gave no verdict. Shown in the CLI card, the plan page card and, in one line with a link, on the blocked task row; the notification now names what is needed. `bt_attempt_facts.manual_resolutions` reads `attempt_resolved_manually` so the attempt's failure reads «cancelled by operator: <reason>» (the executor's text is kept as `failure_executor`).
- **Consequences:** + no card without cause or next step. − the guidance text is static per reason code; an unforeseen cause still says «look at the error». Other system-made cancellations (pause, rebase) are not yet explained this way.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · pictures REQ-020

## D-097 — A stop is diagnosed from its evidence, by rules and by a cheap agent, and shown as origin, steps and one recommended move

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-096
- **Context:** the owner could not tell why tasks were blocked: REQ-020 T1 showed «attempts_exhausted» and REQ-027 T16 «identity_unverified». The real causes were a plan check running `git` in M6's sandbox (no `.git`) and a start refused by `INTEGRATION_CONFLICT` between T14a's redo and T14b. The reason code is the last guard that tripped, not the cause. The owner asked that an agent such as Haiku 5.5 or GPT-6 Luna medium explain the stop and tell them how to fix it, visually.
- **Decision:** (1) `bt_block_diagnosis.explain` reads the run's evidence (start rejections, M6 notes, every attempt's failure, closures by hand, the plan) and matches known causes. Each match gives kind, headline, origin, steps and the option to pick. A clash adds the option `rework_conflict`, which redoes, with `--only`, the task built on a replaced result and reopens the blocked one. A review whose commands M6 refuses names each command and the reason. (2) `bt_block_agent` sends the same evidence bundle, with a short sheet of how the system works, to a cheap model (config `diagnosis.profile|model|effort|timeout_seconds`, default Claude Haiku; tools that write are disallowed, Codex runs read-only). The answer must be JSON; it is checked (known kind, offered option, 1-4 steps) and cached per request in `RUN.diagnoses/`. The watchdog asks for it on each new request when `diagnosis.auto` is on; it can also be asked from the panel (`/api/flow/diagnose`, `/plans/<p>/<r>/diagnose`) or with `scheduler-op REQ diagnose <id>`. (3) `bt_page_diagnosis` renders one panel for /flow and the plan page. It shows a kind chip, a headline, «De dónde viene» and «Cómo solucionarlo». The recommended option comes first, the others are folded, and the `retry_with_note` text is prefilled. Error and evidence are folded underneath. (4) M6 accepts leading `NAME=value` assignments (run through `env`; sandbox-owned names refused). The plan check now warns when a verification runs `git`. (5) Later the same day: an audit stopped by `rework_limit` offers `rework_findings` (redo, with `--only`, the tasks the refused rework named; the owner writes the findings, which become each task's audit note). A review where every criterion passed and the only issue is `CHECK_UNMAPPED` recommends `review_pass`. Review cards list each criterion's status.
- **Consequences:** + the card names the cause, where it comes from and the move. On the two real cases, Haiku took 14-19 s and Luna medium 5 s, and both picked the right move once the prompt said the reason code is not the cause. + one-click fix for clashes. − a rule is matched on text; a misleading error can mislead it, which is why the agent's opinion is also shown. − each new stop spends one cheap-model call.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-020 (pictures), REQ-027

## D-098 — The bitácora pull never kills git while it holds an autostash, and never rebases under uncommitted code

- **Date:** 2026-10-20 · **Status:** Accepted
- **Context:** at 13:20 a SessionStart ran `bt_vcs.pull()`: `git pull --rebase --autostash` with an 8 s timeout. git was killed after it saved the autostash and before it applied it back. The timeout was treated as «offline». Every uncommitted change of the skill (D-096 and D-097, about 560 lines in 20 files) vanished from the working tree into `stash@{0}` while two schedulers were running and importing the skill lazily. It was recovered with `git checkout <stash> -- skill/`; the tree had not changed since.
- **Decision:** only `git fetch` is time-bounded (killing it loses nothing). The rebase onto upstream is local and runs only when the branch is behind. It is skipped, with a warning, while any path outside the bitácora has uncommitted changes. It is never killed (600 s bound). A failure names `git stash list` in case work is missing.
- **Consequences:** + a slow network can no longer empty the working tree. − a machine with uncommitted skill work does not receive other machines' bitácora changes until that work is committed (the warning says so).
- **Source:** [day log](2026-10/W4/2026-10-20.md)

## D-099 — A retry reads the history of the task's earlier attempts, and is warned when they keep failing the same way

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-097
- **Context:** the owner saw tasks retried again and again with no change and asked why a retry has no context of the earlier failures. It had only the last verification failure (`RUN.notes/<task>.verify.md`, overwritten each time). It did not see how many attempts had failed, failures of other kinds (refused starts, timeouts, cancellations), or that the error repeated. REQ-027 reached 13 attempts on T15, 12 on T10 and 11 on T6, with the same INTEGRATION_CONFLICT three times on T14. Each budget round stops at `scheduler.max_attempts` (3), but every rework, plan revision or owner retry opens a new round. The card's «same failure» rule never fired either, because a verification failure is stored only as an `m6://` reference.
- **Decision:** `bt_attempt_history`. M6 appends each rejection (the failing commands and the tail of their output) to `RUN.notes/<task>.history.jsonl`, with a signature: commands and error lines without numbers, hashes and paths. Other failures come from M1's attempts. The retry prompt gets «Earlier attempts of this task», oldest first and at most 6, after the owner and audit notes and before the last failure in full. A repeat is written as «the same failure as attempt #N». When the last two or more attempts share a signature, the prompt adds a WARNING: find the root cause, which may be outside the code, and report it instead of repeating the change. The card uses the same count. A known cause that keeps coming back says «Ya van N intentos seguidos», and an unknown one says «Los últimos N intentos fallaron exactamente igual». The diagnosing agent reads the same history.
- **Consequences:** + a retry no longer starts blind, and repetition is visible to the agent and to the owner. − attempts verified before this change have no recorded text (they show as «not recorded»); the signature is a heuristic and two different errors on the same lines may collide.
- **Source:** [day log](2026-10/W4/2026-10-20.md)

## D-100 — A retry of a failed attempt is carried onto its prerequisites' new work, never continued on a stale tree

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** the retry continuation of 2026-10-19 (`3fa49886`)
- **Context:** REQ-027 T18, the independent audit, came back twice with the same F1/F2 after T16 and T17 had been redone. T16's att-0199 already had `reverse_proxy 172.20.0.1:8790`. T18's att-0201 had started from its own previous snapshot (att-0198) and audited the old tree. `RetryContinuation._plan` only checked whether the base had moved when the earlier work was sent back by an audit. A failed or rejected attempt «continued whatever the base», which a test pinned. Every loop of «audit rejects → prerequisites fixed → audit retried» therefore re-read stale code. This is one source of the long attempt counts.
- **Decision:** every retry compares the base it starts from today with the previous attempt's base (integration commits are deterministic, so an unchanged base is an exact match). When the base is unchanged, the retry continues from the snapshot. When it changed, the snapshot is carried onto the new base (`carry`: a merge over the previous base, with conflict markers to resolve when the two overlap). When the snapshot cannot be carried, the retry starts on the new base with the old snapshot as read-only reference. When the previous base is unknown, the old behaviour stays. The prompt note says the prerequisites were redone and their work must be kept.
- **Consequences:** + a retried task, especially an audit, sees the fixes it is waiting for. − a failed attempt that overlaps the redone prerequisites now resolves conflict markers instead of silently dropping their changes.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027

## D-101 — Fingerprint central decisions without treating them as evidence payload
- **Date:** 2026-10-20 · **Status:** Accepted
- **Context:** REQ-029 requirements-v1 could not validate because the canonical `DECISIONS.md` is 181,964 bytes, while explicitly supplied evidence is intentionally limited to 65,536 bytes.
- **Decision:** Keep the full canonical `../../DECISIONS.md` authority fingerprint and drift detection, but compute its SHA-256 incrementally in bounded memory. It remains digest-only and is not loaded as review evidence; all supplied evidence and the persisted snapshot keep their existing limits.
- **Alternatives:** Omit the canonical decisions fingerprint (weakens authority drift detection); raise the general source limit (expands evidence payload limits unnecessarily); truncate the file (misses changes).
- **Consequences:** + large central decision logs remain verifiable without weakening evidence bounds / − full file is read on each fingerprint check.
- **Source:** [day log](../../dev/2026-10/W4/2026-10-20.md) · REQ-029

## D-102 — Ignore Scheduler-generated plan status in requirements fingerprints
- **Date:** 2026-10-20 · **Status:** Accepted
- **Context:** Starting a requirements-v1 Scheduler run refreshes the generated `bitacora:status` block in `PLAN.md`. The next requirements check treated ordinary task-state updates as authority drift and could block the following task.
- **Decision:** Normalize only the exact marker-delimited generated status block before fingerprinting PLAN.md. Keep plan scope, task contracts, explicit evidence, and all other content fingerprinted; status-block edits cannot silently change approved requirements.
- **Alternatives:** Re-record requirements after every task-status update (causes approval churn); exclude the whole PLAN.md status section (too broad); stop Scheduler status projection (loses useful read-model visibility).
- **Consequences:** + Scheduler progress no longer revokes unchanged requirements approval / − correctness depends on the status block retaining its reserved exact markers.
- **Source:** [day log](../../dev/2026-10/W4/2026-10-20.md) · REQ-029

## D-103 — Approve structural recovery r2 and temporarily unblock REQ-027
- **Date:** 2026-10-20 · **Status:** Accepted
- **Context:** Existing ordered REQ-027 lineage repeatedly rejects T15a against stale accepted T15b after ordinary rework exhaustion. Owner approved the independently reviewed REQ-029 r2 amendment and explicitly requested T15a unblocked concurrently with Pictures REQ-020.
- **Decision:** Execute the reviewed 24-task r2 through Scheduler, preserving accepted T1–T3. Automatic future structural recovery requires full evidence, scoped convergence, preserved counters, both-side proof and independent audit. Separately authorize one supported owner-operated T15b-only rework and reopen T15a now; this interim owner intervention is not proof of automatic recovery. Keep REQ-020 running. No relay or continuous coordinator log monitoring.
- **Alternatives:** Unchanged T15a retry retains the stale conflict; waiting for the complete upgrade delays current work.
- **Consequences:** + Current tasks can progress while the system upgrade runs / − owner-operated rework grants a fresh ordinary budget for T15b; the future automated path must preserve exhausted counters.
- **Rollback:** Stop/hold via Scheduler; preserve frozen revisions, snapshots and audit history. No product-code rollback or deletion is authorized by this ruling.
- **Source:** Owner chat approval and unblock request; conflict-amendment/REVIEW.md and DELTA.md.

## D-104 — The integration give-way is not held to the audit rework limit

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-088, D-089
- **Context:** REQ-027 T4a was rejected seven times by the integration gate («T4a vs T5a»: `bt_remote_api.py`, `bt_server.py`, `test_remote_api.py`) and stopped on `same_cause_limit`; the cards (and a cheap agent) told the owner to patch T4a's files. The cause was in the rule: when a redone task clashes with accepted work that was built on the result it replaces, the gate is meant to accept the task and send those others back to resolve (give way). The check that decides it used the same limit as an audit's rework (`max_reworks`, 2). T5a had already been sent back that often by earlier audit rounds, so the give-way was refused and the gate rejected T4a again, for a clash that only the others could resolve. Retrying could not help, so each round burned attempts and ended in the owner.
- **Decision:** the give-way is checked as an operator-style rework (`Scheduler.rework_problem(..., owner=True)`), not as an audit verdict, and has its own ceiling `gates.integration_rework_limit` (default 6 sends back per task) against ping-pong; past it the clash is rejected on the task that caused it as before. A test reproduces it (the other side already reworked `max_reworks` times) and fails without the change.
- **Consequences:** + a redone task is accepted and its dependents rebuilt on top of it, with no owner involved. − the accepted tasks can be sent back more often than `max_reworks` (up to the ceiling) when they keep clashing with redone upstream work; the real prevention of that churn is REQ-029 (structural recovery) and the integration line per run (P-134). Tasks that edit files outside their declared paths (T5a edited T4/T4a's files) still cause the clashes in the first place: not addressed here.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T4a

## D-105 — The architecture checks of a project travel with every implement task; the decisions log may grow without revoking approvals

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-090, D-101
- **Context:** the REQ-029 regression task (T7) failed on five module-boundary tests: `bt_recovery_conflicts.py`, `bt_recovery_convergence.py` and the quality adapter imported the M5 package outside its adapter, and a test imported the core. Each task that wrote those files verified only its own tests, so the first run of the project's boundary tests was the final regression, which cannot repair anything; its card then offered to retry it. The failure note also clipped the output to its last 1500 characters, so only the last of five failures was visible. Separately, appending D-104 to `DECISIONS.md` stopped the REQ-029 run (`REQUIREMENTS_REVALIDATION_REQUIRED`): the requirements gate fingerprints the whole decisions log, so any new decision by any session revokes the approval.
- **Decision:** (1) `project.json` `guards` lists a repository's architecture checks; `plan-json check` warns for each `implement` task of that repository that lacks one (`bt_plan_guards`), and the planner prompt says to carry them, so the task that breaks a rule is the one told to repair it. The metodologia project lists the five boundary tests. (2) The M6 failure note names every failing test (`FAIL:`/`ERROR:`/pytest `FAILED`) before the clipped tail. (3) The requirements gate treats a decisions log that is the approved text plus appended lines as unchanged; editing the approved text still counts as drift. (4) T3b, T4 and T4a of REQ-029 were sent back with notes naming the rule and the offending lines; T7 waits for them.
- **Consequences:** + a boundary violation is caught by the task that writes it. + logging a decision no longer halts runs. − the guard command (about 100 s here) runs on every implement task of the repository; − it covers only what the project lists, and a plan frozen before has no guards until revised.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-029 T7

## D-106 — A failure note shows the real error: both streams, no notices, early error lines kept

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-090, D-105
- **Context:** REQ-027 T15c failed `npm run verify` repeatedly and the owner's card (and the agent's next prompt) showed only `npm notice New major version of npm available`. The note took the first non-empty stream, and stderr held only npm notices while the failing test (`failure review route did not load the rejected task's reviewAttempt`, audit finding F26) was on stdout, so every retry was blind. The same week REQ-029 T7 failed on `test_flow_contract` (a global coverage test that wants every new M1 audit kind and module table registered in the /flow bus) because the plan runs the regression before the task that owns the bus: a coupling the tasks that add the kinds do not see.
- **Decision:** (1) The failure note reads both streams, drops `npm notice/warn` lines, and when the output is longer than the tail keeps up to 20 earlier error lines (`error`, `TS1234`, `AssertionError`, `✖`, `FAIL`…) and names every failing test. (2) The metodologia project guard (D-105) now includes `tests.test_flow_contract`, so a task that adds an audit kind or table is told at once. (3) REQ-029: T6a was sent back to register the three recovery audit kinds and four tables in `bt_flow_bus`; T10 builds the views on top. (4) REQ-027 T15c retried with the exact failing assertion.
- **Consequences:** + retries see what failed. − a failure that is only on stdout and only noise-like lines is still shown whole; the clipping remains 1500 characters of tail. The plan-level cause (a regression task before the owner of a coupled registry) is not detected by a lint yet.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T15c, REQ-029 T7

## D-107 — A test must not depend on the zone or the date it runs on

- **Date:** 2026-10-20 · **Status:** Accepted
- **Context:** REQ-029 T7 failed again, now on `test_codex_structured` (`None != 1792562880`), unrelated to the recovery work. The limit text «Try again at Oct 21st, 2026 1:08 AM» is parsed as local time and counted only while in the future. M6 runs with `TZ=UTC` (empty environment), where 01:08 UTC had already passed, so the reset was unknown; on this machine (UTC-5) the same test would have started failing at 01:08 tonight. The task could not have fixed it and every retry repeated the failure.
- **Decision:** the test pins the zone (`America/Bogota`) and the clock (`1792540000`) around the call and keeps its expected value; it passes under UTC, Bogotá and Tokyo. The running T7 was retried with this exact change as the owner's note (the test file is T7's to change; the parser is right). A plain retry would have failed identically.
- **Consequences:** + the suite no longer depends on the zone or on today's date for this case. − other tests may hide the same dependency; the full suite has not been run under `TZ=UTC` (it takes about nine minutes and loads the machine while runs verify), so that sweep is pending.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-029 T7

## D-108 — A failed check is run again once; a pass on the rerun counts

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-106
- **Context:** REQ-027 T15c and T15d were blocked by the same 20-45 s browser test (`panel-browser.test.mjs`, waits of 7-30 s). It passes when run alone on the failing attempt's worktree and fails when the machine is busy: at the time the load average was 16 on 8 cores, with Baldur's Gate 3 at about 560 % CPU, three runs, their agents and a test suite running. Each timing failure spent an attempt of a task whose code was fine and ended in a card for the owner.
- **Decision:** `QualityPolicy.rerun_failed_checks` (config `verifier.rerun_failed_checks`, default 1, 0 = never, at most 3): a command check that fails is run again; if it passes, the check passes and its stderr says «failed once (exit N) and passed when run again; flaky under load»; if it keeps failing, the last run judges it. A test covers pass-on-rerun, never, and the bound.
- **Consequences:** + load-induced failures stop costing attempts; the note stays in the evidence. − a genuinely intermittent defect can pass once; a check that really fails costs its duration twice (45 s here); the rerun is invisible in the verdict except for that stderr note, so there is no flakiness metric yet. The owner process of a run reads it at its next restart. Playing a game on this machine still slows every run.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T15c, T15d

## D-109 — A check on the audit's own ledger cannot stop the audit gate from running

- **Date:** 2026-10-20 · **Status:** Accepted · **Refines:** D-091
- **Context:** REQ-029 T8 (the backend audit) found 14 high defects and was rejected three times with «F1 (high) is still open and blocking». Its verification was `recovery_acceptance.py audit --ledger <ledger>`, which exits 1 while a blocking finding is open. The audit gate (which turns blocking findings into remediation tasks, D-091) runs only after M6 passes, so the audit could never pass, the gate never spoke, and the attempts were spent without a remediation task; the card then offered a plain retry.
- **Decision:** for a `kind: audit` task whose every failed check names the task's own findings ledger, the gate judges the ledger even though M6 said FAIL: blocking findings reject the audit through the gate (evidence, remediation, or rework as before); with nothing against the ledger the failure of the check stands. A test covers the three cases (blocking ledger, clean ledger, a failed check about something else) and fails without the change. The ledger decision belongs to the gate (`gates.audit_blocking`); a verification should check the ledger's form.
- **Consequences:** + audits that verify their ledger with an exit code no longer deadlock. − the rule is matched by the ledger path appearing in the command; a differently written check is not recognised. The plan's acceptance wording «contains no open critical or high finding» is now judged by the gate, not by that command. REQ-029 T8 retried (att-0029).
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-029 T8

## D-110 — A task that changes a module runs that module's own tests (path-scoped guards)

- **Date:** 2026-10-21 · **Status:** Accepted · **Refines:** D-105
- **Context:** REQ-029 T7 (the final regression) failed on four tests of the existing M6-M1 adapter. T4 had added a verification-map guard to `_deliver_one` (`bt_scheduler_quality_delivery.before_acceptance`) that treated ordinary tasks as if they needed a map, so the verdict was never submitted. T4 verified only its own tests; the adapter's test directory ran first in T7, which cannot repair. Same class as the boundary tests (D-105) and the flow contract (D-106).
- **Decision:** project guards (`project.json`) accept `paths` (globs): the guard applies only to tasks that declare a matching `expected_paths`. The metodologia project now lists, for each package (`bt_planner` with the plan adapters, `bt_scheduler_core`, `_decision`, `_executor`, `_monitor`, `_quality` with `bt_scheduler_quality_*.py`, `_recovery`), `cd skill/scripts && python3 -m unittest discover -s <package>/tests`. `plan-json check` warns for each implement task that lacks the guard of a module it touches. T4 of REQ-029 was sent back with the four failing tests and the cause; the REQ-029 plan, frozen earlier, has 21 such warnings and no guards.
- **Consequences:** + the task that breaks a module's tests is the one told. − each guarded task pays the module's test time; the guard matches declared paths, so a task that edits a module without declaring it escapes (the planner's declared paths are guidance, not a limit).
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-029 T7

## D-111 — A fix reaches the audit only through the tasks between it and the audit

- **Date:** 2026-10-21 · **Status:** Accepted · **Refines:** D-087, D-104
- **Context:** REQ-027's T18 audit found the same findings for rounds (F2, F26, F32 for five rounds, then F41/F42 twice) although the named tasks were redone each time. Checking the trees: T8a's redone result (`bt_remote_edit.py` with the objective aliases and the plan-drift/rollback guards, 103 lines) is absent from T16, T17 and the audited T18 tree (the old 57-line file). An audit reads the tree built from its prerequisites' accepted snapshots, and each accepted task keeps the version of the files it was built on: `rework --only T8a` replaces T8a but T9 (built on the old T8a) is the lineage T16/T17/T18 inherit, so the fix never arrives; the integration gate only rebuilds tasks that clash by text. REQ-029's backend audit has the same shape (T2/T3b findings, a linear chain to T7/T8).
- **Decision:** (1) The `rework_findings` option (and the CLI step it prints) now includes the accepted tasks that are descendants of the named ones and ancestors of the audit (`bt_block_diagnosis.lineage_between`), so the new result is rebuilt into the lineage; tasks off that path and tasks already pending are left alone. (2) For REQ-027, T8a, T9, T16, T17 were sent back together (T18 waits); for REQ-029, T2, T3b, T4, T4a, T5, T6a, T7 with their downstream (cascade) because the audited tree is T7's. (3) The lasting fix is REQ-028 part 1 (P-134): one integration line per run where each accepted result is merged and every task starts from the current integrated tree; until it exists a rework must carry its lineage.
- **Consequences:** + findings stop returning for tasks that were fixed but never integrated into the audited tree. − a rework of an upstream task rebuilds more tasks (the cost of correctness); the rebuilt ones can resolve conflicts badly (REQ-029 T2's mid-function splice came from that). P-134 is now the main structural debt of the Scheduler.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T18, REQ-029 T8

## D-112 — The give-way ceiling counts only the integration gate's own give-ways

- **Date:** 2026-10-21 · **Status:** Accepted · **Refines:** D-104
- **Context:** REQ-027 T17 was rejected 18 times by «integration gate: T17 vs T18.3 for T18: remote/gateway/server.py» and blocked. D-104 lets the gate accept the redone task and send the accepted one it clashes with back, up to `gates.integration_rework_limit` (6). The limit was checked against the task's total `reworks`, which also counts audit rounds and operator reworks: T18.3 (a remediation task reworked every audit round) had six, so the give-way was refused and T17 was rejected on a clash only T18.3 could resolve.
- **Decision:** the ceiling counts only the gate's own `rework_requested` entries naming the task (`QualityVerificationPort._give_ways_of`, from the audit log); audit and operator reworks no longer count. The tests set six ordinary reworks (allowed) and two prior give-ways with ceiling two (refused). T17 retried on it (att-0329).
- **Consequences:** + the ceiling measures what it was made for, a ping-pong between two tasks. − it reads the audit log on each clash (small).
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T17

## D-113 — A result that puts undeclared files back to an older version is rejected

- **Date:** 2026-10-21 · **Status:** Accepted · **Refines:** D-089, D-111
- **Context:** after D-111 the REQ-027 audit still found F41/F42 (T8a's edit module): T9's tree had the 103-line fix but T16's, built from T9 + T14 + T14b + T15f, had the old 57-line file. The integration of T9+T14+T14b kept 103; adding T15f's snapshot (which carries the older T8a lineage) made the merge return 57. A result that holds an older version of a file a predecessor fixed hands the regression to every merge after it. Whether it came from an agent resolving a conflict with the stale side or from the integrator's fallback merge over earlier results was not established (the T15f snapshot itself shows no revert against its first parent).
- **Decision:** `PredecessorIntegrator.reverted(task, snapshot)` finds files changed to a blob that an earlier commit of the base's history had (and not the base's own), outside the paths the task declares; the quality adapter rejects such a result at acceptance with a note to restore them (`revert_check`, wired like the markers check). It catches agent-made reverts; it does not catch the integrator picking an old side, which stays open. Also done by hand for REQ-027: T6 (new finding F55, timestamp cursor), T15f, T16, T17 sent back with the instruction to keep T8a's newest `bt_remote_edit.py` (a targeted rework instead of the 21-task cascade the card offered). REQ-029 T5a retried with the fix for its `.git`-dependent test (a disposable repository).
- **Consequences:** + a stale-file regression is rejected where it is made. − heuristic by blob history (40 commits deep), false positive when a task deliberately restores an older version of a file it does not declare. The true fix is still one integration line per run (P-134).
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T18

## D-114 — Remediation tasks of one round run one after another

- **Date:** 2026-10-21 · **Status:** Accepted · **Refines:** D-091, D-112
- **Context:** REQ-027 T18.2 was blocked after ten attempts by «integration gate: T18.2 vs T18.3 for T18.3» with the give-way ceiling (6) reached. The remediation tasks T18.1, T18.2, T18.3 and T18.5 had each been sent back six times by the gate: remediation tasks of different components were built side by side but edit the same files (`remote/gateway/server.py`, `bt_remote_api.py`), and the chain T17 → T18.1 → T18.2 → T18.3 was rebuilt in full for each audit round and each rework of T17.
- **Decision:** `bt_remediation.build_revision` chains all the tasks of a round, not only those of one component (`gates.remediation_parallel`, default off; the old behaviour stays available and tested). For the running REQ-027 the machine setting `gates.integration_rework_limit` was raised from 6 to 12 and T18.2 retried (att-0340).
- **Consequences:** + no clashes between remediation tasks that were never ordered. − a round with several independent areas takes longer. − the raised ceiling is a setting of this machine, not a rule; the chain length (a rebuild of the whole lineage per round) remains the cost of not having an integration line (P-134).
- **Source:** [day log](2026-10/W4/2026-10-20.md) · REQ-027 T18.2

## D-115 — The scheduler answers plain integration clashes itself (at most three times per task)

- **Date:** 2026-10-21 · **Status:** Accepted · **Refines:** D-097, D-111
- **Context:** the owner, seeing 20 attempts on one task, said the scheduler cannot try the same thing and fail the same way 25 times. Measured on the M1 history: REQ-027 has 343 attempts for 43 tasks; of its 67 rejections 54 are clashes between accepted tasks (30 at the integration gate, 24 start rejections) and only 21 are failed verifications; the longest streak of the identical failure signature is 5, usually 3 (M5's `same_cause_limit` works). What repeats is the failure CLASS across resets: each rework or retry gives a fresh budget, and a person had to answer the same card (redo the task built on a stale result) about two dozen times.
- **Decision:** the watchdog answers a card by itself when its diagnosis is a plain integration clash with the `rework_conflict` option and high confidence (`Watch._heal`, also while the owner keeps working): it redoes the stale side exactly as the recommended option does, records `by: scheduler` and a reason, and stops after `HEAL_LIMIT` (3) such answers per task, leaving the card for a person. Nothing else is answered automatically. The three watchdogs were restarted on it (owners untouched).
- **Alternatives:** automate more kinds (audit rework, retries): rejected for now, they change code or need per-task findings. Remove the human reset (a hard lifetime cap per task): proposed, not built.
- **Consequences:** + the largest class of owner cards disappears. − three clashes per task is a heuristic; the lasting fix is the integration line (P-134) which removes the clashes at their source. Verification reviews where every criterion and check passed and only `CHECK_UNMAPPED` remains (REQ-020 T11) still wait for the owner: asked whether the system may approve those too.
- **Source:** [day log](2026-10/W4/2026-10-20.md) · owner question 2026-10-21


## D-116 — The integration line is the default, and no integrated tree may silently lose an accepted task's file

- **Date:** 2026-10-22 · **Status:** Accepted · **Refines:** D-089, D-113 · **Closes:** P-134
- **Context:** REQ-020's T14 started from a predecessor merge that kept T10's `voice.ts` and dropped T12's `directions.ts` and T13's `packages.ts` (a snapshot that is a git ancestor of another is assumed to be already inside it, even when its tree dropped the file); three attempts went on rediscovering it. Reproduced in `tests/test_integration_invariant.py::Req020Replica`.
- **Decision:** `gates.integration_line` is on for every new run. After every integration (predecessor merge and line fold) `bt_integration_invariant` checks that each file an accepted task left is in the tree with its content (exempt: another task also changed it; a deletion the deleter declares in `expected_paths`; a deletion by a task built on the owner). A violation is restored from the owner's snapshot as one repair commit and recorded; a repair that does not hold is `INTEGRATION_FILES_LOST`; a candidate that deletes siblings' files undeclared is rejected at verification. A run in flight migrates to the line at its next start only if a dry-run fold holds all its accepted tasks (`gates.integration_line_migrate`); else `RUN.integration-line.skipped` says why. The full clashing path list is kept unclipped in `RUN.conflicts.jsonl` (REQ-029 R11).
- **Consequences:** + no silent incomplete tree. − measured on the live runs: REQ-020 would NOT migrate (line holds 5 of 15 accepted tasks: their lineage was built on older results of their predecessors) and REQ-029 holds 7 of 22, so both stay on the predecessor merge, protected by the invariant (no false alarm on either: 0 events). New runs get the line from the start.
- **Source:** REQ-030 (mission prompt-scheduler-hardening)

## D-117 — Tasks are kept apart by declared surface, not by size (only on the line)

- **Date:** 2026-10-22 · **Status:** Accepted · **Refines:** D-114
- **Context:** both nights ran at ratio 1.00 (minutes of attempt / wall): `exclusive_scopes` serialised every `large_change`/`full_feature`/`full_system` task. Replaying the recorded plans and attempt times through the real core (`bt_scheduler_replica`): REQ-020 1.00 -> 1.14 (wall 1587 -> 1397 min, -12 %, equal to the DAG's own bound), REQ-029 1.00 -> 1.01 (34 of 36 tasks claim the resource `recovery-case-v1`, which is always exclusive); 4 or 6 slots change nothing on either, so `max_parallel_tasks` stays 3. The wall time of the night was 2530 min against 1587 of first-pass attempts: the loss is rejected and redone attempts, not idle slots.
- **Decision:** `scheduler.exclusive_scopes` defaults to `[]`; `gates.remediation_parallel` defaults to true. Both take effect only on a run on the line: a run in flight without `RUN.integration-line` keeps the legacy scopes and chained remediation (D-114 stands for it). An explicit owner setting always wins.
- **Consequences:** + new runs overlap whatever declares disjoint paths. − gain depends on the plan's graph; the planner's habit of tagging almost every task with one shared resource is filed as a Proposal.
- **Source:** REQ-030

## D-118 — Minimal rework: a ceiling, content-based rebase, real finding text

- **Date:** 2026-10-22 · **Status:** Accepted · **Refines:** D-087, D-091
- **Context:** REQ-029: 22 rework requests, 140 task redos, ~870 accepted minutes thrown away, one request sending back 23 tasks; its plan revisions reset 74 accepted tasks when 40 had changed content (r2->r6 replay).
- **Decision:** `gates.rework_confirm_over` (3): an audit rejection that would discard more accepted tasks blocks the audit with `rework_impact` (the findings notes are written anyway, with evidence); `scheduler-op rework|revise` refuse with count and estimated minutes until `--confirm`. `gates.rebase_cascade: content` (default): `revise` keeps every accepted task whose own content (objective, scope, checks) did not change; `test`/`audit` tasks over reset work are redone.
- **Consequences:** + ~46 % fewer redos on the recorded revisions. − accepted dependents of a redone task are no longer reset, so correctness relies on the line merge and the redone test/audit tasks.
- **Source:** REQ-030

## D-119 — Proportional verification, mixed evidence and attestation receipts

- **Date:** 2026-10-22 · **Status:** Accepted
- **Decision:** M6 reuses a passing check on the same git tree + command + environment (never a failure), runs expensive checks last and skips them once a cheaper one failed (`CHECK_DEFERRED`), accepts a criterion backed by several checks (`mixed_evidence`), and settles a manual check with an HMAC-sealed coordinator receipt (`scheduler-op REQ attest TASK --reason …`, bound to task + purpose + value + expected; digest in the evidence manifest; the open review is requeued once). `verifier.max_workspace_mb` and `scheduler.min_free_mb` are configurable and the diagnosis names the cause of ENOSPC.
- **Consequences:** + fewer minutes per rejected attempt, fewer cards for manual evidence. − the receipt key sits on the same machine as the agents: it protects against edits and mix-ups, not against a forger with full filesystem access (documented in `bt_attestation`).
- **Source:** REQ-030

## D-120 — Self-healing and evolution are capabilities of the scheduler

- **Date:** 2026-10-22 · **Status:** Accepted · **Refines:** D-115, D-097
- **Decision:** the watchdog runs `bt_scheduler_healing.cycle` over the open stops: closed taxonomy (plan defect, integration defect, regression, environment, criterion without mapping, quota, transient) from the LAST real error; smallest safe repair per class (retry, redo the stale side, retry with a note citing the evidence, accept an all-PASS review with an unmapped extra check, rename a check's purpose to its criterion, insert a repair task before an execute-only task); signature-keyed (idempotent), bounded (`healing.*`, per-cycle cap), never repeats a failed strategy, records in `RUN.healing.json` and `RUN.interventions.jsonl`; `scheduler-op REQ heal stop|revert`. `scheduler-evolve` aggregates the interventions into proposals (HIGH risk -> numbered P- items), applies a LOW-risk setting only after an A/B on replicas, and `bt_recovery_benchmark` (12 stops of the night, versioned results) must not get worse between versions: night 10 human interventions / 1086 min waiting, v1 2 / 76 (minutes = time until the recovery action, not until the work is redone). The quota rule now reads only the last error (REQ-029 called a replaced route "quota").
- **Consequences:** + the same stops no longer wait for a person. − the two stops left for a person are a mass rework and a full disk, by design.
- **Source:** REQ-030

## D-121 — The coordinator, the failure analyst and the mapped-checks gate are on

- **Date:** 2026-10-22 · **Status:** Accepted · **Refines:** D-115, D-120
- **Decision:** (1) the coordinator (`bt_coordinator`, per-project opt-in `coordinator.projects`, today `pictures`) runs the manual live commands of a review on the attempt's snapshot, attests them when all exit 0, and rejects the review (`review_fail`, output as reason) when a command ran and exited >0; a command that could not run leaves the review for a person. (2) `bt_attempt_analyst` (`analyst.auto`, on) reads a task that failed more than twice and puts cause and advice in the next prompt; it executes nothing. (3) `planner.require_mapped_checks` is now ON in the owner's config: a plan with a check that maps to no criterion is not publishable (`planner` refuses with the list); revert with `bt_config set planner.require_mapped_checks false`.
- **Consequences:** + the unmapped-check stops (CHECK_UNMAPPED, T12/T14a) are caught when the plan is written, not at verification; + live evidence no longer waits for a person. − a plan with a supplementary command check must now map it to a criterion; a live run spends the project's real services and credentials (test credentials only).
- **Source:** REQ-030, P-155, P-157, P-138

## D-122 — Engine v2 (subplans, Designer, knowledge stores) is built outside the flow, directly on main

- **Date:** 2026-10-23 · **Status:** Accepted
- **Context:** Master spec v1.7 (`engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md`) redesigns the cycle around functional subplans, versioned compositions and an eighth role. Building it through the scheduler would mean the engine modifying itself.
- **Decision:**
  - Owner rulings are in `engine-v2/CONTRACT.md` (they prevail over the master).
  - Work runs outside the methodology flow (no REQ/plan/scheduler), directly on `main`, with one lead and Codex `gpt-6-luna` high workers (6 max, accounts codex/codex-2/codex-luis); push after each green merge.
  - `PLAN.json` gets a new schema version with optional `subplans`; each subplan sits inside one milestone (D-01 = A, D-02).
  - All 14 private skills are approved, including the 3 Implementer drafts.
  - Designer is a full role: `design/` area in the project repo, opus/high and sol/high, 3 private skills and 4 public adaptations.
  - Visual QA is a third Reviewer axis `visual` (D-05).
  - Researcher gets an external knowledge store and private skills.
  - Upstream skills are fetched, SHA-pinned, license-checked and adapted, never executed.
  - The workspace cleanup has a backup first.
  - Live runs david-ui REQ-001 and pictures REQ-020 stay held.
- **Consequences:**
  - \+ One agreed contract and a self-contained execution prompt (`engine-v2/PROMPT.md`).
  - − `main` is also the live skill, so held runs resumed later will run on v2 code unless pinned to the `pre-engine-v2` tag.
- **Source:** engine-v2 (session fdcfb6a3)

## D-123 — Engine v2 P0: backup by bundle + dirty snapshots, not full tarballs

- **Date:** 2026-10-23 · **Status:** Accepted · **Refines:** D-122
- **Context:** The 18 terminal metodologia run folders (REQ-027 r1–r12, REQ-029 r1–r7) held 574 attempt checkouts, 213 GB, with 12 GB free on `/home`. A literal tarball of each `.state/executor/<run>` (CONTRACT §5) could not fit.
- **Decision:** The backup in `~/backups/metodologia-engine-v2-2026-10-23/` keeps everything that is not reproducible:
  - `refs.bundle`: 1186 refs, verified. It holds the 574 `m3/att-*` branches, 12 merged local branches, 12 merged remote branches and a temporary ref for each of the 588 removed worktree HEADs, so detached HEADs are included too.
  - `dirty/` + `dirty.tar.zst`: per worktree, `status.txt`, the `HEAD` sha, `tracked.patch` (`git diff HEAD --binary`) and `untracked.tar` (non-ignored files). 436 worktrees were dirty.
  - `runs/<run>.tar.zst`: each run folder with everything except the checkout directories, i.e. ledgers, attempts, journal, locks and the per-worktree `.json` metadata.

  Clean tracked content is reproducible from the bundle; ignored files (`__pycache__`, `node_modules`) are not kept. Removed: 585 worktrees (574 attempts + 11 feature/agent/scratch), 3 stale `/tmp` worktrees pruned, 18 run folders, 586 local branches and 12 remote branches. Kept: the 5 WIP branches in CONTRACT §5, plus the unmerged local-only `backup/pre-workflow-removal-20261013` and `wt/T14-4ec8b9d4`. These two are not on the cleanup list.
- **Consequences:**
  - \+ Every deleted ref and dirty file is restorable: `git fetch <bundle> 'refs/*:refs/restored/*'`, then `git apply tracked.patch` in a checkout of `HEAD`.
  - − `df` showed no space freed. `/home` is btrfs with snapper snapshots of `@home`, which keep the blocks until they rotate. Snapshots were not touched.
- **Source:** engine-v2

## D-124 — PLAN.json schema 1.3.0: optional subplans and composition gates inside PLAN.json

- **Date:** 2026-10-23 · **Status:** Accepted · **Refines:** D-122 (D-01 = A, D-02)
- **Decision:** The design is `engine-v2/SCHEMA-1.3.0.md`. It was reviewed by the antagonist before implementation: 1 blocker and 4 major findings, all folded in.
  - Optional `subplans[]` (one milestone each; observable `outcome`; `covers`; criteria carried by their own tasks; `produces`/`consumes` with `contract|implementation|publication` dependencies; checkpoints; integration test; audit; `ui` Designer gate) and `composition_gates[]`.
  - Tasks gain `subplan_id`, `ui` and the `design` kind; verifications gain `environment`/`requires`/`authorization_needed`.
  - Errors: undeclared cross-subplan edges, implement work outside subplans, chains of more than 6 tasks without a barrier, UI work without a Designer gate, and file-existence probes used as behaviour checks.
  - 1.0.0–1.2.0 documents keep validation, canonical bytes and hashes. The 1.3.0 names are refused in them at publication only.
  - New skeletons stay 1.2.0 and the adapter refuses to approve a 1.3.0 plan until F4 makes M1/M2/M6 consume it.
- **Consequences:**
  - \+ One artifact, atomic freeze, P-177 caught by plan structure.
  - − F4 must ship the consumers before anyone can run a 1.3.0 plan.
- **Source:** engine-v2

## D-125 — Engine v2 phases close in order; independent work starts early

- **Date:** 2026-10-23 · **Status:** Accepted · **Refines:** D-122
- **Decision:** Phases P0→F5 are closed (review, suite, push, bitácora) in order. Work that owns no F1 file and does not consume the 1.3.0 schema (F2 role prompts, skills and install support; F3 knowledge store) starts in parallel while F1's schema is on the critical path. F4 consumers start only after F1's schema is merged and reviewed.
- **Consequences:**
  - \+ The six Codex slots stay busy.
  - − Phase entries may report work merged before the phase formally opened.
- **Source:** engine-v2

## D-126 — External verification authority comes from operator files, never the plan

- **Date:** 2026-10-24 · **Status:** Accepted · **Refines:** D-125
- **Decision:** For schema 1.3 `environment`/`requires`/`authorization_needed`, the owner injects M6's trusted ports from operator-owned sources outside the plan and the repos: a required resource exists only if the owner's environment or `~/.config/flow/secrets.env` declares that variable NAME (values are never read, logged or stored); a staging/production verification is authorized only by a matching entry in `<bitacora>/<project>/verification-policy.json`. Absent or unreadable policy, or no match, blocks as BLOCKED_EXTERNAL before any command runs; sandbox needs no authorization.
- **Consequences:**
  - \+ A plan can declare what it needs but can never grant itself credentials or production access.
  - − Each project that wants staging/production checks needs an operator policy file before its first 1.3 run.
- **Source:** engine-v2 F4-9b (lead session 1fbc12c7)
- **Refinement 2026-10-24 (after F4-9 reviews):** a policy entry authorizes only when `environment` matches, its `authorization` text equals the plan's `authorization_needed`, and (if it lists `requirements`) the REQ is listed; an empty variable is not an available resource. Policy and secrets reads refuse symlinks, non-regular files and files over 64 KiB.

## D-127 — The owner approves every design contract before UI work starts

- **Date:** 2026-10-24 · **Status:** Accepted · **Refines:** D-126
- **Decision:** The Designer is integrated through the whole flow. Every design contract version (`design/contracts/<c>@vN.md`) needs the owner's approval — web requirement page or `bitacora.py design approve|changes REQ-NNN <c>@vN`, mirroring plan approval — and the approval pins the contract blob sha256. The M3 gate starts a `ui:true` task only when the contract is in the base tree, approved, and its blob matches the approved hash; otherwise the task waits with an owner-attention reason, without failing or spending code-retry budget. The Runner captures the visual evidence (screenshots per breakpoint × state) that the Reviewer `visual` axis judges. Plans without UI subplans are unchanged.
- **Consequences:**
  - \+ The owner sees and signs off every design before code is written against it.
  - − UI subplans pause at each contract version until the owner answers.
- **Source:** owner, 2026-10-24 (lead session 1fbc12c7)

## D-128 — Planner, Designer and owner work together during planning; plan approval approves the designs

- **Date:** 2026-10-25 · **Status:** Accepted · **Refines:** D-127
- **Decision:** The Designer drafts each UI subplan in the background while the owner and the Planner talk (`bitacora.py design draft|sync|drafts|feedback REQ-NNN`). Drafts live in the requirement folder (`design/<c>@vN.md` contract + `.html` static mockup, state in `design/drafts.json`), never in a repo. The web Plan tab is a live region (poll + per-block digest swap) showing the plan in EN, ES or both, every subplan with its tasks, and under each UI subplan its mockup, contract, Designer questions and an owner feedback form; changes made in the conversation appear without reload. A subplan is redesigned when its PLAN.json part changes and settles (45 s), when feedback arrives, or on request. Spanish translation is incremental per section, cached by SHA-256 (`.translations/cache.json`, `PLAN.es.md`, `SPEC.es.md`), with a tool-less runner-role model. Plan approval is refused while any draft is missing, running, failed, outdated or has unapplied feedback; approval pins each ready draft (`via: plan`, SHA-256) and the run's `design` task copies it byte for byte, so the M3 gate passes and UI tasks do not pause. Requirements that never started a planning draft keep the D-127 flow.
- **Consequences:**
  - \+ The owner sees and corrects designs before approving the plan; one approval instead of one per contract.
  - − Designer sessions (opus/sol high) and translation spend quota during planning, including redesigns after plan edits.
- **Source:** owner, 2026-10-25 (session 0976796f), built outside the flow like D-122

## D-129 — Retire captured executor worktrees after three days

- **Date:** 2026-10-25 · **Status:** Accepted
- **Context:** 173 retained Pictures executor worktrees accumulated dependency/build trees. Standard du reports roughly 150 GiB under the methodology bitácora; Btrfs reflinks/snapshots mean that is not the reclaimable-space figure. David explicitly requested deleting redundant copies and a three-day automatic retention process.
- **Decision:** Opt-in schema-1 M3 retention CLI and an hourly systemd user timer on this machine. Retire only terminal attempts ended at least 72h ago, while holding the executor's exclusive nonblocking lock, after proving exact current content and HEAD match the durable captured snapshot, managed Git/path ownership and no observable process use. Preserve unknown ignored data, post-capture edits, busy roots, nonterminal attempts and recent work. Keep branches, refs, manifests, ledger and audit/handoff records.
- **Alternatives:** Age-based recursive deletion — rejected because active/unsaved work could be lost. Keep every worktree forever — rejected because dependency/build duplication grows without bound. Delete only caches — insufficient to implement the owner's copy-retention request and leaves thousands of checkout files.
- **Consequences:** + bounded retention of reconstructable old copies, explicit reasons for skips, durable action audit; − paused or modified copies remain until reconciled, physical recovery depends on Btrfs snapshots. No Btrfs snapshot deletion authorized by this decision.
- **Rollback:** Disable the user timer; reconstruct a retired checkout from the retained snapshot ref using `git worktree add --detach`. No commit/ref/branch history is deleted by retention.
- **Source:** David's explicit cleanup request; [day log](2026-10/W4/2026-10-25.md).

## D-130 — Collaborative planning: requirements, skeleton, subplan by subplan, approval

- **Date:** 2026-10-26 · **Status:** Accepted · **Refines:** D-128
- **Decision:** Standard and Deep requirements are planned by the owner, the Planner and the Designer together, in four phases shown as a stepper on the web Plan tab (`bt_planning_flow`, state in `<req>/.planning/flow.json`, CLI `bitacora.py planning start|status|outline-confirm|focus|confirm`): (1) only the initial, plan-wide questions; (2) a skeleton of milestones and subplans (outcome, covers, `ui`, no tasks) the owner confirms; (3) one subplan in focus at a time — behavior, design, inputs and tasks — confirmed by the owner, while the Designer drafts only the focused UI subplan; inputs (credentials, hosts, paths, accounts) are asked per subplan and recorded in SPEC `## Inputs` with a `Subplan` column, locations only; (4) the plan goes to `review` when every subplan is confirmed, and approval refuses any subplan not confirmed or changed since (digest of its PLAN.json part, tasks, inputs and draft). Requirements not started on the flow keep D-128.
- **Consequences:**
  - \+ Fewer wasted Designer runs (one subplan at a time); the owner closes each slice with its design and credentials before moving on; execution cannot stop for an input that was never asked.
  - − More owner interactions (one confirmation per subplan); a plan edit after confirmation reopens that subplan.
- **Source:** owner, 2026-10-26 (session 0976796f): questions answered «Tablero de esqueleto», «Confirmar cada subplan», «Credenciales en cada subplan», «Designer en el subplan en foco»

## D-131 — Each finished subplan is tried and approved by the owner; the plan is not done until all are

- **Date:** 2026-10-26 · **Status:** Accepted · **Refines:** D-130
- **Decision:** The run does not pause at the end of a subplan, but a plan with subplans cannot be closed until the owner has tried and approved each one on its own. The Planner writes SPEC `## Pruebas` per subplan (where: local, production, external; how; what to see) and a subplan cannot be confirmed without it. The engine's published subplan version (immutable commit) is exposed in `RUN.projection.json` (`subplans`); the owner is notified and sees it in the Plan tab → Probar, the run card and the «Ahora» strip, opens exactly that commit in a worktree outside the repos (`bitacora.py verify open`), and approves or rejects it. Decisions live in `<req>/.verification/decisions.json`, pinned to the version and commit; a newer version makes them outdated. The review merge refuses while any subplan is not approved. Revert is shown as a command plus the subplans that depend on it; nothing reverts by itself.
- **Consequences:**
  - \+ The owner verifies slices independently and can still test each one after the plan is finished; nothing ships unseen.
  - \+ Built on the engine's existing subplan versions: no change to the Scheduler state machine.
  - − More owner interactions (one approval per subplan); a rejection keeps the requirement open, records the note and files a PENDING item (no automatic corrective task yet).
  - − Only runs enrolled for it are gated (collaborative flow or SPEC `## Pruebas`, and a projection that reports `subplans`); runs planned earlier are never gated, even if resumed. Once seen the gate is persisted in the ledger (`gated`) so a projection written without subplans or a PLAN.json caught mid-edit cannot open it.
  - − `verify approve|reject --by owner` is honor-system like `planning confirm`: an agent must pass it only when the owner said so; the web is the real owner channel.
- **Source:** owner, 2026-10-26 (session d05f524b); implemented manually, not as a bitácora requirement.


## D-132 — A subplan can be built WITH the owner in a hands-on agent session before the plan goes on

- **Date:** 2026-10-26 · **Status:** Accepted · **Refines:** D-130
- **Decision:** From a subplan's «Sesión» tab (or `bitacora.py sessions start|status|finish REQ SP`) the owner starts an interactive Claude Code agent (Sonnet 5.5 medium by default, Opus 5.5 high optional) in a tmux session (D-133) in its own git worktree outside the repos (`~/.local/share/bitacora-sessions/<project>/<REQ>/<SP>`) on a branch `session/<req>-<sp>` created from `origin/main`. The first message carries the subplan's outcome, acceptance criteria, the SPEC requirements it covers and the working rules (small commits, never push, merge or deploy, no other checkout, never print secrets). `finish` records the branch head; `planning resume` lists the sessions and the Planner writes that subplan's tasks around the branch instead of rebuilding it.
- **Consequences:**
  - \+ UI-feel or owner-judgment work (rectangular tables, Backing in REQ-021) can be done interactively before the rest of the plan is defined.
  - \+ No change to the Scheduler or the integration lines; nothing reaches `main`.
  - − The session's branch is not yet adopted by the engine as the subplan's published version (P-205): until then the Planner plans review/tests/integration tasks around it.
  - − The agent runs with permissions bypassed (as every agent here does) and the web only starts it from loopback; one running session per subplan.
- **Autonomous mode (same day, owner: «quiero lanzar la ejecución del subplan desde aquí»):** the engine cannot run one subplan of a draft plan: approval freezes the WHOLE PLAN.json, the draft is full of subplans without tasks (`plan-json check` refuses it), and while the Planner keeps editing, a launch is refused with PLAN_DRIFT. So «Ejecutar subplan» (button next to «Confirmar subplan» and in the Sesión tab; `sessions start --mode auto`) starts a session in the same worktree/branch model whose prompt carries the subplan's tasks in dependency order with their objective, expected paths, criteria and verify commands, and orders it to run them alone, commit per task, use an INDEPENDENT subagent for audit tasks and ask only one batched question when blocked. It is NOT the Scheduler (no frozen run, no guaranteed independent auditor, no durable state machine); the full plan will rebuild the subplan unless P-205 adopts the branch.
- **Source:** owner, 2026-10-26 (session d05f524b), REQ-021 SP-3 and SP-1.

## D-133 — Agents the owner needs to talk to run in tmux, so the web can read and type into them

- **Date:** 2026-10-26 · **Status:** Accepted · **Refines:** D-130, D-132
- **Decision:** The dedicated Planner and the hands-on subplan sessions run inside a detached tmux session on a private socket (`tmux -L bitacora`, names `bit-<project>-<REQ>-planner|hands-<sp>`). `bt_agent_terminal` can `send` text (typed as if by the owner, then Enter), show the `screen` and tell whether it is alive. The Plan tab has a live strip with the agent's state, its last steps and its screen, a text box per agent (a separate block, so the live refresh never swaps it while the owner types), and «Abrir un Planner para este plan». Server actions `agent-say` and `agent-start` accept loopback only and never take a tmux name from the client. Attach by hand with `tmux -L bitacora attach -t <name>`.
- **Consequences:**
  - \+ The owner can unblock or steer an idle agent from the web without access to its terminal; closes the web→agent half of P-203 for agents started this way.
  - − Agents started in a plain terminal window are not reachable (the strip says so); an already running one has to be reopened (its reasoning is lost; `planning resume` rebuilds the state).
  - − A message typed through the web is a plain user message: a busy agent queues it. Typed text is logged in the plan's activity feed (first 100 characters).
- **Continuity (same day, owner: «la sesión debe ser agnóstica, matarla e iniciar una fresca sin perder nada»):** the Planner is started with `--session-id <uuid>` pinned in `.planning/planner.json`; opening or restarting it (web «Reiniciar el Planner») runs `claude --resume <id>`, so the whole conversation returns; if the transcript is gone it starts fresh and relies on `planning resume` plus the Planner's own notes (`planning note`, `.planning/notes.jsonl`: findings, decisions with reasons, questions, to-dos, handoff), which the prompt orders it to write continuously. Verified on the live REQ-021 Planner: killed and resumed with its conversation intact. Also: what the owner does on the web (answering a round, confirming the skeleton or a subplan, changing focus) is typed to the Planner as an automatic notice, closing the wake-up half of P-203 for web-managed Planners; the open round is answered from the Plan tab.
- **Source:** owner, 2026-10-26 (session d05f524b).

## D-134 — The Scheduler runs a plan in stages: a stage is a frozen projection of the draft onto confirmed subplans

- **Date:** 2026-10-26 · **Status:** Accepted · **Refines:** D-130, D-131 · **Supersedes:** the autonomous mode of D-132
- **Context:** The owner wants «Ejecutar subplan» in the Plan tab to make THE SCHEDULER run a confirmed subplan (M1–M6, independent audits, durable state, verification) while he and the Planner keep defining the rest; later subplans join the same run keeping what was accepted. Today approval freezes the whole PLAN.json, `check` refuses a draft with empty subplans, and the launch gate refuses any edit of PLAN.json (PLAN_DRIFT).
- **Options weighed:**
  - (A) A `stages` field inside the working PLAN.json, frozen whole with unfinished subplans marked "draft": the validator would need a second, weaker mode for half the document; a frozen revision would contain unapproved content; every consumer (M1/M2/M3/M6) would need to skip it. Rejected.
  - (B) A separate stage manifest beside an unchanged full revision: two authorities for one run, and the frozen revision still has to be valid as a whole. Rejected.
  - (C) **Chosen.** A stage is an ordinary frozen revision whose content is the *projection* of the draft onto a cumulative set S of subplans. Consumers see a complete, valid, hash-checked plan; nothing in M1/M2/M3/M6 changes; joining is the existing `rebase`.
- **Decision:**
  - **Contract (normal execution, no compatibility requirement).** Every approval freezes a stage; whole-plan approval is a stage holding every subplan/task. The owner explicitly dropped backward compatibility with old plans, revisions and RUN.json files. Schema 1.3.0 subplan revisions carry `stage: {"version": 1, "subplans": [...]}`; a revision without this field means its own complete scope, using the same projection gate. The projection keeps: the tasks of S; tasks without a subplan that are ancestors of a task of S, or whose subplan ancestors are all in S (with at least one), or every task when S is every subplan; the milestones those tasks use; `requirements` = what the kept subplans/tasks cover, in plan order; composition gates whose subplans are all in S and whose task is kept; interfaces whose producer is kept (consumers filtered to kept tasks); every other top-level key unchanged. A task of S whose prerequisite is not kept is refused (`STAGE_NOT_CLOSED`: the subplan it needs must join the stage first). Stages are cumulative (`STAGE_NOT_CUMULATIVE`).
  - **Validation.** The projection passes the unchanged publication validator (schema, graph, subplans, composition gates, UI gates, audits, `audit-ledger`, mapped checks) with the SPEC requirement ids restricted to the stage's; the stage's requirements must exist in SPEC; PLAN.md must agree with the projection for the stage's tasks and milestones. The rest of the draft stays a draft and is never validated by a partial-stage freeze; complete approval validates EVERY SPEC requirement.
  - **Eligibility (methodology side, `bt_stages`).** Partial-stage actions require the collaborative flow; every subplan of S (earlier ones included) confirmed by the owner and unchanged since (flow digest: PLAN.json part, tasks, inputs, `## Pruebas` rows, draft), with tasks and a `## Pruebas` row; no pending plan-wide input; the UI drafts of S ready, pinned with the stage (`pin_for_plan` restricted to S). Refusals name the subplan (`STAGE_SUBPLAN_UNCONFIRMED`). Publication carries the captured plan through validation and freeze; a guard rejects concurrent changes to approval documents (`STAGE_APPROVAL_CHANGED`).
  - **Approval and freeze.** `bitacora.py stage run REQ SP-n[,SP-m]` (web: «Ejecutar subplan» next to «Confirmar subplan») is the owner's approval of the stage: it freezes revision N+1 = projection(draft, S_prev ∪ {SP-n}) with manifest `source: approval` and pins `stage: {subplans, pending_subplans, requirements_sha256, plan_md_sha256}` (unhashed approval-time facts, like `plan_md_sha256` today). Idempotent only when projection, approval pins and remaining-scope metadata equal the latest stage. A changed covered SPEC item requires a new approval revision, even if plan JSON is identical. PLAN.md `status` is not touched: the plan stays in planning. `stage status REQ` lists stages. Like `planning confirm`, the CLI is honor-system: an agent runs it only when the owner said so.
  - **One drift gate for every plan.** The launch/join gate compares projection(draft, S_frozen) with the frozen revision (revision number ignored) and the SPEC requirement items of the stage and the stage's PLAN.md task lines with the pinned digests: any difference is `PLAN_DRIFT`, `PLAN_PROSE_DRIFT` or `PLAN_REQUIREMENTS_DRIFT`; edits outside S never matter; an unreadable draft is `PLAN_INVALID` (fail closed). A running stage keeps executing its frozen revision whatever the draft says (as every run does today); a change to an approved subplan reaches the run only by re-confirming it and running a new stage. `plan-json check` no longer compares the draft's `revision` with a frozen number (drafts are not revisions once staged).
  - **Joining the same run.** No run yet: a new Scheduler run starts on the stage (background owner, as launch does). A run exists: the owner keeps executing its bound revision (`scheduler-run --resume` binds to the run's own revision, not the newest stage, so a restart never fails with PLAN_MISMATCH); while a newer stage is frozen it pauses new dispatch (M1 pause, released afterwards unless the operator had paused it), and when no attempt is alive it stops, rebases onto the newest stage (`rebase_run`, content cascade) and resumes in the same process. Accepted work = M1's rebase rule: a task whose content fingerprint is unchanged keeps its accepted attempt under the configured rebase cascade; a changed task (a stage-1 subplan the Planner re-defined and the owner re-confirmed) is redone with a fresh budget, judges over it too; its subplan publishes version N+1 and D-131 marks the earlier approval outdated.
  - **Lines, versions, gates.** Unchanged mechanisms: the run id survives the rebase, so `refs/m3/line/<run>/<role>/<SP>` lines and published `SP@vN` versions carry over (an unaffected rebase rebinds the same version); a gate composing SP-1 with SP-2 enters with the stage that contains both and consumes SP-1's published version. A subplan consuming another must run with it (closure).
  - **Audits.** A milestone audit or the final audit is an ordinary task: it enters the stage where all the subplans it follows are present, so it runs when its scope is complete, never on a partial milestone. Each subplan's own audit/integration test runs with its stage.
  - **Closing.** A stage run that reaches `completed` is a finished stage, not a finished plan: the notification says so and the projection carries `stage` (`complete: false`). The review merge refuses while the latest stage does not cover the whole draft (`STAGE_INCOMPLETE`, fail closed) besides D-131 (draft subplans not built are «se está construyendo»). The final approval of a staged plan freezes the complete stage (projection must equal the whole draft) and joins the run.
  - **Requirements gate.** For Scheduler execution, `require_ready` waives the PLAN.md/SPEC.md file fingerprints (planning legitimately edits them) because approval scope has separate pins; resume binds to its immutable revision; every other evidence file, DECISIONS.md and unresolved items still block.
  - **What the owner sees.** Plan tab: «Ejecutar subplan» on a confirmed subplan, «En ejecución (etapa rN)» once it is in a stage; run page and «Ahora» card: the stage's subplans and how many remain; notifications at the end of each stage and when a subplan version is ready to try (D-131). Routing is unchanged: M2 picks agent/model per task and audits use the audit route.
  - **D-132.** The hands-on session (Sesión tab) stays; its autonomous mode (`sessions start --mode auto`) is refused with `SESSION_AUTO_SUPERSEDED` pointing at `stage run`.
- **Consequences:**
  - \+ One subplan runs under every Scheduler guarantee while the rest is still being planned; no change to the M1 state machine or M2/M3/M6 routing/acceptance roles.
  - − A subplan that consumes another cannot run before it; a stage can only grow (dropping a running subplan needs a full re-plan).
  - − Joining waits for in-flight attempts to finish (dispatch paused meanwhile). A durable join marker preserves pause ownership between targets and recovers runtime binding after an interrupted rebase.
  - − `stage run` from the CLI is honor-system; the web button is the owner's channel.
- **Rollback:** revert the staged-execution code as a unit before resuming real runs; inspect any run rebased to a new stage and explicitly choose its frozen revision. No automatic migration or legacy compatibility is promised. Scheduler-generated revisions splice into the draft instead of replacing unfinished scope.
- **Source:** owner, 2026-10-26 («Lo que queremos es que el Scheduler lo pueda mandar»), brief `briefs/staged-execution.md`; built manually outside the flow (owner rule).

## D-135 — The Designer composes mockups from a checked david-ui stand-in kit; the owner browses it at `/components`

- **Date:** 2026-10-26 · **Status:** Superseded by D-136 · **Refines:** D-127 · **Tracks:** P-207 (swap for the real package)
- **Context:** The REQ-021 mockups had off-centre layouts, cramped padding and failing contrast, worst in dark theme. The owner wants the Designer to «steal» the components of the planned `@dav033/david-ui` (not built yet: no package, `theme.css` or catalog) and to see them himself.
- **Decision:**
  - **Tokens mirror shadcn/ui names** (`--background`, `--foreground`, `--card`, `--popover`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--input`, `--ring`, `--chart-1..5`, `--sidebar-*`, `--radius`), which is what david-ui's Tailwind 4 `theme.css` will carry (SPEC R3/R18, shadcn base), plus proposed extensions (`--success|warning|info[-soft]`, `--primary-soft`, `--destructive-soft`), type/spacing/shadow scales and the three motion profiles of R8 (`data-motion=subtle|natural|expressive`, `prefers-reduced-motion` collapses to instant). Values: Catppuccin Latte/Mocha, mauve accent, deepened where AA needs it. All of it lives in `kit/tokens.css`; `kit/components.css` reads tokens only (no raw colours). P-207 = replace `tokens.css` values from the real `theme.css` and rename snippet ids to catalog ids; no component rewrite.
  - **Components:** the 30 P1 shadcn components of the inventory (§3.1–3.6) plus Input Group, Radio Group and Progress (P2, forms), written from scratch with shadcn anatomy (no Animate UI/React Bits/Bencho code). One snippet file per component, `kit/components/<id>.html`, with comment-delimited examples (variants and states); `kit/components/manifest.json` lists id, shadcn name, category, priority, states. The Designer copies anatomy from these files; the gallery renders the same files.
  - **Consumption:** a mockup keeps `<!-- kit:css -->` / `<!-- kit:js -->` markers; `kit/inline.py` replaces them with the current `tokens.css + components.css` and `kit.js` (idempotent, re-run after a kit change). `kit.js` (small, optional) binds `#theme`/`#motion` selects and dialog/sheet/menu/popover/tabs/toast/combobox demos. Project tokens win: a project maps its palette onto the same roles in a later `:root`/`[data-theme]` block and `contrast.py <mockup>` checks the effective values.
  - **Checks:** `contrast.py` (every text/surface pair and every non-text edge, both themes); `audit_mockup.py` renders every view × state × scene × theme at desktop and 390 px and fails on text/non-text/focus contrast, mixed alignment, cramped padding and overflow; exits 2 (never a pass) without Playwright/Chromium.
  - **Gallery:** `/components` in the web UI (nav «Componentes»; CLI `bitacora.py components`), one sandboxed iframe per component (so real media queries apply to the width switch), switches for theme, motion and width, search, copyable HTML, and three reference mockups built only from snippets (rendered at 390/768/1280 px and scaled to fit).
  - **Mockup contract kept:** `kit/templates/mockup.html` carries the `.mockup-bar` with the native `view`/`state`/`scene`/`theme` selects that `mockup-bridge.js` drives; `kit.js` shows parts by `data-show-view|state|scene` and `data-hide-state`, so the Designer writes no switching script of its own. The brief (`bt_design_drafts._brief`) gives the kit's absolute path and the three commands, and asks for the audit's RESULT line in the report.
  - **Audit honesty (after the independent review):** colours are read through a canvas (oklch, color-mix…), an unreadable text colour fails as `unmeasured`; focus compares each stop with itself unfocused (an unchanged shadow is not an indicator) and walks every rendered view/state/dialog at desktop width; 0 keyboard stops fails; the planning chrome is the highest block holding the selects and nothing product-like; phone gutters (12 px) and field text inset are checked; sampling, capped walks, gradient backgrounds and a missing `<main>` print warnings. Limits left: P-209.
- **Consequences:** + Designers compose from vetted anatomy and must show a measured PASS; the owner sees every component, variant, state, theme and motion profile. − The audit is heuristic (P-209); the kit's tablet range keeps the full sidebar (P-210); until P-207 the look is a stand-in.
- **Source:** owner, 2026-10-26 («nos vamos a robar los componentes», «una parte donde pueda ver los componentes»); brief `briefs/designer-kit.md`; built manually outside the flow (owner rule).
## D-136 — Real library workspace and owner-chosen creative directions for planning designs

- **Date:** 2026-10-26 · **Status:** Accepted · **Supersedes:** D-135
- **Context:** The owner rejected recreated shadcn-style components and generic mockups, requested real libraries,
  rich motion, three structurally distinct alternatives and an explicit choice before finalizing the contract.
  Implementation is a direct skill edit under the owner's exception, outside the methodology flow.
- **Decision:** Install real shadcn/Base UI, Animate UI, Bencho and React Bits through their published methods in
  `~/.local/share/bitacora/kit-workspace`, outside Git with a local lockfile. The skill owns the manifest, theme,
  demos, offline builder and audit. `/components` shows real demos, source/category/priority/status filters,
  reduced motion, copyable imports and truthful gaps; the HTML stand-in remains at `/components/kit`.
  Planning draft requests launch one bounded batch of 1–3 independent Designer explorations per requirement
  (default 3), each with two candidate thumbnails, revision-specific artifacts, eight-axis notes and rendered
  selector evidence. A rendered DNA gate checks geometry, typography, navigation and motion. The owner chooses
  through authenticated local-panel controls or CLI; only then a finalizer writes the single canonical contract
  and selected HTML. Confirmation/approval refuses unchosen, failed, stale or unfinished designs. `--fresh`
  starts from requirements/unresolved feedback and preserves history. Failed siblings do not erase good work;
  abandoned queued directions expire and automatic failures obey retry/backoff limits.
- **Alternatives:** Recreated stand-in as primary — rejected by owner. One default style or colour-only variants —
  rejected by owner. Production package `@dav033/david-ui` — not available; keep P-207 for eventual catalog adoption.
- **Consequences:** + Real imports, offline single-file mockups, creative choice and reproducible render evidence.
  − Three explorations plus finalization spend more quota. The heuristic gate does not prove aesthetic quality;
  screenshots still need inspection. Provider CLIs already run unrestricted: task scope is contractual, not an OS
  sandbox claim. The installed Bencho Picker does not satisfy the inventory's inertial-wheel contract (visible gap).
- **Rollback:** Use `--directions 1` while preserving owner choice; use the explicit fallback kit if the workspace
  is unavailable. Restore the previous skill implementation only with its historical approval semantics and
  retain all existing exploration/history files. No service restart or REQ-021 relaunch was performed here.
- **Evidence:** `briefs/designer-kit-v2.notes.md`, `briefs/designer-kit-phase4.research.md`, isolated real fixture
  recorded in `/tmp/designer-real-e2e-root`; independent Antagonist A1–A5 corrected with regression tests.
- **Source:** owner briefs `designer-kit-v2.md` and `designer-kit-phase4.md` including ADDENDUM; relay
  `dev/relay/RELAY-20261026-214844.md` continued by Codex.

## D-137 — Security gate per task, independent test oracles and a buildable remediation for subplan plans

- **Date:** 2026-10-27 · **Status:** Accepted · **Supersedes:** the "high risk does not override audit coverage" clause of D-066
- **Context:** REQ-021 SP-1 audit (T1.8) found 5 high and 10 lower defects across T1.2–T1.7; rework would have sent 6
  accepted tasks back (limit 3 without owner confirmation) and the owner called a mass return unacceptable. Evidence:
  `bt_review_policy` forbade any antagonist pass per task while the subplan audit was pending, including risk-high
  security tasks; task checks were self-written happy-path scripts; T1.7's matrix took its oracle from the
  implementation's route map, sent only GET and counted 405/5xx as allowed (F15). The designed fallback (audit
  findings → remediation tasks on the integrated tree) never fired: `_command_covers` accepted only commands that name
  a path, and `npm run <script>` names none; and remediation tasks lacked `subplan_id`, so 1.3.0 plans rejected them.
- **Decision:** (1) Security-sensitive tasks (`bt_planner.quality.security_sensitive`: risk high, kind implement, text
  names a security surface) keep ONE security-only antagonist pass before acceptance under audit coverage
  (`bt_review_policy.SECURITY_GATE`, checklist in `subagents.md` §The security gate). (2) Test oracles come from the SPEC,
  cover every role × method and assert denied cases (`engineering.md` §5, Reviewer standards axis, `oracle_independence`
  warning). (3) Planner states an abuse-case criterion per security-sensitive task (`security_abuse_cases` warning, planner
  instructions). (4) Package-script checks cover their owner's own paths and remediation tasks join the audit's subplan.
- **Alternatives:** Per-commit antagonist everywhere (rejected: one Opus session per commit); a new plan field
  `security: true` (rejected: old plans would not benefit, the text heuristic needs no schema change); making the new
  planner checks errors (rejected: frozen plans are not re-gated, warnings are the cue before approval).
- **Consequences:** + Defects of the SP-1 class are met while the builder still has the context; + an audit rejection
  becomes small remediation tasks (REQ-021: T1.9, T1.10) instead of a 6-task rework. − About one extra security pass
  per security-sensitive task. The security pass is an instruction to the builder, not enforced by the scheduler; the
  audit remains the backstop. The text heuristic can miss a surface that names none of its words.
- **Rollback:** Restore `WITH_AUDIT` in `commit_review_rule` (remove the `_security_unit` branch); drop the two
  warnings in `bt_planner/contract.py`; the coverage and `subplan_id` fixes are independent bug fixes.
- **Evidence:** `bt_remediation.build_revision` on REQ-021's real plan and T1.8 ledger returns revision 2 with T1.9/T1.10
  (it returned None before); `oracle_independence` flags T1.7, T2.6, T4.7, T4.31, T5.4, T6.5 of the same plan;
  tests `test_harness_optimization.ReviewPolicyTests`, `bt_planner.tests.test_security_checks`, `test_remediation`,
  `test_recovery_compiler`; 385 planner tests pass.
- **Source:** owner request in session b4d5d9f9 (relay `dev/relay/RELAY-20261027-145405.md`).
- **Addendum (2026-10-27, same session):** the first real remediation in a staged 1.3.0 plan exposed two more gaps, now fixed in `bt_remediation.apply`: it marked the audited subplan "changed" (owner had to reconfirm a running subplan) and left new tasks out of PLAN.md (stage approval refused). `apply` now re-pins confirmations that held (`keep_confirmed`) and writes the task lines (`sync_markdown`). Tests in `test_remediation`.
- **Addendum 2 (2026-10-27):** `bt_design_directions.choosable` — one direction whose mockup lacks its declared traits no longer hides the sound ones (the aggregate comparison used to block every choice). Owner ruling: SP-3 drops its design contract because its UI is only cards and a group inside the existing Fondos y muebles panel.

## D-138 — A check with no output and no CPU is a hang and fails the code

- **Date:** 2026-10-27 · **Status:** Accepted
- **Context:** REQ-021 T1.10's verification sat 39 min in a test deadlocked on a 2-connection test pool. The verifier cut checks only at `max_command_seconds` (3000 s), kept its heartbeat alive, and `CHECK_TIMEOUT` is classified as transient infrastructure, so healing retried the same hang and the owner had to diagnose it by hand.
- **Decision:** `verifier.max_idle_seconds` (default 600, 0 = off): a check whose whole process tree prints nothing and uses under 5% of a core for that long is killed and FAILS as a code defect, with `[M6] CHECK_HUNG` naming the processes; it is never rerun.
- **Consequences:** + a hang costs 10 min instead of 39-100 and the builder is sent back with the cause; − a legitimately silent, CPU-free wait longer than 10 min (rare) would be failed: raise the key for that project.
- **Rollback:** `verifier.max_idle_seconds = 0`.
- **Evidence:** `bt_scheduler_quality/tests/test_runner.py` (hang fails, busy silent passes, off switch), 98 quality tests; commit `9e3c81a73`.

## D-139 — The failure analyst never judges an audit that rejects, and checks may inherit the environment

- **Date:** 2026-10-27 · **Status:** Accepted
- **Context:** REQ-021 T1.8's re-audit was cancelled after seconds, six times, by the failure analyst: `failures()` counted cancelled attempts and the audit's own `audit gate:` rejections, so three legitimate rejections made the analyst call the audit "not the task" and stop every re-run. Separately, checks started with an empty environment and cost runs whenever a variable was missing.
- **Decision:** (1) `bt_attempt_analyst.failures` excludes cancelled attempts and rejections whose text starts `audit gate:`. (2) Remediation tasks do not inherit tool-level resources (`package.json…`). (3) New `verifier.inherit_env` (name globs, `["*"]` = all) hands checks the owner's environment and every secret-file variable; sandbox-protected names stay refused, secret-looking values redacted.
- **Consequences:** + audits can always run and judge; + remediation can run beside unrelated work; − with `["*"]` code under test can see the owner's secrets (narrow it with globs).
- **Rollback:** `verifier.inherit_env = []`; restore the old `failures()` filter.
- **Evidence:** tests in `test_attempt_analyst`, `test_remediation`, `test_verifier_env`; T1.8 att-0039 completed and produced a real verdict; commits e3d851c96, 6c8da1103, 9dd7c38b0.

## D-140 — The system asks pending Planner assumptions and applies the answer; Planners survive a reboot

- **Date:** 2026-10-28 · **Status:** Accepted
- **Context:** REQ-021 SP-3 could not be confirmed: its only blocker was a Planner assumption waiting for the owner, with no question round, so the panel offered nothing to answer. The Planner had died with a reboot (tmux), and `round new` had overwritten the answered round 13 after a numbering gap.
- **Decision:** `bt_input_rounds.ensure` opens a confirm-or-change round for each pending owner-owned assumption of the focused subplan (never for keys or paths the owner must supply) and `apply_answers` resolves the SPEC row or leaves a note for the Planner; `new_round` numbers by highest + 1; the subplan note links to open questions; the panel revives Planners of plans still in planning (ran within 3 days, conversation present).
- **Consequences:** + no silent block on an unasked assumption; + answers work without a live Planner; − the system writes the Status cell of a SPEC table row (only on an owner confirmation).
- **Rollback:** remove the `ensure` calls and `_revive_planners`; behaviour returns to Planner-only rounds.
- **Evidence:** `tests/test_input_rounds.py` (9), commit `4cd2ed0a1`; round 14 answered via web and applied by the revived Planner.

## D-141 — Stage readiness is a standing gate, not a button surprise

- **Date:** 2026-10-28 · **Status:** Accepted
- **Context:** REQ-021's SP-3 was confirmed by the owner, but «Ejecutar subplan» was refused with three plan errors (evidence citing a later subplan's task, a composition gate that also composes unstaged subplans). The gate that decides it, `stage_problem`, ran only on the button; the full-plan check drowns those errors among the ones of unfinished subplans.
- **Decision:** `bt_plan_adapter.stage_readiness` walks every next stage in plan order (a subplan without tasks ends the chain); `bt_stage_readiness` caches it by PLAN.json/PLAN.md/SPEC.md content, `bt_planning_flow.problems` disables the confirm button with the reason, `plan-json check` prints `ERROR STAGE`, and `plan-json stages` shows the table. Planner instructions: run it after every edit.
- **Consequences:** + structure errors reach the Planner and the owner when they arise; − a subplan cannot be confirmed while its stage is structurally refused (header and environment errors excluded); the test checks structure, not code quality.
- **Rollback:** remove the `problem_for` call in `bt_planning_flow.problems` and the check lines in `bt_cli_plan`.
- **Evidence:** `tests/test_stage_readiness.py`, `tests/test_stage_readiness_gate.py` (9); live run: SP-3..SP-6 pass; commits 0c0aab046, 3ee99ae62.

## D-142 — The owner manages execution and tests from the Plan tab

- **Date:** 2026-10-28 · **Status:** Accepted
- **Context:** the owner could only act on a blocked task (decision cards, recovery, self-healing, rework) on a different page (`/plans/<project>/<REQ>`) or in the terminal, and the Plan tab did not show which subplans had finished running.
- **Decision:** a per-subplan «Ejecución» tab in the Plan tab (`bt_page_planning_run`) reusing the run page's cards and rows, plus «Reintentar» per task and «Devolver tareas aceptadas» (`bt_plans_api.rework` → `scheduler-op rework --only`, cost confirmation); the subplan list shows `ejecución n/m ✓`; forms carry `back` (local `/p/…` paths only).
- **Consequences:** + one place to follow and decide; − the status is read once per few seconds (shared cache); running a single test on demand is still not offered (checks run inside each task).
- **Rollback:** remove the `run` view and tab and the `rework` / `retry-task` actions.
- **Evidence:** `tests/test_page_planning_run.py` (8); rendered SP-2 view checked in a browser; commit `19011d35f`.

## D-143 — Build order follows consumption: a consumer builds on the audited producer

- **Date:** 2026-10-28 · **Status:** Accepted (delegated by the owner: «lo mejor para la arquitectura y el ciclo de vida»)
- **Context:** REQ-021's SP-2 consumes SP-1's contracts but its builder tasks (T2.2–T2.5) depended only on T1.4, so they were built on the pre-audit SP-1. After the audit fixed `proxy.ts`, the permission map and the local mode, SP-2's accepted tasks no longer fit the integrated tree (two real conflicts: `package.json`, `src/lib/cuentas/permisos.ts`); T2.6 could not start and the engine's recovery path was unusable while other work ran.
- **Decision:** the first builder task of a consuming subplan follows the producer's audit (`T2.2 after T1.8b`, plan r12) and the four tasks already built are redone on that base. Accepted over: waiting for the run to drain (hours, with SP-3 piling work on the old base), the unproven conflict-recovery path (blocked by `stale_activation`) and a manual reconciliation outside the flow.
- **Consequences:** + SP-2 integrates with the audited SP-1 and later work conflicts less; − four accepted tasks redone (about an hour) and SP-3's T3.2 restarted.
- **Rollback:** a new revision without `T1.8b` in T2.2's `after`.
- **Evidence:** `git merge-tree` of the two final trees (2 conflicts); plan r12, stage r13, rework of T2.2–T2.5; analyst fix commit `fd29501fb`.


## D-144 — Retire the legacy runtime's duplicated infrastructure only behind proven equivalence (proposal)

- **Date:** 2026-10-28 · **Status:** Proposed (REQ-030 item 9; nothing is removed by this decision)
- **Context:** the durable runtime (`bt_durable` on DBOS + `bt_supervisor`) now owns pictures REQ-021; the legacy
  runtime still owns pictures REQ-020 (29 completed, 2 pending, 1 blocked, no live attempt) and the finished runs
  REQ-019, metodologia REQ-027 and REQ-029. M0 counted ~4–5k lines of generic infrastructure the durable runtime
  replaces. The comparable benchmark (REQ-030 evidence `iter2/bench-runtimes.md`) shows the durable side needed fewer
  agent launches and owner interventions on the same plan and failures, but REQ-021's first live durable attempts were
  orphaned by a supervisor defect (fixed in `366cbf372`): equivalence on a real plan is not yet shown.
- **Decision:** each group below is removed in its own commit, with the full regression, only when its condition holds;
  until then it stays and keeps serving legacy-owned runs.

| Group (legacy) | Durable equivalent | Evidence of equivalence | Condition to remove |
|---|---|---|---|
| Hard-coded REQ-021 repairs (`bt_scheduler_monitor_repairs.py`, the T3.2 option in `bt_scheduler_decisions.py`) | none needed: REQ-021 is `dbos`-owned and the legacy owner refuses it (`OWNED_BY_DBOS`) | ownership record + refusal test | REQ-021 completes on the durable runtime (its `migrate --rollback` window closes) |
| Watchdog and per-run services (`bt_scheduler_watch`, `metodologia-run-*`, `metodologia-monitor-*`) | `bt-durable.service` `Restart=always` + DBOS recovery | engine SIGKILL and PostgreSQL outage e2e (0 duplicate launches) | the durable runtime finishes one real plan (REQ-021) with no owner intervention caused by infrastructure, AND no legacy-owned run is unfinished |
| Hold file (`RUN.hold`, `ops.on_hold`) | `bt-durable pause/resume` (`RunCommand`, request ids) | stale/duplicate command tests | Pause gap closed in REQ-030 iteration 2 (`325905fe4`, patch `bt-task-respects-pause`, `test_durable_e2e.test_a_paused_run_starts_no_retry_until_it_is_resumed`). Remove when no legacy-owned run can still be held (same condition as the outboxes row) |
| Outboxes and second state machine (M1 dispatch outbox, M3 ledger/loop/recovery/shim/procinfo, M4 incident outbox, M5 checkpoints, M6 request outbox) | DBOS steps/child workflows, `bt_supervisor` (systemd units, cgroup kill) | e2e: one process per attempt key across crashes, cancellation stops every writer, one verdict per verify key | no legacy-owned run is unfinished (REQ-020 migrated with `bt-durable migrate` or closed) AND `execution.backend` defaults to `dbos` |
| Healing ×4, ready-monitor, watch restarts | classifier (10 classes) + bounded policy | benchmark: a verifier heap limit cost legacy 2 redundant agent attempts and an owner decision; durable repaired it with 0 extra launches | same as the outboxes row |
| `bt_lock.central_lock`, `bt_integration_lock`, legacy integration line writer | integration by compare-and-swap on refs (`GitLineIntegrator`) | concurrent integration tests, subplan lines e2e | same as the outboxes row |

- **Procedure (per group):** `bt-durable status` for every `dbos` run; `python3 -c` scan of `RUN.owner.json` and
  `.state/scheduler/*.db` for unfinished legacy-owned runs (must be none for rows 2, 4–6); remove the group; run the
  full regression (only the 5 baseline failures allowed); deploy with the usual backup + smoke.
- **Consequences:** + no duplicate engines once the conditions hold; − both runtimes are maintained until REQ-020 is
  migrated or closed; the hold-file gap is a real difference, not a formality.
- **Rollback:** the removal commits are independent; reverting one restores that group.
- **Evidence:** REQ-030 `REPORT.md`, `evidence/iter2/bench-runtimes.md`, `evidence/iter2/orphan-units-20261028.txt`.

## D-145 — Durable runtime: subplans and gates, legacy briefs, manual receipts, pause for retries (REQ-030 iteration 2)

- **Date:** 2026-10-28 · **Status:** Accepted (REQ-030 items 1–3; branch `req030-iter2-wip`)
- **Context:** the durable runtime ran pictures REQ-021 (plan 1.3.0, 4 subplans, 3 composition gates) on one line,
  with a basic brief (no owner notes: T2.6's a1 prompt lacked `RUN.notes/T2.6.md`), and without the M6 attestation port
  (T3.2's valid receipt was invisible, so its reconciliation launched an agent). A paused run still let running task
  workflows launch retries.
- **Decision:**
  - Subplans reuse the legacy definitions (core `Plan.subplans`, `bt_integration_line.scoped_task_ids`) and the
    composition engine (`bt_composition` via its adapter); lines are `refs/bt/subplan/<project>/<req>/r<rev>/<role>/<SP>`
    from the run line's pinned base, merged by CAS; a gate task starts on the engine's candidate when its members are
    complete. Durable composition ids/refs/store are namespaced (`<req>.bt-r<rev>`). Not ported: publishing a
    composition with an M6 proof bound to the candidate's exact tree (the gate passes when its task is accepted on a
    snapshot built on the candidate).
  - Briefs are built by the legacy `owner_notes`/`contract_notes` (shared, so the runtimes cannot drift); the durable
    verifier writes the same `RUN.notes` history/verify notes. Legacy fix: its design contract notes were dropped.
  - Manual checks: M6 gets the run's `bt_attestation` lookup; a missing receipt is a `MANUAL_EVIDENCE_REQUIRED` owner
    decision with `reverify` (same snapshot, no agent), `bt-durable attest` seals and answers it.
  - Pause gates retries in running task workflows.
  - Every workflow-body plan read goes through the `bt.plan_text` step (`steps.workflow_plan`): the per-process cache
    made a recovered run skip its first step (`DBOSUnexpectedStepError`) — a latent defect that a restart of the live
    engine could have hit.
  - Each step-sequence change sits behind a patch placed before a plain step: `bt-run-subplans`,
    `bt-task-reconcile-asks-owner`, `bt-task-owner-reverify`, `bt-task-respects-pause`; proven by
    `tests/test_durable_upgrade.py` (previous engine code from git → current code, same database).
- **Alternatives rejected:** rewriting the subplan/composition logic for DBOS (duplicates CONSERVAR logic); one line per
  run with subplans as labels (a member would start on unrelated subplans' work); restarting REQ-021 as a new run
  (loses its recorded history and inherited proofs).
- **Consequences:** + REQ-021 keeps its workflows and gains subplan lines after an operator pins
  `refs/bt/line/pictures/REQ-021/r15/pictures-base` (`fa101a47`); − four patches to deprecate once no workflow can be on
  the old path; − the composition proof is weaker than the legacy one (documented in the README).
- **Evidence:** `test_durable_subplans`, `test_durable_briefs`, `test_durable_attestations`, `test_durable_upgrade`,
  `test_durable_e2e.test_a_paused_run_starts_no_retry_until_it_is_resumed`; REQ-030 `REPORT.md`.

## D-146 — The Designer drafts every subplan with tasks in parallel, not only the one in focus

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-130 (its «Designer only on the focused UI subplan»)
- **Context:** on pictures REQ-021 the owner chose SP-4's direction and opened SP-5, whose tasks were written, but no
  Designer started: the flow only drafted the focused subplan, and `bt_design_drafts.request` allowed one Designer batch
  per requirement, so SP-5..SP-7 would each have waited for the previous design and for the owner's confirmation.
- **Decision:** under collaborative planning the Designer works by itself, in parallel, on the subplan in focus and on
  every other unconfirmed UI subplan that already has tasks (`bt_planning_flow.design_scope`); confirming the skeleton,
  confirming a subplan or moving the focus starts all of them at once (`_design`). A subplan without tasks still waits
  for its focus (there is nothing settled to design yet). The concurrency limit is one Designer batch per subplan, never
  per requirement: requesting, iterating, amending and owner feedback wait only for the same subplan's Designer.
- **Consequences:** + the owner reviews designs as soon as subplans are defined, without waiting one by one;
  − several direction batches can run at once (more quota at the same time); `.planning/designers.paused` still stops
  every automatic run.
- **Source:** owner, 2026-10-29 («¿por qué un Designer tendría que quedar libre? Perfectamente pueden paralelizar …
  quiero que sea el comportamiento normal»).
- **Evidence:** `test_planning_flow` (`test_designer_waits_for_the_skeleton_then_designs_every_subplan_with_tasks`,
  `test_a_subplan_without_tasks_waits_for_its_focus`, `test_designers_of_different_subplans_work_in_parallel`),
  `test_design_amend`, `test_design_directions`; red on `main` `2d354a955`, green on branch `designer-parallel`.

## D-147 — Each subplan has a control block: flow, what waits for the owner, blockers, work, news, decisions

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-130, D-142
- **Context:** the subplan view showed one line («pendiente — para confirmarlo falta …») and a plan-wide feed dominated by
  translation events; run decisions, gate waits, versions to try and open round questions of a subplan lived in other
  tabs, so the owner had to open each one not to miss anything (pictures REQ-021: T94's decision blocked SP-4's T4.1 and
  nothing on SP-4 said so).
- **Decision:** above the subplan tabs a fixed control block (`bt_subplan_status` data, `bt_page_subplan_control`
  render) shows the subplan's flow (Definir, Diseñar, Confirmar, Ejecutar, Probar, Aprobado), «Te toca a ti» with the
  action at hand, «Falta para avanzar» with who resolves each item (Planner, Designer, the owner, the run), «Trabajando
  ahora», the subplan's news (marked «nuevo» since the last visit, remembered by the browser only) and the decisions
  taken (confirmations, chosen direction, answered round questions tagged «SP-n:», verdicts). The subplan list counts
  what waits for the owner per subplan and marks news; the right column follows the open subplan without translation
  events, with «Todo el plan» to see everything. Built directly on the existing components and reviewed live (owner
  choice), no design contract.
- **Consequences:** + one place per subplan to see everything that needs attention; − round questions are tied to a
  subplan only by their «SP-n:» prefix (or a single-subplan coverage), and «nuevo» is per browser.
- **Source:** owner, 2026-10-29 («quiero que este sea el panel de control absoluto … que no me pierda nada»; options
  chosen: fixed block, feed filtered to the subplan, build directly and review live, «nuevo» marks and list counts).
- **Evidence:** `test_subplan_control` (7); Playwright run on a copy of REQ-021 (desktop/phone, dark/light, keyboard,
  «nuevo» across visits, feed switch, action links, no horizontal overflow).

## D-148 — «Ejecutar subplan» is refused on a plan the durable runtime runs, until it can join a later stage

- **Date:** 2026-10-29 · **Status:** Superseded by D-149 before deployment · **Refines:** D-134, D-145
- **Context:** pictures REQ-021 belongs to the durable runtime (`RUN.owner.json` backend `dbos`). «Ejecutar subplan»
  froze a new stage and asked the legacy Scheduler to join it; the legacy owner refuses a durable run, and the durable
  runtime has no stage join, so the stage was approved, nothing ran and the page said «El Scheduler empezó la
  ejecución». The subplan control block (D-147) would have invited the owner to press it for SP-4.
- **Decision:** `bt_stages.run`/`start_or_join` raise `DURABLE_OWNER` before anything is frozen when the run's owner is
  the durable runtime; the button becomes «Ejecutar subplan: aún no disponible en el runtime durable» and the control
  block lists it under «Falta para avanzar» (who: Ejecución) instead of «Te toca a ti».
- **Consequences:** + no false «started» and no orphan stage; − confirmed subplans of a durable run wait until the
  durable runtime can join a later stage into the running run (proposal, needs a `DBOS.patch`-gated change).
- **Source:** found while building D-147 (session 7db4552d).
- **Evidence:** `test_stages.Eligibility.test_a_plan_run_by_the_durable_runtime_is_refused_before_anything_is_frozen`
  (red on `main` d5a5402ed: the stage was attempted), `test_subplan_control`.

## D-149 — A later stage continues a durable run in a new run of the stage's revision

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-134, D-145 · **Supersedes:** D-148
- **Context:** pictures REQ-021 runs on the durable runtime (r15: SP-1, SP-2, SP-14, SP-3); the owner confirmed SP-4 and
  more subplans follow. D-134's join belongs to the legacy Scheduler, which refuses a durable run, and a durable run is
  bound to one frozen revision (line refs, attempt keys, compositions carry `r<N>`), so it could not take a stage.
- **Decision:** «Ejecutar subplan» freezes the stage as before; for a durable owner `bt_stages` calls `bt-durable join`
  (`bt_durable.stage_join`). The run of the new revision continues the current one: its lines are copied (create-only);
  accepted, unchanged tasks are inherited without a step (`LegacyTask.integrated`, only a new run's input can carry it,
  so no running workflow changes its step sequence and no patch is needed); a task with a captured but unaccepted
  snapshot is reconciled; the rest runs; gates compose again. A stage that changes accepted tasks needs confirmation
  (`JOIN_NEEDS_CONFIRM`). With live attempts the run is paused and the engine completes the join when they end
  (`RUN.join.json`). Then the old run's workflows are cancelled, `RUN.owner.json` moves by CAS and the new run starts
  with the old run's settings; `RUN.durable-run.json` moves last.
- **Consequences:** + approved subplans of a durable plan run without re-running accepted work, and operator commits on
  the lines (REQ-021's package.json union on SP-3) are kept; − open owner decisions of the old run end with it (a
  reconciled task asks again if needed); − the old run's history stays under its own revision (the panels follow the
  owner record).
- **Source:** owner, 2026-10-29 («sí»: implement it so SP-4 onward can run).
- **Evidence:** `test_durable_stage_join` (2 e2e: inherit without relaunch, reconcile from the snapshot, a new task on
  the copied line, confirmation for changed accepted work, a join that waits for a live attempt and is completed by the
  engine); `test_stages` (the durable branch never starts the legacy Scheduler); a read-only plan against live REQ-021:
  43 inherit (24 legacy material, 19 durable attempts), T94 reconcile from `19ca9774`, T92 redo, nothing live or redone.

## D-150 — Each subplan's «Ejecución» frames its own Flow; the Flow reads the durable runtime

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-147, D-149
- **Context:** the owner asked to monitor the Flow (module map, messages, each task's route) for one subplan from its
  «Ejecución» tab. The Flow only read the legacy Scheduler stores, so for pictures REQ-021 (durable since r15) it said
  «en pausa, último mensaje hace 15 h» while the durable runtime worked. Found on the way: a stage joined to a run the
  owner had paused (REQ-021 was paused from the web at 08:21) would have started unpaused.
- **Decision:** `bt_flow_durable` turns the run's durable telemetry into flow messages between the same parties (new bus
  store `dbos`, cursor = line, unknown records kept); the live API accepts `subplan:P/REQ/SP` (the subplan's tasks and
  the gate tasks that compose it); `/flow?embed=1` drops the page chrome; the subplan's «Ejecución» frames that Flow
  with `data-persist`, and the Plan tab's live refresh swaps everything around such a child instead of reloading it.
  `LegacyProgress.paused` carries the owner's pause into a joined stage (not the join's own waiting pause).
- **Consequences:** + one subplan's execution is watched where it is planned, for legacy and durable runs alike;
  − the telemetry file is read whole per refresh (small today); − gate tasks of every gate a subplan is in show in its
  Flow, including gates of later stages.
- **Source:** owner, 2026-10-29 («quiero que aquí también pueda monitorear lo de flow, pero para el subplan específico»).
- **Evidence:** `test_subplan_flow` (4), `test_durable_stage_join.test_the_owners_pause_carries_into_the_new_stage`;
  Playwright on a copy of REQ-021: SP-2's frame shows its 8 tasks, its gates and 80 messages, keeps its window across a
  refresh that changed the detail block, no page errors.

## D-151 — The Designer runs on Opus 5.5 high first, GPT-6.1 Terra high as its Codex fallback

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-146
- **Context:** the Designer's choices were Opus 5.5 high and GPT-6.1 Sol high, ranked by quota headroom. Codex was
  running out of quota (codex-1 91 %, codex-2 96 % of the five-hour window), yet the design explorations of pictures
  REQ-021 went to Sol: the Opus account whose five-hour window had just renewed read as «unknown» and lost the ranking.
- **Decision:** the owner orders the Designer (`bt_role_policy.ORDERED_ROLES`): Opus 5.5 high first whenever its
  account is below the high-pressure line and not blocked, the same owner order explicit high complexity already
  had; GPT-6.1 Terra high replaces Sol as the fallback. `gpt-6.1-terra` joins the model catalog (Codex, rank 1, quota
  weight 4, estimated). The Codex Designer profile (`agents/designer.md`) names Terra.
- **Consequences:** + designs stop spending the scarce Codex quota while Opus has room; + the owner's preference holds
  even when a renewed window reads as unknown; − Terra's quota weight is a guess until telemetry measures it;
  − ranking by headroom no longer applies to the Designer (only to unordered roles).
- **Source:** owner, 2026-10-29 («codex se está quedando sin cuota… cambiemos los modelos diseñador de sol 6.1 a terra
  6.1 alto y de preferencia opus 5.5, hagamos que los diseñadores actuales corran con opus»).
- **Evidence:** `test_role_routing` (ordered Designer picks Opus over a headroom-richer Codex), `test_role_policy`,
  `test_scheduler_decision_sources`, `test_agent_skills_static`; live ranking: claude opus high (claude-luis) first,
  then codex gpt-6.1-terra high.

## D-152 — A sandbox check that names a host path is refused at approval

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-134
- **Context:** pictures REQ-021 T4.1 (copy the approved `proyectos@v1` contract into the repository) was verified with
  `cmp -- design/contracts/proyectos@v1.md /home/david/bitacora/…/design/proyectos@v1.md`. The verifier runs checks
  in a sandbox holding only a copy of the repository, so the check failed on every attempt although the copy was
  byte-identical: three attempts on GPT-6 Luna, a coordinated repair, then decision `T4.1:d1` for a person. T3.4 carries
  the same pattern (inherited, accepted under the legacy runtime).
- **Decision:** `bt_planner.command_checks.host_paths` finds sandbox command checks naming `~` or a path under `/home`,
  `/root`, `/Users`, `/mnt` or `/media` (also as `--flag=` or `NAME=` values). The contract reports them as warnings
  (`plan-json check`, the Planner's stage readiness); stage approval and whole-plan approval refuse a new or changed
  one with `PLAN_CHECK_HOST_PATH`. A check frozen exactly so in the latest revision was approved before this gate and
  is not re-gated. For REQ-021 the owner approved r17 = r16 with only T4.1's check replaced by a sha256 pin of the
  approved contract (`node -e`, runs in the sandbox, still byte-for-byte), frozen with `freeze_revision` (spliced into
  the draft) and joined into the durable run.
- **Consequences:** + the Planner learns while writing, the owner's «Ejecutar subplan» refuses before a run can stall;
  − the list of host roots is a heuristic (a system path the sandbox does not mount still passes); − a check that
  reads the bitácora on purpose must pin content instead.
- **Source:** owner, 2026-10-29 (approved «r17 con huella sha256»); the gate follows the self-improvement rule
  (reproducible defect).
- **Evidence:** `test_plan_host_path_gate` (7); live REQ-021: the draft's only host path is T3.4 (warned, not gated),
  r16 judged as new is refused for T3.4 and T4.1; `join` r16→r17 inherit 45 / redo 11, T4.1 completed on its first
  r17 attempt.

## D-153 — A direction's motion claim holds when the element or a descendant declares motion, or it moved by script

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-146
- **Context:** pictures REQ-021 SP-6 (`gasto-ia@v1`): the owner could only choose direction B. The comparison reported
  A's `.group-marker` and C's `.band-toggle` as traits their mockups do not show, so `choosable` hid their buttons. Both
  move: A's marker is scaled in by Framer Motion on mount and on every grouping change, C's toggle carries its motion on
  its chevron child (`.band-toggle svg { transition: transform }`) and in `whileTap`. The probe read only the element's
  own computed transition and the animations running at that instant.
- **Decision:** `compare_directions.py` installs an init script that records every element animated through WAAPI, a
  transition or CSS animation event, or a style change while the page is measured; a motion claim holds when the
  element or a descendant declares motion or moved. The stored comparisons of REQ-021's pending designs were recomputed
  (backup of `drafts.json` in the session scratchpad): SP-6 A, B and C choosable; SP-7 and SP-12 keep A unavailable
  (`.count-total`/`.summary-total`, `.loading-scan`), B and C choosable. Those three show only in one state of the
  mockup's `#state` select (counter result, calculator totals, loading), which the probe never changed: it now measures
  every view as it opens, then every view in every state (`fea1c3d12`). Recomputed again: SP-7's iteration r2 (direction
  A, the owner's left tool bar) and SP-12 A, B, C choosable.
- **Consequences:** + a direction is no longer hidden for motion the probe could not see; − a motion selector on a
  large container passes when any descendant declares a transition (weaker than before for such claims).
- **Source:** owner, 2026-10-29 («estoy en sp6 quiero elegir la dirección … pero no veo botón»).
- **Evidence:** `test_compare_motion_evidence` (child transition and finished script animation pass, a still element
  fails; fails on the previous tool), `test_design_directions`, `test_design_drafts`; live: SP-6 shows three «Elegir esta
  dirección» buttons and «Direcciones distintas: comprobado». Integrated before its full regression to unblock the owner;
  the full regression runs with D-154.

## D-154 — Agents of a durable run receive the owner's test variables; cache reads count a tenth of the token budget

- **Date:** 2026-10-29 · **Status:** Accepted; the cache weighting corrected by D-157 (it never applied live) · **Refines:** REQ-030 (durable runtime)
- **Context:** pictures REQ-021 T4.2 stopped for a person after one attempt: «the task used its token budget», checks
  failed. Two causes that also stopped T3.12, T14.4 (twice) and T94. (1) The agent wrote a Postgres test it could not
  run: the verifier receives `PICTURES_REQ021_DATABASE_URL` from the owner's secret files (`verifier.secret_files`), an
  agent receives only the engine's environment, by design (no real credentials for agents); so a mismatch between the
  agent's own test and code (`DOCUMENTO_INVALIDO` expected, `PIEZA_INVALIDA` thrown) reached the verifier. Only T94/T92
  had a database, through an operator note. (2) The attempt reported 12.36 M input tokens, 12.16 M of them Codex cache
  reads, plus 59 k output; the budget (8 M per task) summed them all, so one long Codex session used it whole and the
  engine escalated instead of retrying. Claude reports cache reads apart, so only Codex attempts were hit, and all 52
  durable REQ-021 attempts ran on GPT-6 Luna (the engine's `execution.routes`).
- **Decision:** `execution.agent_env_file` (default `~/.config/metodologia/agent-{project}.env`) is a dotenv file the
  owner keeps with TEST values only; every agent of the project's durable runs receives its variables and its brief names
  them (never the values). For pictures it holds the disposable container `req021-visual-audit-pg` (loopback, random
  password), never the owner's own databases or secrets. `budget_tokens` counts cached input a tenth. T4.2 was answered
  `retry_with_note` (restore a1 from `daa50bdd`, make code and test agree, run the test with the disposable database).
- **Consequences:** + agents run their database checks before finishing; + a long Codex session no longer exhausts its
  task's budget by re-reading its cache; − the container was started with `--rm` and has no restart policy: a reboot
  removes it and the file's URL stops working until it is recreated (the owner's list keeps its removal as his call);
  − the legacy runtime's agents do not read the file.
- **Source:** owner, 2026-10-29 («las dos cosas y además investigar por qué no tenía acceso a la base de datos, dárselo
  y que no pase de nuevo»).
- **Evidence:** `test_durable_agent_env` (4); full regression with D-153 running; telemetry and the attempt's
  `output.log` usage line.

## D-155 — A stage that needs subplans not run yet waits for their approval; the Planner follows quota

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-134, D-149
- **Context:** pictures REQ-021. (1) «Ejecutar SP-8» was refused with plan errors about SP-7's tasks and composition
  gates: SP-8 needs SP-7, which had not run (its design was being finalized); the owner wants to press it now and have
  SP-8 wait until SP-7 has run and he approved it. (2) «Ejecutar SP-6» was refused for `PLAN_CHECKS_UNMAPPED` (the
  owner's `planner.require_mapped_checks`), which the stage readiness the Planner reads never showed
  (`allow_unmapped=True`). (3) The Planner ran on a fixed account, `~/.claude-work`, which hit its weekly limit at 12:05;
  five notices from the web were answered «You've hit your weekly limit» and lost, so SP-9..SP-13 got no `## Pruebas`
  rows and the owner was asked for them.
- **Decision:** `bt_stage_queue`: a stage whose gate passes only with earlier subplans not run yet is queued in
  `.planning/stage-queue.json` (an unconfirmed subplan is still refused) and runs when the owner approves, in «Probar»,
  every subplan it waits for (`bt_verification.decide` drains the queue); one that still cannot run stays with its
  error. Stage readiness applies the mapping gate the button applies. `bt_agent_terminal.planner_account` starts the
  Planner on the Claude account the router ranks first for the planner role (the owner's override still wins), copying
  its conversation there; a notice that finds it out of quota starts it again on another account and tells it on start.
  Operator actions the same day: SP-6's seven summary checks split into one check per criterion with the same command
  (`keep_confirmed` re-pinned the owner's confirmation); the Planner restarted on claude-luis with the missing tests as
  its first job.
  The Planner only runs where it can run unattended (`planner_route`): Claude accounts whose settings accept
  bypass-permissions mode (`skipDangerousModePermissionPrompt`, set only by the owner: claude-work and the default
  account have it, claude-luis does not), else the first Codex route of the ranking (the owner's Codex homes never ask),
  starting from `planning resume`; a notice that finds it on an owner-only prompt tells the owner where instead of
  typing into it. Live at 12:53 the Planner moved to codex-luis `gpt-6.1-sol` high.
- **Consequences:** + the owner can order stages ahead; + the Planner no longer dies silently with its account nor
  waits on a prompt only the owner answers; − on Codex it starts a new conversation from its saved notes (its Claude
  conversation stays on record and resumes when a Claude account can run it).
- **Source:** owner, 2026-10-29 («me gustaría poder ejecutar sp8 pero que espere la ejecución y aprobación de sp7»;
  «de SP-9 para arriba faltan pruebas, eso debería hacerse automáticamente»).
- **Evidence:** `test_stage_queue` (6), `test_planner_account` (4); live: `stage_problem` for [SP-8] refused, for
  [SP-7, SP-8] OK; `planner_account` → claude-luis, avoiding it → claude-work.

## D-156 — «Probar» sees the subplan versions a durable run published; the engine announces them

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-131, D-155
- **Context:** checking that SP-8's queue (D-155) could ever drain: in pictures REQ-021, SP-1, SP-2, SP-14 and SP-3
  were complete and their versions published by the durable composer (`publish_subplan_version`, stores under
  `.state/durable/composition/`), yet «Probar» showed only SP-1 (from the legacy projection) and the rest «se está
  construyendo». `bt_verification` read only `RUN.projection.json`, which the legacy Scheduler writes and the durable
  runtime never does (last written 2026-10-28 17:13, before the migration). No subplan of a durable run could be
  approved, so a stage queued behind one would have waited forever, and the owner was never told a subplan was ready.
- **Decision:** `bt_verification.durable_versions` reads the durable composition stores (one per approved revision)
  when `RUN.owner.json` gives the run to the durable runtime; a version is a change of the subplan's commit over time
  (a stage join re-publishing the same tree keeps the owner's decision, a new commit outdates it). The engine projector
  calls `on_projection` after each projection, as the legacy Scheduler does (desktop notice and feed line «SPx terminó
  y está listo para probar»).
- **Consequences:** + D-131's owner verification works on durable runs; + SP-8 runs when SP-7 is approved;
  − version numbers differ from the composer's per-revision numbers (they count distinct commits).
- **Source:** operator, 2026-10-29, while verifying the owner's request «que espere la ejecución y aprobación de sp7».
- **Evidence:** `test_durable_verification` (4); live read: SP-1 v1, SP-2 v1, SP-14 v1, SP-3 v2 (`8ac04102`, the owner's
  conflict resolution) «por probar»; their commits are in `~/dev/pictures`, so «Probar» can open them.

## D-157 — The verifier's sandbox runs Python checks with uv; Codex cache reads really count a tenth

- **Date:** 2026-10-29 · **Status:** Accepted · **Corrects:** D-154 · **Refines:** REQ-030 (M6 sandbox)
- **Context:** pictures REQ-021 T6.3 stopped for a person after one attempt. (1) Its check, `npm run
  gasto:test-captura`, ends with `uv run --frozen --directory services/ai-api --extra test pytest`; the verifier's
  sandbox showed only Node and the Playwright cache, so «uv: command not found» (exit 127, BLOCKED_EXTERNAL) while the
  TypeScript half passed 4/4. No earlier REQ-021 check had used uv. (2) The stop read «the task used its token budget»
  although D-154 weighted cache reads: the Codex driver hands the engine `input_tokens`, `cache_read_tokens` and a
  `total_tokens` that counts the cache in full; `budget_tokens` took that total and looked for `cached_input_tokens`,
  and its test used the raw Codex names, so the weighting never applied (T6.3: 23.94 M counted, 2.76 M meant).
- **Decision:** the sandbox toolchain shows uv and the Pythons it manages (`UV_CACHE_DIR` throwaway in /tmp, no Python
  downloads); a package root with `pyproject.toml` gets its `.venv` like `node_modules` (the attempt's own, else the
  repository's when `uv.lock` is byte-identical; `pyvenv.cfg` marks a finished install), as a throwaway overlay in the
  workspace and read-only at its own path, which its scripts' shebangs name. `budget_tokens` uses the driver's split
  by provider (Codex input includes its cache reads, Claude's does not), the total only without a split.
- **Consequences:** + Python checks run where Node checks already did; + long Codex sessions no longer exhaust their
  task's budget; − a uv check whose project is installed editable rebuilds it in the overlay each run (a second);
  − with `verifier.network` off a rebuild that needs a build backend fails.
- **Source:** the owner's standing order (2026-10-29): every blocked task is a system defect to fix at its source.
- **Evidence:** `test_verifier_python_toolchain` (8, one in the real sandbox), `test_durable_agent_env` (budget, driver
  shape); a bwrap emulation of the new mounts on T6.3's tree: uv rebuilt the editable project and pytest passed (3).
  Live: integrated `0b9f36248` (regression 282 files, 4 baseline; DBOS backup `bt_durable-20261029-142224.dump`);
  the owner's `reverify` of T6.3 re-ran its checks on the same snapshot and it completed, no new agent attempt.

## D-158 — «Probar esta versión» starts a version's test servers and opens it in a new tab

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-131, D-156
- **Context:** the owner pressed «Abrir esta versión en local» for pictures REQ-021 SP-1 «at least to see nothing
  explodes» and nothing opened: the button only made a detached copy of the version's commit; preparing it, starting
  its servers (pictures: Next web plus the Python ai-api) and finding the port were left to him. A server an earlier
  session started by hand in that copy (port 3000, no database) still ran, and Next refuses a second dev server in the
  same folder. Owner: «quiero que cuando le doy click me arranque el servidor o servidores de pruebas y que se me abra
  el navegador con la versión en específico».
- **Decision:** `bt_verify_servers` reads a per-project recipe kept by the owner (`<bitácora>/<project>/
  verify-servers.json`: env file, env with `{port:x}` and `${SECRET}` filled from the owner's secret files at start,
  prepare steps, servers with port, ready path and open path), picks free ports, writes a 0600 env next to the copy and
  runs prepare plus every server in one tmux session. «Probar esta versión ↗» posts into a new tab whose page polls the
  servers and replaces itself with the version's URL when all answer; a server that died is reported with its output.
  Servers left listening inside the copy are stopped first (never a process that does not listen); «Detener
  servidores» and «Cerrar la copia» stop them. A missing secret starts nothing. pictures' recipe: the owner's
  `.env.local` with `DATABASE_URL` switched to the REQ-021 test database, the web pointed at the version's own ai-api,
  prepare = `npm ci` when missing, workspace builds, `rag:migrate` (on the test database).
- **Consequences:** + one click from «Probar» to the running version; + versions run side by side on free ports;
  − the recipe names one requirement's test database (pictures REQ-021); − migrations of different versions accumulate
  in the shared test database.
- **Source:** owner, 2026-10-29 (quoted above).
- **Evidence:** `test_verify_servers` (10, one with real processes); live on SP-1: prepare, 36 migrations on
  `req021@127.0.0.1:55433`, ai-api 8001 and web 3000 answered, `/`, `/3d`, `/login` 200.

## D-159 — An audit's brief keeps its screenshots and logs outside the repository

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** REQ-030 (audit gate)
- **Context:** pictures REQ-021 T5.5 (SP-5 visual audit) saved 16 captures next to its report inside the repository;
  the audit gate rejected it for files it did not declare and it audited again, as T2.7 had for SP-2. Nothing told an
  auditor where evidence goes.
- **Decision:** every audit task's notes (`owner_notes`, both runtimes) add: inside the repository only the report and
  the ledger; screenshots, captures and logs in `<requirement>/evidence/<task>/` (absolute path), cited from the report.
- **Consequences:** + no audit pass wasted on undeclared evidence; + captures stay out of the product repository.
- **Source:** the owner's standing order to fix recurring defects at their source.
- **Evidence:** `test_audit_evidence_brief` (2); regression 284 files, 4 baseline; integrated `815ec6a87` with a DBOS
  backup `bt_durable-20261029-151400.dump`.

## D-160 — Compositions fold a member's own work, merge package.json by key and reuse resolved conflicts

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-149, REQ-030 (composition)
- **Context:** pictures REQ-021 r19 settled `blocked` with CG-3, CG-5 and CG-6 rejected (`git_text_conflict` in
  package.json, mapa-rutas.ts, servicio.ts, dependientes.ts) and no decision for the owner. Three causes: (1) SP-4's line,
  built at the r16 stage join, carries its prerequisites as integrations of other subplans' work (79 commits), not as their
  published tips; its delta from its merge base with SP-3 re-applied copies of SP-1, SP-2 and SP-14. (2) Every subplan
  appends npm scripts at the end of `package.json` (SP-3 had needed the owner's hand). (3) SP-4 and SP-5 both edited the
  one-line `TABLAS_TRABAJO_CUENTA` (a genuine conflict). And nothing told the owner the run had stopped.
- **Decision:** the durable composer folds a member from where its own task snapshots start on its line
  (`_own_work_base`), only when every accepted snapshot of it lies there (lines older than the durable runtime keep the
  merge-base rule); the git port merges a conflicted `package.json` by key (`merge_json`, a clash only when both changed a
  value differently) and keeps genuine conflicts' context in `<store>/resolutions/<key>.diff3|.json`, reusing a
  `<key>.resolved` written once for every gate that composes the same three versions; the engine projector notifies the
  owner once when a run settles blocked by rejected gates.
- **Consequences:** + stage-joined subplans compose; + npm-script appends never conflict; + a genuine conflict is
  resolved once; − a resolution is keyed by blob contents: a member that changes the file asks again (as it should).
- **Source:** the owner's standing order: every blocked task is a system defect to fix at its source.
- **Evidence:** `test_compose_conflicts` (6, real git repositories); dry run on r19's refs: with the old rule SP-4
  conflicts in 3 files, with the new rules SP-1..SP-5 fold cleanly up to SP-5's genuine conflict, and with one recorded
  resolution (the union of both table lists, SP-4's tables use `account_id` as SP-5's `columnaCuenta` assumes) SP-1..SP-6
  compose.

## D-161 — Confirming a subplan on the web also sends it to run; the subplan list keeps its scroll

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-134, D-147, D-155
- **Context:** the owner asked (pictures REQ-021, 2026-10-29) that «Confirmar subplan» put the subplan in the execution
  queue without a second click on «Ejecutar subplan», and reported that approving a subplan sent the subplan list on the
  left back to its top. The list scrolls on its own (`planning.css`); the reload after any form, and every live swap of
  the list block (its badges and run chips change every few seconds during a run), replaced it with a copy at scroll 0.
  While checking, SP-8's entry in `.planning/stage-queue.json` was found stale: the owner had run SP-7 and SP-8 from
  their buttons (stages r20, r21), and approving SP-7 in «Probar» would have approved a second, identical stage.
- **Decision:** the web button becomes «Confirmar y ejecutar»: a successful confirmation runs `bt_stages.run` for that
  subplan (it runs now, or waits in the queue for the earlier subplans it needs), loopback only like «Ejecutar subplan»,
  and leaves alone a subplan already in the approved stage or the queue. A queued subplan shows «En cola · espera SP-n»
  and a blocker instead of asking to be run. A stage approval or a drain drops queue entries the approved stage already
  holds (`bt_stage_queue.settle`). `planning-live.js` keeps the list's scroll across live swaps and in-place
  navigation, saves it on `pagehide` with the open subplan and restores it after a form's reload (again on `load`, when
  fonts grow the list); arriving on another subplan brings it into sight.
- **Consequences:** + one click from confirmation to execution; + the list stays where the owner left it; − a
  confirmation in the chat (`planning confirm`) still needs «Ejecutar subplan» or `stage run`.
- **Source:** owner request, 2026-10-29.
- **Evidence:** `test_subplan_control` (3 new), `test_stage_queue` (1 new); headless Chromium on a copy of REQ-021:
  main loses the list position on reload (1089 → 0) and on a live swap (260 → 0); the branch keeps 1089 and 260 and
  brings SP-12 into sight on arrival.

## D-162 — Directions awaiting the owner survive plan changes; delegations get 120 turns

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-151, the Designer directions flow
- **Context:** pictures REQ-021 SP-12 had three directions ready for the owner's choice since 10:59. At 15:40 the
  Planner appended one engineering sentence (an integration-test script) to UI task T12.3's objective; the UI brief's
  digest changed, `bt_design_follow.sync` released the pending choice and started three new explorations. They were the
  first explorations on Claude Opus (D-151), and delegations ran Claude with its default `--max-turns 45`: two of the
  three stopped at 45 turns with the mockup written and no note or comparison JSON ($4 each), leaving one direction.
- **Decision:** an exploration awaiting the owner's choice is never redone by `sync` or by a focus/parallel request
  after a plan change; only an explicit request (`force`/`fresh`: «Rehacer diseño», `design draft --force`) redoes it.
  Choosing a direction drawn before the change folds the mechanical brief diff into the finalise brief and records the
  current brief (`<ref>.r<n>.chosen.behavior.md`). The panel says the directions predate the change and can still be
  chosen. An iteration of an already chosen direction keeps its amend path. Claude delegations take
  `delegate.max_turns` (120, as `scheduler.max_turns`).
- **Consequences:** + a plan edit no longer throws away the owner's options nor spends three Designer runs; + Opus
  Designers can finish; − a large plan change keeps the old directions until the owner asks for new ones.
- **Source:** the owner's question about SP-12 (2026-10-29) and the standing order to fix blocked work at its source.
- **Evidence:** `test_design_directions` (2 new, replacing the old stale-refusal test), `test_harness_controls` (1 new);
  SP-12 delegations D-20261029-154139-9e2d and -34c4 ended `error_max_turns` at 46 turns, -6d7c completed.

## D-163 — A refused bitácora commit unstages and says why

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** the bitácora commit (`bt_vcs.commit`)
- **Context:** from 13:46 the repository's pre-commit hook (gitleaks) refused every bitácora commit on a false positive
  in pictures REQ-021's `.translations/cache.json` (a SHA-256 key next to text mentioning an API). `_commit_locked`
  returned False with the files still staged; `bitacora.py commit` printed «nothing to commit», nothing was committed or
  pushed for hours, and the staged live state made a later `git merge --no-ff` in that checkout abort with a reset.
- **Decision:** when `git commit` fails, the bitácora commit unstages what it staged; when the hook's output is a
  gitleaks refusal it writes the redacted report to `.state/secret-alert.txt`, which the SessionStart and Stop hooks and
  `bitacora.py commit` already surface. How to treat the false positive itself (a path allowlist mirroring
  `bt_secrets.GENERATED`, or one more fingerprint) is the owner's decision: an allowlist was refused by the permission
  classifier as a security weakening.
- **Consequences:** + a refused commit is visible at once and never leaves the live index dirty; − until the owner
  decides on the false positive, bitácora commits stay refused (the files are safe on disk).
- **Source:** the owner's standing order to fix blocked work at its source.
- **Evidence:** `test_bitacora_commit_refused` (2, a real repository with a refusing hook).

## D-164 — Subplan lines settle conflicts like the composer

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-160, REQ-030 (integration lines)
- **Context:** pictures REQ-021 r24: once CG-3 composed (D-160), its gate task T93 passed its own checks but was rejected
  with `INTEGRATION_CONFLICT: package.json (line of SP-11)`. A gate task is integrated into every subplan line whose
  scope holds it, and `GitLineIntegrator._merge` used a plain `git merge-tree`: the npm scripts each subplan appends,
  which the composer now merges by key, conflicted again on the lines. The second attempt started from the same
  candidate and would have conflicted the same way.
- **Decision:** when `git merge-tree` reports conflicts on a line (run line, subplan lines, `sync`), the integrator
  settles them with the composer's rules: `package.json` merged by key and the recorded resolutions in
  `<state>/composition/resolutions` (a new genuine conflict leaves its context there, as at a gate). Only with a single
  merge base and a composer; otherwise the conflict stays as git found it.
- **Consequences:** + gate tasks and members integrate where the composer composes; + one place records how a genuine
  conflict is resolved; − a criss-cross history still reports the raw conflict.
- **Source:** the owner's standing order: every blocked task is a system defect to fix at its source.
- **Evidence:** `test_compose_conflicts.LineIntegration` (2, real git): a line holding script `b` takes a gate snapshot
  adding `c` without a conflict; without a composer the conflict is reported as before. Live: T93 a1 telemetry
  `recovery_decision INTEGRATION_CONFLICT`, its a2 prompt «conflicts with accepted work in: package.json (line of SP-11)».

## D-165 — Dependencies are typed when the plan is written

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** plan contract interfaces (schema 1.2.0/1.3.0), Planner role
- **Context:** pictures REQ-021 T7.4 (SP-7 checkpoint) asserted that every counter call lands in the usage ledger under
  its tool tag. That behaviour is wired and proven in SP-6 (capture T6.3, end-to-end test T6.5, interface IF-3 owned by
  SP-6), but T7.4 depended only on T6.2, the table's producer, and was not an IF-3 consumer. SP-7's line never held the
  capture; four attempts failed (`needs_decision T7.4:d1`). Its checkpoint also started `next dev` without the Python
  backend. The owner: «si una tarea depende de otra debe estar tipificado desde el principio y que se trabaje en
  consecuencia».
- **Decision:** the validator refuses an interface consumer outside the interface's `owner` subplan that does not depend
  on the interface's `integration_task` (or a gate after it), unless that integration task is a composition gate task;
  the producer alone proves only the contract. The Planner reviews, task by task before each subplan's confirmation, what
  its acceptance and checks rely on without building it, types each reliance in `after` or as an interface consumer,
  says which servers a check starts and how, and records the review in a planning note. For REQ-021 the Planner revises
  T7.4 (depends on CG-6's T96, consumes IF-3, its checkpoint starts the local ai-api with a shared HMAC secret and
  deterministic providers) and reviews SP-7..SP-13 for the same pattern.
- **Consequences:** + a cross-subplan reliance is visible and scheduled before any attempt; − semantic reliance inside
  free text still depends on the Planner's review: the validator enforces what is declared.
- **Source:** owner request, 2026-10-29 16:40.
- **Evidence:** `bt_planner/tests/test_interfaces.py` (2 new); the live REQ-021 plan passes unchanged; T96's ancestors
  include T6.3 and T6.5.

## D-166 — Reconfirming a running subplan approves its stage again

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-161
- **Context:** after D-165 the Planner typed T7.4's dependency on CG-6 and fixed SP-8/SP-9 dependencies; SP-7, SP-8 and
  SP-9 already run in stage r24 and need the owner's re-confirmation. D-161's «Confirmar y ejecutar» left a subplan of
  the approved stage alone («ya está en ejecución»), so a re-confirmed change would never reach the run.
- **Decision:** when the owner confirms on the web a subplan that is already in the approved stage (it changed), the
  stage is approved again with it and the run joins the new revision; while other changed subplans of the stage wait
  for confirmation, the message says so instead of an error. «Ejecutar subplan» on a running subplan still does nothing.
- **Consequences:** + a re-confirmed change reaches the run in one click; − each re-confirmation is a stage revision
  and a join (accepted unchanged work is inherited).
- **Source:** the owner's REQ-021 re-confirmation of SP-7..SP-9, 2026-10-29.
- **Evidence:** `test_subplan_control.test_reconfirming_a_running_subplan_approves_the_stage_again`.

## D-167 — The durable engine heals its runs' decisions

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** REQ-029 R3/R4 (model step), REQ-030 (durable runtime)
- **Context:** the owner: failures of an agent's work and of the environment should be solved by the system on its own;
  plan and system defects at least detected and routed. The legacy Scheduler's self-healing answers a stop with the
  diagnosing model's `retry`/`retry_with_note` (`healing.model_diagnosis`, which the owner had switched on), but the
  durable runtime that runs pictures REQ-021 never got it: T4.2, T7.4 and T93 each waited in `needs_decision` for the
  operator.
- **Decision:** `bt_durable/healing.py`, called from the engine's maintenance pass (`service._heal_decisions`, every
  30 s): for each open decision offering `retry`/`retry_with_note`, a background diagnosis by `bt_block_agent`
  (`diagnosis.*`) reads the failure, the task, its dependencies and its attempts; a later pass sends the validated choice
  to that exact round as `by: healing` — once per failure signature and task, within `healing.max_per_task` and
  `healing.max_actions`, never when the model is unsure. A diagnosis of kind `plan` goes to the run's Planner with its
  evidence and the decision stays for the owner. Every step is recorded in the activity feed as «Autocuración». Outside
  the workflows: bt.run/bt.task keep their sequence, so no `DBOS.patch` is needed.
- **Consequences:** + retries with a concrete note happen in seconds instead of waiting for a person; + plan defects
  reach the Planner with evidence; − the diagnosing model (`diagnosis.profile`/`model`) spends tokens on every decision
  and can be wrong: one try per signature, then the owner.
- **Source:** owner, 2026-10-29 («sí» to porting the self-healing to the durable engine).
- **Evidence:** `test_healing_durable_decisions` (3).

## D-168 — Task sessions never do the bitácora's chores

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-163, the bitácora hooks
- **Context:** after D-163 made a refused bitácora commit raise the secret alert, pictures REQ-021 T93's durable attempt
  (Codex, gate CG-3) finished its task, met the alert in the bitácora Stop hook, added a gitleaks fingerprint to
  `bitacora/.gitleaksignore` and committed it (`042a31ca`, «fix: remove secret») on the local `main` of
  `~/dev/metodologia`, outside its worktree and its task. Durable attempts carried no marker the hooks could see
  (only `BITACORA_ROOT`), so their Stop hook also asked them for day-log updates.
- **Decision:** durable attempts get `BITACORA_ATTEMPT=<attempt key>`; the Stop hook returns at once for them, and the
  secret alert (SessionStart warning and Stop block) is shown only to sessions that are not system runs
  (`BITACORA_ATTEMPT`, `BITACORA_TASK`, `BITACORA_DELEGATION`).
- **Consequences:** + task agents answer to their task and their verifier only; − none known: the operator and owner
  sessions still see the alert.
- **Source:** the operator's finding while answering the owner about T7.4, 2026-10-29 17:05.
- **Evidence:** `test_hooks_system_runs`; T93 a3 `output.log` (item_45 reads `.state/secret-alert.txt`; its final message
  reports commit `042a31ca`). The commit itself (one verified false-positive fingerprint) stays on `main` for the owner.

## D-169 — A criss-cross line merge settles against a virtual base

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-164
- **Context:** pictures REQ-021 r25, gate task T93 (CG-3) blocked with «the integration conflict keeps coming back»
  (`INTEGRATION_CONFLICT`, package.json, line of SP-7, `max_same_signature`). The gate snapshot and SP-7's line had both
  taken SP-3 and SP-4, so `git merge-base --all` gave three bases; D-164's `_settle` merged package.json by key only with
  a single base and otherwise left git's conflict, so every retry met the same conflict. No agent could ever fix it.
- **Decision:** with several merge bases the line integrator first merges them into a virtual base commit, recursively,
  as git's recursive strategy does, using the composer's rules (package.json by key; a conflict left between bases keeps
  git's markers, so that file then conflicts as before). The virtual-base merges record no resolution requests.
- **Consequences:** + gates built on composed candidates integrate into lines that share several members; + a script one
  side removed is not resurrected (a `{}` base would); − a conflict between the bases themselves still reaches the owner.
- **Rule:** a conflict that a retry cannot change (same snapshot lineage, same signature) is a system defect: fix the
  integrator, never ask the agent to retry it.
- **Source:** operator monitoring of REQ-021, 2026-10-29 17:44.
- **Evidence:** `test_compose_conflicts.LineIntegration.test_a_criss_cross_history_settles_against_a_virtual_base` (red
  without the fix); reproduced on pictures: SP-7 tip `043fd6a9` × T93 a2 snapshot `ac842911` settles with all keys kept.

## D-170 — The engine's INFO lines reach its journal

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-167
- **Context:** after integrating D-167 the operator looked for «healing:» in the engine journal and found none, though
  healing had answered pictures REQ-021 T93:d1 (`retry_with_note`, RUN.durable-healing.json, activity «Autocuración»).
  `bt_durable`'s loggers had no handler: their INFO lines («healing: …», «stage join: …», «engine started») fell to
  Python's last-resort handler, which prints WARNING and up only. Only DBOS's own logger was configured.
- **Decision:** `bt-durable engine` attaches one stderr handler to the `bt_durable` logger at INFO (DBOS-like format,
  no propagation), idempotently.
- **Rule:** what the engine decides on its own (healing, joins, future solver) must be visible in its journal.
- **Source:** operator verification of the D-167 deploy, 2026-10-29 18:18.
- **Evidence:** `test_durable_engine_log`; journal of bt-durable.service on 2026-10-29 shows no `bt_durable` INFO line.

## D-171 — A verification cut short by an engine restart runs again once

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** REQ-030 (durable M6 port)
- **Context:** the 18:44 restart that deployed D-170 killed pictures REQ-021 T95's running verification. DBOS re-ran the
  verify step; M6's request row was still `running`, so `QualityEngine.verify` raised `REQUEST_IN_PROGRESS` and the task
  opened T95:d1 as a runtime defect for the owner. The legacy owner recovers such rows on start
  (`recover_interrupted` + `retry_interrupted`, once per request); the durable M6 port never did. Every engine deploy
  during a verification would block a task.
- **Decision:** `operator_verifier` (engine start, the store's only user) records each `running` request as interrupted
  (ENGINE_INTERRUPTED, no check replayed) and queues it again once; `QualityEngine.verify` claims a `queued` request
  (the claim is atomic). A second interruption of the same request stays a review for the owner.
- **Rule:** an engine restart must never turn in-flight work into a decision; every durable step that holds external
  state needs its restart path tested.
- **Source:** operator monitoring of REQ-021, 2026-10-29 18:45 (T95:d1 answered `reverify` to unblock it at once).
- **Evidence:** `test_durable_m6_restart` (4; negative control reproduces REQUEST_IN_PROGRESS).

## D-172 — A conflicting hunk that is one side's change plus additions settles to the larger side

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-160, D-164, D-169
- **Context:** pictures REQ-021 r25, gate T95 (CG-5) a3 passed verification and then met
  `src/lib/cuentas/dependientes.ts (line of SP-8)` at integration. Both sides had the same new
  `TABLAS_TRABAJO_CUENTA` line and SP-8 also appended `anonimizarGastoCuenta` after it; git reports that single hunk as a
  conflict (git's own `merge-tree` too), the composer wrote a resolution request nobody answers in a durable run, and the
  task would retry into the same conflict. The merge bases (three) also disagreed on that line, so D-169's virtual base
  kept markers there.
- **Decision:** after `package.json` (D-160) and before recorded resolutions, `GitSubprocessPort.merge_tree` settles a
  text file whose every conflicting hunk (`git merge-file --diff3`, 31-character markers) is one side's lines plus
  additions in order, taking the larger side there — unless an added non-blank line was in the base of that hunk (that
  would bring back what the other side removed). Anything else stays a conflict. It serves the composer and the lines.
- **Consequences:** + "same change, one side added more" no longer blocks gates; − a true semantic clash expressed as
  pure additions (both sides needed, but in a different order) is not detected by text merging; verification still runs
  on the merged result.
- **Rule:** before a conflict reaches an agent or the owner, ask whether a retry can change it; if not, the merge rules
  are the defect.
- **Source:** operator monitoring of REQ-021, 2026-10-29 19:25.
- **Evidence:** `test_compose_conflicts.SubsumedHunks` (3; inputs confirmed to conflict in plain `git merge-file`); the
  exact blobs of resolution request `3627c792…` settle to SP-8's version.

## D-173 — A gate task starts from its candidate caught up with its lines

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-164, D-172
- **Context:** pictures REQ-021 r25, gate T95 (CG-5). Every attempt (a1..a6) started from the same composition
  candidate, built from the members' *registered versions*; its work is integrated into the members' *current subplan
  lines*, which other tasks kept moving (T93 put a `NODE_ENV` fix on SP-7's line, T8.1/T8.3/T8.6 moved SP-8's). Attempts
  a3 and a5 passed verification and then conflicted at integration (`dependientes.ts` with SP-8; then
  `test-harness-taller-esenciales.ts` with SP-7, the same fix written with the properties in another order). No
  attempt's base held the SP-7 or SP-8 tips, so retries could not converge.
- **Decision:** `base_ref` for a `gate:<CG>` home merges into the candidate the tips of the existing subplan lines the
  task will be integrated into (`subplans.lines_of`), objects only, with the line integrator's merge and the composer's
  settling rules; a line that conflicts is left out (logged) and its conflict still surfaces at integration. Inside the
  `bt.base_ref` step: no change in the order of steps.
- **Consequences:** + the gate agent sees, and resolves in its own work, what the lines gained since composition; its
  integration then fast-forwards or merges cleanly; − a gate attempt now verifies a slightly larger tree than the
  candidate (the lines' newer accepted work), which it must be compatible with anyway.
- **Rule:** a retry must start from a base that contains whatever it will be integrated into; otherwise the retry cannot
  change the outcome.
- **Source:** operator monitoring of REQ-021, 2026-10-29 19:40.
- **Evidence:** `test_compose_conflicts.GateBase` (2; red without the fix); probe on pictures: T95's candidate
  `5d807d5b` takes SP-6, SP-7 and SP-8 tips without a conflict (SP-3..SP-5 already in).

## D-174 — A virtual base uses the recorded resolutions; a resolution serves both sides

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-160, D-169, D-172, D-173
- **Context:** pictures REQ-021 r25 gate T95 (CG-5) failed seven times; healing answered `retry_with_note` each time
  (19:50: «Conflicto de integración con SP-8 en src/lib/cuentas/dependientes.ts»). D-169's virtual base merged the bases
  SP-5 × SP-4 without the composer's recorded resolution `2cac2038…` (recorded as SP-4 × SP-5), so it kept git's markers
  in dependientes.ts and every merge with SP-8's line conflicted. Three resolution requests had sat open for up to 3 h
  (`3a744e91…` 17:06, `3627c792…` 19:09, `3e63cd40…` 19:36): nobody is told about them.
- **Decision:** the virtual base applies recorded resolutions and never writes new requests; a recorded resolution also
  settles the same three versions met with ours and theirs swapped (the final content is the same). The operator wrote
  the three open resolutions (the known union of dependientes.ts; the harness test's two orderings of the same keys).
- **Rule:** a conflict request without an owner is a block: REQ-031's Solucionador gets an «open resolution» trigger.
- **Source:** operator monitoring of REQ-021, 2026-10-29 19:55.
- **Evidence:** `test_compose_conflicts` (11; the two new tests fail without the fix); probe on pictures: SP-8 tip
  `91a8e714` × T95 a5 `bc5510ea` / a6 `f5c855f2` integrate without conflict.

## D-175 — The engine starts a Solucionador for blocks the healing cannot resolve

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-167, D-170, REQ-030 (durable runtime) · **Requirement:** REQ-031
- **Context:** the owner: every blocked task is a system error. On 2026-10-29 every block of pictures REQ-021 that D-167's
  healing could not answer waited for an operator session that found the origin by hand (D-165, D-169, D-171, D-174),
  fixed it, ran the regression, backup, integration and restart, and recorded a rule. Three composition resolution
  requests also sat open for up to 3 h while T95 failed INTEGRATION_CONFLICT on every retry.
- **Decision:** `bt_durable/solver.py`, in the engine's maintenance pass right after healing and outside the workflows,
  starts a full-access session, the Solucionador. Triggers, each once per key: decisions healing left for the owner and
  signatures that came back after its retry (`heal(escalate=...)`); PENDING tasks with no state change for
  `solver.stuck_minutes` beyond their known waits; run workflows in ERROR; composition resolution requests without
  `.resolved` older than `solver.resolution_after_seconds` (`bt_durable/resolutions.py`). One session per run (later
  triggers go to its inbox), `solver.max_concurrent` on the machine, `solver.max_per_task` per task. Claude Opus high,
  bypassing permissions, on the unattended account with quota (`role_route(..., "solver")`; Codex otherwise), in tmux
  `bit-<project>-<REQ>-solver` inside its own systemd scope (so it survives the engine restart it may cause), moved to
  another account on a spent quota. Brief and prompt: `RUN.solver/<id>/`, `agents/solver.md`; closed by `result.json`
  (`fixed|answered|asked_owner|gave_up`), its disappearance or the `solver.max_minutes` watchdog (`gave_up`, owner told).
  It runs only while healing runs. The run panel shows it; its answers carry `by: solver`.
- **Consequences:** + a block no cheaper rung resolves is worked on within one pass; + one place records what was fixed
  and why; − an Opus session per hard block spends quota; − one session per run serialises a trigger storm.
- **Rule:** metodologia is never built or repaired through metodologia's own scheduler, handoff or launch (owner,
  2026-10-29); the Solucionador fixes it in its own worktree and integrates only through `bt_integrate`. A process the
  engine starts that must outlive an engine restart runs outside the engine's cgroup.
- **Source:** owner, 2026-10-29 (REQ-031 interview; «manda a un subagente de opus»); built by an Opus subagent.
- **Evidence:** `test_durable_solver` (10), `test_healing_durable_decisions` (extended), `test_durable_panel`,
  `test_agent_terminal.ScopedStart`, `test_role_routing`; branch regression 294 files, only the 4 baseline failures.

## D-176 — Integrating metodologia is a repo-owned script

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** the operators' manual procedure (REQ-030 pre-deploy.txt)
- **Context:** integrations were done by hand from scratchpad scripts (regress.py, dbos_backup.py); a no-ff merge in the
  live checkout once refused staged bitácora changes and its abort reset them; load flakes (test_platform,
  test_supervisor_limits) needed a judgment call each time; two operator sessions integrated the same afternoon.
- **Decision:** `skill/scripts/bt_regress.py` (full regression; baseline in `integrate.allowed_failures`; any other
  failure rerun alone once) and `skill/scripts/bt_integrate.py` under one machine-wide flock (`<state>/integrate.lock`):
  preflight (live checkout on main, branch committed, no `bitacora/` paths, main's code already in the branch) →
  regression → DBOS backup when runtime code changed + release-log entry → `merge --no-ff` in a deploy worktree →
  `merge --ff-only` in `~/dev/metodologia` + push → restart the units the changed paths need → smoke; a failed smoke
  reverts the merge the same way. Exit codes: 0 integrated, 1 refused, 2 ff refused, 3 reverted, 4 revert failed, 75 busy.
- **Consequences:** + one safe procedure for operators and the Solucionador; + integrations never race; − the lock is held
  through the ~30 min regression.
- **Rule:** the live checkout only ever sees `merge --ff-only` and `push`; operators integrate through `bt_integrate`.
- **Source:** REQ-031 T1; operator procedure of 2026-10-29.
- **Evidence:** `test_integrate` (11, real temporary git repositories); first live use: the Solucionador's own integration.

## D-177 — A known-failing suite is fixed at its origin, never allowlisted

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-176
- **Context:** every full regression tolerated four failing suites (`integrate.allowed_failures`), each a real defect:
  `bt_planner.interfaces.check()` crashed (TypeError) on a malformed schema-1.3 id instead of reporting it; since
  89e2c76ed `bt_review_policy`/`bt_verifier_env` imported `bt_planner` past its adapter; the real designer kit kept its
  entrance springs running under reduced motion (`useReveal` gave Motion the same target) and its test checked a shared
  prebuilt dist from 2026-10-26, not the checkout; `test_recovery_views` read a route that had moved to
  `bt_server_plans` (the token check is still first); the remote panel never listed the `/components` gallery (404).
- **Decision:** each fixed where it lives (commits 0bea559a1, 2f5d89c96, 3aa734b08, e574ad3d0, 411d01cdd);
  `bt_regress.BASELINE = ()` and `integrate.allowed_failures` defaults to `[]` (55e017e1d). A rendered-UI test builds
  what it checks from the checkout.
- **Rule:** an entry in the allowlist needs an owner-accepted reason and a date; a red suite is a defect.
- **Source:** owner's goal, 2026-10-29 21:00 («no te limites a parchear… arreglar el origen»); fixed by an Opus subagent.
- **Evidence:** branch `fix-baseline` regression 294 files, no failures (two bt_durable load flakes passing alone, sent
  to the Metamorfosis audit).

## D-178 — Process teardown and observation are ordered

- **Date:** 2026-10-29 · **Status:** Accepted
- **Context:** `test_platform` and `test_supervisor_limits` failed under load (load «flakes» called judgment calls in
  D-171..D-176's integrations). Both were product races: `bt_runsession.kill_tree` returned after reaping the leader
  while SIGKILLed group members still existed; `bt_supervisor/pgroup.observe()` listed live processes before reading
  `exit.json`, so an attempt the reaper had just ended came back «exited» with a dead pid in `live_pids`.
- **Decision:** `kill_tree` returns only when `killpg` reports the group gone (≤10 s, resending SIGKILL); `observe()`
  samples processes after deciding the state, as the systemd backend does (34f3e5d3f, 440c5e168).
- **Rule:** a load flake is a race to find, never a rerun to accept.
- **Evidence:** 10× parallel with 32 CPU hogs: baseline 2/10 and 1/10 failed; fixed 0/20 and 0/30.

## D-179 — A successful integration removes its clean worktree

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-176
- **Context:** on 2026-10-29 the operator removed 14 clean, merged worktrees and 64 merged branches left by two days of
  integrations; `~/dev/metodologia-iter2` held 51 lines of Metamorfosis documentation never committed.
- **Decision:** after a passing smoke `bt_integrate` removes the branch's worktree when `git status --porcelain` is
  empty and deletes the branch with `git branch -d` (never `-D`); `--keep-worktree` skips it; a caller inside the
  worktree gets the command instead; the live checkout and the deploy worktree are never removed (d3c3d16f1).
- **Rule:** a worktree outlives its branch only when it holds uncommitted work, and then it is reported.
- **Evidence:** `test_integrate` (14).

## D-180 — The scheduler owner settles its own work before it judges a run terminal

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** the legacy scheduler owner loop (`bt_scheduler_run.run`)
- **Context:** `test_scheduler_owner_e2e_subplans` (restart boundaries) failed under load in 54% of runs (13/24). M6
  verdicts reach M1 from their own threads; a verdict landing between the owner's reconcile pass and the snapshot the
  loop judges the run by ended the run `blocked` with a subplan accepted but never published, or `completed` with its
  composition still a candidate — and removed the autostart, so nothing resumed it. A product race, not a test race.
- **Decision:** the owner pass is one helper (`_owner_pass`); when a snapshot looks terminal the owner runs one more pass
  on it and the run ends only if that pass makes no progress (a terminal snapshot has no running attempt, so one pass
  suffices). The terminal notification is suppressed only when that pass found work.
- **Rejected:** a wait in the test (the product was wrong); taking the snapshot before the pass (moves the window).
- **Source:** owner's goal 2026-10-29 («arreglar el origen»); found and fixed by an Opus subagent (`4b72b998e`), the
  notification kept for a waiting blocked run by the operator (`ce50a946c`).
- **Evidence:** two deterministic tests that hold the T8/T13 verdict inside the owner pass (fail on the old loop);
  under 12 parallel runs + 32 CPU hogs: before 13/24 failed, after 0/24.

## D-186 — Bracketed paths read as missing when they are missing

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-160, D-172, D-174
- **Context:** pictures REQ-021 r25 stalled at 23:05 with nothing running and no decision: gate CG-7 (T97) failed to
  compose on every turn with `GitCommandError: path 'src/app/proyectos/[id]/page.tsx' does not exist in 217e5e50`. For a
  missing path with glob characters (Next.js `[id]` routes) `git rev-parse REV:path` exits 0 echoing the argument, so
  the composer's `_blob_id` took "REV:path" for a blob id and `_diff3`'s `cat-file` raised; `git show REV:path` exits 0
  printing the commit, so the D-172/D-160 file reads (`_text_at`, `_json_at`, the package.json indent) could read it as
  file content.
- **Decision:** `_blob_id` uses `rev-parse --verify --quiet --end-of-options` and accepts only an object id; every file
  read at a revision uses `cat-file blob REV:path`.
- **Rule:** git plumbing that resolves `REV:path` must use `--verify`/`cat-file`, never a porcelain or a bare `rev-parse`.
- **Source:** operator monitoring of REQ-021, 2026-10-29 23:20.
- **Evidence:** `test_compose_conflicts.BracketedPaths` (2; red without the fix); repro of CG-7 on a mirror of pictures.

## D-187 — A member whose line holds an earlier candidate is folded from it

- **Date:** 2026-10-29 · **Status:** Accepted · **Refines:** D-160, D-164, D-173
- **Context:** with D-186, CG-7 composed but was rejected: SP-7 conflicted in 13 files. Gate tasks integrate into their
  members' lines (D-164), so SP-7's line held T93/T95/T96's work and CG-6's candidate C3 itself; `_own_work_base` found
  SP-7's snapshots on both sides of those gate merges and fell back to the merge base with SP-6's line, so SP-7's delta
  re-applied SP-3..SP-6 onto a candidate that already had them.
- **Decision:** before the other rules, a member is folded from the largest earlier non-rejected candidate of the same
  run whose members were all folded before it and whose commit is an ancestor of the member's tip (a true common base
  of both sides). `bt_composition.Store.list_candidates` lists a plan's candidates.
- **Consequences:** + later gates compose from what earlier gates already proved; the CG-7 candidate equals SP-7's line
  tree; − none known: without such a candidate the previous rules apply unchanged.
- **Rule:** a fold's base must be a common ancestor of both sides' content; a base that predates content already on
  both sides re-applies it.
- **Source:** operator monitoring of REQ-021, 2026-10-29 23:25.
- **Evidence:** `test_compose_conflicts.PriorCandidate`; repro on a mirror of pictures and a copy of the r25 composition
  store: CG-7 → C4 `candidate`, no conflict, tree identical to SP-7's line tip.

## D-181 — On SIGTERM the engine exits right after DBOS is destroyed

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** REQ-030 (durable runtime), D-171
- **Context:** every engine restart ended in systemd «State 'stop-sigterm' timed out. Killing» after the stop timeout,
  with a DBOS «System database accessed before DBOS was launched» traceback. uv forwarded SIGTERM and DBOS shut down,
  but DBOS 3.3 `_destroy` leaves its non-daemon workflow threads (a run in `DBOS.recv` up to 300 s, an owner decision up
  to 24 h, long steps) and the interpreter waited for them — while they kept doing external effects.
- **Decision:** `service.serve` calls `os._exit` right after `engine.stop()` when it owns the signals (exit 1 if the loop
  failed). Unrecorded steps re-run after recovery: nothing a SIGKILL would not lose.
- **Evidence:** `test_durable_shutdown` (stop < 15 s, the next engine finishes the run with 1 launch; old code 85 s and the
  journal's traceback). Commit 8076460a3. Found by the Metamorfosis audit (Opus subagent, owner's goal 2026-10-29).

## D-182 — bt.run and bt.task have no DBOS recovery limit

- **Date:** 2026-10-30 · **Status:** Accepted
- **Context:** DBOS adds 1 to `recovery_attempts` on every dispatch, recoveries included, and never resets it; past
  `max_recovery_attempts` (100) a workflow is dead-lettered (MAX_RECOVERY_ATTEMPTS_EXCEEDED). Live: `bt:pictures:
  REQ-021:r25` was at 7 after one day of deploys.
- **Decision:** the long-lived `bt.run`/`bt.task` workflows have no limit; agent, verify and integrate children keep it.
- **Evidence:** `ManyRestarts` (count 150 between engines: dead-lettered before, completed now). Commit 52454bd16.

## D-183 — The engine's interpreter and database variables never reach agents, checks or tmux sessions

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** the agent environment rule (366cbf372)
- **Context:** under `uv run` the engine has `VIRTUAL_ENV` and the venv's `bin` first on PATH; `m3` copied them to every
  agent, so an agent's `pip install` hit the live engine's venv. A `bitacora` tmux server started by the engine (for the
  Solucionador) gave every later session its `BT_DURABLE_DATABASE_URL`, password included. REPORT's claim that the
  database variables never reach an agent had no test.
- **Decision:** `m3.inherited_env()` drops the venv variables and its `bin`; the M6 sandbox drops the same names;
  `bt_agent_terminal._run` runs tmux with a cleaned environment. A tmux server already running keeps its old environment
  until restarted (the live one was checked: it has none of these names).
- **Evidence:** commits f5ed593a3, 65226b40f, 8719f3a01 with their tests (real tmux on a private socket).

## D-184 — Refs that must exist together are written in one transaction

- **Date:** 2026-10-30 · **Status:** Accepted
- **Context:** `_run_line` wrote a run line and its `-base` pin with two commands; a crash between them left
  `LINE_BASE_UNKNOWN` on every later sync until someone pinned it by hand.
- **Decision:** both refs in one `update-ref --stdin` transaction; a pin left without its line starts the line at it.
- **Evidence:** `test_durable_line_pin` (a crash after each ref write, real git). Commit 1fe734e54.

## D-185 — A stage join leaves a durable marker before it cancels, and joins are serialised

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-149
- **Context:** a join cut between `client.cancel(old)` and `client.start(new)` left the run cancelled; with no live
  attempts no `RUN.join.json` existed, so the engine's drain pass never finished it, and no trigger noticed.
- **Decision:** `RUN.join.json` is written (fsynced) before the cancel and removed only after the run pointer moved; the
  drain finishes a join from it; `RUN.join.lock` serialises CLI joins and the drain (the drain skips a busy one).
- **Evidence:** an end-to-end join killed after the cancel is finished by the engine. Commit 2746e3a4f.

## D-188 — A transient «unknown» observation never kills a healthy agent

- **Date:** 2026-10-30 · **Status:** Accepted
- **Context:** `test_durable_postgres` launched the agent twice under load: one unanswered `systemctl --user show` made the
  supervisor report `unknown`, and the agent workflow treated it as «not running», killed the healthy agent and launched
  it again — a real double launch, also seen 4/10 in `test_durable_remote`'s archived engine.
- **Decision:** the `bt.observe`/`bt.launch` steps look again for up to 30 s before acting on `unknown`; the reaper,
  which must act at once, does not.
- **Evidence:** `test_durable_observe_hiccup` (a systemctl shim failing one call: old code killed the agent after 7 of
  100 heartbeats; now 1 launch). Postgres stress 26/26. Commits dd21ab302, 45f51668b, 9786b678f.

## D-189 — One history line per verdict

- **Date:** 2026-10-30 · **Status:** Accepted
- **Context:** a verify step re-run after a restart appended a second line to `RUN.notes/<task>.history.jsonl`.
- **Decision:** each line names its verdict (attempt, profile, M6 result ref); a repeat is skipped. Commit 3cf2ad902.

## D-190 — The Solucionador also watches stalled and ended runs

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-175
- **Context:** pictures REQ-021 r25 sat PENDING with nothing running and no decision while CG-7 failed to compose, then
  ended 23:19 «blocked» (CG-7 rejected, COMPOSE_FAILED 3 turns); the Solucionador never started.
- **Decision:** `stalled` (run PENDING, not paused, no live task, no open decision, summary and gates unchanged for
  `solver.stuck_minutes`, clock from the last change) and `ended` (run SUCCESS with a rejected gate, or blocked with a
  task the owner did not stop — owner stops read from the telemetry and RUN.decisions.jsonl), fired at once, once per
  run workflow and set. The brief carries the gate telemetry and the remedy: fix the origin, then `bt-durable retry-task
  <project> <REQ> <gate task>` (a known case in `agents/solver.md`).
- **Evidence:** `test_durable_solver`. Commits a9c42696c, 21f461bf2.

## D-191 — A step that runs out of retries reports its cause

- **Date:** 2026-10-30 · **Status:** Accepted
- **Context:** CG-7 was rejected as «bt.compose has exceeded its maximum of 3 retries»; the GitCommandError that caused it
  was lost (live telemetry), so the cause had to be dug out by hand.
- **Decision:** the rejection text keeps the last error's text (text only; no step-sequence change). Commit 450854f5e.
- **Also in this branch:** three test races fixed (`test_durable_versioning`, the lab waits for the engine's schema
  marker, `test_durable_e2e`'s cancel counted other labs' processes); the bt_durable README rescued from an uncommitted
  worktree and checked against the code. Open: one unexplained double launch of T2 in `test_durable_subplans` (stale
  lock), not reproduced in 16 stressed runs since D-188. Proposals left: the maintenance loop on the main thread without
  git timeouts; pin `application_version` before DBOS 3.4; M6 policy cached for the engine's life; CI replay of live
  histories; an owner retry after an escalation reuses the last automatic retry's base.

## D-192 — Only the current run's rejected gates are announced

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-160 (blocked-run notice)
- **Context:** at each engine restart of 2026-10-30 (00:09, 00:41) the owner got «El run se detuvo: la composición de
  CG-3 (T93), CG-5 (T95), CG-6 (T96) tiene conflictos…» and, once, the same for CG-7, while r25 ran with every gate
  composed. Every engine start projects each settled run workflow once more; `_announce_blocked` ran for r19's and r24's
  rejections too, and its one-key marker (`RUN.blocked-notice.json`) flipped between runs, so each was told again.
- **Decision:** the notice is only for the run the requirement points at (`RUN.durable-run.json`).
- **Rule:** anything an engine pass tells the owner is about the current run; history is shown, never announced.
- **Source:** operator watch of REQ-021, 2026-10-30 02:15.
- **Evidence:** `test_compose_conflicts.BlockedNotice.test_an_earlier_run_of_the_requirement_is_never_announced`
  (fails without the fix).

## D-193 — A rejected gate's conflict reaches the Solucionador

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-175, D-190
- **Context:** 04:38 the composer rejected pictures REQ-021 r25's CG-9 (`git_text_conflict` on
  `src/components/tres-d/Taller3D.tsx` and `Biblioteca.tsx`, members SP-4/5/7/8/9) and wrote two resolution requests.
  The run kept running other tasks; the `resolution` trigger only attached a request to a run whose open decision named
  it (or the one run with an INTEGRATION_CONFLICT decision), and a composer rejection leaves no decision — the
  Solucionador never started; `ended` (D-190) would fire only when the whole run settled.
- **Decision:** `resolutions.rejected_paths` reads each gate's last rejected `gate_composed` event (per-member conflict
  paths) for the gates the run's summary rejects now; a request on one of those paths goes to that run, task = the gate.
- **Evidence:** `test_durable_solver.test_a_rejected_gates_conflict_goes_to_its_run_without_any_decision`; live probe on
  r25: exactly the two CG-9 requests, the older unrelated requests ignored.

## D-194 — A Solucionador session's commands are its own

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-175, D-190
- **Context:** the first live Solucionador session (`20261030-051648-0278`, 05:16–05:30) resolved CG-9's two conflicts
  (pictures D-077) and ran `bt-durable retry-task pictures REQ-021 T99`, which was recorded `by: owner`: `retry-task`
  took no `--by`. The Solucionador's actions and the owner's must stay apart (D-190 reads owner stops from them; the
  panel and the bitácora attribute decisions).
- **Decision:** `answer`, `retry-task`, `pause` and `resume` default to `solver` inside a Solucionador session
  (`BITACORA_SOLVER`, set by `bt_durable.solver`) and to `owner` elsewhere; `retry-task` takes `--by` like `answer`.
- **Evidence:** `test_durable_solver.test_inside_a_solver_session_its_commands_are_its_own`.
- **Also seen in that first session:** it ran on Codex gpt-6.1-sol, not Claude Opus — by policy: claude-work at 100% of
  its week, claude-personal excluded from work projects, claude-luis without `skipDangerousModePermissionPrompt` (only
  the owner sets it).

## D-195 — «Probar» shows the version's real URL; a click restarts it clean

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-156, D-158
- **Context:** the owner, at the machine: «Probar» did not work, and it is critical — if a version cannot be tried,
  nothing makes sense. Evidence (Opus subagent, real Chromium/Firefox): links went through `p<port>.localhost:8765`
  (`bt_version_proxy`), which does not carry WebSockets, so Next's live reload failed (501) and the SP-1 page reloaded
  itself 3 times in 170 s with 35 socket errors (direct URL: once, no errors); a failed preparation looked like
  «Preparando…» forever (no pid file, pane kept); a click reused an existing session instead of restarting; the steps
  pointed at `localhost:3000` while the version ran elsewhere; SP-1/SP-2 servers from the day before were still running.
- **Decision:** the panel shows `http://localhost:<port>/` with «Probar ↗»; a click (new tab) stops everything of that
  version — processes marked `BITACORA_VERIFY_ID`, descendants of its tmux pane, or listeners working inside its copy;
  never by port alone, never other versions or unrelated services — refuses a copy that is not exactly the published
  commit, starts it clean (`.next` and old logs removed, stable ports, a port held by anything else skipped), shows the
  phase and on failure the step and log tail, and opens the URL when every server answers. «Cómo probarlo» (3–8 steps)
  is generated from the subplan's `## Pruebas` row (SPEC.es.md), the plan's checks and its acceptance criteria, with the
  version's own URLs and the accounts named (never secrets). `bt_version_proxy` is removed (remote use: `ssh -L`). A
  requirement may carry its own `verify-servers.json`.
- **Evidence:** `test_verify_procs`, `test_verify_guide`, `test_verify_servers` (21); e2e on the live bitácora: SP-1's
  leftovers replaced and loaded (200); SP-8/SP-9/T10.5 started from their snapshots in a proof root, a second click and
  a two-tab race leave one tree, SP-9's click leaves SP-8 untouched. Commit 778d2e902.
- **Found on the way:** pictures REQ-021 lines from CG-3 on carry two `039_*` migrations (SP-4, SP-5); `rag:migrate`
  refuses them, so SP-7/8/9 and T10.5 cannot be tried until the run fixes it — sent to the run's Planner 07:40.

## D-196 — A manual-evidence decision is tried and answered from its card

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-195, the durable attest path
- **Context:** T10.5 asked for manual evidence (English/Spanish AI replies) and offered only «Reintentar»; the owner: it
  should open a button that sends me to test that something.
- **Decision:** a `MANUAL_EVIDENCE_REQUIRED`/`CRITERION_MANUAL` decision offering `reverify` carries its task, request and
  attempt; its card offers «Probar esto ↗» (starts that attempt's snapshot with the same clean machinery), the check as
  steps (account, what to type in each language, what to see, the configured provider without secrets), «Funciona»
  (the owner's evidence → `bt-durable attest --by owner` → reverify) and «No funciona» (`retry_with_note`). tmux session
  names replace `.`/`:` (a dot is a window/pane separator; `T10.5` sessions were never found).
- **Evidence:** `test_manual_check` (7). Commits b444479e9, a02520a1e.

## D-197 — The integration regression is staged

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-176, D-177
- **Context:** every integration cost ~30 min of full regression under the machine-wide lock, even for a 2-file change;
  the owner asked for a selective regression (2026-10-30).
- **Decision:** `integrate.regression` = `staged` (default): the suites the change can reach (plus the always-run boundary
  and contract suites and the changed suites) run first and stop at the first real failure — the fast red — then the
  rest runs before the merge. `selective` (opt-in, `--selective`) integrates on the selection alone and runs the full
  regression of the merge afterwards in its own transient unit; a red is written to the release log with the
  `bt_integrate.py --revert MERGE …` command and notified, never reverted silently. `full` skips the selection. The
  Solucionador never passes `--selective` (it integrates unattended).
- **Evidence:** on the 8 integrations since 2026-10-29 21:57: recall 4/4 failed suites (the one real failure, owner-race's
  boundary test, in the first phase: red at ≤7m45s instead of 27m40s); staged costs ~1 min more than full; selective
  would have saved ~5.8 min on trusted changes. Branch regression 301 files, no failures. Commits d6124698f, c496bd58b,
  a9152fd7a, bdfb00051 (a relative-path bug in `bt_regress` found by its own first run). Built by an Opus subagent.

## D-198 — What the impact selection follows, and when it is not trusted

- **Date:** 2026-10-30 · **Status:** Accepted
- **Decision:** `bt_regress_select` walks a static `ast` graph of the repo (cached by content): module imports
  transitively; lazy imports, module names in strings (`importlib`, `mock.patch`, `-m`), console scripts and scripts run
  by file name only from the suite and what it imports directly, and inside one package at any depth; assets, folders
  and globs named by the suite. Not trusted (everything runs, reached suites first): `pyproject.toml` beyond
  `py-modules`, `uv.lock`, `.python-version`, the regression's own code, a non-`test_*.py` file under a tests folder, a
  changed non-doc file no suite reaches, or more than `integrate.selective_max_percent` (40) of the suites.
- **Rule:** a change the static graph cannot see runs everything.
- **Evidence:** co-change recall 276/276 over 188 commits (0.984 before the in-package lazy rule); following lazy imports
  everywhere would select 283/300 suites. Commits d6124698f, 615303d2f.

## D-199 — A message to an agent counts as sent only when it left the input box

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** the Planner notice path (`bt_agent_terminal.send`)
- **Context:** 07:40 the operator sent pictures REQ-021's Planner (Codex) the 039 migration defect with `tell-planner`,
  which answered «Enviado al Planner»; at 07:46 the Planner's input box still held «[Pasted Content 1020 chars]»: Codex
  keeps a long typed text as a paste until a second Enter. Every long notice (web actions, healing's plan defects,
  the Solucionador's `tell-planner`) could be lost the same way.
- **Decision:** after Enter, `send` reads the input box (the last prompt line); while it still holds the message or a
  paste placeholder it presses Enter again (3 tries), and otherwise says «Quedó escrito en el agente sin enviarse».
- **Evidence:** `test_agent_terminal.test_a_message_left_as_a_paste_is_submitted_again` (real tmux) and
  `test_unsent_reads_only_the_input_box`.

## D-200 — Where to try a version is a list of links to its real pages

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-195, D-196
- **Context:** the owner (several times): «en vez del botón de probar debe darme el link a la URL donde probarlo y que me
  abra la URL en el navegador… tampoco salen las URLs que se deben probar, las específicas de la solución». D-195 kept a
  «Probar ↗» button next to the root URL; the pages the test names (`/login`, `/3d`) were plain text until the version
  was running, and the restart tab always landed on `/`.
- **Decision:** «Dónde probarlo» lists the version's URL and every page its test names, each a plain link to
  `http://localhost:<port>/<page>` (also while stopped). On a running version a click opens the page as it is; otherwise
  it stops everything of the version, starts it clean from its commit and the new tab lands on that same page (`path`,
  validated: same host only). «Reiniciar desde cero» forces the restart; no «Probar» button. The manual-evidence card
  (T10.5) works the same way with the pages its steps name.
- **Evidence:** `test_verify_servers.Panel`, `test_manual_check`; real Chromium on a copy of the panel: SP-2 running →
  the `/login` link opened `http://localhost:3001/login`; SP-2 stopped → the `/3d` link restarted it clean (new pids at
  09:13:18) and landed on `http://localhost:3001/login?from=%2F3d` (the app's own sign-in redirect).

## D-201 — Each version link carries its SSH bridge and opens on the owner's own computer

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-200
- **Context:** «Probar» still «did not work» for the owner: they work from a **Windows** computer reaching this machine
  through an SSH tunnel to 8765 (AdvIn's reverse tunnel, port 2222), so every `http://localhost:<port>` link pointed at
  their own computer. Their ask: next to each link, the SSH bridge command, and if possible the click should run it on
  the computer they are using.
- **Decision:** next to each page link: «copiar puente» (`ssh -N -L <port>:127.0.0.1:<port> <destination>`, env `BITACORA_TUNNEL_TARGET`,
  default `laptop`, the owner's SSH alias for this machine; env `BITACORA_TUNNEL_TARGET`) and «en mi computador ↗» (`bitacora://open/?port=&path=`).
  A browser cannot run commands by itself, so a one-time opener for Windows (`assets/bitacora-opener.ps1`, served at
  `/static/bitacora-opener.ps1`; per-user `HKCU` protocol, no administrator) asks once for the SSH destination, and on
  each link starts the bridge in a minimized window when the port is closed, waits for it and opens the page in the
  default browser. It accepts only a port 1024–65535 and a local path; the SSH destination lives in its own config, never
  in the link. A stopped version is restarted clean in the background before the opener is called.
- **Evidence:** `test_verify_servers.Panel.test_each_link_has_its_bridge_and_opens_on_the_owners_computer`; rendered on a
  copy of the panel. The PowerShell opener was not run on Windows here (no Windows machine); its first real use is the
  owner's.

## D-202 — «Probar» starts a version already signed in; «Reiniciar con login» for accounts and roles

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-195, D-200
- **Context:** the owner: «¿podemos hacer que en local no pida login? que ya esté autenticado desde el principio».
  pictures already has a development-only local mode (`AUTH_LOCAL_SIN_RESTRICCIONES=1`: loopback peers are the local
  administrator; refused by `next build`, production and the ai-api). Through the owner's SSH bridge the peer is loopback.
- **Decision:** a recipe server may declare `local_auth` (env applied only to that server's run line, never to prepare or
  other servers); «Probar» starts with it by default and records `login: false`; «Reiniciar con login (roles)» starts as
  in production, for tests of a given account or role, and the panel says which mode is running. pictures' recipe sets it
  on the web server (backup of the previous recipe in the operator's scratchpad).
- **Found:** with the mode on, `/3d` and `/admin/cuentas` answer 200 signed in, but pictures' home (`src/app/page.tsx`)
  reads the session from the cookie only and redirects to `/login` — a product defect sent to REQ-021's Planner.
- **Evidence:** `test_verify_servers.SignedIn` (3); live: SP-8 restarted with `login: false`, the web process carries
  the variable and the ai-api does not; `/3d` 200 (Taller), `/admin/cuentas` 200.


## D-203 — Repeated verifier interruptions preserve their cause and use bounded snapshot recovery

- **Context:** pictures REQ-021 r26 T10.45:d1@k1 was classified as a missing resource (`BLOCKED_ENV`), but its M6 result contains only `ENGINE_INTERRUPTED`: startup recovery requeued the request at 09:53:19 and a second restart exhausted that request retry at 10:06:03. A coding-agent retry cannot fix an interrupted verifier.
- **Decision:** classify a pure interruption as verification/ENGINE_INTERRUPTED and use the existing bounded same-snapshot REVERIFY path. Mixed issues, permissions and manual evidence keep their guards. Version-gate the changed task branch with DBOS.patch("bt-task-interrupted-reverify") in the execution recovery-policy module; historical escalation keeps its step sequence. Request-level recovery stays once per key; task repair/time budgets remain enforced.
- **Consequences:** new task histories can verify the captured snapshot again without a new coding attempt after request recovery is exhausted; existing open decisions still require an explicit solver answer. No acceptance is fabricated, and a repeated failure after the repair budget escalates with its concrete cause. Integration pending validation in solver/20261030-100736-d494 when this entry was written.
- **Rule:** never infer missing resources solely from M6's aggregate BLOCKED_ENV when its sole concrete issue is ENGINE_INTERRUPTED. Never reverify mixed/authorization/manual issues through this rule; never alter workflow history without a patch.
- **Source:** Solucionador session 20261030-100736-d494, brief trigger pictures:REQ-021:r26:T10.45:T10.45:d1@k1; M6 request and engine journal read directly.
- **Evidence:** test_durable_m6_restart.test_exhausted_restart_recovery_uses_bounded_snapshot_reverification reproduces the two-interruption store path red before the fix; seven tests pass after it, including exhausted-budget, mixed-issue and patch false/true checks. test_durable_control: 17 pass; test_durable_restart_verify: 1 real restart test passes. Full integration regression and live outcome will be recorded in REPORT.md.

## D-204 — An engine restart waits for running verifications

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-171, D-176, D-203
- **Context:** two deploys 35 min apart (09:31 D-200, 10:06 D-201) cut pictures REQ-021 r26 T10.45's verification twice.
  D-171 re-runs an interrupted verification once per request, so the second cut left it as a review the classifier
  read as BLOCKED_ENV, «a declared resource or tool is missing» — nothing was missing; healing's diagnosis failed and
  the Solucionador was started (10:07). With several integrations an hour, any long verification can meet two restarts.
- **Decision:** before restarting `bt-durable.service`, `bt_integrate` waits until no M6 request is `running` (read-only
  sqlite), up to `integrate.drain_minutes` (20), and logs how long it waited and what it restarted over. How a twice-cut
  verification is classified and re-verified is D-203 (the Solucionador's fix, same incident).
- **Rule:** a deploy must not turn work in flight into a decision; the once-per-request recovery is for crashes.
- **Evidence:** `test_integrate.Drain` (2).


## D-208 — Gitless verification commands receive a read-only snapshot identity

- **Context:** REQ-021 r26 T10.45 requires evidence bound to the exact candidate, but its harness runs git rev-parse/diff inside M6. SnapshotResolver intentionally materializes no .git; the actual attempt has no Git mounts because its repository is itself a linked worktree. Even when legacy Git mounts exist, HEAD belongs to the agent worktree rather than the captured M3 snapshot. M6 knows the validated snapshot SHA but did not expose it to commands.
- **Decision:** add the versioned, additive m6.snapshot-context/1 input at fixed sandbox path /run/bt-m6/snapshot.json, mounted read-only outside /workspace. Generate it only after trusted handoff/commit validation and snapshot reconstruction, with exact snapshot/base SHAs, handoff manifest digest, per-file SHA256/link records and their canonical content digest. No caller env variable or repository file supplies this identity. The context module owns serialization; existing commands may ignore it.
- **Consumers/rollback:** T10.45 harness and later exact-candidate checks may validate this envelope and compare materialized harness/source hashes. Current commands remain unchanged. Removing the additive input makes consumers fail closed; it does not alter result schema, authorization, sandbox permission policy or frozen acceptance. Standard tree-cache semantics remain: a check that needs fresh candidate-bound execution declares its required resources (T10.45 already does), which disables pass reuse.
- **Consequences:** product tasks can consume trustworthy exact-candidate metadata without exposing a mutable Git repository or inventing a SHA. This input does not grant authorization or attest a manual check. Integration pending the solver regression.
- **Rule:** candidate SHA comes from the verifier's validated snapshot, never agent HEAD or arbitrary caller-provided values; verify source/harness hashes against the read-only envelope.
- **Source:** Solucionador 20261030-100736-d494, frozen T10.45 binding criterion and direct inspection of M6 snapshot/check runner and actual _git_mounts result ().
- **Evidence:** regression and live sandbox proof will be recorded in session REPORT.md.

## D-205 — Every version link opens already signed in as a real test account

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-200, D-201, D-202
- **Context:** the owner clarified «que en local no necesite iniciar sesión»: «es que se inicie sesión automáticamente».
  D-202's local-administrator shortcut skipped the session, so pictures' home and navigation (which read the cookie)
  still sent them to /login and hid Administración; roles could not be tried.
- **Decision:** a recipe's `auto_login` (`cookie`, `accounts`, `default`, `mint`): the panel runs `mint` in the
  version's copy with its environment and `BT_LOGIN_ACCOUNT`, gets a real session token, sets it as the app's cookie
  (`HttpOnly; SameSite=Lax`, host-only: localhost cookies hold for every port, so the landing uses the panel's own host)
  and redirects to the page. Links go through `/p/<p>/req/<R>/verify-go` (panel token, this machine only), which also
  starts a stopped version and comes back to sign in; the real URL stays as the link text. «Entras ya con sesión
  iniciada como» picks the account (one per role); the Windows opener sets the cookie first. pictures' recipe mints a row
  in `account_sessions` for `test+<role>@req021.test` and accepts the version's data notice for it; D-202's local mode
  is off for pictures. The six test accounts were seeded in the REQ-021 test database with a generated password stored in
  the owner's secrets file (`PICTURES_TEST_PASSWORD`, 600), as the owner chose.
- **Evidence:** `test_verify_servers.AutoLogin` (3); real Chromium on a copy of the panel: SP-2 stopped → link → restart →
  signed in as test+administrador → landed in the app with its account menu; `/admin/cuentas` 200 with the cookie.

## D-209 — A decision number is reserved when it is taken

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** `bitacora.py id`
- **Context:** `next_id` computed the next D-NNN from DECISIONS.md alone, so every session or agent that chose a number
  before writing its entry could pick one already chosen elsewhere: four collisions on 2026-10-29/30 (D-172 twice,
  D-202 twice, the Solucionador's «D-205» against `metodologia-02`'s), each fixed by renumbering commits and entries.
- **Decision:** `bitacora.py id D --reserve "<who: what for>"` records the number in `<project>/.ids-reserved.json`
  under a file lock; every later `id` call, reserving or not, skips reserved numbers even before their entry exists.
  The documentation and the Solucionador's prompt say to reserve the moment a number is chosen.
- **Rule:** a number is taken when it is reserved, not when it is written.
- **Evidence:** `test_ids_high_water` (16 parallel reservations, 16 distinct numbers; a plain read skips reservations).
  Numbers handed out by hand today before this existed: D-205 (`metodologia-02`), D-206/D-207 (engine races), D-208
  (Solucionador, verifier snapshot), D-210 (restart-safe engine).

## D-211 — Every start lands signed in, and the guide speaks of the open session

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-205
- **Context:** right after D-205 the owner stopped and restarted SP-2 and was asked to sign in; signing in by hand failed.
  Evidence: no session was minted after 11:30 (the clicks never went through the sign-in: an old panel tab, a typed URL
  or «Reiniciar desde cero», whose waiting tab landed on the plain URL), and the guide still said «inicia sesión como
  admin@prueba.local», an account the REQ-021 test database does not have (the seeded ones are `test+<role>@req021.test`).
- **Decision:** when the recipe signs in automatically, every waiting tab (restart, «Reiniciar desde cero», decision
  cards) comes back through `/verify-go` before landing; the guide maps the plan's accounts to the seeded ones
  (`admin@…` → `test+administrador@…`, `designer-plus@…` → `test+designer_plus@…`), says the session is already open,
  drops the seed/password steps, and the manual-evidence card signs in as the account its check needs.
- **Rule:** a guide never asks the owner for something the system already did or for data that does not exist.
- **Evidence:** `test_verify_guide.SignedIn`, `test_verify_servers.AutoLogin` (waiting page default); the SP-2 guide
  rendered on a copy of the panel.

## D-220 — One full regression at a time; merged deploy branches are removed

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-176, D-197
- **Context:** (found by `metodologia-90`) three full regressions ran at once on 2026-10-30 — a post-merge run, another
  post-merge run and a staged integration — and one took 1 h 40; the shared load produced the «load flake, passes alone»
  lines every integration then had to judge. Separately, step 4's `deploy-<branch>` branches were never deleted after a
  passing smoke: 17 merged ones had piled up.
- **Decision:** `Services.regress` (integrations and post-merge runs alike) holds `<state>/regress-slot.lock`, so one
  full regression runs at a time (waits up to 2 h). After a successful fast-forward (or revert) the deploy worktree is
  detached on main and its `deploy-`/`revert-` branch deleted with `-d`.
- **Rule:** load races are hunted on purpose (stress scripts, the D-210 chaos test), never by accident of scheduling.
- **Evidence:** `test_integrate.Hygiene` (three regressions in parallel threads never overlap); the success-path test
  asserts the deploy branch is gone. Commit 7c29360ba.


### Integration receipt for D-203 and D-208 · 2026-10-30

Solucionador 20261030-100736-d494 integrated merge fff622890f28b8093a9a0afda9c4077d056bea1b through bt_integrate only: 303 suites, no failures (first26 3m05s, rest277 24m56s), DBOS backup, push, 40-second verifier drain, both unit restarts and passing smoke; integrator exit0 and clean worktree/branch cleanup. Quality module189, focused restart7/control17/real-kill2/context2 checks and pre-integration sdist/wheel build pass; Ruff/whitespace pass. No Python static type checker configured. Full receipt/report is pictures REQ-021 RUN.solver/20261030-100736-d494/REPORT.md. Owner-authorized r27 join superseded the original r26 decision, so no stale answer was sent.


## D-221 — Re-verification observes a fresh integration of the same snapshot

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** durable owner re-verification, D-174
- **Context:** pictures REQ-021 r27 T2.55:d2@k1 repeats an SP-14 menu conflict after the exact recorded resolutions exist. The real integrator now merges ca9858ee with e3dfac3e successfully, but `_evaluate` reuses `bt:<attempt>:integrate` and DBOS returns the previously completed conflict result. Repeating an agent cannot repair that cached observation.
- **Decision:** bind nonstandard verification profiles to distinct integration child workflow IDs, behind `DBOS.patch(bt-task-reverify-reintegrates)`. Preserve the standard identity and old recorded histories; replay of the same profile remains idempotent. A failed verification still cannot reach integration.
- **Consequences:** each new same-snapshot verification can observe newly recorded resolutions or a changed line without launching an agent. Integration still uses the existing all-lines compare-and-swap and never advances a conflicting line. Integration and live decision handling pending at entry creation; the session report records the final receipt.
- **Rule:** a cached conflict is evidence about the previous integration observation, not a permanent verdict on an immutable snapshot. Replaying an observation reuses its result; explicitly re-verifying creates a fresh observation.
- **Source:** Solucionador 20261030-120814-28ad; live r27 T2.55:d2@k1; execution/workflows.py `_owner` and `_evaluate`.
- **Evidence:** new test_durable_reintegrate reproduces the stale result before the fix (3 tests, 1 failure, exit 1); all three local seam tests pass after it. Five final regression tests pass, including real DBOS restart and exact recorded resolution. A separate old-engine-to-new-engine replay passes with the historical cached integration intact (19.770s). The panel regression verifies both database orderings. Full integration receipt is recorded in the session REPORT.md when complete.

## D-212 — Diagnosing agents run isolated from the user's settings, hooks and memory

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-168, D-183 (agents never get the operator's environment)
- **Context:** every healing diagnosis of pictures REQ-021 today failed «la respuesta no trae JSON» (r26 T10.45:d1 10:07,
  r27 T2.55:d1 12:01, T2.55:d2 12:07), so each decision reached the Solucionador with no diagnosis. Reproduced with the
  same profile (`claude`, haiku): `claude -p` loaded the user's CLAUDE.md, the metodologia skill and the hooks, began its
  answer «Aye», took the bitácora's gitleaks notice as its task, and the final message (the one `--output-format text`
  prints) was that report — 45–88 s, no JSON.
- **Decision:** `bt_block_agent.argv` (diagnosis, attempt analyst, manual reviewer) runs Claude with the read-only tools
  only (`Read,Grep,Glob`: the analyst reads its sealed snapshot), `--strict-mcp-config` with an empty MCP config,
  `--setting-sources ""` and `--disable-slash-commands` — as the translator and the Planner diagnostic already do. A
  failed parse stores what the agent said instead (240 chars) as evidence.
- **Rule:** an engine-owned model call never inherits the operator's Claude settings, hooks, memory or MCP servers.
- **Evidence:** `test_block_diagnosis` (27; argv isolation and the kept answer red on main); live probe of the same
  request isolated: valid JSON 2/2 in 6.6 s and 8.5 s (kind `conflict`, the D-213 cause). Branch `diagnosis-isolated`.

## D-213 — A member is accepted once its own subplan line takes it; another subplan's line that conflicts is reported

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-164, D-173
- **Context:** pictures REQ-021 r27 T2.55 (SP-2; the stage r27 added it, so it became an ancestor of SP-14's accepted
  tasks) failed `bt.integrate` at 11:40:01 with a conflict in `MenuCuenta.tsx`/`textos-cuenta.ts` «(line of SP-14)».
  RECONCILE_INTEGRATION rebuilt it, but `bt.base_ref` returns its own SP-2 tip (b3f997fe) for every attempt, and SP-14's
  work is not on it: a2 spent 20 min and met the same conflict; d1 (11:59), the Solucionador's `reverify`, d2 (12:05).
  `GitLineIntegrator.integrate` required every subplan line in the task's scope to merge, while the legacy
  `SubplanLineRouter` applies a member to its own line only and the run's own `sync` already reports such a conflict.
- **Decision:** `integrate(..., home=)`: once the member's own line takes it, a conflict on another subplan's line leaves
  that line as it was and is reported (`subplan_line_conflict`, read by the Solucionador's gate trail); the gate that
  composes both subplans meets it where resolutions are made. Gate tasks and calls with no home keep the old rule. The
  change is inside the `bt.integrate` step (no step sequence change, no patch).
- **Rule:** a failure whose retry starts from the same base can never be the task's failure.
- **Evidence:** `test_durable_subplans.OtherSubplansLine` (3, real git, red on main). Found by the second Metamorfosis
  audit (Opus subagent). Not done (proposals): a gate line left out at base time (D-173) still fails every retry the same
  way; dependents of a left-out predecessor are not held (legacy `PREDECESSOR_NEEDS_RESOLUTION`); `sync_lines` repeats
  its report each time the accepted set changes.

## D-214 — The Solucionador's watchdog and account move wait for the session's own integration; a superseded session is told and kept

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-175, D-176
- **Context:** Solucionador session `20261030-100736-d494` (started 10:07:36, `solver.max_minutes` 120) was running its
  own `bt_integrate.py --session 20261030-100736-d494` (D-203/D-208), a child of its agent in tmux; at 12:07:36
  `_supervise` would have killed the tmux session and the integration with it, mid-regression or mid-merge. The operator
  raised the limit to 240 at 11:53; the integration landed at 11:59. Its trigger (r26 T10.45:d1) had also gone with r26,
  cancelled by the 11:18 stage join.
- **Decision:** `solver.integrations(sid)` finds live `bt_integrate.py --session <sid>` processes (post-merge runs are
  their own units, left out); while one runs, neither the watchdog nor the account move kills the session, for at most
  `solver.integrate_grace_minutes` (120) beyond `max_minutes`, recorded once in the activity feed. A session whose
  requirement's run is no longer its trigger's run is told once (inbox + typed): do not answer the old decision, finish
  and integrate the fix, check the current run; it is not killed.
- **Rule:** a supervisor never kills a process tree that holds the integration lock.
- **Evidence:** `test_durable_solver` (5 new, 4 red on main); live probe `integrations('20261030-100736-d494') == [2582981]`.
  `solver.max_minutes` goes back to 120 once this is on main. A sounder complement (bt_integrate re-executing its
  pre-merge phase in a transient unit) is left to the owner of `bt_integrate`.

## D-225 — An integration runs in its own unit; its caller only follows it

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-176, D-214
- **Context:** (suggested by `metodologia-90`) the Solucionador's `bt_integrate` was a child of its codex process in
  tmux; its own watchdog would have killed the session at 12:07 in the middle of the D-203 integration (D-214 now makes
  that watchdog wait). Any other kill of an integration's caller — an agent session, its tmux, a terminal — could still
  cut it after the merge and before the restart and smoke, or halfway through its regression.
- **Decision:** `bt_integrate` re-runs itself in a transient user unit (`bt-integrate-<branch>-<stamp>`, its output in
  `~/.local/share/bitacora-integrate/runs/<unit>.log`, its exit code in `<unit>.rc`) and the caller follows the log and
  returns that exit code; if the caller dies, the integration finishes. `--attached` (and `--dry-run`, post-merge runs
  and runs already inside the unit) run in place.
- **Evidence:** `test_integrate.Detached` (2); a live smoke (a refused integration ran in its unit and returned 75).
  Numbered D-225 because D-221 was taken meanwhile — the collision class D-209 removes.

## D-227 — The regression creates its worktree's uv venv when a suite needs it

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-197 (staged/selective regression)
- **Context:** integrating `diagnosis-isolated` (12:33) died with a Python traceback — `FileNotFoundError` on
  `<worktree>/.venv/bin/python` — as soon as the selection reached a suite that needs DBOS: an integration's worktree is
  a fresh `git worktree add` and nothing created its venv; operators and agents had always made it by hand.
- **Decision:** `bt_regress.venv` runs `uv sync --frozen` once per worktree (cached, under a lock) when the first suite
  that needs the venv starts; a failed sync fails each such suite with the reason in its log (code 125) instead of
  crashing the regression.
- **Rule:** a step the integration needs is the integration's, never the operator's memory.
- **Evidence:** `test_regress_venv` (3; red on main: no `venv`); live: `uv sync --frozen` in the `diagnosis-isolated`
  worktree, 3.2 s. Integrated with D-212 (branch `diagnosis-isolated`).


## D-228 — A regression forcing SIGTTIN must establish its child's signal disposition

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-177 (repair regression failures at their origin)
- **Context:** audit-metamorfosis-2's full integration regression and its isolated rerun both failed test_terminal_read_before_json_resumes_after_forced_background_stop: "fixture did not force the SIGTTIN startup window". The same suite passed in the Solucionador's foreground context (18 tests), but running the exact case with inherited SIGTTIN=SIG_IGN reproduced the failure deterministically. Ignored dispositions survive fork/exec, so the fixture's required stopped state cannot occur in that invocation environment.
- **Decision:** reset SIGTTIN to SIG_DFL in the fixture child before it opens/reads the controlling terminal. Add an explicit regression with the caller's SIGTTIN ignored, restoring the caller's previous disposition afterward. Keep the original real stopped-state, resumed input, success and timeout assertions unchanged. This is a test-fixture correction; production terminal and permission policy are unchanged.
- **Consequences:** the regression proves the intended startup window independently of the invoking shell's inherited ignored signal. It remains red if the production SIGCONT recovery is removed. No timeout is increased and no failure is allowlisted.
- **Rule:** a fixture asserting a kernel signal transition must establish the disposition necessary for that transition rather than inherit it from its launcher.
- **Source:** Solucionador 20261030-120814-28ad, while integrating D-221; prior integration audit-metamorfosis-2 refused on this same regression.
- **Evidence:** terminal-ignored-red.log and new terminal-regression-red.log both exit 1 before the correction, with the exact prior fixture assertion (0.737s / 0.735s). The final full terminal-suite result and integration receipt are recorded in the session REPORT.md.

## D-206 — Old engines run by tests never kill other labs' agents; a re-run launch adopts when systemd is slow

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-188, D-191
- **Context:** `test_durable_shutdown` saw «2 != 1» launches under load, and D-191 had left an unexplained double T2 in
  `test_durable_subplans`. Origin: every test lab uses the same attempt keys, and the old engines that the upgrade and
  replay suites run (code from before e2d961ee5) kill any process of the user carrying that key — when one finished its
  T1 it SIGTERMed the T1 agent of every other lab on the machine (AGENT_CANCELLED → 30 s → a second launch). Reproduced
  naturally: 10 of 14 stressed labs lost their agent in the same second while another regression ran
  `test_durable_remote`. Separately, a real defect: a `bt.launch` re-run after a restart while the user manager did not
  answer exhausted DBOS's 3 tries in seconds (D-188's grace covered observation, not launch's own `systemctl show`),
  ending the agent workflow in ERROR with a healthy agent killed by the reaper.
- **Decision:** `durable_support.export_engine` scopes an old engine's kill scan to processes without
  `BT_SUPERVISOR_ID`; `SystemdSupervisor.launch` adopts its unit from its own files (record, started.json, exit.json)
  when the manager does not answer, and `bt.launch` retries MANAGER_UNAVAILABLE for up to 30 s. No step order changes.
- **Rule:** a test that runs old code must never act on processes it did not create.
- **Evidence:** `test_durable_launch_hiccup`, `test_durable_old_engines`, a new `test_supervisor_lifecycle` case;
  injected hiccup with 16 CPU hogs: main 5/5 red, branch 5/5 green. Commits bf534e7d5, 09bf01a0a, 0680767af, 30e5bfba6.

## D-207 — Tests wait for a join's last act, not its middle

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-185
- **Context:** `test_durable_stage_join` failed under load asserting the join marker was gone right after the owner
  record named the new run; the join writes the owner before `client.start`, the run pointer and the marker removal,
  which is deliberately last (a drain cut after the owner write is finished by the next pass). The product is right.
- **Decision:** the drain tests wait for the marker to disappear, then check owner and pointer. Under load: main 1/16,
  branch 0/16. Commit 82be089d7.

## D-210 — A deliberate restart costs the interrupted work nothing

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-171, D-181, D-203, D-204
- **Context:** the owner (11:2x): «no importa que se reinicie el motor, éste debería ser capaz de continuar sin problemas
  autónomamente». D-171 re-ran an interrupted verification once per request, so two deploys turned T10.45 into a
  decision; DBOS counts every recovery against `max_recovery_attempts`.
- **Decision:** `bt_durable/restarts.py`: the engine writes `engine.session.json` at start and, on SIGTERM, a matching
  fsynced `engine.stopped.json` before DBOS is destroyed and before D-181's `os._exit`; at start it classifies the last
  stop as `clean`, `unexplained` or `first`. After a clean stop, M6 requeues interrupted verifications without spending
  their retry (`requeue_after_clean_stop`, evidence in `verification_restarts`) and PENDING workflows get back the
  dispatch DBOS's recovery counts (`credit_recoveries`); agents are adopted (D-206), joins finished by the drain.
  Composition per M6 request: clean stop → same request requeued free (D-210); first unexplained stop → same request
  requeued once (D-171); second unexplained → a new `:relaxed` request re-verifies the same snapshot, counted against
  the task's `max_environment_repairs` (D-203). Exactly one path per case; none requeues a request twice. No step order
  changes, no `DBOS.patch` needed.
- **Rule:** restarts are routine; only unexplained deaths spend budget.
- **Evidence:** `test_durable_restarts`, `test_durable_restart_verify` (3 SIGTERMs on one verification: 0 retries, 3
  restarts recorded; plus D-203's two-SIGKILL case), `test_durable_shutdown` (recovery_attempts stays 1), and the chaos
  e2e `test_durable_chaos` (3 subplans, audits, gate CG-1, 5 seeded restarts incl. one SIGKILL and a verification cut
  twice): 6/6 seeds green, main 6/6 red. Branch regression 307 files, no failures, no reruns. Commits f2c126c80,
  a4948bfe4, 8b94b4a32, merge 1a1548efc.

- **Focused receipt for D-228:** commit df426432 on solver/20261030-120814-28ad; all 19 terminal tests pass in 4.074s (terminal-green.log, exit 0). The ignored-caller regression was red before the fixture correction and all original assertions/timeouts remain unchanged. Integration is still pending.

## D-229 — Regression suites start with the job-control signals at their default

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-177 (failures fixed at origin), D-227
- **Context:** the integrations of `audit-metamorfosis-2` (12:33) and `diagnosis-isolated` (13:02) were refused for
  `test_orchestration_terminal`, red in the full run and alone, while it passes by hand. Not load: `bt_integrate` was
  started from a background shell (an agent's tool), which ignores SIGTTIN, SIGTTOU and SIGTSTP (SigIgn of the live
  integration process); an ignored disposition survives exec, so the suite's child read the tty from the background, got
  EIO instead of stopping, and the fixture failed every time. A first margin fix on the fixture (wait-until 10 s) was
  withdrawn: it did not touch the cause.
- **Decision:** `bt_regress` runs each suite as `python -c` that resets those three signals to SIG_DFL and then runs
  `unittest.main(argv=[…, name])` — `python -m unittest name` with a sane start, wherever the regression is launched from.
- **Rule:** a test environment starts from defaults, not from whatever its launcher inherited.
- **Evidence:** `run_suite` on `test_orchestration_terminal` with the three signals ignored: main 1, branch 0;
  `test_regress_venv.Signals` red against main's `bt_regress`. Branch `diagnosis-isolated` (with D-212, D-227).

## D-230 — The integrate lock serves waiters in arrival order

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-176, D-220
- **Context:** `machine_lock` polled a non-blocking flock, so whoever polled at the right moment won: `integrate-hygiene`
  waited from 12:32 to its 90-minute limit while the Solucionador's and `metodologia-90`'s integrations, started later,
  went first. With three or four sessions and agents integrating, an early waiter could starve indefinitely.
- **Decision:** `machine_lock` (the integrate lock and the regression slot) keeps a ticket queue next to the lock file
  (`<lock>.queue/<time_ns>-<pid>`); only the oldest live waiter tries the flock; a dead waiter's ticket is dropped.
  Waiters running older code (no ticket) can still take a free lock until every caller runs this one.
- **Evidence:** `test_integrate.FairLock` (arrival order a, b, c behind a holder; a dead ticket is skipped). First
  number taken with `id D --reserve` (D-209).

## D-231 — Probar's automatic sign-in works in any project: the recipe seeds its accounts and names its roles

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-205, D-211
- **Context:** owner: «es importante que la cuestión con las credenciales no sólo funcione en REQ-021 sino en cualquier
  entorno en general». Test accounts had been seeded by hand, the guide mapped roles through a pictures-only
  `_ROLE_ALIAS`, the accounts were named `@req021.test` in a project-level recipe, and a missing account or a malformed
  recipe failed without saying why.
- **Decision:** `auto_login` may declare `seed`, an idempotent command run in the version's copy with its environment,
  `BT_TEST_ACCOUNTS` (`[{email, role}]`) and `BT_TEST_PASSWORD` (the owner's secret named by `password_secret`); the
  panel runs it once when `mint` exits 3 (missing account), retries `mint`, and records the outcome in the version's
  state and `login.log` with secrets masked. `accounts` may be `{email, role, label, aliases}` (plain strings still
  work); the guide, the manual-evidence card and the picker map plan accounts through them. A malformed `auto_login` is
  refused on load with a Spanish message; a failed sign-in lands on a panel page that says why, with «Abrir sin sesión».
  pictures moved to `test+<role>@pictures.test`, seeded with its own scrypt parameters (old rows kept; backup
  `verify-servers.json.bak-20261030`). Contract: `references/requirements.md` «Test servers recipe».
- **Rule:** what a project needs to sign in lives in its recipe, never in metodologia's code; a secret reaches only the
  seed's environment.
- **Evidence:** `test_verify_servers.AutoLogin` (+4, one a non-pictures app seeded on its first click),
  `test_verify_guide.SignedIn` (+2); 125 selected suites pass. Live (copy of the panel on 8781, real Chromium): SP-2 link
  → seed created six accounts → signed in as `test+administrador@pictures.test`; `/admin/cuentas` 200; a password
  sign-in through `/api/login` 200 (the seeded hash matches pictures' `verifyPassword`). Built by an Opus subagent.
  Until it is on main the live recipe stays at the backup (main's panel ignores object accounts).

## D-233 — A confirmed medium audit finding blocks by default, so it is repaired

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-087 (forward remediation), the audit gate's default policy
- **Context:** pictures REQ-021 T2.7 (SP-2 visual review) confirmed six medium contract mismatches in T2.3/T2.4/T2.5
  (no ES/EN control on access screens, Escape leaves the invitation dialog open, rows clipped at 360 px, plain loading
  text instead of skeletons…). Only critical/high blocked, so they would have stayed open with nobody sent to fix them;
  the operator asked the owner whether to include medium. Owner: «los hallazgos son reales y son un problema, entonces
  hay que arreglarlo, es algo que el sistema debería poder hacer sin mi intervención».
- **Decision:** default `gates.audit_blocking` = critical+high+medium (`bt_config` default and
  `bt_audit_gate.BLOCKING_SEVERITIES`; live config set 14:53); `low` stays informational. Blocking findings go through
  the existing remediation (named tasks reworked, audit rerun, bounded by `gates.remediation_rounds`).
- **Rule:** a confirmed defect is repaired by the system; the owner is asked only for what the system cannot decide.
- **Evidence:** `test_audit_gate` (`test_a_confirmed_medium_finding_blocks_by_default_so_it_is_repaired`; the two tests
  that encoded the old default updated); `test_audit_routing`, `test_planblock`, `test_durable_audits(_upgrade)` pass.
  Branch `audit-medium-blocks`; the one-line `bt_config` default changed with its owner session's agreement.

## D-234 — A blocking finding that names only its audit reruns the audit

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-087 (audit remediation)
- **Context:** pictures REQ-021 r27 T2.7 at 14:49: the visual audit's high finding F8 named only T2.7 («T2.7 must be
  rerun»; its capture harness failed on `/cuenta`). `bt_audit_gate.evaluate` drops the audit's own id, so F8 had no
  owner and the run held the audit blocked «for the owner». The operator retried it by hand at ~14:55 with a note.
- **Decision:** the durable `AuditGate.judge` reports an open blocking finding whose tasks name only the audit as a
  problem of the audit; the run reruns the audit with a note naming what to complete, within `gates.remediation_rounds`,
  then holds it as before. Judged inside the `bt.audit_gate` step (no step order change, no patch); the legacy gate is
  unchanged; mixed with owned findings, the audit reruns first.
- **Rule:** a gap in an audit's own coverage goes back to the audit, never to the owner first.
- **Evidence:** `test_durable_audits` (2 real-DBOS e2e + 1 unit; red with the live message before the fix). Built by an
  Opus subagent; full regression 304/304.

## D-235 — A task the run holds blocked while it goes on reaches the Solucionador

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** D-190, REQ-031
- **Context:** T2.7 sat blocked from 14:49 with no decision while r27 kept running other tasks; `stalled`/`ended`
  triggers see only runs that stopped, so nobody was told until the operator acted.
- **Decision:** Solucionador trigger kind `blocked`: the run is PENDING and not paused and holds a task `blocked` with no
  decision behind it, after `solver.blocked_after_seconds` (300); once per block (round workflow + reason); a block
  already handed over is not given again by `stalled`/`ended`; the brief carries the reason and the `retry-task` command.
  No desktop notification of its own (the activity line records it).
- **Rule:** every block without a decision reaches someone, once.
- **Evidence:** `test_durable_solver` (2 new; red→green); full regression 304/304. Integrated with D-233.

## D-236 — A tool's warning is never the decisive line

- **Date:** 2026-10-30 · **Status:** Accepted · **Refines:** the failure digest (`bitacora_platform.failure_lines`)
- **Context:** pictures REQ-021 r27 T10.45 a2 and a3 failed verification and their agents were told, as the «decisive
  lines», uv's «warning: Failed to hardlink files; falling back to full copy…» (it matched the weak word «Failed»),
  while the real cause — `CG-10: candidate_identity_failure: snapshot source bytes match …` followed by a node
  `+ actual - expected` diff — matched nothing (a snake_case code has no word boundary before «failure»). Two attempts
  retried blind; the same digest feeds healing's diagnosis and the Solucionador's brief.
- **Decision:** uv's hardlink warning and its two advice lines are noise like npm's notices; `+ actual - expected` and
  snake_case `*_failure:` / `*_error:` codes rank as strong.
- **Rule:** when an attempt fails twice with the same digest, check the digest names the real cause before blaming the
  agent.
- **Evidence:** `test_failure_lines.test_uvs_hardlink_warning_is_never_the_decisive_line` (red before the fix).
