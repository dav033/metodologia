# Plan artifacts: producers and consumers (T1 of REQ-009)

Source: code read on 2026-10-14 at `/home/david/dev/metodologia` (working tree with uncommitted work). Line numbers come
from reading; they drift.

## Producers

| Artifact | Producer | Notes |
|---|---|---|
| `SPEC.md` | `skill/scripts/bitacora.py` `req new` (≈362-367), template `skill/templates/SPEC.md` | `status: clarifying`, `track: standard` |
| `PLAN.md` | `bitacora.py` `req plan` (≈369-378), template `skill/templates/PLAN.md` | `status: in-progress`; task grammar documented in an HTML comment of the template |
| `HANDOFF.md` | `bt_launch.write_handoff` (`bt_launch.py:24`, written at `:87`) | called by `bt_launch.launch`, which requires the requirements gate and `status == approved`, then sets `launched` |
| auto handoff | `bt_handoff.py:186-214` | `assess` → optional self-approval (`bt_rounds.plan_decide`) → `launch(mode="marathon")` |
| `RUN.json` | `bt_run.py:71` → `bt_runstate.init_state` (`:225`); `sync_plan` (`:194`), load `:244`, save `:258` | frozen at creation; later PLAN drift is only reported (`plan_drift`) |
| `PLAN.json` | **none** (this requirement adds it) | |

## Consumers of PLAN.md

- Parser: `bt_runstate.parse_plan` / `parse_task_line` / `milestones` (`bt_runstate.py:29-135`).
  - Task line: `- [ |x|X] T<n>[.m][a-z] <— – -- - :> title · key: value …`; fields split on ` · `, keys lowercased.
  - Milestones: only `### M<n>` / `#### M<n>` headings; any other heading resets the milestone.
  - `verify` only from a backticked value; `after` keeps tokens `T\d+(\.\d+)?[a-z]?`; `files`/`resources` reject
    absolute or `..` paths; `covers:` ignored; `<!-- -->` stripped first.
  - `complexity`/`size` normalised to S/M/L; `risk` raw lowercase (not validated); `kind` validated against
    `bt_agents.KINDS`; `level` only `architecture` matters.
- Users of the parse: `bt_handoff.assess` (`:116`, risk check `:156-158`), `bt_run`, `bt_runsession`, `bt_runsettle`,
  `bt_runtask.tick_plan` (`:27`), `bt_rounds.plan_review/plan_decide` (`:109/:117`), `bt_server.py:167-219`,
  `bt_page_req.py`, `bt_page_review.py`, `bt_orchestration_transition.py:64,117` (needs `approved`),
  `bt_requirements_gate.py` (hashes normalised SPEC/PLAN; `legacy` when no snapshot).
- RUN.json `complexity`/`risk` come from `_new_task` (`bt_runstate.py:138-146`); absent in PLAN lines ⇒ null.

## Approval and versioning today

`status:` front matter in PLAN.md (`in-progress|review|changes-requested|approved|launched|done|merged`), written by
`bt_rounds`, `bt_server`, `bt_launch:199`, `bt_run:267`; each approval appends a log line and commits through
`bt_vcs.commit`. There is no revision store; history is git. `bitacora.py run` itself does not check status (only
`launch`/`handoff` do).

## Conventions

Stdlib-only (`pyproject` `dependencies = []`, Python ≥3.12, `from __future__ import annotations`), hand-written
validation (`bt_requirements_gate._validate`), unittest tests in `skill/scripts/tests/` run with
`PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v`; new modules are listed in
`pyproject.toml` `py-modules`; file guard 500 lines (`bt_runstate.py` 497, `bt_run.py` 498 ⇒ do not grow them).

## Real examples (pictures project)

- REQ-013: `PLAN.md` only, tasks under `## Phase N` (no `### M`), non-canonical status text.
- REQ-015: `PLAN.md` (4 tasks with `after/files/verify/covers`), `SPEC.md`, `REPORT.md`; no RUN.json.
- REQ-016: `PLAN.md` (`### M1/M2`, T1-T3), `RUN.json` (all `complexity`/`risk` null), `HANDOFF.md`, audits.
- Across all plans: `complexity:` in 7 lines, `risk:` in 3, `level:` in 14, `kind:` in 10.

## Gaps this requirement closes

No uniform classification, no structured plan file, no consistency check between narrative and operational data, no
frozen revision, no `plan_id`/`revision` reference from a run.
