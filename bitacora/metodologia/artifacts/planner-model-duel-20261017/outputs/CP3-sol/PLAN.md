---
status: draft
---
# REQ-CP3 — Plan quality summary in review surfaces

Draft revision 1. Source: SPEC.md, requirements R1–R3. Repository role: `repository` → `./repo`. Nothing is approved, frozen, launched, or implemented.

## Scope and inspected findings

Expose the existing quality analysis on the web Plan tab and verify the existing terminal report. Preserve legacy rendering and approval behavior.

Observed facts:

- R1 already has an implementation: `skill/scripts/bitacora.py:396` dispatches to `bt_cli_plan.dispatch`, which calls `bt_plan_adapter.run_cli`; `skill/scripts/bt_planner/cli.py` handles `report` and prints JSON. `skill/scripts/tests/test_plan_integration.py`, class `Cli`, checks its exit status but discards output.
- `skill/scripts/bt_planner/quality.py:187` computes critical-path task IDs and estimated minutes, widest dependency level, classification distributions, low-confidence IDs, declared-evidence coverage, and verification gaps. These are planned properties, not execution results.
- `skill/scripts/bt_page_req.py:99` renders plan Markdown followed by the existing form or status notice. It does not request a quality report.
- `skill/scripts/tests/test_plan_boundary.py` requires that only the adapter imports the planner module. The web consumer must use that boundary.
- `skill/scripts/bt_planner/contract.py:452` provides validated, read-only loading with typed missing, malformed, unreadable, oversized, and invalid-plan errors.
- Approval remains owned by `bt_rounds.plan_decide` and the server’s POST handler in `skill/scripts/bt_server.py`. Displaying a report must not call them.
- `pyproject.toml` already packages the affected modules and declares no runtime dependencies. `README.md` documents unittest discovery; `test_metrics_page.py` demonstrates HTML escaping checks; `test_00_isolation.py` documents temporary-root isolation.
- The inspected checkout declares planner schema 1.1.0. This delivery uses the supplied 1.2.0 planning contract; upgrading the product schema is outside scope.

Also inspected: `bt_pages.py`, `bt_cli_flows.py`, planner CLI/sync/public exports, planner report tests, and supplied schema/example. No applicable repository AGENTS.md was found.

## Proposed assumptions and decision gates

No owner answers or approvals are available.

- **D1 — presentation, proposed:** show critical-path IDs and estimated minutes, widest level, and low-confidence IDs immediately before the approval form. Put classification distributions, declared-evidence counts, and tasks lacking command verification in secondary details. Use the page’s existing Spanish language and styling. Empty lists receive explicit empty-state text.
- **D2 — invalid files, proposed:** absent PLAN.json adds no markup; a present but unusable file shows a concise “summary unavailable” notice without metrics. Preserve existing form behavior and approval gates. Do not expose paths, raw file content, or exception messages.
- **A1 — terminal scope:** R1 means the explicit `plan-json report` command. Automatically printing summaries during `plan review` or `plan approve` is excluded.
- **A2 — semantics:** evidence coverage means evidence was declared; widest level is a graph property. Neither establishes verified evidence, available execution capacity, approval, or product acceptance.

T2 and the presentation acceptance portion of T3 are gated on accepting or revising D1/D2 during later plan review. Rejection requires updating their behavior and checks before implementation; implementers must not silently choose alternatives. T1 can establish the read-only data contract and legacy baseline independently.

## Milestones and tasks

### M1 — Adapter summary and terminal baseline

Acceptance: a structured summary is available through the adapter; existing terminal JSON and error behavior are protected; deterministic legacy HTML references exist before renderer changes.

- [ ] T1 — Expose a read-only adapter summary and protect terminal behavior · repo: repository · covers: R1, R2, R3 · kind: implement · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -p 'test_plan_integration.py' -v`

Add `quality_summary(rdir)` in `bt_plan_adapter.py`. Load and validate through the planner, then reuse `quality.analyze`; do not parse CLI output or duplicate calculations. Return the IF-1 availability contract. Keep `run_cli`, its JSON shape, and its exit statuses unchanged.

Extend integration tests to capture terminal output for a branching fixture: T1=30 minutes, T2 after T1=60, T3 after T1=20 with low confidence. Expect critical path T1→T2=90 minutes, width 2, and low-confidence list `[T3]`. Cover missing and invalid terminal input with exit 2 and no fabricated metrics.

Before renderer changes, capture deterministic no-PLAN.json HTML references for no status, review, approved, launched, in-progress, done, and changes-requested. Store these as planned test fixtures, not planning evidence. Added tests must isolate filesystem roots before application imports.

### M2 — Web summary and cross-surface verification

Acceptance: the Plan tab presents the agreed summary, CLI/web values agree, unavailable summaries remain distinguishable from absence, and legacy output matches the captured references.

- [ ] T2 — Render the adapter summary on the Plan tab · repo: repository · after: T1 · covers: R2, R3 · kind: implement · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -p 'test_plan_quality_page.py' -v`

Decision-gated on D1/D2. Have `plan_panel` obtain IF-1 from the adapter using the plan’s parent directory. For available data, render the agreed primary metrics and secondary details between Markdown and the existing form/notice. Preserve report ordering and values; label minutes as estimates and evidence as declared coverage.

For absence, return exactly the former HTML. For unavailable data, show only the agreed notice beside the existing content. Escape all report-derived strings. Add focused rendering tests, including empty lists and hostile strings supplied through a mocked adapter.

- [ ] T3 — Verify review integration and legacy compatibility · repo: repository · after: T2 · covers: R1, R2, R3 · kind: test · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -p 'test_plan_*.py' -v`

Exercise the actual CLI dispatcher and `req_page(..., tab="plan")` against the same isolated fixture. Assert expected metric values and cross-surface parity. Cover absent, malformed, non-object, schema-invalid, oversized, and mocked unreadable files; distinguish unavailable notices from successful summaries.

Compare legacy HTML with T1 references across statuses. Assert reporting/rendering leave requirement files and revision/run state unchanged, and never invoke approval, freeze, launch, or subprocess execution. Retain the import-boundary checks. Perform the planned product inspection only after D1/D2 are settled.

## Interfaces and dependencies

**IF-1 — adapter quality summary**, owned by `bt_plan_adapter.py`: T1 produces; T2 consumes; T3 verifies integration.

Input: requirement directory. Output: dictionary with `availability` (`absent`, `available`, or `unavailable`), `summary` (the unchanged analysis dictionary only when available, otherwise null), and `error_code` (a stable planner code only when unavailable, otherwise null).

Missing PLAN.json, including disappearance before loading, yields absence. Other expected loading/validation errors yield unavailable. No fabricated zeros, persisted cache, workspace lookup, approval check, or state mutation is introduced. CLI reporting retains its existing contract.

Graph: T1 → T2 → T3. T2 needs the adapter and baseline; T3 needs the completed renderer. Shared contract and test paths are explicitly ordered.

Coverage: R1 → T1/T3; R2 → T1/T2/T3; R3 → T1/T2/T3. No orphan work is planned.

## Verification, risks, and self-review

All commands are planned, run from the repository root. No tests, builds, validator, or report commands were executed in this session. New checks and fixtures are identified by `created_by` in JSON.

- **Static:** retain the adapter-only import boundary.
- **Functional:** adapter availability/error behavior and focused HTML rendering.
- **Integration:** actual CLI dispatch and Plan-tab rendering share expected analysis values.
- **Regression:** exact legacy HTML, terminal output/error compatibility, and no reporting side effects.
- **Product:** inspect metric visibility, labels, empty states, and unavailable notices; automated checks alone do not establish presentation acceptance.

Semantic self-review:

- **Fact:** R1 is already wired; correction is stronger output verification, not a replacement CLI.
- **Plausible risk, medium:** parsing stdout or recalculating metrics could drift between surfaces. Correction: IF-1 reuses the existing analysis.
- **Plausible risk, medium:** malformed files could break review rendering or resemble a successful empty report. Correction: explicit availability states and error tests.
- **Product decisions:** D1/D2 remain proposed. Their downstream tasks are gated.
- **Plausible risk, medium:** a report could be mistaken for approval or evidence validation. Correction: precise labels and preserved approval boundaries.

External consumers were not established; preserve terminal output rather than asserting external compatibility. Estimates are provisional, include local verification, and have no comparable execution-history samples. No historical measurement, execution assignment, or quota estimate is claimed.
