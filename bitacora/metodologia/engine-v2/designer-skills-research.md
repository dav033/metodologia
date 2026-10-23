# Designer skills research (2026-10-23)

Method: web search + repo page fetches via summarizer (not raw reads for most). Exact SKILL.md paths for several are NOT verified; repo URLs are. Licenses are from repo pages unless noted. Nothing executed.

## Candidates
1. anthropics/skills frontend-design — https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md ; LICENSE.txt verified Apache-2.0 (folder-level). Aesthetic direction, avoids generic AI look. WRITES PRODUCTION CODE (production-grade frontend). Fit: (a) low-med as aesthetic-direction checklist only, (b) ok, (c) no. Repo has mixed per-skill licenses (docx/pdf/pptx/xlsx are source-available, not Apache) - always check per folder.
2. anthropics/skills webapp-testing — https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md ; frontmatter "Complete terms in LICENSE.txt" (not read; likely Apache-2.0, UNVERIFIED). Playwright screenshots/DOM inspection with with_server.py helper. Fit (c) good as capture mechanism; no contract comparison. Runs scripts/servers.
3. jakubkrehel/skills — https://github.com/jakubkrehel/skills ; MIT; 8.2k stars (as reported). Skills: better-interface (combined review a11y/layout/writing/type/color), better-accessibility (WCAG 2.2: focus, ARIA, forms, zoom), better-layout (responsive, reading order, translation space), better-writing (labels, errors, empty states), better-colors (tokens, contrast), interface-review (reviews a branch/PR for UI regressions), state-machine (renders all states of component on throwaway page with mock data + state switcher), break (renders every scenario), variant (compares variants), build-design (Figma/image -> code with project tokens; writes production code). Fit: (a) high via writing/layout/a11y/colors as checklists; (b) state-machine/variant are close to preview but write throwaway pages; (c) interface-review + better-accessibility good. Conflicts: build-design writes prod code; user-invoked skills; exact SKILL.md paths unverified.
4. wshobson/agents plugins/ui-design — https://github.com/wshobson/agents/tree/main/plugins/ui-design ; MIT (README). Skills: design-system-patterns, accessibility-compliance, responsive-design, web-component-design, interaction-design, visual-design-foundations (+ mobile). Also plugin accessibility-compliance. Fit (a) medium-high as reference knowledge (tokens, breakpoints); plugin brings agents/commands (orchestration) - take skills only. Not verified individually.
5. oakoss/agent-skills — https://github.com/oakoss/agent-skills ; MIT; 19 stars (immature). ux-designer (journeys, wireframes, prototypes, 5 phases IA->handoff), ui-ux-polish, accessibility (WCAG 2.2 AA), figma-developer. Fit (a) best structural match to "contract/handoff" but low maturity; may impose own phases.
6. mae616/design-skills — https://github.com/mae616/design-skills ; MIT. ui-designer (IA, hierarchy), frontend-implementation ("states as specs", intent not pixels), accessibility-engineer, usability-psychologist (cognitive load, error prevention), creative-coder. Fit (a) good for hierarchy/states/usability; small repo.
7. vercel-labs/agent-skills web-design-guidelines — https://github.com/vercel-labs/agent-skills ; MIT; 32.9k stars. 100+ rules a11y/perf/UX reviewing UI CODE. Fit (c) static code audit, (a) as rule source. Vercel-flavored.
8. addyosmani/agent-skills frontend-ui-engineering + browser-testing-with-devtools — https://github.com/addyosmani/agent-skills ; MIT; ~110k stars. Implementation-oriented (implementer side), Chrome DevTools MCP live DOM inspection. Fit (c) browser-testing-with-devtools for rendered audit; frontend-ui-engineering is for implementers. Imposes its own workflow commands.
9. testdino-hq/playwright-skill — https://github.com/testdino-hq/playwright-skill ; MIT; 401 stars. core/visual-regression.md (thresholds, masking), core/accessibility.md (axe-core), core/mobile-and-responsive.md, playwright-cli/device-emulation.md. Fit (c) best single source. Writes test code (in repo - conflicts with "no files in repos" rule unless in design area).
10. currents-dev playwright-best-practices (docs.currents.dev/ai/agent-skill-playwright-best-practices) — license UNVERIFIED. Similar to 9.
11. manutej/luxor-claude-marketplace playwright-visual-testing — design-system oriented, flagged HIGH risk by skills.sh audit; avoid.
12. PramodDutta/qaskills playwright-visual-testing — pixel-diff only, no a11y; license unverified.
13. wshobson/agents, obra/superpowers — superpowers (15 skills: brainstorming, writing-plans, verification-before-completion...) has NO design/UI skill; license not seen in fetch (believed MIT, UNVERIFIED). Imposes own doc system/subagent orchestration; not for designer.
14. felvieira/claude-skills-fv ui-ux-design (tessl score 86%), plugin87/ux-ui-agent-skills (tokens, atomic design, variants/states), bergside/awesome-design-skills — not opened; licenses unverified.

No candidate found that does contract versioning/impact analysis or contract-vs-render comparison: that is a gap -> private skills.
No CC BY-SA / Commons Clause / AGPL seen among verified ones; unverified ones may differ.

## Ranking
Designer core: jakubkrehel/skills (better-writing, better-layout, better-accessibility, better-colors, state-machine), wshobson ui-design (design-system-patterns, responsive-design), mae616 (ui-designer, frontend-implementation states-as-specs), oakoss ux-designer (conditional, immature).
Visual QA: testdino-hq/playwright-skill, anthropics webapp-testing, jakubkrehel interface-review, vercel web-design-guidelines, addyosmani browser-testing-with-devtools.
Recommendation: vendor/adapt (copy rules, not install wholesale) with license attribution (MIT/Apache keep notices).

## Proposed private skills
- ui-ux-contract-authoring: template + checklist for contract (structure, hierarchy, tokens, nav, flows, states, responsive, a11y, acceptance criteria), project-agnostic.
- design-contract-versioning-and-impact: semver for contracts/previews, change log, impact analysis of visual changes, approval gate for implementers.
- preview-prototype-maintenance: optional mock-data preview in design area, state switcher, never production code, sync with contract version.
(Optional 4th: rendered-ui-fidelity-audit for Reviewer: screenshots per breakpoint/state, axe, diff vs contract criteria.)
