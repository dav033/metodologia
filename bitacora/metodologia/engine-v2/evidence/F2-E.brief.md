# Task F2-E — Runtime enforcement of the Designer write scope + per-project preview setting

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
CONTRACT §3: "Designer may write only under `design/`. The runtime enforces that ownership; the prompt alone is not
enough." And: the preview is optional per project (setting), the contract is mandatory with UI work.
(`/home/david/dev/metodologia/bitacora/metodologia/engine-v2/CONTRACT.md` §3; schema design
`.../engine-v2/SCHEMA-1.3.0.md` §2–3: task `kind: design`.)

## You own
- The M3 executor adapter side that validates an attempt's result (`skill/scripts/bt_scheduler_executor_adapter.py`
  and/or the module that builds/validates handoffs, e.g. `skill/scripts/bt_scheduler_executor_wiring.py` — find the
  exact place where an attempt's snapshot is finalized/handed to verification; the audit read-only rule
  `gates.audit_read_only` in the quality adapter is the closest precedent: read it, keep the same style).
- `skill/scripts/bt_config.py` (only the new `design.*` keys and their validation), its tests.
- New tests: `skill/scripts/tests/test_designer_write_scope.py` (+ config tests in the existing config test file).
- Docs: one short paragraph in `skill/references/modules.md` §Agent executor (only that paragraph).

## Requirements
1. Scope rule: for an attempt of a task with `kind: design` (read from the frozen plan the executor already
   receives; schema 1.3.0), every path changed between the attempt's start base and its snapshot (added, modified,
   deleted, renamed — both sides of a rename) must be under `design/` of that repository. Otherwise the attempt is
   refused before verification with a stable, permanent cause code (e.g. `DESIGN_SCOPE_VIOLATION`) naming the
   offending paths; the work stays preserved (snapshot kept) like other refused results; nothing outside `design/` is
   ever integrated from it. Same rule via a role check if the route names the `designer` role.
2. `design.preview` setting: default `false`; per-project override following the existing config patterns (find how
   per-project lists such as `coordinator.projects` work and mirror them, e.g. `design.preview_projects`). When off,
   a design attempt that writes `design/preview/**` is refused with `DESIGN_PREVIEW_DISABLED`; when on, it is allowed.
   `bitacora.py config` shows/sets it like other keys.
3. Legacy behaviour unchanged for every other task kind and for plans < 1.3.0 (they cannot contain `design` tasks).
4. Tests first (fail before the change): violation refused with the paths; rename out of `design/` refused; preview
   off/on; non-design task unaffected; legacy plan unaffected.

## Verify
New tests, the executor adapter and quality adapter tests, and the full suite per RULES.md.
