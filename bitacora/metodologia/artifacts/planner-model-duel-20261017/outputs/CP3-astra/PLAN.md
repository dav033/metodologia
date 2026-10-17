---
status: draft
---
# REQ-CP3 — Plan quality summary at review
Revision: 1 · Contract: 1.2.0 · Requirement: SPEC.md

Draft only. No implementation, tests, builds, validation, approval or launch occurred. Verification below is planned. Repository: `repository` → `./repo`.

## Scope and inspected findings

Expose the existing quality analysis on the Plan approval tab, preserve the terminal report, and keep rendering unchanged when PLAN.json is absent.

- **R1 already has an implementation:** `skill/scripts/bitacora.py:396` dispatches to `bt_cli_plan.dispatch`; `skill/scripts/bt_cli_plan.py:15-22` accepts `report` and calls the adapter; `skill/scripts/bt_plan_adapter.py:98-102` delegates to the module. `skill/scripts/tests/test_plan_integration.py:202-227` checks report success but does not assert its contents.
- **Report semantics already exist:** `skill/scripts/bt_planner/cli.py:97-105` prints JSON after validation. `skill/scripts/bt_planner/quality.py:184-232` computes critical-path task IDs and estimated minutes, widest dependency level, distributions, low-confidence IDs and verification/evidence indicators. Reuse these calculations.
- **Correct web consumer:** `skill/scripts/bt_page_req.py:36-41,99-115` renders the Plan tab and approval form. `skill/scripts/bt_page_review.py` handles completed code review and merging; it is not the target.
- **Boundary:** `skill/scripts/tests/test_plan_boundary.py:19-66` enforces access to the planner through `bt_plan_adapter.py`. The web renderer must not import the module directly.
- **Safe loading:** `skill/scripts/bt_planner/contract.py:452-469` provides validated, bounded loading and typed errors. `skill/scripts/bt_planner/__init__.py` exports `load`; the adapter may import the existing quality analyzer.
- **Rendering and configuration:** `skill/scripts/bt_pages.py:16-40` supplies Spanish HTML and escaping conventions; `skill/assets/style.css:29-31,66-67` has suitable card, KPI and warning styles. `pyproject.toml` packages the affected modules without new dependencies.
- **Verification foundation:** inspected integration fixtures, `test_plan_launch_paths.py`, `test_metrics_page.py`, `test_00_isolation.py`, the planner analysis assertions in `bt_planner/tests/test_evidence.py:484-491`, and README test instructions. No AGENTS.md was found inside the cell.

Out of scope: new graph algorithms, changing the report JSON format, report-driven approval rules, scheduler changes, schema migration, automatic terminal approval interception, additional web endpoints or dependencies.

## Proposed assumptions and decision gates

These are proposals, not owner decisions; no Q&A occurred.

- **D1 — Invalid PLAN.json:** display an escaped “summary unavailable” warning, retain the existing document/form, and omit metrics. Absence remains silent. Existing approval validation remains authoritative. T1's error contract and T2's error presentation are gated on accepting this proposal in the eventual requirement review.
- **D2 — Presentation:** show the three R2 metrics in a compact Spanish section before the plan document: critical-path IDs and estimated minutes, widest level in tasks, and low-confidence IDs or an explicit “none.” The existing terminal JSON continues exposing the fuller classification/evidence summary. T2 is gated on accepting this scope; additional web details require revised acceptance criteria.
- A widest level is a graph statistic, not an execution allocation. Estimated minutes are not measured runtime. Summary availability does not prove publishability, verified evidence, approval or product acceptance.
- External consumers of terminal output are unknown. Preserve its current JSON shape and exit behavior; do not claim external compatibility has been verified.

## Milestones

### M1 — Preserve reporting and expose structured analysis

Acceptance: R1 has content-level regression coverage; the adapter exposes ready, absent and invalid outcomes without modifying requirement artifacts.

- [ ] T1 — Expose read-only summary through the adapter · repo: repository · covers: R1, R2, R3 · kind: implement · files: skill/scripts/bt_plan_adapter.py, skill/scripts/tests/test_plan_integration.py · resources: plan-quality-summary · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v`

Add `quality_summary(rdir)` with the IF-1 contract. Load and validate once through the module, then call its existing analyzer. Return absent only for a missing file; malformed JSON, invalid contracts, unreadable files and excessive size produce invalid, without numeric defaults. Normalize diagnostics to safe codes/messages without exposing absolute paths. Do not invoke check/freeze/launch, a subprocess, evidence commands or workspace discovery for this web read.

Keep the existing CLI route and JSON unchanged. Extend integration tests to assert parsed report contents and exit codes, not just successful dispatch. Cover adapter ready/absent/invalid behavior, removal during loading, and unchanged artifact bytes.

### M2 — Show and verify the review summary

Acceptance: R2 appears on the actual Plan approval page; R3 retains the complete legacy panel output and controls; report reads have no approval or runtime side effects.

- [ ] T2 — Render the summary on the Plan approval tab · repo: repository · after: T1 · covers: R2, R3 · kind: implement · files: skill/scripts/bt_page_req.py, skill/scripts/tests/test_plan_summary_page.py · resources: plan-quality-summary, plan-review-rendering · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v`

Consume IF-1 through the adapter. For ready, prepend the agreed summary using existing styles and escaped dynamic text. For absent, return exactly the pre-change `md("doc", read(plan)) + form`, with no extra wrapper or placeholder. For invalid, prepend the D1 warning while retaining the original body and form. Preserve form action, token, fields, status behavior and existing controls.

Create renderer tests for ready, no low-confidence tasks, absent, invalid and hostile diagnostics. Compare complete absent-case output against a baseline derived from the pre-change renderer for draft, review, approved, launched, in-progress and done. Preserve the existing no-PLAN.md branch.

- [ ] T3 — Verify CLI and review-page parity and legacy behavior · repo: repository · after: T2 · covers: R1, R2, R3 · kind: test · files: skill/scripts/tests/test_plan_integration.py, skill/scripts/tests/test_plan_summary_page.py · resources: plan-quality-summary, plan-review-rendering · verify: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -v`

Exercise the real CLI dispatch and `req_page(..., tab="plan")` against the same isolated requirement. Use a branching fixture with T1=30 minutes, T2=60 after T1, and low-confidence T3=20 after T1: expect critical path T1→T2=90 minutes, widest level 2, and low confidence T3. These are fixture expectations, not measurements. Assert parity with the adapter and terminal JSON.

Check missing, malformed, unreadable and invalid PLAN.json; ensure unavailable data never appears as zero or an empty valid summary. Compare file bytes and directory entries before/after reads, including existing RUN.json and revision artifacts. Patch roots and isolate subprocess environments before imports; use no real owner configuration. Run the existing boundary and launch-regression coverage without changing its allowlist. Finally inspect the rendered page at narrow and wide widths, without submitting approval.

## Traceability, risks and verification

| Requirement | Delivery and acceptance |
|---|---|
| R1 | T1 preserves and asserts terminal output; T3 verifies real dispatch against the page fixture. |
| R2 | T1 produces IF-1; T2 renders it; T3 verifies actual page integration and visual usability. |
| R3 | T1 distinguishes absence; T2 preserves exact legacy HTML; T3 verifies page and artifact regressions. |

IF-1 is produced by T1, consumed by T2 and T3, and integrated by T3. Dependency chain: T1 → T2 → T3. Shared edits and contracts are ordered.

Semantic self-review, not independent approval:
- **Fact:** R1 already exists; duplicating its command or replacing JSON would add unnecessary compatibility risk. Correction: strengthen coverage and preserve routing.
- **Plausible risk, medium:** placing the section in the completed-code Review tab misses approval-time use. Provenance: `bt_page_req.py:36-41`. Correction: target `plan_panel` and test `req_page`.
- **Plausible risk, medium:** missing and invalid data could be conflated. Provenance: `contract.py:452-469`. Correction: explicit three-state adapter contract.
- **Plausible risk, high impact:** raw diagnostics inserted into the local approval page could inject markup. Provenance: existing escaping conventions in `bt_pages.py` and `test_metrics_page.py`. Correction: escape every dynamic value and test hostile content.
- **Product decisions:** D1/D2 remain proposed and gate their dependent behavior.

Functional and integration checks will be added by their named tasks; existing tests are evidence only of available coverage, not successful execution. The boundary check is static verification; legacy HTML, CLI shape, artifact immutability and launch tests provide regression verification. Visual inspection supplies product evidence separately.

Estimates are planning judgments: T1 75 minutes, T2 75 minutes, T3 60 minutes, including local verification. No comparable execution history was available or queried; actual duration and success rates remain unknown. The host supplies deterministic validation results after capture.
