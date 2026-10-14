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
