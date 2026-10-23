# Engine v2 — agreed contract (owner rulings, 2026-10-23)

Source documents, in precedence order:

1. **This file** — owner rulings taken on 2026-10-23 (session `fdcfb6a3`). It overrides the master where they differ.
2. `METODOLOGIA_AGENTES_SUBPLANES.md` (same folder) — master spec v1.7, verbatim copy of what the owner pasted.
   Its §§17–21 prevail over its historical sections.

Decision record: D-122 in `../DECISIONS.md`.

## 1. Working frame

| Topic | Ruling |
|---|---|
| Framework | Developed **outside** the Metodología flow: no REQ, no SPEC/PLAN approval, no `launch`/`handoff`/`scheduler-run`/`delegate`. Pure agents: one lead + workers. |
| Where | **Directly on `main`** of `dav033/metodologia` (`~/dev/metodologia`). Workers use temporary worktrees outside the repo; only the lead merges into `main`. |
| Live runs | Stopped and held by the owner's order: david-ui REQ-001 and pictures REQ-020 (`scheduler-op … stop --hold`). They stay held; don't resume them or touch their `.state`. |
| Push cadence | Push `origin/main` **after every green merge** (full suite green). |
| Workers | Codex `gpt-6-luna`, reasoning effort `high`. Up to **6 in parallel**, rotating accounts `~/.codex`, `~/.codex-2` and `~/.codex-luis` (all three authorized). Claude subagents are also allowed (explorer/reviewer/antagonist/runner). |
| Bitácora | Record work **per phase** in the `metodologia` project: day-log entry plus `DECISIONS.md` for every decision; a closing entry per phase. No REQ is created. |
| Upstream skills | Fetch the original SKILL.md, **pin the commit SHA**, verify the license, record provenance in `skill/references/third-party-notices.md`, and write **original adaptations**. Never execute or install anything from upstream. Don't copy CC BY-SA text (Trail of Bits) or text whose license is unverified. |

## 2. Scope — every phase is in

- **F1 Planner + contract.** `PLAN.json` gets a **new schema version** (Option A, D-01); `subplans` is optional and 1.2.0 plans stay valid.
  - Each **subplan belongs to exactly one milestone**, and each task to at most one subplan (D-02). A milestone remains a global phase.
  - Independent audits become per-subplan audits plus composition gates.
  - Validator, atomic freeze, migration/compat and the P-177 regression case are part of F1.
- **F2 Skills and prompts.** All **14 private skills of the master become approved**, including the **3 Implementer drafts**, which the owner approved; the extractor's `proposal` exclusion no longer applies. On top of those:
  - the 2 Runner support files;
  - the new Designer skills, the Reviewer visual axis and the Researcher skills listed below;
  - Ponytail/Caveman adaptations in Implementer;
  - prompt addenda (§20.7) and `install_agents.py` support.
- **F3 Knowledge stores.** Explorer gets the Knowledge Map Ingestor (§10.4–10.9). Researcher gets an **external knowledge store**, separate from the code map, with the §11.5 requirements, plus private skills and adaptations of the 4 recommended public skills (§11.4).
- **F4 Git engine + M1–M6.**
  - Subplan versions, composition manifests, candidate integration workspaces and selective propagation (§3).
  - The verify/reintegrate/adapt/rework/reimplement distinction.
  - Result taxonomy (`BLOCKED_EXTERNAL` etc.) as compatible evidence fields, with migration.
  - Gates: subplan audit, composition, Designer contract, visual axis.
  - Adapting M1/M2/M3/M5/M6, aligning the review policy (`subagents.md` vs `bt_review_policy.py`) and the D-10 benchmark.

## 3. Designer — full eighth role (overrides master §§4–5 «pending»)

- `skill/agents/designer.md`, a role like any other, plus install support for Claude, Codex and Antigravity.
- Declared model: Claude `opus` / `high`; Codex `gpt-6.1-sol` / `high`. M2 may reroute.
- Owns the **UI/UX contract** and the optional **preview**. They live in the **project repo under `design/`**:
  - `design/contracts/<contract-id>@v<N>.md` (versioned, immutable once approved);
  - `design/preview/` (only when the project enables the preview).
- Designer may write **only under `design/`**. The runtime enforces that ownership; the prompt alone is not enough. Designer never owns production code.
- Private skills:
  - `ui-ux-contract-authoring` — contract template and checklist: structure, hierarchy, tokens, navigation, flows, states, responsive, a11y, acceptance criteria.
  - `design-contract-versioning-and-impact` — versioning, changelog, impact of a visual change on the subplans and views that consume it; approval gate for implementers.
  - `preview-prototype-maintenance` — optional preview with mock data and a state switcher, synced to the contract version.
- Public skills to adapt (pinned SHA plus license check):
  - `jakubkrehel/skills` (MIT): better-writing, better-layout, better-accessibility, better-colors, state-machine; **exclude** build-design.
  - `wshobson/agents` plugin `ui-design` (MIT): design-system-patterns and responsive-design; don't install the plugin or its agents.
  - `mae616/design-skills` (MIT): ui-designer (hierarchy, information architecture, «states as specs»).
  - `anthropics/skills` `frontend-design` (Apache-2.0): **conditional**, aesthetic direction only, never writing production code.
- The Planner **must** detect UI work and plan the Designer gate (master §7.5, P-PL-04 now active). The preview is optional per project; the contract is mandatory whenever there is UI work.
- **Visual QA = a third Reviewer axis `visual`** (D-05), read-only, with the new private skill `rendered-ui-fidelity-audit`. It captures each breakpoint and state, runs axe and compares the result with the contract criteria.
  - Technique sources: `testdino-hq/playwright-skill` (MIT) and `anthropics/skills` `webapp-testing`, whose license must be verified before adapting.
  - Spec and standards keep one axis per session.
- Research notes: `designer-skills-research.md` (this folder).

## 4. Researcher

- Gets private skills (names fixed by the lead in F2 and recorded as a decision). Suggested names: `external-research-memory` and `source-freshness-verification`.
- Adapt the four public skills recommended in master §11.4:
  - SkillMedev `deep-research`;
  - citypaul `evaluate-existing-solutions`;
  - jp-cruz `fact-checker`;
  - SkillMedev `research-synthesis`.
- Writes go only to the approved knowledge store through its ingestor; Researcher never edits code.

## 5. Workspace cleanup (phase P0)

Before anything is deleted, back up to `~/backups/metodologia-engine-v2-2026-10-23/`:
- a `git bundle` of every ref that will be deleted;
- a tarball of every `.state/executor` folder that will be removed.

What gets cleaned up:

- All `m3/att-*` attempt worktrees and branches of **closed** metodologia runs (REQ-027/REQ-029 and older), including their dirty files, which the bundle and tarball preserve.
- Feature worktrees that are already in `main` or pushed:
  - `metodologia-{m2,m5,m6-quality,hardening,panel,req029,audit-readiness}`;
  - `.claude/worktrees/*`;
  - `/tmp/metodologia-*`;
  - `~/.local/tmp/metodologia-supervisor-check`;
  - the scratchpad `head-wt`.
- Remote branches **fully merged** into `origin/main`. Unmerged WIP branches stay: `feat/scheduler-m2-learning-quota`, `feat/scheduler-m5-recovery-manager`, `feat/scheduler-m6-quality`, `worktree-agent-a698b731c149f8d18`, `wip/supervisor-check`. They carry the 2026-10-23 WIP snapshots.
- `bitacora/.state/executor/*` of **terminal** metodologia runs, archived and then removed.
- **Never** touch david-ui REQ-001, pictures REQ-020, or any other project's live or held state. The frozen david-ui builder (pid 2108326, SIGSTOP) stays as it is.

## 6. Non-negotiables carried from the master

- Planner never approves, launches or routes. Explorer, Reviewer and Antagonist stay read-only. Runner never fixes code.
- M6 alone adjudicates acceptance. M5 owns recovery. M2 owns routing.
- No unsupported fields in schema 1.2.0. Legacy `SPEC.md`, `PLAN.md` and `PLAN.json` plans keep passing.
- A changed ancestor never triggers a blanket reimplementation; incompatibility must be demonstrated.
- No secret values in plans, logs or evidence. A missing credential means `BLOCKED`, never `FAIL` and never `PASS`.
- Implementer exclusions stand: no `systematic-debugging`, `verification-before-completion` or `receiving-code-review`.
