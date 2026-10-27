# Designer kit v2 / phase 4 — continuation evidence

Owner briefs: `designer-kit-v2.md`, `designer-kit-phase4.md` including ADDENDUM. Continued directly from
`dev/relay/RELAY-20261026-214844.md` after checking the live dirty tree. No requirement/plan flow, commits,
pushes, deployments, service restart, live Pictures writes or REQ-021 Designer relaunch.

## Real workspace and gallery

- Existing phase-A installation was preserved, not repeated. Workspace:
  `~/.local/share/bitacora/kit-workspace`, outside Git, with package-lock.json and install.json.
- `real/smoke.py` rendered 93/93 demos cleanly in both themes (`/tmp/designer-kit-smoke.log`).
  Inventory coverage is **92/93**, deliberately distinct from render success: shadcn 42/42,
  Animate UI capabilities 7/7, Bencho 11/12, React Bits 32/32. Bencho's published Picker selects assignees,
  not an inertial wheel; its compiled demo remains visible with a contract-gap notice (P-212).
- Animate UI enhancements: 19/22. Pagination and Sidebar require manual integration; Sonner retains its
  own motion rather than introducing a second toast engine (P-211). The manifest explains each gap.
- Gallery filters/search, theme/motion/width and reduced-motion controls were exercised in Chromium.
  Screenshots: `/tmp/designer-kit-shots/components-{1280,390}-{light,dark}.png`.
  Parent inspected desktop light and phone dark. Browser reports: `/tmp/designer-kit-gallery-browser-final.log`
  (before the final explicit Picker gap: done93/gap0 then), `/tmp/designer-kit-post-rebuild-browser.log`.
- References now accept the gallery's parent-only `kit:set` messages and query theme/motion/reduced flags.
  TextType uses complete static text under reduced motion, avoiding its independent GSAP timers/cursor.
  Regression tests exercise both behaviours. Partial offline rebuild logs:
  `/tmp/designer-kit-rebuild.log`, `/tmp/designer-kit-rebuild-final.log` (zero failed builds).

## Designer and directions

- Real libraries first; offline TSX builder inlines React, CSS, fonts, Motion/GSAP into one HTML. The fallback
  plain HTML kit remains explicit. Source role, private skill, generated brief and craft guidance were updated.
  Actual provider argv already uses unrestricted execution (Codex bypass / Claude skip-permissions); do not
  call this an OS sandbox. Write scope is the delegation's contractual boundary, not a runtime filesystem guard.
- Default three Designers, configurable 1–3, one live batch per requirement. Each produces two thumbnail candidates,
  then its strongest complete direction with eight-axis notes and measurable selectors. Revision-specific files
  preserve earlier explorations; prior notes form the cross-subplan look ledger with shared product identity.
- Rendered DNA compares geometry, computed typography, navigation and actual keyframe/easing evidence; missing
  measurement and colour-only variants fail closed. This heuristic does not replace human aesthetic judgement.
- Plan and review show A/B/C switcher, simultaneous previews, fullscreen links, axes, pair metrics, owner choice,
  previous directions and targeted feedback. Choice records activity and notifies Planner on the web. Token/origin
  tests reject untrusted POSTs. Confirmation/approval requires choice plus ready finalized canonical contract.
- `design draft REQ-NNN ref@v1 --fresh --directions 3`: compose from requirements/unresolved feedback, preserving
  previous files. Web redo and feedback use fresh mode. Single-direction mode still requires owner choice.

## Real isolated E2E

- Fixture pointer: `/tmp/designer-real-e2e-root` → `/tmp/designer-real-e2e-_3g67_kc`.
  Project fixture, requirement `REQ-001-taller`, one view, two states; no live project files used as write targets.
- Three actual `bt_design_drafts.request` delegations used codex-luis, gpt-6.1-sol, high, through the real supervisor.
  They produced six candidate thumbnail HTMLs, three TSX/built HTMLs and Markdown/JSON notes without a fake delegate.
- A: **Pliego de taller** — editorial working sheet, left filter column and ruled event rows.
  B: **Mesa suspendida** — staggered suspended cards and spatial staging.
  C: **Pliegues de trabajo** — folded horizontal sheets, measuring rail and tactile actions.
- All three outcomes claimed; system settlement reached choosing. Pair gate PASS, geometry similarity .010/.010/.029;
  typography and motion differed for every pair. Navigation matched B/C by the semantic landmark probe but did not
  produce a pair collision. Evidence: `/tmp/designer-real-e2e-settle.json`.
- Independent offline contrast/audit on each exploration: 158 token pairs each; 8/8 render combinations each,
  PASS, no contrast/nontext/focus/alignment/padding/overflow findings. Logs:
  `/tmp/designer-real-e2e-audit-{a,b,c}.log`.
- Twelve screenshots in `/tmp/designer-real-e2e-shots/`; parent inspected all three desktop light and all three
  phone dark. The compositions are visibly distinct while retaining the required Catppuccin/mauve identity.
- Fixture-only simulated owner choice selected A and launched a fourth real Designer finalizer. Its final outcome
  and canonical contract acceptance are recorded below once settled; this is not owner approval of a live design.

## Independent Antagonist

Fresh read-only pass returned five evidenced findings, all fixed with regressions:
A1 single-direction mode reused stale exploration state; A2 failed batches missed failure/automatic-run budgets;
A3 abandoned queued directions never expired; A4 references ignored gallery controls; A5 TextType still animated
under reduced motion. No finding was dismissed. Canonical/server/preview responsibilities were split into focused
modules, preserving unrelated dirty-tree changes. D-136 supersedes D-135; P-207 now tracks eventual package adoption.

## Research adopted (no repeat research)

The prior session's full pinned-source investigation and ranking remains at `designer-kit-phase4.research.md`.
Distilled locally into `david-ui-kit/directions.md`, craft/role guidance and third-party notices: huashu is first
for six-to-three exploration/ledger/critique; taste and impeccable for product-derived direction/working screens;
Emil for interaction motion; oil-ui for distinctness; LottieFiles for choreography; design-dna for measured vs
qualitative traits; Gesso for mechanical critique; hallmark/anti-slop for generator tells. Derivative lists and
product funnels were rejected as methods; brand reference libraries remain optional stance material, not copied marks.

## Limits and remaining work

- Existing audit heuristics remain P-209; reduced-motion screenshots and still-state checks do not prove 60fps.
  No FPS budget or automated semantic taste judgement is claimed.
- Some published Bencho/MagicBento internals retain English copy; real-library origin is preserved, and live project
  copy must still be localized by the Designer. Picker semantic mismatch and Animate enhancements are explicit gaps.
- No full-repository suite, global typecheck or full package build has been claimed; focused checks are recorded below.
- P-213: the real finalizer found that switching Quieto during an entrance does not immediately stop all Motion
  replacements. Finishing active WAAPI/CSS and then covering two RAF phases did not fix the actual Motion case.
  A stronger real-entrance regression now exposes it; no test was weakened. The owner was asked, as required by
  AGENTS §1 after two failed attempts, whether to continue with explicit Motion controls preserving form/filter state.
- `bitacora-web.service` was not restarted: the orchestrating session must load the new source when authorized.
  REQ-021 was not touched/relaunched; the owner/orchestrator still controls its pause marker and launch.

## Final checks

- Full requested acceptance plus route/approval boundaries: 135 tests, exit 0, 54.296s, before strengthening the
  hot-switch regression. `/tmp/designer-kit-acceptance-final.log` retains the complete result.
- Latest focused canonical/direction/HTTP gates: 43 tests, pass (`/tmp/designer-kit-final-gates.log`).
- Runtime/browser suite: 6 passed before the stronger real-Motion interruption assertion. Current strengthened
  case FAILS after 60ms with actual entrance animations still running (`/tmp/designer-kit-motion-real-after.log`).
  Synthetic 5s WAAPI interruption plus retained input passed; that is insufficient evidence for Motion itself.
- Strict scoped TS check: `node <workspace>/node_modules/typescript/bin/tsc -p /tmp/designer-kit-tsconfig.json`, exit 0.
  The temporary config maps installed React types and workspace aliases without a deprecated baseUrl.
- New modules/tests: Ruff passed; planning-live/mockup-nav `node --check` passed; `git diff --check` passed.
- Chooser screenshot `/tmp/designer-kit-chooser.png` inspected. Real panel/layout, A/B/C/all switching and thumbnail
  bridge navigation passed on an isolated read-only server; no POST. Final Picker gap still has a visible real preview.
- First real finalizer reached ready, chosen A, revision 1, with twelve-section contract, chosen HTML and archived pair.
  It honestly reported the hot-switch concern. A second fixture finalizer was launched to rebuild the chosen source
  with the current toolkit; its outcome was still pending when P-213 was raised. Do not call the entire work ready
  for live Designers until this regression is resolved or the owner explicitly accepts the limitation.
- Final git status evidence: `/tmp/designer-kit-git-status-final.txt`; unrelated concurrent work was preserved.
  Live Pictures translation changes appeared during the session (activity timestamp 21:58); no direct command here
  wrote Pictures or removed its Designers pause flag. The flag's mtime remained 21:48.
