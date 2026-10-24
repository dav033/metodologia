STATUS: DONE
SUMMARY: Added Researcher’s two private skills and four conditional public adaptations.
Updated the Researcher prompt with conditional loading and the `CLAIMS` output contract.
The knowledge-store CLI is absent from this worktree; the skill reports that limitation rather than claiming a query or ingestion.
CHANGES: `skill/agents/researcher.md` — conditional loading, untrusted-source guardrail, and claims output.
`skill/agents/researcher/skills/external-research-memory/SKILL.md` — query-first workflow and `research-claims/1` format.
`skill/agents/researcher/skills/source-freshness-verification/SKILL.md` — source independence, freshness windows, contradictions, and untrusted-content handling.
`skill/agents/researcher/references/public-research-techniques.md` — adaptations, license/SHA/provenance table, and exclusions.
VERIFICATION: `git diff --check` and staged diff check → exit 0.
`research-claims/1` JSON and required paths check → exit 0.
`python -m unittest discover -s tests` → exit 1 (962.980s): 2,404 tests; 15 baseline failures, 6 skipped; no additional failures.
COMMITS: `374635f79` feat(researcher): add memory and freshness skills
PROVENANCE: `SkillMedev/skills` `97a13607d669157a4a16d5ba79b77f208319f7b9` (MIT): deep research and synthesis techniques. `citypaul/.dotfiles` `cd4028d57d6e4e95814f7b8ee55ca13c23a9c2f0` (MIT applies to target directory): solution evaluation. `jp-cruz/agent-skills` `ace4ecdcdffdfd7c37f8fa55d315e4c455b2e6bd` (MIT): claim verification. `jamditis/claude-skills-journal`: repository not found; license unverified, no content adapted.
CONCERNS: The knowledge-store README and CLI are absent from this worktree; query attempts confirm `bitacora.py` has no `knowledge` command here. `ev2/F2-G` is 6 commits behind `origin/main`; no rebase performed.