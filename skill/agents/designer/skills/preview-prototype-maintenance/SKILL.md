---
name: preview-prototype-maintenance
description: Maintain the project's optional design preview under design/preview with mock data, a state switcher and an explicit contract version label.
---

# Preview prototype maintenance — Designer private skill

Load only when the project setting `design.preview` is enabled and the design task requests preview work. The project setting defaults to off. A UI/UX contract remains mandatory when preview is off.

## Keep the preview a design artifact

- Store preview files only in `design/preview/`; the executor enforces the role's `design/**` write boundary.
- Use mock data that resembles the shape of expected content. Never use production credentials, private user data or live production data.
- Add a visible state switcher for the contract's relevant states so reviewers can inspect loading, empty, error, success, disabled, validation and other applicable states on demand.
- Make the preview navigable across the views and flows within the design task. Keep copy and visual decisions aligned with the referenced contract.
- Label the preview with the exact contract id and version it represents. Keep the label visible to reviewers and update it only alongside an intentional contract-version change.
- Keep preview code and assets self-contained under `design/preview/`. Do not add routes, dependencies, tests or code to the production app.
- Describe limitations clearly: mock data, omitted behavior, unverified accessibility, or states not represented.

## Change and handoff

When a contract version changes, compare the preview with the new contract. Update the preview and its visible version label if the design changed; otherwise record why it remains representative. Never edit an approved contract to match a preview. If preview and contract disagree, report the mismatch and resolve the contract through its approval and versioning process.

Report the preview path, contract id/version, represented states and known limitations. Present it as a navigable design prototype for review, never as the implemented product or proof that production behavior exists.
