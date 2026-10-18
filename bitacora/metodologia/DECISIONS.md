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
