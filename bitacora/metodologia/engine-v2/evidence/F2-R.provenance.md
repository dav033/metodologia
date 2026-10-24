STATUS: DONE
SUMMARY: Added the Reviewer visual axis and conditional skill loading while preserving the role's tools and read-only boundary.
Updated all three private skills to carry semantic fingerprints, severity, classification, criterion/contract references, and M6 ownership boundaries.
Added rendered UI audit steps for declared breakpoint × state coverage, conditional axe use, screenshot evidence, and explicit BLOCKED reporting.
M6's existing `audit-findings/1` ledger remains authoritative; Reviewer metadata is evidence, not a second persisted format.
VERIFICATION: Python stdlib path/frontmatter check → exit 0 (<1s); no missing local paths or frontmatter name mismatches.
VERIFICATION: `git diff --check` and `git diff --cached --check` → exit 0 (<1s).
VERIFICATION: `python -m unittest discover -s tests` → exit 1 (907.037s; 2404 tests, 15 failures, 6 skipped; all 15 match RULES.md baseline, zero additional failures).
COMMITS: 081711b3e885d24ee73a880d5957f60b325d1dfc feat(reviewer): add visual review axis and skills
PROVENANCE:
- Repo: akkie76/code-review-skills; path: `dist/codex/evidence-code-review/SKILL.md`; SHA: `ca7b11c91906c60cc8aed611d5acb191d0335723`; license: MIT (root `LICENSE`); adapted scope freeze, concern coverage, evidence validation, and false-positive checks into `skill/agents/reviewer/skills/evidence-based-findings/SKILL.md`.
- Repo: JUNERDD/skills; path: `skills/code-review/SKILL.md`; SHA: `f76dec9eacbcea858e1d469710067020bd3fec6a`; license: MIT (root `LICENSE`); adapted coverage IDs, semantic finding identity, and review lineage into `skill/agents/reviewer/skills/evidence-based-findings/SKILL.md`; excluded delegation, report files, and review automation.
- Repo: trailofbits/skills; path: `plugins/differential-review/skills/differential-review/SKILL.md`; SHA: `196a9073ab10d35bacf111f945e02c00b2c6883a`; license: CC BY-SA 4.0 (root `LICENSE`); principles-only risk-scoped changed-path and consumer analysis, no text copied, referenced in `skill/agents/reviewer.md` and `skill/agents/reviewer/skills/evidence-based-findings/SKILL.md`.
- Repo: testdino-hq/playwright-skill; path: `SKILL.md`; SHA: `178d1cb537604279d7b54500c4823a6db42b9de6`; license: MIT (root `LICENSE`); adapted responsive screenshot evidence and conditional accessibility checks into `skill/agents/reviewer/skills/rendered-ui-fidelity-audit/SKILL.md`.
- Repo: anthropics/skills; path: `skills/webapp-testing/SKILL.md`; SHA: `dbd4588f9e1033efb41dad4bef2f7947c8993d44`; license: Apache-2.0 (skill `skills/webapp-testing/LICENSE.txt`, specified by the skill frontmatter); reference only for inspecting locally rendered apps and screenshots in `skill/agents/reviewer/skills/rendered-ui-fidelity-audit/SKILL.md`; no upstream workflow or helper scripts copied.
CONCERNS: The runner did not provide an explicit `-o` result path in the task context; this result is saved at `/tmp/F2-R-result.txt`.
