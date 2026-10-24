---
name: visual-evidence-capture
description: Capture breakpoint and state screenshots for a Reviewer visual audit using existing project browser tooling.
---

# Visual evidence capture

Use only when a brief asks Runner to provide screenshot evidence for a Reviewer `visual` task. Capture evidence; do
not evaluate design quality, contract fidelity, accessibility, or acceptance.

## Capture

1. Read the named, owner-approved contract and plan task. Extract the declared breakpoints, UI states, entry paths,
   and any required setup or fixtures. Ask the orchestrator for missing material details; do not invent coverage.
2. Reuse the running app and the project's existing browser/preview tooling. Prefer the configured agent Firefox
   through BiDi when available; use Playwright only when the project already has it. Do not install browsers or
   dependencies. In this environment, browser control uses the agent Firefox BiDi endpoint on loopback port 9223;
   never attach to the personal Firefox or port 9222.
3. Capture one screenshot for each declared breakpoint × state, after the specified state is visibly rendered.
   Use stable filenames or the existing evidence tool's IDs that encode the pair, for example
   `visual/<contract>@vN/<breakpoint>--<state>.png`. Preserve original captures; do not crop, annotate, or retouch.
4. If a capture fails, report its attempted path/state and observed blocker. Do not substitute another state, viewport,
   mockup, or stale screenshot without labeling the substitution and getting the orchestrator's direction.

## Return to the orchestrator

List the contract version, app URL/entry path, browser/tooling used, and a coverage table with breakpoint, state,
result, and screenshot evidence ID/path. Include every missing capture and its concrete reason. These are evidence
inputs for Reviewer `visual`; Runner does not issue a visual verdict or claim a review passed.
